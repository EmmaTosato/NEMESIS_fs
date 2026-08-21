"""Unit tests for src/features/clinical.py."""

import logging

import pandas as pd
import pytest

from src.features import clinical
from src.features.clinical import (
    check_participant_variable_coverage,
    extract_target,
    join_lesion_side,
    join_nihss,
    join_participant_variables,
    load_participants,
)


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


def _write_dataset_participants(metadata_root, dataset, rows):
    path = metadata_root / f"{dataset.replace('/', '_')}_participants_lesions.tsv"
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False)
    return path


def test_join_lesion_side_merges_present_column(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [{"participant_id": "sub-1", "lesion_side": "left"}, {"participant_id": "sub-2", "lesion_side": "right"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    side = join_lesion_side(metadata)

    assert side.tolist() == ["left", "right"]


def test_join_lesion_side_per_row_missing_value_becomes_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [{"participant_id": "sub-1", "lesion_side": "left"}, {"participant_id": "sub-2", "lesion_side": "n/a"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    side = join_lesion_side(metadata)

    assert side.tolist() == ["left", "unknown"]


def test_join_lesion_side_dataset_wide_missing_column_becomes_unknown_and_warns(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/PASPORT",
        [{"participant_id": "sub-1", "lesion_volume_ml": "12.3"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/PASPORT"]})

    with caplog.at_level(logging.WARNING):
        side = join_lesion_side(metadata)

    assert side.tolist() == ["unknown"]
    assert "no lesion_side column" in caplog.text


def test_join_lesion_side_unresolvable_dataset_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/NotARealDataset"]})

    with pytest.raises(FileNotFoundError):
        join_lesion_side(metadata)


def test_join_lesion_side_subject_missing_from_participants_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(tmp_path, "UNIPD/WashU", [{"participant_id": "sub-1", "lesion_side": "left"}])
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    with pytest.raises(ValueError, match="sub-2"):
        join_lesion_side(metadata)


def test_join_lesion_side_raises_on_missing_required_columns():
    with pytest.raises(ValueError, match="subject_id"):
        join_lesion_side(pd.DataFrame({"dataset": ["UNIPD/WashU"]}))


def test_join_nihss_merges_present_column(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [{"participant_id": "sub-1", "NIHSS": "4"}, {"participant_id": "sub-2", "NIHSS": "12"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    nihss = join_nihss(metadata)

    assert nihss.tolist() == [4.0, 12.0]


def test_join_nihss_per_row_missing_value_becomes_nan(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [{"participant_id": "sub-1", "NIHSS": "4"}, {"participant_id": "sub-2", "NIHSS": "n/a"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    nihss = join_nihss(metadata)

    assert nihss.tolist()[0] == 4.0
    assert pd.isna(nihss.tolist()[1])


def test_join_nihss_dataset_wide_missing_column_becomes_nan_and_warns(tmp_path, monkeypatch, caplog):
    # Mirrors the real PASPORT gap: no plain "NIHSS" column, only per-timepoint variants.
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/PASPORT",
        [{"participant_id": "sub-1", "NIHSS_at_presentation": "6"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/PASPORT"]})

    with caplog.at_level(logging.WARNING):
        nihss = join_nihss(metadata)

    assert pd.isna(nihss.tolist()[0])
    assert "no NIHSS column" in caplog.text


def test_join_nihss_unresolvable_dataset_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/NotARealDataset"]})

    with pytest.raises(FileNotFoundError):
        join_nihss(metadata)


def test_join_nihss_subject_missing_from_participants_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(tmp_path, "UNIPD/WashU", [{"participant_id": "sub-1", "NIHSS": "4"}])
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    with pytest.raises(ValueError, match="sub-2"):
        join_nihss(metadata)


def test_join_nihss_non_numeric_value_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(tmp_path, "UNIPD/WashU", [{"participant_id": "sub-1", "NIHSS": "not-a-number"}])
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/WashU"]})

    with pytest.raises(ValueError, match="non-numeric"):
        join_nihss(metadata)


def test_join_nihss_raises_on_missing_required_columns():
    with pytest.raises(ValueError, match="subject_id"):
        join_nihss(pd.DataFrame({"dataset": ["UNIPD/WashU"]}))


def test_check_participant_variable_coverage_reports_everything_at_once(tmp_path, monkeypatch):
    """The report must surface every problem in one pass (missing dataset file, missing
    subject, missing variable) rather than stopping at the first - that's the whole point of
    a pre-flight report a human reads before anything is written."""
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [{"participant_id": "sub-1", "age": "70", "sex": "F"}],
    )
    metadata = pd.DataFrame(
        {
            "subject_id": ["sub-1", "sub-2", "sub-3"],
            "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UNIPD/PASPORT"],  # PASPORT has no tsv here
        }
    )

    report = check_participant_variable_coverage(metadata, ["age", "sex", "education"])

    assert report.datasets == ["UNIPD/PASPORT", "UNIPD/WashU"]
    assert report.missing_dataset_files == {"UNIPD/PASPORT": tmp_path / "UNIPD_PASPORT_participants_lesions.tsv"}
    assert report.missing_subjects_by_dataset == {"UNIPD/WashU": ["sub-2"]}
    assert report.missing_variable_by_dataset == {"UNIPD/WashU": ["education"]}
    assert report.n_subjects_by_dataset == {"UNIPD/WashU": 2, "UNIPD/PASPORT": 1}
    assert report.has_hard_failures is True


def test_check_participant_variable_coverage_clean_case_has_no_hard_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [{"participant_id": "sub-1", "age": "70"}, {"participant_id": "sub-2", "age": "65"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    report = check_participant_variable_coverage(metadata, ["age"])

    assert report.missing_dataset_files == {}
    assert report.missing_subjects_by_dataset == {}
    assert report.missing_variable_by_dataset == {}
    assert report.has_hard_failures is False


def test_join_participant_variables_joins_multiple_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [
            {"participant_id": "sub-1", "age": "70", "sex": "F", "education": "12"},
            {"participant_id": "sub-2", "age": "65", "sex": "M", "education": "16"},
        ],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    joined = join_participant_variables(metadata, ["age", "sex", "education"])

    assert joined["age"].tolist() == ["70", "65"]
    assert joined["sex"].tolist() == ["F", "M"]
    assert joined["education"].tolist() == ["12", "16"]
    # original metadata untouched
    assert list(metadata.columns) == ["subject_id", "dataset"]


def test_join_participant_variables_per_row_missing_value_becomes_nan(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(
        tmp_path, "UNIPD/WashU",
        [{"participant_id": "sub-1", "age": "70"}, {"participant_id": "sub-2", "age": "n/a"}],
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    joined = join_participant_variables(metadata, ["age"])

    assert joined["age"].tolist()[0] == "70"
    assert pd.isna(joined["age"].tolist()[1])


def test_join_participant_variables_dataset_wide_missing_column_becomes_nan_and_warns(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(tmp_path, "UNIPD/PASPORT", [{"participant_id": "sub-1", "age": "70"}])
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/PASPORT"]})

    with caplog.at_level(logging.WARNING):
        joined = join_participant_variables(metadata, ["age", "lesion_side"])

    assert joined["age"].tolist() == ["70"]
    assert pd.isna(joined["lesion_side"].tolist()[0])
    assert "no 'lesion_side' column" in caplog.text


def test_join_participant_variables_unresolvable_dataset_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    metadata = pd.DataFrame({"subject_id": ["sub-1"], "dataset": ["UNIPD/NotARealDataset"]})

    with pytest.raises(FileNotFoundError):
        join_participant_variables(metadata, ["age"])


def test_join_participant_variables_subject_missing_from_participants_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    _write_dataset_participants(tmp_path, "UNIPD/WashU", [{"participant_id": "sub-1", "age": "70"}])
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    with pytest.raises(ValueError, match="sub-2"):
        join_participant_variables(metadata, ["age"])
