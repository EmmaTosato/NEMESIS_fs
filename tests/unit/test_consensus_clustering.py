"""Unit tests for src/analysis/consensus_clustering.py."""

import numpy as np
import pytest

from src.analysis.consensus_clustering import (
    CONSENSUS_ELIGIBLE_METHODS,
    K_PARAM_NAME,
    assign_clusters_from_cooccurrence,
    compute_evidence_accumulation_convergence,
    compute_monti_stability,
    compute_rsc_eigengap,
    run_monti_repeats,
    run_rsc_repeats,
    subsampling_stability_index,
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
    with pytest.raises(ValueError, match="gmm.*kmeans.*spectral"):
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
    with pytest.raises(ValueError, match="gmm.*kmeans.*spectral"):
        run_monti_repeats("hdbscan", X, {"min_cluster_size": 3}, n_repeats=5, subsample_fraction=0.8)


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


def test_subsampling_stability_index_high_on_well_separated_blobs():
    X = _two_blobs()
    index = subsampling_stability_index("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, subsample_fraction=0.8)

    assert index > 0.9  # well-separated blobs: the 80% subsample recovers the same partition


def test_subsampling_stability_index_works_for_deterministic_method_too():
    """Unlike run_rsc_repeats/run_monti_repeats, subsampling_stability_index is not restricted
    to CONSENSUS_ELIGIBLE_METHODS - agglomerative is deterministic but the comparison is still
    meaningful (does a smaller sample change the deterministic result?)."""
    X = _two_blobs()
    index = subsampling_stability_index("agglomerative", X, {"n_clusters": 2, "linkage": "ward"}, subsample_fraction=0.8)

    assert index > 0.9


def test_subsampling_stability_index_rejects_unknown_method():
    X = _two_blobs()
    with pytest.raises(ValueError, match="unknown clustering method"):
        subsampling_stability_index("not_a_method", X, {}, subsample_fraction=0.8)


def test_subsampling_stability_index_rejects_invalid_subsample_fraction():
    X = _two_blobs()
    with pytest.raises(ValueError, match="subsample_fraction"):
        subsampling_stability_index("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, subsample_fraction=1.5)


def test_subsampling_stability_index_rejects_too_small_subsample():
    X = _two_blobs(n_per_blob=2)  # 4 points total
    with pytest.raises(ValueError, match="too small"):
        subsampling_stability_index("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, subsample_fraction=0.1)


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


def test_assign_clusters_from_cooccurrence_recovers_well_separated_blobs():
    X = _two_blobs()
    cooccurrence = run_rsc_repeats("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, n_repeats=20)
    labels = assign_clusters_from_cooccurrence(cooccurrence, threshold=0.5)

    assert labels.shape == (40,)
    assert set(labels.tolist()) == {0, 1}
    assert len(set(labels[:20].tolist())) == 1
    assert len(set(labels[20:].tolist())) == 1
    assert labels[0] != labels[20]


def test_assign_clusters_from_cooccurrence_is_0_indexed():
    # a trivial 4x4 co-occurrence: {0,1} fully together, {2,3} fully together,
    # the two pairs never co-occur - a threshold cut should recover exactly that
    cooccurrence = np.array(
        [
            [1.0, 1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
        ]
    )
    labels = assign_clusters_from_cooccurrence(cooccurrence, threshold=0.5)

    assert set(labels.tolist()) == {0, 1}
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]


def test_assign_clusters_from_cooccurrence_cluster_count_emerges_from_threshold():
    # the whole point of Fred & Jain's Merge step: the number of final
    # clusters is never passed in - it comes out of the co-association
    # structure itself. 3 clean blocks, no "3" anywhere in the call.
    cooccurrence = np.array(
        [
            [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 1.0],
        ]
    )
    labels = assign_clusters_from_cooccurrence(cooccurrence, threshold=0.5)
    assert len(set(labels.tolist())) == 3

    # a looser threshold can legitimately merge blocks that co-occurred even
    # a little (here: block {2,3} and {4,5} share weak co-association) -
    # still no n_clusters passed in, the count just changes with the data
    cooccurrence[2:4, 4:6] = 0.2
    cooccurrence[4:6, 2:4] = 0.2
    labels_loose = assign_clusters_from_cooccurrence(cooccurrence, threshold=0.1)
    assert len(set(labels_loose.tolist())) == 2


def test_assign_clusters_from_cooccurrence_rejects_non_square_matrix():
    with pytest.raises(ValueError, match="square"):
        assign_clusters_from_cooccurrence(np.zeros((4, 5)), threshold=0.5)


def test_assign_clusters_from_cooccurrence_rejects_out_of_range_threshold():
    cooccurrence = np.eye(4)
    with pytest.raises(ValueError, match="threshold"):
        assign_clusters_from_cooccurrence(cooccurrence, threshold=1.1)
    with pytest.raises(ValueError, match="threshold"):
        assign_clusters_from_cooccurrence(cooccurrence, threshold=-0.1)


# --- compute_evidence_accumulation_convergence (project-clustering-tuning-redesign memory,
# 26-08-26) ---------------------------------------------------------------------------------


def test_compute_evidence_accumulation_convergence_shape_and_columns():
    X = _two_blobs()
    df = compute_evidence_accumulation_convergence("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, [5, 10, 20])

    assert list(df.columns) == ["n_repeats", "stability_score"]
    assert list(df["n_repeats"]) == [5, 10, 20]
    assert ((df["stability_score"] >= 0.0) & (df["stability_score"] <= 1.0)).all()


def test_compute_evidence_accumulation_convergence_well_separated_blobs_converges_high():
    X = _two_blobs()
    df = compute_evidence_accumulation_convergence("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, [20])

    # well-separated blobs: k-means finds the same 2 clusters regardless of init, so
    # the co-occurrence matrix should already be stable (near 1.0) by 20 repeats
    assert df["stability_score"].iloc[0] > 0.95


def test_compute_evidence_accumulation_convergence_rejects_ineligible_method():
    X = _two_blobs()
    with pytest.raises(ValueError, match="gmm.*kmeans.*spectral"):
        compute_evidence_accumulation_convergence("agglomerative", X, {"n_clusters": 2, "linkage": "ward"}, [5])


def test_compute_evidence_accumulation_convergence_rejects_empty_checkpoints():
    X = _two_blobs()
    with pytest.raises(ValueError, match="non-empty"):
        compute_evidence_accumulation_convergence("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, [])


def test_compute_evidence_accumulation_convergence_rejects_non_positive_checkpoint():
    X = _two_blobs()
    with pytest.raises(ValueError, match=">= 1"):
        compute_evidence_accumulation_convergence("kmeans", X, {"n_clusters": 2, "n_init": "auto"}, [0, 5])
