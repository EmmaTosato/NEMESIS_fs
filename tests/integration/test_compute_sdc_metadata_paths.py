"""`src/pipeline/compute_sdc_metadata.py::main`: rami di errore, scritture atomiche e contenuto del report.

Riusa le fixture sintetiche di `tests/unit/test_compute_sdc_metadata.py` (mappe 4x4x4, registro isolato).
"""

from __future__ import annotations

import json
import logging
import os

import pandas as pd
import pytest

from src.pipeline import compute_sdc_metadata as pipeline
from tests.unit.test_compute_sdc_metadata import (  # noqa: F401  (la fixture autouse va importata per esistere qui)
    _isolated_registry,
    _make_map,
    _redirect_outputs,
    _register,
    _two_subjects,
    _write_config,
)


@pytest.fixture
def run(tmp_path, monkeypatch, _isolated_registry):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = _two_subjects(tmp_path, _isolated_registry)
    output = tmp_path / "meta" / "sdc_metadata.csv"
    return {"tmp": tmp_path, "data": data_root, "out": output, "registry": _isolated_registry}


def _main(run, *extra, **overrides) -> int:
    cfg = _write_config(run["tmp"], run["data"], run["out"], overrides or None)
    return pipeline.main(["--config", str(cfg), *extra])


# --- configurazione -----------------------------------------------------------------------------


def test_missing_config_file_returns_1(run, caplog):
    with caplog.at_level(logging.ERROR):
        assert pipeline.main(["--config", str(run["tmp"] / "absent.json")]) == 1
    assert "config file not found" in caplog.text


def test_malformed_json_config_returns_1(run, caplog):
    path = run["tmp"] / "bad.json"
    path.write_text("{not json")
    with caplog.at_level(logging.ERROR):
        assert pipeline.main(["--config", str(path)]) == 1
    assert "Expecting" in caplog.text
    assert not run["out"].exists()


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"overwrite": "yes"}, "overwrite"),
        ({"datasets": []}, "datasets"),
        ({"resample_interpolation": "bogus"}, "resample_interpolation"),
        ({"grids": {}}, "grids"),
    ],
)
def test_invalid_config_value_returns_1(run, caplog, overrides, expected):
    with caplog.at_level(logging.ERROR):
        assert _main(run, **overrides) == 1
    assert expected in caplog.text
    assert not run["out"].exists()


def test_dry_run_with_invalid_config_still_fails(run):
    assert _main(run, "--dry-run", datasets=[]) == 1
    assert not (run["tmp"] / "summaries").exists()


# --- scritture ------------------------------------------------------------------------------------


def test_log_directory_not_creatable_returns_1_before_opening_any_map(run, monkeypatch, caplog):
    blocker = run["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(pipeline, "LOGS_ROOT", blocker / "logs")
    with caplog.at_level(logging.ERROR):
        assert _main(run) == 1
    assert "cannot set up log file" in caplog.text
    assert not run["out"].exists()


def test_dry_run_report_failure_returns_1(run, monkeypatch, caplog):
    blocker = run["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(pipeline, "REPORTS_ROOT", blocker / "reports")
    with caplog.at_level(logging.ERROR):
        assert _main(run, "--dry-run") == 1
    assert "cannot write output" in caplog.text


def test_atomic_replace_failure_returns_1_and_leaves_no_csv_nor_temp(run, monkeypatch, caplog):
    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with caplog.at_level(logging.ERROR):
        assert _main(run) == 1
    assert "cannot write output" in caplog.text
    assert list(run["out"].parent.iterdir()) == []  # né CSV né file temporaneo


def test_failed_overwrite_keeps_the_previous_csv_intact(run, monkeypatch):
    assert _main(run) == 0
    before = run["out"].read_bytes()

    monkeypatch.setattr(os, "replace", lambda src, dst: (_ for _ in ()).throw(OSError("disk full")))
    assert _main(run, overwrite=True) == 1
    assert run["out"].read_bytes() == before
    assert not list(run["out"].parent.glob(".*_tmp_*"))


def test_computation_failure_with_overwrite_keeps_the_previous_csv(run):
    assert _main(run) == 0
    before = run["out"].read_bytes()
    _register(run["registry"], "sub-STUNIPD0009")  # has_sdc senza mappa su disco
    assert _main(run, overwrite=True) == 1
    assert run["out"].read_bytes() == before


def test_report_failure_after_csv_returns_1(run, monkeypatch, caplog):
    blocker = run["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(pipeline, "REPORTS_ROOT", blocker / "reports")
    with caplog.at_level(logging.ERROR):
        assert _main(run) == 1
    assert "cannot write output" in caplog.text


def test_write_csv_removes_its_temp_file_when_serialization_fails(tmp_path, monkeypatch):
    def boom(self, *args, **kwargs):
        raise OSError("no space")

    monkeypatch.setattr(pd.DataFrame, "to_csv", boom)
    with pytest.raises(OSError, match="no space"):
        pipeline._write_csv(pd.DataFrame({"subject_id": ["a"]}), tmp_path / "o" / "m.csv")
    assert list((tmp_path / "o").iterdir()) == []


# --- contenuto ------------------------------------------------------------------------------------


def test_group_filter_exclusion_is_logged_reported_and_absent_from_the_csv(run, caplog):
    hc = "sub-STUNIPDHC0001"
    _make_map(run["data"], hc, {(2, 2, 2): 1.0})
    _register(run["registry"], hc)
    with caplog.at_level(logging.INFO):
        assert _main(run) == 0

    metrics = pd.read_csv(run["out"])
    assert hc not in set(metrics["subject_id"]) and len(metrics) == 2
    assert f"excluded by group_filter=['ST']: ['{hc}']" in caplog.text
    (report,) = list((run["tmp"] / "summaries").glob("*.md"))
    text = report.read_text()
    assert f"- {hc}" in text and "1 soggetto/i esclusi" in text


def test_csv_has_no_nan_and_load_never_exceeds_brain_voxel_count(run):
    assert _main(run) == 0
    metrics = pd.read_csv(run["out"])
    assert not metrics.isna().any().any()
    assert metrics["disconnection_mean_1mm"].between(0, 1).all()
    assert metrics.dtypes["disconnection_load_voxels_1mm"].kind == "f"


def test_report_distribution_section_counts_zero_load_subjects(run):
    _make_map(run["data"], "sub-STUNIPD0003", {(0, 0, 0): 0.7})  # solo fuori dal cervello -> carico 0
    _register(run["registry"], "sub-STUNIPD0003")
    assert _main(run) == 0
    (report,) = list((run["tmp"] / "summaries").glob("*.md"))
    text = report.read_text()
    assert "## Distribuzione (1mm)" in text
    assert "soggetti con carico = 0: 1" in text
    assert "| UNIPD/WashU | 3 |" in text


def test_dry_run_report_says_nothing_was_computed(run):
    assert _main(run, "--dry-run") == 0
    (report,) = list((run["tmp"] / "summaries").glob("*.md"))
    text = report.read_text()
    assert "## Dry run" in text and "Soggetti per dataset" not in text
    assert not run["out"].exists()


def test_run_config_json_records_exactly_the_config_used(run):
    assert _main(run, resample_interpolation="nearest", run_notes="nota") == 0
    written = json.loads(run["out"].with_suffix(".config.json").read_text())
    assert written["run_notes"] == "nota"
    assert written["group_filter"] == ["ST"]
    assert written["datasets"] == ["UNIPD/WashU"]
