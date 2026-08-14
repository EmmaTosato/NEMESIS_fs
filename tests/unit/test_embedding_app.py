"""Unit tests for src/analysis/embedding_app.py."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from dash import dcc, html

from src.analysis.embedding_app import (
    COLOR_MODE_ORDER,
    NEUTRAL_MODE,
    NO_METRIC,
    ProductionRun,
    UndisplayableRunError,
    build_app,
    build_embedding_figure,
    discover_production_runs,
    graph_content_for,
    load_run,
    method_options,
    metric_options,
    modality_options,
    n_components_options,
    run_params,
    run_title,
    runs_for,
    runs_matching,
)
from src.utils.artifacts import save_matrix


def _make_run_dir(results_root, modality="lesion", method="umap", run_name="10-08_s1", n_dims=2, params=None):
    run_dir = results_root / modality / "dim_reduction" / "production" / method / run_name
    X = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]])[:, :n_dims] if n_dims <= 2 else np.hstack(
        [np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]]), np.zeros((4, n_dims - 2))]
    )
    metadata = pd.DataFrame(
        {
            "subject_id": ["sub-1", "sub-2", "sub-3", "sub-4"],
            "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR", "UKLFR/stroke_UKLFR"],
            "lesion_side": ["left", "right", "left", "right"],
            "lesion_volume_voxels": [100, 200, 50, 400],
            "nihss": [4.0, np.nan, 7.0, 2.0],
        }
    )
    if params is None:
        params = {"n_components": n_dims, "metric": "euclidean"}
    readme_lines = ["# test run", f"Params used: {json.dumps(params)}"]
    save_matrix(run_dir, X, metadata, readme_lines=readme_lines, overwrite=False)
    return run_dir


def test_discover_production_runs_finds_valid_runs_only(tmp_path):
    results_root = tmp_path / "results"
    _make_run_dir(results_root, modality="lesion", method="umap", run_name="run-a")
    _make_run_dir(results_root, modality="lesion", method="pca", run_name="run-b")
    # Not a valid run (no manifest.json) - a stray directory left by something else, must
    # not be picked up.
    (results_root / "lesion" / "dim_reduction" / "production" / "umap" / "not-a-run").mkdir(parents=True)

    runs = discover_production_runs(results_root)

    assert [(r.modality, r.method, r.run_name) for r in runs] == [
        ("lesion", "pca", "run-b"),
        ("lesion", "umap", "run-a"),
    ]


def test_discover_production_runs_missing_root_returns_empty_list(tmp_path):
    assert discover_production_runs(tmp_path / "does_not_exist") == []


def test_discover_production_runs_ignores_tuning_branch(tmp_path):
    results_root = tmp_path / "results"
    tuning_dir = results_root / "lesion" / "dim_reduction" / "tuning" / "umap" / "10-08_s1"
    tuning_dir.mkdir(parents=True)
    (tuning_dir / "manifest.json").write_text("{}")

    assert discover_production_runs(results_root) == []


def test_production_run_properties():
    run = ProductionRun(modality="lesion", method="umap", run_name="13-08_s1.1_nc3_m_dice", path=None)

    assert run.key == "lesion/umap/13-08_s1.1_nc3_m_dice"
    assert run.results_relative_path == Path("results/lesion/dim_reduction/production/umap/13-08_s1.1_nc3_m_dice")


def test_run_title_matches_production_title_format():
    run = ProductionRun(modality="lesion", method="umap", run_name="run-a", path=None)

    assert run_title(run, NEUTRAL_MODE) == "Lesions - Umap"
    assert run_title(run, "dataset") == "Lesions - Umap - dataset"


def test_load_run_2d_and_3d_succeed(tmp_path):
    results_root = tmp_path / "results"
    run_dir_2d = _make_run_dir(results_root, run_name="run-2d", n_dims=2)
    run_dir_3d = _make_run_dir(results_root, run_name="run-3d", n_dims=3)

    embedding_2d, metadata_2d = load_run(ProductionRun("lesion", "umap", "run-2d", run_dir_2d))
    embedding_3d, metadata_3d = load_run(ProductionRun("lesion", "umap", "run-3d", run_dir_3d))

    assert embedding_2d.shape == (4, 2)
    assert embedding_3d.shape == (4, 3)
    assert len(metadata_2d) == 4


@pytest.mark.parametrize("n_dims", [1, 4, 10])
def test_load_run_rejects_embeddings_with_wrong_dimensionality(tmp_path, n_dims):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-bad", n_dims=n_dims)

    with pytest.raises(UndisplayableRunError, match="can only display"):
        load_run(ProductionRun("lesion", "umap", "run-bad", run_dir))


def _embedding_and_metadata(n=4):
    embedding = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])[:n]
    metadata = pd.DataFrame(
        {
            "subject_id": [f"sub-{i}" for i in range(n)],
            "dataset": (["UNIPD/WashU", "UKLFR/stroke_UKLFR"] * n)[:n],
            "lesion_volume_voxels": [10.0, 100.0, 1000.0, 10000.0][:n],
            "nihss": [1.0, np.nan, 5.0, 9.0][:n],
        }
    )
    return embedding, metadata


def test_build_embedding_figure_neutro_2d_single_trace():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, NEUTRAL_MODE, "x", "y", "title")

    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Scatter)
    assert fig.layout.title.text == "title"


def test_build_embedding_figure_categorical_one_trace_per_category():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "dataset", "x", "y", "title")

    names = {trace.name for trace in fig.data}
    assert names == set(metadata["dataset"].unique())


def test_build_embedding_figure_continuous_with_missing_adds_missing_trace():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "nihss", "x", "y", "title")

    names = {trace.name for trace in fig.data}
    assert "missing" in names
    assert "NIHSS (severity)" in names


def test_build_embedding_figure_log_scale_transforms_values_and_sets_decade_ticks():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "volume", "x", "y", "title")

    volume_trace = next(trace for trace in fig.data if trace.name == "lesion volume (voxels)")
    # log10([10, 100, 1000, 10000]) = [1, 2, 3, 4]
    assert list(volume_trace.marker.color) == pytest.approx([1.0, 2.0, 3.0, 4.0])
    assert list(volume_trace.marker.colorbar.tickvals) == pytest.approx([1.0, 2.0, 3.0, 4.0])
    assert list(volume_trace.marker.colorbar.ticktext) == ["10", "100", "1000", "10000"]


def test_build_embedding_figure_3d_uses_scatter3d_and_data_aspect():
    embedding = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])
    _, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, NEUTRAL_MODE, "x", "y", "title", zlabel="z")

    assert isinstance(fig.data[0], go.Scatter3d)
    assert fig.layout.scene.aspectmode == "data"
    assert fig.data[0].marker.opacity == 1.0
    assert fig.data[0].marker.line.color == "white"


def test_build_embedding_figure_zlabel_with_2_column_embedding_raises():
    embedding, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="not 3"):
        build_embedding_figure(embedding, metadata, NEUTRAL_MODE, "x", "y", "title", zlabel="z")


def test_build_embedding_figure_unknown_mode_raises():
    embedding, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="unknown color mode"):
        build_embedding_figure(embedding, metadata, "bogus", "x", "y", "title")


def test_build_embedding_figure_missing_persisted_column_raises():
    embedding, metadata = _embedding_and_metadata()
    metadata = metadata.drop(columns=["nihss"])

    with pytest.raises(ValueError, match="no 'nihss' column"):
        build_embedding_figure(embedding, metadata, "nihss", "x", "y", "title")


def test_color_mode_order_starts_with_neutro():
    assert COLOR_MODE_ORDER[0] == NEUTRAL_MODE
    assert set(COLOR_MODE_ORDER[1:]) == {"dataset", "side", "volume", "nihss"}


def test_graph_content_for_valid_run_returns_graph(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-2d", n_dims=2)
    run = ProductionRun("lesion", "umap", "run-2d", run_dir)

    content = graph_content_for(run, "dataset")

    assert isinstance(content, dcc.Graph)
    assert content.config["displayModeBar"] is False
    assert content.figure.layout.title.text == "Lesions - Umap - dataset"


def test_graph_content_for_undisplayable_run_returns_status_message(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-10d", n_dims=10)
    run = ProductionRun("lesion", "umap", "run-10d", run_dir)

    content = graph_content_for(run, NEUTRAL_MODE)

    assert isinstance(content, html.P)
    assert "can only display" in content.children


def test_build_app_raises_on_empty_runs():
    with pytest.raises(ValueError, match="at least one production run"):
        build_app([])


def _runs(*specs):
    """specs: (modality, method, run_name) tuples - path unused by the picker helpers."""
    return [ProductionRun(modality=m, method=method, run_name=name, path=None) for m, method, name in specs]


def test_modality_options_sorted_and_distinct():
    runs = _runs(("lesion", "umap", "a"), ("lesion", "pca", "b"), ("sdc", "umap", "c"))

    assert modality_options(runs) == ["lesion", "sdc"]


def test_method_options_scoped_to_modality():
    runs = _runs(("lesion", "umap", "a"), ("lesion", "pca", "b"), ("sdc", "umap", "c"))

    assert method_options(runs, "lesion") == ["pca", "umap"]
    assert method_options(runs, "sdc") == ["umap"]


def test_runs_for_scoped_and_chronologically_ordered():
    runs = _runs(
        ("lesion", "umap", "23-07_s1.1_d00"),
        ("lesion", "umap", "13-08_s1.1_nc3_m_dice"),
        ("lesion", "umap", "11-08_s1.1_nc2_m_euclidean"),
        ("lesion", "pca", "26-07_s1.1_c2"),  # different method - excluded
    )

    matching = runs_for(runs, "lesion", "umap")

    assert [r.run_name for r in matching] == [
        "23-07_s1.1_d00",
        "11-08_s1.1_nc2_m_euclidean",
        "13-08_s1.1_nc3_m_dice",
    ]


def test_runs_for_undated_run_name_sorts_last():
    runs = _runs(("lesion", "umap", "no-date-here"), ("lesion", "umap", "23-07_s1.1_d00"))

    matching = runs_for(runs, "lesion", "umap")

    assert [r.run_name for r in matching] == ["23-07_s1.1_d00", "no-date-here"]


def test_run_params_reads_config_md(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-a", params={"n_neighbors": 5, "metric": "dice", "n_components": 3})

    params = run_params(ProductionRun("lesion", "umap", "run-a", run_dir))

    assert params == {"n_neighbors": 5, "metric": "dice", "n_components": 3}


def test_run_params_missing_config_md_raises(tmp_path):
    run_dir = tmp_path / "empty-run"
    run_dir.mkdir()

    with pytest.raises(ValueError, match="no config.md"):
        run_params(ProductionRun("lesion", "umap", "empty-run", run_dir))


def test_run_params_config_md_without_params_line_raises(tmp_path):
    run_dir = tmp_path / "bad-run"
    run_dir.mkdir()
    (run_dir / "config.md").write_text("# just a title, no Params used line\n")

    with pytest.raises(ValueError, match="unexpected format"):
        run_params(ProductionRun("lesion", "umap", "bad-run", run_dir))


def test_metric_options_includes_no_metric_sentinel_for_methods_without_metric(tmp_path):
    results_root = tmp_path / "results"
    _make_run_dir(results_root, method="pca", run_name="run-a", params={"n_components": 150})

    assert metric_options(
        [ProductionRun("lesion", "pca", "run-a", results_root / "lesion/dim_reduction/production/pca/run-a")],
        "lesion", "pca",
    ) == [NO_METRIC]


def test_metric_options_distinct_values(tmp_path):
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(results_root, run_name="run-a", params={"metric": "euclidean", "n_components": 2})
    dir_b = _make_run_dir(results_root, run_name="run-b", params={"metric": "dice", "n_components": 2})
    runs = [ProductionRun("lesion", "umap", "run-a", dir_a), ProductionRun("lesion", "umap", "run-b", dir_b)]

    assert metric_options(runs, "lesion", "umap") == ["dice", "euclidean"]


def test_n_components_options_scoped_to_metric(tmp_path):
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(results_root, run_name="run-a", params={"metric": "euclidean", "n_components": 2})
    dir_b = _make_run_dir(results_root, run_name="run-b", params={"metric": "euclidean", "n_components": 3})
    dir_c = _make_run_dir(results_root, run_name="run-c", params={"metric": "dice", "n_components": 10})
    runs = [
        ProductionRun("lesion", "umap", "run-a", dir_a),
        ProductionRun("lesion", "umap", "run-b", dir_b),
        ProductionRun("lesion", "umap", "run-c", dir_c),
    ]

    assert n_components_options(runs, "lesion", "umap", "euclidean") == [2, 3]
    assert n_components_options(runs, "lesion", "umap", "dice") == [10]


def test_runs_matching_scoped_to_metric_and_n_components(tmp_path):
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(results_root, run_name="11-08_run-a", params={"metric": "euclidean", "n_components": 2})
    dir_b = _make_run_dir(results_root, run_name="11-08_run-b", params={"metric": "dice", "n_components": 2})
    dir_c = _make_run_dir(results_root, run_name="13-08_run-c", params={"metric": "euclidean", "n_components": 3})
    runs = [
        ProductionRun("lesion", "umap", "11-08_run-a", dir_a),
        ProductionRun("lesion", "umap", "11-08_run-b", dir_b),
        ProductionRun("lesion", "umap", "13-08_run-c", dir_c),
    ]

    matching = runs_matching(runs, "lesion", "umap", "euclidean", 2)

    assert [r.run_name for r in matching] == ["11-08_run-a"]


def test_build_app_layout_has_one_button_per_color_mode(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-2d", n_dims=2)
    run = ProductionRun("lesion", "umap", "run-2d", run_dir)

    app = build_app([run])

    # .controls' children: [picker-row-1 (Pipeline/Dato/Tipo di riduzione), picker-row-2
    # (Metrica/Componenti/Run), color-buttons] - color-buttons is the last one, not a fixed
    # index, so this doesn't silently break the next time a row is added/reordered.
    controls_children = app.layout.children[2].children
    color_buttons_div = controls_children[-1]
    assert len(color_buttons_div.children) == len(COLOR_MODE_ORDER)
    assert color_buttons_div.children[0].className == "active"  # neutro selected by default
