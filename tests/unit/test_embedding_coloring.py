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


# --- resolution from the subject registry (06-09-26) -------------------------------------
#
# side/nihss stopped being copied into each run's own metadata.csv when the per-run
# enrichment step was retired; they now resolve from assets/metadata/participants.csv,
# so a run whose metadata carries only subject_id/dataset can still be coloured by them.

_REGISTRY_COLUMNS = ["subject_id", "original_id", "dataset", "disease_id",
                     "has_lesion", "has_sdc", "has_features"]


def _write_registry(metadata_root, rows, extra_columns):
    metadata_root.mkdir(parents=True, exist_ok=True)
    header = [*_REGISTRY_COLUMNS, *extra_columns]
    lines = [",".join(header)] + [",".join(r) for r in rows]
    (metadata_root / "participants.csv").write_text("\n".join(lines) + "\n")


@pytest.fixture
def _registry_root(tmp_path, monkeypatch):
    from src.utils import participants as participants_registry

    root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def test_side_resolves_from_registry_when_run_metadata_lacks_it(_registry_root):
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "left"],
         ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "right"]],
        ["lesion_side"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0002", "sub-STUNIPD0001"]})
    assert list(color_values(metadata, "side")) == ["right", "left"]


def test_side_unresolved_becomes_unknown_not_nan(_registry_root):
    """A categorical mode's values are sorted as plain strings downstream - a NaN would
    raise TypeError, so an empty registry cell must become the explicit bucket."""
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", ""]],
        ["lesion_side"],
    )
    values = color_values(pd.DataFrame({"subject_id": ["sub-STUNIPD0001"]}), "side")
    assert list(values) == ["unknown"]
    assert sorted(set(values))  # sortable as strings, which is the actual contract


def test_nihss_resolves_from_registry_as_numeric(_registry_root):
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "7"],
         ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", ""]],
        ["NIHSS"],
    )
    values = color_values(pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"]}), "nihss")
    assert values[0] == 7.0
    assert pd.isna(values[1])


def test_run_metadata_column_wins_over_the_registry(_registry_root):
    """A run that already carries the column (every run enriched before the rewiring)
    keeps using its own value - the registry is only consulted when it doesn't."""
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "right"]],
        ["lesion_side"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001"], "lesion_side": ["left"]})
    assert list(color_values(metadata, "side")) == ["left"]


def test_registry_without_the_variable_raises(_registry_root):
    """The registry exists but was never enriched with that variable - the caller is told
    which pipeline populates it, instead of getting a blank plot."""
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"]],
        [],
    )
    with pytest.raises(ValueError, match="enrich_metadata"):
        color_values(pd.DataFrame({"subject_id": ["sub-STUNIPD0001"]}), "side")


def test_subject_absent_from_registry_raises(_registry_root):
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "left"]],
        ["lesion_side"],
    )
    with pytest.raises(ValueError, match="no row in the subject registry"):
        color_values(pd.DataFrame({"subject_id": ["sub-STUNIPD0009"]}), "side")


def test_non_registry_mode_still_raises_on_missing_column(_registry_root):
    """volume/dataset/cluster_label are run-level facts with no registry counterpart -
    they must keep failing loudly rather than silently reaching for the registry."""
    with pytest.raises(ValueError, match="metadata has no 'lesion_volume_voxels' column"):
        color_values(pd.DataFrame({"subject_id": ["sub-STUNIPD0001"]}), "volume")
