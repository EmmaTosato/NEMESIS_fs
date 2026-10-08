"""Unit tests for src/analysis/tuning_embeddings.py."""

import json
from pathlib import Path

import numpy as np
import pytest

from src.analysis.tuning_embeddings import combo_key, leaf_dir, load_tuning_run, parse_combo_key

GRID = {"metric": ["dice", "euclidean"], "n_components": [2, 3], "n_neighbors": [5, 15]}
NESTED = ["metric", "n_components"]


def _write_run(run_dir: Path, grid=GRID, nested=NESTED, embeddings=None, config_extra=None) -> None:
    import itertools

    run_dir.mkdir(parents=True, exist_ok=True)
    keys = list(grid)
    if embeddings is None:
        embeddings = {
            combo_key(keys, combo): np.zeros((4, dict(zip(keys, combo)).get("n_components", 2)))
            for combo in itertools.product(*grid.values())
        }
    np.savez(run_dir / "embeddings.npz", **embeddings)
    config = {"reduction_method": "umap", "base_params": {"n_components": 2}, "tuning_grid": grid, "nested_params": nested}
    config.update(config_extra or {})
    (run_dir / "config.md").write_text(f"# t\n\n## Config\n\n```json\n{json.dumps(config, indent=2)}\n```\n\n## Summary\n")


def test_combo_key_and_parse_roundtrip():
    key = combo_key(["metric", "n_components", "min_dist"], ["dice", 10, 0.0])

    assert key == "metric=dice,n_components=10,min_dist=0.0"
    assert parse_combo_key(key) == {"metric": "dice", "n_components": "10", "min_dist": "0.0"}


@pytest.mark.parametrize("bad_key", ["metric", "metric=dice,n_components", "=3", "a=b=c"])
def test_parse_combo_key_rejects_malformed_parts(bad_key):
    with pytest.raises(ValueError, match="malformed combination key"):
        parse_combo_key(bad_key)


def test_leaf_dir_nests_one_level_per_nested_param():
    path = leaf_dir(Path("out"), ["metric", "n_components"], {"metric": "dice", "n_components": 10})

    assert path == Path("out/metric=dice/n_components=10")


def test_leaf_dir_without_nested_params_is_the_run_dir():
    assert leaf_dir(Path("out"), [], {}) == Path("out")


def test_load_tuning_run_reads_grid_and_every_embedding(tmp_path):
    _write_run(tmp_path)

    run = load_tuning_run(tmp_path)

    assert run.reduction_method == "umap"
    assert run.nested_params == NESTED
    assert run.tuning_grid == GRID
    assert len(run.embeddings) == 8
    assert run.embeddings["metric=dice,n_components=3,n_neighbors=5"].shape == (4, 3)


def test_load_tuning_run_without_embeddings_npz_says_how_to_get_one(tmp_path):
    _write_run(tmp_path)
    (tmp_path / "embeddings.npz").unlink()

    with pytest.raises(FileNotFoundError, match="save_tuning_embeddings=true"):
        load_tuning_run(tmp_path)


def test_load_tuning_run_rejects_embeddings_that_do_not_match_the_declared_grid(tmp_path):
    """Regression guard for lessons_learned.md #18: a directory reused by a run with another grid
    keeps a config.md that describes only the last writer - never evaluate such a mix."""
    keys = list(GRID)
    stale = {combo_key(keys, ("dice", 2, 5)): np.zeros((4, 2))}
    _write_run(tmp_path, embeddings=stale)

    with pytest.raises(ValueError, match="does not match the tuning_grid"):
        load_tuning_run(tmp_path)


def test_load_tuning_run_config_without_json_block_raises(tmp_path):
    _write_run(tmp_path)
    (tmp_path / "config.md").write_text("# no block here\n")

    with pytest.raises(ValueError, match="no ```json config block"):
        load_tuning_run(tmp_path)


def test_load_tuning_run_config_missing_field_raises(tmp_path):
    _write_run(tmp_path)
    text = (tmp_path / "config.md").read_text().replace('"nested_params"', '"nested_params_renamed"')
    (tmp_path / "config.md").write_text(text)

    with pytest.raises(ValueError, match="missing 'nested_params'"):
        load_tuning_run(tmp_path)


def test_load_tuning_run_nested_param_not_in_grid_raises(tmp_path):
    _write_run(tmp_path, nested=["metric", "perplexity"])

    with pytest.raises(ValueError, match="not in tuning_grid"):
        load_tuning_run(tmp_path)
