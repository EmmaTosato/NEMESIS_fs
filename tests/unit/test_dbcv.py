import numpy as np
import pytest

from src.analysis.dbcv import dbcv


def _three_blobs(n: int = 40, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = np.vstack([rng.normal(centre, 0.3, (n, 4)) for centre in (0.0, 5.0, 10.0)])
    return X, np.repeat([0, 1, 2], n)


def test_separated_blobs_score_close_to_one_and_each_cluster_is_reported():
    X, labels = _three_blobs()
    score, per_cluster = dbcv(X, labels)
    assert score > 0.8
    assert set(per_cluster) == {0, 1, 2}
    assert score == pytest.approx(np.mean(list(per_cluster.values())))  # equal sizes, no noise: the plain average


def test_all_noise_is_undefined_not_zero():
    # the hdbscan package returns the integer 0 for this input, which reads as a measured score of 0
    X, _ = _three_blobs()
    score, per_cluster = dbcv(X, np.full(len(X), -1))
    assert np.isnan(score) and per_cluster == {}


def test_a_single_cluster_is_undefined():
    X, labels = _three_blobs()
    for lab in (np.zeros(len(X), dtype=int), np.where(labels == 0, 0, -1)):
        score, per_cluster = dbcv(X, lab)
        assert np.isnan(score) and per_cluster == {}


def test_a_cluster_of_one_subject_raises():
    X, labels = _three_blobs()
    labels = labels.copy()
    labels[0] = 3
    with pytest.raises(ValueError, match="at least 2 subjects"):
        dbcv(X, labels)


def test_noise_lowers_the_score_through_the_weights():
    X, labels = _three_blobs()
    without_noise, _ = dbcv(X, labels)
    noisy = labels.copy()
    noisy[labels == 1] = -1  # a whole blob thrown into the noise
    with_noise, per_cluster = dbcv(X, noisy)
    assert with_noise < without_noise
    assert set(per_cluster) == {0, 2}


def test_label_gaps_do_not_change_the_score():
    X, labels = _three_blobs()
    gapped = np.where(labels == 1, 5, labels)
    assert dbcv(X, gapped)[0] == pytest.approx(dbcv(X, labels)[0])
    assert set(dbcv(X, gapped)[1]) == {0, 2, 5}


def test_non_finite_values_and_length_mismatch_raise():
    X, labels = _three_blobs()
    bad = X.copy()
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        dbcv(bad, labels)
    with pytest.raises(ValueError, match="one row per label"):
        dbcv(X, labels[:-1])
