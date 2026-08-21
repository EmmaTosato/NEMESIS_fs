"""Unit tests for src/analysis/embedding_coloring.py."""

import pandas as pd
import pytest

from src.analysis.embedding_coloring import COLOR_MODES, color_values, resolve_color_mode


def test_registry_has_expected_modes():
    # cluster_label added 15-08-26 (docs/dev/clustering_migration_plan.md §3) - clustering.py's
    # own production output, never consumed via a pipeline's color_by config (see this
    # module's own docstring), only by src.pipeline.embedding_app.
    assert set(COLOR_MODES) == {"dataset", "side", "volume", "nihss", "cluster_label"}


def test_registry_column_mapping():
    assert resolve_color_mode("dataset").column == "dataset"
    assert resolve_color_mode("side").column == "lesion_side"
    assert resolve_color_mode("volume").column == "lesion_volume_voxels"
    assert resolve_color_mode("nihss").column == "nihss"
    assert resolve_color_mode("cluster_label").column == "cluster_label"


def test_dataset_mode_is_categorical_and_reads_metadata_column():
    mode = resolve_color_mode("dataset")
    assert mode.kind == "categorical"
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2", "sub-3"], "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR"]})
    values = color_values(metadata, "dataset")
    assert list(values) == ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR"]


def test_volume_mode_is_continuous_and_reads_persisted_column():
    """Regression (2026-08-17): "volume" used to recompute X.sum(axis=1) live, with no
    binarity guard - silently wrong for a parcellated (continuous) X. Now reads the already-
    computed lesion_volume_voxels column instead, same as every other mode - never touches X
    at all."""
    mode = resolve_color_mode("volume")
    assert mode.kind == "continuous"
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2", "sub-3"], "lesion_volume_voxels": [2, 1, 3]})
    values = color_values(metadata, "volume")
    assert list(values) == [2, 1, 3]


def test_volume_mode_uses_log_scale():
    assert resolve_color_mode("volume").log_scale is True


def test_nihss_mode_uses_linear_scale():
    assert resolve_color_mode("nihss").log_scale is False


def test_categorical_modes_default_log_scale_false():
    assert resolve_color_mode("dataset").log_scale is False
    assert resolve_color_mode("side").log_scale is False


def test_side_mode_is_categorical_and_reads_persisted_column():
    mode = resolve_color_mode("side")
    assert mode.kind == "categorical"
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "lesion_side": ["left", "right"]})
    values = color_values(metadata, "side")
    assert list(values) == ["left", "right"]


def test_nihss_mode_is_continuous_and_reads_persisted_column():
    mode = resolve_color_mode("nihss")
    assert mode.kind == "continuous"
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "nihss": [4.0, float("nan")]})
    values = color_values(metadata, "nihss")
    assert values[0] == 4.0
    assert pd.isna(values[1])


def test_color_values_missing_column_raises():
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/WashU"]})
    with pytest.raises(ValueError, match="metadata has no 'lesion_volume_voxels' column"):
        color_values(metadata, "volume")


def test_resolve_color_mode_unknown_raises():
    with pytest.raises(ValueError, match="unknown color_by mode 'bogus' - known:"):
        resolve_color_mode("bogus")


def test_cluster_label_mode_is_categorical_and_reads_metadata_column():
    mode = resolve_color_mode("cluster_label")
    assert mode.kind == "categorical"
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2", "sub-3"], "cluster_label": [0, 1, -1]})
    values = color_values(metadata, "cluster_label")
    assert list(values) == [0, 1, -1]


def test_cluster_label_mode_uses_linear_scale_not_applicable_but_default_false():
    # kind="categorical", so log_scale is irrelevant to rendering (see build_embedding_figure)
    # - still asserted for consistency with every other mode's default.
    assert resolve_color_mode("cluster_label").log_scale is False
