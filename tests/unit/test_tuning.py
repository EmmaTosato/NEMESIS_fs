"""Unit tests for src/analysis/tuning.py."""

import numpy as np
import pytest
from sklearn.manifold import trustworthiness

from src.analysis.pca_method import decomposition_spectra
from src.analysis.tuning import (
    TUNING_METRIC_NAMES,
    evaluate_pacmap,
    evaluate_pca,
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


_PCA_BASE = {"solver": "blocks", "standardize": False, "dual": True, "rotation": "none"}


def test_evaluate_pca_returns_embedding_and_variance():
    embedding, score = evaluate_pca(_X, {**_PCA_BASE, "n_components": 3})
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


def test_evaluate_umap_euclidean_metric_uses_distance_cache(monkeypatch):
    """Regression (docs/debugging/debug_25_08_26.md): metric="euclidean" used to always
    fall through to umap-learn's own per-fit neighbor search on raw X, recomputed from
    scratch on every call - 17-35 minutes per n_neighbors/min_dist combination on the
    project's real 5269x264274 lesion matrix, vs. 88s to precompute the whole distance
    matrix once (measured directly). Now goes through the same precomputed-distance +
    distance_cache path as jaccard/dice: two calls sharing one distance_cache compute the
    distance matrix once, not twice. Fails on the pre-fix code (evaluate_umap never
    imported/called src.analysis.tuning.precomputed_distance for any metric)."""
    import src.analysis.tuning as tuning_module

    call_count = 0
    real_precomputed_distance = tuning_module.precomputed_distance

    def _counting_precomputed_distance(X, metric):
        nonlocal call_count
        call_count += 1
        return real_precomputed_distance(X, metric)

    monkeypatch.setattr(tuning_module, "precomputed_distance", _counting_precomputed_distance)

    distance_cache: dict = {}
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "euclidean"}
    evaluate_umap(_X, params, trustworthiness_n_neighbors=5, distance_cache=distance_cache)
    evaluate_umap(_X, params, trustworthiness_n_neighbors=5, distance_cache=distance_cache)

    assert call_count == 1, f"expected precomputed_distance to run once for euclidean with a shared cache, got {call_count}"
    assert "euclidean" in distance_cache


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


def test_evaluate_tsne_euclidean_metric_uses_distance_cache(monkeypatch):
    """Regression (2026-08-25, docs/debugging/debug_25_08_26.md): extended from umap-only to
    tsne too, on request - same shape of test as
    test_evaluate_umap_euclidean_metric_uses_distance_cache above."""
    import src.analysis.tuning as tuning_module

    call_count = 0
    real_precomputed_distance = tuning_module.precomputed_distance

    def _counting_precomputed_distance(X, metric):
        nonlocal call_count
        call_count += 1
        return real_precomputed_distance(X, metric)

    monkeypatch.setattr(tuning_module, "precomputed_distance", _counting_precomputed_distance)

    distance_cache: dict = {}
    params = {"n_components": 2, "perplexity": 10, "random_state": 0, "metric": "euclidean"}
    evaluate_tsne(_X, params, trustworthiness_n_neighbors=5, distance_cache=distance_cache)
    evaluate_tsne(_X, params, trustworthiness_n_neighbors=5, distance_cache=distance_cache)

    assert call_count == 1, f"expected precomputed_distance to run once for euclidean with a shared cache, got {call_count}"
    assert "euclidean" in distance_cache


def test_evaluate_tsne_binary_metric_scored_against_matching_metric_not_euclidean():
    params = {"n_components": 2, "perplexity": 10, "random_state": 0, "metric": "jaccard"}
    embedding, matching_metric_score = evaluate_tsne(_X_BINARY, params, trustworthiness_n_neighbors=5)
    euclidean_score = float(trustworthiness(_X_BINARY, embedding, n_neighbors=5, metric="euclidean"))
    assert matching_metric_score != pytest.approx(euclidean_score)


def test_evaluate_pca_with_varimax_returns_embedding_and_the_same_variance_as_without():
    params = {**_PCA_BASE, "n_components": 3}
    embedding, score = evaluate_pca(_X, {**params, "rotation": "varimax", "rotation_max_iter": 500})
    _, unrotated_score = evaluate_pca(_X, params)

    assert embedding.shape == (40, 3)
    assert score == pytest.approx(unrotated_score)  # a rotation redistributes the variance, it does not change the total


def test_evaluate_pca_fits_the_decomposition_only_once(monkeypatch):
    """AUDIT_FINDINGS.md #57 regression, kept for the `pca` method: the evaluation used to fit a
    standalone PCA just to read the explained variance, then fit its own, identical one for the
    embedding - 2 decompositions per combination instead of 1."""
    import src.analysis.pca_method as pca_method

    call_count = 0
    real_fit = pca_method.fit_covariance_pca

    def _counting_fit(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return real_fit(*args, **kwargs)

    monkeypatch.setattr(pca_method, "fit_covariance_pca", _counting_fit)

    evaluate_pca(_X, {**_PCA_BASE, "rotation": "varimax", "rotation_max_iter": 500, "n_components": 3})

    assert call_count == 1, f"expected one decomposition, got {call_count}"


def test_evaluate_pacmap_returns_embedding_and_trustworthiness():
    embedding, score = evaluate_pacmap(
        _X,
        {"n_components": 2, "n_neighbors": 5, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0},
        trustworthiness_n_neighbors=5,
    )
    assert embedding.shape == (40, 2)
    assert 0.0 <= score <= 1.0


def test_run_tuning_sweep_pca_one_param():
    df, _embeddings_by_combo = run_tuning_sweep("pca", _X, base_params=_PCA_BASE, tuning_grid={"n_components": [2, 4, 6]}, trustworthiness_n_neighbors=None)
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


def test_run_tuning_sweep_pca_with_varimax_one_param():
    df, _embeddings_by_combo = run_tuning_sweep(
        "pca",
        _X,
        base_params={**_PCA_BASE, "rotation": "varimax", "rotation_max_iter": 500},
        tuning_grid={"n_components": [2, 4, 6]},
        trustworthiness_n_neighbors=None,
    )
    assert list(df.columns) == ["n_components", TUNING_METRIC_NAMES["pca"]]
    assert list(df["n_components"]) == [2, 4, 6]
    # varimax rotation is orthogonal - doesn't change total variance explained
    assert df[TUNING_METRIC_NAMES["pca"]].is_monotonic_increasing


def test_run_tuning_sweep_pca_over_variance_share_keeps_the_share_it_asked_for():
    shares = [0.5, 0.8, 0.9]
    df, embeddings_by_combo = run_tuning_sweep(
        "pca", _X, base_params=_PCA_BASE, tuning_grid={"variance_share": shares}, trustworthiness_n_neighbors=None
    )
    assert list(df.columns) == ["variance_share", TUNING_METRIC_NAMES["pca"]]
    for share, score in zip(df["variance_share"], df[TUNING_METRIC_NAMES["pca"]]):
        assert score >= share  # the smallest number of components that reaches the share
    # more variance asked, never fewer components
    widths = [embeddings_by_combo[(share,)].shape[1] for share in shares]
    assert widths == sorted(widths)


def test_run_tuning_sweep_pca_rejects_a_grid_over_n_components_when_base_also_fixes_variance_share():
    with pytest.raises(ValueError, match="exactly one of n_components and variance_share"):
        run_tuning_sweep(
            "pca", _X, base_params={**_PCA_BASE, "variance_share": 0.9}, tuning_grid={"n_components": [2, 4]}, trustworthiness_n_neighbors=None
        )


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


# --- the pca sweep fits the decomposition once per thing the fit depends on ---------------------


def _count_pca_fits(monkeypatch):
    import src.analysis.pca_method as pca_method

    calls = []
    real_fit = pca_method.fit_covariance_pca

    def _counting_fit(*args, **kwargs):
        calls.append(kwargs)
        return real_fit(*args, **kwargs)

    monkeypatch.setattr(pca_method, "fit_covariance_pca", _counting_fit)
    return calls


def test_pca_sweep_over_n_components_fits_the_decomposition_once(monkeypatch):
    calls = _count_pca_fits(monkeypatch)

    df, _ = run_tuning_sweep("pca", _X, _PCA_BASE, {"n_components": [2, 3, 4, 5, 6]}, None)

    assert len(df) == 5
    assert len(calls) == 1


def test_pca_sweep_over_rotation_and_variance_share_still_fits_once(monkeypatch):
    calls = _count_pca_fits(monkeypatch)

    df, _ = run_tuning_sweep(
        "pca", _X, {**_PCA_BASE, "rotation_max_iter": 500}, {"rotation": ["none", "varimax"], "variance_share": [0.6, 0.9]}, None
    )

    assert len(df) == 4
    assert len(calls) == 1


def test_pca_sweep_refits_for_each_value_of_a_param_the_decomposition_depends_on(monkeypatch):
    calls = _count_pca_fits(monkeypatch)

    run_tuning_sweep("pca", _X, {**_PCA_BASE, "n_components": 3}, {"standardize": [False, True], "dual": [True, False]}, None)

    assert len(calls) == 4  # 2 x 2: every (standardize, dual) is a different decomposition


def test_pca_sweep_gives_the_same_scores_and_embeddings_as_evaluating_each_combination_alone():
    grid = {"rotation": ["none", "varimax"], "n_components": [2, 4]}
    base = {**_PCA_BASE, "rotation_max_iter": 500}
    df, embeddings = run_tuning_sweep("pca", _X, base, grid, None)

    combinations = [(rotation, n) for rotation in grid["rotation"] for n in grid["n_components"]]
    for (rotation, n_components), row in zip(combinations, df.itertuples()):
        alone, alone_score = evaluate_pca(_X, {**base, "rotation": rotation, "n_components": n_components})
        np.testing.assert_allclose(embeddings[(rotation, n_components)], alone, atol=1e-10)
        assert getattr(row, TUNING_METRIC_NAMES["pca"]) == pytest.approx(alone_score)


def test_pca_sweep_with_the_sklearn_solver_fits_once(monkeypatch):
    from sklearn.decomposition import PCA

    fits = []
    real_fit = PCA.fit
    monkeypatch.setattr(PCA, "fit", lambda self, *a, **k: fits.append(1) or real_fit(self, *a, **k))

    run_tuning_sweep("pca", _X, {"solver": "sklearn", "standardize": False, "rotation": "none"}, {"n_components": [2, 3, 4]}, None)

    assert len(fits) == 1


def test_pca_sweep_fits_into_the_model_cache_it_is_given():
    cache: dict = {}

    df, _ = run_tuning_sweep("pca", _X, _PCA_BASE, {"n_components": [2, 3]}, None, cache)

    assert len(df) == 2
    assert list(decomposition_spectra(cache)) == ["solver=blocks,standardize=False,dual=True"]


def test_a_model_cache_given_to_a_method_without_one_is_an_error():
    with pytest.raises(ValueError, match="has no model cache"):
        run_tuning_sweep("pacmap", _X, {"n_components": 2, "n_neighbors": 3, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0}, {"n_neighbors": [2]}, 2, {})
