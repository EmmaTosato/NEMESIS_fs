"""Append-only per-method run history (runs.csv / runs_tuning.csv).

A run's config.md/report describe that one run in isolation. These CSVs answer
a different question - "every run (tuning sweep or production) that ever
wrote into a given method folder, and how did it differ" - across time.
Never overwritten, never atomic (a log, not a primary artifact - same tier
as summaries/logs, see docs/dev/design_patterns.md).

Deliberately does not know about session *meaning* - what session "s1.1" was
for, which datasets/modality it covers, etc. That's SESSIONS.md, hand-written
by a human (docs/experiments/SESSIONS.md) - this module only ever appends a
data row keyed by run_id, never reads or writes session descriptions.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

FIELDNAMES = ["session", "id", "timestamp", "input_path", "params", "output", "notes"]

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
    computed on the same underlying data (see docs/dev/config.md).

    extra_columns inserts caller-specific columns right after "id" (31-08-26 -
    previously prepended before "session", moved so "session"/"id" always
    stay the row's leading identity columns regardless of what a given
    caller adds), for a pipeline that shares one runs_csv_path across more
    than one dimension (e.g. atlas_combo for build_fc_matrix.py/mask_fc.py,
    or reduction_method/exploded tag_param values for clustering.py) - every
    call writing to the same runs_csv_path must pass the same extra_columns
    keys, since the header is only written once, on the first call.
    """
    if "_" in run_id:
        session, id_part = run_id.split("_", 1)
    else:
        session, id_part = run_id, ""

    if run_type not in _FILE_NAME_BY_RUN_TYPE:
        raise ValueError(f"run_type must be one of {sorted(_FILE_NAME_BY_RUN_TYPE)}, got {run_type!r}")
    runs_csv_path = log_dir / _FILE_NAME_BY_RUN_TYPE[run_type]

    fieldnames = FIELDNAMES[:2] + list(extra_columns) + FIELDNAMES[2:] if extra_columns else FIELDNAMES
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
                "id": id_part,
                "timestamp": now.strftime("%d-%m-%y %H:%M"),
                "input_path": str(input_path),
                "params": json.dumps(params_summary),
                "output": str(output_dir),
                "notes": run_notes or "",
            }
        )
        writer.writerow(row)
