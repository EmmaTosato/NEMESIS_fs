"""CLI entry point: cluster an already-built feature matrix directly, no reduction.

Usage:
    python -m src.pipeline.clustering --config config/pipelines/clustering.json

Reads a matrix artifact (input_path must already exist - either a raw/
parcellated matrix or an already-computed dim_reduction embedding, this
script doesn't care which). Two modes, chosen by `fine_tuning`, same
convention as dim_reduction.py:

- fine_tuning=false (production): clusters with every method in
  clustering_methods (one or more) using that method's "params" from
  params_clustering.json, writing a new artifact per method: the same
  matrix (unchanged - clustering doesn't transform the feature space) as
  matrix.npy, cluster_label appended to metadata.csv, a static 2D scatter
  plot of the first 2 raw features colored by cluster (cluster_plot.png) -
  a coarse sanity check only, since those 2 features are not a meaningful
  projection (no reduction happened) - an interactive HTML version
  (cluster_plot_interactive.html) with a dropdown to switch coloring
  between cluster and dataset, hover showing every metadata column per
  point, and a per-sample silhouette diagnostic (silhouette_plot.png,
  computed on the full matrix used for clustering, not just the 2 display
  features - see src/analysis/clustering_tuning.py::compute_silhouette_samples),
  skipped with a warning if the chosen result is degenerate (fewer than 2
  non-noise clusters). When more than one method is requested, an additional
  side-by-side comparison plot is written to
  <output_root>/comparison/<dd-mm>_<session_name>/cluster_comparison.png.
- fine_tuning=true (manual hyperparameter search, every method in
  clustering_methods, one sweep each over that method's "tuning_grid"):
  since clustering has no ground truth to score against, every combination
  is scored with 3 generic internal-validation indices (silhouette,
  Calinski-Harabasz, Davies-Bouldin - see src/analysis/clustering_tuning.py)
  plus a method-specific extra where one exists (kmeans' inertia, gmm's
  bic/aic). Writes tuning_results.csv + tuning_plot.png (one subplot per
  metric) to <output_root>/<method>/tuning/<dd-mm>_<session_name>/, plus a
  standalone diagnostic plot for the 2 methods that have one, independent of
  the swept grid: agglomerative's dendrogram.png, spectral's
  eigengap_plot.png. No automatic selection -
  a human reads the outputs and picks parameters by hand, writes them into
  params_clustering.json's "params", and re-runs with fine_tuning=false.

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

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_tuning import (
    CONSENSUS_METRIC_COLUMNS,
    METHOD_METRIC_COLUMNS,
    STANDALONE_DIAGNOSTIC_METHODS,
    compute_dendrogram_linkage,
    compute_eigengap,
    compute_silhouette_samples,
    consensus_suggestion_lines,
    run_clustering_tuning_sweep,
)
from src.analysis.model_config import ClusteringConfig, load_clustering_config
from src.analysis.params import load_consensus_config, load_method_params, load_tuning_grid
from src.analysis.plotting import (
    compose_comparison_title,
    compose_run_title,
    plot_clusters_2d,
    plot_clusters_comparison,
    plot_clusters_interactive,
    plot_clustering_tuning_heatmaps,
    plot_clustering_tuning_metrics,
    plot_dendrogram,
    plot_eigengap,
    plot_silhouette_analysis,
)
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

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

    if config.fine_tuning:
        return _run_fine_tuning(config, X, now, log_path)

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
            suptitle=compose_comparison_title(comparison_dir, None),
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
    """Runs one clustering method end to end (params, artifact, plot,
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

        try:
            sample_labels, sample_silhouette_values = compute_silhouette_samples(X, cluster_labels)
            plot_silhouette_analysis(
                sample_labels,
                sample_silhouette_values,
                X[:, :2],
                cluster_labels,
                output_dir / "silhouette_plot.png",
                xlabel="feature 0 (raw)",
                ylabel="feature 1 (raw)",
                title=plot_title,
            )
            logging.info("[%s] silhouette plot written to %s", method, output_dir / "silhouette_plot.png")
        except ValueError as exc:
            logging.warning("[%s] skipping silhouette_plot.png: %s", method, exc)
    else:
        logging.warning(
            "[%s] matrix has only %d feature(s) - skipping cluster_plot.png/cluster_plot_interactive.html (needs at least 2)",
            method,
            X.shape[1],
        )

    try:
        append_run_log_entry(
            _run_log_dir(config, method), effective_session_name, now, "production", params, output_dir, config.run_notes
        )
    except OSError as exc:
        logging.error("[%s] cannot write run log: %s", method, exc, exc_info=True)
        return None

    logging.info("[%s] done - output written to %s", method, output_dir)
    return cluster_labels


def _comparison_dir(config: ClusteringConfig, now: datetime) -> Path:
    return config.output_root / "comparison" / f"{now.strftime('%d-%m')}_{config.session_name}"


def _run_log_dir(config: ClusteringConfig, method: str) -> Path:
    return config.output_root / method


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
        "fine_tuning": config.fine_tuning,
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
    """"Clusters found: N" - excludes HDBSCAN/OPTICS-style noise label -1 from
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


def _run_fine_tuning(config: ClusteringConfig, X: np.ndarray, now: datetime, log_path: Path) -> int:
    for method in config.clustering_methods:
        if not _run_one_method_tuning(config, method, X, now):
            return 1

    logging.info(
        "done - fine-tuning for all %d method(s) written under %s, log written to %s",
        len(config.clustering_methods),
        config.output_root,
        log_path,
    )
    return 0


def _run_one_method_tuning(config: ClusteringConfig, method: str, X: np.ndarray, now: datetime) -> bool:
    """Runs one method's fine-tuning sweep end to end (sweep, tuning_results.csv,
    plot(s), config.md, runs.csv). Returns False if this method's tuning
    failed - the caller stops the whole run, no partial-failure tolerance,
    consistent with the production loop's own fail-fast behavior.
    """
    try:
        base_params, _ = load_method_params(config.params_file, method)
        tuning_grid = load_tuning_grid(config.params_file, method)
        consensus_config = load_consensus_config(config.params_file, method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error("[%s] %s", method, exc)
        return False

    results = run_clustering_tuning_sweep(method, X, base_params, tuning_grid, consensus_config)

    output_dir = _tuning_output_dir(config, method, now)
    try:
        _write_tuning_output(output_dir, results, tuning_grid, method, X, base_params, config, now)
    except (FileExistsError, OSError) as exc:
        logging.error("[%s] %s", method, exc)
        return False
    logging.info("[%s] tuning results written to %s (%d combination(s) evaluated)", method, output_dir, len(results))

    try:
        append_run_log_entry(
            _run_log_dir(config, method),
            config.session_name,
            now,
            "tuning",
            {"base_params": base_params, "tuning_grid": tuning_grid},
            output_dir,
            config.run_notes,
        )
    except OSError as exc:
        logging.error("[%s] cannot write run log: %s", method, exc, exc_info=True)
        return False

    return True


def _tuning_output_dir(config: ClusteringConfig, method: str, now: datetime) -> Path:
    return config.output_root / method / "tuning" / f"{now.strftime('%d-%m')}_{config.session_name}"


def _write_tuning_output(
    output_dir: Path,
    results: pd.DataFrame,
    tuning_grid: dict[str, list],
    method: str,
    X: np.ndarray,
    base_params: dict,
    config: ClusteringConfig,
    now: datetime,
) -> None:
    if output_dir.exists() and not config.overwrite:
        raise FileExistsError(
            f"output directory {output_dir} already exists and overwrite=False "
            "- set overwrite=True to replace it, or choose a different session_name"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "tuning_results.csv", index=False)

    swept_params = list(tuning_grid.keys())
    title = compose_run_title(output_dir, config.project)
    metric_cols = METHOD_METRIC_COLUMNS[method] + [c for c in CONSENSUS_METRIC_COLUMNS if c in results.columns]
    if len(swept_params) == 1:
        plot_clustering_tuning_metrics(results, swept_params[0], metric_cols, output_dir / "tuning_plot.png", title)
    elif len(swept_params) == 2:
        plot_clustering_tuning_heatmaps(
            results, swept_params[0], swept_params[1], metric_cols, output_dir / "tuning_plot.png", title
        )
    else:
        logging.warning(
            "[%s] tuning_grid has %d swept parameters - no metric plot generated (only 1 or 2 are supported)",
            method,
            len(swept_params),
        )

    if method in STANDALONE_DIAGNOSTIC_METHODS:
        _write_standalone_diagnostic(output_dir, method, X, base_params, title)

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
                "clustering_method": method,
                "params_file": str(config.params_file),
                "session_name": config.session_name,
            },
            indent=2,
        ),
        "```",
        "",
        "## Summary",
        "",
        f"Swept parameters: {swept_params}",
        f"Combinations evaluated: {len(results)}",
        f"Metrics: {metric_cols}",
        "",
        "No automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.",
    ]
    (output_dir / "config.md").write_text("\n".join(readme_lines) + "\n")

    suggestion_lines = consensus_suggestion_lines(results, method)
    if suggestion_lines:
        (output_dir / "consensus_suggestions.md").write_text(
            "\n".join([f"# {title} — consensus/stability suggestions", ""] + suggestion_lines) + "\n"
        )


def _write_standalone_diagnostic(output_dir: Path, method: str, X: np.ndarray, base_params: dict, title: str) -> None:
    """Diagnostic plot independent of the swept tuning_grid, computed once
    from base_params - see src/analysis/clustering_tuning.py's module
    docstring for why these 2 (and only these 2) methods get one.
    """
    if method == "agglomerative":
        linkage_matrix = compute_dendrogram_linkage(X, base_params)
        plot_dendrogram(linkage_matrix, output_dir / "dendrogram.png", title)
        logging.info("[%s] dendrogram written to %s", method, output_dir / "dendrogram.png")
    elif method == "spectral":
        eigenvalues = compute_eigengap(X, base_params)
        plot_eigengap(eigenvalues, output_dir / "eigengap_plot.png", title)
        logging.info("[%s] eigengap plot written to %s", method, output_dir / "eigengap_plot.png")
    else:
        raise ValueError(f"no standalone diagnostic wired for method {method!r}")


def _log_path(config: ClusteringConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
