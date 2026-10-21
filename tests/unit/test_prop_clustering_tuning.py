"""Test a proprieta' / parametrici delle parti pure e di configurazione di src/analysis/clustering_tuning.py:
guardie di geometria euclidea, combinazioni ward non valide, `representative_values`, regola 1-SE del gap,
righe di suggerimento del consenso, validazione degli argomenti dello sweep e la sua struttura (righe =
prodotto cartesiano meno le combinazioni scartate). Gli stimatori costosi sono gia' coperti da
test_clustering_tuning.py.
"""

from __future__ import annotations

import itertools
import logging
import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import clustering_tuning as CT
from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.consensus_clustering import CONSENSUS_ELIGIBLE_METHODS, K_PARAM_NAME
from tests.factories.matrices import gaussian_blobs

_X, _TRUE = gaussian_blobs(n_per_blob=10, seed=3)
_GENERIC = ["silhouette", "calinski_harabasz", "davies_bouldin"]


# ---- registri: coerenza interna ----------------------------------------------------------------------------------------------------------


def test_metric_columns_are_declared_for_exactly_the_registered_clustering_methods():
    assert set(CT.METHOD_METRIC_COLUMNS) == set(CLUSTERING_METHODS)


@pytest.mark.parametrize("method", sorted(CT.METHOD_METRIC_COLUMNS))
def test_every_method_reports_the_three_generic_scores_without_repeated_columns(method):
    columns = CT.METHOD_METRIC_COLUMNS[method]
    assert columns[:3] == _GENERIC
    assert len(columns) == len(set(columns))


def test_the_extra_metric_evaluators_only_cover_methods_with_extra_columns():
    for method in CT._EXTRA_METRICS_EVALUATORS:
        assert method in CLUSTERING_METHODS
        assert len(CT.METHOD_METRIC_COLUMNS[method]) > 3  # un evaluator "extra" senza colonne extra non avrebbe senso


def test_stability_and_consensus_registries_agree_on_their_eligible_methods():
    assert set(CT.STABILITY_TARGET_PARAM) == set(CT.STABILITY_NUISANCE_PARAM) == set(CT.STABILITY_METRIC_NAME) == set(CT._STABILITY_ESTIMATORS)
    assert CT.STABILITY_ELIGIBLE_METHODS == set(CT.STABILITY_TARGET_PARAM)
    assert CT.STABILITY_ELIGIBLE_METHODS <= CONSENSUS_ELIGIBLE_METHODS  # stability e' un sottoinsieme del consenso
    for method in CT.STABILITY_ELIGIBLE_METHODS:
        assert CT.STABILITY_TARGET_PARAM[method] == K_PARAM_NAME[method]  # lo stesso "k" in entrambi


def test_standalone_diagnostics_are_registered_methods():
    assert CT.STANDALONE_DIAGNOSTIC_METHODS <= set(CLUSTERING_METHODS)


# ---- require_euclidean_compatible -------------------------------------------------------------------------------------------------------------


_SAFE_AFFINITY = [None, "nearest_neighbors", "rbf"]
_SAFE_METRIC = [None, "euclidean"]


@pytest.mark.parametrize("affinity", _SAFE_AFFINITY)
@pytest.mark.parametrize("metric", _SAFE_METRIC)
def test_euclidean_safe_values_are_accepted_in_every_combination(affinity, metric):
    CT.require_euclidean_compatible({"affinity": affinity, "metric": metric})
    CT.require_euclidean_compatible({k: v for k, v in (("affinity", affinity), ("metric", metric)) if v is not None})


def test_require_euclidean_compatible_accepts_none_and_empty():
    CT.require_euclidean_compatible(None)
    CT.require_euclidean_compatible({})
    CT.require_euclidean_compatible({"n_clusters": 3, "linkage": "average"})  # chiavi irrilevanti ignorate


@settings(max_examples=100)
@given(value=st.text(max_size=12).filter(lambda s: s not in {"nearest_neighbors", "rbf", "euclidean"}))
def test_any_other_affinity_or_metric_string_is_refused_naming_the_value(value):
    with pytest.raises(ValueError, match="Euclidean") as e1:
        CT.require_euclidean_compatible({"affinity": value})
    assert repr(value) in str(e1.value)
    with pytest.raises(ValueError, match="Euclidean") as e2:
        CT.require_euclidean_compatible({"metric": value})
    assert repr(value) in str(e2.value)


@pytest.mark.parametrize(
    "key, value",
    [("affinity", "euclidean"), ("metric", "rbf"), ("metric", "l2"), ("affinity", "precomputed"), ("metric", "Euclidean"), ("metric", ""),
     ("affinity", 0), ("metric", False)]
    + [("metric", m) for m in ("cosine", "manhattan", "dice", "jaccard", "precomputed", "nearest_neighbors")]
    + [("affinity", a) for a in ("cosine", "poly", "sigmoid", "precomputed_nearest_neighbors")],
)
def test_the_allow_lists_are_per_key_and_exact(key, value):
    with pytest.raises(ValueError):
        CT.require_euclidean_compatible({key: value})


@pytest.mark.parametrize("params", [{"metric": ["euclidean"]}, {"affinity": ["rbf"]}, {"metric": {"a": 1}}])
def test_an_unhashable_metric_or_affinity_is_a_valueerror(params):
    with pytest.raises(ValueError):
        CT.require_euclidean_compatible(params)


@pytest.mark.parametrize("params", [{"metric": ["euclidean"]}, {"linkage": "ward", "metric": {"a": 1}}])
def test_an_unhashable_metric_in_the_ward_check_is_a_valueerror(params):
    with pytest.raises(ValueError):
        CT.is_invalid_ward_metric_combo(params)


# ---- is_invalid_ward_metric_combo: tabella di verita' --------------------------------------------------------------------------------------------


@settings(max_examples=200)
@given(linkage=st.one_of(st.sampled_from(["ward", "average", "complete", "single"]), st.text(max_size=5)),
       metric=st.one_of(st.sampled_from(["euclidean", "l2", "cosine", "manhattan", "dice", "jaccard"]), st.text(max_size=5)))
def test_ward_with_a_non_euclidean_metric_is_the_only_invalid_combination(linkage, metric):
    assert CT.is_invalid_ward_metric_combo({"linkage": linkage, "metric": metric}) is (linkage == "ward" and metric not in {"euclidean", "l2"})


@pytest.mark.parametrize(
    "params, expected",
    [({}, False), ({"linkage": "ward"}, False), ({"metric": "cosine"}, True), ({"metric": "euclidean"}, False),
     ({"linkage": "average", "metric": "cosine"}, False), ({"linkage": "ward", "metric": "l2"}, False), ({"linkage": "ward", "metric": "dice"}, True),
     ({"metric": None}, True)],
)
def test_ward_defaults_are_ward_and_euclidean(params, expected):
    """Default linkage 'ward' e metric 'euclidean' (quelli di sklearn): una chiave assente non e' 'metrica non euclidea'."""
    assert CT.is_invalid_ward_metric_combo(params) is expected


# ---- representative_values ---------------------------------------------------------------------------------------------------------------------------


@settings(max_examples=150)
@given(values=st.lists(st.integers(-1000, 1000), min_size=1, max_size=30))
def test_representative_values_are_min_median_max_sorted_and_distinct(values):
    out = CT.representative_values(values)
    ordered = sorted(values)
    assert out == sorted(set(out)) and 1 <= len(out) <= 3
    assert set(out) <= set(values)
    assert out[0] == ordered[0] and out[-1] == ordered[-1]
    assert ordered[len(ordered) // 2] in out


@settings(max_examples=60)
@given(values=st.lists(st.integers(0, 50), min_size=1, max_size=15), seed=st.integers(0, 1000))
def test_representative_values_ignore_order_and_duplicates_and_do_not_mutate_the_input(values, seed):
    shuffled = list(values)
    np.random.default_rng(seed).shuffle(shuffled)
    snapshot = list(shuffled)
    assert CT.representative_values(shuffled) == CT.representative_values(values)
    assert shuffled == snapshot


def test_representative_values_of_nothing_is_a_valueerror():
    with pytest.raises(ValueError, match="at least one value"):
        CT.representative_values([])


# ---- gap_statistic_suggested_k --------------------------------------------------------------------------------------------------------------------------


def _gap_frame(ks, gaps, sks):
    return pd.DataFrame({"n_clusters": ks, "gap": gaps, "gap_sk": sks})


def _oracle(frame):
    ordered = frame.sort_values("n_clusters").reset_index(drop=True)
    for i in range(len(ordered) - 1):
        if ordered.loc[i, "gap"] >= ordered.loc[i + 1, "gap"] - ordered.loc[i + 1, "gap_sk"]:
            return int(ordered.loc[i, "n_clusters"])
    return None


@settings(max_examples=200)
@given(
    ks=st.lists(st.integers(1, 30), min_size=1, max_size=8, unique=True),
    data=st.data(),
)
def test_the_one_se_rule_matches_its_definition_and_never_picks_the_last_k(ks, data):
    gaps = [data.draw(st.floats(-2, 2, allow_nan=False)) for _ in ks]
    sks = [data.draw(st.floats(0, 1, allow_nan=False)) for _ in ks]
    frame = _gap_frame(ks, gaps, sks)
    out = CT.gap_statistic_suggested_k(frame)
    assert out == _oracle(frame)
    assert out is None or (out in ks and out != max(ks))  # l'ultimo k non ha un successore con cui confrontarsi


@settings(max_examples=60)
@given(ks=st.lists(st.integers(1, 30), min_size=2, max_size=8, unique=True), seed=st.integers(0, 10**6))
def test_the_row_order_of_the_gap_table_does_not_change_the_answer(ks, seed):
    rng = np.random.default_rng(seed)
    frame = _gap_frame(ks, rng.normal(size=len(ks)), rng.uniform(0, 1, size=len(ks)))
    shuffled = frame.sample(frac=1.0, random_state=seed)
    assert CT.gap_statistic_suggested_k(shuffled) == CT.gap_statistic_suggested_k(frame)


def test_the_gap_rule_with_an_empty_table_is_none_not_an_error():
    assert CT.gap_statistic_suggested_k(_gap_frame([], [], [])) is None


# ---- consensus_suggestion_lines ----------------------------------------------------------------------------------------------------------------------------


@settings(max_examples=80)
@given(method=st.sampled_from(sorted(CONSENSUS_ELIGIBLE_METHODS)),
       scores=st.lists(st.floats(0, 1, allow_nan=False), min_size=2, max_size=6, unique=True),
       with_rsc=st.booleans(), with_monti=st.booleans())
def test_each_suggestion_names_the_k_with_the_highest_score_of_its_own_column(method, scores, with_rsc, with_monti):
    k_param = K_PARAM_NAME[method]
    ks = list(range(2, 2 + len(scores)))
    frame = pd.DataFrame({k_param: ks})
    if with_rsc:
        frame["rsc_eigengap"] = scores
    if with_monti:
        frame["monti_stability"] = scores[::-1]
    lines = CT.consensus_suggestion_lines(frame, method)
    assert len(lines) == int(with_rsc) + int(with_monti)
    best = ks[int(np.argmax(scores))]
    best_reversed = ks[int(np.argmax(scores[::-1]))]
    expected = ([f"RSC suggests {k_param}={best} (largest eigengap on the co-occurrence matrix)"] if with_rsc else []) + \
               ([f"Monti suggests {k_param}={best_reversed} (highest 1-PAC stability score)"] if with_monti else [])
    assert lines == expected


# ---- run_clustering_tuning_sweep: validazione degli argomenti -------------------------------------------------------------------------------------------------


@settings(max_examples=60)
@given(method=st.text(max_size=10).filter(lambda m: m not in CLUSTERING_METHODS))
def test_an_unknown_clustering_method_is_a_valueerror_listing_the_known_ones(method):
    with pytest.raises(ValueError, match="unknown clustering method") as excinfo:
        CT.run_clustering_tuning_sweep(method, _X, {}, {"n_clusters": [2]})
    assert all(known in str(excinfo.value) for known in CLUSTERING_METHODS)


@pytest.mark.parametrize("method", sorted(set(CLUSTERING_METHODS) - CONSENSUS_ELIGIBLE_METHODS))
@pytest.mark.parametrize("config", [{"rsc": {"n_repeats": 2}}, {}, {"monti": {"n_repeats": 2, "subsample_fraction": 0.5}}])
def test_consensus_config_for_an_ineligible_method_is_refused_before_any_fit(method, config):
    """Anche un blocco vuoto ({}): 'dato' e' diverso da 'None', il metodo non lo supporta."""
    with pytest.raises(ValueError, match="only defined for"):
        CT.run_clustering_tuning_sweep(method, _X, {}, {"n_clusters": [2]}, consensus_config=config)


def test_the_spectral_affinity_aware_sweep_requires_affinity_in_the_grid():
    for grid in ({}, {"n_clusters": [2, 3]}, {"gamma": [0.1]}):
        with pytest.raises(ValueError, match="requires 'affinity'"):
            CT.run_spectral_affinity_aware_sweep(_X, {"random_state": 0}, grid)


# ---- struttura dello sweep ------------------------------------------------------------------------------------------------------------------------------------


@settings(max_examples=12)
@given(ks=st.lists(st.integers(2, 5), min_size=1, max_size=3, unique=True), n_inits=st.lists(st.integers(1, 3), min_size=1, max_size=2, unique=True))
def test_kmeans_sweep_has_one_row_per_combination_in_order_with_its_declared_columns(ks, n_inits):
    grid = {"n_clusters": ks, "n_init": n_inits}
    results, labels = CT.run_clustering_tuning_sweep("kmeans", _X, {"random_state": 0}, grid)
    combos = list(itertools.product(*grid.values()))
    assert [tuple(r) for r in results[list(grid)].itertuples(index=False)] == combos
    assert list(labels) == combos
    assert set(CT.METHOD_METRIC_COLUMNS["kmeans"]) | {"noise_fraction"} <= set(results.columns)
    assert list(results.columns)[: len(grid)] == list(grid)  # prima le chiavi spazzolate
    for combo, lab in labels.items():
        assert lab.shape == (len(_X),) and len(np.unique(lab)) == combo[0]
    assert (results["noise_fraction"] == 0.0).all()


@settings(max_examples=10)
@given(
    linkages=st.lists(st.sampled_from(["ward", "average", "complete"]), min_size=1, max_size=3, unique=True),
    metrics=st.lists(st.sampled_from(["euclidean", "cosine", "manhattan"]), min_size=1, max_size=3, unique=True),
)
def test_agglomerative_sweep_keeps_exactly_the_valid_ward_combinations(linkages, metrics, caplog):
    grid = {"linkage": linkages, "metric": metrics}
    valid = [(lk, m) for lk, m in itertools.product(linkages, metrics) if not (lk == "ward" and m != "euclidean")]
    if not valid:
        return  # tutta la griglia scartata: caso separato (test_a_grid_whose_every_combination_is_invalid...)
    caplog.clear()  # caplog e' per-test, non per-esempio hypothesis
    with caplog.at_level(logging.WARNING):
        results, labels = CT.run_clustering_tuning_sweep("agglomerative", _X, {"n_clusters": 3}, grid)
    assert [tuple(r) for r in results[["linkage", "metric"]].itertuples(index=False)] == valid
    assert list(labels) == valid
    assert caplog.text.count("skipping invalid combination") == len(linkages) * len(metrics) - len(valid)
    assert not ((results["linkage"] == "ward") & (results["metric"] != "euclidean")).any()
    # euclideo: CH/DB definiti; altrimenti NaN esplicito (non zero, non assenti)
    non_euclid = results[results["metric"] != "euclidean"]
    assert non_euclid[["calinski_harabasz", "davies_bouldin"]].isna().all().all()
    assert results.loc[results["metric"] == "euclidean", ["calinski_harabasz", "davies_bouldin"]].notna().all().all()


def test_a_grid_whose_every_combination_is_invalid_is_an_error_not_an_empty_sweep():
    with pytest.raises(ValueError):
        CT.run_clustering_tuning_sweep("agglomerative", _X, {"n_clusters": 3}, {"linkage": ["ward"], "metric": ["cosine"]})


# ---- metriche pure: invarianze --------------------------------------------------------------------------------------------------------------------------------


@settings(max_examples=40)
@given(permutation=st.permutations([0, 1, 2]), scale=st.floats(0.1, 20, allow_nan=False), shift=st.floats(-50, 50, allow_nan=False))
def test_dunn_index_ignores_label_names_and_is_invariant_to_scale_and_translation(permutation, scale, shift):
    base = CT.dunn_index(_X, _TRUE)
    relabeled = np.array(permutation)[_TRUE]
    assert CT.dunn_index(_X, relabeled) == pytest.approx(base)
    assert CT.dunn_index(_X * scale + shift, _TRUE) == pytest.approx(base, rel=1e-6)
    assert base > 1.0  # blob ben separati: distanza minima fra cluster > diametro massimo


@settings(max_examples=40)
@given(noise_idx=st.lists(st.integers(0, len(_X) - 1), max_size=10, unique=True))
def test_noise_points_are_ignored_by_dunn_and_reported_by_noise_fraction(noise_idx):
    labels = _TRUE.copy()
    labels[noise_idx] = -1
    surviving = [c for c in range(3) if (labels == c).sum() >= 2]
    if len(surviving) < 2 or len(noise_idx) > len(_X) - 8:
        return
    kept = labels != -1
    assert CT.dunn_index(_X, labels) == pytest.approx(CT.dunn_index(_X[kept], labels[kept]))
    metrics = CT.compute_clustering_metrics(_X, labels)
    assert metrics["noise_fraction"] == pytest.approx(len(noise_idx) / len(_X))
    reference = CT.compute_clustering_metrics(_X[kept], labels[kept])
    assert metrics["silhouette"] == pytest.approx(reference["silhouette"])


@settings(max_examples=30)
@given(permutation=st.permutations([0, 1, 2]))
def test_generic_metrics_do_not_depend_on_the_label_names(permutation):
    base = CT.compute_clustering_metrics(_X, _TRUE)
    other = CT.compute_clustering_metrics(_X, np.array(permutation)[_TRUE])
    assert other == pytest.approx(base)
    assert all(math.isfinite(base[k]) for k in _GENERIC) and base["noise_fraction"] == 0.0


@pytest.mark.parametrize("labels", [np.zeros(30, dtype=int), np.full(30, -1), np.arange(30)])
def test_degenerate_labelings_yield_nan_scores_with_the_noise_fraction_still_reported(labels, caplog):
    with caplog.at_level(logging.WARNING):
        metrics = CT.compute_clustering_metrics(_X, labels)
    assert all(math.isnan(metrics[k]) for k in _GENERIC)
    assert metrics["noise_fraction"] == float((labels == -1).mean())
    assert "degenerate" in caplog.text
