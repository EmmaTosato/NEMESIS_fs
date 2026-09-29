"""Unit tests for src/pipeline/enrich_metadata.py - synthetic tsv/csv fixtures, no real data."""

import json
import logging
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.pipeline.enrich_metadata import (
    EnrichMetadataConfig,
    LesionMetricsConfig,
    compute_fresh_lesion_volumes,
    compute_geometric_lesion_sides,
    enrich,
    load_config,
    resolve_dataset_values,
    source_column_for,
)
from src.utils.metadata_sources import DatasetSource

_REGISTRY_COLUMNS = ["subject_id", "original_id", "dataset", "disease_id", "has_lesion", "has_sdc", "has_features"]

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _registry(rows):
    return pd.DataFrame(rows, columns=_REGISTRY_COLUMNS)


def _write_tsv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(columns)] + ["\t".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n")
    return path


def _config(tmp_path, sources, variables, fill=False, lesion_metrics=None, datasets=None):
    return EnrichMetadataConfig(
        project="test",
        sources=sources,
        participants_path=tmp_path / "participants.csv",
        datasets=datasets,
        variables=variables,
        lesion_metrics=lesion_metrics,
        fill=fill,
        run_notes="test",
    )


def _make_lesion_mask(data_root, dataset, subject_id, lesion_voxels):
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _write_lesion_matrix_config(tmp_path, data_root, datasets, brain_voxels=None):
    """A build_lesion_matrix.json-shaped config, the shape compute_fresh_lesion_volumes/
    compute_geometric_lesion_sides (via load_build_matrix_config) expect for
    lesion_metrics.build_matrix_config. brain_voxels, if given, also writes a brain
    mask and sets brain_mask_path - needed by any test exercising
    correct_out_of_brain=True."""
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), template_path)
    cfg = {
        "project": "test",
        "data_root": str(data_root),
        "datasets": datasets,
        "reference_template_path": str(template_path),
        "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "output_root": str(tmp_path / "unused_matrix_output"),
        "session_name": "unused",
        "overwrite": False,
    }
    if brain_voxels is not None:
        brain_mask_path = tmp_path / "brain_mask.nii.gz"
        volume = np.zeros(_SHAPE, dtype=np.float32)
        for voxel in brain_voxels:
            volume[voxel] = 1.0
        nib.save(nib.Nifti1Image(volume, _AFFINE), brain_mask_path)
        cfg["brain_mask_path"] = str(brain_mask_path)
    path = tmp_path / "build_lesion_matrix.json"
    path.write_text(json.dumps(cfg))
    return path


def test_joins_on_original_id_not_subject_id(tmp_path):
    """UCL-UK's raw participant_id is the legacy site id, not the canonical subject
    id - joining on subject_id would silently match nothing for the whole dataset
    (.claude/lessons_learned.md #30)."""
    tsv = _write_tsv(
        tmp_path / "raw.tsv", ["participant_id", "age"], [["ST_UCL-UK_0001", "61"], ["ST_UCL-UK_0002", "48"]]
    )
    sources = {"UCL-UK/UCLStrokeData": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        ["sub-STUCLUK0001", "ST_UCL-UK_0001", "UCL-UK/UCLStrokeData", "ST", "True", "False", "False"],
        ["sub-STUCLUK0002", "ST_UCL-UK_0002", "UCL-UK/UCLStrokeData", "ST", "True", "False", "False"],
    ])

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"]))
    assert list(out["age"]) == ["61", "48"]


def test_missing_column_for_one_dataset_is_not_an_error(tmp_path):
    """A variable absent from a dataset's tsv is a structural per-dataset gap
    (UCL-UK has no NIHSS at all) - every subject gets an empty cell, no raise."""
    tsv_a = _write_tsv(tmp_path / "a.tsv", ["participant_id", "age", "NIHSS"], [["sub-STUNIPD0001", "70", "4"]])
    tsv_b = _write_tsv(tmp_path / "b.tsv", ["participant_id", "age"], [["sub-STUKE0001", "55"]])
    sources = {
        "UNIPD/WashU": DatasetSource(tsv_a, tmp_path),
        "UKE/WAKEUP_acute": DatasetSource(tsv_b, tmp_path),
    }
    registry = _registry([
        ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"],
        ["sub-STUKE0001", "sub-STUKE0001", "UKE/WAKEUP_acute", "ST", "True", "True", "False"],
    ])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["age", "NIHSS"]))
    assert list(out["age"]) == ["70", "55"]
    assert out.loc[0, "NIHSS"] == "4"
    assert pd.isna(out.loc[1, "NIHSS"])
    missing = {c.dataset: c.missing_variables for c in coverages}
    assert missing["UKE/WAKEUP_acute"] == ["NIHSS"]
    assert missing["UNIPD/WashU"] == []


def test_na_sentinel_and_blank_become_empty(tmp_path):
    """"n/a" and a blank cell are both genuine missing values, never kept as strings."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "n/a"], ["sub-STUNIPD0002", ""], ["sub-STUNIPD0003", "62"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2, 3)
    ])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["age"]))
    assert pd.isna(out.loc[0, "age"]) and pd.isna(out.loc[1, "age"])
    assert out.loc[2, "age"] == "62"
    assert coverages[0].n_missing_cells["age"] == 2


def test_registered_substitution_is_applied_and_reported(tmp_path):
    """PASPORT has no baseline NIHSS - the documented NIHSS_at_presentation proxy is
    applied, and surfaced in the coverage record rather than being invisible."""
    tsv = _write_tsv(
        tmp_path / "p.tsv", ["participant_id", "NIHSS_at_presentation"], [["sub-STUNIPD0001", "9"]]
    )
    sources = {"UNIPD/PASPORT": DatasetSource(tsv, tmp_path)}
    registry = _registry([["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/PASPORT", "ST", "True", "True", "False"]])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["NIHSS"]))
    assert out.loc[0, "NIHSS"] == "9"
    assert coverages[0].substituted == {"NIHSS": "NIHSS_at_presentation"}


def test_substitution_is_not_applied_to_other_datasets(tmp_path):
    """The proxy is registered for PASPORT only - another dataset lacking NIHSS gets
    an empty cell, never NIHSS_at_presentation silently."""
    tsv = _write_tsv(
        tmp_path / "w.tsv", ["participant_id", "NIHSS_at_presentation"], [["sub-STUNIPD0001", "9"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"]])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["NIHSS"]))
    assert pd.isna(out.loc[0, "NIHSS"])
    assert coverages[0].substituted == {}


def test_source_column_for_prefers_canonical_name():
    assert source_column_for("UNIPD/PASPORT", "NIHSS", ["NIHSS", "NIHSS_at_presentation"]) == "NIHSS"
    assert source_column_for("UNIPD/PASPORT", "NIHSS", ["NIHSS_at_presentation"]) == "NIHSS_at_presentation"
    assert source_column_for("UNIPD/WashU", "NIHSS", ["NIHSS_at_presentation"]) is None


def test_subject_absent_from_raw_tsv_raises(tmp_path):
    """participants.csv and the raw tsv disagreeing about who exists is a real
    inconsistency, not a missing value."""
    tsv = _write_tsv(tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"]])
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([["sub-STUNIPD0009", "sub-STUNIPD0009", "UNIPD/WashU", "ST", "True", "True", "False"]])

    with pytest.raises(ValueError, match="no row in"):
        enrich(registry, _config(tmp_path, sources, ["age"]))


def test_lesion_side_source_marks_only_resolved_values(tmp_path):
    """lesion_side_source distinguishes a clinically recorded side from an unresolved
    one - so a later, geometrically computed value stays distinguishable."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "lesion_side"],
        [["sub-STUNIPD0001", "left"], ["sub-STUNIPD0002", "n/a"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])

    out, _ = enrich(registry, _config(tmp_path, sources, ["lesion_side"]))
    assert out.loc[0, "lesion_side_source"] == "clinical"
    assert pd.isna(out.loc[1, "lesion_side_source"])


def test_fill_true_preserves_existing_values(tmp_path):
    """fill=true only writes empty cells - an existing value is never overwritten."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])
    registry["age"] = ["999", np.nan]  # 999 is a hand-corrected value that must survive

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], fill=True))
    assert list(out["age"]) == ["999", "55"]


def test_fill_false_recomputes_every_value(tmp_path):
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])
    registry["age"] = ["999", np.nan]

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], fill=False))
    assert list(out["age"]) == ["70", "55"]


def test_out_of_scope_dataset_keeps_its_values(tmp_path):
    """A run restricted to one dataset never blanks another dataset's existing cells."""
    tsv = _write_tsv(tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"]])
    sources = {
        "UNIPD/WashU": DatasetSource(tsv, tmp_path),
        "UKE/WAKEUP_acute": DatasetSource(tmp_path / "missing.tsv", tmp_path),
    }
    registry = _registry([
        ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"],
        ["sub-STUKE0001", "sub-STUKE0001", "UKE/WAKEUP_acute", "ST", "True", "True", "False"],
    ])
    registry["age"] = [np.nan, "44"]

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], datasets=["UNIPD/WashU"]))
    assert list(out["age"]) == ["70", "44"]


def _volume_only_metrics(build_matrix_config, correct_out_of_brain=False):
    return LesionMetricsConfig(
        build_matrix_config=build_matrix_config,
        correct_out_of_brain=correct_out_of_brain,
        compute_volume=True,
        compute_side=False,
        side_threshold=0.2,
    )


def _side_only_metrics(build_matrix_config, threshold=0.1, correct_out_of_brain=False):
    return LesionMetricsConfig(
        build_matrix_config=build_matrix_config,
        correct_out_of_brain=correct_out_of_brain,
        compute_volume=False,
        compute_side=True,
        side_threshold=threshold,
    )


def test_compute_fresh_lesion_volumes_reads_from_masks(tmp_path):
    data_root = tmp_path / "data"
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    matrix_config_path = _write_lesion_matrix_config(tmp_path, data_root, ["UNIPD/WashU"])

    volumes = compute_fresh_lesion_volumes(matrix_config_path, ["UNIPD/WashU"], correct_out_of_brain=False)

    assert volumes == {"sub-STUNIPD0001": 2}


def test_compute_fresh_lesion_volumes_applies_out_of_brain_correction(tmp_path):
    """Regression: compute_fresh_lesion_volumes used to bypass build_lesion_matrix()'s
    own out-of-brain correction entirely - a subject's lesion_volume_voxels here could
    silently disagree with a production matrix built with correct_out_of_brain=true."""
    data_root = tmp_path / "data"
    # 2 voxels inside the brain mask, 1 outside - only the 2 inside should survive.
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1), (1, 2, 1), (5, 5, 5)])
    matrix_config_path = _write_lesion_matrix_config(
        tmp_path, data_root, ["UNIPD/WashU"], brain_voxels=[(1, 1, 1), (1, 2, 1)]
    )

    volumes = compute_fresh_lesion_volumes(matrix_config_path, ["UNIPD/WashU"], correct_out_of_brain=True)

    assert volumes == {"sub-STUNIPD0001": 2}


def test_compute_fresh_lesion_volumes_skips_datasets_outside_matrix_config(tmp_path, caplog):
    """An enrich_metadata run can legitimately be scoped wider than any one
    build_lesion_matrix.json happens to cover - a dataset outside the intersection is
    skipped (warned), not an error."""
    data_root = tmp_path / "data"
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    matrix_config_path = _write_lesion_matrix_config(tmp_path, data_root, ["UNIPD/WashU"])

    with caplog.at_level(logging.WARNING):
        volumes = compute_fresh_lesion_volumes(matrix_config_path, ["UKE/WAKEUP_acute"], correct_out_of_brain=False)

    assert volumes == {}
    assert "UKE/WAKEUP_acute" in caplog.text


def test_lesion_volume_is_written_as_an_integer_not_a_float(tmp_path):
    """A voxel count must never be serialized as "4.0": a subject with no lesion mask
    introduces a NaN, which would promote the whole column to float64."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]],
    )
    data_root = tmp_path / "data"
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2), (1, 1, 3), (1, 1, 4)])
    matrix_config_path = _write_lesion_matrix_config(tmp_path, data_root, ["UNIPD/WashU"])
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2)
    ])

    out, _ = enrich(
        registry, _config(tmp_path, sources, ["age"], lesion_metrics=_volume_only_metrics(matrix_config_path))
    )
    path = tmp_path / "out.csv"
    out.to_csv(path, index=False)
    written = pd.read_csv(path, dtype=str)["lesion_volume_voxels"]
    assert written[0] == "4"  # sub-STUNIPD0002 has no manual_masks entry at all
    assert pd.isna(written[1])


def test_load_config_rejects_unknown_variable(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age", "not_a_variable"], "fill": False, "run_notes": "n",
    }))
    with pytest.raises(ValueError, match="unknown variable"):
        load_config(config_path)


def test_load_config_rejects_duplicate_variables(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age", "age"], "fill": False, "run_notes": "n",
    }))
    with pytest.raises(ValueError, match="duplicate"):
        load_config(config_path)


def test_resolve_dataset_values_reports_missing_cell_counts(tmp_path):
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age", "sex"],
        [["sub-STUNIPD0001", "70", "M"], ["sub-STUNIPD0002", "n/a", "F"]],
    )
    rows = pd.DataFrame({
        "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"],
        "original_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"],
    })
    _, coverage = resolve_dataset_values(
        "UNIPD/WashU", DatasetSource(tsv, tmp_path), rows, ["age", "sex"]
    )
    assert coverage.n_missing_cells == {"age": 1, "sex": 0}


def test_rerun_over_already_enriched_file_is_idempotent(tmp_path):
    """Regression (.claude/lessons_learned.md #17): the merge branch only runs when the
    column already exists, so it was never exercised by a first run. participants.csv is
    read with dtype=str, and pandas' "str" dtype rejects a NaN assignment - a re-run
    writing back a genuinely missing value used to raise TypeError.
    """
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "n/a"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2)
    ])
    config = _config(tmp_path, sources, ["age"])

    first, _ = enrich(registry, config)
    # round-trip through CSV exactly as the pipeline does, so the dtype matches production
    path = tmp_path / "participants.csv"
    first.to_csv(path, index=False)
    second, _ = enrich(pd.read_csv(path, dtype=str), config)

    assert second.loc[0, "age"] == "70"
    assert pd.isna(second.loc[1, "age"])


def test_rerun_with_lesion_volume_over_enriched_file(tmp_path):
    """Same branch, for the numeric column: a subject with no lesion mask maps to NaN,
    which must survive being written back into an existing str-dtype column."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]],
    )
    data_root = tmp_path / "data"
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2), (1, 1, 3), (1, 1, 4)])
    matrix_config_path = _write_lesion_matrix_config(tmp_path, data_root, ["UNIPD/WashU"])
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2)
    ])
    config = _config(tmp_path, sources, ["age"], lesion_metrics=_volume_only_metrics(matrix_config_path))

    first, _ = enrich(registry, config)
    path = tmp_path / "participants.csv"
    first.to_csv(path, index=False)
    second, _ = enrich(pd.read_csv(path, dtype=str), config)

    assert str(second.loc[0, "lesion_volume_voxels"]) == "4"  # non "4.0"
    assert pd.isna(second.loc[1, "lesion_volume_voxels"])


# --- lesion_metrics config validation -----------------------------------------------------------


def test_load_config_lesion_metrics_requires_lesion_side_when_compute_side_true(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age"], "fill": False, "run_notes": "n",
        "lesion_metrics": {
            "build_matrix_config": "m.json", "correct_out_of_brain": False,
            "compute_volume": False, "compute_side": True, "side_threshold": 0.2,
        },
    }))
    with pytest.raises(ValueError, match="compute_side"):
        load_config(config_path)


def test_load_config_lesion_metrics_rejects_both_compute_flags_false(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age"], "fill": False, "run_notes": "n",
        "lesion_metrics": {
            "build_matrix_config": "m.json", "correct_out_of_brain": False,
            "compute_volume": False, "compute_side": False, "side_threshold": 0.2,
        },
    }))
    with pytest.raises(ValueError, match="nothing to compute"):
        load_config(config_path)


def test_load_config_lesion_metrics_rejects_out_of_range_side_threshold(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["lesion_side"], "fill": False, "run_notes": "n",
        "lesion_metrics": {
            "build_matrix_config": "m.json", "correct_out_of_brain": False,
            "compute_volume": False, "compute_side": True, "side_threshold": 1.5,
        },
    }))
    with pytest.raises(ValueError, match="side_threshold"):
        load_config(config_path)


def test_load_config_lesion_metrics_parses_valid_block(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["lesion_side"], "fill": False, "run_notes": "n",
        "lesion_metrics": {
            "build_matrix_config": "m.json", "correct_out_of_brain": True,
            "compute_volume": True, "compute_side": True, "side_threshold": 0.2,
        },
    }))
    config = load_config(config_path)
    assert config.lesion_metrics == LesionMetricsConfig(
        build_matrix_config=Path("m.json"), correct_out_of_brain=True,
        compute_volume=True, compute_side=True, side_threshold=0.2,
    )


# --- geometric lesion_side fallback -------------------------------------------------------------


def _make_side_registry_and_tsv(tmp_path, data_root):
    """3 UNIPD/WashU subjects: 0001 has a clinical lesion_side (never touched by the
    fallback), 0002/0003 don't and each have a real mask lesioned only at voxel index
    >= 1 - anatomical-right for the module-level _AFFINE (no translation, index 0 is
    the exact midline) - so both are unambiguously classifiable as 'right'."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "lesion_side"],
        [["sub-STUNIPD0001", "left"], ["sub-STUNIPD0002", "n/a"], ["sub-STUNIPD0003", "n/a"]],
    )
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0002", [(1, 1, 1), (1, 2, 1)])
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0003", [(1, 1, 1)])
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2, 3)
    ])
    return tsv, registry


def test_geometric_fallback_fills_only_missing_lesion_side(tmp_path):
    data_root = tmp_path / "data"
    tsv, registry = _make_side_registry_and_tsv(tmp_path, data_root)
    matrix_config_path = _write_lesion_matrix_config(tmp_path, data_root, ["UNIPD/WashU"])
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}

    out, _ = enrich(
        registry,
        _config(tmp_path, sources, ["lesion_side"], lesion_metrics=_side_only_metrics(matrix_config_path)),
    )

    by_id = out.set_index("subject_id")
    assert by_id.loc["sub-STUNIPD0001", ["lesion_side", "lesion_side_source"]].tolist() == ["left", "clinical"]
    assert by_id.loc["sub-STUNIPD0002", ["lesion_side", "lesion_side_source"]].tolist() == ["right", "geometric"]
    assert by_id.loc["sub-STUNIPD0003", ["lesion_side", "lesion_side_source"]].tolist() == ["right", "geometric"]


_TRANSLATED_AFFINE = np.array(
    [[2.0, 0.0, 0.0, -10.0], [0.0, 2.0, 0.0, -10.0], [0.0, 0.0, 2.0, -10.0], [0.0, 0.0, 0.0, 1.0]]
)  # world_x(i) = 2*i - 10: index 1 is anatomical-left, index 8 is anatomical-right
   # (module-level _AFFINE has no translation, so it can only ever produce "right" -
   # not usable for a test that needs the correction to flip the classified side).


def test_geometric_fallback_applies_out_of_brain_correction(tmp_path):
    """Same regression as compute_fresh_lesion_volumes, for the laterality side: 3
    left-side lesion voxels sit inside the brain, 5 right-side voxels sit outside it.
    Uncorrected, right dominates (5 > 3) -> 'right'. Corrected, the 5 out-of-brain
    voxels are zeroed and only the 3 left-side ones remain -> 'left'."""
    data_root = tmp_path / "data"
    subject_dir = data_root / "UNIPD/WashU" / "manual_masks" / "sub-STUNIPD0001" / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in [(1, 1, 1), (1, 2, 1), (1, 3, 1), (8, 1, 1), (8, 2, 1), (8, 3, 1), (8, 4, 1), (8, 5, 1)]:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _TRANSLATED_AFFINE), subject_dir / "sub-STUNIPD0001_label-lesion_mask.nii.gz")

    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _TRANSLATED_AFFINE), template_path)
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    brain_volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in [(1, 1, 1), (1, 2, 1), (1, 3, 1)]:
        brain_volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(brain_volume, _TRANSLATED_AFFINE), brain_mask_path)
    matrix_config_path = tmp_path / "build_lesion_matrix.json"
    matrix_config_path.write_text(json.dumps({
        "project": "test", "data_root": str(data_root), "datasets": ["UNIPD/WashU"],
        "reference_template_path": str(template_path),
        "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5, "resample_interpolation": "nearest",
        "output_root": str(tmp_path / "unused"), "session_name": "unused", "overwrite": False,
        "brain_mask_path": str(brain_mask_path),
    }))

    uncorrected = compute_geometric_lesion_sides(
        matrix_config_path, ["UNIPD/WashU"], threshold=0.1, correct_out_of_brain=False
    )
    corrected = compute_geometric_lesion_sides(
        matrix_config_path, ["UNIPD/WashU"], threshold=0.1, correct_out_of_brain=True
    )

    assert uncorrected == {"sub-STUNIPD0001": "right"}
    assert corrected == {"sub-STUNIPD0001": "left"}


def test_compute_geometric_lesion_sides_skips_datasets_outside_matrix_config(tmp_path, caplog):
    data_root = tmp_path / "data"
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    matrix_config_path = _write_lesion_matrix_config(tmp_path, data_root, ["UNIPD/WashU"])

    with caplog.at_level(logging.WARNING):
        sides = compute_geometric_lesion_sides(
            matrix_config_path, ["UKE/WAKEUP_acute"], threshold=0.2, correct_out_of_brain=False
        )

    assert sides == {}
    assert "UKE/WAKEUP_acute" in caplog.text


def test_compute_geometric_lesion_sides_warns_on_partial_coverage(tmp_path, caplog):
    """Regression: a dataset uncovered by build_matrix_config must be named in the log
    even when *some* other requested dataset IS covered - a partial drop is exactly as
    silent as a total one otherwise (found 28-09-26, in a real dry-run: NEMESIS_T0
    dropped with zero log line naming it, because UKLFR/WashU/etc. in the same call
    made the old 'is in_scope empty at all' check pass)."""
    data_root = tmp_path / "data"
    _make_lesion_mask(data_root, "UNIPD/WashU", "sub-STUNIPD0001", [(1, 1, 1)])
    matrix_config_path = _write_lesion_matrix_config(tmp_path, data_root, ["UNIPD/WashU"])

    with caplog.at_level(logging.WARNING):
        sides = compute_geometric_lesion_sides(
            matrix_config_path, ["UNIPD/WashU", "UNIPD/NEMESIS_T0"], threshold=0.2, correct_out_of_brain=False
        )

    assert "UNIPD/NEMESIS_T0" in caplog.text  # the uncovered dataset must be named, not just implied
    assert sides == {"sub-STUNIPD0001": "right"}  # UNIPD/WashU still computed despite the partial miss
