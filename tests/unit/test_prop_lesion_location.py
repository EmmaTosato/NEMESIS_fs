"""Test a proprietà di `src/features/lesion_location.py`: frazioni che sommano a 1, dominante con
spareggio deterministico, mappa delle categorie contro un oracolo per voxel (precedenza), atlanti
accettati solo se sono una mappa intera di voxel sulla griglia (lesson #40), parser dell'XML.

Atlanti sintetici LAS su griglia RAS 8x8x8 a 2 mm (`tests/unit/location_fixtures.py`); i voxel dei
test evitano la fetta superiore (z = 7), riservata ai voxel di "completamento" delle etichette.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.features.lesion_location import (
    LOCATION_CATEGORIES,
    LesionAtlas,
    _check_integer_voxel_map,
    _read_labels,
    build_location_categories,
    location_columns,
    location_metrics,
)
from tests.unit.location_fixtures import make_location_spec

SHAPE = (8, 8, 8)
AFFINE = np.diag([2.0, 2.0, 2.0, 1.0])
AFFINE[:3, 3] = -7.0
N = int(np.prod(SHAPE))
voxel = st.tuples(st.integers(0, 7), st.integers(0, 7), st.integers(0, 6))
categories_array = st.lists(st.integers(0, len(LOCATION_CATEGORIES)), min_size=1, max_size=60).map(lambda v: np.array(v, dtype=np.uint8))


def reference() -> nib.Nifti1Image:
    return nib.Nifti1Image(np.zeros(SHAPE, np.float32), AFFINE)


def raveled(voxels) -> np.ndarray:
    volume = np.zeros(SHAPE, bool)
    for v in voxels:
        volume[v] = True
    return volume.ravel()


# --- location_metrics (puro) --------------------------------------------------------------------


@given(categories=categories_array, data=st.data())
def test_fractions_sum_to_one_over_the_in_brain_lesion_and_the_dominant_is_the_first_maximum(categories, data):
    lesion = np.array(data.draw(st.lists(st.booleans(), min_size=len(categories), max_size=len(categories))))
    metrics = location_metrics(lesion, categories, "g")
    counts = np.bincount(categories[lesion], minlength=len(LOCATION_CATEGORIES) + 1)[1:]
    assert list(metrics) == location_columns("g")
    if counts.sum() == 0:
        assert all(np.isnan(v) for v in metrics.values())
        return
    fractions = [metrics[f"location_{c}_g"] for c in LOCATION_CATEGORIES]
    assert sum(fractions) == pytest.approx(1.0) and all(0.0 <= f <= 1.0 for f in fractions)
    assert fractions == pytest.approx((counts / counts.sum()).tolist())
    best = max(counts)
    assert metrics["location_dominant_g"] == next(c for c, n in zip(LOCATION_CATEGORIES, counts) if n == best)


@given(categories=categories_array, outside=st.integers(0, 40))
def test_lesion_voxels_outside_the_brain_never_enter_the_denominator(categories, outside):
    inside_lesion = np.ones(len(categories), bool)
    base = location_metrics(inside_lesion, categories, "g")
    padded_categories = np.concatenate([categories, np.zeros(outside, np.uint8)])
    padded = location_metrics(np.concatenate([inside_lesion, np.ones(outside, bool)]), padded_categories, "g")
    assert base.keys() == padded.keys()
    for key in base:
        if isinstance(base[key], float) and np.isnan(base[key]):
            assert np.isnan(padded[key])
        else:
            assert padded[key] == base[key]


@pytest.mark.parametrize("tied", [(0, 1), (2, 5), (6, 3), (0, 6)])
def test_an_exact_tie_goes_to_the_category_earlier_in_the_precedence_order(tied):
    categories = np.array([tied[0] + 1, tied[1] + 1], dtype=np.uint8)
    for order in (categories, categories[::-1].copy()):  # l'ordine dei voxel non conta
        assert location_metrics(np.ones(2, bool), order, "g")["location_dominant_g"] == LOCATION_CATEGORIES[min(tied)]


@given(n_lesion=st.integers(1, 30), n_categories=st.integers(1, 30))
def test_a_shape_mismatch_between_lesion_and_category_map_raises(n_lesion, n_categories):
    assume(n_lesion != n_categories)
    with pytest.raises(ValueError, match="voxels"):
        location_metrics(np.ones(n_lesion, bool), np.ones(n_categories, np.uint8), "g")


# --- mappa delle categorie contro un oracolo per voxel -------------------------------------------


def oracle(cortex, cerebellum, subcortical, brain) -> np.ndarray:
    out = np.zeros(N, np.uint8)
    value = {name: i for i, name in enumerate(LOCATION_CATEGORIES, start=1)}
    for v in np.flatnonzero(brain):
        index = np.unravel_index(v, SHAPE)
        kind = subcortical.get(index)
        in_cortex, in_cerebellum = index in cortex, index in cerebellum
        if kind == "stem" or in_cerebellum:
            out[v] = value["infratentorial"]
        elif kind == "gray":
            out[v] = value["subcortical_gray"]
        elif in_cortex and kind == "white":
            out[v] = value["cortex_white_boundary"]
        elif in_cortex:
            out[v] = value["cortex_only"]
        elif kind == "white":
            out[v] = value["white_matter_only"]
        elif kind == "ventricle":
            out[v] = value["ventricle"]
        else:
            out[v] = value["unlabeled"]
    return out


@given(
    cortex=st.sets(voxel, max_size=40),
    cerebellum=st.sets(voxel, max_size=20),
    subcortical=st.dictionaries(voxel, st.sampled_from(["white", "gray", "stem", "ventricle"]), max_size=40),
    brain=st.sets(voxel, min_size=100, max_size=400),
    data=st.data(),
)
@settings(max_examples=20)
def test_category_map_follows_the_precedence_rules_voxel_by_voxel(cortex, cerebellum, subcortical, brain, data):
    # I tre atlanti si sovrappongono davvero solo se lo forziamo: i voxel dell'atlante sottocorticale
    # vengono copiati (a caso) negli altri due, cosi' ogni coppia di categorie si contende dei voxel.
    shared = sorted(subcortical)
    if shared:
        cortex = cortex | data.draw(st.sets(st.sampled_from(shared)))
        cerebellum = cerebellum | data.draw(st.sets(st.sampled_from(shared)))
    brain = brain | set(shared)
    with tempfile.TemporaryDirectory() as tmp:
        spec = make_location_spec(
            Path(tmp), SHAPE, AFFINE, "g", cortex=cortex, cerebellum=cerebellum,
            white=[v for v, k in subcortical.items() if k == "white"], gray=[v for v, k in subcortical.items() if k == "gray"],
            stem=[v for v, k in subcortical.items() if k == "stem"], ventricle=[v for v, k in subcortical.items() if k == "ventricle"],
        )
        categories = build_location_categories(spec, reference(), raveled(brain))
    assert categories.dtype == np.uint8 and categories.shape == (N,)
    # Fuori dalla fetta di completamento (z = 7) la mappa e' quella dell'oracolo; fuori dal cervello e' 0.
    z = np.unravel_index(np.arange(N), SHAPE)[2]
    usable = z < 7
    assert np.array_equal(categories[usable], oracle(cortex, cerebellum, subcortical, raveled(brain))[usable])
    assert not categories[~raveled(brain)].any()


def test_a_brain_mask_of_the_wrong_size_raises():
    with tempfile.TemporaryDirectory() as tmp:
        spec = make_location_spec(Path(tmp), SHAPE, AFFINE, "g")
        with pytest.raises(ValueError, match="raveled brain mask"):
            build_location_categories(spec, reference(), np.ones(N - 1, bool))


# --- l'atlante deve essere una mappa intera di voxel ------------------------------------------------


def _atlas_image(affine: np.ndarray, shape=SHAPE) -> nib.Nifti1Image:
    return nib.Nifti1Image(np.zeros(shape, np.float32), affine)


@given(shift=st.tuples(st.integers(-5, 5), st.integers(-5, 5), st.integers(-5, 5)), flip_x=st.booleans(), swap_xy=st.booleans())
def test_integer_voxel_shifts_flips_and_axis_swaps_are_accepted(shift, flip_x, swap_xy):
    affine = AFFINE.copy()
    linear = np.diag([-1.0 if flip_x else 1.0, 1.0, 1.0])
    if swap_xy:
        linear = linear @ np.array([[0.0, 1, 0], [1, 0, 0], [0, 0, 1]])
    affine[:3, :3] = AFFINE[:3, :3] @ linear
    affine[:3, 3] = AFFINE[:3, 3] + AFFINE[:3, :3] @ np.array(shift, float)
    _check_integer_voxel_map(_atlas_image(affine), reference(), "x")


@given(fraction=st.floats(0.01, 0.99).filter(lambda f: abs(f - round(f)) > 5e-3), axis=st.integers(0, 2))
def test_a_fractional_voxel_offset_is_rejected(fraction, axis):
    affine = AFFINE.copy()
    affine[axis, 3] += AFFINE[axis, axis] * fraction
    with pytest.raises(ValueError, match="not an exact integer voxel map"):
        _check_integer_voxel_map(_atlas_image(affine), reference(), "x")


@pytest.mark.parametrize("name, mutate", [
    ("double-resolution", lambda a: a.__setitem__((0, 0), 4.0)),
    ("rotated-45deg", lambda a: a.__setitem__((slice(0, 2), slice(0, 2)), 2.0 * np.array([[1, -1], [1, 1]]) / np.sqrt(2))),
    ("shear", lambda a: a.__setitem__((0, 1), 1.0)),
])
def test_a_non_signed_permutation_linear_part_is_rejected(name, mutate):
    affine = AFFINE.copy()
    mutate(affine)
    with pytest.raises(ValueError, match="not an exact integer voxel map"):
        _check_integer_voxel_map(_atlas_image(affine), reference(), "x")


@given(shape=st.tuples(st.integers(2, 9), st.integers(2, 9), st.integers(2, 9)))
def test_an_atlas_on_another_shape_is_rejected_even_with_the_same_affine(shape):
    assume(shape != SHAPE)
    with pytest.raises(ValueError, match="shape"):
        _check_integer_voxel_map(_atlas_image(AFFINE, shape), reference(), "x")


# --- parser dell'XML --------------------------------------------------------------------------------


def _xml(entries: list[tuple[int, str]]) -> str:
    return '<?xml version="1.0"?><atlas><data>' + "".join(f'<label index="{i}" x="0" y="0" z="0">{name}</label>' for i, name in entries) + "</data></atlas>"


@given(entries=st.dictionaries(st.integers(0, 60), st.text("abcdefXYZ -", min_size=1, max_size=12).filter(lambda s: s.strip()), min_size=1, max_size=10))
def test_xml_labels_are_keyed_by_index_plus_one_with_the_text_stripped(entries):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "a.xml"
        path.write_text(_xml(list(entries.items())))
        labels = _read_labels(path)
    assert labels == {i + 1: name.strip() for i, name in entries.items()}
    assert 0 not in labels  # 0 e' "nessuna etichetta"


@given(index=st.integers(0, 30))
def test_a_repeated_label_index_raises(index):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "a.xml"
        path.write_text(_xml([(index, "A"), (index, "B")]))
        with pytest.raises(ValueError, match="appears twice"):
            _read_labels(path)


@pytest.mark.parametrize("content, exception", [("<atlas><data></data></atlas>", ValueError), ("<atlas><data><label", ValueError), ("", ValueError)])
def test_an_xml_without_labels_or_unparsable_raises(content, exception):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "a.xml"
        path.write_text(content)
        with pytest.raises(exception):
            _read_labels(path)


def test_a_missing_labels_file_or_atlas_image_raises():
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(FileNotFoundError):
            _read_labels(Path(tmp) / "absent.xml")
        spec = make_location_spec(Path(tmp), SHAPE, AFFINE, "g")
        missing = LesionAtlas(Path(tmp) / "absent.nii.gz", spec.cortical.labels_path)
        broken = type(spec)(spec.grid, missing, spec.subcortical, spec.cerebellum)
        with pytest.raises(FileNotFoundError, match="atlas image"):
            build_location_categories(broken, reference(), np.ones(N, bool))
