"""A directory of cache entries, each computed once in a worker thread and written atomically.

For results too slow to compute inside a request (minutes) and worth keeping across app starts: the
adp distance matrix (src/analysis/raw_distances.py), the voxelwise t-maps of a PCA run's components
(src/analysis/component_maps.py). The caller names an entry by a key built from the *content* it is
computed from, so a changed input gets a new entry instead of a stale one; this module owns the thread,
the atomic write and the error handling, nothing about what the entry holds.
"""

from __future__ import annotations

import logging
import os
import shutil
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path


class BackgroundDiskCache:
    """One worker thread (two multi-minute computations in parallel would only fight for the cores and the
    memory), one cache directory. Plain instance state, owned by whoever builds it. Entries are never
    deleted here: one no input points to any more is just disk, safe to remove by hand."""

    def __init__(self, cache_dir: Path, thread_name_prefix: str) -> None:
        self._cache_dir = Path(cache_dir)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=thread_name_prefix)
        self._pending: dict[str, Future] = {}
        self._lock = threading.Lock()

    def request(self, key: str, compute: Callable[[Path], None]) -> Path | None:
        """The directory of entry `key` once it exists, or None while it is still being computed (the first
        call for a key starts the computation; later calls just look at it).

        `compute(directory)` writes the entry's files into an empty temporary directory it is given. If it
        raises, the exception is raised here, once, and the failed attempt is forgotten, so the next call
        tries again."""
        directory = self._cache_dir / key
        if directory.is_dir():
            return directory
        with self._lock:
            future = self._pending.get(key)
            if future is None:
                logging.info("background cache: computing entry %s", key)
                future = self._executor.submit(_build, compute, directory)
                self._pending[key] = future
        if not future.done():
            return None
        with self._lock:
            self._pending.pop(key, None)
        future.result()
        return directory


def _build(compute: Callable[[Path], None], directory: Path) -> None:
    """Runs `compute` into a temporary sibling of `directory`, renamed into place as the last step, so
    `directory` never exists half written (same swap as src/utils/artifacts.py::save_matrix)."""
    temporary = directory.with_name(f"{directory.name}.tmp-{os.getpid()}")
    temporary.mkdir(parents=True)
    try:
        compute(temporary)
        os.replace(temporary, directory)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    logging.info("background cache: entry %s saved", directory)
