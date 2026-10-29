"""The numbers of one production run of clustering.py: `production_results.csv` (one row per measure of the run) and
`production_results_per_cluster.csv` (one row per cluster).

The three methods of the tuning chain have them: agglomerative, hdbscan and hdbscan_soft. A measure that is not defined for
the run (fewer than 2 clusters, a distance it needs to be Euclidean, a refit that does not reproduce the labels) has an
empty `value` and the reason in `note`: never a made-up number. config.md keeps only the parameters the run started from.

The functions here are the single place that computes these numbers: the production run writes them as it clusters, and
the backfill of runs already written calls the same ones on the saved matrix and labels.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.clustering_evaluation import GeometricSummary, geometric_summary, model_fit_metrics
from src.analysis.dbcv import RunDbcv, run_dbcv
from src.analysis.partition_shape import NOISE_LABEL, partition_shape

RESULTS_FILENAME = "production_results.csv"
PER_CLUSTER_FILENAME = "production_results_per_cluster.csv"
RESULTS_COLUMNS = ["metric", "value", "note"]
RESULTS_METHODS = ("agglomerative", "hdbscan", "hdbscan_soft")

EUCLIDEAN_ONLY_NOTE = "Euclidean distance only"
NO_CLUSTER_NOTE = "no cluster: every subject is noise"

_NAN = float("nan")


@dataclass(frozen=True)
class ProductionResults:
    """The two tables of a run, and what the figures of the run are drawn from: `summary` (agglomerative: the silhouette of
    every subject behind silhouette_plot.png, None when it was not defined) and `dbcv` (density methods: the DBCV per
    cluster behind dbcv_plot.png)."""

    results: pd.DataFrame
    per_cluster: pd.DataFrame
    summary: GeometricSummary | None = None
    dbcv: RunDbcv | None = None


def _results_table(rows: list[tuple[str, float, str]]) -> pd.DataFrame:
    """The rows of production_results.csv. `value` is an object column so that a count is written as `3`, not `3.0`."""
    metrics, values, notes = (list(column) for column in zip(*rows))
    return pd.DataFrame({"metric": metrics, "value": pd.Series(values, dtype=object), "note": notes}, columns=RESULTS_COLUMNS)


def _cluster_base(labels: np.ndarray) -> pd.DataFrame:
    """One row per cluster (noise left out): its label and its number of subjects, in label order."""
    sizes = partition_shape(labels).cluster_sizes
    return pd.DataFrame({"cluster": pd.Series(list(sizes), dtype=int), "n": pd.Series(list(sizes.values()), dtype=int)})


def agglomerative_results(X: np.ndarray, labels: np.ndarray, params: dict) -> ProductionResults:
    """The results of an agglomerative run on the matrix it was clustered on, `params` being the run's own.

    silhouette (in the run's own distance), calinski_harabasz, davies_bouldin and dunn (Euclidean only: empty with the note
    otherwise), largest_cluster_share, cophenetic_correlation and dendrogram_jump (the tree is refit with the run's params
    and used only if it gives the stored labels). What `geometric_summary` or `model_fit_metrics` cannot define for the run
    (they raise ValueError: fewer than 2 clusters, a refit that does not reproduce the labels) is empty with the reason."""
    labels = np.asarray(labels)
    shape = partition_shape(labels)
    try:
        summary, summary_note = geometric_summary(X, labels, params), ""
    except ValueError as exc:
        summary, summary_note = None, f"not defined: {exc}"
    try:
        tree, tree_note = model_fit_metrics("agglomerative", X, params, labels), ""
    except ValueError as exc:
        tree, tree_note = None, f"not defined: {exc}"

    if summary is None:
        index_rows = [(name, _NAN, summary_note) for name in ("silhouette", "calinski_harabasz", "davies_bouldin", "dunn")]
    else:
        euclidean = summary.metric == "euclidean"
        note = "" if euclidean else EUCLIDEAN_ONLY_NOTE
        index_rows = [
            ("silhouette", summary.silhouette, ""),
            # GeometricSummary has these three as NaN unless the distance is Euclidean: the note says why
            ("calinski_harabasz", summary.calinski_harabasz, note),
            ("davies_bouldin", summary.davies_bouldin, note),
            ("dunn", summary.dunn, note),
        ]
    tree_rows = (
        [("cophenetic_correlation", _NAN, tree_note), ("dendrogram_jump", _NAN, tree_note)]
        if tree is None
        else [("cophenetic_correlation", tree["cophenetic_correlation"], ""), ("dendrogram_jump", tree["dendrogram_jump"], "")]
    )
    share_note = NO_CLUSTER_NOTE if np.isnan(shape.largest_cluster_share) else ""
    rows = [*index_rows, ("largest_cluster_share", shape.largest_cluster_share, share_note), *tree_rows]

    if summary is None:
        per_cluster = _cluster_base(labels).assign(silhouette_mean=_NAN, share_negative=_NAN)
    else:
        per_cluster = summary.clusters.rename_axis("cluster").reset_index()
    return ProductionResults(_results_table(rows), per_cluster, summary=summary)


def density_results(
    X: np.ndarray, labels: np.ndarray, params: dict, membership_own: np.ndarray, persistence: np.ndarray | None = None
) -> ProductionResults:
    """The results of an hdbscan (`persistence` None) or hdbscan_soft run, on the matrix it was clustered on.

    `membership_own` is the probability of every subject of belonging to its own cluster, NaN for the noise (it has no
    cluster); `persistence` is the stability of every cluster, `cluster_persistence_` of the fitted model, one value for each
    cluster label 0..k-1. Rows: n_clusters_found, noise_fraction, largest_cluster_share, dbcv (empty with the reason when
    it is not defined), membership_mean (mean of `membership_own` over the clustered subjects) and, for hdbscan_soft,
    persistence_mean (mean over the clusters). Raises ValueError for a `membership_own` that does not match the labels, or a
    `persistence` that is not one value per cluster."""
    labels = np.asarray(labels)
    membership_own = np.asarray(membership_own, dtype=float)
    if membership_own.shape != labels.shape:
        raise ValueError(f"membership_own has shape {membership_own.shape}, the labels {labels.shape}")
    noise = labels == NOISE_LABEL
    if not np.array_equal(noise, np.isnan(membership_own)):
        raise ValueError("membership_own must be NaN exactly for the noise subjects (label -1): the noise has no cluster")
    shape = partition_shape(labels)
    if persistence is not None:
        persistence = np.asarray(persistence, dtype=float)
        if list(shape.cluster_sizes) != list(range(shape.n_clusters)) or persistence.shape != (shape.n_clusters,):
            raise ValueError(
                f"persistence needs one value per cluster label 0..{shape.n_clusters - 1}, got {persistence.shape} "
                f"for the clusters {list(shape.cluster_sizes)}"
            )

    dbcv = run_dbcv(X, labels, params)
    no_cluster = shape.n_clusters == 0
    rows = [
        ("n_clusters_found", shape.n_clusters, ""),
        ("noise_fraction", shape.noise_fraction, ""),
        ("largest_cluster_share", shape.largest_cluster_share, NO_CLUSTER_NOTE if no_cluster else ""),
        ("dbcv", _NAN if dbcv.note else dbcv.score, dbcv.note),
        ("membership_mean", _NAN if no_cluster else float(membership_own[~noise].mean()), NO_CLUSTER_NOTE if no_cluster else ""),
    ]
    if persistence is not None:
        rows.append(("persistence_mean", _NAN if no_cluster else float(persistence.mean()), NO_CLUSTER_NOTE if no_cluster else ""))

    per_cluster = _cluster_base(labels)
    per_cluster["dbcv"] = per_cluster["cluster"].map(dict(zip(dbcv.clusters["cluster"], dbcv.clusters["dbcv"])))
    per_cluster["membership_mean"] = [float(membership_own[labels == cluster].mean()) for cluster in per_cluster["cluster"]]
    if persistence is not None:
        per_cluster["persistence"] = persistence[per_cluster["cluster"].to_numpy(dtype=int)]
    return ProductionResults(_results_table(rows), per_cluster, dbcv=dbcv)


def compute_production_results(
    method: str,
    X: np.ndarray,
    labels: np.ndarray,
    params: dict,
    membership_own: np.ndarray | None = None,
    persistence: np.ndarray | None = None,
) -> ProductionResults:
    """The results of a production run of `method` (one of RESULTS_METHODS). `membership_own` is required for the density
    methods and `persistence` for hdbscan_soft only (hdbscan of sklearn has none). Raises ValueError otherwise."""
    if method == "agglomerative":
        if membership_own is not None or persistence is not None:
            raise ValueError("agglomerative has no membership or persistence")
        return agglomerative_results(X, labels, params)
    if method in ("hdbscan", "hdbscan_soft"):
        if membership_own is None:
            raise ValueError(f"{method} needs membership_own (the probability of every subject in its own cluster)")
        if (persistence is None) != (method == "hdbscan"):
            raise ValueError("persistence is for hdbscan_soft only: hdbscan of sklearn does not have it")
        return density_results(X, labels, params, membership_own, persistence)
    raise ValueError(f"no production results for method {method!r} - known: {list(RESULTS_METHODS)}")


def _write_csv(table: pd.DataFrame, path: Path) -> None:
    """Writes through a temporary file, so that a run killed mid-write never leaves a half-written table."""
    temporary = path.with_name(path.name + ".tmp")
    table.to_csv(temporary, index=False)
    os.replace(temporary, path)


def write_production_results(output_dir: Path, results: ProductionResults, overwrite: bool = False) -> list[Path]:
    """Writes the two tables into `output_dir` and returns their paths. Raises FileExistsError, before writing anything,
    if one of them exists and `overwrite` is False."""
    paths = [output_dir / RESULTS_FILENAME, output_dir / PER_CLUSTER_FILENAME]
    existing = [path.name for path in paths if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"{output_dir} already has {existing}: pass overwrite=True to replace them")
    _write_csv(results.results, paths[0])
    _write_csv(results.per_cluster, paths[1])
    return paths
