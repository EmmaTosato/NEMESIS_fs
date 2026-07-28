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
    "session_name": "run1",
    "overwrite": False,
}


def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload))
    return path


def test_dim_reduction_config_valid(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "regress_out_volume": False,
    }
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", payload))
    assert config.reduction_method == "umap"
    assert config.fine_tuning is False
    assert config.regress_out_volume is False
    assert config.run_notes is None


def test_dim_reduction_config_with_run_notes(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": True,
        "regress_out_volume": False,
        "run_notes": "provo n_neighbors piu alto",
    }
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", payload))
    assert config.fine_tuning is True
    assert config.run_notes == "provo n_neighbors piu alto"


def test_dim_reduction_config_missing_fine_tuning_raises(tmp_path):
    payload = {**_SHARED, "reduction_method": "umap", "params_file": "config/registry/params_reduction.json"}
    with pytest.raises(ValueError, match="missing required field 'fine_tuning'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_unknown_method_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "bogus",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "regress_out_volume": False,
    }
    with pytest.raises(ValueError, match="unknown reduction_method"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_regress_out_volume_true(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "regress_out_volume": True,
    }
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", payload))
    assert config.regress_out_volume is True


def test_dim_reduction_config_missing_regress_out_volume_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="missing required field 'regress_out_volume'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_non_bool_regress_out_volume_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "regress_out_volume": "true",
    }
    with pytest.raises(ValueError, match="field 'regress_out_volume' must be a boolean"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_clustering_config_valid(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.clustering_methods == ("kmeans",)
    assert config.fine_tuning is False


def test_clustering_config_multiple_methods_valid(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans", "dbscan", "gmm"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.clustering_methods == ("kmeans", "dbscan", "gmm")


def test_clustering_config_fine_tuning_true(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": True,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.fine_tuning is True


def test_clustering_config_missing_fine_tuning_raises(tmp_path):
    payload = {**_SHARED, "clustering_methods": ["kmeans"], "params_file": "config/registry/params_clustering.json"}
    with pytest.raises(ValueError, match="missing required field 'fine_tuning'"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_unknown_method_raises(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["bogus"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="unknown clustering_method"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_duplicate_methods_raises(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans", "kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="duplicate entries"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_empty_list_raises(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": [],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="non-empty list"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_non_list_raises(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": "kmeans",
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="non-empty list"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_dim_reduction_clustering_config_valid(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "tsne",
        "reduction_params_file": "config/registry/params_reduction.json",
        "clustering_methods": ["kmeans"],
        "clustering_params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "regress_out_volume": False,
    }
    config = load_dim_reduction_clustering_config(_write(tmp_path, "drc.json", payload))
    assert config.reduction_method == "tsne"
    assert config.clustering_methods == ("kmeans",)
    assert str(config.reduction_params_file) == "config/registry/params_reduction.json"
    assert str(config.clustering_params_file) == "config/registry/params_clustering.json"
    assert config.fine_tuning is False
    assert config.regress_out_volume is False


def test_dim_reduction_clustering_config_missing_fine_tuning_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "tsne",
        "reduction_params_file": "config/registry/params_reduction.json",
        "clustering_methods": ["kmeans"],
        "clustering_params_file": "config/registry/params_clustering.json",
    }
    with pytest.raises(ValueError, match="missing required field 'fine_tuning'"):
        load_dim_reduction_clustering_config(_write(tmp_path, "drc.json", payload))


def test_dim_reduction_clustering_config_missing_regress_out_volume_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "tsne",
        "reduction_params_file": "config/registry/params_reduction.json",
        "clustering_methods": ["kmeans"],
        "clustering_params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="missing required field 'regress_out_volume'"):
        load_dim_reduction_clustering_config(_write(tmp_path, "drc.json", payload))


def test_missing_required_field_raises(tmp_path):
    payload = {"project": "x"}
    with pytest.raises(ValueError, match="missing required field"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dim_reduction_config(tmp_path / "nope.json")
