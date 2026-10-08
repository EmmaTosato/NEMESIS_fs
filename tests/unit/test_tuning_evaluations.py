"""Unit tests for src/analysis/tuning_evaluations.py."""

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.clustering import hdbscan_cluster
from src.analysis.tuning_embeddings import TuningRun, combo_key
from src.analysis.tuning_evaluations import (
    EVALUATIONS,
    KIND_EMBEDDING_EVALUATION,
    KIND_SWEEP_SCORE,
    require_native_score_declared,
    run_embedding_evaluations,
    validate_embedding_evaluations_feasible,
    validate_tuning_evaluations_block,
    visualization_key,
)

HDBSCAN_SETTINGS = {"min_cluster_size": 10, "min_samples": 3}
GRID = {"metric": ["euclidean"], "n_components": [2, 4], "n_neighbors": [5, 15]}


def _blobs(n_components: int, seed: int = 0) -> np.ndarray:
    """3 well-separated blobs of 40 points in n_components dimensions."""
    rng = np.random.default_rng(seed)
    centers = np.zeros((3, n_components))
    centers[1, 0], centers[2, 1] = 20.0, 20.0
    return np.vstack([rng.normal(centers[i], 0.5, size=(40, n_components)) for i in range(3)])


def _structureless_twin(seed: int = 1) -> np.ndarray:
    """A 2D cloud with no cluster structure at all - stands in for a twin fit that is a
    different, uninformative embedding of the same subjects."""
    return np.random.default_rng(seed).uniform(0, 1, size=(120, 2))


def _run(tmp_path: Path, nested=("metric", "n_components"), twin_is_structureless=False) -> TuningRun:
    keys = list(GRID)
    embeddings = {}
    for combo in itertools.product(*GRID.values()):
        n_components = dict(zip(keys, combo))["n_components"]
        embedding = _structureless_twin() if (twin_is_structureless and n_components == 2) else _blobs(n_components)
        embeddings[combo_key(keys, combo)] = embedding
    return TuningRun(
        run_dir=tmp_path,
        reduction_method="umap",
        base_params={"n_components": 2},
        tuning_grid=GRID,
        nested_params=list(nested),
        embeddings=embeddings,
    )


# --- block validation ----------------------------------------------------------------------


def test_registry_kinds():
    assert EVALUATIONS["trustworthiness"].kind == KIND_SWEEP_SCORE
    assert EVALUATIONS["cumulative_explained_variance"].kind == KIND_SWEEP_SCORE
    assert EVALUATIONS["plot_hdbscan"].kind == KIND_EMBEDDING_EVALUATION


def test_validate_block_accepts_registered_evaluations():
    block = {"trustworthiness": {}, "plot_hdbscan": HDBSCAN_SETTINGS}

    assert validate_tuning_evaluations_block(block) == block


def test_validate_block_rejects_a_kind_the_caller_cannot_honour():
    with pytest.raises(ValueError, match="sweep_score and cannot be run here"):
        validate_tuning_evaluations_block({"trustworthiness": {}}, frozenset({KIND_EMBEDDING_EVALUATION}))


# --- native score declaration --------------------------------------------------------------


def test_require_native_score_declared_accepts_the_methods_own_score():
    require_native_score_declared({"trustworthiness": {}, "plot_hdbscan": HDBSCAN_SETTINGS}, "trustworthiness", "umap")


@pytest.mark.parametrize(
    "block",
    [
        {"plot_hdbscan": HDBSCAN_SETTINGS},  # omits what the sweep does compute
        {"cumulative_explained_variance": {}},  # another family's score
        {"trustworthiness": {}, "cumulative_explained_variance": {}},  # states something the run does not do
    ],
)
def test_require_native_score_declared_rejects_a_block_that_misstates_the_sweep(block):
    with pytest.raises(ValueError, match="declare exactly the sweep score"):
        require_native_score_declared(block, "trustworthiness", "umap")


# --- visualization twin --------------------------------------------------------------------


def test_visualization_key_is_itself_for_a_2d_embedding():
    key = "metric=euclidean,n_components=2,n_neighbors=5"

    assert visualization_key(key, 2, {key: np.zeros((3, 2))}) == key


def test_visualization_key_of_a_higher_dimensional_embedding_is_its_2d_twin():
    twin = "metric=euclidean,n_components=2,n_neighbors=5"

    assert visualization_key("metric=euclidean,n_components=4,n_neighbors=5", 4, {twin: np.zeros((3, 2))}) == twin


def test_visualization_key_without_n_components_in_the_sweep_raises():
    with pytest.raises(ValueError, match="no n_components in the sweep"):
        visualization_key("perplexity=30", 3, {})


def test_visualization_key_missing_twin_raises():
    with pytest.raises(ValueError, match="twin .* was not swept"):
        visualization_key("metric=euclidean,n_components=4,n_neighbors=5", 4, {})


# --- feasibility, before the sweep ---------------------------------------------------------


def test_feasible_when_the_grid_includes_the_2d_twin():
    validate_embedding_evaluations_feasible({"plot_hdbscan": HDBSCAN_SETTINGS}, {"n_components": 2}, {"n_components": [2, 5, 10]})


@pytest.mark.parametrize(
    "base_params, grid",
    [({"n_components": 2}, {"n_components": [5, 10]}), ({"n_components": 3}, {"n_neighbors": [5]})],
)
def test_infeasible_when_a_higher_dimensional_embedding_has_no_2d_twin(base_params, grid):
    with pytest.raises(ValueError, match="2-component twin"):
        validate_embedding_evaluations_feasible({"plot_hdbscan": HDBSCAN_SETTINGS}, base_params, grid)


def test_sweep_scores_have_nothing_to_check_for_feasibility():
    validate_embedding_evaluations_feasible({"trustworthiness": {}}, {"n_components": 3}, {"n_neighbors": [5]})


# --- plot_hdbscan --------------------------------------------------------------------------


def test_plot_hdbscan_writes_one_grid_and_csv_per_nested_leaf(tmp_path):
    written = run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, _run(tmp_path), overwrite=False)

    leaves = ["metric=euclidean/n_components=2", "metric=euclidean/n_components=4"]
    expected = {tmp_path / leaf / name for leaf in leaves for name in ("hdbscan_grid_mcs10_ms3.png", "hdbscan_results_mcs10_ms3.csv")}
    assert set(written) == expected
    assert all(path.is_file() for path in expected)


def test_plot_hdbscan_csv_has_one_typed_row_per_combination_of_the_leaf(tmp_path):
    run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, _run(tmp_path), overwrite=False)

    csv = pd.read_csv(tmp_path / "metric=euclidean/n_components=4" / "hdbscan_results_mcs10_ms3.csv")

    assert list(csv.columns) == ["metric", "n_components", "n_neighbors", "n_clusters_found", "noise_fraction"]
    assert list(csv["n_neighbors"]) == [5, 15]
    assert set(csv["n_components"]) == {4}
    assert (csv["n_clusters_found"] == 3).all()  # the 3 blobs


def test_plot_hdbscan_clusters_in_the_embeddings_own_space_not_on_its_2d_twin(tmp_path):
    """Regression guard for the central design point: a 4-component embedding's clusters are
    found in its own 4 dimensions and merely drawn on the 2-component twin. With a twin that has
    no structure at all, clustering on the twin would find ~no clusters; clustering in the own
    space still finds the 3 blobs."""
    run = _run(tmp_path, twin_is_structureless=True)

    run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, run, overwrite=False)

    own_space = pd.read_csv(tmp_path / "metric=euclidean/n_components=4" / "hdbscan_results_mcs10_ms3.csv")
    on_the_twin = len(np.unique(hdbscan_cluster(_structureless_twin(), HDBSCAN_SETTINGS)))
    assert (own_space["n_clusters_found"] == 3).all()
    assert on_the_twin != 3  # so the 3 above cannot have come from clustering the twin


def test_plot_hdbscan_without_nested_params_writes_into_the_run_dir(tmp_path):
    run = TuningRun(
        run_dir=tmp_path,
        reduction_method="tsne",
        base_params={},
        tuning_grid={"perplexity": [5, 30]},
        nested_params=[],
        embeddings={"perplexity=5": _blobs(2), "perplexity=30": _blobs(2, seed=2)},
    )

    written = run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, run, overwrite=False)

    assert {p.parent for p in written} == {tmp_path}


def test_plot_hdbscan_refuses_to_replace_existing_files_unless_overwrite(tmp_path):
    run = _run(tmp_path)
    run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, run, overwrite=False)

    with pytest.raises(FileExistsError, match="overwrite=true"):
        run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, run, overwrite=False)
    run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, run, overwrite=True)


def test_plot_hdbscan_with_other_settings_adds_files_instead_of_replacing(tmp_path):
    run = _run(tmp_path)
    other = {"min_cluster_size": 20, "min_samples": 5}

    run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, run, overwrite=False)
    run_embedding_evaluations({"plot_hdbscan": other}, run, overwrite=False)

    leaf = tmp_path / "metric=euclidean/n_components=2"
    assert (leaf / "hdbscan_grid_mcs10_ms3.png").is_file()
    assert (leaf / "hdbscan_grid_mcs20_ms5.png").is_file()


def test_plot_hdbscan_missing_twin_raises_before_writing_anything(tmp_path):
    run = _run(tmp_path)
    del run.embeddings["metric=euclidean,n_components=2,n_neighbors=5"]

    with pytest.raises(ValueError, match="twin"):
        run_embedding_evaluations({"plot_hdbscan": HDBSCAN_SETTINGS}, run, overwrite=False)
    assert not list(tmp_path.rglob("*.png"))


def test_run_embedding_evaluations_skips_sweep_scores(tmp_path):
    assert run_embedding_evaluations({"trustworthiness": {}}, _run(tmp_path), overwrite=False) == []
    assert not list(tmp_path.rglob("*.png"))
