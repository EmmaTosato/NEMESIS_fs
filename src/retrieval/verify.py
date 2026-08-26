"""Post-copy verification: does data/ actually match its current EBRAIN source?

Re-derives, for a given subject selection, the same source file
Dataset.resolve() would pick, and compares it byte-for-byte (sha256) against
the corresponding local file. Never trusts a successful copy or a
pre-existing destination as proof the content is right - see
docs/dev/retrieval.md's "Checksum verification" section for why, and for the
2 callers this module is shared between (src.pipeline.retrieve_data's own
post-copy phase, scripts/verify_retrieval.py standalone).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from src.retrieval.config import RetrievalConfig, RetrieveItem
from src.retrieval.dataset import Dataset
from src.retrieval.output_layout import local_dataset_root, local_relative_path, pipeline_folder


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


def local_destination(
    config: RetrievalConfig, dataset_name: str, subject_id: str, item: RetrieveItem, filename: str
) -> Path:
    return local_dataset_root(config, dataset_name) / local_relative_path(item, subject_id, filename)


def _verify_subject_files(
    name: str,
    ds: Dataset,
    subject_id: str,
    config: RetrievalConfig,
    result: VerificationResult,
    expected_local_files: set[Path],
) -> None:
    """Only checks retrieve items whose object this dataset actually has
    (see Dataset.has_object) - an item skipped at copy time for this dataset
    (see retrieve_data._report_skipped_retrieve_items) was never expected to
    land locally either, so it's not a verification target here."""
    for item in config.retrieve:
        if not ds.has_object(item.object):
            continue
        resolved = ds.resolve(subject_id, item)  # [] if source doesn't have it either - see stats.missing
        for source in resolved:
            local_path = local_destination(config, name, subject_id, item, source.name)
            expected_local_files.add(local_path)
            label = f"{name}: {subject_id} {'/'.join(item.path_key())}"
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


def _known_items_for_dataset(config: RetrievalConfig, ds: Dataset) -> list[RetrieveItem]:
    """Every (object, ...) combination registered in the registry for an
    object this dataset actually has - not just the ones this run's
    `config.retrieve` asks for. Used to recognize a local file left over
    from an earlier run that requested a different combination, as opposed
    to a genuine orphan (see _local_file_matches_known_registry_entry)."""
    items = []
    for object_ in config.file_patterns.project_roots:
        if not ds.has_object(object_):
            continue
        for combo in config.file_patterns.combinations_for(object_):
            items.append(RetrieveItem.from_path(*combo))
    return items


def _local_file_matches_known_registry_entry(
    relative_path: Path, config: RetrievalConfig, ds: Dataset
) -> bool:
    """True if `relative_path` (relative to the dataset's local root) is a
    legitimate local file for *some* registered combination this dataset
    has - even one not among this run's `config.retrieve` items - rather
    than a genuine orphan (stale naming, leftover from before a source
    rename). Checked structurally against the registry already loaded in
    memory (pipeline folder + datatype + filename-template match, subject_id
    substituted from the path itself) - deliberately does not re-query the
    source, since the point is recognizing *local* leftovers from a
    different retrieve item, not re-verifying their content (that's
    _verify_subject_files's job, for items this run does request)."""
    parts = relative_path.parts
    if len(parts) != 4:
        return False
    pipeline_seen, subject_id_seen, datatype_seen, filename_seen = parts
    for item in _known_items_for_dataset(config, ds):
        if item.datatype != datatype_seen or pipeline_folder(item) != pipeline_seen:
            continue
        templates = config.file_patterns.templates_for(*item.path_key())
        expected_filenames = {t.split("/")[-1].format(subject_id=subject_id_seen) for t in templates}
        if filename_seen in expected_filenames:
            return True
    return False


def _find_unexpected_local_files(
    name: str, ds: Dataset, config: RetrievalConfig, expected_local_files: set[Path], result: VerificationResult
) -> None:
    root = local_dataset_root(config, name)
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if not path.is_file() or path in expected_local_files:
            continue
        relative_path = path.relative_to(root)
        if relative_path == Path("participants.tsv"):
            continue  # always a known per-dataset file type, regardless of include_tabular_data this run
        if _local_file_matches_known_registry_entry(relative_path, config, ds):
            continue  # legitimate leftover from a different retrieve item/earlier run, not an orphan
        result.unexpected_local_files.append(
            f"{name}: {path} - not the current resolution for any expected subject/retrieve item"
        )


def verify_dataset(name: str, ds: Dataset, subjects: list[str], config: RetrievalConfig) -> VerificationResult:
    """Verifies data/ for one dataset against source, for exactly `subjects`
    (the same selection the copy phase used - callers own that selection,
    this function only verifies). Also checks participants.tsv when
    requested, and flags any local file that's a genuine orphan - not the
    current resolution for any expected subject/retrieve item, *and* not a
    recognized leftover from some other registered combination this dataset
    has (see _local_file_matches_known_registry_entry) - stale naming from
    before a source rename, not just "this run didn't ask for it"."""
    result = VerificationResult()
    expected_local_files: set[Path] = set()
    for subject_id in subjects:
        _verify_subject_files(name, ds, subject_id, config, result, expected_local_files)
    _verify_participants_file(name, ds, config, result, expected_local_files)
    _find_unexpected_local_files(name, ds, config, expected_local_files, result)
    return result
