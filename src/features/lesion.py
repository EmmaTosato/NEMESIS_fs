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

from src.features.lesion_correction import zero_out_of_brain_voxels
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
    correct_out_of_brain: bool,
    brain_mask_path: Path | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str], list[str]]:
    """Build X (n_subjects x n_features), row-aligned metadata, and drop-mask.

    Returns (X, metadata, non_constant_mask, excluded_by_group,
    excluded_by_min_volume, excluded_by_out_of_brain, corrected_subjects) -
    see docs/dev/lesion_matrix.md. excluded_by_group is subjects skipped
    because their naming-derived group isn't in group_filter (None means no
    restriction). excluded_by_min_volume/excluded_by_out_of_brain are
    subjects dropped by the two optional exclusion thresholds below - empty
    list when the corresponding threshold is None (no filtering applied),
    never conflated with excluded_by_group. corrected_subjects is the
    subjects whose lesion mask actually had a voxel zeroed by
    correct_out_of_brain (empty when that flag is False). metadata always
    gains lesion_volume_voxels (reflecting correction, when applied), plus
    out_of_brain_fraction when max_out_of_brain_fraction is not None - no
    other clinical/derived field is added here, see
    src/pipeline/enrich_metadata.py, which writes them into the subject
    registry (assets/metadata/participants.csv), not into this matrix.

    min_lesion_volume_voxels/max_out_of_brain_fraction are quality filters
    applied after discovery/group_filter, using metrics computed from this
    run's own resampled/binarized voxel data (not from the subject registry,
    which may reflect a different run's grid/binarize_threshold) - None
    disables the corresponding filter entirely. correct_out_of_brain zeroes
    out-of-brain lesion voxels instead of excluding the subject - the "fix"
    counterpart to max_out_of_brain_fraction's "exclude", applied before
    min_lesion_volume_voxels so that filter sees the corrected volume.
    Raises ValueError if both correct_out_of_brain and
    max_out_of_brain_fraction are active (never combined - see
    _apply_out_of_brain_correction; also enforced at config-load time,
    src/analysis/build_config.py, but re-checked here since this function is
    callable directly, lessons_learned.md #2). brain_mask_path is read
    whenever either max_out_of_brain_fraction or correct_out_of_brain is
    active (ignored otherwise, same conditional-field convention as
    SdcMatrixConfig's representation-specific fields,
    src/analysis/build_config.py).
    """
    if correct_out_of_brain and max_out_of_brain_fraction is not None:
        raise ValueError(
            "correct_out_of_brain and max_out_of_brain_fraction cannot both be set - "
            "pick one admission strategy (zero the offending voxels, or exclude the subject)"
        )
    X_voxelwise, metadata, excluded_by_group, reference_img = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter,
    )
    X_voxelwise, metadata, corrected_subjects = _apply_out_of_brain_correction(
        X_voxelwise, metadata, reference_img, correct_out_of_brain, brain_mask_path,
    )
    X_voxelwise, metadata, excluded_by_min_volume, excluded_by_out_of_brain = _filter_by_lesion_quality(
        X_voxelwise, metadata, reference_img, min_lesion_volume_voxels, max_out_of_brain_fraction, brain_mask_path,
    )
    X, non_constant_mask = _drop_constant_features(X_voxelwise)
    return (
        X, metadata, non_constant_mask, excluded_by_group,
        excluded_by_min_volume, excluded_by_out_of_brain, corrected_subjects,
    )


def compute_lesion_volumes(
    data_root: Path,
    datasets: list[str],
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
    correct_out_of_brain: bool = False,
    brain_mask_path: Path | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Per-subject lesion_volume_voxels for every subject discovered under
    data_root/datasets (after group_filter) - the volume-only counterpart of
    compute_lesion_quality_metrics, for a consumer that doesn't need
    out_of_brain_fraction (no brain_mask_path needed unless correct_out_of_brain is
    set, so it skips that load/resample entirely when it isn't). The single
    computation src.pipeline.enrich_metadata relies on for its own
    lesion_volume_voxels column - see that module's docstring for why it no
    longer copies the value from a separately-built build_lesion_matrix.py artifact
    (a second, independently-drifting definition of the same quantity - found
    28-09-26, .claude/history/methods_changelog.md).

    correct_out_of_brain/brain_mask_path (default: disabled) apply the same
    out-of-brain voxel correction build_lesion_matrix() does
    (_apply_out_of_brain_correction) before counting - so a caller that wants this
    volume to match a production matrix built with correct_out_of_brain=true gets
    the corrected count, not a second, uncorrected definition of the same subject's
    lesion (see enrich_metadata.py's own lesion_metrics.correct_out_of_brain).

    Returns (metadata, excluded_by_group). metadata has subject_id, dataset,
    lesion_volume_voxels.
    """
    X_voxelwise, metadata, excluded_by_group, reference_img = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter,
    )
    _, metadata, _ = _apply_out_of_brain_correction(
        X_voxelwise, metadata, reference_img, correct_out_of_brain, brain_mask_path,
    )
    return metadata, excluded_by_group


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
    """Per-subject out_of_brain_fraction for every subject discovered under
    data_root/datasets (after group_filter) - no admission threshold applied here,
    unlike build_lesion_matrix()'s _filter_by_lesion_quality. Meant for inspecting
    the full distribution before picking max_out_of_brain_fraction, or for caching
    this metric (expensive: one nibabel load + resample per subject) into a CSV for
    reuse - see src/pipeline/check_lesion_quality.py.

    Returns (metadata, excluded_by_group). metadata does NOT carry
    lesion_volume_voxels (computed internally as a byproduct of discovery, but
    dropped before returning) - assets/metadata/participants.csv (written by
    src.pipeline.enrich_metadata, via compute_lesion_volumes) is the one place to
    get that value, never a second copy here (found 28-09-26: the two had drifted
    by up to 38x for some subjects, see .claude/history/methods_changelog.md).
    """
    X_voxelwise, metadata, excluded_by_group, reference_img = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter,
    )
    brain_mask = _load_and_binarize_brain_mask(brain_mask_path, reference_img)
    metadata = metadata.drop(columns=["lesion_volume_voxels"]).copy()
    metadata["out_of_brain_fraction"] = _out_of_brain_fractions(X_voxelwise, brain_mask)
    return metadata, excluded_by_group


def compute_lesion_laterality_metrics(
    data_root: Path,
    datasets: list[str],
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
    correct_out_of_brain: bool = False,
    brain_mask_path: Path | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Per-subject hemisphere voxel counts and laterality index for every subject
    discovered under data_root/datasets (after group_filter) - no side classification
    (left/right/both) applied here, only the raw counts/index a bilaterality
    threshold is calibrated and applied against downstream (see
    scripts/calibrate_lesion_side_threshold.py).

    laterality_index = (left_voxels - right_voxels) / (left_voxels + right_voxels)
    - the standard formula from the lesion/fMRI laterality-index literature
    (e.g. Wilke & Lidzba's LI-toolbox convention, applied to stroke lesion masks
    in Rorden's Gigascience LI protocol): positive means left-dominant, negative
    right-dominant, magnitude near 0 means bilateral. NaN when both counts are 0
    (a lesion confined entirely to the single midline voxel plane, or - not
    expected for a real ST subject, but not excluded here either - literally no
    lesion) - a legitimate, explicit domain case, not an error.

    correct_out_of_brain/brain_mask_path (default: disabled): same out-of-brain
    voxel correction as compute_lesion_volumes/build_lesion_matrix() - a stray
    out-of-brain voxel counted toward left_voxels/right_voxels could otherwise bias
    laterality_index for no anatomical reason.

    Returns (metadata, excluded_by_group). metadata carries subject_id, dataset,
    lesion_volume_voxels, left_voxels, right_voxels, laterality_index.
    """
    X_voxelwise, metadata, excluded_by_group, reference_img = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter,
    )
    X_voxelwise, metadata, _ = _apply_out_of_brain_correction(
        X_voxelwise, metadata, reference_img, correct_out_of_brain, brain_mask_path,
    )
    left_mask, right_mask = _hemisphere_masks(reference_img)
    X_bool = X_voxelwise.astype(bool)
    metadata = metadata.copy()
    metadata["left_voxels"] = (X_bool & left_mask).sum(axis=1, dtype=np.int64)
    metadata["right_voxels"] = (X_bool & right_mask).sum(axis=1, dtype=np.int64)
    total = (metadata["left_voxels"] + metadata["right_voxels"]).to_numpy()
    difference = (metadata["left_voxels"] - metadata["right_voxels"]).to_numpy()
    metadata["laterality_index"] = np.where(total > 0, difference / np.where(total > 0, total, 1), np.nan)
    return metadata, excluded_by_group


KNOWN_LESION_SIDES = ("left", "right", "both")


def lesion_side_from_laterality_index(laterality_index: float, threshold: float) -> str:
    """left/right/both from a laterality_index and a bilaterality threshold -
    calibrated against clinical lesion_side labels in
    scripts/calibrate_lesion_side_threshold.py (28-09-26: threshold=0.20, the
    literature default, reproduces 97.4% of 1445 clinically-labelled subjects -
    see that script's own report and .claude/history/methods_changelog.md).

    Shared by the calibration script and src.pipeline.enrich_metadata's own
    geometric fallback - one definition, not two independently-drifting copies.

    Raises ValueError for a NaN laterality_index - a subject with no computable
    laterality_index (see compute_lesion_laterality_metrics) must be filtered out
    by the caller before reaching this function, never silently classified.
    """
    if np.isnan(laterality_index):
        raise ValueError(
            "lesion_side_from_laterality_index() called with a NaN laterality_index - "
            "filter these out before classifying (see compute_lesion_laterality_metrics)"
        )
    if abs(laterality_index) < threshold:
        return "both"
    return "left" if laterality_index > 0 else "right"


# Tolerance for the affine-linearity check below - same order of magnitude as
# _AFFINE_ATOL, loose enough for float32 header round-tripping, tight enough that a
# real off-diagonal rotation/shear term (never sub-micron in practice) cannot pass.
_AFFINE_DIAGONAL_ATOL = 1e-3


def _hemisphere_masks(reference_img: nib.Nifti1Image) -> tuple[np.ndarray, np.ndarray]:
    """Boolean (left, right) masks on reference_img's grid, raveled to match
    X_voxelwise's column order (same C-order .ravel() as _load_and_binarize_lesion's
    data.ravel(), since reference_img.shape is exactly X_voxelwise's per-subject
    unflattened shape).

    Left = anatomical-left of the MNI midline, Right = anatomical-right - derived
    from the first voxel axis's world coordinate (reference_img.affine), not
    assumed from array position. The exact midline plane (world-x == 0) belongs to
    neither side, excluded from both hemisphere counts (a single voxel-thick slice,
    not a meaningful side).

    Raises ValueError if the first voxel axis isn't purely left-right (an
    off-diagonal affine term, or first-axis orientation other than 'R'/'L') - this
    function assumes an axis-aligned MNI-style reference grid, same assumption
    load_reference_image's callers already make everywhere else in this module.
    """
    affine = reference_img.affine
    if abs(affine[0, 1]) > _AFFINE_DIAGONAL_ATOL or abs(affine[0, 2]) > _AFFINE_DIAGONAL_ATOL:
        raise ValueError(
            f"reference_img's affine has a non-zero off-diagonal term on the first row ({affine[0, :3]}) - "
            "hemisphere classification assumes an axis-aligned MNI-style grid where the first voxel axis "
            "maps directly to world-space left-right, with no rotation/shear"
        )
    orientation = nib.aff2axcodes(affine)
    if orientation[0] not in ("R", "L"):
        raise ValueError(
            f"reference_img's first axis orientation is {orientation[0]!r}, expected 'R' or 'L' - "
            "hemisphere classification assumes the first voxel axis maps to the left-right anatomical axis"
        )
    nx, ny, nz = reference_img.shape
    world_x = affine[0, 0] * np.arange(nx) + affine[0, 3]
    if orientation[0] == "L":
        world_x = -world_x  # flip so positive always means anatomical Right, regardless of storage orientation
    left_mask = np.broadcast_to((world_x < 0)[:, None, None], (nx, ny, nz)).ravel()
    right_mask = np.broadcast_to((world_x > 0)[:, None, None], (nx, ny, nz)).ravel()
    return left_mask, right_mask


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


def _apply_out_of_brain_correction(
    X_voxelwise: np.ndarray,
    metadata: pd.DataFrame,
    reference_img: nib.Nifti1Image,
    correct_out_of_brain: bool,
    brain_mask_path: Path | None,
) -> tuple[np.ndarray, pd.DataFrame, list[str]]:
    """Zero out-of-brain lesion voxels for every subject (src.features.lesion_correction)
    when correct_out_of_brain is True, recomputing lesion_volume_voxels for the corrected
    data - a no-op (metadata/lesion_volume_voxels untouched, empty corrected_subjects)
    when correct_out_of_brain is False.

    Runs before _filter_by_lesion_quality so min_lesion_volume_voxels (if set) sees the
    corrected volume, not the pre-correction one - the two are never in tension since
    correct_out_of_brain and max_out_of_brain_fraction are mutually exclusive (checked in
    build_lesion_matrix).
    """
    if not correct_out_of_brain:
        return X_voxelwise, metadata, []
    if brain_mask_path is None:
        raise ValueError(
            "correct_out_of_brain is set but brain_mask_path is None - "
            "cannot zero out-of-brain voxels without a brain mask"
        )
    brain_mask = _load_and_binarize_brain_mask(brain_mask_path, reference_img)
    X_corrected, was_corrected = zero_out_of_brain_voxels(X_voxelwise, brain_mask)
    metadata = metadata.copy()
    metadata["lesion_volume_voxels"] = X_corrected.sum(axis=1, dtype=np.int64)
    corrected_subjects = sorted(metadata.loc[was_corrected, "subject_id"])
    return X_corrected, metadata, corrected_subjects


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
