"""Unit tests for src/features/sdc.py - synthetic CSV/TSV fixtures, no real data required."""

import nibabel as nib
import numpy as np
import pytest

from src.utils import participants as participants_registry
from src.features.sdc import (
    build_sdc_matrix,
    build_sdc_streamline_matrix,
    build_sdc_voxelwise_matrix,
    load_reference_regions,
)

_VOXELWISE_AFFINE = np.eye(4) * 2
_VOXELWISE_AFFINE[3, 3] = 1
_VOXELWISE_SHAPE = (4, 4, 4)

_ATLAS = "test_atlas"
_OBJECT = "disconnectome"
_VALUE_COLUMN = "mean_overlap"

_REGISTRY_HEADER = "subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features"


def _register_subject(metadata_root, dataset, subject_id, has_lesion=True):
    """Appends one row to participants.csv - lesion mask presence is resolved
    from this registry, not from disk (see src/features/sdc.py's module
    docstring for why: a local `data/` copy can be a partial retrieval
    sample, this registry is not).

    has_lesion=False registers a subject the registry knows about but which
    has no mask - distinct from a subject absent from the registry entirely.
    """
    metadata_root.mkdir(parents=True, exist_ok=True)
    path = metadata_root / "participants.csv"
    if not path.is_file():
        path.write_text(_REGISTRY_HEADER + "\n")
    with path.open("a") as f:
        f.write(f"{subject_id},{subject_id},{dataset},ST,{has_lesion},True,False\n")


def _register_lesion_mask(metadata_root, dataset, subject_id):
    """Registers a subject that does have a lesion mask."""
    _register_subject(metadata_root, dataset, subject_id, has_lesion=True)


def _make_sdc_csv(data_root, dataset, subject_id, object_, atlas, rows, value_column=_VALUE_COLUMN):
    """rows: dict[region_name, value]. An empty dict writes a header-only CSV
    (real-world case: BCBToolKit produced zero disconnected regions for this
    subject/atlas - see docs/dev/sdc_matrix.md)."""
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"{subject_id}_space-MNI152NLin6Asym_LF-{object_}_atlas-{atlas}.csv"
    lines = [f"region_name,{value_column}"]
    lines += [f"{region},{value}" for region, value in rows.items()]
    path.write_text("\n".join(lines) + "\n")


def _make_reference_labels(path, region_names):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["region_name"] + list(region_names)
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture(autouse=True)
def _metadata_root(tmp_path, monkeypatch):
    """Every test gets its own isolated metadata root - never touches
    the real assets/metadata/."""
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", metadata_root)
    return metadata_root


def test_build_sdc_matrix_reindexes_missing_regions_to_zero(tmp_path, _metadata_root):
    """The core alignment behaviour: BCBToolKit omits regions at zero overlap
    instead of writing them explicitly - reindex must restore them as 0.0,
    not drop the subject or shrink the column count."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B", "C"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5, "C": 0.2})  # B omitted

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0002")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0002", _OBJECT, _ATLAS, {"A": 0.1, "B": 0.9, "C": 0.3})

    X, metadata, region_names, excluded_by_group, _, excluded_no_lesion_mask, sdc_not_yet_computed = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert list(region_names) == ["A", "B", "C"]
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    np.testing.assert_array_equal(X[0], [0.5, 0.0, 0.2])
    np.testing.assert_array_equal(X[1], [0.1, 0.9, 0.3])
    assert excluded_by_group == []
    assert excluded_no_lesion_mask == []
    assert sdc_not_yet_computed == []


def test_build_sdc_matrix_no_column_dropped_even_if_constant(tmp_path, _metadata_root):
    """2026-08-27 project decision: unlike build_lesion_matrix.py's
    _drop_constant_features, a column here always means the same region
    regardless of which subjects a given run includes - no drop, ever."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})  # B always omitted
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0002")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0002", _OBJECT, _ATLAS, {"A": 0.7})

    X, _, region_names, *_ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert X.shape == (2, 2)  # "B" column kept even though constant at 0.0 across all subjects
    assert list(region_names) == ["A", "B"]


def test_build_sdc_matrix_empty_csv_becomes_zero_vector(tmp_path, _metadata_root):
    """A subject with a registered lesion mask and a real (but header-only)
    SDC CSV is a legitimate domain case (BCBToolKit found zero disconnected
    regions), distinct from a missing lesion mask (excluded entirely, see
    next test)."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {})  # header only, no rows

    X, metadata, region_names, *_ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    np.testing.assert_array_equal(X[0], [0.0, 0.0])


def test_build_sdc_matrix_excludes_subject_without_lesion_mask(tmp_path, _metadata_root):
    """Real case confirmed in the cohort (sub-STUKLFR0005, absent from
    has_lesion=False in participants.csv - docs/dev/sdc_matrix.md):
    a subject with SDC output but no lesion mask registered in the
    registry is excluded entirely, not silently kept as an all-zero
    row indistinguishable from a genuine zero-disconnection observation."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5, "B": 0.1})
    # sub-STUNIPD0002 has SDC output but is never registered as having a lesion mask
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0002", _OBJECT, _ATLAS, {"A": 0.9})

    X, metadata, _, excluded_by_group, _, excluded_no_lesion_mask, sdc_not_yet_computed = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_no_lesion_mask == ["sub-STUNIPD0002"]
    assert sdc_not_yet_computed == []
    assert excluded_by_group == []


def test_build_sdc_matrix_tracks_lesion_mask_without_sdc_yet(tmp_path, _metadata_root):
    """A subject registered with a lesion mask but no SDC file yet (not yet
    computed upstream) is excluded from X and tracked separately - distinct
    from excluded_no_lesion_mask, opposite direction of the gap."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0002")  # no SDC CSV at all

    X, metadata, _, _, _, excluded_no_lesion_mask, sdc_not_yet_computed = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_no_lesion_mask == []
    assert sdc_not_yet_computed == ["sub-STUNIPD0002"]


def test_build_sdc_matrix_group_filter_excludes_hc(tmp_path, _metadata_root):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPDHC0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPDHC0001", _OBJECT, _ATLAS, {"A": 0.1})

    X, metadata, _, excluded_by_group, _, _, _ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=["ST"],
        excluded_subjects=frozenset(),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_group == ["sub-STUNIPDHC0001"]


def test_build_sdc_matrix_missing_registry_raises(tmp_path, _metadata_root):
    """No participants.csv at all is a real configuration problem (registry
    never generated by src/pipeline/populate_metadata.py) - never silently
    treated as "zero subjects have a lesion mask"."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})

    with pytest.raises(FileNotFoundError, match="subject registry not found"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_matrix_dataset_absent_from_registry_raises(tmp_path, _metadata_root):
    """A structural gap in the registry this pipeline depends on for its core
    admission criterion: the registry exists but knows nothing about the
    requested dataset (typo'd name, or genuinely not onboarded yet) - never
    silently treated as "nobody in that dataset has a lesion mask"."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    _register_lesion_mask(_metadata_root, "siteB", "sub-STUNIPD0002")  # registry exists, siteA absent
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})

    with pytest.raises(ValueError, match="no row in the subject registry"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_matrix_unknown_region_raises(tmp_path, _metadata_root):
    """A region_name in a subject's CSV that isn't in the reference label set
    is a hard error (atlas mismatch or corrupt file), never silently ignored
    or added as an extra column."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5, "Z": 0.9})  # "Z" unknown

    with pytest.raises(ValueError, match="not in the reference label set"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_matrix_duplicate_region_name_raises(tmp_path, _metadata_root):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A", "B"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    subject_dir = tmp_path / "siteA" / "sdc" / "sub-STUNIPD0001"
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"sub-STUNIPD0001_space-MNI152NLin6Asym_LF-{_OBJECT}_atlas-{_ATLAS}.csv"
    path.write_text(f"region_name,{_VALUE_COLUMN}\nA,0.5\nA,0.6\n")  # duplicate "A"

    with pytest.raises(ValueError, match="duplicate region_name"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_matrix_invalid_object_raises(tmp_path, _metadata_root):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    with pytest.raises(ValueError, match="object_ must be one of"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="not_a_real_object",
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_matrix_invalid_value_column_raises(tmp_path, _metadata_root):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    with pytest.raises(ValueError, match="value_column must be one of"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column="not_a_real_column",
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_matrix_no_admitted_subjects_raises(tmp_path, _metadata_root):
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")  # no SDC file for anyone

    with pytest.raises(ValueError, match="no subjects admitted"):
        build_sdc_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_=_OBJECT,
            atlas=_ATLAS,
            value_column=_VALUE_COLUMN,
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
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


# --- build_sdc_voxelwise_matrix (added 03/09) ---------------------------------


def _make_disconnectome_map(data_root, dataset, subject_id, volume, affine=_VOXELWISE_AFFINE):
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
    nib.save(nib.Nifti1Image(volume.astype(np.float32), affine), path)


def _make_voxelwise_reference_template(path):
    nib.save(nib.Nifti1Image(np.zeros(_VOXELWISE_SHAPE, dtype=np.float32), _VOXELWISE_AFFINE), path)


def test_build_sdc_voxelwise_matrix_preserves_continuous_values(tmp_path, _metadata_root):
    """Core difference from build_lesion_matrix.py: disconnection probability
    is never binarized - the exact float value on disk must survive into X."""
    template_path = tmp_path / "reference_template.nii.gz"
    _make_voxelwise_reference_template(template_path)

    volume1 = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
    volume1[1, 1, 1] = 0.75
    volume1[2, 2, 2] = 0.25
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_disconnectome_map(tmp_path, "siteA", "sub-STUNIPD0001", volume1)

    volume2 = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
    volume2[1, 1, 1] = 0.10
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0002")
    _make_disconnectome_map(tmp_path, "siteA", "sub-STUNIPD0002", volume2)

    X, metadata, non_constant_mask, excluded_by_group, _, excluded_no_lesion_mask, sdc_not_yet_computed = (
        build_sdc_voxelwise_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="disconnectome",
            reference_template_path=template_path,
            resample_interpolation="nearest",
            group_filter=None,
            excluded_subjects=frozenset(),
        )
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    # 2 non-constant voxels survive the drop (voxel[1,1,1] varies 0.75/0.10, voxel[2,2,2]
    # varies 0.25/0.0) - every other voxel is 0.0 for both subjects and gets dropped.
    assert X.shape == (2, 2)
    assert non_constant_mask.sum() == 2
    np.testing.assert_allclose(np.sort(X[0]), sorted([0.75, 0.25]))
    np.testing.assert_allclose(np.sort(X[1]), sorted([0.10, 0.0]))
    assert excluded_by_group == []
    assert excluded_no_lesion_mask == []
    assert sdc_not_yet_computed == []


def test_build_sdc_voxelwise_matrix_resamples_when_grid_differs(tmp_path, _metadata_root):
    template_path = tmp_path / "reference_template.nii.gz"
    _make_voxelwise_reference_template(template_path)

    # A subject whose disconnectome-map sits on a different (finer) grid than the
    # reference - must be resampled onto the reference grid before stacking, exactly
    # like src/features/lesion.py's voxel-wise path.
    fine_affine = np.eye(4)
    fine_affine[3, 3] = 1
    fine_volume = np.full((8, 8, 8), 0.5, dtype=np.float32)
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_disconnectome_map(tmp_path, "siteA", "sub-STUNIPD0001", fine_volume, affine=fine_affine)

    volume2 = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0002")
    _make_disconnectome_map(tmp_path, "siteA", "sub-STUNIPD0002", volume2)

    X, metadata, *_ = build_sdc_voxelwise_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_="disconnectome",
        reference_template_path=template_path,
        resample_interpolation="continuous",
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    assert X.shape[0] == 2
    # Resampled onto the 4x4x4 reference grid, not left at its native 8x8x8 shape.
    assert X.shape[1] <= 4 * 4 * 4


def test_build_sdc_voxelwise_matrix_excludes_subject_without_lesion_mask(tmp_path, _metadata_root):
    template_path = tmp_path / "reference_template.nii.gz"
    _make_voxelwise_reference_template(template_path)

    volume = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
    volume[0, 0, 0] = 0.5
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_disconnectome_map(tmp_path, "siteA", "sub-STUNIPD0001", volume)
    # sub-STUNIPD0002 has SDC output but is never registered as having a lesion mask
    _make_disconnectome_map(tmp_path, "siteA", "sub-STUNIPD0002", volume)

    X, metadata, _, excluded_by_group, _, excluded_no_lesion_mask, sdc_not_yet_computed = build_sdc_voxelwise_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_="disconnectome",
        reference_template_path=template_path,
        resample_interpolation="nearest",
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_no_lesion_mask == ["sub-STUNIPD0002"]
    assert sdc_not_yet_computed == []
    assert excluded_by_group == []


def test_build_sdc_voxelwise_matrix_object_lesion_raises(tmp_path, _metadata_root):
    """Deliberately restricted to object_='disconnectome' (see module
    docstring) - the lesion-map equivalent is build_lesion_matrix.py's job,
    from its own authoritative manual_masks/ source."""
    template_path = tmp_path / "reference_template.nii.gz"
    _make_voxelwise_reference_template(template_path)

    with pytest.raises(ValueError, match="object_ must be one of"):
        build_sdc_voxelwise_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="lesion",
            reference_template_path=template_path,
            resample_interpolation="nearest",
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_voxelwise_matrix_no_admitted_subjects_raises(tmp_path, _metadata_root):
    template_path = tmp_path / "reference_template.nii.gz"
    _make_voxelwise_reference_template(template_path)
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")  # no SDC file for anyone

    with pytest.raises(ValueError, match="no subjects admitted"):
        build_sdc_voxelwise_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="disconnectome",
            reference_template_path=template_path,
            resample_interpolation="nearest",
            group_filter=None,
            excluded_subjects=frozenset(),
        )


# --- the shared hand-curated exclusion list ------------------------------------------------------


def test_build_sdc_matrix_applies_the_excluded_subjects_list(tmp_path, _metadata_root):
    """The same list src.features.lesion applies, resolved in the one place BOTH SDC
    representations share (_subjects_with_lesion_mask). Without this, a lesion-vs-SDC comparison
    would silently compare two different cohorts."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])

    for subject_id, value in (("sub-STUNIPD0001", 0.5), ("sub-STUNIPD0002", 0.2)):
        _register_lesion_mask(_metadata_root, "siteA", subject_id)
        _make_sdc_csv(tmp_path, "siteA", subject_id, _OBJECT, _ATLAS, {"A": value})

    X, metadata, _, excluded_by_group, excluded_by_list, _, _ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset({"sub-STUNIPD0002"}),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_list == ["sub-STUNIPD0002"]
    assert excluded_by_group == []
    assert X.shape[0] == 1


def test_build_sdc_voxelwise_matrix_applies_the_excluded_subjects_list(tmp_path, _metadata_root):
    """Both representations go through the same admission pass, so the list cannot apply to one
    and not the other - asserted for the voxelwise builder too rather than assumed."""
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_VOXELWISE_SHAPE, dtype=np.float32), _VOXELWISE_AFFINE), template_path)

    for subject_id, value in (("sub-STUNIPD0001", 0.5), ("sub-STUNIPD0002", 0.2)):
        volume = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
        volume[1, 1, 1] = value
        _register_lesion_mask(_metadata_root, "siteA", subject_id)
        _make_disconnectome_map(tmp_path, "siteA", subject_id, volume)

    X, metadata, _, _, excluded_by_list, _, _ = build_sdc_voxelwise_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_="disconnectome",
        reference_template_path=template_path,
        resample_interpolation="nearest",
        group_filter=None,
        excluded_subjects=frozenset({"sub-STUNIPD0002"}),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_list == ["sub-STUNIPD0002"]
    assert X.shape[0] == 1


def test_excluded_subject_out_of_group_is_reported_as_group_not_list(tmp_path, _metadata_root):
    """A subject excluded by group_filter must never also appear in excluded_by_list: the same
    subject counted twice would make the two exclusion tallies in the run report overlap, so
    "why does this matrix have N subjects" stops adding up."""
    reference_path = tmp_path / "labels.csv"
    _make_reference_labels(reference_path, ["A"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPD0001", _OBJECT, _ATLAS, {"A": 0.5})
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPDHC0001")
    _make_sdc_csv(tmp_path, "siteA", "sub-STUNIPDHC0001", _OBJECT, _ATLAS, {"A": 0.1})

    _, metadata, _, excluded_by_group, excluded_by_list, _, _ = build_sdc_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_=_OBJECT,
        atlas=_ATLAS,
        value_column=_VALUE_COLUMN,
        reference_labels_path=reference_path,
        group_filter=["ST"],
        excluded_subjects=frozenset({"sub-STUNIPDHC0001"}),
    )

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_by_group == ["sub-STUNIPDHC0001"]
    assert excluded_by_list == []


# --- build_sdc_streamline_matrix (added 30/09) --------------------------------

_STREAMLINE_ATLAS_SUFFIX = "yeh_hcp1065_streamline"


def _make_streamline_csv(data_root, dataset, subject_id, rows, object_="lesion"):
    """rows: dict[tract, streamline_ratio]. Unlike _make_sdc_csv, a real file
    always lists every tract (zeros included) - an incomplete dict here is the
    corrupt-file case, not an omitted zero."""
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    path = subject_dir / f"{subject_id}_space-MNI152NLin6Asym_LF-{object_}_atlas-{_STREAMLINE_ATLAS_SUFFIX}.csv"
    lines = ["tract,streamline_ratio"] + [f"{tract},{value}" for tract, value in rows.items()]
    path.write_text("\n".join(lines) + "\n")


def _make_reference_tracts(path, tract_names):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(["tract"] + list(tract_names)) + "\n")


def test_build_sdc_streamline_matrix_aligns_by_tract_name_not_row_order(tmp_path, _metadata_root):
    """The two subjects' CSVs list the same tracts in a different order: X must
    be aligned by name, so column j means the same tract for both rows."""
    reference_path = tmp_path / "tracts.csv"
    _make_reference_tracts(reference_path, ["AF_L", "AF_R", "CST_L"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0001", {"AF_L": 0.5, "AF_R": 0.0, "CST_L": 0.25})
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0002")
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0002", {"CST_L": 0.75, "AF_L": 0.1, "AF_R": 1.0})

    X, metadata, tract_names, *_ = build_sdc_streamline_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_="lesion",
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert list(tract_names) == ["AF_L", "AF_R", "CST_L"]
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    np.testing.assert_allclose(X, [[0.5, 0.0, 0.25], [0.1, 1.0, 0.75]])


def test_build_sdc_streamline_matrix_missing_tract_raises(tmp_path, _metadata_root):
    """The deliberate difference from build_sdc_matrix: a tract absent from the
    CSV is a truncated/corrupt file, never filled with 0.0 - this file writes
    every tract explicitly (verified on all 1734 real files, 30/09)."""
    reference_path = tmp_path / "tracts.csv"
    _make_reference_tracts(reference_path, ["AF_L", "AF_R", "CST_L"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0001", {"AF_L": 0.5, "CST_L": 0.25})  # AF_R missing

    with pytest.raises(ValueError, match="AF_R"):
        build_sdc_streamline_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="lesion",
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_streamline_matrix_unknown_tract_raises(tmp_path, _metadata_root):
    reference_path = tmp_path / "tracts.csv"
    _make_reference_tracts(reference_path, ["AF_L", "AF_R"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0001", {"AF_L": 0.5, "AF_R": 0.1, "ZZZ": 0.9})

    with pytest.raises(ValueError, match="ZZZ"):
        build_sdc_streamline_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="lesion",
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_streamline_matrix_no_column_dropped_even_if_constant(tmp_path, _metadata_root):
    """Same rule as build_sdc_matrix: column j always names the same tract,
    regardless of which subjects a run admits."""
    reference_path = tmp_path / "tracts.csv"
    _make_reference_tracts(reference_path, ["AF_L", "AF_R"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0001", {"AF_L": 0.5, "AF_R": 0.0})
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0002")
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0002", {"AF_L": 0.7, "AF_R": 0.0})

    X, _, tract_names, *_ = build_sdc_streamline_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_="lesion",
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert X.shape == (2, 2)
    assert list(tract_names) == ["AF_L", "AF_R"]


def test_build_sdc_streamline_matrix_object_disconnectome_raises(tmp_path, _metadata_root):
    """BCBToolKit writes this CSV only in the LF-lesion family - there is no
    LF-disconnectome variant to read."""
    reference_path = tmp_path / "tracts.csv"
    _make_reference_tracts(reference_path, ["AF_L"])

    with pytest.raises(ValueError, match="lesion"):
        build_sdc_streamline_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="disconnectome",
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )


def test_build_sdc_streamline_matrix_excludes_subject_without_lesion_mask(tmp_path, _metadata_root):
    reference_path = tmp_path / "tracts.csv"
    _make_reference_tracts(reference_path, ["AF_L"])

    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0001", {"AF_L": 0.5})
    _make_streamline_csv(tmp_path, "siteA", "sub-STUNIPD0002", {"AF_L": 0.9})  # never registered

    X, metadata, _, _, _, excluded_no_lesion_mask, _ = build_sdc_streamline_matrix(
        data_root=tmp_path,
        datasets=["siteA"],
        object_="lesion",
        reference_labels_path=reference_path,
        group_filter=None,
        excluded_subjects=frozenset(),
    )

    assert X.shape[0] == 1
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded_no_lesion_mask == ["sub-STUNIPD0002"]


def test_build_sdc_streamline_matrix_no_admitted_subjects_raises(tmp_path, _metadata_root):
    reference_path = tmp_path / "tracts.csv"
    _make_reference_tracts(reference_path, ["AF_L"])
    _register_lesion_mask(_metadata_root, "siteA", "sub-STUNIPD0001")  # no streamline CSV at all

    with pytest.raises(ValueError, match="no subjects admitted"):
        build_sdc_streamline_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="lesion",
            reference_labels_path=reference_path,
            group_filter=None,
            excluded_subjects=frozenset(),
        )
