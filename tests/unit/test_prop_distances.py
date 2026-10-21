"""Property tests for src/analysis/distances.py.

Le proprietà che una distanza deve avere per costruzione (simmetria, diagonale nulla, intervallo,
equivarianza alle permutazioni), l'accordo con scipy/sklearn sullo stesso input, e i casi limite
(riga di soli zeri, matrici 1x1, offset comune grande, dtype stretti) che devono sollevare l'errore
documentato o dare un numero finito corretto. Complementa tests/unit/test_distances.py (valori
calcolati a mano) senza ripeterlo.
"""

from unittest import mock

import numpy as np
import pytest
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra.numpy import arrays
from scipy.spatial.distance import cdist
from sklearn.metrics.pairwise import euclidean_distances

from src.analysis import distances
from src.analysis.distances import (
    PRECOMPUTABLE_METRICS,
    binary_pairwise_distance,
    euclidean_pairwise_distance,
    pairwise_distance,
    precomputed_distance,
)

_BINARY_METRICS = ["jaccard", "dice"]
_ALL_METRICS = ["jaccard", "dice", "euclidean"]
_TOL = 1e-9


# --- strategie ----------------------------------------------------------------------------------------------


def _without_empty_rows(X: np.ndarray) -> np.ndarray:
    X = X.copy()
    X[~(X != 0).any(axis=1), 0] = 1
    return X


_shapes = st.tuples(st.integers(1, 12), st.integers(1, 20))

binary_matrices = _shapes.flatmap(lambda s: arrays(np.uint8, s, elements=st.integers(0, 1))).map(_without_empty_rows)

# non negativi, con molti zeri esatti (le matrici reali sono sparse) e nessuna riga vuota
continuous_matrices = _shapes.flatmap(
    lambda s: arrays(np.float64, s, elements=st.one_of(st.just(0.0), st.floats(0.01, 50.0, allow_nan=False)))
).map(_without_empty_rows)

real_matrices = _shapes.flatmap(lambda s: arrays(np.float64, s, elements=st.floats(-20.0, 20.0, allow_nan=False, allow_infinity=False)))


def _reference_weighted(X: np.ndarray, metric: str) -> np.ndarray:
    """Dice (Czekanowski) / Jaccard (Ruzicka) pesati, da definizione: sum_min esplicito, nessuna scorciatoia."""
    X = np.asarray(X, dtype=np.float64)
    sum_min = np.minimum(X[:, None, :], X[None, :, :]).sum(axis=2)
    total = X.sum(axis=1)[:, None] + X.sum(axis=1)[None, :]
    if metric == "dice":
        return 1 - 2 * sum_min / total
    return 1 - sum_min / (total - sum_min)


def _assert_valid_distance_matrix(D: np.ndarray, n: int) -> None:
    assert D.shape == (n, n)
    assert np.isfinite(D).all()
    np.testing.assert_array_equal(np.diag(D), 0.0)
    np.testing.assert_allclose(D, D.T, atol=_TOL)
    assert (D >= -_TOL).all()


# --- binary_pairwise_distance --------------------------------------------------------------------------------


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=binary_matrices)
def test_binary_distance_is_a_symmetric_zero_diagonal_matrix_in_unit_range(metric, X):
    D = binary_pairwise_distance(X, metric)

    _assert_valid_distance_matrix(D, len(X))
    assert (D <= 1 + _TOL).all()


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=binary_matrices)
def test_binary_distance_agrees_with_scipy(metric, X):
    expected = cdist(X.astype(bool), X.astype(bool), metric)

    np.testing.assert_allclose(binary_pairwise_distance(X, metric), expected, atol=_TOL)


@given(X=binary_matrices)
def test_dice_is_a_fixed_function_of_jaccard(X):
    """d_dice = d_jac / (2 - d_jac): lega le due formule indipendenti, quindi un errore in una sola si vede."""
    jaccard = binary_pairwise_distance(X, "jaccard")
    dice = binary_pairwise_distance(X, "dice")

    np.testing.assert_allclose(dice, jaccard / (2 - jaccard), atol=_TOL)
    assert (dice <= jaccard + _TOL).all()


@given(X=binary_matrices, data=st.data())
def test_jaccard_satisfies_the_triangle_inequality(X, data):
    """Jaccard è una vera metrica (Dice no): d(i,k) <= d(i,j) + d(j,k) per ogni terna."""
    D = binary_pairwise_distance(X, "jaccard")
    n = len(X)
    i, j, k = (data.draw(st.integers(0, n - 1)) for _ in range(3))

    assert D[i, k] <= D[i, j] + D[j, k] + _TOL


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=binary_matrices, data=st.data())
def test_a_duplicated_row_is_at_distance_zero_from_its_twin_and_equidistant_from_the_rest(metric, X, data):
    i = data.draw(st.integers(0, len(X) - 1))
    extended = np.vstack([X, X[i]])

    D = binary_pairwise_distance(extended, metric)

    assert D[i, -1] == 0.0
    np.testing.assert_allclose(D[-1, :-1], D[i, :-1], atol=_TOL)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(mask=arrays(np.bool_, 8, elements=st.booleans()))
def test_disjoint_nonempty_rows_are_at_distance_one(metric, mask):
    assume(mask.any() and not mask.all())
    X = np.vstack([mask, ~mask]).astype(np.uint8)

    assert binary_pairwise_distance(X, metric)[0, 1] == pytest.approx(1.0)
    assert pairwise_distance(X, metric)[0, 1] == pytest.approx(1.0)


@pytest.mark.parametrize("metric", _ALL_METRICS)
@given(X=binary_matrices, data=st.data())
def test_precomputed_distance_is_equivariant_to_a_row_permutation(metric, X, data):
    permutation = data.draw(st.permutations(range(len(X))))
    permutation = np.asarray(permutation)

    D = precomputed_distance(X, metric)
    D_permuted = precomputed_distance(X[permutation], metric)

    np.testing.assert_allclose(D_permuted, D[np.ix_(permutation, permutation)], atol=_TOL)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=binary_matrices, bad=st.sampled_from([2, 7, 255]), data=st.data())
def test_binary_distance_rejects_a_value_outside_zero_one(metric, X, bad, data):
    X = X.copy()
    X[data.draw(st.integers(0, X.shape[0] - 1)), data.draw(st.integers(0, X.shape[1] - 1))] = bad

    with pytest.raises(ValueError, match="strictly binary"):
        binary_pairwise_distance(X, metric)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=binary_matrices, data=st.data())
def test_an_all_zero_row_raises_in_both_functions_instead_of_giving_nan(metric, X, data):
    position = data.draw(st.integers(0, len(X)))
    with_empty = np.insert(X, position, 0, axis=0)

    with pytest.raises(ValueError, match="all-zero row|at least one nonzero"):
        binary_pairwise_distance(with_empty, metric)
    with pytest.raises(ValueError, match="all-zero row"):
        pairwise_distance(with_empty, metric)


def test_binary_distance_does_not_wrap_around_on_a_narrow_dtype():
    """lessons_learned #13: intersezioni oltre 255 con uint8 non devono andare in overflow."""
    X = np.ones((3, 600), dtype=np.uint8)
    X[2, 300:] = 0

    for metric in _BINARY_METRICS:
        assert binary_pairwise_distance(X, metric)[0, 1] == 0.0
        assert 0.0 < binary_pairwise_distance(X, metric)[0, 2] < 1.0
        np.testing.assert_allclose(pairwise_distance(X, metric), binary_pairwise_distance(X, metric), atol=_TOL)


# --- euclidean -----------------------------------------------------------------------------------------------


@given(X=real_matrices)
def test_euclidean_distance_properties_and_agreement_with_scipy(X):
    D = euclidean_pairwise_distance(X)

    _assert_valid_distance_matrix(D, len(X))
    # forma espansa: due righe uguali non escono a 0 ma a ~sqrt(eps)*||x|| (qui <= 1e-4), non è un errore di formula
    np.testing.assert_allclose(D, cdist(X, X), atol=1e-4)


@pytest.mark.parametrize("function", [euclidean_pairwise_distance, lambda X: pairwise_distance(X, "euclidean")], ids=["euclidean_pairwise", "pairwise_distance"])
@given(X=real_matrices)
def test_euclidean_matches_scipy_with_a_large_common_offset(function, X):
    """lessons_learned #42: ||x||^2 + ||y||^2 - 2<x,y> è una differenza di numeri grandi se X ha un
    grosso offset comune. A 1000 l'errore deve restare trascurabile e la diagonale esattamente 0."""
    shifted = X + 1000.0  # la forma espansa perde ~sqrt(eps)*||x|| ~ 6e-5 su righe quasi uguali: soglia 1e-3

    D = function(shifted)

    np.testing.assert_array_equal(np.diag(D), 0.0)
    assert np.isfinite(D).all() and (D >= 0).all()
    np.testing.assert_allclose(D, cdist(X, X), atol=1e-3)


@given(X=real_matrices, scale=st.floats(0.1, 100.0))
def test_euclidean_is_homogeneous_of_degree_one(X, scale):
    np.testing.assert_allclose(
        pairwise_distance(X * scale, "euclidean"), scale * pairwise_distance(X, "euclidean"), rtol=1e-6, atol=1e-4
    )


@given(X=real_matrices)
def test_euclidean_agrees_with_sklearn_and_between_the_two_implementations(X):
    np.testing.assert_allclose(euclidean_pairwise_distance(X), euclidean_distances(X), atol=1e-9)
    np.testing.assert_allclose(pairwise_distance(X, "euclidean"), euclidean_pairwise_distance(X), atol=1e-4)


@given(X=real_matrices, data=st.data())
def test_euclidean_accepts_an_all_zero_row(X, data):
    with_empty = np.insert(X, data.draw(st.integers(0, len(X))), 0.0, axis=0)

    D = pairwise_distance(with_empty, "euclidean")

    assert np.isfinite(D).all()
    np.testing.assert_allclose(D, cdist(with_empty, with_empty), atol=1e-4)


# --- pairwise_distance: binario e continuo ------------------------------------------------------------------


@pytest.mark.parametrize("dtype", [np.uint8, np.float32, np.float64])
@pytest.mark.parametrize("metric", _ALL_METRICS)
@given(X=binary_matrices)
def test_pairwise_distance_on_binary_equals_the_binary_and_euclidean_functions_for_any_dtype(metric, dtype, X):
    X = X.astype(dtype)

    np.testing.assert_allclose(pairwise_distance(X, metric), precomputed_distance(X, metric), atol=1e-6)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=continuous_matrices)
def test_continuous_dice_and_jaccard_match_the_definition_with_explicit_minimum(metric, X):
    D = pairwise_distance(X, metric, n_jobs=1)

    _assert_valid_distance_matrix(D, len(X))
    assert (D <= 1 + _TOL).all()
    np.testing.assert_allclose(D, _reference_weighted(X, metric), atol=1e-9)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=continuous_matrices, scale=st.floats(0.01, 1000.0))
def test_continuous_dice_and_jaccard_do_not_depend_on_the_scale_of_the_values(metric, X, scale):
    """sum_min e le somme di riga scalano entrambe con c: il rapporto no. Un errore di denominatore lo rompe."""
    np.testing.assert_allclose(pairwise_distance(X * scale, metric, n_jobs=1), pairwise_distance(X, metric, n_jobs=1), atol=1e-8)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=continuous_matrices, data=st.data())
def test_continuous_distance_is_equivariant_to_row_permutation_and_to_column_permutation(metric, X, data):
    rows = np.asarray(data.draw(st.permutations(range(X.shape[0]))))
    columns = np.asarray(data.draw(st.permutations(range(X.shape[1]))))

    D = pairwise_distance(X, metric, n_jobs=1)

    np.testing.assert_allclose(pairwise_distance(X[rows], metric, n_jobs=1), D[np.ix_(rows, rows)], atol=1e-9)
    np.testing.assert_allclose(pairwise_distance(X[:, columns], metric, n_jobs=1), D, atol=1e-9)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=continuous_matrices)
def test_continuous_dice_is_a_fixed_function_of_continuous_jaccard(metric, X):
    """Czekanowski e Ruzicka stanno nella stessa relazione di Dice e Jaccard binari."""
    jaccard = pairwise_distance(X, "jaccard", n_jobs=1)
    dice = pairwise_distance(X, "dice", n_jobs=1)

    np.testing.assert_allclose(dice, jaccard / (2 - jaccard), atol=1e-8)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=arrays(np.uint8, st.tuples(st.integers(2, 8), st.integers(1, 12)), elements=st.integers(0, 255)))
def test_narrow_integer_counts_are_not_wrapped_modulo_256(metric, X):
    """Una matrice uint8 di conteggi (non binaria): somme di riga e minimi vanno accumulati in float64."""
    X = _without_empty_rows(X)

    np.testing.assert_allclose(pairwise_distance(X, metric, n_jobs=1), _reference_weighted(X, metric), atol=1e-9)


@pytest.mark.parametrize("metric", _ALL_METRICS)
@pytest.mark.parametrize("chunk", [1, 2, 5])
@given(binary=binary_matrices, continuous=continuous_matrices)
@settings(max_examples=25)
def test_the_column_block_size_never_changes_the_result(metric, chunk, binary, continuous):
    for X in (binary, continuous):
        single_block = pairwise_distance(X, metric, n_jobs=1)
        with mock.patch.object(distances, "_GRAM_CHUNK", chunk), mock.patch.object(distances, "_L1_ROW_BLOCK", 2):
            np.testing.assert_allclose(pairwise_distance(X, metric, n_jobs=1), single_block, atol=1e-6)


@given(X=continuous_matrices)
@settings(max_examples=15)
def test_the_number_of_threads_never_changes_the_result(X):
    np.testing.assert_allclose(pairwise_distance(X, "jaccard", n_jobs=1), pairwise_distance(X, "jaccard", n_jobs=2), atol=1e-12)


@pytest.mark.parametrize("metric", _BINARY_METRICS)
@given(X=continuous_matrices, data=st.data())
def test_a_negative_value_on_a_continuous_matrix_raises_for_dice_and_jaccard(metric, X, data):
    X = X + 1.0  # righe a somma positiva: l'unico difetto è il valore negativo, non una riga vuota
    X[data.draw(st.integers(0, X.shape[0] - 1)), data.draw(st.integers(0, X.shape[1] - 1))] = -0.5

    with pytest.raises(ValueError, match="non-negative"):
        pairwise_distance(X, metric)


@pytest.mark.parametrize("shape", [(1, 1), (1, 7), (6, 1), (2, 1)])
@pytest.mark.parametrize("metric", _ALL_METRICS)
def test_degenerate_shapes_give_finite_zero_diagonal_matrices(metric, shape):
    """1 riga, 1 colonna: nessuna divisione per zero, nessun NaN."""
    X = np.ones(shape)

    D = pairwise_distance(X, metric)

    _assert_valid_distance_matrix(D, shape[0])
    np.testing.assert_allclose(D, 0.0, atol=_TOL)  # tutte le righe identiche


@pytest.mark.parametrize("metric", _ALL_METRICS)
def test_constant_columns_do_not_break_any_metric(metric):
    X = np.column_stack([np.ones(5), np.full(5, 3.0), np.arange(1.0, 6.0)])

    D = pairwise_distance(X, metric)

    _assert_valid_distance_matrix(D, 5)
    if metric != "euclidean":
        np.testing.assert_allclose(D, _reference_weighted(X, metric), atol=_TOL)


@pytest.mark.parametrize("function", [binary_pairwise_distance, pairwise_distance, precomputed_distance])
@pytest.mark.parametrize("metric", ["cosine", "", "Jaccard", "manhattan"])
def test_every_entry_point_rejects_an_unknown_metric_name(function, metric):
    with pytest.raises(ValueError, match="unsupported metric"):
        function(np.ones((3, 3)), metric)


def test_precomputable_metrics_cover_exactly_what_precomputed_distance_dispatches():
    X = np.eye(3)
    for metric in PRECOMPUTABLE_METRICS:
        assert precomputed_distance(X, metric).shape == (3, 3)


@pytest.mark.parametrize("metric", _ALL_METRICS)
@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_a_matrix_with_nan_or_inf_is_rejected_not_turned_into_nan_distances(metric, bad):
    X = np.array([[1.0, bad], [1.0, 2.0]])

    with pytest.raises(ValueError, match=f"metric={metric!r} needs finite values"):
        pairwise_distance(X, metric)
