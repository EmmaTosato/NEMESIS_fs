"""Integration tests against the real EBRAIN-mounted Clinical_connectome data.

Skipped entirely if the mount is not reachable on this machine. Ground truth
is never a hardcoded number - the datasets are actively curated (subjects and
files are added on EBRAIN over time), so a frozen count would fail the moment
the data legitimately changes, not when the code breaks. Instead, every check
here recomputes its own expectation directly from the real filesystem at test
run time (independent of Dataset/file_patterns.json) and compares it against
what Dataset.resolve() reports - a mismatch then always signals a real
discrepancy in the resolution logic, never a stale number. Uses the real
config/registry/file_patterns.json registry, not a synthetic one, since the whole
point here is verifying the production mapping against real data.

Scoped to `manual_masks` (lesion) and `FC-pearson` (feature, WashU only) -
native/raw retrieval is descoped this round, see
docs/dev/retrieval.md "This round vs. a future native/raw round".
"""

from pathlib import Path

import pytest

from src.retrieval.config import RetrieveItem, load_file_patterns
from src.retrieval.dataset import Dataset

PROJECT_ROOT = Path("/data/corbetta/Clinical_connectome")
FILE_PATTERNS_PATH = Path("config/registry/file_patterns.json")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)

FILE_PATTERNS = load_file_patterns(FILE_PATTERNS_PATH) if FILE_PATTERNS_PATH.is_file() else None

ALL_DATASETS = ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"]

_LESION_MASK_GLOB = "sub-*/anat/*_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
_FC_PEARSON_S1_GLOB = "sub-*/func/*_FC-pearson_atlas-Schaefer200TianS1Buckner7N.csv"
_FC_PEARSON_S2_GLOB = "sub-*/func/*_FC-pearson_atlas-Schaefer200TianS2Buckner7N.csv"


def _subject_id_from_match(path: Path) -> str:
    return path.parent.parent.name  # sub-*/<anat|func>/<file> - subject folder is two levels up


@pytest.mark.parametrize("dataset_name", ALL_DATASETS)
def test_manual_masks_lesion_mask_resolution_matches_raw_filesystem(dataset_name):
    """Ground truth: which valid subjects actually have a mask file on disk
    right now, found independently via a raw glob - not via file_patterns.json
    or Dataset at all. Compared against Dataset.resolve() for the same set of
    subjects; any difference is a real bug in the resolution logic, since both
    sides look at the filesystem at the same moment."""
    ds = Dataset(dataset_name, FILE_PATTERNS)
    valid_subjects = set(ds.subjects("lesion", "manual_masks"))
    manual_masks_root = PROJECT_ROOT / dataset_name / "derivatives" / "manual_masks"
    ground_truth = {
        _subject_id_from_match(path) for path in manual_masks_root.glob(_LESION_MASK_GLOB)
    } & valid_subjects
    item = RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")
    via_resolve = {sub for sub in valid_subjects if ds.resolve(sub, item)}
    assert via_resolve == ground_truth


def test_feature_fc_pearson_resolution_matches_raw_filesystem():
    """WashU only - the only one of the 4 datasets with a features/ tree at
    all (see Dataset.has_object)."""
    ds = Dataset("UNIPD/WashU", FILE_PATTERNS)
    valid_subjects = set(ds.subjects("feature", None))
    features_root = PROJECT_ROOT / "features" / "UNIPD" / "WashU"
    ground_truth = {
        _subject_id_from_match(path)
        for glob in (_FC_PEARSON_S1_GLOB, _FC_PEARSON_S2_GLOB)
        for path in features_root.glob(glob)
    } & valid_subjects
    item = RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson")
    via_resolve = {sub for sub in valid_subjects if ds.resolve(sub, item)}
    assert via_resolve == ground_truth


def test_subjects_with_both_fc_pearson_atlases_get_both_files():
    """Regression for a specific nuance: unlike lesion_roi's historical
    naming-variant case, the two registered FC-pearson templates
    (Schaefer200TianS1/S2Buckner7N) are not alternate names for the same
    file - they are two genuinely different, simultaneously-present atlas
    files. A subject with both on disk must resolve to exactly 2 paths, not
    1 (see FilePatterns docstring: "grab every one of these that exists")."""
    features_root = PROJECT_ROOT / "features" / "UNIPD" / "WashU"
    s1_subjects = {_subject_id_from_match(p) for p in features_root.glob(_FC_PEARSON_S1_GLOB)}
    s2_subjects = {_subject_id_from_match(p) for p in features_root.glob(_FC_PEARSON_S2_GLOB)}
    both = s1_subjects & s2_subjects
    assert both  # sanity: the fixture assumption holds on real data

    ds = Dataset("UNIPD/WashU", FILE_PATTERNS)
    item = RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson")
    subject_id = sorted(both)[0]
    resolved = ds.resolve(subject_id, item)
    assert len(resolved) == 2
