"""Test a proprietà / parametrici di src/analysis/reduction.py: `embed` (validazione prima del calcolo) ed
`embedding_for_viz` (quando si riusa, quando si taglia, quando si rifiuta).

Le parti che adattano davvero un UMAP/t-SNE sono gia' coperte da test_reduction.py: qui si prova la logica
decisionale con metodi economici (pca) o rifiutata prima di qualunque fit.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import reduction as R
from tests.factories.matrices import binary_matrix

_FLOATS = st.floats(allow_nan=False, allow_infinity=False, min_value=-5, max_value=5, width=32)


def _embeddings(min_cols: int = 1, max_cols: int = 8):
    return st.tuples(st.integers(2, 10), st.integers(min_cols, max_cols)).flatmap(
        lambda shape: st.lists(st.lists(_FLOATS, min_size=shape[1], max_size=shape[1]), min_size=shape[0], max_size=shape[0]).map(np.array)
    )


# ---- embedding_for_viz: stesso numero di colonne ----------------------------------------------------------------------------------------------


@settings(max_examples=40)
@given(embedding=_embeddings(), method=st.text(max_size=8), params=st.dictionaries(st.text(max_size=4), st.integers(), max_size=3))
def test_an_embedding_that_already_has_the_viz_columns_is_returned_as_is_for_any_method(embedding, method, params):
    assert R.embedding_for_viz(method, np.zeros((1, 1)), params, embedding, embedding.shape[1]) is embedding


# ---- pca ordinata per varianza: lo slice e' legittimo -----------------------------------------------------------------------------------------------


_ORDERED_PARAMS = [{"rotation": "none"}, {"rotation": "varimax", "rotation_n_components": 8}, {"rotation": "none", "rotation_n_components": 3}]
_UNORDERED_PARAMS = [{"rotation": "varimax"}, {"rotation": "quartimax"}, {}]


@settings(max_examples=40)
@given(embedding=_embeddings(min_cols=2), params=st.sampled_from(_ORDERED_PARAMS), data=st.data())
def test_a_variance_ordered_pca_is_cut_to_exactly_its_leading_columns(embedding, params, data):
    view = data.draw(st.integers(1, embedding.shape[1] - 1))
    out = R.embedding_for_viz("pca", np.zeros((1, 1)), params, embedding, view)
    assert out.shape == (embedding.shape[0], view)
    assert np.array_equal(out, embedding[:, :view])


@settings(max_examples=60)
@given(embedding=_embeddings(max_cols=4), params=st.sampled_from(_ORDERED_PARAMS), extra=st.integers(1, 4))
def test_asking_a_pca_for_more_columns_than_it_has_is_a_valueerror(embedding, params, extra):
    with pytest.raises(ValueError, match="fewer than viz_n_components"):
        R.embedding_for_viz("pca", np.zeros((1, 1)), params, embedding, embedding.shape[1] + extra)


@settings(max_examples=60)
@given(embedding=_embeddings(min_cols=2), params=st.sampled_from(_UNORDERED_PARAMS), view=st.integers(1, 9))
def test_a_pca_whose_columns_have_no_order_is_never_sliced(embedding, params, view):
    if view == embedding.shape[1]:
        return
    with pytest.raises(ValueError, match="no valid viz-refit"):
        R.embedding_for_viz("pca", np.zeros((1, 1)), params, embedding, view)


@pytest.mark.parametrize("method", ["pacmap", "pca", "nope", "", "UMAP", "raw"])
@settings(max_examples=30)
@given(embedding=_embeddings(min_cols=2), view=st.integers(1, 9))
def test_a_non_refittable_method_with_a_different_dimensionality_is_a_valueerror_naming_the_refittable_ones(method, embedding, view):
    if view == embedding.shape[1]:
        return
    with pytest.raises(ValueError, match="no valid viz-refit") as excinfo:
        R.embedding_for_viz(method, np.zeros((1, 1)), {"rotation": "varimax"} if method == "pca" else {}, embedding, view)
    assert "umap" in str(excinfo.value) and "tsne" in str(excinfo.value)


def test_the_refittable_methods_are_exactly_the_neighbor_graph_ones():
    assert R._REFITTABLE_FOR_VIZ == {"umap", "tsne"}
    assert R._REFITTABLE_FOR_VIZ <= set(R.REDUCTION_METHODS)  # una voce non registrata non potrebbe mai essere rifittata


@pytest.mark.parametrize(
    "method, params, expected",
    [
        ("pca", {"rotation": "none"}, True),
        ("pca", {"rotation": "none", "rotation_n_components": 5}, True),
        ("pca", {"rotation": "varimax", "rotation_n_components": 5}, True),
        ("pca", {"rotation": "varimax"}, False),
        ("pca", {}, False),
        ("umap", {"rotation": "none"}, False),
        ("tsne", {"rotation_n_components": 5}, False),
        ("pacmap", {"rotation": "none"}, False),
        ("PCA", {"rotation": "none"}, False),
    ],
)
def test_columns_ordered_by_variance_truth_table(method, params, expected):
    assert R._columns_ordered_by_variance(method, params) is expected


# ---- embed: validazione prima di qualunque fit -----------------------------------------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    metric=st.sampled_from(sorted(R.SUPPORTED_BINARY_METRICS)),
    bad=st.sampled_from([2, -1, 0.5, 0.999, 1.0001, float("nan"), float("inf"), -float("inf"), 255]),
    row=st.integers(0, 11),
    col=st.integers(0, 39),
    precompute=st.booleans(),
)
def test_a_jaccard_or_dice_embedding_of_a_non_binary_matrix_is_a_valueerror_in_both_modes(metric, bad, row, col, precompute):
    X = binary_matrix().astype(float)
    X[row, col] = bad
    with pytest.raises(ValueError, match="strictly binary"):
        R.embed("pca", X, {"metric": metric}, precompute_distance_metric=precompute)


@pytest.mark.parametrize("metric", sorted(R.SUPPORTED_BINARY_METRICS))
def test_an_all_zero_row_makes_jaccard_and_dice_undefined_and_is_a_valueerror_when_precomputing(metric):
    X = binary_matrix()
    X[3] = 0
    with pytest.raises(ValueError, match="all-zero|undefined"):
        R.embed("pca", X, {"metric": metric}, precompute_distance_metric=True)


@pytest.mark.parametrize("metric", sorted(R.PRECOMPUTABLE_METRICS))
def test_the_distance_cache_is_filled_once_per_metric_and_reused_by_identity(metric):
    X = binary_matrix()
    cache: dict = {}
    with pytest.raises(ValueError):  # pca non accetta "precomputed": ci interessa solo che la cache si sia riempita prima
        R.embed("pca", X, {"metric": metric}, cache)
    assert set(cache) == {metric} and cache[metric].shape == (len(X), len(X))
    matrix = cache[metric]
    with pytest.raises(ValueError):
        R.embed("pca", X, {"metric": metric}, cache)
    assert cache[metric] is matrix  # riusata, non ricalcolata


@pytest.mark.parametrize("metric", sorted(R.PRECOMPUTABLE_METRICS))
def test_without_precompute_the_cache_is_left_untouched(metric):
    cache: dict = {}
    X = binary_matrix()
    with pytest.raises(ValueError):
        R.embed("pca", X, {"metric": metric}, cache, precompute_distance_metric=False)
    assert cache == {}


@settings(max_examples=40)
@given(params=st.dictionaries(st.sampled_from(["a", "b"]), st.integers(), max_size=2))
def test_embed_never_mutates_the_params_it_is_given(params):
    X = binary_matrix()
    snapshot = dict(params)
    try:
        R.embed("pca", X, {**params, "metric": "dice"})
    except ValueError:
        pass
    assert params == snapshot


# ---- bug sospetti ---------------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("method", ["foo", "", "UMAP", "raw"])
def test_embed_with_an_unregistered_method_is_a_valueerror(method):
    with pytest.raises(ValueError):
        R.embed(method, binary_matrix(), {})


@pytest.mark.parametrize("view", [0, -1, -3])
def test_a_non_positive_viz_n_components_is_a_valueerror(view):
    embedding = np.arange(20.0).reshape(5, 4)
    with pytest.raises(ValueError):
        R.embedding_for_viz("pca", np.zeros((1, 1)), {"rotation": "none"}, embedding, view)
