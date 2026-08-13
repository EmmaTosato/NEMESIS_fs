"""Unit tests for src/analysis/understanding_umap_report.py - _combo_key,
_read_base_n_components, _color_values_for_mode, and an E2E generate_report
run over a tiny real-shaped (synthetic, small) tuning-output fixture."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.understanding_umap_report import (
    _color_values_for_mode,
    _combo_key,
    _read_base_n_components,
    generate_report,
)

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
    """A tiny nested_params=["metric", "n_components"] UMAP tuning dir, same
    shape as src.pipeline.dim_reduction's real output - one metric, 2
    n_components leaves (2 and 3), 2 n_neighbors x 2 min_dist combos each.
    """
    root.mkdir(parents=True)
    metadata = _metadata()
    metadata.to_csv(root / "metadata.csv", index=False)
    (root / "config.md").write_text(
        "# fake tuning run\n\n```json\n"
        '{"base_params": {"n_components": 2}}\n'
        "```\n"
    )

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
    """A tiny nested_params=["metric"] t-SNE tuning dir (always 2D), same
    subject cohort/order as _write_umap_tuning_dir.
    """
    root.mkdir(parents=True)
    metadata = _metadata()
    metadata.to_csv(root / "metadata.csv", index=False)

    leaf = root / f"metric={metric}"
    leaf.mkdir(parents=True)
    rows = []
    arrays = {}
    for perplexity in (5, 15):
        rows.append({"metric": metric, "perplexity": perplexity, "trustworthiness": 0.9})
        key = f"metric={metric},perplexity={perplexity}"
        arrays[key] = np.random.default_rng(1).normal(size=(len(_SUBJECT_IDS), 2))
    pd.DataFrame(rows).to_csv(leaf / "tuning_results.csv", index=False)
    np.savez(root / "embeddings.npz", **arrays)
    return root


def test_combo_key_matches_key_value_pairs_in_order():
    row = pd.Series({"metric": "dice", "n_neighbors": 15, "min_dist": 0.1, "trustworthiness": 0.9})

    assert _combo_key(row, ["metric", "n_neighbors", "min_dist"]) == "metric=dice,n_neighbors=15,min_dist=0.1"


def test_read_base_n_components(tmp_path):
    (tmp_path / "config.md").write_text('# run\n\n```json\n{"base_params": {"n_components": 3}}\n```\n')

    assert _read_base_n_components(tmp_path) == 3


def test_read_base_n_components_raises_without_fenced_json_block(tmp_path):
    (tmp_path / "config.md").write_text("# run\n\nno json here\n")

    with pytest.raises(ValueError, match="fenced"):
        _read_base_n_components(tmp_path)


def test_color_values_for_mode_none_is_neutral_single_color():
    colors = _color_values_for_mode(_metadata(), "none")

    assert colors == {"color": "#1f77b4", "colorscale": None, "opacity": 0.5}


def test_color_values_for_mode_categorical_maps_missing_label_to_neutral_gray():
    colors = _color_values_for_mode(_metadata(), "side")

    # "unknown" (subject 4) must get the fixed neutral gray, never a palette color
    assert colors["color"][3] == "#9e9d98"
    assert colors["colorscale"] is None
    assert colors["opacity"] == 1.0


def test_color_values_for_mode_continuous_log_scale_rejects_non_positive_values():
    metadata = _metadata()
    metadata.loc[0, "lesion_volume_voxels"] = 0.0

    with pytest.raises(ValueError, match="log-scaled"):
        _color_values_for_mode(metadata, "volume")


def test_color_values_for_mode_continuous_not_log_scale_keeps_raw_values():
    colors = _color_values_for_mode(_metadata(), "nihss")

    assert colors["colorscale"] == "Viridis"
    assert colors["color"][0] == 4.0


def test_generate_report_writes_one_html_per_metric(tmp_path):
    umap_dir = _write_umap_tuning_dir(tmp_path / "umap")
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne")
    output_dir = tmp_path / "out"

    output_paths = generate_report(umap_dir, tsne_dir, output_dir)

    assert output_paths == [output_dir / "understanding_umap_dice.html"]
    html = output_paths[0].read_text()
    assert "Figure 1:" in html and "Figure 5:" in html
    assert "Figure 6:" not in html
    assert f"subjects:</span> {len(_SUBJECT_IDS)}" in html


def test_generate_report_raises_on_cohort_mismatch(tmp_path):
    umap_dir = _write_umap_tuning_dir(tmp_path / "umap")
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne")
    # corrupt the t-SNE side's cohort after the fact
    tsne_metadata = pd.read_csv(tsne_dir / "metadata.csv")
    tsne_metadata.loc[0, "subject_id"] = "sub-DIFFERENT"
    tsne_metadata.to_csv(tsne_dir / "metadata.csv", index=False)

    with pytest.raises(ValueError, match="don't match"):
        generate_report(umap_dir, tsne_dir, tmp_path / "out")


def test_generate_report_raises_filenotfounderror_on_missing_umap_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        generate_report(tmp_path / "does-not-exist", tmp_path / "tsne", tmp_path / "out")
