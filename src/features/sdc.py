"""Build a 2D feature matrix (n_subjects x n_regions) from parcellated SDC output.

Each subject's disconnectome (or lesion) CSV under sdc/<subject>/dwi/ holds one
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

A subject is only admitted into X if it has BOTH a real lesion mask
(lesion_glob, cross-checked the same way build_lesion_matrix.py discovers
lesion files) and the requested SDC CSV - a subject present in sdc/ without a
lesion mask (a real case found in this cohort, see docs/dev/sdc_matrix.md) is
excluded explicitly (excluded_no_lesion_mask), never silently included as an
all-zero row indistinguishable from a genuine "no disconnection" observation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.features.subject_discovery import discover_files_by_subject

KNOWN_OBJECTS = frozenset({"disconnectome", "lesion"})
KNOWN_VALUE_COLUMNS = frozenset({
    "fraction_covered", "mean_overlap", "weighted_mean_overlap",
    "sum_overlap", "p90_overlap", "p95_overlap",
})


def build_sdc_matrix(
    data_root: Path,
    datasets: list[str],
    lesion_glob: str,
    object_: str,
    atlas: str,
    value_column: str,
    reference_labels_path: Path,
    group_filter: list[str] | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str]]:
    """Build X (n_subjects x n_regions, fixed = len(region_names)), row-aligned
    metadata, and the region names naming each column.

    Returns (X, metadata, region_names, excluded_by_group,
    excluded_no_lesion_mask, sdc_not_yet_computed) - see module docstring and
    docs/dev/sdc_matrix.md. excluded_by_group merges the group-filter
    exclusions from both the lesion-mask and the SDC-file discovery passes.
    """
    if object_ not in KNOWN_OBJECTS:
        raise ValueError(f"object_ must be one of {sorted(KNOWN_OBJECTS)}, got {object_!r}")
    if value_column not in KNOWN_VALUE_COLUMNS:
        raise ValueError(f"value_column must be one of {sorted(KNOWN_VALUE_COLUMNS)}, got {value_column!r}")

    region_names = load_reference_regions(reference_labels_path)

    lesion_subjects, excluded_lesion = _discover_by_dataset(data_root, datasets, lesion_glob, group_filter)
    sdc_glob = f"sdc/*/dwi/*_LF-{object_}_atlas-{atlas}.csv"
    sdc_files, excluded_sdc = _discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    subject_dfs: dict[tuple[str, str], pd.DataFrame] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        excluded_no_lesion_mask.extend(sorted(sdc_ids - lesion_ids))
        sdc_not_yet_computed.extend(sorted(lesion_ids - sdc_ids))
        for subject_id in sorted(lesion_ids & sdc_ids):
            path = sdc_files[dataset][subject_id]
            subject_dfs[(dataset, subject_id)] = _load_and_validate_csv(path, region_names, value_column)

    if not subject_dfs:
        raise ValueError(
            "no subjects admitted - the intersection of subjects with a lesion mask "
            f"(lesion_glob={lesion_glob!r}) and subjects with an SDC file (object={object_!r}, "
            f"atlas={atlas!r}) is empty; check 'datasets'/'data_root' in the config"
        )

    X, metadata = _stack_aligned_matrix(subject_dfs, region_names, value_column)
    return X, metadata, region_names, excluded_by_group, sorted(excluded_no_lesion_mask), sorted(sdc_not_yet_computed)


def load_reference_regions(reference_labels_path: Path) -> np.ndarray:
    """Load the authoritative, fixed region list for one atlas.

    Public so callers that only need the region set (e.g. a sanity check
    against a freshly-retrieved atlas combo) don't have to run full matrix
    discovery/validation via build_sdc_matrix.
    """
    if not reference_labels_path.is_file():
        raise FileNotFoundError(f"reference_labels_path not found: {reference_labels_path}")
    df = pd.read_csv(reference_labels_path)
    if "region_name" not in df.columns:
        raise ValueError(f"{reference_labels_path}: missing 'region_name' column")
    regions = df["region_name"].tolist()
    if len(set(regions)) != len(regions):
        raise ValueError(f"{reference_labels_path}: duplicate region_name entries in reference file")
    return np.array(sorted(regions))


def _discover_by_dataset(
    data_root: Path, datasets: list[str], glob_pattern: str, group_filter: list[str] | None
) -> tuple[dict[str, dict[str, Path]], list[str]]:
    """discover_files_by_subject run once per dataset, merged into one dict.

    Used both for lesion_glob (does this subject have a real lesion mask?)
    and for the SDC glob (does this subject have this object/atlas's CSV?) -
    same discovery machinery, different glob, see module docstring for why
    both passes are needed.
    """
    by_dataset: dict[str, dict[str, Path]] = {}
    excluded: list[str] = []
    for dataset in datasets:
        by_subject, excluded_here = discover_files_by_subject(data_root, dataset, glob_pattern, group_filter)
        by_dataset[dataset] = by_subject
        excluded.extend(excluded_here)
    return by_dataset, excluded


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
