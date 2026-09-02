"""Integration test: full enrich_lesion_metadata.py CLI run (main()) on synthetic data.

Pure tmp_path E2E, no EBRAIN mount needed - operates only on an already-local metadata.csv
(subject_id/dataset columns), local participants.tsv files, and, for compute_volume=true, an
already-local matrix.npy sitting next to metadata.csv.
"""

import json
import logging

import numpy as np
import pandas as pd

from src.features import clinical
from src.pipeline import enrich_lesion_metadata

# RUNS_LOG_ROOT is a fixed, non-configurable relative path (data/derived/enrich_lesion_metadata)
# - every test below monkeypatch.chdir(tmp_path), so it always resolves under tmp_path without
# needing its own monkeypatch.setattr (same trick REPORTS_ROOT/LOGS_ROOT already rely on).
_RUNS_LOG_DIR_NAME = "data/derived/enrich_lesion_metadata"


def _write_metadata_csv(tmp_path, subject_rows):
    metadata_path = tmp_path / "metadata.csv"
    pd.DataFrame(subject_rows).to_csv(metadata_path, index=False)
    return metadata_path


def _write_matrix_npy(metadata_path, X):
    np.save(metadata_path.parent / "matrix.npy", X)


def _make_participants_tsv(metadata_root, dataset, rows):
    metadata_root.mkdir(parents=True, exist_ok=True)
    path = metadata_root / f"{dataset.replace('/', '_')}_participants_lesions.tsv"
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False)
    return path


def _write_config(tmp_path, metadata_path, variables, compute_volume=False, overwrite=False, write_in_place=False, copy_output_path=None):
    # copy_output_path is required exactly when write_in_place is False - default it to a
    # fixed, explicit tmp_path location so existing callers don't all need to name one by hand
    # (real config authors always do, per code_standards.md §0).
    if not write_in_place and copy_output_path is None:
        copy_output_path = tmp_path / "copy_run1"
    cfg = {
        "project": "testproj",
        "metadata_path": str(metadata_path),
        "compute_volume": compute_volume,
        "variables": variables,
        "copy_output_path": str(copy_output_path) if copy_output_path is not None else None,
        "session_name": "run1",
        "overwrite": overwrite,
        "write_in_place": write_in_place,
        "run_notes": None,
    }
    cfg_path = tmp_path / "enrich.json"
    cfg_path.write_text(json.dumps(cfg))
    return cfg_path


def test_enrich_lesion_metadata_end_to_end(tmp_path, monkeypatch, caplog):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(
        metadata_root, "siteA",
        [{"participant_id": "sub-1", "age": "70", "sex": "F"}, {"participant_id": "sub-2", "age": "n/a", "sex": "M"}],
    )
    metadata_path = _write_metadata_csv(
        tmp_path,
        [
            {"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10},
            {"subject_id": "sub-2", "dataset": "siteA", "lesion_volume_voxels": 20},
        ],
    )
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age", "sex"])

    with caplog.at_level(logging.INFO):
        rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    # docs/debugging/debug_25_08_26.md: a run's duration must be logged, success or not.
    assert "run duration:" in caplog.text
    out_dir = tmp_path / "copy_run1"
    metadata_out = pd.read_csv(out_dir / "metadata.csv")
    assert list(metadata_out.columns) == ["subject_id", "dataset", "lesion_volume_voxels", "age", "sex"]
    assert metadata_out["age"].tolist()[0] == 70
    assert pd.isna(metadata_out["age"].tolist()[1])
    # metadata_path itself is untouched - the whole point of the input/output split
    original = pd.read_csv(metadata_path)
    assert list(original.columns) == ["subject_id", "dataset", "lesion_volume_voxels"]
    assert (out_dir / "config.md").exists()
    assert (out_dir / "manifest.json").exists()
    assert list((tmp_path / "summaries" / "enrich_lesion_metadata").glob("*.md"))
    assert list((tmp_path / "logs" / "enrich_lesion_metadata").glob("*.log"))
    assert (tmp_path / _RUNS_LOG_DIR_NAME / "runs.csv").exists()


def test_enrich_lesion_metadata_compute_volume_sums_matrix_next_to_metadata(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}, {"participant_id": "sub-2", "age": "65"}])
    # Stale/wrong lesion_volume_voxels in metadata.csv, on purpose - compute_volume=true must
    # overwrite it with the real value summed from matrix.npy, not just leave it.
    metadata_path = _write_metadata_csv(
        tmp_path,
        [
            {"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 999},
            {"subject_id": "sub-2", "dataset": "siteA", "lesion_volume_voxels": 999},
        ],
    )
    _write_matrix_npy(metadata_path, np.array([[1, 1, 0, 0], [1, 0, 0, 0]], dtype=np.uint8))
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], compute_volume=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    out_dir = tmp_path / "copy_run1"
    metadata_out = pd.read_csv(out_dir / "metadata.csv").set_index("subject_id")
    assert metadata_out.loc["sub-1", "lesion_volume_voxels"] == 2
    assert metadata_out.loc["sub-2", "lesion_volume_voxels"] == 1


def test_enrich_lesion_metadata_compute_volume_missing_matrix_raises(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path / "assets_metadata")
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 1}])
    # no matrix.npy written next to metadata_path
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], compute_volume=True)

    with caplog.at_level(logging.INFO):
        rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1
    # Duration must be logged on the error path too, not just on success.
    assert "run duration:" in caplog.text


def test_enrich_lesion_metadata_compute_volume_parcellated_matrix_raises(tmp_path, monkeypatch):
    """A continuous (non-binary) matrix - e.g. an atlas-based fractional-damage summary, or
    any other non-voxel-wise source - must raise, never silently sum fractions as if they
    were voxel counts."""
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path / "assets_metadata")
    metadata_path = _write_metadata_csv(
        tmp_path,
        [
            {"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 1},
            {"subject_id": "sub-2", "dataset": "siteA", "lesion_volume_voxels": 1},
        ],
    )
    _write_matrix_npy(metadata_path, np.array([[0.3, 0.8], [1.0, 0.5]]))
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], compute_volume=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1


def test_enrich_lesion_metadata_dry_run_writes_nothing(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10}])
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path), "--dry-run"])

    assert rc == 0
    assert not (tmp_path / "copy_run1").exists()
    assert not (tmp_path / _RUNS_LOG_DIR_NAME).exists()


def test_enrich_lesion_metadata_missing_dataset_tsv_fails_without_writing(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    metadata_root.mkdir()  # exists, but no tsv for "siteA" inside it
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10}])
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1
    assert not (tmp_path / "copy_run1").exists()
    report_files = list((tmp_path / "summaries" / "enrich_lesion_metadata").glob("*.md"))
    assert report_files
    assert "FAILED" in report_files[0].read_text()


def test_enrich_lesion_metadata_missing_variable_for_one_dataset_still_succeeds(tmp_path, monkeypatch):
    """A structural gap uses each variable's own established missing-value convention -
    'unknown' for lesion_side, never NaN (see test below for why that distinction is load-
    bearing, not cosmetic)."""
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10}])
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age", "lesion_side"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    out_dir = tmp_path / "copy_run1"
    metadata_out = pd.read_csv(out_dir / "metadata.csv")
    assert metadata_out["age"].tolist() == [70]
    assert metadata_out["lesion_side"].tolist() == ["unknown"]


def test_enrich_lesion_metadata_matches_existing_dim_reduction_metadata_convention(tmp_path, monkeypatch):
    """Regression (2026-08-17, on request): lesion_side/NIHSS must land in the output with
    the exact same column name and missing-value convention every existing
    results/lesion/dim_reduction/**/metadata.csv already uses (subject_id,dataset,
    lesion_volume_voxels,lesion_side,nihss - lesion_side="unknown"/"left"/"right", nihss
    numeric+NaN) - not whatever the generic joiner or the raw tsv column casing would produce
    on their own (tsv column is "NIHSS", uppercase; generic-joined lesion_side would be NaN
    for a structural gap instead of "unknown")."""
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(
        metadata_root, "siteA",
        [
            {"participant_id": "sub-1", "lesion_side": "left", "NIHSS": "12"},
            {"participant_id": "sub-2", "lesion_side": "n/a", "NIHSS": "n/a"},
        ],
    )
    metadata_path = _write_metadata_csv(
        tmp_path,
        [
            {"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10},
            {"subject_id": "sub-2", "dataset": "siteA", "lesion_volume_voxels": 20},
        ],
    )
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["lesion_side", "NIHSS"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    out_dir = tmp_path / "copy_run1"
    metadata_out = pd.read_csv(out_dir / "metadata.csv")
    assert list(metadata_out.columns) == ["subject_id", "dataset", "lesion_volume_voxels", "lesion_side", "nihss"]
    assert metadata_out["lesion_side"].tolist() == ["left", "unknown"]
    assert metadata_out["nihss"].tolist()[0] == 12.0
    assert pd.isna(metadata_out["nihss"].tolist()[1])


def test_enrich_lesion_metadata_second_run_without_overwrite_fails(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10}])
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], overwrite=False)

    assert enrich_lesion_metadata.main(["--config", str(cfg_path)]) == 0
    assert enrich_lesion_metadata.main(["--config", str(cfg_path)]) == 1  # same copy_output_path both times


def test_enrich_lesion_metadata_rejects_missing_metadata_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, tmp_path / "does_not_exist.csv", ["age"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1


def _write_full_matrix_artifact(tmp_path, subject_rows, X):
    """A minimal but complete matrix artifact (metadata.csv + matrix.npy + manifest.json +
    config.md) - the shape write_in_place=true requires metadata_path to sit inside."""
    artifact_dir = tmp_path / "matrix_artifact"
    artifact_dir.mkdir()
    metadata_path = artifact_dir / "metadata.csv"
    pd.DataFrame(subject_rows).to_csv(metadata_path, index=False)
    np.save(artifact_dir / "matrix.npy", X)
    (artifact_dir / "manifest.json").write_text(
        json.dumps({"created_at": "2026-01-01T00:00:00+00:00", "matrix_shape": list(X.shape), "metadata_columns": list(subject_rows[0].keys())})
    )
    (artifact_dir / "config.md").write_text("# original build\n\nsome pre-existing content.\n")
    return metadata_path


def test_enrich_lesion_metadata_write_in_place_updates_matrix_artifact_directory(tmp_path, monkeypatch):
    """Regression (2026-08-28): write_in_place=true writes the enriched columns back into
    metadata_path's own directory - matrix.npy/config.md's original content untouched,
    manifest.json's metadata_columns refreshed and an enrichment_history entry appended."""
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}, {"participant_id": "sub-2", "age": "65"}])
    X = np.array([[0.1, 0.2], [0.3, 0.4]])
    metadata_path = _write_full_matrix_artifact(
        tmp_path, [{"subject_id": "sub-1", "dataset": "siteA"}, {"subject_id": "sub-2", "dataset": "siteA"}], X
    )
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], write_in_place=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    artifact_dir = metadata_path.parent
    metadata_out = pd.read_csv(artifact_dir / "metadata.csv")
    assert list(metadata_out.columns) == ["subject_id", "dataset", "age"]
    assert metadata_out["age"].tolist() == [70, 65]
    # matrix.npy untouched
    np.testing.assert_array_equal(np.load(artifact_dir / "matrix.npy"), X)
    manifest = json.loads((artifact_dir / "manifest.json").read_text())
    assert manifest["metadata_columns"] == ["subject_id", "dataset", "age"]
    assert manifest["enrichment_history"][0]["variables"] == ["age"]
    # config.md kept its original content, with the new section appended, not replaced
    config_md = (artifact_dir / "config.md").read_text()
    assert "some pre-existing content." in config_md
    assert "## Enrichment" in config_md
    # this run's only real output was the matrix artifact itself - RUNS_LOG_ROOT gets nothing
    # but the run log entry, no per-run artifact directory of its own (2026-09-02: there is no
    # more output_root-driven standalone location at all, in either write_in_place branch)
    assert (tmp_path / _RUNS_LOG_DIR_NAME / "runs.csv").is_file()


def test_enrich_lesion_metadata_write_in_place_row_mismatch_raises(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    # matrix.npy has 2 rows, metadata.csv only 1 - a corrupt/mismatched artifact
    X = np.array([[0.1], [0.2]])
    metadata_path = _write_full_matrix_artifact(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA"}], X)
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], write_in_place=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1


def test_enrich_lesion_metadata_write_in_place_requires_a_full_matrix_artifact(tmp_path, monkeypatch):
    """write_in_place=true against a bare metadata.csv (no matrix.npy/manifest.json next to
    it, e.g. the output of a previous non-in-place enrichment run) must raise, not silently
    do nothing or crash with a confusing error."""
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA"}])
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], write_in_place=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1


def test_enrich_lesion_metadata_write_in_place_existing_column_without_overwrite_fails(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    X = np.array([[0.1]])
    metadata_path = _write_full_matrix_artifact(
        tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "age": 999}], X  # "age" already present
    )
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], write_in_place=True, overwrite=False)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1
    # untouched on rejection
    assert pd.read_csv(metadata_path)["age"].tolist() == [999]


def test_enrich_lesion_metadata_write_in_place_re_requesting_same_variables_does_not_duplicate_columns(tmp_path, monkeypatch):
    """Regression (2026-09-02): re-running enrichment on an already-enriched artifact with the
    SAME variable names (a refresh, e.g. after fixing a stale upstream tsv) used to duplicate
    every re-requested column (metadata.columns already had 'age', 'variables' asked for 'age'
    again -> two 'age' columns in the output) - every prior write_in_place run in this repo's
    history happened to request a disjoint variable set each time, so this branch was never
    exercised until a real refresh run hit it."""
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}, {"participant_id": "sub-2", "age": "65"}])
    X = np.array([[0.1, 0.2], [0.3, 0.4]])
    metadata_path = _write_full_matrix_artifact(
        tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "age": 999}, {"subject_id": "sub-2", "dataset": "siteA", "age": 999}], X
    )
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], write_in_place=True, overwrite=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    metadata_out = pd.read_csv(metadata_path)
    assert list(metadata_out.columns) == ["subject_id", "dataset", "age"]
    assert metadata_out["age"].tolist() == [70, 65]


def test_enrich_lesion_metadata_write_in_place_re_requesting_nihss_does_not_duplicate_columns(tmp_path, monkeypatch):
    """Regression (2026-09-02): NIHSS is requested uppercase but stored lowercase ("nihss") -
    re-requesting it on an already-enriched artifact used to produce TWO "nihss" columns even
    after the generic same-name fix above, because the case-only rename collided with the
    still-present stale lowercase column instead of overwriting it (see _join_variables'
    docstring, point 2)."""
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "NIHSS": "12"}, {"participant_id": "sub-2", "NIHSS": "4"}])
    X = np.array([[0.1, 0.2], [0.3, 0.4]])
    metadata_path = _write_full_matrix_artifact(
        tmp_path,
        [
            {"subject_id": "sub-1", "dataset": "siteA", "nihss": 999.0},
            {"subject_id": "sub-2", "dataset": "siteA", "nihss": 999.0},
        ],
        X,
    )
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["NIHSS"], write_in_place=True, overwrite=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    metadata_out = pd.read_csv(metadata_path)
    assert list(metadata_out.columns) == ["subject_id", "dataset", "nihss"]
    assert metadata_out["nihss"].tolist() == [12.0, 4.0]


def test_enrich_lesion_metadata_write_in_place_existing_column_with_overwrite_replaces_it(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    X = np.array([[0.1]])
    metadata_path = _write_full_matrix_artifact(
        tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "age": 999}], X
    )
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, ["age"], write_in_place=True, overwrite=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    assert pd.read_csv(metadata_path)["age"].tolist() == [70]
