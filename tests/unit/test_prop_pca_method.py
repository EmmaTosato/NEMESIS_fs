"""Property tests for src/analysis/pca_method.py (il metodo `pca` del registro dei parametri).

Su matrici casuali: i due solver (blocks, sklearn) danno lo stesso spettro, la stessa quota di
varianza e le stesse norme dei punteggi; `explained_share` è la quota cumulata dei componenti tenuti;
`variance_share` tiene il numero minimo di componenti che la raggiunge; la `model_cache` condivide
una sola decomposizione fra n_components/rotazioni diverse e ne tiene una per ogni scelta che la
cambia davvero. Complementa tests/unit/test_pca_method.py senza ripeterlo.
"""

import itertools

import numpy as np
import pytest
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra.numpy import arrays

from src.analysis.pca_method import SOLVERS, decomposition_spectra, fit_pca, fit_pca_embedding

_floats = st.floats(-10.0, 10.0, allow_nan=False, allow_infinity=False)
matrices = st.tuples(st.integers(4, 12), st.integers(2, 8)).flatmap(lambda shape: arrays(np.float64, shape, elements=_floats))

_BLOCKS = {"solver": "blocks", "standardize": False, "rotation": "none", "dual": True}
_SKLEARN = {"solver": "sklearn", "standardize": False, "rotation": "none"}
_SOLVER_PARAMS = {"blocks-dual": _BLOCKS, "blocks-covariance": {**_BLOCKS, "dual": False}, "sklearn": _SKLEARN}


def _varying(X: np.ndarray) -> bool:
    return bool((X.std(axis=0, ddof=1) > 1e-3).all())


def _rank(X: np.ndarray) -> int:
    """Componenti con varianza, con la stessa nozione del codice (autovalore > 1e-10 del massimo) ma senza zona grigia:
    una matrice con autovalori fra 1e-14 e 1e-6 del massimo viene scartata, il test non può dire chi ha ragione."""
    squared = np.linalg.svd(X - X.mean(axis=0), compute_uv=False) ** 2
    if squared.max() < 1e-12:  # matrice costante a meno dell'arrotondamento della media: nessuna componente reale
        return 0
    ratio = squared / squared.max()
    assume(not ((ratio > 1e-14) & (ratio < 1e-6)).any())
    return int((ratio >= 1e-6).sum())


# --- spettro e quota spiegata --------------------------------------------------------------------------------


@pytest.mark.parametrize("standardize", [False, True])
@given(X=matrices)
@settings(max_examples=30)
def test_the_three_ways_to_fit_report_one_spectrum_and_one_explained_share(standardize, X):
    assume(_varying(X) or not standardize)
    k = _rank(X)
    assume(k >= 2)
    fits = {name: fit_pca(X, {**params, "standardize": standardize, "n_components": k - 1}) for name, params in _SOLVER_PARAMS.items()}

    reference = fits["sklearn"]
    scale = max(reference.eigenvalues.max(), 1e-12)
    for name, fit in fits.items():
        size = min(len(fit.eigenvalues), len(reference.eigenvalues))
        np.testing.assert_allclose(fit.eigenvalues[:size], reference.eigenvalues[:size], atol=1e-8 * scale, err_msg=name)
        assert fit.explained_share == pytest.approx(reference.explained_share, abs=1e-8), name
        assert fit.embedding.shape == (len(X), k - 1) and fit.n_components == k - 1
        np.testing.assert_allclose(
            np.linalg.norm(fit.embedding, axis=0), np.linalg.norm(reference.embedding, axis=0), atol=1e-6 * max(1.0, scale), err_msg=name
        )


@pytest.mark.parametrize("name", list(_SOLVER_PARAMS))
@given(X=matrices)
@settings(max_examples=30)
def test_explained_share_is_the_cumulative_share_of_the_kept_components_and_grows_with_their_number(name, X):
    k = _rank(X)
    assume(k >= 1)
    cache: dict = {}

    fits = [fit_pca(X, {**_SOLVER_PARAMS[name], "n_components": n}, cache) for n in range(1, k + 1)]

    shares = [fit.explained_share for fit in fits]
    eigenvalues = fits[0].eigenvalues
    assert shares == pytest.approx(list(np.cumsum(eigenvalues / eigenvalues.sum())[:k]), abs=1e-9)
    assert all(a < b + 1e-12 for a, b in zip(shares, shares[1:]))
    assert 0 < shares[0] <= shares[-1] <= 1 + 1e-9
    assert shares[-1] == pytest.approx(1.0, abs=1e-9)  # tutti i componenti con varianza: tutta la varianza
    assert len(cache) == 1  # una sola decomposizione per tutti gli n_components


@pytest.mark.parametrize("name", list(_SOLVER_PARAMS))
@given(X=matrices, share=st.floats(0.05, 1.0))
@settings(max_examples=30)
def test_variance_share_keeps_the_minimum_components_that_reach_it(name, X, share):
    assume(_rank(X) >= 1)

    fit = fit_pca(X, {**_SOLVER_PARAMS[name], "variance_share": share})

    cumulative = np.cumsum(fit.eigenvalues / fit.eigenvalues.sum())
    assert fit.n_components >= 1 and fit.embedding.shape == (len(X), fit.n_components)
    assert cumulative[fit.n_components - 1] >= share - 1e-9
    assert fit.n_components == 1 or cumulative[fit.n_components - 2] < share + 1e-9
    assert fit.explained_share == pytest.approx(cumulative[fit.n_components - 1], abs=1e-9)


@given(X=matrices)
@settings(max_examples=20)
def test_fit_pca_embedding_is_the_two_value_view_of_fit_pca(X):
    assume(_rank(X) >= 1)
    params = {**_BLOCKS, "n_components": 1}

    embedding, share = fit_pca_embedding(X, params)
    fit = fit_pca(X, params)

    np.testing.assert_array_equal(embedding, fit.embedding)
    assert share == fit.explained_share


@given(X=matrices, offset=st.sampled_from([0.0, 1000.0]))
@settings(max_examples=20)
def test_a_large_common_offset_changes_neither_the_share_nor_the_component_count(X, offset):
    assume(_rank(X) >= 2)
    params = {**_BLOCKS, "variance_share": 0.8}

    plain, shifted = fit_pca(X, params), fit_pca(X + offset, params)

    assert shifted.n_components == plain.n_components
    assert shifted.explained_share == pytest.approx(plain.explained_share, abs=1e-6)


# --- rotazione con rotation_n_components ---------------------------------------------------------------------


@given(seed=st.integers(0, 40), kept=st.integers(1, 4))
@settings(max_examples=10)
def test_rotating_more_components_than_kept_returns_the_rotated_ones_that_explain_most_variance(seed, kept):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(30, 4)) @ rng.normal(size=(4, 20)) + 0.1 * rng.normal(size=(30, 20))
    params = {**_BLOCKS, "rotation": "varimax", "rotation_max_iter": 500, "rotation_n_components": 4, "n_components": kept}

    fit = fit_pca(X, params)

    assert fit.embedding.shape == (30, kept) and fit.n_components == kept
    assert 0 < fit.explained_share <= fit_pca(X, {**_BLOCKS, "n_components": 4}).explained_share + 1e-9
    np.testing.assert_allclose(fit.embedding.var(axis=0, ddof=1), 1.0, rtol=1e-6)


# --- model_cache ---------------------------------------------------------------------------------------------


@given(X=matrices)
@settings(max_examples=20)
def test_the_cache_holds_one_decomposition_per_choice_that_changes_it_and_gives_the_same_answers_as_a_fresh_fit(X):
    assume(_varying(X) and _rank(X) >= 2)
    cache: dict = {}
    combos = list(itertools.product([False, True], ["blocks-dual", "blocks-covariance", "sklearn"]))

    for standardize, name in combos:
        params = {**_SOLVER_PARAMS[name], "standardize": standardize, "n_components": 1}
        cached = fit_pca(X, params, cache)
        np.testing.assert_allclose(cached.embedding, fit_pca(X, params).embedding, atol=1e-9)
        fit_pca(X, {**params, "n_components": 2}, cache)  # un altro n_components non aggiunge entrate

    assert len(cache) == len(combos)
    spectra = decomposition_spectra(cache)
    assert len(spectra) == len(combos)
    assert all(np.all(np.diff(values) <= 1e-9) for values in spectra.values())


def test_without_a_cache_each_call_is_independent_and_a_given_empty_cache_is_filled():
    X = np.random.default_rng(0).normal(size=(10, 5))
    cache: dict = {}

    fit_pca(X, {**_BLOCKS, "n_components": 2})
    assert cache == {}
    fit_pca(X, {**_BLOCKS, "n_components": 2}, cache)
    assert len(cache) == 1


def test_resource_knobs_are_part_of_the_cache_key_and_not_of_the_result():
    X = np.random.default_rng(1).normal(size=(10, 6))
    cache: dict = {}

    first = fit_pca(X, {**_BLOCKS, "n_components": 2, "chunk_columns": 2}, cache)
    second = fit_pca(X, {**_BLOCKS, "n_components": 2, "chunk_columns": 4}, cache)

    assert len(cache) == 2
    np.testing.assert_allclose(first.eigenvalues, second.eigenvalues, atol=1e-10)
    np.testing.assert_allclose(np.abs(first.embedding), np.abs(second.embedding), atol=1e-8)


# --- validazione dei parametri -------------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["solver", "standardize", "rotation", "dual", "n_components", "variance_share", "chunk_columns", "max_matrix_gib"])
def test_a_null_value_is_rejected_for_every_param_rather_than_read_as_absent(key):
    params = {**_BLOCKS, "n_components": 2, key: None}

    with pytest.raises(ValueError, match="null"):
        fit_pca(np.eye(5), params)


@pytest.mark.parametrize("key", ["solver", "standardize", "rotation"])
def test_every_always_required_param_is_named_when_missing(key):
    params = {k: v for k, v in {**_BLOCKS, "n_components": 2}.items() if k != key}

    with pytest.raises(ValueError, match="requires"):
        fit_pca(np.eye(5), params)


@given(extra=st.text(alphabet="abcdefgh_", min_size=1, max_size=10).filter(lambda k: k not in _BLOCKS and k not in {"n_components", "variance_share", "chunk_columns", "max_matrix_gib", "rotation_max_iter", "rotation_n_components"}))
def test_an_unknown_param_is_rejected_by_name(extra):
    with pytest.raises(ValueError, match="unknown param"):
        fit_pca(np.eye(5), {**_BLOCKS, "n_components": 1, extra: 1})


@pytest.mark.parametrize("solver", ["", "BLOCKS", "svd", "randomized"])
def test_only_the_registered_solvers_are_accepted(solver):
    assert set(SOLVERS) == {"blocks", "sklearn"}
    with pytest.raises(ValueError, match="solver must be one of"):
        fit_pca(np.eye(5), {**_BLOCKS, "solver": solver, "n_components": 1})


@pytest.mark.parametrize("params", [{}, {"n_components": 1, "variance_share": 0.5}])
@pytest.mark.parametrize("solver", list(_SOLVER_PARAMS))
def test_exactly_one_of_n_components_and_variance_share_is_required_with_every_solver(solver, params):
    with pytest.raises(ValueError, match="exactly one"):
        fit_pca(np.random.default_rng(0).normal(size=(8, 4)), {**_SOLVER_PARAMS[solver], **params})


@pytest.mark.parametrize("bad", [0, 5, 2.0, True, "2", -1])
@pytest.mark.parametrize("solver", list(_SOLVER_PARAMS))
def test_an_unusable_n_components_is_rejected_with_every_solver(solver, bad):
    X = np.random.default_rng(0).normal(size=(8, 4))  # 4 componenti con varianza al massimo
    with pytest.raises(ValueError, match="n_components must be"):
        fit_pca(X, {**_SOLVER_PARAMS[solver], "n_components": bad})


@pytest.mark.parametrize("bad", [0.0, -0.2, 1.01, float("nan")])
@pytest.mark.parametrize("solver", list(_SOLVER_PARAMS))
def test_a_variance_share_outside_zero_one_is_rejected_with_every_solver(solver, bad):
    with pytest.raises(ValueError, match="share must be in"):
        fit_pca(np.random.default_rng(0).normal(size=(8, 4)), {**_SOLVER_PARAMS[solver], "variance_share": bad})


@pytest.mark.parametrize("bad", ["yes", 1, 0, None])
def test_standardize_and_dual_must_be_real_booleans(bad):
    for key in ("standardize", "dual"):
        with pytest.raises(ValueError):
            fit_pca(np.eye(5), {**_BLOCKS, "n_components": 1, key: bad})


@pytest.mark.parametrize("rotation", ["varimax", "quartimax"])
def test_a_rotation_without_its_iteration_cap_is_rejected_and_none_needs_no_cap(rotation):
    X = np.random.default_rng(0).normal(size=(10, 5))

    with pytest.raises(ValueError, match="rotation_max_iter"):
        fit_pca(X, {**_BLOCKS, "rotation": rotation, "n_components": 2})
    assert fit_pca(X, {**_BLOCKS, "n_components": 2}).embedding.shape == (10, 2)


@pytest.mark.parametrize("extra", ["dual", "chunk_columns", "max_matrix_gib"])
def test_the_sklearn_solver_rejects_every_blocks_only_param(extra):
    value = {"dual": True, "chunk_columns": 4, "max_matrix_gib": 1.0}[extra]

    with pytest.raises(ValueError, match="only apply to solver 'blocks'"):
        fit_pca(np.eye(5), {**_SKLEARN, "n_components": 1, extra: value})


def test_the_blocks_solver_requires_dual():
    with pytest.raises(ValueError, match="requires 'dual'"):
        fit_pca(np.eye(5), {"solver": "blocks", "standardize": False, "rotation": "none", "n_components": 1})


# --- decomposition_spectra -----------------------------------------------------------------------------------


@pytest.mark.parametrize("entry", [("bogus", 1), ("pca",), ("randomized", False)])
def test_a_cache_entry_that_is_not_a_pca_decomposition_is_named_in_the_error(entry):
    with pytest.raises(ValueError, match="not a pca decomposition"):
        decomposition_spectra({entry: object()})


# --- casi limite ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("solver", list(_SOLVER_PARAMS))
def test_every_solver_rejects_a_variance_share_on_a_matrix_without_variance(solver):
    with pytest.raises(ValueError, match="no variance"):
        fit_pca(np.full((6, 3), 2.0), {**_SOLVER_PARAMS[solver], "variance_share": 0.5})


@pytest.mark.parametrize("name", list(_SOLVER_PARAMS))
def test_a_single_column_matrix_has_one_component_that_explains_everything(name):
    X = np.random.default_rng(0).normal(size=(7, 1))

    fit = fit_pca(X, {**_SOLVER_PARAMS[name], "n_components": 1})

    assert fit.embedding.shape == (7, 1) and fit.explained_share == pytest.approx(1.0)
    np.testing.assert_allclose(np.abs(fit.embedding[:, 0]), np.abs(X[:, 0] - X.mean()), atol=1e-9)
