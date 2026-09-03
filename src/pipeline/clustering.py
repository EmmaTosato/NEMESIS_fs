"""CLI entry point: cluster an already-built feature matrix directly, no reduction.

Usage:
    python -m src.pipeline.clustering --config config/pipelines/clustering.json

Reads a matrix artifact (input_path must already exist - either a raw/
parcellated matrix or an already-computed dim_reduction embedding). `reduced_data`
is a required config flag (docs/dev/clustering_migration_plan.md §1) - this pipeline
never calls embed() itself in either case, so loading is identical regardless; the
one place it does gate real behavior (26-08-26) is _require_matching_reduction_run
below, which only runs when reduced_data is True (input_path is then itself a
dim_reduction.py run, so it has a reduction method/params to cross-check a
viz_embedding_path against - see below).

Two modes, chosen by `fine_tuning`, same convention as dim_reduction.py:

- fine_tuning=false (production): clusters with every method in
  clustering_methods (one or more) using that method's "params" from
  params_clustering.json, writing a new artifact per method: the same
  matrix (unchanged - clustering doesn't transform the feature space) as
  matrix.npy, cluster_label appended to metadata.csv, plus a set of
  cluster-colored plots (cluster_plot.png, silhouette_plot.png) - all
  built on a *viz embedding* resolved once per run,
  never a slice of X (see _resolve_viz_embedding/plan §3): reused directly
  when X already has 2 or 3 components, or read from `viz_embedding_path` (a
  companion 2D/3D embedding computed separately, e.g. via dim_reduction.py,
  same random_state/n_neighbors/metric as whatever produced X, only
  n_components different - checked, not just documented, whenever
  reduced_data is True: see _require_matching_reduction_run)
  when X has any other number - every scatter plot is skipped with a clear
  warning, not silently drawn from X[:, :2], when neither applies.
  Single-run interactivity is covered by src.pipeline.embedding_app, not by
  a plot written here; the silhouette
  diagnostic (silhouette_plot.png) is computed on the full matrix used for
  clustering, not the viz embedding - see
  src/analysis/clustering_tuning.py::compute_silhouette_samples), skipped
  with a warning if the chosen result is degenerate (fewer than 2 non-noise
  clusters). No cross-method comparison artifact is written any more - the
  side-by-side production/comparison/ plot (static + interactive) was
  removed 01-09-26 on request (docs/dev/models.md); comparing methods means
  opening each method's own cluster_plot.png/embedding_app.py run.
- fine_tuning=true (manual hyperparameter search, every method in
  clustering_methods, one sweep each over that method's "tuning_grid"):
  since clustering has no ground truth to score against, every combination
  is scored with 3 generic internal-validation indices (silhouette,
  Calinski-Harabasz, Davies-Bouldin - see src/analysis/clustering_tuning.py)
  plus a method-specific extra where one exists (kmeans' inertia, gmm's
  bic/aic). Writes tuning_results.csv + tuning_plot.png (one subplot per
  metric) to <output_root>/tuning/<method>/<dd-mm>_<session_name>/, plus a
  standalone diagnostic plot for the 2 methods that have one, independent of
  the swept `n_clusters`/`n_components` grid: agglomerative's
  dendrogram_metric=<metric>.png (one per swept metric, one subplot per valid
  linkage), spectral's eigengap_affinity=<affinity>.png (one per swept
  affinity, one subplot per value of that affinity's own hyperparameter). No
  automatic selection -
  a human reads the outputs and picks parameters by hand, writes them into
  params_clustering.json's "params", and re-runs with fine_tuning=false. The
  sweep can also persist every combination's actual cluster-label array (not
  just its scores) into <output_root>/tuning/<method>/<dd-mm>_<session_name>/
  clusterings.npz, plus a self-contained metadata.csv, when
  config.save_tuning_clusterings is true (opt-in, off by default, mirrors
  dim_reduction.py's save_tuning_embeddings) - so a later reader can inspect
  any evaluated combination's labels without recomputing the sweep.

Output lives under two separate branches of output_root, never mixed:
<output_root>/production/<method>/ (production, runs.csv) and
<output_root>/tuning/<method>/ (tuning, runs_tuning.csv) - each branch keeps
its own chronological run history, distinct from any single run's own
config.md (see docs/dev/config.md).
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

from src.analysis.clustering import CLUSTERING_METHODS, _validate_evidence_accumulation_params
from src.analysis.clustering_tuning import (
    CONSENSUS_METRIC_COLUMNS,
    METHOD_METRIC_COLUMNS,
    SPECTRAL_AFFINITY_HYPERPARAM,
    STABILITY_ELIGIBLE_METHODS,
    STABILITY_METRIC_NAME,
    STABILITY_NUISANCE_PARAM,
    STABILITY_TARGET_PARAM,
    STANDALONE_DIAGNOSTIC_METHODS,
    compute_dendrogram_linkage,
    compute_eigengap,
    compute_interclass_distance_matrix,
    compute_silhouette_samples,
    compute_stability_sweep,
    consensus_suggestion_lines,
    hdbscan_labels_and_probabilities,
    is_invalid_ward_metric_combo,
    representative_values,
    run_clustering_tuning_sweep,
    run_spectral_affinity_aware_sweep,
)
from src.analysis.consensus_clustering import assign_clusters_from_cooccurrence, compute_evidence_accumulation_convergence, run_rsc_repeats
from src.analysis.model_config import ClusteringConfig, load_clustering_config
from src.analysis.params import (
    build_tag_from_values,
    load_consensus_config,
    load_method_params,
    load_stability_config,
    load_tag_params,
    load_tag_spec,
    load_tuning_grid,
)
from src.analysis.plotting import (
    compose_cluster_plot_title,
    compose_clustering_tuning_title,
    plot_clusters_2d,
    plot_clustering_tuning_heatmaps,
    plot_clustering_tuning_metrics,
    plot_consensus_matrix_heatmap,
    plot_dendrograms_grid,
    plot_eigengaps_grid,
    plot_grouped_tuning_metrics,
    plot_interclass_distance_matrix,
    plot_silhouette_analysis,
    plot_spectral_tuning,
    plot_stability_analysis,
    plot_tuning_curve,
)
from src.utils.artifacts import load_matrix, read_dim_reduction_method, read_run_params, save_matrix
from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.run_log import append_run_log_entry

LOGS_ROOT = Path("logs") / "clustering"
LOG_FILENAME_PREFIX = "clustering"


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

        # reduced_data is declarative only (docs/dev/clustering_migration_plan.md §1) - loading is
        # identical either way (load_matrix above, no embed() call in this pipeline). Logged so a run's
        # log/console output always makes explicit which of the two the operator declared, rather than
        # leaving it implicit in whatever input_path happens to point at.
        if config.reduced_data:
            logging.info("reduced_data=true - input_path treated as an already-computed embedding (%s, shape %s)", config.input_path, X.shape)
        else:
            logging.info("reduced_data=false - input_path treated as a raw feature matrix (%s, shape %s)", config.input_path, X.shape)

        try:
            embedding_tag = _embedding_tag(config)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        if config.fine_tuning:
            return _run_fine_tuning(config, X, metadata, now, log_path, embedding_tag)

        try:
            X_viz = _resolve_viz_embedding(X, metadata, config.viz_embedding_path, config.input_path, config.reduced_data)
        except ValueError as exc:
            logging.error(str(exc))
            return 1
        if X_viz is None:
            logging.warning(
                "X has %d components (not 2 or 3) and no viz_embedding_path was given - skipping every "
                "cluster-colored plot (cluster_plot.png/silhouette_plot.png) for this run. If X has more "
                "than 3 components, produce a companion 2D/3D embedding separately (dim_reduction.py, "
                "same params as the one used for this input, only n_components different) and set "
                "viz_embedding_path to plot - see docs/dev/clustering_migration_plan.md §3.",
                X.shape[1],
            )

        for method in config.clustering_methods:
            cluster_labels = _run_one_method(config, method, X, X_viz, metadata, now, embedding_tag)
            if cluster_labels is None:
                return 1

        logging.info("done - all %d method(s) written under %s, log written to %s", len(config.clustering_methods), config.output_root, log_path)
        return 0
    finally:
        log_duration(now)


def _resolve_viz_embedding(
    X: np.ndarray,
    metadata: pd.DataFrame,
    viz_embedding_path: Path | None,
    input_path: Path,
    reduced_data: bool,
) -> np.ndarray | None:
    """Resolves the 2D/3D coordinates used for every cluster-colored scatter plot in this
    pipeline - always independent from X, whatever dimensionality clustering itself used.

    - X already has 2 or 3 columns: reused as-is, zero extra cost - the common case (X is
      already an embedding built for viz, or clustering.py is running directly on a small raw
      matrix).
    - X has any other number of columns (typically >3 - an embedding built for clustering, not
      viewing): clustering.py never calls embed() itself (see
      docs/dev/clustering_migration_plan.md §2), so it cannot refit a projection - a
      viz_embedding_path must point at a companion embedding computed separately (same
      random_state/n_neighbors/metric as whatever produced X, only n_components different - see
      plan §3), covering the exact same subjects in the exact same order. Returns None (caller
      skips every scatter plot, logging why once) when no such path was given - never sliced to
      X[:, :2] regardless of X's own provenance (lessons_learned.md #16).

    Two structural checks (shape, subject order) alone don't guarantee the companion is
    actually a twin of X's own embedding - it could be structurally valid and still come from
    an unrelated reduction method or a different metric/n_neighbors/random_state, producing a
    geometrically unrelated layout that plots real cluster labels onto a misleading picture,
    with no error to notice it by (found in discussion, 26-08-26). When reduced_data is True
    (input_path is itself a dim_reduction.py production run, so it has something comparable to
    check), _require_matching_reduction_run additionally verifies the companion was built by
    the same method with the same params (n_components excepted). Skipped when reduced_data is
    False - input_path is then a raw feature matrix from a different pipeline, whose config.md
    has nothing comparable to a reduction method/params to check against.
    """
    if X.shape[1] in (2, 3):
        return X
    if viz_embedding_path is None:
        return None
    viz_X, viz_metadata, _extra_arrays = load_matrix(viz_embedding_path)
    if viz_X.shape[1] not in (2, 3):
        raise ValueError(
            f"viz_embedding_path {viz_embedding_path} has {viz_X.shape[1]} component(s) - "
            "must be a 2D or 3D companion embedding, not another one clustering.py can't plot either"
        )
    if list(viz_metadata["subject_id"]) != list(metadata["subject_id"]):
        raise ValueError(
            f"viz_embedding_path {viz_embedding_path} does not cover the same subjects, in the "
            "same order, as input_path - refusing to plot cluster labels onto mismatched points"
        )
    if reduced_data:
        _require_matching_reduction_run(input_path, viz_embedding_path)
    return viz_X


def _require_matching_reduction_run(input_path: Path, viz_embedding_path: Path) -> None:
    """Guards against a viz_embedding_path that passes _resolve_viz_embedding's structural
    checks (same subjects, same order, 2/3 components) but was actually built by a different
    reduction method or with different hyperparameters than input_path's own run - a companion
    like that plots real cluster labels onto an unrelated geometry, a misleading plot rather
    than a missing one, so this always raises rather than warning (unlike a missing
    viz_embedding_path, which is a documented "no plot" case, not a wrong one).

    Only called when reduced_data is True, i.e. input_path is itself a dim_reduction.py
    production run - viz_embedding_path always is one too, by construction (it's the only way
    to get a 2D/3D companion of an embedding space).

    Two checks, both content-based (never derived from either path's own directory structure -
    unlike embedding_app.py's discover_production_runs, neither path here is guaranteed to sit
    under a <production>/<method>/ convention):
    - same reduction method (read_dim_reduction_method, each run's own config.md title line) -
      needed on top of the params comparison below, since two different methods' params dicts
      could otherwise share no conflicting keys (e.g. pca has very few) and go undetected.
    - every resolved param except n_components identical (read_run_params, each run's own
      "Params used" dict) - generic dict comparison, no per-method special-casing, symmetric
      (a key present in only one run's dict is exactly as much a mismatch as a differing
      value).
    """
    input_method = read_dim_reduction_method(input_path)
    viz_method = read_dim_reduction_method(viz_embedding_path)
    if input_method != viz_method:
        raise ValueError(
            f"viz_embedding_path {viz_embedding_path} was built with reduction method "
            f"{viz_method!r}, but input_path {input_path} was built with {input_method!r} - "
            "a companion embedding must come from the same reduction method"
        )

    input_params = read_run_params(input_path)
    viz_params = read_run_params(viz_embedding_path)
    compared_keys = (set(input_params) | set(viz_params)) - {"n_components"}
    mismatched = {
        key: (input_params.get(key, "<missing>"), viz_params.get(key, "<missing>"))
        for key in compared_keys
        if input_params.get(key, "<missing>") != viz_params.get(key, "<missing>")
    }
    if mismatched:
        details = ", ".join(f"{key} (input={inp!r}, viz={viz!r})" for key, (inp, viz) in sorted(mismatched.items()))
        raise ValueError(
            f"viz_embedding_path {viz_embedding_path} does not share input_path {input_path}'s "
            f"reduction params (only n_components may differ) - mismatched: {details}"
        )


def _run_one_method(
    config: ClusteringConfig,
    method: str,
    X: np.ndarray,
    X_viz: np.ndarray | None,
    metadata: pd.DataFrame,
    now: datetime,
    embedding_tag: str | None,
) -> np.ndarray | None:
    """Runs one clustering method end to end (params, artifact, plot,
    runs.csv). Returns the cluster_labels actually saved, or None if this
    method's run failed - the caller stops the whole run.

    X_viz is the 2D/3D coordinates used for every scatter plot (see
    _resolve_viz_embedding) - independent from X, whatever dimensionality
    clustering itself used. None means no scatter plot can be honestly
    produced for this run (already logged once by the caller) - every plot
    call below is skipped, not silently drawn from a slice of X.

    embedding_tag (from _embedding_tag, computed once per run by the caller) is input_path's
    own tag (e.g. "m_euclidean_nc2") - None when reduced_data is False or the source method has
    no tag_param. Folded into the output folder name so it never has to be hand-typed into
    session_name (31-08-26, tag-params-multi-key session).
    """
    try:
        params, tag = load_method_params(config.params_file, method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return None

    try:
        if method == "hdbscan":
            # project-clustering-tuning-redesign memory (26-08-26): probabilities_ (per-point
            # membership confidence) is only reachable from the fitted estimator, not from
            # CLUSTERING_METHODS["hdbscan"]'s labels-only contract - refit directly here to size
            # cluster_plot.png's markers by it below.
            cluster_labels, membership_probabilities = hdbscan_labels_and_probabilities(X, params)
        else:
            cluster_labels = CLUSTERING_METHODS[method](X, params)
            membership_probabilities = None
    except (TypeError, ValueError) as exc:
        # Same gap as HIGH #11 (dim_reduction.py's embed()), found here during the same
        # audit under #18 - load_method_params validates the file/method exist, never the
        # *contents* of params (e.g. a typo'd key, or a value sklearn's constructor rejects).
        logging.error("[%s] cannot fit with params %s: %s", method, params, exc)
        return None

    metadata_out = metadata.copy()
    metadata_out["cluster_label"] = cluster_labels
    
    effective_session_name = config.session_name
    if embedding_tag:
        effective_session_name = f"{effective_session_name}_{embedding_tag}"
    if tag:
        effective_session_name = f"{effective_session_name}_{tag}"
    output_dir = (
        config.output_root / "production" / method / config.reduction_method / f"{now.strftime('%d-%m')}_{effective_session_name}"
    )

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

    if X_viz is not None:
        plot_title = compose_cluster_plot_title(output_dir, config.reduction_method, method)

        plot_clusters_2d(
            X_viz,
            cluster_labels,
            output_dir / "cluster_plot.png",
            xlabel="viz dim 1",
            ylabel="viz dim 2",
            title=plot_title,
            point_sizes=membership_probabilities,
        )
        logging.info("[%s] cluster plot written to %s", method, output_dir / "cluster_plot.png")

        try:
            sample_labels, sample_silhouette_values = compute_silhouette_samples(X, cluster_labels)
            plot_silhouette_analysis(
                sample_labels,
                sample_silhouette_values,
                X_viz,
                cluster_labels,
                output_dir / "silhouette_plot.png",
                xlabel="viz dim 1",
                ylabel="viz dim 2",
                title=plot_title,
            )
            logging.info("[%s] silhouette plot written to %s", method, output_dir / "silhouette_plot.png")
        except ValueError as exc:
            logging.warning("[%s] skipping silhouette_plot.png: %s", method, exc)
    else:
        logging.warning(
            "[%s] no viz embedding available (see warning logged in main()) - skipping "
            "cluster_plot.png/silhouette_plot.png",
            method,
        )

    try:
        run_log_columns = _reduction_extra_columns(config)
    except ValueError as exc:
        logging.error("[%s] cannot describe run log input: %s", method, exc)
        return None

    try:
        # reduction_method/reduction_n_components/reduction_metric always logged
        # (_reduction_extra_columns); one extra column per tag_param key on top (31-08-26),
        # exploded from `params` rather than re-parsing the joined tag string - a reader of
        # runs.csv gets each hyperparameter as its own filterable column instead of having to
        # split "n_clust4_linkward" back apart by hand.
        run_log_columns.update({key: str(params[key]) for key in load_tag_params(config.params_file, method)})
        append_run_log_entry(
            _run_log_dir(config, method, "production"),
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
        logging.error("[%s] cannot write run log: %s", method, exc, exc_info=True)
        return None

    logging.info("[%s] done - output written to %s", method, output_dir)
    return cluster_labels


def _embedding_tag(config: ClusteringConfig) -> str | None:
    """Builds input_path's own embedding tag (e.g. "m_euclidean_nc2"), so a production output
    folder never needs that hand-typed into session_name - previously the only way to make a
    folder name show which embedding it came from, with nothing checking that string against
    the real input_path (see docs/experiments/clustering/s1_production.md
    naming discussion, 31-08-26).

    None when reduced_data is False (input_path is a raw feature matrix, no embedding
    hyperparameters to tag) or when config.reduction_method has no "tag_param" declared in
    reduction_params_file - a legitimate "nothing to tag" case, same as load_method_params' own
    tag_str=None.

    Reads the *actual* hyperparameters input_path was built with (read_run_params, from its own
    config.md) rather than reduction_params_file's current registered defaults for that method -
    so the tag always matches the real artifact, even if the registry's defaults changed since
    input_path was produced.
    """
    if not config.reduced_data:
        return None
    tag_param, tag_prefix = load_tag_spec(config.reduction_params_file, config.reduction_method)
    if tag_param is None:
        return None
    actual_params = read_run_params(config.input_path)
    return build_tag_from_values(config.reduction_params_file, config.reduction_method, tag_param, tag_prefix, actual_params)


def _reduction_extra_columns(config: ClusteringConfig) -> dict[str, str]:
    """The 3 flat extra_columns runs.csv/runs_tuning.csv/config.md always log about
    clustering's input embedding: reduction_method (required regardless of reduced_data - the
    "raw" sentinel when reduced_data is False, docs/dev/config.md), reduction_n_components,
    reduction_metric.

    Prefixed "reduction_" (not the bare "n_components"/"metric" the embedding's own config.md
    uses) to avoid colliding with a clustering method's *own* tag_param of the same name for
    the exact same row - gmm's own hyperparameter is literally "n_components" (its mixture
    component count, params_clustering.json) and would otherwise silently collide with the
    embedding's n_components in the same runs.csv row.

    reduction_n_components/reduction_metric are "" (not omitted - see below) when reduced_data
    is False, or when reduced_data is True but the source method has no such hyperparameter
    (pca/pacmap have no "metric") - read straight from input_path's own config.md via
    read_run_params, the single source of truth for "what did this embedding actually use",
    never re-declared as a separate ClusteringConfig field (would drift if that run were ever
    redone with different params). Always all 3 keys present (never conditionally omitted):
    one runs.csv/runs_tuning.csv is shared across every reduction_method that ever feeds a
    given clustering method (_run_log_dir has no reduction_method segment), so the
    extra_columns key *set* must stay identical across every row - append_run_log_entry's
    header-guard raises otherwise.

    Cross-checks config.reduction_method (declared, never inferred from path text) against
    input_path's own config.md title (read_dim_reduction_method) whenever reduced_data is True
    - same "config vs. artifact reality" discipline _require_matching_reduction_run already
    applies to viz_embedding_path. Raises ValueError on a mismatch, and propagates
    read_dim_reduction_method's/read_run_params' own ValueError when input_path's config.md is
    missing or malformed.
    """
    columns = {"reduction_method": config.reduction_method, "reduction_n_components": "", "reduction_metric": ""}
    if config.reduced_data:
        actual_method = read_dim_reduction_method(config.input_path)
        if actual_method != config.reduction_method:
            raise ValueError(
                f"config.input_path {config.input_path} was built with reduction method "
                f"{actual_method!r}, but config declares reduction_method={config.reduction_method!r}"
            )
        reduction_params = read_run_params(config.input_path)
        if "n_components" in reduction_params:
            columns["reduction_n_components"] = str(reduction_params["n_components"])
        if "metric" in reduction_params:
            columns["reduction_metric"] = str(reduction_params["metric"])
    return columns


def _run_log_dir(config: ClusteringConfig, method: str, branch: str) -> Path:
    """branch is "production" or "tuning" (same literal each caller also passes
    as append_run_log_entry's own run_type) - the two runs.csv/runs_tuning.csv
    histories live under separate output_root branches, never side by side.
    """
    return config.output_root / branch / method


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
        "reduced_data": config.reduced_data,
        "viz_embedding_path": str(config.viz_embedding_path) if config.viz_embedding_path else None,
        "run_notes": config.run_notes,
    }
    # reduction_method/reduction_n_components/reduction_metric (31-08-26) - same 3 values
    # runs.csv's own extra_columns log for this run (_reduction_extra_columns), previously
    # entirely absent from this config.md even though config.reduction_method has always been
    # a required field - a reader of one run's own report couldn't see which embedding
    # variant it was built from without cross-referencing runs.csv or the output path itself.
    payload.update(_reduction_extra_columns(config))
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


def _run_fine_tuning(
    config: ClusteringConfig, X: np.ndarray, metadata: pd.DataFrame, now: datetime, log_path: Path, embedding_tag: str | None
) -> int:
    for method in config.clustering_methods:
        if not _run_one_method_tuning(config, method, X, metadata, now, embedding_tag):
            return 1

    logging.info(
        "done - fine-tuning for all %d method(s) written under %s, log written to %s",
        len(config.clustering_methods),
        config.output_root,
        log_path,
    )
    return 0


def _run_one_method_tuning(
    config: ClusteringConfig, method: str, X: np.ndarray, metadata: pd.DataFrame, now: datetime, embedding_tag: str | None
) -> bool:
    """Runs one method's fine-tuning sweep end to end (sweep, tuning_results.csv,
    plot(s), config.md, runs.csv). Returns False if this method's tuning
    failed - the caller stops the whole run, no partial-failure tolerance,
    consistent with the production loop's own fail-fast behavior.

    embedding_tag (from _embedding_tag, computed once by the caller) is folded into the output
    folder name the same way production does (31-08-26, tag-params-multi-key session) - a
    tuning run has no tag_param of its own (it sweeps a whole grid, not one value), so without
    this, two tuning runs of the same session_name against different source embeddings would
    collide in tuning/<method>/<reduction_method>/ instead of ending up in separate folders.
    """
    try:
        base_params, _ = load_method_params(config.params_file, method)
        tuning_grid = load_tuning_grid(config.params_file, method)
        consensus_config = load_consensus_config(config.params_file, method)
        stability_config = load_stability_config(config.params_file, method)
        # Resolved once, up front (fails before running the sweep, not after) - reused for
        # both this run's own config.md (_write_tuning_output) and runs_tuning.csv's
        # extra_columns below, instead of recomputing/re-reading input_path's config.md twice.
        run_log_columns = _reduction_extra_columns(config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error("[%s] %s", method, exc)
        return False

    if method == "spectral" and "affinity" in tuning_grid and config.save_tuning_clusterings:
        # run_spectral_affinity_aware_sweep's labels_by_combo keys are (affinity, *sub_combo) -
        # sub_combo's own key order varies per affinity sub-sweep (each restricted to its own
        # hyperparameter alone), so it never lines up with the full tuning_grid.keys() order
        # _write_tuning_clusterings/_combo_key assume for every other method - refusing rather
        # than silently writing misaligned keys into clusterings.npz.
        logging.error(
            "[%s] save_tuning_clusterings is not supported together with a swept 'affinity' - "
            "disable save_tuning_clusterings or don't sweep 'affinity' for this run",
            method,
        )
        return False

    try:
        if method == "spectral" and "affinity" in tuning_grid:
            # project-clustering-tuning-redesign memory (26-08-26): n_neighbors/gamma only
            # apply to their own affinity - avoid wasting half the sweep on the irrelevant one.
            results, labels_by_combo = run_spectral_affinity_aware_sweep(X, base_params, tuning_grid, consensus_config)
        else:
            results, labels_by_combo = run_clustering_tuning_sweep(method, X, base_params, tuning_grid, consensus_config)
    except (TypeError, ValueError) as exc:
        # TypeError: a bad tuning_grid value reaches the estimator's own **params unpack
        # (same gap as _run_one_method's production path above, HIGH #11/#18).
        logging.error("[%s] %s", method, exc)
        return False

    effective_session_name = f"{config.session_name}_{embedding_tag}" if embedding_tag else config.session_name
    output_dir = _tuning_output_dir(config, method, now, embedding_tag)
    try:
        _write_tuning_output(
            output_dir, results, labels_by_combo, tuning_grid, method, X, metadata, base_params, config, now, run_log_columns
        )
    except (FileExistsError, OSError) as exc:
        logging.error("[%s] %s", method, exc)
        return False
    logging.info("[%s] tuning results written to %s (%d combination(s) evaluated)", method, output_dir, len(results))

    if stability_config is not None:
        title = compose_clustering_tuning_title(output_dir, method)
        try:
            _write_stability_output(output_dir, method, X, tuning_grid, stability_config, title)
        except (ValueError, TypeError, OSError) as exc:
            logging.error("[%s] stability analysis failed: %s", method, exc)
            return False
        logging.info("[%s] stability analysis written to %s", method, output_dir)

    try:
        append_run_log_entry(
            _run_log_dir(config, method, "tuning"),
            effective_session_name,
            now,
            "tuning",
            {"base_params": base_params, "tuning_grid": tuning_grid},
            output_dir,
            config.run_notes,
            config.input_path,
            extra_columns=run_log_columns,
        )
    except OSError as exc:
        logging.error("[%s] cannot write run log: %s", method, exc, exc_info=True)
        return False

    return True


def _tuning_output_dir(config: ClusteringConfig, method: str, now: datetime, embedding_tag: str | None) -> Path:
    # embedding_tag folded in (31-08-26, tag-params-multi-key session) - a tuning run has no
    # tag_param of its own to disambiguate different source embeddings sharing the same
    # session_name, unlike production's per-method tag (see _run_one_method_tuning docstring).
    session = f"{config.session_name}_{embedding_tag}" if embedding_tag else config.session_name
    return config.output_root / "tuning" / method / config.reduction_method / f"{now.strftime('%d-%m')}_{session}"


def _write_tuning_output(
    output_dir: Path,
    results: pd.DataFrame,
    labels_by_combo: dict[tuple, np.ndarray],
    tuning_grid: dict[str, list],
    method: str,
    X: np.ndarray,
    metadata: pd.DataFrame,
    base_params: dict,
    config: ClusteringConfig,
    now: datetime,
    reduction_columns: dict[str, str],
) -> None:
    if output_dir.exists():
        if not config.overwrite:
            raise FileExistsError(
                f"output directory {output_dir} already exists and overwrite=False "
                "- set overwrite=True to replace it, or choose a different session_name"
            )
        # A previous run into this exact output_dir may have left a
        # standalone diagnostic (dendrogram.png/eigengap_plot.png) this run's
        # method doesn't produce - wipe first so overwrite=True always means
        # "this directory reflects exactly this run" (same rationale as
        # dim_reduction.py's _write_tuning_output, see lessons_learned.md #18).
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "tuning_results.csv", index=False)

    swept_params = list(tuning_grid.keys())
    if config.save_tuning_clusterings:
        _write_tuning_clusterings(output_dir, labels_by_combo, swept_params)
        # Same subjects/row order for every combination in this sweep (one X/metadata for the
        # whole run) - written once at the top, not per combination. Self-contained so a later
        # reader never needs to reload X or rerun the sweep, just this file + clusterings.npz
        # (mirrors dim_reduction.py::_write_tuning_output's metadata.csv next to embeddings.npz).
        metadata.to_csv(output_dir / "metadata.csv", index=False)
    title = compose_clustering_tuning_title(output_dir, method)
    metric_cols = METHOD_METRIC_COLUMNS[method] + [c for c in CONSENSUS_METRIC_COLUMNS if c in results.columns]
    if method == "spectral" and "affinity" in tuning_grid:
        # project-clustering-tuning-redesign memory (26-08-26): the affinity-aware sweep's own
        # x-axis is whatever other key was actually swept (typically n_clusters) - "affinity"
        # itself and its own hyperparameter (n_neighbors/gamma) become the per-line grouping
        # inside plot_spectral_tuning, not a plot axis.
        other_params = [key for key in swept_params if key not in ("affinity", "n_neighbors", "gamma")]
        if len(other_params) == 1:
            plot_spectral_tuning(results, other_params[0], metric_cols, output_dir / "tuning_plot.png", title)
        else:
            logging.warning(
                "[%s] affinity-aware sweep has %d parameter(s) besides affinity/n_neighbors/gamma - "
                "no metric plot generated (plot_spectral_tuning needs exactly 1)",
                method,
                len(other_params),
            )
    elif method == "evidence_accumulation" and "threshold" in tuning_grid and len(swept_params) == 2:
        # project-clustering-tuning-redesign memory (26-08-26): threshold x Split-phase k -
        # one line per Split-phase k value, x=threshold (never a heatmap for this pair - lets a
        # human read whether the Merge-phase result is sensitive to "how much larger than
        # expected" the Split decomposition was).
        split_k_param = next(key for key in swept_params if key != "threshold")
        plot_grouped_tuning_metrics(results, "threshold", split_k_param, metric_cols, output_dir / "tuning_plot.png", title)
    elif len(swept_params) == 1:
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
        _write_standalone_diagnostic(output_dir, method, X, base_params, tuning_grid, metadata, title)

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
                "clustering_methods_requested": list(config.clustering_methods),
                "params_file": str(config.params_file),
                "output_root": str(config.output_root),
                "session_name": config.session_name,
                "overwrite": config.overwrite,
                "fine_tuning": config.fine_tuning,
                "reduced_data": config.reduced_data,
                "save_tuning_clusterings": config.save_tuning_clusterings,
                "run_notes": config.run_notes,
                # viz_embedding_path deliberately absent (unlike _config_summary's production
                # payload) - never read during fine-tuning, main() returns via _run_fine_tuning
                # before _resolve_viz_embedding is ever called, so it plays no role in this run.
                **reduction_columns,
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


def _combo_key(keys: list[str], combo: tuple) -> str:
    """Self-describing string key for one tuning combination, e.g.
    'n_clusters=3,random_state=0' - same names/order as tuning_grid.keys() for
    that run (matches labels_by_combo's own combo tuple, see
    run_clustering_tuning_sweep), so it's identical, character for character,
    to the string a caller rebuilds from that same row's own values in
    tuning_results.csv - no separate index file needed to join the two.
    Twin of dim_reduction.py's own _combo_key (not shared - each pipeline
    keeps its own private tuning-output helpers, same convention as the rest
    of this module's _write_tuning_output/_tuning_output_dir pair).
    """
    return ",".join(f"{key}={value}" for key, value in zip(keys, combo))


def _write_tuning_clusterings(output_dir: Path, labels_by_combo: dict[tuple, np.ndarray], keys: list[str]) -> None:
    """Serializes every combination's cluster-label array actually computed by the sweep
    (the full Cartesian product, not just what tuning_plot.png shows) into a single
    clusterings.npz, keyed by _combo_key. Opt-in via config.save_tuning_clusterings - before
    this flag existed no tuning run ever wrote this file, so it stays off by default
    (code_standards.md §0/§5: no silent change to an existing run's output shape).
    """
    arrays = {_combo_key(keys, combo): labels for combo, labels in labels_by_combo.items()}
    final_path = output_dir / "clusterings.npz"
    # Atomic (same rationale as dim_reduction.py::_write_tuning_embeddings, HIGH #24, 2026-08):
    # np.savez writing directly to the final path would leave a truncated clusterings.npz
    # sitting next to an otherwise-complete tuning_results.csv/config.md if the run were killed
    # mid-write (SLURM timeout, Ctrl+C) - temp-file-then-rename, same pattern as save_matrix.
    tmp_path = output_dir / f".clusterings_tmp_{uuid.uuid4().hex}.npz"
    np.savez(tmp_path, **arrays)
    tmp_path.replace(final_path)


def _write_stability_output(
    output_dir: Path, method: str, X: np.ndarray, tuning_grid: dict[str, list], stability_config: dict, title: str
) -> None:
    """kmeans/gmm's init/n_init stability-analysis diagnostic (see
    src/analysis/clustering_tuning.py::compute_stability_sweep) - writes
    stability_results.csv + stability_plot.png into the same tuning output_dir
    as the plain sweep. Representative target values (n_clusters/n_components)
    are derived from this run's own tuning_grid, not declared separately in
    stability_config - raises ValueError if STABILITY_TARGET_PARAM[method]
    isn't a swept key in this tuning_grid, since there's nothing to derive
    them from otherwise.
    """
    if method not in STABILITY_ELIGIBLE_METHODS:
        raise ValueError(f"stability analysis is only defined for {sorted(STABILITY_ELIGIBLE_METHODS)}, got {method!r}")
    target_param = STABILITY_TARGET_PARAM[method]
    if target_param not in tuning_grid:
        raise ValueError(f"[{method}] stability analysis needs {target_param!r} in tuning_grid to pick representative values")

    target_values = representative_values(tuning_grid[target_param])
    stability_df = compute_stability_sweep(
        method, X, target_values, stability_config["nuisance_values"], stability_config["n_init_range"], stability_config["n_repeats"]
    )
    stability_df.to_csv(output_dir / "stability_results.csv", index=False)
    plot_stability_analysis(
        stability_df, target_param, STABILITY_NUISANCE_PARAM[method], STABILITY_METRIC_NAME[method], output_dir / "stability_plot.png", title
    )


def _write_standalone_diagnostic(
    output_dir: Path, method: str, X: np.ndarray, base_params: dict, tuning_grid: dict[str, list], metadata: pd.DataFrame, title: str
) -> None:
    """Diagnostic plot(s) independent of which value in the swept grid ends up chosen - see
    src/analysis/clustering_tuning.py's module docstring for why these 3 (and only these 3)
    methods get one.
    """
    if method == "agglomerative":
        _write_agglomerative_diagnostics(output_dir, X, base_params, tuning_grid, metadata, title)
    elif method == "spectral":
        _write_spectral_diagnostics(output_dir, X, base_params, tuning_grid, title)
    elif method == "evidence_accumulation":
        _write_evidence_accumulation_diagnostics(output_dir, X, base_params, title)
    else:
        raise ValueError(f"no standalone diagnostic wired for method {method!r}")


def _default_convergence_checkpoints(n_repeats: int) -> list[int]:
    """5 evenly-spaced checkpoints up to base_params' own n_repeats (10%/25%/50%/75%/100%,
    floored at 1, deduplicated and sorted) - a reasonable default sweep of "how many repeats"
    to score convergence at, without requiring a separate config field for it.
    """
    fractions = (0.1, 0.25, 0.5, 0.75, 1.0)
    return sorted({max(1, round(n_repeats * fraction)) for fraction in fractions})


def _write_evidence_accumulation_diagnostics(output_dir: Path, X: np.ndarray, base_params: dict, title: str) -> None:
    """evidence_accumulation's 2 new standalone diagnostics (project-clustering-tuning-redesign
    memory, 26-08-26), both built directly on consensus_clustering.py's existing machinery, both
    computed once from base_params (independent of the swept tuning_grid, same "standalone"
    convention as agglomerative's dendrogram/spectral's eigengap):

    - n_repeats_convergence.csv/.png: does the co-occurrence matrix actually stabilize as
      n_repeats grows, or is base_params' own n_repeats arbitrary? (compute_evidence_
      accumulation_convergence, incremental checkpoints, never refit from scratch per value).
    - consensus_matrix_heatmap.png: Monti et al. 2003's own headline visualization, at
      base_params' own n_repeats/threshold - the co-occurrence matrix reordered by the final
      cluster assignment it actually produces.
    """
    base_method, split_params, n_repeats, base_seed, threshold = _validate_evidence_accumulation_params(base_params)

    checkpoints = _default_convergence_checkpoints(n_repeats)
    convergence_df = compute_evidence_accumulation_convergence(base_method, X, split_params, checkpoints, base_seed=base_seed)
    convergence_df.to_csv(output_dir / "n_repeats_convergence.csv", index=False)
    plot_tuning_curve(convergence_df, "n_repeats", "stability_score", output_dir / "n_repeats_convergence.png", title)
    logging.info("[evidence_accumulation] n_repeats convergence written to %s", output_dir / "n_repeats_convergence.png")

    co_occurrence = run_rsc_repeats(base_method, X, split_params, n_repeats, base_seed=base_seed)
    final_labels = assign_clusters_from_cooccurrence(co_occurrence, threshold)
    heatmap_path = output_dir / "consensus_matrix_heatmap.png"
    plot_consensus_matrix_heatmap(co_occurrence, final_labels, heatmap_path, title)
    logging.info("[evidence_accumulation] consensus matrix heatmap written to %s", heatmap_path)


def _write_spectral_diagnostics(output_dir: Path, X: np.ndarray, base_params: dict, tuning_grid: dict[str, list], title: str) -> None:
    """One eigengap plot per swept `affinity` value, one subplot per value of that affinity's
    own hyperparameter (SPECTRAL_AFFINITY_HYPERPARAM: `n_neighbors` for `nearest_neighbors`,
    `gamma` for `rbf`) - found 28-08-26 that the previous single eigengap_plot.png was always
    computed from `base_params` alone (compute_eigengap(X, base_params)), never reflecting a
    swept `affinity`/hyperparameter: the exact same "diagnostic frozen at base_params" gap
    already documented for agglomerative's dendrogram (clustering_tuning_guide.md), just found
    later for spectral. Falls back to a single affinity (`base_params`/default "rbf", matching
    compute_eigengap's own default) with a single subplot when `affinity` isn't swept - same
    grouping mechanism as _write_agglomerative_diagnostics' per-metric dendrogram grid.
    """
    affinities = list(dict.fromkeys(tuning_grid["affinity"])) if "affinity" in tuning_grid else [base_params.get("affinity", "rbf")]

    for affinity in affinities:
        hyperparam_name = SPECTRAL_AFFINITY_HYPERPARAM[affinity]
        if hyperparam_name in tuning_grid:
            hyperparam_values = list(dict.fromkeys(tuning_grid[hyperparam_name]))
        elif hyperparam_name in base_params:
            hyperparam_values = [base_params[hyperparam_name]]
        else:
            hyperparam_values = [None]  # let compute_eigengap fall back to its own default (n_neighbors=10/gamma=1.0)

        eigenvalues_by_label = {}
        for value in hyperparam_values:
            combo_params = {**base_params, "affinity": affinity}
            if value is not None:
                combo_params[hyperparam_name] = value
            label = f"{hyperparam_name}={value if value is not None else 'default'}"
            eigenvalues_by_label[label] = compute_eigengap(X, combo_params)

        eigengap_path = output_dir / f"eigengap_affinity={affinity}.png"
        plot_eigengaps_grid(eigenvalues_by_label, eigengap_path, f"{title} (affinity={affinity})")
        logging.info("[spectral] eigengap plot written to %s", eigengap_path)


def _write_agglomerative_diagnostics(
    output_dir: Path, X: np.ndarray, base_params: dict, tuning_grid: dict[str, list], metadata: pd.DataFrame, title: str
) -> None:
    """One dendrogram plot per swept `metric` value, one subplot per `linkage` valid for that
    metric (ward+non-euclidean skipped, same rule the sweep itself applies via
    is_invalid_ward_metric_combo) - found 28-08-26 that the previous per-linkage dendrogram
    (project-clustering-tuning-redesign memory, 26-08-26) was always computed at a fixed
    `metric` (base_params' default, "euclidean"), never reflecting a swept `metric`
    (clustering_tuning_guide.md documented this as a known limitation before it was fixed
    here). Falls back to a single metric/linkage (base_params/defaults) with a single subplot
    when neither is swept - same shape, no separate code path needed. Plus a metric-selection
    pre-check, independent of any fit: one interclass-distance heatmap per swept `metric` value
    (or the base_params/default "euclidean" metric alone when metric isn't swept), using
    "dataset" as the weak ground-truth proxy grouping - skipped with a warning (not a sweep
    failure) when metadata has no "dataset" column to use as one.
    """
    linkages = list(dict.fromkeys(tuning_grid["linkage"])) if "linkage" in tuning_grid else [base_params.get("linkage", "ward")]
    metrics = list(dict.fromkeys(tuning_grid["metric"])) if "metric" in tuning_grid else [base_params.get("metric", "euclidean")]

    # See compute_dendrogram_linkage's distance_cache docstring: a jaccard/dice distance matrix
    # depends only on (X, metric), not on linkage - shared here across every linkage sharing the
    # same metric, instead of recomputed once per (metric, linkage) combination.
    distance_cache: dict[str, np.ndarray] = {}
    for metric in metrics:
        linkage_matrices = {}
        for linkage in linkages:
            combo_params = {**base_params, "linkage": linkage, "metric": metric}
            if is_invalid_ward_metric_combo(combo_params):
                continue  # same skip the sweep itself applies - ward requires euclidean/l2
            linkage_matrices[linkage] = compute_dendrogram_linkage(X, combo_params, distance_cache)

        dendrogram_path = output_dir / f"dendrogram_metric={metric}.png"
        plot_dendrograms_grid(linkage_matrices, dendrogram_path, f"{title} (metric={metric})")
        logging.info("[agglomerative] dendrogram written to %s", dendrogram_path)

    if "dataset" not in metadata.columns:
        logging.warning(
            "[agglomerative] metadata has no 'dataset' column - skipping interclass_distance_matrix.png "
            "(no weak ground-truth proxy grouping available)"
        )
        return

    metrics = list(dict.fromkeys(tuning_grid["metric"])) if "metric" in tuning_grid else [base_params.get("metric", "euclidean")]
    proxy_labels = metadata["dataset"].to_numpy()
    results_by_metric = {metric: compute_interclass_distance_matrix(X, proxy_labels, metric) for metric in metrics}
    interclass_path = output_dir / "interclass_distance_matrix.png"
    plot_interclass_distance_matrix(results_by_metric, interclass_path, title)
    logging.info("[agglomerative] interclass distance matrix written to %s", interclass_path)


def _log_path(config: ClusteringConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{LOG_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
