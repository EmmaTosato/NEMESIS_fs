"""CLI entry point: retrieve lesion data and metadata into the local workspace.

Usage:
    python -m src.pipeline.retrieve_data --config config/data_retrieval.json

Structural problems (unsupported modality/space, unknown group, unreachable
dataset root, unknown explicit subject) are validated upfront across ALL
requested datasets before anything is copied - a bad request never leaves
partial output behind. Per-subject/per-file issues (a file missing for one
subject, a copy that fails for one subject) are logged and do not stop the
run; a summary report is written at the end either way.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.retrieval import verify
from src.retrieval.config import RetrievalConfig, RetrieveItem, load_config
from src.retrieval.dataset import Dataset

REPORTS_ROOT = Path("reports") / "data_retrieval"
LOGS_ROOT = Path("logs") / "data_retrieval"
REPORT_FILENAME_PREFIX = "copy_summary"


@dataclass(frozen=True)
class ReportEntry:
    """One Missing/Ambiguous line, tagged with which (space, modality) it
    belongs to - lets the report sub-group entries by that instead of
    dumping every retrieve item's misses into one flat per-dataset list.
    `group` is "" for entries not tied to one specific retrieve item (e.g.
    an explicitly requested subject absent from this dataset entirely)."""

    group: str
    line: str


@dataclass
class DatasetStats:
    subjects_selected: int = 0
    copied: int = 0
    skipped_existing: int = 0
    failed: int = 0
    missing: list[ReportEntry] = field(default_factory=list)
    ambiguous: list[ReportEntry] = field(default_factory=list)
    non_conforming: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    missing_locally: list[str] = field(default_factory=list)
    unexpected_local_files: list[str] = field(default_factory=list)


def _build_datasets(config: RetrievalConfig) -> dict[str, Dataset]:
    """Instantiate a Dataset per requested name. Raises FileNotFoundError
    immediately if any dataset root is unreachable - before any copying."""
    return {name: Dataset(config.project_root, name, config.file_patterns) for name in config.datasets}


def _validate_upfront(datasets: dict[str, Dataset], config: RetrievalConfig) -> None:
    """Raise ValueError if the request is structurally impossible for any
    requested dataset. Runs for ALL datasets before any file is copied."""
    for name, ds in datasets.items():
        if config.subjects is None:
            _validate_group_filter(name, ds, config)
        _validate_retrieve_items(name, ds, config)
    if config.subjects is not None:
        _validate_explicit_subjects(datasets, config.subjects)


def _validate_group_filter(name: str, ds: Dataset, config: RetrievalConfig) -> None:
    if config.group_filter is None:
        return
    for group in config.group_filter:
        if not ds.subjects(group=group):
            raise ValueError(f"{name}: group_filter {group!r} matches 0 subjects")


def _validate_retrieve_items(name: str, ds: Dataset, config: RetrievalConfig) -> None:
    for item in config.retrieve:
        if not ds.available(item.space, item.modality):
            raise ValueError(
                f"{name}: no file registered/found for space={item.space!r} modality={item.modality!r}"
            )


def _validate_explicit_subjects(datasets: dict[str, Dataset], subjects: list[str]) -> None:
    known = {s for ds in datasets.values() for s in ds.subjects()}
    unknown = [s for s in subjects if s not in known]
    if unknown:
        raise ValueError(f"subjects not found in any requested dataset: {unknown}")


def _select_subjects(ds: Dataset, config: RetrievalConfig) -> list[str]:
    if config.subjects is not None:
        wanted = set(config.subjects)
        return [s for s in ds.subjects() if s in wanted]
    if config.group_filter is None:
        return ds.subjects()
    selected = {s for group in config.group_filter for s in ds.subjects(group=group)}
    return sorted(selected)


def _destination_path(
    config: RetrievalConfig, dataset_name: str, subject_id: str, space: str, source: Path
) -> Path:
    return config.output_root / config.project / dataset_name / subject_id / "lesion" / space / source.name


def _copy_one(source: Path, destination: Path, overwrite: bool, stats: DatasetStats) -> None:
    if destination.exists() and not overwrite:
        logging.info("skip (exists): %s", destination)
        stats.skipped_existing += 1
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        logging.warning("copy failed: %s -> %s (%s)", source, destination, exc, exc_info=True)
        stats.failed += 1
        return
    logging.info("copied: %s", destination)
    stats.copied += 1


def _missing_message(name: str, subject_id: str, item: RetrieveItem) -> ReportEntry:
    """Missing-file entry for the report, tagged with the (space, modality)
    that produced it (see ReportEntry) so multiple retrieve items don't get
    interleaved into one flat list per dataset. Whether this subject has
    data in some other space/modality is a separate question, answered by
    the full per-subject matrix report (src.retrieval.matrix), not by this
    pipeline - this line only states what THIS run looked for and didn't
    find."""
    return ReportEntry(
        group=f"{item.space}/{item.modality}", line=f"{name}: {subject_id} - no {item.space}/{item.modality}"
    )


def _retrieve_subject(
    name: str, ds: Dataset, subject_id: str, config: RetrievalConfig, stats: DatasetStats
) -> None:
    for item in config.retrieve:
        resolved = ds.resolve(subject_id, item.space, item.modality)
        if resolved is None:
            stats.missing.append(_missing_message(name, subject_id, item))
            continue
        if resolved.extra_matches:
            extra_names = ", ".join(m.name for m in resolved.extra_matches)
            stats.ambiguous.append(
                ReportEntry(
                    group=f"{item.space}/{item.modality}",
                    line=f"{name}: {subject_id} - {item.space}/{item.modality}: using "
                    f"{resolved.path.name}, also matched {extra_names}",
                )
            )
            logging.warning(
                "ambiguous match for %s %s/%s: using %s, also matched %s",
                subject_id,
                item.space,
                item.modality,
                resolved.path.name,
                extra_names,
            )
        destination = _destination_path(config, name, subject_id, item.space, resolved.path)
        _copy_one(resolved.path, destination, config.overwrite, stats)


def _retrieve_participants(name: str, ds: Dataset, config: RetrievalConfig, stats: DatasetStats) -> None:
    """Copies participants.tsv through the same _copy_one path as any other
    file - its outcome folds into the same copied/skipped/failed counts
    already in the summary table, rather than a separate status field only
    this one file had. Absence at source (e.g. WashU has none) is a
    legitimate per-dataset fact, not tracked here - see the dataset matrix
    report (src.retrieval.matrix) for what each dataset does/doesn't have."""
    source = ds.participants_tsv_path()
    if source is None:
        return
    destination = config.output_root / config.project / name / "participants.tsv"
    _copy_one(source, destination, config.overwrite, stats)


def _report_explicit_subjects_absent_from_dataset(
    name: str, config: RetrievalConfig, subjects: list[str], stats: DatasetStats
) -> None:
    """When subjects is set, config.subjects may name people that live in a
    different one of the requested datasets, not this one - _validate_explicit_subjects
    only checks presence in ANY requested dataset. Report that per dataset
    instead of leaving it silent, so a typo'd dataset selection is visible
    even though the run as a whole is valid."""
    if config.subjects is None:
        return
    present = set(subjects)
    absent = dict.fromkeys(s for s in config.subjects if s not in present)  # dedup, keep order
    stats.missing += [
        ReportEntry(group="", line=f"{name}: {s} - not present in this dataset") for s in absent
    ]


def _report_non_conforming_subject_folders(name: str, ds: Dataset, stats: DatasetStats) -> None:
    """sub-* folders that don't match the expected naming convention are
    never retrieved (Dataset.subjects() already excludes them) - this makes
    their exclusion visible instead of silent, regardless of whether the
    request used group_filter or not (see docs/dev/retrieval.md for the
    inconsistency this replaces)."""
    stats.non_conforming = [
        f"{name}: {folder} - does not match expected subject naming, excluded from retrieval"
        for folder in ds.non_conforming_subject_folders()
    ]
    if stats.non_conforming:
        logging.warning("%s: %d non-conforming subject folder(s) excluded", name, len(stats.non_conforming))


def _retrieve_dataset(name: str, ds: Dataset, config: RetrievalConfig, stats: DatasetStats) -> None:
    subjects = _select_subjects(ds, config)
    stats.subjects_selected = len(subjects)
    _report_non_conforming_subject_folders(name, ds, stats)
    _report_explicit_subjects_absent_from_dataset(name, config, subjects, stats)
    logging.info("%s: retrieving %d subjects", name, len(subjects))
    for subject_id in subjects:
        _retrieve_subject(name, ds, subject_id, config, stats)
    if config.include_tabular_data:
        _retrieve_participants(name, ds, config, stats)


def _verify_dataset_copies(name: str, ds: Dataset, config: RetrievalConfig, stats: DatasetStats) -> None:
    """Re-derives what data/ should contain for this dataset (same subject
    selection the copy phase used) and compares it against the current source
    byte-for-byte - catches both a corrupted write and a local file that was
    correct when copied but no longer matches because the source changed
    since (see src.retrieval.verify). Runs from _retrieve_all only after
    EVERY requested dataset has finished copying, never interleaved with the
    copy phase of any dataset."""
    subjects = _select_subjects(ds, config)
    result = verify.verify_dataset(name, ds, subjects, config)
    stats.mismatched = result.mismatched
    stats.missing_locally = result.missing_locally
    stats.unexpected_local_files = result.unexpected_local_files
    for message in result.mismatched:
        logging.error("checksum mismatch: %s", message)
    for message in result.missing_locally:
        logging.error("not copied despite source having it: %s", message)
    for message in result.unexpected_local_files:
        logging.warning("unexpected local file: %s", message)


def _retrieve_all(datasets: dict[str, Dataset], config: RetrievalConfig) -> dict[str, DatasetStats]:
    stats = {name: DatasetStats() for name in datasets}
    for name, ds in datasets.items():
        _retrieve_dataset(name, ds, config, stats[name])
    for name, ds in datasets.items():
        _verify_dataset_copies(name, ds, config, stats[name])
    return stats


def _config_summary(config: RetrievalConfig) -> str:
    """JSON dump of the fields actually used from the config file - derived
    from the parsed RetrievalConfig (not a re-read of the file) so it can
    never drift from what the run actually used."""
    payload = {
        "output_root": str(config.output_root),
        "project": config.project,
        "project_root": str(config.project_root),
        "file_patterns": str(config.file_patterns_path),
        "datasets": config.datasets,
        "group_filter": config.group_filter,
        "subjects": config.subjects,
        "retrieve": [{"space": item.space, "modality": item.modality} for item in config.retrieve],
        "include_tabular_data": config.include_tabular_data,
        "overwrite": config.overwrite,
    }
    return json.dumps(payload, indent=2)


def _section_header(title: str, subtitle: str) -> list[str]:
    """Title as a heading, explanation as a separate italic subtitle line
    below it - kept apart so the heading itself stays scannable instead of
    one long run-on line mixing the section name and its explanation."""
    return ["", f"## {title}", f"*{subtitle}*", ""]


def _grouped_section(
    stats: dict[str, DatasetStats], attr: str, title: str, subtitle: str, count_label: str
) -> list[str]:
    """Shared rendering for report sections holding a flat list[str] per
    dataset (Non-conforming, Mismatched, Not-copied, Unexpected): grouped per
    dataset, a count per group, a '---' separator between groups, and 'none'
    when nothing in any dataset has an entry."""
    lines = _section_header(title, subtitle)
    groups = [(name, getattr(s, attr)) for name, s in stats.items() if getattr(s, attr)]
    if not groups:
        lines.append("- none")
    for i, (_name, entries) in enumerate(groups):
        if i > 0:
            lines += ["---", ""]
        lines += [f"- {line}" for line in entries]
        lines += ["", f"{count_label} = {len(entries)}", ""]
    return lines


def _grouped_by_modality_section(
    stats: dict[str, DatasetStats], attr: str, title: str, subtitle: str, count_label: str
) -> list[str]:
    """Rendering for Missing/Ambiguous: same per-dataset grouping as
    _grouped_section, but each dataset's entries (list[ReportEntry]) are
    further sub-grouped by which (space, modality) produced them, each with
    its own sub-heading and count - a run requesting several modalities in
    `retrieve` would otherwise interleave them into one flat, hard-to-scan
    list per dataset. Entries with group="" (not tied to one retrieve item,
    e.g. an explicitly requested subject absent from this dataset) get no
    sub-heading, listed first."""
    lines = _section_header(title, subtitle)
    groups = [(name, getattr(s, attr)) for name, s in stats.items() if getattr(s, attr)]
    if not groups:
        lines.append("- none")
    for i, (_name, entries) in enumerate(groups):
        if i > 0:
            lines += ["---", ""]
        by_modality: dict[str, list[str]] = {}
        for entry in entries:
            by_modality.setdefault(entry.group, []).append(entry.line)
        for j, (modality_key, modality_lines) in enumerate(by_modality.items()):
            if j > 0:
                lines.append("")
            if modality_key:
                lines.append(f"**{modality_key}** ({len(modality_lines)})")
            lines += [f"- {line}" for line in modality_lines]
        lines += ["", f"{count_label} = {len(entries)}", ""]
    return lines


def _build_report(config: RetrievalConfig, stats: dict[str, DatasetStats], now: datetime) -> str:
    lines = [
        f"# {config.project}_{now.strftime('%d-%m-%y')}",
        f"## {now.strftime('%H:%M')}",
        "",
        "## Config",
        "",
        "```json",
        _config_summary(config),
        "```",
        "",
        "## Summary",
        "",
        "| dataset | subjects | copied | skipped (exists) | failed |",
        "|---|---|---|---|---|",
    ]
    for name, s in stats.items():
        lines.append(
            f"| {name} | {s.subjects_selected} | {s.copied} | {s.skipped_existing} | {s.failed} |"
        )
    lines += _grouped_by_modality_section(
        stats,
        "missing",
        "Missing",
        "File not found for a specific subject, or an explicitly requested subject not "
        "present in this dataset. Sub-grouped by which space/modality was requested.",
        "Missing Count",
    )
    lines += _grouped_by_modality_section(
        stats,
        "ambiguous",
        "Ambiguous",
        "More than one registered file matched for a subject - the highest-priority one "
        "was used. Sub-grouped by which space/modality was requested.",
        "Ambiguous Count",
    )
    lines += _grouped_section(
        stats,
        "non_conforming",
        "Non-conforming subject folders",
        "Folders found on disk that don't match the expected subject naming convention - "
        "excluded from retrieval.",
        "Non-conforming Count",
    )
    lines += _grouped_section(
        stats,
        "mismatched",
        "Mismatched",
        "A local file's checksum differs from its current source - possible corruption, "
        "or the source changed after this file was copied.",
        "Mismatched Count",
    )
    lines += _grouped_section(
        stats,
        "missing_locally",
        "Not copied despite source having it",
        "Verification found the source file, but data/ doesn't have it - a copy that "
        "silently failed to land.",
        "Not Copied Count",
    )
    lines += _grouped_section(
        stats,
        "unexpected_local_files",
        "Unexpected local files",
        "Present in data/ but not the current resolution for any expected subject/modality "
        "- stale naming or a leftover from a prior run.",
        "Unexpected Count",
    )
    return "\n".join(lines)


def _write_report(config: RetrievalConfig, stats: dict[str, DatasetStats], now: datetime | None = None) -> Path:
    now = now or datetime.now()
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, stats, now))
    return report_path


def _log_path(config: RetrievalConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


def _attach_file_handler(log_path: Path) -> None:
    """Persist the same narrative already printed to console into a log file.
    Attached only once the config's project is known, so a config-load
    failure (no project name yet) never blocks producing an error message.

    Removes any FileHandler left over from a previous main() call in the same
    process (e.g. repeated invocations in a notebook) - otherwise log lines
    from a later run would keep being written into an earlier run's file."""
    root_logger = logging.getLogger()
    for old_handler in [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]:
        root_logger.removeHandler(old_handler)
        old_handler.close()
    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root_logger.addHandler(handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Retrieve lesion data and metadata into the local workspace."
    )
    parser.add_argument("--config", required=True, help="Path to a data_retrieval.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # basicConfig() is a no-op if the root logger already has a handler (e.g. under
    # pytest, or a second call in the same interpreter) - set the level explicitly
    # so INFO records still reach our FileHandler even when that happens.
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    log_path = _log_path(config, now)
    _attach_file_handler(log_path)

    try:
        datasets = _build_datasets(config)
        _validate_upfront(datasets, config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    stats = _retrieve_all(datasets, config)
    report_path = _write_report(config, stats, now)

    total_verification_errors = sum(
        len(s.mismatched) + len(s.missing_locally) for s in stats.values()
    )
    if total_verification_errors:
        logging.error(
            "post-copy verification found %d problem(s) against source - see report: %s",
            total_verification_errors,
            report_path,
        )
    logging.info("done - report written to %s, log written to %s", report_path, log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
