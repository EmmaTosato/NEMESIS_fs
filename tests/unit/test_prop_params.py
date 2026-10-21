"""Test a proprietà / parametrici di src/analysis/params.py.

Il contratto sotto prova (docstring del modulo): ogni loader o restituisce un valore valido o solleva
`FileNotFoundError` (file assente) / `ValueError` (forma o contenuto del registro sbagliati) - mai
`TypeError`/`KeyError`/`AttributeError` (lessons_learned #7, #8). I registri vengono generati per
mutazione di una entry valida, con un valore JSON arbitrario (None, bool, interi enormi, NaN, liste,
oggetti annidati) al posto di un campo.
"""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import params as P
from src.analysis.clustering_tuning import STABILITY_ELIGIBLE_METHODS
from src.analysis.consensus_clustering import CONSENSUS_ELIGIBLE_METHODS

_METHOD = "kmeans"  # eleggibile sia per "consensus" che per "stability"

_VALID_ENTRY = {
    "params": {"n_clusters": 3, "init": "k-means++", "random_state": 0},
    "tag_param": ["n_clusters", "init"],
    "tag_prefix": ["k", "i"],
    "tag_omit": {"init": "k-means++"},
    "tuning_grid": {"n_clusters": [2, 3, 4], "init": ["k-means++", "random"]},
    "nested_params": ["init"],
    "trustworthiness_n_neighbors": 5,
    "consensus": {"rsc": {"n_repeats": 3}, "monti": {"n_repeats": 3, "subsample_fraction": 0.8}},
    "stability": {"nuisance_values": ["k-means++", "random"], "n_init_range": [1, 5], "n_repeats": 3},
}

_ALL_LOADERS = {
    "load_method_params": lambda f: P.load_method_params(f, _METHOD),
    "load_tag_spec": lambda f: P.load_tag_spec(f, _METHOD),
    "load_tag_params": lambda f: P.load_tag_params(f, _METHOD),
    "load_tuning_grid": lambda f: P.load_tuning_grid(f, _METHOD),
    "load_nested_params": lambda f: P.load_nested_params(f, _METHOD, {"n_clusters": [2, 3], "init": ["a", "b"]}),
    "load_consensus_config": lambda f: P.load_consensus_config(f, _METHOD),
    "load_stability_config": lambda f: P.load_stability_config(f, _METHOD),
    "load_trustworthiness_n_neighbors": lambda f: P.load_trustworthiness_n_neighbors(f, _METHOD),
}

# ---- strategie ----------------------------------------------------------------------------------

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

# Percorsi (dal registro) in cui sostituire/cancellare un valore: ogni campo dell'entry e alcuni
# sotto-campi e indici di lista.
_PATHS = [
    (_METHOD,),
    (_METHOD, "params"),
    (_METHOD, "params", "n_clusters"),
    (_METHOD, "tag_param"),
    (_METHOD, "tag_param", 0),
    (_METHOD, "tag_prefix"),
    (_METHOD, "tag_prefix", 1),
    (_METHOD, "tag_omit"),
    (_METHOD, "tag_omit", "init"),
    (_METHOD, "tuning_grid"),
    (_METHOD, "tuning_grid", "n_clusters"),
    (_METHOD, "tuning_grid", "n_clusters", 0),
    (_METHOD, "nested_params"),
    (_METHOD, "nested_params", 0),
    (_METHOD, "trustworthiness_n_neighbors"),
    (_METHOD, "consensus"),
    (_METHOD, "consensus", "rsc"),
    (_METHOD, "consensus", "rsc", "n_repeats"),
    (_METHOD, "consensus", "monti"),
    (_METHOD, "consensus", "monti", "subsample_fraction"),
    (_METHOD, "stability"),
    (_METHOD, "stability", "nuisance_values"),
    (_METHOD, "stability", "nuisance_values", 0),
    (_METHOD, "stability", "n_init_range"),
    (_METHOD, "stability", "n_init_range", 1),
    (_METHOD, "stability", "n_repeats"),
]
_DELETE = object()
_TAG_PATHS = [p for p in _PATHS if len(p) == 1 or p[1] in {"params", "tag_param", "tag_prefix", "tag_omit"}]


def _mutated(path: tuple, value: object) -> dict:
    registry = {_METHOD: copy.deepcopy(_VALID_ENTRY)}
    *parents, leaf = path
    node = registry
    for step in parents:
        node = node[step]
    if value is _DELETE:
        del node[leaf]
    else:
        node[leaf] = value
    return registry


def _write(directory: str, obj: object) -> Path:
    path = Path(directory) / "params.json"
    path.write_text(json.dumps(obj))
    return path


def _call_documented(loader, file: Path):
    """Chiama il loader: ritorna il risultato, oppure None se ha sollevato l'eccezione documentata."""
    try:
        return loader(file)
    except ValueError:
        return None


# ---- fuzz per mutazione ----------------------------------------------------------------------------


def test_the_unmutated_registry_is_accepted_by_every_loader():
    """Ancora del fuzz: se il registro di partenza fosse già invalido, ogni mutazione 'passerebbe' per caso."""
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {_METHOD: _VALID_ENTRY})
        for name, loader in _ALL_LOADERS.items():
            loader(file)  # non solleva
        params, tag = P.load_method_params(file, _METHOD)
        assert params == _VALID_ENTRY["params"]
        assert tag == "k3"  # init == "k-means++" e' il valore di tag_omit: la sua parte viene omessa


@settings(max_examples=150)
@given(path=st.sampled_from(_PATHS), value=st.one_of(_json, st.just(_DELETE)))
def test_every_loader_returns_or_raises_valueerror_on_a_mutated_registry(path, value):
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, _mutated(path, value))
        for loader in _ALL_LOADERS.values():
            _call_documented(loader, file)


@settings(max_examples=100)
@given(top=_json)
def test_a_registry_whose_top_level_is_not_an_object_is_a_valueerror(top):
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, top)
        for loader in _ALL_LOADERS.values():
            if isinstance(top, dict) and _METHOD in top:
                continue
            with pytest.raises(ValueError):
                loader(file)


def test_the_documented_exceptions_for_a_missing_or_unreadable_registry(tmp_path):
    for loader in _ALL_LOADERS.values():
        with pytest.raises(FileNotFoundError):
            loader(tmp_path / "does_not_exist.json")
        with pytest.raises(FileNotFoundError):
            loader(tmp_path)  # una cartella non e' un file


@pytest.mark.parametrize("content", ['{"kmeans": {"params": {"a": 1', "", "{'kmeans': 1}", '{"kmeans": }', "\x00\x01"])
def test_a_truncated_or_malformed_registry_raises_valueerror_not_a_silent_default(tmp_path, content):
    file = tmp_path / "params.json"
    file.write_text(content)
    for loader in _ALL_LOADERS.values():
        with pytest.raises(ValueError):  # json.JSONDecodeError e' un ValueError
            loader(file)


def test_an_unreadable_registry_propagates_the_oserror_instead_of_hiding_it(tmp_path, monkeypatch):
    file = _write(str(tmp_path), {_METHOD: _VALID_ENTRY})
    real_open = Path.open

    def failing_open(self, *args, **kwargs):
        if self == file:
            raise PermissionError(13, "Permission denied", str(self))
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)
    for loader in _ALL_LOADERS.values():
        with pytest.raises(PermissionError):
            loader(file)


@settings(max_examples=60)
@given(method=st.text(max_size=8).filter(lambda m: m != _METHOD))
def test_an_unregistered_method_is_a_valueerror_naming_it(method):
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {_METHOD: _VALID_ENTRY})
        for loader in (
            lambda f: P.load_method_params(f, method),
            lambda f: P.load_tag_spec(f, method),
            lambda f: P.load_tag_params(f, method),
            lambda f: P.load_tuning_grid(f, method),
            lambda f: P.load_consensus_config(f, method),
            lambda f: P.load_stability_config(f, method),
            lambda f: P.load_trustworthiness_n_neighbors(f, method),
        ):
            with pytest.raises(ValueError, match="no entry for method"):
                loader(file)


# ---- coerenza fra i loader del tag ----------------------------------------------------------------


@settings(max_examples=80)
@given(path=st.sampled_from(_TAG_PATHS), value=st.one_of(_json, st.just(_DELETE)))
def test_the_two_tag_paths_agree_whenever_both_accept_the_registry(path, value):
    """load_method_params e load_tag_spec + build_tag_from_values usano la stessa formula (_join_tag):
    se entrambi accettano, la stringa e' identica."""
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, _mutated(path, value))
        loaded = _call_documented(lambda f: P.load_method_params(f, _METHOD), file)
        if loaded is None:
            return
        params, tag = loaded
        tag_param, tag_prefix = P.load_tag_spec(file, _METHOD)
        if tag is None:
            assert tag_param is None
            return
        assert P.build_tag_from_values(file, _METHOD, tag_param, tag_prefix, params) == tag
        assert P.load_tag_params(file, _METHOD) == tag_param


# ---- matrici parametriche: costruzione del tag -------------------------------------------------------


@pytest.mark.parametrize(
    "tag_param, tag_prefix, params, tag_omit, expected",
    [
        (["n"], ["nc"], {"n": 4}, None, "nc4"),
        (["n"], ["nc"], {"n": 0}, None, "nc0"),
        (["n"], ["nc"], {"n": -2}, None, "nc-2"),
        (["n"], ["nc"], {"n": 0.5}, None, "nc05"),  # il punto decimale sparisce
        (["n"], ["nc"], {"n": 1e-05}, None, "nc1e-05"),
        (["n"], ["nc"], {"n": True}, None, "ncTrue"),
        (["n"], ["nc"], {"n": None}, None, "ncNone"),
        (["n"], ["nc"], {"n": "a.b.c"}, None, "ncabc"),
        (["n"], ["nc"], {"n": [1, 2]}, None, "nc[1, 2]"),
        (["n"], [""], {"n": 7}, None, "7"),
        (["a", "b"], ["x", "y"], {"a": 1, "b": 2}, None, "x1_y2"),
        (["b", "a"], ["y", "x"], {"a": 1, "b": 2}, None, "y2_x1"),  # l'ordine e' quello di tag_param
        (["a", "b"], ["x", "y"], {"a": 1, "b": 2, "extra": 9}, None, "x1_y2"),  # chiavi non in tag_param ignorate
        (["a", "b"], ["x", "y"], {"a": 1, "b": 2}, {"a": 1}, "y2"),
        (["a", "b"], ["x", "y"], {"a": 1, "b": 2}, {"a": 99}, "x1_y2"),  # il valore diverso non viene omesso
        (["a", "b"], ["x", "y"], {"a": 1, "b": 2}, {"b": 2}, "x1"),
        (["a", "b"], ["x", "y"], {"a": "none", "b": 2}, {"a": "none"}, "y2"),
    ],
)
def test_tag_matrix(tmp_path, tag_param, tag_prefix, params, tag_omit, expected):
    entry = {"params": params, "tag_param": tag_param, "tag_prefix": tag_prefix}
    if tag_omit is not None:
        entry["tag_omit"] = tag_omit
    file = _write(str(tmp_path), {"m": entry})
    assert P.load_method_params(file, "m")[1] == expected
    # la stessa formula via load_tag_spec + build_tag_from_values
    spec = P.load_tag_spec(file, "m")
    assert P.build_tag_from_values(file, "m", *spec, params) == expected


@settings(max_examples=80)
@given(
    values=st.lists(st.one_of(st.integers(-1000, 1000), st.text(alphabet="abc._-", max_size=5), st.floats(allow_nan=False, allow_infinity=False)), min_size=1, max_size=4),
    prefixes=st.lists(st.text(alphabet="abcxyz", max_size=3), min_size=4, max_size=4),
)
def test_the_tag_is_the_underscore_join_of_prefix_plus_dotless_value(values, prefixes):
    names = [f"p{i}" for i in range(len(values))]
    prefixes = prefixes[: len(values)]
    params = dict(zip(names, values))
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {"m": {"params": params, "tag_param": names, "tag_prefix": prefixes}})
        tag = P.load_method_params(file, "m")[1]
    assert tag == "_".join(f"{prefix}{str(value).replace('.', '')}" for prefix, value in zip(prefixes, values))
    assert "." not in tag


@settings(max_examples=60)
@given(n=st.integers(1, 4), data=st.data())
def test_tag_omit_drops_exactly_the_parts_whose_value_matches_and_never_empties_the_tag(n, data):
    names = [f"p{i}" for i in range(n)]
    values = [data.draw(st.integers(0, 3)) for _ in names]
    omitted = [data.draw(st.booleans()) for _ in names]
    tag_omit = {name: value for name, value, drop in zip(names, values, omitted) if drop}
    entry = {"params": dict(zip(names, values)), "tag_param": names, "tag_prefix": [f"q{i}-" for i in range(n)], "tag_omit": tag_omit}
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {"m": entry})
        if all(omitted):
            with pytest.raises(ValueError, match="empty"):
                P.load_method_params(file, "m")
            return
        tag = P.load_method_params(file, "m")[1]
    kept = [f"q{i}-{value}" for i, (value, drop) in enumerate(zip(values, omitted)) if not drop]
    assert tag == "_".join(kept)


# ---- load_nested_params: oracolo sul numero di parametri liberi ------------------------------------------


@settings(max_examples=80)
@given(n_keys=st.integers(1, 5), data=st.data())
def test_nested_params_is_valid_iff_one_or_two_free_parameters_remain(n_keys, data):
    keys = [f"k{i}" for i in range(n_keys)]
    grid = {key: [1, 2] for key in keys}
    nested = data.draw(st.lists(st.sampled_from(keys), unique=True, max_size=n_keys))
    nested = data.draw(st.permutations(nested))
    free = n_keys - len(nested)
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {"m": {"nested_params": list(nested)}})
        if free in (1, 2):
            assert P.load_nested_params(file, "m", grid) == list(nested)  # stesso ordine, outermost first
        else:
            with pytest.raises(ValueError, match="free parameter"):
                P.load_nested_params(file, "m", grid)


@settings(max_examples=40)
@given(unknown=st.text(alphabet="xyz", min_size=1, max_size=3))
def test_nested_params_naming_a_key_outside_the_grid_is_rejected(unknown):
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {"m": {"nested_params": [unknown]}})
        with pytest.raises(ValueError, match="not present in tuning_grid"):
            P.load_nested_params(file, "m", {"a": [1], "b": [1]})


# ---- tuning_grid / trustworthiness: confini ---------------------------------------------------------------


@settings(max_examples=80)
@given(values=st.lists(st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False), st.text(max_size=4)), min_size=1, max_size=5, unique=True))
def test_a_grid_axis_of_plain_scalars_is_returned_unchanged(values):
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {"m": {"tuning_grid": {"x": values}}})
        assert P.load_tuning_grid(file, "m") == {"x": values}


@pytest.mark.parametrize("bad", [[[1]], [{"a": 1}], [1, [2]], [1, {}], [[]]])
def test_a_grid_axis_with_a_nested_container_is_a_valueerror_not_an_unhashable_typeerror(tmp_path, bad):
    file = _write(str(tmp_path), {"m": {"tuning_grid": {"x": bad}}})
    with pytest.raises(ValueError, match="non-hashable"):
        P.load_tuning_grid(file, "m")


@pytest.mark.parametrize("bad", [None, 3, "ab", {}, [], [1], {"x": []}, {"x": 3}, {"x": None}, {"x": "ab"}, {"x": {}}])
def test_a_malformed_tuning_grid_is_a_valueerror(tmp_path, bad):
    file = _write(str(tmp_path), {"m": {"tuning_grid": bad}})
    with pytest.raises(ValueError):
        P.load_tuning_grid(file, "m")


@pytest.mark.parametrize(
    "value, valid",
    [(1, True), (5, True), (10**18, True), (0, False), (-1, False), (True, False), (False, False), (1.0, False),
     (5.5, False), ("5", False), (None, False), ([5], False), ({}, False), (float("nan"), False), (float("inf"), False)],
)
def test_trustworthiness_n_neighbors_accepts_only_a_positive_int(tmp_path, value, valid):
    file = _write(str(tmp_path), {"m": {"trustworthiness_n_neighbors": value}})
    if valid:
        assert P.load_trustworthiness_n_neighbors(file, "m") == value
    else:
        with pytest.raises(ValueError, match="positive integer"):
            P.load_trustworthiness_n_neighbors(file, "m")


# ---- consensus / stability: matrici di confine -----------------------------------------------------------------


@pytest.mark.parametrize(
    "fraction, valid",
    [(0.5, True), (0.001, True), (0.999, True), (0.0, False), (1.0, False), (-0.1, False), (1.5, False), (float("nan"), False),
     (float("inf"), False), (True, False), (False, False), (None, False), ("0.5", False), ([0.5], False)],
)
def test_monti_subsample_fraction_is_an_open_interval_zero_one(tmp_path, fraction, valid):
    block = {"monti": {"n_repeats": 2, "subsample_fraction": fraction}}
    file = _write(str(tmp_path), {_METHOD: {"consensus": block}})
    if valid:
        assert P.load_consensus_config(file, _METHOD) == block
    else:
        with pytest.raises(ValueError, match="subsample_fraction"):
            P.load_consensus_config(file, _METHOD)


@pytest.mark.parametrize(
    "n_repeats, valid",
    [(1, True), (2, True), (10**9, True), (0, False), (-3, False), (True, False), (2.0, False), (None, False), ("2", False), ([2], False),
     (float("nan"), False)],
)
@pytest.mark.parametrize("kind", ["rsc", "monti"])
def test_consensus_n_repeats_is_a_positive_int_for_both_blocks(tmp_path, kind, n_repeats, valid):
    block = {"n_repeats": n_repeats}
    if kind == "monti":
        block["subsample_fraction"] = 0.5
    file = _write(str(tmp_path), {_METHOD: {"consensus": {kind: block}}})
    if valid:
        assert P.load_consensus_config(file, _METHOD) == {kind: block}
    else:
        with pytest.raises(ValueError, match="n_repeats"):
            P.load_consensus_config(file, _METHOD)


_ALL_METHOD_NAMES = ["umap", "tsne", "pca", "pacmap", "kmeans", "gmm", "agglomerative", "hdbscan", "hdbscan_soft", "spectral",
                     "adp", ""]


@pytest.mark.parametrize("method", _ALL_METHOD_NAMES)
def test_consensus_and_stability_eligibility_follows_the_registries_exactly(tmp_path, method):
    """Un blocco "consensus"/"stability" e' accettato solo per i metodi dei rispettivi insiemi di eleggibilita'."""
    file = _write(str(tmp_path), {method: {"consensus": {"rsc": {"n_repeats": 2}}, "stability": _VALID_ENTRY["stability"]}})
    if method in CONSENSUS_ELIGIBLE_METHODS:
        assert P.load_consensus_config(file, method) == {"rsc": {"n_repeats": 2}}
    else:
        with pytest.raises(ValueError, match="only defined for"):
            P.load_consensus_config(file, method)
    if method in STABILITY_ELIGIBLE_METHODS:
        assert P.load_stability_config(file, method) == _VALID_ENTRY["stability"]
    else:
        with pytest.raises(ValueError, match="only defined for"):
            P.load_stability_config(file, method)


@pytest.mark.parametrize("field, bad", [
    ("nuisance_values", []), ("nuisance_values", [1]), ("nuisance_values", ["a", 2]), ("nuisance_values", "ab"), ("nuisance_values", None),
    ("n_init_range", []), ("n_init_range", [0]), ("n_init_range", [True]), ("n_init_range", [1.0]), ("n_init_range", [-1, 2]), ("n_init_range", 3),
    ("n_repeats", 0), ("n_repeats", True), ("n_repeats", 2.5), ("n_repeats", None),
])
def test_stability_block_boundary_matrix(tmp_path, field, bad):
    block = {**_VALID_ENTRY["stability"], field: bad}
    file = _write(str(tmp_path), {_METHOD: {"stability": block}})
    with pytest.raises(ValueError, match=field):
        P.load_stability_config(file, _METHOD)


@settings(max_examples=80)
@given(extra=st.text(alphabet="abcdefg_", min_size=1, max_size=8))
def test_unknown_keys_in_consensus_and_stability_blocks_are_rejected(extra):
    stability_ok = {"nuisance_values", "n_init_range", "n_repeats"}
    with tempfile.TemporaryDirectory() as directory:
        file = _write(directory, {_METHOD: {"consensus": {"rsc": {"n_repeats": 2}, extra: {}}, "stability": {**_VALID_ENTRY["stability"], extra: 1}}})
        if extra != "monti":  # "monti" e' una chiave nota (qui con un blocco incompleto: errore comunque)
            with pytest.raises(ValueError, match="unknown key"):
                P.load_consensus_config(file, _METHOD)
        if extra not in stability_ok:
            with pytest.raises(ValueError, match="unknown key"):
                P.load_stability_config(file, _METHOD)


# ---- bug sospetti (lessons_learned #5): duplicati nelle liste di config silenziosamente accettati ----------------


def test_a_grid_axis_with_duplicate_values_is_rejected(tmp_path):
    file = _write(str(tmp_path), {"m": {"tuning_grid": {"n_components": [2, 2, 3]}}})
    with pytest.raises(ValueError, match="duplicate"):
        P.load_tuning_grid(file, "m")


def test_nested_params_with_a_repeated_name_is_rejected(tmp_path):
    file = _write(str(tmp_path), {"m": {"nested_params": ["a", "a"]}})
    with pytest.raises(ValueError, match="duplicate"):
        P.load_nested_params(file, "m", {"a": [1, 2], "b": [1], "c": [1]})


def test_tag_param_with_a_repeated_name_is_rejected(tmp_path):
    file = _write(str(tmp_path), {"m": {"params": {"a": 1}, "tag_param": ["a", "a"], "tag_prefix": ["x", "y"]}})
    with pytest.raises(ValueError, match="duplicate"):
        P.load_method_params(file, "m")
