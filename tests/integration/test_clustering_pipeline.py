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
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
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


def test_clustering_end_to_end(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    original_X = np.load(input_dir / "matrix.npy")

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["kmeans"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    exit_code = clustering.main(["--config", str(cfg_path)])
    assert exit_code == 0

    out_dir = next(p for p in (output_root / "kmeans").iterdir() if p.is_dir())
    X = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert np.array_equal(X, original_X)  # unchanged, per design (no reduction happened)
    assert list(metadata.columns) == ["subject_id", "dataset", "cluster_label"]
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
    assert (out_dir / "cluster_plot.png").stat().st_size > 0

    runs_csv = (output_root / "kmeans" / "runs.csv").read_text()
    assert "run1" in runs_csv
    assert "production" in runs_csv


def test_clustering_end_to_end_agglomerative(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"agglomerative": {"params": {"n_clusters": 3, "linkage": "ward"}}}))

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["agglomerative"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "agglomerative").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}


def test_clustering_end_to_end_gmm(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"gmm": {"params": {"n_components": 3, "random_state": 0}}}))

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["gmm"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "gmm").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}


def test_clustering_end_to_end_spectral(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps({"spectral": {"params": {"n_clusters": 3, "affinity": "nearest_neighbors", "random_state": 0}}})
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["spectral"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "spectral").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}


def test_clustering_end_to_end_dbscan_reports_noise_separately(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"dbscan": {"params": {"eps": 0.5, "min_samples": 5}}}))

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["dbscan"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "dbscan").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    # this sparse raw-voxel synthetic fixture (eps=0.5/min_samples=5) puts every
    # subject in the noise bucket - a real exercise of the -1 path, not a mock
    assert set(metadata["cluster_label"].unique()) == {-1}

    readme = (out_dir / "config.md").read_text()
    assert "Clusters found: 0" in readme
    assert "12 noise points, label -1" in readme


def test_clustering_end_to_end_multiple_methods_writes_comparison_plot(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}},
                "agglomerative": {"params": {"n_clusters": 3, "linkage": "ward"}},
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["kmeans", "agglomerative"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    # both methods get their own full artifact, unchanged from the single-method case
    for method in ("kmeans", "agglomerative"):
        out_dir = next(p for p in (output_root / method).iterdir() if p.is_dir())
        metadata = pd.read_csv(out_dir / "metadata.csv")
        assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
        assert (out_dir / "cluster_plot.png").stat().st_size > 0

    # per-method reports don't collide (method disambiguates the filename)
    report_dir = tmp_path / "cl_summaries" / "testproj"
    reports = list(report_dir.glob("clustering_summary__*.md"))
    assert len(reports) == 2
    assert any("kmeans" in p.name for p in reports)
    assert any("agglomerative" in p.name for p in reports)

    comparison_dir = next(p for p in (output_root / "comparison").iterdir() if p.is_dir())
    assert (comparison_dir / "cluster_comparison.png").stat().st_size > 0
    comparison_readme = (comparison_dir / "config.md").read_text()
    assert "kmeans" in comparison_readme
    assert "agglomerative" in comparison_readme


def test_clustering_fine_tuning_kmeans_writes_sweep_with_inertia(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3, 4]},
                }
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["kmeans"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "run_notes": "prova sweep n_clusters",
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next((output_root / "kmeans" / "tuning").iterdir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    assert not (tuning_dir / "matrix.npy").exists()  # a sweep is not a matrix artifact

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results["n_clusters"]) == [2, 3, 4]
    assert "inertia" in results.columns
    assert "silhouette" in results.columns

    runs_csv = (output_root / "kmeans" / "runs.csv").read_text()
    assert "tune1" in runs_csv
    assert "tuning" in runs_csv
    assert "prova sweep n_clusters" in runs_csv


def test_clustering_fine_tuning_gmm_writes_bic_aic(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {"gmm": {"params": {"n_components": 3, "random_state": 0}, "tuning_grid": {"n_components": [2, 3]}}}
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["gmm"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next((output_root / "gmm" / "tuning").iterdir())
    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert "bic" in results.columns
    assert "aic" in results.columns


def test_clustering_fine_tuning_agglomerative_writes_dendrogram(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {"agglomerative": {"params": {"n_clusters": 3, "linkage": "ward"}, "tuning_grid": {"n_clusters": [2, 3]}}}
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["agglomerative"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next((output_root / "agglomerative" / "tuning").iterdir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    assert (tuning_dir / "dendrogram.png").stat().st_size > 0  # standalone diagnostic, agglomerative-only


def test_clustering_fine_tuning_spectral_writes_eigengap(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "spectral": {
                    "params": {"n_clusters": 3, "affinity": "nearest_neighbors", "n_neighbors": 5, "random_state": 0},
                    "tuning_grid": {"n_clusters": [2, 3]},
                }
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["spectral"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next((output_root / "spectral" / "tuning").iterdir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    assert (tuning_dir / "eigengap_plot.png").stat().st_size > 0  # standalone diagnostic, spectral-only


def test_clustering_fine_tuning_dbscan_writes_k_distance_and_noise_fraction(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps({"dbscan": {"params": {"eps": 0.5, "min_samples": 3}, "tuning_grid": {"eps": [0.3, 5.0]}}})
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["dbscan"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next((output_root / "dbscan" / "tuning").iterdir())
    assert (tuning_dir / "k_distance_plot.png").stat().st_size > 0  # standalone diagnostic, dbscan-only

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert "noise_fraction" in results.columns


def test_clustering_fine_tuning_multiple_methods_stops_on_first_failure(tmp_path, monkeypatch):
    """A method with no tuning_grid entry fails its own sweep - the whole
    fine-tuning run stops there (no partial-failure tolerance), same
    philosophy as the production loop.
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "REPORTS_ROOT", tmp_path / "cl_summaries")
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                },
                # agglomerative has no "tuning_grid" entry on purpose
                "agglomerative": {"params": {"n_clusters": 3, "linkage": "ward"}},
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["kmeans", "agglomerative"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 1
