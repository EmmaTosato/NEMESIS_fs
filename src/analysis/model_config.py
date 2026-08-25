"""Parsing/validation of dim_reduction.json, clustering.json.

Same style as build_config.py / src/retrieval/config.py: hand-written
_require_* helpers, every field validated upfront. reduction_method is
checked against REDUCTION_METHODS; clustering_methods (a non-empty list,
duplicates rejected - lessons_learned.md #5) has every element checked
against CLUSTERING_METHODS - requires those registries to already exist,
which is why this module was built after reduction.py/clustering.py (see
docs/dev/config.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.reduction import REDUCTION_METHODS


@dataclass(frozen=True)
class DimReductionConfig:
    project: str
    input_path: Path
    reduction_method: str
    params_file: Path
    output_root: Path
    session_name: str
    overwrite: bool
    fine_tuning: bool
    color_by: tuple[str, ...]
    viz_n_components: int
    write_embeddings_grid: bool
    save_tuning_embeddings: bool
    precompute_distance_metric: bool
    run_notes: str | None


@dataclass(frozen=True)
class ClusteringConfig:
    project: str
    input_path: Path
    clustering_methods: tuple[str, ...]
    params_file: Path
    output_root: Path
    session_name: str
    overwrite: bool
    fine_tuning: bool
    reduced_data: bool
    viz_embedding_path: Path | None
    run_notes: str | None


def load_dim_reduction_config(path: str | Path) -> DimReductionConfig:
    raw = _read_config(path)
    project, input_path, output_root, session_name, overwrite, run_notes = _load_shared_fields(raw)
    return DimReductionConfig(
        project=project,
        input_path=input_path,
        reduction_method=_validate_method(_require_str(raw, "reduction_method"), REDUCTION_METHODS, "reduction_method"),
        params_file=Path(_require_str(raw, "params_file")),
        output_root=output_root,
        session_name=session_name,
        overwrite=overwrite,
        fine_tuning=_require_bool(raw, "fine_tuning"),
        color_by=_require_str_list_allow_empty(raw, "color_by"),
        viz_n_components=_require_viz_n_components(raw),
        write_embeddings_grid=_require_bool(raw, "write_embeddings_grid"),
        save_tuning_embeddings=_require_bool(raw, "save_tuning_embeddings"),
        precompute_distance_metric=_require_bool(raw, "precompute_distance_metric"),
        run_notes=run_notes,
    )


def load_clustering_config(path: str | Path) -> ClusteringConfig:
    raw = _read_config(path)
    project, input_path, output_root, session_name, overwrite, run_notes = _load_shared_fields(raw)
    return ClusteringConfig(
        project=project,
        input_path=input_path,
        clustering_methods=_require_method_list(raw, "clustering_methods", CLUSTERING_METHODS),
        params_file=Path(_require_str(raw, "params_file")),
        output_root=output_root,
        session_name=session_name,
        overwrite=overwrite,
        fine_tuning=_require_bool(raw, "fine_tuning"),
        # Declarative only (docs/dev/clustering_migration_plan.md §1) - does not trigger any
        # different loading/computation, clustering.py always just clusters whatever load_matrix
        # returns for input_path. Forces every config to state explicitly whether input_path is
        # an already-computed embedding or a raw feature matrix, instead of the code silently
        # guessing from shape - matters for the viz-dimensionality handling in clustering.py.
        reduced_data=_require_bool(raw, "reduced_data"),
        # Optional (docs/dev/clustering_migration_plan.md §3) - only consulted when X has more
        # than 3 components and there is a cluster-colored scatter to plot; a companion 2D/3D
        # embedding computed separately (same reduction params as X's own, only n_components
        # different), never recomputed by clustering.py itself.
        viz_embedding_path=_optional_path(raw, "viz_embedding_path"),
        run_notes=run_notes,
    )


def _read_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")
    return raw


def _load_shared_fields(raw: dict) -> tuple[str, Path, Path, str, bool, str | None]:
    return (
        _require_str(raw, "project"),
        Path(_require_str(raw, "input_path")),
        Path(_require_str(raw, "output_root")),
        _require_str(raw, "session_name"),
        _require_bool(raw, "overwrite"),
        _optional_str(raw, "run_notes"),
    )


def _require_str(raw: dict, key: str) -> str:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string, got {value!r}")
    return value


def _require_bool(raw: dict, key: str) -> bool:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, bool):
        raise ValueError(f"config: field {key!r} must be a boolean, got {value!r}")
    return value


def _optional_str(raw: dict, key: str) -> str | None:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string when set, got {value!r}")
    return value


def _optional_path(raw: dict, key: str) -> Path | None:
    value = _optional_str(raw, key)
    return Path(value) if value is not None else None


def _validate_method(value: str, registry: dict, field_name: str) -> str:
    if value not in registry:
        raise ValueError(f"config: unknown {field_name} {value!r} - known: {sorted(registry)}")
    return value


def _require_str_list(raw: dict, key: str) -> tuple[str, ...]:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty list, got {value!r}")
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"config: field {key!r} must contain only non-empty strings, got {item!r}")
    if len(set(value)) != len(value):
        raise ValueError(f"config: field {key!r} contains duplicate entries: {value!r}")
    return tuple(value)


def _require_method_list(raw: dict, key: str, registry: dict) -> tuple[str, ...]:
    return tuple(_validate_method(m, registry, "clustering_method") for m in _require_str_list(raw, key))


def _require_str_list_allow_empty(raw: dict, key: str) -> tuple[str, ...]:
    """Like _require_str_list, but an empty list is valid (color_by's "no
    extra coloring" case) - only "the field is missing entirely" is an error,
    forcing every config to state the choice explicitly rather than fall
    back to a default. Actual color mode names (e.g. "dataset"/"volume") are
    resolved against src/analysis/embedding_coloring.COLOR_MODES at plot
    time, not here - keeps this module free of a dependency on that registry.
    """
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list):
        raise ValueError(f"config: field {key!r} must be a list, got {value!r}")
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"config: field {key!r} must contain only non-empty strings, got {item!r}")
    if len(set(value)) != len(value):
        raise ValueError(f"config: field {key!r} contains duplicate entries: {value!r}")
    return tuple(value)


def _require_viz_n_components(raw: dict) -> int:
    """viz_n_components must be 2 or 3 - the only dimensionalities any
    plotting function in this codebase supports (2D static+interactive, 3D
    interactive-only, see src/analysis/embedding_plots.py).
    """
    key = "viz_n_components"
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int) or value not in (2, 3):
        raise ValueError(f"config: field {key!r} must be 2 or 3, got {value!r}")
    return value
