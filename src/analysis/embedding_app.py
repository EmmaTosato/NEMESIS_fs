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
"""

from __future__ import annotations

import itertools
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate

from src.analysis.embedding_coloring import COLOR_MODES
from src.analysis.embedding_coloring import color_values as read_color_values
from src.analysis.plotting import _CATEGORICAL_PALETTE, _NOISE_COLOR, compose_embedding_plot_title
from src.utils.artifacts import MANIFEST_FILENAME, load_matrix, read_run_params

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
.page-subtitle {{ font-size: 16px; color: #767676; text-align: center; margin: 0 0 56px; }}
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
.status-message {{ text-align: center; color: #767676; font-size: 15px; margin: 64px 0; }}
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
    own fixed segments. clustering.py's "comparison" pseudo-method directory (see
    clustering.py::_comparison_dir, itself nested one <reduction_method> segment deep too) is
    naturally excluded here without any special-casing: it only ever holds a config.md, never a
    manifest.json, so it fails the same existence check every other incomplete/non-run
    directory does.

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


# A run_name's own leading "DD-MM" (every run seen so far: "13-08_s1.1_nc3_m_dice",
# "23-07_s1.1_c150", ...) - used only to order/default the "Giorno" picker chronologically
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


# Sentinel for "this method's own params have no 'metric' key at all" (PCA/PaCMAP today,
# see config/registry/params_reduction.json - their base params dicts never include one,
# unlike UMAP/t-SNE) - distinct from any real metric string, so the "Metrica" picker still
# has exactly one, always-selectable option for those methods instead of an empty dropdown.
# Also the only value clustering pipeline runs ever report (15-08-26) - a clustering method's
# own params (kmeans' n_clusters, hdbscan's min_cluster_size, ...) have no "metric" axis in
# this picker's sense at all, not just sometimes-missing like pca/pacmap's.
NO_METRIC = "—"

# Sibling sentinel for "this run's params have no 'n_components' key at all" - every
# clustering pipeline run (15-08-26): clustering.py never resamples X's dimensionality, so its
# own params dict has no n_components concept (the picker still shows the "Componenti" step
# for a uniform layout across both pipelines, just with this one always-selectable option). An
# int, not a string like NO_METRIC, to keep n_components_options' return type uniform
# (list[int]) for its dim_reduction-pipeline case - -1 is safely distinct from any real
# n_components value (always >= 1).
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


def metric_options(runs: list[ProductionRun], modality: str, pipeline: str, method: str) -> list[str]:
    """Distinct `metric` values actually used by (modality, pipeline, method)'s own runs,
    sorted - NO_METRIC included if any of them has no 'metric' key in its own params at all.

    Clustering pipeline runs always resolve to exactly [NO_METRIC]: a clustering method's own
    params (kmeans' n_clusters, hdbscan's min_cluster_size, ...) never carry a 'metric' key in
    this picker's sense at all - explicit branch, not a guess (see NO_METRIC's own docstring)."""
    if pipeline == "clustering":
        return [NO_METRIC]
    values = {
        params.get("metric", NO_METRIC)
        for run in runs_for(runs, modality, pipeline, method)
        if (params := _run_params_or_none(run)) is not None
    }
    return sorted(values)


def n_components_options(runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str) -> list[int]:
    """Distinct `n_components` values among (modality, pipeline, method, metric)'s own runs,
    sorted ascending - includes every value actually used, even ones this app can't display
    (e.g. 150 for the full-dimensionality PCA production run): the picker's job is to reflect
    what was actually run, not to pre-filter it down to what's displayable (graph_content_for
    already reports that clearly per-run, see UndisplayableRunError).

    Clustering pipeline runs always resolve to exactly [NO_N_COMPONENTS] (see its docstring) -
    clustering.py never resamples X's dimensionality, so there is no n_components axis to
    report."""
    if pipeline == "clustering":
        return [NO_N_COMPONENTS]
    values = {
        params["n_components"]
        for run in runs_for(runs, modality, pipeline, method)
        if (params := _run_params_or_none(run)) is not None and params.get("metric", NO_METRIC) == metric
    }
    return sorted(values)


def runs_matching(
    runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str, n_components: int
) -> list[ProductionRun]:
    """Runs matching (modality, pipeline, method, metric, n_components) exactly,
    chronologically ordered - the final picker step ("Run"): today this is usually exactly one
    run (each combination has only ever been produced once), but stays a list rather than
    assuming that - a rerun of the same combination on a later date is a legitimate, real
    scenario this picker must keep showing both of, not silently collapse to one.

    Clustering pipeline runs skip the metric/n_components filter entirely (both picker steps
    only ever offer their one NO_METRIC/NO_N_COMPONENTS sentinel option for this pipeline, see
    metric_options/n_components_options - filtering on them would be a no-op, not a real
    narrowing) and return every run for (modality, pipeline, method) directly."""
    if pipeline == "clustering":
        return runs_for(runs, modality, pipeline, method)
    matches = []
    for run in runs_for(runs, modality, pipeline, method):
        params = _run_params_or_none(run)
        if params is not None and params.get("metric", NO_METRIC) == metric and params.get("n_components") == n_components:
            matches.append(run)
    return matches


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
            # enrich_lesion_metadata.py run yet), it got x=[]/y=[] (nothing to plot) but
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

    return dcc.Graph(figure=figure, config={"displayModeBar": False}, style={"width": "100%"})


def _color_button_label(mode_name: str) -> str:
    # Raw mode.label, not .capitalize()'d - "NIHSS (severity)".capitalize() would produce
    # "Nihss (severity)" (str.capitalize lowercases every character but the first), the same
    # trap the notebook prototype's _panel_title left uncorrected; sidestepped here by not
    # reformatting the label's casing at all, same as compose_embedding_plot_title's own
    
    return "neutro" if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label


def build_app(runs: list[ProductionRun]) -> Dash:
    """Builds the Dash app: a run picker (dcc.Dropdown, one entry per discovered production
    run) plus a color-mode button group (COLOR_MODE_ORDER, styled as a chip row via CSS, not
    a second dropdown - the design brief this was built against, 14-08-26, asked for "bottoni"
    explicitly) driving one dcc.Graph. No client-side state beyond which button is active
    (dcc.Store) - the embedding/figure itself is rebuilt server-side on every run/color change
    (load_run + build_embedding_figure), never cached: at this cohort size (~1150 subjects,
    matrix.npy a few hundred KB at most) a fresh disk read + figure build is fast enough that
    a cache would add complexity for no measurable benefit.

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

    app = Dash(__name__)
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
                            _picker_field("Run", "run-picker"),
                        ],
                    ),
                    html.Div(color_buttons, className="color-buttons"),
                ],
            ),
            dcc.Store(id="selected-color-mode", data=NEUTRAL_MODE),
            html.Div(id="graph-area", className="graph-wrap"),
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
        Output("run-picker", "options"),
        Output("run-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
        Input("metric-picker", "value"),
        Input("n-components-picker", "value"),
    )
    def _update_run_picker(
        modality: str, pipeline: str | None, method: str | None, metric: str | None, n_components: int | None
    ):
        if pipeline is None or method is None or metric is None or n_components is None:
            # An upstream picker just changed and hasn't propagated its new value here yet -
            # each cascading callback is a separate step in Dash's dependency graph, not a
            # synchronous call chain.
            raise PreventUpdate
        matching = runs_matching(runs, modality, pipeline, method, metric, n_components)
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

    return app
