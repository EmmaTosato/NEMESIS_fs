"""CLI entry point: add clinical/demographic attributes to the project's single
participant table - what we know about each subject.

The counterpart of scripts/populate_metadata.py (which answers "who exists"):
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
- lesion_volume_voxels is copied from an already-built lesion_matrix artifact's
  own metadata.csv (config.lesion_volume_from), never recomputed here: that
  column is build_lesion_matrix.py's own output, and recomputing it from raw
  masks would create a second, independently-drifting definition of the same
  quantity.

The join is on `original_id`, NOT on `subject_id`: a raw tsv's participant_id is
the canonical subject id for most datasets but the legacy site id for UCL-UK
("ST_UCL-UK_0001"). participants.csv already stores both, so it is the bridge -
joining on subject_id would silently match nothing for that whole dataset
(.claude/lessons_learned.md #30).

Missing values are a plain empty cell, uniformly, for every variable. This file
is a registry, not a plotting input: a consumer that needs a categorical
sentinel (e.g. "unknown" for a colour legend) applies its own on read. The one
exception carrying extra information is lesion_side_source, which records where
a lesion_side value came from ("clinical") so a later, geometrically computed
value stays distinguishable from a clinically recorded one.

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
LESION_VOLUME_COLUMN = "lesion_volume_voxels"

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
class EnrichMetadataConfig:
    project: str
    sources: dict[str, DatasetSource]
    participants_path: Path
    datasets: list[str] | None
    variables: list[str]
    lesion_volume_from: Path | None
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

    lesion_volume_from = raw.get("lesion_volume_from")
    if lesion_volume_from is not None and not isinstance(lesion_volume_from, str):
        raise ValueError(f"{path}: 'lesion_volume_from' must be a string path or null")

    return EnrichMetadataConfig(
        project=str(raw["project"]),
        sources=sources,
        participants_path=Path(str(raw["participants_path"])),
        datasets=datasets,
        variables=variables,
        lesion_volume_from=None if lesion_volume_from is None else Path(lesion_volume_from),
        fill=raw["fill"],
        run_notes=str(raw["run_notes"]),
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


def load_lesion_volumes(artifact_dir: Path) -> dict[str, int]:
    """lesion_volume_voxels per subject, from a build_lesion_matrix.py artifact.

    Read from that artifact's own metadata.csv rather than recomputed from its
    matrix.npy: the column is build_lesion_matrix's output and must have exactly
    one definition. An artifact predating the column raises, naming it - never
    silently skipped, and never re-derived here under a second definition.
    """
    metadata_path = artifact_dir / "metadata.csv"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"lesion_volume_from: no metadata.csv in {artifact_dir}")
    metadata = pd.read_csv(metadata_path)
    for column in ("subject_id", LESION_VOLUME_COLUMN):
        if column not in metadata.columns:
            raise ValueError(
                f"{metadata_path}: missing {column!r} column - this artifact predates "
                f"{LESION_VOLUME_COLUMN} and cannot supply it; rebuild it with build_lesion_matrix.py"
            )
    return dict(zip(metadata["subject_id"], metadata[LESION_VOLUME_COLUMN].astype(int)))


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

    if config.lesion_volume_from is not None:
        volumes = load_lesion_volumes(config.lesion_volume_from)
        # Nullable Int64, not the float64 a plain map() produces: a subject absent from
        # the lesion matrix introduces a NaN, which would promote the whole column to
        # float and write a voxel *count* as "4616.0". Int64 keeps NA and stays integral.
        fresh = out["subject_id"].map(volumes).astype("Int64")
        out[LESION_VOLUME_COLUMN] = _apply(out.get(LESION_VOLUME_COLUMN), fresh, in_scope, config.fill)
        logging.info(
            "lesion_volume_voxels: %d/%d subject(s) matched from %s",
            int(fresh.notna().sum()), len(out), config.lesion_volume_from,
        )

    return out, coverages


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


def report_lines(config: EnrichMetadataConfig, coverages: list[DatasetCoverage], now: datetime) -> list[str]:
    lines = [
        f"# enrich_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"file: `{config.participants_path}` · fill: {config.fill} · variables: {', '.join(config.variables)}",
        f"lesion_volume_from: {config.lesion_volume_from or '-'}",
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
            if not config.participants_path.is_file():
                raise FileNotFoundError(
                    f"{config.participants_path} not found - run scripts/populate_metadata.py first "
                    "(it creates the file this script enriches)"
                )
            registry = pd.read_csv(config.participants_path, dtype=str)
            table, coverages = enrich(registry, config)
        except (FileNotFoundError, ValueError) as exc:
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
