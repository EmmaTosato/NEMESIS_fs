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
static side-by-side grid. plot_tuning_curve/plot_tuning_heatmap exist because a human has to eyeball a
fine-tuning sweep to pick parameters by hand (src/analysis/tuning.py) - no
automatic selection. plot_clustering_tuning_metrics/plot_dendrogram/
plot_eigengap/plot_k_distance are the same "human eyeballs a sweep" idea
applied to clustering.py's own fine-tuning mode (src/analysis/clustering_tuning.py)
- one generic multi-metric curve plus 3 method-specific standalone diagnostics
(dendrogram for agglomerative, eigengap for spectral, k-distance for dbscan),
also with no automatic selection.
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
# Fixed neutral gray for the DBSCAN/OPTICS noise label -1, kept out of the
# categorical set so it never impersonates a real cluster.
_NOISE_COLOR = "#9e9d98"

_COMPARISON_SUBPLOT_WIDTH = 7.0
_COMPARISON_SUBPLOT_HEIGHT = 5.5
_COMPARISON_WSPACE = 0.65
_COMPARISON_HSPACE = 0.55
_COMPARISON_TITLE_FONTSIZE = 15
_COMPARISON_MARKER_SIZE = 18
_COMPARISON_AXIS_PADDING_FRACTION = 0.08


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


def compose_comparison_title(output_dir: Path, reduction_method: str | None) -> str:
    """Suptitle for a cluster-method comparison plot:
    "Clustering comparison - <Modality> - <reduction_method>" (or without the
    trailing segment when reduction_method is None, e.g. clustering.py's
    comparison, which clusters a matrix directly with no reduction step).

    <Modality> is the naive capitalized plural (append "s") of output_dir's
    modality segment - the first path part after a leading "results", e.g.
    "lesion" -> "Lesions" - so a future modality (e.g. "sdc" -> "Sdcs") picks
    up the same format automatically. Reused verbatim by both clustering.py
    and dim_reduction_clustering.py so the two comparison plots can't drift
    out of format sync with each other.
    """
    parts = output_dir.parts
    if parts and parts[0] == "results":
        parts = parts[1:]
    if not parts:
        raise ValueError(f"cannot derive a modality from output_dir {output_dir} - no path segments after 'results'")
    modality_title = parts[0][0].upper() + parts[0][1:] + "s"
    if reduction_method:
        return f"Clustering comparison - {modality_title} - {reduction_method}"
    return f"Clustering comparison - {modality_title}"


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


def plot_embedding_interactive(
    X_2d: np.ndarray,
    metadata: pd.DataFrame,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    color_column: str = "dataset",
) -> None:
    """Interactive HTML scatter of the first 2 columns of X_2d, colored by
    metadata[color_column], with every metadata column shown on hover.

    Standalone self-contained HTML (plotly, no server) - open it directly in
    a browser. Every subject_id/dataset stays attached to its point, unlike
    plot_embedding_2d's anonymous dots, so an outlier or a cluster boundary
    can be traced back to a specific subject by hovering.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_embedding_interactive needs at least 2 columns, got shape {X_2d.shape}")
    if len(metadata) != X_2d.shape[0]:
        raise ValueError(
            f"X_2d has {X_2d.shape[0]} rows but metadata has {len(metadata)} rows - must match"
        )
    if color_column not in metadata.columns:
        raise ValueError(
            f"color_column {color_column!r} not found in metadata columns {list(metadata.columns)}"
        )

    plot_df = metadata.copy()
    plot_df["_dim1"] = X_2d[:, 0]
    plot_df["_dim2"] = X_2d[:, 1]

    fig = px.scatter(
        plot_df,
        x="_dim1",
        y="_dim2",
        color=color_column,
        hover_data=list(metadata.columns),
        title=title,
    )
    fig.update_layout(xaxis_title=xlabel, yaxis_title=ylabel)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)


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


def plot_clusters_interactive(
    X_2d: np.ndarray,
    metadata: pd.DataFrame,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    cluster_column: str = "cluster_label",
    dataset_column: str = "dataset",
) -> None:
    """Interactive HTML scatter of the first 2 columns of X_2d, with a
    dropdown to switch the point coloring between cluster_column and
    dataset_column - every metadata column shown on hover either way.

    One self-contained HTML instead of two separate files: cluster
    assignment and dataset/site are both plausible lenses on the same 2D
    layout (does a cluster boundary track a site effect, or genuine
    structure?), and switching between them in place answers that better
    than opening two files side by side. Built with two full px.scatter
    trace sets (one per coloring) merged into one go.Figure, toggled via
    trace `visible` - plotly hides a trace's legend entry automatically
    when visible=False, so the legend always matches the active coloring.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_interactive needs at least 2 columns, got shape {X_2d.shape}")
    if len(metadata) != X_2d.shape[0]:
        raise ValueError(
            f"X_2d has {X_2d.shape[0]} rows but metadata has {len(metadata)} rows - must match"
        )
    for column in (cluster_column, dataset_column):
        if column not in metadata.columns:
            raise ValueError(f"column {column!r} not found in metadata columns {list(metadata.columns)}")

    plot_df = metadata.copy()
    plot_df["_dim1"] = X_2d[:, 0]
    plot_df["_dim2"] = X_2d[:, 1]
    plot_df["_cluster_str"] = plot_df[cluster_column].astype(str)

    hover_columns = list(metadata.columns)
    fig_by_cluster = px.scatter(plot_df, x="_dim1", y="_dim2", color="_cluster_str", hover_data=hover_columns)
    fig_by_dataset = px.scatter(plot_df, x="_dim1", y="_dim2", color=dataset_column, hover_data=hover_columns)
    for trace in fig_by_dataset.data:
        trace.visible = False

    n_cluster_traces = len(fig_by_cluster.data)
    n_dataset_traces = len(fig_by_dataset.data)
    title_by_cluster = f"{title} (colored by {cluster_column})"
    title_by_dataset = f"{title} (colored by {dataset_column})"

    fig = go.Figure(data=list(fig_by_cluster.data) + list(fig_by_dataset.data))
    fig.update_layout(
        title=title_by_cluster,
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
                buttons=[
                    dict(
                        label=f"Color by {cluster_column}",
                        method="update",
                        args=[
                            {"visible": [True] * n_cluster_traces + [False] * n_dataset_traces},
                            {"title": title_by_cluster},
                        ],
                    ),
                    dict(
                        label=f"Color by {dataset_column}",
                        method="update",
                        args=[
                            {"visible": [False] * n_cluster_traces + [True] * n_dataset_traces},
                            {"title": title_by_dataset},
                        ],
                    ),
                ],
            )
        ],
    )

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
    x_pad = (x_max - x_min) * _COMPARISON_AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _COMPARISON_AXIS_PADDING_FRACTION
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
            s=_COMPARISON_MARKER_SIZE,
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


def plot_clustering_tuning_metrics(df: pd.DataFrame, param_col: str, metric_cols: list[str], output_path: Path, title: str) -> None:
    """One line-plot subplot per metric in metric_cols, all sharing param_col
    on the x-axis - the clustering-tuning equivalent of plot_tuning_curve, but
    for more than one metric at once. Silhouette ([-1, 1]), Calinski-Harabasz
    (unbounded positive, grows with cluster count) and Davies-Bouldin
    (unbounded positive, lower is better) live on incomparable scales -
    overlaying them on one shared axis would be misleading, so each gets its
    own subplot instead.
    """
    if not metric_cols:
        raise ValueError("plot_clustering_tuning_metrics needs at least one metric column")

    sorted_df = df.sort_values(param_col)

    fig, axes = plt.subplots(1, len(metric_cols), figsize=(5 * len(metric_cols), 4.5), squeeze=False)
    for ax, metric_col in zip(axes[0], metric_cols):
        ax.plot(sorted_df[param_col], sorted_df[metric_col], marker="o")
        ax.set_xlabel(param_col)
        ax.set_ylabel(metric_col)
    fig.suptitle(title)

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
    ax.set_title(title)

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
    ax.set_title(title)
    ax.legend()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_k_distance(distances: np.ndarray, output_path: Path, title: str) -> None:
    """Sorted k-distance curve (clustering_tuning.compute_k_distance) for
    picking DBSCAN's eps by eye - a good eps sits at the "knee" (steepest
    rise) of this ascending curve.
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(range(1, len(distances) + 1), distances, marker=".", markersize=3)
    ax.set_xlabel("points sorted by distance")
    ax.set_ylabel("distance to k-th nearest neighbor")
    ax.set_title(title)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
