"""Unit tests for src/pipeline/embedding_app.py's main() (the CLI entry point) -
AUDIT_FINDINGS.md #45: this file didn't exist before, main()'s own error handling
(specifically app.run()'s OSError) had no test coverage of its own (only
src/analysis/embedding_app.py's underlying functions were tested).
"""

from pathlib import Path

import nibabel as nib
import numpy as np

from src.analysis.build_config import BuildMatrixConfig, SdcMatrixConfig
from src.analysis.embedding_app import ProductionRun
from src.pipeline import embedding_app


def _fake_run():
    return ProductionRun(modality="lesion", pipeline="dim_reduction", method="umap", run_name="run-a", path=None)


def _fake_build_matrix_config() -> BuildMatrixConfig:
    return BuildMatrixConfig(
        project="test",
        data_root=Path("unused"),
        datasets=["siteA"],
        group_filter=None,
        reference_template_path=Path("unused.nii.gz"),
        lesion_glob="*/manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        binarize_threshold=0.5,
        resample_interpolation="nearest",
        excluded_subjects_path=Path("unused.csv"),
        correct_out_of_brain=False,
        brain_mask_path=None,
        output_root=Path("unused"),
        session_name="test",
        overwrite=False,
        run_notes=None,
    )


def _fake_sdc_matrix_config() -> SdcMatrixConfig:
    return SdcMatrixConfig(
        project="test",
        data_root=Path("unused"),
        datasets=["siteA"],
        group_filter=None,
        excluded_subjects_path=Path("unused.csv"),
        object="disconnectome",
        representation="voxelwise",
        atlas=None,
        value_column=None,
        reference_labels_path=None,
        reference_template_path=Path("unused.nii.gz"),
        resample_interpolation="nearest",
        output_root=Path("unused"),
        session_name="test",
        overwrite=False,
        run_notes=None,
    )


def _fake_reference_img() -> nib.Nifti1Image:
    return nib.Nifti1Image(np.zeros((4, 4, 4), dtype=np.float32), np.eye(4))


def _patch_lesion_config(monkeypatch):
    """Every main() call touches --lesion-config (load_build_matrix_config +
    load_reference_image) unconditionally, once production runs are found - stubbed here so
    these CLI-level tests (which only exercise discover_production_runs/build_app wiring) never
    depend on the real config/pipelines/build_lesion_matrix.json or its reference template
    actually existing on disk (code_standards.md §4: mock only external I/O, never the code
    under test - here that's genuinely external I/O, the same reasoning already applied to
    discover_production_runs/build_app below)."""
    monkeypatch.setattr(embedding_app, "load_build_matrix_config", lambda path: _fake_build_matrix_config())
    monkeypatch.setattr(embedding_app, "load_reference_image", lambda path: _fake_reference_img())


def _patch_sdc_config(monkeypatch):
    """Same reasoning as _patch_lesion_config, for --sdc-config (load_build_sdc_matrix_config,
    added 29-09-26 alongside the SDC disconnectome anatomy panels) - load_reference_image is
    shared with _patch_lesion_config's own patch above (same function, two call sites)."""
    monkeypatch.setattr(embedding_app, "load_build_sdc_matrix_config", lambda path: _fake_sdc_matrix_config())


def test_main_no_production_runs_found_returns_1(tmp_path, monkeypatch):
    monkeypatch.setattr(embedding_app, "discover_production_runs", lambda results_root: [])
    exit_code = embedding_app.main(["--results-root", str(tmp_path)])
    assert exit_code == 1


def test_main_server_port_in_use_returns_1_not_raw_traceback(tmp_path, monkeypatch):
    """AUDIT_FINDINGS.md #45 regression: app.run() used to have no try/except at all - an
    OSError from a port already in use (a realistic scenario: a leftover instance of this
    same app already running) propagated as a raw traceback instead of a clean return 1."""
    monkeypatch.setattr(embedding_app, "discover_production_runs", lambda results_root: [_fake_run()])
    _patch_lesion_config(monkeypatch)
    _patch_sdc_config(monkeypatch)

    class _FakeApp:
        def run(self, debug, port):
            raise OSError(f"[Errno 48] Address already in use: {port}")

    monkeypatch.setattr(embedding_app, "build_app", lambda runs, lesion_cfg, sdc_cfg, clustering_params_file, preload=False: _FakeApp())

    exit_code = embedding_app.main(["--results-root", str(tmp_path), "--port", "8060"])
    assert exit_code == 1


def test_main_build_app_value_error_returns_1(tmp_path, monkeypatch):
    monkeypatch.setattr(embedding_app, "discover_production_runs", lambda results_root: [_fake_run()])
    _patch_lesion_config(monkeypatch)
    _patch_sdc_config(monkeypatch)

    def _raise(runs, lesion_cfg, sdc_cfg, clustering_params_file, preload=False):
        raise ValueError("mixed pipelines with incompatible run shapes")

    monkeypatch.setattr(embedding_app, "build_app", _raise)

    exit_code = embedding_app.main(["--results-root", str(tmp_path)])
    assert exit_code == 1


def test_main_sdc_config_not_voxelwise_returns_1(tmp_path, monkeypatch):
    """29-09-26: the SDC anatomy panels need the raw disconnectome-map.nii.gz that only
    representation="voxelwise" resolves (reference_template_path/resample_interpolation) - a
    "parcellated" build_sdc_matrix.json must fail loudly at startup (code_standards.md §0),
    never silently build an SdcViewerConfig missing fields it needs."""
    monkeypatch.setattr(embedding_app, "discover_production_runs", lambda results_root: [_fake_run()])
    _patch_lesion_config(monkeypatch)
    parcellated_config = SdcMatrixConfig(
        project="test", data_root=Path("unused"), datasets=["siteA"], group_filter=None,
        excluded_subjects_path=Path("unused.csv"),
        object="disconnectome", representation="parcellated", atlas="schaefer_200_7n",
        value_column="value", reference_labels_path=Path("unused.csv"), reference_template_path=None,
        resample_interpolation=None, output_root=Path("unused"), session_name="test", overwrite=False,
        run_notes=None,
    )
    monkeypatch.setattr(embedding_app, "load_build_sdc_matrix_config", lambda path: parcellated_config)

    exit_code = embedding_app.main(["--results-root", str(tmp_path)])
    assert exit_code == 1
