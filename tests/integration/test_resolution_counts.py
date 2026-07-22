"""Integration tests against the real EBRAIN-mounted Clinical_connectome data.

Skipped entirely if the mount is not reachable on this machine. Ground truth
is never a hardcoded number - the datasets are actively curated (subjects and
files are added on EBRAIN over time), so a frozen count would fail the moment
the data legitimately changes, not when the code breaks. Instead, every check
here recomputes its own expectation directly from the real filesystem at test
run time (independent of Dataset/file_patterns.json) and compares it against
what Dataset.resolve() reports - a mismatch then always signals a real
discrepancy in the resolution logic, never a stale number. Uses the real
config/registry/file_patterns_server.json registry, not a synthetic one, since
the whole point here is verifying the production mapping against real data.

FC-pearson's ground-truth globs are derived from whatever templates are
currently registered (see _fc_pearson_globs) rather than hardcoding a couple
of atlas names - the registered set has changed size before (2 -> 15 atlases)
and will likely change again, and a hardcoded subset would silently stop
covering newly-added/removed templates without either test failing.

Scoped to `manual_masks` (lesion) and `FC-pearson` (feature, WashU only) -
native/raw retrieval is descoped this round, see
docs/dev/retrieval.md "This round vs. a future native/raw round".
"""

from pathlib import Path

import pytest

from src.retrieval.config import RetrieveItem, load_file_patterns
from src.retrieval.dataset import Dataset

PROJECT_ROOT = Path("/data/corbetta/Clinical_connectome")
FILE_PATTERNS_PATH = Path("config/registry/file_patterns_server.json")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)

FILE_PATTERNS = load_file_patterns(FILE_PATTERNS_PATH) if FILE_PATTERNS_PATH.is_file() else None

ALL_DATASETS = ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"]

_LESION_MASK_GLOB = "sub-*/anat/*_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"


def _fc_pearson_globs() -> list[str]:
    """One glob per template currently registered for feature/func/FC-pearson
    - whatever that set is today (see module docstring), not a fixed list."""
    templates = FILE_PATTERNS.templates_for("feature", "func", "FC-pearson")
    return [template.replace("{subject_id}", "sub-*") for template in templates]


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
        for glob in _fc_pearson_globs()
        for path in features_root.glob(glob)
    } & valid_subjects
    item = RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson")
    via_resolve = {sub for sub in valid_subjects if ds.resolve(sub, item)}
    assert via_resolve == ground_truth


def test_subject_with_every_fc_pearson_atlas_gets_every_file():
    """Regression for a specific nuance: unlike lesion_roi's historical
    naming-variant case, the registered FC-pearson templates are not
    alternate names for the same file - they are genuinely different,
    simultaneously-present atlas files. A subject with every registered
    atlas on disk must resolve to exactly that many paths, one per template
    (see FilePatterns docstring: "grab every one of these that exists"), not
    just one."""
    features_root = PROJECT_ROOT / "features" / "UNIPD" / "WashU"
    globs = _fc_pearson_globs()
    per_atlas_subjects = [
        {_subject_id_from_match(p) for p in features_root.glob(glob)} for glob in globs
    ]
    subjects_with_all = set.intersection(*per_atlas_subjects)
    assert subjects_with_all  # sanity: the fixture assumption holds on real data

    ds = Dataset("UNIPD/WashU", FILE_PATTERNS)
    item = RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson")
    subject_id = sorted(subjects_with_all)[0]
    resolved = ds.resolve(subject_id, item)
    assert len(resolved) == len(globs)
