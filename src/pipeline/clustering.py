"""CLI entry point: cluster an already-built feature matrix directly, no reduction.

Usage:
    python -m src.pipeline.clustering --config config/pipelines/clustering.json

Reads a matrix artifact (input_path must already exist), clusters it as-is
with the configured method, and writes a new artifact: the same matrix
(unchanged - clustering doesn't transform the feature space) as matrix.npy,
cluster_label appended to metadata.csv, plus a basic 2D scatter plot of the
first 2 raw features colored by cluster - a coarse sanity check only, since
those 2 features are not a meaningful projection (no reduction happened).
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.model_config import ClusteringConfig, load_clustering_config
from src.analysis.params import load_method_params
from src.analysis.plotting import plot_clusters_2d
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler

REPORTS_ROOT = Path("reports") / "clustering"
LOGS_ROOT = Path("logs") / "clustering"
REPORT_FILENAME_PREFIX = "clustering_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cluster a feature matrix directly with a configured method.")
    parser.add_argument("--config", required=True, help="Path to a clustering.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_clustering_config(args.config)
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
        params = load_method_params(config.params_file, config.clustering_method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    cluster_labels = CLUSTERING_METHODS[config.clustering_method](X, params)

    metadata_out = metadata.copy()
    metadata_out["cluster_label"] = cluster_labels

    output_dir = _output_dir(config, now)
    try:
        save_matrix(
            output_dir,
            X,
            metadata_out,
            _build_readme_lines(config, X, cluster_labels, params, now),
            overwrite=config.overwrite,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("clustered matrix written to %s (shape %s)", output_dir, X.shape)

    if X.shape[1] >= 2:
        plot_clusters_2d(
            X[:, :2],
            cluster_labels,
            output_dir / "cluster_plot.png",
            xlabel="feature 0 (raw)",
            ylabel="feature 1 (raw)",
            title=f"{config.project} — {config.clustering_method} (no reduction)",
        )
        logging.info("cluster plot written to %s", output_dir / "cluster_plot.png")
    else:
        logging.warning("matrix has only %d feature(s) - skipping cluster_plot.png (needs at least 2)", X.shape[1])

    try:
        report_path = _write_report(config, X, cluster_labels, params, now)
    except OSError as exc:
        logging.error("cannot write report: %s", exc, exc_info=True)
        return 1

    logging.info(
        "done - output written to %s, report written to %s, log written to %s", output_dir, report_path, log_path
    )
    return 0


def _output_dir(config: ClusteringConfig, now: datetime) -> Path:
    return config.output_root / config.clustering_method / f"{now.strftime('%d-%m')}_{config.run_name}"


def _config_summary(config: ClusteringConfig) -> str:
    payload = {
        "project": config.project,
        "input_path": str(config.input_path),
        "clustering_method": config.clustering_method,
        "params_file": str(config.params_file),
        "output_root": str(config.output_root),
        "run_name": config.run_name,
        "overwrite": config.overwrite,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(config: ClusteringConfig, X: np.ndarray, cluster_labels: np.ndarray, params: dict) -> list[str]:
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
        f"Matrix shape: {X.shape[0]} subjects x {X.shape[1]} features",
        f"Clusters found: {n_clusters}",
        f"Params used: {json.dumps(params)}",
    ]


def _build_readme_lines(
    config: ClusteringConfig, X: np.ndarray, cluster_labels: np.ndarray, params: dict, now: datetime
) -> list[str]:
    title = f"# {config.project} clustering ({config.clustering_method}) — {now.strftime('%d-%m-%y %H:%M')}"
    return [title, ""] + _summary_lines(config, X, cluster_labels, params)


def _build_report(config: ClusteringConfig, X: np.ndarray, cluster_labels: np.ndarray, params: dict, now: datetime) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')}", ""] + _summary_lines(
        config, X, cluster_labels, params
    )
    return "\n".join(lines)


def _write_report(config: ClusteringConfig, X: np.ndarray, cluster_labels: np.ndarray, params: dict, now: datetime) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, X, cluster_labels, params, now))
    return report_path


def _log_path(config: ClusteringConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
