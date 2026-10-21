"""`src/pipeline/calibrate_lesion_side_threshold.py`: rami di errore di `main` e dei due loader, contenuto del report."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from src.pipeline import calibrate_lesion_side_threshold as cal

DATASET = "UNIPD/WashU"
IDS = [f"sub-STUNIPD{i:04d}" for i in range(1, 7)]
SIDES = ["left", "right", "left", "right", "both", "left"]
LI = [0.9, -0.8, 0.7, -0.6, 0.0, 0.5]  # allineati alle etichette: soglia 0.2 -> 6/6


def _write(tmp_path, participants=None, measured=None):
    p, m = tmp_path / "participants.csv", tmp_path / "lesion_metadata.csv"
    pd.DataFrame(
        participants
        or {
            "subject_id": IDS, "dataset": DATASET, "lesion_side": SIDES, "lesion_side_source": "clinical",
        }
    ).to_csv(p, index=False)
    pd.DataFrame(
        measured or {"subject_id": IDS, "dataset": DATASET, "laterality_index_2mm": LI}
    ).to_csv(m, index=False)
    return p, m


@pytest.fixture
def paths(tmp_path, monkeypatch):
    monkeypatch.setattr(cal, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(cal, "LOGS_ROOT", tmp_path / "logs")
    return _write(tmp_path)


def _main(paths, grid="2mm", datasets=(DATASET,)):
    p, m = paths
    return cal.main(["--grid", grid, "--datasets", *datasets, "--participants-path", str(p), "--lesion-metadata-path", str(m)])


# --- loader -----------------------------------------------------------------------------------


@pytest.mark.parametrize("missing", ["subject_id", "dataset", "lesion_side", "lesion_side_source"])
def test_load_ground_truth_names_the_missing_column(tmp_path, missing):
    p, _ = _write(tmp_path)
    frame = pd.read_csv(p).drop(columns=[missing])
    frame.to_csv(p, index=False)
    with pytest.raises(ValueError, match=f"missing required column '{missing}'"):
        cal.load_ground_truth(p, [DATASET])


def test_load_ground_truth_rejects_an_unknown_side_value(tmp_path):
    p, _ = _write(tmp_path, participants={
        "subject_id": IDS[:2], "dataset": DATASET, "lesion_side": ["left", "sinistra"], "lesion_side_source": "clinical",
    })
    with pytest.raises(ValueError, match=r"unexpected lesion_side value\(s\) \['sinistra'\]"):
        cal.load_ground_truth(p, [DATASET])


def test_load_ground_truth_dataset_without_clinical_labels_raises(tmp_path):
    p, _ = _write(tmp_path)
    with pytest.raises(ValueError, match=r"no clinically-sourced lesion_side found for dataset\(s\) \['UKLFR/x'\]"):
        cal.load_ground_truth(p, [DATASET, "UKLFR/x"])


def test_load_ground_truth_excludes_other_datasets_and_geometric_labels(tmp_path):
    p, _ = _write(tmp_path, participants={
        "subject_id": IDS[:4], "dataset": [DATASET, DATASET, "Other", DATASET],
        "lesion_side": ["left", "right", "left", "both"],
        "lesion_side_source": ["clinical", "geometric", "clinical", "clinical"],
    })
    truth = cal.load_ground_truth(p, [DATASET])
    assert list(truth["subject_id"]) == [IDS[0], IDS[3]]
    assert list(truth.columns) == ["subject_id", "dataset", "lesion_side"]


def test_load_laterality_index_missing_file_names_the_producing_pipeline(tmp_path):
    with pytest.raises(FileNotFoundError, match="compute_lesion_metadata"):
        cal.load_laterality_index(tmp_path / "absent.csv", "2mm")


def test_load_laterality_index_renames_the_grid_column(tmp_path):
    _, m = _write(tmp_path)
    frame = cal.load_laterality_index(m, "2mm")
    assert list(frame.columns) == ["subject_id", "dataset", "laterality_index"]
    assert frame["laterality_index"].tolist() == LI


def test_load_laterality_index_with_no_grid_column_says_none_available(tmp_path):
    _, m = _write(tmp_path, measured={"subject_id": IDS, "dataset": DATASET, "other": 1})
    with pytest.raises(ValueError, match="available grid"):
        cal.load_laterality_index(m, "2mm")


# --- main: errori -----------------------------------------------------------------------------


def test_main_missing_participants_returns_1(paths, caplog):
    paths[0].unlink()
    with caplog.at_level(logging.ERROR):
        assert _main(paths) == 1
    assert "participants.csv" in caplog.text or "No such file" in caplog.text
    assert not (paths[0].parent / "summaries").exists()


def test_main_unknown_grid_returns_1_naming_available(paths, caplog):
    with caplog.at_level(logging.ERROR):
        assert _main(paths, grid="1mm") == 1
    assert "'laterality_index_1mm'" in caplog.text and "['2mm']" in caplog.text


def test_main_dataset_without_labels_returns_1(paths, caplog):
    with caplog.at_level(logging.ERROR):
        assert _main(paths, datasets=("Nowhere",)) == 1
    assert "no clinically-sourced lesion_side" in caplog.text


def test_main_log_directory_not_creatable_returns_1(paths, tmp_path, monkeypatch, caplog):
    blocker = tmp_path / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(cal, "LOGS_ROOT", blocker / "logs")
    with caplog.at_level(logging.ERROR):
        assert _main(paths) == 1
    assert "cannot set up log file" in caplog.text
    assert not (tmp_path / "summaries").exists()


def test_main_stale_lesion_metadata_returns_1_listing_the_unmatched_subjects(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(cal, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(cal, "LOGS_ROOT", tmp_path / "logs")
    paths = _write(tmp_path, measured={"subject_id": IDS[:4], "dataset": DATASET, "laterality_index_2mm": LI[:4]})
    with caplog.at_level(logging.ERROR):
        assert _main(paths) == 1
    assert "2 clinically-labelled subject(s) have no row" in caplog.text
    assert IDS[4] in caplog.text and "stale" in caplog.text
    assert not (tmp_path / "summaries").exists()


def test_main_report_write_failure_returns_1(paths, tmp_path, monkeypatch, caplog):
    blocker = tmp_path / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(cal, "REPORTS_ROOT", blocker / "reports")
    with caplog.at_level(logging.ERROR):
        assert _main(paths) == 1
    assert "cannot write report" in caplog.text


# --- main: contenuto ----------------------------------------------------------------------------


def test_undefined_laterality_index_is_warned_named_and_excluded(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(cal, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(cal, "LOGS_ROOT", tmp_path / "logs")
    li = list(LI)
    li[5] = np.nan
    paths = _write(tmp_path, measured={"subject_id": IDS, "dataset": DATASET, "laterality_index_2mm": li})
    with caplog.at_level(logging.WARNING):
        assert _main(paths) == 0
    assert "1 subject(s) have an undefined laterality_index" in caplog.text and IDS[5] in caplog.text
    (report,) = list((tmp_path / "summaries").glob("*.md"))
    text = report.read_text()
    assert "usable clinical label + computable laterality_index: 5" in text
    assert IDS[5] not in text


def test_report_marks_literature_default_and_has_both_confusion_matrices(paths, tmp_path):
    assert _main(paths) == 0
    (report,) = list((tmp_path / "summaries").glob("*.md"))
    text = report.read_text()
    assert "*(literature default)*" in text or "*(best)*" in text
    assert "## Confusion matrix — Literature default (|LI| < 0.2), threshold=0.20" in text
    assert "## Confusion matrix — Best on this data" in text
    # Con questi dati la soglia 0.2 riproduce tutte le etichette: 6/6
    assert "| 0.20" in text and "6/6" in text
    assert text.count("\n| 0.") == len(cal.THRESHOLD_GRID)  # una riga per soglia della griglia


def test_threshold_grid_contains_the_literature_default_exactly_once():
    assert (np.isclose(cal.THRESHOLD_GRID, cal.LITERATURE_DEFAULT_THRESHOLD)).sum() == 1


def test_best_threshold_logged_is_the_one_with_maximum_accuracy(paths, caplog):
    with caplog.at_level(logging.INFO):
        assert _main(paths) == 0
    assert "6 subject(s) calibrated on" in caplog.text and "accuracy=1.000" in caplog.text
    assert "run duration" in caplog.text


def test_duplicate_subject_in_lesion_metadata_is_rejected(tmp_path, monkeypatch, caplog):
    """Pattern #5/#2: una riga duplicata gonfia n_total e l'accuratezza senza alcun errore."""
    monkeypatch.setattr(cal, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(cal, "LOGS_ROOT", tmp_path / "logs")
    paths = _write(
        tmp_path,
        measured={"subject_id": [*IDS, IDS[0]], "dataset": DATASET, "laterality_index_2mm": [*LI, LI[0]]},
    )
    assert _main(paths) == 1


def test_all_laterality_indices_undefined_is_an_error_not_a_nan_report(tmp_path, monkeypatch):
    monkeypatch.setattr(cal, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(cal, "LOGS_ROOT", tmp_path / "logs")
    paths = _write(tmp_path, measured={"subject_id": IDS, "dataset": DATASET, "laterality_index_2mm": [np.nan] * 6})
    assert _main(paths) == 1
