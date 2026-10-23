"""Unit tests for src/analysis/cluster_overview.py."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.cluster_overview import (
    OVERVIEW_COLUMNS,
    OVERVIEW_MAP_WIDTH,
    OVERVIEW_SINGLE_MAP_WIDTH,
    build_overview_embedding_figure,
    overview_grid_plan,
)

LABELS = np.array([0, 0, 1, 1, 1, 2])
EMBEDDING = np.arange(12, dtype=float).reshape(6, 2)
TAGS = {0: "Cluster 0", 1: "Cluster 1", 2: "Cluster 2"}
COLORS = {0: "#111111", 1: "#222222", 2: "#333333"}


def _figure(order=(0, 1, 2), embedding=EMBEDDING, labels=LABELS, tags=TAGS, colors=COLORS):
    return build_overview_embedding_figure(embedding, labels, order, tags, colors)


def test_a_single_cluster_gets_one_bigger_map_and_any_other_number_two_columns():
    assert overview_grid_plan(1) == (1, OVERVIEW_SINGLE_MAP_WIDTH)
    for n_clusters in (2, 3, 7, 30):
        assert overview_grid_plan(n_clusters) == (OVERVIEW_COLUMNS, OVERVIEW_MAP_WIDTH)


def test_no_cluster_to_draw_raises():
    with pytest.raises(ValueError, match="nothing to draw"):
        overview_grid_plan(0)


def test_the_figure_has_one_trace_per_cluster_in_the_given_order_with_its_tag_and_colour():
    figure = _figure(order=(2, 0, 1))

    assert [trace.name for trace in figure.data] == ["Cluster 2", "Cluster 0", "Cluster 1"]
    assert [trace.marker.color for trace in figure.data] == ["#333333", "#111111", "#222222"]
    assert [len(trace.x) for trace in figure.data] == [1, 2, 3]
    assert figure.layout.showlegend is True


def test_the_legend_names_the_clusters_without_their_size_which_stays_in_the_hover():
    figure = _figure()

    assert all("n=" not in trace.name for trace in figure.data)
    assert [trace.hovertemplate for trace in figure.data][1].startswith("Cluster 1 (n=3)")


def test_points_are_svg_not_webgl():
    assert all(type(trace).__name__ == "Scatter" for trace in _figure().data)


def test_a_cluster_not_in_order_is_not_drawn():
    assert [trace.name for trace in _figure(order=(1,)).data] == ["Cluster 1"]


def test_a_three_component_embedding_is_refused_not_sliced():
    with pytest.raises(ValueError, match="2 components"):
        _figure(embedding=np.zeros((6, 3)))


def test_an_embedding_with_a_non_finite_point_is_refused():
    broken = EMBEDDING.copy()
    broken[2, 1] = np.nan

    with pytest.raises(ValueError, match="non-finite"):
        _figure(embedding=broken)


def test_labels_of_another_length_than_the_embedding_raise():
    with pytest.raises(ValueError, match="5 labels"):
        _figure(labels=LABELS[:-1])


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"order": (0, 0)}, "repeat"),
        ({"order": (0, 9)}, "no subject"),
        ({"tags": {0: "a", 1: "b"}}, "no tag"),
        ({"colors": {0: "#000", 1: "#111"}}, "no tag or no colour"),
    ],
)
def test_an_inconsistent_cluster_description_raises(kwargs, message):
    with pytest.raises(ValueError, match=message):
        _figure(**kwargs)


@settings(max_examples=40, deadline=None)
@given(sizes=st.lists(st.integers(1, 20), min_size=1, max_size=12))
def test_every_subject_is_drawn_exactly_once(sizes):
    labels = np.repeat(np.arange(len(sizes)), sizes)
    embedding = np.random.default_rng(0).normal(size=(len(labels), 2))
    order = list(range(len(sizes)))

    figure = build_overview_embedding_figure(
        embedding, labels, order, {i: f"Cluster {i}" for i in order}, {i: "#000000" for i in order}
    )

    assert [len(trace.x) for trace in figure.data] == sizes
