"""Shared log-file-handler setup and run-duration logging for the pipeline CLI scripts.

attach_file_handler is not used by src/pipeline/retrieve_data.py, which already has its own
working copy of the same logic - left untouched rather than refactored in, to avoid
introducing risk on stable, already-in-production code that wasn't asked for. log_duration has
no such duplicate and is used by every src/pipeline/*.py entry point, retrieve_data.py included.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path


def attach_file_handler(log_path: Path) -> None:
    """Persist the same narrative already printed to console into a log file.

    Removes any FileHandler left over from a previous main() call in the same
    process (e.g. repeated invocations under pytest) - otherwise log lines
    from a later run would keep being written into an earlier run's file.
    """
    root_logger = logging.getLogger()
    for old_handler in [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]:
        root_logger.removeHandler(old_handler)
        old_handler.close()
    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root_logger.addHandler(handler)


def log_duration(start_time: datetime) -> None:
    """Logs how long the run took (H:MM:SS) since start_time, rounded to the
    nearest second - a single INFO line, separate from whatever "done - ..."/
    "cannot ..." message a pipeline's main() already logs right before it.

    Callers wrap the whole of main() after start_time is captured in a
    try/finally with this as the finally body, so duration is logged on every
    exit - a clean success (return 0) and an early return after an error
    (return 1) alike - not just the happy path: knowing how long a run took
    BEFORE it failed is exactly the case that motivated this (see
    docs/debugging/debug_25_08_26.md, a slow tuning sweep with no way to tell
    its runtime from the log alone). A failure before start_time is captured
    (argument parsing, config loading) has no start_time to measure from and
    is out of scope here - there is nothing to time yet.
    """
    elapsed = timedelta(seconds=round((datetime.now() - start_time).total_seconds()))
    logging.info("run duration: %s", elapsed)
