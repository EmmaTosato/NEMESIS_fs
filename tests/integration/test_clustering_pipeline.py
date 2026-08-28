"""Integration test: clustering.py (no reduction) chained onto a build_lesion_matrix.py output."""

import json
import logging

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
        subject_id = f"sub-STUNIPD{i:04d}"
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
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    build_cfg_path = tmp_path / "build.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0
    return next(p for p in output_root.iterdir() if p.is_dir())


def _write_viz_embedding(tmp_path, name, subject_metadata):
    """Builds a tiny 2D companion embedding artifact (see
    clustering.py::_resolve_viz_embedding) covering the exact same subjects,
    in the exact same order, as subject_metadata - the shape viz_embedding_path
    must have to be accepted."""
    from src.utils.artifacts import save_matrix

    n = len(subject_metadata)
    viz_X = np.random.default_rng(0).normal(size=(n, 2))
    viz_dir = tmp_path / name
    save_matrix(viz_dir, viz_X, subject_metadata.copy(), ["# viz embedding fixture"], overwrite=False)
    return viz_dir


def _write_dim_reduction_run(tmp_path, name, n_subjects, n_components, method, params):
    """Builds a synthetic dim_reduction.py-shaped production run (title line + "Params
    used: {...}", the exact contract dim_reduction.py::_build_readme_lines writes) - used to
    test clustering.py's reduced_data=True cross-check
    (clustering._require_matching_reduction_run) without running the real dim_reduction.py
    pipeline end to end. Two calls with the same n_subjects cover the exact same
    deterministic subject_id list, in the exact same order - the shape
    _resolve_viz_embedding's structural check already requires."""
    from src.utils.artifacts import save_matrix

    subject_ids = [f"sub-STUNIPD{i:04d}" for i in range(n_subjects)]
    metadata = pd.DataFrame({"subject_id": subject_ids, "dataset": ["siteA"] * n_subjects})
    X = np.random.default_rng(1).normal(size=(n_subjects, n_components))
    readme_lines = [
        f"# testproj dim_reduction ({method}) — 26-08-26 10:00",
        "",
        f"Params used: {json.dumps(params)}",
    ]
    run_dir = tmp_path / name
    save_matrix(run_dir, X, metadata, readme_lines, overwrite=False)
    return run_dir


def test_clustering_end_to_end(tmp_path, monkeypatch, caplog):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    original_X = np.load(input_dir / "matrix.npy")
    input_metadata = pd.read_csv(input_dir / "metadata.csv")
    viz_dir = _write_viz_embedding(tmp_path, "viz_embedding", input_metadata)

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    with caplog.at_level(logging.INFO):
        exit_code = clustering.main(["--config", str(cfg_path)])
    assert exit_code == 0
    # docs/debugging/debug_25_08_26.md: a run's duration must be logged, success or not.
    assert "run duration:" in caplog.text

    out_dir = next(p for p in (output_root / "production" / "kmeans").iterdir() if p.is_dir())
    X = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert np.array_equal(X, original_X)  # unchanged, per design (no reduction happened)
    # lesion_volume_voxels is now always computed by build_lesion_matrix.py (2026-08-17) -
    # inherited unchanged through clustering.py's own metadata pass-through, alongside the
    # cluster_label this pipeline itself appends.
    assert list(metadata.columns) == ["subject_id", "dataset", "lesion_volume_voxels", "cluster_label"]
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
    # X has 57 raw voxel columns (not 2 or 3) - this plot only exists because
    # viz_embedding_path was given (see _resolve_viz_embedding), not from a
    # slice of X (lessons_learned.md #16).
    assert (out_dir / "cluster_plot.png").stat().st_size > 0

    runs_csv = (output_root / "production" / "kmeans" / "runs.csv").read_text()
    assert "run1" in runs_csv
    assert not (output_root / "tuning" / "kmeans" / "runs_tuning.csv").exists()  # production/tuning are separate files, not a column


def test_clustering_unrecognized_hyperparameter_returns_1_not_raw_traceback(tmp_path, monkeypatch, caplog):
    """Regression (HIGH #18, 2026-08 - the same gap #11 fixed in dim_reduction.py, found here
    in clustering.py's own production path during the same audit, against a config that no
    longer exists after dim_reduction_clustering.py's removal): load_method_params only
    validates that the file/method exist, never the *contents* of params - a typo'd
    hyperparameter key reached CLUSTERING_METHODS[method](X, params) unprotected and
    propagated as a raw TypeError instead of logging.error + return 1."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_cluster": 3, "random_state": 0, "n_init": "auto"}}}))

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": None,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    with caplog.at_level(logging.INFO):
        exit_code = clustering.main(["--config", str(cfg_path)])
    assert exit_code == 1
    assert not output_root.exists()
    # Duration must be logged on the error path too, not just on success. This error is
    # raised deep in the per-method loop (_run_one_method) - confirms the finally in main()
    # still fires through that nesting, not just for the flat early-return paths.
    assert "run duration:" in caplog.text


def test_clustering_viz_embedding_path_wrong_n_components_raises(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    input_metadata = pd.read_csv(input_dir / "metadata.csv")
    from src.utils.artifacts import save_matrix

    bad_viz_dir = tmp_path / "bad_viz"
    save_matrix(
        bad_viz_dir,
        np.random.default_rng(0).normal(size=(len(input_metadata), 5)),  # 5 components, not 2 or 3
        input_metadata.copy(),
        ["# bad viz fixture"],
        overwrite=False,
    )

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(bad_viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 1


def test_clustering_viz_embedding_path_mismatched_subjects_raises(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    input_metadata = pd.read_csv(input_dir / "metadata.csv")
    shuffled_metadata = input_metadata.iloc[::-1].reset_index(drop=True)  # same subjects, different order
    viz_dir = _write_viz_embedding(tmp_path, "shuffled_viz", shuffled_metadata)

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 1


def test_clustering_end_to_end_no_viz_embedding_skips_plots(tmp_path, monkeypatch):
    """Regression: X here has 57 raw voxel columns (not 2 or 3) and no
    viz_embedding_path is given - every cluster-colored plot must be skipped
    with a warning, never silently drawn from X[:, :2] (lessons_learned.md #16)."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "kmeans").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}  # the artifact itself is still written
    assert not (out_dir / "cluster_plot.png").exists()
    assert not (out_dir / "silhouette_plot.png").exists()


def test_clustering_end_to_end_agglomerative(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "agglomerative").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}


def test_clustering_end_to_end_gmm(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "gmm").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}


def test_clustering_end_to_end_spectral(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "spectral").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}


def test_clustering_end_to_end_evidence_accumulation(tmp_path, monkeypatch):
    """evidence_accumulation (Fred & Jain 2002, base_method="spectral" here -
    i.e. Zanola et al. 2026's RSC specifically) chained through the full
    production pipeline exactly like every other method - final labels come
    from src.analysis.consensus_clustering.assign_clusters_from_cooccurrence,
    not from a single spectral_cluster run (see
    clustering.py::evidence_accumulation_cluster).
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "evidence_accumulation": {
                    "params": {
                        "base_method": "spectral",
                        "n_clusters": 3,
                        "affinity": "nearest_neighbors",
                        "n_neighbors": 5,
                        "n_repeats": 10,
                        "threshold": 0.5,
                        "base_seed": 0,
                    }
                }
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["evidence_accumulation"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "evidence_accumulation").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    # unlike every other method, the number of clusters isn't a parameter
    # here - it emerges from the threshold cut, so only the label shape/type
    # is checked, not a specific bounded set of values
    assert len(metadata["cluster_label"]) == 12
    assert (metadata["cluster_label"] >= 0).all()
    # X has 57 raw voxel columns and no viz_embedding_path was given here - no
    # cluster_plot.png, see test_clustering_end_to_end_no_viz_embedding_skips_plots.
    assert not (out_dir / "cluster_plot.png").exists()


def test_clustering_end_to_end_hdbscan_reports_noise_separately(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"hdbscan": {"params": {"min_cluster_size": 5}}}))

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["hdbscan"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "hdbscan").iterdir() if p.is_dir())
    metadata = pd.read_csv(out_dir / "metadata.csv")
    # this sparse raw-voxel synthetic fixture (min_cluster_size=5 on 12 subjects)
    # puts every subject in the noise bucket - a real exercise of the -1 path,
    # not a mock
    assert set(metadata["cluster_label"].unique()) == {-1}

    readme = (out_dir / "config.md").read_text()
    assert "Clusters found: 0" in readme
    assert "12 noise points, label -1" in readme


def test_clustering_end_to_end_hdbscan_cluster_plot_sized_by_probabilities(tmp_path, monkeypatch):
    """project-clustering-tuning-redesign memory (26-08-26): the production cluster_plot.png
    for hdbscan must be produced via the probabilities_-aware path
    (hdbscan_labels_and_probabilities), not the plain labels-only CLUSTERING_METHODS["hdbscan"]
    every other method still uses."""
    input_dir = _build_matrix(tmp_path, monkeypatch, n_subjects=30)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"hdbscan": {"params": {"min_cluster_size": 3}}}))

    input_metadata = pd.read_csv(input_dir / "metadata.csv")
    viz_dir = _write_viz_embedding(tmp_path, "viz_embedding", input_metadata)

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["hdbscan"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "hdbscan").iterdir() if p.is_dir())
    assert (out_dir / "cluster_plot.png").stat().st_size > 0


def test_clustering_fine_tuning_hdbscan_min_samples_joint_sweep_writes_heatmap(tmp_path, monkeypatch):
    """project-clustering-tuning-redesign memory (26-08-26): min_cluster_size x min_samples
    reuses the existing 2-swept-param heatmap mechanism, in a single sweep run (no repeated/
    sequential tuning runs)."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {"hdbscan": {"params": {}, "tuning_grid": {"min_cluster_size": [2, 5], "min_samples": [2, 5]}}}
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["hdbscan"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_joint",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "hdbscan").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0  # heatmap, 2 swept params

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 4
    assert set(results["min_samples"]) == {2, 5}


def test_clustering_end_to_end_multiple_methods_writes_comparison_plot(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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

    input_metadata = pd.read_csv(input_dir / "metadata.csv")
    viz_dir = _write_viz_embedding(tmp_path, "viz_embedding", input_metadata)

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    # both methods get their own full artifact, unchanged from the single-method case
    for method in ("kmeans", "agglomerative"):
        out_dir = next(p for p in (output_root / "production" / method).iterdir() if p.is_dir())
        metadata = pd.read_csv(out_dir / "metadata.csv")
        assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
        assert (out_dir / "cluster_plot.png").stat().st_size > 0

    comparison_dir = next(p for p in (output_root / "production" / "comparison").iterdir() if p.is_dir())
    assert (comparison_dir / "cluster_comparison.png").stat().st_size > 0
    assert (comparison_dir / "cluster_comparison_interactive.html").stat().st_size > 0
    comparison_readme = (comparison_dir / "config.md").read_text()
    assert "kmeans" in comparison_readme
    assert "agglomerative" in comparison_readme


def test_clustering_comparison_dir_overwrite_false_rerun_fails_without_clobbering(tmp_path, monkeypatch):
    """Regression (HIGH #16, 2026-08): unlike save_matrix (per-method output) and
    _write_tuning_output, comparison/ never checked config.overwrite at all - a second run
    with the same session_name but a genuinely different clustering_methods list (one
    already-existing method fails fast via save_matrix's own overwrite=False, but if even
    one genuinely new method succeeds, the comparison block used to silently overwrite the
    first run's cluster_comparison.png/config.md, the one artifact overwrite=False was
    supposed to protect."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
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

    input_metadata = pd.read_csv(input_dir / "metadata.csv")
    viz_dir = _write_viz_embedding(tmp_path, "viz_embedding", input_metadata)

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))
    assert clustering.main(["--config", str(cfg_path)]) == 0

    comparison_dir = next(p for p in (output_root / "production" / "comparison").iterdir() if p.is_dir())
    original_readme = (comparison_dir / "config.md").read_text()
    assert "agglomerative" not in original_readme

    # Second run, same session_name/day (so same comparison_dir), a different method list -
    # overwrite stays False.
    cfg["clustering_methods"] = ["agglomerative"]
    cfg_path.write_text(json.dumps(cfg))
    assert clustering.main(["--config", str(cfg_path)]) == 1

    # comparison/ from the first run must be untouched, not silently overwritten.
    assert (comparison_dir / "config.md").read_text() == original_readme


def test_clustering_comparison_plot_failure_returns_1_not_raw_traceback(tmp_path, monkeypatch):
    """Regression (HIGH #15, 2026-08): unlike save_matrix/append_run_log_entry elsewhere in
    this same main(), the comparison-plot block had no try/except at all - an OSError while
    writing cluster_comparison.png (e.g. disk full) propagated as a raw traceback even
    though every per-method run before it had already completed and been saved
    successfully."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    def _raise_disk_full(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(clustering, "plot_clusters_comparison", _raise_disk_full)

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    input_metadata = pd.read_csv(input_dir / "metadata.csv")
    viz_dir = _write_viz_embedding(tmp_path, "viz_embedding", input_metadata)

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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 1
    # the per-method output, already written before the comparison block, survives.
    assert (output_root / "production" / "kmeans").exists()


def test_clustering_fine_tuning_kmeans_writes_sweep_with_inertia(tmp_path, monkeypatch, caplog):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": "prova sweep n_clusters",
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    with caplog.at_level(logging.INFO):
        exit_code = clustering.main(["--config", str(cfg_path)])
    assert exit_code == 0
    # fine-tuning's own completion point (separate from production's) must log duration too.
    assert "run duration:" in caplog.text

    tuning_dir = next(p for p in (output_root / "tuning" / "kmeans").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    assert not (tuning_dir / "matrix.npy").exists()  # a sweep is not a matrix artifact

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results["n_clusters"]) == [2, 3, 4]
    assert "inertia" in results.columns
    assert "silhouette" in results.columns

    runs_csv = (output_root / "tuning" / "kmeans" / "runs_tuning.csv").read_text()
    assert "tune1" in runs_csv
    assert "prova sweep n_clusters" in runs_csv
    assert not (output_root / "production" / "kmeans" / "runs.csv").exists()  # tuning writes runs_tuning.csv, not runs.csv


def test_clustering_fine_tuning_save_tuning_clusterings_true_writes_clusterings_npz(tmp_path, monkeypatch):
    """Regression (26-08-26, save_tuning_clusterings feature): opt-in must persist every
    swept combination's actual cluster-label array (not just its scores in
    tuning_results.csv) plus a self-contained metadata.csv, keyed the same way as
    dim_reduction.py's own save_tuning_embeddings/embeddings.npz."""
    input_dir = _build_matrix(tmp_path, monkeypatch, n_subjects=12)
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
        "session_name": "tune_save",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "kmeans").iterdir() if p.is_dir())
    npz = np.load(tuning_dir / "clusterings.npz")
    assert set(npz.files) == {"n_clusters=2", "n_clusters=3", "n_clusters=4"}
    for key, expected_n_clusters in [("n_clusters=2", 2), ("n_clusters=3", 3), ("n_clusters=4", 4)]:
        labels = npz[key]
        assert labels.shape == (12,)
        assert len(set(labels)) == expected_n_clusters

    metadata = pd.read_csv(tuning_dir / "metadata.csv")
    assert list(metadata["subject_id"]) == [f"sub-STUNIPD{i:04d}" for i in range(12)]


def test_clustering_fine_tuning_save_tuning_clusterings_false_skips_clusterings_npz(tmp_path, monkeypatch):
    """Regression companion to the test above: the default (False) must not write
    clusterings.npz/metadata.csv at all - opt-in means genuinely off unless requested."""
    input_dir = _build_matrix(tmp_path, monkeypatch, n_subjects=12)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}, "tuning_grid": {"n_clusters": [2, 3]}}})
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["kmeans"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_nosave",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "kmeans").iterdir() if p.is_dir())
    assert not (tuning_dir / "clusterings.npz").exists()
    assert not (tuning_dir / "metadata.csv").exists()


def test_clustering_fine_tuning_two_swept_params_writes_heatmap(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "agglomerative": {
                    "params": {"n_clusters": 2, "linkage": "ward"},
                    "tuning_grid": {"n_clusters": [2, 3], "linkage": ["ward", "average"]},
                }
            }
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "agglomerative").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0  # heatmap, not the 1-param line plot

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 4  # 2 x 2 cartesian product
    assert set(results["linkage"]) == {"ward", "average"}


def test_clustering_fine_tuning_overwrite_wipes_stale_plot_from_incompatible_prior_grid(tmp_path, monkeypatch):
    """Regression: re-running fine_tuning into the same output_dir with
    overwrite=True but a differently-shaped tuning_grid (3+ swept params,
    which produces no plot at all - only 1 or 2 are supported) used to leave
    the prior run's tuning_plot.png sitting there, stale and undescribed by
    the freshly-written config.md - same root cause as dim_reduction.py's
    leaf-folder staleness (lessons_learned.md #18)."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    output_root = tmp_path / "cl_out"
    params_path = tmp_path / "params_clustering.json"

    def _cfg(overwrite):
        return {
            "project": "testproj",
            "input_path": str(input_dir),
            "clustering_methods": ["kmeans"],
            "params_file": str(params_path),
            "output_root": str(output_root),
            "session_name": "tune_reuse",
            "overwrite": overwrite,
            "fine_tuning": True,
            "reduced_data": False,
            "save_tuning_clusterings": False,
            "run_notes": None,
        }

    # Run 1: 1 swept param -> writes a real tuning_plot.png (line plot).
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                }
            }
        )
    )
    cfg_path = tmp_path / "cl1.json"
    cfg_path.write_text(json.dumps(_cfg(overwrite=False)))
    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "kmeans").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0

    # Run 2: same output_dir, overwrite=True, but 3 swept params - no plot
    # supported (only 1 or 2), see _write_tuning_output's own warning branch.
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3], "random_state": [0, 1], "n_init": [1, 2]},
                }
            }
        )
    )
    cfg_path2 = tmp_path / "cl2.json"
    cfg_path2.write_text(json.dumps(_cfg(overwrite=True)))
    assert clustering.main(["--config", str(cfg_path2)]) == 0

    assert not (tuning_dir / "tuning_plot.png").exists(), (
        "stale plot from the prior, incompatible grid must not survive overwrite=True"
    )
    assert (tuning_dir / "tuning_results.csv").is_file()


def test_clustering_fine_tuning_kmeans_with_consensus_writes_rsc_monti_columns(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                    "consensus": {"rsc": {"n_repeats": 5}, "monti": {"n_repeats": 10, "subsample_fraction": 0.8}},
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
        "session_name": "tune_consensus",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": "prova consensus/stability clustering",
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "kmeans").iterdir() if p.is_dir())
    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert "rsc_eigengap" in results.columns
    assert "monti_stability" in results.columns
    assert results["rsc_eigengap"].notna().all()
    assert results["monti_stability"].notna().all()

    # config.md stays a pure launch snapshot - the suggestion goes in its own file
    config_md = (tuning_dir / "config.md").read_text()
    assert "suggests" not in config_md.lower()

    suggestions = (tuning_dir / "consensus_suggestions.md").read_text()
    assert "RSC suggests n_clusters=" in suggestions
    assert "Monti suggests n_clusters=" in suggestions


def test_clustering_fine_tuning_agglomerative_metric_aware_sweep_writes_new_diagnostics(tmp_path, monkeypatch):
    """project-clustering-tuning-redesign memory (26-08-26): a swept linkage x metric grid must
    (1) skip the invalid ward+non-euclidean combinations rather than crash, (2) write one
    dendrogram per swept linkage value (not a single stale dendrogram.png), (3) write
    interclass_distance_matrix.png, one heatmap per swept metric value, using the fixture's own
    "dataset" metadata column as the weak ground-truth proxy grouping."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "agglomerative": {
                    "params": {"n_clusters": 3},
                    "tuning_grid": {
                        "n_clusters": [2, 3],
                        "linkage": ["ward", "average"],
                        "metric": ["euclidean", "cosine"],
                    },
                }
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["agglomerative"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_metric_aware",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "agglomerative").iterdir() if p.is_dir())
    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    # 2 n_clusters x 2 linkage x 2 metric = 8, minus the 2 invalid ward+cosine combos
    assert len(results) == 6
    assert not ((results["linkage"] == "ward") & (results["metric"] == "cosine")).any()
    assert results.loc[results["metric"] == "cosine", "calinski_harabasz"].isna().all()
    assert results.loc[results["metric"] == "euclidean", "calinski_harabasz"].notna().all()

    # ward+cosine is invalid (skipped), so dendrogram_metric=euclidean.png has 2 linkage
    # subplots (ward, average) but dendrogram_metric=cosine.png only has 1 (average)
    assert (tuning_dir / "dendrogram_metric=euclidean.png").stat().st_size > 0
    assert (tuning_dir / "dendrogram_metric=cosine.png").stat().st_size > 0
    assert not (tuning_dir / "dendrogram.png").exists()  # replaced by the per-metric files
    assert not (tuning_dir / "dendrogram_ward.png").exists()  # replaced by the per-metric files

    assert (tuning_dir / "interclass_distance_matrix.png").stat().st_size > 0


def test_clustering_fine_tuning_kmeans_with_stability_writes_stability_output(tmp_path, monkeypatch):
    """project-clustering-tuning-redesign memory (26-08-26): an opt-in "stability" config
    block must produce stability_results.csv/stability_plot.png alongside the plain sweep,
    at the 3 representative n_clusters values derived from tuning_grid (min/median/max of
    [2, 3, 4] -> [2, 3, 4])."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3, 4]},
                    "stability": {"nuisance_values": ["k-means++", "random"], "n_init_range": [1, 3], "n_repeats": 2},
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
        "session_name": "tune_stability",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "kmeans").iterdir() if p.is_dir())
    assert (tuning_dir / "stability_plot.png").stat().st_size > 0

    stability = pd.read_csv(tuning_dir / "stability_results.csv")
    assert set(stability["n_clusters"]) == {2, 3, 4}
    assert set(stability["init"]) == {"k-means++", "random"}
    assert (stability["inertia"] > 0).all()


def test_clustering_fine_tuning_gmm_writes_bic_aic(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "gmm").iterdir() if p.is_dir())
    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert "bic" in results.columns
    assert "aic" in results.columns


def test_clustering_fine_tuning_gmm_covariance_type_joint_sweep_writes_heatmap(tmp_path, monkeypatch):
    """project-clustering-tuning-redesign memory (26-08-26): n_components x covariance_type is
    a legitimate joint sweep (AIC/BIC are the correct model-selection tool for it), needing
    zero change to run_clustering_tuning_sweep - covariance_type reaches GaussianMixture(**params)
    like any other swept key."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "gmm": {
                    "params": {"n_components": 3, "random_state": 0},
                    "tuning_grid": {"n_components": [2, 3], "covariance_type": ["full", "diag"]},
                }
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["gmm"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_covariance",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "gmm").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0  # heatmap, 2 swept params

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 4
    assert set(results["covariance_type"]) == {"full", "diag"}
    assert results["bic"].notna().all()
    assert results["aic"].notna().all()


def test_clustering_fine_tuning_gmm_with_stability_writes_stability_output(tmp_path, monkeypatch):
    """gmm inherits kmeans's stability analysis (project-clustering-tuning-redesign memory,
    26-08-26) - on its own knobs (n_init/init_params) and its own metric (bic)."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "gmm": {
                    "params": {"n_components": 3, "random_state": 0},
                    "tuning_grid": {"n_components": [2, 3, 4]},
                    "stability": {"nuisance_values": ["kmeans", "random"], "n_init_range": [1, 3], "n_repeats": 2},
                }
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["gmm"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_gmm_stability",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "gmm").iterdir() if p.is_dir())
    assert (tuning_dir / "stability_plot.png").stat().st_size > 0

    stability = pd.read_csv(tuning_dir / "stability_results.csv")
    assert set(stability["n_components"]) == {2, 3, 4}
    assert set(stability["init_params"]) == {"kmeans", "random"}
    assert stability["bic"].notna().all()


def test_clustering_fine_tuning_agglomerative_writes_dendrogram(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "agglomerative").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    # linkage/metric not swept -> base_params defaults (ward, euclidean), single-subplot file
    assert (tuning_dir / "dendrogram_metric=euclidean.png").stat().st_size > 0  # standalone diagnostic, agglomerative-only


def test_clustering_fine_tuning_spectral_writes_eigengap(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "spectral").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    # affinity not swept -> base_params' own affinity (nearest_neighbors), single-subplot file
    assert (tuning_dir / "eigengap_affinity=nearest_neighbors.png").stat().st_size > 0  # standalone diagnostic, spectral-only


def test_clustering_fine_tuning_spectral_affinity_aware_sweep_writes_combined_plot(tmp_path, monkeypatch):
    """project-clustering-tuning-redesign memory (26-08-26): a swept 'affinity' runs the
    affinity-aware sweep (2 sub-sweeps, n_neighbors/gamma each only applying to their own
    affinity) and writes the combined plot_spectral_tuning tuning_plot.png, not the generic
    line/heatmap dispatch."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "spectral": {
                    "params": {"n_clusters": 3, "assign_labels": "cluster_qr", "random_state": 0},
                    "tuning_grid": {
                        "n_clusters": [2, 3],
                        "affinity": ["nearest_neighbors", "rbf"],
                        "n_neighbors": [5, 10],
                        "gamma": [0.5, 1.0],
                    },
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
        "session_name": "tune_affinity",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "spectral").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    # affinity swept (nearest_neighbors, rbf) -> one eigengap file per affinity, each with a
    # subplot per swept value of its own hyperparameter (found 28-08-26: the old single
    # eigengap_plot.png never reflected this, always computed from base_params alone)
    assert (tuning_dir / "eigengap_affinity=nearest_neighbors.png").stat().st_size > 0
    assert (tuning_dir / "eigengap_affinity=rbf.png").stat().st_size > 0
    assert not (tuning_dir / "eigengap_plot.png").exists()  # replaced by the per-affinity files

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 8
    assert set(results["affinity"]) == {"nearest_neighbors", "rbf"}


def test_clustering_fine_tuning_spectral_affinity_aware_sweep_rejects_save_tuning_clusterings(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "spectral": {
                    "params": {"n_clusters": 3, "assign_labels": "cluster_qr", "random_state": 0},
                    "tuning_grid": {"n_clusters": [2, 3], "affinity": ["nearest_neighbors", "rbf"], "n_neighbors": [5], "gamma": [1.0]},
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
        "session_name": "tune_affinity_reject",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": True,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 1


def test_clustering_fine_tuning_hdbscan_writes_noise_fraction(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps({"hdbscan": {"params": {}, "tuning_grid": {"min_cluster_size": [2, 8]}}})
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["hdbscan"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    # HDBSCAN gets no standalone diagnostic (unlike agglomerative/spectral) -
    # no eps to read off a plot by eye, see clustering_tuning.py's module docstring
    tuning_dir = next(p for p in (output_root / "tuning" / "hdbscan").iterdir() if p.is_dir())
    assert not (tuning_dir / "k_distance_plot.png").exists()

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert "noise_fraction" in results.columns


def test_clustering_fine_tuning_evidence_accumulation_threshold_split_k_sweep_writes_new_diagnostics(tmp_path, monkeypatch):
    """project-clustering-tuning-redesign memory (26-08-26): threshold x Split-phase n_clusters
    joint sweep (grouped line plot, not a heatmap) + n_repeats convergence check + consensus
    matrix heatmap, all in one fine-tuning run."""
    input_dir = _build_matrix(tmp_path, monkeypatch, n_subjects=15)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "evidence_accumulation": {
                    "params": {
                        "base_method": "kmeans",
                        "n_clusters": 6,
                        "n_init": "auto",
                        "n_repeats": 10,
                        "threshold": 0.5,
                        "base_seed": 0,
                    },
                    "tuning_grid": {"threshold": [0.3, 0.5, 0.7], "n_clusters": [4, 6]},
                }
            }
        )
    )

    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["evidence_accumulation"],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_ea",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "evidence_accumulation").iterdir() if p.is_dir())
    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 6  # 3 thresholds x 2 split-k
    assert set(results["n_clusters"]) == {4, 6}

    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0  # grouped line plot, not a heatmap

    assert (tuning_dir / "n_repeats_convergence.png").stat().st_size > 0
    convergence = pd.read_csv(tuning_dir / "n_repeats_convergence.csv")
    assert list(convergence.columns) == ["n_repeats", "stability_score"]
    assert len(convergence) > 0

    assert (tuning_dir / "consensus_matrix_heatmap.png").stat().st_size > 0


def test_clustering_fine_tuning_multiple_methods_stops_on_first_failure(tmp_path, monkeypatch):
    """A method with no tuning_grid entry fails its own sweep - the whole
    fine-tuning run stops there (no partial-failure tolerance), same
    philosophy as the production loop.
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 1


def test_clustering_fine_tuning_sweep_value_error_is_caught_not_propagated(tmp_path, monkeypatch):
    """Regression: run_clustering_tuning_sweep sat between two try/except
    blocks in _run_one_method_tuning, itself unprotected - a ValueError
    raised inside it (e.g. run_monti_repeats finding two subjects never
    co-sampled together) used to propagate as a raw, unhandled exception out
    of main() instead of the clean logging.error + return 1 every other
    failure in this function already gets."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")

    def _raise(*args, **kwargs):
        raise ValueError("subjects sub-00 and sub-05 never co-sampled together")

    monkeypatch.setattr(clustering, "run_clustering_tuning_sweep", _raise)

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                },
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
        "reduced_data": False,
        "save_tuning_clusterings": False,
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl_valueerror.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 1


def test_clustering_viz_embedding_matching_reduction_run_succeeds(tmp_path, monkeypatch):
    """Regression (26-08-26, found in discussion about viz_embedding_path's structural-only
    checks): reduced_data=True + a companion built with the same reduction method and the
    same params (n_components excepted) must be accepted and produce plots."""
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")
    shared_params = {"n_neighbors": 15, "metric": "euclidean", "random_state": 0}
    input_dir = _write_dim_reduction_run(
        tmp_path, "input_5d", n_subjects=12, n_components=5, method="umap",
        params={**shared_params, "n_components": 5},
    )
    viz_dir = _write_dim_reduction_run(
        tmp_path, "viz_2d", n_subjects=12, n_components=2, method="umap",
        params={**shared_params, "n_components": 2},
    )

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

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
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl_match.json"
    cfg_path.write_text(json.dumps(cfg))

    assert clustering.main(["--config", str(cfg_path)]) == 0
    run_dir = next(p for p in (output_root / "production" / "kmeans").iterdir() if p.is_dir())
    assert (run_dir / "cluster_plot.png").exists()


def test_clustering_viz_embedding_different_reduction_method_raises(tmp_path, monkeypatch, caplog):
    """Regression (26-08-26): a companion built with a different reduction method than
    input_path must be rejected, even though it passes every structural check (same
    subjects, same order, 2D) - accepting it would plot real cluster labels onto an
    unrelated geometry."""
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")
    input_dir = _write_dim_reduction_run(
        tmp_path, "input_5d", n_subjects=12, n_components=5, method="umap",
        params={"n_neighbors": 15, "metric": "euclidean", "random_state": 0, "n_components": 5},
    )
    viz_dir = _write_dim_reduction_run(
        tmp_path, "viz_2d", n_subjects=12, n_components=2, method="pca",
        params={"random_state": 0, "n_components": 2},
    )

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["kmeans"],
        "params_file": str(params_path),
        "output_root": str(tmp_path / "cl_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl_method_mismatch.json"
    cfg_path.write_text(json.dumps(cfg))

    with caplog.at_level(logging.ERROR):
        assert clustering.main(["--config", str(cfg_path)]) == 1
    assert "'pca'" in caplog.text and "'umap'" in caplog.text


def test_clustering_viz_embedding_mismatched_param_raises(tmp_path, monkeypatch, caplog):
    """Regression (26-08-26): same reduction method, but a companion built with a different
    hyperparameter (n_neighbors) than input_path must be rejected - only n_components is
    allowed to differ between the two runs."""
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")
    input_dir = _write_dim_reduction_run(
        tmp_path, "input_5d", n_subjects=12, n_components=5, method="umap",
        params={"n_neighbors": 15, "metric": "euclidean", "random_state": 0, "n_components": 5},
    )
    viz_dir = _write_dim_reduction_run(
        tmp_path, "viz_2d", n_subjects=12, n_components=2, method="umap",
        params={"n_neighbors": 30, "metric": "euclidean", "random_state": 0, "n_components": 2},
    )

    params_path = tmp_path / "params_clustering.json"
    params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "clustering_methods": ["kmeans"],
        "params_file": str(params_path),
        "output_root": str(tmp_path / "cl_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "viz_embedding_path": str(viz_dir),
        "run_notes": None,
    }
    cfg_path = tmp_path / "cl_param_mismatch.json"
    cfg_path.write_text(json.dumps(cfg))

    with caplog.at_level(logging.ERROR):
        assert clustering.main(["--config", str(cfg_path)]) == 1
    assert "n_neighbors" in caplog.text and "15" in caplog.text and "30" in caplog.text
