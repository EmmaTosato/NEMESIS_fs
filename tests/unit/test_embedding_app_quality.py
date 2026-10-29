"""Unit tests for the "Clustering evaluation" panel of src/analysis/embedding_app.py."""

import time

import numpy as np
import pandas as pd
import pytest
from dash import dcc, html
from sklearn.cluster import AgglomerativeClustering

from src.analysis.clustering_evaluation import AdpSummary, adp_summary, silhouette_breakdown, soft_membership_summary
from src.analysis.embedding_app import (
    adp_quality_content_for,
    cluster_quality_content_for,
    index_entries_for,
    run_adp_summary,
    run_production_results,
    run_silhouette_samples,
    run_soft_membership,
)
from src.analysis.embedding_app.runs import ProductionRun
from src.analysis.production_results import SavedResults, compute_production_results, write_production_results
from src.analysis.raw_distances import RawDistanceStore
from src.utils.artifacts import save_matrix
from tests.unit.test_embedding_app import _make_run_dir

# What _make_run_dir saves as the matrix of a run.
_FIXTURE_MATRIX = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]])
_AGGLOMERATIVE_PARAMS = {"n_clusters": 2, "linkage": "average", "metric": "euclidean"}


def _saved_agglomerative(values: dict | None = None, notes: dict | None = None) -> SavedResults:
    """What an agglomerative run saved: 7 clusters over 5845 subjects."""
    all_values = {
        "silhouette": 0.546, "calinski_harabasz": 17157.442, "davies_bouldin": 0.462, "dunn": 0.0123,
        "largest_cluster_share": 0.412, "cophenetic_correlation": 0.7312, "dendrogram_jump": 1.4567, **(values or {}),
    }
    per_cluster = pd.DataFrame({
        "cluster": range(7), "n": [2000, 1500, 900, 600, 400, 300, 145],
        "silhouette_mean": [0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.21], "share_negative": [0.0, 0.01, 0.02, 0.03, 0.05, 0.1, 0.15],
    })
    return SavedResults(all_values, {name: "" for name in all_values} | (notes or {}), per_cluster)


def _saved_density(soft: bool = False, values: dict | None = None, notes: dict | None = None, per_cluster=None) -> SavedResults:
    """What an hdbscan (or hdbscan_soft) run saved: 2 clusters of 100 and 200 subjects, a quarter of the subjects noise."""
    all_values = {
        "n_clusters_found": 2.0, "noise_fraction": 0.25, "largest_cluster_share": 0.412, "dbcv": 0.227, "membership_mean": 0.88,
        **({"persistence_mean": 0.55} if soft else {}), **(values or {}),
    }
    if per_cluster is None:
        per_cluster = pd.DataFrame({"cluster": [0, 1], "n": [100, 200], "dbcv": [0.72, -0.1], "membership_mean": [0.9, 0.85]})
        if soft:
            per_cluster["persistence"] = [0.3, 0.8]
    return SavedResults(all_values, {name: "" for name in all_values} | (notes or {}), per_cluster)


def _silhouette():
    return silhouette_breakdown(np.repeat([0, 1], [100, 200]), np.concatenate([np.full(100, 0.21), np.full(200, 0.6)]))


def _run(method="agglomerative", reduction_method="umap", path=None) -> ProductionRun:
    return ProductionRun("lesion", "clustering", method, "15-10_x", path, reduction_method=reduction_method)


def _unused(_run):
    raise ValueError("not under test")


def _panel(saved, method="agglomerative", silhouette=_silhouette, soft=_unused, metric="euclidean"):
    """The panel of a run of `method` that saved `saved`, with the silhouette, the soft membership and the metric given."""
    return cluster_quality_content_for(
        _run(method), results_of=lambda _run: saved, silhouette_of=lambda _run: silhouette(), soft_of=soft, metric_of=lambda _run: metric
    )


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


def _graphs(component) -> list:
    if isinstance(component, dcc.Graph):
        return [component]
    children = getattr(component, "children", None)
    if children is None or isinstance(children, str):
        return []
    return [graph for child in (children if isinstance(children, (list, tuple)) else [children]) for graph in _graphs(child)]


def test_the_index_lists_the_panel_for_a_clustering_run_only():
    lesion_clustering, lesion_dr = _run(), ProductionRun("lesion", "dim_reduction", "umap", "x", None)

    assert "cluster-quality-panel" in [a for a, _ in index_entries_for(lesion_clustering)]
    assert "cluster-quality-panel" not in [a for a, _ in index_entries_for(lesion_dr)]


# --- agglomerative: the numbers it saved -----------------------------------------------------------


def test_the_agglomerative_panel_shows_every_saved_number_with_italian_formatting():
    text = _text(_panel(_saved_agglomerative()))

    for expected in ("0,546", "17.157,4", "0,462", "0,0123", "41,2%", "0,731", "Dendrogram jump (k=7)", "1,46", "5845 subjects"):
        assert expected in text
    assert "0,431" not in text and "worst cluster" not in text and "mean over clusters" not in text  # no macro, no weakest cluster
    assert "How to read these indices" in text


def test_the_agglomerative_panel_has_a_row_per_cluster_with_its_saved_silhouette():
    text = _text(_panel(_saved_agglomerative()))

    assert "Mean silhouette" in text and "Negative silhouette" in text
    assert "0,21" in text and "15,0%" in text  # the last cluster: 145 subjects, mean 0.21, 15% negative


def test_an_index_the_run_did_not_define_is_a_dash_with_the_reason_it_saved():
    saved = _saved_agglomerative(
        {name: float("nan") for name in ("calinski_harabasz", "davies_bouldin", "dunn")},
        {name: "Euclidean distance only" for name in ("calinski_harabasz", "davies_bouldin", "dunn")},
    )

    text = _text(_panel(saved, metric="cosine"))

    assert "0,546" in text  # the silhouette, measured in the cosine distance
    assert "nan" not in text.lower() and "—" in text
    assert text.count("Euclidean distance only") == 3  # Calinski-Harabasz, Davies-Bouldin, Dunn
    assert "uses the cosine distance" in text


def test_a_euclidean_run_has_no_dash_and_no_metric_sentence():
    text = _text(_panel(_saved_agglomerative()))

    assert "Euclidean distance only" not in text and "uses the" not in text


def test_the_agglomerative_panel_intro_and_chart_do_not_say_noise_is_excluded():
    text = _text(_panel(_saved_agglomerative()))

    assert "5845 subjects" in text and "one panel per cluster" in text
    assert "with noise (-1) excluded" not in text and "one panel per cluster, noise excluded" not in text
    assert "Clusters (noise excluded)" not in text and "Clusters 7" in text.replace(",", "")  # the row is just "Clusters"


def test_the_agglomerative_guide_explains_both_statistics_and_not_how_the_tree_is_rebuilt():
    text = _text(_panel(_saved_agglomerative()))

    assert "Cophenetic correlation: how faithfully the tree reflects the real distances" in text
    assert "Dendrogram jump (at the run's k): how sharp the cut at k is" in text
    assert "k to k-1 clusters" in text and "k+1 to k" in text
    assert "rebuilt" not in text and "exactly the saved labels" not in text


def test_the_tree_statistics_that_were_not_defined_say_why_instead_of_a_number():
    saved = _saved_agglomerative(
        {"cophenetic_correlation": float("nan"), "dendrogram_jump": float("nan")},
        {"cophenetic_correlation": "not defined: refit does not reproduce the stored labels",
         "dendrogram_jump": "not defined: refit does not reproduce the stored labels"},
    )

    text = _text(_panel(saved))

    assert text.count("does not reproduce the stored labels") == 2 and "nan" not in text.lower()


def test_the_panel_draws_one_silhouette_graph_with_a_panel_per_cluster():
    (graph,) = _graphs(_panel(_saved_agglomerative()))

    assert [len(trace.x) for trace in graph.figure.data] == [100, 200]  # every subject of each cluster is drawn


def test_the_silhouette_of_every_subject_that_cannot_be_drawn_says_why_and_the_saved_numbers_stay():
    def refuse():
        raise ValueError("the run was computed on 221955 columns")

    content = _panel(_saved_agglomerative(), silhouette=refuse)

    text = _text(content)
    assert "221955 columns" in text and "0,546" in text and "Dendrogram jump" in text
    assert _graphs(content) == []


def test_the_guide_to_the_indices_is_a_collapsed_menu_right_under_the_heading():
    def missing(_run):
        raise FileNotFoundError("15-10_x has no production_results.csv")

    for method, panel in (
        ("agglomerative", _panel(_saved_agglomerative())),
        ("agglomerative", cluster_quality_content_for(_run(), results_of=missing)),
        ("hdbscan", _panel(_saved_density(), "hdbscan")),
        ("hdbscan", cluster_quality_content_for(_run("hdbscan"), results_of=missing)),
    ):
        first = panel.children[0]
        assert isinstance(first, html.Details) and "How to read" in _text(first), method
        assert "open" not in (first.to_plotly_json()["props"])  # collapsed by default
    assert "Limits" in _text(_panel(_saved_agglomerative()).children[0])


# --- the runs the panel has nothing to read for ------------------------------------------------------


def test_a_run_without_the_saved_files_says_so_instead_of_computing_anything(tmp_path):
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="agglomerative", run_name="15-10_x",
        params=_AGGLOMERATIVE_PARAMS, extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )

    content = cluster_quality_content_for(_run(path=run_dir))

    text = _text(content)
    assert "has no production_results.csv" in text and "15-10_x" in text
    assert _graphs(content) == [] and "Silhouette (mean" not in text


def test_files_that_are_not_the_methods_say_why_instead_of_a_table():
    def refuse(_run):
        raise ValueError("production_results.csv has the metrics ['dbcv'], an agglomerative run has [...]")

    text = _text(cluster_quality_content_for(_run(), results_of=refuse))

    assert "an agglomerative run has" in text


@pytest.mark.parametrize("method", ["kmeans", "gmm", "spectral", "adp"])
def test_a_method_without_saved_results_says_so_and_names_the_ones_with_them(method):
    text = _text(cluster_quality_content_for(_run(method=method), results_of=_unused))

    assert repr(method) in text and "agglomerative" in text and "hdbscan_soft" in text


def test_run_production_results_reads_the_files_of_the_run_dir(tmp_path):
    X = _FIXTURE_MATRIX
    labels = AgglomerativeClustering(**_AGGLOMERATIVE_PARAMS).fit_predict(X)
    write_production_results(tmp_path, compute_production_results("agglomerative", X, labels, _AGGLOMERATIVE_PARAMS))

    saved = run_production_results(_run(path=tmp_path))

    assert saved.values["silhouette"] > 0 and list(saved.per_cluster["n"]) == [3, 1]  # average linkage on the 4 fixture points
    with pytest.raises(FileNotFoundError, match="production_results.csv"):
        run_production_results(_run(path=tmp_path / "other"))


def test_run_silhouette_samples_reads_the_run_matrix_labels_and_params(tmp_path):
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="agglomerative", run_name="15-10_x",
        params=_AGGLOMERATIVE_PARAMS, extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )

    breakdown = run_silhouette_samples(_run(path=run_dir))

    assert len(breakdown.subject_values) == 4 and breakdown.micro > 0


def test_run_silhouette_samples_refuses_a_matrix_wider_than_the_limit(tmp_path, monkeypatch):
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="agglomerative", run_name="15-10_x",
        params=_AGGLOMERATIVE_PARAMS, extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    monkeypatch.setattr("src.analysis.embedding_app.MAX_QUALITY_COLUMNS", 1)  # the fixture matrix has 2 columns

    with pytest.raises(ValueError, match="2 columns"):
        run_silhouette_samples(_run(path=run_dir))


def test_the_panel_of_a_saved_agglomerative_run_reads_the_files_and_draws_the_silhouette(tmp_path):
    labels = AgglomerativeClustering(**_AGGLOMERATIVE_PARAMS).fit_predict(_FIXTURE_MATRIX)
    run_dir = _make_run_dir(
        tmp_path / "results", pipeline="clustering", method="agglomerative", run_name="15-10_x",
        params=_AGGLOMERATIVE_PARAMS, extra_metadata={"cluster_label": labels},
    )
    results = compute_production_results("agglomerative", _FIXTURE_MATRIX, labels, _AGGLOMERATIVE_PARAMS)
    write_production_results(run_dir, results)

    content = cluster_quality_content_for(_run(path=run_dir))

    text = _text(content)
    assert "4 subjects" in text and "Cophenetic correlation" in text and "Dendrogram jump (k=2)" in text
    assert len(_graphs(content)) == 1
    # the numbers are the saved ones: editing the file changes the panel, nothing is computed again
    saved_file = run_dir / "production_results.csv"
    saved_file.write_text("".join("silhouette,0.123456,\n" if line.startswith("silhouette,") else line for line in saved_file.read_text().splitlines(keepends=True)))
    assert "0,123" in _text(cluster_quality_content_for(_run(path=run_dir)))


_SOFT_LABELS = np.array([0, 0, 1, 1, -1, 0])
_SOFT_MEMBERSHIP = np.array([[0.9, 0.05], [0.4, 0.35], [0.1, 0.8], [0.2, 0.3], [0.05, 0.05], [0.6, 0.1]])




# --- hdbscan and hdbscan_soft: the numbers they saved -----------------------------------------------


@pytest.mark.parametrize("method", ["hdbscan", "hdbscan_soft"])
def test_a_density_run_shows_dbcv_and_not_the_geometric_indices(method):
    soft = method == "hdbscan_soft"
    content = _panel(_saved_density(soft), method, soft=lambda _run: soft_membership_summary(_SOFT_LABELS, _SOFT_MEMBERSHIP))

    text = _text(content)
    assert "How to read DBCV" in text and "DBCV" in text and "0,227" in text and "41,2%" in text and "25,0%" in text
    assert "Mean probability in own cluster" in text and "0,88" in text
    for absent in ("Silhouette (mean", "Calinski-Harabasz (", "Davies-Bouldin (", "Dunn ("):
        assert absent not in text
    assert any("DBCV of the cluster" in str(graph.figure.layout.xaxis.title.text) for graph in _graphs(content))
    assert "Warning" not in text  # no noise limit


def test_an_hdbscan_run_has_the_probability_per_cluster_and_no_persistence_nor_soft_membership():
    text = _text(_panel(_saved_density(), "hdbscan"))

    assert "Mean probability" in text and "0,9" in text and "0,85" in text
    assert "Persistence" not in text and "persistence" not in text and "Cluster membership" not in text
    assert "Position in the cluster" not in text and "Model statistic" not in text


def test_a_hdbscan_soft_run_has_the_persistence_and_the_soft_membership_with_heatmap_and_no_subject_list():
    content = _panel(_saved_density(soft=True), "hdbscan_soft", soft=lambda _run: soft_membership_summary(_SOFT_LABELS, _SOFT_MEMBERSHIP))

    text = _text(content)
    assert "Mean persistence" in text and "0,55" in text and "Persistence" in text and "0,3" in text and "0,8" in text
    assert "Cluster membership" in text and "1 noise subjects" in text
    assert "least firmly" not in text and "sub-3" not in text  # no list of subjects: its length would be a threshold
    assert len(_graphs(content)) == 2  # the DBCV bars and the membership heatmap


def test_a_soft_membership_that_cannot_be_read_says_why_and_leaves_the_rest():
    def refuse(_run):
        raise ValueError("the run has no membership.npy")

    text = _text(_panel(_saved_density(soft=True), "hdbscan_soft", soft=refuse))

    assert "no membership.npy" in text and "DBCV" in text and "0,227" in text


def test_a_dbcv_the_run_did_not_define_is_a_dash_with_the_reason_it_saved_and_no_chart():
    saved = _saved_density(
        values={"dbcv": float("nan"), "n_clusters_found": 1.0}, notes={"dbcv": "not defined: fewer than 2 clusters"},
        per_cluster=pd.DataFrame({"cluster": [0], "n": [200], "dbcv": [float("nan")], "membership_mean": [0.9]}),
    )

    content = _panel(saved, "hdbscan")

    text = _text(content)
    assert "not defined: fewer than 2 clusters" in text and "—" in text and "nan" not in text.lower()
    assert "Largest cluster" in text and "Noise" in text
    assert _graphs(content) == []


def test_a_run_that_is_all_noise_renders_with_the_reasons_and_no_cluster_row():
    saved = _saved_density(
        soft=True,
        values={"n_clusters_found": 0.0, "noise_fraction": 1.0, "largest_cluster_share": float("nan"), "dbcv": float("nan"),
                "membership_mean": float("nan"), "persistence_mean": float("nan")},
        notes={"largest_cluster_share": "no cluster: every subject is noise", "membership_mean": "no cluster: every subject is noise",
               "persistence_mean": "no cluster: every subject is noise", "dbcv": "not defined: fewer than 2 clusters"},
        per_cluster=pd.DataFrame({"cluster": [], "n": [], "dbcv": [], "membership_mean": [], "persistence": []}),
    )

    content = _panel(saved, "hdbscan_soft", soft=_unused)

    text = _text(content)
    assert text.count("no cluster: every subject is noise") == 3 and "100,0%" in text and "nan" not in text.lower()
    assert _graphs(content) == []


def test_the_panel_of_a_saved_density_run_reads_the_files(tmp_path):
    from tests.unit.test_production_results import _noisy_blobs

    X, labels, membership = _noisy_blobs()
    run = _save_run(tmp_path, "hdbscan", X, labels, {})
    write_production_results(run.path, compute_production_results("hdbscan", X, labels, {}, membership))

    content = cluster_quality_content_for(run)

    text = _text(content)
    assert "Clusters (noise excluded) 2" in text.replace(",", "") and "DBCV" in text
    assert len(_graphs(content)) == 1  # the DBCV bars


# --- adp (its own panel: computed here, in the background) ---------------------------------------


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
    assert "Purity of the 5 neighbors" in text and "Purity expected by chance" in text and "Pairs at distance 1" in text
    assert len(_graphs(content)) == 1  # the silhouette panels
    assert "How to read these indices" in text and "60 clustered subjects out of 60" in text


def test_the_adp_panel_says_it_is_computing_and_asks_to_keep_polling():
    content, pending = adp_quality_content_for(_run(method="adp", reduction_method="raw"), lambda _run: None)

    assert pending is True and "Computing" in _text(content)


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
            {"id": "selected-page-tab", "property": "data", "value": "clustering"},
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
        assert "Computing" in json.dumps(payload["cluster-quality-content"], ensure_ascii=False)  # still computing: keep polling
        time.sleep(0.05)

    assert payload["cluster-quality-poll"]["disabled"] is True
    assert "Purity of the 1 neighbors" in json.dumps(payload["cluster-quality-content"], ensure_ascii=False)


def _save_run(tmp_path, method, X, labels, params, extra_arrays=None):
    import json

    run_dir = tmp_path / "results" / "lesion" / "clustering" / "production" / method / "umap" / "15-10_x"
    metadata = pd.DataFrame({"subject_id": [f"sub-{i}" for i in range(len(X))], "cluster_label": labels})
    readme = ["# test run", "", f"Params used: {json.dumps(params)}"]
    save_matrix(run_dir, X, metadata, readme_lines=readme, overwrite=False, extra_arrays=extra_arrays)
    return ProductionRun("lesion", "clustering", method, "15-10_x", run_dir, reduction_method="umap")

def test_run_soft_membership_reads_the_saved_membership(tmp_path):
    X = np.zeros((6, 2))
    run = _save_run(tmp_path, "hdbscan_soft", X, _SOFT_LABELS, {"min_cluster_size": 2}, extra_arrays={"membership": _SOFT_MEMBERSHIP})

    summary = run_soft_membership(run)

    assert summary.n_noise == 1 and list(summary.clusters.index) == [0, 1]


def test_run_soft_membership_refuses_a_run_without_membership_npy(tmp_path):
    run = _save_run(tmp_path, "hdbscan_soft", np.zeros((6, 2)), _SOFT_LABELS, {"min_cluster_size": 2})

    with pytest.raises(ValueError, match="membership.npy"):
        run_soft_membership(run)
