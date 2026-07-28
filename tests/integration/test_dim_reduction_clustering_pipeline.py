"""Integration test: dim_reduction_clustering.py chained onto a build_lesion_matrix.py output."""

import csv
import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.pipeline import build_lesion_matrix, dim_reduction_clustering

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _build_matrix(tmp_path, monkeypatch, n_subjects=12):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
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
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    build_cfg_path = tmp_path / "build.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0
    return next(p for p in output_root.iterdir() if p.is_dir())


def test_dim_reduction_clustering_end_to_end(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "regress_out_volume": False,
        "run_notes": "prova pca+kmeans",
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    exit_code = dim_reduction_clustering.main(["--config", str(cfg_path)])
    assert exit_code == 0

    out_dir = next(p for p in (output_root / "pca" / "kmeans").iterdir() if p.is_dir())
    embedding = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert embedding.shape == (12, 2)
    assert list(metadata.columns) == ["subject_id", "dataset", "cluster_label"]
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
    assert (out_dir / "cluster_plot.png").stat().st_size > 0

    with (output_root / "pca" / "runs.csv").open(newline="") as f:
        runs_rows = list(csv.DictReader(f))
    assert len(runs_rows) == 1
    assert runs_rows[0]["reduction_method"] == "pca"
    assert runs_rows[0]["clustering_method"] == "kmeans"
    assert runs_rows[0]["session"] == "run1"
    assert runs_rows[0]["notes"] == "prova pca+kmeans"


def test_dim_reduction_clustering_end_to_end_multiple_methods_writes_comparison_plot(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "regress_out_volume": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    for method in ("kmeans", "agglomerative"):
        out_dir = next(p for p in (output_root / "pca" / method).iterdir() if p.is_dir())
        embedding = np.load(out_dir / "matrix.npy")
        assert embedding.shape == (12, 2)
        assert (out_dir / "cluster_plot.png").stat().st_size > 0

    # both methods share one runs.csv under the reduction folder, distinguished by clustering_method
    with (output_root / "pca" / "runs.csv").open(newline="") as f:
        runs_rows = list(csv.DictReader(f))
    assert [row["clustering_method"] for row in runs_rows] == ["kmeans", "agglomerative"]
    assert all(row["reduction_method"] == "pca" for row in runs_rows)

    comparison_dir = next(p for p in (output_root / "pca" / "comparison").iterdir() if p.is_dir())
    assert comparison_dir.name.startswith("pca_")
    assert (comparison_dir / "cluster_comparison.png").stat().st_size > 0
    assert (comparison_dir / "cluster_comparison_interactive.html").stat().st_size > 0
    comparison_html = (comparison_dir / "cluster_comparison_interactive.html").read_text()
    assert "plotly" in comparison_html
    assert "updatemenus" in comparison_html
    comparison_readme = (comparison_dir / "config.md").read_text()
    assert "kmeans" in comparison_readme
    assert "agglomerative" in comparison_readme
    assert "pca" in comparison_readme


def test_dim_reduction_clustering_fine_tuning_kmeans_sweeps_against_one_embedding(tmp_path, monkeypatch):
    """fine_tuning=true: the reduction runs once (fixed params, never swept),
    then kmeans' own tuning_grid is swept against that one embedding.
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3, 4]},
                }
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "regress_out_volume": False,
        "run_notes": "prova sweep n_clusters su embedding pca",
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next((output_root / "pca" / "kmeans" / "tuning").iterdir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    assert not (tuning_dir / "matrix.npy").exists()  # a sweep is not a matrix artifact

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results["n_clusters"]) == [2, 3, 4]
    assert "inertia" in results.columns
    assert "silhouette" in results.columns

    # no comparison plot in tuning mode - only one method's sweep, and a sweep
    # isn't a single set of cluster labels to compare side by side anyway
    assert not (output_root / "pca" / "comparison").exists()

    assert not (output_root / "pca" / "runs.csv").exists()  # tuning writes runs_tuning.csv, not runs.csv
    with (output_root / "pca" / "runs_tuning.csv").open(newline="") as f:
        runs_rows = list(csv.DictReader(f))
    assert runs_rows[0]["reduction_method"] == "pca"
    assert runs_rows[0]["clustering_method"] == "kmeans"
    assert runs_rows[0]["notes"] == "prova sweep n_clusters su embedding pca"


def test_dim_reduction_clustering_fine_tuning_agglomerative_writes_dendrogram(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "agglomerative": {
                    "params": {"n_clusters": 3, "linkage": "ward"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                }
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["agglomerative"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "regress_out_volume": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next((output_root / "pca" / "agglomerative" / "tuning").iterdir())
    assert (tuning_dir / "dendrogram.png").stat().st_size > 0  # standalone diagnostic, agglomerative-only


def _make_varying_volume_dataset(data_root, n_subjects=12):
    """Unlike _build_matrix's _make_dataset (fixed 5-voxel draws, which can
    coincidentally tie every subject's lesion volume at the same count),
    each subject here gets a strictly increasing, non-overlapping voxel
    count - guarantees the lesion-volume covariate actually varies, which
    regress_out_covariate requires (zero-variance covariate raises).
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
    _make_varying_volume_dataset(data_root)
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
    build_cfg_path = tmp_path / "build_varying.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0
    return next(p for p in output_root.iterdir() if p.is_dir())


def test_dim_reduction_clustering_regress_out_volume_changes_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix_varying_volume(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    output_root = tmp_path / "drc_out"

    def _run(regress_out_volume: bool, session_name: str) -> np.ndarray:
        cfg = {
            "project": "testproj",
            "input_path": str(input_dir),
            "reduction_method": "pca",
            "reduction_params_file": str(reduction_params_path),
            "clustering_methods": ["kmeans"],
            "clustering_params_file": str(clustering_params_path),
            "output_root": str(output_root),
            "session_name": session_name,
            "overwrite": False,
            "fine_tuning": False,
            "regress_out_volume": regress_out_volume,
            "run_notes": None,
        }
        cfg_path = tmp_path / f"drc_{session_name}.json"
        cfg_path.write_text(json.dumps(cfg))
        assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0
        out_dir = next(p for p in (output_root / "pca" / "kmeans").iterdir() if session_name in p.name)
        return np.load(out_dir / "matrix.npy")

    embedding_plain = _run(False, "plain")
    embedding_regressed = _run(True, "regressed")

    assert embedding_plain.shape == embedding_regressed.shape
    assert not np.array_equal(embedding_plain, embedding_regressed)


def test_dim_reduction_clustering_regress_out_volume_incompatible_with_dice_raises(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(
        json.dumps(
            {
                "umap": {
                    "params": {
                        "n_neighbors": 3,
                        "min_dist": 0.1,
                        "n_components": 2,
                        "random_state": 0,
                        "metric": "dice",
                    }
                }
            }
        )
    )
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(tmp_path / "drc_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "regress_out_volume": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 1


def test_dim_reduction_clustering_fine_tuning_missing_tuning_grid_raises(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    # kmeans has no "tuning_grid" entry on purpose
    clustering_params_path.write_text(
        json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}})
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "regress_out_volume": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 1
