"""DBCV (Density-Based Clustering Validation, Moulavi et al. 2014), the internal index of the density methods.

`dbcv` is the index itself; `run_dbcv` is what the tuning evaluations (src/analysis/clustering_tuning_analysis.py::
density_metrics), the production run of hdbscan / hdbscan_soft (src/pipeline/clustering.py) and the Embedding Explorer
(src/analysis/clustering_evaluation.py::density_summary) all call, so the three give the same number, and the same
"not defined" answer with its reason, for the same labels. Explanation and source: knowledge/notes/
dim_reduction_clustering/clustering_methods/evaluation_metrics.md §8.

Why not the silhouette-family indices for these methods: they are computed on the non-noise subjects only, so
discarding the hardest subjects as noise raises them, and they assume compact clusters. DBCV weighs each cluster by
its share of all the subjects, noise included, so the noise lowers the score by itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.clustering_tuning import require_euclidean_compatible
from src.analysis.partition_shape import NOISE_LABEL, partition_shape

CLUSTER_COLUMNS = ["cluster", "n", "dbcv"]


def dbcv(X: np.ndarray, labels: np.ndarray) -> tuple[float, dict[int, float]]:
    """DBCV of a clustering, euclidean, over all the subjects (label -1 is noise).

    Returns (score, per_cluster): `score` in [-1, 1], higher is better, the average of the clusters' own scores
    weighted by |cluster| / n_subjects (noise counted in n_subjects); `per_cluster` maps each cluster label to its
    own score.

    - Fewer than 2 clusters (all noise, or a single cluster): the index is undefined (it compares clusters with each
      other), so `score` is NaN and `per_cluster` is empty. The `hdbscan` package returns the integer 0 for "all
      noise", indistinguishable from a real score of 0: that case is never passed to it.
    - A cluster with a single subject has no internal structure to measure: raises ValueError (the density methods
      of this project never produce one, min_cluster_size is at least 2).
    - Raises ValueError for a `labels`/`X` length mismatch or a non-finite value in `X`.
    """
    X = np.asarray(X)
    labels = np.asarray(labels)
    if X.ndim != 2 or len(X) != len(labels):
        raise ValueError(f"X must be 2D with one row per label, got X.shape={X.shape} and {len(labels)} labels")
    if not np.isfinite(X).all():
        raise ValueError("DBCV needs finite values: X contains NaN or inf")

    clusters, sizes = np.unique(labels[labels != NOISE_LABEL], return_counts=True)
    if len(clusters) < 2:
        return float("nan"), {}
    singletons = clusters[sizes < 2].tolist()
    if singletons:
        raise ValueError(f"DBCV needs at least 2 subjects per cluster, cluster(s) {singletons} have one")

    try:
        from hdbscan.validity import validity_index  # the package is the reference implementation of the index
    except ImportError as exc:
        raise ImportError("DBCV needs the standalone `hdbscan` package (listed in environment.yml) - not installed") from exc

    compact = np.full(len(labels), NOISE_LABEL)
    for new_label, cluster in enumerate(clusters):
        compact[labels == cluster] = new_label
    score, per_cluster = validity_index(X, compact, metric="euclidean", per_cluster_scores=True)
    return float(score), {int(cluster): float(per_cluster[i]) for i, cluster in enumerate(clusters)}


@dataclass(frozen=True)
class RunDbcv:
    """The DBCV of one run: `score` (NaN when undefined, see `note`), `clusters` (columns cluster, n, dbcv; empty when
    undefined) and `note`, why it is undefined ("" when it is not)."""

    score: float
    clusters: pd.DataFrame
    note: str


def run_dbcv(X: np.ndarray, labels: np.ndarray, combo_params: dict) -> RunDbcv:
    """DBCV of a run, with its per-cluster table. `combo_params` is the run's own params.

    Two outcomes are legitimate and come back as NaN with the reason in `note`, never as an error and never as a
    number: a run clustered under a non-Euclidean metric/affinity (DBCV here is Euclidean, it is not computed in
    another geometry) and a run with fewer than 2 clusters (the index compares clusters with each other).
    Everything `dbcv` raises for stays an error (a cluster of one subject, non-finite values, a length mismatch)."""
    try:
        require_euclidean_compatible(combo_params)
    except ValueError:
        return RunDbcv(float("nan"), pd.DataFrame(columns=CLUSTER_COLUMNS), f"not defined for metric={combo_params.get('metric')!r}: DBCV is Euclidean")
    score, per_cluster = dbcv(X, labels)
    if not per_cluster:
        return RunDbcv(score, pd.DataFrame(columns=CLUSTER_COLUMNS), "not defined: fewer than 2 clusters")
    sizes = partition_shape(labels).cluster_sizes
    clusters = pd.DataFrame({"cluster": list(per_cluster), "n": [sizes[c] for c in per_cluster], "dbcv": list(per_cluster.values())})
    return RunDbcv(score, clusters, "")
