"""Unit tests for src/pipeline/calibrate_lesion_side_threshold.py - the script that compares the
geometric lesion_side against the clinical labels in participants.csv.

Regression: the script imported KNOWN_LESION_SIDES from src.features.lesion after a refactor had
deleted it, so it failed at import time - and nothing noticed, because no test ever imported it.
"""

import pandas as pd
import pytest

from src.features.lesion import KNOWN_LESION_SIDES, lesion_side_from_laterality_index
from src.pipeline.calibrate_lesion_side_threshold import (
    evaluate_threshold,
    load_ground_truth,
    load_laterality_index,
    main,
)


def test_known_lesion_sides_covers_everything_the_classifier_returns():
    returned = {lesion_side_from_laterality_index(li, 0.2) for li in (-1.0, -0.5, 0.0, 0.1, 0.5, 1.0)}

    assert returned == set(KNOWN_LESION_SIDES)


def test_evaluate_threshold_counts_a_full_inversion_as_wrong_at_every_threshold():
    merged = pd.DataFrame(
        {"lesion_side": ["left", "right", "left"], "laterality_index": [0.9, -0.8, -1.0]}
    )

    result = evaluate_threshold(merged, 0.2)

    assert (result.n_correct, result.n_total) == (2, 3)
    assert result.confusion.loc["left", "right"] == 1


def _write_inputs(tmp_path):
    participants = tmp_path / "participants.csv"
    pd.DataFrame(
        {
            "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
            "dataset": ["UNIPD/WashU"] * 3,
            "lesion_side": ["left", "right", "left"],
            "lesion_side_source": ["clinical", "clinical", "geometric"],
        }
    ).to_csv(participants, index=False)
    measured = tmp_path / "lesion_metadata.csv"
    pd.DataFrame(
        {
            "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"],
            "dataset": ["UNIPD/WashU"] * 3,
            "laterality_index_2mm": [0.8, -0.7, 0.9],
        }
    ).to_csv(measured, index=False)
    return participants, measured


def test_load_ground_truth_keeps_only_clinically_sourced_labels(tmp_path):
    participants, _ = _write_inputs(tmp_path)

    truth = load_ground_truth(participants, ["UNIPD/WashU"])

    assert list(truth["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_load_laterality_index_unknown_grid_names_the_available_ones(tmp_path):
    _, measured = _write_inputs(tmp_path)

    with pytest.raises(ValueError, match="2mm"):
        load_laterality_index(measured, "3mm")


def test_main_end_to_end_writes_a_report(tmp_path, monkeypatch):
    participants, measured = _write_inputs(tmp_path)
    monkeypatch.chdir(tmp_path)

    rc = main([
        "--grid", "2mm", "--datasets", "UNIPD/WashU",
        "--participants-path", str(participants), "--lesion-metadata-path", str(measured),
    ])

    assert rc == 0
    reports = list((tmp_path / "summaries/calibrate_lesion_side_threshold").glob("*.md"))
    assert len(reports) == 1
    assert "grid: 2mm" in reports[0].read_text()
