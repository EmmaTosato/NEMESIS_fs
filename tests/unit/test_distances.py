"""Unit tests for src/analysis/distances.py."""

import numpy as np
import pytest

from src.analysis.distances import (
    PRECOMPUTABLE_METRICS,
    SUPPORTED_BINARY_METRICS,
    binary_pairwise_distance,
    euclidean_pairwise_distance,
    pairwise_distance,
    precomputed_distance,
)
from src.analysis import distances

# A=[1,1,0,0], B=[1,0,1,0], C=[1,1,1,1] - hand-computed below
_X = np.array(
    [
        [1, 1, 0, 0],
        [1, 0, 1, 0],
        [1, 1, 1, 1],
    ]
)


def test_jaccard_distance_matches_hand_computed_values():
    dist = binary_pairwise_distance(_X, "jaccard")
    # A-B: intersection=1, union=2+2-1=3 -> 1 - 1/3
    assert dist[0, 1] == pytest.approx(2 / 3)
    # A-C: intersection=2, union=2+4-2=4 -> 1 - 2/4
    assert dist[0, 2] == pytest.approx(0.5)
    # B-C: intersection=2, union=2+4-2=4 -> 1 - 2/4
    assert dist[1, 2] == pytest.approx(0.5)
    assert np.allclose(np.diag(dist), 0.0)
    assert np.allclose(dist, dist.T)


def test_dice_distance_matches_hand_computed_values():
    dist = binary_pairwise_distance(_X, "dice")
    # A-B: 1 - 2*1/(2+2)
    assert dist[0, 1] == pytest.approx(0.5)
    # A-C: 1 - 2*2/(2+4)
    assert dist[0, 2] == pytest.approx(1 / 3)
    # B-C: 1 - 2*2/(2+4)
    assert dist[1, 2] == pytest.approx(1 / 3)
    assert np.allclose(np.diag(dist), 0.0)
    assert np.allclose(dist, dist.T)


def test_unsupported_metric_raises():
    with pytest.raises(ValueError, match="unsupported metric 'cosine'"):
        binary_pairwise_distance(_X, "cosine")


def test_all_zero_row_raises():
    X_with_empty_row = np.array([[1, 1, 0, 0], [0, 0, 0, 0]])
    with pytest.raises(ValueError, match="every row to have at least one nonzero feature"):
        binary_pairwise_distance(X_with_empty_row, "jaccard")


def test_supported_binary_metrics_is_jaccard_and_dice():
    assert SUPPORTED_BINARY_METRICS == {"jaccard", "dice"}


def test_precomputable_metrics_is_jaccard_dice_euclidean():
    assert PRECOMPUTABLE_METRICS == {"jaccard", "dice", "euclidean"}


def test_euclidean_pairwise_distance_matches_hand_computed_values():
    dist = euclidean_pairwise_distance(_X)
    # A=[1,1,0,0], B=[1,0,1,0]: sqrt(0+1+1+0) = sqrt(2)
    assert dist[0, 1] == pytest.approx(np.sqrt(2))
    # A=[1,1,0,0], C=[1,1,1,1]: sqrt(0+0+1+1) = sqrt(2)
    assert dist[0, 2] == pytest.approx(np.sqrt(2))
    # B=[1,0,1,0], C=[1,1,1,1]: sqrt(0+1+0+1) = sqrt(2)
    assert dist[1, 2] == pytest.approx(np.sqrt(2))
    assert np.allclose(np.diag(dist), 0.0)
    assert np.allclose(dist, dist.T)


def test_precomputed_distance_dispatches_by_metric():
    assert np.allclose(precomputed_distance(_X, "euclidean"), euclidean_pairwise_distance(_X))
    assert np.allclose(precomputed_distance(_X, "jaccard"), binary_pairwise_distance(_X, "jaccard"))
    assert np.allclose(precomputed_distance(_X, "dice"), binary_pairwise_distance(_X, "dice"))


def test_precomputed_distance_unsupported_metric_raises():
    with pytest.raises(ValueError, match="unsupported metric 'cosine'"):
        precomputed_distance(_X, "cosine")


@pytest.mark.parametrize("metric", ["jaccard", "dice", "euclidean"])
def test_pairwise_distance_on_binary_matches_the_existing_binary_and_euclidean_functions(metric):
    rng = np.random.default_rng(0)
    X = (rng.random((20, 50)) < 0.3).astype(np.uint8)
    X[:, 0] = 1  # no all-zero row

    assert np.allclose(pairwise_distance(X, metric), precomputed_distance(X, metric))


def test_pairwise_distance_continuous_dice_and_jaccard_match_hand_computed_values():
    # x=[1,2], y=[2,1]: sum_min = min(1,2)+min(2,1) = 2, sums 3 and 3
    X = np.array([[1.0, 2.0], [2.0, 1.0]])

    assert pairwise_distance(X, "dice")[0, 1] == pytest.approx(1 - 2 * 2 / 6)
    assert pairwise_distance(X, "jaccard")[0, 1] == pytest.approx(1 - 2 / (6 - 2))
    assert pairwise_distance(X, "euclidean")[0, 1] == pytest.approx(np.sqrt(2))


@pytest.mark.parametrize("metric", ["jaccard", "dice"])
def test_pairwise_distance_continuous_formula_reduces_to_the_classic_one_on_zero_one_data(metric, monkeypatch):
    rng = np.random.default_rng(2)
    X = (rng.random((20, 50)) < 0.3).astype(np.float64)
    X[:, 0] = 1
    monkeypatch.setattr(distances, "_is_binary", lambda X: False)  # force the weighted (L1) branch

    assert np.allclose(pairwise_distance(X, metric), binary_pairwise_distance(X, metric))


def test_pairwise_distance_blocks_give_the_same_result_as_a_single_block(monkeypatch):
    rng = np.random.default_rng(1)
    binary = (rng.random((15, 40)) < 0.4).astype(np.uint8)
    binary[:, 0] = 1
    continuous = rng.random((15, 40))
    expected = {(name, metric): pairwise_distance(X, metric) for name, X in [("bin", binary), ("cont", continuous)] for metric in PRECOMPUTABLE_METRICS}

    monkeypatch.setattr(distances, "_GRAM_CHUNK", 7)

    for (name, metric), single_block in expected.items():
        X = binary if name == "bin" else continuous
        assert np.allclose(pairwise_distance(X, metric), single_block)


def test_pairwise_distance_zero_row_raises_for_dice_and_jaccard_but_not_for_euclidean():
    X = np.array([[1, 0, 1], [0, 0, 0], [1, 1, 1]])

    for metric in ("dice", "jaccard"):
        with pytest.raises(ValueError, match="all-zero row"):
            pairwise_distance(X, metric)
    assert pairwise_distance(X, "euclidean")[0, 1] == pytest.approx(np.sqrt(2))


def test_pairwise_distance_negative_values_raise_for_dice_but_not_for_euclidean():
    X = np.array([[1.0, -2.0], [2.0, 1.0]])

    with pytest.raises(ValueError, match="non-negative"):
        pairwise_distance(X, "dice")
    assert pairwise_distance(X, "euclidean")[0, 1] == pytest.approx(np.sqrt(1 + 9))


def test_pairwise_distance_unsupported_metric_raises():
    with pytest.raises(ValueError, match="unsupported metric 'cosine'"):
        pairwise_distance(_X, "cosine")
