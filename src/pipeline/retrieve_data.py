"""CLI entry point: retrieve lesion/feature data and metadata into the local workspace.

Usage:
    python -m src.pipeline.retrieve_data --config config/retrieval.json

Structural problems (unsupported object/space/modality, unknown group,
unreachable dataset root, unknown explicit subject) are validated upfront
across ALL requested datasets before anything is copied - a bad request
never leaves partial output behind. Per-subject/per-file issues (a file
missing for one subject, a copy that fails for one subject) are logged and
do not stop the run; a summary report is written at the end either way.
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
    """One Failed/Missing line, tagged with which (object, space, modality)
    it belongs to - lets the report sub-group entries by that instead of
    dumping every retrieve item's issues into one flat per-dataset list.
    `group` is "" for entries not tied to one specific retrieve item (e.g.
    an explicitly requested subject absent from this dataset entirely, or a
    failed participants.tsv copy)."""

    group: str
    line: str


@dataclass
class DatasetStats:
    subjects_selected: int = 0
    copied: int = 0
    skipped_existing: int = 0
    failed: list[ReportEntry] = field(default_factory=list)
    missing: list[ReportEntry] = field(default_factory=list)
    non_conforming: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    missing_locally: list[str] = field(default_factory=list)
    unexpected_local_files: list[str] = field(default_factory=list)


def _build_datasets(config: RetrievalConfig) -> dict[str, Dataset]:
    """Instantiate a Dataset per requested name. Construction itself touches
    no filesystem (see Dataset) - a missing dataset root still surfaces
    immediately in practice, since _validate_upfront always runs right after
    this, before any copying."""
    return {name: Dataset(name, config.file_patterns) for name in config.datasets}


def _known_object_spaces(config: RetrievalConfig) -> set[tuple[str, str]]:
    """Every (object, space) the file_patterns registry knows about, for any
    object this run's `retrieve` list touches - broader than the exact
    (object, space) pairs named in `retrieve` itself. A subject known via one
    space (e.g. native) must stay discoverable even when this run only
    requests a *different* space of the same object (e.g. mni) - otherwise
    they'd be invisible to the whole run instead of correctly showing up as
    a per-item "File not found" entry (see _missing_message)."""
    requested_objects = {item.object for item in config.retrieve}
    return {(o, s) for o, s in config.file_patterns.all_object_spaces() if o in requested_objects}


def _discover_subjects(ds: Dataset, config: RetrievalConfig, group: str | None = None) -> set[str]:
    """Union of subjects visible in any space of any object this run
    touches, for this dataset (see _known_object_spaces)."""
    return {
        subject_id
        for object_, space in _known_object_spaces(config)
        for subject_id in ds.subjects(object_, space, group=group)
    }


def _validate_upfront(datasets: dict[str, Dataset], config: RetrievalConfig) -> None:
    """Raise ValueError if the request is structurally impossible for any
    requested dataset. Runs for ALL datasets before any file is copied."""
    for name, ds in datasets.items():
        if config.subjects is None:
            _validate_group_filter(name, ds, config)
        _validate_retrieve_items(name, ds, config)
    if config.subjects is not None:
        _validate_explicit_subjects(datasets, config)


def _validate_group_filter(name: str, ds: Dataset, config: RetrievalConfig) -> None:
    if config.group_filter is None:
        return
    for group in config.group_filter:
        if not _discover_subjects(ds, config, group=group):
            raise ValueError(f"{name}: group_filter {group!r} matches 0 subjects")


def _validate_retrieve_items(name: str, ds: Dataset, config: RetrievalConfig) -> None:
    for item in config.retrieve:
        if not ds.available(item.object, item.space, item.modality):
            raise ValueError(
                f"{name}: no file registered/found for object={item.object!r} "
                f"space={item.space!r} modality={item.modality!r}"
            )


def _validate_explicit_subjects(datasets: dict[str, Dataset], config: RetrievalConfig) -> None:
    assert config.subjects is not None
    known = {s for ds in datasets.values() for s in _discover_subjects(ds, config)}
    unknown = [s for s in config.subjects if s not in known]
    if unknown:
        raise ValueError(f"subjects not found in any requested dataset: {unknown}")


def _select_subjects(ds: Dataset, config: RetrievalConfig) -> list[str]:
    if config.subjects is not None:
        wanted = set(config.subjects)
        return sorted(_discover_subjects(ds, config) & wanted)
    if config.group_filter is None:
        return sorted(_discover_subjects(ds, config))
    selected = {s for group in config.group_filter for s in _discover_subjects(ds, config, group=group)}
    return sorted(selected)


def _destination_path(
    config: RetrievalConfig, dataset_name: str, subject_id: str, object_: str, space: str, source: Path
) -> Path:
    return config.output_root / config.project / dataset_name / subject_id / object_ / space / source.name


def _copy_one(
    source: Path, destination: Path, overwrite: bool, stats: DatasetStats, label: str, group: str = ""
) -> None:
    """`label` identifies the file for the Failed-section entry - e.g.
    "<dataset>: <subject_id> - <object>/<space>/<modality>" for a lesion
    file, or "<dataset>: participants.tsv". `group` is the
    (object, space, modality) tag used to sub-group Failed like Missing (see
    ReportEntry) - "" for files not tied to one specific retrieve item (e.g.
    participants.tsv)."""
    if destination.exists() and not overwrite:
        logging.info("skip (exists): %s", destination)
        stats.skipped_existing += 1
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        logging.warning("copy failed: %s -> %s (%s)", source, destination, exc, exc_info=True)
        stats.failed.append(ReportEntry(group=group, line=f"{label}: copy failed ({exc})"))
        return
    logging.info("copied: %s", destination)
    stats.copied += 1


def _missing_message(ds: Dataset, name: str, subject_id: str, item: RetrieveItem) -> ReportEntry:
    """File-not-found entry for the report, tagged with the
    (object, space, modality) that produced it (see ReportEntry) so multiple
    retrieve items don't get interleaved into one flat list per dataset.
    Distinguishes *why* nothing matched - "empty folder" (the directory that
    would hold the file exists but has nothing in it - the file was simply
    never produced for this subject) vs "not found" (every other case) - see
    Dataset.describe_absence. Whether this subject has data in some *other*
    object/space/modality is a separate question, answered by the
    data_summary report (src.retrieval.matrix), not here."""
    reason = ds.describe_absence(subject_id, item)
    group = f"{item.object}/{item.space}/{item.modality}"
    return ReportEntry(group=group, line=f"{name}: {subject_id} - no {group} ({reason})")


def _retrieve_subject(
    name: str, ds: Dataset, subject_id: str, config: RetrievalConfig, stats: DatasetStats
) -> None:
    for item in config.retrieve:
        resolved = ds.resolve(subject_id, item)
        if not resolved:
            stats.missing.append(_missing_message(ds, name, subject_id, item))
            continue
        group = f"{item.object}/{item.space}/{item.modality}"
        label = f"{name}: {subject_id} - {group}"
        for source in resolved:
            destination = _destination_path(config, name, subject_id, item.object, item.space, source)
            _copy_one(source, destination, config.overwrite, stats, label, group=group)


def _retrieve_participants(name: str, ds: Dataset, config: RetrievalConfig, stats: DatasetStats) -> None:
    """Copies participants.tsv through the same _copy_one path as any other
    file - its outcome folds into the same copied/skipped/failed counts
    already in the summary table, rather than a separate status field only
    this one file had. Absence at source (e.g. WashU has none) is a
    legitimate per-dataset fact, not tracked here - see the data_summary
    report (src.retrieval.matrix) for what each dataset does/doesn't have."""
    source = ds.participants_tsv_path()
    if source is None:
        return
    destination = config.output_root / config.project / name / "participants.tsv"
    _copy_one(source, destination, config.overwrite, stats, f"{name}: participants.tsv")


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


def _report_non_conforming_subject_folders(
    name: str, ds: Dataset, config: RetrievalConfig, stats: DatasetStats
) -> None:
    """sub-* folders that don't match the expected naming convention are
    never retrieved (Dataset.subjects() already excludes them) - this makes
    their exclusion visible instead of silent. Checked across every
    (object, space) this run actually requests, since non-conforming folders
    can exist under any of their independent subject containers."""
    found: set[str] = set()
    for object_, space in _known_object_spaces(config):
        found |= set(ds.non_conforming_subject_folders(object_, space))
    stats.non_conforming = [
        f"{name}: {folder} - does not match expected subject naming, excluded from retrieval"
        for folder in sorted(found)
    ]
    if stats.non_conforming:
        logging.warning("%s: %d non-conforming subject folder(s) excluded", name, len(stats.non_conforming))


def _retrieve_dataset(name: str, ds: Dataset, config: RetrievalConfig, stats: DatasetStats) -> None:
    subjects = _select_subjects(ds, config)
    stats.subjects_selected = len(subjects)
    _report_non_conforming_subject_folders(name, ds, config, stats)
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
        "file_patterns": str(config.file_patterns_path),
        "datasets": config.datasets,
        "group_filter": config.group_filter,
        "subjects": config.subjects,
        "retrieve": [
            {"object": item.object, "space": item.space, "modality": item.modality} for item in config.retrieve
        ],
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
    """Rendering for Failed/Missing: same per-dataset grouping as
    _grouped_section, but each dataset's entries (list[ReportEntry]) are
    further sub-grouped by which (object, space, modality) produced them,
    each with its own sub-heading and count - a run requesting several
    modalities in `retrieve` would otherwise interleave them into one flat,
    hard-to-scan list per dataset. Entries with group="" (not tied to one
    retrieve item, e.g. an explicitly requested subject absent from this
    dataset) get no sub-heading, listed first."""
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
        "| dataset | copied | skipped (exists) | failed |",
        "|---|---|---|---|",
    ]
    for name, s in stats.items():
        lines.append(f"| {name} | {s.copied} | {s.skipped_existing} | {len(s.failed)} |")
    lines += _grouped_by_modality_section(
        stats,
        "failed",
        "Failed",
        "A file's copy did not complete correctly, for the reason given. Sub-grouped by "
        "which object/space/modality was requested.",
        "Failed Count",
    )
    lines += _grouped_by_modality_section(
        stats,
        "missing",
        "File not found",
        "No registered file found for a specific subject (or an explicitly requested "
        "subject not present in this dataset). \"empty folder\" means the directory that "
        "would hold the file exists but is empty; \"not found\" covers every other case. "
        "Sub-grouped by which object/space/modality was requested.",
        "File Not Found Count",
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
        description="Retrieve lesion/feature data and metadata into the local workspace."
    )
    parser.add_argument("--config", required=True, help="Path to a retrieval.json file")
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
