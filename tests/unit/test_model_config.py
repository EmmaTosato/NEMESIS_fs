"""Unit tests for src/analysis/model_config.py."""

import json

import pytest

from src.analysis.model_config import (
    load_clustering_config,
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
        "color_by": ["dataset", "volume"],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
    }
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", payload))
    assert config.reduction_method == "umap"
    assert config.fine_tuning is False
    assert config.color_by == ("dataset", "volume")
    assert config.viz_n_components == 2
    assert config.write_embeddings_grid is True
    assert config.save_tuning_embeddings is False
    assert config.run_notes is None


def test_dim_reduction_config_with_run_notes(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
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
    }
    with pytest.raises(ValueError, match="unknown reduction_method"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def _dr_payload(**overrides):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
    }
    payload.update(overrides)
    return payload


def test_dim_reduction_config_color_by_empty_list_valid(tmp_path):
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(color_by=[])))
    assert config.color_by == ()


def test_dim_reduction_config_missing_color_by_raises(tmp_path):
    payload = _dr_payload()
    del payload["color_by"]
    with pytest.raises(ValueError, match="missing required field 'color_by'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_color_by_non_list_raises(tmp_path):
    with pytest.raises(ValueError, match="field 'color_by' must be a list"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(color_by="dataset")))


def test_dim_reduction_config_color_by_duplicate_raises(tmp_path):
    with pytest.raises(ValueError, match="duplicate entries"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(color_by=["dataset", "dataset"])))


def test_dim_reduction_config_missing_viz_n_components_raises(tmp_path):
    payload = _dr_payload()
    del payload["viz_n_components"]
    with pytest.raises(ValueError, match="missing required field 'viz_n_components'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_viz_n_components_must_be_2_or_3(tmp_path):
    with pytest.raises(ValueError, match="field 'viz_n_components' must be 2 or 3"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(viz_n_components=4)))


def test_dim_reduction_config_viz_n_components_rejects_bool(tmp_path):
    with pytest.raises(ValueError, match="field 'viz_n_components' must be 2 or 3"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(viz_n_components=True)))


def test_dim_reduction_config_missing_write_embeddings_grid_raises(tmp_path):
    payload = _dr_payload()
    del payload["write_embeddings_grid"]
    with pytest.raises(ValueError, match="missing required field 'write_embeddings_grid'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_write_embeddings_grid_non_bool_raises(tmp_path):
    with pytest.raises(ValueError, match="field 'write_embeddings_grid' must be a boolean"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(write_embeddings_grid="true")))


def test_dim_reduction_config_missing_save_tuning_embeddings_raises(tmp_path):
    payload = _dr_payload()
    del payload["save_tuning_embeddings"]
    with pytest.raises(ValueError, match="missing required field 'save_tuning_embeddings'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_save_tuning_embeddings_non_bool_raises(tmp_path):
    with pytest.raises(ValueError, match="field 'save_tuning_embeddings' must be a boolean"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(save_tuning_embeddings="true")))


def test_clustering_config_valid(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.clustering_methods == ("kmeans",)
    assert config.fine_tuning is False
    assert config.reduced_data is False


def test_clustering_config_reduced_data_true_valid(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": True,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.reduced_data is True


def test_clustering_config_missing_reduced_data_raises(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="missing required field 'reduced_data'"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_reduced_data_non_bool_raises(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": "true",
    }
    with pytest.raises(ValueError, match="field 'reduced_data' must be a boolean"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_viz_embedding_path_defaults_to_none(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": True,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.viz_embedding_path is None


def test_clustering_config_viz_embedding_path_set(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": True,
        "viz_embedding_path": "results/lesion/dim_reduction/production/umap/23-07_s1.1_d00",
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert str(config.viz_embedding_path) == "results/lesion/dim_reduction/production/umap/23-07_s1.1_d00"


def test_clustering_config_multiple_methods_valid(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans", "hdbscan", "gmm"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.clustering_methods == ("kmeans", "hdbscan", "gmm")


def test_clustering_config_fine_tuning_true(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": True,
        "reduced_data": False,
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


def test_missing_required_field_raises(tmp_path):
    payload = {"project": "x"}
    with pytest.raises(ValueError, match="missing required field"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dim_reduction_config(tmp_path / "nope.json")
