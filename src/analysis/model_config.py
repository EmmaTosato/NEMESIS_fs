"""Parsing/validation of dim_reduction.json, dim_reduction_clustering.json, clustering.json.

Same style as build_config.py / src/retrieval/config.py: hand-written
_require_* helpers, every field validated upfront. reduction_method/
clustering_method are checked against REDUCTION_METHODS/CLUSTERING_METHODS
here - requires those registries to already exist, which is why this module
was built after reduction.py/clustering.py (see docs/dev/analysis.md).
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
    run_name: str
    overwrite: bool


@dataclass(frozen=True)
class ClusteringConfig:
    project: str
    input_path: Path
    clustering_method: str
    params_file: Path
    output_root: Path
    run_name: str
    overwrite: bool


@dataclass(frozen=True)
class DimReductionClusteringConfig:
    project: str
    input_path: Path
    reduction_method: str
    reduction_params_file: Path
    clustering_method: str
    clustering_params_file: Path
    output_root: Path
    run_name: str
    overwrite: bool


def load_dim_reduction_config(path: str | Path) -> DimReductionConfig:
    raw = _read_config(path)
    project, input_path, output_root, run_name, overwrite = _load_shared_fields(raw)
    return DimReductionConfig(
        project=project,
        input_path=input_path,
        reduction_method=_validate_method(_require_str(raw, "reduction_method"), REDUCTION_METHODS, "reduction_method"),
        params_file=Path(_require_str(raw, "params_file")),
        output_root=output_root,
        run_name=run_name,
        overwrite=overwrite,
    )


def load_clustering_config(path: str | Path) -> ClusteringConfig:
    raw = _read_config(path)
    project, input_path, output_root, run_name, overwrite = _load_shared_fields(raw)
    return ClusteringConfig(
        project=project,
        input_path=input_path,
        clustering_method=_validate_method(
            _require_str(raw, "clustering_method"), CLUSTERING_METHODS, "clustering_method"
        ),
        params_file=Path(_require_str(raw, "params_file")),
        output_root=output_root,
        run_name=run_name,
        overwrite=overwrite,
    )


def load_dim_reduction_clustering_config(path: str | Path) -> DimReductionClusteringConfig:
    raw = _read_config(path)
    project, input_path, output_root, run_name, overwrite = _load_shared_fields(raw)
    return DimReductionClusteringConfig(
        project=project,
        input_path=input_path,
        reduction_method=_validate_method(_require_str(raw, "reduction_method"), REDUCTION_METHODS, "reduction_method"),
        reduction_params_file=Path(_require_str(raw, "reduction_params_file")),
        clustering_method=_validate_method(
            _require_str(raw, "clustering_method"), CLUSTERING_METHODS, "clustering_method"
        ),
        clustering_params_file=Path(_require_str(raw, "clustering_params_file")),
        output_root=output_root,
        run_name=run_name,
        overwrite=overwrite,
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


def _load_shared_fields(raw: dict) -> tuple[str, Path, Path, str, bool]:
    return (
        _require_str(raw, "project"),
        Path(_require_str(raw, "input_path")),
        Path(_require_str(raw, "output_root")),
        _require_str(raw, "run_name"),
        _require_bool(raw, "overwrite"),
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


def _validate_method(value: str, registry: dict, field_name: str) -> str:
    if value not in registry:
        raise ValueError(f"config: unknown {field_name} {value!r} - known: {sorted(registry)}")
    return value
