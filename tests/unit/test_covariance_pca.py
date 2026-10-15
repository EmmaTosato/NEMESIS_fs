"""Unit tests for src/analysis/covariance_pca.py - synthetic matrices, no real data required."""

import numpy as np
import pytest
from sklearn.decomposition import PCA

from src.analysis.covariance_pca import (
    component_t_maps,
    fit_covariance_pca,
    map_reproducibility,
    positive_peak_signs,
    squared_correlation,
    varimax_scores,
)
from src.analysis.reduction import pca_varimax_embed


def _structured_matrix(n_samples=60, n_features=200, n_latent=4, offset=0.0, seed=0):
    """Latent factors with sparse, distinct loadings plus noise: a PCA with a clear top-k and a
    varimax rotation with something to find. `offset` is a large common mean added to every
    value (lessons_learned.md #42: identities that hold on centered data can fail on data with a
    big offset)."""
    rng = np.random.default_rng(seed)
    factors = rng.normal(size=(n_samples, n_latent))
    width = n_features // n_latent
    loadings = np.zeros((n_latent, n_features))
    for k in range(n_latent):
        loadings[k, k * width : (k + 1) * width] = rng.uniform(1, 2, size=width)
    return factors @ loadings + 0.1 * rng.normal(size=(n_samples, n_features)) + offset


@pytest.mark.parametrize("offset", [0.0, 1000.0])
def test_eigenvalues_and_ratios_match_sklearn_pca(offset):
    X = _structured_matrix(offset=offset)
    pca = fit_covariance_pca(X, chunk_columns=64)
    reference = PCA().fit(X)

    k = 20
    np.testing.assert_allclose(pca.eigenvalues[:k], reference.explained_variance_[:k], rtol=1e-8)
    np.testing.assert_allclose(pca.explained_variance_ratio[:k], reference.explained_variance_ratio_[:k], rtol=1e-8)


def test_chunk_size_does_not_change_the_result():
    X = _structured_matrix()
    whole = fit_covariance_pca(X, chunk_columns=10_000)
    chunked = fit_covariance_pca(X, chunk_columns=7)

    np.testing.assert_allclose(chunked.eigenvalues, whole.eigenvalues, rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(chunked.column_means, whole.column_means)


def test_n_components_for_reads_the_cumulative_curve():
    X = _structured_matrix()
    pca = fit_covariance_pca(X)
    cumulative = pca.cumulative_variance_ratio

    k = pca.n_components_for(0.9)
    assert cumulative[k - 1] >= 0.9
    assert k == 1 or cumulative[k - 2] < 0.9
    # share=1.0 lands on the last component with variance, never one past the last component
    assert pca.n_nonzero_components() <= pca.n_components_for(1.0) <= pca.n_samples


@pytest.mark.parametrize("share", [0.0, -0.1, 1.5])
def test_n_components_for_rejects_a_share_outside_zero_one(share):
    pca = fit_covariance_pca(_structured_matrix())
    with pytest.raises(ValueError, match="share must be in"):
        pca.n_components_for(share)


def _match_up_to_sign_and_order(a: np.ndarray, b: np.ndarray) -> float:
    """Smallest, over the columns of `a`, of its best |correlation| with a column of `b`: 1.0 when
    the two sets are the same components, possibly reordered or sign-flipped."""
    correlation = np.abs(np.corrcoef(a.T, b.T)[: a.shape[1], a.shape[1] :])
    return float(correlation.max(axis=1).min())


def test_varimax_scores_match_pca_varimax_embed():
    """The memory-light path computes the same scores as the in-memory reference implementation
    (src/analysis/reduction.py), up to the sign and order of each rotated component."""
    X = _structured_matrix(offset=1000.0)
    k = 4
    pca = fit_covariance_pca(X, chunk_columns=50)

    scores, rotated = varimax_scores(X, pca, n_components=k, max_iter=500, chunk_columns=50)
    reference = pca_varimax_embed(X, {"n_components": k, "rotation_max_iter": 500})

    assert scores.shape == (X.shape[0], k)
    assert rotated.shape == (X.shape[1], k)
    assert _match_up_to_sign_and_order(scores, reference) > 0.999


def test_varimax_scores_chunk_size_does_not_change_the_result():
    X = _structured_matrix()
    pca = fit_covariance_pca(X)
    scores_whole, _ = varimax_scores(X, pca, n_components=4, max_iter=500, chunk_columns=10_000)
    scores_chunked, _ = varimax_scores(X, pca, n_components=4, max_iter=500, chunk_columns=13)

    np.testing.assert_allclose(scores_chunked, scores_whole, atol=1e-8)


def test_varimax_separates_the_latent_factors():
    """Each rotated component loads on one block of 50 features: the property varimax exists for.
    A plain PCA of the same data mixes the blocks."""
    X = _structured_matrix()  # 200 features = 4 blocks of 50
    pca = fit_covariance_pca(X)
    _, rotated = varimax_scores(X, pca, n_components=4, max_iter=500)

    block_share = []
    for column in range(4):
        energy = rotated[:, column] ** 2
        block_share.append(max(energy[k * 50 : (k + 1) * 50].sum() for k in range(4)) / energy.sum())
    assert min(block_share) > 0.9


@pytest.mark.parametrize("n_components", [1, 0])
def test_varimax_needs_at_least_two_components(n_components):
    X = _structured_matrix()
    pca = fit_covariance_pca(X)
    with pytest.raises(ValueError, match="n_components >= 2"):
        varimax_scores(X, pca, n_components=n_components, max_iter=500)


def test_varimax_rejects_more_components_than_the_matrix_has():
    X = _structured_matrix(n_samples=10, n_features=50)
    pca = fit_covariance_pca(X)
    with pytest.raises(ValueError, match="exceeds the 9 components"):
        varimax_scores(X, pca, n_components=10, max_iter=500)  # n-1 = 9 after centering


def test_varimax_rejects_a_matrix_other_than_the_fitted_one():
    pca = fit_covariance_pca(_structured_matrix())
    with pytest.raises(ValueError, match="PCA was fitted on"):
        varimax_scores(_structured_matrix(n_features=150), pca, n_components=3, max_iter=500)


def test_squared_correlation_known_values():
    covariate = np.arange(10, dtype=float)
    scores = np.column_stack([2 * covariate + 1, -covariate, np.tile([0.0, 1.0], 5)])

    r2 = squared_correlation(scores, covariate)

    assert r2[0] == pytest.approx(1.0)
    assert r2[1] == pytest.approx(1.0)  # sign does not matter
    assert 0.0 <= r2[2] < 0.1


def test_squared_correlation_rejects_nan_and_constant_covariates():
    scores = np.random.default_rng(0).normal(size=(10, 3))
    with pytest.raises(ValueError, match="NaN"):
        squared_correlation(scores, np.array([1.0, np.nan] + [2.0] * 8))
    with pytest.raises(ValueError, match="constant"):
        squared_correlation(scores, np.ones(10))


def test_pca_scores_match_sklearn_transform_up_to_sign():
    X = _structured_matrix(offset=1000.0)
    scores = fit_covariance_pca(X, chunk_columns=64).pca_scores(6)
    reference = PCA(n_components=6).fit_transform(X)

    assert _match_up_to_sign_and_order(scores, reference) > 1 - 1e-9
    np.testing.assert_allclose(np.abs(scores), np.abs(reference), atol=1e-6)


@pytest.mark.parametrize("n_components", [0, 10])
def test_pca_scores_reject_an_out_of_range_n_components(n_components):
    pca = fit_covariance_pca(_structured_matrix(n_samples=10, n_features=50))
    with pytest.raises(ValueError, match="n_components must be between 1 and 9"):
        pca.pca_scores(n_components)


def _reference_t(values, scores):
    """Textbook OLS t-statistics of `values ~ 1 + scores`, one voxel at a time, via lstsq."""
    n, k = scores.shape
    design = np.column_stack([np.ones(n), scores])
    out = np.empty((k, values.shape[1]))
    for j in range(values.shape[1]):
        beta, *_ = np.linalg.lstsq(design, values[:, j], rcond=None)
        residual = values[:, j] - design @ beta
        sigma2 = residual @ residual / (n - k - 1)
        covariance = sigma2 * np.linalg.inv(design.T @ design)
        out[:, j] = beta[1:] / np.sqrt(np.diag(covariance)[1:])
    return out


def _scores_and_matrix(offset=0.0):
    X = _structured_matrix(n_samples=80, n_features=120, offset=offset)
    pca = fit_covariance_pca(X)
    scores, _ = varimax_scores(X, pca, n_components=4, max_iter=500)
    return X, scores


@pytest.mark.parametrize("offset", [0.0, 1000.0])
def test_component_t_maps_match_textbook_ols_on_a_subset(offset):
    X, scores = _scores_and_matrix(offset)
    rows = np.arange(0, 80, 2)

    (maps,) = component_t_maps(X, scores, [rows], chunk_columns=17)

    np.testing.assert_allclose(maps.t, _reference_t(X[rows], scores[rows]), rtol=1e-6, atol=1e-8)
    assert maps.n_rows == 40
    assert maps.n_degenerate_voxels == 0


def test_component_t_maps_one_pass_serves_every_subset_and_chunking_changes_nothing():
    X, scores = _scores_and_matrix()
    first, second = np.arange(0, 80, 2), np.arange(1, 80, 2)

    together = component_t_maps(X, scores, [first, second], chunk_columns=13)
    alone = component_t_maps(X, scores, [second], chunk_columns=10_000)

    np.testing.assert_allclose(together[1].t, alone[0].t, atol=1e-9)


def test_component_t_maps_count_and_zero_a_voxel_constant_in_the_subset():
    X, scores = _scores_and_matrix()
    X = X.copy()
    rows = np.arange(0, 40)
    X[rows, 5] = 3.0  # constant within the subset, varying outside it

    (maps,) = component_t_maps(X, scores, [rows])

    assert maps.n_degenerate_voxels == 1
    np.testing.assert_array_equal(maps.t[:, 5], 0.0)
    assert np.abs(maps.t[:, 6]).max() > 0  # a neighbouring voxel is not affected


def test_component_t_maps_reject_a_subset_too_small_or_repeating_rows_or_mismatched_scores():
    X, scores = _scores_and_matrix()
    with pytest.raises(ValueError, match="needs more than 5 rows"):
        component_t_maps(X, scores, [np.arange(5)])
    with pytest.raises(ValueError, match="more than once"):
        component_t_maps(X, scores, [np.array([0, 1, 2, 3, 4, 5, 6, 6])])
    with pytest.raises(ValueError, match="do not match X"):
        component_t_maps(X, scores[:-1], [np.arange(20)])


def test_halves_of_a_structured_matrix_give_reproducible_maps():
    X, scores = _scores_and_matrix()
    first, second = component_t_maps(X, scores, [np.arange(0, 80, 2), np.arange(1, 80, 2)])

    assert map_reproducibility(first.t, second.t).min() > 0.8


def test_map_reproducibility_known_values_and_constant_map_raises():
    a = np.array([[1.0, 2.0, 3.0, 4.0], [1.0, 0.0, 1.0, 0.0]])
    np.testing.assert_allclose(map_reproducibility(a, a), [1.0, 1.0])
    np.testing.assert_allclose(map_reproducibility(a, -a), [-1.0, -1.0])
    with pytest.raises(ValueError, match="constant map"):
        map_reproducibility(a, np.vstack([a[0], np.ones(4)]))
    with pytest.raises(ValueError, match="same 2D shape"):
        map_reproducibility(a, a[:1])


def test_positive_peak_signs_flip_the_components_whose_strongest_voxel_is_negative():
    maps = np.array([[1.0, -5.0, 2.0], [3.0, 1.0, -2.0], [0.5, 0.1, 4.0]])

    signs = positive_peak_signs(maps)

    np.testing.assert_array_equal(signs, [-1.0, 1.0, 1.0])
    assert ((maps * signs[:, None])[np.arange(3), np.argmax(np.abs(maps), axis=1)] > 0).all()
