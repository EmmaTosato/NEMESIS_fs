"""Test a proprietà / parametrici di src/analysis/model_config.py.

Contratto: `FileNotFoundError` se il file non c'e', `ValueError` identificando il campo per ogni problema
di forma o dominio - mai `TypeError`/`KeyError`/`AttributeError` (lessons_learned #1, #5, #7, #8).
Le config vengono generate per mutazione di una config valida con un valore JSON arbitrario.
"""

from __future__ import annotations

import copy
import itertools
import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import model_config as M
from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.reduction import REDUCTION_METHODS
from src.analysis.tuning_evaluations import EVALUATIONS, KIND_EMBEDDING_EVALUATION, KIND_SWEEP_SCORE

_HDBSCAN = {"min_cluster_size": 5, "min_samples": 2}
_SHARED = {"project": "p", "input_path": "in", "output_root": "out", "session_name": "s", "overwrite": False, "run_notes": "n"}

_CASES: dict[str, tuple] = {
    "dim_reduction": (
        M.load_dim_reduction_config,
        {**_SHARED, "reduction_method": "umap", "params_file": "pf.json", "fine_tuning": False, "color_by": ["dataset"],
         "viz_n_components": 2, "save_tuning_embeddings": False, "precompute_distance_metric": True,
         "tuning_evaluations": {"trustworthiness": {}, "plot_hdbscan": _HDBSCAN}},
        {"run_notes"},
    ),
    "evaluate_tuning_embeddings": (
        M.load_evaluate_tuning_embeddings_config,
        {"tuning_dir": "td", "overwrite": True, "tuning_evaluations": {"plot_hdbscan": _HDBSCAN}},
        set(),
    ),
    "analyze_clustering_tuning": (
        M.load_analyze_clustering_tuning_config,
        {"tuning_dir": "td", "overwrite": False, "evaluations_file": "ef.json", "write_report": True,
         "tuning_evaluations": {"general": [], "agglomerative": ["cophenetic_correlation"]}},
        set(),
    ),
    "clustering_reduced": (
        M.load_clustering_config,
        {**_SHARED, "reduction_method": "umap", "clustering_methods": ["kmeans", "gmm"], "params_file": "pf.json",
         "reduction_params_file": "rpf.json", "fine_tuning": True, "reduced_data": True, "viz_embedding_path": "viz",
         "save_tuning_clusterings": False, "evaluations_file": "ef.json",
         "tuning_evaluations": {"general": [], "kmeans": [], "gmm": []}},
        {"run_notes", "viz_embedding_path"},
    ),
    "clustering_raw": (
        M.load_clustering_config,
        {**_SHARED, "reduction_method": "raw", "clustering_methods": ["hdbscan"], "params_file": "pf.json", "fine_tuning": False,
         "reduced_data": False, "save_tuning_clusterings": True, "evaluations_file": "ef.json",
         "tuning_evaluations": {"general": [], "hdbscan": ["density_metrics"]}},
        {"run_notes", "viz_embedding_path"},
    ),
}
_CASE_NAMES = list(_CASES)

_NESTED = {
    "dim_reduction": [("color_by", 0), ("tuning_evaluations", "plot_hdbscan"), ("tuning_evaluations", "plot_hdbscan", "min_samples"),
                      ("tuning_evaluations", "trustworthiness")],
    "evaluate_tuning_embeddings": [("tuning_evaluations", "plot_hdbscan"), ("tuning_evaluations", "plot_hdbscan", "min_cluster_size")],
    "analyze_clustering_tuning": [("tuning_evaluations", "general"), ("tuning_evaluations", "agglomerative"),
                                  ("tuning_evaluations", "agglomerative", 0)],
    "clustering_reduced": [("clustering_methods", 0), ("clustering_methods", 1), ("tuning_evaluations", "general"),
                           ("tuning_evaluations", "kmeans")],
    "clustering_raw": [("clustering_methods", 0), ("tuning_evaluations", "general"), ("tuning_evaluations", "hdbscan"),
                       ("tuning_evaluations", "hdbscan", 0)],
}

_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(-5, 5),
    st.integers(min_value=10**30, max_value=10**40),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(max_size=6),
)
_json = st.recursive(
    _scalars,
    lambda children: st.one_of(st.lists(children, max_size=3), st.dictionaries(st.text(max_size=4), children, max_size=3)),
    max_leaves=6,
)
_DELETE = object()


def _paths(case: str) -> list[tuple]:
    return [(key,) for key in _CASES[case][1]] + [("unknown_field",)] + _NESTED[case]


def _mutated(case: str, path: tuple, value: object) -> dict:
    config = copy.deepcopy(_CASES[case][1])
    *parents, leaf = path
    node = config
    for step in parents:
        node = node[step]
    if value is _DELETE:
        if isinstance(node, list):
            del node[leaf]
        else:
            node.pop(leaf, None)
    else:
        node[leaf] = value
    return config


def _load(case: str, obj: object):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "cfg.json"
        path.write_text(json.dumps(obj))
        return _CASES[case][0](path)


# ---- ancora + fuzz ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", _CASE_NAMES)
def test_the_unmutated_config_loads(case):
    assert _load(case, _CASES[case][1]) is not None


@settings(max_examples=250)
@given(case=st.sampled_from(_CASE_NAMES), data=st.data())
def test_a_mutated_config_loads_or_raises_valueerror_never_another_exception(case, data):
    path = data.draw(st.sampled_from(_paths(case)))
    value = data.draw(st.one_of(_json, st.just(_DELETE)))
    try:
        _load(case, _mutated(case, path, value))
    except ValueError:
        pass


@settings(max_examples=100)
@given(case=st.sampled_from(_CASE_NAMES), top=_json)
def test_a_top_level_that_is_not_an_object_is_a_valueerror(case, top):
    if isinstance(top, dict):
        return
    with pytest.raises(ValueError, match="top-level"):
        _load(case, top)


@pytest.mark.parametrize("case", _CASE_NAMES)
def test_missing_file_and_directory_raise_filenotfounderror(case, tmp_path):
    for target in (tmp_path / "absent.json", tmp_path):
        with pytest.raises(FileNotFoundError, match="config file not found"):
            _CASES[case][0](target)


@pytest.mark.parametrize("case", _CASE_NAMES)
@pytest.mark.parametrize("fraction", [0.2, 0.6, 0.95])
def test_a_truncated_file_is_a_valueerror(case, fraction, tmp_path):
    text = json.dumps(_CASES[case][1])
    file = tmp_path / "cfg.json"
    file.write_text(text[: int(len(text) * fraction)])
    with pytest.raises(ValueError):
        _CASES[case][0](file)


# ---- campi per tipo ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("case, field", [(c, k) for c in _CASE_NAMES for k in _CASES[c][1] if k not in _CASES[c][2]])
def test_deleting_any_required_field_names_it_in_the_error(case, field):
    with pytest.raises(ValueError, match=field):
        _load(case, _mutated(case, (field,), _DELETE))


@pytest.mark.parametrize("case, field", [(c, k) for c in _CASE_NAMES for k, v in _CASES[c][1].items() if isinstance(v, str)])
@pytest.mark.parametrize("bad", [0, 1, True, 1.5, [], ["a"], {}, {"a": 1}, ""])
def test_string_fields_reject_non_strings_and_empty_strings(case, field, bad):
    with pytest.raises(ValueError, match=field):
        _load(case, _mutated(case, (field,), bad))


@pytest.mark.parametrize("case, field", [(c, k) for c in _CASE_NAMES for k, v in _CASES[c][1].items() if isinstance(v, bool)])
@pytest.mark.parametrize("bad", [0, 1, "true", "no", None, [], {}, 1.0])
def test_boolean_fields_reject_truthy_and_falsy_non_booleans(case, field, bad):
    with pytest.raises(ValueError, match=field):
        _load(case, _mutated(case, (field,), bad))


@pytest.mark.parametrize("field", ["run_notes"])
@pytest.mark.parametrize("case", ["dim_reduction", "clustering_reduced", "clustering_raw"])
def test_optional_strings_accept_absent_or_null_but_not_empty_or_wrong_type(case, field):
    assert getattr(_load(case, _mutated(case, (field,), _DELETE)), field) is None
    assert getattr(_load(case, _mutated(case, (field,), None)), field) is None
    for bad in ("", 3, True, [], {}):
        with pytest.raises(ValueError, match=field):
            _load(case, _mutated(case, (field,), bad))


# ---- metodi: registri ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("method", sorted(REDUCTION_METHODS))
def test_every_registered_reduction_method_is_accepted_by_dim_reduction(method):
    assert _load("dim_reduction", _mutated("dim_reduction", ("reduction_method",), method)).reduction_method == method


@pytest.mark.parametrize("method", sorted(set(REDUCTION_METHODS) | {"raw"}))
def test_clustering_accepts_every_reduction_method_and_the_raw_sentinel(method):
    config = _mutated("clustering_raw", ("reduction_method",), method)
    assert _load("clustering_raw", config).reduction_method == method


@pytest.mark.parametrize("method", ["raw"])
def test_dim_reduction_does_not_accept_the_raw_sentinel(method):
    with pytest.raises(ValueError, match="unknown reduction_method"):
        _load("dim_reduction", _mutated("dim_reduction", ("reduction_method",), method))


@settings(max_examples=80)
@given(method=st.text(max_size=10).filter(lambda m: m and m not in REDUCTION_METHODS))
def test_an_unregistered_reduction_method_is_rejected_in_both_loaders(method):
    with pytest.raises(ValueError):
        _load("dim_reduction", _mutated("dim_reduction", ("reduction_method",), method))
    if method != "raw":
        with pytest.raises(ValueError):
            _load("clustering_raw", _mutated("clustering_raw", ("reduction_method",), method))


@pytest.mark.parametrize("method", sorted(CLUSTERING_METHODS))
def test_every_registered_clustering_method_is_accepted(method):
    config = _mutated("clustering_raw", ("clustering_methods",), [method])
    assert _load("clustering_raw", config).clustering_methods == (method,)


@settings(max_examples=60)
@given(methods=st.lists(st.sampled_from(sorted(CLUSTERING_METHODS)), min_size=1, max_size=len(CLUSTERING_METHODS), unique=True))
def test_a_unique_list_of_clustering_methods_keeps_its_order_as_a_tuple(methods):
    loaded = _load("clustering_raw", _mutated("clustering_raw", ("clustering_methods",), methods)).clustering_methods
    assert loaded == tuple(methods) and isinstance(loaded, tuple)


@settings(max_examples=80)
@given(methods=st.lists(st.sampled_from(sorted(CLUSTERING_METHODS)), min_size=2, max_size=5))
def test_a_clustering_methods_list_is_accepted_iff_it_has_no_duplicates(methods):
    config = _mutated("clustering_raw", ("clustering_methods",), methods)
    if len(set(methods)) != len(methods):
        with pytest.raises(ValueError, match="duplicate"):
            _load("clustering_raw", config)
    else:
        assert _load("clustering_raw", config).clustering_methods == tuple(methods)


@pytest.mark.parametrize(
    "bad",
    [[], None, "kmeans", {"kmeans": 1}, 3, [""], [1], [None], [["kmeans"]], ["kmeans", "nope"], ["nope"], ["KMEANS"], ["dbscan"], ["kmeans", "kmeans"]],
)
def test_malformed_clustering_methods_are_a_valueerror(bad):
    with pytest.raises(ValueError, match="clustering_method"):
        _load("clustering_raw", _mutated("clustering_raw", ("clustering_methods",), bad))


# ---- color_by -------------------------------------------------------------------------------------------------------------


@settings(max_examples=60)
@given(items=st.lists(st.text(min_size=1, max_size=4), max_size=5, unique=True))
def test_color_by_accepts_any_unique_list_of_non_empty_strings_including_empty(items):
    assert _load("dim_reduction", _mutated("dim_reduction", ("color_by",), items)).color_by == tuple(items)


@pytest.mark.parametrize("bad", [None, "dataset", 3, {"a": 1}, [""], [1], [None], ["a", "a"], ["a", "b", "a"], [["a"]]])
def test_malformed_color_by_is_a_valueerror(bad):
    with pytest.raises(ValueError, match="color_by"):
        _load("dim_reduction", _mutated("dim_reduction", ("color_by",), bad))


# ---- viz_n_components, k_range, frazione -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("value, valid", [(2, True), (3, True), (1, False), (4, False), (0, False), (-2, False), (2.0, False), (True, False),
                                          (False, False), ("2", False), (None, False), ([2], False), (10**30, False)])
def test_viz_n_components_is_exactly_2_or_3(value, valid):
    config = _mutated("dim_reduction", ("viz_n_components",), value)
    if valid:
        assert _load("dim_reduction", config).viz_n_components == value
    else:
        with pytest.raises(ValueError, match="viz_n_components"):
            _load("dim_reduction", config)


# ---- reduced_data <-> reduction_params_file ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("reduced_data, params_file, valid", [(True, "r.json", True), (True, None, False), (False, None, True), (False, "r.json", False)])
def test_reduction_params_file_is_required_exactly_when_the_data_is_reduced(reduced_data, params_file, valid):
    config = copy.deepcopy(_CASES["clustering_reduced"][1])
    config["reduced_data"] = reduced_data
    config.pop("reduction_params_file")
    if params_file is not None:
        config["reduction_params_file"] = params_file
    if valid:
        assert _load("clustering_reduced", config).reduction_params_file == (Path(params_file) if params_file else None)
    else:
        with pytest.raises(ValueError, match="reduction_params_file"):
            _load("clustering_reduced", config)


@pytest.mark.parametrize("bad", ["", 3, True, [], {}])
def test_a_wrongly_typed_reduction_params_file_is_a_valueerror_even_when_it_would_be_forbidden(bad):
    config = _mutated("clustering_raw", ("reduction_params_file",), bad)
    with pytest.raises(ValueError):
        _load("clustering_raw", config)


# ---- tuning_evaluations -------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("value", [None, [], "plot_hdbscan", 3, True, [{"plot_hdbscan": {}}]])
def test_a_tuning_evaluations_block_that_is_not_an_object_is_a_valueerror(value):
    for case in ("dim_reduction", "evaluate_tuning_embeddings"):
        with pytest.raises(ValueError, match="tuning_evaluations"):
            _load(case, _mutated(case, ("tuning_evaluations",), value))


def test_an_empty_tuning_evaluations_block_is_valid_for_dim_reduction_but_not_for_the_standalone_entry_point():
    assert _load("dim_reduction", _mutated("dim_reduction", ("tuning_evaluations",), {})).tuning_evaluations == {}
    with pytest.raises(ValueError, match="at least one"):
        _load("evaluate_tuning_embeddings", _mutated("evaluate_tuning_embeddings", ("tuning_evaluations",), {}))


@pytest.mark.parametrize("name", sorted(n for n, spec in EVALUATIONS.items() if spec.kind == KIND_SWEEP_SCORE))
def test_the_standalone_entry_point_rejects_every_sweep_score(name):
    with pytest.raises(ValueError, match="cannot be run here"):
        _load("evaluate_tuning_embeddings", _mutated("evaluate_tuning_embeddings", ("tuning_evaluations",), {name: {}}))


@pytest.mark.parametrize("name", sorted(n for n, spec in EVALUATIONS.items() if spec.kind == KIND_EMBEDDING_EVALUATION))
def test_the_standalone_entry_point_accepts_every_embedding_evaluation_with_valid_settings(name):
    settings_ = _HDBSCAN if name == "plot_hdbscan" else {}
    loaded = _load("evaluate_tuning_embeddings", _mutated("evaluate_tuning_embeddings", ("tuning_evaluations",), {name: settings_}))
    assert loaded.tuning_evaluations == {name: settings_}


@settings(max_examples=60)
@given(name=st.text(max_size=12).filter(lambda n: n not in EVALUATIONS))
def test_an_unregistered_evaluation_name_is_rejected(name):
    with pytest.raises(ValueError, match="unknown tuning evaluation"):
        _load("dim_reduction", _mutated("dim_reduction", ("tuning_evaluations",), {name: {}}))


# ---- il config non cambia con l'ordine dei campi nel file -----------------------------------------------------------------------------------


@settings(max_examples=20)
@given(order=st.permutations(list(_CASES["clustering_reduced"][1])))
def test_field_order_in_the_file_does_not_change_the_loaded_config(order):
    base = _CASES["clustering_reduced"][1]
    shuffled = {key: base[key] for key in order}
    assert _load("clustering_reduced", shuffled) == _load("clustering_reduced", base)


def test_a_loaded_config_is_immutable():
    config = _load("dim_reduction", _CASES["dim_reduction"][1])
    with pytest.raises(AttributeError):
        config.overwrite = True  # dataclass frozen


def test_every_case_pair_of_methods_combinations_is_loadable():
    """Tutte le coppie ordinate (reduction, clustering) del registro sono configurazioni valide: la validazione non
    codifica compatibilita' fra i due che il codice a valle non conosce."""
    for reduction, clustering in itertools.product(sorted(set(REDUCTION_METHODS) | {"raw"}), sorted(CLUSTERING_METHODS)):
        config = _mutated("clustering_raw", ("reduction_method",), reduction)
        config["clustering_methods"] = [clustering]
        assert _load("clustering_raw", config).clustering_methods == (clustering,)
