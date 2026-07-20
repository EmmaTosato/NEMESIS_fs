"""Unit tests for src/analysis/model_config.py."""

import json

import pytest

from src.analysis.model_config import (
    load_clustering_config,
    load_dim_reduction_clustering_config,
    load_dim_reduction_config,
)

_SHARED = {
    "project": "clinical_connectome",
    "input_path": "data/derived/lesion_matrix/run1",
    "output_root": "results/x",
    "run_name": "run1",
    "overwrite": False,
}


def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload))
    return path


def test_dim_reduction_config_valid(tmp_path):
    payload = {**_SHARED, "reduction_method": "umap", "params_file": "config/registry/params_reduction.json"}
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", payload))
    assert config.reduction_method == "umap"


def test_dim_reduction_config_unknown_method_raises(tmp_path):
    payload = {**_SHARED, "reduction_method": "bogus", "params_file": "config/registry/params_reduction.json"}
    with pytest.raises(ValueError, match="unknown reduction_method"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_clustering_config_valid(tmp_path):
    payload = {**_SHARED, "clustering_method": "kmeans", "params_file": "config/registry/params_clustering.json"}
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.clustering_method == "kmeans"


def test_clustering_config_unknown_method_raises(tmp_path):
    payload = {**_SHARED, "clustering_method": "bogus", "params_file": "config/registry/params_clustering.json"}
    with pytest.raises(ValueError, match="unknown clustering_method"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_dim_reduction_clustering_config_valid(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "tsne",
        "reduction_params_file": "config/registry/params_reduction.json",
        "clustering_method": "kmeans",
        "clustering_params_file": "config/registry/params_clustering.json",
    }
    config = load_dim_reduction_clustering_config(_write(tmp_path, "drc.json", payload))
    assert config.reduction_method == "tsne"
    assert config.clustering_method == "kmeans"
    assert str(config.reduction_params_file) == "config/registry/params_reduction.json"
    assert str(config.clustering_params_file) == "config/registry/params_clustering.json"


def test_missing_required_field_raises(tmp_path):
    payload = {"project": "x"}
    with pytest.raises(ValueError, match="missing required field"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dim_reduction_config(tmp_path / "nope.json")
