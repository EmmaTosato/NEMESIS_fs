"""Unit tests for the linked run pickers (Dato -> ... -> Parametri -> Run) of src/analysis/embedding_app.py."""

import json

import pytest

from src.analysis.embedding_app import (
    PICKER_FIELDS,
    ProductionRun,
    build_app,
    resolve_pickers,
    run_picker_values,
)
from tests.unit.test_embedding_app import _clustering_params_file, _lesion_cfg, _make_run_dir, _sdc_cfg


@pytest.fixture
def _runs(tmp_path):
    """Runs that differ on every picker step: two modalities, both pipelines, two metrics/n_components."""
    root = tmp_path / "results"

    def dim_reduction(modality, run_name, metric, n_components):
        path = _make_run_dir(
            root, modality=modality, run_name=run_name, params={"metric": metric, "n_components": n_components}
        )
        return ProductionRun(modality, "dim_reduction", "umap", run_name, path)

    def clustering(modality, run_name, n_clusters, metric, n_components):
        path = _make_run_dir(
            root, modality=modality, pipeline="clustering", method="kmeans", run_name=run_name,
            params={"n_clusters": n_clusters}, reduction_metric=metric, reduction_n_components=n_components,
        )
        return ProductionRun(modality, "clustering", "kmeans", run_name, path, reduction_method="umap")

    return [
        dim_reduction("lesion", "10-08_a", "euclidean", 2),
        dim_reduction("lesion", "11-08_b", "dice", 3),
        clustering("lesion", "12-08_k3", 3, "euclidean", 2),
        clustering("lesion", "13-08_k5", 5, "dice", 3),
        clustering("sdc", "14-08_s3", 3, "euclidean", 2),
    ]


def _first_render(modality="lesion"):
    return {field: modality if field == "modality" else None for field in PICKER_FIELDS}


def test_first_render_fills_every_step_and_picks_the_first_combination(_runs, tmp_path):
    options, chosen = resolve_pickers(_runs, _first_render(), None, _clustering_params_file(tmp_path))

    assert chosen["pipeline"] == "dim_reduction" and chosen["method"] == "umap"
    assert chosen["metric"] == "dice"  # first of the sorted metrics, as before
    assert chosen["run"] == "lesion/dim_reduction/umap/11-08_b"
    assert all(chosen[field] in options[field] for field in PICKER_FIELDS)


def test_choosing_a_run_aligns_every_step_to_its_left_with_that_run(_runs, tmp_path):
    # Regression (16-10-26): the steps were separate callbacks and the Run list never fed back, so
    # the steps could show values of a different run than the one on screen.
    params_file = _clustering_params_file(tmp_path)
    current = {
        "modality": "lesion", "pipeline": "dim_reduction", "method": "umap", "reduction": "—",
        "metric": "euclidean", "n_components": 2, "tag_params": "—", "run": "sdc/clustering/kmeans/umap/14-08_s3",
    }

    options, chosen = resolve_pickers(_runs, current, "run", params_file)

    assert chosen == {
        "modality": "sdc", "pipeline": "clustering", "method": "kmeans", "reduction": "umap",
        "metric": "euclidean", "n_components": 2, "tag_params": "n_clusters=3", "run": current["run"],
    }
    assert options["pipeline"] == ["clustering"]  # sdc has no dim_reduction run to offer


def test_changing_the_modality_offers_only_what_that_modality_has(_runs, tmp_path):
    # Regression (16-10-26): after switching lesion -> sdc the pickers kept offering the other
    # modality's pipelines, methods and parameters.
    params_file = _clustering_params_file(tmp_path)
    current = {
        "modality": "sdc", "pipeline": "dim_reduction", "method": "umap", "reduction": "—",
        "metric": "dice", "n_components": 3, "tag_params": "—", "run": "lesion/dim_reduction/umap/11-08_b",
    }

    options, chosen = resolve_pickers(_runs, current, "modality", params_file)

    assert options["pipeline"] == ["clustering"] and chosen["pipeline"] == "clustering"
    assert options["metric"] == ["euclidean"] and options["n_components"] == [2]
    assert options["tag_params"] == ["n_clusters=3"]
    assert options["run"] == ["sdc/clustering/kmeans/umap/14-08_s3"]


def test_a_step_keeps_its_value_when_it_is_still_offered_after_an_upstream_change(_runs, tmp_path):
    params_file = _clustering_params_file(tmp_path)
    current = {
        "modality": "lesion", "pipeline": "clustering", "method": "kmeans", "reduction": "umap",
        "metric": "dice", "n_components": 3, "tag_params": "n_clusters=5", "run": "lesion/clustering/kmeans/umap/13-08_k5",
    }

    # metric changes to euclidean: n_components 3 no longer exists for it, so it falls back to 2 and
    # the parameters follow; the run is the only one left for that combination.
    options, chosen = resolve_pickers(_runs, {**current, "metric": "euclidean"}, "metric", params_file)

    assert chosen["n_components"] == 2 and chosen["tag_params"] == "n_clusters=3"
    assert chosen["run"] == "lesion/clustering/kmeans/umap/12-08_k3"


def test_every_run_resolves_to_itself_with_every_step_offering_its_value(_runs, tmp_path):
    params_file = _clustering_params_file(tmp_path)
    stale = _first_render()

    for run in _runs:
        options, chosen = resolve_pickers(_runs, {**stale, "run": run.key}, "run", params_file)

        assert chosen["run"] == run.key
        assert {f: chosen[f] for f in PICKER_FIELDS if f != "run"} == run_picker_values(run, params_file)
        assert all(chosen[field] in options[field] for field in PICKER_FIELDS)


def test_resolve_pickers_raises_when_a_step_has_nothing_to_offer(tmp_path):
    with pytest.raises(ValueError, match="picker step 'modality' has no option"):
        resolve_pickers([], _first_render(), None, _clustering_params_file(tmp_path))


def test_the_picker_callback_answers_in_one_response_for_every_step(_runs, tmp_path):
    # End to end through Dash: the single callback has every step as input and output.
    app = build_app(_runs, _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path))
    app.server.config["TESTING"] = True
    ids = {field: f"{field.replace('_', '-')}-picker" for field in PICKER_FIELDS}
    values = {field: None for field in PICKER_FIELDS} | {"modality": "sdc"}
    body = {
        "output": ".." + "...".join(f"{ids[f]}.{prop}" for f in PICKER_FIELDS for prop in ("options", "value")) + "..",
        "outputs": [{"id": ids[f], "property": prop} for f in PICKER_FIELDS for prop in ("options", "value")],
        "inputs": [{"id": ids[f], "property": "value", "value": values[f]} for f in PICKER_FIELDS],
        "changedPropIds": [f"{ids['modality']}.value"],
    }

    response = app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")

    assert response.status_code == 200
    payload = response.get_json()["response"]
    assert payload[ids["pipeline"]]["value"] == "clustering"
    assert payload[ids["run"]]["value"] == "sdc/clustering/kmeans/umap/14-08_s3"
    assert payload[ids["run"]]["options"] == [{"label": "14-08_s3", "value": "sdc/clustering/kmeans/umap/14-08_s3"}]
