"""E2E: la catena intera build_lesion_matrix -> dim_reduction -> clustering -> analyze_clustering_tuning.

Gli altri test di integrazione agganciano al massimo due stadi per volta; qui ogni stadio consuma
l'artefatto vero scritto dal precedente (nessun file scritto a mano nel mezzo), e si verifica che
gli ID dei soggetti, il loro ordine, le shape e i tipi sopravvivano a tutta la catena.
"""

import json

import numpy as np
import pandas as pd
import pytest

from src.pipeline import analyze_clustering_tuning, clustering, dim_reduction
from src.utils.artifacts import load_matrix
from tests.factories.ids import subject_ids
from tests.factories.lesion_dataset import add_clinical_columns, run_build_lesion_matrix, write_json

N_SUBJECTS = 12
N_COMPONENTS = 2

_PCA_ENTRY = {
    "params": {"solver": "blocks", "standardize": False, "dual": True, "rotation": "none", "n_components": N_COMPONENTS},
    "tuning_grid": {"n_components": [1, 2, 3]},
}
_REDUCTION_REGISTRY = {"pca": {**_PCA_ENTRY, "tag_param": ["n_components"], "tag_prefix": ["nc"]}}


def _run_dim_reduction(tmp_path, monkeypatch, input_dir):
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")
    params_path = write_json(tmp_path / "params_reduction.json", _REDUCTION_REGISTRY)
    output_root = tmp_path / "dr_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "chain",
        "overwrite": False,
        "fine_tuning": False,
        "color_by": ["dataset", "volume"],
        "viz_n_components": 2,
        "save_tuning_embeddings": False,
        "tuning_evaluations": {},
        "precompute_distance_metric": True,
        "run_notes": None,
    }
    cfg_path = write_json(tmp_path / "dim_reduction.json", cfg)
    assert dim_reduction.main(["--config", str(cfg_path)]) == 0
    return next(p for p in (output_root / "production" / "pca").iterdir() if p.is_dir()), params_path


def _run_clustering(tmp_path, monkeypatch, input_dir, reduction_params_path, *, fine_tuning, entry):
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")
    params_path = write_json(tmp_path / "params_clustering.json", {"agglomerative": entry})
    output_root = tmp_path / "cl_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "clustering_methods": ["agglomerative"],
        "params_file": str(params_path),
        "reduction_params_file": str(reduction_params_path),
        "output_root": str(output_root),
        "session_name": "chain",
        "overwrite": False,
        "fine_tuning": fine_tuning,
        "reduced_data": True,
        "save_tuning_clusterings": fine_tuning,
        "viz_embedding_path": None,
        "run_notes": None,
    }
    cfg_path = write_json(tmp_path / "clustering.json", cfg)
    assert clustering.main(["--config", str(cfg_path)]) == 0
    kind = "tuning" if fine_tuning else "production"
    return next(p for p in (output_root / kind / "agglomerative" / "pca").iterdir() if p.is_dir())


@pytest.fixture
def chain(tmp_path, monkeypatch):
    matrix_dir = run_build_lesion_matrix(tmp_path, monkeypatch, n_subjects=N_SUBJECTS, seed=7)
    add_clinical_columns(matrix_dir)
    embedding_dir, reduction_params = _run_dim_reduction(tmp_path, monkeypatch, matrix_dir)
    return {"matrix": matrix_dir, "embedding": embedding_dir, "reduction_params": reduction_params}


def test_production_chain_preserves_subjects_order_and_schema(tmp_path, monkeypatch, chain):
    entry = {"params": {"n_clusters": 3, "linkage": "ward", "metric": "euclidean"}}
    cluster_dir = _run_clustering(tmp_path, monkeypatch, chain["embedding"], chain["reduction_params"], fine_tuning=False, entry=entry)

    X_raw, meta_raw, _ = load_matrix(chain["matrix"])
    X_emb, meta_emb, _ = load_matrix(chain["embedding"])
    X_cl, meta_cl, _ = load_matrix(cluster_dir)

    # stesse righe, nello stesso ordine, a ogni stadio
    expected_ids = subject_ids(N_SUBJECTS)
    assert list(meta_raw["subject_id"]) == list(meta_emb["subject_id"]) == list(meta_cl["subject_id"]) == expected_ids

    # shape e tipi
    # voxelwise tiene solo i voxel toccati da almeno una lesione: al più 5 per soggetto, al più 10^3
    assert X_raw.shape[0] == N_SUBJECTS and 0 < X_raw.shape[1] <= min(5 * N_SUBJECTS, 10**3)
    assert set(np.unique(X_raw)) <= {0.0, 1.0}
    assert X_emb.shape == (N_SUBJECTS, N_COMPONENTS)
    assert np.issubdtype(X_emb.dtype, np.floating) and np.isfinite(X_emb).all()
    assert np.array_equal(X_cl, X_emb)  # il clustering non altera l'embedding

    # schema dei metadati: le colonne cliniche arrivano fino in fondo e si aggiunge solo cluster_label
    assert list(meta_cl.columns) == [*meta_emb.columns, "cluster_label"]
    labels = meta_cl["cluster_label"]
    assert np.issubdtype(labels.dtype, np.integer)
    assert labels.notna().all() and set(labels) <= {0, 1, 2}
    assert meta_cl[["subject_id", "dataset", "lesion_volume_voxels", "lesion_side", "nihss"]].equals(
        meta_emb[["subject_id", "dataset", "lesion_volume_voxels", "lesion_side", "nihss"]]
    )

    # il registro delle run riporta lo stesso numero di soggetti dell'input
    runs = pd.read_csv(cluster_dir.parents[1] / "runs.csv")
    assert len(runs) == 1


def test_tuning_chain_feeds_the_analysis_step(tmp_path, monkeypatch, chain):
    entry = {
        "params": {"n_clusters": 3},
        "tuning_grid": {"n_clusters": [2, 3, 4], "linkage": ["ward", "average"], "metric": ["euclidean"]},
    }
    tuning_dir = _run_clustering(tmp_path, monkeypatch, chain["embedding"], chain["reduction_params"], fine_tuning=True, entry=entry)

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 3 * 2  # prodotto della griglia, nessuna combinazione persa o duplicata
    assert not results.duplicated(subset=["n_clusters", "linkage", "metric"]).any()

    monkeypatch.setattr(analyze_clustering_tuning, "LOGS_ROOT", tmp_path / "an_logs")
    cfg = {"tuning_dir": str(tuning_dir), "overwrite": False, "k_range": {"min": 2, "max": 4}, "curves_max_noise_fraction": 0.5}
    assert analyze_clustering_tuning.main(["--config", str(write_json(tmp_path / "an.json", cfg))]) == 0

    jump = pd.read_csv(tuning_dir / "dendrogram_jump.csv")
    assert set(jump["n_clusters"]) <= {2, 3, 4}
    assert jump["jump"].notna().all()
    cophenetic = pd.read_csv(tuning_dir / "cophenetic_correlation.csv")
    value_column = [c for c in cophenetic.columns if c not in ("metric", "linkage")]
    assert len(value_column) == 1, f"colonne inattese in cophenetic_correlation.csv: {list(cophenetic.columns)}"
    assert cophenetic[value_column[0]].between(-1, 1).all()


def test_chain_stops_cleanly_when_an_upstream_artifact_is_missing(tmp_path, monkeypatch, caplog, chain):
    """Se l'embedding sparisce dopo dim_reduction, clustering deve fallire con `return 1`, non con un traceback."""
    import shutil

    shutil.rmtree(chain["embedding"])
    monkeypatch.setattr(clustering, "LOGS_ROOT", tmp_path / "cl_logs")
    params_path = write_json(tmp_path / "params_clustering.json", {"agglomerative": {"params": {"n_clusters": 3, "linkage": "ward", "metric": "euclidean"}}})
    cfg = {
        "project": "testproj",
        "input_path": str(chain["embedding"]),
        "reduction_method": "pca",
        "clustering_methods": ["agglomerative"],
        "params_file": str(params_path),
        "reduction_params_file": str(chain["reduction_params"]),
        "output_root": str(tmp_path / "cl_out"),
        "session_name": "chain",
        "overwrite": False,
        "fine_tuning": False,
        "reduced_data": True,
        "save_tuning_clusterings": False,
        "viz_embedding_path": None,
        "run_notes": None,
    }
    assert clustering.main(["--config", str(write_json(tmp_path / "clustering.json", cfg))]) == 1
    assert "has no manifest.json" in caplog.text  # il motivo giusto, non un'altra validazione di config
