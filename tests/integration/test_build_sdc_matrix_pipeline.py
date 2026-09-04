"""Integration test: full build_sdc_matrix.py CLI run (main()) on synthetic data.

No EBRAIN mount needed - build_sdc_matrix operates on already-local files
(SDC CSVs) plus a synthetic participants.tsv registry, so this is a pure
tmp_path E2E, always runs (no skipif).
"""

import json
import logging

import nibabel as nib
import numpy as np
import pandas as pd

from src.features import clinical
from src.pipeline import build_sdc_matrix

_ATLAS = "test_atlas"
_OBJECT = "disconnectome"
_VALUE_COLUMN = "mean_overlap"
_LESION_MASK_COLUMN = "lesion/manual_masks/anat/lesion_mask"

_VOXELWISE_AFFINE = np.eye(4) * 2
_VOXELWISE_AFFINE[3, 3] = 1
_VOXELWISE_SHAPE = (4, 4, 4)


def _register_lesion_mask(metadata_root, dataset, subject_id):
    metadata_root.mkdir(parents=True, exist_ok=True)
    path = metadata_root / f"{dataset.replace('/', '_')}_participants_lesions.tsv"
    if not path.is_file():
        path.write_text(f"participant_id\t{_LESION_MASK_COLUMN}\n")
    with path.open("a") as f:
        f.write(f"{subject_id}\tpresent\n")


def _make_sdc_csv(data_root, dataset, subject_id, rows):
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"{subject_id}_space-MNI152NLin6Asym_LF-{_OBJECT}_atlas-{_ATLAS}.csv"
    lines = [f"region_name,{_VALUE_COLUMN}"] + [f"{region},{value}" for region, value in rows.items()]
    path.write_text("\n".join(lines) + "\n")


def _make_reference_labels(path, region_names):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(["region_name"] + list(region_names)) + "\n")


def _make_dataset(data_root, metadata_root, n_subjects=5):
    rng = np.random.default_rng(1)
    for i in range(n_subjects):
        subject_id = f"sub-STUNIPD{i:04d}"
        _register_lesion_mask(metadata_root, "siteA", subject_id)
        rows = {region: round(float(rng.random()), 3) for region in ["A", "B", "C"] if rng.random() > 0.3}
        _make_sdc_csv(data_root, "siteA", subject_id, rows)


def _write_config(tmp_path, data_root, output_root, overrides=None):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B", "C"])
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "object": _OBJECT,
        "representation": "parcellated",
        "atlas": _ATLAS,
        "value_column": _VALUE_COLUMN,
        "reference_labels_path": str(reference_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
    }
    cfg.update(overrides or {})
    path = tmp_path / "build_sdc_matrix.json"
    path.write_text(json.dumps(cfg))
    return path


def _make_disconnectome_map(data_root, dataset, subject_id, volume):
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
    nib.save(nib.Nifti1Image(volume.astype(np.float32), _VOXELWISE_AFFINE), path)


def _write_voxelwise_config(tmp_path, data_root, output_root, overrides=None):
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_VOXELWISE_SHAPE, dtype=np.float32), _VOXELWISE_AFFINE), template_path)
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "object": _OBJECT,
        "representation": "voxelwise",
        "reference_template_path": str(template_path),
        "resample_interpolation": "nearest",
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
    }
    cfg.update(overrides or {})
    path = tmp_path / "build_sdc_matrix.json"
    path.write_text(json.dumps(cfg))
    return path


def test_build_sdc_matrix_end_to_end(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root, metadata_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    with caplog.at_level(logging.INFO):
        exit_code = build_sdc_matrix.main(["--config", str(config_path)])
    assert exit_code == 0
    assert "run duration:" in caplog.text

    run_dirs = [p for p in output_root.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    out_dir = run_dirs[0]
    assert out_dir.name.endswith("_run1")

    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "config.md").is_file()
    matrix = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    region_names = np.load(out_dir / "region_names.npy", allow_pickle=True)

    assert matrix.shape == (5, 3)  # 5 subjects, 3 reference regions - no drop, ever
    assert len(metadata) == 5
    assert list(region_names) == ["A", "B", "C"]

    reports = list((tmp_path / "summaries" / "testproj").glob("*.md"))
    logs = list((tmp_path / "logs" / "testproj").glob("*.log"))
    assert len(reports) == 1
    assert len(logs) == 1

    runs_csv = (output_root / "runs.csv").read_text()
    assert "run1" in runs_csv


def test_build_sdc_matrix_excluded_subjects_recorded_in_config_md(tmp_path, monkeypatch):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _register_lesion_mask(metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(data_root, "siteA", "sub-STUNIPD0001", {"A": 0.5})
    # sub-STUNIPD0002 has SDC output but is never registered with a lesion mask
    _make_sdc_csv(data_root, "siteA", "sub-STUNIPD0002", {"A": 0.9})
    # sub-STUNIPD0003 is registered with a lesion mask but has no SDC output yet
    _register_lesion_mask(metadata_root, "siteA", "sub-STUNIPD0003")

    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_sdc_matrix.main(["--config", str(config_path)]) == 0

    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]

    config_md = (out_dir / "config.md").read_text()
    assert "sub-STUNIPD0002" in config_md
    assert "Excluded (SDC output present but no lesion mask)" in config_md
    assert "sub-STUNIPD0003" in config_md
    assert "Have a lesion mask but no SDC output yet" in config_md


def test_build_sdc_matrix_config_md_has_params_used_line(tmp_path, monkeypatch):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root, metadata_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_sdc_matrix.main(["--config", str(config_path)]) == 0

    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    config_md = (out_dir / "config.md").read_text()
    expected = f'Params used: {{"object": "{_OBJECT}", "atlas": "{_ATLAS}", "value_column": "{_VALUE_COLUMN}"}}'
    assert expected in config_md


def test_invalid_config_returns_1_not_raw_traceback(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root, metadata_root)
    config_path = _write_config(tmp_path, data_root, output_root, overrides={"object": "not_a_real_object"})

    with caplog.at_level(logging.INFO):
        exit_code = build_sdc_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert not output_root.exists()


def test_overwrite_false_rerun_fails_without_touching_existing_output(tmp_path, monkeypatch):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root, metadata_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_sdc_matrix.main(["--config", str(config_path)]) == 0
    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    manifest_before = (out_dir / "manifest.json").read_text()

    exit_code = build_sdc_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert (out_dir / "manifest.json").read_text() == manifest_before


def test_build_sdc_matrix_voxelwise_end_to_end(tmp_path, monkeypatch, caplog):
    """representation='voxelwise' (added 03/09): same CLI, disconnectome-map
    .nii.gz directly instead of the per-atlas CSVs - extra_arrays holds
    non_constant_mask, not region_names (no atlas involved)."""
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    for i, value in enumerate([0.5, 0.2, 0.0]):
        subject_id = f"sub-STUNIPD{i:04d}"
        _register_lesion_mask(metadata_root, "siteA", subject_id)
        volume = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
        volume[0, 0, 0] = value
        _make_disconnectome_map(data_root, "siteA", subject_id, volume)
    config_path = _write_voxelwise_config(tmp_path, data_root, output_root)

    with caplog.at_level(logging.INFO):
        exit_code = build_sdc_matrix.main(["--config", str(config_path)])
    assert exit_code == 0
    assert "run duration:" in caplog.text

    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    matrix = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    non_constant_mask = np.load(out_dir / "non_constant_mask.npy")

    assert len(metadata) == 3
    assert not (out_dir / "region_names.npy").exists()
    # only voxel [0,0,0] varies (0.5/0.2/0.0) across the 3 subjects - every other voxel is
    # constant at 0.0 and gets dropped.
    assert matrix.shape == (3, 1)
    assert non_constant_mask.sum() == 1

    config_md = (out_dir / "config.md").read_text()
    assert '"representation": "voxelwise"' in config_md
    assert "3 subjects x 1 voxels" in config_md


def test_build_sdc_matrix_voxelwise_object_lesion_rejected_at_config_load(tmp_path, monkeypatch, caplog):
    """representation='voxelwise' only supports object='disconnectome' - see
    src/features/sdc.py module docstring. Caught at config-load time (fails
    before any file discovery), not deep inside build_sdc_voxelwise_matrix."""
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    config_path = _write_voxelwise_config(tmp_path, data_root, output_root, overrides={"object": "lesion"})

    with caplog.at_level(logging.INFO):
        exit_code = build_sdc_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert "voxelwise" in caplog.text
    assert not output_root.exists()
