"""Test a proprietà di src/analysis/cluster_composition.py: la tabella di composizione somma alla
coorte, le barre al 100% per cluster, i NaN e i soggetti fuori registro non spariscono né cambiano
il denominatore, l'ordine delle righe è irrilevante."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.cluster_composition import (
    COMPOSITION_VARIABLES,
    build_composition_figure,
    cluster_colors,
    composition_frame,
)
from src.utils import participants as participants_registry
from tests.factories.ids import subject_id

_BY_NAME = {v.name: v for v in COMPOSITION_VARIABLES}
_LABELS = [-1, 0, 2, 7]  # rumore e id non contigui
_SIDES = ["left", "right", "both"]
_DATASETS = ["UNIPD/WashU", "UKLFR/stroke_UKLFR", "UNIPD/PSP"]


# --- composition_frame sul registro ---------------------------------------------------------------


def _write_registry(root, subjects: list[str], seed: int, drop_columns=()) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(subjects)
    registry = pd.DataFrame({
        "subject_id": subjects, "original_id": subjects, "dataset": rng.choice(_DATASETS, size=n),
        "disease_id": "ST", "has_lesion": "True", "has_sdc": "True", "has_features": "False",
        "lesion_side": rng.choice(_SIDES + [""], size=n),  # "" = cella vuota del registro
        "NIHSS": [("" if rng.random() < 0.3 else f"{rng.integers(0, 25)}") for _ in range(n)],
        "lesion_volume_voxels_2mm": [f"{rng.integers(1, 90_000)}" for _ in range(n)],
        "disconnection_load_voxels_2mm": [f"{rng.integers(1, 90_000)}" for _ in range(n)],
        "location_dominant_2mm": rng.choice(["cortex_only", "white_matter_only"], size=n),
    }).drop(columns=list(drop_columns))
    root.mkdir(exist_ok=True)
    registry.to_csv(root / "participants.csv", index=False)
    return registry


@st.composite
def _run(draw):
    """Metadata di una run con soggetti in ordine casuale, alcuni fuori registro (indici 12..15)."""
    ids = draw(st.permutations(list(range(16))).map(lambda p: p[: draw(st.integers(1, 16))]))
    labels = draw(st.lists(st.sampled_from(_LABELS), min_size=len(ids), max_size=len(ids)))
    return list(ids), labels


@settings(max_examples=40)
@given(_run())
def test_composition_frame_has_one_row_per_subject_in_run_order_and_lists_the_unregistered(tmp_path_factory, monkeypatch, caplog, run):
    ids, labels = run
    root = tmp_path_factory.mktemp("meta")
    registry = _write_registry(root, [subject_id(i) for i in range(12)], seed=5)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    metadata = pd.DataFrame({"subject_id": [subject_id(i) for i in ids], "cluster_label": labels})

    caplog.clear()  # hypothesis riusa la fixture tra gli esempi
    with caplog.at_level(logging.WARNING):
        frame, unregistered = composition_frame(metadata)

    assert len(frame) == len(metadata)  # nessun soggetto perso: la dimensione è quella della run
    assert frame["subject_id"].tolist() == metadata["subject_id"].tolist()
    assert frame["cluster_label"].tolist() == labels
    assert unregistered == sorted(set(metadata["subject_id"]) - set(registry["subject_id"]))
    assert bool(unregistered) == any("no row in" in r.message for r in caplog.records)  # avvisa se e solo se serve
    missing_rows = frame["subject_id"].isin(unregistered)
    for variable in COMPOSITION_VARIABLES:
        assert frame.loc[missing_rows, variable.name].isna().all()
    known = frame.loc[~missing_rows].set_index("subject_id")
    expected = registry.set_index("subject_id").reindex(known.index)
    np.testing.assert_allclose(known["lesion_volume"], expected["lesion_volume_voxels_2mm"].astype(float))
    # NIHSS: cella vuota -> NaN numerico, non 0 e non stringa
    np.testing.assert_allclose(known["nihss"], pd.to_numeric(expected["NIHSS"]), equal_nan=True)


@settings(max_examples=25)
@given(st.permutations(list(range(10))))
def test_composition_frame_follows_the_subject_when_the_rows_are_shuffled(tmp_path_factory, monkeypatch, order):
    root = tmp_path_factory.mktemp("meta")
    _write_registry(root, [subject_id(i) for i in range(10)], seed=1)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    labels = [(i * 3) % 4 for i in range(10)]
    straight, _ = composition_frame(pd.DataFrame({"subject_id": [subject_id(i) for i in range(10)], "cluster_label": labels}))
    shuffled, _ = composition_frame(
        pd.DataFrame({"subject_id": [subject_id(i) for i in order], "cluster_label": [labels[i] for i in order]})
    )
    pd.testing.assert_frame_equal(straight.set_index("subject_id").sort_index(), shuffled.set_index("subject_id").sort_index())


@pytest.mark.parametrize("variable", COMPOSITION_VARIABLES, ids=lambda v: v.name)
def test_composition_frame_names_the_registry_column_it_cannot_find(tmp_path, monkeypatch, variable):
    _write_registry(tmp_path / "meta", [subject_id(0), subject_id(1)], seed=0, drop_columns=[variable.registry_column])
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", tmp_path / "meta")
    metadata = pd.DataFrame({"subject_id": [subject_id(0)], "cluster_label": [0]})
    with pytest.raises(ValueError, match=variable.registry_column):
        composition_frame(metadata)


def test_composition_frame_refuses_a_run_without_cluster_labels(tmp_path, monkeypatch):
    _write_registry(tmp_path / "meta", [subject_id(0)], seed=0)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", tmp_path / "meta")
    with pytest.raises(ValueError, match="not a clustering run"):
        composition_frame(pd.DataFrame({"subject_id": [subject_id(0)]}))


# --- build_composition_figure ---------------------------------------------------------------------


def _frame(labels, sides, nihss, volume) -> pd.DataFrame:
    n = len(labels)
    return pd.DataFrame({
        "subject_id": [subject_id(i) for i in range(n)], "cluster_label": labels,
        "dataset": ["UNIPD/WashU"] * n, "lesion_side": sides, "location_dominant": ["cortex_only"] * n,
        "nihss": nihss, "lesion_volume": volume, "disconnection_load": [1.0] * n,
    })


_side_values = st.sampled_from([*_SIDES, None, ""])


@st.composite
def _categorical_frame(draw):
    n = draw(st.integers(1, 40))
    labels = draw(st.lists(st.sampled_from(_LABELS), min_size=n, max_size=n))
    sides = draw(st.lists(_side_values, min_size=n, max_size=n))
    return _frame(labels, sides, [1.0] * n, [10.0] * n)


@settings(max_examples=20)
@given(_categorical_frame())
def test_categorical_bars_cover_the_available_subjects_and_each_cluster_sums_to_100(frame):
    figure = build_composition_figure(frame, _BY_NAME["lesion_side"])
    available = frame["lesion_side"].isin(_SIDES)
    assert f"n={int(available.sum())}/{len(frame)}" in figure.layout.title.text  # denominatore = coorte intera

    labels = sorted(set(frame["cluster_label"]))
    assert [t.name for t in figure.data] == ["left", "right", "both"]  # ordine del vocabolario chiuso
    counts = np.array([list(t.x) for t in figure.data])  # categorie x cluster
    assert counts.sum() == available.sum()
    for position, label in enumerate(labels):
        in_cluster = frame[available & (frame["cluster_label"] == label)]
        assert counts[:, position].sum() == len(in_cluster)
        shares = np.array([t.customdata[position][1] for t in figure.data])
        assert shares.sum() == pytest.approx(100.0 if len(in_cluster) else 0.0)
    assert all(list(t.y) == [str(label) for label in labels] for t in figure.data)


@given(st.lists(st.sampled_from(_LABELS), min_size=2, max_size=20), st.sampled_from(["up", "SINISTRA", "0"]))
def test_a_value_outside_the_closed_vocabulary_raises_instead_of_being_dropped(labels, bad):
    sides = ["left"] * len(labels)
    sides[-1] = bad
    with pytest.raises(ValueError, match="outside the closed category list"):
        build_composition_figure(_frame(labels, sides, [1.0] * len(labels), [1.0] * len(labels)), _BY_NAME["lesion_side"])


@settings(max_examples=20)
@given(st.lists(st.tuples(st.sampled_from(_LABELS), st.sampled_from([None, 1.0, 5.5, 20.0])), min_size=1, max_size=30))
def test_continuous_boxes_hold_exactly_the_non_missing_values_one_box_per_cluster(rows):
    labels = [r[0] for r in rows]
    nihss = [np.nan if r[1] is None else r[1] for r in rows]
    frame = _frame(labels, ["left"] * len(rows), nihss, [100.0] * len(rows))
    figure = build_composition_figure(frame, _BY_NAME["nihss"])
    assert [t.name for t in figure.data] == [str(label) for label in sorted(set(labels))]
    plotted = sum(len(t.y) for t in figure.data)
    assert plotted == int(np.isfinite(nihss).sum())
    assert f"n={plotted}/{len(rows)}" in figure.layout.title.text
    assert figure.layout.yaxis.type == "linear"
    assert build_composition_figure(frame, _BY_NAME["lesion_volume"]).layout.yaxis.type == "log"


@pytest.mark.parametrize("variable", COMPOSITION_VARIABLES, ids=lambda v: v.name)
def test_a_single_cluster_and_a_fully_missing_variable_still_build_a_figure(variable):
    frame = _frame([3, 3, 3], [None] * 3, [np.nan] * 3, [np.nan] * 3).assign(dataset=None, location_dominant=None, disconnection_load=np.nan)
    figure = build_composition_figure(frame, variable)
    assert f"n=0/3" in figure.layout.title.text


@given(st.lists(st.sampled_from(_LABELS), min_size=1, max_size=30), st.integers(0, 10_000))
def test_cluster_colors_cover_every_label_and_do_not_depend_on_row_order(labels, seed):
    frame = _frame(labels, ["left"] * len(labels), [1.0] * len(labels), [1.0] * len(labels))
    colors = cluster_colors(frame)
    assert set(colors) == set(labels)
    assert all(len(c) == 7 and c.startswith("#") for c in colors.values())
    shuffled = frame.sample(frac=1.0, random_state=seed)
    assert cluster_colors(shuffled) == colors
    named = [c for label, c in colors.items() if label != -1]
    assert len(set(named)) == len(named) or len(named) > 8  # colori distinti finché la palette basta
