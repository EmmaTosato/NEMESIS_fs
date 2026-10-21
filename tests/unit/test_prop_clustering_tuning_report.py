"""Unit tests for src/analysis/clustering_tuning_report.py."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.clustering_tuning_report import (
    _k_ranges,
    _silhouette_comment,
    tuning_report_markdown,
)


@given(st.lists(st.one_of(st.none(), st.floats(-1, 1, allow_nan=False)), min_size=2, max_size=20))
def test_the_silhouette_bullets_count_exactly_the_negative_and_the_missing_values_and_never_a_band(values):
    group = pd.DataFrame({"n_clusters": range(2, 2 + len(values)), "silhouette": pd.Series(values, dtype=float)})
    text = "\n".join(_silhouette_comment(group))
    negative = int((group["silhouette"] < 0).sum())
    missing = int(group["silhouette"].isna().sum())

    assert ("- **Silhouette negativa**: nessuna" in text) == (negative == 0)
    if negative:
        assert f"- **Silhouette negativa**: {negative} k su {len(values)} (" in text
    assert ("Silhouette non calcolabile" in text) == (missing > 0)
    if missing:
        assert f"- **Silhouette non calcolabile**: {missing} k su {len(values)} (" in text
    assert "fascia" not in text and "convenzione" not in text


@st.composite
def _adp_results(draw):
    n = draw(st.integers(1, 10))
    z_values = draw(st.permutations([1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]).map(lambda p: p[:n]))
    metrics = draw(st.lists(st.sampled_from(["dice", "jaccard", "euclidean"]), min_size=n, max_size=n))
    silhouettes = draw(st.lists(st.one_of(st.none(), st.floats(-0.5, 0.9, allow_nan=False).map(lambda v: round(v, 3))), min_size=n, max_size=n))
    return pd.DataFrame({"metric": metrics, "Z": z_values, "silhouette": pd.Series(silhouettes, dtype=float), "n_clusters_found": [3.0] * n})


@settings(max_examples=30)
@given(_adp_results())
def test_the_adp_report_has_every_row_once_ordered_by_silhouette_with_the_empty_ones_last(tmp_path_factory, results):
    report = tuning_report_markdown(tmp_path_factory.mktemp("run"), "adp", Path("matrix"), results)
    sections = re.split(r"^## metric = ", report, flags=re.M)[1:]
    assert {s.split("\n", 1)[0] for s in sections} == set(results["metric"])  # una tabella per metrica, nessuna persa
    total_rows = 0
    for section in sections:
        name = section.split("\n", 1)[0]
        table_lines = [line for line in section.split("## Termini")[0].splitlines() if line.startswith("| ")][1:]  # senza intestazione
        z_in_report = [float(line.split("|")[1]) for line in table_lines]
        group = results[results["metric"] == name]
        expected = group.sort_values("silhouette", ascending=False, na_position="last", kind="stable")["Z"].tolist()
        assert z_in_report == expected
        total_rows += len(table_lines)
    assert total_rows == len(results)


@pytest.mark.parametrize("method", ["kmeans", "gmm", "spectral", "dbscan"])
def test_a_report_for_a_method_without_one_is_refused(method):
    with pytest.raises(ValueError, match="no report for clustering_method"):
        tuning_report_markdown(Path("run"), method, Path("m"), pd.DataFrame({"silhouette": [0.1]}))


@pytest.mark.parametrize("method", ["adp", "hdbscan"])
def test_the_agglomerative_frames_are_refused_for_every_other_method(method):
    frame = pd.DataFrame({"metric": ["dice"], "Z": [1.0], "silhouette": [0.1]})
    with pytest.raises(ValueError, match="belong to the agglomerative report"):
        tuning_report_markdown(Path("run"), method, Path("m"), frame, cophenetic=frame)


@given(st.sets(st.integers(1, 60), min_size=1, max_size=20))
def test_k_ranges_expands_back_to_exactly_the_given_values(values):
    text = _k_ranges(sorted(values))
    expanded = set()
    for part in text.split(", "):
        low, _, high = part.partition("-")
        expanded.update(range(int(low), int(high or low) + 1))
    assert expanded == values
    assert text == _k_ranges(sorted(values, reverse=True))  # l'ordine di ingresso è irrilevante
