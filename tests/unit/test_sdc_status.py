"""Unit tests for src/sdc/status.py: SubjectStatus/StageEvent round-trip
through write_status/read_all_statuses, and validation of unknown
status/stage/outcome values."""

import pytest

from src.sdc.status import KNOWN_STATUSES, StageEvent, SubjectStatus, read_all_statuses, write_status


def test_stage_event_rejects_unknown_stage():
    with pytest.raises(ValueError):
        StageEvent(stage="not_a_stage", outcome="ok", duration_s=1.0, detail="x")


def test_stage_event_rejects_unknown_outcome():
    with pytest.raises(ValueError):
        StageEvent(stage="resample", outcome="not_an_outcome", duration_s=1.0, detail="x")


def test_subject_status_rejects_unknown_status():
    with pytest.raises(ValueError):
        SubjectStatus(subject_id="sub-STUNIPD0001", task_id=0, status="not_a_status", detail="x")


def test_subject_status_defaults_to_no_stages():
    status = SubjectStatus(subject_id="sub-STUNIPD0001", task_id=0, status="ok", detail="x")
    assert status.stages == ()


def test_failed_stage2_check_is_a_known_status():
    assert "failed_stage2_check" in KNOWN_STATUSES


def test_write_and_read_status_round_trips_stages(tmp_path):
    status_dir = tmp_path / "_status"
    stages = (
        StageEvent(stage="resample", outcome="ok", duration_s=0.5, detail="conforming"),
        StageEvent(stage="stage1_process", outcome="ok", duration_s=120.0, detail="stage1 subprocess completed"),
        StageEvent(stage="stage1_check", outcome="ok", duration_s=0.1, detail="disconnectome output verified"),
    )
    written = SubjectStatus(subject_id="sub-STUNIPD0001", task_id=3, status="ok", detail="stage1+stage2 completed", stages=stages)

    write_status(status_dir, written)
    [read], failed = read_all_statuses(status_dir)

    assert read == written
    assert failed == {}


def test_read_all_statuses_reconstructs_stage_event_type(tmp_path):
    status_dir = tmp_path / "_status"
    write_status(
        status_dir,
        SubjectStatus(
            subject_id="sub-STUNIPD0001",
            task_id=0,
            status="failed_stage1_check",
            detail="shape mismatch",
            stages=(StageEvent(stage="stage1_check", outcome="failed", duration_s=0.2, detail="shape mismatch"),),
        ),
    )

    [read], failed = read_all_statuses(status_dir)

    assert isinstance(read.stages[0], StageEvent)
    assert read.stages[0].stage == "stage1_check"
    assert failed == {}


def test_read_all_statuses_raises_if_status_dir_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_all_statuses(tmp_path / "does_not_exist")


def test_read_all_statuses_isolates_corrupt_file_from_the_rest(tmp_path):
    """Regression: a truncated/corrupt status file (e.g. from a task killed
    mid-write before write_status became atomic) used to raise and abort
    reading for every other subject in the same directory - one bad file
    must not hide every good one."""
    status_dir = tmp_path / "_status"
    write_status(
        status_dir, SubjectStatus(subject_id="sub-STUNIPD0001", task_id=0, status="ok", detail="fine")
    )
    (status_dir / "sub-STUNIPD0002.json").write_text('{"subject_id": "sub-STUNIPD0002", "task_id": 0, "stat')  # truncated

    statuses, failed = read_all_statuses(status_dir)

    assert [s.subject_id for s in statuses] == ["sub-STUNIPD0001"]
    assert "sub-STUNIPD0002" in failed


def test_write_status_is_atomic_no_tmp_file_left_behind(tmp_path):
    status_dir = tmp_path / "_status"
    write_status(status_dir, SubjectStatus(subject_id="sub-STUNIPD0001", task_id=0, status="ok", detail="fine"))

    files = sorted(p.name for p in status_dir.iterdir())
    assert files == ["sub-STUNIPD0001.json"]  # no leftover .tmp/hidden file
