"""Integration test: evaluate_clustering_tuning.py chained onto a real clustering.py fine-tuning run."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.pipeline import evaluate_clustering_tuning, clustering
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


REGISTRY = json.loads(Path("config/registry/clustering_evaluations.json").read_text())
EVALUATIONS_BY_METHOD = {
    "agglomerative": ["k_curves", "cophenetic_correlation", "dendrogram_jump", "linkage_agreement", "largest_cluster_share", "dunn_index"],
    "hdbscan": ["density_metrics", "tuning_heatmaps", "dbcv_curves"],
}


def _evaluations_file(tmp_path):
    """The shipped registry with the k range these tiny fixtures need."""
    path = tmp_path / "evaluations.json"
    settings = {**REGISTRY, "dendrogram_jump": {"k_range": {"min": 3, "max": 6}}}
    path.write_text(json.dumps(settings))
    return path


def _run_tuning(tmp_path, monkeypatch, method, entry, evaluations=(), write_report=False):
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
        "evaluations_file": str(_evaluations_file(tmp_path)),
        "tuning_evaluations": {"general": [], method: list(evaluations)},
        "write_report": write_report,
        "run_notes": None,
    }
    config_path = tmp_path / "cl.json"
    config_path.write_text(json.dumps(config))
    assert clustering.main(["--config", str(config_path)]) == 0
    return next(p for p in (output_root / "tuning" / method / "raw").iterdir() if p.is_dir())


def _analyze(tmp_path, monkeypatch, tuning_dir, overwrite=False, evaluations=None, write_report=True):
    monkeypatch.setattr(evaluate_clustering_tuning, "LOGS_ROOT", tmp_path / "an_logs")
    config = {
        "tuning_dir": str(tuning_dir),
        "overwrite": overwrite,
        "evaluations_file": str(_evaluations_file(tmp_path)),
        "tuning_evaluations": {"general": [], **(EVALUATIONS_BY_METHOD if evaluations is None else evaluations)},
        "write_report": write_report,
    }
    config_path = tmp_path / "an.json"
    config_path.write_text(json.dumps(config))
    return evaluate_clustering_tuning.main(["--config", str(config_path)])


def test_agglomerative_run_gets_cophenetic_jump_and_curves(tmp_path, monkeypatch):
    entry = {
        "params": {"n_clusters": 3},
        "tuning_grid": {"n_clusters": [2, 3, 4], "linkage": ["ward", "average", "single"], "metric": ["euclidean", "cosine"]},
    }
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "agglomerative", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0

    cophenetic = pd.read_csv(tuning_dir / "cophenetic_correlation.csv")
    assert set(zip(cophenetic["metric"], cophenetic["linkage"])) == {
        ("euclidean", "ward"), ("euclidean", "average"), ("euclidean", "single"), ("cosine", "average"), ("cosine", "single"),
    }
    jump = pd.read_csv(tuning_dir / "dendrogram_jump.csv")
    assert set(jump["n_clusters"]) == {3, 4, 5, 6}
    # three blobs: the sharpest ward cut is at 3 clusters
    ward = jump[(jump["metric"] == "euclidean") & (jump["linkage"] == "ward")].set_index("n_clusters")["jump"]
    assert ward.idxmax() == 3
    for metric in ("euclidean", "cosine"):
        assert (tuning_dir / f"k_curves_metric={metric}.png").stat().st_size > 0
        assert not (tuning_dir / f"k_curves_single_metric={metric}.png").exists()  # single is not drawn
    report = (tuning_dir / "report.md").read_text()
    assert "## metric = euclidean" in report and "## metric = cosine" in report
    assert "### linkage = single" in report and "k_curves_single" not in report
    agreement = pd.read_csv(tuning_dir / "linkage_agreement.csv")
    assert set(zip(agreement["linkage_a"], agreement["linkage_b"])) == {
        ("ward", "average"), ("ward", "single"), ("average", "single")  # euclidean has ward; cosine only average and single
    } | {("average", "single")}
    assert agreement["ari"].between(-1, 1).all() and "### Accordo tra linkage (ARI)" in report
    assert report.count("### Cophenetic correlation") == 2 and report.count("### Salto del dendrogramma") == 2  # one per metric
    assert "| 3 | " in report.split("### Salto del dendrogramma")[1]  # k_range 3-6 of this config


def test_hdbscan_run_gets_density_metrics_with_dbcv_the_map_and_the_curves(tmp_path, monkeypatch):
    entry = {
        "params": {"min_cluster_size": 10, "min_samples": 5},
        "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]},
    }
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0

    metrics = pd.read_csv(tuning_dir / "density_metrics.csv")
    assert len(metrics) == 4
    assert {"largest_cluster_share", "n_clusters_found", "dbcv"} <= set(metrics.columns)
    assert "usable" not in metrics.columns
    # three blobs of equal size are found whole, with a third of the subjects in each
    assert metrics["n_clusters_found"].eq(3).all()
    assert metrics["largest_cluster_share"].round(2).eq(0.33).all()
    assert metrics["dbcv"].gt(0.5).all()  # three well-separated blobs
    report = (tuning_dir / "report.md").read_text()
    assert "## min_samples = 3" in report and "## min_samples = 5" in report  # one table per min_samples
    assert "| min_cluster_size | n_clusters_found | noise_fraction | largest_cluster_share | dbcv |" in report
    for name in ("dbcv_curves.png", "tuning_plot.png"):
        assert (tuning_dir / name).stat().st_size > 0
        assert f"({name})" in report


def test_a_second_run_without_overwrite_stops_and_leaves_the_files(tmp_path, monkeypatch, caplog):
    entry = {"params": {"min_cluster_size": 10, "min_samples": 5}, "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)
    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0
    before = (tuning_dir / "density_metrics.csv").read_bytes()

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 1
    assert "overwrite=true" in caplog.text
    assert (tuning_dir / "density_metrics.csv").read_bytes() == before

    assert _analyze(tmp_path, monkeypatch, tuning_dir, overwrite=True) == 0


def test_a_folder_that_is_not_a_clustering_tuning_run_stops(tmp_path, monkeypatch, caplog):
    assert _analyze(tmp_path, monkeypatch, tmp_path / "nothing_here") == 1
    assert "tuning config not found" in caplog.text


def _adp_run(tmp_path):
    run_dir = tmp_path / "adp_run"
    run_dir.mkdir()
    (run_dir / "config.md").write_text('# t\n\n```json\n{"clustering_method": "adp", "input_path": "m", "fine_tuning": true}\n```\n')
    return run_dir


def test_adp_run_gets_only_the_report(tmp_path, monkeypatch):
    run_dir = _adp_run(tmp_path)
    pd.DataFrame(
        {"metric": ["dice", "dice", "euclidean"], "Z": [1.0, 2.5, 1.0], "n_clusters_found": [30.0, 12.0, 2.0],
         "largest_cluster_share": [0.2, 0.3, 0.98], "silhouette": [0.03, 0.05, -0.2]}
    ).to_csv(run_dir / "tuning_results.csv", index=False)

    assert _analyze(tmp_path, monkeypatch, run_dir) == 0

    report = (run_dir / "report.md").read_text()
    assert "## metric = dice" in report and "## metric = euclidean" in report
    assert sorted(path.name for path in run_dir.iterdir()) == ["config.md", "report.md", "tuning_results.csv"]


def test_adp_run_without_tuning_results_stops(tmp_path, monkeypatch, caplog):
    assert _analyze(tmp_path, monkeypatch, _adp_run(tmp_path)) == 1
    assert "tuning_results.csv" in caplog.text


def test_hdbscan_run_with_all_noise_still_gets_density_metrics_with_the_dbcv_undefined(tmp_path, monkeypatch):
    """Regression: 8 of 58 real tuning runs have every combination all noise; the analysis used to stop without
    writing anything for them. There is no noise limit any more: the figures are drawn, the DBCV is undefined, not 0."""
    entry = {"params": {"min_cluster_size": 30, "min_samples": 3}, "tuning_grid": {"min_cluster_size": [30, 40], "min_samples": [3]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir) == 0

    metrics = pd.read_csv(tuning_dir / "density_metrics.csv")
    assert metrics["noise_fraction"].eq(1.0).all()
    assert metrics["dbcv"].isna().all()
    assert (tuning_dir / "dbcv_curves.png").stat().st_size > 0
    assert "- **DBCV**: mai definito" in (tuning_dir / "report.md").read_text()


def test_a_sweep_that_declares_the_evaluations_writes_the_files_a_later_analysis_writes(tmp_path, monkeypatch):
    """The sweep and evaluate_clustering_tuning run the same function: same files, same numbers."""
    entry = {"params": {"min_cluster_size": 10, "min_samples": 5}, "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry, evaluations=EVALUATIONS_BY_METHOD["hdbscan"])
    by_the_sweep = (tuning_dir / "density_metrics.csv").read_bytes()
    assert (tuning_dir / "dbcv_curves.png").stat().st_size > 0
    assert "Evaluations applied: ['density_metrics', 'tuning_heatmaps', 'dbcv_curves']" in (tuning_dir / "config.md").read_text()

    assert _analyze(tmp_path, monkeypatch, tuning_dir, overwrite=True) == 0

    assert (tuning_dir / "density_metrics.csv").read_bytes() == by_the_sweep  # the DBCV included


def test_the_report_needs_the_evaluation_files_and_says_which_is_missing(tmp_path, monkeypatch, caplog):
    entry = {"params": {"min_cluster_size": 10, "min_samples": 5}, "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir, evaluations={"hdbscan": []}) == 1

    assert "density_metrics.csv" in caplog.text and "not found" in caplog.text
    assert not (tuning_dir / "report.md").exists()


def test_without_a_report_only_the_listed_evaluations_run(tmp_path, monkeypatch):
    entry = {"params": {"min_cluster_size": 10, "min_samples": 5}, "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry)

    assert _analyze(tmp_path, monkeypatch, tuning_dir, evaluations={"hdbscan": ["density_metrics"]}, write_report=False) == 0

    assert (tuning_dir / "density_metrics.csv").is_file()
    assert not (tuning_dir / "dbcv_curves.png").exists() and not (tuning_dir / "report.md").exists()


def test_a_sweep_with_write_report_writes_the_report_a_later_analysis_writes(tmp_path, monkeypatch):
    entry = {"params": {"min_cluster_size": 10, "min_samples": 5}, "tuning_grid": {"min_cluster_size": [10, 15], "min_samples": [3, 5]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "hdbscan", entry, evaluations=EVALUATIONS_BY_METHOD["hdbscan"], write_report=True)
    by_the_sweep = (tuning_dir / "report.md").read_bytes()
    assert b"## min_samples = 3" in by_the_sweep

    assert _analyze(tmp_path, monkeypatch, tuning_dir, overwrite=True) == 0

    assert (tuning_dir / "report.md").read_bytes() == by_the_sweep


def test_internal_metrics_run_later_reproduces_what_the_sweep_wrote_and_needs_overwrite(tmp_path, monkeypatch, caplog):
    """The sweep and the evaluation score with the same functions: rewriting tuning_results.csv from the stored labels
    changes no value of an agglomerative run, and it is refused without overwrite=true."""
    entry = {"params": {"n_clusters": 3}, "tuning_grid": {"n_clusters": [2, 3], "linkage": ["ward", "average"], "metric": ["euclidean", "cosine"]}}
    tuning_dir = _run_tuning(tmp_path, monkeypatch, "agglomerative", entry)
    by_the_sweep = pd.read_csv(tuning_dir / "tuning_results.csv")
    evaluations = {"agglomerative": ["internal_metrics"]}

    assert _analyze(tmp_path, monkeypatch, tuning_dir, evaluations=evaluations, write_report=False) == 1
    assert "overwrite=true" in caplog.text and pd.read_csv(tuning_dir / "tuning_results.csv").equals(by_the_sweep)

    assert _analyze(tmp_path, monkeypatch, tuning_dir, overwrite=True, evaluations=evaluations, write_report=False) == 0

    rewritten = pd.read_csv(tuning_dir / "tuning_results.csv")
    pd.testing.assert_frame_equal(rewritten, by_the_sweep, check_exact=False, rtol=1e-9)
    assert rewritten["calinski_harabasz"].isna().eq(rewritten["metric"] == "cosine").all()  # euclidean-only, undefined under cosine
