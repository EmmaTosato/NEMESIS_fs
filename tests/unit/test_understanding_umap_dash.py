"""Unit tests for src/analysis/understanding_umap_dash.py - _slider_reset,
_umap_combo_figure/_tsne_combo_figure error handling, and a smoke test that
build_app produces a working Dash app over a tiny real-shaped (synthetic,
small) tuning-output fixture, same fixture-building convention as
test_understanding_umap_report.py."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from dash import Dash

from src.analysis.understanding_umap_dash import _slider_reset, _tsne_combo_figure, _umap_combo_figure, build_app
from src.analysis.understanding_umap_report import load_tuning_data

_SUBJECT_IDS = ["sub-1", "sub-2", "sub-3", "sub-4"]


def _metadata() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "subject_id": _SUBJECT_IDS,
            "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR", "UKLFR/stroke_UKLFR"],
            "lesion_volume_voxels": [1200.0, 3400.0, 800.0, 5600.0],
            "lesion_side": ["left", "right", "left", "unknown"],
            "nihss": [4.0, 12.0, np.nan, 7.0],
        }
    )


def _write_umap_tuning_dir(root: Path, metric: str = "dice") -> Path:
    root.mkdir(parents=True)
    _metadata().to_csv(root / "metadata.csv", index=False)
    (root / "config.md").write_text('# fake run\n\n```json\n{"base_params": {"n_components": 2}}\n```\n')

    arrays = {}
    for n_components in (2, 3):
        leaf = root / f"metric={metric}" / f"n_components={n_components}"
        leaf.mkdir(parents=True)
        rows = []
        for n_neighbors in (5, 15):
            for min_dist in (0.0, 0.5):
                rows.append({"metric": metric, "n_components": n_components, "n_neighbors": n_neighbors, "min_dist": min_dist, "trustworthiness": 0.9})
                key = f"metric={metric},n_components={n_components},n_neighbors={n_neighbors},min_dist={min_dist}"
                arrays[key] = np.random.default_rng(0).normal(size=(len(_SUBJECT_IDS), n_components))
        pd.DataFrame(rows).to_csv(leaf / "tuning_results.csv", index=False)
    np.savez(root / "embeddings.npz", **arrays)
    return root


def _write_tsne_tuning_dir(root: Path, metric: str = "dice") -> Path:
    root.mkdir(parents=True)
    _metadata().to_csv(root / "metadata.csv", index=False)

    leaf = root / f"metric={metric}"
    leaf.mkdir(parents=True)
    rows, arrays = [], {}
    for perplexity in (5, 15):
        rows.append({"metric": metric, "perplexity": perplexity, "trustworthiness": 0.9})
        key = f"metric={metric},perplexity={perplexity}"
        arrays[key] = np.random.default_rng(1).normal(size=(len(_SUBJECT_IDS), 2))
    pd.DataFrame(rows).to_csv(leaf / "tuning_results.csv", index=False)
    np.savez(root / "embeddings.npz", **arrays)
    return root


def test_slider_reset_indexes_from_zero():
    lo, hi, marks, value = _slider_reset([5, 15, 30])

    assert (lo, hi, value) == (0, 2, 0)
    assert marks == {0: "5", 1: "15", 2: "30"}


def test_umap_combo_figure_raises_for_missing_combo():
    results = pd.DataFrame({"metric": ["dice"], "n_neighbors": [5], "min_dist": [0.0], "trustworthiness": [0.9]})
    embeddings = {"metric=dice,n_neighbors=5,min_dist=0.0": np.zeros((4, 2))}

    with pytest.raises(ValueError, match="no UMAP combo"):
        _umap_combo_figure(results, embeddings, _metadata(), "dice", n_neighbors=99, min_dist=0.0, is_3d=False)


def test_tsne_combo_figure_raises_for_missing_combo():
    results = pd.DataFrame({"metric": ["dice"], "perplexity": [5], "trustworthiness": [0.9]})
    embeddings = {"metric=dice,perplexity=5": np.zeros((4, 2))}

    with pytest.raises(ValueError, match="no t-SNE combo"):
        _tsne_combo_figure(results, embeddings, _metadata(), perplexity=99)


def test_build_app_smoke(tmp_path):
    umap_dir = _write_umap_tuning_dir(tmp_path / "umap")
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne")
    data = load_tuning_data(umap_dir, tsne_dir)

    app = build_app(data)

    assert isinstance(app, Dash)
    layout_ids = {c.id for c in app.layout.children if hasattr(c, "id")}
    # spot-check a few ids from each of the 5 figures are actually present -
    # not exhaustive, just enough to catch a layout that fails to build any
    # figure's components at all.
    all_ids = _collect_ids(app.layout)
    for expected in ["fig1-grid", "fig2-plot", "fig3-2d-plot", "fig3-3d-plot", "fig4-grid", "fig5-umap-plot", "fig5-tsne-plot"]:
        assert expected in all_ids, f"missing component id {expected!r}"


def _collect_ids(component) -> set:
    ids = set()
    comp_id = getattr(component, "id", None)
    if comp_id is not None:
        ids.add(comp_id)
    children = getattr(component, "children", None)
    if children is None:
        return ids
    if not isinstance(children, list):
        children = [children]
    for child in children:
        if hasattr(child, "id") or hasattr(child, "children"):
            ids |= _collect_ids(child)
    return ids
