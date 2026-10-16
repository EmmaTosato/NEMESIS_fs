"""Unit tests for src/analysis/raw_distances.py."""

import time

import numpy as np
import pytest

from src.analysis import raw_distances
from src.analysis.distances import pairwise_distance
from src.analysis.raw_distances import RawDistanceStore


def _matrix() -> np.ndarray:
    rng = np.random.default_rng(0)
    matrix = (rng.random((8, 40)) > 0.6).astype(np.uint8)
    matrix[3] = 0  # an all-zero row: its dice distance is undefined, so it is left out
    return matrix


def _save(tmp_path, matrix, name="matrix.npy"):
    path = tmp_path / name
    np.save(path, matrix)
    return path, [f"sub-{i}" for i in range(len(matrix))]


def _wait_for(store, path, ids, metric="dice", timeout=30.0):
    """request() until the background computation is done (it returns None while it runs)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = store.request(path, ids, metric)
        if result is not None:
            return result
        time.sleep(0.05)
    raise AssertionError("the distances were not ready in time")


def test_the_distances_are_those_of_the_non_empty_subjects_and_the_mask_says_which(tmp_path):
    matrix = _matrix()
    path, ids = _save(tmp_path, matrix)

    result = _wait_for(RawDistanceStore(tmp_path / "cache"), path, ids)

    expected_mask = np.array([i != 3 for i in range(8)])
    assert (result.non_empty == expected_mask).all()
    assert np.allclose(result.distances, pairwise_distance(matrix[expected_mask], "dice"))
    assert result.distances.shape == (7, 7)


def test_a_second_store_reads_the_entry_from_disk_without_computing(tmp_path, monkeypatch):
    path, ids = _save(tmp_path, _matrix())
    first = _wait_for(RawDistanceStore(tmp_path / "cache"), path, ids)

    def refuse(*_args, **_kwargs):
        raise AssertionError("the cached entry must not be recomputed")

    monkeypatch.setattr(raw_distances, "pairwise_distance", refuse)
    second = RawDistanceStore(tmp_path / "cache").request(path, ids, "dice")  # no waiting: it is on disk

    assert second is not None and np.array_equal(second.distances, first.distances)


def test_a_matrix_with_other_content_gets_its_own_entry_not_a_stale_one(tmp_path):
    matrix = _matrix()
    path_a, ids = _save(tmp_path, matrix, "a.npy")
    corrected = matrix.copy()
    corrected[0] = 1 - corrected[0]  # row 0 is always among the sampled rows
    path_b, _ = _save(tmp_path, corrected, "b.npy")
    store = RawDistanceStore(tmp_path / "cache")

    result_a = _wait_for(store, path_a, ids)
    result_b = _wait_for(store, path_b, ids)

    assert len([d for d in (tmp_path / "cache").iterdir() if d.is_dir()]) == 2
    assert not np.allclose(result_a.distances, result_b.distances)


def test_the_same_matrix_under_another_metric_is_a_separate_entry(tmp_path):
    path, ids = _save(tmp_path, _matrix())
    store = RawDistanceStore(tmp_path / "cache")

    _wait_for(store, path, ids, "dice")
    _wait_for(store, path, ids, "jaccard")

    assert sorted(d.name.split("-")[0] for d in (tmp_path / "cache").iterdir()) == ["dice", "jaccard"]


def test_a_failed_computation_raises_once_leaves_no_entry_and_is_retried(tmp_path, monkeypatch):
    path, ids = _save(tmp_path, _matrix())
    store = RawDistanceStore(tmp_path / "cache")
    real = raw_distances.pairwise_distance

    def fail(*_args, **_kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(raw_distances, "pairwise_distance", fail)
    with pytest.raises(ValueError, match="boom"):
        _wait_for(store, path, ids)
    assert list(tmp_path.glob("cache/*")) == []  # neither the entry nor a leftover temporary directory

    monkeypatch.setattr(raw_distances, "pairwise_distance", real)
    assert _wait_for(store, path, ids).distances.shape == (7, 7)


def test_a_subject_list_that_does_not_match_the_rows_raises(tmp_path):
    path, ids = _save(tmp_path, _matrix())

    with pytest.raises(ValueError, match="one row per subject id"):
        RawDistanceStore(tmp_path / "cache").request(path, ids[:-1], "dice")
