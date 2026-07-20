"""Integration test: full build_lesion_matrix.py CLI run (main()) on synthetic data.

No EBRAIN mount needed - build_lesion_matrix operates on already-local files,
so this is a pure tmp_path E2E, always runs (no skipif).
"""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.pipeline import build_lesion_matrix

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _make_lesion_subject(data_root, dataset, subject_id, lesion_voxels):
    subject_dir = data_root / dataset / subject_id / "lesion" / "manual_masks" / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _make_dataset(data_root, n_subjects=5):
    rng = np.random.default_rng(1)
    for i in range(n_subjects):
        voxels = [tuple(rng.integers(0, 10, size=3)) for _ in range(5)]
        _make_lesion_subject(data_root, "siteA", f"sub-{i:02d}", voxels)


def _write_config(tmp_path, data_root, output_root, overrides=None):
    cfg = {
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
    cfg.update(overrides or {})
    path = tmp_path / "build_lesion_matrix.json"
    path.write_text(json.dumps(cfg))
    return path


def test_build_lesion_matrix_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    exit_code = build_lesion_matrix.main(["--config", str(config_path)])
    assert exit_code == 0

    output_dirs = list(output_root.iterdir())
    assert len(output_dirs) == 1
    out_dir = output_dirs[0]
    assert out_dir.name.endswith("_run1")

    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "README.md").is_file()
    matrix = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert matrix.shape[0] == 5
    assert len(metadata) == 5

    reports = list((tmp_path / "reports" / "testproj").glob("*.md"))
    logs = list((tmp_path / "logs" / "testproj").glob("*.log"))
    assert len(reports) == 1
    assert len(logs) == 1


def test_overwrite_false_rerun_fails_without_touching_existing_output(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_lesion_matrix.main(["--config", str(config_path)]) == 0
    out_dir = next(output_root.iterdir())
    manifest_before = (out_dir / "manifest.json").read_text()

    exit_code = build_lesion_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert (out_dir / "manifest.json").read_text() == manifest_before  # untouched


def test_parcellate_with_save_parcellated_volumes(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root, n_subjects=3)

    atlas = np.zeros(_SHAPE, dtype=np.int32)
    atlas[0:5, 0:5, 0:5] = 1
    atlas[5:10, 5:10, 5:10] = 2
    atlas_path = tmp_path / "atlas.nii.gz"
    nib.save(nib.Nifti1Image(atlas, _AFFINE), atlas_path)

    config_path = _write_config(
        tmp_path,
        data_root,
        output_root,
        overrides={
            "parcellate": True,
            "atlas_path": str(atlas_path),
            "parcel_aggregation": "fraction_lesioned",
            "save_parcellated_volumes": True,
        },
    )

    exit_code = build_lesion_matrix.main(["--config", str(config_path)])
    assert exit_code == 0

    out_dir = next(output_root.iterdir())
    assert (out_dir / "parcel_ids.npy").is_file()
    volumes = list((out_dir / "parcellated_volumes").glob("*.nii.gz"))
    assert len(volumes) == 3
