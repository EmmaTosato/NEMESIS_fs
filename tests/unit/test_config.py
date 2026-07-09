"""Unit tests for retrieval.config - structural validation only, no filesystem I/O."""

import json

import pytest

from src.retrieval.config import RetrieveItem, load_config

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
    data = {**VALID_CONFIG, **(overrides or {})}
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


def test_modality_not_valid_for_native_space_raises(tmp_path):
    path = _write_config(tmp_path, {"retrieve": [{"space": "native", "modality": "lesion_mask"}]})
    with pytest.raises(ValueError, match="modality"):
        load_config(path)


def test_modality_not_valid_for_mni_space_raises(tmp_path):
    path = _write_config(tmp_path, {"retrieve": [{"space": "mni", "modality": "T1w"}]})
    with pytest.raises(ValueError, match="modality"):
        load_config(path)


def test_unknown_group_in_group_filter_raises(tmp_path):
    path = _write_config(tmp_path, {"group_filter": ["ST", "BOGUS"]})
    with pytest.raises(ValueError, match="group_filter"):
        load_config(path)


def test_group_filter_omitted_is_none(tmp_path):
    data = {k: v for k, v in VALID_CONFIG.items() if k != "group_filter"}
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
