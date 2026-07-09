"""One-off check: does data/ actually match its EBRAIN source, subject by subject?

Re-derives, for every subject the config says should have been retrieved, the
same source file Dataset.resolve() would have picked, and compares it byte-
for-byte (sha256) against the corresponding local file. Reports mismatches,
subjects/files missing locally, and local files that don't correspond to any
current source resolution (stale copies from a prior naming scheme or a
config that has since changed).

Usage:
    conda run -n nemesis python scripts/verify_retrieval.py --config config/data_retrieval.json
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from src.retrieval.config import RetrievalConfig, load_config
from src.retrieval.dataset import Dataset


@dataclass
class VerificationResult:
    ok: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    missing_locally: list[str] = field(default_factory=list)
    unexpected_local_files: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _select_subjects(ds: Dataset, config: RetrievalConfig) -> list[str]:
    if config.subjects is not None:
        wanted = set(config.subjects)
        return [s for s in ds.subjects() if s in wanted]
    if config.group_filter is None:
        return ds.subjects()
    selected = {s for group in config.group_filter for s in ds.subjects(group=group)}
    return sorted(selected)


def _local_dataset_root(config: RetrievalConfig, dataset_name: str) -> Path:
    return config.output_root / config.project / dataset_name


def _local_destination(config: RetrievalConfig, dataset_name: str, subject_id: str, space: str, filename: str) -> Path:
    return _local_dataset_root(config, dataset_name) / subject_id / "lesion" / space / filename


def _verify_subject(
    name: str, ds: Dataset, subject_id: str, config: RetrievalConfig, result: VerificationResult, expected_local_files: set[Path]
) -> None:
    for item in config.retrieve:
        resolved = ds.resolve(subject_id, item.space, item.modality)
        if resolved is None:
            continue
        local_path = _local_destination(config, name, subject_id, item.space, resolved.path.name)
        expected_local_files.add(local_path)
        label = f"{name}: {subject_id} {item.space}/{item.modality}"
        if not local_path.is_file():
            result.missing_locally.append(f"{label} - source exists ({resolved.path}) but not copied to {local_path}")
            continue
        if _sha256(resolved.path) != _sha256(local_path):
            result.mismatched.append(f"{label} - checksum differs: {resolved.path} vs {local_path}")
            continue
        result.ok.append(f"{label} - matches {resolved.path}")


def _verify_participants(name: str, ds: Dataset, config: RetrievalConfig, result: VerificationResult, expected_local_files: set[Path]) -> None:
    if not config.include_tabular_data:
        return
    source = ds.participants_tsv_path()
    if source is None:
        return
    local_path = _local_dataset_root(config, name) / "participants.tsv"
    expected_local_files.add(local_path)
    label = f"{name}: participants.tsv"
    if not local_path.is_file():
        result.missing_locally.append(f"{label} - source exists ({source}) but not copied to {local_path}")
        return
    if _sha256(source) != _sha256(local_path):
        result.mismatched.append(f"{label} - checksum differs: {source} vs {local_path}")
        return
    result.ok.append(f"{label} - matches {source}")


def _find_unexpected_local_files(name: str, config: RetrievalConfig, expected_local_files: set[Path], result: VerificationResult) -> None:
    root = _local_dataset_root(config, name)
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if path.is_file() and path not in expected_local_files:
            result.unexpected_local_files.append(f"{name}: {path} - not the current resolution for any expected subject/modality")


def verify(config: RetrievalConfig) -> VerificationResult:
    result = VerificationResult()
    for name in config.datasets:
        ds = Dataset(config.project_root, name, config.file_patterns)
        expected_subjects = _select_subjects(ds, config)
        expected_local_files: set[Path] = set()
        for subject_id in expected_subjects:
            _verify_subject(name, ds, subject_id, config, result, expected_local_files)
        _verify_participants(name, ds, config, result, expected_local_files)
        _find_unexpected_local_files(name, config, expected_local_files, result)
    return result


def _print_section(title: str, entries: list[str]) -> None:
    print(f"\n## {title} ({len(entries)})")
    for entry in entries:
        print(f"- {entry}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a data_retrieval.json file")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    result = verify(config)

    print(f"OK: {len(result.ok)} file(s) verified byte-for-byte against source")
    _print_section("Checksum mismatches", result.mismatched)
    _print_section("Missing local file (source has it, not copied)", result.missing_locally)
    _print_section("Unexpected local files (stale / no longer resolvable from source)", result.unexpected_local_files)

    return 1 if (result.mismatched or result.missing_locally or result.unexpected_local_files) else 0


if __name__ == "__main__":
    raise SystemExit(main())
