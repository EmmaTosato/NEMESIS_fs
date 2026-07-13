"""Unit tests for retrieval.config - structural validation only, no filesystem I/O."""

import json
from pathlib import Path

import pytest

from src.retrieval.config import FilePatterns, RetrieveItem, load_config, load_file_patterns

VALID_FILE_PATTERNS = {
    "lesion": {
        "project_root": "/data/corbetta/Clinical_connectome",
        "native": {
            "lesion_roi": ["{subject_id}/anat/{subject_id}_lesion_roi.nii.gz"],
        },
        "mni": {
            "lesion_mask": [
                "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz"
            ],
        },
    },
}


def _write_file_patterns(tmp_path, data=None, name="file_patterns.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data if data is not None else VALID_FILE_PATTERNS))
    return path


VALID_CONFIG = {
    "output_root": "data/",
    "project": "clinical_connectome",
    "datasets": ["UNIPD/WashU", "UKLFR/stroke_UKLFR"],
    "group_filter": ["ST"],
    "subjects": None,
    "retrieve": [
        {"object": "lesion", "space": "mni", "modality": "lesion_mask"},
        {"object": "lesion", "space": "native", "modality": "lesion_roi"},
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
        RetrieveItem(object="lesion", space="mni", modality="lesion_mask"),
        RetrieveItem(object="lesion", space="native", modality="lesion_roi"),
    ]
    assert config.include_tabular_data is True
    assert config.overwrite is False
    assert config.file_patterns.has("lesion", "mni", "lesion_mask")
    assert config.file_patterns.has("lesion", "native", "lesion_roi")
    assert config.file_patterns.project_root_for("lesion") == Path("/data/corbetta/Clinical_connectome")


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


def test_unknown_object_raises(tmp_path):
    path = _write_config(
        tmp_path, {"retrieve": [{"object": "bogus", "space": "native", "modality": "lesion_roi"}]}
    )
    with pytest.raises(ValueError, match="object"):
        load_config(path)


def test_retrieve_combination_not_registered_in_file_patterns_raises(tmp_path):
    """space/modality validity is no longer a static constant - it depends on
    whatever is registered in file_patterns.json, cross-checked in load_config
    (see config._require_known_combinations). Here `lesion_mask` is only
    registered under `mni`, not `native`."""
    path = _write_config(
        tmp_path, {"retrieve": [{"object": "lesion", "space": "native", "modality": "lesion_mask"}]}
    )
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
                {"object": "lesion", "space": "mni", "modality": "lesion_mask"},
                {"object": "lesion", "space": "mni", "modality": "lesion_mask"},
            ]
        },
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_config(path)


def test_retrieve_item_rejects_unknown_object_when_constructed_directly():
    """The object invariant must hold regardless of how RetrieveItem is
    built, not just when going through load_config - see
    config.RetrieveItem.__post_init__. space/modality validity is NOT
    checked here anymore (see FilePatterns tests below) - it depends on the
    external file_patterns registry, not a static constant."""
    with pytest.raises(ValueError, match="object"):
        RetrieveItem(object="bogus", space="native", modality="T1w")


def test_load_file_patterns_valid(tmp_path):
    path = _write_file_patterns(tmp_path)
    patterns = load_file_patterns(path)
    assert isinstance(patterns, FilePatterns)
    assert patterns.has("lesion", "native", "lesion_roi")
    assert patterns.has("lesion", "mni", "lesion_mask")
    assert not patterns.has("lesion", "mni", "T1w")
    assert patterns.templates_for("lesion", "native", "lesion_roi") == [
        "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz"
    ]


def test_load_file_patterns_reads_project_root_per_object(tmp_path):
    path = _write_file_patterns(tmp_path)
    patterns = load_file_patterns(path)
    assert str(patterns.project_root_for("lesion")) == "/data/corbetta/Clinical_connectome"


def test_load_file_patterns_supports_multiple_templates_per_combination(tmp_path):
    path = _write_file_patterns(
        tmp_path,
        {
            "lesion": {
                "project_root": "/data/corbetta/Clinical_connectome",
                "native": {
                    "lesion_roi": [
                        "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz",
                        "{subject_id}/anat/{subject_id}_space-T1w_lesion_roi.nii.gz",
                    ]
                },
            }
        },
    )
    patterns = load_file_patterns(path)
    assert len(patterns.templates_for("lesion", "native", "lesion_roi")) == 2


def test_file_patterns_combinations_for_returns_only_that_object(tmp_path):
    path = _write_file_patterns(
        tmp_path,
        {
            "lesion": {
                "project_root": "/data/corbetta/Clinical_connectome",
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
            "feature": {
                "project_root": "/data/corbetta/Clinical_connectome/features",
                "func": {"motion": ["{subject_id}/func/{subject_id}_desc-motion.tsv"]},
            },
        },
    )
    patterns = load_file_patterns(path)
    assert patterns.combinations_for("lesion") == [
        ("lesion", "mni", "lesion_mask"),
        ("lesion", "native", "T1w"),
        ("lesion", "native", "lesion_roi"),
    ]
    assert patterns.combinations_for("feature") == [("feature", "func", "motion")]


def test_file_patterns_all_object_spaces(tmp_path):
    path = _write_file_patterns(
        tmp_path,
        {
            "lesion": {
                "project_root": "/data/corbetta/Clinical_connectome",
                "native": {"T1w": ["{subject_id}/anat/{subject_id}_T1w.nii.gz"]},
                "mni": {
                    "lesion_mask": [
                        "derivatives/manual_masks/{subject_id}/anat/{subject_id}_label-lesion_mask.nii.gz"
                    ]
                },
            },
            "feature": {
                "project_root": "/data/corbetta/Clinical_connectome/features",
                "func": {"motion": ["{subject_id}/func/{subject_id}_desc-motion.tsv"]},
            },
        },
    )
    patterns = load_file_patterns(path)
    assert patterns.all_object_spaces() == {("lesion", "native"), ("lesion", "mni"), ("feature", "func")}


def test_file_patterns_templates_for_unknown_combination_raises(tmp_path):
    path = _write_file_patterns(tmp_path)
    patterns = load_file_patterns(path)
    with pytest.raises(ValueError, match="no file pattern registered"):
        patterns.templates_for("lesion", "native", "T1w")


def test_file_patterns_project_root_for_unknown_object_raises(tmp_path):
    path = _write_file_patterns(tmp_path)
    patterns = load_file_patterns(path)
    with pytest.raises(ValueError, match="no project_root"):
        patterns.project_root_for("feature")


def test_load_file_patterns_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_file_patterns(tmp_path / "does_not_exist.json")


def test_load_file_patterns_rejects_non_object_top_level(tmp_path):
    path = tmp_path / "file_patterns.json"
    path.write_text(json.dumps(["not", "an", "object"]))
    with pytest.raises(ValueError, match="JSON object"):
        load_file_patterns(path)


def test_load_file_patterns_rejects_unknown_object(tmp_path):
    path = _write_file_patterns(
        tmp_path, {"bogus_object": {"project_root": "/x", "T1w": ["sub-{subject_id}_T1w.nii.gz"]}}
    )
    with pytest.raises(ValueError, match="unknown object"):
        load_file_patterns(path)


def test_load_file_patterns_rejects_missing_project_root(tmp_path):
    path = _write_file_patterns(
        tmp_path, {"lesion": {"native": {"T1w": ["{subject_id}/anat/{subject_id}_T1w.nii.gz"]}}}
    )
    with pytest.raises(ValueError, match="project_root"):
        load_file_patterns(path)


def test_load_file_patterns_rejects_empty_modality_list(tmp_path):
    path = _write_file_patterns(
        tmp_path, {"lesion": {"project_root": "/x", "native": {"T1w": []}}}
    )
    with pytest.raises(ValueError, match="non-empty list"):
        load_file_patterns(path)


def test_load_file_patterns_rejects_template_without_subject_id_placeholder(tmp_path):
    path = _write_file_patterns(
        tmp_path, {"lesion": {"project_root": "/x", "native": {"T1w": ["sub-fixed-name.nii.gz"]}}}
    )
    with pytest.raises(ValueError, match="subject_id"):
        load_file_patterns(path)
