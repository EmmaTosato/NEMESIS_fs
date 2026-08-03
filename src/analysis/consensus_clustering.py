"""Consensus/stability clustering: two literature methods answering different
questions about how much a candidate `k` can be trusted, both reusing the
existing per-k sweep in clustering_tuning.py rather than being a separate
diagnostic mode - params_clustering.json already sweeps exactly n_clusters/
n_components for kmeans/gmm/spectral, so "how stable is this k" is one more
column per already-swept row.

- RSC (Tshimanga et al. 2025, cited by Zanola et al. 2026 - papers/Zanola et
  al - 2026 - ...): "how stable is the assignment to random init, on the
  exact same data?" No resampling - N repeats of the same method on the full
  dataset, varying only the random seed. Only meaningful for methods with
  genuine internal stochasticity (k-means centroid init, GMM init, spectral
  clustering's internal k-means step) - agglomerative/hdbscan are
  deterministic given the same data, so a repeat with a different seed
  reproduces the identical partition (a degenerate, uninformative
  co-occurrence matrix). See compute_rsc_eigengap.
- Monti et al. 2003: "how stable is the assignment to who's in the sample?"
  N repeats on a random subsample of subjects each time. Restricted here to
  the same 3 methods (CONSENSUS_ELIGIBLE_METHODS) so the two stability
  notions are directly comparable, though the resampling idea itself would
  apply to any method. See compute_monti_stability for one deliberate
  deviation from the literal 2003 formula (PAC instead of area-under-CDF).
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import eigh
from scipy.sparse import csgraph

from src.analysis.clustering import CLUSTERING_METHODS

CONSENSUS_ELIGIBLE_METHODS = {"kmeans", "gmm", "spectral"}
K_PARAM_NAME = {"kmeans": "n_clusters", "gmm": "n_components", "spectral": "n_clusters"}


def _check_eligible(method: str) -> None:
    if method not in CONSENSUS_ELIGIBLE_METHODS:
        raise ValueError(
            f"consensus/stability clustering is only defined for {sorted(CONSENSUS_ELIGIBLE_METHODS)} "
            f"(methods with genuine internal stochasticity), got {method!r}"
        )


def run_rsc_repeats(method: str, X: np.ndarray, params: dict, n_repeats: int, base_seed: int = 0) -> np.ndarray:
    """RSC co-occurrence matrix: n_repeats runs of `method` on the full X,
    varying only random_state. Returns an (n_samples, n_samples) matrix where
    entry [i, j] is the fraction of runs in which subjects i and j were
    assigned to the same cluster.
    """
    _check_eligible(method)
    if n_repeats < 1:
        raise ValueError(f"n_repeats must be >= 1, got {n_repeats}")

    n_samples = X.shape[0]
    co_occurrence = np.zeros((n_samples, n_samples), dtype=float)
    for i in range(n_repeats):
        labels = CLUSTERING_METHODS[method](X, {**params, "random_state": base_seed + i})
        co_occurrence += labels[:, None] == labels[None, :]

    return co_occurrence / n_repeats


def run_monti_repeats(
    method: str, X: np.ndarray, params: dict, n_repeats: int, subsample_fraction: float, base_seed: int = 0
) -> np.ndarray:
    """Monti-style consensus matrix: n_repeats runs of `method`, each on a
    random subsample (without replacement) of subsample_fraction of the
    subjects. Returns an (n_samples, n_samples) matrix where entry [i, j] is
    co-clustered / co-sampled for that pair, i.e. how often i,j land in the
    same cluster among the runs where both happened to be drawn.

    Raises ValueError if any pair of subjects was never jointly sampled
    across the n_repeats draws - an explicit failure (n_repeats/
    subsample_fraction too low for this n_samples), never a silent NaN/0.
    """
    _check_eligible(method)
    if n_repeats < 1:
        raise ValueError(f"n_repeats must be >= 1, got {n_repeats}")
    if not (0.0 < subsample_fraction < 1.0):
        raise ValueError(f"subsample_fraction must be in (0, 1), got {subsample_fraction}")

    n_samples = X.shape[0]
    subsample_size = round(subsample_fraction * n_samples)
    co_sampled = np.zeros((n_samples, n_samples), dtype=float)
    co_clustered = np.zeros((n_samples, n_samples), dtype=float)

    for i in range(n_repeats):
        rng = np.random.default_rng(base_seed + i)
        subsample = rng.choice(n_samples, size=subsample_size, replace=False)
        labels = CLUSTERING_METHODS[method](X[subsample], params)

        sampled_mask = np.zeros(n_samples, dtype=bool)
        sampled_mask[subsample] = True
        co_sampled += sampled_mask[:, None] & sampled_mask[None, :]

        full_labels = np.full(n_samples, -1)
        full_labels[subsample] = labels
        same_cluster = (full_labels[:, None] == full_labels[None, :]) & sampled_mask[:, None] & sampled_mask[None, :]
        co_clustered += same_cluster

    never_co_sampled = co_sampled == 0
    np.fill_diagonal(never_co_sampled, False)
    if never_co_sampled.any():
        raise ValueError(
            f"{int(never_co_sampled.sum() / 2)} subject pair(s) were never jointly sampled across {n_repeats} "
            f"repeats at subsample_fraction={subsample_fraction} - increase n_repeats or subsample_fraction"
        )

    return co_clustered / co_sampled


def compute_rsc_eigengap(cooccurrence_matrix: np.ndarray, k: int) -> float:
    """Gap between the k-th and (k-1)-th (1-indexed) sorted eigenvalues of
    the co-occurrence matrix's normalized Laplacian - not the biggest gap
    anywhere (that's the generic eigengap heuristic already in
    clustering_tuning.compute_eigengap), but specifically the gap at the
    position that matters for this candidate k, matching the paper's own
    "difference between k+1-th and k-th ordered eigenvalues" read across the
    different co-occurrence matrices built for each k attempted.
    """
    if k < 1 or k >= cooccurrence_matrix.shape[0]:
        raise ValueError(f"k must be in [1, n_samples), got k={k} for a {cooccurrence_matrix.shape[0]}x... matrix")

    laplacian = csgraph.laplacian(cooccurrence_matrix, normed=True)
    if hasattr(laplacian, "toarray"):
        laplacian = laplacian.toarray()
    eigenvalues = eigh(laplacian, eigvals_only=True, subset_by_index=[0, k])
    eigenvalues = np.sort(eigenvalues)
    return float(eigenvalues[k] - eigenvalues[k - 1])


def compute_monti_stability(consensus_matrix: np.ndarray, ambiguous_band: tuple[float, float] = (0.1, 0.9)) -> float:
    """1 - Proportion of Ambiguous Clustering (PAC): the fraction of the
    consensus matrix's off-diagonal entries falling *outside* ambiguous_band
    (a consensus value near 0 or 1 is unambiguous; near 0.5 is not). Higher
    is more stable, matching compute_rsc_eigengap's direction.

    Deliberate deviation from Monti et al. 2003's own area-under-CDF
    statistic: Șenbabaoğlu et al. 2014 showed that statistic is biased toward
    favoring larger k. PAC is the standard fix, used e.g. by
    ConsensusClusterPlus - not an invention for this codebase.
    """
    lower, upper = ambiguous_band
    n = consensus_matrix.shape[0]
    upper_triangle = consensus_matrix[np.triu_indices(n, k=1)]
    proportion_ambiguous = float(np.mean((upper_triangle > lower) & (upper_triangle < upper)))
    return 1.0 - proportion_ambiguous
