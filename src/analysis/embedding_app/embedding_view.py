"""The scatter of one run's embedding: the colours it can be read by, the figure itself, and
the graph area of the page.

Everything here is a pure function of a run plus a colour mode - no callbacks, no app state.
The panels around it (anatomy, description, quality) read a cluster's centroid and its
representative subject from here, so the circle drawn on the scatter and the subject whose
anatomy is shown are the same computation, not two.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate

from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import (
    ProductionRun,
    UndisplayableRunError,
    load_cluster_space,
    load_run,
    view_note_for,
)
from src.analysis.embedding_app.style import _FONT_STACK, _GRID_BORDER, _TEXT_COLOR, _italian_figure
from src.analysis.embedding_coloring import (
    COLOR_MODES,
    DEFAULT_GRID,
    GRID_MODES,
    color_values as read_color_values,
    grid_column,
)
from src.analysis.plotting import (
    _NOISE_COLOR,
    _ordered_categories,
    _palette_for_categories,
    compose_embedding_plot_title,
)

if TYPE_CHECKING:  # importing it for real would close the loop context -> anatomy -> this module
    from src.analysis.embedding_app.context import AppContext

# "neutro" first, same convention as embedding_coloring.COLOR_MODES/the notebook prototype -
# the neutral single-color view is always available and always the default, every other
# entry is a registered color_by mode name.
NEUTRAL_MODE = "neutral"
_NEUTRAL_DESCRIPTION = (
    "No coloring: every point is a patient, all the same color. "
    "Use it to read the shape of the embedding without any other information."
)
COLOR_MODE_ORDER: tuple[str, ...] = (NEUTRAL_MODE, *COLOR_MODES.keys())

# The metadata column a clustering run's own labels are in, read from the registry rather than
# written out again: the panels that group subjects by cluster all index by it.
_CLUSTER_LABEL_COLUMN = COLOR_MODES["cluster_label"].column


def _color_label(mode_name: str) -> str | None:
    return None if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label


def run_title(run: ProductionRun, mode_name: str) -> str:
    """Same production-style title every other plot in this pipeline uses (e.g. "Lesions -
    Umap - dataset") - compose_embedding_plot_title is the single source of truth for this
    format, never re-derived by hand here."""
    return compose_embedding_plot_title(run.results_relative_path, run.method, _color_label(mode_name))


def _log_decade_ticks(values: np.ndarray) -> tuple[list[float], list[str]]:
    """Decade tick positions (in log10 space) spanning `values`' real (non-log) range, e.g.
    [1, 10, 100, 1000] for a 1..2000 range - the same "one tick per order of magnitude" a
    matplotlib LogNorm colorbar's default LogFormatter would pick, reimplemented here because
    Plotly has no log-scale colorbar of its own (see build_embedding_figure's docstring)."""
    lo = int(np.floor(np.log10(values.min())))
    hi = int(np.ceil(np.log10(values.max())))
    ticks = [10.0**exponent for exponent in range(lo, hi + 1)]
    return [float(np.log10(tick)) for tick in ticks], [f"{tick:g}" for tick in ticks]


def build_embedding_figure(
    embedding: np.ndarray,
    metadata: pd.DataFrame,
    mode_name: str,
    xlabel: str,
    ylabel: str,
    title: str,
    zlabel: str | None = None,
    grid: str = DEFAULT_GRID,
    modality: str | None = None,
) -> go.Figure:
    """Builds the Plotly figure for one (run, color mode) combination - 2D if `zlabel` is
    None, 3D otherwise (branches on `embedding.shape[1]`/`zlabel` the same way the
    post-results_analysis notebook's show_embedding_plotly prototype does, since this
    function IS that prototype, promoted to reusable src/ code once the notebook exploration
    settled on a final style - never a re-derivation by hand).

    Unlike the removed plot_embedding_interactive, a continuous mode's log_scale is honored
    here: values are log10-transformed for the marker color, with the colorbar's own ticks
    relabeled back to real units (_log_decade_ticks) - plotly has no direct LogNorm-equivalent
    color axis, so this is done by hand rather than left linear as the old function was.

    Raises UndisplayableRunError-independent ValueErrors for a bad embedding/mode/metadata
    combination (e.g. `mode_name` not in COLOR_MODE_ORDER) - a caller that only ever offers
    COLOR_MODE_ORDER's own entries as UI choices should never actually hit these.

    `modality` is the run's own ProductionRun.modality, only needed to enforce a mode's
    restricted_to_modality (06-10-26, on request: disconnection_load/disconnection_mean only
    apply to an sdc run) - None (the default) skips that check, for callers with no modality
    concept of their own (src/pipeline/plot_tuning_embedding_3d.py, replotting a tuning sweep).
    graph_content_for, the production caller, always passes run.modality.
    """
    if mode_name not in COLOR_MODE_ORDER:
        raise ValueError(f"unknown color mode {mode_name!r} - known: {list(COLOR_MODE_ORDER)}")
    if mode_name != NEUTRAL_MODE:
        restriction = COLOR_MODES[mode_name].restricted_to_modality
        if restriction is not None and modality is not None and modality != restriction:
            raise ValueError(
                f"color mode {mode_name!r} only applies to modality={restriction!r} runs, not "
                f"{modality!r} - pick a different colour for this run"
            )
    is_3d = zlabel is not None
    if is_3d and embedding.shape[1] != 3:
        raise ValueError(f"zlabel given but embedding has {embedding.shape[1]} columns, not 3")
    if not is_3d and embedding.shape[1] < 2:
        raise ValueError(f"The figure needs at least 2 columns, got shape {embedding.shape}")

    scatter_cls = go.Scatter3d if is_3d else go.Scatter
    marker_kwargs = dict(
        size=6,
        opacity=1.0 if is_3d else 0.85,
        line=dict(width=0.6, color="white") if is_3d else dict(width=0),
    )
    subject_ids = metadata["subject_id"].to_numpy() if "subject_id" in metadata.columns else None

    def _trace_kwargs(mask: np.ndarray | None = None) -> dict:
        idx = np.where(mask)[0] if mask is not None else np.arange(embedding.shape[0])
        kw = dict(x=embedding[idx, 0], y=embedding[idx, 1])
        if is_3d:
            kw["z"] = embedding[idx, 2]
        if subject_ids is not None:
            kw["text"] = subject_ids[idx]
            kw["hoverinfo"] = "text"
        return kw

    fig = go.Figure()
    has_colorbar = False  # set below for a continuous mode - moves the legend so it can't sit on top of it

    if mode_name == NEUTRAL_MODE:
        fig.add_trace(scatter_cls(**_trace_kwargs(), mode="markers", marker=dict(color="#3aa9e0", **marker_kwargs)))
    else:
        mode = COLOR_MODES[mode_name]
        # A grid mode (lesion volume, disconnection) reads whichever grid the button row below
        # the colour chips has selected; every other mode uses its own declared registry column.
        registry_column = grid_column(mode_name, grid) if mode_name in GRID_MODES else None
        values = read_color_values(metadata, mode_name, registry_column=registry_column)

        if mode.kind == "categorical":
            unique_categories = _ordered_categories(values, mode.categories)
            palette = _palette_for_categories(unique_categories, category_order=mode.categories)
            for category in unique_categories:
                fig.add_trace(
                    scatter_cls(
                        **_trace_kwargs(values == category), mode="markers", name=str(category),
                        marker=dict(color=palette[category], **marker_kwargs),
                    )
                )
        else:
            values = np.asarray(values, dtype=float)
            is_missing = np.isnan(values)
            color_values = values
            colorbar_kwargs: dict = dict(title=mode.label)
            if mode.log_scale:
                non_missing = values[~is_missing]
                # A NEGATIVE value is impossible for every log-scaled mode this registry has
                # (all are non-negative quantities) - that is corrupt data and must stop the plot.
                if (non_missing < 0).any():
                    raise ValueError(
                        f"Color mode {mode_name!r} is log_scale but has negative values - "
                        f"cannot log-transform, and a negative value is not legitimate here"
                    )
                # ZERO is legitimate and expected (30-09-26): lesion volume on the 2mm grid is
                # a nearest-neighbour resample of a 1mm mask, so a small lesion can come out at
                # 0 voxels without the mask being empty (docs/dev/metadata.md). log10(0) has no
                # position on the scale, which is exactly what "missing" means here - so it is
                # drawn neutral gray like any other missing value, not treated as corrupt.
                # Refusing the whole plot over it made the mode unusable for real cohorts.
                zero = ~is_missing & (values == 0)
                if zero.any():
                    logging.warning(
                        "color mode %r: %d subject(s) have a value of 0 - no position "
                        "on a log scale, drawn as missing (gray)",
                        mode_name, int(zero.sum()),
                    )
                    is_missing = is_missing | zero
                color_values = np.where(is_missing, np.nan, np.log10(np.where(is_missing, 1.0, values)))
                # Recomputed after folding the zeros in: the decade ticks are built from the
                # values actually drawn on the scale, and a 0 left in here would make the
                # lower bound log10(0) = -inf.
                non_missing = values[~is_missing]
                if non_missing.size:
                    tickvals, ticktext = _log_decade_ticks(non_missing)
                    colorbar_kwargs = dict(title=mode.label, tickvals=tickvals, ticktext=ticktext)

            if is_missing.any():
                fig.add_trace(
                    scatter_cls(
                        **_trace_kwargs(is_missing), mode="markers", name="missing",
                        marker=dict(color=_NOISE_COLOR, **marker_kwargs),
                    )
                )
            # AUDIT_FINDINGS.md #65: this trace used to be added unconditionally - when
            # every value for this color mode is NaN (e.g. "nihss" on a dataset without
            # not enriched in the registry yet), it got x=[]/y=[] (nothing to plot) but
            # still showed up as a legend entry with mode.label and no visible marker,
            # confusing next to the real "missing" trace that already explains the gap.
            if (~is_missing).any():
                has_colorbar = True
                fig.add_trace(
                    scatter_cls(
                        **_trace_kwargs(~is_missing), mode="markers", name=mode.label,
                        # showlegend=False (02-10-26 feedback: "la legenda ... si sovrappone"):
                        # the colorbar already carries this trace's own name as its title, so a
                        # legend entry repeating it just duplicates that label - and Plotly's
                        # default legend position (top-right) sits exactly where the colorbar
                        # does, so the two visibly overlapped. The "missing"/"centroide" entries
                        # above/below still need the legend, so it is moved (not removed) below.
                        showlegend=False,
                        marker=dict(
                            color=color_values[~is_missing], colorscale="Viridis", colorbar=colorbar_kwargs,
                            **marker_kwargs,
                        ),
                    )
                )

    axis_style = dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=_GRID_BORDER)
    layout_kwargs = dict(
        title=dict(text=title, font=dict(size=18, family=_FONT_STACK, color=_TEXT_COLOR), x=0.02, xanchor="left"),
        template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR),
        # Extra bottom margin only where the legend is relocated there (has_colorbar) - a plain
        # categorical/neutral mode keeps the default top-right legend, no colorbar to collide with.
        margin=dict(l=10, r=10, t=70, b=70 if has_colorbar else 10),
        height=680 if is_3d else 560,
    )
    if has_colorbar:
        # A continuous mode's colorbar sits at the plot's right edge, the same corner Plotly's
        # own default legend occupies - moved below the plot instead of overlapping it.
        layout_kwargs["legend"] = dict(orientation="h", xanchor="center", x=0.5, yanchor="top", y=-0.12)
    if is_3d:
        thin_axis = dict(showbackground=False, showgrid=False, zeroline=True, linewidth=1, showline=True)
        layout_kwargs["scene"] = dict(
            xaxis=dict(title=xlabel, **thin_axis),
            yaxis=dict(title=ylabel, **thin_axis),
            zaxis=dict(title=zlabel, **thin_axis),
            aspectmode="data",
        )
    else:
        layout_kwargs["xaxis"] = dict(title=xlabel, **axis_style)
        layout_kwargs["yaxis"] = dict(title=ylabel, **axis_style)

    fig.update_layout(**layout_kwargs)
    return fig


def _add_cluster_centroids_trace(
    figure: go.Figure, embedding: np.ndarray, metadata: pd.DataFrame, cluster_space: np.ndarray | None = None
) -> None:
    """Overlays a black-outlined circle + cluster_label text at each cluster's centroid
    (cluster_centroids_with_nearest_subject) on top of `figure`'s own point traces, as an
    extra Plotly trace on the live interactive scatter.

    The trace starts hidden (visible="legendonly", 29-09-26 on request): the circles sit on top
    of the points and are a deliberate lookup ("where is cluster 3 centred"), not the default
    view. Clicking its legend entry turns it on.

    A no-op for a dim_reduction.py run (no cluster_label column) - mutates `figure` in place,
    nothing to return."""
    column = COLOR_MODES["cluster_label"].column
    if column not in metadata.columns:
        return
    centroids = cluster_centroids_with_nearest_subject(embedding, metadata, cluster_space)
    dim_columns = [c for c in centroids.columns if c.startswith("dim")]
    is_3d = len(dim_columns) == 3
    scatter_cls = go.Scatter3d if is_3d else go.Scatter
    coords_kwargs = dict(x=centroids[dim_columns[0]], y=centroids[dim_columns[1]])
    if is_3d:
        coords_kwargs["z"] = centroids[dim_columns[2]]
    figure.add_trace(
        scatter_cls(
            **coords_kwargs, mode="markers+text", name="centroid",
            text=[str(label) for label in centroids.index],
            textposition="middle center",
            textfont=dict(color="black", size=11, family=_FONT_STACK),
            marker=dict(size=18 if is_3d else 22, color="rgba(0,0,0,0)", line=dict(width=2, color="black")),
            hovertext=[
                f"cluster {label} - representative: {row.nearest_subject_id}"
                for label, row in centroids.iterrows()
            ],
            hoverinfo="text",
            # Off until the reader asks for it from the legend (29-09-26, on request).
            # "legendonly" is the one way to do this that keeps the trace in the legend as a
            # dimmed, clickable entry - visible=False would drop it from the legend entirely,
            # leaving no way to turn it back on.
            visible="legendonly",
            showlegend=True,
        )
    )


def graph_content_for(
    run: ProductionRun, mode_name: str, grid: str = DEFAULT_GRID
) -> html.P | dcc.Graph:
    """The graph-area.children Dash callback's actual body, pulled out as a plain function -
    directly unit-testable (no Dash callback-context wrapping to fight, see
    tests/unit/test_embedding_app.py) and kept as the single place this logic lives, not
    duplicated between a callback closure and a test harness.

    Returns an html.P status message (never raises) for a run that can't be displayed
    (UndisplayableRunError from load_run, or a ValueError from build_embedding_figure - e.g. a
    color mode's own persisted column missing from this particular run's metadata.csv), a
    dcc.Graph otherwise. Modebar hidden via the Graph's own config (Plotly's modebar is
    rendered inside the figure's own DOM subtree, unreachable by page-level CSS).

    config has no "responsive": True (2026-08-14, on request: the graph "si sminchia" on
    scroll) - Plotly's responsive mode attaches a ResizeObserver that recomputes the plot's
    size on every layout event, not just an actual window resize; scrolling a page that
    contains a WebGL scatter3d canvas is exactly the kind of layout event known to misfire
    that observer (a corrupted/squished redraw, not a crash - easy to miss in isolated
    testing, only visible once the page is tall enough to scroll). Sized instead by CSS
    (.graph-wrap/.graph-wrap > div, width: 100%) applied once at mount - the graph still
    fills the available width on load, it just doesn't keep re-measuring itself afterwards.
    """
    try:
        embedding, metadata = load_run(run)
    except UndisplayableRunError as exc:
        return html.P(str(exc), className="status-message")

    zlabel = f"{run.method} dim 3" if embedding.shape[1] == 3 else None
    try:
        figure = build_embedding_figure(
            embedding, metadata, mode_name,
            f"{run.method} dim 1", f"{run.method} dim 2", run_title(run, mode_name),
            grid=grid,
            zlabel=zlabel,
            modality=run.modality,
        )
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    _add_cluster_centroids_trace(figure, embedding, metadata, load_cluster_space(run))
    note = view_note_for(run)
    if note is not None:
        figure.add_annotation(
            text=note, xref="paper", yref="paper", x=0, y=-0.12, showarrow=False, xanchor="left",
            font=dict(size=11, color="#555", family=_FONT_STACK),
        )

    # modeBarButtons (not modeBarButtonsToRemove): an explicit whitelist survives 2D<->3D
    # unchanged (Plotly's default button set differs between them - a removal-list would need
    # its own 3D variant to actually hide everything else), and "toImage" is the one save
    # affordance this app offers per plot (01-09-26, on request) - still hidden until hover
    # (Plotly's own default displayModeBar="hover"), so the minimal look from 14-08-26 holds.
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    return dcc.Graph(id="embedding-graph", figure=_italian_figure(figure), config=config, style={"width": "100%"})


def cluster_options(metadata: pd.DataFrame) -> list[int]:
    """Sorted distinct cluster_label values in `metadata` - only meaningful for a clustering.py
    run (dim_reduction.py runs never have this column, see ProductionRun.pipeline). HDBSCAN's
    noise label (-1) is included like any other value - the same treatment
    COLOR_MODES["cluster_label"] already gives it, never hidden."""
    column = COLOR_MODES["cluster_label"].column
    return sorted(int(value) for value in pd.unique(metadata[column]))


def cluster_centroids_with_nearest_subject(
    embedding: np.ndarray, metadata: pd.DataFrame, cluster_space: np.ndarray | None = None
) -> pd.DataFrame:
    """Per-cluster centroid (mean of that cluster's own embedding coordinates) plus the real
    subject_id closest to it in that same embedding space (Euclidean distance), read from
    `metadata` directly. A centroid is a mean point, not
    a real subject - this is the closest real one, used both to overlay circled centroids on
    the embedding scatter (graph_content_for) and to pick which real subject's anatomy the
    "Soggetto rappresentativo del cluster" panel shows (representative_subject_content_for).

    Distance is computed in the reduced embedding space (the same dim0/dim1[/dim2] coordinates
    plotted), not the original pre-reduction feature space - consistent with where the
    centroid circle itself is drawn (see docs/dev/anatomical_maps.md).

    `cluster_space` (a run shown on a twin's coordinates, see load_run/load_cluster_space): the
    matrix the clusters were computed on. The centroid and the nearest real subject are then
    found there, and the dim columns hold the *drawn* coordinates of that nearest subject (the
    mean of the drawn points would not be the cluster's centre); distance_to_centroid is in
    cluster_space.

    Returns one row per cluster_label, indexed by it, with columns dim0..dim{n-1} (centroid
    coordinates, or the nearest subject's drawn coordinates with cluster_space),
    nearest_subject_id, distance_to_centroid.

    Raises ValueError if `metadata` has no cluster_label column (only a clustering.py run has
    one - dim_reduction.py runs never reach this) or if `embedding`/`metadata` have mismatched
    row counts (would silently misalign points to the wrong subject_id otherwise)."""
    column = COLOR_MODES["cluster_label"].column
    if column not in metadata.columns:
        raise ValueError(f"metadata has no {column!r} column - centroids only apply to a clustering.py run")
    if len(embedding) != len(metadata):
        raise ValueError(f"embedding has {len(embedding)} rows but metadata has {len(metadata)} - can't align them")
    if cluster_space is not None and len(cluster_space) != len(metadata):
        raise ValueError(f"cluster_space has {len(cluster_space)} rows but metadata has {len(metadata)} - can't align them")

    dim_columns = [f"dim{i}" for i in range(embedding.shape[1])]
    coords = pd.DataFrame(embedding, columns=dim_columns)
    coords[column] = metadata[column].to_numpy()
    coords["subject_id"] = metadata["subject_id"].to_numpy()

    rows = []
    for cluster_label, group in coords.groupby(column):
        if cluster_space is None:
            centroid = group[dim_columns].mean()
            distances = np.linalg.norm(group[dim_columns].to_numpy() - centroid.to_numpy(), axis=1)
            nearest_position = distances.argmin()
            drawn = centroid
        else:
            members = cluster_space[group.index.to_numpy()]
            distances = np.linalg.norm(members - members.mean(axis=0), axis=1)
            nearest_position = distances.argmin()
            drawn = group[dim_columns].iloc[nearest_position]
        rows.append({
            column: cluster_label,
            **drawn.to_dict(),
            "nearest_subject_id": group["subject_id"].iloc[nearest_position],
            "distance_to_centroid": float(distances[nearest_position]),
        })
    return pd.DataFrame(rows).set_index(column)


def color_mode_description(mode_name: str) -> str:
    """The sentence shown above the plot for `mode_name` (neutral included)."""
    return _NEUTRAL_DESCRIPTION if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].description


def color_mode_description_children(mode_name: str) -> str | list:
    """What fills the description block above the plot: the sentence alone, or, for a mode with a `legend`, the
    sentence followed by one bullet per label saying what it means."""
    description = color_mode_description(mode_name)
    legend = () if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].legend
    if not legend:
        return description
    return [description, html.Ul([html.Li([html.B(label), f": {meaning}"]) for label, meaning in legend], className="color-legend")]


def _color_button_label(mode_name: str) -> str:
    # Raw mode.label, not .capitalize()'d - "NIHSS (severity)".capitalize() would produce
    # "Nihss (severity)" (str.capitalize lowercases every character but the first), the same
    # trap the notebook prototype's _panel_title left uncorrected; sidestepped here by not
    # reformatting the label's casing at all, same as compose_embedding_plot_title's own
    # color_by segment (src/analysis/plotting.py), which interpolates the label verbatim
    # instead of re-casing it.
    return "neutral" if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label


def register_callbacks(app: Dash, context: AppContext) -> None:
    """Wires this panel to the app. Called once by build_app, which owns the layout the ids
    below refer to."""
    @app.callback(
        Output("selected-color-mode", "data"),
        Input({"type": "color-mode-btn", "mode": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _select_color_mode(_all_n_clicks: list[int]) -> str:
        if ctx.triggered_id is None:
            raise PreventUpdate
        return ctx.triggered_id["mode"]

    @app.callback(
        Output({"type": "color-mode-btn", "mode": ALL}, "className"),
        Input("selected-color-mode", "data"),
        State({"type": "color-mode-btn", "mode": ALL}, "id"),
    )
    def _highlight_active_button(selected_mode: str, ids: list[dict]) -> list[str]:
        return ["active" if button_id["mode"] == selected_mode else "" for button_id in ids]

    @app.callback(
        Output("selected-grid", "data"),
        Input({"type": "grid-btn", "grid": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _select_grid(_all_n_clicks: list[int]) -> str:
        if ctx.triggered_id is None:
            raise PreventUpdate
        return ctx.triggered_id["grid"]

    @app.callback(
        Output({"type": "grid-btn", "grid": ALL}, "className"),
        Input("selected-grid", "data"),
        State({"type": "grid-btn", "grid": ALL}, "id"),
    )
    def _highlight_active_grid(selected_grid: str, ids: list[dict]) -> list[str]:
        return ["active" if button_id["grid"] == selected_grid else "" for button_id in ids]

    @app.callback(Output("color-description", "children"), Input("selected-color-mode", "data"))
    def _describe_color_mode(selected_mode: str) -> str | list:
        return color_mode_description_children(selected_mode)

    @app.callback(
        Output("color-grid-row", "style"),
        Input("selected-color-mode", "data"),
    )
    def _toggle_grid_row(selected_mode: str) -> dict:
        return {} if selected_mode in GRID_MODES else {"display": "none"}

    @app.callback(
        Output("graph-area", "children"),
        Input("run-picker", "value"),
        Input("selected-color-mode", "data"),
        Input("selected-grid", "data"),
    )
    def _update_graph(run_key: str | None, selected_mode: str, grid: str):
        if run_key in (None, UNSET):
            raise PreventUpdate
        return graph_content_for(context.runs_by_key[run_key], selected_mode, grid)
