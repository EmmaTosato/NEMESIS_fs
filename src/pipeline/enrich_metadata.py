"""CLI entry point: add clinical/demographic attributes to the project's single
participant table - what we know about each subject.

The counterpart of src/pipeline/populate_metadata.py (which answers "who exists"):
this script writes further columns into that SAME file, assets/metadata/participants.csv.
Neither script ever destroys the other's columns. See docs/dev/metadata.md.

Usage:
    conda activate nemesis
    python -m src.pipeline.enrich_metadata --config config/pipelines/enrich_metadata.json

Where each value comes from:

- Clinical/demographic variables (age, sex, education, lesion_side, NIHSS,
  clinical_date, ...) are read from each dataset's RAW participants.tsv
  (data/clinical_connectome/metadata_tsv/, paths in
  config/registry/metadata_sources.json) - the same registry populate_metadata
  reads, so the dataset -> path mapping exists in exactly one place.
- Everything derived from a lesion mask (the volume, and as a fallback the lesion
  side) is COPIED from assets/metadata/lesion_metadata.csv
  (config.lesion_metadata - see below), written by
  src.pipeline.compute_lesion_metadata. This pipeline opens no NIfTI file of its
  own: it is a join between the raw clinical tsvs and that CSV.

The join is on `original_id`, NOT on `subject_id`: a raw tsv's participant_id is
the canonical subject id for most datasets but the legacy site id for UCL-UK
("ST_UCL-UK_0001"). participants.csv already stores both, so it is the bridge -
joining on subject_id would silently match nothing for that whole dataset
(.claude/lessons_learned.md #30).

Missing values are a plain empty cell, uniformly, for every variable. This file
is a registry, not a plotting input: a consumer that needs a categorical
sentinel (e.g. "unknown" for a colour legend) applies its own on read. The one
exception carrying extra information is lesion_side_source, which records where
a lesion_side value came from - "clinical" (the raw tsv) or "geometric" (a
subject whose side the registry takes from the geometry of its own lesion mask -
see config.lesion_metadata below and knowledge/neuroimaging/lesion_laterality.md).
A clinical value is overwritten by a geometric one in exactly one case, forced on
purpose and listed per dataset in `geometric_override_datasets` (below): the clinical
side is the exact opposite of the mask's.

lesion_metadata (config, optional, null skips the mask-derived columns entirely):
the join onto assets/metadata/lesion_metadata.csv.

- `path`: that CSV. Written by src.pipeline.compute_lesion_metadata, which owns
  every decision about HOW a mask is measured (which voxel grids, whether
  out-of-brain voxels are zeroed, the laterality threshold). None of those
  settings appear here: this pipeline copies numbers, it does not compute them.
- `copy_columns`: columns copied across under the SAME name, for every in-scope
  subject, under the run's `overwrite` rule (below). Each must exist in the CSV and
  must not be a column src/pipeline/populate_metadata.py owns.
- `lesion_side_from`: which CSV column fills `lesion_side`. Its rule differs from
  copy_columns, which is why it is a separate key: it writes ONLY where the
  clinical resolution above left the cell empty, in either `overwrite` mode, and it
  also writes lesion_side_source="geometric". Outside `geometric_override_datasets` a clinical
  value is never overwritten. It also records which grid the registry's side comes
  from (e.g. "lesion_side_2mm"), since the CSV carries one per grid. null disables
  the fill, leaving lesion_side clinical-only. Requires `lesion_side` in `variables`.
- `geometric_override_datasets`: datasets whose clinical lesion_side is known to be
  unreliable (WashU: ~7% of the labelled subjects have it inverted, every one a full
  inversion with |laterality_index| >= 0.95 - docs/dev/metadata.md). For a subject of
  one of them whose clinical side is left/right and whose `lesion_side_from` side is
  the opposite one (left vs right - a `both` never triggers it), the registry takes the
  GEOMETRIC side and writes lesion_side_source="geometric". This is a forced assumption
  (the clinical label is the wrong one, not the mask), not a measured fact; every
  overridden subject is logged at WARNING. [] disables it; a non-empty list requires
  `lesion_side_from` and `overwrite: true` (it overwrites a filled cell, which append mode
  never does).

The join is on subject_id and is strict in both directions: a subject with
has_lesion=True but no row in the CSV means the CSV is stale (re-run
compute_lesion_metadata), and a row in the CSV for a subject the registry does not
know - or knows as has_lesion=False - means the two files disagree about who has a
mask. Both raise rather than being silently skipped.

sdc_metadata (config, optional, null skips it): the same kind of join, for what the
disconnectome maps measure - assets/metadata/sdc_metadata.csv, written by
src.pipeline.compute_sdc_metadata (how disconnected each subject is overall, on the 1mm grid).

- `path`: that CSV. compute_sdc_metadata owns every decision about HOW a map is measured
  (the grid, the brain mask, the interpolation); none of those settings appear here.
- `copy_columns`: columns copied across under the SAME name, for every in-scope subject,
  under the run's `overwrite` rule - exactly as for lesion_metadata, and with the same strict join, only against
  `has_sdc` instead of `has_lesion`: a subject flagged has_sdc=True with no row means the CSV
  is stale (re-run compute_sdc_metadata), and a row for a subject the registry does not know -
  or knows as has_sdc=False - means the two files disagree about who has SDC output.

Two kinds of gap are reported and are NOT errors:
- a variable absent from one dataset's tsv entirely (structural per-dataset gap,
  e.g. UCL-UK has no NIHSS column at all) - every subject of that dataset gets
  an empty cell, logged once at WARNING;
- a per-subject blank/"n/a" cell in a dataset that does have the column.

A subject present in participants.csv but absent from its own dataset's raw tsv
IS an error: the two files disagree about who exists, which populate_metadata's
own inner join should have made impossible.

`overwrite` (config, required) - one rule for EVERY column this script writes (clinical
variables, lesion_side_source, and the copy_columns of both joins):
- false - append: only empty cells are written (a new subject, a new column, a gap the raw tsv
          has since filled); a cell that already holds a value is left exactly as it is. An
          existing value that differs from the freshly resolved one is logged at WARNING, per
          column, so a stale value is never kept in silence.
- true  - rewrite: every in-scope cell is recomputed and replaced, including with an empty one.

`protected_path` (config, required, null for none) - a JSON file, assets/metadata/
participants_protected.json, `{"columns": [...], "subjects": [...]}`. A cell whose column is
listed or whose subject is listed is never written, in either mode - the way to keep a
hand-corrected column or subject through an `overwrite: true` run. Every listed subject must be
in participants.csv, and every listed column must be one this config writes and one that already
exists in participants.csv; anything else raises (a typo would otherwise protect nothing, in
silence). `lesion_side` and `lesion_side_source` move together: protecting one column requires
protecting the other.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.metadata_sources import DatasetSource, load_metadata_sources
from src.utils.participants import load_participants_registry
from src.utils.logging_setup import attach_file_handler, log_duration

REPORTS_ROOT = Path("summaries") / "enrich_metadata"
LOGS_ROOT = Path("logs") / "enrich_metadata"
REPORT_FILENAME_PREFIX = "enrich_summary"

# Columns this script owns. populate_metadata.py owns the rest and is never
# allowed to be overwritten from here (and vice versa).
KNOWN_VARIABLES = ("age", "sex", "education", "lesion_side", "NIHSS", "clinical_date")
LESION_SIDE_VARIABLE = "lesion_side"
LESION_SIDE_SOURCE_COLUMN = "lesion_side_source"
LESION_SIDE_SOURCE_CLINICAL = "clinical"
LESION_SIDE_SOURCE_GEOMETRIC = "geometric"
_MEASURED_KEY_COLUMNS = ("subject_id", "dataset")
# Columns src/pipeline/populate_metadata.py owns - "who exists". A lesion_metadata column may never be
# copied onto one of them: the two scripts never overwrite each other's work (see module
# docstring), and a copy_columns entry naming one of these would silently break that rule.
_REGISTRY_OWNED_COLUMNS = ("subject_id", "original_id", "dataset", "disease_id",
                           "has_lesion", "has_sdc", "has_features")
_LESION_FLAG_COLUMN = "has_lesion"
_SDC_FLAG_COLUMN = "has_sdc"

# The only missing-value sentinel observed in the real participants.tsv files
# (verified 27/07/26); a genuinely empty field is already NaN from read_csv.
_MISSING_SENTINEL = "n/a"

# Deliberate, reviewable per-dataset substitutions: a variable read from a
# differently-named column because the canonical one does not exist for that
# cohort. Every substitution is logged at WARNING and listed in the run report -
# it is a clinical equivalence assumption, so it must never be invisible.
# PASPORT has no baseline NIHSS at all, only NIHSS_at_presentation/24H/3m
# (docs/dev/metadata.md, "Due eccezioni che enrich dovrà codificare esplicitamente").
VARIABLE_SOURCE_OVERRIDES: dict[tuple[str, str], str] = {
    ("UNIPD/PASPORT", "NIHSS"): "NIHSS_at_presentation",
}


@dataclass(frozen=True)
class LesionMetadataJoin:
    """How to join assets/metadata/lesion_metadata.csv onto the registry - see module docstring.

    copy_columns are copied under their own name for every in-scope subject, overwriting.
    lesion_side_from (optional) has a different rule - fill-only-where-empty, plus
    lesion_side_source - which is why it is not just another entry in copy_columns.
    geometric_override_datasets is the one exception to "never overwrite a clinical side"."""

    path: Path
    copy_columns: list[str]
    lesion_side_from: str | None
    geometric_override_datasets: list[str]


@dataclass(frozen=True)
class SdcMetadataJoin:
    """How to join assets/metadata/sdc_metadata.csv onto the registry - see module docstring.

    Only copy_columns, no counterpart of lesion_side_from/geometric_override_datasets: every
    column the disconnection CSV holds is a plain per-subject measurement to copy, none of them
    fills a gap in a clinical variable."""

    path: Path
    copy_columns: list[str]


@dataclass(frozen=True)
class ProtectedCells:
    """What a run must leave intact in participants.csv - see module docstring.

    A cell is protected when its column is in `columns` OR its subject is in `subjects`; a
    protected cell is never written, whatever `overwrite` says."""

    path: Path
    columns: list[str]
    subjects: list[str]


@dataclass(frozen=True)
class EnrichMetadataConfig:
    project: str
    sources: dict[str, DatasetSource]
    participants_path: Path
    datasets: list[str] | None
    variables: list[str]
    lesion_metadata: LesionMetadataJoin | None
    sdc_metadata: SdcMetadataJoin | None
    overwrite: bool
    protected: ProtectedCells | None
    run_notes: str


@dataclass(frozen=True)
class DatasetCoverage:
    """What one dataset could and could not supply, for the run report."""

    dataset: str
    n_subjects: int
    missing_variables: list[str]
    substituted: dict[str, str]
    n_missing_cells: dict[str, int]


# --- config ---------------------------------------------------------------------------------


def load_config(path: str | Path) -> EnrichMetadataConfig:
    """Load and validate an enrich_metadata.json file.

    Every field is validated before any file is read, so a typo'd variable name
    fails immediately instead of after every dataset has been parsed.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(raw).__name__}")
    for key in (
        "project", "metadata_sources", "participants_path", "variables", "overwrite", "protected_path", "run_notes"
    ):
        if key not in raw:
            raise ValueError(f"{path}: missing required key {key!r}")
    if not isinstance(raw["overwrite"], bool):
        raise ValueError(f"{path}: 'overwrite' must be a boolean, got {raw['overwrite']!r}")

    variables = _unique_str_list(raw["variables"], "variables", path)
    if not variables:
        raise ValueError(f"{path}: 'variables' is empty - nothing to enrich")
    unknown = [v for v in variables if v not in KNOWN_VARIABLES]
    if unknown:
        raise ValueError(f"{path}: unknown variable(s) {unknown}; known: {list(KNOWN_VARIABLES)}")

    sources = load_metadata_sources(Path(raw["metadata_sources"]))
    datasets = None if raw.get("datasets") is None else _unique_str_list(raw["datasets"], "datasets", path)
    if datasets is not None:
        if not datasets:
            raise ValueError(f"{path}: 'datasets' is an empty list - use null to mean 'every dataset'")
        missing = [d for d in datasets if d not in sources]
        if missing:
            raise ValueError(f"{path}: dataset(s) not in {raw['metadata_sources']}: {missing}")

    lesion_metadata = _load_lesion_metadata_config(raw.get("lesion_metadata"), variables, path)
    sdc_metadata = _load_sdc_metadata_config(raw.get("sdc_metadata"), lesion_metadata, path)
    protected = _load_protected(raw["protected_path"], path)

    return EnrichMetadataConfig(
        project=str(raw["project"]),
        sources=sources,
        participants_path=Path(str(raw["participants_path"])),
        datasets=datasets,
        variables=variables,
        lesion_metadata=lesion_metadata,
        sdc_metadata=sdc_metadata,
        overwrite=raw["overwrite"],
        protected=protected,
        run_notes=str(raw["run_notes"]),
    )


_PROTECTED_KEYS = {"columns", "subjects"}


def _load_protected(raw_path: object, config_path: Path) -> ProtectedCells | None:
    """Parse the file named by 'protected_path' - null means nothing is protected.

    Shape/type validated here; whether each column and subject exists is checked against the real
    participants.csv, by _check_protected, since that needs the registry."""
    if raw_path is None:
        return None
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError(f"{config_path}: 'protected_path' must be a non-empty string or null")
    path = Path(raw_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"{config_path}: 'protected_path' {path} not found - create it as "
            '{"columns": [], "subjects": []}, or set protected_path to null for no protection'
        )
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != _PROTECTED_KEYS:
        found = sorted(raw) if isinstance(raw, dict) else type(raw).__name__
        raise ValueError(f"{path}: expected an object with exactly the keys {sorted(_PROTECTED_KEYS)}, got {found}")
    return ProtectedCells(
        path=path,
        columns=_unique_str_list(raw["columns"], "columns", path),
        subjects=_unique_str_list(raw["subjects"], "subjects", path),
    )


def _load_lesion_metadata_config(raw_block: object, variables: list[str], path: Path) -> LesionMetadataJoin | None:
    """Parse the optional 'lesion_metadata' block - null (the default) skips the CSV entirely.

    Shape/type validated here; whether each named column actually exists is checked against the
    CSV itself (read_lesion_metadata), because the CSV's metric columns are named after the
    grids src.pipeline.compute_lesion_metadata was configured with - so there is no fixed
    vocabulary to check against at config-load time, only the real file.
    """
    if raw_block is None:
        return None
    if not isinstance(raw_block, dict):
        raise ValueError(f"{path}: 'lesion_metadata' must be an object or null")
    for key in ("path", "copy_columns", "lesion_side_from", "geometric_override_datasets"):
        if key not in raw_block:
            raise ValueError(f"{path}: 'lesion_metadata' is missing required key {key!r}")
    if not isinstance(raw_block["path"], str) or not raw_block["path"]:
        raise ValueError(f"{path}: 'lesion_metadata.path' must be a non-empty string")

    copy_columns = _unique_str_list(raw_block["copy_columns"], "lesion_metadata.copy_columns", path)
    owned = [c for c in copy_columns if c in _REGISTRY_OWNED_COLUMNS]
    if owned:
        raise ValueError(
            f"{path}: 'lesion_metadata.copy_columns' names column(s) {owned} owned by "
            "src/pipeline/populate_metadata.py - the two scripts never overwrite each other's columns"
        )

    lesion_side_from = raw_block["lesion_side_from"]
    if lesion_side_from is not None:
        if not isinstance(lesion_side_from, str) or not lesion_side_from:
            raise ValueError(f"{path}: 'lesion_metadata.lesion_side_from' must be a non-empty string or null")
        if LESION_SIDE_VARIABLE not in variables:
            raise ValueError(
                f"{path}: 'lesion_metadata.lesion_side_from' is set but {LESION_SIDE_VARIABLE!r} is not in "
                "'variables' - there is no clinical resolution for it to fill the gaps of"
            )
        if lesion_side_from in copy_columns:
            raise ValueError(
                f"{path}: {lesion_side_from!r} is both 'lesion_side_from' and in 'copy_columns' - it would be "
                f"copied verbatim AND used to fill {LESION_SIDE_VARIABLE!r}, writing the same fact twice under "
                "two names with two different rules"
            )
    if not copy_columns and lesion_side_from is None:
        raise ValueError(
            f"{path}: 'lesion_metadata' is set but 'copy_columns' is empty and 'lesion_side_from' is null - "
            "nothing to copy; use null to disable the block entirely"
        )

    override_datasets = _unique_str_list(
        raw_block["geometric_override_datasets"], "lesion_metadata.geometric_override_datasets", path
    )
    if override_datasets and lesion_side_from is None:
        raise ValueError(
            f"{path}: 'lesion_metadata.geometric_override_datasets' is {override_datasets} but "
            "'lesion_side_from' is null - there is no geometric side to force"
        )

    return LesionMetadataJoin(
        path=Path(raw_block["path"]), copy_columns=copy_columns, lesion_side_from=lesion_side_from,
        geometric_override_datasets=override_datasets,
    )


def _load_sdc_metadata_config(
    raw_block: object, lesion_metadata: LesionMetadataJoin | None, path: Path
) -> SdcMetadataJoin | None:
    """Parse the optional 'sdc_metadata' block - null (the default) skips the CSV entirely.

    Shape/type validated here; whether each named column exists is checked against the CSV
    itself (read_sdc_metadata), whose column names carry the grid compute_sdc_metadata was
    configured with.

    A column named by both this block and lesion_metadata is rejected: two joins writing the
    same participants.csv column would leave it holding whichever ran second, with no error.
    """
    if raw_block is None:
        return None
    if not isinstance(raw_block, dict):
        raise ValueError(f"{path}: 'sdc_metadata' must be an object or null")
    for key in ("path", "copy_columns"):
        if key not in raw_block:
            raise ValueError(f"{path}: 'sdc_metadata' is missing required key {key!r}")
    if not isinstance(raw_block["path"], str) or not raw_block["path"]:
        raise ValueError(f"{path}: 'sdc_metadata.path' must be a non-empty string")

    copy_columns = _unique_str_list(raw_block["copy_columns"], "sdc_metadata.copy_columns", path)
    if not copy_columns:
        raise ValueError(
            f"{path}: 'sdc_metadata' is set but 'copy_columns' is empty - nothing to copy; "
            "use null to disable the block entirely"
        )
    owned = [c for c in copy_columns if c in _REGISTRY_OWNED_COLUMNS]
    if owned:
        raise ValueError(
            f"{path}: 'sdc_metadata.copy_columns' names column(s) {owned} owned by "
            "src/pipeline/populate_metadata.py - the two scripts never overwrite each other's columns"
        )
    clashing = [c for c in copy_columns if c in KNOWN_VARIABLES or c == LESION_SIDE_SOURCE_COLUMN]
    if lesion_metadata is not None:
        clashing += [c for c in copy_columns if c in lesion_metadata.copy_columns]
    if clashing:
        raise ValueError(
            f"{path}: 'sdc_metadata.copy_columns' names column(s) {sorted(set(clashing))} that another part of "
            "this config already writes - two writers for one participants.csv column"
        )
    return SdcMetadataJoin(path=Path(raw_block["path"]), copy_columns=copy_columns)


def _unique_str_list(value: object, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"{path}: {field!r} must be a list of non-empty strings")
    duplicates = sorted({v for v in value if value.count(v) > 1})
    if duplicates:
        raise ValueError(f"{path}: {field!r} has duplicate entrie(s): {duplicates}")
    return list(value)


# --- reading the sources --------------------------------------------------------------------


def _normalize_missing(value: object) -> object:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    return np.nan if text == "" or text == _MISSING_SENTINEL else text


def read_raw_participants(source: DatasetSource, dataset: str) -> pd.DataFrame:
    """One dataset's raw participants.tsv, indexed by its own participant_id.

    Read with dtype=str: these files carry ids with leading zeros and dates,
    both of which pandas' type inference would silently mangle.
    """
    if not source.participants_tsv.is_file():
        raise FileNotFoundError(f"{dataset}: raw participants.tsv not found at {source.participants_tsv}")
    participants = pd.read_csv(source.participants_tsv, sep="\t", dtype=str)
    if "participant_id" not in participants.columns:
        raise ValueError(
            f"{source.participants_tsv}: expected a 'participant_id' column, got {list(participants.columns)}"
        )
    duplicated = sorted(participants.loc[participants["participant_id"].duplicated(), "participant_id"])
    if duplicated:
        raise ValueError(f"{source.participants_tsv}: duplicate participant_id(s): {duplicated}")
    return participants.set_index("participant_id")


def source_column_for(dataset: str, variable: str, available: list[str]) -> str | None:
    """Which raw column supplies `variable` for `dataset` - None if that dataset
    simply doesn't have it (a structural gap, not an error).

    Resolution order: the canonical name if present, otherwise an explicitly
    registered substitution. A substitution is never guessed from a similar
    name - only VARIABLE_SOURCE_OVERRIDES' hand-written entries are honoured.
    """
    if variable in available:
        return variable
    override = VARIABLE_SOURCE_OVERRIDES.get((dataset, variable))
    if override is not None and override in available:
        return override
    return None


# --- per-dataset resolution -----------------------------------------------------------------


def resolve_dataset_values(
    dataset: str,
    source: DatasetSource,
    registry_rows: pd.DataFrame,
    variables: list[str],
) -> tuple[dict[str, dict[str, object]], DatasetCoverage]:
    """{variable: {subject_id: value}} for one dataset, plus its coverage record.

    Raises ValueError if a subject listed in participants.csv has no row in its
    own dataset's raw tsv - the two files disagreeing about who exists is a real
    inconsistency (populate_metadata's inner join should make it impossible),
    never a legitimate "missing value".
    """
    participants = read_raw_participants(source, dataset)
    available = list(participants.columns)

    unknown_ids = sorted(set(registry_rows["original_id"]) - set(participants.index))
    if unknown_ids:
        raise ValueError(
            f"{dataset}: {len(unknown_ids)} subject(s) in the registry have no row in "
            f"{source.participants_tsv} (original_id): {unknown_ids[:5]}"
        )

    values: dict[str, dict[str, object]] = {}
    missing_variables: list[str] = []
    substituted: dict[str, str] = {}
    n_missing_cells: dict[str, int] = {}

    for variable in variables:
        column = source_column_for(dataset, variable, available)
        if column is None:
            missing_variables.append(variable)
            values[variable] = {s: np.nan for s in registry_rows["subject_id"]}
            n_missing_cells[variable] = len(registry_rows)
            logging.warning(
                "dataset=%s: no %r column in %s - %d subject(s) left empty",
                dataset, variable, source.participants_tsv, len(registry_rows),
            )
            continue
        if column != variable:
            substituted[variable] = column
            logging.warning(
                "dataset=%s: %r resolved from column %r (registered substitution - a clinical "
                "equivalence assumption, see VARIABLE_SOURCE_OVERRIDES)", dataset, variable, column,
            )

        lookup = participants[column]
        per_subject = {
            row.subject_id: _normalize_missing(lookup.loc[row.original_id])
            for row in registry_rows.itertuples()
        }
        values[variable] = per_subject
        n_missing_cells[variable] = sum(1 for v in per_subject.values() if pd.isna(v))

    coverage = DatasetCoverage(
        dataset=dataset,
        n_subjects=len(registry_rows),
        missing_variables=missing_variables,
        substituted=substituted,
        n_missing_cells=n_missing_cells,
    )
    return values, coverage


def read_lesion_metadata(
    join: LesionMetadataJoin, registry: pd.DataFrame, datasets: list[str]
) -> pd.DataFrame:
    """Read assets/metadata/lesion_metadata.csv and check it agrees with the registry.

    Returned frame is indexed by subject_id, carrying only the columns this run copies. See
    _read_measured_csv for the parsing and the three strict join checks, here run against
    has_lesion."""
    requested = list(join.copy_columns) + ([] if join.lesion_side_from is None else [join.lesion_side_from])
    return _read_measured_csv(
        join.path, requested, registry, datasets,
        flag_column=_LESION_FLAG_COLUMN, producer="src.pipeline.compute_lesion_metadata",
        block="lesion_metadata", what="a lesion mask",
    )


def read_sdc_metadata(join: SdcMetadataJoin, registry: pd.DataFrame, datasets: list[str]) -> pd.DataFrame:
    """Read assets/metadata/sdc_metadata.csv and check it agrees with the registry - the same
    parsing and strict join as read_lesion_metadata, run against has_sdc."""
    return _read_measured_csv(
        join.path, list(join.copy_columns), registry, datasets,
        flag_column=_SDC_FLAG_COLUMN, producer="src.pipeline.compute_sdc_metadata",
        block="sdc_metadata", what="SDC output",
    )


def _read_measured_csv(
    path: Path,
    requested: list[str],
    registry: pd.DataFrame,
    datasets: list[str],
    *,
    flag_column: str,
    producer: str,
    block: str,
    what: str,
) -> pd.DataFrame:
    """Read one per-subject measurements CSV (lesion_metadata.csv, sdc_metadata.csv) and check it
    agrees with the registry.

    subject_id/dataset are read as str (never let pandas strip a leading zero); the metric
    columns keep their own inferred types, so a voxel count stays an integer.

    Three disagreements raise, none is skipped (see module docstring for why each is a real
    inconsistency rather than a missing value):

    - an in-scope subject flagged `flag_column`=True with no row in the CSV -> the CSV is stale;
    - a row whose subject_id is not in the registry at all -> a spurious row;
    - a row for a subject the registry records as `flag_column`=False -> the two files disagree
      about who has `what`.

    The first check is scoped to `datasets` (a run may legitimately enrich a subset of the
    cohort); the other two are global, since a row that matches nobody is wrong regardless of
    which datasets this run happens to touch.
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found - it is written by {producer}; "
            f"run that first, or set {block!r} to null to skip these columns"
        )
    key_dtypes = {column: str for column in _MEASURED_KEY_COLUMNS}
    measured = pd.read_csv(path, dtype=key_dtypes)

    missing_keys = [c for c in _MEASURED_KEY_COLUMNS if c not in measured.columns]
    if missing_keys:
        raise ValueError(f"{path}: missing required column(s) {missing_keys}")
    absent = [c for c in requested if c not in measured.columns]
    if absent:
        raise ValueError(
            f"{path}: column(s) {absent} requested by {block!r} are not in the file; "
            f"it has {list(measured.columns)}"
        )
    duplicated = sorted(measured.loc[measured["subject_id"].duplicated(), "subject_id"])
    if duplicated:
        raise ValueError(f"{path}: duplicate subject_id row(s): {duplicated}")

    _check_agrees_with_registry(path, measured, registry, datasets, flag_column, producer, what)
    return measured.set_index("subject_id")[requested]


def _check_agrees_with_registry(
    path: Path,
    measured_table: pd.DataFrame,
    registry: pd.DataFrame,
    datasets: list[str],
    flag_column: str,
    producer: str,
    what: str,
) -> None:
    """The three strict join checks of _read_measured_csv, kept apart from the parsing."""
    if flag_column not in registry.columns:
        raise ValueError(
            f"registry has no {flag_column!r} column - it is written by "
            f"src/pipeline/populate_metadata.py and is what says which subjects have {what} at all"
        )
    has_flag = registry[flag_column]
    if not pd.api.types.is_bool_dtype(has_flag):
        # NOT astype(bool): on a str-dtype registry (participants.csv is read with dtype=str)
        # that maps the string "False" to True, since any non-empty string is truthy - the
        # checks below would then silently invert. The registry must arrive already parsed,
        # which is what src.utils.participants.load_participants_registry is for.
        raise ValueError(
            f"registry column {flag_column!r} has dtype {has_flag.dtype} instead of bool - "
            "read participants.csv through src.utils.participants.load_participants_registry, "
            "which parses the has_* flags explicitly"
        )
    measured = set(measured_table["subject_id"])

    in_scope = registry["dataset"].isin(datasets)
    expected = set(registry.loc[in_scope & has_flag, "subject_id"])
    stale = sorted(expected - measured)
    if stale:
        raise ValueError(
            f"{path}: {len(stale)} in-scope subject(s) with {flag_column}=True have no row "
            f"(e.g. {stale[:5]}) - the file predates them; re-run {producer}"
        )

    unknown = sorted(measured - set(registry["subject_id"]))
    if unknown:
        raise ValueError(
            f"{path}: {len(unknown)} subject(s) have no row in the registry (e.g. {unknown[:5]}) - "
            "the two files disagree about who exists"
        )
    without_flag = sorted(measured & set(registry.loc[~has_flag, "subject_id"]))
    if without_flag:
        raise ValueError(
            f"{path}: {len(without_flag)} subject(s) are measured here but recorded as "
            f"{flag_column}=False in the registry (e.g. {without_flag[:5]}) - the two files "
            f"disagree about who has {what}"
        )


# --- assembling the enriched table ------------------------------------------------------------


def enrich(registry: pd.DataFrame, config: EnrichMetadataConfig) -> tuple[pd.DataFrame, list[DatasetCoverage]]:
    """Add the requested columns to `registry`, returning the new table and per-dataset coverage."""
    for column in ("subject_id", "original_id", "dataset"):
        if column not in registry.columns:
            raise ValueError(f"{config.participants_path}: missing required column {column!r}")

    datasets = config.datasets if config.datasets is not None else sorted(set(registry["dataset"]))
    unknown = sorted(set(datasets) - set(registry["dataset"]))
    if unknown:
        raise ValueError(f"dataset(s) {unknown} have no row in {config.participants_path}")
    _check_write_rules(registry, config)

    values_by_variable: dict[str, dict[str, object]] = {v: {} for v in config.variables}
    coverages: list[DatasetCoverage] = []
    for dataset in datasets:
        rows = registry.loc[registry["dataset"] == dataset, ["subject_id", "original_id"]]
        resolved, coverage = resolve_dataset_values(dataset, config.sources[dataset], rows, config.variables)
        for variable, per_subject in resolved.items():
            values_by_variable[variable].update(per_subject)
        coverages.append(coverage)
        logging.info(
            "%s: %d subject(s), missing variables=%s, substituted=%s",
            dataset, coverage.n_subjects, coverage.missing_variables or "-", coverage.substituted or "-",
        )

    out = registry.copy()
    in_scope = out["dataset"].isin(datasets)
    for variable in config.variables:
        fresh = out["subject_id"].map(values_by_variable[variable])
        _merge_column(out, variable, fresh, in_scope, config, config.overwrite)

    if LESION_SIDE_VARIABLE in config.variables:
        # From what the raw tsv resolved THIS run, not from out[lesion_side] after the merge: in
        # append mode the latter still holds an earlier geometric fill, which would then read as a
        # "clinical" source that contradicts the "geometric" one already recorded for it.
        resolved_side = out["subject_id"].map(values_by_variable[LESION_SIDE_VARIABLE]).notna()
        source = pd.Series(np.nan, index=out.index, dtype=object)
        source.loc[resolved_side] = LESION_SIDE_SOURCE_CLINICAL
        _merge_column(out, LESION_SIDE_SOURCE_COLUMN, source, in_scope, config, config.overwrite)

    if config.lesion_metadata is not None:
        join = config.lesion_metadata
        measured = read_lesion_metadata(join, registry, datasets)

        _copy_measured_columns(out, measured, join.copy_columns, in_scope, "lesion_metadata", join.path, config)

        if join.lesion_side_from is not None:
            missing = (
                in_scope & out[LESION_SIDE_VARIABLE].isna()
                & ~_protected_mask(out, config.protected, LESION_SIDE_VARIABLE)
            )
            if not missing.any():
                logging.info("lesion_metadata: every in-scope subject already has a clinical lesion_side")
            else:
                # Restricted to exactly the subjects whose cell is empty: the CSV has a side for
                # every measured subject, so an unrestricted copy would overwrite the clinical
                # values too - the one thing this branch must never do.
                missing_ids = set(out.loc[missing, "subject_id"])
                sides = {
                    subject_id: side
                    for subject_id, side in measured[join.lesion_side_from].items()
                    if subject_id in missing_ids and pd.notna(side)
                }
                # Append mode regardless of config.overwrite: `missing` already restricts this to
                # currently-empty cells, so this only ever writes into a gap the clinical
                # resolution left behind - and a recompute here would blank every other cell.
                _merge_column(out, LESION_SIDE_VARIABLE, out["subject_id"].map(sides), in_scope, config, False)
                _merge_column(
                    out, LESION_SIDE_SOURCE_COLUMN,
                    out["subject_id"].map({s: LESION_SIDE_SOURCE_GEOMETRIC for s in sides}),
                    in_scope, config, False,
                )
                logging.info(
                    "lesion_metadata: %d/%d subject(s) missing lesion_side filled from %s",
                    len(sides), int(missing.sum()), join.lesion_side_from,
                )
                # The final per-subject state, split by cause, so "why is this subject still
                # empty" never needs cross-referencing two warnings and participants.csv by hand.
                still_missing = missing_ids - set(sides)
                if still_missing:
                    no_side = sorted(s for s in still_missing if s in measured.index)
                    if no_side:
                        logging.warning(
                            "lesion_metadata: %d subject(s) remain without lesion_side - measured, but "
                            "%s is empty for them (no side attributable to their mask): %s",
                            len(no_side), join.lesion_side_from, no_side,
                        )
                    unmeasured = sorted(s for s in still_missing if s not in measured.index)
                    if unmeasured:
                        logging.warning(
                            "lesion_metadata: %d subject(s) remain without lesion_side - no clinical value "
                            "and no row in %s (they have no lesion mask): %s",
                            len(unmeasured), join.path, unmeasured,
                        )
            _force_geometric_side_on_inversions(
                out, measured[join.lesion_side_from], join, in_scope, config.protected
            )

    if config.sdc_metadata is not None:
        sdc_join = config.sdc_metadata
        sdc_measured = read_sdc_metadata(sdc_join, registry, datasets)
        _copy_measured_columns(
            out, sdc_measured, sdc_join.copy_columns, in_scope, "sdc_metadata", sdc_join.path, config
        )

    return out, coverages


def _written_columns(config: EnrichMetadataConfig) -> list[str]:
    """Every participants.csv column this config can write - what a protected column must be one of."""
    columns = list(config.variables)
    if LESION_SIDE_VARIABLE in config.variables:
        columns.append(LESION_SIDE_SOURCE_COLUMN)
    if config.lesion_metadata is not None:
        columns += config.lesion_metadata.copy_columns
    if config.sdc_metadata is not None:
        columns += config.sdc_metadata.copy_columns
    return columns


def _check_write_rules(registry: pd.DataFrame, config: EnrichMetadataConfig) -> None:
    """The cross-checks of `overwrite` and the protected file against the real registry.

    Here and not in load_config because they need participants.csv, and because tests (and any
    caller) build an EnrichMetadataConfig directly: the one always-run place is enrich()."""
    join = config.lesion_metadata
    if join is not None and join.geometric_override_datasets and not config.overwrite:
        raise ValueError(
            f"'lesion_metadata.geometric_override_datasets' is {join.geometric_override_datasets} but "
            "'overwrite' is false: the override replaces a filled lesion_side, which append mode never does"
        )
    protected = config.protected
    if protected is None:
        return
    unknown_subjects = sorted(set(protected.subjects) - set(registry["subject_id"]))
    if unknown_subjects:
        raise ValueError(
            f"{protected.path}: subject(s) {unknown_subjects} are not in {config.participants_path} - "
            "a misspelt id would protect nothing"
        )
    written = _written_columns(config)
    not_written = [c for c in protected.columns if c not in written]
    if not_written:
        raise ValueError(
            f"{protected.path}: column(s) {not_written} are not written by this config (it writes "
            f"{sorted(written)}), so protecting them does nothing - probably a typo"
        )
    not_in_table = [c for c in protected.columns if c not in registry.columns]
    if not_in_table:
        raise ValueError(
            f"{protected.path}: column(s) {not_in_table} do not exist in {config.participants_path} yet - "
            "protection keeps what is already there, and there is nothing to keep"
        )
    pair = {LESION_SIDE_VARIABLE, LESION_SIDE_SOURCE_COLUMN}
    listed = pair & set(protected.columns)
    if listed and listed != pair:
        raise ValueError(
            f"{protected.path}: {sorted(listed)} is protected without {sorted(pair - listed)} - "
            "lesion_side and lesion_side_source describe the same fact and must be protected together"
        )


def _protected_mask(out: pd.DataFrame, protected: ProtectedCells | None, column: str) -> pd.Series:
    """True for every row whose cell in `column` must not be written."""
    if protected is None:
        return pd.Series(False, index=out.index)
    if column in protected.columns:
        return pd.Series(True, index=out.index)
    return out["subject_id"].isin(protected.subjects)


def _merge_column(
    out: pd.DataFrame, column: str, fresh: pd.Series, in_scope: pd.Series, config: EnrichMetadataConfig,
    overwrite: bool,
) -> None:
    """Merge `fresh` into out[column], IN PLACE, under `overwrite` and the run's protected cells."""
    out[column] = _apply(
        out.get(column), fresh, in_scope, overwrite, _protected_mask(out, config.protected, column), column
    )


def _copy_measured_columns(
    out: pd.DataFrame, measured: pd.DataFrame, columns: list[str], in_scope: pd.Series, block: str, path: Path,
    config: EnrichMetadataConfig,
) -> None:
    """Copy `columns` of a per-subject measurements frame (indexed by subject_id) onto `out`,
    IN PLACE, under the same name, for every in-scope subject, under `config.overwrite`."""
    for column in columns:
        values = measured[column]
        fresh = out["subject_id"].map(values)
        # Nullable Int64 for an integer source column, not the float64 a plain map() yields:
        # subjects outside this run's scope are absent from `values`, introducing a NaN that
        # promotes the whole column to float and would write a voxel *count* as "4616.0".
        # Int64 keeps NA and stays integral (the out-of-scope rows are dropped by _apply
        # anyway, but the dtype is decided before that).
        if pd.api.types.is_integer_dtype(values):
            fresh = fresh.astype("Int64")
        _merge_column(out, column, fresh, in_scope, config, config.overwrite)
        logging.info(
            "%s: %d/%d subject(s) matched for %s (from %s)", block, int(fresh.notna().sum()), len(out), column, path
        )


_OPPOSITE_SIDE = {"left": "right", "right": "left"}


def _force_geometric_side_on_inversions(
    out: pd.DataFrame, geometric_side: pd.Series, join: LesionMetadataJoin, in_scope: pd.Series,
    protected: ProtectedCells | None,
) -> None:
    """Overwrite, IN PLACE on `out`, the clinical lesion_side of every subject of a
    `geometric_override_datasets` dataset whose clinical side is the exact opposite of
    `geometric_side` (indexed by subject_id) - and mark it lesion_side_source="geometric".
    A protected lesion_side is never overridden.

    Only a left/right clash triggers it: a geometric `both` (or an empty side) never overrides a
    clinical left/right, because that is a disagreement of degree, not the full inversion this
    exists for. Each overridden subject is logged at WARNING - this deliberately contradicts the
    dataset's own tsv, so it must never be invisible.
    """
    unknown = sorted(set(join.geometric_override_datasets) - set(out["dataset"]))
    if unknown:
        raise ValueError(
            f"'lesion_metadata.geometric_override_datasets' names dataset(s) {unknown} that have no row "
            "in the registry"
        )
    clinical = in_scope & out["dataset"].isin(join.geometric_override_datasets) & (
        out[LESION_SIDE_SOURCE_COLUMN] == LESION_SIDE_SOURCE_CLINICAL
    ) & ~_protected_mask(out, protected, LESION_SIDE_VARIABLE)
    measured_side = out["subject_id"].map(geometric_side)
    inverted = clinical & out[LESION_SIDE_VARIABLE].map(_OPPOSITE_SIDE).eq(measured_side)
    if not inverted.any():
        return
    forced = sorted(out.loc[inverted, "subject_id"])
    logging.warning(
        "lesion_side: %d subject(s) have a clinical side opposite to their mask (%s) - registry forced "
        "to the geometric side, lesion_side_source=%s: %s",
        len(forced), join.lesion_side_from, LESION_SIDE_SOURCE_GEOMETRIC, forced,
    )
    out.loc[inverted, LESION_SIDE_VARIABLE] = measured_side[inverted]
    out.loc[inverted, LESION_SIDE_SOURCE_COLUMN] = LESION_SIDE_SOURCE_GEOMETRIC


def _apply(
    existing: pd.Series | None,
    fresh: pd.Series,
    in_scope: pd.Series,
    overwrite: bool,
    protected: pd.Series,
    column: str,
) -> pd.Series:
    """Merge freshly resolved values into an existing column, honouring `overwrite`.

    Out-of-scope rows (a dataset this run didn't touch) and protected rows always keep whatever
    they had - a partial run never blanks a dataset it wasn't asked about. In append mode
    (overwrite=False) only empty cells are written; an existing value that differs from the
    fresh one is kept and counted at WARNING, never dropped or kept in silence.
    """
    writable_scope = in_scope & ~protected
    if existing is None:
        return fresh.where(writable_scope, np.nan)
    # astype(object) first: participants.csv is read with dtype=str, and pandas' "str"
    # dtype rejects a NaN assignment outright (TypeError). A re-run over an
    # already-enriched file always writes some NaN back (a subject whose value is
    # genuinely missing), so without this the second run of any variable fails while
    # the first one - when the column didn't exist yet and this branch was skipped
    # entirely - looked fine (.claude/lessons_learned.md #17).
    kept = existing.astype(object).copy()
    if overwrite:
        kept.loc[writable_scope] = fresh.loc[writable_scope]
        return kept
    writable = writable_scope & existing.isna()
    kept.loc[writable] = fresh.loc[writable]
    # Compared as text: participants.csv is read with dtype=str, so the stored side of the
    # comparison is always a string, whatever type the fresh one has.
    both = writable_scope & existing.notna() & fresh.notna()
    differing = both & (existing.astype(str) != fresh.astype(str))
    if differing.any():
        logging.warning(
            "%s: %d existing value(s) differ from the freshly resolved one and were kept "
            "(overwrite=false) - set overwrite to true to replace them, or fix the source",
            column, int(differing.sum()),
        )
    return kept


def write_table(table: pd.DataFrame, output_path: Path) -> None:
    """Atomic write (temp file + os.replace) - same guarantee as populate_metadata.py:
    a crash never leaves a half-written participants file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_path.name}_tmp_", dir=output_path.parent)
    os.close(fd)
    try:
        table.to_csv(tmp_name, index=False)
        os.replace(tmp_name, output_path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


# --- report ---------------------------------------------------------------------------------


def _lesion_metadata_summary(join: LesionMetadataJoin | None) -> str:
    """JSON dump of the lesion_metadata block (or 'null'), not the dataclass's own repr() -
    the latter is illegible in a report meant to be read as a document."""
    if join is None:
        return "null"
    payload = {
        "path": str(join.path),
        "copy_columns": join.copy_columns,
        "lesion_side_from": join.lesion_side_from,
        "geometric_override_datasets": join.geometric_override_datasets,
    }
    return json.dumps(payload, indent=2)


def _protected_summary(protected: ProtectedCells | None) -> str:
    """One report line naming what the run left intact, so a protected cell is never an invisible reason a
    value did not change."""
    if protected is None:
        return "protected: none"
    return (
        f"protected (`{protected.path}`): columns {protected.columns or 'none'} · "
        f"{len(protected.subjects)} subject(s) {protected.subjects or ''}".rstrip()
    )


def _sdc_metadata_summary(join: SdcMetadataJoin | None) -> str:
    """JSON dump of the sdc_metadata block (or 'null') - see _lesion_metadata_summary."""
    if join is None:
        return "null"
    return json.dumps({"path": str(join.path), "copy_columns": join.copy_columns}, indent=2)


def report_lines(config: EnrichMetadataConfig, coverages: list[DatasetCoverage], now: datetime) -> list[str]:
    lines = [
        f"# enrich_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"file: `{config.participants_path}` · overwrite: {config.overwrite} · variables: {', '.join(config.variables)}",
        "",
        _protected_summary(config.protected),
        "",
        "lesion_metadata:",
        "```json",
        _lesion_metadata_summary(config.lesion_metadata),
        "```",
        "",
        "sdc_metadata:",
        "```json",
        _sdc_metadata_summary(config.sdc_metadata),
        "```",
        "",
        f"notes: {config.run_notes}",
        "",
        "## Celle vuote per dataset e variabile",
        "",
        "| dataset | soggetti | " + " | ".join(config.variables) + " |",
        "|---" * (len(config.variables) + 2) + "|",
    ]
    for coverage in coverages:
        cells = []
        for variable in config.variables:
            n = coverage.n_missing_cells.get(variable, 0)
            cells.append("— (assente)" if variable in coverage.missing_variables else f"{n}")
        lines.append(f"| {coverage.dataset} | {coverage.n_subjects} | " + " | ".join(cells) + " |")

    substitutions = {c.dataset: c.substituted for c in coverages if c.substituted}
    if substitutions:
        lines += ["", "## Sostituzioni di colonna applicate", "",
                  "Assunzioni di equivalenza clinica registrate in `VARIABLE_SOURCE_OVERRIDES`, non dedotte:", ""]
        for dataset, mapping in substitutions.items():
            for variable, column in mapping.items():
                lines.append(f"- **{dataset}**: `{variable}` letta da `{column}`")
    return lines


def write_report(config: EnrichMetadataConfig, coverages: list[DatasetCoverage], now: datetime) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(report_lines(config, coverages, now)) + "\n")
    return report_path


# --- entry point ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add clinical/demographic attributes to participants.csv.")
    parser.add_argument("--config", required=True, help="Path to an enrich_metadata.json config")
    parser.add_argument("--dry-run", action="store_true", help="Run every check and write the report, but not the table")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    now = datetime.now()
    try:
        try:
            config = load_config(args.config)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            logging.error(str(exc))
            return 1

        try:
            LOGS_ROOT.mkdir(parents=True, exist_ok=True)
            attach_file_handler(LOGS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log")
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        try:
            # Through src.utils.participants, not a raw read_csv: it is the module that owns this
            # file, and it validates the has_* flags into real bools - which the lesion_metadata
            # join below needs (has_lesion is what says who should have a row in the CSV).
            registry = load_participants_registry(config.participants_path)
            table, coverages = enrich(registry, config)
        except (FileNotFoundError, ValueError) as exc:
            # No ImageFileError any more: this pipeline opens no NIfTI file at all since the
            # mask-derived columns became a join onto assets/metadata/lesion_metadata.csv.
            logging.error(str(exc))
            return 1

        try:
            report_path = write_report(config, coverages, now)
            if args.dry_run:
                logging.info("dry-run - nothing written to %s, report at %s", config.participants_path, report_path)
                return 0
            write_table(table, config.participants_path)
        except OSError as exc:
            logging.error("cannot write output: %s", exc, exc_info=True)
            return 1

        logging.info(
            "done - %d subject(s) in %s, report written to %s", len(table), config.participants_path, report_path
        )
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
