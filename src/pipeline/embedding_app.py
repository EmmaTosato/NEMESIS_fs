"""CLI entry point: launch the interactive embedding-explorer Dash app - a live, local-only
replacement for the old per-run embedding_plot_interactive.html (removed 2026-08-14, see
src/analysis/plotting.py's module docstring). Discovers every dim_reduction.py AND clustering.py
production run under --results-root (src.analysis.embedding_app.PRODUCTION_PIPELINES, extended
15-08-26 to cover clustering.py too - docs/dev/clustering_migration_plan.md §3), lets a human
pick one from a dropdown and a color mode from a button group, and renders it as an interactive
2D or 3D Plotly scatter - see docs/guides/embedding_app.md.

Local dev tool, never sbatch (same reasoning as
src.pipeline.run_understanding_umap_dash: an interactive app with no batch-job shape has
nothing for SLURM to do - it just needs a browser pointed at whichever machine runs this).

Usage:
    conda activate nemesis
    python -m src.pipeline.embedding_app

Then open http://127.0.0.1:8060 in a browser. --results-root defaults to "results" (relative
to wherever this is run from - run it from the repo root, same as every other src/pipeline/
entry point).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.analysis.embedding_app import build_app, discover_production_runs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", default="results", help="Root results/ directory to scan (default: results)")
    # 8060, not Dash's own default 8050 - src.pipeline.run_understanding_umap_dash already
    # binds 8050 by default, and the two apps are meant to run side by side (one explores
    # production runs, the other explores tuning sweeps - see src/analysis/embedding_app.py's
    # module docstring for why they're separate tools), not fight over the same port.
    parser.add_argument("--port", type=int, default=8060, help="Local port to serve on (default: 8060)")
    parser.add_argument("--debug", action="store_true", help="Enable Dash's debug mode (auto-reload, in-browser error overlay)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    runs = discover_production_runs(Path(args.results_root))
    if not runs:
        logging.error(
            "no production runs found under %s/*/{dim_reduction,clustering}/production/*/* - "
            "run a pipeline in production mode first (e.g. python -m src.pipeline.dim_reduction, "
            "fine_tuning: false)",
            args.results_root,
        )
        return 1

    try:
        app = build_app(runs)
    except ValueError as exc:
        logging.error(str(exc))
        return 1

    logging.info("serving %d run(s) on http://127.0.0.1:%d - Ctrl+C to stop", len(runs), args.port)
    app.run(debug=args.debug, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
