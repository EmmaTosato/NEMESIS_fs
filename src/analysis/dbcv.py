"""DBCV (Density-Based Clustering Validation, Moulavi et al. 2014), the internal index of the density methods.

One function, `dbcv`, used by the tuning evaluations (src/analysis/clustering_tuning_analysis.py::density_metrics),
the production run of hdbscan / hdbscan_soft (src/pipeline/clustering.py) and the Embedding Explorer, so the three
give the same number for the same labels. Explanation and source: knowledge/notes/dim_reduction_clustering/
clustering_methods/evaluation_metrics.md §8.

Why not the silhouette-family indices for these methods: they are computed on the non-noise subjects only, so
discarding the hardest subjects as noise raises them, and they assume compact clusters. DBCV weighs each cluster by
its share of all the subjects, noise included, so the noise lowers the score by itself.
"""

from __future__ import annotations

import numpy as np

NOISE_LABEL = -1


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
