"""`src/analysis/embedding_plots.py` e `component_map_plots.py`: rami di fallimento di un singolo grafico e validazioni.

Complementa `test_embedding_plots.py` (successo + modalità di colore fallita): qui falliscono il grafico "unico", il
rendering categorico/continuo e la griglia "unico", e si verifica che il resto dell'output venga comunque scritto.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from src.analysis import embedding_plots
from src.analysis.component_map_plots import PAPER_REPRODUCIBILITY, build_reproducibility_figure
from src.analysis.embedding_plots import write_embedding_grid, write_embedding_plots


def _data(n=10):
    rng = np.random.default_rng(0)
    metadata = pd.DataFrame({
        "subject_id": [f"sub-{i}" for i in range(n)],
        "dataset": ["A"] * (n // 2) + ["B"] * (n - n // 2),
    })
    return rng.random((n, 2)) * 10, metadata


def _title(label):
    return f"t - {label}" if label else "t"


def _boom(*args, **kwargs):
    raise RuntimeError("render exploded")


def test_unico_failure_is_a_warning_and_color_modes_are_still_written(tmp_path, monkeypatch, caplog):
    embedding, metadata = _data()
    monkeypatch.setattr(embedding_plots, "plot_embedding_2d", _boom)
    with caplog.at_level(logging.WARNING):
        write_embedding_plots(embedding, metadata, ["dataset"], tmp_path, "x", "y", _title)
    assert not (tmp_path / "embedding_plot_unico.png").exists()
    assert (tmp_path / "embedding_plot_dataset.png").stat().st_size > 0
    assert "failed to generate 'unico' embedding plot: render exploded" in caplog.text


def test_categorical_render_failure_names_the_mode_and_keeps_the_others(tmp_path, monkeypatch, caplog):
    embedding, metadata = _data()
    monkeypatch.setattr(embedding_plots, "plot_embedding_categorical", _boom)
    with caplog.at_level(logging.WARNING):
        write_embedding_plots(embedding, metadata, ["dataset"], tmp_path, "x", "y", _title)
    assert (tmp_path / "embedding_plot_unico.png").is_file()
    assert not (tmp_path / "embedding_plot_dataset.png").exists()
    assert "failed to generate 'dataset' embedding plot" in caplog.text


def test_continuous_render_failure_is_isolated_per_mode(tmp_path, monkeypatch, caplog):
    from src.utils import participants as participants_registry

    embedding, metadata = _data()
    root = tmp_path / "metadata"
    root.mkdir()
    pd.DataFrame({
        "subject_id": metadata["subject_id"], "original_id": metadata["subject_id"], "dataset": "A", "disease_id": "ST",
        "has_lesion": "True", "has_sdc": "False", "has_features": "False",
        "lesion_volume_voxels_2mm": np.arange(1, 11),
    }).to_csv(root / "participants.csv", index=False)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    monkeypatch.setattr(embedding_plots, "plot_embedding_continuous", _boom)
    out = tmp_path / "out"
    out.mkdir()

    with caplog.at_level(logging.WARNING):
        write_embedding_plots(embedding, metadata, ["dataset", "volume"], out, "x", "y", _title)

    assert (out / "embedding_plot_dataset.png").is_file()
    assert not (out / "embedding_plot_volume.png").exists()
    assert "failed to generate 'volume' embedding plot: render exploded" in caplog.text


def test_color_values_failure_message_carries_the_cause(tmp_path, caplog):
    embedding, metadata = _data()
    with caplog.at_level(logging.WARNING):
        write_embedding_plots(embedding, metadata, ["cluster_label"], tmp_path, "x", "y", _title)
    assert "failed to read values for color_by mode 'cluster_label'" in caplog.text
    assert "metadata has no 'cluster_label' column" in caplog.text


def test_grid_unico_failure_is_a_warning_and_color_grids_still_written(tmp_path, monkeypatch, caplog):
    rng = np.random.default_rng(1)
    blocks = [("k", [("a", rng.random((6, 2))), ("b", rng.random((6, 2)))])]
    metadata = pd.DataFrame({"subject_id": [f"s{i}" for i in range(6)], "dataset": ["A"] * 3 + ["B"] * 3})
    real = embedding_plots.plot_embedding_grid_blocks

    def fail_only_unico(blocks, path, *args, **kwargs):
        if path.name.endswith("_unico.png"):
            raise RuntimeError("render exploded")
        return real(blocks, path, *args, **kwargs)

    monkeypatch.setattr(embedding_plots, "plot_embedding_grid_blocks", fail_only_unico)
    with caplog.at_level(logging.WARNING):
        write_embedding_grid(blocks, metadata, ["dataset"], tmp_path, "x", "y", _title)
    assert not (tmp_path / "embeddings_grid_unico.png").exists()
    assert (tmp_path / "embeddings_grid_dataset.png").stat().st_size > 0
    assert "failed to generate 'unico' embedding grid" in caplog.text


def test_three_component_embedding_with_zlabel_writes_nothing_and_computes_no_values(tmp_path, monkeypatch):
    monkeypatch.setattr(embedding_plots, "color_values", _boom)  # non deve nemmeno essere chiamata
    embedding = np.random.default_rng(0).random((10, 3))
    _, metadata = _data()
    write_embedding_plots(embedding, metadata, ["dataset"], tmp_path, "x", "y", _title, zlabel="z")
    assert list(tmp_path.iterdir()) == []


def test_single_column_embedding_is_rejected(tmp_path):
    _, metadata = _data()
    with pytest.raises(ValueError, match="2 or 3 embedding dimensions, got 1"):
        write_embedding_plots(np.zeros((10, 1)), metadata, [], tmp_path, "x", "y", _title)


# --- component_map_plots ----------------------------------------------------------------------------------


def test_reproducibility_figure_has_one_bar_per_component_with_the_selected_one_darker():
    values = np.array([0.9, 0.8, 0.4])
    figure = build_reproducibility_figure(values, selected=2)
    (bar,) = figure.data
    assert list(bar.x) == [1, 2, 3]
    np.testing.assert_allclose(bar.y, values)
    colors = list(bar.marker.color)
    assert colors[1] != colors[0] and colors[0] == colors[2]


def test_reproducibility_figure_draws_the_paper_mean_as_a_reference_line():
    figure = build_reproducibility_figure(np.array([0.5, 0.6]), selected=1)
    (line,) = figure.layout.shapes
    assert line.y0 == line.y1 == PAPER_REPRODUCIBILITY
    assert tuple(figure.layout.yaxis.range) == (0, 1.02)


def test_reproducibility_figure_rejects_empty_input():
    with pytest.raises(ValueError, match="no component to draw"):
        build_reproducibility_figure(np.array([]), selected=1)


@pytest.mark.parametrize("selected", [0, 4, -1])
def test_reproducibility_figure_rejects_selected_outside_range(selected):
    with pytest.raises(ValueError, match=r"selected must be in 1\.\.3"):
        build_reproducibility_figure(np.array([0.9, 0.8, 0.4]), selected=selected)
