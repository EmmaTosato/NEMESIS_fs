"""Who the subjects of a cluster are: the demographic and clinical table, and the
composition of each cluster next to the others.

Reads the variables declared in cluster_description/cluster_composition and prints them as
they are - counts, medians, shares - with no statistical test between clusters: the comparison
is made by reading, not by a p-value.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pandas as pd
from dash import Dash, Input, Output
from dash import dcc, html
from dash.exceptions import PreventUpdate

from src.analysis.cluster_composition import COMPOSITION_VARIABLES, build_composition_figure, composition_frame
from src.analysis.cluster_description import (
    CLUSTER_DESCRIPTION_VARIABLES,
    ClusterDescriptionVariable,
    ClusterStats,
    build_cluster_description_figure,
    cluster_composition,
    clusters_comparison_stats,
)
from src.analysis.embedding_app.blocks import _warning_box
from src.analysis.embedding_app.panels.overview import ALL_CLUSTERS
from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import run_metadata
from src.analysis.embedding_app.style import _italian_figure
from src.analysis.embedding_app.tabs import TAB_CLUSTERING, tab_is_active
from src.analysis.plotting import _palette_for_labels
from src.utils.number_format import format_number


def _unregistered_subjects_warning(unregistered: list[str]) -> html.Div | None:
    """Sibling of _missing_subjects_warning for cluster_description_content_for (29-09-26) - a
    DIFFERENT gap, deliberately worded so the two are never confused: _missing_subjects_warning
    is about a subject whose lesion/disconnectome FILE isn't on disk (excluded from that map),
    this one is about a subject with no row in assets/metadata/participants.csv at all (still
    counted in the panel's own n/total, just with no value for any variable). None when every
    subject of the cluster resolved."""
    if not unregistered:
        return None
    return _warning_box(
        f"{len(unregistered)} subjects of this cluster have no row in the registry "
        f"(assets/metadata/participants.csv). They count in the total of every variable, but "
        f"carry no value.",
        detail=", ".join(unregistered),
    )


def _format_continuous_cell(summary: dict, variable: ClusterDescriptionVariable) -> html.Td:
    """`media ± ds` at this variable's own declared precision, plus the coverage note where the
    variable does not cover the whole cluster.

    No in-cell bar (29-09-26, on request: "non voglio quelle righe colorate nella tabella, mi
    confondono la lettura"). The cross-cluster comparison is carried by the numbers alone -
    which is what the Italian formatting and the larger type are for - while the figure above
    stays the visual read.

    An empty cell is "—", never "nan ± nan" and never a blank that could read as a rendering gap.
    """
    if summary["n_available"] == 0:
        return html.Td([html.Div("—", className="stat-value stat-empty")])

    decimals = variable.decimals
    mean = format_number(summary["mean"], decimals)
    # std is None for a single subject: a standard deviation of one value does not exist, which
    # is a different statement from "0".
    spread = None if summary["std"] is None else f"± {format_number(summary['std'], decimals)}"

    value = [mean] if spread is None else [mean, " ", html.Span(spread, className="stat-sd")]
    return html.Td(
        [html.Div(value, className="stat-value"), _coverage_note(summary)],
        # Hover detail only - median/min/max enhance, they never gate: the headline number and
        # the coverage are both readable without hovering.
        title=(
            f"mediana {format_number(summary['median'], decimals)} · "
            f"min {format_number(summary['min'], decimals)} · "
            f"max {format_number(summary['max'], decimals)}"
        ),
    )


def _format_categorical_cell(summary: dict) -> html.Td:
    """Counts per category, sorted by name so a category keeps the same position in every row
    and the column can be read downwards. No proportion bar (29-09-26, on request) - the
    figure's own bar chart above carries that."""
    if summary["n_available"] == 0:
        return html.Td([html.Div("—", className="stat-value stat-empty")])

    label = " · ".join(f"{c} {summary['counts'][c]}" for c in sorted(summary["counts"]))
    return html.Td([html.Div(label, className="stat-value"), _coverage_note(summary)])


def _coverage_note(summary: dict) -> html.Span | None:
    """The n_available/n_total line, shown ONLY where the variable is actually incomplete.

    It used to sit under every cell: 25 near-identical fractions competing with the values they
    were annotating, which is how a coverage note stops being read at all. Printed only when it
    says something, it goes back to being a signal. Full coverage is not silently assumed
    either - the caption under the table states the rule."""
    if summary["n_available"] == summary["n_total"]:
        return None
    return html.Span(f"{summary['n_available']}/{summary['n_total']}", className="stats-n")


def _stats_table(entries: Sequence[tuple[str, str, ClusterStats, bool]]) -> html.Table:
    """One row per entry (name, swatch colour, stats, highlighted), one column per CLUSTER_DESCRIPTION_VARIABLES entry,
    so a variable is read down a column across the rows rather than by flipping a dropdown. The rows are clusters in
    the cross-cluster table and the cluster that splits plus the two it gives in the Dendrogram Explorer; the cells are
    the same in both (_format_continuous_cell, _format_categorical_cell)."""
    # Plain headers: the per-variable colored underline was dropped on request (29-09-26). The
    # figure above still colors each variable and the in-cell bars carry the same hue, so the
    # column/panel tie survives without a second colored rule competing with the header text.
    header = html.Tr([
        html.Th("Cluster"), html.Th("Subjects"),
        *[html.Th(variable.label) for variable in CLUSTER_DESCRIPTION_VARIABLES],
    ])

    rows = []
    for name, color, stat, highlighted in entries:
        size = [html.Div(format_number(stat.n_total, 0), className="stat-value")]
        if stat.n_unregistered:
            size.append(html.Span(f"{stat.n_unregistered} not in registry", className="stats-n"))
        cells = [
            _format_categorical_cell(stat.summaries[v.name]) if v.kind == "categorical"
            else _format_continuous_cell(stat.summaries[v.name], v)
            for v in CLUSTER_DESCRIPTION_VARIABLES
        ]
        rows.append(
            html.Tr(
                [
                    html.Td(html.Div([html.Span(className="stats-swatch", style={"background": color}), name], className="stats-cluster")),
                    html.Td(size),
                    *cells,
                ],
                className="selected" if highlighted else "",
            )
        )
    return html.Table([html.Thead(header), html.Tbody(rows)], className="stats-table")


def _clusters_comparison_table(stats: list[ClusterStats], selected_cluster: int | None) -> html.Div:
    """The cross-cluster comparison table rendered under the selected cluster's own figure
    (29-09-26, on request) - one row per cluster, one column per CLUSTER_DESCRIPTION_VARIABLES
    entry, so a variable is read down a column across clusters rather than by flipping the
    dropdown between them.

    A table rather than a second figure: the ask was for the numbers themselves, and a 5-8
    cluster x 5 variable grid is past the point where a reader can hold that many color classes
    apart. It doubles as the table view the figure's own fills require for accessibility. In-cell
    bars were tried and removed on request (29-09-26) - they competed with the digits rather
    than supporting them.

    Every cluster of the run is listed, including the selected one (highlighted) and hdbscan's
    noise bucket (-1, labelled as such rather than shown as a cluster named "-1"). With
    selected_cluster=None no row is highlighted (the comparison section has no chosen cluster)."""
    palette = _palette_for_labels([stat.cluster_label for stat in stats])
    entries = [
        (
            "Noise" if stat.cluster_label == -1 else f"Cluster {stat.cluster_label}", palette[stat.cluster_label], stat,
            stat.cluster_label == selected_cluster,
        )
        for stat in stats
    ]
    return html.Div(
        [
            _stats_table(entries),
            html.P(
                [
                    html.B("Values: "),
                    "mean ± standard deviation.",
                    html.Br(),
                    html.B("Sex: "),
                    "count per category.",
                    html.Br(),
                    html.B("Number under the value: "),
                    "subjects that have that variable, out of the cluster total. It appears only "
                    "where the variable does not cover the whole cluster.",
                    html.Br(),
                    html.B("Hover over a cell: "),
                    "median, minimum and maximum.",
                ],
                className="stats-caption",
            ),
        ],
        className="stats-table-wrap",
    )


def cluster_description_content_for(metadata: pd.DataFrame, cluster_label: int) -> dcc.Graph | html.Div | html.P:
    """Panel "Descrizione del cluster" (29-09-26, on request), shown after the two frequency-map
    panels - age/sex/education/NIHSS/lesion-volume composition of `cluster_label`'s subjects
    (src.analysis.cluster_description.cluster_composition/build_cluster_description_figure),
    every one of them read from assets/metadata/participants.csv (see that module's own
    docstring for why, not a run's own metadata.csv). Visible for any clustering.py run
    regardless of modality - unlike the two frequency-map panels, this doesn't need a
    disconnectome/lesion mask file at all, only the subject registry.

    Same never-raises contract as every other *_content_for function here: an empty cluster
    renders an html.P status message instead of crashing the callback. A cluster whose subjects
    are only *partly* in the registry is not an error at all (29-09-26, on request): the figure
    is built over everyone, with the unregistered subjects counted in each variable's n_total
    but contributing no value, and an _unregistered_subjects_warning line naming them is
    rendered above it - the same "partial result, never silent" shape the two anatomy panels
    already use for a subject whose mask file is missing. Rendered as a plain dcc.Graph (Plotly's own "toImage"
    camera icon is this panel's only export, same as the main embedding scatter) - no Salva
    HTML/PNG buttons, those exist only for the nilearn iframe-based anatomy panels above, which
    have no built-in export of their own."""
    try:
        composition, unregistered = cluster_composition(metadata, cluster_label)
        stats = clusters_comparison_stats(metadata)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")

    palette = _palette_for_labels([stat.cluster_label for stat in stats])
    figure = build_cluster_description_figure(composition, cluster_label, color=palette.get(cluster_label))
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}

    children: list = []
    warning = _unregistered_subjects_warning(unregistered)
    if warning is not None:
        children.append(warning)
    children.append(dcc.Graph(figure=_italian_figure(figure), config=config, style={"width": "100%"}))
    children.append(_clusters_comparison_table(stats, cluster_label))
    return html.Div(children)


def cluster_composition_content_for(metadata: pd.DataFrame) -> html.Div | html.P:
    """Panel "Composizione dei cluster" (07-10-26, on request), last panel of the page: every
    cluster of the run side by side, one plot per variable (dataset, lesion side, dominant lesion
    location as 100%-stacked bars; NIHSS, lesion volume, disconnection load as box plots), all
    read from assets/metadata/participants.csv (src.analysis.cluster_composition). Unlike
    "Descrizione del cluster" it does not depend on the chosen cluster: it is the same for the
    whole run, so its callback only listens to the run picker.

    Same never-raises contract as every other *_content_for function here: a run whose registry
    lacks a needed column renders an html.P status message. Subjects missing from the registry
    stay in the plots as missing values, named in an _unregistered_subjects_warning line."""
    try:
        frame, unregistered = composition_frame(metadata)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")

    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    children: list = []
    warning = _unregistered_subjects_warning(unregistered)
    if warning is not None:
        children.append(warning)
    children.append(
        html.Div(
            className="composition-grid",
            children=[
                dcc.Graph(figure=_italian_figure(build_composition_figure(frame, variable)), config=config, style={"width": "100%"})
                for variable in COMPOSITION_VARIABLES
            ],
        )
    )
    return html.Div(children)


if TYPE_CHECKING:  # importing it for real would close a loop through the panels
    from src.analysis.embedding_app.context import AppContext


def register_callbacks(app: Dash, context: AppContext) -> None:
    """Wires this panel to the app. Called once by build_app, which owns the layout the ids
    below refer to."""
    @app.callback(
        Output("cluster-description-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_cluster_description(run_key: str | None, cluster_label: int | str | None, selected_tab: str | None):
        if run_key in (None, UNSET) or cluster_label is None:
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        if cluster_label == ALL_CLUSTERS:
            return html.P("Choose a cluster to see its description.", className="status-message")
        return cluster_description_content_for(run_metadata(run), cluster_label)

    @app.callback(
        Output("cluster-composition-content", "children"),
        Input("run-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_cluster_composition(run_key: str | None, selected_tab: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        return cluster_composition_content_for(run_metadata(run))

def description_panel() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
        id="cluster-description-panel",
        className="anatomy-panel",
        style={"display": "none"},
        children=[
            html.H2("Cluster description", className="section-heading"),
            html.Div(id="cluster-description-content"),
        ],
    )

def composition_panel() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
        id="cluster-composition-panel",
        className="anatomy-panel",
        style={"display": "none"},
        children=[
            html.H2("Cluster composition", className="section-heading"),
            html.Div(id="cluster-composition-content"),
        ],
    )
