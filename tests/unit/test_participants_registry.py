"""Unit tests for src/utils/participants.py::load_excluded_subjects - the hand-curated list of
subjects kept out of the production matrices, each row scoped to the matrix(es) it applies to.

Every test gets its own isolated metadata root (never touches the real assets/metadata/), same
convention as tests/unit/test_features_sdc.py's own _metadata_root fixture.
"""

import pandas as pd
import pytest

import src.utils.participants as participants_registry
from src.utils.participants import (
    KNOWN_EXCLUSION_REASONS,
    KNOWN_EXCLUSION_SCOPES,
    load_excluded_subjects,
)

_HEADER = "subject_id,dataset,reason,scope,value\n"
_SCOPE = "lesion"  # the matrix "asking" in tests that are not about scoping


@pytest.fixture
def metadata_root(tmp_path, monkeypatch):
    root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def _write_registry(metadata_root, rows):
    """rows: (subject_id, dataset) pairs. Only the columns load_participants_registry requires."""
    metadata_root.mkdir(parents=True, exist_ok=True)
    lines = ["subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features"]
    lines += [f"{s},{s},{dataset},ST,True,True,False" for s, dataset in rows]
    (metadata_root / "participants.csv").write_text("\n".join(lines) + "\n")


def _write_list(tmp_path, body):
    path = tmp_path / "excluded_subjects.csv"
    path.write_text(_HEADER + body)
    return path


def test_header_only_file_means_nothing_excluded(tmp_path, metadata_root):
    """The explicit way to say "exclude nobody". It short-circuits before the registry lookup,
    so it stays usable before any participants.csv exists - note no _write_registry here."""
    excluded = load_excluded_subjects(_write_list(tmp_path, ""), _SCOPE)

    assert excluded.empty
    assert list(excluded.columns) == ["subject_id", "dataset", "reason", "scope", "value"]


def test_missing_file_raises_and_says_how_to_exclude_nobody(tmp_path):
    """A missing file is indistinguishable from "never written", so it must not be read as
    "exclude nobody" - that would silently admit every borderline subject."""
    with pytest.raises(FileNotFoundError, match="header row"):
        load_excluded_subjects(tmp_path / "never_written.csv", _SCOPE)


def test_valid_rows_are_returned_with_numeric_value(tmp_path, metadata_root):
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU"), ("sub-STUKE0146", "UKE/WAKEUP_acute")])
    path = _write_list(
        tmp_path,
        "sub-STUNIPD0001,UNIPD/WashU,lesion_too_small,all,2\n"
        "sub-STUKE0146,UKE/WAKEUP_acute,out_of_brain_fraction_too_high,all,0.83\n",
    )

    excluded = load_excluded_subjects(path, _SCOPE)

    assert list(excluded["subject_id"]) == ["sub-STUNIPD0001", "sub-STUKE0146"]
    assert excluded["value"].tolist() == [2.0, 0.83]
    assert pd.api.types.is_float_dtype(excluded["value"])


def test_missing_column_raises(tmp_path, metadata_root):
    path = tmp_path / "excluded_subjects.csv"
    path.write_text("subject_id,dataset,reason,value\nsub-STUNIPD0001,UNIPD/WashU,empty_mask,0\n")

    with pytest.raises(ValueError, match="missing required column"):
        load_excluded_subjects(path, _SCOPE)


def test_duplicate_subject_in_the_same_scope_raises(tmp_path, metadata_root):
    """Rejected rather than deduplicated: two rows for one subject in one scope make the reason it
    was dropped from that matrix ambiguous, and are almost always a copy-paste mistake
    (lessons_learned.md #5)."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(
        tmp_path,
        "sub-STUNIPD0001,UNIPD/WashU,lesion_too_small,lesion,2\nsub-STUNIPD0001,UNIPD/WashU,empty_mask,lesion,0\n",
    )

    with pytest.raises(ValueError, match="duplicate \\(subject_id, scope\\)"):
        load_excluded_subjects(path, _SCOPE)


def test_unregistered_reason_raises_and_lists_the_known_ones(tmp_path, metadata_root):
    """The vocabulary is closed so a typo cannot quietly become a new category nothing counts."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(tmp_path, "sub-STUNIPD0001,UNIPD/WashU,lesion_to_small,all,2\n")  # typo

    with pytest.raises(ValueError, match="unregistered reason") as exc:
        load_excluded_subjects(path, _SCOPE)
    assert all(reason in str(exc.value) for reason in KNOWN_EXCLUSION_REASONS)


def test_subject_absent_from_the_registry_raises(tmp_path, metadata_root):
    """A typo'd id would otherwise exclude nobody, silently - the matrix would be built with the
    subject still in it and nothing would say so."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(tmp_path, "sub-STUNIPD9999,UNIPD/WashU,empty_mask,all,0\n")

    with pytest.raises(ValueError, match="have no row in"):
        load_excluded_subjects(path, _SCOPE)


def test_dataset_disagreeing_with_the_registry_raises(tmp_path, metadata_root):
    """`dataset` is redundant with the registry, and redundant hand-typed data drifts - so it is
    checked rather than trusted or silently ignored."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(tmp_path, "sub-STUNIPD0001,UNIPD/PASPORT,empty_mask,all,0\n")

    with pytest.raises(ValueError, match="name the wrong dataset"):
        load_excluded_subjects(path, _SCOPE)


def test_non_numeric_value_raises(tmp_path, metadata_root):
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(tmp_path, "sub-STUNIPD0001,UNIPD/WashU,lesion_too_small,all,piccola\n")

    with pytest.raises(ValueError, match="non-numeric 'value'"):
        load_excluded_subjects(path, _SCOPE)


def test_blank_subject_id_raises(tmp_path, metadata_root):
    """A trailing/blank row from a hand edit must not silently become an unnamed exclusion."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(tmp_path, " ,UNIPD/WashU,empty_mask,all,0\n")

    with pytest.raises(ValueError, match="empty subject_id"):
        load_excluded_subjects(path, _SCOPE)


# --- scope (added 30/09) -------------------------------------------------------


def _write_scoped_list(tmp_path, metadata_root):
    """Three subjects, one row each: everywhere, lesion only, streamline only."""
    _write_registry(
        metadata_root,
        [("sub-STUNIPD0001", "UNIPD/WashU"), ("sub-STUNIPD0002", "UNIPD/WashU"), ("sub-STUNIPD0003", "UNIPD/WashU")],
    )
    return _write_list(
        tmp_path,
        "sub-STUNIPD0001,UNIPD/WashU,empty_mask,all,0\n"
        "sub-STUNIPD0002,UNIPD/WashU,lesion_too_small,lesion,2\n"
        "sub-STUNIPD0003,UNIPD/WashU,all_zero_features,sdc-streamline,0\n",
    )


def test_each_scope_gets_its_own_rows_plus_all(tmp_path, metadata_root):
    """The point of the column: a subject unusable in one feature space stays in the others."""
    path = _write_scoped_list(tmp_path, metadata_root)

    assert list(load_excluded_subjects(path, "lesion")["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    assert list(load_excluded_subjects(path, "sdc-streamline")["subject_id"]) == [
        "sub-STUNIPD0001",
        "sub-STUNIPD0003",
    ]
    # neither of the other two rows applies to a representation nobody scoped them to
    assert list(load_excluded_subjects(path, "sdc-voxelwise")["subject_id"]) == ["sub-STUNIPD0001"]


def test_row_scoped_to_another_matrix_is_still_validated(tmp_path, metadata_root):
    """A typo in a row meant for the streamline matrix must fail when the LESION matrix runs too,
    not lie dormant until someone builds streamline - validation covers the whole file."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(tmp_path, "sub-STUNIPD0001,UNIPD/WashU,all_zero_featuress,sdc-streamline,0\n")  # typo

    with pytest.raises(ValueError, match="unregistered reason"):
        load_excluded_subjects(path, "lesion")


def test_unregistered_scope_raises_and_lists_the_known_ones(tmp_path, metadata_root):
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(tmp_path, "sub-STUNIPD0001,UNIPD/WashU,empty_mask,sdc-streamlines,0\n")  # typo

    with pytest.raises(ValueError, match="unregistered scope") as exc:
        load_excluded_subjects(path, _SCOPE)
    assert all(scope in str(exc.value) for scope in KNOWN_EXCLUSION_SCOPES)


def test_same_subject_in_two_different_scopes_is_allowed(tmp_path, metadata_root):
    """Two narrow rows for one subject are not a duplicate: each says something different."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(
        tmp_path,
        "sub-STUNIPD0001,UNIPD/WashU,lesion_too_small,lesion,2\n"
        "sub-STUNIPD0001,UNIPD/WashU,all_zero_features,sdc-streamline,0\n",
    )

    assert len(load_excluded_subjects(path, "lesion")) == 1
    assert len(load_excluded_subjects(path, "sdc-streamline")) == 1


def test_scope_all_plus_a_narrower_row_for_the_same_subject_raises(tmp_path, metadata_root):
    """'all' already covers every matrix, so a second row can only contradict it - and which one
    wins would depend on which matrix asks. Rejected rather than resolved."""
    _write_registry(metadata_root, [("sub-STUNIPD0001", "UNIPD/WashU")])
    path = _write_list(
        tmp_path,
        "sub-STUNIPD0001,UNIPD/WashU,empty_mask,all,0\n"
        "sub-STUNIPD0001,UNIPD/WashU,all_zero_features,sdc-streamline,0\n",
    )

    with pytest.raises(ValueError, match="both a scope='all' row and a narrower one"):
        load_excluded_subjects(path, _SCOPE)


@pytest.mark.parametrize("asked", ["all", "sdc", "", "Lesion"])
def test_asking_for_a_scope_that_is_not_askable_raises(tmp_path, metadata_root, asked):
    """'all' is a value rows carry, not a matrix that can ask; the rest are typos. Both must
    fail rather than quietly return an empty or unfiltered list."""
    path = _write_scoped_list(tmp_path, metadata_root)

    with pytest.raises(ValueError, match="scope must be one of"):
        load_excluded_subjects(path, asked)


def test_all_zero_features_is_a_registered_reason():
    assert "all_zero_features" in KNOWN_EXCLUSION_REASONS
