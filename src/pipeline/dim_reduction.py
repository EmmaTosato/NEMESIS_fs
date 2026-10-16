"""CLI entry point: apply a dimensionality-reduction method to an already-built feature matrix.

Usage:
    python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json

Reads a matrix artifact written by build_lesion_matrix.py (input_path must
already exist - no auto-build fallback). Two modes, chosen by `fine_tuning`:

- fine_tuning=false (production): embeds with the method's "params" from
  params_reduction.json, writes a normal matrix artifact holding the
  embedding. metadata is passed through unchanged from input_path (2026-08-17:
  this pipeline no longer enriches it itself) - lesion_volume_voxels is
  always already there, written once by build_lesion_matrix.py
  (src/features/lesion.py); lesion_side/nihss are NOT in metadata at all -
  they are subject-level clinical facts resolved at plot time from the
  subject registry, assets/metadata/participants.csv
  (src/analysis/embedding_coloring.py's color_values). A color_by entry the
  registry can't resolve raises a clear error there rather than silently
  recomputing something possibly wrong.
  src/pipeline/replot_dim_reduction.py regenerates every plot from metadata.csv
  alone, without reloading the original feature matrix, same as this
  pipeline's own plotting.
- fine_tuning=true (manual hyperparameter search, umap/tsne/pca/
  pacmap - t-SNE only sweeps perplexity, its other params still come from
  Thiebaut de Schotten et al. 2020): evaluates every combination in the
  method's "tuning_grid", writes a comparison table (tuning_results.csv)
  instead of an embedding - plus a line plot (tuning_plot.png) only when
  exactly one parameter is swept; 2+ swept parameters get no plot (heatmaps
  removed on request), just the CSV. No automatic selection - a human reads
  it, picks parameters by hand, writes them into params_reduction.json's
  "params", and re-runs with fine_tuning=false. The evaluation mechanisms applied are
  declared in config.tuning_evaluations (src/analysis/tuning_evaluations.py): the sweep's own
  score (always) plus the embedding-based ones (today plot_hdbscan: HDBSCAN on every
  combination, one grid PNG + CSV per nested leaf). The embedding-based ones can also be run
  later on a stored run, without refitting: src/pipeline/evaluate_tuning_embeddings.py.

Output lives under two separate branches of output_root, never mixed:
<output_root>/production/<method>/ (embeddings + plots + runs.csv) and
<output_root>/tuning/<method>/ (sweep tables/plots + runs_tuning.csv) - a
tuning run and a production run can never collide on disk, and each branch
carries its own chronological run history, distinct from any single run's
own config.md (see docs/dev/config.md). fine_tuning=true's sweep can also
persist every combination's actual embedding (not just its score) into
<output_root>/tuning/<method>/<dd-mm>_<session_name>/embeddings.npz, plus a
self-contained metadata.csv (same enrichment _run_production always applies),
when config.save_tuning_embeddings is true (opt-in, off by default) - so a
later reader can plot any saved combination without reloading X or the
participants.tsv registry.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.distances import SUPPORTED_BINARY_METRICS, require_binary_matrix
from src.analysis.embedding_plots import write_embedding_grid, write_embedding_plots
from src.analysis.model_config import DimReductionConfig, load_dim_reduction_config
from src.analysis.covariance_pca import components_for_share
from src.analysis.pca_method import decomposition_spectra, fit_pca
from src.analysis.params import load_method_params, load_nested_params, load_tag_params, load_trustworthiness_n_neighbors, load_tuning_grid
from src.analysis.plotting import compose_embedding_plot_title, compose_run_title, compose_tuning_leaf_title, plot_scree, plot_tuning_curve
from src.analysis.reduction import embed, embedding_for_viz
from src.analysis.tuning import METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS, TUNING_METRIC_NAMES, run_tuning_sweep
from src.analysis.tuning_embeddings import TuningRun, combo_key, leaf_dir
from src.analysis.tuning_evaluations import (
    require_native_score_declared,
    run_embedding_evaluations,
    validate_embedding_evaluations_feasible,
)
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.run_log import append_run_log_entry

LOGS_ROOT = Path("logs") / "dim_reduction"
LOG_FILENAME_PREFIX = "dim_reduction"
# The pca tuning's second scree plot shows only this many components (scree_plot_zoom.png), written
# when the full plot shows more.
SCREE_ZOOM_COMPONENTS = 50


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Embed a feature matrix with a configured dimensionality-reduction method.")
    parser.add_argument("--config", required=True, help="Path to a dim_reduction.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_dim_reduction_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    try:
        try:
            log_path = _log_path(config, now)
            attach_file_handler(log_path)
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        try:
            X, metadata, _extra_arrays = load_matrix(config.input_path, mmap=_reads_matrix_in_blocks(config))
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        if config.fine_tuning:
            return _run_fine_tuning(config, X, metadata, now, log_path)
        return _run_production(config, X, metadata, now, log_path)
    finally:
        log_duration(now)


def _reads_matrix_in_blocks(config: DimReductionConfig) -> bool:
    """True when the method reads the matrix a block of columns at a time (pca with the 'blocks'
    solver), so it can stay on disk instead of being loaded whole: a 6.8 GB matrix then costs one
    block of memory. Every other method needs the matrix in memory."""
    if config.reduction_method != "pca":
        return False
    params, _tag = load_method_params(config.params_file, "pca")
    return params.get("solver") == "blocks"


def _embed_production(
    config: DimReductionConfig, X: np.ndarray, params: dict, distance_cache: dict[str, np.ndarray]
) -> tuple[np.ndarray, dict, dict[str, np.ndarray], list[str]]:
    """(embedding, params as recorded for the run, extra arrays to save beside it, summary lines).

    For pca the recorded params carry the number of components actually kept (the answer to
    variance_share, which the params alone do not give) and the run keeps its whole variance
    spectrum, so the curve behind a variance_share choice can be read back. Every other method
    records the params as given."""
    if config.reduction_method != "pca":
        embedding = embed(config.reduction_method, X, params, distance_cache, config.precompute_distance_metric)
        return embedding, params, {}, []
    fit = fit_pca(X, params)
    note = f"PCA kept {fit.n_components} components, explaining {fit.explained_share:.1%} of the variance"
    if "variance_share" in params:
        note += f" (the smallest number reaching variance_share={params['variance_share']})"
    return fit.embedding, {**params, "n_components": fit.n_components}, {"eigenvalues": fit.eigenvalues}, [note]


def _run_production(
    config: DimReductionConfig, X: np.ndarray, metadata: pd.DataFrame, now: datetime, log_path: Path
) -> int:
    try:
        params, tag = load_method_params(config.params_file, config.reduction_method)
        if params.get("metric") in SUPPORTED_BINARY_METRICS:
            require_binary_matrix(X, params["metric"])
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    effective_session_name = f"{config.session_name}_{tag}" if tag else config.session_name
    output_dir = config.output_root / "production" / config.reduction_method / f"{now.strftime('%d-%m')}_{effective_session_name}"

    # distance_cache: if params["metric"] is jaccard/dice, embed() below and any viz
    # refit right after share the same precomputed distance matrix instead of
    # recomputing it (see src/analysis/reduction.py::embed's docstring).
    distance_cache: dict[str, np.ndarray] = {}
    try:
        embedding, params, extra_arrays, notes = _embed_production(config, X, params, distance_cache)
    except (TypeError, ValueError) as exc:
        # TypeError: an unrecognized hyperparameter in params_reduction.json (e.g. a typo'd
        # key) reaches the estimator's own **params unpack and raises there, not from any
        # validation this pipeline does itself. ValueError: a recognized but out-of-range
        # value (e.g. n_neighbors >= n_samples).
        logging.error("%s: cannot fit embedding with params %s: %s", config.reduction_method, params, exc)
        return 1

    # Separate embedding for visualization only (2 or 3 components, config.viz_n_components) -
    # reused as-is when it already matches (every production config today: both are 2, zero
    # extra cost); refit from raw X otherwise for umap/tsne only, since slicing
    # embedding[:, :viz_n_components] out of a higher-dimensional fit is not a meaningful
    # projection (see src/analysis/reduction.py::embedding_for_viz's docstring) - pca/
    # pacmap raise instead of a silent slice or an invalid refit.
    try:
        viz_embedding = embedding_for_viz(
            config.reduction_method, X, params, embedding, config.viz_n_components, distance_cache, config.precompute_distance_metric
        )
    except ValueError as exc:
        logging.error(str(exc))
        return 1

    try:
        save_matrix(
            output_dir,
            embedding,
            metadata,
            _build_readme_lines(config, X, embedding, params, now, notes),
            overwrite=config.overwrite,
            extra_arrays=extra_arrays,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("embedding written to %s (shape %s)", output_dir, embedding.shape)

    xlabel, ylabel = f"{config.reduction_method} dim 1", f"{config.reduction_method} dim 2"
    zlabel = f"{config.reduction_method} dim 3" if viz_embedding.shape[1] == 3 else None
    write_embedding_plots(
        viz_embedding,
        metadata,
        list(config.color_by),
        output_dir,
        xlabel,
        ylabel,
        lambda label: compose_embedding_plot_title(output_dir, config.reduction_method, label.capitalize() if label else None),
        zlabel=zlabel,
    )

    try:
        # One extra column per tag_param key (31-08-26, mirrors clustering.py's own
        # runs.csv columns) - exploded from `params` rather than re-parsing the joined tag
        # string, so a reader gets each hyperparameter as its own filterable column instead
        # of having to split "m_dice_nc2" back apart by hand.
        run_log_columns = {key: str(params[key]) for key in load_tag_params(config.params_file, config.reduction_method)}
        append_run_log_entry(
            config.output_root / "production" / config.reduction_method,
            effective_session_name,
            now,
            "production",
            params,
            output_dir,
            config.run_notes,
            config.input_path,
            extra_columns=run_log_columns,
        )
    except OSError as exc:
        logging.error("cannot write run log: %s", exc, exc_info=True)
        return 1

    logging.info("done - embedding written to %s, log written to %s", output_dir, log_path)
    return 0


def _run_fine_tuning(config: DimReductionConfig, X: np.ndarray, metadata: pd.DataFrame, now: datetime, log_path: Path) -> int:
    method = config.reduction_method
    try:
        params, _ = load_method_params(config.params_file, method)
        tuning_grid = load_tuning_grid(config.params_file, method)
        nested_params = load_nested_params(config.params_file, method, tuning_grid)
        trustworthiness_n_neighbors = (
            load_trustworthiness_n_neighbors(config.params_file, method)
            if method in METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS
            else None
        )
        # Before the sweep, which can take hours: a block that misstates the sweep's own score, or
        # asks for an evaluation the grid cannot support, must fail now, not after the fits.
        require_native_score_declared(config.tuning_evaluations, TUNING_METRIC_NAMES[method], method)
        validate_embedding_evaluations_feasible(config.tuning_evaluations, params, tuning_grid)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    # pca only: the decomposition(s) the sweep fits, kept to report their variance spectrum below.
    model_cache = {} if method == "pca" else None
    try:
        results, embeddings_by_combo = run_tuning_sweep(method, X, params, tuning_grid, trustworthiness_n_neighbors, model_cache)
    except ValueError as exc:
        logging.error(str(exc))
        return 1

    output_dir = _tuning_output_dir(config, now)
    try:
        _write_tuning_output(
            output_dir,
            results,
            embeddings_by_combo,
            params,
            tuning_grid,
            nested_params,
            TUNING_METRIC_NAMES[method],
            config,
            X,
            metadata,
            now,
            config.overwrite,
        )
    except (FileExistsError, OSError, ValueError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("tuning results written to %s (%d combinations evaluated)", output_dir, len(results))

    if model_cache is not None:
        try:
            spectra = decomposition_spectra(model_cache)
            _write_pca_spectra(
                output_dir, spectra, compose_run_title(output_dir, config.project), _scree_components(params, tuning_grid, spectra)
            )
        except (OSError, ValueError) as exc:
            logging.error("cannot write the pca spectrum (the sweep itself was written to %s): %s", output_dir, exc, exc_info=True)
            return 1

    if not _run_embedding_evaluations(config, output_dir, params, tuning_grid, nested_params, embeddings_by_combo):
        return 1

    try:
        append_run_log_entry(
            config.output_root / "tuning" / config.reduction_method,
            config.session_name,
            now,
            "tuning",
            {"base_params": params, "tuning_grid": tuning_grid},
            output_dir,
            config.run_notes,
            config.input_path,
        )
    except OSError as exc:
        logging.error("cannot write run log: %s", exc, exc_info=True)
        return 1

    logging.info("done - tuning results written to %s, log written to %s", output_dir, log_path)
    return 0


def _tuning_output_dir(config: DimReductionConfig, now: datetime) -> Path:
    return config.output_root / "tuning" / config.reduction_method / f"{now.strftime('%d-%m')}_{config.session_name}"


def _run_embedding_evaluations(
    config: DimReductionConfig,
    output_dir: Path,
    base_params: dict,
    tuning_grid: dict[str, list],
    nested_params: list[str],
    embeddings_by_combo: dict[tuple, np.ndarray],
) -> bool:
    """Runs the embedding-based evaluations declared in config.tuning_evaluations on the sweep that
    was just computed (in memory - works whether or not save_tuning_embeddings is on). False, with
    the error logged, if one fails: the sweep's own files are already on disk by then, and the
    same evaluations can be re-run on them without refitting (src/pipeline/evaluate_tuning_embeddings.py).
    """
    keys = list(tuning_grid)
    run = TuningRun(
        run_dir=output_dir,
        reduction_method=config.reduction_method,
        base_params=base_params,
        tuning_grid=tuning_grid,
        nested_params=nested_params,
        embeddings={combo_key(keys, combo): embedding for combo, embedding in embeddings_by_combo.items()},
    )
    try:
        written = run_embedding_evaluations(config.tuning_evaluations, run, overwrite=False)
    except (FileExistsError, OSError, ValueError) as exc:
        logging.error("tuning evaluation failed (the sweep itself was written to %s): %s", output_dir, exc)
        return False
    if written and not config.save_tuning_embeddings:
        logging.warning(
            "save_tuning_embeddings=false: these evaluations ran on the in-memory sweep and cannot be re-run later "
            "with other settings - set it to true to keep embeddings.npz"
        )
    return True



def _write_tuning_output(
    output_dir: Path,
    results: pd.DataFrame,
    embeddings_by_combo: dict[tuple, np.ndarray],
    base_params: dict,
    tuning_grid: dict[str, list],
    nested_params: list[str],
    metric_col: str,
    config: DimReductionConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    now: datetime,
    overwrite: bool,
) -> None:
    if output_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"output directory {output_dir} already exists and overwrite=False "
                "- set overwrite=True to replace it, or choose a different session_name"
            )
        # A previous run into this exact output_dir may have used a different
        # nested_params/tuning_grid, leaving leaf folders this run's own
        # config.md below never describes (see lessons_learned.md #18) - wipe
        # first so overwrite=True always means "this directory reflects
        # exactly this run", never this run's files layered on whatever
        # leaves a prior, incompatible grid left behind.
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "tuning_results.csv", index=False)

    swept_params = list(tuning_grid.keys())
    if config.save_tuning_embeddings:
        _write_tuning_embeddings(output_dir, embeddings_by_combo, swept_params)
        # Same subjects/row order for every combination in this sweep (one X/metadata
        # for the whole run) - written once at the top, not per leaf. Self-contained
        # (already enriched by the caller above) so a later reader never needs X or
        # the participants.tsv registry again, just this file + embeddings.npz.
        metadata.to_csv(output_dir / "metadata.csv", index=False)
    free_params = [key for key in swept_params if key not in nested_params]
    title = compose_run_title(output_dir, config.project)

    if not nested_params:
        if len(free_params) == 1:
            plot_tuning_curve(results, free_params[0], metric_col, output_dir / "tuning_plot.png", title)
        else:
            logging.warning(
                "tuning_grid has %d swept parameters and no nested_params declared - no plot generated "
                "(only a 1-parameter curve is supported without nested_params; tuning_results.csv still has "
                "every evaluated combination)",
                len(swept_params),
            )
    else:
        _write_nested_tuning_leaves(
            output_dir, results, embeddings_by_combo, base_params, tuning_grid, nested_params, free_params, config, metadata
        )

    readme_lines = [
        f"# {title}",
        "",
        "## Config",
        "",
        "```json",
        json.dumps(
            {
                "project": config.project,
                "input_path": str(config.input_path),
                "reduction_method": config.reduction_method,
                "params_file": str(config.params_file),
                "session_name": config.session_name,
                "base_params": base_params,
                "tuning_grid": tuning_grid,
                "nested_params": nested_params,
                "tuning_evaluations": config.tuning_evaluations,
            },
            indent=2,
        ),
        "```",
        "",
        "## Summary",
        "",
        f"Swept parameters: {swept_params}",
        f"Nested parameters (one subfolder per real combination): {nested_params or 'none'}",
        f"Free/grid parameters (embeddings_grid.png per leaf): {free_params}",
        f"Combinations evaluated: {len(results)}",
        f"Metric: {metric_col}",
        f"Evaluations applied: {list(config.tuning_evaluations)}",
        "",
        "Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png (or the per-leaf "
        "embeddings_grid_*.png) and pick parameters by hand.",
    ]
    (output_dir / "config.md").write_text("\n".join(readme_lines) + "\n")


def _write_tuning_embeddings(output_dir: Path, embeddings_by_combo: dict[tuple, np.ndarray], keys: list[str]) -> None:
    """Serializes every combination's embedding actually computed by the sweep
    (not just the ones shown in embeddings_grid_*.png - the full Cartesian
    product) into a single embeddings.npz, keyed by tuning_embeddings.combo_key. Opt-in via
    config.save_tuning_embeddings - before this flag existed no tuning run
    ever wrote this file, so it stays off by default (code_standards.md
    §0/§5: no silent change to an existing run's output shape).
    """
    arrays = {combo_key(keys, combo): embedding for combo, embedding in embeddings_by_combo.items()}
    _savez_atomic(output_dir / "embeddings.npz", arrays)


def _savez_atomic(final_path: Path, arrays: dict[str, np.ndarray]) -> None:
    # Atomic (HIGH #24, 2026-08): np.savez wrote directly to the final path - a run killed
    # mid-write (SLURM timeout, Ctrl+C) left a truncated embeddings.npz sitting next to an
    # otherwise-complete tuning_results.csv/config.md, indistinguishable from a successful
    # run until something actually tries to np.load it. Same temp-file-then-rename pattern
    # as save_matrix (src/utils/artifacts.py), scaled down to one file instead of a directory.
    tmp_path = final_path.parent / f".{final_path.stem}_tmp_{uuid.uuid4().hex}.npz"
    np.savez(tmp_path, **arrays)
    tmp_path.replace(final_path)


def _scree_components(params: dict, tuning_grid: dict[str, list], spectra: dict[str, np.ndarray]) -> int:
    """How many components the scree plot shows: the most any combination of the sweep keeps."""
    if "n_components" in tuning_grid:
        sizes = tuning_grid["n_components"]
    elif "n_components" in params:
        sizes = [params["n_components"]]
    else:
        shares = tuning_grid["variance_share"] if "variance_share" in tuning_grid else [params["variance_share"]]
        sizes = [components_for_share(eigenvalues, share) for eigenvalues in spectra.values() for share in shares]
    return max(sizes)


def _write_pca_spectra(output_dir: Path, spectra: dict[str, np.ndarray], title: str, n_shown: int) -> None:
    """eigenvalues.npz (one array per decomposition the sweep fitted, keyed by what defines it) and
    scree_plot.png (its first `n_shown` components), plus scree_plot_zoom.png on the first
    SCREE_ZOOM_COMPONENTS when `n_shown` is larger: the variance spectrum, which tuning_results.csv
    only samples at the swept values. Written for every pca tuning, whether or not
    save_tuning_embeddings is on (47 KB)."""
    _savez_atomic(output_dir / "eigenvalues.npz", spectra)
    plot_scree(spectra, output_dir / "scree_plot.png", title, n_shown)
    if n_shown > SCREE_ZOOM_COMPONENTS:
        plot_scree(spectra, output_dir / "scree_plot_zoom.png", f"{title} - first {SCREE_ZOOM_COMPONENTS} components", SCREE_ZOOM_COMPONENTS)


# embeddings_grid.png is a static-only diagnostic (no interactive counterpart) - always 2
# components, never a refit. Any leaf/cell whose own n_components isn't this value gets no
# embeddings_grid output at all as of 26-08-26 (see _write_nested_tuning_leaves/
# _build_grid_blocks) - a static image (PNG) or one-off interactive HTML was judged not worth
# producing at all for a >2-component embedding, tuning or production alike, now that
# src.pipeline.embedding_app (a live Dash app) already covers exactly that case for any
# already-written run. Production's own embedding_plots.py::write_embedding_plots follows the
# same rule for n_dims==3 (no PNG, no HTML - see its own docstring). To look at one specific
# >2-component tuning combination on demand, use src/pipeline/plot_tuning_embedding_3d.py against
# this run's own embeddings.npz - a manual, on-request tool, not something this pipeline ever
# generates automatically for every leaf/color mode.
_TUNING_GRID_N_COMPONENTS = 2


def _write_nested_tuning_leaves(
    output_dir: Path,
    results: pd.DataFrame,
    embeddings_by_combo: dict[tuple, np.ndarray],
    base_params: dict,
    tuning_grid: dict[str, list],
    nested_params: list[str],
    free_params: list[str],
    config: DimReductionConfig,
    metadata: pd.DataFrame,
) -> None:
    """Groups `results` by nested_params (one subfolder per real combination
    actually present), writing each leaf's own filtered tuning_results.csv
    always, plus, unless every cell this leaf could show turns out to have
    n_components != _TUNING_GRID_N_COMPONENTS (see `_build_grid_blocks`),
    embeddings_grid_<color>.png (see
    src/analysis/embedding_plots.py::write_embedding_grid): one row per free
    parameter, holding every other free parameter at base_params' own value.

    No cell is ever refit to _TUNING_GRID_N_COMPONENTS (26-08-26, on
    request) - a cell whose own combination has some other n_components is
    just left out, never rendered as a static image at all, since it would
    only ever add a distorted/incomplete view on top of what
    src/pipeline/plot_tuning_embedding_3d.py already gives on demand for that
    exact combination. If a leaf's own n_components (checked upfront here
    only when "n_components" is itself one of `nested_params`, i.e. fixed
    for the whole leaf) already isn't _TUNING_GRID_N_COMPONENTS, every cell
    in every block would be dropped this same way - skipped here instead,
    without ever calling `_build_grid_blocks` at all, so this is a
    fast-path special case of the same rule, not a second one.
    """
    keys = list(tuning_grid.keys())
    for group_key, group in results.groupby(nested_params, sort=False):
        raw_values = group_key if isinstance(group_key, tuple) else (group_key,)
        leaf = {name: (value.item() if hasattr(value, "item") else value) for name, value in zip(nested_params, raw_values)}

        leaf_path = leaf_dir(output_dir, nested_params, leaf)
        leaf_path.mkdir(parents=True, exist_ok=True)
        group.to_csv(leaf_path / "tuning_results.csv", index=False)

        leaf_n_components = leaf.get("n_components")
        if leaf_n_components is not None and leaf_n_components != _TUNING_GRID_N_COMPONENTS:
            logging.info(
                "skipping embeddings_grid for %s: n_components=%s (only n_components=%d combinations get "
                "this diagnostic - see src/pipeline/plot_tuning_embedding_3d.py for an on-demand 3D view of a "
                "specific combination)",
                leaf_path, leaf_n_components, _TUNING_GRID_N_COMPONENTS,
            )
            continue

        blocks = _build_grid_blocks(free_params, tuning_grid, keys, leaf, base_params, embeddings_by_combo, leaf_path)
        if not blocks:
            logging.info(
                "skipping embeddings_grid for %s: every combination this leaf could show has "
                "n_components != %d - nothing left to plot",
                leaf_path, _TUNING_GRID_N_COMPONENTS,
            )
            continue

        leaf_title = compose_tuning_leaf_title(output_dir, config.reduction_method, leaf)
        write_embedding_grid(
            blocks,
            metadata,
            list(config.color_by),
            leaf_path,
            f"{config.reduction_method} dim 1",
            f"{config.reduction_method} dim 2",
            lambda label, leaf_title=leaf_title: f"{leaf_title} - {label.capitalize()}" if label else leaf_title,
        )


def _build_grid_blocks(
    free_params: list[str],
    tuning_grid: dict[str, list],
    keys: list[str],
    leaf: dict,
    base_params: dict,
    embeddings_by_combo: dict[tuple, np.ndarray],
    leaf_path: Path,
) -> list[tuple[str, list[tuple[str, np.ndarray]]]]:
    """For each free parameter, one cell per value it can take - every other
    free parameter held at base_params' own value (must be one of that
    parameter's own tuning_grid values, else raises: the embedding for that
    exact combination was never computed by run_tuning_sweep - fix by adding
    the base_params value to that parameter's tuning_grid list).

    A cell whose own combination's embedding doesn't already have exactly
    _TUNING_GRID_N_COMPONENTS columns is dropped, never refit (26-08-26, on
    request - see _write_nested_tuning_leaves) - this only actually happens
    when "n_components" is a *free* parameter (not nested, so not caught by
    that function's own upfront leaf-level check) with a swept value other
    than _TUNING_GRID_N_COMPONENTS; every other free parameter's cells stay
    at whatever n_components `leaf`/`base_params` already fixes, which is
    _TUNING_GRID_N_COMPONENTS whenever this function is even reached (the
    caller already skipped the leaf otherwise). A block left with zero cells
    after dropping is omitted from the returned list entirely rather than
    appended empty - the caller skips writing anything at all if every block
    ends up omitted this way.
    """
    blocks = []
    for varying in free_params:
        held_params = [p for p in free_params if p != varying]
        cells = []
        for value in tuning_grid[varying]:
            combo_values = []
            for key in keys:
                if key == varying:
                    combo_values.append(value)
                elif key in leaf:
                    combo_values.append(leaf[key])
                else:
                    if key not in base_params:
                        raise ValueError(
                            f"cannot build embeddings_grid: free parameter {key!r} has no base_params value "
                            f"to hold it at while varying {varying!r}"
                        )
                    combo_values.append(base_params[key])
            combo = tuple(combo_values)
            if combo not in embeddings_by_combo:
                raise ValueError(
                    f"no embedding computed for combination {dict(zip(keys, combo))!r} - the base_params "
                    f"value for {held_params!r} must be present in that parameter's own tuning_grid list "
                    "for the embeddings_grid plot to hold it there"
                )
            embedding = embeddings_by_combo[combo]
            if embedding.shape[1] != _TUNING_GRID_N_COMPONENTS:
                logging.info(
                    "skipping embeddings_grid cell %s in %s (%s=%s): n_components=%d, not %d - "
                    "see src/pipeline/plot_tuning_embedding_3d.py for an on-demand 3D view of this combination",
                    dict(zip(keys, combo)), leaf_path, varying, value, embedding.shape[1], _TUNING_GRID_N_COMPONENTS,
                )
                continue
            cells.append((str(value), embedding))
        if cells:
            blocks.append((varying, cells))
    return blocks


def _config_summary(config: DimReductionConfig) -> str:
    payload = {
        "project": config.project,
        "input_path": str(config.input_path),
        "reduction_method": config.reduction_method,
        "params_file": str(config.params_file),
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "fine_tuning": config.fine_tuning,
        "color_by": list(config.color_by),
        "viz_n_components": config.viz_n_components,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict, notes: list[str]) -> list[str]:
    return [
        "## Config",
        "",
        "```json",
        _config_summary(config),
        "```",
        "",
        "## Summary",
        "",
        f"Input matrix shape: {X.shape[0]} subjects x {X.shape[1]} features",
        f"Embedding shape: {embedding.shape[0]} subjects x {embedding.shape[1]} components",
        *notes,
        f"Params used: {json.dumps(params)}",
    ]


def _build_readme_lines(
    config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict, now: datetime, notes: list[str]
) -> list[str]:
    return [f"# {config.project} dim_reduction ({config.reduction_method}) — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, X, embedding, params, notes
    )


def _log_path(config: DimReductionConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{LOG_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
