"""Unit tests for scripts/populate_metadata.py - synthetic fixtures, no EBRAIN mount needed."""

import json

import pandas as pd
import pytest

from scripts import populate_metadata as pm

_DATASET = "UNIPD/WashU"


def _write_tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False)


def _make_subject_dirs(derivatives_dir, data_type, subject_ids):
    for subject_id in subject_ids:
        (derivatives_dir / data_type / subject_id).mkdir(parents=True)


def _source(tmp_path):
    return pm.DatasetSource(
        participants_tsv=tmp_path / "metadata_tsv" / "participants_WashU.tsv",
        derivatives_dir=tmp_path / "derivatives" / "UNIPD" / "WashU",
    )


def _config(tmp_path, **overrides):
    defaults = dict(
        project="clinical_connectome",
        sources={_DATASET: _source(tmp_path)},
        datasets=[_DATASET],
        group_filter=["ST"],
        output_path=tmp_path / "participants.csv",
        overwrite=False,
        run_notes="test",
    )
    defaults.update(overrides)
    return pm.PopulateMetadataConfig(**defaults)


# --- to_subject_id --------------------------------------------------------------------------


def test_to_subject_id_canonical_passthrough():
    assert pm.to_subject_id("sub-STUNIPD0001") == "sub-STUNIPD0001"


def test_to_subject_id_rebuilds_ucl_legacy_form():
    assert pm.to_subject_id("ST_UCL-UK_0001") == "sub-STUCLUK0001"


def test_to_subject_id_raises_on_unrecognized_shape():
    with pytest.raises(ValueError, match="participant_id"):
        pm.to_subject_id("not-an-id")


# --- discovery ------------------------------------------------------------------------------


def test_discover_subjects_on_disk_reports_empty_set_for_absent_data_type(tmp_path):
    derivatives_dir = tmp_path / "derivatives" / "UNIPD" / "WashU"
    _make_subject_dirs(derivatives_dir, "manual_masks", ["sub-STUNIPD0001"])

    found = pm.discover_subjects_on_disk(derivatives_dir)

    assert found["manual_masks"] == {"sub-STUNIPD0001"}
    assert found["sdc"] == set()  # dataset simply doesn't have this tree - not an error
    assert found["features"] == set()


def test_discover_subjects_on_disk_ignores_non_subject_files(tmp_path):
    """README_ARCHIVE.md is a real, expected file in pruned local copies - it must not be
    mistaken for a subject nor make discovery fail."""
    derivatives_dir = tmp_path / "derivatives" / "UNIPD" / "WashU"
    _make_subject_dirs(derivatives_dir, "features", ["sub-STUNIPD0002"])
    (derivatives_dir / "features" / "README_ARCHIVE.md").write_text("pruned")

    assert pm.discover_subjects_on_disk(derivatives_dir)["features"] == {"sub-STUNIPD0002"}


def test_load_participants_tsv_raises_on_duplicate_subject(tmp_path):
    path = tmp_path / "participants.tsv"
    _write_tsv(path, [{"participant_id": "sub-STUNIPD0001"}, {"participant_id": "sub-STUNIPD0001"}])

    with pytest.raises(ValueError, match="duplicate subject id"):
        pm.load_participants_tsv(path, _DATASET)


# --- per-dataset join -----------------------------------------------------------------------


def test_only_subjects_present_in_both_tsv_and_disk_are_admitted(tmp_path):
    source = _source(tmp_path)
    _write_tsv(
        source.participants_tsv,
        [
            {"participant_id": "sub-STUNIPD0001", "disease_id": "ST"},  # both -> admitted
            {"participant_id": "sub-STUNIPD0002", "disease_id": "ST"},  # tsv only -> excluded
        ],
    )
    _make_subject_dirs(source.derivatives_dir, "manual_masks", ["sub-STUNIPD0001", "sub-STUNIPD0003"])

    outcome = pm.build_dataset_outcome(_DATASET, source, group_filter=None)

    assert list(outcome.rows["subject_id"]) == ["sub-STUNIPD0001"]
    assert outcome.only_in_tsv == ["sub-STUNIPD0002"]
    assert outcome.only_on_disk == ["sub-STUNIPD0003"]  # on disk, no clinical row -> excluded


def test_presence_columns_reflect_each_data_type_independently(tmp_path):
    source = _source(tmp_path)
    _write_tsv(source.participants_tsv, [{"participant_id": "sub-STUNIPD0001", "disease_id": "ST"}])
    _make_subject_dirs(source.derivatives_dir, "manual_masks", ["sub-STUNIPD0001"])
    _make_subject_dirs(source.derivatives_dir, "sdc", ["sub-STUNIPD0001"])

    row = pm.build_dataset_outcome(_DATASET, source, group_filter=None).rows.iloc[0]

    assert (row["has_lesion"], row["has_sdc"], row["has_features"]) == (True, True, False)


def test_group_filter_excludes_healthy_controls(tmp_path):
    source = _source(tmp_path)
    _write_tsv(
        source.participants_tsv,
        [{"participant_id": "sub-STUNIPD0001", "disease_id": "ST"}, {"participant_id": "sub-STUNIPDHC0001", "disease_id": "HC"}],
    )
    _make_subject_dirs(source.derivatives_dir, "features", ["sub-STUNIPD0001", "sub-STUNIPDHC0001"])

    outcome = pm.build_dataset_outcome(_DATASET, source, group_filter=["ST"])

    assert list(outcome.rows["subject_id"]) == ["sub-STUNIPD0001"]
    assert outcome.excluded_by_group == ["sub-STUNIPDHC0001"]


def test_disease_id_comes_from_subject_id_and_mismatch_is_reported(tmp_path):
    """The tsv says ST, the subject id says HC - the id wins (every other layer parses it
    the same way) and the disagreement is surfaced instead of silently picked between."""
    source = _source(tmp_path)
    _write_tsv(source.participants_tsv, [{"participant_id": "sub-STUNIPDHC0001", "disease_id": "ST"}])
    _make_subject_dirs(source.derivatives_dir, "features", ["sub-STUNIPDHC0001"])

    outcome = pm.build_dataset_outcome(_DATASET, source, group_filter=None)

    assert outcome.rows.iloc[0]["disease_id"] == "HC"
    assert outcome.disease_id_mismatch == [("sub-STUNIPDHC0001", "ST", "HC")]


def test_ucl_legacy_ids_are_promoted_and_original_kept(tmp_path):
    source = pm.DatasetSource(
        participants_tsv=tmp_path / "participants_UCL.tsv",
        derivatives_dir=tmp_path / "derivatives" / "UCL-UK" / "UCLStrokeData",
    )
    _write_tsv(source.participants_tsv, [{"participant_id": "ST_UCL-UK_0001", "disease_id": "ST"}])
    _make_subject_dirs(source.derivatives_dir, "manual_masks", ["sub-STUCLUK0001"])

    row = pm.build_dataset_outcome("UCL-UK/UCLStrokeData", source, group_filter=None).rows.iloc[0]

    assert row["subject_id"] == "sub-STUCLUK0001"
    assert row["original_id"] == "ST_UCL-UK_0001"


# --- merge with an existing file --------------------------------------------------------------


def test_merge_without_overwrite_appends_only_new_subjects_and_keeps_enriched_columns(tmp_path):
    """Regression guard: a second populate run must never wipe the columns enrich_metadata
    wrote into the same file, nor rewrite rows that already exist."""
    output_path = tmp_path / "participants.csv"
    pd.DataFrame(
        [{"subject_id": "sub-STUNIPD0001", "dataset": _DATASET, "has_lesion": True, "age": "54"}]
    ).to_csv(output_path, index=False)
    fresh = pd.DataFrame(
        [
            {"subject_id": "sub-STUNIPD0001", "dataset": _DATASET, "has_lesion": False},
            {"subject_id": "sub-STUNIPD0002", "dataset": _DATASET, "has_lesion": True},
        ]
    )

    merged = pm.merge_with_existing(fresh, output_path, overwrite=False)

    assert list(merged["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    assert merged.loc[merged["subject_id"] == "sub-STUNIPD0001", "has_lesion"].item() == "True"  # untouched
    assert merged.loc[merged["subject_id"] == "sub-STUNIPD0001", "age"].item() == "54"
    assert pd.isna(merged.loc[merged["subject_id"] == "sub-STUNIPD0002", "age"].item())


def test_merge_with_overwrite_recomputes_own_columns_but_carries_over_enriched_ones(tmp_path):
    output_path = tmp_path / "participants.csv"
    pd.DataFrame(
        [
            {"subject_id": "sub-STUNIPD0001", "dataset": _DATASET, "has_lesion": True, "age": "54"},
            {"subject_id": "sub-STUNIPD0009", "dataset": _DATASET, "has_lesion": True, "age": "77"},
        ]
    ).to_csv(output_path, index=False)
    fresh = pd.DataFrame([{"subject_id": "sub-STUNIPD0001", "dataset": _DATASET, "has_lesion": False}])

    merged = pm.merge_with_existing(fresh, output_path, overwrite=True)

    assert list(merged["subject_id"]) == ["sub-STUNIPD0001"]  # no longer admitted -> dropped
    assert not merged.iloc[0]["has_lesion"]  # own column recomputed
    assert merged.iloc[0]["age"] == "54"  # enrich's column preserved


def test_write_table_is_atomic_and_roundtrips_as_strings(tmp_path):
    output_path = tmp_path / "nested" / "participants.csv"
    table = pd.DataFrame([{"subject_id": "sub-STUNIPD0001", "original_id": "0001"}])

    pm.write_table(table, output_path)

    assert pd.read_csv(output_path, dtype=str).iloc[0]["original_id"] == "0001"  # leading zero kept
    assert not list(output_path.parent.glob(".*_tmp_*"))  # no temp leftovers


# --- config ---------------------------------------------------------------------------------


def _write_config(tmp_path, **overrides):
    sources_path = tmp_path / "metadata_sources.json"
    sources_path.write_text(
        json.dumps({_DATASET: {"participants_tsv": "a.tsv", "derivatives_dir": "b"}})
    )
    payload = {
        "project": "clinical_connectome",
        "metadata_sources": str(sources_path),
        "datasets": [_DATASET],
        "group_filter": ["ST"],
        "output_path": str(tmp_path / "participants.csv"),
        "overwrite": False,
        "run_notes": "test",
    }
    payload.update(overrides)
    config_path = tmp_path / "populate_metadata.json"
    config_path.write_text(json.dumps(payload))
    return config_path


def test_load_config_reads_a_valid_file(tmp_path):
    config = pm.load_config(str(_write_config(tmp_path)))

    assert config.datasets == [_DATASET]
    assert config.group_filter == ["ST"]
    assert config.sources[_DATASET].participants_tsv == pm.Path("a.tsv")


def test_load_config_raises_on_duplicate_dataset(tmp_path):
    path = _write_config(tmp_path, datasets=[_DATASET, _DATASET])

    with pytest.raises(ValueError, match="duplicate"):
        pm.load_config(str(path))


def test_load_config_raises_on_dataset_absent_from_the_registry(tmp_path):
    path = _write_config(tmp_path, datasets=["UNIPD/NotRegistered"])

    with pytest.raises(ValueError, match="not in"):
        pm.load_config(str(path))
