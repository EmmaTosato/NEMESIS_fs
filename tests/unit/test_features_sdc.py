"""Unit tests for src/features/sdc.py - synthetic CSV fixtures, no real data required."""

import numpy as np
import pytest

from src.features.sdc import build_sdc_matrix, load_reference_regions

_ATLAS = "test_atlas"
_OBJECT = "disconnectome"
_VALUE_COLUMN = "mean_overlap"


def _make_lesion_mask(data_root, dataset, subject_id):
    """Content is irrelevant - build_sdc_matrix only checks the file's existence
    (same as build_lesion_matrix.py's own discovery, reused here) to decide
    whether a subject is admitted, never its content."""
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    (subject_dir / f"{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz").write_bytes(b"dummy")


def _make_sdc_csv(data_root, dataset, subject_id, object_, atlas, rows, value_column=_VALUE_COLUMN):
    """rows: dict[region_name, value]. An empty dict writes a header-only CSV
    (real-world case: BCBToolKit produced zero disconnected regions for this
    subject/atlas - see docs/dev/sdc_matrix.md)."""
    subject_dir = data_root / dataset / "sdc" / subject_id / "dwi"
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"{subject_id}_space-MNI152NLin6Asym_LF-{object_}_atlas-{atlas}.csv"
    lines = [f"region_name,{value_column}"]
    lines += [f"{region},{value}" for region, value in rows.items()]
    path.write_text("\n".join(lines) + "\n")


def _make_reference_labels(path, region_names):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["region_name"] + list(region_names)
    path.write_text("\n".join(lines) + "\n")


def test_build_sdc_matrix_reindexes_missing_regions_to_zero(tmp_path):
    """The core alignment behaviour: BCBToolKit omits regions at zero overlap
    instead of writing them explicitly - reindex must restore them as 0.0,
    not drop the subject or shrink the column count."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B", "C"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5, "C": 0.2})  # B omitted

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0002")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0002", _OBJECT, _ATLAS, {"A": 0.1, "B": 0.9, "C": 0.3})

    X, metadata, region_names, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
    )

    assert list(region_names) == ["A", "B", "C"]
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    np.testing.assert_array_equal(X[0], [0.5, 0.0, 0.2])
    np.testing.assert_array_equal(X[1], [0.1, 0.9, 0.3])
    assert excluded_by_group == []
    assert excluded_no_lesion_mask == []
    assert sdc_not_yet_computed == []


def test_build_sdc_matrix_no_column_dropped_even_if_constant(tmp_path):
    """2026-08-27 project decision: unlike build_lesion_matrix.py's
    _drop_constant_features, a column here always means the same region
    regardless of which subjects a given run includes - no drop, ever."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})  # B always omitted
    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0002")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0002", _OBJECT, _ATLAS, {"A": 0.7})

    X, _, region_names, *_ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
    )

    assert X.shape == (2, 2)  # "B" column kept even though constant at 0.0 across all subjects
    assert list(region_names) == ["A", "B"]


def test_build_sdc_matrix_empty_csv_becomes_zero_vector(tmp_path):
    """A subject with a real lesion mask and a real (but header-only) SDC CSV
    is a legitimate domain case (BCBToolKit found zero disconnected regions),
    distinct from a missing lesion mask (excluded entirely, see next test)."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {})  # header only, no rows

    X, metadata, region_names, *_ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    np.testing.assert_array_equal(X[0], [0.0, 0.0])


def test_build_sdc_matrix_excludes_subject_without_lesion_mask(tmp_path):
    """Real case found in the cohort (sub-STUKLFR0671, docs/dev/sdc_matrix.md):
    a subject with SDC output but no lesion mask is excluded entirely, not
    silently kept as an all-zero row indistinguishable from a genuine
    zero-disconnection observation."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5, "B": 0.1})
    # sub-STUNIPD0002 has SDC output but no lesion mask at all
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0002", _OBJECT, _ATLAS, {"A": 0.9})

    X, metadata, _, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_no_lesion_mask == ["sub-STUNIPD0002"]
    assert sdc_not_yet_computed == []
    assert excluded_by_group == []


def test_build_sdc_matrix_tracks_lesion_mask_without_sdc_yet(tmp_path):
    """A subject with a lesion mask but no SDC file yet (not yet computed
    upstream) is excluded from X and tracked separately - distinct from
    excluded_no_lesion_mask, opposite direction of the gap."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})
    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0002")  # no SDC CSV at all

    X, metadata, _, _, excluded_no_lesion_mask, sdc_not_yet_computed = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_no_lesion_mask == []
    assert sdc_not_yet_computed == ["sub-STUNIPD0002"]


def test_build_sdc_matrix_group_filter_excludes_hc(tmp_path):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})
    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPDHC0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPDHC0001", _OBJECT, _ATLAS, {"A": 0.1})

    X, metadata, _, excluded_by_group, _, _ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=["ST"],
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_group == ["sub-STUNIPDHC0001"]


def test_build_sdc_matrix_unknown_region_raises(tmp_path):
    """A region_name in a subject's CSV that isn't in the reference label set
    is a hard error (atlas mismatch or corrupt file), never silently ignored
    or added as an extra column."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5, "Z": 0.9})  # "Z" unknown

    with pytest.raises(ValueError, match="not in the reference label set"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
        )


def test_build_sdc_matrix_duplicate_region_name_raises(tmp_path):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")
    subject_dir = tmp_path / "siteA" / "sdc" / "sub-STUNIPD0001" / "dwi"
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"sub-STUNIPD0001_space-MNI152NLin6Asym_LF-{_OBJECT}_atlas-{_ATLAS}.csv"
    path.write_text(f"region_name,{_VALUE_COLUMN}\nA,0.5\nA,0.6\n")  # duplicate "A"

    with pytest.raises(ValueError, match="duplicate region_name"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
        )


def test_build_sdc_matrix_invalid_object_raises(tmp_path):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    with pytest.raises(ValueError, match="object_ must be one of"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            object_="not_a_real_object",
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
        )


def test_build_sdc_matrix_invalid_value_column_raises(tmp_path):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    with pytest.raises(ValueError, match="value_column must be one of"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column="not_a_real_column",
            reference_labels_path=reference_path,
            group_filter=None,
        )


def test_build_sdc_matrix_no_admitted_subjects_raises(tmp_path):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    _make_lesion_mask(tmp_path, "siteA", "sub-STUNIPD0001")  # no SDC file for anyone

    with pytest.raises(ValueError, match="no subjects admitted"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            lesion_glob="manual_masks/*/anat/*_label-lesion_mask.nii.gz",
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
        )


def test_load_reference_regions_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="reference_labels_path not found"):
        load_reference_regions(tmp_path / "does_not_exist.csv")


def test_load_reference_regions_duplicate_raises(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("region_name\nA\nA\nB\n")
    with pytest.raises(ValueError, match="duplicate region_name"):
        load_reference_regions(path)


def test_load_reference_regions_valid(tmp_path):
    path = tmp_path / "labels.csv"
    _make_reference_labels(path, ["C", "A", "B"])
    regions = load_reference_regions(path)
    assert list(regions) == ["A", "B", "C"]  # sorted, regardless of file's own row order
