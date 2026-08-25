"""Unit tests for scripts/download_sdc.py - CLI parsing and RetrievalConfig
construction only, no filesystem/EBRAIN mount needed (the actual copy is
retrieve_data.run(), already covered by tests/unit/test_retrieve_pipeline.py)."""

import json

import pytest

from scripts import download_sdc
from src.retrieval.config import RetrieveItem


def _write_file_patterns(tmp_path):
    path = tmp_path / "file_patterns.json"
    path.write_text(
        json.dumps(
            {
                "sdc": {
                    "project_root": "/data/corbetta/Clinical_connectome/features/Clinical_connectome_stroke",
                    "dwi": {
                        "disconnectome-map": ["lesion/{subject_id}/{subject_id}_desc-disconnectome.nii.gz"],
                        "lesion-LF": ["lesion/{subject_id}/{subject_id}_LF-lesion_atlas-aal.csv"],
                    },
                }
            }
        )
    )
    return path


def test_defaults_select_every_dataset_and_category(tmp_path):
    file_patterns_path = _write_file_patterns(tmp_path)
    args = download_sdc._parse_args(["--file-patterns", str(file_patterns_path)])
    assert set(args.datasets) == set(download_sdc.SDC_DATASETS)
    assert set(args.categories) == set(download_sdc.SDC_CATEGORIES)
    assert args.overwrite is False


def test_unknown_dataset_rejected_by_argparse(tmp_path):
    file_patterns_path = _write_file_patterns(tmp_path)
    with pytest.raises(SystemExit):
        download_sdc._parse_args(
            ["--file-patterns", str(file_patterns_path), "--datasets", "NOT/AREALDATASET"]
        )


def test_build_config_narrows_to_requested_datasets_and_categories(tmp_path):
    file_patterns_path = _write_file_patterns(tmp_path)
    args = download_sdc._parse_args(
        [
            "--file-patterns", str(file_patterns_path),
            "--datasets", "UNIPD/WashU",
            "--categories", "disconnectome-map",
            "--output-root", str(tmp_path / "data"),
        ]
    )
    config = download_sdc._build_config(args)
    assert config.datasets == ["UNIPD/WashU"]
    assert config.retrieve == [RetrieveItem(object="sdc", pipeline=None, datatype="dwi", suffix="disconnectome-map")]
    assert config.group_filter == ["ST"]
    assert config.include_tabular_data is False
    assert config.overwrite is False


def test_build_config_overwrite_flag_propagates(tmp_path):
    file_patterns_path = _write_file_patterns(tmp_path)
    args = download_sdc._parse_args(
        ["--file-patterns", str(file_patterns_path), "--categories", "disconnectome-map", "--overwrite"]
    )
    config = download_sdc._build_config(args)
    assert config.overwrite is True


def test_build_config_input_root_overrides_registry_project_root(tmp_path):
    file_patterns_path = _write_file_patterns(tmp_path)
    custom_root = tmp_path / "other_mount" / "Clinical_connectome_stroke"
    args = download_sdc._parse_args(
        [
            "--file-patterns", str(file_patterns_path),
            "--categories", "disconnectome-map",
            "--input-root", str(custom_root),
        ]
    )
    config = download_sdc._build_config(args)
    assert config.file_patterns.project_root_for("sdc") == custom_root


def test_build_config_without_input_root_keeps_registry_project_root(tmp_path):
    file_patterns_path = _write_file_patterns(tmp_path)
    args = download_sdc._parse_args(["--file-patterns", str(file_patterns_path), "--categories", "disconnectome-map"])
    config = download_sdc._build_config(args)
    assert str(config.file_patterns.project_root_for("sdc")) == (
        "/data/corbetta/Clinical_connectome/features/Clinical_connectome_stroke"
    )


def test_build_config_missing_file_patterns_raises(tmp_path):
    args = download_sdc._parse_args(
        ["--file-patterns", str(tmp_path / "does_not_exist.json"), "--categories", "disconnectome-map"]
    )
    with pytest.raises(FileNotFoundError):
        download_sdc._build_config(args)
