"""Unit tests for src/analysis/reduction.py."""

import numpy as np
import pytest

from src.analysis.reduction import (
    REDUCTION_METHODS,
    embed,
    embedding_for_viz,
    pacmap_embed,
    pca_embed,
    pca_varimax_embed,
    tsne_embed,
    umap_embed,
)

_X = np.random.default_rng(0).random((30, 15))
_X_BINARY = (np.random.default_rng(1).random((30, 20)) > 0.7).astype(np.uint8)


def test_registry_has_expected_methods():
    assert set(REDUCTION_METHODS) == {"umap", "tsne", "pca", "pca_varimax", "pacmap"}
    assert REDUCTION_METHODS["umap"] is umap_embed
    assert REDUCTION_METHODS["tsne"] is tsne_embed
    assert REDUCTION_METHODS["pca"] is pca_embed
    assert REDUCTION_METHODS["pca_varimax"] is pca_varimax_embed
    assert REDUCTION_METHODS["pacmap"] is pacmap_embed


def test_pca_embed_shape_and_determinism():
    params = {"n_components": 3}
    out1 = pca_embed(_X, params)
    out2 = pca_embed(_X, params)
    assert out1.shape == (30, 3)
    assert np.allclose(out1, out2)  # PCA is deterministic, no random_state needed


def test_umap_embed_shape():
    out = umap_embed(_X, {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0})
    assert out.shape == (30, 2)


def test_tsne_embed_shape():
    out = tsne_embed(_X, {"perplexity": 5, "n_components": 2, "random_state": 0})
    assert out.shape == (30, 2)


def test_pca_varimax_embed_shape_and_determinism():
    params = {"n_components": 3, "rotation_max_iter": 500}
    out1 = pca_varimax_embed(_X, params)
    out2 = pca_varimax_embed(_X, params)
    assert out1.shape == (30, 3)
    assert np.allclose(out1, out2)  # PCA + varimax rotation is deterministic


def test_pca_varimax_embed_missing_n_components_raises():
    with pytest.raises(ValueError, match="n_components"):
        pca_varimax_embed(_X, {"rotation_max_iter": 500})


def test_pca_varimax_embed_missing_rotation_max_iter_raises():
    with pytest.raises(ValueError, match="rotation_max_iter"):
        pca_varimax_embed(_X, {"n_components": 3})


def test_pca_varimax_embed_rotates_scaled_loadings_not_raw_eigenvectors():
    """Regression test for the loadings-scaling bug (2026-08 literature review):
    pca_varimax_embed used to rotate PCA.components_ directly (unit-norm
    eigenvectors) instead of factor loadings (eigenvector * sqrt(eigenvalue)).
    Varimax is an orthogonal rotation, so it preserves the total
    reconstructed covariance of whatever matrix it rotates - Lambda_rot @
    Lambda_rot.T must equal Lambda @ Lambda.T for the *loadings* Lambda, not
    for the raw eigenvectors. This fails under the old (unscaled) code
    whenever explained_variance_ isn't ~1 for every retained component (true
    for any real, non-pathological input), and passes once loadings are
    scaled correctly.
    """
    from sklearn.decomposition import PCA

    params = {"n_components": 3, "rotation_max_iter": 500}
    fitted = PCA(n_components=3).fit(_X)
    loadings = fitted.components_.T * np.sqrt(fitted.explained_variance_)
    unrotated_covariance = loadings @ loadings.T

    embedding = pca_varimax_embed(_X, params)

    # Reconstruct the rotated loadings straight from the embedding: with real
    # loadings, lstsq(Lambda_rot, X_centered.T) is a genuine multiple
    # regression (Lambda_rot.T @ Lambda_rot != I), invertible via the normal
    # equations - Lambda_rot recovered this way must reproduce the same
    # covariance the unrotated loadings do (varimax is variance-preserving).
    X_centered = _X - _X.mean(axis=0)
    rotated_loadings, *_ = np.linalg.lstsq(embedding, X_centered, rcond=None)
    rotated_loadings = rotated_loadings.T
    rotated_covariance = rotated_loadings @ rotated_loadings.T

    assert np.allclose(rotated_covariance, unrotated_covariance, atol=1e-6)
    # Also pin down that this is NOT the degenerate orthonormal case the old
    # bug produced (Lambda_rot.T @ Lambda_rot == I) - a real varimax rotation
    # on scaled loadings should not be exactly orthonormal itself.
    assert not np.allclose(rotated_loadings.T @ rotated_loadings, np.eye(3), atol=1e-3)


def test_pacmap_embed_shape():
    out = pacmap_embed(
        _X, {"n_components": 2, "n_neighbors": 5, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0}
    )
    assert out.shape == (30, 2)


def test_embed_euclidean_matches_direct_reduction_methods_call():
    # No metric/binary handling involved - embed() must be a transparent
    # pass-through for anything that isn't jaccard/dice.
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0}
    direct = umap_embed(_X, params)
    via_embed = embed("umap", _X, params)
    assert np.allclose(direct, via_embed)


def test_embed_jaccard_matches_precomputed_binary_pairwise_distance():
    """Regression test for the tuning/production discrepancy (2026-08,
    literature-validation review): production used to pass metric="jaccard"
    straight to umap.UMAP on raw X, while tuning.py's sweep precomputed the
    exact Jaccard distance matrix and passed metric="precomputed" - two
    different code paths that could compute different neighbor graphs.
    embed() must now produce bit-identical output to the tuning path.
    """
    from src.analysis.distances import binary_pairwise_distance

    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "jaccard"}
    via_embed = embed("umap", _X_BINARY, params)

    distance_matrix = binary_pairwise_distance(_X_BINARY, "jaccard")
    precomputed_params = {k: v for k, v in params.items() if k != "metric"}
    precomputed_params["metric"] = "precomputed"
    direct = umap_embed(distance_matrix, precomputed_params)

    assert np.allclose(via_embed, direct)


def test_embed_dice_forces_tsne_init_random():
    # sklearn's TSNE default init="pca" cannot run on a distance matrix -
    # embed() must override it whenever metric is precomputed.
    params = {"n_components": 2, "perplexity": 5, "random_state": 0, "metric": "dice"}
    embedding = embed("tsne", _X_BINARY, params)
    assert embedding.shape == (30, 2)


def test_embed_non_binary_matrix_with_jaccard_raises():
    X_continuous = np.random.default_rng(2).random((30, 20))
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "jaccard"}
    with pytest.raises(ValueError, match="strictly binary"):
        embed("umap", X_continuous, params)


def test_embed_distance_cache_reused_across_calls():
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "jaccard"}
    cache: dict[str, np.ndarray] = {}
    embed("umap", _X_BINARY, params, cache)
    assert "jaccard" in cache
    cached_matrix = cache["jaccard"]
    embed("umap", _X_BINARY, {**params, "n_neighbors": 10}, cache)
    # Same object reused, not recomputed, for a second call at the same metric.
    assert cache["jaccard"] is cached_matrix


def test_embedding_for_viz_reuses_when_already_matching_dimensions():
    embedding = umap_embed(_X, {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0})
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0}

    viz_embedding = embedding_for_viz("umap", _X, params, embedding, viz_n_components=2)

    assert viz_embedding is embedding


def test_embedding_for_viz_refits_when_dimensions_differ():
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 5, "random_state": 0}
    embedding = umap_embed(_X, params)
    assert embedding.shape == (30, 5)

    viz_embedding = embedding_for_viz("umap", _X, params, embedding, viz_n_components=2)

    assert viz_embedding.shape == (30, 2)
    assert viz_embedding is not embedding


def test_embedding_for_viz_refit_matches_direct_call_with_same_params():
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 5, "random_state": 0}
    embedding = umap_embed(_X, params)

    viz_embedding = embedding_for_viz("umap", _X, params, embedding, viz_n_components=2)
    direct_2d = umap_embed(_X, {**params, "n_components": 2})

    assert np.allclose(viz_embedding, direct_2d)


def test_embedding_for_viz_tsne_refits_when_dimensions_differ():
    params = {"perplexity": 5, "n_components": 3, "random_state": 0}
    embedding = tsne_embed(_X, params)
    assert embedding.shape == (30, 3)

    viz_embedding = embedding_for_viz("tsne", _X, params, embedding, viz_n_components=2)

    assert viz_embedding.shape == (30, 2)


@pytest.mark.parametrize("method", ["pca", "pca_varimax", "pacmap"])
def test_embedding_for_viz_raises_for_non_refittable_methods_when_dimensions_differ(method):
    """Regression (2026-08-17, on request): pca/pca_varimax/pacmap must never
    silently slice (invalid for pacmap/pca_varimax, see reduction.py's own
    docstring) nor silently refit (mathematically meaningless for
    pca_varimax's jointly-optimized rotation) when the production embedding's
    own dimensionality doesn't already match viz_n_components - only
    umap/tsne refit. A 5-column embedding is a plausible stand-in for any of
    the 3 excluded methods' real output shape (this test only exercises
    embedding_for_viz's own dispatch, not each method's own embed function)."""
    embedding = np.random.default_rng(3).random((30, 5))
    with pytest.raises(ValueError, match="no valid viz-refit"):
        embedding_for_viz(method, _X, {"n_components": 5}, embedding, viz_n_components=2)


@pytest.mark.parametrize("method", ["pca", "pca_varimax", "pacmap"])
def test_embedding_for_viz_reuses_non_refittable_methods_when_already_matching(method):
    """The exclusion from _REFITTABLE_FOR_VIZ only matters when a refit would
    actually be needed - the cheap "already the right shape" path stays
    available for every method, refittable or not."""
    embedding = np.random.default_rng(4).random((30, 2))
    viz_embedding = embedding_for_viz(method, _X, {"n_components": 2}, embedding, viz_n_components=2)
    assert viz_embedding is embedding
