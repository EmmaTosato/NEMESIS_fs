"""Unit tests for the "Valutazione del clustering" panel of src/analysis/embedding_app.py."""

import pandas as pd
import pytest
from dash import dcc, html

from src.analysis.clustering_evaluation import GeometricSummary
from src.analysis.embedding_app import (
    NOISE_WARNING_FRACTION,
    ProductionRun,
    cluster_quality_content_for,
    index_entries_for,
    run_geometric_summary,
)
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
