"""`src/pipeline/populate_metadata.py::main`: percorsi di successo, idempotenza e rami di errore (-> `return 1`).

Mondo sintetico su disco: una `participants.tsv`, gli alberi `derivatives/<data_type>/sub-*`, il registro
`metadata_sources.json`. `LOGS_ROOT`/`REPORTS_ROOT` (relativi alla cwd) puntano a `tmp_path`.
"""

from __future__ import annotations

import json
import logging
import os

import pandas as pd
import pytest

from src.pipeline import populate_metadata as pm

DATASET = "UNIPD/WashU"
ST = ["sub-STUNIPD0001", "sub-STUNIPD0002"]
HC = "sub-STUNIPDHC0001"


@pytest.fixture(autouse=True)
def _drop_file_handlers():
    yield
    root = logging.getLogger()
    for handler in [h for h in root.handlers if isinstance(h, logging.FileHandler)]:
        root.removeHandler(handler)
        handler.close()


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(pm, "LOGS_ROOT", tmp_path / "logs")
    monkeypatch.setattr(pm, "REPORTS_ROOT", tmp_path / "summaries")
    tsv = tmp_path / "participants_WashU.tsv"
    pd.DataFrame(
        {
            "participant_id": [*ST, HC, "sub-STUNIPD0003"],  # 0003: solo nel tsv
            "disease_id": ["ST", "ST", "HC", "ST"],
        }
    ).to_csv(tsv, sep="\t", index=False)
    derivatives = tmp_path / "derivatives"
    for sid in (*ST, HC, "sub-STUNIPD0099"):  # 0099: solo su disco
        (derivatives / "manual_masks" / sid).mkdir(parents=True)
    (derivatives / "bcbtoolkit" / ST[0]).mkdir(parents=True)
    sources = tmp_path / "metadata_sources.json"
    sources.write_text(json.dumps({DATASET: {"participants_tsv": str(tsv), "derivatives_dir": str(derivatives)}}))
    config = {
        "project": "t",
        "metadata_sources": str(sources),
        "datasets": [DATASET],
        "group_filter": ["ST"],
        "output_path": str(tmp_path / "out" / "participants.csv"),
        "overwrite": False,
        "run_notes": "n",
    }
    return {"tmp": tmp_path, "tsv": tsv, "derivatives": derivatives, "sources": sources, "config": config}


def _run(world, **overrides) -> int:
    payload = {**world["config"], **overrides}
    path = world["tmp"] / "cfg.json"
    path.write_text(json.dumps(payload))
    return pm.main(["--config", str(path)])


def _output(world) -> pd.DataFrame:
    return pd.read_csv(world["config"]["output_path"], dtype=str)


def test_happy_path_writes_table_report_and_log(world, caplog):
    with caplog.at_level(logging.INFO):  # sotto pytest basicConfig è un no-op: il livello va alzato a mano
        assert _run(world) == 0

    table = _output(world)
    assert list(table.columns) == pm.OWN_COLUMNS
    assert list(table["subject_id"]) == ST  # HC escluso dal group_filter, 0003/0099 dall'ammissione
    assert table["disease_id"].eq("ST").all()
    assert table.set_index("subject_id").loc[ST[0], ["has_lesion", "has_sdc", "has_features"]].tolist() == [
        "True", "True", "False",
    ]
    assert table.set_index("subject_id").loc[ST[1], "has_sdc"] == "False"
    assert not table.isna().any().any()

    (report,) = list((world["tmp"] / "summaries").glob("populate_summary__*.md"))
    text = report.read_text()
    assert "sub-STUNIPD0003" in text  # solo nel tsv
    assert "sub-STUNIPD0099" in text  # solo su disco
    assert HC in text  # escluso per gruppo
    (log,) = list((world["tmp"] / "logs").glob("populate_summary__*.log"))
    assert "run duration" in log.read_text()


def test_group_filter_null_admits_healthy_controls(world):
    assert _run(world, group_filter=None) == 0
    table = _output(world)
    assert HC in set(table["subject_id"])
    assert table.set_index("subject_id").loc[HC, "disease_id"] == "HC"


def test_second_run_without_overwrite_leaves_existing_file_byte_identical(world):
    assert _run(world) == 0
    out = world["tmp"] / "out" / "participants.csv"
    before = out.read_bytes()
    assert _run(world) == 0
    assert out.read_bytes() == before


def test_rerun_appends_a_newly_arrived_subject_without_touching_enriched_columns(world):
    assert _run(world) == 0
    out = world["tmp"] / "out" / "participants.csv"
    enriched = pd.read_csv(out, dtype=str)
    enriched["age"] = ["54", "61"]
    enriched.to_csv(out, index=False)

    new = "sub-STUNIPD0004"
    pd.concat([pd.read_csv(world["tsv"], sep="\t", dtype=str), pd.DataFrame({"participant_id": [new], "disease_id": ["ST"]})]).to_csv(
        world["tsv"], sep="\t", index=False
    )
    (world["derivatives"] / "features" / new).mkdir(parents=True)

    assert _run(world) == 0
    table = pd.read_csv(out, dtype=str).set_index("subject_id")
    assert list(table.index) == [*ST, new]
    assert table.loc[ST, "age"].tolist() == ["54", "61"]
    assert pd.isna(table.loc[new, "age"])
    assert table.loc[new, "has_features"] == "True"


def test_overwrite_true_drops_vanished_subject_and_lists_it_in_report(world):
    assert _run(world) == 0
    import shutil

    shutil.rmtree(world["derivatives"] / "manual_masks" / ST[1])
    assert _run(world, overwrite=True) == 0

    assert list(_output(world)["subject_id"]) == [ST[0]]
    report = sorted((world["tmp"] / "summaries").glob("populate_summary__*.md"))[-1]  # due run: l'ultimo per orario
    assert f"- {ST[1]}" in report.read_text()


def test_disease_id_mismatch_is_reported_and_id_wins(world):
    pd.DataFrame({"participant_id": ST, "disease_id": ["ST", "PD"]}).to_csv(world["tsv"], sep="\t", index=False)
    assert _run(world) == 0
    assert _output(world).set_index("subject_id").loc[ST[1], "disease_id"] == "ST"
    (report,) = list((world["tmp"] / "summaries").glob("populate_summary__*.md"))
    assert "tsv says 'PD', subject id says 'ST'" in report.read_text()


def test_non_subject_directory_is_warned_and_ignored(world, caplog):
    (world["derivatives"] / "features" / "stray_dir").mkdir(parents=True)
    with caplog.at_level(logging.WARNING):
        assert _run(world) == 0
    assert "non-subject director" in caplog.text and "stray_dir" in caplog.text
    assert "stray_dir" not in "".join(_output(world)["subject_id"])


# --- errori di configurazione ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutation, expected",
    [
        ({"project": None}, "missing required key 'project'"),
        ({"metadata_sources": None}, "missing required key 'metadata_sources'"),
        ({"datasets": None}, "missing required key 'datasets'"),
        ({"output_path": None}, "missing required key 'output_path'"),
        ({"overwrite": None}, "missing required key 'overwrite'"),
        ({"run_notes": None}, "missing required key 'run_notes'"),
        ({"datasets": []}, "'datasets' is empty"),
        ({"datasets": DATASET}, "must be a list of strings"),
        ({"datasets": [1]}, "must be a list of strings"),
        ({"datasets": [DATASET, DATASET]}, "duplicate"),
        ({"group_filter": []}, "empty list"),
        ({"group_filter": ["ST", "ST"]}, "duplicate"),
        ({"group_filter": "ST"}, "must be a list of strings"),
        ({"overwrite": "true"}, "must be a boolean"),
        ({"datasets": ["Nowhere/Nothing"]}, "not in"),
    ],
)
def test_invalid_config_returns_1_and_names_the_cause(world, caplog, mutation, expected):
    payload = dict(world["config"])
    for key, value in mutation.items():
        if value is None and key in payload and key != "group_filter":
            del payload[key]
        else:
            payload[key] = value
    cfg = world["tmp"] / "cfg.json"
    cfg.write_text(json.dumps(payload))

    with caplog.at_level(logging.ERROR):
        assert pm.main(["--config", str(cfg)]) == 1

    assert expected in caplog.text
    assert not (world["tmp"] / "out").exists()  # nessuna scrittura


@pytest.mark.parametrize(
    "content, expected",
    [
        (None, "No such file"),
        ("{not json", "Expecting"),
        ("[1, 2]", "expected a JSON object, got list"),
    ],
)
def test_unreadable_config_file_returns_1(world, caplog, content, expected):
    cfg = world["tmp"] / "broken.json"
    if content is not None:
        cfg.write_text(content)
    with caplog.at_level(logging.ERROR):
        assert pm.main(["--config", str(cfg)]) == 1
    assert expected in caplog.text


def test_missing_metadata_sources_file_returns_1(world, caplog):
    world["sources"].unlink()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "metadata_sources.json" in caplog.text


# --- errori sugli input -----------------------------------------------------------------------------


def test_missing_participants_tsv_returns_1(world, caplog):
    world["tsv"].unlink()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "participants.tsv not found" in caplog.text
    assert not (world["tmp"] / "out").exists()


@pytest.mark.parametrize(
    "tsv_text, expected",
    [
        ("subject\tdisease_id\nsub-STUNIPD0001\tST\n", "expected a 'participant_id' column"),
        ("participant_id\nweird-id\n", "matches neither the canonical"),
        ("participant_id\nsub-STUNIPD0001\nsub-STUNIPD0001\n", "duplicate subject id"),
    ],
)
def test_malformed_participants_tsv_returns_1(world, caplog, tsv_text, expected):
    world["tsv"].write_text(tsv_text)
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert expected in caplog.text


def test_existing_output_without_subject_id_column_is_refused_untouched(world, caplog):
    out = world["tmp"] / "out" / "participants.csv"
    out.parent.mkdir()
    out.write_text("foo,bar\n1,2\n")
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "refusing to merge" in caplog.text
    assert out.read_text() == "foo,bar\n1,2\n"


def test_unparseable_existing_output_returns_1(world):
    """Un CSV esistente corrotto (campi in eccesso) deve dare `return 1`, non un traceback del parser."""
    out = world["tmp"] / "out" / "participants.csv"
    out.parent.mkdir()
    out.write_text('subject_id,x\n"unterminated,1\n')
    assert _run(world) == 1


# --- errori di scrittura ---------------------------------------------------------------------------


def test_log_directory_not_creatable_returns_1(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("file, non cartella")
    monkeypatch.setattr(pm, "LOGS_ROOT", blocker / "logs")
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot set up log file" in caplog.text
    assert not (world["tmp"] / "out").exists()


def test_output_replace_failure_returns_1_and_leaves_previous_file_and_no_temp(world, monkeypatch, caplog):
    assert _run(world) == 0
    out = world["tmp"] / "out" / "participants.csv"
    before = out.read_bytes()

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with caplog.at_level(logging.ERROR):
        assert _run(world, overwrite=True) == 1
    assert "cannot write output" in caplog.text
    assert out.read_bytes() == before
    assert not list(out.parent.glob(".*_tmp_*"))


def test_report_directory_not_creatable_returns_1(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("x")
    monkeypatch.setattr(pm, "REPORTS_ROOT", blocker / "reports")
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot write output" in caplog.text


def test_write_table_removes_its_temp_file_when_serialization_fails(tmp_path, monkeypatch):
    def boom(self, *args, **kwargs):
        raise OSError("no space")

    monkeypatch.setattr(pd.DataFrame, "to_csv", boom)
    with pytest.raises(OSError, match="no space"):
        pm.write_table(pd.DataFrame({"subject_id": ["a"]}), tmp_path / "o" / "participants.csv")
    assert list((tmp_path / "o").iterdir()) == []
