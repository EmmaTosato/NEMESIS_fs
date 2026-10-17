"""Unit tests for src/analysis/background_cache.py."""

import threading
import time

import pytest

from src.analysis.background_cache import BackgroundDiskCache


def _wait_for(cache, key, compute, timeout=30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        directory = cache.request(key, compute)
        if directory is not None:
            return directory
        time.sleep(0.02)
    raise AssertionError("the entry was not ready in time")


def _write(name):
    def compute(directory):
        (directory / name).write_text("done")

    return compute


def test_request_returns_none_while_the_entry_is_computed_then_its_directory(tmp_path):
    release = threading.Event()

    def slow(directory):
        release.wait(timeout=30)
        (directory / "x.txt").write_text("done")

    cache = BackgroundDiskCache(tmp_path / "cache", "test")

    assert cache.request("entry", slow) is None  # started, not finished
    assert cache.request("entry", slow) is None  # looking again does not start a second computation
    release.set()
    directory = _wait_for(cache, "entry", slow)

    assert (directory / "x.txt").read_text() == "done"


def test_an_existing_entry_is_returned_without_computing(tmp_path):
    cache = BackgroundDiskCache(tmp_path / "cache", "test")
    _wait_for(cache, "entry", _write("a.txt"))

    def refuse(_directory):
        raise AssertionError("must not recompute")

    assert BackgroundDiskCache(tmp_path / "cache", "test").request("entry", refuse) == tmp_path / "cache" / "entry"


def test_a_failed_computation_raises_once_leaves_nothing_and_is_retried(tmp_path):
    cache = BackgroundDiskCache(tmp_path / "cache", "test")

    def fail(directory):
        (directory / "partial.txt").write_text("half")
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        _wait_for(cache, "entry", fail)
    assert list((tmp_path / "cache").iterdir()) == []  # neither the entry nor the half-written temporary directory

    assert (_wait_for(cache, "entry", _write("ok.txt")) / "ok.txt").exists()
