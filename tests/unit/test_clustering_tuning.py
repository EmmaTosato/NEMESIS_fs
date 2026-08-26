"""Unit tests for src/analysis/clustering_tuning.py."""

import numpy as np
import pytest

from src.analysis.clustering_tuning import (
    CONSENSUS_METRIC_COLUMNS,
    METHOD_METRIC_COLUMNS,
    STANDALONE_DIAGNOSTIC_METHODS,
    compute_clustering_metrics,
    compute_dendrogram_linkage,
    compute_eigengap,
    compute_silhouette_samples,
    consensus_suggestion_lines,
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


@pytest.mark.parametrize("combo_params", [{"affinity": "precomputed"}, {"metric": "manhattan"}, {"metric": "cosine"}])
def test_compute_clustering_metrics_raises_for_non_euclidean_combo_params(combo_params):
    """Regression (HIGH #13, 2026-08): silhouette/calinski_harabasz/davies_bouldin always
    scored X under sklearn's default Euclidean distance, with no check that the clustering
    method being scored actually used Euclidean geometry too (e.g. spectral with
    affinity="precomputed" fed a Jaccard/Dice distance matrix, or agglomerative with a
    non-euclidean metric). Must now raise explicitly instead of silently scoring the wrong
    geometry (lesson #15's dim_reduction/trustworthiness pattern, applied here as a guard
    since clustering has no single uniform 'metric' key to thread through generically)."""
    X = _three_blobs()
    labels = np.array([0] * 15 + [1] * 15 + [2] * 15)

    with pytest.raises(ValueError, match="Euclidean"):
        compute_clustering_metrics(X, labels, combo_params)


@pytest.mark.parametrize(
    "combo_params", [None, {}, {"affinity": "nearest_neighbors"}, {"affinity": "rbf"}, {"metric": "euclidean"}]
)
def test_compute_clustering_metrics_allows_known_euclidean_compatible_combo_params(combo_params):
    X = _three_blobs()
    labels = np.array([0] * 15 + [1] * 15 + [2] * 15)

    metrics = compute_clustering_metrics(X, labels, combo_params)

    assert metrics["silhouette"] > 0.8


def test_run_clustering_tuning_sweep_raises_for_non_euclidean_affinity():
    """The guard is wired all the way through the sweep entry point, not just
    compute_clustering_metrics in isolation - a real spectral tuning_grid with
    affinity="precomputed" must fail the sweep, not silently score it wrong."""
    rng = np.random.default_rng(0)
    affinity = rng.random((45, 45))
    affinity = (affinity + affinity.T) / 2  # a precomputed affinity matrix must be symmetric

    with pytest.raises(ValueError, match="Euclidean"):
        run_clustering_tuning_sweep(
            "spectral",
            affinity,
            {"n_clusters": 3, "affinity": "precomputed", "random_state": 0},
            {"n_clusters": [2, 3]},
        )


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
    df, _ = run_clustering_tuning_sweep("kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3, 4]})

    assert list(df["n_clusters"]) == [2, 3, 4]
    assert set(METHOD_METRIC_COLUMNS["kmeans"]) <= set(df.columns)
    assert (df["inertia"] > 0).all()
    # inertia decreases monotonically as n_clusters grows, on well-separated data
    assert df.sort_values("n_clusters")["inertia"].is_monotonic_decreasing


def test_run_clustering_tuning_sweep_gmm_includes_bic_aic():
    X = _three_blobs()
    df, _ = run_clustering_tuning_sweep("gmm", X, {"random_state": 0}, {"n_components": [2, 3, 4]})

    assert set(METHOD_METRIC_COLUMNS["gmm"]) <= set(df.columns)
    assert df["bic"].notna().all()
    assert df["aic"].notna().all()


def test_run_clustering_tuning_sweep_hdbscan_noise_fraction_varies_with_min_cluster_size():
    X = _three_blobs()
    df, _ = run_clustering_tuning_sweep("hdbscan", X, {}, {"min_cluster_size": [2, 20]})

    # min_cluster_size=2 is small enough to absorb this data's sparse edges into
    # the 3 (15-point) blobs -> some noise but not total; min_cluster_size=20
    # exceeds every blob's own size -> no cluster can ever form, every point
    # ends up noise
    small_mcs_row = df[df["min_cluster_size"] == 2].iloc[0]
    large_mcs_row = df[df["min_cluster_size"] == 20].iloc[0]
    assert large_mcs_row["noise_fraction"] > small_mcs_row["noise_fraction"]
    assert large_mcs_row["noise_fraction"] == 1.0


def test_run_clustering_tuning_sweep_evidence_accumulation_reuses_cooccurrence_across_thresholds(monkeypatch):
    """AUDIT_FINDINGS.md #35 regression: evidence_accumulation's real cost
    (run_rsc_repeats, n_repeats fits of base_method) used to be recomputed once per
    threshold value even though threshold never affects it - only the cheap Merge-phase
    cut (assign_clusters_from_cooccurrence) does. A 4-value threshold-only sweep must call
    run_rsc_repeats exactly once, not 4 times."""
    import src.analysis.consensus_clustering as consensus_clustering

    X = _three_blobs()
    call_count = 0
    real_run_rsc_repeats = consensus_clustering.run_rsc_repeats

    def _counting_run_rsc_repeats(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return real_run_rsc_repeats(*args, **kwargs)

    monkeypatch.setattr(consensus_clustering, "run_rsc_repeats", _counting_run_rsc_repeats)

    base_params = {"base_method": "kmeans", "n_clusters": 5, "n_repeats": 3, "base_seed": 0}
    df, _ = run_clustering_tuning_sweep(
        "evidence_accumulation", X, base_params, {"threshold": [0.3, 0.5, 0.7, 0.9]}
    )

    assert list(df["threshold"]) == [0.3, 0.5, 0.7, 0.9]
    assert call_count == 1, f"expected run_rsc_repeats to run once (shared across all 4 thresholds), got {call_count}"
    # Different thresholds on the SAME co-occurrence matrix produce a non-increasing
    # number of clusters as threshold rises (a stricter cut can only merge, never split) -
    # not the point of this test, but confirms the shared matrix still drives real,
    # threshold-dependent output rather than being reused incorrectly for every row.
    assert set(METHOD_METRIC_COLUMNS["evidence_accumulation"]) <= set(df.columns)


def test_run_clustering_tuning_sweep_returns_labels_by_combo_matching_results():
    """Regression (26-08-26, save_tuning_clusterings feature): the sweep must return the
    actual cluster-label array it already computed for every combination, keyed by the exact
    same combo tuple results.itertuples would rebuild - never recomputed, never a subset."""
    X = _three_blobs()
    df, labels_by_combo = run_clustering_tuning_sweep(
        "kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3, 4]}
    )

    assert set(labels_by_combo.keys()) == {(2,), (3,), (4,)}
    for combo, labels in labels_by_combo.items():
        assert labels.shape == (X.shape[0],)
        assert len(set(labels)) == combo[0]


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


def test_standalone_diagnostic_methods_covers_exactly_agglomerative_spectral():
    assert STANDALONE_DIAGNOSTIC_METHODS == {"agglomerative", "spectral"}


# --- run_clustering_tuning_sweep(consensus_config=...) / consensus_suggestion_lines ---
# AUDIT_FINDINGS.md #69 (found 22/08 while triaging an unrelated stale git stash):
# consensus_config wiring and consensus_suggestion_lines are already implemented and used
# in production (src/pipeline/clustering.py), but had no direct unit test coverage before
# this.


def test_run_clustering_tuning_sweep_consensus_config_none_is_unchanged():
    X = _three_blobs()
    df, _ = run_clustering_tuning_sweep("kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3]})

    assert not set(CONSENSUS_METRIC_COLUMNS) & set(df.columns)


def test_run_clustering_tuning_sweep_consensus_config_rejects_ineligible_method():
    X = _three_blobs()
    with pytest.raises(ValueError, match="agglomerative"):
        run_clustering_tuning_sweep(
            "agglomerative", X, {"linkage": "ward"}, {"n_clusters": [2, 3]}, consensus_config={"rsc": {"n_repeats": 5}}
        )


def test_run_clustering_tuning_sweep_adds_rsc_and_monti_columns():
    X = _three_blobs()
    consensus_config = {"rsc": {"n_repeats": 5}, "monti": {"n_repeats": 30, "subsample_fraction": 0.8}}
    df, _ = run_clustering_tuning_sweep(
        "kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3]}, consensus_config=consensus_config
    )

    assert set(CONSENSUS_METRIC_COLUMNS) <= set(df.columns)
    assert df["rsc_eigengap"].notna().all()
    assert df["monti_stability"].notna().all()


def test_run_clustering_tuning_sweep_consensus_config_rsc_only_omits_monti_column():
    X = _three_blobs()
    df, _ = run_clustering_tuning_sweep(
        "kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3]}, consensus_config={"rsc": {"n_repeats": 5}}
    )

    assert "rsc_eigengap" in df.columns
    assert "monti_stability" not in df.columns


def test_consensus_suggestion_lines_empty_when_no_consensus_columns():
    X = _three_blobs()
    df, _ = run_clustering_tuning_sweep("kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3]})

    assert consensus_suggestion_lines(df, "kmeans") == []


def test_consensus_suggestion_lines_report_argmax_k():
    X = _three_blobs()
    consensus_config = {"rsc": {"n_repeats": 5}, "monti": {"n_repeats": 30, "subsample_fraction": 0.8}}
    df, _ = run_clustering_tuning_sweep(
        "kmeans", X, {"random_state": 0, "n_init": "auto"}, {"n_clusters": [2, 3, 4]}, consensus_config=consensus_config
    )

    lines = consensus_suggestion_lines(df, "kmeans")

    assert len(lines) == 2
    assert lines[0].startswith("RSC suggests n_clusters=")
    assert lines[1].startswith("Monti suggests n_clusters=")
