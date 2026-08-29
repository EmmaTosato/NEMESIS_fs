"""Unit tests for src/analysis/understanding_umap_report.py - _combo_key,
_read_base_n_components, _color_values_for_mode, and an E2E generate_report
run over a tiny real-shaped (synthetic, small) tuning-output fixture."""

import json
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


def _sdc_metadata() -> pd.DataFrame:
    """Same subjects/order as _metadata(), but shaped like a build_sdc_matrix.py-derived
    tuning run's metadata.csv - no lesion_volume_voxels, since a continuous disconnectome
    matrix has no meaningful per-subject "volume" (see docs/dev/sdc_matrix.md)."""
    metadata = _metadata()
    return metadata.drop(columns=["lesion_volume_voxels"])


def _write_umap_tuning_dir(root: Path, metric: str = "dice", metadata: pd.DataFrame | None = None) -> Path:
    """A tiny nested_params=["metric", "n_components"] UMAP tuning dir, same
    shape as src.pipeline.dim_reduction's real output - one metric, 2
    n_components leaves (2 and 3), 2 n_neighbors x 2 min_dist combos each.
    """
    root.mkdir(parents=True)
    metadata = _metadata() if metadata is None else metadata
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


def _write_tsne_tuning_dir(root: Path, metric: str = "dice", metadata: pd.DataFrame | None = None) -> Path:
    """A tiny nested_params=["metric"] t-SNE tuning dir (always 2D), same
    subject cohort/order as _write_umap_tuning_dir.
    """
    root.mkdir(parents=True)
    metadata = _metadata() if metadata is None else metadata
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


def test_read_base_n_components_raises_valueerror_not_keyerror_when_key_missing(tmp_path):
    """Regression (HIGH #23, 2026-08): the fenced json block's own keys were indexed
    directly (["base_params"]["n_components"]) with no validation - a config.md whose
    fenced block parses but is missing either key raised a raw KeyError, not caught by
    any caller's `except ValueError` (load_tuning_data -> generate_report -> main())."""
    (tmp_path / "config.md").write_text('# run\n\n```json\n{"base_params": {"rotation_max_iter": 500}}\n```\n')

    with pytest.raises(ValueError, match="n_components"):
        _read_base_n_components(tmp_path)


def test_read_base_n_components_raises_valueerror_when_block_is_not_an_object(tmp_path):
    (tmp_path / "config.md").write_text("# run\n\n```json\n[1, 2, 3]\n```\n")

    with pytest.raises(ValueError, match="n_components"):
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


def test_color_values_for_mode_continuous_nan_becomes_json_safe_none():
    """Regression (HIGH #21, 2026-08): a continuous mode's per-subject NaN (subject 3's
    "nihss" in _metadata - a real PASPORT-like structural gap) used to be embedded verbatim
    as a raw float NaN, which json.dumps serializes as the bare token `NaN` - not valid JSON
    (JavaScript's JSON.parse rejects it). Must be Python None (-> JSON `null`) instead, and
    the whole colors dict must be JSON-serializable end to end."""
    colors = _color_values_for_mode(_metadata(), "nihss")

    assert colors["color"][2] is None
    # json.dumps allows a raw float NaN by default (Python-only extension, invalid per the
    # JSON spec) without raising - the only real check is that the token never appears.
    assert "NaN" not in json.dumps(colors)


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


def test_generate_report_omits_color_modes_missing_from_metadata(tmp_path):
    """Regression (2026-08-28): a tuning run whose metadata.csv has no lesion_volume_voxels
    (e.g. a build_sdc_matrix.py-derived matrix, which has no meaningful per-subject "volume")
    used to crash with KeyError: 'lesion_volume_voxels' - COLOR_BY_MODES always included
    "volume" regardless of what the real metadata.csv actually has. Must now succeed,
    offering only the color modes this run's own metadata actually backs."""
    sdc_metadata = _sdc_metadata()
    umap_dir = _write_umap_tuning_dir(tmp_path / "umap", metadata=sdc_metadata)
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne", metadata=sdc_metadata)

    output_paths = generate_report(umap_dir, tsne_dir, tmp_path / "out")

    html = output_paths[0].read_text()
    assert 'onclick="setColor(\'dataset\'' in html
    assert 'onclick="setColor(\'side\'' in html
    assert 'onclick="setColor(\'nihss\'' in html
    assert 'onclick="setColor(\'volume\'' not in html
    assert '"volume":' not in html.split("const COLORS = ")[1].split(";")[0]


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


def test_generate_report_raises_valueerror_on_corrupt_embeddings_npz(tmp_path):
    """Regression (HIGH #24, 2026-08): a run interrupted mid-write (SLURM timeout,
    Ctrl+C) during dim_reduction.py's np.savez leaves embeddings.npz truncated - np.load
    raised zipfile.BadZipFile/OSError, neither caught by generate_understanding_umap_report.py's
    `except (FileNotFoundError, ValueError)`, so it propagated as a raw traceback."""
    umap_dir = _write_umap_tuning_dir(tmp_path / "umap")
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne")
    # A genuinely truncated npz (real npz files are zip archives) - not just an arbitrary
    # byte string, to actually exercise zipfile.BadZipFile, not numpy's own unrelated
    # "looks like a pickle" ValueError for a file that never looked like a zip at all.
    npz_bytes = (umap_dir / "embeddings.npz").read_bytes()
    (umap_dir / "embeddings.npz").write_bytes(npz_bytes[: len(npz_bytes) // 2])

    with pytest.raises(ValueError, match="cannot read embeddings"):
        generate_report(umap_dir, tsne_dir, tmp_path / "out")


def test_generate_report_removes_partial_output_when_a_later_metric_fails(tmp_path, monkeypatch):
    """Regression (HIGH #22, 2026-08): a report with 2+ metrics used to leave the earlier
    metric's understanding_umap_<metric>.html on disk even when a later metric's
    build_leaf_page failed partway through the sweep - a second run afterwards would look
    complete (both files eventually exist) but a run that's interrupted and never retried
    would leave a report that silently looks finished while missing one metric's page."""
    import src.analysis.understanding_umap_report as report_module

    umap_dir = _write_umap_tuning_dir(tmp_path / "umap", metric="dice")
    # A second metric leaf, just enough for load_tuning_data's own metrics discovery
    # (glob("metric=*")) to see 2 metrics - build_leaf_page itself is monkeypatched below,
    # so its own tuning_results.csv/embeddings.npz content never needs to be real.
    (umap_dir / "metric=euclidean" / "n_components=2").mkdir(parents=True)
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne", metric="dice")
    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True)

    def _fake_build_leaf_page(metric, *args, **kwargs):
        output_path = args[-1]
        if metric == "euclidean":
            raise ValueError("simulated failure: no n_components=3 leaf for this metric")
        output_path.write_text("<html>fake report</html>")

    monkeypatch.setattr(report_module, "build_leaf_page", _fake_build_leaf_page)

    with pytest.raises(ValueError, match="simulated failure"):
        report_module.generate_report(umap_dir, tsne_dir, output_dir)

    assert not (output_dir / "understanding_umap_dice.html").exists()
    assert not (output_dir / "understanding_umap_euclidean.html").exists()
