"""Which single-run evaluation applies to which clustering method.

Backs notebooks/post-results_analysis/clustering_evaluation.ipynb: each of its sections is one
evaluation (a metric, or a bundle of metrics, or a plot) and declares here which of
CLUSTERING_METHODS it is meaningful for. The notebook calls require_applicable before every
section, so a run of the wrong method is refused loudly instead of producing a number that
looks valid and is not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture

from src.analysis.clustering import CLUSTERING_METHODS


@dataclass(frozen=True)
class Evaluation:
    methods: frozenset[str]
    reason: str


_ALL_METHODS = frozenset(CLUSTERING_METHODS)

EVALUATIONS: dict[str, Evaluation] = {
    "geometric_metrics": Evaluation(_ALL_METHODS, "defined on any (X, labels) pair"),
    "model_fit_metrics": Evaluation(
        frozenset({"kmeans", "gmm", "hdbscan"}),
        "only these expose a model-specific statistic (inertia, BIC/AIC, noise fraction); "
        "agglomerative, spectral and evidence_accumulation have none",
    ),
    "subsampling_stability": Evaluation(_ALL_METHODS, "refit on a subsample is defined for any method"),
    "clinical_association": Evaluation(_ALL_METHODS, "depends only on the labels"),
    "produced_plots": Evaluation(_ALL_METHODS, "plots written by clustering.py for every method"),
    "centroids": Evaluation(_ALL_METHODS, "mean of the embedding coordinates per cluster"),
    "representative_maps": Evaluation(_ALL_METHODS, "nearest real subject to each centroid"),
}


def require_applicable(evaluation: str, method: str) -> None:
    if evaluation not in EVALUATIONS:
        raise ValueError(f"unknown evaluation {evaluation!r} - known: {sorted(EVALUATIONS)}")
    spec = EVALUATIONS[evaluation]
    if method not in spec.methods:
        raise ValueError(
            f"evaluation {evaluation!r} is not defined for method {method!r} - applicable to "
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
