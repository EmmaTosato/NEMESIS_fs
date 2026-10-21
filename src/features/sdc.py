"""Build 2D feature matrices (n_subjects x n_features) from BCBToolKit's SDC output.

The parcellated representation (one row per anatomical region, from the per-atlas CSVs) is
built by src.features.parcellated_csv.build_parcellated_matrix, shared with the parcellated
lesion matrix; this module holds the other three things built from the same bcbtoolkit/ tree,
and the admission rule they all follow (a subject needs a lesion mask registered in
assets/metadata/participants.csv AND the requested output - see that module's docstring).

The voxel-wise representation (`build_sdc_voxelwise_matrix`, added
03/09) builds a voxel-wise matrix directly from the `disconnectome-map`
`.nii.gz` (the pre-parcellation volume the `LF-disconnectome_atlas-*.csv`
files above are themselves derived from) - same resampling-onto-a-common-grid
approach as `src/features/lesion.py`'s voxel-wise lesion matrix, but the
disconnectome values are a **continuous** [0, 1] probability, never
binarized (unlike a lesion mask). `correct_out_of_brain` (added 16/10) zeroes the
voxels outside a brain mask after resampling and keeps the subject, as in the lesion
matrix: tractography leaks past the brain (median 0.80% of a map's mass, up to 15.3% over the 5845-subject cohort),
and without the correction the matrix and `compute_sdc_metadata`'s disconnection load
(which sums only inside the brain) would not describe the same quantity. Deliberately restricted to
`object_="disconnectome"` only: the equivalent for `object_="lesion"` (the
`lesion-map` .nii.gz, itself just the resampled input lesion mask BCBToolKit
used) would duplicate `build_lesion_matrix.py`'s own job from a different,
less authoritative source (`manual_masks/` is the real source; `bcbtoolkit/`
only carries a copy of it as SDC's own computation input) - not built here,
raises explicitly if requested.

The streamline representation (`build_sdc_streamline_matrix`, added 30/09) reads the
`yeh_hcp1065_streamline` CSV (`tract,streamline_ratio`) - one value per white
matter tract, the proportion of its streamlines affected. Its schema shares
nothing with the parcellated CSVs above (no `region_name`, no choice of
value column), which is why it is its own builder rather than a parameter of
`build_parcellated_matrix`. Restricted to `object_="lesion"`: BCBToolKit writes this
file only in the `LF-lesion` family, there is no `LF-disconnectome` variant
of it. Despite that name the quantity is a disconnection measure, which is
why it belongs to the s2.x (disconnectome) track - see
docs/experiments/README.md.

Unlike the parcellated CSVs, this one writes **every** tract explicitly,
zeros included (verified on the full local cohort, 30/09: all 1734 files
across the 7 datasets that have it carry the same 87 tracts in the same
order, 2-42 of them non-zero per subject). A tract missing from a subject's
CSV is therefore not the legitimate "omitted because zero" case it is for
the parcellated builder - it means a truncated or corrupt file, and raises
instead of being filled with 0.0.

`compute_sdc_metadata` (added 06/10) is not a matrix builder: it reduces each subject's
disconnectome-map to two per-subject scalars (how disconnected the subject is, overall) for
assets/metadata/sdc_metadata.csv - the disconnection counterpart of the lesion volume that
src.features.lesion.compute_lesion_metadata measures. See its own docstring.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.image import resample_to_img

from src.features.lesion import LesionGrid, load_brain_mask, load_reference_image, validate_lesion_grids
from src.features.lesion_correction import zero_out_of_brain_voxels
from src.features.parcellated_csv import (
    BCBTOOLKIT_DIR,
    discover_by_dataset,
    load_reference_regions,
    registered_subjects,
    require_finite_numeric,
    subjects_with_lesion_mask,
)

KNOWN_REPRESENTATIONS = frozenset({"parcellated", "voxelwise", "streamline"})
_VOXELWISE_SUPPORTED_OBJECTS = frozenset({"disconnectome"})
# The streamline CSV exists only in the LF-lesion family - BCBToolKit writes no
# LF-disconnectome variant of it (see module docstring).
_STREAMLINE_SUPPORTED_OBJECTS = frozenset({"lesion"})

# Fixed by the source file's own schema, not a config choice: this CSV has
# exactly one identifier column and one value column, unlike the parcellated
# CSVs' 6 interchangeable statistics (parcellated_csv.KNOWN_VALUE_COLUMNS).
STREAMLINE_ATLAS = "yeh_hcp1065_streamline"
_STREAMLINE_TRACT_COLUMN = "tract"
_STREAMLINE_VALUE_COLUMN = "streamline_ratio"

_SDC_FLAG_COLUMN = "has_sdc"

# Same tolerance as src/features/lesion.py's _AFFINE_ATOL - loose enough to
# absorb float32-header round-tripping noise, tight enough that no real
# registration/resampling difference (always whole fractions of a mm) passes
# unnoticed. Not imported from lesion.py: a private helper, and this module's
# own copy is one line - see lesson_learned.md's general stance on premature
# cross-module sharing of private helpers in this repo (src/sdc/resample.py
# already has its own third, non-tolerant variant of the same check).
_AFFINE_ATOL = 1e-3


def _needs_resample(img: nib.Nifti1Image, reference_img: nib.Nifti1Image) -> bool:
    return img.shape != reference_img.shape or not np.allclose(img.affine, reference_img.affine, atol=_AFFINE_ATOL)


def build_sdc_voxelwise_matrix(
    data_root: Path,
    datasets: list[str],
    object_: str,
    reference_template_path: Path,
    resample_interpolation: str,
    group_filter: list[str] | None,
    excluded_subjects: frozenset[str],
    correct_out_of_brain: bool,
    brain_mask_path: Path | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str], list[str], list[tuple[str, int, float]]]:
    """Build X (n_subjects x n_voxels) from the `disconnectome-map` .nii.gz -
    the pre-parcellation volume `build_parcellated_matrix`'s CSVs are themselves
    derived from. Continuous [0, 1] disconnection probability per voxel,
    never binarized - see module docstring.

    Same admission criterion as build_parcellated_matrix (a lesion mask registered in
    assets/metadata/participants.csv (has_lesion), not on the hand-curated
    exclusion list, AND the requested SDC file present), and the same
    constant-column drop as
    build_lesion_matrix.py (voxels that are identically 0.0 for every admitted
    subject - dropped to keep X a manageable size, recoverable via
    non_constant_mask).

    correct_out_of_brain zeroes every voxel outside the brain mask, after the map is
    resampled onto the reference grid and BEFORE the constant-column drop (both passes of
    `_stack_voxelwise_matrix`), so an out-of-brain voxel becomes a constant column and
    disappears. Without it, tractography that leaves the brain survives as columns: on the
    5845-subject cohort, 64110 of the 291345 non-constant columns lie outside the 2mm brain
    mask. brain_mask_path is required exactly when the flag is set and must be on (or
    nearest-resampled to) the reference grid, see `load_brain_mask`.

    Returns (X, metadata, non_constant_mask, excluded_by_group,
    excluded_by_list, excluded_no_lesion_mask, sdc_not_yet_computed,
    corrected_subjects). corrected_subjects is (subject_id, n_voxels_corrected,
    mass_removed_fraction) triples, sorted by subject_id - empty when the flag is off, and
    only the subjects that actually had a voxel zeroed when it is on. The map is a
    continuous probability, so the share of its mass that was removed (sum of the
    probability outside the brain / sum overall) says how much was lost, which a voxel
    count alone does not.
    """
    if object_ not in _VOXELWISE_SUPPORTED_OBJECTS:
        raise ValueError(
            f"object_ must be one of {sorted(_VOXELWISE_SUPPORTED_OBJECTS)} for representation='voxelwise' "
            f"(the lesion-map equivalent is already built by build_lesion_matrix.py, from its own "
            f"authoritative manual_masks/ source), got {object_!r}"
        )

    lesion_subjects, excluded_lesion, excluded_by_list = subjects_with_lesion_mask(
        datasets, group_filter, excluded_subjects
    )
    sdc_glob = f"{BCBTOOLKIT_DIR}/*/*_res-1_desc-{object_}.nii.gz"
    sdc_files, excluded_sdc = discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    admitted: dict[tuple[str, str], Path] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        # A subject on the exclusion list has its mask (it was removed from lesion_ids on purpose,
        # by subjects_with_lesion_mask), so it must not be re-reported as "no lesion mask".
        excluded_no_lesion_mask.extend(sorted(sdc_ids - lesion_ids - set(excluded_by_list)))
        sdc_not_yet_computed.extend(sorted(lesion_ids - sdc_ids))
        for subject_id in sorted(lesion_ids & sdc_ids):
            admitted[(dataset, subject_id)] = sdc_files[dataset][subject_id]

    if not admitted:
        raise ValueError(
            "no subjects admitted - the intersection of subjects with a registered lesion mask "
            f"(assets/metadata/participants.csv, has_lesion) and subjects with an SDC file "
            f"(object={object_!r}, representation='voxelwise') is empty; check 'datasets'/'data_root' "
            "in the config"
        )

    reference_img = load_reference_image(reference_template_path)
    brain_mask = _brain_mask_for_correction(correct_out_of_brain, brain_mask_path, reference_img)
    X, metadata, non_constant_mask, corrected_subjects = _stack_voxelwise_matrix(
        admitted, reference_img, resample_interpolation, brain_mask
    )
    if correct_out_of_brain and X.shape[1] == 0:
        # Only here: with the flag off the matrix is what it has always been; with it on, an empty
        # result means the brain mask removed every voxel that varied - a wrong mask, not a result.
        raise ValueError(
            f"every voxel is constant across the {X.shape[0]} admitted subject(s) once the voxels "
            f"outside {brain_mask_path} are zeroed - the matrix would have no column"
        )
    return (
        X, metadata, non_constant_mask, excluded_by_group, excluded_by_list,
        sorted(excluded_no_lesion_mask), sorted(sdc_not_yet_computed), corrected_subjects,
    )


def _brain_mask_for_correction(
    correct_out_of_brain: bool, brain_mask_path: Path | None, reference_img: nib.Nifti1Image
) -> np.ndarray | None:
    """The boolean brain mask on the reference grid when the correction is on, None when it is off.

    Raises when the flag is set without a mask (a correction that silently did nothing would
    leave a run looking corrected when it is not), when the mask is empty (it would zero every
    voxel of every subject) and, through `load_brain_mask`, when the file is missing."""
    if not correct_out_of_brain:
        return None
    if brain_mask_path is None:
        raise ValueError(
            "correct_out_of_brain is set but brain_mask_path is None - "
            "cannot zero out-of-brain voxels without a brain mask"
        )
    brain_mask = load_brain_mask(brain_mask_path, reference_img)
    if not brain_mask.any():
        raise ValueError(
            f"brain_mask_path {brain_mask_path} has no voxel inside it on the reference grid - "
            "correct_out_of_brain would zero every voxel of every subject"
        )
    return brain_mask


def build_sdc_streamline_matrix(
    data_root: Path,
    datasets: list[str],
    object_: str,
    reference_labels_path: Path,
    group_filter: list[str] | None,
    excluded_subjects: frozenset[str],
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str], list[str]]:
    """Build X (n_subjects x n_tracts, fixed = len(tract_names)) from the
    `yeh_hcp1065_streamline` CSV - one streamline_ratio per white matter
    tract. See module docstring.

    Same admission criterion as the other two builders. Alignment is by tract
    name against the fixed reference list, never by row position - the rows
    happen to be in a stable order across the whole local cohort, but nothing
    in the format guarantees it (lessons_learned.md #3).

    No column is ever dropped, even if constant across every admitted
    subject - same reasoning as build_parcellated_matrix: column j must always name
    the same tract regardless of which subjects a run admits.

    Returns (X, metadata, tract_names, excluded_by_group, excluded_by_list,
    excluded_no_lesion_mask, sdc_not_yet_computed).
    """
    if object_ not in _STREAMLINE_SUPPORTED_OBJECTS:
        raise ValueError(
            f"object_ must be one of {sorted(_STREAMLINE_SUPPORTED_OBJECTS)} for "
            f"representation='streamline' (BCBToolKit writes the {STREAMLINE_ATLAS} CSV only in the "
            f"LF-lesion family), got {object_!r}"
        )

    tract_names = load_reference_regions(reference_labels_path, column=_STREAMLINE_TRACT_COLUMN)

    lesion_subjects, excluded_lesion, excluded_by_list = subjects_with_lesion_mask(
        datasets, group_filter, excluded_subjects
    )
    sdc_glob = f"{BCBTOOLKIT_DIR}/*/*_LF-{object_}_atlas-{STREAMLINE_ATLAS}.csv"
    sdc_files, excluded_sdc = discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    subject_series: dict[tuple[str, str], pd.Series] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        # A subject on the exclusion list has its mask (it was removed from lesion_ids on purpose,
        # by subjects_with_lesion_mask), so it must not be re-reported as "no lesion mask".
        excluded_no_lesion_mask.extend(sorted(sdc_ids - lesion_ids - set(excluded_by_list)))
        sdc_not_yet_computed.extend(sorted(lesion_ids - sdc_ids))
        for subject_id in sorted(lesion_ids & sdc_ids):
            path = sdc_files[dataset][subject_id]
            subject_series[(dataset, subject_id)] = _load_and_validate_streamline_csv(path, tract_names)

    if not subject_series:
        raise ValueError(
            "no subjects admitted - the intersection of subjects with a registered lesion mask "
            f"(assets/metadata/participants.csv, has_lesion) and subjects with an SDC file "
            f"(object={object_!r}, representation='streamline') is empty; check 'datasets'/'data_root' "
            "in the config"
        )

    X, metadata = _stack_streamline_matrix(subject_series, tract_names)
    return (
        X, metadata, tract_names, excluded_by_group, excluded_by_list,
        sorted(excluded_no_lesion_mask), sorted(sdc_not_yet_computed),
    )


# The two columns compute_sdc_metadata writes, each suffixed with the grid's own name. One place,
# so the writer, the column order and the config that copies them into participants.csv cannot
# disagree about what a grid contributes.
DISCONNECTION_LOAD_PREFIX = "disconnection_load_voxels"
DISCONNECTION_MEAN_PREFIX = "disconnection_mean"

# A disconnection probability lives in [0, 1]. Float32 files round-trip a hair above 1.0, so the
# upper bound is not exact - but a map on a 0-100 scale (a percent) would be ~100x too large and
# pass every other check, so it must stop the run rather than become a plausible-looking column.
_PROBABILITY_UPPER_BOUND = 1.0 + 1e-4


def compute_sdc_metadata(
    data_root: Path,
    datasets: list[str],
    disconnectome_glob: str,
    resample_interpolation: str,
    group_filter: list[str] | None,
    grids: list[LesionGrid],
) -> tuple[pd.DataFrame, list[str]]:
    """How disconnected each subject is, overall - two scalars per subject, on every grid in `grids`.

    The single computation src.pipeline.compute_sdc_metadata writes to
    assets/metadata/sdc_metadata.csv. Returns (metadata, excluded_by_group); metadata carries
    subject_id, dataset and, per grid, suffixed with that grid's name:

    - disconnection_load_voxels_<g>: the sum of the disconnection probability over the voxels
      inside the brain mask. The disconnection counterpart of lesion_volume_voxels: for a
      binary map it IS a voxel count; here each voxel contributes its probability instead of 0
      or 1, so the unit is "probability-weighted voxels" (mm^3 on a 1mm grid).
    - disconnection_mean_<g>: that sum divided by the number of brain voxels - the mean
      disconnection probability over the brain, in [0, 1]. The divisor is a constant of the
      grid, so this column orders subjects exactly as the load does; it exists because a
      fraction reads more directly than a voxel count.

    Each map is read from disk once and resampled once per grid, like compute_lesion_metadata.
    On a grid coarser than the maps' native 1mm, "nearest" is a subsample: the load there sums
    2mm voxels (8 mm^3 each), so it is about 1/8 of the 1mm load but not exactly (measured on the
    full cohort: 8 x load_2mm / load_1mm has median 1.001, range 0.989-1.017).

    Voxels outside the brain mask are excluded from both (lesion_metadata's own
    correct_out_of_brain=True makes the same choice for lesions): BCBToolKit's disconnectome
    carries a median 0.80% of its mass there (up to 8.9% in one case, measured on 400 random
    subjects), which is tractography leaking past the brain, not
    disconnection.

    Every map is resampled onto the grid with the file's OWN header, never by assuming a
    fixed relationship to the reference. The disconnectome maps do not share one voxel lattice:
    across the 8 datasets there are 3 distinct headers (LAS with an x offset of +90, RAS with
    -90, RAS with -91 like the MNI template), so one dataset needs an x flip, another a
    one-voxel shift and a third nothing. A hardcoded flip is right for exactly one of them and
    silently mirrors the others. With the default "nearest" interpolation each of those is an
    exact integer remapping, so the sum is not altered by the resampling.

    Admission comes from the registry (has_sdc in participants.csv), not from a glob on disk,
    and the two must agree in both directions: a subject the registry says has SDC output but
    whose map is not on disk, or a map on disk for a subject the registry does not flag, raises.
    Either means populate_metadata.py and the data disagree about who exists, and measuring
    "whoever happens to be on disk" would hide it. No exclusion list is applied here: like
    compute_lesion_metadata this measures every subject; who to drop is decided downstream.

    Streaming, one map at a time - only scalars are kept per subject.
    """
    validate_lesion_grids(grids)
    contexts = [_disconnection_grid_context(grid) for grid in grids]

    registered, excluded_by_group_registry = registered_subjects(datasets, group_filter, _SDC_FLAG_COLUMN)
    sdc_files, excluded_by_group_disk = discover_by_dataset(data_root, datasets, disconnectome_glob, group_filter)
    _check_registry_agrees_with_disk(registered, sdc_files, disconnectome_glob)

    rows: list[dict[str, object]] = []
    for dataset in datasets:
        for subject_id, path in sorted(sdc_files[dataset].items()):
            # One disk read per subject, shared by every grid (nibabel caches the data array).
            img = nib.load(path)
            row: dict[str, object] = {"subject_id": subject_id, "dataset": dataset}
            for context in contexts:
                load = _disconnection_load(img, path, context, resample_interpolation)
                row[context.load_column] = load
                row[context.mean_column] = load / context.n_brain_voxels
            rows.append(row)

    if not rows:
        raise ValueError(
            f"no subjects measured under {data_root} for datasets={datasets} (group_filter={group_filter!r}) - "
            "the registry flags no subject with SDC output in scope"
        )
    metadata = pd.DataFrame(rows, columns=_disconnection_metadata_columns(contexts))
    return metadata, sorted(set(excluded_by_group_registry) | set(excluded_by_group_disk))


def _check_registry_agrees_with_disk(
    registered: dict[str, list[str]], on_disk: dict[str, dict[str, Path]], glob_pattern: str
) -> None:
    """Both directions of "the registry and the data agree about who has SDC output".

    Collected over every dataset before raising, so one run reports the whole disagreement
    instead of the first dataset's."""
    problems: list[str] = []
    for dataset, flagged in registered.items():
        absent = sorted(set(flagged) - set(on_disk[dataset]))
        unflagged = sorted(set(on_disk[dataset]) - set(flagged))
        if absent:
            problems.append(
                f"{dataset}: {len(absent)} subject(s) flagged {_SDC_FLAG_COLUMN}=True in the registry have no "
                f"file matching {glob_pattern!r} (e.g. {absent[:5]}) - the data is incomplete, or this is a "
                "partial local copy of it"
            )
        if unflagged:
            problems.append(
                f"{dataset}: {len(unflagged)} subject(s) have a file matching {glob_pattern!r} but are not flagged "
                f"{_SDC_FLAG_COLUMN}=True in the registry (e.g. {unflagged[:5]}) - re-run "
                "src/pipeline/populate_metadata.py"
            )
    if problems:
        raise ValueError("the subject registry and the SDC output on disk disagree:\n  " + "\n  ".join(problems))


@dataclass(frozen=True, eq=False)
class _DisconnectionGridContext:
    """Everything derived once per grid and reused for every subject: the reference image, the
    brain mask, its voxel count and the two column names. eq=False: numpy fields."""

    reference_img: nib.Nifti1Image
    brain_mask: np.ndarray
    n_brain_voxels: int
    load_column: str
    mean_column: str


def _disconnection_grid_context(grid: LesionGrid) -> _DisconnectionGridContext:
    reference_img = load_reference_image(grid.reference_template_path)
    brain_mask = load_brain_mask(grid.brain_mask_path, reference_img)
    n_brain_voxels = int(brain_mask.sum())
    if n_brain_voxels == 0:
        raise ValueError(
            f"brain mask {grid.brain_mask_path} has no voxel inside it on grid {grid.name!r} - "
            "the mean disconnection over the brain is undefined"
        )
    return _DisconnectionGridContext(
        reference_img=reference_img,
        brain_mask=brain_mask,
        n_brain_voxels=n_brain_voxels,
        load_column=f"{DISCONNECTION_LOAD_PREFIX}_{grid.name}",
        mean_column=f"{DISCONNECTION_MEAN_PREFIX}_{grid.name}",
    )


def _disconnection_metadata_columns(contexts: list[_DisconnectionGridContext]) -> list[str]:
    """Explicit column order, grids in declaration order - also what fixes the columns of an
    empty frame."""
    columns = ["subject_id", "dataset"]
    for context in contexts:
        columns += [context.load_column, context.mean_column]
    return columns


def _disconnection_load(
    img: nib.Nifti1Image, path: Path, context: _DisconnectionGridContext, resample_interpolation: str
) -> float:
    """One subject's summed disconnection probability inside the brain mask, on one grid.

    `path` only names the file in the error: `img` is its already-loaded image.

    Raises ValueError for a map that is not a [0, 1] probability (negative, non-finite, or above
    1) - see _PROBABILITY_UPPER_BOUND for why that check exists."""
    values = _disconnectome_values(img, context.reference_img, resample_interpolation)
    if not np.isfinite(values).all() or values.min() < 0.0 or values.max() > _PROBABILITY_UPPER_BOUND:
        raise ValueError(
            f"{path}: disconnectome values are not a [0, 1] probability "
            f"(min={values.min()}, max={values.max()}, finite={bool(np.isfinite(values).all())}) - "
            "refusing to sum a map on an unknown scale"
        )
    return float(values[context.brain_mask].sum(dtype=np.float64))



def _load_and_validate_streamline_csv(path: Path, tract_names: np.ndarray) -> pd.Series:
    """Read one subject's streamline CSV into a tract -> streamline_ratio
    Series, validated against the reference tract list.

    Unlike parcellated_csv.load_and_validate_csv, a **missing** tract raises instead of being
    filled with 0.0: this file writes every tract explicitly, zeros included,
    so an incomplete one is truncated or corrupt, not a legitimate omission
    (see module docstring).
    """
    df = pd.read_csv(path)
    for column in (_STREAMLINE_TRACT_COLUMN, _STREAMLINE_VALUE_COLUMN):
        if column not in df.columns:
            raise ValueError(f"{path}: missing {column!r} column - unexpected file shape")

    dup = df[_STREAMLINE_TRACT_COLUMN].duplicated()
    if dup.any():
        raise ValueError(
            f"{path}: {int(dup.sum())} duplicate {_STREAMLINE_TRACT_COLUMN} value(s): "
            f"{df.loc[dup, _STREAMLINE_TRACT_COLUMN].tolist()}"
        )

    found = set(df[_STREAMLINE_TRACT_COLUMN])
    expected = set(tract_names)
    unknown = found - expected
    if unknown:
        raise ValueError(
            f"{path}: {len(unknown)} {_STREAMLINE_TRACT_COLUMN} value(s) not in the reference tract set: "
            f"{sorted(unknown)} - check that the reference file matches this atlas"
        )
    missing = expected - found
    if missing:
        raise ValueError(
            f"{path}: {len(missing)} tract(s) missing from a file expected to list all "
            f"{len(tract_names)}: {sorted(missing)} - truncated or corrupt file, not an omitted "
            "zero (see src/features/sdc.py's module docstring)"
        )
    ratio = require_finite_numeric(df, path, _STREAMLINE_TRACT_COLUMN, _STREAMLINE_VALUE_COLUMN)
    negative = ratio < 0
    if negative.any():
        raise ValueError(
            f"{path}: {int(negative.sum())} negative {_STREAMLINE_VALUE_COLUMN} value(s) - a proportion of "
            f"streamlines cannot be below 0, e.g. {df.loc[negative, _STREAMLINE_TRACT_COLUMN].tolist()[:5]}"
        )
    return pd.Series(ratio.values, index=df[_STREAMLINE_TRACT_COLUMN])


def _stack_streamline_matrix(
    subject_series: dict[tuple[str, str], pd.Series], tract_names: np.ndarray
) -> tuple[np.ndarray, pd.DataFrame]:
    features = []
    subject_ids: list[str] = []
    dataset_labels: list[str] = []
    for (dataset, subject_id), series in sorted(subject_series.items()):
        # Reordering only - completeness is already guaranteed by
        # _load_and_validate_streamline_csv, so no fill value can apply here.
        features.append(series.reindex(tract_names).values)
        subject_ids.append(subject_id)
        dataset_labels.append(dataset)
    X = np.stack(features)
    metadata = pd.DataFrame({"subject_id": subject_ids, "dataset": dataset_labels})
    return X, metadata


def _load_disconnectome_voxels(
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str, brain_mask: np.ndarray | None
) -> tuple[np.ndarray, int, float]:
    """Load one subject's disconnectome-map, resampled onto reference_img's
    grid if needed, flattened to float32 - never binarized (continuous [0, 1]
    disconnection probability, unlike src/features/lesion.py's
    _load_and_binarize_lesion). With a brain_mask, the voxels outside it are zeroed.

    Returns (voxels, n_voxels_corrected, mass_removed_fraction), the last two (0, 0.0) when
    brain_mask is None or the map has nothing outside it."""
    voxels = _disconnectome_values(nib.load(path), reference_img, resample_interpolation)
    if brain_mask is None:
        return voxels, 0, 0.0
    return _zero_out_of_brain(voxels, brain_mask, path)


def _zero_out_of_brain(voxels: np.ndarray, brain_mask: np.ndarray, path: Path) -> tuple[np.ndarray, int, float]:
    """One map with its out-of-brain voxels zeroed (`zero_out_of_brain_voxels`), the count of
    voxels that were zeroed, and the fraction of the map's mass they held.

    Raises for a non-finite or negative value: the mass fraction is only defined for a
    non-negative, finite field, and a NaN would silently turn it into NaN."""
    if not np.isfinite(voxels).all() or voxels.min() < 0.0:
        raise ValueError(
            f"{path}: disconnectome values are not a finite, non-negative field "
            f"(min={voxels.min()}, finite={bool(np.isfinite(voxels).all())}) - "
            "cannot compute the mass removed by correct_out_of_brain"
        )
    corrected, n_corrected_voxels = zero_out_of_brain_voxels(voxels[None, :], brain_mask)
    n_voxels = int(n_corrected_voxels[0])
    if n_voxels == 0:
        return voxels, 0, 0.0
    removed_mass = float(voxels[~brain_mask].sum(dtype=np.float64))
    total_mass = float(voxels.sum(dtype=np.float64))
    return corrected[0], n_voxels, removed_mass / total_mass


def _disconnectome_values(
    img: nib.Nifti1Image, reference_img: nib.Nifti1Image, resample_interpolation: str
) -> np.ndarray:
    """An already-loaded disconnectome-map resampled onto reference_img's grid if needed,
    flattened to float32."""
    if _needs_resample(img, reference_img):
        img = resample_to_img(
            img, reference_img, interpolation=resample_interpolation, force_resample=True, copy_header=True
        )
    return img.get_fdata().ravel().astype(np.float32)


def _stack_voxelwise_matrix(
    admitted: dict[tuple[str, str], Path],
    reference_img: nib.Nifti1Image,
    resample_interpolation: str,
    brain_mask: np.ndarray | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[tuple[str, int, float]]]:
    """X (n_subjects x n_non_constant_voxels), metadata, the boolean non-constant mask over
    the full reference grid and the (subject_id, n_voxels_corrected, mass_removed_fraction)
    triples of the subjects the out-of-brain correction touched, built in two passes over the
    maps so that the full n_subjects x n_grid_voxels matrix is never held in memory.

    Pass 1 reads every map and keeps only the running per-voxel min and max; a voxel is constant
    when they are equal (NaN never equals itself, so a NaN voxel is kept - the same outcome as
    `X.min(axis=0) != X.max(axis=0)` on the stacked matrix). Pass 2 reads every map again and
    writes only the kept voxels into a preallocated array. Both passes walk the same sorted
    order, so row i is the same subject in both, and both apply the same out-of-brain
    correction (brain_mask, when given) before anything is compared or stored: the mask that
    decides which columns are constant must be the one on the values that fill them.
    """
    ordered = sorted(admitted.items())
    paths = [path for _, path in ordered]
    non_constant_mask = _non_constant_voxel_mask(paths, reference_img, resample_interpolation, brain_mask)

    X = np.empty((len(paths), int(non_constant_mask.sum())), dtype=np.float32)
    corrected_subjects: list[tuple[str, int, float]] = []
    for row, ((_, subject_id), path) in enumerate(ordered):
        voxels, n_voxels_corrected, mass_removed = _load_disconnectome_voxels(
            path, reference_img, resample_interpolation, brain_mask
        )
        X[row] = voxels[non_constant_mask]
        if n_voxels_corrected > 0:
            corrected_subjects.append((subject_id, n_voxels_corrected, mass_removed))

    metadata = pd.DataFrame(
        {
            "subject_id": [subject_id for (_, subject_id), _ in ordered],
            "dataset": [dataset for (dataset, _), _ in ordered],
        }
    )
    return X, metadata, non_constant_mask, sorted(corrected_subjects)


def _non_constant_voxel_mask(
    paths: list[Path], reference_img: nib.Nifti1Image, resample_interpolation: str, brain_mask: np.ndarray | None
) -> np.ndarray:
    lowest: np.ndarray | None = None
    highest: np.ndarray | None = None
    for path in paths:
        voxels, _, _ = _load_disconnectome_voxels(path, reference_img, resample_interpolation, brain_mask)
        if lowest is None or highest is None:
            lowest, highest = voxels.copy(), voxels.copy()
        else:
            np.minimum(lowest, voxels, out=lowest)
            np.maximum(highest, voxels, out=highest)
    if lowest is None or highest is None:
        raise ValueError("cannot find non-constant voxels: no disconnectome maps were given")
    return lowest != highest
