"""The app's memos: what gets kept, on which key, and what deliberately does not.

These used to be closures inside build_app, reachable only by firing a callback. As an
AppContext they can be tested for what they are actually for - not recomputing something slow -
which no test did before: a memo that silently stopped memoising would have shown up only as a
slow app.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

import tests.unit.test_embedding_app as fixtures
from src.analysis.embedding_app.context import AppContext
from src.analysis.embedding_app.runs import ProductionRun

SUBJECTS = ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003", "sub-STUNIPD0004"]


@pytest.fixture
def context(tmp_path):
    """A context over one lesion clustering run whose subjects have real masks on disk, so the
    anatomy memos have something to build. Returns the context and the run."""
    results, data = tmp_path / "results", tmp_path / "data"
    for subject in SUBJECTS:
        fixtures._make_lesion_subject(data, "UNIPD/WashU", subject, [(1, 1, 1)])
    run_dir = fixtures._make_run_dir(
        results, pipeline="clustering", method="kmeans", run_name="cl", params={"n_clusters": 2},
        extra_metadata={
            "subject_id": SUBJECTS, "dataset": ["UNIPD/WashU"] * 4, "cluster_label": [0, 0, 1, 1],
        },
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "cl", run_dir, reduction_method="umap")
    ctx = AppContext.build(
        [run], fixtures._lesion_cfg(data), fixtures._sdc_cfg(data),
        fixtures._clustering_params_file(tmp_path), tmp_path / "cache",
    )
    return ctx, run


def test_a_cluster_map_is_built_once_and_served_again(context):
    ctx, run = context
    metadata = fixtures.pd.read_csv(run.path / "metadata.csv")

    first = ctx.cluster_overlap_view(run, metadata, 0, ctx.lesion_cfg)
    again = ctx.cluster_overlap_view(run, metadata, 0, ctx.lesion_cfg)

    assert again is first, "la seconda chiamata ha ricostruito la mappa invece di riusarla"
    assert len(ctx.cluster_views) == 1


def test_the_same_cluster_drawn_at_two_widths_is_two_entries(context):
    """The overview draws a cluster smaller than its own panel does, and a nilearn view carries
    its width - one entry for both would serve the wrong size to whichever asked second."""
    ctx, run = context
    metadata = fixtures.pd.read_csv(run.path / "metadata.csv")

    ctx.cluster_overlap_view(run, metadata, 0, ctx.lesion_cfg, width_view=900)
    ctx.cluster_overlap_view(run, metadata, 0, ctx.lesion_cfg, width_view=420)

    assert len(ctx.cluster_views) == 2


def test_two_clusters_are_two_entries(context):
    ctx, run = context
    metadata = fixtures.pd.read_csv(run.path / "metadata.csv")

    ctx.cluster_overlap_view(run, metadata, 0, ctx.lesion_cfg)
    ctx.cluster_overlap_view(run, metadata, 1, ctx.lesion_cfg)

    assert len(ctx.cluster_views) == 2


def test_a_map_that_could_not_be_built_is_not_kept(context):
    """A cluster whose subjects have no file on disk raises; keeping that would make a problem
    that gets fixed - a mount that came back, a file that was copied - permanent for the life of
    the app."""
    ctx, run = context
    metadata = fixtures.pd.read_csv(run.path / "metadata.csv")
    metadata["subject_id"] = ["sub-STUNIPD9001", "sub-STUNIPD9002", "sub-STUNIPD9003", "sub-STUNIPD9004"]

    with pytest.raises(ValueError):
        ctx.cluster_overlap_view(run, metadata, 0, ctx.lesion_cfg)

    assert ctx.cluster_views == {}


def test_the_disconnection_maps_have_their_own_memo(context):
    """A (run, cluster) key says nothing about which anatomy family built the entry, so one
    shared dict would serve a lesion map where a disconnection map was asked for."""
    ctx, run = context

    assert ctx.cluster_views is not ctx.disconnection_views


def test_an_embedding_that_cannot_be_drawn_comes_back_as_a_message_not_an_exception(context):
    ctx, run = context

    embedding, message = ctx.embedding(run)

    assert message is None
    assert isinstance(embedding, np.ndarray)


def test_the_context_cannot_have_a_field_swapped_after_the_app_is_built(context):
    """Frozen: a callback may fill a memo, never replace one."""
    ctx, _run = context

    with pytest.raises(Exception):
        ctx.cluster_views = {}


def test_building_a_context_puts_its_mask_cache_under_the_cache_directory(tmp_path):
    """The mask stores keep each subject's voxels on disk too, so the cache survives a restart,
    under a subdirectory of the one --cache-dir the app is given. The directory inside it is
    named after a signature of the grid, the interpolation and the threshold, so the two stores
    share the root without being able to serve each other's entries - here they land in one
    directory because the two fixture configs genuinely agree on all three (in production the
    lesion grid is res-2 and the disconnectome res-1)."""
    run_dir = fixtures._make_run_dir(tmp_path / "results", run_name="dr")

    AppContext.build(
        [ProductionRun("lesion", "dim_reduction", "umap", "dr", run_dir)],
        fixtures._lesion_cfg(tmp_path / "data"), fixtures._sdc_cfg(tmp_path / "data"),
        fixtures._clustering_params_file(tmp_path), tmp_path / "cache",
    )

    masks = tmp_path / "cache" / "binary_masks"
    assert [entry.name for entry in masks.iterdir() if entry.is_dir()] != []


def test_a_different_threshold_gets_its_own_mask_cache(tmp_path):
    """What makes sharing the root safe: change one thing the voxels depend on and the entries
    go somewhere else, instead of a mask thresholded at 0.5 being served for a query at 0.9."""
    run_dir = fixtures._make_run_dir(tmp_path / "results", run_name="dr")
    lesion_cfg = fixtures._lesion_cfg(tmp_path / "data")
    args = (fixtures._clustering_params_file(tmp_path), tmp_path / "cache")
    run = ProductionRun("lesion", "dim_reduction", "umap", "dr", run_dir)

    AppContext.build([run], lesion_cfg, fixtures._sdc_cfg(tmp_path / "data"), *args)
    before = {entry.name for entry in (tmp_path / "cache" / "binary_masks").iterdir()}
    AppContext.build(
        [run], dataclasses.replace(lesion_cfg, binarize_threshold=0.9),
        fixtures._sdc_cfg(tmp_path / "data"), *args,
    )
    after = {entry.name for entry in (tmp_path / "cache" / "binary_masks").iterdir()}

    assert len(after - before) == 1


def test_a_context_cannot_be_built_with_no_readable_run(tmp_path):
    run_dir = fixtures._make_run_dir(
        tmp_path / "results", pipeline="clustering", method="kmeans", run_name="cl",
        extra_metadata={"cluster_label": [0, 0, 1, 1]},
    )
    run = ProductionRun("lesion", "clustering", "kmeans", "cl", run_dir, reduction_method="umap")

    with pytest.raises(ValueError, match="no run has readable params"):
        AppContext.build(
            [run], fixtures._lesion_cfg(tmp_path / "data"), fixtures._sdc_cfg(tmp_path / "data"),
            fixtures._clustering_params_file(tmp_path), tmp_path / "cache",
        )
