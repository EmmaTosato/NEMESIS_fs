"""Unit tests for src.pipeline.checkpoint.get_or_run: cache hit/miss
behavior, crash-safety (a directory without a manifest is a miss, never a
corrupt hit), and overwrite_cache forcing a rerun despite a valid hit.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.pipeline.checkpoint import get_or_run
from src.utils.hashing import chain_hash
from src.utils.step import StepResult


def _make_run_fn(call_count: list[int]):
    def run_fn(prev, params):
        call_count[0] += 1
        n_rows = params.get("n_rows", 3)
        X = np.full((n_rows, 2), call_count[0], dtype=float)
        metadata = pd.DataFrame({"subject_id": [f"s{i}" for i in range(n_rows)]})
        return StepResult(X=X, metadata=metadata, params_used=params, step_name="fake")

    return run_fn


def test_cache_miss_then_hit(tmp_path):
    call_count = [0]
    run_fn = _make_run_fn(call_count)

    result1, hash1, cached1 = get_or_run(
        cache_root=tmp_path,
        step_index=0,
        step_name="fake",
        params={"n_rows": 3},
        prior_chain_hash=None,
        run_fn=run_fn,
        step_input=None,
        overwrite=False,
    )
    assert cached1 is False
    assert call_count[0] == 1

    result2, hash2, cached2 = get_or_run(
        cache_root=tmp_path,
        step_index=0,
        step_name="fake",
        params={"n_rows": 3},
        prior_chain_hash=None,
        run_fn=run_fn,
        step_input=None,
        overwrite=False,
    )
    assert cached2 is True
    assert call_count[0] == 1  # run_fn not called again
    assert hash1 == hash2
    np.testing.assert_array_equal(result1.X, result2.X)


def test_cache_miss_on_param_change(tmp_path):
    call_count = [0]
    run_fn = _make_run_fn(call_count)

    _, hash1, _ = get_or_run(
        cache_root=tmp_path,
        step_index=0,
        step_name="fake",
        params={"n_rows": 3},
        prior_chain_hash=None,
        run_fn=run_fn,
        step_input=None,
        overwrite=False,
    )
    _, hash2, cached2 = get_or_run(
        cache_root=tmp_path,
        step_index=0,
        step_name="fake",
        params={"n_rows": 5},
        prior_chain_hash=None,
        run_fn=run_fn,
        step_input=None,
        overwrite=False,
    )
    assert cached2 is False
    assert call_count[0] == 2
    assert hash1 != hash2


def test_partial_cache_directory_treated_as_miss(tmp_path):
    """Simulates a crash mid-write: a step directory exists with an array
    already written but no manifest.json yet. Must be treated as a miss,
    never as a corrupt hit."""
    call_count = [0]
    run_fn = _make_run_fn(call_count)

    this_hash = chain_hash(None, "fake", {"n_rows": 3})
    step_dir = tmp_path / f"00_fake_{this_hash[:10]}"
    step_dir.mkdir(parents=True)
    np.save(step_dir / "X.npy", np.zeros((3, 2)))
    # no manifest.json written - simulates an interrupted save()

    _, _, cached = get_or_run(
        cache_root=tmp_path,
        step_index=0,
        step_name="fake",
        params={"n_rows": 3},
        prior_chain_hash=None,
        run_fn=run_fn,
        step_input=None,
        overwrite=False,
    )
    assert cached is False
    assert call_count[0] == 1


def test_overwrite_cache_forces_rerun(tmp_path):
    call_count = [0]
    run_fn = _make_run_fn(call_count)

    get_or_run(
        cache_root=tmp_path,
        step_index=0,
        step_name="fake",
        params={"n_rows": 3},
        prior_chain_hash=None,
        run_fn=run_fn,
        step_input=None,
        overwrite=False,
    )
    _, _, cached = get_or_run(
        cache_root=tmp_path,
        step_index=0,
        step_name="fake",
        params={"n_rows": 3},
        prior_chain_hash=None,
        run_fn=run_fn,
        step_input=None,
        overwrite=True,
    )
    assert cached is False
    assert call_count[0] == 2


def test_chain_hash_changes_with_prior_hash():
    """Two steps with identical name/params but a different prior_chain_hash
    must produce different hashes - this is what makes an upstream change
    cascade into every downstream cache key."""
    hash_a = chain_hash("prior-a", "fake", {"n_rows": 3})
    hash_b = chain_hash("prior-b", "fake", {"n_rows": 3})
    assert hash_a != hash_b
