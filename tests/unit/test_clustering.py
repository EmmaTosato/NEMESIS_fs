"""Unit tests for src/analysis/clustering.py."""

import numpy as np

from src.analysis.clustering import (
    CLUSTERING_METHODS,
    agglomerative_cluster,
    dbscan_cluster,
    gmm_cluster,
    kmeans_cluster,
    spectral_cluster,
)

_X = np.random.default_rng(0).random((30, 5))


def test_registry_has_expected_methods():
    assert set(CLUSTERING_METHODS) == {"kmeans", "agglomerative", "gmm", "dbscan", "spectral"}
    assert CLUSTERING_METHODS["kmeans"] is kmeans_cluster
    assert CLUSTERING_METHODS["agglomerative"] is agglomerative_cluster
    assert CLUSTERING_METHODS["gmm"] is gmm_cluster
    assert CLUSTERING_METHODS["dbscan"] is dbscan_cluster
    assert CLUSTERING_METHODS["spectral"] is spectral_cluster


def test_kmeans_cluster_shape_and_label_count():
    labels = kmeans_cluster(_X, {"n_clusters": 4, "random_state": 0, "n_init": "auto"})
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {0, 1, 2, 3}


def test_agglomerative_cluster_shape_and_label_count():
    labels = agglomerative_cluster(_X, {"n_clusters": 4, "linkage": "ward"})
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {0, 1, 2, 3}


def test_gmm_cluster_shape_and_label_count():
    labels = gmm_cluster(_X, {"n_components": 4, "random_state": 0})
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {0, 1, 2, 3}


def test_spectral_cluster_shape_and_label_count():
    labels = spectral_cluster(_X, {"n_clusters": 4, "affinity": "nearest_neighbors", "random_state": 0})
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {0, 1, 2, 3}


def test_dbscan_cluster_shape_and_noise_label():
    # eps=0.5/min_samples=5 on this synthetic (30, 5) uniform data produces
    # noise (-1) plus one real cluster (0) - verified by manual smoke-test.
    # The point of this test is that -1 is a legitimate label, not an error.
    labels = dbscan_cluster(_X, {"eps": 0.5, "min_samples": 5})
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {-1, 0, 1, 2, 3}
    assert -1 in labels.tolist()
