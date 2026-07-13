"""Unit tests for Dataset.resolve() and Dataset.available() - lesion file resolution."""

import pytest

from src.retrieval.config import FilePatterns, RetrieveItem
from src.retrieval.dataset import Dataset


def _make_patterns(project_root):
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={
            ("lesion", "native", "T1w"): ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
            ("lesion", "native", "FLAIR"): ["{subject_id}/anat/{subject_id}_FLAIR.nii.gz"],
            ("lesion", "native", "lesion_roi"): [
                "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz",
                "{subject_id}/anat/{subject_id}_space-T1w_lesion_roi.nii.gz",
            ],
            ("lesion", "mni", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/"
                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
            ],
        },
    )


def _item(space: str, modality: str) -> RetrieveItem:
    return RetrieveItem(object="lesion", space=space, modality=modality)


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _make_washu_like(tmp_path):
    """Synthetic dataset mirroring WashU's convention:
    - sub-STUNIPD0001 has T1w + native lesion_roi (space-T1w variant) + MNI mask
    - sub-STUNIPD0002 has T1w but no lesion_roi (structurally supported, missing for this subject)
    """
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_T1w.nii.gz")
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_space-T1w_lesion_roi.nii.gz")
    _touch(
        root
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    _touch(root / "sub-STUNIPD0002" / "anat" / "sub-STUNIPD0002_T1w.nii.gz")
    return tmp_path


def _make_psp_like(tmp_path):
    """Synthetic dataset mirroring PSP's convention: no native lesion_roi at all."""
    root = tmp_path / "UNIPD" / "PSP"
    _touch(root / "sub-STUNIPD0100" / "anat" / "sub-STUNIPD0100_FLAIR.nii.gz")
    _touch(
        root
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0100"
        / "anat"
        / "sub-STUNIPD0100_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    return tmp_path


def test_resolve_native_existing_file(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    resolved = ds.resolve("sub-STUNIPD0001", _item("native", "T1w"))
    assert [p.name for p in resolved] == ["sub-STUNIPD0001_T1w.nii.gz"]


def test_resolve_native_lesion_roi_naming_variant(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    resolved = ds.resolve("sub-STUNIPD0001", _item("native", "lesion_roi"))
    assert len(resolved) == 1
    assert "lesion_roi" in resolved[0].name


def test_resolve_returns_empty_list_when_missing_for_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    # lesion_roi is structurally registered, but sub-0002 has no matching file.
    assert ds.resolve("sub-STUNIPD0002", _item("native", "lesion_roi")) == []


def test_resolve_returns_every_matching_template_when_more_than_one_exists(tmp_path):
    """If a subject has files matching more than one registered template for
    the same (space, modality), all of them are returned - there is no
    priority/ambiguity concept anymore (see FilePatterns docstring): grab
    every one that exists."""
    root = _make_washu_like(tmp_path)
    _touch(root / "UNIPD" / "WashU" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_roi.nii.gz")
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    resolved = ds.resolve("sub-STUNIPD0001", _item("native", "lesion_roi"))
    assert {p.name for p in resolved} == {
        "sub-STUNIPD0001_lesion_roi.nii.gz",
        "sub-STUNIPD0001_space-T1w_lesion_roi.nii.gz",
    }


def test_resolve_raises_for_unregistered_combination(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    with pytest.raises(ValueError, match="no file pattern registered"):
        ds.resolve("sub-STUNIPD0001", _item("native", "CT"))  # not registered at all


def test_resolve_returns_empty_list_for_unknown_subject(tmp_path):
    """resolve() no longer validates subject existence separately - an
    unknown/garbage subject_id simply has no matching file on disk, exactly
    like a known subject missing this specific file (see Dataset.resolve
    docstring: subject existence and space membership fold into the same
    filesystem check)."""
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.resolve("sub-STUNIPD9999", _item("native", "T1w")) == []


def test_resolve_mni_mask_existing_file(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    resolved = ds.resolve("sub-STUNIPD0001", _item("mni", "lesion_mask"))
    assert len(resolved) == 1
    assert "label-lesion_mask" in resolved[0].name


def test_resolve_mni_mask_returns_empty_list_when_missing_for_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.resolve("sub-STUNIPD0002", _item("mni", "lesion_mask")) == []


def test_describe_absence_not_found_when_folder_does_not_exist_at_all(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    # sub-STUNIPD0002 has no derivatives/manual_masks/sub-STUNIPD0002/ folder at all.
    assert ds.describe_absence("sub-STUNIPD0002", _item("mni", "lesion_mask")) == "not found"


def test_describe_absence_not_found_when_folder_has_other_content(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    # sub-STUNIPD0002's anat/ folder exists and has a T1w file, just not lesion_roi.
    assert ds.describe_absence("sub-STUNIPD0002", _item("native", "lesion_roi")) == "not found"


def test_describe_absence_empty_folder_when_folder_exists_with_nothing_in_it(tmp_path):
    root = _make_washu_like(tmp_path)
    (root / "UNIPD" / "WashU" / "sub-STUNIPD0099" / "anat").mkdir(parents=True)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.describe_absence("sub-STUNIPD0099", _item("native", "T1w")) == "empty folder"


def test_available_true_when_at_least_one_subject_has_it(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(root))
    assert ds.available("lesion", "native", "T1w") is True
    assert ds.available("lesion", "native", "lesion_roi") is True
    assert ds.available("lesion", "mni", "lesion_mask") is True


def test_available_false_when_dataset_structurally_lacks_it(tmp_path):
    root = _make_psp_like(tmp_path)
    ds = Dataset("UNIPD/PSP", _make_patterns(root))
    assert ds.available("lesion", "native", "lesion_roi") is False
    assert ds.available("lesion", "native", "T1w") is False  # PSP-like fixture has no T1w at all
    assert ds.available("lesion", "native", "FLAIR") is True
