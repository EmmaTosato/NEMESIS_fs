"""Integration test: clustering.py (no reduction) chained onto a build_lesion_matrix.py output."""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.pipeline import build_lesion_matrix, clustering

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _build_matrix(tmp_path, monkeypatch, n_subjects=12):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    rng = np.random.default_rng(4)
    for i in range(n_subjects):
        subject_id = f"sub-{i:02d}"
        subject_dir = data_root / "siteA" / subject_id / "lesion" / "manual_masks" / "anat"
        subject_dir.mkdir(parents=True, exist_ok=True)
        volume = np.zeros(_SHAPE, dtype=np.float32)
        for voxel in [tuple(rng.integers(0, 10, size=3)) for _ in range(5)]:
            volume[voxel] = 1.0
        nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")

    output_root = tmp_path / "matrix_out"
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


def test_clustering_end_to_end(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_reports")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    original_X = np.load(input_dir / "matrix.npy")

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_method": "kmeans",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "run_name": "run1",
        "overwrite": False,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    exit_code = clustering.main(["--config", str(cfg_path)])
    assert exit_code == 0

    out_dir = next((output_root / "kmeans").iterdir())
    X = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert np.array_equal(X, original_X)  # unchanged, per design (no reduction happened)
    assert list(metadata.columns) == ["subject_id", "dataset", "cluster_label"]
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
    assert (out_dir / "cluster_plot.png").stat().st_size > 0
