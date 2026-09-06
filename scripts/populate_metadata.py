"""CLI entry point: build the project's single participant table - who exists.

Answers exactly one question per subject: does this subject exist, and which
kinds of data does it have on disk. It joins each dataset's raw
participants.tsv (data/clinical_connectome/metadata_tsv/, paths declared in
config/registry/metadata_sources.json) against the subject folders actually
present under that dataset's derivatives/ tree, and writes one row per
subject to a single CSV (assets/metadata/participants.csv by default).

Deliberately knows nothing about clinical/demographic attributes (age, sex,
NIHSS, lesion_side, ...) or anything computed from imaging - those are
src.pipeline.enrich_metadata's job, writing further columns into this same
file. See docs/dev/metadata.md.

Usage:
    conda activate nemesis
    PYTHONPATH=. python scripts/populate_metadata.py --config config/pipelines/populate_metadata.json

Admission rule: a subject is written only if it appears BOTH in its dataset's
participants.tsv AND as a sub-* folder under at least one of the registered
data-type trees (manual_masks/sdc/features). Both kinds of mismatch (in the
tsv but nowhere on disk; on disk but absent from the tsv) are excluded and
listed in the report - never silently dropped.

`disease_id` is taken from the subject id itself (src.retrieval.dataset.group_of,
the same parser every other layer uses), NOT copied from the tsv: the tsv's own
value is compared against it and any disagreement is reported as a data problem
rather than picked between silently.

`overwrite` (config):
- false - only append subjects not already in the output file; every existing
  row is left byte-for-byte alone.
- true - recompute this script's own columns for every subject, and drop rows
  whose subject no longer qualifies. Columns written by enrich_metadata are
  preserved for the subjects that survive (this script never destroys another
  script's work), but a subject dropped here loses its enriched values too.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.retrieval.dataset import group_of
from src.utils.logging_setup import attach_file_handler, log_duration

# Structural, not configurable: the three data-type trees a dataset can hold under
# derivatives/<dataset>/, and the boolean column each one gets in the output.
PRESENCE_COLUMN_BY_DATA_TYPE = {
    "manual_masks": "has_lesion",
    "sdc": "has_sdc",
    "features": "has_features",
}
OWN_COLUMNS = ["subject_id", "original_id", "dataset", "disease_id", *PRESENCE_COLUMN_BY_DATA_TYPE.values()]

REPORTS_ROOT = Path("summaries") / "populate_metadata"
LOGS_ROOT = Path("logs") / "populate_metadata"
REPORT_FILENAME_PREFIX = "populate_summary"

_SUBJECT_DIR_RE = re.compile(r"^sub-[A-Za-z0-9]+$")
# A raw, non-canonical participant_id like "ST_UCL-UK_0001" (UCL-UK's shape):
# {disease}_{site, possibly hyphenated}_{numeric id}.
_RAW_PARTICIPANT_ID_RE = re.compile(r"^(?P<disease>[A-Z]+)_(?P<site>[A-Za-z-]+)_(?P<num>\d+)$")


@dataclass(frozen=True)
class DatasetSource:
    participants_tsv: Path
    derivatives_dir: Path


@dataclass(frozen=True)
class PopulateMetadataConfig:
    project: str
    sources: dict[str, DatasetSource]
    datasets: list[str]
    group_filter: list[str] | None
    output_path: Path
    overwrite: bool
    run_notes: str


@dataclass(frozen=True)
class DatasetOutcome:
    """One dataset's admitted rows plus every subject that didn't make it, and why."""

    dataset: str
    rows: pd.DataFrame
    only_in_tsv: list[str]
    only_on_disk: list[str]
    excluded_by_group: list[str]
    disease_id_mismatch: list[tuple[str, str, str]]  # subject_id, tsv value, id-derived value


# --- config ---------------------------------------------------------------------------------


def load_metadata_sources(path: Path) -> dict[str, DatasetSource]:
    """Parse the shared dataset->paths registry, validating its shape before use."""
    raw = json.loads(Path(path).read_text())
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{path}: expected a non-empty JSON object of dataset -> paths")
    sources = {}
    for dataset, entry in raw.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: {dataset!r} must map to an object, got {type(entry).__name__}")
        for key in ("participants_tsv", "derivatives_dir"):
            if not isinstance(entry.get(key), str):
                raise ValueError(f"{path}: {dataset!r} is missing a string {key!r}")
        sources[dataset] = DatasetSource(Path(entry["participants_tsv"]), Path(entry["derivatives_dir"]))
    return sources


def load_config(path: str) -> PopulateMetadataConfig:
    raw = json.loads(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(raw).__name__}")
    for key in ("project", "metadata_sources", "datasets", "output_path", "overwrite", "run_notes"):
        if key not in raw:
            raise ValueError(f"{path}: missing required key {key!r}")

    datasets = _unique_str_list(raw["datasets"], "datasets", path)
    if not datasets:
        raise ValueError(f"{path}: 'datasets' is empty - nothing to populate")
    group_filter = None if raw.get("group_filter") is None else _unique_str_list(raw["group_filter"], "group_filter", path)
    if group_filter is not None and not group_filter:
        raise ValueError(f"{path}: 'group_filter' is an empty list - use null to mean 'every group'")
    if not isinstance(raw["overwrite"], bool):
        raise ValueError(f"{path}: 'overwrite' must be a boolean")

    sources = load_metadata_sources(Path(raw["metadata_sources"]))
    unknown = [d for d in datasets if d not in sources]
    if unknown:
        raise ValueError(f"{path}: dataset(s) not in {raw['metadata_sources']}: {unknown}")

    return PopulateMetadataConfig(
        project=str(raw["project"]),
        sources=sources,
        datasets=datasets,
        group_filter=group_filter,
        output_path=Path(raw["output_path"]),
        overwrite=raw["overwrite"],
        run_notes=str(raw["run_notes"]),
    )


def _unique_str_list(value: object, field: str, path: str) -> list[str]:
    """A list of strings with no repeats - a duplicated entry is a config typo that would
    otherwise silently collapse (or double-count) instead of being flagged."""
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f"{path}: {field!r} must be a list of strings")
    duplicates = sorted({v for v in value if value.count(v) > 1})
    if duplicates:
        raise ValueError(f"{path}: {field!r} has duplicate entrie(s): {duplicates}")
    return list(value)


# --- discovery ------------------------------------------------------------------------------


def to_subject_id(participant_id: str) -> str:
    """Canonical `sub-{disease}{site}{num}` form from a raw participants.tsv
    participant_id. Most datasets already store the canonical form; UCL-UK is the
    exception ("ST_UCL-UK_0001"). Raises if neither shape matches, rather than
    silently producing an id that will never match anything on disk."""
    if participant_id.startswith("sub-"):
        return participant_id
    match = _RAW_PARTICIPANT_ID_RE.match(participant_id)
    if match is None:
        raise ValueError(
            f"participant_id {participant_id!r} matches neither the canonical 'sub-*' form "
            "nor the '{disease}_{site}_{num}' fallback pattern"
        )
    return f"sub-{match['disease']}{match['site'].replace('-', '')}{match['num']}"


def discover_subjects_on_disk(derivatives_dir: Path) -> dict[str, set[str]]:
    """{data type -> subject ids present under it}, for every registered data type.

    A data-type tree this dataset simply doesn't have (e.g. no features/ at all) is a
    legitimate per-dataset gap and yields an empty set, not an error. Non-subject files
    (README_ARCHIVE.md, .DS_Store) are ignored; a non-subject *directory* is unexpected
    structure and is logged as a warning.
    """
    by_data_type: dict[str, set[str]] = {}
    for data_type in PRESENCE_COLUMN_BY_DATA_TYPE:
        tree = derivatives_dir / data_type
        if not tree.is_dir():
            by_data_type[data_type] = set()
            continue
        subjects: set[str] = set()
        unexpected: list[str] = []
        for entry in sorted(tree.iterdir()):
            if not entry.is_dir():
                continue
            if _SUBJECT_DIR_RE.match(entry.name):
                subjects.add(entry.name)
            else:
                unexpected.append(entry.name)
        if unexpected:
            logging.warning("%s: %d non-subject director(ies) ignored: %s", tree, len(unexpected), unexpected[:5])
        by_data_type[data_type] = subjects
    return by_data_type


def load_participants_tsv(path: Path, dataset: str) -> pd.DataFrame:
    """Raw participants.tsv as strings, with a canonical `subject_id` column added and
    the source id kept in `original_id`. Raises on a missing file, a missing
    participant_id column, or duplicate subjects (a repeated subject would otherwise
    double-count silently)."""
    if not path.is_file():
        raise FileNotFoundError(f"{dataset}: participants.tsv not found at {path}")
    participants = pd.read_csv(path, sep="\t", dtype=str)
    if "participant_id" not in participants.columns:
        raise ValueError(f"{path}: expected a 'participant_id' column, got {list(participants.columns)}")

    participants = participants.copy()
    participants["original_id"] = participants["participant_id"]
    participants["subject_id"] = participants["participant_id"].map(to_subject_id)
    duplicated = sorted(participants.loc[participants["subject_id"].duplicated(), "subject_id"])
    if duplicated:
        raise ValueError(f"{path}: duplicate subject id(s) after canonicalization: {duplicated}")
    return participants


# --- per-dataset join -----------------------------------------------------------------------


def build_dataset_outcome(
    dataset: str, source: DatasetSource, group_filter: list[str] | None
) -> DatasetOutcome:
    """Inner-join one dataset's participants.tsv against its on-disk subjects, keeping
    only subjects present in both and passing group_filter."""
    participants = load_participants_tsv(source.participants_tsv, dataset)
    on_disk = discover_subjects_on_disk(source.derivatives_dir)
    disk_subjects = set().union(*on_disk.values()) if on_disk else set()
    tsv_subjects = set(participants["subject_id"])

    admitted, excluded_by_group, mismatches = [], [], []
    for _, participant in participants.loc[participants["subject_id"].isin(disk_subjects)].iterrows():
        subject_id = participant["subject_id"]
        disease_id = group_of(subject_id)
        if group_filter is not None and disease_id not in group_filter:
            excluded_by_group.append(subject_id)
            continue
        tsv_disease_id = participant.get("disease_id")
        if isinstance(tsv_disease_id, str) and tsv_disease_id.strip() and tsv_disease_id.strip() != disease_id:
            mismatches.append((subject_id, tsv_disease_id.strip(), disease_id))
        admitted.append(
            {
                "subject_id": subject_id,
                "original_id": participant["original_id"],
                "dataset": dataset,
                "disease_id": disease_id,
                **{
                    column: subject_id in on_disk[data_type]
                    for data_type, column in PRESENCE_COLUMN_BY_DATA_TYPE.items()
                },
            }
        )

    return DatasetOutcome(
        dataset=dataset,
        rows=pd.DataFrame(admitted, columns=OWN_COLUMNS),
        only_in_tsv=sorted(tsv_subjects - disk_subjects),
        only_on_disk=sorted(disk_subjects - tsv_subjects),
        excluded_by_group=sorted(excluded_by_group),
        disease_id_mismatch=sorted(mismatches),
    )


def build_table(config: PopulateMetadataConfig) -> tuple[pd.DataFrame, list[DatasetOutcome]]:
    outcomes = [build_dataset_outcome(d, config.sources[d], config.group_filter) for d in config.datasets]
    for outcome in outcomes:
        logging.info(
            "%s: admitted=%d only_in_tsv=%d only_on_disk=%d excluded_by_group=%d disease_id_mismatch=%d",
            outcome.dataset, len(outcome.rows), len(outcome.only_in_tsv), len(outcome.only_on_disk),
            len(outcome.excluded_by_group), len(outcome.disease_id_mismatch),
        )
    table = pd.concat([o.rows for o in outcomes], ignore_index=True)
    return table, outcomes


# --- merge with what's already on disk -------------------------------------------------------


def merge_with_existing(fresh: pd.DataFrame, output_path: Path, overwrite: bool) -> pd.DataFrame:
    """Combine freshly computed rows with an already-written participants file.

    overwrite=False: existing rows are returned untouched, only genuinely new subjects
    are appended (columns another script added keep their values; the new rows get empty
    cells for them).
    overwrite=True: this script's own columns are recomputed for every surviving subject,
    while any other script's columns are carried over by subject_id - a subject no longer
    admitted is dropped entirely.
    """
    if not output_path.is_file():
        return fresh
    existing = pd.read_csv(output_path, dtype=str)
    if "subject_id" not in existing.columns:
        raise ValueError(f"{output_path}: existing file has no 'subject_id' column - refusing to merge into it")

    if not overwrite:
        new_rows = fresh.loc[~fresh["subject_id"].isin(set(existing["subject_id"]))]
        logging.info("overwrite=false: %d existing row(s) untouched, %d new subject(s) appended", len(existing), len(new_rows))
        return pd.concat([existing, new_rows], ignore_index=True)

    foreign_columns = [c for c in existing.columns if c not in OWN_COLUMNS]
    merged = fresh.merge(existing[["subject_id", *foreign_columns]], on="subject_id", how="left")
    dropped = sorted(set(existing["subject_id"]) - set(fresh["subject_id"]))
    if dropped:
        logging.warning("overwrite=true: %d subject(s) no longer admitted, dropped: %s", len(dropped), dropped[:5])
    logging.info("overwrite=true: rebuilt %d row(s), carried over column(s) %s", len(merged), foreign_columns)
    return merged


def write_table(table: pd.DataFrame, output_path: Path) -> None:
    """Atomic write (temp file + os.replace) - a crash never leaves a half-written
    participants file, which every downstream consumer treats as the source of truth."""
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


def report_lines(config: PopulateMetadataConfig, outcomes: list[DatasetOutcome], n_written: int, now: datetime) -> list[str]:
    lines = [
        f"# populate_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"output: `{config.output_path}` ({n_written} rows) · overwrite: {config.overwrite} · "
        f"group_filter: {config.group_filter}",
        f"notes: {config.run_notes}",
        "",
        "| dataset | admitted | only in tsv | only on disk | excluded by group | disease_id mismatch |",
        "|---|---|---|---|---|---|",
    ]
    for outcome in outcomes:
        lines.append(
            f"| {outcome.dataset} | {len(outcome.rows)} | {len(outcome.only_in_tsv)} | {len(outcome.only_on_disk)} | "
            f"{len(outcome.excluded_by_group)} | {len(outcome.disease_id_mismatch)} |"
        )
    lines += _anomaly_sections(outcomes)
    return lines


def _anomaly_sections(outcomes: list[DatasetOutcome]) -> list[str]:
    """One section per anomaly kind, listing the subjects behind the counts above -
    omitted entirely when there's nothing to report."""
    sections = {
        "Only in participants.tsv (no data on disk - excluded)": {o.dataset: o.only_in_tsv for o in outcomes},
        "Only on disk (absent from participants.tsv - excluded)": {o.dataset: o.only_on_disk for o in outcomes},
        "Excluded by group_filter": {o.dataset: o.excluded_by_group for o in outcomes},
    }
    lines: list[str] = []
    for title, by_dataset in sections.items():
        entries = {d: subjects for d, subjects in by_dataset.items() if subjects}
        if not entries:
            continue
        lines += ["", f"## {title}", ""]
        for dataset, subjects in entries.items():
            lines.append(f"- **{dataset}** ({len(subjects)}): {', '.join(subjects)}")

    mismatches = {o.dataset: o.disease_id_mismatch for o in outcomes if o.disease_id_mismatch}
    if mismatches:
        lines += ["", "## disease_id mismatch (participants.tsv vs. subject id)", ""]
        for dataset, rows in mismatches.items():
            for subject_id, tsv_value, parsed in rows:
                lines.append(f"- **{dataset}** {subject_id}: tsv says {tsv_value!r}, subject id says {parsed!r}")
    return lines


def write_report(config: PopulateMetadataConfig, outcomes: list[DatasetOutcome], n_written: int, now: datetime) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(report_lines(config, outcomes, n_written, now)) + "\n")
    return report_path


# --- entry point ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the project's single participant table (who exists).")
    parser.add_argument("--config", required=True, help="Path to a populate_metadata.json config")
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
            fresh, outcomes = build_table(config)
            table = merge_with_existing(fresh, config.output_path, config.overwrite)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        try:
            write_table(table, config.output_path)
            report_path = write_report(config, outcomes, len(table), now)
        except OSError as exc:
            logging.error("cannot write output: %s", exc, exc_info=True)
            return 1

        logging.info("done - %d subject(s) in %s, report written to %s", len(table), config.output_path, report_path)
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
