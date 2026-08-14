"""Interactive Dash version of the "Understanding UMAP" report - same real
tuning output, same 5 figures, same layout language (reuses
src.analysis.understanding_umap_report's own _CSS, TuningData/
load_tuning_data, and figure builders directly, not a re-implementation) as
its static-HTML sibling. The two live alongside each other on purpose (on
request, 14-08-26): the static report stays the pipeline's own artifact
(publishable, no server needed), this one is a local dev tool for a human to
explore the same data live.

Built on Dash instead of the static report's hand-rolled Plotly.animate + a
JSON blob of every precomputed combo baked into inline JS: a Dash callback
recomputes exactly the ONE combo a slider/picker asks for, in Python, at
request time - no separate axis-range bookkeeping needed either
(Dash's dcc.Graph calls Plotly.react() on every figure-prop change, which
recomputes autorange on its own, unlike Plotly.animate - the entire "Bug fix
13-08-26" padded-range workaround in the static report's build_slider_section
has no equivalent problem to work around here).

One process serves every metric via a single picker (not one HTML file per
metric like the static report) - metric is shared UI state, every figure's
own callback reads it.

Run: see src/pipeline/run_understanding_umap_dash.py (local dev server only,
never sbatch - an interactive app has no batch-job shape).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from src.analysis.understanding_umap_report import (
    _CANVAS_PX,
    _CELL_PX,
    _CSS,
    _GRID_BORDER,
    _MARKER_OPACITY_FACTOR_3D,
    _MARKER_SIZE_3D,
    COLOR_BY_MODES,
    TuningData,
    _color_values_for_mode,
    _combo_key,
    _legend_html_for_mode,
    build_comparison_grid_figure,
    build_grid_figure,
)

_AXIS_2D = {"showticklabels": False, "showgrid": False, "zeroline": False, "showline": True,
            "linecolor": _GRID_BORDER, "mirror": True}
_AXIS_3D_BASE = {"showticklabels": False, "showgrid": False, "showbackground": False, "title": "", "zeroline": True, "zerolinewidth": 1.5}
_ANIMATION_OPTIONS = {"frame": {"duration": 400, "redraw": True}, "transition": {"duration": 400, "easing": "quad-in-out"}}


def _leaf_paths(data: TuningData, metric: str) -> tuple[Path, Path, Path]:
    return (
        data.umap_tuning_dir / f"metric={metric}" / "n_components=2",
        data.umap_tuning_dir / f"metric={metric}" / "n_components=3",
        data.tsne_tuning_dir / f"metric={metric}",
    )


class _PreloadedResults:
    """tuning_results.csv for every metric, read once at app startup (not
    per-callback) - a slider drag fires many callbacks a second, re-reading
    a CSV from disk on every one of them would be wasteful and, on a slow
    filesystem, laggy enough to be noticeable.
    """

    def __init__(self, data: TuningData):
        self.umap_2d: dict[str, pd.DataFrame] = {}
        self.umap_3d: dict[str, pd.DataFrame] = {}
        self.tsne: dict[str, pd.DataFrame] = {}
        for metric in data.metrics:
            leaf_2d, leaf_3d, tsne_leaf = _leaf_paths(data, metric)
            self.umap_2d[metric] = pd.read_csv(leaf_2d / "tuning_results.csv")
            self.umap_3d[metric] = pd.read_csv(leaf_3d / "tuning_results.csv")
            self.tsne[metric] = pd.read_csv(tsne_leaf / "tuning_results.csv")


def _slider_options(results: pd.DataFrame, param: str) -> list:
    return sorted(results[param].unique().tolist())


def _slider_reset(options: list) -> tuple[int, int, dict, int]:
    """min/max/marks/value for a dcc.Slider keyed by INDEX into `options`,
    not by the raw values themselves - a float like 0.0/1.0 round-trips
    through Dash's own value<->mark JSON encoding fine, but indices sidestep
    any such mismatch entirely (same reasoning as the static report's own
    combo_points, see build_slider_section's docstring), and resetting to
    index 0 on every metric change keeps behavior predictable rather than
    trying to preserve a previous value that may not exist in the new
    metric's own option list.
    """
    marks = {i: str(v) for i, v in enumerate(options)}
    return 0, len(options) - 1, marks, 0


def _single_combo_2d_figure(points: np.ndarray, subject_ids: pd.Series, marker: dict) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=points[:, 0], y=points[:, 1], mode="markers",
        marker=marker, text=subject_ids, hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        width=_CANVAS_PX, height=_CANVAS_PX, plot_bgcolor="white", paper_bgcolor="white",
        margin={"t": 5, "b": 5, "l": 5, "r": 5}, xaxis=_AXIS_2D, yaxis=_AXIS_2D,
    )
    return fig


def _single_combo_3d_figure(points: np.ndarray, subject_ids: pd.Series, marker: dict) -> go.Figure:
    fig = go.Figure(go.Scatter3d(
        x=points[:, 0], y=points[:, 1], z=points[:, 2], mode="markers",
        marker=marker, text=subject_ids, hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        width=_CANVAS_PX, height=_CANVAS_PX, paper_bgcolor="white", margin={"t": 5, "b": 5, "l": 5, "r": 5},
        scene={
            "xaxis": {**_AXIS_3D_BASE, "zerolinecolor": "rgba(217,95,63,0.6)"},
            "yaxis": {**_AXIS_3D_BASE, "zerolinecolor": "rgba(63,163,95,0.6)"},
            "zaxis": {**_AXIS_3D_BASE, "zerolinecolor": "rgba(63,120,217,0.6)"},
        },
    )
    return fig


def _umap_combo_figure(results: pd.DataFrame, embeddings: dict, metadata: pd.DataFrame, metric: str, n_neighbors, min_dist, is_3d: bool) -> go.Figure:
    key_order = [c for c in results.columns if c != "trustworthiness"]
    match = results[(results["n_neighbors"] == n_neighbors) & (results["min_dist"] == min_dist)]
    if match.empty:
        raise ValueError(f"no UMAP combo for metric={metric!r}, n_neighbors={n_neighbors!r}, min_dist={min_dist!r}")
    points = embeddings[_combo_key(match.iloc[0], key_order)]
    colors = _color_values_for_mode(metadata, "none")
    if is_3d:
        marker = {"size": _MARKER_SIZE_3D, "color": colors["color"], "opacity": colors["opacity"] * _MARKER_OPACITY_FACTOR_3D, "line": {"width": 0}}
        return _single_combo_3d_figure(points, metadata["subject_id"], marker)
    marker = {"size": 6, "color": colors["color"], "opacity": colors["opacity"], "line": {"width": 0}}
    return _single_combo_2d_figure(points, metadata["subject_id"], marker)


def _tsne_combo_figure(results: pd.DataFrame, embeddings: dict, metadata: pd.DataFrame, perplexity) -> go.Figure:
    key_order = [c for c in results.columns if c != "trustworthiness"]
    match = results[results["perplexity"] == perplexity]
    if match.empty:
        raise ValueError(f"no t-SNE combo for perplexity={perplexity!r}")
    points = embeddings[_combo_key(match.iloc[0], key_order)]
    colors = _color_values_for_mode(metadata, "none")
    marker = {"size": 6, "color": colors["color"], "opacity": colors["opacity"], "line": {"width": 0}}
    return _single_combo_2d_figure(points, metadata["subject_id"], marker)


def _slider_row(param_id: str, label: str) -> html.Div:
    return html.Div(
        [html.Span(label, className="dash-slider-label"), dcc.Slider(id=param_id, min=0, max=1, step=1, value=0, marks={})],
        className="dash-slider-row",
    )


def build_app(data: TuningData) -> Dash:
    preloaded = _PreloadedResults(data)
    metric_options = [{"label": m, "value": m} for m in data.metrics]
    default_metric = data.metrics[0]

    app = Dash(__name__)
    app.index_string = app.index_string.replace("{%css%}", f"{{%css%}}<style>{_CSS}</style>")
    app.layout = html.Div(className="dash-page", children=[
        html.Div("Understanding UMAP — interactive", className="page-title"),
        html.Div([
            html.Span("metric: ", className="name"),
            dcc.RadioItems(id="metric", options=metric_options, value=default_metric, inline=True),
        ], className="dash-metric-picker"),

        html.Div("UMAP across parameters", className="section-title"),
        html.Div(f"Real data - {len(data.real_metadata)} lesion subjects, production tuning run", className="section-note"),
        html.Div(className="figure", children=[
            html.Div(className="container below-menu", children=[
                html.Div(className="figures-container", children=[
                    html.Div(className="left-column", children=[
                        html.Div(className="left-column-spacer"),
                        html.Div(className="left-column-content", children=[
                            html.Div(className="left-column-header", children=[html.Div("n_neighbors", className="n-neighbors-header")]),
                            html.Div(id="fig1-row-labels", className="left-column-labels"),
                        ]),
                    ]),
                    html.Div(children=[
                        html.Div("min_dist", id="fig1-min-dist-header", className="min-dist-header"),
                        html.Div(id="fig1-col-labels", className="min-dist-labels"),
                        dcc.Graph(id="fig1-grid", config={"displayModeBar": False}),
                    ]),
                ]),
                html.Div(className="menu", children=[
                    dcc.RadioItems(id="color-by", options=[{"label": m, "value": m} for m in COLOR_BY_MODES], value="none", inline=True, className="color-buttons"),
                    html.Div(id="fig1-legend"),
                ]),
            ]),
            html.Div([html.Span("Figure 1: ", className="figure-number"), "UMAP projection of the lesion cohort - drag n_neighbors/color_by to explore."], className="caption"),
        ]),
        html.Div(className="figure", children=[
            html.Div(className="dual-slider", children=[
                dcc.Graph(id="fig2-plot", config={"displayModeBar": False}, animate=True, animation_options=_ANIMATION_OPTIONS),
                _slider_row("fig2-n-neighbors", "n_neighbors:"),
                _slider_row("fig2-min-dist", "min_dist:"),
            ]),
            html.Div([html.Span("Figure 2: ", className="figure-number"), "Drag either slider to change n_neighbors/min_dist independently."], className="caption"),
        ]),

        html.Div("UMAP across dimensions", className="section-title"),
        html.Div(f"Real data - {len(data.real_metadata)} lesion subjects, production tuning run", className="section-note"),
        html.Div(className="figure", children=[
            html.Div(className="panel-row", children=[
                html.Div(className="slider-panel", children=[
                    html.Div("UMAP (2D)", className="dual-slider-title"),
                    dcc.Graph(id="fig3-2d-plot", config={"displayModeBar": False}, animate=True, animation_options=_ANIMATION_OPTIONS),
                    _slider_row("fig3-2d-n-neighbors", "n_neighbors:"), _slider_row("fig3-2d-min-dist", "min_dist:"),
                ]),
                html.Div(className="slider-panel", children=[
                    html.Div("UMAP (3D)", className="dual-slider-title"),
                    dcc.Graph(id="fig3-3d-plot", config={"displayModeBar": False}),
                    _slider_row("fig3-3d-n-neighbors", "n_neighbors:"), _slider_row("fig3-3d-min-dist", "min_dist:"),
                ]),
            ]),
            html.Div([html.Span("Figure 3: ", className="figure-number"), "UMAP into 2D (left) vs 3D (right) - the 3D embedding is a separate fit."], className="caption"),
        ]),

        html.Div("UMAP vs t-SNE", className="section-title"),
        html.Div(f"Real data - {len(data.real_metadata)} lesion subjects, production tuning run", className="section-note"),
        html.Div(className="figure", children=[
            html.Div(className="container below-menu", children=[
                dcc.Graph(id="fig4-grid", config={"displayModeBar": False}),
                html.Div(className="menu", children=[html.Div("Same lesion cohort, projected with two different methods.", className="params")]),
            ]),
            html.Div([html.Span("Figure 4: ", className="figure-number"), "UMAP and t-SNE at matching values of each method's own local-neighborhood parameter."], className="caption"),
        ]),
        html.Div(className="figure", children=[
            html.Div(className="panel-row", children=[
                html.Div(className="slider-panel", children=[
                    html.Div("UMAP", className="dual-slider-title"),
                    dcc.Graph(id="fig5-umap-plot", config={"displayModeBar": False}, animate=True, animation_options=_ANIMATION_OPTIONS),
                    _slider_row("fig5-umap-n-neighbors", "n_neighbors:"), _slider_row("fig5-umap-min-dist", "min_dist:"),
                ]),
                html.Div(className="slider-panel", children=[
                    html.Div("t-SNE", className="dual-slider-title"),
                    dcc.Graph(id="fig5-tsne-plot", config={"displayModeBar": False}, animate=True, animation_options=_ANIMATION_OPTIONS),
                    _slider_row("fig5-tsne-perplexity", "perplexity:"),
                ]),
            ]),
            html.Div([html.Span("Figure 5: ", className="figure-number"), "UMAP and t-SNE into 2D - drag either panel's own slider(s) independently, same subjects on both sides."], className="caption"),
        ]),
    ])

    def _reset_pair(metric: str, results_by_metric: dict[str, pd.DataFrame]):
        results = results_by_metric[metric]
        nn_min, nn_max, nn_marks, nn_val = _slider_reset(_slider_options(results, "n_neighbors"))
        md_min, md_max, md_marks, md_val = _slider_reset(_slider_options(results, "min_dist"))
        return nn_min, nn_max, nn_marks, nn_val, md_min, md_max, md_marks, md_val

    @app.callback(
        Output("fig2-n-neighbors", "min"), Output("fig2-n-neighbors", "max"), Output("fig2-n-neighbors", "marks"), Output("fig2-n-neighbors", "value"),
        Output("fig2-min-dist", "min"), Output("fig2-min-dist", "max"), Output("fig2-min-dist", "marks"), Output("fig2-min-dist", "value"),
        Input("metric", "value"),
    )
    def _reset_fig2(metric):
        return _reset_pair(metric, preloaded.umap_2d)

    @app.callback(
        Output("fig3-2d-n-neighbors", "min"), Output("fig3-2d-n-neighbors", "max"), Output("fig3-2d-n-neighbors", "marks"), Output("fig3-2d-n-neighbors", "value"),
        Output("fig3-2d-min-dist", "min"), Output("fig3-2d-min-dist", "max"), Output("fig3-2d-min-dist", "marks"), Output("fig3-2d-min-dist", "value"),
        Input("metric", "value"),
    )
    def _reset_fig3_2d(metric):
        return _reset_pair(metric, preloaded.umap_2d)

    @app.callback(
        Output("fig3-3d-n-neighbors", "min"), Output("fig3-3d-n-neighbors", "max"), Output("fig3-3d-n-neighbors", "marks"), Output("fig3-3d-n-neighbors", "value"),
        Output("fig3-3d-min-dist", "min"), Output("fig3-3d-min-dist", "max"), Output("fig3-3d-min-dist", "marks"), Output("fig3-3d-min-dist", "value"),
        Input("metric", "value"),
    )
    def _reset_fig3_3d(metric):
        return _reset_pair(metric, preloaded.umap_3d)

    @app.callback(
        Output("fig5-umap-n-neighbors", "min"), Output("fig5-umap-n-neighbors", "max"), Output("fig5-umap-n-neighbors", "marks"), Output("fig5-umap-n-neighbors", "value"),
        Output("fig5-umap-min-dist", "min"), Output("fig5-umap-min-dist", "max"), Output("fig5-umap-min-dist", "marks"), Output("fig5-umap-min-dist", "value"),
        Input("metric", "value"),
    )
    def _reset_fig5_umap(metric):
        return _reset_pair(metric, preloaded.umap_2d)

    @app.callback(
        Output("fig5-tsne-perplexity", "min"), Output("fig5-tsne-perplexity", "max"),
        Output("fig5-tsne-perplexity", "marks"), Output("fig5-tsne-perplexity", "value"),
        Input("metric", "value"),
    )
    def _reset_fig5_tsne(metric):
        return _slider_reset(_slider_options(preloaded.tsne[metric], "perplexity"))

    @app.callback(
        Output("fig1-row-labels", "children"), Output("fig1-row-labels", "style"),
        Output("fig1-col-labels", "children"), Output("fig1-col-labels", "style"),
        Output("fig1-min-dist-header", "style"),
        Input("metric", "value"),
    )
    def _update_fig1_chrome(metric):
        results = preloaded.umap_2d[metric]
        row_values = sorted(results["n_neighbors"].unique().tolist())
        col_values = sorted(results["min_dist"].unique().tolist())
        grid_h, grid_w = _CELL_PX * len(row_values), _CELL_PX * len(col_values)
        row_children = [html.Div(str(v), style={"height": f"{_CELL_PX}px"}) for v in row_values]
        col_children = [html.Div(str(v), style={"width": f"{_CELL_PX}px"}) for v in col_values]
        return row_children, {"height": f"{grid_h}px"}, col_children, {"width": f"{grid_w}px"}, {"width": f"{grid_w}px"}

    @app.callback(Output("fig1-grid", "figure"), Output("fig1-legend", "children"), Input("metric", "value"), Input("color-by", "value"))
    def _update_fig1(metric, color_by):
        leaf_2d, _leaf_3d, _tsne_leaf = _leaf_paths(data, metric)
        fig, _rows, _cols = build_grid_figure(leaf_2d, data.real_embeddings, data.real_metadata, default_mode=color_by, cell_px=_CELL_PX)
        legend = _legend_children(data.real_metadata, color_by)
        return fig, legend

    @app.callback(Output("fig2-plot", "figure"), Input("metric", "value"), Input("fig2-n-neighbors", "value"), Input("fig2-min-dist", "value"))
    def _update_fig2(metric, nn_idx, md_idx):
        results = preloaded.umap_2d[metric]
        n_neighbors = _slider_options(results, "n_neighbors")[nn_idx]
        min_dist = _slider_options(results, "min_dist")[md_idx]
        return _umap_combo_figure(results, data.real_embeddings, data.real_metadata, metric, n_neighbors, min_dist, is_3d=False)

    @app.callback(Output("fig3-2d-plot", "figure"), Input("metric", "value"), Input("fig3-2d-n-neighbors", "value"), Input("fig3-2d-min-dist", "value"))
    def _update_fig3_2d(metric, nn_idx, md_idx):
        results = preloaded.umap_2d[metric]
        n_neighbors = _slider_options(results, "n_neighbors")[nn_idx]
        min_dist = _slider_options(results, "min_dist")[md_idx]
        return _umap_combo_figure(results, data.real_embeddings, data.real_metadata, metric, n_neighbors, min_dist, is_3d=False)

    @app.callback(Output("fig3-3d-plot", "figure"), Input("metric", "value"), Input("fig3-3d-n-neighbors", "value"), Input("fig3-3d-min-dist", "value"))
    def _update_fig3_3d(metric, nn_idx, md_idx):
        results = preloaded.umap_3d[metric]
        n_neighbors = _slider_options(results, "n_neighbors")[nn_idx]
        min_dist = _slider_options(results, "min_dist")[md_idx]
        return _umap_combo_figure(results, data.real_embeddings, data.real_metadata, metric, n_neighbors, min_dist, is_3d=True)

    @app.callback(Output("fig4-grid", "figure"), Input("metric", "value"))
    def _update_fig4(metric):
        tsne_results = preloaded.tsne[metric]
        umap_results = preloaded.umap_2d[metric]
        perplexity_values = sorted(tsne_results["perplexity"].unique().tolist())
        n_neighbors_values = sorted(umap_results["n_neighbors"].unique().tolist())
        column_values = sorted(set(perplexity_values) | set(n_neighbors_values))
        return build_comparison_grid_figure(
            tsne_results, data.tsne_embeddings, umap_results, data.real_embeddings, data.real_metadata,
            column_values, cell_px=_CELL_PX,
        )

    @app.callback(Output("fig5-umap-plot", "figure"), Input("metric", "value"), Input("fig5-umap-n-neighbors", "value"), Input("fig5-umap-min-dist", "value"))
    def _update_fig5_umap(metric, nn_idx, md_idx):
        results = preloaded.umap_2d[metric]
        n_neighbors = _slider_options(results, "n_neighbors")[nn_idx]
        min_dist = _slider_options(results, "min_dist")[md_idx]
        return _umap_combo_figure(results, data.real_embeddings, data.real_metadata, metric, n_neighbors, min_dist, is_3d=False)

    @app.callback(Output("fig5-tsne-plot", "figure"), Input("metric", "value"), Input("fig5-tsne-perplexity", "value"))
    def _update_fig5_tsne(metric, pplx_idx):
        results = preloaded.tsne[metric]
        perplexity = _slider_options(results, "perplexity")[pplx_idx]
        return _tsne_combo_figure(results, data.tsne_embeddings, data.real_metadata, perplexity)

    return app


def _legend_children(metadata: pd.DataFrame, mode: str):
    html_str = _legend_html_for_mode(metadata, mode)
    if not html_str:
        return None
    return dcc.Markdown(html_str, dangerously_allow_html=True)
