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

from src.retrieval.config import RetrievalConfig, load_config
from src.retrieval.dataset import Dataset

REPORTS_ROOT = Path("reports") / "data_retrieval"
LOGS_ROOT = Path("logs") / "data_retrieval"


@dataclass
class DatasetStats:
    subjects_selected: int = 0
    copied: int = 0
    skipped_existing: int = 0
    failed: int = 0
    missing: list[str] = field(default_factory=list)
    ambiguous: list[str] = field(default_factory=list)
    non_conforming: list[str] = field(default_factory=list)
    participants_status: str = "not requested"


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


def _retrieve_subject(
    name: str, ds: Dataset, subject_id: str, config: RetrievalConfig, stats: DatasetStats
) -> None:
    for item in config.retrieve:
        resolved = ds.resolve(subject_id, item.space, item.modality)
        if resolved is None:
            stats.missing.append(f"{name}: {subject_id} - no {item.space}/{item.modality}")
            continue
        if resolved.extra_matches:
            extra_names = ", ".join(m.name for m in resolved.extra_matches)
            stats.ambiguous.append(
                f"{name}: {subject_id} - {item.space}/{item.modality}: using "
                f"{resolved.path.name}, also matched {extra_names}"
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
    source = ds.participants_tsv_path()
    if source is None:
        stats.participants_status = "absent at source"
        return
    destination = config.output_root / config.project / name / "participants.tsv"
    if destination.exists() and not config.overwrite:
        stats.participants_status = "skipped (exists)"
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        logging.warning("copy failed: %s -> %s (%s)", source, destination, exc, exc_info=True)
        stats.participants_status = "failed"
        return
    stats.participants_status = "copied"


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
    stats.missing += [f"{name}: {s} - not present in this dataset" for s in absent]


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


def _retrieve_all(datasets: dict[str, Dataset], config: RetrievalConfig) -> dict[str, DatasetStats]:
    stats = {name: DatasetStats() for name in datasets}
    for name, ds in datasets.items():
        _retrieve_dataset(name, ds, config, stats[name])
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


def _grouped_section(stats: dict[str, DatasetStats], attr: str, header: str, count_label: str) -> list[str]:
    """Shared rendering for the Missing/Ambiguous/Non-conforming report
    sections: grouped per dataset, a count per group, a '---' separator
    between groups, and 'none' when nothing in any dataset has an entry."""
    lines = ["", header, ""]
    groups = [(name, getattr(s, attr)) for name, s in stats.items() if getattr(s, attr)]
    if not groups:
        lines.append("- none")
    for i, (_name, entries) in enumerate(groups):
        if i > 0:
            lines += ["---", ""]
        lines += [f"- {line}" for line in entries]
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
        "| dataset | subjects | copied | skipped (exists) | failed | participants.tsv |",
        "|---|---|---|---|---|---|",
    ]
    for name, s in stats.items():
        lines.append(
            f"| {name} | {s.subjects_selected} | {s.copied} | {s.skipped_existing} | "
            f"{s.failed} | {s.participants_status} |"
        )
    lines += _grouped_section(
        stats,
        "missing",
        "## Missing (file not found for a specific subject, or an explicitly "
        "requested subject not present in this dataset)",
        "Missing Count",
    )
    lines += _grouped_section(
        stats,
        "ambiguous",
        "## Ambiguous (more than one registered file matched for a subject - "
        "highest-priority one used)",
        "Ambiguous Count",
    )
    lines += _grouped_section(
        stats,
        "non_conforming",
        "## Non-conforming subject folders (found on disk, excluded from retrieval)",
        "Non-conforming Count",
    )
    return "\n".join(lines)


def _write_report(config: RetrievalConfig, stats: dict[str, DatasetStats], now: datetime | None = None) -> Path:
    now = now or datetime.now()
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, stats, now))
    return report_path


def _log_path(config: RetrievalConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{now.strftime('%d-%m-%y__%H-%M')}.log"


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
    logging.info("done - report written to %s, log written to %s", report_path, log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
