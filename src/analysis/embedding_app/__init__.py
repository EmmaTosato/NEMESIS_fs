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

import io
import json
import logging
import re
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from nilearn import plotting as nilearn_plotting
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.anatomical_maps import (
    BinaryMaskStore,
    DiscoveredFiles,
    build_mean_map,
    build_overlap_map,
    resolve_available_lesion_paths,
    resolve_lesion_paths,
)
from src.analysis.cluster_comparison import (
    AGREEMENT_LEVELS,
    AGREEMENT_SCALE,
    AlignedRuns,
    ContingencyTables,
    agreement_level,
    agreement_metrics,
    align_runs,
    build_table_heatmap,
    chi_square_independence,
    cluster_name,
    contingency_tables,
    purity_table,
)
from src.analysis.cluster_composition import COMPOSITION_VARIABLES, build_composition_figure, composition_frame
from src.analysis.cluster_quality import build_dbcv_figure, build_mean_membership_figure, build_silhouette_figure
from src.analysis.component_map_plots import build_reproducibility_figure
from src.analysis.component_maps import ComponentMapSet, ComponentMapStore, MapGeometry, load_map_geometry, to_volume
from src.analysis.clustering_evaluation import (
    AdpSummary,
    SilhouetteBreakdown,
    SoftMembership,
    adp_summary,
    per_cluster_silhouette,
    require_applicable,
    run_metric,
    soft_membership_summary,
)
from src.analysis.production_results import RESULTS_METHODS, SavedResults, read_production_results
from src.analysis.raw_distances import RawDistanceStore
from src.analysis.cluster_description import (
    CLUSTER_DESCRIPTION_VARIABLES,
    ClusterDescriptionVariable,
    ClusterStats,
    build_cluster_description_figure,
    cluster_composition,
    clusters_comparison_stats,
    group_stats,
)
from src.analysis.cluster_pair import (
    PairComparison,
    PairFrame,
    build_odds_ratio_figure,
    centroid_separation,
    difference_image,
    pair_clinical_comparison,
    pair_frame,
    pair_regression,
    regression_term_label,
)
from src.analysis.clustering_tuning_analysis import load_clustering_tuning_run
from src.analysis.cluster_overview import build_overview_embedding_figure, overview_grid_plan
from src.analysis.dendrogram_splits import (
    SplitTree,
    build_split_tree,
    build_step_embedding_figure,
    build_tree_figure,
    replay_splits,
    saved_labels_for,
    single_label,
)
from src.analysis.embedding_app.picker import (
    PICKER_FIELDS,
    SPLIT_TAG_PARAMS,
    UNSET,
    _load_tag_params_or_none,
    _n_components_option_label,
    _run_tag_param_label,
    index_runs,
    open_pickers,
    resolve_pickers,
)
from src.analysis.embedding_app.runs import (
    ProductionRun,
    UndisplayableRunError,
    _matrix_shape,
    _run_chronological_key,
    load_cluster_space,
    load_run,
    run_metadata,
    run_params,
    run_reduction_axis,
    view_note_for,
)
from src.analysis.embedding_app.style import _FONT_STACK, _GRID_BORDER, _INDEX_STRING, _TEXT_COLOR
from src.analysis.embedding_coloring import COLOR_MODES
from src.analysis.embedding_coloring import (
    DEFAULT_GRID,
    GRID_MODES,
    available_grids,
    grid_column,
)
from src.analysis.embedding_coloring import color_values as read_color_values
from src.analysis.params import load_tag_params
from src.analysis.plotting import (
    _NOISE_COLOR,
    _ordered_categories,
    _palette_for_categories,
    _palette_for_labels,
    compose_embedding_plot_title,
)
from src.analysis.tuning_match import TuningMatch, find_compatible_tunings
from src.utils.artifacts import (
    MANIFEST_FILENAME,
    MATRIX_FILENAME,
    METADATA_FILENAME,
    load_matrix,
    read_run_config,
    read_run_params,
)
from src.utils.number_format import PLOTLY_SEPARATORS, format_number, format_scientific
from src.utils.participants import load_participants_registry

_CLUSTER_LABEL_COLUMN = COLOR_MODES["cluster_label"].column

# "neutro" first, same convention as embedding_coloring.COLOR_MODES/the notebook prototype -
# the neutral single-color view is always available and always the default, every other
# entry is a registered color_by mode name.
NEUTRAL_MODE = "neutral"
_NEUTRAL_DESCRIPTION = (
    "No coloring: every point is a patient, all the same color. "
    "Use it to read the shape of the embedding without any other information."
)
COLOR_MODE_ORDER: tuple[str, ...] = (NEUTRAL_MODE, *COLOR_MODES.keys())


@dataclass(frozen=True)
class LesionViewerConfig:
    """Everything src.analysis.anatomical_maps needs to resolve/build a lesion anatomy map,
    bundled so callbacks don't carry 5 loose params (same reasoning as ProductionRun itself).
    Built once at startup by src.pipeline.embedding_app from build_lesion_matrix.json (via
    src.analysis.build_config.load_build_matrix_config) - the same config/loader
    build_lesion_matrix.py itself uses, never re-parsed by hand here.
    """

    data_root: Path
    lesion_glob: str
    reference_img: nib.Nifti1Image
    binarize_threshold: float
    resample_interpolation: str


# Same fixed pattern as src.features.sdc.build_sdc_voxelwise_matrix's own
# f"bcbtoolkit/*/*_res-1_desc-{object_}.nii.gz" with object_="disconnectome" - this app only ever wants
# the disconnectome map itself (never "lesion", SDC's own other known object, see
# src.features.sdc.KNOWN_OBJECTS - that one is already covered by the lesion viewer above,
# reading straight from manual_masks/ instead of bcbtoolkit/), so the pattern is inlined as a plain
# constant here rather than threading an unused object_ parameter through SdcViewerConfig.
SDC_DISCONNECTOME_GLOB = "bcbtoolkit/*/*_res-1_desc-disconnectome.nii.gz"


@dataclass(frozen=True)
class SdcViewerConfig:
    """Everything the SDC disconnectome anatomy panels need - same bundling reasoning as
    LesionViewerConfig. Built once at startup by src.pipeline.embedding_app from
    build_sdc_matrix.json's own voxelwise fields (via
    src.analysis.build_config.load_build_sdc_matrix_config) - the same config/loader
    build_sdc_matrix.py itself uses for its 'voxelwise' representation, never re-parsed by hand
    here. Its own reference_img/resample_interpolation are loaded separately from
    LesionViewerConfig's (never reused across the two - build_sdc_matrix.json's own
    reference_template_path is a different grid, res-1, from build_lesion_matrix.json's res-2,
    confirmed by reading both configs rather than assumed identical).

    No binarize_threshold, unlike LesionViewerConfig: disconnectome values are a continuous
    [0, 1] probability, never binarized (see src.features.sdc's own module docstring) - both
    anatomy panels below use a near-zero display threshold instead (same reasoning as the lesion
    cluster-overlap map's own 1e-6, see overlap_map_content_for).
    """

    data_root: Path
    disconnectome_glob: str
    reference_img: nib.Nifti1Image
    resample_interpolation: str


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


# nilearn.plotting.view_img's own default (600px) reads narrow inside this page's 1100px-wide
# .page container, next to the 34px anatomy-panel headings (01-09-26 feedback) - both anatomy
# viewers pass this explicitly instead. Height scales with it automatically (nilearn's own
# _json_view_size keeps the sagittal/coronal/axial aspect ratio, never distorted by width_view).
_ANATOMY_VIEWER_WIDTH = 900

# Display cmap/threshold shared by every ortho/interactive SDC disconnectome view (single-subject
# viewer, per-cluster mean map, and their own static-PNG downloads - never the glass-brain
# download, which has its own separate threshold/alpha below). cmap="magma" - briefly changed to
# "nipy_spectral" on 29-09-26 (to match Thiebaut de Schotten et al. 2020's own Fig. 1 colormap),
# reverted the same day ("non mi piace la palette arcobaleno") in favor of a sequential,
# single-hue-family colormap - plasma/viridis were also compared on real data
# (tmp/anatomy_rendering/130_cluster_disconnection_*, 131_disconnectome_single_*) before settling
# back on magma, already used elsewhere in this app (glass-brain download below, cluster overlap's
# sibling "hot"). threshold=0.02 (was the near-zero epsilon 1e-6, kept across both colormap
# choices) - at 1e-6, near-zero disconnection-probability noise renders in the colormap's own
# near-black floor color, scattered as ugly black speckle across the brain on both the
# single-subject map and, worse, the per-cluster mean map ("troppo nero" feedback, 29-09-26) -
# confirmed clean at 0.02 against a real 975-subject cluster mean and a real single-subject map
# (tmp/anatomy_rendering/110_cluster_disconnection_*, 120_disconnectome_single_*). Distinct
# problem from the glass-brain streaking below (that one is specific to projecting/summing along
# the full volume depth), but the same fix shape - raise the near-zero epsilon to a real floor.
_DISCONNECTOME_CMAP = "magma"
_DISCONNECTOME_DISPLAY_THRESHOLD = 0.02


def _masked_for_view_colorbar(img: nib.Nifti1Image, threshold: float) -> nib.Nifti1Image:
    """A copy of img with every voxel inside [-threshold, threshold] zeroed - lets a view_img
    call receive a near-zero epsilon (1e-6, this app's usual "any non-zero voxel" convention)
    instead of a real, wide threshold like _DISCONNECTOME_DISPLAY_THRESHOLD.

    view_img's own interactive colorbar paints every value inside [-threshold, threshold] flat
    opaque gray (nilearn.plotting._engine_utils.threshold_cmap, hardcoded gray (0.5, 0.5, 0.5,
    1.0), not configurable through view_img's public API) - invisible for a near-zero epsilon
    (a sliver against vmax) but a visibly wide gray band at the low end of the scale for a real
    threshold like 0.02 (30-09-26 feedback: "perché c'è del grigio nella scala"). Zeroing the
    data ourselves the same way nilearn's own thresholding would (html_stat_map._threshold_data:
    values inside [-threshold, threshold] become 0) and passing 1e-6 to view_img instead hides
    the exact same voxels without the artifact. Callers keep passing the real, unmasked image to
    every other consumer (PNG download, cached return value) - this masked copy exists only for
    what view_img itself renders."""
    data = img.get_fdata()
    masked = np.where(np.abs(data) > threshold, data, 0.0).astype(data.dtype)
    return nib.Nifti1Image(masked, img.affine)

# --- Per-cluster disconnection map: two readings of the same subjects (30-09-26) ------------
# The mean map and the lesion overlap map are the SAME estimator (voxelwise mean over the
# cluster) on different data, but that makes them mean different things: averaging BINARY
# masks yields a fraction of subjects, averaging CONTINUOUS probabilities does not. A mean of
# 0.6 could be "every subject at 0.6" or "60% at 1.0 and 40% at 0.0" - indistinguishable - so
# it cannot be read as "60% of the cluster is disconnected here", which is exactly what the
# lesion overlap map does say. "percent" restores that reading by binarizing each subject
# first and then counting, making the two maps identical by construction.
DISCONNECTION_PERCENT_MODE = "percent"
DISCONNECTION_MEAN_MODE = "mean"
DEFAULT_DISCONNECTION_MAP_MODE = DISCONNECTION_PERCENT_MODE
DISCONNECTION_MAP_MODE_LABELS = {
    DISCONNECTION_PERCENT_MODE: "% of subjects disconnected",
    DISCONNECTION_MEAN_MODE: "mean probability",
}
# The per-subject probability a voxel must EXCEED for that subject to count as disconnected
# there (build_overlap_map binarizes with a strict >, same as for a lesion mask).
# 0.5 is "more likely disconnected than not" - the same more-likely-than-not cutoff the
# lesion-mask literature uses to binarize a smoothed probabilistic mask (e.g. Keator et al.
# 2021, knowledge/papers/stroke_related/). Declared here as ONE named constant rather than exposed
# as a slider: a threshold the reader can sweep invites fishing for the value that makes a
# cluster look separable, which is not what this panel is for. Changing it is a deliberate,
# reviewable edit - and it must be stated wherever the map is shown, since the map's meaning
# depends on it entirely.
DISCONNECTION_PROBABILITY_THRESHOLD = 0.5

# Display-only threshold/alpha for the SDC glass-brain static download (29-09-26, on request) -
# deliberately not the same threshold the SDC ortho/interactive views use above (see
# _static_glass_brain_png_bytes' own docstring for why a glass-brain projection needs its own,
# higher threshold). Picked by comparing 1e-6/0.05/0.1/0.2 against real subject data
# (tmp/anatomy_rendering/90_disconnectome_glass_lyrz_magma_alpha90_thr*.png) and confirmed by the
# user - 0.1 hides the near-zero noise streaks without cutting into the real signal.
_DISCONNECTOME_GLASS_BRAIN_THRESHOLD = 0.1
_DISCONNECTOME_GLASS_BRAIN_ALPHA = 0.9


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


def _resolve_subject_dataset(metadata: pd.DataFrame, subject_id: str) -> str:
    matches = metadata.loc[metadata["subject_id"] == subject_id, "dataset"]
    if matches.empty:
        raise ValueError(f"{subject_id!r} not found in this run's metadata")
    return matches.iloc[0]


def _style_nilearn_html(html_page: str) -> str:
    """nilearn's view_img HTML has no <style> block at all (verified against a real generated
    page, 01-09-26) - the only ordinary, CSS-reachable text it has (the "Opacity" label/slider)
    renders in the browser's plain default font instead of this app's own (feedback: "Opacity
    deve rispettare lo stesso font"). Injected once, right before </head> (present exactly once
    in every nilearn-generated page), reused for both the embedded iframe and the "Salva HTML"
    download - both should look the same."""
    style_block = f"<style>body {{ font-family: {_FONT_STACK}; color: {_TEXT_COLOR}; font-size: 14px; }}</style>"
    return html_page.replace("</head>", f"{style_block}\n</head>", 1)


def _static_glass_brain_png_bytes(
    stat_map_img: str | nib.Nifti1Image, *, threshold: float, cmap: str, colorbar: bool, alpha: float = 1.0
) -> bytes:
    """Glass-brain counterpart to _static_png_bytes' plot_stat_map rendering (29-09-26, on
    request) - a single transparent-brain projection (nilearn.plotting.plot_glass_brain,
    display_mode="lyrz") instead of 3 flat ortho slices, for each anatomy panel's own "Salva PNG
    (glass brain)" button. black_bg=False/plot_abs=False mirror _static_png_bytes' own
    white-background, non-negative-data choices.

    Unlike plot_stat_map, plot_glass_brain projects (sums) along the full depth of the volume -
    a near-zero display threshold (e.g. the 1e-6 epsilon _build_subject_disconnectome_view uses
    to show "any real disconnection probability") makes faint background noise visible as thin
    dark streaks across the whole silhouette, confirmed on real disconnectome data (tmp/
    anatomy_rendering/, 29-09-26). Each caller passes a threshold picked for its own data -
    _DISCONNECTOME_GLASS_BRAIN_THRESHOLD for the SDC panels, lesion_cfg.binarize_threshold for
    the lesion panel (already clean at that threshold - a binary mask has no near-zero noise to
    hide) - never a shared default that would silently reintroduce the streaking for one caller
    while being wrong for the other."""
    display = nilearn_plotting.plot_glass_brain(
        stat_map_img, threshold=threshold, cmap=cmap, colorbar=colorbar, black_bg=False,
        display_mode="lyrz", plot_abs=False, alpha=alpha,
    )
    buffer = io.BytesIO()
    display.savefig(buffer, dpi=150)
    display.close()
    buffer.seek(0)
    return buffer.getvalue()


def _static_png_bytes(stat_map_img: str | nib.Nifti1Image, *, threshold: float, cmap: str, colorbar: bool) -> bytes:
    """Non-interactive PNG counterpart to the "Salva HTML" download (11-09-26, on request) -
    view_img's own HTML page has no static-image export, so this renders the same stat_map_img
    a second time via nilearn.plotting.plot_stat_map instead, matching the interactive view's own
    bg_img/threshold/cmap/colorbar choices (see _build_subject_lesion_view/
    _build_cluster_overlap_view) rather than an independently-styled second rendering.
    symmetric_cbar=False mirrors view_img's own symmetric_cmap=False: both maps this app ever
    passes here are non-negative (a binary lesion mask, or a 0-100% overlap percentage), so
    nilearn's "auto" guess is unnecessary to rely on. No bg_img passed - unlike view_img,
    plot_stat_map's own `bg_img` default already *is* an MNI152 template object, not a string
    shortcut (view_img's own "MNI152" string raises `ValueError: File not found` if passed here,
    confirmed against the installed nilearn version rather than assumed). Matplotlib's Agg
    backend is already active process-wide by the time this runs (src.analysis.plotting, imported
    by this module, sets it at import time) - no figure ever reaches a GUI backend."""
    display = nilearn_plotting.plot_stat_map(
        stat_map_img, black_bg=False, threshold=threshold, cmap=cmap, colorbar=colorbar, title=None,
        symmetric_cbar=False,
    )
    buffer = io.BytesIO()
    display.savefig(buffer, dpi=150)
    display.close()
    buffer.seek(0)
    return buffer.getvalue()


def _anatomy_viewer(
    view: StatMapView, heading: str, caption: str, warning: str | None = None, note: str | None = None
) -> html.Div:
    """Shared layout for both anatomy panels: a heading + a one-line color-legend caption, both
    ordinary HTML we render ourselves (never nilearn's own `title`/colorbar text - see
    _build_subject_lesion_view's docstring for why), above the iframe sized to the view's own
    exact pixel dimensions (view.width/height) and centered, instead of stretching a fixed-height
    iframe to the panel's full width and leaving the rest as dead space (01-09-26 feedback: the
    scatter's own .graph-wrap already established this "centered, content-sized" pattern).

    warning (29-09-26, on request): an optional extra line, rendered between the caption and the
    iframe, for a cluster-level map built from fewer subjects than the cluster actually has (see
    overlap_map_content_for/disconnection_map_content_for) - omitted (no 3rd `<p>` at all, not an
    empty one) when every requested subject resolved, so a panel with nothing to report keeps
    exactly its original 2-paragraph shape.

    key=heading on the Iframe (01-09-26 bug fix - "se cambio il cluster non mi si cambia la
    mappa"): a browser doesn't reliably re-navigate an <iframe> just because its own `srcDoc`
    attribute value changed in place - React/Dash's default diffing patches the attribute on the
    *same* DOM node, which several browsers then leave showing their stale, already-rendered
    content. `key` forces Dash's front-end to unmount+remount the node instead of patching it in
    place whenever `heading` changes - and `heading` (a subject_id or "Cluster N (n=...)") is
    already guaranteed to change whenever the actual content does, so no separate id is needed.
    """
    # note (30-09-26): a second, quieter line inside the same paragraph - for the part of a
    # caption that explains WHY the map is built this way rather than what the colour means.
    # One paragraph, not two, so the two lines stay visually bound to each other.
    # Kept a plain string when there is no note, so a panel that never had one (both
    # single-subject viewers, the lesion overlap map) keeps exactly its previous shape.
    caption_children = caption if note is None else [caption, html.Span(note, className="anatomy-note")]
    children = [
        html.H3(heading, className="anatomy-subject-title"),
        html.P(caption_children, className="anatomy-caption"),
    ]
    if warning is not None:
        children.append(_warning_box(warning))
    children.append(
        html.Div(
            html.Iframe(
                key=heading, srcDoc=_style_nilearn_html(view.html),
                style={"width": f"{view.width}px", "height": f"{view.height}px"},
            ),
            className="anatomy-viewer-wrap",
        )
    )
    return html.Div(children)


def _build_subject_lesion_view(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, lesion_cfg: LesionViewerConfig
) -> tuple[StatMapView, str]:
    """Returns (view, dataset) - dataset is needed by the caller to build its own subject-name
    heading, since title=None below (nilearn draws `title` straight onto its <canvas>, with no
    width check or line-wrapping at all - a moderately long subject_id silently overflows past
    the panel edge with no way to fix it via CSS; see _anatomy_viewer). colorbar=False: this is
    a binary lesion mask (voxel is lesioned or not) - a 0/1 colorbar conveys no real gradient
    information, unlike the cluster overlap map below.

    Raises ValueError (never silently) if subject_id/dataset/lesion file can't be resolved -
    see resolve_lesion_paths. threshold reuses lesion_cfg.binarize_threshold rather than a
    second hardcoded 0.5, so the viewer shows exactly the same binarization the source feature
    matrix used, not an independently-chosen display threshold.

    cmap="autumn" (briefly changed to "magma" on 29-09-26, reverted same day - magma's top color
    for a binary mask is a near-white pale yellow, "troppo pallido" against the white background
    on real data; autumn's is a solid bright yellow, confirmed against several alternatives -
    hot/inferno/plasma equally or more washed out, Reds/YlOrRd a legible but duller dark red -
    tmp/anatomy_rendering/100_lesion_ortho_*.png). See _download_lesion_png for the matching
    static-PNG cmap and _download_lesion_glass_png for the glass-brain download's own (same)
    "autumn" choice."""
    dataset = _resolve_subject_dataset(metadata, subject_id)
    lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob)
    view = nilearn_plotting.view_img(
        str(lesion_paths[subject_id]), bg_img="MNI152", black_bg=False, threshold=lesion_cfg.binarize_threshold,
        cmap="autumn", symmetric_cmap=False, title=None, colorbar=False, width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, dataset


def lesion_viewer_content_for(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, lesion_cfg: LesionViewerConfig
) -> html.Div | html.P:
    """graph_content_for's own never-raises contract, extended to this panel: an html.P status
    message on any resolution failure (subject not in this run, dataset unresolvable, lesion
    file missing on disk) instead of crashing the click callback - a single bad subject must
    not take down the whole app (lesson #21's isolation principle, applied per-click here)."""
    try:
        view, dataset = _build_subject_lesion_view(run, subject_id, metadata, lesion_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(view, f"{subject_id} ({dataset})", "Colored area = Lesion")


def _build_cluster_overlap_view(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig,
    mask_store: BinaryMaskStore | None = None, discovered: DiscoveredFiles | None = None,
    width_view: int = _ANATOMY_VIEWER_WIDTH,
) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
    """Returns (view, n_subjects, percentage_img, missing_subjects) - n_subjects is needed by
    the caller to build its own heading (title=None here, same reasoning as
    _build_subject_lesion_view); percentage_img (the same image the view itself renders) is
    returned alongside it (11-09-26) so the "Salva PNG" download can reuse it rather than paying
    build_overlap_map's per-subject load+resample cost a second time. colorbar stays on (unlike
    the subject viewer): the overlap percentage is a genuinely continuous, informative value.

    missing_subjects (29-09-26, on request) lists cluster members whose lesion mask isn't
    resolvable on disk right now (resolve_available_lesion_paths) - excluded from the map
    instead of failing the whole panel over them (a real, already-documented local data gap,
    e.g. after a lesion-mask swap left some subjects' raw files no longer retrieved on this
    machine - .claude/history/data_changelog.md 23-09-26). n_subjects counts only the resolved
    subjects actually used - the same denominator build_overlap_map's percentage is computed
    against, never the cluster's full nominal size.

    Raises ValueError if cluster_label has no subjects in this run's metadata, or if EVERY one
    of them is unresolvable (see resolve_available_lesion_paths/build_overlap_map) - a map with
    zero subjects behind it is not a legitimate partial result. threshold is a near-zero epsilon
    (not lesion_cfg.binarize_threshold, which binarizes each individual subject's mask before
    counting - see build_overlap_map) so every voxel with any real overlap (>0%) is shown, not
    just voxels above some display-only cutoff."""
    column = COLOR_MODES["cluster_label"].column
    cluster_metadata = metadata.loc[metadata[column] == cluster_label]
    if cluster_metadata.empty:
        raise ValueError(f"no subjects with {column}={cluster_label!r} in this run's metadata")
    dataset_by_subject = dict(zip(cluster_metadata["subject_id"], cluster_metadata["dataset"]))
    lesion_paths, missing_subjects = resolve_available_lesion_paths(
        list(dataset_by_subject), dataset_by_subject, lesion_cfg.data_root, lesion_cfg.lesion_glob, discovered
    )
    _count_img, percentage_img = build_overlap_map(
        lesion_paths, lesion_cfg.reference_img, lesion_cfg.binarize_threshold, lesion_cfg.resample_interpolation,
        store=mask_store,
    )
    view = nilearn_plotting.view_img(
        percentage_img, bg_img="MNI152", black_bg=False, threshold=1e-6, cmap="hot", symmetric_cmap=False, title=None,
        width_view=width_view,
    )
    return view, len(lesion_paths), percentage_img, missing_subjects


def _warning_box(message: str, detail: str | None = None) -> html.Div:
    """The shared boxed callout for every "partial result" warning on the page (29-09-26
    feedback: "warning tipo questo devono essere renderizzati un po' meglio").

    An uppercase vivid label carries the alarm; the message itself stays BLACK body text. That
    split is deliberate: coloring the whole block would make the information read as decoration
    and cost it contrast, while the label alone is enough to say "this is not routine caption
    text" - which is exactly how the previous thin amber line failed.

    detail: the long, non-prose tail (a list of subject ids), set apart from the sentence so the
    sentence stays readable when the tail runs to a dozen ids."""
    children: list = [html.Span("Warning", className="warning-label"), message]
    if detail is not None:
        children.append(html.Span(detail, className="warning-detail"))
    return html.Div(children, className="anatomy-warning")


def _missing_subjects_warning(missing_subjects: list[str]) -> str | None:
    """Shared warning text for overlap_map_content_for/disconnection_map_content_for (29-09-26)
    - None (no warning line at all, see _anatomy_viewer's own `warning` param) when every
    requested subject resolved."""
    if not missing_subjects:
        return None
    return (
        f"{len(missing_subjects)} cluster subjects left out of the map (data not found on disk): "
        f"{', '.join(sorted(missing_subjects))}"
    )


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


def _map_texts(modality: str, map_mode: str = DISCONNECTION_PERCENT_MODE) -> tuple[str, str | None]:
    """(caption, note) of a cluster map: what its colour means, and for a disconnection map why it is built that way.
    One wording for the panel of a cluster, the overview of every cluster and the walk down the tree, so the maps read
    the same wherever they appear. Raises ValueError for an unknown modality or map mode."""
    if modality == "lesion":
        return "Color = % of subjects in the cluster with a lesion in that voxel (0-100%)", None
    if modality != "sdc":
        raise ValueError(f"unknown map modality {modality!r} - known: ['lesion', 'sdc']")
    if map_mode == DISCONNECTION_PERCENT_MODE:
        return (
            "Color = % of subjects in the cluster disconnected in that voxel (0-100%).",
            None,
        )
    if map_mode == DISCONNECTION_MEAN_MODE:
        return (
            "Color = mean disconnection probability of the cluster in that voxel (0-1).",
            "The mean tells how strong the disconnection is.",
        )
    raise ValueError(f"unknown disconnection map mode {map_mode!r} - known: {sorted(DISCONNECTION_MAP_MODE_LABELS)}")


def overlap_map_content_for(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig,
    build_view: Callable[
        [ProductionRun, pd.DataFrame, int, LesionViewerConfig], tuple[StatMapView, int, nib.Nifti1Image, list[str]]
    ] = _build_cluster_overlap_view,
) -> html.Div | html.P:
    """Same never-raises contract as lesion_viewer_content_for - a cluster with zero resolvable
    subjects shows a status message in the panel, not a crashed callback. A cluster with *some*
    (not all) unresolvable subjects instead renders the map over its available subjects, with an
    extra warning line naming which ones were excluded (_missing_subjects_warning) - never a
    silent partial result.

    build_view defaults to the always-fresh _build_cluster_overlap_view (what every test calls
    this with) - build_app passes its own cached wrapper instead (01-09-26 perf fix: measured
    ~40ms/subject, dominating the whole panel's response time for a real several-hundred-subject
    cluster - see anatomical_maps.build_overlap_map's own docstring), so switching back to an
    already-viewed cluster in the running app is instant, without this function itself needing
    to know anything about caching."""
    try:
        view, n_subjects, _percentage_img, missing_subjects = build_view(run, metadata, cluster_label, lesion_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(
        view, f"Cluster {cluster_label} (n={n_subjects})",
        "Color = % of subjects in the cluster with a lesion in that voxel (0-100%)",
        warning=_missing_subjects_warning(missing_subjects),
    )


def _build_subject_disconnectome_view(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, sdc_cfg: SdcViewerConfig
) -> tuple[StatMapView, str]:
    """Returns (view, dataset) - same reasoning as _build_subject_lesion_view (single-source
    title, resolved via resolve_lesion_paths against sdc_cfg's own disconnectome_glob rather
    than lesion_cfg's lesion_glob). colorbar=True (unlike the lesion viewer): disconnectome
    values are a genuinely continuous [0, 1] probability per voxel, not a binary mask - a
    colorbar conveys real information here. Masks with _DISCONNECTOME_DISPLAY_THRESHOLD before
    viewing, not a binarize threshold (disconnectome values are never binarized, see
    src.features.sdc's module docstring) - see that constant's own docstring for why it isn't a
    near-zero epsilon, and _masked_for_view_colorbar's for why view_img itself gets 1e-6 instead.

    Raises ValueError (never silently) if subject_id/dataset/disconnectome file can't be
    resolved - see resolve_lesion_paths."""
    dataset = _resolve_subject_dataset(metadata, subject_id)
    disconnectome_paths = resolve_lesion_paths(
        [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
    )
    disconnectome_img = nib.load(str(disconnectome_paths[subject_id]))
    view = nilearn_plotting.view_img(
        _masked_for_view_colorbar(disconnectome_img, _DISCONNECTOME_DISPLAY_THRESHOLD), bg_img="MNI152",
        black_bg=False, threshold=1e-6, cmap=_DISCONNECTOME_CMAP, symmetric_cmap=False,
        title=None, colorbar=True, width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, dataset


def disconnectome_viewer_content_for(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, sdc_cfg: SdcViewerConfig
) -> html.Div | html.P:
    """lesion_viewer_content_for's own never-raises contract, for the SDC disconnectome panel -
    an html.P status message on any resolution failure instead of crashing the click callback."""
    try:
        view, dataset = _build_subject_disconnectome_view(run, subject_id, metadata, sdc_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(view, f"{subject_id} ({dataset})", "Color = disconnection probability per voxel (0-1)")


def _build_cluster_disconnection_view(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, sdc_cfg: SdcViewerConfig,
    map_mode: str = DEFAULT_DISCONNECTION_MAP_MODE, mask_store: BinaryMaskStore | None = None,
    discovered: DiscoveredFiles | None = None, width_view: int = _ANATOMY_VIEWER_WIDTH,
) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
    """Returns (view, n_subjects, mean_img, missing_subjects) - same reasoning as
    _build_cluster_overlap_view (including missing_subjects - see its own docstring), but the
    continuous-data counterpart: build_mean_map's voxelwise mean instead of build_overlap_map's
    binarized count/percentage (there is no "binarize each subject then count" step for a value
    that's already a continuous probability, see build_mean_map's own docstring). mean_img is
    returned alongside the view (same reasoning as percentage_img above) so the "Salva PNG"
    download can reuse it rather than paying build_mean_map's per-subject load+resample cost a
    second time.

    map_mode (30-09-26, on request):

    - "percent" (default) binarizes each subject's disconnectome at
      DISCONNECTION_PROBABILITY_THRESHOLD and counts, via the SAME build_overlap_map the lesion
      panel uses - so the two maps become the same quantity, "% of the cluster's subjects
      affected in this voxel", and are directly comparable. Displayed with the same near-zero
      display threshold as the lesion overlap map, for the same reason.
    - "mean" is the previous behaviour, build_mean_map's voxelwise mean of the continuous
      probabilities. It uses the full information instead of discarding it at a cutoff, so it
      still sees widespread sub-threshold disconnection that "percent" shows as empty - but it
      is NOT a proportion of subjects (see the constants above).

    Raises ValueError for an unknown map_mode, if cluster_label has no subjects in this run's
    metadata, or if EVERY one of them is unresolvable (see resolve_available_lesion_paths)."""
    if map_mode not in DISCONNECTION_MAP_MODE_LABELS:
        raise ValueError(
            f"unknown disconnection map mode {map_mode!r} - known: {sorted(DISCONNECTION_MAP_MODE_LABELS)}"
        )
    column = COLOR_MODES["cluster_label"].column
    cluster_metadata = metadata.loc[metadata[column] == cluster_label]
    if cluster_metadata.empty:
        raise ValueError(f"no subjects with {column}={cluster_label!r} in this run's metadata")
    dataset_by_subject = dict(zip(cluster_metadata["subject_id"], cluster_metadata["dataset"]))
    disconnectome_paths, missing_subjects = resolve_available_lesion_paths(
        list(dataset_by_subject), dataset_by_subject, sdc_cfg.data_root, sdc_cfg.disconnectome_glob, discovered
    )
    if map_mode == DISCONNECTION_PERCENT_MODE:
        _count_img, img = build_overlap_map(
            disconnectome_paths, sdc_cfg.reference_img,
            DISCONNECTION_PROBABILITY_THRESHOLD, sdc_cfg.resample_interpolation, store=mask_store,
        )
        display_threshold = 1e-6  # any non-zero voxel, exactly as the lesion overlap map
        view_source = img
    else:
        img = build_mean_map(disconnectome_paths, sdc_cfg.reference_img, sdc_cfg.resample_interpolation)
        # threshold=1e-6 below, not _DISCONNECTOME_DISPLAY_THRESHOLD directly - see
        # _masked_for_view_colorbar's own docstring (avoids view_img's gray sub-threshold band).
        view_source = _masked_for_view_colorbar(img, _DISCONNECTOME_DISPLAY_THRESHOLD)
        display_threshold = 1e-6
    # The colormap stays magma in both modes: it encodes WHICH DATA this is (disconnection,
    # not lesion), a cue the app uses everywhere, while the scale is what now matches the
    # lesion map in "percent".
    view = nilearn_plotting.view_img(
        view_source, bg_img="MNI152", black_bg=False, threshold=display_threshold,
        cmap=_DISCONNECTOME_CMAP, symmetric_cmap=False, title=None, width_view=width_view,
    )
    return view, len(disconnectome_paths), img, missing_subjects


def disconnection_map_content_for(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, sdc_cfg: SdcViewerConfig,
    build_view: Callable[
        ..., tuple[StatMapView, int, nib.Nifti1Image, list[str]]
    ] = _build_cluster_disconnection_view,
    map_mode: str = DEFAULT_DISCONNECTION_MAP_MODE,
) -> html.Div | html.P:
    """Same never-raises contract as overlap_map_content_for (including the same skip-and-warn
    behavior for a cluster with *some* unresolvable subjects, _missing_subjects_warning) - a
    cluster with zero resolvable subjects shows a status message in the panel, not a crashed
    callback.

    build_view defaults to the always-fresh _build_cluster_disconnection_view (what every test
    calls this with) - build_app passes its own cached wrapper instead, same perf reasoning as
    overlap_map_content_for's own cache (per-subject load+resample dominates the panel's response
    time for a real several-hundred-subject cluster)."""
    try:
        view, n_subjects, _img, missing_subjects = build_view(run, metadata, cluster_label, sdc_cfg, map_mode)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    # The caption states the threshold in "percent" mode: the map's whole meaning depends on
    # it, so it must never be read without it.
    caption, note = _map_texts("sdc", map_mode)
    return _anatomy_viewer(
        view, f"Cluster {cluster_label} (n={n_subjects})", caption,
        warning=_missing_subjects_warning(missing_subjects), note=note,
    )


def representative_subject_content_for(
    run: ProductionRun, embedding: np.ndarray, metadata: pd.DataFrame, cluster_label: int,
    lesion_cfg: LesionViewerConfig, sdc_cfg: SdcViewerConfig,
) -> html.Div | html.P:
    """Panel "Soggetto rappresentativo del cluster" (29-09-26, on request), shown after the
    two per-cluster map panels: the real subject closest to `cluster_label`'s centroid in the
    embedding space (cluster_centroids_with_nearest_subject) - a centroid is a mean point, not
    a real subject, this shows the closest real one instead. Dispatches to the lesion or SDC
    disconnectome viewer by `run.modality`.

    Same never-raises contract as every other *_content_for function here: an empty/
    unresolvable cluster, or a representative subject whose file can't be resolved on disk,
    renders an html.P status message instead of crashing the callback."""
    try:
        centroids = cluster_centroids_with_nearest_subject(embedding, metadata, load_cluster_space(run))
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    if cluster_label not in centroids.index:
        column = COLOR_MODES["cluster_label"].column
        return html.P(f"no subjects with {column}={cluster_label!r} in this run's metadata", className="status-message")
    subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
    distance = centroids.loc[cluster_label, "distance_to_centroid"]

    try:
        if run.modality == "lesion":
            view, dataset = _build_subject_lesion_view(run, subject_id, metadata, lesion_cfg)
        else:
            view, dataset = _build_subject_disconnectome_view(run, subject_id, metadata, sdc_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(
        view, f"Cluster {cluster_label} — representative: {subject_id} ({dataset})",
        f"Real subject closest to the cluster centroid in the clustering space (distance={format_number(distance, 3)})",
    )


def _italian_figure(figure: go.Figure) -> go.Figure:
    """`figure` with ',' as decimal separator and '.' for thousands in every number Plotly formats (ticks, hover,
    colorbars), as format_number does for the text of the page."""
    return figure.update_layout(separators=PLOTLY_SEPARATORS)


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


# --- PCA component maps (16-10-26) ---------------------------------------------------------------

# A voxel of a component's map is coloured when its |t| reaches this share of the component's peak |t|: with
# thousands of subjects even small effects have a high t, and a fixed |t| > 3 would colour almost the whole brain.
COMPONENT_MAP_THRESHOLD_FRACTION = 0.3
_COMPONENT_MAP_CMAP = "cold_hot"


@dataclass(frozen=True)
class ComponentMapData:
    """What the component-map panel needs for one pca run: the maps, where their voxels are, and whether the
    source matrix was modified after the run was written (the maps then pair the run's scores with a matrix that
    may not be the one they came from)."""

    maps: ComponentMapSet
    geometry: MapGeometry
    source_modified_after_run: bool


def _is_pca_run(run: ProductionRun) -> bool:
    return run.pipeline == "dim_reduction" and run.method == "pca"


def run_component_maps(run: ProductionRun, store: ComponentMapStore) -> ComponentMapData | None:
    """The component maps of a pca dim_reduction run (src/analysis/component_maps.py), or None while they are
    still being computed in the background.

    The scores are the run's own matrix.npy; the matrix they are regressed against is the run's `input_path`
    (relative to the folder the app is launched from, the repo root). Raises ValueError, with the cause, for a
    run that is not a pca one, a source matrix that is missing, not voxelwise, or not the run's (other subjects)."""
    if not _is_pca_run(run):
        raise ValueError("component maps exist only for dim_reduction runs with the pca method")
    input_path = read_run_config(run.path)["input_path"]
    source_dir = Path(input_path)
    if not (source_dir / MATRIX_FILENAME).is_file():
        raise ValueError(
            f"the matrix the run was computed on ({input_path}) does not exist: it is needed for the maps, "
            "and it is looked up from the folder the app was launched from"
        )
    geometry = load_map_geometry(source_dir)
    maps = store.request(source_dir, np.load(run.path / MATRIX_FILENAME), run_metadata(run)["subject_id"].tolist())
    if maps is None:
        return None
    written = datetime.fromisoformat(json.loads((run.path / MANIFEST_FILENAME).read_text())["created_at"])
    modified = datetime.fromtimestamp((source_dir / MATRIX_FILENAME).stat().st_mtime, tz=timezone.utc)
    return ComponentMapData(maps=maps, geometry=geometry, source_modified_after_run=modified > written)


def _build_component_map_view(data: ComponentMapData, component: int) -> tuple[StatMapView, float]:
    """(interactive view, peak t) of one component (1-based): the t-map of the component, voxels below
    COMPONENT_MAP_THRESHOLD_FRACTION of its peak left uncoloured, the three sections crossing at the peak.
    Raises ValueError for a component with an all-zero map or outside the run's components."""
    n_components = data.maps.t.shape[0]
    if not 1 <= component <= n_components:
        raise ValueError(f"component {component} does not exist: the run has {n_components}")
    t_map = np.asarray(data.maps.t[component - 1])
    peak_column = int(np.argmax(np.abs(t_map)))
    peak = float(t_map[peak_column])
    if peak == 0.0:
        raise ValueError(f"the map of component {component} is all zero: no voxel has an effect")
    peak_voxel = np.unravel_index(np.flatnonzero(data.geometry.mask)[peak_column], data.geometry.shape)
    peak_mm = nib.affines.apply_affine(data.geometry.affine, peak_voxel)
    shown = _masked_for_view_colorbar(to_volume(t_map, data.geometry), COMPONENT_MAP_THRESHOLD_FRACTION * abs(peak))
    view = nilearn_plotting.view_img(
        shown, bg_img="MNI152", black_bg=False, threshold=1e-6, cmap=_COMPONENT_MAP_CMAP, symmetric_cmap=True,
        vmax=abs(peak), cut_coords=tuple(float(c) for c in peak_mm), title=None, width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, peak


def component_maps_content_for(
    run: ProductionRun,
    component: int,
    maps_of: Callable[[ProductionRun], ComponentMapData | None],
    view_of: Callable[[ComponentMapData, int], tuple[StatMapView, float]] = _build_component_map_view,
) -> tuple[html.Div | html.P, bool]:
    """(content, pending) of the "Mappe delle componenti" panel for one component (1-based) of a pca run:
    the reproducibility of every component's map, then the chosen component's t-map in an interactive viewer.
    `pending` is True while the maps are still being computed: the content then says so and the caller keeps
    polling. Same never-raises contract as the other *_content_for functions."""
    try:
        data = maps_of(run)
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message"), False
    if data is None:
        return html.P(
            "Computing the maps: one pass over the voxel matrix for each subject, from a few minutes "
            "upwards depending on the matrix. It is saved to disk: next time it is instant. The page updates by itself.",
            className="status-message",
        ), True
    try:
        view, peak = view_of(data, component)
    except ValueError as exc:
        return html.P(str(exc), className="status-message"), False

    reproducibility = data.maps.reproducibility
    children: list = []
    if data.source_modified_after_run:
        children.append(_warning_box(
            "The matrix the run was computed on was modified after the run. If its subjects or its values "
            "have changed, the maps pair the run scores with data that is not what they came from."
        ))
    children += [
        html.P(
            f"Mean reproducibility {format_number(float(reproducibility.mean()), 3)} ± "
            f"{format_number(float(reproducibility.std(ddof=1)) if len(reproducibility) > 1 else 0.0, 3)}, "
            f"from {format_number(float(reproducibility.min()), 3)} (component {int(reproducibility.argmin()) + 1}) to "
            f"{format_number(float(reproducibility.max()), 3)} (component {int(reproducibility.argmax()) + 1}). "
            "The paper reports 0.813 ± 0.079 with halves of 666 subjects: here the halves are much larger, so the values are not directly comparable.",
            className="section-intro",
        ),
        dcc.Graph(
            figure=_italian_figure(build_reproducibility_figure(reproducibility, component)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        ),
        _anatomy_viewer(
            view,
            heading=f"Component {component}: max t {format_number(abs(peak), 0)}, reproducibility {format_number(float(reproducibility[component - 1]), 2)}",
            caption=(
                "Red: the more a subject has this component, the more that voxel is disconnected. Blue: the more it has it, the less it is disconnected. "
                f"Voxels with |t| of at least {format_number(COMPONENT_MAP_THRESHOLD_FRACTION * 100, 0)}% of the peak are colored."
            ),
            note=(
                "The sign of a component is arbitrary: each map is oriented with the peak red, so look at the shape, "
                "not the color. The map is the t of a multiple regression per voxel on the scores of all components together "
                "(not the component weights), without a permutation test."
            ),
        ),
    ]
    return html.Div(children), False


# --- Clustering quality (16-10-26) ----------------------------------------------------------------

# The silhouette of every subject reads every pair of subjects, so its cost grows with the number of columns:
# about a second for 5845 subjects x 10 components, minutes for the 221955 voxels of a raw lesion matrix.
# Past this many columns the panel does not draw it (the notebook reads such a run memory-mapped).
MAX_QUALITY_COLUMNS = 1000


def _require_narrow_matrix(run: ProductionRun) -> None:
    """Raises ValueError if the matrix `run` was clustered on has more than MAX_QUALITY_COLUMNS columns."""
    n_columns = _matrix_shape(run)[1]
    if n_columns > MAX_QUALITY_COLUMNS:
        raise ValueError(
            f"the run was computed on {n_columns} columns (raw data, not an embedding): not drawn here "
            f"beyond {MAX_QUALITY_COLUMNS} columns (read the indices of the tuning: tuning_results.csv and report.md)"
        )


def run_production_results(run: ProductionRun) -> SavedResults:
    """The numbers the production run saved (production_results.csv and production_results_per_cluster.csv): the panel
    shows them, it does not compute them again. Raises FileNotFoundError for a run without the files and ValueError
    for files that are not the method's (read_production_results)."""
    return read_production_results(run.path, run.method)


def run_distance_metric(run: ProductionRun) -> str:
    """The distance the run was clustered with (the one its silhouette is measured in)."""
    return run_metric(run_params(run))


def run_silhouette_samples(run: ProductionRun) -> SilhouetteBreakdown:
    """The silhouette of every subject of a clustering run, on the matrix it was clustered on (matrix.npy) and in the
    run's own distance: the one thing the saved tables do not hold, because it has a value per subject.

    Raises ValueError, with the cause, for a matrix with more than MAX_QUALITY_COLUMNS columns or a run the silhouette
    is not defined for (fewer than 2 clusters, a non-Euclidean affinity)."""
    _require_narrow_matrix(run)
    matrix, metadata, _extra_arrays = load_matrix(run.path)
    return per_cluster_silhouette(matrix, metadata["cluster_label"].to_numpy(), run_params(run))


def run_soft_membership(run: ProductionRun) -> SoftMembership:
    """The soft clustering of a hdbscan_soft run: the per-cluster summary with the mean
    membership vectors. Read from the membership.npy the run saved, no refit. Raises ValueError, with the
    cause, for another method or a run without membership.npy."""
    require_applicable("soft_membership", run.method)
    _matrix, metadata, extra_arrays = load_matrix(run.path, mmap=True)  # only the labels and membership are wanted
    if "membership" not in extra_arrays:
        raise ValueError("the run has no membership.npy: it is not an hdbscan_soft production run")
    return soft_membership_summary(metadata["cluster_label"].to_numpy(), extra_arrays["membership"])


# How often the panel looks again at a background computation (milliseconds).
_QUALITY_POLL_MS = 5000

# Neighbours counted by the purity of an adp run.
ADP_K_NEIGHBORS = 10


def run_adp_summary(run: ProductionRun, store: RawDistanceStore) -> AdpSummary | None:
    """k-neighbour purity and silhouette on the dice distance of an adp run, or None while the distance
    matrix is still being computed in the background (RawDistanceStore.request).

    Reads the run's own matrix.npy (what adp clustered: the matrix may have been rebuilt since, the
    run keeps its copy) memory-mapped, and only metadata.csv for the subjects and labels. Raises
    ValueError for a run that is not adp, or whatever adp_summary refuses."""
    require_applicable("knn_purity", run.method)
    metadata = run_metadata(run)
    distances = store.request(run.path / MATRIX_FILENAME, metadata["subject_id"].tolist(), run_params(run)["metric"])
    if distances is None:
        return None
    return adp_summary(distances.distances, distances.non_empty, metadata["cluster_label"].to_numpy(), ADP_K_NEIGHBORS)


def _guide(title: str, points: list[tuple[str, str]], limits: list[str] | None = None) -> html.Details:
    """A collapsed explanation under a panel's heading: one bullet per idea ("Name: sentence"), then, if any,
    the limits of the reading, one bullet each."""
    children: list = [
        html.Summary(title),
        html.Ul([html.Li([html.B(f"{name}: "), text]) for name, text in points], className="comparison-points"),
    ]
    if limits:
        children += [
            html.P("Limits", className="comparison-subheading"),
            html.Ul([html.Li(limit) for limit in limits], className="comparison-points"),
        ]
    return html.Details(className="comparison-guide", children=children)


def _adp_guide() -> html.Details:
    """How to read the adp indices (the adp indices)."""
    return _guide(
        "How to read these indices",
        [
            ("Neighbor purity", (
                f"for each subject, the share of its {ADP_K_NEIGHBORS} nearest neighbors (dice distance, the one adp used to "
                "cluster) that lies in its own cluster. From 0 to 1; near 1 the neighbors almost always lie in its "
                "cluster. Read it next to the value expected by chance, (cluster n - 1) / (total n - 1)"
            )),
            ("Small clusters", (
                f"a cluster with {ADP_K_NEIGHBORS} subjects or fewer cannot reach 1: it stays in the table but is left out of the summary"
            )),
            ("Pairs at distance 1", (
                "share of subject pairs with no voxel in common, to be looked at before the silhouette. If it is high "
                "(lesions: 84%) almost all distances equal 1 and the silhouette stays near 0 whatever the structure: "
                "use the purity. If it is low (voxelwise disconnectome: 0.0015%) the silhouette is read as for the other methods"
            )),
            ("Share with ties", (
                "subjects whose last counted neighbor has the same distance as the next one; for them the purity is the value "
                "expected when choosing at random among the ties"
            )),
        ],
        [
            "Purity is partly circular: adp forms the clusters on exactly these neighbors. A high purity says the clusters are coherent, not that they are \"true\".",
            "The silhouette is on the dice distance: it is not comparable with the Euclidean one of the runs on embeddings.",
            "Noise (-1) and the subjects with an all-zero matrix (dice distance undefined, adp labels them -1) are excluded.",
        ],
    )


def adp_quality_content_for(
    run: ProductionRun, summary_of: Callable[[ProductionRun], AdpSummary | None]
) -> tuple[html.Div | html.P, bool]:
    """(content, pending) of the "Valutazione del clustering" panel for an adp run: the k-neighbour purity,
    the silhouette on the dice distance and the share of pairs at distance 1, with a per-cluster table.
    `pending` is True while the distance matrix is still being computed: the content then says so and
    the caller keeps polling. Same never-raises contract as the other *_content_for functions."""
    try:
        summary = summary_of(run)
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message"), False
    if summary is None:
        return html.P(
            "Computing the dice distance matrix between the subjects (about 4 minutes for lesions, "
            "up to about 25 for the voxelwise disconnectome). It is saved to disk: next time it is instant. "
            "The page updates by itself.",
            className="status-message",
        ), True

    def share(value: float) -> str:
        return f"{format_number(value * 100, 1)}%"

    purity, silhouette = summary.purity, summary.silhouette
    rows = [
        [f"Purity of the {summary.k} neighbors", format_number(purity.purity, 3), "higher is better, from 0 to 1"],
        ["Purity expected by chance", format_number(purity.chance, 3), "to be read next to the purity"],
        ["Dice silhouette (mean over subjects)", format_number(silhouette.micro, 3), "higher is better, from -1 to 1"],
        ["Pairs at distance 1", share(summary.pairs_at_distance_1), "if it is high the silhouette is not informative"],
        ["Clusters (noise excluded)", str(len(purity.clusters)), ""],
        ["Noise", share(summary.noise_fraction), "of the subjects"],
        [f"Subjects in clusters of {summary.k} or fewer", str(purity.n_not_evaluable), "left out of the purity summary"],
        ["Share with ties", share(purity.tied_share), "subjects with neighbors at equal distance"],
    ]
    cluster_rows = [
        [
            str(label), str(int(row.n)), format_number(row.purity, 3), format_number(row.chance, 3),
            "yes" if row.evaluable else "no", format_number(row.silhouette_mean, 3), share(row.share_negative),
        ]
        for label, row in summary.clusters.iterrows()
    ]
    children: list = [_adp_guide()]
    children += [
        html.P(
            f"Computed on the dice distance of the raw data, the one adp clustered with, on {summary.n_clustered} "
            f"clustered subjects out of {summary.n_subjects}.",
            className="quality-intro",
        ),
        _table(["Index", "Value", "Reading"], rows, text_columns=(0, 2)),
        html.P("Per cluster", className="comparison-subheading"),
        _table(
            ["Cluster", "Subjects", "Purity", "Expected by chance", "Evaluable", "Mean silhouette", "Negative silhouette"],
            cluster_rows, text_columns=(0,),
        ),
        _chart_heading("Silhouette per cluster", "one panel per cluster, noise excluded"),
        dcc.Graph(
            figure=_italian_figure(build_silhouette_figure(summary.silhouette.subject_labels, summary.silhouette.subject_values)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        ),
    ]
    return html.Div(children), False


def _quality_guide() -> html.Details:
    """How to read the geometric indices (the geometric indices)."""
    return _guide(
        "How to read these indices",
        [
            ("Silhouette", (
                "for each subject, compares the mean distance from its own cluster with that from the nearest cluster. "
                "From -1 to 1, higher is better: near 1 the clusters are sharp, near 0 the boundaries are ambiguous, "
                "negative the subject is in the wrong cluster"
            )),
            ("Calinski-Harabasz", "dispersion between clusters divided by that within clusters. Higher is better"),
            ("Davies-Bouldin", "for each cluster, similarity to the most similar cluster. Lower is better, 0 = compact and separated clusters"),
            ("Dunn", "minimum distance between clusters divided by the maximum diameter of a cluster. Higher is better, it is sensitive to outliers"),
            ("Plot per cluster", (
                "one panel per cluster with the silhouette of each subject, highest at the top: it shows which clusters have "
                "ambiguous boundaries even if the overall mean is good (how many subjects are below zero, how homogeneous "
                "the cluster is). The panel height follows the cluster size, with a minimum so that a small cluster "
                "stays readable; a one-subject cluster has silhouette 0 by convention. The red line is the mean over the "
                "subjects. Hovering over a point shows the cluster, its size and the silhouette of that subject"
            )),
        ],
        [
            "None of the four indices has a reference value.",
            "A cloud with no clusters, split by an algorithm, still has a positive silhouette (ward, 3 clusters, "
            "2-component Gaussian cloud: about 0.4): the value alone does not say whether there is structure.",
            "Calinski-Harabasz, Davies-Bouldin and Dunn of a single run have no scale.",
            "Different embeddings (2 or 10 components, lesion or sdc) are not comparable with each other.",
        ],
    )


def _soft_membership_block(
    run: ProductionRun, soft_of: Callable[[ProductionRun], SoftMembership]
) -> html.Div:
    """Section 3.2 for a hdbscan_soft run: per cluster table and mean membership vectors."""
    heading = html.P("Cluster membership (soft clustering)", className="comparison-subheading")
    try:
        summary = soft_of(run)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])

    def other(value) -> str:
        return "—" if pd.isna(value) else str(int(value))

    cluster_rows = [
        [
            str(label), str(int(row.n)), format_number(row.own_mean, 3),
            other(row.top_other), format_number(row.top_other_mean, 3) if pd.notna(row.top_other_mean) else "—",
        ]
        for label, row in summary.clusters.iterrows()
    ]
    return html.Div([
        heading,
        _guide(
            "How to read these tables",
            [
                ("Rows", "do not sum to 1: the rest is the probability of being noise"),
                ("Heatmap", "diagonal = mean probability in the own cluster; off-diagonal = clusters that overlap"),
            ],
            [
                "It depends on the density of the clustered space: on UMAP with min_dist = 0 it also measures how tightly UMAP packed the groups.",
                "There is no reference value for a probability: the tables report means, with no threshold.",
            ],
        ),
        html.P(f"{summary.n_noise} noise subjects: they have no cluster of their own, and have a separate row in the matrix.", className="quality-intro"),
        _table(
            ["Cluster", "Subjects", "Mean probability in own", "Most likely other cluster", "Mean probability in the other"],
            cluster_rows, text_columns=(0,),
        ),
        _chart_heading("Mean membership vectors", "rows: subjects cluster; columns: membership cluster"),
        dcc.Graph(
            figure=_italian_figure(build_mean_membership_figure(summary.mean_vectors)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        ),
    ])


def _density_guide(soft: bool) -> html.Details:
    """How to read DBCV, the probability of a subject in its cluster and (hdbscan_soft) the persistence of a cluster, and
    why the silhouette-family indices are not shown for hdbscan / hdbscan_soft."""
    points = [
        ("DBCV", (
            "density-based cluster validity (Moulavi et al. 2014). For each cluster it compares how sparse the cluster is "
            "inside with how far it is from the nearest cluster. From -1 to 1, higher is better"
        )),
        ("The run's score", (
            "the average of the clusters' own scores, each weighted by its share of all the subjects, noise included: "
            "the noise lowers the score by itself, so a clustering that throws the hard subjects away is not rewarded"
        )),
        ("Plot per cluster", "one bar per cluster with its own score and size; the dashed line is the run's score, which is not the mean of the bars"),
        ("Probability", (
            "from 0 to 1, within the cluster: near 1 the subject is at the core, near 0 at the margin. It is not the probability "
            "of being in this cluster rather than another, nor comparable across clusters of different density"
        )),
    ]
    if soft:
        points.append((
            "Persistence",
            "from 0 to 1 for each cluster: 1 is a cluster that lasts over all the distance scales of the tree, 0 one that vanishes at once",
        ))
    return _guide(
        "How to read DBCV",
        points,
        [
            "Silhouette, Calinski-Harabasz, Davies-Bouldin and Dunn are not computed for these methods: they use the non-noise subjects only "
            "(the hardest ones, thrown into the noise, make them rise) and assume compact clusters.",
            "DBCV has no reference value, and it is not comparable across different embeddings.",
            "It is undefined with fewer than 2 clusters.",
            "The probability depends on the density of the clustered space: on UMAP with min_dist = 0 it tells how tightly UMAP packed "
            "the cluster, not that it is real. There is no reference value for a probability"
            + (" or a persistence" if soft else "") + ": the tables report means, with no threshold.",
        ],
    )


def _saved_row(label: str, saved: SavedResults, name: str, decimals: int, reading: str, percent: bool = False) -> list[str]:
    """[label, value, reading] of a metric a run saved. A metric that is not defined for the run is a dash and the reason
    saved with it (its note)."""
    value = saved.values[name]
    if np.isnan(value):
        return [label, "—", saved.notes[name]]
    return [label, f"{format_number(value * 100, 1)}%" if percent else format_number(value, decimals), reading]


def _cell(value: float, decimals: int) -> str:
    """A number of a per-cluster table, a dash where the run saved none."""
    return "—" if pd.isna(value) else format_number(value, decimals)


def _share_cell(value: float) -> str:
    return "—" if pd.isna(value) else f"{format_number(value * 100, 1)}%"


def _tree_block(saved: SavedResults, n_clusters: int) -> html.Div:
    """The "Model statistic" block of an agglomerative run: the cophenetic correlation and the dendrogram jump it saved."""
    rows = [
        _saved_row("Cophenetic correlation", saved, "cophenetic_correlation", 3, ""),
        _saved_row(f"Dendrogram jump (k={n_clusters})", saved, "dendrogram_jump", 2, ""),
    ]
    return html.Div([
        html.P("Model statistic", className="comparison-subheading"),
        # the third column only says why a statistic is not defined: no column when every one is
        _table(["Statistic", "Value", "Reading"], rows, text_columns=(0, 2))
        if any(row[2] for row in rows)
        else _table(["Statistic", "Value"], [row[:2] for row in rows], text_columns=(0,)),
        html.P(
            "Cophenetic correlation: how faithfully the tree reflects the real distances between subjects. From -1 to 1: "
            "the higher, the better the tree reproduces them. It is measured with the run's own distance, so it is not "
            "comparable between runs with a different metric.",
            className="comparison-note centered",
        ),
        html.P(
            "Dendrogram jump (at the run's k): how sharp the cut at k is. It is the height of the merge that takes the tree "
            "from k to k-1 clusters divided by the height of the merge from k+1 to k. Near 1 the tree has no clear gap at k; "
            "the higher, the sharper the cut. Heights are in the units of each linkage, so it is not comparable between linkages.",
            className="comparison-note centered",
        ),
    ])


def _agglomerative_quality_content(
    run: ProductionRun,
    saved: SavedResults,
    metric: str,
    silhouette_of: Callable[[ProductionRun], SilhouetteBreakdown],
) -> html.Div:
    """The panel of an agglomerative run: the indices and the tree statistics it saved, its table per cluster, and the
    silhouette of every subject (the one part computed here, `silhouette_of`; a run it cannot be drawn for says why)."""
    clusters = saved.per_cluster
    n_clusters = len(clusters)
    rows = [
        _saved_row("Silhouette (mean over subjects)", saved, "silhouette", 3, "higher is better, from -1 to 1"),
        _saved_row("Calinski-Harabasz", saved, "calinski_harabasz", 1, "higher is better"),
        _saved_row("Davies-Bouldin", saved, "davies_bouldin", 3, "lower is better"),
        _saved_row("Dunn", saved, "dunn", 4, "higher is better"),
        ["Clusters", str(n_clusters), ""],
        _saved_row("Largest cluster", saved, "largest_cluster_share", 1, "of the subjects", percent=True),
    ]
    cluster_rows = [
        [str(int(row.cluster)), str(int(row.n)), _cell(row.silhouette_mean, 3), _share_cell(row.share_negative)]
        for row in clusters.itertuples()
    ]
    try:
        breakdown = silhouette_of(run)
    except (ValueError, OSError) as exc:
        silhouette_chart: list = [html.P(str(exc), className="status-message")]
    else:
        silhouette_chart = [dcc.Graph(
            figure=_italian_figure(build_silhouette_figure(breakdown.subject_labels, breakdown.subject_values)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        )]
    return html.Div([
        _quality_guide(),
        html.P(
            f"{int(clusters['n'].sum())} subjects, as the production run saved them (production_results.csv)"
            + ("." if metric == "euclidean" else f". The silhouette uses the {metric} distance, the one the clustering used."),
            className="quality-intro",
        ),
        _table(["Index", "Value", "Reading"], rows, text_columns=(0, 2)),
        html.P("Per cluster", className="comparison-subheading"),
        _table(["Cluster", "Subjects", "Mean silhouette", "Negative silhouette"], cluster_rows, text_columns=(0,)),
        _chart_heading("Silhouette per cluster", "one panel per cluster"),
        *silhouette_chart,
        _tree_block(saved, n_clusters),
    ])


def _density_quality_content(
    run: ProductionRun, saved: SavedResults, soft_of: Callable[[ProductionRun], SoftMembership]
) -> html.Div:
    """The panel of an hdbscan / hdbscan_soft run: DBCV, the shares of clusters and noise and the mean probability of the
    subjects in their cluster (and, for hdbscan_soft, the persistence of the clusters) as the run saved them, its table
    per cluster and the DBCV of every cluster. A DBCV not defined for the run is a dash with the reason and no chart.
    hdbscan_soft adds its soft membership, read from the membership.npy the run saved."""
    soft = run.method == "hdbscan_soft"
    rows = [
        _saved_row("DBCV", saved, "dbcv", 3, "higher is better, from -1 to 1"),
        ["Clusters (noise excluded)", str(int(saved.values["n_clusters_found"])), ""],
        _saved_row("Largest cluster", saved, "largest_cluster_share", 1, "of the subjects", percent=True),
        _saved_row("Noise", saved, "noise_fraction", 1, "of the subjects", percent=True),
        _saved_row("Mean probability in own cluster", saved, "membership_mean", 3, "mean over the clustered subjects"),
    ]
    if soft:
        rows.append(_saved_row("Mean persistence", saved, "persistence_mean", 3, "mean over the clusters"))
    columns = ["Cluster", "Subjects", "DBCV", "Mean probability"] + (["Persistence"] if soft else [])
    cluster_rows = [
        [str(int(row.cluster)), str(int(row.n)), _cell(row.dbcv, 3), _cell(row.membership_mean, 3)]
        + ([_cell(row.persistence, 3)] if soft else [])
        for row in saved.per_cluster.itertuples()
    ]
    chart: list = []
    if not np.isnan(saved.values["dbcv"]):
        clusters = saved.per_cluster.set_index("cluster")[["n", "dbcv"]]
        try:
            figure = build_dbcv_figure(clusters, saved.values["dbcv"])
        except ValueError as exc:
            chart = [_chart_heading("DBCV per cluster", "one bar per cluster; the dashed line is the run's score"), html.P(str(exc), className="status-message")]
        else:
            chart = [
                _chart_heading("DBCV per cluster", "one bar per cluster; the dashed line is the run's score"),
                dcc.Graph(
                    figure=_italian_figure(figure),
                    config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
                    style={"width": "100%"},
                ),
            ]
    return html.Div([
        _density_guide(soft),
        html.P("As the production run saved them (production_results.csv).", className="quality-intro"),
        _table(["Index", "Value", "Reading"], rows, text_columns=(0, 2)),
        html.P("Per cluster", className="comparison-subheading"),
        _table(columns, cluster_rows, text_columns=(0,)),
        *chart,
        *([_soft_membership_block(run, soft_of)] if soft else []),
    ])


def cluster_quality_content_for(
    run: ProductionRun,
    results_of: Callable[[ProductionRun], SavedResults] = run_production_results,
    silhouette_of: Callable[[ProductionRun], SilhouetteBreakdown] = run_silhouette_samples,
    soft_of: Callable[[ProductionRun], SoftMembership] = run_soft_membership,
    metric_of: Callable[[ProductionRun], str] = run_distance_metric,
) -> html.Div:
    """Panel "Clustering evaluation" of an agglomerative, hdbscan or hdbscan_soft run: under the collapsed guide to the
    indices, the numbers the production run saved (`results_of`: production_results.csv and
    production_results_per_cluster.csv, never computed again) and its table per cluster. An agglomerative run adds the
    silhouette of every subject (`silhouette_of`), the one part computed here; an hdbscan_soft run its soft membership.
    Not tied to the chosen cluster.

    Same never-raises contract as every other *_content_for: a run without the saved files (written before production
    runs saved them) or with files that are not its method's renders the cause instead of a table, and so does a method
    the panel has no numbers for."""
    if run.method not in RESULTS_METHODS:
        return html.Div([html.P(
            f"The panel has no numbers for the method {run.method!r}: production runs of {list(RESULTS_METHODS)} save them.",
            className="status-message",
        )])
    agglomerative = run.method == "agglomerative"
    try:
        saved = results_of(run)
        metric = metric_of(run) if agglomerative else ""
    except (ValueError, OSError) as exc:
        guide = _quality_guide() if agglomerative else _density_guide(run.method == "hdbscan_soft")
        return html.Div([guide, html.P(str(exc), className="status-message")])
    if agglomerative:
        return _agglomerative_quality_content(run, saved, metric, silhouette_of)
    return _density_quality_content(run, saved, soft_of)


# --- Comparison inside a run and between two runs (08-10-26) ------------------------------------

COMPARISON_MODE_CLUSTERS = "clusters"
COMPARISON_MODE_MODALITY = "modality"
COMPARISON_MODE_LABELS: dict[str, str] = {
    COMPARISON_MODE_CLUSTERS: "Within the same clustering",
    COMPARISON_MODE_MODALITY: "Between modalities (lesion vs sdc)",
}
COMPARISON_MODE_RULES: dict[str, str] = {
    COMPARISON_MODE_CLUSTERS: (
        "Two clusters of the same run (also the HDBSCAN noise, -1): demographic and clinical profile, "
        "variables that distinguish them, distance between centroids and anatomy, on the subjects of the two clusters only."
    ),
    COMPARISON_MODE_MODALITY: (
        "Two runs of different modalities (lesion and sdc) with the same clustering method, the same parameters "
        "and the same starting embedding (reduction method, components, metric): "
        "only the modality changes, and the comparison is made on the subjects in common."
    ),
}


def comparison_run_label(run: ProductionRun) -> str:
    return f"{run.modality} · {run.method} · {run.run_name}"


def comparison_candidates(runs: list[ProductionRun]) -> list[ProductionRun]:
    """Runs that can be the first side of a comparison, in either mode: every clustering run.
    Ordered by modality, method, then chronologically."""
    candidates = [run for run in runs if run.pipeline == "clustering"]
    return sorted(candidates, key=lambda run: (run.modality, run.method, _run_chronological_key(run)))


def comparison_incompatibility(run_a: ProductionRun, run_b: ProductionRun, clustering_params_file: str | Path) -> str | None:
    """Why `run_a` and `run_b` cannot be compared across modalities, or None if they can: different
    modality, but same clustering method, same values of that method's registered tag_param
    (k, linkage, ...) and same upstream embedding settings - so that the only thing that varies is
    the modality, never also the clustering criterion.

    Raises ValueError when a run's config.md/params cannot be read."""
    if run_a.key == run_b.key:
        return "the two runs are the same run"
    for run in (run_a, run_b):
        if run.pipeline != "clustering":
            return f"{run.key} is not a clustering run"
    if run_a.modality == run_b.modality:
        return f"both runs have modality {run_a.modality!r}: different modalities are needed"
    if run_a.method != run_b.method:
        return f"different clustering methods ({run_a.method} ≠ {run_b.method}): in this mode only the modality must change"
    if run_a.reduction_method != run_b.reduction_method:
        return f"different reduction methods ({run_a.reduction_method} ≠ {run_b.reduction_method})"
    axis_a, axis_b = run_reduction_axis(run_a), run_reduction_axis(run_b)
    if axis_a != axis_b:
        return f"different starting embeddings (metric, components): {axis_a} ≠ {axis_b}"
    tag_param = _load_tag_params_or_none(clustering_params_file, run_a.method)
    if tag_param:
        label_a, label_b = _run_tag_param_label(run_a, tag_param), _run_tag_param_label(run_b, tag_param)
        if label_a is None or label_b is None:
            raise ValueError(f"{run_a.path} / {run_b.path}: cannot read the {run_a.method} parameters of both runs")
        if label_a != label_b:
            return f"different method parameters ({label_a} ≠ {label_b})"
    return None


def comparable_runs(runs: list[ProductionRun], run_a: ProductionRun, clustering_params_file: str | Path) -> list[ProductionRun]:
    """The runs that can sit opposite `run_a` across modalities (the options of the second picker).
    A run whose config.md or params cannot be read is left out and logged, like the other pickers:
    one broken run must not hide every other option."""
    compatible = []
    for candidate in comparison_candidates(runs):
        try:
            reason = comparison_incompatibility(run_a, candidate, clustering_params_file)
        except ValueError as exc:
            logging.warning("%s: excluded from the comparison options: %s", candidate.path, exc)
            continue
        if reason is None:
            compatible.append(candidate)
    return compatible


def _chart_heading(title: str, subtitle: str) -> html.Div:
    """The title of a chart as page text (a sub-heading and one line under it), not inside the figure."""
    return html.Div([
        html.P(title, className="comparison-subheading"),
        html.P(subtitle, className="quality-intro"),
    ])


def _table(headers: list[str], rows: list[list], text_columns: tuple[int, ...] = (0,)) -> html.Div:
    """A table of the comparison section. The columns in `text_columns` hold labels (left-aligned),
    the rest numbers; a header may break at "\\n" (see .comparison-table), so a column is as wide as
    its numbers, not as its title."""
    def cells(tag, values):
        return [tag(value, className="text-col" if i in text_columns else None) for i, value in enumerate(values)]

    table = html.Table(
        [html.Thead(html.Tr(cells(html.Th, headers))), html.Tbody([html.Tr(cells(html.Td, row)) for row in rows])],
        className="stats-table comparison-table",
    )
    return html.Div(table, className="stats-table-wrap comparison-table-wrap")


def _points(lead: str, points: list) -> html.Div:
    """A note as one lead sentence and one short line per idea; a point is a string or a list of
    children (so a term can be bold)."""
    return html.Div([
        html.P(lead, className="comparison-lead"),
        html.Ul([html.Li(point) for point in points], className="comparison-points"),
    ])


def _agreement_guide() -> html.Details:
    """How to read the four agreement metrics, collapsed under the metrics table."""
    scale_rows = [
        [level, f"{_scale_range(AGREEMENT_SCALE['ARI'], i)}", f"{_scale_range(AGREEMENT_SCALE['NMI'], i)}"]
        for i, level in enumerate(AGREEMENT_LEVELS)
    ]
    return html.Details(
        className="comparison-guide",
        children=[
            html.Summary("How to read these metrics"),
            html.Ul([
                html.Li([html.B("ARI (Adjusted Rand Index): "), (
                    "agreement between the two partitions, corrected for chance. It counts the pairs of subjects put together "
                    "(or separated) by both. 1 = identical, 0 = as by chance, it can go below 0. "
                    "It does not inflate when there are many clusters."
                )]),
                html.Li([html.B("NMI (Normalized Mutual Information): "), (
                    "how much information the two partitions share, between 0 and 1. It is the harmonic mean of "
                    "homogeneity and completeness. More intuitive than ARI, but it can overestimate the agreement with many clusters."
                )]),
                html.Li([html.B("Homogeneity: "), "how much each cluster of A contains subjects of a single cluster of B (1 if A is a finer subdivision of B)."]),
                html.Li([html.B("Completeness: "), "how much the subjects of a cluster of B stay together in a single cluster of A (1 if B is a finer subdivision of A)."]),
            ]),
            html.P(
                "NMI, being a mean, hides the direction of an imbalance: two pairs with the same NMI "
                "can have low homogeneity and high completeness, or the opposite. That is why the two should "
                "also be read separately. High homogeneity and low completeness means A is finer than B "
                "(it splits the clusters of B); the opposite, that B is finer than A. The contingency table below "
                "tells which clusters cause the imbalance.",
                className="comparison-note",
            ),
            _table(["Level", "ARI", "NMI"], scale_rows),
        ],
    )


def _scale_range(bounds: tuple[float, ...], level_index: int) -> str:
    if level_index == 0:
        return f"< {bounds[0]}"
    if level_index == len(bounds):
        return f"> {bounds[-1]}"
    return f"{bounds[level_index - 1]}–{bounds[level_index]}"


def _comparison_summary(run_a: ProductionRun, run_b: ProductionRun, aligned: AlignedRuns) -> html.Div:
    """Which run is A and B, and how many subjects the comparison actually covers: the
    intersection is always stated against each run's full size, never absorbed silently."""
    return html.Div(
        className="comparison-summary",
        children=[
            html.P([html.B("A: "), comparison_run_label(run_a), f" · {format_number(aligned.n_a, 0)} subjects"]),
            html.P([html.B("B: "), comparison_run_label(run_b), f" · {format_number(aligned.n_b, 0)} subjects"]),
            html.P(
                [
                    html.B("Compared: "),
                    f"{format_number(aligned.n_common, 0)} subjects in common "
                    f"(only in A: {format_number(aligned.n_only_a, 0)} · only in B: {format_number(aligned.n_only_b, 0)}).",
                ]
            ),
        ],
    )


def _agreement_block(aligned: AlignedRuns) -> html.Div:
    metrics = agreement_metrics(aligned.labels_a, aligned.labels_b)
    rows = [
        [name, html.Span(format_number(value, 3), className="stat-value"), agreement_level(name, value) or "—"]
        for name, value in metrics.items()
    ]
    return html.Div([
        html.H3("Agreement between the partitions", className="comparison-heading"),
        _table(["Metric", "Value", "Reading"], rows, text_columns=(0, 2)),
        _agreement_guide(),
    ])


def _contingency_block(tables: ContingencyTables) -> html.Div:
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    figures = [
        build_table_heatmap(
            tables.counts, title="Subjects per pair of clusters", row_axis_title="cluster of A",
            column_axis_title="cluster of B", decimals=0, colorbar_title="subjects",
        ),
        build_table_heatmap(
            tables.row_pct, title="By row: where each cluster of A goes", row_axis_title="cluster of A",
            column_axis_title="cluster of B", decimals=1, suffix="%", colorbar_title="% of the row",
        ),
        build_table_heatmap(
            tables.col_pct, title="By column: where each cluster of B comes from", row_axis_title="cluster of A",
            column_axis_title="cluster of B", decimals=1, suffix="%", colorbar_title="% of the column",
        ),
    ]
    return html.Div([
        html.H3("Where each cluster ends up", className="comparison-heading"),
        html.P(
            "The numeric labels of the two clusterings are independent: cluster 0 of A is not “the same” as 0 of B. "
            "Only where the mass goes matters. By row: if almost everything is in one column, that cluster of A coincides with a "
            "cluster of B; if it is spread out, the two clusterings split it differently. By column the same holds, read "
            "from the side of B.",
            className="comparison-note",
        ),
        html.Div(
            className="composition-grid",
            children=[dcc.Graph(figure=_italian_figure(figure), config=config, style={"width": "100%"}) for figure in figures],
        ),
    ])


def _chi_square_block(counts: pd.DataFrame) -> html.Div:
    heading = html.H3("Statistical association", className="comparison-heading")
    try:
        result = chi_square_independence(counts)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    figure = build_table_heatmap(
        result.residuals, title="Standardized residuals", row_axis_title="cluster of A",
        column_axis_title="cluster of B", decimals=1, diverging=True, colorbar_title="residual",
    )
    return html.Div([
        heading,
        html.P(
            [
                html.B("Chi-square test of independence: "),
                f"χ² = {format_number(result.chi2, 1)}, degrees of freedom = {result.dof}, p = {format_scientific(result.p_value, 2)}.",
            ],
            className="comparison-summary-line",
        ),
        html.P(
            "H0: membership in a cluster of A is independent of membership in a cluster of B. With low p (< 0.05) the two "
            "partitions are not independent. The residuals tell where: red = the pair of clusters co-occurs more than "
            "expected, blue = less, gray = in line with independence. The p-value tells whether there is an association, the residuals "
            "which pairs drive it.",
            className="comparison-note",
        ),
        dcc.Graph(figure=_italian_figure(figure), config=config, style={"width": "100%"}),
    ])


def _purity_table(counts: pd.DataFrame, source: str, target: str) -> html.Div:
    table = purity_table(counts)
    rows = [
        [
            f"{source}: {cluster_name(int(label))}",
            format_number(int(row.n_subjects), 0),
            f"{target}: {cluster_name(int(row.dominant_target_cluster))}",
            html.Span(f"{format_number(float(row.purity_pct), 1)}%", className="stat-value"),
        ]
        for label, row in table.iterrows()
    ]
    return html.Div([
        html.P(f"Clusters of {source} to {target}", className="comparison-subheading"),
        _table(["Cluster", "Subjects", "Mostly goes to", "Share"], rows, text_columns=(0, 2)),
    ])


def _purity_block(counts: pd.DataFrame) -> html.Div:
    return html.Div([
        html.H3("Cluster purity", className="comparison-heading"),
        html.P(
            "For each cluster: where the largest share of its subjects ends up and how much it weighs. From the least pure (spread over "
            "several clusters) to the purest (almost all in one). The two directions are complementary: a cluster of A may "
            "flow entirely into one of B, while that of B also collects subjects of other clusters of A.",
            className="comparison-note",
        ),
        html.Div(
            className="composition-grid",
            children=[_purity_table(counts, "A", "B"), _purity_table(counts.T, "B", "A")],
        ),
    ])


def _clinical_profile_block(aligned: AlignedRuns, run_a: ProductionRun, run_b: ProductionRun) -> html.Div:
    """Clinical/demographic table of each run's clusters, on the common subjects. The centroids of
    two modalities live in different feature spaces and cannot be compared; what can be compared
    is the clinical phenotype of each cluster, which does not depend on coordinates."""
    heading = html.H3("Clinical profile of the clusters", className="comparison-heading")
    children: list = [
        heading,
        html.P(
            "The two modalities have different feature spaces: the centroids are not comparable. The comparison is on the "
            "clinical phenotype of each cluster, which does not depend on the coordinates. Subjects in common.",
            className="comparison-note",
        ),
    ]
    for side, run, labels in (("A", run_a, aligned.labels_a), ("B", run_b, aligned.labels_b)):
        frame = pd.DataFrame({"subject_id": aligned.subject_ids, _CLUSTER_LABEL_COLUMN: labels})
        children.append(html.P(f"{side}: {comparison_run_label(run)}", className="comparison-subheading"))
        try:
            children.append(_clusters_comparison_table(clusters_comparison_stats(frame), None))
        except (ValueError, OSError) as exc:
            children.append(html.P(str(exc), className="status-message"))
    return html.Div(children)


def comparison_content_for(run_a: ProductionRun, run_b: ProductionRun, clustering_params_file: str | Path) -> html.Div | html.P:
    """Mode "Tra modalità" of the "Confronto" section (08-10-26, on request): how two clustering
    runs of different modalities relate on the subjects they share - agreement metrics, contingency
    tables, chi-square test, purity, and the clinical profile of each cluster. Centroids are not
    compared: the two modalities live in different feature spaces.

    Same never-raises contract as every other *_content_for function here: a pair that is not
    comparable, a run that cannot be read or an empty intersection renders an html.P status
    message naming the cause, never a half-built section."""
    try:
        reason = comparison_incompatibility(run_a, run_b, clustering_params_file)
        if reason is not None:
            return html.P(f"The two runs are not comparable: {reason}.", className="status-message")
        aligned = align_runs(run_metadata(run_a), run_metadata(run_b))
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message")

    tables = contingency_tables(aligned.labels_a, aligned.labels_b)
    return html.Div([
        _comparison_summary(run_a, run_b, aligned),
        _agreement_block(aligned),
        _contingency_block(tables),
        _chi_square_block(tables.counts),
        _purity_block(tables.counts),
        _clinical_profile_block(aligned, run_a, run_b),
    ])


# --- Two clusters of the same run (08-10-26) --------------------------------------------------

_PAIR_SIGNIFICANCE_LEVEL = 0.05


def _pair_name(label: int) -> str:
    """"cluster 3", or "rumore" for HDBSCAN's -1 bucket. The two clusters are always called by
    their real label, never "1" and "2": a run's labels start at 0, and "cluster 1" would then
    name a different cluster than the one labelled 1."""
    return "noise" if label == -1 else f"cluster {label}"


def pair_cluster_option_label(label: int, metadata: pd.DataFrame) -> str:
    n_subjects = int((metadata[_CLUSTER_LABEL_COLUMN] == label).sum())
    return f"{_pair_name(label).capitalize()} · {format_number(n_subjects, 0)} subjects"


def _format_p(value: float) -> str:
    if np.isnan(value):
        return "—"
    return format_number(value, 3) if value >= 0.001 else format_scientific(value, 1)


def _p_fdr_cell(value: float):
    """The corrected p, in bold when it is under the 0.05 level."""
    text = _format_p(value)
    return html.Span(text, className="stat-value") if not np.isnan(value) and value < _PAIR_SIGNIFICANCE_LEVEL else text


def _format_optional(value: float, decimals: int) -> str:
    return "—" if np.isnan(value) else format_number(value, decimals)


def _format_median(value: float) -> str:
    """Whole numbers from 100 up (a voxel count), two decimals below (an age is read to the year
    elsewhere, but a share of the lesion is 0.xx)."""
    return "—" if np.isnan(value) else format_number(value, 0 if abs(value) >= 100 else 2)


def _cluster_pair_summary(run: ProductionRun, metadata: pd.DataFrame, label_1: int, label_2: int) -> html.Div:
    def line(role: str, label: int) -> html.P:
        n_subjects = int((metadata[_CLUSTER_LABEL_COLUMN] == label).sum())
        return html.P([html.B(f"{role}: "), f"{_pair_name(label)} · {format_number(n_subjects, 0)} subjects"])

    return html.Div(
        className="comparison-summary",
        children=[html.P([html.B("Run: "), comparison_run_label(run)]), line("First cluster", label_1), line("Second cluster", label_2)],
    )


def _cluster_pair_clinical_block(pair: PairFrame, label_1: int, label_2: int) -> html.Div:
    heading = html.H3("Demographic and clinical profile", className="comparison-heading")
    try:
        comparison: PairComparison = pair_clinical_comparison(pair, label_1)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)

    numeric_rows = [
        [
            row.variable, format_number(int(row.n_1), 0), format_number(int(row.n_2), 0),
            _format_median(row.median_1), _format_median(row.median_2), _format_optional(row.r, 2),
            _format_p(row.p), _p_fdr_cell(row.p_fdr),
        ]
        for row in comparison.numeric.itertuples()
    ]
    categorical_rows = [
        [
            row.variable, row.category, format_number(int(row.n_1), 0), format_number(int(row.n_2), 0),
            "—" if np.isnan(row.share_1) else f"{format_number(100 * row.share_1, 1)}%",
            "—" if np.isnan(row.share_2) else f"{format_number(100 * row.share_2, 1)}%",
            _format_optional(row.odds_ratio, 2), _format_p(row.p), _p_fdr_cell(row.p_fdr),
        ]
        for row in comparison.categorical.itertuples()
    ]
    children: list = [
        heading,
        _points(
            f"Each row compares a variable between {name_1} and {name_2}, on the subjects of the two clusters.",
            [
                [html.B("Numeric variables"), f" (Mann-Whitney test): the medians are compared. “r” measures the difference, "
                 f"from -1 to 1: positive if the values of {name_1} are higher, negative if they are lower, 0 if there is no difference. "
                 "Beyond 0.3 (in absolute value) the difference is already visible."],
                [html.B("Categorical variables"), f" (Fisher exact test, one category against all the others): the share "
                 f"of subjects with that category is compared. The odds ratio is above 1 if the category is more frequent in {name_1}, "
                 f"below 1 if it is more frequent in {name_2}."],
                [html.B("p"), " is the probability that the difference is due to chance; ", html.B("p (FDR)"),
                 " is the same value corrected for the number of comparisons made together. In bold below 0.05: "
                 "the difference is probably real."],
                [html.B("“—”"), ": the test was not run, because on one side there are fewer than 2 subjects with the data."],
            ],
        ),
    ]
    warning = _pair_unregistered_warning(pair.unregistered)
    if warning is not None:
        children.append(warning)
    children += [
        html.P("Numeric variables", className="comparison-subheading"),
        _table(
            ["Variable", f"n\n{name_1}", f"n\n{name_2}", f"Median\n{name_1}", f"Median\n{name_2}", "r", "p", "p\n(FDR)"],
            numeric_rows,
        ),
        html.P("Categorical variables", className="comparison-subheading"),
        _table(
            ["Variable", "Category", f"n\n{name_1}", f"n\n{name_2}", f"Share\n{name_1}", f"Share\n{name_2}", "Odds\nratio", "p", "p\n(FDR)"],
            categorical_rows,
            text_columns=(0, 1),
        ),
    ]
    return html.Div(children)


def _pair_unregistered_warning(unregistered: list[str]) -> html.Div | None:
    if not unregistered:
        return None
    return _warning_box(
        f"{len(unregistered)} subjects of the two clusters have no row in the registry (assets/metadata/participants.csv). "
        "They count in the number of subjects of each cluster, but carry no value.",
        detail=", ".join(unregistered),
    )


def _cluster_pair_regression_block(pair: PairFrame, label_1: int, label_2: int) -> html.Div:
    heading = html.H3("What distinguishes the two clusters", className="comparison-heading")
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)
    note = _points(
        f"For each variable: how much the probability of being in {name_1} rather than in {name_2} changes, all the others being equal. "
        "Only the subjects of the two clusters are used (logistic regression).",
        [
            [html.B("Variables considered"), ": age, NIHSS, lesion volume (log10), cortical share, subcortical gray share "
             "and infratentorial share, sex and dataset."],
            [html.B("Odds ratio"), f": above 1 the variable makes more likely {name_1}, below 1 {name_2}, equal to 1 it does not "
             "change anything. For numeric variables it is per one more standard deviation."],
            [html.B("Blue dot"), ": the 95% confidence interval does not contain 1, so the effect is distinguishable from “no effect”."],
            [html.B("Warning"), ": it is an association, not a cause. A variable derived from the clustering input "
             "(the volume, for a lesion run) is associated with the clusters by construction too."],
            ["Subjects with missing data in any of the variables are excluded."],
        ],
    )
    try:
        result = pair_regression(pair, label_1)
    except ValueError as exc:
        return html.Div([heading, note, html.P(str(exc), className="status-message")])

    config = {"displayModeBar": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"], "displaylogo": False}
    rows = [
        [
            regression_term_label(term), format_number(row.odds_ratio, 2),
            f"{format_number(row.ci_low, 2)} – {format_number(row.ci_high, 2)}", _format_p(row.p_value),
            format_number(row.vif, 1),
        ]
        for term, row in result.coefficients.iterrows()
    ]
    return html.Div([
        heading,
        note,
        html.P(
            f"{format_number(result.n_used, 0)} subjects used ({format_number(result.n_in_cluster, 0)} in {name_1}, "
            f"{format_number(result.n_used - result.n_in_cluster, 0)} in {name_2}; "
            f"{format_number(result.n_dropped_missing, 0)} excluded for missing data) · AUC = {format_number(result.auc, 2)} · "
            f"pseudo-R² = {format_number(result.pseudo_r2, 2)}",
            className="comparison-summary-line",
        ),
        dcc.Graph(figure=_italian_figure(build_odds_ratio_figure(result, label_1, label_2)), config=config, style={"width": "100%"}),
        _table(["Variable", "Odds\nratio", "Interval\n95%", "p", "VIF"], rows),
        _points(
            "How to read the quality measures:",
            [
                [html.B("AUC"), ": how well the variables together distinguish the two clusters. 0.5 = as by chance, 1 = perfectly. "
                 "It is computed on the same subjects as the model, so it is slightly optimistic."],
                [html.B("Pseudo-R² (McFadden)"), ": 0.2-0.4 is already a good fit."],
                [html.B("VIF"), ": how much a variable is already explained by the others. Above about 5 its odds ratio is unstable."],
            ],
        ),
    ])


def _cluster_pair_centroid_block(
    run: ProductionRun, embedding: np.ndarray, metadata: pd.DataFrame, label_1: int, label_2: int
) -> html.Div:
    heading = html.H3("Distance between centroids", className="comparison-heading")
    if run.reduction_method == "raw":
        return html.Div([
            heading,
            html.P(
                "The run is on raw data: its matrix is the feature space, not an embedding, and the centroids "
                "are not computed.",
                className="status-message",
            ),
        ])
    try:
        separation = centroid_separation(embedding, metadata, label_1, label_2)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)
    return html.Div([
        heading,
        _points(
            "How far apart the two clusters are in the space the clustering was run on.",
            [
                [html.B("Distance between centroids"), ": the straight-line distance between the centers of the two clusters."],
                [html.B("Radius"), ": the mean distance of the subjects of a cluster from its own center, i.e. how “wide” the cluster is."],
                [html.B("How to read them"), ": distance much larger than the two radii = well separated clusters; "
                 "distance similar to the radii = clusters that touch."],
            ],
        ),
        _table(
            ["Distance between\ncentroids", f"Radius\n{name_1}", f"Radius\n{name_2}"],
            [[
                html.Span(format_number(separation.distance, 2), className="stat-value"),
                format_number(separation.radius_1, 2), format_number(separation.radius_2, 2),
            ]],
        ),
    ])


def cluster_pair_content_for(run: ProductionRun, label_1: int, label_2: int) -> html.Div | html.P:
    """Mode "Dentro lo stesso clustering" of the "Confronto" section (08-10-26, on request), without
    the anatomy (cluster_pair_anatomy_for, a separate and much slower panel): the clinical profile,
    the regression and the centroid distance of two clusters of `run`.

    Same never-raises contract as every other *_content_for function here: a run that is not a
    clustering run, a cluster that is empty or the same as the other, or a registry that cannot be
    read renders an html.P status message naming the cause."""
    try:
        if run.pipeline != "clustering":
            raise ValueError(f"{run.key} is not a clustering run")
        embedding, metadata, _extra = load_matrix(run.path)
        pair = pair_frame(metadata, label_1, label_2)
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message")
    return html.Div([
        _cluster_pair_summary(run, metadata, label_1, label_2),
        _cluster_pair_clinical_block(pair, label_1, label_2),
        _cluster_pair_regression_block(pair, label_1, label_2),
        _cluster_pair_centroid_block(run, embedding, metadata, label_1, label_2),
    ])


def _pair_map_viewers(
    build: Callable[[int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]],
    label_1: int, label_2: int, what: str,
) -> list:
    """The map of each cluster and their difference, as three anatomy viewers. `build(label)` is the
    same per-cluster builder the single-cluster panels use (cached in the running app); what comes
    back is each cluster's own image, subtracted voxel by voxel. `what` names the quantity ("lesione"
    or "disconnessione"). A failure of either cluster (no subject with a file on disk) is one status
    message, never a difference built from half of it."""
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)
    try:
        view_1, n_1, image_1, missing_1 = build(label_1)
        view_2, n_2, image_2, missing_2 = build(label_2)
        difference = difference_image(image_1, image_2)
    except ValueError as exc:
        return [html.P(str(exc), className="status-message")]
    difference_view = nilearn_plotting.view_img(
        difference, bg_img="MNI152", black_bg=False, threshold=1e-6, cmap="RdBu_r", symmetric_cmap=True, title=None,
        width_view=_ANATOMY_VIEWER_WIDTH,
    )
    caption = f"Color = % of subjects in the cluster with {what} in that voxel (0-100%)"
    return [
        _anatomy_viewer(view_1, f"{_pair_name(label_1).capitalize()} (n={n_1})", caption, warning=_missing_subjects_warning(missing_1)),
        _anatomy_viewer(view_2, f"{_pair_name(label_2).capitalize()} (n={n_2})", caption, warning=_missing_subjects_warning(missing_2)),
        _anatomy_viewer(
            difference_view, f"Difference: {name_1} minus {name_2}",
            f"Red: {what} more frequent in {name_1}. Blue: more frequent in {name_2}. The intensity is the difference "
            "between the two percentages of subjects, in percentage points, voxel by voxel.",
        ),
    ]


def cluster_pair_anatomy_for(
    run: ProductionRun, label_1: int, label_2: int, lesion_cfg: LesionViewerConfig, sdc_cfg: SdcViewerConfig,
    build_overlap_view: Callable[..., tuple[StatMapView, int, nib.Nifti1Image, list[str]]] = _build_cluster_overlap_view,
    build_disconnection_view: Callable[..., tuple[StatMapView, int, nib.Nifti1Image, list[str]]] = _build_cluster_disconnection_view,
) -> html.Div | html.P:
    """The anatomy of two clusters of `run` (08-10-26, on request): the lesion overlap map of each and
    their difference and, for an sdc run, the same three for the disconnection (percent mode, so the
    difference is in points of the same quantity as the lesion one).

    A separate panel from cluster_pair_content_for because building a cluster's map reads every one of
    its subjects' NIfTI files the first time (build_app passes cached builders, as for the
    single-cluster panels): the numbers above must not wait for it. Never raises (same contract as
    overlap_map_content_for): a failure is an html.P status message."""
    try:
        if run.pipeline != "clustering":
            raise ValueError(f"{run.key} is not a clustering run")
        metadata = run_metadata(run)
        if label_1 == label_2:
            raise ValueError(f"the two clusters are the same ({_pair_name(label_1)}): nothing to compare")
        present = set(cluster_options(metadata))
        for label in (label_1, label_2):
            if label not in present:
                raise ValueError(f"no subjects with {_CLUSTER_LABEL_COLUMN}={label!r} in this run's metadata")
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message")

    children: list = [
        html.H3("Lesion anatomy", className="comparison-heading"),
        *_pair_map_viewers(
            lambda label: build_overlap_view(run, metadata, label, lesion_cfg), label_1, label_2, "lesion"
        ),
    ]
    if run.modality == "sdc":
        children += [
            html.H3("Disconnection anatomy", className="comparison-heading"),
            *_pair_map_viewers(
                lambda label: build_disconnection_view(run, metadata, label, sdc_cfg, DISCONNECTION_PERCENT_MODE),
                label_1, label_2, "disconnection",
            ),
        ]
    return html.Div(children)


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


# --- Dendrogram and splits (21-10-26) --------------------------------------------------------

# Which map the two children of a split are drawn with: both exist for any run of this app (both viewer configs are
# always loaded), whatever modality the run itself is.
DENDROGRAM_MAP_MODALITIES = {"lesion": "Lesion", "sdc": "Disconnection"}


def tuning_root_of(run: ProductionRun) -> Path:
    """The folder holding the tuning runs of `run`'s method and modality: results/<modality>/clustering/tuning/<method>.
    Raises ValueError for a run that is not a clustering production run with a reduction segment in its path."""
    if run.pipeline != "clustering" or run.reduction_method is None:
        raise ValueError(f"{run.path} is not a clustering production run: it has no tuning to look for")
    # <results>/<modality>/clustering/production/<method>/<reduction>/<run_name>
    return run.path.parents[3] / "tuning" / run.method


def run_compatible_tunings(run: ProductionRun) -> list[TuningMatch]:
    """Every agglomerative tuning that clustered the same matrix as `run` (src.analysis.tuning_match), compatible or
    not. The `input_path`s of config.md are relative to the working directory the app is launched from. Raises
    ValueError for a run that is not agglomerative or whose params cannot be matched."""
    if run.method != "agglomerative":
        raise ValueError(f"{run.path}: the dendrogram is only defined for agglomerative runs, not {run.method!r}")
    return find_compatible_tunings(run.path, tuning_root_of(run), Path.cwd())


def build_run_split_tree(run: ProductionRun, tuning_dir: Path) -> SplitTree:
    """The tree of the matrix `run` clustered, with the labels `tuning_dir` saved for the run's (linkage, metric).
    Raises ValueError when the run's params lack them, when the matrix is not narrow enough to compute a tree on, or
    when the recomputed tree does not reproduce the tuning's labels (src.analysis.dendrogram_splits)."""
    _require_narrow_matrix(run)
    params = run_params(run)
    missing = [name for name in ("linkage", "metric") if name not in params]
    if missing:
        raise ValueError(f"{run.path}: params lack {missing}, the tree cannot be rebuilt")
    saved = saved_labels_for(load_clustering_tuning_run(tuning_dir), params["linkage"], params["metric"])
    matrix, metadata, _extra_arrays = load_matrix(run.path)
    run_labels = metadata[_CLUSTER_LABEL_COLUMN].to_numpy()
    return build_split_tree(
        matrix, params["linkage"], params["metric"], saved, run_labels, _palette_for_labels(cluster_options(metadata))
    )


def dendrogram_tuning_note(matches: list[TuningMatch]) -> html.Div:
    """Under the tuning picker: what the compatible ones are, and why each other candidate is not."""
    rejected = [match for match in matches if not match.compatible]
    children: list = []
    if not any(match.compatible for match in matches):
        children.append(
            html.P(
                "No compatible tuning: an agglomerative tuning on the same matrix is needed, with the "
                "labels saved (save_tuning_clusterings) for this run combination.",
                className="status-message",
            )
        )
    if rejected:
        children.append(html.P("Same matrix but not compatible:", className="anatomy-caption"))
        children.append(html.Ul([html.Li(f"{match.run_dir.name}: {match.reason_rejected}") for match in rejected]))
    return html.Div(children)


def dendrogram_k_options(tree: SplitTree) -> list[int]:
    """The k the tuning swept (up to the highest the palette can colour): the ones that can be picked."""
    return list(tree.saved_ks)


# build_view(run, metadata whose cluster_label is a cut of the tree, label of the cluster in that cut, modality, name of
# the cluster, map width) -> its anatomy view. The name (the leaves it holds) identifies the subjects of a cluster across
# the k, so the app caches by it: a cluster that survives several splits is built once.
DendrogramViewBuilder = Callable[
    [ProductionRun, pd.DataFrame, int, str, str, int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]
]

_STEP_PARENT_WIDTH = 640  # native width of the map of the cluster that splits, and of the two it gives (pixels)
_STEP_CHILD_WIDTH = 495


def _color_of(members: np.ndarray, leaf_color: np.ndarray, tree: SplitTree) -> str:
    """The colour (hex) of a group of subjects that is one whole cluster of the cut `leaf_color` belongs to."""
    return tree.palette[single_label(leaf_color[tree.leaf_of_subject], members, "group colour")]


def _dendrogram_map_tile(
    run: ProductionRun, metadata: pd.DataFrame, labels: np.ndarray, label: int, name: str, title: str, color: str,
    width: int, modality: str, build_view: DendrogramViewBuilder, large: bool,
) -> html.Div | html.P:
    """The map of one cluster of the cut `labels`; a cluster that cannot be drawn shows its own status message."""
    try:
        view, n_subjects, _img, missing = build_view(
            run, metadata.assign(**{_CLUSTER_LABEL_COLUMN: labels}), label, modality, name, width
        )
    except ValueError as exc:
        return html.P(f"{name}: {exc}", className="status-message")
    return _map_tile(view, f"{title} (n={n_subjects})", color, large=large, warning=_missing_subjects_warning(missing))


@dataclass(frozen=True)
class DendrogramStep:
    """What one screen of the walk down the tree shows. `parent` is the cluster that splits (as it was at k-1, labelled
    `parent_label` in the cut `parent_labels`) and `children` the two it gives; on the first screen there are no children
    and `parent` is the cluster that will split next. `leaf_color` are the colours of the leaves at `k`,
    `previous_leaf_color` those at k-1 (None on the first screen), `highlighted` the labels of the cut at k whose names
    are drawn bigger in the embedding."""

    head: str
    k: int
    leaf_color: np.ndarray
    previous_leaf_color: np.ndarray | None
    highlighted: set[int]
    note: str
    parent: dict
    parent_title: str
    parent_labels: np.ndarray
    parent_label: int
    children: list[dict]
    first: bool


def _subject_ids_of(metadata: pd.DataFrame, rows: np.ndarray) -> np.ndarray:
    """The subject ids of the given rows of a run's metadata (the rows of its matrix, which the tree's members index)."""
    return metadata["subject_id"].to_numpy()[rows]


def dendrogram_step_content_for(
    run: ProductionRun, metadata: pd.DataFrame, registry: pd.DataFrame, tree: SplitTree, embedding: np.ndarray,
    step: DendrogramStep, modality: str, build_view: DendrogramViewBuilder,
) -> html.Div:
    """One screen of the walk down the tree. On the left the tree and the embedding at `step.k`; on the right the map of
    the parent, under it the maps of its children side by side, under them a table describing those groups. Never
    raises into the callback: an embedding that cannot be drawn (not 2D) shows a status message in place of its figure,
    a cluster that cannot be mapped one in place of its map."""
    parent = step.parent
    try:
        embedding_figure: dcc.Graph | html.P = _static_graph(
            build_step_embedding_figure(
                embedding, tree.labels_by_k[step.k], step.leaf_color, tree.palette, tree.leaf_of_subject, step.highlighted,
                step.note
            )
        )
    except ValueError as exc:
        embedding_figure = html.P(str(exc), className="status-message")
    parent_color = _color_of(parent["members"], step.leaf_color if step.previous_leaf_color is None else step.previous_leaf_color, tree)
    groups = [(f"{step.parent_title} {parent['name']}", parent_color, parent["members"])]
    rows = [html.Div(
        _dendrogram_map_tile(
            run, metadata, step.parent_labels, step.parent_label, parent["name"], f"{step.parent_title}: {parent['name']}",
            parent_color, _STEP_PARENT_WIDTH, modality, build_view, large=True,
        ),
        className="dendrogram-step-row",
    )]
    if step.children:
        child_colors = [_color_of(child["members"], step.leaf_color, tree) for child in step.children]
        rows.append(html.Div(
            [
                _dendrogram_map_tile(
                    run, metadata, tree.labels_by_k[step.k], child["label"], child["name"], f"New: {child['name']}", color,
                    _STEP_CHILD_WIDTH, modality, build_view, large=True,
                )
                for child, color in zip(step.children, child_colors)
            ],
            className="dendrogram-step-row",
        ))
        groups += [(f"New {child['name']}", color, child["members"]) for child, color in zip(step.children, child_colors)]
    entries = [(name, color, group_stats(0, _subject_ids_of(metadata, members), registry), False) for name, color, members in groups]
    return html.Div(
        className="dendrogram-step first" if step.first else "dendrogram-step",
        children=[
            html.H3(step.head, className="dendrogram-step-title"),
            html.Div(
                className="dendrogram-step-body",
                children=[
                    html.Div([_static_graph(build_tree_figure(tree.Z, tree.layout, tree.members, step.leaf_color, tree.palette, step.k)), embedding_figure]),
                    html.Div(rows, className="dendrogram-step-maps"),
                ],
            ),
            html.Div(_stats_table(entries), className="stats-table-wrap dendrogram-step-table"),
        ],
    )


def dendrogram_steps_content_for(
    run: ProductionRun, metadata: pd.DataFrame, tree: SplitTree, embedding: np.ndarray, k: int, modality: str,
    build_view: DendrogramViewBuilder, registry: pd.DataFrame,
) -> html.Div | html.P:
    """The walk down the tree, from the tuning's smallest k to `k`, one screen each. The first shows that k's
    embedding and the one cluster that splits next; every later one shows the embedding with the split already done, the
    cluster that split (as it was at k-1) and the two it gave, with a table describing the three. `metadata` is the run's
    own: the labels the clusters are looked up by are the tree's cut at each k, not the run's `cluster_label`.
    `registry` is the participants registry indexed by subject_id. Raises ValueError for an unknown modality."""
    if modality not in DENDROGRAM_MAP_MODALITIES:
        raise ValueError(f"unknown map modality {modality!r} - known: {sorted(DENDROGRAM_MAP_MODALITIES)}")
    options = dendrogram_k_options(tree)
    if k not in options:
        return html.P(f"k={k} is not among those of the tuning (from {options[0]} to {options[-1]})", className="status-message")
    k0 = options[0]
    last = min(max(k, k0 + 1), tree.k_max)
    steps = {step_k: (colors, split) for step_k, colors, split in replay_splits(tree.Z, tree.labels_by_k, tree.leaf_of_subject, len(tree.members), last)}

    colors0, _ = steps[k0]
    if k0 + 1 in steps:
        following = steps[k0 + 1][1]["parent"]
        label = single_label(tree.labels_by_k[k0], following["members"], "parent")
        first = dendrogram_step_content_for(
            run, metadata, registry, tree, embedding,
            DendrogramStep(
                head=f"k={k0}: {k0} clusters. The next one to split is {following['name']} (n={following['n']})", k=k0,
                leaf_color=colors0, previous_leaf_color=None, highlighted={label}, note="in bold the one that will split",
                parent=following, parent_title="Will split", parent_labels=tree.labels_by_k[k0], parent_label=label,
                children=[], first=True,
            ),
            modality, build_view,
        )
    else:
        first = html.P(f"k={k0}: {k0} clusters, no further split in the tuning", className="status-message")
    screens = [first]

    for step_k in range(k0 + 1, k + 1):
        colors, split = steps[step_k]
        parent, (child_a, child_b) = split["parent"], split["children"]
        head = (
            f"k={step_k}: {parent['name']} (n={parent['n']}) split into {child_a['name']} (n={child_a['n']}) and "
            f"{child_b['name']} (n={child_b['n']}), merge distance {format_number(split['distance'], 1)}"
        )
        parent_label = single_label(tree.labels_by_k[step_k - 1], parent["members"], "parent")
        screens.append(dendrogram_step_content_for(
            run, metadata, registry, tree, embedding,
            DendrogramStep(
                head=head, k=step_k, leaf_color=colors, previous_leaf_color=steps[step_k - 1][0],
                highlighted={child_a["label"], child_b["label"]}, note="in bold the two born from the split",
                parent=parent, parent_title="Was", parent_labels=tree.labels_by_k[step_k - 1], parent_label=parent_label,
                children=[child_a, child_b], first=False,
            ),
            modality, build_view,
        ))
    return html.Div(screens, className="dendrogram-steps wide-block")


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


_LESION_PLACEHOLDER = html.P("Click a point in the embedding to see the lesion.", className="status-message")
_DISCONNECTOME_PLACEHOLDER = html.P(
    "Click a point in the embedding to see the disconnectome.", className="status-message"
)


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
