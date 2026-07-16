"""Unit tests for src.analysis.config - structural validation of
analysis-pipeline config files.

Uses a small local fake step registry (see _make_registry) rather than any
real step implementation - src.analysis.config only needs a registry shaped
like src.analysis.steps.STEP_REGISTRY, never a specific one, so these tests
exercise the config parsing/validation logic in isolation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.config import load_config
from src.analysis.steps import StepDefinition
from src.utils.step import StepResult


def _fake_source_run(prev: StepResult | None, params: dict) -> StepResult:
    n_rows = params["n_rows"]
    X = np.zeros((n_rows, 2))
    metadata = pd.DataFrame({"subject_id": [f"s{i}" for i in range(n_rows)]})
    return StepResult(X=X, metadata=metadata, params_used=params, step_name="fake_source")


def _fake_source_validate(params: dict) -> dict:
    if "n_rows" not in params or not isinstance(params["n_rows"], int):
        raise ValueError("fake_source: 'n_rows' must be an int")
    return dict(params)


def _fake_transform_run(prev: StepResult | None, params: dict) -> StepResult:
    assert prev is not None
    return StepResult(X=prev.X, metadata=prev.metadata, params_used=params, step_name="fake_transform")


def _fake_transform_validate(params: dict) -> dict:
    if "multiplier" not in params or not isinstance(params["multiplier"], int):
        raise ValueError("fake_transform: 'multiplier' must be an int")
    return dict(params)


def _make_registry() -> dict[str, StepDefinition]:
    return {
        "fake_source": StepDefinition(
            run=_fake_source_run, validate_params=_fake_source_validate, requires_input=False
        ),
        "fake_transform": StepDefinition(
            run=_fake_transform_run, validate_params=_fake_transform_validate, requires_input=True
        ),
    }


def _write_config(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload))
    return path


def _valid_payload() -> dict:
    return {
        "modality": "lesion",
        "project": "clinical_connectome",
        "cache_root": "data/derived/lesion_embedding",
        "overwrite_cache": False,
        "steps": [
            {"name": "fake_source", "params": {"n_rows": 10}},
            {"name": "fake_transform", "params": {"multiplier": 2}},
        ],
    }


def test_valid_config_loads(tmp_path):
    path = _write_config(tmp_path, _valid_payload())
    config = load_config(path, _make_registry())
    assert config.modality == "lesion"
    assert config.project == "clinical_connectome"
    assert config.cache_root == Path("data/derived/lesion_embedding")
    assert config.overwrite_cache is False
    assert [s.name for s in config.steps] == ["fake_source", "fake_transform"]
    assert config.steps[0].params == {"n_rows": 10}


def test_missing_config_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "does_not_exist.json", _make_registry())


@pytest.mark.parametrize("missing_key", ["modality", "project", "cache_root", "overwrite_cache", "steps"])
def test_missing_required_field_raises(tmp_path, missing_key):
    payload = _valid_payload()
    del payload[missing_key]
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValueError, match=missing_key):
        load_config(path, _make_registry())


def test_empty_steps_list_raises(tmp_path):
    payload = _valid_payload()
    payload["steps"] = []
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValueError, match="steps"):
        load_config(path, _make_registry())


def test_unknown_step_name_raises(tmp_path):
    payload = _valid_payload()
    payload["steps"][0]["name"] = "does_not_exist"
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValueError, match="does_not_exist"):
        load_config(path, _make_registry())


def test_transform_step_first_raises(tmp_path):
    """A step with requires_input=True must never be first in the chain -
    there is no previous StepResult to give it."""
    payload = _valid_payload()
    payload["steps"] = [{"name": "fake_transform", "params": {"multiplier": 2}}]
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValueError, match=r"steps\[0\]"):
        load_config(path, _make_registry())


def test_source_step_after_first_position_raises(tmp_path):
    """A step with requires_input=False (a "source" step) must only appear
    at index 0 - a second one later in the chain would silently discard
    the previous step's output instead of consuming it."""
    payload = _valid_payload()
    payload["steps"] = [
        {"name": "fake_source", "params": {"n_rows": 10}},
        {"name": "fake_source", "params": {"n_rows": 5}},
    ]
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValueError, match=r"steps\[1\]"):
        load_config(path, _make_registry())


def test_invalid_step_params_raises(tmp_path):
    payload = _valid_payload()
    payload["steps"][1]["params"] = {"multiplier": "not-an-int"}
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValueError, match="multiplier"):
        load_config(path, _make_registry())


def test_duplicate_step_names_with_different_params_allowed(tmp_path):
    """Regression guard: unlike src.retrieval.config's `retrieve` list,
    `steps` must NOT reject repeated step names - running the same step
    twice with different params (e.g. two `pca` calls at different points
    in a chain) is legitimate and must load successfully."""
    payload = _valid_payload()
    payload["steps"] = [
        {"name": "fake_source", "params": {"n_rows": 10}},
        {"name": "fake_transform", "params": {"multiplier": 2}},
        {"name": "fake_transform", "params": {"multiplier": 3}},
    ]
    path = _write_config(tmp_path, payload)
    config = load_config(path, _make_registry())
    assert [s.name for s in config.steps] == ["fake_source", "fake_transform", "fake_transform"]
    assert config.steps[1].params == {"multiplier": 2}
    assert config.steps[2].params == {"multiplier": 3}
