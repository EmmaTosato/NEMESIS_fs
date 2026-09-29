"""Unit tests for src/analysis/cluster_description.py."""

import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from src.analysis.cluster_description import (
    CLUSTER_DESCRIPTION_VARIABLES,
    build_cluster_description_figure,
    cluster_composition,
    clusters_comparison_stats,
    variable_summary,
)

_REGISTRY_COLUMNS = ["subject_id", "original_id", "dataset", "disease_id", "has_lesion", "has_sdc", "has_features"]


def _write_registry(metadata_root, rows, extra_columns):
    """Same shape as tests/unit/test_embedding_coloring.py's own _write_registry - a minimal
    assets/metadata/participants.csv with only the columns a given test needs."""
    metadata_root.mkdir(parents=True, exist_ok=True)
    header = [*_REGISTRY_COLUMNS, *extra_columns]
    lines = [",".join(header)] + [",".join(r) for r in rows]
    (metadata_root / "participants.csv").write_text("\n".join(lines) + "\n")


@pytest.fixture
def _registry_root(tmp_path, monkeypatch):
    from src.utils import participants as participants_registry

    root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def _base_row(subject_id, dataset="UNIPD/WashU"):
    return [subject_id, subject_id, dataset, "ST", "True", "True", "False"]


def test_cluster_composition_joins_registry_for_cluster_subjects(_registry_root):
    _write_registry(
        _registry_root,
        [
            [*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "5.0", "1000"],
            [*_base_row("sub-STUNIPD0002"), "70.0", "M", "16.0", "10.0", "2000"],
            [*_base_row("sub-STUNIPD0003"), "80.0", "F", "8.0", "3.0", "3000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({
        "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
        "cluster_label": [0, 0, 1],
    })

    composition, unregistered = cluster_composition(metadata, 0)

    assert unregistered == []
    assert set(composition["subject_id"]) == {"sub-STUNIPD0001", "sub-STUNIPD0002"}
    assert composition.set_index("subject_id").loc["sub-STUNIPD0001", "age"] == pytest.approx(60.0)
    assert composition.set_index("subject_id").loc["sub-STUNIPD0002", "sex"] == "M"
    assert composition.set_index("subject_id").loc["sub-STUNIPD0002", "lesion_volume_voxels"] == pytest.approx(2000.0)


def test_cluster_composition_raises_on_empty_cluster(_registry_root):
    _write_registry(_registry_root, [[*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "5.0", "1000"]],
                     ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"])
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001"], "cluster_label": [0]})

    with pytest.raises(ValueError, match="99"):
        cluster_composition(metadata, 99)


def test_cluster_composition_reports_unregistered_subjects_instead_of_raising(_registry_root, caplog):
    """29-09-26 regression (behaviour change, on request): a subject of the cluster with no row
    in participants.csv used to raise ValueError, killing the whole panel for the cluster. It is
    now reported - returned to the caller AND logged at WARNING - and the other subjects are
    still described."""
    _write_registry(_registry_root, [[*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "5.0", "1000"]],
                     ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"])
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD9999"], "cluster_label": [0, 0]})

    with caplog.at_level(logging.WARNING):
        composition, unregistered = cluster_composition(metadata, 0)

    assert unregistered == ["sub-STUNIPD9999"]
    assert "sub-STUNIPD9999" in caplog.text
    # The registered subject is still fully described...
    assert composition.set_index("subject_id").loc["sub-STUNIPD0001", "age"] == pytest.approx(60.0)
    # ...and the unregistered one is KEPT as an all-missing row, not dropped, so n_total stays
    # the cluster's true size (the denominator this panel's whole contract rests on).
    assert len(composition) == 2
    age = next(v for v in CLUSTER_DESCRIPTION_VARIABLES if v.name == "age")
    sex = next(v for v in CLUSTER_DESCRIPTION_VARIABLES if v.name == "sex")
    assert variable_summary(composition, age)["n_available"] == 1
    assert variable_summary(composition, age)["n_total"] == 2
    assert variable_summary(composition, sex)["n_available"] == 1
    assert variable_summary(composition, sex)["n_total"] == 2
    assert variable_summary(composition, sex)["counts"] == {"F": 1}


def test_cluster_composition_figure_builds_with_unregistered_subjects(_registry_root):
    """The all-missing row must not break the figure either (a Box over an empty/partial series,
    a Bar over counts that exclude it) - the panel's real end-to-end path for this case."""
    _write_registry(_registry_root, [[*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "5.0", "1000"]],
                     ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"])
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD9999"], "cluster_label": [0, 0]})

    composition, _unregistered = cluster_composition(metadata, 0)

    assert isinstance(build_cluster_description_figure(composition, 0), go.Figure)


def test_variable_summary_continuous_reports_coverage_and_stats():
    variable = next(v for v in CLUSTER_DESCRIPTION_VARIABLES if v.name == "age")
    composition = pd.DataFrame({"subject_id": ["a", "b", "c"], "age": [60.0, 70.0, np.nan]})

    summary = variable_summary(composition, variable)

    assert summary["n_available"] == 2
    assert summary["n_total"] == 3
    assert summary["mean"] == pytest.approx(65.0)
    assert summary["median"] == pytest.approx(65.0)
    assert summary["min"] == pytest.approx(60.0)
    assert summary["max"] == pytest.approx(70.0)


def test_variable_summary_categorical_counts_and_treats_empty_as_missing():
    variable = next(v for v in CLUSTER_DESCRIPTION_VARIABLES if v.name == "sex")
    composition = pd.DataFrame({"subject_id": ["a", "b", "c", "d"], "sex": ["F", "M", "F", ""]})

    summary = variable_summary(composition, variable)

    assert summary["n_available"] == 3
    assert summary["n_total"] == 4
    assert summary["counts"] == {"F": 2, "M": 1}


def test_build_cluster_description_figure_has_one_trace_per_variable():
    composition = pd.DataFrame({
        "subject_id": ["a", "b"],
        "age": [60.0, 70.0],
        "sex": ["F", "M"],
        "education": [12.0, np.nan],
        "nihss": [5.0, 8.0],
        "lesion_volume_voxels": [1000.0, 2000.0],
    })

    figure = build_cluster_description_figure(composition, 0)

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == len(CLUSTER_DESCRIPTION_VARIABLES)
    # "sex" is the only categorical variable - its trace is a Bar, every other one a Box.
    assert sum(isinstance(trace, go.Bar) for trace in figure.data) == 1
    assert sum(isinstance(trace, go.Box) for trace in figure.data) == 4


def test_clusters_comparison_stats_covers_every_cluster_in_label_order(_registry_root):
    """29-09-26, on request: one entry per cluster, ascending, each carrying the same
    variable_summary dicts the single-cluster figure is drawn from."""
    _write_registry(
        _registry_root,
        [
            [*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "4.0", "1000"],
            [*_base_row("sub-STUNIPD0002"), "70.0", "M", "16.0", "8.0", "2000"],
            [*_base_row("sub-STUNIPD0003"), "80.0", "M", "8.0", "12.0", "3000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({
        "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
        "cluster_label": [1, 0, 0],
    })

    stats = clusters_comparison_stats(metadata)

    assert [s.cluster_label for s in stats] == [0, 1]
    assert [s.n_total for s in stats] == [2, 1]
    assert stats[0].summaries["age"]["mean"] == pytest.approx(75.0)
    assert stats[0].summaries["sex"]["counts"] == {"M": 2}
    assert stats[1].summaries["age"]["mean"] == pytest.approx(60.0)
    # std of a single value does not exist - None, never 0.0 (which would read as "no spread").
    assert stats[1].summaries["age"]["std"] is None


def test_clusters_comparison_stats_agrees_with_cluster_composition_for_the_same_cluster(_registry_root):
    """The table and the figure must never disagree: both go through variable_summary over the
    same join, so every stat for a given cluster is identical whichever way it was reached."""
    _write_registry(
        _registry_root,
        [
            [*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "4.0", "1000"],
            [*_base_row("sub-STUNIPD0002"), "70.0", "M", "16.0", "8.0", "2000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"], "cluster_label": [0, 0]})

    composition, _unregistered = cluster_composition(metadata, 0)
    stats = clusters_comparison_stats(metadata)

    for variable in CLUSTER_DESCRIPTION_VARIABLES:
        assert stats[0].summaries[variable.name] == variable_summary(composition, variable)


def test_clusters_comparison_stats_counts_unregistered_subjects_per_cluster(_registry_root):
    """n_total stays the cluster's true size and n_unregistered says how much of it the registry
    can't describe - the table's own version of the figure's n_available/n_total contract."""
    _write_registry(_registry_root, [[*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "4.0", "1000"]],
                     ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"])
    metadata = pd.DataFrame({
        "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD9998", "sub-STUNIPD9999"],
        "cluster_label": [0, 0, 1],
    })

    stats = {s.cluster_label: s for s in clusters_comparison_stats(metadata)}

    assert (stats[0].n_total, stats[0].n_unregistered) == (2, 1)
    assert (stats[1].n_total, stats[1].n_unregistered) == (1, 1)
    assert stats[1].summaries["age"]["n_available"] == 0


def test_clusters_comparison_stats_raises_without_a_cluster_label_column(_registry_root):
    _write_registry(_registry_root, [[*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "4.0", "1000"]],
                     ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"])
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001"]})

    with pytest.raises(ValueError, match="cluster_label"):
        clusters_comparison_stats(metadata)


def test_build_cluster_description_figure_lays_out_three_per_row_with_readable_type(_registry_root):
    """29-09-26 feedback ("label e assi così piccoli"): the 5 variables must not sit in one row
    of 5 (~200px each at the app's width). 3 per row, the unused trailing cell hidden rather
    than drawn as an empty framed subplot, and no axis type left at Plotly's small defaults."""
    _write_registry(
        _registry_root,
        [
            [*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "4.0", "1000"],
            [*_base_row("sub-STUNIPD0002"), "70.0", "M", "16.0", "8.0", "2000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"], "cluster_label": [0, 0]})
    composition, _unregistered = cluster_composition(metadata, 0)

    figure = build_cluster_description_figure(composition, 0, color="#e87ba4")

    layout = figure.layout.to_plotly_json()
    widths = {round(layout[k]["domain"][1] - layout[k]["domain"][0], 3)
              for k in layout if k.startswith("xaxis") and "domain" in layout[k]}
    assert widths == {0.273}  # 3 columns, not 5
    assert layout["xaxis6"]["visible"] is False and layout["yaxis6"]["visible"] is False
    assert {a.font.size for a in figure.layout.annotations} == {17}
    assert "#e87ba4" in figure.layout.title.text and "2 soggetti" in figure.layout.title.text
    # Bold heading, pinned to the top with a wide margin under it (29-09-26 feedback).
    assert figure.layout.title.text.startswith("<b>")
    assert figure.layout.margin.t >= 150

    # Coverage belongs to the subplot TITLE, not the x-axis title: under the categorical
    # subplot the F/M tick labels push an axis title lower than under the box plots, which
    # have none, leaving the five n= figures on two different baselines. Regression guard for
    # that specific misalignment (29-09-26, caught by rendering the figure and looking at it).
    titles = [a.text for a in figure.layout.annotations]
    assert all("n=" in t for t in titles)
    assert not any(layout[k].get("title", {}).get("text") for k in layout if k.startswith("xaxis"))


def test_every_variable_color_is_a_distinct_member_of_the_app_palette():
    """The per-variable colors (29-09-26, on request: "più varietà nei colori dato che stiamo
    plottando variabili diverse") are a hand-picked SUBSET of the app's categorical palette, in
    a hand-picked order - chosen by running the dataviz validator over candidate subsets, since
    the palette's own first 5 fail its 3:1 contrast check. That makes them exactly the kind of
    hardcoded constants that drift: this pins them to the palette they claim to come from, and
    guards against two variables silently sharing a hue when a 6th is added."""
    from src.analysis.plotting import _CATEGORICAL_PALETTE

    colors = [v.color for v in CLUSTER_DESCRIPTION_VARIABLES]
    assert len(set(colors)) == len(colors), f"two variables share a color: {colors}"
    assert set(colors) <= set(_CATEGORICAL_PALETTE), (
        f"variable color(s) not in the app palette: {sorted(set(colors) - set(_CATEGORICAL_PALETTE))}"
    )


def test_figure_marks_and_titles_use_each_variable_own_color(_registry_root):
    """Each subplot's marks and its title carry that variable's own color, and the categorical
    subplot uses ONE color for every bar rather than one per category - a single series, whose
    categories are already named by the tick labels and counted by the direct labels."""
    _write_registry(
        _registry_root,
        [
            [*_base_row("sub-STUNIPD0001"), "60.0", "F", "12.0", "4.0", "1000"],
            [*_base_row("sub-STUNIPD0002"), "70.0", "M", "16.0", "8.0", "2000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"], "cluster_label": [0, 0]})
    composition, _unregistered = cluster_composition(metadata, 0)

    figure = build_cluster_description_figure(composition, 0)

    by_name = {v.name: v for v in CLUSTER_DESCRIPTION_VARIABLES}
    titles = [a.text for a in figure.layout.annotations]
    for variable in CLUSTER_DESCRIPTION_VARIABLES:
        assert any(variable.color in t and variable.label in t for t in titles), variable.name

    box_colors = {t.line.color for t in figure.data if isinstance(t, go.Box)}
    assert box_colors == {v.color for v in CLUSTER_DESCRIPTION_VARIABLES if v.kind == "continuous"}

    bar = next(t for t in figure.data if isinstance(t, go.Bar))
    assert bar.marker.line.color == by_name["sex"].color
    # One fill for the whole trace, not a per-category list.
    assert isinstance(bar.marker.color, str)


def test_rgba_rejects_a_non_hex_color():
    """_rgba derives every pale fill from a variable's single declared color - a malformed one
    must fail loudly, not produce a silently broken rgba() string the browser ignores."""
    from src.analysis.cluster_description import _rgba

    assert _rgba("#1a6bab", 0.5) == "rgba(26,107,171,0.5)"
    with pytest.raises(ValueError, match="rrggbb"):
        _rgba("1a6bab", 0.5)
