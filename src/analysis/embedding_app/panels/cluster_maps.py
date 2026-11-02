"""The maps of a whole cluster: its lesion overlap or its disconnection, the real subject
closest to its centroid, and every cluster of the run side by side.

A layer above anatomy.py, which draws one subject or builds one map: these callbacks decide
which cluster is asked for, read it through the app's memos, and hand the result to the panel
that shows it or to the button that saves it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate

from src.analysis.anatomical_maps import resolve_lesion_paths
from src.analysis.embedding_app.anatomy import (
    DEFAULT_DISCONNECTION_MAP_MODE,
    _DISCONNECTOME_CMAP,
    _DISCONNECTOME_DISPLAY_THRESHOLD,
    _build_subject_disconnectome_view,
    _build_subject_lesion_view,
    _resolve_subject_dataset,
    _static_png_bytes,
    _style_nilearn_html,
    disconnection_map_content_for,
    overlap_map_content_for,
    representative_subject_content_for,
)
from src.analysis.embedding_app.embedding_view import cluster_centroids_with_nearest_subject
from src.analysis.embedding_app.panels.overview import ALL_CLUSTERS, all_clusters_content_for
from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import UndisplayableRunError, load_cluster_space, load_run, run_metadata
from src.analysis.embedding_app.tabs import TAB_CLUSTERING, tab_is_active

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
