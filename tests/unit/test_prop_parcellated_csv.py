"""Test a proprietà di `src/features/parcellated_csv.py`: allineamento per nome (mai per posizione),
regioni omesse = 0.0, ammissione dei soggetti (registro x CSV x lista di esclusione x gruppo) come
partizione esatta, ID e valori che devono far sollevare.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.features.parcellated_csv import (
    BCBTOOLKIT_DIR,
    build_parcellated_matrix,
    discover_by_dataset,
    load_and_validate_csv,
    load_reference_regions,
    registered_subjects,
    stack_aligned_matrix,
    subjects_with_lesion_mask,
)
from src.utils import participants as participants_registry

ATLAS = "test_atlas"
OBJECT = "disconnectome"
VALUE = "mean_overlap"
REGISTRY_HEADER = "subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features\n"
PATIENTS = [f"sub-STUNIPD{i:04d}" for i in range(5)]
CONTROLS = [f"sub-STUNIPDHC{i:04d}" for i in range(2)]

region_names = st.text("abcdefghij_", min_size=1, max_size=6)
region_sets = st.lists(region_names, min_size=1, max_size=8, unique=True)
value = st.floats(0, 1, width=32)


def write_reference(path: Path, regions, column: str = "region_name") -> Path:
    path.write_text("\n".join([column, *regions]) + "\n")
    return path


def write_csv(data_root: Path, dataset: str, subject: str, rows: dict[str, float]) -> Path:
    path = data_root / dataset / BCBTOOLKIT_DIR / subject / f"{subject}_space-MNI152NLin6Asym_LF-{OBJECT}_atlas-{ATLAS}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"region_name": list(rows), VALUE: list(rows.values())}).to_csv(path, index=False)
    return path


def write_registry(metadata_root: Path, rows: list[tuple[str, str, bool]]) -> None:
    """rows: (dataset, subject_id, has_lesion)."""
    metadata_root.mkdir(parents=True, exist_ok=True)
    (metadata_root / "participants.csv").write_text(
        REGISTRY_HEADER + "".join(f"{s},{s},{d},ST,{lesion},True,False\n" for d, s, lesion in rows)
    )


# --- load_reference_regions ---------------------------------------------------------------------


@given(regions=region_sets, data=st.data())
def test_reference_regions_come_back_sorted_whatever_the_file_order(regions, data):
    shuffled = data.draw(st.permutations(regions))
    with tempfile.TemporaryDirectory() as tmp:
        loaded = load_reference_regions(write_reference(Path(tmp) / "r.csv", shuffled))
    assert loaded.tolist() == sorted(regions)


@given(regions=region_sets, dup=st.data())
def test_a_duplicated_reference_region_raises(regions, dup):
    repeated = dup.draw(st.sampled_from(regions))
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match="duplicate"):
        load_reference_regions(write_reference(Path(tmp) / "r.csv", [*regions, repeated]))


@pytest.mark.parametrize("column, requested", [("tract", "region_name"), ("region_name", "tract")])
def test_the_identifier_column_must_be_the_requested_one(column, requested):
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match="missing"):
        load_reference_regions(write_reference(Path(tmp) / "r.csv", ["a"], column), column=requested)


def test_a_missing_reference_file_raises():
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(FileNotFoundError):
        load_reference_regions(Path(tmp) / "absent.csv")


# --- load_and_validate_csv / stack_aligned_matrix -------------------------------------------------


@given(regions=region_sets, data=st.data())
def test_matrix_row_is_aligned_by_region_name_and_omitted_regions_are_zero(regions, data):
    reference = np.array(sorted(regions))
    present = data.draw(st.lists(st.sampled_from(regions), unique=True, max_size=len(regions)))
    values = {r: data.draw(value) for r in present}
    with tempfile.TemporaryDirectory() as tmp:
        frame = load_and_validate_csv(write_csv(Path(tmp), "d", "sub-STUNIPD0001", values), reference, VALUE)
    X, metadata = stack_aligned_matrix({("d", "sub-STUNIPD0001"): frame}, reference, VALUE)
    assert X.shape == (1, len(regions))
    assert X[0].tolist() == pytest.approx([values.get(r, 0.0) for r in reference])
    assert not np.isnan(X).any() and metadata.to_dict("records") == [{"subject_id": "sub-STUNIPD0001", "dataset": "d"}]


@given(regions=st.lists(region_names, min_size=2, max_size=8, unique=True), data=st.data())
def test_the_order_of_the_rows_inside_a_csv_never_changes_the_matrix(regions, data):
    reference = np.array(sorted(regions))
    values = {r: data.draw(value) for r in regions}
    shuffled = {k: values[k] for k in data.draw(st.permutations(list(values)))}
    with tempfile.TemporaryDirectory() as tmp:
        frame_a = load_and_validate_csv(write_csv(Path(tmp), "d", "sub-STUNIPD0001", values), reference, VALUE)
        frame_b = load_and_validate_csv(write_csv(Path(tmp), "d", "sub-STUNIPD0002", shuffled), reference, VALUE)
    X, _ = stack_aligned_matrix({("d", "sub-STUNIPD0001"): frame_a, ("d", "sub-STUNIPD0002"): frame_b}, reference, VALUE)
    assert np.array_equal(X[0], X[1])


def test_an_empty_csv_is_a_row_of_zeros_not_a_missing_subject():
    reference = np.array(["a", "b", "c"])
    with tempfile.TemporaryDirectory() as tmp:
        frame = load_and_validate_csv(write_csv(Path(tmp), "d", "sub-STUNIPD0001", {}), reference, VALUE)
    X, _ = stack_aligned_matrix({("d", "sub-STUNIPD0001"): frame}, reference, VALUE)
    assert X.tolist() == [[0.0, 0.0, 0.0]]


@given(keys=st.sets(st.tuples(st.sampled_from(["d2", "d1"]), st.integers(0, 20)), min_size=1, max_size=6))
def test_rows_are_sorted_by_dataset_then_subject_id_not_by_insertion_order(keys):
    reference = np.array(["a"])
    frames = {(d, f"sub-STUNIPD{i:04d}"): pd.DataFrame({"region_name": ["a"], VALUE: [float(i)]}) for d, i in sorted(keys, reverse=True)}
    X, metadata = stack_aligned_matrix(frames, reference, VALUE)
    expected = sorted(frames)
    assert list(zip(metadata["dataset"], metadata["subject_id"])) == expected
    assert X[:, 0].tolist() == [float(int(s[-4:])) for _, s in expected]


@given(regions=region_sets, extra=region_names)
def test_a_region_unknown_to_the_reference_raises_and_is_named(regions, extra):
    assume(extra not in regions)
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match="not in the reference") as excinfo:
        load_and_validate_csv(write_csv(Path(tmp), "d", "sub-STUNIPD0001", {regions[0]: 0.1, extra: 0.2}), np.array(regions), VALUE)
    assert extra in str(excinfo.value)


@given(regions=region_sets)
def test_a_region_listed_twice_raises(regions):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.csv"
        pd.DataFrame({"region_name": [regions[0], regions[0]], VALUE: [0.1, 0.2]}).to_csv(path, index=False)
        with pytest.raises(ValueError, match="duplicate"):
            load_and_validate_csv(path, np.array(regions), VALUE)


@pytest.mark.parametrize("columns", [["region_name"], [VALUE], ["name", VALUE]])
def test_a_csv_missing_the_identifier_or_the_value_column_raises(columns):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.csv"
        pd.DataFrame({c: ["a"] if c != VALUE else [0.1] for c in columns}).to_csv(path, index=False)
        with pytest.raises(ValueError, match="missing"):
            load_and_validate_csv(path, np.array(["a"]), VALUE)


@pytest.mark.parametrize("bad", ["abc", "1,5x"])
def test_a_non_numeric_value_cell_is_rejected(bad):
    reference = np.array(["a", "b"])
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.csv"
        pd.DataFrame({"region_name": ["a", "b"], VALUE: ["0.1", bad]}).to_csv(path, index=False)
        try:
            frame = load_and_validate_csv(path, reference, VALUE)
        except ValueError:
            return
    X, _ = stack_aligned_matrix({("d", "s"): frame}, reference, VALUE)
    assert X.dtype.kind == "f"


@pytest.mark.parametrize("bad", ["", "inf", "-inf"])
def test_an_empty_or_infinite_value_cell_raises_naming_file_line_and_region(bad):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.csv"
        pd.DataFrame({"region_name": ["a", "b"], VALUE: ["0.1", bad]}).to_csv(path, index=False)
        with pytest.raises(ValueError, match="not a finite number") as excinfo:
            load_and_validate_csv(path, np.array(["a", "b"]), VALUE)
    assert str(path) in str(excinfo.value) and "line 3" in str(excinfo.value) and "'b'" in str(excinfo.value)


# --- registro dei soggetti -------------------------------------------------------------------------

@given(flags=st.lists(st.booleans(), min_size=len(PATIENTS) + len(CONTROLS), max_size=len(PATIENTS) + len(CONTROLS)),
       group_filter=st.sampled_from([None, ["ST"], ["HC"], ["ST", "HC"], []]))
def test_registered_subjects_split_flagged_subjects_by_group(flags, group_filter):
    subjects = PATIENTS + CONTROLS
    with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as patch:
        patch.setattr(participants_registry, "METADATA_ROOT", Path(tmp))
        write_registry(Path(tmp), [("d", s, f) for s, f in zip(subjects, flags)])
        by_dataset, excluded = registered_subjects(["d"], group_filter, "has_lesion")
    flagged = [s for s, f in zip(subjects, flags) if f]
    keep = [s for s in flagged if group_filter is None or ("HC" if "HC" in s else "ST") in group_filter]
    assert by_dataset == {"d": keep}
    assert excluded == sorted(set(flagged) - set(keep))


def test_a_dataset_without_a_registry_row_raises_instead_of_meaning_nobody_has_a_mask():
    with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as patch:
        patch.setattr(participants_registry, "METADATA_ROOT", Path(tmp))
        write_registry(Path(tmp), [("d", PATIENTS[0], True)])
        with pytest.raises(ValueError, match="no row in the subject registry"):
            registered_subjects(["d", "ghost"], None, "has_lesion")


@given(states=st.lists(st.tuples(st.booleans(), st.booleans()), min_size=len(PATIENTS) + len(CONTROLS), max_size=len(PATIENTS) + len(CONTROLS)))
def test_exclusion_list_is_applied_after_the_group_so_nobody_is_reported_twice(states):
    subjects = PATIENTS + CONTROLS
    excluded = frozenset(s for s, (_, e) in zip(subjects, states) if e)
    with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as patch:
        patch.setattr(participants_registry, "METADATA_ROOT", Path(tmp))
        write_registry(Path(tmp), [("d", s, lesion) for s, (lesion, _) in zip(subjects, states)])
        kept, by_group, by_list = subjects_with_lesion_mask(["d"], ["ST"], excluded)
    with_mask = {s for s, (lesion, _) in zip(subjects, states) if lesion}
    assert set(kept["d"]) == {s for s in with_mask if s in PATIENTS and s not in excluded}
    assert by_group == sorted(s for s in with_mask if s in CONTROLS)
    assert by_list == sorted(s for s in with_mask & excluded if s in PATIENTS)
    assert set(by_group).isdisjoint(by_list)


# --- build_parcellated_matrix: la partizione dei soggetti e' esatta ---------------------------------


@given(
    states=st.lists(
        st.tuples(st.booleans(), st.booleans(), st.booleans(), st.booleans()),  # registrato, has_lesion, ha CSV, escluso
        min_size=len(PATIENTS) + len(CONTROLS), max_size=len(PATIENTS) + len(CONTROLS),
    ),
    group_filter=st.sampled_from([None, ["ST"]]),
)
@settings(max_examples=40)
def test_every_subject_lands_in_exactly_one_bucket(states, group_filter):
    subjects = PATIENTS + CONTROLS
    info = dict(zip(subjects, states))

    def in_scope(s):
        return group_filter is None or s in PATIENTS

    lesion_ids = {s for s, (reg, les, _, exc) in info.items() if reg and les and not exc and in_scope(s)}
    listed = {s for s, (reg, les, _, exc) in info.items() if reg and les and exc and in_scope(s)}
    csv_ids = {s for s, (_, _, csv, _) in info.items() if csv and in_scope(s)}
    assume(lesion_ids & csv_ids)

    with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as patch:
        root = Path(tmp)
        patch.setattr(participants_registry, "METADATA_ROOT", root / "metadata")
        write_registry(root / "metadata", [("d", s, les) for s, (reg, les, _, _) in info.items() if reg])
        for s, (_, _, csv, _) in info.items():
            if csv:
                write_csv(root, "d", s, {"b": 0.5, "a": float(int(s[-4:])) / 10})
        X, metadata, regions, by_group, by_list, no_mask, not_yet = build_parcellated_matrix(
            root, ["d"], OBJECT, ATLAS, VALUE, write_reference(root / "ref.csv", ["a", "b", "c"]), group_filter,
            frozenset(s for s, (_, _, _, exc) in info.items() if exc),
        )
    admitted = sorted(lesion_ids & csv_ids)
    assert metadata["subject_id"].tolist() == admitted and regions.tolist() == ["a", "b", "c"]
    assert np.allclose(X, [[float(int(s[-4:])) / 10, 0.5, 0.0] for s in admitted])
    assert by_list == sorted(listed)
    assert no_mask == sorted(csv_ids - lesion_ids - listed)
    assert not_yet == sorted(lesion_ids - csv_ids)
    assert set(admitted).isdisjoint(no_mask) and set(admitted).isdisjoint(not_yet) and set(admitted).isdisjoint(by_list)
    if group_filter is not None:
        assert set(CONTROLS) & set(admitted) == set()
        assert by_group == sorted(
            {s for s, (reg, les, _, _) in info.items() if reg and les and s in CONTROLS}
            | {s for s, (_, _, csv, _) in info.items() if csv and s in CONTROLS}
        )


def test_nobody_admitted_raises_and_does_not_return_an_empty_matrix():
    with tempfile.TemporaryDirectory() as tmp, pytest.MonkeyPatch.context() as patch:
        root = Path(tmp)
        patch.setattr(participants_registry, "METADATA_ROOT", root / "metadata")
        write_registry(root / "metadata", [("d", PATIENTS[0], True)])
        write_csv(root, "d", PATIENTS[1], {"a": 0.1})  # ha il CSV ma non e' nel registro
        with pytest.raises(ValueError, match="no subjects admitted"):
            build_parcellated_matrix(root, ["d"], OBJECT, ATLAS, VALUE, write_reference(root / "ref.csv", ["a"]), None, frozenset())


@pytest.mark.parametrize("kwargs, match", [({"object_": "tract"}, "object_"), ({"value_column": "p_value"}, "value_column")])
def test_unknown_object_or_value_column_raises_before_reading_anything(kwargs, match):
    call = dict(data_root=Path("/nonexistent"), datasets=["d"], object_=OBJECT, atlas=ATLAS, value_column=VALUE,
                reference_labels_path=Path("/nonexistent/ref.csv"), group_filter=None, excluded_subjects=frozenset())
    call.update(kwargs)
    with pytest.raises(ValueError, match=match):
        build_parcellated_matrix(**call)


@given(in_both=st.sets(st.integers(0, 5)), only_a=st.sets(st.integers(6, 9)))
def test_discovery_is_per_dataset_and_the_same_subject_may_live_in_two_datasets(in_both, only_a):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i in in_both:
            for dataset in ("a", "b"):
                write_csv(root, dataset, PATIENTS[0][:-4] + f"{i:04d}", {"x": 0.1})
        for i in only_a:
            write_csv(root, "a", PATIENTS[0][:-4] + f"{i:04d}", {"x": 0.1})
        found, excluded = discover_by_dataset(root, ["a", "b"], f"{BCBTOOLKIT_DIR}/*/*_LF-{OBJECT}_atlas-{ATLAS}.csv", None)
    assert set(found["a"]) == {PATIENTS[0][:-4] + f"{i:04d}" for i in in_both | only_a}
    assert set(found["b"]) == {PATIENTS[0][:-4] + f"{i:04d}" for i in in_both} and excluded == []
