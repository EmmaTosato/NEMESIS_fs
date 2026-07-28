"""Unit tests for src/analysis/consensus_clustering.py."""

import numpy as np
import pytest

from src.analysis.consensus_clustering import (
    CONSENSUS_ELIGIBLE_METHODS,
    K_PARAM_NAME,
    compute_monti_stability,
    compute_rsc_eigengap,
    run_monti_repeats,
    run_rsc_repeats,
)


def _two_blobs(n_per_blob=20):
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.2, size=(n_per_blob, 2)),
            rng.normal(loc=[6, 6], scale=0.2, size=(n_per_blob, 2)),
        ]
    )


def test_consensus_eligible_methods_and_k_param_names():
    assert CONSENSUS_ELIGIBLE_METHODS == {"kmeans", "gmm", "spectral"}
    assert K_PARAM_NAME == {"kmeans": "n_clusters", "gmm": "n_components", "spectral": "n_clusters"}


def test_run_rsc_repeats_rejects_ineligible_method():
    X = _two_blobs()
    with pytest.raises(ValueError, match="kmeans.*gmm.*spectral"):
        run_rsc_repeats("agglomerative", X, {"n_clusters": 2, "linkage": "ward"}, n_repeats=5)


def test_run_rsc_repeats_on_well_separated_blobs_is_near_binary():
    X = _two_blobs()
    cooccurrence = run_rsc_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=20)

    assert cooccurrence.shape == (40, 40)
    assert np.allclose(np.diag(cooccurrence), 1.0)  # a subject always co-occurs with itself
    # well-separated blobs: k-means finds the same 2 clusters regardless of
    # init, so co-occurrence should be essentially 0 or 1, never ambiguous
    within_blob = cooccurrence[:20, :20]
    across_blobs = cooccurrence[:20, 20:]
    assert (within_blob > 0.99).all()
    assert (across_blobs < 0.01).all()


def test_run_monti_repeats_rejects_ineligible_method():
    X = _two_blobs()
    with pytest.raises(ValueError, match="kmeans.*gmm.*spectral"):
        run_monti_repeats("dbscan", X, {"eps": 0.5, "min_samples": 3}, n_repeats=5, subsample_fraction=0.8)


def test_run_monti_repeats_rejects_invalid_subsample_fraction():
    X = _two_blobs()
    with pytest.raises(ValueError, match="subsample_fraction"):
        run_monti_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=5, subsample_fraction=1.5)


def test_run_monti_repeats_raises_when_pairs_never_co_sampled():
    X = _two_blobs()
    # 2 repeats at a tiny subsample fraction on 40 subjects: virtually
    # guaranteed some pair is never drawn together in either repeat
    with pytest.raises(ValueError, match="never jointly sampled"):
        run_monti_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=2, subsample_fraction=0.1)


def test_run_monti_repeats_on_well_separated_blobs_is_near_binary():
    X = _two_blobs()
    consensus = run_monti_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=30, subsample_fraction=0.8)

    assert consensus.shape == (40, 40)
    within_blob = consensus[:20, :20]
    across_blobs = consensus[:20, 20:]
    assert (within_blob > 0.9).all()
    assert (across_blobs < 0.1).all()


def test_compute_rsc_eigengap_larger_for_true_k_than_wrong_k():
    X = _two_blobs()
    cooccurrence_k2 = run_rsc_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=20)
    cooccurrence_k3 = run_rsc_repeats("kmeans", X, {"n_clusters": 3, "n_init": "auto"}, n_repeats=20)

    gap_true_k = compute_rsc_eigengap(cooccurrence_k2, k=2)
    gap_wrong_k = compute_rsc_eigengap(cooccurrence_k3, k=3)

    # true k=2: a near-binary co-occurrence matrix has a large gap right at
    # position 2; forcing k=3 on 2 real blobs is unstable across inits
    # (arbitrary 3rd split), so its own position-3 gap should be smaller
    assert gap_true_k > gap_wrong_k


def test_compute_monti_stability_higher_for_true_k_than_wrong_k():
    X = _two_blobs()
    consensus_k2 = run_monti_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=30, subsample_fraction=0.8)
    consensus_k3 = run_monti_repeats("kmeans", X, {"n_clusters": 3, "n_init": "auto"}, n_repeats=30, subsample_fraction=0.8)

    stability_true_k = compute_monti_stability(consensus_k2)
    stability_wrong_k = compute_monti_stability(consensus_k3)

    assert stability_true_k > stability_wrong_k


def test_compute_monti_stability_bounds():
    X = _two_blobs()
    consensus = run_monti_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=30, subsample_fraction=0.8)
    score = compute_monti_stability(consensus)

    assert 0.0 <= score <= 1.0
