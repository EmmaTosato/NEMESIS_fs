"""Property tests for src/analysis/cluster_quality.py (le due figure del pannello "Valutazione del clustering").

Le figure sono dati prima che pixel: ogni proprietà qui sotto è su ciò che le figure contengono
(valori, ordine, etichette, linea della media), per tabelle di forma arbitraria.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from src.analysis.cluster_quality import build_mean_membership_figure, build_silhouette_figure
from src.analysis.plotting import _SILHOUETTE_MIN_PANEL_SHARE, _palette_for_labels


_fast = settings(max_examples=12)  # costruire una figura plotly costa ~30 ms


@st.composite
def subject_silhouettes(draw, min_clusters=1, max_clusters=10):
    """The cluster and the silhouette of each subject: 1 to 10 clusters, each with 1 to 60 subjects."""
    labels = draw(st.lists(st.integers(0, 40), min_size=min_clusters, max_size=max_clusters, unique=True))
    sizes = draw(st.lists(st.integers(1, 60), min_size=len(labels), max_size=len(labels)))
    values = draw(st.lists(st.floats(-1, 1, allow_nan=False), min_size=sum(sizes), max_size=sum(sizes)))
    return np.repeat(labels, sizes), np.asarray(values)


# --- build_silhouette_figure ---------------------------------------------------------------------------------


@_fast
@given(subjects=subject_silhouettes())
def test_there_is_one_panel_per_cluster_in_ascending_label_order_holding_exactly_its_subjects(subjects):
    labels, values = subjects

    figure = build_silhouette_figure(labels, values)

    clusters = sorted(set(labels.tolist()))
    assert [a.text for a in figure.layout.annotations[:-1]] == [f"cluster {c}" for c in clusters]
    for trace, cluster in zip(figure.data, clusters):
        np.testing.assert_array_equal(np.asarray(trace.x), np.sort(values[labels == cluster])[::-1])
    assert sum(len(trace.x) for trace in figure.data) == len(values)  # no subject lost or drawn twice


@_fast
@given(subjects=subject_silhouettes(), data=st.data())
def test_the_figure_does_not_depend_on_the_order_of_the_subjects(subjects, data):
    labels, values = subjects
    order = data.draw(st.permutations(range(len(labels))))

    a, b = build_silhouette_figure(labels, values), build_silhouette_figure(labels[order], values[order])

    assert [list(t.x) for t in a.data] == [list(t.x) for t in b.data]
    assert [t.fillcolor for t in a.data] == [t.fillcolor for t in b.data]
    assert a.layout.shapes[0].x0 == pytest.approx(b.layout.shapes[0].x0)


@_fast
@given(subjects=subject_silhouettes())
def test_the_average_line_is_the_mean_over_the_subjects_in_every_panel_and_inside_their_range(subjects):
    labels, values = subjects

    figure = build_silhouette_figure(labels, values)

    assert len(figure.layout.shapes) == len(set(labels.tolist()))
    for line in figure.layout.shapes:
        assert line.x0 == line.x1 == pytest.approx(values.mean())
        assert values.min() - 1e-12 <= line.x0 <= values.max() + 1e-12
    assert f"{values.mean():.2f}" in figure.layout.annotations[-1].text


@_fast
@given(subjects=subject_silhouettes())
def test_the_axes_are_the_full_silhouette_range_and_the_height_grows_with_the_clusters(subjects):
    labels, values = subjects

    figure = build_silhouette_figure(labels, values)

    assert all(tuple(axis.range) == (-1, 1) for axis in figure.select_xaxes())
    more = build_silhouette_figure(np.concatenate([labels, labels + 100]), np.concatenate([values, values]))
    assert more.layout.height > figure.layout.height


@_fast
@given(subjects=subject_silhouettes())
def test_the_panel_heights_follow_the_cluster_sizes_but_never_fall_below_the_floor(subjects):
    labels, values = subjects

    figure = build_silhouette_figure(labels, values)

    heights = np.array([axis.domain[1] - axis.domain[0] for axis in figure.select_yaxes()])
    shares = np.array([np.mean(labels == cluster) for cluster in sorted(set(labels.tolist()))])
    expected = np.maximum(shares, _SILHOUETTE_MIN_PANEL_SHARE)
    np.testing.assert_allclose(heights / heights.sum(), expected / expected.sum(), rtol=1e-6)


@_fast
@given(subjects=subject_silhouettes())
def test_every_cluster_gets_the_color_of_the_scatter_palette(subjects):
    labels, values = subjects

    figure = build_silhouette_figure(labels, values)

    clusters = sorted(set(labels.tolist()))
    palette = _palette_for_labels(clusters)
    assert [trace.fillcolor for trace in figure.data] == [palette[cluster] for cluster in clusters]


@_fast
@given(subjects=subject_silhouettes(), position=st.integers(0, 10_000))
def test_one_non_finite_silhouette_is_refused_not_drawn_with_a_nan_average_line(subjects, position):
    labels, values = subjects
    broken = values.copy()
    broken[position % len(broken)] = np.nan

    with pytest.raises(ValueError, match="not a finite number"):
        build_silhouette_figure(labels, broken)


def test_a_single_cluster_is_drawn_and_the_average_is_its_own():
    figure = build_silhouette_figure(np.array([3, 3, 3]), np.array([0.1, 0.4, 0.7]))

    assert len(figure.data) == 1 and figure.layout.shapes[0].x0 == pytest.approx(0.4)
    assert figure.layout.annotations[0].text == "cluster 3"


# --- build_mean_membership_figure ----------------------------------------------------------------------------


@st.composite
def membership_tables(draw):
    columns = draw(st.lists(st.integers(0, 15), min_size=1, max_size=8, unique=True))
    with_noise = draw(st.booleans())
    rows = sorted(draw(st.lists(st.integers(0, 15), min_size=1, max_size=8, unique=True)))
    index = ([-1] if with_noise else []) + rows
    values = draw(st.lists(st.lists(st.floats(0, 1, allow_nan=False), min_size=len(columns), max_size=len(columns)), min_size=len(index), max_size=len(index)))
    return pd.DataFrame(values, index=index, columns=sorted(columns))


@_fast
@given(table=membership_tables())
def test_the_heatmap_holds_the_table_unchanged_with_one_row_per_cluster_and_noise_named_rumore(table):
    heatmap = build_mean_membership_figure(table).data[0]

    np.testing.assert_array_equal(np.asarray(heatmap.z), table.to_numpy())
    assert list(heatmap.x) == [f"cluster {int(c)}" for c in table.columns]
    assert list(heatmap.y) == ["rumore" if int(label) == -1 else f"cluster {int(label)}" for label in table.index]
    assert ("rumore" in list(heatmap.y)) == (-1 in table.index)
    assert (heatmap.zmin, heatmap.zmax) == (0, 1)


@_fast
@given(table=membership_tables())
def test_the_cell_text_is_each_value_with_two_decimals(table):
    heatmap = build_mean_membership_figure(table).data[0]

    expected = [[f"{value:.2f}" for value in row] for row in table.to_numpy()]
    assert [list(row) for row in heatmap.text] == expected


@_fast
@given(table=membership_tables())
def test_the_heatmap_height_grows_with_the_number_of_rows(table):
    taller = pd.concat([table, table.rename(index=lambda label: label + 100 if label != -1 else 99)])

    assert build_mean_membership_figure(taller).layout.height > build_mean_membership_figure(table).layout.height


def test_the_heatmap_rejects_a_table_without_rows_and_one_without_columns():
    with pytest.raises(ValueError, match="no cluster to draw"):
        build_mean_membership_figure(pd.DataFrame(columns=[0, 1]))
    with pytest.raises(ValueError, match="no cluster to draw"):
        build_mean_membership_figure(pd.DataFrame(index=[0, 1]))
