"""Test a proprietà / parametrici di src/analysis/tuning.py (`run_tuning_sweep` e i registri).

Lo sweep e' provato con `pca` (solver sklearn, deterministico e veloce): la struttura che si controlla -
prodotto cartesiano, ordine, chiavi, colonne, validazione degli argomenti - e' identica per ogni metodo.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import tuning as T
from src.analysis.reduction import REDUCTION_METHODS
from src.analysis.tuning_evaluations import CUMULATIVE_EXPLAINED_VARIANCE, TRUSTWORTHINESS

_X = np.random.default_rng(7).normal(size=(14, 6))
_BASE = {"solver": "sklearn", "standardize": False, "rotation": "none"}


def _sweep(grid: dict, base: dict | None = None):
    return T.run_tuning_sweep("pca", _X, _BASE if base is None else base, grid, None)


_AXES = st.fixed_dictionaries(
    {"n_components": st.lists(st.integers(1, 6), min_size=1, max_size=4, unique=True)},
    optional={"standardize": st.lists(st.booleans(), min_size=1, max_size=2, unique=True)},
)


# ---- struttura del risultato -----------------------------------------------------------------------------------------------------------


@settings(max_examples=40)
@given(grid=_AXES)
def test_one_row_per_combination_in_cartesian_product_order(grid):
    results, embeddings = _sweep(grid)
    combos = list(itertools.product(*grid.values()))
    assert len(results) == len(combos) == math.prod(len(v) for v in grid.values())
    assert list(results.columns) == [*grid, CUMULATIVE_EXPLAINED_VARIANCE]  # chiavi nell'ordine della griglia + la colonna dello score
    assert [tuple(row) for row in results[list(grid)].itertuples(index=False)] == combos  # l'ordine e' quello di itertools.product
    assert list(embeddings) == combos
    assert results.index.tolist() == list(range(len(combos)))


@settings(max_examples=40)
@given(grid=_AXES)
def test_each_embedding_has_the_swept_number_of_components_and_one_row_per_subject(grid):
    _, embeddings = _sweep(grid)
    keys = list(grid)
    for combo, embedding in embeddings.items():
        assert embedding.shape == (len(_X), dict(zip(keys, combo))["n_components"])
        assert np.isfinite(embedding).all()


@settings(max_examples=30)
@given(components=st.lists(st.integers(1, 6), min_size=2, max_size=5, unique=True))
def test_the_cumulative_explained_variance_is_in_unit_interval_and_grows_with_n_components(components):
    results, _ = _sweep({"n_components": components})
    scores = results.set_index("n_components")[CUMULATIVE_EXPLAINED_VARIANCE]
    assert ((scores >= 0) & (scores <= 1 + 1e-9)).all()
    ordered = scores.sort_index().to_numpy()
    assert (np.diff(ordered) >= -1e-9).all()  # tenere piu' componenti non puo' spiegare meno varianza
    if 6 in components:
        assert scores[6] == pytest.approx(1.0)  # rango pieno: tutta la varianza


@settings(max_examples=20)
@given(grid=_AXES)
def test_the_sweep_does_not_mutate_its_inputs_and_is_deterministic(grid):
    base = dict(_BASE)
    grid_before = {k: list(v) for k, v in grid.items()}
    X_before = _X.copy()
    first, e1 = _sweep(grid, base)
    second, e2 = _sweep(grid, base)
    assert base == _BASE and grid == grid_before and np.array_equal(_X, X_before)
    pd.testing.assert_frame_equal(first, second)
    assert all(np.array_equal(e1[k], e2[k]) for k in e1)


def test_swept_values_override_base_params_for_the_swept_keys_only():
    base = {**_BASE, "n_components": 5}  # il valore di base e' sovrascritto dall'asse n_components
    _, embeddings = _sweep({"n_components": [2, 3]}, base)
    assert {e.shape[1] for e in embeddings.values()} == {2, 3}
    _, embeddings = _sweep({"standardize": [False, True]}, base)  # asse non toccato: resta il 5 di base
    assert {e.shape[1] for e in embeddings.values()} == {5}


# ---- registri e validazione degli argomenti ----------------------------------------------------------------------------------------------------


def test_registries_describe_the_same_methods():
    assert set(T.TUNING_METRIC_NAMES) == set(T._EVALUATORS)
    assert set(T.TUNING_METRIC_NAMES) <= set(REDUCTION_METHODS)
    assert T.METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS <= set(T.TUNING_METRIC_NAMES)
    assert T.METHODS_WITH_DISTANCE_CACHE <= T.METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS
    assert T.METHODS_WITH_MODEL_CACHE <= set(T.TUNING_METRIC_NAMES)
    for method, score in T.TUNING_METRIC_NAMES.items():
        needs_neighbors = method in T.METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS
        assert (score == TRUSTWORTHINESS) == needs_neighbors  # trustworthiness <=> serve n_neighbors; altrimenti varianza spiegata
    # ogni metodo e' esattamente in una delle due famiglie di score
    assert set(T.TUNING_METRIC_NAMES.values()) == {TRUSTWORTHINESS, CUMULATIVE_EXPLAINED_VARIANCE}


@settings(max_examples=60)
@given(method=st.text(max_size=10).filter(lambda m: m not in T.TUNING_METRIC_NAMES))
def test_an_unsupported_method_is_a_valueerror_listing_the_supported_ones(method):
    with pytest.raises(ValueError, match="fine-tuning not supported") as excinfo:
        T.run_tuning_sweep(method, _X, {}, {"a": [1]}, 5)
    assert all(known in str(excinfo.value) for known in T.TUNING_METRIC_NAMES)


@pytest.mark.parametrize("method", sorted(T.METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS))
def test_trustworthiness_methods_require_n_neighbors_before_any_fit(method):
    with pytest.raises(ValueError, match="trustworthiness_n_neighbors is required"):
        T.run_tuning_sweep(method, _X, {}, {"n_components": [2]}, None)


@pytest.mark.parametrize("method", sorted(set(T.TUNING_METRIC_NAMES) - T.METHODS_WITH_MODEL_CACHE))
def test_a_model_cache_given_to_a_method_without_one_is_a_valueerror_even_if_empty(method):
    with pytest.raises(ValueError, match="no model cache"):
        T.run_tuning_sweep(method, _X, {}, {"n_components": [2]}, 5, model_cache={})


def test_a_caller_model_cache_is_filled_by_the_pca_sweep_and_reused_by_a_second_sweep():
    cache: dict = {}
    first, _ = T.run_tuning_sweep("pca", _X, _BASE, {"n_components": [2, 3]}, None, model_cache=cache)
    assert cache  # il decomposition fitted e' leggibile dal chiamante
    keys_after_first = set(cache)
    second, _ = T.run_tuning_sweep("pca", _X, _BASE, {"n_components": [2, 3, 4]}, None, model_cache=cache)
    assert set(cache) == keys_after_first  # n_components non cambia la decomposizione: nessun nuovo fit
    assert second.iloc[:2][CUMULATIVE_EXPLAINED_VARIANCE].tolist() == pytest.approx(first[CUMULATIVE_EXPLAINED_VARIANCE].tolist())


# ---- bug sospetti ----------------------------------------------------------------------------------------------------------------------------------


def test_a_duplicate_value_in_an_axis_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        _sweep({"n_components": [2, 2, 3]})


def test_an_empty_axis_is_an_error_not_an_empty_sweep():
    with pytest.raises(ValueError, match="empty"):
        _sweep({"n_components": []})
