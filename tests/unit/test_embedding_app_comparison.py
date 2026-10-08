"""Unit tests for the run-comparison section and the page index of src/analysis/embedding_app.py."""

import json

import numpy as np
import pandas as pd
import pytest
from dash import dcc, html

from src.analysis.embedding_app import (
    COMPARISON_MODE_EMBEDDING,
    COMPARISON_MODE_MODALITY,
    ProductionRun,
    build_app,
    comparable_runs,
    comparison_candidates,
    comparison_content_for,
    comparison_incompatibility,
    index_entries_for,
)
from src.utils.artifacts import save_matrix
from tests.unit.test_embedding_app import _clustering_params_file, _lesion_cfg, _sdc_cfg

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
        "age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm",
    ]
    rows = [
        [s, s, "UNIPD/WashU", "ST", "True", "True", "False", str(50 + i), "F" if i % 2 else "M", "12", str(i), str(1000 * (i + 1))]
        for i, s in enumerate(_SUBJECTS)
    ]
    (root / "participants.csv").write_text("\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n")
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def _params_file(tmp_path, methods=("kmeans",)):
    return _clustering_params_file(tmp_path, methods=methods)


# --- compatibility rules ---------------------------------------------------------------------


def test_same_embedding_mode_accepts_two_methods_on_the_same_input(tmp_path):
    run_a = _make_clustering_run(tmp_path, method="kmeans")
    run_b = _make_clustering_run(tmp_path, method="gmm", params={"n_components": 2})

    assert comparison_incompatibility(run_a, run_b, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path)) is None


def test_same_embedding_mode_rejects_a_different_input_path(tmp_path):
    run_a = _make_clustering_run(tmp_path, run_name="a", input_path="results/lesion/dim_reduction/production/umap/emb-1")
    run_b = _make_clustering_run(tmp_path, run_name="b", input_path="results/lesion/dim_reduction/production/umap/emb-2")

    reason = comparison_incompatibility(run_a, run_b, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path))

    assert "non partono dallo stesso embedding" in reason


def test_same_embedding_mode_rejects_a_run_on_raw_data(tmp_path):
    run_a = _make_clustering_run(tmp_path, run_name="a")
    run_b = _make_clustering_run(tmp_path, run_name="b", reduction_method="raw")

    reason = comparison_incompatibility(run_a, run_b, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path))

    assert "dati grezzi" in reason


def test_a_run_is_not_comparable_with_itself(tmp_path):
    run = _make_clustering_run(tmp_path)

    assert comparison_incompatibility(run, run, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path)) == "le due run sono la stessa run"


def test_same_embedding_mode_raises_when_config_has_no_input_path(tmp_path):
    run_a = _make_clustering_run(tmp_path, run_name="a")
    run_b = _make_clustering_run(tmp_path, run_name="b")
    config = run_b.path / "config.md"
    config.write_text(config.read_text().replace('"input_path"', '"other_key"'))

    with pytest.raises(ValueError, match="no input_path"):
        comparison_incompatibility(run_a, run_b, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path))


def _modality_pair(tmp_path, **sdc_overrides):
    lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="03-09_s1-k5", params={"n_clusters": 5})
    sdc_kwargs = dict(modality="sdc", run_name="10-09_s2-k5", params={"n_clusters": 5}, input_path="results/sdc/x")
    sdc_kwargs.update(sdc_overrides)
    return lesion, _make_clustering_run(tmp_path, **sdc_kwargs)


def test_modality_mode_accepts_same_method_parameters_and_embedding_axis(tmp_path):
    lesion, sdc = _modality_pair(tmp_path)

    assert comparison_incompatibility(lesion, sdc, COMPARISON_MODE_MODALITY, _params_file(tmp_path)) is None


def test_modality_mode_rejects_the_same_modality(tmp_path):
    lesion, _sdc = _modality_pair(tmp_path)
    other_lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="04-09_s1-k5", params={"n_clusters": 5})

    reason = comparison_incompatibility(lesion, other_lesion, COMPARISON_MODE_MODALITY, _params_file(tmp_path))

    assert "modalità diverse" in reason


def test_modality_mode_rejects_a_different_clustering_method(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, method="gmm")

    reason = comparison_incompatibility(lesion, sdc, COMPARISON_MODE_MODALITY, _params_file(tmp_path, methods=("kmeans", "gmm")))

    assert "metodi di clustering diversi" in reason


def test_modality_mode_rejects_different_method_parameters(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, params={"n_clusters": 4})

    reason = comparison_incompatibility(lesion, sdc, COMPARISON_MODE_MODALITY, _params_file(tmp_path))

    assert "parametri del metodo diversi" in reason
    assert "n_clusters=5" in reason and "n_clusters=4" in reason


def test_modality_mode_rejects_a_different_upstream_metric(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, reduction_metric="dice")

    reason = comparison_incompatibility(lesion, sdc, COMPARISON_MODE_MODALITY, _params_file(tmp_path))

    assert "embedding di partenza diversi" in reason


def test_modality_mode_rejects_a_different_number_of_components(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, reduction_n_components=3)

    assert "embedding di partenza diversi" in comparison_incompatibility(
        lesion, sdc, COMPARISON_MODE_MODALITY, _params_file(tmp_path)
    )


def test_an_unknown_comparison_mode_raises(tmp_path):
    lesion, sdc = _modality_pair(tmp_path)

    with pytest.raises(ValueError, match="unknown comparison mode"):
        comparison_incompatibility(lesion, sdc, "other", _params_file(tmp_path))


def test_candidates_are_clustering_runs_and_the_embedding_mode_drops_raw_ones(tmp_path):
    umap_run = _make_clustering_run(tmp_path, run_name="a")
    raw_run = _make_clustering_run(tmp_path, run_name="b", reduction_method="raw")
    dim_reduction_run = ProductionRun("lesion", "dim_reduction", "umap", "c", tmp_path / "c")

    runs = [umap_run, raw_run, dim_reduction_run]

    assert comparison_candidates(runs, COMPARISON_MODE_EMBEDDING) == [umap_run]
    assert comparison_candidates(runs, COMPARISON_MODE_MODALITY) == [umap_run, raw_run]


def test_comparable_runs_keeps_only_the_compatible_partners(tmp_path):
    lesion, sdc = _modality_pair(tmp_path)
    sdc_k4 = _make_clustering_run(tmp_path, modality="sdc", run_name="10-09_s2-k4", params={"n_clusters": 4})
    other_lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="04-09_s1-k5", params={"n_clusters": 5})

    partners = comparable_runs([lesion, sdc, sdc_k4, other_lesion], lesion, COMPARISON_MODE_MODALITY, _params_file(tmp_path))

    assert partners == [sdc]


def test_comparable_runs_skips_an_unreadable_run_and_logs_it(tmp_path, caplog):
    run_a = _make_clustering_run(tmp_path, run_name="a")
    good = _make_clustering_run(tmp_path, run_name="b", method="gmm", params={"n_components": 2})
    broken = _make_clustering_run(tmp_path, run_name="c", method="agglomerative", params={"n_clusters": 2})
    (broken.path / "config.md").write_text("no config block here")

    with caplog.at_level("WARNING"):
        partners = comparable_runs([run_a, good, broken], run_a, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path))

    assert partners == [good]
    assert any("excluded from the comparison options" in record.message for record in caplog.records)


# --- section content -------------------------------------------------------------------------


def _flatten_text(component) -> str:
    """All the plain text under a Dash component tree."""
    if isinstance(component, str):
        return component
    if isinstance(component, (list, tuple)):
        return " ".join(_flatten_text(child) for child in component)
    children = getattr(component, "children", None)
    return "" if children is None else _flatten_text(children)


def _count_graphs(component) -> int:
    if isinstance(component, dcc.Graph):
        return 1
    if isinstance(component, (list, tuple)):
        return sum(_count_graphs(child) for child in component)
    children = getattr(component, "children", None)
    return 0 if children is None else _count_graphs(children)


def test_same_embedding_content_has_metrics_tables_and_centroid_distances(tmp_path):
    run_a = _make_clustering_run(tmp_path, method="kmeans", labels=(0, 0, 1, 1))
    run_b = _make_clustering_run(tmp_path, method="gmm", labels=(1, 1, 0, 0), params={"n_components": 2})

    content = comparison_content_for(run_a, run_b, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path))

    text = _flatten_text(content)
    assert isinstance(content, html.Div)
    assert "4 soggetti in comune" in text
    assert "Distanza tra centroidi" in text
    assert "Profilo clinico" not in text
    # 3 contingency heatmaps + residuals + centroid distances
    assert _count_graphs(content) == 5


def test_same_embedding_content_reports_embeddings_that_differ_in_the_data(tmp_path):
    run_a = _make_clustering_run(tmp_path, method="kmeans")
    run_b = _make_clustering_run(tmp_path, method="gmm", embedding=_EMBEDDING + 1.0, params={"n_components": 2})

    content = comparison_content_for(run_a, run_b, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path))

    assert "not in the same embedding" in _flatten_text(content)


def test_modality_content_reports_the_partial_intersection_and_the_clinical_profile(tmp_path, _registry_root):
    lesion = _make_clustering_run(tmp_path, modality="lesion", run_name="03-09_s1-k5", params={"n_clusters": 5})
    sdc = _make_clustering_run(
        tmp_path, modality="sdc", run_name="10-09_s2-k5", params={"n_clusters": 5}, input_path="results/sdc/x",
        subjects=[*_SUBJECTS[1:], "sub-STUNIPD0099"], labels=(1, 1, 0, 0),
    )

    content = comparison_content_for(lesion, sdc, COMPARISON_MODE_MODALITY, _params_file(tmp_path))

    text = _flatten_text(content)
    assert "3 soggetti in comune" in text
    assert "solo in A: 1" in text and "solo in B: 1" in text
    assert "Profilo clinico dei cluster" in text
    assert "Distanza tra centroidi" not in text


def test_content_for_an_incompatible_pair_names_the_reason(tmp_path):
    lesion, sdc = _modality_pair(tmp_path, params={"n_clusters": 4})

    content = comparison_content_for(lesion, sdc, COMPARISON_MODE_MODALITY, _params_file(tmp_path))

    assert isinstance(content, html.P)
    assert "non sono confrontabili" in content.children


def test_content_for_runs_without_common_subjects_says_so(tmp_path):
    run_a = _make_clustering_run(tmp_path, method="kmeans")
    run_b = _make_clustering_run(
        tmp_path, method="gmm", subjects=["sub-STUNIPD0090", "sub-STUNIPD0091"], labels=(0, 1),
        embedding=_EMBEDDING[:2], params={"n_components": 2},
    )

    content = comparison_content_for(run_a, run_b, COMPARISON_MODE_EMBEDDING, _params_file(tmp_path))

    assert isinstance(content, html.P)
    assert "intersection is empty" in content.children


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


def test_the_comparison_content_callback_end_to_end(tmp_path, _registry_root):
    run_a = _make_clustering_run(tmp_path, method="kmeans")
    run_b = _make_clustering_run(tmp_path, method="gmm", labels=(1, 1, 0, 0), params={"n_components": 2})
    app = build_app([run_a, run_b], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _params_file(tmp_path))
    app.server.config["TESTING"] = True
    client = app.server.test_client()

    body = {
        "output": "comparison-content.children",
        "outputs": {"id": "comparison-content", "property": "children"},
        "inputs": [
            {"id": "comparison-run-a", "property": "value", "value": run_a.key},
            {"id": "comparison-run-b", "property": "value", "value": run_b.key},
        ],
        "changedPropIds": ["comparison-run-b.value"],
        "state": [{"id": "selected-comparison-mode", "property": "data", "value": COMPARISON_MODE_EMBEDDING}],
    }
    response = client.post("/_dash-update-component", data=json.dumps(body), content_type="application/json")

    assert response.status_code == 200
    assert "4 soggetti in comune" in json.dumps(response.get_json())
