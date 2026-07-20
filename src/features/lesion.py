"""Build a 2D feature matrix (n_subjects x n_features) from lesion masks.

Two output shapes, chosen by `parcellate`:
- voxel-wise (default): each subject is a flattened binary lesion volume.
- parcellated: each subject is the proportion of damage per atlas region -
  same "proportion of damage per ROI" characterisation used in Thiebaut de
  Schotten et al. 2020 (MMP + subcortical atlas) ahead of their varimax PCA.
  The atlas is caller-supplied (`atlas_path`) - any volumetric, discrete-label
  NIfTI works, not just MMP.

Migrated from notebooks/lesion_analysis.ipynb (voxel-wise path only, cells
4-8): same algorithm, restructured into typed, independently testable
functions per src/ code standards. The notebook itself is left as-is, as the
exploratory reference.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.image import resample_to_img

# Each entry reduces a (n_subjects, n_voxels_in_parcel) block to (n_subjects,).
# Only one method exists today (binary lesion masks only support "proportion
# of damage"); kept as a registry, not hardcoded, because SDC/FC will need
# other reductions (e.g. sum, mean of continuous values) on the same
# parcellation machinery.
PARCEL_AGGREGATIONS: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "fraction_lesioned": lambda voxel_block: voxel_block.mean(axis=1),
}


def build_lesion_matrix(
    data_root: Path,
    datasets: list[str],
    reference_dataset: str,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    parcellate: bool,
    atlas_path: Path | None = None,
    parcel_aggregation: str | None = None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, np.ndarray | None]:
    """Build X (n_subjects x n_features), row-aligned metadata, and drop-mask.

    Returns (X, metadata, non_constant_mask, parcel_ids). parcel_ids is None
    iff parcellate=False (voxel-wise has no parcel identity to report) -
    otherwise it holds the atlas label id behind each column of X, already
    filtered to the columns that survived the constant-feature drop.
    """
    _validate_parcellation_args(parcellate, atlas_path, parcel_aggregation)
    if reference_dataset not in datasets:
        raise ValueError(f"reference_dataset {reference_dataset!r} must be one of {datasets}")

    lesion_files = _discover_lesion_files(data_root, datasets, lesion_glob)
    reference_img = _load_reference_image(lesion_files, reference_dataset)
    X_voxelwise, metadata = _stack_voxel_matrix(
        lesion_files, reference_img, resample_interpolation, binarize_threshold
    )

    parcel_ids: np.ndarray | None = None
    if parcellate:
        atlas_labels, parcel_ids = load_and_resample_atlas(atlas_path, reference_img)
        aggregation_fn = PARCEL_AGGREGATIONS[parcel_aggregation]
        X_raw = _parcellate_matrix(X_voxelwise, atlas_labels, parcel_ids, aggregation_fn)
    else:
        X_raw = X_voxelwise

    X, non_constant_mask = _drop_constant_features(X_raw)
    if parcellate:
        parcel_ids = parcel_ids[non_constant_mask]

    return X, metadata, non_constant_mask, parcel_ids


def load_and_resample_atlas(
    atlas_path: Path, reference_img: nib.Nifti1Image
) -> tuple[np.ndarray, np.ndarray]:
    """Load a label atlas and resample it (nearest) onto reference_img's grid.

    Nearest is forced regardless of the lesion masks' resample_interpolation:
    a label atlas holds discrete parcel ids, not continuous intensities - any
    other interpolation would invent label values that match no real parcel.

    Returns (atlas_labels, parcel_ids): atlas_labels is the resampled 3D
    integer label volume; parcel_ids is the sorted list of non-zero labels
    found in it (0 is background, excluded), which fixes the column order
    used everywhere else in this module.
    """
    atlas_img = nib.load(atlas_path)
    if atlas_img.shape != reference_img.shape:
        atlas_img = resample_to_img(
            atlas_img, reference_img, interpolation="nearest", force_resample=True, copy_header=True
        )
    atlas_labels = np.asarray(atlas_img.get_fdata()).astype(np.int64)

    parcel_ids = np.unique(atlas_labels)
    parcel_ids = parcel_ids[parcel_ids != 0]
    if parcel_ids.size == 0:
        raise ValueError(f"atlas {atlas_path} has no non-zero labels after resampling to the reference grid")

    return atlas_labels, parcel_ids


def reconstruct_parcel_volume(
    parcel_values: np.ndarray, atlas_labels: np.ndarray, parcel_ids: np.ndarray
) -> np.ndarray:
    """Paint one subject's per-parcel values back onto the atlas voxel grid.

    QC/visualisation only - not used by build_lesion_matrix. Callers (e.g. the
    build_lesion_matrix pipeline script, when save_parcellated_volumes=True)
    wrap the result in a nib.Nifti1Image with the reference affine and write
    it to disk; this function does no I/O itself.
    """
    if parcel_values.shape[0] != parcel_ids.shape[0]:
        raise ValueError(
            f"parcel_values has {parcel_values.shape[0]} entries but parcel_ids has "
            f"{parcel_ids.shape[0]} - must match"
        )
    volume = np.zeros(atlas_labels.shape, dtype=np.float64)
    for value, parcel_id in zip(parcel_values, parcel_ids):
        volume[atlas_labels == parcel_id] = value
    return volume


def _validate_parcellation_args(
    parcellate: bool, atlas_path: Path | None, parcel_aggregation: str | None
) -> None:
    if parcellate:
        if atlas_path is None or parcel_aggregation is None:
            raise ValueError("atlas_path and parcel_aggregation are both required when parcellate=True")
        if parcel_aggregation not in PARCEL_AGGREGATIONS:
            raise ValueError(
                f"unknown parcel_aggregation {parcel_aggregation!r} - "
                f"known: {sorted(PARCEL_AGGREGATIONS)}"
            )
    elif atlas_path is not None or parcel_aggregation is not None:
        raise ValueError("atlas_path/parcel_aggregation must not be set when parcellate=False")


def _discover_lesion_files(data_root: Path, datasets: list[str], lesion_glob: str) -> dict[str, list[Path]]:
    lesion_files: dict[str, list[Path]] = {}
    for dataset in datasets:
        dataset_root = data_root / dataset
        files = sorted(dataset_root.glob(lesion_glob))
        # subject dirs only - excludes root-level files like participants.tsv
        n_subject_dirs = len([p for p in dataset_root.iterdir() if p.is_dir()])
        # one lesion mask expected per subject dir; stop on mismatch rather than
        # silently proceeding with missing or duplicated data
        if len(files) != n_subject_dirs:
            raise ValueError(
                f"{dataset}: {n_subject_dirs} subject dirs but {len(files)} lesion masks "
                f"found matching {lesion_glob!r} - check the retrieval report"
            )
        lesion_files[dataset] = files
    return lesion_files


def _load_reference_image(lesion_files: dict[str, list[Path]], reference_dataset: str) -> nib.Nifti1Image:
    files = lesion_files[reference_dataset]
    if not files:
        raise ValueError(f"reference_dataset {reference_dataset!r} has no lesion files to build the reference grid from")
    return nib.load(files[0])


def _load_and_binarize_lesion(
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str, binarize_threshold: float
) -> np.ndarray:
    img = nib.load(path)
    if img.shape != reference_img.shape:
        img = resample_to_img(
            img, reference_img, interpolation=resample_interpolation, force_resample=True, copy_header=True
        )
    # re-binarize: interpolation/registration can leave near-1/near-0 values
    data = img.get_fdata() > binarize_threshold
    return data.ravel().astype(np.uint8)


def _stack_voxel_matrix(
    lesion_files: dict[str, list[Path]],
    reference_img: nib.Nifti1Image,
    resample_interpolation: str,
    binarize_threshold: float,
) -> tuple[np.ndarray, pd.DataFrame]:
    subject_ids: list[str] = []
    dataset_labels: list[str] = []
    vectors: list[np.ndarray] = []

    for dataset, files in lesion_files.items():
        for f in files:
            vectors.append(_load_and_binarize_lesion(f, reference_img, resample_interpolation, binarize_threshold))
            subject_ids.append(f.name.split("_")[0])
            dataset_labels.append(dataset)

    X = np.stack(vectors)
    metadata = pd.DataFrame({"subject_id": subject_ids, "dataset": dataset_labels})
    return X, metadata


def _parcellate_matrix(
    X_voxelwise: np.ndarray,
    atlas_labels: np.ndarray,
    parcel_ids: np.ndarray,
    aggregation_fn: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    atlas_flat = atlas_labels.ravel()
    X_parcellated = np.empty((X_voxelwise.shape[0], parcel_ids.shape[0]), dtype=np.float64)
    for column, parcel_id in enumerate(parcel_ids):
        parcel_voxel_mask = atlas_flat == parcel_id
        X_parcellated[:, column] = aggregation_fn(X_voxelwise[:, parcel_voxel_mask])
    return X_parcellated


def _drop_constant_features(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    non_constant_mask = X.min(axis=0) != X.max(axis=0)
    return X[:, non_constant_mask], non_constant_mask
