"""Unit tests for src/analysis/clustering.py."""

import numpy as np
import pytest

from src.analysis.clustering import (
    CLUSTERING_METHODS,
    agglomerative_cluster,
    gmm_cluster,
    hdbscan_cluster,
    kmeans_cluster,
    rsc_cluster,
    spectral_cluster,
)

_X = np.random.default_rng(0).random((30, 5))


def _two_blobs(n_per_blob=15):
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.2, size=(n_per_blob, 2)),
            rng.normal(loc=[6, 6], scale=0.2, size=(n_per_blob, 2)),
        ]
    )


def test_registry_has_expected_methods():
    assert set(CLUSTERING_METHODS) == {"kmeans", "agglomerative", "gmm", "hdbscan", "spectral", "rsc"}
    assert CLUSTERING_METHODS["kmeans"] is kmeans_cluster
    assert CLUSTERING_METHODS["agglomerative"] is agglomerative_cluster
    assert CLUSTERING_METHODS["gmm"] is gmm_cluster
    assert CLUSTERING_METHODS["hdbscan"] is hdbscan_cluster
    assert CLUSTERING_METHODS["spectral"] is spectral_cluster
    assert CLUSTERING_METHODS["rsc"] is rsc_cluster


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


def test_hdbscan_cluster_shape_and_noise_label():
    # min_cluster_size=3 on this synthetic (30, 5) uniform data produces
    # noise (-1) plus 2 real clusters - verified by manual smoke-test.
    # The point of this test is that -1 is a legitimate label, not an error.
    labels = hdbscan_cluster(_X, {"min_cluster_size": 3})
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {-1, 0, 1, 2, 3}
    assert -1 in labels.tolist()


def test_rsc_cluster_recovers_well_separated_blobs():
    X = _two_blobs()
    labels = rsc_cluster(
        X, {"n_clusters": 2, "affinity": "nearest_neighbors", "n_neighbors": 10, "n_repeats": 20}
    )
    assert labels.shape == (30,)
    assert set(labels.tolist()) == {0, 1}
    # every point within a blob must share the label - well-separated data,
    # co-occurrence should be unambiguous, so the final assignment must be exact
    assert len(set(labels[:15].tolist())) == 1
    assert len(set(labels[15:].tolist())) == 1
    assert labels[0] != labels[15]


def test_rsc_cluster_requires_n_repeats():
    X = _two_blobs()
    with pytest.raises(ValueError, match="n_repeats"):
        rsc_cluster(X, {"n_clusters": 2, "affinity": "nearest_neighbors", "n_neighbors": 10})


def test_rsc_cluster_requires_n_clusters():
    X = _two_blobs()
    with pytest.raises(ValueError, match="n_clusters"):
        rsc_cluster(X, {"affinity": "nearest_neighbors", "n_neighbors": 10, "n_repeats": 20})


def test_rsc_cluster_rejects_fixed_random_state():
    X = _two_blobs()
    with pytest.raises(ValueError, match="random_state"):
        rsc_cluster(
            X,
            {"n_clusters": 2, "affinity": "nearest_neighbors", "n_neighbors": 10, "n_repeats": 20, "random_state": 0},
        )
