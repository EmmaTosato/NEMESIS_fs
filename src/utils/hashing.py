"""Deterministic content hashing, used to key analysis-pipeline step
checkpoints (see src.pipeline.checkpoint)."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def chain_hash(prior_hash: str | None, step_name: str, params: dict[str, Any]) -> str:
    """Hash of a step's identity within its chain: its own name/params plus
    the hash of everything that ran before it. Any upstream change (a
    different param, a different prior step, a different position in the
    chain) therefore changes this hash too, without needing an explicit
    staleness comparison - a cache directory keyed by a stale hash is simply
    never looked up again.

    Raises ValueError if `params` contains a value that can't be serialized
    deterministically (e.g. an arbitrary object) - a step's own
    validate_params is expected to only ever produce plain JSON-safe types
    (str/int/float/bool/list/dict/None), so this should not happen in
    practice; surfacing it clearly here is preferable to silently
    stringifying an unexpected value.
    """
    payload = {"prior": prior_hash, "name": step_name, "params": params}
    try:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    except TypeError as exc:
        raise ValueError(
            f"chain_hash: params for step {step_name!r} are not JSON-serializable: {exc}"
        ) from exc
    return hashlib.sha256(encoded).hexdigest()
