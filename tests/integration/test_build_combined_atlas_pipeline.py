"""Integration test: full build_combined_atlas.py CLI run (main()) on the real,
small atlas files checked into assets/atlases/ - no synthetic fixture needed
or wanted here, since the whole point of the pipeline is to validate exactly
these two files.
"""

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.pipeline import build_combined_atlas

_ASSETS = Path(__file__).resolve().parents[2] / "assets" / "atlases"
_CORTICAL_PATH = _ASSETS / "MNI_Glasser_HCP_v1.0.nii.gz"
_SUBCORTICAL_PATH = _ASSETS / "HarvardOxford-sub-maxprob-thr25-2mm.nii.gz"

pytestmark = pytest.mark.skipif(
    not (_CORTICAL_PATH.is_file() and _SUBCORTICAL_PATH.is_file()),
    reason="real atlas files not present under assets/atlases/",
)


def _write_config(tmp_path):
    output_atlas_path = tmp_path / "combined.nii.gz"
    output_label_table_path = tmp_path / "combined_labels.csv"
    cfg = {
        "cortical_atlas_path": str(_CORTICAL_PATH),
        "subcortical_atlas_path": str(_SUBCORTICAL_PATH),
        "output_atlas_path": str(output_atlas_path),
        "output_label_table_path": str(output_label_table_path),
        "overwrite": False,
    }
    config_path = tmp_path / "cfg.json"
    config_path.write_text(json.dumps(cfg))
    return config_path, output_atlas_path, output_label_table_path


def test_build_combined_atlas_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path, output_atlas_path, output_label_table_path = _write_config(tmp_path)

    exit_code = build_combined_atlas.main(["--config", str(config_path)])

    assert exit_code == 0
    assert output_atlas_path.is_file()
    assert output_label_table_path.is_file()

    combined_img = nib.load(output_atlas_path)
    combined_labels = np.asarray(combined_img.get_fdata()).astype(np.int64)
    unique_labels = set(np.unique(combined_labels).tolist()) - {0}
    assert len(unique_labels) == 372
    assert unique_labels == set(range(1, 181)) | {181 + i for i in range(6)} | set(range(1001, 1181)) | {
        1181 + i for i in range(6)
    }

    label_table = pd.read_csv(output_label_table_path)
    assert len(label_table) == 372
    assert set(label_table["source"]) == {"glasser_mmp", "harvard_oxford_subcortical"}
    assert (label_table["source"] == "harvard_oxford_subcortical").sum() == 12
    assert set(label_table.loc[label_table["source"] == "harvard_oxford_subcortical", "name"]) == {
        f"{hemi}_{name}"
        for hemi in ("L", "R")
        for name in ("Thalamus", "Caudate", "Putamen", "Pallidum", "Hippocampus", "Amygdala")
    }


def test_build_combined_atlas_refuses_to_overwrite_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path, output_atlas_path, _label_table_path = _write_config(tmp_path)
    build_combined_atlas.main(["--config", str(config_path)])

    exit_code = build_combined_atlas.main(["--config", str(config_path)])

    assert exit_code == 1
