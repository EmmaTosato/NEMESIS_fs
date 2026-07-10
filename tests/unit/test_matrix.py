"""Unit tests for src.retrieval.matrix - synthetic fixtures, no EBRAIN mount needed."""

from src.retrieval import matrix
from src.retrieval.config import FilePatterns, RetrievalConfig
from src.retrieval.dataset import Dataset

_FILE_PATTERNS = FilePatterns(
    patterns={
        ("native", "T1w"): ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
        ("native", "lesion_roi"): ["{subject_id}/anat/{subject_id}_lesion_roi.nii.gz"],
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


def _minimal_config(tmp_path, project_root):
    return RetrievalConfig(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        project_root=project_root,
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=_FILE_PATTERNS,
        datasets=["UNIPD/WashU"],
        group_filter=None,
        subjects=None,
        retrieve=[],
        include_tabular_data=False,
        overwrite=False,
    )


def test_combinations_from_file_patterns_orders_native_before_mni(tmp_path):
    project_root = _make_washu_like(tmp_path)
    config = _minimal_config(tmp_path, project_root)
    assert matrix.combinations_from_file_patterns(config) == [
        ("native", "T1w"),
        ("native", "lesion_roi"),
        ("mni", "lesion_mask"),
    ]


def test_build_matrix_reports_filename_when_present_and_missing_marker_when_absent(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU", _FILE_PATTERNS)
    combinations = [("native", "T1w"), ("native", "lesion_roi"), ("mni", "lesion_mask")]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001", "sub-STUNIPD0002"], combinations)

    row1 = next(r for r in rows if r.subject_id == "sub-STUNIPD0001")
    assert row1.cells["native/T1w"] == "sub-STUNIPD0001_T1w.nii.gz"
    assert row1.cells["native/lesion_roi"] == matrix.MISSING_CELL
    assert row1.cells["mni/lesion_mask"] == "sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"

    row2 = next(r for r in rows if r.subject_id == "sub-STUNIPD0002")
    assert row2.cells["native/T1w"] == "sub-STUNIPD0002_T1w.nii.gz"
    assert row2.cells["mni/lesion_mask"] == matrix.MISSING_CELL


def test_count_present_counts_non_missing_cells_per_column(tmp_path):
    project_root = _make_washu_like(tmp_path)
    ds = Dataset(project_root, "UNIPD/WashU", _FILE_PATTERNS)
    combinations = [("native", "T1w"), ("native", "lesion_roi"), ("mni", "lesion_mask")]
    rows = matrix.build_matrix(ds, ["sub-STUNIPD0001", "sub-STUNIPD0002"], combinations)

    counts = matrix.count_present(rows, combinations)
    assert counts == {"native/T1w": 2, "native/lesion_roi": 0, "mni/lesion_mask": 1}
