"""Property tests for src/analysis/raw_distances.py.

Due cose da garantire per qualunque matrice: (1) la chiave di cache cambia quando cambia ciò da cui
la distanza dipende (contenuto, metrica, ordine/identità dei soggetti, shape, dtype) e solo allora;
(2) la matrice calcolata e salvata è esattamente quella di `pairwise_distance` sulle righe non vuote.
Il calcolo è chiamato direttamente (`_compute_into`/`_load`), senza il thread di background già
coperto da test_raw_distances.py: così ogni esempio è deterministico e istantaneo.
"""

import tempfile
import time
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.extra.numpy import arrays

from src.analysis.distances import pairwise_distance
from src.analysis.raw_distances import RawDistanceStore, _cache_key, _compute_into, _load

_METRICS = ["dice", "jaccard", "euclidean"]

_matrices = st.tuples(st.integers(1, 10), st.integers(1, 15)).flatmap(lambda s: arrays(np.uint8, s, elements=st.integers(0, 1)))


def _ids(n: int) -> list[str]:
    return [f"sub-STUNIPD{i:04d}" for i in range(n)]


def _computed(matrix: np.ndarray, metric: str):
    """(RawDistances) di una matrice salvata su disco, come fa request() ma senza thread."""
    with tempfile.TemporaryDirectory() as workdir:
        path = Path(workdir) / "matrix.npy"
        np.save(path, matrix)
        out = Path(workdir) / "entry"
        out.mkdir()
        _compute_into(out, path, metric)
        loaded = _load(out)
        return type(loaded)(non_empty=np.array(loaded.non_empty), distances=np.array(loaded.distances))


# --- _cache_key ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("metric", _METRICS)
@given(matrix=_matrices)
def test_the_cache_key_is_deterministic_and_prefixed_by_the_metric(metric, matrix):
    key = _cache_key(matrix, _ids(len(matrix)), metric)

    assert key == _cache_key(matrix.copy(), _ids(len(matrix)), metric)
    assert key.startswith(f"{metric}-")


@given(matrix=_matrices)
def test_the_cache_key_changes_with_the_metric(matrix):
    keys = {_cache_key(matrix, _ids(len(matrix)), metric) for metric in _METRICS}

    assert len(keys) == len(_METRICS)


@given(matrix=_matrices, data=st.data())
def test_the_cache_key_changes_when_a_sampled_row_changes(matrix, data):
    """Fino a 64 righe sono tutte campionate: una modifica di qualunque cella cambia la chiave."""
    row = data.draw(st.integers(0, matrix.shape[0] - 1))
    column = data.draw(st.integers(0, matrix.shape[1] - 1))
    changed = matrix.copy()
    changed[row, column] = 1 - changed[row, column]

    assert _cache_key(changed, _ids(len(matrix)), "dice") != _cache_key(matrix, _ids(len(matrix)), "dice")


@given(matrix=_matrices)
def test_the_cache_key_depends_on_the_subject_ids_and_their_order(matrix):
    ids = _ids(len(matrix))
    base = _cache_key(matrix, ids, "dice")

    assert _cache_key(matrix, [f"x{i}" for i in range(len(ids))], "dice") != base
    if len(ids) > 1:
        assert _cache_key(matrix, ids[::-1], "dice") != base


@given(matrix=_matrices)
def test_the_cache_key_depends_on_dtype_and_shape(matrix):
    ids = _ids(len(matrix))
    base = _cache_key(matrix, ids, "dice")

    assert _cache_key(matrix.astype(np.float32), ids, "dice") != base
    assert _cache_key(np.hstack([matrix, matrix[:, :1]]), ids, "dice") != base


def test_rows_beyond_the_sampled_ones_are_not_part_of_the_key():
    """Limite noto e documentato dal nome (_SAMPLED_ROWS): con più di 64 righe una cella fuori campione non cambia la chiave."""
    matrix = np.zeros((200, 4), dtype=np.uint8)
    matrix[:, 0] = 1
    changed = matrix.copy()
    sampled = set(np.linspace(0, 199, num=64, dtype=int).tolist())
    unsampled = next(i for i in range(200) if i not in sampled)
    changed[unsampled, 1] = 1

    assert _cache_key(changed, _ids(200), "dice") == _cache_key(matrix, _ids(200), "dice")


# --- contenuto della cache: _compute_into / _load -----------------------------------------------------------


@pytest.mark.parametrize("metric", _METRICS)
@given(matrix=_matrices, empty=st.lists(st.booleans(), min_size=10, max_size=10))
@settings(max_examples=30)
def test_the_stored_distances_are_those_of_the_non_empty_rows_and_the_mask_says_which(metric, matrix, empty):
    matrix = matrix.copy()
    matrix[np.asarray(empty[: len(matrix)])] = 0
    expected_mask = matrix.sum(axis=1) != 0
    if not expected_mask.any():
        return  # caso coperto dal test dedicato sotto

    result = _computed(matrix, metric)

    np.testing.assert_array_equal(result.non_empty, expected_mask)
    assert result.distances.shape == (int(expected_mask.sum()),) * 2
    np.testing.assert_allclose(result.distances, pairwise_distance(matrix[expected_mask], metric), atol=1e-12)
    assert np.isfinite(result.distances).all()
    np.testing.assert_array_equal(np.diag(result.distances), 0.0)


@pytest.mark.parametrize("metric", _METRICS)
def test_a_matrix_with_only_empty_rows_gives_an_empty_distance_matrix_and_an_all_false_mask(metric):
    result = _computed(np.zeros((4, 6), dtype=np.uint8), metric)

    assert not result.non_empty.any() and result.non_empty.shape == (4,)
    assert result.distances.shape == (0, 0)


@given(matrix=_matrices)
def test_dropping_empty_rows_does_not_change_the_distances_among_the_others(matrix):
    """La stessa matrice con righe vuote intercalate ha le stesse distanze fra le righe non vuote."""
    matrix = matrix.copy()
    matrix[0, 0] = 1
    padded = np.insert(matrix, 1, 0, axis=0)

    np.testing.assert_allclose(_computed(padded, "dice").distances, _computed(matrix, "dice").distances, atol=1e-12)


# --- request(): validazioni sincrone e metrica ignota -------------------------------------------------------


@pytest.mark.parametrize("shape", [(5,), (2, 3, 4)])
def test_request_rejects_a_matrix_that_is_not_two_dimensional(tmp_path, shape):
    path = tmp_path / "m.npy"
    np.save(path, np.ones(shape, dtype=np.uint8))

    with pytest.raises(ValueError, match="one row per subject id"):
        RawDistanceStore(tmp_path / "cache").request(path, _ids(shape[0]), "dice")


@pytest.mark.parametrize("metric", ["cosine", "manhattan", "Dice"])
def test_request_with_an_unsupported_metric_raises_value_error_instead_of_returning_a_matrix(tmp_path, metric):
    path = tmp_path / "m.npy"
    np.save(path, np.eye(4, dtype=np.uint8))
    store = RawDistanceStore(tmp_path / "cache")

    deadline = time.monotonic() + 30
    with pytest.raises(ValueError, match="unsupported metric"):
        while time.monotonic() < deadline:
            if store.request(path, _ids(4), metric) is not None:
                pytest.fail("a distance matrix was returned for an unsupported metric")
            time.sleep(0.05)
