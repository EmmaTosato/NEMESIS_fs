"""Integration test: full build_sdc_matrix.py CLI run (main()) on synthetic data.

No EBRAIN mount needed - build_sdc_matrix operates on already-local files, so
this is a pure tmp_path E2E, always runs (no skipif).
"""

import json
import logging

import numpy as np
import pandas as pd

from src.pipeline import build_sdc_matrix

_ATLAS = "test_atlas"
_OBJECT = "disconnectome"
_VALUE_COLUMN = "mean_overlap"


def _make_lesion_mask(data_root, dataset, subject_id):
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    (subject_dir / f"{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz").write_bytes(b"dummy")


def _make_sdc_csv(data_root, dataset, subject_id, rows):
    subject_dir = data_root / dataset / "sdc" / subject_id / "dwi"
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"{subject_id}_space-MNI152NLin6Asym_LF-{_OBJECT}_atlas-{_ATLAS}.csv"
    lines = [f"region_name,{_VALUE_COLUMN}"] + [f"{region},{value}" for region, value in rows.items()]
    path.write_text("\n".join(lines) + "\n")


def _make_reference_labels(path, region_names):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(["region_name"] + list(region_names)) + "\n")


def _make_dataset(data_root, n_subjects=5):
    rng = np.random.default_rng(1)
    for i in range(n_subjects):
        subject_id = f"sub-STUNIPD{i:04d}"
        _make_lesion_mask(data_root, "siteA", subject_id)
        rows = {region: round(float(rng.random()), 3) for region in ["A", "B", "C"] if rng.random() > 0.3}
        _make_sdc_csv(data_root, "siteA", subject_id, rows)


def _write_config(tmp_path, data_root, output_root, overrides=None):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B", "C"])
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        "object": _OBJECT,
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


def test_build_sdc_matrix_end_to_end(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
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

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_lesion_mask(data_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(data_root, "siteA", "sub-STUNIPD0001", {"A": 0.5})
    # sub-STUNIPD0002 has SDC output but no lesion mask - must be excluded, not zero-filled
    _make_sdc_csv(data_root, "siteA", "sub-STUNIPD0002", {"A": 0.9})
    # sub-STUNIPD0003 has a lesion mask but no SDC output yet
    _make_lesion_mask(data_root, "siteA", "sub-STUNIPD0003")

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

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_sdc_matrix.main(["--config", str(config_path)]) == 0

    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    config_md = (out_dir / "config.md").read_text()
    expected = f'Params used: {{"object": "{_OBJECT}", "atlas": "{_ATLAS}", "value_column": "{_VALUE_COLUMN}"}}'
    assert expected in config_md


def test_invalid_config_returns_1_not_raw_traceback(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root, overrides={"object": "not_a_real_object"})

    with caplog.at_level(logging.INFO):
        exit_code = build_sdc_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert not output_root.exists()


def test_overwrite_false_rerun_fails_without_touching_existing_output(tmp_path, monkeypatch):
    monkeypatch.setattr(build_sdc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_sdc_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "out"
    _make_dataset(data_root)
    config_path = _write_config(tmp_path, data_root, output_root)

    assert build_sdc_matrix.main(["--config", str(config_path)]) == 0
    out_dir = next(p for p in output_root.iterdir() if p.is_dir())
    manifest_before = (out_dir / "manifest.json").read_text()

    exit_code = build_sdc_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    assert (out_dir / "manifest.json").read_text() == manifest_before
