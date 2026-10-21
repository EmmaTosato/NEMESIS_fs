"""`src/pipeline/enrich_metadata.py::main` e `load_config`: percorsi di successo, semantica di `overwrite`/protezione
e rami di errore (-> `return 1`, `participants.csv` intatto), su un mondo sintetico completo su disco.

Mondo: 4 soggetti UNIPD/WashU; lesion_side clinico per S1/S3, vuoto per S2/S4; geometrico per S1-S3 (S3 invertito
rispetto al clinico); SDC per S1-S3 (S4 ha has_sdc=False).
"""

from __future__ import annotations

import json
import logging
import os

import pandas as pd
import pytest

from src.pipeline import enrich_metadata as em

DATASET = "UNIPD/WashU"
S1, S2, S3, S4 = (f"sub-STUNIPD000{i}" for i in range(1, 5))
OVERRIDE_BLOCK = {
    "path": None, "copy_columns": ["lesion_volume_voxels_2mm"], "lesion_side_from": "lesion_side_2mm",
    "geometric_override_datasets": [],
}


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(em, "LOGS_ROOT", tmp_path / "logs")
    monkeypatch.setattr(em, "REPORTS_ROOT", tmp_path / "summaries")
    participants = tmp_path / "participants.csv"
    pd.DataFrame(
        {
            "subject_id": [S1, S2, S3, S4], "original_id": [S1, S2, S3, S4], "dataset": DATASET, "disease_id": "ST",
            "has_lesion": "True", "has_sdc": ["True", "True", "True", "False"], "has_features": "False",
        }
    ).to_csv(participants, index=False)
    tsv = tmp_path / "raw.tsv"
    tsv.write_text(
        "participant_id\tage\tlesion_side\tNIHSS\n"
        f"{S1}\t61\tleft\t4\n{S2}\t55\t\t7\n{S3}\t70\tright\tn/a\n{S4}\t48\t\t2\n"
    )
    sources = tmp_path / "metadata_sources.json"
    sources.write_text(json.dumps({DATASET: {"participants_tsv": str(tsv), "derivatives_dir": str(tmp_path)}}))
    lesion = tmp_path / "lesion_metadata.csv"
    pd.DataFrame(
        {
            "subject_id": [S1, S2, S3, S4], "dataset": DATASET,
            "lesion_volume_voxels_2mm": [1000, 2000, 3000, 4000],
            "lesion_side_2mm": ["left", "right", "left", None],
        }
    ).to_csv(lesion, index=False)
    sdc = tmp_path / "sdc_metadata.csv"
    pd.DataFrame(
        {"subject_id": [S1, S2, S3], "dataset": DATASET, "disconnection_load_voxels_2mm": [10.5, 20.5, 30.5]}
    ).to_csv(sdc, index=False)
    config = {
        "project": "t", "metadata_sources": str(sources), "participants_path": str(participants),
        "datasets": None, "variables": ["age", "lesion_side", "NIHSS"], "overwrite": False, "protected_path": None,
        "run_notes": "n",
        "lesion_metadata": {**OVERRIDE_BLOCK, "path": str(lesion)},
        "sdc_metadata": {"path": str(sdc), "copy_columns": ["disconnection_load_voxels_2mm"]},
    }
    return {"tmp": tmp_path, "participants": participants, "tsv": tsv, "lesion": lesion, "sdc": sdc,
            "sources": sources, "config": config}


def _run(world, *extra, **overrides) -> int:
    payload = {**world["config"], **overrides}
    path = world["tmp"] / "enrich.json"
    path.write_text(json.dumps(payload))
    return em.main(["--config", str(path), *extra])


def _table(world) -> pd.DataFrame:
    return pd.read_csv(world["participants"], dtype=str).set_index("subject_id")


def _drop(world, *keys):
    return {k: v for k, v in world["config"].items() if k not in keys}


# --- percorso felice -------------------------------------------------------------------------------


def test_first_run_writes_clinical_geometric_and_measured_columns(world, caplog):
    with caplog.at_level(logging.INFO):
        assert _run(world) == 0

    table = _table(world)
    assert table.loc[[S1, S2, S3, S4], "age"].tolist() == ["61", "55", "70", "48"]
    assert table["lesion_side"].tolist()[:3] == ["left", "right", "right"]
    assert pd.isna(table.loc[S4, "lesion_side"])
    assert table["lesion_side_source"].tolist()[:3] == ["clinical", "geometric", "clinical"]
    assert pd.isna(table.loc[S4, "lesion_side_source"])
    assert table["NIHSS"].tolist()[0:2] == ["4", "7"] and pd.isna(table.loc[S3, "NIHSS"])  # "n/a" -> vuoto
    assert table["lesion_volume_voxels_2mm"].tolist() == ["1000", "2000", "3000", "4000"]  # interi, non "1000.0"
    assert table["disconnection_load_voxels_2mm"].tolist()[:3] == ["10.5", "20.5", "30.5"]
    assert pd.isna(table.loc[S4, "disconnection_load_voxels_2mm"])
    # colonne di populate_metadata intatte, nell'ordine originale in testa
    assert list(table.reset_index().columns[:7]) == list(em._REGISTRY_OWNED_COLUMNS)
    assert "run duration" in caplog.text
    # i due avvisi sui soggetti ancora senza lato: S4 misurato ma senza lato attribuibile
    assert "remain without lesion_side - measured" in caplog.text and S4 in caplog.text


def test_report_has_a_row_per_dataset_and_the_protected_line(world):
    assert _run(world) == 0
    (report,) = list((world["tmp"] / "summaries").glob("enrich_summary__*.md"))
    text = report.read_text()
    assert "protected: none" in text
    assert f"| {DATASET} | 4 |" in text
    assert "| dataset | soggetti | age | lesion_side | NIHSS |" in text


def test_dry_run_writes_report_but_leaves_participants_byte_identical(world):
    before = world["participants"].read_bytes()
    assert _run(world, "--dry-run") == 0
    assert world["participants"].read_bytes() == before
    assert len(list((world["tmp"] / "summaries").glob("enrich_summary__*.md"))) == 1


def test_rerun_in_append_mode_keeps_existing_values_and_warns_about_the_stale_ones(world, caplog):
    assert _run(world) == 0
    world["tsv"].write_text(world["tsv"].read_text().replace(f"{S1}\t61", f"{S1}\t99"))
    with caplog.at_level(logging.WARNING):
        assert _run(world) == 0
    assert _table(world).loc[S1, "age"] == "61"  # mai sovrascritto in silenzio...
    assert "age: 1 existing value(s) differ" in caplog.text  # ...e segnalato


def test_rerun_with_overwrite_replaces_the_value(world):
    assert _run(world) == 0
    world["tsv"].write_text(world["tsv"].read_text().replace(f"{S1}\t61", f"{S1}\t99"))
    assert _run(world, overwrite=True) == 0
    table = _table(world)
    assert table.loc[S1, "age"] == "99"
    assert table.loc[S2, "lesion_side"] == "right" and table.loc[S2, "lesion_side_source"] == "geometric"


def test_geometric_override_forces_an_inverted_clinical_side_and_warns(world, caplog):
    block = {**world["config"]["lesion_metadata"], "geometric_override_datasets": [DATASET]}
    with caplog.at_level(logging.WARNING):
        assert _run(world, overwrite=True, lesion_metadata=block) == 0
    table = _table(world)
    assert table.loc[S3, ["lesion_side", "lesion_side_source"]].tolist() == ["left", "geometric"]
    assert table.loc[S1, ["lesion_side", "lesion_side_source"]].tolist() == ["left", "clinical"]
    assert "opposite to their mask" in caplog.text and S3 in caplog.text


def test_dataset_subset_leaves_the_others_untouched(world):
    other = pd.read_csv(world["participants"], dtype=str)
    other.loc[len(other)] = ["sub-STUKE0001", "sub-STUKE0001", "UKE/Other", "ST", "False", "False", "False"]
    other.to_csv(world["participants"], index=False)
    assert _run(world, datasets=[DATASET], lesion_metadata=None, sdc_metadata=None) == 0
    table = _table(world)
    assert pd.isna(table.loc["sub-STUKE0001", "age"]) and table.loc[S1, "age"] == "61"


def test_missing_column_in_one_tsv_is_a_reported_gap_not_an_error(world, caplog):
    with caplog.at_level(logging.WARNING):
        assert _run(world, variables=["age", "sex"], lesion_metadata=None, sdc_metadata=None) == 0
    assert "no 'sex' column" in caplog.text
    assert _table(world)["sex"].isna().all()
    (report,) = list((world["tmp"] / "summaries").glob("*.md"))
    assert "— (assente)" in report.read_text()


# --- configurazione -----------------------------------------------------------------------------------


def test_missing_config_file_returns_1(world, caplog):
    with caplog.at_level(logging.ERROR):
        assert em.main(["--config", str(world["tmp"] / "absent.json")]) == 1
    assert "config file not found" in caplog.text


def test_malformed_and_non_object_config_return_1(world, caplog):
    for text, expected in (("{broken", "Expecting"), ("[1]", "expected a JSON object, got list")):
        path = world["tmp"] / "bad.json"
        path.write_text(text)
        caplog.clear()
        with caplog.at_level(logging.ERROR):
            assert em.main(["--config", str(path)]) == 1
        assert expected in caplog.text


@pytest.mark.parametrize("key", ["project", "metadata_sources", "participants_path", "variables", "overwrite", "protected_path", "run_notes"])
def test_each_required_key_is_enforced(world, caplog, key):
    path = world["tmp"] / "cfg.json"
    path.write_text(json.dumps(_drop(world, key)))
    with caplog.at_level(logging.ERROR):
        assert em.main(["--config", str(path)]) == 1
    assert f"missing required key '{key}'" in caplog.text


LESION = {**OVERRIDE_BLOCK, "path": "x.csv"}


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"overwrite": "yes"}, "'overwrite' must be a boolean"),
        ({"variables": []}, "'variables' is empty"),
        ({"variables": ["age", "age"]}, "duplicate"),
        ({"variables": ["height"]}, "unknown variable"),
        ({"variables": "age"}, "list of non-empty strings"),
        ({"datasets": []}, "empty list"),
        ({"datasets": ["Nope"]}, "not in"),
        ({"datasets": [DATASET, DATASET]}, "duplicate"),
        ({"lesion_metadata": "x"}, "must be an object or null"),
        ({"lesion_metadata": {"path": "x"}}, "missing required key"),
        ({"lesion_metadata": {**LESION, "path": ""}}, "non-empty string"),
        ({"lesion_metadata": {**LESION, "copy_columns": ["has_lesion"]}}, "owned by"),
        ({"lesion_metadata": {**LESION, "lesion_side_from": ""}}, "non-empty string or null"),
        ({"lesion_metadata": {**LESION, "copy_columns": ["lesion_side_2mm"]}}, "both 'lesion_side_from' and in 'copy_columns'"),
        ({"lesion_metadata": {**LESION, "copy_columns": [], "lesion_side_from": None}}, "nothing to copy"),
        ({"lesion_metadata": {**LESION, "lesion_side_from": None, "geometric_override_datasets": [DATASET]}}, "no geometric side to force"),
        ({"variables": ["age"]}, "'lesion_side' is not in 'variables'"),
        ({"sdc_metadata": "x"}, "must be an object or null"),
        ({"sdc_metadata": {"path": "x"}}, "missing required key"),
        ({"sdc_metadata": {"path": "", "copy_columns": ["a"]}}, "non-empty string"),
        ({"sdc_metadata": {"path": "x", "copy_columns": []}}, "'copy_columns' is empty"),
        ({"sdc_metadata": {"path": "x", "copy_columns": ["has_sdc"]}}, "owned by"),
        ({"sdc_metadata": {"path": "x", "copy_columns": ["age"]}}, "two writers"),
        ({"sdc_metadata": {"path": "x", "copy_columns": ["lesion_volume_voxels_2mm"]}}, "two writers"),
        ({"protected_path": 3}, "non-empty string or null"),
    ],
)
def test_invalid_config_returns_1_and_leaves_participants_untouched(world, caplog, overrides, expected):
    before = world["participants"].read_bytes()
    with caplog.at_level(logging.ERROR):
        assert _run(world, **overrides) == 1
    assert expected in caplog.text
    assert world["participants"].read_bytes() == before


def test_missing_metadata_sources_file_returns_1(world, caplog):
    world["sources"].unlink()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "metadata_sources.json" in caplog.text


# --- ingressi mancanti o incoerenti ------------------------------------------------------------------------


def test_missing_participants_csv_returns_1(world, caplog):
    world["participants"].unlink()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "subject registry not found" in caplog.text


def test_unparseable_has_flag_in_registry_returns_1(world, caplog):
    frame = pd.read_csv(world["participants"], dtype=str)
    frame.loc[0, "has_lesion"] = "yes"
    frame.to_csv(world["participants"], index=False)
    before = world["participants"].read_bytes()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "'True'/'False'" in caplog.text
    assert world["participants"].read_bytes() == before


@pytest.mark.parametrize(
    "tsv_text, expected",
    [
        ("subject\tage\nx\t1\n", "expected a 'participant_id' column"),
        (f"participant_id\tage\n{S1}\t1\n{S1}\t2\n", "duplicate participant_id"),
        (f"participant_id\tage\n{S1}\t1\n", "have no row in"),  # S2-S4 mancano nel tsv
    ],
)
def test_malformed_raw_tsv_returns_1(world, caplog, tsv_text, expected):
    world["tsv"].write_text(tsv_text)
    with caplog.at_level(logging.ERROR):
        assert _run(world, variables=["age"], lesion_metadata=None, sdc_metadata=None) == 1
    assert expected in caplog.text


def test_missing_raw_tsv_returns_1(world, caplog):
    world["tsv"].unlink()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "raw participants.tsv not found" in caplog.text


def test_dataset_in_config_but_absent_from_registry_returns_1(world, caplog):
    sources = json.loads(world["sources"].read_text())
    sources["UKE/Ghost"] = sources[DATASET]
    world["sources"].write_text(json.dumps(sources))
    with caplog.at_level(logging.ERROR):
        assert _run(world, datasets=["UKE/Ghost"]) == 1
    assert "have no row in" in caplog.text


@pytest.mark.parametrize("column", ["subject_id", "original_id", "dataset"])
def test_registry_missing_a_key_column_returns_1(world, caplog, column):
    frame = pd.read_csv(world["participants"], dtype=str).drop(columns=[column])
    frame.to_csv(world["participants"], index=False)
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert column in caplog.text


# --- join con lesion_metadata / sdc_metadata -------------------------------------------------------------------


def _edit_csv(path, fn):
    frame = pd.read_csv(path)
    fn(frame).to_csv(path, index=False)


@pytest.mark.parametrize(
    "block, mutation, expected",
    [
        ("lesion", lambda f: f.iloc[:3], "have no row"),  # S4 ha has_lesion=True ma nessuna riga: file obsoleto
        ("lesion", lambda f: pd.concat([f, f.iloc[[0]]]), "duplicate subject_id row"),
        ("lesion", lambda f: pd.concat([f, f.iloc[[0]].assign(subject_id="sub-STUNIPD0099")]), "no row in the registry"),
        ("lesion", lambda f: f.drop(columns=["lesion_side_2mm"]), "are not in the file"),
        ("lesion", lambda f: f.drop(columns=["dataset"]), "missing required column"),
        ("sdc", lambda f: pd.concat([f, f.iloc[[0]].assign(subject_id=S4)]), "recorded as"),  # S4 has_sdc=False
        ("sdc", lambda f: f.iloc[:2], "have no row"),
        ("sdc", lambda f: f.rename(columns={"disconnection_load_voxels_2mm": "other"}), "are not in the file"),
    ],
)
def test_measured_csv_disagreeing_with_registry_returns_1_untouched(world, caplog, block, mutation, expected):
    _edit_csv(world[block], mutation)
    before = world["participants"].read_bytes()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert expected in caplog.text
    assert world["participants"].read_bytes() == before


@pytest.mark.parametrize("block", ["lesion", "sdc"])
def test_missing_measured_csv_names_the_producing_pipeline(world, caplog, block):
    world[block].unlink()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "compute_" in caplog.text and "set" in caplog.text


def test_geometric_override_with_append_mode_is_rejected(world, caplog):
    block = {**world["config"]["lesion_metadata"], "geometric_override_datasets": [DATASET]}
    with caplog.at_level(logging.ERROR):
        assert _run(world, lesion_metadata=block) == 1  # overwrite=false
    assert "append mode never does" in caplog.text


def test_geometric_override_naming_an_absent_dataset_returns_1(world, caplog):
    block = {**world["config"]["lesion_metadata"], "geometric_override_datasets": ["UKE/Ghost"]}
    with caplog.at_level(logging.ERROR):
        assert _run(world, overwrite=True, lesion_metadata=block) == 1
    assert "have no row in the registry" in caplog.text


# --- celle protette ---------------------------------------------------------------------------------------------


def _protect(world, columns=(), subjects=()):
    path = world["tmp"] / "protected.json"
    path.write_text(json.dumps({"columns": list(columns), "subjects": list(subjects)}))
    return str(path)


def test_protected_subject_and_column_survive_an_overwrite_run(world):
    assert _run(world) == 0
    world["tsv"].write_text(world["tsv"].read_text().replace("\t61\t", "\t90\t").replace("\t55\t", "\t91\t").replace("\t7\n", "\t8\n"))
    protected = _protect(world, columns=["NIHSS"], subjects=[S1])
    assert _run(world, overwrite=True, protected_path=protected) == 0
    table = _table(world)
    assert table.loc[S1, "age"] == "61"  # soggetto protetto
    assert table.loc[S2, "age"] == "91"  # non protetto: riscritto
    assert table.loc[S2, "NIHSS"] == "7"  # colonna protetta: mai riscritta
    report = sorted((world["tmp"] / "summaries").glob("*.md"))[-1]  # due run: l'ultimo per nome (= per orario)
    assert "protected (" in report.read_text()


@pytest.mark.parametrize(
    "columns, subjects, expected",
    [
        ([], ["sub-STUNIPD0099"], "a misspelt id would protect nothing"),
        (["height"], [], "protecting them does nothing"),
        (["lesion_side"], [], "must be protected together"),
    ],
)
def test_protected_file_inconsistent_with_the_registry_returns_1(world, caplog, columns, subjects, expected):
    assert _run(world) == 0
    before = world["participants"].read_bytes()
    with caplog.at_level(logging.ERROR):
        assert _run(world, overwrite=True, protected_path=_protect(world, columns, subjects)) == 1
    assert expected in caplog.text
    assert world["participants"].read_bytes() == before


def test_protecting_a_column_that_does_not_exist_yet_returns_1(world, caplog):
    with caplog.at_level(logging.ERROR):
        assert _run(world, protected_path=_protect(world, columns=["NIHSS"])) == 1
    assert "do not exist" in caplog.text


@pytest.mark.parametrize(
    "content, expected",
    [(None, "not found"), ("{broken", "not valid JSON"), ('{"columns": []}', "exactly the keys"), ("[]", "exactly the keys")],
)
def test_broken_protected_file_returns_1(world, caplog, content, expected):
    path = world["tmp"] / "protected.json"
    if content is not None:
        path.write_text(content)
    with caplog.at_level(logging.ERROR):
        assert _run(world, protected_path=str(path)) == 1
    assert expected in caplog.text


# --- scritture --------------------------------------------------------------------------------------------------------


def test_log_directory_not_creatable_returns_1(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(em, "LOGS_ROOT", blocker / "logs")
    before = world["participants"].read_bytes()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot set up log file" in caplog.text
    assert world["participants"].read_bytes() == before


def test_report_failure_returns_1_before_touching_participants(world, monkeypatch, caplog):
    blocker = world["tmp"] / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(em, "REPORTS_ROOT", blocker / "reports")
    before = world["participants"].read_bytes()
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot write output" in caplog.text
    assert world["participants"].read_bytes() == before


def test_atomic_replace_failure_returns_1_and_keeps_the_previous_file_without_temp(world, monkeypatch, caplog):
    before = world["participants"].read_bytes()
    monkeypatch.setattr(os, "replace", lambda src, dst: (_ for _ in ()).throw(OSError("disk full")))
    with caplog.at_level(logging.ERROR):
        assert _run(world) == 1
    assert "cannot write output" in caplog.text
    assert world["participants"].read_bytes() == before
    assert not list(world["tmp"].glob(".participants.csv_tmp_*"))


def test_write_table_removes_its_temp_file_when_serialization_fails(tmp_path, monkeypatch):
    def boom(self, *args, **kwargs):
        raise OSError("no space")

    monkeypatch.setattr(pd.DataFrame, "to_csv", boom)
    with pytest.raises(OSError, match="no space"):
        em.write_table(pd.DataFrame({"a": [1]}), tmp_path / "o" / "participants.csv")
    assert list((tmp_path / "o").iterdir()) == []


# --- rami residui di lesion_side e del report ---------------------------------------------------------------------


def test_subject_without_lesion_mask_and_without_clinical_side_is_warned_as_unmeasured(world, caplog):
    registry = pd.read_csv(world["participants"], dtype=str)
    registry.loc[registry["subject_id"] == S4, "has_lesion"] = "False"
    registry.to_csv(world["participants"], index=False)
    _edit_csv(world["lesion"], lambda f: f[f["subject_id"] != S4])

    with caplog.at_level(logging.WARNING):
        assert _run(world) == 0
    assert "no clinical value and no row in" in caplog.text and S4 in caplog.text
    assert pd.isna(_table(world).loc[S4, "lesion_side"])


def test_when_every_subject_has_a_clinical_side_nothing_is_filled_from_the_geometry(world, caplog):
    world["tsv"].write_text(world["tsv"].read_text().replace(f"{S2}\t55\t\t", f"{S2}\t55\tright\t").replace(f"{S4}\t48\t\t", f"{S4}\t48\tleft\t"))
    with caplog.at_level(logging.INFO):
        assert _run(world) == 0
    assert "every in-scope subject already has a clinical lesion_side" in caplog.text
    table = _table(world)
    assert set(table["lesion_side_source"]) == {"clinical"}
    assert table["lesion_side"].tolist() == ["left", "right", "right", "left"]


def test_report_lists_the_registered_column_substitution(world):
    registry = pd.read_csv(world["participants"], dtype=str)
    registry["dataset"] = "UNIPD/PASPORT"
    registry.to_csv(world["participants"], index=False)
    world["tsv"].write_text(
        "participant_id\tNIHSS_at_presentation\n" + "".join(f"{s}\t{i}\n" for i, s in enumerate((S1, S2, S3, S4), 3))
    )
    sources = json.loads(world["sources"].read_text())
    world["sources"].write_text(json.dumps({"UNIPD/PASPORT": sources[DATASET]}))
    assert _run(world, variables=["NIHSS"], lesion_metadata=None, sdc_metadata=None) == 0
    assert _table(world)["NIHSS"].tolist() == ["3", "4", "5", "6"]
    (report,) = list((world["tmp"] / "summaries").glob("*.md"))
    assert "`NIHSS` letta da `NIHSS_at_presentation`" in report.read_text()
