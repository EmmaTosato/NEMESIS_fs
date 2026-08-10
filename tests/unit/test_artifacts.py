"""Unit tests for src/utils/artifacts.py - save_matrix/load_matrix roundtrip and error paths."""

import numpy as np
import pandas as pd
import pytest

from src.utils.artifacts import load_matrix, save_matrix


def _matrix_and_metadata():
    X = np.arange(12).reshape(4, 3)
    metadata = pd.DataFrame({"subject_id": ["a", "b", "c", "d"], "dataset": ["siteA"] * 4})
    return X, metadata


def test_save_and_load_roundtrip(tmp_path):
    X, metadata = _matrix_and_metadata()
    extra = {"non_constant_mask": np.array([True, False, True])}
    out_dir = tmp_path / "run1"

    result_dir = save_matrix(out_dir, X, metadata, ["# readme"], overwrite=False, extra_arrays=extra)

    assert result_dir == out_dir
    X2, metadata2, extra2 = load_matrix(out_dir)
    assert np.array_equal(X, X2)
    assert metadata.equals(metadata2)
    assert np.array_equal(extra["non_constant_mask"], extra2["non_constant_mask"])
    assert (out_dir / "config.md").read_text() == "# readme\n"


def test_overwrite_false_raises_on_existing_dir(tmp_path):
    X, metadata = _matrix_and_metadata()
    out_dir = tmp_path / "run1"
    save_matrix(out_dir, X, metadata, ["x"], overwrite=False)

    with pytest.raises(FileExistsError, match="overwrite=False"):
        save_matrix(out_dir, X, metadata, ["x"], overwrite=False)


def test_overwrite_true_replaces_existing_dir(tmp_path):
    X, metadata = _matrix_and_metadata()
    out_dir = tmp_path / "run1"
    save_matrix(out_dir, X, metadata, ["x"], overwrite=False)

    save_matrix(out_dir, X * 2, metadata, ["y"], overwrite=True)
    X2, _metadata2, _extra2 = load_matrix(out_dir)
    assert np.array_equal(X2, X * 2)


def test_load_matrix_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="manifest.json"):
        load_matrix(tmp_path / "does_not_exist")


def test_reserved_extra_array_name_raises(tmp_path):
    X, metadata = _matrix_and_metadata()
    with pytest.raises(ValueError, match="reserved name"):
        save_matrix(tmp_path / "run1", X, metadata, ["x"], overwrite=False, extra_arrays={"matrix": X})


def test_row_count_mismatch_between_X_and_metadata_raises(tmp_path):
    X, metadata = _matrix_and_metadata()
    with pytest.raises(ValueError, match="rows"):
        save_matrix(tmp_path / "run1", X, metadata.iloc[:2], ["x"], overwrite=False)


def test_extra_arrays_not_shape_checked_against_X(tmp_path):
    """non_constant_mask (feature-aligned, not subject-aligned) must be
    accepted even though its length differs from X.shape[0] - regression test
    for the bug found while testing build_lesion_matrix.py (see
    docs/dev/lesion_matrix.md)."""
    X, metadata = _matrix_and_metadata()
    feature_aligned = np.ones(1000, dtype=bool)  # unrelated length to X's 4 rows / 3 columns
    save_matrix(tmp_path / "run1", X, metadata, ["x"], overwrite=False, extra_arrays={"non_constant_mask": feature_aligned})

    _X2, _metadata2, extra2 = load_matrix(tmp_path / "run1")
    assert extra2["non_constant_mask"].shape == (1000,)


def test_no_leftover_tmp_dir_after_save(tmp_path):
    X, metadata = _matrix_and_metadata()
    save_matrix(tmp_path / "run1", X, metadata, ["x"], overwrite=False)

    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(".")]
    assert leftovers == []
