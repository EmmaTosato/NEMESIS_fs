"""Unit tests for the "Mappe delle componenti" panel of src/analysis/embedding_app.py."""

import json
import os
import time

import numpy as np
import pandas as pd
import pytest
from dash import dcc, html

from src.analysis.component_maps import ComponentMapSet, ComponentMapStore, MapGeometry, load_map_geometry
from src.analysis.embedding_app import (
    ComponentMapData,
    ProductionRun,
    _build_component_map_view,
    build_app,
    component_maps_content_for,
    index_entries_for,
    run_component_maps,
)
from src.utils.artifacts import save_matrix
from tests.unit.test_component_maps import _scores_and_matrix, _source_dir
from tests.unit.test_embedding_app import _lesion_cfg, _make_run_dir, _sdc_cfg

_GRID = (5, 5, 5)


def _pca_run(tmp_path, scores, input_path, method="pca", pipeline="dim_reduction", ids=None):
    """A production run directory whose config.md records `input_path` (what run_component_maps reads)."""
    run_dir = tmp_path / "results" / "sdc" / pipeline / "production" / method / "15-10_pca"
    config = {"input_path": str(input_path), "reduction_method": method}
    readme = ["# pca run", "", "## Config", "```json", json.dumps(config), "```", "", 'Params used: {"n_components": 2}']
    ids = ids if ids is not None else [f"sub-{i}" for i in range(len(scores))]
    save_matrix(run_dir, scores, pd.DataFrame({"subject_id": ids, "dataset": "X"}), readme_lines=readme, overwrite=False)
    return ProductionRun("sdc", pipeline, method, "15-10_pca", run_dir)


def _wait(store, run, timeout=60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = run_component_maps(run, store)
        if data is not None:
            return data
        time.sleep(0.05)
    raise AssertionError("the maps were not ready in time")


def _data(tmp_path, source_modified_after_run=False) -> ComponentMapData:
    scores, matrix = _scores_and_matrix()
    geometry = load_map_geometry(_source_dir(tmp_path, matrix))
    t = np.zeros((2, 40), dtype=np.float32)
    t[0, 3], t[0, 4] = 12.0, 6.0
    t[1, 25] = 9.0
    return ComponentMapData(
        maps=ComponentMapSet(t=t, reproducibility=np.array([0.95, 0.4]), n_degenerate_voxels=0),
        geometry=geometry, source_modified_after_run=source_modified_after_run,
    )


def _text(component) -> str:
    if isinstance(component, str):
        return component
    children = getattr(component, "children", None)
    if children is None:
        return ""
    return " ".join(_text(child) for child in (children if isinstance(children, (list, tuple)) else [children]))


def _find(component, kind) -> list:
    if isinstance(component, kind):
        return [component]
    children = getattr(component, "children", None)
    if children is None or isinstance(children, str):
        return []
    return [found for child in (children if isinstance(children, (list, tuple)) else [children]) for found in _find(child, kind)]


def test_run_component_maps_pairs_the_run_scores_with_the_source_matrix_it_names(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    run = _pca_run(tmp_path, scores, source)

    data = _wait(ComponentMapStore(tmp_path / "cache"), run)

    assert data.maps.t.shape == (2, 40) and int(data.geometry.mask.sum()) == 40
    assert data.source_modified_after_run is False


def test_a_source_matrix_modified_after_the_run_was_written_is_flagged(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    run = _pca_run(tmp_path, scores, source)
    later = time.time() + 3600
    os.utime(source / "matrix.npy", (later, later))

    assert _wait(ComponentMapStore(tmp_path / "cache"), run).source_modified_after_run is True


def test_run_component_maps_refuses_what_is_not_a_pca_dim_reduction_run(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)

    with pytest.raises(ValueError, match="only for dim_reduction runs with the pca method"):
        run_component_maps(_pca_run(tmp_path / "a", scores, source, method="umap"), ComponentMapStore(tmp_path / "cache"))
    with pytest.raises(ValueError, match="only for dim_reduction runs with the pca method"):
        run_component_maps(_pca_run(tmp_path / "b", scores, source, pipeline="clustering"), ComponentMapStore(tmp_path / "cache"))


def test_run_component_maps_names_a_missing_or_non_voxelwise_source(tmp_path):
    scores, matrix = _scores_and_matrix()
    store = ComponentMapStore(tmp_path / "cache")

    with pytest.raises(ValueError, match="does not exist"):
        run_component_maps(_pca_run(tmp_path / "a", scores, tmp_path / "no_such_matrix"), store)
    with pytest.raises(ValueError, match="non_constant_mask.npy"):
        run_component_maps(_pca_run(tmp_path / "b", scores, _source_dir(tmp_path / "src", matrix, mask=False)), store)


def test_run_component_maps_refuses_a_source_with_other_subjects(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    run = _pca_run(tmp_path, scores, source, ids=[f"other-{i}" for i in range(len(scores))])

    with pytest.raises(ValueError, match="not the matrix this run was computed from"):
        run_component_maps(run, ComponentMapStore(tmp_path / "cache"))


def test_the_component_view_is_centred_on_the_peak_and_returns_its_t(tmp_path):
    data = _data(tmp_path)

    view, peak = _build_component_map_view(data, 1)

    assert peak == 12.0 and view.html  # the largest |t| of component 1
    assert _build_component_map_view(data, 2)[1] == 9.0


def test_the_component_view_refuses_an_unknown_component_and_an_all_zero_map(tmp_path):
    data = _data(tmp_path)
    with pytest.raises(ValueError, match="component 3 does not exist"):
        _build_component_map_view(data, 3)
    zeros = ComponentMapData(
        maps=ComponentMapSet(t=np.zeros((1, 40), dtype=np.float32), reproducibility=np.array([0.5]), n_degenerate_voxels=0),
        geometry=data.geometry, source_modified_after_run=False,
    )
    with pytest.raises(ValueError, match="is all zero"):
        _build_component_map_view(zeros, 1)


def _stub_view(_data, component):
    class _View:
        html, width, height = "<html></html>", 900, 300

    return _View(), 12.0 if component == 1 else -9.0


def test_the_panel_shows_the_reproducibility_graph_and_the_chosen_component(tmp_path):
    run = ProductionRun("sdc", "dim_reduction", "pca", "x", tmp_path)
    data = _data(tmp_path)

    content, pending = component_maps_content_for(run, 2, lambda _run: data, _stub_view)

    text = _text(content)
    assert pending is False
    assert "Component 2: max t 9, reproducibility 0,40" in text
    assert "Mean reproducibility 0,675" in text and "(component 2)" in text  # the weakest component
    assert len(_find(content, dcc.Graph)) == 1 and "Warning" not in text


def test_the_panel_warns_when_the_source_matrix_changed_after_the_run(tmp_path):
    run = ProductionRun("sdc", "dim_reduction", "pca", "x", tmp_path)
    data = _data(tmp_path, source_modified_after_run=True)

    content, _pending = component_maps_content_for(run, 1, lambda _run: data, _stub_view)

    assert "Warning" in _text(content) and "modified after the run" in _text(content)


def test_the_panel_says_it_is_computing_and_asks_to_keep_polling(tmp_path):
    run = ProductionRun("sdc", "dim_reduction", "pca", "x", tmp_path)

    content, pending = component_maps_content_for(run, 1, lambda _run: None, _stub_view)

    assert pending is True and "Computing" in _text(content)


def test_the_panel_names_the_cause_when_the_maps_cannot_be_made(tmp_path):
    run = ProductionRun("sdc", "dim_reduction", "pca", "x", tmp_path)

    def refuse(_run):
        raise ValueError("la matrice sorgente non è voxelwise")

    content, pending = component_maps_content_for(run, 1, refuse, _stub_view)

    assert pending is False and isinstance(content, html.P) and "non è voxelwise" in content.children


def test_the_index_lists_the_panel_for_a_pca_run_only():
    pca = ProductionRun("sdc", "dim_reduction", "pca", "x", None)
    umap = ProductionRun("sdc", "dim_reduction", "umap", "x", None)
    clustering = ProductionRun("sdc", "clustering", "kmeans", "x", None, reduction_method="umap")

    assert "pca-map-panel" in [a for a, _ in index_entries_for(pca)]
    assert all("pca-map-panel" not in [a for a, _ in index_entries_for(run)] for run in (umap, clustering, None))


def _post(app, outputs, inputs, changed):
    body = {
        "output": ".." + "...".join(f"{i}.{p}" for i, p in outputs) + "..",
        "outputs": [{"id": i, "property": p} for i, p in outputs],
        "inputs": [{"id": i, "property": p, "value": v} for i, p, v in inputs],
        "changedPropIds": changed,
    }
    response = app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")
    assert response.status_code == 200
    return response.get_json()["response"]


def test_the_panel_is_shown_with_its_components_for_a_pca_run_and_hidden_otherwise(tmp_path):
    scores, matrix = _scores_and_matrix()
    pca = _pca_run(tmp_path / "pca", scores, _source_dir(tmp_path / "src", matrix))
    umap_dir = _make_run_dir(tmp_path / "results2", method="umap", run_name="10-08_s1")
    umap = ProductionRun("lesion", "dim_reduction", "umap", "10-08_s1", umap_dir)
    app = build_app([pca, umap], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), tmp_path / "params.json", tmp_path / "cache")
    app.server.config["TESTING"] = True
    outputs = [("pca-map-panel", "style"), ("pca-component-picker", "options"), ("pca-component-picker", "value")]

    shown = _post(app, outputs, [("run-picker", "value", pca.key)], ["run-picker.value"])
    hidden = _post(app, outputs, [("run-picker", "value", umap.key)], ["run-picker.value"])

    assert shown["pca-map-panel"]["style"] == {} and shown["pca-component-picker"]["value"] == 1
    assert [o["value"] for o in shown["pca-component-picker"]["options"]] == [1, 2]
    assert hidden["pca-map-panel"]["style"] == {"display": "none"} and hidden["pca-component-picker"]["options"] == []
