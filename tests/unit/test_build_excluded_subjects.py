"""Unit tests for src/pipeline/build_excluded_subjects.py - the config -> excluded_subjects.csv build.

Every test gets its own isolated metadata root and working directory (never touches the real
assets/metadata/, summaries/ or logs/).
"""

import json

import pandas as pd
import pytest

import src.utils.participants as participants_registry
from src.pipeline.build_excluded_subjects import (
    OUTPUT_COLUMNS,
    build_table,
    describe_change,
    load_config,
    main,
    read_lesion_metadata,
    validate_and_write,
)

_REGISTRY = [
    ("sub-STUNIPD0001", "UNIPD/WashU"),
    ("sub-STUNIPD0002", "UNIPD/WashU"),
    ("sub-STUKE0146", "UKE/WAKEUP_acute"),
    ("sub-STUCLUK0383", "UCL-UK/UCLStrokeData"),
]
_HEADER = ",".join(OUTPUT_COLUMNS) + "\n"


@pytest.fixture
def metadata_root(tmp_path, monkeypatch):
    root = tmp_path / "metadata"
    root.mkdir()
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    monkeypatch.chdir(tmp_path)
    lines = ["subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features"]
    lines += [f"{s},{s},{dataset},ST,True,True,False" for s, dataset in _REGISTRY]
    (root / "participants.csv").write_text("\n".join(lines) + "\n")
    pd.DataFrame(
        {
            "subject_id": [s for s, _ in _REGISTRY],
            "lesion_volume_voxels_1mm": [40, 0, 3, 90],
            "lesion_volume_voxels_2mm": [5, 0, 0, 11],
            "out_of_brain_fraction_2mm": [0.0, None, 0.8123456789, 0.1],
        }
    ).to_csv(root / "lesion_metadata.csv", index=False)
    return root


def _entry(reason="lesion_too_small", scope="all", subjects=("sub-STUNIPD0001",), **value):
    body = {"reason": reason, "scope": scope, "subjects": list(subjects)}
    body.update(value or {"value_column": "lesion_volume_voxels_2mm"})
    return body


def _write_config(tmp_path, exclusions, **overrides):
    config = {
        "project": "p",
        "output_path": "assets/metadata/excluded_subjects.csv",
        "lesion_metadata_path": "metadata/lesion_metadata.csv",
        "exclusions": exclusions,
        "run_notes": "n",
        **overrides,
    }
    path = tmp_path / "c.json"
    path.write_text(json.dumps(config))
    return path


def _table(tmp_path, exclusions):
    config = load_config(_write_config(tmp_path, exclusions))
    registry = participants_registry.load_participants_registry()
    return build_table(config, read_lesion_metadata(config.lesion_metadata_path), registry)


# --- config ---------------------------------------------------------------------------------


def test_load_config_parses_entries(tmp_path, metadata_root):
    config = load_config(_write_config(tmp_path, [_entry(), _entry("all_zero_features", "sdc-streamline", value=0)]))

    assert [(e.reason, e.scope) for e in config.exclusions] == [("lesion_too_small", "all"), ("all_zero_features", "sdc-streamline")]
    assert config.exclusions[0].value_column == "lesion_volume_voxels_2mm" and config.exclusions[0].value is None
    assert config.exclusions[1].value == 0 and config.exclusions[1].value_column is None


def test_load_config_empty_exclusions_means_nobody_excluded(tmp_path, metadata_root):
    assert load_config(_write_config(tmp_path, [])).exclusions == []


@pytest.mark.parametrize(
    "entry, message",
    [
        (_entry(reason="typo_reason"), "unregistered reason"),
        (_entry(scope="everywhere"), "unregistered scope"),
        (_entry(subjects=[]), "non-empty list"),
        (_entry(subjects=["sub-STUNIPD0001", "sub-STUNIPD0001"]), "duplicate subject"),
        ({"reason": "empty_mask", "scope": "all", "subjects": ["sub-STUNIPD0001"]}, "exactly one of"),
        ({**_entry(), "value": 0}, "exactly one of"),
        (_entry(value=True), "must be a number"),
        ({**_entry(), "extra": 1}, "unknown key"),
    ],
)
def test_load_config_rejects_a_malformed_entry(tmp_path, metadata_root, entry, message):
    with pytest.raises(ValueError, match=message):
        load_config(_write_config(tmp_path, [entry]))


def test_load_config_rejects_the_same_reason_and_scope_twice(tmp_path, metadata_root):
    with pytest.raises(ValueError, match="more than one entry"):
        load_config(_write_config(tmp_path, [_entry(), _entry(subjects=["sub-STUKE0146"])]))


def test_load_config_requires_every_top_level_key(tmp_path, metadata_root):
    path = _write_config(tmp_path, [])
    raw = json.loads(path.read_text())
    del raw["run_notes"]
    path.write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="run_notes"):
        load_config(path)


# --- build_table ----------------------------------------------------------------------------


def test_build_table_takes_dataset_from_the_registry_and_value_from_the_column(tmp_path, metadata_root):
    table = _table(tmp_path, [_entry(subjects=["sub-STUNIPD0001", "sub-STUCLUK0383"])])

    assert list(table.columns) == OUTPUT_COLUMNS
    assert table.to_dict("records") == [
        {"subject_id": "sub-STUNIPD0001", "dataset": "UNIPD/WashU", "reason": "lesion_too_small", "scope": "all", "value": "5"},
        {"subject_id": "sub-STUCLUK0383", "dataset": "UCL-UK/UCLStrokeData", "reason": "lesion_too_small", "scope": "all", "value": "11"},
    ]


def test_build_table_keeps_a_fraction_with_every_digit_and_a_count_as_an_integer(tmp_path, metadata_root):
    table = _table(tmp_path, [_entry("out_of_brain_fraction_too_high", subjects=["sub-STUKE0146"], value_column="out_of_brain_fraction_2mm")])

    assert table.loc[0, "value"] == "0.8123456789"


def test_build_table_constant_value(tmp_path, metadata_root):
    table = _table(tmp_path, [_entry("all_zero_features", "sdc-streamline", subjects=["sub-STUCLUK0383"], value=0)])

    assert table.loc[0, "value"] == "0"


def test_build_table_no_exclusions_is_an_empty_table_with_the_columns(tmp_path, metadata_root):
    table = _table(tmp_path, [])

    assert table.empty and list(table.columns) == OUTPUT_COLUMNS


def test_build_table_subject_not_in_the_registry_raises(tmp_path, metadata_root):
    with pytest.raises(ValueError, match="not in the registry"):
        _table(tmp_path, [_entry(subjects=["sub-NOPE"])])


def test_build_table_subject_without_a_lesion_metadata_row_raises(tmp_path, metadata_root):
    lesion = pd.read_csv(metadata_root / "lesion_metadata.csv")
    lesion[lesion["subject_id"] != "sub-STUNIPD0001"].to_csv(metadata_root / "lesion_metadata.csv", index=False)

    with pytest.raises(ValueError, match="no row in lesion_metadata.csv"):
        _table(tmp_path, [_entry(subjects=["sub-STUNIPD0001"])])


def test_build_table_unknown_value_column_lists_what_the_file_has(tmp_path, metadata_root):
    with pytest.raises(ValueError, match="not in lesion_metadata.csv"):
        _table(tmp_path, [_entry(value_column="typo_column")])


def test_build_table_empty_value_raises(tmp_path, metadata_root):
    """sub-STUNIPD0002's out_of_brain_fraction is NaN (an empty mask): a blank value must not be written."""
    with pytest.raises(ValueError, match="is empty for"):
        _table(tmp_path, [_entry("out_of_brain_fraction_too_high", subjects=["sub-STUNIPD0002"], value_column="out_of_brain_fraction_2mm")])


def test_build_table_empty_mask_must_really_be_empty(tmp_path, metadata_root):
    """A typo'd id would otherwise exclude a subject with a real lesion (40 voxels at 1 mm)."""
    with pytest.raises(ValueError, match="empty mask but with value != 0"):
        _table(tmp_path, [_entry("empty_mask", subjects=["sub-STUNIPD0001"], value_column="lesion_volume_voxels_1mm")])


def test_build_table_empty_mask_accepts_a_zero_volume(tmp_path, metadata_root):
    table = _table(tmp_path, [_entry("empty_mask", subjects=["sub-STUNIPD0002"], value_column="lesion_volume_voxels_1mm")])

    assert table.loc[0, "value"] == "0"


def test_read_lesion_metadata_missing_file_points_at_the_pipeline_that_writes_it(tmp_path):
    with pytest.raises(FileNotFoundError, match="compute_lesion_metadata"):
        read_lesion_metadata(tmp_path / "nope.csv")


def test_read_lesion_metadata_duplicate_subject_raises(tmp_path):
    path = tmp_path / "lesion_metadata.csv"
    pd.DataFrame({"subject_id": ["sub-A", "sub-A"], "x": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(ValueError, match="duplicate subject_id"):
        read_lesion_metadata(path)


# --- validate_and_write / describe_change ---------------------------------------------------


def test_validate_and_write_dry_run_writes_nothing_and_leaves_no_temp_file(tmp_path, metadata_root):
    table = _table(tmp_path, [_entry()])
    output = tmp_path / "out" / "excluded_subjects.csv"

    validate_and_write(table, output, dry_run=True)

    assert list(output.parent.iterdir()) == []


def test_validate_and_write_replaces_the_file(tmp_path, metadata_root):
    table = _table(tmp_path, [_entry()])
    output = tmp_path / "excluded_subjects.csv"
    output.write_text("old,header\n")

    validate_and_write(table, output, dry_run=False)

    assert pd.read_csv(output, dtype=str).to_dict("records") == table.to_dict("records")


def test_validate_and_write_rejects_a_table_the_matrix_pipelines_would_reject(tmp_path, metadata_root):
    """A subject with an `all` row and a narrower one contradicts itself: the existing file stays untouched."""
    table = _table(tmp_path, [_entry(), _entry("all_zero_features", "sdc-streamline", value=0)])
    output = tmp_path / "excluded_subjects.csv"
    output.write_text("keep,me\n")

    with pytest.raises(ValueError, match="scope='all' row and a narrower one"):
        validate_and_write(table, output, dry_run=False)

    assert output.read_text() == "keep,me\n"
    assert [p.name for p in tmp_path.iterdir() if p.name.startswith(".excluded")] == []


def test_describe_change_missing_file_old_schema_and_diff(tmp_path, metadata_root):
    table = _table(tmp_path, [_entry(subjects=["sub-STUNIPD0001", "sub-STUCLUK0383"])])
    output = tmp_path / "excluded_subjects.csv"

    assert "does not exist" in describe_change(table, output)[0]

    output.write_text("subject_id,dataset,reason,value\n")
    assert "instead of" in describe_change(table, output)[0]

    output.write_text(_HEADER + "sub-STUNIPD0001,UNIPD/WashU,lesion_too_small,all,5\nsub-STUKE0146,UKE/WAKEUP_acute,empty_mask,all,0\n")
    lines = describe_change(table, output)
    assert lines[0] == "1 unchanged, 1 added, 1 removed"
    assert any(line.startswith("+ sub-STUCLUK0383") for line in lines)
    assert any(line.startswith("- sub-STUKE0146") for line in lines)


# --- main (end to end) ----------------------------------------------------------------------


def test_main_writes_the_file_and_report_and_log(tmp_path, metadata_root):
    config = _write_config(tmp_path, [
        _entry("empty_mask", subjects=["sub-STUNIPD0002"], value_column="lesion_volume_voxels_1mm"),
        _entry("all_zero_features", "sdc-streamline", subjects=["sub-STUKE0146"], value=0),
    ])

    assert main(["--config", str(config)]) == 0

    written = pd.read_csv(tmp_path / "assets/metadata/excluded_subjects.csv", dtype=str)
    assert written.to_dict("records") == [
        {"subject_id": "sub-STUNIPD0002", "dataset": "UNIPD/WashU", "reason": "empty_mask", "scope": "all", "value": "0"},
        {"subject_id": "sub-STUKE0146", "dataset": "UKE/WAKEUP_acute", "reason": "all_zero_features", "scope": "sdc-streamline", "value": "0"},
    ]
    assert len(list((tmp_path / "summaries/build_excluded_subjects").glob("*.md"))) == 1
    assert len(list((tmp_path / "logs/build_excluded_subjects").glob("*.log"))) == 1


def test_main_replaces_a_file_with_the_old_schema_and_the_result_loads_for_the_matrix_pipelines(tmp_path, metadata_root):
    """Regression: the file left with only `subject_id,dataset,reason,value` (no `scope`) is rebuilt
    from the config, and the result passes the validator both matrix pipelines call."""
    output = tmp_path / "assets/metadata/excluded_subjects.csv"
    output.parent.mkdir(parents=True)
    output.write_text("subject_id,dataset,reason,value\n")
    config = _write_config(tmp_path, [_entry("all_zero_features", "sdc-streamline", subjects=["sub-STUKE0146"], value=0)])

    assert main(["--config", str(config)]) == 0

    for scope in ("lesion", "sdc-streamline"):
        loaded = participants_registry.load_excluded_subjects(output, scope)
        assert list(loaded["subject_id"]) == (["sub-STUKE0146"] if scope == "sdc-streamline" else [])


def test_main_dry_run_writes_the_report_but_not_the_csv(tmp_path, metadata_root):
    config = _write_config(tmp_path, [_entry()])

    assert main(["--config", str(config), "--dry-run"]) == 0

    assert not (tmp_path / "assets/metadata/excluded_subjects.csv").exists()
    assert len(list((tmp_path / "summaries/build_excluded_subjects").glob("*.md"))) == 1


def test_main_empty_exclusions_writes_a_header_only_file(tmp_path, metadata_root):
    assert main(["--config", str(_write_config(tmp_path, []))]) == 0

    assert (tmp_path / "assets/metadata/excluded_subjects.csv").read_text() == _HEADER


def test_main_a_bad_config_returns_1_and_writes_nothing(tmp_path, metadata_root):
    config = _write_config(tmp_path, [_entry(reason="typo_reason")])

    assert main(["--config", str(config)]) == 1
    assert not (tmp_path / "assets/metadata/excluded_subjects.csv").exists()


def test_main_a_table_the_validator_rejects_returns_1_and_keeps_the_existing_file(tmp_path, metadata_root):
    output = tmp_path / "assets/metadata/excluded_subjects.csv"
    output.parent.mkdir(parents=True)
    output.write_text(_HEADER)
    config = _write_config(tmp_path, [_entry(), _entry("all_zero_features", "sdc-streamline", value=0)])

    assert main(["--config", str(config)]) == 1
    assert output.read_text() == _HEADER
