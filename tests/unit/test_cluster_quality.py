"""Unit tests for src/analysis/cluster_quality.py."""

import pandas as pd
import pytest

from src.analysis.cluster_composition import cluster_colors
from src.analysis.cluster_quality import build_silhouette_figure


def _clusters(index=(0, 1, 2)) -> pd.DataFrame:
    return pd.DataFrame(
        {"n": [30, 5, 120], "silhouette_mean": [0.52, -0.1, 0.33], "share_negative": [0.02, 0.6, 0.1]}, index=list(index)
    )


def test_one_horizontal_bar_per_cluster_labelled_with_its_size_on_the_full_silhouette_range():
    figure = build_silhouette_figure(_clusters())

    bar = figure.data[0]
    assert bar.orientation == "h" and list(bar.y) == ["0 · n=30", "1 · n=5", "2 · n=120"]
    assert list(bar.x) == [0.52, -0.1, 0.33]
    assert tuple(figure.layout.xaxis.range) == (-1, 1)


def test_the_bars_have_the_color_the_clusters_have_in_the_embedding_scatter():
    figure = build_silhouette_figure(_clusters(index=(0, 2, 5)))

    scatter = cluster_colors(pd.DataFrame({"cluster_label": [-1, 0, 2, 5]}))  # noise included, as in the scatter
    assert list(figure.data[0].marker.color) == [scatter[0], scatter[2], scatter[5]]


def test_the_hover_reports_the_size_and_the_share_of_negative_silhouettes():
    figure = build_silhouette_figure(_clusters())

    assert [tuple(point) for point in figure.data[0].customdata] == [(30, pytest.approx(2.0)), (5, pytest.approx(60.0)), (120, pytest.approx(10.0))]
    assert "%{customdata[1]" in figure.data[0].hovertemplate


def test_the_clusters_are_drawn_in_ascending_label_order_whatever_the_table_order():
    shuffled = _clusters().iloc[[2, 0, 1]]

    assert list(build_silhouette_figure(shuffled).data[0].y) == ["0 · n=30", "1 · n=5", "2 · n=120"]


def test_a_table_without_clusters_or_without_a_needed_column_raises():
    with pytest.raises(ValueError, match="no cluster to draw"):
        build_silhouette_figure(_clusters().iloc[0:0])
    with pytest.raises(ValueError, match="share_negative"):
        build_silhouette_figure(_clusters().drop(columns="share_negative"))
