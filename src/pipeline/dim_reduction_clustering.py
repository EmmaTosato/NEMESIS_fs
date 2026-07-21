"""CLI entry point: reduce then cluster an already-built feature matrix.

Usage:
    python -m src.pipeline.dim_reduction_clustering --config config/pipelines/dim_reduction_clustering.json

Reads a matrix artifact (input_path must already exist), embeds it once with
the configured reduction method, then clusters that same embedding (not the
raw matrix) with every method in clustering_methods (one or more). Each
method writes its own artifact: the embedding as matrix.npy, cluster_label
appended to metadata.csv, a static 2D scatter plot colored by cluster
(cluster_plot.png) for a first visual sanity check, and an interactive HTML
version (cluster_plot_interactive.html) with a dropdown to switch coloring
between cluster and dataset, hover showing every metadata column per point.
When more than one clustering method is requested, an additional side-by-side
comparison plot is written to
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
from src.analysis.model_config import DimReductionClusteringConfig, load_dim_reduction_clustering_config
from src.analysis.params import load_method_params
from src.analysis.plotting import compose_run_title, plot_clusters_2d, plot_clusters_comparison, plot_clusters_interactive
from src.analysis.reduction import REDUCTION_METHODS
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

REPORTS_ROOT = Path("reports") / "dim_reduction_clustering"
LOGS_ROOT = Path("logs") / "dim_reduction_clustering"
REPORT_FILENAME_PREFIX = "dim_reduction_clustering_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reduce once, then cluster the embedding with one or more configured methods.")
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
        reduction_params, reduction_tag = load_method_params(config.reduction_params_file, config.reduction_method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    embedding = REDUCTION_METHODS[config.reduction_method](X, reduction_params)
    
    effective_reduction_session = f"{config.session_name}_{reduction_tag}" if reduction_tag else config.session_name

    labels_by_method: dict[str, np.ndarray] = {}
    for method in config.clustering_methods:
        cluster_labels = _run_one_method(config, method, X, embedding, metadata, reduction_params, reduction_tag, now)
        if cluster_labels is None:
            return 1
        labels_by_method[method] = cluster_labels

    if embedding.shape[1] >= 2:
        comparison_dir = config.output_root / "comparison" / f"{now.strftime('%d-%m')}_{effective_reduction_session}"
        plot_clusters_comparison(
            embedding[:, :2],
            labels_by_method,
            comparison_dir / "cluster_comparison.png",
            xlabel=f"{config.reduction_method} dim 1",
            ylabel=f"{config.reduction_method} dim 2",
            suptitle=compose_run_title(comparison_dir, config.project),
        )
        
        lines = [
            f"# {config.project} dim_reduction_clustering method comparison "
            f"({config.reduction_method}) — {now.strftime('%d-%m-%y %H:%M')}",
            "",
            f"Reduction method: {config.reduction_method}",
            f"Clustering methods compared: {list(config.clustering_methods)}",
            "",
            "Individual outputs:",
        ]
        lines += [f"- `{config.output_root / _method_dir(config, m)}`" for m in config.clustering_methods]
        comparison_dir.mkdir(parents=True, exist_ok=True)
        (comparison_dir / "config.md").write_text("\n".join(lines) + "\n")
        
        logging.info("comparison plot written to %s", comparison_dir / "cluster_comparison.png")
    else:
        logging.warning(
            "embedding has only %d component(s) - skipping cluster_comparison.png (needs at least 2)", embedding.shape[1]
        )

    logging.info(
        "done - all %d method(s) written under %s, log written to %s", len(config.clustering_methods), config.output_root, log_path
    )
    return 0


def _run_one_method(
    config: DimReductionClusteringConfig,
    method: str,
    X: np.ndarray,
    embedding: np.ndarray,
    metadata: pd.DataFrame,
    reduction_params: dict,
    reduction_tag: str | None,
    now: datetime,
) -> np.ndarray | None:
    """Runs one clustering method on the (already computed once) embedding -
    artifact, plot, report, runs.csv. Returns the cluster_labels actually
    saved (for the comparison plot to reuse verbatim), or None on failure -
    the caller stops the whole run.
    """
    try:
        clustering_params, clustering_tag = load_method_params(config.clustering_params_file, method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return None

    cluster_labels = CLUSTERING_METHODS[method](embedding, clustering_params)

    metadata_out = metadata.copy()
    metadata_out["cluster_label"] = cluster_labels
    
    tags = [t for t in (reduction_tag, clustering_tag) if t]
    effective_session_name = config.session_name + ("_" + "_".join(tags) if tags else "")

    output_dir = config.output_root / _method_dir(config, method) / f"{now.strftime('%d-%m')}_{effective_session_name}"
    try:
        save_matrix(
            output_dir,
            embedding,
            metadata_out,
            _build_readme_lines(config, method, X, embedding, cluster_labels, reduction_params, clustering_params, now),
            overwrite=config.overwrite,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return None
    logging.info("[%s] embedding+clusters written to %s (shape %s)", method, output_dir, embedding.shape)

    if embedding.shape[1] >= 2:
        plot_title = compose_run_title(output_dir, config.project)

        plot_clusters_2d(
            embedding[:, :2],
            cluster_labels,
            output_dir / "cluster_plot.png",
            xlabel=f"{config.reduction_method} dim 1",
            ylabel=f"{config.reduction_method} dim 2",
            title=plot_title,
        )
        logging.info("[%s] cluster plot written to %s", method, output_dir / "cluster_plot.png")

        plot_clusters_interactive(
            embedding[:, :2],
            metadata_out,
            output_dir / "cluster_plot_interactive.html",
            xlabel=f"{config.reduction_method} dim 1",
            ylabel=f"{config.reduction_method} dim 2",
            title=plot_title,
        )
        logging.info("[%s] interactive cluster plot written to %s", method, output_dir / "cluster_plot_interactive.html")
    else:
        logging.warning(
            "[%s] embedding has only %d component(s) - skipping cluster_plot.png/cluster_plot_interactive.html (needs at least 2)",
            method,
            embedding.shape[1],
        )

    try:
        report_path = _write_report(config, method, X, embedding, cluster_labels, reduction_params, clustering_params, now)
        append_run_log_entry(
            _runs_csv_path(config, method),
            effective_session_name,
            now,
            "production",
            {"reduction_params": reduction_params, "clustering_params": clustering_params},
            output_dir,
            config.run_notes,
        )
    except OSError as exc:
        logging.error("[%s] cannot write report/run log: %s", method, exc, exc_info=True)
        return None

    logging.info("[%s] done - output written to %s, report written to %s", method, output_dir, report_path)
    return cluster_labels


def _comparison_dir(config: DimReductionClusteringConfig, now: datetime) -> Path:
    return config.output_root / "comparison" / f"{now.strftime('%d-%m')}_{config.session_name}"


def _method_dir(config: DimReductionClusteringConfig, method: str) -> str:
    return f"{config.reduction_method}-{method}"


def _runs_csv_path(config: DimReductionClusteringConfig, method: str) -> Path:
    return config.output_root / _method_dir(config, method) / "runs.csv"


def _config_summary(config: DimReductionClusteringConfig, method: str) -> str:
    payload = {
        "project": config.project,
        "input_path": str(config.input_path),
        "reduction_method": config.reduction_method,
        "reduction_params_file": str(config.reduction_params_file),
        "clustering_method": method,
        "clustering_methods_requested": list(config.clustering_methods),
        "clustering_params_file": str(config.clustering_params_file),
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(
    config: DimReductionClusteringConfig,
    method: str,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
) -> list[str]:
    return [
        "## Config",
        "",
        "```json",
        _config_summary(config, method),
        "```",
        "",
        "## Summary",
        "",
        f"Input matrix shape: {X.shape[0]} subjects x {X.shape[1]} features",
        f"Embedding shape: {embedding.shape[0]} subjects x {embedding.shape[1]} components",
        _clusters_found_line(cluster_labels),
        f"Reduction params used: {json.dumps(reduction_params)}",
        f"Clustering params used: {json.dumps(clustering_params)}",
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
    config: DimReductionClusteringConfig,
    method: str,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
    now: datetime,
) -> list[str]:
    title = f"# {config.project} dim_reduction_clustering ({config.reduction_method}+{method}) — {now.strftime('%d-%m-%y %H:%M')}"
    return [title, ""] + _summary_lines(config, method, X, embedding, cluster_labels, reduction_params, clustering_params)


def _build_report(
    config: DimReductionClusteringConfig,
    method: str,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
    now: datetime,
) -> str:
    lines = [
        f"# {config.project}_{now.strftime('%d-%m-%y')}",
        f"## {now.strftime('%H:%M')} ({config.reduction_method}+{method})",
        "",
    ] + _summary_lines(config, method, X, embedding, cluster_labels, reduction_params, clustering_params)
    return "\n".join(lines)


def _write_report(
    config: DimReductionClusteringConfig,
    method: str,
    X: np.ndarray,
    embedding: np.ndarray,
    cluster_labels: np.ndarray,
    reduction_params: dict,
    clustering_params: dict,
    now: datetime,
) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    # method in the filename: multiple methods share the same `now` in one
    # run, so without it the 2nd method's report would silently overwrite the 1st's.
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{method}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(
        _build_report(config, method, X, embedding, cluster_labels, reduction_params, clustering_params, now)
    )
    return report_path


def _write_comparison_readme(comparison_dir: Path, config: DimReductionClusteringConfig, now: datetime) -> None:
    dated_run = f"{now.strftime('%d-%m')}_{config.session_name}"
    lines = [
        f"# {config.project} dim_reduction_clustering method comparison "
        f"({config.reduction_method}) — {now.strftime('%d-%m-%y %H:%M')}",
        "",
        f"Reduction method: {config.reduction_method}",
        f"Clustering methods compared: {list(config.clustering_methods)}",
        "",
        "Individual outputs:",
    ]
    lines += [f"- `{config.output_root / _method_dir(config, m) / dated_run}`" for m in config.clustering_methods]
    comparison_dir.mkdir(parents=True, exist_ok=True)
    (comparison_dir / "config.md").write_text("\n".join(lines) + "\n")


def _log_path(config: DimReductionClusteringConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
