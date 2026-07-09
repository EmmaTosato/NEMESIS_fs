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
FILE_PATTERNS_PATH = Path("config/file_patterns.json")

pytestmark = pytest.mark.skipif(
    not PROJECT_ROOT.is_dir(), reason="EBRAIN mount not available on this machine"
)


def _two_subjects_with_mni_mask(dataset_name: str, file_patterns) -> list[str]:
    ds = Dataset(PROJECT_ROOT, dataset_name, file_patterns)
    with_mask = [s for s in ds.subjects(group="ST") if ds.resolve(s, "mni", "lesion_mask") is not None]
    return with_mask[:2]


def test_end_to_end_small_real_run(tmp_path, monkeypatch):
    monkeypatch.setattr(retrieve_data, "REPORTS_ROOT", tmp_path / "reports")
    file_patterns = load_file_patterns(FILE_PATTERNS_PATH)
    subjects = _two_subjects_with_mni_mask("UNIPD/PASPORT", file_patterns)
    assert len(subjects) == 2  # sanity: the fixture assumption holds on real data

    config = RetrievalConfig(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        project_root=PROJECT_ROOT,
        file_patterns_path=FILE_PATTERNS_PATH,
        file_patterns=file_patterns,
        datasets=["UNIPD/PASPORT"],
        group_filter=None,
        subjects=subjects,
        retrieve=[RetrieveItem(space="mni", modality="lesion_mask")],
        include_tabular_data=True,
        overwrite=False,
    )

    datasets = retrieve_data._build_datasets(config)
    retrieve_data._validate_upfront(datasets, config)
    stats = retrieve_data._retrieve_all(datasets, config)

    assert stats["UNIPD/PASPORT"].subjects_selected == 2
    assert stats["UNIPD/PASPORT"].copied == 2
    assert stats["UNIPD/PASPORT"].failed == 0
    assert stats["UNIPD/PASPORT"].participants_status == "copied"

    for subject_id in subjects:
        copied = (
            tmp_path
            / "data"
            / "clinical_connectome"
            / "UNIPD"
            / "PASPORT"
            / subject_id
            / "lesion"
            / "mni"
        )
        assert list(copied.glob("*_label-lesion_mask.nii.gz"))

    participants_copy = tmp_path / "data" / "clinical_connectome" / "UNIPD" / "PASPORT" / "participants.tsv"
    assert participants_copy.is_file()

    report_path = retrieve_data._write_report(config, stats)
    assert report_path.is_file()
    assert "UNIPD/PASPORT" in report_path.read_text()

    # Second run, overwrite=False: everything should be skipped, nothing re-copied.
    stats_second_run = retrieve_data._retrieve_all(datasets, config)
    assert stats_second_run["UNIPD/PASPORT"].copied == 0
    assert stats_second_run["UNIPD/PASPORT"].skipped_existing == 2
    assert stats_second_run["UNIPD/PASPORT"].participants_status == "skipped (exists)"
