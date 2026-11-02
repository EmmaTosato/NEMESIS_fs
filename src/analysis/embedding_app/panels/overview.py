"""Every cluster of a run side by side: one map tile each, in a grid.

The same per-cluster map the anatomy panel builds for one cluster, drawn for all of them at
once as static images - the point is comparing the clusters, not inspecting one.
"""

from __future__ import annotations

from collections.abc import Callable

import nibabel as nib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.cluster_overview import build_overview_embedding_figure, overview_grid_plan
from src.analysis.embedding_app.anatomy import _map_texts, _style_nilearn_html
from src.analysis.embedding_app.blocks import _missing_subjects_warning
from src.analysis.embedding_app.embedding_view import cluster_options
from src.analysis.embedding_app.runs import ProductionRun
from src.analysis.embedding_app.style import _italian_figure
from src.analysis.embedding_coloring import COLOR_MODES
from src.analysis.plotting import _palette_for_labels


# --- Overview of every cluster (22-10-26) -----------------------------------------------------

# The value of the Clustering Explorer's cluster picker that draws every cluster instead of one.
ALL_CLUSTERS = "all"


def _map_tile(view: StatMapView, title: str, swatch: str, large: bool = False, warning: str | None = None) -> html.Div:
    """One map of the overview or of the walk down the tree: the cluster's name behind a square of its colour in the
    embedding, over the viewer. Sized by the view itself: the iframe has the exact pixel size nilearn gave it."""
    children = [
        html.Div(
            [html.Span(className="map-swatch", style={"background": swatch}), title],
            className="map-tile-title large" if large else "map-tile-title",
        ),
        html.Iframe(
            key=f"{title}|{view.width}", srcDoc=_style_nilearn_html(view.html),
            style={"width": f"{view.width}px", "height": f"{view.height}px"},
        ),
    ]
    if warning is not None:
        children.append(html.P(warning, className="anatomy-note"))
    return html.Div(children, className="map-tile", style={"width": f"{view.width}px"})


def _static_graph(figure: go.Figure) -> dcc.Graph:
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    return dcc.Graph(figure=_italian_figure(figure), config=config, style={"height": f"{figure.layout.height}px"})


def cluster_overview_content_for(
    heading: str,
    caption: str,
    note: str | None,
    embedding: np.ndarray | None,
    embedding_message: str | None,
    labels: np.ndarray,
    order: list[int],
    tags: dict[int, str],
    colors: dict[int, str],
    build_tile: Callable[[int, int], tuple[StatMapView, int, list[str]]],
    extra_classes: str = "",
) -> html.Div:
    """Every cluster of `labels` at once: the small embedding, drawn once, with its legend on the left and the maps of
    all the clusters on the right, two per row, as many rows as needed (the page scrolls, there are no screens).

    `build_tile(label, width)` returns (view, n_subjects, subjects without a file) for one cluster at a map width. It
    may raise ValueError: that cluster then shows its own status message and the others are still drawn. Without an
    `embedding` the maps are drawn all the same and `embedding_message` says why there is no embedding (a run whose
    embedding is not drawable, or not 2-component). Raises ValueError for no cluster at all."""
    cols, width = overview_grid_plan(len(order))
    tiles: list = []
    for label in order:
        try:
            view, n_subjects, missing = build_tile(label, width)
        except ValueError as exc:
            tiles.append(html.P(f"{tags[label]}: {exc}", className="status-message"))
            continue
        tiles.append(_map_tile(view, f"{tags[label]} (n={n_subjects})", colors[label], warning=_missing_subjects_warning(missing)))
    if embedding is None:
        left: html.Div | html.P = html.P(embedding_message, className="status-message")
    else:
        try:
            left = _static_graph(build_overview_embedding_figure(embedding, labels, order, tags, colors))
        except ValueError as exc:
            left = html.P(str(exc), className="status-message")
    return html.Div(
        className=f"cluster-overview wide-block {extra_classes}".strip(),
        children=[
            html.H3(heading, className="overview-heading"),
            html.P([caption, html.Span(note, className="anatomy-note") if note else None], className="anatomy-caption"),
            html.Div(
                className="overview-body",
                children=[html.Div(left, className="overview-embedding"), html.Div(tiles, className="overview-grid", style={"gridTemplateColumns": f"repeat({cols}, auto)"})],
            ),
        ],
    )


def all_clusters_content_for(
    run: ProductionRun,
    metadata: pd.DataFrame,
    embedding: np.ndarray | None,
    embedding_message: str | None,
    modality: str,
    map_mode: str,
    build_view: Callable[[ProductionRun, pd.DataFrame, int, int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]],
) -> html.Div:
    """What "all" in the Clustering Explorer's cluster picker draws: every cluster of the run (the noise of hdbscan
    included, as "Rumore"), the maps of `modality` ("lesion" or "sdc", with `map_mode` for the latter), in the colours of
    the run's embedding scatter. `build_view(run, metadata, label, width)` builds one cluster's view."""
    labels = metadata[COLOR_MODES["cluster_label"].column].to_numpy()
    order = cluster_options(metadata)
    palette = _palette_for_labels(order)
    tags = {label: "Noise" if label == -1 else f"Cluster {label}" for label in order}
    caption, note = _map_texts(modality, map_mode)

    def build_tile(label: int, width: int) -> tuple[StatMapView, int, list[str]]:
        view, n_subjects, _img, missing = build_view(run, metadata, label, width)
        return view, n_subjects, missing

    return cluster_overview_content_for(
        f"All clusters of the run: {len(order)}", caption, note, embedding, embedding_message, labels, order, tags, palette,
        build_tile, extra_classes="all-clusters-overview",
    )
