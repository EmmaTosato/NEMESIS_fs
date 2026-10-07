"""Unit tests for src/analysis/embedding_app.py."""

import json
import logging
import threading
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from dash import dcc, html

from src.analysis.embedding_app import DISCONNECTION_PROBABILITY_THRESHOLD
from src.analysis.embedding_coloring import DEFAULT_GRID, available_grids
from src.analysis.embedding_app import (
    COLOR_MODE_ORDER,
    NEUTRAL_MODE,
    NO_METRIC,
    NO_N_COMPONENTS,
    PRODUCTION_PIPELINES,
    LesionViewerConfig,
    ProductionRun,
    SdcViewerConfig,
    UndisplayableRunError,
    _FONT_STACK,
    _build_cluster_disconnection_view,
    _build_cluster_overlap_view,
    _n_components_option_label,
    _static_glass_brain_png_bytes,
    _static_png_bytes,
    build_app,
    build_embedding_figure,
    cluster_centroids_with_nearest_subject,
    cluster_description_content_for,
    cluster_options,
    disconnectome_viewer_content_for,
    disconnection_map_content_for,
    discover_production_runs,
    color_mode_description,
    graph_content_for,
    lesion_viewer_content_for,
    load_run,
    method_options,
    metric_options,
    modality_options,
    n_components_options,
    overlap_map_content_for,
    pipeline_options,
    representative_subject_content_for,
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


_DISCONNECTOME_GLOB = "sdc/*/*_res-1_desc-disconnectome.nii.gz"


def _sdc_cfg(data_root):
    reference_img = nib.Nifti1Image(np.zeros(_LESION_SHAPE, dtype=np.float32), _LESION_AFFINE)
    return SdcViewerConfig(
        data_root=data_root, disconnectome_glob=_DISCONNECTOME_GLOB, reference_img=reference_img,
        resample_interpolation="nearest",
    )


def _make_disconnectome_subject(data_root, dataset, subject_id, voxel_values):
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_LESION_SHAPE, dtype=np.float32)
    for voxel, value in voxel_values.items():
        volume[voxel] = value
    nib.save(nib.Nifti1Image(volume, _LESION_AFFINE), subject_dir / f"{subject_id}_res-1_desc-disconnectome.nii.gz")


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


def _registry_for_embedding_fixture(metadata_root, n=4):
    """Registry rows matching _embedding_and_metadata's own subjects (30-09-26): side/nihss/
    volume all resolve from participants.csv now, so a figure test for one of those modes has
    to supply the registry, not just the run's metadata."""
    metadata_root.mkdir(parents=True, exist_ok=True)
    header = [*_PARTICIPANTS_REGISTRY_COLUMNS, "lesion_side", "NIHSS", "lesion_volume_voxels_2mm"]
    volumes = ["10", "100", "1000", "10000"][:n]
    nihss = ["1.0", "", "5.0", "9.0"][:n]
    sides = ["left", "right", "left", "right"][:n]
    rows = [
        [f"sub-{i}", f"sub-{i}", "UNIPD/WashU", "ST", "True", "True", "False", sides[i], nihss[i], volumes[i]]
        for i in range(n)
    ]
    (metadata_root / "participants.csv").write_text(
        "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"
    )


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


def _registry_with_location(metadata_root, locations):
    metadata_root.mkdir(parents=True, exist_ok=True)
    header = [*_PARTICIPANTS_REGISTRY_COLUMNS, "location_dominant_2mm"]
    rows = [
        [f"sub-{i}", f"sub-{i}", "UNIPD/WashU", "ST", "True", "True", "False", location]
        for i, location in enumerate(locations)
    ]
    (metadata_root / "participants.csv").write_text(
        "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"
    )


def test_build_embedding_figure_location_mode_is_in_vocabulary_order_with_stable_colours(tmp_path, monkeypatch):
    """One trace per location present, in the vocabulary's order (not alphabetical); and the same
    label has the same colour whether or not another label is in the plot - the reason the mode
    declares a closed vocabulary."""
    from src.utils import participants as participants_registry

    monkeypatch.setattr(participants_registry, "METADATA_ROOT", tmp_path / "metadata")
    embedding, metadata = _embedding_and_metadata()

    _registry_with_location(
        tmp_path / "metadata", ["white_matter_only", "cortex_white_boundary", "cortex_only", ""]
    )
    full = build_embedding_figure(embedding, metadata, "location", "x", "y", "title")
    _registry_with_location(
        tmp_path / "metadata", ["white_matter_only", "cortex_only", "cortex_only", "white_matter_only"]
    )
    without_boundary = build_embedding_figure(embedding, metadata, "location", "x", "y", "title")

    assert [trace.name for trace in full.data] == [
        "cortex_only", "cortex_white_boundary", "white_matter_only", "unknown"
    ]
    colour = lambda fig: {trace.name: trace.marker.color for trace in fig.data}
    assert colour(full)["white_matter_only"] == colour(without_boundary)["white_matter_only"]
    assert colour(full)["cortex_only"] == colour(without_boundary)["cortex_only"]
    assert colour(full)["unknown"] == "#9e9d98"


def test_build_embedding_figure_cluster_label_mode_one_trace_per_cluster():
    # cluster_label is an int column, including hdbscan-style noise (-1) - rendered as just
    # another category (no special gray styling), see embedding_coloring.py's own note on why.
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "cluster_label", "x", "y", "title")

    names = {trace.name for trace in fig.data}
    assert names == {"0", "1", "-1"}


def test_build_embedding_figure_continuous_with_missing_adds_missing_trace(_participants_registry_root):
    embedding, metadata = _embedding_and_metadata()
    _registry_for_embedding_fixture(_participants_registry_root)

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


def test_build_embedding_figure_log_scale_transforms_values_and_sets_decade_ticks(
    _participants_registry_root,
):
    embedding, metadata = _embedding_and_metadata()
    _registry_for_embedding_fixture(_participants_registry_root)

    fig = build_embedding_figure(embedding, metadata, "volume", "x", "y", "title")

    volume_trace = next(trace for trace in fig.data if trace.name == "lesion volume")
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
    """'cluster_label' has no registry counterpart (it belongs to a clustering run, nowhere
    else), so it must keep failing on the run's own metadata alone. 'volume' left this group
    on 30-09-26 - it now resolves from the registry."""
    embedding, metadata = _embedding_and_metadata()
    metadata = metadata.drop(columns=["cluster_label"])

    with pytest.raises(ValueError, match="no 'cluster_label' column"):
        build_embedding_figure(embedding, metadata, "cluster_label", "x", "y", "title")


def test_build_embedding_figure_volume_zero_is_drawn_missing_not_refused(_participants_registry_root):
    """30-09-26: a 2mm volume of 0 is legitimate (nearest-neighbour resampling of a 1mm mask
    can drop a small lesion to 0 voxels without the mask being empty, docs/dev/metadata.md).
    log10(0) has no position on the scale, so that subject is drawn as missing - refusing the
    whole plot over it made the mode unusable on real cohorts. A NEGATIVE count would still
    raise: that is corrupt data, not a legitimate value."""
    embedding, metadata = _embedding_and_metadata()
    _participants_registry_root.mkdir(parents=True, exist_ok=True)
    header = [*_PARTICIPANTS_REGISTRY_COLUMNS, "lesion_volume_voxels_2mm"]
    rows = [
        [f"sub-{i}", f"sub-{i}", "UNIPD/WashU", "ST", "True", "True", "False", v]
        for i, v in enumerate(["0", "100", "1000", "10000"])
    ]
    (_participants_registry_root / "participants.csv").write_text(
        "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"
    )

    fig = build_embedding_figure(embedding, metadata, "volume", "x", "y", "title")

    assert "missing" in {trace.name for trace in fig.data}
    volume_trace = next(t for t in fig.data if t.name == "lesion volume")
    # Ticks are built from the values actually on the scale - the 0 must not drag the lower
    # bound to log10(0) = -inf.
    assert list(volume_trace.marker.colorbar.ticktext) == ["100", "1000", "10000"]


def _registry_with_disconnection(metadata_root, loads, means, grid="2mm"):
    metadata_root.mkdir(parents=True, exist_ok=True)
    header = [*_PARTICIPANTS_REGISTRY_COLUMNS, f"disconnection_load_voxels_{grid}", f"disconnection_mean_{grid}"]
    rows = [
        [f"sub-{i}", f"sub-{i}", "UNIPD/WashU", "ST", "True", "True", "False", str(loads[i]), str(means[i])]
        for i in range(len(loads))
    ]
    (metadata_root / "participants.csv").write_text(
        "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"
    )


@pytest.mark.parametrize(
    "mode_name, label", [("disconnection_load", "disconnection load"), ("disconnection_mean", "mean disconnection")]
)
def test_build_embedding_figure_disconnection_modes_draw_a_linear_colorbar(
    _participants_registry_root, mode_name, label
):
    """Both modes plot from the registry on a LINEAR scale: the colorbar carries the mode's own
    label and real values, with no log10 tick relabelling (that is what volume does)."""
    embedding, metadata = _embedding_and_metadata()
    _registry_with_disconnection(
        _participants_registry_root, [1000, 20000, 60000, 400000], [0.0005, 0.011, 0.033, 0.22]
    )

    fig = build_embedding_figure(embedding, metadata, mode_name, "x", "y", "title")

    trace = next(t for t in fig.data if t.name == label)
    assert trace.marker.colorbar.title.text == label
    assert trace.marker.colorbar.tickvals is None  # no decade ticks: not log-scaled
    assert min(trace.marker.color) == (1000 if mode_name == "disconnection_load" else 0.0005)


@pytest.mark.parametrize("mode_name", ["disconnection_load", "disconnection_mean"])
def test_build_embedding_figure_disconnection_follows_the_selected_grid(_participants_registry_root, mode_name):
    """The grid buttons must change what is drawn: the same mode reads the 1mm column when "1mm"
    is selected and the 2mm one otherwise. A registry holding both with different values pins
    that the selection is honoured and not silently ignored."""
    embedding, metadata = _embedding_and_metadata()
    _participants_registry_root.mkdir(parents=True, exist_ok=True)
    columns = {"disconnection_load": "disconnection_load_voxels", "disconnection_mean": "disconnection_mean"}
    prefix = columns[mode_name]
    header = [*_PARTICIPANTS_REGISTRY_COLUMNS, f"{prefix}_2mm", f"{prefix}_1mm"]
    rows = [
        [f"sub-{i}", f"sub-{i}", "UNIPD/WashU", "ST", "True", "True", "False", str(10 + i), str(1000 + i)]
        for i in range(4)
    ]
    (_participants_registry_root / "participants.csv").write_text(
        "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"
    )

    default = build_embedding_figure(embedding, metadata, mode_name, "x", "y", "title")
    one_mm = build_embedding_figure(embedding, metadata, mode_name, "x", "y", "title", grid="1mm")

    def drawn(fig):
        return min(next(t for t in fig.data if t.marker.colorbar is not None and t.marker.colorbar.title.text).marker.color)

    assert drawn(default) == 10
    assert drawn(one_mm) == 1000


def test_build_embedding_figure_unknown_grid_raises(_participants_registry_root):
    embedding, metadata = _embedding_and_metadata()
    _registry_with_disconnection(_participants_registry_root, [1, 2, 3, 4], [0.1, 0.2, 0.3, 0.4])

    with pytest.raises(ValueError, match="unknown grid '3mm'"):
        build_embedding_figure(embedding, metadata, "disconnection_load", "x", "y", "title", grid="3mm")


def test_build_embedding_figure_disconnection_zero_is_a_real_value_on_the_linear_scale(_participants_registry_root):
    """A subject with no measurable disconnection has load 0. On a linear scale that is the
    bottom of the colour range, not a missing value - unlike lesion volume 0 on the log scale."""
    embedding, metadata = _embedding_and_metadata()
    _registry_with_disconnection(_participants_registry_root, [0, 20000, 60000, 400000], [0.0, 0.011, 0.033, 0.22])

    fig = build_embedding_figure(embedding, metadata, "disconnection_load", "x", "y", "title")

    assert "missing" not in {trace.name for trace in fig.data}
    trace = next(t for t in fig.data if t.name == "disconnection load")
    assert 0 in list(trace.marker.color)


@pytest.mark.parametrize("mode_name", ["disconnection_load", "disconnection_mean"])
def test_build_embedding_figure_disconnection_modes_raise_on_a_non_sdc_modality(_participants_registry_root, mode_name):
    """06-10-26, on request: a 'lesion' run's embedding is about lesion location/volume, not
    overall disconnection - the mode must refuse, not silently colour from the registry just
    because the value happens to exist there for the same subjects."""
    embedding, metadata = _embedding_and_metadata()
    _registry_with_disconnection(
        _participants_registry_root, [1000, 20000, 60000, 400000], [0.0005, 0.011, 0.033, 0.22]
    )

    with pytest.raises(ValueError, match=r"only applies to modality='sdc' runs, not 'lesion'"):
        build_embedding_figure(embedding, metadata, mode_name, "x", "y", "title", modality="lesion")


@pytest.mark.parametrize("mode_name", ["disconnection_load", "disconnection_mean"])
def test_build_embedding_figure_disconnection_modes_allowed_on_sdc_modality(_participants_registry_root, mode_name):
    embedding, metadata = _embedding_and_metadata()
    _registry_with_disconnection(
        _participants_registry_root, [1000, 20000, 60000, 400000], [0.0005, 0.011, 0.033, 0.22]
    )

    fig = build_embedding_figure(embedding, metadata, mode_name, "x", "y", "title", modality="sdc")

    assert len(fig.data) > 0


def test_build_embedding_figure_disconnection_modes_unrestricted_when_modality_not_given(_participants_registry_root):
    """modality=None (the default) is for callers with no modality concept of their own
    (plot_tuning_embedding_3d.py) - the restriction only engages when a caller actually states
    a modality that conflicts."""
    embedding, metadata = _embedding_and_metadata()
    _registry_with_disconnection(
        _participants_registry_root, [1000, 20000, 60000, 400000], [0.0005, 0.011, 0.033, 0.22]
    )

    fig = build_embedding_figure(embedding, metadata, "disconnection_load", "x", "y", "title")

    assert len(fig.data) > 0


def test_build_embedding_figure_volume_mode_is_not_restricted_by_modality(_participants_registry_root):
    """Unchanged behaviour for every pre-existing registry mode (dataset/side/volume/nihss):
    only disconnection_load/disconnection_mean declare a restricted_to_modality."""
    _registry_for_embedding_fixture(_participants_registry_root)
    embedding, metadata = _embedding_and_metadata()

    fig = build_embedding_figure(embedding, metadata, "volume", "x", "y", "title", modality="sdc")

    assert len(fig.data) > 0


def test_color_mode_order_starts_with_neutro():
    assert COLOR_MODE_ORDER[0] == NEUTRAL_MODE
    assert set(COLOR_MODE_ORDER[1:]) == {
        "dataset", "side", "location", "volume", "disconnection_load", "disconnection_mean", "nihss",
        "cluster_label",
    }


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


def test_graph_content_for_disconnection_mode_on_a_lesion_run_returns_status_message(tmp_path):
    """End-to-end through graph_content_for (not just build_embedding_figure directly): a
    'lesion'-modality run asking for 'disconnection_load' gets a clear status message, same as
    any other ValueError this function already turns into one - never a plotted graph."""
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, modality="lesion", run_name="run-2d", n_dims=2)
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-2d", run_dir)

    content = graph_content_for(run, "disconnection_load")

    assert isinstance(content, html.P)
    assert "only applies to modality='sdc'" in content.children


def test_build_app_raises_on_empty_runs(tmp_path):
    with pytest.raises(ValueError, match="at least one production run"):
        build_app([], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path))


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

    app = build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path))

    # .controls' children: [picker-row-1 (Dato/Pipeline/Metodo), picker-row-2
    # (Metrica/Componenti/Run), color-buttons] - color-buttons is the last one, not a fixed
    # index, so this doesn't silently break the next time a row is added/reordered.
    controls_children = app.layout.children[2].children
    color_buttons_div = controls_children[-2]  # -1 is the grid row below it
    assert len(color_buttons_div.children) == len(COLOR_MODE_ORDER)
    assert color_buttons_div.children[0].className == "active"  # neutro selected by default

    # The grid row: hidden until a grid mode (volume, disconnection) is picked, one button per
    # grid the registry can actually serve, the default one pre-selected (30-09-26).
    grid_row = controls_children[-1]
    assert grid_row.id == "color-grid-row"
    assert grid_row.style == {"display": "none"}
    grid_buttons = grid_row.children[1:]  # children[0] is the "Griglia" label
    assert [b.id["grid"] for b in grid_buttons] == available_grids()
    assert [b.className for b in grid_buttons if b.id["grid"] == DEFAULT_GRID] == ["active"]


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
    # (src.utils.subject_ids._SUBJECT_RE, enforced unconditionally by discover_files_by_subject
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


def test_static_png_bytes_from_lesion_mask_path_returns_valid_png(tmp_path):
    # str path input, exactly what _download_lesion_png passes (lesion_paths[subject_id]) - not
    # bg_img="MNI152" (view_img's own shortcut, see _static_png_bytes's docstring): passing that
    # string to plot_stat_map raises ValueError: File not found: 'MNI152', caught only by this
    # end-to-end call, not by a mocked plot_stat_map.
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    lesion_path = data_root / "UNIPD/WashU" / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii.gz"

    png_bytes = _static_png_bytes(str(lesion_path), threshold=0.5, cmap="autumn", colorbar=False)

    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_static_glass_brain_png_bytes_from_lesion_mask_path_returns_valid_png(tmp_path):
    # "Salva PNG (glass brain)" button's own helper (29-09-26, on request) - same str-path input
    # shape as _download_lesion_glass_png passes (lesion_paths[subject_id]), autumn/no-colorbar
    # matching that callback's own choice for a binary mask (see its docstring).
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    lesion_path = data_root / "UNIPD/WashU" / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii.gz"

    png_bytes = _static_glass_brain_png_bytes(str(lesion_path), threshold=0.5, cmap="autumn", colorbar=False)

    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_build_cluster_overlap_view_returns_percentage_img_for_static_png(tmp_path):
    # Regression for the new 3rd return value (11-09-26): percentage_img must be the exact image
    # the interactive view itself renders, not a separately-built one, and must itself be a valid
    # input to _static_png_bytes (would have failed loudly before the bg_img="MNI152" fix above).
    # 4 subjects (the fixture's own default row count) - cluster 0 has 2 of them, only one
    # lesioned at (1, 1, 1), same shape as test_overlap_map_content_for_valid_cluster_returns_iframe.
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", subject_ids[0], [(1, 1, 1)])
    _make_lesion_subject(data_root, "UNIPD/WashU", subject_ids[1], [])
    _make_lesion_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], [(2, 2, 2)])
    _make_lesion_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], [(2, 2, 2)])
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    view, n_subjects, percentage_img, missing = _build_cluster_overlap_view(run, metadata, 0, _lesion_cfg(data_root))

    assert n_subjects == 2
    assert missing == []
    assert percentage_img.shape == _LESION_SHAPE
    # 1 of 2 subjects lesioned at (1, 1, 1) - 50% overlap there, 0% everywhere else.
    assert percentage_img.get_fdata()[1, 1, 1] == pytest.approx(50.0)
    assert percentage_img.get_fdata()[0, 0, 0] == pytest.approx(0.0)

    png_bytes = _static_png_bytes(percentage_img, threshold=1e-6, cmap="hot", colorbar=True)
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


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


def test_build_cluster_overlap_view_skips_unresolvable_subject_and_reports_it(tmp_path):
    # 29-09-26, on request: a cluster with one member missing on disk (e.g. after the 23-09-26
    # lesion-mask swap, .claude/history/data_changelog.md) still produces a map over the
    # subjects that ARE resolvable, instead of failing the whole panel - sub-STUNIPD0002 is in
    # this cluster's metadata but has no lesion file created for it below.
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", subject_ids[0], [(1, 1, 1)])
    # subject_ids[1] deliberately has no lesion file on disk at all.
    _make_lesion_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], [(2, 2, 2)])
    _make_lesion_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], [(2, 2, 2)])
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    view, n_subjects, percentage_img, missing = _build_cluster_overlap_view(run, metadata, 0, _lesion_cfg(data_root))

    assert n_subjects == 1
    assert missing == ["sub-STUNIPD0002"]
    # 1 of 1 *resolved* subjects lesioned at (1, 1, 1) - 100%, not 50% (the missing subject is
    # excluded from the denominator entirely, not counted as "not lesioned").
    assert percentage_img.get_fdata()[1, 1, 1] == pytest.approx(100.0)


def test_overlap_map_content_for_partial_cluster_shows_warning(tmp_path):
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", subject_ids[0], [(1, 1, 1)])
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
    heading, caption, warning, viewer_wrap = content.children
    assert heading.children == "Cluster 0 (n=1)"
    assert warning.className == "anatomy-warning"
    assert "sub-STUNIPD0002" in _warning_text(warning)
    assert isinstance(viewer_wrap.children, html.Iframe)


def test_disconnectome_viewer_content_for_unresolvable_subject_returns_status_message(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, modality="sdc", run_name="run-a")
    run = ProductionRun("sdc", "dim_reduction", "umap", "run-a", run_dir)
    metadata = run_metadata(run)

    content = disconnectome_viewer_content_for(run, "sub-does-not-exist", metadata, _sdc_cfg(tmp_path))

    assert isinstance(content, html.P)
    assert "sub-does-not-exist" in content.children


def test_disconnectome_viewer_content_for_valid_subject_returns_iframe(tmp_path):
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", {(1, 1, 1): 0.8})
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", run_name="run-a",
        extra_metadata={"subject_id": ["sub-STUNIPD0001", "sub-2", "sub-3", "sub-4"]},
    )
    run = ProductionRun("sdc", "dim_reduction", "umap", "run-a", run_dir)
    metadata = run_metadata(run)

    content = disconnectome_viewer_content_for(run, "sub-STUNIPD0001", metadata, _sdc_cfg(data_root))

    assert isinstance(content, html.Div)
    heading, _caption, viewer_wrap = content.children
    assert heading.children == "sub-STUNIPD0001 (UNIPD/WashU)"
    iframe = viewer_wrap.children
    assert isinstance(iframe, html.Iframe)
    assert _FONT_STACK in iframe.srcDoc


def test_disconnection_map_content_for_empty_cluster_returns_status_message(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    content = disconnection_map_content_for(run, metadata, 99, _sdc_cfg(tmp_path))

    assert isinstance(content, html.P)
    assert "99" in content.children


def test_build_cluster_disconnection_percent_mode_counts_subjects_over_the_threshold(tmp_path):
    """30-09-26, on request: "percent" makes the disconnection map the SAME quantity as the
    lesion overlap map - % of the cluster's subjects affected in a voxel - by binarizing each
    subject at DISCONNECTION_PROBABILITY_THRESHOLD before averaging, instead of averaging the
    continuous probabilities.

    Same fixture as the mean test below, which is the point: at (1,1,1) two subjects hold 0.8
    and 0.4, so the MEAN is 0.6 while the PERCENT is 50% (only the 0.8 exceeds 0.5). The two
    numbers answer different questions, and 0.6 must never be read as "60% of the cluster"."""
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[0], {(1, 1, 1): 0.8, (2, 2, 2): 0.2})
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[1], {(1, 1, 1): 0.4})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], {(3, 3, 3): 0.9})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], {(3, 3, 3): 0.9})
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")

    _view, n_subjects, percent_img, missing = _build_cluster_disconnection_view(
        run, run_metadata(run), 0, _sdc_cfg(data_root), map_mode="percent"
    )

    assert (n_subjects, missing) == (2, [])
    values = percent_img.get_fdata()
    assert values[1, 1, 1] == pytest.approx(50.0)   # 1 of 2 subjects above 0.5
    assert values[2, 2, 2] == pytest.approx(0.0)    # 0.2 is below the threshold for everyone
    assert values[0, 0, 0] == pytest.approx(0.0)


def test_build_cluster_disconnection_view_rejects_an_unknown_map_mode(tmp_path):
    """A typo'd mode must fail with the known list, never silently fall through to one of the
    two real maps - they answer different questions."""
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    for dataset, sid in zip(["UNIPD/WashU"] * 2 + ["UKLFR/stroke_UKLFR"] * 2, subject_ids):
        _make_disconnectome_subject(data_root, dataset, sid, {(1, 1, 1): 0.8})
    run_dir = _make_run_dir(
        tmp_path / "results", modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")

    with pytest.raises(ValueError, match="unknown disconnection map mode"):
        _build_cluster_disconnection_view(run, run_metadata(run), 0, _sdc_cfg(data_root), map_mode="bogus")


def test_build_cluster_disconnection_view_returns_mean_img_for_static_png(tmp_path):
    # Mirrors test_build_cluster_overlap_view_returns_percentage_img_for_static_png - continuous
    # mean instead of binarized percentage: cluster 0 has 2 subjects, disconnection 0.8/0.4 at
    # (1,1,1) -> mean 0.6, one of them also 0.2 at (2,2,2) -> mean 0.1 (divided by both subjects,
    # not just the one with a nonzero value there - build_mean_map's own contract).
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[0], {(1, 1, 1): 0.8, (2, 2, 2): 0.2})
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[1], {(1, 1, 1): 0.4})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], {(3, 3, 3): 0.5})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], {(3, 3, 3): 0.5})
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    view, n_subjects, mean_img, missing = _build_cluster_disconnection_view(
        run, metadata, 0, _sdc_cfg(data_root), map_mode="mean"
    )

    assert n_subjects == 2
    assert missing == []
    assert mean_img.shape == _LESION_SHAPE
    assert mean_img.get_fdata()[1, 1, 1] == pytest.approx(0.6)
    assert mean_img.get_fdata()[2, 2, 2] == pytest.approx(0.1)
    assert mean_img.get_fdata()[0, 0, 0] == pytest.approx(0.0)

    png_bytes = _static_png_bytes(mean_img, threshold=1e-6, cmap="magma", colorbar=True)
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_build_cluster_disconnection_view_skips_unresolvable_subject_and_reports_it(tmp_path):
    # Same skip-and-warn behavior as test_build_cluster_overlap_view_skips_unresolvable_subject_
    # and_reports_it, for the continuous SDC mean map - subject_ids[1] has no disconnectome file.
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[0], {(1, 1, 1): 0.8})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], {(3, 3, 3): 0.5})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], {(3, 3, 3): 0.5})
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    view, n_subjects, mean_img, missing = _build_cluster_disconnection_view(
        run, metadata, 0, _sdc_cfg(data_root), map_mode="mean"
    )

    assert n_subjects == 1
    assert missing == ["sub-STUNIPD0002"]
    # Mean over the 1 resolved subject only (0.8), not divided by 2 as if the missing subject
    # contributed a 0 - it's excluded from the denominator entirely.
    assert mean_img.get_fdata()[1, 1, 1] == pytest.approx(0.8)


def test_disconnection_map_content_for_partial_cluster_shows_warning(tmp_path):
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[0], {(1, 1, 1): 0.8})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], {(3, 3, 3): 0.5})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], {(3, 3, 3): 0.5})
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    content = disconnection_map_content_for(run, metadata, 0, _sdc_cfg(data_root))

    assert isinstance(content, html.Div)
    heading, caption, warning, viewer_wrap = content.children
    assert heading.children == "Cluster 0 (n=1)"
    assert warning.className == "anatomy-warning"
    assert "sub-STUNIPD0002" in _warning_text(warning)
    assert isinstance(viewer_wrap.children, html.Iframe)


def test_static_glass_brain_png_bytes_from_disconnectome_path_returns_valid_png(tmp_path):
    # "Salva PNG (glass brain)" button's own helper for the SDC panel (29-09-26, on request) -
    # threshold=0.1/alpha=0.9 matching _download_disconnectome_glass_png's own constants
    # (_DISCONNECTOME_GLASS_BRAIN_THRESHOLD/_ALPHA), picked to hide the near-zero noise streaks
    # a glass-brain projection would otherwise show (see that function's own docstring).
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", {(1, 1, 1): 0.8})
    disconnectome_path = (
        data_root / "UNIPD/WashU" / "sdc" / "sub-STUNIPD0001" / "sub-STUNIPD0001_res-1_desc-disconnectome.nii.gz"
    )

    png_bytes = _static_glass_brain_png_bytes(
        str(disconnectome_path), threshold=0.1, cmap="magma", colorbar=True, alpha=0.9,
    )

    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_disconnection_map_content_for_valid_cluster_returns_iframe(tmp_path):
    subject_ids = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUKLFR0001", "sub-STUKLFR0002"]
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[0], {(1, 1, 1): 0.6})
    _make_disconnectome_subject(data_root, "UNIPD/WashU", subject_ids[1], {(1, 1, 1): 0.4})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[2], {(2, 2, 2): 0.5})
    _make_disconnectome_subject(data_root, "UKLFR/stroke_UKLFR", subject_ids[3], {(2, 2, 2): 0.5})
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": subject_ids, "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    metadata = run_metadata(run)

    content = disconnection_map_content_for(run, metadata, 0, _sdc_cfg(data_root))

    assert isinstance(content, html.Div)
    heading, caption, viewer_wrap = content.children
    assert heading.children == "Cluster 0 (n=2)"
    # The caption is [sentence, <span class="anatomy-note">] since 30-09-26: what the colour
    # means on the first line, why the map is built this way on a quieter second one.
    sentence, note = caption.children
    assert "%" in sentence and "0-100%" in sentence     # default mode is "percent"
    assert note.className == "anatomy-note"
    assert f"{DISCONNECTION_PROBABILITY_THRESHOLD:g}" in note.children
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


def test_tag_param_options_method_missing_from_registry_returns_sentinel_not_raise(tmp_path, caplog):
    # Regression: a clustering method with real production runs on disk but no entry in
    # params_clustering.json (a registry/artifact mismatch, e.g. a method renamed/dropped from
    # the registry after its output was written - lessons_learned.md #12, "dbscan" -> "hdbscan"
    # for real) used to propagate load_tag_params' own ValueError straight out of
    # tag_param_options, crashing the "Parametri" picker step (500) the moment this method was
    # selected - with the old code this test fails with an uncaught ValueError.
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", method="dbscan", run_name="run-a",
        params={"eps": 0.5}, reduction_metric="euclidean", reduction_n_components=2,
    )
    runs = [ProductionRun("lesion", "clustering", "dbscan", "run-a", run_dir, reduction_method="umap")]
    # Registry only knows "kmeans" - "dbscan" is unregistered, same shape as a dropped method.
    params_file = _clustering_params_file(tmp_path, methods=("kmeans",))

    with caplog.at_level("WARNING"):
        labels = tag_param_options(runs, "lesion", "clustering", "dbscan", "euclidean", 2, params_file)

    assert labels == [NO_METRIC]
    assert "dbscan" in caplog.text


def test_runs_matching_method_missing_from_registry_returns_empty_not_raise(tmp_path):
    # Same registry gap as above, exercised through runs_matching's own separate
    # load_tag_params call site (line ~539) - tag_param_options being fixed doesn't protect this
    # second, independent call site, since a caller could reach it with a non-NO_METRIC label
    # (e.g. a stale dropdown value from before the registry was edited mid-session).
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", method="dbscan", run_name="run-a",
        params={"eps": 0.5}, reduction_metric="euclidean", reduction_n_components=2,
    )
    runs = [ProductionRun("lesion", "clustering", "dbscan", "run-a", run_dir, reduction_method="umap")]
    params_file = _clustering_params_file(tmp_path, methods=("kmeans",))

    matching = runs_matching(runs, "lesion", "clustering", "dbscan", "euclidean", 2, "eps=0.5", params_file)

    assert matching == []


def test_lesion_save_buttons_do_not_use_stale_clickdata_after_run_switch(tmp_path):
    # Regression (01-09-26 bug fix): embedding-graph.clickData is a client-side prop that does
    # NOT reset just because run-picker switches to a different run (graph-area's children get
    # replaced, but Dash/React patches the same-id Graph node rather than remounting it) - only
    # lesion-viewer-content.children used to reset to the placeholder (via ctx.triggered_id ==
    # "run-picker"). The Save buttons read clickData directly via State, so with the old code
    # pressing "Salva HTML"/"Salva PNG" right after switching runs - without clicking a new point
    # on the new run - silently downloaded the *previous* run's clicked subject, with the visible
    # panel already showing "Clicca un punto..." and no indication of what was actually
    # downloaded. Exercised through the real Dash callbacks (Flask test client), not the
    # underlying pure functions, since the bug lived in the callback wiring itself (which State
    # each callback reads), not in graph_content_for/lesion_viewer_content_for.
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    results_root = tmp_path / "results"
    shared_subject_metadata = {"subject_id": ["sub-STUNIPD0001", "sub-2", "sub-3", "sub-4"]}
    dir_a = _make_run_dir(results_root, run_name="run-a", extra_metadata=shared_subject_metadata)
    dir_b = _make_run_dir(results_root, run_name="run-b", extra_metadata=shared_subject_metadata)
    run_a = ProductionRun("lesion", "dim_reduction", "umap", "run-a", dir_a)
    run_b = ProductionRun("lesion", "dim_reduction", "umap", "run-b", dir_b)
    app = build_app([run_a, run_b], _lesion_cfg(data_root), _sdc_cfg(data_root), _clustering_params_file(tmp_path))
    app.server.config["TESTING"] = True
    client = app.server.test_client()

    def post(output_id_props, inputs, changed, state=None):
        outputs = [{"id": i, "property": p} for i, p in output_id_props]
        if len(outputs) > 1:
            output = ".." + "...".join(f"{i}.{p}" for i, p in output_id_props) + ".."
        else:
            output = f"{output_id_props[0][0]}.{output_id_props[0][1]}"
            outputs = outputs[0]  # a genuinely single output needs a bare dict, not a list-of-one
            # (a list-of-one is misread as a wildcard multi-output spec by this Dash version -
            # confirmed against its own _validate.validate_multi_return while investigating the
            # original bug report).
        body = {"output": output, "outputs": outputs, "inputs": inputs, "changedPropIds": changed, "state": state or []}
        resp = client.post("/_dash-update-component", data=json.dumps(body), content_type="application/json")
        return resp

    click_data = {"points": [{"text": "sub-STUNIPD0001"}]}

    # 1) Click the subject while run-a is selected - the Store records it.
    resp = post(
        [("lesion-viewer-content", "children"), ("lesion-viewer-subject", "data")],
        [
            {"id": "embedding-graph", "property": "clickData", "value": click_data},
            {"id": "run-picker", "property": "value", "value": run_a.key},
        ],
        ["embedding-graph.clickData"],
    )
    assert resp.status_code == 200
    assert resp.get_json()["response"]["lesion-viewer-subject"]["data"] == "sub-STUNIPD0001"

    # 2) Switch to run-b (clickData itself would still be the stale value client-side, exactly
    # as in the real browser bug) - the Store must reset to None, same as the visible placeholder.
    resp = post(
        [("lesion-viewer-content", "children"), ("lesion-viewer-subject", "data")],
        [
            {"id": "embedding-graph", "property": "clickData", "value": click_data},
            {"id": "run-picker", "property": "value", "value": run_b.key},
        ],
        ["run-picker.value"],
    )
    assert resp.status_code == 200
    response = resp.get_json()["response"]
    assert response["lesion-viewer-subject"]["data"] is None
    assert "Clicca un punto" in json.dumps(response["lesion-viewer-content"]["children"])

    # 3) Press "Salva HTML" without clicking a new point on run-b - the Save callback now reads
    # the just-reset Store (None), not the still-stale embedding-graph.clickData, so it must not
    # produce a download at all (PreventUpdate -> 204, no "lesion-download" key in the response).
    resp = post(
        [("lesion-download", "data")],
        [{"id": "lesion-save-btn", "property": "n_clicks", "value": 1}],
        ["lesion-save-btn.n_clicks"],
        state=[
            {"id": "lesion-viewer-subject", "property": "data", "value": None},
            {"id": "run-picker", "property": "value", "value": run_b.key},
        ],
    )
    assert resp.status_code == 204


def test_sdc_panels_visible_only_for_sdc_modality_runs(tmp_path):
    # The two new SDC anatomy panels (disconnectome-panel, disconnection-map-panel) must stay
    # hidden for a "lesion" modality run (no disconnectome-map.nii.gz to show at all) and only
    # appear for a "sdc" one - disconnection-map-panel additionally needs pipeline="clustering"
    # (a cluster_label to group by), unlike disconnectome-panel which works for any pipeline.
    data_root = tmp_path / "data"
    results_root = tmp_path / "results"
    lesion_dir = _make_run_dir(results_root, modality="lesion", run_name="lesion-run")
    sdc_dim_reduction_dir = _make_run_dir(results_root, modality="sdc", run_name="sdc-dr-run")
    sdc_clustering_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="sdc-cl-run",
        extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    lesion_run = ProductionRun("lesion", "dim_reduction", "umap", "lesion-run", lesion_dir)
    sdc_dr_run = ProductionRun("sdc", "dim_reduction", "umap", "sdc-dr-run", sdc_dim_reduction_dir)
    sdc_cl_run = ProductionRun("sdc", "clustering", "kmeans", "sdc-cl-run", sdc_clustering_dir, reduction_method="umap")
    app = build_app([lesion_run, sdc_dr_run, sdc_cl_run], _lesion_cfg(data_root), _sdc_cfg(data_root), _clustering_params_file(tmp_path))
    app.server.config["TESTING"] = True
    client = app.server.test_client()

    def panel_style(output_id, run_key):
        body = {
            "output": f"{output_id}.style",
            "outputs": {"id": output_id, "property": "style"},
            "inputs": [{"id": "run-picker", "property": "value", "value": run_key}],
            "changedPropIds": ["run-picker.value"],
            "state": [],
        }
        resp = client.post("/_dash-update-component", data=json.dumps(body), content_type="application/json")
        assert resp.status_code == 200
        return resp.get_json()["response"][output_id]["style"]

    assert panel_style("disconnectome-panel", lesion_run.key) == {"display": "none"}
    assert panel_style("disconnectome-panel", sdc_dr_run.key) == {}
    assert panel_style("disconnectome-panel", sdc_cl_run.key) == {}

    assert panel_style("disconnection-map-panel", lesion_run.key) == {"display": "none"}
    # sdc modality but dim_reduction pipeline (no cluster_label) - still hidden.
    assert panel_style("disconnection-map-panel", sdc_dr_run.key) == {"display": "none"}
    assert panel_style("disconnection-map-panel", sdc_cl_run.key) == {}


def test_representative_subject_panel_visible_only_for_clustering_runs(tmp_path):
    # representative-subject-panel's style is one of 6 Outputs on the same
    # _update_cluster_picker callback (options/value/clustering-section style/cluster-map-panel
    # style/this one/cluster-description-panel style) - all 6 must be requested together
    # (Dash's raw endpoint 500s on a subset of a registered multi-output callback's own
    # Outputs, confirmed while writing this test). clustering-section joined the group on
    # 30-09-26, when the cluster chooser was lifted into its own section header.
    data_root = tmp_path / "data"
    results_root = tmp_path / "results"
    dr_dir = _make_run_dir(results_root, run_name="dr-run")
    cl_dir = _make_run_dir(
        results_root, pipeline="clustering", run_name="cl-run", extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    dr_run = ProductionRun("lesion", "dim_reduction", "umap", "dr-run", dr_dir)
    cl_run = ProductionRun("lesion", "clustering", "kmeans", "cl-run", cl_dir, reduction_method="umap")
    app = build_app([dr_run, cl_run], _lesion_cfg(data_root), _sdc_cfg(data_root), _clustering_params_file(tmp_path))
    app.server.config["TESTING"] = True
    client = app.server.test_client()

    output_id_props = [
        ("cluster-picker", "options"), ("cluster-picker", "value"),
        ("clustering-section", "style"), ("cluster-map-panel", "style"),
        ("representative-subject-panel", "style"), ("cluster-description-panel", "style"),
    ]

    def cluster_picker_outputs(run_key):
        body = {
            "output": ".." + "...".join(f"{i}.{p}" for i, p in output_id_props) + "..",
            "outputs": [{"id": i, "property": p} for i, p in output_id_props],
            "inputs": [{"id": "run-picker", "property": "value", "value": run_key}],
            "changedPropIds": ["run-picker.value"],
            "state": [],
        }
        resp = client.post("/_dash-update-component", data=json.dumps(body), content_type="application/json")
        assert resp.status_code == 200
        return resp.get_json()["response"]

    assert cluster_picker_outputs(dr_run.key)["representative-subject-panel"]["style"] == {"display": "none"}
    assert cluster_picker_outputs(cl_run.key)["representative-subject-panel"]["style"] == {}


def test_cluster_centroids_with_nearest_subject_finds_true_nearest_point():
    # 3 points per cluster (not 2) - a 2-point cluster is always exactly equidistant from its
    # own mean, which would make "nearest" an untested tie rather than a real computation.
    # Cluster 0: sub-b is a far outlier that pulls the mean away from sub-a, past sub-c -
    # sub-c ends up strictly closer to the mean than sub-a despite starting nearer the origin.
    embedding = np.array([
        [0.0, 0.0],    # sub-a
        [10.0, 10.0],  # sub-b (outlier)
        [0.1, 0.1],    # sub-c - true nearest to cluster 0's centroid
        [5.0, 5.0],    # sub-d
        [5.2, 5.1],    # sub-e - true nearest to cluster 1's centroid
        [20.0, 20.0],  # sub-f (outlier)
    ])
    metadata = pd.DataFrame({
        "subject_id": ["sub-a", "sub-b", "sub-c", "sub-d", "sub-e", "sub-f"],
        "cluster_label": [0, 0, 0, 1, 1, 1],
    })

    result = cluster_centroids_with_nearest_subject(embedding, metadata)

    assert list(result.index) == [0, 1]
    assert result.loc[0, "dim0"] == pytest.approx(10.1 / 3)
    assert result.loc[0, "dim1"] == pytest.approx(10.1 / 3)
    assert result.loc[0, "nearest_subject_id"] == "sub-c"
    assert result.loc[1, "nearest_subject_id"] == "sub-e"
    # sub-c's own distance to (10.1/3, 10.1/3), computed independently of the function under test.
    expected_distance = float(np.linalg.norm([0.1 - 10.1 / 3, 0.1 - 10.1 / 3]))
    assert result.loc[0, "distance_to_centroid"] == pytest.approx(expected_distance)


def test_cluster_centroids_trace_starts_hidden_but_stays_in_the_legend():
    """29-09-26, on request: "fai in modo che di default siano deselezionati i centroidi sul
    plot, solo quando selezionati dalla legenda diventano attivi". visible="legendonly" is the
    only setting that does both - visible=False would drop the trace from the legend entirely,
    leaving the reader no way to switch it back on."""
    from src.analysis.embedding_app import _add_cluster_centroids_trace

    figure = go.Figure()
    embedding = np.array([[0.0, 0.0], [1.0, 1.0], [5.0, 5.0], [6.0, 6.0]])
    metadata = pd.DataFrame({
        "subject_id": ["sub-a", "sub-b", "sub-c", "sub-d"],
        "cluster_label": [0, 0, 1, 1],
    })

    _add_cluster_centroids_trace(figure, embedding, metadata)

    trace = figure.data[-1]
    assert trace.name == "centroide"
    assert trace.visible == "legendonly"
    assert trace.showlegend is True


def test_cluster_centroids_with_nearest_subject_raises_without_cluster_label_column():
    embedding = np.array([[0.0, 0.0], [1.0, 1.0]])
    metadata = pd.DataFrame({"subject_id": ["sub-a", "sub-b"]})

    with pytest.raises(ValueError, match="cluster_label"):
        cluster_centroids_with_nearest_subject(embedding, metadata)


def test_cluster_centroids_with_nearest_subject_raises_on_mismatched_row_counts():
    embedding = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    metadata = pd.DataFrame({"subject_id": ["sub-a", "sub-b"], "cluster_label": [0, 0]})

    with pytest.raises(ValueError, match="rows"):
        cluster_centroids_with_nearest_subject(embedding, metadata)


def test_representative_subject_content_for_lesion_modality_returns_iframe(tmp_path):
    # Default _make_run_dir fixture: index-0/index-1 subjects at (0,0)/(1,1) in cluster 0, both
    # dataset UNIPD/WashU - centroid (0.5, 0.5) is exactly equidistant from both (a symmetric
    # 2-point cluster, see test_cluster_centroids_with_nearest_subject_finds_true_nearest_point's
    # own docstring for why that's a tie) - only the index-0 subject needs a real lesion file
    # since numpy's argmin deterministically returns the first index on an exact tie. subject_id
    # overridden to a real site-prefixed name (lessons_learned.md #28) only for that one subject.
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": ["sub-STUNIPD0001", "sub-2", "sub-3", "sub-4"], "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    embedding, metadata = load_run(run)

    content = representative_subject_content_for(run, embedding, metadata, 0, _lesion_cfg(data_root), _sdc_cfg(data_root))

    assert isinstance(content, html.Div)
    heading, caption, viewer_wrap = content.children
    assert "Cluster 0" in heading.children
    assert "sub-STUNIPD0001" in heading.children
    assert "distanza=" in caption.children
    assert isinstance(viewer_wrap.children, html.Iframe)


def test_representative_subject_content_for_sdc_modality_dispatches_to_disconnectome_view(tmp_path):
    # Same tie reasoning as the lesion test above - the index-0 subject wins cluster 0's tie
    # deterministically.
    data_root = tmp_path / "data"
    _make_disconnectome_subject(data_root, "UNIPD/WashU", "sub-STUNIPD0001", {(1, 1, 1): 0.8})
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering", run_name="run-a",
        extra_metadata={"subject_id": ["sub-STUNIPD0001", "sub-2", "sub-3", "sub-4"], "cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    embedding, metadata = load_run(run)

    content = representative_subject_content_for(run, embedding, metadata, 0, _lesion_cfg(data_root), _sdc_cfg(data_root))

    assert isinstance(content, html.Div)
    heading, _caption, viewer_wrap = content.children
    assert "sub-STUNIPD0001" in heading.children
    assert isinstance(viewer_wrap.children, html.Iframe)


def test_representative_subject_content_for_unknown_cluster_returns_status_message(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", run_name="run-a", extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")
    embedding, metadata = load_run(run)

    content = representative_subject_content_for(run, embedding, metadata, 99, _lesion_cfg(tmp_path), _sdc_cfg(tmp_path))

    assert isinstance(content, html.P)
    assert "99" in content.children


def test_graph_content_for_adds_centroid_trace_for_clustering_run(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(
        results_root, pipeline="clustering", run_name="run-a", extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "run-a", run_dir, reduction_method="umap")

    content = graph_content_for(run, NEUTRAL_MODE)

    assert isinstance(content, dcc.Graph)
    trace_names = [trace.name for trace in content.figure.data]
    assert "centroide" in trace_names


def test_graph_content_for_no_centroid_trace_for_dim_reduction_run(tmp_path):
    results_root = tmp_path / "results"
    run_dir = _make_run_dir(results_root, pipeline="dim_reduction", run_name="run-a")
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-a", run_dir)

    content = graph_content_for(run, NEUTRAL_MODE)

    assert isinstance(content, dcc.Graph)
    trace_names = [trace.name for trace in content.figure.data]
    assert "centroide" not in trace_names


_PARTICIPANTS_REGISTRY_COLUMNS = ["subject_id", "original_id", "dataset", "disease_id", "has_lesion", "has_sdc", "has_features"]


def _write_participants_registry(metadata_root, rows, extra_columns):
    """Same shape as tests/unit/test_embedding_coloring.py's/test_cluster_description.py's own
    _write_registry - a minimal assets/metadata/participants.csv, monkeypatched via
    _participants_registry_root below."""
    metadata_root.mkdir(parents=True, exist_ok=True)
    header = [*_PARTICIPANTS_REGISTRY_COLUMNS, *extra_columns]
    lines = [",".join(header)] + [",".join(r) for r in rows]
    (metadata_root / "participants.csv").write_text("\n".join(lines) + "\n")


@pytest.fixture
def _participants_registry_root(tmp_path, monkeypatch):
    from src.utils import participants as participants_registry

    root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def test_cluster_description_content_for_valid_cluster_returns_graph(_participants_registry_root):
    _write_participants_registry(
        _participants_registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "60.0", "F", "12.0", "5.0", "1000"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "70.0", "M", "16.0", "10.0", "2000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"], "cluster_label": [0, 0]})

    content = cluster_description_content_for(metadata, 0)

    # The panel is always a Div now (29-09-26): the figure, plus the cross-cluster comparison
    # table under it. No warning paragraph here - every subject is in the registry.
    assert isinstance(content, html.Div)
    graph, table_wrap = content.children
    assert isinstance(graph, dcc.Graph)
    assert isinstance(table_wrap, html.Div)


def test_cluster_description_content_for_empty_cluster_returns_status_message(_participants_registry_root):
    _write_participants_registry(
        _participants_registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "60.0", "F", "12.0", "5.0", "1000"]],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001"], "cluster_label": [0]})

    content = cluster_description_content_for(metadata, 99)

    assert isinstance(content, html.P)
    assert "99" in content.children


def test_cluster_description_content_for_unregistered_subjects_renders_graph_with_warning(
    _participants_registry_root,
):
    """29-09-26 regression (behaviour change, on request): a cluster containing subjects absent
    from participants.csv used to render only an html.P error and no figure at all. It now
    renders the figure over the whole cluster, preceded by a warning line naming the missing
    subjects - same partial-result shape the two anatomy panels already use."""
    _write_participants_registry(
        _participants_registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "60.0", "F", "12.0", "5.0", "1000"]],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame(
        {"subject_id": ["sub-STUNIPD0001", "sub-STUKLFR0062"], "cluster_label": [0, 0]}
    )

    content = cluster_description_content_for(metadata, 0)

    assert isinstance(content, html.Div)
    warning, graph, table_wrap = content.children
    assert isinstance(warning, html.Div) and warning.className == "anatomy-warning"
    assert "sub-STUKLFR0062" in _warning_text(warning)
    # The vivid label is a separate element from the black body text - that split is the whole
    # point of the box (see _warning_box), so it is asserted, not left to CSS alone.
    assert warning.children[0].className == "warning-label"
    assert isinstance(graph, dcc.Graph)
    assert isinstance(table_wrap, html.Div)


def _warning_text(box):
    """Flatten a _warning_box Div to plain text - it is a label Span + the message + an optional
    detail Span, not a bare string, since 29-09-26 ("warning tipo questo devono essere
    renderizzati un po' meglio")."""
    out = []
    for child in box.children:
        out.append(child.children if isinstance(child, html.Span) else child)
    return " ".join(str(x) for x in out)


def _table_rows(content):
    """The <tr> list of the comparison table inside a cluster_description_content_for result."""
    table = next(c for c in content.children if isinstance(c, html.Div)).children[0]
    return table.children[1].children


def test_cluster_description_table_compares_every_cluster_and_marks_the_selected_one(
    _participants_registry_root,
):
    """29-09-26, on request ("statistiche numeriche a confronto tra tutti i vari cluster"): the
    table lists EVERY cluster of the run, not just the one picked in the dropdown, and the
    picked one is the only row flagged `selected`."""
    _write_participants_registry(
        _participants_registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "60.0", "F", "12.0", "5.0", "1000"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "70.0", "M", "16.0", "10.0", "2000"],
            ["sub-STUNIPD0003", "sub-STUNIPD0003", "UNIPD/WashU", "ST", "True", "True", "False", "80.0", "M", "8.0", "3.0", "3000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({
        "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
        "cluster_label": [0, 1, 1],
    })

    rows = _table_rows(cluster_description_content_for(metadata, 1))

    assert len(rows) == 2
    assert [r.className for r in rows] == ["", "selected"]


def test_cluster_description_table_labels_the_noise_bucket_not_as_a_cluster(_participants_registry_root):
    """hdbscan's -1 is every unassigned subject, not a cluster called "-1" - it must be listed
    (it is a real group of this run's subjects) but named for what it is."""
    _write_participants_registry(
        _participants_registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "60.0", "F", "12.0", "5.0", "1000"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "70.0", "M", "16.0", "10.0", "2000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"], "cluster_label": [-1, 0]})

    rows = _table_rows(cluster_description_content_for(metadata, 0))

    assert rows[0].children[0].children.children[1] == "Rumore"
    assert rows[1].children[0].children.children[1] == "Cluster 0"


def test_cluster_description_table_cells_are_numbers_only(_participants_registry_root):
    """29-09-26, on request ("non voglio quelle righe colorate nella tabella, mi confondono la
    lettura"): in-cell bars were tried and removed. A cell is the value plus, only where the
    variable is incomplete, its coverage note - nothing else."""
    _write_participants_registry(
        _participants_registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "25.0", "F", "10.0", "2.0", "1000"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "75.0", "M", "10.0", "2.0", "3000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"], "cluster_label": [0, 0]})

    row = _table_rows(cluster_description_content_for(metadata, 0))[0]

    age_cell = row.children[2]
    assert len(age_cell.children) == 2            # value + coverage slot, no bar
    assert age_cell.children[1] is None           # 2/2 covered, so no note either
    assert age_cell.children[0].className == "stat-value"
    # Italian formatting: '.' groups thousands, ',' is the decimal separator.
    assert age_cell.children[0].children[0] == "50,0"
    assert row.children[6].children[0].children[0] == "2.000"


def test_cluster_description_table_prints_coverage_only_where_incomplete(_participants_registry_root):
    """The n_available/n_total note used to sit under every cell - 25 near-identical fractions
    drowning the values they annotate. Printed only where the variable really is incomplete, it
    goes back to being a signal."""
    _write_participants_registry(
        _participants_registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "60.0", "F", "", "5.0", "1000"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "70.0", "M", "16.0", "10.0", "2000"],
        ],
        ["age", "sex", "education", "NIHSS", "lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"], "cluster_label": [0, 0]})

    row = _table_rows(cluster_description_content_for(metadata, 0))[0]

    age_cell, education_cell = row.children[2], row.children[4]
    assert age_cell.children[1] is None                      # 2/2 - nothing to say
    assert education_cell.children[1].children == "1/2"      # genuinely incomplete



def test_preload_fills_both_stores_so_cluster_maps_need_no_file_reads(tmp_path, monkeypatch):
    # sdc clustering run whose subjects have both a lesion mask and a disconnectome on disk.
    results_root, data_root = tmp_path / "results", tmp_path / "data"
    subject_ids = [f"sub-STUNIPD000{i}" for i in range(1, 5)]
    run_dir = _make_run_dir(
        results_root, modality="sdc", pipeline="clustering",
        extra_metadata={"cluster_label": [0, 0, 1, 1], "subject_id": subject_ids},
    )
    run = ProductionRun("sdc", "clustering", "kmeans", "10-08_s1", run_dir, reduction_method="umap")
    for subject_id, dataset in zip(subject_ids, ["UNIPD/WashU"] * 2 + ["UKLFR/stroke_UKLFR"] * 2):
        _make_lesion_subject(data_root, dataset, subject_id, [(1, 1, 1)])
        _make_disconnectome_subject(data_root, dataset, subject_id, {(1, 1, 1): 0.9})
    app = build_app(
        [run], _lesion_cfg(data_root), _sdc_cfg(data_root), _clustering_params_file(tmp_path), preload=True
    )
    for thread in threading.enumerate():
        if thread.name == "store-preload":
            thread.join(timeout=30)

    def _no_reads(path):
        raise AssertionError(f"file read after preload: {path}")

    monkeypatch.setattr("src.analysis.anatomical_maps.nib.load", _no_reads)
    app.server.config["TESTING"] = True
    client = app.server.test_client()
    body = {
        "output": "cluster-map-content.children",
        "outputs": {"id": "cluster-map-content", "property": "children"},
        "inputs": [
            {"id": "run-picker", "property": "value", "value": run.key},
            {"id": "cluster-picker", "property": "value", "value": 0},
        ],
        "changedPropIds": ["cluster-picker.value"],
        "state": [],
    }
    resp = client.post("/_dash-update-component", data=json.dumps(body), content_type="application/json")
    assert resp.status_code == 200
    assert "status-message" not in json.dumps(resp.get_json())


def test_preload_failure_is_logged_and_does_not_crash(tmp_path, caplog):
    # No files on disk at all: resolution raises, the preload logs it with a traceback and ends.
    run_dir = _make_run_dir(tmp_path / "results", pipeline="clustering", extra_metadata={"cluster_label": [0, 0, 1, 1]})
    run = ProductionRun("lesion", "clustering", "kmeans", "10-08_s1", run_dir, reduction_method="umap")

    with caplog.at_level(logging.INFO):
        build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path), preload=True)
        for thread in threading.enumerate():
            if thread.name == "store-preload":
                thread.join(timeout=30)

    failures = [r for r in caplog.records if "preload lesion failed" in r.getMessage()]
    assert len(failures) == 1 and failures[0].exc_info


@pytest.mark.parametrize("mode_name", COLOR_MODE_ORDER)
def test_every_color_mode_has_a_description_without_an_equals_sign(mode_name):
    """The sentence above the plot: every button, the neutral one included, must have one - an
    empty paragraph would read as a layout glitch - and it is prose, not "Colore = ..." notation
    (06-10-26, on request)."""
    description = color_mode_description(mode_name)

    assert description.strip()
    assert "=" not in description


def test_each_description_belongs_to_its_own_mode():
    descriptions = [color_mode_description(mode) for mode in COLOR_MODE_ORDER]

    assert len(set(descriptions)) == len(COLOR_MODE_ORDER)  # none copy-pasted onto a second mode


def test_description_sits_between_the_section_heading_and_the_plot(tmp_path):
    run_dir = _make_run_dir(tmp_path / "results", run_name="run-2d", n_dims=2)
    run = ProductionRun("lesion", "dim_reduction", "umap", "run-2d", run_dir)
    app = build_app([run], _lesion_cfg(tmp_path), _sdc_cfg(tmp_path), _clustering_params_file(tmp_path))
    ids = [getattr(child, "id", None) for child in app.layout.children]

    heading = next(i for i, child in enumerate(app.layout.children) if getattr(child, "children", None) == "Embedding Visualization")
    assert ids[heading + 1] == "color-description"
    assert ids[heading + 2] == "graph-area"
    assert app.layout.children[heading + 1].children == color_mode_description("neutro")
