"""Test a proprietà di `src/utils/run_log.append_run_log_entry`: N append -> N righe leggibili
(anche se il file ha perso l'a-capo finale), nessuna scrittura parziale sugli errori, schema coerente."""

from __future__ import annotations

import csv
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from src.utils.run_log import FIELDNAMES, append_run_log_entry

# Celle CSV arbitrarie: virgole, virgolette, a-capo (anche \r), unicode, ma niente surrogati
# isolati (non codificabili in UTF-8) né NUL.
_CELL = st.text(alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"), max_size=25)
_RUN_ID = st.text(alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"), min_size=1, max_size=15)
_EXTRA_KEY = st.from_regex(r"[a-z][a-z_]{0,8}", fullmatch=True).filter(lambda k: k not in FIELDNAMES)
_JSON_LEAF = st.none() | st.booleans() | st.integers(-10**9, 10**9) | st.floats(allow_nan=False, allow_infinity=False) | _CELL
_PARAMS = st.dictionaries(_CELL, st.recursive(_JSON_LEAF, lambda c: st.lists(c, max_size=3) | st.dictionaries(_CELL, c, max_size=3), max_leaves=6), max_size=4)
_NOW = st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2068, 12, 31))

# Righe da accodare: (run_id, notes, params, now)
_ENTRY = st.tuples(_RUN_ID, st.none() | _CELL, _PARAMS, _NOW)


def _read(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="") as f:
        return list(csv.DictReader(f))


def _append(log_dir, entry, run_type="production", extra=None, idx=0):
    run_id, notes, params, now = entry
    append_run_log_entry(log_dir, run_id, now, run_type, params, Path(f"out/{idx}"), notes, Path(f"in/{idx}"), extra)


@given(entries=st.lists(_ENTRY, min_size=1, max_size=5), run_type=st.sampled_from(["production", "tuning"]))
def test_n_appends_give_n_readable_rows_with_exact_fields(entries, run_type):
    with tempfile.TemporaryDirectory() as tmp:
        for i, entry in enumerate(entries):
            _append(Path(tmp), entry, run_type, idx=i)
        rows = _read(Path(tmp) / ("runs.csv" if run_type == "production" else "runs_tuning.csv"))

    assert len(rows) == len(entries)
    for i, (row, (run_id, notes, params, now)) in enumerate(zip(rows, entries)):
        assert list(row) == FIELDNAMES  # nessuna colonna extra/restkey
        assert row["session"] == run_id.split("_", 1)[0]
        assert row["notes"] == (notes or "")
        assert json.loads(row["params"]) == params
        assert row["input_path"] == f"in/{i}" and row["output"] == f"out/{i}"
        assert datetime.strptime(row["timestamp"], "%d-%m-%y %H:%M") == now.replace(second=0, microsecond=0)


@given(
    first=_ENTRY,
    second=_ENTRY,
    cut_bytes=st.sampled_from([1, 2]),
    extra=st.dictionaries(_EXTRA_KEY, _CELL, max_size=2),
)
def test_append_after_losing_trailing_newline_keeps_both_rows_separate(first, second, cut_bytes, extra):
    """Il file perde l'a-capo finale (modifica a mano / run uccisa): la riga successiva non va incollata."""
    with tempfile.TemporaryDirectory() as tmp:
        _append(Path(tmp), first, "tuning", extra or None)
        runs_csv = Path(tmp) / "runs_tuning.csv"
        raw = runs_csv.read_bytes()
        assert raw.endswith(b"\r\n")
        runs_csv.write_bytes(raw[:-cut_bytes])  # 1 = resta '\r'; 2 = manca il terminatore (il caso che incollava)

        _append(Path(tmp), second, "tuning", extra or None, idx=1)
        rows = _read(runs_csv)

    assert len(rows) == 2
    assert all(None not in row for row in rows)  # niente restkey: nessuna riga sovradimensionata
    assert [r["output"] for r in rows] == ["out/0", "out/1"]
    assert rows[0]["notes"] == (first[1] or "") and rows[1]["notes"] == (second[1] or "")
    assert json.loads(rows[1]["params"]) == second[2]


@given(entries=st.lists(_ENTRY, min_size=1, max_size=4), extra=st.dictionaries(_EXTRA_KEY, _CELL, min_size=1, max_size=3))
def test_extra_columns_land_right_after_session_in_every_row(entries, extra):
    with tempfile.TemporaryDirectory() as tmp:
        for i, entry in enumerate(entries):
            _append(Path(tmp), entry, extra=extra, idx=i)
        rows = _read(Path(tmp) / "runs.csv")

    expected_header = [FIELDNAMES[0], *extra, *FIELDNAMES[1:]]
    assert len(rows) == len(entries)
    for row in rows:
        assert list(row) == expected_header
        assert {k: row[k] for k in extra} == extra


@given(
    first_extra=st.dictionaries(_EXTRA_KEY, _CELL, max_size=3),
    second_extra=st.dictionaries(_EXTRA_KEY, _CELL, max_size=3),
    entry=_ENTRY,
)
def test_schema_mismatch_raises_valueerror_and_leaves_file_byte_identical(first_extra, second_extra, entry):
    """Stessi extra_columns (stesso ordine) -> ok; chiavi diverse o ordine diverso -> ValueError, file intatto."""
    with tempfile.TemporaryDirectory() as tmp:
        _append(Path(tmp), entry, extra=first_extra or None)
        runs_csv = Path(tmp) / "runs.csv"
        before = runs_csv.read_bytes()

        if list(first_extra) == list(second_extra):
            _append(Path(tmp), entry, extra=second_extra or None, idx=1)
            assert len(_read(runs_csv)) == 2
        else:
            with pytest.raises(ValueError, match="header"):
                _append(Path(tmp), entry, extra=second_extra or None, idx=1)
            assert runs_csv.read_bytes() == before


@given(bad=st.text(max_size=12).filter(lambda s: s not in ("production", "tuning")), entry=_ENTRY)
def test_any_other_run_type_raises_and_writes_nothing(bad, entry):
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="run_type"):
            append_run_log_entry(Path(tmp), entry[0], entry[3], bad, entry[2], Path("o"), entry[1], Path("i"))
        assert list(Path(tmp).iterdir()) == []


@given(entry=_ENTRY)
def test_log_dir_is_created_when_missing(entry):
    with tempfile.TemporaryDirectory() as tmp:
        nested = Path(tmp) / "a" / "b" / "umap"
        _append(nested, entry)
        assert len(_read(nested / "runs.csv")) == 1


@pytest.mark.parametrize("content", [b"", b"\n", b"not,the,header\n", b"session\r\n"])
def test_preexisting_file_with_wrong_or_empty_header_raises_valueerror_and_is_not_touched(tmp_path, content):
    runs_csv = tmp_path / "runs.csv"
    runs_csv.write_bytes(content)
    with pytest.raises(ValueError, match="header"):
        append_run_log_entry(tmp_path, "s1_r", datetime(2026, 1, 1), "production", {}, Path("o"), None, Path("i"))
    assert runs_csv.read_bytes() == content


def test_log_dir_that_is_a_file_raises_oserror(tmp_path):
    blocker = tmp_path / "umap"
    blocker.write_text("i am a file")
    with pytest.raises(OSError):
        append_run_log_entry(blocker, "s1_r", datetime(2026, 1, 1), "production", {}, Path("o"), None, Path("i"))
    assert blocker.read_text() == "i am a file"


@settings(max_examples=25)
@given(entries=st.lists(_ENTRY, min_size=1, max_size=3))
def test_production_and_tuning_logs_are_independent(entries):
    with tempfile.TemporaryDirectory() as tmp:
        for i, entry in enumerate(entries):
            _append(Path(tmp), entry, "production", idx=i)
        assert not (Path(tmp) / "runs_tuning.csv").exists()
        _append(Path(tmp), entries[0], "tuning")
        assert len(_read(Path(tmp) / "runs.csv")) == len(entries)
        assert len(_read(Path(tmp) / "runs_tuning.csv")) == 1


@pytest.mark.parametrize("reserved", FIELDNAMES)
def test_extra_column_colliding_with_a_reserved_field_raises(tmp_path, reserved):
    with pytest.raises(ValueError):
        append_run_log_entry(
            tmp_path, "s1_r", datetime(2026, 1, 1), "production", {}, Path("o"), "n", Path("i"), {reserved: "x"}
        )
