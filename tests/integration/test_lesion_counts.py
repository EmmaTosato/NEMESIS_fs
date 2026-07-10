"""Integration tests against the real EBRAIN-mounted Clinical_connectome data.

Skipped entirely if the mount is not reachable on this machine. Ground truth
is never a hardcoded number - the datasets are actively curated (subjects and
files are added on EBRAIN over time), so a frozen count would fail the moment
the data legitimately changes, not when the code breaks. Instead, every check
here recomputes its own expectation directly from the real filesystem at test
run time (independent of Dataset/file_patterns.json) and compares it against
what Dataset.resolve()/.available() report - a mismatch then always signals a
real discrepancy in the resolution logic, never a stale number. Uses the real
config/file_patterns.json registry, not a synthetic one, since the whole
point here is verifying the production mapping against real data.
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

# Which dataset structurally has which native modality is stable (a scanning
# protocol fact), unlike per-subject counts - safe to keep as a small fixed
# table, re-verified every run against Dataset.available().
EXPECTED_AVAILABLE_MODALITIES = {
    "UNIPD/WashU": {"T1w", "T2w", "FLAIR", "lesion_roi"},
    "UNIPD/PASPORT": {"CT", "FLAIR", "lesion_roi"},
    "UNIPD/PSP": {"CT", "FLAIR"},
    "UKLFR/stroke_UKLFR": {"T1w", "T2w", "FLAIR", "lesion_roi"},
}

ALL_NATIVE_MODALITIES = ("T1w", "T2w", "FLAIR", "CT", "lesion_roi")

_MNI_MASK_GLOB = "sub-*/anat/*_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
_NATIVE_T1W_GLOB = "sub-*/anat/*_T1w.nii.gz"


def _subject_id_from_match(path: Path) -> str:
    return path.parent.parent.name  # sub-*/anat/<file> - subject folder is two levels up


@pytest.mark.parametrize("dataset_name", list(EXPECTED_AVAILABLE_MODALITIES))
def test_mni_mask_resolution_matches_raw_filesystem(dataset_name):
    """Ground truth: which valid subjects actually have a mask file on disk
    right now, found independently via a raw glob - not via file_patterns.json
    or Dataset at all. Compared against Dataset.resolve() for the same set of
    subjects; any difference is a real bug in the resolution logic, since both
    sides look at the filesystem at the same moment."""
    ds = Dataset(PROJECT_ROOT, dataset_name, FILE_PATTERNS)
    valid_subjects = set(ds.subjects())
    manual_masks_root = PROJECT_ROOT / dataset_name / "derivatives" / "manual_masks"
    ground_truth = {
        _subject_id_from_match(path) for path in manual_masks_root.glob(_MNI_MASK_GLOB)
    } & valid_subjects
    via_resolve = {sub for sub in valid_subjects if ds.resolve(sub, "mni", "lesion_mask") is not None}
    assert via_resolve == ground_truth


@pytest.mark.parametrize("dataset_name", ["UNIPD/WashU", "UKLFR/stroke_UKLFR"])
def test_native_t1w_resolution_matches_raw_filesystem(dataset_name):
    ds = Dataset(PROJECT_ROOT, dataset_name, FILE_PATTERNS)
    valid_subjects = set(ds.subjects())
    dataset_root = PROJECT_ROOT / dataset_name
    ground_truth = {
        _subject_id_from_match(path) for path in dataset_root.glob(_NATIVE_T1W_GLOB)
    } & valid_subjects
    via_resolve = {sub for sub in valid_subjects if ds.resolve(sub, "native", "T1w") is not None}
    assert via_resolve == ground_truth


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
