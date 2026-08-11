"""Integration test: src.pipeline.compute_sdc._run_task end-to-end on
synthetic data, with subprocess.run mocked inside src.sdc.runner (the only
legitimate mock target here - the real bcb-lf-preprocess/bcb-lesion-features
binaries aren't available in this environment, per code_standards.md #4).

Focus: the per-subject salvage behaviour added on top of a CalledProcessError
from Stage 1/2 (see docs/debugging session 2026-07-25 handoff / .claude/plan
"Log/report strutturati per compute_sdc") - a subprocess failure must not
indiscriminately fail every subject in the chunk if some of them actually
produced valid output before the crash, and the task's own exit code must
only be 1 when zero subjects are salvageable.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import nibabel as nib
import numpy as np

from src.pipeline.compute_sdc import _link_subject, _run_aggregate, _run_task
from src.sdc.config import SDCConfig
from src.sdc.manifest import ManifestRow, write_manifest
from src.sdc.runner import _EXPECTED_SHAPE
from src.sdc.status import SubjectStatus, read_all_statuses, write_status

_AFFINE = np.eye(4)


def _write_reference(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(np.zeros(_EXPECTED_SHAPE, dtype=np.uint8), _AFFINE), path)


def _write_lesion(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.zeros(_EXPECTED_SHAPE, dtype=np.uint8)
    data[1, 1, 1] = 1
    nib.save(nib.Nifti1Image(data, _AFFINE), path)


def _config(tmp_path: Path, output_root: Path) -> SDCConfig:
    return SDCConfig(
        project="test",
        file_patterns_path=Path("unused.json"),
        file_patterns=None,
        datasets=["UNIPD/WashU"],
        group_filter=None,
        bcbtoolkit_path=tmp_path / "bcbtoolkit",
        mni152_reference_path=tmp_path / "reference.nii.gz",
        tracks_dir=None,
        cores_per_subject=1,
        stage2_ebrains=False,
        stage2_presets=[],
        output_root=output_root,
        session_name="test_session",
        overwrite=False,
        run_notes=None,
    )


def _write_disconnectome(prep_dir: Path, subject_id: str) -> None:
    path = prep_dir / subject_id / "lesion" / f"{subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(np.zeros(_EXPECTED_SHAPE, dtype=np.float32), _AFFINE), path)


def _write_stage2_output(prep_dir: Path, subject_id: str) -> None:
    lesion_dir = prep_dir / subject_id / "lesion"
    lesion_dir.mkdir(parents=True, exist_ok=True)
    (lesion_dir / f"{subject_id}_desc-lesion_mapstats.tsv").write_text("header\tcol\nvalue\t1\n")
    (lesion_dir / f"{subject_id}_desc-disconnectome_mapstats.tsv").write_text("header\tcol\nvalue\t1\n")


def _setup(tmp_path: Path, subject_ids: list[str]) -> tuple[SDCConfig, Path]:
    _write_reference(tmp_path / "reference.nii.gz")
    output_root = tmp_path / "output_root"
    config = _config(tmp_path, output_root)
    output_dir = output_root / config.session_name

    rows = []
    for subject_id in subject_ids:
        lesion_path = tmp_path / "lesions" / f"{subject_id}_lesion_mask.nii.gz"
        _write_lesion(lesion_path)
        rows.append(ManifestRow(subject_id=subject_id, dataset="UNIPD/WashU", lesion_mask_path=lesion_path))
    write_manifest(rows, output_dir / "manifest.csv")
    return config, output_dir


def _stage1_mock_writing(prep_dir: Path, subjects_to_write: set[str], returncode: int):
    def _run(command, capture_output, text):
        bids_dir = Path(command[command.index("--bids-dir") + 1])
        for subject_dir in bids_dir.iterdir():
            if subject_dir.name in subjects_to_write:
                _write_disconnectome(prep_dir, subject_dir.name)
        return subprocess.CompletedProcess(command, returncode=returncode, stdout="ok", stderr="" if returncode == 0 else "boom")

    return _run


def _stage2_mock_writing(prep_dir: Path, subjects_to_write: set[str], returncode: int):
    def _run(command, capture_output, text):
        validated_dir = Path(command[command.index("--prep-dir") + 1])
        for subject_dir in validated_dir.iterdir():
            if subject_dir.name in subjects_to_write:
                _write_stage2_output(prep_dir, subject_dir.name)
        return subprocess.CompletedProcess(command, returncode=returncode, stdout="ok", stderr="" if returncode == 0 else "boom")

    return _run


def test_run_task_full_success_writes_ok_status_with_full_stage_trace(tmp_path):
    config, output_dir = _setup(tmp_path, ["sub-A", "sub-B"])
    task_dir = output_dir / "_work" / "task_0"
    prep_dir = task_dir / "prep"

    def dispatch(command, capture_output, text):
        if command[0] == "bcb-lf-preprocess":
            return _stage1_mock_writing(prep_dir, {"sub-A", "sub-B"}, returncode=0)(command, capture_output, text)
        return _stage2_mock_writing(prep_dir, {"sub-A", "sub-B"}, returncode=0)(command, capture_output, text)

    with patch("src.sdc.runner.subprocess.run", side_effect=dispatch):
        exit_code = _run_task(config, output_dir, task_id=0, task_count=1, dry_run=False)

    assert exit_code == 0
    statuses = {s.subject_id: s for s in read_all_statuses(output_dir / "_status")[0]}
    assert statuses["sub-A"].status == "ok"
    assert statuses["sub-B"].status == "ok"
    stage_names = [event.stage for event in statuses["sub-A"].stages]
    assert stage_names == ["resample", "stage1_process", "stage1_check", "stage2_process", "stage2_check"]
    assert all(event.duration_s >= 0.0 for event in statuses["sub-A"].stages)


def test_run_task_salvages_subject_that_completed_before_stage1_crash(tmp_path):
    config, output_dir = _setup(tmp_path, ["sub-A", "sub-B"])
    task_dir = output_dir / "_work" / "task_0"
    prep_dir = task_dir / "prep"

    def dispatch(command, capture_output, text):
        if command[0] == "bcb-lf-preprocess":
            # only sub-A got written before the simulated crash on sub-B
            return _stage1_mock_writing(prep_dir, {"sub-A"}, returncode=1)(command, capture_output, text)
        return _stage2_mock_writing(prep_dir, {"sub-A"}, returncode=0)(command, capture_output, text)

    with patch("src.sdc.runner.subprocess.run", side_effect=dispatch):
        exit_code = _run_task(config, output_dir, task_id=0, task_count=1, dry_run=False)

    assert exit_code == 0
    statuses = {s.subject_id: s for s in read_all_statuses(output_dir / "_status")[0]}
    assert statuses["sub-A"].status == "ok"
    assert statuses["sub-B"].status == "failed_stage1_process"
    assert "returned non-zero exit status" in statuses["sub-B"].detail


def test_run_task_returns_1_when_no_subject_salvageable_after_stage1_crash(tmp_path):
    config, output_dir = _setup(tmp_path, ["sub-A", "sub-B"])
    task_dir = output_dir / "_work" / "task_0"
    prep_dir = task_dir / "prep"

    def dispatch(command, capture_output, text):
        return _stage1_mock_writing(prep_dir, set(), returncode=1)(command, capture_output, text)

    with patch("src.sdc.runner.subprocess.run", side_effect=dispatch):
        exit_code = _run_task(config, output_dir, task_id=0, task_count=1, dry_run=False)

    assert exit_code == 1
    statuses = {s.subject_id: s for s in read_all_statuses(output_dir / "_status")[0]}
    assert statuses["sub-A"].status == "failed_stage1_process"
    assert statuses["sub-B"].status == "failed_stage1_process"


def test_run_task_returns_1_when_stage1_binary_not_found(tmp_path):
    """Regression: FileNotFoundError/OSError from subprocess.run (e.g. the
    bcb-lf-preprocess binary not on PATH - a cluster module not loaded) used
    to propagate unhandled instead of the clean logging.error + return 1
    every other structural failure in this function gets."""
    config, output_dir = _setup(tmp_path, ["sub-A"])

    def dispatch(command, capture_output, text):
        raise FileNotFoundError("[Errno 2] No such file or directory: 'bcb-lf-preprocess'")

    with patch("src.sdc.runner.subprocess.run", side_effect=dispatch):
        exit_code = _run_task(config, output_dir, task_id=0, task_count=1, dry_run=False)

    assert exit_code == 1


def test_run_task_returns_1_when_stage2_binary_not_found(tmp_path):
    config, output_dir = _setup(tmp_path, ["sub-A"])
    task_dir = output_dir / "_work" / "task_0"
    prep_dir = task_dir / "prep"

    def dispatch(command, capture_output, text):
        if command[0] == "bcb-lf-preprocess":
            return _stage1_mock_writing(prep_dir, {"sub-A"}, returncode=0)(command, capture_output, text)
        raise FileNotFoundError("[Errno 2] No such file or directory: 'bcb-lesion-features'")

    with patch("src.sdc.runner.subprocess.run", side_effect=dispatch):
        exit_code = _run_task(config, output_dir, task_id=0, task_count=1, dry_run=False)

    assert exit_code == 1


def test_run_aggregate_isolates_corrupt_status_file_from_the_rest(tmp_path):
    """Regression: a single corrupt status file (e.g. from a task killed
    mid-write) used to abort --mode aggregate entirely, hiding every other
    subject already completed successfully. It must instead be skipped and
    reported, not fail the whole aggregate run."""
    config, output_dir = _setup(tmp_path, ["sub-A"])
    status_dir = output_dir / "_status"
    write_status(status_dir, SubjectStatus(subject_id="sub-A", task_id=0, status="ok", detail="fine"))
    (status_dir / "sub-B.json").write_text('{"subject_id": "sub-B", "task_id": 0, "stat')  # truncated

    exit_code = _run_aggregate(config, output_dir, datetime.now())

    assert exit_code == 0
    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["total"] == 1
    assert "sub-B" in manifest["unreadable_status_files"]
    assert "sub-B" in (output_dir / "config.md").read_text()


def _write_marker_dir(path: Path, content: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "marker.txt").write_text(content)


def test_link_subject_creates_symlink_when_absent(tmp_path):
    source = tmp_path / "task_0" / "prep" / "sub-A" / "lesion"
    _write_marker_dir(source, "task_0")
    destination = tmp_path / "output" / "sub-A"

    _link_subject(source, destination)

    assert destination.is_symlink()
    assert destination.resolve() == source.resolve()


def test_link_subject_is_a_noop_when_already_correctly_linked(tmp_path):
    source = tmp_path / "task_0" / "prep" / "sub-A" / "lesion"
    _write_marker_dir(source, "task_0")
    destination = tmp_path / "output" / "sub-A"
    _link_subject(source, destination)
    original_target = destination.readlink()

    _link_subject(source, destination)  # second call, same source

    assert destination.readlink() == original_target


def test_link_subject_relinks_to_newer_source(tmp_path):
    """Regression: a stale symlink from an earlier (e.g. retried) task used
    to survive forever, silently - destination.exists() alone can't tell
    "already correctly linked" from "linked to something else that still
    happens to exist", both make it True. A subject reprocessed in a later
    task (retry after a manifest rebuild) must end up pointing at the newer
    task's output, not the stale one, the next time --mode aggregate runs."""
    old_source = tmp_path / "task_0" / "prep" / "sub-A" / "lesion"
    _write_marker_dir(old_source, "task_0")
    destination = tmp_path / "output" / "sub-A"
    _link_subject(old_source, destination)
    assert destination.resolve() == old_source.resolve()

    new_source = tmp_path / "task_17" / "prep" / "sub-A" / "lesion"
    _write_marker_dir(new_source, "task_17")

    _link_subject(new_source, destination)

    assert destination.is_symlink()
    assert destination.resolve() == new_source.resolve()
