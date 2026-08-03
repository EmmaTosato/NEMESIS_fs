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


def kmeans_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return KMeans(**params).fit_predict(X)


def agglomerative_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return AgglomerativeClustering(**params).fit_predict(X)


def gmm_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return GaussianMixture(**params).fit_predict(X)


def hdbscan_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return HDBSCAN(**params).fit_predict(X)


def spectral_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    return SpectralClustering(**params).fit_predict(X)


CLUSTERING_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "kmeans": kmeans_cluster,
    "agglomerative": agglomerative_cluster,
    "gmm": gmm_cluster,
    "hdbscan": hdbscan_cluster,
    "spectral": spectral_cluster,
}
