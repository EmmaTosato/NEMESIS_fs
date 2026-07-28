"""Standalone, read-only report: full per-subject data-availability CSV, one
file per dataset.

For every subject visible in any (object, pipeline) the registry knows about
(see matrix.select_all_subjects), and every leaf combination registered in
that config's file_patterns_local.json/file_patterns_server.json, shows whether the file exists on the
EBRAIN source: "-" if present, "missing" if not. Independent of what any
specific retrieval run's `retrieve` list asks for - a complete picture of
what the dataset actually has, not an explanation of one run's gaps (see
src.pipeline.retrieve_data for that). Never copies or modifies anything.

Unlike the timestamped copy_summary report, this one is a current snapshot,
not a run log: same fixed filename every time, overwritten on each call.

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/data_summary.py --config config/pipelines/retrieval_server.json
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.retrieval import matrix
from src.retrieval.config import RetrievalConfig, load_config
from src.retrieval.dataset import Dataset

REPORTS_ROOT = Path("assets") / "dataset_summaries"
REPORT_FILENAME_PREFIX = "data_summary"


def _dataset_report_path(dataset_name: str) -> Path:
    safe_name = dataset_name.replace("/", "_")
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    return REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{safe_name}.csv"


def write_reports(config: RetrievalConfig) -> list[Path]:
    combinations = matrix.combinations_from_file_patterns(config)
    written = []
    for name in config.datasets:
        ds = Dataset(name, config.file_patterns)
        subjects = matrix.select_all_subjects(ds, config)
        rows = matrix.build_matrix(ds, subjects, combinations)
        csv_rows = matrix.to_csv_rows(rows, combinations)
        path = _dataset_report_path(name)
        with path.open("w", newline="") as f:
            csv.writer(f).writerows(csv_rows)
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a retrieval_local.json/retrieval_server.json file")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    for path in write_reports(config):
        print(f"data summary written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
