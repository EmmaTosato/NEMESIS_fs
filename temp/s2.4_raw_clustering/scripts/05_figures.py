"""Figures: HDBSCAN grid, agglomerative k-curves, cluster position in the (volume, disconnection load) plane."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import CACHE, IMAGES, TABLES, load_participants, load_subjects

COLORS = ["#4C78A8", "#E45756", "#54A24B", "#B279A2", "#F58518", "#9D755D"]


def hdbscan_grid() -> None:
    d = pd.read_csv(TABLES / "hdbscan_grid.csv")
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    for i, metric in enumerate(("euclidean", "cosine")):
        g = d[d["metric"] == metric]
        for j, (col, title, fmt) in enumerate((("noise_share", "noise share", "{:.0%}"), ("n_clusters", "n clusters", "{:d}"))):
            piv = g.pivot(index="min_samples", columns="min_cluster_size", values=col)
            ax = axes[i, j]
            ax.imshow(piv.values, cmap="Greys", aspect="auto", vmin=0, vmax=1 if col == "noise_share" else max(10, piv.values.max()))
            ax.set_xticks(range(piv.shape[1]), piv.columns)
            ax.set_yticks(range(piv.shape[0]), piv.index)
            for (r, c), v in np.ndenumerate(piv.values):
                ax.text(c, r, fmt.format(v), ha="center", va="center", fontsize=8, color="white" if (v > 0.5 if col == "noise_share" else v > 10) else "black")
            ax.set_title(f"{metric}: {title} (0 of 28 usable)")
            ax.set_xlabel("min_cluster_size")
            ax.set_ylabel("min_samples")
    fig.savefig(IMAGES / "hdbscan_grid.png", dpi=130)
    plt.close(fig)


def agglomerative_curves() -> None:
    d = pd.read_csv(TABLES / "agglomerative_k.csv")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), constrained_layout=True)
    for (l, m), g in d.groupby(["linkage", "metric"], sort=False):
        label = f"{l}/{m}"
        axes[0].plot(g["k"], g["silhouette"], marker="o", ms=3, label=label)
        axes[1].plot(g["k"], g["gap"], marker="o", ms=3, label=label)
        axes[2].plot(g["k"], g["smallest_share"] * 100, marker="o", ms=3, label=label)
    axes[2].axhline(1, color="k", ls="--", lw=1)
    axes[2].set_yscale("log")
    for ax, t, y in zip(axes, ("silhouette (precomputed)", "dendrogram gap h(k→k-1)/h(k+1→k)", "smallest cluster, % of subjects (dashed: 1%)"), ("silhouette", "gap", "%")):
        ax.set_title(t)
        ax.set_xlabel("k")
        ax.set_ylabel(y)
    axes[0].legend(fontsize=8)
    fig.savefig(IMAGES / "agglomerative_k.png", dpi=130)
    plt.close(fig)


def volume_load_plane() -> None:
    meta = load_subjects()
    part = load_participants(meta["subject_id"])
    agg, hdb = np.load(CACHE / "agglomerative_partitions.npz"), np.load(CACHE / "hdbscan_partitions.npz")
    panels = (("ward / euclidean, k=3", agg["linkage=ward,metric=euclidean,k=3"]), ("ward / euclidean, k=4", agg["linkage=ward,metric=euclidean,k=4"]),
              ("HDBSCAN / cosine, mcs=50 ms=20 (grey = noise)", hdb["metric=cosine,min_cluster_size=50,min_samples=20"]))
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), constrained_layout=True, sharex=True, sharey=True)
    x, y = np.log10(part["lesion_volume_voxels_2mm"]), np.log10(part["disconnection_load_voxels_2mm"])
    for ax, (title, lab) in zip(axes, panels):
        noise = lab < 0
        ax.scatter(x[noise], y[noise], s=4, c="#BBBBBB", alpha=0.5, label="noise")
        for c in np.unique(lab[~noise]):
            ax.scatter(x[lab == c], y[lab == c], s=4, c=COLORS[c % len(COLORS)], alpha=0.6, label=f"cluster {c} (n={int((lab == c).sum())})")
        ax.set_title(title)
        ax.set_xlabel("log10 lesion volume (voxels, 2 mm)")
        ax.legend(fontsize=7, markerscale=3)
    axes[0].set_ylabel("log10 disconnection load (voxels, 2 mm)")
    fig.savefig(IMAGES / "clusters_volume_load.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    hdbscan_grid()
    agglomerative_curves()
    volume_load_plane()
