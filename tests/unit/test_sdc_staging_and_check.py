"""Unit tests for src/sdc/staging.py and the check_stage1_outputs() gate in
src/sdc/runner.py. Uses real (small-array) NIfTI files via nibabel rather
than mocking nibabel itself - only true external I/O (BCBToolKit subprocess
calls) is out of scope for these tests, per code_standards.md #4."""

import numpy as np
import nibabel as nib
import pytest

from src.sdc.manifest import ManifestRow
from src.sdc.runner import _EXPECTED_SHAPE, check_stage1_outputs
from src.sdc.staging import stage_subjects


def _row(tmp_path, subject_id):
    lesion_path = tmp_path / "lesions" / f"{subject_id}_lesion_mask.nii.gz"
    lesion_path.parent.mkdir(parents=True, exist_ok=True)
    lesion_path.touch()
    return ManifestRow(subject_id=subject_id, dataset="UNIPD/WashU", lesion_mask_path=lesion_path)


def test_stage_subjects_creates_bids_symlinks(tmp_path):
    row = _row(tmp_path, "sub-STUNIPD0001")
    staging_dir = tmp_path / "staging"

    stage_subjects([row], staging_dir)

    link = staging_dir / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_mask.nii.gz"
    assert link.is_symlink()
    assert link.resolve() == row.lesion_mask_path.resolve()


def test_stage_subjects_refuses_nonempty_staging_dir(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    (staging_dir / "stray_file").touch()

    with pytest.raises(FileExistsError):
        stage_subjects([_row(tmp_path, "sub-STUNIPD0001")], staging_dir)


def _write_disconnectome(prep_dir, subject_id, shape):
    path = prep_dir / subject_id / "lesion" / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(np.zeros(shape, dtype=np.float32), affine=np.eye(4))
    nib.save(image, path)
    return path


def test_check_stage1_outputs_passes_correct_shape(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_disconnectome(prep_dir, row.subject_id, _EXPECTED_SHAPE)

    passed, failed = check_stage1_outputs([row], prep_dir)

    assert passed == [row]
    assert failed == {}


def test_check_stage1_outputs_flags_missing_file(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")

    passed, failed = check_stage1_outputs([row], prep_dir)

    assert passed == []
    assert "missing" in failed[row.subject_id]


def test_check_stage1_outputs_flags_wrong_shape(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_disconnectome(prep_dir, row.subject_id, (10, 10, 10))

    passed, failed = check_stage1_outputs([row], prep_dir)

    assert passed == []
    assert "shape" in failed[row.subject_id]


def test_check_stage1_outputs_does_not_stop_on_one_subject_failure(tmp_path):
    prep_dir = tmp_path / "prep"
    good_row = _row(tmp_path, "sub-STUNIPD0001")
    bad_row = _row(tmp_path, "sub-STUNIPD0002")
    _write_disconnectome(prep_dir, good_row.subject_id, _EXPECTED_SHAPE)
    _write_disconnectome(prep_dir, bad_row.subject_id, (5, 5, 5))

    passed, failed = check_stage1_outputs([good_row, bad_row], prep_dir)

    assert passed == [good_row]
    assert bad_row.subject_id in failed
