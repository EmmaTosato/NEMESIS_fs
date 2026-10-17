"""Unit tests for src/analysis/pca_evaluation.py."""

import json

import numpy as np
import pandas as pd
import pytest

from src.analysis import pca_evaluation
from src.analysis.covariance_pca import fit_covariance_pca, pca_scores, rotated_scores
from src.analysis.pca_evaluation import (
    default_embedding_components,
    load_pca_run,
    load_source_matrix,
    registry_values,
    rotated_variance_shares,
)

_N_SUBJECTS, _N_FEATURES, _K = 40, 30, 4


def _matrix(seed=0, offset=0.0):
    """Four blocks of voxels moving together, plus noise: varimax has real structure to find."""
    rng = np.random.default_rng(seed)
    latent = rng.normal(size=(_N_SUBJECTS, _K))
    loadings = np.zeros((_K, _N_FEATURES))
    for k in range(_K):
        loadings[k, k * 7 : k * 7 + 7] = rng.uniform(1.0, 2.0, size=7)
    return latent @ loadings + rng.normal(scale=0.3, size=(_N_SUBJECTS, _N_FEATURES)) + offset


def _ids():
    return [f"sub-{i:02d}" for i in range(_N_SUBJECTS)]


def _write_config(run_dir, title_method="pca", params=None, **config):
    lines = [f"# proj dim_reduction ({title_method}) - 16-10-26", ""]
    if params is not None:
        lines += [f"Params used: {json.dumps(params)}", ""]
    lines += ["## Config", "```json", json.dumps(config), "```"]
    (run_dir / "config.md").write_text("\n".join(lines))


def _source_dir(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    return source


def _production_run(tmp_path, X, rotation="varimax", n_components=_K, standardize=False):
    pca = fit_covariance_pca(X, standardize=standardize)
    scores = (
        rotated_scores(X, pca, n_components, rotation, 500)[0] if rotation != "none" else pca_scores(X, pca, n_components)
    )
    run = tmp_path / "production"
    run.mkdir()
    np.save(run / "matrix.npy", scores)
    np.save(run / "eigenvalues.npy", pca.eigenvalues)
    pd.DataFrame({"subject_id": _ids(), "dataset": "X"}).to_csv(run / "metadata.csv", index=False)
    params = {"solver": "blocks", "standardize": standardize, "dual": True, "rotation": rotation, "n_components": n_components}
    _write_config(run, params=params, input_path=str(_source_dir(tmp_path)))
    return run, scores, pca


def _tuning_run(tmp_path, X, grid=None, base=None, nested=(), **overrides):
    pca = fit_covariance_pca(X)
    grid = grid if grid is not None else {"rotation": ["none", "varimax"], "n_components": [2, 3]}
    base = base if base is not None else {"standardize": False, "rotation": "none", "n_components": 3}
    arrays = {}
    for rotation in grid.get("rotation", [base["rotation"]]):
        for n in grid.get("n_components", [base["n_components"]]):
            key = ",".join(f"{name}={value}" for name, value in {"rotation": rotation, "n_components": n}.items() if name in grid)
            arrays[key] = pca_scores(X, pca, n) if rotation == "none" else rotated_scores(X, pca, n, rotation, 500)[0]
    run = tmp_path / "tuning"
    run.mkdir()
    np.savez(run / "embeddings.npz", **arrays)
    np.savez(run / "eigenvalues.npz", **{"solver=blocks,standardize=False,dual=True": pca.eigenvalues})
    pd.DataFrame({"subject_id": _ids(), "dataset": "X"}).to_csv(run / "metadata.csv", index=False)
    config = {
        "reduction_method": "pca", "input_path": str(_source_dir(tmp_path)),
        "base_params": base, "tuning_grid": grid, "nested_params": list(nested),
    } | overrides
    _write_config(run, **config)
    return run, arrays, pca


# --- rotated_variance_shares ---------------------------------------------------------------------------------


def test_the_rotated_shares_are_those_of_the_rotated_loadings():
    X = _matrix()
    pca = fit_covariance_pca(X)
    scores, loadings = rotated_scores(X, pca, _K, "varimax", 500)

    shares = rotated_variance_shares(X, scores, pca.eigenvalues)

    np.testing.assert_allclose(shares, (loadings**2).sum(axis=0) / pca.eigenvalues.sum(), rtol=1e-8)
    assert shares.sum() == pytest.approx(pca.cumulative_variance_ratio[_K - 1])


def test_the_rotated_shares_of_a_standardized_pca_are_those_of_its_loadings():
    X = _matrix()
    pca = fit_covariance_pca(X, standardize=True)
    scores, loadings = rotated_scores(X, pca, _K, "varimax", 500)

    shares = rotated_variance_shares(X, scores, pca.eigenvalues, standardize=True)

    np.testing.assert_allclose(shares, (loadings**2).sum(axis=0) / pca.eigenvalues.sum(), rtol=1e-8)


def test_the_rotated_shares_do_not_depend_on_a_large_common_offset():
    X = _matrix(offset=1000.0)
    pca = fit_covariance_pca(X)
    scores, loadings = rotated_scores(X, pca, _K, "varimax", 500)

    shares = rotated_variance_shares(X, scores, pca.eigenvalues)

    np.testing.assert_allclose(shares, (loadings**2).sum(axis=0) / pca.eigenvalues.sum(), rtol=1e-6)


def test_the_rotated_shares_reject_unrotated_scores():
    X = _matrix()
    pca = fit_covariance_pca(X)

    with pytest.raises(ValueError, match="variance 1"):
        rotated_variance_shares(X, pca_scores(X, pca, _K), pca.eigenvalues)


def test_the_rotated_shares_reject_a_matrix_of_other_subjects():
    X = _matrix()
    pca = fit_covariance_pca(X)
    scores, _ = rotated_scores(X, pca, _K, "varimax", 500)

    with pytest.raises(ValueError, match="subjects of the scores"):
        rotated_variance_shares(X[:-1], scores, pca.eigenvalues)


# --- default_embedding_components ----------------------------------------------------------------------------


def test_an_unrotated_run_draws_its_first_two_components():
    assert default_embedding_components("none", None) == (0, 1)


def test_a_rotated_run_draws_the_two_components_with_most_variance():
    assert default_embedding_components("varimax", np.array([0.05, 0.30, 0.10, 0.20])) == (1, 3)


def test_a_rotated_run_without_its_shares_raises():
    with pytest.raises(ValueError, match="no order"):
        default_embedding_components("varimax", None)


# --- load_pca_run: production --------------------------------------------------------------------------------


def test_a_production_run_is_read_whole(tmp_path):
    X = _matrix()
    run_dir, scores, pca = _production_run(tmp_path, X)

    run = load_pca_run(run_dir)

    assert (run.kind, run.rotation, run.n_components, run.standardize) == ("production", "varimax", _K, False)
    np.testing.assert_array_equal(run.scores, scores)
    np.testing.assert_array_equal(run.eigenvalues, pca.eigenvalues)
    assert run.subject_ids == _ids()
    assert run.source_dir == tmp_path / "source"


def test_a_production_run_refuses_a_rotation_or_a_count_of_components(tmp_path):
    run_dir, _, _ = _production_run(tmp_path, _matrix())

    with pytest.raises(ValueError, match="production run"):
        load_pca_run(run_dir, rotation="none")


def test_a_production_run_of_another_method_raises(tmp_path):
    run_dir, _, _ = _production_run(tmp_path, _matrix())
    (run_dir / "config.md").write_text((run_dir / "config.md").read_text().replace("dim_reduction (pca)", "dim_reduction (umap)"))

    with pytest.raises(ValueError, match="'umap' run, not a 'pca'"):
        load_pca_run(run_dir)


def test_a_production_run_whose_scores_disagree_with_its_params_raises(tmp_path):
    run_dir, scores, _ = _production_run(tmp_path, _matrix())
    np.save(run_dir / "matrix.npy", scores[:, :2])

    with pytest.raises(ValueError, match="n_components"):
        load_pca_run(run_dir)


def test_a_run_whose_source_matrix_is_gone_raises(tmp_path):
    run_dir, _, _ = _production_run(tmp_path, _matrix())
    (tmp_path / "source").rmdir()

    with pytest.raises(FileNotFoundError, match="not on this disk"):
        load_pca_run(run_dir)


def test_a_directory_that_is_not_a_run_raises(tmp_path):
    with pytest.raises(ValueError, match="neither"):
        load_pca_run(tmp_path)


# --- load_pca_run: tuning ------------------------------------------------------------------------------------


def test_a_tuning_combination_is_read_with_the_rotation_and_count_asked(tmp_path):
    X = _matrix()
    run_dir, arrays, pca = _tuning_run(tmp_path, X)

    run = load_pca_run(run_dir, rotation="varimax", n_components=3)

    assert (run.kind, run.rotation, run.n_components) == ("tuning", "varimax", 3)
    np.testing.assert_array_equal(run.scores, arrays["rotation=varimax,n_components=3"])
    np.testing.assert_array_equal(run.eigenvalues, pca.eigenvalues)
    assert run.subject_ids == _ids()


def test_a_parameter_the_grid_did_not_sweep_is_the_base_one(tmp_path):
    X = _matrix()
    run_dir, arrays, _ = _tuning_run(
        tmp_path, X, grid={"n_components": [2, 3]}, base={"standardize": False, "rotation": "varimax", "n_components": 3}
    )

    run = load_pca_run(run_dir, rotation="varimax", n_components=2)

    np.testing.assert_array_equal(run.scores, arrays["n_components=2"])
    with pytest.raises(ValueError, match="0 combinations"):
        load_pca_run(run_dir, rotation="none", n_components=2)


def test_a_combination_that_was_not_swept_raises_with_the_swept_ones(tmp_path):
    run_dir, _, _ = _tuning_run(tmp_path, _matrix())

    with pytest.raises(ValueError, match="0 combinations.*rotation=none,n_components=2"):
        load_pca_run(run_dir, rotation="none", n_components=10)


def test_a_tuning_needs_the_combination_to_judge(tmp_path):
    run_dir, _, _ = _tuning_run(tmp_path, _matrix())

    with pytest.raises(ValueError, match="which combination"):
        load_pca_run(run_dir)


def test_a_tuning_with_nested_leaves_raises(tmp_path):
    run_dir, _, _ = _tuning_run(tmp_path, _matrix(), nested=["rotation"])

    with pytest.raises(ValueError, match="nested leaves"):
        load_pca_run(run_dir, rotation="none", n_components=2)


def test_a_tuning_that_swept_another_parameter_raises(tmp_path):
    run_dir, _, _ = _tuning_run(tmp_path, _matrix())
    config = (run_dir / "config.md").read_text().replace('"n_components": [2, 3]', '"n_components": [2, 3], "standardize": [true, false]')
    (run_dir / "config.md").write_text(config)

    with pytest.raises(ValueError, match="only rotation and n_components are supported"):
        load_pca_run(run_dir, rotation="none", n_components=2)


def test_a_tuning_of_another_method_raises(tmp_path):
    run_dir, _, _ = _tuning_run(tmp_path, _matrix(), reduction_method="umap")

    with pytest.raises(ValueError, match="'umap' tuning"):
        load_pca_run(run_dir, rotation="none", n_components=2)


def test_a_tuning_with_several_decompositions_raises(tmp_path):
    run_dir, _, pca = _tuning_run(tmp_path, _matrix())
    np.savez(run_dir / "eigenvalues.npz", a=pca.eigenvalues, b=pca.eigenvalues)

    with pytest.raises(ValueError, match="2 decompositions"):
        load_pca_run(run_dir, rotation="none", n_components=2)


# --- load_source_matrix --------------------------------------------------------------------------------------


def _save_source(run_dir, X, ids):
    source = run_dir.parent / "source"
    np.save(source / "matrix.npy", X)
    pd.DataFrame({"subject_id": ids, "dataset": "X"}).to_csv(source / "metadata.csv", index=False)


def test_the_source_matrix_is_the_one_with_the_subjects_of_the_run_in_order(tmp_path):
    X = _matrix()
    run_dir, _, _ = _production_run(tmp_path, X)
    _save_source(run_dir, X, _ids())

    matrix = load_source_matrix(load_pca_run(run_dir))

    np.testing.assert_array_equal(matrix, X)


def test_a_source_matrix_with_the_subjects_in_another_order_raises(tmp_path):
    X = _matrix()
    run_dir, _, _ = _production_run(tmp_path, X)
    ids = _ids()
    ids[0], ids[1] = ids[1], ids[0]
    _save_source(run_dir, X, ids)

    with pytest.raises(ValueError, match="first difference at row 0"):
        load_source_matrix(load_pca_run(run_dir))


def test_a_source_matrix_with_fewer_subjects_raises(tmp_path):
    X = _matrix()
    run_dir, _, _ = _production_run(tmp_path, X)
    _save_source(run_dir, X[:-1], _ids()[:-1])

    with pytest.raises(ValueError, match="not the matrix this run was computed from"):
        load_source_matrix(load_pca_run(run_dir))


# --- registry_values -----------------------------------------------------------------------------------------


def _registry(monkeypatch, frame):
    monkeypatch.setattr(pca_evaluation, "load_participants_registry", lambda: frame)


def test_registry_values_follow_the_order_of_the_subjects(monkeypatch):
    _registry(monkeypatch, pd.DataFrame({"subject_id": ["a", "b", "c"], "volume": ["10", "20", "30"]}))

    np.testing.assert_array_equal(registry_values(["c", "a"], "volume"), [30.0, 10.0])


def test_registry_values_raise_for_a_subject_that_is_not_registered(monkeypatch):
    _registry(monkeypatch, pd.DataFrame({"subject_id": ["a"], "volume": ["10"]}))

    with pytest.raises(ValueError, match="not in the registry"):
        registry_values(["a", "z"], "volume")


def test_registry_values_raise_for_a_subject_without_the_value(monkeypatch):
    _registry(monkeypatch, pd.DataFrame({"subject_id": ["a", "b"], "volume": ["10", np.nan]}))

    with pytest.raises(ValueError, match="no 'volume'"):
        registry_values(["a", "b"], "volume")


def test_registry_values_raise_for_a_column_that_does_not_exist(monkeypatch):
    _registry(monkeypatch, pd.DataFrame({"subject_id": ["a"], "volume": ["10"]}))

    with pytest.raises(ValueError, match="no 'age' column"):
        registry_values(["a"], "age")
