"""Unit tests for the "all" option of the Clustering Explorer's cluster picker (src/analysis/embedding_app.py)."""

import json
import re

import numpy as np
import pandas as pd
import pytest
from dash import dcc, html

from src.analysis.embedding_app import (
    ALL_CLUSTERS,
    CSS,
    ProductionRun,
    _build_cluster_disconnection_view,
    _build_cluster_overlap_view,
    all_clusters_content_for,
    build_app,
    run_metadata,
)
from tests.unit.test_embedding_app import (
    _clustering_params_file,
    _lesion_cfg,
    _make_disconnectome_subject,
    _make_lesion_subject,
    _make_run_dir,
    _sdc_cfg,
)

SUBJECTS = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
LABELS = [0, 0, 1, 2]


def _run(tmp_path, labels=LABELS, modality="lesion", n_dims=2):
    results = tmp_path / "results"
    run_dir = _make_run_dir(
        results, modality=modality, pipeline="clustering", run_name="run-a", n_dims=n_dims, params={"n_clusters": 3},
        extra_metadata={"subject_id": SUBJECTS, "cluster_label": labels},
    )
    return ProductionRun(modality, "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")


def _embedding():
    return np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]])


def _fake_view(run, metadata, label, width):
    raise ValueError("no map in this test")


def _content(tmp_path, labels=LABELS, embedding="given", message=None, build_view=_fake_view, modality="lesion", map_mode="percent"):
    run = _run(tmp_path, labels)
    embedding = _embedding() if isinstance(embedding, str) else embedding
    return all_clusters_content_for(run, run_metadata(run), embedding, message, modality, map_mode, build_view)


def _grid(content):
    return content.children[2].children[1]


def _left(content):
    """What sits in the embedding column: the figure, or the message that stands in for it."""
    return content.children[2].children[0].children


def test_every_cluster_has_a_map_two_to_a_row_and_one_embedding_with_a_legend_without_sizes(tmp_path):
    seen = []

    def build_view(run, metadata, label, width):
        seen.append((label, width))
        raise ValueError("no map")

    content = _content(tmp_path, build_view=build_view)

    left, grid = _left(content), _grid(content)
    assert [label for label, _ in seen] == [0, 1, 2]
    assert grid.style["gridTemplateColumns"] == "repeat(2, auto)"
    assert isinstance(left, dcc.Graph)
    assert [trace.name for trace in left.figure.data] == ["Cluster 0", "Cluster 1", "Cluster 2"]


def test_the_map_width_is_the_overview_one_not_the_panel_one(tmp_path):
    widths = []

    def build_view(run, metadata, label, width):
        widths.append(width)
        raise ValueError("no map")

    _content(tmp_path, build_view=build_view)

    assert set(widths) == {580}


def test_a_single_cluster_gets_one_bigger_map(tmp_path):
    widths = []

    def build_view(run, metadata, label, width):
        widths.append(width)
        raise ValueError("no map")

    content = _content(tmp_path, labels=[0, 0, 0, 0], build_view=build_view)

    assert widths == [760] and _grid(content).style["gridTemplateColumns"] == "repeat(1, auto)"


def test_the_noise_of_hdbscan_is_drawn_as_rumore_in_its_gray(tmp_path):
    content = _content(tmp_path, labels=[-1, 0, 0, 1])

    left = _left(content)
    assert [trace.name for trace in left.figure.data] == ["Noise", "Cluster 0", "Cluster 1"]
    assert left.figure.data[0].marker.color == "#9e9e9e" or left.figure.data[0].marker.color != left.figure.data[1].marker.color


def test_the_colours_are_those_of_the_embedding_scatter(tmp_path):
    from src.analysis.plotting import _palette_for_labels

    content = _content(tmp_path)

    left = _left(content)
    palette = _palette_for_labels([0, 1, 2])
    assert [trace.marker.color for trace in left.figure.data] == [palette[0], palette[1], palette[2]]


def test_a_cluster_that_cannot_be_mapped_shows_its_own_message_and_the_others_are_drawn(tmp_path):
    tmp = tmp_path
    for index, subject in enumerate(SUBJECTS[:2]):
        _make_lesion_subject(tmp / "data", "UNIPD/WashU", subject, [(index, 1, 1)])

    def build_view(run, metadata, label, width):
        return _build_cluster_overlap_view(run, metadata, label, _lesion_cfg(tmp / "data"), width_view=width)

    grid = _grid(_content(tmp, build_view=build_view))

    kinds = [type(child).__name__ for child in grid.children]
    assert kinds == ["Div", "P", "P"]  # cluster 0 has files, 1 and 2 have none
    assert grid.children[0].className == "map-tile"
    assert "Cluster 1" in grid.children[1].children


def test_a_map_tile_has_the_clusters_colour_square_the_name_and_the_size(tmp_path):
    from src.analysis.plotting import _palette_for_labels

    for index, subject in enumerate(SUBJECTS):
        dataset = "UNIPD/WashU" if "UNIPD" in subject else "UKLFR/stroke_UKLFR"
        _make_lesion_subject(tmp_path / "data", dataset, subject, [(index, 1, 1)])

    def build_view(run, metadata, label, width):
        return _build_cluster_overlap_view(run, metadata, label, _lesion_cfg(tmp_path / "data"), width_view=width)

    tile = _grid(_content(tmp_path, build_view=build_view)).children[0]

    title = tile.children[0]
    assert title.children[0].style["background"] == _palette_for_labels([0, 1, 2])[0]
    assert title.children[1] == "Cluster 0 (n=2)"
    assert isinstance(tile.children[1], html.Iframe)


def test_the_disconnection_maps_use_the_disconnection_caption_of_the_chosen_mode(tmp_path):
    percent = _content(tmp_path / "percent", modality="sdc", map_mode="percent").children[1]
    mean = _content(tmp_path / "mean", modality="sdc", map_mode="mean").children[1]

    assert "disconnected" in percent.children[0] and "mean disconnection probability" in mean.children[0]


def test_the_disconnection_tiles_are_built_with_the_disconnection_builder(tmp_path):
    for index, subject in enumerate(SUBJECTS):
        dataset = "UNIPD/WashU" if "UNIPD" in subject else "UKLFR/stroke_UKLFR"
        _make_disconnectome_subject(tmp_path / "data", dataset, subject, {(index, 3, 3): 0.9})

    def build_view(run, metadata, label, width):
        return _build_cluster_disconnection_view(run, metadata, label, _sdc_cfg(tmp_path / "data"), width_view=width)

    grid = _grid(_content(tmp_path, build_view=build_view, modality="sdc"))

    assert all(child.className == "map-tile" for child in grid.children)


def test_without_an_embedding_the_maps_are_drawn_and_the_message_says_why(tmp_path):
    content = _content(tmp_path, embedding=None, message="this run has no embedding to draw")

    left, grid = _left(content), _grid(content)
    assert isinstance(left, html.P) and left.children == "this run has no embedding to draw"
    assert len(grid.children) == 3


def test_a_three_component_embedding_is_a_message_not_a_slice(tmp_path):
    content = _content(tmp_path, embedding=np.zeros((4, 3)))

    assert "2 components" in _left(content).children


def test_the_overview_is_a_wide_block_marked_so_that_the_save_buttons_are_hidden(tmp_path):
    classes = _content(tmp_path).className.split()

    assert "wide-block" in classes and "all-clusters-overview" in classes


def test_an_unknown_map_mode_raises(tmp_path):
    with pytest.raises(ValueError, match="unknown disconnection map mode"):
        _content(tmp_path, modality="sdc", map_mode="median")


# --- callbacks, through the app's own HTTP endpoint ---------------------------------------------------------------


def _app(tmp_path, run):
    return build_app([run], _lesion_cfg(tmp_path / "data"), _sdc_cfg(tmp_path / "data"), _clustering_params_file(tmp_path), tmp_path / "cache")


def _post(app, outputs, inputs, state=()):
    specs = [{"id": component, "property": prop} for component, prop in outputs]
    names = [f"{component}.{prop}" for component, prop in outputs]
    body = {
        "output": names[0] if len(names) == 1 else ".." + "...".join(names) + "..",
        "outputs": specs[0] if len(specs) == 1 else specs,
        "inputs": [{"id": c, "property": p, "value": v} for c, p, v in inputs],
        "state": [{"id": c, "property": p, "value": v} for c, p, v in state],
        "changedPropIds": [f"{inputs[0][0]}.{inputs[0][1]}"],
    }
    app.server.config["TESTING"] = True
    return app.server.test_client().post("/_dash-update-component", data=json.dumps(body), content_type="application/json")


def test_the_cluster_picker_offers_all_on_top_and_still_starts_at_the_first_cluster(tmp_path):
    run = _run(tmp_path)
    outputs = [("cluster-picker", "options"), ("cluster-picker", "value"), ("clustering-section", "style"),
               ("cluster-map-panel", "style"), ("representative-subject-panel", "style"), ("cluster-description-panel", "style"),
               ("cluster-composition-panel", "style"), ("cluster-quality-panel", "style")]

    answer = _post(_app(tmp_path, run), outputs, [("run-picker", "value", run.key)]).get_json()["response"]

    options = answer["cluster-picker"]["options"]
    assert options[0] == {"label": "all", "value": ALL_CLUSTERS}
    assert [option["value"] for option in options[1:]] == [0, 1, 2]
    assert answer["cluster-picker"]["value"] == 0


def test_all_in_the_lesion_map_panel_draws_every_cluster(tmp_path):
    run = _run(tmp_path)

    response = _post(
        _app(tmp_path, run), [("cluster-map-content", "children")],
        [("run-picker", "value", run.key), ("cluster-picker", "value", ALL_CLUSTERS)],
    )

    assert response.status_code == 200
    body = json.dumps(response.get_json()["response"])
    assert "all-clusters-overview" in body and "Cluster 0" in body and "Cluster 2" in body


def test_all_in_the_disconnection_panel_draws_every_cluster_of_an_sdc_run(tmp_path):
    run = _run(tmp_path, modality="sdc")

    response = _post(
        _app(tmp_path, run), [("disconnection-map-content", "children")],
        [("run-picker", "value", run.key), ("cluster-picker", "value", ALL_CLUSTERS), ("selected-disconnection-mode", "data", "percent")],
    )

    assert response.status_code == 200
    assert "all-clusters-overview" in json.dumps(response.get_json()["response"])


def test_all_in_the_per_cluster_panels_asks_to_choose_a_cluster(tmp_path):
    run = _run(tmp_path)
    app = _app(tmp_path, run)

    for output in ("representative-subject-content", "cluster-description-content"):
        response = _post(app, [(output, "children")], [("run-picker", "value", run.key), ("cluster-picker", "value", ALL_CLUSTERS)])

        assert response.status_code == 200
        assert "Choose a cluster" in json.dumps(response.get_json()["response"])


def test_a_single_cluster_still_gets_its_own_panel_not_the_overview(tmp_path):
    run = _run(tmp_path)

    response = _post(
        _app(tmp_path, run), [("cluster-map-content", "children")],
        [("run-picker", "value", run.key), ("cluster-picker", "value", 0)],
    )

    assert "all-clusters-overview" not in json.dumps(response.get_json()["response"])


@pytest.mark.parametrize(
    ("button", "download"),
    [("cluster-save-btn", "cluster-download"), ("cluster-png-btn", "cluster-png-download"),
     ("representative-save-btn", "representative-download"), ("representative-png-btn", "representative-png-download"),
     ("disconnection-save-btn", "disconnection-download"), ("disconnection-png-btn", "disconnection-png-download")],
)
def test_the_save_buttons_do_nothing_for_all(tmp_path, button, download):
    run = _run(tmp_path, modality="sdc")

    response = _post(
        _app(tmp_path, run), [(download, "data")], [(button, "n_clicks", 1)],
        state=[("run-picker", "value", run.key), ("cluster-picker", "value", ALL_CLUSTERS)],
    )

    assert response.status_code == 204


def test_the_stylesheet_hides_the_save_buttons_of_a_panel_that_shows_all():
    from src.analysis.embedding_app import _INDEX_STRING

    assert ".anatomy-panel:has(.all-clusters-overview) .save-btn-row" in _INDEX_STRING


def _css_rule(selector: str) -> str:
    match = re.search(re.escape(selector) + r" \{([^}]*)\}", CSS)
    assert match, f"no CSS rule for {selector}"
    return match.group(1)


def test_the_embedding_column_is_sticky_so_that_it_follows_the_reader_down_the_maps(tmp_path):
    content = _content(tmp_path)

    assert content.children[2].children[0].className == "overview-embedding"
    assert "position: sticky" in _css_rule(".overview-embedding")


def test_the_wide_block_is_not_a_scroll_container_or_the_sticky_embedding_would_stick_to_it(tmp_path):
    """overflow auto/hidden/scroll on an ancestor makes it the scrollport that `position: sticky` looks at: the block
    never scrolls, so the embedding would never stick to the window. `clip` cuts without making a scrollport."""
    rule = _css_rule(".wide-block")

    assert not re.search(r"overflow(-[xy])?:\s*(auto|hidden|scroll)", rule)
