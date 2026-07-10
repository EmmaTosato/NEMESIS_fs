"""Unit tests for src.pipeline.retrieve_data - synthetic fixtures, no EBRAIN mount needed."""

import json
from datetime import datetime

import pytest

from src.pipeline import retrieve_data
from src.pipeline.retrieve_data import ReportEntry
from src.retrieval.config import FilePatterns, RetrievalConfig, RetrieveItem
from src.retrieval.dataset import Dataset

_FILE_PATTERNS = FilePatterns(
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
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_FILE_PATTERNS,
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


def _make_second_dataset_like(tmp_path):
    """1 ST subject with native T1w, in a different dataset tree under the
    same project_root as _make_washu_like (so both can be requested together)."""
    root = tmp_path / "UNIPD" / "PASPORT"
    _touch(root / "sub-STUNIPD0500" / "anat" / "sub-STUNIPD0500_T1w.nii.gz")
    return tmp_path


def test_explicit_subject_absent_from_one_dataset_reported_as_missing(tmp_path):
    project_root = _make_washu_like(tmp_path)
    _make_second_dataset_like(tmp_path)
    config = _make_config(
        tmp_path,
        project_root,
        datasets=["UNIPD/WashU", "UNIPD/PASPORT"],
        group_filter=None,
        subjects=["sub-STUNIPD0001", "sub-STUNIPD0500"],
        retrieve=[RetrieveItem(space="native", modality="T1w")],
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)  # both subjects exist somewhere - must not raise
    stats = retrieve_data._retrieve_all(datasets, config)

    assert ReportEntry(group="", line="UNIPD/WashU: sub-STUNIPD0500 - not present in this dataset") in (
        stats["UNIPD/WashU"].missing
    )
    assert ReportEntry(group="", line="UNIPD/PASPORT: sub-STUNIPD0001 - not present in this dataset") in (
        stats["UNIPD/PASPORT"].missing
    )
    assert stats["UNIPD/WashU"].copied == 1  # sub-STUNIPD0001 still retrieved from the dataset that has it
    assert stats["UNIPD/PASPORT"].copied == 1  # sub-STUNIPD0500 likewise


def test_retrieve_dataset_reports_non_conforming_folder_without_crashing(tmp_path):
    project_root = _make_washu_like(tmp_path)
    _touch(project_root / "UNIPD" / "WashU" / "sub-TEST" / "anat" / "placeholder.txt")
    config = _make_config(tmp_path, project_root, group_filter=None)
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)  # must not raise
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].non_conforming == [
        "UNIPD/WashU: sub-TEST - does not match expected subject naming, excluded from retrieval"
    ]
    assert stats["UNIPD/WashU"].subjects_selected == 3  # only the 3 real subjects, sub-TEST excluded


def test_retrieve_dataset_with_group_filter_does_not_crash_on_non_conforming_folder(tmp_path):
    project_root = _make_washu_like(tmp_path)
    _touch(project_root / "UNIPD" / "WashU" / "sub-TEST" / "anat" / "placeholder.txt")
    config = _make_config(tmp_path, project_root, group_filter=["ST"])
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)  # must not raise
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].non_conforming == [
        "UNIPD/WashU: sub-TEST - does not match expected subject naming, excluded from retrieval"
    ]


def test_retrieve_dataset_counts_subjects_with_native_and_mni_data(tmp_path):
    """subjects_native/subjects_mni count ANY file registered under that
    space (per file_patterns.json), independent of which specific modality
    `retrieve` actually asks for - here retrieve only asks for mni/lesion_mask,
    yet subjects_native must still reflect the 2 ST subjects that have T1w."""
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, group_filter=["ST"])
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    # ST subjects: sub-STUNIPD0001 (T1w + mni mask), sub-STUNIPD0002 (T1w only).
    assert stats["UNIPD/WashU"].subjects_native == 2
    assert stats["UNIPD/WashU"].subjects_mni == 1


def test_missing_entry_notes_subject_has_data_in_the_other_space(tmp_path):
    """sub-STUNIPD0002 has native T1w but no mni lesion_mask - the Missing
    line for it must say so, so a reader doesn't have to go check
    file_patterns.json / disk by hand to know whether this is 'no data at
    all' or 'raw arrived, derivative didn't'."""
    project_root = _make_washu_like(tmp_path)
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(space="mni", modality="lesion_mask")],
        subjects=["sub-STUNIPD0002"],
        group_filter=None,
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].missing == [
        ReportEntry(
            group="mni/lesion_mask",
            line="UNIPD/WashU: sub-STUNIPD0002 - no mni/lesion_mask (in native not in mni)",
        )
    ]


def test_missing_entry_notes_reverse_direction_when_only_mni_present(tmp_path):
    project_root = tmp_path
    root = project_root / "UNIPD" / "WashU"
    # A second subject with native T1w, so the dataset-wide availability check
    # (native/T1w must exist *somewhere* in this dataset) still passes - only
    # sub-STUNIPD0099 itself is missing it, which is what this test is about.
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_T1w.nii.gz")
    # sub-STUNIPD0099's own folder must exist for Dataset.subjects() to know
    # about it at all - only its derivatives/manual_masks entry carries data.
    _touch(root / "sub-STUNIPD0099" / "dwi" / "sub-STUNIPD0099_dwi.nii.gz")
    _touch(
        root
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0099"
        / "anat"
        / "sub-STUNIPD0099_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(space="native", modality="T1w")],
        subjects=["sub-STUNIPD0099"],
        group_filter=None,
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].missing == [
        ReportEntry(
            group="native/T1w",
            line="UNIPD/WashU: sub-STUNIPD0099 - no native/T1w (in mni not in native)",
        )
    ]


def test_missing_entry_has_no_annotation_when_subject_has_neither_space(tmp_path):
    project_root = tmp_path
    root = project_root / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0099" / "anat" / "placeholder_not_a_registered_file.txt")
    # A second subject with an mni mask, so the dataset-wide availability
    # check (mni/lesion_mask must exist *somewhere*) still passes - only
    # sub-STUNIPD0099 itself has neither space, which is what this test covers.
    _touch(
        root
        / "derivatives"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(space="mni", modality="lesion_mask")],
        subjects=["sub-STUNIPD0099"],
        group_filter=None,
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].missing == [
        ReportEntry(group="mni/lesion_mask", line="UNIPD/WashU: sub-STUNIPD0099 - no mni/lesion_mask")
    ]


def test_retrieve_subject_flags_ambiguous_match(tmp_path):
    project_root = _make_washu_like(tmp_path)
    root = project_root / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_roi.nii.gz")
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_space-T1w_lesion_roi.nii.gz")
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(space="native", modality="lesion_roi")],
        subjects=["sub-STUNIPD0001"],
        group_filter=None,
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert len(stats["UNIPD/WashU"].ambiguous) == 1
    assert "sub-STUNIPD0001" in stats["UNIPD/WashU"].ambiguous[0].line
    assert stats["UNIPD/WashU"].ambiguous[0].group == "native/lesion_roi"
    assert stats["UNIPD/WashU"].copied == 1  # highest-priority match still copied


def test_select_subjects_no_filter_returns_everyone(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU", _FILE_PATTERNS)
    config = _make_config(tmp_path, project_root, group_filter=None)
    assert retrieve_data._select_subjects(ds, config) == ds.subjects()


def test_select_subjects_group_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU", _FILE_PATTERNS)
    config = _make_config(tmp_path, project_root, group_filter=["HC"])
    assert retrieve_data._select_subjects(ds, config) == ["sub-STUNIPDHC0003"]


def test_select_subjects_explicit_bypasses_group_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU", _FILE_PATTERNS)
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
    # 3 subjects selected, all 3 have native (T1w), only sub-STUNIPD0001 has mni (lesion_mask),
    # 3 copied, 0 skipped, 0 failed, participants.tsv not requested (include_tabular_data=False).
    assert "| UNIPD/WashU | 3 | 3 | 1 | 3 | 0 | 0 | not requested |" in report_text


def _minimal_config(tmp_path, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        project_root=tmp_path / "source",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_FILE_PATTERNS,
        datasets=["UNIPD/WashU", "UNIPD/PASPORT"],
        group_filter=["ST"],
        subjects=None,
        retrieve=[RetrieveItem(space="mni", modality="lesion_mask")],
        include_tabular_data=True,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_build_report_title_and_config_dump(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {"UNIPD/WashU": retrieve_data.DatasetStats(), "UNIPD/PASPORT": retrieve_data.DatasetStats()}
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    lines = report.splitlines()
    assert lines[0] == "# clinical_connectome_09-07-26"
    assert lines[1] == "## 10:22"
    assert '"project": "clinical_connectome"' in report
    assert '"overwrite": false' in report
    assert '"file_patterns":' in report
    assert '"UNIPD/WashU"' in report and '"UNIPD/PASPORT"' in report


def test_build_report_groups_missing_by_dataset_with_counts_and_separator(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(group="mni/lesion_mask", line="UNIPD/WashU: sub-A - no mni/lesion_mask"),
                ReportEntry(group="mni/lesion_mask", line="UNIPD/WashU: sub-B - no mni/lesion_mask"),
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(
            missing=[ReportEntry(group="mni/lesion_mask", line="UNIPD/PASPORT: sub-C - no mni/lesion_mask")]
        ),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    expected_block = (
        "**mni/lesion_mask** (2)\n"
        "- UNIPD/WashU: sub-A - no mni/lesion_mask\n"
        "- UNIPD/WashU: sub-B - no mni/lesion_mask\n"
        "\n"
        "Missing Count = 2\n"
        "\n"
        "---\n"
        "\n"
        "**mni/lesion_mask** (1)\n"
        "- UNIPD/PASPORT: sub-C - no mni/lesion_mask\n"
        "\n"
        "Missing Count = 1"
    )
    assert expected_block in report


def test_build_report_sub_groups_missing_by_modality_within_one_dataset(tmp_path):
    """A run requesting more than one (space, modality) must not interleave
    their misses into one flat list per dataset - each gets its own
    sub-heading and count, so a reader can scan one modality at a time."""
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(group="native/T1w", line="UNIPD/WashU: sub-A - no native/T1w"),
                ReportEntry(group="mni/lesion_mask", line="UNIPD/WashU: sub-A - no mni/lesion_mask"),
                ReportEntry(group="native/T1w", line="UNIPD/WashU: sub-B - no native/T1w"),
            ]
        ),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    expected_block = (
        "**native/T1w** (2)\n"
        "- UNIPD/WashU: sub-A - no native/T1w\n"
        "- UNIPD/WashU: sub-B - no native/T1w\n"
        "\n"
        "**mni/lesion_mask** (1)\n"
        "- UNIPD/WashU: sub-A - no mni/lesion_mask\n"
        "\n"
        "Missing Count = 3"
    )
    assert expected_block in report


def test_build_report_omits_dataset_with_no_missing_entries(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            missing=[ReportEntry(group="mni/lesion_mask", line="UNIPD/WashU: sub-A - no mni/lesion_mask")]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(missing=[]),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    missing_section = report.split("## Missing")[1].split("## Ambiguous")[0]
    assert "UNIPD/PASPORT" not in missing_section
    assert missing_section.count("Missing Count") == 1


def test_build_report_includes_ambiguous_and_non_conforming_sections(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            ambiguous=[
                ReportEntry(
                    group="native/lesion_roi",
                    line="UNIPD/WashU: sub-A - native/lesion_roi: using X, also matched Y",
                )
            ],
            non_conforming=["UNIPD/WashU: sub-TEST - does not match expected subject naming, excluded from retrieval"],
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    assert "## Ambiguous" in report
    assert "Ambiguous Count = 1" in report
    assert "## Non-conforming subject folders" in report
    assert "Non-conforming Count = 1" in report


def test_build_report_includes_mismatched_section(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            mismatched=["UNIPD/WashU: sub-A native/T1w - checksum differs from source: /a vs /b"]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    assert "## Mismatched" in report
    assert "Mismatched Count = 1" in report


def test_write_report_path_uses_data_retrieval_folder_and_project(tmp_path, monkeypatch):
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports" / "data_retrieval")
    config = _minimal_config(tmp_path)
    stats = {"UNIPD/WashU": retrieve_data.DatasetStats(), "UNIPD/PASPORT": retrieve_data.DatasetStats()}
    report_path = retrieve_data._write_report(config, stats)
    assert report_path.parent == tmp_path / "reports" / "data_retrieval" / "clinical_connectome"
    assert report_path.suffix == ".md"


def _write_file_patterns_json(path):
    path.write_text(
        json.dumps(
            {
                "native": {"T1w": ["{subject_id}/anat/{subject_id}_T1w.nii.gz"]},
                "mni": {
                    "lesion_mask": [
                        "derivatives/manual_masks/{subject_id}/anat/"
                        "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
                    ]
                },
            }
        )
    )


def _write_json_config(config_path, project_root, output_root, **overrides):
    file_patterns_path = config_path.parent / "file_patterns.json"
    if not file_patterns_path.is_file():
        _write_file_patterns_json(file_patterns_path)
    payload = {
        "output_root": str(output_root),
        "project": "clinical_connectome",
        "project_root": str(project_root),
        "file_patterns": str(file_patterns_path),
        "datasets": ["UNIPD/WashU"],
        "group_filter": None,
        "subjects": None,
        "retrieve": [{"space": "native", "modality": "T1w"}],
        "include_tabular_data": False,
        "overwrite": False,
    }
    payload.update(overrides)
    config_path.write_text(json.dumps(payload))


def test_main_writes_paired_log_and_report(tmp_path, monkeypatch):
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(retrieve_data, "LOGS_ROOT", tmp_path / "logs")
    project_root = _make_washu_like(tmp_path / "source")
    config_path = tmp_path / "config.json"
    _write_json_config(config_path, project_root, tmp_path / "data")

    exit_code = retrieve_data.main(["--config", str(config_path)])

    assert exit_code == 0
    report_files = list((tmp_path / "reports" / "clinical_connectome").glob("*.md"))
    log_files = list((tmp_path / "logs" / "clinical_connectome").glob("*.log"))
    assert len(report_files) == 1
    assert len(log_files) == 1
    assert report_files[0].stem == log_files[0].stem  # same run, same timestamp

    log_text = log_files[0].read_text()
    assert "retrieving 3 subjects" in log_text
    assert "copied:" in log_text


def test_main_verifies_only_after_every_dataset_has_finished_copying(tmp_path, monkeypatch):
    """End-to-end: a local file left over from a previous run whose source has
    since changed must be caught, logged as an ERROR, and surfaced in the
    report - not silently skipped as 'already exists'. Also pins down that
    verification is a distinct final phase (see _retrieve_all): the "copied"/
    "retrieving N subjects" narrative for every dataset is fully written to
    the log before the first "checksum mismatch" line appears."""
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(retrieve_data, "LOGS_ROOT", tmp_path / "logs")
    project_root = _make_washu_like(tmp_path / "source")
    config_path = tmp_path / "config.json"
    output_root = tmp_path / "data"
    _write_json_config(config_path, project_root, output_root)

    stale_destination = (
        output_root
        / "clinical_connectome"
        / "UNIPD"
        / "WashU"
        / "sub-STUNIPD0001"
        / "lesion"
        / "native"
        / "sub-STUNIPD0001_T1w.nii.gz"
    )
    stale_destination.parent.mkdir(parents=True)
    stale_destination.write_bytes(b"stale-from-a-previous-run")

    exit_code = retrieve_data.main(["--config", str(config_path)])

    assert exit_code == 0  # per-file issues are logged, not fatal to the run
    report_text = (tmp_path / "reports" / "clinical_connectome").glob("*.md").__next__().read_text()
    assert "## Mismatched" in report_text
    assert "sub-STUNIPD0001" in report_text.split("## Mismatched")[1]

    log_text = (tmp_path / "logs" / "clinical_connectome").glob("*.log").__next__().read_text()
    assert "ERROR: checksum mismatch" in log_text
    assert "ERROR: post-copy verification found 1 problem(s)" in log_text
    # copying (2 subjects have T1w, 1 skipped as stale-but-existing) happened before verification
    assert log_text.index("skip (exists)") < log_text.index("checksum mismatch")


def test_main_does_not_leak_log_lines_across_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(retrieve_data, "LOGS_ROOT", tmp_path / "logs")

    project_root_a = _make_washu_like(tmp_path / "run_a" / "source")
    config_a = tmp_path / "run_a" / "config_a.json"
    config_a.parent.mkdir(parents=True, exist_ok=True)
    _write_json_config(config_a, project_root_a, tmp_path / "run_a" / "data")
    retrieve_data.main(["--config", str(config_a)])

    project_root_b = _make_washu_like(tmp_path / "run_b" / "source")
    config_b = tmp_path / "run_b" / "config_b.json"
    config_b.parent.mkdir(parents=True, exist_ok=True)
    _write_json_config(config_b, project_root_b, tmp_path / "run_b" / "data", project="other_project")
    retrieve_data.main(["--config", str(config_b)])

    log_files_a = list((tmp_path / "logs" / "clinical_connectome").glob("*.log"))
    log_files_b = list((tmp_path / "logs" / "other_project").glob("*.log"))
    assert len(log_files_a) == 1
    assert len(log_files_b) == 1

    text_a = log_files_a[0].read_text()
    assert "run_b" not in text_a  # the first run's log must not receive lines from the second run
