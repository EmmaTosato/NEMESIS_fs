"""Test a proprietà di src/analysis/clustering.py: il contratto comune di CLUSTERING_METHODS (etichette
intere, rumore solo dove previsto, determinismo, indipendenza dall'ordine delle righe), le forme limite
(n=2,3; k=1, k=n) e la validazione di adp."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sklearn.metrics import adjusted_rand_score

from src.analysis.clustering import (
    CLUSTERING_METHODS,
    hdbscan_soft_fit,
    own_cluster_membership,
    soft_membership_matrix,
)
from tests.factories.matrices import gaussian_blobs

# Parametri per tre blob ben separati (24 soggetti): ogni metodo sensato li ritrova. `adp` non è qui:
# richiede dadapy, installato in un altro ambiente.
_BLOB_PARAMS: dict[str, dict] = {
    "kmeans": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
    "agglomerative": {"n_clusters": 3, "linkage": "ward"},
    "gmm": {"n_components": 3, "random_state": 0},
    "hdbscan": {"min_cluster_size": 4},
    "hdbscan_soft": {"min_cluster_size": 4},
    "spectral": {"n_clusters": 3, "affinity": "nearest_neighbors", "n_neighbors": 5, "random_state": 0},
}
_DENSITY = {"hdbscan", "hdbscan_soft"}
_METHODS = sorted(_BLOB_PARAMS)


@pytest.fixture(scope="module")
def blobs() -> tuple[np.ndarray, np.ndarray]:
    return gaussian_blobs(n_per_blob=8, seed=0)


def test_the_parametrized_methods_are_every_registered_one_except_adp():
    assert set(_BLOB_PARAMS) == set(CLUSTERING_METHODS) - {"adp"}


# --- contratto comune -----------------------------------------------------------------------------


@pytest.mark.parametrize("method", _METHODS)
def test_labels_are_one_integer_per_subject_and_contiguous_from_zero(method, blobs):
    X, truth = blobs
    labels = CLUSTERING_METHODS[method](X, dict(_BLOB_PARAMS[method]))

    assert labels.shape == (len(X),)
    assert np.issubdtype(labels.dtype, np.integer)
    assert labels.min() >= (-1 if method in _DENSITY else 0)  # il rumore (-1) solo per i metodi a densità
    clustered = np.unique(labels[labels != -1])
    assert clustered.tolist() == list(range(len(clustered)))  # 0..k-1, nessun buco
    assert adjusted_rand_score(truth, labels) == pytest.approx(1.0)  # i blob separati sono ritrovati


@pytest.mark.parametrize("method", _METHODS)
def test_the_same_call_twice_gives_identical_labels_and_leaves_the_inputs_alone(method, blobs):
    X, _ = blobs
    params = dict(_BLOB_PARAMS[method])
    snapshot_X, snapshot_params = X.copy(), dict(params)
    first = CLUSTERING_METHODS[method](X, params)
    second = CLUSTERING_METHODS[method](X, params)
    np.testing.assert_array_equal(first, second)
    np.testing.assert_array_equal(X, snapshot_X)
    assert params == snapshot_params


@pytest.mark.parametrize("method", _METHODS)
@settings(max_examples=6)
@given(st.integers(0, 10_000))
def test_the_partition_does_not_depend_on_the_row_order(method, blobs, seed):
    X, _ = blobs
    order = np.random.default_rng(seed).permutation(len(X))
    straight = CLUSTERING_METHODS[method](X, dict(_BLOB_PARAMS[method]))
    permuted = CLUSTERING_METHODS[method](X[order], dict(_BLOB_PARAMS[method]))
    assert adjusted_rand_score(straight[order], permuted) == pytest.approx(1.0)


@pytest.mark.parametrize("method", _METHODS)
def test_a_common_translation_of_the_data_does_not_change_the_partition(method, blobs):
    X, _ = blobs
    base = CLUSTERING_METHODS[method](X, dict(_BLOB_PARAMS[method]))
    moved = CLUSTERING_METHODS[method](X + 500.0, dict(_BLOB_PARAMS[method]))
    assert adjusted_rand_score(base, moved) == pytest.approx(1.0)


# --- forme limite ---------------------------------------------------------------------------------

_K_METHODS = [("kmeans", "n_clusters"), ("agglomerative", "n_clusters"), ("gmm", "n_components")]


@pytest.mark.parametrize("method, k_name", _K_METHODS)
@pytest.mark.parametrize("n", [2, 3])
@pytest.mark.parametrize("k_is_n", [False, True], ids=["k=1", "k=n"])
def test_one_cluster_and_one_cluster_per_subject_on_two_and_three_subjects(method, k_name, n, k_is_n):
    X = np.random.default_rng(0).random((n, 3))
    k = n if k_is_n else 1
    params = {**_BLOB_PARAMS[method], k_name: k}
    labels = CLUSTERING_METHODS[method](X, params)
    assert labels.shape == (n,)
    assert len(np.unique(labels)) == k


@pytest.mark.parametrize("method", ["kmeans", "agglomerative"])
@settings(max_examples=25)
@given(n=st.integers(2, 14), data=st.data(), seed=st.integers(0, 10_000))
def test_exactly_k_clusters_for_any_k_up_to_the_number_of_distinct_subjects(method, n, data, seed):
    k = data.draw(st.integers(1, n))
    X = np.random.default_rng(seed).normal(size=(n, 3))
    labels = CLUSTERING_METHODS[method](X, {**_BLOB_PARAMS[method], "n_clusters": k})
    assert sorted(np.unique(labels).tolist()) == list(range(k))


@settings(max_examples=20)
@given(n=st.integers(2, 14), data=st.data(), seed=st.integers(0, 10_000))
def test_gmm_uses_at_most_k_components_and_labels_stay_in_range(n, data, seed):
    k = data.draw(st.integers(1, n))
    X = np.random.default_rng(seed).normal(size=(n, 3))
    labels = CLUSTERING_METHODS["gmm"](X, {**_BLOB_PARAMS["gmm"], "n_components": k})
    assert labels.shape == (n,) and labels.min() >= 0 and labels.max() < k


@pytest.mark.parametrize("method", sorted(_DENSITY))
@pytest.mark.parametrize("n", [2, 3])
def test_density_methods_call_everything_noise_when_there_are_too_few_subjects_for_a_cluster(method, n):
    X = np.random.default_rng(0).random((n, 3))
    labels = CLUSTERING_METHODS[method](X, {"min_cluster_size": 2})
    assert labels.tolist() == [-1] * n


# --- hdbscan_soft e appartenenza morbida ----------------------------------------------------------


def test_soft_membership_has_one_column_per_cluster_with_probabilities_that_leave_room_for_noise(blobs):
    X, _ = blobs
    fitted = hdbscan_soft_fit(X, {"min_cluster_size": 4})
    membership = soft_membership_matrix(fitted)
    n_clusters = len(np.unique(fitted.labels_[fitted.labels_ != -1]))
    assert membership.shape == (len(X), n_clusters)
    assert (membership >= -1e-12).all() and (membership <= 1 + 1e-9).all()
    assert (membership.sum(axis=1) <= 1 + 1e-9).all()  # il resto è la probabilità di essere rumore, mai > 1
    own = own_cluster_membership(membership, fitted.labels_)
    assert np.isfinite(own).all() and (own > 0).all()  # in blob separati ognuno appartiene al proprio cluster


def test_soft_membership_of_a_fit_with_no_cluster_is_an_empty_matrix_not_an_error():
    X = np.random.default_rng(0).random((12, 2))
    fitted = hdbscan_soft_fit(X, {"min_cluster_size": 12})
    assert (fitted.labels_ == -1).all()
    assert soft_membership_matrix(fitted).shape == (12, 0)


@given(st.lists(st.integers(-1, 3), min_size=1, max_size=30), st.integers(0, 10_000))
def test_own_cluster_membership_is_nan_for_noise_and_the_labels_column_elsewhere(labels, seed):
    labels = np.array(labels)
    membership = np.random.default_rng(seed).random((len(labels), 4))
    own = own_cluster_membership(membership, labels)
    assert np.isnan(own).tolist() == (labels == -1).tolist()  # il rumore non appartiene a nessuno: NaN, non 0
    clustered = labels != -1
    np.testing.assert_array_equal(own[clustered], membership[np.flatnonzero(clustered), labels[clustered]])


# --- validazione di adp ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [{"metric": "chebyshev", "Z": 1.5, "maxk": 5}, {"metric": "dice", "Z": 0, "maxk": 5},
                                 {"metric": "dice", "Z": 1.5, "maxk": 1}, {"metric": "dice", "Z": 1.5}, {"metric": "dice", "Z": 1.5, "maxk": 5, "typo": 1}])
def test_adp_refuses_invalid_parameters_before_it_needs_dadapy(bad):
    with pytest.raises(ValueError):
        CLUSTERING_METHODS["adp"](np.ones((4, 4)), bad)
