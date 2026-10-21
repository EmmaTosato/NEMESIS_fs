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
        (json.dumps({**VALID, "dendrogram_jump": {"k_range": {"min": 5, "max": 3}}}), "greater than"),
        (json.dumps({**VALID, "dendrogram_jump": {"k_range": {"min": 1, "max": 3}}}), "integer >= 2"),
        (json.dumps({**VALID, "noise_filtered_curves": {"max_noise_fraction": 0}}), r"in \(0, 1\]"),
        (json.dumps({**VALID, "noise_filtered_curves": {"max_noise_fraction": 1.5}}), r"in \(0, 1\]"),
        (json.dumps({**VALID, "noise_filtered_curves": {}}), "max_noise_fraction"),
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


def test_density_evaluations_write_their_files_and_nothing_else(tmp_path):
    run = _density_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["density_metrics", "noise_filtered_curves"]})

    written = run_evaluations(block, _settings(), run, overwrite=False)

    assert sorted(path.name for path in written) == ["density_metrics.csv", "noise_filtered_curves.png"]
    metrics = pd.read_csv(tmp_path / "density_metrics.csv")
    assert metrics["n_clusters_found"].tolist() == [4, 2]
    assert (tmp_path / "noise_filtered_curves.png").stat().st_size > 0


def test_an_evaluation_not_in_the_block_is_not_run(tmp_path):
    run = _density_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["density_metrics"]})

    run_evaluations(block, _settings(), run, overwrite=False)

    assert not (tmp_path / "noise_filtered_curves.png").exists()


def test_the_noise_limit_comes_from_the_settings_not_from_the_code(tmp_path):
    rows = [{"min_cluster_size": 5, "min_samples": 5, "noise_fraction": 0.4, "silhouette": 0.5, "davies_bouldin": 1.0}]
    run = ClusteringTuningRun(tmp_path, "hdbscan", Path("m"), pd.DataFrame(rows), {"min_cluster_size=5,min_samples=5": np.repeat([0, 1], 10)})
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["noise_filtered_curves"]})

    under_default = run_evaluations(block, {**_settings(), "noise_filtered_curves": {"max_noise_fraction": 0.1}}, run, overwrite=False)
    over_default = run_evaluations(block, {**_settings(), "noise_filtered_curves": {"max_noise_fraction": 0.5}}, run, overwrite=False)

    assert under_default == []  # no combination under 10% noise: a finding about the run, not an error
    assert [path.name for path in over_default] == ["noise_filtered_curves.png"]


def test_a_second_run_without_overwrite_stops_and_overwrite_replaces(tmp_path):
    run = _density_run(tmp_path)
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": ["density_metrics"]})
    run_evaluations(block, _settings(), run, overwrite=False)

    with pytest.raises(FileExistsError, match="overwrite=true"):
        run_evaluations(block, _settings(), run, overwrite=False)
    run_evaluations(block, _settings(), run, overwrite=True)


def test_a_block_with_no_key_for_the_runs_method_raises(tmp_path):
    run = _density_run(tmp_path, "hdbscan_soft")
    block = validate_tuning_evaluations_block({"general": [], "hdbscan": []})

    with pytest.raises(ValueError, match="no key for"):
        run_evaluations(block, _settings(), run, overwrite=False)


def test_agglomerative_evaluations_read_the_matrix_of_the_run_and_share_a_cache(tmp_path):
    run = _agglomerative_run(tmp_path)
    block = validate_tuning_evaluations_block(
        {"general": [], "agglomerative": ["cophenetic_correlation", "dendrogram_jump", "linkage_agreement"]}
    )
    settings = {**_settings(), "dendrogram_jump": {"k_range": {"min": 2, "max": 4}}}

    written = run_evaluations(block, settings, run, overwrite=False)

    assert [path.name for path in written] == ["cophenetic_correlation.csv", "dendrogram_jump.csv", "linkage_agreement.csv"]
    assert set(pd.read_csv(run.run_dir / "dendrogram_jump.csv")["n_clusters"]) == {2, 3, 4}
    assert set(pd.read_csv(run.run_dir / "cophenetic_correlation.csv")["linkage"]) == {"ward", "average"}


def test_a_matrix_the_caller_holds_is_used_instead_of_the_run_input_path(tmp_path):
    run = _agglomerative_run(tmp_path)
    run = ClusteringTuningRun(run.run_dir, run.method, tmp_path / "does_not_exist", run.results, run.labels)
    block = validate_tuning_evaluations_block({"general": [], "agglomerative": ["cophenetic_correlation"]})

    written = run_evaluations(block, _settings(), run, overwrite=False, matrix=_three_blobs())

    assert [path.name for path in written] == ["cophenetic_correlation.csv"]
