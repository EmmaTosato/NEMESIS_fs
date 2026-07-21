"""Integration test: dim_reduction_clustering.py chained onto a build_lesion_matrix.py output."""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.pipeline import build_lesion_matrix, dim_reduction_clustering

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _build_matrix(tmp_path, monkeypatch, n_subjects=12):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "reports")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    rng = np.random.default_rng(3)
    for i in range(n_subjects):
        subject_id = f"sub-{i:02d}"
        subject_dir = data_root / "siteA" / subject_id / "lesion" / "manual_masks" / "anat"
        subject_dir.mkdir(parents=True, exist_ok=True)
        volume = np.zeros(_SHAPE, dtype=np.float32)
        for voxel in [tuple(rng.integers(0, 10, size=3)) for _ in range(5)]:
            volume[voxel] = 1.0
        nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")

    output_root = tmp_path / "matrix_out"
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
        "run_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    build_cfg_path = tmp_path / "build.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0
    return next(p for p in output_root.iterdir() if p.is_dir())


def test_dim_reduction_clustering_end_to_end(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "REPORTS_ROOT", tmp_path / "drc_reports")
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "run_name": "run1",
        "overwrite": False,
        "run_notes": "prova pca+kmeans",
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    exit_code = dim_reduction_clustering.main(["--config", str(cfg_path)])
    assert exit_code == 0

    out_dir = next(p for p in (output_root / "pca-kmeans").iterdir() if p.is_dir())
    embedding = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert embedding.shape == (12, 2)
    assert list(metadata.columns) == ["subject_id", "dataset", "cluster_label"]
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
    assert (out_dir / "cluster_plot.png").stat().st_size > 0

    runs_md = (output_root / "pca-kmeans" / "RUNS.md").read_text()
    assert "run1" in runs_md
    assert "prova pca+kmeans" in runs_md


def test_dim_reduction_clustering_end_to_end_multiple_methods_writes_comparison_plot(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "REPORTS_ROOT", tmp_path / "drc_reports")
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}},
                "agglomerative": {"params": {"n_clusters": 3, "linkage": "ward"}},
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans", "agglomerative"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "run_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    for method in ("pca-kmeans", "pca-agglomerative"):
        out_dir = next(p for p in (output_root / method).iterdir() if p.is_dir())
        embedding = np.load(out_dir / "matrix.npy")
        assert embedding.shape == (12, 2)
        assert (out_dir / "cluster_plot.png").stat().st_size > 0

    comparison_dir = next(p for p in (output_root / "comparison").iterdir() if p.is_dir())
    assert (comparison_dir / "cluster_comparison.png").stat().st_size > 0
    comparison_readme = (comparison_dir / "README.md").read_text()
    assert "kmeans" in comparison_readme
    assert "agglomerative" in comparison_readme
    assert "pca" in comparison_readme
