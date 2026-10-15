"""HDBSCAN (sklearn, metric="precomputed") on the raw-matrix distances: 7 x 4 grid per metric."""
from __future__ import annotations

import itertools
import time

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN
from sklearn.metrics import silhouette_score

from common import CACHE, MAX_K, MAX_LARGEST, MAX_NOISE, METRICS, MIN_K, TABLES, load_distance, peak_rss_gb

MIN_CLUSTER_SIZE = (10, 15, 20, 30, 50, 75, 100)
MIN_SAMPLES = (1, 5, 10, 20)


def usable(n_clusters: int, noise: float, largest: float) -> bool:
    return MIN_K <= n_clusters <= MAX_K and noise <= MAX_NOISE and largest <= MAX_LARGEST


def summarize(labels: np.ndarray, D: np.ndarray) -> dict:
    n = len(labels)
    clustered = labels >= 0
    sizes = np.bincount(labels[clustered]) if clustered.any() else np.array([], dtype=int)
    k = len(sizes)
    sil = float("nan")
    if k >= 2 and clustered.sum() > k:
        idx = np.flatnonzero(clustered)
        sil = float(silhouette_score(D[np.ix_(idx, idx)], labels[idx], metric="precomputed"))
    noise = float((~clustered).mean())
    largest = float(sizes.max() / n) if k else 0.0
    return {
        "n_clusters": k, "noise_share": noise, "largest_share": largest,
        "smallest_size": int(sizes.min()) if k else 0, "silhouette_nonnoise": sil,
        "usable": usable(k, noise, largest),
    }


def main() -> None:
    rows, partitions = [], {}
    for metric in METRICS:
        D = load_distance(metric)
        D64 = D.astype(np.float64)  # sklearn precomputed path; float32 would be copied anyway (copy=True)
        for mcs, ms in itertools.product(MIN_CLUSTER_SIZE, MIN_SAMPLES):
            t0 = time.perf_counter()
            labels = HDBSCAN(min_cluster_size=mcs, min_samples=ms, metric="precomputed", copy=True).fit_predict(D64)
            fit_s = time.perf_counter() - t0
            row = {"metric": metric, "min_cluster_size": mcs, "min_samples": ms, **summarize(labels, D), "fit_seconds": round(fit_s, 1), "peak_rss_gb": round(peak_rss_gb(), 2)}
            rows.append(row)
            partitions[f"metric={metric},min_cluster_size={mcs},min_samples={ms}"] = labels.astype(np.int32)
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
        del D64
    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "hdbscan_grid.csv", index=False)
    np.savez_compressed(CACHE / "hdbscan_partitions.npz", **partitions)
    print(df.groupby("metric")["usable"].agg(["sum", "count"]))


if __name__ == "__main__":
    main()
