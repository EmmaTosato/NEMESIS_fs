"""Standalone, read-only utility: regenerate the 2D scatter plot(s) for an
already-written dim_reduction/dim_reduction_clustering run, without
recomputing the embedding.

matrix.npy in a run directory (written by src.pipeline.dim_reduction or
src.pipeline.dim_reduction_clustering) already holds the final embedding
coordinates - the expensive step (t-SNE/UMAP/PCA fit) never needs to be
redone just because src/analysis/plotting.py's plotting code changed.

Reads matrix.npy + metadata.csv from --run-dir and overwrites the matching
plot file(s) in place. Only works for a run whose saved embedding has exactly
2 components - it deliberately never reloads the original feature matrix, so
unlike dim_reduction.py/dim_reduction_clustering.py it has no way to refit a
lower-dimensional visualization projection when a run's own n_components is
above its viz_n_components (see src/analysis/reduction.py::embedding_for_viz);
raises ValueError for any other component count, rerun the original pipeline
instead.
- dim_reduction run (metadata has no cluster_label column): embedding_plot_unico.png
  + one embedding_plot_<name>.png per src.analysis.embedding_coloring.COLOR_MODES
  entry whose backing column is present in this run's metadata.csv (today:
  dataset/side/volume/nihss - see embedding_coloring.PERSISTED_COLUMN_BY_MODE for
  the mode-name -> column mapping). No interactive HTML here anymore (2026-08-14,
  on request) - superseded by the live src.pipeline.embedding_app (any production
  run, any color mode, no static file to regenerate per run - see
  docs/guides/embedding_app.md). Every static PNG value is read directly from
  metadata.csv (persisted there by dim_reduction.py's
  _run_production/enrich_metadata_with_lesion_info) - never recomputed from the
  original feature matrix nor rejoined from assets/metadata/participants.tsv. A
  mode whose column this run's metadata.csv predates (e.g. an old run before
  "nihss" existed) is skipped with a WARNING, not silently omitted.
- dim_reduction_clustering run (metadata has cluster_label): cluster_plot.png
  + cluster_plot_interactive.html (2 files, cluster-colored only - no dataset
  coloring here, see plotting.py's plot_clusters_interactive).

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/replot_dim_reduction.py --run-dir results/lesion/dim_reduction/umap/21-07_s1_d01
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.embedding_coloring import COLOR_MODES, PERSISTED_COLUMN_BY_MODE
from src.analysis.plotting import (
    compose_cluster_plot_title,
    compose_embedding_plot_title,
    plot_clusters_2d,
    plot_clusters_interactive,
    plot_embedding_2d,
    plot_embedding_categorical,
    plot_embedding_continuous,
)
from src.utils.artifacts import load_matrix

CLUSTER_LABEL_COLUMN = "cluster_label"


def replot(run_dir: Path) -> list[Path]:
    X, metadata, _extra_arrays = load_matrix(run_dir)
    if X.shape[1] != 2:
        raise ValueError(
            f"run {run_dir} has a saved embedding with {X.shape[1]} component(s) - this script can only replot an "
            "already-2-component embedding: it deliberately avoids reloading the original feature matrix, so it has "
            "no way to refit a lower-dimensional visualization projection the way dim_reduction.py/"
            "dim_reduction_clustering.py do (see src/analysis/reduction.py::embedding_for_viz). Rerun the original "
            "pipeline instead if this run's saved embedding has more components than its own viz_n_components."
        )

    if CLUSTER_LABEL_COLUMN in metadata.columns:
        return _replot_clustering(run_dir, X, metadata)
    return _replot_embedding(run_dir, X, metadata)


def _replot_clustering(run_dir: Path, X: np.ndarray, metadata: pd.DataFrame) -> list[Path]:
    # <output_root>/production/<reduction_method>/<clustering_method>/<dd-mm>_<tag> - only the 2
    # levels immediately above run_dir matter here (clustering_method, then reduction_method);
    # whatever sits above that (production/, or nothing, pre-2026-08) is never inspected.
    reduction_method = run_dir.parent.parent.name
    clustering_method = run_dir.parent.name
    xlabel, ylabel = f"{reduction_method} dim 1", f"{reduction_method} dim 2"
    title = compose_cluster_plot_title(run_dir, reduction_method, clustering_method)

    static_path = run_dir / "cluster_plot.png"
    plot_clusters_2d(X, metadata[CLUSTER_LABEL_COLUMN].to_numpy(), static_path, xlabel, ylabel, title)
    interactive_path = run_dir / "cluster_plot_interactive.html"
    plot_clusters_interactive(X, metadata, interactive_path, xlabel, ylabel, title)
    return [static_path, interactive_path]


def _replot_embedding(run_dir: Path, X: np.ndarray, metadata: pd.DataFrame) -> list[Path]:
    if "dataset" not in metadata.columns:
        raise ValueError(
            f"run {run_dir}: metadata.csv has no 'dataset' column - this predates every embedding-plot schema "
            "this script knows about; rerun src.pipeline.dim_reduction to regenerate it"
        )

    # <output_root>/production/<reduction_method>/<dd-mm>_<tag> - only the 1 level immediately
    # above run_dir matters here; whatever sits above that is never inspected.
    reduction_method = run_dir.parent.name
    xlabel, ylabel = f"{reduction_method} dim 1", f"{reduction_method} dim 2"
    output_paths = []

    static_path = run_dir / "embedding_plot_unico.png"
    plot_embedding_2d(X, static_path, xlabel, ylabel, compose_embedding_plot_title(run_dir, reduction_method))
    output_paths.append(static_path)

    for name, mode in COLOR_MODES.items():
        column = PERSISTED_COLUMN_BY_MODE.get(name)
        if column is None or column not in metadata.columns:
            logging.warning(
                "run %s: metadata.csv has no %r column for color_by mode %r - skipping this plot "
                "(rerun src.pipeline.dim_reduction to add it)",
                run_dir, column, name,
            )
            continue

        values = metadata[column].to_numpy()
        title = compose_embedding_plot_title(run_dir, reduction_method, mode.label)

        static_path = run_dir / f"embedding_plot_{name}.png"
        if mode.kind == "categorical":
            plot_embedding_categorical(X, values, static_path, xlabel, ylabel, title, legend_title=mode.label)
        else:
            plot_embedding_continuous(
                X, values, static_path, xlabel, ylabel, title,
                colorbar_label=mode.label, log_scale=mode.log_scale,
            )
        output_paths.append(static_path)

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
