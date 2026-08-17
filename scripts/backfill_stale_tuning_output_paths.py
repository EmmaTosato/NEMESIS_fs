"""One-off script: corrects `output` values in `runs.csv`/`runs_tuning.csv` that still point
at the pre-reorg directory layout (`<method>/tuning/<leaf>`, e.g.
`results/lesion/dim_reduction/tsne/tuning/04-08_s1.1`), left stale after the 2026-08
production/tuning results-layout split (`docs/dev/models.md`) moved the real directories to
`tuning/<method>/<leaf>` (e.g. `results/lesion/dim_reduction/tuning/tsne/04-08_s1.1`) without
also rewriting the `output` column of rows written before the move.

Found 16-08-26 while precision-checking `results/dim_reduction_strategies.csv`
(`scripts/build_dim_reduction_strategies_csv.py`, which skips any row whose `output` doesn't
exist on disk - lessons_learned.md #21): several genuinely-existing tuning runs (e.g. tsne's
04-08_s1.1) were being skipped as "stale" purely because their recorded `output` used the old
segment order, not because the run itself is gone.

Scope, deliberately narrow: this script does **one specific, verifiable** thing per row - if
`output` doesn't exist, try swapping the `<method>/tuning/` segment pair to `tuning/<method>/`
and check whether *that* directory exists. If it does, the row is corrected to the real,
confirmed-on-disk path - never a guess, always checked against the filesystem before writing
anything back. A row whose `output` doesn't match this exact known pattern, or whose swapped
candidate doesn't exist either (e.g. a genuinely deleted/renamed-away run), is left untouched
and logged - this script only reverses this one known historical rename, it does not try to
locate arbitrarily-moved/deleted runs (lessons_learned.md #21 - one unrecoverable row must not
block every other, already-resolvable row).

Idempotent: a row whose `output` already exists (already correct, or already backfilled by a
previous run) is left untouched. A file with nothing to fix is not rewritten at all.

Usage (run from the repo root - `output` values are repo-root-relative, same convention as
scripts/backfill_runs_csv_input_path.py):
    PYTHONPATH=. conda run -n nemesis python scripts/backfill_stale_tuning_output_paths.py --results-root results
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
from pathlib import Path

# Matches only the exact historical layout this script knows how to reverse - "<anything>/
# dim_reduction/<method>/tuning/<leaf>" -> "<anything>/dim_reduction/tuning/<method>/<leaf>".
# Anchored on the literal "dim_reduction" segment (the only pipeline this reorg touched) so it
# never matches an unrelated path shape by accident.
_STALE_LAYOUT_RE = re.compile(r"^(?P<prefix>.*/dim_reduction)/(?P<method>[^/]+)/tuning/(?P<leaf>[^/]+)$")


def find_runs_csv_files(results_root: Path) -> list[Path]:
    return sorted(results_root.rglob("runs.csv")) + sorted(results_root.rglob("runs_tuning.csv"))


def corrected_output(output_value: str) -> str | None:
    """Returns the corrected `output` value if `output_value` doesn't exist but matches the
    known stale layout and its swapped candidate does exist on disk - None if `output_value`
    is already fine (exists as-is) or isn't recoverable this way (no match, or the swapped
    candidate doesn't exist either)."""
    if Path(output_value).is_dir():
        return None
    match = _STALE_LAYOUT_RE.match(output_value)
    if not match:
        return None
    candidate = f"{match.group('prefix')}/tuning/{match.group('method')}/{match.group('leaf')}"
    return candidate if Path(candidate).is_dir() else None


def backfill_file(csv_path: Path) -> tuple[int, int]:
    """Returns (n_corrected, n_still_stale). (0, 0) if every row's `output` already exists."""
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    if "output" not in fieldnames:
        raise ValueError(f"{csv_path}: no 'output' column - not a runs.csv this script recognizes")

    n_corrected = 0
    n_still_stale = 0
    for row in rows:
        if Path(row["output"]).is_dir():
            continue
        fixed = corrected_output(row["output"])
        if fixed is not None:
            logging.info("%s: row session=%s id=%s - %s -> %s", csv_path, row.get("session"), row.get("id"), row["output"], fixed)
            row["output"] = fixed
            n_corrected += 1
        else:
            logging.warning(
                "%s: row session=%s id=%s output=%s not found on disk (not the known stale-layout "
                "pattern, or no matching directory either way) - left as-is", csv_path, row.get("session"), row.get("id"), row["output"],
            )
            n_still_stale += 1

    if n_corrected:
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logging.info("%s: corrected %d row(s), %d still unresolved", csv_path, n_corrected, n_still_stale)
    elif n_still_stale:
        logging.info("%s: %d row(s) unresolved, nothing to correct - file left untouched", csv_path, n_still_stale)
    else:
        logging.info("%s: every row's output already exists - skipped", csv_path)
    return n_corrected, n_still_stale


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

    total_corrected = 0
    total_stale = 0
    for csv_path in csv_files:
        try:
            corrected, stale = backfill_file(csv_path)
        except ValueError as exc:
            logging.error("%s: %s", csv_path, exc)
            return 1
        total_corrected += corrected
        total_stale += stale

    logging.info(
        "done - %d file(s) scanned, %d row(s) corrected, %d row(s) still unresolved (genuinely gone, or a different issue)",
        len(csv_files), total_corrected, total_stale,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
