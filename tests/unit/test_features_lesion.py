"""Unit tests for src/features/lesion.py - synthetic .nii.gz fixtures, no real data required."""

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.features.lesion import (
    LesionGrid,
    _hemisphere_masks,
    _load_and_binarize_lesion,
    _metadata_columns,
    build_lesion_matrix,
    compute_lesion_metadata,
    lesion_side_from_laterality_index,
    load_reference_image,
    validate_lesion_grids,
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
    (`<pipeline>/<subject_id>/anat/...`) the real local data layout uses
    today - regression fixture for
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
            excluded_subjects=frozenset(),
            correct_out_of_brain=False,
            brain_mask_path=None,
        )


def test_build_lesion_matrix_voxelwise(tmp_path):
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0003", [(5, 5, 5)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, corrected_subjects = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            excluded_subjects=frozenset(),
            correct_out_of_brain=False,
            brain_mask_path=None,
        )
    )

    assert excluded_by_group == []
    assert excluded_by_list == []
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
    # This pipeline adds no quality metric to its own metadata: assets/metadata/lesion_metadata.csv
    # (src.pipeline.compute_lesion_metadata) is the one place those live.
    assert "out_of_brain_fraction" not in metadata.columns


def test_build_lesion_matrix_voxelwise_pipeline_first_layout(tmp_path):
    """Regression: _discover_lesion_files must derive where subject folders
    sit from lesion_glob itself, not assume they're dataset_root's immediate
    children - the real local layout is pipeline-first
    (<pipeline>/<subject_id>/...) today, not subject-first."""
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject_pipeline_first(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, corrected_subjects = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            excluded_subjects=frozenset(),
            correct_out_of_brain=False,
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

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, corrected_subjects = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=["ST"],
            excluded_subjects=frozenset(),
            correct_out_of_brain=False,
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
            excluded_subjects=frozenset(),
            correct_out_of_brain=False,
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
            excluded_subjects=frozenset(),
            correct_out_of_brain=False,
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
            excluded_subjects=frozenset(),
            correct_out_of_brain=False,
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


def test_build_lesion_matrix_correct_out_of_brain_zeroes_voxels_and_reports_corrected_subjects(tmp_path):
    """correct_out_of_brain zeroes each subject's out-of-brain voxels in place (rather than
    excluding the subject) and recomputes lesion_volume_voxels from the corrected data -
    only the genuinely contaminated subject is listed in corrected_subjects."""
    # sub-0001: 1 voxel inside the brain mask, 1 outside -> the outside one gets zeroed.
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (9, 9, 9)])
    # sub-0002: fully inside the brain mask -> untouched, not corrected.
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    brain_mask_path = tmp_path / "brain_mask.nii.gz"
    _make_brain_mask(brain_mask_path, [(1, 1, 1)])

    X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, corrected_subjects = (
        build_lesion_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            reference_template_path=template_path,
            lesion_glob=_GLOB,
            binarize_threshold=0.5,
            resample_interpolation="nearest",
            group_filter=None,
            excluded_subjects=frozenset(),
            correct_out_of_brain=True,
            brain_mask_path=brain_mask_path,
        )
    )

    assert corrected_subjects == [("sub-STUNIPD0001", 1)]
    assert excluded_by_list == []  # correction fixes it, never excludes
    row1 = metadata.loc[metadata["subject_id"] == "sub-STUNIPD0001"].iloc[0]
    assert row1["lesion_volume_voxels"] == 1  # the out-of-brain voxel was zeroed, not counted
    row2 = metadata.loc[metadata["subject_id"] == "sub-STUNIPD0002"].iloc[0]
    assert row2["lesion_volume_voxels"] == 1


def test_build_lesion_matrix_correct_out_of_brain_requires_brain_mask_path(tmp_path):
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
            excluded_subjects=frozenset(),
            correct_out_of_brain=True,
            brain_mask_path=None,
        )


# --- laterality --------------------------------------------------------------------------------

# A genuine MNI-like affine with a real negative half (unlike module-level _AFFINE, which has no
# translation and therefore no world-negative voxels at all) - world_x(i) = 2*i - 10, so i=0..4 is
# anatomical-left, i=5 is the exact midline, i=6..9 is anatomical-right.
_LATERALITY_AFFINE = np.array(
    [[2.0, 0.0, 0.0, -10.0], [0.0, 2.0, 0.0, -10.0], [0.0, 0.0, 2.0, -10.0], [0.0, 0.0, 0.0, 1.0]]
)


def _make_lesion_subject_with_affine(data_root, dataset, subject_id, lesion_voxels, affine):
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, affine), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def test_hemisphere_masks_splits_left_right_excludes_midline():
    reference_img = nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _LATERALITY_AFFINE)
    left_mask, right_mask = _hemisphere_masks(reference_img)

    left_3d = left_mask.reshape(_SHAPE)
    right_3d = right_mask.reshape(_SHAPE)
    assert left_3d[:5].all() and not left_3d[5:].any()
    assert right_3d[6:].all() and not right_3d[:6].any()


def test_hemisphere_masks_raises_on_off_diagonal_affine():
    affine = _LATERALITY_AFFINE.copy()
    affine[0, 1] = 1.0  # rotation/shear term on the first row
    reference_img = nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), affine)
    with pytest.raises(ValueError, match="off-diagonal"):
        _hemisphere_masks(reference_img)


def test_hemisphere_masks_raises_on_wrong_first_axis_orientation():
    """A degenerate first row (affine[0, :3] all zero - world_x has no dependency on
    ANY voxel axis, not even axis 0) passes the off-diagonal check (0 == 0) but leaves
    axis 0 with no well-defined left-right correspondence at all - nib.aff2axcodes
    reports 'A' for it here, not 'R'/'L'. A corrupt/degenerate reference header, not a
    realistic MNI grid - hemisphere classification must refuse to guess rather than
    silently split a meaningless axis."""
    affine = np.array([[0.0, 0.0, 0.0, -10.0], [5.0, 2.0, 0.0, -10.0], [0.0, 0.0, 2.0, -10.0], [0.0, 0.0, 0.0, 1.0]])
    reference_img = nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), affine)
    with pytest.raises(ValueError, match="orientation"):
        _hemisphere_masks(reference_img)


def test_lesion_side_from_laterality_index_classifies_by_threshold():
    assert lesion_side_from_laterality_index(0.5, threshold=0.2) == "left"
    assert lesion_side_from_laterality_index(-0.5, threshold=0.2) == "right"
    assert lesion_side_from_laterality_index(0.1, threshold=0.2) == "both"
    assert lesion_side_from_laterality_index(-0.19, threshold=0.2) == "both"
    assert lesion_side_from_laterality_index(0.2, threshold=0.2) == "left"  # strict '<', boundary is not "both"


def test_lesion_side_from_laterality_index_raises_on_nan():
    with pytest.raises(ValueError, match="NaN"):
        lesion_side_from_laterality_index(float("nan"), threshold=0.2)


# --- compute_lesion_metadata (multi-grid, streaming) --------------------------------------------

# Two grids in the same relationship the real data has: the masks are saved on the FINE grid
# (natively, no resampling - like the real 1mm manual masks), and the COARSE grid is an exact 2x
# subsample of it (like the 2mm production template). world_x(i) = i - 10 on the fine grid and
# 2*i - 10 on the coarse one, so both are centred on the midline, and coarse voxel i samples fine
# voxel 2*i with nearest-neighbour interpolation - which makes every expected count below exact
# rather than approximate, and lets a lesion on an odd fine index vanish on the coarse grid.
_FINE_SHAPE = (20, 20, 20)
_FINE_AFFINE = np.array(
    [[1.0, 0.0, 0.0, -10.0], [0.0, 1.0, 0.0, -10.0], [0.0, 0.0, 1.0, -10.0], [0.0, 0.0, 0.0, 1.0]]
)
_COARSE_SHAPE = _SHAPE
_COARSE_AFFINE = _LATERALITY_AFFINE

_REAL_GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"


def _make_lesion_subject_on_fine_grid(data_root, dataset, subject_id, lesion_voxels):
    """A subject's mask on the fine grid, in the pipeline-first layout the real local data uses."""
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_FINE_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _FINE_AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _make_two_grids(tmp_path, fine_brain_region=None, coarse_brain_region=None):
    """The two LesionGrid entries, each with its own template and its own brain mask ON that same
    grid. A None region means "the whole volume is brain", i.e. nothing is ever out-of-brain."""
    grids = []
    for name, shape, affine, region in (
        ("fine", _FINE_SHAPE, _FINE_AFFINE, fine_brain_region),
        ("coarse", _COARSE_SHAPE, _COARSE_AFFINE, coarse_brain_region),
    ):
        template_path = tmp_path / f"{name}_template.nii.gz"
        nib.save(nib.Nifti1Image(np.zeros(shape, dtype=np.float32), affine), template_path)

        brain = np.ones(shape, dtype=np.float32)
        if region is not None:
            brain[:] = 0.0
            brain[region] = 1.0
        brain_mask_path = tmp_path / f"{name}_brain_mask.nii.gz"
        nib.save(nib.Nifti1Image(brain, affine), brain_mask_path)

        grids.append(
            LesionGrid(name=name, reference_template_path=template_path, brain_mask_path=brain_mask_path)
        )
    return grids


def _compute(tmp_path, grids, correct_out_of_brain=False, side_threshold=0.2, group_filter=None):
    return compute_lesion_metadata(
        data_root=tmp_path,
        datasets=["siteA"],
        lesion_glob=_REAL_GLOB,
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        group_filter=group_filter,
        grids=grids,
        correct_out_of_brain=correct_out_of_brain,
        side_threshold=side_threshold,
    )


def test_compute_lesion_metadata_columns_are_four_per_grid_in_declaration_order(tmp_path):
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    grids = _make_two_grids(tmp_path)

    metadata, excluded_by_group = _compute(tmp_path, grids)

    assert excluded_by_group == []
    assert list(metadata.columns) == [
        "subject_id", "dataset",
        "lesion_volume_voxels_fine", "out_of_brain_fraction_fine",
        "laterality_index_fine", "lesion_side_fine",
        "lesion_volume_voxels_coarse", "out_of_brain_fraction_coarse",
        "laterality_index_coarse", "lesion_side_coarse",
    ]
    assert list(metadata.columns) == _metadata_columns(grids)


def test_compute_lesion_metadata_tiny_lesion_survives_on_fine_grid_and_vanishes_on_coarse(tmp_path):
    """The reason both grids exist at all: a lesion of a few voxels can be lost entirely by the
    coarse grid's nearest-neighbour subsampling, so a 0 there does NOT mean the mask is empty.
    Only the fine (native) count can tell a genuinely empty mask from a lost lesion - which is
    exactly the question that could not be answered for the 3 real subjects whose 2mm volume was
    0 (sub-STUKLFR0671/sub-STUKE0146/sub-STUKE0201).

    sub-...0001's voxels are all on EVEN fine indices, so each one is sampled by a coarse voxel
    and survives; sub-...0002's single voxel is on odd indices, which no coarse voxel samples.
    """
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 2), (4, 2, 2), (2, 4, 2)])
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0002", [(3, 3, 3)])
    grids = _make_two_grids(tmp_path)

    metadata, _ = _compute(tmp_path, grids)
    by_id = metadata.set_index("subject_id")

    survived = by_id.loc["sub-STUNIPD0001"]
    assert (survived["lesion_volume_voxels_fine"], survived["lesion_volume_voxels_coarse"]) == (3, 3)
    assert survived["lesion_side_fine"] == survived["lesion_side_coarse"] == "left"

    lost = by_id.loc["sub-STUNIPD0002"]
    assert lost["lesion_volume_voxels_fine"] == 1
    assert lost["lesion_side_fine"] == "left"
    # Lost on the coarse grid: no voxels at all, so nothing is measurable there - and every
    # coarse metric says so explicitly instead of reporting a misleading 0.0 side/fraction.
    assert lost["lesion_volume_voxels_coarse"] == 0
    assert np.isnan(lost["out_of_brain_fraction_coarse"])
    assert np.isnan(lost["laterality_index_coarse"])
    assert pd.isna(lost["lesion_side_coarse"])


def test_compute_lesion_metadata_fraction_is_measured_before_correction(tmp_path):
    """out_of_brain_fraction must reflect the RAW mask even when correct_out_of_brain zeroes those
    same voxels: correction drives the fraction to 0 by construction, so measuring it afterwards
    would leave the column unable to answer the only question it exists for (which subjects are
    contaminated enough to exclude). The volume, in contrast, is post-correction."""
    # 4 lesion voxels, 2 of them at k=0 (outside the brain on both grids) -> fraction 0.5
    _make_lesion_subject_on_fine_grid(
        tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 2), (4, 2, 2), (2, 2, 0), (4, 2, 0)]
    )
    grids = _make_two_grids(
        tmp_path,
        fine_brain_region=(slice(None), slice(None), slice(2, None)),
        coarse_brain_region=(slice(None), slice(None), slice(1, None)),
    )

    uncorrected, _ = _compute(tmp_path, grids, correct_out_of_brain=False)
    corrected, _ = _compute(tmp_path, grids, correct_out_of_brain=True)

    for grid_name in ("fine", "coarse"):
        assert uncorrected.loc[0, f"out_of_brain_fraction_{grid_name}"] == pytest.approx(0.5)
        assert corrected.loc[0, f"out_of_brain_fraction_{grid_name}"] == pytest.approx(0.5)
        assert uncorrected.loc[0, f"lesion_volume_voxels_{grid_name}"] == 4
        assert corrected.loc[0, f"lesion_volume_voxels_{grid_name}"] == 2


def test_compute_lesion_metadata_side_is_classified_after_correction(tmp_path):
    """An out-of-brain voxel is not lesion, so it must not be allowed to decide the side either.
    Here 3 right-hemisphere voxels sit outside the brain and 2 left-hemisphere ones inside it:
    uncorrected that is laterality_index = (2-3)/5 = -0.2 -> "right" (the boundary is not
    "both", see lesion_side_from_laterality_index), while after correction only the 2 genuine
    left voxels remain -> +1.0 -> "left". The flip is the assertion."""
    _make_lesion_subject_on_fine_grid(
        tmp_path, "siteA", "sub-STUNIPD0001",
        [(2, 2, 2), (4, 2, 2), (12, 2, 2), (14, 2, 2), (16, 2, 2)],
    )
    grids = _make_two_grids(
        tmp_path,
        fine_brain_region=(slice(0, 11), slice(None), slice(None)),
        coarse_brain_region=(slice(0, 6), slice(None), slice(None)),
    )

    uncorrected, _ = _compute(tmp_path, grids, correct_out_of_brain=False)
    corrected, _ = _compute(tmp_path, grids, correct_out_of_brain=True)

    for grid_name in ("fine", "coarse"):
        assert uncorrected.loc[0, f"laterality_index_{grid_name}"] == pytest.approx(-0.2)
        assert uncorrected.loc[0, f"lesion_side_{grid_name}"] == "right"
        assert corrected.loc[0, f"laterality_index_{grid_name}"] == pytest.approx(1.0)
        assert corrected.loc[0, f"lesion_side_{grid_name}"] == "left"
        assert corrected.loc[0, f"out_of_brain_fraction_{grid_name}"] == pytest.approx(0.6)


def test_compute_lesion_metadata_empty_mask_reports_nan_not_zero(tmp_path):
    """A genuinely empty mask: volume 0 is a real count, but the fraction/index/side are
    undefined, not 0 - reporting 0.0 for the fraction would place an empty mask among the
    cleanest subjects in the very distribution used to pick an exclusion threshold."""
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0002", [])
    grids = _make_two_grids(tmp_path)

    metadata, _ = _compute(tmp_path, grids)
    empty = metadata.set_index("subject_id").loc["sub-STUNIPD0002"]

    assert empty["lesion_volume_voxels_fine"] == 0
    assert np.isnan(empty["out_of_brain_fraction_fine"])
    assert np.isnan(empty["laterality_index_fine"])
    assert pd.isna(empty["lesion_side_fine"])


def test_compute_lesion_metadata_mask_entirely_outside_brain_empties_after_correction(tmp_path):
    """The case correct_out_of_brain exists to make visible: fraction 1.0 on the raw mask, and a
    volume of 0 after correction - the two columns together say "this mask is entirely outside
    the brain", which neither says alone."""
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 0), (4, 2, 0)])
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0002", [(2, 2, 2), (4, 2, 2)])
    grids = _make_two_grids(
        tmp_path,
        fine_brain_region=(slice(None), slice(None), slice(2, None)),
        coarse_brain_region=(slice(None), slice(None), slice(1, None)),
    )

    metadata, _ = _compute(tmp_path, grids, correct_out_of_brain=True)
    outside = metadata.set_index("subject_id").loc["sub-STUNIPD0001"]

    assert outside["out_of_brain_fraction_fine"] == pytest.approx(1.0)
    assert outside["lesion_volume_voxels_fine"] == 0
    assert pd.isna(outside["lesion_side_fine"])


def test_compute_lesion_metadata_reads_each_mask_once_regardless_of_grid_count(tmp_path, monkeypatch):
    """The whole point of measuring every grid in one pass: two grids must not mean two reads of
    the same file. Asserted directly, because nothing else would notice the regression - a
    per-grid re-read produces identical numbers, only slower."""
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0002", [(4, 2, 2)])
    grids = _make_two_grids(tmp_path)

    real_load = nib.load
    loaded: list[str] = []

    def counting_load(path, *args, **kwargs):
        loaded.append(str(path))
        return real_load(path, *args, **kwargs)

    monkeypatch.setattr("src.features.lesion.nib.load", counting_load)
    _compute(tmp_path, grids)

    mask_loads = [path for path in loaded if "label-lesion_mask" in path]
    assert len(mask_loads) == 2  # one per subject, not one per (subject, grid)


def test_compute_lesion_metadata_raises_when_every_mask_is_empty_on_a_grid(tmp_path):
    """The same aggregate safety net build_lesion_matrix has, per grid: one empty mask is a
    legitimate per-subject case, a whole cohort of them is a misconfiguration."""
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    grids = _make_two_grids(tmp_path)

    with pytest.raises(ValueError, match="every subject's lesion mask is empty on grid"):
        compute_lesion_metadata(
            data_root=tmp_path,
            datasets=["siteA"],
            lesion_glob=_REAL_GLOB,
            binarize_threshold=1.0,
            resample_interpolation="nearest",
            group_filter=None,
            grids=grids,
            correct_out_of_brain=False,
            side_threshold=0.2,
        )


def test_compute_lesion_metadata_raises_when_group_filter_leaves_no_subject(tmp_path):
    """group_filter excluding everyone leaves an empty frame, which must be an explicit error -
    otherwise an empty CSV would be written and read back as a complete cache."""
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    grids = _make_two_grids(tmp_path)

    with pytest.raises(ValueError, match="no subjects discovered"):
        _compute(tmp_path, grids, group_filter=["HC"])


def test_validate_grids_rejects_empty_duplicate_and_non_alphanumeric_names(tmp_path):
    fine, coarse = _make_two_grids(tmp_path)

    with pytest.raises(ValueError, match="at least one voxel grid"):
        validate_lesion_grids([])
    with pytest.raises(ValueError, match="duplicate grid name"):
        validate_lesion_grids([fine, fine])
    # A name carrying a separator would corrupt the CSV column it becomes a suffix of.
    with pytest.raises(ValueError, match="not alphanumeric"):
        validate_lesion_grids([LesionGrid("2 mm", fine.reference_template_path, fine.brain_mask_path), coarse])


# --- the hand-curated exclusion list ------------------------------------------------------------


def _build(tmp_path, template_path, excluded_subjects, datasets=("siteA",)):
    return build_lesion_matrix(
        data_root=tmp_path,
        datasets=list(datasets),
        reference_template_path=template_path,
        lesion_glob=_GLOB,
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        group_filter=None,
        excluded_subjects=excluded_subjects,
        correct_out_of_brain=False,
        brain_mask_path=None,
    )


def test_build_lesion_matrix_excluded_subjects_are_dropped_and_reported_separately(tmp_path):
    """The exclusion list replaces the two thresholds this function used to apply itself: the
    decision now lives in assets/metadata/excluded_subjects.csv, read by BOTH matrix pipelines,
    so they cannot disagree about who is in. Reported apart from excluded_by_group, because
    "not a stroke patient" and "a stroke patient we chose to drop" are different facts."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1), (1, 1, 2)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0003", [(5, 5, 5)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    X, metadata, _, excluded_by_group, excluded_by_list, _ = _build(
        tmp_path, template_path, frozenset({"sub-STUNIPD0002"})
    )

    assert excluded_by_group == []
    assert excluded_by_list == ["sub-STUNIPD0002"]
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0003"]
    assert X.shape[0] == 2


def test_build_lesion_matrix_excluded_subject_mask_is_never_read(tmp_path, monkeypatch):
    """The exclusion is applied to the discovered file list, before any mask is opened - not by
    dropping rows from an already-built matrix. Asserted directly: a post-hoc row drop would
    produce exactly the same matrix, only after paying to read every excluded subject."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 2)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    real_load = nib.load
    loaded = []

    def counting_load(path, *args, **kwargs):
        loaded.append(str(path))
        return real_load(path, *args, **kwargs)

    monkeypatch.setattr("src.features.lesion.nib.load", counting_load)
    _build(tmp_path, template_path, frozenset({"sub-STUNIPD0002"}))

    assert not any("sub-STUNIPD0002" in path for path in loaded)
    assert any("sub-STUNIPD0001" in path for path in loaded)


def test_build_lesion_matrix_raises_when_the_list_excludes_everyone(tmp_path):
    """An empty matrix must never be written: _drop_constant_features/save_matrix would happily
    accept one, and every downstream run would read a 0-subject artifact as legitimate."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 2)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    with pytest.raises(ValueError, match="no subjects left to build a matrix from"):
        _build(tmp_path, template_path, frozenset({"sub-STUNIPD0001", "sub-STUNIPD0002"}))


def test_build_lesion_matrix_reports_only_the_exclusions_in_its_own_scope(tmp_path):
    """The list covers every dataset in the project, while a run usually scopes a few - so
    excluded_by_list must name only the subjects this run actually discovered. Reporting the
    whole list would misstate what the matrix contains (e.g. "12 excluded" in a run whose
    cohort only ever contained 1 of them)."""
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject(tmp_path, "siteA", "sub-STUNIPD0002", [(1, 1, 2)])
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)

    _, metadata, _, _, excluded_by_list, _ = _build(
        tmp_path, template_path, frozenset({"sub-STUNIPD0002", "sub-STUKE0146", "sub-STUCLUK0001"})
    )

    assert excluded_by_list == ["sub-STUNIPD0002"]  # not the two subjects of other datasets
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]


def test_compute_lesion_metadata_midline_only_lesion_has_no_attributable_side(tmp_path):
    """A lesion confined to the exact midline voxel plane belongs to neither hemisphere (that
    plane is excluded from both, see _hemisphere_masks), so both counts are 0 and there is no
    side to attribute - distinct from an empty mask, since the volume here is NOT 0."""
    # fine grid: world_x(i) = i - 10, so i=10 is the midline plane; it maps to coarse i=5, also
    # that grid's own midline - the same subject is midline-only on both grids.
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0001", [(10, 2, 2), (10, 4, 2)])
    _make_lesion_subject_on_fine_grid(tmp_path, "siteA", "sub-STUNIPD0002", [(2, 2, 2)])
    grids = _make_two_grids(tmp_path)

    metadata, _ = _compute(tmp_path, grids)
    midline = metadata.set_index("subject_id").loc["sub-STUNIPD0001"]

    assert midline["lesion_volume_voxels_fine"] == 2  # a real lesion, not an empty mask
    assert np.isnan(midline["laterality_index_fine"])
    assert pd.isna(midline["lesion_side_fine"])
