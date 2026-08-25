"""Unit tests for src/utils/logging_setup.py's log_duration.

Regression context: docs/debugging/debug_25_08_26.md - a slow UMAP tuning sweep had no way
to tell how long it had taken from the log alone, once the run was already over. log_duration
is the fix, called from a `finally` block wrapping each pipeline's main() (see the pipeline
integration tests for end-to-end wiring) so duration is logged on every exit, not just success.
"""

import logging
from datetime import datetime, timedelta

from src.utils.logging_setup import log_duration


def test_log_duration_logs_rounded_hms(caplog):
    start_time = datetime(2026, 8, 25, 10, 0, 0)
    with caplog.at_level(logging.INFO):
        log_duration(start_time)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "INFO"
    assert "run duration:" in caplog.records[0].message


def test_log_duration_formats_hours_minutes_seconds(caplog, monkeypatch):
    start_time = datetime(2026, 8, 25, 10, 0, 0)
    fake_now = start_time + timedelta(hours=1, minutes=2, seconds=5)

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_now

    monkeypatch.setattr("src.utils.logging_setup.datetime", _FixedDatetime)

    with caplog.at_level(logging.INFO):
        log_duration(start_time)

    assert "run duration: 1:02:05" in caplog.records[0].message


def test_log_duration_rounds_sub_second_elapsed_to_nearest_second(caplog, monkeypatch):
    start_time = datetime(2026, 8, 25, 10, 0, 0)
    fake_now = start_time + timedelta(seconds=44, microseconds=600_000)  # rounds up to 45s

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_now

    monkeypatch.setattr("src.utils.logging_setup.datetime", _FixedDatetime)

    with caplog.at_level(logging.INFO):
        log_duration(start_time)

    assert "run duration: 0:00:45" in caplog.records[0].message
