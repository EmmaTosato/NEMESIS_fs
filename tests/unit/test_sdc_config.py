"""Unit tests for src/sdc/config.py."""

import json

import pytest

from src.sdc.config import load_sdc_config

_LESION_LEAF = ("lesion", "manual_masks", "anat", "lesion_mask")


def _write_file_patterns(tmp_path, project_root):
    path = tmp_path / "file_patterns.json"
    path.write_text(
        json.dumps(
            {
                "lesion": {
                    "project_root": str(project_root),
                    "manual_masks": {"anat": {"lesion_mask": ["{subject_id}/anat/{subject_id}_lesion_mask.nii.gz"]}},
                }
            }
        )
    )
    return path


def _write_bcbtoolkit(tmp_path):
    bcb_dir = tmp_path / "BCBToolKit"
    bcb_dir.mkdir()
    (bcb_dir / "run_disco.sh").touch()
    mni152_dir = bcb_dir / "Tools" / "extraFiles"
    mni152_dir.mkdir(parents=True)
    (mni152_dir / "MNI152.nii.gz").touch()
    return bcb_dir


def _base_config(tmp_path):
    return {
        "project": "clinical_connectome",
        "file_patterns": str(_write_file_patterns(tmp_path, tmp_path / "data")),
        "datasets": ["UNIPD/WashU"],
        "group_filter": ["ST"],
        "bcbtoolkit_path": str(_write_bcbtoolkit(tmp_path)),
        "tracks_dir": None,
        "cores_per_subject": 4,
        "stage2_ebrains": True,
        "stage2_presets": [],
        "output_root": "data/derived/sdc",
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }


def _write(tmp_path, overrides):
    cfg = {**_base_config(tmp_path), **overrides}
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg))
    return path


def test_valid_config(tmp_path):
    config = load_sdc_config(_write(tmp_path, {}))
    assert config.project == "clinical_connectome"
    assert config.cores_per_subject == 4
    assert config.stage2_ebrains is True
    assert config.tracks_dir is None
    assert config.mni152_reference_path.is_file()
    assert config.file_patterns.has(*_LESION_LEAF)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_sdc_config(tmp_path / "nope.json")


def test_bcbtoolkit_path_without_run_disco_raises(tmp_path):
    empty_dir = tmp_path / "not_bcb"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="run_disco.sh"):
        load_sdc_config(_write(tmp_path, {"bcbtoolkit_path": str(empty_dir)}))


def test_tracks_dir_must_exist(tmp_path):
    with pytest.raises(ValueError, match="tracks_dir"):
        load_sdc_config(_write(tmp_path, {"tracks_dir": str(tmp_path / "nope")}))


def test_bcbtoolkit_path_without_mni152_reference_raises(tmp_path):
    bcb_dir = tmp_path / "BCBToolKitNoReference"
    bcb_dir.mkdir()
    (bcb_dir / "run_disco.sh").touch()
    with pytest.raises(ValueError, match="Tools/extraFiles/MNI152.nii.gz"):
        load_sdc_config(_write(tmp_path, {"bcbtoolkit_path": str(bcb_dir)}))


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"cores_per_subject": 0}, "positive integer"),
        ({"cores_per_subject": -1}, "positive integer"),
        ({"cores_per_subject": True}, "positive integer"),
        ({"datasets": []}, "must not be empty"),
        ({"datasets": ["UNIPD/WashU", "UNIPD/WashU"]}, "duplicate entries"),
        ({"group_filter": ["XX"]}, "unknown group"),
        ({"stage2_ebrains": "yes"}, "must be a boolean"),
        ({"project": ""}, "non-empty string"),
    ],
)
def test_invalid_configs_raise_value_error(tmp_path, overrides, match):
    with pytest.raises(ValueError, match=match):
        load_sdc_config(_write(tmp_path, overrides))


def test_top_level_must_be_object(tmp_path):
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(["not", "an", "object"]))
    with pytest.raises(ValueError, match="top-level content must be a JSON object"):
        load_sdc_config(path)
