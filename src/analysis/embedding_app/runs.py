"""Discovery and reading of the production runs the Embedding Explorer displays.

A run is one already-written output of dim_reduction.py or clustering.py: this module finds
them under results/, reads a run's own artifacts (matrix, metadata, params) and reports a run
it cannot display instead of drawing something misleading. It knows nothing about the page -
no Dash, no figures, no panels.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.artifacts import (
    MANIFEST_FILENAME,
    MATRIX_FILENAME,
    METADATA_FILENAME,
    load_matrix,
    read_run_config,
    read_run_params,
)


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


# Sentinel for "this axis doesn't apply to this run at all" - shared across the selectors that can lack a
# value (Metrica/Componenti: PCA/PaCMAP dim_reduction runs have no 'metric' key, config/registry/params_reduction.json;
# a clustering run built directly on un-reduced data, reduction_method="raw", has no upstream-embedding
# metric/n_components; Parametri of a dim_reduction run, or of a method with no tag_param registered). One shared
# "—" rather than one per axis, so the placeholder reads identically everywhere. Not UNSET ("---"): that is a
# selector that is not a filter, this is a real value a run has (that it has none).
NO_METRIC = "—"

# Sibling sentinel for "this run's own axis has no 'n_components' value" (see NO_METRIC) - an int, not a string
# like NO_METRIC - -1 is safely distinct from any real n_components value (always >= 1).
NO_N_COMPONENTS = -1


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
    _matrix, metadata, _extra_arrays = load_matrix(run.path, mmap=True)  # the matrix stays on disk: only the csv is wanted
    return metadata


def _run_params_or_none(run: ProductionRun) -> dict | None:
    """run_params(run), isolated per-run (HIGH #25, 2026-08 - lesson #21). The 3 picker
    helpers below each call this once per run in a comprehension - a single run with a
    corrupt/truncated config.md must not take down every other run's picker options with
    it (e.g. a picker over 8 runs of one method, one has a bad config.md ->
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
    which have no metric/n_components concept at all; their own hyperparameters are the "Parametri" selector, run_picker_values).
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


class UndisplayableRunError(ValueError):
    """A production run's saved embedding has more than 3 columns - no viz-only projection
    was ever persisted for it (dim_reduction.py's viz_embedding is refit in-memory and used
    only to write the now-removed embedding_plot_interactive.html/PNGs at production time,
    never saved to disk on its own), and this app, like src/pipeline/replot_dim_reduction.py, never
    reloads the original feature matrix to refit one - slicing embedding[:, :3] instead would
    be the exact mistake lessons_learned.md #16 documents (a UMAP/t-SNE/PaCMAP embedding's
    columns carry no importance ordering, so a slice is an arbitrary cut, not a summary)."""


def _matrix_shape(run: ProductionRun) -> tuple[int, ...]:
    """The saved matrix's shape, read from manifest.json without loading matrix.npy - a
    clustering.py run on a raw matrix (ADP on a 5845 x 221955 lesion matrix is 1.2 GB) must not
    be read in full just to learn that it is not 2D/3D."""
    manifest = json.loads((run.path / MANIFEST_FILENAME).read_text())
    return tuple(manifest["matrix_shape"])


def _viz_twin_path(run: ProductionRun) -> Path | None:
    """The `viz_embedding_path` recorded in a clustering.py run's own config.md - the 2D/3D
    twin embedding clustering.py already validated as a twin of this run's input (same
    reduction method and params except n_components, same subjects in the same order, see
    clustering.py::_resolve_viz_embedding) when the run was written. None when the run was
    written without one (a legitimate, recorded case: no usable twin existed). Relative paths
    are relative to the working directory, same as every other path in the run's config.md."""
    if run.pipeline != "clustering":
        return None
    raw = read_run_config(run.path).get("viz_embedding_path")
    return None if raw is None else Path(raw)


def _load_viz_twin(run: ProductionRun, twin_path: Path, metadata: pd.DataFrame) -> np.ndarray:
    """Loads the twin embedding for a clustering run that cannot be displayed directly,
    checking again (the twin could have been moved or rewritten since the run was made) that
    it is 2D/3D and covers exactly this run's subjects in this run's order - a mismatch would
    draw every cluster label on the wrong subject with no error to notice it by."""
    try:
        twin_embedding, twin_metadata, _extra_arrays = load_matrix(twin_path)
    except FileNotFoundError as exc:
        raise UndisplayableRunError(
            f"Run {run.path} was made with viz_embedding_path={twin_path}, which can no longer be read: {exc}"
        ) from exc
    if twin_embedding.shape[1] not in (2, 3):
        raise UndisplayableRunError(
            f"Run {run.path}: viz_embedding_path {twin_path} has {twin_embedding.shape[1]} components, not 2 or 3"
        )
    if list(twin_metadata["subject_id"]) != list(metadata["subject_id"]):
        raise UndisplayableRunError(
            f"Run {run.path}: viz_embedding_path {twin_path} does not cover the same subjects in the same order "
            "as the run - the cluster labels would be drawn on the wrong points"
        )
    return twin_embedding


def load_run(run: ProductionRun) -> tuple[np.ndarray, pd.DataFrame]:
    """Loads `run`'s embedding + metadata, raising UndisplayableRunError (not silently
    slicing) if it cannot be shown as 2D/3D.

    A run whose own matrix is 2D/3D is read from disk as is. A clustering.py run whose matrix
    has any other number of columns (e.g. clustered on a 10-component UMAP, or on a raw
    matrix) is shown on the coordinates of the twin embedding recorded in its own config.md
    (`viz_embedding_path`): the points are where the twin puts them, the colors are the
    clusters computed in the run's own space. view_note_for says so on the figure. Without a
    recorded twin the run stays undisplayable."""
    shape = _matrix_shape(run)
    if len(shape) == 2 and shape[1] in (2, 3):
        embedding, metadata, _extra_arrays = load_matrix(run.path)
        return embedding, metadata

    twin_path = _viz_twin_path(run)
    if twin_path is not None:
        metadata = pd.read_csv(run.path / METADATA_FILENAME)
        return _load_viz_twin(run, twin_path, metadata), metadata

    n_dims = shape[1]
    # AUDIT_FINDINGS.md #43/#44: this message used to always point at dim_reduction.py's
    # viz_n_components, even for a clustering.py run - clustering.py has no such config
    # field (it never reduces dimensionality itself, see docs/dev/models.md's
    # "reduced_data (declarative-only)" section) and rerunning it would leave matrix.npy's
    # dimensionality unchanged either way, so that advice would not fix anything there.
    if run.pipeline == "dim_reduction":
        fix_hint = "rerun dim_reduction.py with viz_n_components 2 or 3, or pick a different run"
    else:
        fix_hint = (
            f"{run.pipeline}.py does not reduce dimensionality itself - rerun it with a viz_embedding_path "
            "(a 2D/3D twin of its input embedding, same params except n_components), or pick a different run"
        )
    raise UndisplayableRunError(
        f"Run {run.path} has a saved embedding with {n_dims} components - this app can only display an "
        f"already-2-or-3-component embedding: {fix_hint}."
    )


def view_note_for(run: ProductionRun) -> str | None:
    """A one-line caveat for a run shown on a twin's coordinates (see load_run), None for a run
    shown on its own matrix. The picture is not the space the clusters were computed in, and
    the figure has to say so."""
    shape = _matrix_shape(run)
    if len(shape) == 2 and shape[1] in (2, 3):
        return None
    twin_path = _viz_twin_path(run)
    if twin_path is None:
        return None
    return (
        f"2D view of embedding {twin_path.name}: not the space the clusters were computed in "
        f"({shape[1]} components). Positions from the 2D twin, colors from the clusters."
    )


def load_cluster_space(run: ProductionRun) -> np.ndarray | None:
    """The matrix a clustering.py run actually clustered, when it differs from what is drawn
    (a run shown on a twin's coordinates, see load_run) and is itself an embedding
    (`reduced_data` true): the centroid and its nearest subject have to be found there, not in
    the 2D picture, where the mean of the drawn points is not the cluster's centre. None
    otherwise: a run drawn on its own matrix, or one clustered on a raw matrix (ADP on a
    221955-column lesion matrix), where a mean of binary columns would not be the metric
    the clusters were computed with - those fall back to the drawn coordinates."""
    shape = _matrix_shape(run)
    if run.pipeline != "clustering" or (len(shape) == 2 and shape[1] in (2, 3)):
        return None
    if not read_run_config(run.path)["reduced_data"]:
        return None
    return np.load(run.path / MATRIX_FILENAME)
