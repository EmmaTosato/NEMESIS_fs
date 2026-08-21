"""Unit tests for src/features/functional.py - synthetic fixtures, no real data required."""

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.features.functional import (
    build_fc_matrix_from_masked,
    compute_parcel_coverage,
    discover_masked_fc_files,
    discover_subject_files,
    drop_constant_edges,
    find_compromised_nodes,
    load_atlas,
    mask_dataset_fc,
    mask_fc_by_lesion,
    mask_subject_fc,
    resample_lesion_to_atlas,
    resolve_atlas_paths,
    stack_fc_vectors,
    vectorize_upper_triangle,
)

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (14, 14, 14)  # big enough for a >256-voxel parcel (regression test below)


def _make_atlas_img(block_a=np.s_[0:7, 0:7, 0:7], block_b=np.s_[7:14, 7:14, 7:14]):
    """Two parcels: block_a has 7*7*7=343 voxels (>256, for the uint8-overflow regression)."""
    data = np.zeros(_SHAPE, dtype=np.int32)
    data[block_a] = 1
    data[block_b] = 2
    return nib.Nifti1Image(data, _AFFINE)


def _make_label_table(tmp_path, names=("Region_A", "Region_B")):
    path = tmp_path / "atlas_dseg.tsv"
    pd.DataFrame({"index": [1, 2], "label": list(names)}).to_csv(path, sep="\t", index=False)
    return path


def _all_voxels_in_block(block):
    """Every (x, y, z) coordinate inside a np.s_[...] 3D slice block."""
    xs, ys, zs = (range(s.start, s.stop) for s in block)
    return [(x, y, z) for x in xs for y in ys for z in zs]


def _make_lesion_img(lesioned_voxels):
    data = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesioned_voxels:
        data[voxel] = 1.0
    return nib.Nifti1Image(data, _AFFINE)


def _make_fc(node_names, values=None):
    n = len(node_names)
    if values is None:
        rng = np.random.default_rng(0)
        m = rng.normal(size=(n, n))
        values = (m + m.T) / 2
        np.fill_diagonal(values, 1.0)
    return pd.DataFrame(values, index=node_names, columns=node_names)


# --- load_atlas -------------------------------------------------------------


def test_load_atlas_missing_files_raise(tmp_path):
    with pytest.raises(FileNotFoundError, match="atlas_path"):
        load_atlas(tmp_path / "missing.nii.gz", tmp_path / "missing.tsv")


def test_load_atlas_bad_label_table_raises(tmp_path):
    atlas_path = tmp_path / "atlas.nii.gz"
    nib.save(_make_atlas_img(), atlas_path)
    bad_table = tmp_path / "bad.tsv"
    pd.DataFrame({"foo": [1], "bar": ["x"]}).to_csv(bad_table, sep="\t", index=False)

    with pytest.raises(ValueError, match="must have 'index' and 'label'"):
        load_atlas(atlas_path, bad_table)


def test_load_atlas_valid(tmp_path):
    atlas_path = tmp_path / "atlas.nii.gz"
    nib.save(_make_atlas_img(), atlas_path)
    label_table_path = _make_label_table(tmp_path)

    atlas_img, label_table = load_atlas(atlas_path, label_table_path)
    assert atlas_img.shape == _SHAPE
    assert list(label_table["label"]) == ["Region_A", "Region_B"]


# --- compute_parcel_coverage (+ the two regression bugs) --------------------


def test_compute_parcel_coverage_no_lesion():
    atlas_img = _make_atlas_img()
    healthy_img = nib.Nifti1Image(np.ones(_SHAPE, dtype=np.int32), _AFFINE)
    coverage = compute_parcel_coverage(atlas_img, [1, 2], healthy_img)
    assert coverage == pytest.approx([1.0, 1.0])


def test_compute_parcel_coverage_uint8_overflow_regression():
    """Regression: a >256-voxel parcel must not silently wrap module 256 in the
    voxel-counting step (docs/debugging/debug_23_07_26.md #1)."""
    atlas_img = _make_atlas_img()  # parcel 1 is the 7x7x7=343 voxel block [0:7, 0:7, 0:7] (> 256)
    healthy = np.ones(_SHAPE, dtype=np.int32)
    # Lesion 7 voxels, all within parcel 1's block (indices 0-6 on every axis).
    for i in range(7):
        healthy[0, 0, i] = 0
    healthy_img = nib.Nifti1Image(healthy, _AFFINE)

    coverage = compute_parcel_coverage(atlas_img, [1, 2], healthy_img)
    assert coverage[0] == pytest.approx((343 - 7) / 343)
    assert coverage[1] == pytest.approx(1.0)


def test_compute_parcel_coverage_fully_lesioned_parcel_regression():
    """Regression: a parcel with zero surviving healthy voxels must read
    coverage=0.0, not disappear/misalign against the unmasked parcel list
    (docs/debugging/debug_23_07_26.md #2)."""
    atlas_img = _make_atlas_img()
    healthy = np.ones(_SHAPE, dtype=np.int32)
    healthy[0:7, 0:7, 0:7] = 0  # parcel 1 entirely lesioned
    healthy_img = nib.Nifti1Image(healthy, _AFFINE)

    coverage = compute_parcel_coverage(atlas_img, [1, 2], healthy_img)
    assert coverage[0] == 0.0
    assert coverage[1] == pytest.approx(1.0)


# --- resample_lesion_to_atlas ------------------------------------------------


def test_resample_lesion_to_atlas_binarizes():
    atlas_img = _make_atlas_img()
    lesion_img = _make_lesion_img([(1, 1, 1), (2, 2, 2)])
    lesion_data = resample_lesion_to_atlas(lesion_img, atlas_img, "nearest", 0.5)
    assert lesion_data.dtype == np.int32
    assert lesion_data[1, 1, 1] == 1
    assert lesion_data[0, 0, 0] == 0
    assert lesion_data.sum() == 2


# --- find_compromised_nodes / mask_fc_by_lesion / vectorize_upper_triangle --


def test_find_compromised_nodes():
    node_names = np.array(["A", "B", "C"])
    coverage = np.array([0.9, 0.4, 0.5])
    compromised = find_compromised_nodes(coverage, node_names, min_coverage=0.5)
    assert list(compromised) == ["B"]  # 0.5 is not < 0.5, only B (0.4) qualifies


def test_mask_fc_by_lesion_sets_nan_rows_and_columns():
    node_names = np.array(["A", "B", "C"])
    fc = _make_fc(node_names)
    fc_masked = mask_fc_by_lesion(fc, node_names, np.array(["B"]))

    assert fc_masked.loc["B"].isna().all()  # whole row B: NaN
    assert fc_masked["B"].isna().all()  # whole column B: NaN
    # A-A and A-C (not involving B) must survive untouched
    assert fc_masked.loc["A", "A"] == fc.loc["A", "A"]
    assert fc_masked.loc["A", "C"] == fc.loc["A", "C"]
    assert fc_masked.loc["C", "A"] == fc.loc["C", "A"]
    assert not fc.loc["B"].isna().any()  # original untouched


def test_mask_fc_by_lesion_misaligned_raises():
    node_names = np.array(["A", "B", "C"])
    fc = _make_fc(node_names)
    fc_shuffled = fc.iloc[[1, 0, 2]]  # row order no longer matches node_names

    with pytest.raises(ValueError, match="do not match"):
        mask_fc_by_lesion(fc_shuffled, node_names, np.array(["B"]))


def test_vectorize_upper_triangle():
    node_names = np.array(["A", "B", "C"])
    values = np.array([[1.0, 0.2, 0.3], [0.2, 1.0, 0.4], [0.3, 0.4, 1.0]])
    fc = pd.DataFrame(values, index=node_names, columns=node_names)

    vector = vectorize_upper_triangle(fc, node_names)
    assert list(vector.index) == ["A__B", "A__C", "B__C"]
    assert list(vector.values) == pytest.approx([0.2, 0.3, 0.4])


# --- mask_subject_fc (end-to-end, single subject) ---------------------------


def test_mask_subject_fc_end_to_end():
    atlas_img = _make_atlas_img()
    label_ids = [1, 2]
    node_names = np.array(["Region_A", "Region_B"])
    lesion_img = _make_lesion_img(_all_voxels_in_block(np.s_[0:7, 0:7, 0:7]))  # parcel 1 entirely lesioned

    fc = _make_fc(node_names)
    fc_masked, compromised_names = mask_subject_fc(
        lesion_img, fc, atlas_img, label_ids, node_names, min_coverage=0.5,
        resample_interpolation="nearest", binarize_threshold=0.5,
    )

    assert list(compromised_names) == ["Region_A"]
    assert fc_masked.loc["Region_A"].isna().all()  # whole row, including Region_A-Region_B
    # Region_B's only surviving value in a 2-node atlas is its own diagonal (Region_A is compromised)
    assert fc_masked.loc["Region_B", "Region_B"] == fc.loc["Region_B", "Region_B"]


# --- resolve_atlas_paths -----------------------------------------------------


def test_resolve_atlas_paths():
    nii_path, tsv_path = resolve_atlas_paths("assets/atlases/fmriprep", "Yan200TianS2Buckner7N")
    assert str(nii_path) == "assets/atlases/fmriprep/atlas-Yan200TianS2Buckner7N/atlas-Yan200TianS2Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz"
    assert str(tsv_path) == "assets/atlases/fmriprep/atlas-Yan200TianS2Buckner7N/atlas-Yan200TianS2Buckner7N_dseg.tsv"


# --- discover_subject_files ---------------------------------------------------


def _make_dataset_dir(tmp_path, dataset, subjects_with_lesion, subjects_with_fc, combo="ComboX"):
    dataset_root = tmp_path / dataset
    for subject in subjects_with_lesion:
        d = dataset_root / "manual_masks" / subject / "anat"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{subject}_label-lesion_mask.nii.gz").touch()
    for subject in subjects_with_fc:
        d = dataset_root / "features" / subject / "func"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{subject}_FC-pearson_atlas-{combo}.csv").touch()
    return tmp_path


_LESION_GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"
_FC_GLOB_TEMPLATE = "features/*/func/*_FC-pearson_atlas-{combo}.csv"


def test_discover_subject_files_skips_subjects_missing_lesion(tmp_path):
    _make_dataset_dir(
        tmp_path, "siteA",
        subjects_with_lesion=["sub-01", "sub-02"],
        subjects_with_fc=["sub-01", "sub-02", "sub-03"],
        combo="ComboX",
    )

    subject_files, missing_lesion, excluded_by_group = discover_subject_files(
        tmp_path, "siteA", "ComboX", _LESION_GLOB, _FC_GLOB_TEMPLATE, group_filter=None
    )
    assert set(subject_files) == {"sub-01", "sub-02"}
    assert missing_lesion == ["sub-03"]
    assert excluded_by_group == []


def test_discover_subject_files_none_usable_raises(tmp_path):
    _make_dataset_dir(tmp_path, "siteA", subjects_with_lesion=[], subjects_with_fc=["sub-01"], combo="ComboX")

    with pytest.raises(ValueError, match="no subject"):
        discover_subject_files(tmp_path, "siteA", "ComboX", _LESION_GLOB, _FC_GLOB_TEMPLATE, group_filter=None)


def test_discover_subject_files_no_fc_raises(tmp_path):
    (tmp_path / "siteA").mkdir()
    with pytest.raises(FileNotFoundError, match="no FC files"):
        discover_subject_files(tmp_path, "siteA", "ComboX", _LESION_GLOB, _FC_GLOB_TEMPLATE, group_filter=None)


# --- discover_subject_files: group_filter (ST vs HC, regression for the WashU HC bug) -----


def test_discover_subject_files_group_filter_excludes_hc_not_as_missing_lesion(tmp_path):
    """Regression: WashU's features/ tree holds both patients (ST) and healthy
    controls (HC) side by side. An HC subject has an FC file but, being
    healthy, never a lesion mask - without group_filter it would land in
    missing_lesion (wrongly implying "a patient whose mask wasn't drawn").
    With group_filter=["ST"] it must be excluded before that distinction is
    even computed, and reported separately as excluded_by_group."""
    _make_dataset_dir(
        tmp_path, "siteA",
        subjects_with_lesion=["sub-STUNIPD0001"],
        subjects_with_fc=["sub-STUNIPD0001", "sub-STUNIPDHC0001"],
        combo="ComboX",
    )

    subject_files, missing_lesion, excluded_by_group = discover_subject_files(
        tmp_path, "siteA", "ComboX", _LESION_GLOB, _FC_GLOB_TEMPLATE, group_filter=["ST"]
    )
    assert set(subject_files) == {"sub-STUNIPD0001"}
    assert missing_lesion == []
    assert excluded_by_group == ["sub-STUNIPDHC0001"]


def test_discover_subject_files_group_filter_none_keeps_old_missing_lesion_behavior(tmp_path):
    """Without an explicit group_filter, the HC subject above still surfaces
    (as missing_lesion, not silently dropped) - group_filter=None is a
    deliberate opt-out, not an implicit exclusion of HC."""
    _make_dataset_dir(
        tmp_path, "siteA",
        subjects_with_lesion=["sub-STUNIPD0001"],
        subjects_with_fc=["sub-STUNIPD0001", "sub-STUNIPDHC0001"],
        combo="ComboX",
    )

    subject_files, missing_lesion, excluded_by_group = discover_subject_files(
        tmp_path, "siteA", "ComboX", _LESION_GLOB, _FC_GLOB_TEMPLATE, group_filter=None
    )
    assert set(subject_files) == {"sub-STUNIPD0001"}
    assert missing_lesion == ["sub-STUNIPDHC0001"]
    assert excluded_by_group == []


def test_discover_subject_files_group_filter_can_include_hc(tmp_path):
    """group_filter=["ST", "HC"] opts back in - e.g. Task 3's HC comparison
    cohort - rather than the mechanism being ST-only by construction."""
    _make_dataset_dir(
        tmp_path, "siteA",
        subjects_with_lesion=["sub-STUNIPD0001", "sub-STUNIPDHC0001"],
        subjects_with_fc=["sub-STUNIPD0001", "sub-STUNIPDHC0001"],
        combo="ComboX",
    )

    subject_files, missing_lesion, excluded_by_group = discover_subject_files(
        tmp_path, "siteA", "ComboX", _LESION_GLOB, _FC_GLOB_TEMPLATE, group_filter=["ST", "HC"]
    )
    assert set(subject_files) == {"sub-STUNIPD0001", "sub-STUNIPDHC0001"}
    assert excluded_by_group == []


# --- stack_fc_vectors ---------------------------------------------------------


def test_stack_fc_vectors():
    vectors = {
        "sub-01": pd.Series([0.1, 0.2], index=["A__B", "A__C"]),
        "sub-02": pd.Series([0.3, np.nan], index=["A__B", "A__C"]),
    }
    X, metadata, edge_names = stack_fc_vectors(vectors)
    assert edge_names == ["A__B", "A__C"]
    assert list(metadata["subject_id"]) == ["sub-01", "sub-02"]
    assert X.shape == (2, 2)
    assert np.isnan(X[1, 1])


def test_stack_fc_vectors_misaligned_edges_raises():
    vectors = {
        "sub-01": pd.Series([0.1, 0.2], index=["A__B", "A__C"]),
        "sub-02": pd.Series([0.3, 0.4], index=["A__C", "A__B"]),  # different order
    }
    with pytest.raises(ValueError, match="do not match"):
        stack_fc_vectors(vectors)


# --- drop_constant_edges -------------------------------------------------------


def test_drop_constant_edges_drops_identical_column():
    edge_names = ["A__B", "A__C", "B__C"]
    X = np.array(
        [
            [0.1, 5.0, 0.9],
            [0.2, 5.0, 0.8],
            [0.3, 5.0, 0.7],
        ]
    )
    X_filtered, kept_names, dropped_info = drop_constant_edges(X, edge_names)
    assert kept_names == ["A__B", "B__C"]
    assert dropped_info == [("A__C", 5.0)]
    assert X_filtered.shape == (3, 2)


def test_drop_constant_edges_keeps_columns_with_any_nan():
    edge_names = ["A__B", "A__C"]
    X = np.array(
        [
            [5.0, np.nan],
            [5.0, 0.1],
            [5.0, 0.2],
        ]
    )
    # A__B is identical among fully-observed rows but has no NaN at all -> constant, dropped.
    # A__C has a NaN -> kept unconditionally, even though the non-NaN values differ.
    X_filtered, kept_names, dropped_info = drop_constant_edges(X, edge_names)
    assert kept_names == ["A__C"]
    assert dropped_info == [("A__B", 5.0)]


def test_drop_constant_edges_none_found():
    edge_names = ["A__B", "A__C"]
    X = np.array([[0.1, 0.2], [0.3, 0.4]])
    X_filtered, kept_names, dropped_info = drop_constant_edges(X, edge_names)
    assert kept_names == edge_names
    assert dropped_info == []
    np.testing.assert_array_equal(X_filtered, X)


# --- discover_masked_fc_files / build_fc_matrix_from_masked -------------------


def test_discover_masked_fc_files_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="no masked FC files"):
        discover_masked_fc_files(tmp_path)


def test_build_fc_matrix_from_masked_end_to_end(tmp_path):
    node_names = ["A", "B", "C"]
    fc1 = pd.DataFrame([[1.0, 0.1, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]], index=node_names, columns=node_names)
    fc2 = pd.DataFrame([[1.0, 0.1, 0.9], [0.1, 1.0, 0.3], [0.9, 0.3, 1.0]], index=node_names, columns=node_names)
    fc2.loc["B", :] = np.nan
    fc2.loc[:, "B"] = np.nan

    fc1.to_csv(tmp_path / "sub-01_masked_fc.csv")
    fc2.to_csv(tmp_path / "sub-02_masked_fc.csv")

    X, metadata, edge_names, dropped_info = build_fc_matrix_from_masked(tmp_path)

    assert list(metadata["subject_id"]) == ["sub-01", "sub-02"]
    assert edge_names == ["A__B", "A__C", "B__C"]
    assert X.shape == (2, 3)
    assert np.isnan(X[1, 0]) and np.isnan(X[1, 2])  # A__B, B__C for sub-02
    assert not np.isnan(X[1, 1])  # A__C untouched
    assert X[0, 1] == pytest.approx(0.2) and X[1, 1] == pytest.approx(0.9)  # A__C differs -> not constant
    assert dropped_info == []


def test_build_fc_matrix_from_masked_node_mismatch_raises(tmp_path):
    node_names_a = ["A", "B"]
    node_names_b = ["B", "A"]
    fc1 = pd.DataFrame([[1.0, 0.1], [0.1, 1.0]], index=node_names_a, columns=node_names_a)
    fc2 = pd.DataFrame([[1.0, 0.1], [0.1, 1.0]], index=node_names_b, columns=node_names_b)
    fc1.to_csv(tmp_path / "sub-01_masked_fc.csv")
    fc2.to_csv(tmp_path / "sub-02_masked_fc.csv")

    with pytest.raises(ValueError, match="does not match the reference subject"):
        build_fc_matrix_from_masked(tmp_path)


# --- mask_dataset_fc (orchestrator) -------------------------------------------


def test_mask_dataset_fc_end_to_end(tmp_path):
    atlas_path = tmp_path / "atlas.nii.gz"
    nib.save(_make_atlas_img(), atlas_path)
    label_table_path = _make_label_table(tmp_path)
    node_names = ["Region_A", "Region_B"]

    data_root = tmp_path / "data"
    combo = "ComboX"
    for subject, lesioned in [("sub-01", True), ("sub-02", False)]:
        lesion_dir = data_root / "siteA" / "manual_masks" / subject / "anat"
        lesion_dir.mkdir(parents=True, exist_ok=True)
        voxels = _all_voxels_in_block(np.s_[0:7, 0:7, 0:7]) if lesioned else []
        nib.save(_make_lesion_img(voxels), lesion_dir / f"{subject}_label-lesion_mask.nii.gz")

        fc_dir = data_root / "siteA" / "features" / subject / "func"
        fc_dir.mkdir(parents=True, exist_ok=True)
        _make_fc(node_names).to_csv(fc_dir / f"{subject}_FC-pearson_atlas-{combo}.csv", sep="\t")

    output_dir = tmp_path / "out"
    summary, missing_lesion, excluded_by_group, failed = mask_dataset_fc(
        data_root=data_root,
        dataset="siteA",
        atlas_path=atlas_path,
        label_table_path=label_table_path,
        atlas_combo=combo,
        lesion_glob=_LESION_GLOB,
        fc_glob_template=_FC_GLOB_TEMPLATE,
        min_coverage=0.5,
        resample_interpolation="nearest",
        binarize_threshold=0.5,
        output_dir=output_dir,
        group_filter=None,
    )

    assert missing_lesion == []
    assert excluded_by_group == []
    assert failed == {}
    assert set(summary["subject_id"]) == {"sub-01", "sub-02"}
    sub01_row = summary[summary["subject_id"] == "sub-01"].iloc[0]
    sub02_row = summary[summary["subject_id"] == "sub-02"].iloc[0]
    assert sub01_row["n_compromised_nodes"] == 1
    assert sub02_row["n_compromised_nodes"] == 0
    assert (output_dir / "sub-01_masked_fc.csv").is_file()
    assert (output_dir / "sub-02_masked_fc.csv").is_file()


def test_mask_dataset_fc_one_bad_subject_does_not_abort_the_others(tmp_path):
    """Regression (HIGH #9, 2026-08): a single subject with a mismatched FC node
    order (or a corrupt lesion/FC file) used to raise straight out of the per-subject
    loop, discarding every subject already masked earlier in the same call. Now
    isolated per subject (lesson #21) - the good subject stays written, the bad one
    is reported in `failed`, not silently dropped nor fatal."""
    atlas_path = tmp_path / "atlas.nii.gz"
    nib.save(_make_atlas_img(), atlas_path)
    label_table_path = _make_label_table(tmp_path)
    node_names = ["Region_A", "Region_B"]

    data_root = tmp_path / "data"
    combo = "ComboX"
    for subject, lesioned in (("sub-01", True), ("sub-02", False)):
        lesion_dir = data_root / "siteA" / "manual_masks" / subject / "anat"
        lesion_dir.mkdir(parents=True, exist_ok=True)
        voxels = _all_voxels_in_block(np.s_[0:7, 0:7, 0:7]) if lesioned else []
        nib.save(_make_lesion_img(voxels), lesion_dir / f"{subject}_label-lesion_mask.nii.gz")

        fc_dir = data_root / "siteA" / "features" / subject / "func"
        fc_dir.mkdir(parents=True, exist_ok=True)
        _make_fc(node_names).to_csv(fc_dir / f"{subject}_FC-pearson_atlas-{combo}.csv", sep="\t")

    # sub-02's FC file has its node order scrambled relative to the atlas - the exact
    # per-subject failure mode described in the audit finding.
    bad_fc_path = data_root / "siteA" / "features" / "sub-02" / "func" / f"sub-02_FC-pearson_atlas-{combo}.csv"
    _make_fc(list(reversed(node_names))).to_csv(bad_fc_path, sep="\t")

    output_dir = tmp_path / "out"
    summary, missing_lesion, excluded_by_group, failed = mask_dataset_fc(
        data_root=data_root,
        dataset="siteA",
        atlas_path=atlas_path,
        label_table_path=label_table_path,
        atlas_combo=combo,
        lesion_glob=_LESION_GLOB,
        fc_glob_template=_FC_GLOB_TEMPLATE,
        min_coverage=0.5,
        resample_interpolation="nearest",
        binarize_threshold=0.5,
        output_dir=output_dir,
        group_filter=None,
    )

    assert set(summary["subject_id"]) == {"sub-01"}
    assert (output_dir / "sub-01_masked_fc.csv").is_file()
    assert not (output_dir / "sub-02_masked_fc.csv").exists()
    assert set(failed) == {"sub-02"}
    assert "node order" in failed["sub-02"]
