"""Unit tests for Dataset identity: construction, subjects(), group_of()."""

import pytest

from src.retrieval.config import FilePatterns
from src.retrieval.dataset import Dataset

# These tests only exercise subjects()/group_of()/_require_subject(), none of
# which touch file_patterns - an empty registry is enough.
_EMPTY_PATTERNS = FilePatterns(patterns={})


def _make_dataset_root(tmp_path, subject_ids):
    root = tmp_path / "UNIPD" / "WashU"
    for subject_id in subject_ids:
        (root / subject_id / "anat").mkdir(parents=True)
    return tmp_path


def test_missing_root_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Dataset(tmp_path, "UNIPD/WashU", _EMPTY_PATTERNS)


def test_subjects_lists_all_sorted(tmp_path):
    project_root = _make_dataset_root(
        tmp_path, ["sub-STUNIPD0003", "sub-STUNIPD0001", "sub-STUNIPDHC0002"]
    )
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.subjects() == ["sub-STUNIPD0001", "sub-STUNIPD0003", "sub-STUNIPDHC0002"]


def test_subjects_filtered_by_group(tmp_path):
    project_root = _make_dataset_root(
        tmp_path, ["sub-STUNIPD0001", "sub-STUNIPDHC0002"]
    )
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.subjects(group="ST") == ["sub-STUNIPD0001"]
    assert ds.subjects(group="HC") == ["sub-STUNIPDHC0002"]
    assert ds.subjects(group="PD") == []


def test_subjects_excludes_non_conforming_folders(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-TEST"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.subjects() == ["sub-STUNIPD0001"]


def test_subjects_with_group_filter_does_not_crash_on_non_conforming_folder(tmp_path):
    """Regression: subjects(group=...) used to call group_of() on every
    sub-* folder, including non-conforming ones, crashing the whole request
    even though the real ST subjects were fine. Non-conforming folders must
    now be excluded before group_of() is ever reached."""
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-TEST"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.subjects(group="ST") == ["sub-STUNIPD0001"]


def test_non_conforming_subject_folders_lists_them(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-TEST", "sub-backup_old"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.non_conforming_subject_folders() == ["sub-TEST", "sub-backup_old"]


def test_non_conforming_subject_folders_empty_when_all_conform(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-STUNIPDHC0002"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.non_conforming_subject_folders() == []


def test_group_of_stroke_subject(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.group_of("sub-STUNIPD0001") == "ST"


def test_group_of_healthy_control(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPDHC0002"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.group_of("sub-STUNIPDHC0002") == "HC"


def test_group_of_malformed_subject_id_raises(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    with pytest.raises(ValueError, match="subject_id"):
        ds.group_of("not-a-subject-id")


def test_require_subject_raises_for_unknown_subject(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    with pytest.raises(ValueError, match="sub-STUNIPD9999"):
        ds._require_subject("sub-STUNIPD9999")


def test_require_subject_does_not_raise_for_known_subject(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001"])
    ds = Dataset(project_root, "UNIPD/WashU", _EMPTY_PATTERNS)
    ds._require_subject("sub-STUNIPD0001")
