"""Integration test: dim_reduction.py chained onto a build_lesion_matrix.py output, on synthetic data."""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.pipeline import build_lesion_matrix, dim_reduction

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _make_dataset(data_root, n_subjects=8):
    rng = np.random.default_rng(2)
    for i in range(n_subjects):
        subject_id = f"sub-{i:02d}"
        subject_dir = data_root / "siteA" / subject_id / "lesion" / "manual_masks" / "anat"
        subject_dir.mkdir(parents=True, exist_ok=True)
        volume = np.zeros(_SHAPE, dtype=np.float32)
        for voxel in [tuple(rng.integers(0, 10, size=3)) for _ in range(5)]:
            volume[voxel] = 1.0
        nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _build_matrix(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "matrix_out"
    _make_dataset(data_root)

    build_cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "reference_dataset": "siteA",
        "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "parcellate": False,
        "atlas_path": None,
        "parcel_aggregation": None,
        "save_parcellated_volumes": False,
        "output_root": str(output_root),
        "run_name": "run1",
        "overwrite": False,
    }
    build_cfg_path = tmp_path / "build.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0

    return next(output_root.iterdir())


def _write_params(tmp_path):
    params_path = tmp_path / "params_reduction.json"
    params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    return params_path


def test_dim_reduction_end_to_end_chained(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_reports")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "run_name": "run1",
        "overwrite": False,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    out_dir = next((output_root / "pca").iterdir())
    embedding = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert embedding.shape == (8, 2)
    assert list(metadata.columns) == ["subject_id", "dataset"]  # unchanged, per design
    assert len(metadata) == 8


def test_dim_reduction_missing_input_path_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_reports")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    dr_cfg = {
        "project": "testproj",
        "input_path": str(tmp_path / "does_not_exist"),
        "reduction_method": "pca",
        "params_file": str(params_path),
        "output_root": str(tmp_path / "dr_out"),
        "run_name": "run1",
        "overwrite": False,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    assert dim_reduction.main(["--config", str(dr_cfg_path)]) == 1
