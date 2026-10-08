"""Unit tests for src/analysis/cluster_composition.py."""

import logging

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.analysis.cluster_composition import (
    COMPOSITION_VARIABLES,
    CompositionVariable,
    build_composition_figure,
    cluster_colors,
    composition_frame,
)

_REGISTRY_COLUMNS = ["subject_id", "original_id", "dataset", "disease_id", "has_lesion", "has_sdc", "has_features"]
_EXTRA_COLUMNS = ["lesion_side", "NIHSS", "lesion_volume_voxels_2mm", "disconnection_load_voxels_2mm", "location_dominant_2mm"]


def _write_registry(metadata_root, rows, extra_columns=_EXTRA_COLUMNS):
    metadata_root.mkdir(parents=True, exist_ok=True)
    lines = [",".join([*_REGISTRY_COLUMNS, *extra_columns])] + [",".join(r) for r in rows]
    (metadata_root / "participants.csv").write_text("\n".join(lines) + "\n")


@pytest.fixture
def _registry_root(tmp_path, monkeypatch):
    from src.utils import participants as participants_registry

    root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def _row(subject_id, dataset, side, nihss, volume, load, location):
    return [subject_id, subject_id, dataset, "ST", "True", "True", "False", side, nihss, volume, load, location]


def _frame() -> pd.DataFrame:
    return pd.DataFrame({
        "subject_id": ["a", "b", "c", "d"],
        "cluster_label": [0, 0, 1, 1],
        "dataset": ["X", "Y", "X", "X"],
        "lesion_side": ["left", "left", "right", "both"],
        "location_dominant": ["cortex_only", "white_matter_only", "cortex_only", "cortex_only"],
        "nihss": [1.0, 5.0, 10.0, None],
        "lesion_volume": [100.0, 1000.0, 5000.0, 20000.0],
        "disconnection_load": [10.0, 20.0, 30.0, 40.0],
    })


def test_composition_frame_joins_every_variable_from_the_registry(_registry_root):
    _write_registry(_registry_root, [
        _row("sub-STUNIPD0001", "UNIPD/WashU", "left", "5.0", "1000", "20000.5", "cortex_only"),
        _row("sub-STUNIPD0002", "UKLFR/stroke_UKLFR", "right", "10.0", "2000", "30000.5", "white_matter_only"),
    ])
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0002", "sub-STUNIPD0001"], "cluster_label": [1, 0]})

    frame, unregistered = composition_frame(metadata)

    assert unregistered == []
    assert list(frame["subject_id"]) == ["sub-STUNIPD0002", "sub-STUNIPD0001"]  # metadata's order, not the registry's
    first = frame.set_index("subject_id").loc["sub-STUNIPD0001"]
    assert first["dataset"] == "UNIPD/WashU"
    assert first["lesion_side"] == "left"
    assert first["nihss"] == pytest.approx(5.0)
    assert first["lesion_volume"] == pytest.approx(1000.0)
    assert first["disconnection_load"] == pytest.approx(20000.5)
    assert first["location_dominant"] == "cortex_only"


def test_composition_frame_keeps_an_unregistered_subject_as_missing_and_warns(_registry_root, caplog):
    _write_registry(_registry_root, [_row("sub-STUNIPD0001", "UNIPD/WashU", "left", "5.0", "1000", "20000.5", "cortex_only")])
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0099"], "cluster_label": [0, 0]})

    with caplog.at_level(logging.WARNING):
        frame, unregistered = composition_frame(metadata)

    assert unregistered == ["sub-STUNIPD0099"]
    assert len(frame) == 2
    assert pd.isna(frame.set_index("subject_id").loc["sub-STUNIPD0099", "nihss"])
    assert "sub-STUNIPD0099" in caplog.text


def test_composition_frame_raises_without_cluster_labels(_registry_root):
    _write_registry(_registry_root, [])

    with pytest.raises(ValueError, match="not a clustering run"):
        composition_frame(pd.DataFrame({"subject_id": ["a"]}))


def test_composition_frame_raises_when_the_registry_lacks_a_column(_registry_root):
    _write_registry(_registry_root, [_row("a", "X", "left", "5.0", "1000", "1", "cortex_only")[:8]], extra_columns=["lesion_side"])

    with pytest.raises(ValueError, match="enrich_metadata"):
        composition_frame(pd.DataFrame({"subject_id": ["a"], "cluster_label": [0]}))


def test_categorical_figure_has_one_stacked_percent_bar_trace_per_category():
    variable = next(v for v in COMPOSITION_VARIABLES if v.name == "lesion_side")

    figure = build_composition_figure(_frame(), variable)

    assert [trace.name for trace in figure.data] == ["left", "right", "both"]  # the closed order, not alphabetical
    assert all(isinstance(trace, go.Bar) and trace.orientation == "h" for trace in figure.data)
    assert figure.layout.barnorm == "percent"
    counts = {trace.name: list(trace.x) for trace in figure.data}
    assert counts == {"left": [2, 0], "right": [0, 1], "both": [0, 1]}


def test_categorical_figure_rejects_a_value_outside_the_closed_vocabulary():
    frame = _frame()
    frame.loc[0, "lesion_side"] = "middle"
    variable = next(v for v in COMPOSITION_VARIABLES if v.name == "lesion_side")

    with pytest.raises(ValueError, match="middle"):
        build_composition_figure(frame, variable)


def test_continuous_figure_has_one_box_per_cluster_in_its_scatter_color():
    variable = next(v for v in COMPOSITION_VARIABLES if v.name == "disconnection_load")
    frame = _frame()

    figure = build_composition_figure(frame, variable)

    assert [trace.name for trace in figure.data] == ["0", "1"]
    assert all(isinstance(trace, go.Box) for trace in figure.data)
    colors = cluster_colors(frame)
    assert [trace.line.color for trace in figure.data] == [colors[0], colors[1]]


def test_the_title_reports_how_many_subjects_have_the_value():
    variable = next(v for v in COMPOSITION_VARIABLES if v.name == "nihss")

    figure = build_composition_figure(_frame(), variable)

    assert "n=3/4" in figure.layout.title.text  # one NIHSS is missing


def test_a_log_scale_variable_draws_a_log_axis_and_the_others_do_not():
    log_variable = next(v for v in COMPOSITION_VARIABLES if v.name == "lesion_volume")
    linear_variable = next(v for v in COMPOSITION_VARIABLES if v.name == "nihss")

    assert log_variable.log_scale
    assert build_composition_figure(_frame(), log_variable).layout.yaxis.type == "log"
    assert build_composition_figure(_frame(), linear_variable).layout.yaxis.type == "linear"


def test_a_noise_cluster_gets_the_neutral_gray_like_in_the_scatter():
    frame = _frame().assign(cluster_label=[-1, -1, 0, 0])

    colors = cluster_colors(frame)

    assert set(colors) == {-1, 0}
    assert colors[-1] != colors[0]


def test_custom_variable_without_category_order_sorts_its_categories():
    variable = CompositionVariable("dataset", "Dataset", "categorical", "dataset")

    figure = build_composition_figure(_frame(), variable)

    assert [trace.name for trace in figure.data] == ["X", "Y"]
