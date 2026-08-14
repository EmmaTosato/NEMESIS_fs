"""Builds an "Understanding UMAP" style HTML report from already-computed
dim_reduction tuning output - no refit, read-only over tuning_results.csv/
embeddings.npz/metadata.csv, same convention as scripts/replot_dim_reduction.py.

Replicates pair-code.github.io/understanding-umap's Figures 2, 4, 5 and 7
LAYOUT (not their content - our own lesion embeddings, not toy datasets) as
one HTML page per metric leaf (see build_leaf_page):
  - Figure 1 here / PAIR's Figure 4: NxM n_neighbors/min_dist grid (build_grid_figure)
  - Figure 2 here / PAIR's Figure 5: dual-slider explorer (build_slider_section)
  - Figure 3 here: UMAP 2D vs UMAP 3D, same dual-slider mechanism (build_2d_vs_3d_section) -
    no PAIR figure of its own, extends Figure 5's own mechanism along a new axis
  - Figure 4 here / PAIR's Figure 7: 2-row UMAP-vs-t-SNE comparison grid (build_comparison_grid_figure)
  - Figure 5 here / PAIR's Figure 6: UMAP-vs-t-SNE dual-slider, live (build_method_comparison_slider_section)

UMAP-only figures come first, the UMAP-vs-t-SNE comparison comes last - not
PAIR's own interleaved narrative order, on request. PAIR's own Figure 2
(side-by-side 3D UMAP/t-SNE scatter) has no equivalent here: it needs a real
t-SNE sweep with an n_components=3 leaf to pair against the real 3D UMAP
leaf, which doesn't exist yet (today's t-SNE tuning runs are perplexity-only,
always 2D) - add a build_3d_comparison_section-style function once one does,
rather than pairing real UMAP 3D with no t-SNE 3D counterpart.

Key structural point, taken from the real page's own CSS
(src/visualizations/hyperparameters_visualization/components/Visualization.svelte,
github.com/PAIR-code/understanding-umap) and confirmed against a screenshot:
the figure is a two-column flex row - `.figures-container` (the grid) on the
LEFT, `.menu` (picker + description text) on the RIGHT, with the italic
"Figure N: ..." caption centered BELOW the whole thing. Figures 1 and 4 (the
widest ones, once both were switched to the full 1150-subject cohort)
instead stack the menu BELOW the grid via the `.below-menu` modifier, so the
figure stays centered with equal margins instead of the side-by-side row
overflowing the page and squeezing the menu asymmetrically - see the CSS
comments on `.container.below-menu` for the measured-live reasoning. Plotly
draws only the scatter cells themselves, with all of its own chrome (titles,
margins, tick labels, gridlines) stripped - the layout chrome is plain
HTML/CSS around it.

One HTML file per nested-param leaf (metric=dice, metric=euclidean today),
every figure for that leaf stacked as sections inside that same file.
"""

from __future__ import annotations

import itertools
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis.plotting import _CATEGORICAL_PALETTE, _NOISE_COLOR

logger = logging.getLogger(__name__)

# production's own base_params value for min_dist whenever it's not the swept
# axis (config/registry/params_reduction.json's umap.params) - t-SNE has no
# min_dist-like 2nd free parameter to match against, so every UMAP cell in
# the Figure 4 comparison grid is read at this one fixed min_dist, varying
# only n_neighbors (mirrors PAIR's own Figure 7, which varies exactly one
# parameter per method).
UMAP_BASE_MIN_DIST = 0.0
# "none" first: the neutral single-color view, matching plot_embedding_2d's
# embedding_plot_unico.png (no grouping, just the shape of the embedding) -
# the default here as it is there, with the color_by modes as opt-ins on top.
COLOR_BY_MODES = ["none", "dataset", "side", "volume", "nihss"]

# _CATEGORICAL_PALETTE reused directly from plotting.py's import above (not
# re-declared here) so the two never drift apart - see plotting.py's own
# comment for the CVD-safe validation behind this palette/neutral-gray choice.
_MISSING_CATEGORY_COLOR = _NOISE_COLOR
_MISSING_CATEGORY_LABEL = "unknown"
CONTINUOUS_COLORSCALE = "Viridis"
# plot_embedding_2d draws its uncolored scatter with matplotlib's default
# first color (#1f77b4) at alpha 0.5 - same two values here, so the "none"
# view matches embedding_plot_unico.png rather than inventing a blue.
_NEUTRAL_COLOR = "#1f77b4"
_NEUTRAL_OPACITY = 0.5

# Per-cell size for the NxM grid (Figure 1) and the 2-row comparison grid
# (Figure 4). PAIR's own toy-dataset cells are ~88x92px holding ~300 points
# (measured live via getComputedStyle on the real page) - our own lesion
# cohort (1150 subjects) is ~3.8x denser, so a plain 105px cell (an earlier,
# untuned guess) left individual points illegible, just a blob. Sized instead
# to match PAIR's own point density (~0.0425 pts/px^2): 1150 points at that
# density needs a cell around 165px.
_CELL_PX = 165
# PAIR's own single-embedding slider (Figure 5, mammoth) renders at 440x440
# (measured live), not a smaller guess - matched here for Figures 2/3/5,
# which all render our own real 1150-subject cohort.
_CANVAS_PX = 440
# 3D scatter needs its own (smaller, more transparent) marker than the 2D
# default (size 6, opacity from default_colors) - a 3D point cloud collapses
# depth onto the same 2D screen a 2D scatter already occupies fully, so the
# SAME marker size overlaps far more there than in 2D at an equal subject
# count. Smaller size cuts the per-point footprint; the extra opacity cut on
# top lets overlapping points show through as a density gradient instead of
# a flat blob (same idea PAIR's own scatter-gl uses via additive WebGL
# blending - Plotly's Scatter3d has no blending mode, alpha is the closest
# lever).
_MARKER_SIZE_3D = 3
_MARKER_OPACITY_FACTOR_3D = 0.7
# rgba(0,0,0,0.1) is PAIR's own .demo-data cell border (measured via
# getComputedStyle on the live page - the UA-less inline style Svelte sets,
# no CSS source for it), not a flat gray hex.
_GRID_BORDER = "rgba(0,0,0,0.1)"
# PAIR's own text color (getComputedStyle color on .figures-container/
# .caption/.menu = rgb(51,51,51)), not #222 - every text color below
# inherits from body, single source of truth.
_TEXT_COLOR = "#333"
# hyperparameters_visualization/components/Visualization.svelte's own
# .left-column-spacer height (flat 40px in PAIR's source, not computed from
# header+label height) - kept as one named constant since the header/label
# CSS below reuses the same numbers deliberately.
_MIN_DIST_HEADER_H = 30
_MIN_DIST_LABELS_H = 18
_LEFT_COLUMN_SPACER_H = _MIN_DIST_HEADER_H + _MIN_DIST_LABELS_H

_METADATA_COLUMN_BY_MODE = {"dataset": "dataset", "side": "lesion_side", "volume": "lesion_volume_voxels", "nihss": "nihss"}
_CATEGORICAL_MODES = {"dataset", "side"}
# Which continuous modes are drawn on a log scale, mirroring
# embedding_coloring.COLOR_MODES' own log_scale flag: volume is heavily
# right-skewed (a few large-lesion outliers otherwise flatten everyone else
# into one dark color - confirmed on the real 1150-subject cohort), nihss is
# not. plotting.py gets this via matplotlib's LogNorm; Plotly has no
# equivalent norm, so the values themselves are log10'd before being handed
# over - same visual mapping, since no colorbar is drawn on these cells.
_LOG_SCALE_MODES = {"volume"}


def _combo_key(row: pd.Series, key_order: list[str]) -> str:
    """Same string format as src.pipeline.dim_reduction._combo_key
    (the writer of embeddings.npz's own keys: 'metric=X,n_neighbors=Y,...'),
    kept as a separate implementation here rather than imported - that one
    takes an in-memory (keys, combo tuple) pair from a live sweep, this one
    rebuilds the identical string from a tuning_results.csv row already read
    back off disk; sharing a signature between the two would force one side
    into an awkward call shape for no real benefit.
    """
    return ",".join(f"{k}={row[k]}" for k in key_order)


def _read_base_n_components(tuning_dir: Path) -> int:
    config_md = (tuning_dir / "config.md").read_text()
    match = re.search(r"```json\n(.*?)\n```", config_md, re.DOTALL)
    if match is None:
        raise ValueError(f"{tuning_dir}/config.md has no fenced ```json``` block - can't read base_params.n_components")
    return json.loads(match.group(1))["base_params"]["n_components"]


def _categorical_color_map(categories) -> dict:
    """category -> hex, cycling _CATEGORICAL_PALETTE in the given (already
    sorted) category order - the fixed neutral gray always goes to
    _MISSING_CATEGORY_LABEL, never a palette color, so it can't be mistaken
    for a real category. Factored out of _color_values_for_mode so the
    color_by legend (_legend_html_for_mode) builds its chips from the exact
    same mapping the grid itself was colored with, rather than a second,
    independently-cycled copy that could drift if ever called in a different
    order.
    """
    colors = itertools.cycle(_CATEGORICAL_PALETTE)
    color_map = {}
    for cat in categories:
        color_map[cat] = _MISSING_CATEGORY_COLOR if cat == _MISSING_CATEGORY_LABEL else next(colors)
    return color_map


# 6-stop approximation of Plotly/matplotlib's own Viridis colorscale (the
# actual stops Plotly ships), used only for the continuous-mode legend's CSS
# gradient bar - the grid/slider markers themselves are colored by Plotly's
# real Viridis (via colorscale="Viridis" in _color_values_for_mode), this is
# a static visual stand-in since a CSS linear-gradient can't call into
# Plotly's own colorscale interpolation.
_VIRIDIS_CSS_STOPS = "#440154, #414487, #2a788e, #22a884, #7ad151, #fde725"


def _legend_html_for_mode(metadata: pd.DataFrame, mode: str) -> str:
    """A small legend for whichever color_by mode is active - empty for
    "none" (no color meaning to explain), one chip per category for
    dataset/side (color from the exact same _categorical_color_map the grid
    itself uses), a Viridis gradient bar with min/max labels for volume/nihss
    (log10-scaled range for volume, matching how the grid itself is colored -
    see _LOG_SCALE_MODES). Swapped into the page's #legend div by setColor()
    every time the color_by picker changes, alongside the grid's own restyle.
    """
    if mode == "none":
        return ""

    column = _METADATA_COLUMN_BY_MODE[mode]
    if mode in _CATEGORICAL_MODES:
        categories = metadata[column].astype("category").cat.categories
        color_map = _categorical_color_map(categories)
        chips = "".join(f'<div class="category-chip" style="background-color:{color_map[c]}">{c}</div>' for c in categories)
        return f'<div class="categories">{chips}</div>'

    values = metadata[column].to_numpy(dtype=float)
    finite = values[~np.isnan(values)]
    lo, hi = float(finite.min()), float(finite.max())
    unit = " voxels" if mode == "volume" else ""
    return f"""<div class="gradient-legend">
      <span>{lo:.3g}{unit}</span>
      <div class="gradient-bar" style="background: linear-gradient(to right, {_VIRIDIS_CSS_STOPS});"></div>
      <span>{hi:.3g}{unit}</span>
    </div>"""


def _color_values_for_mode(metadata: pd.DataFrame, mode: str) -> dict:
    """marker.color/colorscale/opacity for one view: "none" is the neutral
    single-color one (plot_embedding_2d's look), categorical modes map each
    category to a fixed hex, continuous modes hand over numeric values (log10
    for the log_scale ones, see _LOG_SCALE_MODES) plus a colorscale.
    """
    if mode == "none":
        return {"color": _NEUTRAL_COLOR, "colorscale": None, "opacity": _NEUTRAL_OPACITY}

    column = _METADATA_COLUMN_BY_MODE[mode]
    if mode in _CATEGORICAL_MODES:
        categories = metadata[column].astype("category")
        color_map = _categorical_color_map(categories.cat.categories)
        return {"color": categories.map(color_map).tolist(), "colorscale": None, "opacity": 1.0}

    values = metadata[column].to_numpy(dtype=float)
    if mode in _LOG_SCALE_MODES:
        # LogNorm's own domain rule: non-positive values have no place on a log
        # scale. plotting.py leans on matplotlib to mask them; here they'd
        # silently become -inf/NaN, so reject them explicitly instead.
        positive = values[~np.isnan(values)]
        if (positive <= 0).any():
            raise ValueError(f"mode {mode!r} is log-scaled but has non-positive values - cannot map onto a log color scale")
        values = np.log10(values)
    return {"color": values.tolist(), "colorscale": CONTINUOUS_COLORSCALE, "opacity": 1.0}


def build_grid_figure(
    leaf_dir: Path, embeddings: dict, metadata: pd.DataFrame, default_mode: str = "none", cell_px: int = _CELL_PX
) -> tuple[go.Figure, list, list]:
    """Bare NxM scatter grid - no titles/labels/margins of its own (all of
    that is HTML/CSS around it, see _build_grid_block_html). Cells share a
    continuous 1px border, like the table-looking grid in the original.

    default_mode picks the INITIAL coloring only - always "none" today (the
    single neutral color, matching plot_embedding_2d) since build_leaf_page's
    color_by picker lets a human switch it afterwards. Kept as a real
    parameter, same as build_slider_section's own default_mode, rather than
    hardcoded "none" inline - a picker-less caller could still want a
    pre-colored default.
    """
    results = pd.read_csv(leaf_dir / "tuning_results.csv")
    key_order = [c for c in results.columns if c != "trustworthiness"]
    row_values = sorted(results["n_neighbors"].unique())
    col_values = sorted(results["min_dist"].unique())
    default_colors = _color_values_for_mode(metadata, default_mode)

    fig = make_subplots(rows=len(row_values), cols=len(col_values), horizontal_spacing=0, vertical_spacing=0)
    axis_kwargs = {
        "showticklabels": False, "showgrid": False, "zeroline": False, "ticks": "",
        "showline": True, "linecolor": _GRID_BORDER, "linewidth": 1, "mirror": True,
    }
    for r, nn in enumerate(row_values, start=1):
        for c, md in enumerate(col_values, start=1):
            match = results[(results["n_neighbors"] == nn) & (results["min_dist"] == md)]
            if match.empty:
                continue
            points = embeddings[_combo_key(match.iloc[0], key_order)]
            fig.add_trace(
                go.Scattergl(
                    x=points[:, 0], y=points[:, 1], mode="markers",
                    marker={"size": 3, "color": default_colors["color"],
                            "colorscale": default_colors["colorscale"],
                            "opacity": default_colors["opacity"], "line": {"width": 0}},
                    text=metadata["subject_id"], hovertemplate="%{text}<extra></extra>", showlegend=False,
                ),
                row=r, col=c,
            )
            fig.update_xaxes(row=r, col=c, **axis_kwargs)
            fig.update_yaxes(row=r, col=c, **axis_kwargs)

    fig.update_layout(
        width=cell_px * len(col_values), height=cell_px * len(row_values),
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
    )
    return fig, row_values, col_values


def _build_grid_block_html(
    leaf_dir: Path,
    embeddings: dict,
    metadata: pd.DataFrame,
    div_id: str,
    default_mode: str = "none",
    include_plotlyjs: bool = True,
    cell_px: int = _CELL_PX,
) -> tuple[str, int]:
    """The whole `.figures-container` block for one leaf's Figure-1-style
    grid: min_dist/n_neighbors chrome (left-column, headers, labels) wrapping
    the bare Plotly grid from build_grid_figure - everything build_leaf_page
    needs for its own Figure 1, factored out of it for readability. Returns
    (html, n_cells) - n_cells is needed by the caller's own color-restyle JS
    (one array entry per grid cell, see setColor).
    """
    grid_fig, row_values, col_values = build_grid_figure(leaf_dir, embeddings, metadata, default_mode, cell_px=cell_px)
    grid_html = grid_fig.to_html(
        full_html=False, include_plotlyjs=include_plotlyjs, div_id=div_id, config={"displayModeBar": False}
    )
    col_labels = "".join(f"<div style='width:{cell_px}px'>{v}</div>" for v in col_values)
    row_labels = "".join(f"<div style='height:{cell_px}px'>{v}</div>" for v in row_values)
    grid_w = cell_px * len(col_values)
    grid_h = cell_px * len(row_values)

    html = f"""<div class="figures-container">
      <div class="left-column">
        <div class="left-column-spacer"></div>
        <div class="left-column-content" style="height:{grid_h}px">
          <div class="left-column-header" style="height:{grid_h}px">
            <div class="n-neighbors-header">n_neighbors</div>
          </div>
          <div class="left-column-labels" style="height:{grid_h}px">{row_labels}</div>
        </div>
      </div>
      <div>
        <div class="min-dist-header" style="width:{grid_w}px">min_dist</div>
        <div class="min-dist-labels" style="width:{grid_w}px">{col_labels}</div>
        {grid_html}
      </div>
    </div>"""
    return html, len(grid_fig.data)


def build_comparison_grid_figure(
    tsne_results: pd.DataFrame,
    tsne_embeddings: dict,
    umap_results: pd.DataFrame,
    umap_embeddings: dict,
    metadata: pd.DataFrame,
    column_values: list[float],
    default_mode: str = "none",
    cell_px: int = _CELL_PX,
) -> go.Figure:
    """A 2-row bare scatter grid - row 1 = t-SNE by perplexity, row 2 = UMAP
    by n_neighbors (at UMAP_BASE_MIN_DIST) - no titles/labels/margins of its
    own, same as build_grid_figure, all chrome is HTML/CSS around it (see
    _build_comparison_block_html).

    column_values is the UNION of both methods' own real swept values - a
    value only one method actually swept leaves the OTHER row's cell at that
    column empty (no fabricated data), same convention as build_grid_figure's
    own `if match.empty: continue`.
    """
    default_colors = _color_values_for_mode(metadata, default_mode)
    fig = make_subplots(rows=2, cols=len(column_values), horizontal_spacing=0, vertical_spacing=0)
    axis_kwargs = {
        "showticklabels": False, "showgrid": False, "zeroline": False, "ticks": "",
        "showline": True, "linecolor": _GRID_BORDER, "linewidth": 1, "mirror": True,
    }

    tsne_key_order = [c for c in tsne_results.columns if c != "trustworthiness"]
    umap_key_order = [c for c in umap_results.columns if c != "trustworthiness"]

    for c, value in enumerate(column_values, start=1):
        for row_idx, (embeddings, key_order, match) in enumerate(
            [
                (tsne_embeddings, tsne_key_order, tsne_results[tsne_results["perplexity"] == value]),
                (
                    umap_embeddings,
                    umap_key_order,
                    umap_results[(umap_results["n_neighbors"] == value) & (umap_results["min_dist"] == UMAP_BASE_MIN_DIST)],
                ),
            ],
            start=1,
        ):
            fig.update_xaxes(row=row_idx, col=c, **axis_kwargs)
            fig.update_yaxes(row=row_idx, col=c, **axis_kwargs)
            if match.empty:
                continue
            points = embeddings[_combo_key(match.iloc[0], key_order)]
            fig.add_trace(
                go.Scattergl(
                    x=points[:, 0], y=points[:, 1], mode="markers",
                    marker={"size": 3, "color": default_colors["color"],
                            "colorscale": default_colors["colorscale"],
                            "opacity": default_colors["opacity"], "line": {"width": 0}},
                    text=metadata["subject_id"], hovertemplate="%{text}<extra></extra>", showlegend=False,
                ),
                row=row_idx, col=c,
            )

    fig.update_layout(
        width=cell_px * len(column_values), height=cell_px * 2,
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
    )
    return fig


def _build_comparison_block_html(
    metric: str,
    tsne_tuning_dir: Path,
    umap_leaf_dir: Path,
    tsne_embeddings: dict,
    umap_embeddings: dict,
    metadata: pd.DataFrame,
    div_id: str,
    include_plotlyjs: bool = True,
    cell_px: int = _CELL_PX,
) -> tuple[str, int, dict]:
    """The whole `.figures-container` block for Figure 4 (t-SNE-vs-UMAP
    comparison at one metric) - same factoring purpose as
    _build_grid_block_html for Figure 1. Returns (html, n_cells, info) -
    info carries the swept-value lists/gaps the caller's own menu/caption
    text needs (perplexity_values, n_neighbors_values, missing_tsne,
    missing_umap), so build_leaf_page doesn't have to re-derive them.

    `umap_leaf_dir` is the already-resolved leaf directory holding
    tuning_results.csv, not `umap_tuning_dir / f"metric={metric}"`
    reconstructed internally - the UMAP tuning run nests an extra
    n_components=2/ level the (flat) t-SNE run doesn't, same reasoning as
    build_slider_section's own `leaf_dir` parameter (see its docstring).

    Raises ValueError if `metric` has no t-SNE leaf - every UMAP metric
    happens to have a t-SNE counterpart today, but that's a fact about
    today's registry, not something to assume silently forever.
    """
    tsne_leaf = tsne_tuning_dir / f"metric={metric}"
    if not tsne_leaf.exists():
        raise ValueError(
            f"no t-SNE leaf for metric={metric!r} in {tsne_tuning_dir} - Figure 4 needs a t-SNE sweep "
            "at the same metric as this UMAP leaf to compare against"
        )
    tsne_results = pd.read_csv(tsne_leaf / "tuning_results.csv")
    umap_results = pd.read_csv(umap_leaf_dir / "tuning_results.csv")

    perplexity_values = sorted(tsne_results["perplexity"].unique().tolist())
    n_neighbors_values = sorted(umap_results["n_neighbors"].unique().tolist())
    column_values = sorted(set(perplexity_values) | set(n_neighbors_values))

    grid_fig = build_comparison_grid_figure(
        tsne_results, tsne_embeddings, umap_results, umap_embeddings, metadata, column_values, cell_px=cell_px
    )
    grid_html = grid_fig.to_html(
        full_html=False, include_plotlyjs=include_plotlyjs, div_id=div_id, config={"displayModeBar": False}
    )
    grid_w = cell_px * len(column_values)
    grid_h = cell_px * 2
    col_labels = "".join(f"<div style='width:{cell_px}px'>{v}</div>" for v in column_values)

    html = f"""<div class="figures-container">
      <div class="left-column">
        <div class="left-column-spacer" style="height:{_LEFT_COLUMN_SPACER_H}px"></div>
        <div class="left-column-content" style="height:{grid_h}px">
          <div class="left-column-labels plain" style="height:{grid_h}px">
            <div class="method-label" style="height:{cell_px}px">t-SNE</div>
            <div class="method-label" style="height:{cell_px}px">UMAP</div>
          </div>
        </div>
      </div>
      <div>
        <div class="hyperparam-header" style="width:{grid_w}px">n_neighbors (UMAP) / perplexity (t-SNE)</div>
        <div class="hyperparam-labels" style="width:{grid_w}px">{col_labels}</div>
        {grid_html}
      </div>
    </div>"""

    info = {
        "perplexity_values": perplexity_values,
        "n_neighbors_values": n_neighbors_values,
        "missing_tsne": sorted(set(column_values) - set(perplexity_values)),
        "missing_umap": sorted(set(column_values) - set(n_neighbors_values)),
    }
    return html, len(grid_fig.data), info


def build_2d_vs_3d_section(
    metric: str,
    umap_tuning_dir: Path,
    umap_embeddings: dict,
    metadata: pd.DataFrame,
    instance_prefix: str,
    include_plotlyjs: bool = False,
) -> str:
    """UMAP 2D vs UMAP 3D, side by side - PAIR's own Figure 5 text ("UMAP
    projections ... into 2 dimensions, with various settings for the
    n_neighbors and min_dist parameters") applied to a dimensionality
    comparison instead: same dual-slider mechanism (build_slider_section),
    same n_neighbors/min_dist sliders, but now driving TWO independent
    embeddings (a real 2D sweep and a real 3D sweep - not a slice of one or
    the other, see docs/dev/design_patterns.md / lessons_learned.md #16) so
    the same slider settings can be compared at both dimensionalities at
    once. Not a PAIR figure of its own - PAIR's page never compares 2D vs 3D
    for the SAME method, only different methods at a fixed dimensionality -
    but reuses the exact same interaction mechanism PAIR already established.

    `umap_tuning_dir` is expected shaped `metric=X/n_components=Y/`
    (nested_params=["metric", "n_components"]) - both the 2D and 3D leaves
    for this metric live under the SAME tuning_dir/embeddings, unlike
    build_method_comparison_slider_section's umap-vs-tsne panels (two
    genuinely separate methods/runs).
    """
    leaf_2d = umap_tuning_dir / f"metric={metric}" / "n_components=2"
    leaf_3d = umap_tuning_dir / f"metric={metric}" / "n_components=3"
    if not leaf_3d.exists():
        raise ValueError(
            f"no UMAP 3D leaf for metric={metric!r} in {umap_tuning_dir} - build_2d_vs_3d_section needs a "
            "3D sweep (n_components=3) at the same metric as this 2D leaf to compare against"
        )

    html_2d, desc_2d, _ = build_slider_section(
        leaf_2d, umap_embeddings, metadata, free_params=["n_neighbors", "min_dist"],
        instance_id=f"2d-{instance_prefix}", metric=metric, title="UMAP (2D)", include_plotlyjs=include_plotlyjs,
        canvas_px=_CANVAS_PX,
    )
    html_3d, desc_3d, _ = build_slider_section(
        leaf_3d, umap_embeddings, metadata, free_params=["n_neighbors", "min_dist"],
        instance_id=f"3d-{instance_prefix}", metric=metric, title="UMAP (3D)", include_plotlyjs=False,
        canvas_px=_CANVAS_PX,
    )
    return f"""<div class="panel-row">
      <div class="slider-panel">{html_2d}{desc_2d}</div>
      <div class="slider-panel">{html_3d}{desc_3d}</div>
    </div>"""


def build_method_comparison_slider_section(
    metric: str,
    umap_leaf_dir: Path,
    umap_embeddings: dict,
    tsne_tuning_dir: Path,
    tsne_embeddings: dict,
    metadata: pd.DataFrame,
    instance_prefix: str,
    include_plotlyjs: bool = False,
) -> str:
    """Two independent slider panels side by side - UMAP (n_neighbors +
    min_dist) left, t-SNE (perplexity) right - drag either independently,
    same subjects, both in 2D. Distinct from Figure 4 (a STATIC grid over
    every combination at once, not draggable) - both stay on the page
    because they answer different questions (grid: survey everything at a
    glance; sliders: watch ONE setting move both projections live).

    `umap_leaf_dir` is the already-resolved leaf directory (see
    _build_comparison_block_html's own docstring for why).
    """
    tsne_leaf = tsne_tuning_dir / f"metric={metric}"
    if not tsne_leaf.exists():
        raise ValueError(
            f"no t-SNE leaf for metric={metric!r} in {tsne_tuning_dir} - build_method_comparison_slider_section "
            "needs a t-SNE sweep at the same metric as this UMAP leaf to compare against"
        )

    umap_html, umap_desc, _ = build_slider_section(
        umap_leaf_dir, umap_embeddings, metadata, free_params=["n_neighbors", "min_dist"],
        instance_id=f"cmp-umap-{instance_prefix}", metric=metric, title="UMAP", include_plotlyjs=include_plotlyjs,
        canvas_px=_CANVAS_PX,
    )
    tsne_html, tsne_desc, _ = build_slider_section(
        tsne_leaf, tsne_embeddings, metadata, free_params=["perplexity"],
        instance_id=f"cmp-tsne-{instance_prefix}", metric=metric, title="t-SNE", include_plotlyjs=False,
        canvas_px=_CANVAS_PX,
    )
    return f"""<div class="panel-row">
      <div class="slider-panel">{umap_html}{umap_desc}</div>
      <div class="slider-panel">{tsne_html}{tsne_desc}</div>
    </div>"""


def build_slider_section(
    leaf_dir: Path,
    embeddings: dict,
    metadata: pd.DataFrame,
    free_params: list[str],
    instance_id: str,
    metric: str,
    default_mode: str = "none",
    include_plotlyjs: bool = True,
    title: str | None = None,
    canvas_px: int = _CANVAS_PX,
) -> tuple[str, str, str]:
    """One view, N independent sliders (one per entry in `free_params`, e.g.
    ["n_neighbors", "min_dist"] for UMAP or just ["perplexity"] for t-SNE),
    animated 500ms ease-in-out-QUAD tween on any slider's change - same
    mechanism AND same easing as PAIR's own hand-written Tween class
    (mammoth_visualization/js/tween.js: TWEEN_DURATION=500, easeInOutQuad -
    Plotly's own 'cubic-in-out' is a different curve). PAIR doesn't use
    Plotly's own frame/slider widget for this either (it's Svelte on:input
    handlers calling their Tween directly) - Plotly's built-in
    `layout.sliders` only drives ONE degree of freedom per slider through a
    fixed frame sequence, which can't represent "N independent sliders
    jointly selecting one of an N-D grid of combinations" without a slider
    position depending on every OTHER slider's current value too. Same
    approach here: plain HTML range inputs + a JS handler that looks up the
    right precomputed embedding and calls `Plotly.animate` directly - no
    Plotly `sliders`/`frames` on this figure.

    2D vs 3D is auto-detected from the embeddings' own column count (2 or 3)
    - draws go.Scatter/xaxis+yaxis for 2D, go.Scatter3d/scene for 3D (with a
    thin colored zeroline per axis, not a bare Plotly default cube) - the
    caller doesn't have to know or declare which, it's a property of the
    embedding actually being plotted, not of this function's caller.

    Combinations are keyed by a joined tuple of PER-SLIDER INDICES (e.g.
    "0_2"), not by the swept values themselves - a float like 0.0/1.0
    stringifies as "0"/"1" in JS but "0.0"/"1.0" in Python f-strings, which
    would silently break the lookup for exactly those two boundary values;
    indices sidestep the mismatch entirely.

    `title`, if given, renders as a bold centered `.dual-slider-title` above
    the plot.

    `metric` is taken as an explicit string, not derived from `leaf_dir`'s
    own path (e.g. `leaf_dir.name`) - callers pass leaf directories at two
    different nesting depths (`metric=X/` for a flat tuning run,
    `metric=X/n_components=Y/` for one nested on n_components too), so a
    fixed number of `.parent` hops would silently read the wrong path
    segment for whichever depth wasn't the one last tested against.

    Each combo is an INDEPENDENT UMAP/t-SNE fit with its own arbitrary
    coordinate scale - n_neighbors=30's embedding does not live anywhere near
    n_neighbors=5's. Plotly.animate only swaps the DATA arrays, it never
    recomputes axis autorange the way a fresh Plotly.newPlot would - so
    without an explicit range update pushed through the SAME animate call,
    every combo after the first renders against the FIRST combo's axis
    range: a combo whose spread doesn't overlap the first at all renders
    completely off-canvas, blank, with no error (confirmed on real data - a
    n_neighbors=30 combo at x=[18.4,22.4] against an initial x-range of
    [1.79,13.31]). Fixed by computing each combo's own padded range
    (`combo_ranges`, `_padded_range`, 7% padding matching Plotly's own
    autorange margin) and pushing it through Plotly.animate's own `layout`
    alongside `data` (see `updateSlider_` below) - same as PAIR's mammoth
    demo re-fitting its camera/scale to each frame rather than reusing the
    first.
    """
    if not free_params:
        raise ValueError("build_slider_section needs at least one entry in free_params")
    results = pd.read_csv(leaf_dir / "tuning_results.csv")
    key_order = [c for c in results.columns if c != "trustworthiness"]
    # .item() unwraps numpy int64/float64 to plain Python types - json.dumps
    # below rejects numpy scalars outright.
    options = {p: [v.item() for v in sorted(results[p].unique())] for p in free_params}
    default_colors = _color_values_for_mode(metadata, default_mode)
    div_id = f"slider-{instance_id}"
    # instance_id (e.g. "2d-dice", "cmp-umap-euclidean") is safe inside an HTML
    # id attribute or a JS string literal (getElementById(...)) - hyphens are
    # fine there - but NOT as part of a bare JS identifier (`const X_2d-dice`
    # parses as `X_2d - dice`, a subtraction, not a name: "missing initializer"
    # at runtime). js_id is the identifier-safe version, used only for
    # const/function names below; every HTML id/getElementById string keeps
    # using instance_id as-is.
    js_id = re.sub(r"\W", "_", instance_id)

    combo_points = {}
    for idx_tuple in itertools.product(*(range(len(options[p])) for p in free_params)):
        match = results
        for p, idx in zip(free_params, idx_tuple):
            match = match[match[p] == options[p][idx]]
        if match.empty:
            continue
        points = embeddings[_combo_key(match.iloc[0], key_order)]
        combo_points["_".join(map(str, idx_tuple))] = [[round(float(c), 4) for c in row] for row in points]

    first_key = "_".join("0" for _ in free_params)
    if first_key not in combo_points:
        raise ValueError(
            f"leaf {leaf_dir} has no combination at the first index of every free_param {free_params} "
            "- every slider's own option list must include at least the value the first index points to"
        )
    first_points = combo_points[first_key]
    n_dims = len(first_points[0])
    if n_dims not in (2, 3):
        raise ValueError(f"build_slider_section supports 2D or 3D embeddings, got {n_dims} columns")

    _AXIS_PAD_FRAC = 0.07  # matches Plotly's own autorange padding, measured live

    def _padded_range(values: list[float]) -> list[float]:
        lo, hi = min(values), max(values)
        pad = (hi - lo) * _AXIS_PAD_FRAC if hi > lo else 1.0
        return [round(lo - pad, 4), round(hi + pad, 4)]

    axis_names = ["x", "y", "z"][:n_dims]
    combo_ranges = {
        key: {axis: _padded_range([p[i] for p in points]) for i, axis in enumerate(axis_names)}
        for key, points in combo_points.items()
    }

    first_range = combo_ranges[first_key]
    marker = {"size": 6, "color": default_colors["color"], "opacity": default_colors["opacity"], "line": {"width": 0}}
    if n_dims == 2:
        fig = go.Figure(data=[go.Scatter(
            x=[p[0] for p in first_points], y=[p[1] for p in first_points], mode="markers",
            marker=marker, text=metadata["subject_id"], hovertemplate="%{text}<extra></extra>",
        )])
        # Explicit range (our own _padded_range, not Plotly's client-side
        # autorange) so the very first frame is scaled the exact same way
        # every later Plotly.animate frame will be - see combo_ranges/
        # updateSlider_ below for why a fixed/unset range breaks on drag.
        axis = {"showticklabels": False, "showgrid": False, "zeroline": False, "showline": True,
                "linecolor": _GRID_BORDER, "mirror": True}
        fig.update_layout(width=canvas_px, height=canvas_px, plot_bgcolor="white", paper_bgcolor="white",
                          margin={"t": 5, "b": 5, "l": 5, "r": 5},
                          xaxis={**axis, "range": first_range["x"]}, yaxis={**axis, "range": first_range["y"]})
    else:
        marker_3d = {**marker, "size": _MARKER_SIZE_3D, "opacity": marker["opacity"] * _MARKER_OPACITY_FACTOR_3D}
        fig = go.Figure(data=[go.Scatter3d(
            x=[p[0] for p in first_points], y=[p[1] for p in first_points], z=[p[2] for p in first_points], mode="markers",
            marker=marker_3d, text=metadata["subject_id"], hovertemplate="%{text}<extra></extra>",
        )])
        axis3d_base = {"showticklabels": False, "showgrid": False, "showbackground": False, "title": "",
                        "zeroline": True, "zerolinewidth": 1.5}
        fig.update_layout(
            width=canvas_px, height=canvas_px, paper_bgcolor="white", margin={"t": 5, "b": 5, "l": 5, "r": 5},
            scene={
                "xaxis": {**axis3d_base, "zerolinecolor": "rgba(217,95,63,0.6)", "range": first_range["x"]},
                "yaxis": {**axis3d_base, "zerolinecolor": "rgba(63,163,95,0.6)", "range": first_range["y"]},
                "zaxis": {**axis3d_base, "zerolinecolor": "rgba(63,120,217,0.6)", "range": first_range["z"]},
            },
        )
    fig_html = fig.to_html(full_html=False, include_plotlyjs=include_plotlyjs, div_id=div_id, config={"displayModeBar": False})

    # Every id/global inside this block is suffixed by instance_id - this
    # section can be embedded more than once on the same page (comparison
    # sections below) without one instance's slider driving the other's plot.
    # PAIR bolds the PARAMETER NAME ("n_neighbors:"), not the live value.
    title_html = f'<div class="dual-slider-title">{title}</div>' if title else ""
    slider_rows_html = "".join(
        f"""<div class="slider-row"><span class="slider-label"><span class="param-name">{p}:</span> <span id="{p}-val-{instance_id}">{options[p][0]}</span></span>
        <input type="range" min="0" max="{len(options[p]) - 1}" value="0" step="1" id="{p}-slider-{instance_id}"></div>"""
        for p in free_params
    )
    html = f"""<div class="dual-slider">
      {title_html}
      {fig_html}
      {slider_rows_html}
    </div>
    <script>
    const OPTIONS_{js_id} = {json.dumps(options)};
    const COMBO_POINTS_{js_id} = {json.dumps(combo_points)};
    const COMBO_RANGES_{js_id} = {json.dumps(combo_ranges)};
    const FREE_PARAMS_{js_id} = {json.dumps(free_params)};
    function updateSlider_{js_id}() {{
      const idxs = FREE_PARAMS_{js_id}.map(p => document.getElementById(p + '-slider-{instance_id}').value);
      FREE_PARAMS_{js_id}.forEach((p, i) => {{
        document.getElementById(p + '-val-{instance_id}').innerText = OPTIONS_{js_id}[p][idxs[i]];
      }});
      const key = idxs.join('_');
      const pts = COMBO_POINTS_{js_id}[key];
      const rng = COMBO_RANGES_{js_id}[key];
      const animData = {{x: pts.map(p => p[0]), y: pts.map(p => p[1])}};
      // Each combo is an independent fit with its own coordinate scale -
      // Plotly.animate never recomputes axis autorange on its own (unlike
      // Plotly.newPlot/react), so the target frame's own range has to be
      // pushed through explicitly or later combos render squashed or fully
      // off-canvas against the FIRST combo's range (see this function's
      // own docstring for the diagnosed bug/fix).
      const layoutUpdate = pts[0].length === 3
        ? {{scene: {{xaxis: {{range: rng.x}}, yaxis: {{range: rng.y}}, zaxis: {{range: rng.z}}}}}}
        : {{xaxis: {{range: rng.x}}, yaxis: {{range: rng.y}}}};
      if (pts[0].length === 3) animData.z = pts.map(p => p[2]);
      // 'quad-in-out' matches PAIR's own Tween class exactly (easeInOutQuad,
      // 500ms - mammoth_visualization/js/tween.js), not Plotly's 'cubic-in-out'.
      Plotly.animate('{div_id}', {{data: [animData], layout: layoutUpdate}},
        {{transition: {{duration: 500, easing: 'quad-in-out'}}, frame: {{duration: 500, redraw: true}}}});
    }}
    FREE_PARAMS_{js_id}.forEach(p => document.getElementById(p + '-slider-{instance_id}').addEventListener('input', updateSlider_{js_id}));
    </script>"""

    options_lines = "".join(f"<span class='name'>{p} options:</span> {options[p]}<br>" for p in free_params)
    description = (
        f"<div class='params'>The same subjects, re-projected as you drag {'either' if len(free_params) == 2 else 'the'} "
        f"slider{'s' if len(free_params) > 1 else ''} independently. "
        f"Points move between positions instead of jumping, so a subject can be followed across settings."
        f"<br><br><span class='name'>metric:</span> {metric}<br>"
        f"{options_lines}</div>"
    )
    return html, description, div_id


_CSS = f"""
body {{ font-family: -apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu,
       Cantarell, "Helvetica Neue", sans-serif;
       /* Wide enough to fit Figure 1/4's real-data grid (1150 subjects, _CELL_PX=165)
       plus its left-column labels and menu without the row overflowing the page and
       squeezing the menu asymmetrically (see .container.below-menu below). */
       margin: 24px auto; max-width: 1450px; color: {_TEXT_COLOR}; font-size: 16px;
       /* Plain white page, no dark-mode variant - explicit here so the page doesn't
       inherit a dark host background when left unset. */
       background: #fff; }}
.page-title {{ font-size: 32px; font-weight: 800; text-align: center; margin: 8px 0 48px; }}
.section-title {{ font-size: 20px; font-weight: 700; text-align: center; color: {_TEXT_COLOR};
                  margin: 64px 0 32px; }}
/* Bumped from 13px (illegible next to the 20px section-title above it, on request
   13-08-26) - still visually secondary via its own muted gray, just readable now. */
.section-note {{ text-align: center; font-size: 16px; color: #767676; margin: -20px 0 32px; }}
.figure {{ display: flex; flex-direction: column; align-items: center; margin-bottom: 96px; }}
/* Figure 2 only now (Figures 1/4 use the .below-menu variant instead, see below) -
   grid+sliders left, menu right. align-items:center (not PAIR's own flex-start)
   because the left column is taller than the menu text (plot + 2 slider rows below
   it) - flex-start left the menu's paragraph pinned to the very top, next to the
   plot, floating well above where the sliders actually are; centered it reads as
   one balanced block instead (on request, 13-08-26). */
.container {{ display: flex; flex-direction: row; align-items: center; }}
/* Figures 1 and 4 (both real-data, wide grids) - menu moved BELOW the grid instead
   of beside it, so the figure stays centered with equal white margins left/right
   instead of the row overflowing the page and flexbox squeezing the menu down from
   its own max-width to make the row fit (confirmed live: without this, the row's
   total width equalled the page's exactly, i.e. zero margin on either side). A
   modifier on .container, not a change to .container itself - Figure 2's own
   .container (narrower, fits comfortably) keeps the original side-by-side layout. */
.container.below-menu {{ flex-direction: column; align-items: center; }}
.container.below-menu .menu {{ max-width: 620px; margin-top: 28px; text-align: center; }}
.container.below-menu .color-buttons {{ justify-content: center; }}
/* .figures-container's own margin-right:20px (below) exists to clear a menu sitting
   to its RIGHT - stray/asymmetric once the menu moves below, so cancelled here
   rather than in the shared rule itself. */
.container.below-menu .figures-container {{ margin-right: 0; }}
.figures-container {{ display: flex; font-size: 12px; margin-right: 20px; }}
/* left edge: spacer (aligns with min_dist header+labels above the grid) stacked above a row
   containing [rotated bold "n_neighbors" label, non-bold swept values]. */
.left-column {{ display: flex; flex-direction: column; align-items: flex-end; }}
.left-column-spacer {{ height: {_LEFT_COLUMN_SPACER_H}px; }}
.left-column-content {{ display: flex; flex-direction: row; align-items: center;
                        justify-content: space-around; }}
.left-column-header {{ display: flex; flex-direction: column; align-items: center;
                       justify-content: space-around; width: 30px; }}
.n-neighbors-header {{ writing-mode: vertical-lr; text-orientation: sideways;
                      transform: rotate(180deg); font-weight: 800; font-size: 12px; }}
.left-column-labels {{ display: flex; flex-direction: column; align-items: flex-end;
                      justify-content: space-around; padding-right: 6px; }}
.left-column-labels div {{ display: flex; align-items: center; }}
.min-dist-header {{ font-weight: 800; font-size: 12px; display: flex; flex-direction: row;
                    align-items: center; justify-content: space-around; height: {_MIN_DIST_HEADER_H}px; }}
.min-dist-labels {{ display: flex; flex-direction: row; align-items: flex-end;
                    justify-content: space-around; height: {_MIN_DIST_LABELS_H}px; }}
.min-dist-labels div {{ text-align: center; }}
.menu {{ display: flex; flex-direction: column; max-width: 320px; font-size: 16px; }}
.color-buttons {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 18px; }}
.color-buttons button {{ font: inherit; font-size: 13px; padding: 6px 12px; cursor: pointer;
                        border: 1px solid #ccc; border-radius: 4px; background: #fff; }}
.color-buttons button.active {{ border-color: #4a90d9; border-width: 2px; background: #f0f7fd; }}
.params {{ line-height: 1.7; }}
.params .name {{ font-weight: 600; }}
/* Figure 1's color_by legend (#legend, populated/rebuilt by setColor() every
   time the color_by picker changes) - sits right under .params, next to the
   plot, on request (14-08-26: color_by picker had no legend at all, so
   "dataset"/"side" colors had no explanation anywhere on the page). Empty
   for the default "none" mode (nothing to explain), a chip row for
   dataset/side, a gradient bar for volume/nihss - see
   _legend_html_for_mode's own docstring. */
#legend {{ margin-top: 18px; }}
.categories {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.category-chip {{ padding: 4px 10px; border-radius: 3px; color: #fff; font-size: 13px; font-weight: 600; }}
.gradient-legend {{ display: flex; align-items: center; gap: 8px; font-size: 13px; }}
.gradient-bar {{ width: 140px; height: 12px; border-radius: 3px; border: 1px solid rgba(0,0,0,0.15); }}
/* max-width was none (PAIR's own caption is unconstrained) - fine on PAIR's own
   page, where every figure is roughly the same width as the page itself. Once
   body widened to 1450px for Figure 1/4's own wide grid, an unconstrained caption
   wrapped at nearly the FULL page width regardless of how narrow its own figure
   was (confirmed live: Figure 3's caption spanned all 1450px, edge to edge, zero
   margin - "hai tolto i margini bianchi", 14-08-26) - capped here so every
   caption keeps a comfortable, consistent margin regardless of page width. */
.caption {{ text-align: center; font-style: italic; font-size: 13px; color: {_TEXT_COLOR};
           margin: 20px auto; max-width: 900px; }}
.caption .figure-number {{ font-weight: 600; }}
code {{ background: #f2f2f2; padding: 1px 4px; border-radius: 3px; font-size: 13px; }}
.dual-slider {{ display: flex; flex-direction: column; align-items: center; }}
.dual-slider-title {{ text-align: center; font-weight: bold; margin-bottom: 20px; }}
.slider-row {{ display: flex; flex-direction: row; justify-content: center; align-items: center;
               margin-top: 6px; }}
.slider-label {{ width: 150px; margin-right: 10px; text-align: right; }}
.slider-label .param-name {{ font-weight: 600; }}
.slider-row input[type=range] {{ width: 230px; }}
.left-column-labels.plain {{ font-weight: 800; }}
.hyperparam-header {{ font-weight: 800; font-size: 12px; display: flex; flex-direction: row;
                      align-items: center; justify-content: space-around; height: {_MIN_DIST_HEADER_H}px; }}
.hyperparam-labels {{ display: flex; flex-direction: row; align-items: flex-end;
                      justify-content: space-around; height: {_MIN_DIST_LABELS_H}px; }}
.hyperparam-labels div {{ text-align: center; }}
.method-label {{ display: flex; align-items: center; }}
/* Generic 2-panel side-by-side layout, shared by build_2d_vs_3d_section (Figure 3) and
   build_method_comparison_slider_section (Figure 5) - each panel there is a whole
   build_slider_section output (plot + its own sliders + its own .params description). */
.panel-row {{ display: flex; flex-direction: row; gap: 32px; justify-content: center; flex-wrap: wrap; }}
.slider-panel {{ display: flex; flex-direction: column; align-items: center; max-width: 460px; }}
/* build_slider_section concatenates its own .dual-slider (plot+sliders) directly
   against its .params description with no gap - fine when .params sits in a side
   .menu column (Figure 2), but inside a stacked .slider-panel (Figures 3/5) the two
   read as one crowded block without this (on request, 13-08-26). */
.slider-panel .params {{ margin-top: 24px; }}
"""


def build_leaf_page(
    metric: str,
    real_umap_dir: Path,
    real_embeddings: dict,
    real_metadata: pd.DataFrame,
    n_components: int,
    tsne_tuning_dir: Path,
    tsne_embeddings: dict,
    output_path: Path,
) -> None:
    """Every figure on this page reads real production tuning output -
    real_umap_dir (nested_params=["metric", "n_components"]) for the UMAP
    side, tsne_tuning_dir (nested_params=["metric"], always 2D) for the
    t-SNE side. Both must be the same cohort, same row order - the caller
    (generate_report) checks this once for both metrics rather than here per
    metric, to fail before any file is written.
    """
    real_leaf_dir = real_umap_dir / f"metric={metric}" / "n_components=2"
    results = pd.read_csv(real_leaf_dir / "tuning_results.csv")

    # Plotly.js itself only needs to be embedded ONCE per page (it's a global
    # `Plotly` the browser loads from the first inline <script>, every other
    # figure's own <div>+<script> reuses it) - the grid goes first
    # (include_plotlyjs=True), everything else after reuses it.
    grid_container_html, n_cells = _build_grid_block_html(
        real_leaf_dir, real_embeddings, real_metadata, div_id="grid", default_mode="none", include_plotlyjs=True,
        cell_px=_CELL_PX,
    )
    slider_section_html, slider_description, _div_id = build_slider_section(
        real_leaf_dir, real_embeddings, real_metadata, free_params=["n_neighbors", "min_dist"],
        instance_id=metric, metric=metric, title=f"metric = {metric}", include_plotlyjs=False,
        canvas_px=_CANVAS_PX,
    )
    twod_vs_3d_html = build_2d_vs_3d_section(
        metric, real_umap_dir, real_embeddings, real_metadata, instance_prefix=metric,
    )
    # No color_by picker of its own, same precedent as the dual-slider Figure 2 -
    # n_cells isn't needed by build_leaf_page since nothing here restyles it.
    comparison_html, _comparison_n_cells, comparison_info = _build_comparison_block_html(
        metric, tsne_tuning_dir, real_leaf_dir, tsne_embeddings, real_embeddings, real_metadata,
        div_id="comparison-grid", include_plotlyjs=False, cell_px=_CELL_PX,
    )
    comparison_slider_html = build_method_comparison_slider_section(
        metric, real_leaf_dir, real_embeddings, tsne_tuning_dir, tsne_embeddings, real_metadata, instance_prefix=metric,
    )

    # color_by picker: plain HTML buttons driving Plotly.restyle on the grid -
    # one array per mode, broadcast to every cell (same subjects in all of them).
    # legend_by_mode is the same idea for the #legend div - see
    # _legend_html_for_mode's own docstring for why it isn't computed once
    # up front but rebuilt (from a precomputed HTML string, not refit) every
    # time the picker changes.
    colors_by_mode = {m: _color_values_for_mode(real_metadata, m) for m in COLOR_BY_MODES}
    legend_by_mode = {m: _legend_html_for_mode(real_metadata, m) for m in COLOR_BY_MODES}
    button_parts = []
    for i, m in enumerate(COLOR_BY_MODES):
        active_class = ' class="active"' if i == 0 else ""
        button_parts.append(f"<button onclick=\"setColor('{m}', this)\"{active_class}>{m}</button>")
    buttons_html = "".join(button_parts)

    html = f"""<html><head><meta charset="utf-8"><title>Understanding UMAP — metric={metric}</title>
<style>{_CSS}</style></head><body>

<div class="page-title">Understanding UMAP</div>

<div class="section-title">UMAP across parameters</div>
<div class="section-note">Real data - {len(real_metadata)} lesion subjects, production tuning run</div>

<div class="figure">
  <div class="container below-menu">
    {grid_container_html}
    <div class="menu">
      <div class="color-buttons">{buttons_html}</div>
      <div class="params">
        Lesion embeddings of the same stroke cohort, projected with UMAP.<br><br>
        <span class="name">metric:</span> {metric}<br>
        <span class="name">n_components:</span> {n_components}<br>
        <span class="name">subjects:</span> {len(real_metadata)}<br>
        <span class="name">combinations:</span> {len(results)}
      </div>
      <div id="legend"></div>
    </div>
  </div>
  <div class="caption"><span class="figure-number">Figure 1:</span> UMAP projection of the lesion cohort with a variety of common
    values for the <code>n_neighbors</code> and <code>min_dist</code> parameters.</div>
</div>

<div class="figure">
  <div class="container">
    <div class="figures-container">{slider_section_html}</div>
    <div class="menu">{slider_description}</div>
  </div>
  <div class="caption"><span class="figure-number">Figure 2:</span> Drag either slider to change <code>n_neighbors</code>/<code>min_dist</code> independently.</div>
</div>

<div class="section-title">UMAP across dimensions</div>
<div class="section-note">Real data - {len(real_metadata)} lesion subjects, production tuning run</div>

<div class="figure">
  {twod_vs_3d_html}
  <div class="caption"><span class="figure-number">Figure 3:</span> The same lesion cohort, projected with UMAP into 2 dimensions
    (left) and 3 dimensions (right) - drag either panel's own sliders to change <code>n_neighbors</code>/<code>min_dist</code>
    independently. The 3D embedding is a separate fit, not the 2D one with an extra coordinate added.</div>
</div>

<div class="section-title">UMAP vs t-SNE</div>
<div class="section-note">Real data - {len(real_metadata)} lesion subjects, production tuning run</div>

<div class="figure">
  <div class="container below-menu">
    {comparison_html}
    <div class="menu">
      <div class="params">
        Same lesion cohort, projected with two different methods.<br><br>
        <span class="name">metric:</span> {metric}<br>
        <span class="name">t-SNE perplexity options:</span> {comparison_info["perplexity_values"]}<br>
        <span class="name">UMAP n_neighbors options:</span> {comparison_info["n_neighbors_values"]} (min_dist fixed at {UMAP_BASE_MIN_DIST})<br>
        <span class="name">subjects:</span> {len(real_metadata)}
      </div>
    </div>
  </div>
  <div class="caption"><span class="figure-number">Figure 4:</span> UMAP and t-SNE projections of the same lesion cohort,
    compared at matching values of each method's own local-neighborhood parameter.
    {(f"t-SNE never swept perplexity={comparison_info['missing_tsne']} - those cells are empty. " if comparison_info["missing_tsne"] else "")}
    {(f"UMAP never swept n_neighbors={comparison_info['missing_umap']} - those cells are empty." if comparison_info["missing_umap"] else "")}
  </div>
</div>

<div class="figure">
  {comparison_slider_html}
  <div class="caption"><span class="figure-number">Figure 5:</span> UMAP and t-SNE projections of the same lesion cohort into 2
    dimensions - drag either panel's own slider(s) independently, same subjects on both sides.</div>
</div>

<script>
const COLORS = {json.dumps({m: colors_by_mode[m] for m in COLOR_BY_MODES})};
const LEGENDS = {json.dumps(legend_by_mode)};
const N_CELLS = {n_cells};
function setColor(mode, btn) {{
  const c = COLORS[mode];
  const idx = Array.from({{length: N_CELLS}}, (_, i) => i);
  Plotly.restyle('grid', {{'marker.color': idx.map(() => c.color),
                           'marker.colorscale': idx.map(() => c.colorscale),
                           'marker.opacity': idx.map(() => c.opacity)}}, idx);
  document.getElementById('legend').innerHTML = LEGENDS[mode];
  document.querySelectorAll('.color-buttons button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}}
</script>
</body></html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    logger.info("report written to %s", output_path)


@dataclass
class TuningData:
    """Everything the static HTML report (build_leaf_page/generate_report)
    needs, loaded and cohort-validated exactly once - see load_tuning_data.
    """

    umap_tuning_dir: Path
    tsne_tuning_dir: Path
    real_embeddings: dict
    real_metadata: pd.DataFrame
    n_components: int
    tsne_embeddings: dict
    metrics: list[str]


def load_tuning_data(umap_tuning_dir: Path, tsne_tuning_dir: Path) -> TuningData:
    """Loads + cohort-validates the UMAP/t-SNE tuning output - factored out
    of generate_report as its own step for readability. Raises ValueError if
    the UMAP and t-SNE cohorts don't match (different subjects, order, or
    metadata columns) - every figure assumes row-for-row alignment between
    the two, so a mismatch here would silently compare two different
    populations under one legend.
    """
    if not umap_tuning_dir.exists():
        raise FileNotFoundError(f"umap_tuning_dir does not exist: {umap_tuning_dir}")
    if not tsne_tuning_dir.exists():
        raise FileNotFoundError(f"tsne_tuning_dir does not exist: {tsne_tuning_dir}")

    real_data = np.load(umap_tuning_dir / "embeddings.npz")
    real_embeddings = {key: real_data[key] for key in real_data.files}
    real_metadata = pd.read_csv(umap_tuning_dir / "metadata.csv")
    n_components = _read_base_n_components(umap_tuning_dir)

    tsne_data = np.load(tsne_tuning_dir / "embeddings.npz")
    tsne_embeddings = {key: tsne_data[key] for key in tsne_data.files}
    tsne_metadata = pd.read_csv(tsne_tuning_dir / "metadata.csv")
    if not real_metadata.equals(tsne_metadata):
        raise ValueError(
            f"UMAP metadata ({umap_tuning_dir}) and t-SNE metadata ({tsne_tuning_dir}) don't match "
            "(different subjects, order, or columns) - every figure needs the same cohort on both sides"
        )

    metrics = sorted(p.name.split("=")[1] for p in umap_tuning_dir.glob("metric=*"))
    if not metrics:
        raise ValueError(f"no metric=* leaves found under {umap_tuning_dir}")

    return TuningData(
        umap_tuning_dir=umap_tuning_dir, tsne_tuning_dir=tsne_tuning_dir,
        real_embeddings=real_embeddings, real_metadata=real_metadata, n_components=n_components,
        tsne_embeddings=tsne_embeddings, metrics=metrics,
    )


def generate_report(umap_tuning_dir: Path, tsne_tuning_dir: Path, output_dir: Path) -> list[Path]:
    """Top-level entry point: one HTML page per metric leaf found under
    umap_tuning_dir, written to output_dir.
    """
    data = load_tuning_data(umap_tuning_dir, tsne_tuning_dir)

    output_paths = []
    for metric in data.metrics:
        output_path = output_dir / f"understanding_umap_{metric}.html"
        build_leaf_page(
            metric, data.umap_tuning_dir, data.real_embeddings, data.real_metadata, data.n_components,
            data.tsne_tuning_dir, data.tsne_embeddings, output_path,
        )
        output_paths.append(output_path)
    return output_paths
