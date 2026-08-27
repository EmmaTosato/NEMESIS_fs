"""Unit tests for src/analysis/params.py."""

import json

import pytest

from src.analysis.params import (
    load_consensus_config,
    load_method_params,
    load_nested_params,
    load_stability_config,
    load_trustworthiness_n_neighbors,
    load_tuning_grid,
)


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


def test_load_tuning_grid_nested_list_value_raises(tmp_path):
    """AUDIT_FINDINGS.md #56 regression: a value list with a nested list/object element
    (e.g. a typo'd extra bracket, [5, 15, [30]] instead of [5, 15, 30]) used to pass this
    validation (it's still a non-empty list) and only fail much later with a cryptic
    `TypeError: unhashable type: 'list'` from itertools.product/tuple(combo_values), the
    first time that value was used as a dict key."""
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": {"n_neighbors": [5, 15, [30]]}}})
    with pytest.raises(ValueError, match="non-hashable value"):
        load_tuning_grid(path, "umap")


def test_load_tuning_grid_nested_dict_value_raises(tmp_path):
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": {"metric": [{"bad": "value"}]}}})
    with pytest.raises(ValueError, match="non-hashable value"):
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


def test_load_nested_params_absent_returns_empty_list(tmp_path):
    path = _write(tmp_path, {"pca": {"params": {}, "tuning_grid": {"n_components": [2, 4]}}})
    assert load_nested_params(path, "pca", {"n_components": [2, 4]}) == []


def test_load_nested_params_valid(tmp_path):
    tuning_grid = {"metric": ["euclidean", "jaccard"], "n_components": [2, 5], "n_neighbors": [5, 15], "min_dist": [0.0, 0.1]}
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": tuning_grid, "nested_params": ["metric", "n_components"]}})
    assert load_nested_params(path, "umap", tuning_grid) == ["metric", "n_components"]


def test_load_nested_params_not_a_list_raises(tmp_path):
    tuning_grid = {"metric": ["euclidean", "jaccard"], "n_neighbors": [5, 15]}
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": tuning_grid, "nested_params": "metric"}})
    with pytest.raises(ValueError, match="must be a list of strings"):
        load_nested_params(path, "umap", tuning_grid)


def test_load_nested_params_unknown_reference_raises(tmp_path):
    tuning_grid = {"metric": ["euclidean", "jaccard"], "n_neighbors": [5, 15]}
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": tuning_grid, "nested_params": ["typo_metric"]}})
    with pytest.raises(ValueError, match="not present in tuning_grid"):
        load_nested_params(path, "umap", tuning_grid)


def test_load_nested_params_zero_free_params_raises(tmp_path):
    tuning_grid = {"metric": ["euclidean", "jaccard"]}
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": tuning_grid, "nested_params": ["metric"]}})
    with pytest.raises(ValueError, match="must be exactly 1 or 2"):
        load_nested_params(path, "umap", tuning_grid)


def test_load_nested_params_too_many_free_params_raises(tmp_path):
    tuning_grid = {
        "metric": ["euclidean", "jaccard"],
        "a": [1, 2],
        "b": [1, 2],
        "c": [1, 2],
    }
    path = _write(tmp_path, {"umap": {"params": {}, "tuning_grid": tuning_grid, "nested_params": ["metric"]}})
    with pytest.raises(ValueError, match="must be exactly 1 or 2"):
        load_nested_params(path, "umap", tuning_grid)


# --- load_consensus_config -------------------------------------------------------
# AUDIT_FINDINGS.md #69 (found 22/08 while triaging an unrelated stale git stash):
# load_consensus_config/consensus_suggestion_lines/run_clustering_tuning_sweep's
# consensus_config path are all already implemented and used in production
# (src/analysis/consensus_clustering.py's RSC/Monti), but had no direct unit test
# coverage at all before this - only indirectly exercised if a real config happened to
# set a "consensus" block, which none of the checked-in production configs do.


def test_load_consensus_config_absent_returns_none(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}}})
    assert load_consensus_config(path, "kmeans") is None


def test_load_consensus_config_valid(tmp_path):
    path = _write(
        tmp_path,
        {
            "kmeans": {
                "params": {},
                "consensus": {"rsc": {"n_repeats": 200}, "monti": {"n_repeats": 200, "subsample_fraction": 0.8}},
            }
        },
    )
    consensus = load_consensus_config(path, "kmeans")
    assert consensus == {"rsc": {"n_repeats": 200}, "monti": {"n_repeats": 200, "subsample_fraction": 0.8}}


def test_load_consensus_config_rsc_only(tmp_path):
    path = _write(tmp_path, {"spectral": {"params": {}, "consensus": {"rsc": {"n_repeats": 50}}}})
    assert load_consensus_config(path, "spectral") == {"rsc": {"n_repeats": 50}}


def test_load_consensus_config_rejects_ineligible_method(tmp_path):
    """hdbscan (agglomerative/hdbscan's replacement for the deterministic-methods case,
    lessons_learned.md #12) has no genuine internal stochasticity to repeat - a "consensus"
    block for it must raise, not silently no-op or produce a degenerate co-occurrence
    matrix."""
    path = _write(tmp_path, {"hdbscan": {"params": {}, "consensus": {"rsc": {"n_repeats": 200}}}})
    with pytest.raises(ValueError, match="only.*defined for"):
        load_consensus_config(path, "hdbscan")


def test_load_consensus_config_rejects_unknown_key(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}, "consensus": {"bogus": {}}}})
    with pytest.raises(ValueError, match="unknown key"):
        load_consensus_config(path, "kmeans")


def test_load_consensus_config_rejects_non_dict(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}, "consensus": "not-a-dict"}})
    with pytest.raises(ValueError, match="must be a non-empty JSON object"):
        load_consensus_config(path, "kmeans")


def test_load_consensus_config_rejects_bad_n_repeats(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}, "consensus": {"rsc": {"n_repeats": 0}}}})
    with pytest.raises(ValueError, match="n_repeats must be a positive integer"):
        load_consensus_config(path, "kmeans")

    path2 = _write(tmp_path, {"kmeans": {"params": {}, "consensus": {"rsc": {"n_repeats": True}}}})
    with pytest.raises(ValueError, match="n_repeats must be a positive integer"):
        load_consensus_config(path2, "kmeans")


def test_load_consensus_config_rejects_bad_subsample_fraction(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}, "consensus": {"monti": {"n_repeats": 5, "subsample_fraction": 1.5}}}})
    with pytest.raises(ValueError, match="subsample_fraction must be in"):
        load_consensus_config(path, "kmeans")


# --- load_stability_config ---------------------------------------------------------
# project-clustering-tuning-redesign memory (26-08-26): kmeans/gmm's init/n_init
# stability-analysis diagnostic config block.


def test_load_stability_config_absent_returns_none(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}}})
    assert load_stability_config(path, "kmeans") is None


def test_load_stability_config_valid(tmp_path):
    path = _write(
        tmp_path,
        {"kmeans": {"params": {}, "stability": {"nuisance_values": ["k-means++", "random"], "n_init_range": [1, 5, 10], "n_repeats": 5}}},
    )
    assert load_stability_config(path, "kmeans") == {
        "nuisance_values": ["k-means++", "random"],
        "n_init_range": [1, 5, 10],
        "n_repeats": 5,
    }


def test_load_stability_config_rejects_ineligible_method(tmp_path):
    path = _write(
        tmp_path,
        {"agglomerative": {"params": {}, "stability": {"nuisance_values": ["a"], "n_init_range": [1], "n_repeats": 1}}},
    )
    with pytest.raises(ValueError, match="only.*defined for"):
        load_stability_config(path, "agglomerative")


def test_load_stability_config_rejects_unknown_key(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}, "stability": {"bogus": 1}}})
    with pytest.raises(ValueError, match="unknown key"):
        load_stability_config(path, "kmeans")


def test_load_stability_config_rejects_bad_nuisance_values(tmp_path):
    path = _write(tmp_path, {"kmeans": {"params": {}, "stability": {"nuisance_values": [], "n_init_range": [1], "n_repeats": 1}}})
    with pytest.raises(ValueError, match="nuisance_values must be a non-empty list"):
        load_stability_config(path, "kmeans")


def test_load_stability_config_rejects_bad_n_init_range(tmp_path):
    path = _write(
        tmp_path, {"kmeans": {"params": {}, "stability": {"nuisance_values": ["random"], "n_init_range": [0], "n_repeats": 1}}}
    )
    with pytest.raises(ValueError, match="n_init_range must be a non-empty list of positive integers"):
        load_stability_config(path, "kmeans")


def test_load_stability_config_rejects_bad_n_repeats(tmp_path):
    path = _write(
        tmp_path, {"kmeans": {"params": {}, "stability": {"nuisance_values": ["random"], "n_init_range": [1], "n_repeats": 0}}}
    )
    with pytest.raises(ValueError, match="n_repeats must be a positive integer"):
        load_stability_config(path, "kmeans")
