"""Unit tests for src/pipeline/compute_sdc_metadata.py - synthetic .nii.gz fixtures, no EBRAIN mount
needed. Full main() CLI runs, same convention as tests/unit/test_compute_lesion_metadata.py (a
pipeline whose output is a metadata file, tested through its CLI rather than only its functions).

The numerical behaviour (what is summed, the per-header realignment, the registry/disk agreement)
is pinned in tests/unit/test_features_sdc.py; this file covers what the CLI adds around it.
"""

import json
import logging

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.pipeline import compute_sdc_metadata as pipeline
from src.utils import participants as participants_registry

_SHAPE = (4, 4, 4)
_AFFINE = np.array([[1.0, 0.0, 0.0, -2.0], [0.0, 1.0, 0.0, -2.0], [0.0, 0.0, 1.0, -2.0], [0.0, 0.0, 0.0, 1.0]])
_DATASET = "UNIPD/WashU"
_REGISTRY_HEADER = "subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features"


@pytest.fixture(autouse=True)
def _isolated_registry(tmp_path, monkeypatch):
    """Every test reads its own registry, never the real assets/metadata/participants.csv."""
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", metadata_root)
    metadata_root.mkdir()
    (metadata_root / "participants.csv").write_text(_REGISTRY_HEADER + "\n")
    return metadata_root


def _register(metadata_root, subject_id, has_sdc=True):
    with (metadata_root / "participants.csv").open("a") as f:
        f.write(f"{subject_id},{subject_id},{_DATASET},ST,True,{has_sdc},False\n")


def _make_map(data_root, subject_id, voxels):
    subject_dir = data_root / _DATASET / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for index, probability in voxels.items():
        volume[index] = probability
    nib.save(
        nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
    )


def _write_config(tmp_path, data_root, output_path, overrides=None, grid_overrides=None):
    """A one-grid ("1mm") config whose brain mask keeps world x >= 0 (array index i >= 2).
    `grid_overrides` patches that grid's own fields; a "name" key renames it."""
    template = tmp_path / "template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), template)
    brain = np.zeros(_SHAPE, dtype=np.float32)
    brain[2:] = 1.0
    brain_path = tmp_path / "brain_mask.nii.gz"
    nib.save(nib.Nifti1Image(brain, _AFFINE), brain_path)
    grid = {"reference_template_path": str(template), "brain_mask_path": str(brain_path)}
    grid_overrides = dict(grid_overrides or {})
    grid_name = grid_overrides.pop("name", "1mm")
    grid.update(grid_overrides)
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "output_path": str(output_path),
        "datasets": [_DATASET],
        "group_filter": ["ST"],
        "disconnectome_glob": "sdc/*/*_res-1_desc-disconnectome.nii.gz",
        "resample_interpolation": "nearest",
        "grids": {grid_name: grid},
        "overwrite": False,
        "run_notes": "test",
    }
    cfg.update(overrides or {})
    path = tmp_path / "compute_sdc_metadata.json"
    path.write_text(json.dumps(cfg))
    return path


def _redirect_outputs(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(pipeline, "LOGS_ROOT", tmp_path / "logs")


def _two_subjects(tmp_path, metadata_root):
    data_root = tmp_path / "data"
    _make_map(data_root, "sub-STUNIPD0001", {(2, 2, 2): 0.5, (3, 2, 2): 0.25, (1, 2, 2): 0.9})  # i=1: outside brain
    _make_map(data_root, "sub-STUNIPD0002", {(2, 0, 0): 1.0})
    _register(metadata_root, "sub-STUNIPD0001")
    _register(metadata_root, "sub-STUNIPD0002")
    return data_root


def test_compute_sdc_metadata_end_to_end(tmp_path, monkeypatch, caplog, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    with caplog.at_level(logging.INFO):
        exit_code = pipeline.main(["--config", str(config_path)])

    assert exit_code == 0
    assert "run duration:" in caplog.text

    metrics = pd.read_csv(output_path)
    assert list(metrics.columns) == [
        "subject_id", "dataset", "disconnection_load_voxels_1mm", "disconnection_mean_1mm"
    ]
    by_id = metrics.set_index("subject_id")
    assert by_id.loc["sub-STUNIPD0001", "disconnection_load_voxels_1mm"] == 0.75
    assert by_id.loc["sub-STUNIPD0002", "disconnection_load_voxels_1mm"] == 1.0
    assert by_id.loc["sub-STUNIPD0001", "disconnection_mean_1mm"] == pytest.approx(0.75 / 32)

    reports = list((tmp_path / "summaries").glob("*.md"))
    logs = list((tmp_path / "logs").glob("*.log"))
    assert len(reports) == 1 and len(logs) == 1
    report = reports[0].read_text()
    assert "| UNIPD/WashU | 2 |" in report
    assert "Nessuno." in report  # group_filter excluded nobody


def test_compute_sdc_metadata_writes_its_own_config_beside_the_csv(tmp_path, monkeypatch, _isolated_registry):
    """lessons_learned.md #18/#36: a CSV whose grid/interpolation are unknown cannot be
    interpreted, and this pipeline has no per-run output directory to record them in."""
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    assert pipeline.main(["--config", str(config_path)]) == 0

    written = json.loads((tmp_path / "sdc_metadata.config.json").read_text())
    assert list(written["grids"]) == ["1mm"]
    assert written["grids"]["1mm"]["brain_mask_path"].endswith("brain_mask.nii.gz")
    assert written["resample_interpolation"] == "nearest"
    assert "written" in written


def test_compute_sdc_metadata_skips_when_output_exists_and_overwrite_false(tmp_path, monkeypatch, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    output_path.write_text("subject_id,dataset\nsub-fake,siteA\n")
    before = output_path.read_text()
    config_path = _write_config(tmp_path, data_root, output_path)

    assert pipeline.main(["--config", str(config_path)]) == 0

    assert output_path.read_text() == before  # untouched - the expensive part is never re-paid
    assert not (tmp_path / "summaries").exists()  # never even started a run


def test_compute_sdc_metadata_overwrite_replaces_the_csv(tmp_path, monkeypatch, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    output_path.write_text("subject_id,dataset\nsub-fake,siteA\n")
    config_path = _write_config(tmp_path, data_root, output_path, overrides={"overwrite": True})

    assert pipeline.main(["--config", str(config_path)]) == 0

    assert list(pd.read_csv(output_path)["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]


def test_compute_sdc_metadata_dry_run_opens_no_map_and_writes_no_csv(tmp_path, monkeypatch, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    real_load = nib.load
    loaded = []

    def counting_load(path, *args, **kwargs):
        loaded.append(str(path))
        return real_load(path, *args, **kwargs)

    monkeypatch.setattr("src.features.sdc.nib.load", counting_load)
    monkeypatch.setattr("src.features.lesion.nib.load", counting_load)
    exit_code = pipeline.main(["--config", str(config_path), "--dry-run"])

    assert exit_code == 0
    assert not output_path.exists()
    assert not (tmp_path / "sdc_metadata.config.json").exists()
    assert loaded == []  # not even the template: nothing is opened before the config is known good
    assert len(list((tmp_path / "summaries").glob("*.md"))) == 1


def test_compute_sdc_metadata_registry_and_disk_disagreeing_returns_1_not_a_traceback(
    tmp_path, monkeypatch, _isolated_registry
):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    _register(_isolated_registry, "sub-STUNIPD0003")  # flagged has_sdc, no map on disk
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_sdc_metadata_corrupt_map_returns_1_not_a_traceback(tmp_path, monkeypatch, _isolated_registry):
    """A truncated .nii.gz among the maps is a clean logged error - same handling as
    compute_lesion_metadata (nib ImageFileError)."""
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    broken = next((data_root / _DATASET / "sdc" / "sub-STUNIPD0002").glob("*.nii.gz"))
    broken.write_bytes(b"not a nifti")
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_sdc_metadata_grid_missing_brain_mask_returns_1(tmp_path, monkeypatch, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(
        tmp_path, data_root, output_path, grid_overrides={"brain_mask_path": str(tmp_path / "missing.nii.gz")}
    )

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_sdc_metadata_grid_name_unusable_as_column_suffix_returns_1(tmp_path, monkeypatch, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path, grid_overrides={"name": "1 mm"})

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_sdc_metadata_unknown_dataset_returns_1(tmp_path, monkeypatch, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path, overrides={"datasets": ["UNIPD/Typo"]})

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_sdc_metadata_two_grids_end_to_end(tmp_path, monkeypatch, _isolated_registry):
    """Both grids' columns reach the CSV, the run config and the report - the 1mm/2mm choice the
    Embedding Explorer offers for disconnection rests on this file carrying both."""
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output_path = tmp_path / "sdc_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)
    cfg = json.loads(config_path.read_text())
    cfg["grids"]["2mm"] = cfg["grids"]["1mm"]  # same files: only the naming/column plumbing is under test
    config_path.write_text(json.dumps(cfg))

    assert pipeline.main(["--config", str(config_path)]) == 0

    assert list(pd.read_csv(output_path).columns) == [
        "subject_id", "dataset",
        "disconnection_load_voxels_1mm", "disconnection_mean_1mm",
        "disconnection_load_voxels_2mm", "disconnection_mean_2mm",
    ]
    assert list(json.loads((tmp_path / "sdc_metadata.config.json").read_text())["grids"]) == ["1mm", "2mm"]
    report = next((tmp_path / "summaries").glob("*.md")).read_text()
    assert "## Distribuzione (1mm)" in report and "## Distribuzione (2mm)" in report
