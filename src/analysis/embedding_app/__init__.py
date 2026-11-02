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

import nibabel as nib
import numpy as np
import pandas as pd
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.anatomical_maps import (
    BinaryMaskStore,
    DiscoveredFiles,
    resolve_available_lesion_paths,
    resolve_lesion_paths,
)
from src.analysis.clustering_evaluation import AdpSummary, SilhouetteBreakdown, SoftMembership
from src.analysis.component_maps import ComponentMapStore
from src.analysis.dendrogram_splits import SplitTree
from src.analysis.embedding_app.anatomy import (
    DEFAULT_DISCONNECTION_MAP_MODE,
    DISCONNECTION_MAP_MODE_LABELS,
    DISCONNECTION_PERCENT_MODE,
    DISCONNECTION_PROBABILITY_THRESHOLD,
    _ANATOMY_VIEWER_WIDTH,
    _DISCONNECTOME_CMAP,
    _DISCONNECTOME_DISPLAY_THRESHOLD,
    _DISCONNECTOME_GLASS_BRAIN_ALPHA,
    _DISCONNECTOME_GLASS_BRAIN_THRESHOLD,
    _DISCONNECTOME_PLACEHOLDER,
    _LESION_PLACEHOLDER,
    LesionViewerConfig,
    SdcViewerConfig,
    _build_cluster_disconnection_view,
    _build_cluster_overlap_view,
    _build_subject_disconnectome_view,
    _build_subject_lesion_view,
    _resolve_subject_dataset,
    _static_glass_brain_png_bytes,
    _static_png_bytes,
    _style_nilearn_html,
    disconnection_map_content_for,
    disconnectome_viewer_content_for,
    lesion_viewer_content_for,
    overlap_map_content_for,
    representative_subject_content_for,
)
from src.analysis.embedding_app.embedding_view import (
    COLOR_MODE_ORDER,
    NEUTRAL_MODE,
    _NEUTRAL_DESCRIPTION,
    _color_button_label,
    cluster_centroids_with_nearest_subject,
    cluster_options,
    color_mode_description_children,
    graph_content_for,
)
from src.analysis.embedding_app.panels.dendrogram import (
    DENDROGRAM_MAP_MODALITIES,
    DendrogramViewBuilder,
    build_run_split_tree,
    dendrogram_k_options,
    dendrogram_steps_content_for,
    dendrogram_tuning_note,
    run_compatible_tunings,
)
from src.analysis.embedding_app.panels.description import (
    cluster_composition_content_for,
    cluster_description_content_for,
)
from src.analysis.embedding_app.panels.overview import ALL_CLUSTERS, all_clusters_content_for
from src.analysis.embedding_app.panels.pca_maps import (
    ComponentMapData,
    _build_component_map_view,
    _is_pca_run,
    component_maps_content_for,
    run_component_maps,
)
from src.analysis.embedding_app.panels.quality import (
    _QUALITY_POLL_MS,
    adp_quality_content_for,
    cluster_quality_content_for,
    run_adp_summary,
    run_silhouette_samples,
    run_soft_membership,
)
from src.analysis.embedding_app.picker import (
    PICKER_FIELDS,
    SPLIT_TAG_PARAMS,
    UNSET,
    _n_components_option_label,
    index_runs,
    open_pickers,
    resolve_pickers,
)
from src.analysis.embedding_app.runs import (
    ProductionRun,
    UndisplayableRunError,
    _matrix_shape,
    load_cluster_space,
    load_run,
    run_metadata,
    run_params,
)
from src.analysis.embedding_app.style import _INDEX_STRING
from src.analysis.embedding_app.tabs import (
    PAGE_TAB_LABELS,
    TAB_CLUSTERING,
    TAB_DENDROGRAM,
    TAB_EMBEDDING,
    _index_links,
    active_page_tab,
    index_entries_for,
    page_tabs_for,
    tab_is_active,
)
from src.analysis.embedding_coloring import DEFAULT_GRID, GRID_MODES, available_grids
from src.analysis.raw_distances import RawDistanceStore
from src.analysis.tuning_match import TuningMatch
from src.utils.participants import load_participants_registry




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
    single-subject lesion viewer added 01-09-26 (one small NIfTI, also fast enough uncached) -
    but *not* for the per-cluster overlap map (same panel-family, very different cost: measured
    ~40ms/subject to load+resample, dominating the whole panel's response time for a real
    several-hundred-subject cluster), which this app does cache in-process
    (cluster_view_cache/_cached_cluster_overlap_view below, 01-09-26 perf fix). The two SDC
    disconnectome panels added 29-09-26 (single-subject viewer, per-cluster mean-disconnection
    map) mirror this exact split - single-subject uncached, per-cluster cached
    (disconnection_view_cache/_cached_cluster_disconnection_view) - same per-subject cost shape,
    just averaging instead of counting (build_mean_map vs build_overlap_map).

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

    runs_by_key = {run.key: run for run in runs}
    # Each run's value at every filter selector, read once here and not on every click.
    indexed_runs = index_runs(runs, clustering_params_file)

    # Per-subject "voxels above threshold" memos (30-09-26), shared by every run and cluster of
    # this app instance - see BinaryMaskStore. Plain closure variables, like the view caches.
    lesion_store = BinaryMaskStore(
        lesion_cfg.reference_img, lesion_cfg.resample_interpolation, lesion_cfg.binarize_threshold,
        cache_dir=Path(cache_dir) / "binary_masks",
    )
    disconnection_store = BinaryMaskStore(
        sdc_cfg.reference_img, sdc_cfg.resample_interpolation, DISCONNECTION_PROBABILITY_THRESHOLD,
        cache_dir=Path(cache_dir) / "binary_masks",
    )

    # Cluster-overlap-map cache (01-09-26 perf fix) - process-lifetime, in-memory, scoped to
    # this one app instance (a plain closure variable, not a module-level global -
    # code_standards.md §1 "no stato globale"). Keyed by (run.key, cluster_label): switching
    # back to an already-viewed cluster (or re-viewing it via the "Salva HTML" button after
    # already looking at it) is then instant instead of re-loading+resampling every subject's
    # real NIfTI mask from disk again. A failed build (ValueError - an unresolvable subject) is
    # never cached, so a transient/fixable problem can be retried on the next click.
    # Which files each dataset holds (22-10-26): found once per app, shared by every per-cluster map and the preload.
    discovered_files = DiscoveredFiles()

    cluster_view_cache: dict[tuple[str, int, int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]] = {}

    def _cached_cluster_overlap_view(
        run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig,
        width_view: int = _ANATOMY_VIEWER_WIDTH,
    ) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
        # The width is part of the key: the same cluster is drawn big in its own panel and smaller in the overview.
        cache_key = (run.key, cluster_label, width_view)
        if cache_key not in cluster_view_cache:
            cluster_view_cache[cache_key] = _build_cluster_overlap_view(
                run, metadata, cluster_label, lesion_cfg, mask_store=lesion_store, discovered=discovered_files,
                width_view=width_view,
            )
        return cluster_view_cache[cache_key]

    # Same caching reasoning as cluster_view_cache above, for the SDC per-cluster mean
    # disconnection map (29-09-26) - a separate dict/cache_key namespace since a (run.key,
    # cluster_label) pair for a clustering run could in principle collide across the two if
    # they shared one dict (a clustering run's own key doesn't encode which of the two anatomy
    # families produced a given cache entry).
    disconnection_view_cache: dict[
        tuple[str, int, str, int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]
    ] = {}

    def _cached_cluster_disconnection_view(
        run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, sdc_cfg: SdcViewerConfig,
        map_mode: str = DEFAULT_DISCONNECTION_MAP_MODE, width_view: int = _ANATOMY_VIEWER_WIDTH,
    ) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
        # map_mode is part of the key (30-09-26): the same cluster now has two different maps,
        # and keying on (run, cluster) alone would serve whichever was built first for both. The width too (22-10-26).
        cache_key = (run.key, cluster_label, map_mode, width_view)
        if cache_key not in disconnection_view_cache:
            disconnection_view_cache[cache_key] = _build_cluster_disconnection_view(
                run, metadata, cluster_label, sdc_cfg, map_mode, mask_store=disconnection_store,
                discovered=discovered_files, width_view=width_view,
            )
        return disconnection_view_cache[cache_key]

    # Silhouette of every subject per run (16-10-26): about a second for a 5845-subject run, so computed once per
    # run and served from memory afterwards. Same closure-cache reasoning as the two view caches above;
    # a run it is not defined for raises ValueError and is never cached.
    silhouette_cache: dict[str, SilhouetteBreakdown] = {}
    # The representative subject's viewer: about a second of nilearn per (run, cluster), kept like the other views.
    representative_cache: dict[tuple[str, int], html.Div] = {}
    soft_membership_cache: dict[str, SoftMembership] = {}

    # Dendrogram panel (21-10-26). The compatible tunings of a run are looked up once per run (the runs themselves are
    # fixed at startup); the tree is the seconds-long part, kept per (run, tuning); the two anatomy views of a split
    # cost about 40 ms per subject, kept per (run, tuning, modality, cluster name). A failed build is never cached.
    compatible_tunings_cache: dict[str, list[TuningMatch]] = {}
    split_tree_cache: dict[tuple[str, str], SplitTree] = {}
    dendrogram_view_cache: dict[tuple, tuple[StatMapView, int, nib.Nifti1Image, list[str]]] = {}

    def _compatible_tunings(run: ProductionRun) -> list[TuningMatch]:
        if run.key not in compatible_tunings_cache:
            compatible_tunings_cache[run.key] = run_compatible_tunings(run)
        return compatible_tunings_cache[run.key]

    def _chosen_tuning_dir(run: ProductionRun, tuning_value: str | None) -> Path:
        """The compatible tuning picked in the panel. PreventUpdate for a value that is not one of this run's compatible
        tunings: the callbacks of the panel also fire with the value left over from the previously chosen run."""
        if tuning_value is None:
            raise PreventUpdate
        try:
            compatible = {str(match.run_dir) for match in _compatible_tunings(run) if match.compatible}
        except ValueError:
            raise PreventUpdate
        if tuning_value not in compatible:
            raise PreventUpdate
        return Path(tuning_value)

    def _cached_split_tree(run: ProductionRun, tuning_dir: Path) -> SplitTree:
        key = (run.key, str(tuning_dir))
        if key not in split_tree_cache:
            split_tree_cache[key] = build_run_split_tree(run, tuning_dir)
        return split_tree_cache[key]

    def _cached_dendrogram_view(
        run: ProductionRun, metadata_at_k: pd.DataFrame, label: int, modality: str, name: str, width: int, tuning_dir: Path
    ) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
        # Keyed by the cluster's name (the leaves it holds), not by k: a cluster that survives several splits is the
        # same subjects at each of them, and is built once per map width (the overview draws it smaller than the steps).
        key = (run.key, str(tuning_dir), modality, name, width)
        if key not in dendrogram_view_cache:
            if modality == "lesion":
                dendrogram_view_cache[key] = _build_cluster_overlap_view(
                    run, metadata_at_k, label, lesion_cfg, mask_store=lesion_store, discovered=discovered_files,
                    width_view=width,
                )
            else:
                dendrogram_view_cache[key] = _build_cluster_disconnection_view(
                    run, metadata_at_k, label, sdc_cfg, DISCONNECTION_PERCENT_MODE, mask_store=disconnection_store,
                    discovered=discovered_files, width_view=width,
                )
        return dendrogram_view_cache[key]

    def _run_embedding(run: ProductionRun) -> tuple[np.ndarray | None, str | None]:
        """(embedding, None) of a run, or (None, why it cannot be drawn): the overview of every cluster still draws the
        maps of a run whose embedding is missing, and says so."""
        try:
            embedding, _metadata = load_run(run)
        except UndisplayableRunError as exc:
            return None, str(exc)
        return embedding, None

    def _cached_soft_membership(run: ProductionRun) -> SoftMembership:
        if run.key not in soft_membership_cache:
            soft_membership_cache[run.key] = run_soft_membership(run)
        return soft_membership_cache[run.key]
    raw_distance_store = RawDistanceStore(Path(cache_dir) / "raw_distances")
    component_map_store = ComponentMapStore(Path(cache_dir) / "component_maps")
    component_map_cache: dict[str, ComponentMapData] = {}
    component_view_cache: dict[tuple[str, int], tuple[StatMapView, float]] = {}

    def _cached_component_maps(run: ProductionRun) -> ComponentMapData | None:
        # Memoised once computed (reading the entry back is cheap, not free); None (still computing) is not.
        if run.key not in component_map_cache:
            data = run_component_maps(run, component_map_store)
            if data is None:
                return None
            component_map_cache[run.key] = data
        return component_map_cache[run.key]

    def _cached_component_view(data: ComponentMapData, component: int) -> tuple[StatMapView, float]:
        # The view of a component is a second of nilearn; keyed by the maps' identity through the run key it came from.
        key = next(run_key for run_key, cached in component_map_cache.items() if cached is data), component
        if key not in component_view_cache:
            component_view_cache[key] = _build_component_map_view(data, component)
        return component_view_cache[key]
    adp_summary_cache: dict[str, AdpSummary] = {}

    def _cached_adp_summary(run: ProductionRun) -> AdpSummary | None:
        # Seconds once the distance matrix exists, so memoised per run; None (still computing) is not.
        if run.key not in adp_summary_cache:
            summary = run_adp_summary(run, raw_distance_store)
            if summary is None:
                return None
            adp_summary_cache[run.key] = summary
        return adp_summary_cache[run.key]

    def _cached_silhouette(run: ProductionRun) -> SilhouetteBreakdown:
        if run.key not in silhouette_cache:
            silhouette_cache[run.key] = run_silhouette_samples(run)
        return silhouette_cache[run.key]

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
                html.Div(
                    id="page-tab-bar",
                    className="tab-bar",
                    children=[
                        html.Button(
                            label, id={"type": "page-tab-btn", "tab": name}, n_clicks=0,
                            className="tab-btn active" if name == TAB_EMBEDDING else "tab-btn",
                        )
                        for name, label in PAGE_TAB_LABELS.items()
                    ],
                ),
                html.Div(
                    id="tab-embedding",
                    className="tab-content",
                    children=[
                        html.H2("Embedding Visualization", id="embedding-section", className="section-heading"),
                        html.Div(_NEUTRAL_DESCRIPTION, id="color-description", className="color-description"),
                        html.Div(id="graph-area", className="graph-wrap"),
                        # Always-visible (per design decision, 01-09-26 - not an appear-on-click popup):
                        # placeholder until a point is clicked, subject's nilearn viewer afterward.
                        html.Div(
                            id="lesion-panel",
                            className="anatomy-panel",
                            children=[
                                html.H2("Lesion anatomy", className="section-heading"),
                                html.Div(id="lesion-viewer-content", children=_LESION_PLACEHOLDER),
                                # Single source of truth for "which subject is actually visible in the panel
                                # above right now" (01-09-26 bug fix) - set atomically with
                                # lesion-viewer-content.children by the same callback below, never derived
                                # separately from embedding-graph.clickData again downstream. clickData is a
                                # client-side prop that does NOT reset just because a *different* dcc.Graph
                                # instance with the same id gets mounted in its place (switching run-picker
                                # replaces graph-area's children, but React/Dash patches the same-id node
                                # rather than remounting it) - the Save buttons below used to read clickData
                                # directly via State, so after a run change they kept silently offering a
                                # download for the *previous* run's clicked subject even though this panel
                                # had already reset to the placeholder, with no visible link between what was
                                # shown and what got downloaded. None whenever the panel shows the placeholder
                                # or an unresolvable-subject error, so a stale/absent selection can never be
                                # downloaded regardless of what embedding-graph.clickData still holds.
                                dcc.Store(id="lesion-viewer-subject", data=None),
                                html.Div(
                                    className="save-btn-row",
                                    children=[
                                        html.Button("Save HTML", id="lesion-save-btn", n_clicks=0, className="save-btn"),
                                        html.Button("Save PNG", id="lesion-png-btn", n_clicks=0, className="save-btn"),
                                        html.Button(
                                            "Save PNG (glass brain)", id="lesion-glass-png-btn", n_clicks=0, className="save-btn"
                                        ),
                                    ],
                                ),
                                dcc.Download(id="lesion-download"),
                                dcc.Download(id="lesion-png-download"),
                                dcc.Download(id="lesion-glass-png-download"),
                            ],
                        ),
                        # Hidden by default (style toggled by _update_disconnectome_panel_visibility below) -
                        # only a modality="sdc" run (its subjects have a disconnectome-map.nii.gz on disk,
                        # see SDC_DISCONNECTOME_GLOB) ever shows this panel; a "lesion" run has no such file,
                        # showing it there would be either empty or a crash on every single click (01-09-26 -
                        # 29-09-26 SDC extension, on request: "come per le lesioni ... plottare anche la
                        # frequency map con la disconnessione").
                        html.Div(
                            id="disconnectome-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Disconnection (SDC)", className="section-heading"),
                                html.Div(id="disconnectome-viewer-content", children=_DISCONNECTOME_PLACEHOLDER),
                                # Same clickData-persistence fix as lesion-viewer-subject above, same reasoning.
                                dcc.Store(id="disconnectome-viewer-subject", data=None),
                                html.Div(
                                    className="save-btn-row",
                                    children=[
                                        html.Button("Save HTML", id="disconnectome-save-btn", n_clicks=0, className="save-btn"),
                                        html.Button("Save PNG", id="disconnectome-png-btn", n_clicks=0, className="save-btn"),
                                        html.Button(
                                            "Save PNG (glass brain)", id="disconnectome-glass-png-btn", n_clicks=0,
                                            className="save-btn",
                                        ),
                                    ],
                                ),
                                dcc.Download(id="disconnectome-download"),
                                dcc.Download(id="disconnectome-png-download"),
                                dcc.Download(id="disconnectome-glass-png-download"),
                            ],
                        ),
                        # Hidden by default (style toggled by _update_pca_panel below): only a pca dim_reduction run has
                        # components. 16-10-26, on request: the brain maps of the components, as in section 6 of
                        # notebooks/pipeline_building/thiebaut_2020_replication.ipynb.
                        html.Div(
                            id="pca-map-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Component maps", className="section-heading"),
                                html.Div(
                                    className="cluster-chooser",
                                    children=[
                                        html.Label("Component", className="picker-label"),
                                        dcc.Dropdown(id="pca-component-picker", clearable=False),
                                    ],
                                ),
                                html.Div(id="pca-map-content"),
                                # Enabled only while the maps are being computed in the background.
                                dcc.Interval(id="pca-map-poll", interval=_QUALITY_POLL_MS, disabled=True),
                            ],
                        ),
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
                        html.Div(
                            id="cluster-map-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Overlap map per cluster", className="section-heading"),
                                html.Div(id="cluster-map-content"),
                                html.Div(
                                    className="save-btn-row",
                                    children=[
                                        html.Button("Save HTML", id="cluster-save-btn", n_clicks=0, className="save-btn"),
                                        html.Button("Save PNG", id="cluster-png-btn", n_clicks=0, className="save-btn"),
                                    ],
                                ),
                                dcc.Download(id="cluster-download"),
                                dcc.Download(id="cluster-png-download"),
                            ],
                        ),
                        # Hidden by default (style toggled by _update_disconnection_map_panel_visibility
                        # below) - needs BOTH a modality="sdc" run (a disconnectome file to average) AND a
                        # clustering.py run (a cluster_label to group by), unlike disconnectome-panel above
                        # which only needs the former. Reuses cluster-picker itself (no separate "Cluster"
                        # dropdown here) - the same clustering run has exactly one set of clusters regardless
                        # of which map family (lesion overlap vs disconnection mean) is being viewed, so a
                        # second dropdown would only ever show the identical options as the first.
                        html.Div(
                            id="disconnection-map-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Disconnection per cluster", className="section-heading"),
                                # 30-09-26: two readings of the same subjects, explicitly chosen rather
                                # than one silently assumed - see DISCONNECTION_PERCENT_MODE's comment.
                                html.Div(
                                    [
                                        html.Span("Map", className="grid-row-label"),
                                        *[
                                            html.Button(
                                                DISCONNECTION_MAP_MODE_LABELS[mode],
                                                id={"type": "disconnection-mode-btn", "mode": mode},
                                                n_clicks=0,
                                                className="active" if mode == DEFAULT_DISCONNECTION_MAP_MODE else "",
                                            )
                                            for mode in DISCONNECTION_MAP_MODE_LABELS
                                        ],
                                    ],
                                    className="color-buttons grid-row",
                                ),
                                html.Div(id="disconnection-map-content"),
                                html.Div(
                                    className="save-btn-row",
                                    children=[
                                        html.Button("Save HTML", id="disconnection-save-btn", n_clicks=0, className="save-btn"),
                                        html.Button("Save PNG", id="disconnection-png-btn", n_clicks=0, className="save-btn"),
                                    ],
                                ),
                                dcc.Download(id="disconnection-download"),
                                dcc.Download(id="disconnection-png-download"),
                            ],
                        ),
                        # Hidden by default (style toggled by _update_cluster_picker below, same condition
                        # as cluster-map-panel/disconnection-map-panel - run.pipeline == "clustering") -
                        # 29-09-26, on request: shown *after* the two per-cluster map panels above (moved
                        # there the same day, from its first position above them), driven by the *same*
                        # "Cluster" dropdown they already share (cluster-picker itself is defined inside
                        # cluster-map-panel above - Dash resolves callbacks by component id regardless of
                        # where in the tree that id physically lives).
                        html.Div(
                            id="representative-subject-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Representative subject of the cluster", className="section-heading"),
                                html.Div(id="representative-subject-content"),
                                html.Div(
                                    className="save-btn-row",
                                    children=[
                                        html.Button("Save HTML", id="representative-save-btn", n_clicks=0, className="save-btn"),
                                        html.Button("Save PNG", id="representative-png-btn", n_clicks=0, className="save-btn"),
                                    ],
                                ),
                                dcc.Download(id="representative-download"),
                                dcc.Download(id="representative-png-download"),
                            ],
                        ),
                        # Hidden by default (style toggled by _update_cluster_picker below, same condition
                        # as cluster-map-panel - run.pipeline == "clustering") - 29-09-26, on request: last
                        # of the per-cluster panels, driven by the same shared cluster-picker. Visible for
                        # any clustering.py run regardless of modality (age/sex/education/NIHSS/lesion
                        # volume come from the subject registry, not from a disconnectome/lesion file).
                        html.Div(
                            id="cluster-description-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Cluster description", className="section-heading"),
                                html.Div(id="cluster-description-content"),
                            ],
                        ),
                        # Hidden by default (style toggled by _update_cluster_picker below, same condition as
                        # the other per-cluster panels) - 07-10-26, on request: last panel of the page. Not
                        # driven by cluster-picker: it compares every cluster of the run at once.
                        html.Div(
                            id="cluster-composition-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Cluster composition", className="section-heading"),
                                html.Div(id="cluster-composition-content"),
                            ],
                        ),
                        # Hidden by default (style toggled by _update_cluster_picker, same condition as the other
                        # clustering panels) - 16-10-26, on request: the whole-run geometric indices, after the
                        # composition panel. Like it, not driven by cluster-picker.
                        html.Div(
                            id="cluster-quality-panel",
                            className="anatomy-panel",
                            style={"display": "none"},
                            children=[
                                html.H2("Clustering evaluation", className="section-heading"),
                                html.Div(id="cluster-quality-content"),
                                # Enabled only while an adp run's distance matrix is being computed in the background.
                                dcc.Interval(id="cluster-quality-poll", interval=_QUALITY_POLL_MS, disabled=True),
                            ],
                        ),
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
                        html.Div(
                            id="dendrogram-panel",
                            className="section-divider",
                            style={"display": "none"},
                            children=[
                                html.H2("Dendrogram Explorer", className="section-title"),
                                html.P(
                                    "Going from k-1 to k clusters, one cluster splits in two. Choose a k: the tree is walked from the "
                                    "smallest k up to that k. Each step shows the tree and the embedding, the anatomy of the cluster "
                                    "that splits and of the two it gives, and a table describing them. The labels for each k come from "
                                    "a tuning compatible with this run.",
                                    className="section-intro",
                                ),
                                html.Div(
                                    className="cluster-chooser cluster-chooser-wide",
                                    children=[
                                        html.Label("Compatible tuning", className="picker-label"),
                                        dcc.Dropdown(id="dendrogram-tuning-picker", clearable=False),
                                    ],
                                ),
                                html.Div(id="dendrogram-tuning-note"),
                                html.Div(
                                    className="cluster-chooser",
                                    children=[
                                        html.Label("k", className="picker-label"),
                                        dcc.Dropdown(id="dendrogram-k-picker", clearable=False),
                                    ],
                                ),
                                html.Div(
                                    className="cluster-chooser",
                                    children=[
                                        html.Label("Map", className="picker-label"),
                                        dcc.Dropdown(
                                            id="dendrogram-map-picker", clearable=False, value="lesion",
                                            options=[{"label": label, "value": value} for value, label in DENDROGRAM_MAP_MODALITIES.items()],
                                        ),
                                    ],
                                ),
                                html.H2("Agglomerative decomposed", className="dendrogram-steps-title"),
                                dcc.Loading(html.Div(id="dendrogram-steps-content")),
                            ],
                        ),
                    ],
                ),
                ],
            ),
            # Last child and position: fixed, so its place in the DOM does not matter. Collapsed by default; the links are rebuilt for the chosen run by _update_page_index.
            html.Details(
                id="page-index",
                className="page-index",
                children=[
                    html.Summary("Index"),
                    html.Nav(id="page-index-links", children=_index_links(index_entries_for(None, TAB_EMBEDDING))),
                ],
            ),
        ],
    )

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
        return active_page_tab(runs_by_key[run_key], current)

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
        run = runs_by_key[run_key]
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

    @app.callback(Output("reduction-picker-field", "style"), Input("pipeline-picker", "value"))
    def _toggle_reduction_picker(pipeline: str | None):
        if pipeline is None:
            raise PreventUpdate
        return {"display": "none"} if pipeline == "dim_reduction" else {}

    @app.callback(
        Output("tag-params-label", "children"),
        Output("tag-params-rest-field", "style"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
    )
    def _update_tag_params_selectors(pipeline: str | None, method: str | None):
        if pipeline is None or method is None:
            raise PreventUpdate
        split = method in SPLIT_TAG_PARAMS
        shown = pipeline != "dim_reduction" and (split or method == UNSET)
        return ("k" if method == "agglomerative" else "Parameters"), ({} if shown else {"display": "none"})

    # One callback for every selector (see resolve_pickers): the 10 values (and the "Riavvia" button) come in, the
    # 10 option lists and 10 values go out. The nine before "Run" are optional filters ("---" = not a filter); "Run" lists the runs
    # that match the filters that are set. The selectors are both inputs and outputs of this callback; Dash
    # does not re-trigger a callback from its own outputs.
    picker_ids = {field: f"{field.replace('_', '-')}-picker" for field in PICKER_FIELDS}

    @app.callback(
        [Output(picker_ids[field], prop) for field in PICKER_FIELDS for prop in ("options", "value")],
        [*(Input(picker_ids[field], "value") for field in PICKER_FIELDS), Input("reset-pickers-btn", "n_clicks")],
    )
    def _update_pickers(*values):
        *picker_values, _reset_clicks = values
        current = dict(zip(PICKER_FIELDS, picker_values))
        changed = next((field for field in PICKER_FIELDS if picker_ids[field] == ctx.triggered_id), None)
        if ctx.triggered_id == "reset-pickers-btn":
            state = open_pickers(indexed_runs)
        else:
            state = resolve_pickers(indexed_runs, current, changed)

        def label(field: str, value) -> str:
            if value == UNSET:
                return UNSET
            if field == "run":
                return state.run_labels[value]
            return _n_components_option_label(value) if field == "n_components" else str(value)

        outputs = []
        for field in PICKER_FIELDS:
            outputs += [[{"label": label(field, value), "value": value} for value in state.options[field]], state.chosen[field]]
        return outputs

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
        return graph_content_for(runs_by_key[run_key], selected_mode, grid)

    @app.callback(
        Output("lesion-viewer-content", "children"),
        Output("lesion-viewer-subject", "data"),
        Input("embedding-graph", "clickData"),
        Input("run-picker", "value"),
    )
    def _update_lesion_viewer(click_data: dict | None, run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        # A run change resets to the placeholder (ctx.triggered_id tells the two Inputs apart) -
        # a subject clicked on a previous run must not linger once the picker moves on. The
        # Store resets to None in lockstep, so the Save buttons below (reading it, not
        # embedding-graph.clickData directly) can never offer a stale cross-run download - see
        # the Store's own docstring in app.layout for the clickData-persistence bug this fixes.
        if ctx.triggered_id == "run-picker" or click_data is None:
            return _LESION_PLACEHOLDER, None
        subject_id = click_data["points"][0].get("text")
        if subject_id is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        return lesion_viewer_content_for(run, subject_id, run_metadata(run), lesion_cfg), subject_id

    @app.callback(
        Output("lesion-download", "data"),
        Input("lesion-save-btn", "n_clicks"),
        State("lesion-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_lesion_html(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            view, _dataset = _build_subject_lesion_view(run, subject_id, run_metadata(run), lesion_cfg)
        except ValueError:
            # The visible panel already reports this via lesion_viewer_content_for - the save
            # button simply has nothing to offer, not a second error surface.
            raise PreventUpdate
        return dcc.send_string(_style_nilearn_html(view.html), filename=f"{subject_id}_lesion_3d.html")

    @app.callback(
        Output("lesion-png-download", "data"),
        Input("lesion-png-btn", "n_clicks"),
        State("lesion-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_lesion_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            # Resolves the subject's real lesion mask path directly - no need to build the
            # interactive view_img (_build_subject_lesion_view) just to render a static PNG.
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob)
        except ValueError:
            # Same never-raises-into-the-callback contract as _download_lesion_html: the visible
            # panel already reports this, the save button simply has nothing to offer.
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            str(lesion_paths[subject_id]), threshold=lesion_cfg.binarize_threshold, cmap="autumn", colorbar=False,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_lesion.png")

    @app.callback(
        Output("lesion-glass-png-download", "data"),
        Input("lesion-glass-png-btn", "n_clicks"),
        State("lesion-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_lesion_glass_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob)
        except ValueError:
            # Same never-raises-into-the-callback contract as _download_lesion_png.
            raise PreventUpdate
        # cmap="autumn" - same choice as _build_subject_lesion_view's own ortho view (see its
        # docstring): a binary mask has no gradient to show, autumn's solid bright yellow reads
        # clearly on both the ortho and this glass-brain projection.
        png_bytes = _static_glass_brain_png_bytes(
            str(lesion_paths[subject_id]), threshold=lesion_cfg.binarize_threshold, cmap="autumn", colorbar=False,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_lesion_glass.png")

    @app.callback(
        Output("disconnectome-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_disconnectome_panel_visibility(run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        return {} if runs_by_key[run_key].modality == "sdc" else {"display": "none"}

    @app.callback(
        Output("disconnectome-viewer-content", "children"),
        Output("disconnectome-viewer-subject", "data"),
        Input("embedding-graph", "clickData"),
        Input("run-picker", "value"),
    )
    def _update_disconnectome_viewer(click_data: dict | None, run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        # Same run-change reset as _update_lesion_viewer, plus a modality gate: a "lesion" run's
        # subjects don't have a disconnectome-map.nii.gz to resolve at all (this panel stays
        # hidden for them via _update_disconnectome_panel_visibility, but its own content must
        # still reset rather than linger/attempt a doomed resolution on every click).
        if run.modality != "sdc" or ctx.triggered_id == "run-picker" or click_data is None:
            return _DISCONNECTOME_PLACEHOLDER, None
        subject_id = click_data["points"][0].get("text")
        if subject_id is None:
            raise PreventUpdate
        return disconnectome_viewer_content_for(run, subject_id, run_metadata(run), sdc_cfg), subject_id

    @app.callback(
        Output("disconnectome-download", "data"),
        Input("disconnectome-save-btn", "n_clicks"),
        State("disconnectome-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnectome_html(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            view, _dataset = _build_subject_disconnectome_view(run, subject_id, run_metadata(run), sdc_cfg)
        except ValueError:
            raise PreventUpdate
        return dcc.send_string(_style_nilearn_html(view.html), filename=f"{subject_id}_disconnectome.html")

    @app.callback(
        Output("disconnectome-png-download", "data"),
        Input("disconnectome-png-btn", "n_clicks"),
        State("disconnectome-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnectome_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            disconnectome_paths = resolve_lesion_paths(
                [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
            )
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            str(disconnectome_paths[subject_id]), threshold=_DISCONNECTOME_DISPLAY_THRESHOLD,
            cmap=_DISCONNECTOME_CMAP, colorbar=True,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_disconnectome.png")

    @app.callback(
        Output("disconnectome-glass-png-download", "data"),
        Input("disconnectome-glass-png-btn", "n_clicks"),
        State("disconnectome-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnectome_glass_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            disconnectome_paths = resolve_lesion_paths(
                [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
            )
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_glass_brain_png_bytes(
            str(disconnectome_paths[subject_id]), threshold=_DISCONNECTOME_GLASS_BRAIN_THRESHOLD, cmap="magma",
            colorbar=True, alpha=_DISCONNECTOME_GLASS_BRAIN_ALPHA,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_disconnectome_glass.png")

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
        run = runs_by_key[run_key]
        hidden = {"display": "none"}
        if run.pipeline != "clustering":
            return [], None, hidden, hidden, hidden, hidden, hidden, hidden
        clusters = cluster_options(run_metadata(run))
        return (
            [{"label": ALL_CLUSTERS, "value": ALL_CLUSTERS}]
            + [{"label": str(cluster_label), "value": cluster_label} for cluster_label in clusters],
            clusters[0], {}, {}, {}, {}, {}, {},
        )

    @app.callback(
        Output("cluster-map-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_cluster_map(run_key: str | None, cluster_label: int | str | None, selected_tab: str | None):
        if run_key in (None, UNSET) or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        if cluster_label == ALL_CLUSTERS:
            embedding, embedding_message = _run_embedding(run)
            return all_clusters_content_for(
                run, run_metadata(run), embedding, embedding_message, "lesion", DEFAULT_DISCONNECTION_MAP_MODE,
                lambda run_, metadata, label, width: _cached_cluster_overlap_view(run_, metadata, label, lesion_cfg, width_view=width),
            )
        return overlap_map_content_for(run, run_metadata(run), cluster_label, lesion_cfg, build_view=_cached_cluster_overlap_view)

    @app.callback(
        Output("representative-subject-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_representative_subject(run_key: str | None, cluster_label: int | str | None, selected_tab: str | None):
        if run_key in (None, UNSET) or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        if cluster_label == ALL_CLUSTERS:
            return html.P("Choose a cluster to see its representative subject.", className="status-message")
        try:
            embedding, metadata = load_run(run)
        except UndisplayableRunError as exc:
            # Same never-raises-into-the-callback contract as every other *_content_for
            # panel - the main graph above already shows this same error for this run.
            return html.P(str(exc), className="status-message")
        key = (run.key, cluster_label)
        if key not in representative_cache:
            content = representative_subject_content_for(run, embedding, metadata, cluster_label, lesion_cfg, sdc_cfg)
            if not isinstance(content, html.P):  # a status message (a missing file...) is not remembered: it may be fixed
                representative_cache[key] = content
            return content
        return representative_cache[key]

    @app.callback(
        Output("cluster-description-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_cluster_description(run_key: str | None, cluster_label: int | str | None, selected_tab: str | None):
        if run_key in (None, UNSET) or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
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
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        return cluster_composition_content_for(run_metadata(run))

    @app.callback(
        Output("cluster-quality-content", "children"),
        Output("cluster-quality-poll", "disabled"),
        Input("run-picker", "value"),
        Input("cluster-quality-poll", "n_intervals"),
        Input("selected-page-tab", "data"),
    )
    def _update_cluster_quality(run_key: str | None, _n_intervals: int, selected_tab: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return [], True  # nothing shown, so nothing to poll for (reopening the tab restarts it)
        if run.method == "adp":
            content, pending = adp_quality_content_for(run, summary_of=_cached_adp_summary)
            return content, not pending
        return cluster_quality_content_for(run, silhouette_of=_cached_silhouette, soft_of=_cached_soft_membership), True

    def _is_agglomerative(run: ProductionRun) -> bool:
        return run.pipeline == "clustering" and run.method == "agglomerative"

    @app.callback(
        Output("dendrogram-panel", "style"),
        Output("dendrogram-tuning-picker", "options"),
        Output("dendrogram-tuning-picker", "value"),
        Output("dendrogram-tuning-note", "children"),
        Output("dendrogram-map-picker", "value"),
        Input("run-picker", "value"),
    )
    def _update_dendrogram_panel(run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        if not _is_agglomerative(run):
            return {"display": "none"}, [], None, [], no_update
        default_map = "lesion"
        try:
            matches = _compatible_tunings(run)
        except ValueError as exc:
            return {}, [], None, html.P(str(exc), className="status-message"), default_map
        options = [{"label": match.run_dir.name, "value": str(match.run_dir)} for match in matches if match.compatible]
        return {}, options, (options[0]["value"] if options else None), dendrogram_tuning_note(matches), default_map

    @app.callback(
        Output("dendrogram-k-picker", "options"),
        Output("dendrogram-k-picker", "value"),
        Input("run-picker", "value"),
        Input("dendrogram-tuning-picker", "value"),
    )
    def _update_dendrogram_k(run_key: str | None, tuning_value: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        if not _is_agglomerative(run):
            raise PreventUpdate
        tuning_dir = _chosen_tuning_dir(run, tuning_value)
        try:
            tree = _cached_split_tree(run, tuning_dir)
        except ValueError:
            return [], None  # the figure callback shows why
        k_values = dendrogram_k_options(tree)
        production_k = run_params(run)["n_clusters"]
        # The production k, or the nearest one the tuning swept (a sweep can have holes: 2..6, 8, 10).
        return [{"label": str(k), "value": k} for k in k_values], min(k_values, key=lambda k: abs(k - production_k))

    def _dendrogram_context(run_key: str | None, tuning_value: str | None, k: int | None, modality: str | None):
        """(run, tuning dir, tree) the two callbacks below work on, or a status message in their place when the tree
        cannot be built. PreventUpdate while the pickers still hold values of the previously chosen run."""
        if run_key in (None, UNSET) or k is None or modality is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if not _is_agglomerative(run):
            raise PreventUpdate
        tuning_dir = _chosen_tuning_dir(run, tuning_value)
        try:
            tree = _cached_split_tree(run, tuning_dir)
        except ValueError as exc:
            return html.P(str(exc), className="status-message")
        if k not in dendrogram_k_options(tree):
            raise PreventUpdate  # the k left over from the previous tuning, until the k picker is refilled
        return run, tuning_dir, tree

    def _dendrogram_build_view(tuning_dir: Path) -> DendrogramViewBuilder:
        return lambda run_, metadata_at_k, label, modality_, name, width: _cached_dendrogram_view(
            run_, metadata_at_k, label, modality_, name, width, tuning_dir
        )

    @app.callback(
        Output("dendrogram-steps-content", "children"),
        Input("run-picker", "value"),
        Input("dendrogram-tuning-picker", "value"),
        Input("dendrogram-k-picker", "value"),
        Input("dendrogram-map-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_dendrogram_steps(
        run_key: str | None, tuning_value: str | None, k: int | None, modality: str | None, selected_tab: str | None
    ):
        if run_key not in (None, UNSET) and not tab_is_active(runs_by_key[run_key], selected_tab, TAB_DENDROGRAM):
            return []
        context = _dendrogram_context(run_key, tuning_value, k, modality)
        if isinstance(context, html.P):
            return context
        run, tuning_dir, tree = context
        embedding, embedding_message = _run_embedding(run)
        if embedding is None:
            return html.P(embedding_message, className="status-message")
        return dendrogram_steps_content_for(
            run, run_metadata(run), tree, embedding, k, modality, _dendrogram_build_view(tuning_dir),
            load_participants_registry().set_index("subject_id"),
        )

    @app.callback(
        Output("pca-map-panel", "style"),
        Output("pca-component-picker", "options"),
        Output("pca-component-picker", "value"),
        Input("run-picker", "value"),
    )
    def _update_pca_panel(run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        if not _is_pca_run(run):
            return {"display": "none"}, [], None
        n_components = _matrix_shape(run)[1]
        return {}, [{"label": f"Component {k}", "value": k} for k in range(1, n_components + 1)], 1

    @app.callback(
        Output("pca-map-content", "children"),
        Output("pca-map-poll", "disabled"),
        Input("run-picker", "value"),
        Input("pca-component-picker", "value"),
        Input("pca-map-poll", "n_intervals"),
    )
    def _update_pca_maps(run_key: str | None, component: int | None, _n_intervals: int):
        if run_key in (None, UNSET) or component is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if not _is_pca_run(run):
            raise PreventUpdate
        content, pending = component_maps_content_for(run, component, _cached_component_maps, _cached_component_view)
        return content, not pending

    @app.callback(
        Output("representative-download", "data"),
        Input("representative-save-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_representative_html(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key in (None, UNSET) or cluster_label is None or cluster_label == ALL_CLUSTERS:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            embedding, metadata = load_run(run)
            centroids = cluster_centroids_with_nearest_subject(embedding, metadata, load_cluster_space(run))
            subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
            if run.modality == "lesion":
                view, _dataset = _build_subject_lesion_view(run, subject_id, metadata, lesion_cfg)
            else:
                view, _dataset = _build_subject_disconnectome_view(run, subject_id, metadata, sdc_cfg)
        except (ValueError, KeyError):
            # Same never-raises-into-the-callback contract as _download_lesion_html: the
            # visible panel already reports this, the save button simply has nothing to offer.
            # ValueError also covers UndisplayableRunError (its own subclass) from load_run.
            raise PreventUpdate
        return dcc.send_string(
            _style_nilearn_html(view.html), filename=f"cluster_{cluster_label}_representative_{subject_id}.html"
        )

    @app.callback(
        Output("representative-png-download", "data"),
        Input("representative-png-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_representative_png(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key in (None, UNSET) or cluster_label is None or cluster_label == ALL_CLUSTERS:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            embedding, metadata = load_run(run)
            centroids = cluster_centroids_with_nearest_subject(embedding, metadata, load_cluster_space(run))
            subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
            dataset = _resolve_subject_dataset(metadata, subject_id)
            if run.modality == "lesion":
                lesion_paths = resolve_lesion_paths(
                    [subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob
                )
                png_bytes = _static_png_bytes(
                    str(lesion_paths[subject_id]), threshold=lesion_cfg.binarize_threshold, cmap="autumn",
                    colorbar=False,
                )
            else:
                disconnectome_paths = resolve_lesion_paths(
                    [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
                )
                png_bytes = _static_png_bytes(
                    str(disconnectome_paths[subject_id]), threshold=_DISCONNECTOME_DISPLAY_THRESHOLD,
                    cmap=_DISCONNECTOME_CMAP, colorbar=True,
                )
        except (ValueError, KeyError):
            raise PreventUpdate
        return dcc.send_bytes(png_bytes, filename=f"cluster_{cluster_label}_representative_{subject_id}.png")

    @app.callback(
        Output("cluster-download", "data"),
        Input("cluster-save-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_cluster_html(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key in (None, UNSET) or cluster_label is None or cluster_label == ALL_CLUSTERS:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            view, _n_subjects, _percentage_img, _missing = _cached_cluster_overlap_view(run, run_metadata(run), cluster_label, lesion_cfg)
        except ValueError:
            raise PreventUpdate
        return dcc.send_string(_style_nilearn_html(view.html), filename=f"cluster_{cluster_label}_overlap_map.html")

    @app.callback(
        Output("cluster-png-download", "data"),
        Input("cluster-png-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_cluster_png(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key in (None, UNSET) or cluster_label is None or cluster_label == ALL_CLUSTERS:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            # Reuses the same process-lifetime cache the HTML download/panel display already
            # populate - percentage_img is the exact image the interactive view itself renders,
            # not a second build_overlap_map pass (see _build_cluster_overlap_view's docstring).
            _view, _n_subjects, percentage_img, _missing = _cached_cluster_overlap_view(run, run_metadata(run), cluster_label, lesion_cfg)
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_png_bytes(percentage_img, threshold=1e-6, cmap="hot", colorbar=True)
        return dcc.send_bytes(png_bytes, filename=f"cluster_{cluster_label}_overlap_map.png")

    @app.callback(
        Output("disconnection-map-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_disconnection_map_panel_visibility(run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = runs_by_key[run_key]
        return {} if (run.modality == "sdc" and run.pipeline == "clustering") else {"display": "none"}

    @app.callback(
        Output("disconnection-map-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-disconnection-mode", "data"),
        Input("selected-page-tab", "data"),
    )
    def _update_disconnection_map(run_key: str | None, cluster_label: int | str | None, map_mode: str, selected_tab: str | None):
        if run_key in (None, UNSET) or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        if cluster_label == ALL_CLUSTERS:
            embedding, embedding_message = _run_embedding(run)
            return all_clusters_content_for(
                run, run_metadata(run), embedding, embedding_message, "sdc", map_mode,
                lambda run_, metadata, label, width: _cached_cluster_disconnection_view(
                    run_, metadata, label, sdc_cfg, map_mode, width_view=width
                ),
            )
        return disconnection_map_content_for(
            run, run_metadata(run), cluster_label, sdc_cfg,
            build_view=_cached_cluster_disconnection_view, map_mode=map_mode,
        )

    @app.callback(
        Output("selected-disconnection-mode", "data"),
        Input({"type": "disconnection-mode-btn", "mode": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _select_disconnection_mode(_all_n_clicks: list[int]) -> str:
        if ctx.triggered_id is None:
            raise PreventUpdate
        return ctx.triggered_id["mode"]

    @app.callback(
        Output({"type": "disconnection-mode-btn", "mode": ALL}, "className"),
        Input("selected-disconnection-mode", "data"),
        State({"type": "disconnection-mode-btn", "mode": ALL}, "id"),
    )
    def _highlight_active_disconnection_mode(selected: str, ids: list[dict]) -> list[str]:
        return ["active" if button_id["mode"] == selected else "" for button_id in ids]

    @app.callback(
        Output("disconnection-download", "data"),
        Input("disconnection-save-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnection_html(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key in (None, UNSET) or cluster_label is None or cluster_label == ALL_CLUSTERS:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        try:
            view, _n_subjects, _mean_img, _missing = _cached_cluster_disconnection_view(run, run_metadata(run), cluster_label, sdc_cfg)
        except ValueError:
            raise PreventUpdate
        return dcc.send_string(
            _style_nilearn_html(view.html), filename=f"cluster_{cluster_label}_disconnection_mean_map.html"
        )

    @app.callback(
        Output("disconnection-png-download", "data"),
        Input("disconnection-png-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnection_png(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key in (None, UNSET) or cluster_label is None or cluster_label == ALL_CLUSTERS:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        try:
            # Reuses the same process-lifetime cache the HTML download/panel display already
            # populate - mean_img is the exact image the interactive view itself renders, not a
            # second build_mean_map pass (see _build_cluster_disconnection_view's docstring).
            _view, _n_subjects, mean_img, _missing = _cached_cluster_disconnection_view(run, run_metadata(run), cluster_label, sdc_cfg)
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            mean_img, threshold=_DISCONNECTOME_DISPLAY_THRESHOLD, cmap=_DISCONNECTOME_CMAP, colorbar=True,
        )
        return dcc.send_bytes(png_bytes, filename=f"cluster_{cluster_label}_disconnection_mean_map.png")

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
        run = runs_by_key[run_key]
        return _index_links(index_entries_for(run, active_page_tab(run, selected_tab)))

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
            ("lesion", lesion_store, lesion_cfg.data_root, lesion_cfg.lesion_glob),
            ("disconnection", disconnection_store, sdc_cfg.data_root, sdc_cfg.disconnectome_glob),
        ):
            by_subject = datasets[name]
            if not by_subject:
                continue
            try:
                paths, _missing = resolve_available_lesion_paths(
                    list(by_subject), by_subject, cfg_data_root, glob, discovered_files
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
