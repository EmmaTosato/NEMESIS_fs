"""Minimal plotting for the modeling pipeline scripts - cluster separation and fine-tuning sweeps.

Not a general visualization module: a handful of narrow-purpose functions.
More than 2 dimensions is still out of scope. Per-dataset coloring and
interactivity were explicitly deferred in the analysis pipeline v2 handoff,
then un-deferred on request: plot_embedding_interactive/plot_clusters_interactive
exist because a static PNG can't answer "which subject is that outlier
point" - they need per-point hover identity, which only an interactive plot
can give. plot_clusters_2d exists only because seeing clusters on a 2D
scatter is the minimum needed to sanity-check a clustering run;
plot_clusters_comparison_interactive extends the same per-point hover need to
a multi-method comparison, one dropdown option per method instead of a
static side-by-side grid. plot_silhouette_analysis is the per-cluster
breakdown of that same sanity check, for one already-chosen production
result - a single aggregate silhouette number (reported during fine_tuning,
see clustering_tuning.compute_clustering_metrics) can hide a bad cluster
averaged out by good ones; this plots every sample's own coefficient,
grouped by cluster, next to the same 2D scatter. plot_tuning_curve exists because a human has to eyeball a
fine-tuning sweep to pick parameters by hand (src/analysis/tuning.py) - no
automatic selection; a 2+-parameter dim_reduction.py sweep gets no plot at
all, only tuning_results.csv (no heatmap here - removed on request, kept for
clustering_tuning.py below). plot_clustering_tuning_metrics/plot_dendrogram/
plot_eigengap are the same "human eyeballs a sweep" idea applied to
clustering.py's own fine-tuning mode (src/analysis/clustering_tuning.py) -
one generic multi-metric curve plus 2 method-specific standalone diagnostics
(dendrogram for agglomerative, eigengap for spectral - HDBSCAN gets no
standalone diagnostic, see clustering_tuning.py's module docstring), also
with no automatic selection. plot_embedding_categorical/
plot_embedding_continuous extend dim_reduction.py's production embedding plot
beyond the single-color plot_embedding_2d and the dataset-only
plot_embedding_interactive: any string category (dataset, lesion side) or
continuous quantity (lesion volume) per subject can be the color axis, each
written as its own embedding_plot_<name>.png - a static PNG only has one
legend/colorbar, so combining more than one coloring on the same static image
isn't attempted here (the interactive plot_embedding_interactive already
answers "what if I want a different color" via color_column, no separate
function needed for that side). Cluster-vs-dataset coloring in
plot_clusters_interactive was un-deferred and then re-deferred: a clustering
plot's job is to show the cluster assignment, dataset coloring belongs to
dim_reduction.py's own embedding_plot_dataset instead - keeping the two
concerns in the two places that already own them, rather than one function
answering both.
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram

# Pink/azzurro/green categorical palette (5 tones, user-requested hue
# families) - CVD-safe on EVERY pairwise combination (not just neighbors,
# relevant since scatter points from different clusters sit next to each
# other anywhere on the plot, not just adjacent in a legend), verified with
# a Python port of the dataviz skill's validate_palette.js (same OKLab/
# Machado-CVD math, same thresholds - worst all-pairs CVD dE 8.6, worst
# normal-vision dE 18.3, both clear of the 8.0/15.0 gates). Colors cycle
# past 5 clusters (an inherent limit of a validated-safe set, not a bug).
_CATEGORICAL_PALETTE = [
    "#e87ba4",  # pink
    "#3aa9e0",  # azzurro (sky blue)
    "#008300",  # green
    "#b03d68",  # pink (deep rose)
    "#1a6bab",  # azzurro (navy)
]
# Fixed neutral gray for the HDBSCAN/OPTICS noise label -1, kept out of the
# categorical set so it never impersonates a real cluster.
_NOISE_COLOR = "#9e9d98"

# Shared between plot_clusters_2d (single method) and plot_clusters_comparison (grid).
_MARKER_SIZE = 18
_AXIS_PADDING_FRACTION = 0.08

_COMPARISON_SUBPLOT_WIDTH = 7.0
_COMPARISON_SUBPLOT_HEIGHT = 5.5
_COMPARISON_WSPACE = 0.65
_COMPARISON_HSPACE = 0.55
_COMPARISON_TITLE_FONTSIZE = 15

_SINGLE_PLOT_WIDTH = 7.5
_SINGLE_PLOT_HEIGHT = 5.5
_SINGLE_PLOT_TITLE_FONTSIZE = 15
_SINGLE_PLOT_TITLE_PAD = 20

_TUNING_METRICS_SUBPLOT_WIDTH = 6.0
_TUNING_METRICS_SUBPLOT_HEIGHT = 4.5
_TUNING_METRICS_WSPACE = 0.4
_TUNING_METRICS_HSPACE = 0.4

_SILHOUETTE_SUBPLOT_WIDTH = 6.5
_SILHOUETTE_HEIGHT = 5.5
_SILHOUETTE_WSPACE = 0.35
_SILHOUETTE_BAND_GAP = 10  # vertical gap (in samples) between per-cluster silhouette bands


def _square_grid_shape(n_items: int) -> tuple[int, int]:
    """Smallest square (nrows == ncols) grid that fits n_items, e.g. 4 -> (2, 2),
    5 -> (3, 3). Trades a few empty cells for a grid that always reads as
    regular, rather than the narrower rectangle a minimal-area packing
    (ncols=ceil(sqrt(n)), nrows=ceil(n/ncols)) would produce for n=5 (3x2).
    """
    if n_items < 1:
        raise ValueError(f"_square_grid_shape needs at least 1 item, got {n_items}")
    side = math.ceil(math.sqrt(n_items))
    return side, side


def _palette_for_labels(unique_labels: list[int]) -> dict[int, str]:
    """Maps each cluster label to a color: -1 (noise) always gets the fixed
    neutral gray, every other label cycles through the validated categorical
    palette in ascending label order.
    """
    palette: dict[int, str] = {}
    colors = itertools.cycle(_CATEGORICAL_PALETTE)
    for label in unique_labels:
        if label == -1:
            palette[label] = _NOISE_COLOR
        else:
            palette[label] = next(colors)
    return palette


def compose_run_title(output_dir: Path, project: str) -> str:
    """Compose a plot title from a run's own output directory path, prefixed
    with `project` - e.g. output_dir=results/lesion/dim_reduction/umap/21-07_s1_d01
    -> "clinical_connectome — lesion › dim_reduction › umap › 21-07_s1_d01".

    Single source of truth for "which run is this": output_dir is the same
    Path every pipeline script already builds for save_matrix/logging, so the
    title can never drift out of sync with it, and stays correct no matter
    how deep results/ ends up nested (modality/pipeline/method/session/tag -
    see docs/dev/analysis.md) without this function needing to know about any
    of those axes individually. Drops a leading "results" path segment for
    readability (every pipeline's output_root today starts with "results/");
    falls back to the full path if it doesn't, rather than raising - a
    cosmetic difference only, not a broken title.
    """
    parts = output_dir.parts
    if parts and parts[0] == "results":
        parts = parts[1:]
    return f"{project} — " + " › ".join(parts)


def _modality_title(output_dir: Path) -> str:
    """Naive capitalized plural (append "s") of output_dir's modality segment
    - the first path part after a leading "results", e.g. "lesion" ->
    "Lesions" - so a future modality (e.g. "sdc" -> "Sdcs") picks up the same
    format automatically. Shared by every title composer below so they can't
    drift out of format sync with each other.
    """
    parts = output_dir.parts
    if parts and parts[0] == "results":
        parts = parts[1:]
    if not parts:
        raise ValueError(f"cannot derive a modality from output_dir {output_dir} - no path segments after 'results'")
    return parts[0][0].upper() + parts[0][1:] + "s"


def compose_comparison_title(output_dir: Path, reduction_method: str | None) -> str:
    """Suptitle for a cluster-method comparison plot:
    "Clustering comparison - <Modality> - <reduction_method>" (or without the
    trailing segment when reduction_method is None, e.g. clustering.py's
    comparison, which clusters a matrix directly with no reduction step).
    """
    modality_title = _modality_title(output_dir)
    if reduction_method:
        return f"Clustering comparison - {modality_title} - {reduction_method}"
    return f"Clustering comparison - {modality_title}"


def compose_cluster_plot_title(output_dir: Path, reduction_method: str, clustering_method: str) -> str:
    """Title for a single clustering method's static scatter (cluster_plot.png):
    "<Modality> - <ReductionMethod> - <ClusteringMethod>", each segment
    capitalized (Python's str.capitalize(), e.g. "umap" -> "Umap").
    """
    modality_title = _modality_title(output_dir)
    return f"{modality_title} - {reduction_method.capitalize()} - {clustering_method.capitalize()}"


def compose_embedding_plot_title(output_dir: Path, reduction_method: str, color_by: str | None = None) -> str:
    """Title for a dim_reduction.py embedding scatter: "<Modality> -
    <ReductionMethod>" (embedding_plot_unico.png, single color) or "<Modality>
    - <ReductionMethod> - <color_by>" (embedding_plot_{dataset,volume,side}.*),
    same capitalization/format convention as compose_cluster_plot_title so
    the two plot families read as one style instead of two.
    """
    modality_title = _modality_title(output_dir)
    if color_by:
        return f"{modality_title} - {reduction_method.capitalize()} - {color_by}"
    return f"{modality_title} - {reduction_method.capitalize()}"


def plot_embedding_2d(
    X_2d: np.ndarray, output_path: Path, xlabel: str, ylabel: str, title: str
) -> None:
    """Scatter the first 2 columns of X_2d (no color labels), to output_path.

    Same visual conventions as plot_clusters_2d (figure size, marker size,
    bold/padded title, axis padding beyond the data's own min/max) minus the
    legend/palette - there's no grouping to label here, just one color.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_embedding_2d needs at least 2 columns, got shape {X_2d.shape}")

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION

    fig, ax = plt.subplots(figsize=(_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT))
    ax.scatter(X_2d[:, 0], X_2d[:, 1], alpha=0.5, s=_MARKER_SIZE, edgecolor="none")
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _palette_for_categories(categories: list[str], missing_label: str = "unknown") -> dict[str, str]:
    """Maps each category string to a color: missing_label always gets the
    fixed neutral gray (same convention as -1/noise in _palette_for_labels),
    every other category cycles through the validated categorical palette in
    the order given (callers pass a sorted list, so this is deterministic).
    """
    palette: dict[str, str] = {}
    colors = itertools.cycle(_CATEGORICAL_PALETTE)
    for category in categories:
        if category == missing_label:
            palette[category] = _NOISE_COLOR
        else:
            palette[category] = next(colors)
    return palette


def plot_embedding_categorical(
    X_2d: np.ndarray,
    categories: np.ndarray,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    legend_title: str,
    missing_label: str = "unknown",
) -> None:
    """Scatter the first 2 columns of X_2d, colored by an arbitrary string
    category per point (e.g. dataset, lesion side), to output_path.

    Same visual treatment as plot_clusters_2d: validated categorical
    palette (missing_label - default "unknown" - always the same neutral
    gray used for cluster noise, so a structurally-missing value never
    impersonates a real category), legend anchored outside the axes, axis
    limits padded beyond the data's own min/max, bold/padded title.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_embedding_categorical needs at least 2 columns, got shape {X_2d.shape}")

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION
    unique_categories = sorted(pd.unique(categories).tolist())

    fig, ax = plt.subplots(figsize=(_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT))
    sns.scatterplot(
        x=X_2d[:, 0],
        y=X_2d[:, 1],
        hue=categories,
        hue_order=unique_categories,
        palette=_palette_for_categories(unique_categories, missing_label),
        s=_MARKER_SIZE,
        edgecolor="none",
        legend="full",
        ax=ax,
    )
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)
    handles, legend_labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        legend_labels,
        title=legend_title,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_embedding_continuous(
    X_2d: np.ndarray,
    values: np.ndarray,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    colorbar_label: str,
) -> None:
    """Scatter the first 2 columns of X_2d, colored by a continuous value per
    point (e.g. lesion volume in voxels), with a colorbar, to output_path.

    Same figure size/marker size/axis padding/bold-padded-title conventions
    as plot_clusters_2d/plot_embedding_categorical - a continuous quantity
    has no legend entries to place, so a colorbar takes that role instead.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_embedding_continuous needs at least 2 columns, got shape {X_2d.shape}")

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION

    fig, ax = plt.subplots(figsize=(_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT))
    scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=values, cmap="viridis", s=_MARKER_SIZE, edgecolor="none")
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)
    fig.colorbar(scatter, ax=ax, label=colorbar_label)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_embedding_interactive(
    X: np.ndarray,
    metadata: pd.DataFrame,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    color_column: str = "dataset",
    zlabel: str | None = None,
) -> None:
    """Interactive HTML scatter of the first 2 or 3 columns of X, colored by
    metadata[color_column], with every metadata column shown on hover.

    Standalone self-contained HTML (plotly, no server) - open it directly in
    a browser. Every subject_id/dataset stays attached to its point, unlike
    plot_embedding_2d's anonymous dots, so an outlier or a cluster boundary
    can be traced back to a specific subject by hovering.

    Branches on X.shape[1]: 2 columns -> px.scatter, 3 columns -> px.scatter_3d
    (needs `zlabel`, since a 3D scene has a third axis to label) - a 3D
    embedding gets no static-PNG counterpart anywhere in this module (a
    non-rotatable 3D scatter is often unreadable), this interactive plot is
    its only rendering. Raises ValueError for any other column count.
    """
    n_dims = X.shape[1]
    if n_dims not in (2, 3):
        raise ValueError(f"plot_embedding_interactive supports 2 or 3 columns, got shape {X.shape}")
    if len(metadata) != X.shape[0]:
        raise ValueError(f"X has {X.shape[0]} rows but metadata has {len(metadata)} rows - must match")
    if color_column not in metadata.columns:
        raise ValueError(f"color_column {color_column!r} not found in metadata columns {list(metadata.columns)}")
    if n_dims == 3 and zlabel is None:
        raise ValueError("plot_embedding_interactive needs zlabel for a 3-column embedding")

    plot_df = metadata.copy()
    plot_df["_dim1"] = X[:, 0]
    plot_df["_dim2"] = X[:, 1]

    if n_dims == 2:
        fig = px.scatter(plot_df, x="_dim1", y="_dim2", color=color_column, hover_data=list(metadata.columns), title=title)
        fig.update_layout(xaxis_title=xlabel, yaxis_title=ylabel)
    else:
        plot_df["_dim3"] = X[:, 2]
        fig = px.scatter_3d(
            plot_df, x="_dim1", y="_dim2", z="_dim3", color=color_column, hover_data=list(metadata.columns), title=title
        )
        fig.update_layout(scene={"xaxis_title": xlabel, "yaxis_title": ylabel, "zaxis_title": zlabel})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)


def plot_clusters_2d(
    X_2d: np.ndarray, cluster_labels: np.ndarray, output_path: Path, xlabel: str, ylabel: str, title: str
) -> None:
    """Scatter the first 2 columns of X_2d, colored by cluster_labels, to output_path.

    Callers pass whatever 2D array is actually meaningful for their case
    (a dimensionality-reduction embedding, or raw features when there's no
    reduction) - this function has no opinion on where X_2d came from. Same
    treatment as plot_clusters_comparison's per-panel styling: validated
    categorical palette, legend anchored outside the axes (never over the
    data), axis limits padded beyond the data's own min/max so edge points
    aren't clipped by their own marker radius, extra title padding.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_2d needs at least 2 columns, got shape {X_2d.shape}")

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION
    unique_labels = sorted(np.unique(cluster_labels).tolist())

    fig, ax = plt.subplots(figsize=(_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT))
    sns.scatterplot(
        x=X_2d[:, 0],
        y=X_2d[:, 1],
        hue=cluster_labels,
        hue_order=unique_labels,
        palette=_palette_for_labels(unique_labels),
        s=_MARKER_SIZE,
        edgecolor="none",
        legend="full",
        ax=ax,
    )
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)
    handles, legend_labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        legend_labels,
        title="cluster",
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_silhouette_analysis(
    sample_labels: np.ndarray,
    sample_silhouette_values: np.ndarray,
    X_2d: np.ndarray,
    display_labels: np.ndarray,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
) -> None:
    """The classic sklearn-style two-panel silhouette diagnostic for one
    already-chosen production clustering result.

    Left: one filled horizontal band per cluster, its members' individual
    silhouette coefficients sorted ascending within the band - a wide,
    uniformly high band reads as a well-separated cluster; a band dipping
    below 0 means those members sit, on average, closer to a neighboring
    cluster than their own. A dashed line marks the mean over all bands,
    which equals compute_clustering_metrics's aggregate "silhouette" number
    exactly (silhouette_score is defined as that mean) - this plot is a
    breakdown of that single number, not a different metric. Right: the same
    2D scatter as plot_clusters_2d, for a side-by-side spatial read.

    sample_labels/sample_silhouette_values come from
    clustering_tuning.compute_silhouette_samples - noise (-1) already
    excluded there, since silhouette is undefined for a "cluster" that isn't
    one. display_labels is the FULL label vector (noise included, grayed out
    by _palette_for_labels) so the scatter panel still shows where noise
    points physically sit, even though they have no band on the left.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_silhouette_analysis needs at least 2 columns in X_2d, got shape {X_2d.shape}")

    display_unique = sorted(np.unique(display_labels).tolist())
    palette = _palette_for_labels(display_unique)
    avg_score = float(np.mean(sample_silhouette_values))

    fig, (ax_sil, ax_scatter) = plt.subplots(
        1,
        2,
        figsize=(_SILHOUETTE_SUBPLOT_WIDTH * 2, _SILHOUETTE_HEIGHT),
        gridspec_kw={"wspace": _SILHOUETTE_WSPACE},
    )

    y_lower = _SILHOUETTE_BAND_GAP
    for label in sorted(np.unique(sample_labels).tolist()):
        values = np.sort(sample_silhouette_values[sample_labels == label])
        y_upper = y_lower + len(values)
        ax_sil.fill_betweenx(np.arange(y_lower, y_upper), 0, values, facecolor=palette[label], edgecolor=palette[label])
        ax_sil.text(-0.05, y_lower + 0.5 * len(values), str(label))
        y_lower = y_upper + _SILHOUETTE_BAND_GAP
    ax_sil.axvline(avg_score, color="red", linestyle="--", label=f"mean = {avg_score:.3f}")
    ax_sil.set_xlabel("silhouette coefficient")
    ax_sil.set_ylabel("cluster")
    ax_sil.set_yticks([])
    ax_sil.legend(loc="lower right")

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION
    sns.scatterplot(
        x=X_2d[:, 0],
        y=X_2d[:, 1],
        hue=display_labels,
        hue_order=display_unique,
        palette=palette,
        s=_MARKER_SIZE,
        edgecolor="none",
        legend="full",
        ax=ax_scatter,
    )
    ax_scatter.set_xlim(x_min - x_pad, x_max + x_pad)
    ax_scatter.set_ylim(y_min - y_pad, y_max + y_pad)
    ax_scatter.set_xlabel(xlabel)
    ax_scatter.set_ylabel(ylabel)
    handles, legend_labels = ax_scatter.get_legend_handles_labels()
    ax_scatter.legend(
        handles, legend_labels, title="cluster", loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0
    )

    fig.suptitle(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_clusters_interactive(
    X_2d: np.ndarray,
    metadata: pd.DataFrame,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    cluster_column: str = "cluster_label",
) -> None:
    """Interactive HTML scatter of the first 2 columns of X_2d, colored by
    cluster_column, with every metadata column shown on hover.

    Cluster-only coloring on purpose (no dataset/site toggle here - a
    clustering plot's job is to inspect the cluster assignment; dataset
    coloring lives on dim_reduction.py's own embedding_plot_dataset instead,
    see plotting.py's module docstring / docs/dev/analysis.md).
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_interactive needs at least 2 columns, got shape {X_2d.shape}")
    if len(metadata) != X_2d.shape[0]:
        raise ValueError(
            f"X_2d has {X_2d.shape[0]} rows but metadata has {len(metadata)} rows - must match"
        )
    if cluster_column not in metadata.columns:
        raise ValueError(f"column {cluster_column!r} not found in metadata columns {list(metadata.columns)}")

    plot_df = metadata.copy()
    plot_df["_dim1"] = X_2d[:, 0]
    plot_df["_dim2"] = X_2d[:, 1]
    plot_df["_cluster_str"] = plot_df[cluster_column].astype(str)

    hover_columns = list(metadata.columns)
    fig = px.scatter(plot_df, x="_dim1", y="_dim2", color="_cluster_str", hover_data=hover_columns, title=title)
    fig.update_layout(xaxis_title=xlabel, yaxis_title=ylabel, legend_title=cluster_column)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)


def plot_clusters_comparison(
    X_2d: np.ndarray,
    labels_by_method: dict[str, np.ndarray],
    output_path: Path,
    xlabel: str,
    ylabel: str,
    suptitle: str,
) -> None:
    """Square grid of subplots (see _square_grid_shape), one per method, same
    X_2d, colored by that method's own cluster_labels via the validated
    categorical palette (_palette_for_labels) - noise label -1 always gray.

    Shared x/y limits (with a fixed padding fraction beyond the data's own
    min/max, so edge points aren't clipped by their own marker radius) across
    every subplot so the comparison is visually honest - a method that
    spreads points wider isn't allowed to look more "spread out" just
    because matplotlib auto-scaled its own axes differently. Each subplot's
    legend is anchored just outside its own axes (never over the data) -
    subplots are widened and spaced out accordingly.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_comparison needs at least 2 columns, got shape {X_2d.shape}")
    if not labels_by_method:
        raise ValueError("plot_clusters_comparison needs at least one method in labels_by_method")

    methods = list(labels_by_method)
    nrows, ncols = _square_grid_shape(len(methods))

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION
    xlim = (x_min - x_pad, x_max + x_pad)
    ylim = (y_min - y_pad, y_max + y_pad)

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(_COMPARISON_SUBPLOT_WIDTH * ncols, _COMPARISON_SUBPLOT_HEIGHT * nrows),
        squeeze=False,
        gridspec_kw={"wspace": _COMPARISON_WSPACE, "hspace": _COMPARISON_HSPACE},
    )
    for i, method in enumerate(methods):
        ax = axes[i // ncols][i % ncols]
        labels = labels_by_method[method]
        unique_labels = sorted(np.unique(labels).tolist())
        sns.scatterplot(
            x=X_2d[:, 0],
            y=X_2d[:, 1],
            hue=labels,
            hue_order=unique_labels,
            palette=_palette_for_labels(unique_labels),
            s=_MARKER_SIZE,
            edgecolor="none",
            legend="full",
            ax=ax,
        )
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(method, fontsize=_COMPARISON_TITLE_FONTSIZE, fontweight="bold")
        handles, legend_labels = ax.get_legend_handles_labels()
        ax.legend(
            handles,
            legend_labels,
            title="cluster",
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            borderaxespad=0.0,
            fontsize="small",
            title_fontsize="small",
        )
    for i in range(len(methods), nrows * ncols):
        axes[i // ncols][i % ncols].set_visible(False)
    fig.suptitle(suptitle, fontsize=_COMPARISON_TITLE_FONTSIZE + 2, fontweight="bold")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_clusters_comparison_interactive(
    X_2d: np.ndarray,
    labels_by_method: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
) -> None:
    """Interactive HTML scatter of the first 2 columns of X_2d, with a
    dropdown to switch the point coloring between each clustering method's
    own cluster assignment - every metadata column shown on hover regardless
    of which method is selected.

    Same dropdown mechanism as plot_clusters_interactive (one full trace set
    per option, toggled via `visible`), but with one option per method
    instead of a fixed cluster/dataset pair: same 2D layout, same points,
    only which method's labels color them changes - answers "do these two
    methods agree on this boundary" without opening N separate HTML files.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_comparison_interactive needs at least 2 columns, got shape {X_2d.shape}")
    if len(metadata) != X_2d.shape[0]:
        raise ValueError(
            f"X_2d has {X_2d.shape[0]} rows but metadata has {len(metadata)} rows - must match"
        )
    if not labels_by_method:
        raise ValueError("plot_clusters_comparison_interactive needs at least one method in labels_by_method")

    plot_df = metadata.copy()
    plot_df["_dim1"] = X_2d[:, 0]
    plot_df["_dim2"] = X_2d[:, 1]
    hover_columns = list(metadata.columns)

    methods = list(labels_by_method)
    traces_per_method = []
    all_traces = []
    for method in methods:
        plot_df["_cluster_str"] = pd.Series(labels_by_method[method], index=plot_df.index).astype(str)
        fig_method = px.scatter(plot_df, x="_dim1", y="_dim2", color="_cluster_str", hover_data=hover_columns)
        traces_per_method.append(len(fig_method.data))
        all_traces.extend(fig_method.data)

    first_method_trace_count = traces_per_method[0]
    for trace in all_traces[first_method_trace_count:]:
        trace.visible = False

    buttons = []
    offset = 0
    for method, n_traces in zip(methods, traces_per_method):
        visibility = [False] * len(all_traces)
        visibility[offset : offset + n_traces] = [True] * n_traces
        buttons.append(
            dict(
                label=method,
                method="update",
                args=[{"visible": visibility}, {"title": f"{title} (colored by {method})"}],
            )
        )
        offset += n_traces

    fig = go.Figure(data=all_traces)
    fig.update_layout(
        title=f"{title} (colored by {methods[0]})",
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
                buttons=buttons,
            )
        ],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)


def plot_embedding_grid_blocks(
    blocks: list[tuple[str, list[tuple[str, np.ndarray]]]],
    output_path: Path,
    xlabel: str,
    ylabel: str,
    suptitle: str,
    color_values: np.ndarray | None = None,
    color_kind: str | None = None,
    legend_title: str | None = None,
) -> None:
    """One row of small scatter subplots per entry in `blocks` - each entry
    is (block_title, [(cell_title, embedding_2d), ...]), e.g. block_title=
    "n_neighbors", one cell per swept n_neighbors value while every other
    grid parameter stays at its production/base value (the caller - see
    src/analysis/embedding_plots.py::write_embedding_grid - decides which
    embeddings go in which cell; this function only lays them out).

    Shows the *real* embeddings side by side (unlike plot_tuning_curve's
    single numeric score), so a human can see how the point cloud's shape
    actually changes with a parameter, not just how one aggregate metric
    moves. A dedicated label row (own axis, text only) sits above each
    block's scatter row, and a blank spacer row separates one block from the
    next - real whitespace, not just subplot padding, so multiple blocks in
    one figure read as visually distinct sections.

    All cells share the same x/y axis limits (padded beyond the combined
    min/max of every embedding shown) and the same coloring: `color_values`/
    `color_kind` is None/None for "unico" (single color, same convention as
    plot_embedding_2d), or a color_by mode's per-subject values plus
    "categorical"/"continuous" (same two renderings as
    plot_embedding_categorical/plot_embedding_continuous) - every cell is a
    fit of the same subjects, so one shared legend/colorbar for the whole
    figure is enough, taken from the first cell only.
    """
    if not blocks:
        raise ValueError("plot_embedding_grid_blocks needs at least one block")
    if color_kind not in (None, "categorical", "continuous"):
        raise ValueError(f"color_kind must be None, 'categorical' or 'continuous', got {color_kind!r}")

    ncols = max(len(cells) for _, cells in blocks)
    all_points = np.concatenate([embedding for _, cells in blocks for _, embedding in cells], axis=0)
    x_min, x_max = all_points[:, 0].min(), all_points[:, 0].max()
    y_min, y_max = all_points[:, 1].min(), all_points[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION

    height_ratios: list[float] = []
    for i in range(len(blocks)):
        height_ratios += [0.5, 4.0]
        if i < len(blocks) - 1:
            height_ratios.append(0.8)

    fig = plt.figure(figsize=(_TUNING_METRICS_SUBPLOT_WIDTH * ncols, sum(height_ratios) * 0.9))
    gridspec = fig.add_gridspec(len(height_ratios), ncols, height_ratios=height_ratios, hspace=0.15, wspace=0.35)

    legend_handles_labels = None
    row = 0
    for block_title, cells in blocks:
        label_ax = fig.add_subplot(gridspec[row, :])
        label_ax.axis("off")
        label_ax.text(0.5, 0.5, block_title, ha="center", va="center", fontweight="bold", fontsize=12)
        row += 1

        for col, (cell_title, embedding) in enumerate(cells):
            ax = fig.add_subplot(gridspec[row, col])
            if color_values is None:
                ax.scatter(embedding[:, 0], embedding[:, 1], alpha=0.5, s=_MARKER_SIZE, edgecolor="none")
            elif color_kind == "categorical":
                unique_categories = sorted(pd.unique(color_values).tolist())
                show_legend = legend_handles_labels is None
                sns.scatterplot(
                    x=embedding[:, 0],
                    y=embedding[:, 1],
                    hue=color_values,
                    hue_order=unique_categories,
                    palette=_palette_for_categories(unique_categories),
                    s=_MARKER_SIZE,
                    edgecolor="none",
                    legend="full" if show_legend else False,
                    ax=ax,
                )
                if show_legend:
                    legend_handles_labels = ax.get_legend_handles_labels()
                    ax.get_legend().remove()
            else:  # continuous
                ax.scatter(embedding[:, 0], embedding[:, 1], c=color_values, cmap="viridis", s=_MARKER_SIZE, edgecolor="none")
            ax.set_xlim(x_min - x_pad, x_max + x_pad)
            ax.set_ylim(y_min - y_pad, y_max + y_pad)
            ax.set_title(cell_title, fontsize=10)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        for col in range(len(cells), ncols):
            fig.add_subplot(gridspec[row, col]).axis("off")
        row += 1

        if row < len(height_ratios) and height_ratios[row] < 1:
            fig.add_subplot(gridspec[row, :]).axis("off")
            row += 1

    if legend_handles_labels:
        fig.legend(*legend_handles_labels, title=legend_title, loc="upper left", bbox_to_anchor=(1.0, 0.95))

    fig.suptitle(suptitle, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold")
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


def plot_clustering_tuning_heatmaps(
    df: pd.DataFrame, param_x: str, param_y: str, metric_cols: list[str], output_path: Path, title: str
) -> None:
    """One heatmap subplot per metric in metric_cols, sharing param_x/param_y
    on the two axes - a 2-parameter clustering-tuning sweep (params_clustering.json),
    one heatmap per metric at once (see plot_clustering_tuning_metrics
    for why silhouette/Calinski-Harabasz/Davies-Bouldin/extras each need
    their own subplot rather than one shared axis).
    """
    if not metric_cols:
        raise ValueError("plot_clustering_tuning_heatmaps needs at least one metric column")

    nrows, ncols = _square_grid_shape(len(metric_cols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(_TUNING_METRICS_SUBPLOT_WIDTH * ncols, _TUNING_METRICS_SUBPLOT_HEIGHT * nrows),
        squeeze=False,
        gridspec_kw={"wspace": _TUNING_METRICS_WSPACE, "hspace": _TUNING_METRICS_HSPACE},
    )
    for i, metric_col in enumerate(metric_cols):
        ax = axes[i // ncols][i % ncols]
        pivot = df.pivot(index=param_y, columns=param_x, values=metric_col)
        image = ax.imshow(pivot.values, cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xlabel(param_x)
        ax.set_ylabel(param_y)
        ax.set_title(metric_col)
        fig.colorbar(image, ax=ax)
    for i in range(len(metric_cols), nrows * ncols):
        axes[i // ncols][i % ncols].set_visible(False)
    fig.suptitle(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_clustering_tuning_metrics(df: pd.DataFrame, param_col: str, metric_cols: list[str], output_path: Path, title: str) -> None:
    """One line-plot subplot per metric in metric_cols, all sharing param_col
    on the x-axis - the clustering-tuning equivalent of plot_tuning_curve, but
    for more than one metric at once. Silhouette ([-1, 1]), Calinski-Harabasz
    (unbounded positive, grows with cluster count) and Davies-Bouldin
    (unbounded positive, lower is better) live on incomparable scales -
    overlaying them on one shared axis would be misleading, so each gets its
    own subplot instead.

    Laid out on the smallest square grid that fits all metrics (see
    _square_grid_shape), not a single row - a single row of 4-5 subplots
    compresses each one so much that axis labels/ticks collide.
    """
    if not metric_cols:
        raise ValueError("plot_clustering_tuning_metrics needs at least one metric column")

    sorted_df = df.sort_values(param_col)
    nrows, ncols = _square_grid_shape(len(metric_cols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(_TUNING_METRICS_SUBPLOT_WIDTH * ncols, _TUNING_METRICS_SUBPLOT_HEIGHT * nrows),
        squeeze=False,
        gridspec_kw={"wspace": _TUNING_METRICS_WSPACE, "hspace": _TUNING_METRICS_HSPACE},
    )
    for i, metric_col in enumerate(metric_cols):
        ax = axes[i // ncols][i % ncols]
        ax.plot(sorted_df[param_col], sorted_df[metric_col], marker="o")
        ax.set_xlabel(param_col)
        ax.set_ylabel(metric_col)
    for i in range(len(metric_cols), nrows * ncols):
        axes[i // ncols][i % ncols].set_visible(False)
    fig.suptitle(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_dendrogram(linkage_matrix: np.ndarray, output_path: Path, title: str, truncate_last_p: int = 30) -> None:
    """Truncated dendrogram (scipy) from a linkage matrix built by
    clustering_tuning.compute_dendrogram_linkage - a full tree over hundreds
    or thousands of subjects is unreadable, so only the last `truncate_last_p`
    merges are shown (truncate_mode="lastp"), with each collapsed branch
    annotated by how many original subjects it represents.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    dendrogram(linkage_matrix, truncate_mode="lastp", p=truncate_last_p, ax=ax, show_contracted=True)
    ax.set_xlabel(f"cluster size (or subject index if a leaf) - truncated to last {truncate_last_p} merges")
    ax.set_ylabel("merge distance")
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_eigengap(eigenvalues: np.ndarray, output_path: Path, title: str) -> None:
    """Sorted eigenvalues of the affinity graph's Laplacian
    (clustering_tuning.compute_eigengap), with the single biggest gap between
    consecutive eigenvalues marked - the eigengap heuristic for picking
    SpectralClustering's n_clusters: the suggested k is the index right
    before the biggest jump (a Laplacian's near-zero eigenvalues approximate
    the number of well-separated graph components).
    """
    if len(eigenvalues) < 2:
        raise ValueError(f"plot_eigengap needs at least 2 eigenvalues to compute a gap, got {len(eigenvalues)}")

    gaps = np.diff(eigenvalues)
    best_gap_idx = int(np.argmax(gaps))

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(range(1, len(eigenvalues) + 1), eigenvalues, marker="o")
    ax.axvline(best_gap_idx + 1, color="red", linestyle="--", label=f"largest gap after eigenvalue {best_gap_idx + 1}")
    ax.set_xlabel("eigenvalue index")
    ax.set_ylabel("eigenvalue")
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)
    ax.legend()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
