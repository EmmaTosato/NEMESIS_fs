"""Plots of the "Valutazione del clustering" panel in src/analysis/embedding_app.py.

The numbers come from src/analysis/clustering_evaluation.py (geometric_summary); this module only
draws them: the silhouette of every subject, cluster by cluster (section 2.1 of
notebooks/post-results_analysis/clustering_evaluation.ipynb) and the mean membership vectors of a
hdbscan_soft run (section 3.2).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis.plotting import _SILHOUETTE_MIN_PANEL_SHARE, _palette_for_labels

_TEXT_COLOR = "#333"
_MUTED_COLOR = "#767676"
_GRIDLINE_COLOR = "#ececec"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)
_HEATMAP_ROW_HEIGHT = 34  # px per row of the membership heatmap
_PLOT_HEIGHT_BASE = 280  # px of the silhouette panels, plus _PLOT_HEIGHT_PER_CLUSTER for each cluster
_PLOT_HEIGHT_PER_CLUSTER = 40
_PANEL_GAP = 0.012  # of the figure height, between two panels
_AVERAGE_COLOR = "#d62728"
_FIGURE_MARGINS = dict(l=20, r=30, t=40, b=50)
_SILHOUETTE_MARGINS = {**_FIGURE_MARGINS, "l": 90}  # room for the name of each cluster, left of its panel


def build_silhouette_figure(subject_labels: np.ndarray, subject_values: np.ndarray) -> go.Figure:
    """The silhouette of every subject, one panel per cluster, stacked and sharing the silhouette axis (-1 to 1):
    the same picture as silhouette_plot.png of a production run (plotting.plot_silhouette_analysis), without the
    scatter. In a panel the subjects are sorted from the largest silhouette (top) to the smallest, in the color the
    cluster has in the embedding scatter, so the shape shows how many subjects are weak or negative (placed closer to
    another cluster than to their own). A panel is as tall as its cluster is large, with the same floor as the
    production plot, so a small cluster keeps a readable panel. A dashed red line marks the mean over all subjects
    in every panel; hovering a point gives the cluster, its size and the silhouette of that subject.

    `subject_labels`/`subject_values` are the cluster and the silhouette of each subject, noise already left out
    (SilhouetteBreakdown). Raises ValueError if they differ in length, are empty, or a silhouette is not finite."""
    labels = np.asarray(subject_labels)
    values = np.asarray(subject_values, dtype=float)
    if labels.ndim != 1 or labels.shape != values.shape:
        raise ValueError(f"subject labels and silhouettes must be 1D and of the same length, got {labels.shape} and {values.shape}")
    if labels.size == 0:
        raise ValueError("there is no subject to draw")
    if not np.isfinite(values).all():
        raise ValueError("a subject has a silhouette that is not a finite number")

    clusters = sorted(int(cluster) for cluster in np.unique(labels))
    colors = _palette_for_labels(clusters)
    shares = np.array([np.mean(labels == cluster) for cluster in clusters])
    heights = np.maximum(shares, _SILHOUETTE_MIN_PANEL_SHARE)
    figure = make_subplots(
        rows=len(clusters), cols=1, shared_xaxes=True, row_heights=(heights / heights.sum()).tolist(),
        vertical_spacing=min(_PANEL_GAP, 0.3 / max(len(clusters) - 1, 1)),
    )
    average = float(values.mean())
    for row, cluster in enumerate(clusters, start=1):
        members = np.sort(values[labels == cluster])[::-1]
        figure.add_trace(
            go.Scatter(
                x=members, y=np.arange(len(members))[::-1], mode="lines", fill="tozerox", fillcolor=colors[cluster],
                line=dict(color=colors[cluster], width=0.5), showlegend=False,
                hovertemplate=f"cluster {cluster} · {len(members)} soggetti<br>silhouette: %{{x:.3f}}<extra></extra>",
            ),
            row=row, col=1,
        )
        # simple_white gives every shape 0.3 opacity: without opacity=1 the line would be nearly invisible
        figure.add_vline(x=average, row=row, col=1, line_color=_AVERAGE_COLOR, line_width=2, line_dash="dash", opacity=1, layer="above")
        figure.add_annotation(
            text=f"cluster {cluster}", xref="x domain", yref="y domain", x=0, y=0.5, xanchor="right", xshift=-8,
            showarrow=False, row=row, col=1,
        )
        figure.update_yaxes(range=[-0.5, len(members) - 0.5], showticklabels=False, ticks="", row=row, col=1)
    figure.add_annotation(
        x=average, y=1, xref="x", yref="paper", yanchor="bottom", showarrow=False,
        text=f"media sui soggetti = {average:.2f}", font=dict(size=13, color=_AVERAGE_COLOR),
    )
    figure.update_xaxes(range=[-1, 1], gridcolor=_GRIDLINE_COLOR, zeroline=True, zerolinecolor=_MUTED_COLOR)
    figure.update_xaxes(title_text="silhouette", row=len(clusters), col=1)
    figure.update_layout(
        template="simple_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR), margin=_SILHOUETTE_MARGINS,
        height=_SILHOUETTE_MARGINS["t"] + _SILHOUETTE_MARGINS["b"] + _PLOT_HEIGHT_BASE + _PLOT_HEIGHT_PER_CLUSTER * len(clusters),
    )
    return figure


def build_mean_membership_figure(mean_vectors: pd.DataFrame) -> go.Figure:
    """Heatmap of the mean membership vectors of a hdbscan_soft run: one row per cluster of the subjects
    (and "rumore" for the noise, label -1, when there is any), one column per cluster they may belong to, the
    mean probability written in each cell. The diagonal is how firmly a cluster's own subjects belong to it;
    a large off-diagonal cell is a cluster that shares subjects with another. Rows do not sum to 1: the rest
    is the probability of being noise.

    `mean_vectors` is SoftMembership.mean_vectors (index: cluster of the subjects, columns: clusters).
    Raises ValueError if it is empty."""
    if mean_vectors.empty:
        raise ValueError("the mean membership table has no cluster to draw")
    rows = ["rumore" if int(label) == -1 else f"cluster {int(label)}" for label in mean_vectors.index]
    columns = [f"cluster {int(label)}" for label in mean_vectors.columns]
    figure = go.Figure(go.Heatmap(
        z=mean_vectors.to_numpy(), x=columns, y=rows, zmin=0, zmax=1, colorscale="Blues",
        text=[[f"{value:.2f}" for value in row] for row in mean_vectors.to_numpy()], texttemplate="%{text}",
        hovertemplate="soggetti di %{y}<br>probabilità media di stare in %{x}: %{z:.3f}<extra></extra>",
        colorbar=dict(title=dict(text="probabilità", side="top"), x=1.04, thickness=18),
        xgap=2, ygap=2,
    ))
    figure.update_xaxes(type="category", side="top", tickangle=-90, ticks="outside", ticklen=12, tickcolor="rgba(0,0,0,0)")
    figure.update_yaxes(type="category", autorange="reversed", ticks="outside", ticklen=12, tickcolor="rgba(0,0,0,0)")
    figure.update_layout(
        template="simple_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR), margin=dict(l=50, r=50, t=130, b=40),
        height=170 + _HEATMAP_ROW_HEIGHT * len(rows),
    )
    return figure
