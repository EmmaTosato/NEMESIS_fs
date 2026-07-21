"""Unit tests for src/analysis/tuning.py."""

import numpy as np
import pytest

from src.analysis.tuning import (
    TUNING_METRIC_NAMES,
    evaluate_pacmap,
    evaluate_pca,
    evaluate_pca_varimax,
    evaluate_umap,
    run_tuning_sweep,
)

_X = np.random.default_rng(0).random((40, 10))


def test_evaluate_pca_returns_embedding_and_variance():
    embedding, score = evaluate_pca(_X, {"n_components": 3})
    assert embedding.shape == (40, 3)
    assert 0.0 <= score <= 1.0


def test_evaluate_umap_returns_embedding_and_trustworthiness():
    embedding, score = evaluate_umap(_X, {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0}, trustworthiness_n_neighbors=5)
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_evaluate_pca_varimax_returns_embedding_and_variance():
    embedding, score = evaluate_pca_varimax(_X, {"n_components": 3, "rotation_max_iter": 500})
    assert embedding.shape == (40, 3)
    assert 0.0 <= score <= 1.0


def test_evaluate_pacmap_returns_embedding_and_trustworthiness():
    embedding, score = evaluate_pacmap(
        _X,
        {"n_components": 2, "n_neighbors": 5, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0},
        trustworthiness_n_neighbors=5,
    )
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_run_tuning_sweep_pca_one_param():
    df = run_tuning_sweep("pca", _X, base_params={}, tuning_grid={"n_components": [2, 4, 6]}, trustworthiness_n_neighbors=None)
    assert list(df.columns) == ["n_components", TUNING_METRIC_NAMES["pca"]]
    assert len(df) == 3
    assert list(df["n_components"]) == [2, 4, 6]
    # more components should never explain less cumulative variance
    assert df[TUNING_METRIC_NAMES["pca"]].is_monotonic_increasing


def test_run_tuning_sweep_umap_two_params_cartesian_product():
    df = run_tuning_sweep(
        "umap",
        _X,
        base_params={"random_state": 0, "n_components": 2},
        tuning_grid={"n_neighbors": [5, 10], "min_dist": [0.1, 0.5]},
        trustworthiness_n_neighbors=5,
    )
    assert list(df.columns) == ["n_neighbors", "min_dist", TUNING_METRIC_NAMES["umap"]]
    assert len(df) == 4  # 2 x 2 cartesian product


def test_run_tuning_sweep_pca_varimax_one_param():
    df = run_tuning_sweep(
        "pca_varimax",
        _X,
        base_params={"rotation_max_iter": 500},
        tuning_grid={"n_components": [2, 4, 6]},
        trustworthiness_n_neighbors=None,
    )
    assert list(df.columns) == ["n_components", TUNING_METRIC_NAMES["pca_varimax"]]
    assert len(df) == 3
    assert list(df["n_components"]) == [2, 4, 6]
    # varimax rotation is orthogonal - doesn't change total variance explained
    assert df[TUNING_METRIC_NAMES["pca_varimax"]].is_monotonic_increasing


def test_run_tuning_sweep_pacmap_one_param():
    df = run_tuning_sweep(
        "pacmap",
        _X,
        base_params={"n_components": 2, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0},
        tuning_grid={"n_neighbors": [5, 10]},
        trustworthiness_n_neighbors=5,
    )
    assert list(df.columns) == ["n_neighbors", TUNING_METRIC_NAMES["pacmap"]]
    assert len(df) == 2


def test_run_tuning_sweep_pacmap_without_trustworthiness_n_neighbors_raises():
    with pytest.raises(ValueError, match="trustworthiness_n_neighbors is required"):
        run_tuning_sweep(
            "pacmap",
            _X,
            base_params={"n_components": 2, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0},
            tuning_grid={"n_neighbors": [5]},
            trustworthiness_n_neighbors=None,
        )


def test_run_tuning_sweep_unsupported_method_raises():
    with pytest.raises(ValueError, match="fine-tuning not supported for method 'tsne'"):
        run_tuning_sweep("tsne", _X, {}, {"perplexity": [10, 20]}, None)


def test_run_tuning_sweep_umap_without_trustworthiness_n_neighbors_raises():
    with pytest.raises(ValueError, match="trustworthiness_n_neighbors is required"):
        run_tuning_sweep("umap", _X, {"random_state": 0}, {"n_neighbors": [5]}, trustworthiness_n_neighbors=None)
