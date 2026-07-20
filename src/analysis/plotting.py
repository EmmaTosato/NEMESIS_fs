"""Minimal plotting for the modeling pipeline scripts - a first look at cluster separation.

Not a general visualization module: one function, one plot kind. Richer
plots (per-dataset coloring, interactive, more than 2 dimensions) were
explicitly deferred in the analysis pipeline v2 handoff - this exists only
because seeing clusters on a 2D scatter is the minimum needed to sanity-check
a clustering run before looking at anything else.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_clusters_2d(
    X_2d: np.ndarray, cluster_labels: np.ndarray, output_path: Path, xlabel: str, ylabel: str, title: str
) -> None:
    """Scatter the first 2 columns of X_2d, colored by cluster_labels, to output_path.

    Callers pass whatever 2D array is actually meaningful for their case
    (a dimensionality-reduction embedding, or raw features when there's no
    reduction) - this function has no opinion on where X_2d came from.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_2d needs at least 2 columns, got shape {X_2d.shape}")

    fig, ax = plt.subplots(figsize=(6, 5))
    scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=cluster_labels, cmap="tab10", s=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    legend = ax.legend(*scatter.legend_elements(), title="cluster", loc="best")
    ax.add_artist(legend)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
