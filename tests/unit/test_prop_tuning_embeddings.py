"""Test a proprietà / parametrici di src/analysis/tuning_embeddings.py.

Convenzioni su disco di una run di tuning: `combo_key`/`parse_combo_key`, `leaf_dir`, il blocco json di
`config.md` e `load_tuning_run`. Contratto dichiarato: `FileNotFoundError` / `ValueError` con il path esatto e
il pezzo mancante (docstring di `read_tuning_config_block`/`load_tuning_run`) - mai `TypeError` (lesson #7, #8).
"""

from __future__ import annotations

import itertools
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import tuning_embeddings as TE

_NAME = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=6)
_SAFE_VALUE = st.one_of(st.integers(-50, 50), st.floats(allow_nan=False, allow_infinity=False, width=32), st.booleans(),
                        st.text(alphabet="abcxyz-_.", min_size=1, max_size=5))


def _write_config(directory: Path, block: object, prefix: str = "# tuning\n\n", suffix: str = "\n\nfine\n") -> Path:
    path = directory / TE.CONFIG_FILENAME
    path.write_text(f"{prefix}```json\n{json.dumps(block)}\n```{suffix}")
    return path


_DEFAULT = object()


def _valid_block(grid: object = _DEFAULT, nested: object = _DEFAULT) -> dict:
    return {
        "reduction_method": "umap",
        "base_params": {"random_state": 0},
        "tuning_grid": {"a": [1, 2], "b": ["x", "y"]} if grid is _DEFAULT else grid,
        "nested_params": [] if nested is _DEFAULT else nested,
    }


# ---- combo_key / parse_combo_key ------------------------------------------------------------------------------------------


@settings(max_examples=100)
@given(names=st.lists(_NAME, min_size=1, max_size=5, unique=True), data=st.data())
def test_parse_combo_key_inverts_combo_key_preserving_names_order_and_str_values(names, data):
    values = [data.draw(_SAFE_VALUE) for _ in names]
    key = TE.combo_key(names, values)
    parsed = TE.parse_combo_key(key)
    assert list(parsed) == names  # stesso ordine
    assert list(parsed.values()) == [str(v) for v in values]
    # e il percorso inverso: ricostruire la chiave dal parse restituisce la stessa stringa
    assert TE.combo_key(list(parsed), list(parsed.values())) == key


@pytest.mark.parametrize(
    "keys, combo, expected",
    [
        (["a"], [1], "a=1"),
        (["a", "b"], [True, None], "a=True,b=None"),
        (["metric", "n"], ["dice", 10], "metric=dice,n=10"),
        (["x"], [0.1], "x=0.1"),
        (["x"], [1e-05], "x=1e-05"),
        (["x"], [-0.0], "x=-0.0"),
        ([], [], ""),
        (["a", "b"], [1], "a=1"),  # zip tronca: documenta la lunghezza minima
    ],
)
def test_combo_key_matrix(keys, combo, expected):
    assert TE.combo_key(keys, combo) == expected


@pytest.mark.parametrize("key", ["", "a", "=1", "a=", "a=1,b", "a=1,,b=2", "a==1", "a=1=2", ",a=1", "a=1,", "a=1,=2"])
def test_parse_combo_key_rejects_every_part_that_is_not_exactly_one_name_value_pair(key):
    if key == "a=":
        assert TE.parse_combo_key(key) == {"a": ""}  # un valore vuoto e' ben formato: coppia con valore ""
        return
    with pytest.raises(ValueError, match="malformed combination key"):
        TE.parse_combo_key(key)


@settings(max_examples=60)
@given(text=st.text(max_size=20))
def test_parse_combo_key_returns_a_dict_or_raises_valueerror_on_arbitrary_text(text):
    try:
        parsed = TE.parse_combo_key(text)
    except ValueError:
        return
    assert all(name and "=" not in value for name, value in parsed.items())
    assert all("," not in name and "," not in value for name, value in parsed.items())


def test_parse_combo_key_rejects_a_repeated_name():
    with pytest.raises(ValueError):
        TE.parse_combo_key("a=1,a=2")


# ---- expected_combo_keys -------------------------------------------------------------------------------------------------------


@settings(max_examples=80)
@given(grid=st.dictionaries(_NAME, st.lists(st.integers(0, 9), min_size=1, max_size=4, unique=True), min_size=1, max_size=4))
def test_expected_combo_keys_is_the_cartesian_product_with_distinct_keys(grid):
    keys = TE.expected_combo_keys(grid)
    assert len(keys) == math.prod(len(v) for v in grid.values())
    names = list(grid)
    assert all(list(TE.parse_combo_key(k)) == names for k in keys)  # ogni chiave ha tutti i nomi, nell'ordine della griglia
    for combo in itertools.product(*grid.values()):
        assert TE.combo_key(names, combo) in keys


def test_expected_combo_keys_of_an_empty_grid_is_the_single_empty_key():
    assert TE.expected_combo_keys({}) == {""}


@pytest.mark.parametrize("grid, n", [({"a": [1, 1]}, 1), ({"a": [1, 1], "b": [2, 2, 3]}, 2), ({"a": [1, "1"]}, 1), ({"a": [True, 1]}, 2)])
def test_expected_combo_keys_collapses_values_with_the_same_text(grid, n):
    """Documenta il comportamento: e' un insieme di stringhe, quindi 1 e '1' (stesso str) valgono una combinazione sola."""
    assert len(TE.expected_combo_keys(grid)) == n


# ---- leaf_dir ----------------------------------------------------------------------------------------------------------------------


@settings(max_examples=60)
@given(nested=st.lists(_NAME, max_size=4, unique=True), values=st.lists(_SAFE_VALUE, min_size=4, max_size=4))
def test_leaf_dir_has_one_level_per_nested_param_in_order(nested, values):
    root = Path("run")
    leaf = dict(zip(nested, values))
    path = TE.leaf_dir(root, nested, leaf)
    assert path.parts[: len(root.parts)] == root.parts
    assert list(path.relative_to(root).parts) == [f"{name}={leaf[name]}" for name in nested]


def test_leaf_dir_ignores_leaf_keys_that_are_not_nested_and_a_nested_level_without_value_is_a_keyerror():
    assert TE.leaf_dir(Path("r"), ["a"], {"a": 1, "zzz": 9}) == Path("r/a=1")
    with pytest.raises(KeyError):  # un livello senza valore e' un errore di programmazione del chiamante, non un default
        TE.leaf_dir(Path("r"), ["a", "b"], {"a": 1})


# ---- read_tuning_config_block --------------------------------------------------------------------------------------------------------


@settings(max_examples=60)
@given(prefix=st.text(alphabet="abc \n#-.", max_size=30), suffix=st.text(alphabet="abc \n#-.", max_size=30))
def test_the_json_block_is_found_regardless_of_the_prose_around_it(prefix, suffix):
    with tempfile.TemporaryDirectory() as directory:
        path = _write_config(Path(directory), _valid_block(), prefix=prefix + "\n", suffix="\n" + suffix)
        assert TE.read_tuning_config_block(path) == _valid_block()


def test_only_the_first_json_block_is_read():
    with tempfile.TemporaryDirectory() as directory:
        path = _write_config(Path(directory), _valid_block(), suffix="\n\n```json\n{\"reduction_method\": \"other\"}\n```\n")
        assert TE.read_tuning_config_block(path)["reduction_method"] == "umap"


@pytest.mark.parametrize("missing", ["reduction_method", "base_params", "tuning_grid", "nested_params"])
def test_every_required_field_is_named_when_missing(missing):
    block = _valid_block()
    del block[missing]
    with tempfile.TemporaryDirectory() as directory:
        path = _write_config(Path(directory), block)
        with pytest.raises(ValueError, match=missing) as excinfo:
            TE.read_tuning_config_block(path)
        assert str(path) in str(excinfo.value)  # il path esatto, come promette la docstring


@pytest.mark.parametrize("grid", [{}, [], None, "a", 3, [["a", [1]]]])
def test_tuning_grid_that_is_not_a_non_empty_object_is_a_valueerror(grid):
    with tempfile.TemporaryDirectory() as directory:
        path = _write_config(Path(directory), _valid_block(grid=grid))
        with pytest.raises(ValueError, match="tuning_grid"):
            TE.read_tuning_config_block(path)


@pytest.mark.parametrize("nested", [["zzz"], ["a", "zzz"], ["B"]])
def test_nested_params_naming_a_key_outside_the_grid_is_a_valueerror(nested):
    with tempfile.TemporaryDirectory() as directory:
        path = _write_config(Path(directory), _valid_block(nested=nested))
        with pytest.raises(ValueError, match="nested_params"):
            TE.read_tuning_config_block(path)


@pytest.mark.parametrize("text", ["no block here", "```python\nx=1\n```", "", "```\n{}\n```"])
def test_a_config_without_a_json_fence_is_a_valueerror(text, tmp_path):
    path = tmp_path / TE.CONFIG_FILENAME
    path.write_text(text)
    with pytest.raises(ValueError, match="no ```json config block"):
        TE.read_tuning_config_block(path)


@pytest.mark.parametrize("body", ["{not json", "{'a': 1}", "{\"a\": }", "[1, 2", ""])
def test_malformed_json_inside_the_fence_is_a_valueerror(body, tmp_path):
    path = tmp_path / TE.CONFIG_FILENAME
    path.write_text(f"```json\n{body}\n```")
    with pytest.raises(ValueError):  # json.JSONDecodeError
        TE.read_tuning_config_block(path)


def test_a_missing_config_is_a_filenotfounderror_naming_the_path(tmp_path):
    with pytest.raises(FileNotFoundError, match="tuning config not found"):
        TE.read_tuning_config_block(tmp_path / "config.md")
    with pytest.raises(FileNotFoundError):
        TE.read_tuning_config_block(tmp_path)  # una cartella


# ---- bug sospetti (lessons_learned #7, #8): forma del blocco json non validata prima dell'uso ----------------------------------------


@pytest.mark.parametrize("block", [5, None, True, 3.5])
def test_a_json_block_that_is_not_an_object_is_a_valueerror(block, tmp_path):
    path = _write_config(tmp_path, block)
    with pytest.raises(ValueError):
        TE.read_tuning_config_block(path)


@pytest.mark.parametrize("nested", [None, 5, [[1]], [{"a": 1}], True])
def test_nested_params_of_the_wrong_type_is_a_valueerror(nested, tmp_path):
    path = _write_config(tmp_path, _valid_block(nested=nested))
    with pytest.raises(ValueError):
        TE.read_tuning_config_block(path)


@pytest.mark.parametrize("axis", [5, None, 2.5, True])
def test_a_grid_axis_that_is_not_a_list_is_a_valueerror(axis, tmp_path):
    _write_config(tmp_path, _valid_block(grid={"a": axis}))
    np.savez(tmp_path / TE.EMBEDDINGS_FILENAME, **{"a=1": np.zeros((3, 2))})
    with pytest.raises(ValueError):
        TE.load_tuning_run(tmp_path)


@pytest.mark.parametrize("field, value", [("reduction_method", 5), ("reduction_method", None), ("reduction_method", ""), ("base_params", [1]), ("base_params", None)])
def test_reduction_method_and_base_params_are_type_checked(field, value, tmp_path):
    block = _valid_block()
    block[field] = value
    path = _write_config(tmp_path, block)
    with pytest.raises(ValueError):
        TE.read_tuning_config_block(path)


# ---- load_tuning_run -----------------------------------------------------------------------------------------------------------------------


def _write_run(directory: Path, grid: dict, nested: list | None = None, keys: set[str] | None = None) -> dict[str, np.ndarray]:
    _write_config(directory, _valid_block(grid=grid, nested=_DEFAULT if nested is None else nested))
    names = list(grid)
    expected = keys if keys is not None else {TE.combo_key(names, combo) for combo in itertools.product(*grid.values())}
    arrays = {key: np.full((4, 2), float(i)) for i, key in enumerate(sorted(expected))}
    np.savez(directory / TE.EMBEDDINGS_FILENAME, **arrays)
    return arrays


_GRIDS = st.dictionaries(_NAME, st.lists(st.integers(0, 9), min_size=1, max_size=3, unique=True), min_size=1, max_size=3)


@settings(max_examples=40)
@given(grid=_GRIDS)
def test_a_run_whose_npz_matches_the_grid_roundtrips_every_array(grid):
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        arrays = _write_run(directory, grid)
        run = TE.load_tuning_run(directory)
        assert set(run.embeddings) == set(arrays)
        assert all(np.array_equal(run.embeddings[k], arrays[k]) for k in arrays)
        assert run.tuning_grid == grid and run.reduction_method == "umap" and run.run_dir == directory


@settings(max_examples=40)
@given(grid=_GRIDS, data=st.data())
def test_dropping_any_one_combination_from_the_npz_is_a_valueerror_naming_it(grid, data):
    expected = sorted(TE.expected_combo_keys(grid))
    drop = data.draw(st.sampled_from(expected))
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        _write_run(directory, grid, keys=set(expected) - {drop})
        with pytest.raises(ValueError, match="1 combination") as excinfo:
            TE.load_tuning_run(directory)
        assert drop in str(excinfo.value)


@settings(max_examples=40)
@given(grid=_GRIDS, extra=st.text(alphabet="qrs", min_size=1, max_size=4))
def test_an_extra_array_in_the_npz_is_a_valueerror(grid, extra):
    expected = TE.expected_combo_keys(grid)
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        _write_run(directory, grid, keys=expected | {f"{extra}=1"})
        with pytest.raises(ValueError, match="unexpected"):
            TE.load_tuning_run(directory)


def test_a_grid_widened_after_the_run_is_detected(tmp_path):
    """lessons_learned #18: config.md descrive solo l'ultimo writer; le chiavi del npz sono la verita'."""
    _write_run(tmp_path, {"a": [1, 2]})
    _write_config(tmp_path, _valid_block(grid={"a": [1, 2, 3]}))
    with pytest.raises(ValueError, match="does not match the tuning_grid"):
        TE.load_tuning_run(tmp_path)


def test_nested_params_are_returned_as_a_fresh_list_in_declared_order(tmp_path):
    _write_run(tmp_path, {"a": [1, 2], "b": [3, 4]}, nested=["b", "a"])
    run = TE.load_tuning_run(tmp_path)
    assert run.nested_params == ["b", "a"]
    assert isinstance(run.nested_params, list)


def test_missing_embeddings_or_config_are_filenotfounderrors_with_the_exact_path(tmp_path):
    with pytest.raises(FileNotFoundError, match="embeddings.npz"):
        TE.load_tuning_run(tmp_path)
    np.savez(tmp_path / TE.EMBEDDINGS_FILENAME, x=np.zeros(2))
    with pytest.raises(FileNotFoundError, match="config"):
        TE.load_tuning_run(tmp_path)


@pytest.mark.parametrize("keep", [0, 10, "half"])
def test_a_truncated_npz_is_reported_as_a_domain_error_naming_the_file(keep, tmp_path):
    arrays = _write_run(tmp_path, {"a": [1, 2]})
    raw = (tmp_path / TE.EMBEDDINGS_FILENAME).read_bytes()
    cut = len(raw) // 2 if keep == "half" else keep
    (tmp_path / TE.EMBEDDINGS_FILENAME).write_bytes(raw[:cut])
    with pytest.raises((ValueError, OSError)) as excinfo:
        TE.load_tuning_run(tmp_path)
    assert TE.EMBEDDINGS_FILENAME in str(excinfo.value)
    assert arrays  # usata
