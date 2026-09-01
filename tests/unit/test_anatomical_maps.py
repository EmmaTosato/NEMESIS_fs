"""Unit tests for src/analysis/anatomical_maps.py - synthetic .nii.gz fixtures, no real data required."""

import nibabel as nib
import numpy as np
import pytest

from src.analysis.anatomical_maps import build_overlap_map, resolve_lesion_paths

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)
_LESION_GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"


def _make_lesion_subject(data_root, dataset, subject_id, lesion_voxels):
    """Pipeline-first layout (dataset/manual_masks/<subject_id>/anat/...) - the real local
    retrieval layout, matching _LESION_GLOB above (same fixture shape as
    tests/unit/test_features_lesion.py::_make_lesion_subject_pipeline_first)."""
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _reference_img():
    return nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE)


def test_resolve_lesion_paths_returns_one_path_per_subject(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(2, 2, 2)])

    resolved = resolve_lesion_paths(
        ["sub-STUNIPD0001", "sub-STUNIPD0002"],
        {"sub-STUNIPD0001": "siteA", "sub-STUNIPD0002": "siteA"},
        tmp_path,
        _LESION_GLOB,
    )

    assert set(resolved) == {"sub-STUNIPD0001", "sub-STUNIPD0002"}
    assert resolved["sub-STUNIPD0001"].name == "sub-STUNIPD0001_label-lesion_mask.nii.gz"


def test_resolve_lesion_paths_unresolvable_subject_raises_naming_it(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])

    with pytest.raises(ValueError, match="sub-STUNIPD9999"):
        resolve_lesion_paths(
            ["sub-STUNIPD0001", "sub-STUNIPD9999"],
            {"sub-STUNIPD0001": "siteA", "sub-STUNIPD9999": "siteA"},
            tmp_path,
            _LESION_GLOB,
        )


def test_resolve_lesion_paths_subject_missing_from_dataset_map_raises(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])

    with pytest.raises(ValueError, match="sub-STUNIPD0001"):
        resolve_lesion_paths(["sub-STUNIPD0001"], {}, tmp_path, _LESION_GLOB)


def test_build_overlap_map_counts_and_percentage(tmp_path):
    # 3 subjects, voxel (1,1,1) lesioned in all 3, voxel (2,2,2) lesioned in only 1.
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (2, 2, 2)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0003", [(1, 1, 1)])
    lesion_paths = resolve_lesion_paths(
        ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
        {"sub-STUNIPD0001": "siteA", "sub-STUNIPD0002": "siteA", "sub-STUNIPD0003": "siteA"},
        tmp_path,
        _LESION_GLOB,
    )

    count_img, percentage_img = build_overlap_map(
        lesion_paths, _reference_img(), binarize_threshold=0.5, resample_interpolation="nearest"
    )

    counts = count_img.get_fdata()
    percentage = percentage_img.get_fdata()
    assert counts[1, 1, 1] == 3
    assert counts[2, 2, 2] == 1
    assert counts[0, 0, 0] == 0
    assert percentage[1, 1, 1] == pytest.approx(100.0)
    assert percentage[2, 2, 2] == pytest.approx(100.0 / 3)


def test_build_overlap_map_empty_input_raises():
    with pytest.raises(ValueError, match="empty"):
        build_overlap_map({}, _reference_img(), binarize_threshold=0.5, resample_interpolation="nearest")


def test_build_overlap_map_one_corrupt_file_still_raises(tmp_path):
    """Regression for the 01-09-26 ThreadPoolExecutor rewrite (perf fix - per-subject
    load+resample now runs concurrently): a single bad file among many must still abort the
    whole map (same as the original sequential loop), not be silently skipped/swallowed by the
    thread pool."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    good_paths = resolve_lesion_paths(
        ["sub-STUNIPD0001"], {"sub-STUNIPD0001": "siteA"}, tmp_path, _LESION_GLOB
    )
    lesion_paths = dict(good_paths)
    lesion_paths["sub-STUNIPD9999"] = tmp_path / "does-not-exist.nii.gz"

    with pytest.raises(Exception):
        build_overlap_map(lesion_paths, _reference_img(), binarize_threshold=0.5, resample_interpolation="nearest")
