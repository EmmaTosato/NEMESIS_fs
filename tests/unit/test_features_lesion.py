"""Unit tests for src/features/lesion.py - synthetic .nii.gz fixtures, no real data required."""

import nibabel as nib
import numpy as np
import pytest

from src.features.lesion import (
    build_lesion_matrix,
    load_and_resample_atlas,
    load_reference_image,
    reconstruct_parcel_volume,
)

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _make_lesion_subject(data_root, dataset, subject_id, lesion_voxels):
    subject_dir = data_root / dataset / subject_id / "lesion" / "manual_masks" / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _make_atlas(path, block_a, block_b):
    atlas = np.zeros(_SHAPE, dtype=np.int32)
    atlas[block_a] = 1
    atlas[block_b] = 2
    nib.save(nib.Nifti1Image(atlas, _AFFINE), path)


def _make_reference_template(path):
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), path)


_GLOB = "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz"


def _make_lesion_subject_pipeline_first(data_root, dataset, subject_id, lesion_voxels):
    """Same fixture as _make_lesion_subject, but in the pipeline-first shape
    (`<pipeline>/<subject_id>/anat/...`) the real local retrieval layout uses
    today (src.retrieval.output_layout) - regression fixture for
    test_build_lesion_matrix_voxelwise_pipeline_first_layout below."""
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def test_build_lesion_matrix_voxelwise(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-01", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject(tmp_path, "siteA", "sub-02", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-03", [(5, 5, 5)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, parcel_ids = build_lesion_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        reference_template_path=template_path,
        lesion_glob=_GLOB,
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        parcellate=False,
    )

    assert parcel_ids is None
    assert list(metadata["subject_id"]) == ["sub-01", "sub-02", "sub-03"]
    assert X.shape[0] == 3
    assert non_constant_mask.sum() == X.shape[1]
    # 3 distinct lesioned voxels across all subjects survive the constant-feature drop
    assert X.shape[1] == 3


def test_build_lesion_matrix_voxelwise_pipeline_first_layout(tmp_path):
    """Regression: _discover_lesion_files must derive where subject folders
    sit from lesion_glob itself, not assume they're dataset_root's immediate
    children - the real local layout is pipeline-first
    (<pipeline>/<subject_id>/...) today, not subject-first."""
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-01", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-02", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, parcel_ids = build_lesion_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        reference_template_path=template_path,
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        parcellate=False,
    )

    assert parcel_ids is None
    assert list(metadata["subject_id"]) == ["sub-01", "sub-02"]
    assert X.shape[0] == 2


def test_build_lesion_matrix_subject_count_mismatch_raises(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-01", [(1, 1, 1)])
    (tmp_path / "siteA" / "sub-02").mkdir(parents=True)  # subject dir with no lesion file
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(ValueError, match="subject dirs"):
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            parcellate=False,
        )


def test_build_lesion_matrix_parcellated_fraction_lesioned(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-01", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject(tmp_path, "siteA", "sub-02", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-03", [(5, 5, 5)])

    atlas_path = tmp_path / "atlas.nii.gz"
    block_a = np.s_[0:5, 0:5, 0:5]
    block_b = np.s_[5:10, 5:10, 5:10]
    _make_atlas(atlas_path, block_a, block_b)
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, _non_constant_mask, parcel_ids = build_lesion_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        reference_template_path=template_path,
        lesion_glob=_GLOB,
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        parcellate=True,
        atlas_path=atlas_path,
        parcel_aggregation="fraction_lesioned",
    )

    assert list(parcel_ids) == [1, 2]
    assert X.shape == (3, 2)
    parcel_a_size = 5 * 5 * 5
    assert X[0, 0] == pytest.approx(2 / parcel_a_size)
    assert X[1, 0] == pytest.approx(1 / parcel_a_size)
    assert X[2, 0] == 0
    assert X[2, 1] == pytest.approx(1 / parcel_a_size)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"parcellate": True}, "required when parcellate=True"),
        ({"parcellate": False, "atlas_path": "x.nii.gz"}, "must not be set when parcellate=False"),
        ({"parcellate": False, "parcel_aggregation": "fraction_lesioned"}, "must not be set when parcellate=False"),
    ],
)
def test_parcellation_argument_validation(tmp_path, kwargs, match):
    _make_lesion_subject(tmp_path, "siteA", "sub-01", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    base = dict(
        data_root=tmp_path,
        datasets=["siteA"],
        reference_template_path=template_path,
        lesion_glob=_GLOB,
        binarize_threshold=0.5,
        resample_interpolation="nearest",
    )
    base.update(kwargs)
    with pytest.raises(ValueError, match=match):
        build_lesion_matrix(**base)


def test_unknown_parcel_aggregation_raises(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-01", [(1, 1, 1)])
    atlas_path = tmp_path / "atlas.nii.gz"
    _make_atlas(atlas_path, np.s_[0:5, 0:5, 0:5], np.s_[5:10, 5:10, 5:10])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(ValueError, match="unknown parcel_aggregation"):
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            parcellate=True,
            atlas_path=atlas_path,
            parcel_aggregation="bogus",
        )


def test_load_and_resample_atlas_excludes_background(tmp_path):
    reference_dir = tmp_path / "siteA" / "sub-01" / "lesion" / "manual_masks" / "anat"
    reference_dir.mkdir(parents=True)
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), reference_dir / "sub-01_label-lesion_mask.nii.gz")
    reference_img = nib.load(reference_dir / "sub-01_label-lesion_mask.nii.gz")

    atlas_path = tmp_path / "atlas.nii.gz"
    _make_atlas(atlas_path, np.s_[0:5, 0:5, 0:5], np.s_[5:10, 5:10, 5:10])

    atlas_labels, parcel_ids = load_and_resample_atlas(atlas_path, reference_img)
    assert atlas_labels.shape == _SHAPE
    assert list(parcel_ids) == [1, 2]  # 0 (background) excluded


def test_load_and_resample_atlas_all_background_raises(tmp_path):
    reference_dir = tmp_path / "siteA" / "sub-01" / "lesion" / "manual_masks" / "anat"
    reference_dir.mkdir(parents=True)
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), reference_dir / "sub-01_label-lesion_mask.nii.gz")
    reference_img = nib.load(reference_dir / "sub-01_label-lesion_mask.nii.gz")

    atlas_path = tmp_path / "empty_atlas.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.int32), _AFFINE), atlas_path)

    with pytest.raises(ValueError, match="no non-zero labels"):
        load_and_resample_atlas(atlas_path, reference_img)


def test_reconstruct_parcel_volume():
    atlas_labels = np.zeros(_SHAPE, dtype=np.int64)
    atlas_labels[0:5, 0:5, 0:5] = 1
    atlas_labels[5:10, 5:10, 5:10] = 2
    parcel_ids = np.array([1, 2])
    parcel_values = np.array([0.4, 0.9])

    volume = reconstruct_parcel_volume(parcel_values, atlas_labels, parcel_ids)
    assert volume.shape == _SHAPE
    assert np.all(volume[0:5, 0:5, 0:5] == 0.4)
    assert np.all(volume[5:10, 5:10, 5:10] == 0.9)
    assert volume[9, 0, 0] == 0  # background stays 0


def test_reconstruct_parcel_volume_length_mismatch_raises():
    atlas_labels = np.zeros(_SHAPE, dtype=np.int64)
    with pytest.raises(ValueError, match="must match"):
        reconstruct_parcel_volume(np.array([0.1, 0.2]), atlas_labels, np.array([1]))


def test_load_reference_image_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="reference_template_path not found"):
        load_reference_image(tmp_path / "does_not_exist.nii.gz")


def test_load_reference_image_valid(tmp_path):
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    reference_img = load_reference_image(template_path)
    assert reference_img.shape == _SHAPE
