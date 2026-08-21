"""Integration test: full enrich_lesion_metadata.py CLI run (main()) on synthetic data.

Pure tmp_path E2E, no EBRAIN mount needed - operates only on an already-local metadata.csv
(subject_id/dataset columns), local participants.tsv files, and, for compute_volume=true, an
already-local matrix.npy sitting next to metadata.csv.
"""

import json

import numpy as np
import pandas as pd

from src.features import clinical
from src.pipeline import enrich_lesion_metadata


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


def _write_config(tmp_path, metadata_path, output_root, variables, compute_volume=False, overwrite=False):
    cfg = {
        "project": "testproj",
        "metadata_path": str(metadata_path),
        "compute_volume": compute_volume,
        "variables": variables,
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": overwrite,
        "run_notes": None,
    }
    cfg_path = tmp_path / "enrich.json"
    cfg_path.write_text(json.dumps(cfg))
    return cfg_path


def test_enrich_lesion_metadata_end_to_end(tmp_path, monkeypatch):
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
    output_root = tmp_path / "clinical_metadata"
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, output_root, ["age", "sex"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    out_dir = next(output_root.glob("*_run1"))
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
    assert (output_root / "runs.csv").exists()


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
    output_root = tmp_path / "clinical_metadata"
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, output_root, ["age"], compute_volume=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    out_dir = next(output_root.glob("*_run1"))
    metadata_out = pd.read_csv(out_dir / "metadata.csv").set_index("subject_id")
    assert metadata_out.loc["sub-1", "lesion_volume_voxels"] == 2
    assert metadata_out.loc["sub-2", "lesion_volume_voxels"] == 1


def test_enrich_lesion_metadata_compute_volume_missing_matrix_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path / "assets_metadata")
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 1}])
    # no matrix.npy written next to metadata_path
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, tmp_path / "clinical_metadata", ["age"], compute_volume=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1


def test_enrich_lesion_metadata_compute_volume_parcellated_matrix_raises(tmp_path, monkeypatch):
    """A continuous (non-binary) matrix - what build_lesion_matrix.py produces with
    parcellate=true - must raise, never silently sum fractions as if they were voxel counts."""
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
    cfg_path = _write_config(tmp_path, metadata_path, tmp_path / "clinical_metadata", ["age"], compute_volume=True)

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1


def test_enrich_lesion_metadata_dry_run_writes_nothing(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    _make_participants_tsv(metadata_root, "siteA", [{"participant_id": "sub-1", "age": "70"}])
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10}])
    output_root = tmp_path / "clinical_metadata"
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, output_root, ["age"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path), "--dry-run"])

    assert rc == 0
    assert not output_root.exists()


def test_enrich_lesion_metadata_missing_dataset_tsv_fails_without_writing(tmp_path, monkeypatch):
    metadata_root = tmp_path / "assets_metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    metadata_root.mkdir()  # exists, but no tsv for "siteA" inside it
    metadata_path = _write_metadata_csv(tmp_path, [{"subject_id": "sub-1", "dataset": "siteA", "lesion_volume_voxels": 10}])
    output_root = tmp_path / "clinical_metadata"
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, output_root, ["age"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1
    assert not output_root.exists()
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
    output_root = tmp_path / "clinical_metadata"
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, output_root, ["age", "lesion_side"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    out_dir = next(output_root.glob("*_run1"))
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
    output_root = tmp_path / "clinical_metadata"
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, output_root, ["lesion_side", "NIHSS"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 0
    out_dir = next(output_root.glob("*_run1"))
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
    output_root = tmp_path / "clinical_metadata"
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, metadata_path, output_root, ["age"], overwrite=False)

    assert enrich_lesion_metadata.main(["--config", str(cfg_path)]) == 0
    assert enrich_lesion_metadata.main(["--config", str(cfg_path)]) == 1  # same session_name, same day


def test_enrich_lesion_metadata_rejects_missing_metadata_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = _write_config(tmp_path, tmp_path / "does_not_exist.csv", tmp_path / "clinical_metadata", ["age"])

    rc = enrich_lesion_metadata.main(["--config", str(cfg_path)])

    assert rc == 1
