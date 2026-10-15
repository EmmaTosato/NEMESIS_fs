"""Parcellated BCBToolKit CSVs -> a subjects x regions matrix, for either object (lesion or disconnectome).

Each subject's CSV under bcbtoolkit/<subject>/ (`*_LF-<object>_atlas-<atlas>.csv`) holds one row
per brain region damaged/disconnected above zero for a given atlas - BCBToolKit omits rows for
regions at zero overlap rather than writing them explicitly (verified empirically on the real
cohort: zero rows with an explicit 0.0 value were ever found - see
notebooks/exploration/sdc_analysis.ipynb). Rows are not in a stable order across subjects, so
alignment is done by region_name (reindex against a fixed reference), never by row position -
there is no common spatial grid to resample onto here.

This module is the one place that logic lives, shared by the two matrix families that read these
CSVs: src/features/sdc.py (object="disconnectome", the s2.x sessions) and
src/pipeline/build_lesion_matrix.py (object="lesion", the s1.x parcellated session). It sits below
both in the layering (utils -> features) so neither has to import the other - sdc.py already
imports src.features.lesion, so the reverse would be circular. The subject-admission helpers
(registry lookup, exclusion list, per-dataset discovery) are shared the same way by the other
sdc.py builders, which is why they are public here.

reference_labels_path (assets/atlases/sdc_labels/<atlas>.csv) is the authoritative, fixed region
list for a given atlas - derived once from the full real cohort (every region reached its
known/expected cardinality, see docs/dev/sdc_matrix.md) and never re-derived per run. Every
region_name found in a subject's CSV must exist in this reference (raise ValueError otherwise - an
atlas mismatch or corrupt file, never guessed past); a reference region missing from a subject's
CSV is the expected/legitimate "omitted, zero overlap" case, filled with 0.0. No column is ever
dropped from X even if constant across every admitted subject - column j always means the same
region regardless of which subjects a given run includes (2026-08-27, on request).

A subject is only admitted into X if it has BOTH a lesion mask registered in the subject registry
AND the requested CSV - a subject with a CSV but no registered lesion mask is excluded explicitly
(excluded_no_lesion_mask), and a subject with a registered mask but no CSV is reported
(csv_not_yet_computed), never silently included as an all-zero row indistinguishable from a
genuine "no overlap" observation.

"Has a lesion mask" is resolved against `assets/metadata/participants.csv` (via
src.utils.participants), NOT by globbing manual_masks/ on disk (unlike the voxel-wise
build_lesion_matrix) - a local `data/` copy can be a partial local sample (found 2026-08-27: this
Mac had only 10 lesion masks per dataset physically present, vs. 195-705 in bcbtoolkit/), while the
registry is authoritative about which subjects genuinely have a lesion mask regardless of what is
currently retrieved on any one machine.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.features.subject_discovery import discover_files_by_subject
from src.utils.participants import load_participants_registry
from src.utils.subject_ids import group_of

KNOWN_OBJECTS = frozenset({"disconnectome", "lesion"})
KNOWN_VALUE_COLUMNS = frozenset({
    "fraction_covered", "mean_overlap", "weighted_mean_overlap",
    "sum_overlap", "p90_overlap", "p95_overlap",
})
# Per-dataset tree (derivatives/<site>/<dataset>/) holding BCBToolKit's output: the disconnectome
# and lesion maps and their per-atlas CSVs.
BCBTOOLKIT_DIR = "bcbtoolkit"

_LESION_FLAG_COLUMN = "has_lesion"


def build_parcellated_matrix(
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
    metadata, and the region names naming each column, from the per-subject
    `LF-<object_>` CSVs of one atlas.

    Returns (X, metadata, region_names, excluded_by_group, excluded_by_list,
    excluded_no_lesion_mask, csv_not_yet_computed) - see module docstring,
    docs/dev/sdc_matrix.md and docs/dev/lesion_matrix.md. excluded_by_group
    merges the group-filter exclusions from both the lesion-mask-registry and
    the CSV discovery passes. excluded_by_list is the hand-curated admission
    list (src.utils.participants.load_excluded_subjects), restricted to the
    subjects in scope for this run. csv_not_yet_computed is the admitted
    subjects with no CSV: reported, never given a row of zeros.
    """
    if object_ not in KNOWN_OBJECTS:
        raise ValueError(f"object_ must be one of {sorted(KNOWN_OBJECTS)}, got {object_!r}")
    if value_column not in KNOWN_VALUE_COLUMNS:
        raise ValueError(f"value_column must be one of {sorted(KNOWN_VALUE_COLUMNS)}, got {value_column!r}")

    region_names = load_reference_regions(reference_labels_path)

    lesion_subjects, excluded_lesion, excluded_by_list = subjects_with_lesion_mask(
        datasets, group_filter, excluded_subjects
    )
    csv_glob = f"{BCBTOOLKIT_DIR}/*/*_LF-{object_}_atlas-{atlas}.csv"
    csv_files, excluded_csv = discover_by_dataset(data_root, datasets, csv_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_csv))

    subject_dfs: dict[tuple[str, str], pd.DataFrame] = {}
    excluded_no_lesion_mask: list[str] = []
    csv_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        csv_ids = set(csv_files.get(dataset, {}))
        # A subject on the exclusion list has its mask (it was removed from lesion_ids on purpose,
        # by subjects_with_lesion_mask), so it must not be re-reported as "no lesion mask".
        excluded_no_lesion_mask.extend(sorted(csv_ids - lesion_ids - set(excluded_by_list)))
        csv_not_yet_computed.extend(sorted(lesion_ids - csv_ids))
        for subject_id in sorted(lesion_ids & csv_ids):
            path = csv_files[dataset][subject_id]
            subject_dfs[(dataset, subject_id)] = load_and_validate_csv(path, region_names, value_column)

    if not subject_dfs:
        raise ValueError(
            "no subjects admitted - the intersection of subjects with a registered lesion mask "
            f"(assets/metadata/participants.csv, has_lesion) and subjects with a CSV "
            f"(object={object_!r}, atlas={atlas!r}) is empty; check 'datasets'/'data_root' in the config"
        )

    X, metadata = stack_aligned_matrix(subject_dfs, region_names, value_column)
    return (
        X, metadata, region_names, excluded_by_group, excluded_by_list,
        sorted(excluded_no_lesion_mask), sorted(csv_not_yet_computed),
    )


def load_reference_regions(reference_labels_path: Path, column: str = "region_name") -> np.ndarray:
    """Load the authoritative, fixed region list for one atlas.

    `column` names the identifier column in the reference file: "region_name"
    for the parcellated atlases, "tract" for yeh_hcp1065_streamline (whose
    source CSVs use that name - the reference file mirrors its own atlas's
    schema rather than renaming it).

    Public so callers that only need the region set (e.g. a sanity check
    against a freshly-retrieved atlas combo) don't have to run full matrix
    discovery/validation via build_parcellated_matrix.
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


def discover_by_dataset(
    data_root: Path, datasets: list[str], glob_pattern: str, group_filter: list[str] | None
) -> tuple[dict[str, dict[str, Path]], list[str]]:
    """discover_files_by_subject run once per dataset, merged into one dict.

    Used for the BCBToolKit-output glob only (does this subject have this object/atlas's
    CSV?) - lesion mask presence is resolved from participants.csv instead,
    see subjects_with_lesion_mask and the module docstring for why.
    """
    by_dataset: dict[str, dict[str, Path]] = {}
    excluded: list[str] = []
    for dataset in datasets:
        by_subject, excluded_here = discover_files_by_subject(data_root, dataset, glob_pattern, group_filter)
        by_dataset[dataset] = by_subject
        excluded.extend(excluded_here)
    return by_dataset, excluded


def registered_subjects(
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


def subjects_with_lesion_mask(
    datasets: list[str], group_filter: list[str] | None, excluded_subjects: frozenset[str]
) -> tuple[dict[str, dict[str, None]], list[str], list[str]]:
    """Which subjects have a lesion mask, per dataset - from
    assets/metadata/participants.csv's has_lesion flag, not from disk (see
    module docstring). Return shape matches discover_by_dataset's
    {dataset: {subject_id: ...}} so both feed the same intersection logic in
    build_parcellated_matrix - the per-subject value here carries no information
    (unlike discover_by_dataset's Path), only the key set matters.

    Returns (by_dataset, excluded_by_group, excluded_by_list). This is the one
    place every BCBToolKit-based builder resolves its admitted subjects (the parcellated matrix
    of either object, and the sdc.py voxelwise and streamline ones), so applying the
    hand-curated exclusion list here covers all of them at once - and guarantees these matrices
    drop exactly the subjects the voxel-wise lesion matrix drops (src.features.lesion's own
    _drop_excluded_subjects), which is the reason that list is a single file.
    excluded_by_list names only subjects in scope for this run, never the whole
    list.
    """
    in_group, excluded = registered_subjects(datasets, group_filter, _LESION_FLAG_COLUMN)
    by_dataset: dict[str, dict[str, None]] = {}
    excluded_by_list: list[str] = []
    for dataset in datasets:
        # Applied after group_filter (inside registered_subjects) so a subject is never
        # reported twice: an HC subject on the exclusion list is excluded by group, not by the list.
        excluded_by_list.extend(s for s in in_group[dataset] if s in excluded_subjects)
        by_dataset[dataset] = {s: None for s in in_group[dataset] if s not in excluded_subjects}
    return by_dataset, excluded, sorted(excluded_by_list)


def load_and_validate_csv(path: Path, region_names: np.ndarray, value_column: str) -> pd.DataFrame:
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


def stack_aligned_matrix(
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