"""Unit tests for src/analysis/clustering_tuning_evaluations.py."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_tuning_analysis import ClusteringTuningRun
from src.analysis.clustering_tuning_evaluations import (
    EVALUATIONS,
    GENERAL,
    evaluations_for,
    load_evaluation_settings,
    refuse_existing,
    require_methods_declared,
    run_evaluations,
    validate_tuning_evaluations_block,
)
from src.utils.artifacts import save_matrix

REGISTRY_FILE = Path("config/registry/clustering_evaluations.json")
VALID = json.loads(REGISTRY_FILE.read_text())


def _three_blobs() -> np.ndarray:
    rng = np.random.default_rng(0)
    return np.vstack([rng.normal(loc=center, scale=0.3, size=(15, 2)) for center in ([0, 0], [8, 8], [0, 8])])


def _agglomerative_run(tmp_path: Path) -> ClusteringTuningRun:
    matrix_dir = tmp_path / "matrix"
    X = _three_blobs()
    metadata = pd.DataFrame({"subject_id": [f"sub-STUNIPD{i:04d}" for i in range(len(X))], "dataset": "siteA"})
    save_matrix(matrix_dir, X, metadata, ["# blobs"], overwrite=False)
    rows = [
        {"n_clusters": k, "linkage": linkage, "metric": "euclidean", "silhouette": 0.5, "davies_bouldin": 1.0, "calinski_harabasz": 10.0}
        for k in (2, 3)
        for linkage in ("ward", "average")
    ]
    labels = {f"n_clusters={r['n_clusters']},linkage={r['linkage']},metric=euclidean": np.repeat(np.arange(r["n_clusters"]), 45 // r["n_clusters"] + 1)[:45] for r in rows}
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    return ClusteringTuningRun(run_dir, "agglomerative", matrix_dir, pd.DataFrame(rows), labels)


def _density_run(tmp_path: Path, method: str = "hdbscan") -> ClusteringTuningRun:
    rows = [{"min_cluster_size": s, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.5, "davies_bouldin": 1.0} for s in (5, 10)]
    labels = {"min_cluster_size=5,min_samples=5": np.repeat([0, 1, 2, 3], 5), "min_cluster_size=10,min_samples=5": np.repeat([0, 1], 10)}
    return ClusteringTuningRun(tmp_path, method, Path("m"), pd.DataFrame(rows), labels)


def _settings() -> dict[str, dict]:
    return load_evaluation_settings(REGISTRY_FILE)


def test_the_shipped_registry_file_lists_exactly_the_registered_evaluations():
    assert set(_settings()) == set(EVALUATIONS)


def test_every_evaluation_applies_to_known_clustering_methods_only():
    for name, spec in EVALUATIONS.items():
        assert spec.methods <= set(CLUSTERING_METHODS), name


@pytest.mark.parametrize(
    "content, message",
    [
        ("not json", "not valid JSON"),
        ("[]", "must be an object"),
        (json.dumps({}), "missing"),
        (json.dumps({**VALID, "invented": {}}), "unknown"),
        (json.dumps({**VALID, "k_curves": {"dpi": 3}}), "takes no settings"),
        (json.dumps({**VALID, "dendrogram_jump": {"k_range": {"min": 2, "max": 30}}}), "takes no settings"),  # the k is each combination's own
        (json.dumps({**VALID, "dbcv_curves": {"max_noise_fraction": 0.1}}), "takes no settings"),
        (json.dumps({**VALID, "noise_filtered_curves": {}}), "unknown"),  # the noise limit is gone from the registry
    ],
)
def test_a_bad_registry_file_raises(tmp_path, content, message):
    path = tmp_path / "evaluations.json"
    path.write_text(content)

    with pytest.raises(ValueError, match=message):
        load_evaluation_settings(path)


def test_a_missing_registry_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="evaluations registry not found"):
        load_evaluation_settings(tmp_path / "absent.json")


def test_a_valid_block_keeps_its_keys_and_order():
    block = validate_tuning_evaluations_block(
        {"general": [], "agglomerative": ["dendrogram_jump", "k_curves"], "hdbscan_soft": ["density_metrics"]}
    )

    assert block == {"general": (), "agglomerative": ("dendrogram_jump", "k_curves"), "hdbscan_soft": ("density_metrics",)}


@pytest.mark.parametrize(
    "block, message",
    [
        ([], "must be an object"),
        ({"agglomerative": []}, "needs a 'general' key"),
        ({"general": [], "kmeanz": []}, "unknown key"),
        ({"general": "k_curves"}, "must be a list"),
        ({"general": [], "agglomerative": ["k_curves", "k_curves"]}, "duplicate"),
        ({"general": [], "agglomerative": ["invented"]}, "unknown clustering tuning evaluation"),
        ({"general": [], "hdbscan": ["cophenetic_correlation"]}, "does not apply"),
        ({"general": [], "hdbscan": ["dunn_index"]}, "does not apply"),
        ({"general": [], "hdbscan_soft": ["largest_cluster_share"]}, "does not apply"),
        ({"general": ["density_metrics"]}, "does not apply to every method"),
    ],
)
def test_a_bad_block_raises(block, message):
    with pytest.raises(ValueError, match=message):
        validate_tuning_evaluations_block(block)


def test_every_method_the_block_is_applied_to_needs_its_own_key():
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": []})

    require_methods_declared(block, ("agglomerative",))
    with pytest.raises(ValueError, match=r"no key for \['hdbscan'\]"):
        require_methods_declared(block, ("agglomerative", "hdbscan"))


def test_evaluations_for_lists_the_general_ones_before_the_methods_own():
    assert evaluations_for({"general": ("g",), "hdbscan": ("a", "b")}, "hdbscan") == ("g", "a", "b")


def test_refuse_existing_names_the_files_and_overwrite_lets_them_through(tmp_path):
    (tmp_path / "a.csv").write_text("x")

    with pytest.raises(FileExistsError, match=r"\['a.csv'\].*overwrite=true"):
        refuse_existing([tmp_path / "a.csv", tmp_path / "b.csv"], overwrite=False)
    refuse_existing([tmp_path / "a.csv"], overwrite=True)
    refuse_existing([tmp_path / "b.csv"], overwrite=False)


def _blobs(n_subjects: int = 20) -> np.ndarray:
    rng = np.random.default_rng(0)
    return np.repeat([0.0, 6.0, 12.0], -(-n_subjects // 3))[:n_subjects, None] + rng.normal(scale=0.3, size=(n_subjects, 3))


DENSITY_BLOCK = {"general": [], "hdbscan": ["density_metrics", "tuning_heatmaps", "dbcv_curves"]}


def test_density_evaluations_write_their_files_and_nothing_else(tmp_path):
    run = _density_run(tmp_path)
    block = validate_tuning_evaluations_block(DENSITY_BLOCK)

    written = run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())

    assert sorted(path.name for path in written) == ["dbcv_curves.png", "tuning_plot.png", "tuning_results.csv"]
    metrics = pd.read_csv(tmp_path / "tuning_results.csv")
    assert metrics["n_clusters_found"].tolist() == [4, 2]  # the run did not write it: it comes from the labels
    assert not (tmp_path / "density_metrics.csv").exists()
    assert metrics["dbcv"].notna().all()
    for name in ("dbcv_curves.png", "tuning_plot.png"):
        assert (tmp_path / name).stat().st_size > 0


def test_the_figures_of_a_soft_run_get_one_file_per_selection_method(tmp_path):
    run = _density_run(tmp_path, "hdbscan_soft")
    run = ClusteringTuningRun(
        tmp_path, "hdbscan_soft", run.input_path,
        pd.concat([run.results.assign(cluster_selection_method=m) for m in ("eom", "leaf")], ignore_index=True),
        {f"{key},cluster_selection_method={m}": labels for m in ("eom", "leaf") for key, labels in run.labels.items()},
    )
    block = validate_tuning_evaluations_block({"general": [], "hdbscan_soft": DENSITY_BLOCK["hdbscan"]})

    written = run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())

    assert sorted(path.name for path in written) == [
        "dbcv_curves_cluster_selection_method=eom.png", "dbcv_curves_cluster_selection_method=leaf.png",
        "tuning_plot_cluster_selection_method=eom.png", "tuning_plot_cluster_selection_method=leaf.png", "tuning_results.csv",
    ]


def test_the_figures_read_the_density_columns_so_density_metrics_must_be_declared_before_them(tmp_path):
    run = _density_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["dbcv_curves"]})

    with pytest.raises(ValueError, match=r"no column\(s\).*run the `density_metrics` evaluation"):
        run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())


def test_density_metrics_keeps_the_sweeps_own_columns_and_adds_only_its_two(tmp_path):
    run = _density_run(tmp_path)
    run.results["n_clusters_found"] = [4, 2]  # what the sweep wrote
    run.results["membership_mean"] = [0.7, 0.8]  # comes from the fit: no evaluation can recompute it
    _write_results(run)
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["density_metrics"]})

    run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())

    stored = pd.read_csv(tmp_path / "tuning_results.csv")
    assert list(stored.columns)[-2:] == ["largest_cluster_share", "dbcv"]  # appended after the sweep's columns, which keep their place
    assert stored["membership_mean"].tolist() == [0.7, 0.8] and stored["n_clusters_found"].tolist() == [4, 2]
    assert stored["dbcv"].notna().all()


def test_density_metrics_stops_when_the_runs_cluster_count_contradicts_the_labels_and_leaves_the_file(tmp_path):
    run = _density_run(tmp_path)
    run.results["n_clusters_found"] = [4, 3]  # the second combination has 2 clusters in the stored labels
    _write_results(run)
    before = (tmp_path / "tuning_results.csv").read_bytes()
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["density_metrics"]})

    with pytest.raises(ValueError, match="n_clusters_found"):
        run_evaluations(block, _settings(), run, overwrite=True, matrix=_blobs())

    assert (tmp_path / "tuning_results.csv").read_bytes() == before


def test_an_evaluation_not_in_the_block_is_not_run(tmp_path):
    run = _density_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["density_metrics"]})

    run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())

    assert not (tmp_path / "dbcv_curves.png").exists()


def test_there_is_no_noise_limit_a_run_with_much_noise_still_gets_its_figures(tmp_path):
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.9}]
    labels = {"min_cluster_size=5,min_samples=5": np.array([0] * 2 + [1] * 2 + [-1] * 16)}
    run = ClusteringTuningRun(tmp_path, "hdbscan", Path("m"), pd.DataFrame(rows), labels)
    block = validate_tuning_evaluations_block(DENSITY_BLOCK)

    written = run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())

    assert "dbcv_curves.png" in [path.name for path in written]


def test_a_second_run_without_overwrite_stops_and_overwrite_replaces(tmp_path):
    run = _density_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["density_metrics"]})
    run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())

    with pytest.raises(FileExistsError, match="overwrite=true"):
        run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs())
    run_evaluations(block, _settings(), run, overwrite=True, matrix=_blobs())


def test_a_block_with_no_key_for_the_runs_method_raises(tmp_path):
    run = _density_run(tmp_path, "hdbscan_soft")
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": []})

    with pytest.raises(ValueError, match="no key for"):
        run_evaluations(block, _settings(), run, overwrite=False)


def _write_results(run: ClusteringTuningRun) -> None:
    run.results.to_csv(run.run_dir / "tuning_results.csv", index=False)


def test_agglomerative_evaluations_read_the_matrix_of_the_run_and_share_a_cache(tmp_path):
    run = _agglomerative_run(tmp_path)
    block = validate_tuning_evaluations_block(
        {"general": [], "agglomerative": ["cophenetic_correlation", "dendrogram_jump", "linkage_agreement"]}
    )

    written = run_evaluations(block, _settings(), run, overwrite=False)

    # the jump is a column of tuning_results.csv, the two tables with another key are files of their own
    assert [path.name for path in written] == ["cophenetic_correlation.csv", "tuning_results.csv", "linkage_agreement.csv"]
    stored = pd.read_csv(run.run_dir / "tuning_results.csv")
    assert len(stored) == 4 and stored["jump"].notna().all()
    assert set(pd.read_csv(run.run_dir / "cophenetic_correlation.csv")["linkage"]) == {"ward", "average"}
    assert not (run.run_dir / "dendrogram_jump.csv").exists()


def test_the_dunn_and_largest_share_evaluations_add_their_columns_to_tuning_results_and_keep_the_others(tmp_path):
    run = _agglomerative_run(tmp_path)
    run.results["marker"] = "kept"
    _write_results(run)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["largest_cluster_share", "dunn_index"]})

    written = run_evaluations(block, _settings(), run, overwrite=False)

    assert [path.name for path in written] == ["tuning_results.csv", "tuning_results.csv"]
    stored = pd.read_csv(run.run_dir / "tuning_results.csv")
    assert list(stored.columns) == [*pd.read_csv(run.run_dir / "tuning_results.csv", nrows=0).columns[:-2], "largest_cluster_share", "dunn"]
    assert len(stored) == 4 and stored["largest_cluster_share"].between(0, 1).all() and stored["dunn"].notna().all()
    assert stored["marker"].eq("kept").all() and stored["silhouette"].eq(0.5).all()
    assert not list(run.run_dir.glob("*.tmp")) and not (run.run_dir / "dunn_index.csv").exists()
    assert run.results["dunn"].notna().all()  # the evaluations after it, and the report, see the new columns


def test_a_per_combination_evaluation_refuses_to_replace_its_column_without_overwrite_and_replaces_only_that_column(tmp_path):
    run = _agglomerative_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["dunn_index"]})
    run_evaluations(block, _settings(), run, overwrite=False)
    stored = pd.read_csv(run.run_dir / "tuning_results.csv")
    run.results["dunn"] = -1.0  # a stale value the evaluation has to correct
    run.results["silhouette"] = 7.0  # a column it does not own: it must come out of the file as it is in memory

    with pytest.raises(FileExistsError, match=r"already has the column\(s\) \['dunn'\].*overwrite=true"):
        run_evaluations(block, _settings(), run, overwrite=False)
    assert pd.read_csv(run.run_dir / "tuning_results.csv").equals(stored)  # refused: nothing touched

    run_evaluations(block, _settings(), run, overwrite=True)

    replaced = pd.read_csv(run.run_dir / "tuning_results.csv")
    assert replaced["dunn"].gt(0).all()  # recomputed, no longer -1
    assert replaced["silhouette"].eq(7.0).all() and list(replaced.columns) == list(stored.columns)


def test_a_per_combination_evaluation_checks_the_file_before_computing_the_table(tmp_path, monkeypatch):
    import src.analysis.clustering_tuning_evaluations as evaluations

    run = _agglomerative_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["dunn_index"]})
    run_evaluations(block, _settings(), run, overwrite=False)

    def fail(*args, **kwargs):
        raise AssertionError("the table was computed before the column was checked")

    monkeypatch.setattr(evaluations, "dunn_table", fail)

    with pytest.raises(FileExistsError):
        run_evaluations(block, _settings(), run, overwrite=False)


def _two_metric_run(tmp_path: Path) -> ClusteringTuningRun:
    """ward and average for euclidean, average only for cosine (ward + cosine is invalid and was never swept)."""
    rows = [
        {"n_clusters": k, "linkage": linkage, "metric": metric}
        for k in (2, 3)
        for linkage, metric in (("ward", "euclidean"), ("average", "euclidean"), ("average", "cosine"))
    ]
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    return ClusteringTuningRun(run_dir, "agglomerative", Path("does_not_exist"), pd.DataFrame(rows), {})


def test_the_dendrograms_evaluation_writes_one_file_per_metric_of_the_run(tmp_path):
    run = _two_metric_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["dendrograms"]})

    written = run_evaluations(block, _settings(), run, overwrite=False, matrix=_three_blobs())

    assert [path.name for path in written] == ["dendrogram_metric=euclidean.png", "dendrogram_metric=cosine.png"]
    assert all(path.stat().st_size > 0 for path in written)


def test_the_dendrograms_evaluation_draws_the_number_of_merges_the_registry_asks_for(tmp_path):
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["dendrograms"]})
    sizes = {}
    for last_merges in (5, 30):
        run = _two_metric_run(tmp_path / str(last_merges))
        settings = {**_settings(), "dendrograms": {"truncate_last_p": last_merges}}
        written = run_evaluations(block, settings, run, overwrite=False, matrix=_three_blobs())
        sizes[last_merges] = written[0].read_bytes()

    assert sizes[5] != sizes[30]


def test_the_dendrograms_evaluation_refuses_to_replace_its_files_without_overwrite(tmp_path):
    run = _two_metric_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["dendrograms"]})
    run_evaluations(block, _settings(), run, overwrite=False, matrix=_three_blobs())

    with pytest.raises(FileExistsError, match="dendrogram_metric=cosine.png"):
        run_evaluations(block, _settings(), run, overwrite=False, matrix=_three_blobs())
    run_evaluations(block, _settings(), run, overwrite=True, matrix=_three_blobs())


@pytest.mark.parametrize("settings", [{}, {"truncate_last_p": 1}, {"truncate_last_p": 30.0}, {"truncate_last_p": True}, {"truncate_last_p": 30, "other": 1}])
def test_the_dendrograms_registry_entry_needs_exactly_an_integer_number_of_merges_of_at_least_two(settings, tmp_path):
    bad = tmp_path / "registry.json"
    bad.write_text(json.dumps({**VALID, "dendrograms": settings}))

    with pytest.raises(ValueError, match="dendrograms"):
        load_evaluation_settings(bad)


def test_a_matrix_the_caller_holds_is_used_instead_of_the_run_input_path(tmp_path):
    run = _agglomerative_run(tmp_path)
    run = ClusteringTuningRun(run.run_dir, run.method, tmp_path / "does_not_exist", run.results, run.labels)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["cophenetic_correlation"]})

    written = run_evaluations(block, _settings(), run, overwrite=False, matrix=_three_blobs())

    assert [path.name for path in written] == ["cophenetic_correlation.csv"]


def test_internal_metrics_rewrites_the_columns_it_owns_only_with_overwrite_and_keeps_the_others(tmp_path):
    run = _agglomerative_run(tmp_path)
    run.results["silhouette"] = 9.0  # a stale value the evaluation has to correct
    run.results["noise_fraction"] = 0.0
    run.results["marker"] = "kept"
    _write_results(run)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["internal_metrics"]})

    with pytest.raises(FileExistsError, match="overwrite=true"):
        run_evaluations(block, _settings(), run, overwrite=False, matrix=_three_blobs())
    assert pd.read_csv(run.run_dir / "tuning_results.csv")["silhouette"].eq(9.0).all()  # refused: nothing touched

    written = run_evaluations(block, _settings(), run, overwrite=True, matrix=_three_blobs())

    assert [path.name for path in written] == ["tuning_results.csv"]
    stored = pd.read_csv(run.run_dir / "tuning_results.csv")
    assert stored["silhouette"].between(-1, 1).all()  # recomputed, no longer 9.0
    assert stored["marker"].eq("kept").all()
    assert list(stored.columns) == list(run.results.columns)
    assert not list(run.run_dir.glob("*.tmp"))  # the temporary file was renamed over the original
    assert run.results["silhouette"].between(-1, 1).all()  # the evaluations after it see the new values


def test_internal_metrics_does_not_apply_to_a_method_it_cannot_recompute():
    with pytest.raises(ValueError, match="does not apply"):
        validate_tuning_evaluations_block({"general": [], "kmeans": ["internal_metrics"]})


def _png_width(path: Path) -> int:
    import matplotlib.image as mpimg

    return mpimg.imread(path).shape[1]


@pytest.mark.parametrize(
    "evaluation, method, figure",
    [
        ("k_curves", "agglomerative", "k_curves_metric=euclidean.png"),
        ("dendrograms", "agglomerative", "dendrogram_metric=euclidean.png"),
        ("tuning_heatmaps", "hdbscan", "tuning_plot.png"),
        ("dbcv_curves", "hdbscan", "dbcv_curves.png"),
    ],
)
def test_every_figure_of_an_evaluation_is_saved_at_figure_dpi(tmp_path, monkeypatch, evaluation, method, figure):
    import src.analysis.clustering_tuning_evaluations as evaluations

    widths = {}
    for dpi in (50, 100):
        monkeypatch.setattr(evaluations, "FIGURE_DPI", dpi)
        folder = tmp_path / str(dpi)
        folder.mkdir()
        if method == "agglomerative":
            run = _two_metric_run(folder)
            run = ClusteringTuningRun(
                run.run_dir, run.method, run.input_path,
                pd.DataFrame([{"n_clusters": k, "linkage": linkage, "metric": "euclidean", "silhouette": 0.5, "davies_bouldin": 1.0}
                              for k in (2, 3) for linkage in ("ward", "average")]),
                run.labels,
            )
        else:
            run = _density_run(folder)
        block = validate_tuning_evaluations_block({"general": [], method: ["density_metrics", evaluation] if method == "hdbscan" else [evaluation]})
        run_evaluations(block, _settings(), run, overwrite=False, matrix=_blobs() if method == "hdbscan" else _three_blobs())
        widths[dpi] = _png_width(run.run_dir / figure)

    assert widths[100] == pytest.approx(2 * widths[50], abs=3)
