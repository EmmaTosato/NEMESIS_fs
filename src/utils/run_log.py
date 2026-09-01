"""Append-only per-method run history (runs.csv / runs_tuning.csv).

A run's config.md/report describe that one run in isolation. These CSVs answer
a different question - "every run (tuning sweep or production) that ever
wrote into a given method folder, and how did it differ" - across time.
Never overwritten, never atomic (a log, not a primary artifact - same tier
as summaries/logs, see docs/dev/design_patterns.md).

Deliberately does not know about session *meaning* - what session "s1.1" was
for, which datasets/modality it covers, etc. That's data_sessions.md, hand-written
by a human (docs/experiments/data_sessions.md) - this module only ever appends a
data row keyed by run_id, never reads or writes session descriptions.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

FIELDNAMES = ["session", "timestamp", "input_path", "params", "output", "notes"]

RunType = Literal["production", "tuning"]
_FILE_NAME_BY_RUN_TYPE: dict[RunType, str] = {"production": "runs.csv", "tuning": "runs_tuning.csv"}


def append_run_log_entry(
    log_dir: Path,
    run_id: str,
    now: datetime,
    run_type: RunType,
    params_summary: dict,
    output_dir: Path,
    run_notes: str | None,
    input_path: Path,
    extra_columns: dict[str, str] | None = None,
) -> None:
    """Append one row to runs_csv_path, creating it (with a header) if absent.

    run_type picks which of two files the row goes to (runs.csv for
    "production", runs_tuning.csv for "tuning") - raises ValueError for
    anything else, the runtime backstop for a typo'd run_type.

    input_path is the source matrix this run was computed from - distinct
    from output_dir (where *this* run's own artifact landed), so a reader of
    runs.csv can tell whether two rows with identical params were actually
    computed on the same underlying data (see docs/dev/config.md). Always a
    plain path string - a caller whose input can itself be a dim_reduction.py
    run (clustering.py, reduced_data-aware) records what that embedding
    actually used via its own flat extra_columns instead (reduction_method/
    reduction_n_components/reduction_metric, src/pipeline/clustering.py's
    _reduction_extra_columns) rather than nesting it inside this column.

    run_id's only remaining role (31-08-26, since "id" was dropped as a
    column - it duplicated data already recoverable from output_dir's own
    name and, for dim_reduction.py/clustering.py production rows, from their
    own exploded tag_param extra_columns; no reader ever parsed it back
    apart) is naming this row's session: everything before its first "_" (a
    bare run_id with no "_" - e.g. a session_name with no production tag -
    is the whole session, same as before).

    extra_columns inserts caller-specific columns right after "session"
    (31-08-26, follows "id"'s removal - previously right after "id"), for a
    pipeline that shares one runs_csv_path across more than one dimension
    (e.g. atlas_combo for build_fc_matrix.py/mask_fc.py, or exploded
    tag_param/reduction_* values for dim_reduction.py/clustering.py) - every
    call writing to the same runs_csv_path must pass the same extra_columns
    keys, since the header is only written once, on the first call. A
    runs_csv_path shared across more than one distinct source (e.g. one
    clustering method's runs_tuning.csv receiving rows sourced from more
    than one reduction_method over its lifetime) must keep that key *set*
    identical on every call regardless of which source a given row actually
    has - fill with "" for a key that doesn't apply to this particular row
    rather than omitting it (clustering.py's reduction_n_components/
    reduction_metric do exactly this for a source method with no such
    hyperparameter, e.g. pca has no "metric").
    """
    session = run_id.split("_", 1)[0]

    if run_type not in _FILE_NAME_BY_RUN_TYPE:
        raise ValueError(f"run_type must be one of {sorted(_FILE_NAME_BY_RUN_TYPE)}, got {run_type!r}")
    runs_csv_path = log_dir / _FILE_NAME_BY_RUN_TYPE[run_type]

    fieldnames = FIELDNAMES[:1] + list(extra_columns) + FIELDNAMES[1:] if extra_columns else FIELDNAMES
    runs_csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not runs_csv_path.is_file()

    if not write_header:
        with runs_csv_path.open("r", newline="") as f:
            existing_header = next(csv.reader(f), None)
        if existing_header != fieldnames:
            raise ValueError(
                f"{runs_csv_path} has header {existing_header}, but the current schema is "
                f"{fieldnames} - FIELDNAMES (or this caller's extra_columns) changed since this "
                "file was created. Appending would silently misalign every column after the "
                "mismatch. Migrate the file to the new schema by hand before running this again."
            )

    with runs_csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        row = dict(extra_columns) if extra_columns else {}
        row.update(
            {
                "session": session,
                "timestamp": now.strftime("%d-%m-%y %H:%M"),
                "input_path": str(input_path),
                "params": json.dumps(params_summary),
                "output": str(output_dir),
                "notes": run_notes or "",
            }
        )
        writer.writerow(row)
