"""Standalone, read-only report: full per-subject data-availability matrix.

For every subject selected by a data_retrieval.json config, and every
(space, modality) registered in that config's file_patterns.json, shows
whether the file exists on the EBRAIN source and, if so, which filename
resolved. Independent of what any specific retrieval run's `retrieve` list
asks for - a complete picture of what the dataset actually has, not an
explanation of one run's gaps (see src.pipeline.retrieve_data for that).
Never copies or modifies anything.

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/dataset_matrix.py --config config/data_retrieval.json
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from src.pipeline.retrieve_data import REPORTS_ROOT, _select_subjects
from src.retrieval import matrix
from src.retrieval.config import RetrievalConfig, load_config
from src.retrieval.dataset import Dataset

REPORT_FILENAME_PREFIX = "dataset_matrix"


def _dataset_table(
    name: str, rows: list[matrix.MatrixRow], combinations: list[tuple[str, str]]
) -> list[str]:
    columns = [f"{space}/{modality}" for space, modality in combinations]
    lines = [
        "",
        f"## {name}",
        "",
        "| subject | " + " | ".join(columns) + " |",
        "|---|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append(f"| {row.subject_id} | " + " | ".join(row.cells[c] for c in columns) + " |")
    counts = matrix.count_present(rows, combinations)
    lines.append("| **present** | " + " | ".join(str(counts[c]) for c in columns) + " |")
    return lines


def _build_report(config: RetrievalConfig, now: datetime) -> str:
    lines = [
        f"# {REPORT_FILENAME_PREFIX}_{config.project}_{now.strftime('%d-%m-%y')}",
        f"## {now.strftime('%H:%M')}",
        "",
        "Full data-availability matrix: one row per subject, one column per (space, modality) "
        "registered in `config/file_patterns.json`. Cell = resolved filename, or `missing` if "
        "no registered template matches on disk for that subject. The `present` row at the "
        "bottom of each table sums how many subjects have a real file per column - for a "
        "combination actually requested in `retrieve`, that number should match "
        "`copied + skipped (exists)` for the same (space, modality) in the matching "
        "`copy_summary` report.",
    ]
    combinations = matrix.combinations_from_file_patterns(config)
    for name in config.datasets:
        ds = Dataset(config.project_root, name, config.file_patterns)
        subjects = _select_subjects(ds, config)
        rows = matrix.build_matrix(ds, subjects, combinations)
        lines += _dataset_table(name, rows, combinations)
    return "\n".join(lines)


def _write_report(config: RetrievalConfig, now: datetime | None = None) -> Path:
    now = now or datetime.now()
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, now))
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a data_retrieval.json file")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    report_path = _write_report(config)
    print(f"dataset matrix written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
