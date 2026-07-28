"""Unit tests for src/analysis/covariates.py."""

import numpy as np
import pytest

from src.analysis.covariates import (
    VolumeRegressionIncompatibleError,
    check_volume_regression_compatible,
    regress_out_covariate,
)


def test_regress_out_covariate_removes_linear_effect():
    rng = np.random.default_rng(0)
    n = 200
    covariate = rng.uniform(0, 100, size=n)
    independent_signal = rng.normal(size=(n, 2))
    embedding = np.column_stack([5.0 + 2.0 * covariate, -3.0 + 0.5 * covariate]) + independent_signal

    residual = regress_out_covariate(embedding, covariate)

    # OLS residuals are orthogonal to the design matrix by construction - the
    # linear relationship with covariate must be gone regardless of the signal shape.
    assert abs(np.corrcoef(residual[:, 0], covariate)[0, 1]) < 1e-6
    assert abs(np.corrcoef(residual[:, 1], covariate)[0, 1]) < 1e-6


def test_regress_out_covariate_shape_mismatch_raises():
    embedding = np.zeros((10, 2))
    covariate = np.zeros(9)
    with pytest.raises(ValueError, match="has 10 rows but covariate has 9 values"):
        regress_out_covariate(embedding, covariate)


def test_regress_out_covariate_zero_variance_covariate_raises():
    embedding = np.random.default_rng(0).normal(size=(10, 2))
    covariate = np.full(10, 5.0)
    with pytest.raises(ValueError, match="zero variance"):
        regress_out_covariate(embedding, covariate)


def test_check_volume_regression_compatible_raises_for_jaccard():
    with pytest.raises(ValueError, match="incompatible with metric='jaccard'"):
        check_volume_regression_compatible(True, {"metric": "jaccard"})


def test_check_volume_regression_compatible_raises_for_dice():
    with pytest.raises(ValueError, match="incompatible with metric='dice'"):
        check_volume_regression_compatible(True, {"metric": "dice"})


def test_check_volume_regression_compatible_allows_euclidean():
    check_volume_regression_compatible(True, {"metric": "euclidean"})


def test_check_volume_regression_compatible_allows_missing_metric():
    # methods with no "metric" concept at all (pca, pacmap, tsne today)
    check_volume_regression_compatible(True, {})


def test_check_volume_regression_compatible_no_check_when_flag_false():
    check_volume_regression_compatible(False, {"metric": "jaccard"})


def test_check_volume_regression_compatible_raises_dedicated_exception_type():
    # tuning.py's run_tuning_sweep catches this specific type to skip just the
    # incompatible combination - a plain ValueError would be indistinguishable
    # from any other failure and either crash the sweep or mask real bugs.
    with pytest.raises(VolumeRegressionIncompatibleError):
        check_volume_regression_compatible(True, {"metric": "jaccard"})
