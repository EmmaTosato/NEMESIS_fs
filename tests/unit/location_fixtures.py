"""Synthetic atlases for the lesion-location tests - tiny, on a toy grid, in the same relationship the
real files have to the project's templates: the atlas images are LAS (x axis reversed) while the
reference grid is whatever affine the test passes (RAS in every test), so a correct run has to go
through the affines, and a naive array flip gets a different answer.

Each atlas is built from voxel lists given in the REFERENCE grid's index space. The label of a
voxel (Left/Right) comes from its world x, so the sign checks of the real code pass by
construction; a voxel exactly on the midline is a mistake in the test and raises. Every label an
atlas declares must have a voxel (the real code checks that), so a label no scenario voxel uses
gets a "completion" cell on the TOP slab (k = nz - 1) - scenarios must keep off that slab.
"""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from src.features.lesion_location import LesionAtlas, LesionLocationSpec

_GRAY = ("Thalamus", "Caudate", "Putamen", "Pallidum", "Hippocampus", "Amygdala", "Accumbens")


def _flip_x(affine: np.ndarray, nx: int) -> np.ndarray:
    """Affine of the same image with its x axis stored reversed (voxel i <-> nx - 1 - i)."""
    flip = np.array([[-1.0, 0, 0, nx - 1], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]])
    return affine @ flip


def write_atlas(
    tmp_path: Path, name: str, shape: tuple[int, int, int], affine: np.ndarray,
    labels: dict[str, list[tuple[int, int, int]]], las: bool = True,
) -> LesionAtlas:
    """An atlas image + XML from {label name: reference-grid voxels}. Voxel value = XML index + 1."""
    data = np.zeros(shape, dtype=np.int16)
    xml_labels = []
    for index, (label, voxels) in enumerate(labels.items()):
        xml_labels.append(f'<label index="{index}" x="0" y="0" z="0">{label}</label>')
        for voxel in voxels:
            if data[voxel] != 0:
                raise ValueError(f"test fixture: voxel {voxel} is claimed by two labels of the {name} atlas")
            data[voxel] = index + 1
    image_affine = _flip_x(affine, shape[0]) if las else affine
    image_data = data[::-1] if las else data
    image_path = tmp_path / f"{name}_atlas.nii.gz"
    nib.save(nib.Nifti1Image(np.ascontiguousarray(image_data), image_affine), image_path)
    labels_path = tmp_path / f"{name}_atlas.xml"
    labels_path.write_text(
        '<?xml version="1.0" encoding="ISO-8859-1"?>\n<atlas version="1.0"><data>\n'
        + "\n".join(xml_labels) + "\n</data></atlas>\n"
    )
    return LesionAtlas(image_path=image_path, labels_path=labels_path)


def make_location_spec(
    tmp_path: Path, shape: tuple[int, int, int], affine: np.ndarray, grid: str = "coarse", *,
    cortex=(), white=(), gray=(), stem=(), ventricle=(), cerebellum=(),
) -> LesionLocationSpec:
    """The three atlases for a scenario. cortex -> cortical atlas; white/gray/stem/ventricle ->
    subcortical atlas (so they cannot overlap each other, as in the real maxprob atlas);
    cerebellum -> cerebellum atlas."""
    atlas_dir = tmp_path / "atlases"
    atlas_dir.mkdir(exist_ok=True)
    nx, ny, nz = shape
    world_x = affine[0, 0] * np.arange(nx) + affine[0, 3]
    left_i, right_i = np.where(world_x < 0)[0], np.where(world_x > 0)[0]

    def side(voxel):
        if voxel[2] == nz - 1:
            raise ValueError(f"test fixture: voxel {voxel} is on the top slab reserved for completion cells")
        x = world_x[voxel[0]]
        if x == 0:
            raise ValueError(f"test fixture: voxel {voxel} is on the midline, which has no hemisphere label")
        return "Left" if x < 0 else "Right"

    def by_label(voxels, names):
        """{label name: voxels} for a kind whose label is "<side> <name>"."""
        return {f"{s} {n}": [v for v in voxels if side(v) == s] for s in ("Left", "Right") for n in names}

    def complete(labels: dict[str, list[tuple[int, int, int]]]) -> dict[str, list[tuple[int, int, int]]]:
        used = 0
        for label, voxels in labels.items():
            if voxels:
                continue
            hemisphere = left_i if label.startswith("Left") else right_i
            if label.startswith(("Left", "Right")):
                voxels.append((int(hemisphere[used % len(hemisphere)]), used // len(hemisphere), nz - 1))
            else:
                voxels.append((int(right_i[-1]), ny - 1, nz - 1))
            used += 1
        return labels

    cortical = complete({"Left Region": [v for v in cortex if side(v) == "Left"],
                         "Right Region": [v for v in cortex if side(v) == "Right"]})
    sub: dict[str, list[tuple[int, int, int]]] = {}
    sub.update(by_label(white, ["Cerebral White Matter"]))
    sub.update(by_label(gray, list(_GRAY)[:1]))  # scenario gray voxels are all "Thalamus"
    for structure in _GRAY[1:]:
        sub.update({f"{s} {structure}": [] for s in ("Left", "Right")})
    sub["Left Lateral Ventrical"] = [v for v in ventricle if side(v) == "Left"]  # the real XML's spelling
    sub["Right Lateral Ventricle"] = [v for v in ventricle if side(v) == "Right"]
    sub["Brain-Stem"] = list(stem)
    for voxel in stem:
        side(voxel)  # top-slab guard only
    cereb = complete({"Left I-IV": [v for v in cerebellum if side(v) == "Left"],
                      "Right I-IV": [v for v in cerebellum if side(v) == "Right"]})
    return LesionLocationSpec(
        grid=grid,
        cortical=write_atlas(atlas_dir, "cortical", shape, affine, cortical),
        subcortical=write_atlas(atlas_dir, "subcortical", shape, affine, complete(sub)),
        cerebellum=write_atlas(atlas_dir, "cerebellum", shape, affine, cereb),
    )


def location_config_block(spec: LesionLocationSpec) -> dict[str, object]:
    """The `location` block of a compute_lesion_metadata.json config for `spec`."""
    def atlas(a: LesionAtlas) -> dict[str, str]:
        return {"image_path": str(a.image_path), "labels_path": str(a.labels_path)}

    return {
        "grid": spec.grid,
        "atlases": {
            "cortical": atlas(spec.cortical),
            "subcortical": atlas(spec.subcortical),
            "cerebellum": atlas(spec.cerebellum),
        },
    }
