"""Build a 2D feature matrix (n_subjects x n_features) from lesion masks.

Each subject is a flattened binary lesion volume (voxel-wise) - the notebook's
original approach. An earlier version also supported an atlas-parcellated
output shape (proportion of damage per ROI); removed 25/08/26 (project
decision - the Thiebaut de Schotten et al. 2020 parcellation-then-varimax-PCA
replication this fed is no longer pursued through this pipeline; see
management/notes/TODO.md).

Migrated from notebooks/pipeline_building/lesion_matrix_build.ipynb
(voxel-wise path only): same algorithm, restructured into typed, independently testable
functions per src/ code standards. The notebook itself is left as-is, as the
exploratory reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.image import resample_to_img

from src.features.lesion_correction import zero_out_of_brain_voxels
from src.features.subject_discovery import discover_files_by_subject
from src.utils.subject_ids import group_of


def build_lesion_matrix(
    data_root: Path,
    datasets: list[str],
    reference_template_path: Path,
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
    excluded_subjects: frozenset[str],
    correct_out_of_brain: bool,
    brain_mask_path: Path | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[tuple[str, int]]]:
    """Build X (n_subjects x n_features), row-aligned metadata, and drop-mask.

    Returns (X, metadata, non_constant_mask, excluded_by_group,
    excluded_by_list, corrected_subjects) - see docs/dev/lesion_matrix.md.
    excluded_by_group is subjects skipped because their naming-derived group
    isn't in group_filter (None means no restriction). excluded_by_list is the
    subjects skipped because they appear in `excluded_subjects`, restricted to
    the ones actually discovered here - never conflated with
    excluded_by_group, and never the whole list (most of it belongs to
    datasets this run didn't touch). corrected_subjects is (subject_id,
    n_voxels_corrected) pairs for subjects whose lesion mask actually had a
    voxel zeroed by correct_out_of_brain (empty when that flag is False).
    metadata gains lesion_volume_voxels (reflecting correction, when applied)
    and no other clinical/derived field - see src/pipeline/enrich_metadata.py,
    which writes those into the subject registry
    (assets/metadata/participants.csv), not into this matrix.

    excluded_subjects is the hand-curated admission list
    (src.utils.participants.load_excluded_subjects), applied right after
    discovery/group_filter so an excluded subject's mask is never even read.
    There is deliberately no threshold-based filter here any more: which
    borderline subject to drop is decided once, by looking at
    assets/metadata/lesion_metadata.csv, and recorded in that one list which
    the SDC matrix reads too - so the two matrices cannot disagree about who
    is in (see .claude/history/methods_changelog.md).

    correct_out_of_brain zeroes out-of-brain lesion voxels, keeping the
    subject in the matrix with lesion_volume_voxels recomputed from the
    corrected data; brain_mask_path is read only when it is active (ignored
    otherwise, same conditional-field convention as SdcMatrixConfig's
    representation-specific fields, src/analysis/build_config.py).
    """
    X_voxelwise, metadata, excluded_by_group, excluded_by_list, reference_img = _voxelwise_matrix_with_volume(
        data_root, datasets, reference_template_path, lesion_glob, binarize_threshold,
        resample_interpolation, group_filter, excluded_subjects,
    )
    X_voxelwise, metadata, corrected_subjects = _apply_out_of_brain_correction(
        X_voxelwise, metadata, reference_img, correct_out_of_brain, brain_mask_path,
    )
    X, non_constant_mask = _drop_constant_features(X_voxelwise)
    return X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, corrected_subjects


@dataclass(frozen=True)
class LesionGrid:
    """One voxel grid the lesion masks are measured on, for compute_lesion_metadata.

    `name` becomes the suffix of every column this grid produces
    ("2mm" -> lesion_volume_voxels_2mm, out_of_brain_fraction_2mm, ...), so it must be
    alphanumeric: a name carrying a comma/quote would corrupt the CSV those columns are
    written to. The vocabulary is deliberately open (not a fixed {"1mm", "2mm"}) - adding a
    third grid is a config entry, not a code change.

    brain_mask_path is required, not optional: it is what both the out-of-brain fraction and
    the out-of-brain correction are measured against, and those are the whole point of
    measuring a mask on a grid at all. It must be on this same grid (resampled with
    nearest-neighbour if it isn't, see _load_and_binarize_brain_mask).
    """

    name: str
    reference_template_path: Path
    brain_mask_path: Path


def compute_lesion_metadata(
    data_root: Path,
    datasets: list[str],
    lesion_glob: str,
    binarize_threshold: float,
    resample_interpolation: str,
    group_filter: list[str] | None,
    grids: list[LesionGrid],
    correct_out_of_brain: bool,
    side_threshold: float,
) -> tuple[pd.DataFrame, list[str]]:
    """Every mask-derived per-subject metric, on every grid in `grids`, in one pass.

    The single computation src.pipeline.compute_lesion_metadata writes to
    assets/metadata/lesion_metadata.csv - see that module's docstring for the file's role.

    Returns (metadata, excluded_by_group). metadata carries subject_id, dataset, and four
    columns per grid, suffixed with that grid's own name:
    lesion_volume_voxels_<g>, out_of_brain_fraction_<g>, laterality_index_<g>, lesion_side_<g>.

    Streaming, one subject at a time - deliberately NOT built on _voxelwise_matrix_with_volume
    like build_lesion_matrix() is. That function stacks every subject's flattened volume in
    memory before computing anything, which costs ~5.3 GB on the 2mm grid (902_629 voxels x
    5853 subjects, uint8) and ~42 GB on the 1mm grid - the latter simply not runnable. Here only
    scalars are kept per subject, so the peak is one mask plus the per-grid masks (tens of MB),
    independent of cohort size.

    Each mask is read from disk once and resampled once per grid (only where _needs_resample
    says its own grid differs - the manual masks are natively 1mm, so a 1mm grid resamples
    nothing, while a 2mm grid is a nearest-neighbour subsample in which a very small lesion can
    shrink or vanish; comparing the two volumes tells a genuinely empty mask from a lesion lost
    in the resampling).

    Per grid, in this order: binarize, measure out_of_brain_fraction on the RAW mask, then
    (when correct_out_of_brain) zero the out-of-brain voxels, then count volume and laterality
    on the corrected mask. The fraction is deliberately pre-correction: correction drives it to
    0 by construction, so measuring it afterwards would make the column useless for deciding
    which subjects to exclude - which is what it exists for. Volume and laterality are
    deliberately post-correction: a voxel outside the brain is not lesion, so it must not be
    counted, nor bias the left/right split.
    """
    validate_lesion_grids(grids)
    contexts = [_grid_context(grid) for grid in grids]
    lesion_files, excluded_by_group = _discover_lesion_files(data_root, datasets, lesion_glob, group_filter)

    rows: list[dict[str, object]] = []
    for dataset in datasets:
        for subject_id, path in sorted(lesion_files[dataset].items()):
            # One disk read per subject: nibabel caches the data array on first access, so the
            # per-grid resampling below reuses it instead of re-reading the file per grid.
            img = nib.load(path)
            row: dict[str, object] = {"subject_id": subject_id, "dataset": dataset}
            for context in contexts:
                row.update(
                    _metrics_on_grid(
                        img, context, resample_interpolation, binarize_threshold,
                        correct_out_of_brain, side_threshold,
                    )
                )
            rows.append(row)

    metadata = pd.DataFrame(rows, columns=_metadata_columns(grids))
    if metadata.empty:
        raise ValueError(
            f"no subjects discovered under {data_root} for datasets={datasets} "
            f"(group_filter={group_filter!r}) - nothing to compute"
        )
    _check_some_mask_is_non_empty(metadata, grids, binarize_threshold, correct_out_of_brain)
    return metadata, excluded_by_group


def lesion_side_from_laterality_index(laterality_index: float, threshold: float) -> str:
    """left/right/both from a laterality_index and a bilaterality threshold -
    calibrated against clinical lesion_side labels in
    src/pipeline/calibrate_lesion_side_threshold.py (28-09-26: threshold=0.20, the
    literature default, reproduces 97.4% of 1445 clinically-labelled subjects on the
    2mm grid - see that script's own report and .claude/history/methods_changelog.md).

    Shared by the calibration script and compute_lesion_metadata's per-grid side
    attribution - one definition, not two independently-drifting copies.

    Raises ValueError for a NaN laterality_index - a subject with no computable
    laterality_index (see _laterality_index) must be filtered out by the caller
    before reaching this function, never silently classified.
    """
    if np.isnan(laterality_index):
        raise ValueError(
            "lesion_side_from_laterality_index() called with a NaN laterality_index - "
            "filter these out before classifying (see _laterality_index)"
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
    excluded_subjects: frozenset[str],
) -> tuple[np.ndarray, pd.DataFrame, list[str], list[str], nib.Nifti1Image]:
    """Discovery + binarization + lesion_volume_voxels - everything
    build_lesion_matrix() needs before the out-of-brain correction and
    dropping constant features. Also returns reference_img (the loaded,
    not-yet-resampled reference grid) - _apply_out_of_brain_correction needs it
    to resample brain_mask_path onto the same grid as X_voxelwise's columns.

    excluded_subjects is dropped after discovery but BEFORE any mask is read
    (_stack_voxel_matrix below), so an excluded subject costs nothing. The
    drop happens after _discover_lesion_files' own mask-count consistency
    check, which must still see the complete set: a subject deliberately kept
    out of a matrix is not a subject whose mask is missing from disk."""
    lesion_files, excluded_by_group = _discover_lesion_files(data_root, datasets, lesion_glob, group_filter)
    lesion_files, excluded_by_list = _drop_excluded_subjects(lesion_files, excluded_subjects)
    if not lesion_files or not any(lesion_files.values()):
        raise ValueError(
            f"no subjects left to build a matrix from: every discovered subject was excluded "
            f"(group_filter={group_filter!r}, {len(excluded_by_list)} on the excluded-subjects list)"
        )
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
    return X_voxelwise, metadata, excluded_by_group, excluded_by_list, reference_img


def _drop_excluded_subjects(
    lesion_files: dict[str, dict[str, Path]], excluded_subjects: frozenset[str]
) -> tuple[dict[str, dict[str, Path]], list[str]]:
    """Remove the hand-curated exclusions from the discovered masks.

    Returns (kept, dropped) - `dropped` is only the subjects actually present here, not the
    whole list: the list covers every dataset, while a run usually scopes a few, so reporting
    the whole list as "excluded by this run" would misstate what this matrix contains."""
    kept: dict[str, dict[str, Path]] = {}
    dropped: list[str] = []
    for dataset, by_subject in lesion_files.items():
        kept[dataset] = {s: path for s, path in by_subject.items() if s not in excluded_subjects}
        dropped.extend(s for s in by_subject if s in excluded_subjects)
    return kept, sorted(dropped)


def _apply_out_of_brain_correction(
    X_voxelwise: np.ndarray,
    metadata: pd.DataFrame,
    reference_img: nib.Nifti1Image,
    correct_out_of_brain: bool,
    brain_mask_path: Path | None,
) -> tuple[np.ndarray, pd.DataFrame, list[tuple[str, int]]]:
    """Zero out-of-brain lesion voxels for every subject (src.features.lesion_correction)
    when correct_out_of_brain is True, recomputing lesion_volume_voxels for the corrected
    data - a no-op (metadata/lesion_volume_voxels untouched, empty corrected_subjects)
    when correct_out_of_brain is False.

    corrected_subjects is (subject_id, n_voxels_corrected) pairs, not subject_id alone -
    "who was corrected" without "how many voxels" isn't enough to judge whether a
    correction was a 1-voxel edge artifact or a large registration problem worth
    investigating (see docs/dev/lesion_matrix.md).
    """
    if not correct_out_of_brain:
        return X_voxelwise, metadata, []
    if brain_mask_path is None:
        raise ValueError(
            "correct_out_of_brain is set but brain_mask_path is None - "
            "cannot zero out-of-brain voxels without a brain mask"
        )
    brain_mask = _load_and_binarize_brain_mask(brain_mask_path, reference_img)
    X_corrected, n_corrected_voxels = zero_out_of_brain_voxels(X_voxelwise, brain_mask)
    metadata = metadata.copy()
    metadata["lesion_volume_voxels"] = X_corrected.sum(axis=1, dtype=np.int64)
    was_corrected = n_corrected_voxels > 0
    corrected_subjects = sorted(
        zip(metadata.loc[was_corrected, "subject_id"], n_corrected_voxels[was_corrected].astype(int).tolist())
    )
    return X_corrected, metadata, corrected_subjects


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


# The four metrics compute_lesion_metadata produces per grid. Each one's column name is this
# prefix plus that grid's own name - one place, so the writer, the column order and the
# emptiness check below can never disagree about what a grid contributes.
_GRID_METRIC_PREFIXES = ("lesion_volume_voxels", "out_of_brain_fraction", "laterality_index", "lesion_side")


def validate_lesion_grids(grids: list[LesionGrid]) -> None:
    """At least one grid, alphanumeric names, no duplicates.

    Public because src.analysis.build_config calls it at config-load time, so a bad grid name
    is rejected before any mask is opened - one definition of what makes a grid name usable,
    living next to the code that turns it into a column suffix.

    Duplicate names are rejected rather than silently collapsed: two grids sharing a name
    would write the same four columns twice, the second overwriting the first, so a
    copy-pasted config entry would look like it had been honoured (lessons_learned.md #5).
    """
    if not grids:
        raise ValueError("grids is empty - compute_lesion_metadata needs at least one voxel grid")
    non_alphanumeric = sorted({grid.name for grid in grids if not grid.name.isalnum()})
    if non_alphanumeric:
        raise ValueError(
            f"grid name(s) {non_alphanumeric} are not alphanumeric - a grid name becomes a CSV "
            "column suffix, so it cannot carry a separator or quote"
        )
    names = [grid.name for grid in grids]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate grid name(s): {duplicates} - each grid writes its own columns")


@dataclass(frozen=True, eq=False)
class _GridContext:
    """Everything derived once per grid and reused for every subject: the grid itself, its
    brain mask and its two hemisphere masks. Computed once because each is a full-volume array
    (tens of MB at 1mm) whose derivation does not depend on any subject.

    eq=False: the fields are numpy arrays, whose element-wise __eq__ would make a generated
    __eq__/__hash__ either raise or return an array instead of a bool.
    """

    name: str
    reference_img: nib.Nifti1Image
    brain_mask: np.ndarray
    left_mask: np.ndarray
    right_mask: np.ndarray


def _grid_context(grid: LesionGrid) -> _GridContext:
    reference_img = load_reference_image(grid.reference_template_path)
    left_mask, right_mask = _hemisphere_masks(reference_img)
    return _GridContext(
        name=grid.name,
        reference_img=reference_img,
        brain_mask=_load_and_binarize_brain_mask(grid.brain_mask_path, reference_img),
        left_mask=left_mask,
        right_mask=right_mask,
    )


def _metrics_on_grid(
    img: nib.Nifti1Image,
    context: _GridContext,
    resample_interpolation: str,
    binarize_threshold: float,
    correct_out_of_brain: bool,
    side_threshold: float,
) -> dict[str, object]:
    """One subject's four metrics on one grid - see compute_lesion_metadata for why the
    fraction is measured before the correction and the counts after it.

    lesion_side is NaN (an empty cell, the same missing-value convention as every other
    metadata column) exactly when laterality_index is: zero lesion voxels on both sides of the
    midline, so there is no side to attribute. lesion_side_from_laterality_index is never
    called with that NaN - it raises by design rather than classify it.
    """
    lesion = _binarize_on_grid(img, context.reference_img, resample_interpolation, binarize_threshold)
    fraction = _out_of_brain_fraction(lesion, context.brain_mask)
    if correct_out_of_brain:
        corrected, _ = zero_out_of_brain_voxels(lesion[None, :], context.brain_mask)
        lesion = corrected[0]
    left_voxels = int((lesion & context.left_mask).sum())
    right_voxels = int((lesion & context.right_mask).sum())
    index = _laterality_index(left_voxels, right_voxels)
    return {
        f"lesion_volume_voxels_{context.name}": int(lesion.sum()),
        f"out_of_brain_fraction_{context.name}": fraction,
        f"laterality_index_{context.name}": index,
        f"lesion_side_{context.name}": (
            np.nan if np.isnan(index) else lesion_side_from_laterality_index(index, side_threshold)
        ),
    }


def _metadata_columns(grids: list[LesionGrid]) -> list[str]:
    """The explicit column order, grids in declaration order - also what fixes the columns of
    an empty frame, which a plain DataFrame(rows) could not know."""
    columns = ["subject_id", "dataset"]
    for grid in grids:
        columns += [f"{prefix}_{grid.name}" for prefix in _GRID_METRIC_PREFIXES]
    return columns


def _check_some_mask_is_non_empty(
    metadata: pd.DataFrame, grids: list[LesionGrid], binarize_threshold: float, correct_out_of_brain: bool
) -> None:
    """Raise if EVERY subject's volume is 0 on some grid - the same aggregate safety net
    _voxelwise_matrix_with_volume applies, per grid. A single subject with 0 voxels is a
    legitimate per-subject case (lessons_learned.md #6); a whole cohort at 0 is not, for any
    real stroke cohort, and points at a misconfigured threshold or a mask on the wrong grid.
    """
    for grid in grids:
        column = f"lesion_volume_voxels_{grid.name}"
        if not (metadata[column] == 0).all():
            continue
        causes = [
            f"binarize_threshold={binarize_threshold!r} (resampled lesion values are typically in "
            "[0, 1], so 1.0 or higher means the '>' comparison never passes for anyone)"
        ]
        if correct_out_of_brain:
            causes.append(
                f"brain_mask_path={grid.brain_mask_path} not covering this grid's brain (correction "
                "would then zero every lesion voxel)"
            )
        raise ValueError(
            f"every subject's lesion mask is empty on grid {grid.name!r} - check " + "; or ".join(causes)
        )


def _laterality_index(left_voxels: int, right_voxels: int) -> float:
    """(left - right) / (left + right) - the standard laterality-index convention from the
    lesion/fMRI literature (Wilke & Lidzba's LI-toolbox; Rorden's Gigascience LI protocol applied
    to stroke lesion masks): positive means left-dominant, negative right-dominant, magnitude near
    0 means bilateral. NaN when both counts are 0 (a lesion confined to the single midline voxel
    plane, or an empty mask): a legitimate, explicit domain case the caller must handle, not an
    error."""
    total = left_voxels + right_voxels
    if total == 0:
        return float("nan")
    return (left_voxels - right_voxels) / total


def _out_of_brain_fraction(lesion: np.ndarray, brain_mask: np.ndarray) -> float:
    """Fraction of ONE subject's lesion voxels falling outside brain_mask.

    NaN for an empty mask, deliberately: "none of its voxels are outside the brain" is a
    different fact from "it has no voxels", and reporting 0.0 would put an empty mask among the
    cleanest subjects in the very distribution used to pick an exclusion threshold.
    """
    lesion_voxels = int(lesion.sum())
    if lesion_voxels == 0:
        return float("nan")
    return int((lesion & ~brain_mask).sum()) / lesion_voxels


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
                f"{subject_glob!r} - check 'datasets'/'data_root' in the config, or copy "
                "this dataset under data_root if it isn't there yet"
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
                f"found matching {lesion_glob!r} - check the local data copy"
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


def _binarize_on_grid(
    img: nib.Nifti1Image, reference_img: nib.Nifti1Image, resample_interpolation: str, binarize_threshold: float
) -> np.ndarray:
    """One already-loaded mask, resampled onto reference_img's grid if it isn't already on it
    (_needs_resample) and binarized, raveled in the same C order as _hemisphere_masks and
    _load_and_binarize_brain_mask - boolean, so it combines with those directly.

    Takes a loaded image rather than a path because compute_lesion_metadata measures the same
    mask on several grids and must not re-read it once per grid.

    The re-binarization is not redundant with the source mask already being binary:
    interpolation/registration leave near-1/near-0 values that have to be thresholded again.
    """
    if _needs_resample(img, reference_img):
        img = resample_to_img(
            img, reference_img, interpolation=resample_interpolation, force_resample=True, copy_header=True
        )
    return (img.get_fdata() > binarize_threshold).ravel()


def _load_and_binarize_lesion(
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str, binarize_threshold: float
) -> np.ndarray:
    """uint8 (not bool) for stacking into a voxel matrix - see _stack_voxel_matrix. The
    binarization itself is _binarize_on_grid's, shared with compute_lesion_metadata rather
    than written twice."""
    return _binarize_on_grid(nib.load(path), reference_img, resample_interpolation, binarize_threshold).astype(
        np.uint8
    )


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
