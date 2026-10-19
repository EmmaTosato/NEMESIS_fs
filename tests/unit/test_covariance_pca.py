"""Unit tests for src/analysis/covariance_pca.py - synthetic matrices, no real data required."""

import itertools

import numpy as np
import pytest
from factor_analyzer.rotator import ORTHOGONAL_ROTATIONS, Rotator
from sklearn.decomposition import PCA

from src.analysis.covariance_pca import (
    CovariancePca,
    component_t_maps,
    fit_covariance_pca,
    leading_rotated_scores,
    map_reproducibility,
    pca_embedding,
    pca_scores,
    positive_peak_signs,
    resolve_n_components,
    rotated_scores,
    squared_correlation,
)


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


def _scaled(X: np.ndarray, standardize: bool) -> np.ndarray:
    centered = X - X.mean(axis=0)
    return centered / X.std(axis=0, ddof=1) if standardize else centered


def _sklearn_varimax_reference(X: np.ndarray, n_components: int, standardize: bool = False) -> np.ndarray:
    """The in-memory reference: sklearn PCA, varimax on the factor loadings, scores by least squares."""
    Z = _scaled(X, standardize)
    fitted = PCA(n_components=n_components).fit(Z)
    loadings = fitted.components_.T * np.sqrt(fitted.explained_variance_)
    rotated = Rotator(method="varimax", max_iter=500).fit_transform(loadings)
    return np.linalg.lstsq(rotated, Z.T, rcond=None)[0].T


def test_varimax_scores_match_the_sklearn_reference():
    """The memory-light path computes the same scores as sklearn PCA + Rotator + least squares,
    up to the sign and order of each rotated component."""
    X = _structured_matrix(offset=1000.0)
    k = 4
    pca = fit_covariance_pca(X, chunk_columns=50)

    scores, rotated = rotated_scores(X, pca, k, "varimax", 500, chunk_columns=50)
    reference = _sklearn_varimax_reference(X, k)

    assert scores.shape == (X.shape[0], k)
    assert rotated.shape == (X.shape[1], k)
    assert _match_up_to_sign_and_order(scores, reference) > 0.999


def test_varimax_scores_chunk_size_does_not_change_the_result():
    X = _structured_matrix()
    pca = fit_covariance_pca(X)
    scores_whole, _ = rotated_scores(X, pca, 4, "varimax", 500, chunk_columns=10_000)
    scores_chunked, _ = rotated_scores(X, pca, 4, "varimax", 500, chunk_columns=13)

    np.testing.assert_allclose(scores_chunked, scores_whole, atol=1e-8)


def test_varimax_separates_the_latent_factors():
    """Each rotated component loads on one block of 50 features: the property varimax exists for.
    A plain PCA of the same data mixes the blocks."""
    X = _structured_matrix()  # 200 features = 4 blocks of 50
    pca = fit_covariance_pca(X)
    _, rotated = rotated_scores(X, pca, 4, "varimax", 500)

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
        rotated_scores(X, pca, n_components, "varimax", 500)


def test_varimax_rejects_more_components_than_the_matrix_has():
    X = _structured_matrix(n_samples=10, n_features=50)
    pca = fit_covariance_pca(X)
    with pytest.raises(ValueError, match="n_components must be between 1 and 9"):
        rotated_scores(X, pca, 10, "varimax", 500)  # n-1 = 9 after centering


def test_varimax_rejects_a_matrix_other_than_the_fitted_one():
    pca = fit_covariance_pca(_structured_matrix())
    with pytest.raises(ValueError, match="PCA was fitted on"):
        rotated_scores(_structured_matrix(n_features=150), pca, 3, "varimax", 500)


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
    scores = pca_scores(X, fit_covariance_pca(X, chunk_columns=64), 6)
    reference = PCA(n_components=6).fit_transform(X)

    assert _match_up_to_sign_and_order(scores, reference) > 1 - 1e-9
    np.testing.assert_allclose(np.abs(scores), np.abs(reference), atol=1e-6)


@pytest.mark.parametrize("n_components", [0, 10])
def test_pca_scores_reject_an_out_of_range_n_components(n_components):
    X = _structured_matrix(n_samples=10, n_features=50)
    with pytest.raises(ValueError, match="n_components must be between 1 and 9"):
        pca_scores(X, fit_covariance_pca(X), n_components)


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
    scores, _ = rotated_scores(X, pca, 4, "varimax", 500)
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


# --- standardize / dual / rotation / n_components, against sklearn -------------------------------

_ALL_PATHS = list(itertools.product([False, True], [True, False]))  # (standardize, dual)


@pytest.mark.parametrize("standardize,dual", _ALL_PATHS)
@pytest.mark.parametrize("offset", [0.0, 1000.0])
def test_every_path_matches_sklearn_pca_on_the_scaled_matrix(standardize, dual, offset):
    X = _structured_matrix(offset=offset)
    pca = fit_covariance_pca(X, standardize=standardize, dual=dual, chunk_columns=64)
    reference = PCA().fit(_scaled(X, standardize))

    k = 20
    np.testing.assert_allclose(pca.eigenvalues[:k], reference.explained_variance_[:k], rtol=1e-8)
    np.testing.assert_allclose(pca.explained_variance_ratio[:k], reference.explained_variance_ratio_[:k], rtol=1e-8)
    scores = pca_scores(X, pca, 6)
    np.testing.assert_allclose(np.abs(scores), np.abs(PCA(n_components=6).fit_transform(_scaled(X, standardize))), atol=1e-6)
    assert pca.dual is dual and pca.standardized is standardize


def test_standardize_changes_the_components_when_features_have_unequal_spread():
    X = _structured_matrix()
    X[:, :20] *= 50.0  # one block of features with a much larger spread
    covariance = fit_covariance_pca(X, standardize=False)
    correlation = fit_covariance_pca(X, standardize=True)

    assert not np.allclose(covariance.explained_variance_ratio[:4], correlation.explained_variance_ratio[:4], rtol=0.05)
    # the correlation matrix has unit diagonal: the variance to explain is the number of features
    assert correlation.eigenvalues.sum() == pytest.approx(X.shape[1])


@pytest.mark.parametrize("dual", [True, False])
def test_chunk_size_does_not_change_either_path(dual):
    X = _structured_matrix()
    whole = fit_covariance_pca(X, dual=dual, chunk_columns=10_000)
    chunked = fit_covariance_pca(X, dual=dual, chunk_columns=7)

    np.testing.assert_allclose(chunked.eigenvalues, whole.eigenvalues, rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(pca_scores(X, chunked, 5, chunk_columns=7), pca_scores(X, whole, 5), atol=1e-8)


@pytest.mark.parametrize("standardize", [False, True])
def test_dual_and_covariance_paths_give_the_same_rotated_scores(standardize):
    X = _structured_matrix(offset=1000.0)
    dual = fit_covariance_pca(X, standardize=standardize, dual=True, chunk_columns=50)
    direct = fit_covariance_pca(X, standardize=standardize, dual=False, chunk_columns=50)

    scores_dual, _ = rotated_scores(X, dual, 4, "varimax", 500, chunk_columns=50)
    scores_direct, _ = rotated_scores(X, direct, 4, "varimax", 500, chunk_columns=50)

    assert _match_up_to_sign_and_order(scores_dual, scores_direct) > 0.999
    assert _match_up_to_sign_and_order(scores_direct, _sklearn_varimax_reference(X, 4, standardize)) > 0.999


@pytest.mark.parametrize("rotation", [name for name in ORTHOGONAL_ROTATIONS])
def test_every_orthogonal_rotation_keeps_the_total_variance_of_the_loadings(rotation):
    X = _structured_matrix()
    pca = fit_covariance_pca(X)
    fitted = PCA(n_components=4).fit(X - X.mean(axis=0))
    loadings = fitted.components_.T * np.sqrt(fitted.explained_variance_)

    scores, rotated = rotated_scores(X, pca, 4, rotation, 500)

    assert scores.shape == (X.shape[0], 4)
    assert (rotated**2).sum() == pytest.approx((loadings**2).sum(), rel=1e-8)


def test_rotated_scores_have_unit_variance_and_the_unrotated_ones_keep_their_variance():
    X = _structured_matrix()
    pca = fit_covariance_pca(X)
    rotated, _ = rotated_scores(X, pca, 4, "varimax", 500)

    np.testing.assert_allclose(rotated.var(axis=0, ddof=1), 1.0, rtol=1e-8)
    np.testing.assert_allclose(pca_scores(X, pca, 4).var(axis=0, ddof=1), pca.eigenvalues[:4], rtol=1e-8)


@pytest.mark.parametrize("rotation", ["promax", "oblimin", "none", "bogus"])
def test_rotated_scores_reject_what_is_not_an_orthogonal_rotation(rotation):
    X = _structured_matrix()
    with pytest.raises(ValueError, match="not an orthogonal rotation"):
        rotated_scores(X, fit_covariance_pca(X), 4, rotation, 500)


def test_pca_embedding_dispatches_on_rotation_and_rejects_an_unknown_one():
    X = _structured_matrix()
    pca = fit_covariance_pca(X)

    np.testing.assert_allclose(pca_embedding(X, pca, 4, "none", 500), pca_scores(X, pca, 4))
    np.testing.assert_allclose(pca_embedding(X, pca, 4, "varimax", 500), rotated_scores(X, pca, 4, "varimax", 500)[0])
    with pytest.raises(ValueError, match="rotation must be one of"):
        pca_embedding(X, pca, 4, "bogus", 500)


# --- n_components / variance_share ---------------------------------------------------------------


def test_resolve_n_components_takes_exactly_one_of_the_two():
    pca = fit_covariance_pca(_structured_matrix())

    assert resolve_n_components(pca.eigenvalues, 7, None) == 7
    assert resolve_n_components(pca.eigenvalues, None, 0.9) == pca.n_components_for(0.9)
    for both_or_neither in [(None, None), (5, 0.9)]:
        with pytest.raises(ValueError, match="exactly one of n_components and variance_share"):
            resolve_n_components(pca.eigenvalues, *both_or_neither)


def test_resolve_n_components_rejects_a_count_beyond_the_components_with_variance():
    pca = fit_covariance_pca(_structured_matrix(n_samples=10, n_features=50))
    with pytest.raises(ValueError, match="between 1 and 9"):
        resolve_n_components(pca.eigenvalues, 10, None)


def test_variance_share_gives_a_different_count_on_matrices_with_different_spectra():
    """The point of variance_share: the same 90% needs fewer components on a low-rank matrix."""
    low_rank = fit_covariance_pca(_structured_matrix(n_latent=2))
    high_rank = fit_covariance_pca(_structured_matrix(n_latent=8))

    assert resolve_n_components(low_rank.eigenvalues, None, 0.9) < resolve_n_components(high_rank.eigenvalues, None, 0.9)


# --- guards: nothing is silently dropped, ignored or allocated -----------------------------------


def test_standardize_rejects_a_constant_column():
    X = _structured_matrix()
    X[:, 5] = 3.0
    X[:, 17] = 0.0
    with pytest.raises(ValueError, match=r"2 column\(s\) are constant.*\[5, 17\]"):
        fit_covariance_pca(X, standardize=True)
    fit_covariance_pca(X, standardize=False)  # a constant column is harmless to a covariance PCA


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_fit_rejects_nan_and_infinite_values(bad):
    X = _structured_matrix()
    X[3, 10] = bad
    with pytest.raises(ValueError, match="NaN or infinite"):
        fit_covariance_pca(X)


@pytest.mark.parametrize("dual,side,hint", [(True, 60, "dual=False"), (False, 200, "dual=True")])
def test_fit_refuses_to_build_a_square_matrix_above_the_memory_ceiling(dual, side, hint):
    X = _structured_matrix(n_samples=60, n_features=200)
    with pytest.raises(ValueError, match=rf"{side} x {side}.*{hint}"):
        fit_covariance_pca(X, dual=dual, max_matrix_gib=1e-9)


def test_the_two_vector_sets_cannot_both_or_neither_be_given():
    pca = fit_covariance_pca(_structured_matrix(n_samples=10, n_features=20))
    common = dict(
        eigenvalues=pca.eigenvalues, column_means=pca.column_means, column_scales=pca.column_scales,
        standardized=False, n_samples=10,
    )
    with pytest.raises(ValueError, match="exactly one of left_vectors"):
        CovariancePca(**common)
    with pytest.raises(ValueError, match="exactly one of left_vectors"):
        CovariancePca(**common, left_vectors=pca.left_vectors, right_vectors=pca.left_vectors)
    with pytest.raises(ValueError, match="eigenvalues"):
        CovariancePca(**{**common, "eigenvalues": pca.eigenvalues[:5]}, left_vectors=pca.left_vectors)


@pytest.mark.parametrize("dual", [True, False])
def test_a_saved_model_loads_back_identical_and_gives_the_same_scores(dual, tmp_path):
    X = _structured_matrix()
    pca = fit_covariance_pca(X, standardize=True, dual=dual)
    path = tmp_path / "model.npz"

    pca.save(path)
    loaded = CovariancePca.load(path)

    assert loaded.dual is dual and loaded.standardized is True and loaded.n_samples == pca.n_samples
    np.testing.assert_array_equal(loaded.eigenvalues, pca.eigenvalues)
    np.testing.assert_array_equal(pca_scores(X, loaded, 5), pca_scores(X, pca, 5))
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("bad", [2.5, True, 0, "3"])
def test_resolve_n_components_rejects_a_non_integer_or_non_positive_count(bad):
    pca = fit_covariance_pca(_structured_matrix())
    with pytest.raises(ValueError, match="n_components must be an integer"):
        resolve_n_components(pca.eigenvalues, bad, None)


# --- leading_rotated_scores ----------------------------------------------------------------------------------


def _rotated_shares(X, n_rotated):
    pca = fit_covariance_pca(X)
    scores, loadings = rotated_scores(X, pca, n_rotated, "varimax", 500)
    return pca, scores, (loadings**2).sum(axis=0) / pca.eigenvalues.sum()


def test_leading_rotated_scores_are_the_rotated_components_that_explain_the_most_variance_most_first():
    X = _structured_matrix(n_latent=5)
    pca, scores, shares = _rotated_shares(X, 10)
    # the fixture must leave the rotated columns out of order, or the sort below proves nothing
    assert not np.all(np.diff(shares) <= 0)

    kept, explained = leading_rotated_scores(X, pca, 10, 3, "varimax", 500)

    expected = np.argsort(-shares, kind="stable")[:3]
    np.testing.assert_allclose(kept, scores[:, expected], atol=1e-10)
    assert explained == pytest.approx(shares[expected].sum())
    assert np.all(np.diff(shares[expected]) <= 0)


def test_leading_rotated_scores_keeping_every_rotated_component_only_reorders_them():
    X = _structured_matrix(n_latent=5)
    pca, scores, shares = _rotated_shares(X, 6)

    kept, explained = leading_rotated_scores(X, pca, 6, 6, "varimax", 500)

    np.testing.assert_allclose(kept, scores[:, np.argsort(-shares, kind="stable")], atol=1e-10)
    assert explained == pytest.approx(pca.cumulative_variance_ratio[5])


def test_leading_rotated_scores_of_a_smaller_k_are_the_start_of_the_larger_ones():
    X = _structured_matrix(n_latent=5)
    pca = fit_covariance_pca(X)

    two, _ = leading_rotated_scores(X, pca, 10, 2, "varimax", 500)
    five, _ = leading_rotated_scores(X, pca, 10, 5, "varimax", 500)

    np.testing.assert_allclose(two, five[:, :2], atol=1e-10)


@pytest.mark.parametrize("n_kept", [0, 11])
def test_leading_rotated_scores_reject_keeping_more_than_the_rotated_or_nothing(n_kept):
    X = _structured_matrix()
    with pytest.raises(ValueError, match="n_kept must be between 1 and n_rotated=10"):
        leading_rotated_scores(X, fit_covariance_pca(X), 10, n_kept, "varimax", 500)
