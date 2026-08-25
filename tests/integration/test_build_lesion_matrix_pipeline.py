"""Integration test: full build_lesion_matrix.py CLI run (main()) on synthetic data.

No EBRAIN mount needed - build_lesion_matrix operates on already-local files,
so this is a pure tmp_path E2E, always runs (no skipif).
"""

import json
import logging

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
        _make_lesion_subject(data_root, "siteA", f"sub-STUNIPD{i:04d}", voxels)


def _make_reference_template(path):
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), path)


def _write_config(tmp_path, data_root, output_root, overrides=None):
    template_path = tmp_path / "reference_template.nii.gz"
    _make_reference_template(template_path)
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "reference_template_path": str(template_path),
        "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
    }
    cfg.update(overrides or {})
    path = tmp_path / "build_lesion_matrix.json"
    path.write_text(json.dumps(cfg))
    return path


def test_build_lesion_matrix_end_to_end(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    with caplog.at_level(logging.INFO):
        exit_code = build_lesion_matrix.main(["--config", str(config_path)])
    assert exit_code == 0
    # docs/debugging/debug_25_08_26.md: a run's duration must be logged, success or not.
    assert "run duration:" in caplog.text

    run_dirs = [p for p in output_root.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    out_dir = run_dirs[0]
    assert out_dir.name.endswith("_run1")

    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "config.md").is_file()
    matrix = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert matrix.shape[0] == 5
    assert len(metadata) == 5

    reports = list((tmp_path / "summaries" / "testproj").glob("*.md"))
    logs = list((tmp_path / "logs" / "testproj").glob("*.log"))
    assert len(reports) == 1
    assert len(logs) == 1

    runs_csv = (output_root / "runs.csv").read_text()
    assert "run1" in runs_csv
    assert not (output_root / "runs_tuning.csv").exists()  # production/tuning are separate files, not a column


def test_build_lesion_matrix_group_filter_excludes_hc(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPDHC0001", [(2, 2, 2)])
    config_path = _write_config(tmp_path, data_root, output_root, overrides={"group_filter": ["ST"]})

    exit_code = build_lesion_matrix.main(["--config", str(config_path)])
    assert exit_code == 0

    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]

    # AUDIT_FINDINGS.md #48 regression: excluded_by_group used to be logged only (logs/,
    # not a permanent artifact) - config.md (a permanent artifact next to matrix.npy) must
    # also record which subjects were excluded and why, not just the final subject count.
    config_md = (out_dir / "config.md").read_text()
    assert "sub-STUNIPDHC0001" in config_md
    assert "Excluded by group_filter" in config_md


def test_build_lesion_matrix_config_md_has_params_used_line(tmp_path, monkeypatch):
    """AUDIT_FINDINGS.md #49 regression: build_lesion_matrix.py's config.md used to have
    only the generic full-config JSON dump, never the single-line "Params used: {...}"
    form dim_reduction.py/clustering.py already standardize on (and
    embedding_app.py::run_params already parses, for those two pipelines)."""
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_lesion_matrix.main(["--config", str(config_path)]) == 0

    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    config_md = (out_dir / "config.md").read_text()
    assert 'Params used: {"binarize_threshold": 0.5}' in config_md
    assert "Excluded by group_filter" in config_md
    assert "None." in config_md  # no group_filter set -> nothing excluded


def test_build_lesion_matrix_corrupt_lesion_mask_returns_1_not_raw_traceback(tmp_path, monkeypatch, caplog):
    """Regression (HIGH #20, 2026-08): nib.load raises nibabel.filebasedimages.ImageFileError
    for a truncated/corrupt .nii.gz - not FileNotFoundError (the file exists) nor ValueError
    (nibabel's own exception, not ours) - so it used to propagate as a raw traceback instead
    of the usual logging.error + return 1."""
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(1, 1, 1)])
    # A real file, non-empty, but not a valid gzip/NIfTI stream.
    bad_path = (
        data_root
        / "siteA"
        / "sub-STUNIPD0002"
        / "lesion"
        / "manual_masks"
        / "anat"
        / "sub-STUNIPD0002_label-lesion_mask.nii.gz"
    )
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    bad_path.write_bytes(b"not a real nifti file, truncated mid-transfer")

    config_path = _write_config(tmp_path, data_root, output_root)

    with caplog.at_level(logging.INFO):
        exit_code = build_lesion_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert not output_root.exists()
    # Duration must be logged on the error path too, not just on success (lesson from
    # docs/debugging/debug_25_08_26.md - a slow run that fails is exactly when knowing how
    # long it ran before failing matters most).
    assert "run duration:" in caplog.text


def test_overwrite_false_rerun_fails_without_touching_existing_output(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_lesion_matrix.main(["--config", str(config_path)]) == 0
    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    manifest_before = (out_dir / "manifest.json").read_text()

    exit_code = build_lesion_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert (out_dir / "manifest.json").read_text() == manifest_before  # untouched
