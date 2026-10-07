"""Unit tests for src/features/sdc.py - synthetic CSV/TSV fixtures, no real data required."""

import tracemalloc

import nibabel as nib
import numpy as np
import pytest

from src.utils import participants as participants_registry
from src.features.lesion import LesionGrid
from src.features.sdc import (
    build_sdc_matrix,
    build_sdc_streamline_matrix,
    build_sdc_voxelwise_matrix,
    compute_sdc_metadata,
    load_reference_regions,
)

_VOXELWISE_AFFINE = np.eye(4) * 2
_VOXELWISE_AFFINE[3, 3] = 1
_VOXELWISE_SHAPE = (4, 4, 4)

_ATLAS = "test_atlas"
_OBJECT = "disconnectome"
_VALUE_COLUMN = "mean_overlap"

_REGISTRY_HEADER = "subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features"


def _register_subject(metadata_root, dataset, subject_id, has_lesion=True, has_sdc=True):
    """Appends one row to participants.csv - lesion mask presence is resolved
    from this registry, not from disk (see src/features/sdc.py's module
    docstring for why: a local `data/` copy can be a partial local
    sample, this registry is not).

    has_lesion=False registers a subject the registry knows about but which
    has no mask - distinct from a subject absent from the registry entirely.
    """
    metadata_root.mkdir(parents=True, exist_ok=True)
    path = metadata_root / "participants.csv"
    if not path.is_file():
        path.write_text(_REGISTRY_HEADER + "\n")
    with path.open("a") as f:
        f.write(f"{subject_id},{subject_id},{dataset},ST,{has_lesion},{has_sdc},False\n")


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


def _build_voxelwise(tmp_path, template_path):
    return build_sdc_voxelwise_matrix(
        data_root=tmp_path,
        datasets=["siteA", "siteB"],
        object_="disconnectome",
        reference_template_path=template_path,
        resample_interpolation="nearest",
        group_filter=None,
        excluded_subjects=frozenset(),
    )


def test_build_sdc_voxelwise_matrix_matches_stack_then_drop_constant_columns(tmp_path, _metadata_root):
    """The two-pass build must give exactly what stacking every map and dropping the columns where
    min == max gives, on the cases where a shortcut would diverge: a voxel constant but non-zero
    (dropped), nonzero in one subject only (kept), NaN in one subject (kept: NaN != NaN), NaN in
    all subjects (kept), and subjects registered out of order across two datasets (rows sorted)."""
    template_path = tmp_path / "reference_template.nii.gz"
    _make_voxelwise_reference_template(template_path)
    rng = np.random.default_rng(0)
    volumes = {}
    for dataset, subject_id in [("siteB", "sub-STUNIPD0003"), ("siteA", "sub-STUNIPD0002"), ("siteA", "sub-STUNIPD0001"), ("siteB", "sub-STUNIPD0004")]:
        volume = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
        volume[0, 0, 0] = 0.5
        volume[1, 1, 1] = rng.random()
        volume[3, 3, 3] = np.nan
        if subject_id == "sub-STUNIPD0004":
            volume[2, 2, 2] = 0.9
            volume[0, 1, 0] = np.nan
        _register_lesion_mask(_metadata_root, dataset, subject_id)
        _make_disconnectome_map(tmp_path, dataset, subject_id, volume)
        volumes[(dataset, subject_id)] = volume

    X, metadata, non_constant_mask, *_ = _build_voxelwise(tmp_path, template_path)

    ordered = sorted(volumes)
    stacked = np.stack([volumes[key].ravel() for key in ordered])
    expected_mask = stacked.min(axis=0) != stacked.max(axis=0)
    assert list(metadata["subject_id"]) == [subject_id for _, subject_id in ordered]
    assert list(metadata["dataset"]) == [dataset for dataset, _ in ordered]
    np.testing.assert_array_equal(non_constant_mask, expected_mask)
    assert non_constant_mask.sum() == 4  # (1,1,1), (2,2,2), (0,1,0), (3,3,3); not the constant 0.5 nor zeros
    assert X.dtype == np.float32
    np.testing.assert_array_equal(X, stacked[:, expected_mask])


def test_build_sdc_voxelwise_matrix_never_holds_the_full_voxel_matrix_in_memory(tmp_path, _metadata_root):
    """Regression: the build used to stack every subject's full-grid vector before dropping the
    constant voxels, so its peak was about twice the full n_subjects x n_grid_voxels matrix
    (~42 GB for 5845 subjects on the 2mm grid) even though only a third of the columns are kept.
    Only 1% of the voxels vary here, so the peak must stay far below the full matrix."""
    shape = (40, 40, 40)
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(shape, dtype=np.float32), _VOXELWISE_AFFINE), template_path)
    n_subjects = 60
    rng = np.random.default_rng(0)
    varying = rng.choice(np.prod(shape), size=int(0.01 * np.prod(shape)), replace=False)
    for i in range(n_subjects):
        subject_id = f"sub-STUNIPD{i:04d}"
        volume = np.zeros(np.prod(shape), dtype=np.float32)
        volume[varying] = rng.random(varying.size)
        _register_lesion_mask(_metadata_root, "siteA", subject_id)
        _make_disconnectome_map(tmp_path, "siteA", subject_id, volume.reshape(shape))

    tracemalloc.start()
    try:
        X, *_ = build_sdc_voxelwise_matrix(
            data_root=tmp_path,
            datasets=["siteA"],
            object_="disconnectome",
            reference_template_path=template_path,
            resample_interpolation="nearest",
            group_filter=None,
            excluded_subjects=frozenset(),
        )
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    full_matrix_bytes = n_subjects * np.prod(shape) * 4
    assert X.shape == (n_subjects, varying.size)
    assert peak_bytes < full_matrix_bytes / 2


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


# --- a subject on the exclusion list is not "missing its lesion mask" ------------


def test_excluded_subject_is_not_also_reported_as_missing_its_lesion_mask(tmp_path, _metadata_root):
    """The exclusion list removes a subject from the lesion-mask set on purpose, so a naive
    `sdc_ids - lesion_ids` re-reported it under "SDC output present but no lesion mask" - false,
    it has the mask. Asserted for all three builders (the same line was copy-pasted into each)."""
    labels = tmp_path / "labels.csv"
    _make_reference_labels(labels, ["A"])
    tracts = tmp_path / "tracts.csv"
    _make_reference_tracts(tracts, ["AF_L"])
    template = tmp_path / "reference_template.nii.gz"
    _make_voxelwise_reference_template(template)

    for subject_id in ("sub-STUNIPD0001", "sub-STUNIPD0002"):
        _register_lesion_mask(_metadata_root, "siteA", subject_id)
        _make_sdc_csv(tmp_path, "siteA", subject_id, _OBJECT, _ATLAS, {"A": 0.5})
        _make_streamline_csv(tmp_path, "siteA", subject_id, {"AF_L": 0.5})
        volume = np.zeros(_VOXELWISE_SHAPE, dtype=np.float32)
        volume[0, 0, 0] = 0.5 if subject_id.endswith("1") else 0.2
        _make_disconnectome_map(tmp_path, "siteA", subject_id, volume)

    common = dict(data_root=tmp_path, datasets=["siteA"], group_filter=None,
                  excluded_subjects=frozenset({"sub-STUNIPD0002"}))
    results = {
        "parcellated": build_sdc_matrix(
            object_=_OBJECT, atlas=_ATLAS, value_column=_VALUE_COLUMN, reference_labels_path=labels, **common),
        "voxelwise": build_sdc_voxelwise_matrix(
            object_=_OBJECT, reference_template_path=template, resample_interpolation="nearest", **common),
        "streamline": build_sdc_streamline_matrix(
            object_="lesion", reference_labels_path=tracts, **common),
    }

    for name, (_, _, _, _, excluded_by_list, excluded_no_lesion_mask, _) in results.items():
        assert excluded_by_list == ["sub-STUNIPD0002"], name
        assert excluded_no_lesion_mask == [], name


# --- compute_sdc_metadata ---------------------------------------------------------------------------
#
# The reference lattice is RAS with world x = i - 2 (so x in {-2, -1, 0, 1}), and the brain mask keeps
# only world x >= 0 (i >= 2): asymmetric in x on purpose, so a map that lands on the wrong lattice
# changes the in-brain sum instead of cancelling out.

_METADATA_SHAPE = (4, 4, 4)
_REFERENCE_AFFINE = np.array(
    [[1.0, 0.0, 0.0, -2.0], [0.0, 1.0, 0.0, -2.0], [0.0, 0.0, 1.0, -2.0], [0.0, 0.0, 0.0, 1.0]]
)
_GLOB = "sdc/*/*_res-1_desc-disconnectome.nii.gz"
_DATASET = "UNIPD/WashU"


def _metadata_grid(tmp_path, brain_x_from_index=2):
    template = tmp_path / "template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_METADATA_SHAPE, dtype=np.float32), _REFERENCE_AFFINE), template)
    brain = np.zeros(_METADATA_SHAPE, dtype=np.float32)
    brain[brain_x_from_index:] = 1.0
    brain_path = tmp_path / "brain_mask.nii.gz"
    nib.save(nib.Nifti1Image(brain, _REFERENCE_AFFINE), brain_path)
    return LesionGrid("1mm", template, brain_path)


def _affine_with_x(sign, offset):
    affine = _REFERENCE_AFFINE.copy()
    affine[0, 0] = sign
    affine[0, 3] = offset
    return affine


def _make_disconnectome(data_root, subject_id, voxels, affine=_REFERENCE_AFFINE, dataset=_DATASET):
    """voxels: {(i, j, k): probability} in the FILE's own index space."""
    subject_dir = data_root / dataset / "sdc" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_METADATA_SHAPE, dtype=np.float32)
    for index, probability in voxels.items():
        volume[index] = probability
    nib.save(
        nib.Nifti1Image(volume, affine), subject_dir / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
    )


def _compute(tmp_path, data_root, datasets=(_DATASET,), group_filter=("ST",), grids=None):
    return compute_sdc_metadata(
        data_root, list(datasets), _GLOB, "nearest", None if group_filter is None else list(group_filter),
        grids or [_metadata_grid(tmp_path)],
    )


def test_compute_sdc_metadata_sums_probability_inside_the_brain_and_divides_by_brain_voxels(tmp_path, _metadata_root):
    data_root = tmp_path / "data"
    # i=2 and i=3 are inside the brain (x >= 0); i=1 is outside and must not count.
    _make_disconnectome(data_root, "sub-STUNIPD0002", {(2, 2, 2): 0.5, (3, 2, 2): 0.25, (1, 2, 2): 0.9})
    _make_disconnectome(data_root, "sub-STUNIPD0001", {(2, 0, 0): 1.0})
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0002")

    metadata, excluded = _compute(tmp_path, data_root)

    assert list(metadata.columns) == ["subject_id", "dataset", "disconnection_load_voxels_1mm", "disconnection_mean_1mm"]
    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]  # sorted within a dataset
    assert excluded == []
    n_brain = 2 * 4 * 4
    by_id = metadata.set_index("subject_id")
    assert by_id.loc["sub-STUNIPD0001", "disconnection_load_voxels_1mm"] == 1.0
    assert by_id.loc["sub-STUNIPD0002", "disconnection_load_voxels_1mm"] == 0.75
    assert by_id.loc["sub-STUNIPD0002", "disconnection_mean_1mm"] == 0.75 / n_brain


@pytest.mark.parametrize(
    "affine, blob_a, blob_b",
    [
        pytest.param(_REFERENCE_AFFINE, (2, 2, 2), (1, 2, 2), id="reference-lattice"),
        # LAS (x = 1 - i), the header 4370 real subjects carry: the same physical voxels sit at
        # mirrored indices.
        pytest.param(_affine_with_x(-1.0, 1.0), (1, 2, 2), (2, 2, 2), id="las-mirrored"),
        # RAS shifted by one voxel (x = i - 1), the header of another 1032 real subjects.
        pytest.param(_affine_with_x(1.0, -1.0), (1, 2, 2), (0, 2, 2), id="ras-shifted-one-voxel"),
    ],
)
def test_compute_sdc_metadata_realigns_every_map_with_its_own_header(tmp_path, _metadata_root, affine, blob_a, blob_b):
    """Regression: the real disconnectome maps sit on 3 distinct voxel lattices (by dataset), so
    the SAME physical content is stored at different array indices. blob A (prob 0.5) is at world
    x = 0, inside the brain; blob B (0.25) at world x = -1, outside. Every header must give 0.5.

    Fails for the two shortcuts that look plausible: reading the array by index (LAS gives 0.25,
    the shifted lattice 0.0) and flipping every map unconditionally (mirrors the reference-lattice
    file and the shifted one)."""
    data_root = tmp_path / "data"
    _make_disconnectome(data_root, "sub-STUNIPD0001", {blob_a: 0.5, blob_b: 0.25}, affine=affine)
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")

    metadata, _ = _compute(tmp_path, data_root)

    assert metadata.loc[0, "disconnection_load_voxels_1mm"] == 0.5


def test_compute_sdc_metadata_excludes_group_filtered_subjects_and_reports_them(tmp_path, _metadata_root):
    data_root = tmp_path / "data"
    for subject_id in ("sub-STUNIPD0001", "sub-STUNIPDHC0001"):
        _make_disconnectome(data_root, subject_id, {(2, 2, 2): 0.5})
        _register_subject(_metadata_root, _DATASET, subject_id)

    metadata, excluded = _compute(tmp_path, data_root, group_filter=("ST",))

    assert list(metadata["subject_id"]) == ["sub-STUNIPD0001"]
    assert excluded == ["sub-STUNIPDHC0001"]


def test_compute_sdc_metadata_raises_when_the_registry_flags_a_subject_with_no_map(tmp_path, _metadata_root):
    data_root = tmp_path / "data"
    _make_disconnectome(data_root, "sub-STUNIPD0001", {(2, 2, 2): 0.5})
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0002")  # flagged has_sdc, nothing on disk

    with pytest.raises(ValueError, match=r"have no file matching.*sub-STUNIPD0002"):
        _compute(tmp_path, data_root)


def test_compute_sdc_metadata_raises_when_a_map_exists_for_a_subject_the_registry_does_not_flag(tmp_path, _metadata_root):
    data_root = tmp_path / "data"
    _make_disconnectome(data_root, "sub-STUNIPD0001", {(2, 2, 2): 0.5})
    _make_disconnectome(data_root, "sub-STUNIPD0002", {(2, 2, 2): 0.5})
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0002", has_sdc=False)

    with pytest.raises(ValueError, match=r"not flagged.*populate_metadata"):
        _compute(tmp_path, data_root)


def test_compute_sdc_metadata_reports_every_disagreeing_dataset_in_one_error(tmp_path, _metadata_root):
    data_root = tmp_path / "data"
    for dataset, subject_id in ((_DATASET, "sub-STUNIPD0001"), ("UNIPD/PSP", "sub-STUNIPD0101")):
        _register_subject(_metadata_root, dataset, subject_id)  # flagged, no map on disk

    with pytest.raises(ValueError) as exc_info:
        _compute(tmp_path, data_root, datasets=(_DATASET, "UNIPD/PSP"))

    assert _DATASET in str(exc_info.value) and "UNIPD/PSP" in str(exc_info.value)


@pytest.mark.parametrize("bad_value", [50.0, -0.1, float("nan")])
def test_compute_sdc_metadata_rejects_a_map_that_is_not_a_unit_probability(tmp_path, _metadata_root, bad_value):
    """A percent-scale map (0-100) would sum ~100x too large and pass every other check."""
    data_root = tmp_path / "data"
    _make_disconnectome(data_root, "sub-STUNIPD0001", {(2, 2, 2): bad_value})
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")

    with pytest.raises(ValueError, match="not a \\[0, 1\\] probability"):
        _compute(tmp_path, data_root)


def test_compute_sdc_metadata_unknown_dataset_raises(tmp_path, _metadata_root):
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")

    with pytest.raises(ValueError, match="no row in the subject registry"):
        _compute(tmp_path, tmp_path / "data", datasets=("UNIPD/Typo",))


def test_compute_sdc_metadata_raises_when_nothing_is_in_scope(tmp_path, _metadata_root):
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001", has_sdc=False)

    with pytest.raises(ValueError, match="no subjects measured"):
        _compute(tmp_path, tmp_path / "data")


def test_compute_sdc_metadata_raises_on_an_empty_brain_mask(tmp_path, _metadata_root):
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")
    grid = _metadata_grid(tmp_path, brain_x_from_index=4)  # slice(4, None) of a 4-wide axis: empty

    with pytest.raises(ValueError, match="no voxel inside it"):
        _compute(tmp_path, tmp_path / "data", grids=[grid])


def test_compute_sdc_metadata_zero_disconnection_is_a_value_not_an_error(tmp_path, _metadata_root):
    """A subject whose in-brain map is all zero measures 0.0: the quantity is well-defined (no
    disconnection), unlike the lesion side of an empty mask. The log-scaled colour mode draws
    it as missing; the CSV keeps the honest number."""
    data_root = tmp_path / "data"
    _make_disconnectome(data_root, "sub-STUNIPD0001", {(1, 2, 2): 0.7})  # only outside the brain
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")

    metadata, _ = _compute(tmp_path, data_root)

    assert metadata.loc[0, "disconnection_load_voxels_1mm"] == 0.0
    assert metadata.loc[0, "disconnection_mean_1mm"] == 0.0


def _coarse_grid(tmp_path):
    """A 2x2x2 grid with 2-unit voxels whose centres are world x/y/z in {-2, 0} - exactly the
    even-indexed voxels of the 4x4x4 reference lattice, so "nearest" keeps source voxels i/j/k in
    {0, 2} and drops the odd ones. Its brain mask keeps world x >= 0 (index 1 on the x axis)."""
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    affine[:3, 3] = -2.0
    template = tmp_path / "template_2mm.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros((2, 2, 2), dtype=np.float32), affine), template)
    brain = np.zeros((2, 2, 2), dtype=np.float32)
    brain[1:] = 1.0
    brain_path = tmp_path / "brain_mask_2mm.nii.gz"
    nib.save(nib.Nifti1Image(brain, affine), brain_path)
    return LesionGrid("2mm", template, brain_path)


def test_compute_sdc_metadata_writes_two_columns_per_grid_in_declaration_order(tmp_path, _metadata_root):
    data_root = tmp_path / "data"
    _make_disconnectome(data_root, "sub-STUNIPD0001", {(2, 2, 2): 0.5})
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")

    metadata, _ = _compute(tmp_path, data_root, grids=[_coarse_grid(tmp_path), _metadata_grid(tmp_path)])

    assert list(metadata.columns) == [
        "subject_id", "dataset",
        "disconnection_load_voxels_2mm", "disconnection_mean_2mm",
        "disconnection_load_voxels_1mm", "disconnection_mean_1mm",
    ]


def test_compute_sdc_metadata_each_grid_is_its_own_measurement_not_a_rescaling(tmp_path, _metadata_root):
    """On the coarse grid "nearest" is a subsample: of the two in-brain blobs (0.5 at i=2 and 0.25
    at i=3) only the one on an even index is sampled, so the 2mm load is 0.5 - not the 1mm load
    (0.75) divided by 8. The means divide by each grid's own brain-voxel count (4 vs 32)."""
    data_root = tmp_path / "data"
    _make_disconnectome(data_root, "sub-STUNIPD0001", {(2, 2, 2): 0.5, (3, 2, 2): 0.25})
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")

    metadata, _ = _compute(tmp_path, data_root, grids=[_metadata_grid(tmp_path), _coarse_grid(tmp_path)])

    row = metadata.iloc[0]
    assert row["disconnection_load_voxels_1mm"] == 0.75
    assert row["disconnection_mean_1mm"] == 0.75 / 32
    assert row["disconnection_load_voxels_2mm"] == 0.5
    assert row["disconnection_mean_2mm"] == 0.5 / 4


def test_compute_sdc_metadata_reads_each_map_once_however_many_grids(tmp_path, _metadata_root, monkeypatch):
    """The cost that scales is the disk read of ~5800 maps: a second grid must reuse the loaded
    image (same contract as compute_lesion_metadata), not re-read every file."""
    data_root = tmp_path / "data"
    for subject_id in ("sub-STUNIPD0001", "sub-STUNIPD0002"):
        _make_disconnectome(data_root, subject_id, {(2, 2, 2): 0.5})
        _register_subject(_metadata_root, _DATASET, subject_id)

    real_load = nib.load
    map_reads: list[str] = []

    def counting_load(path, *args, **kwargs):
        if "desc-disconnectome" in str(path):
            map_reads.append(str(path))
        return real_load(path, *args, **kwargs)

    monkeypatch.setattr("src.features.sdc.nib.load", counting_load)
    _compute(tmp_path, data_root, grids=[_metadata_grid(tmp_path), _coarse_grid(tmp_path)])

    assert len(map_reads) == 2


def test_compute_sdc_metadata_duplicate_grid_names_raise(tmp_path, _metadata_root):
    _register_subject(_metadata_root, _DATASET, "sub-STUNIPD0001")
    grid = _metadata_grid(tmp_path)

    with pytest.raises(ValueError, match="duplicate|unique"):
        _compute(tmp_path, tmp_path / "data", grids=[grid, grid])
