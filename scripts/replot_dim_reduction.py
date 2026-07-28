"""Standalone, read-only utility: regenerate the 2D scatter plot(s) for an
already-written dim_reduction/dim_reduction_clustering run, without
recomputing the embedding.

matrix.npy in a run directory (written by src.pipeline.dim_reduction or
src.pipeline.dim_reduction_clustering) already holds the final embedding
coordinates - the expensive step (t-SNE/UMAP/PCA fit) never needs to be
redone just because src/analysis/plotting.py's plotting code changed.

Reads matrix.npy + metadata.csv from --run-dir and overwrites the matching
plot file(s) in place:
- dim_reduction run (metadata has no cluster_label column): embedding_plot.png
  + embedding_plot_{dataset,volume,side}.png/.html (7 files total). dataset/
  lesion_volume_voxels/lesion_side are read directly from metadata.csv (persisted
  there by dim_reduction.py's _run_production) - never recomputed from the
  original feature matrix nor rejoined from assets/metadata. Raises ValueError
  if metadata.csv predates those columns (rerun dim_reduction.py instead of
  guessing at a fallback).
- dim_reduction_clustering run (metadata has cluster_label): cluster_plot.png
  + cluster_plot_interactive.html (2 files, cluster-colored only - no dataset
  coloring here, see plotting.py's plot_clusters_interactive).

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/replot_dim_reduction.py --run-dir results/lesion/dim_reduction/umap/21-07_s1_d01
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.plotting import (
    compose_cluster_plot_title,
    compose_embedding_plot_title,
    plot_clusters_2d,
    plot_clusters_interactive,
    plot_embedding_2d,
    plot_embedding_categorical,
    plot_embedding_continuous,
    plot_embedding_interactive,
)
from src.utils.artifacts import load_matrix

CLUSTER_LABEL_COLUMN = "cluster_label"
_REQUIRED_EMBEDDING_COLUMNS = ("dataset", "lesion_volume_voxels", "lesion_side")


def replot(run_dir: Path) -> list[Path]:
    X, metadata, _extra_arrays = load_matrix(run_dir)
    if X.shape[1] < 2:
        raise ValueError(
            f"run {run_dir} has an embedding with {X.shape[1]} component(s) - need at least 2 to plot"
        )

    if CLUSTER_LABEL_COLUMN in metadata.columns:
        return _replot_clustering(run_dir, X, metadata)
    return _replot_embedding(run_dir, X, metadata)


def _replot_clustering(run_dir: Path, X: np.ndarray, metadata: pd.DataFrame) -> list[Path]:
    # <output_root>/<reduction_method>/<clustering_method>/<dd-mm>_<tag>
    reduction_method = run_dir.parent.parent.name
    clustering_method = run_dir.parent.name
    xlabel, ylabel = f"{reduction_method} dim 1", f"{reduction_method} dim 2"
    title = compose_cluster_plot_title(run_dir, reduction_method, clustering_method)

    static_path = run_dir / "cluster_plot.png"
    plot_clusters_2d(X[:, :2], metadata[CLUSTER_LABEL_COLUMN].to_numpy(), static_path, xlabel, ylabel, title)
    interactive_path = run_dir / "cluster_plot_interactive.html"
    plot_clusters_interactive(X[:, :2], metadata, interactive_path, xlabel, ylabel, title)
    return [static_path, interactive_path]


def _replot_embedding(run_dir: Path, X: np.ndarray, metadata: pd.DataFrame) -> list[Path]:
    missing_columns = [c for c in _REQUIRED_EMBEDDING_COLUMNS if c not in metadata.columns]
    if missing_columns:
        raise ValueError(
            f"run {run_dir}: metadata.csv is missing {missing_columns} - this run predates the "
            "Dataset/Volume/Side plots; rerun src.pipeline.dim_reduction to regenerate it with the current schema"
        )

    # <output_root>/<reduction_method>/<dd-mm>_<tag>
    reduction_method = run_dir.parent.name
    xlabel, ylabel = f"{reduction_method} dim 1", f"{reduction_method} dim 2"
    output_paths = []

    static_path = run_dir / "embedding_plot.png"
    plot_embedding_2d(X[:, :2], static_path, xlabel, ylabel, compose_embedding_plot_title(run_dir, reduction_method))
    output_paths.append(static_path)

    for color_by, column in (("Dataset", "dataset"), ("Side", "lesion_side")):
        suffix = column.replace("lesion_", "")
        title = compose_embedding_plot_title(run_dir, reduction_method, color_by)

        static_path = run_dir / f"embedding_plot_{suffix}.png"
        plot_embedding_categorical(X[:, :2], metadata[column].to_numpy(), static_path, xlabel, ylabel, title, legend_title=column)
        output_paths.append(static_path)

        interactive_path = run_dir / f"embedding_plot_{suffix}.html"
        plot_embedding_interactive(X[:, :2], metadata, interactive_path, xlabel, ylabel, title, color_column=column)
        output_paths.append(interactive_path)

    volume_title = compose_embedding_plot_title(run_dir, reduction_method, "Volume")
    static_path = run_dir / "embedding_plot_volume.png"
    plot_embedding_continuous(
        X[:, :2], metadata["lesion_volume_voxels"].to_numpy(), static_path, xlabel, ylabel, volume_title,
        colorbar_label="lesion volume (voxels)",
    )
    output_paths.append(static_path)

    interactive_path = run_dir / "embedding_plot_volume.html"
    plot_embedding_interactive(
        X[:, :2], metadata, interactive_path, xlabel, ylabel, volume_title, color_column="lesion_volume_voxels"
    )
    output_paths.append(interactive_path)

    return output_paths


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
