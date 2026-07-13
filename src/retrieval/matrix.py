"""Full per-subject data-availability matrix.

Independent of what any specific retrieval run requests: for every subject
the registry knows about, and every (object, space, modality) registered in
file_patterns.json, shows whether the file exists and, if so, which filename
resolved. Answers "what does our data actually look like across everything we
know how to look for" as one complete picture - as opposed to
src.pipeline.retrieve_data's report, which only explains the gaps for
whatever this run's `retrieve` list actually asked for. Rendered by
scripts/data_summary.py as one presence/absence CSV per dataset.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.retrieval.config import RetrievalConfig, RetrieveItem
from src.retrieval.dataset import Dataset

MISSING_CELL = "missing"
PRESENT_CELL = "-"


@dataclass(frozen=True)
class MatrixRow:
    """One subject's presence/absence across every registered
    (object, space, modality)."""

    subject_id: str
    cells: dict[str, str]  # "object/space/modality" -> resolved filename, or MISSING_CELL


def combinations_from_file_patterns(config: RetrievalConfig) -> list[tuple[str, str, str]]:
    """Every (object, space, modality) triple registered in this project's
    file_patterns registry, across every known object, in a stable order -
    the matrix's columns, independent of what any particular run's
    `retrieve` list asks for. Assumes every leaf combination is exactly 3
    levels deep (object, space-or-equivalent, modality) - true for
    everything registered today (`lesion` and `feature` alike); a deeper
    object would need this generalized when it's actually added."""
    combos: list[tuple[str, str, str]] = []
    for object_ in config.file_patterns.project_roots:
        for combo in config.file_patterns.combinations_for(object_):
            if len(combo) != 3:
                raise ValueError(
                    "data_summary only supports 3-level (object, space, modality) "
                    f"combinations, got {combo}"
                )
            combos.append(combo)
    return sorted(combos)


def select_all_subjects(ds: Dataset, config: RetrievalConfig) -> list[str]:
    """Every subject visible in ANY (object, space) the registry knows about
    for this dataset, filtered by group_filter/subjects the same way a
    normal run would - broader than retrieve_data._select_subjects, which
    only looks at the exact (object, space) pairs a run's `retrieve` list
    requests. This is the full picture, independent of what's being
    retrieved."""
    all_spaces = config.file_patterns.all_object_spaces()
    if config.subjects is not None:
        found = {s for object_, space in all_spaces for s in ds.subjects(object_, space)}
        return sorted(found & set(config.subjects))
    if config.group_filter is None:
        return sorted({s for object_, space in all_spaces for s in ds.subjects(object_, space)})
    return sorted(
        {
            s
            for object_, space in all_spaces
            for group in config.group_filter
            for s in ds.subjects(object_, space, group=group)
        }
    )


def build_matrix(ds: Dataset, subjects: list[str], combinations: list[tuple[str, str, str]]) -> list[MatrixRow]:
    """One MatrixRow per subject, one cell per (object, space, modality)
    combination. If more than one registered template matches (e.g.
    lesion_roi's two naming variants), the cell shows the first match's
    filename - the CSV rendering (to_csv_rows) only cares about presence,
    not which/how many matched."""
    rows = []
    for subject_id in subjects:
        cells = {}
        for object_, space, modality in combinations:
            resolved = ds.resolve(subject_id, RetrieveItem(object=object_, space=space, modality=modality))
            cells[f"{object_}/{space}/{modality}"] = resolved[0].name if resolved else MISSING_CELL
        rows.append(MatrixRow(subject_id=subject_id, cells=cells))
    return rows


def count_present(rows: list[MatrixRow], combinations: list[tuple[str, str, str]]) -> dict[str, int]:
    """How many rows have a real file (not MISSING_CELL) for each column -
    meant to reconcile against a retrieve_data.py run's copied+skipped
    (exists) count for the same (object, space, modality), when that
    combination was actually requested in that run's config."""
    return {
        f"{object_}/{space}/{modality}": sum(
            1 for row in rows if row.cells[f"{object_}/{space}/{modality}"] != MISSING_CELL
        )
        for object_, space, modality in combinations
    }


def to_csv_rows(rows: list[MatrixRow], combinations: list[tuple[str, str, str]]) -> list[list[str]]:
    """Renders the matrix as plain presence/absence rows for csv.writer: a
    header, one row per subject (PRESENT_CELL "-" or MISSING_CELL "missing"
    per column - the point here is presence, not the exact filename, unlike
    MatrixRow.cells), and a trailing "present" row with count_present()'s
    per-column totals."""
    header = ["subject"] + [f"{object_}/{space}/{modality}" for object_, space, modality in combinations]
    csv_rows = [header]
    for row in rows:
        csv_rows.append(
            [row.subject_id]
            + [
                MISSING_CELL if row.cells[f"{object_}/{space}/{modality}"] == MISSING_CELL else PRESENT_CELL
                for object_, space, modality in combinations
            ]
        )
    counts = count_present(rows, combinations)
    csv_rows.append(
        ["present"] + [str(counts[f"{object_}/{space}/{modality}"]) for object_, space, modality in combinations]
    )
    return csv_rows
