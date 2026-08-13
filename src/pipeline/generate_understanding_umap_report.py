"""CLI entry point: build an "Understanding UMAP" style HTML report from
already-computed UMAP and t-SNE tuning output - no refit, read-only, same
convention as scripts/replot_dim_reduction.py.

Usage:
    PYTHONPATH=. conda run -n nemesis python -m src.pipeline.generate_understanding_umap_report \\
        --umap-tuning-dir results/lesion/dim_reduction/tuning/umap/13-08_s1.1 \\
        --tsne-tuning-dir results/lesion/dim_reduction/tuning/tsne/13-08_s1.1

Both directories must be `fine_tuning=true` output from src.pipeline.dim_reduction
with save_tuning_embeddings=true (so embeddings.npz exists, not just
tuning_results.csv) - the UMAP one nested on ["metric", "n_components"], the
t-SNE one on ["metric"] alone. The two must share the same subject cohort in
the same row order (checked once, for both metrics, before any file is
written - see src.analysis.understanding_umap_report.generate_report).

Writes one understanding_umap_<metric>.html per metric leaf directly into
--umap-tuning-dir (no separate report directory - the report belongs next to
the tuning run it was built from, same principle as embeddings_grid_*.png
already living inside each leaf).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.analysis.understanding_umap_report import generate_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--umap-tuning-dir", required=True, help="UMAP tuning output (nested_params=[metric, n_components])")
    parser.add_argument("--tsne-tuning-dir", required=True, help="t-SNE tuning output (nested_params=[metric])")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    umap_tuning_dir = Path(args.umap_tuning_dir)
    tsne_tuning_dir = Path(args.tsne_tuning_dir)
    try:
        output_paths = generate_report(umap_tuning_dir, tsne_tuning_dir, output_dir=umap_tuning_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    for path in output_paths:
        logging.info("report written: %s", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
