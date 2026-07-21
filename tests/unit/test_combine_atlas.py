"""Unit tests for src/atlases/combine.py - synthetic arrays, no real atlas files required."""

import nibabel as nib
import numpy as np
import pytest

from src.atlases.combine import (
    SUBCORTICAL_STRUCTURES,
    merge_cortical_subcortical,
    remap_subcortical_labels,
    resample_subcortical_to_cortical_grid,
    subcortical_output_mapping,
    validate_combined_label_count,
)

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1


def test_subcortical_output_mapping_has_12_entries_no_collisions_with_cortical_range():
    mapping = subcortical_output_mapping()

    assert len(mapping) == 12
    output_values = [output_value for output_value, _name in mapping.values()]
    assert len(set(output_values)) == 12  # bijection, no two structures share an output value
    for value in output_values:
        assert not (1 <= value <= 180) and not (1001 <= value <= 1180)  # never collides with Glasser's own range


def test_subcortical_output_mapping_matches_known_correct_indices():
    # Regression for the off-by-one bug found in this session (debug_21_07_26.md):
    # R_Hippocampus/R_Amygdala are NOT at a uniform +11 offset from their left counterparts.
    mapping = subcortical_output_mapping()

    assert mapping[9][1] == "L_Hippocampus"
    assert mapping[19][1] == "R_Hippocampus"
    assert mapping[10][1] == "L_Amygdala"
    assert mapping[20][1] == "R_Amygdala"


def test_remap_subcortical_labels_keeps_only_registered_structures():
    source = np.array([0, 4, 5, 8, 11, 15], dtype=np.int64)  # 8=Brain-Stem, 11=L_Accumbens: not registered

    remapped = remap_subcortical_labels(source)

    expected_left_thalamus = subcortical_output_mapping()[4][0]
    expected_left_caudate = subcortical_output_mapping()[5][0]
    expected_right_thalamus = subcortical_output_mapping()[15][0]
    assert remapped.tolist() == [0, expected_left_thalamus, expected_left_caudate, 0, 0, expected_right_thalamus]


def test_merge_cortical_subcortical_prefers_cortical_on_overlap():
    cortical = np.array([1, 0, 0, 3], dtype=np.int64)
    subcortical = np.array([0, 181, 182, 181], dtype=np.int64)  # index 3 overlaps with cortical label 3

    merged, n_overlap = merge_cortical_subcortical(cortical, subcortical)

    assert merged.tolist() == [1, 181, 182, 3]
    assert n_overlap == 1


def test_validate_combined_label_count_raises_on_mismatch():
    too_few = np.zeros(10, dtype=np.int64)
    too_few[:5] = 1  # only 1 unique non-zero label, not 372

    with pytest.raises(ValueError, match="372"):
        validate_combined_label_count(too_few)


def test_validate_combined_label_count_accepts_exactly_372():
    labels = np.arange(373)  # values 0..372 -> 372 non-zero unique labels

    validate_combined_label_count(labels)  # must not raise


def test_resample_subcortical_to_cortical_grid_uses_nearest_neighbour():
    small_shape = (4, 4, 4)
    large_shape = (8, 8, 8)
    subcortical_data = np.zeros(small_shape, dtype=np.int64)
    subcortical_data[1, 1, 1] = 15
    subcortical_img = nib.Nifti1Image(subcortical_data.astype(np.float32), _AFFINE)
    cortical_img = nib.Nifti1Image(np.zeros(large_shape, dtype=np.float32), _AFFINE / 2 * np.array([1, 1, 1, 2]))

    resampled = resample_subcortical_to_cortical_grid(subcortical_img, cortical_img)

    assert resampled.shape == large_shape
    # nearest-neighbour on discrete labels never invents values absent from the source
    assert set(np.unique(resampled).tolist()) <= {0, 15}


def test_all_six_structures_registered():
    names = {name for name, _left, _right in SUBCORTICAL_STRUCTURES}
    assert names == {"Thalamus", "Caudate", "Putamen", "Pallidum", "Hippocampus", "Amygdala"}
