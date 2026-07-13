"""Unit tests for src.retrieval.verify - synthetic fixtures, no EBRAIN mount needed."""

from src.retrieval import verify
from src.retrieval.config import FilePatterns, RetrievalConfig, RetrieveItem
from src.retrieval.dataset import Dataset


def _make_patterns(project_root):
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={
            ("lesion", "native", "T1w"): ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
            ("lesion", "mni", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/"
                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
            ],
        },
    )


def _touch(path, content=b"data"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _make_config(tmp_path, project_root, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_make_patterns(project_root),
        datasets=["UNIPD/WashU"],
        group_filter=["ST"],
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", space="native", modality="T1w")],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def _make_dataset(tmp_path):
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_T1w.nii.gz", b"content-1")
    ds = Dataset("UNIPD/WashU", _make_patterns(tmp_path))
    return tmp_path, ds


def _local_t1w_path(config, subject_id):
    return (
        config.output_root
        / config.project
        / "UNIPD"
        / "WashU"
        / subject_id
        / "lesion"
        / "native"
        / f"{subject_id}_T1w.nii.gz"
    )


def test_verify_dataset_ok_when_local_content_matches_source(tmp_path):
    project_root, ds = _make_dataset(tmp_path)
    config = _make_config(tmp_path, project_root)
    _touch(_local_t1w_path(config, "sub-STUNIPD0001"), b"content-1")

    result = verify.verify_dataset("UNIPD/WashU", ds, ["sub-STUNIPD0001"], config)

    assert result.mismatched == []
    assert result.missing_locally == []
    assert result.unexpected_local_files == []


def test_verify_dataset_flags_checksum_mismatch(tmp_path):
    """The core case: a local file present (e.g. skipped because it already
    existed) whose content no longer matches the current source."""
    project_root, ds = _make_dataset(tmp_path)
    config = _make_config(tmp_path, project_root)
    _touch(_local_t1w_path(config, "sub-STUNIPD0001"), b"stale-content")

    result = verify.verify_dataset("UNIPD/WashU", ds, ["sub-STUNIPD0001"], config)

    assert len(result.mismatched) == 1
    assert "sub-STUNIPD0001" in result.mismatched[0]
    assert "lesion/native/T1w" in result.mismatched[0]


def test_verify_dataset_flags_missing_locally_when_source_has_file_but_local_does_not(tmp_path):
    project_root, ds = _make_dataset(tmp_path)
    config = _make_config(tmp_path, project_root)
    # no local file created at all

    result = verify.verify_dataset("UNIPD/WashU", ds, ["sub-STUNIPD0001"], config)

    assert len(result.missing_locally) == 1
    assert "sub-STUNIPD0001" in result.missing_locally[0]
    assert result.mismatched == []


def test_verify_dataset_skips_subjects_where_source_has_no_file(tmp_path):
    """An empty resolve() list (source itself lacks the file) is not a
    verification concern - already covered by stats.missing during the copy
    phase."""
    project_root, ds = _make_dataset(tmp_path)
    _touch(project_root / "UNIPD" / "WashU" / "sub-STUNIPD0002" / "anat" / "placeholder.txt")
    config = _make_config(tmp_path, project_root)

    result = verify.verify_dataset("UNIPD/WashU", ds, ["sub-STUNIPD0002"], config)

    assert result.mismatched == []
    assert result.missing_locally == []


def test_verify_dataset_flags_unexpected_local_file(tmp_path):
    project_root, ds = _make_dataset(tmp_path)
    config = _make_config(tmp_path, project_root)
    _touch(_local_t1w_path(config, "sub-STUNIPD0001"), b"content-1")
    stale_leftover = (
        config.output_root / config.project / "UNIPD" / "WashU" / "sub-STUNIPD0001" / "lesion" / "native"
        / "sub-STUNIPD0001_old_naming.nii.gz"
    )
    _touch(stale_leftover, b"leftover")

    result = verify.verify_dataset("UNIPD/WashU", ds, ["sub-STUNIPD0001"], config)

    assert len(result.unexpected_local_files) == 1
    assert "old_naming" in result.unexpected_local_files[0]


def test_verify_dataset_checks_participants_tsv(tmp_path):
    project_root, ds = _make_dataset(tmp_path)
    _touch(project_root / "UNIPD" / "WashU" / "participants.tsv", b"participant_id\nsub-STUNIPD0001\n")
    config = _make_config(tmp_path, project_root, include_tabular_data=True)
    _touch(_local_t1w_path(config, "sub-STUNIPD0001"), b"content-1")
    _touch(
        config.output_root / config.project / "UNIPD" / "WashU" / "participants.tsv",
        b"participant_id\nsub-STUNIPD0001\n",
    )

    result = verify.verify_dataset("UNIPD/WashU", ds, ["sub-STUNIPD0001"], config)

    assert result.mismatched == []
    assert result.missing_locally == []


def test_verify_dataset_flags_participants_tsv_mismatch(tmp_path):
    project_root, ds = _make_dataset(tmp_path)
    _touch(project_root / "UNIPD" / "WashU" / "participants.tsv", b"current-table")
    config = _make_config(tmp_path, project_root, include_tabular_data=True)
    _touch(_local_t1w_path(config, "sub-STUNIPD0001"), b"content-1")
    _touch(
        config.output_root / config.project / "UNIPD" / "WashU" / "participants.tsv",
        b"stale-table",
    )

    result = verify.verify_dataset("UNIPD/WashU", ds, ["sub-STUNIPD0001"], config)

    assert len(result.mismatched) == 1
    assert "participants.tsv" in result.mismatched[0]
