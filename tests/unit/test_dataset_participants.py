"""Unit tests for Dataset.participants()."""

from src.retrieval.config import FilePatterns
from src.retrieval.dataset import Dataset


def _make_patterns(project_root):
    # participants() never touches the modality registry - project_root is the
    # only thing it needs (participants.tsv always lives under the lesion root).
    return FilePatterns(project_roots={"lesion": project_root}, patterns={})


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def test_participants_returns_none_when_absent(tmp_path):
    root = tmp_path / "UNIPD" / "WashU"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_T1w.nii.gz")
    ds = Dataset("UNIPD/WashU", _make_patterns(tmp_path))
    assert ds.participants() is None
    assert ds.participants_tsv_path() is None


def test_participants_returns_dataframe_when_present(tmp_path):
    root = tmp_path / "UNIPD" / "PASPORT"
    _touch(root / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_CT.nii.gz")
    (root / "participants.tsv").write_text(
        "participant_id\tage\tsex\nsub-STUNIPD0001\t54\tM\n"
    )
    ds = Dataset("UNIPD/PASPORT", _make_patterns(tmp_path))
    df = ds.participants()
    assert df is not None
    assert list(df.columns) == ["participant_id", "age", "sex"]
    assert df.iloc[0]["participant_id"] == "sub-STUNIPD0001"
    assert df.iloc[0]["age"] == "54"
    assert ds.participants_tsv_path() == root / "participants.tsv"
