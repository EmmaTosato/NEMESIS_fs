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
INCOMPLETE_CELL = "incomplete"
PRESENT_CELL = "present"


@dataclass(frozen=True)
class CellStatus:
    """One subject's status for one registered leaf combination: how many of
    the combination's registered templates matched on disk (`matched`), out
    of how many are registered in total (`total`) - see docs/dev/retrieval.md
    for why this isn't just a binary present/missing. `filename` is the
    first matched file's name, or None if nothing matched.

    marker() collapses this into the three-state presence used by the CSV:
    matched == 0 -> missing; 0 < matched < total -> incomplete; matched ==
    total -> present."""

    matched: int
    total: int
    filename: str | None

    def marker(self) -> str:
        if self.matched == 0:
            return MISSING_CELL
        if self.matched < self.total:
            return INCOMPLETE_CELL
        return PRESENT_CELL


@dataclass(frozen=True)
class MatrixRow:
    """One subject's presence/absence across every registered leaf
    combination."""

    subject_id: str
    cells: dict[str, CellStatus]  # "/".join(path_key()) -> CellStatus


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


def _discovery_keys(ds: Dataset, config: RetrievalConfig) -> set[tuple[str, str | None]]:
    """Every (object, pipeline) subject_discovery_keys() lists that this
    dataset structurally has (see Dataset.has_object) - the full picture
    select_all_subjects/validate_subject_filters both discover subjects
    from, independent of any specific run's `retrieve` list."""
    return {(o, p) for o, p in config.file_patterns.subject_discovery_keys() if ds.has_object(o)}


def select_all_subjects(ds: Dataset, config: RetrievalConfig) -> list[str]:
    """Every subject visible under ANY (object, pipeline) the registry knows
    about for this dataset, filtered by group_filter/subjects the same way a
    normal run would - broader than retrieve_data._select_subjects (see
    docs/dev/retrieval.md), the full picture independent of what's being
    retrieved. Skips objects this dataset structurally doesn't have (rather
    than raising) - call validate_subject_filters first to distinguish that
    from a group_filter/subjects that matches nothing by config mistake."""
    discovery_keys = _discovery_keys(ds, config)
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


def validate_subject_filters(ds: Dataset, config: RetrievalConfig, dataset_name: str) -> None:
    """Raise ValueError if group_filter/subjects would silently select zero
    subjects for this dataset - the same "structurally impossible request"
    check retrieve_data._validate_upfront makes for a run's own narrower
    subject set, scoped here to the full (object, pipeline) picture
    select_all_subjects draws from instead (see docs/dev/retrieval.md for
    why retrieve_data's own validators can't be reused directly here).

    A dataset with genuinely zero subjects (no filter applied) is not an
    error here - select_all_subjects' own documented "nothing to report"
    case, not a config mistake."""
    if config.subjects is None and config.group_filter is None:
        return
    discovery_keys = _discovery_keys(ds, config)
    all_subjects = {s for object_, pipeline in discovery_keys for s in ds.subjects(object_, pipeline)}
    if not all_subjects:
        return
    if config.subjects is not None:
        unknown = [s for s in config.subjects if s not in all_subjects]
        if unknown:
            raise ValueError(f"{dataset_name}: subjects not found in this dataset: {unknown}")
        return
    for group in config.group_filter:
        matched = {s for object_, pipeline in discovery_keys for s in ds.subjects(object_, pipeline, group=group)}
        if not matched:
            raise ValueError(f"{dataset_name}: group_filter {group!r} matches 0 subjects")


def build_matrix(ds: Dataset, subjects: list[str], combinations: list[tuple[str, ...]]) -> list[MatrixRow]:
    """One MatrixRow per subject, one CellStatus per registered leaf
    combination (see CellStatus's own docstring / docs/dev/retrieval.md for
    why this isn't just binary present/missing). A column whose object this
    dataset doesn't structurally have gets matched=0 for every subject
    without calling resolve() at all - that would raise, since resolve() is
    for a specifically-requested object where a missing root is a real
    error, not "this object doesn't apply here"."""
    rows = []
    for subject_id in subjects:
        cells = {}
        for combo in combinations:
            key = "/".join(combo)
            object_ = combo[0]
            total = len(ds.file_patterns.templates_for(*combo))
            if not ds.has_object(object_):
                cells[key] = CellStatus(matched=0, total=total, filename=None)
                continue
            item = RetrieveItem.from_path(*combo)
            resolved = ds.resolve(subject_id, item)
            cells[key] = CellStatus(
                matched=len(resolved),
                total=total,
                filename=resolved[0].name if resolved else None,
            )
        rows.append(MatrixRow(subject_id=subject_id, cells=cells))
    return rows


def to_csv_rows(rows: list[MatrixRow], combinations: list[tuple[str, ...]]) -> list[list[str]]:
    """Renders the matrix as three-state presence rows for csv.writer: a
    header, one row per subject (PRESENT_CELL "present" / INCOMPLETE_CELL
    "incomplete" / MISSING_CELL "missing" per column, from
    CellStatus.marker() - the point here is presence, not the exact
    filename, unlike MatrixRow.cells). No aggregate rows - per-column
    present/missing totals are computed separately (in a notebook), not
    baked into this file."""
    columns = ["/".join(combo) for combo in combinations]
    header = ["subject"] + columns
    csv_rows = [header]
    for row in rows:
        csv_rows.append([row.subject_id] + [row.cells[key].marker() for key in columns])
    return csv_rows
