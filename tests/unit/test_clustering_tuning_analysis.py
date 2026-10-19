"""Unit tests for src/analysis/clustering_tuning_analysis.py."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.clustering_tuning_analysis import (
    CONVENTION_LINES,
    ClusteringTuningRun,
    agglomerative_analysis,
    combo_key,
    convention_lines_caption,
    dendrogram_jump,
    density_metrics,
    k_curves_figure,
    k_curves_file_name,
    k_curves_targets,
    load_clustering_tuning_run,
    noise_filtered_curves_figures,
    silhouette_band,
    silhouette_zoom_limits,
    tuning_report_markdown,
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


def test_density_metrics_computes_the_cluster_count_and_the_largest_share(tmp_path):
    metrics = density_metrics(_density_run(tmp_path))

    assert metrics["n_clusters_found"].tolist() == [4, 2, 3]
    assert metrics["largest_cluster_share"].tolist() == pytest.approx([0.25, 0.5, 0.8])
    assert "usable" not in metrics.columns  # a measurement table, no verdict


def test_density_metrics_counts_noise_in_the_denominator_of_the_largest_share(tmp_path):
    labels = np.array([0] * 6 + [1] * 4 + [-1] * 10)
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.5, "silhouette": 0.5, "davies_bouldin": 1.0}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": labels})

    metrics = density_metrics(load_clustering_tuning_run(tmp_path))

    assert metrics.loc[0, "largest_cluster_share"] == pytest.approx(6 / 20)


def test_density_metrics_rejects_n_clusters_found_that_disagrees_with_the_labels(tmp_path):
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.5, "davies_bouldin": 1.0, "n_clusters_found": 7}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": np.repeat([0, 1], 5)})

    with pytest.raises(ValueError, match="n_clusters_found"):
        density_metrics(load_clustering_tuning_run(tmp_path))


def test_density_metrics_all_noise_has_no_largest_share(tmp_path):
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 1.0, "silhouette": np.nan, "davies_bouldin": np.nan}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": np.full(8, -1)})

    metrics = density_metrics(load_clustering_tuning_run(tmp_path))

    assert np.isnan(metrics.loc[0, "largest_cluster_share"])


def test_noise_filtered_curves_with_no_combination_kept_returns_no_figure_instead_of_raising(tmp_path):
    """Regression: a run with every combination above the noise limit (UMAP euclidean, streamline) used to
    abort before density_metrics.csv was written, so the runs with no structure got no output at all."""
    metrics = density_metrics(_density_run(tmp_path)).assign(noise_fraction=0.5)

    figures, without_figure = noise_filtered_curves_figures(metrics, 0.1)

    assert figures == {}
    assert without_figure == [""]


def test_noise_filtered_curves_returns_one_figure_for_hdbscan(tmp_path):
    metrics = density_metrics(_density_run(tmp_path))

    figures, without_figure = noise_filtered_curves_figures(metrics, 0.1)

    assert list(figures) == [""]
    assert without_figure == []


def test_noise_filtered_curves_returns_one_figure_per_selection_method(tmp_path):
    metrics = density_metrics(_density_run(tmp_path))
    soft = pd.concat([metrics.assign(cluster_selection_method="eom"), metrics.assign(cluster_selection_method="leaf")])

    figures, without_figure = noise_filtered_curves_figures(soft, 0.1)

    assert sorted(figures) == ["eom", "leaf"]
    assert without_figure == []


def test_noise_filtered_curves_reports_the_selection_method_with_no_combination_under_the_limit(tmp_path):
    """Regression: on a real hdbscan_soft run `leaf` never goes below 15% noise, and that used to abort the
    whole analysis instead of leaving out only the figure that could not be drawn."""
    metrics = density_metrics(_density_run(tmp_path))
    soft = pd.concat([metrics.assign(cluster_selection_method="eom"), metrics.assign(cluster_selection_method="leaf", noise_fraction=0.4)])

    figures, without_figure = noise_filtered_curves_figures(soft, 0.1)

    assert list(figures) == ["eom"]
    assert without_figure == ["leaf"]


def _agglomerative_run(tmp_path: Path, rows: list[dict]) -> ClusteringTuningRun:
    results = pd.DataFrame(rows)
    return ClusteringTuningRun(tmp_path, "agglomerative", Path("matrix_dir"), results, {})


def _three_blobs() -> np.ndarray:
    rng = np.random.default_rng(0)
    return np.vstack([rng.normal(loc=center, scale=0.3, size=(15, 2)) for center in ([0, 0], [8, 8], [0, 8])])


def test_agglomerative_analysis_scores_each_valid_metric_linkage_pair(tmp_path):
    rows = [
        {"n_clusters": k, "linkage": linkage, "metric": metric, "silhouette": 0.5, "davies_bouldin": 1.0}
        for k in (2, 3)
        for linkage, metric in (("ward", "euclidean"), ("average", "euclidean"), ("ward", "cosine"), ("average", "cosine"))
    ]
    run = _agglomerative_run(tmp_path, rows)

    cophenetic, jump = agglomerative_analysis(run, _three_blobs(), range(3, 6))

    # ward + cosine is invalid in sklearn and was never swept: it must not appear
    assert set(zip(cophenetic["metric"], cophenetic["linkage"])) == {("euclidean", "ward"), ("euclidean", "average"), ("cosine", "average")}
    assert cophenetic["cophenetic_correlation"].between(0, 1).all()
    assert set(jump["n_clusters"]) == {3, 4, 5}
    # three well-separated blobs: the cut at 3 clusters is sharper than the one at 5, for ward
    ward = jump[(jump["metric"] == "euclidean") & (jump["linkage"] == "ward")].set_index("n_clusters")["jump"]
    assert ward[3] > ward[5]


def test_agglomerative_analysis_rejects_a_density_run(tmp_path):
    run = ClusteringTuningRun(tmp_path, "hdbscan", Path("m"), pd.DataFrame(), {})

    with pytest.raises(ValueError, match="needs an agglomerative run"):
        agglomerative_analysis(run, _three_blobs(), range(3, 4))


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


@pytest.mark.parametrize(
    "silhouette, band",
    [(0.99, "0.71-1.00"), (0.71, "0.71-1.00"), (0.706, "0.71-1.00"), (0.7049, "0.51-0.70"), (0.51, "0.51-0.70"),
     (0.50, "0.26-0.50"), (0.26, "0.26-0.50"), (0.25, "0.00-0.25"), (0.0, "0.00-0.25"), (-0.0001, None), (-0.5, None)],
)
def test_silhouette_band_follows_the_convention_after_rounding_to_two_decimals(silhouette, band):
    assert silhouette_band(silhouette) == band


def test_silhouette_band_rejects_nan():
    with pytest.raises(ValueError, match="NaN silhouette"):
        silhouette_band(float("nan"))


def test_silhouette_zoom_limits_pad_the_range_and_a_flat_series_gets_a_fixed_padding():
    low, high = silhouette_zoom_limits(pd.Series([0.4, 0.5, np.nan]))
    assert (low, high) == pytest.approx((0.4 - 0.008, 0.5 + 0.008))
    assert silhouette_zoom_limits(pd.Series([0.3, 0.3])) == pytest.approx((0.25, 0.35))
    with pytest.raises(ValueError, match="no silhouette"):
        silhouette_zoom_limits(pd.Series([np.nan]))


def test_convention_lines_caption_names_the_lines_inside_and_outside_the_fitted_axis():
    caption = convention_lines_caption(pd.DataFrame({"silhouette": [0.40, 0.52]}))

    assert "Asse fisso: tutte visibili" in caption
    assert "visibili 0.51, fuori asse 0.00, 0.26, 0.71" in caption


def test_k_curves_targets_give_single_its_own_figure_and_follow_the_metric_order():
    targets = k_curves_targets(_curves_results())

    assert targets == [("euclidean", False), ("euclidean", True), ("cosine", False)]
    assert [k_curves_file_name(metric, single) for metric, single in targets] == [
        "k_curves_metric=euclidean.png", "k_curves_single_metric=euclidean.png", "k_curves_metric=cosine.png",
    ]


def test_k_curves_figure_rejects_a_metric_or_a_group_the_run_does_not_have():
    results = _curves_results()

    with pytest.raises(ValueError, match="metric='manhattan'"):
        k_curves_figure(results, "manhattan", single=False)
    with pytest.raises(ValueError, match="metric='cosine' and the single linkage"):
        k_curves_figure(results, "cosine", single=True)


def test_k_curves_figure_keeps_single_out_of_the_main_figure_and_alone_in_its_own():
    results = _curves_results()

    main = k_curves_figure(results, "euclidean", single=False)
    alone = k_curves_figure(results, "euclidean", single=True)

    assert [line.get_label() for line in main.axes[0].get_lines() if not line.get_label().startswith("_")] == ["ward"]
    assert [line.get_label() for line in alone.axes[0].get_lines() if not line.get_label().startswith("_")] == ["single"]


def test_k_curves_figure_has_a_fixed_and_a_fitted_silhouette_axis_and_drops_an_empty_davies_bouldin_panel():
    results = _curves_results()

    euclidean = k_curves_figure(results, "euclidean", single=False)
    cosine = k_curves_figure(results, "cosine", single=False)

    assert len(euclidean.axes) == 3 and len(cosine.axes) == 2
    assert euclidean.axes[0].get_ylim() == (-1, 1)
    assert euclidean.axes[1].get_ylim() == pytest.approx(silhouette_zoom_limits(pd.Series([0.5, 0.4])))
    # the fixed axis shows all four dashed lines of the convention (plus the one data line)
    assert len(euclidean.axes[0].get_lines()) == 1 + len(CONVENTION_LINES)


def _agglomerative_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "n_clusters": [2, 3, 2, 3],
            "linkage": ["ward", "ward", "average", "average"],
            "metric": ["euclidean", "euclidean", "cosine", "cosine"],
            "silhouette": [0.30, 0.45, 0.20, 0.10],
            "noise_fraction": [0.0, 0.0, 0.0, 0.0],
            "calinski_harabasz": [7258.9, 1200.0, np.nan, np.nan],
            "davies_bouldin": [0.7, 0.8, np.nan, np.nan],
        }
    )


def _dendrogram_frames(results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The cophenetic and jump frames agglomerative_analysis would give for `results`: 0.9 for every (metric, linkage),
    a jump of 1 + n_clusters / 10 for every n_clusters."""
    pairs = results[["metric", "linkage"]].drop_duplicates()
    cophenetic = pairs.assign(cophenetic_correlation=0.9)
    jump = results[["metric", "linkage", "n_clusters"]].assign(jump=lambda frame: 1 + frame["n_clusters"] / 10)
    return cophenetic, jump


def _agglomerative_report(tmp_path: Path, results: pd.DataFrame) -> str:
    cophenetic, jump = _dendrogram_frames(results)
    return tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results, cophenetic, jump)


def test_tuning_report_has_a_table_per_metric_and_linkage_with_the_three_indices_by_n_clusters(tmp_path):
    report = _agglomerative_report(tmp_path, _agglomerative_results())

    assert "## metric = euclidean" in report and "## metric = cosine" in report
    assert report.index("## metric = euclidean") < report.index("## metric = cosine")
    ward = report.split("### linkage = ward")[1].split("### ")[0]
    assert "| n_clusters | silhouette | davies_bouldin | calinski_harabasz |" in ward
    assert ward.index("| 2 | 0.300 | 0.700 | 7,259 |") < ward.index("| 3 | 0.450 | 0.800 | 1,200 |")  # by n_clusters, not by silhouette
    assert "noise_fraction" not in report


def test_tuning_report_shows_an_empty_index_as_a_dash_and_has_no_verdict_of_ours(tmp_path):
    report = _agglomerative_report(tmp_path, _agglomerative_results())

    assert "| 2 | 0.200 | – | – |" in report
    for verdict in ("usable", "usabile", "buono", "stabile", "candidat"):
        assert verdict not in report.lower()


def test_tuning_report_places_each_n_clusters_in_a_silhouette_band_and_says_what_a_negative_one_is(tmp_path):
    results = pd.DataFrame(
        {
            "n_clusters": [2, 3, 4, 5, 6],
            "linkage": ["single"] * 5,
            "metric": ["euclidean"] * 5,
            "silhouette": [0.30, 0.45, 0.10, -0.05, -0.20],
            "davies_bouldin": [1.0] * 5,
            "calinski_harabasz": [10.0] * 5,
        }
    )

    report = _agglomerative_report(tmp_path, results)

    assert "  - 0.26-0.50 (debole, forse artificiale): 2 k su 5 (k 2-3)" in report
    assert "  - 0.00-0.25 (nessuna struttura sostanziale): 1 k su 5 (k 4)" in report
    assert "  - negativa: 2 k su 5 (k 5-6); non accettabile per convenzione, la combinazione resta nel report" in report
    assert "0.71-1.00" not in report.split("## Termini")[0]  # a band no combination falls in is not listed
    assert "- Curva della silhouette: k=2: 0.300, k=6: -0.200" in report


def test_tuning_report_says_when_no_silhouette_is_negative(tmp_path):
    report = _agglomerative_report(tmp_path, _agglomerative_results())

    assert "  - negativa: nessun k" in report


def test_tuning_report_points_to_the_curves_figures_and_to_single_only_when_the_run_has_it(tmp_path):
    with_single = _agglomerative_report(tmp_path, _curves_results())
    without_single = _agglomerative_report(tmp_path, _agglomerative_results())

    assert "(k_curves_metric=euclidean.png)" in with_single and "(k_curves_single_metric=euclidean.png)" in with_single
    assert "(k_curves_metric=cosine.png)" in with_single and "k_curves_single_metric=cosine.png" not in with_single
    assert "k_curves_single" not in without_single


def test_tuning_report_defines_the_bands_with_their_source_and_the_two_indices_without_one(tmp_path):
    report = _agglomerative_report(tmp_path, _agglomerative_results())

    terms = report.split("## Termini")[1]
    assert "Kaufman & Rousseeuw (1990)" in terms and "0.26-0.50 debole" in terms
    assert "Per Davies-Bouldin e Calinski-Harabasz non esiste una convenzione con fonte" in terms


def test_tuning_report_has_a_cophenetic_table_and_a_jump_table_per_metric(tmp_path):
    report = _agglomerative_report(tmp_path, _curves_results())

    euclidean = report.split("## metric = euclidean")[1].split("## metric = cosine")[0]
    assert "### Cophenetic correlation" in euclidean and "### Salto del dendrogramma" in euclidean
    cophenetic = euclidean.split("### Cophenetic correlation")[1].split("### Salto")[0]
    assert cophenetic.index("| ward | 0.900 |") < cophenetic.index("| single | 0.900 |")  # linkage order, not alphabetical
    jump = euclidean.split("### Salto del dendrogramma")[1]
    assert "| n_clusters | ward | single |" in jump and "| 2 | 1.200 | 1.200 |" in jump
    # cosine has only average: its jump table has no other linkage column
    assert "| n_clusters | average |" in report.split("## metric = cosine")[1]


def test_tuning_report_links_the_images_clustering_wrote_in_the_run_folder_and_only_those(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    for name in ("dendrogram_metric=euclidean.png", "labels_2d_ward_euclidean.png", "interclass_distance_matrix.png"):
        (run_dir / name).write_bytes(b"png")

    report = _agglomerative_report(tmp_path, _curves_results())

    assert "(dendrogram_metric=euclidean.png)" in report and "(labels_2d_ward_euclidean.png)" in report
    assert "(interclass_distance_matrix.png)" in report
    assert "labels_2d_single_euclidean.png" not in report and "dendrogram_metric=cosine.png" not in report


def test_tuning_report_defines_cophenetic_and_jump_without_a_band(tmp_path):
    terms = _agglomerative_report(tmp_path, _curves_results()).split("## Termini")[1]

    assert "**`cophenetic_correlation`**" in terms and "**`jump`**" in terms
    assert terms.count("Nessuna fascia con fonte in letteratura") == 2


def test_tuning_report_of_agglomerative_needs_the_cophenetic_and_jump_frames_and_no_other_method_takes_them(tmp_path):
    results = _curves_results()
    cophenetic, jump = _dendrogram_frames(results)

    with pytest.raises(ValueError, match="needs the cophenetic and jump frames"):
        tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results)
    with pytest.raises(ValueError, match="belong to the agglomerative report"):
        tuning_report_markdown(tmp_path / "run", "adp", Path("matrix"), pd.DataFrame({"metric": ["dice"], "Z": [1.0], "silhouette": [0.1]}), cophenetic, jump)
    with pytest.raises(ValueError, match="no cophenetic or jump row for metric='cosine'"):
        tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results, cophenetic[cophenetic["metric"] != "cosine"], jump)
    with pytest.raises(ValueError, match=r"cophenetic has no column\(s\) \['cophenetic_correlation'\]"):
        tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results, cophenetic.drop(columns="cophenetic_correlation"), jump)


def test_tuning_report_of_hdbscan_has_a_single_table_and_integer_counts(tmp_path):
    results = pd.DataFrame(
        {"min_cluster_size": [10, 50], "min_samples": [1, 5], "silhouette": [0.5, np.nan], "noise_fraction": [0.2, 1.0],
         "n_clusters_found": [205.0, 0.0], "largest_cluster_share": [0.1, np.nan]}
    )

    report = tuning_report_markdown(tmp_path / "run", "hdbscan", Path("matrix"), results)

    assert report.count("## ") == 2  # "Tabella" and "Termini"
    assert "| 10 | 1 | 0.500 | 0.200 | 205 | 0.100 |" in report
    assert "| 50 | 5 | – | 1.000 | 0 | – |" in report  # an empty silhouette sorts last


def test_tuning_report_groups_hdbscan_soft_by_selection_method_and_defines_the_terms_present(tmp_path):
    results = pd.DataFrame(
        {"min_cluster_size": [10, 10], "min_samples": [1, 1], "cluster_selection_method": ["eom", "leaf"], "silhouette": [0.5, 0.4],
         "membership_mean": [0.6, 0.7]}
    )

    report = tuning_report_markdown(tmp_path / "run", "hdbscan_soft", Path("matrix"), results)

    assert "## cluster_selection_method = eom" in report and "## cluster_selection_method = leaf" in report
    assert "**`membership_mean`**" in report and "**`davies_bouldin`**" not in report


def test_tuning_report_of_adp_formats_z_without_trailing_zeros(tmp_path):
    results = pd.DataFrame({"metric": ["dice"], "Z": [1.65], "silhouette": [0.03], "n_clusters_found": [30.0]})

    assert "| 1.65 | 0.030 | 30 |" in tuning_report_markdown(tmp_path / "run", "adp", Path("matrix"), results)


def test_tuning_report_rejects_a_method_without_report_and_a_missing_column(tmp_path):
    with pytest.raises(ValueError, match="no report for clustering_method 'kmeans'"):
        tuning_report_markdown(tmp_path / "run", "kmeans", Path("matrix"), _agglomerative_results())
    with pytest.raises(ValueError, match=r"no column\(s\) \['silhouette'\]"):
        _agglomerative_report(tmp_path, _agglomerative_results().drop(columns="silhouette"))
