"""Unit tests for src.pipeline.retrieve_data - synthetic fixtures, no EBRAIN mount needed."""

import json
from datetime import datetime

import pytest

from src.pipeline import retrieve_data
from src.pipeline.retrieve_data import ReportEntry
from src.retrieval.config import FilePatterns, RetrievalConfig, RetrieveItem
from src.retrieval.dataset import Dataset


def _make_patterns(lesion_root, feature_root=None):
    project_roots = {"lesion": lesion_root}
    patterns = {
        ("lesion", "manual_masks", "anat", "lesion_mask"): [
            "derivatives/manual_masks/{subject_id}/anat/"
            "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
        ],
        # Structurally registered, deliberately never present in any fixture
        # below - used to exercise the "no file registered/found anywhere"
        # STOP (see test_validate_upfront_raises_for_unsupported_suffix).
        ("lesion", "manual_masks", "anat", "FLAIR"): [
            "derivatives/manual_masks/{subject_id}/anat/{subject_id}_FLAIR.nii.gz"
        ],
    }
    if feature_root is not None:
        project_roots["feature"] = feature_root
        patterns[("feature", "func", "FC-pearson")] = ["{subject_id}/func/{subject_id}_FC-pearson.csv"]
    return FilePatterns(project_roots=project_roots, patterns=patterns)


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _make_washu_like(tmp_path):
    """3 subjects (2 ST + 1 HC), all with a manual_masks lesion_mask file."""
    root = tmp_path / "UNIPD" / "WashU"
    for subject_id in ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPDHC0003"]:
        _touch(
            root / "derivatives" / "manual_masks" / subject_id / "anat"
            / f"{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
        )
    return tmp_path


def _make_config(tmp_path, project_root, feature_root=None, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_make_patterns(project_root, feature_root),
        datasets=["UNIPD/WashU"],
        group_filter=["ST"],
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_validate_upfront_raises_for_unsupported_suffix(tmp_path):
    project_root = _make_washu_like(tmp_path)
    config = _make_config(
        tmp_path,
        project_root,
        retrieve=[RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="FLAIR")],
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


def test_validate_upfront_catches_broken_template_even_without_group_filter_or_subjects(tmp_path):
    """Regression: with group_filter=None and subjects=None (the "retrieve
    everyone" case), _validate_group_filter used to skip subject discovery
    entirely, so a template missing {subject_id} as its own path segment
    (see Dataset._subject_container) was never exercised during validation -
    it only surfaced later, mid-copy, outside any try/except in main(),
    crashing with a raw traceback instead of a clean stop. Now
    _validate_subject_discovery exercises it unconditionally."""
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "placeholder.nii.gz")
    broken_patterns = FilePatterns(
        project_roots={"lesion": tmp_path},
        patterns={("lesion", "manual_masks", "anat", "lesion_mask"): ["anat/{subject_id}_lesion_mask.nii.gz"]},
    )
    config = RetrievalConfig(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=broken_patterns,
        datasets=["UNIPD/WashU"],
        group_filter=None,
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")],
        include_tabular_data=False,
        overwrite=False,
    )
    datasets = retrieve_data._build_datasets(config)
    with pytest.raises(ValueError, match=r"\{subject_id\}"):
        retrieve_data._validate_upfront(datasets, config)


def _make_second_dataset_like(tmp_path):
    """1 ST subject with a manual_masks lesion_mask, in a different dataset
    tree under the same project_root as _make_washu_like (so both can be
    requested together)."""
    root = tmp_path / "UNIPD" / "PASPORT"
    _touch(
        root / "derivatives" / "manual_masks" / "sub-STUNIPD0500" / "anat"
        / "sub-STUNIPD0500_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
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
    """sub-TEST sits under the manual_masks container - non-conforming
    folders are only checked in the (object, pipeline) pairs actually
    requested and present for this dataset (see _known_object_pipelines)."""
    project_root = _make_washu_like(tmp_path)
    _touch(project_root / "UNIPD" / "WashU" / "derivatives" / "manual_masks" / "sub-TEST" / "anat" / "placeholder.txt")
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
    _touch(project_root / "UNIPD" / "WashU" / "derivatives" / "manual_masks" / "sub-TEST" / "anat" / "placeholder.txt")
    config = _make_config(tmp_path, project_root, group_filter=["ST"])
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)  # must not raise
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].non_conforming == [
        "UNIPD/WashU: sub-TEST - does not match expected subject naming, excluded from retrieval"
    ]


def test_missing_entry_is_tagged_and_says_not_found_when_derivatives_dir_absent(tmp_path):
    """sub-STUNIPD0002 gets a manual_masks container folder (derivatives/
    manual_masks/sub-STUNIPD0002/anat/) with unrelated content, so it *is* a
    known subject there (a folder identifies it - see
    _known_object_pipelines), but the folder has no lesion_mask file inside -
    describe_absence must say "not found", not "empty folder" (that's only
    when the folder exists but has nothing in it at all - see
    test_dataset_lesion.py). Tagged with its path_key() group so multi-item
    runs can be sub-grouped (see _build_report tests)."""
    root = tmp_path / "UNIPD" / "WashU"
    _touch(
        root / "derivatives" / "manual_masks" / "sub-STUNIPD0001" / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    _touch(root / "derivatives" / "manual_masks" / "sub-STUNIPD0002" / "anat" / "other_file.txt")
    config = _make_config(tmp_path, tmp_path, group_filter=["ST"])
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].missing == [
        ReportEntry(
            group="lesion/manual_masks/anat/lesion_mask",
            line="UNIPD/WashU: sub-STUNIPD0002 - no lesion/manual_masks/anat/lesion_mask (not found)",
        )
    ]


def test_subject_known_only_via_feature_is_not_reported_as_missing_for_lesion(tmp_path):
    """Regression (adapted): discovery must stay scoped to exactly the
    (object, pipeline) pairs this run's `retrieve` list asks for - a subject
    known only under some *other* object (here: feature, not requested at
    all) must not be selected, counted, or reported as missing. The
    file_patterns registry knows about `feature` (a real WashU subject has a
    feature file), but since `retrieve` never asks for it, that subject stays
    entirely invisible to this run - the broader "what does this dataset have
    everywhere" picture is data_summary's job (src.retrieval.matrix), not
    this report's."""
    project_root = _make_washu_like(tmp_path)
    feature_root = tmp_path / "features"
    _touch(feature_root / "UNIPD" / "WashU" / "sub-STUNIPD0099" / "func" / "sub-STUNIPD0099_FC-pearson.csv")
    config = _make_config(tmp_path, project_root, feature_root=feature_root, group_filter=None)
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].subjects_selected == 3  # only the 3 real lesion subjects
    assert stats["UNIPD/WashU"].missing == []
    assert stats["UNIPD/WashU"].copied == 3


def test_retrieve_subject_copies_every_matching_template(tmp_path):
    """If a subject has files matching more than one registered template for
    the same leaf, all of them get copied - there is no priority/ambiguity
    concept anymore (see FilePatterns docstring: "grab every one of these
    that exists")."""
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "derivatives" / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    _touch(
        root / "derivatives" / "manual_masks" / "sub-STUNIPD0001" / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    file_patterns = FilePatterns(
        project_roots={"lesion": tmp_path},
        patterns={
            ("lesion", "manual_masks", "anat", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz",
                "derivatives/manual_masks/{subject_id}/anat/"
                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz",
            ]
        },
    )
    config = _make_config(
        tmp_path,
        tmp_path,
        file_patterns=file_patterns,
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
        tmp_path,
        project_root,
        group_filter=["PD"],
        subjects=["sub-STUNIPD0001", "sub-STUNIPD0002"],
    )
    assert retrieve_data._select_subjects(ds, config) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_validate_retrieve_items_raises_when_no_item_applies_to_dataset_at_all(tmp_path):
    """A dataset supporting NONE of the requested retrieve items at all is a
    STOP, not a silent 0-subjects success - very likely the wrong dataset was
    listed in `datasets`."""
    project_root = _make_washu_like(tmp_path)
    feature_root = tmp_path / "features"  # never populated - UNIPD/WashU subfolder doesn't exist under it
    config = _make_config(
        tmp_path,
        project_root,
        feature_root=feature_root,
        group_filter=None,  # a group_filter would raise its own "matches 0 subjects" first
        retrieve=[RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson")],
    )
    datasets = retrieve_data._build_datasets(config)
    with pytest.raises(ValueError, match="none of the requested"):
        retrieve_data._validate_upfront(datasets, config)


def test_retrieve_dataset_warns_and_skips_when_object_absent_from_dataset(tmp_path):
    """WARNING, not STOP: a retrieve item whose object this dataset
    structurally lacks (feature has no root here) is skipped for this
    dataset only - the lesion item still runs normally. Mirrors the pattern
    src.retrieval.matrix already implements for the data_summary report."""
    project_root = _make_washu_like(tmp_path)
    feature_root = tmp_path / "features"  # never populated for UNIPD/WashU
    config = _make_config(
        tmp_path,
        project_root,
        feature_root=feature_root,
        group_filter=None,
        retrieve=[
            RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask"),
            RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson"),
        ],
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)  # must not raise - the lesion item alone is enough
    stats = retrieve_data._retrieve_all(datasets, config)
    assert stats["UNIPD/WashU"].skipped_objects == [
        "UNIPD/WashU: object='feature' not present in this dataset - skipping feature/func/FC-pearson"
    ]
    assert stats["UNIPD/WashU"].copied == 3  # lesion still copied normally for all 3 subjects
    assert stats["UNIPD/WashU"].missing == []  # feature item skipped entirely, not reported per-subject


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


def test_copy_one_tracks_participants_outcome_separately_from_data_counts(tmp_path):
    """Regression: participants.tsv used to fold into the same
    copied/skipped_existing counters as data files (lesion masks/feature
    CSVs), making those counts off-by-one against the real number of data
    files copied - e.g. a real run against WashU showed 203 "copied" for
    202 real manual_masks subjects, the +1 being participants.tsv.
    `is_participants=True` must route the outcome into
    `stats.participants_outcome` instead."""
    source = tmp_path / "participants.tsv"
    source.write_bytes(b"data")
    destination = tmp_path / "out" / "participants.tsv"
    stats = retrieve_data.DatasetStats()

    retrieve_data._copy_one(
        source, destination, overwrite=False, stats=stats, label="test", is_participants=True
    )
    assert stats.participants_outcome == "copied"
    assert stats.copied == 0  # must not count towards data-file totals

    stats2 = retrieve_data.DatasetStats()
    retrieve_data._copy_one(
        source, destination, overwrite=False, stats=stats2, label="test", is_participants=True
    )
    assert stats2.participants_outcome == "skipped (exists)"
    assert stats2.skipped_existing == 0


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
        label="UNIPD/WashU: sub-A - lesion/manual_masks/anat/lesion_mask",
        group="lesion/manual_masks/anat/lesion_mask",
    )  # must not raise
    assert len(stats.failed) == 1
    assert stats.failed[0] == ReportEntry(
        group="lesion/manual_masks/anat/lesion_mask",
        line="UNIPD/WashU: sub-A - lesion/manual_masks/anat/lesion_mask: copy failed (disk full)",
    )
    assert stats.copied == 0


def test_copy_one_logs_and_continues_when_destination_parent_cannot_be_created(tmp_path):
    """Regression, found via fuzzing config/output_root values: mkdir() used
    to run outside the try/except, so a destination whose parent directory
    can't be created (e.g. a path component collides with an existing
    plain file - output_root itself, or any intermediate segment) crashed
    the whole run with a raw traceback instead of a per-file Failed entry."""
    source = tmp_path / "source.nii.gz"
    source.write_bytes(b"data")
    blocked = tmp_path / "blocked_by_a_file"
    blocked.write_text("i am a file, not a directory")
    destination = blocked / "subdir" / "dest.nii.gz"  # blocked/ can never contain a subdir/
    stats = retrieve_data.DatasetStats()
    retrieve_data._copy_one(source, destination, overwrite=False, stats=stats, label="test")  # must not raise
    assert len(stats.failed) == 1
    assert "copy failed" in stats.failed[0].line
    assert stats.copied == 0


def test_full_run_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    project_root = _make_washu_like(tmp_path)
    config = _make_config(tmp_path, project_root, group_filter=None)

    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)

    # All 3 subjects (2 ST + 1 HC) have a lesion_mask, all 3 should be copied.
    assert stats["UNIPD/WashU"].copied == 3
    assert stats["UNIPD/WashU"].missing == []

    copied_file = (
        tmp_path
        / "data"
        / "clinical_connectome"
        / "derivatives"
        / "UNIPD"
        / "WashU"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    )
    assert copied_file.is_file()

    report_path = retrieve_data._write_report(config, stats)
    report_text = report_path.read_text()
    assert "UNIPD/WashU" in report_text
    # 3 copied, 0 skipped, 0 failed, no fatal error.
    assert "| UNIPD/WashU | 3 | 0 | 0 | — | — |" in report_text


def test_retrieve_all_records_fatal_error_without_losing_other_datasets_stats(tmp_path, monkeypatch):
    """Regression: _retrieve_dataset raising for one dataset (e.g. a broken
    registry path caught only at runtime) used to propagate straight out of
    _retrieve_all, losing the DatasetStats already collected - for every
    dataset, not just the failing one - and preventing _write_report from
    ever running (see main()). Now the exception is caught per-dataset:
    everything copied before the error is still counted, a sibling dataset
    that raises nothing runs to completion including verification, and the
    failure itself is recorded on DatasetStats.fatal_error instead of
    disappearing."""
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    project_root = _make_washu_like(tmp_path)
    (tmp_path / "UNIPD" / "PASPORT").mkdir(parents=True)
    for subject_id in ["sub-STUNIPD0001"]:
        _touch(
            tmp_path / "UNIPD" / "PASPORT" / "derivatives" / "manual_masks" / subject_id / "anat"
            / f"{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
        )
    config = _make_config(
        tmp_path, project_root, group_filter=None, datasets=["UNIPD/WashU", "UNIPD/PASPORT"]
    )
    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)

    real_retrieve_dataset = retrieve_data._retrieve_dataset

    def _raise_for_washu(name, ds, config, stats):
        if name == "UNIPD/WashU":
            raise FileNotFoundError("dataset root not found: /broken/path")
        return real_retrieve_dataset(name, ds, config, stats)

    monkeypatch.setattr(retrieve_data, "_retrieve_dataset", _raise_for_washu)

    stats = retrieve_data._retrieve_all(datasets, config)

    assert stats["UNIPD/WashU"].fatal_error == "dataset root not found: /broken/path"
    assert stats["UNIPD/WashU"].copied == 0
    # Sibling dataset unaffected - copied and verified normally.
    assert stats["UNIPD/PASPORT"].fatal_error is None
    assert stats["UNIPD/PASPORT"].copied == 1
    assert stats["UNIPD/PASPORT"].mismatched == []

    report_path = retrieve_data._write_report(config, stats)
    report_text = report_path.read_text()
    assert "## FATAL - retrieval aborted partway through" in report_text
    assert "**UNIPD/WashU**: dataset root not found: /broken/path" in report_text
    assert "| UNIPD/WashU | 0 | 0 | 0 | — | dataset root not found: /broken/path |" in report_text
    assert "| UNIPD/PASPORT | 1 | 0 | 0 | — | — |" in report_text


def _minimal_config(tmp_path, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_make_patterns(tmp_path / "source"),
        datasets=["UNIPD/WashU", "UNIPD/PASPORT"],
        group_filter=["ST"],
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")],
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
                ReportEntry(
                    group="lesion/manual_masks/anat/lesion_mask",
                    line="UNIPD/WashU: sub-A - no lesion/manual_masks/anat/lesion_mask",
                ),
                ReportEntry(
                    group="lesion/manual_masks/anat/lesion_mask",
                    line="UNIPD/WashU: sub-B - no lesion/manual_masks/anat/lesion_mask",
                ),
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(
                    group="lesion/manual_masks/anat/lesion_mask",
                    line="UNIPD/PASPORT: sub-C - no lesion/manual_masks/anat/lesion_mask",
                )
            ]
        ),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    expected_block = (
        "**lesion/manual_masks/anat/lesion_mask** (2)\n"
        "- UNIPD/WashU: sub-A - no lesion/manual_masks/anat/lesion_mask\n"
        "- UNIPD/WashU: sub-B - no lesion/manual_masks/anat/lesion_mask\n"
        "\n"
        "File Not Found Count = 2\n"
        "\n"
        "---\n"
        "\n"
        "**lesion/manual_masks/anat/lesion_mask** (1)\n"
        "- UNIPD/PASPORT: sub-C - no lesion/manual_masks/anat/lesion_mask\n"
        "\n"
        "File Not Found Count = 1"
    )
    assert expected_block in report


def test_build_report_sub_groups_missing_by_retrieve_item_within_one_dataset(tmp_path):
    """A run requesting more than one retrieve item must not interleave
    their misses into one flat list per dataset - each gets its own
    sub-heading and count, so a reader can scan one item at a time."""
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(
                    group="lesion/manual_masks/anat/lesion_mask",
                    line="UNIPD/WashU: sub-A - no lesion/manual_masks/anat/lesion_mask",
                ),
                ReportEntry(
                    group="feature/func/FC-pearson", line="UNIPD/WashU: sub-A - no feature/func/FC-pearson"
                ),
                ReportEntry(
                    group="lesion/manual_masks/anat/lesion_mask",
                    line="UNIPD/WashU: sub-B - no lesion/manual_masks/anat/lesion_mask",
                ),
            ]
        ),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    expected_block = (
        "**lesion/manual_masks/anat/lesion_mask** (2)\n"
        "- UNIPD/WashU: sub-A - no lesion/manual_masks/anat/lesion_mask\n"
        "- UNIPD/WashU: sub-B - no lesion/manual_masks/anat/lesion_mask\n"
        "\n"
        "**feature/func/FC-pearson** (1)\n"
        "- UNIPD/WashU: sub-A - no feature/func/FC-pearson\n"
        "\n"
        "File Not Found Count = 3"
    )
    assert expected_block in report


def test_build_report_omits_dataset_with_no_missing_entries(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            missing=[
                ReportEntry(
                    group="lesion/manual_masks/anat/lesion_mask",
                    line="UNIPD/WashU: sub-A - no lesion/manual_masks/anat/lesion_mask",
                )
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(missing=[]),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    missing_section = report.split("## File not found")[1].split("## Skipped")[0]
    assert "UNIPD/PASPORT" not in missing_section
    assert missing_section.count("File Not Found Count") == 1


def test_build_report_includes_failed_section(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            failed=[
                ReportEntry(
                    group="lesion/manual_masks/anat/lesion_mask",
                    line="UNIPD/WashU: sub-A - lesion/manual_masks/anat/lesion_mask: copy failed (disk full)",
                )
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    assert "## Failed" in report
    assert "Failed Count = 1" in report
    assert "| UNIPD/WashU | 0 | 0 | 1 | — | — |" in report  # summary table's failed column reflects len(failed)


def test_build_report_includes_skipped_objects_section(tmp_path):
    config = _minimal_config(tmp_path)
    stats = {
        "UNIPD/WashU": retrieve_data.DatasetStats(
            skipped_objects=[
                "UNIPD/WashU: object='feature' not present in this dataset - skipping feature/func/FC-pearson"
            ]
        ),
        "UNIPD/PASPORT": retrieve_data.DatasetStats(),
    }
    report = retrieve_data._build_report(config, stats, datetime(2026, 7, 9, 10, 22))
    assert "## Skipped - object not present in this dataset" in report
    assert "Skipped Count = 1" in report


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
            mismatched=[
                "UNIPD/WashU: sub-A lesion/manual_masks/anat/lesion_mask - checksum differs from source: /a vs /b"
            ]
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
                    "manual_masks": {
                        "anat": {
                            "lesion_mask": [
                                "derivatives/manual_masks/{subject_id}/anat/"
                                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
                            ]
                        }
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
        "retrieve": [{"object": "lesion", "pipeline": "manual_masks", "datatype": "anat", "suffix": "lesion_mask"}],
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


def test_main_still_writes_report_when_participants_tsv_fetch_raises(tmp_path, monkeypatch, caplog):
    """Regression for the real incident this was modeled on: a broken
    file_patterns.json project_root made participants_tsv_path() raise
    FileNotFoundError - which used to propagate straight out of
    _retrieve_all/main() before _write_report ever ran, even though every
    subject had already been copied successfully. Now main() still writes
    the report (with everything copied, plus a FATAL entry) and exits 1,
    instead of leaving no report/no trace of the completed copy work."""
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(retrieve_data, "LOGS_ROOT", tmp_path / "logs")
    project_root = _make_washu_like(tmp_path / "source")
    config_path = tmp_path / "config.json"
    _write_json_config(config_path, project_root, tmp_path / "data", include_tabular_data=True)

    def _raise(ds):
        raise FileNotFoundError("dataset root not found: /data/corbetta/Clinical_connectome/derivatives/UNIPD/WashU")

    monkeypatch.setattr(Dataset, "participants_tsv_path", _raise)

    exit_code = retrieve_data.main(["--config", str(config_path)])

    assert exit_code == 1
    assert "retrieval aborted partway through for dataset(s)" in caplog.text

    report_files = list((tmp_path / "reports" / "clinical_connectome").glob("*.md"))
    assert len(report_files) == 1  # the report IS written despite the crash
    report_text = report_files[0].read_text()
    assert "## FATAL - retrieval aborted partway through" in report_text
    assert "dataset root not found" in report_text
    # The 3 subjects were copied before participants.tsv was ever attempted.
    assert "| UNIPD/WashU | 3 | 0 | 0 | — |" in report_text


def test_main_stops_cleanly_when_log_directory_cannot_be_created(tmp_path, monkeypatch, caplog):
    """Regression: _log_path()/_attach_file_handler() used to run outside any
    try/except in main() - an unwritable log location (here: a plain file
    sitting where the log directory needs to be) crashed with a raw
    traceback instead of a clean stop."""
    blocked_logs_root = tmp_path / "logs_is_a_file"
    blocked_logs_root.write_text("i am a file, not a directory")
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(retrieve_data, "LOGS_ROOT", blocked_logs_root)
    project_root = _make_washu_like(tmp_path / "source")
    config_path = tmp_path / "config.json"
    _write_json_config(config_path, project_root, tmp_path / "data")

    exit_code = retrieve_data.main(["--config", str(config_path)])  # must not raise

    assert exit_code == 1
    assert "cannot set up log file" in caplog.text


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
        / "derivatives"
        / "UNIPD"
        / "WashU"
        / "manual_masks"
        / "sub-STUNIPD0001"
        / "anat"
        / "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
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
    # copying (3 subjects have lesion_mask, 1 skipped as stale-but-existing) happened before verification
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
