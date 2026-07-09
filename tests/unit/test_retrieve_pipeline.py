"""Unit tests for src.pipeline.retrieve_data - synthetic fixtures, no EBRAIN mount needed."""

import pytest

from src.pipeline import retrieve_data
from src.retrieval.config import RetrievalConfig, RetrieveItem
from src.retrieval.dataset import Dataset


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _make_washu_like(tmp_path):
    """2 ST subjects (one with a T1w+mni mask, one missing the mni mask) + 1 HC subject."""
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_T1w.nii.gz")
    _touch(
        root
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    _touch(root / "sub-STUNIPD0002" / "anat" / "sub-STUNIPD0002_T1w.nii.gz")
    _touch(root / "sub-STUNIPDHC0003" / "anat" / "sub-STUNIPDHC0003_T1w.nii.gz")
    return tmp_path


def _make_config(tmp_path, project_root, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        project_root=project_root,
        datasets=["UNIPD/WashU"],
        group_filter=["ST"],
        subjects=None,
        retrieve=[RetrieveItem(space="mni", modality="lesion_mask")],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_validate_upfront_raises_for_unsupported_modality(tmp_path):
    project_root = _make_washu_like(tmp_path)
    config = _make_config(
        tmp_path, project_root, retrieve=[RetrieveItem(space="native", modality="FLAIR")]
    )
    datasets = retrieve_data._build_datasets(config)
    with pytest.raises(ValueError, match="FLAIR"):
        retrieve_data._validate_upfront(datasets, config)


def test_validate_upfront_raises_when_group_filter_matches_nobody(tmp_path):
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, group_filter=["PD"])
    datasets = retrieve_data._build_datasets(config)
    with pytest.raises(ValueError, match="group_filter"):
        retrieve_data._validate_upfront(datasets, config)


def test_validate_upfront_ignores_group_filter_when_subjects_explicit(tmp_path):
    project_root = _make_washu_like(tmp_path)
    # group_filter alone would match nobody, but it must be ignored since subjects is explicit.
    config = _make_config(
        tmp_path, project_root, group_filter=["PD"], subjects=["sub-STUNIPD0001"]
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)  # must not raise


def test_validate_upfront_raises_for_unknown_explicit_subject(tmp_path):
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, subjects=["sub-STUNIPD9999"])
    datasets = retrieve_data._build_datasets(config)
    with pytest.raises(ValueError, match="sub-STUNIPD9999"):
        retrieve_data._validate_upfront(datasets, config)


def test_select_subjects_no_filter_returns_everyone(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU")
    config = _make_config(tmp_path, project_root, group_filter=None)
    assert retrieve_data._select_subjects(ds, config) == ds.subjects()


def test_select_subjects_group_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU")
    config = _make_config(tmp_path, project_root, group_filter=["HC"])
    assert retrieve_data._select_subjects(ds, config) == ["sub-STUNIPDHC0003"]


def test_select_subjects_explicit_bypasses_group_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU")
    config = _make_config(
        tmp_path, project_root, group_filter=["PD"], subjects=["sub-STUNIPD0001", "sub-STUNIPD0002"]
    )
    assert retrieve_data._select_subjects(ds, config) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_copy_one_copies_new_file(tmp_path):
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"data")
    destination = tmp_path / "out" / "dest.nii.gz"
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=False, stats=stats)
    assert destination.read_bytes() == b"data"
    assert stats.copied == 1


def test_copy_one_skips_existing_when_overwrite_false(tmp_path):
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"new")
    destination = tmp_path / "dest.nii.gz"
    destination.write_bytes(b"old")
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=False, stats=stats)
    assert destination.read_bytes() == b"old"
    assert stats.skipped_existing == 1
    assert stats.copied == 0


def test_copy_one_overwrites_when_true(tmp_path):
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"new")
    destination = tmp_path / "dest.nii.gz"
    destination.write_bytes(b"old")
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=True, stats=stats)
    assert destination.read_bytes() == b"new"
    assert stats.copied == 1


def test_copy_one_logs_and_continues_on_failure(tmp_path, monkeypatch):
    def _raise_oserror(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(retrieve_data.shutil, "copy2", _raise_oserror)
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"data")
    destination = tmp_path / "dest.nii.gz"
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=False, stats=stats)  # must not raise
    assert stats.failed == 1
    assert stats.copied == 0


def test_full_run_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    project_root = _make_washu_like(tmp_path)
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(space="native", modality="T1w")],
        group_filter=None,
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)

    # All 3 subjects (2 ST + 1 HC) have T1w, all 3 should be copied.
    assert stats["UNIPD/WashU"].copied == 3
    assert stats["UNIPD/WashU"].missing == []

    copied_file = (
        tmp_path
        / "data"
        / "clinical_connectome"
        / "UNIPD"
        / "WashU"
        / "sub-STUNIPD0001"
        / "lesion"
        / "native"
        / "sub-STUNIPD0001_T1w.nii.gz"
    )
    assert copied_file.is_file()

    report_path = retrieve_data._write_report(config, stats)
    report_text = report_path.read_text()
    assert "UNIPD/WashU" in report_text
    assert "| UNIPD/WashU | 3 | 3 | 0 | 0 |" in report_text
