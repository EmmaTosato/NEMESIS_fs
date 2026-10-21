"""Test a proprietà di `src/features/sdc.py`: mappe di disconnessione continue su tre header diversi
(lesson #40), validazione delle probabilita', correzione fuori-cervello (massa rimossa), matrice a due
passate contro un oracolo numpy, CSV delle streamline, accordo registro/disco.

Le NIfTI sono 8x8x8 a 2 mm con origine -7 mm (nessun voxel sulla mediana). Le mappe non toccano x = 0
dell'array, perche' l'header "shift" non puo' rappresentare quel voxel.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.features.lesion import LesionGrid
from src.features.parcellated_csv import BCBTOOLKIT_DIR
from src.features.sdc import (
    _check_registry_agrees_with_disk,
    _disconnectome_values,
    _disconnection_grid_context,
    _disconnection_load,
    _load_and_validate_streamline_csv,
    _needs_resample,
    _stack_streamline_matrix,
    _stack_voxelwise_matrix,
    _zero_out_of_brain,
    compute_sdc_metadata,
)
from src.utils import participants as participants_registry

SHAPE = (8, 8, 8)
N_VOXELS = int(np.prod(SHAPE))
AFFINE = np.diag([2.0, 2.0, 2.0, 1.0])
AFFINE[:3, 3] = -7.0
DATASET = "siteA"
GLOB = f"{BCBTOOLKIT_DIR}/*/*_res-1_desc-disconnectome.nii.gz"

voxel = st.tuples(st.integers(1, 7), st.integers(0, 7), st.integers(0, 7))
probability = st.floats(0.0, 1.0, width=32)
# Pochi livelli: rende frequenti i voxel costanti tra soggetti, che e' il caso interessante della matrice.
level = st.sampled_from([0.0, 0.25, 0.5, 1.0])
prob_maps = st.dictionaries(voxel, probability, max_size=40)
level_maps = st.dictionaries(voxel, level, max_size=40)
brains = st.sets(voxel, min_size=40, max_size=300)


def to_volume(values: dict) -> np.ndarray:
    volume = np.zeros(SHAPE, dtype=np.float32)
    for v, value in values.items():
        volume[v] = value
    return volume


def header_variants(volume: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    las = AFFINE @ np.array([[-1.0, 0, 0, SHAPE[0] - 1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    shifted = AFFINE.copy()
    shifted[0, 3] += AFFINE[0, 0]
    shifted_volume = np.zeros_like(volume)
    shifted_volume[:-1] = volume[1:]
    return {"ras_same_grid": (volume, AFFINE), "las_flipped": (np.ascontiguousarray(volume[::-1]), las), "ras_shifted": (shifted_volume, shifted)}


def save(path: Path, data: np.ndarray, affine: np.ndarray = AFFINE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(data, affine), path)
    return path


def reference_image() -> nib.Nifti1Image:
    return nib.Nifti1Image(np.zeros(SHAPE, np.float32), AFFINE)


def grid_in(root: Path, brain: set | None = None) -> LesionGrid:
    template = save(root / "tpl.nii.gz", np.zeros(SHAPE, np.float32))
    brain_volume = np.ones(SHAPE, np.float32) if brain is None else to_volume({v: 1.0 for v in brain})
    return LesionGrid("g", template, save(root / "brain.nii.gz", brain_volume))


def sid(i: int) -> str:
    return f"sub-STUNIPD{i:04d}"


# --- _disconnectome_values: stessi valori fisici, tre header -----------------------------------


@given(values=prob_maps)
@settings(max_examples=25)
def test_the_three_headers_give_the_same_resampled_values(values):
    reference = to_volume(values).ravel()
    with tempfile.TemporaryDirectory() as tmp:
        for name, (data, affine) in header_variants(to_volume(values)).items():
            img = nib.load(save(Path(tmp) / f"{name}.nii.gz", data, affine))
            assert np.array_equal(_disconnectome_values(img, reference_image(), "nearest"), reference), name


def test_the_variants_are_distinguishable_without_resampling():
    """Guardia: se i tre array grezzi coincidessero, un 'nessun resampling' passerebbe comunque."""
    variants = header_variants(to_volume({(2, 1, 1): 0.5}))
    assert len({tuple(np.flatnonzero(d)) for d, _ in variants.values()}) == 3
    for name, (data, affine) in variants.items():
        assert nib.Nifti1Image(data, affine).shape == SHAPE
        assert _needs_resample(nib.Nifti1Image(data, affine), reference_image()) == (name != "ras_same_grid")


@given(values=prob_maps)
def test_values_are_float32_flat_and_never_binarized(values):
    flat = _disconnectome_values(nib.Nifti1Image(to_volume(values), AFFINE), reference_image(), "nearest")
    assert flat.dtype == np.float32 and flat.shape == (N_VOXELS,)
    assert set(np.unique(flat)) <= {0.0, *map(np.float32, values.values())}


# --- carico di disconnessione ----------------------------------------------------------------


@given(values=prob_maps, brain=brains)
@settings(max_examples=25)
def test_load_is_the_in_brain_sum_identical_on_every_header_and_blind_to_out_of_brain_mass(values, brain):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        context = _disconnection_grid_context(grid_in(root, brain))
        inside = np.zeros(SHAPE, bool)
        for v in brain:
            inside[v] = True
        expected = float(to_volume(values)[inside].sum(dtype=np.float64))
        for name, (data, affine) in header_variants(to_volume(values)).items():
            path = save(root / f"{name}.nii.gz", data, affine)
            load = _disconnection_load(nib.load(path), path, context, "nearest")
            assert load == pytest.approx(expected, rel=1e-12, abs=1e-12), name
        assert 0.0 <= load <= len(brain)
        # Aggiungere massa FUORI dal cervello non cambia il carico.
        polluted = to_volume(values)
        polluted[~inside] = 1.0
        polluted_path = save(root / "polluted.nii.gz", polluted)
        assert _disconnection_load(nib.load(polluted_path), polluted_path, context, "nearest") == pytest.approx(expected, rel=1e-12, abs=1e-12)
    assert context.n_brain_voxels == len(brain)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf, -1e-6, -0.5, 1.001, 2.0])
def test_values_that_are_not_a_unit_probability_raise(bad):
    volume = np.zeros(SHAPE, np.float32)
    volume[3, 3, 3] = bad
    with tempfile.TemporaryDirectory() as tmp:
        context = _disconnection_grid_context(grid_in(Path(tmp)))
        path = save(Path(tmp) / "m.nii.gz", volume)
        with pytest.raises(ValueError, match="probability"):
            _disconnection_load(nib.load(path), path, context, "nearest")


@pytest.mark.parametrize("ok", [0.0, 1.0, 0.5, 1.00005])
def test_values_inside_the_probability_range_and_the_float_slack_are_accepted(ok):
    volume = np.zeros(SHAPE, np.float32)
    volume[3, 3, 3] = ok
    with tempfile.TemporaryDirectory() as tmp:
        context = _disconnection_grid_context(grid_in(Path(tmp)))
        path = save(Path(tmp) / "m.nii.gz", volume)
        assert _disconnection_load(nib.load(path), path, context, "nearest") == pytest.approx(float(np.float32(ok)))


def test_an_empty_brain_mask_raises_instead_of_dividing_by_zero():
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match="no voxel"):
        _disconnection_grid_context(grid_in(Path(tmp), brain=set()))


# --- correzione fuori-cervello: massa rimossa ------------------------------------------------


@given(values=prob_maps, brain=brains)
def test_zeroing_outside_the_brain_reports_the_voxels_and_the_mass_it_removed(values, brain):
    flat = to_volume(values).ravel()
    inside = to_volume({v: 1.0 for v in brain}).ravel() > 0
    corrected, n_voxels, mass_removed = _zero_out_of_brain(flat, inside, Path("m.nii.gz"))
    assert np.array_equal(corrected[inside], flat[inside]) and not corrected[~inside].any()
    assert n_voxels == int((flat[~inside] != 0).sum())
    assert 0.0 <= mass_removed <= 1.0
    if n_voxels:
        assert mass_removed == pytest.approx(float(flat[~inside].sum(dtype=np.float64) / flat.sum(dtype=np.float64)))
    else:
        assert mass_removed == 0.0
    assert flat.sum(dtype=np.float64) == pytest.approx(float(corrected.sum(dtype=np.float64)) + mass_removed * float(flat.sum(dtype=np.float64)))


@pytest.mark.parametrize("bad", [np.nan, -0.1, np.inf])
def test_zeroing_refuses_a_field_whose_mass_is_undefined(bad):
    flat = np.zeros(N_VOXELS, np.float32)
    flat[0] = bad
    with pytest.raises(ValueError, match="finite, non-negative"):
        _zero_out_of_brain(flat, np.ones(N_VOXELS, bool), Path("m.nii.gz"))


# --- matrice voxelwise: oracolo numpy ---------------------------------------------------------


def _stack(root: Path, maps: list[dict], *, brain: set | None, headers: list[str]):
    paths = {}
    for i, values in enumerate(maps):
        data, affine = header_variants(to_volume(values))[headers[i % len(headers)]]
        paths[(DATASET, sid(i))] = save(root / f"{i}.nii.gz", data, affine)
    brain_mask = None if brain is None else (to_volume({v: 1.0 for v in brain}).ravel() > 0)
    return _stack_voxelwise_matrix(paths, reference_image(), "nearest", brain_mask)


@given(maps=st.lists(level_maps, min_size=2, max_size=4), brain=st.one_of(st.none(), brains), headers=st.lists(st.sampled_from(["ras_same_grid", "las_flipped", "ras_shifted"]), min_size=1, max_size=4))
@settings(max_examples=25)
def test_two_pass_matrix_equals_stack_mask_then_drop_constant_columns_on_any_headers(maps, brain, headers):
    with tempfile.TemporaryDirectory() as tmp:
        X, metadata, non_constant, corrected = _stack(Path(tmp), maps, brain=brain, headers=headers)
    stacked = np.stack([to_volume(m).ravel() for m in maps])
    if brain is not None:
        inside = to_volume({v: 1.0 for v in brain}).ravel() > 0
        removed = stacked[:, ~inside].sum(axis=1, dtype=np.float64)
        stacked = np.where(inside[None, :], stacked, 0.0).astype(np.float32)
    expected_mask = stacked.min(axis=0) != stacked.max(axis=0)
    assert np.array_equal(non_constant, expected_mask)
    assert np.array_equal(X, stacked[:, expected_mask]) and X.dtype == np.float32
    assert metadata["subject_id"].tolist() == [sid(i) for i in range(len(maps))]
    if brain is None:
        assert corrected == []
    else:
        originals = [to_volume(m).ravel() for m in maps]
        assert [c[0] for c in corrected] == [sid(i) for i, o in enumerate(originals) if (o[~inside] != 0).any()]
        assert all(0.0 < c[2] <= 1.0 and c[1] > 0 for c in corrected)


@given(maps=st.lists(level_maps, min_size=2, max_size=3))
@settings(max_examples=25)
def test_a_column_constant_across_subjects_is_dropped_whatever_its_value(maps):
    constant = {(4, 4, 4): 0.5}
    with tempfile.TemporaryDirectory() as tmp:
        X, _, non_constant, _ = _stack(Path(tmp), [{**m, **constant} for m in maps], brain=None, headers=["ras_same_grid"])
    assert not non_constant[np.ravel_multi_index((4, 4, 4), SHAPE)]
    assert not (X == 0.5).all(axis=0).any()


def test_a_nan_voxel_is_kept_as_a_column_never_dropped_as_constant():
    nan_volume = np.zeros(SHAPE, np.float32)
    nan_volume[2, 2, 2] = np.nan
    with tempfile.TemporaryDirectory() as tmp:
        paths = {(DATASET, sid(i)): save(Path(tmp) / f"{i}.nii.gz", nan_volume) for i in range(2)}
        X, _, non_constant, _ = _stack_voxelwise_matrix(paths, reference_image(), "nearest", None)
    assert non_constant.sum() == 1 and np.isnan(X).all()


def test_no_maps_at_all_cannot_define_the_constant_columns():
    with pytest.raises(ValueError, match="no disconnectome maps"):
        _stack_voxelwise_matrix({}, reference_image(), "nearest", None)


# --- CSV delle streamline --------------------------------------------------------------------

TRACTS = np.array(sorted(["AF_L", "AF_R", "CC_body", "CST_L", "CST_R", "MCP"]))


def _write_streamline_csv(path: Path, tracts, ratios) -> Path:
    pd.DataFrame({"tract": tracts, "streamline_ratio": ratios}).to_csv(path, index=False)
    return path


@given(ratios=st.lists(st.floats(0, 1), min_size=len(TRACTS), max_size=len(TRACTS)), data=st.data())
def test_streamline_vector_is_aligned_by_tract_name_whatever_the_row_order(ratios, data):
    order = data.draw(st.permutations(range(len(TRACTS))))
    with tempfile.TemporaryDirectory() as tmp:
        series = _load_and_validate_streamline_csv(_write_streamline_csv(Path(tmp) / "s.csv", TRACTS[list(order)], np.array(ratios)[list(order)]), TRACTS)
    X, metadata = _stack_streamline_matrix({(DATASET, sid(0)): series}, TRACTS)
    assert np.allclose(X[0], ratios) and metadata["subject_id"].tolist() == [sid(0)]


@given(drop=st.integers(0, len(TRACTS) - 1))
def test_a_missing_tract_raises_instead_of_being_filled_with_zero(drop):
    keep = [t for i, t in enumerate(TRACTS) if i != drop]
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match=TRACTS[drop]):
        _load_and_validate_streamline_csv(_write_streamline_csv(Path(tmp) / "s.csv", keep, [0.1] * len(keep)), TRACTS)


@given(dup=st.integers(0, len(TRACTS) - 1))
def test_a_duplicated_tract_raises(dup):
    tracts = [*TRACTS, TRACTS[dup]]
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match="duplicate"):
        _load_and_validate_streamline_csv(_write_streamline_csv(Path(tmp) / "s.csv", tracts, [0.1] * len(tracts)), TRACTS)


@given(name=st.text("abcdefXYZ_0123", min_size=1, max_size=8))
def test_a_tract_outside_the_reference_raises(name):
    assume(name not in set(TRACTS))
    tracts = [*TRACTS, name]
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match="not in the reference"):
        _load_and_validate_streamline_csv(_write_streamline_csv(Path(tmp) / "s.csv", tracts, [0.1] * len(tracts)), TRACTS)


@pytest.mark.parametrize("columns", [["tract"], ["streamline_ratio"], ["region_name", "streamline_ratio"]])
def test_a_streamline_csv_with_the_wrong_columns_raises(columns):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.csv"
        pd.DataFrame({c: list(TRACTS) if c != "streamline_ratio" else [0.1] * len(TRACTS) for c in columns}).to_csv(path, index=False)
        with pytest.raises(ValueError, match="missing"):
            _load_and_validate_streamline_csv(path, TRACTS)


@pytest.mark.parametrize("bad", ["abc", "", "inf", "-3"])
def test_a_streamline_ratio_that_is_not_a_finite_proportion_is_rejected(bad):
    with tempfile.TemporaryDirectory() as tmp:
        ratios = ["0.1"] * (len(TRACTS) - 1) + [bad]
        try:
            series = _load_and_validate_streamline_csv(_write_streamline_csv(Path(tmp) / "s.csv", TRACTS, ratios), TRACTS)
        except ValueError:
            return
    X, _ = _stack_streamline_matrix({(DATASET, sid(0)): series}, TRACTS)
    assert X.dtype.kind == "f" and np.isfinite(X).all() and (X >= 0).all()


# --- accordo registro/disco -------------------------------------------------------------------


@given(flagged=st.sets(st.integers(0, 6)), on_disk=st.sets(st.integers(0, 6)))
def test_registry_and_disk_agree_iff_the_two_subject_sets_are_equal_and_the_error_names_the_difference(flagged, on_disk):
    registered = {DATASET: [sid(i) for i in sorted(flagged)]}
    files = {DATASET: {sid(i): Path(f"{sid(i)}.nii.gz") for i in on_disk}}
    if flagged == on_disk:
        _check_registry_agrees_with_disk(registered, files, GLOB)
        return
    with pytest.raises(ValueError, match="disagree") as excinfo:
        _check_registry_agrees_with_disk(registered, files, GLOB)
    message = str(excinfo.value)
    # Il messaggio riporta al massimo 5 esempi per lato: i primi 5 (ordinati) di ogni differenza ci sono sempre.
    assert all(sid(i) in message for i in sorted(flagged - on_disk)[:5] + sorted(on_disk - flagged)[:5])
    assert ("flagged" in message and "have no" in message) == bool(flagged - on_disk)


@given(two=st.permutations([0, 1]))
def test_every_disagreeing_dataset_is_reported_in_the_same_error(two):
    registered = {f"site{i}": [sid(i)] for i in two}
    with pytest.raises(ValueError) as excinfo:
        _check_registry_agrees_with_disk(registered, {f"site{i}": {} for i in two}, GLOB)
    assert all(f"site{i}" in str(excinfo.value) for i in two)


# --- compute_sdc_metadata end-to-end -----------------------------------------------------------

REGISTRY_HEADER = "subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features\n"


def _register(metadata_root: Path, rows: list[tuple[str, bool]]) -> None:
    metadata_root.mkdir(parents=True, exist_ok=True)
    (metadata_root / "participants.csv").write_text(
        REGISTRY_HEADER + "".join(f"{s},{s},{DATASET},ST,True,{flag},False\n" for s, flag in rows)
    )


def _write_map(root: Path, subject: str, data: np.ndarray, affine: np.ndarray) -> None:
    save(root / "data" / DATASET / "bcbtoolkit" / subject / f"{subject}_res-1_desc-disconnectome.nii.gz", data, affine)


@given(values=prob_maps, brain=brains)
@settings(max_examples=15)
def test_metadata_row_is_the_same_for_the_same_content_stored_under_each_header(values, brain):
    names = list(header_variants(to_volume(values)))
    with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as patch:
        root = Path(tmp)
        patch.setattr(participants_registry, "METADATA_ROOT", root / "metadata")
        _register(root / "metadata", [(sid(i), True) for i in range(3)])
        for i, name in enumerate(names):
            data, affine = header_variants(to_volume(values))[name]
            _write_map(root, sid(i), data, affine)
        metadata, excluded = compute_sdc_metadata(root / "data", [DATASET], GLOB, "nearest", None, [grid_in(root, brain)])
    loads = metadata["disconnection_load_voxels_g"].tolist()
    assert len(set(loads)) == 1 and excluded == []
    assert metadata["disconnection_mean_g"].tolist() == pytest.approx([loads[0] / len(brain)] * 3)
    assert (metadata["disconnection_mean_g"] <= 1.0).all()


@given(healthy=st.sets(st.integers(10, 15), min_size=1, max_size=3))
@settings(max_examples=15)
def test_group_filter_removes_controls_from_both_sides_of_the_registry_disk_comparison(healthy):
    with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as patch:
        root = Path(tmp)
        patch.setattr(participants_registry, "METADATA_ROOT", root / "metadata")
        controls = [f"sub-STUNIPDHC{i:04d}" for i in sorted(healthy)]
        _register(root / "metadata", [(sid(0), True), *[(c, True) for c in controls]])
        for subject in (sid(0), *controls):
            _write_map(root, subject, to_volume({(2, 2, 2): 0.5}), AFFINE)
        metadata, excluded = compute_sdc_metadata(root / "data", [DATASET], GLOB, "nearest", ["ST"], [grid_in(root)])
    assert metadata["subject_id"].tolist() == [sid(0)]
    assert excluded == sorted(controls)
