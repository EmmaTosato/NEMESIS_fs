"""Fast precomputed pairwise distance matrices for umap/tsne fine-tuning and
production (src/analysis/tuning.py, src/analysis/reduction.py::embed) -
jaccard/dice/euclidean are all far faster as one precomputed matrix (BLAS)
than left to scipy/umap-learn/sklearn's own per-call machinery. See
docs/dev/models.md ("src/analysis/distances.py" section) for the measured
numbers and the two distinct root causes behind that (jaccard/dice: scipy's
own pairwise distance is slow; euclidean: umap-learn/sklearn's per-fit
neighbor search is slow, not the distance itself).

SUPPORTED_BINARY_METRICS (jaccard/dice, validated by require_binary_matrix)
vs. PRECOMPUTABLE_METRICS (every metric this module can precompute at all) -
tuning.py/reduction.py check PRECOMPUTABLE_METRICS to decide when to take
this path.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics.pairwise import euclidean_distances

SUPPORTED_BINARY_METRICS = {"jaccard", "dice"}
PRECOMPUTABLE_METRICS = SUPPORTED_BINARY_METRICS | {"euclidean"}


def require_binary_matrix(X: np.ndarray, metric: str) -> None:
    """Raises ValueError if X has any value outside {0, 1} - jaccard/dice's
    set-overlap definition is meaningless on non-binary data (see
    docs/dev/models.md). Called both by binary_pairwise_distance below and
    directly by dim_reduction.py's production path, which passes
    metric="jaccard"/"dice" straight to umap.UMAP/sklearn.TSNE without going
    through binary_pairwise_distance - both call sites must reject the same
    bad input.
    """
    if not np.all((X == 0) | (X == 1)):
        raise ValueError(
            f"metric={metric!r} requires a strictly binary (0/1) matrix - X has value(s) outside "
            "{0, 1} (e.g. a continuous matrix in [0, 1] is not a valid input for jaccard/dice - "
            "use a different metric, e.g. euclidean, or a weighted/Ruzicka-style overlap metric "
            "for continuous data instead)"
        )


def binary_pairwise_distance(X: np.ndarray, metric: str) -> np.ndarray:
    """Pairwise Jaccard or Dice distance matrix for a (n_samples, n_features) binary array.

    Raises ValueError if `metric` isn't one of SUPPORTED_BINARY_METRICS, if X
    isn't strictly binary (see require_binary_matrix), or if any row is
    all-zero (Jaccard/Dice are undefined for a sample with no "on" features -
    union/sum would be 0).
    """
    if metric not in SUPPORTED_BINARY_METRICS:
        raise ValueError(f"unsupported metric {metric!r} for binary_pairwise_distance - supported: {sorted(SUPPORTED_BINARY_METRICS)}")
    require_binary_matrix(X, metric)

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


def euclidean_pairwise_distance(X: np.ndarray) -> np.ndarray:
    """Pairwise Euclidean distance matrix for a (n_samples, n_features) array.

    No binary/domain restriction, unlike binary_pairwise_distance - any real-
    valued matrix is valid input. See this module's docstring for why this
    exists (umap-learn/sklearn's own per-fit neighbor search, not the
    distance computation, is the bottleneck at this project's scale).
    """
    return euclidean_distances(X.astype(np.float64))


def precomputed_distance(X: np.ndarray, metric: str) -> np.ndarray:
    """Dispatches to binary_pairwise_distance or euclidean_pairwise_distance by
    metric name - the single entry point tuning.py/reduction.py use once
    metric is known to be in PRECOMPUTABLE_METRICS.

    Raises ValueError for any metric outside PRECOMPUTABLE_METRICS (mirrors
    binary_pairwise_distance's own error for an unsupported binary metric).
    """
    if metric in SUPPORTED_BINARY_METRICS:
        return binary_pairwise_distance(X, metric)
    if metric == "euclidean":
        return euclidean_pairwise_distance(X)
    raise ValueError(f"unsupported metric {metric!r} for precomputed_distance - supported: {sorted(PRECOMPUTABLE_METRICS)}")
