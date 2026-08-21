"""Unit tests for src/features/subject_discovery.py - plain files, no imaging fixtures needed."""

import pytest

from src.features.subject_discovery import discover_files_by_subject


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


def test_discover_files_by_subject_one_file_per_subject(tmp_path):
    dataset_root = tmp_path / "siteA"
    _touch(dataset_root / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    _touch(dataset_root / "sub-STUNIPD0002_label-lesion_mask.nii.gz")

    by_subject, excluded = discover_files_by_subject(tmp_path, "siteA", "*_label-lesion_mask.nii.gz", None)

    assert set(by_subject) == {"sub-STUNIPD0001", "sub-STUNIPD0002"}
    assert excluded == []


def test_discover_files_by_subject_two_files_same_subject_raises(tmp_path):
    """Regression: a leftover/duplicate file matching the same glob for the
    same subject_id used to be resolved arbitrarily (last file wins in the
    dict comprehension, alphabetically), silently. It must instead raise -
    this function's contract is exactly one file per subject per glob."""
    dataset_root = tmp_path / "siteA"
    _touch(dataset_root / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    _touch(dataset_root / "sub-STUNIPD0001_ses-2_label-lesion_mask.nii.gz")
    _touch(dataset_root / "sub-STUNIPD0002_label-lesion_mask.nii.gz")

    with pytest.raises(ValueError, match="sub-STUNIPD0001"):
        discover_files_by_subject(tmp_path, "siteA", "*_label-lesion_mask.nii.gz", None)


def test_discover_files_by_subject_ambiguous_check_runs_before_group_filter(tmp_path):
    """The ambiguity check must not be silently bypassed by group_filter
    excluding the ambiguous subject anyway - it's still a real data problem
    that needs a human to resolve, group_filter is not a way around it."""
    dataset_root = tmp_path / "siteA"
    _touch(dataset_root / "sub-STUNIPDHC0001_label-lesion_mask.nii.gz")
    _touch(dataset_root / "sub-STUNIPDHC0001_ses-2_label-lesion_mask.nii.gz")

    with pytest.raises(ValueError, match="sub-STUNIPDHC0001"):
        discover_files_by_subject(tmp_path, "siteA", "*_label-lesion_mask.nii.gz", ["ST"])


def test_discover_files_by_subject_applies_group_filter(tmp_path):
    dataset_root = tmp_path / "siteA"
    _touch(dataset_root / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    _touch(dataset_root / "sub-STUNIPDHC0001_label-lesion_mask.nii.gz")

    by_subject, excluded = discover_files_by_subject(tmp_path, "siteA", "*_label-lesion_mask.nii.gz", ["ST"])

    assert set(by_subject) == {"sub-STUNIPD0001"}
    assert excluded == ["sub-STUNIPDHC0001"]


def test_discover_files_by_subject_nested_glob_folder_matches_filename(tmp_path):
    """Real production glob shape (manual_masks/*/anat/...) - the subject directory
    segment must be cross-checked against the filename, not just used to discover files."""
    dataset_root = tmp_path / "siteA"
    _touch(dataset_root / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    _touch(dataset_root / "manual_masks" / "sub-STUNIPD0002" / "anat" / "sub-STUNIPD0002_label-lesion_mask.nii.gz")

    by_subject, excluded = discover_files_by_subject(
        tmp_path, "siteA", "manual_masks/*/anat/*_label-lesion_mask.nii.gz", None
    )

    assert set(by_subject) == {"sub-STUNIPD0001", "sub-STUNIPD0002"}
    assert excluded == []


def test_discover_files_by_subject_folder_filename_mismatch_raises(tmp_path):
    """Regression (HIGH #19, 2026-08): a file's subject_id used to be taken purely from
    its filename, never cross-checked against the subject directory it physically lives
    in - a file copied by hand into the wrong subject's folder (filename left unchanged,
    a realistic manual-repair mistake) would silently be attributed to the folder's
    subject_id's neighbor. Must raise instead of guessing which one is right."""
    dataset_root = tmp_path / "siteA"
    # sub-STUNIPD0042's file physically sits under sub-STUNIPD0043's folder.
    _touch(dataset_root / "manual_masks" / "sub-STUNIPD0043" / "anat" / "sub-STUNIPD0042_label-lesion_mask.nii.gz")

    with pytest.raises(ValueError, match="sub-STUNIPD0042.*sub-STUNIPD0043|sub-STUNIPD0043.*sub-STUNIPD0042"):
        discover_files_by_subject(tmp_path, "siteA", "manual_masks/*/anat/*_label-lesion_mask.nii.gz", None)
