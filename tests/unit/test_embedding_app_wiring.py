"""The callbacks no other test used to run.

Everything the panels build is covered by a test that calls the builder directly; what was not
covered is the wiring around them - the callbacks that decide which run is shown, which tab and
which panels are visible, what the colour buttons do, and what each "Save" button hands back.
Measured with coverage before these were written: 22 of the 44 callbacks were executed by no
test at all.

They are fired the way the browser fires them (tests/unit/embedding_app_callbacks.py). The app
under test is the same four-run app the pinned contract describes, so a callback that only
exists for some runs is registered here too.
"""

from __future__ import annotations

import json

import pytest

import tests.unit.test_embedding_app as fixtures
from src.analysis.embedding_app import build_app
from src.analysis.embedding_app.embedding_view import color_mode_description_children
from src.analysis.embedding_app.picker import PICKER_FIELDS, UNSET
from src.analysis.embedding_app.runs import ProductionRun
from tests.unit.embedding_app_callbacks import PREVENTED, fire, fire_one, key_for
from tests.unit.embedding_app_contract import build_fixture_app

LESION_DR = "lesion/dim_reduction/umap/lesion-run"
LESION_CL = "lesion/clustering/kmeans/umap/cl-run"
SDC_DR = "sdc/dim_reduction/umap/sdc-dr-run"

COLOR_BUTTONS = [{"mode": m, "type": "color-mode-btn"} for m in ("neutral", "dataset", "volume")]
GRID_BUTTONS = [{"grid": g, "type": "grid-btn"} for g in ("lesion", "sdc")]
TAB_BUTTONS = [{"tab": t, "type": "page-tab-btn"} for t in ("embedding", "clustering", "dendrogram")]


@pytest.fixture
def app(tmp_path):
    return build_fixture_app(tmp_path)


def _tab_group(prop: str) -> list[str]:
    """One Output on the wildcard tab-button id: one output holding all three buttons."""
    return [f'{json.dumps(b, sort_keys=True, separators=(",", ":"))}.{prop}' for b in TAB_BUTTONS]


def _wildcard_state(buttons: list[dict]) -> list:
    """A wildcard State(..., "id"): one entry per matching component, each holding its own id."""
    return [[{"id": button, "property": "id", "value": button} for button in buttons]]


# --- Which run is shown ------------------------------------------------------------------

def test_no_run_chosen_shows_the_message_and_hides_the_run_content(app):
    content, message = fire(
        app, ["run-content.style", "no-run-message.style"], [("run-picker.value", UNSET)]
    ).values()

    assert content["style"] == {"display": "none"}
    assert message["style"] == {}


def test_a_chosen_run_shows_the_content_and_hides_the_message(app):
    response = fire(app, ["run-content.style", "no-run-message.style"], [("run-picker.value", LESION_DR)])

    assert response["run-content"]["style"] == {}
    assert response["no-run-message"]["style"] == {"display": "none"}


def test_the_run_content_is_left_alone_before_the_picker_has_a_value(app):
    """None is not "no run chosen" (that is UNSET): it is the picker not having rendered yet,
    and overwriting the panels then would fight the callback that fills it."""
    assert fire(app, ["run-content.style", "no-run-message.style"], [("run-picker.value", None)]) is PREVENTED


# --- The tabs ----------------------------------------------------------------------------

def test_clicking_a_tab_button_selects_that_tab(app):
    selected = fire_one(
        app, "selected-page-tab.data",
        [[{"id": b, "property": "n_clicks", "value": 1} for b in TAB_BUTTONS], ("run-picker.value", LESION_CL)],
        changed=['{"tab":"clustering","type":"page-tab-btn"}.n_clicks'],
        state=[("selected-page-tab.data", "embedding")],
    )

    assert selected == "clustering"


def test_changing_run_falls_back_to_a_tab_that_run_actually_has(app):
    """A dim_reduction run has no clustering tab: staying on "clustering" after switching to it
    would show an empty page."""
    selected = fire_one(
        app, "selected-page-tab.data",
        [[{"id": b, "property": "n_clicks", "value": 1} for b in TAB_BUTTONS], ("run-picker.value", LESION_DR)],
        changed=["run-picker.value"],
        state=[("selected-page-tab.data", "clustering")],
    )

    assert selected == "embedding"


def test_a_run_with_one_tab_hides_the_whole_tab_bar(app):
    response = fire(
        app,
        [_tab_group("className"), _tab_group("style"),
         "page-tab-bar.style", "tab-embedding.style", "tab-clustering.style", "tab-dendrogram.style"],
        [("selected-page-tab.data", "embedding"), ("run-picker.value", LESION_DR)],
        state=_wildcard_state(TAB_BUTTONS),
        key=key_for(app, "page-tab-bar.style"),
    )

    assert response["page-tab-bar"]["style"] == {"display": "none"}
    assert response['{"tab":"clustering","type":"page-tab-btn"}']["style"] == {"display": "none"}
    assert response["tab-embedding"]["style"] == {"display": "block"}
    assert response["tab-clustering"]["style"] == {"display": "none"}


def test_a_clustering_run_shows_the_bar_and_marks_the_active_tab(app):
    response = fire(
        app,
        [_tab_group("className"), _tab_group("style"),
         "page-tab-bar.style", "tab-embedding.style", "tab-clustering.style", "tab-dendrogram.style"],
        [("selected-page-tab.data", "clustering"), ("run-picker.value", LESION_CL)],
        state=_wildcard_state(TAB_BUTTONS),
        key=key_for(app, "page-tab-bar.style"),
    )

    assert response["page-tab-bar"]["style"] == {}
    assert response['{"tab":"clustering","type":"page-tab-btn"}']["className"] == "tab-btn active"
    assert response['{"tab":"embedding","type":"page-tab-btn"}']["className"] == "tab-btn"
    # kmeans, not agglomerative: no tree to walk down.
    assert response['{"tab":"dendrogram","type":"page-tab-btn"}']["style"] == {"display": "none"}
    assert response["tab-clustering"]["style"] == {"display": "block"}


# --- The colour buttons ------------------------------------------------------------------

def test_clicking_a_colour_button_selects_that_mode(app):
    selected = fire_one(
        app, "selected-color-mode.data",
        [[{"id": b, "property": "n_clicks", "value": 1} for b in COLOR_BUTTONS]],
        changed=['{"mode":"dataset","type":"color-mode-btn"}.n_clicks'],
    )

    assert selected == "dataset"


def test_only_the_selected_colour_button_is_marked_active(app):
    response = fire(
        app,
        [f'{json.dumps(b, sort_keys=True, separators=(",", ":"))}.className' for b in COLOR_BUTTONS],
        [("selected-color-mode.data", "dataset")],
        state=_wildcard_state(COLOR_BUTTONS),
        key='{"mode":["ALL"],"type":"color-mode-btn"}.className',
    )

    marked = {key for key, value in response.items() if value["className"] == "active"}
    assert marked == {'{"mode":"dataset","type":"color-mode-btn"}'}


def test_the_description_under_the_plot_follows_the_selected_mode(app):
    assert fire_one(app, "color-description.children", [("selected-color-mode.data", "side")]) == json.loads(
        json.dumps(color_mode_description_children("side"), default=lambda o: o.to_plotly_json())
    )


def test_the_grid_row_appears_only_for_a_mode_that_reads_a_grid(app):
    assert fire_one(app, "color-grid-row.style", [("selected-color-mode.data", "volume")]) == {}
    assert fire_one(app, "color-grid-row.style", [("selected-color-mode.data", "dataset")]) == {"display": "none"}


def test_clicking_a_grid_button_selects_that_grid(app):
    selected = fire_one(
        app, "selected-grid.data",
        [[{"id": b, "property": "n_clicks", "value": 1} for b in GRID_BUTTONS]],
        changed=['{"grid":"sdc","type":"grid-btn"}.n_clicks'],
    )

    assert selected == "sdc"


def test_only_the_selected_grid_button_is_marked_active(app):
    response = fire(
        app,
        [f'{json.dumps(b, sort_keys=True, separators=(",", ":"))}.className' for b in GRID_BUTTONS],
        [("selected-grid.data", "sdc")],
        state=_wildcard_state(GRID_BUTTONS),
        key='{"grid":["ALL"],"type":"grid-btn"}.className',
    )

    marked = {key for key, value in response.items() if value["className"] == "active"}
    assert marked == {'{"grid":"sdc","type":"grid-btn"}'}


# --- The plot ------------------------------------------------------------------------------

def test_the_plot_is_drawn_for_the_chosen_run_and_mode(app):
    content = fire_one(
        app, "graph-area.children",
        [("run-picker.value", LESION_DR), ("selected-color-mode.data", "neutral"), ("selected-grid.data", "lesion")],
    )

    assert "status-message" not in json.dumps(content)
    assert json.dumps(content).count("embedding-graph") >= 1


def test_no_plot_is_drawn_while_no_run_is_chosen(app):
    for value in (None, UNSET):
        assert fire(
            app, "graph-area.children",
            [("run-picker.value", value), ("selected-color-mode.data", "neutral"), ("selected-grid.data", "lesion")],
        ) is PREVENTED


# --- The hyperparameter selectors ----------------------------------------------------------

def test_the_second_parameter_selector_is_hidden_for_a_dim_reduction_run(app):
    label, style = fire(
        app, ["tag-params-label.children", "tag-params-rest-field.style"],
        [("pipeline-picker.value", "dim_reduction"), ("method-picker.value", "umap")],
    ).values()

    assert style["style"] == {"display": "none"}
    assert label["children"] == "Parameters"


def test_agglomerative_splits_its_parameters_and_calls_the_first_one_k(app):
    """agglomerative is the one method whose k gets a selector of its own (SPLIT_TAG_PARAMS)."""
    response = fire(
        app, ["tag-params-label.children", "tag-params-rest-field.style"],
        [("pipeline-picker.value", "clustering"), ("method-picker.value", "agglomerative")],
    )

    assert response["tag-params-label"]["children"] == "k"
    assert response["tag-params-rest-field"]["style"] == {}


def test_a_clustering_method_with_one_parameter_block_hides_the_second_selector(app):
    response = fire(
        app, ["tag-params-label.children", "tag-params-rest-field.style"],
        [("pipeline-picker.value", "clustering"), ("method-picker.value", "kmeans")],
    )

    assert response["tag-params-label"]["children"] == "Parameters"
    assert response["tag-params-rest-field"]["style"] == {"display": "none"}


# --- The index of the sections ---------------------------------------------------------------

def test_with_no_run_the_index_lists_only_what_a_runless_page_has(app):
    links = fire_one(app, "page-index-links.children", [("run-picker.value", UNSET), ("selected-page-tab.data", None)])

    labels = [link["props"]["children"] for link in links]
    assert labels == ["Run choice"]


def test_the_index_follows_the_run_and_the_tab(app):
    embedding = fire_one(
        app, "page-index-links.children", [("run-picker.value", LESION_CL), ("selected-page-tab.data", "embedding")]
    )
    clustering = fire_one(
        app, "page-index-links.children", [("run-picker.value", LESION_CL), ("selected-page-tab.data", "clustering")]
    )

    assert [link["props"]["children"] for link in embedding] == ["Run choice", "Embedding Visualization", "Lesion anatomy"]
    assert "Cluster description" in [link["props"]["children"] for link in clustering]


# --- The disconnection-map mode buttons -------------------------------------------------------

def test_clicking_a_disconnection_mode_button_selects_that_mode(app):
    buttons = [{"mode": m, "type": "disconnection-mode-btn"} for m in ("percent", "mean")]

    selected = fire_one(
        app, "selected-disconnection-mode.data",
        [[{"id": b, "property": "n_clicks", "value": 1} for b in buttons]],
        changed=['{"mode":"mean","type":"disconnection-mode-btn"}.n_clicks'],
    )

    assert selected == "mean"


def test_only_the_selected_disconnection_mode_button_is_marked_active(app):
    buttons = [{"mode": m, "type": "disconnection-mode-btn"} for m in ("percent", "mean")]

    response = fire(
        app,
        [f'{json.dumps(b, sort_keys=True, separators=(",", ":"))}.className' for b in buttons],
        [("selected-disconnection-mode.data", "mean")],
        state=[[{"id": b, "property": "id", "value": b} for b in buttons]],
        key='{"mode":["ALL"],"type":"disconnection-mode-btn"}.className',
    )

    marked = {key for key, value in response.items() if value["className"] == "active"}
    assert marked == {'{"mode":"mean","type":"disconnection-mode-btn"}'}


# --- The disconnectome viewer -------------------------------------------------------------------

def test_the_disconnectome_viewer_stays_empty_for_a_lesion_run(app):
    """The panel is hidden for a lesion run anyway, but its content must reset rather than
    attempt a resolution that cannot succeed - those subjects have no disconnectome at all."""
    response = fire(
        app, ["disconnectome-viewer-content.children", "disconnectome-viewer-subject.data"],
        [("embedding-graph.clickData", {"points": [{"text": "sub-STUNIPD0001"}]}), ("run-picker.value", LESION_DR)],
        changed=["embedding-graph.clickData"],
    )

    assert response["disconnectome-viewer-subject"]["data"] is None
    assert "Click a point" in json.dumps(response["disconnectome-viewer-content"]["children"])


def test_changing_run_resets_the_disconnectome_viewer(app):
    response = fire(
        app, ["disconnectome-viewer-content.children", "disconnectome-viewer-subject.data"],
        [("embedding-graph.clickData", {"points": [{"text": "sub-STUNIPD0001"}]}), ("run-picker.value", SDC_DR)],
        changed=["run-picker.value"],
    )

    assert response["disconnectome-viewer-subject"]["data"] is None


# --- The component maps ---------------------------------------------------------------------

def test_the_component_maps_do_nothing_for_a_run_that_is_not_pca(app):
    assert fire(
        app, ["pca-map-content.children", "pca-map-poll.disabled"],
        [("run-picker.value", LESION_DR), ("pca-component-picker.value", 1), ("pca-map-poll.n_intervals", 0)],
    ) is PREVENTED


def test_the_component_maps_do_nothing_before_a_component_is_chosen(app):
    assert fire(
        app, ["pca-map-content.children", "pca-map-poll.disabled"],
        [("run-picker.value", LESION_DR), ("pca-component-picker.value", None), ("pca-map-poll.n_intervals", 0)],
    ) is PREVENTED


# --- The Save buttons with nothing to save -----------------------------------------------------

@pytest.mark.parametrize(
    ("output", "button", "subject_store"),
    [
        ("lesion-download.data", "lesion-save-btn.n_clicks", "lesion-viewer-subject.data"),
        ("lesion-png-download.data", "lesion-png-btn.n_clicks", "lesion-viewer-subject.data"),
        ("lesion-glass-png-download.data", "lesion-glass-png-btn.n_clicks", "lesion-viewer-subject.data"),
        ("disconnectome-download.data", "disconnectome-save-btn.n_clicks", "disconnectome-viewer-subject.data"),
        ("disconnectome-png-download.data", "disconnectome-png-btn.n_clicks", "disconnectome-viewer-subject.data"),
        ("disconnectome-glass-png-download.data", "disconnectome-glass-png-btn.n_clicks",
         "disconnectome-viewer-subject.data"),
    ],
)
def test_a_save_button_offers_nothing_while_no_subject_is_clicked(app, output, button, subject_store):
    """Every Save button reads the Store the viewer fills, not the click on the plot: with no
    subject there is nothing to hand over, and offering a file would mean offering a stale one
    from whichever run was shown before (see the Store's own docstring in the layout)."""
    assert fire(
        app, output, [(button, 1)],
        state=[(subject_store, None), ("run-picker.value", LESION_DR)],
    ) is PREVENTED


@pytest.mark.parametrize(
    ("output", "button", "subject_store"),
    [
        ("lesion-download.data", "lesion-save-btn.n_clicks", "lesion-viewer-subject.data"),
        ("lesion-png-download.data", "lesion-png-btn.n_clicks", "lesion-viewer-subject.data"),
        ("disconnectome-download.data", "disconnectome-save-btn.n_clicks", "disconnectome-viewer-subject.data"),
    ],
)
def test_a_save_button_offers_nothing_for_a_subject_with_no_file_on_disk(app, output, button, subject_store):
    """The fixture runs have no image files at all: resolution raises, and the button must stay
    silent rather than propagate - the visible panel already says what is missing."""
    assert fire(
        app, output, [(button, 1)],
        state=[(subject_store, "sub-STUNIPD0001"), ("run-picker.value", SDC_DR)],
    ) is PREVENTED


# --- The cascade of selectors -----------------------------------------------------------------

PICKER_IDS = {field: f"{field.replace('_', '-')}-picker" for field in PICKER_FIELDS}


@pytest.fixture
def picker_app(tmp_path):
    """An app whose clustering runs actually reach the selectors.

    index_runs leaves out a run whose params do not carry the method's registered tag_param
    (`n_clusters` for kmeans), which is what happens to the contract fixture's clustering runs -
    fine for the panels, useless for testing the cascade. These carry it, so all four runs are
    offered. Returns the app and the runs, so a test names a run by its own key rather than
    repeating the key-building rule."""
    results, data = tmp_path / "results", tmp_path / "data"
    clusters = {"cluster_label": [0, 0, 1, 1]}
    runs = [
        ProductionRun("lesion", "dim_reduction", "umap", "lesion-dr",
                      fixtures._make_run_dir(results, run_name="lesion-dr")),
        ProductionRun("sdc", "dim_reduction", "umap", "sdc-dr",
                      fixtures._make_run_dir(results, modality="sdc", run_name="sdc-dr")),
        ProductionRun("lesion", "clustering", "kmeans", "lesion-cl",
                      fixtures._make_run_dir(results, pipeline="clustering", method="kmeans", run_name="lesion-cl",
                                             params={"n_clusters": 2}, extra_metadata=clusters),
                      reduction_method="umap"),
        ProductionRun("sdc", "clustering", "kmeans", "sdc-cl",
                      fixtures._make_run_dir(results, modality="sdc", pipeline="clustering", method="kmeans",
                                             run_name="sdc-cl", params={"n_clusters": 3}, extra_metadata=clusters),
                      reduction_method="umap"),
    ]
    app = build_app(
        runs, fixtures._lesion_cfg(data), fixtures._sdc_cfg(data),
        fixtures._clustering_params_file(tmp_path), tmp_path / "cache",
    )
    return app, {run.run_name: run.key for run in runs}


def _pickers(app, chosen: dict[str, object], changed: str | None = None, reset: int | None = None) -> dict:
    """Fires the one callback that owns all ten selectors and gives back {field: (options, value)}.

    Every selector is both an input and an output of it, so a test has to hand it the whole
    current state; `chosen` says what is set, the rest is "---" (not a filter). With neither
    `changed` nor `reset` nothing triggered the callback, which is the first render - the one
    case the cascade treats specially."""
    values = [(f"{PICKER_IDS[field]}.value", chosen.get(field, UNSET)) for field in PICKER_FIELDS]
    if changed is not None:
        triggered = [f"{PICKER_IDS[changed]}.value"]
    elif reset is not None:
        triggered = ["reset-pickers-btn.n_clicks"]
    else:
        triggered = []
    response = fire(
        app,
        [f"{PICKER_IDS[field]}.{prop}" for field in PICKER_FIELDS for prop in ("options", "value")],
        [*values, ("reset-pickers-btn.n_clicks", reset)],
        changed=triggered,
    )
    return {
        field: (
            [option["value"] for option in response[PICKER_IDS[field]]["options"]],
            response[PICKER_IDS[field]]["value"],
        )
        for field in PICKER_FIELDS
    }


def test_the_first_render_sets_only_the_modality_and_the_pipeline_and_chooses_no_run(picker_app):
    app, _ = picker_app

    state = _pickers(app, {})

    assert state["modality"][1] == "lesion"
    assert state["pipeline"][1] == "dim_reduction"
    assert state["run"][1] == UNSET
    assert state["method"][1] == UNSET


def test_choosing_a_pipeline_narrows_the_runs_the_last_selector_lists(picker_app):
    app, keys = picker_app

    state = _pickers(app, {"modality": "lesion", "pipeline": "clustering"}, changed="pipeline")

    assert state["run"][0] == [UNSET, keys["lesion-cl"]]
    assert state["method"][0] == [UNSET, "kmeans"]


def test_a_selector_only_offers_values_that_still_give_a_run(picker_app):
    """The cascade reads left to right: with modality=sdc set, every later selector must offer
    only what an sdc run has."""
    app, keys = picker_app

    state = _pickers(app, {"modality": "sdc", "pipeline": "clustering"}, changed="modality")

    assert state["run"][0] == [UNSET, keys["sdc-cl"]]


def test_choosing_a_run_fills_every_selector_still_unset_with_that_runs_own_values(picker_app):
    app, keys = picker_app

    state = _pickers(app, {"run": keys["lesion-cl"]}, changed="run")

    assert state["modality"][1] == "lesion"
    assert state["pipeline"][1] == "clustering"
    assert state["method"][1] == "kmeans"
    assert state["run"][1] == keys["lesion-cl"]


def test_a_filter_that_would_leave_no_run_at_all_goes_back_to_not_being_a_filter(picker_app):
    """modality=sdc and a method no sdc run has cannot both hold. The selector the user just
    touched wins, and the other drops back to "---" rather than listing nothing."""
    app, _ = picker_app

    state = _pickers(app, {"modality": "sdc", "method": "nonexistent-method"}, changed="modality")

    assert state["modality"][1] == "sdc"
    assert state["method"][1] == UNSET
    assert state["run"][0] != [UNSET]


def test_the_restart_button_puts_every_selector_back_to_no_filter(picker_app):
    app, keys = picker_app

    state = _pickers(app, {"modality": "lesion", "pipeline": "clustering", "run": keys["lesion-cl"]}, reset=1)

    assert [state[field][1] for field in PICKER_FIELDS] == [UNSET] * len(PICKER_FIELDS)
    assert len(state["run"][0]) == 5  # "---" plus all four runs


# --- The Save buttons with something to save ---------------------------------------------------

SUBJECTS = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003", "sub-STUNIPD0004"]


@pytest.fixture
def saveable_app(tmp_path):
    """An app whose subjects have real images on disk, so every Save button has something to
    hand over - with no file the buttons take their PreventUpdate path and the code that builds
    the download never runs.

    Returns the app and the two runs: an sdc clustering run (every panel and every button exists
    for it) and a lesion dim_reduction run."""
    results, data = tmp_path / "results", tmp_path / "data"
    for subject in SUBJECTS:
        fixtures._make_lesion_subject(data, "UNIPD/WashU", subject, [(1, 1, 1)])
        fixtures._make_disconnectome_subject(data, "UNIPD/WashU", subject, {(1, 1, 1): 0.8})
    metadata = {"subject_id": SUBJECTS, "dataset": ["UNIPD/WashU"] * 4, "cluster_label": [0, 0, 1, 1]}
    sdc_dir = fixtures._make_run_dir(
        results, modality="sdc", pipeline="clustering", method="kmeans", run_name="sdc-cl",
        params={"n_clusters": 2}, extra_metadata=metadata,
    )
    lesion_dir = fixtures._make_run_dir(
        results, run_name="lesion-dr", extra_metadata={"subject_id": SUBJECTS, "dataset": ["UNIPD/WashU"] * 4},
    )
    runs = [
        ProductionRun("sdc", "clustering", "kmeans", "sdc-cl", sdc_dir, reduction_method="umap"),
        ProductionRun("lesion", "dim_reduction", "umap", "lesion-dr", lesion_dir),
    ]
    app = build_app(
        runs, fixtures._lesion_cfg(data), fixtures._sdc_cfg(data),
        fixtures._clustering_params_file(tmp_path), tmp_path / "cache",
    )
    return app, runs[0], runs[1]


def _downloaded(result) -> dict:
    """The file a Save button handed over: Dash wraps it as {filename, content, base64, ...}."""
    assert result is not PREVENTED, "il pulsante non ha offerto niente"
    assert result["filename"], result
    assert result["content"], result
    return result


@pytest.mark.parametrize(
    ("output", "button", "suffix"),
    [
        ("lesion-download.data", "lesion-save-btn.n_clicks", "_lesion_3d.html"),
        ("lesion-png-download.data", "lesion-png-btn.n_clicks", "_lesion.png"),
        ("lesion-glass-png-download.data", "lesion-glass-png-btn.n_clicks", "_lesion_glass.png"),
    ],
)
def test_every_lesion_save_button_hands_over_the_clicked_subjects_own_file(saveable_app, output, button, suffix):
    app, _sdc_run, lesion_run = saveable_app

    result = _downloaded(fire_one(
        app, output, [(button, 1)],
        state=[("lesion-viewer-subject.data", SUBJECTS[0]), ("run-picker.value", lesion_run.key)],
    ))

    assert result["filename"] == f"{SUBJECTS[0]}{suffix}"


@pytest.mark.parametrize(
    ("output", "button", "suffix"),
    [
        ("disconnectome-download.data", "disconnectome-save-btn.n_clicks", "_disconnectome.html"),
        ("disconnectome-png-download.data", "disconnectome-png-btn.n_clicks", "_disconnectome.png"),
        ("disconnectome-glass-png-download.data", "disconnectome-glass-png-btn.n_clicks",
         "_disconnectome_glass.png"),
    ],
)
def test_every_disconnectome_save_button_hands_over_the_clicked_subjects_own_file(
    saveable_app, output, button, suffix
):
    app, sdc_run, _lesion_run = saveable_app

    result = _downloaded(fire_one(
        app, output, [(button, 1)],
        state=[("disconnectome-viewer-subject.data", SUBJECTS[0]), ("run-picker.value", sdc_run.key)],
    ))

    assert result["filename"] == f"{SUBJECTS[0]}{suffix}"


def test_the_disconnectome_viewer_shows_the_clicked_subject_of_an_sdc_run(saveable_app):
    app, sdc_run, _lesion_run = saveable_app

    response = fire(
        app, ["disconnectome-viewer-content.children", "disconnectome-viewer-subject.data"],
        [("embedding-graph.clickData", {"points": [{"text": SUBJECTS[0]}]}), ("run-picker.value", sdc_run.key)],
        changed=["embedding-graph.clickData"],
    )

    assert response["disconnectome-viewer-subject"]["data"] == SUBJECTS[0]
    assert "Click a point" not in json.dumps(response["disconnectome-viewer-content"]["children"])


def test_the_representative_subject_panel_names_a_real_subject_of_the_cluster(saveable_app):
    app, sdc_run, _lesion_run = saveable_app

    content = fire_one(
        app, "representative-subject-content.children",
        [("run-picker.value", sdc_run.key), ("cluster-picker.value", 0), ("selected-page-tab.data", "clustering")],
        changed=["cluster-picker.value"],
    )

    shown = json.dumps(content)
    assert "status-message" not in shown
    assert any(subject in shown for subject in SUBJECTS[:2])


@pytest.mark.parametrize(
    ("output", "button"),
    [
        ("representative-download.data", "representative-save-btn.n_clicks"),
        ("representative-png-download.data", "representative-png-btn.n_clicks"),
    ],
)
def test_the_representative_subject_save_buttons_hand_over_that_subjects_file(saveable_app, output, button):
    app, sdc_run, _lesion_run = saveable_app

    result = _downloaded(fire_one(
        app, output, [(button, 1)],
        state=[("run-picker.value", sdc_run.key), ("cluster-picker.value", 0)],
    ))

    assert result["filename"].startswith("cluster_0_representative_")
    assert any(subject in result["filename"] for subject in SUBJECTS[:2])


@pytest.mark.parametrize(
    ("output", "button"),
    [
        ("cluster-download.data", "cluster-save-btn.n_clicks"),
        ("cluster-png-download.data", "cluster-png-btn.n_clicks"),
    ],
)
def test_the_cluster_overlap_map_save_buttons_hand_over_the_chosen_cluster(saveable_app, output, button):
    app, sdc_run, _lesion_run = saveable_app

    result = _downloaded(fire_one(
        app, output, [(button, 1)],
        state=[("run-picker.value", sdc_run.key), ("cluster-picker.value", 1)],
    ))

    assert result["filename"].startswith("cluster_1_overlap_map.")


@pytest.mark.parametrize(
    ("output", "button"),
    [
        ("disconnection-download.data", "disconnection-save-btn.n_clicks"),
        ("disconnection-png-download.data", "disconnection-png-btn.n_clicks"),
    ],
)
def test_the_disconnection_map_save_buttons_hand_over_the_chosen_cluster(saveable_app, output, button):
    app, sdc_run, _lesion_run = saveable_app

    result = _downloaded(fire_one(
        app, output, [(button, 1)],
        state=[("run-picker.value", sdc_run.key), ("cluster-picker.value", 1)],
    ))

    assert result["filename"].startswith("cluster_1_disconnection_mean_map.")
