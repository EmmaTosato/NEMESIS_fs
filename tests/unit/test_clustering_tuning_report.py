"""Unit tests for src/analysis/clustering_tuning_report.py."""

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.clustering_tuning_report import (
    require_report_evaluations,
    HINT_AGREEMENT,
    HINT_COPHENETIC,
    HINT_DENDROGRAM,
    HINT_DBCV_CURVES,
    HINT_HEATMAP,
    HINT_JUMP,
    HINT_LABELS_2D,
    curves_hint,
    tuning_report_markdown,
)


def _hint(hint: tuple[str, ...]) -> str:
    """The first bullet of a hint as it is written in a report: enough to find (and count) the block."""
    return f"> - {hint[0]}"


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


def _dendrogram_frames(results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The cophenetic, agreement and jump frames the analysis would give for `results`: 0.9 for every (metric, linkage),
    an ARI of 0.5 for every pair of linkages of a metric at every n_clusters, a jump of 1 + n_clusters / 10."""
    cophenetic = results[["metric", "linkage"]].drop_duplicates().assign(cophenetic_correlation=0.9)
    pairs = [
        {"metric": metric, "n_clusters": k, "linkage_a": a, "linkage_b": b, "ari": 0.5}
        for (metric, k), group in results.groupby(["metric", "n_clusters"])
        for a, b in itertools.combinations([name for name in ("ward", "average", "complete", "single") if name in set(group["linkage"])], 2)
    ]
    agreement = pd.DataFrame(pairs, columns=["metric", "n_clusters", "linkage_a", "linkage_b", "ari"])
    jump = results[["metric", "linkage", "n_clusters"]].assign(jump=lambda frame: 1 + frame["n_clusters"] / 10)
    return cophenetic, agreement, jump


def _agglomerative_report(tmp_path: Path, results: pd.DataFrame) -> str:
    cophenetic, agreement, jump = _dendrogram_frames(results)
    return tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results, cophenetic, agreement, jump)


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


def test_tuning_report_counts_the_negative_silhouettes_and_gives_the_first_and_last_value(tmp_path):
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

    assert "- **Silhouette negativa**: 2 k su 5 (k 5-6)" in report
    assert "- **Dal primo all'ultimo valore** (k): k=2: 0.300, k=6: -0.200" in report
    body = report.split("## Termini")[0]
    assert "fascia" not in body and "convenzione" not in body  # a measurement, not a verdict of a convention


def test_tuning_report_says_when_no_silhouette_is_negative(tmp_path):
    report = _agglomerative_report(tmp_path, _agglomerative_results())

    assert "- **Silhouette negativa**: nessuna" in report


def test_tuning_report_points_to_one_curves_figure_per_metric_and_never_to_a_single_one(tmp_path):
    report = _agglomerative_report(tmp_path, _curves_results())

    assert "(k_curves_metric=euclidean.png)" in report and "(k_curves_metric=cosine.png)" in report
    assert "k_curves_single" not in report
    assert "### linkage = single" in report  # single is not drawn, its table stays


def test_tuning_report_has_no_curves_figure_for_a_metric_with_only_single(tmp_path):
    only_single = _curves_results().query("linkage == 'single'")

    report = _agglomerative_report(tmp_path, only_single)

    assert "k_curves_metric" not in report and "### linkage = single" in report


def test_tuning_report_hint_gives_the_axes_shared_by_the_run(tmp_path):
    report = _agglomerative_report(tmp_path, _curves_results())

    assert "Gli assi sono gli stessi in tutti i grafici di questa serie: silhouette da 0.3 a 0.8, Davies-Bouldin da 0.9 a 1.2" in report
    assert "Gli assi sono gli stessi in tutti i grafici di questa serie: silhouette da 0.3 a 0.8." in report  # cosine: no Davies-Bouldin panel
    assert "`single` non è disegnato" in report


def test_tuning_report_only_mentions_the_silhouette_bands_and_points_to_where_they_are_explained(tmp_path):
    report = _agglomerative_report(tmp_path, _agglomerative_results())

    terms = report.split("## Termini")[1]
    assert "Kaufman & Rousseeuw 1990" in terms and "questo report non le usa" in terms
    assert "evaluation_metrics.md" in terms
    assert "0.26" not in report and "0.71" not in report  # no edge of a band anywhere


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
    for name in ("dendrogram_metric=euclidean.png", "labels_2d_ward_euclidean.png"):
        (run_dir / name).write_bytes(b"png")

    report = _agglomerative_report(tmp_path, _curves_results())

    assert "(dendrogram_metric=euclidean.png)" in report and "(labels_2d_ward_euclidean.png)" in report
    assert "labels_2d_single_euclidean.png" not in report and "dendrogram_metric=cosine.png" not in report


def test_tuning_report_writes_a_how_to_read_line_under_each_table_and_figure_once(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    for name in ("dendrogram_metric=euclidean.png", "labels_2d_ward_euclidean.png", "labels_2d_single_euclidean.png"):
        (run_dir / name).write_bytes(b"png")

    report = _agglomerative_report(tmp_path, _curves_results())

    # euclidean has ward and single, cosine only average: 2 curves figures (single is not drawn), 2 metrics for each table
    for hint, count in ((curves_hint((0.0, 1.0), None), 2), (HINT_COPHENETIC, 2), (HINT_JUMP, 2),
                        (HINT_DENDROGRAM, 1), (HINT_LABELS_2D, 1)):
        assert report.count(_hint(hint)) == count, hint[0][:40]


def test_tuning_report_without_the_images_has_no_hint_for_them_and_a_series_hint_moves_to_the_first_image_that_exists(tmp_path):
    bare = _agglomerative_report(tmp_path, _curves_results())
    assert HINT_DENDROGRAM[0] not in bare and HINT_LABELS_2D[0] not in bare

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "labels_2d_single_euclidean.png").write_bytes(b"png")  # the first of the series (ward) is missing
    report = _agglomerative_report(tmp_path, _curves_results())

    assert report.count(_hint(HINT_LABELS_2D)) == 1
    assert report.index("labels_2d_single_euclidean.png") < report.index(HINT_LABELS_2D[0])


def test_tuning_report_defines_cophenetic_and_jump_without_a_band(tmp_path):
    terms = _agglomerative_report(tmp_path, _curves_results()).split("## Termini")[1]

    assert "**`cophenetic_correlation`**" in terms and "**`jump`**" in terms
    assert terms.count("Nessuna fascia con fonte in letteratura") == 2


def test_tuning_report_of_agglomerative_needs_the_analysis_frames_and_no_other_method_takes_them(tmp_path):
    results = _curves_results()
    cophenetic, agreement, jump = _dendrogram_frames(results)
    adp = pd.DataFrame({"metric": ["dice"], "Z": [1.0], "silhouette": [0.1]})

    with pytest.raises(ValueError, match="needs the cophenetic, agreement and jump frames"):
        tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results)
    with pytest.raises(ValueError, match="belong to the agglomerative report"):
        tuning_report_markdown(tmp_path / "run", "adp", Path("matrix"), adp, cophenetic, agreement, jump)
    with pytest.raises(ValueError, match="no cophenetic or jump row for metric='cosine'"):
        tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results, cophenetic[cophenetic["metric"] != "cosine"], agreement, jump)
    with pytest.raises(ValueError, match=r"agreement has no column\(s\) \['ari'\]"):
        tuning_report_markdown(tmp_path / "run", "agglomerative", Path("matrix"), results, cophenetic, agreement.drop(columns="ari"), jump)


def test_tuning_report_has_an_agreement_table_per_metric_and_says_when_a_metric_has_a_single_linkage(tmp_path):
    report = _agglomerative_report(tmp_path, _curves_results())

    euclidean = report.split("## metric = euclidean")[1].split("## metric = cosine")[0]
    assert "### Accordo tra linkage (ARI)" in euclidean
    agreement = euclidean.split("### Accordo tra linkage (ARI)")[1].split("### Salto")[0]
    assert "| n_clusters | ward-single |" in agreement and "| 2 | 0.500 |" in agreement
    assert _hint(HINT_AGREEMENT) in agreement
    cosine = report.split("## metric = cosine")[1]
    assert "Non calcolabile: la run ha un solo linkage per questa `metric`." in cosine
    assert "**`ari`**" in report.split("## Termini")[1]


def _density_results(soft: bool = False) -> pd.DataFrame:
    """density_metrics of two min_samples x two min_cluster_size; the (50, 5) combination is all noise."""
    frame = pd.DataFrame(
        {
            "min_cluster_size": [10, 50, 10, 50],
            "min_samples": [1, 1, 5, 5],
            "noise_fraction": [0.2, 0.1, 0.25, 1.0],
            "n_clusters_found": [30.0, 5.0, 12.0, 0.0],
            "largest_cluster_share": [0.1, 0.4, 0.2, np.nan],
            "dbcv": [0.12, 0.31, -0.04, np.nan],
        }
    )
    if not soft:
        return frame
    soft_columns = {"membership_mean": 0.6, "persistence_mean": 0.2}
    return pd.concat([frame.assign(cluster_selection_method=method, **soft_columns) for method in ("eom", "leaf")], ignore_index=True)


def test_tuning_report_of_hdbscan_has_a_table_per_min_samples_with_integer_counts_and_the_dbcv(tmp_path):
    report = tuning_report_markdown(tmp_path / "run", "hdbscan", Path("matrix"), _density_results())

    assert "## min_samples = 1" in report and "## min_samples = 5" in report
    assert "| min_cluster_size | n_clusters_found | noise_fraction | largest_cluster_share | dbcv |" in report
    assert "| 10 | 30 | 0.200 | 0.100 | 0.120 |" in report
    assert "| 50 | 0 | 1.000 | – | – |" in report  # all noise: no share, no DBCV
    assert "cluster_selection_method" not in report


def test_tuning_report_of_a_density_method_has_no_silhouette_family_columns_and_says_why(tmp_path):
    report = tuning_report_markdown(tmp_path / "run", "hdbscan", Path("matrix"), _density_results())

    body, terms = report.split("## Termini")
    for name in ("silhouette", "davies_bouldin", "calinski_harabasz"):
        assert name not in body
    assert "Indici non calcolati" in terms and "**`dbcv`**" in terms


def test_tuning_report_of_hdbscan_comments_the_dbcv_the_noise_and_the_cluster_count_of_each_table(tmp_path):
    report = tuning_report_markdown(tmp_path / "run", "hdbscan", Path("matrix"), _density_results())

    first = report.split("## min_samples = 1")[1].split("## min_samples = 5")[0]
    assert "- **DBCV**: da 0.120 (min_cluster_size 10) a 0.310 (min_cluster_size 50)" in first
    assert "- **Rumore**: da 0.100 (min_cluster_size 50) a 0.200 (min_cluster_size 10)" in first
    assert "- **Cluster trovati**: da 5 (min_cluster_size 50) a 30 (min_cluster_size 10)" in first
    assert "Meno di 2 cluster" not in first
    second = report.split("## min_samples = 5")[1]
    assert "- **Meno di 2 cluster** (DBCV non definito): 1 su 2 (min_cluster_size 50)" in second
    assert "- **DBCV**: da -0.040 (min_cluster_size 10) a -0.040 (min_cluster_size 10)" in second


def test_tuning_report_of_a_density_method_with_no_dbcv_at_all_says_so(tmp_path):
    results = _density_results().assign(dbcv=np.nan, n_clusters_found=0.0)

    assert "- **DBCV**: mai definito" in tuning_report_markdown(tmp_path / "run", "hdbscan", Path("matrix"), results)


def test_tuning_report_of_hdbscan_links_the_heatmap_and_the_curves_only_when_they_exist(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    report = tuning_report_markdown(run_dir, "hdbscan", Path("matrix"), _density_results())
    assert "tuning_plot" not in report and "dbcv_curves" not in report

    (run_dir / "tuning_plot.png").write_bytes(b"png")
    (run_dir / "dbcv_curves.png").write_bytes(b"png")
    report = tuning_report_markdown(run_dir, "hdbscan", Path("matrix"), _density_results())

    assert report.count("(tuning_plot.png)") == 1 and report.count(_hint(HINT_HEATMAP)) == 1
    assert report.count("(dbcv_curves.png)") == 1 and report.count(_hint(HINT_DBCV_CURVES)) == 1


def test_tuning_report_links_the_dbcv_curves_per_selection_method_when_they_exist(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "dbcv_curves_cluster_selection_method=eom.png").write_bytes(b"png")

    soft = tuning_report_markdown(run_dir, "hdbscan_soft", Path("matrix"), _density_results(soft=True))

    assert soft.count("(dbcv_curves_cluster_selection_method=eom.png)") == 1 and "dbcv_curves_cluster_selection_method=leaf" not in soft
    assert soft.index("(dbcv_curves_cluster_selection_method=eom.png)") < soft.index("## cluster_selection_method = leaf")


def test_tuning_report_of_hdbscan_soft_has_a_section_per_selection_method_and_the_membership_columns(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "tuning_plot_cluster_selection_method=leaf.png").write_bytes(b"png")

    report = tuning_report_markdown(run_dir, "hdbscan_soft", Path("matrix"), _density_results(soft=True))

    assert report.index("## cluster_selection_method = eom") < report.index("## cluster_selection_method = leaf")
    assert report.count("### min_samples = 1") == 2 and report.count("### min_samples = 5") == 2
    assert "dbcv | membership_mean | persistence_mean |" in report
    assert "membership_share_below_half" not in report  # no threshold on the probability
    assert "(tuning_plot_cluster_selection_method=leaf.png)" in report and "tuning_plot_cluster_selection_method=eom.png" not in report
    assert "**`membership_mean`**" in report.split("## Termini")[1]


def test_tuning_report_of_a_density_method_rejects_a_table_without_the_density_columns(tmp_path):
    with pytest.raises(ValueError, match=r"no column\(s\) \['dbcv'\]"):
        tuning_report_markdown(tmp_path / "run", "hdbscan", Path("matrix"), _density_results().drop(columns="dbcv"))
    with pytest.raises(ValueError, match=r"no column\(s\) \['largest_cluster_share'\]"):
        tuning_report_markdown(tmp_path / "run", "hdbscan", Path("matrix"), _density_results().drop(columns="largest_cluster_share"))
    with pytest.raises(ValueError, match=r"no column\(s\) \['membership_mean'\]"):
        tuning_report_markdown(tmp_path / "run", "hdbscan_soft", Path("matrix"), _density_results(soft=True).drop(columns="membership_mean"))


def test_tuning_report_of_adp_formats_z_without_trailing_zeros(tmp_path):
    results = pd.DataFrame({"metric": ["dice"], "Z": [1.65], "silhouette": [0.03], "n_clusters_found": [30.0]})

    assert "| 1.65 | 0.030 | 30 |" in tuning_report_markdown(tmp_path / "run", "adp", Path("matrix"), results)


def test_tuning_report_rejects_a_method_without_report_and_a_missing_column(tmp_path):
    with pytest.raises(ValueError, match="no report for clustering_method 'kmeans'"):
        tuning_report_markdown(tmp_path / "run", "kmeans", Path("matrix"), _agglomerative_results())
    with pytest.raises(ValueError, match=r"no column\(s\) \['silhouette'\]"):
        _agglomerative_report(tmp_path, _agglomerative_results().drop(columns="silhouette"))


def test_require_report_evaluations_accepts_a_block_that_lists_what_the_report_reads():
    block = {"general": (), "agglomerative": ("cophenetic_correlation", "dendrogram_jump", "linkage_agreement"), "hdbscan": ("density_metrics",), "adp": ()}

    require_report_evaluations(block, ("agglomerative", "hdbscan", "adp"))


def test_require_report_evaluations_names_the_method_and_the_missing_evaluations():
    block = {"general": (), "agglomerative": ("cophenetic_correlation",)}

    with pytest.raises(ValueError, match=r"lacks \['dendrogram_jump', 'linkage_agreement'\] for 'agglomerative'"):
        require_report_evaluations(block, ("agglomerative",))


def test_require_report_evaluations_refuses_a_method_with_no_report():
    with pytest.raises(ValueError, match="'kmeans' has no report"):
        require_report_evaluations({"general": (), "kmeans": ()}, ("kmeans",))


def test_the_agglomerative_report_says_calinski_harabasz_and_davies_bouldin_are_undefined_for_a_non_euclidean_metric(tmp_path):
    report = _agglomerative_report(tmp_path, _agglomerative_results())

    cosine = report.split("## metric = cosine")[1]
    assert "non sono definiti per `cosine`" in cosine.split("###")[0]
    assert "non sono definiti" not in report.split("## metric = cosine")[0]
