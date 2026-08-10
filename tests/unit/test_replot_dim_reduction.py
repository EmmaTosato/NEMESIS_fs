"""Unit tests for scripts/replot_dim_reduction.py - synthetic fixtures, no real run needed."""

import numpy as np
import pandas as pd
import pytest

from scripts import replot_dim_reduction
from src.utils.artifacts import save_matrix


def _make_run_dir(tmp_path, drop_columns=None):
    run_dir = tmp_path / "results" / "lesion" / "dim_reduction" / "umap" / "10-08_s1"
    X = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5]])
    metadata = pd.DataFrame(
        {
            "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
            "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UNIPD/PASPORT"],
            "lesion_side": ["L", "R", "L"],
            "lesion_volume_voxels": [100, 200, 50],
            "nihss": [4.0, np.nan, 7.0],
        }
    )
    if drop_columns:
        metadata = metadata.drop(columns=list(drop_columns))
    save_matrix(run_dir, X, metadata, readme_lines=["# test run"], overwrite=False)
    return run_dir


def test_replot_embedding_writes_one_pair_per_registered_color_mode(tmp_path):
    """Regression: replot used to hardcode exactly 3 of the 4 registered
    color_by modes (dataset/side/volume) - "nihss" was silently never
    replotted, with no error/log. It must now drive off the same
    embedding_coloring.COLOR_MODES registry production uses."""
    run_dir = _make_run_dir(tmp_path)

    output_paths = replot_dim_reduction.replot(run_dir)

    names = {p.name for p in output_paths}
    assert "embedding_plot_unico.png" in names
    for mode in ("dataset", "side", "volume", "nihss"):
        assert f"embedding_plot_{mode}.png" in names, f"missing static plot for {mode}"
        assert f"embedding_plot_{mode}.html" in names, f"missing interactive plot for {mode}"
    for path in output_paths:
        assert path.is_file()
        assert path.stat().st_size > 0


def test_replot_embedding_skips_missing_column_with_warning_not_crash(tmp_path, caplog):
    """An old run's metadata.csv predating "nihss" must not crash the whole
    replot - just skip that one mode, with a clear warning, and still
    produce every other plot."""
    run_dir = _make_run_dir(tmp_path, drop_columns=["nihss"])

    with caplog.at_level("WARNING"):
        output_paths = replot_dim_reduction.replot(run_dir)

    names = {p.name for p in output_paths}
    assert "embedding_plot_nihss.png" not in names
    assert "embedding_plot_nihss.html" not in names
    assert "embedding_plot_dataset.png" in names  # the rest still get plotted
    assert any("nihss" in record.message for record in caplog.records)


def test_replot_embedding_raises_for_missing_dataset_column(tmp_path):
    run_dir = _make_run_dir(tmp_path, drop_columns=["dataset"])
    with pytest.raises(ValueError, match="dataset"):
        replot_dim_reduction.replot(run_dir)


def test_replot_rejects_embedding_with_more_than_2_components(tmp_path):
    run_dir = tmp_path / "results" / "lesion" / "dim_reduction" / "umap" / "10-08_s1"
    X = np.zeros((3, 5))
    metadata = pd.DataFrame({"subject_id": ["a", "b", "c"], "dataset": ["d", "d", "d"]})
    save_matrix(run_dir, X, metadata, readme_lines=["# test"], overwrite=False)

    with pytest.raises(ValueError, match="5 component"):
        replot_dim_reduction.replot(run_dir)


def test_replot_clustering_run_colors_by_cluster_only(tmp_path):
    run_dir = tmp_path / "results" / "lesion" / "dim_reduction_clustering" / "umap" / "kmeans" / "10-08_s1"
    X = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5]])
    metadata = pd.DataFrame({"subject_id": ["a", "b", "c"], "dataset": ["d", "d", "d"], "cluster_label": [0, 1, 0]})
    save_matrix(run_dir, X, metadata, readme_lines=["# test"], overwrite=False)

    output_paths = replot_dim_reduction.replot(run_dir)

    names = {p.name for p in output_paths}
    assert names == {"cluster_plot.png", "cluster_plot_interactive.html"}
