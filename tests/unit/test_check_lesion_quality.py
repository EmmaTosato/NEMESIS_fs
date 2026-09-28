"""Unit tests for scripts/check_lesion_quality.py - synthetic .nii.gz fixtures, no EBRAIN
mount needed. Full main() CLI runs, same convention as
tests/integration/test_build_lesion_matrix_pipeline.py, kept under tests/unit/ to match
scripts/populate_metadata.py's own test file location."""

import json
import logging

import nibabel as nib
import numpy as np
import pandas as pd

from scripts import check_lesion_quality

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _make_lesion_subject(data_root, dataset, subject_id, lesion_voxels):
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _make_reference_template(path):
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), path)


def _make_brain_mask(path, brain_voxels):
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in brain_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), path)


def _write_config(tmp_path, data_root, brain_mask_path, overrides=None):
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "reference_template_path": str(template_path),
        "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "max_out_of_brain_fraction": 0.5,
        "brain_mask_path": str(brain_mask_path),
        "output_root": str(tmp_path / "unused_matrix_output"),
        "session_name": "run1",
        "overwrite": False,
    }
    cfg.update(overrides or {})
    path = tmp_path / "build_lesion_matrix.json"
    path.write_text(json.dumps(cfg))
    return path


def test_check_lesion_quality_end_to_end(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(check_lesion_quality, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(check_lesion_quality, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])  # inside brain mask
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0002", [(9, 9, 9)])  # outside brain mask
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])
    config_path = _write_config(tmp_path, data_root, brain_mask_path)
    output_path = tmp_path / "lesion_quality_metrics.csv"

    with caplog.at_level(logging.INFO):
        exit_code = check_lesion_quality.main(
            ["--config", str(config_path), "--output-path", str(output_path)]
        )
    assert exit_code == 0
    assert "run duration:" in caplog.text

    metrics = pd.read_csv(output_path)
    assert list(metrics["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    assert list(metrics["out_of_brain_fraction"]) == [0.0, 1.0]
    assert "lesion_volume_voxels" not in metrics.columns  # participants.csv is the one source for it

    reports = list((tmp_path / "summaries").glob("*.md"))
    logs = list((tmp_path / "logs").glob("*.log"))
    assert len(reports) == 1
    assert len(logs) == 1
    assert "out_of_brain_fraction" in reports[0].read_text()


def test_check_lesion_quality_skips_when_output_exists_and_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(check_lesion_quality, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(check_lesion_quality, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])
    config_path = _write_config(tmp_path, data_root, brain_mask_path)
    output_path = tmp_path / "lesion_quality_metrics.csv"
    output_path.write_text("subject_id,dataset,out_of_brain_fraction\nsub-fake,siteA,0.0\n")
    before = output_path.read_text()

    exit_code = check_lesion_quality.main(["--config", str(config_path), "--output-path", str(output_path)])

    assert exit_code == 0
    assert output_path.read_text() == before  # untouched - no --overwrite, no recompute
    assert not (tmp_path / "summaries").exists()  # never even started a run


def test_check_lesion_quality_overwrite_recomputes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_lesion_quality, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(check_lesion_quality, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])
    config_path = _write_config(tmp_path, data_root, brain_mask_path)
    output_path = tmp_path / "lesion_quality_metrics.csv"
    output_path.write_text("subject_id,dataset,out_of_brain_fraction\nsub-fake,siteA,0.0\n")

    exit_code = check_lesion_quality.main(
        ["--config", str(config_path), "--output-path", str(output_path), "--overwrite"]
    )

    assert exit_code == 0
    metrics = pd.read_csv(output_path)
    assert list(metrics["subject_id"]) == ["sub-STUNIPD0001"]  # replaced, not appended to sub-fake


def test_check_lesion_quality_missing_brain_mask_path_returns_1(tmp_path, monkeypatch):
    monkeypatch.setattr(check_lesion_quality, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(check_lesion_quality, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])
    # max_out_of_brain_fraction absent -> config.brain_mask_path resolves to None
    config_path = _write_config(
        tmp_path, data_root, brain_mask_path, overrides={"max_out_of_brain_fraction": None, "brain_mask_path": None}
    )
    output_path = tmp_path / "lesion_quality_metrics.csv"

    exit_code = check_lesion_quality.main(["--config", str(config_path), "--output-path", str(output_path)])

    assert exit_code == 1
    assert not output_path.exists()
