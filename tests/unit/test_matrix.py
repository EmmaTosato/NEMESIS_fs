"""Unit tests for src.retrieval.matrix - synthetic fixtures, no EBRAIN mount needed."""

import pytest

from src.retrieval import matrix
from src.retrieval.config import FilePatterns, RetrievalConfig
from src.retrieval.dataset import Dataset


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _make_washu_like(tmp_path):
    """sub-0001 has a manual_masks lesion_mask (no other_mask); sub-0002 has
    only other_mask (no lesion_mask) - both live under the same
    derivatives/manual_masks/ pipeline folder, so both must still be
    discoverable via that shared container."""
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "derivatives" / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    _touch(root / "derivatives" / "manual_masks" / "sub-STUNIPD0002" / "anat" / "sub-STUNIPD0002_label-other_mask.nii.gz")
    return tmp_path


def _make_patterns(project_root):
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={
            ("lesion", "manual_masks", "anat", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz"
            ],
            ("lesion", "manual_masks", "anat", "other_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-other_mask.nii.gz"
            ],
        },
    )


def _minimal_config(tmp_path, file_patterns, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=file_patterns,
        datasets=["UNIPD/WashU"],
        group_filter=None,
        subjects=None,
        retrieve=[],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_combinations_from_file_patterns_orders_combinations(tmp_path):
    project_root = _make_washu_like(tmp_path)
    config = _minimal_config(tmp_path, _make_patterns(project_root))
    assert matrix.combinations_from_file_patterns(config) == [
        ("lesion", "manual_masks", "anat", "lesion_mask"),
        ("lesion", "manual_masks", "anat", "other_mask"),
    ]


def test_build_matrix_reports_filename_when_present_and_missing_marker_when_absent(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    combinations = [
        ("lesion", "manual_masks", "anat", "lesion_mask"),
        ("lesion", "manual_masks", "anat", "other_mask"),
    ]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001", "sub-STUNIPD0002"], combinations)

    row1 = next(r for r in rows if r.subject_id == "sub-STUNIPD0001")
    assert row1.cells["lesion/manual_masks/anat/lesion_mask"].filename == "sub-STUNIPD0001_label-lesion_mask.nii.gz"
    assert row1.cells["lesion/manual_masks/anat/lesion_mask"].marker() == matrix.PRESENT_CELL
    assert row1.cells["lesion/manual_masks/anat/other_mask"].marker() == matrix.MISSING_CELL

    row2 = next(r for r in rows if r.subject_id == "sub-STUNIPD0002")
    assert row2.cells["lesion/manual_masks/anat/lesion_mask"].marker() == matrix.MISSING_CELL
    assert row2.cells["lesion/manual_masks/anat/other_mask"].filename == "sub-STUNIPD0002_label-other_mask.nii.gz"
    assert row2.cells["lesion/manual_masks/anat/other_mask"].marker() == matrix.PRESENT_CELL


def test_build_matrix_reports_incomplete_when_some_but_not_all_templates_match(tmp_path):
    """A leaf registering more than one template (e.g. feature/func/FC-pearson's
    12 per-atlas files) is not a naming-variant alternate here - all of them
    are expected to coexist per subject. A subject with only 1 of 2
    registered templates must show as incomplete, not present."""
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "derivatives" / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    file_patterns = FilePatterns(
        project_roots={"lesion": tmp_path},
        patterns={
            ("lesion", "manual_masks", "anat", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz",
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_extra-lesion_mask.nii.gz",
            ]
        },
    )
    ds = Dataset("UNIPD/WashU", file_patterns)
    combinations = [("lesion", "manual_masks", "anat", "lesion_mask")]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001"], combinations)

    cell = rows[0].cells["lesion/manual_masks/anat/lesion_mask"]
    assert cell.matched == 1
    assert cell.total == 2
    assert cell.marker() == matrix.INCOMPLETE_CELL


def test_to_csv_rows_uses_present_and_missing_markers(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    combinations = [
        ("lesion", "manual_masks", "anat", "lesion_mask"),
        ("lesion", "manual_masks", "anat", "other_mask"),
    ]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001", "sub-STUNIPD0002"], combinations)

    csv_rows = matrix.to_csv_rows(rows, combinations)
    assert csv_rows == [
        ["subject", "lesion/manual_masks/anat/lesion_mask", "lesion/manual_masks/anat/other_mask"],
        ["sub-STUNIPD0001", "present", "missing"],
        ["sub-STUNIPD0002", "missing", "present"],
    ]


def test_to_csv_rows_uses_incomplete_marker_when_some_templates_missing(tmp_path):
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "derivatives" / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii.gz")
    file_patterns = FilePatterns(
        project_roots={"lesion": tmp_path},
        patterns={
            ("lesion", "manual_masks", "anat", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz",
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_extra-lesion_mask.nii.gz",
            ]
        },
    )
    ds = Dataset("UNIPD/WashU", file_patterns)
    combinations = [("lesion", "manual_masks", "anat", "lesion_mask")]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001"], combinations)

    assert matrix.to_csv_rows(rows, combinations) == [
        ["subject", "lesion/manual_masks/anat/lesion_mask"],
        ["sub-STUNIPD0001", "incomplete"],
    ]


def test_select_all_subjects_unions_across_every_registered_pipeline(tmp_path):
    """sub-STUNIPD0002 only has the other_mask file - select_all_subjects
    must still include them, even though config.retrieve/group_filter isn't
    involved at all here (unlike retrieve_data._select_subjects, this looks
    at every (object, pipeline) the registry knows about, not just what a
    run requests)."""
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _minimal_config(tmp_path, _make_patterns(project_root))
    assert matrix.select_all_subjects(ds, config) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_select_all_subjects_respects_explicit_subjects_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _minimal_config(tmp_path, _make_patterns(project_root), subjects=["sub-STUNIPD0002"])
    assert matrix.select_all_subjects(ds, config) == ["sub-STUNIPD0002"]


def _make_patterns_with_missing_feature_root(project_root):
    """Registers a `feature` object whose project_root points at a directory
    that is never created on disk - mirrors real data (PASPORT/PSP/UKLFR
    have no `features/` tree at all, only WashU does)."""
    patterns = _make_patterns(project_root)
    return FilePatterns(
        project_roots={**patterns.project_roots, "feature": project_root / "features"},
        patterns={
            **patterns.patterns,
            ("feature", "func", "FC-pearson"): ["{subject_id}/func/{subject_id}_FC-pearson.csv"],
        },
    )


def test_select_all_subjects_skips_object_with_no_root_on_this_dataset(tmp_path):
    """A registered object (feature) whose root doesn't exist for this
    dataset must not crash discovery - it's a legitimate "nothing to report
    here", not a failure (see Dataset.has_object)."""
    project_root = _make_washu_like(tmp_path)
    file_patterns = _make_patterns_with_missing_feature_root(project_root)
    ds = Dataset("UNIPD/WashU", file_patterns)
    config = _minimal_config(tmp_path, file_patterns)
    assert matrix.select_all_subjects(ds, config) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_validate_subject_filters_raises_for_unknown_explicit_subject(tmp_path):
    """Regression: scripts/data_summary.py used to call select_all_subjects
    directly with no upfront check - a typo'd subjects entry silently
    selected zero subjects (found & set(config.subjects) is empty), the
    report ended up with only a header row, and nothing signaled why."""
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _minimal_config(tmp_path, _make_patterns(project_root), subjects=["sub-STUNIPD9999"])
    with pytest.raises(ValueError, match="sub-STUNIPD9999"):
        matrix.validate_subject_filters(ds, config, "UNIPD/WashU")


def test_validate_subject_filters_raises_when_group_filter_matches_nobody(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _minimal_config(tmp_path, _make_patterns(project_root), group_filter=["PD"])
    with pytest.raises(ValueError, match="group_filter"):
        matrix.validate_subject_filters(ds, config, "UNIPD/WashU")


def test_validate_subject_filters_passes_for_valid_explicit_subject(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _minimal_config(tmp_path, _make_patterns(project_root), subjects=["sub-STUNIPD0001"])
    matrix.validate_subject_filters(ds, config, "UNIPD/WashU")  # must not raise


def test_validate_subject_filters_does_not_raise_for_genuinely_empty_dataset(tmp_path):
    """A dataset that structurally has no subjects at all (no filter set) is
    a legitimate "nothing to report" case, not a config mistake - distinct
    from a filter that excludes an otherwise non-empty dataset."""
    file_patterns = _make_patterns(tmp_path / "nonexistent")
    ds = Dataset("UNIPD/WashU", file_patterns)
    config = _minimal_config(tmp_path, file_patterns, group_filter=["ST"])
    matrix.validate_subject_filters(ds, config, "UNIPD/WashU")  # must not raise


def test_build_matrix_marks_missing_for_object_with_no_root_on_this_dataset(tmp_path):
    project_root = _make_washu_like(tmp_path)
    file_patterns = _make_patterns_with_missing_feature_root(project_root)
    ds = Dataset("UNIPD/WashU", file_patterns)
    combinations = matrix.combinations_from_file_patterns(_minimal_config(tmp_path, file_patterns))
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001"], combinations)
    assert rows[0].cells["feature/func/FC-pearson"].marker() == matrix.MISSING_CELL
