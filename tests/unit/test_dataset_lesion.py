"""Unit tests for Dataset.resolve() and Dataset.available() - lesion file resolution."""

import pytest

from src.retrieval.config import FilePatterns
from src.retrieval.dataset import Dataset

_PATTERNS = FilePatterns(
    patterns={
        ("native", "T1w"): ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
        ("native", "FLAIR"): ["{subject_id}/anat/{subject_id}_FLAIR.nii.gz"],
        ("native", "lesion_roi"): [
            "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz",
            "{subject_id}/anat/{subject_id}_space-T1w_lesion_roi.nii.gz",
        ],
        ("mni", "lesion_mask"): [
            "derivatives/manual_masks/{subject_id}/anat/"
            "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
        ],
    }
)


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
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    resolved = ds.resolve("sub-STUNIPD0001", "native", "T1w")
    assert resolved is not None
    assert resolved.path.name == "sub-STUNIPD0001_T1w.nii.gz"
    assert resolved.extra_matches == ()


def test_resolve_native_lesion_roi_naming_variant(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    resolved = ds.resolve("sub-STUNIPD0001", "native", "lesion_roi")
    assert resolved is not None
    assert "lesion_roi" in resolved.path.name
    assert resolved.extra_matches == ()


def test_resolve_returns_none_when_missing_for_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    # lesion_roi is structurally registered, but sub-0002 has no matching file.
    assert ds.resolve("sub-STUNIPD0002", "native", "lesion_roi") is None


def test_resolve_flags_extra_matches_when_more_than_one_template_matches(tmp_path):
    """If a subject has files matching more than one registered template for
    the same (space, modality), the first (by priority) is used, and the
    rest are surfaced as extra_matches rather than silently dropped."""
    root = _make_washu_like(tmp_path)
    _touch(root / "UNIPD" / "WashU" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_roi.nii.gz")
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    resolved = ds.resolve("sub-STUNIPD0001", "native", "lesion_roi")
    assert resolved is not None
    assert resolved.path.name == "sub-STUNIPD0001_lesion_roi.nii.gz"  # first template in priority order
    assert len(resolved.extra_matches) == 1
    assert resolved.extra_matches[0].name == "sub-STUNIPD0001_space-T1w_lesion_roi.nii.gz"


def test_resolve_raises_for_unregistered_combination(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    with pytest.raises(ValueError, match="no file pattern registered"):
        ds.resolve("sub-STUNIPD0001", "native", "CT")  # not in _PATTERNS at all


def test_resolve_raises_for_unknown_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    with pytest.raises(ValueError, match="sub-STUNIPD9999"):
        ds.resolve("sub-STUNIPD9999", "native", "T1w")


def test_resolve_mni_mask_existing_file(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    resolved = ds.resolve("sub-STUNIPD0001", "mni", "lesion_mask")
    assert resolved is not None
    assert "label-lesion_mask" in resolved.path.name


def test_resolve_mni_mask_returns_none_when_missing_for_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    assert ds.resolve("sub-STUNIPD0002", "mni", "lesion_mask") is None


def test_available_true_when_at_least_one_subject_has_it(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU", _PATTERNS)
    assert ds.available("native", "T1w") is True
    assert ds.available("native", "lesion_roi") is True
    assert ds.available("mni", "lesion_mask") is True


def test_available_false_when_dataset_structurally_lacks_it(tmp_path):
    root = _make_psp_like(tmp_path)
    ds = Dataset(root, "UNIPD/PSP", _PATTERNS)
    assert ds.available("native", "lesion_roi") is False
    assert ds.available("native", "T1w") is False  # PSP-like fixture has no T1w at all
    assert ds.available("native", "FLAIR") is True
