"""Standalone, on-demand re-check: does data/ still match its EBRAIN source?

Thin CLI wrapper around src.retrieval.verify - the same check the retrieval
pipeline runs automatically at the end of every run (see
src.pipeline.retrieve_data._verify_dataset_copies). Useful when you want to
re-verify already-retrieved data without doing a run at all: read-only, never
copies or modifies anything.

Runs the same upfront validation as retrieve_data.py's main() before
verifying anything (_validate_upfront - group_filter matches >=1 subject,
explicit `subjects` actually exist somewhere) - a typo'd subjects/group_filter
entry must stop this script with a clear error, not silently verify an empty
selection and report "0 problems found" as if everything had been checked.

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/verify_retrieval.py --config config/pipelines/retrieval_server.json
"""

from __future__ import annotations

import argparse
import sys

from src.pipeline.retrieve_data import _build_datasets, _select_subjects, _validate_upfront
from src.retrieval import verify
from src.retrieval.config import load_config


def _print_section(title: str, entries: list[str]) -> None:
    print(f"\n## {title} ({len(entries)})")
    for entry in entries:
        print(f"- {entry}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a retrieval_local.json/retrieval_server.json file")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    datasets = _build_datasets(config)
    try:
        _validate_upfront(datasets, config)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    result = verify.VerificationResult()
    for name, ds in datasets.items():
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
