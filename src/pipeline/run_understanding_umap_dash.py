"""CLI entry point: launch the interactive Dash version of the Understanding
UMAP report - local-only dev tool, never sbatch (an interactive app has no
batch-job shape; keep using
src.pipeline.generate_understanding_umap_report for the pipeline's own
publishable artifact).

Usage:
    PYTHONPATH=. conda run -n nemesis python -m src.pipeline.run_understanding_umap_dash \\
        --umap-tuning-dir results/lesion/dim_reduction/tuning/umap/13-08_s1.1 \\
        --tsne-tuning-dir results/lesion/dim_reduction/tuning/tsne/13-08_s1.1

Then open http://127.0.0.1:8050 in a browser. Same cohort-validation rules
as generate_understanding_umap_report (see
src.analysis.understanding_umap_report.load_tuning_data) - both share the
exact same loader, so a directory that's rejected by one is rejected by the
other for the same reason.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.analysis.understanding_umap_dash import build_app
from src.analysis.understanding_umap_report import load_tuning_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--umap-tuning-dir", required=True, help="UMAP tuning output (nested_params=[metric, n_components])")
    parser.add_argument("--tsne-tuning-dir", required=True, help="t-SNE tuning output (nested_params=[metric])")
    parser.add_argument("--port", type=int, default=8050, help="Local port to serve on (default: 8050)")
    parser.add_argument("--debug", action="store_true", help="Enable Dash's debug mode (auto-reload, in-browser error overlay)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        data = load_tuning_data(Path(args.umap_tuning_dir), Path(args.tsne_tuning_dir))
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    logging.info("serving %d metric(s) on http://127.0.0.1:%d - Ctrl+C to stop", len(data.metrics), args.port)
    app = build_app(data)
    app.run(debug=args.debug, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
