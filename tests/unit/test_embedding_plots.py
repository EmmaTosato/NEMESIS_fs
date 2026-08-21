"""Unit tests for src/analysis/embedding_plots.py."""

import logging

import numpy as np
import pandas as pd
import pytest

from src.analysis.embedding_plots import write_embedding_grid, write_embedding_plots


def _embedding_metadata(n=10, n_dims=2):
    rng = np.random.default_rng(0)
    embedding = rng.random((n, n_dims)) * 10
    metadata = pd.DataFrame(
        {
            "subject_id": [f"sub-{i}" for i in range(n)],
            "dataset": ["UNIPD/WashU"] * (n // 2) + ["UKLFR/stroke_UKLFR"] * (n - n // 2),
            "lesion_volume_voxels": rng.integers(1, 100, size=n),
        }
    )
    return embedding, metadata


def _title_fn(label):
    return f"title - {label}" if label else "title"


def test_write_embedding_plots_2d_writes_unico_and_color_by(tmp_path):
    embedding, metadata = _embedding_metadata()

    write_embedding_plots(embedding, metadata, ["dataset", "volume"], tmp_path, "x", "y", _title_fn)

    assert (tmp_path / "embedding_plot_unico.png").exists()
    assert (tmp_path / "embedding_plot_dataset.png").exists()
    assert (tmp_path / "embedding_plot_volume.png").exists()


def test_write_embedding_plots_empty_color_by_writes_only_unico(tmp_path):
    embedding, metadata = _embedding_metadata()

    write_embedding_plots(embedding, metadata, [], tmp_path, "x", "y", _title_fn)

    files = list(tmp_path.iterdir())
    assert [f.name for f in files] == ["embedding_plot_unico.png"]


def test_write_embedding_plots_3d_writes_nothing(tmp_path):
    # No static rendering exists for a 3-component embedding anywhere in this module -
    # explore it interactively instead via src.pipeline.embedding_app (docs/guides/embedding_app.md).
    embedding, metadata = _embedding_metadata(n_dims=3)

    write_embedding_plots(embedding, metadata, ["dataset"], tmp_path, "x", "y", _title_fn, zlabel="z")

    assert list(tmp_path.iterdir()) == []


def test_write_embedding_plots_3d_without_zlabel_raises(tmp_path):
    embedding, metadata = _embedding_metadata(n_dims=3)

    with pytest.raises(ValueError, match="needs zlabel"):
        write_embedding_plots(embedding, metadata, [], tmp_path, "x", "y", _title_fn)


def test_write_embedding_plots_invalid_dimensions_raises(tmp_path):
    embedding, metadata = _embedding_metadata(n_dims=1)

    with pytest.raises(ValueError, match="supports 2 or 3 embedding dimensions"):
        write_embedding_plots(embedding, metadata, [], tmp_path, "x", "y", _title_fn)


def test_write_embedding_plots_unknown_color_by_raises(tmp_path):
    embedding, metadata = _embedding_metadata()

    with pytest.raises(ValueError, match="unknown color_by mode"):
        write_embedding_plots(embedding, metadata, ["bogus"], tmp_path, "x", "y", _title_fn)


def test_write_embedding_plots_one_bad_color_mode_does_not_abort_the_others(tmp_path, caplog):
    # "side" reads metadata's own lesion_side column - absent here, so color_values raises
    # ValueError for this mode specifically, without touching participants.tsv at all
    # (2026-08-17: "side" no longer recomputes live - see src/analysis/embedding_coloring.py).
    embedding, metadata = _embedding_metadata()

    with caplog.at_level(logging.WARNING):
        write_embedding_plots(embedding, metadata, ["dataset", "side"], tmp_path, "x", "y", _title_fn)

    assert (tmp_path / "embedding_plot_dataset.png").exists()
    assert not (tmp_path / "embedding_plot_side.png").exists()
    assert any("side" in record.message for record in caplog.records)


def test_write_embedding_plots_all_color_modes_fail_writes_only_unico(tmp_path, caplog):
    embedding, metadata = _embedding_metadata()

    with caplog.at_level(logging.WARNING):
        write_embedding_plots(embedding, metadata, ["side"], tmp_path, "x", "y", _title_fn)

    files = list(tmp_path.iterdir())
    assert [f.name for f in files] == ["embedding_plot_unico.png"]


def _blocks(n_per_cell=6):
    rng = np.random.default_rng(0)
    return [
        ("n_neighbors", [("5", rng.random((n_per_cell, 2)) * 10), ("10", rng.random((n_per_cell, 2)) * 10)]),
        ("min_dist", [("0.0", rng.random((n_per_cell, 2)) * 10), ("0.2", rng.random((n_per_cell, 2)) * 10)]),
    ]


def _grid_metadata(n=6):
    rng = np.random.default_rng(1)
    return pd.DataFrame(
        {
            "subject_id": [f"sub-{i}" for i in range(n)],
            "dataset": ["UNIPD/WashU"] * 3 + ["UKLFR/stroke_UKLFR"] * 3,
            "lesion_volume_voxels": rng.integers(1, 100, size=n),
        }
    )


def test_write_embedding_grid_writes_unico_and_color_by(tmp_path):
    metadata = _grid_metadata()

    write_embedding_grid(_blocks(), metadata, ["dataset", "volume"], tmp_path, "x", "y", _title_fn)

    assert (tmp_path / "embeddings_grid_unico.png").exists()
    assert (tmp_path / "embeddings_grid_dataset.png").exists()
    assert (tmp_path / "embeddings_grid_volume.png").exists()


def test_write_embedding_grid_empty_color_by_writes_only_unico(tmp_path):
    metadata = _grid_metadata()

    write_embedding_grid(_blocks(), metadata, [], tmp_path, "x", "y", _title_fn)

    files = list(tmp_path.iterdir())
    assert [f.name for f in files] == ["embeddings_grid_unico.png"]


def test_write_embedding_grid_bad_color_mode_does_not_abort_the_others(tmp_path, caplog):
    metadata = _grid_metadata()  # no lesion_side column

    with caplog.at_level(logging.WARNING):
        write_embedding_grid(_blocks(), metadata, ["dataset", "side"], tmp_path, "x", "y", _title_fn)

    assert (tmp_path / "embeddings_grid_dataset.png").exists()
    assert not (tmp_path / "embeddings_grid_side.png").exists()
    assert any("side" in record.message for record in caplog.records)
