"""Loads per-method hyperparameters from config/registry/params_reduction.json / params_clustering.json.

Shape: {method: {"params": {...}}}. Hyperparameters themselves are never
validated key-by-key here - sklearn/umap raise their own error for a bad
constructor argument when src/analysis/reduction.py or clustering.py unpacks
the returned dict (code_standards.md §5: every hyperparameter lives only in
this file, never hardcoded in src/).
"""

from __future__ import annotations

import json
from pathlib import Path


def load_method_params(params_file: str | Path, method: str) -> dict:
    """Load the params dict registered for `method` in `params_file`.

    Raises FileNotFoundError if params_file doesn't exist, ValueError if its
    top-level shape isn't a JSON object, if `method` has no entry, or if that
    entry's "params" isn't itself a JSON object.
    """
    params_file = Path(params_file)
    if not params_file.is_file():
        raise FileNotFoundError(f"params file not found: {params_file}")

    with params_file.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"{params_file}: top-level content must be a JSON object, got {raw!r}")

    if method not in raw:
        raise ValueError(f"{params_file}: no entry for method {method!r} (known: {sorted(raw)})")
    entry = raw[method]
    if not isinstance(entry, dict) or "params" not in entry:
        raise ValueError(f"{params_file}: entry for method {method!r} must be a JSON object with a 'params' key")

    params = entry["params"]
    if not isinstance(params, dict):
        raise ValueError(f"{params_file}: {method!r}.params must be a JSON object, got {params!r}")

    return params
