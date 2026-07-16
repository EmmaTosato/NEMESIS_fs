"""End-to-end tests for src.pipeline.run_analysis_pipeline.main(), using a
small local fake step registry - mirrors test_retrieve_pipeline.py's
full-main()-under-tmp_path style, but with synthetic in-memory data instead
of real lesion files, since no real feature-extraction step exists yet (see
the analysis-pipeline skeleton plan - STEP_REGISTRY is intentionally empty
in this round).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.steps import StepDefinition
from src.pipeline import run_analysis_pipeline
from src.utils.step import StepResult


def _fake_source_run(prev, params):
    n_rows = params["n_rows"]
    X = np.arange(n_rows * 2, dtype=float).reshape(n_rows, 2)
    metadata = pd.DataFrame({"subject_id": [f"s{i}" for i in range(n_rows)]})
    return StepResult(X=X, metadata=metadata, params_used=params, step_name="fake_source")


def _fake_source_validate(params):
    if "n_rows" not in params or not isinstance(params["n_rows"], int):
        raise ValueError("fake_source: 'n_rows' must be an int")
    return dict(params)


def _fake_transform_run(prev, params):
    return StepResult(X=prev.X * 2, metadata=prev.metadata, params_used=params, step_name="fake_transform")


def _fake_transform_validate(params):
    return dict(params)


def _make_registry():
    return {
        "fake_source": StepDefinition(
            run=_fake_source_run, validate_params=_fake_source_validate, requires_input=False
        ),
        "fake_transform": StepDefinition(
            run=_fake_transform_run, validate_params=_fake_transform_validate, requires_input=True
        ),
    }


def _write_config(tmp_path: Path, cache_root: Path) -> Path:
    payload = {
        "modality": "fake",
        "project": "unit_test",
        "cache_root": str(cache_root),
        "overwrite_cache": False,
        "steps": [
            {"name": "fake_source", "params": {"n_rows": 5}},
            {"name": "fake_transform", "params": {}},
        ],
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload))
    return path


def test_main_end_to_end_writes_report_and_log_and_caches_every_step(tmp_path, monkeypatch):
    monkeypatch.setattr(run_analysis_pipeline, "REPORTS_ROOT", tmp_path / "reports" / "analysis_pipeline")
    monkeypatch.setattr(run_analysis_pipeline, "LOGS_ROOT", tmp_path / "logs" / "analysis_pipeline")

    cache_root = tmp_path / "cache"
    config_path = _write_config(tmp_path, cache_root)

    exit_code = run_analysis_pipeline.main(["--config", str(config_path)], registry=_make_registry())
    assert exit_code == 0

    report_dir = tmp_path / "reports" / "analysis_pipeline" / "unit_test" / "fake"
    log_dir = tmp_path / "logs" / "analysis_pipeline" / "unit_test" / "fake"
    reports = list(report_dir.glob("*.md"))
    logs = list(log_dir.glob("*.log"))
    assert len(reports) == 1
    assert len(logs) == 1

    step_dirs = sorted(cache_root.iterdir())
    assert len(step_dirs) == 2
    for step_dir in step_dirs:
        assert (step_dir / "manifest.json").is_file()


def test_main_second_run_hits_cache_for_every_step(tmp_path, monkeypatch):
    monkeypatch.setattr(run_analysis_pipeline, "REPORTS_ROOT", tmp_path / "reports" / "analysis_pipeline")
    monkeypatch.setattr(run_analysis_pipeline, "LOGS_ROOT", tmp_path / "logs" / "analysis_pipeline")

    cache_root = tmp_path / "cache"
    config_path = _write_config(tmp_path, cache_root)

    call_count = {"fake_source": 0, "fake_transform": 0}

    def counting_source_run(prev, params):
        call_count["fake_source"] += 1
        return _fake_source_run(prev, params)

    def counting_transform_run(prev, params):
        call_count["fake_transform"] += 1
        return _fake_transform_run(prev, params)

    registry = {
        "fake_source": StepDefinition(
            run=counting_source_run, validate_params=_fake_source_validate, requires_input=False
        ),
        "fake_transform": StepDefinition(
            run=counting_transform_run, validate_params=_fake_transform_validate, requires_input=True
        ),
    }

    exit_code_1 = run_analysis_pipeline.main(["--config", str(config_path)], registry=registry)
    assert exit_code_1 == 0
    assert call_count == {"fake_source": 1, "fake_transform": 1}

    exit_code_2 = run_analysis_pipeline.main(["--config", str(config_path)], registry=registry)
    assert exit_code_2 == 0
    assert call_count == {"fake_source": 1, "fake_transform": 1}  # unchanged - both cache hits


def test_main_unknown_step_name_returns_error_exit_code(tmp_path, monkeypatch):
    monkeypatch.setattr(run_analysis_pipeline, "REPORTS_ROOT", tmp_path / "reports" / "analysis_pipeline")
    monkeypatch.setattr(run_analysis_pipeline, "LOGS_ROOT", tmp_path / "logs" / "analysis_pipeline")

    payload = {
        "modality": "fake",
        "project": "unit_test",
        "cache_root": str(tmp_path / "cache"),
        "overwrite_cache": False,
        "steps": [{"name": "does_not_exist", "params": {}}],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(payload))

    exit_code = run_analysis_pipeline.main(["--config", str(config_path)], registry=_make_registry())
    assert exit_code == 1


def test_main_missing_config_file_returns_error_exit_code(tmp_path, monkeypatch):
    monkeypatch.setattr(run_analysis_pipeline, "REPORTS_ROOT", tmp_path / "reports" / "analysis_pipeline")
    monkeypatch.setattr(run_analysis_pipeline, "LOGS_ROOT", tmp_path / "logs" / "analysis_pipeline")

    exit_code = run_analysis_pipeline.main(
        ["--config", str(tmp_path / "does_not_exist.json")], registry=_make_registry()
    )
    assert exit_code == 1
