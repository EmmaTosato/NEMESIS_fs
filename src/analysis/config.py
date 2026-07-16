"""Parsing and validation for analysis-pipeline configuration files - one per
data modality (e.g. config/lesion_embedding.json, later
config/sdc_embedding.json, config/fmri_connectivity_embedding.json).

Structural validation only, same philosophy as src.retrieval.config: no
field is ever given a silent default, and every raised ValueError names the
exact offending field. Step names and per-step params are cross-validated
against a step registry (shaped like src.analysis.steps.STEP_REGISTRY)
passed in explicitly by the caller - not imported directly here - so tests
can validate against a small local fake registry without needing any real
step implementation to exist.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.analysis.steps import StepDefinition


@dataclass(frozen=True)
class StepSpec:
    name: str
    params: dict[str, Any]


@dataclass(frozen=True)
class AnalysisPipelineConfig:
    modality: str
    project: str
    cache_root: Path
    overwrite_cache: bool
    steps: list[StepSpec]


def load_config(path: str | Path, registry: dict[str, StepDefinition]) -> AnalysisPipelineConfig:
    """Load and validate an analysis-pipeline config file against `registry`.

    Raises ValueError identifying the offending field for any structural
    problem: missing/wrong-typed top-level field, an unknown step name, a
    step's own params failing its registered validator, or a step positioned
    inconsistently with its `requires_input` flag (see
    _require_valid_input_ordering).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    steps = _require_steps(raw, registry)

    return AnalysisPipelineConfig(
        modality=_require_str(raw, "modality"),
        project=_require_str(raw, "project"),
        cache_root=Path(_require_str(raw, "cache_root")),
        overwrite_cache=_require_bool(raw, "overwrite_cache"),
        steps=steps,
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


def _require_steps(raw: dict, registry: dict[str, StepDefinition]) -> list[StepSpec]:
    if "steps" not in raw:
        raise ValueError("config: missing required field 'steps'")
    items = raw["steps"]
    if not isinstance(items, list) or not items:
        raise ValueError(f"config: field 'steps' must be a non-empty list, got {items!r}")

    parsed = [_parse_step(index, item, registry) for index, item in enumerate(items)]
    _require_valid_input_ordering(parsed, registry)
    return parsed


def _parse_step(index: int, item: object, registry: dict[str, StepDefinition]) -> StepSpec:
    if not isinstance(item, dict) or "name" not in item or "params" not in item:
        raise ValueError(f"config: steps[{index}] must have 'name' and 'params', got {item!r}")

    name = item["name"]
    if not isinstance(name, str) or not name:
        raise ValueError(f"config: steps[{index}]['name'] must be a non-empty string, got {name!r}")
    if name not in registry:
        raise ValueError(
            f"config: steps[{index}] names unknown step {name!r} (known: {sorted(registry)})"
        )

    params = item["params"]
    if not isinstance(params, dict):
        raise ValueError(f"config: steps[{index}]['params'] must be an object, got {params!r}")

    try:
        validated_params = registry[name].validate_params(params)
    except ValueError as exc:
        raise ValueError(f"config: steps[{index}] ({name!r}) has invalid params: {exc}") from exc

    return StepSpec(name=name, params=validated_params)


def _require_valid_input_ordering(steps: list[StepSpec], registry: dict[str, StepDefinition]) -> None:
    """steps[0] must be a "source" step (requires_input=False - it produces
    its own StepResult from nothing); every step after it must be a
    "transform" step (requires_input=True - it consumes the previous step's
    StepResult). A misplaced source/transform step would otherwise only
    fail later, at run time, less directly - see
    src.pipeline.run_analysis_pipeline.

    Deliberately no uniqueness constraint on step names here: running the
    same step name twice with different params (e.g. two `pca` calls at
    different points in a chain) is legitimate and must not be rejected -
    unlike src.retrieval.config's `retrieve` list, where two identical
    entries genuinely would be redundant.
    """
    for index, step in enumerate(steps):
        requires_input = registry[step.name].requires_input
        if index == 0 and requires_input:
            raise ValueError(
                f"config: steps[0] ({step.name!r}) requires a previous step's output, "
                "but it is the first step in the chain"
            )
        if index > 0 and not requires_input:
            raise ValueError(
                f"config: steps[{index}] ({step.name!r}) is a source step (produces output "
                "from nothing) but is not first in the chain"
            )
