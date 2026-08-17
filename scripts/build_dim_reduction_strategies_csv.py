"""Generates results/dim_reduction_strategies.csv - a one-glance index of every
(session, reduction_method, metric, n_components) combination dim_reduction.py has ever
produced, so a human can see "what already exists" without opening N runs.csv files by hand
(docs/dev/clustering_migration_plan.md §6).

Read-only, regenerated in full on every run - not append-only like runs.csv itself. This file
is a derived index, always safe to throw away and rebuild from the runs.csv/runs_tuning.csv
files that remain the actual source of truth (never hand-edit it - lessons_learned.md #18, a
hand-maintained summary drifts from what's really on disk).

Two sources, joined on session:
- results/<modality>/dim_reduction/{production,tuning}/<reduction_method>/runs*.csv - one row
  per real run; modality/reduction_method read from the file's own path, metric/n_components
  parsed from that row's own `params` JSON column.
- docs/experiments/SESSIONS.md - hand-written narrative (datasets/modality) per session, keyed
  by the same session id runs.csv uses in its own "session" column (e.g. "s1.1").

Deliberately no per-row output path column (no "latest_output", decided in session 14-08-26)
and no run-count columns either (production_runs/tuning_runs dropped 16-08-26, on request):
for the exact path of a specific run, or how many times a combination was run, go to that
method's own runs.csv - this file stays a plain existence index ("does this combination
exist at all"), not a shortcut to individual results or their history.

A runs.csv row's own `output` directory is checked against disk before being counted as
existing (`_output_dir_exists`) - results/ is gitignored and gets reorganized/pruned over
time, so a stale row (e.g. a pre-reorg run whose folder is long gone) doesn't silently make
this index claim a combination still exists when it doesn't (see 16-08-26 fix: the very first
real run against this script reported a "no metric" umap/2 strategy that traced back to
exactly this - a 23-07 run whose output directory no longer exists).

Scope (deliberate, see plan §6's own "Dipendenza" note): only dim_reduction.py's own runs.csv/
runs_tuning.csv today, not clustering.py's `reduced_data=true` branch (which would need
resolving each clustering run's own `input_path` back to the dim_reduction run that produced
it, via the `input_path` column - a real join, not yet implemented here; deferred, not a gap
this script's own schema forecloses).

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/build_dim_reduction_strategies_csv.py --results-root results
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

_SESSION_HEADER_RE = re.compile(r"^## Session (\S+)\s*$")
_SESSION_FIELD_RE = re.compile(r"^- (Starting date|Datasets|Modality):\s*(.*)$")
_REQUIRED_SESSION_FIELDS = ("Starting date", "Datasets", "Modality")

# runs.csv's own "session" column always starts with a lowercase "s" followed by the session
# number SESSIONS.md documents under "## Session <number>" (e.g. runs.csv "s1.1" <-> SESSIONS.md
# "## Session 1.1") - see src/utils/run_log.py's append_run_log_entry, which splits run_id on
# its first "_" to get this value. Anything not matching this convention is a real problem
# (typo'd session_name, or a naming convention this script doesn't know about yet) worth
# surfacing, not guessing past.
_RUNS_CSV_SESSION_RE = re.compile(r"^s(\S.*)$")

# A row whose method has no 'metric' key in its own params (pca/pacmap) - distinct from any
# real metric string, same sentinel convention as src.analysis.embedding_app.NO_METRIC (not
# imported directly - that module pulls in dash, a heavy/optional dependency this read-only
# reporting script has no other reason to need).
NO_METRIC = "—"

OUTPUT_COLUMNS = ["session", "modality", "datasets", "reduction_method", "metric", "n_components"]


@dataclass(frozen=True)
class SessionInfo:
    session_id: str
    starting_date: str
    datasets: str
    modality: str


def parse_sessions_md(path: Path) -> dict[str, SessionInfo]:
    """Parses docs/experiments/SESSIONS.md's fixed-key format (`## Session <id>` header,
    `- Starting date:`/`- Datasets:`/`- Modality:` fields) into {session_id: SessionInfo}.

    Raises ValueError for a session missing any of the 3 required fields, a duplicate session
    id (lessons_learned.md #5), or a field line appearing before any session header - a
    malformed SESSIONS.md should stop this script loudly, not silently produce a half-joined
    table.
    """
    if not path.is_file():
        raise FileNotFoundError(f"{path} does not exist - cannot join session metadata")

    sessions: dict[str, SessionInfo] = {}
    current_id: str | None = None
    fields: dict[str, str] = {}

    def _flush_current_session() -> None:
        if current_id is None:
            return
        missing = [name for name in _REQUIRED_SESSION_FIELDS if name not in fields]
        if missing:
            raise ValueError(f"{path}: session {current_id!r} is missing field(s) {missing}")
        if current_id in sessions:
            raise ValueError(f"{path}: session {current_id!r} is documented more than once")
        sessions[current_id] = SessionInfo(
            session_id=current_id, starting_date=fields["Starting date"], datasets=fields["Datasets"], modality=fields["Modality"]
        )

    for line in path.read_text().splitlines():
        header_match = _SESSION_HEADER_RE.match(line)
        if header_match:
            _flush_current_session()
            current_id, fields = header_match.group(1), {}
            continue
        field_match = _SESSION_FIELD_RE.match(line)
        if field_match:
            if current_id is None:
                raise ValueError(f"{path}: field line {line!r} appears before any '## Session' header")
            fields[field_match.group(1)] = field_match.group(2).strip()
    _flush_current_session()
    return sessions


def _session_lookup_key(runs_csv_session: str) -> str:
    match = _RUNS_CSV_SESSION_RE.match(runs_csv_session)
    if not match:
        raise ValueError(
            f"runs.csv session id {runs_csv_session!r} doesn't match the expected 's<number>' "
            "convention (e.g. 's1.1') - cannot look it up in SESSIONS.md"
        )
    return match.group(1)


@dataclass(frozen=True)
class StrategyKey:
    session: str
    reduction_method: str
    metric: str
    n_components: int


def _output_dir_exists(output_value: str, results_root: Path) -> bool:
    """runs.csv's own `output` column is always a repo-root-relative path starting with
    "results/" (every pipeline writes it via `Path("results") / ...` - same convention
    src.analysis.embedding_app.ProductionRun.results_relative_path relies on) - resolved
    against results_root's own *parent* (the repo root), not results_root itself, since
    `output` already includes the "results/" segment.

    results/ is gitignored and reorganized/pruned over time (docs/dev/clustering_migration_plan.md
    §7 already documented one such gap) - a runs.csv row can outlive the directory it points to.
    Raises ValueError if `output_value` doesn't start with "results/" - a row that doesn't
    follow this repo-wide convention is a real problem worth surfacing, not a case to guess
    past.
    """
    if not output_value.startswith("results/"):
        raise ValueError(f"runs.csv output {output_value!r} doesn't start with 'results/' - unexpected format, cannot resolve it")
    return (results_root.parent / output_value).is_dir()


def _extract_metric_and_n_components(params: dict, run_type: str) -> tuple[str, int]:
    """Production rows: `params` is the resolved single-run hyperparameter dict, read
    directly. Tuning rows: `params` is `{"base_params": {...}, "tuning_grid": {...}}` (see
    dim_reduction.py's fine-tuning append_run_log_entry call) - metric/n_components are read
    from base_params, the sweep's fixed starting point. If either is itself one of
    tuning_grid's swept axes, this reports only that starting value, not every combination the
    sweep actually tried - this file is an index (clustering_migration_plan.md §6), not a
    substitute for that run's own tuning_results.csv.
    """
    source = params["base_params"] if run_type == "tuning" else params
    return source.get("metric", NO_METRIC), source["n_components"]


def _reduction_run_files(results_root: Path) -> list[tuple[Path, str, str]]:
    """(csv_path, run_type, reduction_method) for every dim_reduction.py runs.csv/
    runs_tuning.csv under results_root - reduction_method read from the file's own path
    (results_root/<modality>/dim_reduction/{production,tuning}/<reduction_method>/...), never
    from its content."""
    found = []
    for csv_path in sorted(results_root.glob("*/dim_reduction/production/*/runs.csv")):
        reduction_method = csv_path.relative_to(results_root).parts[3]
        found.append((csv_path, "production", reduction_method))
    for csv_path in sorted(results_root.glob("*/dim_reduction/tuning/*/runs_tuning.csv")):
        reduction_method = csv_path.relative_to(results_root).parts[3]
        found.append((csv_path, "tuning", reduction_method))
    return found


def _collect_strategy_keys(results_root: Path) -> set[StrategyKey]:
    """Every distinct (session, reduction_method, metric, n_components) combination seen across
    every runs.csv/runs_tuning.csv found under results_root - a combination that only ever
    showed up in tuning (still being explored, never promoted to production) or only in
    production is included either way; this index only answers "does it exist", not "how many
    times"/"in which of the two branches" (see module docstring - deliberately dropped
    16-08-26, on request).

    A row whose own `output` directory no longer exists on disk (results/ is gitignored and
    gets reorganized/pruned over time - see _output_dir_exists) is skipped, not counted as
    existing - logged once per skipped row (lessons_learned.md #21, one stale row shouldn't
    silently misrepresent this index as more complete than what's actually still on disk).
    """
    keys: set[StrategyKey] = set()
    for csv_path, run_type, reduction_method in _reduction_run_files(results_root):
        with csv_path.open(newline="") as f:
            for row in csv.DictReader(f):
                if not _output_dir_exists(row["output"], results_root):
                    logging.warning(
                        "%s: row session=%s output=%s no longer exists on disk - skipping stale entry",
                        csv_path, row["session"], row["output"],
                    )
                    continue
                params = json.loads(row["params"])
                metric, n_components = _extract_metric_and_n_components(params, run_type)
                keys.add(StrategyKey(session=row["session"], reduction_method=reduction_method, metric=metric, n_components=n_components))
    return keys


def build_strategies_table(results_root: Path, sessions_md_path: Path) -> pd.DataFrame:
    """Builds the full results/dim_reduction_strategies.csv table: one row per distinct
    (session, reduction_method, metric, n_components) combination actually run, with
    modality/datasets joined in from SESSIONS.md.

    A session referenced by a runs.csv row but undocumented in SESSIONS.md doesn't abort the
    whole table (lessons_learned.md #21 - one bad/missing item shouldn't hide every other,
    already-resolvable row) - its modality/datasets columns get an explicit "undocumented"
    placeholder and the gap is logged loudly, never silently blanked.
    """
    sessions = parse_sessions_md(sessions_md_path)
    keys = _collect_strategy_keys(results_root)

    rows = []
    for key in sorted(keys, key=lambda k: (k.session, k.reduction_method, k.metric, k.n_components)):
        session_info = sessions.get(_session_lookup_key(key.session))
        if session_info is None:
            logging.warning(
                "session %r has runs.csv rows but no entry in %s - modality/datasets left as 'undocumented'",
                key.session, sessions_md_path,
            )
        rows.append(
            {
                "session": key.session,
                "modality": session_info.modality if session_info else "undocumented",
                "datasets": session_info.datasets if session_info else "undocumented",
                "reduction_method": key.reduction_method,
                "metric": key.metric,
                "n_components": key.n_components,
            }
        )
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", default="results", help="Root results/ directory to scan (default: results)")
    parser.add_argument(
        "--sessions-md", default="docs/experiments/SESSIONS.md", help="Path to SESSIONS.md (default: docs/experiments/SESSIONS.md)"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    results_root = Path(args.results_root)
    try:
        table = build_strategies_table(results_root, Path(args.sessions_md))
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    output_path = results_root / "dim_reduction_strategies.csv"
    table.to_csv(output_path, index=False)
    logging.info("%d strategy row(s) written to %s", len(table), output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
