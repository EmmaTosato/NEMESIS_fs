"""Test a proprietà di src/analysis/cluster_pair.py: simmetrie del confronto tra due cluster, NaN nelle
colonne cliniche, soggetti fuori registro, indipendenza dall'ordine delle righe."""

from __future__ import annotations

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.cluster_description import CLUSTER_DESCRIPTION_VARIABLES
from src.analysis.cluster_pair import (
    CATEGORICAL_VARIABLES,
    LOCATION_FRACTIONS,
    PairFrame,
    centroid_separation,
    difference_image,
    pair_clinical_comparison,
    pair_frame,
)
from src.utils import participants as participants_registry
from tests.factories.ids import subject_id

_CONTINUOUS = [v.name for v in CLUSTER_DESCRIPTION_VARIABLES if v.kind == "continuous"]
_LOCATIONS = [name for name, _label, _column in LOCATION_FRACTIONS]
_NUMERIC_COLUMNS = [*_CONTINUOUS, *_LOCATIONS]
_CATEGORIES = {"sex": ["F", "M"], "dataset": ["A", "B", "C"], "lesion_side": ["left", "right"], "location_dominant": ["cortex_only", "white"]}


# --- confronto clinico su un PairFrame costruito direttamente -------------------------------------


def _synthetic_pair(n_1: int, n_2: int, seed: int, nan_rate: float) -> PairFrame:
    """Due cluster (etichette 4 e 9, non contigue) con tutte le colonne del confronto e una quota di NaN."""
    rng = np.random.default_rng(seed)
    n = n_1 + n_2
    frame = pd.DataFrame({"subject_id": [subject_id(i) for i in range(n)], "cluster_label": [4] * n_1 + [9] * n_2})
    for column in _NUMERIC_COLUMNS:
        values = rng.normal(size=n).round(2)  # arrotondati: i pareggi sono realistici e mettono alla prova il test
        values[rng.random(n) < nan_rate] = np.nan
        frame[column] = values
    for name, _label, _column in CATEGORICAL_VARIABLES:
        values = rng.choice(_CATEGORIES[name], size=n).astype(object)
        values[rng.random(n) < nan_rate] = np.nan
        frame[name] = values
    return PairFrame(frame=frame, unregistered=[])


_pair_args = st.tuples(st.integers(2, 8), st.integers(2, 8), st.integers(0, 10_000), st.sampled_from([0.0, 0.2, 0.6]))


@settings(max_examples=30)
@given(_pair_args)
def test_tests_are_swapped_consistently_when_the_two_clusters_swap(args):
    pair = _synthetic_pair(*args)
    forward, backward = pair_clinical_comparison(pair, 4), pair_clinical_comparison(pair, 9)

    pd.testing.assert_series_equal(forward.numeric["n_1"], backward.numeric["n_2"], check_names=False)
    pd.testing.assert_series_equal(forward.numeric["median_1"], backward.numeric["median_2"], check_names=False)
    np.testing.assert_allclose(forward.numeric["r"], -backward.numeric["r"], atol=1e-12, equal_nan=True)
    np.testing.assert_allclose(forward.numeric["p"], backward.numeric["p"], atol=1e-12, equal_nan=True)
    np.testing.assert_allclose(forward.numeric["p_fdr"], backward.numeric["p_fdr"], atol=1e-12, equal_nan=True)
    np.testing.assert_allclose(forward.categorical["share_1"], backward.categorical["share_2"], atol=1e-12, equal_nan=True)
    np.testing.assert_allclose(forward.categorical["p"], backward.categorical["p"], atol=1e-12, equal_nan=True)
    both_finite = np.isfinite(forward.categorical["odds_ratio"]) & np.isfinite(backward.categorical["odds_ratio"])
    both_positive = (forward.categorical["odds_ratio"] > 0) & (backward.categorical["odds_ratio"] > 0)
    usable = (both_finite & both_positive).to_numpy()
    np.testing.assert_allclose(
        forward.categorical["odds_ratio"].to_numpy()[usable] * backward.categorical["odds_ratio"].to_numpy()[usable], 1.0, rtol=1e-9
    )


@given(_pair_args)
def test_counts_exclude_missing_values_and_statistics_stay_in_range(args):
    n_1, n_2, seed, nan_rate = args
    pair = _synthetic_pair(*args)
    frame = pair.frame
    comparison = pair_clinical_comparison(pair, 4)

    first = comparison.numeric.set_index("variable")
    for name, label in [(v.name, v.label) for v in CLUSTER_DESCRIPTION_VARIABLES if v.kind == "continuous"]:
        in_1 = frame.loc[frame["cluster_label"] == 4, name]
        in_2 = frame.loc[frame["cluster_label"] == 9, name]
        assert first.loc[label, "n_1"] == in_1.notna().sum()
        assert first.loc[label, "n_2"] == in_2.notna().sum()
    assert (comparison.numeric["n_1"] <= n_1).all() and (comparison.numeric["n_2"] <= n_2).all()

    numeric = comparison.numeric
    assert numeric["r"].dropna().between(-1.0, 1.0).all()
    # un lato con meno di 2 valori lascia r e p mancanti, mai 0 (e viceversa: con >= 2 per lato il test c'è)
    enough = (numeric["n_1"] >= 2) & (numeric["n_2"] >= 2)
    assert (numeric["p"].notna() == enough).all()
    assert (numeric.loc[~enough, "r"].isna()).all()

    for table in (comparison.numeric, comparison.categorical):
        p, p_fdr = table["p"], table["p_fdr"]
        assert p_fdr.notna().equals(p.notna())  # FDR dove c'è un p, e solo lì
        assert p.dropna().between(0, 1).all() and p_fdr.dropna().between(0, 1).all()
        assert (p_fdr.dropna() >= p.dropna() - 1e-12).all()  # BH non abbassa mai un p
    categorical = comparison.categorical
    assert categorical[["share_1", "share_2"]].stack().dropna().between(0, 1).all()  # NaN = lato con meno di 2 subjects
    assert (categorical["n_1"] + categorical["n_2"] > 0).all()


@settings(max_examples=30)
@given(_pair_args)
def test_the_comparison_does_not_depend_on_the_row_order_of_the_frame(args):
    pair = _synthetic_pair(*args)
    shuffled = PairFrame(pair.frame.sample(frac=1.0, random_state=1).reset_index(drop=True), [])
    first, second = pair_clinical_comparison(pair, 4), pair_clinical_comparison(shuffled, 4)
    pd.testing.assert_frame_equal(first.numeric, second.numeric)
    pd.testing.assert_frame_equal(first.categorical, second.categorical)


def test_a_column_that_is_entirely_missing_leaves_its_tests_missing_not_zero():
    pair = _synthetic_pair(5, 5, seed=0, nan_rate=0.0)
    pair.frame["age"] = np.nan
    pair.frame["sex"] = np.nan
    comparison = pair_clinical_comparison(pair, 4)
    age = comparison.numeric.set_index("variable").loc["Age (years)"]
    assert age["n_1"] == 0 and age["n_2"] == 0
    assert np.isnan(age[["median_1", "median_2", "r", "p"]].astype(float)).all()
    assert "Sex" not in set(comparison.categorical["variable"])  # nessuna categoria da testare


@pytest.mark.parametrize("label_1", [4, 9])
def test_the_frame_filled_with_a_single_cluster_is_refused(label_1):
    pair = _synthetic_pair(3, 3, seed=0, nan_rate=0.0)
    one_cluster = PairFrame(pair.frame.assign(cluster_label=label_1), [])
    with pytest.raises(ValueError, match="empty or is the whole frame"):
        pair_clinical_comparison(one_cluster, label_1)


# --- pair_frame sul registro ----------------------------------------------------------------------

_REGISTRY_NUMERIC = ["age", "education", "NIHSS", "lesion_volume_voxels_2mm", *[column for _n, _l, column in LOCATION_FRACTIONS]]


def _write_registry(root, subjects: list[str], seed: int, volume_cells: list[str] | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(subjects)
    registry = pd.DataFrame({
        "subject_id": subjects, "original_id": subjects, "dataset": rng.choice(["UNIPD/WashU", "UNIPD/PSP"], size=n),
        "disease_id": "ST", "has_lesion": "True", "has_sdc": "True", "has_features": "False",
        "sex": rng.choice(["F", "M", ""], size=n),  # "" = valore mancante nel registro
        "lesion_side": rng.choice(["left", "right"], size=n), "location_dominant_2mm": rng.choice(["cortex_only", "white"], size=n),
    })
    for column in _REGISTRY_NUMERIC:
        registry[column] = [f"{v:.3f}" for v in rng.uniform(0, 100, size=n)]
    if volume_cells is not None:
        registry["lesion_volume_voxels_2mm"] = volume_cells
    root.mkdir(exist_ok=True)
    registry.to_csv(root / "participants.csv", index=False)
    return registry


@st.composite
def _run_metadata(draw):
    """Soggetti 0..11 in un ordine casuale, ciascuno nel cluster 0/2/5 (non contigui); alcuni fuori registro."""
    order = draw(st.permutations(list(range(12))))
    labels = draw(st.lists(st.sampled_from([0, 2, 5]), min_size=12, max_size=12))
    missing = draw(st.sets(st.sampled_from(list(range(12))), max_size=4))
    return order, labels, missing


@given(_run_metadata())
def test_pair_frame_keeps_every_subject_of_the_two_clusters_and_reports_the_unregistered_ones_sorted(tmp_path_factory, monkeypatch, data):
    order, labels, missing = data
    root = tmp_path_factory.mktemp("meta")
    ids = [subject_id(i) for i in range(12)]
    _write_registry(root, [ids[i] for i in range(12) if i not in missing] or [ids[0]], seed=3)
    registered = {ids[i] for i in range(12) if i not in missing} or {ids[0]}
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    metadata = pd.DataFrame({"subject_id": [ids[i] for i in order], "cluster_label": [labels[i] for i in order]})
    present = set(labels)
    if not {0, 2} <= present:
        return

    result = pair_frame(metadata, 0, 2)
    chosen = metadata[metadata["cluster_label"].isin([0, 2])]
    assert result.frame["subject_id"].tolist() == chosen["subject_id"].tolist()  # nessun soggetto perso, ordine della run
    assert set(result.frame["cluster_label"]) == {0, 2}
    assert result.unregistered == sorted(set(chosen["subject_id"]) - registered)
    unregistered_rows = result.frame["subject_id"].isin(result.unregistered)
    assert result.frame.loc[unregistered_rows, _NUMERIC_COLUMNS].isna().all().all()  # lezione #38: fuori registro = mancante, non scartato
    assert result.frame.loc[~unregistered_rows, "age"].notna().all()


@settings(max_examples=25)
@given(st.permutations(list(range(12))))
def test_pair_frame_values_follow_the_subject_not_the_row_position(tmp_path_factory, monkeypatch, order):
    root = tmp_path_factory.mktemp("meta")
    ids = [subject_id(i) for i in range(12)]
    _write_registry(root, ids, seed=7)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    labels = [i % 2 for i in range(12)]
    straight = pair_frame(pd.DataFrame({"subject_id": ids, "cluster_label": labels}), 0, 1).frame.set_index("subject_id")
    shuffled = pair_frame(
        pd.DataFrame({"subject_id": [ids[i] for i in order], "cluster_label": [labels[i] for i in order]}), 0, 1
    ).frame.set_index("subject_id")
    pd.testing.assert_frame_equal(straight.sort_index(), shuffled.sort_index())


@given(st.lists(st.sampled_from(["", "nan", "abc", "0", "-5", "1", "250", "1e3"]), min_size=4, max_size=4))
def test_log_lesion_volume_is_defined_only_for_a_positive_numeric_volume(tmp_path_factory, monkeypatch, cells):
    root = tmp_path_factory.mktemp("meta")
    ids = [subject_id(i) for i in range(4)]
    _write_registry(root, ids, seed=1, volume_cells=cells)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    frame = pair_frame(pd.DataFrame({"subject_id": ids, "cluster_label": [0, 0, 1, 1]}), 0, 1).frame
    volume = pd.to_numeric(pd.Series(cells), errors="coerce")
    positive = (volume > 0).to_numpy()
    assert frame["log_lesion_volume"].notna().to_numpy().tolist() == positive.tolist()  # un volume 0 è mancante, non -inf
    assert not np.isinf(frame["log_lesion_volume"]).any()
    np.testing.assert_allclose(frame.loc[positive, "log_lesion_volume"], np.log10(volume[positive]))
    assert frame["lesion_volume_voxels"].isna().tolist() == volume.isna().tolist()


# --- centroid_separation e difference_image -------------------------------------------------------


@st.composite
def _embedding_with_labels(draw):
    n = draw(st.integers(4, 30))
    n_dims = draw(st.integers(1, 4))
    seed = draw(st.integers(0, 10_000))
    labels = draw(st.lists(st.sampled_from([-1, 0, 3, 8]), min_size=n, max_size=n))
    embedding = np.random.default_rng(seed).normal(size=(n, n_dims)) * 5
    return embedding, np.array(labels)


@given(_embedding_with_labels(), st.integers(0, 10_000))
def test_centroid_separation_is_symmetric_translation_invariant_and_row_order_free(data, seed):
    embedding, labels = data
    present = sorted(set(labels.tolist()))
    if len(present) < 2:
        return
    one, two = present[0], present[-1]
    metadata = pd.DataFrame({"subject_id": [subject_id(i) for i in range(len(labels))], "cluster_label": labels})

    forward = centroid_separation(embedding, metadata, one, two)
    backward = centroid_separation(embedding, metadata, two, one)
    assert forward.distance == pytest.approx(backward.distance, abs=1e-12)
    assert (forward.radius_1, forward.radius_2) == pytest.approx((backward.radius_2, backward.radius_1))
    assert forward.distance >= 0 and forward.radius_1 >= 0 and forward.radius_2 >= 0

    shifted = centroid_separation(embedding + np.arange(embedding.shape[1]) * 37.0, metadata, one, two)
    assert shifted.distance == pytest.approx(forward.distance, abs=1e-8)
    assert shifted.radius_1 == pytest.approx(forward.radius_1, abs=1e-8)

    order = np.random.default_rng(seed).permutation(len(labels))
    permuted = centroid_separation(embedding[order], metadata.iloc[order].reset_index(drop=True), one, two)
    assert permuted.distance == pytest.approx(forward.distance, abs=1e-10)
    assert permuted.radius_2 == pytest.approx(forward.radius_2, abs=1e-10)


@given(st.integers(1, 5), st.floats(0.1, 50, allow_nan=False))
def test_centroid_separation_of_two_point_clusters_is_their_distance_and_radii_zero(n_dims, gap):
    embedding = np.zeros((2, n_dims))
    embedding[1, 0] = gap
    metadata = pd.DataFrame({"subject_id": ["a", "b"], "cluster_label": [1, 2]})
    result = centroid_separation(embedding, metadata, 1, 2)
    assert result.distance == pytest.approx(gap)
    assert result.radius_1 == 0.0 and result.radius_2 == 0.0


def _image(seed: int, shape=(3, 4, 2)) -> nib.Nifti1Image:
    return nib.Nifti1Image(np.random.default_rng(seed).normal(size=shape).astype(np.float32), np.diag([2.0, 2.0, 2.0, 1.0]))


@given(st.integers(0, 1000), st.integers(0, 1000), st.integers(0, 1000))
def test_difference_image_is_antisymmetric_telescopic_and_zero_on_itself(seed_a, seed_b, seed_c):
    a, b, c = _image(seed_a), _image(seed_b), _image(seed_c)
    ab = difference_image(a, b).get_fdata()
    np.testing.assert_allclose(ab, -difference_image(b, a).get_fdata(), atol=1e-6)
    np.testing.assert_allclose(ab + difference_image(b, c).get_fdata(), difference_image(a, c).get_fdata(), atol=1e-5)
    assert not difference_image(a, a).get_fdata().any()
    assert np.allclose(difference_image(a, b).affine, a.affine)


@pytest.mark.parametrize("shape_2, scale", [((3, 4, 3), 2.0), ((3, 4, 2), 2.0001), ((3, 4, 2), 1.0)])
def test_difference_image_refuses_any_grid_that_is_not_the_same(shape_2, scale):
    image_2 = nib.Nifti1Image(np.zeros(shape_2, dtype=np.float32), np.diag([scale, scale, scale, 1.0]))
    with pytest.raises(ValueError, match="not on the same grid"):
        difference_image(_image(0), image_2)
