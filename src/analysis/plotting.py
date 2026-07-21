"""Minimal plotting for the modeling pipeline scripts - cluster separation and fine-tuning sweeps.

Not a general visualization module: a handful of narrow-purpose functions.
Richer plots (per-dataset coloring, interactive, more than 2 dimensions) were
explicitly deferred in the analysis pipeline v2 handoff - plot_clusters_2d
exists only because seeing clusters on a 2D scatter is the minimum needed to
sanity-check a clustering run; plot_tuning_curve/plot_tuning_heatmap exist
because a human has to eyeball a fine-tuning sweep to pick parameters by hand
(src/analysis/tuning.py) - no automatic selection.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_embedding_2d(
    X_2d: np.ndarray, output_path: Path, xlabel: str, ylabel: str, title: str
) -> None:
    """Scatter the first 2 columns of X_2d (no color labels), to output_path."""
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_embedding_2d needs at least 2 columns, got shape {X_2d.shape}")

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(X_2d[:, 0], X_2d[:, 1], alpha=0.5, s=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


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


def plot_clusters_comparison(
    X_2d: np.ndarray,
    labels_by_method: dict[str, np.ndarray],
    output_path: Path,
    xlabel: str,
    ylabel: str,
    suptitle: str,
) -> None:
    """Grid of subplots, one per method, same X_2d, colored by that method's own cluster_labels.

    Shared x/y limits across every subplot so the comparison is visually
    honest - a method that spreads points wider isn't allowed to look more
    "spread out" just because matplotlib auto-scaled its own axes differently.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_comparison needs at least 2 columns, got shape {X_2d.shape}")
    if not labels_by_method:
        raise ValueError("plot_clusters_comparison needs at least one method in labels_by_method")

    methods = list(labels_by_method)
    ncols = min(3, len(methods))
    nrows = -(-len(methods) // ncols)  # ceil division
    xlim = (X_2d[:, 0].min(), X_2d[:, 0].max())
    ylim = (X_2d[:, 1].min(), X_2d[:, 1].max())

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows), squeeze=False)
    for i, method in enumerate(methods):
        ax = axes[i // ncols][i % ncols]
        scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=labels_by_method[method], cmap="tab10", s=12)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(method)
        legend = ax.legend(*scatter.legend_elements(), title="cluster", loc="best", fontsize="small")
        ax.add_artist(legend)
    for i in range(len(methods), nrows * ncols):
        axes[i // ncols][i % ncols].set_visible(False)
    fig.suptitle(suptitle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tuning_curve(df: pd.DataFrame, param_col: str, metric_col: str, output_path: Path, title: str) -> None:
    """Line plot: one swept hyperparameter vs. the tuning metric (e.g. PCA's n_components sweep)."""
    sorted_df = df.sort_values(param_col)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(sorted_df[param_col], sorted_df[metric_col], marker="o")
    ax.set_xlabel(param_col)
    ax.set_ylabel(metric_col)
    ax.set_title(title)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tuning_heatmap(
    df: pd.DataFrame, param_x: str, param_y: str, metric_col: str, output_path: Path, title: str
) -> None:
    """Heatmap: two swept hyperparameters vs. the tuning metric (e.g. UMAP's n_neighbors x min_dist grid)."""
    pivot = df.pivot(index=param_y, columns=param_x, values=metric_col)

    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(pivot.values, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel(param_x)
    ax.set_ylabel(param_y)
    ax.set_title(title)
    fig.colorbar(image, ax=ax, label=metric_col)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
