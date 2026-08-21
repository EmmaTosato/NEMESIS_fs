"""Unit tests for src/analysis/build_config.py."""

import json

import pytest

from src.analysis.build_config import load_build_matrix_config, load_enrich_lesion_metadata_config, load_mask_fc_config

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
    "session_name": "run1",
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
    assert config.group_filter is None  # absent from _BASE -> no restriction


def test_group_filter_defaults_to_none_when_absent(tmp_path):
    config = load_build_matrix_config(_write(tmp_path, {}))
    assert config.group_filter is None


def test_group_filter_restricts_to_declared_groups(tmp_path):
    config = load_build_matrix_config(_write(tmp_path, {"group_filter": ["ST"]}))
    assert config.group_filter == ["ST"]


def test_group_filter_can_include_multiple_groups(tmp_path):
    config = load_build_matrix_config(_write(tmp_path, {"group_filter": ["ST", "HC"]}))
    assert config.group_filter == ["ST", "HC"]


def test_group_filter_unknown_group_raises(tmp_path):
    with pytest.raises(ValueError, match="unknown group"):
        load_build_matrix_config(_write(tmp_path, {"group_filter": ["XX"]}))


def test_group_filter_empty_list_raises(tmp_path):
    with pytest.raises(ValueError, match="non-empty list"):
        load_build_matrix_config(_write(tmp_path, {"group_filter": []}))


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


# --- load_mask_fc_config: group_filter ----------------------------------------

_MASK_FC_BASE = {
    "project": "clinical_connectome",
    "data_root": "data/clinical_connectome/derivatives",
    "dataset": "UNIPD/WashU",
    "atlas_root": "assets/atlases/fmriprep",
    "atlas_combos": ["Yan200TianS2Buckner7N"],
    "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
    "fc_glob_template": "features/*/func/*_FC-pearson_atlas-{combo}.csv",
    "min_coverage": 0.5,
    "resample_interpolation": "nearest",
    "binarize_threshold": 0.5,
    "output_root": "data/derived/features/masked_fc",
    "session_name": "s1",
    "overwrite": False,
}


def _write_mask_fc(tmp_path, overrides):
    cfg = {**_MASK_FC_BASE, **overrides}
    path = tmp_path / "mask_fc_cfg.json"
    path.write_text(json.dumps(cfg))
    return path


def test_mask_fc_group_filter_defaults_to_none_when_absent(tmp_path):
    config = load_mask_fc_config(_write_mask_fc(tmp_path, {}))
    assert config.group_filter is None


def test_mask_fc_group_filter_restricts_to_declared_groups(tmp_path):
    config = load_mask_fc_config(_write_mask_fc(tmp_path, {"group_filter": ["ST"]}))
    assert config.group_filter == ["ST"]


def test_mask_fc_group_filter_unknown_group_raises(tmp_path):
    with pytest.raises(ValueError, match="unknown group"):
        load_mask_fc_config(_write_mask_fc(tmp_path, {"group_filter": ["XX"]}))


_ENRICH_BASE = {
    "project": "clinical_connectome",
    "metadata_path": "data/derived/lesion_matrix/21-07_s1.1/metadata.csv",
    "compute_volume": False,
    "variables": ["age", "sex"],
    "output_root": "data/derived/clinical_metadata",
    "session_name": "s1",
    "overwrite": False,
}


def _write_enrich(tmp_path, overrides):
    cfg = {**_ENRICH_BASE, **overrides}
    path = tmp_path / "enrich_cfg.json"
    path.write_text(json.dumps(cfg))
    return path


def test_enrich_lesion_metadata_valid_config(tmp_path):
    config = load_enrich_lesion_metadata_config(_write_enrich(tmp_path, {}))
    assert config.compute_volume is False
    assert config.variables == ["age", "sex"]
    assert str(config.metadata_path) == "data/derived/lesion_matrix/21-07_s1.1/metadata.csv"


def test_enrich_lesion_metadata_compute_volume_true_needs_no_extra_field(tmp_path):
    config = load_enrich_lesion_metadata_config(_write_enrich(tmp_path, {"compute_volume": True}))
    assert config.compute_volume is True


def test_enrich_lesion_metadata_variables_must_be_unique(tmp_path):
    with pytest.raises(ValueError, match="duplicate entries"):
        load_enrich_lesion_metadata_config(_write_enrich(tmp_path, {"variables": ["age", "age"]}))
