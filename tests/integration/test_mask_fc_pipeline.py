"""Integration test: full mask_fc.py CLI run (main()) on synthetic data.

No EBRAIN mount needed - mask_fc operates on already-local files, so this is
a pure tmp_path E2E, always runs (no skipif).
"""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.pipeline import mask_fc

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _make_atlas(atlas_dir, combo):
    atlas_dir = atlas_dir / f"atlas-{combo}"
    atlas_dir.mkdir(parents=True, exist_ok=True)
    data = np.zeros(_SHAPE, dtype=np.int32)
    data[0:5, 0:5, 0:5] = 1
    data[5:10, 5:10, 5:10] = 2
    nib.save(nib.Nifti1Image(data, _AFFINE), atlas_dir / f"atlas-{combo}_space-MNI152NLin6Asym_res-2_dseg.nii.gz")
    pd.DataFrame({"index": [1, 2], "label": ["Region_A", "Region_B"]}).to_csv(
        atlas_dir / f"atlas-{combo}_dseg.tsv", sep="\t", index=False
    )


def _make_subject(data_root, dataset, subject, combo, node_names, lesion_voxels):
    lesion_dir = data_root / dataset / "manual_masks" / subject / "anat"
    lesion_dir.mkdir(parents=True, exist_ok=True)
    lesion_data = np.zeros(_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        lesion_data[voxel] = 1.0
    nib.save(nib.Nifti1Image(lesion_data, _AFFINE), lesion_dir / f"{subject}_label-lesion_mask.nii.gz")

    fc_dir = data_root / dataset / "features" / subject / "func"
    fc_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    m = rng.normal(size=(len(node_names), len(node_names)))
    values = (m + m.T) / 2
    np.fill_diagonal(values, 1.0)
    pd.DataFrame(values, index=node_names, columns=node_names).to_csv(
        fc_dir / f"{subject}_FC-pearson_atlas-{combo}.csv", sep="\t"
    )


def _write_config(tmp_path, data_root, atlas_root, output_root, overrides=None):
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "dataset": "siteA",
        "atlas_root": str(atlas_root),
        "atlas_combos": ["ComboX"],
        "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        "fc_glob_template": "features/*/func/*_FC-pearson_atlas-{combo}.csv",
        "min_coverage": 0.5,
        "resample_interpolation": "nearest",
        "binarize_threshold": 0.5,
        "output_root": str(output_root),
        "session_name": "s1",
        "overwrite": False,
    }
    cfg.update(overrides or {})
    path = tmp_path / "mask_fc.json"
    path.write_text(json.dumps(cfg))
    return path


def _all_voxels_in_block(block):
    xs, ys, zs = (range(s.start, s.stop) for s in block)
    return [(x, y, z) for x in xs for y in ys for z in zs]


def test_mask_fc_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(mask_fc, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(mask_fc, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    atlas_root = tmp_path / "atlases"
    output_root = tmp_path / "out"
    node_names = ["Region_A", "Region_B"]
    _make_atlas(atlas_root, "ComboX")
    _make_subject(data_root, "siteA", "sub-STUNIPD0001", "ComboX", node_names, _all_voxels_in_block(np.s_[0:5, 0:5, 0:5]))
    _make_subject(data_root, "siteA", "sub-STUNIPD0002", "ComboX", node_names, [])

    config_path = _write_config(tmp_path, data_root, atlas_root, output_root)
    exit_code = mask_fc.main(["--config", str(config_path)])
    assert exit_code == 0

    combo_dir = output_root / "ComboX"
    assert (combo_dir / "sub-STUNIPD0001_masked_fc.csv").is_file()
    assert (combo_dir / "sub-STUNIPD0002_masked_fc.csv").is_file()

    sub01 = pd.read_csv(combo_dir / "sub-STUNIPD0001_masked_fc.csv", index_col=0)
    assert sub01.loc["Region_A"].isna().all()  # fully lesioned parcel

    sub02 = pd.read_csv(combo_dir / "sub-STUNIPD0002_masked_fc.csv", index_col=0)
    assert not sub02.isna().any().any()  # no lesion at all

    summary = pd.read_csv(combo_dir / "mask_summary.csv")
    assert set(summary["subject_id"]) == {"sub-STUNIPD0001", "sub-STUNIPD0002"}

    reports = list((tmp_path / "summaries" / "testproj").glob("*.md"))
    logs = list((tmp_path / "logs" / "testproj").glob("*.log"))
    assert len(reports) == 1
    assert len(logs) == 1

    runs_csv = (output_root / "runs.csv").read_text()
    assert "s1" in runs_csv
    assert "ComboX" in runs_csv


def test_mask_fc_overwrite_false_rerun_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(mask_fc, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(mask_fc, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    atlas_root = tmp_path / "atlases"
    output_root = tmp_path / "out"
    node_names = ["Region_A", "Region_B"]
    _make_atlas(atlas_root, "ComboX")
    _make_subject(data_root, "siteA", "sub-STUNIPD0001", "ComboX", node_names, [])

    config_path = _write_config(tmp_path, data_root, atlas_root, output_root)
    assert mask_fc.main(["--config", str(config_path)]) == 0
    assert mask_fc.main(["--config", str(config_path)]) == 1


def test_mask_fc_group_filter_excludes_healthy_controls(tmp_path, monkeypatch):
    """Regression: a dataset's features/ tree can hold both patients (ST) and
    healthy controls (HC) side by side (real WashU layout). With
    group_filter=["ST"] in the config, an HC subject that has an FC file but
    (being healthy) no lesion mask must be excluded from the run entirely,
    not written out and not counted as missing_lesion."""
    monkeypatch.setattr(mask_fc, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(mask_fc, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    atlas_root = tmp_path / "atlases"
    output_root = tmp_path / "out"
    node_names = ["Region_A", "Region_B"]
    _make_atlas(atlas_root, "ComboX")
    _make_subject(data_root, "siteA", "sub-STUNIPD0001", "ComboX", node_names, [])

    # Healthy control: FC file only, no lesion mask - structurally never has one.
    fc_dir = data_root / "siteA" / "features" / "sub-STUNIPDHC0001" / "func"
    fc_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(np.eye(2), index=node_names, columns=node_names).to_csv(
        fc_dir / "sub-STUNIPDHC0001_FC-pearson_atlas-ComboX.csv", sep="\t"
    )

    config_path = _write_config(tmp_path, data_root, atlas_root, output_root, overrides={"group_filter": ["ST"]})
    exit_code = mask_fc.main(["--config", str(config_path)])
    assert exit_code == 0

    combo_dir = output_root / "ComboX"
    assert (combo_dir / "sub-STUNIPD0001_masked_fc.csv").is_file()
    assert not (combo_dir / "sub-STUNIPDHC0001_masked_fc.csv").is_file()

    summary = pd.read_csv(combo_dir / "mask_summary.csv")
    assert set(summary["subject_id"]) == {"sub-STUNIPD0001"}


def test_mask_fc_overwrite_true_removes_stale_files_from_previous_run(tmp_path, monkeypatch):
    """Regression (HIGH #10/CRITICAL #5, 2026-08): a first run with group_filter=None
    writes a masked_fc.csv for a healthy-control subject that later gets excluded once
    group_filter=["ST"] is set; a second run with overwrite=True must not leave that
    stale file sitting in output_dir for build_fc_matrix.py to silently pick up."""
    monkeypatch.setattr(mask_fc, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(mask_fc, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    atlas_root = tmp_path / "atlases"
    output_root = tmp_path / "out"
    node_names = ["Region_A", "Region_B"]
    _make_atlas(atlas_root, "ComboX")
    _make_subject(data_root, "siteA", "sub-STUNIPD0001", "ComboX", node_names, [])
    # HC subject with its own (structurally-shouldn't-exist-but-does) lesion mask, so
    # group_filter=None genuinely masks and writes it out - not just skips it as
    # missing_lesion - and group_filter=["ST"] excludes it by group instead.
    _make_subject(data_root, "siteA", "sub-STUNIPDHC0001", "ComboX", node_names, [])

    # Run 1: group_filter=None (typo/oversight) - both ST and HC get masked.
    config_path = _write_config(tmp_path, data_root, atlas_root, output_root, overrides={"group_filter": None})
    assert mask_fc.main(["--config", str(config_path)]) == 0
    combo_dir = output_root / "ComboX"
    assert (combo_dir / "sub-STUNIPDHC0001_masked_fc.csv").is_file()

    # Run 2: group_filter corrected to ["ST"], overwrite=True, same output_root.
    config_path = _write_config(
        tmp_path, data_root, atlas_root, output_root, overrides={"group_filter": ["ST"], "overwrite": True}
    )
    assert mask_fc.main(["--config", str(config_path)]) == 0

    assert (combo_dir / "sub-STUNIPD0001_masked_fc.csv").is_file()
    assert not (combo_dir / "sub-STUNIPDHC0001_masked_fc.csv").is_file()


def test_mask_fc_missing_lesion_subject_skipped_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(mask_fc, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(mask_fc, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    atlas_root = tmp_path / "atlases"
    output_root = tmp_path / "out"
    node_names = ["Region_A", "Region_B"]
    _make_atlas(atlas_root, "ComboX")
    _make_subject(data_root, "siteA", "sub-STUNIPD0001", "ComboX", node_names, [])

    # sub-STUNIPD0002 has an FC file but no lesion mask - a known, legitimate per-subject gap
    fc_dir = data_root / "siteA" / "features" / "sub-STUNIPD0002" / "func"
    fc_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(np.eye(2), index=node_names, columns=node_names).to_csv(
        fc_dir / "sub-STUNIPD0002_FC-pearson_atlas-ComboX.csv", sep="\t"
    )

    config_path = _write_config(tmp_path, data_root, atlas_root, output_root)
    exit_code = mask_fc.main(["--config", str(config_path)])
    assert exit_code == 0

    combo_dir = output_root / "ComboX"
    assert (combo_dir / "sub-STUNIPD0001_masked_fc.csv").is_file()
    assert not (combo_dir / "sub-STUNIPD0002_masked_fc.csv").is_file()
