"""Test a proprieta' di `src/utils/logging_setup.py` (handler su file, durata) e
`src/utils/metadata_sources.py` (parsing del registro dataset -> path)."""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.metadata_sources import DatasetSource, load_metadata_sources


@pytest.fixture
def root_logger():
    """Root logger a livello INFO; a fine test si ripristinano handler e livello originali."""
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    root.setLevel(logging.INFO)
    yield root
    for handler in root.handlers[:]:
        if handler not in saved_handlers:
            root.removeHandler(handler)
            handler.close()
    for handler in saved_handlers:
        if handler not in root.handlers:
            root.addHandler(handler)
    root.setLevel(saved_level)


def _file_handlers(root: logging.Logger) -> list[logging.FileHandler]:
    return [h for h in root.handlers if isinstance(h, logging.FileHandler)]


# Messaggi su una sola riga, UTF-8 sicuro (niente surrogati), senza "\n"/"\r"/separatori Unicode di riga.
_MESSAGE = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Zl", "Zp")), min_size=1, max_size=30
)


@settings(max_examples=25)
@given(n_calls=st.integers(1, 4), messages=st.lists(_MESSAGE, min_size=1, max_size=4))
def test_only_the_last_attached_file_receives_messages(root_logger, n_calls, messages):
    with tempfile.TemporaryDirectory() as tmp:
        paths = [Path(tmp) / f"run{i}.log" for i in range(n_calls)]
        handlers = []
        for path in paths:
            attach_file_handler(path)
            handlers.append(_file_handlers(root_logger)[-1])
            assert len(_file_handlers(root_logger)) == 1  # mai due FileHandler insieme
        for message in messages:
            logging.info(message)
        last = _file_handlers(root_logger)[0]
        last.flush()

        assert last is handlers[-1]
        assert all(h.stream is None for h in handlers[:-1])  # i precedenti sono stati chiusi
        assert paths[-1].read_text(encoding="utf-8").split("\n") == [f"INFO: {m}" for m in messages] + [""]
        assert all(p.read_text(encoding="utf-8") == "" for p in paths[:-1])


def test_non_file_handlers_survive_and_levelname_prefix_format(root_logger, tmp_path):
    stream_handler = logging.StreamHandler()
    root_logger.addHandler(stream_handler)
    attach_file_handler(tmp_path / "a.log")
    attach_file_handler(tmp_path / "b.log")

    assert stream_handler in root_logger.handlers
    logging.warning("w %s", "x")
    logging.error("e")
    _file_handlers(root_logger)[0].flush()
    assert (tmp_path / "b.log").read_text() == "WARNING: w x\nERROR: e\n"


def test_attach_in_a_missing_directory_raises_oserror_and_adds_no_handler(root_logger, tmp_path):
    with pytest.raises(OSError):
        attach_file_handler(tmp_path / "missing_dir" / "run.log")
    assert _file_handlers(root_logger) == []


@settings(max_examples=40)
@given(seconds=st.integers(0, 40 * 86400))
def test_log_duration_reports_whole_seconds_as_h_mm_ss(caplog, seconds):
    start = datetime.now() - timedelta(seconds=seconds, milliseconds=200)  # 0.2 s sopra: lontano dal .5 del round
    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_duration(start)

    [record] = caplog.records
    assert record.levelno == logging.INFO
    assert record.getMessage() == f"run duration: {timedelta(seconds=seconds)}"


# --- metadata_sources --------------------------------------------------------------------------

_PATH_TEXT = st.text(alphabet="abcXYZ012/_.-", min_size=1, max_size=15).filter(lambda p: p.strip() != "")
_ENTRY = st.fixed_dictionaries({"participants_tsv": _PATH_TEXT, "derivatives_dir": _PATH_TEXT})
_NAME = st.text(alphabet="ABCabc-_", min_size=1, max_size=8)


def _load(raw_text: str):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "metadata_sources.json"
        path.write_text(raw_text)
        return load_metadata_sources(path)


@given(st.dictionaries(_NAME, _ENTRY, min_size=1, max_size=5))
def test_valid_registry_roundtrips_in_order_as_paths(raw):
    sources = _load(json.dumps(raw))
    assert list(sources) == list(raw)
    for name, entry in raw.items():
        assert sources[name] == DatasetSource(Path(entry["participants_tsv"]), Path(entry["derivatives_dir"]))
        assert isinstance(sources[name].participants_tsv, Path)


@given(st.dictionaries(_NAME, _ENTRY, min_size=1, max_size=3), st.dictionaries(st.text(min_size=1, max_size=6), st.integers(), max_size=3))
def test_unknown_extra_keys_in_an_entry_are_ignored(raw, extra):
    padded = {k: {**v, **{f"x_{ek}": ev for ek, ev in extra.items()}} for k, v in raw.items()}
    assert _load(json.dumps(padded)) == _load(json.dumps(raw))


@given(st.sampled_from([[], {}, "text", 5, 1.5, None, True, [{"participants_tsv": "a", "derivatives_dir": "b"}]]))
def test_non_object_or_empty_top_level_raises_valueerror(payload):
    with pytest.raises(ValueError, match="non-empty JSON object"):
        _load(json.dumps(payload))


@given(st.sampled_from([[], "text", 5, None, True, ["participants_tsv", "derivatives_dir"]]))
def test_entry_that_is_not_an_object_raises_valueerror_naming_the_dataset(entry):
    with pytest.raises(ValueError, match="'UCL'"):
        _load(json.dumps({"UCL": entry}))


_BAD_LEAF = st.sampled_from([None, 5, 1.5, True, [], ["a/b"], {}, {"p": "a"}])


@given(key=st.sampled_from(["participants_tsv", "derivatives_dir"]), bad=_BAD_LEAF, drop=st.booleans())
def test_wrong_typed_or_missing_leaf_raises_valueerror_never_typeerror(key, bad, drop):
    entry = {"participants_tsv": "a.tsv", "derivatives_dir": "d"}
    if drop:
        del entry[key]
    else:
        entry[key] = bad
    with pytest.raises(ValueError, match=key):
        _load(json.dumps({"UCL": entry}))


@given(st.sampled_from(["", "{", "nope", '{"a": }', "[1,"]))
def test_malformed_json_raises_valueerror(text):
    with pytest.raises(ValueError):  # json.JSONDecodeError e' una sottoclasse
        _load(text)


def test_missing_file_raises_filenotfounderror(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_metadata_sources(tmp_path / "nope.json")


def test_one_bad_dataset_fails_the_whole_registry(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"OK": {"participants_tsv": "a", "derivatives_dir": "b"}, "BAD": {"participants_tsv": "a"}}))
    with pytest.raises(ValueError, match="BAD"):
        load_metadata_sources(path)


@pytest.mark.parametrize("key", ["participants_tsv", "derivatives_dir"])
@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_path_string_raises_valueerror(tmp_path, key, blank):
    entry = {"participants_tsv": "a.tsv", "derivatives_dir": "d", key: blank}
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"UCL": entry}))
    with pytest.raises(ValueError):
        load_metadata_sources(path)


def test_duplicate_dataset_key_in_json_raises_valueerror(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(
        '{"UCL": {"participants_tsv": "a.tsv", "derivatives_dir": "d1"},'
        ' "UCL": {"participants_tsv": "b.tsv", "derivatives_dir": "d2"}}'
    )
    with pytest.raises(ValueError):
        load_metadata_sources(path)
