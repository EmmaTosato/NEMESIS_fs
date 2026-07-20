"""Shared log-file-handler setup for the analysis pipeline CLI scripts.

Not used by src/pipeline/retrieve_data.py, which already has its own working
copy of the same logic - left untouched rather than refactored in, to avoid
introducing risk on stable, already-in-production code that wasn't asked for.
"""

from __future__ import annotations

import logging
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
