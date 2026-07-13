"""Post-copy verification: does data/ actually match its current EBRAIN source?

Re-derives, for a given subject selection, the same source file
Dataset.resolve() would pick, and compares it byte-for-byte (sha256) against
the corresponding local file. Never trusts a successful copy or a pre-existing
destination as proof the content is right: a copy can be corrupted mid-write,
and a local file that was correct when first retrieved may no longer match if
the source changed upstream since (e.g. a corrected lesion mask).

Shared by two callers, on purpose - one algorithm, not two:
- src.pipeline.retrieve_data: runs this automatically as the pipeline's last
  phase, once every requested dataset has finished copying (never
  interleaved with the copy phase of any dataset).
- scripts/verify_retrieval.py: standalone, on-demand re-check of data/
  against source, without running a retrieval at all.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from src.retrieval.config import RetrievalConfig
from src.retrieval.dataset import Dataset


@dataclass
class VerificationResult:
    mismatched: list[str] = field(default_factory=list)
    missing_locally: list[str] = field(default_factory=list)
    unexpected_local_files: list[str] = field(default_factory=list)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_dataset_root(config: RetrievalConfig, dataset_name: str) -> Path:
    return config.output_root / config.project / dataset_name


def local_destination(
    config: RetrievalConfig, dataset_name: str, subject_id: str, object_: str, space: str, filename: str
) -> Path:
    return local_dataset_root(config, dataset_name) / subject_id / object_ / space / filename


def _verify_subject_files(
    name: str,
    ds: Dataset,
    subject_id: str,
    config: RetrievalConfig,
    result: VerificationResult,
    expected_local_files: set[Path],
) -> None:
    for item in config.retrieve:
        resolved = ds.resolve(subject_id, item)  # [] if source doesn't have it either - see stats.missing
        for source in resolved:
            local_path = local_destination(config, name, subject_id, item.object, item.space, source.name)
            expected_local_files.add(local_path)
            label = f"{name}: {subject_id} {item.object}/{item.space}/{item.modality}"
            if not local_path.is_file():
                result.missing_locally.append(f"{label} - source has it ({source}) but data/ doesn't")
                continue
            if sha256(source) != sha256(local_path):
                result.mismatched.append(
                    f"{label} - checksum differs from source: {source} vs {local_path}"
                )


def _verify_participants_file(
    name: str,
    ds: Dataset,
    config: RetrievalConfig,
    result: VerificationResult,
    expected_local_files: set[Path],
) -> None:
    if not config.include_tabular_data:
        return
    source = ds.participants_tsv_path()
    if source is None:
        return
    local_path = local_dataset_root(config, name) / "participants.tsv"
    expected_local_files.add(local_path)
    label = f"{name}: participants.tsv"
    if not local_path.is_file():
        result.missing_locally.append(f"{label} - source has it ({source}) but data/ doesn't")
        return
    if sha256(source) != sha256(local_path):
        result.mismatched.append(f"{label} - checksum differs from source: {source} vs {local_path}")


def _find_unexpected_local_files(
    name: str, config: RetrievalConfig, expected_local_files: set[Path], result: VerificationResult
) -> None:
    root = local_dataset_root(config, name)
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if path.is_file() and path not in expected_local_files:
            result.unexpected_local_files.append(
                f"{name}: {path} - not the current resolution for any expected subject/modality"
            )


def verify_dataset(name: str, ds: Dataset, subjects: list[str], config: RetrievalConfig) -> VerificationResult:
    """Verifies data/ for one dataset against source, for exactly `subjects`
    (the same selection the copy phase used - callers own that selection,
    this function only verifies). Also checks participants.tsv when
    requested, and flags any local file that no longer corresponds to a
    current source resolution (stale naming, leftover from a prior run)."""
    result = VerificationResult()
    expected_local_files: set[Path] = set()
    for subject_id in subjects:
        _verify_subject_files(name, ds, subject_id, config, result, expected_local_files)
    _verify_participants_file(name, ds, config, result, expected_local_files)
    _find_unexpected_local_files(name, config, expected_local_files, result)
    return result
