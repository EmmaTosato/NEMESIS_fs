"""Where in the brain a lesion sits: seven exclusive anatomical categories per voxel, and each
lesion's fraction in every one of them.

Three FSL atlases (assets/atlases/fsl/, maxprob-thr25) are combined into one category map on the
grid the location is measured on - Harvard-Oxford cortical, Harvard-Oxford subcortical,
Cerebellum-MNIfnirt. The categories, in the order that is also the CSV column order and the
tie-break of the dominant one (see LOCATION_CATEGORIES):

    infratentorial         Brain-Stem (HO) + cerebellum; the whole brainstem, midbrain included
    subcortical_gray       thalamus, caudate, putamen, pallidum, hippocampus, amygdala, accumbens
    cortex_only            HO cortical and not HO "Cerebral White Matter"
    cortex_white_boundary  HO cortical AND HO "Cerebral White Matter": the two atlases disagree
    white_matter_only      HO "Cerebral White Matter" and not HO cortical
    ventricle              HO lateral ventricle
    unlabeled              inside the brain mask, no label in any atlas

Infratentorial and subcortical gray take every voxel they claim; cortex and white matter never
override each other, the voxels both claim are their own category. That is the point of the
"boundary" category: the two Harvard-Oxford atlases are separate files whose borders are not
guaranteed to agree, and the cortical band at thr25 is generous, so assigning those voxels to
either side would hide an uncertainty that belongs to the atlas, not to the lesion.

Everything here is alignment-sensitive (the atlases are LAS, the project's templates RAS), so
`build_location_categories` goes through each image's affine and refuses an atlas it cannot
resample losslessly - see _load_atlas. docs/dev/metadata.md ("La sede della lesione") is the
reference for the schema.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
from nibabel.affines import apply_affine
from nilearn.image import resample_to_img

# In precedence order: the first is also the first CSV column after `dominant`, and when two
# categories hold exactly the same number of lesion voxels (common for lesions of a few voxels)
# the one earlier in this tuple is the dominant - np.argmax returns the first maximum. The
# category map's own values are the 1-based position in this tuple; 0 is "outside the brain".
LOCATION_CATEGORIES: tuple[str, ...] = (
    "infratentorial",
    "subcortical_gray",
    "cortex_only",
    "cortex_white_boundary",
    "white_matter_only",
    "ventricle",
    "unlabeled",
)
_VALUE_OF = {name: position for position, name in enumerate(LOCATION_CATEGORIES, start=1)}

# Which Harvard-Oxford subcortical labels make up each rule. Matched on the label name because
# the atlas indices are not a stable thing to hardcode (lessons_learned.md #11); the counts
# below are checked so a renamed/added label raises instead of silently changing a category.
_SUBCORTICAL_GRAY_STRUCTURES = ("Thalamus", "Caudate", "Putamen", "Pallidum", "Hippocampus", "Amygdala", "Accumbens")
_BRAIN_STEM_LABEL = "Brain-Stem"
_WHITE_MATTER_SUFFIX = "Cerebral White Matter"
# "Lateral Vent" and not "Lateral Ventricle": the Harvard-Oxford XML spells the left one
# "Left Lateral Ventrical".
_VENTRICLE_FRAGMENT = "Lateral Vent"
_EXPECTED_LABEL_COUNTS = {"subcortical_gray": 14, "brain_stem": 1, "white_matter": 2, "ventricle": 2}

# Tolerance for "this affine is an integer voxel map": same order as src.features.lesion's
# _AFFINE_ATOL, loose enough for float32 header round-tripping.
_ATOL = 1e-3
# A vermis label sits on the midline; anything further than this is not the vermis.
_VERMIS_MAX_ABS_X_MM = 8.0


@dataclass(frozen=True)
class LesionAtlas:
    """One atlas: its label image on the location grid's resolution and its XML label file."""

    image_path: Path
    labels_path: Path


@dataclass(frozen=True)
class LesionLocationSpec:
    """What compute_lesion_metadata needs to measure lesion location: the name of the grid (one of
    the run's `grids`) the three atlases are on, and the three atlases themselves.

    The atlas files must be the resolution of that grid - there is no resampling to a different
    resolution here, an atlas that is not an exact integer voxel map onto the grid is rejected.
    """

    grid: str
    cortical: LesionAtlas
    subcortical: LesionAtlas
    cerebellum: LesionAtlas


def location_columns(grid_name: str) -> list[str]:
    """The CSV columns location adds for one grid, in order: the dominant category first, then
    one fraction per category in LOCATION_CATEGORIES order."""
    return [f"location_dominant_{grid_name}"] + [f"location_{name}_{grid_name}" for name in LOCATION_CATEGORIES]


def build_location_categories(
    spec: LesionLocationSpec, reference_img: nib.Nifti1Image, brain_mask: np.ndarray
) -> np.ndarray:
    """The category map on reference_img's grid, raveled in C order like every other per-voxel
    array in src.features.lesion, uint8: 0 outside brain_mask, otherwise 1 + the index of the
    voxel's category in LOCATION_CATEGORIES.

    brain_mask is the raveled boolean brain mask of the same grid (load_brain_mask).
    """
    cortical, _ = _load_atlas(spec.cortical, reference_img, "cortical")
    subcortical, sub_labels = _load_atlas(spec.subcortical, reference_img, "subcortical")
    cerebellum, _ = _load_atlas(spec.cerebellum, reference_img, "cerebellum")
    if brain_mask.shape != (cortical.size,):
        raise ValueError(
            f"brain_mask has {brain_mask.shape} voxels but the location grid has {cortical.size} - "
            "it must be the raveled brain mask of the same grid"
        )

    gray = np.isin(subcortical, _values_where(sub_labels, _is_subcortical_gray, "subcortical_gray"))
    stem = np.isin(subcortical, _values_where(sub_labels, lambda n: n == _BRAIN_STEM_LABEL, "brain_stem"))
    white = np.isin(subcortical, _values_where(sub_labels, lambda n: n.endswith(_WHITE_MATTER_SUFFIX), "white_matter"))
    ventricle = np.isin(subcortical, _values_where(sub_labels, lambda n: _VENTRICLE_FRAGMENT in n, "ventricle"))
    cortex = cortical > 0
    infratentorial = stem | (cerebellum > 0)

    categories = np.zeros(cortical.shape, dtype=np.uint8)
    # Lowest to highest precedence: each assignment overrides the ones before it.
    categories[brain_mask] = _VALUE_OF["unlabeled"]
    categories[ventricle & brain_mask] = _VALUE_OF["ventricle"]
    categories[white & ~cortex & brain_mask] = _VALUE_OF["white_matter_only"]
    categories[cortex & ~white & brain_mask] = _VALUE_OF["cortex_only"]
    categories[cortex & white & brain_mask] = _VALUE_OF["cortex_white_boundary"]
    categories[gray & brain_mask] = _VALUE_OF["subcortical_gray"]
    categories[infratentorial & brain_mask] = _VALUE_OF["infratentorial"]
    return categories


def location_metrics(lesion: np.ndarray, categories: np.ndarray, grid_name: str) -> dict[str, object]:
    """One subject's location columns: the dominant category and the fraction of the lesion in
    each category.

    The fractions are over the lesion voxels inside the brain mask (the voxels whose category
    is not 0), so they sum to 1 and, when compute_lesion_metadata corrects the out-of-brain
    voxels, their denominator is exactly lesion_volume_voxels_<grid>. A lesion with no voxel
    inside the brain has no location: every column is NaN (an empty cell), the same convention
    as out_of_brain_fraction for an empty mask, never 0.0 - a column of zeros is not "nowhere".

    `dominant` is the category with the most voxels; on an exact tie the earlier one in
    LOCATION_CATEGORIES wins, deterministically (np.argmax returns the first maximum).
    """
    if lesion.shape != categories.shape:
        raise ValueError(f"lesion has {lesion.shape} voxels but the category map {categories.shape}")
    counts = np.bincount(categories[lesion], minlength=len(LOCATION_CATEGORIES) + 1)[1:]
    total = int(counts.sum())
    columns = location_columns(grid_name)
    if total == 0:
        return {column: np.nan for column in columns}
    metrics: dict[str, object] = {columns[0]: LOCATION_CATEGORIES[int(np.argmax(counts))]}
    for column, count in zip(columns[1:], counts):
        metrics[column] = int(count) / total
    return metrics


# --- atlas loading ---------------------------------------------------------------------------


def _load_atlas(atlas: LesionAtlas, reference_img: nib.Nifti1Image, name: str) -> tuple[np.ndarray, dict[int, str]]:
    """(raveled int32 label values on reference_img's grid, {value: label name}).

    Four checks, each raising - none can pass on an atlas that would put labels in the wrong
    place:
    1. the atlas is an exact integer voxel map onto the grid (a signed axis permutation plus an
       integer offset), so nearest-neighbour resampling through the affines loses and moves
       nothing; it is how a LAS atlas lands on a RAS template without ever flipping an array;
    2. per-label voxel counts are unchanged by the resampling;
    3. the voxel values are exactly the XML's indices + 1 (a value with no label, or a label with
       no voxel, means the XML and the image are not the same atlas);
    4. every "Left ..." label has its centroid on the left of the midline in world coordinates,
       every "Right ..." on the right, "Vermis ..." near the midline - what a wrong flip breaks.
    """
    labels = _read_labels(atlas.labels_path)
    if not atlas.image_path.is_file():
        raise FileNotFoundError(f"{name} atlas image not found: {atlas.image_path}")
    image = nib.load(atlas.image_path)
    _check_integer_voxel_map(image, reference_img, name)

    raw = np.rint(np.asarray(image.dataobj)).astype(np.int32)
    resampled = resample_to_img(image, reference_img, interpolation="nearest", force_resample=True, copy_header=True)
    aligned = np.rint(np.asarray(resampled.dataobj)).astype(np.int32)

    for value in np.unique(raw):
        if int((raw == value).sum()) != int((aligned == value).sum()):
            raise ValueError(f"{name} atlas: the number of voxels with value {int(value)} changed by resampling")
    present = set(np.unique(aligned).tolist()) - {0}
    if present != set(labels):
        raise ValueError(
            f"{name} atlas: voxel values {sorted(present)} are not the labels of {atlas.labels_path} "
            f"({sorted(labels)}) - values with no label: {sorted(present - set(labels))}, "
            f"labels with no voxel: {sorted(set(labels) - present)}"
        )
    _check_hemisphere_signs(aligned, reference_img.affine, labels, name)
    return aligned.ravel(), labels


def _read_labels(labels_path: Path) -> dict[int, str]:
    """{voxel value: label name} from a FSL atlas XML. The voxel value is the `index` attribute
    + 1 (0 is "no label"), not the index itself."""
    if not labels_path.is_file():
        raise FileNotFoundError(f"atlas labels file not found: {labels_path}")
    try:
        root = ET.parse(labels_path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"{labels_path} is not a readable XML file: {exc}") from exc
    labels: dict[int, str] = {}
    for element in root.iter("label"):
        value = int(element.attrib["index"]) + 1
        if value in labels:
            raise ValueError(f"{labels_path}: label index {value - 1} appears twice")
        labels[value] = (element.text or "").strip()
    if not labels:
        raise ValueError(f"no <label> entries in {labels_path}")
    return labels


def _check_integer_voxel_map(image: nib.Nifti1Image, reference_img: nib.Nifti1Image, name: str) -> None:
    if image.shape != reference_img.shape:
        raise ValueError(
            f"{name} atlas has shape {image.shape} but the location grid is {reference_img.shape} - "
            "point the config at the atlas file of the grid's resolution"
        )
    voxel_map = np.linalg.inv(reference_img.affine) @ image.affine  # atlas voxel -> grid voxel
    linear, offset = voxel_map[:3, :3], voxel_map[:3, 3]
    permutation = np.abs(np.round(linear))
    is_signed_permutation = (
        np.allclose(linear, np.round(linear), atol=_ATOL)
        and np.allclose(permutation.sum(axis=0), 1)
        and np.allclose(permutation.sum(axis=1), 1)
    )
    if not is_signed_permutation or not np.allclose(offset, np.round(offset), atol=_ATOL):
        raise ValueError(
            f"{name} atlas is not an exact integer voxel map onto the location grid (voxel map "
            f"{np.round(voxel_map, 3).tolist()}): resampling it would lose or shift labels"
        )


def _check_hemisphere_signs(aligned: np.ndarray, affine: np.ndarray, labels: dict[int, str], name: str) -> None:
    violations: list[str] = []
    for value, label in labels.items():
        world_x = float(apply_affine(affine, np.argwhere(aligned == value).mean(axis=0))[0])
        if label.startswith("Left") and not world_x < 0:
            violations.append(f"{label!r} at x={world_x:.1f}")
        elif label.startswith("Right") and not world_x > 0:
            violations.append(f"{label!r} at x={world_x:.1f}")
        elif label.startswith("Vermis") and not abs(world_x) < _VERMIS_MAX_ABS_X_MM:
            violations.append(f"{label!r} at x={world_x:.1f}")
    if violations:
        raise ValueError(
            f"{name} atlas: label(s) on the wrong side of the midline in world coordinates, "
            f"the atlas is mirrored or mislabelled: {violations}"
        )


def _is_subcortical_gray(label: str) -> bool:
    return any(label.endswith(structure) for structure in _SUBCORTICAL_GRAY_STRUCTURES)


def _values_where(labels: dict[int, str], rule: Callable[[str], bool], rule_name: str) -> list[int]:
    """The voxel values whose label matches `rule`, checked against the expected number of
    labels: a renamed or added label must raise here rather than quietly move voxels between
    categories."""
    values = [value for value, label in labels.items() if rule(label)]
    expected = _EXPECTED_LABEL_COUNTS[rule_name]
    if len(values) != expected:
        raise ValueError(
            f"subcortical atlas: {len(values)} label(s) match the {rule_name!r} rule, expected {expected} - "
            f"matched {sorted(labels[v] for v in values)}; the atlas labels changed, review the rule"
        )
    return values
