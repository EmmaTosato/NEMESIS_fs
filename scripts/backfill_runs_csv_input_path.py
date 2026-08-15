"""One-off script: backfill the `input_path` column into existing `runs.csv`/
`runs_tuning.csv` files written before `src/utils/run_log.py` gained that column
(14-08-26, see `docs/dev/clustering_migration_plan.md` §7 - `append_run_log_entry`
now writes it directly at call time, this script only catches up files written
before that change).

For each row, reads `<output>/config.md`'s own "## Config" fenced JSON block and
extracts its `"input_path"` key - the exact same value `append_run_log_entry`
would have written itself, had this column existed at the time.

Rows are backfilled independently (`lessons_learned.md` #21 - one bad row must
not abort every other, already-resolvable row in the same file, or every other
file). A row whose `output` directory or `config.md` no longer exists on disk
(a real, legitimate case for an old row - e.g. a pre-reorg output path since
renamed, or a manually cleaned-up legacy run, not a bug in this script) gets
`input_path=""` with a loud per-row WARNING - never guessed, never silently
left looking successful. The run's own final summary reports both counts
(backfilled vs. left empty) - never silent either way.

Idempotent: a file that already has an `input_path` column is left untouched
(and reported as skipped), so re-running after a partial run/new production
run is safe.

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/backfill_runs_csv_input_path.py --results-root results
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from pathlib import Path

_CONFIG_JSON_RE = re.compile(r"## Config\n\n```json\n(.*?)\n```", re.DOTALL)


def find_runs_csv_files(results_root: Path) -> list[Path]:
    return sorted(results_root.rglob("runs.csv")) + sorted(results_root.rglob("runs_tuning.csv"))


def extract_input_path(config_md_path: Path) -> str:
    if not config_md_path.is_file():
        raise FileNotFoundError(f"{config_md_path} does not exist - cannot backfill input_path from it")
    text = config_md_path.read_text()
    match = _CONFIG_JSON_RE.search(text)
    if not match:
        raise ValueError(f"{config_md_path} has no '## Config' fenced JSON block - unexpected format")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict) or "input_path" not in payload:
        raise ValueError(f"{config_md_path}'s Config JSON has no 'input_path' key")
    return payload["input_path"]


def backfill_file(csv_path: Path) -> tuple[int, int]:
    """Returns (n_backfilled, n_left_empty). (0, 0) if the file already had the column."""
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if "input_path" in fieldnames:
        logging.info("%s: already has input_path - skipped", csv_path)
        return 0, 0
    if "timestamp" not in fieldnames:
        raise ValueError(f"{csv_path}: no 'timestamp' column - not a runs.csv this script recognizes")

    n_backfilled = 0
    n_empty = 0
    for row in rows:
        output_dir = Path(row["output"])
        try:
            row["input_path"] = extract_input_path(output_dir / "config.md")
            n_backfilled += 1
        except (FileNotFoundError, ValueError) as exc:
            logging.warning("%s: row session=%s id=%s - %s - input_path left empty", csv_path, row.get("session"), row.get("id"), exc)
            row["input_path"] = ""
            n_empty += 1

    insert_at = fieldnames.index("timestamp") + 1
    new_fieldnames = fieldnames[:insert_at] + ["input_path"] + fieldnames[insert_at:]

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logging.info("%s: backfilled %d row(s), left %d empty (see warnings above)", csv_path, n_backfilled, n_empty)
    return n_backfilled, n_empty


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", default="results", help="Root results/ directory to scan (default: results)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    results_root = Path(args.results_root)
    if not results_root.is_dir():
        logging.error("results root %s does not exist", results_root)
        return 1

    csv_files = find_runs_csv_files(results_root)
    if not csv_files:
        logging.info("no runs.csv/runs_tuning.csv found under %s - nothing to backfill", results_root)
        return 0

    total_backfilled = 0
    total_empty = 0
    for csv_path in csv_files:
        try:
            backfilled, empty = backfill_file(csv_path)
        except ValueError as exc:
            logging.error("%s: %s", csv_path, exc)
            return 1
        total_backfilled += backfilled
        total_empty += empty

    logging.info(
        "done - %d file(s) scanned, %d row(s) backfilled, %d row(s) left empty (stale/moved output dirs)",
        len(csv_files), total_backfilled, total_empty,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
