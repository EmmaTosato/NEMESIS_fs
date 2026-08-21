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


def require_binary_matrix(X: np.ndarray, metric: str) -> None:
    """Raises ValueError if X has any value outside {0, 1}.

    Jaccard/Dice (both here and umap/sklearn's own native "jaccard"/"dice"
    implementations) are defined on set/boolean overlap - the intersection
    count `X @ X.T` this module relies on is meaningless once a "1" can mean
    "partial membership" rather than "present". Nothing upstream of this
    point guarantees binarity: `build_lesion_matrix.py` can produce a
    strictly binary voxel-wise matrix (`parcellate: false`) or a continuous
    one in [0, 1] (`parcellate: true`, `parcel_aggregation: "fraction_lesioned"`
    - each column is a per-parcel proportion of damage, not a 0/1 flag) from
    the *same* pipeline depending on config - a config that switches
    `parcellate` on without also dropping jaccard/dice from that method's
    `tuning_grid`/`params` would otherwise silently compute numbers that look
    like valid distances but aren't Jaccard/Dice at all (found during a
    2026-08 literature-validation review, before any parcellated run reached
    this code path). Called both by `binary_pairwise_distance` below
    (fine-tuning's precomputed-distance path) and directly by
    `dim_reduction.py`'s production path, which passes
    `metric="jaccard"/"dice"` straight to `umap.UMAP`/`sklearn.TSNE`
    on raw `X` without ever calling `binary_pairwise_distance` itself - both
    call sites must reject the same bad input, not just the precomputed one.
    """
    if not np.all((X == 0) | (X == 1)):
        raise ValueError(
            f"metric={metric!r} requires a strictly binary (0/1) matrix - X has value(s) outside "
            "{0, 1} (e.g. a parcellated 'fraction_lesioned' matrix is continuous in [0, 1] and not "
            "a valid input for jaccard/dice - use a different metric, e.g. euclidean, or a "
            "weighted/Ruzicka-style overlap metric for continuous data instead)"
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
