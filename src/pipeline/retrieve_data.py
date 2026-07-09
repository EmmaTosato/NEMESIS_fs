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
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.retrieval.config import RetrievalConfig, load_config
from src.retrieval.dataset import Dataset

REPORTS_ROOT = Path("reports")


@dataclass
class DatasetStats:
    subjects_selected: int = 0
    copied: int = 0
    skipped_existing: int = 0
    failed: int = 0
    missing: list[str] = field(default_factory=list)
    participants_status: str = "not requested"


def _build_datasets(config: RetrievalConfig) -> dict[str, Dataset]:
    """Instantiate a Dataset per requested name. Raises FileNotFoundError
    immediately if any dataset root is unreachable - before any copying."""
    return {name: Dataset(config.project_root, name) for name in config.datasets}


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
        if item.space == "native" and item.modality not in ds.available_sequences():
            raise ValueError(
                f"{name}: does not have modality {item.modality!r} "
                f"(available: {sorted(ds.available_sequences())})"
            )
        if item.space == "mni" and not ds.has_mni_mask():
            raise ValueError(f"{name}: has no derivatives/manual_masks")


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
        source = (
            ds.native(subject_id, item.modality) if item.space == "native" else ds.mni_mask(subject_id)
        )
        if source is None:
            stats.missing.append(f"{name}: {subject_id} - no {item.space}/{item.modality}")
            continue
        destination = _destination_path(config, name, subject_id, item.space, source)
        _copy_one(source, destination, config.overwrite, stats)


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


def _retrieve_dataset(name: str, ds: Dataset, config: RetrievalConfig, stats: DatasetStats) -> None:
    subjects = _select_subjects(ds, config)
    stats.subjects_selected = len(subjects)
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


def _build_report(config: RetrievalConfig, stats: dict[str, DatasetStats], timestamp: str) -> str:
    requested = ", ".join(f"{item.space}/{item.modality}" for item in config.retrieve)
    lines = [
        f"# Data Retrieval Report — {timestamp}",
        "",
        f"Requested: {requested}",
        f"Group filter: {config.group_filter}",
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
    all_missing = [line for s in stats.values() for line in s.missing]
    lines += ["", "## Missing (file not found for a specific subject)", ""]
    lines += [f"- {line}" for line in all_missing] if all_missing else ["- none"]
    return "\n".join(lines)


def _write_report(config: RetrievalConfig, stats: dict[str, DatasetStats]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"retrieval_{timestamp}.md"
    report_path.write_text(_build_report(config, stats, timestamp))
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Retrieve lesion data and metadata into the local workspace."
    )
    parser.add_argument("--config", required=True, help="Path to a data_retrieval.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        config = load_config(args.config)
        datasets = _build_datasets(config)
        _validate_upfront(datasets, config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    stats = _retrieve_all(datasets, config)
    report_path = _write_report(config, stats)
    logging.info("done - report written to %s", report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
