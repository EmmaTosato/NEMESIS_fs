"""Unit tests for src/features/lesion.py - synthetic .nii.gz fixtures, no real data required."""

import nibabel as nib
import numpy as np
import pytest

from src.features.lesion import (
    _load_and_binarize_lesion,
    build_lesion_matrix,
    compute_lesion_quality_metrics,
    load_reference_image,
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


def _make_reference_template(path):
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), path)


def _make_brain_mask(path, brain_voxels):
    """Binary brain mask on the same grid as _make_reference_template - brain_voxels is
    the set of voxel coordinates considered inside the brain, everything else is 'outside'."""
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in brain_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), path)


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


def test_build_lesion_matrix_binarize_threshold_one_raises(tmp_path):
    """AUDIT_FINDINGS.md #68 regression: binarize_threshold=1.0 passes config-load range
    validation (0.0-1.0 inclusive) but is degenerate for a strict '>' comparison against
    resampled lesion values typically in [0, 1] - every subject's mask binarizes to zero
    voxels silently, with no error identifying binarize_threshold as the cause, until it
    surfaces much later (e.g. X.shape[1] == 0 after _drop_constant_features)."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(ValueError, match="binarize_threshold"):
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=1.0,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )


def test_build_lesion_matrix_voxelwise(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0003", [(5, 5, 5)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )
    )

    assert excluded_by_group == []
    assert excluded_by_min_volume == []
    assert excluded_by_out_of_brain == []
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"]
    assert X.shape[0] == 3
    assert non_constant_mask.sum() == X.shape[1]
    # 3 distinct lesioned voxels across all subjects survive the constant-feature drop
    assert X.shape[1] == 3
    # sub-STUNIPD0001 has 2 lesioned voxels, sub-STUNIPD0002 has 1, sub-STUNIPD0003 has 1
    # (see _make_lesion_subject calls above) - lesion_volume_voxels must reflect the real
    # per-subject voxel count, not X's own post-constant-drop column count (X.shape[1] == 3
    # is a coincidence of this fixture, not what lesion_volume_voxels means for any
    # individual subject).
    assert list(metadata["lesion_volume_voxels"]) == [2, 1, 1]
    assert "out_of_brain_fraction" not in metadata.columns  # threshold disabled -> column not computed


def test_build_lesion_matrix_voxelwise_pipeline_first_layout(tmp_path):
    """Regression: _discover_lesion_files must derive where subject folders
    sit from lesion_glob itself, not assume they're dataset_root's immediate
    children - the real local layout is pipeline-first
    (<pipeline>/<subject_id>/...) today, not subject-first."""
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )
    )

    assert excluded_by_group == []
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    assert X.shape[0] == 2


def test_build_lesion_matrix_group_filter_excludes_hc(tmp_path):
    """A healthy control has no lesion to mask and structurally shouldn't
    ever appear under manual_masks/ - but the discovery mechanism must not
    silently rely on that absence: with group_filter=["ST"], an HC subject
    dir that does exist (e.g. a future data-organization slip) is excluded
    explicitly and reported, not counted as a subject-dir/lesion-mask
    mismatch (see src/features/subject_discovery.py)."""
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPDHC0001", [(5, 5, 5)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=["ST"],
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert X.shape[0] == 1
    assert excluded_by_group == ["sub-STUNIPDHC0001"]


def test_build_lesion_matrix_subject_count_mismatch_raises(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    (tmp_path / "siteA" / "sub-STUNIPD0002").mkdir(parents=True)  # subject dir with no lesion file
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
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )


def test_build_lesion_matrix_malformed_subject_dir_name_raises_even_without_group_filter(tmp_path):
    """AUDIT_FINDINGS.md #46 regression (twin gap of #26, here in _discover_lesion_files'
    own subject_dirs sanity check): group_of() used to validate subject_dirs naming only
    when group_filter was set - a malformed subject folder (here missing the dash after
    "sub", a realistic hand-copy typo) with no lesion file at all inside it used to surface
    only as a generic subject-count mismatch, never as the actual naming problem, whenever
    group_filter=None (lesson #4)."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    (tmp_path / "siteA" / "sub_STUNIPD9999").mkdir(parents=True)  # malformed name, no lesion file
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(ValueError, match="does not match expected naming"):
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )


def test_load_and_binarize_lesion_resamples_when_affine_differs_but_shape_matches(tmp_path):
    """Regression: previously only img.shape != reference_img.shape triggered
    a resample - a lesion mask with the SAME shape but a DIFFERENT affine
    (different physical origin at the same resolution, a real scenario e.g.
    across slightly different acquisition/registration steps) was treated as
    'already aligned' and used as-is, silently misplacing the lesion in
    physical space. Now the affine is compared too (_needs_resample)."""
    reference_img = nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE)

    # Same shape, origin shifted by one voxel (2mm, this affine's own voxel
    # size) along x relative to the reference.
    shifted_affine = _AFFINE.copy()
    shifted_affine[0, 3] += 2.0
    volume = np.zeros(_SHAPE, dtype=np.float32)
    volume[0, 0, 0] = 1.0
    lesion_path = tmp_path / "sub-01_lesion.nii.gz"
    nib.save(nib.Nifti1Image(volume, shifted_affine), lesion_path)

    data = _load_and_binarize_lesion(lesion_path, reference_img, "nearest", 0.5)
    resampled = data.reshape(_SHAPE)

    # A shape-only check would skip resampling entirely and return the raw
    # array unchanged - the lesioned voxel would still sit at (0, 0, 0). The
    # physically correct position, after resampling onto the reference's own
    # (unshifted) grid, is (1, 0, 0) - one voxel over, matching the real 2mm
    # origin offset (verified independently via nilearn.resample_to_img).
    assert resampled[0, 0, 0] == 0
    assert resampled[1, 0, 0] == 1
    assert resampled.sum() == 1


def test_build_lesion_matrix_missing_dataset_root_raises(tmp_path):
    """Regression: a dataset with a wrong/not-yet-retrieved path used to
    silently contribute 0 subjects - Path.glob on a missing directory returns
    [] with no exception, and 0 subject_dirs == 0 lesion masks passed the
    existing count-mismatch check undetected. Now raises FileNotFoundError
    instead, before the group_filter/count-mismatch checks ever run."""
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(FileNotFoundError, match="siteB"):
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA", "siteB"],  # siteB directory never created (typo/not retrieved)
            reference_template_path=template_path,
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )


def test_load_reference_image_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="reference_template_path not found"):
        load_reference_image(tmp_path / "does_not_exist.nii.gz")


def test_load_reference_image_valid(tmp_path):
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    reference_img = load_reference_image(template_path)
    assert reference_img.shape == _SHAPE


def test_build_lesion_matrix_min_volume_threshold_excludes_small_lesion(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2), (1, 1, 3)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(5, 5, 5)])  # 1 voxel, below threshold
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=2,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_min_volume == ["sub-STUNIPD0002"]
    assert excluded_by_out_of_brain == []


def test_build_lesion_matrix_out_of_brain_threshold_excludes_contaminated_subject(tmp_path):
    # sub-0001: 2 voxels, both inside the brain mask -> fraction 0.0, kept.
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    # sub-0002: 2 voxels, both outside the brain mask -> fraction 1.0, excluded.
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(9, 9, 9), (9, 9, 8)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1), (1, 1, 2), (1, 1, 3)])

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=0.5,
            brain_mask_path=brain_mask_path,
        )
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_out_of_brain == ["sub-STUNIPD0002"]
    assert metadata.loc[metadata["subject_id"] == "sub-STUNIPD0001", "out_of_brain_fraction"].iloc[0] == 0.0


def test_build_lesion_matrix_out_of_brain_fraction_partial(tmp_path):
    """1 of 2 lesion voxels outside the brain mask -> fraction 0.5, kept at threshold 0.5."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (9, 9, 9)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=0.5,
            brain_mask_path=brain_mask_path,
        )
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_out_of_brain == []
    assert metadata["out_of_brain_fraction"].iloc[0] == 0.5


def test_build_lesion_matrix_out_of_brain_threshold_without_brain_mask_path_raises(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(ValueError, match="brain_mask_path"):
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=0.5,
            brain_mask_path=None,
        )


def test_build_lesion_matrix_all_subjects_excluded_by_min_volume_raises(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(ValueError, match="no subjects remain"):
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=100,
            max_out_of_brain_fraction=None,
            brain_mask_path=None,
        )


def test_compute_lesion_quality_metrics_no_threshold_all_subjects_included(tmp_path):
    """Unlike build_lesion_matrix, no subject is ever dropped here - the function only
    reports metrics, it never decides admission."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])  # inside brain mask
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(9, 9, 9)])  # outside brain mask
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0003", [])  # zero-volume, legitimate case
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])

    metadata, excluded_by_group = compute_lesion_quality_metrics(
        data_root=tmp_path,
        datasets=["siteA"],
        reference_template_path=template_path,
        lesion_glob=_GLOB,
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        group_filter=None,
        brain_mask_path=brain_mask_path,
    )

    assert excluded_by_group == []
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"]
    assert list(metadata["lesion_volume_voxels"]) == [1, 1, 0]
    assert list(metadata["out_of_brain_fraction"]) == [0.0, 1.0, 0.0]


def test_compute_lesion_quality_metrics_group_filter_excludes_hc(tmp_path):
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPDHC0001", [(5, 5, 5)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])

    metadata, excluded_by_group = compute_lesion_quality_metrics(
        data_root=tmp_path,
        datasets=["siteA"],
        reference_template_path=template_path,
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        group_filter=["ST"],
        brain_mask_path=brain_mask_path,
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_group == ["sub-STUNIPDHC0001"]


def test_build_lesion_matrix_zero_volume_subject_out_of_brain_fraction_is_zero(tmp_path):
    """A subject binarized to 0 lesion voxels (legitimate per-subject case) gets
    out_of_brain_fraction=0.0, not NaN/undefined - vacuously true, and never wrongly
    excluded by max_out_of_brain_fraction on that basis alone."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [])  # empty mask -> 0 voxels
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_min_volume, excluded_by_out_of_brain = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            min_lesion_volume_voxels=None,
            max_out_of_brain_fraction=0.1,
            brain_mask_path=brain_mask_path,
        )
    )

    assert set(metadata["subject_id"]) == {"sub-STUNIPD0001", "sub-STUNIPD0002"}
    assert excluded_by_out_of_brain == []
    zero_volume_row = metadata.loc[metadata["subject_id"] == "sub-STUNIPD0002"].iloc[0]
    assert zero_volume_row["lesion_volume_voxels"] == 0
    assert zero_volume_row["out_of_brain_fraction"] == 0.0
