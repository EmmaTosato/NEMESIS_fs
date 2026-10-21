"""Test a proprietà di src/analysis/cluster_description.py: i riassunti per variabile, la tabella a
confronto di tutti i cluster e il join col registro con NaN e soggetti mancanti."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.cluster_description import (
    CLUSTER_DESCRIPTION_VARIABLES,
    build_cluster_description_figure,
    cluster_composition,
    clusters_comparison_stats,
    variable_summary,
)
from src.utils import participants as participants_registry
from tests.factories.ids import subject_id

_CONTINUOUS = [v for v in CLUSTER_DESCRIPTION_VARIABLES if v.kind == "continuous"]
_CATEGORICAL = [v for v in CLUSTER_DESCRIPTION_VARIABLES if v.kind == "categorical"]
_LABELS = [-1, 0, 3, 9]  # rumore e id non contigui


# --- variable_summary -----------------------------------------------------------------------------


@pytest.mark.parametrize("variable", _CONTINUOUS, ids=lambda v: v.name)
@settings(max_examples=30)
@given(st.lists(st.one_of(st.none(), st.floats(-1e6, 1e6, allow_nan=False)), min_size=0, max_size=30))
def test_continuous_summary_is_consistent_with_its_coverage(variable, values):
    composition = pd.DataFrame({variable.name: pd.Series(values, dtype=float)})
    summary = variable_summary(composition, variable)
    present = [v for v in values if v is not None]

    assert summary["n_total"] == len(values)
    assert summary["n_available"] == len(present)
    if not present:
        assert all(summary[key] is None for key in ("mean", "median", "std", "min", "max"))
        return
    assert summary["min"] <= summary["median"] <= summary["max"]
    assert summary["min"] - 1e-6 <= summary["mean"] <= summary["max"] + 1e-6
    assert summary["min"] == min(present) and summary["max"] == max(present)
    assert (summary["std"] is None) == (len(present) == 1)  # un solo valore: nessuna deviazione standard, non 0
    if summary["std"] is not None:
        assert summary["std"] >= 0


@pytest.mark.parametrize("variable", _CATEGORICAL, ids=lambda v: v.name)
@settings(max_examples=30)
@given(st.lists(st.sampled_from(["F", "M", "", None, np.nan]), min_size=0, max_size=30))
def test_categorical_summary_counts_every_valid_value_and_treats_empty_and_nan_as_missing(variable, values):
    composition = pd.DataFrame({variable.name: pd.Series(values, dtype=object)})
    summary = variable_summary(composition, variable)
    valid = [v for v in values if isinstance(v, str) and v != ""]

    assert summary["n_total"] == len(values)
    assert summary["n_available"] == len(valid)
    assert sum(summary["counts"].values()) == summary["n_available"]
    assert set(summary["counts"]) == set(valid)
    assert "" not in summary["counts"]


@given(st.lists(st.floats(-1e3, 1e3, allow_nan=False), min_size=2, max_size=20), st.integers(0, 10_000))
def test_summary_does_not_depend_on_the_order_of_the_rows(values, seed):
    variable = _CONTINUOUS[0]
    shuffled = np.random.default_rng(seed).permutation(values)
    first = variable_summary(pd.DataFrame({variable.name: values}), variable)
    second = variable_summary(pd.DataFrame({variable.name: shuffled}), variable)
    for key in first:
        assert first[key] == pytest.approx(second[key], abs=1e-6)


# --- registro sintetico ---------------------------------------------------------------------------


def _write_registry(root, subjects: list[str], seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(subjects)
    registry = pd.DataFrame({
        "subject_id": subjects, "original_id": subjects, "dataset": "UNIPD/WashU",
        "disease_id": "ST", "has_lesion": "True", "has_sdc": "True", "has_features": "False",
        "age": [f"{a:.1f}" for a in rng.uniform(30, 90, size=n)],
        "sex": rng.choice(["F", "M", ""], size=n),
        "education": [("" if rng.random() < 0.8 else "12") for _ in range(n)],  # copertura bassa, come nei dati veri
        "NIHSS": [("" if rng.random() < 0.3 else str(rng.integers(0, 25))) for _ in range(n)],
        "lesion_volume_voxels_2mm": [str(rng.integers(1, 90_000)) for _ in range(n)],
    })
    root.mkdir(exist_ok=True)
    registry.to_csv(root / "participants.csv", index=False)
    return registry


@st.composite
def _run_metadata(draw):
    n = draw(st.integers(1, 20))
    ids = draw(st.permutations(list(range(20))).map(lambda p: p[:n]))  # i soggetti 12..19 sono fuori registro
    labels = draw(st.lists(st.sampled_from(_LABELS), min_size=n, max_size=n))
    return pd.DataFrame({"subject_id": [subject_id(i) for i in ids], "cluster_label": labels})


@pytest.fixture
def registry_root(tmp_path_factory, monkeypatch):
    root = tmp_path_factory.mktemp("meta")
    registry = _write_registry(root, [subject_id(i) for i in range(12)], seed=2)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return registry


# --- clusters_comparison_stats --------------------------------------------------------------------


@settings(max_examples=40)
@given(_run_metadata())
def test_comparison_stats_partition_the_run_and_count_the_unregistered_per_cluster(registry_root, metadata):
    stats = clusters_comparison_stats(metadata)
    labels = metadata["cluster_label"].tolist()

    assert [s.cluster_label for s in stats] == sorted(set(labels))  # ordine crescente, il rumore (-1) per primo
    assert sum(s.n_total for s in stats) == len(metadata)  # le dimensioni dei cluster sommano alla coorte
    registered = set(registry_root["subject_id"])
    for s in stats:
        members = metadata.loc[metadata["cluster_label"] == s.cluster_label, "subject_id"]
        assert s.n_total == len(members)
        assert s.n_unregistered == len(set(members) - registered)
        assert 0 <= s.n_unregistered <= s.n_total
        for variable in CLUSTER_DESCRIPTION_VARIABLES:
            summary = s.summaries[variable.name]
            assert summary["n_total"] == s.n_total  # il denominatore è sempre la dimensione vera del cluster
            assert summary["n_available"] <= s.n_total - s.n_unregistered
        # lezione #38: chi è fuori registro non diventa un secondo "mancante": l'età (sempre compilata) lo conta una volta sola
        assert s.summaries["age"]["n_available"] == s.n_total - s.n_unregistered


@settings(max_examples=25)
@given(_run_metadata(), st.integers(0, 10_000))
def test_comparison_stats_do_not_depend_on_the_row_order_of_the_metadata(registry_root, metadata, seed):
    shuffled = metadata.sample(frac=1.0, random_state=seed)
    first, second = clusters_comparison_stats(metadata), clusters_comparison_stats(shuffled)
    assert [s.cluster_label for s in first] == [s.cluster_label for s in second]
    for a, b in zip(first, second):
        assert (a.n_total, a.n_unregistered) == (b.n_total, b.n_unregistered)
        for name in a.summaries:
            for key, value in a.summaries[name].items():
                if isinstance(value, dict):
                    assert value == b.summaries[name][key]
                else:
                    assert value == pytest.approx(b.summaries[name][key], abs=1e-9)


@settings(max_examples=25)
@given(_run_metadata())
def test_each_cluster_of_the_table_equals_the_single_cluster_description(registry_root, metadata):
    for s in clusters_comparison_stats(metadata):
        composition, unregistered = cluster_composition(metadata, s.cluster_label)
        assert len(unregistered) == s.n_unregistered
        for variable in CLUSTER_DESCRIPTION_VARIABLES:
            assert variable_summary(composition, variable) == s.summaries[variable.name]


def test_comparison_stats_refuse_a_run_without_cluster_labels(registry_root):
    with pytest.raises(ValueError, match="not a clustering run"):
        clusters_comparison_stats(pd.DataFrame({"subject_id": [subject_id(0)]}))


# --- cluster_composition --------------------------------------------------------------------------


@settings(max_examples=30)
@given(_run_metadata(), st.sampled_from([-1, 0, 3, 9, 4, 100]))
def test_cluster_composition_is_the_registry_join_of_the_cluster_or_a_clear_error(registry_root, caplog, metadata, label):
    caplog.clear()  # hypothesis riusa la fixture tra gli esempi
    members = metadata.loc[metadata["cluster_label"] == label, "subject_id"].tolist()
    if not members:
        with pytest.raises(ValueError, match="no subjects with cluster_label"):
            cluster_composition(metadata, label)
        return
    with caplog.at_level(logging.WARNING):
        composition, unregistered = cluster_composition(metadata, label)
    assert composition["subject_id"].tolist() == members
    assert unregistered == sorted(set(members) - set(registry_root["subject_id"]))
    assert bool(unregistered) == any("no row in" in r.message for r in caplog.records)
    assert list(composition.columns) == ["subject_id", *(v.name for v in CLUSTER_DESCRIPTION_VARIABLES)]
    gone = composition["subject_id"].isin(unregistered)
    assert composition.loc[gone, [v.name for v in CLUSTER_DESCRIPTION_VARIABLES]].isna().all().all()
    # una cella vuota del registro (education, sesso) diventa NaN, non 0 né la stringa vuota
    assert not (composition["education"].dropna() == 0).any()


# --- figura ---------------------------------------------------------------------------------------


@settings(max_examples=12)
@given(_run_metadata())
def test_the_figure_titles_report_the_true_coverage_of_each_variable(registry_root, metadata):
    label = metadata["cluster_label"].iloc[0]
    composition, _ = cluster_composition(metadata, label)
    figure = build_cluster_description_figure(composition, label)
    titles = " ".join(a.text for a in figure.layout.annotations)
    for variable in CLUSTER_DESCRIPTION_VARIABLES:
        summary = variable_summary(composition, variable)
        assert f"n={summary['n_available']}/{summary['n_total']}" in titles
    assert f"{len(composition)} soggetti" in figure.layout.title.text
