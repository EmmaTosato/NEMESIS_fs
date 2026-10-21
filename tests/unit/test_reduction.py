"""Unit tests for src/analysis/reduction.py."""

import numpy as np
import pytest

from src.analysis.reduction import (
    REDUCTION_METHODS,
    embed,
    embedding_for_viz,
    pacmap_embed,
    pca_embed,
    tsne_embed,
    tsne_init_from_distances,
    umap_embed,
)

_X = np.random.default_rng(0).random((30, 15))
_X_BINARY = (np.random.default_rng(1).random((30, 20)) > 0.7).astype(np.uint8)


def test_registry_has_expected_methods():
    assert set(REDUCTION_METHODS) == {"umap", "tsne", "pca", "pacmap"}
    assert REDUCTION_METHODS["umap"] is umap_embed
    assert REDUCTION_METHODS["tsne"] is tsne_embed
    assert REDUCTION_METHODS["pca"] is pca_embed
    assert REDUCTION_METHODS["pacmap"] is pacmap_embed


_PCA_PARAMS = {"solver": "blocks", "standardize": False, "dual": True, "rotation": "none", "n_components": 3}


def test_pca_embed_shape_and_determinism():
    params = _PCA_PARAMS
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


def test_pca_embed_with_varimax_is_deterministic_and_the_right_shape():
    params = {**_PCA_PARAMS, "rotation": "varimax", "rotation_max_iter": 500}
    out1 = pca_embed(_X, params)
    out2 = pca_embed(_X, params)
    assert out1.shape == (30, 3)
    assert np.allclose(out1, out2)  # PCA + varimax rotation is deterministic


def test_pca_embed_with_varimax_rotates_scaled_loadings_not_raw_eigenvectors():
    """Regression test for the loadings-scaling bug (2026-08 literature review), kept for the
    varimax path of the `pca` method: it used to rotate PCA.components_ directly (unit-norm
    eigenvectors) instead of factor loadings (eigenvector * sqrt(eigenvalue)).
    Varimax is an orthogonal rotation, so it preserves the total reconstructed covariance of
    whatever matrix it rotates - Lambda_rot @ Lambda_rot.T must equal Lambda @ Lambda.T for the
    *loadings* Lambda, not for the raw eigenvectors. This fails under the old (unscaled) code
    whenever explained_variance_ isn't ~1 for every retained component (true for any real,
    non-pathological input), and passes once loadings are scaled correctly.
    """
    from sklearn.decomposition import PCA

    fitted = PCA(n_components=3).fit(_X)
    loadings = fitted.components_.T * np.sqrt(fitted.explained_variance_)
    unrotated_covariance = loadings @ loadings.T

    embedding = pca_embed(_X, {**_PCA_PARAMS, "rotation": "varimax", "rotation_max_iter": 500})

    # Reconstruct the rotated loadings straight from the embedding: with real loadings,
    # lstsq(Lambda_rot, X_centered.T) is a genuine multiple regression, invertible via the normal
    # equations - Lambda_rot recovered this way must reproduce the same covariance the unrotated
    # loadings do (varimax is variance-preserving).
    X_centered = _X - _X.mean(axis=0)
    coefficients, *_ = np.linalg.lstsq(embedding, X_centered, rcond=None)
    rotated_loadings = coefficients.T
    rotated_covariance = rotated_loadings @ rotated_loadings.T

    assert np.allclose(rotated_covariance, unrotated_covariance, atol=1e-6)


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


def test_embed_euclidean_metric_for_umap_uses_precomputed_distance_matrix():
    """Regression (2026-08-25, docs/debugging/debug_25_08_26.md): embed() used to pass
    metric="euclidean" straight through to umap.UMAP on raw X regardless of reduction_method,
    recomputing umap-learn's own neighbor search on every call - for reduction_method="umap"
    specifically, embed() must now match the same precomputed-distance path tuning.py's
    evaluate_umap already takes (bit-identical output, not just "a valid embedding")."""
    from src.analysis.distances import euclidean_pairwise_distance

    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "euclidean"}
    via_embed = embed("umap", _X, params)

    distance_matrix = euclidean_pairwise_distance(_X)
    precomputed_params = {k: v for k, v in params.items() if k != "metric"}
    precomputed_params["metric"] = "precomputed"
    direct = umap_embed(distance_matrix, precomputed_params)

    assert np.allclose(via_embed, direct)


def test_embed_euclidean_metric_for_tsne_uses_precomputed_distance_matrix():
    """Regression (2026-08-25, docs/debugging/debug_25_08_26.md): extended from umap-only to
    tsne too, on request - embed("tsne", ..., metric="euclidean") must now match the same
    precomputed-distance path tuning.py's evaluate_tsne already takes, same as the umap test
    above (bit-identical output). sklearn's TSNE cannot use its default init="pca" on a
    distance matrix, so embed() starts it from classical MDS of that matrix."""
    from src.analysis.distances import euclidean_pairwise_distance

    params = {"n_components": 2, "perplexity": 5, "random_state": 0, "metric": "euclidean"}
    via_embed = embed("tsne", _X, params)

    distance_matrix = euclidean_pairwise_distance(_X)
    precomputed_params = {k: v for k, v in params.items() if k != "metric"}
    precomputed_params["metric"] = "precomputed"
    precomputed_params["init"] = tsne_init_from_distances(distance_matrix, 2, 0)
    direct = tsne_embed(distance_matrix, precomputed_params)

    assert np.allclose(via_embed, direct)


def test_embed_euclidean_distance_cache_reused_across_calls_for_umap():
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "euclidean"}
    cache: dict[str, np.ndarray] = {}
    embed("umap", _X, params, cache)
    assert "euclidean" in cache
    cached_matrix = cache["euclidean"]
    embed("umap", _X, {**params, "n_neighbors": 10}, cache)
    assert cache["euclidean"] is cached_matrix


def test_embed_dice_gives_tsne_a_distance_based_init():
    # sklearn's TSNE default init="pca" cannot run on a distance matrix -
    # embed() must replace it whenever metric is precomputed.
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


def test_embed_precompute_distance_metric_false_passes_metric_through_unchanged(monkeypatch):
    """precompute_distance_metric=False (2026-08-25, on request, docs/debugging/debug_25_08_26.md):
    embed() must skip precomputed_distance entirely and behave exactly like a "vanilla" umap.UMAP
    call - reproducibility against literature/external UMAP runs that never precompute anything."""
    import src.analysis.reduction as reduction_module

    call_count = 0
    real_precomputed_distance = reduction_module.precomputed_distance

    def _counting_precomputed_distance(X, metric):
        nonlocal call_count
        call_count += 1
        return real_precomputed_distance(X, metric)

    monkeypatch.setattr(reduction_module, "precomputed_distance", _counting_precomputed_distance)

    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "euclidean"}
    via_embed = embed("umap", _X, params, None, False)
    direct = umap_embed(_X, params)

    assert call_count == 0, f"expected precomputed_distance to never run with precompute_distance_metric=False, got {call_count} calls"
    assert np.allclose(via_embed, direct)


def test_embed_precompute_distance_metric_false_still_validates_binary_matrix():
    """require_binary_matrix is a data-validity check (jaccard/dice are meaningless on non-binary
    data), independent of whether the distance matrix is actually precomputed - must still raise
    even with precompute_distance_metric=False."""
    X_continuous = np.random.default_rng(2).random((30, 20))
    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "jaccard"}
    with pytest.raises(ValueError, match="strictly binary"):
        embed("umap", X_continuous, params, None, False)


def test_embedding_for_viz_forwards_precompute_distance_metric_to_refit(monkeypatch):
    """precompute_distance_metric must propagate from embedding_for_viz's own refit call to embed
    - otherwise the viz refit could silently precompute while the main fit didn't (or vice versa)."""
    import src.analysis.reduction as reduction_module

    call_count = 0
    real_precomputed_distance = reduction_module.precomputed_distance

    def _counting_precomputed_distance(X, metric):
        nonlocal call_count
        call_count += 1
        return real_precomputed_distance(X, metric)

    monkeypatch.setattr(reduction_module, "precomputed_distance", _counting_precomputed_distance)

    params = {"n_neighbors": 5, "min_dist": 0.1, "n_components": 3, "random_state": 0, "metric": "euclidean"}
    embedding = umap_embed(_X, params)
    embedding_for_viz("umap", _X, params, embedding, 2, None, False)

    assert call_count == 0, f"expected the refit to skip precomputed_distance too, got {call_count} calls"


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


@pytest.mark.parametrize("method", ["pca", "pacmap"])
def test_embedding_for_viz_raises_for_non_refittable_methods_when_dimensions_differ(method):
    """Regression (2026-08-17, on request): pca/pacmap must never silently slice (invalid for
    pacmap, see reduction.py's own docstring) nor silently refit when the production embedding's
    own dimensionality doesn't already match viz_n_components - only umap/tsne refit. A 5-column
    embedding is a plausible stand-in for either excluded method's real output shape (this test
    only exercises embedding_for_viz's own dispatch, not each method's own embed function)."""
    embedding = np.random.default_rng(3).random((30, 5))
    with pytest.raises(ValueError, match="no valid viz-refit"):
        embedding_for_viz(method, _X, {"n_components": 5}, embedding, viz_n_components=2)


@pytest.mark.parametrize("method", ["pca", "pacmap"])
def test_embedding_for_viz_reuses_non_refittable_methods_when_already_matching(method):
    """The exclusion from _REFITTABLE_FOR_VIZ only matters when a refit would
    actually be needed - the cheap "already the right shape" path stays
    available for every method, refittable or not."""
    embedding = np.random.default_rng(4).random((30, 2))
    viz_embedding = embedding_for_viz(method, _X, {"n_components": 2}, embedding, viz_n_components=2)
    assert viz_embedding is embedding


def test_embedding_for_viz_slices_an_unrotated_pca_to_its_leading_components():
    """Regression: a pca production run with more components than viz_n_components (the registry's 150)
    used to fail at the viz step. An unrotated pca's columns are ordered by variance, so its first
    two are a legitimate 2D view (lessons_learned.md #16's one exception)."""
    params = {**_PCA_PARAMS, "n_components": 5}
    embedding = pca_embed(_X, params)

    viz = embedding_for_viz("pca", _X, params, embedding, viz_n_components=2)

    assert viz.shape == (30, 2)
    np.testing.assert_array_equal(viz, embedding[:, :2])


def test_embedding_for_viz_never_slices_a_rotated_pca():
    """After a rotation the columns have no order by variance: a slice would be an arbitrary cut."""
    params = {**_PCA_PARAMS, "n_components": 5, "rotation": "varimax", "rotation_max_iter": 500}
    embedding = pca_embed(_X, params)
    with pytest.raises(ValueError, match="no valid viz-refit"):
        embedding_for_viz("pca", _X, params, embedding, viz_n_components=2)


def test_embedding_for_viz_slices_a_rotated_pca_that_picked_its_components_by_variance():
    """With rotation_n_components the kept rotated components come out most variance first, so the first two
    are a legitimate 2D view (a varimax production run of 12 components used to fail at the viz step)."""
    params = {**_PCA_PARAMS, "n_components": 3, "rotation": "varimax", "rotation_max_iter": 500, "rotation_n_components": 5}
    embedding = pca_embed(_X, params)

    viz = embedding_for_viz("pca", _X, params, embedding, viz_n_components=2)

    np.testing.assert_array_equal(viz, embedding[:, :2])


def test_embedding_for_viz_rejects_a_pca_with_fewer_components_than_the_view_needs():
    params = {**_PCA_PARAMS, "n_components": 1}
    embedding = pca_embed(_X, params)
    with pytest.raises(ValueError, match="fewer than viz_n_components=2"):
        embedding_for_viz("pca", _X, params, embedding, viz_n_components=2)


def test_tsne_init_from_euclidean_distances_equals_pca_scores_up_to_sign():
    """For euclidean distances classical MDS is PCA (Gower 1966): the init must match the one sklearn
    builds for init="pca" - PCA scores rescaled so the first column has std 1e-4."""
    from sklearn.decomposition import PCA

    from src.analysis.distances import euclidean_pairwise_distance

    init = tsne_init_from_distances(euclidean_pairwise_distance(_X), 2, 0)
    scores = PCA(n_components=2).fit_transform(_X)
    expected = scores / np.std(scores[:, 0]) * 1e-4
    assert init.dtype == np.float32
    assert np.std(init[:, 0]) == pytest.approx(1e-4, rel=1e-4)
    for column in range(2):
        sign = np.sign(init[:, column] @ expected[:, column])
        np.testing.assert_allclose(sign * init[:, column], expected[:, column], atol=1e-8)


def test_tsne_init_from_distances_is_deterministic_for_a_seed():
    from src.analysis.distances import binary_pairwise_distance

    distances = binary_pairwise_distance(_X_BINARY, "dice")
    np.testing.assert_array_equal(
        tsne_init_from_distances(distances, 2, 3), tsne_init_from_distances(distances, 2, 3)
    )


def test_tsne_init_from_distances_does_not_modify_the_distance_matrix():
    from src.analysis.distances import euclidean_pairwise_distance

    distances = euclidean_pairwise_distance(_X)
    before = distances.copy()
    tsne_init_from_distances(distances, 2, 0)
    np.testing.assert_array_equal(distances, before)


def test_tsne_init_from_distances_raises_when_every_distance_is_zero():
    with pytest.raises(ValueError, match="every pairwise distance is 0"):
        tsne_init_from_distances(np.zeros((10, 10)), 2, 0)


def test_tsne_init_from_distances_raises_without_positive_leading_eigenvalues():
    # Two points at distance 1 span one dimension only: the second eigenvalue of the MDS Gram matrix is 0.
    distances = np.array([[0.0, 1.0, 1.0], [1.0, 0.0, 2.0], [1.0, 2.0, 0.0]])
    with pytest.raises(ValueError, match="non-positive leading eigenvalues"):
        tsne_init_from_distances(distances, 2, 0)


def test_tsne_init_from_distances_raises_when_n_components_reaches_n_samples():
    with pytest.raises(ValueError, match="n_components < n_samples"):
        tsne_init_from_distances(np.ones((3, 3)) - np.eye(3), 3, 0)
