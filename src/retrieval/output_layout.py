"""Where a retrieved file lands locally, relative to a subject's own folder.

Single source of truth for the local output layout - both
src.pipeline.retrieve_data (copy phase) and src.retrieval.verify (post-copy
checksum check) must agree on the exact same path for the same
(subject, RetrieveItem, filename), or verification would compare the wrong
file (or none at all). No filesystem dependency.
"""

from __future__ import annotations

from pathlib import Path

from src.retrieval.config import RetrieveItem


def local_relative_path(item: RetrieveItem, filename: str) -> Path:
    """<object>/<pipeline>/<datatype>/<filename> for objects that use a
    pipeline (today: lesion), <object>/<datatype>/<filename> for objects that
    don't (today: feature) - mirrors item.path_key() minus its trailing
    `suffix` element (suffix identifies *which* file, not a folder level).
    Depth varies by object by design - see RetrieveItem."""
    return Path(*item.path_key()[:-1], filename)
