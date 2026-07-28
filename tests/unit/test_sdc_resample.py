"""Unit tests for src/sdc/resample.py. Uses real (small-array) NIfTI files
via nibabel rather than mocking nibabel/nilearn, per code_standards.md #4."""

import numpy as np
import nibabel as nib
import pytest

from src.sdc.manifest import ManifestRow
from src.sdc.resample import resample_lesion_if_needed, resample_nonconforming_rows

_REFERENCE_AFFINE = np.array(
    [
        [-1.0, 0.0, 0.0, 9.0],
        [0.0, 1.0, 0.0, -6.0],
        [0.0, 0.0, 1.0, -6.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)
_REFERENCE_SHAPE = (18, 18, 18)


def _reference_img():
    data = np.zeros(_REFERENCE_SHAPE, dtype=np.uint8)
    return nib.Nifti1Image(data, affine=_REFERENCE_AFFINE)


def _write_lesion(path, shape, affine, value=1):
    data = np.zeros(shape, dtype=np.uint8)
    data[shape[0] // 2, shape[1] // 2, shape[2] // 2] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(data, affine=affine), path)


def test_resample_lesion_if_needed_returns_same_path_when_already_conforming(tmp_path):
    lesion_path = tmp_path / "sub-A_lesion_mask.nii.gz"
    _write_lesion(lesion_path, _REFERENCE_SHAPE, _REFERENCE_AFFINE)
    resampled_dir = tmp_path / "resampled"

    result = resample_lesion_if_needed(lesion_path, _reference_img(), resampled_dir)

    assert result == lesion_path
    assert not resampled_dir.exists()


def test_resample_lesion_if_needed_resamples_nonconforming_grid(tmp_path):
    # 1.5x voxel size vs. the reference's 1x, same physical space/origin -
    # mirrors UKLFR's 1.5mm masks vs. the 1mm MNI152NLin6Asym target.
    nonconforming_affine = _REFERENCE_AFFINE.copy()
    nonconforming_affine[:3, :3] *= 1.5
    lesion_path = tmp_path / "sub-B_lesion_mask.nii.gz"
    _write_lesion(lesion_path, (12, 12, 12), nonconforming_affine)
    resampled_dir = tmp_path / "resampled"

    result = resample_lesion_if_needed(lesion_path, _reference_img(), resampled_dir)

    assert result != lesion_path
    assert result.parent == resampled_dir
    resampled_img = nib.load(result)
    assert resampled_img.shape == _REFERENCE_SHAPE
    assert np.array_equal(resampled_img.affine, _REFERENCE_AFFINE)
    # nearest-neighbour on a binary mask must stay binary, never invent
    # intermediate intensities
    assert set(np.unique(resampled_img.get_fdata())) <= {0.0, 1.0}


def test_resample_nonconforming_rows_leaves_conforming_rows_untouched(tmp_path):
    lesion_path = tmp_path / "sub-A_lesion_mask.nii.gz"
    _write_lesion(lesion_path, _REFERENCE_SHAPE, _REFERENCE_AFFINE)
    row = ManifestRow(subject_id="sub-A", dataset="UNIPD/WashU", lesion_mask_path=lesion_path)

    rows, failed, timings = resample_nonconforming_rows([row], _reference_img(), tmp_path / "resampled")

    assert rows == [row]
    assert failed == {}
    assert "sub-A" in timings
    assert timings["sub-A"] >= 0.0


def test_resample_nonconforming_rows_repoints_path_for_nonconforming_row(tmp_path):
    nonconforming_affine = _REFERENCE_AFFINE.copy()
    nonconforming_affine[:3, :3] *= 1.5
    lesion_path = tmp_path / "sub-B_lesion_mask.nii.gz"
    _write_lesion(lesion_path, (12, 12, 12), nonconforming_affine)
    row = ManifestRow(subject_id="sub-B", dataset="UKLFR/stroke_UKLFR", lesion_mask_path=lesion_path)
    resampled_dir = tmp_path / "resampled"

    rows, failed, timings = resample_nonconforming_rows([row], _reference_img(), resampled_dir)

    assert failed == {}
    assert len(rows) == 1
    assert rows[0].subject_id == "sub-B"
    assert rows[0].lesion_mask_path != lesion_path
    assert rows[0].lesion_mask_path.parent == resampled_dir
    assert "sub-B" in timings


def test_resample_nonconforming_rows_isolates_one_unreadable_subject(tmp_path):
    good_path = tmp_path / "sub-A_lesion_mask.nii.gz"
    _write_lesion(good_path, _REFERENCE_SHAPE, _REFERENCE_AFFINE)
    bad_path = tmp_path / "sub-B_lesion_mask.nii.gz"
    bad_path.write_bytes(b"not a nifti file")
    good_row = ManifestRow(subject_id="sub-A", dataset="UNIPD/WashU", lesion_mask_path=good_path)
    bad_row = ManifestRow(subject_id="sub-B", dataset="UKLFR/stroke_UKLFR", lesion_mask_path=bad_path)

    rows, failed, timings = resample_nonconforming_rows([good_row, bad_row], _reference_img(), tmp_path / "resampled")

    assert rows == [good_row]
    assert "sub-B" in failed
    assert "not a loadable NIfTI" in failed["sub-B"]
    assert "sub-A" in timings
    assert "sub-B" in timings


def test_resample_lesion_if_needed_rejects_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.nii.gz"

    with pytest.raises((OSError, ValueError, FileNotFoundError)):
        resample_lesion_if_needed(missing, _reference_img(), tmp_path / "resampled")
