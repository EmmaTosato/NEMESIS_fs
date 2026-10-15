"""Unit tests for src/features/parcellated_csv.py, for the `lesion` object.

The `disconnectome` object (same builder, same code path) is covered in test_features_sdc.py;
what is specific here is that the lesion matrix reads the `LF-lesion` family next to the
`LF-disconnectome` one that every subject also has, and that a subject with no CSV is reported
instead of becoming a row of zeros.
"""

import numpy as np
import pytest

from src.features.parcellated_csv import build_parcellated_matrix
from src.utils import participants as participants_registry

_ATLAS = "test_atlas"
_REGISTRY_HEADER = "subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features"
_LESION_COLUMNS = ("region_name", "n_voxels_region", "n_voxels_overlap", "fraction_covered", "mean_overlap")


@pytest.fixture(autouse=True)
def _metadata_root(tmp_path, monkeypatch):
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", metadata_root)
    return metadata_root


def _register(metadata_root, dataset, subject_id):
    metadata_root.mkdir(parents=True, exist_ok=True)
    path = metadata_root / "participants.csv"
    if not path.is_file():
        path.write_text(_REGISTRY_HEADER + "\n")
    with path.open("a") as f:
        f.write(f"{subject_id},{subject_id},{dataset},ST,True,True,False\n")


def _write_csv(data_root, dataset, subject_id, object_, rows):
    """rows: {region_name: fraction}. Written with the real LF-lesion columns, so a builder
    that picked the wrong value column would read a different number."""
    subject_dir = data_root / dataset / "bcbtoolkit" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    lines = [",".join(_LESION_COLUMNS)] + [f"{r},100,{int(100 * v)},{v},{v / 2}" for r, v in rows.items()]
    (subject_dir / f"{subject_id}_space-MNI152NLin6Asym_LF-{object_}_atlas-{_ATLAS}.csv").write_text(
        "\n".join(lines) + "\n"
    )


def _reference(tmp_path, regions):
    path = tmp_path / "labels.csv"
    path.write_text("\n".join(["region_name", *regions]) + "\n")
    return path


def _build(tmp_path, reference, value_column="fraction_covered", excluded=frozenset()):
    return build_parcellated_matrix(
        data_root=tmp_path, datasets=["siteA"], object_="lesion", atlas=_ATLAS, value_column=value_column,
        reference_labels_path=reference, group_filter=None, excluded_subjects=excluded,
    )


def test_lesion_object_reads_the_lesion_csv_not_the_disconnectome_one(tmp_path, _metadata_root):
    _register(_metadata_root, "siteA", "sub-STUNIPD0001")
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0001", "lesion", {"A": 0.5, "C": 0.25})
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0001", "disconnectome", {"A": 0.9, "B": 0.9, "C": 0.9})

    X, _, region_names, *_ = _build(tmp_path, _reference(tmp_path, ["A", "B", "C"]))

    assert list(region_names) == ["A", "B", "C"]
    np.testing.assert_array_equal(X, [[0.5, 0.0, 0.25]])  # B omitted by BCBToolKit -> 0.0


def test_lesion_value_column_selects_the_requested_statistic(tmp_path, _metadata_root):
    _register(_metadata_root, "siteA", "sub-STUNIPD0001")
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0001", "lesion", {"A": 0.5})

    X, *_ = _build(tmp_path, _reference(tmp_path, ["A"]), value_column="mean_overlap")

    np.testing.assert_array_equal(X, [[0.25]])  # mean_overlap, not fraction_covered (0.5)


def test_subject_with_mask_but_no_lesion_csv_is_reported_not_zero_filled(tmp_path, _metadata_root):
    """The 'admitted but no CSV' case: absent from the matrix and named in csv_not_yet_computed,
    never a row of zeros indistinguishable from a lesion that touches no region."""
    for subject in ("sub-STUNIPD0001", "sub-STUNIPD0002"):
        _register(_metadata_root, "siteA", subject)
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0001", "lesion", {"A": 0.5})
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0002", "disconnectome", {"A": 0.5})  # no lesion CSV

    X, metadata, _, _, _, excluded_no_mask, csv_not_yet_computed = _build(tmp_path, _reference(tmp_path, ["A"]))

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert X.shape == (1, 1)
    assert csv_not_yet_computed == ["sub-STUNIPD0002"]
    assert excluded_no_mask == []


def test_lesion_csv_without_registered_mask_is_excluded_and_named(tmp_path, _metadata_root):
    _register(_metadata_root, "siteA", "sub-STUNIPD0001")
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0001", "lesion", {"A": 0.5})
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0009", "lesion", {"A": 0.5})  # not in the registry

    _, metadata, _, _, _, excluded_no_mask, _ = _build(tmp_path, _reference(tmp_path, ["A"]))

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_no_mask == ["sub-STUNIPD0009"]


def test_subject_on_the_exclusion_list_is_not_reported_as_missing_a_mask(tmp_path, _metadata_root):
    """Regression for lessons_learned #38: an excluded subject has its mask and its CSV, so it
    must appear only under excluded_by_list."""
    for subject in ("sub-STUNIPD0001", "sub-STUNIPD0002"):
        _register(_metadata_root, "siteA", subject)
        _write_csv(tmp_path, "siteA", subject, "lesion", {"A": 0.5})

    _, metadata, _, _, excluded_by_list, excluded_no_mask, csv_not_yet_computed = _build(
        tmp_path, _reference(tmp_path, ["A"]), excluded=frozenset({"sub-STUNIPD0002"})
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_list == ["sub-STUNIPD0002"]
    assert excluded_no_mask == []
    assert csv_not_yet_computed == []


def test_value_column_missing_from_the_lesion_csv_raises(tmp_path, _metadata_root):
    _register(_metadata_root, "siteA", "sub-STUNIPD0001")
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0001", "lesion", {"A": 0.5})  # has no p90_overlap column

    with pytest.raises(ValueError, match="missing 'p90_overlap' column"):
        _build(tmp_path, _reference(tmp_path, ["A"]), value_column="p90_overlap")


def test_region_unknown_to_the_reference_raises(tmp_path, _metadata_root):
    _register(_metadata_root, "siteA", "sub-STUNIPD0001")
    _write_csv(tmp_path, "siteA", "sub-STUNIPD0001", "lesion", {"A": 0.5, "ZZZ": 0.1})

    with pytest.raises(ValueError, match="not in the reference label set"):
        _build(tmp_path, _reference(tmp_path, ["A"]))
