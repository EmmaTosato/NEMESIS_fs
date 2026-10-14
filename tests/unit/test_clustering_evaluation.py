"""Unit tests for src/analysis/clustering_evaluation.py."""

import numpy as np
import pytest
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_evaluation import EVALUATIONS, model_fit_metrics, require_applicable


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
    with pytest.raises(ValueError, match="unknown evaluation"):
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


# --- null_reference_silhouette ---------------------------------------------


def test_null_reference_well_separated_blobs_beat_the_null_by_a_wide_margin():
    from src.analysis.clustering_evaluation import null_reference_silhouette

    X = _three_blobs()
    params = {"n_clusters": 3, "n_init": 10, "random_state": 0}
    labels = KMeans(**params).fit_predict(X)

    reference = null_reference_silhouette("kmeans", X, labels, params, n_null=10)

    assert reference.observed > 0.8
    assert reference.margin > 0.3
    assert reference.empirical_p == pytest.approx(1 / 11)  # no null fit reaches the observed value


def test_null_reference_one_gaussian_blob_is_not_distinguished_from_the_null():
    """A single Gaussian cut into k=3 by kmeans has a clearly positive silhouette, but no more than
    the null: the margin is what separates 'structure' from 'a partition was forced'."""
    from src.analysis.clustering_evaluation import null_reference_silhouette

    X = np.random.default_rng(1).normal(size=(300, 2)).astype(np.float32)
    params = {"n_clusters": 3, "n_init": 10, "random_state": 0}
    labels = KMeans(**params).fit_predict(X)

    reference = null_reference_silhouette("kmeans", X, labels, params, n_null=20)

    assert reference.observed > 0.3  # the absolute value alone looks like structure
    assert abs(reference.margin) < 3 * reference.null_sd
    assert reference.empirical_p > 0.05


@pytest.mark.parametrize("null", ["gaussian", "permute"])
def test_null_reference_is_reproducible_for_a_seed(null):
    from src.analysis.clustering_evaluation import null_reference_silhouette

    X = _three_blobs()
    params = {"n_clusters": 3, "n_init": 3, "random_state": 0}
    labels = KMeans(**params).fit_predict(X)

    first = null_reference_silhouette("kmeans", X, labels, params, null=null, n_null=4, seed=5)
    second = null_reference_silhouette("kmeans", X, labels, params, null=null, n_null=4, seed=5)

    np.testing.assert_array_equal(first.null_values, second.null_values)


def test_null_sample_permute_keeps_each_column_marginal_and_gaussian_keeps_the_dtype():
    from src.analysis.clustering_evaluation import _null_sample

    X = _three_blobs().astype(np.float32)
    rng = np.random.default_rng(0)

    permuted = _null_sample(X, "permute", rng)
    gaussian = _null_sample(X, "gaussian", rng)

    for column in range(X.shape[1]):
        np.testing.assert_array_equal(np.sort(permuted[:, column]), np.sort(X[:, column]))
    assert gaussian.dtype == X.dtype and gaussian.shape == X.shape


def test_null_reference_rejects_adp_unknown_null_and_a_non_euclidean_run():
    from src.analysis.clustering_evaluation import null_reference_silhouette

    X, labels = _three_blobs(), np.repeat([0, 1, 2], 30)
    with pytest.raises(ValueError, match="'adp'"):
        null_reference_silhouette("adp", X, labels, {"metric": "dice", "Z": 2.5, "maxk": 100})
    with pytest.raises(ValueError, match="unknown null"):
        null_reference_silhouette("kmeans", X, labels, {"n_clusters": 3}, null="uniform")
    with pytest.raises(ValueError, match="metric='dice'"):
        null_reference_silhouette("agglomerative", X, labels, {"n_clusters": 3, "metric": "dice"})


def test_null_reference_raises_when_every_null_fit_is_degenerate():
    from src.analysis.clustering_evaluation import null_reference_silhouette

    X = _three_blobs()
    labels = np.repeat([0, 1, 2], 30)
    # min_cluster_size larger than the sample: hdbscan labels everything as noise, on every null fit
    with pytest.raises(ValueError, match="no reference"):
        null_reference_silhouette("hdbscan", X, labels, {"min_cluster_size": 80, "min_samples": 80}, n_null=2)


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
    assert message is not None and "hdbscan_mcs200" in message and "27.4%" in message


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
