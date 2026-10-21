"""Test a proprieta' di `src/utils/participants.py`: registro soggetti e lista esclusi."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest
from hypothesis import assume, given, strategies as st

import src.utils.participants as participants
from src.utils.participants import (
    KNOWN_EXCLUSION_REASONS,
    KNOWN_EXCLUSION_SCOPES,
    load_excluded_subjects,
    load_participants_registry,
    participants_registry_path,
)

_ASKABLE = [s for s in KNOWN_EXCLUSION_SCOPES if s != "all"]
_NARROW = tuple(_ASKABLE)

# Valori che pandas legge come NaN anche con dtype=str: esclusi dalle celle "normali".
_NA_LIKE = {"", "na", "nan", "null", "none", "n/a", "-nan", "-na"}
_TOKEN = st.text(alphabet="abcdefXYZ0123456789_-", min_size=1, max_size=10).filter(lambda t: t.lower() not in _NA_LIKE)
_IDS = st.lists(_TOKEN, min_size=1, max_size=8, unique=True)


def _write_registry(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _registry_frame(ids, datasets=None, flags=None) -> pd.DataFrame:
    n = len(ids)
    flags = flags or [("True", "False", "True")] * n
    return pd.DataFrame(
        {
            "subject_id": ids,
            "dataset": datasets or ["siteA"] * n,
            "has_lesion": [f[0] for f in flags],
            "has_sdc": [f[1] for f in flags],
            "has_features": [f[2] for f in flags],
        }
    )


# --- participants_registry_path / load_participants_registry ---------------------------------

@given(root=st.text(alphabet="abc/_-", min_size=1, max_size=12))
def test_registry_path_follows_metadata_root_at_call_time(root):
    with mock.patch.object(participants, "METADATA_ROOT", Path(root)):
        assert participants_registry_path() == Path(root) / "participants.csv"


@given(ids=_IDS, data=st.data())
def test_registry_roundtrip_has_real_bools_and_preserves_string_ids(ids, data):
    flags = [tuple(data.draw(st.sampled_from(["True", "False"])) for _ in range(3)) for _ in ids]
    ids = [f"0{i}" if i.isdigit() else i for i in ids]  # id che iniziano per 0: non devono perdere lo zero
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "participants.csv"
        _write_registry(path, _registry_frame(ids, flags=flags))
        reg = load_participants_registry(path)

    assert list(reg["subject_id"]) == ids
    for j, col in enumerate(("has_lesion", "has_sdc", "has_features")):
        assert reg[col].dtype == bool
        assert list(reg[col]) == [f[j] == "True" for f in flags]


@given(ids=_IDS, column=st.sampled_from(["has_lesion", "has_sdc", "has_features"]), data=st.data())
def test_any_flag_that_is_not_literally_True_or_False_raises_valueerror(ids, column, data):
    bad = data.draw(st.text(max_size=8).filter(lambda s: s not in ("True", "False")))
    row = data.draw(st.integers(0, len(ids) - 1))
    frame = _registry_frame(ids)
    frame.loc[row, column] = bad
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "participants.csv"
        _write_registry(path, frame)
        with pytest.raises(ValueError, match=column):
            load_participants_registry(path)


@given(ids=_IDS, dup_index=st.integers(0, 7))
def test_duplicate_subject_id_raises_valueerror(ids, dup_index):
    ids = [*ids, ids[dup_index % len(ids)]]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "participants.csv"
        _write_registry(path, _registry_frame(ids))
        with pytest.raises(ValueError, match="duplicate"):
            load_participants_registry(path)


@pytest.mark.parametrize("drop", ["subject_id", "dataset", "has_lesion", "has_sdc", "has_features"])
def test_missing_required_column_raises_valueerror(tmp_path, drop):
    path = tmp_path / "participants.csv"
    _write_registry(path, _registry_frame(["a", "b"]).drop(columns=drop))
    with pytest.raises(ValueError, match=drop):
        load_participants_registry(path)


def test_missing_registry_raises_filenotfounderror(tmp_path):
    with pytest.raises(FileNotFoundError, match="populate_metadata"):
        load_participants_registry(tmp_path / "nope.csv")


@given(ids=_IDS)
def test_registry_keeps_extra_columns_untouched(ids):
    frame = _registry_frame(ids).assign(original_id=[f"x{i}" for i in ids], disease_id="ST")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "participants.csv"
        _write_registry(path, frame)
        reg = load_participants_registry(path)
    assert list(reg.columns) == list(frame.columns)
    assert list(reg["original_id"]) == list(frame["original_id"])


# --- load_excluded_subjects --------------------------------------------------------------------

@st.composite
def _exclusion_files(draw):
    """(registry rows, exclusion rows): ogni soggetto o ha UNA riga 'all', o righe in scope stretti distinti."""
    ids = draw(_IDS)
    datasets = {i: draw(st.sampled_from(["siteA", "siteB"])) for i in ids}
    rows = []
    for i in ids:
        if draw(st.booleans()):
            scopes = ["all"]
        else:
            scopes = draw(st.lists(st.sampled_from(_NARROW), min_size=1, max_size=3, unique=True))
        for scope in scopes:
            rows.append(
                {
                    "subject_id": i,
                    "dataset": datasets[i],
                    "reason": draw(st.sampled_from(KNOWN_EXCLUSION_REASONS)),
                    "scope": scope,
                    "value": draw(st.floats(-1e9, 1e9, allow_nan=False, allow_infinity=False)),
                }
            )
    draw(st.randoms(use_true_random=False)).shuffle(rows)
    return datasets, rows


def _excluded_env(tmp: str, datasets: dict, rows: list[dict]):
    root = Path(tmp) / "metadata"
    _write_registry(root / "participants.csv", _registry_frame(list(datasets), list(datasets.values())))
    list_path = Path(tmp) / "excluded_subjects.csv"
    pd.DataFrame(rows, columns=["subject_id", "dataset", "reason", "scope", "value"]).to_csv(list_path, index=False)
    return root, list_path


@given(_exclusion_files(), st.sampled_from(_ASKABLE))
def test_each_scope_gets_exactly_its_own_rows_plus_all_in_file_order(env, scope):
    datasets, rows = env
    with tempfile.TemporaryDirectory() as tmp:
        root, list_path = _excluded_env(tmp, datasets, rows)
        with mock.patch.object(participants, "METADATA_ROOT", root):
            result = load_excluded_subjects(list_path, scope)

    expected = [r for r in rows if r["scope"] in ("all", scope)]
    assert list(result["subject_id"]) == [r["subject_id"] for r in expected]
    assert list(result["scope"]) == [r["scope"] for r in expected]
    assert result["value"].dtype == "float64"
    assert list(result["value"]) == pytest.approx([r["value"] for r in expected])
    assert list(result.index) == list(range(len(expected)))


@given(_exclusion_files())
def test_asking_every_scope_covers_each_row_at_least_once_and_all_rows_everywhere(env):
    datasets, rows = env
    with tempfile.TemporaryDirectory() as tmp:
        root, list_path = _excluded_env(tmp, datasets, rows)
        with mock.patch.object(participants, "METADATA_ROOT", root):
            results = {s: load_excluded_subjects(list_path, s) for s in _ASKABLE}

    all_ids = {r["subject_id"] for r in rows if r["scope"] == "all"}
    for scope, res in results.items():
        assert all_ids <= set(res["subject_id"])
        assert set(res["scope"]) <= {"all", scope}
    assert sum(len(res) for res in results.values()) == sum(
        len(_ASKABLE) if r["scope"] == "all" else 1 for r in rows
    )


@given(_exclusion_files(), st.sampled_from(_ASKABLE), st.text(max_size=10).filter(lambda t: t not in KNOWN_EXCLUSION_REASONS))
def test_a_bad_row_for_another_scope_still_fails_the_whole_file(env, asked, bad_reason):
    datasets, rows = env
    assume(rows)
    other = next((s for s in _ASKABLE if s != asked), asked)
    rows = [*rows, {"subject_id": "zz-unregistered", "dataset": "siteA", "reason": bad_reason, "scope": other, "value": 1.0}]
    with tempfile.TemporaryDirectory() as tmp:
        root, list_path = _excluded_env(tmp, datasets, rows)
        with mock.patch.object(participants, "METADATA_ROOT", root), pytest.raises(ValueError):
            load_excluded_subjects(list_path, asked)


@given(_exclusion_files(), st.sampled_from(["nan", "abc", "1,5", "--3", "0x1"]))
def test_non_numeric_value_raises_valueerror(env, bad):
    datasets, rows = env
    rows = [dict(rows[0], value=bad), *rows[1:]]
    with tempfile.TemporaryDirectory() as tmp:
        root, list_path = _excluded_env(tmp, datasets, rows)
        with mock.patch.object(participants, "METADATA_ROOT", root):
            for scope in _ASKABLE:
                with pytest.raises(ValueError, match="value"):
                    load_excluded_subjects(list_path, scope)


@given(_exclusion_files(), st.sampled_from(_ASKABLE))
def test_wrong_dataset_for_a_registered_subject_raises(env, scope):
    datasets, rows = env
    rows = [dict(rows[0], dataset="siteZ"), *rows[1:]]
    with tempfile.TemporaryDirectory() as tmp:
        root, list_path = _excluded_env(tmp, datasets, rows)
        with mock.patch.object(participants, "METADATA_ROOT", root), pytest.raises(ValueError, match="dataset"):
            load_excluded_subjects(list_path, scope)


@given(_exclusion_files(), st.sampled_from(_ASKABLE), st.sampled_from(["all-plus-narrow", "duplicate-scope"]))
def test_contradictory_or_duplicated_rows_raise_for_every_scope_asked(env, asked, kind):
    datasets, rows = env
    if kind == "all-plus-narrow":
        base = next((r for r in rows if r["scope"] == "all"), None)
        assume(base is not None)
        extra = dict(base, scope=_NARROW[0])
    else:
        extra = dict(rows[0])  # stessa (subject_id, scope)
    with tempfile.TemporaryDirectory() as tmp:
        root, list_path = _excluded_env(tmp, datasets, [*rows, extra])
        with mock.patch.object(participants, "METADATA_ROOT", root), pytest.raises(ValueError):
            load_excluded_subjects(list_path, asked)


@given(st.text(max_size=12).filter(lambda s: s not in _ASKABLE))
def test_any_unaskable_scope_raises_before_touching_the_file(scope):
    with pytest.raises(ValueError, match="scope"):
        load_excluded_subjects(Path("/definitely/not/there.csv"), scope)
