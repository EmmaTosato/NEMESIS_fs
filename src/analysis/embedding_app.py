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
scripts/replot_dim_reduction.py already established, extended here to cover 3-component runs
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

import itertools
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate
from nilearn import plotting as nilearn_plotting
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.anatomical_maps import build_overlap_map, resolve_lesion_paths
from src.analysis.embedding_coloring import COLOR_MODES
from src.analysis.embedding_coloring import color_values as read_color_values
from src.analysis.params import load_tag_params
from src.analysis.plotting import _CATEGORICAL_PALETTE, _NOISE_COLOR, compose_embedding_plot_title
from src.utils.artifacts import MANIFEST_FILENAME, load_matrix, read_run_config, read_run_params

# "neutro" first, same convention as embedding_coloring.COLOR_MODES/the notebook prototype -
# the neutral single-color view is always available and always the default, every other
# entry is a registered color_by mode name.
NEUTRAL_MODE = "neutro"
COLOR_MODE_ORDER: tuple[str, ...] = (NEUTRAL_MODE, *COLOR_MODES.keys())

# Same measured design tokens as src/analysis/understanding_umap_report.py's own _CSS
# (PAIR-style editorial report, 13/14-08-26 sessions) - not imported directly (that module's
# _CSS is private and tightly coupled to its own grid/slider DOM, none of which this app has),
# but deliberately the same values, so the two Dash tools in this repo read as one visual
# family instead of two unrelated ones. _TEXT_COLOR = PAIR's own measured text color
# (getComputedStyle on the live page = rgb(51,51,51)), font stack = system-ui/-apple-system
# stack PAIR uses, _GRID_BORDER = PAIR's own .demo-data cell border.
_TEXT_COLOR = "#333"
_GRID_BORDER = "rgba(0,0,0,0.1)"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)

# Injected into the Dash app's index_string (src.pipeline.embedding_app.build_app) - ample
# whitespace, no boxy borders/sidebars, a curated button-group instead of a framework dropdown
# for color_by, Plotly's own modebar hidden by the figure config (not CSS) since Dash renders
# it in an iframe-like shadow context CSS can't reach. See the design brief this was built
# against (14-08-26, user-supplied "Senior Frontend/UI-UX" prompt referencing
# pair-code.github.io/understanding-umap as the benchmark) - minimalism, differentiated H1/H2,
# transparent plot background, curated palette, no default-Streamlit/default-Plotly look.
CSS = f"""
body {{ font-family: {_FONT_STACK}; margin: 0; background: #fff; color: {_TEXT_COLOR}; }}
.page {{ max-width: 1100px; margin: 0 auto; padding: 48px 32px 96px; }}
.page-title {{ font-size: 32px; font-weight: 800; text-align: center; margin: 0 0 12px; }}
/* 01-09-26 feedback: the descriptive/status texts across the app (this subtitle, .status-message,
   .anatomy-caption) read "troppo chiaro e scritto in piccolo" - all 3 bumped in size and to a
   darker gray, still clearly secondary to any heading (kept well under .section-heading/
   .anatomy-subject-title's own sizes) but no longer near-illegible. */
.page-subtitle {{ font-size: 18px; color: #595959; text-align: center; margin: 0 0 56px; }}
.controls {{ display: flex; flex-direction: column; align-items: center; gap: 24px; margin-bottom: 32px; }}
/* One field per selection step (Dato -> Pipeline -> Metodo -> Metrica -> Componenti -> Run),
   left-to-right in reading/decision order (2026-08, extended 15-08-26 when Pipeline became a
   real dropdown, not a fixed label) - wraps to multiple rows on a narrow viewport instead of
   overflowing horizontally. */
.picker-row {{ display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-end; gap: 20px; }}
.picker-field {{ display: flex; flex-direction: column; gap: 6px; min-width: 200px; }}
.picker-label {{ font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #767676; }}
.color-buttons {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }}
.color-buttons button {{
    font-family: inherit; font-size: 13px; padding: 7px 16px; cursor: pointer;
    border: 1px solid #ccc; border-radius: 999px; background: #fff; color: {_TEXT_COLOR};
    transition: border-color 0.15s, background 0.15s;
}}
.color-buttons button:hover {{ border-color: #4a90d9; }}
.color-buttons button.active {{ border-color: #4a90d9; border-width: 2px; background: #f0f7fd; font-weight: 600; }}
/* width:100% + no Plotly config.responsive (see graph_content_for) - a stable CSS width set
   once at mount, not a JS ResizeObserver reacting to every later layout event (scrolling
   included) - that combination was the actual cause of the graph distorting on scroll. */
.graph-wrap {{ display: flex; justify-content: center; width: 100%; }}
.graph-wrap > div {{ width: 100%; }}
.status-message {{ text-align: center; color: #595959; font-size: 17px; margin: 64px 0; }}
/* Shared by all 3 section headings (Embedding Visualization / Anatomia lesionale / Overlap map
   per cluster, 01-09-26) - a class of its own rather than a nesting-based ".anatomy-panel h2"
   selector, since "Embedding Visualization" sits above the scatter, outside any .anatomy-panel.
   Same weight/scale family as .page-title (32px) - a real section header, not the 20px
   subheading this panel used to read as (feedback: "va scritto più grande" / "un pelo più
   grande" on a follow-up pass). */
.section-heading {{ font-size: 30px; font-weight: 800; margin: 40px 0 20px; text-align: center; }}
/* Anatomy panels (lesion viewer / cluster overlap map, 01-09-26) - same page-width container as
   .page itself (not .graph-wrap's centered flex, these are full-width blocks with their own
   heading), separated from the picker/scatter above by a thin rule instead of a boxy border. */
.anatomy-panel {{ margin-top: 56px; padding-top: 32px; border-top: 1px solid {_GRID_BORDER}; }}
/* A further bump over .section-heading's own 30px (01-09-26, follow-up feedback: "un po' più
   grandi") - kept scoped to the two anatomy panels, not "Embedding Visualization" above, since
   only these two were called out this time. */
.anatomy-panel .section-heading {{ margin-top: 0; font-size: 34px; }}
.anatomy-controls {{ display: flex; flex-wrap: wrap; align-items: flex-end; gap: 20px; margin-bottom: 20px; }}
/* The subject/cluster heading and its color-legend caption are ordinary HTML we render
   ourselves (01-09-26) - nilearn's own `title`/colorbar labels are drawn straight onto a
   <canvas> with no width check or line-wrapping, silently overflowing past the panel edge for
   anything longer than a few characters (see lesion_viewer_content_for's docstring). Rendering
   them here instead means they're never truncated and take this page's own font, not the
   browser's plain default the embedded nilearn page has no styling for at all. */
.anatomy-subject-title {{ font-size: 18px; font-weight: 600; margin: 0 0 4px; text-align: center; }}
.anatomy-caption {{ font-size: 15px; color: #595959; text-align: center; margin: 0 0 16px; }}
.anatomy-viewer-wrap {{ display: flex; justify-content: center; }}
.anatomy-viewer-wrap iframe {{ border: none; }}
/* Same pill shape as .color-buttons button - one save action per panel reads as the same
   family of control, not a second, differently-styled button style. */
.save-btn {{
    display: block; font-family: inherit; font-size: 13px; padding: 7px 16px; cursor: pointer;
    border: 1px solid #ccc; border-radius: 999px; background: #fff; color: {_TEXT_COLOR};
    transition: border-color 0.15s, background 0.15s; margin: 16px auto 0;
}}
.save-btn:hover {{ border-color: #4a90d9; }}
"""


# The 2 production pipelines this app knows how to discover/display, in preference order
# (used only to pick a sensible default in the "Pipeline" picker - dim_reduction is the more
# mature, more commonly explored pipeline, see README.md's "what's implemented so far" - not
# an alphabetical accident like every other *_options helper below, so kept as its own
# explicitly ordered constant rather than a set).
PRODUCTION_PIPELINES: tuple[str, ...] = ("dim_reduction", "clustering")


@dataclass(frozen=True)
class ProductionRun:
    """One production run discovered under results/<modality>/<pipeline>/production/<method>/
    [<reduction_method>/]<run_name> (pipeline is "dim_reduction" or "clustering", see
    PRODUCTION_PIPELINES) - path is the absolute run directory (what load_matrix needs), the
    rest are its own path segments (what the UI and compose_embedding_plot_title need), kept
    apart rather than re-parsed from path every time.

    reduction_method is None for a dim_reduction.py run (no such segment exists in its path -
    method there already *is* the reduction method) and a real value (e.g. "umap", or "raw" for
    clustering directly on an un-reduced matrix) for a clustering.py run (31-08-26,
    src.analysis.model_config.ClusteringConfig.reduction_method) - the extra segment exists so
    clustering results from different source embeddings never land in the same folder.
    """

    modality: str
    pipeline: str
    method: str
    run_name: str
    path: Path
    reduction_method: str | None = None

    @property
    def key(self) -> str:
        """Stable, unique-per-run string - used as a Dash dropdown option value (Dash
        options need a hashable, JSON-serializable value, not a Path)."""
        parts = [self.modality, self.pipeline, self.method]
        if self.reduction_method is not None:
            parts.append(self.reduction_method)
        parts.append(self.run_name)
        return "/".join(parts)

    @property
    def results_relative_path(self) -> Path:
        """<modality>/<pipeline>/production/<method>/[<reduction_method>/]<run_name>, prefixed
        with "results" - compose_embedding_plot_title (src/analysis/plotting.py) derives the
        modality from an output_dir's own path segments and expects a "results/..."-relative
        Path, not an absolute one (an absolute path's first segment is "/", not "results" - see
        notebooks/post-results_analysis's own fix for the identical issue, 13-08-26)."""
        base = Path("results") / self.modality / self.pipeline / "production" / self.method
        if self.reduction_method is not None:
            base = base / self.reduction_method
        return base / self.run_name


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


def discover_production_runs(results_root: Path) -> list[ProductionRun]:
    """Scans results_root/*/<pipeline>/production/*/* (dim_reduction) or
    results_root/*/<pipeline>/production/*/*/* (clustering, one extra <reduction_method>
    segment - 31-08-26) for valid run directories (must contain manifest.json - the same
    existence check src.utils.artifacts.load_matrix itself uses to decide a run was actually
    completed, not left behind by an interrupted build), across every pipeline in
    PRODUCTION_PIPELINES.

    Generic across modality/method on purpose (2026-08-14, on request: "Tutti, generico") -
    today only lesion/umap (plus lesion/pca, lesion/tsne, lesion/pacmap, lesion/clustering's
    various methods) exist, but a future modality (e.g. sdc) or method needs zero changes here
    to show up, since nothing about the path shape is hardcoded beyond <pipeline>/production's
    own fixed segments. `clustering.py`'s old "comparison" pseudo-method directory (its own
    generation removed 01-09-26, docs/dev/models.md - existing ones from before that date can
    still sit on disk) is naturally excluded here without any special-casing: it only ever held
    a config.md, never a manifest.json, so it fails the same existence check every other
    incomplete/non-run directory does.

    Returns an empty list if results_root doesn't exist or has no matching runs at all - not
    an error: a completely fresh checkout with no pipeline ever run is a legitimate starting
    state for this app (the caller/UI decides how to represent "nothing to show").
    Sorted by (modality, pipeline, method, reduction_method, run_name) for a deterministic
    dropdown order.
    """
    if not results_root.exists():
        return []
    runs = []
    for pipeline in PRODUCTION_PIPELINES:
        glob_pattern = f"*/{pipeline}/production/*/*/*" if pipeline == "clustering" else f"*/{pipeline}/production/*/*"
        for path in results_root.glob(glob_pattern):
            if not (path.is_dir() and (path / MANIFEST_FILENAME).exists()):
                continue
            # relative_to(results_root)'s own parts, not raw negative indices into the
            # absolute path - self-documenting and correct regardless of how deep
            # results_root's own absolute path happens to be.
            parts = path.relative_to(results_root).parts
            if pipeline == "clustering":
                modality, _pipeline_segment, _production, method, reduction_method, run_name = parts
            else:
                modality, _pipeline_segment, _production, method, run_name = parts
                reduction_method = None
            runs.append(
                ProductionRun(
                    modality=modality, pipeline=pipeline, method=method, reduction_method=reduction_method, run_name=run_name, path=path
                )
            )
    return sorted(runs, key=lambda run: (run.modality, run.pipeline, run.method, run.reduction_method or "", run.run_name))


# A run_name's own leading "DD-MM" (every run seen so far: "13-08_s1.1-vol_m_dice_nc3",
# "23-07_s1.1-vol_c150", ...) - used only to order/default the "Giorno" picker chronologically
# (most recent last), never to validate or reject a run_name that doesn't match: a run
# without a recognizable date prefix still shows up, just sorted alphabetically after every
# dated one instead of crashing the picker over a display-order nicety.
_DATE_PREFIX_RE = re.compile(r"^(\d{2})-(\d{2})_")


def _run_chronological_key(run: ProductionRun) -> tuple:
    match = _DATE_PREFIX_RE.match(run.run_name)
    if match is None:
        return (1, 0, 0, run.run_name)
    day, month = int(match.group(1)), int(match.group(2))
    return (0, month, day, run.run_name)


def modality_options(runs: list[ProductionRun]) -> list[str]:
    """Distinct modalities across `runs`, sorted - step 1 of the picker ("Dato"). Only
    "lesion" exists today; a future modality shows up here with zero code changes (same
    generic-discovery contract as discover_production_runs itself)."""
    return sorted({run.modality for run in runs})


def pipeline_options(runs: list[ProductionRun], modality: str) -> list[str]:
    """Distinct pipelines available for `modality` - step 2 of the picker ("Pipeline"), now a
    real choice (15-08-26) rather than the fixed "dim_reduction · produzione" label it used to
    be, since this app discovers both dim_reduction.py and clustering.py runs. Ordered by
    PRODUCTION_PIPELINES' own preference order, not alphabetically (dim_reduction first,
    matching every other *_options helper's plain `sorted()` would put clustering first
    instead - a worse default given dim_reduction is the more mature pipeline)."""
    available = {run.pipeline for run in runs if run.modality == modality}
    return [pipeline for pipeline in PRODUCTION_PIPELINES if pipeline in available]


def method_options(runs: list[ProductionRun], modality: str, pipeline: str) -> list[str]:
    """Distinct methods available for (modality, pipeline), sorted - step 3 of the picker
    ("Metodo": a dim_reduction method like umap/pca, or a clustering method like
    kmeans/hdbscan, depending on the pipeline chosen in step 2)."""
    return sorted({run.method for run in runs if run.modality == modality and run.pipeline == pipeline})


def runs_for(runs: list[ProductionRun], modality: str, pipeline: str, method: str) -> list[ProductionRun]:
    """Runs matching (modality, pipeline, method), chronologically ordered (oldest first, most
    recent last) - the base scope every later picker step (Metrica/Componenti/Run) narrows
    further. Scoped this tightly is the whole point of the multi-step picker (2026-08-14, on
    request): the original single flat dropdown mixed every method's runs together, so picking
    a run meant scanning entries that weren't even the same method."""
    return sorted(
        (run for run in runs if run.modality == modality and run.pipeline == pipeline and run.method == method),
        key=_run_chronological_key,
    )


# Sentinel for "this axis doesn't apply to this run at all" - shared across all 3 narrowing
# axes this app offers (Metrica/Componenti: PCA/PaCMAP dim_reduction runs have no 'metric' key,
# config/registry/params_reduction.json; Parametri: a clustering run built directly on
# un-reduced data, reduction_method="raw", has no upstream-embedding metric/n_components; a
# clustering method with no tag_param registered at all - none today). One shared "—" rather
# than a separate sentinel per axis, so the picker's placeholder reads identically everywhere.
NO_METRIC = "—"

# Sibling sentinel for "this run's own axis has no 'n_components' value" (see NO_METRIC) - an
# int, not a string like NO_METRIC, to keep n_components_options' return type uniform
# (list[int]) - -1 is safely distinct from any real n_components value (always >= 1).
NO_N_COMPONENTS = -1

def _n_components_option_label(n: int) -> str:
    """Dropdown label for one n_components_options() value - AUDIT_FINDINGS.md #64:
    NO_N_COMPONENTS (-1, the clustering-pipeline sentinel) gets NO_METRIC's own readable
    placeholder ("—") instead of the literal string "-1", the same treatment NO_METRIC
    already gets on the metric picker for the analogous case."""
    return NO_METRIC if n == NO_N_COMPONENTS else str(n)


def run_params(run: ProductionRun) -> dict:
    """The exact resolved params dict the run's own pipeline (dim_reduction.py or
    clustering.py) actually used - never re-derived by parsing the run_name's own free-text
    convention (e.g. "nc3"/"m_dice" is a human-chosen session-name shorthand for umap
    specifically, not a guaranteed, parseable field every method's run_name follows -
    pca/tsne/pacmap/clustering runs don't). Thin wrapper over
    src.utils.artifacts.read_run_params (single source of truth, also reused by
    clustering.py's viz_embedding_path cross-check) - see that function's docstring for the
    exact contract/error cases.
    """
    return read_run_params(run.path)


def run_metadata(run: ProductionRun) -> pd.DataFrame:
    """run's own metadata.csv (subject_id/dataset/... columns), independent of the embedding's
    own dimensionality - unlike load_run, this never raises UndisplayableRunError: the anatomy
    panels (lesion_viewer_content_for, cluster_options) only need metadata's columns, not a
    2-or-3-component embedding to plot, so a run with e.g. n_components=10 still exposes them.
    """
    _matrix, metadata, _extra_arrays = load_matrix(run.path)
    return metadata


def _run_params_or_none(run: ProductionRun) -> dict | None:
    """run_params(run), isolated per-run (HIGH #25, 2026-08 - lesson #21). The 3 picker
    helpers below each call this once per run in a comprehension - a single run with a
    corrupt/truncated config.md must not take down every other run's picker options with
    it (e.g. metric_options iterating 8 runs for one method, one has a bad config.md ->
    the whole method used to become unexplorable in the app, not just that one run).
    None on failure, logged as a warning - callers filter it out and keep going.
    """
    try:
        return run_params(run)
    except ValueError as exc:
        logging.warning("%s: cannot read resolved params, excluding this run from picker options: %s", run.path, exc)
        return None


def run_reduction_axis(run: ProductionRun) -> tuple[str, int]:
    """(metric, n_components) of the embedding actually behind this run's own points.

    For a dim_reduction.py run that's the run's own resolved params (run_params). For a
    clustering.py run that's the *upstream* embedding's own metric/n_components (config.md's
    "## Config" fenced block - reduction_metric/reduction_n_components, 31-08-26 -
    src.utils.artifacts.read_run_config - never the clustering method's own hyperparameters,
    which have no metric/n_components concept at all, see tag_param_options for those).
    01-09-26: real clustering runs are built from more than one source embedding (different
    metric/n_components), so this app must let that vary per run here too, not collapse every
    clustering run to one sentinel the way it used to.

    NO_METRIC/NO_N_COMPONENTS when a run genuinely has neither (pca/pacmap for dim_reduction; a
    clustering run built directly on raw un-reduced data - reduction_method="raw" - config.md
    then records reduction_metric/reduction_n_components as "", not a real value).
    """
    if run.pipeline == "dim_reduction":
        params = run_params(run)
        return params.get("metric", NO_METRIC), params.get("n_components", NO_N_COMPONENTS)
    config = read_run_config(run.path)
    metric = config.get("reduction_metric") or NO_METRIC
    raw_n_components = config.get("reduction_n_components") or None
    n_components = int(raw_n_components) if raw_n_components else NO_N_COMPONENTS
    return metric, n_components


def _run_reduction_axis_or_none(run: ProductionRun) -> tuple[str, int] | None:
    """run_reduction_axis(run), isolated per-run (same reasoning as _run_params_or_none) - a
    single run with a corrupt/truncated config.md must not take down every other run's picker
    options with it."""
    try:
        return run_reduction_axis(run)
    except ValueError as exc:
        logging.warning("%s: cannot read resolved reduction axis, excluding this run from picker options: %s", run.path, exc)
        return None


def _runs_for_reduction_axis(
    runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str, n_components: int
) -> list[ProductionRun]:
    """runs_for(...) further narrowed to runs whose own run_reduction_axis equals
    (metric, n_components) - the shared filter metric_options/n_components_options/
    tag_param_options/runs_matching all build on, so "which embedding is this run on" is
    computed in exactly one place. Order preserved from runs_for's own chronological sort."""
    return [
        run
        for run in runs_for(runs, modality, pipeline, method)
        if (axis := _run_reduction_axis_or_none(run)) is not None and axis == (metric, n_components)
    ]


def metric_options(runs: list[ProductionRun], modality: str, pipeline: str, method: str) -> list[str]:
    """Distinct `metric` values actually used by (modality, pipeline, method)'s own runs,
    sorted - NO_METRIC included if any of them has no metric axis at all (run_reduction_axis).
    For a clustering.py run this is the *upstream embedding's* own metric, not the clustering
    method's hyperparameters (see tag_param_options for those)."""
    values = {
        axis[0]
        for run in runs_for(runs, modality, pipeline, method)
        if (axis := _run_reduction_axis_or_none(run)) is not None
    }
    return sorted(values)


def n_components_options(runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str) -> list[int]:
    """Distinct `n_components` values among (modality, pipeline, method, metric)'s own runs
    (metric being run_reduction_axis's own upstream-embedding metric, see metric_options),
    sorted ascending - includes every value actually used, even ones this app can't display
    (e.g. 150 for the full-dimensionality PCA production run): the picker's job is to reflect
    what was actually run, not to pre-filter it down to what's displayable (graph_content_for
    already reports that clearly per-run, see UndisplayableRunError)."""
    values = {
        axis[1]
        for run in runs_for(runs, modality, pipeline, method)
        if (axis := _run_reduction_axis_or_none(run)) is not None and axis[0] == metric
    }
    return sorted(values)


def _run_tag_param_label(run: ProductionRun, tag_param: list[str]) -> str | None:
    """Human-readable "key=value, key2=value2" combination of `run`'s own values for
    `tag_param` (params_clustering.json's registered hyperparameter names for this method, in
    their own declared order) - doubles as the tag_param picker's own option value (two runs
    with the same combination share the same label by construction, no separate encode/decode
    step needed). None if `run`'s own params can't be read, or don't actually carry one of the
    registered keys (a registry/artifact mismatch - excluded, not guessed)."""
    params = _run_params_or_none(run)
    if params is None:
        return None
    try:
        values = {key: params[key] for key in tag_param}
    except KeyError as exc:
        logging.warning("%s: params missing tag_param key %s, excluding this run from picker options", run.path, exc)
        return None
    return ", ".join(f"{key}={value}" for key, value in values.items())


def tag_param_options(
    runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str, n_components: int,
    clustering_params_file: str | Path,
) -> list[str]:
    """Distinct combinations of `method`'s own registered tag_param values
    (config/registry/params_clustering.json, e.g. n_clusters+linkage for agglomerative,
    min_cluster_size+min_samples for hdbscan) actually run among (modality, pipeline, method)'s
    runs on the (metric, n_components) upstream embedding - 01-09-26, on request: a flat "Run"
    dropdown mixing every k/linkage combination together, with no way to narrow by them, was the
    exact complaint that prompted this step.

    dim_reduction pipeline runs, and any clustering method with no tag_param registered at all
    (none today - every params_clustering.json entry declares at least one), always resolve to
    exactly [NO_METRIC] (this axis's own "doesn't apply" sentinel - reused rather than a
    redundant third one, see NO_METRIC's own docstring)."""
    if pipeline != "clustering":
        return [NO_METRIC]
    tag_param = load_tag_params(clustering_params_file, method)
    if not tag_param:
        return [NO_METRIC]
    labels = {
        label
        for run in _runs_for_reduction_axis(runs, modality, pipeline, method, metric, n_components)
        if (label := _run_tag_param_label(run, tag_param)) is not None
    }
    return sorted(labels)


def runs_matching(
    runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str, n_components: int,
    tag_params_label: str, clustering_params_file: str | Path,
) -> list[ProductionRun]:
    """Runs matching (modality, pipeline, method, metric, n_components, tag_params_label)
    exactly, chronologically ordered - the final picker step ("Run"): today this is usually
    exactly one run (each combination has only ever been produced once), but stays a list rather
    than assuming that - a rerun of the same combination on a later date is a legitimate, real
    scenario this picker must keep showing both of, not silently collapse to one.

    dim_reduction pipeline runs (tag_params_label always NO_METRIC there, see tag_param_options)
    skip the tag_params_label filter entirely - it's a no-op for them, not a real narrowing."""
    candidates = _runs_for_reduction_axis(runs, modality, pipeline, method, metric, n_components)
    if pipeline != "clustering" or tag_params_label == NO_METRIC:
        return candidates
    tag_param = load_tag_params(clustering_params_file, method)
    return [run for run in candidates if _run_tag_param_label(run, tag_param) == tag_params_label]


class UndisplayableRunError(ValueError):
    """A production run's saved embedding has more than 3 columns - no viz-only projection
    was ever persisted for it (dim_reduction.py's viz_embedding is refit in-memory and used
    only to write the now-removed embedding_plot_interactive.html/PNGs at production time,
    never saved to disk on its own), and this app, like scripts/replot_dim_reduction.py, never
    reloads the original feature matrix to refit one - slicing embedding[:, :3] instead would
    be the exact mistake lessons_learned.md #16 documents (a UMAP/t-SNE/PaCMAP embedding's
    columns carry no importance ordering, so a slice is an arbitrary cut, not a summary)."""


def load_run(run: ProductionRun) -> tuple[np.ndarray, pd.DataFrame]:
    """Loads `run`'s embedding + metadata via load_matrix, raising UndisplayableRunError (not
    silently slicing) if the saved embedding has other than 2 or 3 columns."""
    embedding, metadata, _extra_arrays = load_matrix(run.path)
    n_dims = embedding.shape[1]
    if n_dims not in (2, 3):
        # AUDIT_FINDINGS.md #43/#44: this message used to always point at dim_reduction.py's
        # viz_n_components, even for a clustering.py run - clustering.py has no such config
        # field (it never reduces dimensionality itself, see docs/dev/models.md's
        # "reduced_data (declarative-only)" section) and rerunning it would leave matrix.npy's
        # dimensionality unchanged either way, so that advice would not fix anything there.
        if run.pipeline == "dim_reduction":
            fix_hint = "rerun dim_reduction.py with viz_n_components 2 or 3, or pick a different run"
        else:
            fix_hint = (
                f"{run.pipeline}.py does not reduce dimensionality itself - point its input_path at an "
                "already-2-or-3-component matrix (e.g. a dim_reduction.py production embedding), or pick a different run"
            )
        raise UndisplayableRunError(
            f"Run {run.path} has a saved embedding with {n_dims} components - this app can only display an "
            f"already-2-or-3-component embedding: {fix_hint}."
        )
    return embedding, metadata


def _color_label(mode_name: str) -> str | None:
    return None if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label


def run_title(run: ProductionRun, mode_name: str) -> str:
    """Same production-style title every other plot in this pipeline uses (e.g. "Lesions -
    Umap - dataset") - compose_embedding_plot_title is the single source of truth for this
    format, never re-derived by hand here."""
    return compose_embedding_plot_title(run.results_relative_path, run.method, _color_label(mode_name))


def _palette_for(categories: list[str], missing_label: str = "unknown") -> dict[str, str]:
    palette: dict[str, str] = {}
    colors = itertools.cycle(_CATEGORICAL_PALETTE)
    for category in categories:
        palette[category] = _NOISE_COLOR if category == missing_label else next(colors)
    return palette


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
    """
    if mode_name not in COLOR_MODE_ORDER:
        raise ValueError(f"unknown color mode {mode_name!r} - known: {list(COLOR_MODE_ORDER)}")
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

    if mode_name == NEUTRAL_MODE:
        fig.add_trace(scatter_cls(**_trace_kwargs(), mode="markers", marker=dict(color="#3aa9e0", **marker_kwargs)))
    else:
        mode = COLOR_MODES[mode_name]
        values = read_color_values(metadata, mode_name)

        if mode.kind == "categorical":
            unique_categories = sorted(pd.unique(values).tolist())
            palette = _palette_for(unique_categories)
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
                if (non_missing <= 0).any():
                    raise ValueError(
                        f"Color mode {mode_name!r} is log_scale but has non-positive values - cannot log-transform"
                    )
                color_values = np.where(is_missing, values, np.log10(values))
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
                fig.add_trace(
                    scatter_cls(
                        **_trace_kwargs(~is_missing), mode="markers", name=mode.label,
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
        margin=dict(l=10, r=10, t=70, b=10),
        height=680 if is_3d else 560,
    )
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


_INDEX_STRING = f"""<!DOCTYPE html>
<html>
<head>
{{%metas%}}
<title>NEMESIS — Embedding Explorer</title>
{{%favicon%}}
{{%css%}}
<style>{CSS}</style>
</head>
<body>
{{%app_entry%}}
<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>"""


def graph_content_for(run: ProductionRun, mode_name: str) -> html.P | dcc.Graph:
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
            zlabel=zlabel,
        )
    except ValueError as exc:
        return html.P(str(exc), className="status-message")

    # modeBarButtons (not modeBarButtonsToRemove): an explicit whitelist survives 2D<->3D
    # unchanged (Plotly's default button set differs between them - a removal-list would need
    # its own 3D variant to actually hide everything else), and "toImage" is the one save
    # affordance this app offers per plot (01-09-26, on request) - still hidden until hover
    # (Plotly's own default displayModeBar="hover"), so the minimal look from 14-08-26 holds.
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    return dcc.Graph(id="embedding-graph", figure=figure, config=config, style={"width": "100%"})


# nilearn.plotting.view_img's own default (600px) reads narrow inside this page's 1100px-wide
# .page container, next to the 34px anatomy-panel headings (01-09-26 feedback) - both anatomy
# viewers pass this explicitly instead. Height scales with it automatically (nilearn's own
# _json_view_size keeps the sagittal/coronal/axial aspect ratio, never distorted by width_view).
_ANATOMY_VIEWER_WIDTH = 900


def cluster_options(metadata: pd.DataFrame) -> list[int]:
    """Sorted distinct cluster_label values in `metadata` - only meaningful for a clustering.py
    run (dim_reduction.py runs never have this column, see ProductionRun.pipeline). HDBSCAN's
    noise label (-1) is included like any other value - the same treatment
    COLOR_MODES["cluster_label"] already gives it, never hidden."""
    column = COLOR_MODES["cluster_label"].column
    return sorted(int(value) for value in pd.unique(metadata[column]))


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


def _anatomy_viewer(view: StatMapView, heading: str, caption: str) -> html.Div:
    """Shared layout for both anatomy panels: a heading + a one-line color-legend caption, both
    ordinary HTML we render ourselves (never nilearn's own `title`/colorbar text - see
    _build_subject_lesion_view's docstring for why), above the iframe sized to the view's own
    exact pixel dimensions (view.width/height) and centered, instead of stretching a fixed-height
    iframe to the panel's full width and leaving the rest as dead space (01-09-26 feedback: the
    scatter's own .graph-wrap already established this "centered, content-sized" pattern).

    key=heading on the Iframe (01-09-26 bug fix - "se cambio il cluster non mi si cambia la
    mappa"): a browser doesn't reliably re-navigate an <iframe> just because its own `srcDoc`
    attribute value changed in place - React/Dash's default diffing patches the attribute on the
    *same* DOM node, which several browsers then leave showing their stale, already-rendered
    content. `key` forces Dash's front-end to unmount+remount the node instead of patching it in
    place whenever `heading` changes - and `heading` (a subject_id or "Cluster N (n=...)") is
    already guaranteed to change whenever the actual content does, so no separate id is needed.
    """
    return html.Div(
        [
            html.H3(heading, className="anatomy-subject-title"),
            html.P(caption, className="anatomy-caption"),
            html.Div(
                html.Iframe(
                    key=heading, srcDoc=_style_nilearn_html(view.html),
                    style={"width": f"{view.width}px", "height": f"{view.height}px"},
                ),
                className="anatomy-viewer-wrap",
            ),
        ]
    )


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
    matrix used, not an independently-chosen display threshold."""
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
    return _anatomy_viewer(view, f"{subject_id} ({dataset})", "Giallo = voxel lesionato")


def _build_cluster_overlap_view(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig
) -> tuple[StatMapView, int]:
    """Returns (view, n_subjects) - n_subjects is needed by the caller to build its own heading
    (title=None here, same reasoning as _build_subject_lesion_view). colorbar stays on (unlike
    the subject viewer): the overlap percentage is a genuinely continuous, informative value.

    Raises ValueError if cluster_label has no subjects in this run's metadata, or any of them
    can't be resolved to a lesion file (see resolve_lesion_paths/build_overlap_map). threshold
    is a near-zero epsilon (not lesion_cfg.binarize_threshold, which binarizes each individual
    subject's mask before counting - see build_overlap_map) so every voxel with any real overlap
    (>0%) is shown, not just voxels above some display-only cutoff."""
    column = COLOR_MODES["cluster_label"].column
    cluster_metadata = metadata.loc[metadata[column] == cluster_label]
    if cluster_metadata.empty:
        raise ValueError(f"no subjects with {column}={cluster_label!r} in this run's metadata")
    dataset_by_subject = dict(zip(cluster_metadata["subject_id"], cluster_metadata["dataset"]))
    lesion_paths = resolve_lesion_paths(list(dataset_by_subject), dataset_by_subject, lesion_cfg.data_root, lesion_cfg.lesion_glob)
    _count_img, percentage_img = build_overlap_map(
        lesion_paths, lesion_cfg.reference_img, lesion_cfg.binarize_threshold, lesion_cfg.resample_interpolation
    )
    view = nilearn_plotting.view_img(
        percentage_img, bg_img="MNI152", black_bg=False, threshold=1e-6, cmap="hot", symmetric_cmap=False, title=None,
        width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, len(lesion_paths)


def overlap_map_content_for(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig,
    build_view: Callable[[ProductionRun, pd.DataFrame, int, LesionViewerConfig], tuple[StatMapView, int]] = _build_cluster_overlap_view,
) -> html.Div | html.P:
    """Same never-raises contract as lesion_viewer_content_for - an empty/unresolvable cluster
    shows a status message in the panel, not a crashed callback.

    build_view defaults to the always-fresh _build_cluster_overlap_view (what every test calls
    this with) - build_app passes its own cached wrapper instead (01-09-26 perf fix: measured
    ~40ms/subject, dominating the whole panel's response time for a real several-hundred-subject
    cluster - see anatomical_maps.build_overlap_map's own docstring), so switching back to an
    already-viewed cluster in the running app is instant, without this function itself needing
    to know anything about caching."""
    try:
        view, n_subjects = build_view(run, metadata, cluster_label, lesion_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(
        view, f"Cluster {cluster_label} (n={n_subjects})",
        "Colore = % di soggetti del cluster con lesione in quel voxel (0-100%)",
    )


def _color_button_label(mode_name: str) -> str:
    # Raw mode.label, not .capitalize()'d - "NIHSS (severity)".capitalize() would produce
    # "Nihss (severity)" (str.capitalize lowercases every character but the first), the same
    # trap the notebook prototype's _panel_title left uncorrected; sidestepped here by not
    # reformatting the label's casing at all, same as compose_embedding_plot_title's own
    
    return "neutro" if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label


_LESION_PLACEHOLDER = html.P("Clicca un punto nell'embedding per vedere la lesione.", className="status-message")


def build_app(runs: list[ProductionRun], lesion_cfg: LesionViewerConfig, clustering_params_file: str | Path) -> Dash:
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
    (cluster_view_cache/_cached_cluster_overlap_view below, 01-09-26 perf fix).

    suppress_callback_exceptions=True (01-09-26): the anatomy panels' own callbacks reference
    component ids ("embedding-graph") that only exist once graph_content_for actually renders a
    Graph into graph-area's children - never part of the static app.layout tree itself - the
    standard Dash idiom for wiring a callback to a dynamically-created component.

    clustering_params_file (01-09-26): config/registry/params_clustering.json (or an equivalent
    test fixture) - the picker's own "Parametri" step (tag_param_options/runs_matching) reads
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
    default_modality = modality_options(runs)[0]

    # Cluster-overlap-map cache (01-09-26 perf fix) - process-lifetime, in-memory, scoped to
    # this one app instance (a plain closure variable, not a module-level global -
    # code_standards.md §1 "no stato globale"). Keyed by (run.key, cluster_label): switching
    # back to an already-viewed cluster (or re-viewing it via the "Salva HTML" button after
    # already looking at it) is then instant instead of re-loading+resampling every subject's
    # real NIfTI mask from disk again. A failed build (ValueError - an unresolvable subject) is
    # never cached, so a transient/fixable problem can be retried on the next click.
    cluster_view_cache: dict[tuple[str, int], tuple[StatMapView, int]] = {}

    def _cached_cluster_overlap_view(
        run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig
    ) -> tuple[StatMapView, int]:
        cache_key = (run.key, cluster_label)
        if cache_key not in cluster_view_cache:
            cluster_view_cache[cache_key] = _build_cluster_overlap_view(run, metadata, cluster_label, lesion_cfg)
        return cluster_view_cache[cache_key]

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

    # 6-step decision order, left to right (2026-08-14, on request - replaces the previous
    # single flat "every run from every method mixed together" dropdown, then extended with
    # explicit Metrica/Componenti steps rather than leaving them buried in the Run label's own
    # free-text run_name): Dato (modality) -> Pipeline -> Metodo -> Metrica -> Componenti ->
    # Run (scoped by every step before it). Pipeline became a real choice, not a fixed label,
    # 15-08-26 (docs/dev/clustering_migration_plan.md §3) once this app started discovering
    # clustering.py runs too - Metrica/Componenti still show up for a clustering-pipeline run
    # (uniform layout across both pipelines), just resolved to their one NO_METRIC/
    # NO_N_COMPONENTS sentinel option each (see metric_options/n_components_options), since
    # clustering method params have no metric/n_components axis to offer. Steps 2-6's own
    # options are populated by the cascading callbacks below, empty at layout-build time.
    def _picker_field(label: str, dropdown_id: str) -> html.Div:
        return html.Div(
            className="picker-field",
            children=[html.Label(label, className="picker-label"), dcc.Dropdown(id=dropdown_id, clearable=False)],
        )

    app.layout = html.Div(
        className="page",
        children=[
            html.H1("Embedding Explorer", className="page-title"),
            html.P(
                "Esplorazione interattiva dei run di produzione (dim_reduction.py/clustering.py) — "
                "scegli un run e una colorazione.",
                className="page-subtitle",
            ),
            html.Div(
                className="controls",
                children=[
                    # Two rows (2026-08-14, on request): Dato/Pipeline/Metodo (the "which
                    # pipeline output" question) above, Metrica/Componenti/Run (the "which
                    # exact combination that pipeline produced" question) below.
                    html.Div(
                        className="picker-row",
                        children=[
                            html.Div(
                                className="picker-field",
                                children=[
                                    html.Label("Dato", className="picker-label"),
                                    dcc.Dropdown(
                                        id="modality-picker",
                                        options=[{"label": m, "value": m} for m in modality_options(runs)],
                                        value=default_modality,
                                        clearable=False,
                                    ),
                                ],
                            ),
                            _picker_field("Pipeline", "pipeline-picker"),
                            _picker_field("Metodo", "method-picker"),
                        ],
                    ),
                    html.Div(
                        className="picker-row",
                        children=[
                            _picker_field("Metrica", "metric-picker"),
                            _picker_field("Componenti", "n-components-picker"),
                            # "Parametri" (01-09-26, on request): real clustering runs vary by
                            # more than just the upstream embedding's metric/n_components - each
                            # method's own hyperparameters (n_clusters/linkage for agglomerative,
                            # etc.) do too. NO_METRIC-only for dim_reduction (see
                            # tag_param_options) - kept in this same row so the picker still
                            # reads as one uniform 4-step sequence across both pipelines.
                            _picker_field("Parametri", "tag-params-picker"),
                            _picker_field("Run", "run-picker"),
                        ],
                    ),
                    html.Div(color_buttons, className="color-buttons"),
                ],
            ),
            dcc.Store(id="selected-color-mode", data=NEUTRAL_MODE),
            html.H2("Embedding Visualization", className="section-heading"),
            html.Div(id="graph-area", className="graph-wrap"),
            # Always-visible (per design decision, 01-09-26 - not an appear-on-click popup):
            # placeholder until a point is clicked, subject's nilearn viewer afterward.
            html.Div(
                className="anatomy-panel",
                children=[
                    html.H2("Anatomia lesionale", className="section-heading"),
                    html.Div(id="lesion-viewer-content", children=_LESION_PLACEHOLDER),
                    html.Button("Salva HTML", id="lesion-save-btn", n_clicks=0, className="save-btn"),
                    dcc.Download(id="lesion-download"),
                ],
            ),
            # Hidden by default (style toggled by _update_cluster_picker below) - only a
            # clustering.py run (metadata has cluster_label) ever shows this panel.
            html.Div(
                id="cluster-map-panel",
                className="anatomy-panel",
                style={"display": "none"},
                children=[
                    html.H2("Overlap map per cluster", className="section-heading"),
                    html.Div(
                        className="anatomy-controls",
                        children=[
                            html.Div(
                                className="picker-field",
                                children=[
                                    html.Label("Cluster", className="picker-label"),
                                    dcc.Dropdown(id="cluster-picker", clearable=False),
                                ],
                            ),
                        ],
                    ),
                    html.Div(id="cluster-map-content"),
                    html.Button("Salva HTML", id="cluster-save-btn", n_clicks=0, className="save-btn"),
                    dcc.Download(id="cluster-download"),
                ],
            ),
        ],
    )

    @app.callback(
        Output("pipeline-picker", "options"),
        Output("pipeline-picker", "value"),
        Input("modality-picker", "value"),
    )
    def _update_pipeline_picker(modality: str):
        pipelines = pipeline_options(runs, modality)
        return [{"label": p, "value": p} for p in pipelines], pipelines[0]

    @app.callback(
        Output("method-picker", "options"),
        Output("method-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
    )
    def _update_method_picker(modality: str, pipeline: str | None):
        if pipeline is None:
            raise PreventUpdate
        methods = method_options(runs, modality, pipeline)
        return [{"label": m, "value": m} for m in methods], methods[0]

    @app.callback(
        Output("metric-picker", "options"),
        Output("metric-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
    )
    def _update_metric_picker(modality: str, pipeline: str | None, method: str | None):
        if pipeline is None or method is None:
            raise PreventUpdate
        metrics = metric_options(runs, modality, pipeline, method)
        return [{"label": m, "value": m} for m in metrics], metrics[0]

    @app.callback(
        Output("n-components-picker", "options"),
        Output("n-components-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
        Input("metric-picker", "value"),
    )
    def _update_n_components_picker(modality: str, pipeline: str | None, method: str | None, metric: str | None):
        if pipeline is None or method is None or metric is None:
            raise PreventUpdate
        n_components_values = n_components_options(runs, modality, pipeline, method, metric)
        options = [{"label": _n_components_option_label(n), "value": n} for n in n_components_values]
        return options, n_components_values[0]

    @app.callback(
        Output("tag-params-picker", "options"),
        Output("tag-params-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
        Input("metric-picker", "value"),
        Input("n-components-picker", "value"),
    )
    def _update_tag_params_picker(
        modality: str, pipeline: str | None, method: str | None, metric: str | None, n_components: int | None
    ):
        if pipeline is None or method is None or metric is None or n_components is None:
            raise PreventUpdate
        labels = tag_param_options(runs, modality, pipeline, method, metric, n_components, clustering_params_file)
        return [{"label": label, "value": label} for label in labels], labels[0]

    @app.callback(
        Output("run-picker", "options"),
        Output("run-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
        Input("metric-picker", "value"),
        Input("n-components-picker", "value"),
        Input("tag-params-picker", "value"),
    )
    def _update_run_picker(
        modality: str, pipeline: str | None, method: str | None, metric: str | None, n_components: int | None,
        tag_params_label: str | None,
    ):
        if pipeline is None or method is None or metric is None or n_components is None or tag_params_label is None:
            # An upstream picker just changed and hasn't propagated its new value here yet -
            # each cascading callback is a separate step in Dash's dependency graph, not a
            # synchronous call chain.
            raise PreventUpdate
        matching = runs_matching(runs, modality, pipeline, method, metric, n_components, tag_params_label, clustering_params_file)
        options = [{"label": run.run_name, "value": run.key} for run in matching]
        default_run_key = matching[-1].key  # most recent by _run_chronological_key
        return options, default_run_key

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
        Output("graph-area", "children"),
        Input("run-picker", "value"),
        Input("selected-color-mode", "data"),
    )
    def _update_graph(run_key: str | None, selected_mode: str):
        if run_key is None:
            raise PreventUpdate
        return graph_content_for(runs_by_key[run_key], selected_mode)

    @app.callback(
        Output("lesion-viewer-content", "children"),
        Input("embedding-graph", "clickData"),
        Input("run-picker", "value"),
    )
    def _update_lesion_viewer(click_data: dict | None, run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        # A run change resets to the placeholder (ctx.triggered_id tells the two Inputs apart) -
        # a subject clicked on a previous run must not linger once the picker moves on.
        if ctx.triggered_id == "run-picker" or click_data is None:
            return _LESION_PLACEHOLDER
        subject_id = click_data["points"][0].get("text")
        if subject_id is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        return lesion_viewer_content_for(run, subject_id, run_metadata(run), lesion_cfg)

    @app.callback(
        Output("lesion-download", "data"),
        Input("lesion-save-btn", "n_clicks"),
        State("embedding-graph", "clickData"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_lesion_html(_n_clicks: int, click_data: dict | None, run_key: str | None):
        if click_data is None or run_key is None:
            raise PreventUpdate
        subject_id = click_data["points"][0].get("text")
        if subject_id is None:
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
        Output("cluster-picker", "options"),
        Output("cluster-picker", "value"),
        Output("cluster-map-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_cluster_picker(run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            return [], None, {"display": "none"}
        clusters = cluster_options(run_metadata(run))
        return [{"label": str(cluster_label), "value": cluster_label} for cluster_label in clusters], clusters[0], {}

    @app.callback(
        Output("cluster-map-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
    )
    def _update_cluster_map(run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        return overlap_map_content_for(run, run_metadata(run), cluster_label, lesion_cfg, build_view=_cached_cluster_overlap_view)

    @app.callback(
        Output("cluster-download", "data"),
        Input("cluster-save-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_cluster_html(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            view, _n_subjects = _cached_cluster_overlap_view(run, run_metadata(run), cluster_label, lesion_cfg)
        except ValueError:
            raise PreventUpdate
        return dcc.send_string(_style_nilearn_html(view.html), filename=f"cluster_{cluster_label}_overlap_map.html")

    return app
