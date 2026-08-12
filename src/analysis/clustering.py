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


def evidence_accumulation_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    """Evidence Accumulation Clustering (Fred & Jain, 2002 - ICPR, "Data
    clustering using evidence accumulation" - papers/sota/Fred et al - 2002
    - Data clustering using evidence accumulation.md, the exact paper Zanola
    et al. 2026 cites for RSC): repeat a base clustering method `n_repeats`
    times (only random_state varying), build a co-occurrence matrix from how
    often each pair of subjects ends up together, then derive final labels
    from that matrix - not from any single one of the N runs - via
    src.analysis.consensus_clustering.assign_clusters_from_cooccurrence (see
    that function's docstring for exactly which algorithm, incl. one
    deliberate deviation from the paper's own cut criterion).

    Method-agnostic on purpose: `params["base_method"]` selects which of
    CONSENSUS_ELIGIBLE_METHODS (kmeans/gmm/spectral - the only 3 with genuine
    internal stochasticity to repeat) gets repeated. Zanola et al. 2026's RSC
    (Tshimanga et al. 2025, papers/nemesis/Zanola et al - 2026 - ...) is
    exactly this recipe specialized to base_method="spectral" - not
    reproduced here as a separate branded method, since Fred & Jain's own
    algorithm never fixes the base clusterer.

    params: {"base_method": one of CONSENSUS_ELIGIBLE_METHODS, "n_repeats":
    int, "base_seed": int (optional, default 0), plus every hyperparameter
    base_method's own CLUSTERING_METHODS function needs - including
    K_PARAM_NAME[base_method] ("n_clusters" for kmeans/spectral,
    "n_components" for gmm), used both for each repeat and for the final cut
    of the co-occurrence matrix}. A fixed 'random_state' is rejected
    explicitly, not silently overridden - each of the n_repeats runs gets
    its own seed (base_seed + i) internally; a single shared one would make
    every repeat identical, producing a degenerate (all-0/1) co-occurrence
    matrix instead of a meaningful stability signal.

    Local import below (not at module top) is deliberate: consensus_clustering
    imports CLUSTERING_METHODS from this module for its generic RSC/Monti
    diagnostics, so a module-level import here in the other direction would
    be circular.
    """
    from src.analysis.consensus_clustering import (
        CONSENSUS_ELIGIBLE_METHODS,
        K_PARAM_NAME,
        assign_clusters_from_cooccurrence,
        run_rsc_repeats,
    )

    params = dict(params)
    if "base_method" not in params:
        raise ValueError(f"evidence_accumulation requires 'base_method' in params - one of {sorted(CONSENSUS_ELIGIBLE_METHODS)}")
    base_method = params.pop("base_method")
    if base_method not in CONSENSUS_ELIGIBLE_METHODS:
        raise ValueError(f"'base_method' must be one of {sorted(CONSENSUS_ELIGIBLE_METHODS)}, got {base_method!r}")
    if "n_repeats" not in params:
        raise ValueError("evidence_accumulation requires 'n_repeats' in params - how many base_method repeats build the co-occurrence matrix")
    n_repeats = params.pop("n_repeats")
    base_seed = params.pop("base_seed", 0)
    k_param = K_PARAM_NAME[base_method]
    if k_param not in params:
        raise ValueError(f"evidence_accumulation with base_method={base_method!r} requires {k_param!r} in params")
    n_clusters = params[k_param]
    if "random_state" in params:
        raise ValueError(
            "evidence_accumulation does not take a fixed 'random_state' - each of the n_repeats runs gets its own "
            "seed (base_seed + i) internally; a single shared random_state would make every repeat identical"
        )

    co_occurrence = run_rsc_repeats(base_method, X, params, n_repeats, base_seed=base_seed)
    return assign_clusters_from_cooccurrence(co_occurrence, n_clusters)


CLUSTERING_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "kmeans": kmeans_cluster,
    "agglomerative": agglomerative_cluster,
    "gmm": gmm_cluster,
    "hdbscan": hdbscan_cluster,
    "spectral": spectral_cluster,
    "evidence_accumulation": evidence_accumulation_cluster,
}
