"""Standalone, on-demand re-check: does data/ still match its EBRAIN source?

Thin CLI wrapper around src.retrieval.verify - the same check the retrieval
pipeline runs automatically at the end of every run (see
src.pipeline.retrieve_data._verify_dataset_copies). Useful when you want to
re-verify already-retrieved data without doing a run at all: read-only, never
copies or modifies anything.

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/verify_retrieval.py --config config/data_retrieval.json
"""

from __future__ import annotations

import argparse

from src.pipeline.retrieve_data import _select_subjects
from src.retrieval import verify
from src.retrieval.config import load_config
from src.retrieval.dataset import Dataset


def _print_section(title: str, entries: list[str]) -> None:
    print(f"\n## {title} ({len(entries)})")
    for entry in entries:
        print(f"- {entry}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a data_retrieval.json file")
    args = parser.parse_args(argv)

    config = load_config(args.config)

    result = verify.VerificationResult()
    for name in config.datasets:
        ds = Dataset(config.project_root, name, config.file_patterns)
        subjects = _select_subjects(ds, config)
        dataset_result = verify.verify_dataset(name, ds, subjects, config)
        result.mismatched += dataset_result.mismatched
        result.missing_locally += dataset_result.missing_locally
        result.unexpected_local_files += dataset_result.unexpected_local_files

    _print_section("Checksum mismatches", result.mismatched)
    _print_section("Missing local file (source has it, not copied)", result.missing_locally)
    _print_section("Unexpected local files (stale / no longer resolvable from source)", result.unexpected_local_files)

    return 1 if (result.mismatched or result.missing_locally or result.unexpected_local_files) else 0


if __name__ == "__main__":
    raise SystemExit(main())
