"""The shape of a clustering result: how many clusters, how much noise, how big the largest cluster is.

One definition for the tuning (src/analysis/clustering_tuning.py, clustering_tuning_analysis.py), the production run
(src/pipeline/clustering.py) and the evaluation the Embedding Explorer and the notebooks read from
(src/analysis/clustering_evaluation.py), so the three count the same way: label -1 is noise, it is never a cluster, and
both shares are over all the subjects, noise included.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

NOISE_LABEL = -1


@dataclass(frozen=True)
class PartitionShape:
    """`cluster_sizes` maps each cluster label (noise excluded) to its number of subjects. `largest_cluster_share` is NaN
    when there is no cluster (every subject is noise): there is no largest cluster to measure."""

    n_subjects: int
    n_clusters: int
    n_noise: int
    noise_fraction: float
    largest_cluster_share: float
    cluster_sizes: dict[int, int]


def partition_shape(labels: np.ndarray) -> PartitionShape:
    """Raises ValueError if `labels` is not a non-empty 1D array: every share divides by the number of subjects."""
    labels = np.asarray(labels)
    if labels.ndim != 1 or labels.size == 0:
        raise ValueError(f"labels must be a non-empty 1D array, got shape {labels.shape}")
    clusters, sizes = np.unique(labels[labels != NOISE_LABEL], return_counts=True)
    n_noise = int((labels == NOISE_LABEL).sum())
    return PartitionShape(
        n_subjects=len(labels),
        n_clusters=len(clusters),
        n_noise=n_noise,
        noise_fraction=n_noise / len(labels),
        largest_cluster_share=float(sizes.max() / len(labels)) if len(sizes) else float("nan"),
        cluster_sizes={int(cluster): int(size) for cluster, size in zip(clusters, sizes)},
    )
