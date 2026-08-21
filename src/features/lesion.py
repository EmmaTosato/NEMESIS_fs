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

from src.features.subject_discovery import discover_files_by_subject
from src.retrieval.dataset import group_of

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
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    parcellate: bool,
    group_filter: list[str] | None,
    atlas_path: Path | None = None,
    parcel_aggregation: str | None = None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, np.ndarray | None, list[str]]:
    """Build X (n_subjects x n_features), row-aligned metadata, and drop-mask.

    Returns (X, metadata, non_constant_mask, parcel_ids, excluded_by_group).
    parcel_ids is None iff parcellate=False (voxel-wise has no parcel
    identity to report) - otherwise it holds the atlas label id behind each
    column of X, already filtered to the columns that survived the
    constant-feature drop. excluded_by_group is the list of subjects skipped
    because their naming-derived group (src.retrieval.dataset.group_of)
    isn't in group_filter - see _discover_lesion_files. group_filter=None
    means no restriction (only correct for datasets known not to mix
    groups - see src/features/subject_discovery.py).

    metadata always gains one column beyond subject_id/dataset:
    lesion_volume_voxels (a real voxel count, computed from the voxel-wise
    matrix before any parcellation - see below). No other clinical/derived
    field is added here - lesion_side/NIHSS/age/... come from a separate,
    dedicated join tool against this function's own output (see
    src/pipeline/enrich_lesion_metadata.py), not from this function.
    """
    _validate_parcellation_args(parcellate, atlas_path, parcel_aggregation)

    X_voxelwise, metadata, excluded_by_group = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter,
    )

    parcel_ids: np.ndarray | None = None
    if parcellate:
        # Reloaded rather than threaded through _voxelwise_matrix_with_volume's return -
        # cheap (a single nib.load), and keeps that shared helper's signature focused on what
        # both its callers (this function, recompute_lesion_volume) actually need.
        reference_img = load_reference_image(reference_template_path)
        atlas_labels, parcel_ids = load_and_resample_atlas(atlas_path, reference_img)
        aggregation_fn = PARCEL_AGGREGATIONS[parcel_aggregation]
        X_raw = _parcellate_matrix(X_voxelwise, atlas_labels, parcel_ids, aggregation_fn)
    else:
        X_raw = X_voxelwise

    X, non_constant_mask = _drop_constant_features(X_raw)
    if parcellate:
        parcel_ids = parcel_ids[non_constant_mask]

    return X, metadata, non_constant_mask, parcel_ids, excluded_by_group


def _voxelwise_matrix_with_volume(
    data_root: Path,
    datasets: list[str],
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
) -> tuple[np.ndarray, pd.DataFrame, list[str]]:
    """Discovery + binarization + lesion_volume_voxels - the first half of
    build_lesion_matrix(), before the optional parcellation branch."""
    lesion_files, excluded_by_group = _discover_lesion_files(data_root, datasets, lesion_glob, group_filter)
    reference_img = load_reference_image(reference_template_path)
    X_voxelwise, metadata = _stack_voxel_matrix(
        lesion_files, reference_img, resample_interpolation, binarize_threshold
    )
    # Always a real voxel count (X_voxelwise is strictly binary, pre-parcellation) - explicit
    # dtype=int64 rather than relying on numpy's own upcasting of a uint8 sum
    # (lessons_learned.md #13 - never assume a reduction upcasts on its own, even where it
    # currently does).
    metadata = metadata.copy()
    metadata["lesion_volume_voxels"] = X_voxelwise.sum(axis=1, dtype=np.int64)
    return X_voxelwise, metadata, excluded_by_group


# Tolerance for the affine comparison below - looser than float equality (nibabel
# round-trips affines through float32 headers on some writers, and a "same grid"
# affine can differ by sub-micron rounding noise that carries no real physical
# meaning), tight enough that no real registration/resampling difference (always
# at least whole fractions of a mm) could pass unnoticed.
_AFFINE_ATOL = 1e-3


def _needs_resample(img: nib.Nifti1Image, reference_img: nib.Nifti1Image) -> bool:
    """True if `img` is not already on `reference_img`'s exact voxel grid -
    same shape AND same affine, not shape alone (see docstrings below: two
    images can share a shape while their affines place that same array of
    voxels at different physical coordinates - e.g. a different origin or
    orientation at the same resolution - which a shape-only check silently
    treats as 'already aligned').
    """
    return img.shape != reference_img.shape or not np.allclose(img.affine, reference_img.affine, atol=_AFFINE_ATOL)


def load_and_resample_atlas(
    atlas_path: Path, reference_img: nib.Nifti1Image
) -> tuple[np.ndarray, np.ndarray]:
    """Load a label atlas and resample it (nearest) onto reference_img's grid.

    Nearest is forced regardless of the lesion masks' resample_interpolation:
    a label atlas holds discrete parcel ids, not continuous intensities - any
    other interpolation would invent label values that match no real parcel.

    Resamples whenever the atlas isn't already on reference_img's exact grid
    (_needs_resample: shape AND affine, not shape alone - a same-shape atlas
    with a different affine would otherwise be used as-is, silently
    mislabeling every voxel against the wrong physical location).

    Returns (atlas_labels, parcel_ids): atlas_labels is the resampled 3D
    integer label volume; parcel_ids is the sorted list of non-zero labels
    found in it (0 is background, excluded), which fixes the column order
    used everywhere else in this module.
    """
    atlas_img = nib.load(atlas_path)
    if _needs_resample(atlas_img, reference_img):
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


def _discover_lesion_files(
    data_root: Path, datasets: list[str], lesion_glob: str, group_filter: list[str] | None
) -> tuple[dict[str, dict[str, Path]], list[str]]:
    """One entry per dataset: {subject_id: lesion_path}, restricted to
    group_filter, sanity-checked against how many (group-filtered) subject
    folders actually exist. Where subject folders sit relative to
    dataset_root differs by local retrieval layout (subject-first vs
    pipeline-first, see src.retrieval.output_layout) - rather than assuming
    they're dataset_root's immediate children (true only for the older
    subject-first layout), the subject-folder glob is derived from
    lesion_glob itself: the last path segment that is exactly "*" (the
    subject-id wildcard, not a compound filename pattern like
    "*_label-lesion_mask.nii.gz").

    The subject-dir count used for the sanity check is itself restricted to
    group_filter (see src.features.subject_discovery) - comparing against
    every folder regardless of group would break as soon as a dataset mixes
    groups under this pipeline/object (not the case today for manual_masks -
    a healthy control has no lesion to mask - but not a guarantee this code
    should silently assume).

    Returns (lesion_files, excluded_by_group) - excluded_by_group merges the
    per-dataset exclusion lists, for the caller to log explicitly.
    """
    segments = lesion_glob.split("/")
    bare_wildcard_indices = [i for i, seg in enumerate(segments) if seg == "*"]
    if not bare_wildcard_indices:
        raise ValueError(
            f"lesion_glob {lesion_glob!r} has no bare '*' path segment identifying where "
            "subject folders sit - cannot sanity-check subject count"
        )
    subject_glob = "/".join(segments[: bare_wildcard_indices[-1] + 1])

    lesion_files: dict[str, dict[str, Path]] = {}
    excluded_by_group: list[str] = []
    for dataset in datasets:
        dataset_root = data_root / dataset
        by_subject, excluded = discover_files_by_subject(data_root, dataset, lesion_glob, group_filter)
        excluded_by_group.extend(excluded)

        subject_dirs = [p.name for p in dataset_root.glob(subject_glob) if p.is_dir()]
        # Checked before group_filter narrows the list: an empty result here means the
        # dataset itself is unreachable (wrong path/name in config, or never retrieved),
        # not a legitimate "this dataset has 0 subjects in the requested group" - that
        # case is only distinguishable *after* filtering, and stays silent-safe (a dataset
        # that genuinely has none of the requested group contributes 0 rows, same as
        # today). Path.glob on a missing/empty directory returns [] with no exception, so
        # without this check a typo'd dataset name silently contributes 0 subjects instead
        # of failing loudly (both by_subject and subject_dirs land on the same empty list,
        # so the len-mismatch check below never fires either).
        if not subject_dirs:
            raise FileNotFoundError(
                f"{dataset}: no subject directories found under {dataset_root} matching "
                f"{subject_glob!r} - check 'datasets'/'data_root' in the config, or run "
                "retrieve_data.py first if this dataset hasn't been retrieved yet"
            )
        # AUDIT_FINDINGS.md #46: group_of() must validate every subject_dirs entry's
        # naming regardless of group_filter (lesson #4/#26's twin gap here) - skipping
        # the call whenever group_filter is None (the common "this dataset doesn't mix
        # groups" case) let a malformed folder name (e.g. "sub_STUNIPD0099", underscore
        # instead of a dash) through silently instead of raising.
        dir_groups = {s: group_of(s) for s in subject_dirs}
        if group_filter is not None:
            subject_dirs = [s for s in subject_dirs if dir_groups[s] in group_filter]
        # one lesion mask expected per (group-filtered) subject dir; stop on mismatch
        # rather than silently proceeding with missing or duplicated data
        if len(by_subject) != len(subject_dirs):
            raise ValueError(
                f"{dataset}: {len(subject_dirs)} subject dirs but {len(by_subject)} lesion masks "
                f"found matching {lesion_glob!r} - check the retrieval report"
            )
        lesion_files[dataset] = by_subject
    return lesion_files, sorted(set(excluded_by_group))


def load_reference_image(reference_template_path: Path) -> nib.Nifti1Image:
    """Load the explicit reference template that fixes the common voxel grid.

    Every subject's lesion mask (and, when parcellate=True, the atlas) is
    resampled onto this image's grid if its own shape or affine differs (see
    _needs_resample) - shape alone isn't enough: two images can share a shape
    while their affines place that voxel array at different physical
    coordinates. Caller-supplied
    on purpose - picking "the first lesion file found" as an implicit
    reference silently ties the common grid to whichever file happens to sort
    first, with no guarantee it's the resolution/space actually wanted (e.g.
    a canonical MNI152 2mm template).

    Public so callers that only need the grid (e.g. the build_lesion_matrix
    pipeline script, to reconstruct QC volumes after the fact) don't have to
    re-run full lesion discovery/validation via build_lesion_matrix.
    """
    if not reference_template_path.is_file():
        raise FileNotFoundError(f"reference_template_path not found: {reference_template_path}")
    return nib.load(reference_template_path)


def _load_and_binarize_lesion(
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str, binarize_threshold: float
) -> np.ndarray:
    img = nib.load(path)
    if _needs_resample(img, reference_img):
        img = resample_to_img(
            img, reference_img, interpolation=resample_interpolation, force_resample=True, copy_header=True
        )
    # re-binarize: interpolation/registration can leave near-1/near-0 values
    data = img.get_fdata() > binarize_threshold
    return data.ravel().astype(np.uint8)


def _stack_voxel_matrix(
    lesion_files: dict[str, dict[str, Path]],
    reference_img: nib.Nifti1Image,
    resample_interpolation: str,
    binarize_threshold: float,
) -> tuple[np.ndarray, pd.DataFrame]:
    subject_ids: list[str] = []
    dataset_labels: list[str] = []
    vectors: list[np.ndarray] = []

    for dataset, by_subject in lesion_files.items():
        for subject_id in sorted(by_subject):
            f = by_subject[subject_id]
            vectors.append(_load_and_binarize_lesion(f, reference_img, resample_interpolation, binarize_threshold))
            subject_ids.append(subject_id)
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
