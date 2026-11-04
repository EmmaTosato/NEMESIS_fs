"""`scripts/build_tuning_summary_tables.py`: classifica dei k, risoluzione della cartella e rami di errore.

Il rendering LaTeX è I/O esterno (`compile_to_png`, già coperto dal test della tabella dei dataset): qui si prova la
logica che decide cosa finisce nelle celle, con dati veri piccoli e senza sostituire nessuna funzione del repo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import scripts.build_tuning_summary_tables as tables
from src.analysis.clustering_tuning_analysis import ClusteringTuningRun


def test_top_k_row_ranks_by_silhouette_and_breaks_ties_by_smaller_k():
    silhouette = pd.Series([0.30, 0.50, 0.50, 0.10, 0.20, 0.40, 0.45], index=[2, 3, 4, 5, 6, 7, 8])
    cells = tables.top_k_row(silhouette)
    assert cells["top_k"] == "3, 4, 8, 7, 2"
    assert cells["range_k"] == "2--8"
    assert cells["top_silhouette"] == "0.300--0.500 (0.200)"
    assert cells["all_silhouette"] == "0.100--0.500"


def test_top_k_row_writes_a_real_minus_sign_for_negative_silhouette():
    silhouette = pd.Series([-0.1, -0.2, -0.3, -0.4, -0.5, -0.6], index=range(2, 8))
    assert tables.top_k_row(silhouette)["all_silhouette"] == "$-$0.600--$-$0.100"


def test_top_k_row_rejects_nan_and_too_few_k():
    with pytest.raises(ValueError, match="NaN at k=\\[3\\]"):
        tables.top_k_row(pd.Series([0.1, np.nan, 0.3, 0.4, 0.5, 0.6], index=range(2, 8)))
    with pytest.raises(ValueError, match="need more than 5"):
        tables.top_k_row(pd.Series([0.1, 0.2, 0.3, 0.4, 0.5], index=range(2, 7)))


def test_find_run_dir_picks_the_session_and_rejects_none_or_several(tmp_path):
    base = tmp_path / "hdbscan" / "pca"
    (base / "17-10_s2.4-vol_nc30").mkdir(parents=True)
    (base / "19-10_s2.4-vol_nc30_varimax").mkdir()  # not the unrotated run
    (base / "17-10_s2.1-x_nc30").mkdir()
    spec = tables.RunSpec("hdbscan", "pca", 30)
    assert tables.find_run_dir(tmp_path, spec, "s2.4-vol").name == "17-10_s2.4-vol_nc30"
    with pytest.raises(FileNotFoundError, match="nc12"):
        tables.find_run_dir(tmp_path, tables.RunSpec("hdbscan", "pca", 12), "s2.4-vol")
    (base / "18-10_s2.4-vol_nc30").mkdir()
    with pytest.raises(ValueError, match="2 tunings match"):
        tables.find_run_dir(tmp_path, spec, "s2.4-vol")


def _density_run(tmp_path, labels_by_key, results):
    return ClusteringTuningRun(tmp_path, "hdbscan", tmp_path, pd.DataFrame(results), labels_by_key)


def test_density_table_leaves_out_no_cluster_rows_and_counts_them_in_the_title(tmp_path):
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(0, 0.1, (20, 2)), rng.normal(5, 0.1, (20, 2))])
    two_clusters = np.repeat([0, 1], 20)
    all_noise = np.full(40, -1)
    results = [
        {"min_cluster_size": 10, "min_samples": 1, "noise_fraction": 0.0, "n_clusters_found": 2, "largest_cluster_share": 0.5, "dbcv": 0.4},
        {"min_cluster_size": 20, "min_samples": 1, "noise_fraction": 1.0, "n_clusters_found": 0, "largest_cluster_share": np.nan, "dbcv": np.nan},
    ]
    labels = {"min_cluster_size=10,min_samples=1": two_clusters, "min_cluster_size=20,min_samples=1": all_noise}
    latex = tables.density_table(_density_run(tmp_path, labels, results), X, None, "PCA, nc2", soft=False)
    assert "1 of 2 combinations with clusters" in latex
    assert "10 / 1" in latex and "20 / 1" not in latex


def test_density_silhouettes_rejects_a_single_cluster(tmp_path):
    X = np.random.default_rng(0).normal(size=(10, 2))
    results = [{"min_cluster_size": 10, "min_samples": 1, "noise_fraction": 0.0, "n_clusters_found": 1, "largest_cluster_share": 1.0, "dbcv": np.nan}]
    run = _density_run(tmp_path, {"min_cluster_size=10,min_samples=1": np.zeros(10, dtype=int)}, results)
    with pytest.raises(ValueError, match="silhouette undefined"):
        tables.density_silhouettes(run, X, run.results)
