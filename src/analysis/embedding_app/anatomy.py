"""The brain maps: one subject's lesion or disconnectome, and the map of a whole cluster.

Resolves a subject's image off disk, puts it on the panel's own grid and renders it either as
an interactive nilearn viewer or as a static PNG to download. The two configs at the top are
built once at startup from the same build_lesion_matrix.json/build_sdc_matrix.json the matrix
pipelines read, never re-parsed by hand here.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from dash import html
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
from src.analysis.embedding_app.blocks import _missing_subjects_warning, _warning_box
from src.analysis.embedding_app.embedding_view import cluster_centroids_with_nearest_subject
from src.analysis.embedding_app.runs import ProductionRun, load_cluster_space
from src.analysis.embedding_app.style import _FONT_STACK, _TEXT_COLOR
from src.analysis.embedding_coloring import COLOR_MODES
from src.utils.number_format import format_number


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
