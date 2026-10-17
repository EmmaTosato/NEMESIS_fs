"""Voxelwise t-maps of a PCA run's components, computed in the background and cached on disk.

The Embedding Explorer's "Mappe delle componenti" panel shows, for a `pca` run of dim_reduction.py, where in
the brain each component lives, as in section 6 of notebooks/pipeline_building/thiebaut_2020_replication.ipynb:
for every voxel of the source matrix, `values ~ intercept + all component scores` is fitted over the subjects
and the t-statistic of each component is the map (src/analysis/covariance_pca.py::component_t_maps). The same
pass also fits two random halves of the subjects, whose maps are correlated to say whether a map is found again
(its reproducibility).

One pass over a voxelwise matrix (5845 x 227235 float32 for the voxelwise disconnection) takes minutes, so the
maps are computed once in a worker thread (src/analysis/background_cache.py) and kept under `cache_dir`. An entry
is named after the content it comes from - the scores, the subject ids, the shape/dtype/sampled rows of the
source matrix, the seed - so a rebuilt matrix or a new run gets a new entry, never a stale one. What it cannot
see is a source matrix whose subjects are the same but whose *values* changed outside the sampled rows since the
scores were computed from it: the caller can compare the matrix's modification time with the run's.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from src.analysis.background_cache import BackgroundDiskCache
from src.analysis.covariance_pca import component_t_maps, map_reproducibility, positive_peak_signs
from src.utils.artifacts import MATRIX_FILENAME, METADATA_FILENAME, read_run_config

# The mask of the source matrix's columns over the template grid, saved with it by build_*_matrix.py (voxelwise).
MASK_FILENAME = "non_constant_mask.npy"

# Seed of the split of the subjects in two halves: fixed, so the reproducibility of a run is repeatable.
SPLIT_SEED = 0

# Bumped when what is computed or how it is oriented changes, so older entries are not served.
_ALGORITHM = "t-maps-1"
_T_FILENAME = "t.npy"
_REPRODUCIBILITY_FILENAME = "reproducibility.npy"
_SUMMARY_FILENAME = "summary.json"
_SAMPLED_ROWS = 64


@dataclass(frozen=True)
class MapGeometry:
    """Where the columns of a voxelwise matrix are in the brain: `mask` (flat, over the whole template grid)
    marks the voxels that are columns of the matrix, in C order; `shape` and `affine` are the grid's."""

    mask: np.ndarray
    shape: tuple[int, int, int]
    affine: np.ndarray


@dataclass(frozen=True)
class ComponentMapSet:
    """`t` is (n_components, n_columns) float32, memory-mapped, each component oriented so that its voxel of
    largest |t| is positive (the sign of a component is arbitrary). `reproducibility` is, per component, the
    correlation across voxels between the maps of two random halves of the subjects. `n_degenerate_voxels` is
    how many voxels of the whole-sample fit had no residual variance (t set to 0, never dropped)."""

    t: np.ndarray
    reproducibility: np.ndarray
    n_degenerate_voxels: int


def load_map_geometry(source_dir: Path) -> MapGeometry:
    """The geometry of the voxelwise matrix in `source_dir`: its `non_constant_mask.npy` and the header of the
    reference template its config.md names (`reference_template_path`, the grid the matrix was built on).

    Raises ValueError, with the cause, for a matrix that is not voxelwise (no mask or no reference template: a
    parcellated, streamline or functional-connectivity matrix has no brain map) or a mask that does not fit the
    template; FileNotFoundError for a missing mask/template file."""
    mask_path = source_dir / MASK_FILENAME
    if not mask_path.is_file():
        raise ValueError(f"{source_dir} has no {MASK_FILENAME}: only a voxelwise matrix can be drawn as a brain map")
    config = read_run_config(source_dir)
    template_path = config.get("reference_template_path")
    if not template_path:
        raise ValueError(f"{source_dir}'s config.md has no reference_template_path: only a voxelwise matrix can be drawn as a brain map")
    template = nib.load(template_path)
    mask = np.load(mask_path)
    if mask.ndim != 1 or mask.dtype != bool or mask.size != int(np.prod(template.shape)):
        raise ValueError(f"{mask_path}: mask {mask.shape} {mask.dtype} does not fit the grid {template.shape} of {template_path}")
    return MapGeometry(mask=mask, shape=tuple(int(n) for n in template.shape), affine=np.asarray(template.affine))


def to_volume(values: np.ndarray, geometry: MapGeometry) -> nib.Nifti1Image:
    """`values` (one per column of the matrix) as a 3D image on the template grid, 0 outside the mask.
    Raises ValueError if their number is not the mask's."""
    if values.shape != (int(geometry.mask.sum()),):
        raise ValueError(f"{values.shape} values for a mask of {int(geometry.mask.sum())} voxels")
    volume = np.zeros(geometry.mask.size, dtype=np.float32)
    volume[geometry.mask] = values
    return nib.Nifti1Image(volume.reshape(geometry.shape), geometry.affine)


class ComponentMapStore:
    """The component maps of PCA runs, in a BackgroundDiskCache under `cache_dir`."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache = BackgroundDiskCache(cache_dir, "component-maps")

    def request(self, source_dir: Path, scores: np.ndarray, subject_ids: Sequence[str]) -> ComponentMapSet | None:
        """The maps of the components whose subject-by-component `scores` were computed from the matrix in
        `source_dir`, or None while they are still being computed (the first call starts the computation).

        `subject_ids` are the rows of `scores` in order and must be the source matrix's own, in the same order:
        the regression pairs row i of the scores with row i of the matrix, so another order would give a map
        that looks fine and is wrong. Raises ValueError for a mismatch (subjects, order, number of rows) or too
        few subjects for the number of components; whatever the computation raised, once (the next call retries)."""
        matrix = np.load(source_dir / MATRIX_FILENAME, mmap_mode="r")
        _require_same_subjects(source_dir, matrix, scores, subject_ids)
        key = _cache_key(matrix, scores, subject_ids)
        directory = self._cache.request(key, lambda temporary: _compute_into(temporary, matrix, scores))
        return None if directory is None else _load(directory)


def _require_same_subjects(source_dir: Path, matrix: np.ndarray, scores: np.ndarray, subject_ids: Sequence[str]) -> None:
    if scores.ndim != 2 or matrix.ndim != 2:
        raise ValueError(f"scores {scores.shape} and matrix {matrix.shape} must both be 2D")
    if not (matrix.shape[0] == scores.shape[0] == len(subject_ids)):
        raise ValueError(
            f"the run has {scores.shape[0]} scores and {len(subject_ids)} subject ids but the source matrix "
            f"{source_dir} has {matrix.shape[0]} rows: it is not the matrix this run was computed from"
        )
    source_ids = pd.read_csv(source_dir / METADATA_FILENAME)["subject_id"].tolist()
    if source_ids != list(subject_ids):
        first = next(i for i, (a, b) in enumerate(zip(source_ids, subject_ids)) if a != b)
        raise ValueError(
            f"the subjects of the source matrix {source_dir} are not the run's, in the same order (first difference at "
            f"row {first}: {source_ids[first]} against {subject_ids[first]}): it is not the matrix this run was computed from"
        )


def _cache_key(matrix: np.ndarray, scores: np.ndarray, subject_ids: Sequence[str]) -> str:
    sampled = np.linspace(0, matrix.shape[0] - 1, num=min(_SAMPLED_ROWS, matrix.shape[0]), dtype=int)
    digest = hashlib.sha1()
    digest.update(f"{_ALGORITHM}|{SPLIT_SEED}|{matrix.shape}|{matrix.dtype}|{scores.shape}|".encode())
    digest.update(np.ascontiguousarray(scores, dtype=np.float64).tobytes())
    digest.update("\n".join(subject_ids).encode())
    for row in sampled:
        digest.update(np.ascontiguousarray(matrix[row]).tobytes())
    return f"{_ALGORITHM}-{digest.hexdigest()[:16]}"


def _compute_into(directory: Path, matrix: np.ndarray, scores: np.ndarray) -> None:
    order = np.random.default_rng(SPLIT_SEED).permutation(matrix.shape[0])
    half_a, half_b = np.sort(order[: matrix.shape[0] // 2]), np.sort(order[matrix.shape[0] // 2 :])
    maps_full, maps_a, maps_b = component_t_maps(matrix, scores, [np.arange(matrix.shape[0]), half_a, half_b])
    signs = positive_peak_signs(maps_full.t)  # the same signs for the whole sample and the halves
    reproducibility = map_reproducibility(maps_a.t * signs[:, None], maps_b.t * signs[:, None])
    np.save(directory / _T_FILENAME, (maps_full.t * signs[:, None]).astype(np.float32))
    np.save(directory / _REPRODUCIBILITY_FILENAME, reproducibility)
    (directory / _SUMMARY_FILENAME).write_text(json.dumps({"n_degenerate_voxels": maps_full.n_degenerate_voxels}))
    logging.info("component maps: %d components over %d voxels computed", scores.shape[1], matrix.shape[1])


def _load(directory: Path) -> ComponentMapSet:
    return ComponentMapSet(
        t=np.load(directory / _T_FILENAME, mmap_mode="r"),
        reproducibility=np.load(directory / _REPRODUCIBILITY_FILENAME),
        n_degenerate_voxels=int(json.loads((directory / _SUMMARY_FILENAME).read_text())["n_degenerate_voxels"]),
    )
