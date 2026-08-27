"""Minimal plotting for the modeling pipeline scripts - cluster separation and fine-tuning sweeps.

Not a general visualization module: a handful of narrow-purpose functions,
each existing to answer one specific "a human eyeballs a sweep/result, no
automatic selection" need. Static functions here stay 2D-only - a 2D/3D
interactive view lives outside this module in
src.analysis.embedding_app/src.pipeline.embedding_app
(docs/guides/embedding_app.md), not a per-run static file. See
docs/dev/plotting.md for what each function is for and why.
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path

import matplotlib
import matplotlib.colors as mcolors

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram
from sklearn.neighbors import NearestNeighbors

# Pink/azzurro/green categorical palette (5 tones, user-requested hue
# families) - CVD-safe on every pairwise combination, verified (OKLab/
# Machado-CVD math, dataviz skill's validate_palette.js - see
# docs/dev/plotting.md before changing these colors). Cycles past 5
# clusters (an inherent limit of a validated-safe set, not a bug).
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

# plot_embedding_2d/plot_embedding_categorical/plot_embedding_continuous only
# (dim_reduction.py's production embedding plots) - a solid, opaque marker at
# _MARKER_SIZE overlaps into one indistinguishable blob at the ~5000+ subject
# scale these plots run at today (validated visually on the real 5269-subject
# 26-08_s1.2 cohort). Smaller reveals density texture; _declutter_points below
# does the heavy lifting on the overlap itself, so alpha only needs a light
# touch (0.9, not the much lower value tried during exploration) once that's
# in place. Deliberately not applied to _MARKER_SIZE's other consumers
# (plot_clusters_2d/plot_clusters_comparison/plot_silhouette_analysis) - out
# of scope for this fix, left for a future pass if the same problem is hit there.
_EMBEDDING_MARKER_SIZE = 6
_EMBEDDING_MARKER_ALPHA = 0.9
# Must match the dpi these 3 functions actually savefig() at - _declutter_points
# converts data units to screen pixels using this value, so a mismatch would
# dose the declutter against a marker footprint that isn't the one actually
# rendered.
_EMBEDDING_DPI = 150

# _declutter_points dosing (26-08-26, same validation session as the constants
# above): visually compared on the real 5269-subject cohort at several doses -
# 1 marker diameter stops literal marker-on-marker occlusion while leaving
# genuinely tight sub-clusters (e.g. one dataset's subjects sitting very close
# together) visually intact; 2-3 diameters starts dissolving those sub-clusters
# into the surrounding cloud, misrepresenting how close those subjects actually
# are in the embedding - see docs/dev/plotting.md. _DECLUTTER_ITERATIONS>1
# because resolving one crowded pair can create a new one with a third point
# that was fine on the previous pass.
_DECLUTTER_MARKER_DIAMETERS = 1.0
_DECLUTTER_ITERATIONS = 3
_DECLUTTER_STRENGTH = 0.8
_DECLUTTER_RANDOM_STATE = 0

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

# plot_embedding_grid_blocks packs the same subject count into a much smaller
# cell than a single full-figure embedding plot - a smaller, lower-alpha
# marker keeps individual points distinguishable instead of merging into one
# solid blob.
_GRID_MARKER_SIZE = 12
_GRID_MARKER_ALPHA = 0.7

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
    title can never drift out of sync with it (see docs/dev/plotting.md).
    Drops a leading "results" path segment for readability; falls back to
    the full path if there isn't one, rather than raising.
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


def compose_tuning_leaf_title(output_dir: Path, reduction_method: str, leaf: dict) -> str:
    """Title for one nested-tuning leaf's embeddings_grid_*.png:
    "<Modality> - <ReductionMethod> - <Metric> - <N> Components", same
    capitalization convention as compose_cluster_plot_title/
    compose_embedding_plot_title. `leaf` is one real nested-parameter
    combination - only the keys actually present are rendered, so this
    works for any nested_params subset (e.g. tsne's leaf has no
    "n_components").
    """
    modality_title = _modality_title(output_dir)
    parts = [modality_title, reduction_method.capitalize()]
    metric = leaf.get("metric")
    if metric is not None:
        parts.append(str(metric).capitalize())
    n_components = leaf.get("n_components")
    if n_components is not None:
        parts.append(f"{n_components} Components")
    return " - ".join(parts)


def _declutter_points(
    X_2d: np.ndarray, xlim: tuple[float, float], ylim: tuple[float, float], figsize: tuple[float, float], marker_size: float
) -> np.ndarray:
    """Pushes points that would literally overlap on screen apart by just
    enough to stop occluding each other, dosed to _DECLUTTER_MARKER_DIAMETERS
    marker diameters (see that constant's comment for why this specific dose
    and not more) - never touches a pair already farther apart on screen than
    that. Distance is computed in screen pixels (via xlim/ylim/figsize/
    _EMBEDDING_DPI), not raw data units, since the two axes can have very
    different data ranges - "close" only means anything in the space the
    marker itself is drawn in.

    Runs _DECLUTTER_ITERATIONS passes of "push each still-crowded point
    directly away from its current nearest neighbor by the shortfall",
    since resolving one pair's overlap can create a new one with a third
    point. An exact-duplicate pair (0 pixel distance) is pushed apart in a
    deterministic random direction (_DECLUTTER_RANDOM_STATE) - there's no
    "away from" direction to compute otherwise.

    Returns a new array in the same data-coordinate space as X_2d (never
    mutates it) - callers plot the result exactly like the original.
    """
    if X_2d.shape[1] != 2:
        raise ValueError(f"_declutter_points needs exactly 2 columns, got shape {X_2d.shape}")
    if X_2d.shape[0] < 2:
        # Nothing can overlap with fewer than 2 points - a legitimate no-op,
        # not a degenerate input (NearestNeighbors(n_neighbors=2) itself
        # would raise on a single row).
        return X_2d.copy()

    px_per_unit = np.array(
        [figsize[0] * _EMBEDDING_DPI / (xlim[1] - xlim[0]), figsize[1] * _EMBEDDING_DPI / (ylim[1] - ylim[0])]
    )
    marker_diameter_px = 2 * math.sqrt(marker_size / math.pi) / 72 * _EMBEDDING_DPI
    tau_px = _DECLUTTER_MARKER_DIAMETERS * marker_diameter_px

    rng = np.random.default_rng(_DECLUTTER_RANDOM_STATE)
    X_px = X_2d * px_per_unit
    for _ in range(_DECLUTTER_ITERATIONS):
        dist, idx = NearestNeighbors(n_neighbors=2).fit(X_px).kneighbors(X_px)
        nearest_dist, nearest_idx = dist[:, 1], idx[:, 1]
        crowded = nearest_dist < tau_px
        if not crowded.any():
            break

        direction = X_px[crowded] - X_px[nearest_idx[crowded]]
        norms = np.linalg.norm(direction, axis=1)
        zero_distance = norms < 1e-9
        if zero_distance.any():
            angles = rng.uniform(0, 2 * math.pi, size=int(zero_distance.sum()))
            direction[zero_distance] = np.column_stack([np.cos(angles), np.sin(angles)])
            norms[zero_distance] = 1.0
        unit_direction = direction / norms[:, None]

        magnitude = np.clip((tau_px - nearest_dist[crowded]) * _DECLUTTER_STRENGTH, 0, tau_px)
        X_px[crowded] += unit_direction * magnitude[:, None]

    return X_px / px_per_unit


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
    xlim = (x_min - x_pad, x_max + x_pad)
    ylim = (y_min - y_pad, y_max + y_pad)
    figsize = (_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT)
    X_2d = _declutter_points(X_2d, xlim, ylim, figsize, _EMBEDDING_MARKER_SIZE)

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(X_2d[:, 0], X_2d[:, 1], alpha=_EMBEDDING_MARKER_ALPHA, s=_EMBEDDING_MARKER_SIZE, edgecolor="none")
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=_EMBEDDING_DPI, bbox_inches="tight")
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
    xlim = (x_min - x_pad, x_max + x_pad)
    ylim = (y_min - y_pad, y_max + y_pad)
    figsize = (_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT)
    unique_categories = sorted(pd.unique(categories).tolist())
    X_2d = _declutter_points(X_2d, xlim, ylim, figsize, _EMBEDDING_MARKER_SIZE)

    fig, ax = plt.subplots(figsize=figsize)
    sns.scatterplot(
        x=X_2d[:, 0],
        y=X_2d[:, 1],
        hue=categories,
        hue_order=unique_categories,
        palette=_palette_for_categories(unique_categories, missing_label),
        s=_EMBEDDING_MARKER_SIZE,
        alpha=_EMBEDDING_MARKER_ALPHA,
        edgecolor="none",
        legend="full",
        ax=ax,
    )
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
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
    fig.savefig(output_path, dpi=_EMBEDDING_DPI, bbox_inches="tight")
    plt.close(fig)


def plot_embedding_continuous(
    X_2d: np.ndarray,
    values: np.ndarray,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    colorbar_label: str,
    log_scale: bool = False,
) -> None:
    """Scatter the first 2 columns of X_2d, colored by a continuous value per
    point (e.g. lesion volume in voxels), with a colorbar, to output_path.

    A NaN in values (e.g. an unresolvable NIHSS score) is drawn in the same
    fixed neutral gray as the categorical plots' missing/noise bucket
    (_NOISE_COLOR), never left to matplotlib's default invisible/transparent
    point - see docs/dev/plotting.md. The colorbar's range is fit to the
    non-NaN values only.

    log_scale=True (used for "volume" - see embedding_coloring.py's
    COLOR_MODES) maps color via matplotlib's LogNorm instead of linear
    normalization, so right-skewed outliers don't flatten the whole scale.
    Raises ValueError if any non-missing value is <= 0 - LogNorm can't
    represent it, and silently masking it out would misrepresent a real
    "zero volume" subject as unresolvable (same doc for why).
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_embedding_continuous needs at least 2 columns, got shape {X_2d.shape}")

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION
    xlim = (x_min - x_pad, x_max + x_pad)
    ylim = (y_min - y_pad, y_max + y_pad)
    figsize = (_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT)

    values = np.asarray(values, dtype=float)
    is_missing = np.isnan(values)

    norm = None
    if log_scale:
        present_values = values[~is_missing]
        if present_values.size and (present_values <= 0).any():
            raise ValueError(
                f"log_scale=True needs every non-missing value > 0, got {int((present_values <= 0).sum())} "
                "value(s) <= 0 - a log color scale can't represent them"
            )
        if present_values.size:
            norm = mcolors.LogNorm(vmin=present_values.min(), vmax=present_values.max())

    X_2d = _declutter_points(X_2d, xlim, ylim, figsize, _EMBEDDING_MARKER_SIZE)

    fig, ax = plt.subplots(figsize=figsize)
    if is_missing.any():
        ax.scatter(
            X_2d[is_missing, 0], X_2d[is_missing, 1],
            c=_NOISE_COLOR, s=_EMBEDDING_MARKER_SIZE, alpha=_EMBEDDING_MARKER_ALPHA, edgecolor="none", label="missing",
        )
    scatter = ax.scatter(
        X_2d[~is_missing, 0], X_2d[~is_missing, 1],
        c=values[~is_missing], cmap="viridis", norm=norm,
        s=_EMBEDDING_MARKER_SIZE, alpha=_EMBEDDING_MARKER_ALPHA, edgecolor="none",
    )
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)
    fig.colorbar(scatter, ax=ax, label=colorbar_label)
    if is_missing.any():
        ax.legend(loc="upper right", framealpha=0.9)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=_EMBEDDING_DPI, bbox_inches="tight")
    plt.close(fig)


_POINT_SIZE_FLOOR = _MARKER_SIZE * 0.3
_POINT_SIZE_SCALE = _MARKER_SIZE * 2.5


def plot_clusters_2d(
    X_2d: np.ndarray,
    cluster_labels: np.ndarray,
    output_path: Path,
    xlabel: str,
    ylabel: str,
    title: str,
    point_sizes: np.ndarray | None = None,
) -> None:
    """Scatter the first 2 columns of X_2d, colored by cluster_labels, to output_path.

    Callers pass whatever 2D array is actually meaningful for their case
    (a dimensionality-reduction embedding, or raw features when there's no
    reduction) - this function has no opinion on where X_2d came from. Same
    treatment as plot_clusters_comparison's per-panel styling: validated
    categorical palette, legend anchored outside the axes (never over the
    data), axis limits padded beyond the data's own min/max so edge points
    aren't clipped by their own marker radius, extra title padding.

    `point_sizes` (project-clustering-tuning-redesign memory, 26-08-26 -
    hdbscan's `probabilities_`, membership confidence in [0, 1]): `None`
    (default) is byte-for-byte the original behavior, one fixed
    `_MARKER_SIZE` for every point. When given, each point's marker area
    scales with its own value instead, floored at `_POINT_SIZE_FLOOR` so even
    a 0-probability point (e.g. HDBSCAN noise, always probability 0) stays
    visible rather than collapsing to an invisible zero-size marker.
    `sns.scatterplot`'s own legend-building breaks when `s` is array-like (it
    tries to reuse the array verbatim as a single legend marker size) - the
    array branch below builds the categorical legend by hand via
    `plt.Line2D` instead, matplotlib's own `ax.scatter` has no such issue.
    """
    if X_2d.shape[1] < 2:
        raise ValueError(f"plot_clusters_2d needs at least 2 columns, got shape {X_2d.shape}")

    x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
    y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
    x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
    y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION
    unique_labels = sorted(np.unique(cluster_labels).tolist())
    palette = _palette_for_labels(unique_labels)
    sizes = _MARKER_SIZE if point_sizes is None else _POINT_SIZE_FLOOR + _POINT_SIZE_SCALE * point_sizes

    fig, ax = plt.subplots(figsize=(_SINGLE_PLOT_WIDTH, _SINGLE_PLOT_HEIGHT))
    if point_sizes is None:
        sns.scatterplot(
            x=X_2d[:, 0],
            y=X_2d[:, 1],
            hue=cluster_labels,
            hue_order=unique_labels,
            palette=palette,
            s=sizes,
            edgecolor="none",
            legend="full",
            ax=ax,
        )
        handles, legend_labels = ax.get_legend_handles_labels()
    else:
        colors = [palette[label] for label in cluster_labels]
        ax.scatter(X_2d[:, 0], X_2d[:, 1], c=colors, s=sizes, edgecolors="none")
        handles = [
            plt.Line2D([0], [0], marker="o", linestyle="", color=palette[label], label=str(label))
            for label in unique_labels
        ]
        legend_labels = [str(label) for label in unique_labels]
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", pad=_SINGLE_PLOT_TITLE_PAD)
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
    already-chosen production clustering result - left: one filled band per
    cluster, members' coefficients sorted ascending, dashed line at the mean
    (equals compute_clustering_metrics's aggregate "silhouette" exactly);
    right: the same 2D scatter as plot_clusters_2d. See docs/dev/plotting.md
    for the full reading guide.

    sample_labels/sample_silhouette_values come from
    clustering_tuning.compute_silhouette_samples (noise already excluded);
    display_labels is the FULL label vector (noise included, grayed out) so
    the scatter panel still shows where noise points physically sit.
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
    categorical palette. Shared x/y limits across every subplot so the
    comparison is visually honest - a method isn't allowed to look more
    "spread out" just from independent axis auto-scaling (see
    docs/dev/plotting.md).
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

    Dropdown-toggled trace set (one full trace per option, toggled via
    `visible`), one option per method: same 2D layout, same points, only
    which method's labels color them changes - answers "do these two
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
    log_scale: bool = False,
) -> None:
    """One row of small scatter subplots per entry in `blocks` - each entry
    is (block_title, [(cell_title, embedding_2d), ...]), e.g. block_title=
    "n_neighbors", one cell per swept value while every other grid parameter
    stays at its base value (the caller, src/analysis/embedding_plots.py::
    write_embedding_grid, decides which embeddings go where; this function
    only lays them out). Shows the *real* embeddings side by side, so a
    human can see how the point cloud's shape changes, not just one
    aggregate metric moving - see docs/dev/plotting.md for the full layout
    rationale.

    Each cell auto-scales to its *own* embedding's min/max rather than
    sharing one axis range - two UMAP/t-SNE fits with different
    hyperparameters have no shared coordinate frame to begin with
    (`.claude/lessons_learned.md` #16). Coloring is shared though: one
    legend/colorbar for the whole figure, taken from the first cell only -
    `color_values`/`color_kind`/`log_scale` behave exactly as in
    plot_embedding_categorical/plot_embedding_continuous, including the
    same NaN/missing-value handling.
    """
    if not blocks:
        raise ValueError("plot_embedding_grid_blocks needs at least one block")
    if color_kind not in (None, "categorical", "continuous"):
        raise ValueError(f"color_kind must be None, 'categorical' or 'continuous', got {color_kind!r}")

    is_missing_color = None
    continuous_norm = None
    if color_kind == "continuous" and color_values is not None:
        color_values = np.asarray(color_values, dtype=float)
        is_missing_color = np.isnan(color_values)
        if log_scale:
            present_values = color_values[~is_missing_color]
            if present_values.size and (present_values <= 0).any():
                raise ValueError(
                    f"log_scale=True needs every non-missing value > 0, got "
                    f"{int((present_values <= 0).sum())} value(s) <= 0 - a log color scale can't represent them"
                )
            if present_values.size:
                continuous_norm = mcolors.LogNorm(vmin=present_values.min(), vmax=present_values.max())

    ncols = max(len(cells) for _, cells in blocks)

    height_ratios: list[float] = []
    for i in range(len(blocks)):
        height_ratios += [0.5, 4.0]
        if i < len(blocks) - 1:
            height_ratios.append(0.8)

    fig = plt.figure(figsize=(_TUNING_METRICS_SUBPLOT_WIDTH * ncols, sum(height_ratios) * 0.9))
    gridspec = fig.add_gridspec(len(height_ratios), ncols, height_ratios=height_ratios, hspace=0.15, wspace=0.35)

    legend_handles_labels = None
    missing_handles_labels = None
    continuous_mappable = None
    data_axes: list[plt.Axes] = []
    row = 0
    for block_title, cells in blocks:
        label_ax = fig.add_subplot(gridspec[row, :])
        label_ax.axis("off")
        label_ax.text(0.5, 0.5, block_title, ha="center", va="center", fontweight="bold", fontsize=12)
        row += 1

        for col, (cell_title, embedding) in enumerate(cells):
            ax = fig.add_subplot(gridspec[row, col])
            if color_values is None:
                ax.scatter(embedding[:, 0], embedding[:, 1], alpha=_GRID_MARKER_ALPHA, s=_GRID_MARKER_SIZE, edgecolor="none")
            elif color_kind == "categorical":
                unique_categories = sorted(pd.unique(color_values).tolist())
                show_legend = legend_handles_labels is None
                sns.scatterplot(
                    x=embedding[:, 0],
                    y=embedding[:, 1],
                    hue=color_values,
                    hue_order=unique_categories,
                    palette=_palette_for_categories(unique_categories),
                    s=_GRID_MARKER_SIZE,
                    alpha=_GRID_MARKER_ALPHA,
                    edgecolor="none",
                    legend="full" if show_legend else False,
                    ax=ax,
                )
                if show_legend:
                    legend_handles_labels = ax.get_legend_handles_labels()
                    ax.get_legend().remove()
            else:  # continuous
                if is_missing_color.any():
                    ax.scatter(
                        embedding[is_missing_color, 0], embedding[is_missing_color, 1],
                        c=_NOISE_COLOR, alpha=_GRID_MARKER_ALPHA, s=_GRID_MARKER_SIZE, edgecolor="none",
                        label="missing",
                    )
                    if missing_handles_labels is None:
                        missing_handles_labels = ax.get_legend_handles_labels()
                scatter = ax.scatter(
                    embedding[~is_missing_color, 0], embedding[~is_missing_color, 1],
                    c=color_values[~is_missing_color], cmap="viridis", norm=continuous_norm,
                    alpha=_GRID_MARKER_ALPHA, s=_GRID_MARKER_SIZE, edgecolor="none",
                )
                if continuous_mappable is None:
                    continuous_mappable = scatter
            data_axes.append(ax)
            x_min, x_max = embedding[:, 0].min(), embedding[:, 0].max()
            y_min, y_max = embedding[:, 1].min(), embedding[:, 1].max()
            x_pad = (x_max - x_min) * _AXIS_PADDING_FRACTION
            y_pad = (y_max - y_min) * _AXIS_PADDING_FRACTION
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
    if continuous_mappable is not None:
        fig.colorbar(continuous_mappable, ax=data_axes, label=legend_title, shrink=0.6)
    if missing_handles_labels:
        fig.legend(*missing_handles_labels, loc="lower left", bbox_to_anchor=(1.0, 0.05))

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
    on the x-axis - the clustering-tuning equivalent of plot_tuning_curve for
    more than one metric at once, each on its own subplot since silhouette/
    Calinski-Harabasz/Davies-Bouldin live on incomparable scales. Laid out
    on the smallest square grid that fits all metrics (see docs/dev/plotting.md).
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


def plot_stability_analysis(
    df: pd.DataFrame, target_param: str, nuisance_param: str, metric_col: str, output_path: Path, title: str
) -> None:
    """One panel per unique target_param value (e.g. n_clusters/n_components),
    errorbar mean +/- std(metric_col) vs n_init, one line per nuisance_param
    value (e.g. init/init_params) - kmeans/gmm's stability-analysis diagnostic
    (clustering_tuning.compute_stability_sweep), modeled on sklearn's
    plot_kmeans_stability_low_dim_dense.html, faceted across the representative
    target values instead of a single one. Purpose: validate the nuisance
    init/n_init parameter is stable *before* trusting the plain tuning sweep's
    per-target scores - see docs/dev/models.md.
    """
    target_values = sorted(df[target_param].unique())
    fig, axes = plt.subplots(
        1, len(target_values), figsize=(5 * len(target_values), 4), squeeze=False, gridspec_kw={"wspace": 0.4}
    )

    for i, target in enumerate(target_values):
        ax = axes[0][i]
        subset = df[df[target_param] == target]
        for nuisance in sorted(subset[nuisance_param].unique()):
            nuisance_subset = subset[subset[nuisance_param] == nuisance]
            stats = nuisance_subset.groupby("n_init")[metric_col].agg(["mean", "std"]).reset_index()
            ax.errorbar(stats["n_init"], stats["mean"], yerr=stats["std"], marker="o", capsize=3, label=str(nuisance))
        ax.set_title(f"{target_param}={target}")
        ax.set_xlabel("n_init")
        ax.set_ylabel(metric_col)
        ax.legend()

    fig.suptitle(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", y=1.05)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_interclass_distance_matrix(
    results_by_metric: dict[str, tuple[list, np.ndarray]], output_path: Path, title: str
) -> None:
    """One heatmap subplot per candidate metric (agglomerative's metric-selection pre-check,
    clustering_tuning.compute_interclass_distance_matrix - project-clustering-tuning-redesign
    memory, 26-08-26, modeled on sklearn's plot_agglomerative_clustering_metrics.html): diagonal
    cells are within-proxy-group spread, off-diagonal cells are between-group separation - a
    metric that keeps the diagonal low and off-diagonal high is a better candidate for that
    metric's own tuning_grid sweep. `results_by_metric` maps each metric name to its own
    (groups, matrix) pair from compute_interclass_distance_matrix, not computed here - this
    function only lays them out.
    """
    if not results_by_metric:
        raise ValueError("plot_interclass_distance_matrix needs at least one metric")

    metrics = list(results_by_metric)
    fig, axes = plt.subplots(
        1, len(metrics), figsize=(4.5 * len(metrics), 4), squeeze=False, gridspec_kw={"wspace": 0.5}
    )

    for i, metric in enumerate(metrics):
        groups, matrix = results_by_metric[metric]
        ax = axes[0][i]
        image = ax.imshow(matrix, cmap="viridis")
        ax.set_xticks(range(len(groups)))
        ax.set_yticks(range(len(groups)))
        ax.set_xticklabels([str(g) for g in groups], rotation=45, ha="right")
        ax.set_yticklabels([str(g) for g in groups])
        for a in range(len(groups)):
            for b in range(len(groups)):
                ax.text(b, a, f"{matrix[a, b]:.2f}", ha="center", va="center", color="white")
        ax.set_title(f"metric={metric}")
        fig.colorbar(image, ax=ax, fraction=0.046)

    fig.suptitle(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold", y=1.05)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_grouped_tuning_metrics(
    df: pd.DataFrame, x_param: str, group_param: str, metric_cols: list[str], output_path: Path, title: str
) -> None:
    """One subplot per metric in metric_cols, `x_param` on the x-axis, one line per unique
    value of `group_param` - the shared layout behind spectral's `(affinity, hyperparameter)`
    grouping and evidence_accumulation's Split-phase-`k` grouping (project-clustering-tuning-
    redesign memory, 26-08-26): both need "one line per group" instead of
    `plot_clustering_tuning_metrics`'s single line, or a heatmap.
    """
    if not metric_cols:
        raise ValueError("plot_grouped_tuning_metrics needs at least one metric column")

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
        for group_value in sorted(df[group_param].unique(), key=str):
            subset = df[df[group_param] == group_value].sort_values(x_param)
            ax.plot(subset[x_param], subset[metric_col], marker="o", markersize=4, label=str(group_value))
        ax.set_xlabel(x_param)
        ax.set_ylabel(metric_col)
        ax.legend(fontsize=7)
    for i in range(len(metric_cols), nrows * ncols):
        axes[i // ncols][i % ncols].set_visible(False)
    fig.suptitle(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_spectral_tuning(df: pd.DataFrame, param_col: str, metric_cols: list[str], output_path: Path, title: str) -> None:
    """One subplot per metric in metric_cols (`param_col`, typically `"n_clusters"`, on the
    x-axis), one line per `(affinity, hyperparameter)` combination - the tuning-plot
    counterpart of `clustering_tuning.run_spectral_affinity_aware_sweep`'s concatenated
    DataFrame (project-clustering-tuning-redesign memory, 26-08-26), where `"n_neighbors"`/
    `"gamma"` are each populated only for their own affinity's rows (`NaN` on the other
    affinity's rows, from `pd.concat`). Builds one label per row from whichever of the two is
    actually set for that row's `"affinity"` value, then delegates the actual layout to
    `plot_grouped_tuning_metrics`.
    """
    if not metric_cols:
        raise ValueError("plot_spectral_tuning needs at least one metric column")

    def _combo_label(row: pd.Series) -> str:
        if row["affinity"] == "nearest_neighbors" and "n_neighbors" in df.columns and pd.notna(row.get("n_neighbors")):
            return f"nearest_neighbors (n_neighbors={row['n_neighbors']:g})"
        if row["affinity"] == "rbf" and "gamma" in df.columns and pd.notna(row.get("gamma")):
            return f"rbf (gamma={row['gamma']:g})"
        return str(row["affinity"])

    df = df.copy()
    df["_combo_label"] = df.apply(_combo_label, axis=1)
    plot_grouped_tuning_metrics(df, param_col, "_combo_label", metric_cols, output_path, title)


def plot_consensus_matrix_heatmap(co_occurrence: np.ndarray, labels: np.ndarray, output_path: Path, title: str) -> None:
    """Monti et al. 2003's own headline visualization for evidence_accumulation
    (project-clustering-tuning-redesign memory, 26-08-26): the co-occurrence matrix
    (`consensus_clustering.run_rsc_repeats`'s output) with subjects reordered by their final
    cluster assignment (`consensus_clustering.assign_clusters_from_cooccurrence`'s output) -
    block-diagonal = confident/clean clusters at this threshold, fuzzy = an ambiguous cut.
    """
    if co_occurrence.shape[0] != co_occurrence.shape[1]:
        raise ValueError(f"co_occurrence must be square, got shape {co_occurrence.shape}")
    if len(labels) != co_occurrence.shape[0]:
        raise ValueError(f"labels has {len(labels)} entries but co_occurrence is {co_occurrence.shape[0]}x{co_occurrence.shape[0]}")

    order = np.argsort(labels)
    reordered = co_occurrence[np.ix_(order, order)]

    fig, ax = plt.subplots(figsize=(6, 5.5))
    image = ax.imshow(reordered, cmap="viridis", vmin=0, vmax=1)
    ax.set_xlabel("subjects (reordered by final cluster)")
    ax.set_ylabel("subjects (reordered by final cluster)")
    ax.set_title(title, fontsize=_SINGLE_PLOT_TITLE_FONTSIZE, fontweight="bold")
    fig.colorbar(image, ax=ax, label="co-occurrence frequency")

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
