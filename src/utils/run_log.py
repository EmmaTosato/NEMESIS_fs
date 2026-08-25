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

    run_type picks which of two files the row goes to - runs.csv for
    "production", runs_tuning.csv for "tuning" - so a fine-tuning sweep and a
    production run never land in the same file, even though they share this
    same append/schema logic. Raises ValueError for anything else - a typo'd
    or new-but-unregistered run_type must not silently fall into one of the
    two files by accident (every call site in this repo passes one of these
    two literal strings; a Literal-typed caller catches a typo at type-check
    time already, this is the runtime backstop).

    input_path (14-08-26) is the source matrix this run was computed from -
    every pipeline's own Config dataclass already carries this, so callers
    just forward `config.input_path`, no new data to compute. Distinct from
    `output_dir`: `output_dir` is where *this* run's own artifact ended up,
    `input_path` is what it was built *from* - added specifically so a reader
    of runs.csv (e.g. results/dim_reduction_strategies.csv's generator, or a
    future "have I already computed this?" lookup helper) can tell whether two
    rows with identical `params` were actually computed on the same underlying
    data, not just assume it from a matching path string
    (docs/dev/clustering_migration_plan.md §6-7).

    extra_columns prepends caller-specific leading columns (e.g. which of two
    axes a row belongs to, for a pipeline that shares one runs_csv_path
    across more than one dimension - see build_fc_matrix.py/mask_fc.py, whose
    runs.csv is shared across every atlas_combo run against a given dataset).
    Every call writing to the *same* runs_csv_path must pass the
    same extra_columns keys, since the header is only written once, on the
    first call. Omitted (None) by every other caller today - keeps FIELDNAMES
    as the exact, unchanged schema for their files.
    """
    if "_" in run_id:
        session, id_part = run_id.split("_", 1)
    else:
        session, id_part = run_id, ""

    if run_type not in _FILE_NAME_BY_RUN_TYPE:
        raise ValueError(f"run_type must be one of {sorted(_FILE_NAME_BY_RUN_TYPE)}, got {run_type!r}")
    runs_csv_path = log_dir / _FILE_NAME_BY_RUN_TYPE[run_type]

    fieldnames = list(extra_columns) + FIELDNAMES if extra_columns else FIELDNAMES
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
