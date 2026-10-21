"""Test a proprietà di src/analysis/consensus_clustering.py: struttura delle matrici di co-occorrenza
(simmetria, diagonale, multipli di 1/n_repeats), covarianza alle permutazioni, stabilità PAC, eigengap."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.consensus_clustering import (
    CONSENSUS_ELIGIBLE_METHODS,
    K_PARAM_NAME,
    compute_monti_stability,
    compute_rsc_eigengap,
    run_monti_repeats,
    run_rsc_repeats,
    subsampling_stability_index,
)
from tests.factories.matrices import gaussian_blobs

_PARAMS = {
    "kmeans": {"n_clusters": 3, "n_init": "auto"},
    "gmm": {"n_components": 3},
    "spectral": {"n_clusters": 3, "affinity": "nearest_neighbors", "n_neighbors": 5},
}
_INELIGIBLE = sorted(set(CLUSTERING_METHODS) - CONSENSUS_ELIGIBLE_METHODS)


@pytest.fixture(scope="module")
def blobs() -> np.ndarray:
    return gaussian_blobs(n_per_blob=6, seed=1)[0]  # 18 soggetti, 3 blob ben separati


def test_the_k_parameter_table_covers_exactly_the_eligible_methods():
    assert set(K_PARAM_NAME) == CONSENSUS_ELIGIBLE_METHODS
    for method, name in K_PARAM_NAME.items():
        assert name in _PARAMS[method]  # il parametro K di ogni metodo è davvero quello usato dal registro


# --- run_rsc_repeats ------------------------------------------------------------------------------


@pytest.mark.parametrize("method", sorted(CONSENSUS_ELIGIBLE_METHODS))
@settings(max_examples=4)
@given(n_repeats=st.integers(1, 4), base_seed=st.integers(0, 100))
def test_rsc_matrix_is_symmetric_with_unit_diagonal_and_multiples_of_one_over_n_repeats(method, blobs, n_repeats, base_seed):
    co = run_rsc_repeats(method, blobs, _PARAMS[method], n_repeats, base_seed=base_seed)
    n = len(blobs)
    assert co.shape == (n, n)
    np.testing.assert_array_equal(co, co.T)
    np.testing.assert_array_equal(np.diag(co), np.ones(n))  # ogni soggetto sta sempre con sé stesso
    assert ((co >= 0) & (co <= 1)).all()
    np.testing.assert_allclose(co * n_repeats, np.round(co * n_repeats), atol=1e-9)
    if n_repeats == 1:
        assert set(np.unique(co)) <= {0.0, 1.0}


@pytest.mark.parametrize("method", sorted(CONSENSUS_ELIGIBLE_METHODS))
@settings(max_examples=4)
@given(st.integers(0, 10_000))
def test_rsc_matrix_follows_the_subjects_when_the_rows_are_permuted(method, blobs, seed):
    order = np.random.default_rng(seed).permutation(len(blobs))
    straight = run_rsc_repeats(method, blobs, _PARAMS[method], 3)
    permuted = run_rsc_repeats(method, blobs[order], _PARAMS[method], 3)
    np.testing.assert_array_equal(permuted, straight[np.ix_(order, order)])


def test_rsc_is_reproducible_with_the_same_base_seed(blobs):
    first = run_rsc_repeats("kmeans", blobs, _PARAMS["kmeans"], 3, base_seed=5)
    np.testing.assert_array_equal(first, run_rsc_repeats("kmeans", blobs, _PARAMS["kmeans"], 3, base_seed=5))


@pytest.mark.parametrize("method", _INELIGIBLE)
def test_every_method_without_internal_stochasticity_is_refused_by_every_ensemble_entry_point(method, blobs):
    with pytest.raises(ValueError, match="only defined for"):
        run_rsc_repeats(method, blobs, {}, 2)
    with pytest.raises(ValueError, match="only defined for"):
        run_monti_repeats(method, blobs, {}, 2, 0.5)


@pytest.mark.parametrize("n_repeats", [0, -3])
def test_zero_or_negative_repeats_are_refused(blobs, n_repeats):
    with pytest.raises(ValueError, match="n_repeats must be >= 1"):
        run_rsc_repeats("kmeans", blobs, _PARAMS["kmeans"], n_repeats)
    with pytest.raises(ValueError, match="n_repeats must be >= 1"):
        run_monti_repeats("kmeans", blobs, _PARAMS["kmeans"], n_repeats, 0.5)


# --- run_monti_repeats ----------------------------------------------------------------------------


@settings(max_examples=8)
@given(fraction=st.floats(0.55, 0.95), n_repeats=st.integers(8, 14), base_seed=st.integers(0, 50))
def test_monti_matrix_is_either_a_valid_consensus_or_the_documented_error(blobs, fraction, n_repeats, base_seed):
    try:
        co = run_monti_repeats("kmeans", blobs, _PARAMS["kmeans"], n_repeats, fraction, base_seed=base_seed)
    except ValueError as error:
        assert "never jointly sampled" in str(error)  # mai un NaN o uno 0 silenzioso
        return
    assert np.isfinite(co).all()
    assert ((co >= 0) & (co <= 1)).all()
    np.testing.assert_array_equal(co, co.T)
    np.testing.assert_array_equal(np.diag(co), np.ones(len(blobs)))


def test_monti_reports_the_pairs_that_were_never_sampled_together(blobs):
    with pytest.raises(ValueError, match="never jointly sampled"):
        run_monti_repeats("kmeans", blobs, _PARAMS["kmeans"], 1, 0.5)  # un solo sorteggio non copre tutte le coppie


@pytest.mark.parametrize("fraction", [0.0, 1.0, -0.2, 1.5, float("nan")])
def test_monti_rejects_a_subsample_fraction_outside_the_open_unit_interval(blobs, fraction):
    with pytest.raises(ValueError, match="subsample_fraction"):
        run_monti_repeats("kmeans", blobs, _PARAMS["kmeans"], 3, fraction)


# --- subsampling_stability_index ------------------------------------------------------------------


@settings(max_examples=8)
@given(fraction=st.floats(0.2, 0.98), base_seed=st.integers(0, 50))
def test_subsampling_stability_is_a_finite_ari_at_most_one(blobs, fraction, base_seed):
    value = subsampling_stability_index("kmeans", blobs, {**_PARAMS["kmeans"], "random_state": 0}, fraction, base_seed=base_seed)
    assert isinstance(value, float) and np.isfinite(value) and value <= 1.0 + 1e-12


@pytest.mark.parametrize("fraction", [0.01, 0.04])  # 18 soggetti: sottocampioni di 0 e 1 punto
def test_subsampling_stability_refuses_a_subsample_of_fewer_than_two_points(blobs, fraction):
    with pytest.raises(ValueError, match="too small"):
        subsampling_stability_index("kmeans", blobs, {**_PARAMS["kmeans"], "random_state": 0}, fraction)


def test_subsampling_stability_of_well_separated_blobs_is_perfect_and_reproducible(blobs):
    params = {**_PARAMS["kmeans"], "random_state": 0}
    first = subsampling_stability_index("kmeans", blobs, params, 0.7, base_seed=2)
    assert first == pytest.approx(1.0)
    assert first == subsampling_stability_index("kmeans", blobs, params, 0.7, base_seed=2)


@pytest.mark.parametrize("fraction", [0.0, 1.0, 2.0])
def test_subsampling_stability_rejects_a_fraction_outside_the_open_unit_interval(blobs, fraction):
    with pytest.raises(ValueError, match="subsample_fraction"):
        subsampling_stability_index("kmeans", blobs, _PARAMS["kmeans"], fraction)


def test_subsampling_stability_rejects_an_unregistered_method(blobs):
    with pytest.raises(ValueError, match="unknown clustering method"):
        subsampling_stability_index("dbscan", blobs, {}, 0.5)


# --- compute_monti_stability ----------------------------------------------------------------------


@st.composite
def _symmetric_unit_matrix(draw, min_n: int = 2, max_n: int = 12):
    n = draw(st.integers(min_n, max_n))
    values = draw(st.lists(st.floats(0, 1), min_size=n * n, max_size=n * n))
    upper = np.triu(np.array(values).reshape(n, n), 1)
    return upper + upper.T + np.eye(n)


@given(_symmetric_unit_matrix(), st.integers(0, 10_000))
def test_stability_is_a_share_independent_of_the_order_of_the_subjects(matrix, seed):
    score = compute_monti_stability(matrix)
    assert 0.0 <= score <= 1.0
    order = np.random.default_rng(seed).permutation(len(matrix))
    assert compute_monti_stability(matrix[np.ix_(order, order)]) == pytest.approx(score)


@given(_symmetric_unit_matrix())
def test_a_wider_ambiguous_band_can_only_lower_the_stability(matrix):
    assert compute_monti_stability(matrix, (0.05, 0.95)) <= compute_monti_stability(matrix, (0.1, 0.9)) + 1e-12


@pytest.mark.parametrize("n", [2, 5, 9])
def test_stability_is_one_for_a_crisp_consensus_and_zero_for_a_fully_ambiguous_one(n):
    crisp = np.kron(np.eye(3), np.ones((n, n)))
    assert compute_monti_stability(crisp) == 1.0
    assert compute_monti_stability(np.full((n, n), 0.5)) == 0.0


def test_stability_of_a_single_subject_is_refused():
    with pytest.raises(ValueError, match="at least 2 subjects"):
        compute_monti_stability(np.ones((1, 1)))


# --- compute_rsc_eigengap -------------------------------------------------------------------------


@st.composite
def _block_cooccurrence(draw):
    sizes = draw(st.lists(st.integers(2, 5), min_size=2, max_size=4))
    return sizes, _blocks(sizes)


def _blocks(sizes: list[int]) -> np.ndarray:
    n = sum(sizes)
    matrix = np.zeros((n, n))
    start = 0
    for size in sizes:
        matrix[start : start + size, start : start + size] = 1.0
        start += size
    return matrix


@given(_block_cooccurrence(), st.integers(0, 10_000))
def test_the_eigengap_peaks_at_the_number_of_blocks_and_is_permutation_invariant(blocks, seed):
    sizes, matrix = blocks
    b = len(sizes)
    gaps = {k: compute_rsc_eigengap(matrix, k) for k in range(1, matrix.shape[0])}
    assert all(gap >= -1e-9 for gap in gaps.values())  # autovalori ordinati: il salto non è mai negativo
    assert max(gaps, key=gaps.get) == b
    assert gaps[b] > 0.1
    assert all(gaps[k] < 1e-8 for k in range(1, b))
    order = np.random.default_rng(seed).permutation(matrix.shape[0])
    assert compute_rsc_eigengap(matrix[np.ix_(order, order)], b) == pytest.approx(gaps[b], abs=1e-9)


@pytest.mark.parametrize("k", [-1, 0, 6, 7])
def test_eigengap_rejects_k_outside_one_to_n_minus_one(k):
    with pytest.raises(ValueError, match=r"k must be in \[1, n_samples\)"):
        compute_rsc_eigengap(np.ones((6, 6)), k)
