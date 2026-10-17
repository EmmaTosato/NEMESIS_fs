"""Unit tests for src/analysis/component_maps.py."""

import json
import time

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.analysis import component_maps
from src.analysis.component_maps import (
    ComponentMapStore,
    MapGeometry,
    load_map_geometry,
    to_volume,
)
from src.analysis.covariance_pca import component_t_maps, positive_peak_signs
from src.utils.artifacts import save_matrix

_GRID = (5, 5, 5)
_N_SUBJECTS = 60


def _scores_and_matrix(seed=0):
    """Two components with disjoint voxel supports, so each map has a clear peak; noise on top."""
    rng = np.random.default_rng(seed)
    scores = rng.normal(size=(_N_SUBJECTS, 2))
    loadings = np.zeros((2, 40))
    loadings[0, :10] = 3.0
    loadings[1, 10:20] = -3.0  # a negative effect: the map must be flipped to have its peak positive
    return scores, scores @ loadings + rng.normal(size=(_N_SUBJECTS, 40))


def _source_dir(tmp_path, matrix, ids=None, mask=True, template=True):
    tmp_path.mkdir(parents=True, exist_ok=True)
    template_path = tmp_path / "template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_GRID, dtype=np.float32), np.diag([2.0, 2.0, 2.0, 1.0])), template_path)
    config = {"representation": "voxelwise"}
    if template:
        config["reference_template_path"] = str(template_path)
    readme = ["# source", "", "## Config", "```json", json.dumps(config), "```"]
    voxel_mask = np.zeros(int(np.prod(_GRID)), dtype=bool)
    voxel_mask[np.arange(0, 80, 2)] = True  # 40 of the 125 voxels
    ids = ids if ids is not None else [f"sub-{i}" for i in range(len(matrix))]
    source = tmp_path / "source"
    save_matrix(
        source, matrix.astype(np.float32), pd.DataFrame({"subject_id": ids, "dataset": "X"}), readme_lines=readme,
        overwrite=False, extra_arrays={"non_constant_mask": voxel_mask} if mask else None,
    )
    return source


def _wait_for(store, source, scores, ids, timeout=60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = store.request(source, scores, ids)
        if result is not None:
            return result
        time.sleep(0.05)
    raise AssertionError("the maps were not ready in time")


def test_the_maps_are_the_t_maps_of_the_source_matrix_oriented_with_a_positive_peak(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    ids = [f"sub-{i}" for i in range(_N_SUBJECTS)]

    result = _wait_for(ComponentMapStore(tmp_path / "cache"), source, scores, ids)

    expected = component_t_maps(matrix.astype(np.float32), scores, [np.arange(_N_SUBJECTS)])[0].t
    signs = positive_peak_signs(expected)
    assert result.t.shape == (2, 40) and result.t.dtype == np.float32
    assert np.allclose(result.t, expected * signs[:, None], rtol=1e-3, atol=1e-3)
    assert result.t[0].argmax() < 10 and result.t[1].argmax() in range(10, 20)  # each peak is where its component lives
    assert all(result.t[k][np.argmax(np.abs(result.t[k]))] > 0 for k in range(2))
    assert result.reproducibility.shape == (2,) and (result.reproducibility > 0.9).all()
    assert result.n_degenerate_voxels == 0


def test_a_second_store_reads_the_cached_maps_without_computing(tmp_path, monkeypatch):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    ids = [f"sub-{i}" for i in range(_N_SUBJECTS)]
    first = _wait_for(ComponentMapStore(tmp_path / "cache"), source, scores, ids)

    def refuse(*_args, **_kwargs):
        raise AssertionError("the cached entry must not be recomputed")

    monkeypatch.setattr(component_maps, "component_t_maps", refuse)
    second = ComponentMapStore(tmp_path / "cache").request(source, scores, ids)  # no waiting: it is on disk

    assert second is not None and np.array_equal(second.t, first.t)


def test_other_scores_get_their_own_entry_not_a_stale_one(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    ids = [f"sub-{i}" for i in range(_N_SUBJECTS)]
    store = ComponentMapStore(tmp_path / "cache")

    _wait_for(store, source, scores, ids)
    other = _wait_for(store, source, scores[:, ::-1].copy(), ids)

    assert len([d for d in (tmp_path / "cache").iterdir() if d.is_dir()]) == 2
    assert other.t.shape == (2, 40)


def test_subjects_in_another_order_are_refused_not_regressed_against_the_wrong_rows(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    ids = [f"sub-{i}" for i in range(_N_SUBJECTS)]
    ids[3], ids[4] = ids[4], ids[3]

    with pytest.raises(ValueError, match="first difference at row 3"):
        ComponentMapStore(tmp_path / "cache").request(source, scores, ids)


def test_a_run_with_another_number_of_subjects_than_the_source_is_refused(tmp_path):
    scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)

    with pytest.raises(ValueError, match="not the matrix this run was computed from"):
        ComponentMapStore(tmp_path / "cache").request(source, scores[:-1], [f"sub-{i}" for i in range(_N_SUBJECTS - 1)])


def test_load_map_geometry_reads_the_mask_and_the_template_grid(tmp_path):
    _scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)

    geometry = load_map_geometry(source)

    assert geometry.shape == _GRID and int(geometry.mask.sum()) == 40
    assert np.allclose(geometry.affine, np.diag([2.0, 2.0, 2.0, 1.0]))


def test_load_map_geometry_names_why_a_matrix_has_no_brain_map(tmp_path):
    _scores, matrix = _scores_and_matrix()

    with pytest.raises(ValueError, match="non_constant_mask.npy"):
        load_map_geometry(_source_dir(tmp_path / "a", matrix, mask=False))
    with pytest.raises(ValueError, match="reference_template_path"):
        load_map_geometry(_source_dir(tmp_path / "b", matrix, template=False))


def test_to_volume_puts_each_value_on_its_voxel_and_zero_elsewhere(tmp_path):
    _scores, matrix = _scores_and_matrix()
    geometry = load_map_geometry(_source_dir(tmp_path, matrix))
    values = np.arange(1, 41, dtype=np.float32)

    image = to_volume(values, geometry)

    flat = image.get_fdata().reshape(-1)
    assert image.shape == _GRID and np.allclose(flat[geometry.mask], values) and (flat[~geometry.mask] == 0).all()
    with pytest.raises(ValueError, match="mask of 40 voxels"):
        to_volume(values[:-1], geometry)


def test_a_mask_that_does_not_fit_the_template_grid_raises(tmp_path):
    _scores, matrix = _scores_and_matrix()
    source = _source_dir(tmp_path, matrix)
    np.save(source / "non_constant_mask.npy", np.zeros(10, dtype=bool))

    with pytest.raises(ValueError, match="does not fit the grid"):
        load_map_geometry(source)
