"""Unit tests for Dataset.native() and Dataset.mni_mask() - lesion resolution and edge cases."""

import pytest

from src.retrieval.dataset import Dataset


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


def test_native_resolves_existing_file(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU")
    path = ds.native("sub-STUNIPD0001", "T1w")
    assert path is not None
    assert path.name == "sub-STUNIPD0001_T1w.nii.gz"


def test_native_resolves_lesion_roi_naming_variant(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU")
    path = ds.native("sub-STUNIPD0001", "lesion_roi")
    assert path is not None
    assert "lesion_roi" in path.name


def test_native_returns_none_when_missing_for_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU")
    # T1w is structurally available in this dataset, but sub-0002 has no lesion_roi.
    assert ds.native("sub-STUNIPD0002", "lesion_roi") is None


def test_native_raises_when_modality_not_supported_by_dataset(tmp_path):
    root = _make_psp_like(tmp_path)
    ds = Dataset(root, "UNIPD/PSP")
    with pytest.raises(ValueError, match="lesion_roi"):
        ds.native("sub-STUNIPD0100", "lesion_roi")


def test_native_raises_for_unknown_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU")
    with pytest.raises(ValueError, match="sub-STUNIPD9999"):
        ds.native("sub-STUNIPD9999", "T1w")


def test_mni_mask_resolves_existing_file(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU")
    path = ds.mni_mask("sub-STUNIPD0001")
    assert path is not None
    assert "label-lesion_mask" in path.name


def test_mni_mask_returns_none_when_missing_for_subject(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU")
    assert ds.mni_mask("sub-STUNIPD0002") is None


def test_mni_mask_raises_when_dataset_has_no_derivatives(tmp_path):
    root = tmp_path / "UNIPD" / "NoDerivatives"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_T1w.nii.gz")
    ds = Dataset(tmp_path, "UNIPD/NoDerivatives")
    with pytest.raises(ValueError, match="derivatives"):
        ds.mni_mask("sub-STUNIPD0001")


def test_available_sequences_discovered_from_disk(tmp_path):
    root = _make_washu_like(tmp_path)
    ds = Dataset(root, "UNIPD/WashU")
    assert ds.available_sequences() == {"T1w", "lesion_roi"}
