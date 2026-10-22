"""Unit tests for the "Valutazione del clustering" panel of src/analysis/embedding_app.py."""

import pandas as pd
import pytest
from dash import dcc, html

from src.analysis.clustering_evaluation import (
    AdpSummary,
    GeometricSummary,
    adp_summary,
    membership_confidence,
    soft_membership_summary,
    weakest_soft_members,
)
from src.analysis.embedding_app import (
    NOISE_WARNING_FRACTION,
    ProductionRun,
    adp_quality_content_for,
    cluster_quality_content_for,
    index_entries_for,
    run_adp_summary,
    run_geometric_summary,
    run_membership_confidence,
    run_model_fit,
    run_soft_membership,
)
import numpy as np
import time

from src.analysis.raw_distances import RawDistanceStore
from src.utils.artifacts import save_matrix
from tests.unit.test_embedding_app import _make_run_dir


def _summary(**overrides) -> GeometricSummary:
    values = dict(
        n_subjects=5845, n_components=2, n_clusters=7, largest_cluster_share=0.412, noise_fraction=0.003,
        silhouette=0.546, silhouette_macro=0.431, silhouette_min=0.21, calinski_harabasz=17157.442,
        davies_bouldin=0.462, dunn=0.0123,
        clusters=pd.DataFrame(
            {"n": [100, 200], "silhouette_mean": [0.21, 0.6], "share_negative": [0.15, 0.01]}, index=[0, 1]
        ),
        subject_labels=np.repeat([0, 1], [100, 200]), subject_values=np.concatenate([np.full(100, 0.21), np.full(200, 0.6)]),
    )
    return GeometricSummary(**{**values, **overrides})


def _run(method="kmeans", reduction_method="umap", path=None) -> ProductionRun:
    return ProductionRun("lesion", "clustering", method, "15-10_x", path, reduction_method=reduction_method)


def _unused(_run):
    raise ValueError("not under test")


def _fit(run) -> dict[str, float]:
    """The statistic each method has, as run_model_fit would return it; a method without one is refused."""
    by_method = {
        "kmeans": {"inertia": 1234.5},
        "gmm": {"bic": 5000.2, "aic": 4900.7},
        "agglomerative": {"n_clusters": 7.0, "cophenetic_correlation": 0.7312, "dendrogram_jump": 1.4567},
        "hdbscan": {"noise_fraction": 0.09, "n_clusters_found": 4.0},
        "hdbscan_soft": {"noise_fraction": 0.01, "n_clusters_found": 8.0},
    }
    if run.method not in by_method:
        raise ValueError(f"no model statistic for {run.method}")
    return by_method[run.method]


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
    text = _text(cluster_quality_content_for(_run(), model_fit_of=_fit, summary_of=lambda _run: _summary()))

    for expected in ("0,546", "0,431", "0,210", "17.157,4", "0,462", "0,0123", "41,2%", "0,3%", "5845 soggetti"):
        assert expected in text
    assert "Come leggere questi indici" in text


def test_the_guide_to_the_indices_is_a_collapsed_menu_right_under_the_heading():
    content = cluster_quality_content_for(_run(), model_fit_of=_fit, summary_of=lambda _run: _summary())
    failing = cluster_quality_content_for(_run(), model_fit_of=_fit, summary_of=_unused)

    for panel in (content, failing):
        first = panel.children[0]
        assert isinstance(first, html.Details) and "Come leggere questi indici" in _text(first)
        assert "open" not in (first.to_plotly_json()["props"])  # collapsed by default
    assert "Limiti" in _text(content.children[0])


def test_a_noise_share_above_the_threshold_adds_a_warning_and_below_it_does_not():
    quiet = cluster_quality_content_for(_run(), model_fit_of=_fit, summary_of=lambda _run: _summary(noise_fraction=NOISE_WARNING_FRACTION))
    noisy = cluster_quality_content_for(_run(), model_fit_of=_fit, summary_of=lambda _run: _summary(noise_fraction=0.25))

    assert "Attenzione" not in _text(quiet)
    assert "Attenzione" in _text(noisy) and "25,0%" in _text(noisy)


def test_a_run_the_indices_are_not_defined_for_renders_the_cause_instead_of_raising():
    def refuse(_run):
        raise ValueError("fewer than 2 clusters")

    content = cluster_quality_content_for(_run(), model_fit_of=_fit, summary_of=refuse)

    assert "fewer than 2 clusters" in _text(content)
    assert "Inertia" in _text(content)  # the model statistic is still there: one failing part never hides the other


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


def test_the_panel_draws_one_silhouette_graph_with_a_panel_per_cluster():
    content = cluster_quality_content_for(_run(), model_fit_of=_fit, summary_of=lambda _run: _summary())

    (graph,) = _graphs(content)
    assert [len(trace.x) for trace in graph.figure.data] == [100, 200]  # every subject of each cluster is drawn


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
    assert len(_graphs(content)) == 1  # the silhouette panels
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


@pytest.mark.parametrize(
    ("method", "metrics", "expected"),
    [
        ("kmeans", {"inertia": 1234.5}, ["Inertia", "1.234,5"]),
        ("gmm", {"bic": 5000.2, "aic": 4900.7}, ["BIC", "5.000,2", "AIC", "4.900,7"]),
        ("hdbscan", {"noise_fraction": 0.093, "n_clusters_found": 4.0}, ["Rumore", "9,3%", "Cluster trovati", "4"]),
        ("hdbscan_soft", {"noise_fraction": 0.003, "n_clusters_found": 8.0}, ["Rumore", "0,3%", "Cluster trovati", "8"]),
    ],
)
def test_the_model_statistic_block_shows_what_each_method_has(method, metrics, expected):
    content = cluster_quality_content_for(
        _run(method=method), lambda _run: _summary(), lambda _run: metrics, confidence_of=_unused, soft_of=_unused
    )

    text = _text(content)
    assert "Statistica del modello" in text
    assert all(piece in text for piece in expected)


def test_a_refit_that_does_not_reproduce_the_labels_says_so_instead_of_showing_a_number():
    def refuse(_run):
        raise ValueError("refitting 'kmeans' does not reproduce the stored labels")

    text = _text(cluster_quality_content_for(_run(), lambda _run: _summary(), refuse))

    assert "does not reproduce the stored labels" in text and "Inertia" not in text


def test_a_method_without_a_model_statistic_says_so():
    # spectral has none: the real run_model_fit refuses it through require_applicable.
    text = _text(cluster_quality_content_for(_run(method="spectral"), lambda _run: _summary()))

    assert "Statistica del modello" in text and "spectral" in text and "agglomerative" in text and "kmeans" in text


def test_the_panel_shows_cophenetic_correlation_and_dendrogram_jump_for_agglomerative():
    text = _text(cluster_quality_content_for(_run(method="agglomerative"), model_fit_of=_fit, summary_of=lambda _run: _summary()))

    assert "Correlazione cofenetica" in text and "0,731" in text
    assert "Salto del dendrogramma (k=7)" in text and "1,46" in text


def test_run_model_fit_reads_cophenetic_correlation_and_jump_of_an_agglomerative_run(tmp_path):
    from sklearn.cluster import AgglomerativeClustering

    params = {"n_clusters": 2, "linkage": "average", "metric": "euclidean"}
    fixture_matrix = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]])  # what _make_run_dir saves
    labels = AgglomerativeClustering(**params).fit_predict(fixture_matrix)
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="agglomerative", run_name="15-10_x",
        params=params, extra_metadata={"cluster_label": labels},
    )

    metrics = run_model_fit(_run(method="agglomerative", path=run_dir))

    assert set(metrics) == {"n_clusters", "cophenetic_correlation", "dendrogram_jump"}
    assert metrics["n_clusters"] == 2.0 and 0 < metrics["cophenetic_correlation"] <= 1 and metrics["dendrogram_jump"] > 0


def test_run_model_fit_refits_the_run_and_reads_its_inertia(tmp_path):
    from sklearn.cluster import KMeans

    params = {"n_clusters": 2, "n_init": 10, "random_state": 0}
    fixture_matrix = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]])  # what _make_run_dir saves
    labels = KMeans(**params).fit(fixture_matrix).labels_  # the numbering a real run would have stored
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="kmeans", run_name="15-10_x",
        params=params, extra_metadata={"cluster_label": labels},
    )

    metrics = run_model_fit(_run(path=run_dir))

    assert set(metrics) == {"inertia"} and metrics["inertia"] > 0


def test_run_model_fit_refuses_a_matrix_wider_than_the_limit(tmp_path, monkeypatch):
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="kmeans", run_name="15-10_x",
        params={"n_clusters": 2, "random_state": 0}, extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    monkeypatch.setattr("src.analysis.embedding_app.MAX_QUALITY_COLUMNS", 1)

    with pytest.raises(ValueError, match="2 colonne"):
        run_model_fit(_run(path=run_dir))


_SOFT_LABELS = np.array([0, 0, 1, 1, -1, 0])
_SOFT_MEMBERSHIP = np.array([[0.9, 0.05], [0.4, 0.35], [0.1, 0.8], [0.2, 0.3], [0.05, 0.05], [0.6, 0.1]])


def _soft_pair():
    weakest = weakest_soft_members(_SOFT_LABELS, _SOFT_MEMBERSHIP, 2)
    weakest.insert(0, "subject_id", [f"sub-{i}" for i in weakest.index])
    return soft_membership_summary(_SOFT_LABELS, _SOFT_MEMBERSHIP, 0.5), weakest


def test_an_hdbscan_run_gets_the_position_in_cluster_block():
    from tests.unit.test_clustering_evaluation import _HDBSCAN_PARAMS, _blobs_of_mixed_density, _fit_hdbscan

    X = _blobs_of_mixed_density()
    labels, _ = _fit_hdbscan(X)
    result = membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, labels, 0.5)

    content = cluster_quality_content_for(
        _run(method="hdbscan"), lambda _run: _summary(), _fit, confidence_of=lambda _run: result, soft_of=_unused
    )

    text = _text(content)
    assert "Posizione nel cluster" in text and f"{result.n_noise} soggetti di rumore" in text
    assert "Sotto 0,50" in text and "Appartenenza ai cluster" not in text


def test_a_hdbscan_soft_run_gets_the_soft_membership_block_with_heatmap_and_weakest_subjects():
    content = cluster_quality_content_for(
        _run(method="hdbscan_soft"), lambda _run: _summary(), _fit, confidence_of=_unused, soft_of=lambda _run: _soft_pair()
    )

    text = _text(content)
    assert "Appartenenza ai cluster" in text and "Posizione nel cluster" not in text
    assert "1 soggetti di rumore" in text
    assert "sub-3" in text and "sub-1" in text and "0,300" in text  # the two weakest, lowest first
    assert len(_graphs(content)) == 2  # the silhouette bars and the membership heatmap


@pytest.mark.parametrize("method", ["hdbscan", "hdbscan_soft"])
def test_a_membership_block_that_cannot_be_computed_says_why_and_leaves_the_rest(method):
    def refuse(_run):
        raise ValueError("refit does not reproduce the stored labels")

    text = _text(cluster_quality_content_for(_run(method=method), lambda _run: _summary(), _fit, confidence_of=refuse, soft_of=refuse))

    assert "does not reproduce the stored labels" in text and "Silhouette" in text


@pytest.mark.parametrize("method", ["kmeans", "gmm", "agglomerative", "spectral"])
def test_the_other_methods_get_neither_membership_block(method):
    text = _text(cluster_quality_content_for(_run(method=method), lambda _run: _summary(), _fit, confidence_of=_unused, soft_of=_unused))

    assert "Posizione nel cluster" not in text and "Appartenenza ai cluster" not in text


def _save_run(tmp_path, method, X, labels, params, extra_arrays=None):
    import json

    run_dir = tmp_path / "results" / "lesion" / "clustering" / "production" / method / "umap" / "15-10_x"
    metadata = pd.DataFrame({"subject_id": [f"sub-{i}" for i in range(len(X))], "cluster_label": labels})
    readme = ["# test run", "", f"Params used: {json.dumps(params)}"]
    save_matrix(run_dir, X, metadata, readme_lines=readme, overwrite=False, extra_arrays=extra_arrays)
    return ProductionRun("lesion", "clustering", method, "15-10_x", run_dir, reduction_method="umap")


def test_run_membership_confidence_refits_hdbscan_and_reads_the_run_labels(tmp_path):
    from tests.unit.test_clustering_evaluation import _HDBSCAN_PARAMS, _blobs_of_mixed_density, _fit_hdbscan

    X = _blobs_of_mixed_density()
    labels, _ = _fit_hdbscan(X)
    run = _save_run(tmp_path, "hdbscan", X, labels, _HDBSCAN_PARAMS)

    result = run_membership_confidence(run)

    assert result.n_noise == int((labels == -1).sum()) and result.threshold == 0.5
    assert sorted(result.clusters.index) == sorted(set(labels) - {-1})


def test_run_membership_confidence_refuses_labels_the_refit_does_not_reproduce(tmp_path):
    from tests.unit.test_clustering_evaluation import _HDBSCAN_PARAMS, _blobs_of_mixed_density, _fit_hdbscan

    X = _blobs_of_mixed_density()
    labels, _ = _fit_hdbscan(X)
    run = _save_run(tmp_path, "hdbscan", X, np.roll(labels, 1), _HDBSCAN_PARAMS)

    with pytest.raises(ValueError, match="does not reproduce the stored labels"):
        run_membership_confidence(run)


def test_run_soft_membership_reads_the_saved_membership_and_names_the_weakest_subjects(tmp_path):
    X = np.zeros((6, 2))
    run = _save_run(tmp_path, "hdbscan_soft", X, _SOFT_LABELS, {"min_cluster_size": 2}, extra_arrays={"membership": _SOFT_MEMBERSHIP})

    summary, weakest = run_soft_membership(run)

    assert summary.n_noise == 1 and list(summary.clusters.index) == [0, 1]
    assert list(weakest["subject_id"])[:2] == ["sub-3", "sub-1"]  # the lowest own probability first


def test_run_soft_membership_refuses_a_run_without_membership_npy(tmp_path):
    run = _save_run(tmp_path, "hdbscan_soft", np.zeros((6, 2)), _SOFT_LABELS, {"min_cluster_size": 2})

    with pytest.raises(ValueError, match="membership.npy"):
        run_soft_membership(run)
