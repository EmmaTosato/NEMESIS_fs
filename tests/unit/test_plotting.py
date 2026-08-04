"""Unit tests for src/analysis/plotting.py - plot_embedding_interactive/plot_clusters_interactive/
plot_clusters_comparison_interactive/compose_run_title/compose_embedding_plot_title/
plot_embedding_categorical/plot_embedding_continuous/plot_clustering_tuning_metrics/
plot_dendrogram/plot_eigengap/plot_silhouette_analysis."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.plotting import (
    compose_embedding_plot_title,
    compose_run_title,
    plot_clustering_tuning_heatmaps,
    plot_clustering_tuning_metrics,
    plot_clusters_comparison_interactive,
    plot_clusters_interactive,
    plot_dendrogram,
    plot_eigengap,
    plot_embedding_categorical,
    plot_embedding_continuous,
    plot_embedding_grid_blocks,
    plot_embedding_interactive,
    plot_silhouette_analysis,
)


def test_compose_run_title_drops_leading_results_segment():
    output_dir = Path("results/lesion/dim_reduction/umap/21-07_s1_d01")

    title = compose_run_title(output_dir, "clinical_connectome")

    assert title == "clinical_connectome — lesion › dim_reduction › umap › 21-07_s1_d01"


def test_compose_run_title_keeps_full_path_without_leading_results():
    output_dir = Path("other_root/umap/21-07_s1")

    title = compose_run_title(output_dir, "clinical_connectome")

    assert title == "clinical_connectome — other_root › umap › 21-07_s1"


def test_compose_embedding_plot_title_base():
    output_dir = Path("results/lesion/dim_reduction/umap/21-07_s1_d01")

    assert compose_embedding_plot_title(output_dir, "umap") == "Lesions - Umap"


def test_compose_embedding_plot_title_with_color_by():
    output_dir = Path("results/lesion/dim_reduction/umap/21-07_s1_d01")

    assert compose_embedding_plot_title(output_dir, "umap", "Dataset") == "Lesions - Umap - Dataset"


def test_compose_embedding_plot_title_raises_without_modality_segment():
    with pytest.raises(ValueError, match="cannot derive a modality"):
        compose_embedding_plot_title(Path("results"), "umap")


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

    with pytest.raises(ValueError, match="supports 2 or 3 columns"):
        plot_embedding_interactive(X_1d, metadata, tmp_path / "out.html", "x", "y", "title")


def test_raises_on_more_than_three_columns(tmp_path):
    X_4d = np.zeros((4, 4))
    _, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="supports 2 or 3 columns"):
        plot_embedding_interactive(X_4d, metadata, tmp_path / "out.html", "x", "y", "title")


def test_writes_html_file_3d_scatter(tmp_path):
    _, metadata = _embedding_and_metadata()
    X_3d = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])
    output_path = tmp_path / "embedding_plot_3d.html"

    plot_embedding_interactive(X_3d, metadata, output_path, "dim 1", "dim 2", "test title", zlabel="dim 3")

    assert output_path.exists()
    html = output_path.read_text()
    assert "plotly" in html
    for subject_id in metadata["subject_id"]:
        assert subject_id in html


def test_raises_without_zlabel_for_3d(tmp_path):
    _, metadata = _embedding_and_metadata()
    X_3d = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])

    with pytest.raises(ValueError, match="needs zlabel"):
        plot_embedding_interactive(X_3d, metadata, tmp_path / "out.html", "x", "y", "title")


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


def test_plot_embedding_categorical_writes_file(tmp_path):
    X_2d, metadata = _embedding_and_metadata()
    output_path = tmp_path / "embedding_plot_dataset.png"

    plot_embedding_categorical(X_2d, metadata["dataset"].to_numpy(), output_path, "x", "y", "title", legend_title="dataset")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_categorical_handles_missing_label(tmp_path):
    categories = np.array(["left", "right", "unknown", "left"])
    X_2d, _ = _embedding_and_metadata()
    output_path = tmp_path / "embedding_plot_side.png"

    plot_embedding_categorical(X_2d, categories, output_path, "x", "y", "title", legend_title="lesion_side")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_categorical_raises_on_fewer_than_two_columns(tmp_path):
    X_1d = np.array([[0.0], [1.0], [2.0], [3.0]])
    categories = np.array(["left", "right", "left", "right"])

    with pytest.raises(ValueError, match="at least 2 columns"):
        plot_embedding_categorical(X_1d, categories, tmp_path / "out.png", "x", "y", "title", legend_title="side")


def test_plot_embedding_continuous_writes_file(tmp_path):
    X_2d, _ = _embedding_and_metadata()
    values = np.array([10.0, 20.0, 30.0, 40.0])
    output_path = tmp_path / "embedding_plot_volume.png"

    plot_embedding_continuous(X_2d, values, output_path, "x", "y", "title", colorbar_label="lesion volume (voxels)")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_continuous_renders_nan_as_gray_points(tmp_path):
    X_2d, _ = _embedding_and_metadata()
    values = np.array([10.0, np.nan, 30.0, 40.0])
    output_path = tmp_path / "embedding_plot_nihss.png"

    plot_embedding_continuous(X_2d, values, output_path, "x", "y", "title", colorbar_label="NIHSS (severity)")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_continuous_all_nan_does_not_raise(tmp_path):
    X_2d, _ = _embedding_and_metadata()
    values = np.full(4, np.nan)
    output_path = tmp_path / "embedding_plot_nihss_all_missing.png"

    plot_embedding_continuous(X_2d, values, output_path, "x", "y", "title", colorbar_label="NIHSS (severity)")

    assert output_path.exists()


def test_plot_embedding_continuous_log_scale_writes_file(tmp_path):
    X_2d, _ = _embedding_and_metadata()
    values = np.array([1.0, 100.0, 5000.0, 40000.0])
    output_path = tmp_path / "embedding_plot_volume.png"

    plot_embedding_continuous(
        X_2d, values, output_path, "x", "y", "title", colorbar_label="lesion volume (voxels)", log_scale=True
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_continuous_log_scale_with_nan_writes_file(tmp_path):
    X_2d, _ = _embedding_and_metadata()
    values = np.array([1.0, np.nan, 5000.0, 40000.0])
    output_path = tmp_path / "embedding_plot_volume_missing.png"

    plot_embedding_continuous(
        X_2d, values, output_path, "x", "y", "title", colorbar_label="lesion volume (voxels)", log_scale=True
    )

    assert output_path.exists()


def test_plot_embedding_continuous_log_scale_rejects_non_positive_value(tmp_path):
    X_2d, _ = _embedding_and_metadata()
    values = np.array([0.0, 100.0, 5000.0, 40000.0])

    with pytest.raises(ValueError, match="log_scale=True needs every non-missing value > 0"):
        plot_embedding_continuous(
            X_2d, values, tmp_path / "out.png", "x", "y", "title", colorbar_label="volume", log_scale=True
        )


def test_plot_embedding_continuous_raises_on_fewer_than_two_columns(tmp_path):
    X_1d = np.array([[0.0], [1.0], [2.0], [3.0]])
    values = np.array([10.0, 20.0, 30.0, 40.0])

    with pytest.raises(ValueError, match="at least 2 columns"):
        plot_embedding_continuous(X_1d, values, tmp_path / "out.png", "x", "y", "title", colorbar_label="volume")


def test_clusters_interactive_writes_html_colored_by_cluster(tmp_path):
    X_2d, metadata = _embedding_and_cluster_metadata()
    output_path = tmp_path / "cluster_plot_interactive.html"

    plot_clusters_interactive(X_2d, metadata, output_path, "dim 1", "dim 2", "test title")

    assert output_path.exists()
    html = output_path.read_text()
    assert "plotly" in html
    assert "Color by" not in html  # no dataset/cluster toggle - cluster-only coloring, no dropdown buttons
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


def _labels_by_method():
    return {
        "kmeans": np.array([0, 0, 1, 1]),
        "agglomerative": np.array([0, 1, 1, 0]),
    }


def test_clusters_comparison_interactive_writes_html_with_dropdown(tmp_path):
    X_2d, metadata = _embedding_and_metadata()
    output_path = tmp_path / "cluster_comparison_interactive.html"

    plot_clusters_comparison_interactive(X_2d, _labels_by_method(), metadata, output_path, "dim 1", "dim 2", "test title")

    assert output_path.exists()
    html = output_path.read_text()
    assert "plotly" in html
    assert "updatemenus" in html
    assert "kmeans" in html
    assert "agglomerative" in html
    for subject_id in metadata["subject_id"]:
        assert subject_id in html


def test_clusters_comparison_interactive_raises_on_fewer_than_two_columns(tmp_path):
    X_1d = np.array([[0.0], [1.0], [2.0], [3.0]])
    _, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="at least 2 columns"):
        plot_clusters_comparison_interactive(X_1d, _labels_by_method(), metadata, tmp_path / "out.html", "x", "y", "title")


def test_clusters_comparison_interactive_raises_on_row_count_mismatch(tmp_path):
    X_2d, metadata = _embedding_and_metadata()
    mismatched_metadata = metadata.iloc[:-1]

    with pytest.raises(ValueError, match="must match"):
        plot_clusters_comparison_interactive(
            X_2d, _labels_by_method(), mismatched_metadata, tmp_path / "out.html", "x", "y", "title"
        )


def test_clusters_comparison_interactive_raises_on_empty_labels_by_method(tmp_path):
    X_2d, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="at least one method"):
        plot_clusters_comparison_interactive(X_2d, {}, metadata, tmp_path / "out.html", "x", "y", "title")


def test_plot_clustering_tuning_metrics_writes_one_subplot_per_metric(tmp_path):
    df = pd.DataFrame(
        {
            "n_clusters": [2, 3, 4],
            "silhouette": [0.4, 0.8, 0.6],
            "calinski_harabasz": [50.0, 500.0, 300.0],
            "inertia": [200.0, 10.0, 8.0],
        }
    )
    output_path = tmp_path / "tuning_plot.png"

    plot_clustering_tuning_metrics(df, "n_clusters", ["silhouette", "calinski_harabasz", "inertia"], output_path, "test title")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_clustering_tuning_metrics_raises_on_empty_metric_cols(tmp_path):
    df = pd.DataFrame({"n_clusters": [2, 3], "silhouette": [0.4, 0.8]})

    with pytest.raises(ValueError, match="at least one metric column"):
        plot_clustering_tuning_metrics(df, "n_clusters", [], tmp_path / "out.png", "title")


def test_plot_clustering_tuning_heatmaps_writes_one_subplot_per_metric(tmp_path):
    df = pd.DataFrame(
        {
            "eps": [0.3, 0.3, 0.5, 0.5],
            "min_samples": [3, 5, 3, 5],
            "silhouette": [0.4, 0.5, 0.6, 0.7],
            "calinski_harabasz": [50.0, 60.0, 70.0, 80.0],
        }
    )
    output_path = tmp_path / "tuning_plot.png"

    plot_clustering_tuning_heatmaps(df, "eps", "min_samples", ["silhouette", "calinski_harabasz"], output_path, "test title")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_clustering_tuning_heatmaps_raises_on_empty_metric_cols(tmp_path):
    df = pd.DataFrame({"eps": [0.3, 0.5], "min_samples": [3, 5], "silhouette": [0.4, 0.8]})

    with pytest.raises(ValueError, match="at least one metric column"):
        plot_clustering_tuning_heatmaps(df, "eps", "min_samples", [], tmp_path / "out.png", "title")


def test_plot_dendrogram_writes_file(tmp_path):
    from src.analysis.clustering_tuning import compute_dendrogram_linkage

    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(loc=[0, 0], size=(10, 2)), rng.normal(loc=[5, 5], size=(10, 2))])
    linkage_matrix = compute_dendrogram_linkage(X, {"linkage": "ward"})
    output_path = tmp_path / "dendrogram.png"

    plot_dendrogram(linkage_matrix, output_path, "test title")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_eigengap_marks_largest_gap(tmp_path):
    eigenvalues = np.array([0.0, 0.01, 0.02, 0.5, 0.6, 0.7])
    output_path = tmp_path / "eigengap_plot.png"

    plot_eigengap(eigenvalues, output_path, "test title")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_eigengap_raises_on_fewer_than_two_eigenvalues(tmp_path):
    with pytest.raises(ValueError, match="at least 2 eigenvalues"):
        plot_eigengap(np.array([0.0]), tmp_path / "out.png", "title")


def _three_blobs_2d():
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.3, size=(15, 2)),
            rng.normal(loc=[5, 5], scale=0.3, size=(15, 2)),
            rng.normal(loc=[0, 5], scale=0.3, size=(15, 2)),
        ]
    )


def test_plot_silhouette_analysis_writes_file(tmp_path):
    from src.analysis.clustering_tuning import compute_silhouette_samples

    X_2d = _three_blobs_2d()
    cluster_labels = np.array([0] * 15 + [1] * 15 + [2] * 15)
    sample_labels, sample_values = compute_silhouette_samples(X_2d, cluster_labels)
    output_path = tmp_path / "silhouette_plot.png"

    plot_silhouette_analysis(sample_labels, sample_values, X_2d, cluster_labels, output_path, "x", "y", "test title")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_silhouette_analysis_handles_noise_in_display_labels_only(tmp_path):
    from src.analysis.clustering_tuning import compute_silhouette_samples

    X_2d = _three_blobs_2d()
    display_labels = np.array([0] * 15 + [1] * 15 + [-1] * 15)
    sample_labels, sample_values = compute_silhouette_samples(X_2d, display_labels)
    output_path = tmp_path / "silhouette_plot.png"

    plot_silhouette_analysis(sample_labels, sample_values, X_2d, display_labels, output_path, "x", "y", "test title")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_silhouette_analysis_raises_on_fewer_than_two_columns(tmp_path):
    sample_labels = np.array([0, 0, 1, 1])
    sample_values = np.array([0.5, 0.6, 0.4, 0.3])
    X_1d = np.array([[0.0], [1.0], [2.0], [3.0]])

    with pytest.raises(ValueError, match="at least 2 columns"):
        plot_silhouette_analysis(sample_labels, sample_values, X_1d, sample_labels, tmp_path / "out.png", "x", "y", "title")


def _small_embeddings(n=8, seed=0):
    rng = np.random.default_rng(seed)
    return rng.random((n, 2)) * 10


def test_plot_embedding_grid_blocks_unico_writes_file(tmp_path):
    blocks = [
        ("n_neighbors", [("5", _small_embeddings()), ("10", _small_embeddings(seed=1))]),
        ("min_dist", [("0.0", _small_embeddings(seed=2)), ("0.2", _small_embeddings(seed=3))]),
    ]
    output_path = tmp_path / "embeddings_grid_unico.png"

    plot_embedding_grid_blocks(blocks, output_path, "dim 1", "dim 2", "test suptitle")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_grid_blocks_categorical_writes_file(tmp_path):
    blocks = [("n_neighbors", [("5", _small_embeddings(n=6)), ("10", _small_embeddings(n=6, seed=1))])]
    color_values = np.array(["UNIPD/WashU"] * 3 + ["UKLFR/stroke_UKLFR"] * 3)
    output_path = tmp_path / "embeddings_grid_dataset.png"

    plot_embedding_grid_blocks(
        blocks, output_path, "dim 1", "dim 2", "test suptitle", color_values=color_values, color_kind="categorical", legend_title="dataset"
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_grid_blocks_continuous_writes_file(tmp_path):
    blocks = [("n_neighbors", [("5", _small_embeddings(n=6)), ("10", _small_embeddings(n=6, seed=1))])]
    color_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    output_path = tmp_path / "embeddings_grid_volume.png"

    plot_embedding_grid_blocks(
        blocks, output_path, "dim 1", "dim 2", "test suptitle", color_values=color_values, color_kind="continuous", legend_title="volume"
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_grid_blocks_continuous_draws_one_shared_colorbar(tmp_path, monkeypatch):
    """Regression test: the continuous branch used to scatter-plot with c=color_values
    but never call fig.colorbar - the figure had no legend/colorbar at all, unlike the
    categorical branch (found by inspecting a real embeddings_grid_volume.png)."""
    import matplotlib.figure

    calls = []
    original_colorbar = matplotlib.figure.Figure.colorbar

    def _spy_colorbar(self, mappable, *args, **kwargs):
        calls.append(kwargs)
        return original_colorbar(self, mappable, *args, **kwargs)

    monkeypatch.setattr(matplotlib.figure.Figure, "colorbar", _spy_colorbar)

    blocks = [
        ("n_neighbors", [("5", _small_embeddings(n=6)), ("10", _small_embeddings(n=6, seed=1))]),
        ("min_dist", [("0.0", _small_embeddings(n=6, seed=2)), ("0.2", _small_embeddings(n=6, seed=3))]),
    ]
    color_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    output_path = tmp_path / "embeddings_grid_volume.png"

    plot_embedding_grid_blocks(
        blocks, output_path, "dim 1", "dim 2", "test suptitle",
        color_values=color_values, color_kind="continuous", legend_title="Lesion volume (voxels)",
    )

    assert len(calls) == 1
    assert calls[0]["label"] == "Lesion volume (voxels)"


def test_plot_embedding_grid_blocks_continuous_nan_draws_missing_legend(tmp_path):
    """Regression test: the continuous branch never NaN-checked color_values at all
    (unlike plot_embedding_continuous's gray/legend treatment) - a subject with a
    missing NIHSS would be scattered with an unmapped NaN color (matplotlib's own
    default: fully transparent, invisible, no legend entry)."""
    blocks = [("n_neighbors", [("5", _small_embeddings(n=6)), ("10", _small_embeddings(n=6, seed=1))])]
    color_values = np.array([1.0, np.nan, 3.0, 4.0, np.nan, 6.0])
    output_path = tmp_path / "embeddings_grid_nihss.png"

    plot_embedding_grid_blocks(
        blocks, output_path, "dim 1", "dim 2", "test suptitle",
        color_values=color_values, color_kind="continuous", legend_title="NIHSS (severity)",
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_grid_blocks_log_scale_uses_lognorm(tmp_path):
    blocks = [("n_neighbors", [("5", _small_embeddings(n=6)), ("10", _small_embeddings(n=6, seed=1))])]
    color_values = np.array([1.0, 10.0, 100.0, 1000.0, 10000.0, 40000.0])
    output_path = tmp_path / "embeddings_grid_volume.png"

    plot_embedding_grid_blocks(
        blocks, output_path, "dim 1", "dim 2", "test suptitle",
        color_values=color_values, color_kind="continuous", legend_title="Lesion volume (voxels)", log_scale=True,
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_embedding_grid_blocks_log_scale_rejects_non_positive_value(tmp_path):
    blocks = [("n_neighbors", [("5", _small_embeddings(n=6)), ("10", _small_embeddings(n=6, seed=1))])]
    color_values = np.array([0.0, 10.0, 100.0, 1000.0, 10000.0, 40000.0])

    with pytest.raises(ValueError, match="log_scale=True needs every non-missing value > 0"):
        plot_embedding_grid_blocks(
            blocks, tmp_path / "out.png", "dim 1", "dim 2", "test suptitle",
            color_values=color_values, color_kind="continuous", legend_title="volume", log_scale=True,
        )


def test_plot_embedding_grid_blocks_single_free_param_one_block(tmp_path):
    blocks = [("perplexity", [("5", _small_embeddings()), ("10", _small_embeddings(seed=1)), ("30", _small_embeddings(seed=2))])]
    output_path = tmp_path / "embeddings_grid_unico.png"

    plot_embedding_grid_blocks(blocks, output_path, "dim 1", "dim 2", "test suptitle")

    assert output_path.exists()


def test_plot_embedding_grid_blocks_empty_raises(tmp_path):
    with pytest.raises(ValueError, match="at least one block"):
        plot_embedding_grid_blocks([], tmp_path / "out.png", "x", "y", "title")


def test_plot_embedding_grid_blocks_invalid_color_kind_raises(tmp_path):
    blocks = [("n_neighbors", [("5", _small_embeddings())])]
    with pytest.raises(ValueError, match="color_kind must be"):
        plot_embedding_grid_blocks(
            blocks, tmp_path / "out.png", "x", "y", "title", color_values=np.array([1, 2]), color_kind="bogus"
        )
