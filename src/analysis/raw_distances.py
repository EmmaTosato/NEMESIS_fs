"""Disk cache of the subject-by-subject distance matrix of a raw feature matrix, computed in the background.

The single-run evaluation of an adp run (src/analysis/clustering_evaluation.py::adp_summary) needs the
distance adp clustered in (dice on the raw matrix): about 4 minutes for the lesion matrix, up to about 25 for
the voxelwise disconnection one. Too long to block a request, too long to redo at every app start, so
RawDistanceStore computes it once in a worker thread (src/analysis/background_cache.py) and keeps it under `cache_dir`.

A cache entry is named after the *content* it was computed from (shape, dtype, a sample of rows, the
subject ids, the metric), not after a path or a date: a corrected matrix gets a new entry instead of
being served a stale one, and runs of the same matrix share one. Entries are never deleted here; an
entry no matrix points to any more is just disk (about 270 MB for 5845 subjects), safe to remove by hand.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.analysis.background_cache import BackgroundDiskCache
from src.analysis.distances import pairwise_distance

_DISTANCES_FILENAME = "distances.npy"
_NON_EMPTY_FILENAME = "non_empty.npy"
_SAMPLED_ROWS = 64


@dataclass(frozen=True)
class RawDistances:
    """`distances` is the (n_non_empty, n_non_empty) matrix between the subjects whose row of the raw
    matrix is not all zero (opened read-only, memory-mapped); `non_empty` is the boolean mask of those
    subjects over all rows. An all-zero row has an undefined dice/jaccard (denominator 0), so it is
    left out, as adp itself does (src/analysis/adp.py)."""

    non_empty: np.ndarray
    distances: np.ndarray


class RawDistanceStore:
    """The distance matrices of raw feature matrices, in a BackgroundDiskCache under `cache_dir`."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache = BackgroundDiskCache(cache_dir, "raw-distances")

    def request(self, matrix_path: Path, subject_ids: Sequence[str], metric: str) -> RawDistances | None:
        """The distances of `matrix_path`'s subjects under `metric`, or None while they are still being
        computed (the first call for a matrix starts the computation; later calls just look at it).

        `subject_ids` are the matrix's rows in order, part of the cache key. Raises whatever the
        computation raised, once: the failed attempt is forgotten, so the next call tries again.
        ValueError for an unsupported metric or a `subject_ids`/matrix length mismatch."""
        matrix = np.load(matrix_path, mmap_mode="r")
        if matrix.ndim != 2 or matrix.shape[0] != len(subject_ids):
            raise ValueError(f"{matrix_path}: matrix {matrix.shape} does not have one row per subject id ({len(subject_ids)})")
        key = _cache_key(matrix, subject_ids, metric)
        directory = self._cache.request(key, lambda temporary: _compute_into(temporary, matrix_path, metric))
        return None if directory is None else _load(directory)


def _cache_key(matrix: np.ndarray, subject_ids: Sequence[str], metric: str) -> str:
    sampled = np.linspace(0, matrix.shape[0] - 1, num=min(_SAMPLED_ROWS, matrix.shape[0]), dtype=int)
    digest = hashlib.sha1()
    digest.update(f"{matrix.shape}|{matrix.dtype}|{metric}|".encode())
    digest.update("\n".join(subject_ids).encode())
    for row in sampled:
        digest.update(np.ascontiguousarray(matrix[row]).tobytes())
    return f"{metric}-{digest.hexdigest()[:16]}"


def _compute_into(directory: Path, matrix_path: Path, metric: str) -> None:
    matrix = np.load(matrix_path, mmap_mode="r")
    non_empty = matrix.sum(axis=1, dtype=np.float64) != 0
    kept = matrix if non_empty.all() else matrix[non_empty]  # the row filter copies the matrix (1.3 GB for the lesions)
    distances = pairwise_distance(kept, metric)
    np.save(directory / _NON_EMPTY_FILENAME, non_empty)
    np.save(directory / _DISTANCES_FILENAME, distances)
    logging.info("raw distances: %s computed for %d subjects", metric, int(non_empty.sum()))


def _load(directory: Path) -> RawDistances:
    return RawDistances(
        non_empty=np.load(directory / _NON_EMPTY_FILENAME),
        distances=np.load(directory / _DISTANCES_FILENAME, mmap_mode="r"),
    )
