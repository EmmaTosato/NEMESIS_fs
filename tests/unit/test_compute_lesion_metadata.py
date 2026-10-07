"""Unit tests for src/pipeline/compute_lesion_metadata.py - synthetic .nii.gz fixtures, no
EBRAIN mount needed. Full main() CLI runs, same convention as
tests/unit/test_populate_metadata.py (a pipeline whose output is a metadata file, tested
through its CLI rather than only its functions).

Two grids in every fixture, in the same relationship the real data has: the masks are written
on the fine grid (natively, no resampling - as the real 1mm manual masks are), and the coarse
grid is an exact 2x subsample of it (as the 2mm production template is).
"""

import json
import logging

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.features.lesion_location import location_columns
from src.pipeline import compute_lesion_metadata as pipeline
from tests.unit.location_fixtures import location_config_block, make_location_spec

_FINE_SHAPE = (20, 20, 20)
_FINE_AFFINE = np.array(
    [[1.0, 0.0, 0.0, -10.0], [0.0, 1.0, 0.0, -10.0], [0.0, 0.0, 1.0, -10.0], [0.0, 0.0, 0.0, 1.0]]
)
_COARSE_SHAPE = (10, 10, 10)
_COARSE_AFFINE = np.array(
    [[2.0, 0.0, 0.0, -10.0], [0.0, 2.0, 0.0, -10.0], [0.0, 0.0, 2.0, -10.0], [0.0, 0.0, 0.0, 1.0]]
)


def _make_lesion_subject(data_root, dataset, subject_id, lesion_voxels):
    subject_dir = data_root / dataset / "manual_masks" / subject_id / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(_FINE_SHAPE, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[voxel] = 1.0
    nib.save(nib.Nifti1Image(volume, _FINE_AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _write_grid_files(tmp_path, name, shape, affine, brain_region):
    template_path = tmp_path / f"{name}_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(shape, dtype=np.float32), affine), template_path)
    brain = np.zeros(shape, dtype=np.float32)
    brain[brain_region] = 1.0
    brain_mask_path = tmp_path / f"{name}_brain_mask.nii.gz"
    nib.save(nib.Nifti1Image(brain, affine), brain_mask_path)
    return {"reference_template_path": str(template_path), "brain_mask_path": str(brain_mask_path)}


def _write_config(tmp_path, data_root, output_path, overrides=None):
    """A two-grid config whose brain masks exclude k=0 (fine) / k=0 (coarse), so a lesion voxel
    placed at k=0 is genuinely out-of-brain on both grids."""
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "output_path": str(output_path),
        "datasets": ["siteA"],
        "group_filter": ["ST"],
        "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "grids": {
            "fine": _write_grid_files(
                tmp_path, "fine", _FINE_SHAPE, _FINE_AFFINE, (slice(None), slice(None), slice(2, None))
            ),
            "coarse": _write_grid_files(
                tmp_path, "coarse", _COARSE_SHAPE, _COARSE_AFFINE, (slice(None), slice(None), slice(1, None))
            ),
        },
        "correct_out_of_brain": True,
        "side_threshold": 0.2,
        # coarse voxel (1,1,1) is cortex only and (2,1,1) white matter only: fine (2,2,2) and (4,2,2)
        "location": location_config_block(
            make_location_spec(tmp_path, _COARSE_SHAPE, _COARSE_AFFINE, "coarse", cortex=[(1, 1, 1)], white=[(2, 1, 1)])
        ),
        "overwrite": False,
        "run_notes": "test",
    }
    cfg.update(overrides or {})
    path = tmp_path / "compute_lesion_metadata.json"
    path.write_text(json.dumps(cfg))
    return path


def _redirect_outputs(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(pipeline, "LOGS_ROOT", tmp_path / "logs")


def test_compute_lesion_metadata_end_to_end(tmp_path, monkeypatch, caplog):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    # left-hemisphere lesion, fully inside the brain on both grids (even fine indices, k >= 2)
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2), (4, 2, 2)])
    # half of it at k=0, i.e. outside the brain on both grids -> fraction 0.5, volume halved
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0002", [(2, 2, 2), (4, 2, 2), (2, 2, 0), (4, 2, 0)])
    output_path = tmp_path / "lesion_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    with caplog.at_level(logging.INFO):
        exit_code = pipeline.main(["--config", str(config_path)])

    assert exit_code == 0
    assert "run duration:" in caplog.text

    metrics = pd.read_csv(output_path)
    assert list(metrics.columns) == [
        "subject_id", "dataset",
        "lesion_volume_voxels_fine", "out_of_brain_fraction_fine",
        "laterality_index_fine", "lesion_side_fine",
        "lesion_volume_voxels_coarse", "out_of_brain_fraction_coarse",
        "laterality_index_coarse", "lesion_side_coarse",
    ] + location_columns("coarse")
    by_id = metrics.set_index("subject_id")
    assert list(by_id.index) == ["sub-STUNIPD0001", "sub-STUNIPD0002"]
    assert by_id.loc["sub-STUNIPD0001", "out_of_brain_fraction_fine"] == 0.0
    assert by_id.loc["sub-STUNIPD0001", "lesion_volume_voxels_fine"] == 2
    assert by_id.loc["sub-STUNIPD0002", "out_of_brain_fraction_fine"] == 0.5
    assert by_id.loc["sub-STUNIPD0002", "lesion_volume_voxels_fine"] == 2  # post-correction
    assert set(by_id["lesion_side_fine"]) == {"left"}
    # location, on the coarse grid: half cortex, half white matter (exact tie -> the earlier category);
    # the voxels outside the brain are not in the denominator
    for subject in ("sub-STUNIPD0001", "sub-STUNIPD0002"):
        assert by_id.loc[subject, "location_cortex_only_coarse"] == 0.5
        assert by_id.loc[subject, "location_white_matter_only_coarse"] == 0.5
        assert by_id.loc[subject, "location_dominant_coarse"] == "cortex_only"

    reports = list((tmp_path / "summaries").glob("*.md"))
    logs = list((tmp_path / "logs").glob("*.log"))
    assert len(reports) == 1 and len(logs) == 1
    report = reports[0].read_text()
    assert "### fine" in report and "### coarse" in report
    assert "## Sede della lesione (coarse)" in report


def test_compute_lesion_metadata_writes_its_own_config_beside_the_csv(tmp_path, monkeypatch):
    """lessons_learned.md #18/#36: a CSV whose grids/correction/threshold are unknown cannot be
    interpreted, and this pipeline has no per-run output directory to record them in - so the
    resolved config is written next to the CSV, by the run that produced it."""
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    assert pipeline.main(["--config", str(config_path)]) == 0

    written = json.loads((tmp_path / "lesion_metadata.config.json").read_text())
    assert written["correct_out_of_brain"] is True
    assert written["side_threshold"] == 0.2
    assert list(written["grids"]) == ["fine", "coarse"]
    assert written["location"]["grid"] == "coarse"
    assert set(written["location"]["atlases"]) == {"cortical", "subcortical", "cerebellum"}
    assert "written" in written


def test_compute_lesion_metadata_skips_when_output_exists_and_overwrite_false(tmp_path, monkeypatch):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    output_path.write_text("subject_id,dataset\nsub-fake,siteA\n")
    before = output_path.read_text()
    config_path = _write_config(tmp_path, data_root, output_path)

    exit_code = pipeline.main(["--config", str(config_path)])

    assert exit_code == 0
    assert output_path.read_text() == before  # untouched - the expensive part is never re-paid
    assert not (tmp_path / "summaries").exists()  # never even started a run


def test_compute_lesion_metadata_overwrite_replaces_the_csv(tmp_path, monkeypatch):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    output_path.write_text("subject_id,dataset\nsub-fake,siteA\n")
    config_path = _write_config(tmp_path, data_root, output_path, overrides={"overwrite": True})

    assert pipeline.main(["--config", str(config_path)]) == 0

    metrics = pd.read_csv(output_path)
    assert list(metrics["subject_id"]) == ["sub-STUNIPD0001"]  # replaced, not appended to sub-fake


def test_compute_lesion_metadata_dry_run_opens_no_mask_and_writes_no_csv(tmp_path, monkeypatch):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)

    real_load = nib.load
    loaded = []

    def counting_load(path, *args, **kwargs):
        loaded.append(str(path))
        return real_load(path, *args, **kwargs)

    monkeypatch.setattr("src.features.lesion.nib.load", counting_load)
    exit_code = pipeline.main(["--config", str(config_path), "--dry-run"])

    assert exit_code == 0
    assert not output_path.exists()
    assert not (tmp_path / "lesion_metadata.config.json").exists()
    assert loaded == []  # not even a template: nothing is opened before the config is known good
    assert len(list((tmp_path / "summaries").glob("*.md"))) == 1


def test_compute_lesion_metadata_grid_missing_brain_mask_returns_1(tmp_path, monkeypatch):
    """brain_mask_path is required for every grid here, unlike in build_lesion_matrix.json where
    the correction it feeds is optional - a grid without one cannot produce either of the two
    metrics it exists to produce."""
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    template_path = tmp_path / "lonely_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_FINE_SHAPE, dtype=np.float32), _FINE_AFFINE), template_path)
    config_path = _write_config(
        tmp_path, data_root, output_path,
        overrides={"grids": {"fine": {"reference_template_path": str(template_path)}}},
    )

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_lesion_metadata_duplicate_grid_name_is_impossible_in_json(tmp_path, monkeypatch):
    """A JSON object cannot hold the same key twice (the last one silently wins), so a duplicate
    grid name can only reach validate_lesion_grids from a direct library call - which
    tests/unit/test_features_lesion.py covers. What this test pins down is the neighbouring
    failure a config CAN express: a grid name that is not usable as a column suffix."""
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    grid_files = _write_grid_files(
        tmp_path, "fine", _FINE_SHAPE, _FINE_AFFINE, (slice(None), slice(None), slice(2, None))
    )
    config_path = _write_config(tmp_path, data_root, output_path, overrides={"grids": {"2 mm": grid_files}})

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_lesion_metadata_unknown_dataset_returns_1(tmp_path, monkeypatch):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path, overrides={"datasets": ["siteB"]})

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def _rewrite_config(config_path, mutate):
    cfg = json.loads(config_path.read_text())
    mutate(cfg)
    config_path.write_text(json.dumps(cfg))


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda cfg: cfg.pop("location"), id="missing_location"),
        pytest.param(lambda cfg: cfg["location"].update(grid="2mm"), id="grid_is_not_one_of_the_grids"),
        pytest.param(lambda cfg: cfg["location"].update(extra=1), id="unknown_key"),
        pytest.param(lambda cfg: cfg["location"]["atlases"].pop("cerebellum"), id="missing_atlas"),
        pytest.param(lambda cfg: cfg["location"]["atlases"].update(extra={}), id="unknown_atlas"),
        pytest.param(lambda cfg: cfg["location"]["atlases"]["cortical"].pop("labels_path"), id="atlas_without_labels"),
        pytest.param(lambda cfg: cfg["location"]["atlases"]["cortical"].update(image_path=""), id="empty_atlas_path"),
    ],
)
def test_compute_lesion_metadata_bad_location_config_returns_1(tmp_path, monkeypatch, mutate):
    """Every shape of a wrong `location` block is rejected at config load, before any mask or atlas
    is opened - there is no run without it, since the CSV's columns would depend on it."""
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)
    _rewrite_config(config_path, mutate)

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()


def test_compute_lesion_metadata_missing_atlas_file_returns_1_before_reading_any_mask(tmp_path, monkeypatch):
    _redirect_outputs(monkeypatch, tmp_path)
    data_root = tmp_path / "data"
    _make_lesion_subject(data_root, "siteA", "sub-STUNIPD0001", [(2, 2, 2)])
    output_path = tmp_path / "lesion_metadata.csv"
    config_path = _write_config(tmp_path, data_root, output_path)
    _rewrite_config(
        config_path, lambda cfg: cfg["location"]["atlases"]["cortical"].update(image_path=str(tmp_path / "nope.nii.gz"))
    )

    assert pipeline.main(["--config", str(config_path)]) == 1
    assert not output_path.exists()
