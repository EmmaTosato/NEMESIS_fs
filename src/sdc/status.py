"""Per-subject outcome tracking, one JSON file per subject under
<output_dir>/_status/. This is how `--mode aggregate` learns what every
(possibly concurrently-run, possibly SLURM-array-parallel) `--mode run` task
did, without the tasks needing to coordinate with each other directly -
each task only ever writes its own subjects' files.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

KNOWN_STATUSES = (
    "ok",
    "failed_resample",
    "failed_stage1_process",
    "failed_stage1_check",
    "failed_stage2_process",
    "dry_run",
)


@dataclass(frozen=True)
class SubjectStatus:
    subject_id: str
    task_id: int
    status: str
    detail: str

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
        statuses.append(SubjectStatus(**raw))
    return statuses
