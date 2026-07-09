"""Integration tests against the real EBRAIN-mounted Clinical_connectome data.

Skipped entirely if the mount is not reachable on this machine. These counts
were verified manually against the real filesystem during design and act as
a regression anchor: a mismatch signals a bug in the file_patterns registry
or the resolution logic, not a change in the (static) source data. Uses the
real config/file_patterns.json registry, not a synthetic one, since the
whole point here is verifying the production mapping against real data.
"""

from pathlib import Path

import pytest

from src.retrieval.config import load_file_patterns
from src.retrieval.dataset import Dataset

PROJECT_ROOT = Path("/data/corbetta/Clinical_connectome")
FILE_PATTERNS_PATH = Path("config/file_patterns.json")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)

FILE_PATTERNS = load_file_patterns(FILE_PATTERNS_PATH) if FILE_PATTERNS_PATH.is_file() else None

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

EXPECTED_AVAILABLE_MODALITIES = {
    "UNIPD/WashU": {"T1w", "T2w", "FLAIR", "lesion_roi"},
    "UNIPD/PASPORT": {"CT", "FLAIR", "lesion_roi"},
    "UNIPD/PSP": {"CT", "FLAIR"},
    "UKLFR/stroke_UKLFR": {"T1w", "T2w", "FLAIR", "lesion_roi"},
}

ALL_NATIVE_MODALITIES = ("T1w", "T2w", "FLAIR", "CT", "lesion_roi")


@pytest.mark.parametrize("dataset_name", list(EXPECTED_MNI_MASK_ST_COUNT))
def test_mni_mask_count_matches_verified_numbers(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name, FILE_PATTERNS)
    count = sum(1 for sub in ds.subjects() if ds.resolve(sub, "mni", "lesion_mask") is not None)
    assert count == EXPECTED_MNI_MASK_ST_COUNT[dataset_name]


@pytest.mark.parametrize("dataset_name", list(EXPECTED_NATIVE_T1W_COUNT))
def test_native_t1w_count_matches_verified_numbers(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name, FILE_PATTERNS)
    count = sum(1 for sub in ds.subjects() if ds.resolve(sub, "native", "T1w") is not None)
    assert count == EXPECTED_NATIVE_T1W_COUNT[dataset_name]


@pytest.mark.parametrize("dataset_name", list(EXPECTED_AVAILABLE_MODALITIES))
def test_available_matches_verified_table(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name, FILE_PATTERNS)
    available = {modality for modality in ALL_NATIVE_MODALITIES if ds.available("native", modality)}
    assert available == EXPECTED_AVAILABLE_MODALITIES[dataset_name]


def test_psp_has_no_native_lesion_roi():
    ds = Dataset(PROJECT_ROOT, "UNIPD/PSP", FILE_PATTERNS)
    assert ds.available("native", "lesion_roi") is False
    assert ds.resolve(ds.subjects()[0], "native", "lesion_roi") is None


def test_no_ambiguous_matches_across_real_data():
    """Regression for the priority-list ambiguity: confirms no real subject,
    in any in-scope dataset, currently has files matching more than one
    registered lesion_roi naming variant simultaneously."""
    for dataset_name in EXPECTED_AVAILABLE_MODALITIES:
        ds = Dataset(PROJECT_ROOT, dataset_name, FILE_PATTERNS)
        if not ds.available("native", "lesion_roi"):
            continue
        for subject_id in ds.subjects():
            resolved = ds.resolve(subject_id, "native", "lesion_roi")
            if resolved is not None:
                assert resolved.extra_matches == (), (
                    f"{dataset_name}: {subject_id} unexpectedly has an ambiguous "
                    f"lesion_roi match: {resolved.extra_matches}"
                )
