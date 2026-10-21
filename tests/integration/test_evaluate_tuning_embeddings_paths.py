"""`src/pipeline/evaluate_tuning_embeddings.py::main`: rami di errore su un tuning già salvato (file veri minuscoli).

Il tuning è scritto a mano nel suo formato su disco (`embeddings.npz` + blocco ```json in `config.md`), lo stesso
che `dim_reduction.py` produce e `load_tuning_run` rilegge.
"""

from __future__ import annotations

import json
import logging

import matplotlib.figure
import numpy as np
import pandas as pd
import pytest

from src.analysis.tuning_embeddings import combo_key
from src.pipeline import evaluate_tuning_embeddings as pipeline

HDBSCAN = {"min_cluster_size": 10, "min_samples": 3}
KEYS = ["metric", "n_components", "n_neighbors"]


def _blobs(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centers = np.array([[0.0, 0.0], [20.0, 0.0], [0.0, 20.0]])
    return np.vstack([rng.normal(c, 0.5, size=(40, 2)) for c in centers])


def _write_tuning_run(directory, grid=None, base_params=None, config_text=None):
    grid = grid or {"metric": ["euclidean"], "n_components": [2], "n_neighbors": [5, 15]}
    directory.mkdir(parents=True, exist_ok=True)
    arrays = {}
    import itertools

    for combo in itertools.product(*grid.values()):
        dims = int(dict(zip(grid, combo))["n_components"])
        arrays[combo_key(list(grid), combo)] = np.hstack([_blobs(), np.zeros((120, dims - 2))]) if dims > 2 else _blobs()
    np.savez(directory / "embeddings.npz", **arrays)
    block = {
        "reduction_method": "umap",
        "base_params": base_params or {"n_components": 2},
        "tuning_grid": grid,
        "nested_params": [],
    }
    (directory / "config.md").write_text(config_text or f"# tuning\n\n```json\n{json.dumps(block)}\n```\n")
    return directory


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "LOGS_ROOT", tmp_path / "logs")
    return {"tmp": tmp_path, "dir": _write_tuning_run(tmp_path / "tuning")}


def _cfg(run, **overrides):
    payload = {
        "tuning_dir": str(run["dir"]),
        "overwrite": False,
        "tuning_evaluations": {"plot_hdbscan": HDBSCAN},
        **overrides,
    }
    path = run["tmp"] / "evaluate.json"
    path.write_text(json.dumps(payload))
    return ["--config", str(path)]


def test_success_writes_png_and_typed_csv_next_to_the_sweep_and_logs_the_count(run, caplog):
    with caplog.at_level(logging.INFO):
        assert pipeline.main(_cfg(run)) == 0

    csv = run["dir"] / "hdbscan_results_mcs10_ms3.csv"
    assert csv.is_file() and (run["dir"] / "hdbscan_grid_mcs10_ms3.png").stat().st_size > 0
    frame = pd.read_csv(csv)
    assert len(frame) == 2  # una riga per combinazione del grid
    assert not frame.isna().any().any()
    assert "done - 2 file(s) written" in caplog.text and "run duration" in caplog.text


def test_missing_config_returns_1(run, caplog):
    with caplog.at_level(logging.ERROR):
        assert pipeline.main(["--config", str(run["tmp"] / "absent.json")]) == 1
    assert "config file not found" in caplog.text


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"tuning_evaluations": {"trustworthiness": {}}}, "cannot be run here"),
        ({"tuning_evaluations": {}}, "at least one evaluation"),
        ({"tuning_evaluations": {"no_such_eval": {}}}, "no_such_eval"),
        ({"overwrite": "yes"}, "overwrite"),
    ],
)
def test_invalid_config_returns_1_and_writes_nothing(run, caplog, overrides, expected):
    with caplog.at_level(logging.ERROR):
        assert pipeline.main(_cfg(run, **overrides)) == 1
    assert expected in caplog.text
    assert not list(run["dir"].glob("hdbscan_*"))


def test_log_directory_not_creatable_returns_1(run, monkeypatch, caplog):
    blocker = run["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(pipeline, "LOGS_ROOT", blocker / "logs")
    with caplog.at_level(logging.ERROR):
        assert pipeline.main(_cfg(run)) == 1
    assert "cannot set up log file" in caplog.text
    assert not list(run["dir"].glob("hdbscan_*"))


@pytest.mark.parametrize(
    "mutation, expected",
    [
        ("no_config", "tuning config not found"),
        ("no_json_block", "has no ```json config block"),
        ("bad_json", "Expecting"),
        ("missing_field", "is missing 'nested_params'"),
        ("npz_grid_mismatch", "does not match the tuning_grid"),
    ],
)
def test_unreadable_stored_run_returns_1_with_the_cause(run, caplog, mutation, expected):
    config = run["dir"] / "config.md"
    if mutation == "no_config":
        config.unlink()
    elif mutation == "no_json_block":
        config.write_text("# nothing here\n")
    elif mutation == "bad_json":
        config.write_text("```json\n{broken\n```\n")
    elif mutation == "missing_field":
        config.write_text('```json\n{"reduction_method": "umap", "base_params": {}, "tuning_grid": {"a": [1]}}\n```\n')
    elif mutation == "npz_grid_mismatch":
        _write_tuning_run(run["dir"], grid={"metric": ["euclidean"], "n_components": [2], "n_neighbors": [5]})
        block = {
            "reduction_method": "umap", "base_params": {"n_components": 2}, "nested_params": [],
            "tuning_grid": {"metric": ["euclidean"], "n_components": [2], "n_neighbors": [5, 15]},
        }
        config.write_text(f"```json\n{json.dumps(block)}\n```\n")

    with caplog.at_level(logging.ERROR):
        assert pipeline.main(_cfg(run)) == 1
    assert expected in caplog.text
    assert not list(run["dir"].glob("hdbscan_*"))


def test_higher_dimensional_combos_without_a_2d_twin_fail_before_writing(run, caplog):
    _write_tuning_run(run["dir"], grid={"metric": ["euclidean"], "n_components": [3, 4], "n_neighbors": [5]})
    with caplog.at_level(logging.ERROR):
        assert pipeline.main(_cfg(run)) == 1
    assert "2-component twin" in caplog.text
    assert not list(run["dir"].glob("hdbscan_*"))


def test_existing_outputs_without_overwrite_return_1_and_are_not_replaced(run, caplog):
    assert pipeline.main(_cfg(run)) == 0
    csv = run["dir"] / "hdbscan_results_mcs10_ms3.csv"
    csv.write_text("sentinel\n")

    with caplog.at_level(logging.ERROR):
        assert pipeline.main(_cfg(run)) == 1
    assert "tuning evaluation failed" in caplog.text
    assert csv.read_text() == "sentinel\n"

    assert pipeline.main(_cfg(run, overwrite=True)) == 0
    assert csv.read_text() != "sentinel\n"


def test_write_failure_during_evaluation_returns_1_with_traceback(run, monkeypatch, caplog):
    def boom(self, *args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", boom)
    with caplog.at_level(logging.ERROR):
        assert pipeline.main(_cfg(run)) == 1
    assert "tuning evaluation failed" in caplog.text and "disk full" in caplog.text
    assert any(r.exc_info for r in caplog.records if r.levelno == logging.ERROR)  # OSError: contesto completo
