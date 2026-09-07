"""Unit tests for src/pipeline/enrich_metadata.py - synthetic tsv/csv fixtures, no real data."""

import json

import numpy as np
import pandas as pd
import pytest

from src.pipeline.enrich_metadata import (
    EnrichMetadataConfig,
    enrich,
    load_config,
    load_lesion_volumes,
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


def _config(tmp_path, sources, variables, fill=False, lesion_volume_from=None, datasets=None):
    return EnrichMetadataConfig(
        project="test",
        sources=sources,
        participants_path=tmp_path / "participants.csv",
        datasets=datasets,
        variables=variables,
        lesion_volume_from=lesion_volume_from,
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


def test_load_lesion_volumes_requires_the_column(tmp_path):
    """An artifact predating lesion_volume_voxels raises, naming it - the value is
    never re-derived here under a second definition."""
    artifact = tmp_path / "art"
    artifact.mkdir()
    pd.DataFrame({"subject_id": ["sub-STUNIPD0001"], "dataset": ["UNIPD/WashU"]}).to_csv(
        artifact / "metadata.csv", index=False
    )
    with pytest.raises(ValueError, match="lesion_volume_voxels"):
        load_lesion_volumes(artifact)


def test_lesion_volume_is_written_as_an_integer_not_a_float(tmp_path):
    """A voxel count must never be serialized as "4616.0": an unmatched subject
    introduces a NaN, which would promote the whole column to float64."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]],
    )
    artifact = tmp_path / "art"
    artifact.mkdir()
    pd.DataFrame({"subject_id": ["sub-STUNIPD0001"], "lesion_volume_voxels": [4616]}).to_csv(
        artifact / "metadata.csv", index=False
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2)
    ])

    out, _ = enrich(registry, _config(tmp_path, sources, ["age"], lesion_volume_from=artifact))
    path = tmp_path / "out.csv"
    out.to_csv(path, index=False)
    written = pd.read_csv(path, dtype=str)["lesion_volume_voxels"]
    assert written[0] == "4616"
    assert pd.isna(written[1])


def test_load_lesion_volumes_reads_the_artifact_column(tmp_path):
    artifact = tmp_path / "art"
    artifact.mkdir()
    pd.DataFrame(
        {"subject_id": ["sub-STUNIPD0001"], "lesion_volume_voxels": [1234]}
    ).to_csv(artifact / "metadata.csv", index=False)
    assert load_lesion_volumes(artifact) == {"sub-STUNIPD0001": 1234}


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


def test_rerun_with_lesion_volume_over_enriched_file(tmp_path):
    """Same branch, for the numeric column: a subject absent from the lesion matrix maps
    to NaN, which must survive being written back into an existing str-dtype column."""
    tsv = _write_tsv(
        tmp_path / "a.tsv", ["participant_id", "age"],
        [["sub-STUNIPD0001", "70"], ["sub-STUNIPD0002", "55"]],
    )
    artifact = tmp_path / "art"
    artifact.mkdir()
    pd.DataFrame({"subject_id": ["sub-STUNIPD0001"], "lesion_volume_voxels": [1234]}).to_csv(
        artifact / "metadata.csv", index=False
    )
    sources = {"UNIPD/WashU": DatasetSource(tsv, tmp_path)}
    registry = _registry([
        [f"sub-STUNIPD000{i}", f"sub-STUNIPD000{i}", "UNIPD/WashU", "ST", "True", "True", "False"]
        for i in (1, 2)
    ])
    config = _config(tmp_path, sources, ["age"], lesion_volume_from=artifact)

    first, _ = enrich(registry, config)
    path = tmp_path / "participants.csv"
    first.to_csv(path, index=False)
    second, _ = enrich(pd.read_csv(path, dtype=str), config)

    assert str(second.loc[0, "lesion_volume_voxels"]) == "1234"  # non "1234.0"
    assert pd.isna(second.loc[1, "lesion_volume_voxels"])
