"""Unit tests for src/analysis/cluster_comparison.py."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from src.analysis.cluster_comparison import (
    AGREEMENT_METRICS,
    agreement_level,
    agreement_metrics,
    align_runs,
    build_table_heatmap,
    centroid_distances,
    chi_square_independence,
    cluster_centroids,
    cluster_name,
    contingency_tables,
    purity_table,
)


def _metadata(subjects, labels):
    return pd.DataFrame({"subject_id": subjects, "cluster_label": labels})


def test_align_runs_keeps_the_common_subjects_in_the_order_of_run_a():
    metadata_a = _metadata(["s1", "s2", "s3", "s4"], [0, 0, 1, 1])
    metadata_b = _metadata(["s4", "s2", "s9"], [5, 6, 7])

    aligned = align_runs(metadata_a, metadata_b)

    assert aligned.subject_ids.tolist() == ["s2", "s4"]
    assert aligned.labels_a.tolist() == [0, 1]
    assert aligned.labels_b.tolist() == [6, 5]
    assert aligned.positions_a.tolist() == [1, 3]
    assert aligned.positions_b.tolist() == [1, 0]
    assert (aligned.n_a, aligned.n_b, aligned.n_common) == (4, 3, 2)
    assert (aligned.n_only_a, aligned.n_only_b) == (2, 1)


def test_align_runs_with_no_common_subject_raises():
    with pytest.raises(ValueError, match="empty"):
        align_runs(_metadata(["s1"], [0]), _metadata(["s2"], [0]))


def test_align_runs_rejects_a_repeated_subject_id():
    with pytest.raises(ValueError, match="duplicate subject_id"):
        align_runs(_metadata(["s1", "s1"], [0, 1]), _metadata(["s1"], [0]))


def test_align_runs_rejects_metadata_without_cluster_labels():
    with pytest.raises(ValueError, match="not a clustering run"):
        align_runs(pd.DataFrame({"subject_id": ["s1"]}), _metadata(["s1"], [0]))


def test_contingency_tables_counts_and_percentages():
    tables = contingency_tables(np.array([0, 0, 0, 1]), np.array([0, 0, 1, 1]))

    assert tables.counts.to_numpy().tolist() == [[2, 1], [0, 1]]
    assert tables.row_pct.sum(axis=1).to_numpy() == pytest.approx([100.0, 100.0])
    assert tables.col_pct.sum(axis=0).to_numpy() == pytest.approx([100.0, 100.0])
    assert tables.row_pct.loc[0, 0] == pytest.approx(200 / 3)
    assert tables.col_pct.loc[0, 1] == pytest.approx(50.0)


def test_identical_partitions_with_renamed_labels_agree_perfectly():
    labels = np.array([0, 0, 1, 1, 2, 2])

    metrics = agreement_metrics(labels, np.array([2, 2, 0, 0, 1, 1]))

    assert list(metrics) == list(AGREEMENT_METRICS)
    assert all(value == pytest.approx(1.0) for value in metrics.values())


def test_a_finer_than_b_gives_full_homogeneity_and_partial_completeness():
    # Every cluster of A sits inside one cluster of B, but B's clusters are split by A.
    labels_a = np.array([0, 1, 2, 3])
    labels_b = np.array([0, 0, 1, 1])

    metrics = agreement_metrics(labels_a, labels_b)

    assert metrics["homogeneity"] == pytest.approx(1.0)
    assert metrics["completeness"] < 1.0


def test_b_finer_than_a_swaps_homogeneity_and_completeness():
    labels_a = np.array([0, 0, 1, 1])
    labels_b = np.array([0, 1, 2, 3])

    metrics = agreement_metrics(labels_a, labels_b)

    assert metrics["completeness"] == pytest.approx(1.0)
    assert metrics["homogeneity"] < 1.0


@pytest.mark.parametrize(
    "metric, value, expected",
    [
        ("ARI", -0.05, "debole/trascurabile"),
        ("ARI", 0.19, "debole/trascurabile"),
        ("ARI", 0.2, "moderato"),
        ("ARI", 0.55, "discreto"),
        ("ARI", 0.7, "forte"),
        ("ARI", 0.95, "quasi identiche"),
        ("NMI", 0.29, "debole/trascurabile"),
        ("NMI", 0.84, "forte"),
        ("NMI", 0.9, "quasi identiche"),
        ("homogeneity", 0.5, None),
        ("completeness", 0.5, None),
    ],
)
def test_agreement_level_follows_the_reading_scale(metric, value, expected):
    assert agreement_level(metric, value) == expected


def test_agreement_level_unknown_metric_raises():
    with pytest.raises(ValueError, match="unknown agreement metric"):
        agreement_level("kappa", 0.5)


def test_chi_square_flags_association_and_residual_signs():
    counts = pd.DataFrame([[40, 2], [3, 35]], index=[0, 1], columns=[0, 1])

    result = chi_square_independence(counts)

    assert result.p_value < 0.001
    assert result.dof == 1
    assert result.residuals.loc[0, 0] > 0 > result.residuals.loc[0, 1]


def test_chi_square_on_a_single_cluster_side_raises():
    with pytest.raises(ValueError, match="at least 2 clusters"):
        chi_square_independence(pd.DataFrame([[10, 20]], index=[0], columns=[0, 1]))


def test_purity_table_orders_from_least_to_most_pure():
    counts = pd.DataFrame([[9, 1], [5, 5], [0, 10]], index=[0, 1, 2], columns=[0, 1])

    table = purity_table(counts)

    assert table.index.tolist() == [1, 0, 2]
    assert table.loc[0, "dominant_target_cluster"] == 0
    assert table.loc[0, "purity_pct"] == pytest.approx(90.0)
    assert table.loc[2, "n_subjects"] == 10


def test_purity_of_the_transposed_table_reads_the_other_direction():
    counts = pd.DataFrame([[10, 0], [4, 6]], index=[0, 1], columns=[0, 1])

    columns_view = purity_table(counts.T)

    assert columns_view.loc[0, "purity_pct"] == pytest.approx(10 / 14 * 100)
    assert columns_view.loc[1, "dominant_target_cluster"] == 1


def test_cluster_centroids_average_each_cluster():
    centroids = cluster_centroids(np.array([[0.0, 0.0], [2.0, 2.0], [10.0, 10.0]]), np.array([0, 0, 1]))

    assert centroids.loc[0].tolist() == [1.0, 1.0]
    assert centroids.loc[1].tolist() == [10.0, 10.0]


def _same_embedding_pair():
    embedding = np.array([[0.0, 0.0], [2.0, 0.0], [10.0, 0.0], [12.0, 0.0]])
    metadata_a = _metadata(["s1", "s2", "s3", "s4"], [0, 0, 1, 1])
    # run B lists the subjects in another order and splits them differently
    order = [2, 0, 3, 1]
    metadata_b = _metadata(["s3", "s1", "s4", "s2"], [0, 0, 1, 1])
    return embedding, embedding[order], metadata_a, metadata_b


def test_centroid_distances_use_the_common_subjects_in_either_run_order():
    embedding_a, embedding_b, metadata_a, metadata_b = _same_embedding_pair()
    aligned = align_runs(metadata_a, metadata_b)

    centroids_a, centroids_b, distances = centroid_distances(embedding_a, embedding_b, aligned)

    assert centroids_a.loc[0].tolist() == [1.0, 0.0]
    assert centroids_b.loc[0].tolist() == [5.0, 0.0]  # run B's cluster 0 is {s3, s1}
    assert distances.loc[0, 0] == pytest.approx(4.0)
    assert distances.loc[1, 1] == pytest.approx(4.0)  # A1 = {s3, s4} at 11, B1 = {s4, s2} at 7


def test_centroid_distances_reject_two_different_embeddings():
    embedding_a, embedding_b, metadata_a, metadata_b = _same_embedding_pair()
    aligned = align_runs(metadata_a, metadata_b)

    with pytest.raises(ValueError, match="not in the same embedding"):
        centroid_distances(embedding_a, embedding_b + 1.0, aligned)


def test_centroid_distances_reject_different_dimensionality():
    embedding_a, embedding_b, metadata_a, metadata_b = _same_embedding_pair()
    aligned = align_runs(metadata_a, metadata_b)

    with pytest.raises(ValueError, match="not the same space"):
        centroid_distances(embedding_a, np.hstack([embedding_b, np.zeros((4, 1))]), aligned)


def test_cluster_name_labels_noise():
    assert cluster_name(-1) == "rumore"
    assert cluster_name(3) == "3"


def test_heatmap_writes_every_value_in_its_cell():
    table = pd.DataFrame([[5, 1], [0, 7]], index=[0, 1], columns=[0, 1])

    figure = build_table_heatmap(
        table, title="t", row_axis_title="A", column_axis_title="B", decimals=0
    )

    assert isinstance(figure.data[0], go.Heatmap)
    assert sorted(annotation.text for annotation in figure.layout.annotations) == ["0", "1", "5", "7"]
    assert figure.data[0].zmin == 0 and figure.data[0].zmax == 7


def test_diverging_heatmap_is_centered_on_zero():
    table = pd.DataFrame([[3.0, -1.0], [-2.0, 1.0]], index=[0, 1], columns=[0, 1])

    figure = build_table_heatmap(
        table, title="t", row_axis_title="A", column_axis_title="B", decimals=1, diverging=True
    )

    assert figure.data[0].zmin == -3.0 and figure.data[0].zmax == 3.0
