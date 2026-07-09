"""Integration tests against the real EBRAIN-mounted Clinical_connectome data.

Skipped entirely if the mount is not reachable on this machine. These counts
were verified manually against the real filesystem during design and act as
a regression anchor: a mismatch signals a bug in the glob/regex resolution
logic, not a change in the (static) source data.
"""

from pathlib import Path

import pytest

from src.retrieval.dataset import Dataset

PROJECT_ROOT = Path("/data/corbetta/Clinical_connectome")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)

EXPECTED_MNI_MASK_ST_COUNT = {
    # WashU: derivatives/manual_masks has 202 subject folders, but one of them
    # (sub-STUNIPD0001) is an orphaned derivative with no matching raw subject
    # folder - Dataset.subjects() (raw-based) correctly does not count it, so
    # the real reachable count is 201, not 202.
    "UNIPD/WashU": 201,
    "UNIPD/PASPORT": 83,
    "UNIPD/PSP": 168,
    "UKLFR/stroke_UKLFR": 697,
}

EXPECTED_NATIVE_T1W_COUNT = {
    "UNIPD/WashU": 296,
    "UKLFR/stroke_UKLFR": 720,
}

EXPECTED_AVAILABLE_SEQUENCES = {
    "UNIPD/WashU": {"T1w", "T2w", "FLAIR", "lesion_roi"},
    "UNIPD/PASPORT": {"CT", "FLAIR", "lesion_roi"},
    "UNIPD/PSP": {"CT", "FLAIR"},
    "UKLFR/stroke_UKLFR": {"T1w", "T2w", "FLAIR", "lesion_roi"},
}


@pytest.mark.parametrize("dataset_name", list(EXPECTED_MNI_MASK_ST_COUNT))
def test_mni_mask_count_matches_verified_numbers(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name)
    count = sum(1 for sub in ds.subjects() if ds.mni_mask(sub) is not None)
    assert count == EXPECTED_MNI_MASK_ST_COUNT[dataset_name]


@pytest.mark.parametrize("dataset_name", list(EXPECTED_NATIVE_T1W_COUNT))
def test_native_t1w_count_matches_verified_numbers(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name)
    count = sum(1 for sub in ds.subjects() if ds.native(sub, "T1w") is not None)
    assert count == EXPECTED_NATIVE_T1W_COUNT[dataset_name]


@pytest.mark.parametrize("dataset_name", list(EXPECTED_AVAILABLE_SEQUENCES))
def test_available_sequences_matches_verified_table(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name)
    assert ds.available_sequences() == EXPECTED_AVAILABLE_SEQUENCES[dataset_name]


def test_psp_has_no_native_lesion_roi():
    ds = Dataset(PROJECT_ROOT, "UNIPD/PSP")
    with pytest.raises(ValueError, match="lesion_roi"):
        ds.native(ds.subjects()[0], "lesion_roi")
