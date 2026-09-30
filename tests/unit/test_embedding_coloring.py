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


def test_volume_mode_is_continuous_and_reads_the_registry(_registry_root):
    """Regression (2026-08-17): "volume" used to recompute X.sum(axis=1) live, with no
    binarity guard - silently wrong for a parcellated (continuous) X. It then read the run's
    own lesion_volume_voxels column; since 30-09-26 it reads the REGISTRY's
    lesion_volume_voxels_2mm, which is computed once on one fixed grid for every subject and
    is therefore comparable across runs (a run's own column counts voxels on whatever grid
    that build_lesion_matrix call used)."""
    mode = resolve_color_mode("volume")
    assert mode.kind == "continuous"
    assert mode.registry_column == "lesion_volume_voxels_2mm"
    _write_registry(
        _registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "2"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "1"],
        ],
        ["lesion_volume_voxels_2mm"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"]})
    assert list(color_values(metadata, "volume")) == [2, 1]


def test_volume_mode_uses_log_scale():
    assert resolve_color_mode("volume").log_scale is True


def test_nihss_mode_uses_linear_scale():
    assert resolve_color_mode("nihss").log_scale is False


def test_categorical_modes_default_log_scale_false():
    assert resolve_color_mode("dataset").log_scale is False
    assert resolve_color_mode("side").log_scale is False


def test_side_mode_is_categorical_and_reads_the_registry(_registry_root):
    mode = resolve_color_mode("side")
    assert mode.kind == "categorical"
    _write_registry(
        _registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "left"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", "right"],
        ],
        ["lesion_side"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"]})
    assert list(color_values(metadata, "side")) == ["left", "right"]


def test_nihss_mode_is_continuous_and_reads_the_registry(_registry_root):
    mode = resolve_color_mode("nihss")
    assert mode.kind == "continuous"
    _write_registry(
        _registry_root,
        [
            ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "4.0"],
            ["sub-STUNIPD0002", "sub-STUNIPD0002", "UNIPD/WashU", "ST", "True", "True", "False", ""],
        ],
        ["NIHSS"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"]})
    values = color_values(metadata, "nihss")
    assert values[0] == 4.0
    assert pd.isna(values[1])


def test_color_values_registry_without_the_volume_column_raises(_registry_root):
    """The registry is now volume's only source, so a registry that was never enriched with
    it must say exactly that - not fall back to whatever a run happens to carry."""
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"]],
        [],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001"]})
    with pytest.raises(ValueError, match="no 'lesion_volume_voxels_2mm' column"):
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


def test_registry_wins_over_a_stale_run_metadata_column(_registry_root):
    """30-09-26, INVERTED on request ("dash deve prendere da participants"). A run enriched
    before the 2026-09-06 migration still carries its own copy of these clinical columns; that
    copy is a snapshot and can disagree with the registry. The registry is now the source of
    truth for any mode that declares a registry_column, so two runs of the same subjects can
    never be coloured differently."""
    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "right"]],
        ["lesion_side"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001"], "lesion_side": ["left"]})
    assert list(color_values(metadata, "side")) == ["right"]


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


def test_subject_absent_from_registry_is_drawn_as_missing_not_raised(_registry_root, caplog):
    """30-09-26 behaviour change: a subject with no registry row used to make the whole mode
    raise, so one run with a handful of subjects predating the last populate_metadata.py pass
    was entirely unplottable. For a COLOUR, "absent from the registry" and "present but blank"
    are the same fact - there is no value to paint with - so it now becomes the same missing
    value, and the count is logged. Same trade cluster_composition settled the same way."""
    import logging

    _write_registry(
        _registry_root,
        [["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False", "left"]],
        ["lesion_side"],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0009"]})

    with caplog.at_level(logging.WARNING):
        values = color_values(metadata, "side")

    assert list(values) == ["left", "unknown"]
    assert "sub-STUNIPD0009" in caplog.text


def test_run_only_mode_still_raises_on_missing_column(_registry_root):
    """dataset/cluster_label are run-level facts with no registry counterpart (volume stopped
    being one on 30-09-26) - they must keep failing loudly rather than reaching for a registry
    column that does not exist for them."""
    with pytest.raises(ValueError, match="metadata has no 'cluster_label' column"):
        color_values(pd.DataFrame({"subject_id": ["sub-STUNIPD0001"]}), "cluster_label")
