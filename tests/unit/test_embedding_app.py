"""Unit tests for src/analysis/embedding_app.py."""

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from dash import dcc, html

from src.analysis.embedding_app import (
    COLOR_MODE_ORDER,
    NEUTRAL_MODE,
    NO_METRIC,
    NO_N_COMPONENTS,
    PRODUCTION_PIPELINES,
    LesionViewerConfig,
    ProductionRun,
    UndisplayableRunError,
    _FONT_STACK,
    _n_components_option_label,
    build_app,
    build_embedding_figure,
    cluster_options,
    discover_production_runs,
    graph_content_for,
    lesion_viewer_content_for,
    load_run,
    method_options,
    metric_options,
    modality_options,
    n_components_options,
    overlap_map_content_for,
    pipeline_options,
    run_metadata,
    run_params,
    run_reduction_axis,
    run_title,
    runs_for,
    runs_matching,
    tag_param_options,
)
from src.utils.artifacts import save_matrix

_LESION_AFFINE = np.eye(4) * 2
_LESION_AFFINE[3, 3] = 1
_LESION_SHAPE = (10, 10, 10)
_LESION_GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"


def _make_lesion_subject(data_root, dataset, subject_id, lesion_voxels):
    """Pipeline-first layout matching _LESION_GLOB - same fixture shape as
    tests/unit/test_anatomical_maps.py::_make_lesion_subject."""
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_LESION_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _LESION_AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _lesion_cfg(data_root):
    reference_img = nib.Nifti1Image(np.zeros(_LESION_SHAPE, dtype=np.float32), _LESION_AFFINE)
    return LesionViewerConfig(
        data_root=data_root, lesion_glob=_LESION_GLOB, reference_img=reference_img,
        binarize_threshold=0.5, resample_interpolation="nearest",
    )


def _clustering_params_file(tmp_path, methods=("kmeans",)):
    """A minimal params_clustering.json-shaped registry (src.analysis.params.load_tag_params)
    for the "Parametri" picker step - only "kmeans" registered by default (n_clusters), since
    that's the only clustering method these fixtures ever use."""
    registry = {method: {"tag_param": ["n_clusters"]} for method in methods}
    path = tmp_path / "params_clustering.json"
    path.write_text(json.dumps(registry))
    return path


def _make_run_dir(
    results_root,
    modality="lesion",
    pipeline="dim_reduction",
    method="umap",
    reduction_method=None,
    run_name="10-08_s1",
    n_dims=2,
    params=None,
    extra_metadata=None,
    reduction_metric="euclidean",
    reduction_n_components=2,
):
    # clustering.py's own production tree has one extra <reduction_method> segment
    # (31-08-26) that dim_reduction.py's doesn't - default it here so every existing
    # pipeline="clustering" call site keeps working without having to name it explicitly.
    if pipeline == "clustering" and reduction_method is None:
        reduction_method = "umap"
    run_dir = results_root / modality / pipeline / "production" / method
    if reduction_method is not None:
        run_dir = run_dir / reduction_method
    run_dir = run_dir / run_name
    X = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]])[:, :n_dims] if n_dims <= 2 else np.hstack(
        [np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5], [3.0, 2.0]]), np.zeros((4, n_dims - 2))]
    )
    metadata = pd.DataFrame(
        {
            "subject_id": ["sub-1", "sub-2", "sub-3", "sub-4"],
            "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR", "UKLFR/stroke_UKLFR"],
            "lesion_side": ["left", "right", "left", "right"],
            "lesion_volume_voxels": [100, 200, 50, 400],
            "nihss": [4.0, np.nan, 7.0, 2.0],
        }
    )
    if extra_metadata:
        for column, values in extra_metadata.items():
            metadata[column] = values
    if params is None:
        params = {"n_components": n_dims, "metric": "euclidean"}
    # "## Config" fenced json block (src.utils.artifacts.read_run_config) - only actually read
    # by run_reduction_axis for a pipeline="clustering" run (a dim_reduction run's own axis
    # comes from "Params used:" instead, see run_reduction_axis's docstring), but written
    # unconditionally so every _make_run_dir call produces a real config.md shape, not one that
    # only happens to work for the specific axis a given test reads.
    config_block = {
        "reduction_method": reduction_method or "umap",
        "reduction_n_components": str(reduction_n_components),
        "reduction_metric": reduction_metric,
    }
    readme_lines = [
        "# test run", "", "## Config", "```json", json.dumps(config_block), "```", "",
        f"Params used: {json.dumps(params)}",
    ]
    save_matrix(run_dir, X, metadata, readme_lines=readme_lines, overwrite=False)
    return run_dir


def test_discover_production_runs_finds_valid_runs_only(tmp_path):
    results_root = tmp_path / "results"
    _make_run_dir(results_root, modality="lesion", method="umap", run_name="run-a")
    _make_run_dir(results_root, modality="lesion", method="pca", run_name="run-b")
    # Not a valid run (no manifest.json) - a stray directory left by something else, must
    # not be picked up.
    (results_root / "lesion" / "dim_reduction" / "production" / "umap" / "not-a-run").mkdir(parents=True)

    runs = discover_production_runs(results_root)

    assert [(r.modality, r.pipeline, r.method, r.run_name) for r in runs] == [
        ("lesion", "dim_reduction", "pca", "run-b"),
        ("lesion", "dim_reduction", "umap", "run-a"),
    ]


def test_discover_production_runs_missing_root_returns_empty_list(tmp_path):
    assert discover_production_runs(tmp_path / "does_not_exist") == []


def test_discover_production_runs_ignores_tuning_branch(tmp_path):
    results_root = tmp_path / "results"
    tuning_dir = results_root / "lesion" / "dim_reduction" / "tuning" / "umap" / "10-08_s1"
    tuning_dir.mkdir(parents=True)
    (tuning_dir / "manifest.json").write_text("{}")

    assert discover_production_runs(results_root) == []


def test_discover_production_runs_finds_clustering_runs_too(tmp_path):
    results_root = tmp_path / "results"
    _make_run_dir(results_root, pipeline="dim_reduction", method="umap", run_name="run-a")
    _make_run_dir(
        results_root,
        pipeline="clustering",
        method="kmeans",
        run_name="run-b",
        params={"n_clusters": 3},
        extra_metadata={"cluster_label": [0, 1, 0, -1]},
    )

    runs = discover_production_runs(results_root)

    # Alphabetical by (modality, pipeline, method, reduction_method, run_name) - same plain
    # sort every other discovery/options helper in this module uses; "clustering" <
    # "dim_reduction". Clustering's own reduction_method defaults to "umap" in
    # _make_run_dir (31-08-26 extra path segment); dim_reduction has none (None).
    assert [(r.modality, r.pipeline, r.method, r.reduction_method, r.run_name) for r in runs] == [
        ("lesion", "clustering", "kmeans", "umap", "run-b"),
        ("lesion", "dim_reduction", "umap", None, "run-a"),
    ]


def test_discover_production_runs_excludes_clustering_comparison_dir(tmp_path):
    # clustering.py's old comparison/ writer (generation removed 01-09-26, docs/dev/models.md)
    # only ever wrote a config.md, never a manifest.json - a leftover directory from before that
    # date must be excluded by the same existence check every other incomplete directory fails,
    # not by a special-cased directory-name check.
    results_root = tmp_path / "results"
    _make_run_dir(results_root, pipeline="clustering", method="kmeans", run_name="run-a")
    comparison_dir = results_root / "lesion" / "clustering" / "production" / "comparison" / "umap" / "10-08_s1"
    comparison_dir.mkdir(parents=True)
    (comparison_dir / "config.md").write_text("# comparison\n")

    runs = discover_production_runs(results_root)

    assert [(r.method, r.run_name) for r in runs] == [("kmeans", "run-a")]


def test_production_run_properties():
    run = ProductionRun(modality="lesion", pipeline="dim_reduction", method="umap", run_name="13-08_s1.1_nc3_m_dice", path=None)

    assert run.key == "lesion/dim_reduction/umap/13-08_s1.1_nc3_m_dice"
    assert run.results_relative_path == Path("results/lesion/dim_reduction/production/umap/13-08_s1.1_nc3_m_dice")


def test_production_run_properties_clustering_pipeline():
    run = ProductionRun(
        modality="lesion", pipeline="clustering", method="kmeans", run_name="10-08_s1", path=None, reduction_method="umap"
    )

    assert run.key == "lesion/clustering/kmeans/umap/10-08_s1"
    assert run.results_relative_path == Path("results/lesion/clustering/production/kmeans/umap/10-08_s1")


def test_production_run_properties_clustering_pipeline_reduction_method_none():
    """reduction_method absent (e.g. a hand-built ProductionRun in older test code, or a
    theoretical clustering run indexed before this field existed) falls back to the flat,
    no-extra-segment shape - same as a dim_reduction run, never a crash or a spurious
    'None' path component."""
    run = ProductionRun(modality="lesion", pipeline="clustering", method="kmeans", run_name="10-08_s1", path=None)

    assert run.key == "lesion/clustering/kmeans/10-08_s1"
    assert run.results_relative_path == Path("results/lesion/clustering/production/kmeans/10-08_s1")


def test_run_title_matches_production_title_format():
    run = ProductionRun(modality="lesion", pipeline="dim_reduction", method="umap", run_name="run-a", path=None)

    assert run_title(run, NEUTRAL_MODE) == "Lesions - Umap"
    assert run_title(run, "dataset") == "Lesions - Umap - dataset"


def test_load_run_2d_and_3d_succeed(tmp_path):
    results_root = tmp_path / "results"
    run_dir_2d = _make_run_dir(results_root, run_name="run-2d", n_dims=2)
    run_dir_3d = _make_run_dir(results_root, run_name="run-3d", n_dims=3)

    embedding_2d, metadata_2d = load_run(ProductionRun("lesion", "dim_reduction", "umap", "run-2d", run_dir_2d))
    embedding_3d, metadata_3d = load_run(ProductionRun("lesion", "dim_reduction", "umap", "run-3d", run_dir_3d))

    assert embedding_2d.shape == (4, 2)
    assert embedding_3d.shape == (4, 3)
    assert len(metadata_2d) == 4


@pytest.mark.parametrize("n_dims", [1, 4, 10])
def test_load_run_rejects_embeddings_with_wrong_dimensionality(tmp_path, n_dims):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-bad", n_dims=n_dims)

    with pytest.raises(UndisplayableRunError, match="can only display"):
        load_run(ProductionRun("lesion", "dim_reduction", "umap", "run-bad", run_dir))


def test_load_run_undisplayable_clustering_run_does_not_suggest_viz_n_components(tmp_path):
    """AUDIT_FINDINGS.md #43/#44 regression: the error message used to always say "Rerun
    dim_reduction pipeline with viz_n_components 2 or 3" regardless of which pipeline
    produced the run - clustering.py has no viz_n_components field at all (it never
    reduces dimensionality itself), so that advice is actionable only for a real
    dim_reduction.py run, never for a clustering.py one."""
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-bad", n_dims=10)

    with pytest.raises(UndisplayableRunError, match="can only display") as exc_info:
        load_run(ProductionRun("lesion", "clustering", "kmeans", "run-bad", run_dir))
    assert "viz_n_components" not in str(exc_info.value)
    assert "clustering.py does not reduce dimensionality" in str(exc_info.value)


def _embedding_and_metadata(n=4):
    embedding = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])[:n]
    metadata = pd.DataFrame(
        {
            "subject_id": [f"sub-{i}" for i in range(n)],
            "dataset": (["UNIPD/WashU", "UKLFR/stroke_UKLFR"] * n)[:n],
            "lesion_volume_voxels": [10.0, 100.0, 1000.0, 10000.0][:n],
            "nihss": [1.0, np.nan, 5.0, 9.0][:n],
            "cluster_label": [0, 1, 0, -1][:n],
        }
    )
    return embedding, metadata


def test_build_embedding_figure_neutro_2d_single_trace():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, NEUTRAL_MODE, "x", "y", "title")

    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Scatter)
    assert fig.layout.title.text == "title"


def test_build_embedding_figure_categorical_one_trace_per_category():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "dataset", "x", "y", "title")

    names = {trace.name for trace in fig.data}
    assert names == set(metadata["dataset"].unique())


def test_build_embedding_figure_cluster_label_mode_one_trace_per_cluster():
    # cluster_label is an int column, including hdbscan-style noise (-1) - rendered as just
    # another category (no special gray styling), see embedding_coloring.py's own note on why.
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "cluster_label", "x", "y", "title")

    names = {trace.name for trace in fig.data}
    assert names == {"0", "1", "-1"}


def test_build_embedding_figure_continuous_with_missing_adds_missing_trace():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "nihss", "x", "y", "title")

    names = {trace.name for trace in fig.data}
    assert "missing" in names
    assert "NIHSS (severity)" in names


def test_build_embedding_figure_all_missing_skips_empty_colored_trace():
    """AUDIT_FINDINGS.md #65 regression: the colored trace used to be added
    unconditionally - with every value NaN (e.g. "nihss" on a dataset never enriched via
    with no NIHSS recorded at all), it got x=[]/y=[] but still showed up as a ghost legend
    entry (mode.label) with no visible marker, alongside the real "missing" trace."""
    embedding, metadata = _embedding_and_metadata()
    metadata["nihss"] = np.nan

    fig = build_embedding_figure(embedding, metadata, "nihss", "x", "y", "title")

    names = [trace.name for trace in fig.data]
    assert names == ["missing"]
    assert "NIHSS (severity)" not in names


def test_build_embedding_figure_log_scale_transforms_values_and_sets_decade_ticks():
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "volume", "x", "y", "title")

    volume_trace = next(trace for trace in fig.data if trace.name == "lesion volume (voxels)")
    # log10([10, 100, 1000, 10000]) = [1, 2, 3, 4]
    assert list(volume_trace.marker.color) == pytest.approx([1.0, 2.0, 3.0, 4.0])
    assert list(volume_trace.marker.colorbar.tickvals) == pytest.approx([1.0, 2.0, 3.0, 4.0])
    assert list(volume_trace.marker.colorbar.ticktext) == ["10", "100", "1000", "10000"]


def test_build_embedding_figure_3d_uses_scatter3d_and_data_aspect():
    embedding = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])
    _, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, NEUTRAL_MODE, "x", "y", "title", zlabel="z")

    assert isinstance(fig.data[0], go.Scatter3d)
    assert fig.layout.scene.aspectmode == "data"
    assert fig.data[0].marker.opacity == 1.0
    assert fig.data[0].marker.line.color == "white"


def test_build_embedding_figure_zlabel_with_2_column_embedding_raises():
    embedding, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="not 3"):
        build_embedding_figure(embedding, metadata, NEUTRAL_MODE, "x", "y", "title", zlabel="z")


def test_build_embedding_figure_unknown_mode_raises():
    embedding, metadata = _embedding_and_metadata()

    with pytest.raises(ValueError, match="nknown color mode"):
        build_embedding_figure(embedding, metadata, "bogus", "x", "y", "title")


def test_build_embedding_figure_missing_persisted_column_raises(tmp_path, monkeypatch):
    """A colour mode whose values can't be resolved anywhere must raise, never plot blanks.

    Since 06-09-26 'nihss' falls back to the subject registry when the run's own metadata
    doesn't carry it, so the unresolvable case is now "not in the run AND not in the
    registry either". METADATA_ROOT is redirected at an empty dir so this stays a unit
    test - it must never depend on the real assets/metadata/participants.csv.
    """
    from src.utils import participants as participants_registry

    monkeypatch.setattr(participants_registry, "METADATA_ROOT", tmp_path / "empty")
    embedding, metadata = _embedding_and_metadata()
    metadata = metadata.drop(columns=["nihss"])

    with pytest.raises(FileNotFoundError, match="subject registry not found"):
        build_embedding_figure(embedding, metadata, "nihss", "x", "y", "title")


def test_build_embedding_figure_missing_run_only_column_raises():
    """'volume' has no registry counterpart (it's a property of the run's own matrix),
    so it must keep failing on the run's metadata alone."""
    embedding, metadata = _embedding_and_metadata()
    metadata = metadata.drop(columns=["lesion_volume_voxels"])

    with pytest.raises(ValueError, match="no 'lesion_volume_voxels' column"):
        build_embedding_figure(embedding, metadata, "volume", "x", "y", "title")


def test_color_mode_order_starts_with_neutro():
    assert COLOR_MODE_ORDER[0] == NEUTRAL_MODE
    assert set(COLOR_MODE_ORDER[1:]) == {"dataset", "side", "volume", "nihss", "cluster_label"}


def test_graph_content_for_valid_run_returns_graph(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-2d", n_dims=2)
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-2d", run_dir)

    content = graph_content_for(run, "dataset")

    assert isinstance(content, dcc.Graph)
    assert content.id == "embedding-graph"
    # modeBarButtons (not displayModeBar=False, 01-09-26) - a single "toImage" save affordance
    # per plot, on request - see graph_content_for's own comment for why a whitelist survives
    # 2D<->3D unchanged where a removal-list wouldn't.
    assert content.config["modeBarButtons"] == [["toImage"]]
    assert content.figure.layout.title.text == "Lesions - Umap - dataset"


def test_graph_content_for_undisplayable_run_returns_status_message(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-10d", n_dims=10)
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-10d", run_dir)

    content = graph_content_for(run, NEUTRAL_MODE)

    assert isinstance(content, html.P)
    assert "can only display" in content.children


def test_build_app_raises_on_empty_runs(tmp_path):
    with pytest.raises(ValueError, match="at least one production run"):
        build_app([], _lesion_cfg(tmp_path), _clustering_params_file(tmp_path))


def _runs(*specs):
    """specs: (modality, pipeline, method, run_name) tuples - path unused by the picker
    helpers."""
    return [ProductionRun(modality=m, pipeline=p, method=method, run_name=name, path=None) for m, p, method, name in specs]


def test_modality_options_sorted_and_distinct():
    runs = _runs(
        ("lesion", "dim_reduction", "umap", "a"),
        ("lesion", "dim_reduction", "pca", "b"),
        ("sdc", "dim_reduction", "umap", "c"),
    )

    assert modality_options(runs) == ["lesion", "sdc"]


def test_pipeline_options_dim_reduction_preferred_over_clustering():
    runs = _runs(
        ("lesion", "clustering", "kmeans", "a"),
        ("lesion", "dim_reduction", "umap", "b"),
        ("sdc", "clustering", "kmeans", "c"),
    )

    assert pipeline_options(runs, "lesion") == ["dim_reduction", "clustering"]
    assert pipeline_options(runs, "sdc") == ["clustering"]


def test_pipeline_options_subset_of_production_pipelines():
    assert set(PRODUCTION_PIPELINES) == {"dim_reduction", "clustering"}


def test_method_options_scoped_to_modality_and_pipeline():
    runs = _runs(
        ("lesion", "dim_reduction", "umap", "a"),
        ("lesion", "dim_reduction", "pca", "b"),
        ("lesion", "clustering", "kmeans", "c"),
        ("sdc", "dim_reduction", "umap", "d"),
    )

    assert method_options(runs, "lesion", "dim_reduction") == ["pca", "umap"]
    assert method_options(runs, "lesion", "clustering") == ["kmeans"]
    assert method_options(runs, "sdc", "dim_reduction") == ["umap"]


def test_runs_for_scoped_and_chronologically_ordered():
    runs = _runs(
        ("lesion", "dim_reduction", "umap", "23-07_s1.1_d00"),
        ("lesion", "dim_reduction", "umap", "13-08_s1.1_nc3_m_dice"),
        ("lesion", "dim_reduction", "umap", "11-08_s1.1_nc2_m_euclidean"),
        ("lesion", "dim_reduction", "pca", "26-07_s1.1_c2"),  # different method - excluded
        ("lesion", "clustering", "umap", "26-07_s1.1_x"),  # same method name, different pipeline - excluded
    )

    matching = runs_for(runs, "lesion", "dim_reduction", "umap")

    assert [r.run_name for r in matching] == [
        "23-07_s1.1_d00",
        "11-08_s1.1_nc2_m_euclidean",
        "13-08_s1.1_nc3_m_dice",
    ]


def test_runs_for_undated_run_name_sorts_last():
    runs = _runs(
        ("lesion", "dim_reduction", "umap", "no-date-here"),
        ("lesion", "dim_reduction", "umap", "23-07_s1.1_d00"),
    )

    matching = runs_for(runs, "lesion", "dim_reduction", "umap")

    assert [r.run_name for r in matching] == ["23-07_s1.1_d00", "no-date-here"]


def test_run_params_reads_config_md(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-a", params={"n_neighbors": 5, "metric": "dice", "n_components": 3})

    params = run_params(ProductionRun("lesion", "dim_reduction", "umap", "run-a", run_dir))

    assert params == {"n_neighbors": 5, "metric": "dice", "n_components": 3}


def test_run_params_missing_config_md_raises(tmp_path):
    run_dir = tmp_path / "empty-run"
    run_dir.mkdir()

    with pytest.raises(ValueError, match="no config.md"):
        run_params(ProductionRun("lesion", "dim_reduction", "umap", "empty-run", run_dir))


def test_run_params_config_md_without_params_line_raises(tmp_path):
    run_dir = tmp_path / "bad-run"
    run_dir.mkdir()
    (run_dir / "config.md").write_text("# just a title, no Params used line\n")

    with pytest.raises(ValueError, match="unexpected format"):
        run_params(ProductionRun("lesion", "dim_reduction", "umap", "bad-run", run_dir))


def test_metric_options_includes_no_metric_sentinel_for_methods_without_metric(tmp_path):
    results_root = tmp_path / "results"
    _make_run_dir(results_root, method="pca", run_name="run-a", params={"n_components": 150})

    assert metric_options(
        [ProductionRun("lesion", "dim_reduction", "pca", "run-a", results_root / "lesion/dim_reduction/production/pca/run-a")],
        "lesion", "dim_reduction", "pca",
    ) == [NO_METRIC]


def test_metric_options_distinct_values(tmp_path):
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(results_root, run_name="run-a", params={"metric": "euclidean", "n_components": 2})
    dir_b = _make_run_dir(results_root, run_name="run-b", params={"metric": "dice", "n_components": 2})
    runs = [
        ProductionRun("lesion", "dim_reduction", "umap", "run-a", dir_a),
        ProductionRun("lesion", "dim_reduction", "umap", "run-b", dir_b),
    ]

    assert metric_options(runs, "lesion", "dim_reduction", "umap") == ["dice", "euclidean"]


def test_metric_options_one_corrupt_run_does_not_hide_the_others(tmp_path, caplog):
    """Regression (HIGH #25, 2026-08): a single run() with a truncated config.md (a
    real-world "editor open on the results/ folder over a network mount" scenario) used
    to raise straight out of the list-comprehension, making metric_options fail for
    EVERY run of that (modality, pipeline, method), not just the corrupt one."""
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(results_root, run_name="run-a", params={"metric": "euclidean", "n_components": 2})
    dir_b = _make_run_dir(results_root, run_name="run-b", params={"metric": "dice", "n_components": 2})
    (dir_b / "config.md").write_text('# test run\nParams used: {"metric": "dice", "n_com')  # truncated mid-write
    runs = [
        ProductionRun("lesion", "dim_reduction", "umap", "run-a", dir_a),
        ProductionRun("lesion", "dim_reduction", "umap", "run-b", dir_b),
    ]

    assert metric_options(runs, "lesion", "dim_reduction", "umap") == ["euclidean"]
    assert "run-b" in caplog.text


def test_metric_options_clustering_pipeline_returns_upstream_reduction_metric(tmp_path):
    # 01-09-26: a clustering run's own "metric" axis is the *upstream embedding's* metric
    # (config.md's "## Config" reduction_metric), not a sentinel - runs.csv already shows this
    # varying across real agglomerative/gmm/... runs, so the picker must reflect it too.
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-a",
        params={"n_clusters": 3}, reduction_metric="dice",
    )
    dir_b = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-b",
        params={"n_clusters": 5}, reduction_metric="euclidean",
    )
    runs = [
        ProductionRun("lesion", "clustering", "kmeans", "run-a", dir_a, reduction_method="umap"),
        ProductionRun("lesion", "clustering", "kmeans", "run-b", dir_b, reduction_method="umap"),
    ]

    assert metric_options(runs, "lesion", "clustering", "kmeans") == ["dice", "euclidean"]


def test_n_components_options_scoped_to_metric(tmp_path):
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(results_root, run_name="run-a", params={"metric": "euclidean", "n_components": 2})
    dir_b = _make_run_dir(results_root, run_name="run-b", params={"metric": "euclidean", "n_components": 3})
    dir_c = _make_run_dir(results_root, run_name="run-c", params={"metric": "dice", "n_components": 10})
    runs = [
        ProductionRun("lesion", "dim_reduction", "umap", "run-a", dir_a),
        ProductionRun("lesion", "dim_reduction", "umap", "run-b", dir_b),
        ProductionRun("lesion", "dim_reduction", "umap", "run-c", dir_c),
    ]

    assert n_components_options(runs, "lesion", "dim_reduction", "umap", "euclidean") == [2, 3]
    assert n_components_options(runs, "lesion", "dim_reduction", "umap", "dice") == [10]


def test_n_components_options_clustering_pipeline_returns_upstream_reduction_n_components(tmp_path):
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-a",
        params={"n_clusters": 3}, reduction_metric="euclidean", reduction_n_components=2,
    )
    dir_b = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-b",
        params={"n_clusters": 5}, reduction_metric="euclidean", reduction_n_components=3,
    )
    runs = [
        ProductionRun("lesion", "clustering", "kmeans", "run-a", dir_a, reduction_method="umap"),
        ProductionRun("lesion", "clustering", "kmeans", "run-b", dir_b, reduction_method="umap"),
    ]

    assert n_components_options(runs, "lesion", "clustering", "kmeans", "euclidean") == [2, 3]


def test_n_components_options_clustering_pipeline_raw_reduction_returns_sentinel(tmp_path):
    """A clustering run built directly on un-reduced data (reduction_method="raw") has no
    upstream embedding at all - config.md then records reduction_metric/reduction_n_components
    as "" (clustering.py::_reduction_extra_columns), which must resolve to the same
    NO_METRIC/NO_N_COMPONENTS sentinel a pca/pacmap dim_reduction run gets, not "" itself."""
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-a",
        reduction_method="raw", params={"n_clusters": 3}, reduction_metric="", reduction_n_components="",
    )
    runs = [ProductionRun("lesion", "clustering", "kmeans", "run-a", dir_a, reduction_method="raw")]

    assert metric_options(runs, "lesion", "clustering", "kmeans") == [NO_METRIC]
    assert n_components_options(runs, "lesion", "clustering", "kmeans", NO_METRIC) == [NO_N_COMPONENTS]


def test_n_components_option_label_maps_sentinel_to_readable_placeholder():
    """AUDIT_FINDINGS.md #64 regression: NO_N_COMPONENTS (-1) used to be labeled str(-1) -
    the literal string "-1" would show up as a dropdown option in the "Componenti" picker
    for any clustering.py run, instead of a readable placeholder like NO_METRIC already has
    for the analogous metric-picker case."""
    assert _n_components_option_label(NO_N_COMPONENTS) == NO_METRIC
    assert _n_components_option_label(2) == "2"
    assert _n_components_option_label(10) == "10"


def test_runs_matching_scoped_to_metric_and_n_components(tmp_path):
    results_root = tmp_path / "results"
    dir_a = _make_run_dir(results_root, run_name="11-08_run-a", params={"metric": "euclidean", "n_components": 2})
    dir_b = _make_run_dir(results_root, run_name="11-08_run-b", params={"metric": "dice", "n_components": 2})
    dir_c = _make_run_dir(results_root, run_name="13-08_run-c", params={"metric": "euclidean", "n_components": 3})
    runs = [
        ProductionRun("lesion", "dim_reduction", "umap", "11-08_run-a", dir_a),
        ProductionRun("lesion", "dim_reduction", "umap", "11-08_run-b", dir_b),
        ProductionRun("lesion", "dim_reduction", "umap", "13-08_run-c", dir_c),
    ]

    matching = runs_matching(runs, "lesion", "dim_reduction", "umap", "euclidean", 2, NO_METRIC, _clustering_params_file(tmp_path))

    assert [r.run_name for r in matching] == ["11-08_run-a"]


def test_runs_matching_clustering_pipeline_scoped_to_reduction_axis_and_tag_params(tmp_path):
    # 01-09-26: real clustering runs vary along 2 independent axes - which embedding they were
    # built from (metric/n_components) and the method's own tag_params (n_clusters here) - both
    # must narrow the "Run" step, not just be ignored the way this used to work.
    results_root = tmp_path / "results"
    params_file = _clustering_params_file(tmp_path)
    dir_a = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="10-08_run-a",
        params={"n_clusters": 3}, reduction_metric="euclidean", reduction_n_components=2,
    )
    dir_b = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="11-08_run-b",
        params={"n_clusters": 5}, reduction_metric="euclidean", reduction_n_components=2,
    )
    dir_c = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="12-08_run-c",
        params={"n_clusters": 3}, reduction_metric="dice", reduction_n_components=2,
    )
    runs = [
        ProductionRun("lesion", "clustering", "kmeans", "10-08_run-a", dir_a, reduction_method="umap"),
        ProductionRun("lesion", "clustering", "kmeans", "11-08_run-b", dir_b, reduction_method="umap"),
        ProductionRun("lesion", "clustering", "kmeans", "12-08_run-c", dir_c, reduction_method="umap"),
    ]

    # Same (metric, n_components) as run-a and run-b, but only run-a's own n_clusters=3.
    matching = runs_matching(runs, "lesion", "clustering", "kmeans", "euclidean", 2, "n_clusters=3", params_file)
    assert [r.run_name for r in matching] == ["10-08_run-a"]

    # A different upstream embedding (dice) excludes run-a/run-b entirely, regardless of tag_params.
    matching_dice = runs_matching(runs, "lesion", "clustering", "kmeans", "dice", 2, "n_clusters=3", params_file)
    assert [r.run_name for r in matching_dice] == ["12-08_run-c"]


def test_build_app_layout_has_one_button_per_color_mode(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-2d", n_dims=2)
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-2d", run_dir)

    app = build_app([run], _lesion_cfg(tmp_path), _clustering_params_file(tmp_path))

    # .controls' children: [picker-row-1 (Dato/Pipeline/Metodo), picker-row-2
    # (Metrica/Componenti/Run), color-buttons] - color-buttons is the last one, not a fixed
    # index, so this doesn't silently break the next time a row is added/reordered.
    controls_children = app.layout.children[2].children
    color_buttons_div = controls_children[-1]
    assert len(color_buttons_div.children) == len(COLOR_MODE_ORDER)
    assert color_buttons_div.children[0].className == "active"  # neutro selected by default


def test_run_metadata_reads_metadata_csv_regardless_of_dimensionality(tmp_path):
    """Unlike load_run, run_metadata never raises UndisplayableRunError - a run with e.g.
    n_components=10 still exposes its metadata columns to the anatomy panels."""
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-10d", n_dims=10)
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-10d", run_dir)

    metadata = run_metadata(run)

    assert list(metadata["subject_id"]) == ["sub-1", "sub-2", "sub-3", "sub-4"]


def test_cluster_options_sorted_unique_including_hdbscan_noise():
    metadata = pd.DataFrame({"cluster_label": [1, 0, -1, 1, 0]})
    assert cluster_options(metadata) == [-1, 0, 1]


def test_lesion_viewer_content_for_unresolvable_subject_returns_status_message(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-a")
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-a", run_dir)
    metadata = run_metadata(run)

    content = lesion_viewer_content_for(run, "sub-does-not-exist", metadata, _lesion_cfg(tmp_path))

    assert isinstance(content, html.P)
    assert "sub-does-not-exist" in content.children


def test_lesion_viewer_content_for_valid_subject_returns_iframe(tmp_path):
    # subject_id must match the project's real ST/HC/... naming convention
    # (src.retrieval.dataset._SUBJECT_RE, enforced unconditionally by discover_files_by_subject
    # - lessons_learned.md #28) - "sub-1" (this file's other, unrelated fixtures) would raise.
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-a", extra_metadata={"subject_id": ["sub-STUNIPD0001", "sub-2", "sub-3", "sub-4"]})
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-a", run_dir)
    metadata = run_metadata(run)

    content = lesion_viewer_content_for(run, "sub-STUNIPD0001", metadata, _lesion_cfg(data_root))

    # The subject heading is our own HTML (H3), not nilearn's own canvas-drawn title (01-09-26 -
    # nilearn draws that straight onto a <canvas> with no width check/wrapping, silently
    # overflowing for anything longer than a few characters) - complete and never truncated.
    assert isinstance(content, html.Div)
    heading, _caption, viewer_wrap = content.children
    assert heading.children == "sub-STUNIPD0001 (UNIPD/WashU)"
    iframe = viewer_wrap.children
    assert isinstance(iframe, html.Iframe)
    # nilearn's own "Opacity" label/slider is the only ordinary (CSS-reachable) text in its
    # page - font-family injected via _style_nilearn_html, verified here rather than trusted.
    assert _FONT_STACK in iframe.srcDoc


def test_overlap_map_content_for_empty_cluster_returns_status_message(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, pipeline="clustering", run_name="run-a", extra_metadata={"cluster_label": [0, 0, 1, 1]})
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    content = overlap_map_content_for(run, metadata, 99, _lesion_cfg(tmp_path))

    assert isinstance(content, html.P)
    assert "99" in content.children


def test_overlap_map_content_for_valid_cluster_returns_iframe(tmp_path):
    # Real site-prefixed subject_ids (see the sibling lesion-viewer test above for why).
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", subject_ids[0], [(1, 1, 1)])
    _make_lesion_subject(data_root, "UNIPD/WashU", subject_ids[1], [(1, 1, 1)])
    _make_lesion_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], [(2, 2, 2)])
    _make_lesion_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], [(2, 2, 2)])
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    content = overlap_map_content_for(run, metadata, 0, _lesion_cfg(data_root))

    assert isinstance(content, html.Div)
    heading, caption, viewer_wrap = content.children
    assert heading.children == "Cluster 0 (n=2)"
    assert "%" in caption.children
    assert isinstance(viewer_wrap.children, html.Iframe)


def test_run_reduction_axis_dim_reduction_reads_own_params(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-a", params={"metric": "dice", "n_components": 3})
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-a", run_dir)

    assert run_reduction_axis(run) == ("dice", 3)


def test_run_reduction_axis_clustering_reads_upstream_embedding(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-a",
        params={"n_clusters": 4}, reduction_metric="dice", reduction_n_components=3,
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")

    assert run_reduction_axis(run) == ("dice", 3)


def test_tag_param_options_returns_sentinel_for_dim_reduction(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, run_name="run-a")
    runs = [ProductionRun("lesion", "dim_reduction", "umap", "run-a", run_dir)]

    labels = tag_param_options(runs, "lesion", "dim_reduction", "umap", "euclidean", 2, _clustering_params_file(tmp_path))

    assert labels == [NO_METRIC]


def test_tag_param_options_distinct_combinations_for_clustering(tmp_path):
    results_root = tmp_path / "results"
    params_file = _clustering_params_file(tmp_path)
    dir_a = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-a",
        params={"n_clusters": 3}, reduction_metric="euclidean", reduction_n_components=2,
    )
    dir_b = _make_run_dir(
        results_root, pipeline="clustering", method="kmeans", run_name="run-b",
        params={"n_clusters": 5}, reduction_metric="euclidean", reduction_n_components=2,
    )
    runs = [
        ProductionRun("lesion", "clustering", "kmeans", "run-a", dir_a, reduction_method="umap"),
        ProductionRun("lesion", "clustering", "kmeans", "run-b", dir_b, reduction_method="umap"),
    ]

    labels = tag_param_options(runs, "lesion", "clustering", "kmeans", "euclidean", 2, params_file)

    assert labels == ["n_clusters=3", "n_clusters=5"]
