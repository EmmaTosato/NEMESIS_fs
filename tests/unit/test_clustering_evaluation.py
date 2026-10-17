"""Unit tests for src/analysis/clustering_evaluation.py."""

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_evaluation import (
    EVALUATIONS,
    adp_summary,
    distance_matrix_silhouette,
    geometric_summary,
    knn_purity,
    saturated_pair_share,
    weakest_soft_members,
    membership_confidence,
    model_fit_metrics,
    require_applicable,
    soft_membership_summary,
)


def _three_blobs():
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.3, size=(30, 2)),
            rng.normal(loc=[5, 5], scale=0.3, size=(30, 2)),
            rng.normal(loc=[0, 5], scale=0.3, size=(30, 2)),
        ]
    )


def test_every_evaluation_names_only_registered_methods():
    for name, spec in EVALUATIONS.items():
        assert spec.methods <= set(CLUSTERING_METHODS), name


def test_require_applicable_accepts_a_listed_method():
    require_applicable("model_fit_metrics", "kmeans")
    require_applicable("geometric_metrics", "agglomerative")


def test_require_applicable_rejects_an_unlisted_method():
    with pytest.raises(ValueError, match="'agglomerative'"):
        require_applicable("model_fit_metrics", "agglomerative")


def test_require_applicable_rejects_an_unknown_evaluation():
    with pytest.raises(ValueError, match="valutazione sconosciuta"):
        require_applicable("silhouete", "kmeans")


def test_model_fit_metrics_kmeans_returns_the_inertia():
    X = _three_blobs()
    params = {"n_clusters": 3, "random_state": 0, "n_init": 10}
    labels = KMeans(**params).fit_predict(X)

    metrics = model_fit_metrics("kmeans", X, params, labels)

    assert metrics == {"inertia": pytest.approx(KMeans(**params).fit(X).inertia_)}


def test_model_fit_metrics_gmm_returns_bic_and_aic():
    X = _three_blobs()
    params = {"n_components": 3, "covariance_type": "full", "random_state": 0}
    labels = GaussianMixture(**params).fit_predict(X)

    metrics = model_fit_metrics("gmm", X, params, labels)

    fitted = GaussianMixture(**params).fit(X)
    assert metrics == {"bic": pytest.approx(fitted.bic(X)), "aic": pytest.approx(fitted.aic(X))}


def test_model_fit_metrics_hdbscan_reads_noise_and_cluster_count_from_labels():
    labels = np.array([0, 0, 1, 1, -1, -1, -1, 2])

    metrics = model_fit_metrics("hdbscan", np.zeros((8, 2)), {}, labels)

    assert metrics == {"noise_fraction": 3 / 8, "n_clusters_found": 3.0}


def test_model_fit_metrics_refuses_a_refit_that_does_not_reproduce_the_labels():
    X = _three_blobs()
    params = {"n_clusters": 3, "random_state": 0, "n_init": 10}
    other_labels = np.arange(len(X)) % 3  # not what KMeans produces on these blobs

    with pytest.raises(ValueError, match="does not reproduce the stored labels"):
        model_fit_metrics("kmeans", X, params, other_labels)


def test_model_fit_metrics_refuses_a_method_without_a_model_statistic():
    with pytest.raises(ValueError, match="'spectral'"):
        model_fit_metrics("spectral", np.zeros((4, 2)), {}, np.zeros(4, dtype=int))


# --- per_cluster_silhouette -------------------------------------------------


def test_per_cluster_silhouette_micro_and_macro_differ_on_unbalanced_clusters():
    from src.analysis.clustering_evaluation import per_cluster_silhouette

    rng = np.random.default_rng(0)
    big = rng.normal(loc=[0, 0], scale=0.3, size=(200, 2))
    small_overlapping = rng.normal(loc=[0.6, 0], scale=0.3, size=(20, 2))  # touches the big cluster
    X = np.vstack([big, small_overlapping])
    labels = np.array([0] * 200 + [1] * 20)

    breakdown = per_cluster_silhouette(X, labels, combo_params={})

    assert breakdown.clusters["n"].tolist() == [200, 20]
    assert breakdown.minimum == breakdown.clusters["silhouette_mean"].min()
    assert breakdown.micro != pytest.approx(breakdown.macro)  # sklearn's mean is dominated by the big cluster
    assert breakdown.micro == pytest.approx(silhouette_score(X, labels))
    assert breakdown.clusters.loc[1, "share_negative"] > breakdown.clusters.loc[0, "share_negative"]


def test_per_cluster_silhouette_excludes_noise():
    from src.analysis.clustering_evaluation import per_cluster_silhouette

    X = _three_blobs()
    labels = np.repeat([0, 1, 2], 30)
    labels[:5] = -1

    breakdown = per_cluster_silhouette(X, labels, combo_params={})

    assert breakdown.clusters["n"].sum() == len(X) - 5


def test_per_cluster_silhouette_refuses_a_non_euclidean_run():
    from src.analysis.clustering_evaluation import per_cluster_silhouette

    with pytest.raises(ValueError, match="metric='dice'"):
        per_cluster_silhouette(_three_blobs(), np.repeat([0, 1, 2], 30), combo_params={"metric": "dice"})


# --- knn_purity -------------------------------------------------------------


def _saturated_dice_distances(n_groups=3, per_group=40, shared=6, own=40):
    """Binary lesion-like masks: inside a group every mask shares `shared` voxels (so dice < 1), across
    groups nothing is shared (dice exactly 1). Most pairs are therefore at distance 1, like the real
    lesion matrices (84% of pairs)."""
    from src.analysis.distances import pairwise_distance

    rng = np.random.default_rng(0)
    n_voxels = n_groups * (shared + per_group * own)
    X = np.zeros((n_groups * per_group, n_voxels), dtype=np.uint8)
    labels = np.repeat(np.arange(n_groups), per_group)
    for group in range(n_groups):
        base = group * (shared + per_group * own)
        X[labels == group, base : base + shared] = 1
        for row, subject in enumerate(np.flatnonzero(labels == group)):
            X[subject, base + shared + row * own : base + shared + (row + 1) * own] = 1
    return pairwise_distance(X, "dice"), labels


def test_knn_purity_sees_the_structure_a_saturated_dice_hides_from_the_silhouette():
    """Regression for the adp silhouette: with most pairs at distance exactly 1 the silhouette of a
    perfect partition collapses towards 0, while the neighbourhood purity is 1."""
    from src.analysis.clustering_evaluation import knn_purity

    distances, labels = _saturated_dice_distances()

    assert (distances[np.triu_indices(len(labels), 1)] == 1.0).mean() > 0.6
    assert silhouette_score(distances, labels, metric="precomputed") < 0.15
    result = knn_purity(distances, labels, k=10)
    assert result.purity == pytest.approx(1.0)
    assert result.chance == pytest.approx(39 / 119)


def test_knn_purity_random_labels_sit_at_chance():
    from src.analysis.clustering_evaluation import knn_purity

    distances, labels = _saturated_dice_distances()
    shuffled = np.random.default_rng(3).permutation(labels)

    result = knn_purity(distances, shuffled, k=10)

    assert abs(result.purity - result.chance) < 0.1


def test_knn_purity_ties_are_resolved_by_expectation_not_by_position():
    """Every subject has the same distance to all others: the k neighbours are a pure tie, so the
    purity must be the share of same-label candidates (2 of the other 5 -> 2/5), whatever the row order."""
    from src.analysis.clustering_evaluation import knn_purity

    labels = np.array([0, 0, 0, 1, 1, 1])
    distances = np.ones((6, 6)) - np.eye(6)
    order = [3, 0, 4, 1, 5, 2]

    result = knn_purity(distances, labels, k=2)
    reordered = knn_purity(distances[order][:, order], labels[order], k=2)

    assert result.purity == pytest.approx(2 / 5)
    assert reordered.purity == pytest.approx(result.purity)
    assert result.tied_share == 1.0


def test_knn_purity_marks_clusters_with_k_or_fewer_members_as_not_evaluable():
    from src.analysis.clustering_evaluation import knn_purity

    rng = np.random.default_rng(0)
    points = np.vstack([rng.normal(0, 0.1, (30, 2)), rng.normal(5, 0.1, (3, 2))])
    labels = np.array([0] * 30 + [1] * 3)
    distances = np.linalg.norm(points[:, None] - points[None], axis=2)

    result = knn_purity(distances, labels, k=5)

    assert not result.clusters.loc[1, "evaluable"]
    assert result.clusters.loc[1, "max_possible"] == pytest.approx(2 / 5)
    assert result.n_not_evaluable == 3
    assert result.purity == pytest.approx(result.clusters.loc[0, "purity"])


def test_knn_purity_rejects_bad_input():
    from src.analysis.clustering_evaluation import knn_purity

    distances, labels = _saturated_dice_distances(per_group=10)
    with pytest.raises(ValueError, match="noise"):
        knn_purity(distances, np.where(np.arange(len(labels)) == 0, -1, labels), k=3)
    with pytest.raises(ValueError, match="k must be in"):
        knn_purity(distances, labels, k=len(labels))
    with pytest.raises(ValueError, match=r"\(30, 30\)"):
        knn_purity(distances[:20, :20], labels, k=3)
    with pytest.raises(ValueError, match="at least 2 clusters"):
        knn_purity(distances, np.zeros(len(labels), dtype=int), k=3)
    with pytest.raises(ValueError, match="lower k"):
        knn_purity(distances, labels, k=15)


# --- noise_warning -----------------------------------------------------------


def test_noise_warning_is_silent_up_to_the_threshold_and_names_the_run_above_it():
    from src.analysis.clustering_evaluation import noise_warning

    assert noise_warning("run_a", 0.004, 0.10) is None
    assert noise_warning("run_a", 0.10, 0.10) is None  # the threshold itself is not above it
    message = noise_warning("hdbscan_mcs200", 0.274, 0.10)
    assert message is not None and "hdbscan_mcs200" in message and "27,4%" in message


def test_noise_warning_rejects_values_outside_the_unit_interval():
    from src.analysis.clustering_evaluation import noise_warning

    with pytest.raises(ValueError, match="noise_fraction"):
        noise_warning("run_a", 27.4, 0.10)  # a percentage passed as a fraction
    with pytest.raises(ValueError, match="threshold"):
        noise_warning("run_a", 0.2, 10)


def test_adp_is_scored_by_knn_purity_and_not_by_the_euclidean_geometric_metrics():
    require_applicable("knn_purity", "adp")
    with pytest.raises(ValueError, match="'adp'"):
        require_applicable("geometric_metrics", "adp")
    with pytest.raises(ValueError, match="'kmeans'"):
        require_applicable("knn_purity", "kmeans")


# --- distance_matrix_silhouette / saturated_pair_share -----------------------


def test_distance_matrix_silhouette_matches_the_euclidean_breakdown_on_euclidean_distances():
    from sklearn.metrics import pairwise_distances

    from src.analysis.clustering_evaluation import distance_matrix_silhouette, per_cluster_silhouette

    X = _three_blobs()
    labels = np.repeat([0, 1, 2], 30)
    expected = per_cluster_silhouette(X, labels, {"n_clusters": 3})
    result = distance_matrix_silhouette(pairwise_distances(X), labels)

    assert result.micro == pytest.approx(expected.micro)
    assert result.macro == pytest.approx(expected.macro)
    assert result.minimum == pytest.approx(expected.minimum)
    pd.testing.assert_frame_equal(result.clusters, expected.clusters)


def test_distance_matrix_silhouette_is_flattened_by_a_saturated_distance():
    """Two clusters whose members are each close to 5 own-cluster neighbours and at distance 1 from
    everyone else: the neighbourhoods are perfect, the silhouette is still near 0 (the lesion case)."""
    from src.analysis.clustering_evaluation import distance_matrix_silhouette, saturated_pair_share

    n_per_cluster = 100
    labels = np.repeat([0, 1], n_per_cluster)
    distances = np.ones((2 * n_per_cluster, 2 * n_per_cluster))
    for start in (0, n_per_cluster):
        for i in range(n_per_cluster):
            for offset in range(1, 6):
                j = start + (i + offset) % n_per_cluster
                distances[start + i, j] = distances[j, start + i] = 0.6
    np.fill_diagonal(distances, 0.0)

    assert distance_matrix_silhouette(distances, labels).micro < 0.1
    assert saturated_pair_share(distances) > 0.9


def test_distance_matrix_silhouette_rejects_bad_input():
    from src.analysis.clustering_evaluation import distance_matrix_silhouette

    distances = np.ones((4, 4)) - np.eye(4)
    with pytest.raises(ValueError, match="noise"):
        distance_matrix_silhouette(distances, np.array([0, 0, 1, -1]))
    with pytest.raises(ValueError, match="to match labels"):
        distance_matrix_silhouette(distances, np.array([0, 0, 1]))
    with pytest.raises(ValueError, match="1 cluster"):
        distance_matrix_silhouette(distances, np.zeros(4, dtype=int))
    with pytest.raises(ValueError, match="NaN or inf"):
        distance_matrix_silhouette(np.full((4, 4), np.nan), np.array([0, 0, 1, 1]))


def test_saturated_pair_share_counts_pairs_not_the_zero_diagonal():
    from src.analysis.clustering_evaluation import saturated_pair_share

    distances = np.array([[0, 1, 1, 0.4], [1, 0, 1 - 1e-12, 1], [1, 1 - 1e-12, 0, 0.5], [0.4, 1, 0.5, 0]])
    assert saturated_pair_share(distances) == pytest.approx(4 / 6)  # pairs (0,1) (0,2) (1,2) (1,3); (1,2) within tolerance
    with pytest.raises(ValueError, match="square"):
        saturated_pair_share(np.ones((3, 4)))
    with pytest.raises(ValueError, match="at least 2"):
        saturated_pair_share(np.zeros((1, 1)))


# --- membership_confidence --------------------------------------------------

_HDBSCAN_PARAMS = {"min_cluster_size": 15, "min_samples": 5}


def _blobs_of_mixed_density():
    """Two tight blobs and a loose one, plus a few far outliers: HDBSCAN finds three clusters,
    some noise, and probabilities below 1 inside the loose cluster."""
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.2, size=(60, 2)),
            rng.normal(loc=[8, 0], scale=1.0, size=(60, 2)),
            rng.normal(loc=[0, 8], scale=0.2, size=(60, 2)),
            [[30.0, 30.0], [-30.0, 30.0], [30.0, -30.0]],
        ]
    )


def _fit_hdbscan(X):
    fitted = HDBSCAN(**_HDBSCAN_PARAMS).fit(X)
    return fitted.labels_, fitted.probabilities_


def test_membership_confidence_summarises_hdbscans_own_probabilities_per_cluster():
    X = _blobs_of_mixed_density()
    labels, probabilities = _fit_hdbscan(X)
    assert (labels == -1).any() and len(set(labels) - {-1}) == 3  # the fixture is what the test assumes

    result = membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, labels, threshold=0.7)

    for cluster, row in result.clusters.iterrows():
        p = probabilities[labels == cluster]
        assert row["n"] == len(p)
        assert row["probability_mean"] == pytest.approx(p.mean())
        assert row["share_below_threshold"] == pytest.approx((p < 0.7).mean())
    assert result.clusters["share_below_threshold"].max() > 0  # the loose cluster has weak members
    assert result.n_noise == int((labels == -1).sum())
    assert result.n_confident == int((probabilities[labels != -1] >= 0.7).sum())


def test_membership_confidence_refuses_a_refit_that_does_not_reproduce_the_labels():
    X = _blobs_of_mixed_density()
    labels, _ = _fit_hdbscan(X)

    with pytest.raises(ValueError, match="does not reproduce the stored labels"):
        membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, np.roll(labels, 1), threshold=0.5)


def test_membership_confidence_refuses_a_method_without_membership_probabilities():
    with pytest.raises(ValueError, match="'kmeans'"):
        membership_confidence("kmeans", np.zeros((4, 2)), {}, np.zeros(4, dtype=int), threshold=0.5)


@pytest.mark.parametrize("threshold", [0.0, -0.1, 1.5])
def test_membership_confidence_rejects_a_threshold_outside_zero_one(threshold):
    X = _blobs_of_mixed_density()
    labels, _ = _fit_hdbscan(X)

    with pytest.raises(ValueError, match="threshold must be in"):
        membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, labels, threshold=threshold)


def test_membership_confidence_refuses_a_run_that_is_all_noise():
    X = _blobs_of_mixed_density()

    with pytest.raises(ValueError, match="every subject is noise"):
        membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, np.full(len(X), -1), threshold=0.5)


def test_membership_confidence_is_registered_for_hdbscan_only():
    require_applicable("membership_confidence", "hdbscan")
    with pytest.raises(ValueError, match="'agglomerative'"):
        require_applicable("membership_confidence", "agglomerative")


# --- soft_membership_summary --------------------------------------------------


def _soft_fixture():
    labels = np.array([0, 0, 0, 1, 1, -1])
    membership = np.array(
        [
            [0.9, 0.05],
            [0.7, 0.20],
            [0.4, 0.30],
            [0.1, 0.8],
            [0.2, 0.6],
            [0.1, 0.1],
        ]
    )
    return labels, membership


def test_soft_membership_summary_reads_each_cluster_from_its_own_column_and_names_the_nearest_other():
    labels, membership = _soft_fixture()

    result = soft_membership_summary(labels, membership, threshold=0.5)

    assert result.clusters.loc[0, "n"] == 3
    assert result.clusters.loc[0, "own_mean"] == pytest.approx((0.9 + 0.7 + 0.4) / 3)
    assert result.clusters.loc[0, "share_below_threshold"] == pytest.approx(1 / 3)
    assert result.clusters.loc[0, "top_other"] == 1
    assert result.clusters.loc[0, "top_other_mean"] == pytest.approx((0.05 + 0.20 + 0.30) / 3)
    assert result.clusters.loc[1, "own_mean"] == pytest.approx(0.7)
    assert result.clusters.loc[1, "top_other"] == 0
    assert result.n_noise == 1


def test_soft_membership_summary_mean_vectors_have_a_noise_row_and_the_own_means_on_the_diagonal():
    labels, membership = _soft_fixture()

    result = soft_membership_summary(labels, membership, threshold=0.5)

    assert result.mean_vectors.index.tolist() == [0, 1, -1]
    np.testing.assert_allclose(np.diag(result.mean_vectors.loc[[0, 1]].to_numpy()), result.clusters["own_mean"].to_numpy())
    np.testing.assert_allclose(result.mean_vectors.loc[-1].to_numpy(), [0.1, 0.1])  # the noise is not renormalised


def test_soft_membership_summary_rejects_inconsistent_input():
    labels, membership = _soft_fixture()

    with pytest.raises(ValueError, match="threshold must be in"):
        soft_membership_summary(labels, membership, threshold=0.0)
    with pytest.raises(ValueError, match="every subject is noise"):
        soft_membership_summary(np.full(6, -1), membership, threshold=0.5)
    with pytest.raises(ValueError, match="0..k-1"):
        soft_membership_summary(np.array([0, 0, 0, 2, 2, -1]), membership, threshold=0.5)
    with pytest.raises(ValueError, match=r"\(6, 2\)"):
        soft_membership_summary(labels, membership[:, :1], threshold=0.5)


def test_soft_membership_is_registered_for_hdbscan_soft_only():
    require_applicable("soft_membership", "hdbscan_soft")
    with pytest.raises(ValueError, match="'hdbscan'"):
        require_applicable("soft_membership", "hdbscan")
    require_applicable("model_fit_metrics", "hdbscan_soft")


def _blob_labels():
    return np.repeat([0, 1, 2], 30)


def test_geometric_summary_matches_sklearn_on_well_separated_blobs():
    X, labels = _three_blobs(), _blob_labels()

    summary = geometric_summary(X, labels, {"n_clusters": 3})

    assert summary.silhouette == pytest.approx(silhouette_score(X, labels))
    assert summary.calinski_harabasz == pytest.approx(calinski_harabasz_score(X, labels))
    assert summary.davies_bouldin == pytest.approx(davies_bouldin_score(X, labels))
    assert (summary.n_subjects, summary.n_components, summary.n_clusters) == (90, 2, 3)
    assert summary.largest_cluster_share == pytest.approx(1 / 3) and summary.noise_fraction == 0.0
    assert summary.silhouette_min <= summary.silhouette and summary.dunn > 0
    assert summary.silhouette_macro == pytest.approx(summary.clusters["silhouette_mean"].mean())
    assert list(summary.clusters["n"]) == [30, 30, 30]


def test_geometric_summary_leaves_noise_out_of_the_indices_but_not_out_of_the_shares():
    X, labels = _three_blobs(), _blob_labels().copy()
    labels[:9] = -1  # 9 of 90 subjects are noise

    summary = geometric_summary(X, labels, {})

    kept = labels != -1
    assert summary.silhouette == pytest.approx(silhouette_score(X[kept], labels[kept]))
    assert summary.noise_fraction == pytest.approx(0.1)
    assert summary.n_clusters == 3
    assert summary.largest_cluster_share == pytest.approx(30 / 90)  # over all subjects, noise included


def test_geometric_summary_needs_two_clusters_once_noise_is_left_out():
    X = _three_blobs()
    labels = np.where(np.arange(90) < 30, 0, -1)

    with pytest.raises(ValueError, match="at least 2 clusters"):
        geometric_summary(X, labels, {})


def test_geometric_summary_refuses_a_run_clustered_under_another_metric():
    with pytest.raises(ValueError, match="Euclidean"):
        geometric_summary(_three_blobs(), _blob_labels(), {"metric": "dice"})


def test_geometric_summary_rejects_labels_that_do_not_match_the_rows():
    with pytest.raises(ValueError, match="one row per label"):
        geometric_summary(_three_blobs(), _blob_labels()[:-1], {})


def test_geometric_summary_raises_when_every_cluster_is_a_single_subject():
    X = np.array([[0.0, 0.0], [1.0, 0.0], [5.0, 5.0]])

    with pytest.raises(ValueError):
        geometric_summary(X, np.array([0, 1, 2]), {})


def _blob_distances():
    X, labels = _three_blobs(), _blob_labels()
    distances = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    return distances, labels


def test_adp_summary_matches_its_parts_on_the_clustered_subjects_only():
    distances, labels = _blob_distances()
    labels = labels.copy()
    labels[:6] = -1  # noise: out of the distance matrix the indices are computed on
    non_empty = np.ones(90, dtype=bool)

    summary = adp_summary(distances, non_empty, labels, k=5)

    kept = labels != -1
    expected_distances = distances[np.ix_(kept, kept)]
    assert summary.purity.purity == pytest.approx(knn_purity(expected_distances, labels[kept], 5).purity)
    assert summary.silhouette.micro == pytest.approx(distance_matrix_silhouette(expected_distances, labels[kept]).micro)
    assert summary.pairs_at_distance_1 == pytest.approx(saturated_pair_share(expected_distances))
    assert (summary.n_subjects, summary.n_clustered, summary.k) == (90, 84, 5)
    assert summary.noise_fraction == pytest.approx(6 / 90)
    assert list(summary.clusters.columns) == [
        "n", "purity", "chance", "max_possible", "evaluable", "silhouette_mean", "share_negative"
    ]


def test_adp_summary_leaves_out_the_subjects_with_an_empty_row_labelled_noise():
    distances, labels = _blob_distances()
    non_empty = np.ones(90, dtype=bool)
    non_empty[[0, 40]] = False  # their distance is undefined: not in the matrix, labelled -1 by adp
    labels = labels.copy()
    labels[[0, 40]] = -1
    kept = np.flatnonzero(non_empty)

    summary = adp_summary(distances[np.ix_(kept, kept)], non_empty, labels, k=5)

    assert summary.n_clustered == 88 and summary.n_subjects == 90
    assert summary.noise_fraction == pytest.approx(2 / 90)


def test_adp_summary_refuses_an_empty_row_subject_that_has_a_cluster():
    distances, labels = _blob_distances()
    non_empty = np.ones(90, dtype=bool)
    non_empty[0] = False  # but labels[0] is cluster 0, which adp never produces
    kept = np.flatnonzero(non_empty)

    with pytest.raises(ValueError, match="not an adp run"):
        adp_summary(distances[np.ix_(kept, kept)], non_empty, labels, k=5)


def test_adp_summary_refuses_distances_that_do_not_match_the_mask():
    distances, labels = _blob_distances()

    with pytest.raises(ValueError, match="do not match"):
        adp_summary(distances[:80, :80], np.ones(90, dtype=bool), labels, k=5)


def _soft_membership():
    labels = np.array([0, 0, 1, 1, -1, 0])
    membership = np.array([
        [0.90, 0.05],
        [0.40, 0.35],  # contested between the two clusters
        [0.10, 0.80],
        [0.20, 0.30],
        [0.05, 0.05],  # noise: no own cluster
        [0.60, 0.10],
    ])
    return labels, membership


def test_weakest_soft_members_lists_the_lowest_own_probability_first_with_the_other_cluster():
    labels, membership = _soft_membership()

    weakest = weakest_soft_members(labels, membership, 2)

    assert list(weakest.index) == [3, 1]  # row positions in labels; the noise subject (row 4) is never listed
    assert list(weakest["cluster"]) == [1, 0]
    assert list(weakest["own_membership"]) == pytest.approx([0.30, 0.40])
    assert list(weakest["best_other"]) == [0, 1]
    assert list(weakest["best_other_probability"]) == pytest.approx([0.20, 0.35])


def test_weakest_soft_members_has_no_other_cluster_when_there_is_only_one():
    weakest = weakest_soft_members(np.array([0, 0, -1]), np.array([[0.9], [0.5], [0.1]]), 5)

    assert list(weakest.index) == [1, 0]
    assert weakest["best_other"].isna().all() and weakest["best_other_probability"].isna().all()


def test_weakest_soft_members_rejects_bad_input():
    labels, membership = _soft_membership()
    with pytest.raises(ValueError, match="at least 1"):
        weakest_soft_members(labels, membership, 0)
    with pytest.raises(ValueError, match="every subject is noise"):
        weakest_soft_members(np.full(6, -1), membership, 3)
    with pytest.raises(ValueError, match="one row per label"):
        weakest_soft_members(labels, membership[:-1], 3)
