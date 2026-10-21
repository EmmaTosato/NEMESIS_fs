"""Property tests for src/analysis/cluster_quality.py (le due figure del pannello "Valutazione del clustering").

Le figure sono dati prima che pixel: ogni proprietà qui sotto è su ciò che le figure contengono
(valori, ordine, etichette, linea della media), per tabelle di forma arbitraria.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from src.analysis.cluster_quality import build_mean_membership_figure, build_silhouette_figure
from src.analysis.plotting import _palette_for_labels


_fast = settings(max_examples=12)  # costruire una figura plotly costa ~30 ms


@st.composite
def silhouette_tables(draw, min_clusters=1, max_clusters=12):
    labels = draw(st.lists(st.integers(0, 40), min_size=min_clusters, max_size=max_clusters, unique=True))
    count = len(labels)
    return pd.DataFrame(
        {
            "n": draw(st.lists(st.integers(1, 500), min_size=count, max_size=count)),
            "silhouette_mean": draw(st.lists(st.floats(-1, 1, allow_nan=False), min_size=count, max_size=count)),
            "share_negative": draw(st.lists(st.floats(0, 1, allow_nan=False), min_size=count, max_size=count)),
        },
        index=labels,
    )


# --- build_silhouette_figure ---------------------------------------------------------------------------------


@_fast
@given(table=silhouette_tables())
def test_the_bars_are_the_clusters_in_ascending_label_order_with_their_own_values(table):
    figure = build_silhouette_figure(table)

    ordered = table.sort_index()
    bar = figure.data[0]
    assert list(bar.y) == [f"{label} · n={n}" for label, n in zip(ordered.index, ordered["n"])]
    np.testing.assert_array_equal(np.asarray(bar.x), ordered["silhouette_mean"].to_numpy())
    np.testing.assert_allclose([row[1] for row in bar.customdata], ordered["share_negative"].to_numpy() * 100)
    assert [row[0] for row in bar.customdata] == list(ordered["n"])


@_fast
@given(table=silhouette_tables(), data=st.data())
def test_the_figure_does_not_depend_on_the_order_of_the_rows_of_the_table(table, data):
    shuffled = table.iloc[list(data.draw(st.permutations(range(len(table)))))]

    a, b = build_silhouette_figure(table), build_silhouette_figure(shuffled)

    assert list(a.data[0].y) == list(b.data[0].y)
    np.testing.assert_array_equal(np.asarray(a.data[0].x), np.asarray(b.data[0].x))
    assert list(a.data[0].marker.color) == list(b.data[0].marker.color)
    assert a.layout.shapes[0].x0 == pytest.approx(b.layout.shapes[0].x0)


@_fast
@given(table=silhouette_tables())
def test_the_average_line_is_the_size_weighted_mean_and_lies_inside_the_range_of_the_bars(table):
    """Media sui soggetti (pesata per n), non media delle barre; sta sempre fra la barra minima e la massima."""
    figure = build_silhouette_figure(table)

    (line,) = figure.layout.shapes
    expected = float((table["silhouette_mean"] * table["n"]).sum() / table["n"].sum())
    assert line.x0 == line.x1 == pytest.approx(expected)
    assert table["silhouette_mean"].min() - 1e-12 <= line.x0 <= table["silhouette_mean"].max() + 1e-12
    assert f"{expected:.2f}" in figure.layout.annotations[0].text


@_fast
@given(table=silhouette_tables(), factor=st.integers(2, 9))
def test_multiplying_every_cluster_size_by_a_constant_does_not_move_the_average_line(table, factor):
    scaled = table.assign(n=table["n"] * factor)

    assert build_silhouette_figure(scaled).layout.shapes[0].x0 == pytest.approx(build_silhouette_figure(table).layout.shapes[0].x0)


@_fast
@given(table=silhouette_tables())
def test_the_axis_is_the_full_silhouette_range_and_the_height_grows_with_the_clusters(table):
    figure = build_silhouette_figure(table)

    assert tuple(figure.layout.xaxis.range) == (-1, 1)
    bigger = build_silhouette_figure(pd.concat([table, table.rename(index=lambda label: label + 100)]))
    assert bigger.layout.height > figure.layout.height


@_fast
@given(table=silhouette_tables())
def test_every_cluster_gets_the_color_of_the_scatter_palette(table):
    figure = build_silhouette_figure(table)

    labels = sorted(int(label) for label in table.index)
    palette = _palette_for_labels(labels)
    assert list(figure.data[0].marker.color) == [palette[label] for label in labels]


@pytest.mark.parametrize("column", ["n", "silhouette_mean", "share_negative"])
@_fast
@given(table=silhouette_tables())
def test_a_missing_required_column_raises_naming_it(column, table):
    with pytest.raises(ValueError, match=column):
        build_silhouette_figure(table.drop(columns=column))


@_fast
@given(table=silhouette_tables())
def test_extra_columns_do_not_change_the_figure(table):
    extended = table.assign(extra=1.0)

    a, b = build_silhouette_figure(table), build_silhouette_figure(extended)

    assert list(a.data[0].y) == list(b.data[0].y)
    np.testing.assert_array_equal(np.asarray(a.data[0].x), np.asarray(b.data[0].x))


def test_a_single_cluster_is_drawn_and_the_average_is_its_own_silhouette():
    table = pd.DataFrame({"n": [7], "silhouette_mean": [0.25], "share_negative": [0.0]}, index=[3])

    figure = build_silhouette_figure(table)

    assert list(figure.data[0].y) == ["3 · n=7"]
    assert figure.layout.shapes[0].x0 == pytest.approx(0.25)


def test_a_table_with_no_subjects_at_all_is_refused_not_drawn_with_a_nan_average_line():
    table = pd.DataFrame({"n": [0, 0], "silhouette_mean": [0.1, 0.2], "share_negative": [0.0, 0.0]}, index=[0, 1])

    with pytest.raises(ValueError, match="n=0"):
        build_silhouette_figure(table)


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
