"""Loads per-method hyperparameters from config/registry/params_reduction.json / params_clustering.json.

Shape: {method: {"params": {...}, "tuning_grid": {...}?, "trustworthiness_n_neighbors": int?, "consensus": {...}?}}.
Hyperparameters themselves are never validated key-by-key here - sklearn/umap
raise their own error for a bad constructor argument when
src/analysis/reduction.py or clustering.py unpacks the returned dict
(code_standards.md §5: every hyperparameter lives only in this file, never
hardcoded in src/). "tuning_grid"/"trustworthiness_n_neighbors" are optional -
only methods that support fine-tuning (today: umap, pca) have them; t-SNE and
kmeans have "params" only. "consensus" (params_clustering.json only) is
optional and restricted to kmeans/gmm/spectral - see
src/analysis/consensus_clustering.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.analysis.consensus_clustering import CONSENSUS_ELIGIBLE_METHODS


def load_method_params(params_file: str | Path, method: str) -> tuple[dict, str | None]:
    """Load the params dict and the optional tag registered for `method`.

    Raises FileNotFoundError if params_file doesn't exist, ValueError if its
    top-level shape isn't a JSON object, if `method` has no entry, or if that
    entry's "params" isn't itself a JSON object.
    """
    entry = _load_method_entry(params_file, method)
    if "params" not in entry:
        raise ValueError(f"{params_file}: entry for method {method!r} must be a JSON object with a 'params' key")
    params = entry["params"]
    if not isinstance(params, dict):
        raise ValueError(f"{params_file}: {method!r}.params must be a JSON object, got {params!r}")
        
    tag_param = entry.get("tag_param")
    tag_prefix = entry.get("tag_prefix", "")
    
    tag_str = None
    if tag_param and tag_param in params:
        val_str = str(params[tag_param]).replace(".", "")
        tag_str = f"{tag_prefix}{val_str}"
        
    return params, tag_str


def load_tuning_grid(params_file: str | Path, method: str) -> dict[str, list]:
    """Load the tuning_grid dict registered for `method` in `params_file`.

    Raises ValueError if `method` has no "tuning_grid" entry, if it isn't a
    JSON object mapping each hyperparameter to a non-empty list of values,
    or if any value in one of those lists is itself a nested list/object -
    such a value is later used as part of a dict key (AUDIT_FINDINGS.md #56,
    lesson #8) and would otherwise raise a cryptic TypeError far downstream
    instead of a clear error here.
    """
    entry = _load_method_entry(params_file, method)
    if "tuning_grid" not in entry:
        raise ValueError(f"{params_file}: method {method!r} has no 'tuning_grid' entry - fine-tuning not configured for it")
    grid = entry["tuning_grid"]
    if not isinstance(grid, dict) or not grid:
        raise ValueError(f"{params_file}: {method!r}.tuning_grid must be a non-empty JSON object, got {grid!r}")
    for key, values in grid.items():
        if not isinstance(values, list) or not values:
            raise ValueError(f"{params_file}: {method!r}.tuning_grid[{key!r}] must be a non-empty list, got {values!r}")
        for value in values:
            if isinstance(value, (list, dict)):
                raise ValueError(
                    f"{params_file}: {method!r}.tuning_grid[{key!r}] has a non-hashable value {value!r} "
                    "(a nested list/object) - every value must be a plain scalar (string/number/bool/null), "
                    "it's later used as part of a dict key to look up this exact combination's embedding"
                )
    return grid


def load_nested_params(params_file: str | Path, method: str, tuning_grid: dict[str, list]) -> list[str]:
    """Load the ordered "nested_params" list registered for `method` in
    `params_file` - the tuning_grid keys fixed one-at-a-time in nested output
    folders, outermost first, as opposed to the "free" keys left over that
    get swept jointly (see docs/dev/models.md's `_write_nested_tuning_leaves`
    entry). Absent -> [] (no nesting), a legitimate case for a method with
    <= 2 total swept parameters (e.g. pacmap/pca today).

    Raises ValueError if nested_params isn't a list of strings, references a
    name not in tuning_grid, or leaves anything other than 1 or 2 free
    parameters (0 = nothing to visualize, >2 = not representable by the
    2-block embedding grid).
    """
    entry = _load_method_entry(params_file, method)
    if "nested_params" not in entry:
        return []

    nested_params = entry["nested_params"]
    if not isinstance(nested_params, list) or not all(isinstance(name, str) for name in nested_params):
        raise ValueError(f"{params_file}: {method!r}.nested_params must be a list of strings, got {nested_params!r}")

    unknown = [name for name in nested_params if name not in tuning_grid]
    if unknown:
        raise ValueError(
            f"{params_file}: {method!r}.nested_params references {unknown!r}, not present in tuning_grid "
            f"(known: {sorted(tuning_grid)})"
        )

    free_params = [key for key in tuning_grid if key not in nested_params]
    if len(free_params) not in (1, 2):
        raise ValueError(
            f"{params_file}: {method!r} has {len(free_params)} free parameter(s) left after nested_params "
            f"{nested_params!r} ({free_params!r}) - must be exactly 1 or 2 (the visualizable grid search)"
        )

    return nested_params


def load_consensus_config(params_file: str | Path, method: str) -> dict | None:
    """Load the optional "consensus" block registered for `method` in
    `params_file` (see docs/dev/models.md's consensus_clustering.py section).
    Absent -> None, a legitimate "not requested" case.

    Raises ValueError if `method` isn't in CONSENSUS_ELIGIBLE_METHODS but a
    "consensus" entry is present anyway, or if the block's shape is wrong:
    only "rsc"/"monti" keys allowed, "rsc" needs an int "n_repeats" >= 1,
    "monti" needs those plus a "subsample_fraction" in (0, 1).
    """
    entry = _load_method_entry(params_file, method)
    if "consensus" not in entry:
        return None
    if method not in CONSENSUS_ELIGIBLE_METHODS:
        raise ValueError(
            f"{params_file}: {method!r} has a 'consensus' entry, but consensus/stability clustering is only "
            f"defined for {sorted(CONSENSUS_ELIGIBLE_METHODS)}"
        )

    consensus = entry["consensus"]
    if not isinstance(consensus, dict) or not consensus:
        raise ValueError(f"{params_file}: {method!r}.consensus must be a non-empty JSON object, got {consensus!r}")
    unknown_keys = set(consensus) - {"rsc", "monti"}
    if unknown_keys:
        raise ValueError(f"{params_file}: {method!r}.consensus has unknown key(s) {sorted(unknown_keys)} - only 'rsc'/'monti' allowed")

    if "rsc" in consensus:
        _validate_n_repeats(params_file, method, "rsc", consensus["rsc"])
    if "monti" in consensus:
        _validate_n_repeats(params_file, method, "monti", consensus["monti"])
        fraction = consensus["monti"].get("subsample_fraction")
        if not isinstance(fraction, (int, float)) or isinstance(fraction, bool) or not (0.0 < fraction < 1.0):
            raise ValueError(f"{params_file}: {method!r}.consensus.monti.subsample_fraction must be in (0, 1), got {fraction!r}")

    return consensus


def _validate_n_repeats(params_file: str | Path, method: str, key: str, block: object) -> None:
    if not isinstance(block, dict):
        raise ValueError(f"{params_file}: {method!r}.consensus.{key} must be a JSON object, got {block!r}")
    n_repeats = block.get("n_repeats")
    if isinstance(n_repeats, bool) or not isinstance(n_repeats, int) or n_repeats < 1:
        raise ValueError(f"{params_file}: {method!r}.consensus.{key}.n_repeats must be a positive integer, got {n_repeats!r}")


def load_trustworthiness_n_neighbors(params_file: str | Path, method: str) -> int:
    """Load the trustworthiness_n_neighbors int registered for `method` in `params_file`.

    Raises ValueError if `method` has no such entry, or it isn't a positive int.
    """
    entry = _load_method_entry(params_file, method)
    if "trustworthiness_n_neighbors" not in entry:
        raise ValueError(f"{params_file}: method {method!r} has no 'trustworthiness_n_neighbors' entry")
    value = entry["trustworthiness_n_neighbors"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{params_file}: {method!r}.trustworthiness_n_neighbors must be a positive integer, got {value!r}")
    return value


def _load_method_entry(params_file: str | Path, method: str) -> dict:
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
    if not isinstance(entry, dict):
        raise ValueError(f"{params_file}: entry for method {method!r} must be a JSON object")
    return entry
