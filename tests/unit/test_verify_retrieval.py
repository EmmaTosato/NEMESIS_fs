"""Unit tests for scripts/verify_retrieval.py - synthetic fixtures, no EBRAIN mount needed."""

from scripts import verify_retrieval
from src.retrieval.config import FilePatterns, RetrievalConfig, RetrieveItem


def _make_patterns(lesion_root):
    return FilePatterns(
        project_roots={"lesion": lesion_root},
        patterns={
            ("lesion", "manual_masks", "anat", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/"
                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
            ],
        },
    )


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _make_washu_like(tmp_path):
    """2 ST subjects, both with a manual_masks lesion_mask file."""
    root = tmp_path / "UNIPD" / "WashU"
    for subject_id in ["sub-STUNIPD0001", "sub-STUNIPD0002"]:
        _touch(
            root / "derivatives" / "manual_masks" / subject_id / "anat"
            / f"{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
        )
    return tmp_path


def _make_config(tmp_path, project_root, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_make_patterns(project_root),
        datasets=["UNIPD/WashU"],
        group_filter=None,
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_main_raises_clean_error_for_typo_subject_instead_of_silently_reporting_zero(tmp_path, monkeypatch, capsys):
    """Regression: verify_retrieval.py used to skip retrieve_data.py's own
    upfront validation entirely - a typo'd subjects entry silently verified
    an empty selection (0 subjects found, so 0 problems reported) and exited
    0, as if everything had actually been checked. It must instead stop with
    a clear error, same as retrieve_data.py's own main() would."""
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, subjects=["sub-STUNIPD9999"])
    monkeypatch.setattr(verify_retrieval, "load_config", lambda path: config)

    exit_code = verify_retrieval.main(["--config", "unused.json"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "sub-STUNIPD9999" in captured.err


def test_main_raises_clean_error_for_group_filter_matching_nobody(tmp_path, monkeypatch, capsys):
    """Same gap, other trigger: group_filter matching 0 subjects."""
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, group_filter=["PD"])
    monkeypatch.setattr(verify_retrieval, "load_config", lambda path: config)

    exit_code = verify_retrieval.main(["--config", "unused.json"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "group_filter" in captured.err


def test_main_verifies_normally_when_subjects_are_valid(tmp_path, monkeypatch):
    """The added validation must not block the legitimate case - a request
    for real, existing subjects still reaches verify_dataset and returns a
    normal exit code (1 here only because the local copy doesn't exist yet
    in this fixture, i.e. missing_locally is non-empty - a real "all good"
    run would return 0, exercised by the retrieve_data integration tests)."""
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, subjects=["sub-STUNIPD0001"])
    monkeypatch.setattr(verify_retrieval, "load_config", lambda path: config)

    exit_code = verify_retrieval.main(["--config", "unused.json"])

    assert exit_code == 1  # missing_locally: nothing was ever copied to output_root in this fixture
