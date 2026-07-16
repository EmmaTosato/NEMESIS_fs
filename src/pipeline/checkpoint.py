"""Checkpointing for analysis-pipeline steps: run-or-reuse-from-cache, keyed
by a hash of everything that produced a step's result (see
src.utils.hashing.chain_hash) - not just that step's own params, so any
upstream change (a different param, or a different step earlier in the
chain) cascades into a different cache key for everything downstream,
without needing an explicit staleness comparison.

Steps themselves are pure (src.utils.step.Step) and know nothing about
caching or the filesystem - this module owns every decision about when/where
a result is persisted, which is exactly the seam a future execution strategy
(e.g. running a step in a subprocess or as a submitted cluster job instead of
in-process, to work around this user's memory-constrained interactive
session) would need to replace, without touching any step's own code.
"""

from __future__ import annotations

import logging
import resource
import time
from pathlib import Path

from src.utils import artifact_store
from src.utils.hashing import chain_hash
from src.utils.step import Step, StepResult


def get_or_run(
    cache_root: Path,
    step_index: int,
    step_name: str,
    params: dict,
    prior_chain_hash: str | None,
    run_fn: Step,
    step_input: StepResult | None,
    overwrite: bool,
) -> tuple[StepResult, str, bool]:
    """Returns (result, this_chain_hash, was_cached).

    `was_cached` is True when a valid cache directory was found and reused
    (run_fn was NOT called), False when run_fn actually ran and its result
    was freshly saved.
    """
    this_hash = chain_hash(prior_chain_hash, step_name, params)
    step_dir = cache_root / f"{step_index:02d}_{step_name}_{this_hash[:10]}"

    if not overwrite and artifact_store.is_valid_cache_dir(step_dir, this_hash):
        logging.info("step cached: index=%d name=%s dir=%s", step_index, step_name, step_dir)
        return artifact_store.load(step_dir), this_hash, True

    start = time.monotonic()
    result = run_fn(step_input, params)
    artifact_store.save(step_dir, result, this_hash)
    duration_s = time.monotonic() - start
    peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    logging.info(
        "step ran: index=%d name=%s duration_s=%.1f peak_rss_mb=%.0f dir=%s",
        step_index,
        step_name,
        duration_s,
        peak_rss_mb,
        step_dir,
    )
    return result, this_hash, False
