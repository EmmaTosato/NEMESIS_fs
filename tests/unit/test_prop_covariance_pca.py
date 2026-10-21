"""Property tests for src/analysis/covariance_pca.py.

Invarianti algebriche della PCA verificate su matrici casuali di forma qualunque (più soggetti che
feature e viceversa, 1 colonna, rango deficiente): la traccia degli autovalori è la varianza totale,
il percorso duale e quello sulla covarianza coincidono, le matrici di Gram dei punteggi non dipendono
da segni né da autovalori coincidenti (a differenza dei punteggi stessi), la rotazione ortogonale
conserva la varianza, la regressione dei punteggi ruotati ha residui ortogonali ai carichi. Completa
tests/unit/test_covariance_pca.py (confronti con sklearn su matrici strutturate) senza ripeterlo.
"""

import numpy as np
import pytest
from factor_analyzer.rotator import ORTHOGONAL_ROTATIONS
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra.numpy import arrays
from sklearn.decomposition import PCA

from src.analysis.covariance_pca import (
    CovariancePca,
    column_statistics,
    component_t_maps,
    components_for_share,
    fit_covariance_pca,
    leading_rotated_scores,
    map_reproducibility,
    nonzero_component_count,
    pca_scores,
    positive_peak_signs,
    resolve_n_components,
    rotated_scores,
    squared_correlation,
)

_floats = st.floats(-10.0, 10.0, allow_nan=False, allow_infinity=False)
_shapes = st.tuples(st.integers(3, 12), st.integers(1, 9))
matrices = _shapes.flatmap(lambda shape: arrays(np.float64, shape, elements=_floats))


def _varying_columns(X: np.ndarray) -> bool:
    return bool((X.std(axis=0, ddof=1) > 1e-3).all())


def _scaled(X: np.ndarray, standardize: bool) -> np.ndarray:
    centered = X - X.mean(axis=0)
    return centered / X.std(axis=0, ddof=1) if standardize else centered


def _structured(seed: int, n=30, p=24, k=3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    loadings = np.zeros((k, p))
    for i in range(k):
        loadings[i, i * (p // k) : (i + 1) * (p // k)] = rng.uniform(1, 2, size=p // k)
    return rng.normal(size=(n, k)) @ loadings + 0.2 * rng.normal(size=(n, p))


# --- autovalori ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("dual", [True, False])
@pytest.mark.parametrize("standardize", [False, True])
@given(X=matrices)
def test_eigenvalues_are_descending_nonnegative_and_sum_to_the_total_variance(dual, standardize, X):
    assume(_varying_columns(X) or not standardize)

    pca = fit_covariance_pca(X, standardize=standardize, dual=dual)

    assert (pca.eigenvalues >= 0).all() and (np.diff(pca.eigenvalues) <= 1e-12).all()
    total = X.shape[1] if standardize else X.var(axis=0, ddof=1).sum()
    assert pca.eigenvalues.sum() == pytest.approx(total, rel=1e-9, abs=1e-9)
    assert pca.n_nonzero_components() <= min(X.shape[0] - 1, X.shape[1])


@pytest.mark.parametrize("standardize", [False, True])
@given(X=matrices)
def test_dual_and_covariance_paths_have_the_same_spectrum_and_agree_with_sklearn(standardize, X):
    assume(_varying_columns(X) or not standardize)
    dual = fit_covariance_pca(X, standardize=standardize, dual=True).eigenvalues
    primal = fit_covariance_pca(X, standardize=standardize, dual=False).eigenvalues

    size = min(len(dual), len(primal))
    scale = max(dual.max(), 1e-12)
    np.testing.assert_allclose(dual[:size], primal[:size], atol=1e-9 * scale)
    reference = PCA(svd_solver="full").fit(_scaled(X, standardize)).explained_variance_
    np.testing.assert_allclose(primal[: len(reference)], reference, atol=1e-9 * scale)


@pytest.mark.parametrize("dual", [True, False])
@given(X=matrices, data=st.data())
def test_spectrum_does_not_depend_on_row_order_column_order_or_a_large_common_offset(dual, X, data):
    rows = np.asarray(data.draw(st.permutations(range(X.shape[0]))))
    columns = np.asarray(data.draw(st.permutations(range(X.shape[1]))))
    base = fit_covariance_pca(X, dual=dual).eigenvalues
    tolerance = 1e-8 * max(base.max(), 1.0)

    np.testing.assert_allclose(fit_covariance_pca(X[rows], dual=dual).eigenvalues, base, atol=tolerance)
    np.testing.assert_allclose(fit_covariance_pca(X[:, columns], dual=dual).eigenvalues, base, atol=tolerance)
    np.testing.assert_allclose(fit_covariance_pca(X + 1000.0, dual=dual).eigenvalues, base, atol=1e-6 * max(base.max(), 1.0))


@given(X=matrices, factors=st.lists(st.floats(0.1, 50.0), min_size=9, max_size=9))
def test_standardized_spectrum_ignores_the_unit_of_each_column(X, factors):
    assume(_varying_columns(X))
    scale = np.asarray(factors[: X.shape[1]])

    np.testing.assert_allclose(
        fit_covariance_pca(X * scale, standardize=True).eigenvalues, fit_covariance_pca(X, standardize=True).eigenvalues, atol=1e-8
    )


# --- punteggi ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("dual", [True, False])
@pytest.mark.parametrize("standardize", [False, True])
@given(X=matrices)
def test_all_components_reproduce_the_gram_matrix_of_the_centered_data_whatever_the_signs(dual, standardize, X):
    """S S^T = Z Z^T quando si tengono tutte le componenti con varianza: invariante a segno e a autovalori doppi."""
    assume(_varying_columns(X) or not standardize)
    pca = fit_covariance_pca(X, standardize=standardize, dual=dual)
    k = pca.n_nonzero_components()
    assume(k >= 1)
    Z = _scaled(X, standardize)

    scores = pca_scores(X, pca, k)

    np.testing.assert_allclose(scores @ scores.T, Z @ Z.T, atol=1e-7 * max(1.0, np.abs(Z @ Z.T).max()))


@pytest.mark.parametrize("dual", [True, False])
@given(X=matrices)
def test_scores_are_uncorrelated_with_variance_equal_to_the_eigenvalue(dual, X):
    pca = fit_covariance_pca(X, dual=dual)
    k = pca.n_nonzero_components()
    assume(k >= 1)

    scores = pca_scores(X, pca, k)

    covariance = np.cov(scores, rowvar=False).reshape(k, k)
    np.testing.assert_allclose(covariance, np.diag(pca.eigenvalues[:k]), atol=1e-8 * max(1.0, pca.eigenvalues[0]))


@given(X=matrices)
def test_dual_and_covariance_scores_span_the_same_norms(X):
    primal = fit_covariance_pca(X, dual=False)
    dual = fit_covariance_pca(X, dual=True)
    k = min(primal.n_nonzero_components(), dual.n_nonzero_components())
    assume(k >= 1)

    norms_primal = np.linalg.norm(pca_scores(X, primal, k), axis=0)
    norms_dual = np.linalg.norm(pca_scores(X, dual, k), axis=0)

    np.testing.assert_allclose(norms_primal, norms_dual, atol=1e-7 * max(1.0, norms_dual.max()))


@given(X=matrices, offset=st.sampled_from([0.0, 1000.0]))
def test_the_single_column_matrix_has_one_component_whose_variance_is_the_column_variance(X, offset):
    column = X[:, :1] + offset
    assume(column.std(ddof=1) > 1e-3)

    pca = fit_covariance_pca(column, dual=False)

    assert pca.eigenvalues.shape == (1,)
    assert pca.eigenvalues[0] == pytest.approx(column.var(ddof=1), rel=1e-6)
    assert nonzero_component_count(pca.eigenvalues) == 1


# --- quanti componenti ---------------------------------------------------------------------------------------


_spectra = st.lists(st.floats(0.01, 100.0), min_size=1, max_size=15).map(lambda v: np.sort(np.asarray(v))[::-1])


@given(eigenvalues=_spectra, share=st.floats(0.001, 1.0), trailing_zeros=st.integers(0, 3))
def test_components_for_share_is_the_smallest_count_whose_cumulative_share_reaches_it(eigenvalues, share, trailing_zeros):
    padded = np.concatenate([eigenvalues, np.zeros(trailing_zeros)])

    k = components_for_share(padded, share)

    cumulative = np.cumsum(eigenvalues / eigenvalues.sum())
    assert 1 <= k <= len(eigenvalues)  # mai oltre le componenti con varianza, nemmeno per share=1.0
    assert cumulative[k - 1] >= share - 1e-12
    assert k == 1 or cumulative[k - 2] < share + 1e-12


@given(eigenvalues=_spectra, low=st.floats(0.001, 1.0), high=st.floats(0.001, 1.0))
def test_components_for_share_grows_with_the_share(eigenvalues, low, high):
    low, high = sorted((low, high))

    assert components_for_share(eigenvalues, low) <= components_for_share(eigenvalues, high)


@given(eigenvalues=_spectra)
def test_asking_for_the_whole_variance_keeps_exactly_the_nonzero_components(eigenvalues):
    padded = np.concatenate([eigenvalues, np.zeros(2)])

    assert components_for_share(padded, 1.0) == len(eigenvalues) == nonzero_component_count(padded)


@pytest.mark.parametrize("share", [0.0, -0.5, 1.0000001, float("nan")])
def test_components_for_share_rejects_a_share_outside_the_half_open_unit_interval(share):
    with pytest.raises(ValueError, match="share must be in"):
        components_for_share(np.array([3.0, 2.0, 1.0]), share)


@given(eigenvalues=_spectra, n=st.integers(1, 20), share=st.floats(0.01, 1.0))
def test_resolve_n_components_takes_exactly_one_of_count_or_share(eigenvalues, n, share):
    with pytest.raises(ValueError, match="exactly one"):
        resolve_n_components(eigenvalues, None, None)
    with pytest.raises(ValueError, match="exactly one"):
        resolve_n_components(eigenvalues, n, share)
    assert resolve_n_components(eigenvalues, None, share) == components_for_share(eigenvalues, share)
    if n <= len(eigenvalues):
        assert resolve_n_components(eigenvalues, n, None) == n
    else:
        with pytest.raises(ValueError, match="between 1 and"):
            resolve_n_components(eigenvalues, n, None)


def test_a_spectrum_without_variance_never_resolves_to_zero_components():
    with pytest.raises(ValueError, match="no variance"):
        resolve_n_components(np.zeros(4), None, 0.5)
    with pytest.raises(ValueError, match="no variance"):
        components_for_share(np.zeros(4), 0.5)


# --- rotazione -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("rotation", ORTHOGONAL_ROTATIONS)
@pytest.mark.parametrize("dual", [True, False])
@pytest.mark.parametrize("seed", [0, 1])
def test_an_orthogonal_rotation_keeps_the_loading_gram_spectrum_and_scores_have_unit_variance(rotation, dual, seed):
    X = _structured(seed)
    pca = fit_covariance_pca(X, dual=dual)

    scores, loadings = rotated_scores(X, pca, 3, rotation, 500)

    np.testing.assert_allclose(np.linalg.eigvalsh(loadings.T @ loadings)[::-1], pca.eigenvalues[:3], rtol=1e-6)
    np.testing.assert_allclose(scores.var(axis=0, ddof=1), 1.0, rtol=1e-6)
    np.testing.assert_allclose(np.cov(scores, rowvar=False), np.eye(3), atol=1e-6)


@pytest.mark.parametrize("rotation", ["varimax", "quartimax"])
@given(seed=st.integers(0, 40), n=st.integers(12, 25), p=st.integers(8, 20))
@settings(max_examples=12)
def test_rotated_scores_are_the_least_squares_coefficients_of_the_data_on_the_rotated_loadings(rotation, seed, n, p):
    """Residuo ortogonale ai carichi: (Z - S L^T) L = 0, cioè S risolve davvero la regressione."""
    X = _structured(seed, n=n, p=p - p % 3 or 3)
    pca = fit_covariance_pca(X)
    scores, loadings = rotated_scores(X, pca, 3, rotation, 500)

    residual = (X - X.mean(axis=0)) - scores @ loadings.T

    np.testing.assert_allclose(residual @ loadings, 0.0, atol=1e-6 * max(1.0, np.abs(X).max()))


@given(seed=st.integers(0, 40), n_kept=st.integers(1, 4))
@settings(max_examples=12)
def test_leading_rotated_scores_return_the_largest_shares_most_first_and_their_total(seed, n_kept):
    X = _structured(seed, n=28, p=24, k=4)
    pca = fit_covariance_pca(X)

    kept_scores, share = leading_rotated_scores(X, pca, 4, n_kept, "varimax", 500)
    all_scores, loadings = rotated_scores(X, pca, 4, "varimax", 500)

    shares = (loadings**2).sum(axis=0) / pca.eigenvalues.sum()
    expected = np.sort(shares)[::-1][:n_kept]
    assert share == pytest.approx(expected.sum())
    assert kept_scores.shape == (28, n_kept)
    kept_variance = (kept_scores**2).sum(axis=0)  # unità di varianza: la quota si legge dai carichi, non dai punteggi
    assert kept_variance == pytest.approx(np.full(n_kept, 27.0), rel=1e-6)
    assert shares.sum() == pytest.approx(pca.eigenvalues[:4].sum() / pca.eigenvalues.sum())
    assert all(any(np.allclose(k, a) for a in all_scores.T) for k in kept_scores.T)


# --- column_statistics ---------------------------------------------------------------------------------------


@given(X=matrices, chunk=st.integers(1, 4))
def test_column_statistics_match_numpy_and_do_not_depend_on_the_chunk(X, chunk):
    means, scales = column_statistics(X, standardize=True, chunk_columns=chunk) if _varying_columns(X) else (None, None)
    plain_means, plain_scales = column_statistics(X, standardize=False, chunk_columns=chunk)

    np.testing.assert_allclose(plain_means, X.mean(axis=0))
    np.testing.assert_array_equal(plain_scales, 1.0)
    if means is not None:
        np.testing.assert_allclose(means, X.mean(axis=0))
        np.testing.assert_allclose(scales, X.std(axis=0, ddof=1))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
@given(X=matrices, data=st.data())
def test_a_non_finite_value_anywhere_is_rejected_by_statistics_and_by_the_fit(bad, X, data):
    X = X.copy()
    X[data.draw(st.integers(0, X.shape[0] - 1)), data.draw(st.integers(0, X.shape[1] - 1))] = bad

    with pytest.raises(ValueError, match="NaN or infinite"):
        column_statistics(X, standardize=False)
    with pytest.raises(ValueError, match="NaN or infinite"):
        fit_covariance_pca(X)


@given(X=matrices, data=st.data())
def test_a_constant_column_is_an_error_only_when_standardizing(X, data):
    X = X.copy()
    X[:, data.draw(st.integers(0, X.shape[1] - 1))] = 3.0

    with pytest.raises(ValueError, match="constant"):
        column_statistics(X, standardize=True)
    means, scales = column_statistics(X, standardize=False)
    assert np.isfinite(means).all() and (scales == 1.0).all()


@pytest.mark.parametrize("shape", [(2, 5), (1, 5), (0, 5)])
def test_a_matrix_with_fewer_than_three_rows_is_rejected(shape):
    with pytest.raises(ValueError, match="at least 3 rows"):
        fit_covariance_pca(np.ones(shape))


def test_a_one_dimensional_array_and_a_zero_chunk_are_rejected():
    with pytest.raises(ValueError, match="2D matrix"):
        fit_covariance_pca(np.arange(6.0))
    with pytest.raises(ValueError, match="chunk_columns"):
        fit_covariance_pca(np.eye(4), chunk_columns=0)


@pytest.mark.parametrize("dual", [True, False])
def test_a_constant_matrix_has_a_zero_spectrum_and_no_component_to_keep(dual):
    pca = fit_covariance_pca(np.full((5, 4), 2.5), dual=dual)

    np.testing.assert_array_equal(pca.eigenvalues, 0.0)
    assert pca.n_nonzero_components() == 0
    with pytest.raises(ValueError, match="between 1 and 0"):
        pca_scores(np.full((5, 4), 2.5), pca, 1)


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"eigenvalues": np.ones(3)}, "needs 5 eigenvalues"),
        ({"column_scales": np.ones(3)}, "column_scales has shape"),
        ({"left_vectors": np.eye(4)}, "5, 5"),
    ],
)
def test_the_model_object_rejects_inconsistent_shapes(overrides, message):
    fields = dict(
        eigenvalues=np.ones(5), column_means=np.zeros(4), column_scales=np.ones(4), standardized=False, n_samples=5, left_vectors=np.eye(5)
    )
    fields.update(overrides)

    with pytest.raises(ValueError, match=message):
        CovariancePca(**fields)


# --- squared_correlation -------------------------------------------------------------------------------------


@st.composite
def scores_and_covariate(draw):
    n = draw(st.integers(4, 15))
    k = draw(st.integers(1, 4))
    scores = draw(arrays(np.float64, (n, k), elements=_floats))
    covariate = draw(arrays(np.float64, n, elements=_floats))
    assume(scores.std(axis=0).min() > 1e-3 and covariate.std() > 1e-3)
    return scores, covariate


@given(case=scores_and_covariate())
def test_squared_correlation_is_the_squared_pearson_correlation_and_lies_in_the_unit_interval(case):
    scores, covariate = case

    r2 = squared_correlation(scores, covariate)

    expected = np.array([np.corrcoef(scores[:, j], covariate)[0, 1] ** 2 for j in range(scores.shape[1])])
    np.testing.assert_allclose(r2, expected, atol=1e-10)
    assert ((r2 >= 0) & (r2 <= 1 + 1e-12)).all()


@given(case=scores_and_covariate(), slope=st.floats(0.1, 50.0), negative=st.booleans(), shift=st.sampled_from([0.0, 1000.0, -37.5]))
def test_squared_correlation_ignores_the_sign_scale_and_offset_of_the_covariate_and_of_the_scores(case, slope, negative, shift):
    scores, covariate = case
    transformed = (-slope if negative else slope) * covariate + shift

    np.testing.assert_allclose(squared_correlation(scores, transformed), squared_correlation(scores, covariate), atol=1e-8)
    np.testing.assert_allclose(squared_correlation(scores * slope + shift, covariate), squared_correlation(scores, covariate), atol=1e-8)


@given(case=scores_and_covariate())
def test_a_covariate_that_is_a_linear_function_of_a_score_has_r_squared_one_on_it(case):
    scores, _ = case

    r2 = squared_correlation(scores, 3.0 * scores[:, 0] - 2.0)

    assert r2[0] == pytest.approx(1.0)


def test_a_constant_score_column_is_rejected_instead_of_giving_nan():
    scores = np.column_stack([np.ones(5), np.arange(5.0)])

    with pytest.raises(ValueError, match=r"score column\(s\) \[0\] are constant"):
        squared_correlation(scores, np.arange(5.0) ** 2)


@pytest.mark.parametrize("scores_shape, covariate_shape", [((5, 2), (4,)), ((5,), (5,)), ((5, 2), (5, 1))])
def test_squared_correlation_rejects_misaligned_shapes(scores_shape, covariate_shape):
    with pytest.raises(ValueError, match="do not align"):
        squared_correlation(np.ones(scores_shape), np.ones(covariate_shape))


# --- map_reproducibility / positive_peak_signs --------------------------------------------------------------


@st.composite
def map_pairs(draw):
    shape = (draw(st.integers(1, 4)), draw(st.integers(3, 12)))
    a = draw(arrays(np.float64, shape, elements=_floats))
    b = draw(arrays(np.float64, shape, elements=_floats))
    assume(a.std(axis=1).min() > 1e-3 and b.std(axis=1).min() > 1e-3)
    return a, b


@given(pair=map_pairs())
def test_reproducibility_is_the_row_wise_pearson_correlation_symmetric_and_bounded(pair):
    a, b = pair

    r = map_reproducibility(a, b)

    np.testing.assert_allclose(r, [np.corrcoef(x, y)[0, 1] for x, y in zip(a, b)], atol=1e-10)
    np.testing.assert_allclose(r, map_reproducibility(b, a), atol=1e-12)
    assert ((r >= -1 - 1e-12) & (r <= 1 + 1e-12)).all()
    np.testing.assert_allclose(map_reproducibility(a, a), 1.0, atol=1e-10)


@given(pair=map_pairs(), scale=st.floats(0.1, 20.0), shift=st.floats(-100, 100))
def test_reproducibility_ignores_a_positive_affine_change_and_flips_sign_under_negation(pair, scale, shift):
    a, b = pair

    np.testing.assert_allclose(map_reproducibility(a * scale + shift, b), map_reproducibility(a, b), atol=1e-8)
    np.testing.assert_allclose(map_reproducibility(-a, b), -map_reproducibility(a, b), atol=1e-10)


def test_reproducibility_rejects_a_constant_map_and_mismatched_shapes():
    good = np.arange(10.0).reshape(2, 5)
    with pytest.raises(ValueError, match="constant map"):
        map_reproducibility(np.vstack([good[0], np.ones(5)]), good)
    with pytest.raises(ValueError, match="same 2D shape"):
        map_reproducibility(good, good[:, :4])
    with pytest.raises(ValueError, match="same 2D shape"):
        map_reproducibility(good[0], good[0])


@given(maps=_shapes.flatmap(lambda s: arrays(np.float64, s, elements=_floats)))
def test_positive_peak_signs_make_the_strongest_voxel_of_each_map_positive_and_are_idempotent(maps):
    signs = positive_peak_signs(maps)

    assert set(np.unique(signs)) <= {-1.0, 1.0}
    oriented = maps * signs[:, None]
    peak = np.argmax(np.abs(maps), axis=1)
    assert (oriented[np.arange(len(maps)), peak] >= 0).all()
    np.testing.assert_array_equal(positive_peak_signs(oriented), 1.0)
    np.testing.assert_array_equal(positive_peak_signs(-maps)[np.abs(maps).max(axis=1) > 0], -signs[np.abs(maps).max(axis=1) > 0])


# --- component_t_maps ----------------------------------------------------------------------------------------


@st.composite
def regression_case(draw):
    n = draw(st.integers(8, 16))
    k = draw(st.integers(1, 3))
    p = draw(st.integers(1, 6))
    scores = draw(arrays(np.float64, (n, k), elements=_floats))
    X = draw(arrays(np.float64, (n, p), elements=_floats))
    assume(np.linalg.svd(scores - scores.mean(axis=0), compute_uv=False).min() > 1e-2)
    assume((X.std(axis=0) > 1e-2).all())
    return X, scores


@given(case=regression_case())
def test_t_maps_equal_the_textbook_ols_t_statistics_of_each_component(case):
    """Calcolo indipendente: lstsq su [1, scores], varianza residua con n-k-1 gradi di libertà, errore standard da (D'D)^-1."""
    X, scores = case
    n, k = scores.shape
    design = np.column_stack([np.ones(n), scores])
    coefficients, *_ = np.linalg.lstsq(design, X, rcond=None)
    residual_variance = ((X - design @ coefficients) ** 2).sum(axis=0) / (n - k - 1)
    assume((residual_variance > 1e-8).all())
    standard_error = np.sqrt(np.diag(np.linalg.inv(design.T @ design))[1:, None] * residual_variance[None, :])

    result = component_t_maps(X, scores, [np.arange(n)])[0]

    np.testing.assert_allclose(result.t, coefficients[1:] / standard_error, rtol=1e-6, atol=1e-6)


@given(case=regression_case(), data=st.data())
def test_t_maps_do_not_depend_on_the_order_of_rows_in_a_subset_or_the_order_of_voxels(case, data):
    X, scores = case
    n = len(X)
    rows = np.arange(n)
    shuffled_rows = np.asarray(data.draw(st.permutations(range(n))))
    voxels = np.asarray(data.draw(st.permutations(range(X.shape[1]))))

    base = component_t_maps(X, scores, [rows])[0]

    np.testing.assert_allclose(component_t_maps(X, scores, [shuffled_rows])[0].t, base.t, atol=1e-7)
    np.testing.assert_allclose(component_t_maps(X[:, voxels], scores, [rows])[0].t, base.t[:, voxels], atol=1e-7)
    assert base.n_rows == n


@given(case=regression_case(), scale=st.floats(0.1, 30.0), shift=st.sampled_from([0.0, 1000.0, -250.0]))
def test_t_maps_ignore_the_scale_sign_and_offset_of_a_voxel_and_the_scale_of_the_scores(case, scale, shift):
    X, scores = case
    rows = [np.arange(len(X))]
    base = component_t_maps(X, scores, rows)[0]

    np.testing.assert_allclose(component_t_maps(X * scale + shift, scores, rows)[0].t, base.t, atol=1e-6)
    np.testing.assert_allclose(component_t_maps(-X, scores, rows)[0].t, -base.t, atol=1e-7)
    np.testing.assert_allclose(component_t_maps(X, scores * scale + shift, rows)[0].t, base.t, atol=1e-6)


@given(case=regression_case(), constant=st.sampled_from([0.0, 1.0, -2.0, 0.5, 4.0]))
def test_a_voxel_constant_in_the_subset_gets_t_zero_and_is_counted_never_dropped(case, constant):
    X, scores = case
    X = X.copy()
    X[:, 0] = constant

    result = component_t_maps(X, scores, [np.arange(len(X))])[0]

    np.testing.assert_array_equal(result.t[:, 0], 0.0)
    assert result.n_degenerate_voxels >= 1
    assert np.isfinite(result.t).all()
    assert result.t.shape == (scores.shape[1], X.shape[1])


def test_a_constant_voxel_is_counted_as_degenerate_whatever_its_value():
    scores = np.random.default_rng(0).normal(size=(11, 2))

    result = component_t_maps(np.full((11, 1), 0.3), scores, [np.arange(11)])[0]

    assert result.n_degenerate_voxels == 1


@given(case=regression_case())
def test_a_voxel_made_of_the_scores_themselves_is_degenerate_not_infinite(case):
    X, scores = case
    X = np.column_stack([scores @ np.ones(scores.shape[1]) + 5.0, X])

    result = component_t_maps(X, scores, [np.arange(len(X))])[0]

    assert np.isfinite(result.t).all() and result.n_degenerate_voxels >= 1
    np.testing.assert_array_equal(result.t[:, 0], 0.0)
