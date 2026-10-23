"""The overview of every cluster of a labelling at once: a small embedding with a legend and the maps of all of them.

Used by the Embedding Explorer for the "all" option of the Clustering Explorer's cluster picker (the clusters of a
production run). What is drawn here is only the embedding and the size of a map; the maps themselves come from
src.analysis.anatomical_maps.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import plotly.graph_objects as go

# Native width (pixels) of a map in the overview: two per row, or one bigger when there is a single cluster. Sized so
# that the embedding column plus two maps fit a 1700 px wide window.
OVERVIEW_MAP_WIDTH = 580
OVERVIEW_SINGLE_MAP_WIDTH = 760
OVERVIEW_COLUMNS = 2

_FONT = {"family": "system-ui, -apple-system, sans-serif", "size": 14}


def overview_grid_plan(n_clusters: int) -> tuple[int, int]:
    """(columns, native width of a map) for `n_clusters` maps: two columns, rows added downwards as needed; a single
    cluster gets one bigger map. Raises ValueError for fewer than one cluster."""
    if n_clusters < 1:
        raise ValueError(f"n_clusters={n_clusters}: there is nothing to draw")
    if n_clusters == 1:
        return 1, OVERVIEW_SINGLE_MAP_WIDTH
    return OVERVIEW_COLUMNS, OVERVIEW_MAP_WIDTH


def build_overview_embedding_figure(
    embedding: np.ndarray,
    labels: np.ndarray,
    order: Sequence[int],
    tags: Mapping[int, str],
    colors: Mapping[int, str],
    height: int = 460,
) -> go.Figure:
    """The embedding, one trace per cluster in `order`, named `tags[label]` in the legend and coloured `colors[label]`.
    The sizes are not in the legend: they are in the hover and in the title of each map. Points are SVG, not WebGL:
    a page holds many figures and browsers allow only a few WebGL contexts. Raises ValueError for an embedding that
    is not 2-component (a larger one is never sliced, lessons learned #16) or has non-finite values, for labels that do not match its rows, or
    for a label in `order` without a tag, a colour or a subject."""
    if embedding.ndim != 2 or embedding.shape[1] != 2:
        raise ValueError(f"the embedding has shape {embedding.shape}: only 2 components can be drawn, never a slice of more")
    if not np.isfinite(embedding).all():
        raise ValueError("the embedding has non-finite coordinates: a point would silently not be drawn")
    if len(labels) != len(embedding):
        raise ValueError(f"{len(labels)} labels for an embedding of {len(embedding)} rows")
    if len(set(order)) != len(order):
        raise ValueError(f"the clusters to draw repeat a label: {list(order)}")
    present = set(np.unique(labels).tolist())
    for label in order:
        if label not in present:
            raise ValueError(f"cluster {label!r} has no subject in the labels")
        if label not in tags or label not in colors:
            raise ValueError(f"cluster {label!r} has no tag or no colour")

    fig = go.Figure()
    for label in order:
        members = np.flatnonzero(labels == label)
        fig.add_trace(
            go.Scatter(
                x=embedding[members, 0], y=embedding[members, 1], mode="markers", name=tags[label],
                marker={"size": 3, "color": colors[label]}, hovertemplate=f"{tags[label]} (n={len(members)})<extra></extra>",
            )
        )
    fig.update_xaxes(title_text="dim 1", title_standoff=4, zeroline=False)
    fig.update_yaxes(title_text="dim 2", title_standoff=4, zeroline=False)
    fig.update_layout(
        template="plotly_white", font=_FONT, showlegend=True, height=height, margin={"l": 44, "r": 6, "t": 6, "b": 120},
        legend={"orientation": "h", "yanchor": "top", "y": -0.15, "x": 0, "font": {"size": 13}, "itemsizing": "constant"},
    )
    return fig
