"""Unit tests for src/analysis/cluster_quality.py."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.cluster_composition import cluster_colors
from src.analysis.cluster_quality import build_dbcv_figure, build_mean_membership_figure, build_silhouette_figure


def _subjects(index=(0, 1, 2), sizes=(30, 5, 120), means=(0.5, -0.1, 0.3)):
    """The cluster and the silhouette of each subject: clusters of the given sizes around the given silhouettes."""
    rng = np.random.default_rng(0)
    labels = np.repeat(list(index), list(sizes))
    values = np.concatenate([np.clip(rng.normal(mean, 0.15, size), -1, 1) for mean, size in zip(means, sizes)])
    return labels, values


def _heights(figure) -> list[float]:
    return [axis.domain[1] - axis.domain[0] for axis in figure.select_yaxes()]


def test_one_panel_per_cluster_with_its_subjects_sorted_from_the_largest_silhouette_at_the_top():
    labels, values = _subjects()

    figure = build_silhouette_figure(labels, values)

    assert len(figure.data) == 3
    for trace, cluster, size in zip(figure.data, (0, 1, 2), (30, 5, 120)):
        expected = np.sort(values[labels == cluster])[::-1]
        np.testing.assert_array_equal(np.asarray(trace.x), expected)
        assert list(trace.y) == list(range(size))[::-1]  # the largest silhouette has the highest y: it is drawn on top
        assert trace.fill == "tozerox"


def test_every_panel_is_on_the_full_silhouette_range_and_the_axis_is_shared():
    figure = build_silhouette_figure(*_subjects())

    assert all(tuple(axis.range) == (-1, 1) for axis in figure.select_xaxes())
    assert [axis.title.text for axis in figure.select_xaxes()] == [None, None, "silhouette"]  # only the bottom one is titled


def test_the_panels_have_the_color_the_clusters_have_in_the_embedding_scatter():
    figure = build_silhouette_figure(*_subjects(index=(0, 2, 5)))

    scatter = cluster_colors(pd.DataFrame({"cluster_label": [-1, 0, 2, 5]}))  # noise included, as in the scatter
    assert [trace.fillcolor for trace in figure.data] == [scatter[0], scatter[2], scatter[5]]


def test_a_dashed_line_marks_the_mean_over_all_subjects_in_every_panel():
    labels, values = _subjects()  # the clusters are very different in size: the mean of the means is another number

    figure = build_silhouette_figure(labels, values)

    assert len(figure.layout.shapes) == 3
    for line in figure.layout.shapes:
        assert line.x0 == line.x1 == pytest.approx(values.mean()) and line.line.dash == "dash"
        assert line.opacity == 1  # simple_white gives every shape 0.3 opacity: the line would be nearly invisible
    assert f"{values.mean():.2f}" in figure.layout.annotations[-1].text
    cluster_means = [values[labels == cluster].mean() for cluster in (0, 1, 2)]
    assert abs(values.mean() - np.mean(cluster_means)) > 0.05


def test_a_panel_is_as_tall_as_its_cluster_is_large_with_a_floor_for_a_tiny_one():
    heights = _heights(build_silhouette_figure(*_subjects()))  # 30, 5 and 120 subjects: shares 0.19, 0.03, 0.77

    assert heights[2] / heights[0] == pytest.approx(120 / 30, rel=0.01)
    assert heights[1] / heights[0] == pytest.approx(0.05 / (30 / 155), rel=0.01)  # 5 subjects get the 5% floor, not 3%


def test_each_panel_is_named_after_its_cluster_and_the_hover_gives_the_size_and_the_silhouette():
    figure = build_silhouette_figure(*_subjects())

    assert [a.text for a in figure.layout.annotations[:3]] == ["cluster 0", "cluster 1", "cluster 2"]
    assert "cluster 2 · 120 subjects" in figure.data[2].hovertemplate and "%{x:.3f}" in figure.data[2].hovertemplate


def test_the_clusters_are_drawn_in_ascending_label_order_whatever_the_order_of_the_subjects():
    labels, values = _subjects()
    shuffled = np.random.default_rng(1).permutation(len(labels))

    a, b = build_silhouette_figure(labels, values), build_silhouette_figure(labels[shuffled], values[shuffled])

    assert [list(t.x) for t in a.data] == [list(t.x) for t in b.data]
    assert [x.text for x in a.layout.annotations] == [x.text for x in b.layout.annotations]


def test_nothing_to_draw_or_unusable_values_raise():
    labels, values = _subjects()
    with pytest.raises(ValueError, match="no subject to draw"):
        build_silhouette_figure(labels[:0], values[:0])
    with pytest.raises(ValueError, match="same length"):
        build_silhouette_figure(labels, values[:-1])
    with pytest.raises(ValueError, match="not a finite number"):
        build_silhouette_figure(labels, np.where(np.arange(len(values)) == 3, np.nan, values))


def _mean_vectors(with_noise=True) -> pd.DataFrame:
    rows = {0: [0.9, 0.1], 1: [0.2, 0.8]}
    if with_noise:
        rows[-1] = [0.05, 0.1]
    return pd.DataFrame.from_dict(rows, orient="index", columns=[0, 1])


def test_the_membership_heatmap_has_a_row_per_subject_cluster_and_a_noise_row_named_rumore():
    figure = build_mean_membership_figure(_mean_vectors())

    heatmap = figure.data[0]
    assert list(heatmap.y) == ["cluster 0", "cluster 1", "noise"] and list(heatmap.x) == ["cluster 0", "cluster 1"]
    assert heatmap.z.tolist() == [[0.9, 0.1], [0.2, 0.8], [0.05, 0.1]]
    assert (heatmap.zmin, heatmap.zmax) == (0, 1)  # a probability, whatever the matrix happens to contain


def test_the_membership_heatmap_without_noise_has_no_noise_row():
    assert list(build_mean_membership_figure(_mean_vectors(with_noise=False)).data[0].y) == ["cluster 0", "cluster 1"]


def test_the_membership_heatmap_rejects_an_empty_table():
    with pytest.raises(ValueError, match="no cluster to draw"):
        build_mean_membership_figure(_mean_vectors().iloc[0:0])


def _dbcv_clusters():
    return pd.DataFrame({"n": [100, 40, 15], "dbcv": [0.72, -0.1, 0.38]}, index=pd.Index([0, 1, 2], name="cluster"))


def test_the_dbcv_figure_has_a_bar_per_cluster_with_its_size_and_a_line_at_the_runs_score():
    figure = build_dbcv_figure(_dbcv_clusters(), 0.227)

    bar = figure.data[0]
    assert list(bar.x) == pytest.approx([0.72, -0.1, 0.38])
    assert list(bar.y) == ["cluster 0  (n=100)", "cluster 1  (n=40)", "cluster 2  (n=15)"]
    assert [line.x0 for line in figure.layout.shapes if line.line.dash == "dash"] == [0.227]  # the run's score, not the mean of the bars
    assert tuple(figure.layout.xaxis.range) == (-1, 1)


def test_the_dbcv_figure_refuses_nothing_to_draw_and_a_score_that_is_not_a_number():
    with pytest.raises(ValueError, match="no cluster"):
        build_dbcv_figure(_dbcv_clusters().iloc[:0], 0.1)
    with pytest.raises(ValueError, match="not a finite"):
        build_dbcv_figure(_dbcv_clusters().assign(dbcv=[0.1, np.nan, 0.2]), 0.1)
