"""Test a proprietà di src/analysis/cluster_comparison.py: invarianti degli indici di accordo e delle
tabelle di contingenza su vettori di etichette arbitrari (cluster unico, tutti singoletti, rumore -1,
id non contigui, nomi permutati)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.cluster_comparison import (
    AGREEMENT_LEVELS,
    AGREEMENT_METRICS,
    AGREEMENT_SCALE,
    agreement_level,
    agreement_metrics,
    align_runs,
    chi_square_independence,
    cluster_centroids,
    cluster_name,
    contingency_tables,
    purity_table,
)

# Id non contigui, con il rumore: la strategia copre sia pochi cluster grandi sia molti piccoli.
_LABEL_POOL = [-1, 0, 1, 3, 7, 12]


@st.composite
def _label_pair(draw, min_size: int = 2, max_size: int = 40):
    n = draw(st.integers(min_size, max_size))
    pool_a = draw(st.lists(st.sampled_from(_LABEL_POOL), min_size=1, max_size=6, unique=True))
    pool_b = draw(st.lists(st.sampled_from(_LABEL_POOL), min_size=1, max_size=6, unique=True))
    a = draw(st.lists(st.sampled_from(pool_a), min_size=n, max_size=n))
    b = draw(st.lists(st.sampled_from(pool_b), min_size=n, max_size=n))
    return np.array(a), np.array(b)


def _rename(labels: np.ndarray, seed: int) -> np.ndarray:
    """Cambia i nomi dei cluster con una biiezione casuale su id non contigui (la partizione resta quella)."""
    names = np.unique(labels)
    rng = np.random.default_rng(seed)
    new_names = rng.choice(np.arange(-5, 500), size=len(names), replace=False)
    return pd.Series(labels).map(dict(zip(names.tolist(), new_names.tolist()))).to_numpy()


# --- agreement_metrics -------------------------------------------------------------------------


@given(_label_pair(), st.integers(0, 10_000), st.integers(0, 10_000))
def test_agreement_is_invariant_to_renaming_the_clusters_of_either_run(pair, seed_a, seed_b):
    a, b = pair
    base = agreement_metrics(a, b)
    renamed = agreement_metrics(_rename(a, seed_a), _rename(b, seed_b))
    for name in AGREEMENT_METRICS:
        assert renamed[name] == pytest.approx(base[name], abs=1e-12)


@given(_label_pair())
def test_ari_and_nmi_are_symmetric_and_homogeneity_completeness_swap(pair):
    a, b = pair
    forward, backward = agreement_metrics(a, b), agreement_metrics(b, a)
    assert forward["ARI"] == pytest.approx(backward["ARI"], abs=1e-12)
    assert forward["NMI"] == pytest.approx(backward["NMI"], abs=1e-12)
    # lezione #41: l'asimmetria è quella documentata, non un'altra
    assert forward["homogeneity"] == pytest.approx(backward["completeness"], abs=1e-12)
    assert forward["completeness"] == pytest.approx(backward["homogeneity"], abs=1e-12)


@given(_label_pair())
def test_every_metric_is_finite_and_inside_its_range(pair):
    a, b = pair
    values = agreement_metrics(a, b)
    assert tuple(values) == AGREEMENT_METRICS
    assert all(np.isfinite(v) for v in values.values())
    assert values["ARI"] <= 1.0 + 1e-12
    for name in ("NMI", "homogeneity", "completeness"):
        assert -1e-12 <= values[name] <= 1.0 + 1e-12


@given(
    st.lists(st.sampled_from(_LABEL_POOL), min_size=2, max_size=40),
    st.dictionaries(st.sampled_from(_LABEL_POOL), st.sampled_from([-1, 0, 1, 2]), min_size=len(_LABEL_POOL), max_size=len(_LABEL_POOL)),
)
def test_a_finer_than_b_gives_full_homogeneity_and_a_coarser_one_full_completeness(labels_a, coarsening):
    """B = f(A): A raffina B. Documentato: omogeneità 1 (ogni cluster di A sta in uno di B).
    Scambiando gli argomenti i due punteggi si scambiano: lo scambio di argomenti dentro
    `agreement_metrics` farebbe fallire questo test."""
    a = np.array(labels_a)
    b = np.array([coarsening[label] for label in labels_a])
    forward, backward = agreement_metrics(a, b), agreement_metrics(b, a)
    assert forward["homogeneity"] == pytest.approx(1.0, abs=1e-12)
    assert backward["completeness"] == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("n", [2, 3, 10])
def test_degenerate_partitions_are_finite(n):
    single = np.zeros(n, dtype=int)
    singletons = np.arange(n)
    for a, b in [(single, single), (singletons, singletons), (single, singletons), (singletons, single)]:
        assert all(np.isfinite(v) for v in agreement_metrics(a, b).values())
    assert agreement_metrics(singletons, singletons)["ARI"] == pytest.approx(1.0)


def test_the_noise_label_is_a_group_like_any_other():
    a = np.array([-1, -1, 0, 0, 1, 1])
    assert agreement_metrics(a, a + 10)["ARI"] == pytest.approx(1.0)  # il rumore rinominato non cambia nulla


# --- contingency_tables ------------------------------------------------------------------------


@given(_label_pair())
def test_contingency_counts_cover_every_subject_and_percentages_sum_to_100(pair):
    a, b = pair
    tables = contingency_tables(a, b)
    assert int(tables.counts.to_numpy().sum()) == len(a)
    assert set(tables.counts.index) == set(a.tolist())
    assert set(tables.counts.columns) == set(b.tolist())
    np.testing.assert_allclose(tables.row_pct.sum(axis=1), 100.0)
    np.testing.assert_allclose(tables.col_pct.sum(axis=0), 100.0)
    assert (tables.counts.to_numpy() >= 0).all()


@given(_label_pair(), st.integers(0, 10_000))
def test_contingency_does_not_depend_on_the_order_of_the_subjects(pair, seed):
    a, b = pair
    order = np.random.default_rng(seed).permutation(len(a))
    pd.testing.assert_frame_equal(contingency_tables(a, b).counts, contingency_tables(a[order], b[order]).counts)


@given(_label_pair())
def test_contingency_of_swapped_runs_is_the_transpose(pair):
    a, b = pair
    forward, backward = contingency_tables(a, b), contingency_tables(b, a)
    np.testing.assert_array_equal(forward.counts.to_numpy(), backward.counts.to_numpy().T)
    np.testing.assert_allclose(forward.row_pct.to_numpy(), backward.col_pct.to_numpy().T)


# --- align_runs --------------------------------------------------------------------------------


@st.composite
def _two_runs(draw):
    n_a = draw(st.integers(1, 25))
    ids = [f"sub-STUNIPD{i:04d}" for i in range(40)]
    in_a = draw(st.permutations(ids).map(lambda p: p[:n_a]))
    n_b = draw(st.integers(1, 25))
    in_b = draw(st.permutations(ids).map(lambda p: p[:n_b]))
    labels_a = draw(st.lists(st.sampled_from(_LABEL_POOL), min_size=n_a, max_size=n_a))
    labels_b = draw(st.lists(st.sampled_from(_LABEL_POOL), min_size=n_b, max_size=n_b))
    meta_a = pd.DataFrame({"subject_id": in_a, "cluster_label": labels_a})
    meta_b = pd.DataFrame({"subject_id": in_b, "cluster_label": labels_b})
    return meta_a, meta_b


@given(_two_runs())
def test_align_runs_reports_the_intersection_against_the_full_sizes(runs):
    meta_a, meta_b = runs
    common = set(meta_a["subject_id"]) & set(meta_b["subject_id"])
    if not common:
        with pytest.raises(ValueError, match="share no subject_id"):
            align_runs(meta_a, meta_b)
        return
    aligned = align_runs(meta_a, meta_b)
    assert aligned.n_common == len(common)
    assert aligned.n_only_a == len(meta_a) - len(common)
    assert aligned.n_only_b == len(meta_b) - len(common)
    assert aligned.n_only_a >= 0 and aligned.n_only_b >= 0
    # nell'ordine di A, ogni soggetto con le proprie etichette
    expected_order = [s for s in meta_a["subject_id"] if s in common]
    assert aligned.subject_ids.tolist() == expected_order
    label_a = dict(zip(meta_a["subject_id"], meta_a["cluster_label"]))
    label_b = dict(zip(meta_b["subject_id"], meta_b["cluster_label"]))
    assert aligned.labels_a.tolist() == [label_a[s] for s in expected_order]
    assert aligned.labels_b.tolist() == [label_b[s] for s in expected_order]


@given(_two_runs(), st.integers(0, 10_000))
def test_align_runs_pairs_the_same_labels_whatever_the_row_order_of_run_b(runs, seed):
    meta_a, meta_b = runs
    if not set(meta_a["subject_id"]) & set(meta_b["subject_id"]):
        return
    shuffled_b = meta_b.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    first, second = align_runs(meta_a, meta_b), align_runs(meta_a, shuffled_b)
    assert first.subject_ids.tolist() == second.subject_ids.tolist()
    assert first.labels_b.tolist() == second.labels_b.tolist()


# --- chi-square, purity, centroids -------------------------------------------------------------


@given(_label_pair(min_size=4))
def test_chi_square_is_consistent_with_the_table_it_receives(pair):
    a, b = pair
    counts = contingency_tables(a, b).counts
    if counts.shape[0] < 2 or counts.shape[1] < 2:
        with pytest.raises(ValueError, match="at least 2 clusters on each side"):
            chi_square_independence(counts)
        return
    result = chi_square_independence(counts)
    assert result.chi2 >= 0.0
    assert 0.0 <= result.p_value <= 1.0
    assert result.dof == (counts.shape[0] - 1) * (counts.shape[1] - 1)
    assert result.residuals.shape == counts.shape
    if result.dof > 1:  # con 1 grado di libertà scipy applica la correzione di Yates
        assert float((result.residuals.to_numpy() ** 2).sum()) == pytest.approx(result.chi2, rel=1e-9)
    # i residui standardizzati pesati hanno somma 0 per riga: (O - E) somma a zero sulle righe
    expected_row_sums = np.zeros(counts.shape[0])
    expected = counts.sum(axis=1).to_numpy()[:, None] * counts.sum(axis=0).to_numpy()[None, :] / counts.to_numpy().sum()
    np.testing.assert_allclose(
        (result.residuals.to_numpy() * np.sqrt(expected)).sum(axis=1), expected_row_sums, atol=1e-8
    )


@given(_label_pair())
def test_purity_table_is_sorted_and_covers_every_subject_once(pair):
    a, b = pair
    counts = contingency_tables(a, b).counts
    table = purity_table(counts)
    assert int(table["n_subjects"].sum()) == len(a)
    assert table["purity_pct"].is_monotonic_increasing
    assert ((table["purity_pct"] > 0) & (table["purity_pct"] <= 100 + 1e-9)).all()
    # la purezza è almeno 1/#colonne: il bersaglio dominante ha la quota massima
    assert (table["purity_pct"] >= 100 / counts.shape[1] - 1e-9).all()
    assert set(table["dominant_target_cluster"]) <= set(counts.columns)


@given(_label_pair())
def test_purity_is_100_when_a_run_refines_the_other_in_that_direction(pair):
    a, _ = pair
    coarse = np.where(a == -1, -1, 0)  # B è un accorpamento di A
    table = purity_table(contingency_tables(a, coarse).counts)
    assert (table["purity_pct"] == 100.0).all()


@given(
    st.lists(st.sampled_from(_LABEL_POOL), min_size=2, max_size=30),
    st.integers(1, 4),
    st.integers(0, 10_000),
)
def test_cluster_centroids_are_the_mean_of_each_cluster_and_weigh_back_to_the_global_mean(labels, n_dims, seed):
    labels = np.array(labels)
    embedding = np.random.default_rng(seed).normal(size=(len(labels), n_dims))
    centroids = cluster_centroids(embedding, labels)
    assert sorted(centroids.index) == sorted(set(labels.tolist()))
    sizes = pd.Series(labels).value_counts().reindex(centroids.index).to_numpy()
    np.testing.assert_allclose((centroids.to_numpy() * sizes[:, None]).sum(axis=0) / len(labels), embedding.mean(axis=0), atol=1e-10)


# --- agreement_level, cluster_name -------------------------------------------------------------


@given(st.floats(-1, 1), st.floats(-1, 1))
def test_agreement_level_is_monotone_in_the_value(x, y):
    lo, hi = sorted((x, y))
    for metric in AGREEMENT_SCALE:
        assert AGREEMENT_LEVELS.index(agreement_level(metric, lo)) <= AGREEMENT_LEVELS.index(agreement_level(metric, hi))


@pytest.mark.parametrize("metric", AGREEMENT_METRICS)
def test_agreement_level_none_exactly_for_metrics_without_a_scale(metric):
    level = agreement_level(metric, 0.5)
    assert (level is None) == (metric not in AGREEMENT_SCALE)


@pytest.mark.parametrize("metric", sorted(AGREEMENT_SCALE))
def test_agreement_level_at_a_bound_belongs_to_the_level_above(metric):
    for position, bound in enumerate(AGREEMENT_SCALE[metric]):
        assert agreement_level(metric, bound) == AGREEMENT_LEVELS[position + 1]


@given(st.integers(-1000, 1000))
def test_cluster_name_labels_only_minus_one_as_noise(label):
    assert (cluster_name(label) == "rumore") == (label == -1)
    if label != -1:
        assert cluster_name(label) == str(label)
