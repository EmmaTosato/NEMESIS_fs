"""Unit tests for src/analysis/clustering_evaluation.py."""

import numpy as np
import pytest
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_evaluation import EVALUATIONS, model_fit_metrics, require_applicable


def _three_blobs():
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.3, size=(30, 2)),
            rng.normal(loc=[5, 5], scale=0.3, size=(30, 2)),
            rng.normal(loc=[0, 5], scale=0.3, size=(30, 2)),
        ]
    )


def test_every_evaluation_names_only_registered_methods():
    for name, spec in EVALUATIONS.items():
        assert spec.methods <= set(CLUSTERING_METHODS), name


def test_require_applicable_accepts_a_listed_method():
    require_applicable("model_fit_metrics", "kmeans")
    require_applicable("geometric_metrics", "agglomerative")


def test_require_applicable_rejects_an_unlisted_method():
    with pytest.raises(ValueError, match="'agglomerative'"):
        require_applicable("model_fit_metrics", "agglomerative")


def test_require_applicable_rejects_an_unknown_evaluation():
    with pytest.raises(ValueError, match="unknown evaluation"):
        require_applicable("silhouete", "kmeans")


def test_model_fit_metrics_kmeans_returns_the_inertia():
    X = _three_blobs()
    params = {"n_clusters": 3, "random_state": 0, "n_init": 10}
    labels = KMeans(**params).fit_predict(X)

    metrics = model_fit_metrics("kmeans", X, params, labels)

    assert metrics == {"inertia": pytest.approx(KMeans(**params).fit(X).inertia_)}


def test_model_fit_metrics_gmm_returns_bic_and_aic():
    X = _three_blobs()
    params = {"n_components": 3, "covariance_type": "full", "random_state": 0}
    labels = GaussianMixture(**params).fit_predict(X)

    metrics = model_fit_metrics("gmm", X, params, labels)

    fitted = GaussianMixture(**params).fit(X)
    assert metrics == {"bic": pytest.approx(fitted.bic(X)), "aic": pytest.approx(fitted.aic(X))}


def test_model_fit_metrics_hdbscan_reads_noise_and_cluster_count_from_labels():
    labels = np.array([0, 0, 1, 1, -1, -1, -1, 2])

    metrics = model_fit_metrics("hdbscan", np.zeros((8, 2)), {}, labels)

    assert metrics == {"noise_fraction": 3 / 8, "n_clusters_found": 3.0}


def test_model_fit_metrics_refuses_a_refit_that_does_not_reproduce_the_labels():
    X = _three_blobs()
    params = {"n_clusters": 3, "random_state": 0, "n_init": 10}
    other_labels = np.arange(len(X)) % 3  # not what KMeans produces on these blobs

    with pytest.raises(ValueError, match="does not reproduce the stored labels"):
        model_fit_metrics("kmeans", X, params, other_labels)


def test_model_fit_metrics_refuses_a_method_without_a_model_statistic():
    with pytest.raises(ValueError, match="'spectral'"):
        model_fit_metrics("spectral", np.zeros((4, 2)), {}, np.zeros(4, dtype=int))
