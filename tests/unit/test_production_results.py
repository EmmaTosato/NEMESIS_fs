"""Unit tests for src/analysis/production_results.py: production_results.csv and production_results_per_cluster.csv."""

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score

from src.analysis.dbcv import run_dbcv
from src.analysis.production_results import (
    EUCLIDEAN_ONLY_NOTE,
    METRICS_BY_METHOD,
    NO_CLUSTER_NOTE,
    PER_CLUSTER_COLUMNS_BY_METHOD,
    PER_CLUSTER_FILENAME,
    RESULTS_FILENAME,
    agglomerative_results,
    compute_production_results,
    density_results,
    read_production_results,
    write_production_results,
)

WARD = {"n_clusters": 3, "linkage": "ward", "metric": "euclidean"}


def _blobs() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(centre, 0.4, (20, 2)) for centre in ((0, 0), (6, 0), (0, 6))])
    return X, np.repeat([0, 1, 2], 20)


def _noisy_blobs() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Two clusters of 30 and 6 noise subjects (label -1), with a probability for the clustered ones and NaN for the noise."""
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(centre, 0.3, (30, 2)) for centre in (0.0, 8.0)] + [rng.uniform(-20, 30, (6, 2))])
    labels = np.array([0] * 30 + [1] * 30 + [-1] * 6)
    membership = np.where(labels == -1, np.nan, np.linspace(0.5, 1.0, len(labels)))
    return X, labels, membership


def _by_metric(results) -> dict[str, tuple[float, str]]:
    return {row.metric: (row.value, row.note) for row in results.results.itertuples()}


def test_agglomerative_results_have_one_row_per_measure_with_the_values_of_the_libraries():
    X, labels = _blobs()
    labels = AgglomerativeClustering(**{k: v for k, v in WARD.items() if k != "metric"}).fit_predict(X)

    results = agglomerative_results(X, labels, WARD)

    rows = _by_metric(results)
    assert list(rows) == [
        "silhouette", "calinski_harabasz", "davies_bouldin", "dunn", "largest_cluster_share", "cophenetic_correlation", "dendrogram_jump",
    ]
    assert rows["silhouette"][0] == pytest.approx(silhouette_score(X, labels))
    assert rows["calinski_harabasz"][0] == pytest.approx(calinski_harabasz_score(X, labels))
    assert rows["davies_bouldin"][0] == pytest.approx(davies_bouldin_score(X, labels))
    assert rows["largest_cluster_share"][0] == pytest.approx(np.bincount(labels).max() / len(labels))
    assert all(note == "" for _value, note in rows.values())
    assert list(results.per_cluster.columns) == ["cluster", "n", "silhouette_mean", "share_negative"]
    assert results.per_cluster["n"].tolist() == np.bincount(labels).tolist()


def test_agglomerative_results_with_a_non_euclidean_metric_leave_the_euclidean_only_indices_empty_with_the_note():
    X, labels = _blobs()
    params = {"n_clusters": 3, "linkage": "average", "metric": "cosine"}
    labels = AgglomerativeClustering(n_clusters=3, linkage="average", metric="cosine").fit_predict(X)

    rows = _by_metric(agglomerative_results(X, labels, params))

    for name in ("calinski_harabasz", "davies_bouldin", "dunn"):
        assert np.isnan(rows[name][0]) and rows[name][1] == EUCLIDEAN_ONLY_NOTE
    assert not np.isnan(rows["silhouette"][0]) and rows["silhouette"][1] == ""


def test_agglomerative_results_leave_the_tree_rows_empty_when_the_refit_does_not_reproduce_the_labels():
    X, _ = _blobs()
    labels = np.arange(len(X)) % 3  # three clusters, but not the ones the tree gives

    rows = _by_metric(agglomerative_results(X, labels, WARD))

    assert not np.isnan(rows["silhouette"][0])  # the indices do not need the tree
    for name in ("cophenetic_correlation", "dendrogram_jump"):
        assert np.isnan(rows[name][0]) and "does not reproduce" in rows[name][1]


def test_agglomerative_results_with_one_cluster_have_empty_indices_with_the_reason_and_still_the_share():
    X, _ = _blobs()

    results = agglomerative_results(X, np.zeros(len(X), dtype=int), {"n_clusters": 1, "linkage": "ward"})

    rows = _by_metric(results)
    for name in ("silhouette", "calinski_harabasz", "davies_bouldin", "dunn"):
        assert np.isnan(rows[name][0]) and "at least 2 clusters" in rows[name][1]
    assert rows["largest_cluster_share"][0] == 1.0
    assert results.summary is None
    assert results.per_cluster["n"].tolist() == [len(X)] and results.per_cluster["silhouette_mean"].isna().all()


def test_density_results_rows_and_per_cluster_table_of_hdbscan():
    X, labels, membership = _noisy_blobs()

    results = density_results(X, labels, {"min_cluster_size": 10}, membership)

    rows = _by_metric(results)
    assert list(rows) == ["n_clusters_found", "noise_fraction", "largest_cluster_share", "dbcv", "membership_mean"]
    assert rows["n_clusters_found"][0] == 2
    assert rows["noise_fraction"][0] == pytest.approx(6 / 66)
    assert rows["largest_cluster_share"][0] == pytest.approx(30 / 66)
    assert rows["dbcv"][0] == pytest.approx(run_dbcv(X, labels, {}).score)
    assert rows["membership_mean"][0] == pytest.approx(np.nanmean(membership))  # the noise (NaN) is not in the mean
    table = results.per_cluster
    assert list(table.columns) == ["cluster", "n", "dbcv", "membership_mean"]
    assert table["n"].tolist() == [30, 30]
    assert table["membership_mean"].tolist() == pytest.approx([membership[labels == c].mean() for c in (0, 1)])
    assert results.dbcv is not None and results.summary is None


def test_density_results_of_hdbscan_soft_add_the_persistence_per_cluster_and_its_mean():
    X, labels, membership = _noisy_blobs()

    results = density_results(X, labels, {}, membership, persistence=np.array([0.2, 0.6]))

    rows = _by_metric(results)
    assert rows["persistence_mean"][0] == pytest.approx(0.4)
    assert list(results.per_cluster.columns) == ["cluster", "n", "dbcv", "membership_mean", "persistence"]
    assert results.per_cluster["persistence"].tolist() == [0.2, 0.6]  # value i belongs to the cluster labelled i


def test_density_results_with_no_cluster_are_empty_with_the_reason_and_have_no_cluster_row():
    X, _, _ = _noisy_blobs()
    labels = np.full(len(X), -1)

    results = density_results(X, labels, {}, np.full(len(X), np.nan), persistence=np.array([]))

    rows = _by_metric(results)
    assert rows["n_clusters_found"][0] == 0 and rows["noise_fraction"][0] == 1.0
    for name in ("largest_cluster_share", "membership_mean", "persistence_mean"):
        assert np.isnan(rows[name][0]) and rows[name][1] == NO_CLUSTER_NOTE
    assert np.isnan(rows["dbcv"][0]) and "fewer than 2 clusters" in rows["dbcv"][1]
    assert len(results.per_cluster) == 0 and "persistence" in results.per_cluster.columns


def test_density_results_with_one_cluster_have_no_dbcv_but_every_other_row():
    X, labels, membership = _noisy_blobs()
    labels = np.where(labels == 1, -1, labels)
    membership = np.where(labels == -1, np.nan, membership)

    results = density_results(X, labels, {}, membership)

    rows = _by_metric(results)
    assert np.isnan(rows["dbcv"][0]) and "fewer than 2 clusters" in rows["dbcv"][1]
    assert rows["n_clusters_found"][0] == 1 and not np.isnan(rows["membership_mean"][0])
    assert results.per_cluster["dbcv"].isna().all() and results.per_cluster["n"].tolist() == [30]


def test_density_results_refuse_a_membership_that_does_not_match_the_noise():
    X, labels, membership = _noisy_blobs()
    wrong = membership.copy()
    wrong[-1] = 0.0  # a noise subject with a probability: the noise has no cluster

    with pytest.raises(ValueError, match="NaN exactly for the noise"):
        density_results(X, labels, {}, wrong)
    with pytest.raises(ValueError, match="shape"):
        density_results(X, labels, {}, membership[:-1])


def test_density_results_refuse_a_persistence_that_is_not_one_value_per_cluster_label():
    X, labels, membership = _noisy_blobs()

    with pytest.raises(ValueError, match="one value per cluster"):
        density_results(X, labels, {}, membership, persistence=np.array([0.5]))
    with pytest.raises(ValueError, match="one value per cluster"):
        density_results(X, np.where(labels == 0, 5, labels), {}, membership, persistence=np.array([0.5, 0.5]))  # labels 1 and 5


def test_compute_production_results_routes_by_method_and_refuses_what_does_not_fit_it():
    X, labels, membership = _noisy_blobs()

    assert "membership_mean" in _by_metric(compute_production_results("hdbscan", X, labels, {}, membership))
    assert "persistence_mean" in _by_metric(compute_production_results("hdbscan_soft", X, labels, {}, membership, np.array([0.1, 0.2])))
    with pytest.raises(ValueError, match="hdbscan of sklearn does not have it"):
        compute_production_results("hdbscan", X, labels, {}, membership, np.array([0.1, 0.2]))
    with pytest.raises(ValueError, match="hdbscan_soft"):
        compute_production_results("hdbscan_soft", X, labels, {}, membership)  # soft without persistence
    with pytest.raises(ValueError, match="needs membership_own"):
        compute_production_results("hdbscan", X, labels, {})
    with pytest.raises(ValueError, match="no membership or persistence"):
        compute_production_results("agglomerative", X, labels, WARD, membership)
    with pytest.raises(ValueError, match="no production results for method 'kmeans'"):
        compute_production_results("kmeans", X, labels, {})


def test_write_production_results_writes_both_tables_with_counts_as_integers_and_leaves_no_temporary_file(tmp_path):
    X, labels, membership = _noisy_blobs()
    results = density_results(X, labels, {}, membership)

    paths = write_production_results(tmp_path, results)

    assert [path.name for path in paths] == [RESULTS_FILENAME, PER_CLUSTER_FILENAME]
    text = (tmp_path / RESULTS_FILENAME).read_text()
    assert text.splitlines()[0] == "metric,value,note"
    assert "n_clusters_found,2," in text  # `2`, not `2.0`
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted([RESULTS_FILENAME, PER_CLUSTER_FILENAME])


def test_write_production_results_refuses_an_existing_table_before_writing_anything_unless_told_to(tmp_path):
    X, labels, membership = _noisy_blobs()
    results = density_results(X, labels, {}, membership)
    (tmp_path / PER_CLUSTER_FILENAME).write_text("kept")

    with pytest.raises(FileExistsError, match=PER_CLUSTER_FILENAME):
        write_production_results(tmp_path, results)
    assert not (tmp_path / RESULTS_FILENAME).exists() and (tmp_path / PER_CLUSTER_FILENAME).read_text() == "kept"

    write_production_results(tmp_path, results, overwrite=True)
    assert pd.read_csv(tmp_path / PER_CLUSTER_FILENAME)["n"].tolist() == [30, 30]


def _one_result_of_each_method() -> dict:
    """The ProductionResults of each of the three methods, on small real data."""
    X, labels = _blobs()
    noisy_X, noisy_labels, membership = _noisy_blobs()
    return {
        "agglomerative": compute_production_results("agglomerative", X, labels, WARD),
        "hdbscan": compute_production_results("hdbscan", noisy_X, noisy_labels, {}, membership),
        "hdbscan_soft": compute_production_results("hdbscan_soft", noisy_X, noisy_labels, {}, membership, np.array([0.3, 0.8])),
    }


def test_the_rows_and_columns_read_back_are_the_ones_each_method_writes():
    for method, results in _one_result_of_each_method().items():
        assert tuple(results.results["metric"]) == METRICS_BY_METHOD[method]
        assert tuple(results.per_cluster.columns) == PER_CLUSTER_COLUMNS_BY_METHOD[method]


@pytest.mark.parametrize("method", ["agglomerative", "hdbscan", "hdbscan_soft"])
def test_read_production_results_gives_back_what_write_production_results_wrote(tmp_path, method):
    results = _one_result_of_each_method()[method]
    write_production_results(tmp_path, results)

    saved = read_production_results(tmp_path, method)

    written = {row.metric: (row.value, row.note) for row in results.results.itertuples()}
    assert set(saved.values) == set(written)
    for metric, (value, note) in written.items():
        assert saved.values[metric] == pytest.approx(float(value) if value == value else np.nan, nan_ok=True)
        assert saved.notes[metric] == (note if isinstance(note, str) else "")
    pd.testing.assert_frame_equal(saved.per_cluster, results.per_cluster, check_dtype=False)


def test_read_production_results_keeps_a_measure_that_is_not_defined_as_nan_with_its_reason(tmp_path):
    X, labels = _blobs()
    write_production_results(tmp_path, compute_production_results("agglomerative", X, labels, {**WARD, "metric": "cosine", "linkage": "average"}))

    saved = read_production_results(tmp_path, "agglomerative")

    assert np.isnan(saved.values["dunn"]) and saved.notes["dunn"] == EUCLIDEAN_ONLY_NOTE
    assert saved.values["silhouette"] > 0 and saved.notes["silhouette"] == ""


def test_read_production_results_of_a_run_that_is_all_noise_has_nan_values_and_no_cluster_row(tmp_path):
    X = np.zeros((6, 2))
    labels = np.full(6, -1)
    write_production_results(tmp_path, compute_production_results("hdbscan_soft", X, labels, {}, np.full(6, np.nan), np.array([])))

    saved = read_production_results(tmp_path, "hdbscan_soft")

    assert saved.values["n_clusters_found"] == 0 and saved.values["noise_fraction"] == 1
    assert np.isnan(saved.values["dbcv"]) and np.isnan(saved.values["membership_mean"])
    assert saved.notes["membership_mean"] == NO_CLUSTER_NOTE and saved.per_cluster.empty


def test_read_production_results_names_the_missing_file(tmp_path):
    write_production_results(tmp_path, _one_result_of_each_method()["hdbscan"])
    (tmp_path / PER_CLUSTER_FILENAME).unlink()

    with pytest.raises(FileNotFoundError, match=PER_CLUSTER_FILENAME):
        read_production_results(tmp_path, "hdbscan")
    with pytest.raises(FileNotFoundError, match=RESULTS_FILENAME):
        read_production_results(tmp_path / "empty", "hdbscan")


def test_read_production_results_refuses_files_that_are_not_the_methods(tmp_path):
    write_production_results(tmp_path, _one_result_of_each_method()["hdbscan"])

    with pytest.raises(ValueError, match="persistence_mean"):
        read_production_results(tmp_path, "hdbscan_soft")  # a plain hdbscan run read as a soft one
    with pytest.raises(ValueError, match="no production results for method 'kmeans'"):
        read_production_results(tmp_path, "kmeans")


def test_read_production_results_refuses_a_header_a_repeated_metric_and_a_value_that_is_not_a_number(tmp_path):
    write_production_results(tmp_path, _one_result_of_each_method()["hdbscan"])
    path = tmp_path / RESULTS_FILENAME
    original = path.read_text()

    path.write_text(original.replace("metric,value,note", "metric,score,note"))
    with pytest.raises(ValueError, match="columns"):
        read_production_results(tmp_path, "hdbscan")
    path.write_text(original.replace("noise_fraction", "dbcv"))
    with pytest.raises(ValueError, match="metrics"):
        read_production_results(tmp_path, "hdbscan")
    path.write_text(original.replace("n_clusters_found,2", "n_clusters_found,two"))
    with pytest.raises(ValueError, match="not a number"):
        read_production_results(tmp_path, "hdbscan")
    path.write_text(original)
    per_cluster = tmp_path / PER_CLUSTER_FILENAME
    per_cluster.write_text(per_cluster.read_text().replace("membership_mean", "probability"))
    with pytest.raises(ValueError, match="columns"):
        read_production_results(tmp_path, "hdbscan")
