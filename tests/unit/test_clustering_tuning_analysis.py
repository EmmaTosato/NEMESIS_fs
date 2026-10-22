"""Unit tests for src/analysis/clustering_tuning_analysis.py."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.clustering_tuning import compute_clustering_metrics_metric_aware
from src.analysis.dbcv import dbcv
from src.analysis.clustering_tuning_analysis import (
    ClusteringTuningRun,
    combo_key,
    cophenetic_table,
    dendrogram_jump,
    dbcv_curves_figures,
    density_metrics,
    jump_table,
    k_curves_figure,
    k_curves_file_name,
    k_curves_targets,
    run_axis_limits,
    linkage_agreement,
    load_clustering_tuning_run,
    recomputed_internal_metrics,
    silhouette_zoom_limits,
)


def _write_config(run_dir: Path, method: str, fine_tuning: bool = True) -> None:
    config = {"clustering_method": method, "input_path": "matrix_dir", "fine_tuning": fine_tuning}
    (run_dir / "config.md").write_text(f"# t\n\n## Config\n\n```json\n{json.dumps(config)}\n```\n")


def _write_run(run_dir: Path, method: str, rows: list[dict], labels: dict[str, np.ndarray]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_config(run_dir, method)
    pd.DataFrame(rows).to_csv(run_dir / "tuning_results.csv", index=False)
    np.savez(run_dir / "clusterings.npz", **labels)


def _density_run(tmp_path: Path) -> ClusteringTuningRun:
    """Three combinations over 20 subjects: 4 balanced clusters; 2 clusters; one cluster holding 80%."""
    balanced = np.repeat([0, 1, 2, 3], 5)
    two = np.repeat([0, 1], 10)
    dominant = np.array([0] * 16 + [1] * 2 + [2] * 2)
    rows = [
        {"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.5, "davies_bouldin": 1.0},
        {"min_cluster_size": 10, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.6, "davies_bouldin": 0.9},
        {"min_cluster_size": 15, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.7, "davies_bouldin": 0.8},
    ]
    labels = {
        "min_cluster_size=5,min_samples=5": balanced,
        "min_cluster_size=10,min_samples=5": two,
        "min_cluster_size=15,min_samples=5": dominant,
    }
    _write_run(tmp_path, "hdbscan", rows, labels)
    return load_clustering_tuning_run(tmp_path)


def test_dendrogram_jump_is_the_ratio_of_two_consecutive_merge_heights():
    # a tree of 5 subjects: merges at heights 1, 2, 4, 20 (the last one joins two clusters)
    linkage = np.array([[0, 1, 1.0, 2], [2, 3, 2.0, 2], [4, 5, 4.0, 4], [6, 7, 20.0, 5]])

    jumps = dendrogram_jump(linkage, range(2, 4))

    assert jumps[2] == pytest.approx(20.0 / 4.0)  # merge 2->1 over merge 3->2
    assert jumps[3] == pytest.approx(4.0 / 2.0)


@pytest.mark.parametrize("k", [1, 5])
def test_dendrogram_jump_rejects_k_outside_the_tree(k):
    linkage = np.array([[0, 1, 1.0, 2], [2, 3, 2.0, 2], [4, 5, 4.0, 4], [6, 7, 20.0, 5]])

    with pytest.raises(ValueError, match="outside 2..4"):
        dendrogram_jump(linkage, range(k, k + 1))


def test_dendrogram_jump_rejects_a_zero_height_denominator():
    linkage = np.array([[0, 1, 0.0, 2], [2, 3, 0.0, 2], [4, 5, 3.0, 4], [6, 7, 5.0, 5]])

    with pytest.raises(ValueError, match="height 0"):
        dendrogram_jump(linkage, range(3, 4))


def test_combo_key_matches_the_keys_clustering_writes():
    row = {"n_clusters": 3, "linkage": "ward", "metric": "euclidean"}

    assert combo_key(row, ("n_clusters", "linkage", "metric")) == "n_clusters=3,linkage=ward,metric=euclidean"


def test_load_run_rejects_adp(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    _write_config(tmp_path, "adp")

    with pytest.raises(ValueError, match="adp is not analysed here"):
        load_clustering_tuning_run(tmp_path)


def test_load_run_rejects_a_production_run(tmp_path):
    _write_config(tmp_path, "hdbscan", fine_tuning=False)

    with pytest.raises(ValueError, match="not a tuning run"):
        load_clustering_tuning_run(tmp_path)


def test_load_run_rejects_clusterings_that_do_not_match_the_results(tmp_path):
    """Regression guard for lessons_learned.md #18: a directory reused by a run with another grid."""
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.5, "davies_bouldin": 1.0}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": np.zeros(4, dtype=int), "min_cluster_size=9,min_samples=5": np.zeros(4, dtype=int)})

    with pytest.raises(ValueError, match="does not match tuning_results.csv"):
        load_clustering_tuning_run(tmp_path)


def _blobs(n_subjects: int = 20) -> np.ndarray:
    """One row per subject of the density runs below: three well-separated blobs, so every labelling has a DBCV."""
    rng = np.random.default_rng(0)
    centres = np.repeat([0.0, 6.0, 12.0], -(-n_subjects // 3))[:n_subjects]
    return centres[:, None] + rng.normal(scale=0.3, size=(n_subjects, 3))


def test_density_metrics_computes_the_cluster_count_the_largest_share_and_the_dbcv(tmp_path):
    run = _density_run(tmp_path)
    X = _blobs()
    metrics = density_metrics(run, X)

    assert metrics["n_clusters_found"].tolist() == [4, 2, 3]
    assert metrics["largest_cluster_share"].tolist() == pytest.approx([0.25, 0.5, 0.8])
    expected = [dbcv(X, run.labels[key])[0] for key in run.labels]
    assert metrics["dbcv"].tolist() == pytest.approx(expected)
    assert "usable" not in metrics.columns  # a measurement table, no verdict


def test_density_metrics_counts_noise_in_the_denominator_of_the_largest_share(tmp_path):
    labels = np.array([0] * 6 + [1] * 4 + [-1] * 10)
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.5}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": labels})

    metrics = density_metrics(load_clustering_tuning_run(tmp_path), _blobs())

    assert metrics.loc[0, "largest_cluster_share"] == pytest.approx(6 / 20)


def test_density_metrics_rejects_n_clusters_found_that_disagrees_with_the_labels(tmp_path):
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.0, "n_clusters_found": 7}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": np.repeat([0, 1], 5)})

    with pytest.raises(ValueError, match="n_clusters_found"):
        density_metrics(load_clustering_tuning_run(tmp_path), _blobs(10))


@pytest.mark.parametrize("labels", [np.full(8, -1), np.zeros(8, dtype=int), np.array([0] * 4 + [-1] * 4)])
def test_density_metrics_leaves_the_dbcv_undefined_below_two_clusters_never_zero(tmp_path, labels):
    """Regression: the hdbscan package returns the integer 0 for an all-noise labelling, which reads as a real score."""
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 1.0}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": labels})

    metrics = density_metrics(load_clustering_tuning_run(tmp_path), _blobs(8))

    assert np.isnan(metrics.loc[0, "dbcv"])
    if (labels == -1).all():
        assert np.isnan(metrics.loc[0, "largest_cluster_share"])


def test_density_metrics_rejects_a_matrix_that_is_not_the_runs(tmp_path):
    with pytest.raises(ValueError, match="one row per label"):
        density_metrics(_density_run(tmp_path), _blobs(19))


def test_dbcv_curves_returns_one_figure_for_hdbscan(tmp_path):
    metrics = density_metrics(_density_run(tmp_path), _blobs())

    figures = dbcv_curves_figures(metrics)

    assert list(figures) == [""]


def test_dbcv_curves_returns_one_figure_per_selection_method(tmp_path):
    metrics = density_metrics(_density_run(tmp_path), _blobs())
    soft = pd.concat([metrics.assign(cluster_selection_method="eom"), metrics.assign(cluster_selection_method="leaf")])

    assert sorted(dbcv_curves_figures(soft)) == ["eom", "leaf"]


def test_dbcv_curves_draw_every_combination_even_with_no_dbcv_and_much_noise(tmp_path):
    """No limit on the noise (a threshold of ours is gone): a run with every DBCV undefined still gets its figure."""
    metrics = density_metrics(_density_run(tmp_path), _blobs()).assign(noise_fraction=0.9, dbcv=np.nan)

    figures = dbcv_curves_figures(metrics)

    assert list(figures) == [""]
    assert len(figures[""].axes[0].lines) == 2  # the line of the data and the zero line


def test_recomputed_internal_metrics_of_agglomerative_match_the_functions_the_sweep_uses():
    X = _three_blobs()
    labels = {
        "n_clusters=2,linkage=average,metric=euclidean": np.repeat([0, 1], [30, 15]),
        "n_clusters=3,linkage=average,metric=cosine": np.repeat([0, 1, 2], 15),
    }
    rows = [{"n_clusters": 2, "linkage": "average", "metric": "euclidean", "silhouette": 9.0, "calinski_harabasz": 9.0, "davies_bouldin": 9.0, "noise_fraction": 0.0},
            {"n_clusters": 3, "linkage": "average", "metric": "cosine", "silhouette": 9.0, "calinski_harabasz": 9.0, "davies_bouldin": 9.0, "noise_fraction": 0.0}]
    run = ClusteringTuningRun(Path("run"), "agglomerative", Path("m"), pd.DataFrame(rows), labels)

    metrics = recomputed_internal_metrics(run, X)

    euclid = compute_clustering_metrics_metric_aware(X, labels["n_clusters=2,linkage=average,metric=euclidean"], "euclidean")
    cosine = compute_clustering_metrics_metric_aware(X, labels["n_clusters=3,linkage=average,metric=cosine"], "cosine")
    assert metrics.loc[0, "silhouette"] == pytest.approx(euclid["silhouette"])
    assert metrics.loc[0, "calinski_harabasz"] == pytest.approx(euclid["calinski_harabasz"])
    assert metrics.loc[1, "silhouette"] == pytest.approx(cosine["silhouette"])
    # Calinski-Harabasz and Davies-Bouldin need the euclidean distance: undefined, not computed, under cosine
    assert np.isnan(metrics.loc[1, "calinski_harabasz"]) and np.isnan(metrics.loc[1, "davies_bouldin"])


def test_recomputed_internal_metrics_of_a_density_run_are_the_noise_fraction_and_keep_the_fit_columns(tmp_path):
    labels = np.array([0] * 6 + [1] * 4 + [-1] * 10)
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.0, "membership_mean": 0.7}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": labels})

    metrics = recomputed_internal_metrics(load_clustering_tuning_run(tmp_path), _blobs())

    assert metrics.loc[0, "noise_fraction"] == pytest.approx(0.5)
    assert metrics.loc[0, "membership_mean"] == 0.7  # comes from the fit: not recomputable, not touched


def test_recomputed_internal_metrics_refuses_a_column_the_run_never_wrote():
    rows = [{"n_clusters": 2, "linkage": "average", "metric": "euclidean"}]
    run = ClusteringTuningRun(Path("run"), "agglomerative", Path("m"), pd.DataFrame(rows), {"n_clusters=2,linkage=average,metric=euclidean": np.repeat([0, 1], [30, 15])})

    with pytest.raises(ValueError, match="did not write it"):
        recomputed_internal_metrics(run, _three_blobs())


def _agglomerative_run(tmp_path: Path, rows: list[dict]) -> ClusteringTuningRun:
    results = pd.DataFrame(rows)
    return ClusteringTuningRun(tmp_path, "agglomerative", Path("matrix_dir"), results, {})


def _three_blobs() -> np.ndarray:
    rng = np.random.default_rng(0)
    return np.vstack([rng.normal(loc=center, scale=0.3, size=(15, 2)) for center in ([0, 0], [8, 8], [0, 8])])


def _rows_with_invalid_ward_cosine() -> list[dict]:
    return [
        {"n_clusters": k, "linkage": linkage, "metric": metric, "silhouette": 0.5, "davies_bouldin": 1.0}
        for k in (2, 3)
        for linkage, metric in (("ward", "euclidean"), ("average", "euclidean"), ("ward", "cosine"), ("average", "cosine"))
    ]


def test_cophenetic_table_scores_each_valid_metric_linkage_pair(tmp_path):
    run = _agglomerative_run(tmp_path, _rows_with_invalid_ward_cosine())

    cophenetic = cophenetic_table(run, _three_blobs())

    # ward + cosine is invalid in sklearn and was never swept: it must not appear
    assert set(zip(cophenetic["metric"], cophenetic["linkage"])) == {("euclidean", "ward"), ("euclidean", "average"), ("cosine", "average")}
    assert cophenetic["cophenetic_correlation"].between(0, 1).all()


def test_jump_table_has_a_row_per_pair_and_k_and_a_sharper_cut_at_the_true_k(tmp_path):
    run = _agglomerative_run(tmp_path, _rows_with_invalid_ward_cosine())

    jump = jump_table(run, _three_blobs(), range(3, 6))

    assert set(jump["n_clusters"]) == {3, 4, 5}
    assert set(zip(jump["metric"], jump["linkage"])) == {("euclidean", "ward"), ("euclidean", "average"), ("cosine", "average")}
    # three well-separated blobs: the cut at 3 clusters is sharper than the one at 5, for ward
    ward = jump[(jump["metric"] == "euclidean") & (jump["linkage"] == "ward")].set_index("n_clusters")["jump"]
    assert ward[3] > ward[5]


@pytest.mark.parametrize("table", [lambda run: cophenetic_table(run, _three_blobs()), lambda run: jump_table(run, _three_blobs(), range(3, 4))])
def test_the_dendrogram_tables_reject_a_density_run(tmp_path, table):
    run = ClusteringTuningRun(tmp_path, "hdbscan", Path("m"), pd.DataFrame(), {})

    with pytest.raises(ValueError, match="needs an agglomerative run"):
        table(run)


def _curves_results() -> pd.DataFrame:
    """ward and single for euclidean, average for cosine (no Davies-Bouldin: it is empty for a non-euclidean metric)."""
    return pd.DataFrame(
        {
            "n_clusters": [2, 3, 2, 3, 2, 3],
            "linkage": ["ward", "ward", "single", "single", "average", "average"],
            "metric": ["euclidean"] * 4 + ["cosine"] * 2,
            "silhouette": [0.5, 0.4, 0.1, -0.2, 0.7, 0.6],
            "davies_bouldin": [1.0, 1.1, 2.0, 2.0, np.nan, np.nan],
            "calinski_harabasz": [100.0, 90.0, 20.0, 10.0, np.nan, np.nan],
        }
    )


def test_silhouette_zoom_limits_pad_the_range_and_a_flat_series_gets_a_fixed_padding():
    low, high = silhouette_zoom_limits(pd.Series([0.4, 0.5, np.nan]))
    assert (low, high) == pytest.approx((0.4 - 0.008, 0.5 + 0.008))
    assert silhouette_zoom_limits(pd.Series([0.3, 0.3])) == pytest.approx((0.25, 0.35))
    with pytest.raises(ValueError, match="no silhouette"):
        silhouette_zoom_limits(pd.Series([np.nan]))


def test_k_curves_targets_are_the_metrics_with_a_linkage_other_than_single_in_the_metric_order():
    results = _curves_results()
    only_single = results[results["linkage"] == "single"].assign(metric="manhattan")

    assert k_curves_targets(results) == ["euclidean", "cosine"]
    assert k_curves_targets(pd.concat([results, only_single])) == ["euclidean", "cosine"]  # a metric with only single has no figure
    assert [k_curves_file_name(metric) for metric in k_curves_targets(results)] == ["k_curves_metric=euclidean.png", "k_curves_metric=cosine.png"]


def test_k_curves_figure_rejects_a_metric_the_run_does_not_have_or_that_has_only_single():
    results = _curves_results()
    only_single = pd.concat([results, results[results["linkage"] == "single"].assign(metric="manhattan")])

    with pytest.raises(ValueError, match="metric='chebyshev'"):
        k_curves_figure(results, "chebyshev")
    with pytest.raises(ValueError, match="metric='manhattan'"):
        k_curves_figure(only_single, "manhattan")


def test_k_curves_figure_does_not_draw_single():
    figure = k_curves_figure(_curves_results(), "euclidean")

    assert [line.get_label() for line in figure.axes[0].get_lines() if not line.get_label().startswith("_")] == ["ward"]


def test_run_axis_limits_take_the_extremes_of_every_metric_and_round_them_out_to_a_tenth():
    results = _curves_results()  # silhouette without single: euclidean 0.4-0.5, cosine 0.6-0.7; Davies-Bouldin only euclidean

    assert run_axis_limits(results, "silhouette") == pytest.approx((0.3, 0.8))
    assert run_axis_limits(results, "davies_bouldin") == pytest.approx((0.9, 1.2))  # the NaN of cosine is ignored


def test_run_axis_limits_ignore_single_even_when_it_is_the_lowest():
    results = _curves_results()  # single reaches -0.2

    assert run_axis_limits(results, "silhouette")[0] > 0


def test_run_axis_limits_reject_a_run_with_no_value_to_fit():
    results = _curves_results().assign(davies_bouldin=np.nan)

    with pytest.raises(ValueError, match="no davies_bouldin"):
        run_axis_limits(results, "davies_bouldin")


def test_k_curves_figures_of_a_run_share_their_axes_and_drop_an_empty_davies_bouldin_panel():
    results = _curves_results()

    euclidean = k_curves_figure(results, "euclidean")
    cosine = k_curves_figure(results, "cosine")

    assert len(euclidean.axes) == 2 and len(cosine.axes) == 1
    assert euclidean.axes[0].get_ylim() == cosine.axes[0].get_ylim() == pytest.approx((0.3, 0.8))
    assert euclidean.axes[1].get_ylim() == pytest.approx((0.9, 1.2))
    # no fixed -1..1 panel and no reference lines: the only line of the silhouette panel is the ward curve
    assert len(euclidean.axes[0].get_lines()) == 1


def test_linkage_agreement_is_the_ari_between_the_partitions_of_each_pair_of_linkages(tmp_path):
    first = np.array([0, 0, 0, 1, 1, 1])
    renamed = np.array([5, 5, 5, 9, 9, 9])  # the same partition under other names
    different = np.array([0, 1, 0, 1, 0, 1])
    rows = [{"n_clusters": 2, "linkage": linkage, "metric": "euclidean", "silhouette": 0.5} for linkage in ("ward", "average", "single")]
    labels = {f"n_clusters=2,linkage={linkage},metric=euclidean": array for linkage, array in (("ward", first), ("average", renamed), ("single", different))}
    _write_run(tmp_path, "agglomerative", rows, labels)

    agreement = linkage_agreement(load_clustering_tuning_run(tmp_path)).set_index(["linkage_a", "linkage_b"])["ari"]

    assert agreement[("ward", "average")] == pytest.approx(1.0)  # naming does not matter
    assert agreement[("ward", "single")] < 0.5 and agreement[("average", "single")] == pytest.approx(agreement[("ward", "single")])
    assert list(agreement.index) == [("ward", "average"), ("ward", "single"), ("average", "single")]  # LINKAGE_ORDER, not alphabetical


def test_linkage_agreement_skips_a_linkage_that_was_not_swept_for_a_metric_and_rejects_a_density_run(tmp_path):
    labels_a, labels_b = np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1])
    rows = [
        {"n_clusters": 2, "linkage": "ward", "metric": "euclidean", "silhouette": 0.5},
        {"n_clusters": 2, "linkage": "average", "metric": "euclidean", "silhouette": 0.5},
        {"n_clusters": 2, "linkage": "average", "metric": "cosine", "silhouette": 0.5},  # ward + cosine is invalid: absent
    ]
    keys = ["n_clusters=2,linkage=ward,metric=euclidean", "n_clusters=2,linkage=average,metric=euclidean", "n_clusters=2,linkage=average,metric=cosine"]
    _write_run(tmp_path, "agglomerative", rows, dict(zip(keys, (labels_a, labels_b, labels_a))))

    agreement = linkage_agreement(load_clustering_tuning_run(tmp_path))

    assert agreement["metric"].tolist() == ["euclidean"]  # cosine has a single linkage: no pair
    with pytest.raises(ValueError, match="needs an agglomerative run"):
        linkage_agreement(ClusteringTuningRun(tmp_path, "hdbscan", Path("m"), pd.DataFrame(), {}))
