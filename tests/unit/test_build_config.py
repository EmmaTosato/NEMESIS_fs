"""Unit tests for src/analysis/build_config.py."""

import json

import pytest

from src.analysis.build_config import load_build_matrix_config

_BASE = {
    "project": "clinical_connectome",
    "data_root": "data/clinical_connectome",
    "datasets": ["UNIPD/WashU", "UNIPD/PASPORT"],
    "reference_template_path": "/templates/mni152_2mm.nii.gz",
    "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
    "binarize_threshold": 0.5,
    "resample_interpolation": "nearest",
    "parcellate": False,
    "atlas_path": None,
    "parcel_aggregation": None,
    "save_parcellated_volumes": False,
    "output_root": "data/derived/lesion_matrix",
    "run_name": "run1",
    "overwrite": False,
}


def _write(tmp_path, overrides):
    cfg = {**_BASE, **overrides}
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg))
    return path


def test_valid_voxelwise_config(tmp_path):
    config = load_build_matrix_config(_write(tmp_path, {}))
    assert config.parcellate is False
    assert config.atlas_path is None
    assert config.binarize_threshold == 0.5
    assert config.resample_interpolation == "nearest"
    assert str(config.reference_template_path) == "/templates/mni152_2mm.nii.gz"


def test_valid_parcellated_config(tmp_path):
    config = load_build_matrix_config(
        _write(tmp_path, {"parcellate": True, "atlas_path": "/atlas.nii.gz", "parcel_aggregation": "fraction_lesioned"})
    )
    assert config.parcellate is True
    assert str(config.atlas_path) == "/atlas.nii.gz"
    assert config.parcel_aggregation == "fraction_lesioned"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_build_matrix_config(tmp_path / "nope.json")


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"resample_interpolation": "cubic"}, "resample_interpolation"),
        ({"binarize_threshold": 5.0}, "between 0.0 and 1.0"),
        ({"binarize_threshold": -0.1}, "between 0.0 and 1.0"),
        ({"binarize_threshold": True}, "must be a number"),
        ({"parcellate": True}, "atlas_path and parcel_aggregation are both required"),
        ({"atlas_path": "/x.nii.gz"}, "must not be set when parcellate=false"),
        (
            {"parcellate": True, "atlas_path": "/x.nii.gz", "parcel_aggregation": "bogus"},
            "unknown parcel_aggregation",
        ),
        ({"save_parcellated_volumes": True}, "save_parcellated_volumes must be false"),
        ({"datasets": ["UNIPD/WashU", "UNIPD/WashU"]}, "duplicate entries"),
        ({"datasets": []}, "non-empty list"),
        ({"project": ""}, "non-empty string"),
        ({"reference_template_path": ""}, "non-empty string"),
    ],
)
def test_invalid_configs_raise_value_error(tmp_path, overrides, match):
    with pytest.raises(ValueError, match=match):
        load_build_matrix_config(_write(tmp_path, overrides))


def test_top_level_must_be_object(tmp_path):
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(["not", "an", "object"]))
    with pytest.raises(ValueError, match="top-level content must be a JSON object"):
        load_build_matrix_config(path)
