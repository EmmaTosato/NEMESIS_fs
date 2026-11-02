"""The maps of a whole cluster: its lesion overlap or its disconnection, the real subject
closest to its centroid, and every cluster of the run side by side.

A layer above anatomy.py, which draws one subject or builds one map: these callbacks decide
which cluster is asked for, read it through the app's memos, and hand the result to the panel
that shows it or to the button that saves it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import nibabel as nib
import numpy as np
import pandas as pd
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html
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
from src.analysis.embedding_app.anatomy import (
    DEFAULT_DISCONNECTION_MAP_MODE,
    DISCONNECTION_MAP_MODE_LABELS,
    DISCONNECTION_PERCENT_MODE,
    DISCONNECTION_PROBABILITY_THRESHOLD,
    _ANATOMY_VIEWER_WIDTH,
    _DISCONNECTOME_CMAP,
    _DISCONNECTOME_DISPLAY_THRESHOLD,
    LesionViewerConfig,
    SdcViewerConfig,
    _anatomy_viewer,
    _build_subject_disconnectome_view,
    _build_subject_lesion_view,
    _map_texts,
    _masked_for_view_colorbar,
    _resolve_subject_dataset,
    _static_png_bytes,
    _style_nilearn_html,
)
from src.analysis.embedding_app.blocks import _missing_subjects_warning
from src.analysis.embedding_app.embedding_view import cluster_centroids_with_nearest_subject
from src.analysis.embedding_app.panels.overview import ALL_CLUSTERS, all_clusters_content_for
from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import UndisplayableRunError, load_cluster_space, load_run, run_metadata
from src.analysis.embedding_app.tabs import TAB_CLUSTERING, tab_is_active
from src.analysis.embedding_coloring import COLOR_MODES
from src.utils.number_format import format_number

if TYPE_CHECKING:  # importing it for real would close the loop context -> anatomy -> this module
    from src.analysis.embedding_app.context import AppContext


def register_callbacks(app: Dash, context: AppContext) -> None:
    """Wires the per-cluster panels to the app. Called once by build_app, which owns the layout
    the ids below refer to."""
    @app.callback(
        Output("cluster-map-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_cluster_map(run_key: str | None, cluster_label: int | str | None, selected_tab: str | None):
        if run_key in (None, UNSET) or cluster_label is None:
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        if cluster_label == ALL_CLUSTERS:
            embedding, embedding_message = context.embedding(run)
            return all_clusters_content_for(
                run, run_metadata(run), embedding, embedding_message, "lesion", DEFAULT_DISCONNECTION_MAP_MODE,
                lambda run_, metadata, label, width: context.cluster_overlap_view(run_, metadata, label, context.lesion_cfg, width_view=width),
            )
        return overlap_map_content_for(run, run_metadata(run), cluster_label, context.lesion_cfg, build_view=context.cluster_overlap_view)

    @app.callback(
        Output("representative-subject-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_representative_subject(run_key: str | None, cluster_label: int | str | None, selected_tab: str | None):
        if run_key in (None, UNSET) or cluster_label is None:
            raise PreventUpdate
        run = context.runs_by_key[run_key]
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
        if key not in context.representatives:
            content = representative_subject_content_for(run, embedding, metadata, cluster_label, context.lesion_cfg, context.sdc_cfg)
            if not isinstance(content, html.P):  # a status message (a missing file...) is not remembered: it may be fixed
                context.representatives[key] = content
            return content
        return context.representatives[key]

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
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            embedding, metadata = load_run(run)
            centroids = cluster_centroids_with_nearest_subject(embedding, metadata, load_cluster_space(run))
            subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
            if run.modality == "lesion":
                view, _dataset = _build_subject_lesion_view(run, subject_id, metadata, context.lesion_cfg)
            else:
                view, _dataset = _build_subject_disconnectome_view(run, subject_id, metadata, context.sdc_cfg)
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
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            embedding, metadata = load_run(run)
            centroids = cluster_centroids_with_nearest_subject(embedding, metadata, load_cluster_space(run))
            subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
            dataset = _resolve_subject_dataset(metadata, subject_id)
            if run.modality == "lesion":
                lesion_paths = resolve_lesion_paths(
                    [subject_id], {subject_id: dataset}, context.lesion_cfg.data_root, context.lesion_cfg.lesion_glob
                )
                png_bytes = _static_png_bytes(
                    str(lesion_paths[subject_id]), threshold=context.lesion_cfg.binarize_threshold, cmap="autumn",
                    colorbar=False,
                )
            else:
                disconnectome_paths = resolve_lesion_paths(
                    [subject_id], {subject_id: dataset}, context.sdc_cfg.data_root, context.sdc_cfg.disconnectome_glob
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
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            view, _n_subjects, _percentage_img, _missing = context.cluster_overlap_view(run, run_metadata(run), cluster_label, context.lesion_cfg)
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
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            # Reuses the same process-lifetime cache the HTML download/panel display already
            # populate - percentage_img is the exact image the interactive view itself renders,
            # not a second build_overlap_map pass (see _build_cluster_overlap_view's docstring).
            _view, _n_subjects, percentage_img, _missing = context.cluster_overlap_view(run, run_metadata(run), cluster_label, context.lesion_cfg)
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
        run = context.runs_by_key[run_key]
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
        run = context.runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return []
        if cluster_label == ALL_CLUSTERS:
            embedding, embedding_message = context.embedding(run)
            return all_clusters_content_for(
                run, run_metadata(run), embedding, embedding_message, "sdc", map_mode,
                lambda run_, metadata, label, width: context.cluster_disconnection_view(
                    run_, metadata, label, context.sdc_cfg, map_mode, width_view=width
                ),
            )
        return disconnection_map_content_for(
            run, run_metadata(run), cluster_label, context.sdc_cfg,
            build_view=context.cluster_disconnection_view, map_mode=map_mode,
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
        run = context.runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        try:
            view, _n_subjects, _mean_img, _missing = context.cluster_disconnection_view(run, run_metadata(run), cluster_label, context.sdc_cfg)
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
        run = context.runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        try:
            # Reuses the same process-lifetime cache the HTML download/panel display already
            # populate - mean_img is the exact image the interactive view itself renders, not a
            # second build_mean_map pass (see _build_cluster_disconnection_view's docstring).
            _view, _n_subjects, mean_img, _missing = context.cluster_disconnection_view(run, run_metadata(run), cluster_label, context.sdc_cfg)
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            mean_img, threshold=_DISCONNECTOME_DISPLAY_THRESHOLD, cmap=_DISCONNECTOME_CMAP, colorbar=True,
        )
        return dcc.send_bytes(png_bytes, filename=f"cluster_{cluster_label}_disconnection_mean_map.png")

def overlap_map_panel() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
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
    )

def disconnection_map_panel() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
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
    )

def representative_panel() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
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
    )


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
