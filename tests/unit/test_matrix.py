"""Unit tests for src.retrieval.matrix - synthetic fixtures, no EBRAIN mount needed."""

from src.retrieval import matrix
from src.retrieval.config import FilePatterns, RetrievalConfig
from src.retrieval.dataset import Dataset


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _make_washu_like(tmp_path):
    """sub-0001 has T1w + mni mask (no lesion_roi); sub-0002 has only T1w."""
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
    return tmp_path


def _make_patterns(project_root):
    return FilePatterns(
        project_roots={"lesion": project_root},
        patterns={
            ("lesion", "native", "T1w"): ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
            ("lesion", "native", "lesion_roi"): ["{subject_id}/anat/{subject_id}_lesion_roi.nii.gz"],
            ("lesion", "mni", "lesion_mask"): [
                "derivatives/manual_masks/{subject_id}/anat/"
                "{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
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
        ("lesion", "mni", "lesion_mask"),
        ("lesion", "native", "T1w"),
        ("lesion", "native", "lesion_roi"),
    ]


def test_build_matrix_reports_filename_when_present_and_missing_marker_when_absent(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    combinations = [("lesion", "native", "T1w"), ("lesion", "native", "lesion_roi"), ("lesion", "mni", "lesion_mask")]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001", "sub-STUNIPD0002"], combinations)

    row1 = next(r for r in rows if r.subject_id == "sub-STUNIPD0001")
    assert row1.cells["lesion/native/T1w"] == "sub-STUNIPD0001_T1w.nii.gz"
    assert row1.cells["lesion/native/lesion_roi"] == matrix.MISSING_CELL
    assert row1.cells["lesion/mni/lesion_mask"] == "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"

    row2 = next(r for r in rows if r.subject_id == "sub-STUNIPD0002")
    assert row2.cells["lesion/native/T1w"] == "sub-STUNIPD0002_T1w.nii.gz"
    assert row2.cells["lesion/mni/lesion_mask"] == matrix.MISSING_CELL


def test_count_present_counts_non_missing_cells_per_column(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    combinations = [("lesion", "native", "T1w"), ("lesion", "native", "lesion_roi"), ("lesion", "mni", "lesion_mask")]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001", "sub-STUNIPD0002"], combinations)

    counts = matrix.count_present(rows, combinations)
    assert counts == {
        "lesion/native/T1w": 2,
        "lesion/native/lesion_roi": 0,
        "lesion/mni/lesion_mask": 1,
    }


def test_to_csv_rows_uses_present_and_missing_markers_with_trailing_count_row(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    combinations = [("lesion", "native", "T1w"), ("lesion", "native", "lesion_roi"), ("lesion", "mni", "lesion_mask")]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001", "sub-STUNIPD0002"], combinations)

    csv_rows = matrix.to_csv_rows(rows, combinations)
    assert csv_rows == [
        ["subject", "lesion/native/T1w", "lesion/native/lesion_roi", "lesion/mni/lesion_mask"],
        ["sub-STUNIPD0001", "-", "missing", "-"],
        ["sub-STUNIPD0002", "-", "missing", "missing"],
        ["present", "2", "0", "1"],
    ]


def test_select_all_subjects_unions_across_every_registered_space(tmp_path):
    """sub-STUNIPD0002 only has native data - select_all_subjects must still
    include them, even though config.retrieve/group_filter isn't involved at
    all here (unlike retrieve_data._select_subjects, this looks at every
    (object, space) the registry knows about, not just what a run
    requests)."""
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _minimal_config(tmp_path, _make_patterns(project_root))
    assert matrix.select_all_subjects(ds, config) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_select_all_subjects_respects_explicit_subjects_filter(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset("UNIPD/WashU", _make_patterns(project_root))
    config = _minimal_config(tmp_path, _make_patterns(project_root), subjects=["sub-STUNIPD0002"])
    assert matrix.select_all_subjects(ds, config) == ["sub-STUNIPD0002"]
