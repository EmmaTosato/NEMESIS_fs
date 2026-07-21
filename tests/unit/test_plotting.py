"""Unit tests for src/analysis/plotting.py - plot_embedding_interactive/plot_clusters_interactive."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.plotting import plot_clusters_interactive, plot_embedding_interactive


def _embedding_and_metadata():
    X_2d = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    metadata = pd.DataFrame(
        {
            "subject_id": ["sub-1", "sub-2", "sub-3", "sub-4"],
            "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR", "UKLFR/stroke_UKLFR"],
        }
    )
    return X_2d, metadata


def _embedding_and_cluster_metadata():
    X_2d, metadata = _embedding_and_metadata()
    metadata = metadata.copy()
    metadata["cluster_label"] = [0, 0, 1, -1]
    return X_2d, metadata


def test_writes_html_file(tmp_path):
    X_2d, metadata = _embedding_and_metadata()
    output_path = tmp_path / "embedding_plot_interactive.html"

    plot_embedding_interactive(X_2d, metadata, output_path, "dim 1", "dim 2", "test title")

    assert output_path.exists()
    html = output_path.read_text()
    assert "plotly" in html
    for subject_id in metadata["subject_id"]:
        assert subject_id in html


def test_raises_on_fewer_than_two_columns(tmp_path):
    X_1d = np.array([[0.0], [1.0], [2.0], [3.0]])
    _, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="at least 2 columns"):
        plot_embedding_interactive(X_1d, metadata, tmp_path / "out.html", "x", "y", "title")


def test_raises_on_row_count_mismatch(tmp_path):
    X_2d, metadata = _embedding_and_metadata()
    mismatched_metadata = metadata.iloc[:-1]

    with pytest.raises(ValueError, match="must match"):
        plot_embedding_interactive(X_2d, mismatched_metadata, tmp_path / "out.html", "x", "y", "title")


def test_raises_on_missing_color_column(tmp_path):
    X_2d, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="color_column"):
        plot_embedding_interactive(
            X_2d, metadata, tmp_path / "out.html", "x", "y", "title", color_column="not_a_column"
        )


def test_clusters_interactive_writes_html_with_dropdown(tmp_path):
    X_2d, metadata = _embedding_and_cluster_metadata()
    output_path = tmp_path / "cluster_plot_interactive.html"

    plot_clusters_interactive(X_2d, metadata, output_path, "dim 1", "dim 2", "test title")

    assert output_path.exists()
    html = output_path.read_text()
    assert "plotly" in html
    assert "updatemenus" in html
    assert "Color by cluster_label" in html
    assert "Color by dataset" in html
    for subject_id in metadata["subject_id"]:
        assert subject_id in html


def test_clusters_interactive_raises_on_fewer_than_two_columns(tmp_path):
    X_1d = np.array([[0.0], [1.0], [2.0], [3.0]])
    _, metadata = _embedding_and_cluster_metadata()

    with pytest.raises(ValueError, match="at least 2 columns"):
        plot_clusters_interactive(X_1d, metadata, tmp_path / "out.html", "x", "y", "title")


def test_clusters_interactive_raises_on_row_count_mismatch(tmp_path):
    X_2d, metadata = _embedding_and_cluster_metadata()
    mismatched_metadata = metadata.iloc[:-1]

    with pytest.raises(ValueError, match="must match"):
        plot_clusters_interactive(X_2d, mismatched_metadata, tmp_path / "out.html", "x", "y", "title")


def test_clusters_interactive_raises_on_missing_cluster_column(tmp_path):
    X_2d, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="cluster_label"):
        plot_clusters_interactive(X_2d, metadata, tmp_path / "out.html", "x", "y", "title")


def test_clusters_interactive_raises_on_missing_dataset_column(tmp_path):
    X_2d, metadata = _embedding_and_cluster_metadata()
    metadata_no_dataset = metadata.drop(columns=["dataset"])

    with pytest.raises(ValueError, match="dataset"):
        plot_clusters_interactive(X_2d, metadata_no_dataset, tmp_path / "out.html", "x", "y", "title")
