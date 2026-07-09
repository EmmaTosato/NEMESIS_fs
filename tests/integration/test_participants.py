"""Integration tests for Dataset.participants() against the real EBRAIN data.

Skipped entirely if the mount is not reachable on this machine.
"""

from pathlib import Path

import pytest

from src.retrieval.config import FilePatterns
from src.retrieval.dataset import Dataset

PROJECT_ROOT = Path("/data/corbetta/Clinical_connectome")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)

# participants() never touches file_patterns - an empty registry is enough.
_EMPTY_PATTERNS = FilePatterns(patterns={})


def test_washu_has_no_participants_tsv():
    ds = Dataset(PROJECT_ROOT, "UNIPD/WashU", _EMPTY_PATTERNS)
    assert ds.participants() is None


@pytest.mark.parametrize(
    "dataset_name", ["UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"]
)
def test_other_datasets_have_participants_tsv(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name, _EMPTY_PATTERNS)
    df = ds.participants()
    assert df is not None
    assert "participant_id" in df.columns
    assert len(df) == len(ds.subjects())
