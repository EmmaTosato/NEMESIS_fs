"""Unit tests for the run selectors (Dato ... Parametri, Run) of src/analysis/embedding_app.py: optional filters."""

import json
import logging

import pytest

from src.analysis.embedding_app import (
    NO_METRIC,
    NO_N_COMPONENTS,
    PICKER_FIELDS,
    PRODUCTION_PIPELINES,
    UNSET,
    ProductionRun,
    build_app,
    index_runs,
    resolve_pickers,
    run_picker_values,
)
from tests.unit.test_embedding_app import _clustering_params_file, _lesion_cfg, _make_run_dir, _sdc_cfg


@pytest.fixture
def _runs(tmp_path):
    """Runs that differ on every selector: two modalities, both pipelines, several metrics/components, a pca (no
    metric), a clustering on raw data (no embedding) and a run whose name has no date."""
    root = tmp_path / "results"

    def dim_reduction(modality, method, run_name, params):
        path = _make_run_dir(root, modality=modality, method=method, run_name=run_name, params=params)
        return ProductionRun(modality, "dim_reduction", method, run_name, path)

    def clustering(modality, run_name, n_clusters, metric, n_components, reduction="umap"):
        path = _make_run_dir(
            root, modality=modality, pipeline="clustering", method="kmeans", run_name=run_name, reduction_method=reduction,
            params={"n_clusters": n_clusters}, reduction_metric=metric, reduction_n_components=n_components,
        )
        return ProductionRun(modality, "clustering", "kmeans", run_name, path, reduction_method=reduction)

    return [
        dim_reduction("lesion", "umap", "10-08_a", {"metric": "euclidean", "n_components": 2}),
        dim_reduction("lesion", "umap", "11-08_b", {"metric": "dice", "n_components": 3}),
        dim_reduction("lesion", "pca", "09-08_p", {"n_components": 5}),
        dim_reduction("lesion", "umap", "undated", {"metric": "dice", "n_components": 2}),
        clustering("lesion", "12-08_k3", 3, "euclidean", 2),
        clustering("lesion", "13-08_k5", 5, "dice", 3),
        clustering("lesion", "13-08_raw", 3, "", "", reduction="raw"),
        clustering("sdc", "14-08_s3", 3, "euclidean", 2),
    ]


@pytest.fixture
def _indexed(_runs, tmp_path):
    return index_runs(_runs, _clustering_params_file(tmp_path))


def _key(modality, pipeline, method, run_name, reduction=None):
    parts = [modality, pipeline, method] + ([reduction] if reduction else []) + [run_name]
    return "/".join(parts)


def _current(**filters):
    """The state the selectors are in: the filters given, every other one open, no run chosen yet."""
    return {field: filters.get(field, UNSET) for field in PICKER_FIELDS} | {"run": filters.get("run")}


# --- the value of a run at each selector ------------------------------------------------------------------------

def test_a_dim_reduction_run_takes_its_own_metric_and_components_and_has_no_parametri(_runs, tmp_path):
    values = run_picker_values(_runs[0], _clustering_params_file(tmp_path))

    assert values == {
        "modality": "lesion", "pipeline": "dim_reduction", "method": "umap", "reduction": NO_METRIC,
        "metric": "euclidean", "n_components": 2, "tag_params": NO_METRIC,
        "n_subjects": 4,
    }


def test_a_method_without_a_metric_has_the_sentinel_not_a_made_up_value(_runs, tmp_path):
    values = run_picker_values(_runs[2], _clustering_params_file(tmp_path))  # pca

    assert values["metric"] == NO_METRIC and values["n_components"] == 5


def test_a_clustering_run_takes_the_upstream_embedding_axis_and_its_own_parameters(_runs, tmp_path):
    values = run_picker_values(_runs[5], _clustering_params_file(tmp_path))

    assert (values["reduction"], values["metric"], values["n_components"], values["tag_params"]) == (
        "umap", "dice", 3, "n_clusters=5",
    )


def test_a_clustering_run_on_raw_data_has_no_embedding_axis(_runs, tmp_path):
    values = run_picker_values(_runs[6], _clustering_params_file(tmp_path))

    assert (values["reduction"], values["metric"], values["n_components"]) == ("raw", NO_METRIC, NO_N_COMPONENTS)


def test_a_method_missing_from_the_registry_has_the_sentinel_for_parametri_not_an_error(_runs, tmp_path):
    values = run_picker_values(_runs[4], _clustering_params_file(tmp_path, methods=("gmm",)))  # kmeans not registered

    assert values["tag_params"] == NO_METRIC


# --- the index ---------------------------------------------------------------------------------------------------

def test_the_index_is_oldest_first_with_an_undated_run_last(_runs, tmp_path):
    indexed = index_runs(_runs, _clustering_params_file(tmp_path))

    names = [item.run.run_name for item in indexed]
    assert names == ["09-08_p", "10-08_a", "11-08_b", "12-08_k3", "13-08_k5", "13-08_raw", "14-08_s3", "undated"]


def test_one_corrupt_run_is_left_out_with_a_warning_and_the_others_stay(_runs, tmp_path, caplog):
    (_runs[1].path / "config.md").write_text("no params here")

    with caplog.at_level(logging.WARNING):
        indexed = index_runs(_runs, _clustering_params_file(tmp_path))

    assert "11-08_b" not in [item.run.run_name for item in indexed] and len(indexed) == len(_runs) - 1
    assert "11-08_b" in caplog.text


def test_an_index_with_no_readable_run_raises(tmp_path):
    with pytest.raises(ValueError, match="no run has readable params"):
        index_runs([], _clustering_params_file(tmp_path))


# --- the selectors -----------------------------------------------------------------------------------------------

def test_the_first_render_opens_on_the_first_modality_and_the_preferred_pipeline_with_the_rest_open(_indexed):
    state = resolve_pickers(_indexed, {field: None for field in PICKER_FIELDS}, None)

    assert state.chosen["modality"] == "lesion" and state.chosen["pipeline"] == "dim_reduction"
    assert all(state.chosen[f] == UNSET for f in ("method", "reduction", "metric", "n_components", "tag_params"))
    assert state.chosen["run"] == _key("lesion", "dim_reduction", "umap", "undated")  # the most recent of the listed runs


def test_every_filter_starts_with_the_open_choice_and_lists_only_what_exists(_indexed):
    state = resolve_pickers(_indexed, _current(modality="sdc"), "modality")

    assert state.options["pipeline"] == [UNSET, "clustering"]  # sdc has no dim_reduction run
    assert state.options["metric"] == [UNSET, "euclidean"] and state.options["n_components"] == [UNSET, 2]
    assert state.options["modality"][0] == UNSET


def test_a_filter_offers_the_values_of_the_runs_the_other_filters_leave_not_its_own_narrowing(_indexed):
    # method=umap narrows the runs, but the method selector still offers pca: it is computed without itself.
    state = resolve_pickers(_indexed, _current(modality="lesion", pipeline="dim_reduction", method="umap"), "method")

    assert state.options["method"] == [UNSET, "pca", "umap"]
    assert state.options["metric"] == [UNSET, "dice", "euclidean"]  # pca's missing metric is not offered here
    assert state.chosen["method"] == "umap"


def test_the_run_list_shows_exactly_the_runs_that_match_the_filters_that_are_set(_indexed):
    state = resolve_pickers(_indexed, _current(modality="lesion", pipeline="clustering", metric="dice"), "metric")

    assert state.options["run"] == [UNSET, _key("lesion", "clustering", "kmeans", "13-08_k5", "umap")]


def test_choosing_a_run_leaves_the_open_filters_open(_indexed):
    run = _key("lesion", "clustering", "kmeans", "12-08_k3", "umap")

    state = resolve_pickers(_indexed, _current(modality="lesion", run=run), "run")

    assert state.chosen["run"] == run
    assert state.chosen["modality"] == "lesion" and state.chosen["method"] == UNSET and state.chosen["metric"] == UNSET


def test_run_offers_the_open_choice_first_and_keeps_it_while_chosen(_indexed):
    state = resolve_pickers(_indexed, _current(modality="lesion", run=UNSET), "run")
    after_filter = resolve_pickers(_indexed, _current(modality="lesion", pipeline="clustering", run=UNSET), "pipeline")

    assert state.options["run"][0] == UNSET and len(state.options["run"]) > 1
    assert state.chosen["run"] == UNSET
    assert after_filter.chosen["run"] == UNSET  # a filter change does not pick a run for the user
    assert UNSET not in state.run_labels


def test_the_first_render_does_not_start_on_the_open_run_choice(_indexed):
    state = resolve_pickers(_indexed, {field: None for field in PICKER_FIELDS}, None)

    assert state.chosen["run"] != UNSET


def test_the_chosen_run_stays_while_the_filters_still_list_it_else_it_is_the_most_recent(_indexed):
    run = _key("lesion", "dim_reduction", "umap", "10-08_a")

    kept = resolve_pickers(_indexed, _current(modality="lesion", pipeline="dim_reduction", run=run), "pipeline")
    moved = resolve_pickers(_indexed, _current(modality="lesion", pipeline="clustering", run=run), "pipeline")

    assert kept.chosen["run"] == run
    assert moved.chosen["run"] == _key("lesion", "clustering", "kmeans", "13-08_raw", "raw")


def test_the_filter_just_changed_wins_and_one_that_would_leave_no_run_goes_back_to_open(_indexed):
    # pipeline=dim_reduction with a leftover method=kmeans from before: nothing matches both, the new pipeline wins.
    state = resolve_pickers(_indexed, _current(modality="lesion", pipeline="dim_reduction", method="kmeans"), "pipeline")

    assert state.chosen["pipeline"] == "dim_reduction" and state.chosen["method"] == UNSET
    assert state.options["run"][1:]  # never without a run to choose, besides UNSET


def test_a_leftover_filter_set_on_a_value_no_run_has_is_dropped(_indexed):
    state = resolve_pickers(_indexed, _current(modality="lesion", metric="no-such-metric"), "modality")

    assert state.chosen["metric"] == UNSET


def test_pipelines_are_offered_in_the_preferred_order_and_raw_reduction_last(_indexed):
    state = resolve_pickers(_indexed, _current(modality="lesion"), "modality")

    assert state.options["pipeline"][1:] == list(PRODUCTION_PIPELINES)
    assert state.options["reduction"] == [UNSET, "umap", NO_METRIC, "raw"]  # raw is last, whatever sorts before it


def test_a_run_is_labelled_with_the_values_of_the_filters_that_are_open(_indexed):
    open_state = resolve_pickers(_indexed, _current(modality="lesion"), "modality")
    set_state = resolve_pickers(_indexed, _current(modality="lesion", pipeline="clustering", method="kmeans", reduction="umap"), "reduction")

    assert open_state.run_labels[_key("lesion", "clustering", "kmeans", "12-08_k3", "umap")] == "12-08_k3  (clustering / kmeans / umap)"
    assert open_state.run_labels[_key("lesion", "dim_reduction", "umap", "10-08_a")] == "10-08_a  (dim_reduction / umap)"  # n.a. left out
    assert set_state.run_labels[_key("lesion", "clustering", "kmeans", "12-08_k3", "umap")] == "12-08_k3"


def test_the_picker_callback_answers_in_one_response_for_every_selector(_runs, tmp_path):
    app = build_app(_runs, _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path), tmp_path / "cache")
    app.server.config["TESTING"] = True
    ids = {field: f"{field.replace('_', '-')}-picker" for field in PICKER_FIELDS}
    values = {field: UNSET for field in PICKER_FIELDS} | {"modality": "sdc", "run": None}
    body = {
        "output": ".." + "...".join(f"{ids[f]}.{prop}" for f in PICKER_FIELDS for prop in ("options", "value")) + "..",
        "outputs": [{"id": ids[f], "property": prop} for f in PICKER_FIELDS for prop in ("options", "value")],
        "inputs": [{"id": ids[f], "property": "value", "value": values[f]} for f in PICKER_FIELDS],
        "changedPropIds": [f"{ids['modality']}.value"],
    }

    response = app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")

    assert response.status_code == 200
    payload = response.get_json()["response"]
    assert payload[ids["pipeline"]]["options"][0] == {"label": UNSET, "value": UNSET}
    assert payload[ids["run"]]["value"] == "sdc/clustering/kmeans/umap/14-08_s3"
    assert payload[ids["run"]]["options"] == [
        {"label": UNSET, "value": UNSET},
        {"label": "14-08_s3  (clustering / kmeans / umap)", "value": "sdc/clustering/kmeans/umap/14-08_s3"},
    ]
    assert payload[ids["n_components"]]["options"][0]["label"] == UNSET


def _post_run_picker(app, run_value, output_ids, output_props):
    body = {
        "output": output_ids,
        "outputs": output_props,
        "inputs": [{"id": "run-picker", "property": "value", "value": run_value}],
        "changedPropIds": ["run-picker.value"],
    }
    return app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")


def test_the_page_content_is_hidden_while_run_is_open_and_shown_for_a_run(_runs, tmp_path):
    app = build_app(_runs, _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path), tmp_path / "cache")
    app.server.config["TESTING"] = True
    output = "..run-content.style...no-run-message.style.."
    outputs = [{"id": "run-content", "property": "style"}, {"id": "no-run-message", "property": "style"}]

    hidden = _post_run_picker(app, UNSET, output, outputs).get_json()["response"]
    shown = _post_run_picker(app, "lesion/dim_reduction/umap/10-08_a", output, outputs).get_json()["response"]

    assert hidden["run-content"]["style"] == {"display": "none"} and hidden["no-run-message"]["style"] == {}
    assert shown["run-content"]["style"] == {} and shown["no-run-message"]["style"] == {"display": "none"}


def test_the_graph_is_not_drawn_while_run_is_open(_runs, tmp_path):
    app = build_app(_runs, _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path), tmp_path / "cache")
    app.server.config["TESTING"] = True
    body = {
        "output": "graph-area.children",
        "outputs": {"id": "graph-area", "property": "children"},
        "inputs": [
            {"id": "run-picker", "property": "value", "value": UNSET},
            {"id": "selected-color-mode", "property": "data", "value": "neutral"},
            {"id": "selected-grid", "property": "data", "value": "2mm"},
        ],
        "changedPropIds": ["run-picker.value"],
    }

    response = app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")

    assert response.status_code == 204  # PreventUpdate: no KeyError on runs_by_key["---"]


# --- the number of subjects ("Soggetti") -------------------------------------------------------------------------

def _with_subjects(indexed, counts):
    """The same runs, each with the subject count given (the fixture runs all share one matrix size)."""
    from dataclasses import replace
    return [replace(item, values={**item.values, "n_subjects": counts[item.run.run_name]}) for item in indexed]


def test_the_subject_count_of_a_run_is_read_from_its_manifest_without_loading_the_matrix(_runs, tmp_path):
    values = run_picker_values(_runs[0], _clustering_params_file(tmp_path))
    manifest = json.loads((_runs[0].path / "manifest.json").read_text())

    assert values["n_subjects"] == manifest["matrix_shape"][0]


def test_a_run_whose_manifest_has_no_shape_is_left_out_with_a_warning(_runs, tmp_path, caplog):
    (_runs[0].path / "manifest.json").write_text("{}")

    with caplog.at_level(logging.WARNING):
        indexed = index_runs(_runs, _clustering_params_file(tmp_path))

    assert _runs[0].key not in [item.run.key for item in indexed] and "matrix_shape" in caplog.text


def test_the_subjects_selector_filters_the_runs_and_is_filtered_by_the_others(_indexed):
    counts = {item.run.run_name: 100 for item in _indexed} | {"10-08_a": 5845, "12-08_k3": 5845, "13-08_k5": 5200}
    indexed = _with_subjects(_indexed, counts)

    state = resolve_pickers(indexed, _current(modality="lesion", n_subjects=5845), "n_subjects")
    assert set(state.options["run"][1:]) == {_key("lesion", "dim_reduction", "umap", "10-08_a"), _key("lesion", "clustering", "kmeans", "12-08_k3", "umap")}

    # with the method narrowed to kmeans, "Soggetti" offers only the counts of kmeans runs (sorted numerically)
    state = resolve_pickers(indexed, _current(modality="lesion", method="kmeans"), "method")
    assert state.options["n_subjects"] == [UNSET, 100, 5200, 5845]
