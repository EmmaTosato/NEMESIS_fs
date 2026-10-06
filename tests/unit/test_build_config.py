"""Unit tests for src/analysis/build_config.py."""

import json

import pytest

from src.analysis.build_config import (
    load_build_fc_matrix_config,
    load_build_matrix_config,
    load_compute_sdc_metadata_config,
    load_mask_fc_config,
)

_BASE = {
    "project": "clinical_connectome",
    "data_root": "data/clinical_connectome",
    "datasets": ["UNIPD/WashU", "UNIPD/PASPORT"],
    "reference_template_path": "/templates/mni152_2mm.nii.gz",
    "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
    "binarize_threshold": 0.5,
    "resample_interpolation": "nearest",
    "excluded_subjects_path": "assets/metadata/excluded_subjects.csv",
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


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_build_matrix_config(tmp_path / "nope.json")


def test_correct_out_of_brain_defaults_to_false_when_absent(tmp_path):
    config = load_build_matrix_config(_write(tmp_path, {}))
    assert config.correct_out_of_brain is False


def test_correct_out_of_brain_requires_brain_mask_path(tmp_path):
    with pytest.raises(ValueError, match="brain_mask_path"):
        load_build_matrix_config(_write(tmp_path, {"correct_out_of_brain": True}))


def test_correct_out_of_brain_with_brain_mask_path_parsed(tmp_path):
    config = load_build_matrix_config(
        _write(tmp_path, {"correct_out_of_brain": True, "brain_mask_path": "/templates/brain_mask.nii.gz"})
    )
    assert config.correct_out_of_brain is True


def test_correct_out_of_brain_non_bool_raises(tmp_path):
    with pytest.raises(ValueError, match="correct_out_of_brain"):
        load_build_matrix_config(
            _write(tmp_path, {"correct_out_of_brain": "true", "brain_mask_path": "/templates/brain_mask.nii.gz"})
        )


def test_brain_mask_path_absent_when_nothing_set(tmp_path):
    config = load_build_matrix_config(_write(tmp_path, {}))
    assert config.brain_mask_path is None
    assert config.brain_mask_path is None


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"resample_interpolation": "cubic"}, "resample_interpolation"),
        ({"binarize_threshold": 5.0}, "between 0.0 and 1.0"),
        ({"binarize_threshold": -0.1}, "between 0.0 and 1.0"),
        ({"binarize_threshold": True}, "must be a number"),
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


# AUDIT_FINDINGS.md #51: test coverage for load_mask_fc_config was limited to group_filter
# only - min_coverage/atlas_combos/resample_interpolation/binarize_threshold/fc_glob_template
# (all required fields of the same loader) had no dedicated test at all.


def test_mask_fc_valid_config(tmp_path):
    config = load_mask_fc_config(_write_mask_fc(tmp_path, {}))
    assert config.min_coverage == 0.5
    assert config.atlas_combos == ["Yan200TianS2Buckner7N"]
    assert config.resample_interpolation == "nearest"
    assert config.binarize_threshold == 0.5
    assert config.fc_glob_template == "features/*/func/*_FC-pearson_atlas-{combo}.csv"


def test_mask_fc_multiple_atlas_combos(tmp_path):
    config = load_mask_fc_config(
        _write_mask_fc(tmp_path, {"atlas_combos": ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"]})
    )
    assert config.atlas_combos == ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"]


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"atlas_combos": []}, "non-empty list"),
        ({"atlas_combos": ["ComboX", "ComboX"]}, "duplicate entries"),
        ({"min_coverage": 1.5}, "between 0.0 and 1.0"),
        ({"min_coverage": -0.1}, "between 0.0 and 1.0"),
        ({"resample_interpolation": "cubic"}, "resample_interpolation"),
        ({"binarize_threshold": 5.0}, "between 0.0 and 1.0"),
        ({"binarize_threshold": True}, "must be a number"),
        ({"fc_glob_template": ""}, "non-empty string"),
        ({"lesion_glob": ""}, "non-empty string"),
    ],
)
def test_mask_fc_invalid_configs_raise_value_error(tmp_path, overrides, match):
    with pytest.raises(ValueError, match=match):
        load_mask_fc_config(_write_mask_fc(tmp_path, overrides))


# --- load_build_fc_matrix_config ------------------------------------------------
# AUDIT_FINDINGS.md #31: this loader had zero dedicated unit tests before (only
# indirect coverage via tests/integration/test_build_fc_matrix_pipeline.py's
# already-valid configs) - unlike its siblings above, a future required field added
# to BuildFcMatrixConfig without validating it would go unnoticed by any test.

_BUILD_FC_MATRIX_BASE = {
    "project": "clinical_connectome",
    "masked_fc_root": "data/derived/features/masked_fc",
    "atlas_combos": ["Yan200TianS2Buckner7N"],
    "output_root": "data/derived/features/fc_matrix",
    "session_name": "s1",
    "overwrite": False,
}


def _write_build_fc_matrix(tmp_path, overrides):
    cfg = {**_BUILD_FC_MATRIX_BASE, **overrides}
    path = tmp_path / "build_fc_matrix_cfg.json"
    path.write_text(json.dumps(cfg))
    return path


def test_build_fc_matrix_valid_config(tmp_path):
    config = load_build_fc_matrix_config(_write_build_fc_matrix(tmp_path, {}))
    assert config.project == "clinical_connectome"
    assert str(config.masked_fc_root) == "data/derived/features/masked_fc"
    assert config.atlas_combos == ["Yan200TianS2Buckner7N"]
    assert str(config.output_root) == "data/derived/features/fc_matrix"
    assert config.session_name == "s1"
    assert config.overwrite is False
    assert config.run_notes is None  # absent from base -> optional, defaults to None


def test_build_fc_matrix_multiple_atlas_combos(tmp_path):
    config = load_build_fc_matrix_config(
        _write_build_fc_matrix(tmp_path, {"atlas_combos": ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"]})
    )
    assert config.atlas_combos == ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"]


def test_build_fc_matrix_run_notes_passthrough(tmp_path):
    config = load_build_fc_matrix_config(_write_build_fc_matrix(tmp_path, {"run_notes": "prova sweep"}))
    assert config.run_notes == "prova sweep"


def test_build_fc_matrix_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_build_fc_matrix_config(tmp_path / "nope.json")


def test_build_fc_matrix_top_level_must_be_object(tmp_path):
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(["not", "an", "object"]))
    with pytest.raises(ValueError, match="top-level content must be a JSON object"):
        load_build_fc_matrix_config(path)


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"project": ""}, "non-empty string"),
        ({"masked_fc_root": ""}, "non-empty string"),
        ({"atlas_combos": []}, "non-empty list"),
        ({"atlas_combos": ["ComboX", "ComboX"]}, "duplicate entries"),
        ({"output_root": ""}, "non-empty string"),
        ({"session_name": ""}, "non-empty string"),
        ({"overwrite": "true"}, "must be a bool"),
        ({"project": None}, "non-empty string"),
    ],
)
def test_build_fc_matrix_invalid_configs_raise_value_error(tmp_path, overrides, match):
    with pytest.raises(ValueError, match=match):
        load_build_fc_matrix_config(_write_build_fc_matrix(tmp_path, overrides))


_ENRICH_BASE = {
    "project": "clinical_connectome",
    "metadata_path": "data/derived/lesion_matrix/21-07_s1.1/metadata.csv",
    "compute_volume": False,
    "variables": ["age", "sex"],
    "copy_output_path": "data/derived/lesion_matrix/s1_copy",
    "session_name": "s1",
    "overwrite": False,
    "write_in_place": False,
}




# --- compute_sdc_metadata.json ------------------------------------------------------------------------

_SDC_METADATA_BASE = {
    "project": "clinical_connectome",
    "data_root": "data/clinical_connectome/derivatives",
    "output_path": "assets/metadata/sdc_metadata.csv",
    "datasets": ["UNIPD/WashU", "UNIPD/PSP"],
    "group_filter": ["ST"],
    "disconnectome_glob": "sdc/*/*_res-1_desc-disconnectome.nii.gz",
    "resample_interpolation": "nearest",
    "grid": {
        "name": "1mm",
        "reference_template_path": "assets/templates/tpl-res-1_T1w.nii.gz",
        "brain_mask_path": "assets/templates/tpl-res-1_desc-brain_mask.nii.gz",
    },
    "overwrite": False,
    "run_notes": "test",
}


def _write_sdc_metadata(tmp_path, overrides=None, drop=()):
    cfg = {**_SDC_METADATA_BASE, **(overrides or {})}
    for key in drop:
        del cfg[key]
    path = tmp_path / "compute_sdc_metadata.json"
    path.write_text(json.dumps(cfg))
    return path


def test_compute_sdc_metadata_config_valid(tmp_path):
    config = load_compute_sdc_metadata_config(_write_sdc_metadata(tmp_path))

    assert config.grid.name == "1mm"
    assert config.grid.brain_mask_path.name == "tpl-res-1_desc-brain_mask.nii.gz"
    assert config.datasets == ["UNIPD/WashU", "UNIPD/PSP"]
    assert config.group_filter == ["ST"]
    assert config.overwrite is False


@pytest.mark.parametrize(
    "overrides, drop, match",
    [
        pytest.param({}, ("grid",), "missing required field 'grid'", id="grid-absent"),
        pytest.param({"grid": "1mm"}, (), "must be an object with a non-empty string 'name'", id="grid-not-an-object"),
        pytest.param(
            {"grid": {"reference_template_path": "a", "brain_mask_path": "b"}}, (), "non-empty string 'name'",
            id="grid-without-name",
        ),
        pytest.param(
            {"grid": {"name": "1mm", "reference_template_path": "a"}}, (), "missing 'brain_mask_path'",
            id="grid-without-brain-mask",
        ),
        pytest.param(
            {"grid": {"name": "1 mm", "reference_template_path": "a", "brain_mask_path": "b"}}, (),
            "not alphanumeric", id="grid-name-not-a-column-suffix",
        ),
        pytest.param({"datasets": ["UNIPD/WashU", "UNIPD/WashU"]}, (), "duplicate", id="duplicate-dataset"),
        pytest.param({"resample_interpolation": "cubic"}, (), "resample_interpolation", id="unknown-interpolation"),
        pytest.param({}, ("disconnectome_glob",), "disconnectome_glob", id="glob-absent"),
        pytest.param({"overwrite": "yes"}, (), "overwrite", id="overwrite-not-a-bool"),
    ],
)
def test_compute_sdc_metadata_config_invalid_raises_value_error(tmp_path, overrides, drop, match):
    with pytest.raises(ValueError, match=match):
        load_compute_sdc_metadata_config(_write_sdc_metadata(tmp_path, overrides, drop))


def test_compute_sdc_metadata_config_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="config file not found"):
        load_compute_sdc_metadata_config(tmp_path / "nope.json")
