"""Property tests for src/analysis/adp.py.

`dadapy` (DADApy, con jax) vive in un altro ambiente e qui non c'è: i test di test_adp.py che la
usano sono saltati, e con loro quasi tutto il modulo restava scoperto. Qui `dadapy.Clustering` è
sostituito da `_FakeClustering`, uno stub della libreria *esterna* (mai del codice sotto test):
- verifica il contratto con cui adp la chiama (vicini ordinati, primo vicino = la riga stessa,
  distanza 0 solo su di sé, forma (n, maxk+1)): se adp passasse dati sbagliati, il test cade;
- dà un clustering deterministico e plausibile (componenti connesse del grafo dei vicini con
  soglia Z * mediana della distanza al primo vicino: Z più alto -> meno cluster, come ADP).
Così si testano tutte le parti scritte qui: piano delle righe, cache per metrica/maxk, punteggi,
ARI fra Z consecutivi, validazione. Non si testa l'algoritmo ADP, che è di DADApy.
"""

import logging
import sys
import types

import numpy as np
import pytest
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra.numpy import arrays
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score

from src.analysis import adp
from src.analysis.adp import (
    ADP_METRICS,
    NOISE_LABEL,
    _AdpSession,
    _euclidean_dispersion_scores,
    _head,
    _plan_rows,
    adp_cluster,
    run_adp_tuning_sweep,
    validate_adp_params,
)
from src.analysis.distances import pairwise_distance
from tests.factories.matrices import gaussian_blobs


class _FakeClustering:
    """Stub di dadapy.Clustering (vedi docstring del modulo)."""

    instances: list["_FakeClustering"] = []

    def __init__(self, distances, maxk, verbose=False):
        neighbour_distances, neighbours = distances
        n = neighbour_distances.shape[0]
        assert neighbour_distances.shape == neighbours.shape == (n, maxk + 1)
        assert (neighbours[:, 0] == np.arange(n)).all(), "il primo vicino di ogni punto deve essere il punto stesso"
        assert (neighbour_distances[:, 0] == 0).all()
        assert (neighbour_distances[:, 1] > 0).all(), "due righe distinte a distanza 0 farebbero dividere per 0 la densità"
        assert (np.diff(neighbour_distances, axis=1) >= 0).all(), "i vicini devono essere ordinati per distanza"
        assert np.isfinite(neighbour_distances).all()
        self.neighbour_distances, self.neighbours, self.maxk = neighbour_distances, neighbours, maxk
        self.intrinsic_dim = None
        self.cluster_assignment = None
        self.clustering_calls: list[float] = []
        type(self).instances.append(self)

    def compute_id_2NN(self):
        self.intrinsic_dim = float(self.neighbour_distances[:, 1].mean() + 1.0)

    def compute_density_PAk(self):
        assert self.intrinsic_dim is not None, "la densità si calcola dopo la dimensione intrinseca"

    def compute_clustering_ADP(self, Z, halo):
        assert halo is False
        self.clustering_calls.append(Z)
        cut = Z * float(np.median(self.neighbour_distances[:, 1]))
        n = len(self.neighbours)
        rows, columns = np.nonzero(self.neighbour_distances[:, 1:] <= cut)
        graph = coo_matrix((np.ones(len(rows)), (rows, self.neighbours[rows, columns + 1])), shape=(n, n))
        _, self.cluster_assignment = connected_components(graph, directed=False)


@pytest.fixture
def fake_dadapy(monkeypatch):
    _FakeClustering.instances = []
    monkeypatch.setitem(sys.modules, "dadapy", types.SimpleNamespace(Clustering=_FakeClustering))
    return _FakeClustering


def _binary_blobs(groups=3, per_group=8, columns_per_group=12, seed=0):
    rng = np.random.default_rng(seed)
    X = np.zeros((groups * per_group, groups * columns_per_group), dtype=np.uint8)
    for row in range(len(X)):
        group = row // per_group
        X[row, group * columns_per_group : (group + 1) * columns_per_group] = rng.random(columns_per_group) < 0.75
        X[row, rng.integers(0, X.shape[1])] = 1  # un po' di rumore fuori blocco
    X[X.sum(axis=1) == 0, 0] = 1
    return X


_PARAMS = {"metric": "dice", "Z": 1.5, "maxk": 4}


# --- _import_dadapy ------------------------------------------------------------------------------------------


def test_import_dadapy_returns_the_clustering_class_when_the_package_is_importable(fake_dadapy):
    assert adp._import_dadapy() is fake_dadapy


# --- validate_adp_params -------------------------------------------------------------------------------------


@given(
    metric=st.sampled_from(ADP_METRICS),
    z=st.one_of(st.integers(1, 50), st.floats(1e-6, 50.0, allow_nan=False)),
    maxk=st.integers(2, 500),
)
def test_valid_params_are_returned_unchanged_with_z_as_a_float(metric, z, maxk):
    returned = validate_adp_params({"metric": metric, "Z": z, "maxk": maxk})

    assert returned == (metric, float(z), maxk) and isinstance(returned[1], float)


@pytest.mark.parametrize("z", [0, -1e-9, float("nan"), float("inf"), float("-inf"), True, False, "1.5", None, [1.0]])
def test_z_must_be_a_positive_finite_number(z):
    with pytest.raises(ValueError, match="'Z' must be a positive number"):
        validate_adp_params({**_PARAMS, "Z": z})


@pytest.mark.parametrize("maxk", [1, 0, -3, 2.0, True, "5", None])
def test_maxk_must_be_an_integer_of_at_least_two(maxk):
    with pytest.raises(ValueError, match="'maxk' must be an integer >= 2"):
        validate_adp_params({**_PARAMS, "maxk": maxk})


@given(extra=st.text(min_size=1, max_size=8).filter(lambda key: key not in {"metric", "Z", "maxk"}))
def test_any_unknown_key_is_rejected_by_name(extra):
    with pytest.raises(ValueError, match="unknown"):
        validate_adp_params({**_PARAMS, extra: 1})


@pytest.mark.parametrize("missing", ["metric", "Z", "maxk"])
def test_every_missing_key_is_rejected_by_name(missing):
    params = {key: value for key, value in _PARAMS.items() if key != missing}

    with pytest.raises(ValueError, match=f"missing \\['{missing}'\\]"):
        validate_adp_params(params)


# --- _head ---------------------------------------------------------------------------------------------------


@given(indices=st.lists(st.integers(0, 10**6), max_size=60))
def test_head_lists_at_most_twenty_indices_and_flags_the_rest(indices):
    text = _head(indices)

    assert text.startswith(str(indices[:20]))
    assert text.endswith(" ...") == (len(indices) > 20)


# --- _plan_rows ----------------------------------------------------------------------------------------------


@st.composite
def matrices_with_zero_and_duplicate_rows(draw):
    base = draw(arrays(np.uint8, st.tuples(st.integers(1, 6), st.integers(2, 8)), elements=st.integers(0, 1)))
    base[~base.any(axis=1), 0] = 1
    picks = draw(st.lists(st.integers(-1, len(base) - 1), min_size=1, max_size=14))  # -1: riga di zeri
    rows = [np.zeros(base.shape[1], dtype=np.uint8) if p < 0 else base[p] for p in picks]
    assume(any(p >= 0 for p in picks))
    return np.vstack(rows)


@given(X=matrices_with_zero_and_duplicate_rows())
def test_row_plan_keeps_nonzero_rows_clusters_each_content_once_and_maps_twins_back(X):
    plan = _plan_rows(X)

    expected_keep = np.flatnonzero(X.sum(axis=1) != 0)
    np.testing.assert_array_equal(plan.keep, expected_keep)
    kept = X[plan.keep]
    # ogni contenuto distinto compare una volta fra i rappresentanti, ed è la sua prima occorrenza
    assert len({row.tobytes() for row in kept}) == len(plan.representatives)
    np.testing.assert_array_equal(kept[plan.representatives][plan.inverse], kept)
    for rep in plan.representatives:
        assert not any((kept[earlier] == kept[rep]).all() for earlier in range(rep))


@given(X=matrices_with_zero_and_duplicate_rows())
def test_full_labels_give_noise_to_zero_rows_and_the_twin_label_to_duplicates(X):
    plan = _plan_rows(X)
    representative_labels = np.arange(len(plan.representatives)) * 7 + 3  # etichette arbitrarie

    full = plan.to_full_labels(representative_labels)

    assert full.shape == (len(X),) and full.dtype == np.int64
    assert ((full == NOISE_LABEL) == (X.sum(axis=1) == 0)).all()
    for i in range(len(X)):
        for j in range(i):
            if X[i].any() and (X[i] == X[j]).all():
                assert full[i] == full[j]


def test_an_all_zero_matrix_raises():
    with pytest.raises(ValueError, match="every row of X is all-zero"):
        _plan_rows(np.zeros((5, 3)))


def test_a_row_of_256_ones_in_uint8_is_not_mistaken_for_a_zero_sum_row():
    """lessons_learned #13: la somma in uint8 farebbe il giro e darebbe 0."""
    X = np.ones((3, 256), dtype=np.uint8)

    np.testing.assert_array_equal(_plan_rows(X).keep, [0, 1, 2])


def test_zero_and_duplicate_rows_are_logged_as_warnings_and_a_clean_matrix_is_not(caplog):
    clean = np.eye(4, dtype=np.uint8)
    with caplog.at_level(logging.WARNING):
        _plan_rows(clean)
    assert caplog.records == []

    dirty = np.vstack([clean, clean[0], np.zeros(4, dtype=np.uint8)])
    with caplog.at_level(logging.WARNING):
        _plan_rows(dirty)
    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "all-zero" in messages and "exact duplicates" in messages
    assert "[5]" in messages and "[4]" in messages  # gli indici di riga di twin e riga vuota


# --- _AdpSession: errori prima di dadapy --------------------------------------------------------------------


@given(n_distinct=st.integers(3, 8), extra=st.integers(0, 3))
def test_maxk_must_be_smaller_than_the_number_of_distinct_rows(n_distinct, extra):
    X = np.eye(n_distinct, dtype=np.uint8)
    X = np.vstack([X, X[:extra]])  # i duplicati non contano come righe distinte

    with pytest.raises(ValueError, match="needs more than maxk distinct rows"):
        _AdpSession(X).density_fit("dice", n_distinct)


@pytest.mark.parametrize("metric", ["dice", "euclidean"])
def test_a_matrix_with_nan_is_refused_before_dadapy_sees_a_non_finite_distance(metric):
    X = _binary_blobs().astype(np.float64)
    X[3, 2] = np.nan

    with pytest.raises(ValueError, match="non-finite"):
        _AdpSession(X).density_fit(metric, 4)


def test_two_distinct_rows_at_numerically_zero_distance_are_refused():
    X = np.vstack([gaussian_blobs(n_per_blob=4)[0], [[0.5, 0.5], [0.5, 0.5 + 1e-13]]])

    with pytest.raises(ValueError, match="distance 0"):
        _AdpSession(X).density_fit("euclidean", 4)


# --- _AdpSession con lo stub di dadapy ----------------------------------------------------------------------


def test_the_session_computes_each_distance_and_each_density_fit_once(fake_dadapy, monkeypatch):
    calls = []
    real = adp.pairwise_distance
    monkeypatch.setattr(adp, "pairwise_distance", lambda X, metric: (calls.append(metric), real(X, metric))[1])
    session = _AdpSession(_binary_blobs())

    for z in (0.5, 1.0, 2.0):
        session.labels("dice", 4, z)
    session.labels("dice", 6, 1.0)
    session.labels("euclidean", 4, 1.0)
    session.squared_euclidean_distance()
    session.squared_euclidean_distance()

    assert sorted(calls) == ["dice", "euclidean"]  # una volta per metrica, anche con più maxk e più Z
    assert len(fake_dadapy.instances) == 3  # (dice,4), (dice,6), (euclidean,4)
    np.testing.assert_allclose(session.squared_euclidean_distance(), session.distance("euclidean") ** 2)
    assert session.plan.n_rows == len(session.X_kept) == 24  # nessuna riga scartata: X_kept è la matrice stessa


@pytest.mark.parametrize("metric", ADP_METRICS)
@given(seed=st.integers(0, 50), n_zero=st.integers(0, 3), n_twins=st.integers(0, 3), z=st.floats(0.3, 3.0))
@settings(max_examples=20)
def test_labels_cover_every_row_noise_only_where_the_row_is_empty_and_twins_agree(metric, seed, n_zero, n_twins, z):
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "dadapy", types.SimpleNamespace(Clustering=_FakeClustering))
        X = _binary_blobs(seed=seed)
        zero_rows = list(range(0, 2 * n_zero, 2))
        X[zero_rows] = 0
        twins = [(5 + 4 * k, 6 + 4 * k) for k in range(n_twins)]
        for original, copy in twins:
            X[copy] = X[original]

        full, kept, intrinsic_dim = _AdpSession(X).labels(metric, 4, z)

    assert full.shape == (len(X),) and np.isfinite(intrinsic_dim)
    assert set(np.flatnonzero(full == NOISE_LABEL)) == set(zero_rows)
    np.testing.assert_array_equal(kept, full[X.sum(axis=1) != 0])
    for original, copy in twins:
        assert full[original] == full[copy]
    clusters = np.unique(full[full != NOISE_LABEL])
    np.testing.assert_array_equal(clusters, np.arange(len(clusters)))


def test_adp_cluster_is_deterministic_and_is_the_label_vector_of_the_sweep(fake_dadapy):
    X = _binary_blobs()

    labels = adp_cluster(X, _PARAMS)
    _, by_combo = run_adp_tuning_sweep(X, _PARAMS, {"Z": [_PARAMS["Z"]]})

    np.testing.assert_array_equal(labels, adp_cluster(X, _PARAMS))
    np.testing.assert_array_equal(labels, by_combo[(_PARAMS["Z"],)])


@given(z_low=st.floats(0.2, 1.0), gap=st.floats(0.5, 3.0))
@settings(max_examples=20)
def test_a_higher_z_never_gives_more_clusters_with_the_stub(z_low, gap):
    """Sanità dello stub e di come adp lo guida (non una proprietà di ADP): Z cresce -> i cluster non aumentano."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "dadapy", types.SimpleNamespace(Clustering=_FakeClustering))
        results, _ = run_adp_tuning_sweep(_binary_blobs(), _PARAMS, {"Z": [z_low, z_low + gap]})

    assert results["n_clusters_found"].iloc[1] <= results["n_clusters_found"].iloc[0]


# --- run_adp_tuning_sweep ------------------------------------------------------------------------------------


def test_the_sweep_has_one_row_per_combination_in_product_order_with_every_documented_column(fake_dadapy):
    grid = {"Z": [2.0, 0.5], "maxk": [3, 5]}

    results, by_combo = run_adp_tuning_sweep(_binary_blobs(), _PARAMS, grid)

    assert list(zip(results["Z"], results["maxk"])) == [(2.0, 3), (2.0, 5), (0.5, 3), (0.5, 5)]
    assert list(by_combo) == [(2.0, 3), (2.0, 5), (0.5, 3), (0.5, 5)]
    for column in ("silhouette", "calinski_harabasz", "davies_bouldin", "noise_fraction", "n_clusters_found",
                   "largest_cluster_share", "n_small_clusters", "id_2nn", "ari_vs_prev_z"):
        assert column in results.columns


@pytest.mark.parametrize("metric", ["dice", "jaccard", "euclidean"])
@given(seed=st.integers(0, 30), n_zero=st.integers(0, 2))
@settings(max_examples=12)
def test_the_summary_columns_are_recomputed_from_the_labels_exactly(metric, seed, n_zero):
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "dadapy", types.SimpleNamespace(Clustering=_FakeClustering))
        X = _binary_blobs(seed=seed)
        X[:n_zero] = 0
        results, by_combo = run_adp_tuning_sweep(X, {**_PARAMS, "metric": metric}, {"Z": [0.8, 1.5, 3.0]})

    kept_mask = X.sum(axis=1) != 0
    for row, labels in zip(results.itertuples(), by_combo.values()):
        clustered = labels[labels != NOISE_LABEL]
        sizes = np.bincount(clustered)
        assert row.noise_fraction == pytest.approx((labels == NOISE_LABEL).mean())
        assert row.n_clusters_found == len(sizes)
        assert row.largest_cluster_share == pytest.approx(sizes.max() / len(labels))
        assert row.n_small_clusters == (sizes < adp.SMALL_CLUSTER_SIZE).sum()
        if 2 <= len(sizes) <= kept_mask.sum() - 1:
            assert row.silhouette == pytest.approx(silhouette_score(pairwise_distance(X[kept_mask], metric), labels[kept_mask], metric="precomputed"))
        else:
            assert np.isnan(row.silhouette) and np.isnan(row.calinski_harabasz) and np.isnan(row.davies_bouldin)


@pytest.mark.parametrize("offset", [0.0, 1000.0])
def test_euclidean_centroid_scores_in_the_sweep_equal_sklearn_on_the_features(fake_dadapy, offset):
    X, _ = gaussian_blobs(n_per_blob=10, scale=0.6)
    X = X + offset

    results, by_combo = run_adp_tuning_sweep(X, {**_PARAMS, "metric": "euclidean", "maxk": 5}, {"Z": [1.0, 2.0]})

    for row, labels in zip(results.itertuples(), by_combo.values()):
        assert 2 <= row.n_clusters_found
        assert row.calinski_harabasz == pytest.approx(calinski_harabasz_score(X, labels), rel=1e-6)
        assert row.davies_bouldin == pytest.approx(davies_bouldin_score(X, labels), rel=1e-6)


def test_dice_and_jaccard_leave_the_centroid_based_scores_as_nan_and_still_score_the_silhouette(fake_dadapy):
    results, _ = run_adp_tuning_sweep(_binary_blobs(), _PARAMS, {"metric": ["dice", "jaccard"]})

    assert results["calinski_harabasz"].isna().all() and results["davies_bouldin"].isna().all()
    assert np.isfinite(results["silhouette"]).all()


def test_too_few_or_too_many_clusters_record_nan_scores_but_keep_the_cluster_counts(fake_dadapy, caplog):
    X = _binary_blobs()

    with caplog.at_level(logging.WARNING):
        results, _ = run_adp_tuning_sweep(X, {**_PARAMS, "maxk": 20}, {"Z": [1e-3, 1e3]})  # maxk alto: il grafo dei vicini collega tutto

    one_per_row, single = results.iloc[0], results.iloc[1]
    assert one_per_row["n_clusters_found"] == len(X) and single["n_clusters_found"] == 1
    assert results[["silhouette", "calinski_harabasz", "davies_bouldin"]].isna().all().all()
    assert single["largest_cluster_share"] == 1.0
    assert any("need 2..n-1" in record.getMessage() for record in caplog.records)


@given(
    z_values=st.lists(st.sampled_from([0.4, 0.7, 1.0, 1.5, 2.2, 3.5]), min_size=1, max_size=6, unique=True),
    max_ks=st.lists(st.sampled_from([3, 4, 6]), min_size=1, max_size=3, unique=True),
    data=st.data(),
)
@settings(max_examples=15)
def test_ari_vs_prev_z_compares_each_combination_with_the_next_lower_z_of_the_same_other_parameters(z_values, max_ks, data):
    z_values = data.draw(st.permutations(z_values))
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "dadapy", types.SimpleNamespace(Clustering=_FakeClustering))
        results, by_combo = run_adp_tuning_sweep(_binary_blobs(), _PARAMS, {"Z": list(z_values), "maxk": list(max_ks)})

    for row in results.itertuples():
        lower = sorted(z for z in z_values if z < row.Z)
        if not lower:
            assert np.isnan(row.ari_vs_prev_z)
            continue
        earlier, later = by_combo[(lower[-1], row.maxk)], by_combo[(row.Z, row.maxk)]
        clustered = (earlier != NOISE_LABEL) & (later != NOISE_LABEL)
        assert row.ari_vs_prev_z == pytest.approx(adjusted_rand_score(earlier[clustered], later[clustered]))
        assert -1.0 - 1e-12 <= row.ari_vs_prev_z <= 1.0 + 1e-12


def test_ari_vs_prev_z_is_nan_for_the_whole_column_when_z_is_not_swept(fake_dadapy):
    results, _ = run_adp_tuning_sweep(_binary_blobs(), _PARAMS, {"maxk": [3, 4, 5]})

    assert results["ari_vs_prev_z"].isna().all()


def test_ari_ignores_the_dropped_rows_instead_of_counting_them_as_a_cluster_both_partitions_share(fake_dadapy):
    X = _binary_blobs()
    X[:6] = 0  # molte righe a rumore in entrambe le partizioni: contarle come un cluster comune gonfia l'ARI

    results, by_combo = run_adp_tuning_sweep(X, _PARAMS, {"Z": [0.7, 1.3]})

    a, b = by_combo[(0.7,)], by_combo[(1.3,)]
    assert (a[:6] == NOISE_LABEL).all() and (b[:6] == NOISE_LABEL).all()
    assert len(np.unique(a[6:])) != len(np.unique(b[6:]))  # le due partizioni differiscono davvero
    assert results["ari_vs_prev_z"].iloc[1] == pytest.approx(adjusted_rand_score(a[6:], b[6:]))
    assert results["ari_vs_prev_z"].iloc[1] != pytest.approx(adjusted_rand_score(a, b))


@pytest.mark.parametrize("bad_grid", [{"Z": [1.0, 0.0]}, {"maxk": [3, 1]}, {"metric": ["dice", "cosine"]}])
def test_an_invalid_value_anywhere_in_the_grid_raises_before_a_result_is_returned(fake_dadapy, bad_grid):
    with pytest.raises(ValueError):
        run_adp_tuning_sweep(_binary_blobs(), _PARAMS, bad_grid)


def test_a_duplicate_value_in_the_grid_is_rejected_instead_of_collapsing_silently(fake_dadapy):
    with pytest.raises(ValueError, match="duplicate"):
        run_adp_tuning_sweep(_binary_blobs(), _PARAMS, {"Z": [1.0, 1.0, 2.0]})


def test_a_non_default_param_in_base_params_that_the_grid_does_not_override_is_used(fake_dadapy):
    results, _ = run_adp_tuning_sweep(_binary_blobs(), {**_PARAMS, "maxk": 6}, {"Z": [1.0]})

    assert len(fake_dadapy.instances) == 1 and fake_dadapy.instances[0].maxk == 6
    assert results["Z"].tolist() == [1.0]


# --- _euclidean_dispersion_scores ---------------------------------------------------------------------------


@st.composite
def labelled_points(draw, max_points=18):
    n = draw(st.integers(5, max_points))
    d = draw(st.integers(1, 5))
    # valori o 0 o di modulo >= 0.01: differenze di 1e-34 fra punti 'uguali' sono rumore, non un caso da confrontare
    X = draw(arrays(np.float64, (n, d), elements=st.one_of(st.just(0.0), st.floats(0.01, 10), st.floats(-10, -0.01))))
    k = draw(st.integers(2, min(5, n - 1)))
    labels = np.asarray(draw(st.lists(st.integers(0, k - 1), min_size=n, max_size=n)))
    assume(len(np.unique(labels)) >= 2)
    return X, labels


def _is_well_spread(X: np.ndarray) -> bool:
    """Rango pieno con margine: `matrix_rank` da solo accetta una nuvola di punti uguali (residuo di centratura ~1e-16)."""
    return bool(np.linalg.svd(X - X.mean(axis=0), compute_uv=False).min() > 1e-3)


@given(case=labelled_points())
def test_dispersion_scores_equal_sklearn_on_generic_points(case):
    X, labels = case
    assume(_is_well_spread(X))  # niente nuvole degeneri: hanno il loro test
    ch, db = _euclidean_dispersion_scores(pairwise_distance(X, "euclidean") ** 2, labels)

    assert ch == pytest.approx(calinski_harabasz_score(X, labels), rel=1e-5, abs=1e-8)
    assert db == pytest.approx(davies_bouldin_score(X, labels), rel=1e-5, abs=1e-8)


@given(case=labelled_points(), data=st.data())
def test_dispersion_scores_do_not_depend_on_row_order_or_on_cluster_names(case, data):
    X, labels = case
    squared = pairwise_distance(X, "euclidean") ** 2
    order = np.asarray(data.draw(st.permutations(range(len(X)))))
    renamed = (labels * 5 + 11)

    base = _euclidean_dispersion_scores(squared, labels)

    assert _euclidean_dispersion_scores(squared[np.ix_(order, order)], labels[order]) == pytest.approx(base, rel=1e-6, abs=1e-8)
    assert _euclidean_dispersion_scores(squared, renamed) == pytest.approx(base, rel=1e-9)


@given(case=labelled_points(), shift=st.sampled_from([0.0, 100.0, 1000.0]))
def test_dispersion_scores_are_finite_and_nonnegative_even_with_a_large_common_offset(case, shift):
    """lessons_learned #42: i residui ~1e-8 della formula non devono diventare un indice enorme o NaN."""
    X, labels = case

    ch, db = _euclidean_dispersion_scores(pairwise_distance(X + shift, "euclidean") ** 2, labels)

    assert np.isfinite(ch) and np.isfinite(db) and ch >= 0 and db >= 0


@given(case=labelled_points(), shift=st.sampled_from([0.0, 1000.0]))
def test_dispersion_scores_are_translation_invariant_up_to_rounding(case, shift):
    X, labels = case
    assume(_is_well_spread(X))

    plain = _euclidean_dispersion_scores(pairwise_distance(X, "euclidean") ** 2, labels)
    shifted = _euclidean_dispersion_scores(pairwise_distance(X + shift, "euclidean") ** 2, labels)

    assert shifted == pytest.approx(plain, rel=1e-3, abs=1e-5)


def test_clusters_made_only_of_identical_points_give_the_degenerate_returns_of_sklearn():
    """Stesso punto ripetuto dentro ogni cluster: dispersione 0 -> CH 1.0 e DB 0.0, come sklearn."""
    X = np.repeat(np.array([[0.0, 0.0], [3.0, 4.0], [-2.0, 5.0]]), 4, axis=0)
    labels = np.repeat([0, 1, 2], 4)

    ch, db = _euclidean_dispersion_scores(pairwise_distance(X, "euclidean") ** 2, labels)

    assert (ch, db) == (pytest.approx(calinski_harabasz_score(X, labels)), pytest.approx(davies_bouldin_score(X, labels)))
    assert (ch, db) == (1.0, 0.0)


def test_clusters_of_identical_points_stay_degenerate_with_a_large_common_offset():
    X = np.repeat(np.array([[0.0, 0.0], [3.0, 4.0], [-2.0, 5.0]]), 4, axis=0) + 1000.0
    labels = np.repeat([0, 1, 2], 4)

    ch, db = _euclidean_dispersion_scores(pairwise_distance(X, "euclidean") ** 2, labels)

    assert ch == pytest.approx(calinski_harabasz_score(X, labels)) and db == pytest.approx(davies_bouldin_score(X, labels))
