"""Test a proprietà di `src/features/lesion.py`: binarizzazione, riga di matrice = maschera appiattita,
invarianza rispetto ai tre header delle maschere (LAS +90 / RAS -90 / RAS -91, lesson #40: stessa
shape NON vuol dire stessa griglia), laterality, correzione fuori-cervello, `compute_lesion_metadata`.

Le NIfTI sono minuscole (8x8x8, voxel da 2 mm). L'origine in x e' -7 mm, quindi nessun voxel cade sulla
linea mediana (world x = 2i - 7 e' sempre dispari). Per simulare i tre header sullo stesso contenuto
fisico servono maschere che non tocchino x = 0 (l'header "shift" non puo' rappresentarlo).
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

from src.features.lesion import (
    LesionGrid,
    _drop_constant_features,
    _hemisphere_masks,
    _laterality_index,
    _load_and_binarize_lesion,
    _needs_resample,
    _out_of_brain_fraction,
    build_lesion_matrix,
    compute_lesion_metadata,
    lesion_side_from_laterality_index,
    load_brain_mask,
    validate_lesion_grids,
)
from src.features.lesion_correction import zero_out_of_brain_voxels
from tests.unit.location_fixtures import make_location_spec

SHAPE = (8, 8, 8)
N_VOXELS = int(np.prod(SHAPE))
AFFINE = np.diag([2.0, 2.0, 2.0, 1.0])
AFFINE[:3, 3] = -7.0
GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"
DATASET = "siteA"

# x >= 1: l'header "shift" (un voxel di scarto in x) non puo' rappresentare il voxel x = 0.
voxel = st.tuples(st.integers(1, 7), st.integers(0, 7), st.integers(0, 6))
any_voxel = st.tuples(st.integers(0, 7), st.integers(0, 7), st.integers(0, 7))
voxel_sets = st.sets(voxel, max_size=40)


def to_volume(voxels, dtype=np.float32) -> np.ndarray:
    volume = np.zeros(SHAPE, dtype=dtype)
    for v in voxels:
        volume[v] = 1
    return volume


def header_variants(volume: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Lo stesso contenuto fisico (volume sulla griglia di riferimento) scritto con i tre header veri."""
    nx = volume.shape[0]
    las = AFFINE @ np.array([[-1.0, 0, 0, nx - 1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    shifted = AFFINE.copy()
    shifted[0, 3] += AFFINE[0, 0]  # il voxel j del file e' il voxel j+1 del riferimento
    shifted_volume = np.zeros_like(volume)
    shifted_volume[:-1] = volume[1:]
    return {"ras_same_grid": (volume, AFFINE), "las_flipped": (np.ascontiguousarray(volume[::-1]), las), "ras_shifted": (shifted_volume, shifted)}


def save(path: Path, data: np.ndarray, affine: np.ndarray = AFFINE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(data, affine), path)
    return path


def reference_image() -> nib.Nifti1Image:
    return nib.Nifti1Image(np.zeros(SHAPE, dtype=np.float32), AFFINE)


def write_subject(root: Path, sid: str, data: np.ndarray, affine: np.ndarray = AFFINE) -> Path:
    return save(root / "data" / DATASET / "manual_masks" / sid / "anat" / f"{sid}_label-lesion_mask.nii.gz", data, affine)


def build(root: Path, **overrides):
    kwargs = dict(
        data_root=root / "data", datasets=[DATASET], reference_template_path=save(root / "ref.nii.gz", np.zeros(SHAPE, np.float32)),
        lesion_glob=GLOB, binarize_threshold=0.5, resample_interpolation="nearest", group_filter=None,
        excluded_subjects=frozenset(), correct_out_of_brain=False, brain_mask_path=None,
    )
    kwargs.update(overrides)
    return build_lesion_matrix(**kwargs)


def assert_matrix_is(X: np.ndarray, non_constant_mask: np.ndarray, rows: list[np.ndarray]) -> None:
    """X e' le righe attese senza le colonne costanti, e la maschera dice esattamente quali sono."""
    expected = np.stack(rows).astype(np.uint8)
    assert np.array_equal(non_constant_mask, expected.min(axis=0) != expected.max(axis=0))
    assert np.array_equal(X, expected[:, non_constant_mask])


def sid(i: int) -> str:
    return f"sub-STUNIPD{i:04d}"


# --- _needs_resample: shape uguale non e' griglia uguale --------------------------------------


@pytest.mark.parametrize("variant", ["las_flipped", "ras_shifted"])
def test_same_shape_but_another_header_needs_resampling(variant):
    data, affine = header_variants(to_volume({(3, 3, 3)}))[variant]
    img = nib.Nifti1Image(data, affine)
    assert img.shape == reference_image().shape
    assert _needs_resample(img, reference_image())


def test_the_reference_header_itself_never_needs_resampling():
    assert not _needs_resample(reference_image(), reference_image())


@given(offset=st.one_of(st.floats(-5e-4, 5e-4), st.floats(5e-3, 3.0), st.floats(-3.0, -5e-3)))
def test_needs_resample_has_a_sub_micron_tolerance_and_nothing_looser(offset):
    moved = AFFINE.copy()
    moved[1, 3] += offset
    assert _needs_resample(nib.Nifti1Image(np.zeros(SHAPE, np.float32), moved), reference_image()) == (abs(offset) > 1e-3)


@given(shape=st.tuples(st.integers(1, 9), st.integers(1, 9), st.integers(1, 9)))
def test_a_different_shape_always_needs_resampling(shape):
    assume(shape != SHAPE)
    assert _needs_resample(nib.Nifti1Image(np.zeros(shape, np.float32), AFFINE), reference_image())


# --- binarizzazione --------------------------------------------------------------------------


@given(voxels=voxel_sets)
@settings(max_examples=25)
def test_three_headers_for_the_same_physical_lesion_give_the_same_row(voxels):
    expected = to_volume(voxels).ravel() > 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, (data, affine) in header_variants(to_volume(voxels)).items():
            path = save(Path(tmp) / f"{name}.nii.gz", data, affine)
            row = _load_and_binarize_lesion(path, reference_image(), "nearest", 0.5)
            assert np.array_equal(row.astype(bool), expected), name
            assert row.dtype == np.uint8 and row.size == N_VOXELS


def test_the_three_header_variants_really_differ_at_array_level():
    """Guardia del test precedente: se i tre array grezzi fossero uguali, saltare il resampling
    passerebbe lo stesso. Un voxel asimmetrico in x li distingue."""
    variants = header_variants(to_volume({(2, 1, 1)}))
    raw = {name: np.flatnonzero(data) for name, (data, _) in variants.items()}
    assert len({tuple(r) for r in raw.values()}) == 3


@given(values=st.dictionaries(any_voxel, st.one_of(st.floats(-2, 2, width=32), st.sampled_from([np.nan, np.inf, -np.inf, 0.5, 0.25, 0.75])), max_size=30),
       threshold=st.sampled_from([0.0, 0.25, 0.5, 0.75, 0.99]))
@settings(max_examples=25)
def test_binarization_is_strictly_greater_than_threshold_and_nan_is_never_lesion(values, threshold):
    volume = np.zeros(SHAPE, dtype=np.float32)
    for v, value in values.items():
        volume[v] = value
    with tempfile.TemporaryDirectory() as tmp:
        row = _load_and_binarize_lesion(save(Path(tmp) / "m.nii.gz", volume), reference_image(), "nearest", threshold)
    assert set(np.unique(row)) <= {0, 1}
    assert np.array_equal(row.astype(bool), volume.astype(np.float64).ravel() > threshold)
    assert not row[np.isnan(volume).ravel()].any()


@given(values=st.dictionaries(any_voxel, st.floats(-1, 2, width=32), max_size=30), low=st.sampled_from([0.0, 0.25, 0.5]), step=st.sampled_from([0.1, 0.4]))
@settings(max_examples=25)
def test_raising_the_threshold_never_adds_lesion_voxels(values, low, step):
    volume = np.zeros(SHAPE, dtype=np.float32)
    for v, value in values.items():
        volume[v] = value
    with tempfile.TemporaryDirectory() as tmp:
        path = save(Path(tmp) / "m.nii.gz", volume)
        loose = _load_and_binarize_lesion(path, reference_image(), "nearest", low)
        strict = _load_and_binarize_lesion(path, reference_image(), "nearest", low + step)
    assert (strict <= loose).all()


@pytest.mark.parametrize("value, threshold, expected", [
    (0.5, 0.5, 0), (np.nextafter(np.float32(0.5), np.float32(1)), 0.5, 1), (np.nextafter(np.float32(0.5), np.float32(0)), 0.5, 0),
    (1.0, 1.0, 0), (1.0, 0.0, 1), (0.0, 0.0, 0), (-1.0, 0.0, 0), (np.inf, 0.5, 1), (-np.inf, 0.5, 0), (np.nan, 0.5, 0),
])
def test_threshold_boundary_values(value, threshold, expected):
    volume = np.zeros(SHAPE, dtype=np.float32)
    volume[2, 2, 2] = value
    with tempfile.TemporaryDirectory() as tmp:
        row = _load_and_binarize_lesion(save(Path(tmp) / "m.nii.gz", volume), reference_image(), "nearest", threshold)
    assert int(row.reshape(SHAPE)[2, 2, 2]) == expected


@pytest.mark.parametrize("dtype", [np.uint8, np.int16, np.int32, np.float32, np.float64])
@pytest.mark.parametrize("suffix", [".nii", ".nii.gz"])
def test_any_storage_dtype_and_compression_gives_the_same_binary_row(dtype, suffix):
    voxels = {(1, 1, 1), (4, 2, 5), (7, 7, 6)}
    with tempfile.TemporaryDirectory() as tmp:
        row = _load_and_binarize_lesion(save(Path(tmp) / f"m{suffix}", to_volume(voxels, dtype)), reference_image(), "nearest", 0.5)
    assert np.flatnonzero(row).tolist() == sorted(np.ravel_multi_index(v, SHAPE) for v in voxels)


@pytest.mark.parametrize("dtype, stored", [(np.uint8, 255), (np.int16, 7), (np.float32, 1000.0)])
def test_non_unit_positive_labels_are_still_lesion(dtype, stored):
    volume = np.zeros(SHAPE, dtype=dtype)
    volume[3, 3, 3] = stored
    with tempfile.TemporaryDirectory() as tmp:
        row = _load_and_binarize_lesion(save(Path(tmp) / "m.nii.gz", volume), reference_image(), "nearest", 0.5)
    assert row.sum() == 1


def test_a_trailing_singleton_fourth_dimension_gives_the_same_row():
    volume = to_volume({(2, 3, 4)})
    with tempfile.TemporaryDirectory() as tmp:
        flat = _load_and_binarize_lesion(save(Path(tmp) / "a.nii.gz", volume), reference_image(), "nearest", 0.5)
        four_d = _load_and_binarize_lesion(save(Path(tmp) / "b.nii.gz", volume[..., None]), reference_image(), "nearest", 0.5)
    assert np.array_equal(flat, four_d)


def test_a_four_dimensional_mask_with_several_volumes_is_rejected_or_has_the_reference_length():
    volume = np.zeros(SHAPE + (2,), dtype=np.float32)
    volume[2, 3, 4, 0] = 1
    with tempfile.TemporaryDirectory() as tmp:
        try:
            row = _load_and_binarize_lesion(save(Path(tmp) / "a.nii.gz", volume), reference_image(), "nearest", 0.5)
        except ValueError:
            return
    assert row.size == N_VOXELS


def test_a_truncated_gzip_never_yields_a_row_silently():
    volume = np.random.default_rng(0).random(SHAPE).astype(np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        path = save(Path(tmp) / "a.nii.gz", volume)
        raw = path.read_bytes()
        path.write_bytes(raw[:-10])
        with pytest.raises((EOFError, OSError, ValueError)):
            _load_and_binarize_lesion(path, reference_image(), "nearest", 0.5)


def test_a_missing_mask_file_raises():
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(FileNotFoundError):
        _load_and_binarize_lesion(Path(tmp) / "absent.nii.gz", reference_image(), "nearest", 0.5)


# --- build_lesion_matrix: riga = maschera appiattita ------------------------------------------


@given(masks=st.lists(voxel_sets, min_size=2, max_size=4), data=st.data())
@settings(max_examples=25)
def test_matrix_row_is_the_flattened_mask_in_subject_id_order(masks, data):
    assume(any(masks))
    ids = data.draw(st.permutations(range(len(masks))))  # id assegnati in ordine casuale
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i, voxels in zip(ids, masks):
            write_subject(root, sid(i), to_volume(voxels))
        X, metadata, non_constant, by_group, by_list, corrected = build(root)
    order = np.argsort(ids)
    rows = [to_volume(masks[k]).ravel() for k in order]
    assert metadata["subject_id"].tolist() == [sid(ids[k]) for k in order]
    assert_matrix_is(X, non_constant, rows)
    assert X.dtype == np.uint8 and non_constant.shape == (N_VOXELS,)
    assert metadata["lesion_volume_voxels"].tolist() == [len(masks[k]) for k in order]
    assert (by_group, by_list, corrected) == ([], [], [])


@given(masks=st.lists(voxel_sets, min_size=2, max_size=3))
@settings(max_examples=25)
def test_matrix_rows_are_the_same_whatever_header_each_subjects_file_has(masks):
    assume(any(masks))
    names = list(header_variants(to_volume(set())))
    with tempfile.TemporaryDirectory() as tmp_ref, tempfile.TemporaryDirectory() as tmp_mixed:
        for i, voxels in enumerate(masks):
            write_subject(Path(tmp_ref), sid(i), to_volume(voxels))
            data, affine = header_variants(to_volume(voxels))[names[i % len(names)]]
            write_subject(Path(tmp_mixed), sid(i), data, affine)
        reference_run, mixed_run = build(Path(tmp_ref)), build(Path(tmp_mixed))
    assert np.array_equal(reference_run[0], mixed_run[0])
    assert np.array_equal(reference_run[2], mixed_run[2])
    assert reference_run[1].equals(mixed_run[1])


@given(masks=st.lists(voxel_sets, min_size=2, max_size=4))
@settings(max_examples=25)
def test_a_cohort_where_every_mask_is_empty_raises_naming_the_threshold(masks):
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(len(masks)):
            write_subject(Path(tmp), sid(i), np.zeros(SHAPE, np.float32))
        with pytest.raises(ValueError, match="binarize_threshold"):
            build(Path(tmp))


def test_one_empty_mask_among_others_is_a_zero_row_not_an_error():
    with tempfile.TemporaryDirectory() as tmp:
        write_subject(Path(tmp), sid(0), to_volume({(1, 1, 1)}))
        write_subject(Path(tmp), sid(1), np.zeros(SHAPE, np.float32))
        write_subject(Path(tmp), sid(2), to_volume({(2, 2, 2)}))
        X, metadata, non_constant, *_ = build(Path(tmp))
    assert metadata["lesion_volume_voxels"].tolist() == [1, 0, 1]
    assert_matrix_is(X, non_constant, [to_volume({(1, 1, 1)}).ravel(), np.zeros(N_VOXELS), to_volume({(2, 2, 2)}).ravel()])
    assert X[1].sum() == 0


@given(masks=st.lists(voxel_sets, min_size=3, max_size=5), data=st.data())
@settings(max_examples=25)
def test_exclusion_list_removes_exactly_the_discovered_listed_subjects(masks, data):
    ids = [sid(i) for i in range(len(masks))]
    excluded = data.draw(st.sets(st.sampled_from(ids)))
    foreign = {"sub-STUKE9999", "sub-STUCLUK0001"}  # nel file di esclusione ma non in questo dataset
    kept = [(s, m) for s, m in zip(ids, masks) if s not in excluded]
    assume(kept and any(m for _, m in kept))
    with tempfile.TemporaryDirectory() as tmp:
        for s, voxels in zip(ids, masks):
            write_subject(Path(tmp), s, to_volume(voxels))
        X, metadata, non_constant, _, by_list, _ = build(Path(tmp), excluded_subjects=frozenset(excluded | foreign))
    assert by_list == sorted(excluded)
    assert metadata["subject_id"].tolist() == [s for s, _ in kept]
    assert_matrix_is(X, non_constant, [to_volume(m).ravel() for _, m in kept])


# --- correzione fuori dal cervello -------------------------------------------------------------


@given(masks=st.lists(voxel_sets, min_size=2, max_size=3), brain=st.sets(voxel, min_size=60, max_size=300), header=st.sampled_from(["ras_same_grid", "las_flipped", "ras_shifted"]))
@settings(max_examples=25)
def test_out_of_brain_correction_keeps_exactly_lesion_and_brain_whatever_the_brain_mask_header(masks, brain, header):
    assume(any(m & brain for m in masks) and any(m for m in masks))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i, voxels in enumerate(masks):
            write_subject(root, sid(i), to_volume(voxels))
        brain_data, brain_affine = header_variants(to_volume(brain))[header]
        brain_path = save(root / "brain.nii.gz", brain_data, brain_affine)
        X, metadata, non_constant, _, _, corrected = build(root, correct_out_of_brain=True, brain_mask_path=brain_path)
    inside = [m & brain for m in masks]
    assert_matrix_is(X, non_constant, [to_volume(m).ravel() for m in inside])
    assert metadata["lesion_volume_voxels"].tolist() == [len(m) for m in inside]
    assert corrected == [(sid(i), len(m - brain)) for i, m in enumerate(masks) if m - brain]


@given(X=st.lists(st.lists(st.booleans(), min_size=6, max_size=6), min_size=1, max_size=5), brain=st.lists(st.booleans(), min_size=6, max_size=6),
       dtype=st.sampled_from([np.uint8, np.int16, np.float32, np.float64]))
def test_zero_out_of_brain_voxels_is_idempotent_subset_and_counts_what_it_removed(X, brain, dtype):
    X, brain = np.array(X).astype(dtype), np.array(brain)
    snapshot = X.copy()
    corrected, n_corrected = zero_out_of_brain_voxels(X, brain)
    assert np.array_equal(X, snapshot)
    assert np.array_equal(corrected[:, brain], X[:, brain]) and not corrected[:, ~brain].any()
    assert np.array_equal(n_corrected, (X[:, ~brain] != 0).sum(axis=1))
    again, again_count = zero_out_of_brain_voxels(corrected, brain)
    assert np.array_equal(again, corrected) and not again_count.any()
    assert corrected.dtype == X.dtype


def test_brain_mask_file_that_is_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_brain_mask(tmp_path / "absent.nii.gz", reference_image())


# --- _drop_constant_features -----------------------------------------------------------------


@given(X=st.lists(st.lists(st.integers(0, 1), min_size=7, max_size=7), min_size=1, max_size=6))
def test_constant_columns_are_exactly_those_with_min_equal_max(X):
    X = np.array(X, dtype=np.uint8)
    kept, mask = _drop_constant_features(X)
    assert np.array_equal(mask, np.array([len(set(col)) > 1 for col in X.T]))
    assert np.array_equal(kept, X[:, mask])
    again, again_mask = _drop_constant_features(kept)
    assert np.array_equal(again, kept) and again_mask.all()


# --- laterality ------------------------------------------------------------------------------


@given(left=st.integers(0, 10_000), right=st.integers(0, 10_000), scale=st.integers(1, 50))
def test_laterality_index_is_bounded_antisymmetric_and_scale_free(left, right, scale):
    index = _laterality_index(left, right)
    if left + right == 0:
        assert np.isnan(index)
        return
    assert -1.0 <= index <= 1.0
    assert index == pytest.approx(-_laterality_index(right, left))
    assert index == pytest.approx(_laterality_index(scale * left, scale * right))
    assert (index > 0) == (left > right) and (index == 0) == (left == right)


@given(index=st.floats(-1, 1), threshold=st.floats(0.01, 0.99))
def test_side_is_left_right_or_both_and_mirrors_under_sign_flip(index, threshold):
    side = lesion_side_from_laterality_index(index, threshold)
    mirror = lesion_side_from_laterality_index(-index, threshold)
    assert side in {"left", "right", "both"}
    assert mirror == {"left": "right", "right": "left", "both": "both"}[side]
    assert (side == "both") == (abs(index) < threshold)


@pytest.mark.parametrize("index, expected", [(0.2, "left"), (-0.2, "right"), (np.nextafter(0.2, 0), "both"), (0.0, "both")])
def test_side_threshold_boundary_is_not_bilateral(index, expected):
    assert lesion_side_from_laterality_index(float(index), 0.2) == expected


@given(grid=st.lists(st.floats(-1, 1), min_size=2, max_size=12, unique=True))
def test_side_is_monotone_along_the_laterality_axis(grid):
    rank = {"right": 0, "both": 1, "left": 2}
    sides = [rank[lesion_side_from_laterality_index(x, 0.3)] for x in sorted(grid)]
    assert sides == sorted(sides)


# --- emisferi e frazione fuori dal cervello -------------------------------------------------


def _x_axis_image(n: int, step: float, origin: float) -> tuple[nib.Nifti1Image, np.ndarray]:
    affine = np.diag([step, 1.0, 1.0, 1.0])
    affine[0, 3] = origin
    world_x = np.broadcast_to((step * np.arange(n) + origin)[:, None, None], (n, 2, 2)).ravel()
    return nib.Nifti1Image(np.zeros((n, 2, 2), np.float32), affine), world_x


@given(n=st.integers(2, 9), step=st.floats(0.5, 3.0), origin=st.floats(-12.5, 12.5))
def test_hemisphere_masks_match_the_world_coordinates_of_every_voxel_on_ras_grids(n, step, origin):
    image, world_x = _x_axis_image(n, step, origin)
    assume(np.abs(world_x).min() > 1e-6)
    left, right = _hemisphere_masks(image)
    assert np.array_equal(left, world_x < 0) and np.array_equal(right, world_x > 0)
    assert not (left & right).any()


@pytest.mark.parametrize("n, step, origin", [(2, 1.0, 0.5), (8, 2.0, 7.0), (5, 1.5, 3.25), (9, 0.5, -1.25)])
def test_hemisphere_masks_match_the_world_coordinates_of_every_voxel_on_las_grids(n, step, origin):
    image, world_x = _x_axis_image(n, -step, origin)  # x decresce con l'indice: asse 'L'
    assert np.abs(world_x).min() > 1e-6
    left, right = _hemisphere_masks(image)
    assert np.array_equal(left, world_x < 0) and np.array_equal(right, world_x > 0)


@given(lesion=st.sets(any_voxel, max_size=60), brain=st.sets(any_voxel, max_size=200))
def test_out_of_brain_fraction_counts_lesion_voxels_off_the_mask(lesion, brain):
    lesion_arr, brain_arr = to_volume(lesion).ravel() > 0, to_volume(brain).ravel() > 0
    fraction = _out_of_brain_fraction(lesion_arr, brain_arr)
    if not lesion:
        assert np.isnan(fraction)
    else:
        assert fraction == pytest.approx(len(lesion - brain) / len(lesion))
        assert 0.0 <= fraction <= 1.0


@given(voxels=st.sets(voxel, min_size=1, max_size=40))
def test_validate_lesion_grids_accepts_alphanumeric_unique_names(voxels):
    names = [f"g{i}" for i in range(len(voxels) % 4 + 1)]
    validate_lesion_grids([LesionGrid(n, Path("t"), Path("b")) for n in names])


@given(name=st.text(min_size=0, max_size=6).filter(lambda s: not s.isalnum()))
def test_validate_lesion_grids_rejects_any_non_alphanumeric_name(name):
    with pytest.raises(ValueError, match="alphanumeric"):
        validate_lesion_grids([LesionGrid(name, Path("t"), Path("b"))])


# --- compute_lesion_metadata -----------------------------------------------------------------


def _grid(root: Path, brain: set | None) -> LesionGrid:
    template = save(root / "tpl.nii.gz", np.zeros(SHAPE, np.float32))
    brain_volume = np.ones(SHAPE, np.float32) if brain is None else to_volume(brain)
    return LesionGrid("g", template, save(root / "brain.nii.gz", brain_volume))


def _metadata(root: Path, grid: LesionGrid, *, correct: bool, threshold: float = 0.5, side_threshold: float = 0.2):
    return compute_lesion_metadata(
        data_root=root / "data", datasets=[DATASET], lesion_glob=GLOB, binarize_threshold=threshold,
        resample_interpolation="nearest", group_filter=None, grids=[grid], correct_out_of_brain=correct,
        side_threshold=side_threshold, location=make_location_spec(root, SHAPE, AFFINE, "g"),
    )


@given(lesion=st.sets(voxel, min_size=1, max_size=40), brain=st.sets(any_voxel, min_size=1, max_size=300), correct=st.booleans())
@settings(max_examples=15)
def test_lesion_metadata_is_identical_under_the_three_headers(lesion, brain, correct):
    assume(not correct or lesion & brain)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, (data, affine) in header_variants(to_volume(lesion)).items():
            write_subject(root, f"sub-STUNIPD{list(header_variants(to_volume(lesion))).index(name):04d}", data, affine)
        metadata, _ = _metadata(root, _grid(root, brain), correct=correct)
    columns = [c for c in metadata.columns if c not in ("subject_id", "dataset")]
    assert len(metadata) == 3
    for _, row in metadata[columns].iloc[1:].iterrows():
        pd.testing.assert_series_equal(row, metadata[columns].iloc[0], check_names=False)


@given(masks=st.lists(st.sets(voxel, min_size=1, max_size=30), min_size=2, max_size=3), brain=st.sets(any_voxel, min_size=150, max_size=400), correct=st.booleans())
@settings(max_examples=20)
def test_metadata_volume_agrees_with_the_matrix_builders_volume_and_with_set_algebra(masks, brain, correct):
    assume(not correct or all(m & brain for m in masks))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i, voxels in enumerate(masks):
            write_subject(root, sid(i), to_volume(voxels))
        grid = _grid(root, brain)
        metadata, _ = _metadata(root, grid, correct=correct)
        matrix_metadata = build(root, correct_out_of_brain=correct, brain_mask_path=grid.brain_mask_path)[1] if len({frozenset(m) for m in masks}) > 1 else None
    kept = [(m & brain) if correct else m for m in masks]
    assert metadata["lesion_volume_voxels_g"].tolist() == [len(k) for k in kept]
    # La frazione fuori dal cervello e' sempre misurata sulla maschera GREZZA, anche con la correzione attiva.
    assert metadata["out_of_brain_fraction_g"].tolist() == pytest.approx([len(m - brain) / len(m) for m in masks])
    if matrix_metadata is not None:
        assert matrix_metadata["lesion_volume_voxels"].tolist() == metadata["lesion_volume_voxels_g"].tolist()
