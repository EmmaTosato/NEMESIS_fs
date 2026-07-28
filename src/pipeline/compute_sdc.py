"""CLI entry point: run BCBToolKit/BCBlib Stage 1 (bcb-lf-preprocess) and
Stage 2 (bcb-lesion-features) over the lesion masks retrieved for a project.

Usage (see docs/guides/compute_sdc.md for the full walkthrough):
    python -m src.pipeline.compute_sdc --config <path> --mode manifest
    python -m src.pipeline.compute_sdc --config <path> --mode run --task-id I --task-count N [--dry-run]
    python -m src.pipeline.compute_sdc --config <path> --mode aggregate

Three modes instead of one, because a production run spans more than one
process invocation by design: `manifest` discovers subjects once and freezes
the list every `run` task slices a chunk from (src/sdc/manifest.py); `run` is
the unit of parallelism (one per SLURM array task, or one per local worker);
`aggregate` merges every task's per-subject outcome (src/sdc/status.py) into
the run's final prep/features directories and run history. Unlike
build_lesion_matrix.py's single all-or-nothing run, per-subject failures here
never stop other subjects (see check_stage1_outputs docstring) - the run's
own exit code only reflects structural failures (bad config, a Stage 1/2
process crash), not "some subjects failed the disconnectome check".

output_dir is `<output_root>/<session_name>` - not date-stamped like the other
pipelines' `<dd-mm>_<session_name>` convention (see build_lesion_matrix.py),
because manifest/run/aggregate for the same run can span multiple days
(SLURM queue wait) and must all resolve to the same directory from config
alone.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from src.sdc.config import SDCConfig, load_sdc_config
from src.sdc.manifest import ManifestRow, build_manifest, read_manifest, select_chunk, write_manifest
from src.sdc.runner import check_stage1_outputs, run_stage1, run_stage2, stage_validated_prep
from src.sdc.staging import stage_subjects
from src.sdc.status import SubjectStatus, read_all_statuses, write_status
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

LOGS_ROOT = Path("logs") / "compute_sdc"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run BCBToolKit Stage 1+2 over a project's lesion masks.")
    parser.add_argument("--config", required=True, help="Path to a compute_sdc.json file")
    parser.add_argument("--mode", required=True, choices=("manifest", "run", "aggregate"))
    parser.add_argument("--task-id", type=int, help="0-based task index, required for --mode run")
    parser.add_argument("--task-count", type=int, help="Total number of tasks, required for --mode run")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="--mode run only: pass --dry-run to bcb-lf-preprocess and skip invoking bcb-lesion-features entirely",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_sdc_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    output_dir = config.output_root / config.session_name
    now = datetime.now()
    try:
        log_path = _log_path(config, args.mode, now)
        attach_file_handler(log_path)
    except OSError as exc:
        logging.error("cannot set up log file: %s", exc, exc_info=True)
        return 1

    if args.mode == "manifest":
        return _run_manifest(config, output_dir)
    if args.mode == "run":
        if args.task_id is None or args.task_count is None:
            logging.error("--mode run requires --task-id and --task-count")
            return 1
        return _run_task(config, output_dir, args.task_id, args.task_count, dry_run=args.dry_run)
    return _run_aggregate(config, output_dir, now)


def _run_manifest(config: SDCConfig, output_dir: Path) -> int:
    manifest_path = output_dir / "manifest.csv"
    if manifest_path.is_file() and not config.overwrite:
        logging.error(
            "manifest already exists at %s and overwrite=false - set overwrite=true in the config to rebuild it",
            manifest_path,
        )
        return 1

    try:
        rows, excluded = build_manifest(config)
    except FileNotFoundError as exc:
        logging.error(str(exc))
        return 1
    if not rows:
        logging.error("manifest: 0 subjects discovered for datasets=%s group_filter=%s", config.datasets, config.group_filter)
        return 1

    try:
        write_manifest(rows, manifest_path)
        (output_dir / "manifest_excluded.json").write_text(json.dumps(excluded, indent=2))
    except OSError as exc:
        logging.error("cannot write manifest: %s", exc, exc_info=True)
        return 1

    logging.info("manifest: %d subject(s) included, %d excluded -> %s", len(rows), len(excluded), manifest_path)
    return 0


def _run_task(config: SDCConfig, output_dir: Path, task_id: int, task_count: int, *, dry_run: bool) -> int:
    try:
        rows = read_manifest(output_dir / "manifest.csv")
        chunk = select_chunk(rows, task_id, task_count)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1
    if not chunk:
        logging.info("task %d/%d: no subjects assigned, nothing to do", task_id, task_count)
        return 0

    task_dir = output_dir / "_work" / f"task_{task_id}"
    staging_dir = task_dir / "staging"
    prep_dir = task_dir / "prep"
    validated_dir = task_dir / "validated_prep"
    features_dir = task_dir / "features"
    status_dir = output_dir / "_status"

    try:
        stage_subjects(chunk, staging_dir)
        run_stage1(chunk, staging_dir, prep_dir, config, dry_run=dry_run)
    except (FileExistsError, OSError) as exc:
        logging.error("task %d: staging/stage1 failed structurally: %s", task_id, exc, exc_info=True)
        return 1
    except subprocess.CalledProcessError as exc:
        logging.error("task %d: stage1 process failed: %s", task_id, exc, exc_info=True)
        for row in chunk:
            write_status(status_dir, SubjectStatus(row.subject_id, task_id, "failed_stage1_process", str(exc)))
        return 1

    if dry_run:
        for row in chunk:
            write_status(status_dir, SubjectStatus(row.subject_id, task_id, "dry_run", "stage1 dry-run only"))
        logging.info("task %d: dry-run complete for %d subject(s), stage2 not invoked", task_id, len(chunk))
        return 0

    passed, failed_check = check_stage1_outputs(chunk, prep_dir)
    for subject_id, reason in failed_check.items():
        write_status(status_dir, SubjectStatus(subject_id, task_id, "failed_stage1_check", reason))
    if not passed:
        logging.warning("task %d: no subject passed the stage1 check, stage2 skipped", task_id)
        return 0

    try:
        stage_validated_prep(passed, prep_dir, validated_dir)
        run_stage2(validated_dir, features_dir, config, dry_run=False)
    except (FileExistsError, OSError) as exc:
        logging.error("task %d: stage2 staging failed structurally: %s", task_id, exc, exc_info=True)
        return 1
    except subprocess.CalledProcessError as exc:
        logging.error("task %d: stage2 process failed: %s", task_id, exc, exc_info=True)
        for row in passed:
            write_status(status_dir, SubjectStatus(row.subject_id, task_id, "failed_stage2_process", str(exc)))
        return 1

    for row in passed:
        write_status(status_dir, SubjectStatus(row.subject_id, task_id, "ok", "stage1+stage2 completed"))
    logging.info("task %d: %d/%d subject(s) completed successfully", task_id, len(passed), len(chunk))
    return 0


def _run_aggregate(config: SDCConfig, output_dir: Path, now: datetime) -> int:
    try:
        statuses = read_all_statuses(output_dir / "_status")
    except FileNotFoundError as exc:
        logging.error(str(exc))
        return 1

    prep_dir = output_dir / "prep"
    features_dir = output_dir / "features"
    counts: dict[str, int] = {}
    for status in statuses:
        counts[status.status] = counts.get(status.status, 0) + 1
        if status.status != "ok":
            continue
        task_dir = output_dir / "_work" / f"task_{status.task_id}"
        try:
            _link_subject(task_dir / "prep" / status.subject_id, prep_dir / status.subject_id)
            _link_subject(task_dir / "features" / status.subject_id, features_dir / status.subject_id)
        except OSError as exc:
            logging.error("aggregate: cannot merge %s: %s", status.subject_id, exc, exc_info=True)
            return 1

    try:
        (output_dir / "manifest.json").write_text(json.dumps({"counts": counts, "total": len(statuses)}, indent=2))
        (output_dir / "config.md").write_text(_readme_text(config, counts, len(statuses), now))
        append_run_log_entry(
            config.output_root, config.session_name, now, "production", counts, output_dir, config.run_notes
        )
    except OSError as exc:
        logging.error("aggregate: cannot write summary/run log: %s", exc, exc_info=True)
        return 1

    logging.info("aggregate: done - %s -> prep/features merged under %s", counts, output_dir)
    return 0


def _link_subject(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    destination.symlink_to(source.resolve())


def _readme_text(config: SDCConfig, counts: dict[str, int], total: int, now: datetime) -> str:
    lines = [
        f"# {config.project} SDC — {config.session_name} — {now.strftime('%d-%m-%y %H:%M')}",
        "",
        f"Total subjects processed: {total}",
        "",
        "| status | count |",
        "|---|---|",
    ]
    for status, count in sorted(counts.items()):
        lines.append(f"| {status} | {count} |")
    return "\n".join(lines) + "\n"


def _log_path(config: SDCConfig, mode: str, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project / config.session_name
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{mode}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
