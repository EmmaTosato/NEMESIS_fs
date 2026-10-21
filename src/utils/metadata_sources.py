"""Parsing of config/registry/metadata_sources.json - the dataset -> paths registry.

Shared by src/pipeline/populate_metadata.py and src/pipeline/enrich_metadata.py so
the mapping from a dataset name to its raw participants.tsv and its derivatives
directory exists in exactly one place. It is not mechanically derivable
(`participants_UCL.tsv` <-> `UCL-UK/UCLStrokeData`), so it has to be declared.

Lives in utils rather than next to either consumer: both are entry points, and
an entry point importing another entry point would invert the layering
(.claude/code_standards.md §1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetSource:
    participants_tsv: Path
    derivatives_dir: Path


def _object_without_duplicates(pairs: list[tuple[str, object]], path: Path) -> dict:
    keys = [k for k, _ in pairs]
    duplicates = sorted({k for k in keys if keys.count(k) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicate key(s) {duplicates} in a JSON object - json.loads would silently keep the last")
    return dict(pairs)


def load_metadata_sources(path: Path) -> dict[str, DatasetSource]:
    """Parse the shared dataset->paths registry, validating its shape before use."""
    raw = json.loads(Path(path).read_text(), object_pairs_hook=lambda pairs: _object_without_duplicates(pairs, path))
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{path}: expected a non-empty JSON object of dataset -> paths")
    sources = {}
    for dataset, entry in raw.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: {dataset!r} must map to an object, got {type(entry).__name__}")
        for key in ("participants_tsv", "derivatives_dir"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f"{path}: {dataset!r} is missing a non-empty string {key!r}")
        sources[dataset] = DatasetSource(Path(entry["participants_tsv"]), Path(entry["derivatives_dir"]))
    return sources
