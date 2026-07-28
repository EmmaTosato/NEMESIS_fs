"""Unit tests for src/analysis/prediction.py."""

import numpy as np
import pytest
from scipy.stats import wilcoxon

from src.analysis.prediction import (
    accuracy_r2,
    benjamini_hochberg,
    compare_lesion_fc,
    pca_variance_retained,
    permutation_test,
    ridge_loocv,
)

_RNG = np.random.default_rng(0)


def test_pca_variance_retained_shape_and_variance():
    X = _RNG.random((30, 15))
    X_pca, fitted = pca_variance_retained(X, 0.95)
    assert X_pca.shape[0] == 30
    assert fitted.explained_variance_ratio_.sum() >= 0.95
    assert X_pca.shape[1] == fitted.n_components_


def test_pca_variance_retained_invalid_ratio_raises():
    X = _RNG.random((10, 5))
    with pytest.raises(ValueError, match="variance_retained"):
        pca_variance_retained(X, 1.5)
    with pytest.raises(ValueError, match="variance_retained"):
        pca_variance_retained(X, 0.0)


def test_ridge_loocv_recovers_strong_linear_signal():
    n, p = 30, 4
    X = _RNG.standard_normal((n, p))
    true_weights = np.array([2.0, -1.5, 0.0, 1.0])
    y = X @ true_weights + 0.01 * _RNG.standard_normal(n)

    lambda_grid = np.logspace(-2, 2, 10)
    y_pred, weights = ridge_loocv(X, y, lambda_grid)

    assert y_pred.shape == (n,)
    assert weights.shape == (p,)
    assert accuracy_r2(y, y_pred) > 0.8


def test_ridge_loocv_mismatched_lengths_raises():
    X = _RNG.random((10, 3))
    y = _RNG.random(9)
    with pytest.raises(ValueError, match="must match"):
        ridge_loocv(X, y, np.logspace(-1, 1, 5))


def test_ridge_loocv_too_few_subjects_raises():
    X = _RNG.random((2, 3))
    y = _RNG.random(2)
    with pytest.raises(ValueError, match="at least 3"):
        ridge_loocv(X, y, np.logspace(-1, 1, 5))


def test_accuracy_r2_known_value():
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.0, 2.0, 3.0, 4.0])
    assert accuracy_r2(y_true, y_pred) == pytest.approx(1.0)

    y_pred_inverted = np.array([4.0, 3.0, 2.0, 1.0])
    assert accuracy_r2(y_true, y_pred_inverted) == pytest.approx(1.0)  # squared -> sign-agnostic


def test_permutation_test_detects_strong_signal():
    n, p = 20, 2
    X = _RNG.standard_normal((n, p))
    y = X @ np.array([3.0, -2.0]) + 0.01 * _RNG.standard_normal(n)
    lambda_grid = np.logspace(-2, 2, 8)

    p_value = permutation_test(X, y, lambda_grid, n_permutations=30, rng=np.random.default_rng(1))
    assert 0.0 < p_value <= 1.0
    assert p_value < 0.1


def test_permutation_test_p_value_in_valid_range_on_noise():
    n, p = 15, 3
    X = _RNG.standard_normal((n, p))
    y = _RNG.standard_normal(n)  # unrelated to X
    lambda_grid = np.logspace(-2, 2, 5)

    p_value = permutation_test(X, y, lambda_grid, n_permutations=10, rng=np.random.default_rng(2))
    assert 0.0 < p_value <= 1.0


def test_compare_lesion_fc_matches_scipy_wilcoxon():
    err_lesion = np.array([0.5, 0.3, 0.8, 0.2, 0.9, 0.4])
    err_fc = np.array([0.2, 0.35, 0.3, 0.25, 0.4, 0.1])

    statistic, p_value = compare_lesion_fc(err_lesion, err_fc)
    expected_statistic, expected_p = wilcoxon(err_lesion, err_fc, alternative="two-sided")
    assert statistic == pytest.approx(expected_statistic)
    assert p_value == pytest.approx(expected_p)


def test_compare_lesion_fc_mismatched_lengths_raises():
    with pytest.raises(ValueError, match="must match"):
        compare_lesion_fc(np.array([1.0, 2.0]), np.array([1.0]))


def test_benjamini_hochberg_matches_hand_computed_reference():
    # Reference case computed by hand (see docstring math in module review):
    # sorted p = [0.001, 0.03, 0.03, 0.04, 0.9] -> BH-corrected sorted =
    # [0.005, 0.05, 0.05, 0.05, 0.9] after the step-up monotonicity correction.
    p_values = np.array([0.03, 0.001, 0.9, 0.04, 0.03])
    expected = np.array([0.05, 0.005, 0.9, 0.05, 0.05])

    corrected = benjamini_hochberg(p_values)
    np.testing.assert_allclose(corrected, expected, atol=1e-9)


def test_benjamini_hochberg_output_is_monotonic_with_sorted_input():
    p_values = np.sort(_RNG.uniform(0, 1, 20))
    corrected = benjamini_hochberg(p_values)
    assert np.all(np.diff(corrected) >= -1e-12)
    assert np.all((corrected >= 0.0) & (corrected <= 1.0))
