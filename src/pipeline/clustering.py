"""CLI entry point: cluster an already-built feature matrix directly, no reduction.

Usage:
    python -m src.pipeline.clustering --config config/pipelines/clustering.json

Reads a matrix artifact (input_path must already exist), clusters it as-is
with every method in clustering_methods (one or more), and writes a new
artifact per method: the same matrix (unchanged - clustering doesn't
transform the feature space) as matrix.npy, cluster_label appended to
metadata.csv, a static 2D scatter plot of the first 2 raw features colored
by cluster (cluster_plot.png) - a coarse sanity check only, since those 2
features are not a meaningful projection (no reduction happened) - and an
interactive HTML version (cluster_plot_interactive.html) with a dropdown to
switch coloring between cluster and dataset, hover showing every metadata
column per point. When more than one method is requested, an additional
side-by-side comparison plot is written to
<output_root>/comparison/<dd-mm>_<session_name>/cluster_comparison.png.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.model_config import ClusteringConfig, load_clustering_config
from src.analysis.params import load_method_params
from src.analysis.plotting import compose_run_title, plot_clusters_2d, plot_clusters_comparison, plot_clusters_interactive
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

REPORTS_ROOT = Path("reports") / "clustering"
LOGS_ROOT = Path("logs") / "clustering"
REPORT_FILENAME_PREFIX = "clustering_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cluster a feature matrix directly with one or more configured methods.")
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
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    labels_by_method: dict[str, np.ndarray] = {}
    for method in config.clustering_methods:
        cluster_labels = _run_one_method(config, method, X, metadata, now)
        if cluster_labels is None:
            return 1
        labels_by_method[method] = cluster_labels

    if X.shape[1] >= 2:
        comparison_dir = _comparison_dir(config, now)
        plot_clusters_comparison(
            X[:, :2],
            labels_by_method,
            comparison_dir / "cluster_comparison.png",
            xlabel="feature 0 (raw)",
            ylabel="feature 1 (raw)",
            suptitle=compose_run_title(comparison_dir, config.project),
        )
        _write_comparison_readme(comparison_dir, config, now)
        logging.info("comparison plot written to %s", comparison_dir / "cluster_comparison.png")
    else:
        logging.warning("matrix has only %d feature(s) - skipping cluster_comparison.png (needs at least 2)", X.shape[1])

    logging.info("done - all %d method(s) written under %s, log written to %s", len(config.clustering_methods), config.output_root, log_path)
    return 0


def _run_one_method(
    config: ClusteringConfig, method: str, X: np.ndarray, metadata: pd.DataFrame, now: datetime
) -> np.ndarray | None:
    """Runs one clustering method end to end (params, artifact, plot, report,
    runs.csv). Returns the cluster_labels actually saved (for the comparison
    plot to reuse verbatim, rather than re-running the method a second time),
    or None if this method's run failed - the caller stops the whole run.
    """
    try:
        params, tag = load_method_params(config.params_file, method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return None

    cluster_labels = CLUSTERING_METHODS[method](X, params)

    metadata_out = metadata.copy()
    metadata_out["cluster_label"] = cluster_labels
    
    effective_session_name = f"{config.session_name}_{tag}" if tag else config.session_name
    output_dir = config.output_root / method / f"{now.strftime('%d-%m')}_{effective_session_name}"
    
    try:
        save_matrix(
            output_dir,
            X,
            metadata_out,
            _build_readme_lines(config, method, X, cluster_labels, params, now),
            overwrite=config.overwrite,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return None
    logging.info("[%s] clustered matrix written to %s (shape %s)", method, output_dir, X.shape)

    if X.shape[1] >= 2:
        plot_title = compose_run_title(output_dir, config.project)

        plot_clusters_2d(
            X[:, :2],
            cluster_labels,
            output_dir / "cluster_plot.png",
            xlabel="feature 0 (raw)",
            ylabel="feature 1 (raw)",
            title=plot_title,
        )
        logging.info("[%s] cluster plot written to %s", method, output_dir / "cluster_plot.png")

        plot_clusters_interactive(
            X[:, :2],
            metadata_out,
            output_dir / "cluster_plot_interactive.html",
            xlabel="feature 0 (raw)",
            ylabel="feature 1 (raw)",
            title=plot_title,
        )
        logging.info("[%s] interactive cluster plot written to %s", method, output_dir / "cluster_plot_interactive.html")
    else:
        logging.warning(
            "[%s] matrix has only %d feature(s) - skipping cluster_plot.png/cluster_plot_interactive.html (needs at least 2)",
            method,
            X.shape[1],
        )

    try:
        report_path = _write_report(config, method, X, cluster_labels, params, now)
        append_run_log_entry(
            _runs_csv_path(config, method), effective_session_name, now, "production", params, output_dir, config.run_notes
        )
    except OSError as exc:
        logging.error("[%s] cannot write report/run log: %s", method, exc, exc_info=True)
        return None

    logging.info("[%s] done - output written to %s, report written to %s", method, output_dir, report_path)
    return cluster_labels


def _comparison_dir(config: ClusteringConfig, now: datetime) -> Path:
    return config.output_root / "comparison" / f"{now.strftime('%d-%m')}_{config.session_name}"


def _runs_csv_path(config: ClusteringConfig, method: str) -> Path:
    return config.output_root / method / "runs.csv"


def _config_summary(config: ClusteringConfig, method: str) -> str:
    payload = {
        "project": config.project,
        "input_path": str(config.input_path),
        "clustering_method": method,
        "clustering_methods_requested": list(config.clustering_methods),
        "params_file": str(config.params_file),
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(config: ClusteringConfig, method: str, X: np.ndarray, cluster_labels: np.ndarray, params: dict) -> list[str]:
    return [
        "## Config",
        "",
        "```json",
        _config_summary(config, method),
        "```",
        "",
        "## Summary",
        "",
        f"Matrix shape: {X.shape[0]} subjects x {X.shape[1]} features",
        _clusters_found_line(cluster_labels),
        f"Params used: {json.dumps(params)}",
    ]


def _clusters_found_line(cluster_labels: np.ndarray) -> str:
    """"Clusters found: N" - excludes DBSCAN/OPTICS-style noise label -1 from
    the cluster count (counting it as a cluster would silently overstate the
    result); reports the noise count separately when present, for any method.
    """
    noise_mask = cluster_labels == -1
    n_clusters = int(np.unique(cluster_labels[~noise_mask]).shape[0])
    line = f"Clusters found: {n_clusters}"
    if noise_mask.any():
        line += f" (+ {int(noise_mask.sum())} noise points, label -1)"
    return line


def _build_readme_lines(
    config: ClusteringConfig, method: str, X: np.ndarray, cluster_labels: np.ndarray, params: dict, now: datetime
) -> list[str]:
    title = f"# {config.project} clustering ({method}) — {now.strftime('%d-%m-%y %H:%M')}"
    return [title, ""] + _summary_lines(config, method, X, cluster_labels, params)


def _build_report(
    config: ClusteringConfig, method: str, X: np.ndarray, cluster_labels: np.ndarray, params: dict, now: datetime
) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')} ({method})", ""] + _summary_lines(
        config, method, X, cluster_labels, params
    )
    return "\n".join(lines)


def _write_report(
    config: ClusteringConfig, method: str, X: np.ndarray, cluster_labels: np.ndarray, params: dict, now: datetime
) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    # method in the filename: multiple methods share the same `now` in one run,
    # so without it the 2nd method's report would silently overwrite the 1st's.
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{method}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, method, X, cluster_labels, params, now))
    return report_path


def _write_comparison_readme(comparison_dir: Path, config: ClusteringConfig, now: datetime) -> None:
    dated_run = f"{now.strftime('%d-%m')}_{config.session_name}"
    lines = [
        f"# {config.project} clustering method comparison — {now.strftime('%d-%m-%y %H:%M')}",
        "",
        f"Methods compared: {list(config.clustering_methods)}",
        "",
        "Individual outputs:",
    ]
    lines += [f"- `{config.output_root / m / dated_run}`" for m in config.clustering_methods]
    comparison_dir.mkdir(parents=True, exist_ok=True)
    (comparison_dir / "config.md").write_text("\n".join(lines) + "\n")


def _log_path(config: ClusteringConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
