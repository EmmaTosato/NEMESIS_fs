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

from src.analysis.clustering import CLUSTERING_METHODS, own_cluster_membership
from src.analysis.clustering_tuning import (
    compute_clustering_metrics,
    compute_silhouette_samples,
    dunn_index,
    hdbscan_labels_and_probabilities,
    require_euclidean_compatible,
)


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
    "knn_purity": Evaluation(
        frozenset({"adp"}),
        "adp decide sui vicini più prossimi di ogni soggetto; su una distanza dice saturata (le lesioni) la "
        "silhouette (che guarda tutte le coppie) non vede questa geometria, quindi la si legge accanto alla "
        "purezza e alla quota di coppie a distanza 1",
    ),
    "model_fit_metrics": Evaluation(
        frozenset({"kmeans", "gmm", "hdbscan", "hdbscan_soft"}),
        "solo questi espongono una statistica propria del modello (inertia, BIC/AIC, quota di rumore); "
        "agglomerative, spectral, evidence_accumulation e adp non ne hanno",
    ),
    "soft_membership": Evaluation(
        frozenset({"hdbscan_soft"}),
        "la matrice soggetti x cluster delle probabilità di appartenenza è un'uscita del soft clustering del pacchetto "
        "hdbscan, salvata con la run: gli altri metodi assegnano un soggetto a un cluster senza un grado di appartenenza "
        "a ciascuno (l'HDBSCAN di sklearn ha solo probabilities_, la vicinanza al nucleo del proprio cluster)",
    ),
    "membership_confidence": Evaluation(
        frozenset({"hdbscan"}),
        "probabilities_ è un'uscita del solo HDBSCAN (forza di appartenenza di ogni soggetto al proprio cluster, "
        "normalizzata dentro il cluster); gli altri metodi assegnano un soggetto a un cluster senza un grado di appartenenza",
    ),
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

    if method in ("hdbscan", "hdbscan_soft"):
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
class MembershipConfidence:
    """How firmly the subjects of an hdbscan run belong to their cluster, from `probabilities_`.

    `clusters` has one row per non-noise cluster: `n`, `probability_mean` and `share_below_threshold`
    (the share of its subjects under `threshold`). `n_confident` counts the non-noise subjects at or
    above `threshold`.
    """

    clusters: pd.DataFrame  # index: cluster label; columns: n, probability_mean, share_below_threshold
    threshold: float
    n_noise: int
    n_confident: int


def membership_confidence(
    method: str, X: np.ndarray, params: dict, labels: np.ndarray, threshold: float
) -> MembershipConfidence:
    """Membership strength of an already-produced hdbscan run.

    `probabilities_` is a lambda value normalised to [0, 1] inside each cluster (0 for noise), so it
    says how close a subject sits to the core of *its* cluster, not how likely it is to belong to this
    cluster rather than another. It exists only on the fitted estimator, which a run does not store: it
    is refit with the run's own params and accepted only if it reproduces the stored labels exactly, as
    in model_fit_metrics. It is a description of the density in the space clustered (an embedding with
    min_dist=0 is already packed), not a validity index.

    `threshold` has no default and no literature backing a value: the caller states it. Noise is left
    out of every number (its probability is 0 by construction).

    Raises ValueError for a method other than hdbscan, a threshold outside (0, 1], a refit that does
    not reproduce the labels, or a run where every subject is noise.
    """
    require_applicable("membership_confidence", method)
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0, 1], got {threshold}")
    labels = np.asarray(labels)
    noise = labels == -1
    if noise.all():
        raise ValueError("every subject is noise (label -1): there is no cluster to describe")

    refit_labels, probabilities = hdbscan_labels_and_probabilities(X, params)
    if not np.array_equal(refit_labels, labels):
        raise ValueError(
            f"refitting 'hdbscan' with params={params} does not reproduce the stored labels - "
            "its probabilities would describe a different fit than the run"
        )

    kept_probabilities = probabilities[~noise]
    frame = pd.DataFrame({"cluster": labels[~noise], "probability": kept_probabilities})
    grouped = frame.groupby("cluster")["probability"]
    clusters = pd.DataFrame(
        {
            "n": grouped.size(),
            "probability_mean": grouped.mean(),
            "share_below_threshold": grouped.apply(lambda p: float((p < threshold).mean())),
        }
    )
    return MembershipConfidence(
        clusters=clusters,
        threshold=threshold,
        n_noise=int(noise.sum()),
        n_confident=int((kept_probabilities >= threshold).sum()),
    )


@dataclass(frozen=True)
class SoftMembership:
    """The soft clustering of a hdbscan_soft run, summarised per cluster.

    `clusters` has one row per cluster: `n`, `own_mean` (mean probability of its subjects of belonging to
    it), `share_below_threshold`, `top_other` (the other cluster its subjects belong to most, on average)
    and `top_other_mean` (that average). `mean_vectors` is the mean membership vector of the subjects of each
    cluster (rows, plus -1 for the noise when there is any) over all the clusters (columns): the diagonal is
    `own_mean`, the off-diagonal cells say which clusters share subjects.
    """

    clusters: pd.DataFrame
    mean_vectors: pd.DataFrame
    threshold: float
    n_noise: int


def soft_membership_summary(labels: np.ndarray, membership: np.ndarray, threshold: float) -> SoftMembership:
    """Per-cluster summary of the (n_subjects, n_clusters) membership matrix saved by a hdbscan_soft run.

    The rows of `membership` do not sum to 1 (the rest is the probability of being noise), so the numbers
    are read as they are, never renormalised. `threshold` has no default: the caller states it. Noise
    (label -1) has no own cluster, so it is left out of `own_mean` and `share_below_threshold`.

    Raises ValueError for a threshold outside (0, 1], a run where every subject is noise, cluster labels
    that are not 0..k-1 (the column order of `membership`), or a matrix that is not (n_subjects, k).
    """
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0, 1], got {threshold}")
    labels = np.asarray(labels)
    cluster_ids = np.unique(labels[labels != -1])
    if len(cluster_ids) == 0:
        raise ValueError("every subject is noise (label -1): there is no cluster to describe")
    if not np.array_equal(cluster_ids, np.arange(len(cluster_ids))):
        raise ValueError(f"cluster labels must be 0..k-1 (the column order of the membership matrix), got {cluster_ids.tolist()}")
    if membership.shape != (len(labels), len(cluster_ids)):
        raise ValueError(f"membership must be ({len(labels)}, {len(cluster_ids)}) to match labels, got {membership.shape}")

    own = own_cluster_membership(membership, labels)
    rows, vectors = [], {}
    for cluster in cluster_ids:
        members = labels == cluster
        vector = membership[members].mean(axis=0)
        vectors[int(cluster)] = vector
        others = np.where(cluster_ids == cluster, -np.inf, vector)
        top_other = int(others.argmax()) if len(cluster_ids) > 1 else None
        rows.append(
            {
                "cluster": int(cluster),
                "n": int(members.sum()),
                "own_mean": float(own[members].mean()),
                "share_below_threshold": float((own[members] < threshold).mean()),
                "top_other": top_other,
                "top_other_mean": float(vector[top_other]) if top_other is not None else float("nan"),
            }
        )
    noise = labels == -1
    if noise.any():
        vectors[-1] = membership[noise].mean(axis=0)
    return SoftMembership(
        clusters=pd.DataFrame(rows).set_index("cluster"),
        mean_vectors=pd.DataFrame.from_dict(vectors, orient="index", columns=cluster_ids.tolist()),
        threshold=threshold,
        n_noise=int(noise.sum()),
    )


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


@dataclass(frozen=True)
class GeometricSummary:
    """The geometric indices of one run, on the space it was clustered in, noise (label -1)
    excluded. `silhouette` is the mean over subjects (micro), `silhouette_macro` the mean of the
    per-cluster means and `silhouette_min` the weakest cluster's (SilhouetteBreakdown), `clusters`
    the per-cluster table; `largest_cluster_share` is over all subjects, noise included, like
    `noise_fraction`."""

    n_subjects: int
    n_components: int
    n_clusters: int
    largest_cluster_share: float
    noise_fraction: float
    silhouette: float
    silhouette_macro: float
    silhouette_min: float
    calinski_harabasz: float
    davies_bouldin: float
    dunn: float
    clusters: pd.DataFrame  # per_cluster_silhouette's table: index cluster label; n, silhouette_mean, share_negative


def geometric_summary(X: np.ndarray, labels: np.ndarray, combo_params: dict) -> GeometricSummary:
    """Silhouette, Calinski-Harabasz, Davies-Bouldin, Dunn and the run's cluster/noise shares, the
    bundle of section 2 of notebooks/post-results_analysis/clustering_evaluation.ipynb.

    Euclidean only: `combo_params` is the run's own params and a run clustered under another
    metric/affinity is refused (require_euclidean_compatible), never scored in the wrong geometry.

    Raises ValueError for a `labels`/`X` length mismatch, fewer than 2 clusters once noise is left
    out, an index that comes out undefined (every cluster a single subject), or a non-Euclidean run.
    """
    labels = np.asarray(labels)
    if X.ndim != 2 or len(X) != len(labels):
        raise ValueError(f"X must be 2D with one row per label, got X.shape={X.shape} and {len(labels)} labels")
    sizes = np.unique(labels[labels != -1], return_counts=True)[1]
    if len(sizes) < 2:
        raise ValueError(f"the indices need at least 2 clusters once noise is left out, this run has {len(sizes)}")
    breakdown = per_cluster_silhouette(X, labels, combo_params)
    metrics = compute_clustering_metrics(X, labels, combo_params=combo_params)
    dunn = dunn_index(X, labels)
    undefined = sorted(name for name, value in {**metrics, "dunn": dunn}.items() if not np.isfinite(value))
    if undefined:
        raise ValueError(f"undefined for this run (every cluster is a single subject?): {undefined}")
    return GeometricSummary(
        n_subjects=len(labels), n_components=X.shape[1], n_clusters=len(sizes),
        largest_cluster_share=float(sizes.max() / len(labels)), noise_fraction=float(metrics["noise_fraction"]),
        silhouette=float(metrics["silhouette"]), silhouette_macro=breakdown.macro, silhouette_min=breakdown.minimum,
        calinski_harabasz=float(metrics["calinski_harabasz"]), davies_bouldin=float(metrics["davies_bouldin"]),
        dunn=float(dunn), clusters=breakdown.clusters,
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
