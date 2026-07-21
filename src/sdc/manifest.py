"""Subject manifest for compute_sdc: the single ordered list of (subject_id,
dataset, lesion_mask_path) that every downstream task (SLURM array index or
local worker) slices into a chunk. Built once, read many times - see
docs/guides/compute_sdc.md, "Perche' un manifest condiviso".
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

from src.retrieval.dataset import Dataset
from src.sdc.config import LESION_ITEM, SDCConfig

_MANIFEST_FIELDS = ("subject_id", "dataset", "lesion_mask_path")


@dataclass(frozen=True)
class ManifestRow:
    subject_id: str
    dataset: str
    lesion_mask_path: Path


def build_manifest(config: SDCConfig) -> tuple[list[ManifestRow], dict[str, str]]:
    """Discover every (subject, lesion mask) pair for config.datasets/group_filter.

    Returns (rows, excluded) - excluded maps subject_id -> reason, for
    subjects seen on disk but not included in rows (missing lesion mask,
    more than one lesion mask matching the registry - ambiguous, not
    resolved arbitrarily, see lessons_learned.md #3 - or the same subject_id
    appearing in more than one configured dataset, see lessons_learned.md
    #5). Excluded subjects never silently disappear: every one is logged and
    returned, so a run's manifest report can show exactly who was left out
    and why."""
    rows: list[ManifestRow] = []
    excluded: dict[str, str] = {}
    seen_subject_to_dataset: dict[str, str] = {}

    for dataset_name in config.datasets:
        dataset = Dataset(dataset_name, config.file_patterns)
        subject_ids = dataset.subjects("lesion", "manual_masks", group=None)
        if config.group_filter is not None:
            subject_ids = [s for s in subject_ids if dataset.group_of(s) in config.group_filter]

        for subject_id in subject_ids:
            if subject_id in seen_subject_to_dataset:
                excluded[subject_id] = (
                    f"duplicate subject_id across datasets ({seen_subject_to_dataset[subject_id]!r} "
                    f"and {dataset_name!r})"
                )
                logging.warning("manifest: excluding %s - %s", subject_id, excluded[subject_id])
                continue
            seen_subject_to_dataset[subject_id] = dataset_name

            matches = dataset.resolve(subject_id, LESION_ITEM)
            if not matches:
                excluded[subject_id] = f"no lesion mask found ({dataset.describe_absence(subject_id, LESION_ITEM)})"
                logging.warning("manifest: excluding %s - %s", subject_id, excluded[subject_id])
                continue
            if len(matches) > 1:
                excluded[subject_id] = f"ambiguous - {len(matches)} lesion masks matched: {matches}"
                logging.warning("manifest: excluding %s - %s", subject_id, excluded[subject_id])
                continue

            rows.append(ManifestRow(subject_id=subject_id, dataset=dataset_name, lesion_mask_path=matches[0]))

    return rows, excluded


def write_manifest(rows: list[ManifestRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_MANIFEST_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {"subject_id": row.subject_id, "dataset": row.dataset, "lesion_mask_path": str(row.lesion_mask_path)}
            )


def read_manifest(path: Path) -> list[ManifestRow]:
    if not path.is_file():
        raise FileNotFoundError(
            f"manifest not found: {path} - run `compute_sdc.py --mode manifest` before `--mode run`"
        )
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(_MANIFEST_FIELDS):
            raise ValueError(
                f"manifest {path} has unexpected columns {reader.fieldnames}, expected {list(_MANIFEST_FIELDS)}"
            )
        return [
            ManifestRow(subject_id=r["subject_id"], dataset=r["dataset"], lesion_mask_path=Path(r["lesion_mask_path"]))
            for r in reader
        ]


def select_chunk(rows: list[ManifestRow], task_id: int, task_count: int) -> list[ManifestRow]:
    """Subjects assigned to this task - a simple stride slice (task_id::task_count)
    so chunk sizes differ by at most one across tasks regardless of how many
    subjects there are, and every subject is covered by exactly one task for
    any (task_id, task_count) pair produced by the SLURM array / local pool
    launchers."""
    if task_count < 1:
        raise ValueError(f"task_count must be >= 1, got {task_count}")
    if not (0 <= task_id < task_count):
        raise ValueError(f"task_id must be in [0, {task_count}), got {task_id}")
    return rows[task_id::task_count]
