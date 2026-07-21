"""Standalone, read-only utility: regenerate the 2D scatter plot(s) for an
already-written dim_reduction/dim_reduction_clustering run, without
recomputing the embedding.

matrix.npy in a run directory (written by src.pipeline.dim_reduction or
src.pipeline.dim_reduction_clustering) already holds the final embedding
coordinates - the expensive step (t-SNE/UMAP/PCA fit) never needs to be
redone just because src/analysis/plotting.py's plotting code changed.

Reads matrix.npy + metadata.csv from --run-dir and overwrites the matching
plot file(s) in place: embedding_plot.png + embedding_plot_interactive.html
if metadata has no cluster_label column (a dim_reduction run), cluster_plot.png
+ cluster_plot_interactive.html if it does (a dim_reduction_clustering/
clustering run).

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/replot_dim_reduction.py --run-dir results/dim_reduction/tsne/21-07_tsne_run1
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.analysis.plotting import (
    plot_clusters_2d,
    plot_clusters_interactive,
    plot_embedding_2d,
    plot_embedding_interactive,
)
from src.utils.artifacts import load_matrix

CLUSTER_LABEL_COLUMN = "cluster_label"


def replot(run_dir: Path) -> list[Path]:
    X, metadata, _extra_arrays = load_matrix(run_dir)
    if X.shape[1] < 2:
        raise ValueError(
            f"run {run_dir} has an embedding with {X.shape[1]} component(s) - need at least 2 to plot"
        )

    label_prefix = run_dir.parent.name
    xlabel, ylabel = f"{label_prefix} dim 1", f"{label_prefix} dim 2"
    title = f"{run_dir.name} (replot)"

    if CLUSTER_LABEL_COLUMN in metadata.columns:
        static_cluster_path = run_dir / "cluster_plot.png"
        plot_clusters_2d(X[:, :2], metadata[CLUSTER_LABEL_COLUMN].to_numpy(), static_cluster_path, xlabel, ylabel, title)
        interactive_cluster_path = run_dir / "cluster_plot_interactive.html"
        plot_clusters_interactive(X[:, :2], metadata, interactive_cluster_path, xlabel, ylabel, title)
        return [static_cluster_path, interactive_cluster_path]

    static_path = run_dir / "embedding_plot.png"
    plot_embedding_2d(X[:, :2], static_path, xlabel, ylabel, title)
    interactive_path = run_dir / "embedding_plot_interactive.html"
    plot_embedding_interactive(X[:, :2], metadata, interactive_path, xlabel, ylabel, title)
    return [static_path, interactive_path]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Existing dim_reduction/dim_reduction_clustering output directory")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    try:
        output_paths = replot(run_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}")
        return 1

    for path in output_paths:
        print(f"plot rewritten to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
