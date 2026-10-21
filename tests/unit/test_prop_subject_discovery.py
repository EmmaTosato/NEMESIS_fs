"""Test a proprietà di `src/features/subject_discovery.py` e della scoperta dei file di lesione.

Le proprietà valgono per layout di cartelle arbitrari (hypothesis): i file sono vuoti, perché la
scoperta legge solo i nomi. Ogni esempio usa una `TemporaryDirectory` nuova (`tmp_path` non viene
azzerato tra gli esempi di uno stesso test).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.features.lesion import _discover_lesion_files
from src.features.subject_discovery import discover_files_by_subject
from src.utils.subject_ids import KNOWN_SITES, group_of

GLOB = "manual_masks/*/anat/*_label-lesion_mask.nii.gz"
FLAT_GLOB = "masks/*_label-lesion_mask.nii.gz"
DATASET = "siteA"


@st.composite
def subject_ids(draw) -> tuple[str, str]:
    """(subject_id, gruppo atteso) costruiti dalle parti: il gruppo atteso non passa da `group_of`."""
    disease = draw(st.sampled_from(["ST", "PD", "GM"]))
    site = draw(st.sampled_from(KNOWN_SITES))
    healthy_control = draw(st.booleans())
    number = draw(st.integers(0, 9999))
    sid = f"sub-{disease}{site}{'HC' if healthy_control else ''}{number:04d}"
    return sid, ("HC" if healthy_control else disease)


unique_subjects = st.lists(subject_ids(), min_size=0, max_size=8, unique_by=lambda pair: pair[0])


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


def _write_layout(root: Path, sids: list[str]) -> dict[str, Path]:
    return {
        sid: _touch(root / DATASET / "manual_masks" / sid / "anat" / f"{sid}_label-lesion_mask.nii.gz")
        for sid in sids
    }


# --- partizione per gruppo ------------------------------------------------------------------


@given(subjects=unique_subjects)
def test_without_a_filter_every_subject_is_returned_and_nobody_is_excluded(subjects):
    with tempfile.TemporaryDirectory() as tmp:
        written = _write_layout(Path(tmp), [sid for sid, _ in subjects])
        found, excluded = discover_files_by_subject(Path(tmp), DATASET, GLOB, None)
    assert {sid: p.name for sid, p in found.items()} == {sid: p.name for sid, p in written.items()}
    assert excluded == []


@given(subjects=unique_subjects, group_filter=st.lists(st.sampled_from(["ST", "HC", "PD", "GM"]), unique=True))
def test_filter_partitions_the_subjects_by_group_and_the_exclusions_are_sorted(subjects, group_filter):
    expected_group = dict(subjects)
    with tempfile.TemporaryDirectory() as tmp:
        _write_layout(Path(tmp), list(expected_group))
        found, excluded = discover_files_by_subject(Path(tmp), DATASET, GLOB, group_filter)
    assert set(found) == {s for s, g in expected_group.items() if g in group_filter}
    assert excluded == sorted(s for s, g in expected_group.items() if g not in group_filter)
    assert set(found).isdisjoint(excluded)
    assert set(found) | set(excluded) == set(expected_group)


@given(subjects=unique_subjects)
def test_complementary_filters_recover_every_subject(subjects):
    with tempfile.TemporaryDirectory() as tmp:
        _write_layout(Path(tmp), [sid for sid, _ in subjects])
        patients, _ = discover_files_by_subject(Path(tmp), DATASET, GLOB, ["ST", "PD", "GM"])
        controls, _ = discover_files_by_subject(Path(tmp), DATASET, GLOB, ["HC"])
    assert set(patients) | set(controls) == {sid for sid, _ in subjects}
    assert set(patients).isdisjoint(controls)
    assert all(group_of(s) == "HC" for s in controls)


@given(subjects=unique_subjects, seed=st.randoms(use_true_random=False))
def test_result_does_not_depend_on_the_order_the_files_were_created_in(subjects, seed):
    sids = [sid for sid, _ in subjects]
    shuffled = sids[:]
    seed.shuffle(shuffled)
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        _write_layout(Path(a), sids)
        _write_layout(Path(b), shuffled)
        found_a, _ = discover_files_by_subject(Path(a), DATASET, GLOB, None)
        found_b, _ = discover_files_by_subject(Path(b), DATASET, GLOB, None)
    assert {s: p.relative_to(a) for s, p in found_a.items()} == {s: p.relative_to(b) for s, p in found_b.items()}


def test_a_filter_naming_no_group_excludes_everybody():
    with tempfile.TemporaryDirectory() as tmp:
        _write_layout(Path(tmp), ["sub-STUNIPD0001", "sub-STUNIPDHC0002"])
        found, excluded = discover_files_by_subject(Path(tmp), DATASET, GLOB, [])
    assert found == {} and excluded == ["sub-STUNIPD0001", "sub-STUNIPDHC0002"]


# --- ID sconosciuti o malformati: devono sollevare anche senza filtro (lesson #4, #20) ---------


@given(
    site=st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=2, max_size=7),
    group_filter=st.sampled_from([None, ["ST"], ["HC"], []]),
)
@settings(max_examples=25)
def test_a_site_outside_the_closed_registry_raises_whatever_the_filter(site, group_filter):
    assume(not any(site.startswith(known) for known in KNOWN_SITES))
    sid = f"sub-ST{site}0001"
    with tempfile.TemporaryDirectory() as tmp:
        _write_layout(Path(tmp), [sid])
        with pytest.raises(ValueError, match="naming"):
            discover_files_by_subject(Path(tmp), DATASET, GLOB, group_filter)


@pytest.mark.parametrize(
    "bad_id",
    [
        "sub_STUNIPD0001",  # underscore al posto del trattino: il `split("_")` ne farebbe "sub"
        "sub-stunipd0001",  # minuscolo
        "sub-STUNIPD",  # nessun numero
        "STUNIPD0001",  # niente prefisso
        "sub-XXUNIPD0001",  # malattia sconosciuta
        "sub-STUNIPD0001x",  # coda spuria
    ],
)
def test_a_malformed_subject_id_raises(bad_id):
    # Per "sub_STUNIPD0001" il nome file si spezza su "_" in "sub": la cartella e il nome divergono
    # e viene sollevato comunque, ma per la ragione del mismatch cartella/file, non del naming.
    with tempfile.TemporaryDirectory() as tmp:
        _write_layout(Path(tmp), [bad_id])
        with pytest.raises(ValueError):
            discover_files_by_subject(Path(tmp), DATASET, GLOB, None)


# --- duplicati e incoerenze cartella/file ---------------------------------------------------


@given(subjects=st.lists(subject_ids(), min_size=1, max_size=5, unique_by=lambda p: p[0]), data=st.data())
def test_a_second_matching_file_for_one_subject_raises_and_names_the_subject(subjects, data):
    sids = [sid for sid, _ in subjects]
    victim = data.draw(st.sampled_from(sids))
    group_filter = data.draw(st.sampled_from([None, ["ST", "PD", "GM", "HC"], ["ST"]]))
    with tempfile.TemporaryDirectory() as tmp:
        written = _write_layout(Path(tmp), sids)
        _touch(written[victim].with_name(f"{victim}_run-2_label-lesion_mask.nii.gz"))
        with pytest.raises(ValueError, match="more than one file") as excinfo:
            discover_files_by_subject(Path(tmp), DATASET, GLOB, group_filter)
    assert victim in str(excinfo.value)


@given(a=subject_ids(), b=subject_ids())
def test_a_file_misfiled_under_another_subjects_folder_raises(a, b):
    assume(a[0] != b[0])
    with tempfile.TemporaryDirectory() as tmp:
        _touch(Path(tmp) / DATASET / "manual_masks" / b[0] / "anat" / f"{a[0]}_label-lesion_mask.nii.gz")
        with pytest.raises(ValueError, match="disagree") as excinfo:
            discover_files_by_subject(Path(tmp), DATASET, GLOB, None)
    assert a[0] in str(excinfo.value) and b[0] in str(excinfo.value)


def test_a_glob_with_two_bare_wildcard_segments_is_ambiguous_and_raises():
    with tempfile.TemporaryDirectory() as tmp:
        _touch(Path(tmp) / DATASET / "x" / "sub-STUNIPD0001" / "sub-STUNIPD0001_a.nii.gz")
        with pytest.raises(ValueError, match="bare '\\*'"):
            discover_files_by_subject(Path(tmp), DATASET, "*/*/*_a.nii.gz", None)


@given(subjects=unique_subjects)
def test_a_flat_glob_without_a_subject_folder_has_no_crosscheck_but_still_validates_ids(subjects):
    with tempfile.TemporaryDirectory() as tmp:
        for sid, _ in subjects:
            _touch(Path(tmp) / DATASET / "masks" / f"{sid}_label-lesion_mask.nii.gz")
        found, _ = discover_files_by_subject(Path(tmp), DATASET, FLAT_GLOB, None)
    assert set(found) == {sid for sid, _ in subjects}


def test_files_that_do_not_match_the_glob_are_ignored():
    with tempfile.TemporaryDirectory() as tmp:
        written = _write_layout(Path(tmp), ["sub-STUNIPD0001"])
        _touch(Path(tmp) / DATASET / "manual_masks" / "sub-STUNIPD0001" / "anat" / "notes.txt")
        _touch(Path(tmp) / DATASET / "manual_masks" / "sub-STUNIPD0001" / "anat" / ".DS_Store")
        _touch(Path(tmp) / DATASET / "manual_masks" / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_label-lesion_mask.nii")
        found, excluded = discover_files_by_subject(Path(tmp), DATASET, GLOB, None)
    assert found == {"sub-STUNIPD0001": written["sub-STUNIPD0001"]} and excluded == []


# --- scoperta delle lesioni (src/features/lesion.py::_discover_lesion_files) -----------------


@given(patients=st.lists(st.integers(0, 9999), min_size=1, max_size=4, unique=True), controls=st.lists(st.integers(0, 9999), min_size=1, max_size=4, unique=True))
def test_a_control_folder_without_a_mask_only_matters_when_controls_are_in_scope(patients, controls):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_layout(root, [f"sub-STUNIPD{n:04d}" for n in patients])
        for n in controls:  # cartelle di controlli SENZA maschera
            (root / DATASET / "manual_masks" / f"sub-STUNIPDHC{n:04d}" / "anat").mkdir(parents=True)
        found, excluded = _discover_lesion_files(root, [DATASET], GLOB, ["ST"])
        assert set(found[DATASET]) == {f"sub-STUNIPD{n:04d}" for n in patients} and excluded == []
        with pytest.raises(ValueError, match="subject dirs"):
            _discover_lesion_files(root, [DATASET], GLOB, None)


def test_a_stray_directory_among_subject_folders_raises_even_without_a_filter():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_layout(root, ["sub-STUNIPD0001"])
        (root / DATASET / "manual_masks" / "backup").mkdir()
        with pytest.raises(ValueError, match="naming"):
            _discover_lesion_files(root, [DATASET], GLOB, None)


def test_a_stray_file_among_subject_folders_is_not_a_subject():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_layout(root, ["sub-STUNIPD0001"])
        _touch(root / DATASET / "manual_masks" / "README.txt")
        found, _ = _discover_lesion_files(root, [DATASET], GLOB, None)
    assert set(found[DATASET]) == {"sub-STUNIPD0001"}


def test_a_dataset_without_any_subject_folder_raises_instead_of_returning_nothing():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / DATASET).mkdir()
        with pytest.raises(FileNotFoundError, match="no subject directories"):
            _discover_lesion_files(Path(tmp), [DATASET], GLOB, None)


def test_a_glob_without_a_bare_wildcard_cannot_be_sanity_checked_and_raises():
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="bare '\\*'"):
            _discover_lesion_files(Path(tmp), [DATASET], "masks/*_label-lesion_mask.nii.gz", None)


@given(subjects=unique_subjects)
def test_one_dataset_failing_does_not_hide_behind_another_that_succeeds(subjects):
    # `datasets` è una lista: ogni dataset è validato, non solo il primo.
    assume(len(subjects) > 0)
    with tempfile.TemporaryDirectory() as tmp:
        _write_layout(Path(tmp), [sid for sid, _ in subjects])
        with pytest.raises(FileNotFoundError):
            _discover_lesion_files(Path(tmp), [DATASET, "missingSite"], GLOB, None)
