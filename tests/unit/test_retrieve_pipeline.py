"""Unit tests for src.pipeline.retrieve_data - synthetic fixtures, no EBRAIN mount needed."""

import json
from datetime import datetime

import pytest

from src.pipeline import retrieve_data
from src.pipeline.retrieve_data import ReportEntry
from src.retrieval.config import FilePatterns, RetrievalConfig, RetrieveItem
from src.retrieval.dataset import Dataset


def _make_patterns(project_root):
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={
            ("lesion", "native", "T1w"): ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
            ("lesion", "native", "FLAIR"): ["{subject_id}/anat/{subject_id}_FLAIR.nii.gz"],
            ("lesion", "native", "lesion_roi"): [
                "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz",
                "{subject_id}/anat/{subject_id}_space-T1w_lesion_roi.nii.gz",
            ],
            ("lesion", "mni", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/"
                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
            ],
        },
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
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_make_patterns(project_root),
        datasets=["UNIPD/WashU"],
        group_filter=["ST"],
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", space="mni", modality="lesion_mask")],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_validate_upfront_raises_for_unsupported_modality(tmp_path):
    project_root = _make_washu_like(tmp_path)
    config = _make_config(
        tmp_path, project_root, retrieve=[RetrieveItem(object="lesion", space="native", modality="FLAIR")]
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
        retrieve=[RetrieveItem(object="lesion", space="native", modality="T1w")],
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


def test_missing_entry_is_tagged_and_says_not_found_when_derivatives_dir_absent(tmp_path):
    """sub-STUNIPD0002 has native T1w but no mni lesion_mask, and no
    derivatives/manual_masks/sub-STUNIPD0002/ folder at all (only
    sub-STUNIPD0001 has one in this fixture) - describe_absence must say
    "not found", not "empty folder" (that's only when the folder exists but
    has nothing in it - see test_dataset_lesion.py). No cross-space
    annotation - that comparison is the data_summary report's job (see
    src.retrieval.matrix), not this pipeline's. Tagged with its
    (object, space, modality) group so multi-item runs can be sub-grouped
    (see _build_report tests)."""
    project_root = _make_washu_like(tmp_path)
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(object="lesion", space="mni", modality="lesion_mask")],
        subjects=["sub-STUNIPD0002"],
        group_filter=None,
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].missing == [
        ReportEntry(
            group="lesion/mni/lesion_mask",
            line="UNIPD/WashU: sub-STUNIPD0002 - no lesion/mni/lesion_mask (not found)",
        )
    ]


def test_retrieve_subject_copies_every_matching_template(tmp_path):
    """If a subject has files matching more than one registered template for
    the same (object, space, modality), all of them get copied - there is no
    priority/ambiguity concept anymore (see FilePatterns docstring: "grab
    every one of these that exists")."""
    project_root = _make_washu_like(tmp_path)
    root = project_root / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_roi.nii.gz")
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_space-T1w_lesion_roi.nii.gz")
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(object="lesion", space="native", modality="lesion_roi")],
        subjects=["sub-STUNIPD0001"],
        group_filter=None,
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].copied == 2
    assert stats["UNIPD/WashU"].missing == []


def test_select_subjects_no_filter_returns_everyone(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _make_config(tmp_path, project_root, group_filter=None)
    # union across every space of the "lesion" object this config touches (native + mni,
    # since config.retrieve requests the "lesion" object, see _known_object_spaces) -
    # every subject has at least native, so all 3 are selected.
    assert retrieve_data._select_subjects(ds, config) == [
        "sub-STUNIPD0001",
        "sub-STUNIPD0002",
        "sub-STUNIPDHC0003",
    ]


def test_select_subjects_group_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _make_config(tmp_path, project_root, group_filter=["HC"])
    assert retrieve_data._select_subjects(ds, config) == ["sub-STUNIPDHC0003"]


def test_select_subjects_explicit_bypasses_group_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _make_config(
        tmp_path, project_root, group_filter=["PD"], subjects=["sub-STUNIPD0001", "sub-STUNIPD0002"]
    )
    assert retrieve_data._select_subjects(ds, config) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_copy_one_copies_new_file(tmp_path):
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"data")
    destination = tmp_path / "out" / "dest.nii.gz"
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=False, stats=stats, label="test")
    assert destination.read_bytes() == b"data"
    assert stats.copied == 1


def test_copy_one_skips_existing_when_overwrite_false(tmp_path):
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"new")
    destination = tmp_path / "dest.nii.gz"
    destination.write_bytes(b"old")
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=False, stats=stats, label="test")
    assert destination.read_bytes() == b"old"
    assert stats.skipped_existing == 1
    assert stats.copied == 0


def test_copy_one_overwrites_when_true(tmp_path):
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"new")
    destination = tmp_path / "dest.nii.gz"
    destination.write_bytes(b"old")
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=True, stats=stats, label="test")
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
    retrieve_data._copy_one(
        source,
        destination,
        overwrite=False,
        stats=stats,
        label="UNIPD/WashU: sub-A - lesion/native/T1w",
        group="lesion/native/T1w",
    )  # must not raise
    assert len(stats.failed) == 1
    assert stats.failed[0] == ReportEntry(
        group="lesion/native/T1w", line="UNIPD/WashU: sub-A - lesion/native/T1w: copy failed (disk full)"
    )
    assert stats.copied == 0


def test_full_run_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    project_root = _make_washu_like(tmp_path)
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(object="lesion", space="native", modality="T1w")],
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
    # 3 copied, 0 skipped, 0 failed.
    assert "| UNIPD/WashU | 3 | 0 | 0 |" in report_text


def _minimal_config(tmp_path, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_make_patterns(tmp_path / "source"),
        datasets=["UNIPD/WashU", "UNIPD/PASPORT"],
        group_filter=["ST"],
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", space="mni", modality="lesion_mask")],
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
                ReportEntry(group="lesion/mni/lesion_mask", line="UNIPD/WashU: sub-A - no lesion/mni/lesion_mask"),
                ReportEntry(group="lesion/mni/lesion_mask", line="UNIPD/WashU: sub-B - no lesion/mni/lesion_mask"),
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(
                    group="lesion/mni/lesion_mask", line="UNIPD/PASPORT: sub-C - no lesion/mni/lesion_mask"
                )
            ]
        ),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    expected_block = (
        "**lesion/mni/lesion_mask** (2)\n"
        "- UNIPD/WashU: sub-A - no lesion/mni/lesion_mask\n"
        "- UNIPD/WashU: sub-B - no lesion/mni/lesion_mask\n"
        "\n"
        "File Not Found Count = 2\n"
        "\n"
        "---\n"
        "\n"
        "**lesion/mni/lesion_mask** (1)\n"
        "- UNIPD/PASPORT: sub-C - no lesion/mni/lesion_mask\n"
        "\n"
        "File Not Found Count = 1"
    )
    assert expected_block in report


def test_build_report_sub_groups_missing_by_modality_within_one_dataset(tmp_path):
    """A run requesting more than one (object, space, modality) must not
    interleave their misses into one flat list per dataset - each gets its
    own sub-heading and count, so a reader can scan one modality at a time."""
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(group="lesion/native/T1w", line="UNIPD/WashU: sub-A - no lesion/native/T1w"),
                ReportEntry(group="lesion/mni/lesion_mask", line="UNIPD/WashU: sub-A - no lesion/mni/lesion_mask"),
                ReportEntry(group="lesion/native/T1w", line="UNIPD/WashU: sub-B - no lesion/native/T1w"),
            ]
        ),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    expected_block = (
        "**lesion/native/T1w** (2)\n"
        "- UNIPD/WashU: sub-A - no lesion/native/T1w\n"
        "- UNIPD/WashU: sub-B - no lesion/native/T1w\n"
        "\n"
        "**lesion/mni/lesion_mask** (1)\n"
        "- UNIPD/WashU: sub-A - no lesion/mni/lesion_mask\n"
        "\n"
        "File Not Found Count = 3"
    )
    assert expected_block in report


def test_build_report_omits_dataset_with_no_missing_entries(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(group="lesion/mni/lesion_mask", line="UNIPD/WashU: sub-A - no lesion/mni/lesion_mask")
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(missing=[]),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    missing_section = report.split("## File not found")[1].split("## Non-conforming")[0]
    assert "UNIPD/PASPORT" not in missing_section
    assert missing_section.count("File Not Found Count") == 1


def test_build_report_includes_failed_section(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            failed=[
                ReportEntry(
                    group="lesion/mni/lesion_mask",
                    line="UNIPD/WashU: sub-A - lesion/mni/lesion_mask: copy failed (disk full)",
                )
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    assert "## Failed" in report
    assert "Failed Count = 1" in report
    assert "| UNIPD/WashU | 0 | 0 | 1 |" in report  # summary table's failed column reflects len(failed)


def test_build_report_includes_non_conforming_section(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            non_conforming=["UNIPD/WashU: sub-TEST - does not match expected subject naming, excluded from retrieval"],
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    assert "## Non-conforming subject folders" in report
    assert "Non-conforming Count = 1" in report


def test_build_report_includes_mismatched_section(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            mismatched=["UNIPD/WashU: sub-A lesion/native/T1w - checksum differs from source: /a vs /b"]
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


def _write_file_patterns_json(path, project_root):
    path.write_text(
        json.dumps(
            {
                "lesion": {
                    "project_root": str(project_root),
                    "native": {"T1w": ["{subject_id}/anat/{subject_id}_T1w.nii.gz"]},
                    "mni": {
                        "lesion_mask": [
                            "derivatives/manual_masks/{subject_id}/anat/"
                            "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
                        ]
                    },
                }
            }
        )
    )


def _write_json_config(config_path, project_root, output_root, **overrides):
    file_patterns_path = config_path.parent / "file_patterns.json"
    if not file_patterns_path.is_file():
        _write_file_patterns_json(file_patterns_path, project_root)
    payload = {
        "output_root": str(output_root),
        "project": "clinical_connectome",
        "file_patterns": str(file_patterns_path),
        "datasets": ["UNIPD/WashU"],
        "group_filter": None,
        "subjects": None,
        "retrieve": [{"object": "lesion", "space": "native", "modality": "T1w"}],
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
