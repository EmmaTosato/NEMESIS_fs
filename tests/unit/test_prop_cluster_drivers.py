"""Test a proprietà di src/analysis/cluster_drivers.py: la regressione logistica cluster-contro-resto
si comporta come una regressione deve (inversioni, invarianze, NaN), oppure solleva un errore chiaro."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.analysis.cluster_drivers import MIN_EVENTS_PER_TERM, cluster_vs_rest_regression

# Gli unici rifiuti ammessi su dati casuali ben condizionati: sono documentati, mai una regressione che sembra
# buona e non lo è. Qualunque altro ValueError fa fallire il test.
_DOCUMENTED_REFUSALS = ("separation", "collinear", "rarer class", "single class")


def _dataset(seed: int, n: int = 240) -> tuple[pd.DataFrame, np.ndarray]:
    """Due numeriche e una categorica a 3 livelli; l'esito dipende debolmente dalle prime due, quindi
    nessuna separazione e nessun termine collineare."""
    rng = np.random.default_rng(seed)
    features = pd.DataFrame({
        "age": rng.normal(60, 10, n), "nihss": rng.normal(8, 4, n),
        "dataset": rng.choice(["A", "B", "C"], size=n, p=[0.5, 0.3, 0.2]),
    })
    logit = 0.4 * (features["age"] - 60) / 10 - 0.3 * (features["nihss"] - 8) / 4
    in_cluster = rng.random(n) < 1 / (1 + np.exp(-logit))
    return features, in_cluster


def _fit(features, in_cluster, **kwargs):
    kwargs.setdefault("numeric", ["age", "nihss"])
    kwargs.setdefault("categorical", ["dataset"])
    kwargs.setdefault("references", {"dataset": "A"})
    try:
        return cluster_vs_rest_regression(features, in_cluster, **kwargs)
    except ValueError as error:
        assume(any(text in str(error) for text in _DOCUMENTED_REFUSALS))  # scarta l'esempio, non nasconde altri errori
        raise


_seeds = st.integers(0, 5000)


@settings(max_examples=25)
@given(_seeds)
def test_the_result_is_internally_consistent(seed):
    features, in_cluster = _dataset(seed)
    result = _fit(features, in_cluster)
    table = result.coefficients

    assert result.n_used + result.n_dropped_missing == len(features)
    assert result.n_in_cluster == int(in_cluster.sum())
    assert (table["ci_low"] <= table["odds_ratio"]).all() and (table["odds_ratio"] <= table["ci_high"]).all()
    assert (table["odds_ratio"] > 0).all() and (table["ci_low"] > 0).all()
    assert table["p_value"].between(0, 1).all()
    assert (table["vif"] >= 1 - 1e-9).all()  # un VIF sotto 1 è impossibile
    assert 0.0 <= result.auc <= 1.0
    assert -1e-9 <= result.pseudo_r2 < 1.0
    assert result.events_per_term >= MIN_EVENTS_PER_TERM
    np.testing.assert_allclose(np.log(table["ci_high"] / table["odds_ratio"]), np.log(table["odds_ratio"] / table["ci_low"]), atol=1e-9)  # IC simmetrico in log


@settings(max_examples=20)
@given(_seeds, st.integers(0, 10_000))
def test_the_row_order_of_the_subjects_does_not_matter(seed, order_seed):
    features, in_cluster = _dataset(seed)
    order = np.random.default_rng(order_seed).permutation(len(features))
    straight = _fit(features, in_cluster)
    shuffled = _fit(features.iloc[order].reset_index(drop=True), in_cluster[order])
    np.testing.assert_allclose(shuffled.coefficients.to_numpy(), straight.coefficients.to_numpy(), rtol=1e-6, atol=1e-8)
    assert shuffled.auc == pytest.approx(straight.auc)
    assert shuffled.pseudo_r2 == pytest.approx(straight.pseudo_r2)


@settings(max_examples=20)
@given(_seeds)
def test_taking_the_complement_of_the_cluster_inverts_every_odds_ratio(seed):
    features, in_cluster = _dataset(seed)
    forward, backward = _fit(features, in_cluster), _fit(features, ~in_cluster)
    np.testing.assert_allclose(forward.coefficients["odds_ratio"] * backward.coefficients["odds_ratio"], 1.0, rtol=1e-6)
    np.testing.assert_allclose(forward.coefficients["p_value"], backward.coefficients["p_value"], rtol=1e-5, atol=1e-10)
    assert forward.pseudo_r2 == pytest.approx(backward.pseudo_r2)
    assert forward.auc == pytest.approx(backward.auc)  # l'AUC del complemento con le probabilità complementari è la stessa


@settings(max_examples=20)
@given(_seeds, st.floats(0.01, 100), st.floats(-1000, 1000))
def test_numeric_odds_are_invariant_to_scale_and_offset_and_invert_with_the_sign(seed, scale, offset):
    features, in_cluster = _dataset(seed)
    base = _fit(features, in_cluster).coefficients
    rescaled = features.assign(age=features["age"] * scale + offset)
    np.testing.assert_allclose(_fit(rescaled, in_cluster).coefficients.loc["age", "odds_ratio"], base.loc["age", "odds_ratio"], rtol=1e-5)
    flipped = features.assign(age=-features["age"])
    np.testing.assert_allclose(_fit(flipped, in_cluster).coefficients.loc["age", "odds_ratio"], 1 / base.loc["age", "odds_ratio"], rtol=1e-5)


@settings(max_examples=20)
@given(_seeds, st.permutations(["A", "B", "C"]))
def test_renaming_the_categorical_levels_only_renames_the_terms(seed, new_names):
    features, in_cluster = _dataset(seed)
    mapping = dict(zip(["A", "B", "C"], new_names))
    straight = _fit(features, in_cluster)
    renamed = _fit(features.assign(dataset=features["dataset"].map(mapping)), in_cluster, references={"dataset": mapping["A"]})
    # stesso modello, termini rinominati: "dataset: B (ref. A)" -> "dataset: <nuovo B> (ref. <nuovo A>)"
    expected_terms = [
        term if not term.startswith("dataset: ") else f"dataset: {mapping[term.split(': ')[1].split(' ')[0]]} (ref. {mapping['A']})"
        for term in straight.coefficients.index
    ]
    renamed_by_term = renamed.coefficients.reindex(expected_terms)
    np.testing.assert_allclose(renamed_by_term["odds_ratio"].to_numpy(), straight.coefficients["odds_ratio"].to_numpy(), rtol=1e-6)


@settings(max_examples=20)
@given(_seeds)
def test_two_level_categorical_odds_invert_when_the_reference_level_swaps(seed):
    features, in_cluster = _dataset(seed)
    features = features.assign(dataset=np.where(features["dataset"] == "A", "A", "B"))
    vs_a = _fit(features, in_cluster, numeric=["age"], references={"dataset": "A"}).coefficients
    vs_b = _fit(features, in_cluster, numeric=["age"], references={"dataset": "B"}).coefficients
    np.testing.assert_allclose(vs_a.loc["dataset: B (ref. A)", "odds_ratio"] * vs_b.loc["dataset: A (ref. B)", "odds_ratio"], 1.0, rtol=1e-6)
    np.testing.assert_allclose(vs_a.loc["age", "odds_ratio"], vs_b.loc["age", "odds_ratio"], rtol=1e-6)


@settings(max_examples=20)
@given(_seeds, st.integers(1, 12), st.sampled_from(["age", "nihss", "dataset"]))
def test_missing_values_are_dropped_counted_and_equal_to_removing_those_rows(seed, n_missing, column):
    features, in_cluster = _dataset(seed, n=240)
    holes = np.random.default_rng(seed + 1).choice(len(features), size=n_missing, replace=False)
    with_nan = features.copy()
    with_nan.loc[holes, column] = np.nan
    result = _fit(with_nan, in_cluster)
    assert result.n_dropped_missing == n_missing
    assert result.n_used == len(features) - n_missing
    kept = np.setdiff1d(np.arange(len(features)), holes)
    reference = _fit(features.iloc[kept].reset_index(drop=True), in_cluster[kept])
    pd.testing.assert_frame_equal(result.coefficients, reference.coefficients)
    assert result.n_in_cluster == int(in_cluster[kept].sum())  # n_in_cluster conta solo chi è stato usato


def test_the_input_features_are_never_modified():
    features, in_cluster = _dataset(3)
    features.loc[0, "age"] = np.nan
    before = features.copy(deep=True)
    _fit(features, in_cluster)
    pd.testing.assert_frame_equal(features, before)


@pytest.mark.parametrize("n_events", [0, 1, 5, 9])
def test_too_few_events_per_term_is_refused_whatever_the_cohort_size(n_events):
    features, _ = _dataset(0, n=400)
    in_cluster = np.zeros(400, dtype=bool)
    in_cluster[:n_events] = True
    expected = "single class" if n_events == 0 else "rarer class"
    with pytest.raises(ValueError, match=expected):
        cluster_vs_rest_regression(features, in_cluster, numeric=["age"], categorical=[])


def test_every_subject_with_a_missing_value_leaves_a_single_class_error_not_a_crash():
    features, in_cluster = _dataset(0, n=60)
    features["age"] = np.where(in_cluster, np.nan, features["age"])  # tutti i soggetti del cluster hanno età mancante
    with pytest.raises(ValueError, match="single class"):
        cluster_vs_rest_regression(features, in_cluster, numeric=["age"], categorical=[])


@given(st.integers(1, 80))
def test_a_length_mismatch_is_refused(n_outcome):
    features, in_cluster = _dataset(0, n=60)
    assume(n_outcome != 60)
    outcome = np.resize(in_cluster, n_outcome)
    with pytest.raises(ValueError, match="rows but in_cluster has"):
        cluster_vs_rest_regression(features, outcome, numeric=["age"], categorical=[])


@pytest.mark.parametrize("kwargs, match", [
    ({"numeric": ["age", "ghost"], "categorical": []}, "columns not in features"),
    ({"numeric": [], "categorical": []}, "no variables to fit"),
    ({"numeric": [], "categorical": ["dataset"], "references": {"dataset": "Z"}}, "reference level"),
])
def test_invalid_variable_specifications_raise_a_clear_error(kwargs, match):
    features, in_cluster = _dataset(0)
    with pytest.raises(ValueError, match=match):
        cluster_vs_rest_regression(features, in_cluster, **kwargs)
