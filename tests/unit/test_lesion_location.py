"""Unit tests for src/features/lesion_location.py - synthetic atlases (tests/unit/location_fixtures.py),
no real atlas and no EBRAIN mount.

The grid is 10x10x10 at 2mm with world x = 2i - 10, so voxel i = 5 is the midline plane and a
voxel's hemisphere is its x index (< 5 left, > 5 right). The atlases are written LAS, the grid is
RAS: nothing here lines up unless the code goes through the affines.
"""

import nibabel as nib
import numpy as np
import pytest

from src.features.lesion_location import (
    LOCATION_CATEGORIES,
    LesionAtlas,
    LesionLocationSpec,
    build_location_categories,
    location_columns,
    location_metrics,
)
from tests.unit.location_fixtures import make_location_spec, write_atlas

_SHAPE = (10, 10, 10)
_AFFINE = np.array([[2.0, 0, 0, -10.0], [0, 2.0, 0, -10.0], [0, 0, 2.0, -10.0], [0, 0, 0, 1.0]])
_VALUE = {name: position for position, name in enumerate(LOCATION_CATEGORIES, start=1)}


def _reference():
    return nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE)


def _brain(outside=()):
    brain = np.ones(_SHAPE, dtype=bool)
    for voxel in outside:
        brain[voxel] = False
    return brain.ravel()


def _categories(spec, outside=()):
    return build_location_categories(spec, _reference(), _brain(outside)).reshape(_SHAPE)


def test_each_category_lands_where_the_rules_say_and_precedence_resolves_overlaps(tmp_path):
    # One voxel per case on slab k=1, i differing between cases so a naive x flip would move them.
    cortex = [(1, 1, 1), (4, 1, 1), (2, 2, 1), (2, 3, 1), (8, 3, 1), (1, 5, 1)]
    white = [(2, 1, 1), (4, 1, 1)]
    gray = [(1, 2, 1), (2, 2, 1)]
    stem = [(7, 2, 1)]
    ventricle = [(1, 3, 1), (2, 3, 1)]
    cerebellum = [(8, 3, 1)]
    spec = make_location_spec(
        tmp_path, _SHAPE, _AFFINE, cortex=cortex, white=white, gray=gray, stem=stem,
        ventricle=ventricle, cerebellum=cerebellum,
    )

    categories = _categories(spec, outside=[(1, 5, 1)])

    assert categories[1, 1, 1] == _VALUE["cortex_only"]
    assert categories[2, 1, 1] == _VALUE["white_matter_only"]
    # both atlases claim it: neither side wins, it is its own category
    assert categories[4, 1, 1] == _VALUE["cortex_white_boundary"]
    assert categories[1, 2, 1] == _VALUE["subcortical_gray"]
    # cortex and gray both claim it: gray takes it
    assert categories[2, 2, 1] == _VALUE["subcortical_gray"]
    assert categories[7, 2, 1] == _VALUE["infratentorial"]
    # cortex and ventricle both claim it: the cortex takes it
    assert categories[2, 3, 1] == _VALUE["cortex_only"]
    assert categories[1, 3, 1] == _VALUE["ventricle"]
    # cortex and cerebellum both claim it: infratentorial takes it
    assert categories[8, 3, 1] == _VALUE["infratentorial"]
    # inside the brain, no atlas names it
    assert categories[6, 8, 1] == _VALUE["unlabeled"]
    # a labelled voxel outside the brain mask is outside, whatever the atlas says
    assert categories[1, 5, 1] == 0


def test_the_las_atlas_is_aligned_through_the_affine_not_by_flipping_the_array(tmp_path):
    """The atlases are stored x-reversed (LAS) against a RAS grid. The right answer is the one a
    RAS-stored atlas gives; the negative control is that reversing the array instead would move
    every asymmetric voxel - so this test cannot pass on a naive flip."""
    kwargs = dict(cortex=[(1, 1, 1), (3, 2, 1)], white=[(2, 1, 1)], gray=[(1, 2, 1)], stem=[(7, 2, 1)])
    categories = _categories(make_location_spec(tmp_path, _SHAPE, _AFFINE, **kwargs))

    assert categories[1, 1, 1] == _VALUE["cortex_only"]
    assert categories[2, 1, 1] == _VALUE["white_matter_only"]
    assert categories[7, 2, 1] == _VALUE["infratentorial"]
    flipped = categories[::-1]
    assert not np.array_equal(flipped, categories)
    assert flipped[1, 1, 1] != _VALUE["cortex_only"]


def test_atlas_off_by_a_fraction_of_a_voxel_is_rejected(tmp_path):
    spec = make_location_spec(tmp_path, _SHAPE, _AFFINE, cortex=[(1, 1, 1)])
    image = nib.load(spec.cortical.image_path)
    shifted_affine = image.affine.copy()
    shifted_affine[0, 3] += 1.0  # half a 2mm voxel
    nib.save(nib.Nifti1Image(np.asarray(image.dataobj), shifted_affine), spec.cortical.image_path)

    with pytest.raises(ValueError, match="not an exact integer voxel map"):
        _categories(spec)


def test_atlas_on_another_shape_is_rejected(tmp_path):
    spec = make_location_spec(tmp_path, _SHAPE, _AFFINE, cortex=[(1, 1, 1)])
    other = write_atlas(tmp_path, "small", (8, 8, 8), _AFFINE, {"Left Region": [(1, 1, 1)], "Right Region": [(6, 1, 1)]})

    with pytest.raises(ValueError, match="shape"):
        _categories(LesionLocationSpec("coarse", other, spec.subcortical, spec.cerebellum))


def test_a_mirrored_atlas_is_rejected_by_the_hemisphere_check(tmp_path):
    """An image whose array is x-reversed but whose affine says it is not: the voxel map is an
    integer one, so the grid check passes - only the world-coordinate side of each label gives it
    away. This is the check a wrong flip would fail."""
    spec = make_location_spec(tmp_path, _SHAPE, _AFFINE, cortex=[(1, 1, 1)])
    image = nib.load(spec.cortical.image_path)
    nib.save(nib.Nifti1Image(np.asarray(image.dataobj), _AFFINE), spec.cortical.image_path)

    with pytest.raises(ValueError, match="wrong side of the midline"):
        _categories(spec)


def test_a_voxel_value_with_no_label_in_the_xml_is_rejected(tmp_path):
    spec = make_location_spec(tmp_path, _SHAPE, _AFFINE, cortex=[(1, 1, 1)])
    image = nib.load(spec.cortical.image_path)
    data = np.asarray(image.dataobj).copy()
    data[3, 3, 3] = 7  # the XML declares labels 1 and 2 only
    nib.save(nib.Nifti1Image(data, image.affine), spec.cortical.image_path)

    with pytest.raises(ValueError, match="are not the labels"):
        _categories(spec)


def test_a_subcortical_label_the_rules_do_not_find_is_rejected(tmp_path):
    """The category rules match label names; an atlas without the brainstem (renamed, dropped)
    must raise instead of silently leaving the brainstem unlabeled."""
    spec = make_location_spec(tmp_path, _SHAPE, _AFFINE)
    xml = spec.subcortical.labels_path
    xml.write_text(xml.read_text().replace("Brain-Stem", "Brain Stem"))

    with pytest.raises(ValueError, match="'brain_stem' rule"):
        _categories(spec)


def test_a_missing_atlas_image_raises(tmp_path):
    spec = make_location_spec(tmp_path, _SHAPE, _AFFINE)
    missing = LesionAtlas(tmp_path / "nope.nii.gz", spec.cortical.labels_path)

    with pytest.raises(FileNotFoundError, match="cortical atlas image"):
        _categories(LesionLocationSpec("coarse", missing, spec.subcortical, spec.cerebellum))


def test_a_brain_mask_of_another_grid_is_rejected(tmp_path):
    spec = make_location_spec(tmp_path, _SHAPE, _AFFINE)

    with pytest.raises(ValueError, match="raveled brain mask of the same grid"):
        build_location_categories(spec, _reference(), np.ones(10, dtype=bool))


# --- per-subject metrics -------------------------------------------------------------------------


def _map(*assignments):
    """A category map over 20 voxels: assignments are (category, first voxel, last voxel + 1)."""
    categories = np.zeros(20, dtype=np.uint8)
    for category, start, stop in assignments:
        categories[start:stop] = _VALUE[category]
    return categories


def _lesion(*voxels):
    lesion = np.zeros(20, dtype=bool)
    lesion[list(voxels)] = True
    return lesion


def test_location_columns_are_the_dominant_then_one_fraction_per_category():
    assert location_columns("2mm") == ["location_dominant_2mm"] + [f"location_{c}_2mm" for c in LOCATION_CATEGORIES]
    assert LOCATION_CATEGORIES[0] == "infratentorial"
    assert len(location_columns("2mm")) == 8


def test_fractions_sum_to_one_and_the_dominant_is_the_largest():
    categories = _map(("white_matter_only", 0, 10), ("cortex_only", 10, 15), ("infratentorial", 15, 20))
    lesion = _lesion(0, 1, 2, 3, 10, 11, 15)  # 4 white, 2 cortex, 1 infratentorial

    metrics = location_metrics(lesion, categories, "2mm")

    assert metrics["location_dominant_2mm"] == "white_matter_only"
    assert metrics["location_white_matter_only_2mm"] == pytest.approx(4 / 7)
    assert metrics["location_cortex_only_2mm"] == pytest.approx(2 / 7)
    assert metrics["location_infratentorial_2mm"] == pytest.approx(1 / 7)
    assert metrics["location_ventricle_2mm"] == 0.0
    assert sum(metrics[c] for c in metrics if c != "location_dominant_2mm") == pytest.approx(1.0)


def test_a_tie_goes_to_the_category_earlier_in_the_precedence_order():
    """Two voxels each - common for tiny lesions - must give the same label every run: the earlier
    category in LOCATION_CATEGORIES (infratentorial before cortex before white matter)."""
    categories = _map(("white_matter_only", 0, 10), ("cortex_only", 10, 20))

    assert location_metrics(_lesion(0, 1, 10, 11), categories, "2mm")["location_dominant_2mm"] == "cortex_only"

    categories = _map(("infratentorial", 0, 10), ("cortex_only", 10, 20))
    assert location_metrics(_lesion(0, 10), categories, "2mm")["location_dominant_2mm"] == "infratentorial"


def test_voxels_outside_the_brain_are_not_in_the_denominator():
    """Category 0 is outside the brain: 3 voxels outside and 1 inside leave one voxel, 100% of it
    in that category - never 25%, and never a fraction that fails to sum to 1."""
    categories = _map(("cortex_only", 5, 10))  # voxels 0-4 and 10-19 are outside (0)
    lesion = _lesion(0, 1, 2, 5)

    metrics = location_metrics(lesion, categories, "2mm")

    assert metrics["location_cortex_only_2mm"] == 1.0
    assert metrics["location_dominant_2mm"] == "cortex_only"


def test_an_empty_lesion_and_a_lesion_entirely_outside_the_brain_have_no_location():
    categories = _map(("cortex_only", 5, 10))

    for lesion in (_lesion(), _lesion(0, 1, 15)):
        metrics = location_metrics(lesion, categories, "2mm")
        assert set(metrics) == set(location_columns("2mm"))
        assert all(np.isnan(value) for value in metrics.values())


def test_a_lesion_on_another_grid_than_the_category_map_raises():
    with pytest.raises(ValueError, match="category map"):
        location_metrics(np.zeros(5, dtype=bool), _map(("cortex_only", 0, 10)), "2mm")
