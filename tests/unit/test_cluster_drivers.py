"""Unit tests for src/analysis/cluster_drivers.py."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.cluster_drivers import MIN_EVENTS_PER_TERM, cluster_vs_rest_regression


def _simulated(n: int = 6000, seed: int = 0) -> tuple[pd.DataFrame, np.ndarray]:
    """True log-odds per standard deviation: signal +1.0, protective -0.6, noise 0; dataset B adds +0.8 over A."""
    rng = np.random.default_rng(seed)
    features = pd.DataFrame(
        {
            "signal": rng.normal(size=n),
            "protective": rng.normal(size=n),
            "noise": rng.normal(size=n),
            "dataset": rng.choice(["A", "A", "B"], size=n),
        }
    )
    logit = -0.5 + 1.0 * features["signal"] - 0.6 * features["protective"] + 0.8 * (features["dataset"] == "B")
    return features, rng.random(n) < 1 / (1 + np.exp(-logit))


def test_the_regression_recovers_the_true_odds_ratios_inside_their_confidence_intervals():
    features, outcome = _simulated()

    result = cluster_vs_rest_regression(features, outcome, numeric=["signal", "protective", "noise"], categorical=["dataset"])

    table = result.coefficients
    for term, true_log_odds in [("signal", 1.0), ("protective", -0.6), ("dataset: B (rif. A)", 0.8), ("noise", 0.0)]:
        assert table.loc[term, "ci_low"] < np.exp(true_log_odds) < table.loc[term, "ci_high"], term
    assert table.loc["signal", "p_value"] < 1e-10
    assert table.loc["noise", "p_value"] > 0.01
    assert result.auc > 0.7
    assert 0 < result.pseudo_r2 < 1


def test_numeric_odds_ratios_are_per_standard_deviation_so_the_unit_of_a_column_does_not_matter():
    features, outcome = _simulated()
    rescaled = features.assign(signal=features["signal"] * 1000 + 50)

    original = cluster_vs_rest_regression(features, outcome, numeric=["signal"], categorical=[])
    changed = cluster_vs_rest_regression(rescaled, outcome, numeric=["signal"], categorical=[])

    pd.testing.assert_frame_equal(original.coefficients, changed.coefficients)


def test_the_standard_error_of_a_single_binary_term_is_woolfs_formula():
    rng = np.random.default_rng(1)
    group = rng.choice(["x", "y"], size=2000, p=[0.7, 0.3])
    outcome = rng.random(2000) < np.where(group == "y", 0.5, 0.25)
    features = pd.DataFrame({"group": group})

    result = cluster_vs_rest_regression(features, outcome, numeric=[], categorical=["group"], references={"group": "x"})

    a, b = ((group == "y") & outcome).sum(), ((group == "y") & ~outcome).sum()
    c, d = ((group == "x") & outcome).sum(), ((group == "x") & ~outcome).sum()
    woolf_se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    row = result.coefficients.loc["group: y (rif. x)"]
    assert row["odds_ratio"] == pytest.approx((a * d) / (b * c), rel=1e-4)
    assert np.log(row["ci_high"] / row["odds_ratio"]) == pytest.approx(1.959964 * woolf_se, rel=1e-4)


def test_the_default_reference_level_is_the_most_frequent_one():
    features, outcome = _simulated()

    result = cluster_vs_rest_regression(features, outcome, numeric=[], categorical=["dataset"])

    assert list(result.coefficients.index) == ["dataset: B (rif. A)"]  # A is twice as frequent as B


def test_subjects_with_a_missing_value_are_dropped_and_counted():
    features, outcome = _simulated()
    features.loc[:99, "signal"] = np.nan

    result = cluster_vs_rest_regression(features, outcome, numeric=["signal"], categorical=["dataset"])

    assert result.n_dropped_missing == 100
    assert result.n_used == len(features) - 100


def test_the_vif_flags_two_overlapping_variables():
    features, outcome = _simulated()
    features["signal_copy"] = features["signal"] + np.random.default_rng(5).normal(0, 0.3, len(features))

    result = cluster_vs_rest_regression(features, outcome, numeric=["signal", "signal_copy", "noise"], categorical=[])

    vif = result.coefficients["vif"]
    assert vif["signal"] > 5 and vif["signal_copy"] > 5
    assert vif["noise"] < 1.5


def test_collinear_terms_raise():
    features, outcome = _simulated()
    features["double"] = features["signal"] * 2

    with pytest.raises(ValueError, match="collinear"):
        cluster_vs_rest_regression(features, outcome, numeric=["signal", "double"], categorical=[])


def test_a_variable_that_separates_the_groups_perfectly_raises():
    features, _ = _simulated()
    outcome = (features["signal"] > 0).to_numpy()

    with pytest.raises(ValueError, match="separation"):
        cluster_vs_rest_regression(features, outcome, numeric=["signal"], categorical=[])


def test_too_few_subjects_in_the_rarer_class_raises():
    features, _ = _simulated(n=600)
    outcome = np.zeros(600, dtype=bool)
    outcome[: MIN_EVENTS_PER_TERM * 2 - 1] = True  # 19 events for 2 terms

    with pytest.raises(ValueError, match="per term"):
        cluster_vs_rest_regression(features, outcome, numeric=["signal", "noise"], categorical=[])


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"numeric": ["nope"], "categorical": []}, "columns not in features"),
        ({"numeric": [], "categorical": []}, "no variables"),
        ({"numeric": [], "categorical": ["dataset"], "references": {"dataset": "Z"}}, "reference level"),
    ],
)
def test_invalid_arguments_raise(kwargs, match):
    features, outcome = _simulated()

    with pytest.raises(ValueError, match=match):
        cluster_vs_rest_regression(features, outcome, **kwargs)


def test_mismatched_length_a_single_class_and_a_constant_column_raise():
    features, outcome = _simulated()

    with pytest.raises(ValueError, match="rows but in_cluster"):
        cluster_vs_rest_regression(features, outcome[:-1], numeric=["signal"], categorical=[])
    with pytest.raises(ValueError, match="single class"):
        cluster_vs_rest_regression(features, np.ones(len(features), dtype=bool), numeric=["signal"], categorical=[])
    with pytest.raises(ValueError, match="constant"):
        cluster_vs_rest_regression(features.assign(signal=1.0), outcome, numeric=["signal"], categorical=[])


def test_the_input_frame_is_not_modified():
    features, outcome = _simulated()
    before = features.copy()

    cluster_vs_rest_regression(features, outcome, numeric=["signal"], categorical=["dataset"])

    pd.testing.assert_frame_equal(features, before)
