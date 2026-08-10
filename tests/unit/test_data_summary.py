"""Unit tests for scripts/data_summary.py - synthetic fixtures, no EBRAIN mount needed."""

from scripts import data_summary
from src.retrieval.config import FilePatterns, RetrievalConfig


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
        retrieve=[],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_main_raises_clean_error_for_typo_subject_instead_of_silently_reporting_almost_nothing(
    tmp_path, monkeypatch, capsys
):
    """Regression: write_reports used to call select_all_subjects with no
    upfront check - a typo'd subjects entry silently produced a CSV with
    only a header row, and main() printed "data summary written to ..." as
    if it had succeeded."""
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, subjects=["sub-STUNIPD9999"])
    monkeypatch.setattr(data_summary, "load_config", lambda path: config)
    monkeypatch.setattr(data_summary, "REPORTS_ROOT", tmp_path / "reports")

    exit_code = data_summary.main(["--config", "unused.json"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "sub-STUNIPD9999" in captured.err
    assert not (tmp_path / "reports").exists()  # nothing written for an invalid request


def test_main_writes_report_normally_for_valid_subjects(tmp_path, monkeypatch):
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, subjects=["sub-STUNIPD0001"])
    monkeypatch.setattr(data_summary, "load_config", lambda path: config)
    monkeypatch.setattr(data_summary, "REPORTS_ROOT", tmp_path / "reports")

    exit_code = data_summary.main(["--config", "unused.json"])

    assert exit_code == 0
    report_path = tmp_path / "reports" / "data_summary__UNIPD_WashU.csv"
    assert report_path.is_file()
