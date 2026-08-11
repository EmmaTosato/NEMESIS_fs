"""CLI entry point: apply a dimensionality-reduction method to an already-built feature matrix.

Usage:
    python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json

Reads a matrix artifact written by build_lesion_matrix.py (input_path must
already exist - no auto-build fallback). Two modes, chosen by `fine_tuning`:

- fine_tuning=false (production): embeds with the method's "params" from
  params_reduction.json, writes a normal matrix artifact holding the
  embedding. metadata gains 3 columns not present on input, via
  src/features/clinical.py's enrich_metadata_with_lesion_info (shared with
  dim_reduction_clustering.py, so both pipelines always persist the same
  enrichment regardless of which one produced a given result):
  lesion_volume_voxels (X.sum(axis=1), the same per-subject voxel count
  regress_out_volume already uses), lesion_side ("unknown" for a
  subject/dataset the source participants.tsv can't resolve), and nihss
  (NaN under the same conditions - a continuous score has no "unknown"
  category to fall into). All three exist to color
  embedding_plot_volume.*/embedding_plot_side.*/embedding_plot_nihss.* (see
  plotting.py) and are persisted, not just computed ad hoc, so
  scripts/replot_dim_reduction.py can regenerate every plot from metadata.csv
  alone, without reloading the original feature matrix.
- fine_tuning=true (manual hyperparameter search, umap/tsne/pca/pca_varimax/
  pacmap - t-SNE only sweeps perplexity, its other params still come from
  Thiebaut de Schotten et al. 2020): evaluates every combination in the
  method's "tuning_grid", writes a comparison table (tuning_results.csv)
  instead of an embedding - plus a line plot (tuning_plot.png) only when
  exactly one parameter is swept; 2+ swept parameters get no plot (heatmaps
  removed on request), just the CSV. No automatic selection - a human reads
  it, picks parameters by hand, writes them into params_reduction.json's
  "params", and re-runs with fine_tuning=false.

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
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.covariates import check_volume_regression_compatible, regress_out_covariate
from src.analysis.embedding_plots import write_embedding_grid, write_embedding_plots
from src.analysis.model_config import DimReductionConfig, load_dim_reduction_config
from src.analysis.params import load_method_params, load_nested_params, load_trustworthiness_n_neighbors, load_tuning_grid
from src.analysis.plotting import compose_embedding_plot_title, compose_run_title, compose_tuning_leaf_title, plot_tuning_curve
from src.analysis.reduction import REDUCTION_METHODS, embedding_for_viz
from src.analysis.tuning import METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS, TUNING_METRIC_NAMES, run_tuning_sweep
from src.features.clinical import enrich_metadata_with_lesion_info
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

LOGS_ROOT = Path("logs") / "dim_reduction"
REPORT_FILENAME_PREFIX = "dim_reduction_summary"


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
        log_path = _log_path(config, now)
        attach_file_handler(log_path)
    except OSError as exc:
        logging.error("cannot set up log file: %s", exc, exc_info=True)
        return 1

    try:
        X, metadata, _extra_arrays = load_matrix(config.input_path)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    if config.fine_tuning:
        return _run_fine_tuning(config, X, metadata, now, log_path)
    return _run_production(config, X, metadata, now, log_path)


def _run_production(
    config: DimReductionConfig, X: np.ndarray, metadata: pd.DataFrame, now: datetime, log_path: Path
) -> int:
    try:
        params, tag = load_method_params(config.params_file, config.reduction_method)
        check_volume_regression_compatible(config.regress_out_volume, params)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    effective_session_name = f"{config.session_name}_{tag}" if tag else config.session_name
    output_dir = config.output_root / "production" / config.reduction_method / f"{now.strftime('%d-%m')}_{effective_session_name}"

    embedding = REDUCTION_METHODS[config.reduction_method](X, params)

    # Same quantity regress_out_volume uses below - computed unconditionally (not just
    # when regress_out_volume is set) since it's also the Volume coloring for the plots.
    lesion_volume_voxels = X.sum(axis=1)

    # Separate embedding for visualization only (2 or 3 components, config.viz_n_components) -
    # reused as-is when it already matches (every production config today: both are 2, zero
    # extra cost); refit from raw X otherwise, since slicing embedding[:, :viz_n_components]
    # out of a higher-dimensional umap/tsne/pacmap fit is not a meaningful projection (see
    # src/analysis/reduction.py::embedding_for_viz's docstring). Computed before
    # regress_out_volume below so both the saved and the plotted embedding get the same
    # treatment.
    viz_embedding = embedding_for_viz(config.reduction_method, X, params, embedding, config.viz_n_components)
    viz_is_saved_embedding = viz_embedding is embedding

    if config.regress_out_volume:
        # X is binary (0/1 per voxel); a row's voxel count is exactly proportional to its
        # lesion volume in ml, and OLS residuals are invariant to that scalar rescaling.
        embedding = regress_out_covariate(embedding, lesion_volume_voxels)
        viz_embedding = embedding if viz_is_saved_embedding else regress_out_covariate(viz_embedding, lesion_volume_voxels)
        logging.info("regressed out lesion volume (voxel count) from both the saved and visualization embeddings")

    try:
        metadata_out = enrich_metadata_with_lesion_info(metadata, X)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    try:
        save_matrix(
            output_dir,
            embedding,
            metadata_out,
            _build_readme_lines(config, X, embedding, params, now),
            overwrite=config.overwrite,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("embedding written to %s (shape %s)", output_dir, embedding.shape)

    xlabel, ylabel = f"{config.reduction_method} dim 1", f"{config.reduction_method} dim 2"
    zlabel = f"{config.reduction_method} dim 3" if viz_embedding.shape[1] == 3 else None
    write_embedding_plots(
        viz_embedding,
        metadata_out,
        X,
        list(config.color_by),
        output_dir,
        xlabel,
        ylabel,
        lambda label: compose_embedding_plot_title(output_dir, config.reduction_method, label.capitalize() if label else None),
        zlabel=zlabel,
    )

    try:
        append_run_log_entry(
            config.output_root / "production" / config.reduction_method,
            effective_session_name,
            now,
            "production",
            params,
            output_dir,
            config.run_notes,
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
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    # Only when embeddings are actually being persisted (save_tuning_embeddings):
    # a future replot of embeddings.npz needs metadata.csv self-contained (literal
    # lesion_volume_voxels/lesion_side/nihss columns), the same enrichment
    # _run_production always applies, so it never has to reload X or hit the
    # participants.tsv registry again. Every other tuning run (the default,
    # save_tuning_embeddings=False) keeps metadata exactly as loaded - unchanged
    # behavior, since embeddings_grid_*.png's own color modes already compute
    # side/nihss/volume live (src/analysis/embedding_coloring.py) without needing
    # this enrichment.
    if config.save_tuning_embeddings:
        try:
            metadata = enrich_metadata_with_lesion_info(metadata, X)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

    try:
        results, embeddings_by_combo = run_tuning_sweep(method, X, params, tuning_grid, trustworthiness_n_neighbors)
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

    try:
        append_run_log_entry(
            config.output_root / "tuning" / config.reduction_method,
            config.session_name,
            now,
            "tuning",
            {"base_params": params, "tuning_grid": tuning_grid},
            output_dir,
            config.run_notes,
        )
    except OSError as exc:
        logging.error("cannot write run log: %s", exc, exc_info=True)
        return 1

    logging.info("done - tuning results written to %s, log written to %s", output_dir, log_path)
    return 0


def _tuning_output_dir(config: DimReductionConfig, now: datetime) -> Path:
    return config.output_root / "tuning" / config.reduction_method / f"{now.strftime('%d-%m')}_{config.session_name}"





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
            output_dir, results, embeddings_by_combo, base_params, tuning_grid, nested_params, free_params, config, X, metadata
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
        "",
        "Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png (or the per-leaf "
        "embeddings_grid_*.png) and pick parameters by hand.",
    ]
    (output_dir / "config.md").write_text("\n".join(readme_lines) + "\n")


def _combo_key(keys: list[str], combo: tuple) -> str:
    """Self-describing string key for one tuning combination, e.g.
    'metric=jaccard,n_components=5,regress_out_volume=False,n_neighbors=15,min_dist=0.1' -
    same names/order as tuning_grid.keys() for that run (matches embeddings_by_combo's
    own combo tuple, see run_tuning_sweep), so it's identical, character for character, to
    the string a caller rebuilds from that same row's own values in tuning_results.csv
    (str(bool) is 'True'/'False', same as pandas' own CSV serialization) - no separate
    index file needed to join the two.
    """
    return ",".join(f"{key}={value}" for key, value in zip(keys, combo))


def _write_tuning_embeddings(output_dir: Path, embeddings_by_combo: dict[tuple, np.ndarray], keys: list[str]) -> None:
    """Serializes every combination's embedding actually computed by the sweep
    (not just the ones shown in embeddings_grid_*.png - the full Cartesian
    product minus any VolumeRegressionIncompatibleError exclusions) into a
    single embeddings.npz, keyed by _combo_key. Opt-in via
    config.save_tuning_embeddings - before this flag existed no tuning run
    ever wrote this file, so it stays off by default (code_standards.md
    §0/§5: no silent change to an existing run's output shape).
    """
    arrays = {_combo_key(keys, combo): embedding for combo, embedding in embeddings_by_combo.items()}
    np.savez(output_dir / "embeddings.npz", **arrays)


# embeddings_grid.png is a static-only diagnostic (no interactive counterpart) - always 2
# components regardless of config.viz_n_components, which governs production/interactive
# plots that can legitimately be 3D (see plot_embedding_grid_blocks, 2D-only by construction).
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
    X: np.ndarray,
    metadata: pd.DataFrame,
) -> None:
    """Groups `results` by nested_params (one subfolder per real combination
    actually present - an invalid combo excluded upstream by run_tuning_sweep,
    e.g. metric=jaccard + regress_out_volume=True, never produces a group
    here, so no empty folder is ever created for it), writing each leaf's own
    filtered tuning_results.csv plus, unless `config.write_embeddings_grid` is
    False, embeddings_grid_<color>.png (see
    src/analysis/embedding_plots.py::write_embedding_grid): one row per free
    parameter, holding every other free parameter at base_params' own value.

    `write_embeddings_grid=False` is a manual opt-out, not an automatic one -
    when a leaf's own n_components differs from _TUNING_GRID_N_COMPONENTS,
    _build_grid_blocks refits at 2 components for the plot, and that refit
    uses the exact same metric/n_neighbors/min_dist/random_state as whatever
    other leaf already swept those same free-parameter values at
    n_components=2 - with a fixed random_state, umap/tsne are deterministic,
    so the two are pixel-identical, not just visually similar. Skip the flag
    (leave it True) unless you already know this run's tuning_grid has no
    n_components=_TUNING_GRID_N_COMPONENTS leaf to be redundant with - the
    refit is otherwise the only way to see this leaf's neighborhood structure
    in 2D at all.
    """
    keys = list(tuning_grid.keys())
    for group_key, group in results.groupby(nested_params, sort=False):
        raw_values = group_key if isinstance(group_key, tuple) else (group_key,)
        leaf = {name: (value.item() if hasattr(value, "item") else value) for name, value in zip(nested_params, raw_values)}

        leaf_dir = output_dir
        for name in nested_params:
            leaf_dir = leaf_dir / f"{name}={leaf[name]}"
        leaf_dir.mkdir(parents=True, exist_ok=True)
        group.to_csv(leaf_dir / "tuning_results.csv", index=False)

        if not config.write_embeddings_grid:
            continue

        blocks = _build_grid_blocks(free_params, tuning_grid, keys, leaf, base_params, embeddings_by_combo, config, X)
        leaf_title = compose_tuning_leaf_title(output_dir, config.reduction_method, leaf)
        write_embedding_grid(
            blocks,
            metadata,
            X,
            list(config.color_by),
            leaf_dir,
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
    config: DimReductionConfig,
    X: np.ndarray,
) -> list[tuple[str, list[tuple[str, np.ndarray]]]]:
    """For each free parameter, one cell per value it can take - every other
    free parameter held at base_params' own value (must be one of that
    parameter's own tuning_grid values, else raises: the embedding for that
    exact combination was never computed by run_tuning_sweep - fix by adding
    the base_params value to that parameter's tuning_grid list). Each cell's
    embedding is reduced to _TUNING_GRID_N_COMPONENTS via embedding_for_viz
    when the combination's own n_components differs (e.g. a leaf whose
    n_components is itself in nested_params, or is a free parameter with a
    swept value other than 2) - the sweep's own embeddings are at whatever
    dimensionality that combination actually used.
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
            combo_params = {**base_params, **dict(zip(keys, combo))}
            # regress_out_volume is a pipeline-level post-fit step, never a
            # REDUCTION_METHODS constructor argument - strip it before
            # embedding_for_viz forwards params straight into e.g. umap.UMAP(**params).
            regress_out_volume_for_combo = combo_params.get("regress_out_volume", False)
            reduction_params_for_combo = {k: v for k, v in combo_params.items() if k != "regress_out_volume"}
            viz_embedding = embedding_for_viz(
                config.reduction_method, X, reduction_params_for_combo, embedding, _TUNING_GRID_N_COMPONENTS
            )
            if viz_embedding is not embedding and regress_out_volume_for_combo:
                # A refit (not the reused-as-is case) never went through
                # run_tuning_sweep's own regress_out_volume step - apply it
                # here too, so the plotted embedding matches what was scored.
                viz_embedding = regress_out_covariate(viz_embedding, X.sum(axis=1))
            cells.append((str(value), viz_embedding))
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
        "regress_out_volume": config.regress_out_volume,
        "color_by": list(config.color_by),
        "viz_n_components": config.viz_n_components,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict) -> list[str]:
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
        f"Params used: {json.dumps(params)}",
    ]


def _build_readme_lines(
    config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict, now: datetime
) -> list[str]:
    return [f"# {config.project} dim_reduction ({config.reduction_method}) — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, X, embedding, params
    )


def _log_path(config: DimReductionConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
