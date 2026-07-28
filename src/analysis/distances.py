"""Fast pairwise distance matrices for binary feature data (e.g. voxel-wise lesion masks).

scipy.spatial.distance.pdist's boolean metrics (jaccard, dice) compute one
pair at a time - on high-dimensional sparse binary data (e.g. 254865 voxel
features) this is prohibitively slow (~19 minutes extrapolated for 1150
subjects, measured directly). Binary overlap is instead a matrix
multiplication (X @ X.T counts shared 1s for every pair at once, via BLAS) -
same result, seconds instead of minutes.
"""

from __future__ import annotations

import numpy as np

SUPPORTED_BINARY_METRICS = {"jaccard", "dice"}


def binary_pairwise_distance(X: np.ndarray, metric: str) -> np.ndarray:
    """Pairwise Jaccard or Dice distance matrix for a (n_samples, n_features) binary array.

    Raises ValueError if `metric` isn't one of SUPPORTED_BINARY_METRICS, or if
    any row is all-zero (Jaccard/Dice are undefined for a sample with no
    "on" features - union/sum would be 0).
    """
    if metric not in SUPPORTED_BINARY_METRICS:
        raise ValueError(f"unsupported metric {metric!r} for binary_pairwise_distance - supported: {sorted(SUPPORTED_BINARY_METRICS)}")

    # float64, not the input's own (often uint8) dtype: intersection counts
    # can exceed a narrow integer type's range and silently wrap (lessons_learned.md #13).
    X_float = X.astype(np.float64)
    sample_size = X_float.sum(axis=1)
    if np.any(sample_size == 0):
        raise ValueError(
            "binary_pairwise_distance requires every row to have at least one nonzero feature - "
            "an all-zero row makes jaccard/dice undefined (union or sum would be 0)"
        )

    intersection = X_float @ X_float.T
    if metric == "jaccard":
        union = sample_size[:, None] + sample_size[None, :] - intersection
        distance = 1 - intersection / union
    else:  # dice
        distance = 1 - (2 * intersection) / (sample_size[:, None] + sample_size[None, :])

    np.fill_diagonal(distance, 0.0)
    return distance
