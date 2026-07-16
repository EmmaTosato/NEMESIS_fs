"""Integration tests for Dataset.participants() against the real EBRAIN data.

Skipped entirely if the mount is not reachable on this machine.

Which specific dataset has a participants.tsv is a curated fact that can
change over time (a dataset that lacked one can gain one) - not asserted here
as a fixed per-dataset truth. What's checked instead is the contract: if a
dataset has one right now, it must be well-formed.
"""

from pathlib import Path

import pytest

from src.retrieval.config import FilePatterns
from src.retrieval.dataset import Dataset

PROJECT_ROOT = Path("/data/corbetta/Clinical_connectome")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)

# participants() only needs project_root - a minimal manual_masks/lesion_mask
# registration is enough to also let subjects() (used for the row-count check
# below) work.
_PATTERNS = FilePatterns(
    project_roots={"lesion": PROJECT_ROOT},
    patterns={
        ("lesion", "manual_masks", "anat", "lesion_mask"): [
            "derivatives/manual_masks/{subject_id}/anat/{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
        ]
    },
)

ALL_DATASETS = ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"]


@pytest.mark.parametrize("dataset_name", ALL_DATASETS)
def test_participants_tsv_is_well_formed_when_present(dataset_name):
    """Row-count equality with subjects() no longer holds: unlike the old
    `native` combo (present for essentially every subject), `manual_masks` is
    a genuine subset of the full roster (not every subject has a lesion
    mask) - so only a subset relationship is checked, not equality."""
    ds = Dataset(dataset_name, _PATTERNS)
    df = ds.participants()
    if df is None:
        return  # legitimate per-dataset fact today, not asserted either way
    assert "participant_id" in df.columns
    assert set(ds.subjects("lesion", "manual_masks")) <= set(df["participant_id"])


def test_at_least_one_dataset_has_participants_tsv():
    """Sanity check that the participants() path is actually exercised by at
    least one real dataset - otherwise test_participants_tsv_is_well_formed_when_present
    could silently pass on every dataset by hitting the `df is None` return."""
    datasets = [Dataset(name, _PATTERNS) for name in ALL_DATASETS]
    assert any(ds.participants() is not None for ds in datasets)
