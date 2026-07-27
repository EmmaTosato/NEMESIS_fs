"""Append-only per-method run history (production_runs.csv / tuning_runs.csv).

A run's config.md/report describe that one run in isolation. These CSVs answer
a different question - "every run (tuning sweep or production) that ever
wrote into a given method folder, and how did it differ" - across time.
Never overwritten, never atomic (a log, not a primary artifact - same tier
as summaries/logs, see docs/dev/design_patterns.md).

Deliberately does not know about session *meaning* - what session "s1.1" was
for, which datasets/modality it covers, etc. That's SESSIONS.md, hand-written
by a human (data/derived/lesion_matrix/SESSIONS.md, symlinked at
results/SESSIONS.md) - this module only ever appends a data row keyed by
run_id, never reads or writes session descriptions.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

FIELDNAMES = ["session", "id", "timestamp", "params", "output", "notes"]


def append_run_log_entry(
    log_dir: Path,
    run_id: str,
    now: datetime,
    run_type: str,
    params_summary: dict,
    output_dir: Path,
    run_notes: str | None,
    extra_columns: dict[str, str] | None = None,
) -> None:
    """Append one row to runs_csv_path, creating it (with a header) if absent.

    run_type distinguishes a fine-tuning sweep from a production run in the
    same log, without splitting them into separate files - seeing both in
    one chronological history is the point (e.g. "s2 used the params the
    20-07 tuning sweep in this same file found best").

    extra_columns prepends caller-specific leading columns (e.g. which of two
    axes a row belongs to, for a pipeline that shares one runs_csv_path
    across more than one dimension - see dim_reduction_clustering.py, whose
    runs.csv is shared by every clustering method run against a given
    reduction). Every call writing to the *same* runs_csv_path must pass the
    same extra_columns keys, since the header is only written once, on the
    first call. Omitted (None) by every other caller today - keeps FIELDNAMES
    as the exact, unchanged schema for their files.
    """
    if "_" in run_id:
        session, id_part = run_id.split("_", 1)
    else:
        session, id_part = run_id, ""

    file_name = "runs.csv" if run_type == "production" else "runs_tuning.csv"
    runs_csv_path = log_dir / file_name

    fieldnames = list(extra_columns) + FIELDNAMES if extra_columns else FIELDNAMES
    runs_csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not runs_csv_path.is_file()

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
                "params": json.dumps(params_summary),
                "output": str(output_dir),
                "notes": run_notes or "",
            }
        )
        writer.writerow(row)
