"""Unit tests for src/analysis/clustering_tuning.py."""

import numpy as np
import pytest

from src.analysis.clustering_tuning import (
    METHOD_METRIC_COLUMNS,
    STANDALONE_DIAGNOSTIC_METHODS,
    compute_clustering_metrics,
    compute_dendrogram_linkage,
    compute_eigengap,
    compute_k_distance,
    compute_silhouette_samples,
    run_clustering_tuning_sweep,
)


def _three_blobs():
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.3, size=(15, 2)),
            rng.normal(loc=[5, 5], scale=0.3, size=(15, 2)),
            rng.normal(loc=[0, 5], scale=0.3, size=(15, 2)),
        ]
    )


def test_compute_clustering_metrics_on_well_separated_clusters():
    X = _three_blobs()
    labels = np.array([0] * 15 + [1] * 15 + [2] * 15)

    metrics = compute_clustering_metrics(X, labels)

    assert metrics["silhouette"] > 0.8  # well-separated blobs
    assert metrics["calinski_harabasz"] > 0
    assert metrics["davies_bouldin"] > 0
    assert metrics["noise_fraction"] == 0.0


def test_compute_clustering_metrics_excludes_noise():
    X = _three_blobs()
    labels = np.array([0] * 15 + [1] * 15 + [-1] * 15)

    metrics = compute_clustering_metrics(X, labels)

    assert metrics["noise_fraction"] == pytest.approx(15 / 45)
    assert not np.isnan(metrics["silhouette"])  # 2 non-noise clusters remain, still computable


def test_compute_clustering_metrics_returns_nan_for_degenerate_single_cluster():
    X = _three_blobs()
    labels = np.zeros(45, dtype=int)  # everything in one cluster

    metrics = compute_clustering_metrics(X, labels)

    assert np.isnan(metrics["silhouette"])
    assert np.isnan(metrics["calinski_harabasz"])
    assert np.isnan(metrics["davies_bouldin"])
    assert metrics["noise_fraction"] == 0.0


def test_compute_clustering_metrics_returns_nan_when_all_noise():
    X = _three_blobs()
    labels = np.full(45, -1)

    metrics = compute_clustering_metrics(X, labels)

    assert np.isnan(metrics["silhouette"])
    assert metrics["noise_fraction"] == 1.0


def test_compute_silhouette_samples_mean_matches_aggregate_silhouette():
    X = _three_blobs()
    labels = np.array([0] * 15 + [1] * 15 + [2] * 15)

    sample_labels, sample_values = compute_silhouette_samples(X, labels)

    assert len(sample_labels) == len(sample_values) == 45
    assert np.mean(sample_values) == pytest.approx(compute_clustering_metrics(X, labels)["silhouette"])


def test_compute_silhouette_samples_excludes_noise():
    X = _three_blobs()
    labels = np.array([0] * 15 + [1] * 15 + [-1] * 15)

    sample_labels, sample_values = compute_silhouette_samples(X, labels)

    assert len(sample_labels) == len(sample_values) == 30
    assert -1 not in sample_labels


def test_compute_silhouette_samples_raises_on_degenerate_single_cluster():
    X = _three_blobs()
    labels = np.zeros(45, dtype=int)

    with pytest.raises(ValueError, match="non-noise cluster"):
        compute_silhouette_samples(X, labels)


def test_compute_silhouette_samples_raises_when_all_noise():
    X = _three_blobs()
    labels = np.full(45, -1)

    with pytest.raises(ValueError, match="non-noise cluster"):
        compute_silhouette_samples(X, labels)


def test_run_clustering_tuning_sweep_kmeans_includes_inertia():
    X = _three_blobs()
    df = run_clustering_tuning_sweep("kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3, 4]})

    assert list(df["n_clusters"]) == [2, 3, 4]
    assert set(METHOD_METRIC_COLUMNS["kmeans"]) <= set(df.columns)
    assert (df["inertia"] > 0).all()
    # inertia decreases monotonically as n_clusters grows, on well-separated data
    assert df.sort_values("n_clusters")["inertia"].is_monotonic_decreasing


def test_run_clustering_tuning_sweep_gmm_includes_bic_aic():
    X = _three_blobs()
    df = run_clustering_tuning_sweep("gmm", X, {"random_state": 0}, {"n_components": [2, 3, 4]})

    assert set(METHOD_METRIC_COLUMNS["gmm"]) <= set(df.columns)
    assert df["bic"].notna().all()
    assert df["aic"].notna().all()


def test_run_clustering_tuning_sweep_dbscan_noise_fraction_varies_with_eps():
    X = _three_blobs()
    df = run_clustering_tuning_sweep("dbscan", X, {"min_samples": 3}, {"eps": [0.05, 2.0]})

    # eps=0.05 is far too small for this data's scale -> mostly/all noise;
    # eps=2.0 comfortably covers each blob -> no noise
    tiny_eps_row = df[df["eps"] == 0.05].iloc[0]
    large_eps_row = df[df["eps"] == 2.0].iloc[0]
    assert tiny_eps_row["noise_fraction"] > large_eps_row["noise_fraction"]
    assert large_eps_row["noise_fraction"] == 0.0


def test_run_clustering_tuning_sweep_unknown_method_raises():
    X = _three_blobs()
    with pytest.raises(ValueError, match="unknown clustering method"):
        run_clustering_tuning_sweep("bogus", X, {}, {"n_clusters": [2]})


def test_compute_dendrogram_linkage_shape():
    X = _three_blobs()
    linkage_matrix = compute_dendrogram_linkage(X, {"linkage": "ward"})

    # scipy linkage matrix: n_samples - 1 merges, 4 columns (child1, child2, distance, count)
    assert linkage_matrix.shape == (44, 4)
    assert (linkage_matrix[:, 2] >= 0).all()  # merge distances are non-negative
    assert linkage_matrix[-1, 3] == 45  # final merge covers every subject


def test_compute_eigengap_finds_gap_matching_known_cluster_count():
    X = _three_blobs()
    eigenvalues = compute_eigengap(X, {"affinity": "nearest_neighbors", "n_neighbors": 5}, max_k=10)

    assert len(eigenvalues) == 11  # max_k + 1 (subset_by_index is inclusive)
    assert (np.diff(eigenvalues) >= -1e-9).all()  # sorted ascending
    # 3 well-separated, internally-connected blobs -> the graph Laplacian has
    # multiplicity-3 near-zero eigenvalue (one per connected component), then
    # a clear jump - this structural property holds regardless of whether
    # that particular gap also happens to be the single largest one further
    # out in the spectrum (which depends on how many eigenvalues/max_k are
    # considered, and isn't guaranteed on a sparse nearest-neighbors graph).
    assert eigenvalues[2] < 1e-6
    assert eigenvalues[3] > 0.05


def test_compute_eigengap_raises_on_unsupported_affinity():
    X = _three_blobs()
    with pytest.raises(ValueError, match="nearest_neighbors.*rbf"):
        compute_eigengap(X, {"affinity": "precomputed"})


def test_compute_k_distance_sorted_ascending():
    X = _three_blobs()
    distances = compute_k_distance(X, min_samples=3)

    assert distances.shape == (45,)
    assert (np.diff(distances) >= 0).all()
    assert (distances > 0).all()


def test_standalone_diagnostic_methods_covers_exactly_agglomerative_spectral_dbscan():
    assert STANDALONE_DIAGNOSTIC_METHODS == {"agglomerative", "spectral", "dbscan"}
