"""The brain maps: one subject's lesion or disconnectome, and the map of a whole cluster.

Resolves a subject's image off disk, puts it on the panel's own grid and renders it either as
an interactive nilearn viewer or as a static PNG to download. The two configs at the top are
built once at startup from the same build_lesion_matrix.json/build_sdc_matrix.json the matrix
pipelines read, never re-parsed by hand here.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import nibabel as nib
import numpy as np
import pandas as pd
from dash import Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate
from nilearn import plotting as nilearn_plotting
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.anatomical_maps import resolve_lesion_paths
from src.analysis.embedding_app.blocks import _warning_box
from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import ProductionRun, run_metadata
from src.analysis.embedding_app.style import _FONT_STACK, _TEXT_COLOR

if TYPE_CHECKING:  # importing it for real would close the loop context -> this module
    from src.analysis.embedding_app.context import AppContext


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
    bg_img/threshold/cmap/colorbar choices (see _build_subject_lesion_view here, and
    panels/cluster_maps.py's _build_cluster_overlap_view for the per-cluster one) rather than an
    independently-styled second rendering.
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


# What each anatomy panel shows before a point has been clicked: the panels exist from the
# first render (their callbacks fill them in place), so they need something to say meanwhile.
_LESION_PLACEHOLDER = html.P("Click a point in the embedding to see the lesion.", className="status-message")
_DISCONNECTOME_PLACEHOLDER = html.P(
    "Click a point in the embedding to see the disconnectome.", className="status-message"
)


def register_callbacks(app: Dash, context: AppContext) -> None:
    """Wires this panel to the app. Called once by build_app, which owns the layout the ids
    below refer to."""
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
        run = context.runs_by_key[run_key]
        return lesion_viewer_content_for(run, subject_id, run_metadata(run), context.lesion_cfg), subject_id

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
        run = context.runs_by_key[run_key]
        try:
            view, _dataset = _build_subject_lesion_view(run, subject_id, run_metadata(run), context.lesion_cfg)
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
        run = context.runs_by_key[run_key]
        try:
            # Resolves the subject's real lesion mask path directly - no need to build the
            # interactive view_img (_build_subject_lesion_view) just to render a static PNG.
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, context.lesion_cfg.data_root, context.lesion_cfg.lesion_glob)
        except ValueError:
            # Same never-raises-into-the-callback contract as _download_lesion_html: the visible
            # panel already reports this, the save button simply has nothing to offer.
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            str(lesion_paths[subject_id]), threshold=context.lesion_cfg.binarize_threshold, cmap="autumn", colorbar=False,
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
        run = context.runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, context.lesion_cfg.data_root, context.lesion_cfg.lesion_glob)
        except ValueError:
            # Same never-raises-into-the-callback contract as _download_lesion_png.
            raise PreventUpdate
        # cmap="autumn" - same choice as _build_subject_lesion_view's own ortho view (see its
        # docstring): a binary mask has no gradient to show, autumn's solid bright yellow reads
        # clearly on both the ortho and this glass-brain projection.
        png_bytes = _static_glass_brain_png_bytes(
            str(lesion_paths[subject_id]), threshold=context.lesion_cfg.binarize_threshold, cmap="autumn", colorbar=False,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_lesion_glass.png")

    @app.callback(
        Output("disconnectome-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_disconnectome_panel_visibility(run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        return {} if context.runs_by_key[run_key].modality == "sdc" else {"display": "none"}

    @app.callback(
        Output("disconnectome-viewer-content", "children"),
        Output("disconnectome-viewer-subject", "data"),
        Input("embedding-graph", "clickData"),
        Input("run-picker", "value"),
    )
    def _update_disconnectome_viewer(click_data: dict | None, run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        # Same run-change reset as _update_lesion_viewer, plus a modality gate: a "lesion" run's
        # subjects don't have a disconnectome-map.nii.gz to resolve at all (this panel stays
        # hidden for them via _update_disconnectome_panel_visibility, but its own content must
        # still reset rather than linger/attempt a doomed resolution on every click).
        if run.modality != "sdc" or ctx.triggered_id == "run-picker" or click_data is None:
            return _DISCONNECTOME_PLACEHOLDER, None
        subject_id = click_data["points"][0].get("text")
        if subject_id is None:
            raise PreventUpdate
        return disconnectome_viewer_content_for(run, subject_id, run_metadata(run), context.sdc_cfg), subject_id

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
        run = context.runs_by_key[run_key]
        try:
            view, _dataset = _build_subject_disconnectome_view(run, subject_id, run_metadata(run), context.sdc_cfg)
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
        run = context.runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            disconnectome_paths = resolve_lesion_paths(
                [subject_id], {subject_id: dataset}, context.sdc_cfg.data_root, context.sdc_cfg.disconnectome_glob
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
        run = context.runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            disconnectome_paths = resolve_lesion_paths(
                [subject_id], {subject_id: dataset}, context.sdc_cfg.data_root, context.sdc_cfg.disconnectome_glob
            )
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_glass_brain_png_bytes(
            str(disconnectome_paths[subject_id]), threshold=_DISCONNECTOME_GLASS_BRAIN_THRESHOLD, cmap="magma",
            colorbar=True, alpha=_DISCONNECTOME_GLASS_BRAIN_ALPHA,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_disconnectome_glass.png")

def lesion_panel() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
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
    )

def disconnectome_panel() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
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
    )
