"""`src/pipeline/build_fc_matrix.py::main`: rami di errore, isolamento per combo e semantica di `overwrite`.

Riusa gli helper di `test_build_fc_matrix_pipeline.py` (CSV mascherati + `mask_summary.csv` + config).
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
import pytest

from src.pipeline import build_fc_matrix
from src.utils.artifacts import load_matrix
from src.utils.run_log import FIELDNAMES
from tests.integration.test_build_fc_matrix_pipeline import _write_config, _write_masked_fc

NODES = ["A", "B", "C"]


def _fc(values_ab, values_ac, values_bc):
    m = np.array([[1.0, values_ab, values_ac], [values_ab, 1.0, values_bc], [values_ac, values_bc, 1.0]])
    return pd.DataFrame(m, index=NODES, columns=NODES)


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(build_fc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_fc_matrix, "LOGS_ROOT", tmp_path / "logs")
    masked = tmp_path / "masked_fc"
    _write_masked_fc(masked, "ComboX", "sub-STUNIPD0001", _fc(0.1, 0.2, 0.3))
    _write_masked_fc(masked, "ComboX", "sub-STUNIPD0002", _fc(0.5, 0.6, 0.7))
    return {"tmp": tmp_path, "masked": masked, "out": tmp_path / "out"}


def _cfg(world, **overrides):
    return _write_config(world["tmp"], world["masked"], world["out"], overrides or None)


def _run(world, **overrides) -> int:
    return build_fc_matrix.main(["--config", str(_cfg(world, **overrides))])


# --- configurazione -----------------------------------------------------------------------------


def test_missing_config_file_returns_1(world, caplog):
    with caplog.at_level(logging.ERROR):
        assert build_fc_matrix.main(["--config", str(world["tmp"] / "absent.json")]) == 1
    assert "config file not found" in caplog.text


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"overwrite": "no"}, "overwrite"),
        ({"atlas_combos": []}, "atlas_combos"),
        ({"atlas_combos": ["ComboX", "ComboX"]}, "atlas_combos"),
        ({"session_name": 3}, "session_name"),
    ],
)
def test_invalid_config_returns_1_and_writes_nothing(world, caplog, overrides, expected):
    with caplog.at_level(logging.ERROR):
        assert _run(world, **overrides) == 1
    assert expected in caplog.text
    assert not world["out"].exists()


def test_log_directory_not_creatable_returns_1(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(build_fc_matrix, "LOGS_ROOT", blocker / "logs")
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot set up log file" in caplog.text
    assert not world["out"].exists()


# --- isolamento per combo -----------------------------------------------------------------------


def test_every_combo_failing_returns_1_listing_each_cause(world, caplog):
    with caplog.at_level(logging.WARNING):
        assert _run(world, atlas_combos=["Nope1", "Nope2"]) == 1
    assert "every configured atlas_combo failed" in caplog.text
    assert "Nope1" in caplog.text and "Nope2" in caplog.text and "no masked FC files" in caplog.text
    assert not world["out"].exists()


def test_skipped_combo_is_recorded_in_the_report_and_the_built_one_is_complete(world):
    assert _run(world, atlas_combos=["ComboX", "ComboMissing"]) == 0
    (report,) = list((world["tmp"] / "summaries" / "testproj").glob("build_summary__*.md"))
    text = report.read_text()
    assert "## Skipped (build failed)" in text
    assert "**ComboMissing**" in text and "no masked FC files" in text
    assert "| ComboX | 2x3 |" in text
    runs = pd.read_csv(world["out"] / "runs.csv")
    assert list(runs["atlas_combo"]) == ["ComboX"]  # il combo saltato non lascia una riga di log


def test_combo_without_mask_summary_is_skipped_with_the_real_cause(world, caplog):
    (world["masked"] / "ComboX" / "mask_summary.csv").unlink()
    with caplog.at_level(logging.WARNING):
        assert _run(world) == 1
    assert "mask_summary.csv" in caplog.text and "ComboX: skipped" in caplog.text


def test_combo_with_node_order_mismatch_is_skipped(world, caplog):
    swapped = _fc(0.9, 0.8, 0.7).loc[["B", "A", "C"], ["B", "A", "C"]]
    _write_masked_fc(world["masked"], "ComboX", "sub-STUNIPD0003", swapped)
    with caplog.at_level(logging.WARNING):
        assert _run(world) == 1
    assert "node order" in caplog.text and "sub-STUNIPD0003" in caplog.text


# --- scritture e confini d'errore ---------------------------------------------------------------


def test_second_run_same_day_without_overwrite_returns_1_and_keeps_first_matrix(world, caplog):
    assert _run(world) == 0
    out_dir = next((world["out"] / "ComboX").iterdir())
    before = (out_dir / "matrix.npy").read_bytes()

    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "ComboX" in caplog.text
    assert (out_dir / "matrix.npy").read_bytes() == before
    assert len(pd.read_csv(world["out"] / "runs.csv")) == 1  # nessuna riga per la run rifiutata


def test_second_run_with_overwrite_replaces_the_matrix(world):
    assert _run(world) == 0
    out_dir = next((world["out"] / "ComboX").iterdir())
    _write_masked_fc(world["masked"], "ComboX", "sub-STUNIPD0003", _fc(0.9, 0.2, 0.1))

    assert _run(world, overwrite=True) == 0
    X, metadata, extra = load_matrix(out_dir)
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002", "sub-STUNIPD0003"]
    assert X.shape == (3, 3)
    assert list(extra["edge_names"]) == ["A__B", "A__C", "B__C"]


def test_schema_drifted_runs_csv_returns_1_not_a_traceback(world, caplog):
    """Lezione #32: l'`except` attorno a `append_run_log_entry` deve coprire il `ValueError` della guardia di header."""
    world["out"].mkdir()
    (world["out"] / "runs.csv").write_text("atlas_combo,run_id,run_type,timestamp\n")
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot write run log" in caplog.text
    assert (world["out"] / "runs.csv").read_text().count("\n") == 1


def test_report_directory_not_creatable_returns_1(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(build_fc_matrix, "REPORTS_ROOT", blocker / "reports")
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot write report" in caplog.text
    assert next((world["out"] / "ComboX").iterdir()).is_dir()  # la matrice era già stata scritta


def test_save_matrix_oserror_is_a_clean_return_1(world, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(build_fc_matrix, "save_matrix", boom)
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "read-only file system" in caplog.text


# --- contenuto degli artefatti --------------------------------------------------------------------


def test_run_row_schema_params_and_input_path(world):
    assert _run(world) == 0
    runs = pd.read_csv(world["out"] / "runs.csv")
    assert list(runs.columns) == [FIELDNAMES[0], "atlas_combo", *FIELDNAMES[1:]]
    row = runs.iloc[0]
    assert (row["session"], row["atlas_combo"]) == ("s1-ComboX", "ComboX")
    assert json.loads(row["params"]) == {"n_subjects": 2, "n_edges": 3}
    assert row["input_path"] == str(world["masked"] / "ComboX")


def test_constant_edge_is_logged_as_warning_and_reported_in_readme(world, caplog):
    # A__C vale 0.2 in entrambi i soggetti: arco costante, da scartare.
    _fc(0.1, 0.2, 0.3).to_csv(world["masked"] / "ComboX" / "sub-STUNIPD0001_masked_fc.csv")
    _fc(0.5, 0.2, 0.7).to_csv(world["masked"] / "ComboX" / "sub-STUNIPD0002_masked_fc.csv")

    with caplog.at_level(logging.WARNING):
        assert _run(world) == 0
    assert "had an identical value across every subject" in caplog.text
    out_dir = next((world["out"] / "ComboX").iterdir())
    X, _, extra = load_matrix(out_dir)
    assert list(extra["edge_names"]) == ["A__B", "B__C"] and X.shape == (2, 2)
    assert "Constant edges dropped: 1" in (out_dir / "config.md").read_text()


def test_single_subject_warns_and_keeps_every_edge(world, caplog):
    for f in (world["masked"] / "ComboX").glob("sub-STUNIPD0002*"):
        f.unlink()
    pd.DataFrame([{"subject_id": "sub-STUNIPD0001", "dataset": "siteA", "n_compromised_nodes": 0}]).to_csv(
        world["masked"] / "ComboX" / "mask_summary.csv", index=False
    )
    with caplog.at_level(logging.WARNING):
        assert _run(world) == 0
    assert "only 1 subject" in caplog.text
    X, _, extra = load_matrix(next((world["out"] / "ComboX").iterdir()))
    assert X.shape == (1, 3) and len(extra["edge_names"]) == 3


def test_nan_statistics_in_report_count_the_masked_edges(world):
    masked = _fc(0.5, 0.6, 0.7)
    masked.loc["B", :] = np.nan
    masked.loc[:, "B"] = np.nan
    _write_masked_fc(world["masked"], "ComboX", "sub-STUNIPD0003", masked)
    assert _run(world) == 0
    (report,) = list((world["tmp"] / "summaries" / "testproj").glob("build_summary__*.md"))
    assert "| ComboX | 3x3 | 0 | 0/0.7/2 |" in report.read_text()
