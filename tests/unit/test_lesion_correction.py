"""Unit tests for src/features/lesion_correction.py - pure array function, no I/O."""

import numpy as np

from src.features.lesion_correction import zero_out_of_brain_voxels


def test_zero_out_of_brain_voxels_zeroes_only_outside_voxels_and_flags_subject():
    # columns: 0,1 inside brain; 2,3 outside brain
    brain_mask = np.array([True, True, False, False])
    X = np.array(
        [
            [1, 0, 1, 1],  # has 2 out-of-brain voxels -> corrected
            [1, 1, 0, 0],  # fully inside -> untouched
        ],
        dtype=np.uint8,
    )

    X_corrected, was_corrected = zero_out_of_brain_voxels(X, brain_mask)

    np.testing.assert_array_equal(X_corrected, [[1, 0, 0, 0], [1, 1, 0, 0]])
    np.testing.assert_array_equal(was_corrected, [True, False])


def test_zero_out_of_brain_voxels_zero_volume_subject_untouched():
    brain_mask = np.array([True, False])
    X = np.zeros((1, 2), dtype=np.uint8)

    X_corrected, was_corrected = zero_out_of_brain_voxels(X, brain_mask)

    np.testing.assert_array_equal(X_corrected, X)
    assert was_corrected.tolist() == [False]


def test_zero_out_of_brain_voxels_does_not_mutate_input():
    brain_mask = np.array([False])
    X = np.array([[1]], dtype=np.uint8)

    X_corrected, _ = zero_out_of_brain_voxels(X, brain_mask)

    assert X[0, 0] == 1  # original untouched
    assert X_corrected[0, 0] == 0
