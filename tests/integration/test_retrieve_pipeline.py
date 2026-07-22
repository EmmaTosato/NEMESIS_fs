"""Integration test: full retrieval run against real EBRAIN data, small scope.

Skipped entirely if the mount is not reachable on this machine. Copies only a
couple of real subjects (via explicit `subjects`) into a tmp_path output_root -
never touches the repo's own data/ or reports/ folders.
"""

from pathlib import Path

import pytest

from src.pipeline import retrieve_data
from src.retrieval.config import RetrievalConfig, RetrieveItem, load_file_patterns
from src.retrieval.dataset import Dataset

PROJECT_ROOT = Path("/data/corbetta/Clinical_connectome")
FILE_PATTERNS_PATH = Path("config/registry/file_patterns_server.json")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)


def _two_subjects_with_lesion_mask(dataset_name: str, file_patterns) -> list[str]:
    ds = Dataset(dataset_name, file_patterns)
    item = RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")
    with_mask = [s for s in ds.subjects("lesion", "manual_masks", group="ST") if ds.resolve(s, item)]
    return with_mask[:2]


def test_end_to_end_small_real_run(tmp_path, monkeypatch):
    """PASPORT: has manual_masks everywhere but no features/ tree at all - the
    feature/FC-pearson item must WARNING-skip for this dataset (see
    src.pipeline.retrieve_data._report_skipped_retrieve_items), not stop the
    run, while lesion/manual_masks still copies normally."""
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    file_patterns = load_file_patterns(FILE_PATTERNS_PATH)
    subjects = _two_subjects_with_lesion_mask("UNIPD/PASPORT", file_patterns)
    assert len(subjects) == 2  # sanity: the fixture assumption holds on real data

    config = RetrievalConfig(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=FILE_PATTERNS_PATH,
        file_patterns=file_patterns,
        datasets=["UNIPD/PASPORT"],
        group_filter=None,
        subjects=subjects,
        retrieve=[
            RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask"),
            RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson"),
        ],
        include_tabular_data=True,
        overwrite=False,
    )

    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)  # must not raise despite feature being absent here
    stats = retrieve_data._retrieve_all(datasets, config)

    assert stats["UNIPD/PASPORT"].subjects_selected == 2
    assert stats["UNIPD/PASPORT"].skipped_objects == [
        "UNIPD/PASPORT: object='feature' not present in this dataset - skipping feature/func/FC-pearson"
    ]
    # 2 subjects' lesion_mask - participants.tsv is tracked separately (see
    # DatasetStats.participants_outcome), not folded into this count.
    assert stats["UNIPD/PASPORT"].copied == 2
    assert stats["UNIPD/PASPORT"].participants_outcome == "copied"
    assert stats["UNIPD/PASPORT"].failed == []

    for subject_id in subjects:
        copied = (
            tmp_path
            / "data"
            / "clinical_connectome"
            / "derivatives"
            / "UNIPD"
            / "PASPORT"
            / "manual_masks"
            / subject_id
            / "anat"
        )
        assert list(copied.glob("*_label-lesion_mask.nii.gz"))

    participants_copy = (
        tmp_path / "data" / "clinical_connectome" / "derivatives" / "UNIPD" / "PASPORT" / "participants.tsv"
    )
    assert participants_copy.is_file()

    report_path = retrieve_data._write_report(config, stats)
    assert report_path.is_file()
    assert "UNIPD/PASPORT" in report_path.read_text()

    # Second run, overwrite=False: everything should be skipped, nothing re-copied.
    stats_second_run = retrieve_data._retrieve_all(datasets, config)
    assert stats_second_run["UNIPD/PASPORT"].copied == 0
    # 2 subjects' lesion_mask already present; participants.tsv likewise (tracked separately).
    assert stats_second_run["UNIPD/PASPORT"].skipped_existing == 2
    assert stats_second_run["UNIPD/PASPORT"].participants_outcome == "skipped (exists)"
