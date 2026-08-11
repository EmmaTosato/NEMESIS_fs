"""CLI entry point: reduce then cluster an already-built feature matrix.

Usage:
    python -m src.pipeline.dim_reduction_clustering --config config/pipelines/dim_reduction_clustering.json

Reads a matrix artifact (input_path must already exist), embeds it once with
the configured reduction method, then clusters that same embedding (not the
raw matrix) with every method in clustering_methods (one or more). In
production mode (fine_tuning=false), metadata is first enriched with
lesion_volume_voxels/lesion_side/nihss via
src/features/clinical.py::enrich_metadata_with_lesion_info - the same
enrichment dim_reduction.py always persists, shared so a result from this
pipeline carries the same columns regardless of which one produced it. Each
method writes its own artifact under
<output_root>/production/<reduction_method>/<clustering_method>/<dd-mm>_<session_name>/:
the embedding as matrix.npy, cluster_label appended to that enriched
metadata.csv, a static
2D scatter plot colored by cluster (cluster_plot.png) for a first visual
sanity check, an interactive HTML version (cluster_plot_interactive.html)
with a dropdown to switch coloring between cluster and dataset, hover showing
every metadata column per point, and a per-sample silhouette diagnostic
(silhouette_plot.png, see src/analysis/clustering_tuning.py::compute_silhouette_samples),
skipped with a warning if the chosen result is degenerate (fewer than 2
non-noise clusters). Every clustering method run against the same
reduction shares one run history,
<output_root>/production/<reduction_method>/runs.csv (see src/utils/run_log.py),
distinguished by its leading reduction_method/clustering_method columns.
When more than one clustering method is requested, an additional side-by-side
comparison (static cluster_comparison.png + interactive
cluster_comparison_interactive.html, dropdown per method) is written to
<output_root>/production/<reduction_method>/comparison/<reduction_method>_<dd-mm>_<session_name>/.

`fine_tuning: true` switches to fine-tuning mode: the reduction step still
runs exactly once, at its already-chosen production params (never swept here
- that's dim_reduction.py's job) - but instead of clustering production, each
method in clustering_methods runs a fine-tuning sweep over its own
tuning_grid *against that one embedding*, via
src/analysis/clustering_tuning.py (same sweep/metrics/standalone-diagnostics
clustering.py's own fine_tuning mode uses). This is the one-shot alternative
to save_matrix-ing the embedding via dim_reduction.py and separately pointing
clustering.py --fine_tuning at it: useful when you only want to tune
clustering on a specific reduction without needing that embedding saved to
disk as its own artifact. Output per method:
<output_root>/tuning/<reduction_method>/<method>/<dd-mm>_<session_name>/
{tuning_results.csv, tuning_plot.png, config.md} plus a standalone diagnostic
plot for agglomerative/spectral. No comparison plot in this mode - a
sweep's rows aren't a single set of cluster labels to compare side by side.

Output lives under two separate branches of output_root, never mixed:
<output_root>/production/... (embeddings/plots/comparison, runs.csv) and
<output_root>/tuning/... (sweep tables/plots, runs_tuning.csv).
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

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.covariates import check_volume_regression_compatible, regress_out_covariate
from src.analysis.embedding_plots import write_embedding_plots
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
from src.analysis.model_config import DimReductionClusteringConfig, load_dim_reduction_clustering_config
from src.analysis.params import load_consensus_config, load_method_params, load_tuning_grid
from src.analysis.plotting import (
    compose_cluster_plot_title,
    compose_comparison_title,
    compose_run_title,
    plot_clusters_2d,
    plot_clusters_comparison,
    plot_clusters_comparison_interactive,
    plot_clusters_interactive,
    plot_clustering_tuning_heatmaps,
    plot_clustering_tuning_metrics,
    plot_dendrogram,
    plot_eigengap,
    plot_silhouette_analysis,
)
from src.analysis.reduction import REDUCTION_METHODS, embedding_for_viz
from src.features.clinical import enrich_metadata_with_lesion_info
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

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

    if config.viz_n_components != 2:
        logging.error(
            "viz_n_components=%d not supported here - every cluster-coloring plot in this pipeline "
            "(plot_clusters_2d/plot_clusters_interactive/plot_silhouette_analysis/plot_clusters_comparison*) "
            "is 2D-only, unlike dim_reduction.py's own embedding plots",
            config.viz_n_components,
        )
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
        check_volume_regression_compatible(config.regress_out_volume, reduction_params)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    embedding = REDUCTION_METHODS[config.reduction_method](X, reduction_params)

    # Separate embedding for visualization only - reused as-is when it already has
    # viz_n_components columns (every config today: both 2, zero extra cost), otherwise
    # refit from raw X (see src/analysis/reduction.py::embedding_for_viz's docstring for why
    # slicing embedding[:, :viz_n_components] is not a valid substitute for umap/tsne/pacmap).
    # Computed before regress_out_volume below so both the clustering and the plotted
    # embedding get the same treatment; clustering/silhouette always use the real `embedding`
    # (whatever its own n_components is), never `viz_embedding`.
    viz_embedding = embedding_for_viz(config.reduction_method, X, reduction_params, embedding, config.viz_n_components)
    viz_is_clustering_embedding = viz_embedding is embedding

    if config.regress_out_volume:
        # X is binary (0/1 per voxel); a row's voxel count is exactly proportional to its
        # lesion volume in ml, and OLS residuals are invariant to that scalar rescaling.
        lesion_load_voxels = X.sum(axis=1)
        embedding = regress_out_covariate(embedding, lesion_load_voxels)
        viz_embedding = embedding if viz_is_clustering_embedding else regress_out_covariate(viz_embedding, lesion_load_voxels)
        logging.info("regressed out lesion volume (voxel count) from both the clustering and visualization embeddings")

    effective_reduction_session = f"{config.session_name}_{reduction_tag}" if reduction_tag else config.session_name

    if config.fine_tuning:
        return _run_fine_tuning(config, embedding, reduction_params, now, log_path)

    # Same enrichment dim_reduction.py always persists - shared via
    # enrich_metadata_with_lesion_info so a result produced by this pipeline
    # carries the same columns forward as one produced by dim_reduction.py,
    # regardless of which was run (see docs/dev/plotting.md). Not done in the
    # fine_tuning branch above: that mode writes no metadata.csv at all (only
    # tuning_results.csv/plots), so an unresolvable subject there would abort
    # a tuning run for a column it never uses.
    try:
        metadata = enrich_metadata_with_lesion_info(metadata, X)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    if config.color_by:
        embedding_dir = (
            config.output_root
            / "production"
            / config.reduction_method
            / "embedding"
            / f"{now.strftime('%d-%m')}_{effective_reduction_session}"
        )
        write_embedding_plots(
            viz_embedding,
            metadata,
            X,
            list(config.color_by),
            embedding_dir,
            f"{config.reduction_method} dim 1",
            f"{config.reduction_method} dim 2",
            lambda label: compose_run_title(embedding_dir, config.project) + (f" — {label}" if label else ""),
        )
        logging.info("embedding color_by plots written to %s", embedding_dir)

    labels_by_method: dict[str, np.ndarray] = {}
    for method in config.clustering_methods:
        cluster_labels = _run_one_method(config, method, X, embedding, viz_embedding, metadata, reduction_params, reduction_tag, now)
        if cluster_labels is None:
            return 1
        labels_by_method[method] = cluster_labels

    comparison_dir = (
        config.output_root
        / "production"
        / config.reduction_method
        / "comparison"
        / f"{config.reduction_method}_{now.strftime('%d-%m')}_{effective_reduction_session}"
    )
    plot_clusters_comparison(
        viz_embedding,
        labels_by_method,
        comparison_dir / "cluster_comparison.png",
        xlabel=f"{config.reduction_method} dim 1",
        ylabel=f"{config.reduction_method} dim 2",
        suptitle=compose_comparison_title(comparison_dir, config.reduction_method),
    )
    logging.info("comparison plot written to %s", comparison_dir / "cluster_comparison.png")

    plot_clusters_comparison_interactive(
        viz_embedding,
        labels_by_method,
        metadata,
        comparison_dir / "cluster_comparison_interactive.html",
        xlabel=f"{config.reduction_method} dim 1",
        ylabel=f"{config.reduction_method} dim 2",
        title=compose_run_title(comparison_dir, config.project),
    )
    logging.info("interactive comparison plot written to %s", comparison_dir / "cluster_comparison_interactive.html")

    lines = [
        f"# {config.project} dim_reduction_clustering method comparison "
        f"({config.reduction_method}) — {now.strftime('%d-%m-%y %H:%M')}",
        "",
        f"Reduction method: {config.reduction_method}",
        f"Clustering methods compared: {list(config.clustering_methods)}",
        "",
        "Individual outputs:",
    ]
    lines += [f"- `{config.output_root / 'production' / _method_dir(config, m)}`" for m in config.clustering_methods]
    comparison_dir.mkdir(parents=True, exist_ok=True)
    (comparison_dir / "config.md").write_text("\n".join(lines) + "\n")

    logging.info(
        "done - all %d method(s) written under %s, log written to %s", len(config.clustering_methods), config.output_root, log_path
    )
    return 0


def _run_one_method(
    config: DimReductionClusteringConfig,
    method: str,
    X: np.ndarray,
    embedding: np.ndarray,
    viz_embedding: np.ndarray,
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

    output_dir = config.output_root / "production" / _method_dir(config, method) / f"{now.strftime('%d-%m')}_{effective_session_name}"
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

    plot_title = compose_cluster_plot_title(output_dir, config.reduction_method, method)

    plot_clusters_2d(
        viz_embedding,
        cluster_labels,
        output_dir / "cluster_plot.png",
        xlabel=f"{config.reduction_method} dim 1",
        ylabel=f"{config.reduction_method} dim 2",
        title=plot_title,
    )
    logging.info("[%s] cluster plot written to %s", method, output_dir / "cluster_plot.png")

    plot_clusters_interactive(
        viz_embedding,
        metadata_out,
        output_dir / "cluster_plot_interactive.html",
        xlabel=f"{config.reduction_method} dim 1",
        ylabel=f"{config.reduction_method} dim 2",
        title=plot_title,
    )
    logging.info("[%s] interactive cluster plot written to %s", method, output_dir / "cluster_plot_interactive.html")

    try:
        sample_labels, sample_silhouette_values = compute_silhouette_samples(embedding, cluster_labels)
        plot_silhouette_analysis(
            sample_labels,
            sample_silhouette_values,
            viz_embedding,
            cluster_labels,
            output_dir / "silhouette_plot.png",
            xlabel=f"{config.reduction_method} dim 1",
            ylabel=f"{config.reduction_method} dim 2",
            title=plot_title,
        )
        logging.info("[%s] silhouette plot written to %s", method, output_dir / "silhouette_plot.png")
    except ValueError as exc:
        logging.warning("[%s] skipping silhouette_plot.png: %s", method, exc)

    try:
        append_run_log_entry(
            config.output_root / "production" / config.reduction_method,
            effective_session_name,
            now,
            "production",
            {"reduction_params": reduction_params, "clustering_params": clustering_params},
            output_dir,
            config.run_notes,
            extra_columns={"reduction_method": config.reduction_method, "clustering_method": method},
        )
    except OSError as exc:
        logging.error("[%s] cannot write run log: %s", method, exc, exc_info=True)
        return None

    logging.info("[%s] done - output written to %s", method, output_dir)
    return cluster_labels


def _method_dir(config: DimReductionClusteringConfig, method: str) -> Path:
    return Path(config.reduction_method) / method




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
        "fine_tuning": config.fine_tuning,
        "regress_out_volume": config.regress_out_volume,
        "viz_n_components": config.viz_n_components,
        "color_by": list(config.color_by),
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


def _run_fine_tuning(
    config: DimReductionClusteringConfig,
    embedding: np.ndarray,
    reduction_params: dict,
    now: datetime,
    log_path: Path,
) -> int:
    for method in config.clustering_methods:
        if not _run_one_method_tuning(config, method, embedding, reduction_params, now):
            return 1

    logging.info(
        "done - fine-tuning for all %d method(s) written under %s, log written to %s",
        len(config.clustering_methods),
        config.output_root,
        log_path,
    )
    return 0


def _run_one_method_tuning(
    config: DimReductionClusteringConfig,
    method: str,
    embedding: np.ndarray,
    reduction_params: dict,
    now: datetime,
) -> bool:
    """Runs one clustering method's fine-tuning sweep against the
    already-computed embedding (never recomputed here - the reduction step
    stays fixed at its own already-chosen production params; only the
    clustering hyperparameters are swept, same evaluators clustering.py's own
    fine_tuning mode uses). Returns False on failure - the caller stops the
    whole run, no partial-failure tolerance, consistent with the production
    loop's own fail-fast behavior.

    Output dir is <dd-mm>_<session_name> - no reduction tag, unlike the
    production path in _run_one_method: which reduction produced the embedding
    is already unambiguous from the enclosing <reduction_method>/<method>/
    folders, and its exact params are always in this run's own config.md, so
    tagging the session name here would only duplicate that without adding
    any information - same convention as dim_reduction.py's/clustering.py's
    own tuning mode (never tagged either, see their _tuning_output_dir).
    """
    try:
        base_params, _ = load_method_params(config.clustering_params_file, method)
        tuning_grid = load_tuning_grid(config.clustering_params_file, method)
        consensus_config = load_consensus_config(config.clustering_params_file, method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error("[%s] %s", method, exc)
        return False

    try:
        results = run_clustering_tuning_sweep(method, embedding, base_params, tuning_grid, consensus_config)
    except ValueError as exc:
        logging.error("[%s] %s", method, exc)
        return False

    output_dir = (
        config.output_root
        / "tuning"
        / config.reduction_method
        / method
        / f"{now.strftime('%d-%m')}_{config.session_name}"
    )
    try:
        _write_tuning_output(output_dir, results, tuning_grid, method, embedding, base_params, reduction_params, config, now)
    except (FileExistsError, OSError) as exc:
        logging.error("[%s] %s", method, exc)
        return False
    logging.info("[%s] tuning results written to %s (%d combination(s) evaluated)", method, output_dir, len(results))

    try:
        append_run_log_entry(
            config.output_root / "tuning" / config.reduction_method,
            config.session_name,
            now,
            "tuning",
            {
                "reduction_params": reduction_params,
                "clustering_base_params": base_params,
                "clustering_tuning_grid": tuning_grid,
            },
            output_dir,
            config.run_notes,
            extra_columns={"reduction_method": config.reduction_method, "clustering_method": method},
        )
    except OSError as exc:
        logging.error("[%s] cannot write run log: %s", method, exc, exc_info=True)
        return False

    return True


def _write_tuning_output(
    output_dir: Path,
    results: pd.DataFrame,
    tuning_grid: dict[str, list],
    method: str,
    embedding: np.ndarray,
    base_params: dict,
    reduction_params: dict,
    config: DimReductionClusteringConfig,
    now: datetime,
) -> None:
    if output_dir.exists():
        if not config.overwrite:
            raise FileExistsError(
                f"output directory {output_dir} already exists and overwrite=False "
                "- set overwrite=True to replace it, or choose a different session_name"
            )
        # Same rationale as dim_reduction.py's/clustering.py's own
        # _write_tuning_output - wipe first so overwrite=True always means
        # "this directory reflects exactly this run" (see lessons_learned.md #18).
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "tuning_results.csv", index=False)

    swept_params = list(tuning_grid.keys())
    title = compose_cluster_plot_title(output_dir, config.reduction_method, method)
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
        _write_standalone_diagnostic(output_dir, method, embedding, base_params, title)

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
                "reduction_params_used": reduction_params,
                "clustering_method": method,
                "clustering_params_file": str(config.clustering_params_file),
                "session_name": config.session_name,
                "clustering_base_params": base_params,
                "clustering_tuning_grid": tuning_grid,
            },
            indent=2,
        ),
        "```",
        "",
        "## Summary",
        "",
        f"Embedding shape: {embedding.shape[0]} subjects x {embedding.shape[1]} components (reduction fixed, not swept)",
        f"Swept parameters: {swept_params}",
        f"Combinations evaluated: {len(results)}",
        f"Metrics: {metric_cols}",
        "",
        "Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.",
    ]
    (output_dir / "config.md").write_text("\n".join(readme_lines) + "\n")

    suggestion_lines = consensus_suggestion_lines(results, method)
    if suggestion_lines:
        (output_dir / "consensus_suggestions.md").write_text(
            "\n".join([f"# {title} — consensus/stability suggestions", ""] + suggestion_lines) + "\n"
        )


def _write_standalone_diagnostic(output_dir: Path, method: str, embedding: np.ndarray, base_params: dict, title: str) -> None:
    """Diagnostic plot independent of the swept tuning_grid, computed once
    from base_params - see src/analysis/clustering_tuning.py's module
    docstring for why these 2 (and only these 2) methods get one. Same
    dispatch as clustering.py's own helper of the same name, duplicated
    rather than shared per this codebase's established per-CLI convention
    (see docs/dev/models.md) - the two callers differ in which config type
    they close over.
    """
    if method == "agglomerative":
        linkage_matrix = compute_dendrogram_linkage(embedding, base_params)
        plot_dendrogram(linkage_matrix, output_dir / "dendrogram.png", title)
        logging.info("[%s] dendrogram written to %s", method, output_dir / "dendrogram.png")
    elif method == "spectral":
        eigenvalues = compute_eigengap(embedding, base_params)
        plot_eigengap(eigenvalues, output_dir / "eigengap_plot.png", title)
        logging.info("[%s] eigengap plot written to %s", method, output_dir / "eigengap_plot.png")
    else:
        raise ValueError(f"no standalone diagnostic wired for method {method!r}")


def _log_path(config: DimReductionClusteringConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
