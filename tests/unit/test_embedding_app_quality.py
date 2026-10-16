"""Unit tests for the "Valutazione del clustering" panel of src/analysis/embedding_app.py."""

import pandas as pd
import pytest
from dash import dcc, html

from src.analysis.clustering_evaluation import AdpSummary, GeometricSummary, adp_summary
from src.analysis.embedding_app import (
    NOISE_WARNING_FRACTION,
    ProductionRun,
    adp_quality_content_for,
    cluster_quality_content_for,
    index_entries_for,
    run_adp_summary,
    run_geometric_summary,
)
import numpy as np
import time

from src.analysis.raw_distances import RawDistanceStore
from tests.unit.test_embedding_app import _make_run_dir


def _summary(**overrides) -> GeometricSummary:
    values = dict(
        n_subjects=5845, n_components=2, n_clusters=7, largest_cluster_share=0.412, noise_fraction=0.003,
        silhouette=0.546, silhouette_macro=0.431, silhouette_min=0.21, calinski_harabasz=17157.442,
        davies_bouldin=0.462, dunn=0.0123,
        clusters=pd.DataFrame(
            {"n": [100, 200], "silhouette_mean": [0.21, 0.6], "share_negative": [0.15, 0.01]}, index=[0, 1]
        ),
    )
    return GeometricSummary(**{**values, **overrides})


def _run(method="kmeans", reduction_method="umap", path=None) -> ProductionRun:
    return ProductionRun("lesion", "clustering", method, "15-10_x", path, reduction_method=reduction_method)


def _text(component) -> str:
    """Every string inside a Dash component tree, space-joined."""
    if isinstance(component, str):
        return component
    children = getattr(component, "children", None)
    if children is None:
        return ""
    if not isinstance(children, (list, tuple)):
        children = [children]
    return " ".join(_text(child) for child in children)


def test_the_panel_shows_every_index_with_italian_number_formatting():
    text = _text(cluster_quality_content_for(_run(), summary_of=lambda _run: _summary()))

    for expected in ("0,546", "0,431", "0,210", "17.157,4", "0,462", "0,0123", "41,2%", "0,3%", "5845 soggetti"):
        assert expected in text
    assert "Come leggere questi indici" in text


def test_a_noise_share_above_the_threshold_adds_a_warning_and_below_it_does_not():
    quiet = cluster_quality_content_for(_run(), summary_of=lambda _run: _summary(noise_fraction=NOISE_WARNING_FRACTION))
    noisy = cluster_quality_content_for(_run(), summary_of=lambda _run: _summary(noise_fraction=0.25))

    assert "Attenzione" not in _text(quiet)
    assert "Attenzione" in _text(noisy) and "25,0%" in _text(noisy)


def test_a_run_the_indices_are_not_defined_for_renders_the_cause_instead_of_raising():
    def refuse(_run):
        raise ValueError("fewer than 2 clusters")

    content = cluster_quality_content_for(_run(), summary_of=refuse)

    assert isinstance(content, html.P) and "fewer than 2 clusters" in content.children


def test_run_geometric_summary_refuses_adp(tmp_path):
    with pytest.raises(ValueError, match="adp"):
        run_geometric_summary(_run(method="adp"))


def test_run_geometric_summary_refuses_a_matrix_wider_than_the_limit(tmp_path, monkeypatch):
    run_dir = _make_run_dir(tmp_path / "results", pipeline="clustering", method="kmeans", run_name="15-10_x", params={"n_clusters": 2})
    monkeypatch.setattr("src.analysis.embedding_app.MAX_QUALITY_COLUMNS", 1)  # the fixture matrix has 2 columns

    with pytest.raises(ValueError, match="2 colonne"):
        run_geometric_summary(_run(path=run_dir))


def test_run_geometric_summary_reads_the_run_matrix_labels_and_params(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="15-10_x", params={"n_clusters": 2},
        extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    summary = run_geometric_summary(_run(path=run_dir))

    assert (summary.n_subjects, summary.n_components, summary.n_clusters) == (4, 2, 2)
    assert summary.silhouette > 0


def test_the_index_lists_the_panel_for_a_clustering_run_only():
    lesion_clustering, lesion_dr = _run(), ProductionRun("lesion", "dim_reduction", "umap", "x", None)

    assert "cluster-quality-panel" in [a for a, _ in index_entries_for(lesion_clustering)]
    assert "cluster-quality-panel" not in [a for a, _ in index_entries_for(lesion_dr)]


def _graphs(component) -> list:
    if isinstance(component, dcc.Graph):
        return [component]
    children = getattr(component, "children", None)
    if children is None or isinstance(children, str):
        return []
    return [graph for child in (children if isinstance(children, (list, tuple)) else [children]) for graph in _graphs(child)]


def test_the_panel_draws_one_silhouette_graph_with_a_bar_per_cluster():
    content = cluster_quality_content_for(_run(), summary_of=lambda _run: _summary())

    (graph,) = _graphs(content)
    assert list(graph.figure.data[0].y) == ["0 · n=100", "1 · n=200"]


def _adp_summary() -> AdpSummary:
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal([0, 0], 0.3, (30, 2)), rng.normal([5, 5], 0.3, (30, 2))])
    labels = np.repeat([0, 1], 30)
    distances = np.linalg.norm(X[:, None] - X[None, :], axis=2)
    return adp_summary(distances, np.ones(60, dtype=bool), labels, k=5)


def test_the_adp_panel_shows_purity_silhouette_and_a_row_per_cluster():
    content, pending = adp_quality_content_for(_run(method="adp", reduction_method="raw"), lambda _run: _adp_summary())

    text = _text(content)
    assert pending is False
    assert "Purezza dei 5 vicini" in text and "Purezza attesa a caso" in text and "Coppie a distanza 1" in text
    assert len(_graphs(content)) == 1  # the silhouette bars
    assert "Come leggere questi indici" in text and "60 soggetti clusterizzati di 60" in text


def test_the_adp_panel_says_it_is_computing_and_asks_to_keep_polling():
    content, pending = adp_quality_content_for(_run(method="adp", reduction_method="raw"), lambda _run: None)

    assert pending is True and "in corso" in _text(content)


def test_the_adp_panel_names_the_cause_when_the_indices_cannot_be_computed():
    def refuse(_run):
        raise ValueError("no cluster has more than k=10 members")

    content, pending = adp_quality_content_for(_run(method="adp", reduction_method="raw"), refuse)

    assert pending is False and isinstance(content, html.P) and "more than k=10" in content.children


def test_run_adp_summary_refuses_a_method_that_is_not_adp(tmp_path):
    with pytest.raises(ValueError, match="kmeans"):
        run_adp_summary(_run(method="kmeans"), RawDistanceStore(tmp_path / "cache"))


def test_run_adp_summary_reads_the_run_matrix_and_waits_for_the_background_distances(tmp_path, monkeypatch):
    monkeypatch.setattr("src.analysis.embedding_app.ADP_K_NEIGHBORS", 1)  # the fixture run has 4 subjects
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="adp", reduction_method="raw", run_name="15-10_x",
        params={"metric": "dice", "Z": 2.5}, extra_metadata={"cluster_label": [-1, 0, 0, 1]}, reduced_data=False,
    )
    run = ProductionRun("lesion", "clustering", "adp", "15-10_x", run_dir, reduction_method="raw")
    store = RawDistanceStore(tmp_path / "cache")  # row 0 of the fixture matrix is all zeros: undefined dice, labelled -1

    deadline = time.monotonic() + 30
    summary = run_adp_summary(run, store)
    while summary is None and time.monotonic() < deadline:
        time.sleep(0.05)
        summary = run_adp_summary(run, store)

    assert summary is not None
    assert (summary.n_subjects, summary.n_clustered, summary.k) == (4, 3, 1)
    assert summary.noise_fraction == pytest.approx(0.25)


def test_the_quality_callback_keeps_polling_an_adp_run_until_its_distances_are_ready(tmp_path, monkeypatch):
    import json

    from src.analysis.embedding_app import build_app
    from tests.unit.test_embedding_app import _lesion_cfg, _sdc_cfg

    monkeypatch.setattr("src.analysis.embedding_app.ADP_K_NEIGHBORS", 1)  # the fixture run has 4 subjects
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="adp", reduction_method="raw", run_name="15-10_x",
        params={"metric": "dice", "Z": 2.5}, extra_metadata={"cluster_label": [-1, 0, 0, 1]}, reduced_data=False,
    )
    run = ProductionRun("lesion", "clustering", "adp", "15-10_x", run_dir, reduction_method="raw")
    params_file = tmp_path / "params_clustering.json"
    params_file.write_text(json.dumps({"adp": {"tag_param": ["Z"]}}))
    app = build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), params_file, tmp_path / "cache")
    app.server.config["TESTING"] = True
    body = {
        "output": "..cluster-quality-content.children...cluster-quality-poll.disabled..",
        "outputs": [{"id": "cluster-quality-content", "property": "children"}, {"id": "cluster-quality-poll", "property": "disabled"}],
        "inputs": [
            {"id": "run-picker", "property": "value", "value": run.key},
            {"id": "cluster-quality-poll", "property": "n_intervals", "value": 0},
        ],
        "changedPropIds": ["run-picker.value"],
    }

    deadline = time.monotonic() + 30
    while True:
        response = app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")
        assert response.status_code == 200
        payload = response.get_json()["response"]
        if payload["cluster-quality-poll"]["disabled"] is True or time.monotonic() > deadline:
            break
        assert "in corso" in json.dumps(payload["cluster-quality-content"], ensure_ascii=False)  # still computing: keep polling
        time.sleep(0.05)

    assert payload["cluster-quality-poll"]["disabled"] is True
    assert "Purezza dei 1 vicini" in json.dumps(payload["cluster-quality-content"], ensure_ascii=False)
