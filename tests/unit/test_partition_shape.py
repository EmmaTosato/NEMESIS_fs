import numpy as np
import pytest

from src.analysis.partition_shape import NOISE_LABEL, partition_shape


def test_counts_clusters_noise_and_the_largest_share_over_all_the_subjects():
    labels = np.array([0, 0, 0, 1, 1, 2, -1, -1, -1, -1])

    shape = partition_shape(labels)

    assert shape.n_subjects == 10 and shape.n_clusters == 3 and shape.n_noise == 4
    assert shape.noise_fraction == pytest.approx(0.4) and shape.largest_cluster_share == pytest.approx(0.3)
    assert shape.cluster_sizes == {0: 3, 1: 2, 2: 1}


def test_noise_is_never_counted_as_a_cluster():
    assert partition_shape(np.array([-1, -1, 0, 0])).n_clusters == 1
    assert NOISE_LABEL == -1


def test_all_noise_has_no_cluster_and_no_largest_share():
    shape = partition_shape(np.full(5, -1))

    assert shape.n_clusters == 0 and shape.noise_fraction == 1.0 and shape.cluster_sizes == {}
    assert np.isnan(shape.largest_cluster_share)


def test_no_noise_has_a_zero_noise_fraction():
    shape = partition_shape(np.array([0, 1, 1, 1]))

    assert shape.noise_fraction == 0.0 and shape.n_noise == 0 and shape.largest_cluster_share == pytest.approx(0.75)


@pytest.mark.parametrize("labels", [np.array([]), np.zeros((2, 2), dtype=int)])
def test_labels_that_are_not_a_non_empty_1d_array_raise(labels):
    with pytest.raises(ValueError, match="non-empty 1D"):
        partition_shape(labels)
