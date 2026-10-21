"""Test a proprieta' di `src/utils/artifacts.py`: round-trip save_matrix -> load_matrix su dtype/shape
arbitrari, atomicita' sotto fallimenti di I/O, errori documentati, lettura di config.md."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.extra import numpy as hnp

from src.utils import artifacts
from src.utils.artifacts import (
    MANIFEST_FILENAME,
    MATRIX_FILENAME,
    METADATA_FILENAME,
    load_matrix,
    read_dim_reduction_method,
    read_run_config,
    read_run_params,
    save_matrix,
)

_RESERVED = sorted(artifacts._RESERVED_EXTRA_ARRAY_NAMES)

_NUMERIC_DTYPES = st.sampled_from(
    [np.float32, np.float64, np.int8, np.int32, np.int64, np.uint8, np.uint16, np.bool_]
)


# hnp.arrays genera anche NaN/inf nei float: np.save deve preservarli.
_MATRICES = st.tuples(st.integers(1, 6), st.integers(0, 6), _NUMERIC_DTYPES).flatmap(
    lambda t: hnp.arrays(dtype=t[2], shape=(t[0], t[1]))
)
_NAMES = st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True).filter(lambda n: n not in artifacts._RESERVED_EXTRA_ARRAY_NAMES)
_STR_ARRAYS = hnp.arrays(
    dtype=np.dtype("U6"),
    shape=hnp.array_shapes(min_dims=1, max_dims=1, max_side=5),
    elements=st.text(alphabet="abcXYZ_-0123456789", min_size=1, max_size=6),
)
_EXTRA = st.dictionaries(
    _NAMES,
    st.one_of(_STR_ARRAYS, hnp.arrays(dtype=_NUMERIC_DTYPES, shape=hnp.array_shapes(min_dims=1, max_dims=3, max_side=4))),
    max_size=3,
)


def _metadata(n: int, seed: int = 0, with_numeric: bool = True) -> pd.DataFrame:
    meta = pd.DataFrame(
        {"subject_id": [f"sub-STUNIPD{i:04d}" for i in range(n)], "dataset": [f"site{i % 3}" for i in range(n)]}
    )
    if with_numeric:
        rng = np.random.default_rng(seed)
        meta["n_voxels"] = np.arange(n, dtype=np.int64) * 7
        meta["frac"] = np.round(rng.random(n), 6)
        meta["flag"] = np.arange(n) % 2 == 0
    return meta


@given(X=_MATRICES, extra=_EXTRA, lines=st.lists(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=20), max_size=4))
def test_roundtrip_preserves_matrix_dtype_metadata_and_extra_arrays(X, extra, lines):
    meta = _metadata(len(X))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "run"
        assert save_matrix(out, X, meta, ["# title", *lines], overwrite=False, extra_arrays=extra) == out
        X2, meta2, extra2 = load_matrix(out)
        manifest = json.loads((out / MANIFEST_FILENAME).read_text())

    assert X2.dtype == X.dtype and X2.shape == X.shape
    np.testing.assert_array_equal(X2, X)  # NaN == NaN
    pd.testing.assert_frame_equal(meta2, meta)
    assert set(extra2) == set(extra)
    for name, arr in extra.items():
        assert extra2[name].dtype == arr.dtype
        np.testing.assert_array_equal(extra2[name], arr)
    assert manifest["matrix_shape"] == list(X.shape)
    assert manifest["matrix_dtype"] == str(X.dtype)
    assert manifest["metadata_columns"] == list(meta.columns)
    assert manifest["extra_arrays"] == {n: list(a.shape) for n, a in extra.items()}


@settings(max_examples=25)
@given(X=_MATRICES.filter(lambda a: a.size > 0))
def test_mmap_load_is_read_only_and_equal(X):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "run"
        save_matrix(out, X, _metadata(len(X)), ["x"], overwrite=False)
        X2, _, _ = load_matrix(out, mmap=True)
        assert isinstance(X2, np.memmap)
        assert not X2.flags.writeable
        np.testing.assert_array_equal(np.asarray(X2), X)
        del X2


@given(n_meta=st.integers(0, 8), n_rows=st.integers(1, 8))
def test_row_count_mismatch_raises_valueerror_and_creates_nothing(n_meta, n_rows):
    if n_meta == n_rows:
        return
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="rows"):
            save_matrix(Path(tmp) / "run", np.zeros((n_rows, 2)), _metadata(n_meta), ["x"], overwrite=False)
        assert list(Path(tmp).iterdir()) == []


@given(clash=st.lists(st.sampled_from(_RESERVED), min_size=1, max_size=4, unique=True), others=st.lists(_NAMES, max_size=2, unique=True))
def test_any_reserved_extra_array_name_raises_and_creates_nothing(clash, others):
    extra = {name: np.zeros(2) for name in [*clash, *others]}
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="reserved"):
            save_matrix(Path(tmp) / "run", np.zeros((2, 2)), _metadata(2), ["x"], overwrite=True, extra_arrays=extra)
        assert list(Path(tmp).iterdir()) == []


@given(X=_MATRICES)
def test_overwrite_false_on_existing_dir_raises_and_leaves_it_untouched(X):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "run"
        save_matrix(out, np.ones((2, 2)), _metadata(2), ["old"], overwrite=False)
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with pytest.raises(FileExistsError):
            save_matrix(out, X, _metadata(len(X)), ["new"], overwrite=False)
        assert {p.name: p.read_bytes() for p in out.iterdir()} == before


@given(X1=_MATRICES, X2=_MATRICES, extra1=_EXTRA, extra2=_EXTRA)
def test_overwrite_true_replaces_everything_without_leftovers_from_the_old_artifact(X1, X2, extra1, extra2):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "run"
        save_matrix(out, X1, _metadata(len(X1)), ["a"], overwrite=False, extra_arrays=extra1)
        save_matrix(out, X2, _metadata(len(X2)), ["b"], overwrite=True, extra_arrays=extra2)
        loaded, meta, loaded_extra = load_matrix(out)
        files = sorted(p.name for p in out.iterdir())
        siblings = sorted(p.name for p in Path(tmp).iterdir())

    np.testing.assert_array_equal(loaded, X2)
    assert len(meta) == len(X2)
    assert set(loaded_extra) == set(extra2)
    assert files == sorted([MANIFEST_FILENAME, MATRIX_FILENAME, METADATA_FILENAME, "config.md", *[f"{n}.npy" for n in extra2]])
    assert siblings == ["run"]


# --- atomicita' sotto fallimenti di I/O (si simula solo l'I/O esterno, mai save_matrix) -----------

_real_np_save = np.save
_real_write_text = Path.write_text


def _failing_save(fail_on: str, exc: BaseException):
    def save(file, arr, *a, **k):
        if Path(file).name == fail_on:
            raise exc
        return _real_np_save(file, arr, *a, **k)

    return save


def _failing_write_text(fail_on: str, exc: BaseException):
    def write_text(self, *a, **k):
        if self.name == fail_on:
            raise exc
        return _real_write_text(self, *a, **k)

    return write_text


_FAILURES = [
    ("np", "matrix.npy"),
    ("np", "extra1.npy"),
    ("text", "config.md"),
    ("text", "manifest.json"),
]


@pytest.mark.parametrize("exc", [OSError("disk full"), KeyboardInterrupt()], ids=["OSError", "KeyboardInterrupt"])
@pytest.mark.parametrize("kind,target", _FAILURES)
@pytest.mark.parametrize("had_previous", [False, True], ids=["fresh", "overwrite"])
def test_failure_midway_leaves_no_tmp_dir_and_the_previous_artifact_intact(tmp_path, kind, target, exc, had_previous):
    out = tmp_path / "run"
    old_X = np.arange(6, dtype=np.float32).reshape(3, 2)
    if had_previous:
        save_matrix(out, old_X, _metadata(3), ["old"], overwrite=False, extra_arrays={"extra1": np.arange(3)})
        before = {p.name: p.read_bytes() for p in out.iterdir()}

    patcher = (
        mock.patch.object(artifacts.np, "save", _failing_save(target, exc))
        if kind == "np"
        else mock.patch.object(Path, "write_text", _failing_write_text(target, exc))
    )
    with patcher, pytest.raises(type(exc)):
        save_matrix(out, np.ones((2, 2)), _metadata(2), ["new"], overwrite=True, extra_arrays={"extra1": np.zeros(2)})

    leftovers = sorted(p.name for p in tmp_path.iterdir())
    if had_previous:
        assert leftovers == ["run"]
        assert {p.name: p.read_bytes() for p in out.iterdir()} == before
        np.testing.assert_array_equal(load_matrix(out)[0], old_X)
    else:
        assert leftovers == []  # ne' output_dir ne' directory temporanee `.run_tmp_*`


# --- load_matrix: errori documentati ----------------------------------------------------------

@pytest.mark.parametrize("missing", [MANIFEST_FILENAME, MATRIX_FILENAME, METADATA_FILENAME, "extra1.npy"])
def test_load_with_a_missing_file_raises_filenotfounderror(tmp_path, missing):
    out = tmp_path / "run"
    save_matrix(out, np.ones((2, 2)), _metadata(2), ["x"], overwrite=False, extra_arrays={"extra1": np.zeros(2)})
    (out / missing).unlink()
    with pytest.raises(FileNotFoundError):
        load_matrix(out)


@given(cut=st.floats(0.05, 0.95), mmap=st.booleans())
@settings(max_examples=30)
def test_truncated_matrix_file_never_loads_silently(cut, mmap):
    """Una matrice troncata deve far fallire il caricamento, non restituire una matrice piu' corta."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "run"
        save_matrix(out, np.arange(60, dtype=np.float64).reshape(10, 6), _metadata(10), ["x"], overwrite=False)
        raw = (out / MATRIX_FILENAME).read_bytes()
        (out / MATRIX_FILENAME).write_bytes(raw[: max(1, int(len(raw) * cut))])
        with pytest.raises((ValueError, EOFError, OSError)):
            X, _, _ = load_matrix(out, mmap=mmap)
            np.asarray(X).copy()  # con mmap il difetto puo' emergere solo alla lettura


@pytest.mark.parametrize("text", ["", "{", "not json", '{"matrix_shape": [1,'])
def test_corrupt_manifest_raises_valueerror(tmp_path, text):
    out = tmp_path / "run"
    save_matrix(out, np.ones((2, 2)), _metadata(2), ["x"], overwrite=False)
    (out / MANIFEST_FILENAME).write_text(text)
    with pytest.raises(ValueError):  # json.JSONDecodeError e' una sottoclasse
        load_matrix(out)


def test_manifest_without_extra_arrays_key_raises(tmp_path):
    out = tmp_path / "run"
    save_matrix(out, np.ones((2, 2)), _metadata(2), ["x"], overwrite=False, extra_arrays={"extra1": np.zeros(2)})
    manifest = json.loads((out / MANIFEST_FILENAME).read_text())
    del manifest["extra_arrays"]
    (out / MANIFEST_FILENAME).write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_matrix(out)


@pytest.mark.parametrize("payload", ["[]", "5", "null", '"text"'])
def test_manifest_with_non_object_json_raises_valueerror(tmp_path, payload):
    out = tmp_path / "run"
    save_matrix(out, np.ones((2, 2)), _metadata(2), ["x"], overwrite=False)
    (out / MANIFEST_FILENAME).write_text(payload)
    with pytest.raises(ValueError):
        load_matrix(out)


@pytest.mark.parametrize("subject_id", ["007", "0012", "NA", "null"])
def test_roundtrip_of_numeric_looking_subject_ids(tmp_path, subject_id):
    meta = pd.DataFrame({"subject_id": [subject_id, "0123"], "dataset": ["a", "b"]})
    save_matrix(tmp_path / "run", np.ones((2, 2)), meta, ["x"], overwrite=False)
    _, meta2, _ = load_matrix(tmp_path / "run")
    assert list(meta2["subject_id"]) == list(meta["subject_id"])


# --- config.md: read_run_params / read_run_config / read_dim_reduction_method --------------------

_JSON = st.recursive(
    st.none() | st.booleans() | st.integers(-10**12, 10**12) | st.floats(allow_nan=False, allow_infinity=False) | st.text(max_size=12),
    lambda c: st.lists(c, max_size=3) | st.dictionaries(st.text(max_size=8), c, max_size=3),
    max_leaves=8,
)
_PARAMS = st.dictionaries(st.text(max_size=8), _JSON, max_size=4)
_NOISE_LINE = st.text(alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\r\x0b\x0c\x1c\x1d\x1e\x85  \n"), max_size=25).filter(
    lambda s: not s.startswith("Params used: ")
)


@given(params=_PARAMS, before=st.lists(_NOISE_LINE, max_size=3), after=st.lists(_NOISE_LINE, max_size=3))
def test_read_run_params_roundtrips_json_at_any_line_position(params, before, after):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "config.md").write_text("\n".join([*before, "Params used: " + json.dumps(params), *after]) + "\n")
        assert read_run_params(Path(tmp)) == params


@given(config=_PARAMS, before=st.lists(_NOISE_LINE.filter(lambda s: "```" not in s and "## Config" not in s), max_size=3))
def test_read_run_config_roundtrips_indented_fenced_block(config, before):
    body = "\n".join([*before, "## Config", "```json", json.dumps(config, indent=2), "```", "trailing"]) + "\n"
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "config.md").write_text(body)
        assert read_run_config(Path(tmp)) == config


@given(st.lists(_NOISE_LINE, max_size=5))
def test_run_readers_without_their_marker_raise_valueerror(lines):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "config.md").write_text("\n".join(lines) + "\n")
        for reader in (read_run_params, read_run_config):
            with pytest.raises(ValueError):
                reader(Path(tmp))


@pytest.mark.parametrize("payload", ["{", "nope", "{'a': 1}", ""])
def test_read_run_params_with_invalid_json_raises_valueerror(tmp_path, payload):
    (tmp_path / "config.md").write_text("Params used: " + payload + "\n")
    with pytest.raises(ValueError):
        read_run_params(tmp_path)


@pytest.mark.parametrize("payload", ["[1, 2]", "5", "null", '"s"'])
def test_read_run_params_with_non_object_json_raises(tmp_path, payload):
    (tmp_path / "config.md").write_text("Params used: " + payload + "\n")
    with pytest.raises(ValueError):
        read_run_params(tmp_path)


@pytest.mark.parametrize("payload", ["[1, 2]", "5", "null", '"s"'])
def test_read_run_config_with_non_object_json_raises(tmp_path, payload):
    (tmp_path / "config.md").write_text(f"## Config\n```json\n{payload}\n```\n")
    with pytest.raises(ValueError):
        read_run_config(tmp_path)


_METHOD = st.from_regex(r"[A-Za-z0-9_+\- ]{1,15}", fullmatch=True)


@given(project=st.text(alphabet="abcdefXYZ0123456789_- ", max_size=15), method=_METHOD, stamp=st.text(alphabet="0123456789-: ", max_size=16))
def test_read_dim_reduction_method_roundtrips_title(project, method, stamp):
    title = f"# {project} dim_reduction ({method}) — {stamp}"
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "config.md").write_text(title + "\nbody (other)\n")
        assert read_dim_reduction_method(Path(tmp)) == method


@given(title=st.text(alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\r\n\x0b\x0c\x1c\x1d\x1e\x85  "), max_size=30).filter(lambda t: " dim_reduction (" not in t))
def test_read_dim_reduction_method_with_other_titles_raises_even_if_body_has_the_pattern(title):
    """Conta solo la prima riga: lo stesso pattern piu' in basso non salva un titolo sbagliato."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "config.md").write_text(title + "\n# x dim_reduction (umap) y\n")
        with pytest.raises(ValueError):
            read_dim_reduction_method(Path(tmp))


@given(st.sampled_from([read_run_params, read_run_config, read_dim_reduction_method]))
def test_run_readers_on_a_dir_without_config_md_raise_valueerror(reader):
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="config.md"):
            reader(Path(tmp))
