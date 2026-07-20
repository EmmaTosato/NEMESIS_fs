"""CLI entry point: reduce then cluster an already-built feature matrix.

Usage:
    python -m src.pipeline.dim_reduction_clustering --config config/pipelines/dim_reduction_clustering.json

Reads a matrix artifact (input_path must already exist), embeds it with the
configured reduction method, clusters the embedding (not the raw matrix)
with the configured clustering method, and writes a new artifact: the
embedding as matrix.npy, cluster_label appended to metadata.csv, plus a basic
2D scatter plot (first 2 embedding dimensions, colored by cluster) for a
first visual sanity check.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.model_config import DimReductionClusteringConfig, load_dim_reduction_clustering_config
from src.analysis.params import load_method_params
from src.analysis.plotting import plot_clusters_2d
from src.analysis.reduction import REDUCTION_METHODS
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler

REPORTS_ROOT = Path("reports") / "dim_reduction_clustering"
LOGS_ROOT = Path("logs") / "dim_reduction_clustering"
REPORT_FILENAME_PREFIX = "dim_reduction_clustering_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reduce then cluster a feature matrix with configured methods.")
    parser.add_argument("--config", required=True, help="Path to a dim_reduction_clustering.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_dim_reduction_clustering_config(args.config)
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
        reduction_params = load_method_params(config.reduction_params_file, config.reduction_method)
        clustering_params = load_method_params(config.clustering_params_file, config.clustering_method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    embedding = REDUCTION_METHODS[config.reduction_method](X, reduction_params)
    cluster_labels = CLUSTERING_METHODS[config.clustering_method](embedding, clustering_params)

    metadata_out = metadata.copy()
    metadata_out["cluster_label"] = cluster_labels

    output_dir = _output_dir(config, now)
    try:
        save_matrix(
            output_dir,
            embedding,
            metadata_out,
            _build_readme_lines(config, X, embedding, cluster_labels, reduction_params, clustering_params, now),
            overwrite=config.overwrite,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("embedding+clusters written to %s (shape %s)", output_dir, embedding.shape)

    if embedding.shape[1] >= 2:
        plot_clusters_2d(
            embedding[:, :2],
            cluster_labels,
            output_dir / "cluster_plot.png",
            xlabel=f"{config.reduction_method} dim 1",
            ylabel=f"{config.reduction_method} dim 2",
            title=f"{config.project} — {config.reduction_method} + {config.clustering_method}",
        )
        logging.info("cluster plot written to %s", output_dir / "cluster_plot.png")
    else:
        logging.warning(
            "embedding has only %d component(s) - skipping cluster_plot.png (needs at least 2)", embedding.shape[1]
        )

    try:
        report_path = _write_report(config, X, embedding, cluster_labels, reduction_params, clustering_params, now)
    except OSError as exc:
        logging.error("cannot write report: %s", exc, exc_info=True)
        return 1

    logging.info(
        "done - output written to %s, report written to %s, log written to %s", output_dir, report_path, log_path
    )
    return 0


def _output_dir(config: DimReductionClusteringConfig, now: datetime) -> Path:
    method_dir = f"{config.reduction_method}-{config.clustering_method}"
    return config.output_root / method_dir / f"{now.strftime('%d-%m')}_{config.run_name}"


def _config_summary(config: DimReductionClusteringConfig) -> str:
    payload = {
        "project": config.project,
        "input_path": str(config.input_path),
        "reduction_method": config.reduction_method,
        "reduction_params_file": str(config.reduction_params_file),
        "clustering_method": config.clustering_method,
        "clustering_params_file": str(config.clustering_params_file),
        "output_root": str(config.output_root),
        "run_name": config.run_name,
        "overwrite": config.overwrite,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(
    config: DimReductionClusteringConfig,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
) -> list[str]:
    n_clusters = int(np.unique(cluster_labels).shape[0])
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
        f"Clusters found: {n_clusters}",
        f"Reduction params used: {json.dumps(reduction_params)}",
        f"Clustering params used: {json.dumps(clustering_params)}",
    ]


def _build_readme_lines(
    config: DimReductionClusteringConfig,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
    now: datetime,
) -> list[str]:
    title = f"# {config.project} dim_reduction_clustering ({config.reduction_method}+{config.clustering_method}) — {now.strftime('%d-%m-%y %H:%M')}"
    return [title, ""] + _summary_lines(config, X, embedding, cluster_labels, reduction_params, clustering_params)


def _build_report(
    config: DimReductionClusteringConfig,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
    now: datetime,
) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')}", ""] + _summary_lines(
        config, X, embedding, cluster_labels, reduction_params, clustering_params
    )
    return "\n".join(lines)


def _write_report(
    config: DimReductionClusteringConfig,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
    now: datetime,
) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, X, embedding, cluster_labels, reduction_params, clustering_params, now))
    return report_path


def _log_path(config: DimReductionClusteringConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
