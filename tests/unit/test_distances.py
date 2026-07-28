"""Unit tests for src/analysis/distances.py."""

import numpy as np
import pytest

from src.analysis.distances import SUPPORTED_BINARY_METRICS, binary_pairwise_distance

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
