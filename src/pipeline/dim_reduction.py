"""CLI entry point: apply a dimensionality-reduction method to an already-built feature matrix.

Usage:
    python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json

Reads a matrix artifact written by build_lesion_matrix.py (input_path must
already exist - no auto-build fallback). Two modes, chosen by `fine_tuning`:

- fine_tuning=false (production): embeds with the method's "params" from
  params_reduction.json, writes a normal matrix artifact holding the
  embedding. metadata gains 2 columns not present on input:
  lesion_volume_voxels (X.sum(axis=1), the same per-subject voxel count
  regress_out_volume already uses) and lesion_side (src/features/clinical.py's
  join_lesion_side, "unknown" for a subject/dataset the source participants.tsv
  can't resolve) - both exist to color embedding_plot_volume.*/embedding_plot_side.*
  (see plotting.py) and are persisted, not just computed ad hoc, so
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

Both modes append an entry to <output_root>/<method>/runs.csv - a
chronological, human-readable history of every run (tuning or production)
for that method, distinct from any single run's own config.md (see
docs/dev/analysis.md).
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.covariates import check_volume_regression_compatible, regress_out_covariate
from src.analysis.model_config import DimReductionConfig, load_dim_reduction_config
from src.analysis.params import load_method_params, load_trustworthiness_n_neighbors, load_tuning_grid
from src.analysis.plotting import (
    compose_embedding_plot_title,
    compose_run_title,
    plot_embedding_2d,
    plot_embedding_categorical,
    plot_embedding_continuous,
    plot_embedding_interactive,
    plot_tuning_curve,
)
from src.analysis.reduction import REDUCTION_METHODS
from src.analysis.tuning import METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS, TUNING_METRIC_NAMES, run_tuning_sweep
from src.features.clinical import join_lesion_side
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
        return _run_fine_tuning(config, X, now, log_path)
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
    output_dir = config.output_root / config.reduction_method / f"{now.strftime('%d-%m')}_{effective_session_name}"

    embedding = REDUCTION_METHODS[config.reduction_method](X, params)

    # Same quantity regress_out_volume uses below - computed unconditionally (not just
    # when regress_out_volume is set) since it's also the Volume coloring for the plots.
    lesion_volume_voxels = X.sum(axis=1)

    if config.regress_out_volume:
        # X is binary (0/1 per voxel); a row's voxel count is exactly proportional to its
        # lesion volume in ml, and OLS residuals are invariant to that scalar rescaling.
        embedding = regress_out_covariate(embedding, lesion_volume_voxels)
        logging.info("regressed out lesion volume (voxel count) from the embedding before saving")

    try:
        lesion_side = join_lesion_side(metadata)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    metadata_out = metadata.copy()
    metadata_out["lesion_volume_voxels"] = lesion_volume_voxels
    metadata_out["lesion_side"] = lesion_side

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

    if embedding.shape[1] >= 2:
        xlabel, ylabel = f"{config.reduction_method} dim 1", f"{config.reduction_method} dim 2"

        try:
            plot_path = output_dir / "embedding_plot.png"
            plot_embedding_2d(
                embedding,
                plot_path,
                xlabel,
                ylabel,
                compose_embedding_plot_title(output_dir, config.reduction_method),
            )
            logging.info("embedding plot written to %s", plot_path)
        except Exception as exc:
            logging.warning("failed to generate embedding plot: %s", exc)

        for color_by, column in (("Dataset", "dataset"), ("Side", "lesion_side")):
            suffix = column.replace("lesion_", "")
            title = compose_embedding_plot_title(output_dir, config.reduction_method, color_by)
            try:
                plot_embedding_categorical(
                    embedding,
                    metadata_out[column].to_numpy(),
                    output_dir / f"embedding_plot_{suffix}.png",
                    xlabel,
                    ylabel,
                    title,
                    legend_title=column,
                )
                logging.info("%s embedding plot written to %s", color_by.lower(), output_dir / f"embedding_plot_{suffix}.png")
            except Exception as exc:
                logging.warning("failed to generate %s embedding plot: %s", color_by.lower(), exc)

            try:
                interactive_path = output_dir / f"embedding_plot_{suffix}.html"
                plot_embedding_interactive(embedding, metadata_out, interactive_path, xlabel, ylabel, title, color_column=column)
                logging.info("interactive %s embedding plot written to %s", color_by.lower(), interactive_path)
            except Exception as exc:
                logging.warning("failed to generate interactive %s embedding plot: %s", color_by.lower(), exc)

        volume_title = compose_embedding_plot_title(output_dir, config.reduction_method, "Volume")
        try:
            plot_embedding_continuous(
                embedding,
                lesion_volume_voxels,
                output_dir / "embedding_plot_volume.png",
                xlabel,
                ylabel,
                volume_title,
                colorbar_label="lesion volume (voxels)",
            )
            logging.info("volume embedding plot written to %s", output_dir / "embedding_plot_volume.png")
        except Exception as exc:
            logging.warning("failed to generate volume embedding plot: %s", exc)

        try:
            interactive_volume_path = output_dir / "embedding_plot_volume.html"
            plot_embedding_interactive(
                embedding, metadata_out, interactive_volume_path, xlabel, ylabel, volume_title, color_column="lesion_volume_voxels"
            )
            logging.info("interactive volume embedding plot written to %s", interactive_volume_path)
        except Exception as exc:
            logging.warning("failed to generate interactive volume embedding plot: %s", exc)

    try:
        append_run_log_entry(
            config.output_root / config.reduction_method,
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


def _run_fine_tuning(config: DimReductionConfig, X: np.ndarray, now: datetime, log_path: Path) -> int:
    method = config.reduction_method
    try:
        params, _ = load_method_params(config.params_file, method)
        tuning_grid = load_tuning_grid(config.params_file, method)
        trustworthiness_n_neighbors = (
            load_trustworthiness_n_neighbors(config.params_file, method)
            if method in METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS
            else None
        )
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    effective_session_name = config.session_name

    try:
        results = run_tuning_sweep(method, X, params, tuning_grid, trustworthiness_n_neighbors)
    except ValueError as exc:
        logging.error(str(exc))
        return 1

    output_dir = _tuning_output_dir(config, now)
    try:
        _write_tuning_output(output_dir, results, params, tuning_grid, TUNING_METRIC_NAMES[method], config, now, config.overwrite)
    except (FileExistsError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("tuning results written to %s (%d combinations evaluated)", output_dir, len(results))

    try:
        append_run_log_entry(
            config.output_root / config.reduction_method,
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
    return config.output_root / config.reduction_method / "tuning" / f"{now.strftime('%d-%m')}_{config.session_name}"





def _write_tuning_output(
    output_dir: Path,
    results: pd.DataFrame,
    base_params: dict,
    tuning_grid: dict[str, list],
    metric_col: str,
    config: DimReductionConfig,
    now: datetime,
    overwrite: bool,
) -> None:
    if output_dir.exists() and not overwrite:
        raise FileExistsError(
            f"output directory {output_dir} already exists and overwrite=False "
            "- set overwrite=True to replace it, or choose a different session_name"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "tuning_results.csv", index=False)

    swept_params = list(tuning_grid.keys())
    title = compose_run_title(output_dir, config.project)
    if len(swept_params) == 1:
        plot_tuning_curve(results, swept_params[0], metric_col, output_dir / "tuning_plot.png", title)
    else:
        logging.warning(
            "tuning_grid has %d swept parameters - no plot generated (heatmaps removed on request, "
            "only a 1-parameter curve is supported; tuning_results.csv still has every evaluated combination)",
            len(swept_params),
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
            },
            indent=2,
        ),
        "```",
        "",
        "## Summary",
        "",
        f"Swept parameters: {swept_params}",
        f"Combinations evaluated: {len(results)}",
        f"Metric: {metric_col}",
        "",
        "Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.",
    ]
    (output_dir / "config.md").write_text("\n".join(readme_lines) + "\n")


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
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
