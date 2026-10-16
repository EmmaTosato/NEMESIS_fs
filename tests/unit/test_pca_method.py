"""Unit tests for src/analysis/pca_method.py - the `pca` params contract and the two solvers."""

import itertools

import numpy as np
import pytest

from src.analysis.pca_method import decomposition_spectra, fit_pca, fit_pca_embedding

_X = np.random.default_rng(0).normal(size=(40, 12)) * np.linspace(3.0, 0.5, 12) + 100.0

_BLOCKS = {"solver": "blocks", "standardize": False, "dual": True, "rotation": "none"}
_SKLEARN = {"solver": "sklearn", "standardize": False, "rotation": "none"}


def _agree_up_to_sign(a: np.ndarray, b: np.ndarray) -> bool:
    return bool(np.allclose(np.abs(a), np.abs(b), atol=1e-8))


@pytest.mark.parametrize("standardize,dual", list(itertools.product([False, True], [True, False])))
def test_blocks_solver_matches_sklearn_solver(standardize, dual):
    """Four paths to one answer: the same embedding (up to the sign of each component) and the same score."""
    sizing = {"n_components": 5}
    blocks, blocks_score = fit_pca_embedding(_X, {**_BLOCKS, "standardize": standardize, "dual": dual, **sizing})
    reference, reference_score = fit_pca_embedding(_X, {**_SKLEARN, "standardize": standardize, **sizing})

    assert blocks.shape == reference.shape == (40, 5)
    assert _agree_up_to_sign(blocks, reference)
    assert blocks_score == pytest.approx(reference_score)


@pytest.mark.parametrize("solver_params", [_BLOCKS, _SKLEARN])
def test_variance_share_keeps_the_smallest_number_of_components_that_reaches_it(solver_params):
    embedding, score = fit_pca_embedding(_X, {**solver_params, "variance_share": 0.9})
    fewer, fewer_score = fit_pca_embedding(_X, {**solver_params, "n_components": embedding.shape[1] - 1})

    assert score >= 0.9
    assert fewer_score < 0.9


def test_variance_share_gives_the_same_number_of_components_with_either_solver():
    blocks, _ = fit_pca_embedding(_X, {**_BLOCKS, "variance_share": 0.8})
    reference, _ = fit_pca_embedding(_X, {**_SKLEARN, "variance_share": 0.8})
    assert blocks.shape == reference.shape


def test_a_param_set_to_null_is_rejected_rather_than_read_as_absent():
    with pytest.raises(ValueError, match=r"\['n_components'\] are null - remove the key"):
        fit_pca_embedding(_X, {**_BLOCKS, "n_components": None, "variance_share": 0.8})


def test_varimax_scores_have_unit_variance_and_score_is_the_unrotated_variance_share():
    params = {**_BLOCKS, "rotation": "varimax", "rotation_max_iter": 500, "n_components": 4}
    embedding, score = fit_pca_embedding(_X, params)
    _, unrotated_score = fit_pca_embedding(_X, {**_BLOCKS, "n_components": 4})

    np.testing.assert_allclose(embedding.var(axis=0, ddof=1), 1.0, rtol=1e-8)
    assert score == pytest.approx(unrotated_score)


def test_resource_knobs_do_not_change_the_result():
    plain, _ = fit_pca_embedding(_X, {**_BLOCKS, "n_components": 4})
    small_chunks, _ = fit_pca_embedding(_X, {**_BLOCKS, "n_components": 4, "chunk_columns": 3, "max_matrix_gib": 1.0})
    np.testing.assert_allclose(small_chunks, plain, atol=1e-8)


def test_the_memory_ceiling_is_enforced_through_the_params():
    with pytest.raises(ValueError, match="max_matrix_gib"):
        fit_pca_embedding(_X, {**_BLOCKS, "n_components": 4, "max_matrix_gib": 1e-9})


@pytest.mark.parametrize(
    "params,message",
    [
        ({**_BLOCKS, "n_components": 3, "random_state": 0}, r"unknown param\(s\) \['random_state'\]"),
        ({"standardize": False, "dual": True, "rotation": "none", "n_components": 3}, r"requires \['solver'\]"),
        ({"solver": "blocks", "dual": True, "n_components": 3}, r"requires \['standardize', 'rotation'\]"),
        ({**_BLOCKS, "solver": "randomized", "n_components": 3}, "solver must be one of"),
        ({**_BLOCKS, "standardize": "yes", "n_components": 3}, "standardize must be true or false"),
        ({**_BLOCKS, "rotation": "bogus", "n_components": 3}, "rotation must be one of"),
        ({**_BLOCKS, "rotation": "promax", "rotation_max_iter": 500, "n_components": 3}, "rotation must be one of"),
        ({**_BLOCKS, "rotation": "varimax", "n_components": 3}, "requires 'rotation_max_iter'"),
        ({"solver": "blocks", "standardize": False, "rotation": "none", "n_components": 3}, "requires 'dual'"),
        ({**_BLOCKS, "dual": "yes", "n_components": 3}, "dual must be true or false"),
        ({**_BLOCKS}, "exactly one of n_components and variance_share"),
        ({**_BLOCKS, "n_components": 3, "variance_share": 0.9}, "exactly one of n_components and variance_share"),
        ({**_BLOCKS, "n_components": 99}, "n_components must be an integer between 1 and"),
        ({**_BLOCKS, "variance_share": 1.5}, "share must be in"),
    ],
)
def test_invalid_params_raise_a_clear_error(params, message):
    with pytest.raises(ValueError, match=message):
        fit_pca_embedding(_X, params)


@pytest.mark.parametrize(
    "extra,message",
    [
        ({"dual": True}, r"\['dual'\] only apply to solver 'blocks'"),
        ({"chunk_columns": 8}, r"\['chunk_columns'\] only apply to solver 'blocks'"),
        ({"max_matrix_gib": 2.0}, r"\['max_matrix_gib'\] only apply to solver 'blocks'"),
        ({"rotation": "varimax", "rotation_max_iter": 500}, "solver 'sklearn' does not rotate"),
    ],
)
def test_the_sklearn_solver_rejects_what_it_would_ignore(extra, message):
    with pytest.raises(ValueError, match=message):
        fit_pca_embedding(_X, {**_SKLEARN, "n_components": 3, **extra})


def test_the_sklearn_solver_runs_without_the_blocks_only_params():
    embedding, _ = fit_pca_embedding(_X, {**_SKLEARN, "n_components": 3})
    assert embedding.shape == (40, 3)


def test_standardize_rejects_a_constant_column_with_either_solver():
    X = _X.copy()
    X[:, 4] = 7.0
    for params in (_BLOCKS, _SKLEARN):
        with pytest.raises(ValueError, match="constant"):
            fit_pca_embedding(X, {**params, "standardize": True, "n_components": 3})


@pytest.mark.parametrize("solver_params", [_BLOCKS, _SKLEARN])
def test_fit_pca_reports_how_many_components_it_kept_and_the_whole_spectrum(solver_params):
    fit = fit_pca(_X, {**solver_params, "variance_share": 0.9})

    assert fit.embedding.shape == (40, fit.n_components)
    assert fit.explained_share == pytest.approx(fit.eigenvalues[: fit.n_components].sum() / fit.eigenvalues.sum())
    assert fit.explained_share >= 0.9 > fit.eigenvalues[: fit.n_components - 1].sum() / fit.eigenvalues.sum()
    assert np.all(np.diff(fit.eigenvalues) <= 0)  # descending: the curve a variance_share is read from


def test_both_solvers_report_the_same_spectrum():
    blocks = fit_pca(_X, {**_BLOCKS, "n_components": 3})
    reference = fit_pca(_X, {**_SKLEARN, "n_components": 3})
    k = min(len(blocks.eigenvalues), len(reference.eigenvalues), 11)  # past the rank both are round-off noise
    np.testing.assert_allclose(blocks.eigenvalues[:k], reference.eigenvalues[:k], rtol=1e-8)


def test_fit_pca_embedding_is_the_two_value_view_of_fit_pca():
    fit = fit_pca(_X, {**_BLOCKS, "n_components": 3})
    embedding, score = fit_pca_embedding(_X, {**_BLOCKS, "n_components": 3})
    np.testing.assert_array_equal(embedding, fit.embedding)
    assert score == fit.explained_share


def test_decomposition_spectra_is_the_spectrum_fit_pca_reports_for_each_solver():
    for solver_params, label in (
        (_BLOCKS, "solver=blocks,standardize=False,dual=True"),
        (_SKLEARN, "solver=sklearn,standardize=False"),
    ):
        cache: dict = {}
        fit = fit_pca(_X, {**solver_params, "n_components": 3}, cache)

        spectra = decomposition_spectra(cache)

        assert list(spectra) == [label]
        np.testing.assert_array_equal(spectra[label], fit.eigenvalues)


def test_decomposition_spectra_has_one_spectrum_per_decomposition_the_sweep_fitted():
    cache: dict = {}
    for standardize in (False, True):
        fit_pca(_X, {**_BLOCKS, "standardize": standardize, "n_components": 3}, cache)
    fit_pca(_X, {**_BLOCKS, "n_components": 5}, cache)  # same decomposition as the first: not a third spectrum

    spectra = decomposition_spectra(cache)

    assert sorted(spectra) == ["solver=blocks,standardize=False,dual=True", "solver=blocks,standardize=True,dual=True"]
    assert not np.allclose(*spectra.values())  # covariance and correlation give different spectra


def test_decomposition_spectra_rejects_an_empty_cache():
    with pytest.raises(ValueError, match="no pca decomposition"):
        decomposition_spectra({})


def test_decomposition_spectra_rejects_decompositions_that_differ_only_in_resource_knobs():
    cache: dict = {}
    fit_pca(_X, {**_BLOCKS, "n_components": 3, "chunk_columns": 4}, cache)
    fit_pca(_X, {**_BLOCKS, "n_components": 3, "chunk_columns": 8}, cache)

    with pytest.raises(ValueError, match="share the spectrum key"):
        decomposition_spectra(cache)
