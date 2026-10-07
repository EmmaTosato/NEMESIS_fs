"""Build a 2D feature matrix (n_subjects x n_regions) from parcellated SDC output.

Each subject's disconnectome (or lesion) CSV under sdc/<subject>/ holds one
row per brain region disconnected/damaged above zero for a given atlas -
BCBToolKit omits rows for regions at zero overlap rather than writing them
explicitly (verified empirically on the real cohort: zero rows with an
explicit 0.0 value were ever found - see notebooks/exploration/sdc_analysis.ipynb).
Rows are not in a stable order across subjects, so alignment is done by
region_name (reindex against a fixed reference), never by row position -
unlike src/features/lesion.py's voxel grid, there is no common spatial grid to
resample onto here.

reference_labels_path (assets/atlases/sdc_labels/<atlas>.csv) is the
authoritative, fixed region list for a given atlas - derived once from the
full real cohort (every region reached its known/expected cardinality, see
docs/dev/sdc_matrix.md) and never re-derived per run. Every region_name found
in a subject's CSV must exist in this reference (raise ValueError otherwise -
an atlas mismatch or corrupt file, never guessed past); a reference region
missing from a subject's CSV is the expected/legitimate "omitted, zero
overlap" case, filled with 0.0. No column is ever dropped from X even if
constant across every admitted subject - the project decision here is that
column j always means the same region regardless of which subjects a given
run includes (2026-08-27, on request).

A subject is only admitted into X if it has BOTH a lesion mask registered in
the subject registry AND the requested SDC CSV - a subject present
in sdc/ without a lesion mask (a real case found in this cohort, see
docs/dev/sdc_matrix.md) is excluded explicitly (excluded_no_lesion_mask),
never silently included as an all-zero row indistinguishable from a genuine
"no disconnection" observation.

"Has a lesion mask" is resolved against `assets/metadata/participants.csv`
(via src.utils.participants), NOT by globbing manual_masks/ on disk directly
(unlike build_lesion_matrix.py) - a local `data/` copy can be a partial
local sample (found 2026-08-27: this Mac had only 10 lesion masks per
dataset physically present, vs. 195-705 in sdc/), while the registry is
authoritative about which subjects genuinely have a lesion mask
regardless of what's currently retrieved on any one machine.

A second, alternative representation (`build_sdc_voxelwise_matrix`, added
03/09) builds a voxel-wise matrix directly from the `disconnectome-map`
`.nii.gz` (the pre-parcellation volume the `LF-disconnectome_atlas-*.csv`
files above are themselves derived from) - same resampling-onto-a-common-grid
approach as `src/features/lesion.py`'s voxel-wise lesion matrix, but the
disconnectome values are a **continuous** [0, 1] probability, never
binarized (unlike a lesion mask). Deliberately restricted to
`object_="disconnectome"` only: the equivalent for `object_="lesion"` (the
`lesion-map` .nii.gz, itself just the resampled input lesion mask BCBToolKit
used) would duplicate `build_lesion_matrix.py`'s own job from a different,
less authoritative source (`manual_masks/` is the real source; `sdc/`
only carries a copy of it as SDC's own computation input) - not built here,
raises explicitly if requested.

A third representation (`build_sdc_streamline_matrix`, added 30/09) reads the
`yeh_hcp1065_streamline` CSV (`tract,streamline_ratio`) - one value per white
matter tract, the proportion of its streamlines affected. Its schema shares
nothing with the parcellated CSVs above (no `region_name`, no choice of
value column), which is why it is its own builder rather than a parameter of
`build_sdc_matrix`. Restricted to `object_="lesion"`: BCBToolKit writes this
file only in the `LF-lesion` family, there is no `LF-disconnectome` variant
of it. Despite that name the quantity is a disconnection measure, which is
why it belongs to the s2.x (disconnectome) track - see
docs/experiments/data_sessions.md.

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

from src.utils.participants import load_participants_registry
from src.features.lesion import LesionGrid, load_brain_mask, load_reference_image, validate_lesion_grids
from src.features.subject_discovery import discover_files_by_subject
from src.utils.subject_ids import group_of

KNOWN_OBJECTS = frozenset({"disconnectome", "lesion"})
KNOWN_VALUE_COLUMNS = frozenset({
    "fraction_covered", "mean_overlap", "weighted_mean_overlap",
    "sum_overlap", "p90_overlap", "p95_overlap",
})
KNOWN_REPRESENTATIONS = frozenset({"parcellated", "voxelwise", "streamline"})
_VOXELWISE_SUPPORTED_OBJECTS = frozenset({"disconnectome"})
# The streamline CSV exists only in the LF-lesion family - BCBToolKit writes no
# LF-disconnectome variant of it (see module docstring).
_STREAMLINE_SUPPORTED_OBJECTS = frozenset({"lesion"})

# Fixed by the source file's own schema, not a config choice: this CSV has
# exactly one identifier column and one value column, unlike the parcellated
# CSVs' 6 interchangeable statistics (KNOWN_VALUE_COLUMNS above).
STREAMLINE_ATLAS = "yeh_hcp1065_streamline"
_STREAMLINE_TRACT_COLUMN = "tract"
_STREAMLINE_VALUE_COLUMN = "streamline_ratio"

_LESION_FLAG_COLUMN = "has_lesion"
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


def build_sdc_matrix(
    data_root: Path,
    datasets: list[str],
    object_: str,
    atlas: str,
    value_column: str,
    reference_labels_path: Path,
    group_filter: list[str] | None,
    excluded_subjects: frozenset[str],
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str], list[str]]:
    """Build X (n_subjects x n_regions, fixed = len(region_names)), row-aligned
    metadata, and the region names naming each column.

    Returns (X, metadata, region_names, excluded_by_group, excluded_by_list,
    excluded_no_lesion_mask, sdc_not_yet_computed) - see module docstring and
    docs/dev/sdc_matrix.md. excluded_by_group merges the group-filter
    exclusions from both the lesion-mask-registry and the SDC-file discovery
    passes. excluded_by_list is the hand-curated admission list
    (src.utils.participants.load_excluded_subjects), the same one the lesion
    matrix applies - restricted to the subjects in scope for this run.
    """
    if object_ not in KNOWN_OBJECTS:
        raise ValueError(f"object_ must be one of {sorted(KNOWN_OBJECTS)}, got {object_!r}")
    if value_column not in KNOWN_VALUE_COLUMNS:
        raise ValueError(f"value_column must be one of {sorted(KNOWN_VALUE_COLUMNS)}, got {value_column!r}")

    region_names = load_reference_regions(reference_labels_path)

    lesion_subjects, excluded_lesion, excluded_by_list = _subjects_with_lesion_mask(
        datasets, group_filter, excluded_subjects
    )
    sdc_glob = f"sdc/*/*_LF-{object_}_atlas-{atlas}.csv"
    sdc_files, excluded_sdc = _discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    subject_dfs: dict[tuple[str, str], pd.DataFrame] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        # A subject on the exclusion list has its mask (it was removed from lesion_ids on purpose,
        # by _subjects_with_lesion_mask), so it must not be re-reported as "no lesion mask".
        excluded_no_lesion_mask.extend(sorted(sdc_ids - lesion_ids - set(excluded_by_list)))
        sdc_not_yet_computed.extend(sorted(lesion_ids - sdc_ids))
        for subject_id in sorted(lesion_ids & sdc_ids):
            path = sdc_files[dataset][subject_id]
            subject_dfs[(dataset, subject_id)] = _load_and_validate_csv(path, region_names, value_column)

    if not subject_dfs:
        raise ValueError(
            "no subjects admitted - the intersection of subjects with a registered lesion mask "
            f"(assets/metadata/participants.csv, has_lesion) and subjects with an SDC file "
            f"(object={object_!r}, atlas={atlas!r}) is empty; check 'datasets'/'data_root' in the config"
        )

    X, metadata = _stack_aligned_matrix(subject_dfs, region_names, value_column)
    return (
        X, metadata, region_names, excluded_by_group, excluded_by_list,
        sorted(excluded_no_lesion_mask), sorted(sdc_not_yet_computed),
    )


def build_sdc_voxelwise_matrix(
    data_root: Path,
    datasets: list[str],
    object_: str,
    reference_template_path: Path,
    resample_interpolation: str,
    group_filter: list[str] | None,
    excluded_subjects: frozenset[str],
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str], list[str]]:
    """Build X (n_subjects x n_voxels) from the `disconnectome-map` .nii.gz -
    the pre-parcellation volume `build_sdc_matrix`'s CSVs are themselves
    derived from. Continuous [0, 1] disconnection probability per voxel,
    never binarized - see module docstring.

    Same admission criterion as build_sdc_matrix (a lesion mask registered in
    assets/metadata/participants.csv (has_lesion), not on the hand-curated
    exclusion list, AND the requested SDC file present), and the same
    constant-column drop as
    build_lesion_matrix.py (voxels outside every admitted subject's brain
    are identically 0.0 - dropped to keep X a manageable size, recoverable
    via non_constant_mask).

    Returns (X, metadata, non_constant_mask, excluded_by_group,
    excluded_by_list, excluded_no_lesion_mask, sdc_not_yet_computed).
    """
    if object_ not in _VOXELWISE_SUPPORTED_OBJECTS:
        raise ValueError(
            f"object_ must be one of {sorted(_VOXELWISE_SUPPORTED_OBJECTS)} for representation='voxelwise' "
            f"(the lesion-map equivalent is already built by build_lesion_matrix.py, from its own "
            f"authoritative manual_masks/ source), got {object_!r}"
        )

    lesion_subjects, excluded_lesion, excluded_by_list = _subjects_with_lesion_mask(
        datasets, group_filter, excluded_subjects
    )
    sdc_glob = f"sdc/*/*_res-1_desc-{object_}.nii.gz"
    sdc_files, excluded_sdc = _discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    admitted: dict[tuple[str, str], Path] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        # A subject on the exclusion list has its mask (it was removed from lesion_ids on purpose,
        # by _subjects_with_lesion_mask), so it must not be re-reported as "no lesion mask".
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
    X, metadata, non_constant_mask = _stack_voxelwise_matrix(admitted, reference_img, resample_interpolation)
    return (
        X, metadata, non_constant_mask, excluded_by_group, excluded_by_list,
        sorted(excluded_no_lesion_mask), sorted(sdc_not_yet_computed),
    )


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
    subject - same reasoning as build_sdc_matrix: column j must always name
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

    lesion_subjects, excluded_lesion, excluded_by_list = _subjects_with_lesion_mask(
        datasets, group_filter, excluded_subjects
    )
    sdc_glob = f"sdc/*/*_LF-{object_}_atlas-{STREAMLINE_ATLAS}.csv"
    sdc_files, excluded_sdc = _discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    subject_series: dict[tuple[str, str], pd.Series] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        # A subject on the exclusion list has its mask (it was removed from lesion_ids on purpose,
        # by _subjects_with_lesion_mask), so it must not be re-reported as "no lesion mask".
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

    registered, excluded_by_group_registry = _registered_subjects(datasets, group_filter, _SDC_FLAG_COLUMN)
    sdc_files, excluded_by_group_disk = _discover_by_dataset(data_root, datasets, disconnectome_glob, group_filter)
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


def load_reference_regions(reference_labels_path: Path, column: str = "region_name") -> np.ndarray:
    """Load the authoritative, fixed region list for one atlas.

    `column` names the identifier column in the reference file: "region_name"
    for the parcellated atlases, "tract" for yeh_hcp1065_streamline (whose
    source CSVs use that name - the reference file mirrors its own atlas's
    schema rather than renaming it).

    Public so callers that only need the region set (e.g. a sanity check
    against a freshly-retrieved atlas combo) don't have to run full matrix
    discovery/validation via build_sdc_matrix.
    """
    if not reference_labels_path.is_file():
        raise FileNotFoundError(f"reference_labels_path not found: {reference_labels_path}")
    df = pd.read_csv(reference_labels_path)
    if column not in df.columns:
        raise ValueError(f"{reference_labels_path}: missing {column!r} column")
    regions = df[column].tolist()
    if len(set(regions)) != len(regions):
        raise ValueError(f"{reference_labels_path}: duplicate {column} entries in reference file")
    return np.array(sorted(regions))


def _discover_by_dataset(
    data_root: Path, datasets: list[str], glob_pattern: str, group_filter: list[str] | None
) -> tuple[dict[str, dict[str, Path]], list[str]]:
    """discover_files_by_subject run once per dataset, merged into one dict.

    Used for the SDC glob only (does this subject have this object/atlas's
    CSV?) - lesion mask presence is resolved from participants.csv instead,
    see _subjects_with_lesion_mask and the module docstring for why.
    """
    by_dataset: dict[str, dict[str, Path]] = {}
    excluded: list[str] = []
    for dataset in datasets:
        by_subject, excluded_here = discover_files_by_subject(data_root, dataset, glob_pattern, group_filter)
        by_dataset[dataset] = by_subject
        excluded.extend(excluded_here)
    return by_dataset, excluded


def _registered_subjects(
    datasets: list[str], group_filter: list[str] | None, flag_column: str
) -> tuple[dict[str, list[str]], list[str]]:
    """Which subjects the registry flags as having something (`flag_column`: has_lesion or
    has_sdc), per dataset, from assets/metadata/participants.csv - not from disk (see module
    docstring).

    Returns (by_dataset, excluded_by_group): the flagged subjects of each dataset that pass
    `group_filter`, and the flagged subjects it removes. The one place every consumer of the
    registry's per-subject flags resolves them, so the group rule and the unknown-dataset check
    exist exactly once.

    Raises ValueError if a requested dataset has no row at all in the registry - a structural
    gap in the file this pipeline depends on for its core admission criterion, not something
    to silently treat as "nobody in that dataset has this".
    """
    registry = load_participants_registry()
    known_datasets = set(registry["dataset"])
    unknown = [d for d in datasets if d not in known_datasets]
    if unknown:
        raise ValueError(
            f"dataset(s) {unknown} have no row in the subject registry "
            f"(assets/metadata/participants.csv); known datasets: {sorted(known_datasets)}"
        )

    by_dataset: dict[str, list[str]] = {}
    excluded: list[str] = []
    for dataset in datasets:
        in_dataset = registry["dataset"] == dataset
        flagged = registry.loc[in_dataset & registry[flag_column], "subject_id"]
        groups = {s: group_of(s) for s in flagged}
        excluded.extend(sorted(s for s in flagged if group_filter is not None and groups[s] not in group_filter))
        by_dataset[dataset] = [s for s in flagged if group_filter is None or groups[s] in group_filter]
    return by_dataset, excluded


def _subjects_with_lesion_mask(
    datasets: list[str], group_filter: list[str] | None, excluded_subjects: frozenset[str]
) -> tuple[dict[str, dict[str, None]], list[str], list[str]]:
    """Which subjects have a lesion mask, per dataset - from
    assets/metadata/participants.csv's has_lesion flag, not from disk (see
    module docstring). Return shape matches _discover_by_dataset's
    {dataset: {subject_id: ...}} so both feed the same intersection logic in
    build_sdc_matrix - the per-subject value here carries no information
    (unlike _discover_by_dataset's Path), only the key set matters.

    Returns (by_dataset, excluded_by_group, excluded_by_list). This is the one
    place BOTH SDC representations resolve their admitted subjects, so applying
    the hand-curated exclusion list here covers build_sdc_matrix and
    build_sdc_voxelwise_matrix at once - and guarantees the SDC matrices drop
    exactly the subjects the lesion matrix drops (src.features.lesion's own
    _drop_excluded_subjects), which is the reason that list is a single file.
    excluded_by_list names only subjects in scope for this run, never the whole
    list.
    """
    in_group, excluded = _registered_subjects(datasets, group_filter, _LESION_FLAG_COLUMN)
    by_dataset: dict[str, dict[str, None]] = {}
    excluded_by_list: list[str] = []
    for dataset in datasets:
        # Applied after group_filter (inside _registered_subjects) so a subject is never
        # reported twice: an HC subject on the exclusion list is excluded by group, not by the list.
        excluded_by_list.extend(s for s in in_group[dataset] if s in excluded_subjects)
        by_dataset[dataset] = {s: None for s in in_group[dataset] if s not in excluded_subjects}
    return by_dataset, excluded, sorted(excluded_by_list)


def _load_and_validate_csv(path: Path, region_names: np.ndarray, value_column: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "region_name" not in df.columns:
        raise ValueError(f"{path}: missing 'region_name' column - unexpected file shape")
    if value_column not in df.columns:
        raise ValueError(f"{path}: missing {value_column!r} column")

    dup = df["region_name"].duplicated()
    if dup.any():
        raise ValueError(
            f"{path}: {int(dup.sum())} duplicate region_name value(s): "
            f"{df.loc[dup, 'region_name'].tolist()}"
        )

    unknown = set(df["region_name"]) - set(region_names)
    if unknown:
        raise ValueError(
            f"{path}: {len(unknown)} region_name value(s) not in the reference label set: "
            f"{sorted(unknown)} - check that the reference file matches this atlas"
        )
    return df


def _stack_aligned_matrix(
    subject_dfs: dict[tuple[str, str], pd.DataFrame], region_names: np.ndarray, value_column: str
) -> tuple[np.ndarray, pd.DataFrame]:
    features = []
    subject_ids: list[str] = []
    dataset_labels: list[str] = []
    for (dataset, subject_id), df in sorted(subject_dfs.items()):
        if len(df) == 0:
            vector = np.zeros(len(region_names))
        else:
            series = df.set_index("region_name")[value_column]
            # BCBToolKit omits regions at zero overlap instead of writing them
            # explicitly - reindex restores them as 0.0 (verified assumption,
            # see module docstring).
            vector = series.reindex(region_names, fill_value=0.0).values
        features.append(vector)
        subject_ids.append(subject_id)
        dataset_labels.append(dataset)
    X = np.stack(features)
    metadata = pd.DataFrame({"subject_id": subject_ids, "dataset": dataset_labels})
    return X, metadata


def _load_and_validate_streamline_csv(path: Path, tract_names: np.ndarray) -> pd.Series:
    """Read one subject's streamline CSV into a tract -> streamline_ratio
    Series, validated against the reference tract list.

    Unlike _load_and_validate_csv, a **missing** tract raises instead of being
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
    return df.set_index(_STREAMLINE_TRACT_COLUMN)[_STREAMLINE_VALUE_COLUMN]


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
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str
) -> np.ndarray:
    """Load one subject's disconnectome-map, resampled onto reference_img's
    grid if needed, flattened to float32 - never binarized (continuous [0, 1]
    disconnection probability, unlike src/features/lesion.py's
    _load_and_binarize_lesion)."""
    return _disconnectome_values(nib.load(path), reference_img, resample_interpolation)


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
    admitted: dict[tuple[str, str], Path], reference_img: nib.Nifti1Image, resample_interpolation: str
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray]:
    """X (n_subjects x n_non_constant_voxels), metadata and the boolean non-constant mask over
    the full reference grid, built in two passes over the maps so that the full
    n_subjects x n_grid_voxels matrix is never held in memory.

    Pass 1 reads every map and keeps only the running per-voxel min and max; a voxel is constant
    when they are equal (NaN never equals itself, so a NaN voxel is kept - the same outcome as
    `X.min(axis=0) != X.max(axis=0)` on the stacked matrix). Pass 2 reads every map again and
    writes only the kept voxels into a preallocated array. Both passes walk the same sorted
    order, so row i is the same subject in both.
    """
    ordered = sorted(admitted.items())
    paths = [path for _, path in ordered]
    non_constant_mask = _non_constant_voxel_mask(paths, reference_img, resample_interpolation)

    X = np.empty((len(paths), int(non_constant_mask.sum())), dtype=np.float32)
    for row, path in enumerate(paths):
        X[row] = _load_disconnectome_voxels(path, reference_img, resample_interpolation)[non_constant_mask]

    metadata = pd.DataFrame(
        {
            "subject_id": [subject_id for (_, subject_id), _ in ordered],
            "dataset": [dataset for (dataset, _), _ in ordered],
        }
    )
    return X, metadata, non_constant_mask


def _non_constant_voxel_mask(
    paths: list[Path], reference_img: nib.Nifti1Image, resample_interpolation: str
) -> np.ndarray:
    lowest: np.ndarray | None = None
    highest: np.ndarray | None = None
    for path in paths:
        voxels = _load_disconnectome_voxels(path, reference_img, resample_interpolation)
        if lowest is None or highest is None:
            lowest, highest = voxels.copy(), voxels.copy()
        else:
            np.minimum(lowest, voxels, out=lowest)
            np.maximum(highest, voxels, out=highest)
    if lowest is None or highest is None:
        raise ValueError("cannot find non-constant voxels: no disconnectome maps were given")
    return lowest != highest
