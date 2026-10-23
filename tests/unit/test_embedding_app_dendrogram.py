"""Unit tests for the dendrogram section of src/analysis/embedding_app.py."""

import dataclasses
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from dash import dcc, html
from scipy.cluster.hierarchy import fcluster

from src.analysis.clustering_tuning import compute_dendrogram_linkage
from src.analysis.dendrogram_splits import PALETTE, replay_splits, saved_labels_for
from src.analysis.embedding_app import (
    DENDROGRAM_MAP_MODALITIES,
    ProductionRun,
    build_app,
    build_run_split_tree,
    dendrogram_k_options,
    dendrogram_steps_content_for,
    index_entries_for,
    run_compatible_tunings,
    tuning_root_of,
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

BLOB_SIZES = (5, 6, 7, 8, 9, 10)  # all different, so no split is between two clusters of equal size
SUBJECTS = [f"sub-STUNIPD{i:04d}" for i in range(sum(BLOB_SIZES))]
DATASET = "UNIPD/WashU"
PRODUCTION_K = 4
LAST_K = 5
LINKAGE, METRIC = "ward", "euclidean"


def _embedding() -> np.ndarray:
    rng = np.random.default_rng(0)
    centres = np.array([[0, 0], [10, 0], [20, 0], [0, 30], [10, 30], [60, 60]], dtype=float)
    spread = np.array([0.3, 0.5, 0.8, 1.2, 1.6, 2.0])
    return np.vstack([rng.normal(c, s, size=(n, 2)) for c, s, n in zip(centres, spread, BLOB_SIZES)])


def _config_md(config: dict, params: dict | None = None) -> list[str]:
    lines = ["# run", "", "## Config", "```json", json.dumps(config), "```", ""]
    return lines + ([f"Params used: {json.dumps(params)}"] if params is not None else [])


@pytest.fixture(autouse=True)
def _participants_registry(tmp_path, monkeypatch):
    """A registry with the subjects of the cohort: the table under a step reads participants.csv."""
    from src.utils import participants

    root = tmp_path / "metadata"
    root.mkdir()
    rng = np.random.default_rng(1)
    pd.DataFrame({
        "subject_id": SUBJECTS, "original_id": SUBJECTS, "dataset": DATASET, "disease_id": "ST", "has_lesion": True,
        "has_sdc": True, "has_features": False, "age": rng.integers(40, 90, len(SUBJECTS)), "sex": rng.choice(["F", "M"], len(SUBJECTS)),
        "education": 12.0, "NIHSS": 4.0, "lesion_volume_voxels_2mm": rng.integers(100, 5000, len(SUBJECTS)),
    }).to_csv(root / "participants.csv", index=False)
    monkeypatch.setattr(participants, "METADATA_ROOT", root)


@pytest.fixture
def cohort(tmp_path: Path) -> dict:
    """A 2D embedding of 45 subjects, an agglomerative production run at k=4 on it and a tuning that swept k=2..5."""
    results = tmp_path / "results"
    embedding = _embedding()
    Z = compute_dendrogram_linkage(embedding, {"linkage": LINKAGE, "metric": METRIC})
    labels = {k: fcluster(Z, k, "maxclust") for k in range(2, LAST_K + 1)}
    input_path = str(results / "lesion" / "dim_reduction" / "production" / "umap" / "emb-1")

    production_dir = results / "lesion" / "clustering" / "production" / "agglomerative" / "umap" / "21-10_s1_k4_link_ward"
    config = {"clustering_method": "agglomerative", "input_path": input_path, "fine_tuning": False, "reduced_data": True,
              "reduction_method": "umap", "reduction_n_components": "2", "reduction_metric": "euclidean"}
    params = {"n_clusters": PRODUCTION_K, "linkage": LINKAGE, "metric": METRIC}
    metadata = pd.DataFrame({"subject_id": SUBJECTS, "dataset": DATASET, "cluster_label": labels[PRODUCTION_K]})
    save_matrix(production_dir, embedding, metadata, readme_lines=_config_md(config, params), overwrite=False)

    tuning_dir = results / "lesion" / "clustering" / "tuning" / "agglomerative" / "umap" / "21-10_s1_nc2"
    tuning_dir.mkdir(parents=True)
    tuning_config = {"clustering_method": "agglomerative", "input_path": input_path, "fine_tuning": True}
    (tuning_dir / "config.md").write_text("\n".join(_config_md(tuning_config)) + "\n")
    rows = [{"n_clusters": k, "linkage": LINKAGE, "metric": METRIC} for k in labels]
    pd.DataFrame(rows).to_csv(tuning_dir / "tuning_results.csv", index=False)
    np.savez(tuning_dir / "clusterings.npz", **{f"n_clusters={k},linkage={LINKAGE},metric={METRIC}": v for k, v in labels.items()})
    pd.DataFrame({"subject_id": SUBJECTS, "dataset": DATASET}).to_csv(tuning_dir / "metadata.csv", index=False)

    run = ProductionRun("lesion", "clustering", "agglomerative", production_dir.name, production_dir, reduction_method="umap")
    return {"run": run, "tuning_dir": tuning_dir, "results": results, "embedding": embedding, "labels": labels, "tmp_path": tmp_path}


def test_tuning_root_is_the_tuning_folder_of_the_same_modality_and_method(cohort):
    assert tuning_root_of(cohort["run"]) == cohort["results"] / "lesion" / "clustering" / "tuning" / "agglomerative"


def test_a_dim_reduction_run_has_no_tuning_root(cohort):
    run = ProductionRun("lesion", "dim_reduction", "umap", "r", cohort["results"] / "x")

    with pytest.raises(ValueError, match="not a clustering production run"):
        tuning_root_of(run)


def test_compatible_tunings_of_the_production_run(cohort):
    (match,) = run_compatible_tunings(cohort["run"])

    assert (match.run_dir, match.compatible) == (cohort["tuning_dir"], True)


def test_compatible_tunings_refuse_a_run_of_another_method(cohort):
    run = ProductionRun("lesion", "clustering", "kmeans", "r", cohort["run"].path, reduction_method="umap")

    with pytest.raises(ValueError, match="agglomerative"):
        run_compatible_tunings(run)


def test_split_tree_of_a_run_follows_the_tuning_up_to_its_last_k(cohort):
    tree = build_run_split_tree(cohort["run"], cohort["tuning_dir"])

    assert dendrogram_k_options(tree) == list(range(2, LAST_K + 1))


def test_split_tree_refuses_a_tuning_whose_labels_are_not_the_tree_of_the_run_matrix(cohort):
    npz = cohort["tuning_dir"] / "clusterings.npz"
    labels = dict(np.load(npz))
    key = f"n_clusters=3,linkage={LINKAGE},metric={METRIC}"
    labels[key] = np.roll(labels[key], 7)
    np.savez(npz, **labels)

    with pytest.raises(ValueError, match="does not reproduce"):
        build_run_split_tree(cohort["run"], cohort["tuning_dir"])


def _never_built(run, metadata_at_k, label, modality, name, width):
    raise ValueError("no map in this test")


def _registry():
    from src.utils.participants import load_participants_registry

    return load_participants_registry().set_index("subject_id")


def _context(cohort):
    tree = build_run_split_tree(cohort["run"], cohort["tuning_dir"])
    metadata = pd.read_csv(cohort["run"].path / "metadata.csv")
    return tree, metadata


def _steps(cohort, k=LAST_K, embedding=None, build_view=_never_built, modality="lesion"):
    tree, metadata = _context(cohort)
    embedding = cohort["embedding"] if embedding is None else embedding
    return dendrogram_steps_content_for(cohort["run"], metadata, tree, embedding, k, modality, build_view, _registry())


def _titles(content):
    return [screen.children[0].children for screen in content.children]


def _parts(screen):
    """(tree graph, embedding graph or message, rows of maps of the right column) of one screen of the walk. The table is
    `screen.children[2]`, below the drawing."""
    body = screen.children[1]
    left, right = body.children
    return left.children[0], left.children[1], right.children


def test_the_walk_goes_from_the_smallest_k_of_the_tuning_to_the_chosen_k_one_screen_each(cohort):
    titles = _titles(_steps(cohort, k=LAST_K))

    assert [title.split(":")[0] for title in titles] == [f"k={k}" for k in range(2, LAST_K + 1)]
    assert "The next one to split" in titles[0]
    assert all("split into" in title for title in titles[1:])


def test_a_shorter_walk_stops_at_the_chosen_k(cohort):
    assert [t.split(":")[0] for t in _titles(_steps(cohort, k=3))] == ["k=2", "k=3"]


def test_the_first_screen_has_only_the_cluster_that_splits_next_and_the_others_have_its_two_children_too(cohort):
    first, *others = _steps(cohort, k=LAST_K).children

    assert len(_parts(first)[2]) == 1  # the parent's map
    for screen in others:
        assert len(_parts(screen)[2]) == 2  # the parent's map, its two children's maps


def test_every_screen_has_the_tree_the_embedding_and_the_table_of_the_split(cohort):
    for screen in _steps(cohort, k=3).children:
        tree_graph, embedding_graph, rows = _parts(screen)
        assert isinstance(tree_graph, dcc.Graph) and isinstance(embedding_graph, dcc.Graph)
        assert screen.children[2].className == "stats-table-wrap dendrogram-step-table"


def test_the_table_of_a_split_describes_the_cluster_that_split_and_the_two_it_gave(cohort):
    tree, _ = _context(cohort)
    screen = _steps(cohort, k=3).children[1]

    table = screen.children[2].children
    names = [row.children[0].children.children[1] for row in table.children[1].children]
    sizes = [row.children[1].children[0].children for row in table.children[1].children]
    assert [name.split()[0] for name in names] == ["Was", "New", "New"]
    assert sizes[0] == f"{sum(int(s_.replace('.', '')) for s_ in sizes[1:])}"  # the parent is the union of the two


def test_a_tuning_that_starts_above_k2_starts_the_walk_at_its_smallest_k(cohort):
    npz = cohort["tuning_dir"] / "clusterings.npz"
    kept = {key: value for key, value in np.load(npz).items() if "n_clusters=2," not in key}
    np.savez(npz, **kept)
    results = pd.read_csv(cohort["tuning_dir"] / "tuning_results.csv")
    results[results["n_clusters"] != 2].to_csv(cohort["tuning_dir"] / "tuning_results.csv", index=False)

    tree, _ = _context(cohort)
    content = _steps(cohort, k=LAST_K)

    assert dendrogram_k_options(tree) == [3, 4, 5]
    assert [t.split(":")[0] for t in _titles(content)] == ["k=3", "k=4", "k=5"]


def test_a_k_the_tuning_skipped_is_walked_through_but_not_offered(cohort):
    npz = cohort["tuning_dir"] / "clusterings.npz"
    np.savez(npz, **{key: value for key, value in np.load(npz).items() if "n_clusters=4," not in key})
    results = pd.read_csv(cohort["tuning_dir"] / "tuning_results.csv")
    results[results["n_clusters"] != 4].to_csv(cohort["tuning_dir"] / "tuning_results.csv", index=False)

    tree, _ = _context(cohort)
    content = _steps(cohort, k=LAST_K)

    assert dendrogram_k_options(tree) == [2, 3, 5]
    assert [t.split(":")[0] for t in _titles(content)] == ["k=2", "k=3", "k=4", "k=5"]


def test_the_embedding_of_a_three_component_run_is_a_status_message_not_a_slice(cohort):
    three = np.hstack([cohort["embedding"], np.zeros((len(SUBJECTS), 1))])

    for screen in _steps(cohort, k=3, embedding=three).children:
        _tree_graph, embedding_part, _rows = _parts(screen)
        assert isinstance(embedding_part, html.P) and "2 components" in embedding_part.children


def test_a_k_outside_the_tuning_is_a_status_message(cohort):
    content = _steps(cohort, k=LAST_K + 1)

    assert isinstance(content, html.P) and "is not among those" in content.children


def test_maps_are_looked_up_by_the_tuning_labels_of_their_own_k_not_by_the_run_labels(cohort):
    # The production run is at k=4, so its own cluster_label is the cut at 4. At step k the cluster that splits is
    # looked up in the cut at k-1 and the two it gives in the cut at k: no column of the run's metadata holds either.
    seen = []

    def build_view(run, metadata_at_k, label, modality, name, width):
        seen.append((metadata_at_k["cluster_label"].to_numpy().copy(), label, modality, name, width))
        raise ValueError("stop here")

    _steps(cohort, k=LAST_K, build_view=build_view)

    parent, child_a, child_b = seen[-3:]  # the last screen: the parent, then its two children
    assert np.array_equal(parent[0], cohort["labels"][LAST_K - 1])
    assert np.array_equal(child_a[0], cohort["labels"][LAST_K]) and np.array_equal(child_b[0], cohort["labels"][LAST_K])
    assert parent[1] in set(cohort["labels"][LAST_K - 1]) and {child_a[1], child_b[1]} <= set(cohort["labels"][LAST_K])
    assert not np.array_equal(cohort["labels"][LAST_K], pd.read_csv(cohort["run"].path / "metadata.csv")["cluster_label"].to_numpy())


def test_the_first_screen_maps_the_cluster_that_splits_at_the_next_k(cohort):
    seen = []

    def build_view(run, metadata_at_k, label, modality, name, width):
        seen.append((int((metadata_at_k["cluster_label"] == label).sum()), name, width))
        raise ValueError("stop here")

    tree, _ = _context(cohort)
    _steps(cohort, k=2, build_view=build_view)

    expected = replay_splits(tree.Z, tree.labels_by_k, tree.leaf_of_subject, len(tree.members), 3)[-1][2]["parent"]
    assert len(seen) == 1 and seen[0][:2] == (expected["n"], expected["name"])


def test_the_parent_is_drawn_bigger_than_its_children(cohort):
    seen = []

    def build_view(run, metadata_at_k, label, modality, name, width):
        seen.append(width)
        raise ValueError("stop here")

    _steps(cohort, k=3, build_view=build_view)

    assert seen[-3] > seen[-2] == seen[-1]


def test_a_cluster_is_always_called_by_the_same_name_so_that_the_cache_keyed_by_it_never_confuses_two(cohort):
    sizes_by_name = {}

    def build_view(run, metadata_at_k, label, modality, name, width):
        sizes_by_name.setdefault(name, set()).add(int((metadata_at_k["cluster_label"] == label).sum()))
        raise ValueError("stop here")

    _steps(cohort, k=LAST_K, build_view=build_view)

    assert all(len(sizes) == 1 for sizes in sizes_by_name.values())


def _real_view_builder(cohort):
    from src.analysis.embedding_app import _build_cluster_disconnection_view, _build_cluster_overlap_view

    tmp_path = cohort["tmp_path"]
    for index, subject in enumerate(SUBJECTS):
        _make_lesion_subject(tmp_path, DATASET, subject, [(index % 10, 2, 2)])
        _make_disconnectome_subject(tmp_path, DATASET, subject, {(index % 10, 3, 3): 0.9})

    def build_view(run, metadata_at_k, label, modality, name, width):
        if modality == "lesion":
            return _build_cluster_overlap_view(run, metadata_at_k, label, _lesion_cfg(tmp_path), width_view=width)
        return _build_cluster_disconnection_view(run, metadata_at_k, label, _sdc_cfg(tmp_path), width_view=width)

    return build_view


def test_every_map_of_a_screen_is_a_titled_viewer_with_the_colour_square_of_its_cluster(cohort):
    build_view = _real_view_builder(cohort)

    for modality in DENDROGRAM_MAP_MODALITIES:
        content = _steps(cohort, k=3, build_view=build_view, modality=modality)

        for screen in content.children[1:]:
            tiles = [tile for row in _parts(screen)[2] for tile in (row.children if isinstance(row.children, list) else [row.children])]
            titles = [tile.children[0].children for tile in tiles]
            assert [title[1].split(":")[0] for title in titles] == ["Was", "New", "New"]
            assert all(title[0].style["background"].startswith("#") for title in titles)
            assert all(isinstance(tile.children[1], html.Iframe) for tile in tiles)


def test_a_cluster_without_resolvable_subjects_is_a_status_message_in_place_of_its_map(cohort):
    from src.analysis.embedding_app import _build_cluster_overlap_view

    # no lesion file was written in this test
    content = _steps(
        cohort, k=3,
        build_view=lambda run, md, label, modality, name, width: _build_cluster_overlap_view(run, md, label, _lesion_cfg(cohort["tmp_path"])),
    )

    for screen in content.children:
        rows = _parts(screen)[2]
        assert all(isinstance(row.children, html.P) or all(isinstance(c, html.P) for c in row.children) for row in rows)


def test_unknown_map_modality_raises(cohort):
    with pytest.raises(ValueError, match="unknown map modality"):
        _steps(cohort, k=3, modality="pet")


def test_the_steps_are_a_wide_block_that_leaves_the_page_column(cohort):
    assert "wide-block" in _steps(cohort, k=3).className


def test_index_lists_the_dendrogram_section_only_for_an_agglomerative_run(cohort):
    anchors = lambda run: [anchor for anchor, _label in index_entries_for(run)]  # noqa: E731
    kmeans = ProductionRun("lesion", "clustering", "kmeans", "r", cohort["run"].path, reduction_method="umap")

    assert "dendrogram-panel" in anchors(cohort["run"])
    assert "dendrogram-panel" not in anchors(kmeans)
    assert "dendrogram-panel" not in anchors(None)


# --- callbacks, through the app's own HTTP endpoint ---------------------------------------------------------------

# Dash needs every output of a callback in the request, in the order the callback declares them.
PANEL_OUTPUTS = [
    ("dendrogram-panel", "style"), ("dendrogram-tuning-picker", "options"), ("dendrogram-tuning-picker", "value"),
    ("dendrogram-tuning-note", "children"), ("dendrogram-map-picker", "value"),
]


def _post(app, outputs: list[tuple[str, str]], inputs: list[tuple[str, str, object]]):
    """One callback request, shaped as Dash's own front end sends it: a single output is `id.prop`, several are
    `..id.prop...id.prop..`."""
    specs = [{"id": component, "property": prop} for component, prop in outputs]
    names = [f"{component}.{prop}" for component, prop in outputs]
    body = {
        "output": names[0] if len(names) == 1 else ".." + "...".join(names) + "..",
        "outputs": specs[0] if len(specs) == 1 else specs,
        "inputs": [{"id": component, "property": prop, "value": value} for component, prop, value in inputs],
        "changedPropIds": [f"{inputs[0][0]}.{inputs[0][1]}"],
    }
    app.server.config["TESTING"] = True
    return app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")


@pytest.fixture
def app(cohort):
    tmp_path = cohort["tmp_path"]
    other = _make_run_dir(cohort["results"], run_name="other")
    other_run = ProductionRun("lesion", "dim_reduction", "umap", "other", other)
    return build_app(
        [cohort["run"], other_run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path, methods=("kmeans", "agglomerative")), tmp_path / "cache"
    )


def test_panel_callback_shows_the_panel_and_offers_the_compatible_tuning(cohort, app):
    response = _post(app, PANEL_OUTPUTS, [("run-picker", "value", cohort["run"].key)])

    assert response.status_code == 200
    answer = response.get_json()["response"]
    assert answer["dendrogram-panel"]["style"] == {}
    assert answer["dendrogram-tuning-picker"]["options"] == [{"label": cohort["tuning_dir"].name, "value": str(cohort["tuning_dir"])}]
    assert answer["dendrogram-tuning-picker"]["value"] == str(cohort["tuning_dir"])
    assert answer["dendrogram-map-picker"]["value"] == "lesion"  # lesion whatever the run's own modality


def test_panel_callback_starts_on_the_lesion_map_also_for_a_disconnection_run(cohort):
    sdc_run = dataclasses.replace(cohort["run"], modality="sdc")
    tmp_path = cohort["tmp_path"]
    app = build_app(
        [sdc_run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path, methods=("kmeans", "agglomerative")), tmp_path / "cache"
    )

    answer = _post(app, PANEL_OUTPUTS, [("run-picker", "value", sdc_run.key)]).get_json()["response"]

    assert answer["dendrogram-map-picker"]["value"] == "lesion"


def test_panel_callback_hides_the_panel_for_a_run_that_is_not_agglomerative(cohort, app):
    other_key = "lesion/dim_reduction/umap/other"

    response = _post(app, PANEL_OUTPUTS, [("run-picker", "value", other_key)])

    assert response.get_json()["response"]["dendrogram-panel"]["style"] == {"display": "none"}


def test_k_callback_offers_the_ks_of_the_tuning_and_starts_at_the_production_k(cohort, app):
    outputs = [("dendrogram-k-picker", "options"), ("dendrogram-k-picker", "value")]

    response = _post(app, outputs, [("run-picker", "value", cohort["run"].key), ("dendrogram-tuning-picker", "value", str(cohort["tuning_dir"]))])

    answer = response.get_json()["response"]
    assert [option["value"] for option in answer["dendrogram-k-picker"]["options"]] == list(range(2, LAST_K + 1))
    assert answer["dendrogram-k-picker"]["value"] == PRODUCTION_K


def test_a_tuning_value_left_over_from_another_run_updates_nothing(cohort, app):
    response = _post(
        app, [("dendrogram-k-picker", "options"), ("dendrogram-k-picker", "value")],
        [("run-picker", "value", cohort["run"].key), ("dendrogram-tuning-picker", "value", "results/lesion/clustering/tuning/agglomerative/umap/not-mine")],
    )

    assert response.status_code == 204


STEPS_OUTPUT = [("dendrogram-steps-content", "children")]
def _steps_inputs(cohort, k):
    return [("run-picker", "value", cohort["run"].key), ("dendrogram-tuning-picker", "value", str(cohort["tuning_dir"])),
            ("dendrogram-k-picker", "value", k), ("dendrogram-map-picker", "value", "lesion")]


def test_steps_callback_walks_the_tree_down_to_k(cohort, app):
    response = _post(app, STEPS_OUTPUT, _steps_inputs(cohort, 3))

    assert response.status_code == 200
    body = json.dumps(response.get_json()["response"])
    assert "k=2:" in body and "k=3:" in body and "k=4:" not in body


def test_steps_callback_with_a_k_outside_the_tuning_updates_nothing(cohort, app):
    assert _post(app, STEPS_OUTPUT, _steps_inputs(cohort, 30)).status_code == 204


def test_saved_labels_helper_agrees_with_the_tuning_files(cohort):
    # Guard on the fixture itself: the tuning really holds the labels the tests above compare against.
    from src.analysis.clustering_tuning_analysis import load_clustering_tuning_run

    saved = saved_labels_for(load_clustering_tuning_run(cohort["tuning_dir"]), LINKAGE, METRIC)

    assert all(np.array_equal(saved[k], cohort["labels"][k]) for k in saved)


def _parent_of(component, target_id):
    """The component whose `children` directly hold the one with id `target_id`, or None."""
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        if any(getattr(child, "id", None) == target_id for child in children):
            return component
        for child in children:
            found = _parent_of(child, target_id)
            if found is not None:
                return found
    elif children is not None and not isinstance(children, str):
        return _parent_of(children, target_id)
    return None


def test_the_dendrogram_explorer_is_the_last_section_of_the_page_and_of_the_index(cohort, app):
    parent = _parent_of(app.layout, "dendrogram-panel")

    assert parent.children[-1].id == "dendrogram-panel"
    assert parent.children[-1].className == "section-divider"  # a section of its own, like "Clustering Explorer"
    assert [anchor for anchor, _label in index_entries_for(cohort["run"])][-1] == "dendrogram-panel"


def test_the_walk_starts_right_after_the_pickers_with_no_overview_of_every_cluster(cohort, app):
    """The "all clusters" overview that used to open the section repeated the "all" option of the Clustering Explorer."""
    panel = next(child for child in _parent_of(app.layout, "dendrogram-panel").children if child.id == "dendrogram-panel")
    texts = [child.children for child in panel.children if isinstance(getattr(child, "children", None), str)]

    assert "dendrogram-overview-content" not in str(panel.to_plotly_json())
    assert "Agglomerative decomposed" in texts
