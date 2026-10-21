"""Unit tests for src/analysis/model_config.py."""

import json
from pathlib import Path

import pytest

from src.analysis.model_config import (
    load_evaluate_clustering_tuning_config,
    load_clustering_config,
    load_dim_reduction_config,
    load_evaluate_dim_reduction_tuning_config,
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
        "save_tuning_embeddings": False,
        "precompute_distance_metric": True,
        "tuning_evaluations": {"trustworthiness": {}, "plot_hdbscan": {"min_cluster_size": 100, "min_samples": 10}},
        "write_report": False,
    }
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", payload))
    assert config.tuning_evaluations == {
        "trustworthiness": {},
        "plot_hdbscan": {"min_cluster_size": 100, "min_samples": 10},
    }
    assert config.reduction_method == "umap"
    assert config.fine_tuning is False
    assert config.color_by == ("dataset", "volume")
    assert config.viz_n_components == 2
    assert config.save_tuning_embeddings is False
    assert config.precompute_distance_metric is True
    assert config.run_notes is None


def test_dim_reduction_config_with_run_notes(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "params_file": "config/registry/params_reduction.json",
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "save_tuning_embeddings": False,
        "precompute_distance_metric": True,
        "tuning_evaluations": {"trustworthiness": {}},
        "write_report": False,
        "run_notes": "provo n_neighbors piu alto",
    }
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", payload))
    assert config.fine_tuning is True
    assert config.run_notes == "provo n_neighbors piu alto"


def test_dim_reduction_config_missing_tuning_evaluations_raises(tmp_path):
    payload = _dr_payload()
    del payload["tuning_evaluations"]
    with pytest.raises(ValueError, match="missing required field 'tuning_evaluations'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


@pytest.mark.parametrize(
    "bad_block, message",
    [
        ([], "must be an object"),
        ({"bogus": {}}, "unknown tuning evaluation 'bogus'"),
        ({"plot_hdbscan": []}, "must be an object of settings"),
        ({"plot_hdbscan": {"min_cluster_size": 100}}, "missing \\['min_samples'\\]"),
        ({"plot_hdbscan": {"min_cluster_size": 100, "min_samples": 10, "typo": 1}}, "unknown \\['typo'\\]"),
        ({"plot_hdbscan": {"min_cluster_size": 1, "min_samples": 10}}, "'min_cluster_size'\\] must be an integer >= 2"),
        ({"plot_hdbscan": {"min_cluster_size": True, "min_samples": 10}}, "must be an integer >= 2"),
        ({"trustworthiness": {"n_neighbors": 10}}, "takes no settings here"),
    ],
)
def test_dim_reduction_config_invalid_tuning_evaluations_raises(tmp_path, bad_block, message):
    with pytest.raises(ValueError, match=message):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(tuning_evaluations=bad_block)))


def test_evaluate_dim_reduction_tuning_config_valid(tmp_path):
    payload = {
        "tuning_dir": "results/lesion/dim_reduction/tuning/umap/07-10_s1.4-vol",
        "overwrite": False,
        "tuning_evaluations": {"plot_hdbscan": {"min_cluster_size": 100, "min_samples": 10}},
        "write_report": False,
    }
    config = load_evaluate_dim_reduction_tuning_config(_write(tmp_path, "ev.json", payload))
    assert config.tuning_dir == Path("results/lesion/dim_reduction/tuning/umap/07-10_s1.4-vol")
    assert config.overwrite is False
    assert config.tuning_evaluations == payload["tuning_evaluations"]


def test_evaluate_dim_reduction_tuning_config_rejects_sweep_score(tmp_path):
    """trustworthiness needs the original matrix, which this entry point never loads - rejected
    at load time instead of being silently skipped."""
    payload = {
        "tuning_dir": "x",
        "overwrite": False,
        "tuning_evaluations": {"trustworthiness": {}, "plot_hdbscan": {"min_cluster_size": 100, "min_samples": 10}},
        "write_report": False,
    }
    with pytest.raises(ValueError, match="'trustworthiness'\\] is a sweep_score and cannot be run here"):
        load_evaluate_dim_reduction_tuning_config(_write(tmp_path, "ev.json", payload))


def test_evaluate_dim_reduction_tuning_config_empty_block_raises(tmp_path):
    payload = {"tuning_dir": "x", "overwrite": False, "tuning_evaluations": {}}
    with pytest.raises(ValueError, match="at least one evaluation"):
        load_evaluate_dim_reduction_tuning_config(_write(tmp_path, "ev.json", payload))


@pytest.mark.parametrize("missing", ["tuning_dir", "overwrite", "tuning_evaluations"])
def test_evaluate_dim_reduction_tuning_config_missing_field_raises(tmp_path, missing):
    payload = {"tuning_dir": "x", "overwrite": False, "tuning_evaluations": {"plot_hdbscan": {"min_cluster_size": 100, "min_samples": 10}}}
    del payload[missing]
    with pytest.raises(ValueError, match=f"missing required field '{missing}'"):
        load_evaluate_dim_reduction_tuning_config(_write(tmp_path, "ev.json", payload))


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
        "save_tuning_embeddings": False,
        "precompute_distance_metric": True,
        "tuning_evaluations": {},
        "write_report": False,
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


def test_dim_reduction_config_missing_save_tuning_embeddings_raises(tmp_path):
    payload = _dr_payload()
    del payload["save_tuning_embeddings"]
    with pytest.raises(ValueError, match="missing required field 'save_tuning_embeddings'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_save_tuning_embeddings_non_bool_raises(tmp_path):
    with pytest.raises(ValueError, match="field 'save_tuning_embeddings' must be a boolean"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(save_tuning_embeddings="true")))


def test_dim_reduction_config_missing_precompute_distance_metric_raises(tmp_path):
    payload = _dr_payload()
    del payload["precompute_distance_metric"]
    with pytest.raises(ValueError, match="missing required field 'precompute_distance_metric'"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", payload))


def test_dim_reduction_config_precompute_distance_metric_non_bool_raises(tmp_path):
    with pytest.raises(ValueError, match="field 'precompute_distance_metric' must be a boolean"):
        load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(precompute_distance_metric="true")))


def test_dim_reduction_config_precompute_distance_metric_false_valid(tmp_path):
    config = load_dim_reduction_config(_write(tmp_path, "dr.json", _dr_payload(precompute_distance_metric=False)))
    assert config.precompute_distance_metric is False


def test_clustering_config_valid(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.clustering_methods == ("kmeans",)
    assert config.reduction_method == "umap"
    assert config.fine_tuning is False
    assert config.reduced_data is False


def test_clustering_config_reduction_method_raw_valid(tmp_path):
    """"raw" is the explicit sentinel for clustering directly on an un-reduced feature
    matrix (docs/dev/clustering_migration_plan.md §1's reduced_data=False case) - not yet
    a real scenario in this project (every clustering run so far reduces first), but the
    field must accept it since it's the documented escape hatch, not just REDUCTION_METHODS'
    own entries."""
    payload = {
        **_SHARED,
        "reduction_method": "raw",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.reduction_method == "raw"


def test_clustering_config_missing_reduction_method_raises(tmp_path):
    payload = {
        **_SHARED,
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    with pytest.raises(ValueError, match="missing required field 'reduction_method'"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_unknown_reduction_method_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "bogus",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    with pytest.raises(ValueError, match="unknown reduction_method"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_reduced_data_true_valid(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "reduction_params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.reduced_data is True
    assert str(config.reduction_params_file) == "config/registry/params_reduction.json"


def test_clustering_config_reduced_data_true_missing_reduction_params_file_raises(tmp_path):
    """reduction_params_file is required exactly when reduced_data is True (31-08-26,
    tag-params-multi-key session) - without it, clustering.py has no registry to read
    input_path's own tag_param/tag_prefix from for the embedding tag."""
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    with pytest.raises(ValueError, match="'reduction_params_file' is required when reduced_data=true"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_reduced_data_false_with_reduction_params_file_raises(tmp_path):
    """The reverse case: reduction_params_file has nothing to describe when reduced_data is
    False (input_path is a raw feature matrix) - forbidden rather than silently ignored, so
    the field never sits unread (code_standards.md §5)."""
    payload = {
        **_SHARED,
        "reduction_method": "raw",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "reduction_params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    with pytest.raises(ValueError, match="'reduction_params_file' must be omitted when reduced_data=false"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_missing_reduced_data_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="missing required field 'reduced_data'"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_reduced_data_non_bool_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
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
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "reduction_params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.viz_embedding_path is None


def test_clustering_config_viz_embedding_path_set(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "reduction_params_file": "config/registry/params_reduction.json",
        "fine_tuning": False,
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
        "viz_embedding_path": "results/lesion/dim_reduction/production/umap/23-07_s1.1_d00",
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert str(config.viz_embedding_path) == "results/lesion/dim_reduction/production/umap/23-07_s1.1_d00"


def test_clustering_config_save_tuning_clusterings_true_valid(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": True,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": [], "kmeans": []},
        "write_report": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.save_tuning_clusterings is True


def test_clustering_config_missing_save_tuning_clusterings_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
    }
    with pytest.raises(ValueError, match="missing required field 'save_tuning_clusterings'"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_save_tuning_clusterings_non_bool_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": "true",
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    with pytest.raises(ValueError, match="field 'save_tuning_clusterings' must be a boolean"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_multiple_methods_valid(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans", "hdbscan", "gmm"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": []},
        "write_report": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.clustering_methods == ("kmeans", "hdbscan", "gmm")


def test_clustering_config_fine_tuning_true(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": [], "kmeans": []},
        "write_report": False,
    }
    config = load_clustering_config(_write(tmp_path, "cl.json", payload))
    assert config.fine_tuning is True


def test_clustering_config_missing_fine_tuning_raises(tmp_path):
    payload = {**_SHARED, "reduction_method": "umap", "clustering_methods": ["kmeans"], "params_file": "config/registry/params_clustering.json"}
    with pytest.raises(ValueError, match="missing required field 'fine_tuning'"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_unknown_method_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["bogus"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="unknown clustering_method"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_duplicate_methods_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["kmeans", "kmeans"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="duplicate entries"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_empty_list_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": [],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": False,
    }
    with pytest.raises(ValueError, match="non-empty list"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_non_list_raises(tmp_path):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
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


def _analyze_payload(**overrides):
    payload = {
        "tuning_dir": "results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_m_dice_nc2",
        "overwrite": False,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": [], "agglomerative": ["cophenetic_correlation", "dendrogram_jump"]},
        "write_report": True,
    }
    payload.update(overrides)
    return payload


def test_evaluate_clustering_tuning_config_valid(tmp_path):
    config = load_evaluate_clustering_tuning_config(_write(tmp_path, "an.json", _analyze_payload()))

    assert config.tuning_dir == Path("results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_m_dice_nc2")
    assert config.evaluations_file == Path("config/registry/clustering_evaluations.json")
    assert config.tuning_evaluations == {"general": (), "agglomerative": ("cophenetic_correlation", "dendrogram_jump")}
    assert config.write_report is True


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"tuning_evaluations": {"agglomerative": []}}, "needs a 'general' key"),
        ({"tuning_evaluations": {"general": [], "agglomerative": ["density_metrics"]}}, "does not apply"),
        ({"tuning_evaluations": {"general": [], "agglomerative": ["nope"]}}, "unknown clustering tuning evaluation"),
        ({"tuning_evaluations": ["cophenetic_correlation"]}, "must be an object"),
        ({"write_report": "yes"}, "'write_report' must be a boolean"),
        ({"overwrite": "no"}, "'overwrite' must be a boolean"),
    ],
)
def test_evaluate_clustering_tuning_config_invalid_raises(tmp_path, overrides, message):
    with pytest.raises(ValueError, match=message):
        load_evaluate_clustering_tuning_config(_write(tmp_path, "an.json", _analyze_payload(**overrides)))


@pytest.mark.parametrize("field", ["evaluations_file", "tuning_evaluations", "write_report"])
def test_evaluate_clustering_tuning_config_has_no_defaults(tmp_path, field):
    payload = _analyze_payload()
    del payload[field]

    with pytest.raises(ValueError, match=f"missing required field '{field}'"):
        load_evaluate_clustering_tuning_config(_write(tmp_path, "an.json", payload))


def _clustering_tuning_payload(**overrides):
    payload = {
        **_SHARED,
        "reduction_method": "umap",
        "clustering_methods": ["agglomerative", "hdbscan"],
        "params_file": "config/registry/params_clustering.json",
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": True,
        "evaluations_file": "config/registry/clustering_evaluations.json",
        "tuning_evaluations": {"general": [], "agglomerative": ["k_curves"], "hdbscan": ["density_metrics"]},
        "write_report": False,
    }
    payload.update(overrides)
    return payload


def test_clustering_config_reads_the_tuning_evaluations_block(tmp_path):
    config = load_clustering_config(_write(tmp_path, "cl.json", _clustering_tuning_payload()))

    assert config.evaluations_file == Path("config/registry/clustering_evaluations.json")
    assert config.tuning_evaluations == {"general": (), "agglomerative": ("k_curves",), "hdbscan": ("density_metrics",)}


def test_clustering_tuning_needs_a_key_for_every_method(tmp_path):
    payload = _clustering_tuning_payload(tuning_evaluations={"general": [], "agglomerative": []})

    with pytest.raises(ValueError, match=r"no key for \['hdbscan'\]"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_a_production_config_needs_no_key_per_method(tmp_path):
    payload = _clustering_tuning_payload(fine_tuning=False, tuning_evaluations={"general": []})

    assert load_clustering_config(_write(tmp_path, "cl.json", payload)).tuning_evaluations == {"general": ()}


def test_clustering_tuning_evaluations_need_the_labels_saved(tmp_path):
    payload = _clustering_tuning_payload(save_tuning_clusterings=False)

    with pytest.raises(ValueError, match="save_tuning_clusterings"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_tuning_without_evaluations_does_not_need_the_labels_saved(tmp_path):
    payload = _clustering_tuning_payload(
        save_tuning_clusterings=False, tuning_evaluations={"general": [], "agglomerative": [], "hdbscan": []}
    )

    assert load_clustering_config(_write(tmp_path, "cl.json", payload)).save_tuning_clusterings is False


def test_clustering_config_write_report_needs_the_evaluations_the_report_reads(tmp_path):
    payload = _clustering_tuning_payload(write_report=True)

    with pytest.raises(ValueError, match=r"write_report is true but tuning_evaluations lacks .* for 'agglomerative'"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_write_report_refuses_a_method_with_no_report(tmp_path):
    payload = _clustering_tuning_payload(
        write_report=True, clustering_methods=["kmeans"], tuning_evaluations={"general": [], "kmeans": []}
    )

    with pytest.raises(ValueError, match="'kmeans' has no report"):
        load_clustering_config(_write(tmp_path, "cl.json", payload))


def test_clustering_config_write_report_valid_with_the_evaluations_listed(tmp_path):
    payload = _clustering_tuning_payload(
        write_report=True,
        clustering_methods=["hdbscan"],
        tuning_evaluations={"general": [], "hdbscan": ["density_metrics"]},
    )

    assert load_clustering_config(_write(tmp_path, "cl.json", payload)).write_report is True


def test_a_production_config_with_write_report_is_not_checked_against_the_evaluations(tmp_path):
    payload = _clustering_tuning_payload(fine_tuning=False, write_report=True, tuning_evaluations={"general": []})

    assert load_clustering_config(_write(tmp_path, "cl.json", payload)).write_report is True
