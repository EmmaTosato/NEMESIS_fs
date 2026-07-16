"""Full per-subject data-availability matrix.

Independent of what any specific retrieval run requests: for every subject
the registry knows about, and every combination registered in
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
PRESENT_CELL = "present"


@dataclass(frozen=True)
class MatrixRow:
    """One subject's presence/absence across every registered leaf
    combination."""

    subject_id: str
    cells: dict[str, str]  # "/".join(path_key()) -> resolved filename, or MISSING_CELL


def combinations_from_file_patterns(config: RetrievalConfig) -> list[tuple[str, ...]]:
    """Every leaf combination registered in this project's file_patterns
    registry, across every known object, in a stable order - the matrix's
    columns, independent of what any particular run's `retrieve` list asks
    for. Depth varies by object (see RetrieveItem) - RetrieveItem.from_path()
    is the single source of truth for what shape is valid per object, so
    this raises the same clear error it would raise for a malformed
    `retrieve` entry, rather than an ad hoc depth check."""
    combos: list[tuple[str, ...]] = []
    for object_ in config.file_patterns.project_roots:
        for combo in config.file_patterns.combinations_for(object_):
            RetrieveItem.from_path(*combo)  # raises if this object's leaves have the wrong shape
            combos.append(combo)
    return sorted(combos)


def select_all_subjects(ds: Dataset, config: RetrievalConfig) -> list[str]:
    """Every subject visible under ANY (object, pipeline) the registry knows
    about for this dataset, filtered by group_filter/subjects the same way a
    normal run would - broader than retrieve_data._select_subjects, which
    only looks at the exact (object, pipeline) pairs a run's `retrieve` list
    requests. This is the full picture, independent of what's being
    retrieved.

    Skips objects this dataset structurally doesn't have at all (e.g. no
    `features/` tree yet - see Dataset.has_object) rather than raising: that
    is a legitimate "nothing to report for this object here", not a
    failure."""
    discovery_keys = {(o, p) for o, p in config.file_patterns.subject_discovery_keys() if ds.has_object(o)}
    if config.subjects is not None:
        found = {s for object_, pipeline in discovery_keys for s in ds.subjects(object_, pipeline)}
        return sorted(found & set(config.subjects))
    if config.group_filter is None:
        return sorted({s for object_, pipeline in discovery_keys for s in ds.subjects(object_, pipeline)})
    return sorted(
        {
            s
            for object_, pipeline in discovery_keys
            for group in config.group_filter
            for s in ds.subjects(object_, pipeline, group=group)
        }
    )


def build_matrix(ds: Dataset, subjects: list[str], combinations: list[tuple[str, ...]]) -> list[MatrixRow]:
    """One MatrixRow per subject, one cell per registered leaf combination.
    If more than one registered template matches (e.g. two simultaneously
    present atlas files, or naming-variant alternates), the cell shows the
    first match's filename - the CSV rendering (to_csv_rows) only cares
    about presence, not which/how many matched.

    A column whose object this dataset doesn't structurally have at all
    (e.g. no `features/` tree yet - see Dataset.has_object) is MISSING_CELL
    for every subject, without calling resolve() at all - that would raise,
    since resolve() is for a specifically-requested object where a missing
    root is a real error, not "this object doesn't apply here"."""
    rows = []
    for subject_id in subjects:
        cells = {}
        for combo in combinations:
            key = "/".join(combo)
            object_ = combo[0]
            if not ds.has_object(object_):
                cells[key] = MISSING_CELL
                continue
            item = RetrieveItem.from_path(*combo)
            resolved = ds.resolve(subject_id, item)
            cells[key] = resolved[0].name if resolved else MISSING_CELL
        rows.append(MatrixRow(subject_id=subject_id, cells=cells))
    return rows


def to_csv_rows(rows: list[MatrixRow], combinations: list[tuple[str, ...]]) -> list[list[str]]:
    """Renders the matrix as plain presence/absence rows for csv.writer: a
    header, one row per subject (PRESENT_CELL "present" or MISSING_CELL
    "missing" per column - the point here is presence, not the exact
    filename, unlike MatrixRow.cells). No aggregate rows - per-column
    present/missing totals are computed separately (in a notebook), not
    baked into this file."""
    columns = ["/".join(combo) for combo in combinations]
    header = ["subject"] + columns
    csv_rows = [header]
    for row in rows:
        csv_rows.append(
            [row.subject_id]
            + [
                MISSING_CELL if row.cells[key] == MISSING_CELL else PRESENT_CELL
                for key in columns
            ]
        )
    return csv_rows
