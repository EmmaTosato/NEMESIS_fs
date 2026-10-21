"""Property tests for src/analysis/pca_evaluation.py.

Le funzioni pure di calcolo (quote di varianza dei componenti ruotati, scelta dei due componenti da
disegnare, lettura delle covariate dal registro, chiave di una combinazione di tuning), su input
casuali. `load_participants_registry` è l'unico I/O esterno e viene sostituito; il resto gira vero.
Complementa tests/unit/test_pca_evaluation.py (letture di run su disco) senza ripeterlo.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra.numpy import arrays

from src.analysis import pca_evaluation
from src.analysis.covariance_pca import fit_covariance_pca, pca_scores, rotated_scores
from src.analysis.pca_evaluation import (
    _combination_key,
    default_embedding_components,
    registry_side_indicator,
    registry_values,
    rotated_variance_shares,
)


def _structured(seed: int, n=30, p=24, k=3, offset=0.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    loadings = np.zeros((k, p))
    for i in range(k):
        loadings[i, i * (p // k) : (i + 1) * (p // k)] = rng.uniform(1, 2, size=p // k)
    return rng.normal(size=(n, k)) @ loadings + 0.2 * rng.normal(size=(n, p)) + offset


# --- rotated_variance_shares ---------------------------------------------------------------------------------


@pytest.mark.parametrize("standardize", [False, True])
@given(seed=st.integers(0, 60), k=st.integers(2, 4))
@settings(max_examples=12)
def test_the_rotated_shares_add_up_to_the_variance_share_of_the_components_that_were_rotated(standardize, seed, k):
    """Una rotazione ortogonale ridistribuisce la varianza fra i componenti, non ne crea né ne perde."""
    X = _structured(seed, k=3)
    pca = fit_covariance_pca(X, standardize=standardize)
    scores, loadings = rotated_scores(X, pca, k, "varimax", 500)

    shares = rotated_variance_shares(X, scores, pca.eigenvalues, standardize=standardize)

    assert shares.shape == (k,) and (shares >= 0).all()
    assert shares.sum() == pytest.approx(pca.explained_variance_ratio[:k].sum(), rel=1e-6)
    np.testing.assert_allclose(shares, (loadings**2).sum(axis=0) / pca.eigenvalues.sum(), rtol=1e-6)


@given(seed=st.integers(0, 60), data=st.data())
@settings(max_examples=12)
def test_the_shares_follow_the_components_when_the_scores_columns_are_reordered(seed, data):
    X = _structured(seed)
    pca = fit_covariance_pca(X)
    scores, _ = rotated_scores(X, pca, 3, "varimax", 500)
    order = np.asarray(data.draw(st.permutations(range(3))))

    shares = rotated_variance_shares(X, scores, pca.eigenvalues)

    np.testing.assert_allclose(rotated_variance_shares(X, scores[:, order], pca.eigenvalues), shares[order], atol=1e-12)
    flipped = scores * np.array([-1.0, 1.0, -1.0])  # il segno di un componente è arbitrario
    np.testing.assert_allclose(rotated_variance_shares(X, flipped, pca.eigenvalues), shares, atol=1e-12)


@given(seed=st.integers(0, 60), data=st.data(), chunk=st.integers(1, 9))
@settings(max_examples=12)
def test_the_shares_do_not_depend_on_subject_order_chunking_or_the_unit_of_the_data(seed, data, chunk):
    X = _structured(seed)
    pca = fit_covariance_pca(X)
    scores, _ = rotated_scores(X, pca, 3, "varimax", 500)
    base = rotated_variance_shares(X, scores, pca.eigenvalues)
    rows = np.asarray(data.draw(st.permutations(range(len(X)))))

    np.testing.assert_allclose(rotated_variance_shares(X[rows], scores[rows], pca.eigenvalues), base, atol=1e-10)
    np.testing.assert_allclose(rotated_variance_shares(X, scores, pca.eigenvalues, chunk_columns=chunk), base, atol=1e-10)
    # X -> 7 X moltiplica per 49 sia i carichi al quadrato sia gli autovalori: la quota non cambia
    np.testing.assert_allclose(rotated_variance_shares(X * 7.0, scores, pca.eigenvalues * 49.0), base, atol=1e-10)


@given(seed=st.integers(0, 60))
@settings(max_examples=8)
def test_the_shares_survive_a_large_common_offset(seed):
    X = _structured(seed)
    pca, pca_shifted = fit_covariance_pca(X), fit_covariance_pca(X + 1000.0)
    scores, _ = rotated_scores(X, pca, 3, "varimax", 500)

    np.testing.assert_allclose(
        rotated_variance_shares(X + 1000.0, scores, pca_shifted.eigenvalues), rotated_variance_shares(X, scores, pca.eigenvalues), atol=1e-8
    )


@given(seed=st.integers(0, 60))
@settings(max_examples=10)
def test_unrotated_scores_are_refused_because_their_variance_is_the_eigenvalue_not_one(seed):
    X = _structured(seed)
    pca = fit_covariance_pca(X)

    with pytest.raises(ValueError, match="variance 1"):
        rotated_variance_shares(X, pca_scores(X, pca, 3), pca.eigenvalues)


@pytest.mark.parametrize("bad_rows", [-1, 1])
def test_a_matrix_with_another_number_of_subjects_than_the_scores_is_refused(bad_rows):
    X = _structured(0)
    pca = fit_covariance_pca(X)
    scores, _ = rotated_scores(X, pca, 3, "varimax", 500)
    X_bad = X[:-1] if bad_rows < 0 else np.vstack([X, X[:1]])

    with pytest.raises(ValueError, match="does not have the"):
        rotated_variance_shares(X_bad, scores, pca.eigenvalues)


def test_a_one_dimensional_matrix_is_refused():
    X = _structured(0)
    pca = fit_covariance_pca(X)
    scores, _ = rotated_scores(X, pca, 3, "varimax", 500)

    with pytest.raises(ValueError, match="does not have the"):
        rotated_variance_shares(X[:, 0], scores, pca.eigenvalues)


# --- default_embedding_components ----------------------------------------------------------------------------


@given(shares=st.one_of(st.none(), arrays(np.float64, st.integers(2, 8), elements=st.floats(0, 1))))
def test_an_unrotated_run_always_draws_the_first_two_components_whatever_the_shares(shares):
    assert default_embedding_components("none", shares) == (0, 1)


@pytest.mark.parametrize("rotation", ["varimax", "quartimax", "equamax", "oblimax", "geomin_ort"])
@given(shares=arrays(np.float64, st.integers(2, 9), elements=st.floats(0, 1), unique=True))
def test_a_rotated_run_draws_the_two_components_with_the_most_variance_the_larger_first(rotation, shares):
    first, second = default_embedding_components(rotation, shares)

    assert first != second
    assert shares[first] > shares[second] >= np.delete(shares, [first, second]).max(initial=-np.inf)
    assert all(isinstance(index, int) for index in (first, second))


@given(shares=arrays(np.float64, st.integers(2, 9), elements=st.floats(0, 1), unique=True), data=st.data())
def test_the_two_components_chosen_follow_the_shares_when_the_components_are_reordered(shares, data):
    order = np.asarray(data.draw(st.permutations(range(len(shares)))))

    first, second = default_embedding_components("varimax", shares)
    moved_first, moved_second = default_embedding_components("varimax", shares[order])

    assert (order[moved_first], order[moved_second]) == (first, second)


@pytest.mark.parametrize("rotation", ["varimax", "quartimax"])
def test_a_rotated_run_without_shares_is_refused_naming_the_rotation(rotation):
    with pytest.raises(ValueError, match=rotation):
        default_embedding_components(rotation, None)


# --- registry_values / registry_side_indicator --------------------------------------------------------------


def _use_registry(monkeypatch, frame: pd.DataFrame) -> None:
    monkeypatch.setattr(pca_evaluation, "load_participants_registry", lambda: frame)


@given(values=st.lists(st.floats(-1e6, 1e6, allow_nan=False), min_size=1, max_size=10), data=st.data())
def test_registry_values_are_returned_as_floats_in_the_order_requested_and_repeats_are_kept(monkeypatch, values, data):
    frame = pd.DataFrame({"subject_id": [f"s{i}" for i in range(len(values))], "v": [repr(v) for v in values]})
    _use_registry(monkeypatch, frame)
    asked = data.draw(st.lists(st.integers(0, len(values) - 1), min_size=1, max_size=12))

    result = registry_values([f"s{i}" for i in asked], "v")

    assert result.dtype == float
    np.testing.assert_allclose(result, np.asarray(values)[asked], rtol=1e-12)  # pandas legge le stringhe con un parser non esatto all'ultimo ulp


@given(n=st.integers(1, 8), data=st.data())
def test_registry_values_name_the_unregistered_subjects_and_the_empty_cells(monkeypatch, n, data):
    frame = pd.DataFrame({"subject_id": [f"s{i}" for i in range(n)], "v": ["1.5"] * n})
    hole = data.draw(st.integers(0, n - 1))
    frame.loc[hole, "v"] = np.nan
    _use_registry(monkeypatch, frame)

    with pytest.raises(ValueError, match="no 'v'"):
        registry_values([f"s{i}" for i in range(n)], "v")
    with pytest.raises(ValueError, match="not in the registry"):
        registry_values(["s0", "ghost"], "v")
    with pytest.raises(ValueError, match="no 'absent' column"):
        registry_values(["s0"], "absent")


def test_registry_values_refuse_a_non_numeric_cell_instead_of_turning_it_into_nan(monkeypatch):
    _use_registry(monkeypatch, pd.DataFrame({"subject_id": ["a", "b"], "v": ["1.0", "high"]}))

    with pytest.raises(ValueError):
        registry_values(["a", "b"], "v")


_SIDES = st.sampled_from(["left", "right", "both", None])


@given(sides=st.lists(_SIDES, min_size=1, max_size=15), data=st.data())
def test_the_side_indicator_is_one_for_left_zero_for_right_over_exactly_the_single_side_subjects(monkeypatch, sides, data):
    ids = [f"s{i}" for i in range(len(sides))]
    _use_registry(monkeypatch, pd.DataFrame({"subject_id": ids, "lesion_side": sides}))
    order = data.draw(st.permutations(range(len(ids))))
    asked = [ids[i] for i in order]

    indicator, keep = registry_side_indicator(asked)

    expected_keep = np.array([sides[i] in ("left", "right") for i in order])
    np.testing.assert_array_equal(keep, expected_keep)
    np.testing.assert_array_equal(indicator, [1.0 if sides[i] == "left" else 0.0 for i in order if sides[i] in ("left", "right")])
    assert len(indicator) == int(keep.sum()) and set(indicator) <= {0.0, 1.0}


@given(typo=st.sampled_from(["Left", "LEFT", "l", "bilateral", "right ", "unknown", "0"]))
def test_a_misspelt_side_is_an_error_not_a_dropped_subject(monkeypatch, typo):
    _use_registry(monkeypatch, pd.DataFrame({"subject_id": ["a", "b"], "lesion_side": ["left", typo]}))

    with pytest.raises(ValueError, match="outside"):
        registry_side_indicator(["a", "b"])


def test_the_side_indicator_refuses_a_missing_column_and_an_unregistered_subject(monkeypatch):
    _use_registry(monkeypatch, pd.DataFrame({"subject_id": ["a"], "other": ["x"]}))
    with pytest.raises(ValueError, match="no 'lesion_side' column"):
        registry_side_indicator(["a"])

    _use_registry(monkeypatch, pd.DataFrame({"subject_id": ["a"], "lesion_side": ["left"]}))
    with pytest.raises(ValueError, match="not in the registry"):
        registry_side_indicator(["a", "z"])


# --- _combination_key ----------------------------------------------------------------------------------------


_ROTATIONS = ["none", "varimax", "quartimax"]
_COUNTS = [2, 3, 5, 10]


def _keys_for(rotations, counts, swept):
    keys = []
    for rotation in rotations:
        for n in counts:
            parts = {"rotation": rotation, "n_components": n}
            keys.append(",".join(f"{name}={value}" for name, value in parts.items() if name in swept))
    return keys


@pytest.mark.parametrize("swept", [("rotation", "n_components"), ("n_components",), ("rotation",)])
@given(
    rotations=st.lists(st.sampled_from(_ROTATIONS), min_size=1, max_size=3, unique=True),
    counts=st.lists(st.sampled_from(_COUNTS), min_size=1, max_size=4, unique=True),
)
def test_every_swept_combination_finds_its_own_key_and_a_combination_outside_the_grid_raises(swept, rotations, counts):
    base = {"rotation": "none", "n_components": 3}
    rotations = rotations if "rotation" in swept else [base["rotation"]]
    counts = counts if "n_components" in swept else [base["n_components"]]
    keys = _keys_for(rotations, counts, swept)

    found = [_combination_key(keys, base, rotation, n, "run") for rotation in rotations for n in counts]

    assert sorted(found) == sorted(keys)
    outside = next(n for n in _COUNTS + [99] if n not in counts)
    with pytest.raises(ValueError, match="0 combinations match"):
        _combination_key(keys, base, rotations[0], outside, "run")


@given(counts=st.lists(st.sampled_from(_COUNTS), min_size=1, max_size=4, unique=True))
def test_an_unswept_parameter_is_read_from_the_base_params_not_from_the_other_keys(counts):
    keys = [f"n_components={n}" for n in counts]
    base = {"rotation": "varimax", "n_components": 3}

    assert _combination_key(keys, base, "varimax", counts[0], "run") == f"n_components={counts[0]}"
    with pytest.raises(ValueError, match="0 combinations match"):
        _combination_key(keys, base, "none", counts[0], "run")  # la rotazione non spazzolata è varimax, non "none"


def test_a_malformed_key_in_the_archive_is_reported_not_skipped():
    with pytest.raises(ValueError, match="malformed combination key"):
        _combination_key(["rotation=varimax,n_components"], {"rotation": "none", "n_components": 3}, "varimax", 3, "run")
