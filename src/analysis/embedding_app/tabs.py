"""The tabs of the page and the index of its sections.

Which tab a section sits in, and which sections a run has at all: a dim_reduction run has no
clustering sections, only an agglomerative run has the dendrogram. The index is built from the
same table, so it never links to a section that is not there.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from dash import ALL, Dash, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate

from src.analysis.embedding_app.panels.pca_maps import _is_pca_run
from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import ProductionRun


# --- Page tabs and index (08-10-26, tabs 23-10-26) ---------------------------------------------

# The page shows one view of the run at a time. A tab exists only for a run that has what it shows: the embedding
# for any run, the clustering panels for a clustering run, the dendrogram for an agglomerative one.
TAB_EMBEDDING = "embedding"
TAB_CLUSTERING = "clustering"
TAB_DENDROGRAM = "dendrogram"
PAGE_TAB_LABELS: dict[str, str] = {TAB_EMBEDDING: "Embedding", TAB_CLUSTERING: "Clustering", TAB_DENDROGRAM: "Dendrogram"}


def _is_clustering_run(run: ProductionRun | None) -> bool:
    return run is not None and run.pipeline == "clustering"


def _is_agglomerative_clustering_run(run: ProductionRun | None) -> bool:
    return _is_clustering_run(run) and run.method == "agglomerative"


_TAB_SHOWN: dict[str, Callable[[ProductionRun | None], bool]] = {
    TAB_EMBEDDING: lambda run: run is not None,
    TAB_CLUSTERING: _is_clustering_run,
    TAB_DENDROGRAM: _is_agglomerative_clustering_run,
}


def page_tabs_for(run: ProductionRun | None) -> list[str]:
    """The tabs `run` has, in page order; none without a run."""
    return [tab for tab, shown in _TAB_SHOWN.items() if shown(run)]


def active_page_tab(run: ProductionRun | None, selected: str | None) -> str:
    """The tab shown for `run` when the user last chose `selected`: that one if the run has it, else the embedding
    (a run without the chosen tab, or none chosen yet). Raises ValueError for a run-less page."""
    if run is None:
        raise ValueError("there is no tab without a run")
    return selected if selected in page_tabs_for(run) else TAB_EMBEDDING


def tab_is_active(run: ProductionRun, selected: str | None, tab: str) -> bool:
    """Whether `tab` is the one shown for `run` after the user chose `selected` (active_page_tab). What the callbacks of
    the Clustering and Dendrogram tabs ask first: a tab that is not shown builds nothing."""
    return active_page_tab(run, selected) == tab


if TYPE_CHECKING:  # importing it for real would close a loop through the panels
    from src.analysis.embedding_app.context import AppContext


# (anchor id, label, tab it sits in, shown for this run?) in page order. The panels that only exist for some runs
# (see _update_cluster_picker and _update_disconnectome_panel_visibility) are listed only for
# those runs, so the index never links to a hidden section. A tab of None is in every tab.
_INDEX_SECTIONS: tuple[tuple[str, str, str | None, Callable[[ProductionRun | None], bool]], ...] = (
    ("controls-section", "Run choice", None, lambda run: True),
    ("embedding-section", "Embedding Visualization", TAB_EMBEDDING, lambda run: run is not None),
    ("lesion-panel", "Lesion anatomy", TAB_EMBEDDING, lambda run: run is not None),
    ("disconnectome-panel", "Disconnection (SDC)", TAB_EMBEDDING, lambda run: run is not None and run.modality == "sdc"),
    ("pca-map-panel", "Component maps", TAB_EMBEDDING, lambda run: run is not None and _is_pca_run(run)),
    ("clustering-section", "Clustering Explorer", TAB_CLUSTERING, _is_clustering_run),
    ("cluster-map-panel", "Overlap map per cluster", TAB_CLUSTERING, _is_clustering_run),
    (
        "disconnection-map-panel", "Disconnection per cluster", TAB_CLUSTERING,
        lambda run: _is_clustering_run(run) and run.modality == "sdc",
    ),
    ("representative-subject-panel", "Representative subject", TAB_CLUSTERING, _is_clustering_run),
    ("cluster-description-panel", "Cluster description", TAB_CLUSTERING, _is_clustering_run),
    ("cluster-composition-panel", "Cluster composition", TAB_CLUSTERING, _is_clustering_run),
    ("cluster-quality-panel", "Clustering evaluation", TAB_CLUSTERING, _is_clustering_run),
    ("dendrogram-panel", "Dendrogram Explorer", TAB_DENDROGRAM, _is_agglomerative_clustering_run),
)


def index_entries_for(run: ProductionRun | None, tab: str | None = None) -> list[tuple[str, str]]:
    """(anchor id, label) of the page sections `run` has, in page order; with `tab`, only those on that tab (and the
    ones on every tab). Raises ValueError for a tab that does not exist."""
    if tab is not None and tab not in PAGE_TAB_LABELS:
        raise ValueError(f"unknown tab {tab!r} - known: {list(PAGE_TAB_LABELS)}")
    return [
        (anchor, label) for anchor, label, section_tab, shown in _INDEX_SECTIONS
        if shown(run) and (tab is None or section_tab in (None, tab))
    ]


def _index_links(entries: list[tuple[str, str]]) -> list[html.A]:
    return [html.A(label, href=f"#{anchor}", className="page-index-link") for anchor, label in entries]


def register_callbacks(app: Dash, context: AppContext) -> None:
    """Wires this panel to the app. Called once by build_app, which owns the layout the ids
    below refer to."""
    @app.callback(
        Output("selected-page-tab", "data"),
        Input({"type": "page-tab-btn", "tab": ALL}, "n_clicks"),
        Input("run-picker", "value"),
        State("selected-page-tab", "data"),
        prevent_initial_call=True,
    )
    def _select_page_tab(_all_n_clicks: list[int], run_key: str | None, current: str):
        if isinstance(ctx.triggered_id, dict):
            return ctx.triggered_id["tab"]
        if run_key in (None, UNSET):
            raise PreventUpdate
        return active_page_tab(context.runs_by_key[run_key], current)

    @app.callback(
        Output({"type": "page-tab-btn", "tab": ALL}, "className"),
        Output({"type": "page-tab-btn", "tab": ALL}, "style"),
        Output("page-tab-bar", "style"),
        Output("tab-embedding", "style"),
        Output("tab-clustering", "style"),
        Output("tab-dendrogram", "style"),
        Input("selected-page-tab", "data"),
        Input("run-picker", "value"),
        State({"type": "page-tab-btn", "tab": ALL}, "id"),
    )
    def _apply_page_tab(selected: str | None, run_key: str | None, ids: list[dict]):
        """Shows the active tab, marks its button and hides the buttons of the tabs the run has not got (and the whole
        bar when the run has only one)."""
        if run_key is None:
            raise PreventUpdate
        if run_key == UNSET:  # nothing is shown: run-content is hidden, and the bar and tabs stay as they were
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        available = page_tabs_for(run)
        active = active_page_tab(run, selected)
        classes = ["tab-btn active" if button["tab"] == active else "tab-btn" for button in ids]
        styles = [{} if button["tab"] in available else {"display": "none"} for button in ids]
        bar_style = {} if len(available) > 1 else {"display": "none"}
        tab_styles = [{"display": "block"} if tab == active else {"display": "none"} for tab in PAGE_TAB_LABELS]
        return classes, styles, bar_style, *tab_styles

    @app.callback(
        Output("run-content", "style"),
        Output("no-run-message", "style"),
        Input("run-picker", "value"),
    )
    def _toggle_run_content(run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        return ({"display": "none"}, {}) if run_key == UNSET else ({}, {"display": "none"})

    @app.callback(
        Output("page-index-links", "children"),
        Input("run-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_page_index(run_key: str | None, selected_tab: str | None):
        if run_key is None:
            raise PreventUpdate
        if run_key == UNSET:
            return _index_links(index_entries_for(None, TAB_EMBEDDING))
        run = context.runs_by_key[run_key]
        return _index_links(index_entries_for(run, active_page_tab(run, selected_tab)))

def page_index() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Details(
        id="page-index",
        className="page-index",
        children=[
            html.Summary("Index"),
            html.Nav(id="page-index-links", children=_index_links(index_entries_for(None, TAB_EMBEDDING))),
        ],
    )

def tab_bar() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
        id="page-tab-bar",
        className="tab-bar",
        children=[
            html.Button(
                label, id={"type": "page-tab-btn", "tab": name}, n_clicks=0,
                className="tab-btn active" if name == TAB_EMBEDDING else "tab-btn",
            )
            for name, label in PAGE_TAB_LABELS.items()
        ],
    )
