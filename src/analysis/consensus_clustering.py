"""Consensus/stability clustering: two literature methods answering different
questions about how much a candidate `k` can be trusted, both reusing the
existing per-k sweep in clustering_tuning.py rather than being a separate
diagnostic mode.

- RSC (Tshimanga et al. 2025, cited by Zanola et al. 2026): stability to
  random init on the same data - N repeats varying only the seed. Only
  meaningful for CONSENSUS_ELIGIBLE_METHODS (kmeans/gmm/spectral, the only 3
  with genuine internal stochasticity) - agglomerative/hdbscan are
  deterministic given the same data, so a repeat would be degenerate.
- Monti et al. 2003: stability to who's in the sample - N repeats on a
  random subsample each time. See compute_monti_stability's own docstring
  for the one deliberate deviation from the literal 2003 formula.

subsampling_stability_index is a lighter sibling of the Monti idea above (a
single full-vs-one-subsample ARI comparison, not an N-repeat ensemble) -
meaningful for any CLUSTERING_METHODS entry, not restricted to
CONSENSUS_ELIGIBLE_METHODS. Used by notebooks/post-results_analysis/clustering_tuning_explorer.ipynb,
not wired into clustering_tuning.py's sweep.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import eigh
from scipy.sparse import csgraph
from sklearn.metrics import adjusted_rand_score

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


def subsampling_stability_index(method: str, X: np.ndarray, params: dict, subsample_fraction: float, base_seed: int = 0) -> float:
    """Adjusted Rand Index between a clustering fit on all of X and the same method/params
    refit on one random subsample_fraction subsample (without replacement) of X - do the
    same subjects land in matching clusters, or does the result depend on the exact sample
    drawn (e.g. a few outliers)? See project-clustering-tuning-evaluation-tables memory.

    Distinct from run_rsc_repeats/run_monti_repeats above: those build an n_repeats
    co-occurrence *ensemble*, meaningful only for CONSENSUS_ELIGIBLE_METHODS (methods with
    genuine internal stochasticity - repeating a deterministic method gives an identical
    result every time). This is a single full-vs-one-subsample comparison scored once via
    ARI, meaningful for any CLUSTERING_METHODS entry (deterministic or not), so it is not
    restricted to CONSENSUS_ELIGIBLE_METHODS. Reuses only CLUSTERING_METHODS and the same
    rng.choice draw-without-replacement shape as run_monti_repeats above, not its
    co-occurrence-matrix machinery - a different output shape for a different question, not
    worth duplicating that machinery for.

    Raises ValueError if `method` isn't a registered CLUSTERING_METHODS entry, if
    subsample_fraction isn't in (0, 1), or if the resulting subsample has fewer than 2
    points (too small to compare a clustering against).
    """
    if method not in CLUSTERING_METHODS:
        raise ValueError(f"unknown clustering method {method!r} - known: {sorted(CLUSTERING_METHODS)}")
    if not (0.0 < subsample_fraction < 1.0):
        raise ValueError(f"subsample_fraction must be in (0, 1), got {subsample_fraction}")

    n_samples = X.shape[0]
    subsample_size = round(subsample_fraction * n_samples)
    if subsample_size < 2:
        raise ValueError(
            f"subsample_fraction={subsample_fraction} on n_samples={n_samples} yields a subsample of "
            f"{subsample_size} point(s) - too small to compare clusterings"
        )

    full_labels = CLUSTERING_METHODS[method](X, params)

    rng = np.random.default_rng(base_seed)
    subsample = rng.choice(n_samples, size=subsample_size, replace=False)
    subsample_labels = CLUSTERING_METHODS[method](X[subsample], params)

    return float(adjusted_rand_score(full_labels[subsample], subsample_labels))


def compute_rsc_eigengap(cooccurrence_matrix: np.ndarray, k: int) -> float:
    """Gap between the (k+1)-th and k-th (1-indexed) sorted eigenvalues of
    the co-occurrence matrix's normalized Laplacian - not the biggest gap
    anywhere (that's clustering_tuning.compute_eigengap's generic heuristic),
    but specifically the position that matters for this candidate k, matching
    the paper's own selection criterion (see docs/dev/models.md; wording
    fixed for an off-by-one per AUDIT_FINDINGS.md #58 - the code itself was
    already correct).
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
    if n < 2:
        raise ValueError(f"consensus_matrix needs at least 2 subjects to have off-diagonal entries, got shape {consensus_matrix.shape}")
    upper_triangle = consensus_matrix[np.triu_indices(n, k=1)]
    proportion_ambiguous = float(np.mean((upper_triangle > lower) & (upper_triangle < upper)))
    return 1.0 - proportion_ambiguous

