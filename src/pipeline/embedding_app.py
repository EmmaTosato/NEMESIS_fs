"""CLI entry point: launch the interactive embedding-explorer Dash app - a live, local-only
replacement for the old per-run embedding_plot_interactive.html (removed 2026-08-14, see
src/analysis/plotting.py's module docstring). Discovers every dim_reduction.py AND clustering.py
production run under --results-root (src.analysis.embedding_app.PRODUCTION_PIPELINES, extended
15-08-26 to cover clustering.py too - docs/dev/clustering_migration_plan.md §3), lets a human
pick one from a dropdown and a color mode from a button group, and renders it as an interactive
2D or 3D Plotly scatter - see docs/guides/embedding_app.md. Extended 01-09-26 with two anatomy
panels (single-subject lesion viewer, per-cluster overlap map) backed by --lesion-config.

Local dev tool, never sbatch - an interactive app with no batch-job shape has nothing for
SLURM to do, it just needs a browser pointed at whichever machine runs this.

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

from src.analysis.build_config import load_build_matrix_config
from src.analysis.embedding_app import LesionViewerConfig, build_app, discover_production_runs
from src.features.lesion import load_reference_image


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", default="results", help="Root results/ directory to scan (default: results)")
    parser.add_argument(
        "--lesion-config",
        default="config/pipelines/build_lesion_matrix.json",
        help="build_lesion_matrix.json-shaped config backing the anatomy panels "
        "(data_root/lesion_glob/reference_template_path/binarize_threshold/resample_interpolation) "
        "(default: config/pipelines/build_lesion_matrix.json)",
    )
    parser.add_argument(
        "--clustering-params-file",
        default="config/registry/params_clustering.json",
        help="params_clustering.json-shaped registry backing the picker's clustering-pipeline "
        "'Parametri' step (each method's own tag_param list) (default: config/registry/params_clustering.json)",
    )
    # 8060, not Dash's own default 8050 - deliberately non-default so this app doesn't collide
    # with another local Dash instance a developer might already have running on 8050.
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

    # Reuses build_lesion_matrix.py's own config loader/validation (single source of truth) -
    # fails fast (FileNotFoundError/ValueError) if the config or its reference template is
    # missing, same as build_lesion_matrix.py itself would, rather than deferring the failure
    # to the first click on a point (code_standards.md §0).
    lesion_matrix_config = load_build_matrix_config(args.lesion_config)
    reference_img = load_reference_image(lesion_matrix_config.reference_template_path)
    lesion_cfg = LesionViewerConfig(
        data_root=lesion_matrix_config.data_root,
        lesion_glob=lesion_matrix_config.lesion_glob,
        reference_img=reference_img,
        binarize_threshold=lesion_matrix_config.binarize_threshold,
        resample_interpolation=lesion_matrix_config.resample_interpolation,
    )

    try:
        app = build_app(runs, lesion_cfg, args.clustering_params_file)
    except ValueError as exc:
        logging.error(str(exc))
        return 1

    logging.info("serving %d run(s) on http://127.0.0.1:%d - Ctrl+C to stop", len(runs), args.port)
    try:
        # AUDIT_FINDINGS.md #45: OSError (e.g. "Address already in use" from a
        # leftover instance on the same --port) used to propagate as a raw traceback.
        # KeyboardInterrupt (Ctrl+C, this app's own documented stop mechanism, logged
        # above) is deliberately NOT caught here - that's a normal, clean shutdown, not
        # a failure to report.
        app.run(debug=args.debug, port=args.port)
    except OSError as exc:
        logging.error("cannot start the server on port %d: %s", args.port, exc, exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
