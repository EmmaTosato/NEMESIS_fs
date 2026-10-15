"""Euclidean + cosine distance matrices (5845 x 5845, float32) of the raw s2.4-vol SDC matrix, validated and cached."""
from __future__ import annotations

import json
import time

import numpy as np
from scipy.spatial.distance import cdist

from common import CACHE, MATRIX_DIR, METRICS, TABLES, load_subjects, peak_rss_gb
from src.analysis.distances import pairwise_distance

CHUNK = 20000
N_CHECK = 200


def cosine_distance(X: np.ndarray) -> np.ndarray:
    """1 - cos, rows normalised to unit norm, Gram accumulated over column blocks in float64 (X never copied whole)."""
    n = X.shape[0]
    sq = np.zeros(n, dtype=np.float64)
    for s in range(0, X.shape[1], CHUNK):
        b = np.asarray(X[:, s : s + CHUNK], dtype=np.float64)
        sq += (b * b).sum(axis=1)
    norm = np.sqrt(sq)
    if np.any(norm == 0):
        raise ValueError(f"{int((norm == 0).sum())} all-zero row(s): cosine undefined")
    gram = np.zeros((n, n), dtype=np.float64)
    for s in range(0, X.shape[1], CHUNK):
        b = np.asarray(X[:, s : s + CHUNK], dtype=np.float64) / norm[:, None]
        gram += b @ b.T
    D = 1.0 - gram
    np.fill_diagonal(D, 0.0)
    return np.maximum(D, 0.0)  # 1 - cos can be -1e-16 by rounding; true cosine distance is >= 0


def validate(D: np.ndarray, X: np.ndarray, metric: str) -> dict:
    n = D.shape[0]
    if D.shape != (n, n):
        raise ValueError(f"{metric}: not square {D.shape}")
    if not np.isfinite(D).all():
        raise ValueError(f"{metric}: non-finite values")
    if np.any(np.diag(D) != 0):
        raise ValueError(f"{metric}: non-zero diagonal")
    asym = float(np.abs(D - D.T).max())
    if asym > 0:
        raise ValueError(f"{metric}: not symmetric, max |D - D.T| = {asym}")
    if D.min() < 0:
        raise ValueError(f"{metric}: negative distance {D.min()}")
    rows = np.sort(np.random.default_rng(0).choice(n, N_CHECK, replace=False))
    sub = np.asarray(X[rows], dtype=np.float64)  # 200 x 291345; the full-row comparison would need a 13.6 GB float64 copy of X
    ref = cdist(sub, sub, metric=metric)
    err = np.abs(D[np.ix_(rows, rows)].astype(np.float64) - ref)
    tol = 1e-4 * max(1.0, float(ref.max())) if metric == "euclidean" else 1e-5
    if err.max() > tol:
        raise ValueError(f"{metric}: max |D - cdist| = {err.max():.3e} on {N_CHECK} rows exceeds tol {tol:.1e}")
    off = D[~np.eye(n, dtype=bool)]
    return {
        "metric": metric, "n": n, "symmetric": True, "diag_zero": True, "finite": True,
        "max_abs_err_vs_cdist_200x200": float(err.max()), "tol": tol,
        "min_offdiag": float(off.min()), "median_offdiag": float(np.median(off)), "max": float(D.max()),
        "n_zero_offdiag_pairs": int((off == 0).sum()),
    }


def main() -> None:
    X = np.load(MATRIX_DIR / "matrix.npy", mmap_mode="r")
    if X.shape[0] != len(load_subjects()):
        raise ValueError("matrix rows != metadata rows")
    report = []
    for metric in METRICS:
        t0 = time.perf_counter()
        D64 = pairwise_distance(X, "euclidean") if metric == "euclidean" else cosine_distance(X)
        elapsed = time.perf_counter() - t0
        D = D64.astype(np.float32)
        del D64
        print(f"{metric}: computed in {elapsed:.0f}s, validating", flush=True)
        info = validate(D, X, metric)
        info.update(compute_seconds=round(elapsed, 1), peak_rss_gb=round(peak_rss_gb(), 2))
        np.save(CACHE / f"D_{metric}.npy", D)  # only a validated matrix reaches the cache
        print(json.dumps(info), flush=True)
        report.append(info)
    import pandas as pd
    pd.DataFrame(report).to_csv(TABLES / "distances_validation.csv", index=False)


if __name__ == "__main__":
    main()
