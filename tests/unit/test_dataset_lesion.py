"""Unit tests for Dataset.resolve() and Dataset.available() - lesion file resolution.

Scoped to `manual_masks` only (native/raw retrieval is descoped this round -
see docs/dev/retrieval.md "This round vs. a future native/raw round")."""

import pytest

from src.retrieval.config import FilePatterns, RetrieveItem
from src.retrieval.dataset import Dataset


def _make_patterns(project_root):
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={
            ("lesion", "manual_masks", "anat", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz",
                "derivatives/manual_masks/{subject_id}/anat/"
                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz",
            ],
        },
    )


def _item(suffix: str) -> RetrieveItem:
    return RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix=suffix)


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _make_washu_like(tmp_path):
    """Synthetic dataset mirroring WashU's convention:
    - sub-STUNIPD0001 has a manual_masks lesion mask (space-tagged variant)
    - sub-STUNIPD0002 has no manual_masks folder at all for this subject
      (structurally supported, missing for this subject)
    """
    root = tmp_path / "UNIPD" / "WashU"
    _touch(
        root
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    return tmp_path


def _make_psp_like(tmp_path):
    """Synthetic dataset where the dataset root exists (has_object("lesion")
    is True) but there is no derivatives/manual_masks/ tree at all -
    structurally lacks the lesion_mask leaf despite the object root being
    present."""
    root = tmp_path / "UNIPD" / "PSP"
    (root / "sub-STUNIPD0100").mkdir(parents=True)
    return tmp_path


def test_resolve_manual_masks_lesion_mask_existing_file(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    resolved = ds.resolve("sub-STUNIPD0001", _item("lesion_mask"))
    assert len(resolved) == 1
    assert "label-lesion_mask" in resolved[0].name


def test_resolve_manual_masks_returns_empty_list_when_missing_for_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.resolve("sub-STUNIPD0002", _item("lesion_mask")) == []


def test_resolve_returns_every_matching_template_when_more_than_one_exists(tmp_path):
    """If a subject has files matching more than one registered template for
    the same leaf, all of them are returned - there is no priority/ambiguity
    concept (see FilePatterns docstring): grab every one that exists."""
    root = _make_washu_like(tmp_path)
    _touch(
        root
        / "UNIPD"
        / "WashU"
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0001_label-lesion_mask.nii.gz"
    )
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    resolved = ds.resolve("sub-STUNIPD0001", _item("lesion_mask"))
    assert {p.name for p in resolved} == {
        "sub-STUNIPD0001_label-lesion_mask.nii.gz",
        "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz",
    }


def test_resolve_raises_for_unregistered_combination(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    with pytest.raises(ValueError, match="no file pattern registered"):
        ds.resolve("sub-STUNIPD0001", _item("CT"))  # not registered at all


def test_resolve_returns_empty_list_for_unknown_subject(tmp_path):
    """resolve() no longer validates subject existence separately - an
    unknown/garbage subject_id simply has no matching file on disk, exactly
    like a known subject missing this specific file (see Dataset.resolve
    docstring: subject existence and pipeline membership fold into the same
    filesystem check)."""
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.resolve("sub-STUNIPD9999", _item("lesion_mask")) == []


def test_describe_absence_not_found_when_folder_does_not_exist_at_all(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    # sub-STUNIPD0002 has no derivatives/manual_masks/sub-STUNIPD0002/ folder at all.
    assert ds.describe_absence("sub-STUNIPD0002", _item("lesion_mask")) == "not found"


def test_describe_absence_not_found_when_folder_has_other_content(tmp_path):
    root = _make_washu_like(tmp_path)
    _touch(
        root
        / "UNIPD"
        / "WashU"
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0002"
        / "anat"
        / "sub-STUNIPD0002_some_other_file.nii.gz"
    )
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.describe_absence("sub-STUNIPD0002", _item("lesion_mask")) == "not found"


def test_describe_absence_empty_folder_when_folder_exists_with_nothing_in_it(tmp_path):
    root = _make_washu_like(tmp_path)
    (root / "UNIPD" / "WashU" / "derivatives" / "manual_masks" / "sub-STUNIPD0099" / "anat").mkdir(parents=True)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.describe_absence("sub-STUNIPD0099", _item("lesion_mask")) == "empty folder"


def test_available_true_when_at_least_one_subject_has_it(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.available(_item("lesion_mask")) is True


def test_available_false_for_cross_subject_mismatch(tmp_path):
    """Regression: a file whose folder subject and filename subject disagree
    (a real-world mis-copy, e.g. sub-A/anat/sub-B_label-lesion_mask.nii.gz)
    used to be reported as "available" - the template's two {subject_id}
    occurrences were replaced with two independent glob wildcards, matching
    regardless of whether the two actually agreed with each other. No real
    subject would ever produce this path via resolve()."""
    root = tmp_path
    _touch(
        root
        / "UNIPD"
        / "WashU"
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0002_label-lesion_mask.nii.gz"
    )
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.available(_item("lesion_mask")) is False


def test_available_false_when_dataset_structurally_lacks_it(tmp_path):
    root = _make_psp_like(tmp_path)
    ds = Dataset("UNIPD/PSP", _make_patterns(root))
    assert ds.available(_item("lesion_mask")) is False
