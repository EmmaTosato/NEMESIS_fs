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


def rsc_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    """Repeated Spectral Clustering (RSC; Tshimanga et al. 2025, applied by
    Zanola et al. 2026 - papers/nemesis/Zanola et al - 2026 - ...): spectral
    clustering's internal k-means step repeated `n_repeats` times (only
    random_state varying) to build a co-occurrence matrix, then final labels
    derived from that matrix - not from any single one of the N runs - via
    src.analysis.consensus_clustering.assign_clusters_from_cooccurrence (see
    that function's docstring for exactly which algorithm and why).

    params: same shape as spectral_cluster's (n_clusters, affinity,
    n_neighbors, ...) plus a required n_repeats and an optional base_seed
    (default 0, forwarded to run_rsc_repeats). A fixed 'random_state' is
    rejected explicitly, not silently overridden - run_rsc_repeats assigns
    each of the n_repeats runs its own seed (base_seed + i); a single fixed
    seed here would make every repeat identical, producing a degenerate
    (all-0/1) co-occurrence matrix instead of a meaningful stability signal.

    Local import below (not at module top) is deliberate: consensus_clustering
    imports CLUSTERING_METHODS from this module for its generic RSC/Monti
    diagnostics (any of kmeans/gmm/spectral), so a module-level import here
    in the other direction would be circular.
    """
    from src.analysis.consensus_clustering import assign_clusters_from_cooccurrence, run_rsc_repeats

    params = dict(params)
    if "n_repeats" not in params:
        raise ValueError("rsc requires 'n_repeats' in params - how many spectral clustering repeats build the co-occurrence matrix")
    n_repeats = params.pop("n_repeats")
    base_seed = params.pop("base_seed", 0)
    if "n_clusters" not in params:
        raise ValueError("rsc requires 'n_clusters' in params")
    n_clusters = params["n_clusters"]
    if "random_state" in params:
        raise ValueError(
            "rsc does not take a fixed 'random_state' - each of the n_repeats runs gets its own seed "
            "(base_seed + i) internally; a single shared random_state would make every repeat identical"
        )

    co_occurrence = run_rsc_repeats("spectral", X, params, n_repeats, base_seed=base_seed)
    return assign_clusters_from_cooccurrence(co_occurrence, n_clusters)


CLUSTERING_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "kmeans": kmeans_cluster,
    "agglomerative": agglomerative_cluster,
    "gmm": gmm_cluster,
    "hdbscan": hdbscan_cluster,
    "spectral": spectral_cluster,
    "rsc": rsc_cluster,
}
