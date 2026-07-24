"""Parsing/validation of dim_reduction.json, dim_reduction_clustering.json, clustering.json.

Same style as build_config.py / src/retrieval/config.py: hand-written
_require_* helpers, every field validated upfront. reduction_method is
checked against REDUCTION_METHODS; clustering_methods (a non-empty list,
duplicates rejected - lessons_learned.md #5) has every element checked
against CLUSTERING_METHODS - requires those registries to already exist,
which is why this module was built after reduction.py/clustering.py (see
docs/dev/analysis.md).
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
    run_notes: str | None


@dataclass(frozen=True)
class DimReductionClusteringConfig:
    project: str
    input_path: Path
    reduction_method: str
    reduction_params_file: Path
    clustering_methods: tuple[str, ...]
    clustering_params_file: Path
    output_root: Path
    session_name: str
    overwrite: bool
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
        run_notes=run_notes,
    )


def load_dim_reduction_clustering_config(path: str | Path) -> DimReductionClusteringConfig:
    raw = _read_config(path)
    project, input_path, output_root, session_name, overwrite, run_notes = _load_shared_fields(raw)
    return DimReductionClusteringConfig(
        project=project,
        input_path=input_path,
        reduction_method=_validate_method(_require_str(raw, "reduction_method"), REDUCTION_METHODS, "reduction_method"),
        reduction_params_file=Path(_require_str(raw, "reduction_params_file")),
        clustering_methods=_require_method_list(raw, "clustering_methods", CLUSTERING_METHODS),
        clustering_params_file=Path(_require_str(raw, "clustering_params_file")),
        output_root=output_root,
        session_name=session_name,
        overwrite=overwrite,
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
