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
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "matrix_out"
    _make_dataset(data_root)
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), template_path)

    build_cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "reference_template_path": str(template_path),
        "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "parcellate": False,
        "atlas_path": None,
        "parcel_aggregation": None,
        "save_parcellated_volumes": False,
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    build_cfg_path = tmp_path / "build.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0

    return next(p for p in output_root.iterdir() if p.is_dir())


def _write_params(tmp_path):
    params_path = tmp_path / "params_reduction.json"
    params_path.write_text(
        json.dumps(
            {
                "pca": {
                    "params": {"n_components": 2},
                    "tuning_grid": {"n_components": [1, 2, 3]},
                },
                "umap": {
                    "params": {"n_neighbors": 3, "min_dist": 0.1, "n_components": 2, "random_state": 0},
                    "tuning_grid": {"n_neighbors": [2, 3], "min_dist": [0.1, 0.5]},
                    "trustworthiness_n_neighbors": 2,
                },
                "pca_varimax": {
                    "params": {"n_components": 2, "rotation_max_iter": 500},
                    "tuning_grid": {"n_components": [2, 3, 4]},
                },
                "pacmap": {
                    "params": {"n_components": 2, "n_neighbors": 3, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0},
                    "tuning_grid": {"n_neighbors": [2, 3]},
                    "trustworthiness_n_neighbors": 2,
                },
            }
        )
    )
    return params_path


def test_dim_reduction_end_to_end_chained(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_summaries")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "regress_out_volume": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    out_dir = next(p for p in (output_root / "pca").iterdir() if p.is_dir())
    embedding = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert embedding.shape == (8, 2)
    assert list(metadata.columns) == ["subject_id", "dataset"]  # unchanged, per design
    assert len(metadata) == 8

    runs_csv = (output_root / "pca" / "runs.csv").read_text()
    assert "run1" in runs_csv
    assert "production" in runs_csv


def test_dim_reduction_fine_tuning_umap_writes_sweep_not_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_summaries")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "regress_out_volume": False,
        "run_notes": "prova sweep",
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next((output_root / "umap" / "tuning").iterdir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    assert not (tuning_dir / "matrix.npy").exists()  # a sweep is not a matrix artifact

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results.columns) == ["n_neighbors", "min_dist", "trustworthiness"]
    assert len(results) == 4  # 2 x 2 grid

    runs_csv = (output_root / "umap" / "runs.csv").read_text()
    assert "tune1" in runs_csv
    assert "tuning" in runs_csv
    assert "prova sweep" in runs_csv


def test_dim_reduction_fine_tuning_pca_varimax_writes_sweep_not_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_summaries")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca_varimax",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "regress_out_volume": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next((output_root / "pca_varimax" / "tuning").iterdir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert not (tuning_dir / "matrix.npy").exists()

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results.columns) == ["n_components", "cumulative_explained_variance"]
    assert len(results) == 3  # 3-value grid


def test_dim_reduction_fine_tuning_pacmap_writes_sweep_not_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_summaries")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pacmap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "regress_out_volume": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next((output_root / "pacmap" / "tuning").iterdir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert not (tuning_dir / "matrix.npy").exists()

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results.columns) == ["n_neighbors", "trustworthiness"]
    assert len(results) == 2  # 2-value grid


def _make_varying_volume_dataset(data_root, n_subjects=8):
    """Unlike _make_dataset (fixed 5-voxel draws, which can coincidentally
    tie every subject's lesion volume at the same count), each subject here
    gets a strictly increasing, non-overlapping voxel count - guarantees the
    lesion-volume covariate actually varies, which regress_out_covariate
    requires (zero-variance covariate raises, see test_covariates.py).
    """
    rng = np.random.default_rng(42)
    for i in range(n_subjects):
        subject_id = f"sub-{i:02d}"
        subject_dir = data_root / "siteA" / subject_id / "lesion" / "manual_masks" / "anat"
        subject_dir.mkdir(parents=True, exist_ok=True)
        n_voxels = 3 + i
        flat = np.zeros(np.prod(_SHAPE), dtype=np.float32)
        flat[rng.choice(flat.shape[0], size=n_voxels, replace=False)] = 1.0
        nib.save(nib.Nifti1Image(flat.reshape(_SHAPE), _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _build_matrix_varying_volume(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "matrix_out"
    _make_varying_volume_dataset(data_root)
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), template_path)

    build_cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "reference_template_path": str(template_path),
        "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "parcellate": False,
        "atlas_path": None,
        "parcel_aggregation": None,
        "save_parcellated_volumes": False,
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    build_cfg_path = tmp_path / "build_varying.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0

    return next(p for p in output_root.iterdir() if p.is_dir())


def test_dim_reduction_regress_out_volume_changes_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix_varying_volume(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_summaries")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"

    def _run(regress_out_volume: bool, session_name: str) -> np.ndarray:
        dr_cfg = {
            "project": "testproj",
            "input_path": str(input_dir),
            "reduction_method": "pca",
            "params_file": str(params_path),
            "output_root": str(output_root),
            "session_name": session_name,
            "overwrite": False,
            "fine_tuning": False,
            "regress_out_volume": regress_out_volume,
            "run_notes": None,
        }
        cfg_path = tmp_path / f"dim_reduction_{session_name}.json"
        cfg_path.write_text(json.dumps(dr_cfg))
        assert dim_reduction.main(["--config", str(cfg_path)]) == 0
        out_dir = next(p for p in (output_root / "pca").iterdir() if session_name in p.name)
        return np.load(out_dir / "matrix.npy")

    embedding_plain = _run(False, "plain")
    embedding_regressed = _run(True, "regressed")

    assert embedding_plain.shape == embedding_regressed.shape
    assert not np.array_equal(embedding_plain, embedding_regressed)


def test_dim_reduction_regress_out_volume_incompatible_with_jaccard_raises(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_summaries")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = tmp_path / "params_reduction.json"
    params_path.write_text(
        json.dumps(
            {
                "umap": {
                    "params": {
                        "n_neighbors": 3,
                        "min_dist": 0.1,
                        "n_components": 2,
                        "random_state": 0,
                        "metric": "jaccard",
                    }
                }
            }
        )
    )
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(tmp_path / "dr_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "regress_out_volume": True,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    assert dim_reduction.main(["--config", str(dr_cfg_path)]) == 1


def test_dim_reduction_missing_input_path_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(dim_reduction, "REPORTS_ROOT", tmp_path / "dr_summaries")
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    dr_cfg = {
        "project": "testproj",
        "input_path": str(tmp_path / "does_not_exist"),
        "reduction_method": "pca",
        "params_file": str(params_path),
        "output_root": str(tmp_path / "dr_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "regress_out_volume": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    assert dim_reduction.main(["--config", str(dr_cfg_path)]) == 1
