"""`src/pipeline/plot_tuning_embedding_3d.py`: percorsi di successo e di errore, su file veri minuscoli.

Il registro dei soggetti (`participants.csv`) è reindirizzato in `tmp_path`: le modalità di colore cliniche
(side, volume, nihss...) lo leggono, e non devono mai toccare `assets/metadata/` vero.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from src.analysis.embedding_app import COLOR_MODE_ORDER, NEUTRAL_MODE
from src.pipeline import plot_tuning_embedding_3d as plot3d
from src.utils import participants as participants_registry
from tests.factories.ids import subject_ids

COMBO = "metric=dice,n_components=3,n_neighbors=5"
N = 6
REGISTRY_CLINICAL = {
    "lesion_side": ["left", "right"] * 3,
    "location_dominant_2mm": ["cortex_only", "ventricle"] * 3,
    "lesion_volume_voxels_2mm": [10, 20, 30, 40, 50, 60],
    "disconnection_load_voxels_2mm": [1, 2, 3, 4, 5, 6],
    "disconnection_mean_2mm": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
    "NIHSS": [1, 2, 3, 4, 5, 6],
}


def _write_registry(root, ids):
    root.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        {
            "subject_id": ids,
            "original_id": ids,
            "dataset": "siteA",
            "disease_id": "ST",
            "has_lesion": "True",
            "has_sdc": "True",
            "has_features": "False",
            **REGISTRY_CLINICAL,
        }
    )
    frame.to_csv(root / "participants.csv", index=False)


def _metadata(ids, extra=()):
    frame = pd.DataFrame({"subject_id": ids, "dataset": ["siteA", "siteB"] * (len(ids) // 2)})
    for column in extra:
        frame[column] = 1
    return frame


@pytest.fixture
def tuning_run(tmp_path, monkeypatch):
    """embeddings.npz (una combo a 3 colonne, una a 2) + metadata.csv + registro isolato."""
    ids = subject_ids(N)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", tmp_path / "metadata")
    _write_registry(tmp_path / "metadata", ids)
    rng = np.random.default_rng(0)
    npz = tmp_path / "embeddings.npz"
    np.savez(npz, **{COMBO: rng.normal(size=(N, 3)), "two_cols": rng.normal(size=(N, 2))})
    csv = tmp_path / "metadata.csv"
    _metadata(ids).to_csv(csv, index=False)
    return {"npz": npz, "csv": csv, "ids": ids, "out": tmp_path / "nested" / "out"}


def _argv(run, combo=COMBO, **overrides):
    values = {"npz": run["npz"], "csv": run["csv"], "out": run["out"], **overrides}
    return [
        "--embeddings-npz", str(values["npz"]),
        "--metadata-csv", str(values["csv"]),
        "--combo-key", combo,
        "--reduction-method", "umap",
        "--output-dir", str(values["out"]),
    ]


def test_dataset_only_metadata_writes_unico_and_dataset_and_warns_for_every_other_mode(tuning_run, caplog):
    with caplog.at_level(logging.WARNING):
        code = plot3d.main(_argv(tuning_run))

    assert code == 0
    written = sorted(p.name for p in tuning_run["out"].glob("*.html"))
    assert written == ["embedding_3d_dataset.html", "embedding_3d_unico.html"]
    skipped = {r.getMessage() for r in caplog.records if r.levelno == logging.WARNING}
    # un avviso per ogni modalità saltata, e ciascuno nomina la colonna che manca
    assert len(skipped) == len(COLOR_MODE_ORDER) - 2
    assert any("'lesion_side'" in m for m in skipped)
    assert any("'cluster_label'" in m for m in skipped)


def test_full_metadata_writes_one_html_per_color_mode_and_it_is_a_3d_scatter(tuning_run):
    frame = _metadata(tuning_run["ids"], extra=[
        "lesion_side", "location_dominant_2mm", "lesion_volume_voxels",
        "disconnection_load_voxels_2mm", "disconnection_mean_2mm", "nihss", "cluster_label",
    ])
    frame.to_csv(tuning_run["csv"], index=False)

    assert plot3d.main(_argv(tuning_run)) == 0

    expected = {"embedding_3d_unico.html"} | {
        f"embedding_3d_{m}.html" for m in COLOR_MODE_ORDER if m != NEUTRAL_MODE
    }
    assert {p.name for p in tuning_run["out"].glob("*.html")} == expected
    for path in tuning_run["out"].glob("*.html"):
        text = path.read_text()
        assert "scatter3d" in text, path.name
        assert "umap dim 3" in text, path.name  # asse z etichettato col metodo
        assert COMBO in text, path.name  # il titolo nomina la combinazione resa


def test_output_dir_is_created_with_parents(tuning_run):
    assert not tuning_run["out"].parent.exists()
    assert plot3d.main(_argv(tuning_run)) == 0
    assert tuning_run["out"].is_dir()


@pytest.mark.parametrize(
    "case, expected_in_log",
    [
        ("missing_npz", "embeddings_npz not found"),
        ("missing_csv", "metadata_csv not found"),
        ("unknown_key", "not found in"),
        ("two_columns", "2-column embedding, not 3"),
        ("row_mismatch", "same tuning run's own metadata.csv"),
    ],
)
def test_bad_inputs_return_1_with_the_cause_and_write_nothing(tuning_run, caplog, case, expected_in_log):
    argv_kwargs, combo = {}, COMBO
    if case == "missing_npz":
        argv_kwargs["npz"] = tuning_run["npz"].with_name("absent.npz")
    elif case == "missing_csv":
        argv_kwargs["csv"] = tuning_run["csv"].with_name("absent.csv")
    elif case == "unknown_key":
        combo = "metric=cosine"
    elif case == "two_columns":
        combo = "two_cols"
    elif case == "row_mismatch":
        _metadata(tuning_run["ids"][:4]).to_csv(tuning_run["csv"], index=False)

    with caplog.at_level(logging.ERROR):
        code = plot3d.main(_argv(tuning_run, combo=combo, **argv_kwargs))

    assert code == 1
    assert expected_in_log in caplog.text
    assert not tuning_run["out"].exists()


def test_unknown_key_error_lists_the_known_keys(tuning_run, caplog):
    with caplog.at_level(logging.ERROR):
        plot3d.main(_argv(tuning_run, combo="metric=cosine"))
    assert COMBO in caplog.text and "two_cols" in caplog.text


def test_load_combo_returns_the_stored_embedding_unsliced(tuning_run):
    embedding, metadata = plot3d._load_combo(tuning_run["npz"], tuning_run["csv"], COMBO)
    with np.load(tuning_run["npz"]) as data:
        np.testing.assert_array_equal(embedding, data[COMBO])
    assert embedding.shape == (N, 3)
    assert list(metadata["subject_id"]) == tuning_run["ids"]


def test_subject_absent_from_registry_is_warned_not_a_crash(tuning_run, caplog):
    """Un soggetto assente dal registro diventa 'unknown' (avviso), non un'eccezione: la resa continua."""
    ids = tuning_run["ids"][:5] + ["sub-STUNIPD9999"]
    pd.DataFrame({"subject_id": ids, "dataset": ["a"] * 6, "lesion_side": ["x"] * 6}).to_csv(
        tuning_run["csv"], index=False
    )
    with caplog.at_level(logging.WARNING):
        assert plot3d.main(_argv(tuning_run)) == 0
    assert (tuning_run["out"] / "embedding_3d_side.html").is_file()
    assert "no row in the subject registry" in caplog.text


def test_registry_absent_while_metadata_has_a_clinical_column_returns_1(tuning_run, monkeypatch, tmp_path):
    """Lezione #9: la resa di una modalità clinica legge il registro; se manca, il confine d'errore di main()
    (che copre solo `_load_combo`) lascia uscire un FileNotFoundError grezzo invece di un `return 1` pulito."""
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", tmp_path / "no_registry")
    _metadata(tuning_run["ids"], extra=["lesion_side"]).to_csv(tuning_run["csv"], index=False)
    assert plot3d.main(_argv(tuning_run)) == 1


def test_html_write_failure_returns_1(tuning_run, monkeypatch, caplog):
    """Lezione #9: la scrittura degli HTML (OSError) non è dentro alcun try/except."""
    import plotly.graph_objects as go

    def boom(self, *args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(go.Figure, "write_html", boom)
    with caplog.at_level(logging.INFO):
        assert plot3d.main(_argv(tuning_run)) == 1
    assert "disk full" in caplog.text and "run duration" in caplog.text
