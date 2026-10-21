"""Advanced Density Peaks (ADP, Rodriguez-Laio density peaks with the statistical test of
d'Errico et al. 2021) clustering, via DADApy, run directly on a feature matrix.

Unlike every other CLUSTERING_METHODS entry, ADP takes no number of clusters: k emerges from the
density landscape, and the single knob `Z` is the significance threshold a density peak must clear
to survive as its own cluster (higher Z -> fewer, more merged clusters). It is also the only method
here that clusters the *distances* of the raw matrix with dice/jaccard (euclidean is supported too),
not an embedding of it. See docs/dev/models.md for the rationale and docs/guides/clustering.md for
how to run it.

Pipeline, for one (X, metric, maxk):
  1. rows with a zero sum are dropped (dice/jaccard are undefined for them), and exact duplicate
     rows are clustered once (DADApy divides by the first-neighbour distance, which would be 0) -
     see _RowPlan; both groups get an explicit label below, never a silent default.
  2. exact N x N distances (src/analysis/distances.py::pairwise_distance), then the maxk nearest
     neighbours go to DADApy through `distances=`.
  3. intrinsic dimension (2NN) and density (PAk) are computed once - they do not depend on Z - so
     a sweep over Z only repeats the cheap clustering step.

Labels of the full matrix: cluster ids 0..k-1, NOISE_LABEL (-1, the same convention as HDBSCAN: ignored
by the scores, counted by noise_fraction) for the dropped zero-sum rows, and each duplicate row
carries the label of its twin.

`dadapy` is imported lazily (_import_dadapy): the library is installed in a separate environment
from the rest of the project (it pulls in jax), so importing this module - which clustering.py does
for the method registry - must work without it. Only a real ADP fit needs it.
"""

from __future__ import annotations

import hashlib
import itertools
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, silhouette_score

from src.analysis.distances import PRECOMPUTABLE_METRICS, pairwise_distance

ADP_METRICS = tuple(sorted(PRECOMPUTABLE_METRICS))
ADP_PARAM_KEYS = frozenset({"metric", "Z", "maxk"})
NOISE_LABEL = -1
SMALL_CLUSTER_SIZE = 10
_LOGGED_INDICES = 20


def _import_dadapy():
    try:
        from dadapy import Clustering
    except ImportError as exc:
        raise ImportError(
            "ADP clustering needs the 'dadapy' package, which is installed in a separate environment from "
            "the rest of the project (docs/guides/clustering.md, section ADP) - run this pipeline from that "
            f"environment. Original error: {exc}"
        ) from exc
    return Clustering


def validate_adp_params(params: dict) -> tuple[str, float, int]:
    """Returns (metric, Z, maxk) after checking `params` holds exactly those 3 keys, all valid.

    metric: one of ADP_METRICS. Z: positive number. maxk: integer >= 2, how many nearest neighbours
    DADApy gets per subject (density and 2NN are estimated within them). Unknown keys raise instead
    of being ignored - a typo'd hyperparameter must not silently run with the default of nothing.
    """
    missing = ADP_PARAM_KEYS - set(params)
    unknown = set(params) - ADP_PARAM_KEYS
    if missing or unknown:
        raise ValueError(f"adp params must be exactly {sorted(ADP_PARAM_KEYS)} - missing {sorted(missing)}, unknown {sorted(unknown)}")
    metric, z, maxk = params["metric"], params["Z"], params["maxk"]
    if metric not in ADP_METRICS:
        raise ValueError(f"adp 'metric' must be one of {list(ADP_METRICS)}, got {metric!r}")
    if isinstance(z, bool) or not isinstance(z, (int, float)) or not np.isfinite(z) or z <= 0:
        raise ValueError(f"adp 'Z' must be a positive number, got {z!r}")
    if isinstance(maxk, bool) or not isinstance(maxk, int) or maxk < 2:
        raise ValueError(f"adp 'maxk' must be an integer >= 2, got {maxk!r}")
    return metric, float(z), maxk


@dataclass(frozen=True)
class _RowPlan:
    """Which rows of X are clustered, and how the others get their label.

    keep: indices (into X) of the rows with a non-zero sum - the ones that have a distance at all.
    representatives: positions (into `keep`) of the first row of every distinct content.
    inverse: for each kept row, the index (into `representatives`) of the row carrying its content.
    """

    n_rows: int
    keep: np.ndarray
    representatives: np.ndarray
    inverse: np.ndarray

    def to_full_labels(self, representative_labels: np.ndarray) -> np.ndarray:
        full = np.full(self.n_rows, NOISE_LABEL, dtype=np.int64)
        full[self.keep] = representative_labels[self.inverse]
        return full


def _plan_rows(X: np.ndarray) -> _RowPlan:
    n_rows = X.shape[0]
    row_sum = X.sum(axis=1, dtype=np.float64)
    keep = np.flatnonzero(row_sum != 0)
    if len(keep) == 0:
        raise ValueError("adp: every row of X is all-zero - nothing to cluster")
    if len(keep) < n_rows:
        zero_rows = np.flatnonzero(row_sum == 0)
        logging.warning(
            "[adp] %d all-zero row(s) have no dice/jaccard distance - labelled %d (noise) for every metric, "
            "so every metric clusters the same subjects; row indices: %s",
            len(zero_rows),
            NOISE_LABEL,
            _head(zero_rows),
        )

    first_row_of_content: dict[bytes, int] = {}
    representatives, inverse = [], []
    for position, row in enumerate(keep):
        digest = hashlib.blake2b(np.asarray(X[row]).tobytes(), digest_size=16).digest()
        if digest not in first_row_of_content:
            first_row_of_content[digest] = len(representatives)
            representatives.append(position)
        inverse.append(first_row_of_content[digest])
    if len(representatives) < len(keep):
        representative_set = set(representatives)
        twins = [int(keep[p]) for p in range(len(keep)) if p not in representative_set]
        logging.warning(
            "[adp] %d row(s) are exact duplicates of another row (distance 0) - clustered once and labelled "
            "like their twin; row indices: %s",
            len(twins),
            _head(twins),
        )
    return _RowPlan(n_rows, keep, np.asarray(representatives), np.asarray(inverse))


def _head(indices) -> str:
    indices = [int(i) for i in indices]
    return str(indices[:_LOGGED_INDICES]) + (" ..." if len(indices) > _LOGGED_INDICES else "")


@dataclass
class _DensityFit:
    """DADApy's Clustering object after intrinsic dimension and density: everything independent of Z."""

    clustering: object
    intrinsic_dim: float


class _AdpSession:
    """One matrix, any number of (metric, maxk, Z) requests, with everything shareable computed once:
    the row plan (per matrix), the full distance matrix (per metric) and the density fit (per
    metric and maxk). Memory grows with the number of distinct metrics requested (one N x N float64
    each) - a sweep rarely asks for more than three.
    """

    def __init__(self, X: np.ndarray) -> None:
        self._plan = _plan_rows(X)
        # copy only when rows were dropped (X can be a ~1.4 GB uint8 matrix)
        self.X_kept = X if len(self._plan.keep) == X.shape[0] else X[self._plan.keep]
        self._distances: dict[str, np.ndarray] = {}
        self._squared_euclidean: np.ndarray | None = None
        self._fits: dict[tuple[str, int], _DensityFit] = {}

    @property
    def plan(self) -> _RowPlan:
        return self._plan

    def distance(self, metric: str) -> np.ndarray:
        """N_kept x N_kept distances (twins included), cached per metric."""
        if metric not in self._distances:
            logging.info("[adp] computing %s distances for %d row(s)", metric, self.X_kept.shape[0])
            self._distances[metric] = pairwise_distance(self.X_kept, metric)
        return self._distances[metric]

    def squared_euclidean_distance(self) -> np.ndarray:
        """Element-wise square of the euclidean distance matrix, cached (Calinski-Harabasz/Davies-Bouldin below)."""
        if self._squared_euclidean is None:
            self._squared_euclidean = self.distance("euclidean") ** 2
        return self._squared_euclidean

    def density_fit(self, metric: str, maxk: int) -> _DensityFit:
        key = (metric, maxk)
        if key not in self._fits:
            self._fits[key] = self._fit_density(metric, maxk)
        return self._fits[key]

    def _fit_density(self, metric: str, maxk: int) -> _DensityFit:
        representatives = self._plan.representatives
        n_distinct = len(representatives)
        if maxk >= n_distinct:
            raise ValueError(f"adp: maxk={maxk} needs more than maxk distinct rows, X has {n_distinct} (after dropping zero rows/duplicates)")
        distances = self.distance(metric)[np.ix_(representatives, representatives)]
        if not np.isfinite(distances).all():
            raise ValueError(f"adp: the {metric} distance matrix has non-finite values")

        neighbours = np.argsort(distances, axis=1, kind="stable")[:, : maxk + 1]
        neighbour_distances = np.take_along_axis(distances, neighbours, axis=1)
        # Rows are distinct, so only a row's own entry may sit at distance 0; a second one is a
        # numerically-zero distance between different rows, on which DADApy's density divides by 0.
        if np.any(neighbour_distances[:, 1] <= 0):
            raise ValueError(
                f"adp: two distinct rows are at {metric} distance 0 (numerically) - the density estimate would "
                "divide by 0; row positions (among the distinct rows): "
                f"{_head(np.flatnonzero(neighbour_distances[:, 1] <= 0))}"
            )

        Clustering = _import_dadapy()
        clustering = Clustering(distances=(neighbour_distances, neighbours), maxk=maxk, verbose=False)
        clustering.compute_id_2NN()
        clustering.compute_density_PAk()
        logging.info("[adp] metric=%s maxk=%d: intrinsic dimension (2NN) = %.2f", metric, maxk, clustering.intrinsic_dim)
        return _DensityFit(clustering, float(clustering.intrinsic_dim))

    def labels(self, metric: str, maxk: int, z: float) -> tuple[np.ndarray, np.ndarray, float]:
        """(labels of every row of X, labels of the kept rows only, intrinsic dimension)."""
        fit = self.density_fit(metric, maxk)
        fit.clustering.compute_clustering_ADP(Z=z, halo=False)
        representative_labels = np.asarray(fit.clustering.cluster_assignment).astype(np.int64)
        full = self._plan.to_full_labels(representative_labels)
        return full, full[self._plan.keep], fit.intrinsic_dim


def adp_cluster(X: np.ndarray, params: dict) -> np.ndarray:
    """ADP labels for every row of X - the CLUSTERING_METHODS contract. params: {"metric", "Z", "maxk"}
    (validate_adp_params). Zero-sum rows get NOISE_LABEL; see the module docstring."""
    metric, z, maxk = validate_adp_params(params)
    full, _, _ = _AdpSession(X).labels(metric, maxk, z)
    return full


def run_adp_tuning_sweep(
    X: np.ndarray, base_params: dict, tuning_grid: dict[str, list]
) -> tuple[pd.DataFrame, dict[tuple, np.ndarray]]:
    """Every combination of tuning_grid (keys among metric/Z/maxk, each overriding base_params) ->
    (results, labels_by_combo), same shape as clustering_tuning.run_clustering_tuning_sweep.

    The distances and the density fit are computed once per metric / (metric, maxk), so a sweep over
    Z - the usual case - costs one fit plus one cheap clustering per value. Columns of results:
    the swept keys; silhouette (on the very distance ADP clustered with); calinski_harabasz and
    davies_bouldin (euclidean only, NaN otherwise - they are centroid-based, same rule as agglomerative);
    noise_fraction; n_clusters_found (non-noise); largest_cluster_share; n_small_clusters (fewer than
    SMALL_CLUSTER_SIZE subjects); id_2nn (intrinsic dimension, constant per metric/maxk); ari_vs_prev_z
    (ARI, on the clustered rows only, against the next-lower Z of the same other parameters, NaN for
    the first - a plateau of ~1 means the partition did not change).

    Raises ValueError for an unknown grid key, for a value repeated within one axis or for any
    invalid parameter value (validate_adp_params).
    """
    unknown = set(tuning_grid) - ADP_PARAM_KEYS
    if unknown:
        raise ValueError(f"adp tuning_grid keys must be among {sorted(ADP_PARAM_KEYS)}, got unknown {sorted(unknown)}")

    for key, values in tuning_grid.items():
        repeated = sorted({value for value in values if list(values).count(value) > 1}, key=str)
        if repeated:
            raise ValueError(
                f"adp tuning_grid[{key!r}] has duplicate value(s) {repeated!r} in {list(values)!r}: "
                "the same combination would be evaluated twice and collapse into one labels_by_combo entry"
            )

    keys = list(tuning_grid)
    combinations = list(itertools.product(*tuning_grid.values()))
    logging.info("Starting adp fine-tuning sweep (%d combinations)", len(combinations))
    session = _AdpSession(X)

    rows, labels_by_combo = [], {}
    for i, combo in enumerate(combinations, 1):
        combo_dict = dict(zip(keys, combo))
        metric, z, maxk = validate_adp_params({**base_params, **combo_dict})
        logging.info("Evaluating combination %d/%d: %s", i, len(combinations), combo_dict)
        full, kept, intrinsic_dim = session.labels(metric, maxk, z)
        rows.append({**combo_dict, **_scores(session, metric, full, kept), "id_2nn": intrinsic_dim})
        labels_by_combo[combo] = full

    results = pd.DataFrame(rows)
    results["ari_vs_prev_z"] = _ari_vs_previous_z(keys, combinations, labels_by_combo)
    return results, labels_by_combo


def _scores(session: _AdpSession, metric: str, full_labels: np.ndarray, kept_labels: np.ndarray) -> dict[str, float]:
    sizes = np.bincount(full_labels[full_labels != NOISE_LABEL])
    n_clusters = int(len(sizes))
    scores = {
        "noise_fraction": float((full_labels == NOISE_LABEL).mean()),
        "n_clusters_found": float(n_clusters),
        "largest_cluster_share": float(sizes.max() / len(full_labels)),
        "n_small_clusters": float((sizes < SMALL_CLUSTER_SIZE).sum()),
    }
    nan = float("nan")
    if n_clusters < 2 or n_clusters > len(kept_labels) - 1:
        logging.warning("[adp] %d cluster(s) found (need 2..n-1) - silhouette/calinski_harabasz/davies_bouldin recorded as NaN", n_clusters)
        return {"silhouette": nan, "calinski_harabasz": nan, "davies_bouldin": nan, **scores}

    scores["silhouette"] = float(silhouette_score(session.distance(metric), kept_labels, metric="precomputed"))
    if metric == "euclidean":
        scores["calinski_harabasz"], scores["davies_bouldin"] = _euclidean_dispersion_scores(session.squared_euclidean_distance(), kept_labels)
    else:
        scores["calinski_harabasz"] = scores["davies_bouldin"] = nan
    return scores


def _euclidean_dispersion_scores(squared_distances: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    """(Calinski-Harabasz, Davies-Bouldin) of a clustering, computed from the matrix of *squared*
    euclidean distances alone - the same two numbers sklearn returns for (X, labels), without X.

    sklearn's versions convert X to float64 (10-14 GB for a 5845 x 221955-291345 voxel matrix, once per
    Z); the distance matrix is already in memory. With S[k, l] = sum of d^2 over the pairs (i in k, j in l)
    and n_k the cluster sizes, every term is exact (not an approximation):
      within-cluster dispersion  W_k = S[k, k] / (2 n_k);   total dispersion T = sum(d^2) / (2 n)
      squared distance of i (in k) to its centroid = (sum_j d_ij^2 over j in k) / n_k - S[k, k] / (2 n_k^2)
      squared distance between centroids k, l = S[k, l] / (n_k n_l) - S[k, k] / (2 n_k^2) - S[l, l] / (2 n_l^2)
    The degenerate returns (1.0 / 0.0 when the dispersion or every centroid distance is 0) are sklearn's.
    """
    n = len(labels)
    clusters, membership = np.unique(labels, return_inverse=True)
    k = len(clusters)
    indicator = np.zeros((n, k))
    indicator[np.arange(n), membership] = 1.0
    sizes = indicator.sum(axis=0)

    to_cluster = squared_distances @ indicator  # (n, k): sum over j in cluster l of d_ij^2
    pair_sums = indicator.T @ to_cluster  # (k, k): S
    within = np.diag(pair_sums) / (2 * sizes)

    within_total = within.sum()
    between_total = squared_distances.sum() / (2 * n) - within_total
    calinski_harabasz = 1.0 if within_total == 0 else float((between_total / (k - 1)) / (within_total / (n - k)))

    squared_to_own_centroid = to_cluster[np.arange(n), membership] / sizes[membership] - np.diag(pair_sums)[membership] / (2 * sizes[membership] ** 2)
    intra = np.bincount(membership, weights=np.sqrt(np.maximum(squared_to_own_centroid, 0.0))) / sizes
    squared_centroid_distance = pair_sums / np.outer(sizes, sizes) - within[:, None] / sizes[:, None] - within[None, :] / sizes[None, :]
    # a centroid's distance to itself is 0 by definition; the formula leaves ~1e-8 of rounding there, which
    # would be divided into the intra-cluster sum below instead of being skipped as sklearn skips an exact 0
    np.fill_diagonal(squared_centroid_distance, 0.0)
    centroid_distance = np.sqrt(np.maximum(squared_centroid_distance, 0.0))
    if np.allclose(intra, 0.0) or np.allclose(centroid_distance, 0.0):
        return calinski_harabasz, 0.0
    centroid_distance[centroid_distance == 0] = np.inf
    davies_bouldin = float(np.mean(np.max((intra[:, None] + intra[None, :]) / centroid_distance, axis=1)))
    return calinski_harabasz, davies_bouldin


def _ari_vs_previous_z(keys: list[str], combinations: list[tuple], labels_by_combo: dict[tuple, np.ndarray]) -> list[float]:
    """For each combination (in the given order), the ARI against the combination with the next-lower
    Z among those sharing every other swept value; NaN when there is none (Z not swept, or lowest Z)."""
    if "Z" not in keys:
        return [float("nan")] * len(combinations)
    z_position = keys.index("Z")

    def group_of(combo: tuple) -> tuple:
        return combo[:z_position] + combo[z_position + 1 :]

    by_group: dict[tuple, list[tuple]] = {}
    for combo in combinations:
        by_group.setdefault(group_of(combo), []).append(combo)
    previous: dict[tuple, tuple] = {}
    for members in by_group.values():
        ordered = sorted(members, key=lambda c: c[z_position])
        previous.update(zip(ordered[1:], ordered[:-1]))
    def ari(earlier: np.ndarray, later: np.ndarray) -> float:
        clustered = (earlier != NOISE_LABEL) & (later != NOISE_LABEL)  # the dropped rows are noise at every Z
        return float(adjusted_rand_score(earlier[clustered], later[clustered]))

    return [ari(labels_by_combo[previous[combo]], labels_by_combo[combo]) if combo in previous else float("nan") for combo in combinations]
