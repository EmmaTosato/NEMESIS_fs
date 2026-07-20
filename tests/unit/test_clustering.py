"""Unit tests for src/analysis/clustering.py."""

import numpy as np

from src.analysis.clustering import CLUSTERING_METHODS, kmeans_cluster

_X = np.random.default_rng(0).random((30, 5))


def test_registry_has_expected_methods():
    assert set(CLUSTERING_METHODS) == {"kmeans"}
    assert CLUSTERING_METHODS["kmeans"] is kmeans_cluster


def test_kmeans_cluster_shape_and_label_count():
    labels = kmeans_cluster(_X, {"n_clusters": 4, "random_state": 0, "n_init": "auto"})
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {0, 1, 2, 3}
