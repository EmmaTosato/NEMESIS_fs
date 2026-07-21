"""Unit tests for src/sdc/manifest.py."""

import pytest

from src.retrieval.config import FilePatterns
from src.sdc.config import SDCConfig
from src.sdc.manifest import build_manifest, read_manifest, select_chunk, write_manifest


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _file_patterns(project_root):
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={
            ("lesion", "manual_masks", "anat", "lesion_mask"): [
                "{subject_id}/anat/{subject_id}_lesion_mask.nii.gz",
            ],
        },
    )


def _config(tmp_path, *, datasets, group_filter=None):
    return SDCConfig(
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_file_patterns(tmp_path / "data"),
        datasets=datasets,
        group_filter=group_filter,
        bcbtoolkit_path=tmp_path / "BCBToolKit",
        tracks_dir=None,
        cores_per_subject=4,
        stage2_ebrains=True,
        stage2_presets=[],
        output_root=tmp_path / "out",
        session_name="run1",
        overwrite=False,
        run_notes=None,
    )


def test_build_manifest_discovers_subjects_and_excludes_missing(tmp_path):
    root = tmp_path / "data" / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_mask.nii.gz")
    # sub-STUNIPD0002 has a folder but no lesion mask file - missing, not crashing.
    (root / "sub-STUNIPD0002").mkdir(parents=True)

    config = _config(tmp_path, datasets=["UNIPD/WashU"])
    rows, excluded = build_manifest(config)

    assert [r.subject_id for r in rows] == ["sub-STUNIPD0001"]
    assert "sub-STUNIPD0002" in excluded
    assert "no lesion mask found" in excluded["sub-STUNIPD0002"]


def test_build_manifest_excludes_duplicate_subject_across_datasets(tmp_path):
    for dataset in ("UNIPD/WashU", "UNIPD/PASPORT"):
        root = tmp_path / "data" / dataset
        _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_mask.nii.gz")

    config = _config(tmp_path, datasets=["UNIPD/WashU", "UNIPD/PASPORT"])
    rows, excluded = build_manifest(config)

    assert len(rows) == 1
    assert "sub-STUNIPD0001" in excluded
    assert "duplicate subject_id across datasets" in excluded["sub-STUNIPD0001"]


def test_build_manifest_applies_group_filter(tmp_path):
    root = tmp_path / "data" / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_mask.nii.gz")
    _touch(root / "sub-PDUNIPD0002" / "anat" / "sub-PDUNIPD0002_lesion_mask.nii.gz")

    config = _config(tmp_path, datasets=["UNIPD/WashU"], group_filter=["ST"])
    rows, _ = build_manifest(config)

    assert [r.subject_id for r in rows] == ["sub-STUNIPD0001"]


def test_write_read_manifest_roundtrip(tmp_path):
    root = tmp_path / "data" / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_mask.nii.gz")
    config = _config(tmp_path, datasets=["UNIPD/WashU"])
    rows, _ = build_manifest(config)

    manifest_path = tmp_path / "manifest.csv"
    write_manifest(rows, manifest_path)
    reloaded = read_manifest(manifest_path)

    assert reloaded == rows


def test_read_manifest_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        read_manifest(tmp_path / "nope.csv")


def test_select_chunk_covers_every_subject_exactly_once():
    rows = list(range(7))
    task_count = 3
    chunks = [select_chunk(rows, task_id, task_count) for task_id in range(task_count)]
    recombined = sorted(subject for chunk in chunks for subject in chunk)
    assert recombined == rows


@pytest.mark.parametrize("task_id, task_count", [(0, 0), (-1, 3), (3, 3)])
def test_select_chunk_rejects_invalid_task_id(task_id, task_count):
    with pytest.raises(ValueError):
        select_chunk([1, 2, 3], task_id, task_count)
