"""Unit tests for src/sdc/staging.py and the check_stage1_outputs()/
check_stage2_outputs() gates in src/sdc/runner.py. Uses real (small-array)
NIfTI files via nibabel rather than mocking nibabel itself - only true
external I/O (BCBToolKit subprocess calls) is out of scope for these tests,
per code_standards.md #4."""

from pathlib import Path

import numpy as np
import nibabel as nib
import pytest

from src.sdc.config import SDCConfig
from src.sdc.manifest import ManifestRow
from src.sdc.runner import _EXPECTED_SHAPE, check_stage1_outputs, check_stage2_outputs
from src.sdc.staging import stage_subjects


def _config(*, stage2_ebrains: bool = False, stage2_presets: list[str] | None = None) -> SDCConfig:
    """Minimal SDCConfig for check_stage2_outputs, which only reads
    stage2_ebrains/stage2_presets - the other fields are never touched by
    that function, so dummy values are enough (SDCConfig itself does no
    validation in __init__, that lives in load_sdc_config)."""
    return SDCConfig(
        project="test",
        file_patterns_path=Path("unused.json"),
        file_patterns=None,
        datasets=["UNIPD/WashU"],
        group_filter=None,
        bcbtoolkit_path=Path("unused"),
        mni152_reference_path=Path("unused.nii.gz"),
        tracks_dir=None,
        cores_per_subject=1,
        stage2_ebrains=stage2_ebrains,
        stage2_presets=stage2_presets or [],
        output_root=Path("unused"),
        session_name="test",
        overwrite=False,
        run_notes=None,
    )


def _row(tmp_path, subject_id):
    lesion_path = tmp_path / "lesions" / f"{subject_id}_lesion_mask.nii.gz"
    lesion_path.parent.mkdir(parents=True, exist_ok=True)
    lesion_path.touch()
    return ManifestRow(subject_id=subject_id, dataset="UNIPD/WashU", lesion_mask_path=lesion_path)


def test_stage_subjects_creates_bids_symlinks(tmp_path):
    row = _row(tmp_path, "sub-STUNIPD0001")
    staging_dir = tmp_path / "staging"

    stage_subjects([row], staging_dir)

    link = staging_dir / "sub-STUNIPD0001" / "anat" / "sub-STUNIPD0001_lesion_mask.nii.gz"
    assert link.is_symlink()
    assert link.resolve() == row.lesion_mask_path.resolve()


def test_stage_subjects_refuses_nonempty_staging_dir(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    (staging_dir / "stray_file").touch()

    with pytest.raises(FileExistsError):
        stage_subjects([_row(tmp_path, "sub-STUNIPD0001")], staging_dir)


def _write_disconnectome(prep_dir, subject_id, shape):
    path = prep_dir / subject_id / "lesion" / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(np.zeros(shape, dtype=np.float32), affine=np.eye(4))
    nib.save(image, path)
    return path


def test_check_stage1_outputs_passes_correct_shape(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_disconnectome(prep_dir, row.subject_id, _EXPECTED_SHAPE)

    passed, failed = check_stage1_outputs([row], prep_dir)

    assert passed == [row]
    assert failed == {}


def test_check_stage1_outputs_flags_missing_file(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")

    passed, failed = check_stage1_outputs([row], prep_dir)

    assert passed == []
    assert "missing" in failed[row.subject_id]


def test_check_stage1_outputs_flags_wrong_shape(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_disconnectome(prep_dir, row.subject_id, (10, 10, 10))

    passed, failed = check_stage1_outputs([row], prep_dir)

    assert passed == []
    assert "shape" in failed[row.subject_id]


def test_check_stage1_outputs_does_not_stop_on_one_subject_failure(tmp_path):
    prep_dir = tmp_path / "prep"
    good_row = _row(tmp_path, "sub-STUNIPD0001")
    bad_row = _row(tmp_path, "sub-STUNIPD0002")
    _write_disconnectome(prep_dir, good_row.subject_id, _EXPECTED_SHAPE)
    _write_disconnectome(prep_dir, bad_row.subject_id, (5, 5, 5))

    passed, failed = check_stage1_outputs([good_row, bad_row], prep_dir)

    assert passed == [good_row]
    assert bad_row.subject_id in failed


def _write_mapstats(prep_dir, subject_id, desc, lines):
    path = prep_dir / subject_id / "lesion" / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-{desc}_mapstats.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    return path


def _write_full_stage2_output(prep_dir, subject_id, atlas_names):
    _write_mapstats(prep_dir, subject_id, "lesion", ["header\tcol", "value\t1"])
    _write_mapstats(prep_dir, subject_id, "disconnectome", ["header\tcol", "value\t1"])
    lesion_dir = prep_dir / subject_id / "lesion"
    for atlas in atlas_names:
        (lesion_dir / f"{subject_id}_LF-lesion_atlas-{atlas}.csv").write_text("a,b\n1,2\n")
        (lesion_dir / f"{subject_id}_LF-disconnectome_atlas-{atlas}.csv").write_text("a,b\n1,2\n")


def test_check_stage2_outputs_passes_complete_output(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_full_stage2_output(prep_dir, row.subject_id, ["AAL", "HarvardOxford"])

    passed, failed = check_stage2_outputs([row], prep_dir, _config(stage2_presets=["AAL", "HarvardOxford"]))

    assert passed == [row]
    assert failed == {}


def test_check_stage2_outputs_flags_missing_mapstats(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")

    passed, failed = check_stage2_outputs([row], prep_dir, _config())

    assert passed == []
    assert "mapstats" in failed[row.subject_id]


def test_check_stage2_outputs_flags_empty_mapstats(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_mapstats(prep_dir, row.subject_id, "lesion", ["header\tcol"])  # header only, no data row
    _write_mapstats(prep_dir, row.subject_id, "disconnectome", ["header\tcol", "value\t1"])

    passed, failed = check_stage2_outputs([row], prep_dir, _config())

    assert passed == []
    assert "lesion mapstats" in failed[row.subject_id]


def test_check_stage2_outputs_flags_missing_atlas_csvs(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_mapstats(prep_dir, row.subject_id, "lesion", ["header\tcol", "value\t1"])
    _write_mapstats(prep_dir, row.subject_id, "disconnectome", ["header\tcol", "value\t1"])
    # only 1 atlas CSV pair on disk, but 2 presets were configured

    passed, failed = check_stage2_outputs([row], prep_dir, _config(stage2_presets=["AAL", "HarvardOxford"]))

    assert passed == []
    assert "atlas CSV" in failed[row.subject_id]


def test_check_stage2_outputs_skips_atlas_count_check_when_no_atlas_configured(tmp_path):
    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_mapstats(prep_dir, row.subject_id, "lesion", ["header\tcol", "value\t1"])
    _write_mapstats(prep_dir, row.subject_id, "disconnectome", ["header\tcol", "value\t1"])

    passed, failed = check_stage2_outputs([row], prep_dir, _config(stage2_ebrains=False, stage2_presets=[]))

    assert passed == [row]
    assert failed == {}


def test_check_stage2_outputs_uses_real_bcblib_ebrains_atlas_count(tmp_path):
    """Regression test: expected_atlas_count for stage2_ebrains=True must be
    read from bcblib's own EBRAINS_ATLAS_SPECS, not a hardcoded number - a
    prior version of this check hardcoded 14 when bcblib actually ships 15,
    which would have failed every stage2_ebrains subject's check in
    production (see docs/guides/compute_sdc.md, stage2_ebrains row)."""
    from bcblib.tools.lesion_features._constants import EBRAINS_ATLAS_SPECS

    prep_dir = tmp_path / "prep"
    row = _row(tmp_path, "sub-STUNIPD0001")
    _write_full_stage2_output(prep_dir, row.subject_id, EBRAINS_ATLAS_SPECS)

    passed, failed = check_stage2_outputs([row], prep_dir, _config(stage2_ebrains=True))

    assert passed == [row]
    assert failed == {}


def test_check_stage2_outputs_does_not_stop_on_one_subject_failure(tmp_path):
    prep_dir = tmp_path / "prep"
    good_row = _row(tmp_path, "sub-STUNIPD0001")
    bad_row = _row(tmp_path, "sub-STUNIPD0002")
    _write_full_stage2_output(prep_dir, good_row.subject_id, ["AAL"])
    # bad_row: no output written at all

    passed, failed = check_stage2_outputs([good_row, bad_row], prep_dir, _config(stage2_presets=["AAL"]))

    assert passed == [good_row]
    assert bad_row.subject_id in failed
