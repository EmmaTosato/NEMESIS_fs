"""Append-only per-method run history (RUNS.md), separate from a single run's own README.md.

A run's README/report describe that one run in isolation. RUNS.md answers a
different question - "how does this run differ from the previous ones, and
why" - across every run (tuning sweep or production) that ever wrote into a
given method folder. Never overwritten, never atomic (a log, not a primary
artifact - same tier as reports/logs, see docs/dev/design_patterns.md).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def append_run_log_entry(
    runs_md_path: Path,
    run_name: str,
    now: datetime,
    run_type: str,
    params_summary: dict,
    output_dir: Path,
    run_notes: str | None,
) -> None:
    """Append one entry to runs_md_path, creating it (with a title) if absent.

    run_type distinguishes a fine-tuning sweep from a production run in the
    same log, without splitting them into separate files - seeing both in
    one chronological history is the point (e.g. "run2 used the params the
    20-07 tuning sweep in this same file found best").
    """
    lines = [f"## {run_name} — {now.strftime('%d-%m-%y %H:%M')} ({run_type})"]
    lines.append(f"Params: {json.dumps(params_summary)}")
    lines.append(f"Output: {output_dir}")
    if run_notes:
        lines.append(f"Note: {run_notes}")
    lines.append("")

    runs_md_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not runs_md_path.is_file()
    with runs_md_path.open("a") as f:
        if is_new:
            f.write(f"# Run history — {runs_md_path.parent.name}\n\n")
        f.write("\n".join(lines) + "\n")
