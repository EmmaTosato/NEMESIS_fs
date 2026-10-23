"""Unit tests for the tabs of the Embedding Explorer page (src/analysis/embedding_app.py)."""

import pytest

from src.analysis.embedding_app import (
    PAGE_TAB_LABELS,
    TAB_CLUSTERING,
    TAB_DENDROGRAM,
    TAB_EMBEDDING,
    ProductionRun,
    active_page_tab,
    build_app,
    index_entries_for,
    page_tabs_for,
)
from tests.unit.test_embedding_app import _clustering_params_file, _lesion_cfg, _make_run_dir, _sdc_cfg


def _run(pipeline="clustering", method="agglomerative", modality="lesion") -> ProductionRun:
    return ProductionRun(modality, pipeline, method, "run", None, reduction_method=None if pipeline == "dim_reduction" else "umap")


AGGLOMERATIVE, KMEANS, DIM_REDUCTION = _run(), _run(method="kmeans"), _run("dim_reduction", "umap")


def test_a_dim_reduction_run_has_only_the_embedding_tab():
    assert page_tabs_for(DIM_REDUCTION) == [TAB_EMBEDDING]


def test_a_clustering_run_has_the_clustering_tab_and_only_an_agglomerative_one_the_dendrogram():
    assert page_tabs_for(KMEANS) == [TAB_EMBEDDING, TAB_CLUSTERING]
    assert page_tabs_for(AGGLOMERATIVE) == [TAB_EMBEDDING, TAB_CLUSTERING, TAB_DENDROGRAM]


def test_no_run_has_no_tab():
    assert page_tabs_for(None) == []


def test_the_chosen_tab_is_kept_while_the_run_has_it_and_otherwise_the_page_falls_back_to_the_embedding():
    assert active_page_tab(AGGLOMERATIVE, TAB_DENDROGRAM) == TAB_DENDROGRAM
    assert active_page_tab(KMEANS, TAB_DENDROGRAM) == TAB_EMBEDDING  # a run that has no dendrogram
    assert active_page_tab(DIM_REDUCTION, TAB_CLUSTERING) == TAB_EMBEDDING
    assert active_page_tab(AGGLOMERATIVE, None) == TAB_EMBEDDING


def test_there_is_no_active_tab_without_a_run():
    with pytest.raises(ValueError, match="without a run"):
        active_page_tab(None, TAB_EMBEDDING)


def test_the_index_of_a_tab_lists_only_its_sections_and_the_run_choice():
    anchors = lambda run, tab: [anchor for anchor, _label in index_entries_for(run, tab)]  # noqa: E731

    assert anchors(AGGLOMERATIVE, TAB_EMBEDDING)[0] == "controls-section"
    assert "cluster-map-panel" not in anchors(AGGLOMERATIVE, TAB_EMBEDDING)
    assert "lesion-panel" not in anchors(AGGLOMERATIVE, TAB_CLUSTERING)
    assert anchors(AGGLOMERATIVE, TAB_DENDROGRAM) == ["controls-section", "dendrogram-panel"]


def test_the_evaluation_is_the_last_section_of_the_clustering_tab():
    assert index_entries_for(KMEANS, TAB_CLUSTERING)[-1][0] == "cluster-quality-panel"


def test_every_section_of_a_run_is_in_the_index_of_exactly_one_tab():
    for run in (AGGLOMERATIVE, KMEANS, DIM_REDUCTION):
        in_tabs = [anchor for tab in PAGE_TAB_LABELS for anchor, _ in index_entries_for(run, tab) if anchor != "controls-section"]

        assert sorted(in_tabs) == sorted(anchor for anchor, _ in index_entries_for(run) if anchor != "controls-section")


def test_the_index_of_a_tab_that_does_not_exist_raises():
    with pytest.raises(ValueError, match="unknown tab"):
        index_entries_for(KMEANS, "evaluation")


def _find(component, wanted_id):
    if getattr(component, "id", None) == wanted_id:
        return component
    children = getattr(component, "children", None)
    for child in children if isinstance(children, (list, tuple)) else [children]:
        if child is not None and not isinstance(child, str):
            found = _find(child, wanted_id)
            if found is not None:
                return found
    return None


@pytest.fixture
def layout(tmp_path):
    run_dir = _make_run_dir(tmp_path / "results", run_name="run-2d", n_dims=2)
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-2d", run_dir)
    return build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path), tmp_path / "cache").layout


def test_the_panels_sit_in_the_tab_they_belong_to(layout):
    tabs = {
        TAB_EMBEDDING: ["embedding-section", "lesion-panel", "disconnectome-panel", "pca-map-panel"],
        TAB_CLUSTERING: [
            "clustering-section", "cluster-map-panel", "disconnection-map-panel", "representative-subject-panel",
            "cluster-description-panel", "cluster-composition-panel", "cluster-quality-panel",
        ],
        TAB_DENDROGRAM: ["dendrogram-panel"],
    }
    for tab, panels in tabs.items():
        ids = [getattr(child, "id", None) for child in _find(layout, f"tab-{tab}").children]
        assert [i for i in ids if i in panels] == panels  # in page order; the embedding tab also has its description and graph
        assert not [p for tab_, others in tabs.items() if tab_ != tab for p in others if p in ids]


def test_the_page_opens_on_the_embedding_tab_with_the_others_hidden(layout):
    assert getattr(_find(layout, "tab-embedding"), "style", None) is None
    assert _find(layout, "tab-clustering").style == {"display": "none"}
    assert _find(layout, "tab-dendrogram").style == {"display": "none"}
    assert _find(layout, "selected-page-tab").data == TAB_EMBEDDING


def test_the_tab_bar_has_one_button_per_tab_with_the_embedding_active(layout):
    bar = _find(layout, "page-tab-bar")

    assert [button.children for button in bar.children] == list(PAGE_TAB_LABELS.values())
    assert [button.className for button in bar.children] == ["tab-btn active", "tab-btn", "tab-btn"]


# --- a tab that is not shown builds nothing (callbacks) ----------------------------------------------------------

import json  # noqa: E402

from tests.unit.test_embedding_app_all_clusters import ALL_CLUSTERS, _app, _post, _run as _clustering_run  # noqa: E402

CLUSTERING_PANELS = [
    ("cluster-map-content", [("cluster-picker", "value", 0)]),
    ("representative-subject-content", [("cluster-picker", "value", 0)]),
    ("cluster-description-content", [("cluster-picker", "value", 0)]),
    ("cluster-composition-content", []),
]  # the evaluation has two outputs (its content and its polling): test_a_hidden_clustering_tab_stops_the_polling_of_the_evaluation


@pytest.mark.parametrize(("output", "extra_inputs"), CLUSTERING_PANELS)
@pytest.mark.parametrize("selected", [TAB_EMBEDDING, TAB_DENDROGRAM])  # the dendrogram tab is not one a kmeans run has
def test_the_clustering_panels_build_nothing_while_another_tab_is_shown(tmp_path, monkeypatch, output, extra_inputs, selected):
    run = _clustering_run(tmp_path)
    app = _app(tmp_path, run)

    def _no_reads(path, *args, **kwargs):
        raise AssertionError(f"file read for a hidden tab: {path}")

    monkeypatch.setattr("src.analysis.anatomical_maps.nib.load", _no_reads)
    response = _post(app, [(output, "children")], [("run-picker", "value", run.key), *extra_inputs, ("selected-page-tab", "data", selected)])

    assert response.status_code == 200
    assert response.get_json()["response"][output]["children"] == []


def test_the_disconnection_panel_builds_nothing_while_another_tab_is_shown(tmp_path):
    run = _clustering_run(tmp_path, modality="sdc")

    response = _post(
        _app(tmp_path, run), [("disconnection-map-content", "children")],
        [("run-picker", "value", run.key), ("cluster-picker", "value", ALL_CLUSTERS), ("selected-disconnection-mode", "data", "percent"),
         ("selected-page-tab", "data", TAB_EMBEDDING)],
    )

    assert response.get_json()["response"]["disconnection-map-content"]["children"] == []


def test_a_hidden_clustering_tab_stops_the_polling_of_the_evaluation(tmp_path):
    run = _clustering_run(tmp_path)

    response = _post(
        _app(tmp_path, run), [("cluster-quality-content", "children"), ("cluster-quality-poll", "disabled")],
        [("run-picker", "value", run.key), ("cluster-quality-poll", "n_intervals", 3), ("selected-page-tab", "data", TAB_EMBEDDING)],
    )

    answer = response.get_json()["response"]
    assert answer["cluster-quality-content"]["children"] == [] and answer["cluster-quality-poll"]["disabled"] is True


def test_the_clustering_tab_builds_its_panels_again_when_it_is_shown(tmp_path):
    run = _clustering_run(tmp_path)

    response = _post(
        _app(tmp_path, run), [("cluster-composition-content", "children")],
        [("run-picker", "value", run.key), ("selected-page-tab", "data", TAB_CLUSTERING)],
    )

    assert "composition-grid" in json.dumps(response.get_json()["response"])


def test_tab_is_active_follows_the_fallback_of_active_page_tab():
    from src.analysis.embedding_app import tab_is_active

    assert tab_is_active(AGGLOMERATIVE, TAB_DENDROGRAM, TAB_DENDROGRAM)
    assert not tab_is_active(KMEANS, TAB_DENDROGRAM, TAB_DENDROGRAM)  # falls back to the embedding
    assert tab_is_active(KMEANS, TAB_DENDROGRAM, TAB_EMBEDDING)
