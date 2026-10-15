"""Agglomerative (scipy linkage on the condensed matrix): ward/euclidean, average+complete x euclidean/cosine; k = 3..30."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import cophenet, cut_tree, fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score

from common import CACHE, TABLES, load_distance, peak_rss_gb

COMBOS = (("ward", "euclidean"), ("average", "euclidean"), ("complete", "euclidean"), ("average", "cosine"), ("complete", "cosine"))
KS = range(3, 31)
MIN_SHARE = 0.01


def main() -> None:
    rows, summary, partitions = [], [], {}
    for metric in ("euclidean", "cosine"):
        D = load_distance(metric)
        n = D.shape[0]
        condensed = squareform(D.astype(np.float64), checks=False)
        for method, m in COMBOS:
            if m != metric:
                continue
            t0 = time.perf_counter()
            Z = linkage(condensed, method=method)
            link_s = time.perf_counter() - t0
            coph = float(cophenet(Z, condensed)[0])
            heights = Z[:, 2]
            if np.any(np.diff(heights) < -1e-12):
                raise ValueError(f"{method}/{metric}: non-monotone dendrogram heights")
            summary.append({"linkage": method, "metric": metric, "cophenetic_corr": coph, "linkage_seconds": round(link_s, 1), "peak_rss_gb": round(peak_rss_gb(), 2)})
            for k in KS:
                # cut by merge order, not by height: with tied heights (complete/cosine saturates at 1.0) a height cut
                # (fcluster maxclust) cannot return exactly k clusters; the tie is reported in tied_at_cut instead.
                labels = cut_tree(Z, n_clusters=k).ravel()
                tied = bool(heights[n - k] == heights[n - k - 1])
                if labels.max() + 1 != k:
                    raise ValueError(f"{method}/{metric}: cut_tree gave {labels.max() + 1} clusters for k={k}")
                if not tied:  # without a tie both cuts must be the same partition
                    ref = fcluster(Z, k, criterion="maxclust") - 1
                    if len(np.unique(ref)) != k or len(np.unique(np.c_[ref, labels], axis=0)) != k:
                        raise ValueError(f"{method}/{metric}: cut_tree and fcluster disagree at k={k} without a height tie")
                sizes = np.bincount(labels)
                rows.append({
                    "linkage": method, "metric": metric, "k": k,
                    "silhouette": float(silhouette_score(D, labels, metric="precomputed")),
                    "smallest_size": int(sizes.min()), "smallest_share": float(sizes.min() / n), "largest_share": float(sizes.max() / n),
                    "gap": float(heights[n - k] / heights[n - k - 1]),  # merge k->k-1 over merge k+1->k
                    "min_size_ok": bool(sizes.min() / n >= MIN_SHARE), "tied_at_cut": tied,
                })
                partitions[f"linkage={method},metric={metric},k={k}"] = labels.astype(np.int32)
            print(summary[-1], flush=True)
    pd.DataFrame(rows).to_csv(TABLES / "agglomerative_k.csv", index=False)
    pd.DataFrame(summary).to_csv(TABLES / "agglomerative_cophenetic.csv", index=False)
    np.savez_compressed(CACHE / "agglomerative_partitions.npz", **partitions)


if __name__ == "__main__":
    main()
