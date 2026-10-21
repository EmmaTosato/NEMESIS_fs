"""Test a proprietà / parametrici di src/analysis/tuning_evaluations.py (parti pure: validazione del blocco,
fattibilita', twin 2D, score nativo). Contratto: `ValueError` con il nome del meccanismo e del campo -
mai `TypeError`/`KeyError` (lesson #7, #8).
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import tuning_evaluations as EV
from src.analysis.tuning_embeddings import combo_key
from src.analysis.tuning_evaluations import (
    CUMULATIVE_EXPLAINED_VARIANCE,
    EVALUATIONS,
    KIND_EMBEDDING_EVALUATION,
    KIND_SWEEP_SCORE,
    PLOT_HDBSCAN,
    TRUSTWORTHINESS,
    VIZ_N_COMPONENTS,
    require_native_score_declared,
    run_embedding_evaluations,
    validate_embedding_evaluations_feasible,
    validate_tuning_evaluations_block,
    visualization_key,
)

_scalars = st.one_of(
    st.none(), st.booleans(), st.integers(-5, 5), st.integers(min_value=10**30, max_value=10**40),
    st.floats(allow_nan=True, allow_infinity=True), st.text(max_size=6),
)
_json = st.recursive(
    _scalars,
    lambda children: st.one_of(st.lists(children, max_size=3), st.dictionaries(st.text(max_size=4), children, max_size=3)),
    max_leaves=6,
)
_HDBSCAN = {"min_cluster_size": 5, "min_samples": 2}
_SWEEP_SCORES = sorted(n for n, spec in EVALUATIONS.items() if spec.kind == KIND_SWEEP_SCORE)
_EMBEDDING_EVALS = sorted(n for n, spec in EVALUATIONS.items() if spec.kind == KIND_EMBEDDING_EVALUATION)


# ---- validate_tuning_evaluations_block ---------------------------------------------------------------------------------------------


@settings(max_examples=300)
@given(block=_json)
def test_an_arbitrary_json_block_is_accepted_or_a_valueerror(block):
    try:
        out = validate_tuning_evaluations_block(block)
    except ValueError:
        return
    assert isinstance(out, dict) and set(out) <= set(EVALUATIONS)


@settings(max_examples=200)
@given(name=st.sampled_from(sorted(EVALUATIONS)), settings_=_json)
def test_arbitrary_settings_for_a_registered_name_are_accepted_or_a_valueerror(name, settings_):
    try:
        out = validate_tuning_evaluations_block({name: settings_})
    except ValueError:
        return
    assert out == {name: settings_} and isinstance(settings_, dict)


@settings(max_examples=100)
@given(name=st.sampled_from(sorted(EVALUATIONS)), kinds=st.sets(st.sampled_from([KIND_SWEEP_SCORE, KIND_EMBEDDING_EVALUATION, "other"])),
       settings_=_json)
def test_allowed_kinds_never_lets_through_another_kind_and_never_raises_other_than_valueerror(name, kinds, settings_):
    try:
        validate_tuning_evaluations_block({name: settings_}, frozenset(kinds))
    except ValueError:
        return
    assert EVALUATIONS[name].kind in kinds


@pytest.mark.parametrize("name", _SWEEP_SCORES)
@settings(max_examples=40)
@given(settings_=st.dictionaries(st.text(min_size=1, max_size=5), _scalars, min_size=1, max_size=3))
def test_a_sweep_score_takes_no_settings(name, settings_):
    with pytest.raises(ValueError, match="takes no settings"):
        validate_tuning_evaluations_block({name: settings_})


@pytest.mark.parametrize("name", _SWEEP_SCORES)
def test_a_sweep_score_with_empty_settings_is_valid(name):
    assert validate_tuning_evaluations_block({name: {}}) == {name: {}}


def test_the_empty_block_is_valid_and_the_result_is_a_copy_of_the_input():
    raw = {PLOT_HDBSCAN: dict(_HDBSCAN)}
    out = validate_tuning_evaluations_block(raw)
    assert out == raw and out is not raw
    out["new"] = 1
    assert "new" not in raw
    assert validate_tuning_evaluations_block({}) == {}


@pytest.mark.parametrize("settings_", [{}, {"min_cluster_size": 5}, {"min_samples": 2}, {**_HDBSCAN, "extra": 1}, {"min_cluster_size": 5, "min_sample": 2}])
def test_plot_hdbscan_needs_exactly_its_two_settings(settings_):
    with pytest.raises(ValueError, match="needs exactly"):
        validate_tuning_evaluations_block({PLOT_HDBSCAN: settings_})


@pytest.mark.parametrize("field, minimum", [("min_cluster_size", 2), ("min_samples", 1)])
@pytest.mark.parametrize(
    "offset, valid",
    [(0, True), (1, True), (10**9, True), (-1, False), (-10, False)],
)
def test_plot_hdbscan_integer_lower_bounds(field, minimum, offset, valid):
    block = {PLOT_HDBSCAN: {**_HDBSCAN, field: minimum + offset}}
    if valid:
        assert validate_tuning_evaluations_block(block) == block
    else:
        with pytest.raises(ValueError, match=field):
            validate_tuning_evaluations_block(block)


@pytest.mark.parametrize("field", ["min_cluster_size", "min_samples"])
@pytest.mark.parametrize("bad", [True, False, 5.0, 5.5, "5", None, [5], {}, float("nan"), float("inf")])
def test_plot_hdbscan_settings_must_be_real_integers_not_bool_float_or_text(field, bad):
    with pytest.raises(ValueError, match=field):
        validate_tuning_evaluations_block({PLOT_HDBSCAN: {**_HDBSCAN, field: bad}})


@pytest.mark.parametrize("settings_", [None, [], "x", 3, True, [{"a": 1}]])
def test_settings_that_are_not_an_object_are_a_valueerror_naming_the_mechanism(settings_):
    with pytest.raises(ValueError, match=PLOT_HDBSCAN):
        validate_tuning_evaluations_block({PLOT_HDBSCAN: settings_})


@settings(max_examples=80)
@given(name=st.text(max_size=12).filter(lambda n: n not in EVALUATIONS))
def test_an_unknown_mechanism_name_lists_the_known_ones(name):
    with pytest.raises(ValueError, match="unknown tuning evaluation") as excinfo:
        validate_tuning_evaluations_block({name: {}})
    assert all(known in str(excinfo.value) for known in EVALUATIONS)


@pytest.mark.parametrize("name, spec", sorted(EVALUATIONS.items()))
def test_every_registered_spec_is_internally_consistent(name, spec):
    assert spec.kind in {KIND_SWEEP_SCORE, KIND_EMBEDDING_EVALUATION}
    if spec.kind == KIND_EMBEDDING_EVALUATION:
        assert spec.run is not None  # un'evaluation su embedding salvati deve poter girare
    else:
        assert spec.run is None and spec.check_feasible is None  # uno score di sweep lo calcola lo sweep


# ---- require_native_score_declared ------------------------------------------------------------------------------------------------------


@settings(max_examples=60)
@given(declared=st.sets(st.sampled_from(_SWEEP_SCORES)), with_hdbscan=st.booleans(), expected=st.sampled_from(_SWEEP_SCORES))
def test_the_native_score_must_be_declared_alone_and_extra_embedding_evaluations_do_not_count(declared, with_hdbscan, expected):
    evaluations = {name: {} for name in declared}
    if with_hdbscan:
        evaluations[PLOT_HDBSCAN] = dict(_HDBSCAN)
    if declared == {expected}:
        require_native_score_declared(evaluations, expected, "umap")
    else:
        with pytest.raises(ValueError, match="exactly the sweep score"):
            require_native_score_declared(evaluations, expected, "umap")


# ---- visualization_key ----------------------------------------------------------------------------------------------------------------------


_NAMES = st.text(alphabet="abcdefg", min_size=1, max_size=4).filter(lambda n: n != "n_components")


@settings(max_examples=100)
@given(others=st.dictionaries(_NAMES, st.integers(0, 9), max_size=3), dim=st.integers(1, 12).filter(lambda d: d != VIZ_N_COMPONENTS), position=st.integers(0, 3))
def test_the_twin_differs_from_the_key_only_in_n_components(others, dim, position):
    names = list(others)
    names.insert(min(position, len(names)), "n_components")
    values = {**others, "n_components": dim}
    key = combo_key(names, [values[n] for n in names])
    twin = combo_key(names, [VIZ_N_COMPONENTS if n == "n_components" else values[n] for n in names])
    assert visualization_key(key, dim, {twin: np.zeros((3, 2))}) == twin
    with pytest.raises(ValueError, match="twin"):
        visualization_key(key, dim, {})


@settings(max_examples=60)
@given(key=st.text(max_size=20), available=st.lists(st.text(max_size=5), max_size=3))
def test_a_2d_embedding_is_its_own_visualization_without_parsing_its_key(key, available):
    assert visualization_key(key, VIZ_N_COMPONENTS, {k: None for k in available}) == key


@settings(max_examples=60)
@given(dim=st.integers(0, 9).filter(lambda d: d != VIZ_N_COMPONENTS), names=st.lists(_NAMES, min_size=1, max_size=3, unique=True))
def test_a_higher_dimensional_embedding_without_n_components_in_its_key_cannot_be_drawn(dim, names):
    key = combo_key(names, [1] * len(names))
    with pytest.raises(ValueError, match="no n_components"):
        visualization_key(key, dim, {key: None})


@pytest.mark.parametrize("key", ["", "n_components", "n_components=", "a=1,,n_components=3"])
def test_a_malformed_key_of_a_non_2d_embedding_is_a_valueerror(key):
    with pytest.raises(ValueError):
        visualization_key(key, 3, {})


# ---- fattibilita' di plot_hdbscan -------------------------------------------------------------------------------------------------------------


def _feasible(grid_dims, base_dims):
    grid = {"metric": ["x"]}
    if grid_dims is not None:
        grid["n_components"] = grid_dims
    base = {} if base_dims is None else {"n_components": base_dims}
    validate_embedding_evaluations_feasible({PLOT_HDBSCAN: dict(_HDBSCAN)}, base, grid)


@settings(max_examples=150)
@given(grid_dims=st.one_of(st.none(), st.lists(st.integers(1, 12), min_size=1, max_size=4)), base_dims=st.one_of(st.none(), st.integers(1, 12)))
def test_feasibility_matches_the_oracle(grid_dims, base_dims):
    """Gira solo se ogni dimensionalita' != 2 puo' essere disegnata sul suo gemello a 2 componenti, che deve essere nello sweep."""
    if grid_dims is not None:
        dims, has_twin = set(grid_dims), VIZ_N_COMPONENTS in grid_dims
    elif base_dims is not None:
        dims, has_twin = {base_dims}, False
    else:
        _feasible(grid_dims, base_dims)  # dimensione ignota: decide il controllo post-sweep
        return
    if dims <= {VIZ_N_COMPONENTS} or has_twin:
        _feasible(grid_dims, base_dims)
    else:
        with pytest.raises(ValueError, match="twin"):
            _feasible(grid_dims, base_dims)


def test_feasibility_of_sweep_scores_and_empty_blocks_is_a_noop():
    for name in _SWEEP_SCORES:
        validate_embedding_evaluations_feasible({name: {}}, {"n_components": 10}, {"n_components": [10]})
    validate_embedding_evaluations_feasible({}, {"n_components": 10}, {"n_components": [10]})


@pytest.mark.parametrize("base, grid", [({"n_components": [3]}, {}), ({}, {"n_components": [[3], 4]}), ({"n_components": {"a": 1}}, {})])
def test_a_non_scalar_n_components_in_the_feasibility_check_is_a_valueerror(base, grid):
    with pytest.raises(ValueError):
        validate_embedding_evaluations_feasible({PLOT_HDBSCAN: dict(_HDBSCAN)}, base, grid)


# ---- run_embedding_evaluations ------------------------------------------------------------------------------------------------------------------


@settings(max_examples=30)
@given(names=st.sets(st.sampled_from(_SWEEP_SCORES)))
def test_a_block_with_only_sweep_scores_runs_nothing_and_touches_no_run(names):
    class Exploding:
        """Se run_embedding_evaluations toccasse il TuningRun, qualunque attributo farebbe esplodere il test."""

        def __getattr__(self, attr):
            raise AssertionError(f"the run was touched ({attr})")

    assert run_embedding_evaluations({name: {} for name in names}, Exploding(), overwrite=False) == []


def test_the_registered_score_names_are_the_ones_tuning_declares():
    from src.analysis.tuning import TUNING_METRIC_NAMES

    assert set(TUNING_METRIC_NAMES.values()) == {TRUSTWORTHINESS, CUMULATIVE_EXPLAINED_VARIANCE} == set(_SWEEP_SCORES)
    assert set(itertools.chain(_SWEEP_SCORES, _EMBEDDING_EVALS)) == set(EV.EVALUATIONS)
