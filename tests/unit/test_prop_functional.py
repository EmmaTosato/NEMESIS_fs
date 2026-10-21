"""Test a proprietà di `src/features/functional.py`: copertura dei parcelli (lesson #13: dtype stretti,
parcelli che spariscono dal masker), header delle lesioni (lesson #40), mascheramento dell'FC,
vettorizzazione del triangolo superiore, archi costanti, scoperta soggetti, isolamento per soggetto.

Atlante e lesioni sono 8x8x8 a 2 mm (origine -7 mm). L'atlante di riferimento ha due parcelli
(A: x < 4, B: x >= 4) e il voxel (7, 7, 7) a 0 come background; un test dedicato copre l'atlante
senza alcun voxel a 0, dove `labels_[0]` di nilearn e' gia' un parcello vero.
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
from hypothesis.extra.numpy import arrays

from src.features.functional import (
    compute_parcel_coverage,
    discover_subject_files,
    drop_constant_edges,
    find_compromised_nodes,
    load_atlas,
    mask_dataset_fc,
    mask_fc_by_lesion,
    mask_subject_fc,
    resample_lesion_to_atlas,
    stack_fc_vectors,
    vectorize_upper_triangle,
)

SHAPE = (8, 8, 8)
AFFINE = np.diag([2.0, 2.0, 2.0, 1.0])
AFFINE[:3, 3] = -7.0
NODES = np.array(["Region_A", "Region_B"])
LESION_GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"
FC_TEMPLATE = "features/*/func/*_FC-pearson_atlas-{combo}.csv"

voxel = st.tuples(st.integers(1, 7), st.integers(0, 7), st.integers(0, 7))
voxel_sets = st.sets(voxel, max_size=60)


def atlas_volume() -> np.ndarray:
    data = np.zeros(SHAPE, np.int32)
    data[:4], data[4:] = 1, 2
    data[7, 7, 7] = 0
    return data


def to_volume(voxels, dtype=np.float32) -> np.ndarray:
    volume = np.zeros(SHAPE, dtype=dtype)
    for v in voxels:
        volume[v] = 1
    return volume


def header_variants(volume: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    las = AFFINE @ np.array([[-1.0, 0, 0, SHAPE[0] - 1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    shifted = AFFINE.copy()
    shifted[0, 3] += AFFINE[0, 0]
    shifted_volume = np.zeros_like(volume)
    shifted_volume[:-1] = volume[1:]
    return {"ras_same_grid": (volume, AFFINE), "las_flipped": (np.ascontiguousarray(volume[::-1]), las), "ras_shifted": (shifted_volume, shifted)}


def expected_compromised(lesion: set, min_coverage: float) -> list[str]:
    """Calcolato sugli insiemi di voxel, indipendentemente da nilearn."""
    atlas = atlas_volume()
    out = []
    for name, label in zip(NODES, (1, 2)):
        total = int((atlas == label).sum())
        lesioned = sum(1 for v in lesion if atlas[v] == label)
        if (total - lesioned) / total < min_coverage:
            out.append(str(name))
    return out


def symmetric_fc(seed: int, names=NODES) -> pd.DataFrame:
    m = np.random.default_rng(seed).normal(size=(len(names), len(names)))
    values = (m + m.T) / 2
    np.fill_diagonal(values, 1.0)
    return pd.DataFrame(values, index=list(names), columns=list(names))


# --- compute_parcel_coverage ---------------------------------------------------------------


@given(labels=arrays(np.int32, (4, 4, 4), elements=st.integers(0, 3)), lesion=arrays(np.bool_, (4, 4, 4)), order_seed=st.integers(0, 1000),
       dtype=st.sampled_from([np.int16, np.int32, np.float32]))
@settings(max_examples=20)
def test_coverage_is_the_healthy_fraction_of_each_parcel_in_label_ids_order(labels, lesion, order_seed, dtype):
    labels[0, 0, 0] = 0  # background sempre presente
    present = sorted(set(np.unique(labels).tolist()) - {0})
    assume(present and (~lesion).any())
    label_ids = list(np.random.default_rng(order_seed).permutation(present))
    atlas = nib.Nifti1Image(labels.astype(dtype), AFFINE)
    healthy = nib.Nifti1Image((~lesion).astype(np.int32), AFFINE, atlas.header)
    coverage = compute_parcel_coverage(atlas, [int(i) for i in label_ids], healthy)
    expected = [float(((~lesion) & (labels == i)).sum()) / float((labels == i).sum()) for i in label_ids]
    assert coverage == pytest.approx(expected)
    assert ((coverage >= 0) & (coverage <= 1)).all()


@given(lesion=voxel_sets)
@settings(max_examples=20)
def test_a_parcel_lesioned_in_full_has_zero_coverage_not_a_missing_key(lesion):
    atlas = nib.Nifti1Image(atlas_volume(), AFFINE)
    full_a = {(x, y, z) for x in range(4) for y in range(8) for z in range(8)}
    healthy = nib.Nifti1Image((1 - to_volume(full_a | lesion, np.int32)), AFFINE, atlas.header)
    coverage = compute_parcel_coverage(atlas, [1, 2], healthy)
    assert coverage[0] == 0.0 and 0.0 <= coverage[1] <= 1.0


def test_a_lesion_covering_the_whole_volume_raises_instead_of_returning_coverage():
    atlas = nib.Nifti1Image(atlas_volume(), AFFINE)
    healthy = nib.Nifti1Image(np.zeros(SHAPE, np.int32), AFFINE, atlas.header)
    with pytest.raises(ValueError, match="empty"):
        compute_parcel_coverage(atlas, [1, 2], healthy)


def test_an_atlas_without_any_background_voxel_still_gets_its_first_parcel_measured():
    data = np.ones(SHAPE, np.int32)
    data[4:] = 2
    atlas = nib.Nifti1Image(data, AFFINE)
    healthy = nib.Nifti1Image(np.ones(SHAPE, np.int32), AFFINE, atlas.header)
    assert compute_parcel_coverage(atlas, [1, 2], healthy).tolist() == [1.0, 1.0]


# --- resample_lesion_to_atlas e mascheramento end-to-end sui tre header ------------------------


@given(lesion=voxel_sets)
@settings(max_examples=25)
def test_the_lesion_lands_on_the_atlas_grid_whatever_header_it_is_stored_with(lesion):
    atlas = nib.Nifti1Image(atlas_volume(), AFFINE)
    expected = to_volume(lesion, np.int32)
    for name, (data, affine) in header_variants(to_volume(lesion)).items():
        resampled = resample_lesion_to_atlas(nib.Nifti1Image(data, affine), atlas, "nearest", 0.5)
        assert resampled.dtype == np.int32 and np.array_equal(resampled, expected), name


@given(lesion=voxel_sets)
@settings(max_examples=25)
def test_a_lesion_stored_on_a_las_atlas_grid_gives_the_same_resampled_mask(lesion):
    """Lo scenario WashU di docs/dev/fc_matrix.md: stessa shape, X invertito rispetto all'atlante."""
    las_data, las_affine = header_variants(atlas_volume())["las_flipped"]
    las_atlas = nib.Nifti1Image(las_data.astype(np.int32), las_affine)
    resampled = resample_lesion_to_atlas(nib.Nifti1Image(to_volume(lesion), AFFINE), las_atlas, "nearest", 0.5)
    assert resampled.sum() == len(lesion)
    assert np.array_equal(resampled[::-1], to_volume(lesion, np.int32))


@pytest.mark.parametrize("value, threshold, expected", [(0.5, 0.5, 0), (0.75, 0.5, 1), (np.nan, 0.5, 0), (1.0, 1.0, 0), (-1.0, 0.0, 0)])
def test_resampled_lesion_binarization_is_strictly_greater_than_threshold(value, threshold, expected):
    volume = np.zeros(SHAPE, np.float32)
    volume[3, 3, 3] = value
    out = resample_lesion_to_atlas(nib.Nifti1Image(volume, AFFINE), nib.Nifti1Image(atlas_volume(), AFFINE), "nearest", threshold)
    assert int(out[3, 3, 3]) == expected


@given(lesion=voxel_sets, min_coverage=st.sampled_from([0.0, 0.25, 0.5, 0.75, 0.9, 1.0]))
@settings(max_examples=25)
def test_compromised_nodes_follow_the_set_algebra_and_not_the_lesion_header(lesion, min_coverage):
    atlas = nib.Nifti1Image(atlas_volume(), AFFINE)
    fc = symmetric_fc(0)
    expected = expected_compromised(lesion, min_coverage)
    for name, (data, affine) in header_variants(to_volume(lesion)).items():
        masked, compromised = mask_subject_fc(nib.Nifti1Image(data, affine), fc, atlas, [1, 2], NODES, min_coverage, "nearest", 0.5)
        assert list(compromised) == expected, name
        nan_nodes = [n for n in NODES if masked.loc[n].isna().all() and masked[n].isna().all()]
        assert nan_nodes == expected, name


def test_the_coverage_threshold_is_exclusive_a_parcel_exactly_at_it_is_kept():
    half_a = {(x, y, z) for x in range(1, 4) for y in range(8) for z in range(8)} | {(0, y, z) for y in range(8) for z in range(8)}
    lesion = {v for v in half_a if v[0] < 2}  # 128 dei 256 voxel di A -> copertura 0.5 esatta
    atlas = nib.Nifti1Image(atlas_volume(), AFFINE)
    _, at_threshold = mask_subject_fc(nib.Nifti1Image(to_volume(lesion), AFFINE), symmetric_fc(0), atlas, [1, 2], NODES, 0.5, "nearest", 0.5)
    _, above = mask_subject_fc(nib.Nifti1Image(to_volume(lesion), AFFINE), symmetric_fc(0), atlas, [1, 2], NODES, 0.5000001, "nearest", 0.5)
    assert list(at_threshold) == [] and list(above) == ["Region_A"]


# --- mask_fc_by_lesion / find_compromised_nodes -------------------------------------------------


@given(seed=st.integers(0, 10_000), n=st.integers(2, 7), data=st.data())
def test_masking_nans_exactly_the_rows_and_columns_of_compromised_nodes_and_leaves_the_rest(seed, n, data):
    names = np.array([f"n{i}" for i in range(n)])
    bad = np.array(sorted(data.draw(st.sets(st.sampled_from(list(names))))), dtype=names.dtype)
    fc = symmetric_fc(seed, names)
    snapshot = fc.copy()
    masked = mask_fc_by_lesion(fc, names, bad)
    pd.testing.assert_frame_equal(fc, snapshot)  # l'input non e' mutato
    nan_mask = masked.isna().to_numpy()
    expected_nan = np.isin(names, bad)[:, None] | np.isin(names, bad)[None, :]
    assert np.array_equal(nan_mask, expected_nan)
    keep = ~np.isin(names, bad)
    assert np.array_equal(masked.to_numpy()[np.ix_(keep, keep)], fc.to_numpy()[np.ix_(keep, keep)])
    assert np.array_equal(nan_mask, nan_mask.T)
    pd.testing.assert_frame_equal(mask_fc_by_lesion(masked, names, bad), masked)  # idempotente


@given(seed=st.integers(0, 100), n=st.integers(3, 6), swap=st.data())
def test_masking_refuses_labels_in_another_order_instead_of_aligning_by_position(seed, n, swap):
    names = np.array([f"n{i}" for i in range(n)])
    i, j = sorted(swap.draw(st.lists(st.integers(0, n - 1), min_size=2, max_size=2, unique=True)))
    shuffled = list(names)
    shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    fc = symmetric_fc(seed, names)
    with pytest.raises(ValueError, match="do not match"):
        mask_fc_by_lesion(fc.reindex(index=shuffled), names, names[:1])
    with pytest.raises(ValueError, match="do not match"):
        mask_fc_by_lesion(fc.reindex(columns=shuffled), names, names[:1])


@given(coverage=st.lists(st.floats(0, 1), min_size=1, max_size=8), threshold=st.floats(0, 1))
def test_compromised_nodes_are_those_strictly_below_the_threshold(coverage, threshold):
    names = np.array([f"n{i}" for i in range(len(coverage))])
    found = find_compromised_nodes(np.array(coverage), names, threshold)
    assert list(found) == [n for n, c in zip(names, coverage) if c < threshold]


# --- vectorize_upper_triangle -------------------------------------------------------------------


@given(seed=st.integers(0, 10_000), n=st.integers(2, 8), nan_nodes=st.data())
def test_upper_triangle_has_n_choose_2_unique_named_edges_and_round_trips(seed, n, nan_nodes):
    names = np.array([f"n{i}" for i in range(n)])
    fc = symmetric_fc(seed, names)
    for node in nan_nodes.draw(st.sets(st.sampled_from(list(names)))):  # nodi mascherati: NaN simmetrico
        fc.loc[node, :] = np.nan
        fc.loc[:, node] = np.nan
    vector = vectorize_upper_triangle(fc, names)
    assert len(vector) == n * (n - 1) // 2 and vector.index.is_unique
    rebuilt = pd.DataFrame(np.nan, index=names, columns=names)
    for edge, value in vector.items():
        a, b = edge.split("__")
        rebuilt.loc[a, b] = rebuilt.loc[b, a] = value
    off_diagonal = ~np.eye(n, dtype=bool)
    assert np.allclose(rebuilt.to_numpy()[off_diagonal], fc.to_numpy()[off_diagonal], equal_nan=True)


@given(seed=st.integers(0, 10_000), n=st.integers(2, 6), delta=st.floats(1e-2, 1.0), data=st.data())
def test_an_asymmetric_matrix_is_rejected_rather_than_losing_the_lower_triangle(seed, n, delta, data):
    names = np.array([f"n{i}" for i in range(n)])
    fc = symmetric_fc(seed, names)
    i, j = data.draw(st.lists(st.integers(0, n - 1), min_size=2, max_size=2, unique=True))
    fc.iloc[i, j] += delta
    with pytest.raises(ValueError, match="not symmetric"):
        vectorize_upper_triangle(fc, names)


def test_a_nan_in_only_one_triangle_is_asymmetric_and_rejected():
    fc = symmetric_fc(0, np.array(["a", "b", "c"]))
    fc.iloc[0, 2] = np.nan
    with pytest.raises(ValueError, match="not symmetric"):
        vectorize_upper_triangle(fc, np.array(["a", "b", "c"]))


def test_ambiguous_edge_names_when_node_names_contain_the_separator_are_rejected():
    names = np.array(["a", "b__c", "a__b", "c"])
    fc = pd.DataFrame(np.ones((4, 4)), index=names, columns=names)
    with pytest.raises(ValueError, match="a__b__c"):
        vectorize_upper_triangle(fc, names)


# --- drop_constant_edges ------------------------------------------------------------------------


@given(X=arrays(np.float64, st.tuples(st.integers(2, 5), st.integers(1, 9)), elements=st.sampled_from([0.0, 1.0, 2.0, np.nan])))
def test_an_edge_is_dropped_iff_fully_observed_and_constant(X):
    names = [f"e{j}" for j in range(X.shape[1])]
    kept_X, kept_names, dropped = drop_constant_edges(X, names)
    constant = [(not np.isnan(col).any()) and col.min() == col.max() for col in X.T]
    assert kept_names == [n for n, c in zip(names, constant) if not c]
    assert np.array_equal(kept_X, X[:, [not c for c in constant]], equal_nan=True)
    assert dropped == [(n, float(X[0, j])) for j, (n, c) in enumerate(zip(names, constant)) if c]
    again_X, again_names, again_dropped = drop_constant_edges(kept_X, kept_names)
    assert again_names == kept_names and again_dropped == [] and np.array_equal(again_X, kept_X, equal_nan=True)


@given(X=arrays(np.float64, (1, 6), elements=st.sampled_from([0.0, 1.0, np.nan])))
def test_a_single_subject_matrix_is_returned_unchanged_whatever_its_values(X, caplog):
    names = [f"e{j}" for j in range(6)]
    kept_X, kept_names, dropped = drop_constant_edges(X, names)
    assert np.array_equal(kept_X, X, equal_nan=True) and kept_names == names and dropped == []


# --- stack_fc_vectors -----------------------------------------------------------------------------


@given(n_subjects=st.integers(1, 5), n_edges=st.integers(1, 6), seed=st.integers(0, 1000))
def test_stacking_keeps_insertion_order_and_pairs_each_subject_with_its_dataset(n_subjects, n_edges, seed):
    edges = [f"e{j}" for j in range(n_edges)]
    rng = np.random.default_rng(seed)
    vectors = {f"sub-STUNIPD{i:04d}": pd.Series(rng.normal(size=n_edges), index=edges) for i in rng.permutation(n_subjects)}
    datasets = {s: f"site{k % 2}" for k, s in enumerate(vectors)}
    X, metadata, edge_names = stack_fc_vectors(vectors, datasets)
    assert edge_names == edges and metadata["subject_id"].tolist() == list(vectors)
    assert np.array_equal(X, np.stack([v.to_numpy() for v in vectors.values()]))
    assert metadata["dataset"].tolist() == [datasets[s] for s in vectors]


@given(n_edges=st.integers(2, 6), data=st.data())
def test_a_subject_whose_edges_are_permuted_is_rejected_not_stacked_by_position(n_edges, data):
    edges = [f"e{j}" for j in range(n_edges)]
    i, j = data.draw(st.lists(st.integers(0, n_edges - 1), min_size=2, max_size=2, unique=True))
    permuted = list(edges)
    permuted[i], permuted[j] = permuted[j], permuted[i]
    vectors = {"sub-STUNIPD0001": pd.Series(np.arange(n_edges, dtype=float), index=edges), "sub-STUNIPD0002": pd.Series(np.arange(n_edges, dtype=float), index=permuted)}
    with pytest.raises(ValueError, match="do not match"):
        stack_fc_vectors(vectors, {s: "d" for s in vectors})


@given(missing=st.sets(st.integers(0, 3), min_size=1))
def test_every_subject_without_a_dataset_entry_is_named_in_the_error(missing):
    vectors = {f"sub-STUNIPD{i:04d}": pd.Series([1.0], index=["e0"]) for i in range(4)}
    datasets = {s: "d" for k, s in enumerate(vectors) if k not in missing}
    with pytest.raises(ValueError) as excinfo:
        stack_fc_vectors(vectors, datasets)
    assert all(f"sub-STUNIPD{i:04d}" in str(excinfo.value) for i in missing)


# --- load_atlas ---------------------------------------------------------------------------------


def test_a_label_table_with_two_parcels_named_alike_is_rejected(tmp_path):
    nib.save(nib.Nifti1Image(atlas_volume(), AFFINE), tmp_path / "atlas.nii.gz")
    pd.DataFrame({"index": [1, 2], "label": ["Same", "Same"]}).to_csv(tmp_path / "dseg.tsv", sep="\t", index=False)
    with pytest.raises(ValueError):
        load_atlas(tmp_path / "atlas.nii.gz", tmp_path / "dseg.tsv")


@given(extra=st.sets(st.integers(3, 20), min_size=1, max_size=3))
@settings(max_examples=15)
def test_label_table_indices_missing_from_the_volume_are_all_named(extra):
    with tempfile.TemporaryDirectory() as tmp:
        nib.save(nib.Nifti1Image(atlas_volume(), AFFINE), Path(tmp) / "atlas.nii.gz")
        pd.DataFrame({"index": [1, 2, *sorted(extra)], "label": [f"r{i}" for i in [1, 2, *sorted(extra)]]}).to_csv(Path(tmp) / "dseg.tsv", sep="\t", index=False)
        with pytest.raises(ValueError, match="absent from the atlas") as excinfo:
            load_atlas(Path(tmp) / "atlas.nii.gz", Path(tmp) / "dseg.tsv")
    assert str(sorted(extra)) in str(excinfo.value)


# --- discover_subject_files ----------------------------------------------------------------------

PATIENTS = [f"sub-STUNIPD{i:04d}" for i in range(5)]
CONTROLS = [f"sub-STUNIPDHC{i:04d}" for i in range(3)]


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


@given(lesion=st.sets(st.sampled_from(PATIENTS + CONTROLS)), fc=st.sets(st.sampled_from(PATIENTS + CONTROLS)),
       group_filter=st.sampled_from([None, ["ST"], ["HC"], ["ST", "HC"]]))
@settings(max_examples=40)
def test_discovery_partitions_subjects_by_group_then_by_lesion_and_fc_presence(lesion, fc, group_filter):
    def in_scope(s: str) -> bool:
        return group_filter is None or ("HC" if "HC" in s else "ST") in group_filter

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for s in lesion:
            _touch(root / "d" / "manual_masks" / s / "anat" / f"{s}_label-lesion_mask.nii.gz")
        for s in fc:
            _touch(root / "d" / "features" / s / "func" / f"{s}_FC-pearson_atlas-C.csv")
        usable = {s for s in fc & lesion if in_scope(s)}
        if not fc:
            with pytest.raises(FileNotFoundError):
                discover_subject_files(root, "d", "C", LESION_GLOB, FC_TEMPLATE, group_filter)
            return
        if not usable:
            with pytest.raises(ValueError, match="no subject"):
                discover_subject_files(root, "d", "C", LESION_GLOB, FC_TEMPLATE, group_filter)
            return
        files, missing_lesion, excluded = discover_subject_files(root, "d", "C", LESION_GLOB, FC_TEMPLATE, group_filter)
    assert set(files) == usable and list(files) == sorted(usable)
    assert missing_lesion == sorted(s for s in fc - lesion if in_scope(s))
    assert excluded == sorted(s for s in fc | lesion if not in_scope(s))
    assert all(lesion_path.name.startswith(s) and fc_path.name.startswith(s) for s, (lesion_path, fc_path) in files.items())


# --- mask_dataset_fc: isolamento per soggetto -----------------------------------------------------


def _dataset(root: Path, subjects: dict[str, dict]) -> tuple[Path, Path, Path, Path]:
    """subjects: {sid: {"lesion": (data, affine) | None, "fc": DataFrame}}. Ritorna (data_root, atlas, tsv, output)."""
    atlas_path = root / "atlas.nii.gz"
    nib.save(nib.Nifti1Image(atlas_volume(), AFFINE), atlas_path)
    tsv = root / "dseg.tsv"
    pd.DataFrame({"index": [1, 2], "label": list(NODES)}).to_csv(tsv, sep="\t", index=False)
    for s, spec in subjects.items():
        if spec.get("lesion") is not None:
            data, affine = spec["lesion"]
            path = root / "data" / "d" / "manual_masks" / s / "anat" / f"{s}_label-lesion_mask.nii.gz"
            path.parent.mkdir(parents=True, exist_ok=True)
            nib.save(nib.Nifti1Image(data, affine), path)
        fc_path = root / "data" / "d" / "features" / s / "func" / f"{s}_FC-pearson_atlas-C.csv"
        fc_path.parent.mkdir(parents=True, exist_ok=True)
        spec["fc"].to_csv(fc_path, sep="\t")
    return root / "data", atlas_path, tsv, root / "out"


def _run(root: Path, subjects: dict, min_coverage: float = 0.5):
    data_root, atlas, tsv, out = _dataset(root, subjects)
    return mask_dataset_fc(data_root, "d", atlas, tsv, "C", LESION_GLOB, FC_TEMPLATE, min_coverage, "nearest", 0.5, out, None) + (out,)


@given(lesions=st.lists(voxel_sets, min_size=1, max_size=3), headers=st.lists(st.sampled_from(["ras_same_grid", "las_flipped", "ras_shifted"]), min_size=1, max_size=3))
@settings(max_examples=15)
def test_summary_counts_compromised_nodes_per_subject_whatever_the_lesion_header(lesions, headers):
    with tempfile.TemporaryDirectory() as tmp:
        subjects = {
            f"sub-STUNIPD{i:04d}": {"lesion": header_variants(to_volume(les))[headers[i % len(headers)]], "fc": symmetric_fc(i)}
            for i, les in enumerate(lesions)
        }
        summary, missing, excluded, failed, out = _run(Path(tmp), subjects)
        written = sorted(p.name for p in out.glob("*_masked_fc.csv"))
    assert failed == {} and missing == [] and excluded == []
    assert summary["subject_id"].tolist() == sorted(subjects)
    assert summary["n_compromised_nodes"].tolist() == [len(expected_compromised(les, 0.5)) for les in lesions]
    assert written == [f"{s}_masked_fc.csv" for s in sorted(subjects)]


def test_a_subject_without_a_lesion_mask_is_reported_not_masked():
    with tempfile.TemporaryDirectory() as tmp:
        subjects = {"sub-STUNIPD0001": {"lesion": (to_volume({(2, 2, 2)}), AFFINE), "fc": symmetric_fc(1)}, "sub-STUNIPD0002": {"lesion": None, "fc": symmetric_fc(2)}}
        summary, missing, _, failed, out = _run(Path(tmp), subjects)
        assert not (out / "sub-STUNIPD0002_masked_fc.csv").exists()
    assert missing == ["sub-STUNIPD0002"] and summary["subject_id"].tolist() == ["sub-STUNIPD0001"] and failed == {}


@pytest.mark.parametrize("bad_fc", [
    pytest.param(symmetric_fc(1, np.array(["Region_B", "Region_A"])), id="nodes-reversed"),
    pytest.param(symmetric_fc(1, np.array(["Region_A", "Region_B", "Region_C"])), id="extra-node"),
    pytest.param(symmetric_fc(1, np.array(["Region_A", "Other"])), id="renamed-node"),
])
def test_an_fc_matrix_with_the_wrong_nodes_fails_that_subject_only(bad_fc):
    with tempfile.TemporaryDirectory() as tmp:
        subjects = {"sub-STUNIPD0001": {"lesion": (to_volume({(2, 2, 2)}), AFFINE), "fc": symmetric_fc(0)}, "sub-STUNIPD0002": {"lesion": (to_volume({(2, 2, 2)}), AFFINE), "fc": bad_fc}}
        summary, _, _, failed, out = _run(Path(tmp), subjects)
        assert (out / "sub-STUNIPD0001_masked_fc.csv").is_file() and not (out / "sub-STUNIPD0002_masked_fc.csv").exists()
    assert set(failed) == {"sub-STUNIPD0002"} and summary["subject_id"].tolist() == ["sub-STUNIPD0001"]


def _truncate_lesion(root: Path, subject: str) -> None:
    path = root / "data" / "d" / "manual_masks" / subject / "anat" / f"{subject}_label-lesion_mask.nii.gz"
    raw = path.read_bytes()
    path.write_bytes(raw[: len(raw) // 2])  # header intact, data stream cut: EOFError at read time


def test_a_truncated_gzip_lesion_fails_that_subject_only():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subjects = {f"sub-STUNIPD000{i}": {"lesion": (np.random.default_rng(i).random(SHAPE).astype(np.float32), AFFINE), "fc": symmetric_fc(i)} for i in (1, 2)}
        data_root, atlas, tsv, out = _dataset(root, subjects)
        _truncate_lesion(root, "sub-STUNIPD0002")
        summary, _, _, failed = mask_dataset_fc(data_root, "d", atlas, tsv, "C", LESION_GLOB, FC_TEMPLATE, 0.5, "nearest", 0.5, out, None)
    assert set(failed) == {"sub-STUNIPD0002"} and summary["subject_id"].tolist() == ["sub-STUNIPD0001"]


def test_when_every_subject_fails_the_result_is_a_clean_report_or_a_domain_error():
    with tempfile.TemporaryDirectory() as tmp:
        subjects = {f"sub-STUNIPD000{i}": {"lesion": (to_volume({(2, 2, 2)}), AFFINE), "fc": symmetric_fc(i, np.array(["Region_B", "Region_A"]))} for i in (1, 2)}
        try:
            summary, _, _, failed, _ = _run(Path(tmp), subjects)
        except ValueError:
            return
    assert set(failed) == set(subjects) and summary.empty
