"""`src/pipeline/mask_fc.py::main`: rami di errore e isolamento per soggetto/combo (tutti -> `return 1` pulito).

Riusa gli helper sintetici di `test_mask_fc_pipeline.py` (atlante 2 regioni, soggetti con lesione + FC).
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
import pytest

from src.pipeline import mask_fc
from src.utils.run_log import FIELDNAMES
from tests.integration.test_mask_fc_pipeline import (
    _make_atlas,
    _make_subject,
    _write_config,
)

NODES = ["Region_A", "Region_B"]
SUB1, SUB2 = "sub-STUNIPD0001", "sub-STUNIPD0002"


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(mask_fc, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(mask_fc, "LOGS_ROOT", tmp_path / "logs")
    data_root, atlas_root, output_root = tmp_path / "data", tmp_path / "atlases", tmp_path / "out"
    _make_atlas(atlas_root, "ComboX")
    _make_subject(data_root, "siteA", SUB1, "ComboX", NODES, [])
    return {"tmp": tmp_path, "data": data_root, "atlas": atlas_root, "out": output_root}


def _cfg(world, **overrides):
    return _write_config(world["tmp"], world["data"], world["atlas"], world["out"], overrides or None)


def _fc_path(world, subject, combo="ComboX"):
    return world["data"] / "siteA" / "features" / subject / "func" / f"{subject}_FC-pearson_atlas-{combo}.csv"


# --- configurazione -----------------------------------------------------------------------------


def test_missing_config_file_returns_1(world, caplog):
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(world["tmp"] / "absent.json")]) == 1
    assert "config file not found" in caplog.text


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"min_coverage": 1.5}, "min_coverage"),
        ({"binarize_threshold": -0.1}, "binarize_threshold"),
        ({"overwrite": "yes"}, "overwrite"),
        ({"atlas_combos": ["ComboX", "ComboX"]}, "atlas_combos"),
        ({"resample_interpolation": "cubic-ish"}, "resample_interpolation"),
    ],
)
def test_invalid_config_value_returns_1_naming_the_field_and_writes_nothing(world, caplog, overrides, expected):
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world, **overrides))]) == 1
    assert expected in caplog.text
    assert not world["out"].exists()


def test_config_missing_a_required_key_returns_1(world, caplog):
    path = _cfg(world)
    payload = json.loads(path.read_text())
    del payload["fc_glob_template"]
    path.write_text(json.dumps(payload))
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(path)]) == 1
    assert "fc_glob_template" in caplog.text


def test_non_object_config_returns_1(world, caplog):
    path = world["tmp"] / "list.json"
    path.write_text("[1, 2]")
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(path)]) == 1
    assert "JSON object" in caplog.text


# --- scritture e confini d'errore ---------------------------------------------------------------


def test_log_directory_not_creatable_returns_1_before_any_masking(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(mask_fc, "LOGS_ROOT", blocker / "logs")
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world))]) == 1
    assert "cannot set up log file" in caplog.text
    assert not world["out"].exists()


def test_overwrite_true_with_undeletable_output_dir_returns_1(world, monkeypatch, caplog):
    assert mask_fc.main(["--config", str(_cfg(world))]) == 0

    def boom(path, *args, **kwargs):
        raise PermissionError("read-only volume")

    monkeypatch.setattr(mask_fc.shutil, "rmtree", boom)
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world, overwrite=True))]) == 1
    assert "cannot clear existing output dir" in caplog.text and "read-only volume" in caplog.text
    assert (world["out"] / "ComboX" / f"{SUB1}_masked_fc.csv").is_file()  # il vecchio output è intatto


def test_missing_atlas_returns_1_naming_the_combo(world, caplog):
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world, atlas_combos=["ComboNoAtlas"]))]) == 1
    assert "ComboNoAtlas" in caplog.text and "atlas_path not found" in caplog.text


def test_failure_on_second_combo_keeps_first_combo_and_skips_remaining(world, caplog):
    _make_atlas(world["atlas"], "ComboC")
    _make_subject(world["data"], "siteA", SUB1, "ComboC", NODES, [])
    cfg = _cfg(world, atlas_combos=["ComboX", "ComboBroken", "ComboC"])
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(cfg)]) == 1
    assert (world["out"] / "ComboX" / "mask_summary.csv").is_file()  # già scritto, resta
    assert not (world["out"] / "ComboC").exists()  # il fallimento abortisce i combo rimanenti
    assert not list((world["tmp"] / "summaries").rglob("*.md"))  # nessun report parziale
    runs = pd.read_csv(world["out"] / "runs.csv")
    assert list(runs["atlas_combo"]) == ["ComboX"]


def test_one_unmaskable_subject_is_isolated_not_fatal(world, caplog):
    """FC con ordine dei nodi diverso: quel soggetto è saltato (e nominato), l'altro è mascherato."""
    _make_subject(world["data"], "siteA", SUB2, "ComboX", NODES, [])
    pd.DataFrame(np.eye(2), index=NODES[::-1], columns=NODES[::-1]).to_csv(_fc_path(world, SUB2), sep="\t")

    with caplog.at_level(logging.WARNING):
        assert mask_fc.main(["--config", str(_cfg(world))]) == 0

    combo_dir = world["out"] / "ComboX"
    assert (combo_dir / f"{SUB1}_masked_fc.csv").is_file()
    assert not (combo_dir / f"{SUB2}_masked_fc.csv").exists()
    assert list(pd.read_csv(combo_dir / "mask_summary.csv")["subject_id"]) == [SUB1]
    assert SUB2 in caplog.text and "could not be masked" in caplog.text


def test_summary_write_failure_returns_1(world, monkeypatch, caplog):
    real_to_csv = pd.DataFrame.to_csv

    def failing_for_summary(self, path_or_buf=None, *args, **kwargs):
        if str(path_or_buf).endswith("mask_summary.csv"):
            raise OSError("disk full")
        return real_to_csv(self, path_or_buf, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_csv", failing_for_summary)
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world))]) == 1
    assert "cannot write mask_summary.csv" in caplog.text
    assert not (world["out"] / "runs.csv").exists()  # nessuna riga di log per una run fallita


def test_schema_drifted_runs_csv_returns_1_not_a_traceback(world, caplog):
    """Lezione #32: l'`except` attorno a `append_run_log_entry` deve coprire il `ValueError` della guardia di header."""
    world["out"].mkdir()
    (world["out"] / "runs.csv").write_text(",".join(["atlas_combo", "run_id", "run_type", "timestamp"]) + "\n")
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world))]) == 1
    assert "cannot write run log" in caplog.text and "Migrate the file" in caplog.text
    assert (world["out"] / "runs.csv").read_text().count("\n") == 1  # non appesa


def test_report_directory_not_creatable_returns_1(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(mask_fc, "REPORTS_ROOT", blocker / "reports")
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world))]) == 1
    assert "cannot write report" in caplog.text


def test_runs_csv_row_has_expected_schema_and_params(world):
    assert mask_fc.main(["--config", str(_cfg(world))]) == 0
    runs = pd.read_csv(world["out"] / "runs.csv")
    assert list(runs.columns) == [FIELDNAMES[0], "atlas_combo", *FIELDNAMES[1:]]
    row = runs.iloc[0]
    assert (row["session"], row["atlas_combo"]) == ("s1-ComboX", "ComboX")
    assert json.loads(row["params"]) == {"min_coverage": 0.5, "n_subjects": 1}
    assert row["output"] == str(world["out"] / "ComboX")


def test_report_lists_each_combo_with_subject_count_and_mean_compromised(world):
    assert mask_fc.main(["--config", str(_cfg(world))]) == 0
    (report,) = list((world["tmp"] / "summaries" / "testproj").glob("mask_summary__*.md"))
    text = report.read_text()
    assert "| ComboX | 1 | 0.0 |" in text
    assert '"atlas_combos": [\n    "ComboX"' in text


def test_missing_lesion_and_group_exclusion_are_logged_with_subject_names(world, caplog):
    other = "sub-STUNIPD0007"
    fc_file = _fc_path(world, other)
    fc_file.parent.mkdir(parents=True)
    pd.DataFrame(np.eye(2), index=NODES, columns=NODES).to_csv(fc_file, sep="\t")
    hc = "sub-STUNIPDHC0001"
    _make_subject(world["data"], "siteA", hc, "ComboX", NODES, [])
    with caplog.at_level(logging.INFO):
        assert mask_fc.main(["--config", str(_cfg(world, group_filter=["ST"]))]) == 0
    assert f"{other}" in caplog.text and "no lesion mask" in caplog.text
    assert hc in caplog.text and "excluded by group_filter" in caplog.text


def test_dataset_with_no_lesion_mask_at_all_returns_1_with_the_cause(world, caplog):
    import shutil

    shutil.rmtree(world["data"] / "siteA" / "manual_masks")
    with caplog.at_level(logging.ERROR):
        assert mask_fc.main(["--config", str(_cfg(world))]) == 1
    assert "has both a lesion mask and an FC file" in caplog.text


def test_every_subject_failing_to_mask_returns_1(world, caplog):
    """Tutti i soggetti hanno un FC con nodi in ordine sbagliato: `failed` li contiene tutti, `rows` è vuoto."""
    pd.DataFrame(np.eye(2), index=NODES[::-1], columns=NODES[::-1]).to_csv(_fc_path(world, SUB1), sep="\t")
    assert mask_fc.main(["--config", str(_cfg(world))]) == 1
