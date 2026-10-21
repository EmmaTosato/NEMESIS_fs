"""Test a proprietà di src/analysis/prediction.py: Benjamini-Hochberg contro l'oracolo di scipy, r^2 di
Siegel e le sue invarianze, ridge LOOCV (equivarianza alla scala di y e alle permutazioni dei soggetti),
p-value di permutazione, Wilcoxon. Tutto su dati minuscoli: nessun test rifà la permutazione lenta."""

from __future__ import annotations

import warnings

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.stats import false_discovery_control

from src.analysis.prediction import (
    accuracy_r2,
    benjamini_hochberg,
    compare_lesion_fc,
    pca_variance_retained,
    permutation_test,
    ridge_loocv,
)

_LAMBDAS = np.array([0.1, 1.0, 10.0])
_p_values = st.lists(st.floats(0, 1), min_size=1, max_size=30)


# --- benjamini_hochberg ---------------------------------------------------------------------------


@given(_p_values)
def test_bh_matches_scipy_and_keeps_the_order_of_the_input(p_values):
    corrected = benjamini_hochberg(np.array(p_values))
    np.testing.assert_allclose(corrected, false_discovery_control(np.array(p_values), method="bh"), atol=1e-12)
    assert corrected.shape == (len(p_values),)


@given(_p_values)
def test_bh_never_lowers_a_p_value_stays_in_the_unit_interval_and_keeps_the_ranking(p_values):
    p = np.array(p_values)
    corrected = benjamini_hochberg(p)
    assert (corrected >= p - 1e-12).all() and (corrected <= 1.0).all() and (corrected >= 0).all()
    # monotonia: p_i <= p_j implica q_i <= q_j
    order = np.argsort(p, kind="stable")
    assert (np.diff(corrected[order]) >= -1e-12).all()


@given(_p_values, st.integers(0, 10_000))
def test_bh_is_equivariant_to_the_order_of_the_tests(p_values, seed):
    p = np.array(p_values)
    order = np.random.default_rng(seed).permutation(len(p))
    np.testing.assert_allclose(benjamini_hochberg(p[order]), benjamini_hochberg(p)[order], atol=1e-12)


@given(st.floats(0, 1))
def test_bh_of_a_single_test_is_the_test_itself(p):
    assert benjamini_hochberg(np.array([p]))[0] == pytest.approx(p)


def test_bh_of_no_tests_is_no_corrected_values():
    assert benjamini_hochberg(np.array([])).shape == (0,)


@given(_p_values)
def test_bh_is_the_textbook_step_up_formula(p_values):
    """q_(i) = min su j >= i di p_(j) * n / j, sui p ordinati: scritto per esteso, indipendente dal codice testato."""
    p = np.array(p_values)
    n = len(p)
    ranked = np.sort(p)
    q_ranked = [min(1.0, min(ranked[j] * n / (j + 1) for j in range(i, n))) for i in range(n)]
    np.testing.assert_allclose(np.sort(benjamini_hochberg(p)), np.sort(q_ranked), atol=1e-12)


# --- accuracy_r2 ----------------------------------------------------------------------------------


@st.composite
def _paired_scores(draw, min_size: int = 3, max_size: int = 20):
    n = draw(st.integers(min_size, max_size))
    seed = draw(st.integers(0, 10_000))
    rng = np.random.default_rng(seed)
    y = rng.normal(size=n)
    return y, 0.5 * y + rng.normal(size=n)


@given(_paired_scores())
def test_r2_is_a_symmetric_share_between_zero_and_one(pair):
    y_true, y_pred = pair
    value = accuracy_r2(y_true, y_pred)
    assert 0.0 <= value <= 1.0 + 1e-12
    assert accuracy_r2(y_pred, y_true) == pytest.approx(value)


@given(_paired_scores(), st.floats(0.01, 100), st.floats(-100, 100), st.booleans())
def test_r2_does_not_change_under_an_affine_transform_of_the_predictions_whatever_its_sign(pair, scale, offset, flip):
    """È il quadrato della correlazione, non l'R^2 di sklearn: una previsione in scala sbagliata o con segno
    invertito ha lo stesso valore (lo dice la docstring)."""
    y_true, y_pred = pair
    transformed = (-scale if flip else scale) * y_pred + offset
    assert accuracy_r2(y_true, transformed) == pytest.approx(accuracy_r2(y_true, y_pred), abs=1e-9)


@given(st.integers(3, 20), st.floats(0.1, 50), st.floats(-50, 50))
def test_r2_is_one_for_an_exact_linear_relation(n, slope, intercept):
    y = np.random.default_rng(n).normal(size=n)
    assert accuracy_r2(y, slope * y + intercept) == pytest.approx(1.0)


@pytest.mark.parametrize("constant_side", ["pred", "true"])
def test_r2_of_a_constant_vector_is_refused_not_a_silent_nan(constant_side):
    varying, constant = np.arange(6.0), np.full(6, 3.0)
    y_true, y_pred = (varying, constant) if constant_side == "pred" else (constant, varying)
    with pytest.raises(ValueError, match="constant"):
        accuracy_r2(y_true, y_pred)


# --- pca_variance_retained ------------------------------------------------------------------------


def _full_variance_ratio(X: np.ndarray) -> np.ndarray:
    from sklearn.decomposition import PCA

    return PCA().fit(X).explained_variance_ratio_


@settings(max_examples=25)
@given(st.integers(0, 10_000), st.floats(0.5, 0.99), st.floats(0.0, 0.01))
def test_pca_keeps_at_least_the_requested_variance_and_more_variance_never_means_fewer_components(seed, retained, extra):
    X = np.random.default_rng(seed).normal(size=(15, 6)) * np.array([5, 3, 2, 1, 0.5, 0.1])
    scores, fitted = pca_variance_retained(X, retained)
    assert scores.shape == (15, fitted.n_components_)
    assert fitted.explained_variance_ratio_.sum() >= retained - 1e-9
    cumulative = np.cumsum(_full_variance_ratio(X))
    m = fitted.n_components_
    assert cumulative[m - 1] >= retained - 1e-9  # basta
    assert m == 1 or cumulative[m - 2] <= retained + 1e-9  # ed è il minimo
    more_scores, more = pca_variance_retained(X, min(0.995, retained + extra))
    assert more.n_components_ >= fitted.n_components_
    assert np.allclose(scores.mean(axis=0), 0, atol=1e-9)  # le componenti sono centrate


@pytest.mark.parametrize("bad", [0.0, -0.5, 1.5, float("nan"), float("inf")])
def test_pca_rejects_a_variance_outside_the_documented_interval(bad):
    with pytest.raises(ValueError, match="variance_retained"):
        pca_variance_retained(np.random.default_rng(0).normal(size=(8, 4)), bad)


def test_pca_accepts_the_documented_upper_bound_of_one():
    scores, fitted = pca_variance_retained(np.random.default_rng(0).normal(size=(8, 4)), 1.0)
    assert scores.shape == (8, 4)
    assert fitted.explained_variance_ratio_.sum() == pytest.approx(1.0)


# --- ridge_loocv ----------------------------------------------------------------------------------


@st.composite
def _regression_data(draw):
    n = draw(st.integers(5, 8))
    p = draw(st.integers(1, 3))
    rng = np.random.default_rng(draw(st.integers(0, 10_000)))
    X = rng.normal(size=(n, p))
    return X, X @ rng.normal(size=p) + 0.3 * rng.normal(size=n)


@settings(max_examples=4)
@given(_regression_data())
def test_ridge_loocv_returns_one_finite_prediction_per_subject_and_one_weight_per_feature(data):
    X, y = data
    y_pred, weights = ridge_loocv(X, y, _LAMBDAS)
    assert y_pred.shape == (len(y),) and weights.shape == (X.shape[1],)
    assert np.isfinite(y_pred).all() and np.isfinite(weights).all()


@settings(max_examples=4)
@given(_regression_data(), st.floats(0.1, 20), st.floats(-20, 20))
def test_predictions_follow_an_affine_rescaling_of_the_scores(data, scale, offset):
    """La scelta di lambda con l'errore quadratico non dipende dalla scala di y: previsioni e r^2 si trasformano di conseguenza."""
    X, y = data
    base, _ = ridge_loocv(X, y, _LAMBDAS)
    moved, _ = ridge_loocv(X, scale * y + offset, _LAMBDAS)
    np.testing.assert_allclose(moved, scale * base + offset, rtol=1e-6, atol=1e-6)
    assert accuracy_r2(scale * y + offset, moved) == pytest.approx(accuracy_r2(y, base), abs=1e-6)


@settings(max_examples=4)
@given(_regression_data(), st.integers(0, 10_000))
def test_each_subject_is_predicted_the_same_whatever_its_position(data, seed):
    X, y = data
    order = np.random.default_rng(seed).permutation(len(y))
    base, weights = ridge_loocv(X, y, _LAMBDAS)
    permuted, permuted_weights = ridge_loocv(X[order], y[order], _LAMBDAS)
    np.testing.assert_allclose(permuted, base[order], rtol=1e-6, atol=1e-8)
    np.testing.assert_allclose(permuted_weights, weights, rtol=1e-6, atol=1e-8)


@settings(max_examples=3)
@given(st.integers(0, 10_000))
def test_a_noiseless_linear_target_is_predicted_with_r2_close_to_one(seed):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(8, 2))
    y = X @ np.array([2.0, -1.0]) + 3.0
    y_pred, _ = ridge_loocv(X, y, np.array([1e-6, 1e-3]))
    assert accuracy_r2(y, y_pred) > 0.99


@pytest.mark.parametrize("n", [0, 1, 2])
def test_ridge_loocv_refuses_fewer_than_three_subjects(n):
    with pytest.raises(ValueError, match="at least 3 subjects"):
        ridge_loocv(np.zeros((n, 2)), np.zeros(n), _LAMBDAS)


@pytest.mark.parametrize("n_rows, n_values", [(5, 4), (4, 5), (6, 3)])
def test_ridge_loocv_refuses_a_mismatch_between_subjects_and_scores(n_rows, n_values):
    with pytest.raises(ValueError, match="must match"):
        ridge_loocv(np.zeros((n_rows, 2)), np.zeros(n_values), _LAMBDAS)


# --- permutation_test -----------------------------------------------------------------------------


@settings(max_examples=3)
@given(st.integers(1, 3), st.integers(0, 10_000))
def test_the_permutation_p_value_is_on_the_grid_and_never_zero(n_permutations, seed):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(6, 2))
    y = rng.normal(size=6)
    p = permutation_test(X, y, _LAMBDAS, n_permutations, np.random.default_rng(seed))
    assert 1 / (1 + n_permutations) <= p <= 1.0  # mai 0: lo dice la docstring
    assert (p * (1 + n_permutations)) == pytest.approx(round(p * (1 + n_permutations)))  # multiplo di 1/(1+N)


def test_the_permutation_test_is_reproducible_with_the_same_generator_seed():
    rng = np.random.default_rng(1)
    X, y = rng.normal(size=(6, 2)), rng.normal(size=6)
    assert permutation_test(X, y, _LAMBDAS, 2, np.random.default_rng(7)) == permutation_test(X, y, _LAMBDAS, 2, np.random.default_rng(7))


def test_with_no_permutations_the_p_value_is_one_not_zero():
    rng = np.random.default_rng(0)
    assert permutation_test(rng.normal(size=(6, 2)), rng.normal(size=6), _LAMBDAS, 0, rng) == 1.0


# --- compare_lesion_fc ----------------------------------------------------------------------------


@given(st.integers(6, 20), st.integers(0, 10_000))
def test_wilcoxon_comparison_is_symmetric_in_the_two_models_and_a_proper_p_value(n, seed):
    rng = np.random.default_rng(seed)
    lesion, fc = rng.gamma(2.0, size=n), rng.gamma(2.0, size=n)
    assume(not np.allclose(lesion, fc))
    statistic, p = compare_lesion_fc(lesion, fc)
    swapped_statistic, swapped_p = compare_lesion_fc(fc, lesion)
    assert 0.0 <= p <= 1.0 and statistic >= 0
    assert p == pytest.approx(swapped_p) and statistic == pytest.approx(swapped_statistic)  # due code: scambiarli non cambia nulla


@pytest.mark.parametrize("n_lesion, n_fc", [(5, 6), (6, 5), (0, 3)])
def test_wilcoxon_comparison_refuses_misaligned_errors(n_lesion, n_fc):
    with pytest.raises(ValueError, match="must match"):
        compare_lesion_fc(np.ones(n_lesion), np.ones(n_fc))


def test_two_identical_error_vectors_are_reported_as_no_difference_not_as_an_error():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # scipy avvisa di una divisione 0/0 che qui è il caso previsto
        statistic, p = compare_lesion_fc(np.arange(1.0, 7.0), np.arange(1.0, 7.0))
    assert (statistic, p) == (0.0, 1.0)
