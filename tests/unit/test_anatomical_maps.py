"""Unit tests for src/analysis/anatomical_maps.py - synthetic .nii.gz fixtures, no real data required."""

import nibabel as nib
import numpy as np
import pytest

from src.analysis.anatomical_maps import (
    build_mean_map,
    build_overlap_map,
    resolve_available_lesion_paths,
    resolve_lesion_paths,
)

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)
_LESION_GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"
_DISCONNECTOME_GLOB = "sdc/*/*_res-1_desc-disconnectome.nii.gz"


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


def _make_disconnectome_subject(data_root, dataset, subject_id, voxel_values):
    """sdc/<subject_id>/<subject_id>_..._res-1_desc-disconnectome.nii.gz - same glob shape as
    src.features.sdc.build_sdc_voxelwise_matrix's own sdc_glob, continuous (never binary) values
    unlike a lesion mask."""
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel, value in voxel_values.items():
        volume[voxel] = value
    nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_res-1_desc-disconnectome.nii.gz")


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


def test_resolve_available_lesion_paths_skips_unresolvable_subjects_and_warns(tmp_path, caplog):
    # 29-09-26, on request: a per-cluster aggregate map (unlike a single-subject viewer) should
    # proceed with whatever subjects ARE resolvable, not fail entirely over one gap.
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(2, 2, 2)])

    with caplog.at_level("WARNING"):
        resolved, missing = resolve_available_lesion_paths(
            ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD9999"],
            {"sub-STUNIPD0001": "siteA", "sub-STUNIPD0002": "siteA", "sub-STUNIPD9999": "siteA"},
            tmp_path,
            _LESION_GLOB,
        )

    assert set(resolved) == {"sub-STUNIPD0001", "sub-STUNIPD0002"}
    assert missing == ["sub-STUNIPD9999"]
    assert any("sub-STUNIPD9999" in record.message for record in caplog.records)


def test_resolve_available_lesion_paths_no_missing_returns_empty_list(tmp_path, caplog):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])

    with caplog.at_level("WARNING"):
        resolved, missing = resolve_available_lesion_paths(
            ["sub-STUNIPD0001"], {"sub-STUNIPD0001": "siteA"}, tmp_path, _LESION_GLOB,
        )

    assert set(resolved) == {"sub-STUNIPD0001"}
    assert missing == []
    assert caplog.records == []


def test_resolve_available_lesion_paths_raises_if_none_resolvable(tmp_path):
    with pytest.raises(ValueError, match="none of the 1 requested"):
        resolve_available_lesion_paths(
            ["sub-STUNIPD9999"], {"sub-STUNIPD9999": "siteA"}, tmp_path, _LESION_GLOB,
        )


def test_resolve_available_lesion_paths_subject_missing_from_dataset_map_raises(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])

    with pytest.raises(ValueError, match="sub-STUNIPD0001"):
        resolve_available_lesion_paths(["sub-STUNIPD0001"], {}, tmp_path, _LESION_GLOB)


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


def test_build_mean_map_averages_continuous_values(tmp_path):
    # 3 subjects, voxel (1,1,1) with values 1.0/0.5/0.0 (mean 0.5), voxel (2,2,2) only in subject 1.
    _make_disconnectome_subject(tmp_path, "siteA", "sub-STUNIPD0001", {(1, 1, 1): 1.0, (2, 2, 2): 0.4})
    _make_disconnectome_subject(tmp_path, "siteA", "sub-STUNIPD0002", {(1, 1, 1): 0.5})
    _make_disconnectome_subject(tmp_path, "siteA", "sub-STUNIPD0003", {(1, 1, 1): 0.0})
    disconnectome_paths = resolve_lesion_paths(
        ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
        {"sub-STUNIPD0001": "siteA", "sub-STUNIPD0002": "siteA", "sub-STUNIPD0003": "siteA"},
        tmp_path,
        _DISCONNECTOME_GLOB,
    )

    mean_img = build_mean_map(disconnectome_paths, _reference_img(), resample_interpolation="nearest")

    mean = mean_img.get_fdata()
    assert mean[1, 1, 1] == pytest.approx(0.5)
    assert mean[2, 2, 2] == pytest.approx(0.4 / 3)
    assert mean[0, 0, 0] == pytest.approx(0.0)


def test_build_mean_map_empty_input_raises():
    with pytest.raises(ValueError, match="empty"):
        build_mean_map({}, _reference_img(), resample_interpolation="nearest")


def test_build_mean_map_one_corrupt_file_still_raises(tmp_path):
    # Same isolation contract as build_overlap_map's own regression (a bad file among many must
    # still abort the whole map, not be silently skipped by the thread pool).
    _make_disconnectome_subject(tmp_path, "siteA", "sub-STUNIPD0001", {(1, 1, 1): 0.7})
    good_paths = resolve_lesion_paths(
        ["sub-STUNIPD0001"], {"sub-STUNIPD0001": "siteA"}, tmp_path, _DISCONNECTOME_GLOB
    )
    disconnectome_paths = dict(good_paths)
    disconnectome_paths["sub-STUNIPD9999"] = tmp_path / "does-not-exist.nii.gz"

    with pytest.raises(Exception):
        build_mean_map(disconnectome_paths, _reference_img(), resample_interpolation="nearest")
