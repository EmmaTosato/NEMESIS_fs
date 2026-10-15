"""Which single-run evaluation applies to which clustering method.

Backs notebooks/post-results_analysis/clustering_evaluation.ipynb: each of its sections is one
evaluation (a metric, or a bundle of metrics) and declares here which of
CLUSTERING_METHODS it is meaningful for. The notebook calls require_applicable before every
section, so a run of the wrong method is refused loudly instead of producing a number that
looks valid and is not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples
from sklearn.mixture import GaussianMixture

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_tuning import compute_silhouette_samples, require_euclidean_compatible


@dataclass(frozen=True)
class Evaluation:
    methods: frozenset[str]
    reason: str


_ALL_METHODS = frozenset(CLUSTERING_METHODS)

EVALUATIONS: dict[str, Evaluation] = {
    "geometric_metrics": Evaluation(
        _ALL_METHODS - {"adp"},
        "indici euclidei su (X, etichette); adp clusterizza la distanza dice della matrice grezza, che questi "
        "indici misurerebbero in un'altra geometria - per adp ci sono la purezza dei vicini e la silhouette sulla distanza dice",
    ),
    "null_reference": Evaluation(
        _ALL_METHODS - {"adp", "evidence_accumulation"},
        "rifitta il metodo su dati senza struttura della stessa forma della run; l'input di adp è la matrice "
        "grezza dei voxel, i cui rifit richiedono minuti ciascuno e che non ha un riferimento gaussiano della stessa forma; "
        "ogni fit di evidence_accumulation ripete spectral 50 volte, troppo lento per decine di rifit",
    ),
    "knn_purity": Evaluation(
        frozenset({"adp"}),
        "adp decide sui vicini più prossimi di ogni soggetto; su una distanza dice saturata (le lesioni) la "
        "silhouette (che guarda tutte le coppie) non vede questa geometria",
    ),
    "adp_silhouette": Evaluation(
        frozenset({"adp"}),
        "silhouette sulla distanza con cui adp clusterizza (dice sulla matrice grezza), non sullo spazio euclideo; "
        "va letta insieme alla quota di coppie a distanza 1, che la rende inutilizzabile quando è alta",
    ),
    "model_fit_metrics": Evaluation(
        frozenset({"kmeans", "gmm", "hdbscan"}),
        "solo questi espongono una statistica propria del modello (inertia, BIC/AIC, quota di rumore); "
        "agglomerative, spectral, evidence_accumulation e adp non ne hanno",
    ),
    "clinical_association": Evaluation(_ALL_METHODS, "dipende solo dalle etichette"),
    "centroids": Evaluation(_ALL_METHODS, "media delle coordinate dell'embedding per cluster"),
    "representative_maps": Evaluation(_ALL_METHODS, "soggetto reale più vicino a ogni centroide"),
}


def require_applicable(evaluation: str, method: str) -> None:
    if evaluation not in EVALUATIONS:
        raise ValueError(f"valutazione sconosciuta {evaluation!r} - note: {sorted(EVALUATIONS)}")
    spec = EVALUATIONS[evaluation]
    if method not in spec.methods:
        raise ValueError(
            f"la valutazione {evaluation!r} non è definita per il metodo {method!r} - si applica a "
            f"{sorted(spec.methods)} ({spec.reason})"
        )


def model_fit_metrics(method: str, X: np.ndarray, params: dict, labels: np.ndarray) -> dict[str, float]:
    """The model-specific statistic of an already-produced run: inertia (kmeans), BIC/AIC (gmm),
    noise fraction and number of clusters found (hdbscan).

    kmeans and gmm need the fitted estimator, which a run does not store, so it is refit with
    the run's own params. The refit is accepted only if it reproduces the stored labels exactly
    - otherwise (e.g. random_state=None) the statistic would describe a different fit than the
    one that produced the labels, and it raises. hdbscan's statistics come from the labels alone.
    """
    require_applicable("model_fit_metrics", method)
    labels = np.asarray(labels)

    if method == "hdbscan":
        noise = labels == -1
        return {
            "noise_fraction": float(noise.mean()),
            "n_clusters_found": float(len(np.unique(labels[~noise]))),
        }

    if method == "kmeans":
        fitted = KMeans(**params).fit(X)
        refit_labels = fitted.labels_
        metrics = {"inertia": float(fitted.inertia_)}
    else:
        fitted = GaussianMixture(**params).fit(X)
        refit_labels = fitted.predict(X)
        metrics = {"bic": float(fitted.bic(X)), "aic": float(fitted.aic(X))}

    if not np.array_equal(refit_labels, labels):
        raise ValueError(
            f"refitting {method!r} with params={params} does not reproduce the stored labels "
            "(is random_state unset?) - its statistic would describe a different fit than the run"
        )
    return metrics


@dataclass(frozen=True)
class SilhouetteBreakdown:
    """Silhouette of one run split by cluster. `micro` is the mean over subjects (what
    sklearn's silhouette_score returns, dominated by the large clusters), `macro` the mean of the
    per-cluster means (every cluster weighs the same), `minimum` the weakest cluster's mean."""

    clusters: pd.DataFrame  # index: cluster label; columns: n, silhouette_mean, share_negative
    micro: float
    macro: float
    minimum: float


def per_cluster_silhouette(X: np.ndarray, labels: np.ndarray, combo_params: dict) -> SilhouetteBreakdown:
    """Per-cluster breakdown of the Euclidean silhouette, noise (label -1) excluded.

    `combo_params` is the run's own params: required (not optional like in
    compute_clustering_metrics) so a run clustered under a non-Euclidean metric/affinity is
    refused here too, instead of being scored under the wrong geometry (lessons_learned.md #15).
    Raises ValueError for fewer than 2 non-noise clusters (compute_silhouette_samples).
    """
    require_euclidean_compatible(combo_params)
    kept_labels, samples = compute_silhouette_samples(X, np.asarray(labels))
    return _silhouette_breakdown(kept_labels, samples)


def _silhouette_breakdown(labels: np.ndarray, samples: np.ndarray) -> SilhouetteBreakdown:
    grouped = pd.DataFrame({"cluster": labels, "silhouette": samples}).groupby("cluster")["silhouette"]
    clusters = pd.DataFrame(
        {"n": grouped.size(), "silhouette_mean": grouped.mean(), "share_negative": grouped.apply(lambda s: float((s < 0).mean()))}
    )
    return SilhouetteBreakdown(
        clusters=clusters,
        micro=float(samples.mean()),
        macro=float(clusters["silhouette_mean"].mean()),
        minimum=float(clusters["silhouette_mean"].min()),
    )


def _check_distance_matrix(distances: np.ndarray, labels: np.ndarray, caller: str) -> None:
    n = len(labels)
    if distances.shape != (n, n):
        raise ValueError(f"distances must be ({n}, {n}) to match labels, got {distances.shape}")
    if not np.isfinite(distances).all():
        raise ValueError("distances contains NaN or inf")
    if (labels == -1).any():
        raise ValueError(f"labels contains noise (-1): pass only the clustered subjects (rows and columns of distances) to {caller}")


def distance_matrix_silhouette(distances: np.ndarray, labels: np.ndarray) -> SilhouetteBreakdown:
    """Per-cluster silhouette on a precomputed distance matrix: the geometry adp clusters in (dice on
    the raw matrix), which the Euclidean `per_cluster_silhouette` would score in another one.

    Only the clustered subjects: rows and columns of `distances` match `labels`, with no noise (-1).
    Raises ValueError for a non-square, non-finite or mismatched `distances`, noise labels, or fewer
    than 2 clusters / every subject its own cluster (the silhouette is undefined).
    """
    labels = np.asarray(labels)
    _check_distance_matrix(distances, labels, "distance_matrix_silhouette")
    n_clusters = len(np.unique(labels))
    if not 2 <= n_clusters <= len(labels) - 1:
        raise ValueError(f"cannot compute the silhouette: {n_clusters} cluster(s) found (need 2..n-1)")
    return _silhouette_breakdown(labels, silhouette_samples(distances, labels, metric="precomputed"))


def saturated_pair_share(distances: np.ndarray, tolerance: float = 1e-9) -> float:
    """Share of the pairs of distinct subjects whose distance is 1 (within `tolerance`).

    dice and jaccard are exactly 1 between two subjects with nothing in common. When most pairs are,
    a silhouette (which averages distances over whole clusters) sits near 0 whatever the neighbourhoods
    look like: 84% of the pairs of the lesion matrix, 0.0015% of the voxelwise disconnection one.
    Raises ValueError for a non-square matrix or fewer than 2 subjects.
    """
    n = distances.shape[0]
    if distances.ndim != 2 or distances.shape[1] != n or n < 2:
        raise ValueError(f"distances must be a square matrix of at least 2 subjects, got {distances.shape}")
    return float((distances >= 1.0 - tolerance).sum() / (n * (n - 1)))  # the zero diagonal never counts


NULL_KINDS = ("gaussian", "permute")


@dataclass(frozen=True)
class NullReference:
    """Observed silhouette against the same method refit on structureless data of the same shape.

    `null_values` holds one silhouette per null fit that found at least 2 clusters; `n_degenerate`
    counts the fits that did not (e.g. hdbscan labelling a structureless cloud as one cluster).
    """

    observed: float
    null_values: np.ndarray
    n_degenerate: int

    @property
    def null_mean(self) -> float:
        return float(self.null_values.mean())

    @property
    def null_sd(self) -> float:
        return float(self.null_values.std(ddof=1)) if len(self.null_values) > 1 else float("nan")

    @property
    def margin(self) -> float:
        """Observed minus null mean: the silhouette the method does NOT get for free."""
        return self.observed - self.null_mean


def _null_sample(X: np.ndarray, kind: str, rng: np.random.Generator) -> np.ndarray:
    """A structureless cloud with X's shape and dtype.

    gaussian: same mean and covariance as X (keeps the linear correlations, loses any shape or
    cluster). permute: every column shuffled on its own (keeps each marginal exactly, loses all
    dependence between columns).
    """
    if kind == "gaussian":
        covariance = np.atleast_2d(np.cov(X, rowvar=False))
        return rng.multivariate_normal(X.mean(axis=0), covariance, size=len(X)).astype(X.dtype)
    return np.column_stack([rng.permutation(X[:, j]) for j in range(X.shape[1])])


def null_reference_silhouette(
    method: str, X: np.ndarray, labels: np.ndarray, params: dict, null: str = "gaussian", n_null: int = 20, seed: int = 0
) -> NullReference:
    """The run's silhouette next to what the same method and params score on structureless data.

    A partition of a cloud with no clusters still gets a positive silhouette (a Gaussian cloud cut
    by ward k=3 scores ~0.40), so the absolute value says little: the margin over the null does.
    The observed value is computed on the stored labels, not on a refit. Noise (-1) is excluded
    on both sides, like everywhere else.

    Raises ValueError for a method outside the "null_reference" registry entry, an unknown `null`,
    n_null < 1, a non-Euclidean run, or when every null fit is degenerate (nothing to compare to).
    """
    require_applicable("null_reference", method)
    require_euclidean_compatible(params)
    if null not in NULL_KINDS:
        raise ValueError(f"unknown null {null!r} - known: {list(NULL_KINDS)}")
    if n_null < 1:
        raise ValueError(f"n_null must be >= 1, got {n_null}")
    if len(labels) != len(X):
        raise ValueError(f"labels has {len(labels)} entries but X has {len(X)} rows")

    observed = float(compute_silhouette_samples(X, np.asarray(labels))[1].mean())
    rng = np.random.default_rng(seed)
    values, n_degenerate = [], 0
    for _ in range(n_null):
        null_X = _null_sample(X, null, rng)
        null_labels = CLUSTERING_METHODS[method](null_X, params)
        kept = null_labels[null_labels != -1]
        if not 2 <= len(np.unique(kept)) <= len(kept) - 1:
            n_degenerate += 1
            continue
        values.append(float(compute_silhouette_samples(null_X, null_labels)[1].mean()))
    if not values:
        raise ValueError(f"all {n_null} null fits of {method!r} with params={params} found fewer than 2 clusters - no reference")
    return NullReference(observed=observed, null_values=np.asarray(values), n_degenerate=n_degenerate)


@dataclass(frozen=True)
class KnnPurity:
    """Share of each subject's k nearest neighbours that sit in its own cluster."""

    clusters: pd.DataFrame  # index: cluster label; columns: n, purity, chance, max_possible, evaluable
    purity: float  # mean over the subjects of the evaluable clusters
    chance: float  # same subjects, labels independent of the geometry
    n_not_evaluable: int  # subjects in clusters of k or fewer members
    tied_share: float  # subjects whose k-th neighbour is tied with the next one (see knn_purity)


_KNN_BLOCK_ROWS = 512


def knn_purity(distances: np.ndarray, labels: np.ndarray, k: int) -> KnnPurity:
    """Neighbourhood purity of a partition on a precomputed distance matrix.

    For each subject, the fraction of its k nearest neighbours (itself excluded) that carry its own
    label. Uses only the order of the distances, so a saturated distance (dice between lesions with
    no voxel in common is exactly 1) does not flatten it the way it flattens the silhouette. Ties at
    the k-th distance are not broken arbitrarily: the fraction is its expectation under a uniform
    random choice among the tied candidates, and `tied_share` reports how many subjects needed that.

    `chance` is the purity of labels unrelated to the geometry, (n_c - 1) / (n - 1) per subject. A
    cluster with k or fewer members cannot reach purity 1 (`max_possible` < 1): it is listed but
    `evaluable` is False and it is left out of the summary.

    Raises ValueError for a non-square, non-finite or mismatched `distances`, noise labels (-1: drop
    those rows first, a noise neighbour is neither same nor different), k outside [1, n - 1], fewer
    than 2 clusters, or no cluster with more than k members.
    """
    labels = np.asarray(labels)
    n = len(labels)
    _check_distance_matrix(distances, labels, "knn_purity")
    if not 1 <= k <= n - 1:
        raise ValueError(f"k must be in [1, {n - 1}], got {k}")
    if len(np.unique(labels)) < 2:
        raise ValueError("knn_purity needs at least 2 clusters")

    purity, tied = np.empty(n), np.empty(n, dtype=bool)
    for start in range(0, n, _KNN_BLOCK_ROWS):
        stop = min(start + _KNN_BLOCK_ROWS, n)
        block = np.array(distances[start:stop], dtype=np.float64)
        block[np.arange(stop - start), np.arange(start, stop)] = np.inf  # a subject is not its own neighbour
        kth = np.partition(block, k - 1, axis=1)[:, k - 1]
        sure, ties = block < kth[:, None], block == kth[:, None]
        same = labels[None, :] == labels[start:stop, None]
        needed = k - sure.sum(axis=1)  # slots left for the tied candidates, 1 <= needed <= n_ties
        n_ties = ties.sum(axis=1)
        purity[start:stop] = ((same & sure).sum(axis=1) + needed * (same & ties).sum(axis=1) / n_ties) / k
        tied[start:stop] = n_ties > needed

    sizes = pd.Series(labels).map(pd.Series(labels).value_counts()).to_numpy()
    chance = (sizes - 1) / (n - 1)
    frame = pd.DataFrame({"cluster": labels, "purity": purity, "chance": chance})
    clusters = frame.groupby("cluster").agg(n=("purity", "size"), purity=("purity", "mean"), chance=("chance", "mean"))
    clusters["max_possible"] = np.minimum(1.0, (clusters["n"] - 1) / k)
    clusters["evaluable"] = clusters["n"] > k
    evaluable_subjects = np.isin(labels, clusters.index[clusters["evaluable"]])
    if not evaluable_subjects.any():
        raise ValueError(f"no cluster has more than k={k} members - lower k")
    return KnnPurity(
        clusters=clusters,
        purity=float(purity[evaluable_subjects].mean()),
        chance=float(chance[evaluable_subjects].mean()),
        n_not_evaluable=int((~evaluable_subjects).sum()),
        tied_share=float(tied.mean()),
    )


def noise_warning(run_name: str, noise_fraction: float, threshold: float) -> str | None:
    """The message for a run whose noise (label -1) share exceeds `threshold`, else None.

    The geometric indices leave the noise out, so above the threshold they describe only
    1 - noise_fraction of the subjects. None is the documented answer for a run under the
    threshold, not a missing value. `threshold` has no default: the caller states it.

    Raises ValueError for a noise_fraction or threshold outside [0, 1].
    """
    for name, value in (("noise_fraction", noise_fraction), ("threshold", threshold)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {value}")
    if noise_fraction <= threshold:
        return None
    share = f"{noise_fraction:.1%}".replace(".", ",")
    return f"{run_name}: il {share} dei soggetti è rumore e gli indici qui sotto non lo valutano"
