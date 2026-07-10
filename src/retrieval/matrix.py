"""Full per-subject data-availability matrix.

Independent of what any specific retrieval run requests: for every subject
selected by a config, and every (space, modality) registered in
file_patterns.json, shows whether the file exists and, if so, which filename
resolved. Answers "what does our data actually look like across everything we
know how to look for" as one complete picture - as opposed to
src.pipeline.retrieve_data's report, which only explains the gaps for
whatever this run's `retrieve` list actually asked for.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.retrieval.config import RetrievalConfig
from src.retrieval.dataset import Dataset

MISSING_CELL = "missing"

# native before mni, alphabetical within each - stable column order across runs.
_SPACE_ORDER = {"native": 0, "mni": 1}


@dataclass(frozen=True)
class MatrixRow:
    """One subject's presence/absence across every registered (space, modality)."""

    subject_id: str
    cells: dict[str, str]  # "space/modality" -> resolved filename, or MISSING_CELL


def combinations_from_file_patterns(config: RetrievalConfig) -> list[tuple[str, str]]:
    """Every (space, modality) pair registered in this project's file_patterns
    registry, in a stable order - the matrix's columns."""
    return sorted(config.file_patterns.patterns.keys(), key=lambda sm: (_SPACE_ORDER[sm[0]], sm[1]))


def build_matrix(ds: Dataset, subjects: list[str], combinations: list[tuple[str, str]]) -> list[MatrixRow]:
    """One MatrixRow per subject, one cell per (space, modality) combination."""
    rows = []
    for subject_id in subjects:
        cells = {}
        for space, modality in combinations:
            resolved = ds.resolve(subject_id, space, modality)
            cells[f"{space}/{modality}"] = resolved.path.name if resolved else MISSING_CELL
        rows.append(MatrixRow(subject_id=subject_id, cells=cells))
    return rows


def count_present(rows: list[MatrixRow], combinations: list[tuple[str, str]]) -> dict[str, int]:
    """How many rows have a real file (not MISSING_CELL) for each column -
    meant to reconcile against a retrieve_data.py run's copied+skipped
    (exists) count for the same (space, modality), when that combination was
    actually requested in that run's config."""
    return {
        f"{space}/{modality}": sum(1 for row in rows if row.cells[f"{space}/{modality}"] != MISSING_CELL)
        for space, modality in combinations
    }
