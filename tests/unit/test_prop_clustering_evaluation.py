"""Test a proprietà di src/analysis/clustering_evaluation.py: la tabella di applicabilità, purezza dei
vicini con i pareggi, silhouette per cluster, appartenenza morbida e riepiloghi geometrici su etichette
arbitrarie (rumore -1, id non contigui, cluster unico, tutti singoletti)."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_evaluation import (
    EVALUATIONS,
    distance_matrix_silhouette,
    geometric_summary,
    knn_purity,
    model_fit_metrics,
    per_cluster_silhouette,
    require_applicable,
    saturated_pair_share,
    soft_membership_summary,
    weakest_soft_members,
)
from tests.factories.matrices import gaussian_blobs


def _points(seed: int, n: int, dims: int = 2) -> np.ndarray:
    return np.random.default_rng(seed).normal(size=(n, dims))


def _distances(points: np.ndarray) -> np.ndarray:
    return np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)


def _rename(labels: np.ndarray, seed: int) -> np.ndarray:
    names = np.unique(labels)
    new = np.random.default_rng(seed).choice(np.arange(10, 500), size=len(names), replace=False)
    return pd.Series(labels).map(dict(zip(names.tolist(), new.tolist()))).to_numpy()


@st.composite
def _clustered_points(draw, with_noise: bool = False, min_n: int = 6, max_n: int = 30):
    """(points, labels): etichette non contigue, almeno 2 cluster veri, eventualmente rumore."""
    n = draw(st.integers(min_n, max_n))
    pool = draw(st.lists(st.sampled_from([0, 1, 4, 9, 11]), min_size=2, max_size=4, unique=True))
    if with_noise:
        pool = [*pool, -1]
    labels = np.array(draw(st.lists(st.sampled_from(pool), min_size=n, max_size=n)))
    assume(len(np.unique(labels[labels != -1])) >= 2)
    return _points(draw(st.integers(0, 10_000)), n), labels


# --- tabella di applicabilità ---------------------------------------------------------------------


@pytest.mark.parametrize("evaluation", sorted(EVALUATIONS))
@pytest.mark.parametrize("method", sorted(CLUSTERING_METHODS))
def test_a_run_is_accepted_exactly_by_the_evaluations_that_list_its_method(evaluation, method):
    if method in EVALUATIONS[evaluation].methods:
        require_applicable(evaluation, method)
    else:
        with pytest.raises(ValueError, match=f"'{method}'"):
            require_applicable(evaluation, method)


def test_an_unknown_evaluation_is_refused_with_the_list_of_known_ones():
    with pytest.raises(ValueError, match="unknown evaluation"):
        require_applicable("silhouette_magica", "kmeans")


def test_every_method_gets_some_evaluation_of_its_geometry():
    for method in CLUSTERING_METHODS:
        assert any(method in EVALUATIONS[name].methods for name in ("geometric_metrics", "knn_purity", "dbcv"))


def test_no_method_gets_both_the_geometric_indices_and_dbcv():
    assert not EVALUATIONS["geometric_metrics"].methods & EVALUATIONS["dbcv"].methods


# --- saturated_pair_share -------------------------------------------------------------------------


@given(st.integers(2, 12), st.integers(0, 10_000), st.sampled_from([0.0, 0.3, 0.7, 1.0]))
def test_saturated_share_counts_the_pairs_at_distance_one(n, seed, saturation):
    rng = np.random.default_rng(seed)
    upper = np.triu(np.where(rng.random((n, n)) < saturation, 1.0, rng.uniform(0, 0.9, size=(n, n))), 1)
    distances = upper + upper.T
    share = saturated_pair_share(distances)
    assert 0.0 <= share <= 1.0
    assert share == pytest.approx((np.triu(distances, 1) >= 1 - 1e-9).sum() / (n * (n - 1) / 2))  # la diagonale non conta mai


@pytest.mark.parametrize("shape", [(1, 1), (3, 4), (0, 0)])
def test_saturated_share_refuses_a_matrix_that_is_not_square_with_two_subjects(shape):
    with pytest.raises(ValueError, match="square matrix of at least 2"):
        saturated_pair_share(np.zeros(shape))


# --- knn_purity -----------------------------------------------------------------------------------


@settings(max_examples=40)
@given(_clustered_points(), st.integers(1, 3), st.integers(0, 10_000))
def test_knn_purity_is_a_share_invariant_to_label_names_and_row_order(data, k, seed):
    points, labels = data
    sizes = pd.Series(labels).value_counts()
    assume((sizes > k).any() and len(points) > k)
    distances = _distances(points)
    result = knn_purity(distances, labels, k)

    assert 0.0 <= result.purity <= 1.0 and 0.0 <= result.chance <= 1.0
    assert result.clusters["n"].sum() == len(labels)
    assert (result.clusters["purity"].between(0, 1)).all()
    assert result.n_not_evaluable == int(sizes[sizes <= k].sum())  # i soggetti dei cluster con <= k membri
    assert result.clusters["evaluable"].tolist() == (result.clusters["n"] > k).tolist()

    renamed = knn_purity(distances, _rename(labels, seed), k)
    assert renamed.purity == pytest.approx(result.purity)
    order = np.random.default_rng(seed).permutation(len(labels))
    permuted = knn_purity(distances[np.ix_(order, order)], labels[order], k)
    assert permuted.purity == pytest.approx(result.purity)
    assert permuted.chance == pytest.approx(result.chance)


@settings(max_examples=40)
@given(st.integers(6, 24), st.integers(2, 4), st.integers(1, 3), st.integers(0, 10_000))
def test_with_every_distance_tied_the_purity_is_exactly_the_chance_level(n, n_clusters, k, seed):
    """Pareggio totale (distanza 1 tra tutti, come due lesioni senza voxel in comune): nessun vicino è più
    vicino di un altro, quindi la purezza attesa è quella di etichette indipendenti dalla geometria."""
    labels = np.random.default_rng(seed).integers(0, n_clusters, size=n)
    assume(len(np.unique(labels)) >= 2 and (pd.Series(labels).value_counts() > k).any() and k < n - 1)
    distances = np.ones((n, n)) - np.eye(n)
    result = knn_purity(distances, labels, k)
    assert result.purity == pytest.approx(result.chance)
    assert result.tied_share == 1.0  # tutti hanno bisogno dello spareggio atteso


def _exact_expected_purity(distances: np.ndarray, labels: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Purezza attesa per soggetto e se ha avuto bisogno dello spareggio, enumerando TUTTE le scelte possibili
    tra i candidati a pari distanza del k-esimo vicino (media esatta, non la formula chiusa del codice)."""
    n = len(labels)
    purity, tied = np.empty(n), np.empty(n, dtype=bool)
    for i in range(n):
        others = [j for j in range(n) if j != i]
        kth = sorted(distances[i, others])[k - 1]
        sure = [j for j in others if distances[i, j] < kth]
        candidates = [j for j in others if distances[i, j] == kth]
        needed = k - len(sure)
        choices = list(itertools.combinations(candidates, needed))
        fractions = [sum(labels[j] == labels[i] for j in [*sure, *chosen]) / k for chosen in choices]
        purity[i], tied[i] = float(np.mean(fractions)), len(candidates) > needed
    return purity, tied


@settings(max_examples=40)
@given(st.integers(5, 8), st.integers(1, 3), st.integers(0, 10_000))
def test_knn_purity_with_tied_distances_is_the_exact_expectation_over_the_tied_choices(n, k, seed):
    rng = np.random.default_rng(seed)
    upper = np.triu(rng.integers(1, 4, size=(n, n)).astype(float), 1)  # distanze intere 1..3: pareggi ovunque
    distances = upper + upper.T
    labels = rng.integers(0, 2, size=n)
    assume(len(np.unique(labels)) == 2 and (np.bincount(labels) > k).any())
    result = knn_purity(distances, labels, k)
    expected_purity, expected_tied = _exact_expected_purity(distances, labels, k)
    evaluable = np.isin(labels, result.clusters.index[result.clusters["evaluable"]])
    assert result.purity == pytest.approx(expected_purity[evaluable].mean())
    assert result.tied_share == pytest.approx(expected_tied.mean())


@settings(max_examples=30)
@given(st.lists(st.integers(4, 8), min_size=2, max_size=4), st.integers(1, 3))
def test_perfectly_separated_blocks_have_purity_one(sizes, k):
    labels = np.repeat(np.arange(len(sizes)) * 5, sizes)
    same = labels[:, None] == labels[None, :]
    distances = np.where(same, 0.1, 1.0) * (1 - np.eye(len(labels)))
    result = knn_purity(distances, labels, k)
    assert result.purity == pytest.approx(1.0)
    assert result.n_not_evaluable == 0
    assert result.purity >= result.chance


def test_knn_purity_of_labels_independent_of_the_geometry_is_near_the_chance_level():
    rng = np.random.default_rng(0)
    points = rng.normal(size=(400, 3))
    labels = rng.integers(0, 3, size=400)
    result = knn_purity(_distances(points), labels, 5)
    assert abs(result.purity - result.chance) < 0.05


@pytest.mark.parametrize("k", [0, -1, 6, 10])
def test_knn_purity_refuses_k_outside_one_to_n_minus_one(k):
    with pytest.raises(ValueError, match="k must be in"):
        knn_purity(np.ones((6, 6)) - np.eye(6), np.array([0, 0, 0, 1, 1, 1]), k)


@pytest.mark.parametrize("labels, match", [
    ([0, 0, 0, 0, 0, 0], "at least 2 clusters"),
    ([0, 0, 0, 1, 1, -1], "noise"),
    ([0, 0, 1, 1, 2, 2], "no cluster has more than"),
])
def test_knn_purity_refuses_degenerate_labelings(labels, match):
    with pytest.raises(ValueError, match=match):
        knn_purity(np.ones((6, 6)) - np.eye(6), np.array(labels), 2)


@pytest.mark.parametrize("bad", ["nan", "inf", "shape"])
def test_distance_functions_refuse_non_finite_or_misshapen_matrices(bad):
    distances = np.ones((6, 6)) - np.eye(6)
    if bad == "nan":
        distances[0, 1] = np.nan
    elif bad == "inf":
        distances[2, 3] = np.inf
    else:
        distances = distances[:, :5]
    labels = np.array([0, 0, 0, 1, 1, 1])
    with pytest.raises(ValueError):
        knn_purity(distances, labels, 1)
    with pytest.raises(ValueError):
        distance_matrix_silhouette(distances, labels)


# --- silhouette -----------------------------------------------------------------------------------


@settings(max_examples=40)
@given(_clustered_points(), st.integers(0, 10_000))
def test_distance_matrix_silhouette_matches_sklearn_and_ignores_label_names_and_order(data, seed):
    points, labels = data
    assume(len(np.unique(labels)) <= len(labels) - 1)
    distances = _distances(points)
    breakdown = distance_matrix_silhouette(distances, labels)

    assert breakdown.micro == pytest.approx(silhouette_score(distances, labels, metric="precomputed"))
    assert -1.0 <= breakdown.minimum <= breakdown.macro <= 1.0
    assert -1.0 <= breakdown.micro <= 1.0
    assert breakdown.clusters["n"].sum() == len(labels)
    assert breakdown.clusters["share_negative"].between(0, 1).all()

    order = np.random.default_rng(seed).permutation(len(labels))
    permuted = distance_matrix_silhouette(distances[np.ix_(order, order)], _rename(labels[order], seed))
    assert permuted.micro == pytest.approx(breakdown.micro) and permuted.macro == pytest.approx(breakdown.macro)


@pytest.mark.parametrize("labels", [[0, 0, 0, 0], [0, 1, 2, 3]])
def test_silhouette_of_one_cluster_or_all_singletons_is_refused_not_invented(labels):
    with pytest.raises(ValueError, match="cannot compute the silhouette"):
        distance_matrix_silhouette(_distances(_points(0, 4)), np.array(labels))


@settings(max_examples=30)
@given(_clustered_points(with_noise=True), st.integers(0, 10_000))
def test_per_cluster_silhouette_leaves_the_noise_out_whatever_its_names(data, seed):
    points, labels = data
    kept = labels != -1
    assume(len(np.unique(labels[kept])) <= kept.sum() - 1)
    breakdown = per_cluster_silhouette(points, labels, {})
    assert -1 not in breakdown.clusters.index
    assert breakdown.clusters["n"].sum() == kept.sum()  # il rumore non è né un cluster né un soggetto valutato
    without_noise = per_cluster_silhouette(points[kept], labels[kept], {})
    assert breakdown.micro == pytest.approx(without_noise.micro)
    assert per_cluster_silhouette(points, _rename_keep_noise(labels, seed), {}).macro == pytest.approx(breakdown.macro)


def _rename_keep_noise(labels: np.ndarray, seed: int) -> np.ndarray:
    renamed = _rename(labels[labels != -1], seed)
    out = labels.copy()
    out[labels != -1] = renamed
    return out


def test_per_cluster_silhouette_refuses_a_run_with_a_non_euclidean_affinity():
    points, labels = gaussian_blobs(5, seed=2)
    with pytest.raises(ValueError, match="Euclidean"):
        per_cluster_silhouette(points, labels, {"affinity": "precomputed"})


def test_per_cluster_silhouette_refuses_a_binary_metric_on_a_continuous_matrix():
    points, labels = gaussian_blobs(5, seed=2)
    with pytest.raises(ValueError, match="dice"):
        per_cluster_silhouette(points, labels, {"metric": "dice"})


# --- geometric_summary ----------------------------------------------------------------------------


@settings(max_examples=40)
@given(_clustered_points(with_noise=True))
def test_geometric_summary_is_finite_and_consistent_or_a_documented_error(data):
    points, labels = data
    try:
        summary = geometric_summary(points, labels, {})
    except ValueError as error:
        assert "undefined" in str(error) or "cannot compute" in str(error) or "at least 2 clusters" in str(error)
        return
    kept = labels != -1
    values = [summary.silhouette, summary.silhouette_macro, summary.silhouette_min, summary.calinski_harabasz,
              summary.davies_bouldin, summary.dunn, summary.noise_fraction, summary.largest_cluster_share]
    assert all(np.isfinite(v) for v in values)
    assert summary.n_subjects == len(labels) and summary.n_components == points.shape[1]
    assert summary.n_clusters == len(np.unique(labels[kept]))
    assert summary.noise_fraction == pytest.approx((~kept).mean())
    assert summary.largest_cluster_share * len(labels) == pytest.approx(pd.Series(labels[kept]).value_counts().max())
    assert summary.calinski_harabasz >= 0 and summary.davies_bouldin >= 0 and summary.dunn >= 0
    assert -1 <= summary.silhouette_min <= summary.silhouette_macro <= 1


@settings(max_examples=25)
@given(_clustered_points(with_noise=True), st.floats(-5000, 5000), st.integers(0, 10_000))
def test_geometric_summary_does_not_depend_on_row_order_or_on_a_common_offset(data, offset, seed):
    """Lezione #42: indici riscritti con identità algebriche si rompono con un grande offset comune."""
    points, labels = data
    try:
        base = geometric_summary(points, labels, {})
    except ValueError:
        return
    order = np.random.default_rng(seed).permutation(len(labels))
    moved = geometric_summary(points[order] + offset, labels[order], {})
    for name in ("silhouette", "silhouette_macro", "calinski_harabasz", "davies_bouldin", "dunn"):
        assert getattr(moved, name) == pytest.approx(getattr(base, name), rel=1e-5, abs=1e-6), name


@pytest.mark.parametrize("labels", [[0] * 10, [-1] * 10, [0] * 5 + [-1] * 5])
def test_geometric_summary_refuses_fewer_than_two_clusters_once_noise_is_left_out(labels):
    with pytest.raises(ValueError, match="at least 2 clusters"):
        geometric_summary(_points(0, 10), np.array(labels), {})


def test_geometric_summary_refuses_all_singletons_instead_of_returning_nan():
    with pytest.raises(ValueError):
        geometric_summary(_points(0, 6), np.arange(6), {})


def test_geometric_summary_refuses_labels_that_do_not_match_the_rows():
    with pytest.raises(ValueError, match="one row per label"):
        geometric_summary(_points(0, 8), np.array([0, 1, 0, 1]), {})


# --- soft membership ------------------------------------------------------------------------------


@st.composite
def _soft_run(draw, min_clusters: int = 1):
    k = draw(st.integers(min_clusters, 4))
    n = draw(st.integers(k + 1, 25))
    labels = np.array(draw(st.lists(st.integers(-1, k - 1), min_size=n, max_size=n)))
    labels[:k] = np.arange(k)  # tutti i cluster 0..k-1 presenti
    membership = np.random.default_rng(draw(st.integers(0, 10_000))).uniform(0.01, 0.99, size=(n, k))
    return labels, membership


@given(_soft_run())
def test_soft_summary_accounts_for_every_subject_and_keeps_probabilities_in_range(run):
    labels, membership = run
    summary = soft_membership_summary(labels, membership)
    k = membership.shape[1]
    assert summary.clusters["n"].sum() == (labels != -1).sum()
    assert summary.n_noise == (labels == -1).sum()
    assert summary.clusters["own_mean"].between(0, 1).all()
    np.testing.assert_allclose(np.diag(summary.mean_vectors.loc[list(range(k))].to_numpy()), summary.clusters["own_mean"].to_numpy())
    assert (-1 in summary.mean_vectors.index) == bool((labels == -1).any())  # il rumore ha il suo vettore medio solo se c'è
    if k > 1:
        assert (summary.clusters["top_other"].to_numpy() != summary.clusters.index.to_numpy()).all()
        assert summary.clusters["top_other_mean"].between(0, 1).all()
    else:
        assert summary.clusters["top_other_mean"].isna().all()  # un solo cluster: nessun "altro", NaN e non 0


@given(_soft_run(), st.integers(1, 40))
def test_weakest_members_are_the_lowest_own_probabilities_noise_excluded(run, n_lowest):
    labels, membership = run
    table = weakest_soft_members(labels, membership, n_lowest)
    clustered = np.flatnonzero(labels != -1)
    own = membership[clustered, labels[clustered]]

    assert len(table) == min(n_lowest, len(clustered))
    assert table["own_membership"].is_monotonic_increasing
    assert set(table.index) <= set(clustered.tolist())  # il rumore non compare mai
    np.testing.assert_allclose(table["own_membership"].to_numpy(), np.sort(own)[: len(table)])
    if membership.shape[1] > 1:
        assert (table["best_other"].to_numpy() != table["cluster"].to_numpy()).all()
    else:
        assert table["best_other"].isna().all() and table["best_other_probability"].isna().all()


def test_soft_summary_and_weakest_refuse_inconsistent_inputs():
    labels = np.array([0, 0, 1, 1, -1])
    good = np.full((5, 2), 0.5)
    with pytest.raises(ValueError, match="every subject is noise"):
        soft_membership_summary(np.full(5, -1), np.empty((5, 0)))
    with pytest.raises(ValueError, match="0..k-1"):
        soft_membership_summary(np.array([0, 0, 2, 2, -1]), good)
    with pytest.raises(ValueError, match="must be"):
        soft_membership_summary(labels, good[:4])
    with pytest.raises(ValueError, match="n_lowest"):
        weakest_soft_members(labels, good, 0)
    with pytest.raises(ValueError, match="every subject is noise"):
        weakest_soft_members(np.full(5, -1), np.empty((5, 0)), 3)


# --- model_fit_metrics ----------------------------------------------------------------------------


@given(st.lists(st.integers(-1, 4), min_size=1, max_size=40))
def test_density_model_fit_reads_noise_and_cluster_count_from_the_labels_alone(labels):
    labels = np.array(labels)
    for method in ("hdbscan", "hdbscan_soft"):
        fit = model_fit_metrics(method, np.empty((len(labels), 0)), {}, labels)
        assert fit["noise_fraction"] == pytest.approx((labels == -1).mean())
        assert fit["n_clusters_found"] == len(np.unique(labels[labels != -1]))


@pytest.mark.parametrize("method", ["spectral", "adp"])
def test_model_fit_metrics_refuses_methods_without_a_model_statistic(method):
    with pytest.raises(ValueError, match=f"'{method}'"):
        model_fit_metrics(method, np.zeros((4, 2)), {}, np.zeros(4, dtype=int))


def test_kmeans_model_fit_needs_the_refit_to_reproduce_the_stored_labels_exactly():
    X, _ = gaussian_blobs(8, seed=4)
    params = {"n_clusters": 3, "random_state": 0, "n_init": "auto"}
    labels = CLUSTERING_METHODS["kmeans"](X, params)
    assert model_fit_metrics("kmeans", X, params, labels)["inertia"] == pytest.approx(KMeans(**params).fit(X).inertia_)
    swapped = (labels + 1) % 3  # stessa partizione, altri nomi: non è la stessa run, e lo dice
    with pytest.raises(ValueError, match="does not reproduce the stored labels"):
        model_fit_metrics("kmeans", X, params, swapped)
