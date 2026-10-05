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
    enrich,
    load_config,
    read_lesion_metadata,
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


def _config(tmp_path, sources, variables, fill=False, lesion_metadata=None, datasets=None):
    return EnrichMetadataConfig(
        project="test",
        sources=sources,
        participants_path=tmp_path / "participants.csv",
        datasets=datasets,
        variables=variables,
        lesion_metadata=lesion_metadata,
        fill=fill,
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


def test_fill_true_preserves_existing_values(tmp_path):
    """fill=true only writes empty cells - an existing value is never overwritten."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])
    registry["age"] = ["999", np.nan]  # 999 is a hand-corrected value that must survive

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], fill=True))
    assert list(out["age"]) == ["999", "55"]


def test_fill_false_recomputes_every_value(tmp_path):
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"], [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]]
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"] for i in (1, 2)
    ])
    registry["age"] = ["999", np.nan]

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], fill=False))
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
        "variables": ["age", "not_a_variable"], "fill": False, "run_notes": "n",
    }))
    with pytest.raises(ValueError, match="unknown variable"):
        load_config(config_path)


def test_load_config_rejects_duplicate_variables(tmp_path):
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"UNIPD/WashU": {"participants_tsv": "a.tsv", "derivatives_dir": "d"}}))
    config_path = tmp_path / "c.json"
    config_path.write_text(json.dumps({
        "project": "p", "metadata_sources": str(sources_path), "participants_path": "x.csv",
        "variables": ["age", "age"], "fill": False, "run_notes": "n",
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


def test_copy_columns_overwrites_even_with_fill_true(tmp_path):
    """A mask-derived value is never hand-corrected in participants.csv (every run copies it
    over), so honouring fill=True here would silently freeze a stale number after the masks
    changed - the opposite of what the clinical columns want."""
    sources = _one_subject_sources(tmp_path, ("participant_id", "age"), [["sub-STUNIPD0001", "70"]])
    registry = _bool_registry([("sub-STUNIPD0001", "UNIPD/WashU", True)])
    registry["lesion_volume_voxels_2mm"] = ["999"]
    path = _write_measured(tmp_path, [["sub-STUNIPD0001", "UNIPD/WashU", 4, "left"]])
    config = _config(
        tmp_path, sources, ["age"], fill=True, lesion_metadata=_join(path, lesion_side_from=None)
    )

    out, _ = enrich(registry, config)

    assert out.loc[0, "lesion_volume_voxels_2mm"] == 4


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
        "variables": list(variables), "lesion_metadata": block, "fill": False, "run_notes": "n",
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
