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

pairwise_distance is the odd one out: a single entry point for the same three metrics that also
accepts a *continuous* non-negative matrix (weighted dice/jaccard) and never converts a whole
raw matrix to float64 - the input of src/analysis/adp.py, which runs on the raw voxel matrices.
"""

from __future__ import annotations

import numpy as np
from joblib import Parallel, delayed
from scipy.spatial.distance import cdist
from sklearn.metrics.pairwise import euclidean_distances

SUPPORTED_BINARY_METRICS = {"jaccard", "dice"}
PRECOMPUTABLE_METRICS = SUPPORTED_BINARY_METRICS | {"euclidean"}

# Columns per block in pairwise_distance's Gram matrix: bounds the float copy of X held in memory
# at once (a raw voxel matrix is ~5000 x 264274), and keeps every float32 block product exact for
# a binary X (integer counts <= _GRAM_CHUNK < 2**24).
_GRAM_CHUNK = 20000

# Rows of the L1 distance matrix computed per parallel task in pairwise_distance (continuous dice/jaccard).
_L1_ROW_BLOCK = 100


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


def pairwise_distance(X: np.ndarray, metric: str, n_jobs: int = -1) -> np.ndarray:
    """Exact (n_samples, n_samples) distance matrix for euclidean/dice/jaccard, on a binary *or*
    a non-negative continuous matrix - the input of src/analysis/adp.py, which runs on the raw
    feature matrices of this project (lesion/SDC voxel-wise: binary or near-binary; SDC streamline:
    87 continuous tract values).

    - **euclidean**: L2, any real-valued X.
    - **dice / jaccard on a binary X**: the classic set-overlap distances from the exact
      intersection counts - identical to binary_pairwise_distance (checked by a test), but
      computed on column blocks so X is never converted to float64 as a whole.
    - **dice / jaccard on a continuous X >= 0**: the weighted generalisations that reduce to the
      classic ones on 0/1 data, with sum_min = sum_f min(x_f, y_f) = (sum x + sum y - L1(x, y)) / 2:
          dice    = 1 - 2 * sum_min / (sum x + sum y)           (Czekanowski / Bray-Curtis)
          jaccard = 1 - sum_min / (sum x + sum y - sum_min)     (Ruzicka)

    The L1 distances of the continuous case (the only slow step: ~2 minutes on 1570 x 290940 with all 8
    cores of a laptop) are computed by column blocks (bounded memory) with the rows split across `n_jobs`
    threads (joblib convention, -1 = every core); the binary and euclidean cases are BLAS matrix
    products and ignore it.

    Raises ValueError for an unsupported metric, for dice/jaccard on a matrix with a negative
    value (the overlap is meaningless) or with an all-zero row (the denominator would be 0).
    """
    if metric not in PRECOMPUTABLE_METRICS:
        raise ValueError(f"unsupported metric {metric!r} for pairwise_distance - supported: {sorted(PRECOMPUTABLE_METRICS)}")

    binary = _is_binary(X)
    row_sum = X.sum(axis=1, dtype=np.float64)
    if metric in SUPPORTED_BINARY_METRICS:
        if np.any(row_sum == 0):
            raise ValueError(
                f"metric={metric!r} is undefined for an all-zero row (the denominator would be 0) - "
                f"{int((row_sum == 0).sum())} such row(s) in X"
            )
        if not binary and X.min() < 0:
            raise ValueError(f"metric={metric!r} on a continuous matrix needs non-negative values, X.min() = {X.min()}")

    if metric == "euclidean" or binary:
        gram = _gram_matrix(X, binary)
        if metric == "euclidean":
            squared_norm = np.diag(gram)
            distance = np.sqrt(np.maximum(squared_norm[:, None] + squared_norm[None, :] - 2 * gram, 0.0))
            np.fill_diagonal(distance, 0.0)
            return distance
        sum_min = gram  # for a 0/1 matrix, min(x_f, y_f) = x_f * y_f: the intersection count is the Gram matrix
    else:
        l1 = _l1_distance_matrix(X, n_jobs)
        sum_min = (row_sum[:, None] + row_sum[None, :] - l1) / 2

    total = row_sum[:, None] + row_sum[None, :]
    distance = 1 - 2 * sum_min / total if metric == "dice" else 1 - sum_min / (total - sum_min)
    np.fill_diagonal(distance, 0.0)
    return distance


def _is_binary(X: np.ndarray) -> bool:
    return all(np.isin(np.asarray(X[:, start : start + _GRAM_CHUNK]), (0, 1)).all() for start in range(0, X.shape[1], _GRAM_CHUNK))


def _gram_matrix(X: np.ndarray, binary: bool) -> np.ndarray:
    """X @ X.T in float64, accumulated over column blocks. A binary X goes through float32 BLAS
    per block (exact, see _GRAM_CHUNK) and is summed in float64; a continuous X stays float64.
    """
    block_dtype = np.float32 if binary else np.float64
    gram = np.zeros((X.shape[0], X.shape[0]), dtype=np.float64)
    for start in range(0, X.shape[1], _GRAM_CHUNK):
        block = np.asarray(X[:, start : start + _GRAM_CHUNK]).astype(block_dtype)
        gram += block @ block.T
    return gram


def _l1_distance_matrix(X: np.ndarray, n_jobs: int) -> np.ndarray:
    """L1 distances, summed over blocks of _GRAM_CHUNK columns so at most one float64 block of X
    (n_samples x _GRAM_CHUNK) exists at a time - a float64 copy of the whole matrix is 13.6 GB for
    5845 x 291345. Within a block the rows are split across threads: scipy's cdist releases the GIL, so
    no copy of the block is made (about 3.6x faster than 1 thread on 8 cores, and faster than processes).
    """
    n_samples = X.shape[0]
    row_blocks = [(start, min(start + _L1_ROW_BLOCK, n_samples)) for start in range(0, n_samples, _L1_ROW_BLOCK)]
    l1 = np.zeros((n_samples, n_samples), dtype=np.float64)
    for column_start in range(0, X.shape[1], _GRAM_CHUNK):
        block = np.ascontiguousarray(X[:, column_start : column_start + _GRAM_CHUNK], dtype=np.float64)
        parts = Parallel(n_jobs=n_jobs, prefer="threads")(delayed(cdist)(block[start:stop], block, "cityblock") for start, stop in row_blocks)
        l1 += np.vstack(parts)
    return l1
