"""Integration test: analyze_clustering_tuning.py chained onto a real clustering.py fine-tuning run."""

import json

import numpy as np
import pandas as pd
import pytest

from src.pipeline import analyze_clustering_tuning, clustering
from src.utils.artifacts import save_matrix

N_PER_BLOB = 20


def _blobs_matrix(tmp_path):
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(loc=center, scale=0.3, size=(N_PER_BLOB, 2)) for center in ([0, 0], [8, 8], [0, 8])])
    ids = [f"sub-STUNIPD{i:04d}" for i in range(len(X))]
    metadata = pd.DataFrame({"subject_id": ids, "dataset": ["siteA"] * len(X)})
    matrix_dir = tmp_path / "blobs"
    save_matrix(matrix_dir, X, metadata, ["# blobs fixture"], overwrite=False)
    return matrix_dir


def _run_tuning(tmp_path, monkeypatch, method, entry):
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")
    params_path = tmp_path / f"params_{method}.json"
    params_path.write_text(json.dumps({method: entry}))
    output_root = tmp_path / "cl_out"
    config = {
        "project": "testproj",
        "input_path": str(_blobs_matrix(tmp_path)),
        "reduction_method": "raw",
        "clustering_methods": [method],
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune",
        "overwrite": False,
        "fine_tuning": True,
        "reduced_data": False,
        "save_tuning_clusterings": True,
        "run_notes": None,
    }
    config_path = tmp_path / "cl.json"
    config_path.write_text(json.dumps(config))
    assert clustering.main(["--config", str(config_path)]) == 0
    return next(p for p in (output_root / "tuning" / method / "raw").iterdir() if p.is_dir())


def _analyze(tmp_path, monkeypatch, tuning_dir, overwrite=False):
    monkeypatch.setattr(analyze_clustering_tuning, "LOGS_ROOT", tmp_path / "an_logs")
    config = {
        "tuning_dir": str(tuning_dir),
        "overwrite": overwrite,
        "k_range": {"min": 3, "max": 6},
        "curves_max_noise_fraction": 0.5,
        "usable": {"min_clusters": 3, "max_clusters": 30, "max_noise_fraction": 0.25, "max_largest_cluster_share": 0.6},
    }
    config_path = tmp_path / "an.json"
    config_path.write_text(json.dumps(config))
    return analyze_clustering_tuning.main(["--config", str(config_path)])


def test_agglomerative_run_gets_cophenetic_jump_and_curves(tmp_path, monkeypatch):
    entry = {
        "params": {"n_clusters": 3},
        "tuning_grid": {"n_clusters": [2, 3, 4], "linkage": ["ward", "average"], "metric": ["euclidean", "cosine"]},
    }
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "agglomerative", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0

    cophenetic = pd.read_csv(tuning_dir / "cophenetic_correlation.csv")
    assert set(zip(cophenetic["metric"], cophenetic["linkage"])) == {("euclidean", "ward"), ("euclidean", "average"), ("cosine", "average")}
    jump = pd.read_csv(tuning_dir / "dendrogram_jump.csv")
    assert set(jump["n_clusters"]) == {3, 4, 5, 6}
    # three blobs: the sharpest ward cut is at 3 clusters
    ward = jump[(jump["metric"] == "euclidean") & (jump["linkage"] == "ward")].set_index("n_clusters")["jump"]
    assert ward.idxmax() == 3
    for metric in ("euclidean", "cosine"):
        assert (tuning_dir / f"k_curves_metric={metric}.png").stat().st_size > 0


def test_hdbscan_run_gets_candidates_and_filtered_curves(tmp_path, monkeypatch):
    entry = {
        "params": {"min_cluster_size": 10, "min_samples": 5},
        "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]},
    }
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0

    candidates = pd.read_csv(tuning_dir / "candidates.csv")
    assert len(candidates) == 4
    assert {"largest_cluster_share", "usable", "n_clusters_found"} <= set(candidates.columns)
    # three blobs of equal size are found whole, with a third of the subjects in each
    assert candidates["n_clusters_found"].eq(3).all()
    assert candidates["largest_cluster_share"].round(2).eq(0.33).all()
    assert candidates["usable"].all()
    assert (tuning_dir / "noise_filtered_curves.png").stat().st_size > 0


def test_a_second_run_without_overwrite_stops_and_leaves_the_files(tmp_path, monkeypatch, caplog):
    entry = {"params": {"min_cluster_size": 10, "min_samples": 5}, "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)
    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0
    before = (tuning_dir / "candidates.csv").read_bytes()

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 1
    assert "overwrite=true" in caplog.text
    assert (tuning_dir / "candidates.csv").read_bytes() == before

    assert _analyze(tmp_path, monkeypatch, tuning_dir, overwrite=True) == 0


def test_a_folder_that_is_not_a_clustering_tuning_run_stops(tmp_path, monkeypatch, caplog):
    assert _analyze(tmp_path, monkeypatch, tmp_path / "nothing_here") == 1
    assert "tuning config not found" in caplog.text


def test_adp_runs_are_refused(tmp_path, monkeypatch, caplog):
    run_dir = tmp_path / "adp_run"
    run_dir.mkdir()
    (run_dir / "config.md").write_text('# t\n\n```json\n{"clustering_method": "adp", "input_path": "m", "fine_tuning": true}\n```\n')

    assert _analyze(tmp_path, monkeypatch, run_dir) == 1
    assert "adp is not analysed here" in caplog.text


def test_hdbscan_run_with_all_noise_still_gets_candidates_without_curves(tmp_path, monkeypatch):
    """Regression: 8 of 58 real tuning runs have every combination above the noise limit; the analysis used to
    stop without writing anything for them."""
    entry = {"params": {"min_cluster_size": 30, "min_samples": 3}, "tuning_grid": {"min_cluster_size": [30, 40], "min_samples": [3]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0

    candidates = pd.read_csv(tuning_dir / "candidates.csv")
    assert candidates["noise_fraction"].eq(1.0).all()
    assert not candidates["usable"].any()
    assert not (tuning_dir / "noise_filtered_curves.png").exists()
