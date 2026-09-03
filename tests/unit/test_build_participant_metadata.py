"""Unit tests for scripts/build_participant_metadata.py - synthetic fixtures, no EBRAIN mount needed."""

import pandas as pd
import pytest

from scripts import build_participant_metadata as bpm


def _write_summary(dir_, name, rows):
    dir_.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dir_ / f"data_summary__{name}.csv", index=False)


def _write_participants(root, center, dataset, rows):
    path = root / center / dataset / "participants.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False)
    return path


def _config(**overrides):
    defaults = dict(datasets_with_lesions=[], datasets_with_features=[])
    defaults.update(overrides)
    return bpm.BuildParticipantMetadataConfig(**defaults)


@pytest.fixture(autouse=True)
def _redirect_roots(tmp_path, monkeypatch):
    monkeypatch.setattr(bpm, "DATASET_SUMMARIES_DIR", tmp_path / "dataset_summaries")
    monkeypatch.setattr(bpm, "DERIVATIVES_ROOT", tmp_path / "derivatives")
    monkeypatch.setattr(bpm, "METADATA_OUT_ROOT", tmp_path / "metadata")


def test_to_subject_id_canonical_passthrough():
    assert bpm.to_subject_id("sub-STUNIPD0001") == "sub-STUNIPD0001"


def test_to_subject_id_raw_format_reconstructed():
    assert bpm.to_subject_id("ST_UCL-UK_0001") == "sub-STUCLUK0001"


def test_to_subject_id_unrecognized_format_raises():
    with pytest.raises(ValueError, match="participant_id"):
        bpm.to_subject_id("not-a-valid-id")


def test_lesions_export_only_for_configured_datasets(tmp_path):
    _write_summary(
        tmp_path / "dataset_summaries",
        "UNIPD_WashU",
        [
            {"subject": "sub-STUNIPD0001", bpm.LESION_COL: "present", bpm.FEATURE_COL: "missing"},
            {"subject": "sub-STUNIPD0002", bpm.LESION_COL: "missing", bpm.FEATURE_COL: "missing"},
        ],
    )
    _write_participants(
        tmp_path / "derivatives",
        "UNIPD",
        "WashU",
        [{"participant_id": "sub-STUNIPD0001", "age": "50"}, {"participant_id": "sub-STUNIPD0002", "age": "60"}],
    )
    config = _config(datasets_with_lesions=["UNIPD_WashU"])

    bpm.build_participant_metadata(config)

    out = tmp_path / "metadata" / "UNIPD_WashU_participants_lesions.tsv"
    df = pd.read_csv(out, sep="\t")
    assert list(df["participant_id"]) == ["sub-STUNIPD0001"]
    # not in datasets_with_features - no feature/join export even though FEATURE_COL exists
    assert not (tmp_path / "metadata" / "UNIPD_WashU_participants_features.tsv").exists()


def test_features_and_join_export_for_configured_dataset(tmp_path):
    _write_summary(
        tmp_path / "dataset_summaries",
        "UNIPD_WashU",
        [
            {"subject": "sub-STUNIPD0001", bpm.LESION_COL: "present", bpm.FEATURE_COL: "present"},
            {"subject": "sub-STUNIPD0002", bpm.LESION_COL: "present", bpm.FEATURE_COL: "missing"},
            {"subject": "sub-STUNIPDHC0001", bpm.LESION_COL: "missing", bpm.FEATURE_COL: "present"},
        ],
    )
    _write_participants(
        tmp_path / "derivatives",
        "UNIPD",
        "WashU",
        [{"participant_id": "sub-STUNIPD0001"}, {"participant_id": "sub-STUNIPD0002"}, {"participant_id": "sub-STUNIPDHC0001"}],
    )
    config = _config(datasets_with_lesions=["UNIPD_WashU"], datasets_with_features=["UNIPD_WashU"])

    bpm.build_participant_metadata(config)

    metadata_dir = tmp_path / "metadata"
    lesions = pd.read_csv(metadata_dir / "UNIPD_WashU_participants_lesions.tsv", sep="\t")
    features = pd.read_csv(metadata_dir / "UNIPD_WashU_participants_features.tsv", sep="\t")
    join = pd.read_csv(metadata_dir / "UNIPD_WashU_participants_join.tsv", sep="\t")
    assert sorted(lesions["participant_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    assert sorted(features["participant_id"]) == ["sub-STUNIPD0001", "sub-STUNIPDHC0001"]
    assert list(join["participant_id"]) == ["sub-STUNIPD0001"]


def test_non_canonical_participant_id_promoted_and_original_preserved(tmp_path):
    """UCL-UK's raw participant_id ("ST_UCL-UK_0001") isn't canonical - the canonical
    subject id must be promoted to participant_id, with the raw value kept as
    original_id (see docs/dev/metadata.md, layer 2)."""
    _write_summary(
        tmp_path / "dataset_summaries",
        "UCL-UK_UCLStrokeData",
        [{"subject": "sub-STUCLUK0001", bpm.LESION_COL: "present"}],
    )
    _write_participants(
        tmp_path / "derivatives",
        "UCL-UK",
        "UCLStrokeData",
        [{"participant_id": "ST_UCL-UK_0001", "age": "70"}],
    )
    config = _config(datasets_with_lesions=["UCL-UK_UCLStrokeData"])

    bpm.build_participant_metadata(config)

    df = pd.read_csv(tmp_path / "metadata" / "UCL-UK_UCLStrokeData_participants_lesions.tsv", sep="\t")
    assert df.loc[0, "participant_id"] == "sub-STUCLUK0001"
    assert df.loc[0, "original_id"] == "ST_UCL-UK_0001"


def test_missing_participants_tsv_is_skipped_not_an_error(tmp_path):
    """A dataset with no local participants.tsv is a legitimate per-dataset gap
    (code_standards.md §0/§3) - the run continues, nothing is written for it."""
    _write_summary(
        tmp_path / "dataset_summaries",
        "UNIPD_PSP",
        [{"subject": "sub-STUNIPD0001", bpm.LESION_COL: "present"}],
    )
    config = _config(datasets_with_lesions=["UNIPD_PSP"])

    bpm.build_participant_metadata(config)  # must not raise

    assert not (tmp_path / "metadata" / "UNIPD_PSP_participants_lesions.tsv").exists()


def test_load_config_missing_key_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"datasets_with_lesions": []}')
    with pytest.raises(ValueError, match="datasets_with_features"):
        bpm.load_config(str(path))


def test_load_config_wrong_value_type_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"datasets_with_lesions": "not-a-list", "datasets_with_features": []}')
    with pytest.raises(ValueError, match="datasets_with_lesions"):
        bpm.load_config(str(path))
