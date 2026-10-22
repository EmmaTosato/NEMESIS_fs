"""Plots of the "Mappe delle componenti" panel in src/analysis/embedding_app.py (numbers: src/analysis/component_maps.py)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

_TEXT_COLOR = "#333"
_MUTED_COLOR = "#767676"
_GRIDLINE_COLOR = "#ececec"
_BAR_COLOR = "#a9c4e8"
_SELECTED_COLOR = "#1f5fa8"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)

# Mean reproducibility of the maps in Thiebaut de Schotten et al. 2020, from halves of 666 subjects (here the halves
# are about 2900, so the values are not directly comparable): drawn as a reference, not as a target.
PAPER_REPRODUCIBILITY = 0.813


def build_reproducibility_figure(reproducibility: np.ndarray, selected: int) -> go.Figure:
    """One bar per component: how well its map is found again in two random halves of the subjects (the
    correlation across voxels, 0 to 1), the `selected` component (1-based) darker, the paper's mean as a dashed
    line. A component whose map is not found again is not a stable pattern, however clean its map looks.

    Raises ValueError for an empty `reproducibility` or a `selected` outside 1..n."""
    n_components = len(reproducibility)
    if n_components == 0:
        raise ValueError("no component to draw")
    if not 1 <= selected <= n_components:
        raise ValueError(f"selected must be in 1..{n_components}, got {selected}")
    positions = np.arange(1, n_components + 1)
    figure = go.Figure(go.Bar(
        x=positions, y=reproducibility, marker=dict(color=[_SELECTED_COLOR if k == selected else _BAR_COLOR for k in positions]),
        hovertemplate="component %{x}<br>reproducibility: %{y:.3f}<extra></extra>", showlegend=False,
    ))
    figure.add_hline(
        y=PAPER_REPRODUCIBILITY, line=dict(color="#c0392b", dash="dash", width=1),
        annotation_text=f"paper mean ({PAPER_REPRODUCIBILITY})", annotation_position="bottom right",
    )
    figure.update_xaxes(title_text="component", type="category", gridcolor=_GRIDLINE_COLOR)
    figure.update_yaxes(title_text="reproducibility between the two halves", range=[0, 1.02], gridcolor=_GRIDLINE_COLOR)
    figure.update_layout(
        title=dict(
            text=f'<b>Map reproducibility</b><br><span style="font-size:13.5px;color:{_MUTED_COLOR}">two random halves of the subjects</span>',
            font=dict(size=17, family=_FONT_STACK, color=_TEXT_COLOR), x=0.02, xanchor="left",
        ),
        template="simple_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR), margin=dict(l=60, r=20, t=80, b=60), height=330,
    )
    return figure
