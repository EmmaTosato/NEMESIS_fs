"""Unit tests for Dataset identity: construction, subjects(), group_of()."""

import pytest

from src.retrieval.config import FilePatterns
from src.retrieval.dataset import Dataset


def _make_patterns(project_root):
    """Minimal registry: one object (lesion), one space (native), one
    modality (T1w) - enough for subjects()/non_conforming_subject_folders()
    to derive where subject folders live (they no longer assume a fixed
    root; see Dataset._subject_container)."""
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={("lesion", "native", "T1w"): ["{subject_id}/anat/{subject_id}_T1w.nii.gz"]},
    )


def _make_dataset_root(tmp_path, subject_ids):
    root = tmp_path / "UNIPD" / "WashU"
    for subject_id in subject_ids:
        (root / subject_id / "anat").mkdir(parents=True)
    return tmp_path


def test_missing_root_raises(tmp_path):
    """Dataset construction itself touches no filesystem - the missing root
    only surfaces once something actually needs it (subjects(), resolve(),
    ...)."""
    ds = Dataset("UNIPD/WashU", _make_patterns(tmp_path))
    with pytest.raises(FileNotFoundError):
        ds.subjects("lesion", "native")


def test_subjects_lists_all_sorted(tmp_path):
    project_root = _make_dataset_root(
        tmp_path, ["sub-STUNIPD0003", "sub-STUNIPD0001", "sub-STUNIPDHC0002"]
    )
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    assert ds.subjects("lesion", "native") == ["sub-STUNIPD0001", "sub-STUNIPD0003", "sub-STUNIPDHC0002"]


def test_subjects_filtered_by_group(tmp_path):
    project_root = _make_dataset_root(
        tmp_path, ["sub-STUNIPD0001", "sub-STUNIPDHC0002"]
    )
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    assert ds.subjects("lesion", "native", group="ST") == ["sub-STUNIPD0001"]
    assert ds.subjects("lesion", "native", group="HC") == ["sub-STUNIPDHC0002"]
    assert ds.subjects("lesion", "native", group="PD") == []


def test_subjects_excludes_non_conforming_folders(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-TEST"])
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    assert ds.subjects("lesion", "native") == ["sub-STUNIPD0001"]


def test_subjects_with_group_filter_does_not_crash_on_non_conforming_folder(tmp_path):
    """Regression: subjects(group=...) used to call group_of() on every
    sub-* folder, including non-conforming ones, crashing the whole request
    even though the real ST subjects were fine. Non-conforming folders must
    now be excluded before group_of() is ever reached."""
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-TEST"])
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    assert ds.subjects("lesion", "native", group="ST") == ["sub-STUNIPD0001"]


def test_non_conforming_subject_folders_lists_them(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-TEST", "sub-backup_old"])
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    assert ds.non_conforming_subject_folders("lesion", "native") == ["sub-TEST", "sub-backup_old"]


def test_non_conforming_subject_folders_empty_when_all_conform(tmp_path):
    project_root = _make_dataset_root(tmp_path, ["sub-STUNIPD0001", "sub-STUNIPDHC0002"])
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    assert ds.non_conforming_subject_folders("lesion", "native") == []


def test_group_of_stroke_subject(tmp_path):
    ds = Dataset("UNIPD/WashU", _make_patterns(tmp_path))
    assert ds.group_of("sub-STUNIPD0001") == "ST"


def test_group_of_healthy_control(tmp_path):
    ds = Dataset("UNIPD/WashU", _make_patterns(tmp_path))
    assert ds.group_of("sub-STUNIPDHC0002") == "HC"


def test_group_of_malformed_subject_id_raises(tmp_path):
    ds = Dataset("UNIPD/WashU", _make_patterns(tmp_path))
    with pytest.raises(ValueError, match="subject_id"):
        ds.group_of("not-a-subject-id")
