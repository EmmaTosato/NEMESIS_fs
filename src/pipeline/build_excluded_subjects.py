"""CLI entry point: build assets/metadata/excluded_subjects.csv from a config.

The config is the decision - which subjects are kept out of the production matrices, for which
reason and for which matrix (scope) - and the CSV is a file derived from it, never edited by hand.
Every subject is listed explicitly: there is no threshold or rule here, because the data have no
natural cut-off and which borderline subject is worth dropping is a judgement call, not a number
(docs/guides/metadata.md). What this script computes is only what a hand-written file would get
wrong: each row's `dataset` (from the registry) and `value` (the metric that motivated the
exclusion, from assets/metadata/lesion_metadata.csv, or a constant).

The whole file is written by this script, from every entry of the config: there is no merge with
rows already in the CSV, so a reason that no notebook knows about (all_zero_features) lives in the
config like any other.

Usage:
    conda activate nemesis
    python -m src.pipeline.build_excluded_subjects --config config/pipelines/build_excluded_subjects.json

The result is checked with the same validator the matrix pipelines use
(src.utils.participants.load_excluded_subjects), on a temporary file, BEFORE the real one is
replaced: a config that would write a file the matrix pipelines reject fails here instead.
--dry-run runs every check and writes the report, but not the CSV.
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

import pandas as pd

from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.participants import (
    KNOWN_EXCLUSION_REASONS,
    KNOWN_EXCLUSION_SCOPES,
    load_excluded_subjects,
    load_participants_registry,
)

REPORTS_ROOT = Path("summaries") / "build_excluded_subjects"
LOGS_ROOT = Path("logs") / "build_excluded_subjects"
REPORT_FILENAME_PREFIX = "excluded_summary"

OUTPUT_COLUMNS = ["subject_id", "dataset", "reason", "scope", "value"]
# A subject listed as an empty mask must really have no voxel: the value is the metric that
# motivated the exclusion, and a typo'd id would otherwise exclude somebody with a real lesion.
_EMPTY_MASK_REASON = "empty_mask"
_ENTRY_KEYS = {"reason", "scope", "subjects", "value_column", "value"}


@dataclass(frozen=True)
class ExclusionEntry:
    """One (reason, scope) group of the config. `value` comes from exactly one of two places:
    value_column (a column of lesion_metadata.csv, read per subject) or value (a constant)."""

    reason: str
    scope: str
    subjects: list[str]
    value_column: str | None
    value: float | None


@dataclass(frozen=True)
class BuildExcludedSubjectsConfig:
    project: str
    output_path: Path
    lesion_metadata_path: Path
    exclusions: list[ExclusionEntry]
    run_notes: str


# --- config ---------------------------------------------------------------------------------


def load_config(path: str | Path) -> BuildExcludedSubjectsConfig:
    """Load and validate a build_excluded_subjects.json file, before any data file is read."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(raw).__name__}")
    for key in ("project", "output_path", "lesion_metadata_path", "exclusions", "run_notes"):
        if key not in raw:
            raise ValueError(f"{path}: missing required key {key!r}")
    for key in ("output_path", "lesion_metadata_path"):
        if not isinstance(raw[key], str) or not raw[key]:
            raise ValueError(f"{path}: {key!r} must be a non-empty string")
    if not isinstance(raw["exclusions"], list):
        raise ValueError(f"{path}: 'exclusions' must be a list (an empty list means nobody is excluded)")

    entries = [_load_entry(item, index, path) for index, item in enumerate(raw["exclusions"])]
    pairs = [(e.reason, e.scope) for e in entries]
    repeated = sorted({p for p in pairs if pairs.count(p) > 1})
    if repeated:
        raise ValueError(f"{path}: (reason, scope) pair(s) listed in more than one entry: {repeated} - merge them")

    return BuildExcludedSubjectsConfig(
        project=str(raw["project"]),
        output_path=Path(raw["output_path"]),
        lesion_metadata_path=Path(raw["lesion_metadata_path"]),
        exclusions=entries,
        run_notes=str(raw["run_notes"]),
    )


def _load_entry(item: object, index: int, path: Path) -> ExclusionEntry:
    where = f"{path}: exclusions[{index}]"
    if not isinstance(item, dict):
        raise ValueError(f"{where} must be an object")
    unknown = sorted(set(item) - _ENTRY_KEYS)
    if unknown:
        raise ValueError(f"{where} has unknown key(s) {unknown}; known: {sorted(_ENTRY_KEYS)}")
    for key in ("reason", "scope", "subjects"):
        if key not in item:
            raise ValueError(f"{where} is missing required key {key!r}")

    if item["reason"] not in KNOWN_EXCLUSION_REASONS:
        raise ValueError(f"{where}: unregistered reason {item['reason']!r}; known: {list(KNOWN_EXCLUSION_REASONS)}")
    if item["scope"] not in KNOWN_EXCLUSION_SCOPES:
        raise ValueError(f"{where}: unregistered scope {item['scope']!r}; known: {list(KNOWN_EXCLUSION_SCOPES)}")

    subjects = item["subjects"]
    if not isinstance(subjects, list) or not subjects or not all(isinstance(s, str) and s for s in subjects):
        raise ValueError(f"{where}: 'subjects' must be a non-empty list of non-empty strings")
    repeated = sorted({s for s in subjects if subjects.count(s) > 1})
    if repeated:
        raise ValueError(f"{where}: duplicate subject(s) {repeated}")

    has_column, has_value = "value_column" in item, "value" in item
    if has_column == has_value:
        raise ValueError(f"{where}: give exactly one of 'value_column' (a lesion_metadata.csv column) and 'value' (a constant)")
    if has_column and (not isinstance(item["value_column"], str) or not item["value_column"]):
        raise ValueError(f"{where}: 'value_column' must be a non-empty string")
    if has_value and (isinstance(item["value"], bool) or not isinstance(item["value"], (int, float))):
        raise ValueError(f"{where}: 'value' must be a number, got {item['value']!r}")

    return ExclusionEntry(
        reason=item["reason"], scope=item["scope"], subjects=list(subjects),
        value_column=item.get("value_column"), value=item.get("value"),
    )


# --- building the table ---------------------------------------------------------------------


def read_lesion_metadata(path: Path) -> pd.DataFrame:
    """assets/metadata/lesion_metadata.csv, indexed by subject_id (str, never re-typed)."""
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found - it is written by src.pipeline.compute_lesion_metadata; run that first"
        )
    measured = pd.read_csv(path, dtype={"subject_id": str})
    if "subject_id" not in measured.columns:
        raise ValueError(f"{path}: missing required column 'subject_id'")
    duplicated = sorted(measured.loc[measured["subject_id"].duplicated(), "subject_id"])
    if duplicated:
        raise ValueError(f"{path}: duplicate subject_id row(s): {duplicated}")
    return measured.set_index("subject_id")


def build_table(
    config: BuildExcludedSubjectsConfig, lesion_metadata: pd.DataFrame, registry: pd.DataFrame
) -> pd.DataFrame:
    """One row per (subject, entry), in config order. `dataset` comes from the registry, `value`
    from the entry; a subject the registry or lesion_metadata.csv does not know raises."""
    datasets = registry.set_index("subject_id")["dataset"]
    rows: list[dict[str, object]] = []
    for entry in config.exclusions:
        unknown = [s for s in entry.subjects if s not in datasets.index]
        if unknown:
            raise ValueError(
                f"{entry.reason}/{entry.scope}: {len(unknown)} subject(s) not in the registry: {unknown[:5]} - "
                "a typo'd id would otherwise exclude nobody, silently"
            )
        values = _entry_values(entry, lesion_metadata)
        if entry.reason == _EMPTY_MASK_REASON:
            not_empty = {s: v for s, v in values.items() if v != 0}
            if not_empty:
                raise ValueError(
                    f"{entry.reason}/{entry.scope}: subject(s) listed as an empty mask but with value != 0 "
                    f"({entry.value_column or 'constant'}): {dict(list(not_empty.items())[:5])}"
                )
        rows += [
            {"subject_id": s, "dataset": datasets[s], "reason": entry.reason, "scope": entry.scope,
             "value": _format_value(values[s])}
            for s in entry.subjects
        ]
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def _entry_values(entry: ExclusionEntry, lesion_metadata: pd.DataFrame) -> dict[str, float]:
    if entry.value_column is None:
        return {s: float(entry.value) for s in entry.subjects}
    if entry.value_column not in lesion_metadata.columns:
        raise ValueError(
            f"{entry.reason}/{entry.scope}: value_column {entry.value_column!r} is not in lesion_metadata.csv; "
            f"it has {list(lesion_metadata.columns)}"
        )
    absent = [s for s in entry.subjects if s not in lesion_metadata.index]
    if absent:
        raise ValueError(
            f"{entry.reason}/{entry.scope}: {len(absent)} subject(s) have no row in lesion_metadata.csv "
            f"(so no {entry.value_column!r}): {absent[:5]}"
        )
    values = lesion_metadata.loc[entry.subjects, entry.value_column]
    missing = sorted(values.index[values.isna()])
    if missing:
        raise ValueError(f"{entry.reason}/{entry.scope}: {entry.value_column!r} is empty for subject(s) {missing[:5]}")
    return {s: float(v) for s, v in values.items()}


def _format_value(value: float) -> str:
    """A count stays an integer ("0", not "0.0"); a fraction keeps every digit."""
    return str(int(value)) if float(value).is_integer() else repr(float(value))


# --- writing --------------------------------------------------------------------------------


def validate_and_write(table: pd.DataFrame, output_path: Path, dry_run: bool) -> None:
    """Check `table` with the validator the matrix pipelines use, on a temporary file next to
    the real one; only then, and only when not dry_run, atomically replace the real file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_path.name}_tmp_", dir=output_path.parent)
    os.close(fd)
    try:
        table.to_csv(tmp_name, index=False)
        load_excluded_subjects(Path(tmp_name), "lesion")
        if not dry_run:
            os.replace(tmp_name, output_path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def describe_change(table: pd.DataFrame, output_path: Path) -> list[str]:
    """What this run changes in the existing CSV, as plain lines - for the log and the report."""
    if not output_path.is_file():
        return [f"{output_path} does not exist: {len(table)} new row(s)"]
    existing = pd.read_csv(output_path, dtype=str)
    if list(existing.columns) != OUTPUT_COLUMNS:
        return [
            f"{output_path} has columns {list(existing.columns)} instead of {OUTPUT_COLUMNS}: "
            f"replaced as a whole by {len(table)} row(s)"
        ]
    old = {tuple(r) for r in existing[OUTPUT_COLUMNS].itertuples(index=False)}
    new = {tuple(r) for r in table[OUTPUT_COLUMNS].itertuples(index=False)}
    lines = [f"{len(old & new)} unchanged, {len(new - old)} added, {len(old - new)} removed"]
    lines += [f"+ {','.join(row)}" for row in sorted(new - old)]
    lines += [f"- {','.join(row)}" for row in sorted(old - new)]
    return lines


# --- report ---------------------------------------------------------------------------------


def report_lines(
    config: BuildExcludedSubjectsConfig, table: pd.DataFrame, change: list[str], now: datetime
) -> list[str]:
    lines = [
        f"# build_excluded_subjects — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"file: `{config.output_path}` · rows: {len(table)} · lesion measures: `{config.lesion_metadata_path}`",
        "",
        f"notes: {config.run_notes}",
        "",
        "## Righe per motivo, scope e dataset",
        "",
    ]
    if table.empty:
        lines.append("(nessuna esclusione, deliberatamente: il file ha la sola intestazione)")
    else:
        counts = table.groupby(["reason", "scope", "dataset"]).size().rename("n_soggetti").reset_index()
        lines += ["| reason | scope | dataset | n soggetti |", "|---|---|---|---|"]
        lines += [f"| {r.reason} | {r.scope} | {r.dataset} | {r.n_soggetti} |" for r in counts.itertuples()]
    lines += ["", "## Cambiamenti rispetto al file attuale", ""] + [f"- {line}" for line in change]
    return lines


def write_report(
    config: BuildExcludedSubjectsConfig, table: pd.DataFrame, change: list[str], now: datetime
) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(report_lines(config, table, change, now)) + "\n")
    return report_path


# --- entry point ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build assets/metadata/excluded_subjects.csv from a config.")
    parser.add_argument("--config", required=True, help="Path to a build_excluded_subjects.json config")
    parser.add_argument("--dry-run", action="store_true", help="Run every check and write the report, but not the CSV")
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
            table = build_table(config, read_lesion_metadata(config.lesion_metadata_path), load_participants_registry())
            change = describe_change(table, config.output_path)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1
        for line in change:
            logging.info("%s", line)

        try:
            validate_and_write(table, config.output_path, args.dry_run)
            report_path = write_report(config, table, change, now)
        except ValueError as exc:
            logging.error("the table would not pass the matrix pipelines' validation: %s", exc)
            return 1
        except OSError as exc:
            logging.error("cannot write output: %s", exc, exc_info=True)
            return 1

        if args.dry_run:
            logging.info("dry-run - nothing written to %s, report at %s", config.output_path, report_path)
        else:
            logging.info("done - %d row(s) in %s, report written to %s", len(table), config.output_path, report_path)
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
