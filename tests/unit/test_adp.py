"""Unit tests for src/analysis/adp.py.

The tests that fit ADP need `dadapy`, which lives in a separate environment from the rest of the
project (see the module docstring): they are skipped where it is not installed. The ones that do
not fit anything (parameter validation, the lazy import itself) run everywhere.
"""

import importlib.util
import sys

import numpy as np
import pytest
from sklearn.metrics import adjusted_rand_score

from src.analysis import adp
from src.analysis.adp import NOISE_LABEL, adp_cluster, run_adp_tuning_sweep, validate_adp_params
from src.analysis.clustering_tuning import run_clustering_tuning_sweep

requires_dadapy = pytest.mark.skipif(importlib.util.find_spec("dadapy") is None, reason="dadapy is not installed in this environment")

_PARAMS = {"metric": "dice", "Z": 1.65, "maxk": 15}


def _blobs(n_per_group=30, n_groups=3, n_features_per_group=40, seed=0):
    """Binary matrix of n_groups groups, each active (p=0.7) on its own block of columns only."""
    rng = np.random.default_rng(seed)
    labels = np.repeat(np.arange(n_groups), n_per_group)
    X = np.zeros((len(labels), n_groups * n_features_per_group), dtype=np.uint8)
    for row, group in enumerate(labels):
        X[row, group * n_features_per_group : (group + 1) * n_features_per_group] = rng.random(n_features_per_group) < 0.7
    return X, labels


@pytest.mark.parametrize(
    "params, message",
    [
        ({"metric": "dice", "Z": 1.0}, "missing \\['maxk'\\]"),
        ({**_PARAMS, "random_state": 0}, "unknown \\['random_state'\\]"),
        ({**_PARAMS, "metric": "cosine"}, "'metric' must be one of"),
        ({**_PARAMS, "Z": 0}, "'Z' must be a positive number"),
        ({**_PARAMS, "Z": -1.0}, "'Z' must be a positive number"),
        ({**_PARAMS, "Z": True}, "'Z' must be a positive number"),
        ({**_PARAMS, "Z": float("nan")}, "'Z' must be a positive number"),
        ({**_PARAMS, "maxk": 1}, "'maxk' must be an integer >= 2"),
        ({**_PARAMS, "maxk": 10.0}, "'maxk' must be an integer >= 2"),
    ],
)
def test_validate_adp_params_rejects_bad_params(params, message):
    with pytest.raises(ValueError, match=message):
        validate_adp_params(params)


def test_validate_adp_params_returns_metric_z_maxk():
    assert validate_adp_params({"maxk": 20, "Z": 2, "metric": "jaccard"}) == ("jaccard", 2.0, 20)


def test_missing_dadapy_raises_a_clear_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "dadapy", None)  # makes `import dadapy` raise ImportError

    with pytest.raises(ImportError, match="separate environment"):
        adp._import_dadapy()


def test_adp_tuning_sweep_rejects_unknown_grid_keys():
    with pytest.raises(ValueError, match="unknown \\['n_clusters'\\]"):
        run_adp_tuning_sweep(np.ones((5, 3)), _PARAMS, {"n_clusters": [2, 3]})


@requires_dadapy
@pytest.mark.parametrize("metric", ["dice", "jaccard", "euclidean"])
def test_adp_cluster_recovers_well_separated_groups(metric):
    X, truth = _blobs()

    labels = adp_cluster(X, {**_PARAMS, "metric": metric})

    assert len(labels) == len(X)
    assert adjusted_rand_score(truth, labels) == pytest.approx(1.0)


@requires_dadapy
def test_adp_cluster_is_deterministic():
    X, _ = _blobs()

    assert np.array_equal(adp_cluster(X, _PARAMS), adp_cluster(X, _PARAMS))


@requires_dadapy
def test_adp_cluster_on_a_continuous_matrix_uses_the_weighted_distance():
    X, truth = _blobs()
    X_continuous = X * np.random.default_rng(1).random(X.shape)

    labels = adp_cluster(X_continuous, _PARAMS)

    assert adjusted_rand_score(truth, labels) == pytest.approx(1.0)


@requires_dadapy
@pytest.mark.parametrize("metric", ["dice", "euclidean"])
def test_adp_cluster_labels_zero_rows_as_noise_and_duplicate_rows_like_their_twin(metric):
    X, _ = _blobs()
    X[5] = 0  # no dice/jaccard distance: dropped for every metric, so the subject set does not depend on the metric
    X[7] = X[6]  # exact duplicate: clustered once

    labels = adp_cluster(X, {**_PARAMS, "metric": metric})

    assert labels[5] == NOISE_LABEL
    assert labels[7] == labels[6] != NOISE_LABEL
    assert (labels == NOISE_LABEL).sum() == 1


def test_adp_cluster_all_zero_matrix_raises():
    with pytest.raises(ValueError, match="every row of X is all-zero"):
        adp_cluster(np.zeros((10, 4)), _PARAMS)


@requires_dadapy
def test_adp_cluster_maxk_not_smaller_than_the_number_of_distinct_rows_raises():
    X, _ = _blobs(n_per_group=3)  # 9 rows

    with pytest.raises(ValueError, match="maxk=15 needs more than maxk distinct rows"):
        adp_cluster(X, _PARAMS)


@requires_dadapy
def test_adp_tuning_sweep_returns_one_row_and_one_label_array_per_combination():
    X, truth = _blobs()

    results, labels_by_combo = run_adp_tuning_sweep(X, _PARAMS, {"Z": [0.5, 1.65, 4.0]})

    assert list(results["Z"]) == [0.5, 1.65, 4.0]
    assert set(labels_by_combo) == {(0.5,), (1.65,), (4.0,)}
    assert all(len(labels) == len(X) for labels in labels_by_combo.values())
    assert list(results["n_clusters_found"]) == [3.0, 3.0, 3.0]
    assert results["largest_cluster_share"].iloc[0] == pytest.approx(1 / 3)
    assert np.isfinite(results["silhouette"]).all()
    assert results["id_2nn"].nunique() == 1  # intrinsic dimension does not depend on Z
    # dice: calinski_harabasz/davies_bouldin are centroid-based, NaN off euclidean
    assert results["calinski_harabasz"].isna().all() and results["davies_bouldin"].isna().all()


@requires_dadapy
def test_adp_tuning_sweep_ari_vs_prev_z_is_nan_for_the_lowest_z_and_follows_z_order_not_grid_order():
    X, _ = _blobs()

    results, labels_by_combo = run_adp_tuning_sweep(X, _PARAMS, {"Z": [4.0, 0.5, 1.65]})

    by_z = results.set_index("Z")["ari_vs_prev_z"]
    assert np.isnan(by_z[0.5])
    assert by_z[1.65] == pytest.approx(adjusted_rand_score(labels_by_combo[(0.5,)], labels_by_combo[(1.65,)]))
    assert by_z[4.0] == pytest.approx(adjusted_rand_score(labels_by_combo[(1.65,)], labels_by_combo[(4.0,)]))


@requires_dadapy
def test_adp_tuning_sweep_without_z_in_the_grid_has_no_ari_and_metric_sweep_scores_euclidean_geometry():
    X, _ = _blobs()

    results, _ = run_adp_tuning_sweep(X, _PARAMS, {"metric": ["dice", "euclidean"]})

    assert results["ari_vs_prev_z"].isna().all()
    euclidean = results[results["metric"] == "euclidean"].iloc[0]
    assert np.isfinite(euclidean["calinski_harabasz"]) and np.isfinite(euclidean["davies_bouldin"])
    assert np.isnan(results[results["metric"] == "dice"].iloc[0]["calinski_harabasz"])


@requires_dadapy
def test_adp_tuning_sweep_reports_noise_fraction_for_dropped_rows():
    X, _ = _blobs()
    X[0] = 0

    results, _ = run_adp_tuning_sweep(X, _PARAMS, {"Z": [1.65]})

    assert results["noise_fraction"].iloc[0] == pytest.approx(1 / len(X))


@requires_dadapy
def test_run_clustering_tuning_sweep_dispatches_adp_to_its_own_sweep():
    X, _ = _blobs()

    results, labels_by_combo = run_clustering_tuning_sweep("adp", X, _PARAMS, {"Z": [1.0, 2.0]})

    assert "n_clusters_found" in results.columns
    assert len(labels_by_combo) == 2


def test_run_clustering_tuning_sweep_rejects_consensus_config_for_adp():
    with pytest.raises(ValueError, match="consensus/stability clustering is only defined"):
        run_clustering_tuning_sweep("adp", np.ones((5, 3)), _PARAMS, {"Z": [1.0]}, {"rsc": {"n_repeats": 3}})


@requires_dadapy
def test_adp_tuning_sweep_ari_vs_prev_z_ignores_the_dropped_rows():
    X, _ = _blobs()
    X[0] = 0

    results, labels_by_combo = run_adp_tuning_sweep(X, _PARAMS, {"Z": [0.5, 1.65]})

    expected = adjusted_rand_score(labels_by_combo[(0.5,)][1:], labels_by_combo[(1.65,)][1:])
    assert results["ari_vs_prev_z"].iloc[1] == pytest.approx(expected)


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("offset", [0.0, 1000.0])
def test_euclidean_dispersion_scores_match_sklearn_computed_on_the_features(seed, offset):
    """offset: a large common shift makes every squared distance between centroids a difference of big
    numbers - the centroid-to-itself entry then comes out ~1e-8 instead of exactly 0, which made the
    Davies-Bouldin ratio explode (1.5e7 instead of 2.3 on the real s2.4-vol sweep) before the diagonal was fixed."""
    from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score

    from src.analysis.adp import _euclidean_dispersion_scores
    from src.analysis.distances import pairwise_distance

    rng = np.random.default_rng(seed)
    X = rng.normal(size=(60, 8)) + np.repeat(rng.normal(scale=3, size=(4, 8)), 15, axis=0) + offset
    labels = np.repeat(np.arange(4), 15)
    labels[rng.choice(60, 6, replace=False)] = rng.integers(0, 4, 6)  # not perfectly separated

    ch, db = _euclidean_dispersion_scores(pairwise_distance(X, "euclidean") ** 2, labels)

    assert ch == pytest.approx(calinski_harabasz_score(X, labels), rel=1e-6)
    assert db == pytest.approx(davies_bouldin_score(X, labels), rel=1e-6)
