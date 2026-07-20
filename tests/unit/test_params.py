"""Unit tests for src/analysis/params.py."""

import json

import pytest

from src.analysis.params import load_method_params


def _write(tmp_path, payload):
    path = tmp_path / "params.json"
    path.write_text(json.dumps(payload))
    return path


def test_load_method_params_valid(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {"n_neighbors": 15}}, "tsne": {"params": {"perplexity": 30}}})
    assert load_method_params(path, "umap") == {"n_neighbors": 15}
    assert load_method_params(path, "tsne") == {"perplexity": 30}


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
