"""Logic behind src.pipeline.embedding_app - a live Dash app to explore any already-written
dim_reduction.py OR clustering.py production run interactively (2D or 3D, color buttons
instead of a dropdown, editorial styling), replacing the old per-run
embedding_plot_interactive.html (removed 2026-08-14, see src/analysis/plotting.py's module
docstring and docs/guides/embedding_app.md).

Extended 15-08-26 (docs/dev/clustering_migration_plan.md §3, the `X.shape[1] == 3` row) to
also discover clustering.py's own production runs, not just dim_reduction.py's - both write
the exact same on-disk shape (matrix.npy/metadata.csv/manifest.json under
production/<method>/<run_name>, see src.utils.artifacts.save_matrix), so a single discovery
pass generalizes over the `<pipeline>` path segment (`dim_reduction` or `clustering`) rather
than needing two separate code paths. A clustering run's metadata.csv additionally has a
`cluster_label` column (src.analysis.clustering_tuning appends it in production, see
clustering.py::_run_one_method) - registered as its own COLOR_MODES entry
(src/analysis/embedding_coloring.py), so this app can color a clustering run by cluster same
as it colors any run by dataset/side/volume/nihss, all through the same generic mechanism.

No refit, no server-side recomputation of the embedding itself - reads matrix.npy/metadata.csv
straight off disk (src.utils.artifacts.load_matrix), same "replot, never re-fit" contract
src/pipeline/replot_dim_reduction.py already established, extended here to cover 3-component runs
too (that script only ever handled 2). A run whose own saved embedding has more than 3
columns (e.g. a real production run kept at its full n_components, no viz-only projection
ever persisted to disk - see production_run_display_error's docstring) is reported as
undisplayable rather than silently sliced to its first 2/3 columns - lessons_learned.md #16.

Kept separate from src/analysis/understanding_umap_report.py / understanding_umap_dash.py on
purpose: those read fine-tuning sweep output (tuning_results.csv/embeddings.npz across a whole
metric x n_neighbors x min_dist grid) to explore *how a parameter choice shapes the embedding*;
this module reads exactly one already-chosen production run at a time, to explore *the result
production settled on* - same distinction the user drew explicitly (14-08-26): "questi fanno
tuning, noi dobbiamo fare production". Two different questions, two different tools - not
sharing a module just because both end up building Plotly figures.

Extended 01-09-26 with two anatomy panels, both promoted from exploratory notebook prototypes
(notebooks/post-results_analysis/embeddings_analysis.ipynb §4,
embedding_to_anatomy_mapping.ipynb §2 - the latter's own docstring already flagged this
promotion as its natural next step) onto src.analysis.anatomical_maps: clicking a point in the
embedding shows that subject's real lesion in an interactive nilearn 3D viewer
(lesion_viewer_content_for), and any clustering.py run (metadata has cluster_label) additionally
gets a per-cluster lesion overlap/frequency map (overlap_map_content_for). Same "no caching,
always a fresh disk read + rebuild" philosophy as the rest of this module - see build_app's own
docstring.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from dash import Dash, Input, Output, dcc, html
from dash.exceptions import PreventUpdate

from src.analysis.anatomical_maps import resolve_available_lesion_paths
from src.analysis.embedding_app.anatomy import (
    DEFAULT_DISCONNECTION_MAP_MODE,
    LesionViewerConfig,
    SdcViewerConfig,
    disconnectome_panel,
    lesion_panel,
    register_callbacks as register_anatomy,
)
from src.analysis.embedding_app.context import AppContext
from src.analysis.embedding_app.embedding_view import (
    COLOR_MODE_ORDER,
    NEUTRAL_MODE,
    _NEUTRAL_DESCRIPTION,
    _color_button_label,
    cluster_options,
    register_callbacks as register_embedding_view,
)
from src.analysis.embedding_app.panels.cluster_maps import (
    disconnection_map_panel,
    overlap_map_panel,
    register_callbacks as register_cluster_maps,
    representative_panel,
)
from src.analysis.embedding_app.panels.dendrogram import (
    layout as dendrogram_panel,
    register_callbacks as register_dendrogram,
)
from src.analysis.embedding_app.panels.description import (
    composition_panel,
    description_panel,
    register_callbacks as register_description,
)
from src.analysis.embedding_app.panels.overview import ALL_CLUSTERS
from src.analysis.embedding_app.panels.pca_maps import (
    layout as pca_map_panel,
    register_callbacks as register_pca_maps,
)
from src.analysis.embedding_app.panels.quality import layout as quality_panel, register_callbacks as register_quality
from src.analysis.embedding_app.picker import UNSET, register_callbacks as register_pickers
from src.analysis.embedding_app.runs import ProductionRun, run_metadata
from src.analysis.embedding_app.style import _INDEX_STRING
from src.analysis.embedding_app.tabs import TAB_EMBEDDING, page_index, register_callbacks as register_tabs, tab_bar
from src.analysis.embedding_coloring import DEFAULT_GRID, available_grids




def build_app(
    runs: list[ProductionRun],
    lesion_cfg: LesionViewerConfig,
    sdc_cfg: SdcViewerConfig,
    clustering_params_file: str | Path,
    cache_dir: str | Path,
    preload: bool = False,
) -> Dash:
    """Builds the Dash app: a run picker (dcc.Dropdown, one entry per discovered production
    run) plus a color-mode button group (COLOR_MODE_ORDER, styled as a chip row via CSS, not
    a second dropdown - the design brief this was built against, 14-08-26, asked for "bottoni"
    explicitly) driving one dcc.Graph. No client-side state beyond which button is active
    (dcc.Store) - the embedding/figure itself is rebuilt server-side on every run/color change
    (load_run + build_embedding_figure), never cached: at this cohort size (~1150 subjects,
    matrix.npy a few hundred KB at most) a fresh disk read + figure build is fast enough that
    a cache would add complexity for no measurable benefit. Same philosophy holds for the
    single-subject lesion viewer (one small NIfTI, also fast enough uncached) - but *not* for
    the per-cluster overlap map (same panel-family, very different cost: measured ~40ms/subject
    to load+resample, dominating the whole panel's response time for a real
    several-hundred-subject cluster). The two SDC disconnectome panels mirror that split -
    single-subject uncached, per-cluster kept - same per-subject cost shape, just averaging
    instead of counting (build_mean_map vs build_overlap_map). Everything this app does keep
    lives in its AppContext (src/analysis/embedding_app/context.py), built once here and read
    by the callbacks below; that module's docstring says what is memoised and on which key.

    suppress_callback_exceptions=True (01-09-26): the anatomy panels' own callbacks reference
    component ids ("embedding-graph") that only exist once graph_content_for actually renders a
    Graph into graph-area's children - never part of the static app.layout tree itself - the
    standard Dash idiom for wiring a callback to a dynamically-created component.

    clustering_params_file (01-09-26): config/registry/params_clustering.json (or an equivalent
    test fixture) - the picker's own "Parametri" selector (run_picker_values) reads
    each clustering method's registered tag_param list from it, so a run can be narrowed by its
    own n_clusters/linkage/etc., not just by the upstream embedding's metric/n_components.

    Raises ValueError if `runs` is empty - an app with a run picker offering nothing to pick
    is a broken starting state, not a legitimate empty one (unlike
    discover_production_runs itself, which legitimately can return an empty list for a fresh
    checkout - the CLI entry point, src.pipeline.embedding_app, is what decides that's worth
    failing loudly on before ever calling this).
    """
    if not runs:
        raise ValueError("The app needs at least one production run - none were discovered, nothing to display")

    context = AppContext.build(runs, lesion_cfg, sdc_cfg, clustering_params_file, cache_dir)

    app = Dash(__name__, suppress_callback_exceptions=True)
    app.index_string = _INDEX_STRING

    color_buttons = [
        html.Button(
            _color_button_label(mode),
            id={"type": "color-mode-btn", "mode": mode},
            n_clicks=0,
            className="active" if mode == NEUTRAL_MODE else "",
        )
        for mode in COLOR_MODE_ORDER
    ]

    # Resolved once at build time, not per callback: which grids the registry holds is a
    # property of participants.csv, which this process does not rewrite while running.
    grid_buttons = [
        html.Button(
            grid,
            id={"type": "grid-btn", "grid": grid},
            n_clicks=0,
            className="active" if grid == DEFAULT_GRID else "",
        )
        for grid in available_grids()
    ]

    # 7-step decision order, left to right (2026-08-14, on request - replaces the previous
    # single flat "every run from every method mixed together" dropdown, then extended with
    # explicit Metrica/Componenti steps rather than leaving them buried in the Run label's own
    # free-text run_name): Dato (modality) -> Pipeline -> Metodo -> Riduzione -> Metrica -> Componenti ->
    # Run (scoped by every step before it). Pipeline became a real choice, not a fixed label,
    # 15-08-26 (docs/dev/clustering_migration_plan.md §3) once this app started discovering
    # clustering.py runs too - Metrica/Componenti still show up for a clustering-pipeline run
    # (uniform layout across both pipelines), just resolved to their one NO_METRIC/
    # NO_N_COMPONENTS sentinel option each , since
    # clustering method params have no metric/n_components axis to offer. Every selector's options are
    # filled by the picker callback below, empty at layout-build time.
    def _picker_field(label: str, dropdown_id: str, field_id: str | None = None, label_id: str | None = None) -> html.Div:
        extra = {} if field_id is None else {"id": field_id}
        label_extra = {} if label_id is None else {"id": label_id}
        return html.Div(
            className="picker-field",
            children=[html.Label(label, className="picker-label", **label_extra), dcc.Dropdown(id=dropdown_id, clearable=False)],
            **extra,
        )

    app.layout = html.Div(
        className="page",
        children=[
            html.H1("Embedding Explorer", className="page-title"),
            html.P(
                "Interactive exploration of production runs — choose a run and a coloring.",
                className="page-subtitle",
            ),
            html.Div(
                id="controls-section",
                className="controls",
                children=[
                    # Two rows, left to right in the order of the cascade (PICKER_FACETS): each selector
                    # offers only what is compatible with the ones before it. "Soggetti" comes after
                    # "Riduzione" (12-10-26 order -> 22-10-26, on request). "Riavvia" puts every selector back at "---".
                    html.Div(
                        className="picker-row",
                        children=[
                            _picker_field("Data", "modality-picker"),
                            _picker_field("Pipeline", "pipeline-picker"),
                            _picker_field("Method", "method-picker"),
                            # Hidden for a dim_reduction run (08-10-26, on request): there the Metodo already
                            # is the reduction method, so this step would only offer one empty option.
                            _picker_field("Reduction", "reduction-picker", field_id="reduction-picker-field"),
                            _picker_field("Subjects", "n-subjects-picker"),
                        ],
                    ),
                    html.Div(
                        className="picker-row",
                        children=[
                            _picker_field("Metric", "metric-picker"),
                            _picker_field("Components", "n-components-picker"),
                            # "Parametri" (01-09-26, on request): real clustering runs vary by
                            # more than just the upstream embedding's metric/n_components - each
                            # method's own hyperparameters (n_clusters/linkage for agglomerative,
                            # etc.) do too. NO_METRIC-only for dim_reduction (see run_picker_values).
                            # Agglomerative has two (SPLIT_TAG_PARAMS): k here, linkage and metric next; the label and
                            # the second selector follow the method (_update_tag_params_selectors).
                            _picker_field("Parameters", "tag-params-picker", label_id="tag-params-label"),
                            _picker_field("Linkage / metric", "tag-params-rest-picker", field_id="tag-params-rest-field"),
                            _picker_field("Run", "run-picker"),
                            html.Button("Reset", id="reset-pickers-btn", n_clicks=0, className="save-btn"),
                        ],
                    ),
                    html.Div(color_buttons, className="color-buttons chips-balanced"),
                    # Only meaningful while a grid mode (lesion volume, disconnection load/mean)
                    # is the active colour mode, so it is hidden otherwise (a grid chooser
                    # floating under an unrelated mode reads as a second, broken colour row).
                    # Built from the grids the registry can actually serve today.
                    html.Div(
                        [
                            html.Span("Grid", className="grid-row-label"),
                            *grid_buttons,
                        ],
                        id="color-grid-row",
                        className="color-buttons grid-row",
                        style={"display": "none"},
                    ),
                ],
            ),
            dcc.Store(id="selected-color-mode", data=NEUTRAL_MODE),
            dcc.Store(id="selected-grid", data=DEFAULT_GRID),
            dcc.Store(id="selected-disconnection-mode", data=DEFAULT_DISCONNECTION_MAP_MODE),
            dcc.Store(id="selected-page-tab", data=TAB_EMBEDDING),
            html.P(
                "No run chosen: the Run selector is at ---. Choose a run to see the charts and panels.",
                id="no-run-message",
                className="page-subtitle",
                style={"display": "none"},
            ),
            # Everything that describes the chosen run; hidden while Run is "---" (_toggle_run_content).
            html.Div(
                id="run-content",
                children=[
                # The three views of a run (embedding, clustering, dendrogram): one is shown at a time (_apply_page_tab),
                # the tabs a run has not got are hidden. Each tab holds the panels that belong together; the panels keep
                # their own visibility callbacks, which only say whether the run has them at all.
                tab_bar(),
                html.Div(
                    id="tab-embedding",
                    className="tab-content",
                    children=[
                        html.H2("Embedding Visualization", id="embedding-section", className="section-heading"),
                        html.Div(_NEUTRAL_DESCRIPTION, id="color-description", className="color-description"),
                        html.Div(id="graph-area", className="graph-wrap"),
                        # Always-visible (per design decision, 01-09-26 - not an appear-on-click popup):
                        # placeholder until a point is clicked, subject's nilearn viewer afterward.
                        lesion_panel(),
                        # Hidden by default (style toggled by _update_disconnectome_panel_visibility below) -
                        # only a modality="sdc" run (its subjects have a disconnectome-map.nii.gz on disk,
                        # see SDC_DISCONNECTOME_GLOB) ever shows this panel; a "lesion" run has no such file,
                        # showing it there would be either empty or a crash on every single click (01-09-26 -
                        # 29-09-26 SDC extension, on request: "come per le lesioni ... plottare anche la
                        # frequency map con la disconnessione").
                        disconnectome_panel(),
                        # Hidden by default (style toggled by _update_pca_panel below): only a pca dim_reduction run has
                        # components. 16-10-26, on request: the brain maps of the components, as in section 6 of
                        # notebooks/pipeline_building/thiebaut_2020_replication.ipynb.
                        pca_map_panel(),
                    ],
                ),
                html.Div(
                    id="tab-clustering",
                    className="tab-content",
                    style={"display": "none"},
                    children=[
                        # Hidden by default (style toggled by _update_cluster_picker below) - only a
                        # 30-09-26, on request: everything below is per-CLUSTER, everything above is
                        # per-subject/whole-run. The break is marked with a heavier rule and its own
                        # title, and the cluster chooser is lifted out of the first panel it happened to
                        # live in (cluster-map-panel) to sit here, centred, as the section's first act -
                        # it scopes every panel that follows, so it belongs to the section, not to one of
                        # its panels. Callbacks still resolve it by component id, so nothing else moves.
                        html.Div(
                            id="clustering-section",
                            className="section-divider",
                            style={"display": "none"},
                            children=[
                                html.H2("Clustering Explorer", className="section-title"),
                                html.P(
                                    "The sections below describe one cluster at a time. Choose which one, or “all” to see them all together.",
                                    className="section-intro",
                                ),
                                html.Div(
                                    className="cluster-chooser",
                                    children=[
                                        html.Label("Cluster", className="picker-label"),
                                        dcc.Dropdown(id="cluster-picker", clearable=False),
                                    ],
                                ),
                            ],
                        ),
                        # clustering.py run (metadata has cluster_label) ever shows this panel.
                        overlap_map_panel(),
                        # Hidden by default (style toggled by _update_disconnection_map_panel_visibility
                        # below) - needs BOTH a modality="sdc" run (a disconnectome file to average) AND a
                        # clustering.py run (a cluster_label to group by), unlike disconnectome-panel above
                        # which only needs the former. Reuses cluster-picker itself (no separate "Cluster"
                        # dropdown here) - the same clustering run has exactly one set of clusters regardless
                        # of which map family (lesion overlap vs disconnection mean) is being viewed, so a
                        # second dropdown would only ever show the identical options as the first.
                        disconnection_map_panel(),
                        # Hidden by default (style toggled by _update_cluster_picker below, same condition
                        # as cluster-map-panel/disconnection-map-panel - run.pipeline == "clustering") -
                        # 29-09-26, on request: shown *after* the two per-cluster map panels above (moved
                        # there the same day, from its first position above them), driven by the *same*
                        # "Cluster" dropdown they already share (cluster-picker itself is defined inside
                        # cluster-map-panel above - Dash resolves callbacks by component id regardless of
                        # where in the tree that id physically lives).
                        representative_panel(),
                        # Hidden by default (style toggled by _update_cluster_picker below, same condition
                        # as cluster-map-panel - run.pipeline == "clustering") - 29-09-26, on request: last
                        # of the per-cluster panels, driven by the same shared cluster-picker. Visible for
                        # any clustering.py run regardless of modality (age/sex/education/NIHSS/lesion
                        # volume come from the subject registry, not from a disconnectome/lesion file).
                        description_panel(),
                        # Hidden by default (style toggled by _update_cluster_picker below, same condition as
                        # the other per-cluster panels) - 07-10-26, on request: last panel of the page. Not
                        # driven by cluster-picker: it compares every cluster of the run at once.
                        composition_panel(),
                        # Hidden by default (style toggled by _update_cluster_picker, same condition as the other
                        # clustering panels) - 16-10-26, on request: the whole-run geometric indices, after the
                        # composition panel. Like it, not driven by cluster-picker.
                        quality_panel(),
                    ],
                ),
                html.Div(
                    id="tab-dendrogram",
                    className="tab-content",
                    style={"display": "none"},
                    children=[
                        # Hidden by default (style toggled by _update_dendrogram_panel below): only an agglomerative
                        # clustering run has a tree. 21-10-26, on request: a section of its own, the last of the page,
                        # like "Clustering Explorer" (section-divider, not one more .anatomy-panel): it follows the tree
                        # k by k on a tuning that reproduces this production run, chosen by the user among the compatible ones.
                        dendrogram_panel(),
                    ],
                ),
                ],
            ),
            # Last child and position: fixed, so its place in the DOM does not matter. Collapsed by default; the links are rebuilt for the chosen run by _update_page_index.
            page_index(),
        ],
    )

    @app.callback(
        Output("cluster-picker", "options"),
        Output("cluster-picker", "value"),
        Output("clustering-section", "style"),
        Output("cluster-map-panel", "style"),
        Output("representative-subject-panel", "style"),
        Output("cluster-description-panel", "style"),
        Output("cluster-composition-panel", "style"),
        Output("cluster-quality-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_cluster_picker(run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        hidden = {"display": "none"}
        if run.pipeline != "clustering":
            return [], None, hidden, hidden, hidden, hidden, hidden, hidden
        clusters = cluster_options(run_metadata(run))
        return (
            [{"label": ALL_CLUSTERS, "value": ALL_CLUSTERS}]
            + [{"label": str(cluster_label), "value": cluster_label} for cluster_label in clusters],
            clusters[0], {}, {}, {}, {}, {}, {},
        )

    register_embedding_view(app, context)

    register_tabs(app, context)

    register_pickers(app, context)

    register_anatomy(app, context)
    register_cluster_maps(app, context)

    register_description(app, context)

    register_quality(app, context)

    register_pca_maps(app, context)

    register_dendrogram(app, context)

    def _preload_stores() -> None:
        """Reads every subject of every clustering run once, in the background, into the two
        BinaryMaskStores, so that afterwards ANY cluster of ANY run is a bincount + a ~1s render
        instead of minutes of reading NIfTIs (30-09-26, a live-demo need: all masks and SDC
        must browse fast). Lesion masks for every clustering run's subjects; disconnectomes for
        the subjects of sdc-modality runs only (the one modality showing that panel). Background
        optimisation only: a failure is logged with its traceback and leaves the store as far as
        it got - a click then reads whatever is still missing itself and raises visibly in the
        panel, nothing is hidden."""
        datasets: dict[str, dict[str, str]] = {"lesion": {}, "disconnection": {}}
        for run in runs:
            if run.pipeline != "clustering":
                continue
            metadata = run_metadata(run)
            by_subject = dict(zip(metadata["subject_id"], metadata["dataset"]))
            datasets["lesion"].update(by_subject)
            if run.modality == "sdc":
                datasets["disconnection"].update(by_subject)
        for name, store, cfg_data_root, glob in (
            ("lesion", context.lesion_store, context.lesion_cfg.data_root, context.lesion_cfg.lesion_glob),
            ("disconnection", context.disconnection_store, context.sdc_cfg.data_root, context.sdc_cfg.disconnectome_glob),
        ):
            by_subject = datasets[name]
            if not by_subject:
                continue
            try:
                paths, _missing = resolve_available_lesion_paths(
                    list(by_subject), by_subject, cfg_data_root, glob, context.discovered_files
                )
                logging.info("preload %s: reading %d subject(s)", name, len(paths))
                store.preload(paths.values())
            except (ValueError, OSError):
                logging.warning("preload %s failed", name, exc_info=True)
                continue
            logging.info("preload %s: done, %d subject(s) in memory", name, len(paths))

    if preload:
        threading.Thread(target=_preload_stores, name="store-preload", daemon=True).start()

    return app
