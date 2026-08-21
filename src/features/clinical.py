"""Loading and target-extraction for clinical/behavioral/demographic fields in participants.tsv.

Used to join a lesion/FC feature matrix's subjects against behavioral deficit
scores (NIHSS, ARAT, 9HPT, Boston naming, Clock, Corsi - see
docs/guides/datasets.md) for the lesion-deficit vs FC-deficit prediction
pipeline (src/pipeline/predict_deficit.py), reproducing Siegel et al. 2016
(docs/notes/Siegel2016_Reproduction.md). join_lesion_side/join_nihss also
back src.pipeline.enrich_lesion_metadata's lesion_side/NIHSS columns (see
that module and src/analysis/embedding_coloring.py's color_values for the
consumers that read them back out of metadata.csv - never recomputed live),
reading the same per-dataset participants.tsv files via load_participants.

participants.tsv's own subject-id column is "participant_id" - renamed to
"subject_id" here, to match the join key already used by every matrix
artifact's metadata.csv (src/utils/artifacts.py).

check_participant_variable_coverage/join_participant_variables (2026-08-17) generalize
join_lesion_side/join_nihss's per-dataset join to an arbitrary, caller-chosen column list
(age, sex, education, lesion_side, clinical_date, NIHSS, ...) instead of those two
hardcoded ones - the mechanism src.pipeline.enrich_lesion_metadata uses to build an
enriched clinical metadata table. join_lesion_side/join_nihss are kept as their own
functions (not rewritten as thin wrappers around the generic one) since their
"unknown"-string/NaN-float missing-value conventions are real, depended-upon contracts for
their own consumers (embedding_coloring.py's categorical/continuous plotting) - the generic
joiner makes no such per-variable type assumption.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# The only missing-value sentinel observed in the real WashU participants.tsv
# (verified 27/07/26) - a genuinely empty field is already turned into a real
# NaN by pandas' own default NA handling in read_csv, even under dtype=str.
_MISSING_SENTINEL = "n/a"

# Fixed repo asset root (assets/metadata/<DATASET>_participants_lesions.tsv,
# "/" in the dataset name turned into "_") - same class of constant as
# dim_reduction.py's LOGS_ROOT: never swapped per run/environment, so it's a
# module constant (monkeypatchable in tests) rather than a config field.
METADATA_ROOT = Path("assets/metadata")

# Sentinel for a subject whose lesion_side cannot be resolved - either the
# whole dataset structurally lacks the column (e.g. PASPORT, which has
# lesion_volume_ml instead) or this one subject's value is missing/blank.
UNKNOWN_LESION_SIDE = "unknown"


def load_participants(path: Path) -> pd.DataFrame:
    """Read participants.tsv, rename participant_id -> subject_id.

    Raises FileNotFoundError if path doesn't exist, ValueError if the
    expected participant_id column is absent (wrong/malformed file - never
    guessed at from a different column name).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"participants.tsv not found: {path}")

    participants = pd.read_csv(path, sep="\t", dtype=str)
    if "participant_id" not in participants.columns:
        raise ValueError(
            f"{path}: expected a 'participant_id' column, got {list(participants.columns)}"
        )
    return participants.rename(columns={"participant_id": "subject_id"})


def extract_target(participants: pd.DataFrame, target: str) -> pd.DataFrame:
    """subject_id + target score, numeric, with missing rows dropped explicitly.

    Raises ValueError if target isn't a column of participants, if it
    contains a non-numeric non-missing value (data corruption - never
    silently coerced to NaN), or if every value is missing (target unusable
    for this cohort, e.g. GDS_15 on the WashU FC cohort - docs/guides/datasets.md).
    """
    if target not in participants.columns:
        raise ValueError(f"unknown behavioral target {target!r} - not a column of participants.tsv")

    raw = participants[["subject_id", target]].copy()
    raw[target] = raw[target].map(_normalize_missing)
    try:
        raw[target] = pd.to_numeric(raw[target], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"target {target!r}: contains a non-numeric, non-missing value ({exc})") from exc

    n_total = len(raw)
    extracted = raw.dropna(subset=[target]).reset_index(drop=True)
    n_dropped = n_total - len(extracted)
    logging.info(
        "target=%s: %d/%d subjects have a usable score (%d dropped, missing)",
        target, len(extracted), n_total, n_dropped,
    )
    if extracted.empty:
        raise ValueError(f"target {target!r} has no usable (non-missing) values in this participants.tsv")

    return extracted


def _normalize_missing(value: object) -> object:
    if pd.isna(value):
        return np.nan
    return np.nan if str(value).strip() == _MISSING_SENTINEL else value


def join_lesion_side(metadata: pd.DataFrame) -> pd.Series:
    """subject_id-aligned lesion_side, joined from one participants.tsv per
    unique dataset value in metadata["dataset"].

    metadata must have "subject_id" and "dataset" columns - the schema every
    matrix artifact's metadata.csv already has. Reads
    METADATA_ROOT/f"{dataset.replace('/', '_')}_participants_lesions.tsv" via
    load_participants, which raises FileNotFoundError if that file doesn't
    exist at all - an unresolvable dataset name is a real configuration
    problem (wrong data_root/naming), never silently papered over.

    A dataset whose participants.tsv exists but has no lesion_side column at
    all (e.g. PASPORT, which has lesion_volume_ml instead) is a known,
    structural per-dataset gap, not an error: every subject in that dataset
    gets UNKNOWN_LESION_SIDE, logged once at WARNING. A subject with a
    genuinely missing per-row value (blank/"n/a") in a dataset that does have
    the column also gets UNKNOWN_LESION_SIDE. Raises ValueError if a subject
    in metadata has no matching row at all in its dataset's participants.tsv
    (data mismatch between the matrix and the metadata registry - not a
    legitimate "missing" case).
    """
    if "subject_id" not in metadata.columns or "dataset" not in metadata.columns:
        raise ValueError(
            f"join_lesion_side needs 'subject_id' and 'dataset' columns, got {list(metadata.columns)}"
        )

    side_by_subject: dict[str, str] = {}
    for dataset in metadata["dataset"].unique():
        path = METADATA_ROOT / f"{dataset.replace('/', '_')}_participants_lesions.tsv"
        participants = load_participants(path)
        subject_ids = metadata.loc[metadata["dataset"] == dataset, "subject_id"]

        if "lesion_side" not in participants.columns:
            logging.warning(
                "dataset=%s: participants file %s has no lesion_side column - %d subject(s) marked %r",
                dataset, path, len(subject_ids), UNKNOWN_LESION_SIDE,
            )
            for subject_id in subject_ids:
                side_by_subject[subject_id] = UNKNOWN_LESION_SIDE
            continue

        side_lookup = participants.set_index("subject_id")["lesion_side"]
        for subject_id in subject_ids:
            if subject_id not in side_lookup.index:
                raise ValueError(
                    f"dataset={dataset}: subject {subject_id!r} not found in {path} - cannot resolve its lesion_side"
                )
            value = _normalize_missing(side_lookup.loc[subject_id])
            side_by_subject[subject_id] = UNKNOWN_LESION_SIDE if pd.isna(value) else str(value).strip()

    return metadata["subject_id"].map(side_by_subject)


def join_nihss(metadata: pd.DataFrame) -> pd.Series:
    """subject_id-aligned baseline NIHSS score (severity, higher = worse),
    joined from one participants.tsv per unique dataset value in
    metadata["dataset"]. Same per-dataset join as join_lesion_side, but for a
    continuous score: a missing value is NaN, not a string sentinel - a
    numeric quantity has no legitimate categorical "unknown" bucket to plot
    into (see plot_embedding_continuous's NaN handling).

    A dataset whose participants.tsv has no plain "NIHSS" column at all
    (PASPORT: only NIHSS_at_presentation/24H/3m, no baseline NIHSS) is a
    known, structural per-dataset gap, not an error - deliberately NOT
    resolved from a differently-named column (that would be a clinical
    equivalence assumption this function has no basis to make): every
    subject in that dataset gets NaN, logged once at WARNING. A subject with
    a genuinely missing per-row value (blank/"n/a") in a dataset that does
    have the column also gets NaN. Raises ValueError if a subject in
    metadata has no matching row at all in its dataset's participants.tsv
    (data mismatch, not a legitimate missing case) or if a non-missing NIHSS
    cell isn't numeric (data corruption, never silently coerced to NaN).
    """
    if "subject_id" not in metadata.columns or "dataset" not in metadata.columns:
        raise ValueError(
            f"join_nihss needs 'subject_id' and 'dataset' columns, got {list(metadata.columns)}"
        )

    nihss_by_subject: dict[str, float] = {}
    for dataset in metadata["dataset"].unique():
        path = METADATA_ROOT / f"{dataset.replace('/', '_')}_participants_lesions.tsv"
        participants = load_participants(path)
        subject_ids = metadata.loc[metadata["dataset"] == dataset, "subject_id"]

        if "NIHSS" not in participants.columns:
            logging.warning(
                "dataset=%s: participants file %s has no NIHSS column - %d subject(s) marked NaN",
                dataset, path, len(subject_ids),
            )
            for subject_id in subject_ids:
                nihss_by_subject[subject_id] = np.nan
            continue

        nihss_lookup = participants.set_index("subject_id")["NIHSS"]
        for subject_id in subject_ids:
            if subject_id not in nihss_lookup.index:
                raise ValueError(
                    f"dataset={dataset}: subject {subject_id!r} not found in {path} - cannot resolve its NIHSS"
                )
            value = _normalize_missing(nihss_lookup.loc[subject_id])
            if pd.isna(value):
                nihss_by_subject[subject_id] = np.nan
                continue
            try:
                nihss_by_subject[subject_id] = float(value)
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"dataset={dataset}: subject {subject_id!r} has non-numeric NIHSS value {value!r} in {path}"
                ) from exc

    return metadata["subject_id"].map(nihss_by_subject)


@dataclass(frozen=True)
class VariableCoverageReport:
    """What join_participant_variables would do for (metadata, variables), computed once
    and shared by both the human-readable report writer (src.pipeline.enrich_lesion_metadata)
    and the join itself - so the report shown to a human before writing anything can never
    disagree with what the join actually does.

    datasets: every distinct metadata["dataset"] value, sorted.
    missing_dataset_files: dataset -> expected participants.tsv path that doesn't exist at
      all - a hard problem (wrong dataset name, or genuinely not onboarded yet).
    missing_subjects_by_dataset: dataset -> subject_ids present in metadata but absent from
      that dataset's own (existing) participants.tsv - a hard problem (data mismatch between
      the matrix and the clinical registry, never a legitimate "missing" case).
    missing_variable_by_dataset: dataset -> requested variables that dataset's participants.tsv
      doesn't have as a column at all - a known, structural per-dataset gap (e.g. PASPORT has
      no baseline NIHSS, no lesion_side), NOT a hard problem: every subject in that dataset
      gets NaN for that column.
    n_subjects_by_dataset: dataset -> subject count in metadata, for the report's own totals.

    A report is safe to join from (write metadata.csv) iff both
    missing_dataset_files and missing_subjects_by_dataset are empty - see
    join_participant_variables/src.pipeline.enrich_lesion_metadata's own gating on this.
    """

    datasets: list[str]
    missing_dataset_files: dict[str, Path]
    missing_subjects_by_dataset: dict[str, list[str]]
    missing_variable_by_dataset: dict[str, list[str]]
    n_subjects_by_dataset: dict[str, int]

    @property
    def has_hard_failures(self) -> bool:
        return bool(self.missing_dataset_files) or bool(self.missing_subjects_by_dataset)


def _participants_tsv_path(dataset: str) -> Path:
    return METADATA_ROOT / f"{dataset.replace('/', '_')}_participants_lesions.tsv"


def check_participant_variable_coverage(metadata: pd.DataFrame, variables: list[str]) -> VariableCoverageReport:
    """Checks, for every dataset in `metadata`, whether its participants.tsv exists, whether
    every metadata subject has a row in it, and which of `variables` that dataset's tsv
    actually has as a column - without joining or raising itself (see join_participant_variables
    for the version that acts on this). Read-only, safe to call purely to build a report.

    Raises ValueError if `metadata` lacks "subject_id"/"dataset" (same contract as
    join_lesion_side/join_nihss - every matrix artifact's metadata.csv already has both).
    """
    if "subject_id" not in metadata.columns or "dataset" not in metadata.columns:
        raise ValueError(
            f"check_participant_variable_coverage needs 'subject_id' and 'dataset' columns, "
            f"got {list(metadata.columns)}"
        )

    datasets = sorted(metadata["dataset"].unique())
    missing_dataset_files: dict[str, Path] = {}
    missing_subjects_by_dataset: dict[str, list[str]] = {}
    missing_variable_by_dataset: dict[str, list[str]] = {}
    n_subjects_by_dataset: dict[str, int] = {}

    for dataset in datasets:
        subject_ids = metadata.loc[metadata["dataset"] == dataset, "subject_id"]
        n_subjects_by_dataset[dataset] = len(subject_ids)
        path = _participants_tsv_path(dataset)
        if not path.is_file():
            missing_dataset_files[dataset] = path
            continue

        participants = load_participants(path)
        missing_subjects = sorted(set(subject_ids) - set(participants["subject_id"]))
        if missing_subjects:
            missing_subjects_by_dataset[dataset] = missing_subjects

        missing_variables = sorted(v for v in variables if v not in participants.columns)
        if missing_variables:
            missing_variable_by_dataset[dataset] = missing_variables

    return VariableCoverageReport(
        datasets=datasets,
        missing_dataset_files=missing_dataset_files,
        missing_subjects_by_dataset=missing_subjects_by_dataset,
        missing_variable_by_dataset=missing_variable_by_dataset,
        n_subjects_by_dataset=n_subjects_by_dataset,
    )


def join_participant_variables(metadata: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Adds one column per name in `variables` to a copy of metadata, joined per-dataset from
    assets/metadata/*_participants_lesions.tsv - the same per-dataset join join_lesion_side/
    join_nihss already do, generalized to an arbitrary, config-driven column list (age, sex,
    education, lesion_side, clinical_date, NIHSS, or any other column a dataset's own
    participants.tsv has) instead of those two hardcoded ones.

    Values are copied as-is (participants.tsv is read as dtype=str throughout this module -
    see load_participants) after normalizing the "n/a" sentinel to a real NaN
    (_normalize_missing) - no numeric/categorical coercion is attempted here, unlike
    join_nihss's own float() cast, since this function has no fixed idea of what kind of
    value a caller-chosen variable holds; a consumer that needs a specific dtype converts it
    itself.

    Raises FileNotFoundError if a dataset in metadata has no participants.tsv at all, or
    ValueError if a subject has no row at all in its dataset's participants.tsv (both re-derived
    from check_participant_variable_coverage, so this function is safe to call on its own -
    it does not trust a caller to have checked first). A variable missing from one dataset's
    own tsv (a structural gap) is NOT an error: every subject in that dataset gets NaN for
    that column, logged once at WARNING - same convention as join_lesion_side/join_nihss.
    """
    coverage = check_participant_variable_coverage(metadata, variables)
    if coverage.missing_dataset_files:
        details = "; ".join(f"{d}: expected {p}" for d, p in sorted(coverage.missing_dataset_files.items()))
        raise FileNotFoundError(f"missing participants.tsv for {len(coverage.missing_dataset_files)} dataset(s): {details}")
    if coverage.missing_subjects_by_dataset:
        details = "; ".join(
            f"{d}: {subjects}" for d, subjects in sorted(coverage.missing_subjects_by_dataset.items())
        )
        raise ValueError(f"subject(s) not found in their dataset's participants.tsv: {details}")

    values_by_variable: dict[str, dict[str, object]] = {variable: {} for variable in variables}
    for dataset in coverage.datasets:
        subject_ids = metadata.loc[metadata["dataset"] == dataset, "subject_id"]
        participants = load_participants(_participants_tsv_path(dataset))

        for variable in variables:
            if variable in coverage.missing_variable_by_dataset.get(dataset, []):
                logging.warning(
                    "dataset=%s: participants file has no %r column - %d subject(s) marked NaN",
                    dataset, variable, len(subject_ids),
                )
                for subject_id in subject_ids:
                    values_by_variable[variable][subject_id] = np.nan
                continue

            lookup = participants.set_index("subject_id")[variable]
            for subject_id in subject_ids:
                value = _normalize_missing(lookup.loc[subject_id])
                values_by_variable[variable][subject_id] = np.nan if pd.isna(value) else value

    metadata_out = metadata.copy()
    for variable in variables:
        metadata_out[variable] = metadata_out["subject_id"].map(values_by_variable[variable])
    return metadata_out
