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


def evidence_accumulation_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    """Evidence Accumulation Clustering (Fred & Jain, 2002 - ICPR, "Data
    clustering using evidence accumulation" - knowledge/sota/Fred et al - 2002
    - Data clustering using evidence accumulation.md, the exact paper Zanola
    et al. 2026 cites for RSC): repeat a base clustering method `n_repeats`
    times (only random_state varying), build a co-occurrence matrix from how
    often each pair of subjects ends up together, then derive final labels
    from that matrix - not from any single one of the N runs - via
    src.analysis.consensus_clustering.assign_clusters_from_cooccurrence.

    Two design parameters, matching the paper's own "Split" and "Merge"
    phases - deliberately *not* the same knob:
    - `K_PARAM_NAME[base_method]` (e.g. `n_clusters` for kmeans/spectral,
      `n_components` for gmm) is the **Split**-phase decomposition size fed
      to each of the `n_repeats` runs - per the paper, this should be
      *larger* than the true expected number of clusters (a large number of
      small, compact clusters to combine), not the final cluster count.
    - `threshold` (the paper's `t`, forwarded to
      assign_clusters_from_cooccurrence) is the **Merge**-phase cut: two
      subjects end up in the same final cluster iff their co-association
      exceeds `t`. The final number of clusters is not chosen in advance -
      it emerges from the data. Paper's own default: `t = 0.5`.

    Method-agnostic on purpose: `params["base_method"]` selects which of
    CONSENSUS_ELIGIBLE_METHODS (kmeans/gmm/spectral - the only 3 with genuine
    internal stochasticity to repeat) gets repeated. Zanola et al. 2026's RSC
    (Tshimanga et al. 2025, knowledge/nemesis/Zanola et al - 2026 - ...) is
    exactly this recipe specialized to base_method="spectral" - not
    reproduced here as a separate branded method, since Fred & Jain's own
    algorithm never fixes the base clusterer.

    params: {"base_method": one of CONSENSUS_ELIGIBLE_METHODS, "n_repeats":
    int, "threshold": float in [0, 1], "base_seed": int (optional, default
    0), plus every hyperparameter base_method's own CLUSTERING_METHODS
    function needs (incl. K_PARAM_NAME[base_method], for the Split phase
    only - see above)}. A fixed 'random_state' is rejected explicitly, not
    silently overridden - each of the n_repeats runs gets its own seed
    (base_seed + i) internally; a single shared one would make every repeat
    identical, producing a degenerate (all-0/1) co-occurrence matrix instead
    of a meaningful stability signal.

    Local import below (not at module top) is deliberate: consensus_clustering
    imports CLUSTERING_METHODS from this module for its generic RSC/Monti
    diagnostics, so a module-level import here in the other direction would
    be circular.
    """
    from src.analysis.consensus_clustering import assign_clusters_from_cooccurrence, run_rsc_repeats

    base_method, split_params, n_repeats, base_seed, threshold = _validate_evidence_accumulation_params(params)
    co_occurrence = run_rsc_repeats(base_method, X, split_params, n_repeats, base_seed=base_seed)
    return assign_clusters_from_cooccurrence(co_occurrence, threshold)


def _validate_evidence_accumulation_params(params: dict) -> tuple[str, dict, int, int, float]:
    """Parsing/validation shared between evidence_accumulation_cluster above and its
    tuning-sweep fast path (clustering_tuning.py - AUDIT_FINDINGS.md #35): split into its
    own function so both call sites raise identically instead of duplicating this logic.
    Returns (base_method, split_params, n_repeats, base_seed, threshold) - split_params is
    `params` with base_method/n_repeats/base_seed/threshold popped, i.e. exactly what
    run_rsc_repeats needs (base_method's own hyperparameters, including the Split-phase
    K_PARAM_NAME[base_method]) - never threshold, which only drives the separate,
    cheap Merge-phase cut (assign_clusters_from_cooccurrence).
    """
    from src.analysis.consensus_clustering import CONSENSUS_ELIGIBLE_METHODS, K_PARAM_NAME

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
    if "threshold" not in params:
        raise ValueError(
            "evidence_accumulation requires 'threshold' in params - the co-association similarity cut (Fred & "
            "Jain 2002's t) that determines how many clusters emerge in the Merge phase"
        )
    threshold = params.pop("threshold")
    k_param = K_PARAM_NAME[base_method]
    if k_param not in params:
        raise ValueError(
            f"evidence_accumulation with base_method={base_method!r} requires {k_param!r} in params (the "
            "Split-phase decomposition size for each repeat, not the final cluster count)"
        )
    if "random_state" in params:
        raise ValueError(
            "evidence_accumulation does not take a fixed 'random_state' - each of the n_repeats runs gets its own "
            "seed (base_seed + i) internally; a single shared random_state would make every repeat identical"
        )
    return base_method, params, n_repeats, base_seed, threshold


CLUSTERING_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "kmeans": kmeans_cluster,
    "agglomerative": agglomerative_cluster,
    "gmm": gmm_cluster,
    "hdbscan": hdbscan_cluster,
    "hdbscan_soft": hdbscan_soft_cluster,
    "spectral": spectral_cluster,
    "evidence_accumulation": evidence_accumulation_cluster,
    "adp": adp_cluster,
}
