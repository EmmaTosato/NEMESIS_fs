"""Manual fine-tuning sweep for clustering methods (kmeans, agglomerative, gmm,
hdbscan, spectral, evidence_accumulation) - mirrors src/analysis/tuning.py's
dim-reduction sweep, but clustering has no ground truth to score against:
every generic metric here is an *internal* validation index computed straight
from (X, cluster_labels), meaningful only within one method's own swept grid,
never compared across methods. No automatic selection, same philosophy as
tuning.py.

Two kinds of extras beyond the 3 generic metrics, see METHOD_METRIC_COLUMNS -
per-combination scalar columns for methods that expose one after fitting
(kmeans' inertia_, gmm's bic_/aic_), and standalone single-fit diagnostics
independent of which n_clusters ends up chosen (agglomerative's dendrogram +
interclass distance matrix, spectral's eigengap, evidence_accumulation's
n_repeats convergence check + consensus matrix heatmap) - see
docs/dev/models.md for the full rationale, including why HDBSCAN gets neither
a standalone diagnostic nor a plotted inertia/bic-style column.
"""

from __future__ import annotations

import itertools
import logging
from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy.linalg import eigh
from scipy.sparse import csgraph
from sklearn.cluster import HDBSCAN, AgglomerativeClustering, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, pairwise_distances, silhouette_samples, silhouette_score
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
from src.analysis.distances import PRECOMPUTABLE_METRICS, SUPPORTED_BINARY_METRICS, precomputed_distance

CONSENSUS_METRIC_COLUMNS = ("rsc_eigengap", "monti_stability")

# Stability analysis (project-clustering-tuning-redesign memory, 26-08-26): kmeans/gmm are
# the only 2 CLUSTERING_METHODS whose result depends on a random init the tuning sweep never
# validates on its own - k/n_components is the real target hyperparameter, init/n_init is a
# nuisance parameter that needs checking *before* trusting the plain sweep, never a joint
# k x init grid (that heatmap was explicitly rejected - see the memory). One shared, generic
# stability sweep (below) serves both methods: only the estimator/param names/scored metric
# differ, the (target x nuisance x n_init x repeat) loop shape is identical.
STABILITY_TARGET_PARAM = {"kmeans": "n_clusters", "gmm": "n_components"}
STABILITY_NUISANCE_PARAM = {"kmeans": "init", "gmm": "init_params"}
STABILITY_METRIC_NAME = {"kmeans": "inertia", "gmm": "bic"}
STABILITY_ELIGIBLE_METHODS = set(STABILITY_TARGET_PARAM)

_STABILITY_ESTIMATORS: dict[str, Callable] = {"kmeans": KMeans, "gmm": GaussianMixture}

METHOD_METRIC_COLUMNS: dict[str, list[str]] = {
    "kmeans": ["silhouette", "calinski_harabasz", "davies_bouldin", "inertia"],
    "agglomerative": ["silhouette", "calinski_harabasz", "davies_bouldin"],
    "gmm": ["silhouette", "calinski_harabasz", "davies_bouldin", "bic", "aic"],
    "hdbscan": ["silhouette", "calinski_harabasz", "davies_bouldin", "noise_fraction", "n_clusters_found"],
    "spectral": ["silhouette", "calinski_harabasz", "davies_bouldin"],
    "evidence_accumulation": ["silhouette", "calinski_harabasz", "davies_bouldin"],
}

STANDALONE_DIAGNOSTIC_METHODS = {"agglomerative", "spectral", "evidence_accumulation"}

# HIGH #13 (audit 15/08/26): the 3 geometric metrics below always score X under
# sklearn's own default (Euclidean) - only valid if the clustering method itself also
# treated X as Euclidean. Explicit allow-list (lesson #20) of every affinity/metric
# value that still means that; anything else (most importantly affinity="precomputed")
# makes compute_clustering_metrics refuse rather than silently score the wrong
# geometry - see docs/dev/models.md for the full rationale (dormant today, AUDIT_FINDINGS.md #13).
_EUCLIDEAN_SAFE_AFFINITY = frozenset({None, "nearest_neighbors", "rbf"})
_EUCLIDEAN_SAFE_METRIC = frozenset({None, "euclidean"})

# agglomerative-only metric-aware sweep (project-clustering-tuning-redesign memory, 26-08-26):
# unlike every other method, agglomerative is deterministic (no random_state) and sklearn
# itself restricts linkage="ward" to euclidean/l2 geometry - see
# is_invalid_ward_metric_combo/_agglomerative_fit_metric_aware/compute_clustering_metrics_metric_aware
# below, and run_clustering_tuning_sweep's dedicated branch.
_WARD_SAFE_METRICS = frozenset({"euclidean", "l2"})


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
    non-noise point its own cluster) is recorded as NaN with a logged warning
    rather than aborting the whole sweep - a bad hyperparameter combination is
    expected information in a tuning sweep, not a bug.

    combo_params (optional, see _require_euclidean_compatible/docs/dev/models.md):
    when given, raises ValueError upfront if it names a distance/affinity this
    function's Euclidean assumption doesn't hold for. None (default) skips the
    check - only run_clustering_tuning_sweep always knows combo_params to pass.
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
    mean is exactly that number). Feeds plotting.plot_silhouette_analysis.

    HDBSCAN-style noise (label -1) is excluded, same convention as
    compute_clustering_metrics. Returns (non_noise_labels,
    sample_silhouette_values), same length/order (noise dropped from both).
    Raises ValueError if fewer than 2 non-noise clusters remain - unlike
    compute_clustering_metrics's NaN-and-warn (built for an unattended
    sweep), this runs once for the already-chosen production result, so the
    caller decides whether to skip the plot.
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


def dunn_index(X: np.ndarray, labels: np.ndarray) -> float:
    """Dunn Index (Dunn 1974): ratio of the smallest inter-cluster distance to the largest
    intra-cluster diameter - unlike Davies-Bouldin (min is better), a *higher* Dunn Index
    means clusters are compact and well separated. Never implemented in this repo before
    (project-clustering-tuning-evaluation-tables memory, 25-08-26) - no sklearn/scipy
    built-in exists, so this is a from-scratch implementation on top of sklearn's own
    pairwise_distances (Euclidean by default, same assumption as compute_clustering_metrics -
    not metric-aware like compute_clustering_metrics_metric_aware, since the exploratory
    evaluation notebook that consumes this only ever runs it on plain-Euclidean data).

    HDBSCAN-style noise (label -1) is excluded, same convention as compute_clustering_metrics.
    Raises ValueError for fewer than 2 non-noise clusters (undefined), or if every non-noise
    cluster is a singleton (every intra-cluster diameter is 0.0, which would make the ratio a
    division by zero rather than a meaningful score).
    """
    labels = np.asarray(labels)
    noise_mask = labels == -1
    non_noise_X = X[~noise_mask]
    non_noise_labels = labels[~noise_mask]
    unique = np.unique(non_noise_labels)
    if len(unique) < 2:
        raise ValueError(f"dunn_index needs >= 2 non-noise clusters, found {len(unique)}")

    distances = pairwise_distances(non_noise_X)

    diameters = [
        distances[np.ix_(idx, idx)].max() if len(idx) >= 2 else 0.0
        for idx in (np.where(non_noise_labels == cluster)[0] for cluster in unique)
    ]
    max_diameter = max(diameters)
    if max_diameter == 0.0:
        raise ValueError("dunn_index undefined: every non-noise cluster is a singleton (intra-cluster diameter 0)")

    min_inter_cluster = np.inf
    for i, cluster_a in enumerate(unique):
        idx_a = np.where(non_noise_labels == cluster_a)[0]
        for cluster_b in unique[i + 1 :]:
            idx_b = np.where(non_noise_labels == cluster_b)[0]
            min_inter_cluster = min(min_inter_cluster, distances[np.ix_(idx_a, idx_b)].min())

    return float(min_inter_cluster / max_diameter)


def is_invalid_ward_metric_combo(combo_params: dict) -> bool:
    """True iff this agglomerative combination pairs linkage="ward" (sklearn's default) with a
    metric other than euclidean/l2 - an invalid sklearn combination
    (AgglomerativeClustering's own `metric` docstring: "If linkage is 'ward', only 'euclidean'
    and 'l2' are accepted"). Checked upfront in run_clustering_tuning_sweep so such a
    combination is skipped with a logged warning, never let through to raise sklearn's own
    ValueError mid-sweep.
    """
    linkage = combo_params.get("linkage", "ward")
    metric = combo_params.get("metric", "euclidean")
    return linkage == "ward" and metric not in _WARD_SAFE_METRICS


def _agglomerative_fit_metric_aware(
    X: np.ndarray, params: dict, distance_cache: dict[str, np.ndarray] | None = None
) -> tuple[np.ndarray, str]:
    """Fits AgglomerativeClustering honoring an arbitrary `metric` (default "euclidean",
    sklearn's own default). Any metric in distances.py::PRECOMPUTABLE_METRICS (jaccard/dice/
    euclidean) is precomputed first via distances.py::precomputed_distance and fit with
    metric="precomputed" (same reuse as the umap/t-SNE fine-tuning path, lesson #29 - no new
    precompute machinery needed) - unless `linkage` is "ward", which sklearn only accepts with
    the literal metric="euclidean"/"l2", never "precomputed" (checked directly here, since
    is_invalid_ward_metric_combo upstream only filters ward+*non-euclidean*, leaving
    ward+euclidean - a valid, common combination - to reach this function). Every other native
    sklearn metric string (cosine/manhattan/...) goes straight into the estimator on raw X, same
    as before. Returns (labels, metric) so the caller can score every generic metric with the
    exact same metric/distance that was actually clustered on.

    **03-09-26, widened from jaccard/dice-only to include euclidean**: found while running this
    sweep directly on a raw, high-dimensional matrix (`25-08_s1.2-vol`, 5269 subjects x 264274
    voxels) - `AgglomerativeClustering(metric="euclidean")` fit directly on raw X does *not* use
    the same BLAS-optimized route `distances.py::euclidean_pairwise_distance`/`sklearn.metrics.
    pairwise.euclidean_distances` does; measured directly on a 1000-subject subsample of this
    same matrix: 8.3s to precompute the full distance matrix vs. 48.7s for a direct fit on raw X
    (~6x), vs. 0.0s to then fit on the already-precomputed matrix. Invisible on a 2-3 column
    embedding (both paths are near-instant there); the dominant cost of the whole sweep on a raw
    voxel matrix, same root shape as lesson #29's original UMAP/t-SNE finding, just found later
    for agglomerative specifically.

    distance_cache (optional, keyed by metric name): a given metric's precomputed distance
    matrix depends only on (X, metric), never on the swept n_clusters/linkage - recomputing it
    per combination (rather than once per metric) was the original, narrower 03-09-26 fix this
    docstring describes above. When given, computed once per metric and reused for every later
    combination sharing it (still excluding `ward`, per the check above - `ward` combinations
    are never cached, always fit directly on raw X).
    """
    params = dict(params)
    metric = params.pop("metric", "euclidean")
    linkage = params.get("linkage", "ward")
    if metric in PRECOMPUTABLE_METRICS and linkage != "ward":
        if distance_cache is not None and metric in distance_cache:
            distance_matrix = distance_cache[metric]
        else:
            distance_matrix = precomputed_distance(X, metric)
            if distance_cache is not None:
                distance_cache[metric] = distance_matrix
        labels = AgglomerativeClustering(**params, metric="precomputed").fit_predict(distance_matrix)
    else:
        labels = AgglomerativeClustering(**params, metric=metric).fit_predict(X)
    return labels, metric


def compute_clustering_metrics_metric_aware(
    X: np.ndarray, labels: np.ndarray, metric: str, distance_cache: dict[str, np.ndarray] | None = None
) -> dict[str, float]:
    """Agglomerative-only counterpart of compute_clustering_metrics, for a `metric` that may not
    be euclidean (project-clustering-tuning-redesign memory, 26-08-26 - the redesign this
    replaces compute_clustering_metrics's blanket `_require_euclidean_compatible` abort with,
    for agglomerative specifically): Silhouette is always computable for any metric
    (sklearn's silhouette_score accepts a metric string or "precomputed" - lesson #15, thread
    the same metric used for clustering into scoring), so it's always kept. Calinski-Harabasz/
    Davies-Bouldin are mathematically euclidean-only (centroid-based, no `metric` parameter
    exists for them at all) - skipped (NaN) for any non-euclidean metric, not aborted.

    Agglomerative never produces the HDBSCAN-style noise label -1 (no stochastic/density
    rejection step) - noise_fraction is always 0.0, kept in the returned dict only for the same
    column shape as compute_clustering_metrics. A degenerate combination (fewer than 2, or more
    than n-1, clusters - possible if n_clusters approaches n_samples) is recorded as NaN with a
    logged warning, same convention as compute_clustering_metrics.

    distance_cache (03-09-26, optional, keyed by metric name): without it, silhouette's own
    distance matrix was computed *again* here for any metric in PRECOMPUTABLE_METRICS - entirely
    independent of, and not reusing, whatever `_agglomerative_fit_metric_aware` already computed
    (and possibly already cached) for the fit itself. For `euclidean` specifically this was the
    same non-BLAS-optimized `sklearn.metrics.silhouette_score(X, labels, metric="euclidean")`
    internal computation `_agglomerative_fit_metric_aware`'s own docstring found slow - found
    here as a second, separate instance of the same gap, still present after that fix, because
    scoring was never routed through the same cache the fit was (a real sweep on
    `25-08_s1.2-vol` still stalled per-combination after the fit-side fix alone, which is what
    surfaced this). When `distance_cache` is given (the caller passes the same
    `agglomerative_distance_cache` `run_clustering_tuning_sweep` already threads into the fit),
    the exact same precomputed matrix is reused for scoring too - one computation per metric,
    shared between fit and score, not two.
    """
    labels = np.asarray(labels)
    n_unique = len(np.unique(labels))
    if n_unique < 2 or n_unique > len(labels) - 1:
        logging.warning(
            "cannot compute silhouette/calinski_harabasz/davies_bouldin: %d cluster(s) found (need 2..n-1) "
            "- degenerate combination, recording NaN",
            n_unique,
        )
        return {"silhouette": float("nan"), "calinski_harabasz": float("nan"), "davies_bouldin": float("nan"), "noise_fraction": 0.0}

    if metric in PRECOMPUTABLE_METRICS:
        if distance_cache is not None and metric in distance_cache:
            distance_matrix = distance_cache[metric]
        else:
            distance_matrix = precomputed_distance(X, metric)
            if distance_cache is not None:
                distance_cache[metric] = distance_matrix
        silhouette = float(silhouette_score(distance_matrix, labels, metric="precomputed"))
    else:
        silhouette = float(silhouette_score(X, labels, metric=metric))

    metrics = {"silhouette": silhouette, "noise_fraction": 0.0}
    if metric == "euclidean":
        metrics["calinski_harabasz"] = float(calinski_harabasz_score(X, labels))
        metrics["davies_bouldin"] = float(davies_bouldin_score(X, labels))
    else:
        metrics["calinski_harabasz"] = float("nan")
        metrics["davies_bouldin"] = float("nan")
    return metrics


def compute_interclass_distance_matrix(X: np.ndarray, proxy_labels: np.ndarray, metric: str) -> tuple[list, np.ndarray]:
    """Average pairwise distance within/between proxy groups for one candidate `metric` -
    independent of any clustering fit (project-clustering-tuning-redesign memory: a
    metric-selection pre-check, modeled on sklearn's plot_agglomerative_clustering_metrics.html
    "interclass distance matrix" panel; doubles as the substitute diagnostic for combinations
    where compute_clustering_metrics_metric_aware skipped Calinski-Harabasz/Davies-Bouldin,
    non-euclidean metrics).

    `proxy_labels` is a weak ground-truth grouping (e.g. dataset/site, lesion side, vascular
    territory - see docs/dev/models.md) - not a clustering result. Returns (sorted unique
    groups, matrix) where matrix[a, b] is the mean pairwise distance between group a and group
    b (diagonal = within-group spread, off-diagonal = between-group separation). A group with
    fewer than 2 members has an undefined within-group spread - recorded as NaN, not 0.0 (which
    would misrepresent "no data" as "identical").
    """
    proxy_labels = np.asarray(proxy_labels)
    groups = sorted(pd.unique(proxy_labels).tolist())
    distance_matrix = precomputed_distance(X, metric) if metric in SUPPORTED_BINARY_METRICS else pairwise_distances(X, metric=metric)

    matrix = np.zeros((len(groups), len(groups)))
    for a, group_a in enumerate(groups):
        idx_a = np.where(proxy_labels == group_a)[0]
        for b, group_b in enumerate(groups):
            idx_b = np.where(proxy_labels == group_b)[0]
            sub = distance_matrix[np.ix_(idx_a, idx_b)]
            if group_a == group_b:
                if len(idx_a) < 2:
                    matrix[a, b] = float("nan")
                else:
                    matrix[a, b] = sub[np.triu_indices(len(idx_a), k=1)].mean()
            else:
                matrix[a, b] = sub.mean()
    return groups, matrix


def hdbscan_labels_and_probabilities(X: np.ndarray, params: dict) -> tuple[np.ndarray, np.ndarray]:
    """Fits HDBSCAN and returns (labels_, probabilities_) - unlike CLUSTERING_METHODS["hdbscan"]
    (hdbscan_cluster, labels only, the uniform contract every generic caller relies on),
    `probabilities_` (per-point membership confidence in [0, 1], always 0 for noise) is only
    reachable from the fitted estimator itself. Used by clustering.py's production path
    (project-clustering-tuning-redesign memory, 26-08-26) to size cluster_plot.png's markers by
    confidence (plotting.plot_clusters_2d's `point_sizes`) - sklearn's own official HDBSCAN
    example's diagnostic (plot_hdbscan.html), not DBCV/condensation tree (see docs/dev/models.md
    for why those were dropped).
    """
    fitted = HDBSCAN(**params).fit(X)
    return fitted.labels_, fitted.probabilities_


def _kmeans_with_extra_metrics(X: np.ndarray, params: dict) -> tuple[np.ndarray, dict[str, float]]:
    fitted = KMeans(**params).fit(X)
    return fitted.labels_, {"inertia": float(fitted.inertia_)}


def _gmm_with_extra_metrics(X: np.ndarray, params: dict) -> tuple[np.ndarray, dict[str, float]]:
    fitted = GaussianMixture(**params).fit(X)
    labels = fitted.predict(X)
    return labels, {"bic": float(fitted.bic(X)), "aic": float(fitted.aic(X))}


def _hdbscan_with_extra_metrics(X: np.ndarray, params: dict) -> tuple[np.ndarray, dict[str, float]]:
    """Unlike kmeans'/gmm's own n_clusters/n_components (already a swept parameter, known
    without inspecting the fit), HDBSCAN's number of clusters is an *output* of
    min_cluster_size/min_samples, never surfaced anywhere in a tuning sweep before this - a
    combination could silently produce a degenerate/over-fragmented result (e.g. min_cluster_size
    too low relative to the cohort size) invisible in tuning_results.csv until it was already
    running in production (see docs/experiments/clustering/s1_production.md, s1.2-vol: 143
    clusters found only at production time for a combination silhouette/noise_fraction alone
    looked reasonable for). label -1 (noise) is excluded, same convention as noise_fraction.
    """
    labels = CLUSTERING_METHODS["hdbscan"](X, params)
    n_clusters_found = float(len(np.unique(labels[labels != -1])))
    return labels, {"n_clusters_found": n_clusters_found}


_EXTRA_METRICS_EVALUATORS: dict[str, Callable[[np.ndarray, dict], tuple[np.ndarray, dict[str, float]]]] = {
    "kmeans": _kmeans_with_extra_metrics,
    "gmm": _gmm_with_extra_metrics,
    "hdbscan": _hdbscan_with_extra_metrics,
}


def run_clustering_tuning_sweep(
    method: str, X: np.ndarray, base_params: dict, tuning_grid: dict[str, list], consensus_config: dict | None = None
) -> tuple[pd.DataFrame, dict[tuple, np.ndarray]]:
    """Evaluate every combination in the Cartesian product of tuning_grid.

    Each combination overrides base_params for the swept keys only. Returns
    (results, labels_by_combo) - same shape as tuning.py::run_tuning_sweep's
    (results, embeddings_by_combo): results is one row per combination (swept
    values, the 3 generic metrics + noise_fraction, plus any method-specific
    extra column - see METHOD_METRIC_COLUMNS/_EXTRA_METRICS_EVALUATORS), the
    only thing written to tuning_results.csv; labels_by_combo keys each
    combination's actual cluster-label array by its exact `combo` tuple,
    in-memory only - already computed to score the metrics above, so
    returning it too is free (never a second fit) - lets a caller that needs
    to *persist* a combination's labels (clustering.py's save_tuning_clusterings)
    avoid recomputing it.

    consensus_config, when given, is {"rsc": {"n_repeats": int}, "monti":
    {"n_repeats": int, "subsample_fraction": float}} (either/both keys) -
    adds "rsc_eigengap"/"monti_stability" columns (see consensus_clustering.py,
    docs/dev/models.md). None (default) leaves output unchanged. Raises
    ValueError if given for a method outside CONSENSUS_ELIGIBLE_METHODS -
    agglomerative/hdbscan are deterministic given the same data, so a
    stability sweep for them would be degenerate.
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

    # AUDIT_FINDINGS.md #35: evidence_accumulation's real cost (run_rsc_repeats, n_repeats
    # fits of base_method) depends only on base_method/n_repeats/base_seed/the Split-phase
    # K_PARAM_NAME[base_method] - never on threshold, which only drives the separate, cheap
    # Merge-phase cut (assign_clusters_from_cooccurrence). Combinations that agree on
    # everything except threshold share one already-computed co-occurrence matrix instead
    # of each recomputing run_rsc_repeats from scratch - a 7-value threshold-only sweep
    # goes from 7*n_repeats fits down to n_repeats.
    cooccurrence_cache: dict[tuple, np.ndarray] = {} if method == "evidence_accumulation" else None

    # See _agglomerative_fit_metric_aware's distance_cache docstring: the jaccard/dice distance
    # matrix depends only on (X, metric), not on n_clusters/linkage - shared across every combo
    # in this sweep that requests the same metric, instead of recomputed per combo.
    agglomerative_distance_cache: dict[str, np.ndarray] = {} if method == "agglomerative" else None

    rows = []
    labels_by_combo: dict[tuple, np.ndarray] = {}
    for i, combo in enumerate(combinations, 1):
        combo_dict = dict(zip(keys, combo))
        combo_params = {**base_params, **combo_dict}

        # Agglomerative-only (project-clustering-tuning-redesign memory, 26-08-26): linkage="ward"
        # + a non-euclidean metric is an invalid sklearn combination - filtered out of the sweep
        # here, with a logged warning, never let through to raise sklearn's own ValueError mid-sweep.
        if method == "agglomerative" and is_invalid_ward_metric_combo(combo_params):
            logging.warning(
                "[agglomerative] skipping invalid combination %s: linkage='ward' requires metric in %s",
                combo_dict,
                sorted(_WARD_SAFE_METRICS),
            )
            continue

        logging.info("Evaluating combination %d/%d: %s", i, total, combo_dict)
        if method == "evidence_accumulation":
            labels = _evidence_accumulation_labels(X, combo_params, cooccurrence_cache)
            extra_metrics = {}
            generic_metrics = compute_clustering_metrics(X, labels, combo_params)
        elif method == "agglomerative":
            labels, metric = _agglomerative_fit_metric_aware(X, combo_params, agglomerative_distance_cache)
            extra_metrics = {}
            generic_metrics = compute_clustering_metrics_metric_aware(X, labels, metric, agglomerative_distance_cache)
        elif method in _EXTRA_METRICS_EVALUATORS:
            labels, extra_metrics = _EXTRA_METRICS_EVALUATORS[method](X, combo_params)
            generic_metrics = compute_clustering_metrics(X, labels, combo_params)
        else:
            labels = CLUSTERING_METHODS[method](X, combo_params)
            extra_metrics = {}
            generic_metrics = compute_clustering_metrics(X, labels, combo_params)

        consensus_metrics = _compute_consensus_metrics(method, X, combo_params, consensus_config)
        rows.append({**combo_dict, **generic_metrics, **extra_metrics, **consensus_metrics})
        labels_by_combo[combo] = labels

    return pd.DataFrame(rows), labels_by_combo


SPECTRAL_AFFINITY_HYPERPARAM = {"nearest_neighbors": "n_neighbors", "rbf": "gamma"}


def run_spectral_affinity_aware_sweep(
    X: np.ndarray, base_params: dict, tuning_grid: dict[str, list], consensus_config: dict | None = None
) -> tuple[pd.DataFrame, dict[tuple, np.ndarray]]:
    """Affinity-aware sweep for spectral (project-clustering-tuning-redesign memory, 26-08-26):
    `"n_neighbors"` only applies to `affinity="nearest_neighbors"`, `"gamma"` only to
    `affinity="rbf"` - sklearn silently ignores whichever doesn't apply to the chosen affinity
    rather than raising, so a full Cartesian product over both would waste half the sweep
    re-fitting duplicate combinations. Runs `run_clustering_tuning_sweep` once per swept
    `"affinity"` value (`tuning_grid["affinity"]`), restricting each sub-sweep's grid to every
    swept key that isn't `SPECTRAL_AFFINITY_HYPERPARAM`'s `n_neighbors`/`gamma` pair, plus that
    affinity's own hyperparameter alone when it's present in `tuning_grid` - then concatenates
    the results with an explicit `"affinity"` column. Requires `"affinity"` to be a `tuning_grid`
    key; the plain `n_clusters`-only sweep (no `"affinity"` swept) is unaffected, still goes
    through `run_clustering_tuning_sweep` directly (see `clustering.py::_run_one_method_tuning`).
    """
    if "affinity" not in tuning_grid:
        raise ValueError("run_spectral_affinity_aware_sweep requires 'affinity' in tuning_grid")

    all_results = []
    labels_by_combo: dict[tuple, np.ndarray] = {}
    for affinity in tuning_grid["affinity"]:
        own_hyperparam = SPECTRAL_AFFINITY_HYPERPARAM.get(affinity)
        sub_grid = {
            key: values
            for key, values in tuning_grid.items()
            if key not in ("affinity", "n_neighbors", "gamma") or key == own_hyperparam
        }
        sub_base_params = {**base_params, "affinity": affinity}
        sub_results, sub_labels = run_clustering_tuning_sweep("spectral", X, sub_base_params, sub_grid, consensus_config)
        sub_results = sub_results.copy()
        sub_results["affinity"] = affinity
        all_results.append(sub_results)
        for combo, labels in sub_labels.items():
            labels_by_combo[(affinity, *combo)] = labels

    return pd.concat(all_results, ignore_index=True), labels_by_combo


def _evidence_accumulation_labels(X: np.ndarray, combo_params: dict, cooccurrence_cache: dict[tuple, np.ndarray]) -> np.ndarray:
    """evidence_accumulation_cluster(X, combo_params), but reusing run_rsc_repeats' result
    across combinations that share everything except threshold (see the cache-existence
    comment in run_clustering_tuning_sweep above) - cache_key is exactly the subset of
    combo_params that run_rsc_repeats actually reads (split_params, plus base_method/
    n_repeats/base_seed), so two combinations differing only in threshold always collide
    on the same key and only the first ever calls run_rsc_repeats.
    """
    from src.analysis.clustering import _validate_evidence_accumulation_params
    from src.analysis.consensus_clustering import assign_clusters_from_cooccurrence, run_rsc_repeats

    base_method, split_params, n_repeats, base_seed, threshold = _validate_evidence_accumulation_params(combo_params)
    cache_key = (base_method, n_repeats, base_seed, tuple(sorted(split_params.items())))
    if cache_key not in cooccurrence_cache:
        cooccurrence_cache[cache_key] = run_rsc_repeats(base_method, X, split_params, n_repeats, base_seed=base_seed)
    return assign_clusters_from_cooccurrence(cooccurrence_cache[cache_key], threshold)


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


def representative_values(values: list[int]) -> list[int]:
    """Min/median/max of a swept list of ints, deduplicated and sorted - the 3
    representative target values (n_clusters for kmeans, n_components for gmm)
    a stability analysis validates init/n_init against (project-clustering-
    tuning-redesign memory, 26-08-26): instability generally grows with the
    target value, so checking one point of tuning_grid doesn't generalize
    across its whole swept range. Raises ValueError on an empty list - there
    is no representative value of nothing.
    """
    if not values:
        raise ValueError("representative_values needs at least one value")
    sorted_values = sorted(values)
    return sorted({sorted_values[0], sorted_values[len(sorted_values) // 2], sorted_values[-1]})


def _stability_metric(method: str, fitted, X: np.ndarray) -> float:
    if method == "kmeans":
        return float(fitted.inertia_)
    return float(fitted.bic(X))  # gmm


def compute_stability_sweep(
    method: str, X: np.ndarray, target_values: list[int], nuisance_values: list[str], n_init_range: list[int], n_repeats: int
) -> pd.DataFrame:
    """Repeats a fit at each (target, nuisance, n_init) combination `n_repeats` times,
    varying only random_state, and records the method's own convergence metric
    (STABILITY_METRIC_NAME) - modeled on sklearn's plot_kmeans_stability_low_dim_dense.html,
    generalized to gmm's own knobs (init_params instead of init, bic instead of inertia - both
    converge to a local optimum the same way, see the project-clustering-tuning-redesign
    memory). One row per (target, nuisance, n_init, repeat), long-form - aggregated at plot
    time (plotting.plot_stability_analysis), not here.

    `target_values` is typically representative_values(tuning_grid[STABILITY_TARGET_PARAM[method]]),
    not the full swept range - the caller decides that, this function only runs the grid it's
    given. Raises ValueError for a method outside STABILITY_ELIGIBLE_METHODS - agglomerative/
    hdbscan/spectral have no comparable init/n_init nuisance parameter to validate this way
    (spectral's own k-means-inherited instability is instead removed at the source, by fixing
    assign_labels="cluster_qr" - see docs/dev/models.md).
    """
    if method not in STABILITY_ELIGIBLE_METHODS:
        raise ValueError(f"stability analysis is only defined for {sorted(STABILITY_ELIGIBLE_METHODS)}, got {method!r}")

    target_param = STABILITY_TARGET_PARAM[method]
    nuisance_param = STABILITY_NUISANCE_PARAM[method]
    metric_name = STABILITY_METRIC_NAME[method]
    estimator_cls = _STABILITY_ESTIMATORS[method]

    rows = []
    for target in target_values:
        for nuisance in nuisance_values:
            for n_init in n_init_range:
                for repeat in range(n_repeats):
                    params = {target_param: target, nuisance_param: nuisance, "n_init": n_init, "random_state": repeat}
                    fitted = estimator_cls(**params).fit(X)
                    rows.append(
                        {
                            target_param: target,
                            nuisance_param: nuisance,
                            "n_init": n_init,
                            "repeat": repeat,
                            metric_name: _stability_metric(method, fitted, X),
                        }
                    )
    return pd.DataFrame(rows)


def compute_dendrogram_linkage(
    X: np.ndarray, params: dict, distance_cache: dict[str, np.ndarray] | None = None
) -> np.ndarray:
    """Fits AgglomerativeClustering with the full merge tree exposed
    (n_clusters=None, distance_threshold=0 forces every merge down to
    singleton leaves; compute_distances=True records each merge's distance),
    then converts sklearn's children_/distances_ into a scipy linkage matrix
    - the format plotting.plot_dendrograms_grid (scipy.cluster.hierarchy.dendrogram)
    expects. Ignores any n_clusters/distance_threshold already in `params` -
    the full hierarchy doesn't depend on which cut you'd eventually pick,
    that's the whole point of looking at it before deciding on one.

    metric-aware the same way _agglomerative_fit_metric_aware is: any metric in
    distances.py::PRECOMPUTABLE_METRICS (jaccard/dice/euclidean) goes through
    distances.py::precomputed_distance and fits with metric="precomputed", instead of letting
    AgglomerativeClustering fall back to its own, much slower internal computation on raw X -
    scipy.spatial.distance.cdist's one-pair-at-a-time path for jaccard/dice (minutes to hours on
    a high-dimensional raw matrix), and a similarly slow non-BLAS-optimized path for euclidean
    (measured ~6x slower than precomputing, 03-09-26 - see _agglomerative_fit_metric_aware's own
    docstring for the numbers). Skipped when `linkage` is "ward" (sklearn only accepts
    metric="euclidean"/"l2" for ward, never "precomputed") - checked directly here for the same
    reason _agglomerative_fit_metric_aware does: is_invalid_ward_metric_combo upstream only
    filters ward+*non-euclidean*, leaving ward+euclidean (a valid combination) to reach this
    function. distance_cache (optional, keyed by metric name), same role as
    _agglomerative_fit_metric_aware's own cache: the caller (clustering.py's
    _write_agglomerative_diagnostics) calls this once per (metric, linkage) combination, so
    without it the same metric's distance matrix would be recomputed for every linkage sharing
    it.
    """
    tree_params = {k: v for k, v in params.items() if k not in ("n_clusters", "distance_threshold", "metric")}
    metric = params.get("metric", "euclidean")
    linkage = params.get("linkage", "ward")
    if metric in PRECOMPUTABLE_METRICS and linkage != "ward":
        if distance_cache is not None and metric in distance_cache:
            distance_matrix = distance_cache[metric]
        else:
            distance_matrix = precomputed_distance(X, metric)
            if distance_cache is not None:
                distance_cache[metric] = distance_matrix
        fitted = AgglomerativeClustering(
            n_clusters=None, distance_threshold=0, compute_distances=True, metric="precomputed", **tree_params
        ).fit(distance_matrix)
    else:
        fitted = AgglomerativeClustering(
            n_clusters=None, distance_threshold=0, compute_distances=True, metric=metric, **tree_params
        ).fit(X)

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
    ("nearest_neighbors" or "rbf", matching spectral_cluster), computes the
    normalized graph Laplacian, and returns its smallest `max_k` eigenvalues
    sorted ascending - plotting.plot_eigengaps_grid reads the eigengap heuristic's
    suggested cluster count off the biggest gap between consecutive values.
    Independent of `params["n_clusters"]`. Raises ValueError for any affinity
    other than "nearest_neighbors"/"rbf".
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
