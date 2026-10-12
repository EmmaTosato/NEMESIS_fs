"""Unit tests for the run-comparison section and the page index of src/analysis/embedding_app.py."""

import json

import numpy as np
import pandas as pd
import pytest
from dash import dcc, html

from src.analysis.embedding_app import (
    COMPARISON_MODE_CLUSTERS,
    COMPARISON_MODE_MODALITY,
    ProductionRun,
    build_app,
    cluster_pair_anatomy_for,
    cluster_pair_content_for,
    comparable_runs,
    comparison_candidates,
    comparison_content_for,
    comparison_incompatibility,
    index_entries_for,
    pair_cluster_option_label,
    run_metadata,
)
from src.utils.artifacts import save_matrix
from tests.unit.test_embedding_app import (
    _clustering_params_file,
    _lesion_cfg,
    _make_disconnectome_subject,
    _make_lesion_subject,
    _make_run_dir,
    _sdc_cfg,
)

_EMBEDDING = np.array([[0.0, 0.0], [1.0, 0.0], [10.0, 0.0], [11.0, 0.0]])
_SUBJECTS = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003", "sub-STUNIPD0004"]


def _make_clustering_run(
    results_root,
    modality="lesion",
    method="kmeans",
    run_name="03-09_s1-k2",
    subjects=None,
    labels=(0, 0, 1, 1),
    embedding=None,
    input_path="results/lesion/dim_reduction/production/umap/emb-1",
    reduction_method="umap",
    reduction_metric="euclidean",
    reduction_n_components=2,
    params=None,
):
    """A clustering production run with the config.md shape the comparison reads (input_path,
    reduction_*) and a cluster_label column in its metadata."""
    run_dir = results_root / modality / "clustering" / "production" / method / reduction_method / run_name
    subjects = _SUBJECTS if subjects is None else subjects
    metadata = pd.DataFrame({"subject_id": subjects, "cluster_label": list(labels)})
    config_block = {
        "input_path": input_path,
        "reduction_method": reduction_method,
        "reduction_n_components": str(reduction_n_components),
        "reduction_metric": reduction_metric,
    }
    readme_lines = [
        "# test run", "", "## Config", "```json", json.dumps(config_block), "```", "",
        f"Params used: {json.dumps(params or {'n_clusters': 2})}",
    ]
    matrix = _EMBEDDING[: len(subjects)] if embedding is None else embedding
    save_matrix(run_dir, matrix, metadata, readme_lines=readme_lines, overwrite=False)
    return ProductionRun(modality, "clustering", method, run_name, run_dir, reduction_method=reduction_method)


@pytest.fixture
def _registry_root(tmp_path, monkeypatch):
    from src.utils import participants as participants_registry

    root = tmp_path / "metadata"
    root.mkdir()
    header = [
        "subject_id", "original_id", "dataset", "disease_id", "has_lesion", "has_sdc", "has_features",
        "age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm", "lesion_side",
        "location_infratentorial_2mm", "location_subcortical_gray_2mm", "location_cortex_only_2mm",
        "location_cortex_white_boundary_2mm", "location_white_matter_only_2mm", "location_ventricle_2mm",
        "location_unlabeled_2mm", "location_dominant_2mm",
    ]
    rows = [
        [s, s, "UNIPD/WashU", "ST", "True", "True", "False", str(50 + i), "F" if i % 2 else "M", "12", str(i), str(1000 * (i + 1)),
         "left", "0.1", "0.2", "0.3", "0.1", "0.1", "0.1", "0.1", "cortex_only"]
        for i, s in enumerate(_SUBJECTS)
    ]
    (root / "participants.csv").write_text("\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n")
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def _params_file(tmp_path, methods=("kmeans",)):
    return _clustering_params_file(tmp_path, methods=methods)


# --- compatibility rules (between modalities) -----------------------------------------------


def test_a_run_is_not_comparable_with_itself(tmp_path):
    run = _make_clustering_run(tmp_path)

    assert comparison_incompatibility(run, run, _params_file(tmp_path)) == "le due run sono la stessa run"


def _modality_pair(tmp_path, **sdc_overrides):
    lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="03-09_s1-k5", params={"n_clusters": 5})
    sdc_kwargs = dict(modality="sdc", run_name="10-09_s2-k5", params={"n_clusters": 5}, input_path="results/sdc/x")
    sdc_kwargs.update(sdc_overrides)
    return lesion, _make_clustering_run(tmp_path, **sdc_kwargs)


def test_modality_mode_accepts_same_method_parameters_and_embedding_axis(tmp_path):
    lesion, sdc = _modality_pair(tmp_path)

    assert comparison_incompatibility(lesion, sdc, _params_file(tmp_path)) is None


def test_modality_mode_rejects_the_same_modality(tmp_path):
    lesion, _sdc = _modality_pair(tmp_path)
    other_lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="04-09_s1-k5", params={"n_clusters": 5})

    reason = comparison_incompatibility(lesion, other_lesion, _params_file(tmp_path))

    assert "modalità diverse" in reason


def test_modality_mode_rejects_a_different_clustering_method(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, method="gmm")

    reason = comparison_incompatibility(lesion, sdc, _params_file(tmp_path, methods=("kmeans", "gmm")))

    assert "metodi di clustering diversi" in reason


def test_modality_mode_rejects_different_method_parameters(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, params={"n_clusters": 4})

    reason = comparison_incompatibility(lesion, sdc, _params_file(tmp_path))

    assert "parametri del metodo diversi" in reason
    assert "n_clusters=5" in reason and "n_clusters=4" in reason


def test_modality_mode_rejects_a_different_upstream_metric(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, reduction_metric="dice")

    reason = comparison_incompatibility(lesion, sdc, _params_file(tmp_path))

    assert "embedding di partenza diversi" in reason


def test_modality_mode_rejects_a_different_number_of_components(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, reduction_n_components=3)

    assert "embedding di partenza diversi" in comparison_incompatibility(lesion, sdc, _params_file(tmp_path))


def test_candidates_are_all_the_clustering_runs_raw_ones_included(tmp_path):
    umap_run = _make_clustering_run(tmp_path, run_name="a")
    raw_run = _make_clustering_run(tmp_path, run_name="b", reduction_method="raw")
    dim_reduction_run = ProductionRun("lesion", "dim_reduction", "umap", "c", tmp_path / "c")

    assert comparison_candidates([umap_run, raw_run, dim_reduction_run]) == [umap_run, raw_run]


def test_comparable_runs_keeps_only_the_compatible_partners(tmp_path):
    lesion, sdc = _modality_pair(tmp_path)
    sdc_k4 = _make_clustering_run(tmp_path, modality="sdc", run_name="10-09_s2-k4", params={"n_clusters": 4})
    other_lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="04-09_s1-k5", params={"n_clusters": 5})

    partners = comparable_runs([lesion, sdc, sdc_k4, other_lesion], lesion, _params_file(tmp_path))

    assert partners == [sdc]


def test_comparable_runs_skips_an_unreadable_run_and_logs_it(tmp_path, caplog):
    lesion, sdc = _modality_pair(tmp_path)
    broken = _make_clustering_run(tmp_path, modality="sdc", run_name="11-09_s2-k5", params={"n_clusters": 5})
    (broken.path / "config.md").write_text("no config block here")

    with caplog.at_level("WARNING"):
        partners = comparable_runs([lesion, sdc, broken], lesion, _params_file(tmp_path))

    assert partners == [sdc]
    assert any("excluded from the comparison options" in record.message for record in caplog.records)


# --- section content -------------------------------------------------------------------------


def _flatten_text(component) -> str:
    """All the plain text under a Dash component tree, with the runs of whitespace between
    components collapsed to one space."""
    return " ".join(_text_pieces(component).split())


def _text_pieces(component) -> str:
    if isinstance(component, str):
        return component
    if isinstance(component, (list, tuple)):
        return " ".join(_text_pieces(child) for child in component)
    children = getattr(component, "children", None)
    return "" if children is None else _text_pieces(children)


def _count_graphs(component) -> int:
    if isinstance(component, dcc.Graph):
        return 1
    if isinstance(component, (list, tuple)):
        return sum(_count_graphs(child) for child in component)
    children = getattr(component, "children", None)
    return 0 if children is None else _count_graphs(children)


def test_modality_content_reports_the_partial_intersection_and_the_clinical_profile(tmp_path, _registry_root):
    lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="03-09_s1-k5", params={"n_clusters": 5})
    sdc = _make_clustering_run(
        tmp_path, modality="sdc", run_name="10-09_s2-k5", params={"n_clusters": 5}, input_path="results/sdc/x",
        subjects=[*_SUBJECTS[1:], "sub-STUNIPD0099"], labels=(1, 1, 0, 0),
    )

    content = comparison_content_for(lesion, sdc, _params_file(tmp_path))

    text = _flatten_text(content)
    assert "3 soggetti in comune" in text
    assert "solo in A: 1" in text and "solo in B: 1" in text
    assert "Profilo clinico dei cluster" in text
    assert "Distanza tra centroidi" not in text


def test_content_for_an_incompatible_pair_names_the_reason(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, params={"n_clusters": 4})

    content = comparison_content_for(lesion, sdc, _params_file(tmp_path))

    assert isinstance(content, html.P)
    assert "non sono confrontabili" in content.children


def test_content_for_runs_without_common_subjects_says_so(tmp_path):
    lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="03-09_s1-k5", params={"n_clusters": 5})
    sdc = _make_clustering_run(
        tmp_path, modality="sdc", run_name="10-09_s2-k5", params={"n_clusters": 5}, input_path="results/sdc/x",
        subjects=["sub-STUNIPD0090", "sub-STUNIPD0091"], labels=(0, 1), embedding=_EMBEDDING[:2],
    )

    content = comparison_content_for(lesion, sdc, _params_file(tmp_path))

    assert isinstance(content, html.P)
    assert "intersection is empty" in content.children


# --- two clusters of one run -----------------------------------------------------------------


def test_pair_content_has_the_summary_clinical_regression_and_centroid_blocks(tmp_path, _registry_root):
    run = _make_clustering_run(tmp_path, labels=(0, 0, 1, 1))

    content = cluster_pair_content_for(run, 0, 1)

    text = _flatten_text(content)
    assert isinstance(content, html.Div)
    assert "Primo cluster: cluster 0 · 2 soggetti" in text and "Secondo cluster: cluster 1 · 2 soggetti" in text
    assert "Profilo demografico e clinico" in text and "Età (anni)" in text and "Sesso" in text
    assert "Cosa distingue i due cluster" in text
    # the registry has the same location shares for every subject, so the regression cannot be fitted:
    # the block says why instead of showing nothing
    assert "constant among the subjects used" in text
    assert "Distanza tra i centroidi" in text
    # the centroids (0.5, 0) and (10.5, 0), each cluster 0.5 wide
    assert "10,00" in text and "0,50" in text


def test_pair_content_swaps_the_clusters_not_the_distance(tmp_path, _registry_root):
    run = _make_clustering_run(tmp_path, labels=(0, 0, 1, 1))

    forward, backward = _flatten_text(cluster_pair_content_for(run, 0, 1)), _flatten_text(cluster_pair_content_for(run, 1, 0))

    assert "Primo cluster: cluster 1" in backward
    assert "10,00" in forward and "10,00" in backward


def test_pair_content_names_the_noise_cluster(tmp_path, _registry_root):
    run = _make_clustering_run(tmp_path, labels=(-1, 0, 0, 1))

    text = _flatten_text(cluster_pair_content_for(run, -1, 0))

    assert "Primo cluster: rumore · 1 soggetti" in text


def test_pair_content_reports_an_empty_or_repeated_cluster(tmp_path, _registry_root):
    run = _make_clustering_run(tmp_path, labels=(0, 0, 1, 1))

    same = cluster_pair_content_for(run, 0, 0)
    empty = cluster_pair_content_for(run, 0, 7)

    assert isinstance(same, html.P) and "same cluster" in same.children
    assert isinstance(empty, html.P) and "no subjects with cluster_label=7" in empty.children


def test_pair_content_warns_about_a_subject_missing_from_the_registry(tmp_path, _registry_root):
    run = _make_clustering_run(
        tmp_path, subjects=[*_SUBJECTS[:3], "sub-STUNIPD0099"], labels=(0, 0, 1, 1), embedding=_EMBEDDING,
    )

    text = _flatten_text(cluster_pair_content_for(run, 0, 1))

    assert "1 soggetti dei due cluster non hanno una riga nel registro" in text
    assert "sub-STUNIPD0099" in text


def test_pair_centroid_block_says_a_raw_run_has_no_embedding(tmp_path, _registry_root):
    run = _make_clustering_run(tmp_path, reduction_method="raw", labels=(0, 0, 1, 1))

    text = _flatten_text(cluster_pair_content_for(run, 0, 1))

    assert "La run è su dati grezzi" in text
    assert "Profilo demografico e clinico" in text


def test_pair_content_refuses_a_dim_reduction_run(tmp_path):
    run = ProductionRun("lesion", "dim_reduction", "umap", "x", tmp_path)

    content = cluster_pair_content_for(run, 0, 1)

    assert isinstance(content, html.P) and "non è una run di clustering" in content.children


def test_pair_cluster_option_label_carries_the_size_and_names_the_noise():
    metadata = pd.DataFrame({"cluster_label": [-1, 0, 0, 0]})

    assert pair_cluster_option_label(0, metadata) == "Cluster 0 · 3 soggetti"
    assert pair_cluster_option_label(-1, metadata) == "Rumore · 1 soggetti"


def _anatomy_run(tmp_path, modality="lesion"):
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    for subject_id, dataset, voxel in zip(subject_ids, ["UNIPD/WashU"] * 2 + ["UKLFR/stroke_UKLFR"] * 2, [(1, 1, 1), (1, 1, 1), (2, 2, 2), (2, 2, 2)]):
        _make_lesion_subject(data_root, dataset, subject_id, [voxel])
        _make_disconnectome_subject(data_root, dataset, subject_id, {voxel: 1.0})
    run_dir = _make_run_dir(
        tmp_path / "results", modality=modality, pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    return ProductionRun(modality, "clustering", "kmeans", "run-a", run_dir, reduction_method="umap"), data_root


def test_pair_anatomy_shows_each_cluster_and_their_difference_for_a_lesion_run(tmp_path):
    run, data_root = _anatomy_run(tmp_path)

    content = cluster_pair_anatomy_for(run, 0, 1, _lesion_cfg(data_root), _sdc_cfg(data_root))

    text = _flatten_text(content)
    assert isinstance(content, html.Div)
    assert "Cluster 0 (n=2)" in text and "Cluster 1 (n=2)" in text
    assert "Differenza: cluster 0 meno cluster 1" in text
    assert "Anatomia della disconnessione" not in text


def test_pair_anatomy_adds_the_disconnection_maps_for_an_sdc_run(tmp_path):
    run, data_root = _anatomy_run(tmp_path, modality="sdc")

    text = _flatten_text(cluster_pair_anatomy_for(run, 0, 1, _lesion_cfg(data_root), _sdc_cfg(data_root)))

    assert "Anatomia della lesione" in text and "Anatomia della disconnessione" in text
    assert text.count("Differenza: cluster 0 meno cluster 1") == 2


def test_pair_anatomy_difference_is_signed_by_which_cluster_has_the_voxel(tmp_path):
    from src.analysis.cluster_pair import difference_image

    run, data_root = _anatomy_run(tmp_path)
    seen = {}

    def build(run_, metadata, label, cfg):
        from src.analysis.embedding_app import _build_cluster_overlap_view

        result = _build_cluster_overlap_view(run_, metadata, label, cfg)
        seen[label] = result[2]
        return result

    cluster_pair_anatomy_for(run, 0, 1, _lesion_cfg(data_root), _sdc_cfg(data_root), build_overlap_view=build)
    difference = difference_image(seen[0], seen[1]).get_fdata()

    assert difference[1, 1, 1] == pytest.approx(100.0)
    assert difference[2, 2, 2] == pytest.approx(-100.0)


def test_pair_anatomy_reports_a_cluster_with_no_file_on_disk(tmp_path):
    run, data_root = _anatomy_run(tmp_path)
    for path in (data_root / "UKLFR").rglob("*.nii.gz"):
        path.unlink()

    content = cluster_pair_anatomy_for(run, 0, 1, _lesion_cfg(data_root), _sdc_cfg(data_root))

    assert isinstance(content, html.Div)
    assert "status-message" in {getattr(child, "className", None) for child in content.children}


def test_pair_anatomy_rejects_the_same_cluster_twice(tmp_path):
    run, data_root = _anatomy_run(tmp_path)

    content = cluster_pair_anatomy_for(run, 0, 0, _lesion_cfg(data_root), _sdc_cfg(data_root))

    assert isinstance(content, html.P) and "lo stesso" in content.children


# --- page index ------------------------------------------------------------------------------


def _layout_ids(component) -> set[str]:
    ids = set()
    if isinstance(component, (list, tuple)):
        for child in component:
            ids |= _layout_ids(child)
        return ids
    component_id = getattr(component, "id", None)
    if isinstance(component_id, str):
        ids.add(component_id)
    children = getattr(component, "children", None)
    if children is not None:
        ids |= _layout_ids(children)
    return ids


def test_index_hides_the_sections_a_run_does_not_have(tmp_path):
    lesion_dr = ProductionRun("lesion", "dim_reduction", "umap", "x", tmp_path)
    lesion_cl = ProductionRun("lesion", "clustering", "kmeans", "x", tmp_path, reduction_method="umap")
    sdc_cl = ProductionRun("sdc", "clustering", "kmeans", "x", tmp_path, reduction_method="umap")

    def anchors(run):
        return [anchor for anchor, _label in index_entries_for(run)]

    assert "clustering-section" not in anchors(lesion_dr) and "disconnectome-panel" not in anchors(lesion_dr)
    assert "clustering-section" in anchors(lesion_cl) and "disconnection-map-panel" not in anchors(lesion_cl)
    assert "disconnection-map-panel" in anchors(sdc_cl) and "disconnectome-panel" in anchors(sdc_cl)
    for run in (None, lesion_dr, lesion_cl, sdc_cl):
        assert anchors(run)[0] == "controls-section" and anchors(run)[-1] == "comparison-section"


def test_every_index_anchor_is_a_real_element_of_the_page(tmp_path):
    run = _make_clustering_run(tmp_path)
    app = build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _params_file(tmp_path))
    ids = _layout_ids(app.layout)

    sdc_run = ProductionRun("sdc", "clustering", "kmeans", "x", tmp_path, reduction_method="umap")
    every_anchor = {anchor for case in (None, run, sdc_run) for anchor, _label in index_entries_for(case)}

    assert every_anchor <= ids


def _post(client, outputs_id, inputs, state_mode, changed):
    body = {
        "output": f"{outputs_id}.children",
        "outputs": {"id": outputs_id, "property": "children"},
        "inputs": inputs,
        "changedPropIds": changed,
        "state": [{"id": "selected-comparison-mode", "property": "data", "value": state_mode}],
    }
    return client.post("/_dash-update-component", data=json.dumps(body), content_type="application/json")


def test_the_modality_content_callback_end_to_end(tmp_path, _registry_root):
    lesion, sdc = _modality_pair(tmp_path)
    app = build_app([lesion, sdc], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _params_file(tmp_path))
    app.server.config["TESTING"] = True

    response = _post(
        app.server.test_client(), "comparison-content",
        [
            {"id": "comparison-run-a", "property": "value", "value": lesion.key},
            {"id": "comparison-run-b", "property": "value", "value": sdc.key},
            {"id": "comparison-cluster-1", "property": "value", "value": None},
            {"id": "comparison-cluster-2", "property": "value", "value": None},
        ],
        COMPARISON_MODE_MODALITY, ["comparison-run-b.value"],
    )

    assert response.status_code == 200
    assert "4 soggetti in comune" in json.dumps(response.get_json())


def test_the_cluster_pair_content_callback_end_to_end(tmp_path, _registry_root):
    run = _make_clustering_run(tmp_path, labels=(0, 0, 1, 1))
    app = build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _params_file(tmp_path))
    app.server.config["TESTING"] = True
    client = app.server.test_client()
    inputs = [
        {"id": "comparison-run-a", "property": "value", "value": run.key},
        {"id": "comparison-run-b", "property": "value", "value": None},
        {"id": "comparison-cluster-1", "property": "value", "value": 0},
        {"id": "comparison-cluster-2", "property": "value", "value": 1},
    ]

    response = _post(client, "comparison-content", inputs, COMPARISON_MODE_CLUSTERS, ["comparison-cluster-2.value"])

    assert response.status_code == 200
    body = json.dumps(response.get_json(), ensure_ascii=False)
    assert "Profilo demografico e clinico" in body and "Distanza tra i centroidi" in body

    inputs[3]["value"] = None
    incomplete = _post(client, "comparison-content", inputs, COMPARISON_MODE_CLUSTERS, ["comparison-cluster-2.value"])
    assert "Scegli i due cluster da confrontare" in json.dumps(incomplete.get_json())


def test_the_cluster_options_callback_lists_the_clusters_of_the_chosen_run(tmp_path):
    run = _make_clustering_run(tmp_path, labels=(0, 0, 1, 1))
    app = build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _params_file(tmp_path))
    app.server.config["TESTING"] = True
    body = {
        "output": "..comparison-cluster-1.options...comparison-cluster-1.value...comparison-cluster-2.options...comparison-cluster-2.value..",
        "outputs": [
            {"id": "comparison-cluster-1", "property": "options"}, {"id": "comparison-cluster-1", "property": "value"},
            {"id": "comparison-cluster-2", "property": "options"}, {"id": "comparison-cluster-2", "property": "value"},
        ],
        "inputs": [{"id": "comparison-run-a", "property": "value", "value": run.key}],
        "changedPropIds": ["comparison-run-a.value"],
        "state": [{"id": "selected-comparison-mode", "property": "data", "value": COMPARISON_MODE_CLUSTERS}],
    }

    response = app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")

    assert response.status_code == 200
    payload = response.get_json()["response"]
    assert [option["value"] for option in payload["comparison-cluster-1"]["options"]] == [0, 1]
    assert payload["comparison-cluster-1"]["value"] is None and payload["comparison-cluster-2"]["value"] is None


@pytest.mark.parametrize(
    ("pipeline", "expected_style"), [("dim_reduction", {"display": "none"}), ("clustering", {})]
)
def test_the_reduction_picker_is_hidden_only_for_a_dim_reduction_run(tmp_path, pipeline, expected_style):
    # Regression (08-10-26): for a dim_reduction run the Metodo already is the reduction method, so
    # "Riduzione" showed a single empty option next to it.
    run = _make_clustering_run(tmp_path, labels=(0, 0, 1, 1))
    app = build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _params_file(tmp_path))
    app.server.config["TESTING"] = True
    body = {
        "output": "reduction-picker-field.style",
        "outputs": {"id": "reduction-picker-field", "property": "style"},
        "inputs": [{"id": "pipeline-picker", "property": "value", "value": pipeline}],
        "changedPropIds": ["pipeline-picker.value"],
    }

    response = app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")

    assert response.status_code == 200
    assert response.get_json()["response"]["reduction-picker-field"]["style"] == expected_style
