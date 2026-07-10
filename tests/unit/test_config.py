"""Unit tests for retrieval.config - structural validation only, no filesystem I/O."""

import json

import pytest

from src.retrieval.config import FilePatterns, RetrieveItem, load_config, load_file_patterns

VALID_FILE_PATTERNS = {
    "native": {
        "lesion_roi": ["{subject_id}/anat/{subject_id}_lesion_roi.nii.gz"],
    },
    "mni": {
        "lesion_mask": [
            "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz"
        ],
    },
}


def _write_file_patterns(tmp_path, data=None, name="file_patterns.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data if data is not None else VALID_FILE_PATTERNS))
    return path


VALID_CONFIG = {
    "output_root": "data/",
    "project": "clinical_connectome",
    "project_root": "/data/corbetta/Clinical_connectome",
    "datasets": ["UNIPD/WashU", "UKLFR/stroke_UKLFR"],
    "group_filter": ["ST"],
    "subjects": None,
    "retrieve": [
        {"space": "mni", "modality": "lesion_mask"},
        {"space": "native", "modality": "lesion_roi"},
    ],
    "include_tabular_data": True,
    "overwrite": False,
}


def _write_config(tmp_path, overrides=None):
    file_patterns_path = _write_file_patterns(tmp_path)
    data = {**VALID_CONFIG, "file_patterns": str(file_patterns_path), **(overrides or {})}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    return path


def test_valid_config_loads(tmp_path):
    config = load_config(_write_config(tmp_path))
    assert config.project == "clinical_connectome"
    assert config.datasets == ["UNIPD/WashU", "UKLFR/stroke_UKLFR"]
    assert config.group_filter == ["ST"]
    assert config.subjects is None
    assert config.retrieve == [
        RetrieveItem(space="mni", modality="lesion_mask"),
        RetrieveItem(space="native", modality="lesion_roi"),
    ]
    assert config.include_tabular_data is True
    assert config.overwrite is False
    assert config.file_patterns.has("mni", "lesion_mask")
    assert config.file_patterns.has("native", "lesion_roi")


def test_missing_config_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "does_not_exist.json")


def test_missing_required_field_raises(tmp_path):
    path = _write_config(tmp_path)
    data = json.loads(path.read_text())
    del data["project"]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="project"):
        load_config(path)


def test_missing_file_patterns_field_raises(tmp_path):
    path = _write_config(tmp_path)
    data = json.loads(path.read_text())
    del data["file_patterns"]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="file_patterns"):
        load_config(path)


def test_file_patterns_file_not_found_raises(tmp_path):
    path = _write_config(tmp_path, {"file_patterns": str(tmp_path / "does_not_exist.json")})
    with pytest.raises(FileNotFoundError):
        load_config(path)


def test_empty_datasets_list_raises(tmp_path):
    path = _write_config(tmp_path, {"datasets": []})
    with pytest.raises(ValueError, match="datasets"):
        load_config(path)


def test_empty_retrieve_list_raises(tmp_path):
    path = _write_config(tmp_path, {"retrieve": []})
    with pytest.raises(ValueError, match="retrieve"):
        load_config(path)


def test_unknown_space_raises(tmp_path):
    path = _write_config(tmp_path, {"retrieve": [{"space": "bogus", "modality": "lesion_roi"}]})
    with pytest.raises(ValueError, match="space"):
        load_config(path)


def test_retrieve_combination_not_registered_in_file_patterns_raises(tmp_path):
    """modality validity is no longer a static constant - it depends on
    whatever is registered in file_patterns.json, cross-checked in load_config
    (see config._require_known_combinations)."""
    path = _write_config(tmp_path, {"retrieve": [{"space": "native", "modality": "lesion_mask"}]})
    with pytest.raises(ValueError, match="not registered"):
        load_config(path)


def test_unknown_group_in_group_filter_raises(tmp_path):
    path = _write_config(tmp_path, {"group_filter": ["ST", "BOGUS"]})
    with pytest.raises(ValueError, match="group_filter"):
        load_config(path)


def test_group_filter_omitted_is_none(tmp_path):
    file_patterns_path = _write_file_patterns(tmp_path)
    data = {k: v for k, v in VALID_CONFIG.items() if k != "group_filter"}
    data["file_patterns"] = str(file_patterns_path)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    config = load_config(path)
    assert config.group_filter is None


def test_subjects_explicit_list(tmp_path):
    path = _write_config(tmp_path, {"subjects": ["sub-STUNIPD0002"]})
    config = load_config(path)
    assert config.subjects == ["sub-STUNIPD0002"]


def test_overwrite_wrong_type_raises(tmp_path):
    path = _write_config(tmp_path, {"overwrite": "false"})
    with pytest.raises(ValueError, match="overwrite"):
        load_config(path)


def test_duplicate_retrieve_items_raise(tmp_path):
    path = _write_config(
        tmp_path,
        {
            "retrieve": [
                {"space": "mni", "modality": "lesion_mask"},
                {"space": "mni", "modality": "lesion_mask"},
            ]
        },
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_config(path)


def test_retrieve_item_rejects_unknown_space_when_constructed_directly():
    """The space invariant must hold regardless of how RetrieveItem is built,
    not just when going through load_config - see config.RetrieveItem.__post_init__.
    Modality validity is NOT checked here anymore (see FilePatterns tests below) -
    it depends on the external file_patterns registry, not a static constant."""
    with pytest.raises(ValueError, match="space"):
        RetrieveItem(space="bogus", modality="T1w")


def test_load_file_patterns_valid(tmp_path):
    path = _write_file_patterns(tmp_path)
    patterns = load_file_patterns(path)
    assert isinstance(patterns, FilePatterns)
    assert patterns.has("native", "lesion_roi")
    assert patterns.has("mni", "lesion_mask")
    assert not patterns.has("mni", "T1w")
    assert patterns.templates_for("native", "lesion_roi") == [
        "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz"
    ]


def test_load_file_patterns_supports_multiple_templates_per_combination(tmp_path):
    path = _write_file_patterns(
        tmp_path,
        {
            "native": {
                "lesion_roi": [
                    "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz",
                    "{subject_id}/anat/{subject_id}_space-T1w_lesion_roi.nii.gz",
                ]
            }
        },
    )
    patterns = load_file_patterns(path)
    assert len(patterns.templates_for("native", "lesion_roi")) == 2


def test_file_patterns_modalities_for_returns_only_that_space(tmp_path):
    path = _write_file_patterns(
        tmp_path,
        {
            "native": {
                "T1w": ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
                "lesion_roi": ["{subject_id}/anat/{subject_id}_lesion_roi.nii.gz"],
            },
            "mni": {
                "lesion_mask": [
                    "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz"
                ]
            },
        },
    )
    patterns = load_file_patterns(path)
    assert sorted(patterns.modalities_for("native")) == ["T1w", "lesion_roi"]
    assert patterns.modalities_for("mni") == ["lesion_mask"]


def test_file_patterns_modalities_for_space_absent_from_registry_is_empty(tmp_path):
    """A registry that only defines "native" (no "mni" key at all - a valid,
    if unusual, registry per load_file_patterns) must report zero modalities
    for "mni", not raise - Dataset.has_any relies on this to mean "nothing
    registered for this space", distinct from KNOWN_SPACES validity."""
    path = _write_file_patterns(
        tmp_path, {"native": {"T1w": ["{subject_id}/anat/{subject_id}_T1w.nii.gz"]}}
    )
    patterns = load_file_patterns(path)
    assert patterns.modalities_for("mni") == []


def test_file_patterns_templates_for_unknown_combination_raises(tmp_path):
    path = _write_file_patterns(tmp_path)
    patterns = load_file_patterns(path)
    with pytest.raises(ValueError, match="no file pattern registered"):
        patterns.templates_for("native", "T1w")


def test_load_file_patterns_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_file_patterns(tmp_path / "does_not_exist.json")


def test_load_file_patterns_rejects_non_object_top_level(tmp_path):
    path = tmp_path / "file_patterns.json"
    path.write_text(json.dumps(["not", "an", "object"]))
    with pytest.raises(ValueError, match="JSON object"):
        load_file_patterns(path)


def test_load_file_patterns_rejects_unknown_space(tmp_path):
    path = _write_file_patterns(tmp_path, {"bogus_space": {"T1w": ["sub-{subject_id}_T1w.nii.gz"]}})
    with pytest.raises(ValueError, match="unknown space"):
        load_file_patterns(path)


def test_load_file_patterns_rejects_empty_modality_list(tmp_path):
    path = _write_file_patterns(tmp_path, {"native": {"T1w": []}})
    with pytest.raises(ValueError, match="non-empty list"):
        load_file_patterns(path)


def test_load_file_patterns_rejects_template_without_subject_id_placeholder(tmp_path):
    path = _write_file_patterns(tmp_path, {"native": {"T1w": ["sub-fixed-name.nii.gz"]}})
    with pytest.raises(ValueError, match="subject_id"):
        load_file_patterns(path)
