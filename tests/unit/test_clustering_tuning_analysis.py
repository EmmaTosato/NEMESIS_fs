"""Unit tests for src/analysis/clustering_tuning_analysis.py."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.clustering_tuning_analysis import (
    ClusteringTuningRun,
    UsableCriteria,
    agglomerative_analysis,
    combo_key,
    dendrogram_jump,
    density_candidates,
    k_curves_figure,
    load_clustering_tuning_run,
    noise_filtered_curves_figures,
)

CRITERIA = UsableCriteria(min_clusters=3, max_clusters=30, max_noise_fraction=0.25, max_largest_cluster_share=0.6)


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


def test_density_candidates_computes_largest_share_and_the_usable_flag(tmp_path):
    run = _density_run(tmp_path)

    candidates = density_candidates(run, CRITERIA)

    assert candidates["n_clusters_found"].tolist() == [4, 2, 3]
    assert candidates["largest_cluster_share"].tolist() == pytest.approx([0.25, 0.5, 0.8])
    # 4 clusters, 25% largest: usable; 2 clusters: too few; 3 clusters but 80% in one: too dominant
    assert candidates["usable"].tolist() == [True, False, False]


def test_density_candidates_counts_noise_in_the_denominator_of_the_largest_share(tmp_path):
    labels = np.array([0] * 6 + [1] * 4 + [-1] * 10)
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.5, "silhouette": 0.5, "davies_bouldin": 1.0}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": labels})

    candidates = density_candidates(load_clustering_tuning_run(tmp_path), CRITERIA)

    assert candidates.loc[0, "largest_cluster_share"] == pytest.approx(6 / 20)
    assert not candidates.loc[0, "usable"]  # 50% noise


def test_density_candidates_rejects_n_clusters_found_that_disagrees_with_the_labels(tmp_path):
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.5, "davies_bouldin": 1.0, "n_clusters_found": 7}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": np.repeat([0, 1], 5)})

    with pytest.raises(ValueError, match="n_clusters_found"):
        density_candidates(load_clustering_tuning_run(tmp_path), CRITERIA)


def test_density_candidates_all_noise_has_no_largest_share_and_is_not_usable(tmp_path):
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 1.0, "silhouette": np.nan, "davies_bouldin": np.nan}]
    _write_run(tmp_path, "hdbscan", rows, {"min_cluster_size=5,min_samples=5": np.full(8, -1)})

    candidates = density_candidates(load_clustering_tuning_run(tmp_path), CRITERIA)

    assert np.isnan(candidates.loc[0, "largest_cluster_share"])
    assert not candidates.loc[0, "usable"]


def test_noise_filtered_curves_with_no_combination_kept_returns_no_figure_instead_of_raising(tmp_path):
    """Regression: a run with every combination above the noise limit (UMAP euclidean, streamline) used to
    abort before candidates.csv was written, so the runs with no structure got no output at all."""
    candidates = density_candidates(_density_run(tmp_path), CRITERIA).assign(noise_fraction=0.5)

    figures, without_figure = noise_filtered_curves_figures(candidates, 0.1)

    assert figures == {}
    assert without_figure == [""]


def test_noise_filtered_curves_returns_one_figure_for_hdbscan(tmp_path):
    candidates = density_candidates(_density_run(tmp_path), CRITERIA)

    figures, without_figure = noise_filtered_curves_figures(candidates, 0.1)

    assert list(figures) == [""]
    assert without_figure == []


def test_noise_filtered_curves_returns_one_figure_per_selection_method(tmp_path):
    candidates = density_candidates(_density_run(tmp_path), CRITERIA)
    soft = pd.concat([candidates.assign(cluster_selection_method="eom"), candidates.assign(cluster_selection_method="leaf")])

    figures, without_figure = noise_filtered_curves_figures(soft, 0.1)

    assert sorted(figures) == ["eom", "leaf"]
    assert without_figure == []


def test_noise_filtered_curves_reports_the_selection_method_with_no_combination_under_the_limit(tmp_path):
    """Regression: on a real hdbscan_soft run `leaf` never goes below 15% noise, and that used to abort the
    whole analysis instead of leaving out only the figure that could not be drawn."""
    candidates = density_candidates(_density_run(tmp_path), CRITERIA)
    soft = pd.concat([candidates.assign(cluster_selection_method="eom"), candidates.assign(cluster_selection_method="leaf", noise_fraction=0.4)])

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


def test_k_curves_figure_rejects_an_unknown_metric():
    results = pd.DataFrame({"n_clusters": [2], "linkage": ["ward"], "metric": ["euclidean"], "silhouette": [0.5], "davies_bouldin": [1.0]})

    with pytest.raises(ValueError, match="no row of the run has metric='manhattan'"):
        k_curves_figure(results, "manhattan")


def test_k_curves_figure_leaves_out_single_linkage():
    results = pd.DataFrame(
        {
            "n_clusters": [2, 3, 2, 3],
            "linkage": ["ward", "ward", "single", "single"],
            "metric": ["euclidean"] * 4,
            "silhouette": [0.5, 0.4, 0.1, 0.1],
            "davies_bouldin": [1.0, 1.1, 2.0, 2.0],
        }
    )

    figure = k_curves_figure(results, "euclidean")

    assert [line.get_label() for line in figure.axes[0].get_lines()] == ["ward"]
