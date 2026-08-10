"""Per-subject outcome tracking, one JSON file per subject under
<output_dir>/_status/. This is how `--mode aggregate` learns what every
(possibly concurrently-run, possibly SLURM-array-parallel) `--mode run` task
did, without the tasks needing to coordinate with each other directly -
each task only ever writes its own subjects' files.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

KNOWN_STATUSES = (
    "ok",
    "failed_resample",
    "failed_stage1_process",
    "failed_stage1_check",
    "failed_stage2_process",
    "failed_stage2_check",
    "dry_run",
)

KNOWN_STAGES = ("resample", "stage1_process", "stage1_check", "stage2_process", "stage2_check")
KNOWN_OUTCOMES = ("ok", "failed", "process_error")


@dataclass(frozen=True)
class StageEvent:
    """One stage a subject passed through during `--mode run`, for the
    structured per-subject report - see SubjectStatus.stages. duration_s is
    per-subject for resample/stage1_check/stage2_check (each subject is
    processed individually there), but shared across the whole task chunk
    for stage1_process/stage2_process - bcb-lf-preprocess/bcb-lesion-features
    operate on a whole directory at once, with no per-subject timing to
    measure (see src/sdc/runner.py)."""

    stage: str
    outcome: str
    duration_s: float
    detail: str

    def __post_init__(self) -> None:
        if self.stage not in KNOWN_STAGES:
            raise ValueError(f"StageEvent: unknown stage {self.stage!r} (known: {KNOWN_STAGES})")
        if self.outcome not in KNOWN_OUTCOMES:
            raise ValueError(f"StageEvent: unknown outcome {self.outcome!r} (known: {KNOWN_OUTCOMES})")


@dataclass(frozen=True)
class SubjectStatus:
    subject_id: str
    task_id: int
    status: str
    detail: str
    stages: tuple[StageEvent, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.status not in KNOWN_STATUSES:
            raise ValueError(f"SubjectStatus: unknown status {self.status!r} (known: {KNOWN_STATUSES})")


def write_status(status_dir: Path, status: SubjectStatus) -> None:
    """Writes <status_dir>/<subject_id>.json atomically (temp-file-then-rename,
    same pattern as src/utils/artifacts.py::save_matrix) - a SLURM task
    killed (OOM/timeout) mid-write must never leave a truncated JSON file,
    which read_all_statuses could otherwise fail to parse."""
    status_dir.mkdir(parents=True, exist_ok=True)
    path = status_dir / f"{status.subject_id}.json"
    fd, tmp_name = tempfile.mkstemp(dir=status_dir, prefix=f".{status.subject_id}_tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(asdict(status), indent=2))
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def read_all_statuses(status_dir: Path) -> tuple[list[SubjectStatus], dict[str, str]]:
    """Returns (statuses, failed): failed maps the offending file's stem
    (best-effort subject_id - a truncated file may not even parse far
    enough to read the real one) -> error reason, for any status file that
    isn't valid JSON or doesn't reconstruct into a SubjectStatus. One
    corrupt file (e.g. from a task killed mid-write before write_status's
    atomic rename above existed, or a leftover from before this fix) must
    not abort aggregation for every other subject already completed
    successfully - same per-item isolation as
    resample_nonconforming_rows/check_stage1_outputs in this same pipeline."""
    if not status_dir.is_dir():
        raise FileNotFoundError(f"status dir not found: {status_dir} - has `--mode run` been executed yet?")
    statuses = []
    failed: dict[str, str] = {}
    for path in sorted(status_dir.glob("*.json")):
        try:
            with path.open() as f:
                raw = json.load(f)
            raw["stages"] = tuple(StageEvent(**event) for event in raw.get("stages", []))
            statuses.append(SubjectStatus(**raw))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            failed[path.stem] = str(exc)
    return statuses, failed
