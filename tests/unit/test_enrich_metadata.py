"""Unit tests for src/pipeline/enrich_metadata.py - synthetic tsv/csv fixtures, no real data."""

import json
import logging
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.pipeline.enrich_metadata import (
    DatasetCoverage,
    EnrichMetadataConfig,
    LesionMetadataJoin,
    ProtectedCells,
    SdcMetadataJoin,
    enrich,
    load_config,
    read_lesion_metadata,
    read_sdc_metadata,
    report_lines,
    resolve_dataset_values,
    source_column_for,
)
from src.utils.metadata_sources import DatasetSource

_REGISTRY_COLUMNS = ["subject_id", "original_id", "dataset", "disease_id", "has_lesion", "has_sdc", "has_features"]

def _registry(rows):
    return pd.DataFrame(rows, columns=_REGISTRY_COLUMNS)


def _write_tsv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(columns)] + ["\t".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n")
    return path


def _config(
    tmp_path, sources, variables, overwrite=True, lesion_metadata=None, datasets=None, sdc_metadata=None,
    protected=None,
):
    return EnrichMetadataConfig(
        project="test",
        sources=sources,
        participants_path=tmp_path / "participants.csv",
        datasets=datasets,
        variables=variables,
        lesion_metadata=lesion_metadata,
        sdc_metadata=sdc_metadata,
        overwrite=overwrite,
        protected=protected,
        run_notes="test",
    )


def test_joins_on_original_id_not_subject_id(tmp_path):
    """UCL-UK's raw participant_id is the legacy site id, not the canonical subject
    id - joining on subject_id would silently match nothing for the whole dataset
    (.claude/lessons_learned.md #30)."""
    tsv = _write_tsv(
        tmp_path / "raw.tsv", ["participant_id", "age"], [["ST_UCL-UK_0001", "61"], ["ST_UCL-UK_0002", "48"]]
    )
    sources = {"UCL-UK/UCLStrokeData": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        ["sub-STUCLUK0001", "ST_UCL-UK_0001", "UCL-UK/UCLStrokeData", "ST", "True", "False", "False"],
        ["sub-STUCLUK0002", "ST_UCL-UK_0002", "UCL-UK/UCLStrokeData", "ST", "True", "False", "False"],
    ])

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"]))
    assert list(out["age"]) == ["61", "48"]


def test_missing_column_for_one_dataset_is_not_an_error(tmp_path):
    """A variable absent from a dataset's tsv is a structural per-dataset gap
    (UCL-UK has no NIHSS at all) - every subject gets an empty cell, no raise."""
    tsv_a = _write_tsv(tmp_path / "a.tsv", ["participant_id", "age", "NIHSS"], [["sub-STUNIPD0001", "70", "4"]])
    tsv_b = _write_tsv(tmp_path / "b.tsv", ["participant_id", "age"], [["sub-STUKE0001", "55"]])
    sources = {
        "UNIPD/WashU": DatasetSource(tsv_a, tmp_path),
        "UKE/WAKEUP_acute": DatasetSource(tsv_b, tmp_path),
    }
    registry = _registry([
        ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"],
        ["sub-STUKE0001", "sub-STUKE0001", "UKE/WAKEUP_acute", "ST", "True", "True", "False"],
    ])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["age", "NIHSS"]))
    assert list(out["age"]) == ["70", "55"]
    assert out.loc[0, "NIHSS"] == "4"
    assert pd.isna(out.loc[1, "NIHSS"])
    missing = {c.dataset: c.missing_variables for c in coverages}
    assert missing["UKE/WAKEUP_acute"] == ["NIHSS"]
    assert missing["UNIPD/WashU"] == []


def test_na_sentinel_and_blank_become_empty(tmp_path):
    """"n/a" and a blank cell are both genuine missing values, never kept as strings."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "n/a"], ["sub-STUNIPD0002", ""], ["sub-STUNIPD0003", "62"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2, 3)
    ])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["age"]))
    assert pd.isna(out.loc[0, "age"]) and pd.isna(out.loc[1, "age"])
    assert out.loc[2, "age"] == "62"
    assert coverages[0].n_missing_cells["age"] == 2


def test_registered_substitution_is_applied_and_reported(tmp_path):
    """PASPORT has no baseline NIHSS - the documented NIHSS_at_presentation proxy is
    applied, and surfaced in the coverage record rather than being invisible."""
    tsv = _write_tsv(
        tmp_path / "p.tsv", ["participant_id", "NIHSS_at_presentation"], [["sub-STUNIPD0001", "9"]]
    )
    sources = {"UNIPD/PASPORT": DatasetSource(tsv, tmp_path)}
    registry = _registry([["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/PASPORT", "ST", "True", "True", "False"]])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["NIHSS"]))
    assert out.loc[0, "NIHSS"] == "9"
    assert coverages[0].substituted == {"NIHSS": "NIHSS_at_presentation"}


def test_substitution_is_not_applied_to_other_datasets(tmp_path):
    """The proxy is registered for PASPORT only - another dataset lacking NIHSS gets
    an empty cell, never NIHSS_at_presentation silently."""
    tsv = _write_tsv(
        tmp_path / "w.tsv", ["participant_id", "NIHSS_at_presentation"], [["sub-STUNIPD0001", "9"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"]])

    out, coverages = enrich(registry, _config(tmp_path, sources, ["NIHSS"]))
    assert pd.isna(out.loc[0, "NIHSS"])
    assert coverages[0].substituted == {}


def test_source_column_for_prefers_canonical_name():
    assert source_column_for("UNIPD/PASPORT", "NIHSS", ["NIHSS", "NIHSS_at_presentation"]) == "NIHSS"
    assert source_column_for("UNIPD/PASPORT", "NIHSS", ["NIHSS_at_presentation"]) == "NIHSS_at_presentation"
    assert source_column_for("UNIPD/WashU", "NIHSS", ["NIHSS_at_presentation"]) is None


def test_subject_absent_from_raw_tsv_raises(tmp_path):
    """participants.csv and the raw tsv disagreeing about who exists is a real
    inconsistency, not a missing value."""
    tsv = _write_tsv(tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"]])
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([["sub-STUNIPD0009", "sub-STUNIPD0009", "UNIPD/WashU", "ST", "True", "True", "False"]])

    with pytest.raises(ValueError, match="no row in"):
        enrich(registry, _config(tmp_path, sources, ["age"]))


def test_lesion_side_source_marks_only_resolved_values(tmp_path):
    """lesion_side_source distinguishes a clinically recorded side from an unresolved
    one - so a later, geometrically computed value stays distinguishable."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "lesion_side"],
        [["sub-STUNIPD0001", "left"], ["sub-STUNIPD0002", "n/a"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])

    out, _ = enrich(registry, _config(tmp_path, sources, ["lesion_side"]))
    assert out.loc[0, "lesion_side_source"] == "clinical"
    assert pd.isna(out.loc[1, "lesion_side_source"])


def test_append_mode_writes_only_the_empty_cells(tmp_path):
    """overwrite=false only writes empty cells - an existing value is never replaced."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])
    registry["age"] = ["999", np.nan]  # 999 is a hand-corrected value that must survive

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], overwrite=False))
    assert list(out["age"]) == ["999", "55"]


def test_overwrite_mode_recomputes_every_value(tmp_path):
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])
    registry["age"] = ["999", np.nan]

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], overwrite=True))
    assert list(out["age"]) == ["70", "55"]


def test_out_of_scope_dataset_keeps_its_values(tmp_path):
    """A run restricted to one dataset never blanks another dataset's existing cells."""
    tsv = _write_tsv(tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"]])
    sources = {
        "UNIPD/WashU": DatasetSource(tsv, tmp_path),
        "UKE/WAKEUP_acute": DatasetSource(tmp_path / "missing.tsv", tmp_path),
    }
    registry = _registry([
        ["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"],
        ["sub-STUKE0001", "sub-STUKE0001", "UKE/WAKEUP_acute", "ST", "True", "True", "False"],
    ])
    registry["age"] = [np.nan, "44"]

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], datasets=["UNIPD/WashU"]))
    assert list(out["age"]) == ["70", "44"]


def test_load_config_rejects_unknown_variable(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age", "not_a_variable"], "overwrite": True, "protected_path": None, "run_notes": "n",
    }))
    with pytest.raises(ValueError, match="unknown variable"):
        load_config(config_path)


def test_load_config_rejects_duplicate_variables(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age", "age"], "overwrite": True, "protected_path": None, "run_notes": "n",
    }))
    with pytest.raises(ValueError, match="duplicate"):
        load_config(config_path)


def test_resolve_dataset_values_reports_missing_cell_counts(tmp_path):
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age", "sex"],
        [["sub-STUNIPD0001", "70", "M"], ["sub-STUNIPD0002", "n/a", "F"]],
    )
    rows = pd.DataFrame({
        "subject_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"],
        "original_id": ["sub-STUNIPD0001", "sub-STUNIPD0002"],
    })
    _, coverage = resolve_dataset_values(
        "UNIPD/WashU", DatasetSource(tsv, tmp_path), rows, ["age", "sex"]
    )
    assert coverage.n_missing_cells == {"age": 1, "sex": 0}


def test_rerun_over_already_enriched_file_is_idempotent(tmp_path):
    """Regression (.claude/lessons_learned.md #17): the merge branch only runs when the
    column already exists, so it was never exercised by a first run. participants.csv is
    read with dtype=str, and pandas' "str" dtype rejects a NaN assignment - a re-run
    writing back a genuinely missing value used to raise TypeError.
    """
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "n/a"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2)
    ])
    config = _config(tmp_path, sources, ["age"])

    first, _ = enrich(registry, config)
    # round-trip through CSV exactly as the pipeline does, so the dtype matches production
    path = tmp_path / "participants.csv"
    first.to_csv(path, index=False)
    second, _ = enrich(pd.read_csv(path, dtype=str), config)

    assert second.loc[0, "age"] == "70"
    assert pd.isna(second.loc[1, "age"])


# --- geometric lesion_side fallback -------------------------------------------------------------


# --- lesion_volume_voxels_1mm (a second grid for the same volume) ---------------------------------


# --- the lesion_metadata join ---------------------------------------------------------------------

_MEASURED_COLUMNS = ["subject_id", "dataset", "lesion_volume_voxels_2mm", "lesion_side_2mm"]


def _write_measured(tmp_path, rows, columns=None):
    """A synthetic assets/metadata/lesion_metadata.csv - the file this pipeline now joins onto
    instead of reading masks itself."""
    path = tmp_path / "lesion_metadata.csv"
    pd.DataFrame(rows, columns=columns or _MEASURED_COLUMNS).to_csv(path, index=False)
    return path


def _join(path, copy_columns=("lesion_volume_voxels_2mm",), lesion_side_from="lesion_side_2mm", override_datasets=()):
    return LesionMetadataJoin(
        path=path, copy_columns=list(copy_columns), lesion_side_from=lesion_side_from,
        geometric_override_datasets=list(override_datasets),
    )


def _bool_registry(rows):
    """Registry rows as (subject_id, dataset, has_lesion) - with has_lesion a REAL bool, the way
    src.utils.participants.load_participants_registry returns it (which is how main() reads the
    file). A str-dtype flag is rejected outright, see
    test_join_rejects_a_string_has_lesion_column."""
    registry = _registry([
        [subject_id, subject_id, dataset, "ST", has_lesion, True, False]
        for subject_id, dataset, has_lesion in rows
    ])
    for column in ("has_lesion", "has_sdc", "has_features"):
        registry[column] = registry[column].astype(bool)
    return registry


def _one_subject_sources(tmp_path, columns=("participant_id", "lesion_side"), rows=None):
    tsv = _write_tsv(tmp_path / "a.tsv", list(columns), rows if rows is not None else [["sub-STUNIPD0001", "n/a"]])
    return {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}


# --- read_lesion_metadata: parsing and the three strict join checks -------------------------------


def test_read_lesion_metadata_missing_file_points_at_the_pipeline_that_writes_it(tmp_path):
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    with pytest.raises(FileNotFoundError, match="compute_lesion_metadata"):
        read_lesion_metadata(_join(tmp_path / "never_written.csv"), registry, ["UNIPD/WashU"])


def test_read_lesion_metadata_missing_key_column_raises(tmp_path):
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", 4, "left"]],
                           columns=["subject_id", "lesion_volume_voxels_2mm", "lesion_side_2mm"])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    with pytest.raises(ValueError, match="missing required column"):
        read_lesion_metadata(_join(path), registry, ["UNIPD/WashU"])


def test_read_lesion_metadata_requested_column_absent_lists_what_the_file_has(tmp_path):
    """The CSV's metric columns are named after the grids compute_lesion_metadata was configured
    with, so a copy_columns entry can only be checked against the real file - and when it fails
    it must say which columns exist, since the answer depends on that other config."""
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    with pytest.raises(ValueError, match="lesion_volume_voxels_1mm"):
        read_lesion_metadata(
            _join(path, copy_columns=["lesion_volume_voxels_1mm"]), registry, ["UNIPD/WashU"]
        )


def test_read_lesion_metadata_duplicate_subject_raises(tmp_path):
    path = _write_measured(tmp_path, [
        ["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"],
        ["sub-STUNIPD0001", "UNIPD/WashU", 9, "right"],
    ])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    with pytest.raises(ValueError, match="duplicate subject_id"):
        read_lesion_metadata(_join(path), registry, ["UNIPD/WashU"])


def test_read_lesion_metadata_stale_file_raises(tmp_path):
    """An in-scope subject with has_lesion=True and no row means the CSV predates it - the number
    that would land in participants.csv simply does not exist yet."""
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    registry = _bool_registry([
        ("sub-STUNIPD0001", "UNIPD/WashU", True), ("sub-STUNIPD0002", "UNIPD/WashU", True),
    ])
    with pytest.raises(ValueError, match="have no row"):
        read_lesion_metadata(_join(path), registry, ["UNIPD/WashU"])


def test_read_lesion_metadata_stale_check_is_scoped_to_this_runs_datasets(tmp_path):
    """A run may legitimately enrich a subset of the cohort, so a subject of an out-of-scope
    dataset missing from the CSV is not this run's problem - unlike the two global checks."""
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    registry = _bool_registry([
        ("sub-STUNIPD0001", "UNIPD/WashU", True), ("sub-STUKE0146", "UKE/WAKEUP_acute", True),
    ])

    measured = read_lesion_metadata(_join(path), registry, ["UNIPD/WashU"])

    assert list(measured.index) == ["sub-STUNIPD0001"]


def test_read_lesion_metadata_spurious_row_raises(tmp_path):
    path = _write_measured(tmp_path, [
        ["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"],
        ["sub-STUNIPD9999", "UNIPD/WashU", 7, "right"],
    ])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    with pytest.raises(ValueError, match="disagree about who exists"):
        read_lesion_metadata(_join(path), registry, ["UNIPD/WashU"])


def test_read_lesion_metadata_row_for_a_subject_without_a_mask_raises(tmp_path):
    """Measured here but has_lesion=False there: one of the two files is wrong about who has a
    mask, and guessing which would corrupt either the registry or the matrix cohort."""
    path = _write_measured(tmp_path, [
        ["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"],
        ["sub-STUNIPD0002", "UNIPD/WashU", 7, "right"],
    ])
    registry = _bool_registry([
        ("sub-STUNIPD0001", "UNIPD/WashU", True), ("sub-STUNIPD0002", "UNIPD/WashU", False),
    ])
    with pytest.raises(ValueError, match="disagree about who has a lesion mask"):
        read_lesion_metadata(_join(path), registry, ["UNIPD/WashU"])


def test_join_rejects_a_string_has_lesion_column(tmp_path):
    """participants.csv is read with dtype=str, where astype(bool) maps the STRING "False" to
    True (any non-empty string is truthy) - which would silently invert every check above. The
    registry must arrive already parsed."""
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    registry = _registry([["sub-STUNIPD0001", "sub-STUNIPD0001", "UNIPD/WashU", "ST", "True", "True", "False"]])

    with pytest.raises(ValueError, match="instead of bool"):
        read_lesion_metadata(_join(path), registry, ["UNIPD/WashU"])


# --- enrich(): copying the columns across ---------------------------------------------------------


def test_copy_columns_writes_the_volume_as_an_integer_not_a_float(tmp_path):
    """Subjects outside this run's scope are absent from the mapping, introducing a NaN that
    promotes the column to float - a voxel *count* would then be written as "4.0"."""
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    config = _config(tmp_path, sources, ["age"], lesion_metadata=_join(path, lesion_side_from=None))

    out, _ = enrich(registry, config)

    assert out.loc[0, "lesion_volume_voxels_2mm"] == 4
    out.to_csv(tmp_path / "written.csv", index=False)
    assert "4.0" not in (tmp_path / "written.csv").read_text()


def test_copy_columns_follow_the_overwrite_rule_and_append_warns_about_the_stale_value(tmp_path, caplog):
    """A mask-derived column obeys the same rule as every other: overwrite=true replaces it, and
    overwrite=false keeps it - but a kept value that differs from the freshly measured one is
    logged, so a number frozen after the masks changed is never kept in silence."""
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    registry["lesion_volume_voxels_2mm"] = ["999"]
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    join = _join(path, lesion_side_from=None)

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], overwrite=True, lesion_metadata=join))
    assert out.loc[0, "lesion_volume_voxels_2mm"] == 4

    with caplog.at_level(logging.WARNING):
        kept, _ = enrich(registry, _config(tmp_path, sources, ["age"], overwrite=False, lesion_metadata=join))
    assert kept.loc[0, "lesion_volume_voxels_2mm"] == "999"
    assert "lesion_volume_voxels_2mm: 1 existing value(s) differ" in caplog.text


def test_append_mode_is_silent_when_the_existing_values_match_the_fresh_ones(tmp_path, caplog):
    """The warning is for a real disagreement: a re-run over an unchanged file, whose stored text
    equals the freshly resolved value, must not cry wolf (an integer count, a float, a string)."""
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", True, True)])
    lesion_csv = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    sdc_csv = _write_sdc_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 59503.8418, 0.032565]])
    config = _config(
        tmp_path, sources, ["age"], overwrite=True,
        lesion_metadata=_join(lesion_csv, lesion_side_from=None), sdc_metadata=_sdc_join(sdc_csv),
    )
    first, _ = enrich(registry, config)
    path = tmp_path / "participants.csv"
    first.to_csv(path, index=False)
    reread = pd.read_csv(path, dtype=str)
    reread[["has_lesion", "has_sdc", "has_features"]] = reread[["has_lesion", "has_sdc", "has_features"]] == "True"

    with caplog.at_level(logging.WARNING):
        enrich(reread, replace(config, overwrite=False))

    assert "differ" not in caplog.text


def test_a_column_not_in_copy_columns_is_not_written(tmp_path):
    """The CSV carries one set of metrics per grid; the registry only gets what copy_columns
    names, and everything else stays available in the CSV for the notebook."""
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    path = _write_measured(
        tmp_path,
        [["sub-STUNIPD0001", "UNIPD/WashU", 4, 32, "left"]],
        columns=["subject_id", "dataset", "lesion_volume_voxels_2mm", "lesion_volume_voxels_1mm", "lesion_side_2mm"],
    )
    config = _config(tmp_path, sources, ["age"], lesion_metadata=_join(path, lesion_side_from=None))

    out, _ = enrich(registry, config)

    assert "lesion_volume_voxels_2mm" in out.columns
    assert "lesion_volume_voxels_1mm" not in out.columns


# --- enrich(): lesion_side_from ------------------------------------------------------------------


def test_lesion_side_from_fills_only_the_cells_the_clinical_pass_left_empty(tmp_path):
    """0001 has a clinical side and must keep it (with source "clinical"); 0002 has none and gets
    the geometric one. The CSV has a side for BOTH, so an unrestricted copy would overwrite the
    clinical value - the one thing this branch must never do."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "lesion_side"],
        [["sub-STUNIPD0001", "left"], ["sub-STUNIPD0002", "n/a"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _bool_registry([
        ("sub-STUNIPD0001", "UNIPD/WashU", True), ("sub-STUNIPD0002", "UNIPD/WashU", True),
    ])
    path = _write_measured(tmp_path, [
        ["sub-STUNIPD0001", "UNIPD/WashU", 4, "right"],  # disagrees with the clinical label
        ["sub-STUNIPD0002", "UNIPD/WashU", 9, "both"],
    ])
    config = _config(tmp_path, sources, ["lesion_side"], lesion_metadata=_join(path, copy_columns=[]))

    out, _ = enrich(registry, config)
    by_id = out.set_index("subject_id")

    assert by_id.loc["sub-STUNIPD0001", "lesion_side"] == "left"
    assert by_id.loc["sub-STUNIPD0001", "lesion_side_source"] == "clinical"
    assert by_id.loc["sub-STUNIPD0002", "lesion_side"] == "both"
    assert by_id.loc["sub-STUNIPD0002", "lesion_side_source"] == "geometric"


def test_lesion_side_from_leaves_the_cell_empty_when_the_csv_has_no_side(tmp_path, caplog):
    """A mask with no attributable side (empty, or confined to the midline plane) has an empty
    lesion_side in the CSV - the registry cell stays empty too, and the warning says why rather
    than leaving "why is this subject still empty" to be reconstructed by hand."""
    tsv = _write_tsv(tmp_path / "a.tsv", ["participant_id", "lesion_side"], [["sub-STUNIPD0001", "n/a"]])
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 0, None]])
    config = _config(tmp_path, sources, ["lesion_side"], lesion_metadata=_join(path, copy_columns=[]))

    with caplog.at_level(logging.WARNING):
        out, _ = enrich(registry, config)

    assert pd.isna(out.loc[0, "lesion_side"])
    assert pd.isna(out.loc[0, "lesion_side_source"])
    assert "no side attributable to their mask" in caplog.text


# --- load_config validation of the block ----------------------------------------------------------


def _write_join_config(tmp_path, block, variables=("lesion_side",)):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": list(variables), "lesion_metadata": block, "overwrite": True, "protected_path": None, "run_notes": "n",
    }))
    return config_path


def test_load_config_parses_a_valid_lesion_metadata_block(tmp_path):
    config = load_config(_write_join_config(tmp_path, {
        "path": "assets/metadata/lesion_metadata.csv",
        "copy_columns": ["lesion_volume_voxels_2mm"],
        "lesion_side_from": "lesion_side_2mm",
        "geometric_override_datasets": [],
    }))

    assert config.lesion_metadata.path == Path("assets/metadata/lesion_metadata.csv")
    assert config.lesion_metadata.copy_columns == ["lesion_volume_voxels_2mm"]
    assert config.lesion_metadata.lesion_side_from == "lesion_side_2mm"
    assert config.lesion_metadata.geometric_override_datasets == []


def test_load_config_rejects_copying_onto_a_column_populate_metadata_owns(tmp_path):
    """The two scripts never overwrite each other's columns - a copy_columns entry naming one of
    populate_metadata's would break that silently."""
    with pytest.raises(ValueError, match="owned by"):
        load_config(_write_join_config(tmp_path, {
            "path": "x.csv", "copy_columns": ["dataset"],
            "lesion_side_from": None, "geometric_override_datasets": [],
        }))


def test_load_config_lesion_side_from_requires_lesion_side_in_variables(tmp_path):
    with pytest.raises(ValueError, match="not in 'variables'"):
        load_config(_write_join_config(tmp_path, {
            "path": "x.csv", "copy_columns": [],
            "lesion_side_from": "lesion_side_2mm", "geometric_override_datasets": [],
        }, variables=("age",)))


def test_load_config_rejects_the_side_column_in_both_keys(tmp_path):
    """The two keys have different write rules, so the same column in both would write the same
    fact twice under two names."""
    with pytest.raises(ValueError, match="both 'lesion_side_from' and in 'copy_columns'"):
        load_config(_write_join_config(tmp_path, {
            "path": "x.csv", "copy_columns": ["lesion_side_2mm"],
            "lesion_side_from": "lesion_side_2mm", "geometric_override_datasets": [],
        }))


def test_load_config_rejects_a_block_that_copies_nothing(tmp_path):
    with pytest.raises(ValueError, match="nothing to copy"):
        load_config(_write_join_config(tmp_path, {
            "path": "x.csv", "copy_columns": [],
            "lesion_side_from": None, "geometric_override_datasets": [],
        }))


# --- enrich(): geometric_override_datasets ------------------------------------------------------


def _override_fixture(tmp_path, rows):
    """rows: (subject_id, dataset, clinical side, geometric side). One tsv per dataset, one measured csv."""
    sources = {}
    for dataset in sorted({r[1] for r in rows}):
        tsv = _write_tsv(
            tmp_path / f"{dataset.replace('/', '_')}.tsv", ["participant_id", "lesion_side"],
            [[r[0], r[2]] for r in rows if r[1] == dataset],
        )
        sources[dataset] = DatasetSource(tsv, tmp_path)
    registry = _bool_registry([(r[0], r[1], True) for r in rows])
    path = _write_measured(tmp_path, [[r[0], r[1], 5, r[3]] for r in rows])
    return sources, registry, path


def test_override_forces_the_geometric_side_only_on_a_full_left_right_inversion(tmp_path, caplog):
    """In a listed dataset a clinical left vs geometric right (and the reverse) takes the geometric
    side with source "geometric". Everything else keeps the clinical value: same side, a geometric
    `both` (a disagreement of degree), and the same inversion in a dataset NOT listed."""
    sources, registry, path = _override_fixture(tmp_path, [
        ("sub-STUNIPD0001", "UNIPD/WashU", "left", "right"),   # inverted -> forced
        ("sub-STUNIPD0002", "UNIPD/WashU", "right", "left"),   # inverted -> forced
        ("sub-STUNIPD0003", "UNIPD/WashU", "left", "left"),    # agrees
        ("sub-STUNIPD0004", "UNIPD/WashU", "left", "both"),    # degree, not inversion
        ("sub-STUNIPD0005", "UNIPD/PSP", "left", "right"),     # inverted, but dataset not listed
    ])
    config = _config(
        tmp_path, sources, ["lesion_side"],
        lesion_metadata=_join(path, copy_columns=[], override_datasets=["UNIPD/WashU"]),
    )

    with caplog.at_level(logging.WARNING):
        out, _ = enrich(registry, config)
    by_id = out.set_index("subject_id")

    assert by_id.loc["sub-STUNIPD0001", ["lesion_side", "lesion_side_source"]].tolist() == ["right", "geometric"]
    assert by_id.loc["sub-STUNIPD0002", ["lesion_side", "lesion_side_source"]].tolist() == ["left", "geometric"]
    for subject, side in (("sub-STUNIPD0003", "left"), ("sub-STUNIPD0004", "left"), ("sub-STUNIPD0005", "left")):
        assert by_id.loc[subject, ["lesion_side", "lesion_side_source"]].tolist() == [side, "clinical"]
    assert "sub-STUNIPD0001" in caplog.text and "sub-STUNIPD0002" in caplog.text
    assert "sub-STUNIPD0003" not in caplog.text


def test_override_disabled_by_default_keeps_the_clinical_side(tmp_path):
    sources, registry, path = _override_fixture(tmp_path, [("sub-STUNIPD0001", "UNIPD/WashU", "left", "right")])
    config = _config(tmp_path, sources, ["lesion_side"], lesion_metadata=_join(path, copy_columns=[]))

    out, _ = enrich(registry, config)

    assert out.loc[0, ["lesion_side", "lesion_side_source"]].tolist() == ["left", "clinical"]


def test_override_rerun_over_the_enriched_file_is_stable(tmp_path):
    """A second run, over the file the first one wrote, gives the same registry."""
    sources, registry, path = _override_fixture(tmp_path, [("sub-STUNIPD0001", "UNIPD/WashU", "left", "right")])
    config = _config(
        tmp_path, sources, ["lesion_side"],
        lesion_metadata=_join(path, copy_columns=[], override_datasets=["UNIPD/WashU"]),
    )

    first, _ = enrich(registry, config)
    second, _ = enrich(first, config)

    assert second.loc[0, ["lesion_side", "lesion_side_source"]].tolist() == ["right", "geometric"]


def test_override_naming_a_dataset_absent_from_the_registry_raises(tmp_path):
    sources, registry, path = _override_fixture(tmp_path, [("sub-STUNIPD0001", "UNIPD/WashU", "left", "left")])
    config = _config(
        tmp_path, sources, ["lesion_side"],
        lesion_metadata=_join(path, copy_columns=[], override_datasets=["UNIPD/Typo"]),
    )

    with pytest.raises(ValueError, match="UNIPD/Typo"):
        enrich(registry, config)


def test_load_config_override_requires_lesion_side_from(tmp_path):
    with pytest.raises(ValueError, match="no geometric side to force"):
        load_config(_write_join_config(tmp_path, {
            "path": "x.csv", "copy_columns": ["lesion_volume_voxels_2mm"], "lesion_side_from": None,
            "geometric_override_datasets": ["UNIPD/WashU"],
        }))


def test_load_config_requires_the_override_key(tmp_path):
    with pytest.raises(ValueError, match="geometric_override_datasets"):
        load_config(_write_join_config(tmp_path, {
            "path": "x.csv", "copy_columns": [], "lesion_side_from": "lesion_side_2mm",
        }))


def test_report_lines_dumps_lesion_metadata_as_json_and_null_when_disabled(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    coverage = [DatasetCoverage("UNIPD/WashU", 1, [], {}, {"age": 0})]
    now = datetime(2026, 9, 29, 12, 0, 0)

    with_join = report_lines(
        _config(tmp_path, sources, ["age"], lesion_metadata=_join(tmp_path / "lesion_metadata.csv")), coverage, now
    )
    assert '"copy_columns": [' in "\n".join(with_join)
    assert '"lesion_side_from": "lesion_side_2mm"' in "\n".join(with_join)

    without = report_lines(_config(tmp_path, sources, ["age"]), coverage, now)
    assert "null" in "\n".join(without)


# --- the sdc_metadata join ------------------------------------------------------------------------------

_SDC_COLUMNS = ["subject_id", "dataset", "disconnection_load_voxels_1mm", "disconnection_mean_1mm"]
_SDC_BOTH = ("disconnection_load_voxels_1mm", "disconnection_mean_1mm")


def _write_sdc_measured(tmp_path, rows, columns=None):
    """A synthetic assets/metadata/sdc_metadata.csv."""
    path = tmp_path / "sdc_metadata.csv"
    pd.DataFrame(rows, columns=columns or _SDC_COLUMNS).to_csv(path, index=False)
    return path


def _sdc_join(path, copy_columns=_SDC_BOTH):
    return SdcMetadataJoin(path=path, copy_columns=list(copy_columns))


def _sdc_registry(rows):
    """Registry rows as (subject_id, dataset, has_sdc, has_lesion), real bools like
    load_participants_registry returns."""
    registry = _registry([
        [subject_id, subject_id, dataset, "ST", has_lesion, has_sdc, False]
        for subject_id, dataset, has_sdc, has_lesion in rows
    ])
    for column in ("has_lesion", "has_sdc", "has_features"):
        registry[column] = registry[column].astype(bool)
    return registry


def test_read_sdc_metadata_missing_file_points_at_the_pipeline_that_writes_it(tmp_path):
    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", True, True)])
    with pytest.raises(FileNotFoundError, match="compute_sdc_metadata"):
        read_sdc_metadata(_sdc_join(tmp_path / "never_written.csv"), registry, ["UNIPD/WashU"])


def test_read_sdc_metadata_requested_column_absent_lists_what_the_file_has(tmp_path):
    """The CSV's column names carry the grid compute_sdc_metadata was configured with, so a
    config naming another grid must say what the file actually holds."""
    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", True, True)])
    path = _write_sdc_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 5.0, 0.1]])
    with pytest.raises(ValueError, match=r"disconnection_load_voxels_2mm.*sdc_metadata.*it has"):
        read_sdc_metadata(_sdc_join(path, ["disconnection_load_voxels_2mm"]), registry, ["UNIPD/WashU"])


def test_read_sdc_metadata_stale_file_raises_and_names_its_producer(tmp_path):
    registry = _sdc_registry([
        ("sub-STUNIPD0001", "UNIPD/WashU", True, True), ("sub-STUNIPD0002", "UNIPD/WashU", True, True),
    ])
    path = _write_sdc_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 5.0, 0.1]])
    with pytest.raises(ValueError, match=r"have no row.*compute_sdc_metadata"):
        read_sdc_metadata(_sdc_join(path), registry, ["UNIPD/WashU"])


def test_read_sdc_metadata_spurious_row_raises(tmp_path):
    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", True, True)])
    path = _write_sdc_measured(
        tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 5.0, 0.1], ["sub-STUNIPD0099", "UNIPD/WashU", 1.0, 0.0]]
    )
    with pytest.raises(ValueError, match="disagree about who exists"):
        read_sdc_metadata(_sdc_join(path), registry, ["UNIPD/WashU"])


def test_read_sdc_metadata_row_for_a_subject_without_sdc_output_raises(tmp_path):
    registry = _sdc_registry([
        ("sub-STUNIPD0001", "UNIPD/WashU", True, True), ("sub-STUNIPD0002", "UNIPD/WashU", False, True),
    ])
    path = _write_sdc_measured(
        tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 5.0, 0.1], ["sub-STUNIPD0002", "UNIPD/WashU", 1.0, 0.0]]
    )
    with pytest.raises(ValueError, match="disagree about who has SDC output"):
        read_sdc_metadata(_sdc_join(path), registry, ["UNIPD/WashU"])


def test_each_join_checks_its_own_flag_not_the_other_ones(tmp_path):
    """Regression for generalising the strict join over a flag column: the lesion join must
    keep reading has_lesion and the SDC join has_sdc. A subject with a mask but no SDC output
    (or the reverse) is legitimate for the join that does not concern it."""
    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", False, True)])  # has_lesion, no SDC
    lesion_csv = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    assert list(read_lesion_metadata(_join(lesion_csv), registry, ["UNIPD/WashU"]).index) == ["sub-STUNIPD0001"]

    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", True, False)])  # SDC, no registered mask
    sdc_csv = _write_sdc_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 5.0, 0.1]])
    assert list(read_sdc_metadata(_sdc_join(sdc_csv), registry, ["UNIPD/WashU"]).index) == ["sub-STUNIPD0001"]


def test_sdc_columns_are_copied_as_floats_without_integer_coercion(tmp_path):
    """A summed probability is not a count: it must keep its fractional part (the Int64
    handling the lesion volume needs would truncate it)."""
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", True, True)])
    path = _write_sdc_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 59503.8418, 0.032565]])
    config = _config(tmp_path, sources, ["age"], sdc_metadata=_sdc_join(path))

    out, _ = enrich(registry, config)

    assert out.loc[0, "disconnection_load_voxels_1mm"] == pytest.approx(59503.8418)
    assert out.loc[0, "disconnection_mean_1mm"] == pytest.approx(0.032565)


def test_sdc_columns_overwrite_in_scope_and_leave_other_datasets_alone(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _sdc_registry([
        ("sub-STUNIPD0001", "UNIPD/WashU", True, True), ("sub-STUKLFR0001", "UKLFR/stroke_UKLFR", True, True),
    ])
    registry["disconnection_load_voxels_1mm"] = ["1.0", "777.0"]
    path = _write_sdc_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 5.0, 0.1]])
    config = _config(
        tmp_path, sources, ["age"], overwrite=True, datasets=["UNIPD/WashU"],
        sdc_metadata=_sdc_join(path, _SDC_BOTH[:1]),
    )

    out, _ = enrich(registry, config)

    by_id = out.set_index("subject_id")["disconnection_load_voxels_1mm"]
    assert float(by_id["sub-STUNIPD0001"]) == 5.0  # stale value replaced
    assert by_id["sub-STUKLFR0001"] == "777.0"  # out-of-scope dataset untouched


def test_both_blocks_can_run_in_the_same_enrichment(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _sdc_registry([("sub-STUNIPD0001", "UNIPD/WashU", True, True)])
    lesion_csv = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    sdc_csv = _write_sdc_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 5.0, 0.1]])
    config = _config(
        tmp_path, sources, ["age"], lesion_metadata=_join(lesion_csv, lesion_side_from=None),
        sdc_metadata=_sdc_join(sdc_csv),
    )

    out, _ = enrich(registry, config)

    assert out.loc[0, "lesion_volume_voxels_2mm"] == 4
    assert out.loc[0, "disconnection_load_voxels_1mm"] == 5.0


# --- load_config validation of the sdc_metadata block ---------------------------------------------------


def _write_sdc_join_config(tmp_path, block, lesion_block=None):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age"], "lesion_metadata": lesion_block, "sdc_metadata": block, "overwrite": True, "protected_path": None, "run_notes": "n",
    }))
    return config_path


def test_load_config_parses_a_valid_sdc_metadata_block(tmp_path):
    config = load_config(_write_sdc_join_config(tmp_path, {
        "path": "assets/metadata/sdc_metadata.csv", "copy_columns": list(_SDC_BOTH),
    }))

    assert config.sdc_metadata.path == Path("assets/metadata/sdc_metadata.csv")
    assert config.sdc_metadata.copy_columns == list(_SDC_BOTH)


def test_load_config_sdc_metadata_defaults_to_disabled(tmp_path):
    assert load_config(_write_sdc_join_config(tmp_path, None)).sdc_metadata is None


@pytest.mark.parametrize(
    "block, match",
    [
        pytest.param("a string", "must be an object or null", id="not-an-object"),
        pytest.param({"copy_columns": ["x"]}, "missing required key 'path'", id="path-absent"),
        pytest.param({"path": "a.csv"}, "missing required key 'copy_columns'", id="copy-columns-absent"),
        pytest.param({"path": "", "copy_columns": ["x"]}, "non-empty string", id="empty-path"),
        pytest.param({"path": "a.csv", "copy_columns": []}, "'copy_columns' is empty", id="nothing-to-copy"),
        pytest.param({"path": "a.csv", "copy_columns": ["x", "x"]}, "duplicate", id="duplicate-column"),
        pytest.param({"path": "a.csv", "copy_columns": ["has_sdc"]}, "owned by", id="registry-owned-column"),
        pytest.param({"path": "a.csv", "copy_columns": ["age"]}, "already writes", id="clashes-with-a-clinical-variable"),
        pytest.param(
            {"path": "a.csv", "copy_columns": ["lesion_side_source"]}, "already writes", id="clashes-with-side-provenance"
        ),
    ],
)
def test_load_config_rejects_a_malformed_sdc_metadata_block(tmp_path, block, match):
    with pytest.raises(ValueError, match=match):
        load_config(_write_sdc_join_config(tmp_path, block))


def test_load_config_rejects_a_column_written_by_both_joins(tmp_path):
    """Two joins writing one participants.csv column would leave it holding whichever ran second."""
    lesion_block = {
        "path": "l.csv", "copy_columns": ["shared_column"], "lesion_side_from": None, "geometric_override_datasets": [],
    }
    with pytest.raises(ValueError, match=r"already writes.*shared_column|shared_column.*already writes"):
        load_config(_write_sdc_join_config(tmp_path, {"path": "s.csv", "copy_columns": ["shared_column"]}, lesion_block))


def test_report_lines_dumps_sdc_metadata_as_json_and_null_when_disabled(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    coverage = [DatasetCoverage("UNIPD/WashU", 1, [], {}, {"age": 0})]
    now = datetime(2026, 10, 6, 12, 0, 0)

    with_join = "\n".join(
        report_lines(_config(tmp_path, sources, ["age"], sdc_metadata=_sdc_join(tmp_path / "sdc_metadata.csv")), coverage, now)
    )
    assert "sdc_metadata:" in with_join
    assert '"disconnection_load_voxels_1mm"' in with_join

    without = "\n".join(report_lines(_config(tmp_path, sources, ["age"]), coverage, now))
    sdc_section = without.split("sdc_metadata:")[1]
    assert sdc_section.lstrip().startswith("```json\nnull")


# --- overwrite + protected cells ------------------------------------------------------------------


def _two_subjects(tmp_path):
    """Two WashU subjects whose registry cells (age 999/888, sex X/Y) disagree with the raw tsv
    (70/55, M/F) - so a cell that changed was written, and a cell that did not was kept."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age", "sex"],
        [["sub-STUNIPD0001", "70", "M"], ["sub-STUNIPD0002", "55", "F"]],
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])
    registry["age"] = ["999", "888"]
    registry["sex"] = ["X", "Y"]
    return sources, registry


def _protected(tmp_path, columns=(), subjects=()):
    return ProtectedCells(path=tmp_path / "protected.json", columns=list(columns), subjects=list(subjects))


def test_a_protected_column_survives_an_overwrite_run(tmp_path):
    sources, registry = _two_subjects(tmp_path)
    config = _config(tmp_path, sources, ["age", "sex"], overwrite=True, protected=_protected(tmp_path, columns=["age"]))

    out, _ = enrich(registry, config)

    assert list(out["age"]) == ["999", "888"]  # protected: kept for every subject
    assert list(out["sex"]) == ["M", "F"]      # not protected: recomputed


def test_a_protected_subject_survives_an_overwrite_run_in_every_column(tmp_path):
    sources, registry = _two_subjects(tmp_path)
    config = _config(
        tmp_path, sources, ["age", "sex"], overwrite=True, protected=_protected(tmp_path, subjects=["sub-STUNIPD0001"])
    )

    out, _ = enrich(registry, config)

    assert list(out["age"]) == ["999", "55"]
    assert list(out["sex"]) == ["X", "F"]


@pytest.mark.parametrize("overwrite", [True, False])
def test_a_protected_cell_is_never_written_even_when_it_is_empty(tmp_path, overwrite):
    """"Intact" means untouched, not "protected unless empty": a protected subject's empty cell stays
    empty, in append mode too - the raw tsv has a value for it, and it must still not be written."""
    sources, registry = _two_subjects(tmp_path)
    registry["age"] = [np.nan, "888"]
    config = _config(
        tmp_path, sources, ["age"], overwrite=overwrite, protected=_protected(tmp_path, subjects=["sub-STUNIPD0001"])
    )

    out, _ = enrich(registry, config)

    assert pd.isna(out.loc[0, "age"])


def test_protection_applies_to_the_columns_copied_from_a_measurements_csv(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    registry["age"] = ["70"]
    registry["lesion_volume_voxels_2mm"] = ["999"]
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    config = _config(
        tmp_path, sources, ["age"], overwrite=True, lesion_metadata=_join(path, lesion_side_from=None),
        protected=_protected(tmp_path, columns=["lesion_volume_voxels_2mm"]),
    )

    out, _ = enrich(registry, config)

    assert out.loc[0, "lesion_volume_voxels_2mm"] == "999"


def test_a_protected_subject_that_is_not_in_participants_raises(tmp_path):
    sources, registry = _two_subjects(tmp_path)
    config = _config(tmp_path, sources, ["age"], protected=_protected(tmp_path, subjects=["sub-STUNIPD9999"]))

    with pytest.raises(ValueError, match="sub-STUNIPD9999"):
        enrich(registry, config)


def test_a_protected_column_this_config_does_not_write_raises(tmp_path):
    """A typo (or a column no run writes) would otherwise protect nothing, in silence."""
    sources, registry = _two_subjects(tmp_path)
    config = _config(tmp_path, sources, ["age"], protected=_protected(tmp_path, columns=["NIHSS"]))

    with pytest.raises(ValueError, match="not written by this config"):
        enrich(registry, config)


def test_a_protected_column_missing_from_participants_raises(tmp_path):
    sources, registry = _two_subjects(tmp_path)
    config = _config(tmp_path, sources, ["age", "sex"], protected=_protected(tmp_path, columns=["sex"]))

    with pytest.raises(ValueError, match="do not exist"):
        enrich(registry.drop(columns=["sex"]), config)


def test_protecting_lesion_side_without_its_source_raises(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "lesion_side"), [["sub-STUNIPD0001", "left"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    registry["lesion_side"] = ["left"]
    registry["lesion_side_source"] = ["clinical"]
    config = _config(tmp_path, sources, ["lesion_side"], protected=_protected(tmp_path, columns=["lesion_side"]))

    with pytest.raises(ValueError, match="must be protected together"):
        enrich(registry, config)


def test_protected_lesion_side_pair_is_kept_through_an_overwrite_run(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "lesion_side"), [["sub-STUNIPD0001", "left"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    registry["lesion_side"] = ["both"]
    registry["lesion_side_source"] = ["geometric"]  # a hand decision to keep
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "right"]])
    config = _config(
        tmp_path, sources, ["lesion_side"], overwrite=True, lesion_metadata=_join(path, copy_columns=[]),
        protected=_protected(tmp_path, columns=["lesion_side", "lesion_side_source"]),
    )

    out, _ = enrich(registry, config)

    assert out.loc[0, ["lesion_side", "lesion_side_source"]].tolist() == ["both", "geometric"]


def test_override_does_not_force_a_protected_subject(tmp_path):
    sources, registry, path = _override_fixture(tmp_path, [("sub-STUNIPD0001", "UNIPD/WashU", "left", "right")])
    registry["lesion_side"] = ["left"]
    registry["lesion_side_source"] = ["clinical"]
    config = _config(
        tmp_path, sources, ["lesion_side"], overwrite=True,
        lesion_metadata=_join(path, copy_columns=[], override_datasets=["UNIPD/WashU"]),
        protected=_protected(tmp_path, subjects=["sub-STUNIPD0001"]),
    )

    out, _ = enrich(registry, config)

    assert out.loc[0, ["lesion_side", "lesion_side_source"]].tolist() == ["left", "clinical"]


def test_override_requires_overwrite_true(tmp_path):
    """The override replaces a filled cell; append mode never does - two rules that cannot both hold."""
    sources, registry, path = _override_fixture(tmp_path, [("sub-STUNIPD0001", "UNIPD/WashU", "left", "right")])
    config = _config(
        tmp_path, sources, ["lesion_side"], overwrite=False,
        lesion_metadata=_join(path, copy_columns=[], override_datasets=["UNIPD/WashU"]),
    )

    with pytest.raises(ValueError, match="append mode never does"):
        enrich(registry, config)


def test_append_mode_keeps_an_earlier_geometric_side_and_its_source(tmp_path, caplog):
    """Where the raw tsv has no side, an earlier geometric fill must survive an append run with
    its "geometric" source - not be relabelled "clinical" because the cell happens to be non-empty."""
    sources = _one_subject_sources(tmp_path, ("participant_id", "lesion_side"), [["sub-STUNIPD0001", "n/a"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    registry["lesion_side"] = ["both"]
    registry["lesion_side_source"] = ["geometric"]
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "both"]])
    config = _config(
        tmp_path, sources, ["lesion_side"], overwrite=False, lesion_metadata=_join(path, copy_columns=[])
    )

    with caplog.at_level(logging.WARNING):
        out, _ = enrich(registry, config)

    assert out.loc[0, ["lesion_side", "lesion_side_source"]].tolist() == ["both", "geometric"]
    assert "differ" not in caplog.text


# --- load_config: overwrite and protected_path ------------------------------------------------------------


def _write_base_config(tmp_path, **changes):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    payload = {
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age"], "overwrite": True, "protected_path": None, "run_notes": "n",
    }
    payload.update(changes)
    payload = {k: v for k, v in payload.items() if v is not _ABSENT}
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps(payload))
    return config_path


_ABSENT = object()


def _write_protected(tmp_path, payload):
    path = tmp_path / "protected.json"
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload))
    return path


def test_load_config_reads_overwrite_and_a_null_protected_path(tmp_path):
    config = load_config(_write_base_config(tmp_path, overwrite=False))

    assert config.overwrite is False
    assert config.protected is None


def test_load_config_reads_the_protected_file(tmp_path):
    protected = _write_protected(tmp_path, {"columns": ["NIHSS"], "subjects": ["sub-STUNIPD0001"]})

    config = load_config(_write_base_config(tmp_path, protected_path=str(protected)))

    assert config.protected == ProtectedCells(path=protected, columns=["NIHSS"], subjects=["sub-STUNIPD0001"])


def test_load_config_accepts_an_empty_protected_file(tmp_path):
    protected = _write_protected(tmp_path, {"columns": [], "subjects": []})

    config = load_config(_write_base_config(tmp_path, protected_path=str(protected)))

    assert config.protected.columns == [] and config.protected.subjects == []


@pytest.mark.parametrize("missing", ["overwrite", "protected_path"])
def test_load_config_requires_overwrite_and_protected_path(tmp_path, missing):
    """An old config that still says "fill" has no "overwrite": it must fail, not run on a default."""
    with pytest.raises(ValueError, match=f"missing required key '{missing}'"):
        load_config(_write_base_config(tmp_path, **{missing: _ABSENT}))


def test_load_config_rejects_a_non_boolean_overwrite(tmp_path):
    with pytest.raises(ValueError, match="'overwrite' must be a boolean"):
        load_config(_write_base_config(tmp_path, overwrite="yes"))


def test_load_config_protected_path_to_a_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="protected_path"):
        load_config(_write_base_config(tmp_path, protected_path=str(tmp_path / "nope.json")))


@pytest.mark.parametrize(
    "payload, match",
    [
        pytest.param('{"columns": []', "not valid JSON", id="not-json"),
        pytest.param([], "exactly the keys", id="not-an-object"),
        pytest.param({"columns": []}, "exactly the keys", id="subjects-absent"),
        pytest.param({"columns": [], "subjects": [], "rows": []}, "exactly the keys", id="unknown-key"),
        pytest.param({"columns": "age", "subjects": []}, "list of non-empty strings", id="columns-not-a-list"),
        pytest.param({"columns": ["age", "age"], "subjects": []}, "duplicate", id="duplicate-column"),
        pytest.param({"columns": [], "subjects": ["sub-A", "sub-A"]}, "duplicate", id="duplicate-subject"),
    ],
)
def test_load_config_rejects_a_malformed_protected_file(tmp_path, payload, match):
    protected = _write_protected(tmp_path, payload)

    with pytest.raises(ValueError, match=match):
        load_config(_write_base_config(tmp_path, protected_path=str(protected)))


def test_report_lines_state_the_overwrite_mode_and_what_is_protected(tmp_path):
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    coverage = [DatasetCoverage("UNIPD/WashU", 1, [], {}, {"age": 0})]
    now = datetime(2026, 10, 7, 12, 0, 0)

    plain = "\n".join(report_lines(_config(tmp_path, sources, ["age"], overwrite=False), coverage, now))
    assert "overwrite: False" in plain and "protected: none" in plain

    guarded = _config(
        tmp_path, sources, ["age"], protected=_protected(tmp_path, columns=["age"], subjects=["sub-STUNIPD0001"])
    )
    text = "\n".join(report_lines(guarded, coverage, now))
    assert "overwrite: True" in text and "['age']" in text and "1 subject(s)" in text
