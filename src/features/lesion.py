"""Build a 2D feature matrix (n_subjects x n_features) from lesion masks.

Each subject is a flattened binary lesion volume (voxel-wise) - the notebook's
original approach. An earlier version also supported an atlas-parcellated
output shape (proportion of damage per ROI); removed 25/08/26 (project
decision - the Thiebaut de Schotten et al. 2020 parcellation-then-varimax-PCA
replication this fed is no longer pursued through this pipeline; see
management/notes/TODO.md).

Migrated from notebooks/lesion_analysis.ipynb (voxel-wise path only, cells
4-8): same algorithm, restructured into typed, independently testable
functions per src/ code standards. The notebook itself is left as-is, as the
exploratory reference.
"""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.image import resample_to_img

from src.features.subject_discovery import discover_files_by_subject
from src.retrieval.dataset import group_of


def build_lesion_matrix(
    data_root: Path,
    datasets: list[str],
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
    min_lesion_volume_voxels: int | None,
    max_out_of_brain_fraction: float | None,
    brain_mask_path: Path | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str]]:
    """Build X (n_subjects x n_features), row-aligned metadata, and drop-mask.

    Returns (X, metadata, non_constant_mask, excluded_by_group,
    excluded_by_min_volume, excluded_by_out_of_brain) - see
    docs/dev/lesion_matrix.md. excluded_by_group is subjects skipped because
    their naming-derived group isn't in group_filter (None means no
    restriction). excluded_by_min_volume/excluded_by_out_of_brain are
    subjects dropped by the two optional lesion-quality thresholds below -
    empty list when the corresponding threshold is None (no filtering
    applied), never conflated with excluded_by_group. metadata always gains
    lesion_volume_voxels, plus out_of_brain_fraction when
    max_out_of_brain_fraction is not None - no other clinical/derived field
    is added here, see src/pipeline/enrich_metadata.py, which writes them
    into the subject registry (assets/metadata/participants.csv), not into
    this matrix.

    min_lesion_volume_voxels/max_out_of_brain_fraction are quality filters
    applied after discovery/group_filter, using metrics computed from this
    run's own resampled/binarized voxel data (not from the subject registry,
    which may reflect a different run's grid/binarize_threshold) - None
    disables the corresponding filter entirely. brain_mask_path is read only
    when max_out_of_brain_fraction is not None (ignored otherwise, same
    conditional-field convention as SdcMatrixConfig's representation-specific
    fields, src/analysis/build_config.py).
    """
    X_voxelwise, metadata, excluded_by_group, reference_img = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter,
    )
    X_voxelwise, metadata, excluded_by_min_volume, excluded_by_out_of_brain = _filter_by_lesion_quality(
        X_voxelwise, metadata, reference_img, min_lesion_volume_voxels, max_out_of_brain_fraction, brain_mask_path,
    )
    X, non_constant_mask = _drop_constant_features(X_voxelwise)
    return X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain


def compute_lesion_quality_metrics(
    data_root: Path,
    datasets: list[str],
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
    brain_mask_path: Path,
) -> tuple[pd.DataFrame, list[str]]:
    """Per-subject lesion_volume_voxels and out_of_brain_fraction for every subject
    discovered under data_root/datasets (after group_filter) - no admission threshold
    applied here, unlike build_lesion_matrix()'s _filter_by_lesion_quality. Meant for
    inspecting the full distribution before picking
    min_lesion_volume_voxels/max_out_of_brain_fraction, or for caching these metrics
    (expensive: one nibabel load + resample per subject) into a CSV for reuse - see
    scripts/check_lesion_quality.py.

    Returns (metadata, excluded_by_group). metadata always carries
    out_of_brain_fraction (unlike build_lesion_matrix's metadata, where that column
    only appears when max_out_of_brain_fraction is active) - computing both metrics
    for every subject is the whole point of this function.
    """
    X_voxelwise, metadata, excluded_by_group, reference_img = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter,
    )
    brain_mask = _load_and_binarize_brain_mask(brain_mask_path, reference_img)
    metadata = metadata.copy()
    metadata["out_of_brain_fraction"] = _out_of_brain_fractions(X_voxelwise, brain_mask)
    return metadata, excluded_by_group


def _voxelwise_matrix_with_volume(
    data_root: Path,
    datasets: list[str],
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
) -> tuple[np.ndarray, pd.DataFrame, list[str], nib.Nifti1Image]:
    """Discovery + binarization + lesion_volume_voxels - everything
    build_lesion_matrix() needs before the lesion-quality filters and
    dropping constant features. Also returns reference_img (the loaded,
    not-yet-resampled reference grid) - _filter_by_lesion_quality needs it to
    resample brain_mask_path onto the same grid as X_voxelwise's columns."""
    lesion_files, excluded_by_group = _discover_lesion_files(data_root, datasets, lesion_glob, group_filter)
    reference_img = load_reference_image(reference_template_path)
    X_voxelwise, metadata = _stack_voxel_matrix(
        lesion_files, reference_img, resample_interpolation, binarize_threshold
    )
    # Always a real voxel count (X_voxelwise is strictly binary) - explicit
    # dtype=int64 rather than relying on numpy's own upcasting of a uint8 sum
    # (lessons_learned.md #13 - never assume a reduction upcasts on its own, even where it
    # currently does).
    metadata = metadata.copy()
    metadata["lesion_volume_voxels"] = X_voxelwise.sum(axis=1, dtype=np.int64)

    # AUDIT_FINDINGS.md #68: binarize_threshold is range-validated at config load time
    # (0.0-1.0 inclusive, src/analysis/build_config.py), but 1.0 itself is a valid-looking
    # yet degenerate value - resampled lesion values are typically in [0, 1] and a strict
    # `>` comparison means nothing ever exceeds exactly 1.0, silently binarizing every
    # subject's mask to all-zero. Checked in aggregate (every subject, not one) since a
    # single subject with 0 lesion voxels is a legitimate per-subject case (lesson #6) -
    # the whole cohort having zero is not, for any real stroke (ST) cohort.
    if (metadata["lesion_volume_voxels"] == 0).all():
        raise ValueError(
            f"every subject's lesion mask binarized to zero voxels (binarize_threshold={binarize_threshold!r}) - "
            "resampled lesion values are typically in [0, 1], so a threshold of 1.0 (or higher) means the "
            "'>' comparison never passes for any subject; check binarize_threshold in the config"
        )
    return X_voxelwise, metadata, excluded_by_group, reference_img


def _filter_by_lesion_quality(
    X_voxelwise: np.ndarray,
    metadata: pd.DataFrame,
    reference_img: nib.Nifti1Image,
    min_lesion_volume_voxels: int | None,
    max_out_of_brain_fraction: float | None,
    brain_mask_path: Path | None,
) -> tuple[np.ndarray, pd.DataFrame, list[str], list[str]]:
    """Drop subjects failing either optional lesion-quality threshold.

    Runs on the full pre-constant-drop voxel grid - out_of_brain_fraction
    needs X_voxelwise's columns at their real spatial positions, which
    _drop_constant_features would otherwise already have removed/reindexed.

    Both thresholds are admission boundaries (a subject is kept iff
    lesion_volume_voxels >= min_lesion_volume_voxels and
    out_of_brain_fraction <= max_out_of_brain_fraction) - None disables the
    respective check entirely, not just relaxes it to a permissive default.
    Raises ValueError if every subject is filtered out (an empty matrix would
    otherwise proceed silently into _drop_constant_features/save_matrix).
    """
    metadata = metadata.reset_index(drop=True)
    keep = np.ones(len(metadata), dtype=bool)
    excluded_by_min_volume: list[str] = []
    excluded_by_out_of_brain: list[str] = []

    if min_lesion_volume_voxels is not None:
        too_small = metadata["lesion_volume_voxels"].to_numpy() < min_lesion_volume_voxels
        excluded_by_min_volume = sorted(metadata.loc[too_small, "subject_id"])
        keep &= ~too_small

    if max_out_of_brain_fraction is not None:
        if brain_mask_path is None:
            raise ValueError(
                "max_out_of_brain_fraction is set but brain_mask_path is None - "
                "cannot compute out_of_brain_fraction without a brain mask"
            )
        brain_mask = _load_and_binarize_brain_mask(brain_mask_path, reference_img)
        fractions = _out_of_brain_fractions(X_voxelwise, brain_mask)
        metadata = metadata.copy()
        metadata["out_of_brain_fraction"] = fractions
        too_contaminated = fractions > max_out_of_brain_fraction
        excluded_by_out_of_brain = sorted(metadata.loc[too_contaminated, "subject_id"])
        keep &= ~too_contaminated

    X_voxelwise = X_voxelwise[keep]
    metadata = metadata.loc[keep].reset_index(drop=True)

    if len(metadata) == 0:
        raise ValueError(
            "no subjects remain after applying lesion-quality filters "
            f"(min_lesion_volume_voxels={min_lesion_volume_voxels!r}, "
            f"max_out_of_brain_fraction={max_out_of_brain_fraction!r}) - relax the threshold(s), "
            "or check that they aren't misconfigured"
        )

    return X_voxelwise, metadata, excluded_by_min_volume, excluded_by_out_of_brain


def _load_and_binarize_brain_mask(brain_mask_path: Path, reference_img: nib.Nifti1Image) -> np.ndarray:
    """Boolean brain-mask array on reference_img's grid, flattened.

    Always resampled with nearest-neighbor interpolation regardless of the
    run's own resample_interpolation - a binary mask, like a lesion mask,
    should never be interpolated any other way (see
    _load_and_binarize_lesion's own re-binarization safety net for the same
    reasoning).
    """
    if not brain_mask_path.is_file():
        raise FileNotFoundError(f"brain_mask_path not found: {brain_mask_path}")
    img = nib.load(brain_mask_path)
    if _needs_resample(img, reference_img):
        img = resample_to_img(img, reference_img, interpolation="nearest", force_resample=True, copy_header=True)
    return (img.get_fdata() > 0.5).ravel()


def _out_of_brain_fractions(X_voxelwise: np.ndarray, brain_mask: np.ndarray) -> np.ndarray:
    """Fraction of each subject's lesion voxels falling outside brain_mask.

    0.0 for a subject with zero lesion voxels (a legitimate per-subject case,
    see _voxelwise_matrix_with_volume) - vacuously true, since no lesion
    voxels means none are outside the brain either; never NaN, so the result
    is always safe to compare against max_out_of_brain_fraction.
    """
    outside_brain = ~brain_mask
    lesion_voxel_counts = X_voxelwise.sum(axis=1)
    outside_counts = (X_voxelwise.astype(bool) & outside_brain).sum(axis=1)
    fractions = np.zeros(X_voxelwise.shape[0], dtype=np.float64)
    has_lesion = lesion_voxel_counts > 0
    fractions[has_lesion] = outside_counts[has_lesion] / lesion_voxel_counts[has_lesion]
    return fractions


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


def _discover_lesion_files(
    data_root: Path, datasets: list[str], lesion_glob: str, group_filter: list[str] | None
) -> tuple[dict[str, dict[str, Path]], list[str]]:
    """One entry per dataset: {subject_id: lesion_path}, restricted to
    group_filter, sanity-checked against how many (group-filtered) subject
    folders actually exist - see docs/dev/lesion_matrix.md for how the
    subject-folder glob is derived and why group_of() validates
    unconditionally here.

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
        # Checked before group_filter narrows the list (unreachable dataset vs. a
        # legitimate 0-subjects-in-group case - see docs/dev/lesion_matrix.md).
        if not subject_dirs:
            raise FileNotFoundError(
                f"{dataset}: no subject directories found under {dataset_root} matching "
                f"{subject_glob!r} - check 'datasets'/'data_root' in the config, or run "
                "retrieve_data.py first if this dataset hasn't been retrieved yet"
            )
        # group_of() validates unconditionally, not only when group_filter is set -
        # AUDIT_FINDINGS.md #46, see docs/dev/lesion_matrix.md.
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

    Every subject's lesion mask is resampled onto this image's grid if its
    own shape or affine differs (see _needs_resample). Caller-supplied on
    purpose, not derived implicitly (see docs/dev/lesion_matrix.md). Public
    so callers that only need the grid don't have to re-run full lesion
    discovery/validation via build_lesion_matrix.
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


def _drop_constant_features(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    non_constant_mask = X.min(axis=0) != X.max(axis=0)
    return X[:, non_constant_mask], non_constant_mask
