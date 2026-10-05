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
  subject, overwriting whatever was there. Each must exist in the CSV and must
  not be a column src/pipeline/populate_metadata.py owns.
- `lesion_side_from`: which CSV column fills `lesion_side`. Its rule differs from
  copy_columns, which is why it is a separate key: it writes ONLY where the
  clinical resolution above left the cell empty, and it also writes
  lesion_side_source="geometric". Outside `geometric_override_datasets` a clinical
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
  `lesion_side_from`.

The join is on subject_id and is strict in both directions: a subject with
has_lesion=True but no row in the CSV means the CSV is stale (re-run
compute_lesion_metadata), and a row in the CSV for a subject the registry does not
know - or knows as has_lesion=False - means the two files disagree about who has a
mask. Both raise rather than being silently skipped.

Mask-derived columns are NOT hand-correctable in participants.csv: every run
copies them over. A value found unreliable in analysis is fixed at the source (the
mask, then re-run compute_lesion_metadata) or the subject goes into
assets/metadata/excluded_subjects.csv - never by editing a cell that the next run
will overwrite anyway. The clinical columns read from the raw tsvs keep the `fill`
semantics below.

Two kinds of gap are reported and are NOT errors:
- a variable absent from one dataset's tsv entirely (structural per-dataset gap,
  e.g. UCL-UK has no NIHSS column at all) - every subject of that dataset gets
  an empty cell, logged once at WARNING;
- a per-subject blank/"n/a" cell in a dataset that does have the column.

A subject present in participants.csv but absent from its own dataset's raw tsv
IS an error: the two files disagree about who exists, which populate_metadata's
own inner join should have made impossible.

`fill` (config):
- true  - only empty cells of the requested variables are written; any value
          already present is left exactly as it is.
- false - every requested variable is recomputed for every in-scope subject.
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
_LESION_METADATA_KEY_COLUMNS = ("subject_id", "dataset")
# Columns src/pipeline/populate_metadata.py owns - "who exists". A lesion_metadata column may never be
# copied onto one of them: the two scripts never overwrite each other's work (see module
# docstring), and a copy_columns entry naming one of these would silently break that rule.
_REGISTRY_OWNED_COLUMNS = ("subject_id", "original_id", "dataset", "disease_id",
                           "has_lesion", "has_sdc", "has_features")
_LESION_FLAG_COLUMN = "has_lesion"

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
class EnrichMetadataConfig:
    project: str
    sources: dict[str, DatasetSource]
    participants_path: Path
    datasets: list[str] | None
    variables: list[str]
    lesion_metadata: LesionMetadataJoin | None
    fill: bool
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
    for key in ("project", "metadata_sources", "participants_path", "variables", "fill", "run_notes"):
        if key not in raw:
            raise ValueError(f"{path}: missing required key {key!r}")
    if not isinstance(raw["fill"], bool):
        raise ValueError(f"{path}: 'fill' must be a boolean, got {raw['fill']!r}")

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

    return EnrichMetadataConfig(
        project=str(raw["project"]),
        sources=sources,
        participants_path=Path(str(raw["participants_path"])),
        datasets=datasets,
        variables=variables,
        lesion_metadata=lesion_metadata,
        fill=raw["fill"],
        run_notes=str(raw["run_notes"]),
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

    Returned frame is indexed by subject_id, carrying only the columns this run copies.
    subject_id/dataset are read as str (never let pandas strip a leading zero); the metric
    columns keep their own inferred types, so a voxel count stays an integer.

    Three disagreements raise, none is skipped (see module docstring for why each is a real
    inconsistency rather than a missing value):

    - an in-scope subject with has_lesion=True and no row in the CSV -> the CSV is stale;
    - a row whose subject_id is not in the registry at all -> a spurious row;
    - a row for a subject the registry records as has_lesion=False -> the two files disagree
      about who has a mask.

    The first check is scoped to `datasets` (a run may legitimately enrich a subset of the
    cohort); the other two are global, since a row that matches nobody is wrong regardless of
    which datasets this run happens to touch.
    """
    if not join.path.is_file():
        raise FileNotFoundError(
            f"{join.path} not found - it is written by src.pipeline.compute_lesion_metadata; "
            "run that first, or set 'lesion_metadata' to null to skip the mask-derived columns"
        )
    key_dtypes = {column: str for column in _LESION_METADATA_KEY_COLUMNS}
    lesion_metadata = pd.read_csv(join.path, dtype=key_dtypes)

    missing_keys = [c for c in _LESION_METADATA_KEY_COLUMNS if c not in lesion_metadata.columns]
    if missing_keys:
        raise ValueError(f"{join.path}: missing required column(s) {missing_keys}")
    requested = list(join.copy_columns) + ([] if join.lesion_side_from is None else [join.lesion_side_from])
    absent = [c for c in requested if c not in lesion_metadata.columns]
    if absent:
        raise ValueError(
            f"{join.path}: column(s) {absent} requested by 'lesion_metadata' are not in the file; "
            f"it has {list(lesion_metadata.columns)}"
        )
    duplicated = sorted(lesion_metadata.loc[lesion_metadata["subject_id"].duplicated(), "subject_id"])
    if duplicated:
        raise ValueError(f"{join.path}: duplicate subject_id row(s): {duplicated}")

    _check_agrees_with_registry(join.path, lesion_metadata, registry, datasets)
    return lesion_metadata.set_index("subject_id")[requested]


def _check_agrees_with_registry(
    path: Path, lesion_metadata: pd.DataFrame, registry: pd.DataFrame, datasets: list[str]
) -> None:
    """The three strict join checks of read_lesion_metadata, kept apart from the parsing."""
    if _LESION_FLAG_COLUMN not in registry.columns:
        raise ValueError(
            f"registry has no {_LESION_FLAG_COLUMN!r} column - it is written by "
            "src/pipeline/populate_metadata.py and is what says which subjects have a mask at all"
        )
    has_mask = registry[_LESION_FLAG_COLUMN]
    if not pd.api.types.is_bool_dtype(has_mask):
        # NOT astype(bool): on a str-dtype registry (participants.csv is read with dtype=str)
        # that maps the string "False" to True, since any non-empty string is truthy - the
        # checks below would then silently invert. The registry must arrive already parsed,
        # which is what src.utils.participants.load_participants_registry is for.
        raise ValueError(
            f"registry column {_LESION_FLAG_COLUMN!r} has dtype {has_mask.dtype} instead of bool - "
            "read participants.csv through src.utils.participants.load_participants_registry, "
            "which parses the has_* flags explicitly"
        )
    measured = set(lesion_metadata["subject_id"])

    in_scope = registry["dataset"].isin(datasets)
    expected = set(registry.loc[in_scope & has_mask, "subject_id"])
    stale = sorted(expected - measured)
    if stale:
        raise ValueError(
            f"{path}: {len(stale)} in-scope subject(s) with {_LESION_FLAG_COLUMN}=True have no row "
            f"(e.g. {stale[:5]}) - the file predates them; re-run src.pipeline.compute_lesion_metadata"
        )

    unknown = sorted(measured - set(registry["subject_id"]))
    if unknown:
        raise ValueError(
            f"{path}: {len(unknown)} subject(s) have no row in the registry (e.g. {unknown[:5]}) - "
            "the two files disagree about who exists"
        )
    without_mask = sorted(measured & set(registry.loc[~has_mask, "subject_id"]))
    if without_mask:
        raise ValueError(
            f"{path}: {len(without_mask)} subject(s) are measured here but recorded as "
            f"{_LESION_FLAG_COLUMN}=False in the registry (e.g. {without_mask[:5]}) - the two files "
            "disagree about who has a lesion mask"
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
        out[variable] = _apply(out.get(variable), fresh, in_scope, config.fill)

    if LESION_SIDE_VARIABLE in config.variables:
        resolved_side = out[LESION_SIDE_VARIABLE].notna()
        source = pd.Series(np.nan, index=out.index, dtype=object)
        source.loc[resolved_side] = LESION_SIDE_SOURCE_CLINICAL
        out[LESION_SIDE_SOURCE_COLUMN] = _apply(
            out.get(LESION_SIDE_SOURCE_COLUMN), source, in_scope, config.fill
        )

    if config.lesion_metadata is not None:
        join = config.lesion_metadata
        measured = read_lesion_metadata(join, registry, datasets)

        for column in join.copy_columns:
            values = measured[column]
            fresh = out["subject_id"].map(values)
            # Nullable Int64 for an integer source column, not the float64 a plain map() yields:
            # subjects outside this run's scope are absent from `values`, introducing a NaN that
            # promotes the whole column to float and would write a voxel *count* as "4616.0".
            # Int64 keeps NA and stays integral (the out-of-scope rows are dropped by _apply
            # anyway, but the dtype is decided before that).
            if pd.api.types.is_integer_dtype(values):
                fresh = fresh.astype("Int64")
            # fill=False regardless of config.fill: a mask-derived value is never hand-corrected
            # in participants.csv (see module docstring), so there is nothing to preserve - and
            # honouring fill=True would silently freeze a stale number after the masks changed.
            out[column] = _apply(out.get(column), fresh, in_scope, fill=False)
            logging.info(
                "lesion_metadata: %d/%d subject(s) matched for %s (from %s)",
                int(fresh.notna().sum()), len(out), column, join.path,
            )

        if join.lesion_side_from is not None:
            missing = in_scope & out[LESION_SIDE_VARIABLE].isna()
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
                # fill=True regardless of config.fill: `missing` already restricts this to
                # currently-empty cells, so this only ever writes into a gap the clinical
                # resolution left behind.
                out[LESION_SIDE_VARIABLE] = _apply(
                    out.get(LESION_SIDE_VARIABLE), out["subject_id"].map(sides), in_scope, fill=True
                )
                out[LESION_SIDE_SOURCE_COLUMN] = _apply(
                    out.get(LESION_SIDE_SOURCE_COLUMN),
                    out["subject_id"].map({s: LESION_SIDE_SOURCE_GEOMETRIC for s in sides}),
                    in_scope,
                    fill=True,
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
            _force_geometric_side_on_inversions(out, measured[join.lesion_side_from], join, in_scope)

    return out, coverages


_OPPOSITE_SIDE = {"left": "right", "right": "left"}


def _force_geometric_side_on_inversions(
    out: pd.DataFrame, geometric_side: pd.Series, join: LesionMetadataJoin, in_scope: pd.Series
) -> None:
    """Overwrite, IN PLACE on `out`, the clinical lesion_side of every subject of a
    `geometric_override_datasets` dataset whose clinical side is the exact opposite of
    `geometric_side` (indexed by subject_id) - and mark it lesion_side_source="geometric".

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
    )
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


def _apply(existing: pd.Series | None, fresh: pd.Series, in_scope: pd.Series, fill: bool) -> pd.Series:
    """Merge freshly resolved values into an existing column, honouring `fill`.

    Out-of-scope rows (a dataset this run didn't touch) always keep whatever
    they had - a partial run never blanks a dataset it wasn't asked about.
    """
    if existing is None:
        return fresh.where(in_scope, np.nan)
    # astype(object) first: participants.csv is read with dtype=str, and pandas' "str"
    # dtype rejects a NaN assignment outright (TypeError). A re-run over an
    # already-enriched file always writes some NaN back (a subject whose value is
    # genuinely missing), so without this the second run of any variable fails while
    # the first one - when the column didn't exist yet and this branch was skipped
    # entirely - looked fine (.claude/lessons_learned.md #17).
    kept = existing.astype(object).copy()
    writable = in_scope & (existing.isna() if fill else True)
    kept.loc[writable] = fresh.loc[writable]
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


def report_lines(config: EnrichMetadataConfig, coverages: list[DatasetCoverage], now: datetime) -> list[str]:
    lines = [
        f"# enrich_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"file: `{config.participants_path}` · fill: {config.fill} · variables: {', '.join(config.variables)}",
        "",
        "lesion_metadata:",
        "```json",
        _lesion_metadata_summary(config.lesion_metadata),
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
