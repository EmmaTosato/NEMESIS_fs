"""Per-subject outcome tracking, one JSON file per subject under
<output_dir>/_status/. This is how `--mode aggregate` learns what every
(possibly concurrently-run, possibly SLURM-array-parallel) `--mode run` task
did, without the tasks needing to coordinate with each other directly -
each task only ever writes its own subjects' files.
"""

from __future__ import annotations

import json
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
    status_dir.mkdir(parents=True, exist_ok=True)
    path = status_dir / f"{status.subject_id}.json"
    path.write_text(json.dumps(asdict(status), indent=2))


def read_all_statuses(status_dir: Path) -> list[SubjectStatus]:
    if not status_dir.is_dir():
        raise FileNotFoundError(f"status dir not found: {status_dir} - has `--mode run` been executed yet?")
    statuses = []
    for path in sorted(status_dir.glob("*.json")):
        with path.open() as f:
            raw = json.load(f)
        raw["stages"] = tuple(StageEvent(**event) for event in raw.get("stages", []))
        statuses.append(SubjectStatus(**raw))
    return statuses
