"""Unit tests for src/utils/artifacts.py - save_matrix/load_matrix roundtrip and error paths."""

import json

import numpy as np
import pandas as pd
import pytest

from src.utils.artifacts import load_matrix, read_dim_reduction_method, read_run_params, save_matrix


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


def _dim_reduction_readme_lines(method: str, params: dict) -> list[str]:
    """Mirrors dim_reduction.py::_build_readme_lines' exact shape (title line + "Params
    used: {...}" as the last line) - the contract read_run_params/read_dim_reduction_method
    are built against."""
    return [
        f"# testproj dim_reduction ({method}) — 26-08-26 10:00",
        "",
        "## Summary",
        "",
        f"Params used: {json.dumps(params)}",
    ]


def test_read_run_params_reads_the_params_used_line(tmp_path):
    X, metadata = _matrix_and_metadata()
    save_matrix(
        tmp_path / "run1", X, metadata,
        _dim_reduction_readme_lines("umap", {"n_neighbors": 15, "n_components": 5, "random_state": 0}),
        overwrite=False,
    )

    assert read_run_params(tmp_path / "run1") == {"n_neighbors": 15, "n_components": 5, "random_state": 0}


def test_read_run_params_missing_config_md_raises(tmp_path):
    with pytest.raises(ValueError, match="config.md"):
        read_run_params(tmp_path / "does_not_exist")


def test_read_run_params_missing_params_line_raises(tmp_path):
    X, metadata = _matrix_and_metadata()
    save_matrix(tmp_path / "run1", X, metadata, ["# readme with no params line"], overwrite=False)

    with pytest.raises(ValueError, match="Params used"):
        read_run_params(tmp_path / "run1")


def test_read_dim_reduction_method_reads_the_title_line(tmp_path):
    X, metadata = _matrix_and_metadata()
    save_matrix(
        tmp_path / "run1", X, metadata,
        _dim_reduction_readme_lines("pacmap", {"n_components": 2}),
        overwrite=False,
    )

    assert read_dim_reduction_method(tmp_path / "run1") == "pacmap"


def test_read_dim_reduction_method_missing_config_md_raises(tmp_path):
    with pytest.raises(ValueError, match="config.md"):
        read_dim_reduction_method(tmp_path / "does_not_exist")


def test_read_dim_reduction_method_wrong_title_shape_raises(tmp_path):
    """A run whose config.md isn't a dim_reduction.py production run (e.g. a raw feature
    matrix from build_lesion_matrix.py) has no "... dim_reduction (<method>) ..." title -
    must raise, never guess a method."""
    X, metadata = _matrix_and_metadata()
    save_matrix(tmp_path / "run1", X, metadata, ["# testproj build_lesion_matrix — 26-08-26"], overwrite=False)

    with pytest.raises(ValueError, match="dim_reduction"):
        read_dim_reduction_method(tmp_path / "run1")
