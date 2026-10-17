"""Plots of the "Valutazione del clustering" panel in src/analysis/embedding_app.py.

The numbers come from src/analysis/clustering_evaluation.py (geometric_summary); this module only
draws them: the silhouette of every cluster (section 2.1 of
notebooks/post-results_analysis/clustering_evaluation.ipynb) and the mean membership vectors of a
hdbscan_soft run (section 3.2).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.analysis.plotting import _palette_for_labels

_TEXT_COLOR = "#333"
_MUTED_COLOR = "#767676"
_GRIDLINE_COLOR = "#ececec"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)
_BAR_HEIGHT = 34
_FIGURE_MARGINS = dict(l=20, r=30, t=80, b=50)
_REQUIRED_COLUMNS = ("n", "silhouette_mean", "share_negative")


def build_silhouette_figure(clusters: pd.DataFrame) -> go.Figure:
    """One horizontal bar per cluster: its mean silhouette, from -1 to 1, in the color the cluster has
    in the embedding scatter. The label of each bar carries the cluster's size ("3 · n=412"), because
    a mean over a handful of subjects is not comparable with one over hundreds; the hover adds the
    share of its subjects with a negative silhouette (placed closer to another cluster than to their own).

    `clusters` is per_cluster_silhouette's table (index: cluster label, noise already left out).
    Raises ValueError if it is empty or lacks one of n/silhouette_mean/share_negative."""
    missing = [column for column in _REQUIRED_COLUMNS if column not in clusters.columns]
    if missing:
        raise ValueError(f"the per-cluster table lacks column(s) {missing}, got {list(clusters.columns)}")
    if clusters.empty:
        raise ValueError("the per-cluster table has no cluster to draw")

    ordered = clusters.sort_index()
    labels = [int(label) for label in ordered.index]
    colors = _palette_for_labels(labels)
    figure = go.Figure(go.Bar(
        y=[f"{label} · n={int(n)}" for label, n in zip(labels, ordered["n"])],
        x=ordered["silhouette_mean"], orientation="h",
        marker=dict(color=[colors[label] for label in labels], line=dict(color="white", width=1)),
        text=[f"{value:.2f}" for value in ordered["silhouette_mean"]], textposition="outside", cliponaxis=False,
        customdata=list(zip(ordered["n"], ordered["share_negative"] * 100)),
        hovertemplate=(
            "cluster %{y}<br>silhouette media: %{x:.3f}<br>soggetti: %{customdata[0]}"
            "<br>con silhouette negativa: %{customdata[1]:.1f}%<extra></extra>"
        ),
        showlegend=False,
    ))
    figure.update_xaxes(range=[-1, 1], title_text="silhouette media del cluster", gridcolor=_GRIDLINE_COLOR, zeroline=True, zerolinecolor=_MUTED_COLOR)
    figure.update_yaxes(type="category", autorange="reversed", title_text="cluster")
    figure.update_layout(
        title=dict(
            text=f'<b>Silhouette per cluster</b><br><span style="font-size:13.5px;color:{_MUTED_COLOR}">rumore escluso</span>',
            font=dict(size=17, family=_FONT_STACK, color=_TEXT_COLOR), x=0.02, xanchor="left",
        ),
        template="simple_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR), margin=_FIGURE_MARGINS,
        height=_FIGURE_MARGINS["t"] + _FIGURE_MARGINS["b"] + _BAR_HEIGHT * len(labels),
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
        colorbar=dict(title="probabilità"),
    ))
    figure.update_xaxes(type="category", side="top")
    figure.update_yaxes(type="category", autorange="reversed")
    figure.update_layout(
        title=dict(
            text=(
                '<b>Vettori medi di appartenenza</b><br><span style="font-size:13.5px;color:'
                f'{_MUTED_COLOR}">righe: cluster dei soggetti; colonne: cluster di appartenenza</span>'
            ),
            font=dict(size=17, family=_FONT_STACK, color=_TEXT_COLOR), x=0.02, xanchor="left",
        ),
        template="simple_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR), margin=dict(l=20, r=20, t=110, b=30),
        height=140 + _BAR_HEIGHT * len(rows),
    )
    return figure
