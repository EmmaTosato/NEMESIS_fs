"""Unit tests for src/analysis/tuning.py."""

import numpy as np
import pytest
from sklearn.manifold import trustworthiness

from src.analysis.tuning import (
    TUNING_METRIC_NAMES,
    evaluate_pacmap,
    evaluate_pca,
    evaluate_pca_varimax,
    evaluate_tsne,
    evaluate_umap,
    run_tuning_sweep,
)

_X = np.random.default_rng(0).random((40, 10))

# Binary fixture for jaccard/dice metric tests - umap/tsne's continuous _X above
# has no "on/off" features, so jaccard/dice (defined on binary vectors) need
# their own fixture. Every row has >=1 nonzero feature (required by
# binary_pairwise_distance).
_X_BINARY = (np.random.default_rng(1).random((40, 20)) > 0.7).astype(np.uint8)


def test_evaluate_pca_returns_embedding_and_variance():
    embedding, score = evaluate_pca(_X, {"n_components": 3})
    assert embedding.shape == (40, 3)
    assert 0.0 <= score <= 1.0


def test_evaluate_umap_returns_embedding_and_trustworthiness():
    embedding, score = evaluate_umap(_X, {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0}, trustworthiness_n_neighbors=5)
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_evaluate_umap_with_jaccard_metric_returns_valid_embedding_and_score():
    embedding, score = evaluate_umap(
        _X_BINARY, {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "jaccard"}, trustworthiness_n_neighbors=5
    )
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_evaluate_umap_with_dice_metric_returns_valid_embedding_and_score():
    embedding, score = evaluate_umap(
        _X_BINARY, {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "dice"}, trustworthiness_n_neighbors=5
    )
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_evaluate_umap_binary_metric_scored_against_matching_metric_not_euclidean():
    # Same embedding, scored two ways: evaluate_umap's own path (trustworthiness
    # against the jaccard distance matrix) vs. naively against raw-X euclidean
    # neighborhoods. These read different notions of "originally close", so
    # they aren't expected to agree - this pins evaluate_umap to the matching-
    # metric behavior rather than silently falling back to euclidean.
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "jaccard"}
    embedding, matching_metric_score = evaluate_umap(_X_BINARY, params, trustworthiness_n_neighbors=5)
    euclidean_score = float(trustworthiness(_X_BINARY, embedding, n_neighbors=5, metric="euclidean"))
    assert matching_metric_score != pytest.approx(euclidean_score)


def test_run_tuning_sweep_no_skipped_reason_column():
    df, _embeddings_by_combo = run_tuning_sweep(
        "umap",
        _X_BINARY,
        base_params={"random_state": 0, "n_components": 2, "min_dist": 0.1},
        tuning_grid={"metric": ["euclidean", "jaccard"]},
        trustworthiness_n_neighbors=5,
    )
    assert "skipped_reason" not in df.columns


def test_evaluate_tsne_returns_embedding_and_trustworthiness():
    embedding, score = evaluate_tsne(_X, {"n_components": 2, "perplexity": 10, "random_state": 0}, trustworthiness_n_neighbors=5)
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_evaluate_tsne_with_jaccard_metric_returns_valid_embedding_and_score():
    embedding, score = evaluate_tsne(
        _X_BINARY, {"n_components": 2, "perplexity": 10, "random_state": 0, "metric": "jaccard"}, trustworthiness_n_neighbors=5
    )
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_evaluate_tsne_with_dice_metric_returns_valid_embedding_and_score():
    embedding, score = evaluate_tsne(
        _X_BINARY, {"n_components": 2, "perplexity": 10, "random_state": 0, "metric": "dice"}, trustworthiness_n_neighbors=5
    )
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_evaluate_tsne_binary_metric_scored_against_matching_metric_not_euclidean():
    params = {"n_components": 2, "perplexity": 10, "random_state": 0, "metric": "jaccard"}
    embedding, matching_metric_score = evaluate_tsne(_X_BINARY, params, trustworthiness_n_neighbors=5)
    euclidean_score = float(trustworthiness(_X_BINARY, embedding, n_neighbors=5, metric="euclidean"))
    assert matching_metric_score != pytest.approx(euclidean_score)


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
    df, _embeddings_by_combo = run_tuning_sweep("pca", _X, base_params={}, tuning_grid={"n_components": [2, 4, 6]}, trustworthiness_n_neighbors=None)
    assert list(df.columns) == ["n_components", TUNING_METRIC_NAMES["pca"]]
    assert len(df) == 3
    assert list(df["n_components"]) == [2, 4, 6]
    # more components should never explain less cumulative variance
    assert df[TUNING_METRIC_NAMES["pca"]].is_monotonic_increasing


def test_run_tuning_sweep_umap_two_params_cartesian_product():
    df, _embeddings_by_combo = run_tuning_sweep(
        "umap",
        _X,
        base_params={"random_state": 0, "n_components": 2},
        tuning_grid={"n_neighbors": [5, 10], "min_dist": [0.1, 0.5]},
        trustworthiness_n_neighbors=5,
    )
    assert list(df.columns) == ["n_neighbors", "min_dist", TUNING_METRIC_NAMES["umap"]]
    assert len(df) == 4  # 2 x 2 cartesian product


def test_run_tuning_sweep_umap_metric_and_n_neighbors_cartesian_product():
    df, _embeddings_by_combo = run_tuning_sweep(
        "umap",
        _X_BINARY,
        base_params={"random_state": 0, "n_components": 2, "min_dist": 0.1},
        tuning_grid={"n_neighbors": [5, 10], "metric": ["euclidean", "jaccard", "dice"]},
        trustworthiness_n_neighbors=5,
    )
    assert list(df.columns) == ["n_neighbors", "metric", TUNING_METRIC_NAMES["umap"]]
    assert len(df) == 6  # 2 x 3 cartesian product
    assert set(df["metric"]) == {"euclidean", "jaccard", "dice"}


def test_run_tuning_sweep_pca_varimax_one_param():
    df, _embeddings_by_combo = run_tuning_sweep(
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
    df, _embeddings_by_combo = run_tuning_sweep(
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
    with pytest.raises(ValueError, match="fine-tuning not supported for method 'kmeans'"):
        run_tuning_sweep("kmeans", _X, {}, {"n_clusters": [2, 3]}, None)


def test_run_tuning_sweep_umap_without_trustworthiness_n_neighbors_raises():
    with pytest.raises(ValueError, match="trustworthiness_n_neighbors is required"):
        run_tuning_sweep("umap", _X, {"random_state": 0}, {"n_neighbors": [5]}, trustworthiness_n_neighbors=None)


def test_run_tuning_sweep_tsne_one_param():
    df, _embeddings_by_combo = run_tuning_sweep(
        "tsne",
        _X,
        base_params={"n_components": 2, "random_state": 0},
        tuning_grid={"perplexity": [5, 10]},
        trustworthiness_n_neighbors=5,
    )
    assert list(df.columns) == ["perplexity", TUNING_METRIC_NAMES["tsne"]]
    assert len(df) == 2


def test_run_tuning_sweep_tsne_without_trustworthiness_n_neighbors_raises():
    with pytest.raises(ValueError, match="trustworthiness_n_neighbors is required"):
        run_tuning_sweep("tsne", _X, {"n_components": 2, "random_state": 0}, {"perplexity": [5]}, trustworthiness_n_neighbors=None)


def test_run_tuning_sweep_tsne_metric_and_perplexity_cartesian_product():
    df, _embeddings_by_combo = run_tuning_sweep(
        "tsne",
        _X_BINARY,
        base_params={"random_state": 0, "n_components": 2},
        tuning_grid={"perplexity": [5, 10], "metric": ["euclidean", "jaccard", "dice"]},
        trustworthiness_n_neighbors=5,
    )
    assert list(df.columns) == ["perplexity", "metric", TUNING_METRIC_NAMES["tsne"]]
    assert len(df) == 6  # 2 x 3 cartesian product
    assert set(df["metric"]) == {"euclidean", "jaccard", "dice"}


def test_run_tuning_sweep_returns_embedding_per_combo():
    df, embeddings_by_combo = run_tuning_sweep(
        "umap",
        _X,
        base_params={"random_state": 0, "n_components": 2},
        tuning_grid={"n_neighbors": [5, 10], "min_dist": [0.1, 0.5]},
        trustworthiness_n_neighbors=5,
    )
    assert len(embeddings_by_combo) == len(df) == 4
    for combo, embedding in embeddings_by_combo.items():
        assert isinstance(combo, tuple) and len(combo) == 2
        assert embedding.shape == (40, 2)
    # combo keys match the swept columns/order in df, e.g. (5, 0.1)
    assert (5, 0.1) in embeddings_by_combo
