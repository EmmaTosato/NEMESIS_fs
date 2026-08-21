"""Manual fine-tuning sweep for clustering methods (kmeans, agglomerative, gmm,
hdbscan, spectral) - mirrors src/analysis/tuning.py's dim-reduction sweep, but
clustering has no ground truth to score against: every generic metric here is
an *internal* validation index computed straight from (X, cluster_labels) -
silhouette / Calinski-Harabasz / Davies-Bouldin, identically for every
method's own swept tuning_grid (never compared across methods - these indices
aren't meaningful cross-method, only within one method's own grid). No
automatic selection, same philosophy as tuning.py: a human reads
tuning_results.csv/tuning_plot.png and picks a value by hand.

Two kinds of extras beyond the 3 generic metrics, see METHOD_METRIC_COLUMNS:
- Per-combination scalar columns, added to the same sweep row when the method
  exposes one after fitting: kmeans' inertia_ (elbow criterion), gmm's
  bic_/aic_ (likelihood-based criteria, unlike the other 3 which are purely
  geometric). HDBSCAN's noise_fraction is generic (computed for every method)
  but only ever non-zero for HDBSCAN, so it's only surfaced as a plotted
  metric there (see clustering.py's _write_tuning_output).
- Standalone, single-fit diagnostics independent of which n_clusters ends up
  chosen - not a function of the swept grid, so they don't belong as sweep
  columns: agglomerative's dendrogram (the full merge hierarchy, computed
  from base_params - see compute_dendrogram_linkage), spectral's eigengap
  (biggest gap between consecutive eigenvalues of the affinity graph's
  Laplacian - the eigengap heuristic, a more principled criterion for
  spectral clustering than the generic geometric indices - see
  compute_eigengap). HDBSCAN gets no standalone diagnostic - unlike DBSCAN
  (replaced here), it has no single distance threshold (eps) to read off a
  plot by eye; min_cluster_size is judged directly from the swept
  noise_fraction/silhouette columns instead.
"""

from __future__ import annotations

import itertools
import logging
from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy.linalg import eigh
from scipy.sparse import csgraph
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_samples, silhouette_score
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import kneighbors_graph

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.consensus_clustering import (
    CONSENSUS_ELIGIBLE_METHODS,
    K_PARAM_NAME,
    compute_monti_stability,
    compute_rsc_eigengap,
    run_monti_repeats,
    run_rsc_repeats,
)

CONSENSUS_METRIC_COLUMNS = ("rsc_eigengap", "monti_stability")

METHOD_METRIC_COLUMNS: dict[str, list[str]] = {
    "kmeans": ["silhouette", "calinski_harabasz", "davies_bouldin", "inertia"],
    "agglomerative": ["silhouette", "calinski_harabasz", "davies_bouldin"],
    "gmm": ["silhouette", "calinski_harabasz", "davies_bouldin", "bic", "aic"],
    "hdbscan": ["silhouette", "calinski_harabasz", "davies_bouldin", "noise_fraction"],
    "spectral": ["silhouette", "calinski_harabasz", "davies_bouldin"],
    "evidence_accumulation": ["silhouette", "calinski_harabasz", "davies_bouldin"],
}

STANDALONE_DIAGNOSTIC_METHODS = {"agglomerative", "spectral"}

# HIGH #13 (audit 15/08/26): silhouette/calinski_harabasz/davies_bouldin always score X
# under sklearn's own default (Euclidean) - correct only as long as the clustering method
# itself also treated X as a plain Euclidean feature space. Registered here (lesson #20,
# explicit allow-list over a free-form guess) are every value known to still mean "X is a
# plain feature matrix, Euclidean validation applies": None (key absent - most methods,
# e.g. kmeans/gmm/hdbscan, don't have this concept at all), "nearest_neighbors"/"rbf" for
# spectral's `affinity` (both build their graph from X via Euclidean distance internally,
# same geometry the validation metrics assume), and "euclidean" for agglomerative's
# `metric`. Anything else - most importantly `affinity="precomputed"` (X is itself a
# distance/affinity matrix built under an arbitrary metric, e.g. Jaccard/Dice) or a
# non-euclidean `metric` - makes X's own coordinates meaningless to a Euclidean index,
# so compute_clustering_metrics refuses outright rather than silently scoring the wrong
# geometry (dormant today: no production/tuning config sets either of these, see
# AUDIT_FINDINGS.md #13).
_EUCLIDEAN_SAFE_AFFINITY = frozenset({None, "nearest_neighbors", "rbf"})
_EUCLIDEAN_SAFE_METRIC = frozenset({None, "euclidean"})


def _require_euclidean_compatible(combo_params: dict | None) -> None:
    if combo_params is None:
        return
    affinity = combo_params.get("affinity")
    if affinity not in _EUCLIDEAN_SAFE_AFFINITY:
        raise ValueError(
            f"compute_clustering_metrics assumes Euclidean geometry (sklearn's default for "
            f"silhouette/calinski_harabasz/davies_bouldin), but affinity={affinity!r} means X is not a "
            "plain Euclidean feature matrix - pass an explicit metric-aware score instead of calling this "
            "function, or register affinity in _EUCLIDEAN_SAFE_AFFINITY if it's actually Euclidean-based"
        )
    metric = combo_params.get("metric")
    if metric not in _EUCLIDEAN_SAFE_METRIC:
        raise ValueError(
            f"compute_clustering_metrics assumes Euclidean geometry (sklearn's default for "
            f"silhouette/calinski_harabasz/davies_bouldin), but metric={metric!r} means clustering itself "
            "did not use Euclidean distance - pass an explicit metric-aware score instead of calling this "
            "function, or register metric in _EUCLIDEAN_SAFE_METRIC if it's actually Euclidean-equivalent"
        )


def compute_clustering_metrics(X: np.ndarray, labels: np.ndarray, combo_params: dict | None = None) -> dict[str, float]:
    """Generic internal-validation metrics for one (X, labels) clustering result.

    HDBSCAN-style noise (label -1) is excluded from silhouette/Calinski-Harabasz
    /Davies-Bouldin (undefined for a "cluster" that isn't one), but
    noise_fraction is always reported so the exclusion is visible, not silent.
    A degenerate combination (fewer than 2 non-noise clusters, or every
    non-noise point its own cluster) can't have these 3 metrics computed at
    all - sklearn itself would raise; caught here and recorded as NaN with a
    warning rather than aborting the whole sweep, since a bad hyperparameter
    combination is expected information in a tuning sweep, not a bug.

    combo_params (optional): the exact params dict the clustering method being scored was
    given - when passed, raises ValueError upfront if it names a distance/affinity this
    function's Euclidean assumption doesn't hold for (see _require_euclidean_compatible).
    None (the default) skips the check - only run_clustering_tuning_sweep, which always
    knows combo_params, is expected to pass it; a caller that already knows X is a plain
    Euclidean feature matrix (e.g. a unit test) doesn't need to.
    """
    _require_euclidean_compatible(combo_params)
    labels = np.asarray(labels)
    noise_mask = labels == -1
    noise_fraction = float(noise_mask.sum()) / len(labels)

    non_noise_X = X[~noise_mask]
    non_noise_labels = labels[~noise_mask]
    n_unique = len(np.unique(non_noise_labels))

    if n_unique < 2 or n_unique > len(non_noise_labels) - 1:
        logging.warning(
            "cannot compute silhouette/calinski_harabasz/davies_bouldin: %d non-noise cluster(s) found "
            "(need 2..n-1) - degenerate combination, recording NaN",
            n_unique,
        )
        return {
            "silhouette": float("nan"),
            "calinski_harabasz": float("nan"),
            "davies_bouldin": float("nan"),
            "noise_fraction": noise_fraction,
        }

    return {
        "silhouette": float(silhouette_score(non_noise_X, non_noise_labels)),
        "calinski_harabasz": float(calinski_harabasz_score(non_noise_X, non_noise_labels)),
        "davies_bouldin": float(davies_bouldin_score(non_noise_X, non_noise_labels)),
        "noise_fraction": noise_fraction,
    }


def compute_silhouette_samples(X: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-sample silhouette coefficients for one (X, labels) clustering result -
    the production-time, per-cluster-breakdown counterpart of
    compute_clustering_metrics's single aggregate "silhouette" number (their
    mean is exactly that number, since silhouette_score is defined as the mean
    of silhouette_samples). Feeds plotting.plot_silhouette_analysis.

    HDBSCAN-style noise (label -1) is excluded, same convention as
    compute_clustering_metrics - silhouette is undefined for a "cluster" that
    isn't one. Returns (non_noise_labels, sample_silhouette_values), same
    length and order (noise rows dropped from both). Raises ValueError if
    fewer than 2 non-noise clusters remain (degenerate combination, nothing
    meaningful to plot) - unlike compute_clustering_metrics's NaN-and-warn
    (built for an unattended sweep over many combinations), this runs once
    for the single already-chosen production result, so the caller decides
    whether to skip the plot.
    """
    labels = np.asarray(labels)
    noise_mask = labels == -1
    non_noise_X = X[~noise_mask]
    non_noise_labels = labels[~noise_mask]
    n_unique = len(np.unique(non_noise_labels))

    if n_unique < 2 or n_unique > len(non_noise_labels) - 1:
        raise ValueError(
            f"cannot compute per-sample silhouette: {n_unique} non-noise cluster(s) found (need 2..n-1)"
        )

    return non_noise_labels, silhouette_samples(non_noise_X, non_noise_labels)


def _kmeans_with_extra_metrics(X: np.ndarray, params: dict) -> tuple[np.ndarray, dict[str, float]]:
    fitted = KMeans(**params).fit(X)
    return fitted.labels_, {"inertia": float(fitted.inertia_)}


def _gmm_with_extra_metrics(X: np.ndarray, params: dict) -> tuple[np.ndarray, dict[str, float]]:
    fitted = GaussianMixture(**params).fit(X)
    labels = fitted.predict(X)
    return labels, {"bic": float(fitted.bic(X)), "aic": float(fitted.aic(X))}


_EXTRA_METRICS_EVALUATORS: dict[str, Callable[[np.ndarray, dict], tuple[np.ndarray, dict[str, float]]]] = {
    "kmeans": _kmeans_with_extra_metrics,
    "gmm": _gmm_with_extra_metrics,
}


def run_clustering_tuning_sweep(
    method: str, X: np.ndarray, base_params: dict, tuning_grid: dict[str, list], consensus_config: dict | None = None
) -> pd.DataFrame:
    """Evaluate every combination in the Cartesian product of tuning_grid.

    Each combination overrides base_params for the swept keys only (unswept
    keys, e.g. random_state, stay fixed at base_params' value). Returns one
    row per combination: the swept parameter values, the 3 generic metrics +
    noise_fraction (compute_clustering_metrics), plus any method-specific
    extra column (see METHOD_METRIC_COLUMNS/_EXTRA_METRICS_EVALUATORS).

    consensus_config, when given, is {"rsc": {"n_repeats": int}, "monti":
    {"n_repeats": int, "subsample_fraction": float}} (either/both keys) -
    adds "rsc_eigengap"/"monti_stability" columns per row (see
    src/analysis/consensus_clustering.py). None (the default) leaves output
    unchanged from before consensus/stability clustering existed. Raises
    ValueError immediately if given for a method outside
    CONSENSUS_ELIGIBLE_METHODS (agglomerative/hdbscan are deterministic given
    the same data - a stability sweep for them would be degenerate/silent
    garbage, not just unsupported).
    """
    if method not in CLUSTERING_METHODS:
        raise ValueError(f"unknown clustering method {method!r} - known: {sorted(CLUSTERING_METHODS)}")
    if consensus_config is not None and method not in CONSENSUS_ELIGIBLE_METHODS:
        raise ValueError(
            f"consensus_config given for method {method!r}, but consensus/stability clustering is only defined for "
            f"{sorted(CONSENSUS_ELIGIBLE_METHODS)}"
        )

    keys = list(tuning_grid.keys())
    combinations = list(itertools.product(*tuning_grid.values()))
    total = len(combinations)
    logging.info("Starting clustering fine-tuning sweep for %s (%d combinations)", method, total)

    rows = []
    for i, combo in enumerate(combinations, 1):
        combo_params = {**base_params, **dict(zip(keys, combo))}
        logging.info("Evaluating combination %d/%d: %s", i, total, dict(zip(keys, combo)))
        if method in _EXTRA_METRICS_EVALUATORS:
            labels, extra_metrics = _EXTRA_METRICS_EVALUATORS[method](X, combo_params)
        else:
            labels = CLUSTERING_METHODS[method](X, combo_params)
            extra_metrics = {}
        generic_metrics = compute_clustering_metrics(X, labels, combo_params)
        consensus_metrics = _compute_consensus_metrics(method, X, combo_params, consensus_config)
        rows.append({**dict(zip(keys, combo)), **generic_metrics, **extra_metrics, **consensus_metrics})

    return pd.DataFrame(rows)


def _compute_consensus_metrics(method: str, X: np.ndarray, combo_params: dict, consensus_config: dict | None) -> dict[str, float]:
    """rsc_eigengap/monti_stability for one already-built combo_params dict -
    the k value they're scored against is read straight off combo_params
    (K_PARAM_NAME[method]), since it's exactly the parameter tuning_grid
    swept to produce this combo.
    """
    if consensus_config is None:
        return {}

    k = combo_params[K_PARAM_NAME[method]]
    metrics: dict[str, float] = {}
    if "rsc" in consensus_config:
        cooccurrence = run_rsc_repeats(method, X, combo_params, consensus_config["rsc"]["n_repeats"])
        metrics["rsc_eigengap"] = compute_rsc_eigengap(cooccurrence, k)
    if "monti" in consensus_config:
        consensus_matrix = run_monti_repeats(
            method, X, combo_params, consensus_config["monti"]["n_repeats"], consensus_config["monti"]["subsample_fraction"]
        )
        metrics["monti_stability"] = compute_monti_stability(consensus_matrix)
    return metrics


def consensus_suggestion_lines(results: pd.DataFrame, method: str) -> list[str]:
    """Readme lines stating each consensus method's own literature-defined
    "suggested k" (RSC: argmax rsc_eigengap; Monti: argmax monti_stability,
    i.e. argmin PAC) - purely informational, never read back by any code.
    Empty list when neither column is present (consensus wasn't requested).
    """
    k_param = K_PARAM_NAME.get(method)
    lines = []
    if "rsc_eigengap" in results.columns:
        best_row = results.loc[results["rsc_eigengap"].idxmax()]
        lines.append(f"RSC suggests {k_param}={int(best_row[k_param])} (largest eigengap on the co-occurrence matrix)")
    if "monti_stability" in results.columns:
        best_row = results.loc[results["monti_stability"].idxmax()]
        lines.append(f"Monti suggests {k_param}={int(best_row[k_param])} (highest 1-PAC stability score)")
    return lines


def compute_dendrogram_linkage(X: np.ndarray, params: dict) -> np.ndarray:
    """Fits AgglomerativeClustering with the full merge tree exposed
    (n_clusters=None, distance_threshold=0 forces every merge down to
    singleton leaves; compute_distances=True records each merge's distance),
    then converts sklearn's children_/distances_ into a scipy linkage matrix
    - the format plotting.plot_dendrogram (scipy.cluster.hierarchy.dendrogram)
    expects. Ignores any n_clusters/distance_threshold already in `params` -
    the full hierarchy doesn't depend on which cut you'd eventually pick,
    that's the whole point of looking at it before deciding on one.
    """
    tree_params = {k: v for k, v in params.items() if k not in ("n_clusters", "distance_threshold")}
    fitted = AgglomerativeClustering(n_clusters=None, distance_threshold=0, compute_distances=True, **tree_params).fit(X)

    n_samples = len(fitted.labels_)
    counts = np.zeros(fitted.children_.shape[0])
    for i, merge in enumerate(fitted.children_):
        count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                count += 1
            else:
                count += counts[child_idx - n_samples]
        counts[i] = count

    return np.column_stack([fitted.children_, fitted.distances_, counts]).astype(float)


def compute_eigengap(X: np.ndarray, params: dict, max_k: int = 20) -> np.ndarray:
    """Builds the same affinity graph SpectralClustering would from `params`
    ("nearest_neighbors" or "rbf", matching src/analysis/clustering.py's
    spectral_cluster), computes the normalized graph Laplacian, and returns
    its smallest `max_k` eigenvalues sorted ascending - plotting.plot_eigengap
    reads the eigengap heuristic's suggested cluster count off the biggest
    gap between consecutive values here. Independent of `params["n_clusters"]`
    - the affinity graph itself doesn't depend on how many clusters you'd cut
    it into.

    Raises ValueError for any affinity other than "nearest_neighbors"/"rbf" -
    those are the only two spectral_cluster actually supports today.
    """
    affinity = params.get("affinity", "rbf")
    if affinity == "nearest_neighbors":
        n_neighbors = params.get("n_neighbors", 10)
        connectivity = kneighbors_graph(X, n_neighbors=n_neighbors, mode="connectivity", include_self=False)
        affinity_matrix = 0.5 * (connectivity + connectivity.T)
    elif affinity == "rbf":
        gamma = params.get("gamma", 1.0)
        affinity_matrix = rbf_kernel(X, gamma=gamma)
    else:
        raise ValueError(f"eigengap computation only supports affinity 'nearest_neighbors'/'rbf', got {affinity!r}")

    laplacian = csgraph.laplacian(affinity_matrix, normed=True)
    if hasattr(laplacian, "toarray"):
        laplacian = laplacian.toarray()
    k = min(max_k, laplacian.shape[0] - 1)
    eigenvalues = eigh(laplacian, eigvals_only=True, subset_by_index=[0, k])
    return np.sort(eigenvalues)
