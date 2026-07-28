"""Unit tests for src/features/clinical.py."""

import pandas as pd
import pytest

from src.features.clinical import extract_target, load_participants


def _write_participants(tmp_path, rows):
    path = tmp_path / "participants.tsv"
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False)
    return path


def test_load_participants_renames_participant_id(tmp_path):
    path = _write_participants(
        tmp_path, [{"participant_id": "sub-STUNIPD0001", "age": "60"}]
    )
    participants = load_participants(path)
    assert "subject_id" in participants.columns
    assert "participant_id" not in participants.columns
    assert participants["subject_id"].tolist() == ["sub-STUNIPD0001"]


def test_load_participants_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_participants(tmp_path / "nope.tsv")


def test_load_participants_missing_participant_id_column_raises(tmp_path):
    path = _write_participants(tmp_path, [{"age": "60"}])
    with pytest.raises(ValueError, match="participant_id"):
        load_participants(path)


def test_extract_target_drops_missing_and_logs_count():
    participants = pd.DataFrame(
        {
            "subject_id": ["sub-0001", "sub-0002", "sub-0003"],
            "NIHSS": ["4", "n/a", "9"],
        }
    )
    extracted = extract_target(participants, "NIHSS")
    assert extracted["subject_id"].tolist() == ["sub-0001", "sub-0003"]
    assert extracted["NIHSS"].tolist() == [4.0, 9.0]


def test_extract_target_treats_empty_field_as_missing():
    participants = pd.DataFrame({"subject_id": ["sub-0001", "sub-0002"], "Clock": ["3", ""]})
    extracted = extract_target(participants, "Clock")
    assert extracted["subject_id"].tolist() == ["sub-0001"]


def test_extract_target_unknown_column_raises():
    participants = pd.DataFrame({"subject_id": ["sub-0001"], "NIHSS": ["4"]})
    with pytest.raises(ValueError, match="unknown behavioral target"):
        extract_target(participants, "not_a_column")


def test_extract_target_non_numeric_value_raises():
    participants = pd.DataFrame({"subject_id": ["sub-0001"], "NIHSS": ["not-a-number"]})
    with pytest.raises(ValueError, match="non-numeric"):
        extract_target(participants, "NIHSS")


def test_extract_target_all_missing_raises():
    participants = pd.DataFrame({"subject_id": ["sub-0001", "sub-0002"], "GDS_15": ["n/a", "n/a"]})
    with pytest.raises(ValueError, match="no usable"):
        extract_target(participants, "GDS_15")
