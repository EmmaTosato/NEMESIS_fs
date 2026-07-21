"""Unit tests for src/analysis/params.py."""

import json

import pytest

from src.analysis.params import load_method_params, load_trustworthiness_n_neighbors, load_tuning_grid


def _write(tmp_path, payload):
    path = tmp_path / "params.json"
    path.write_text(json.dumps(payload))
    return path


def test_load_method_params_valid(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {"n_neighbors": 15}}, "tsne": {"params": {"perplexity": 30}}})
    assert load_method_params(path, "umap") == ({"n_neighbors": 15}, None)
    assert load_method_params(path, "tsne") == ({"perplexity": 30}, None)


def test_unknown_method_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}}})
    with pytest.raises(ValueError, match="no entry for method"):
        load_method_params(path, "pca")


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_method_params(tmp_path / "nope.json", "umap")


def test_missing_params_key_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"not_params": {}}})
    with pytest.raises(ValueError, match="must be a JSON object with a 'params' key"):
        load_method_params(path, "umap")


def test_non_dict_params_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"params": "not-a-dict"}})
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_method_params(path, "umap")


def test_non_dict_top_level_raises(tmp_path):
    path = tmp_path / "params.json"
    path.write_text(json.dumps(["not", "a", "dict"]))
    with pytest.raises(ValueError, match="top-level content must be a JSON object"):
        load_method_params(path, "umap")


def test_load_tuning_grid_valid(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": {"n_neighbors": [5, 15], "min_dist": [0.1, 0.5]}}})
    grid = load_tuning_grid(path, "umap")
    assert grid == {"n_neighbors": [5, 15], "min_dist": [0.1, 0.5]}


def test_load_tuning_grid_missing_raises(tmp_path):
    path = _write(tmp_path, {"tsne": {"params": {}}})
    with pytest.raises(ValueError, match="no 'tuning_grid' entry"):
        load_tuning_grid(path, "tsne")


def test_load_tuning_grid_empty_value_list_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": {"n_neighbors": []}}})
    with pytest.raises(ValueError, match="must be a non-empty list"):
        load_tuning_grid(path, "umap")


def test_load_tuning_grid_non_dict_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": "not-a-dict"}})
    with pytest.raises(ValueError, match="must be a non-empty JSON object"):
        load_tuning_grid(path, "umap")


def test_load_trustworthiness_n_neighbors_valid(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}, "trustworthiness_n_neighbors": 10}})
    assert load_trustworthiness_n_neighbors(path, "umap") == 10


def test_load_trustworthiness_n_neighbors_missing_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}}})
    with pytest.raises(ValueError, match="no 'trustworthiness_n_neighbors' entry"):
        load_trustworthiness_n_neighbors(path, "umap")


def test_load_trustworthiness_n_neighbors_not_positive_int_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}, "trustworthiness_n_neighbors": 0}})
    with pytest.raises(ValueError, match="must be a positive integer"):
        load_trustworthiness_n_neighbors(path, "umap")

    path2 = _write(tmp_path, {"umap": {"params": {}, "trustworthiness_n_neighbors": True}})
    with pytest.raises(ValueError, match="must be a positive integer"):
        load_trustworthiness_n_neighbors(path2, "umap")
