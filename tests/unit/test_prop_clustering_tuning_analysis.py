"""Unit tests for src/analysis/clustering_tuning_analysis.py."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.cluster.hierarchy import linkage
from sklearn.metrics import adjusted_rand_score

from src.analysis.clustering_tuning_analysis import (
    ClusteringTuningRun,
    LINKAGE_ORDER,
    combo_key,
    dendrogram_jump,
    density_metrics,
    k_curves_figure,
    k_curves_targets,
    linkage_agreement,
    load_clustering_tuning_run,
    noise_filtered_curves_figures,
    silhouette_zoom_limits,
)


_LABEL_POOL = [-1, 0, 1, 4, 9]


@settings(max_examples=40)
@given(
    n=st.integers(4, 25),
    method=st.sampled_from(["ward", "average", "complete", "single"]),
    seed=st.integers(0, 10_000),
)
def test_the_jump_is_the_ratio_of_consecutive_merge_heights_and_never_below_one(n, method, seed):
    points = np.random.default_rng(seed).normal(size=(n, 3))
    tree = linkage(points, method=method)
    assume(tree[:, 2].min() > 0)
    jumps = dendrogram_jump(tree, range(2, n))

    assert sorted(jumps) == list(range(2, n))
    for k, value in jumps.items():
        assert value == pytest.approx(tree[-(k - 1), 2] / tree[-k, 2])
        assert value >= 1.0 - 1e-12  # le altezze di questi linkage non decrescono: il salto non scende sotto 1


@given(st.integers(4, 20), st.integers(0, 10_000), st.integers(0, 10_000))
def test_the_jump_does_not_depend_on_the_order_of_the_subjects(n, seed, order_seed):
    points = np.random.default_rng(seed).normal(size=(n, 3))
    order = np.random.default_rng(order_seed).permutation(n)
    first = dendrogram_jump(linkage(points, method="ward"), range(2, n))
    second = dendrogram_jump(linkage(points[order], method="ward"), range(2, n))
    for k in first:
        assert second[k] == pytest.approx(first[k])


@given(st.integers(3, 15), st.integers(-3, 40))
def test_the_jump_refuses_a_k_outside_the_tree(n, k):
    tree = linkage(np.random.default_rng(0).normal(size=(n, 2)), method="ward")
    if 2 <= k <= n - 1:
        assert k in dendrogram_jump(tree, range(k, k + 1))
    else:
        with pytest.raises(ValueError, match="is outside 2.."):
            dendrogram_jump(tree, range(k, k + 1))


def test_a_zero_height_merge_makes_the_jump_undefined_instead_of_infinite():
    points = np.array([[0.0, 0.0], [0.0, 0.0], [5.0, 5.0], [9.0, 0.0]])  # soggetti duplicati: prima fusione a altezza 0
    with pytest.raises(ValueError, match="height 0"):
        dendrogram_jump(linkage(points, method="ward"), range(3, 4))


@given(st.lists(st.one_of(st.none(), st.floats(-1, 1, allow_nan=False)), min_size=1, max_size=20))
def test_the_zoom_limits_always_contain_the_data_and_ignore_the_missing_values(values):
    series = pd.Series(values, dtype=float)
    if series.dropna().empty:
        with pytest.raises(ValueError, match="no silhouette"):
            silhouette_zoom_limits(series)
        return
    low, high = silhouette_zoom_limits(series)
    assert low < high
    assert low <= series.min() and series.max() <= high
    padding = 0.08 * (series.max() - series.min()) or 0.05
    assert (high - low) == pytest.approx(series.max() - series.min() + 2 * padding)


def _write_hdbscan_run(run_dir: Path, labels_by_row: list[np.ndarray], drop_key: bool = False, extra_key: bool = False) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = {"clustering_method": "hdbscan", "input_path": "matrix_dir", "fine_tuning": True}
    (run_dir / "config.md").write_text(f"# t\n\n```json\n{json.dumps(config)}\n```\n")
    rows = [{"min_cluster_size": 5 + 5 * i, "min_samples": 5, "noise_fraction": 0.0, "silhouette": 0.5, "davies_bouldin": 1.0}
            for i in range(len(labels_by_row))]
    pd.DataFrame(rows).to_csv(run_dir / "tuning_results.csv", index=False)
    arrays = {combo_key(row, ("min_cluster_size", "min_samples")): labels for row, labels in zip(rows, labels_by_row)}
    if drop_key:
        arrays.pop(next(iter(arrays)))
    if extra_key:
        arrays["min_cluster_size=999,min_samples=1"] = labels_by_row[0]
    np.savez(run_dir / "clusterings.npz", **arrays)


@settings(max_examples=15)
@given(st.lists(st.lists(st.sampled_from(_LABEL_POOL), min_size=4, max_size=4), min_size=1, max_size=4), st.sampled_from(["ok", "missing", "extra"]))
def test_a_run_loads_back_every_labeling_or_is_refused_when_npz_and_csv_disagree(tmp_path_factory, labelings, damage):
    run_dir = tmp_path_factory.mktemp("run")
    arrays = [np.array(labels) for labels in labelings]
    _write_hdbscan_run(run_dir, arrays, drop_key=damage == "missing", extra_key=damage == "extra")
    if damage != "ok":
        with pytest.raises(ValueError, match="does not match tuning_results.csv"):
            load_clustering_tuning_run(run_dir)
        return
    run = load_clustering_tuning_run(run_dir)
    assert len(run.labels) == len(run.results) == len(arrays)
    for row, expected in zip(run.results.to_dict("records"), arrays):
        np.testing.assert_array_equal(run.labels[combo_key(row, ("min_cluster_size", "min_samples"))], expected)


def _density_run(labelings: list[np.ndarray], method: str = "hdbscan") -> ClusteringTuningRun:
    rows = [{"min_cluster_size": 5 + i, "min_samples": 5} for i in range(len(labelings))]
    results = pd.DataFrame(rows)
    columns = ("min_cluster_size", "min_samples")
    return ClusteringTuningRun(Path("run"), method, Path("m"), results, {combo_key(row, columns): lab for row, lab in zip(rows, labelings)})


@given(st.lists(st.lists(st.sampled_from(_LABEL_POOL), min_size=1, max_size=25), min_size=1, max_size=4), st.integers(0, 10_000))
def test_density_metrics_are_computed_from_the_labels_with_noise_in_the_denominator(labelings, seed):
    arrays = [np.array(lab) for lab in labelings]
    metrics = density_metrics(_density_run(arrays))

    for i, labels in enumerate(arrays):
        found = labels[labels != -1]
        assert metrics.loc[i, "n_clusters_found"] == len(np.unique(found))
        share = metrics.loc[i, "largest_cluster_share"]
        if len(found) == 0:
            assert np.isnan(share)  # tutto rumore: nessun cluster, quindi nessuna quota (non 0)
        else:
            assert share == pytest.approx(pd.Series(found).value_counts().max() / len(labels))
            assert share <= (len(found) / len(labels)) + 1e-12  # il cluster più grande non supera i soggetti non rumore
    renamed = [pd.Series(a).map({v: (v if v == -1 else v + 50) for v in np.unique(a)}).to_numpy() for a in arrays]
    pd.testing.assert_frame_equal(metrics, density_metrics(_density_run(renamed)))


@given(st.lists(st.integers(0, 3), min_size=1, max_size=15))
def test_density_metrics_refuses_a_stored_cluster_count_that_contradicts_the_labels(labels):
    run = _density_run([np.array(labels)])
    true_count = len(np.unique(labels))
    run.results["n_clusters_found"] = [true_count]
    density_metrics(run)  # coerente: passa
    run.results["n_clusters_found"] = [true_count + 1]
    with pytest.raises(ValueError, match="differs from the clusters"):
        density_metrics(run)


@st.composite
def _agglomerative_run(draw):
    n = draw(st.integers(4, 15))
    metrics = draw(st.lists(st.sampled_from(["euclidean", "cosine"]), min_size=1, max_size=2, unique=True))
    linkages = draw(st.lists(st.sampled_from(["ward", "average", "complete", "single"]), min_size=1, max_size=4, unique=True))
    ks = draw(st.lists(st.integers(2, 4), min_size=1, max_size=3, unique=True))
    rows, labels = [], {}
    columns = ("n_clusters", "linkage", "metric")
    for metric, k, link in itertools.product(metrics, ks, linkages):
        if link == "ward" and metric != "euclidean":
            continue  # ward con una distanza non euclidea non esiste in sklearn: non è nella run
        row = {"n_clusters": k, "linkage": link, "metric": metric}
        rows.append(row)
        labels[combo_key(row, columns)] = np.array(draw(st.lists(st.integers(0, k - 1), min_size=n, max_size=n)))
    assume(rows)
    return ClusteringTuningRun(Path("run"), "agglomerative", Path("m"), pd.DataFrame(rows), labels)


@settings(max_examples=25)
@given(_agglomerative_run())
def test_agreement_has_one_symmetric_row_per_pair_of_linkages_in_the_canonical_order(run):
    table = linkage_agreement(run)
    expected_pairs = 0
    for (_metric, _k), group in run.results.groupby(["metric", "n_clusters"]):
        expected_pairs += len(group) * (len(group) - 1) // 2
    assert len(table) == expected_pairs
    if table.empty:  # un solo linkage per (metric, n_clusters): nessuna coppia, tabella vuota con le colonne giuste
        assert list(table.columns) == ["metric", "n_clusters", "linkage_a", "linkage_b", "ari"]
        return
    assert table["ari"].le(1.0 + 1e-12).all() and np.isfinite(table["ari"]).all()
    order = {name: i for i, name in enumerate(LINKAGE_ORDER)}
    assert all(order[a] < order[b] for a, b in zip(table["linkage_a"], table["linkage_b"]))  # mai (b, a), mai (a, a)
    columns = ("n_clusters", "linkage", "metric")
    for row in table.to_dict("records"):
        keys = {linkage_name: combo_key({"n_clusters": row["n_clusters"], "linkage": linkage_name, "metric": row["metric"]}, columns)
                for linkage_name in (row["linkage_a"], row["linkage_b"])}
        assert row["ari"] == pytest.approx(adjusted_rand_score(run.labels[keys[row["linkage_a"]]], run.labels[keys[row["linkage_b"]]]))


@given(st.integers(4, 15), st.integers(2, 4), st.integers(0, 10_000))
def test_two_linkages_with_the_same_partition_under_other_names_agree_perfectly(n, k, seed):
    labels = np.random.default_rng(seed).integers(0, k, size=n)
    columns = ("n_clusters", "linkage", "metric")
    rows = [{"n_clusters": k, "linkage": link, "metric": "euclidean"} for link in ("average", "complete")]
    run = ClusteringTuningRun(
        Path("run"), "agglomerative", Path("m"), pd.DataFrame(rows),
        {combo_key(rows[0], columns): labels, combo_key(rows[1], columns): (labels + 7) % 11},
    )
    assert linkage_agreement(run)["ari"].tolist() == [pytest.approx(1.0)]


@st.composite
def _curves_results(draw):
    rows = []
    for metric in draw(st.lists(st.sampled_from(["euclidean", "cosine", "manhattan", "dice"]), min_size=1, max_size=3, unique=True)):
        for link in draw(st.lists(st.sampled_from(["ward", "average", "complete", "single"]), min_size=1, max_size=4, unique=True)):
            for k in (2, 3, 4):
                rows.append({"metric": metric, "linkage": link, "n_clusters": k, "silhouette": 0.1 * k,
                             "davies_bouldin": 1.0 if metric == "euclidean" else np.nan})
    return pd.DataFrame(rows)


@settings(max_examples=30)
@given(_curves_results())
def test_the_curves_targets_partition_the_rows_of_the_run(results):
    targets = k_curves_targets(results)
    assert len(targets) == len(set(targets))
    covered = 0
    for metric, single in targets:
        subset = results[(results["metric"] == metric) & ((results["linkage"] == "single") == single)]
        assert not subset.empty
        covered += len(subset)
    assert covered == len(results)  # ogni riga della run sta in un solo grafico
    singles = [t for t in targets if t[1]]
    assert {m for m, _ in singles} == set(results.loc[results["linkage"] == "single", "metric"])


@settings(max_examples=8)
@given(_curves_results())
def test_a_figure_exists_for_every_target_and_none_for_a_metric_the_run_does_not_have(results):
    metric, single = k_curves_targets(results)[0]
    figure = k_curves_figure(results, metric, single)
    has_db = results[(results["metric"] == metric) & ((results["linkage"] == "single") == single)]["davies_bouldin"].notna().any()
    assert len(figure.axes) == (3 if has_db else 2)  # il pannello di Davies-Bouldin sparisce se è tutto NaN
    with pytest.raises(ValueError, match="no row of the run has metric"):
        k_curves_figure(results, "chebyshev", False)


@st.composite
def _noise_metrics(draw):
    methods = draw(st.lists(st.sampled_from(["eom", "leaf"]), min_size=1, max_size=2, unique=True)) if draw(st.booleans()) else [None]
    rows = []
    for method in methods:
        for size in (5, 10, 20):
            for samples in (1, 5):
                row = {"min_cluster_size": size, "min_samples": samples, "silhouette": 0.3, "davies_bouldin": 1.2,
                       "noise_fraction": draw(st.sampled_from([0.0, 0.1, 0.4, 0.9]))}
                if method is not None:
                    row["cluster_selection_method"] = method
                rows.append(row)
    return pd.DataFrame(rows)


@settings(max_examples=8)
@given(_noise_metrics(), st.sampled_from([0.0, 0.1, 0.5, 1.0]))
def test_each_group_has_a_noise_filtered_figure_or_is_listed_as_having_none(metrics, limit):
    figures, without = noise_filtered_curves_figures(metrics, limit)
    if "cluster_selection_method" in metrics.columns:
        groups = {name: group for name, group in metrics.groupby("cluster_selection_method")}
    else:
        groups = {"": metrics}
    assert set(figures) | set(without) == set(groups) and not set(figures) & set(without)  # ogni gruppo in uno solo dei due
    for name, group in groups.items():
        kept = int((group["noise_fraction"] <= limit).sum())
        assert (name in without) == (kept == 0)
        if kept:
            assert f"{kept} of {len(group)} combinations" in figures[name]._suptitle.get_text()
