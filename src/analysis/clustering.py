"""Clustering strategies: a plain dict[str, Callable] registry, same pattern as reduction.py.

Each function is a pure array-in/labels-out transform: **params is unpacked
straight into the estimator's constructor, no in-code defaults - every
hyperparameter (e.g. KMeans' n_clusters) comes from
config/registry/params_clustering.json (see src/analysis/params.py).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from sklearn.cluster import HDBSCAN, AgglomerativeClustering, KMeans, SpectralClustering
from sklearn.mixture import GaussianMixture

from src.analysis.adp import adp_cluster


def kmeans_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return KMeans(**params).fit_predict(X)


def agglomerative_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return AgglomerativeClustering(**params).fit_predict(X)


def gmm_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return GaussianMixture(**params).fit_predict(X)


def hdbscan_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return HDBSCAN(**params).fit_predict(X)


def hdbscan_soft_fit(X: np.ndarray, params: dict):
    """The fitted HDBSCAN of the standalone `hdbscan` package, with `prediction_data=True` so that
    `hdbscan.all_points_membership_vectors` (soft clustering: one probability per subject and cluster)
    works on it. The package is a different implementation from scikit-learn's and shares neither its
    `min_samples` convention (the core distance is the distance to the min_samples-th neighbour) nor its
    exact partitions: runs of "hdbscan_soft" and "hdbscan" are not comparable."""
    try:
        import hdbscan
    except ImportError as exc:
        raise ImportError("hdbscan_soft needs the standalone `hdbscan` package (listed in environment.yml) - not installed") from exc
    return hdbscan.HDBSCAN(**params, prediction_data=True).fit(np.asarray(X, dtype=np.float64))


def hdbscan_soft_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return hdbscan_soft_fit(X, params).labels_


def soft_membership_matrix(fitted) -> np.ndarray:
    """The soft clustering of a `hdbscan_soft_fit` estimator: (n_subjects, n_clusters), entry [i, j] the
    probability that subject i belongs to cluster j (`hdbscan.all_points_membership_vectors`). The rows do
    not sum to 1: what is missing is the probability of being noise. The package numbers its clusters
    0..k-1, which is the column order. A fit with no cluster (every subject noise) has no column: the
    matrix is (n_subjects, 0), the documented answer for that outcome, not a missing value.

    Raises ValueError if the package returns a matrix whose column count is not the number of clusters.
    """
    labels = fitted.labels_
    n_clusters = len(np.unique(labels[labels != -1]))
    if n_clusters == 0:
        return np.empty((len(labels), 0))
    from hdbscan import all_points_membership_vectors

    membership = all_points_membership_vectors(fitted)
    if membership.shape != (len(labels), n_clusters):
        raise ValueError(
            f"all_points_membership_vectors returned {membership.shape} for {len(labels)} subjects and "
            f"{n_clusters} clusters - expected one column per cluster"
        )
    return membership


def own_cluster_membership(membership: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Per subject, the soft probability of belonging to its own cluster (the entry of its label's
    column). Noise (label -1) has no own cluster: NaN, not 0 - the subject belongs to none, and a 0
    would read as a measured improbability."""
    labels = np.asarray(labels)
    own = np.full(len(labels), np.nan)
    clustered = np.flatnonzero(labels != -1)
    own[clustered] = membership[clustered, labels[clustered]]
    return own


def spectral_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return SpectralClustering(**params).fit_predict(X)


CLUSTERING_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "kmeans": kmeans_cluster,
    "agglomerative": agglomerative_cluster,
    "gmm": gmm_cluster,
    "hdbscan": hdbscan_cluster,
    "hdbscan_soft": hdbscan_soft_cluster,
    "spectral": spectral_cluster,
    "adp": adp_cluster,
}
