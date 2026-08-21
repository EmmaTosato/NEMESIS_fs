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
the run's final per-subject output directories (Stage 1 + Stage 2 combined,
see run_stage2's docstring) and run history. Unlike
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
import time
from datetime import datetime
from pathlib import Path

import nibabel as nib

from src.sdc.config import SDCConfig, load_sdc_config
from src.sdc.manifest import ManifestRow, build_manifest, read_manifest, select_chunk, write_manifest
from src.sdc.resample import resample_nonconforming_rows
from src.sdc.runner import check_stage1_outputs, check_stage2_outputs, run_stage1, run_stage2, stage_validated_prep
from src.sdc.staging import stage_subjects
from src.sdc.status import StageEvent, SubjectStatus, read_all_statuses, write_status
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
    resampled_dir = task_dir / "resampled"
    staging_dir = task_dir / "staging"
    prep_dir = task_dir / "prep"
    validated_dir = task_dir / "validated_prep"
    status_dir = output_dir / "_status"

    events: dict[str, list[StageEvent]] = {row.subject_id: [] for row in chunk}
    final: dict[str, tuple[str, str]] = {}

    try:
        reference_img = nib.load(config.mni152_reference_path)
        chunk, failed_resample, resample_timings = resample_nonconforming_rows(chunk, reference_img, resampled_dir)
    except OSError as exc:
        logging.error("task %d: loading resample reference failed structurally: %s", task_id, exc, exc_info=True)
        return 1
    for subject_id, reason in failed_resample.items():
        events[subject_id].append(StageEvent("resample", "failed", resample_timings[subject_id], reason))
        final[subject_id] = ("failed_resample", reason)
    for row in chunk:
        events[row.subject_id].append(
            StageEvent("resample", "ok", resample_timings[row.subject_id], "conforming or resampled")
        )
    if not chunk:
        logging.warning("task %d: no subject survived resampling, stage1 skipped", task_id)
        _finalize_statuses(status_dir, task_id, events, final)
        return 0

    try:
        stage_subjects(chunk, staging_dir)
    except (FileExistsError, OSError) as exc:
        logging.error("task %d: staging failed structurally: %s", task_id, exc, exc_info=True)
        return 1

    stage1_process_error: str | None = None
    start = time.perf_counter()
    try:
        run_stage1(chunk, staging_dir, prep_dir, config, dry_run=dry_run)
    except subprocess.CalledProcessError as exc:
        stage1_process_error = str(exc)
        logging.error("task %d: stage1 process failed, attempting per-subject salvage: %s", task_id, exc)
    except OSError as exc:
        # bcb-lf-preprocess not found/not executable (e.g. cluster module not
        # loaded) - the process never even started, so there is nothing to
        # salvage (unlike CalledProcessError above, where it ran and failed
        # partway through - check_stage1_outputs is never reached here).
        logging.error(
            "task %d: stage1 could not be launched (bcb-lf-preprocess not found/not executable?): %s",
            task_id, exc, exc_info=True,
        )
        _finalize_statuses(status_dir, task_id, events, final)
        return 1
    stage1_duration = time.perf_counter() - start
    stage1_outcome = "process_error" if stage1_process_error else "ok"
    for row in chunk:
        events[row.subject_id].append(
            StageEvent("stage1_process", stage1_outcome, stage1_duration, stage1_process_error or "stage1 subprocess completed")
        )

    if dry_run:
        for row in chunk:
            final[row.subject_id] = ("dry_run", "stage1 dry-run only")
        _finalize_statuses(status_dir, task_id, events, final)
        logging.info("task %d: dry-run complete for %d subject(s), stage2 not invoked", task_id, len(chunk))
        return 0

    start = time.perf_counter()
    passed, failed_check = check_stage1_outputs(chunk, prep_dir)
    check1_duration = time.perf_counter() - start
    for subject_id, reason in failed_check.items():
        events[subject_id].append(StageEvent("stage1_check", "failed", check1_duration, reason))
        status = "failed_stage1_process" if stage1_process_error else "failed_stage1_check"
        detail = f"{stage1_process_error} | {reason}" if stage1_process_error else reason
        final[subject_id] = (status, detail)
    for row in passed:
        events[row.subject_id].append(StageEvent("stage1_check", "ok", check1_duration, "disconnectome output verified"))

    if stage1_process_error and not passed:
        logging.error("task %d: stage1 process failed and no subject could be salvaged", task_id)
        _finalize_statuses(status_dir, task_id, events, final)
        return 1
    if stage1_process_error:
        logging.warning(
            "task %d: stage1 process failed but %d/%d subject(s) salvaged via output check",
            task_id, len(passed), len(chunk),
        )
    if not passed:
        logging.warning("task %d: no subject passed the stage1 check, stage2 skipped", task_id)
        _finalize_statuses(status_dir, task_id, events, final)
        return 0

    try:
        stage_validated_prep(passed, prep_dir, validated_dir)
    except (FileExistsError, OSError) as exc:
        logging.error("task %d: stage2 staging failed structurally: %s", task_id, exc, exc_info=True)
        _finalize_statuses(status_dir, task_id, events, final)
        return 1

    stage2_process_error: str | None = None
    start = time.perf_counter()
    try:
        run_stage2(validated_dir, config, dry_run=False)
    except subprocess.CalledProcessError as exc:
        stage2_process_error = str(exc)
        logging.error("task %d: stage2 process failed, attempting per-subject salvage: %s", task_id, exc)
    except OSError as exc:
        # bcb-lesion-features not found/not executable - same reasoning as
        # run_stage1's OSError handler above: nothing to salvage, the
        # process never started.
        logging.error(
            "task %d: stage2 could not be launched (bcb-lesion-features not found/not executable?): %s",
            task_id, exc, exc_info=True,
        )
        _finalize_statuses(status_dir, task_id, events, final)
        return 1
    stage2_duration = time.perf_counter() - start
    stage2_outcome = "process_error" if stage2_process_error else "ok"
    for row in passed:
        events[row.subject_id].append(
            StageEvent("stage2_process", stage2_outcome, stage2_duration, stage2_process_error or "stage2 subprocess completed")
        )

    start = time.perf_counter()
    ok_rows, failed_stage2_check = check_stage2_outputs(passed, prep_dir, config)
    check2_duration = time.perf_counter() - start
    for subject_id, reason in failed_stage2_check.items():
        events[subject_id].append(StageEvent("stage2_check", "failed", check2_duration, reason))
        status = "failed_stage2_process" if stage2_process_error else "failed_stage2_check"
        detail = f"{stage2_process_error} | {reason}" if stage2_process_error else reason
        final[subject_id] = (status, detail)
    for row in ok_rows:
        events[row.subject_id].append(StageEvent("stage2_check", "ok", check2_duration, "stage2 output verified"))
        final[row.subject_id] = ("ok", "stage1+stage2 completed")

    if stage2_process_error and not ok_rows:
        logging.error("task %d: stage2 process failed and no subject could be salvaged", task_id)
        _finalize_statuses(status_dir, task_id, events, final)
        return 1
    if stage2_process_error:
        logging.warning(
            "task %d: stage2 process failed but %d/%d subject(s) salvaged via output check",
            task_id, len(ok_rows), len(passed),
        )

    _finalize_statuses(status_dir, task_id, events, final)
    logging.info("task %d: %d/%d subject(s) completed successfully", task_id, len(ok_rows), len(chunk))
    return 0


def _finalize_statuses(
    status_dir: Path, task_id: int, events: dict[str, list[StageEvent]], final: dict[str, tuple[str, str]]
) -> None:
    """Writes one SubjectStatus per subject that reached a terminal outcome
    in this task, each carrying the full stage-by-stage trace accumulated so
    far. Subjects still in `events` but missing from `final` (e.g. stuck
    mid-pipeline after a structural OSError) are left without a status file,
    same as before this refactor - a structural error requires human
    intervention regardless of a per-subject write here."""
    for subject_id, (status, detail) in final.items():
        write_status(status_dir, SubjectStatus(subject_id, task_id, status, detail, stages=tuple(events[subject_id])))


def _run_aggregate(config: SDCConfig, output_dir: Path, now: datetime) -> int:
    try:
        statuses, failed_status_files = read_all_statuses(output_dir / "_status")
    except FileNotFoundError as exc:
        logging.error(str(exc))
        return 1
    for stem, reason in sorted(failed_status_files.items()):
        logging.warning("aggregate: skipping unreadable status file %s.json: %s", stem, reason)

    counts: dict[str, int] = {}
    for status in statuses:
        counts[status.status] = counts.get(status.status, 0) + 1
        if status.status != "ok":
            continue
        task_dir = output_dir / "_work" / f"task_{status.task_id}"
        try:
            # task_dir/prep/<subject>/lesion already holds both Stage 1 (NIfTI)
            # and Stage 2 (CSV/TSV) output together - see run_stage2's
            # docstring. Linking straight to the "lesion" subfolder (bcblib's
            # own LF_SUBDIR constant - not a real BIDS datatype, just this
            # tool's naming) instead of the subject folder itself flattens the
            # final output to output_dir/<subject>/* directly. Assumes no
            # session-level nesting (bcblib inserts ses-<id>/ between sub-<id>
            # and lesion/ otherwise) - true here since staging.py never
            # creates ses-* folders.
            _link_subject(task_dir / "prep" / status.subject_id / "lesion", output_dir / status.subject_id)
        except OSError as exc:
            logging.error("aggregate: cannot merge %s: %s", status.subject_id, exc, exc_info=True)
            return 1

    try:
        (output_dir / "manifest.json").write_text(
            json.dumps(
                {"counts": counts, "total": len(statuses), "unreadable_status_files": failed_status_files}, indent=2
            )
        )
        (output_dir / "config.md").write_text(
            _readme_text(config, counts, len(statuses), now, statuses, failed_status_files)
        )
        # No single external input_path here (unlike dim_reduction.py/clustering.py's matrix
        # artifacts) - aggregate mode merges per-task staging output into output_dir itself, so
        # the staging root is the closest honest answer to "what was this row built from".
        append_run_log_entry(
            config.output_root,
            config.session_name,
            now,
            "production",
            counts,
            output_dir,
            config.run_notes,
            output_dir / "_work",
        )
    except OSError as exc:
        logging.error("aggregate: cannot write summary/run log: %s", exc, exc_info=True)
        return 1

    logging.info(
        "aggregate: done - %s (%d unreadable status file(s)) -> merged under %s",
        counts,
        len(failed_status_files),
        output_dir,
    )
    return 0


def _link_subject(source: Path, destination: Path) -> None:
    """Symlink destination -> source, re-pointing it if it already exists.

    A prior --mode aggregate run may have linked this subject to an older
    task_dir (e.g. before a retry re-ran and produced a newer task_id for
    the same subject) - destination.exists() alone can't tell "already
    correctly linked" from "linked to something stale", since both make it
    True. Compares resolved targets instead: a no-op if destination already
    points at source (the common case, avoids needless relinking every
    aggregate run), otherwise unlinks and relinks to the current source. A
    destination that isn't a symlink at all (should never happen - this
    function is the only writer of output_dir/<subject>) is left for
    symlink_to's own FileExistsError to surface loudly, not silently
    skipped or overwritten.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    resolved_source = source.resolve()
    if destination.is_symlink():
        if destination.resolve() == resolved_source:
            return
        destination.unlink()
    destination.symlink_to(resolved_source)


def _readme_text(
    config: SDCConfig,
    counts: dict[str, int],
    total: int,
    now: datetime,
    statuses: list[SubjectStatus],
    failed_status_files: dict[str, str],
) -> str:
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
    lines += ["", "## Average stage duration (seconds)", "", "| stage | mean duration (s) | events |", "|---|---|---|"]
    for stage, mean_duration, event_count in _mean_stage_durations(statuses):
        lines.append(f"| {stage} | {mean_duration:.1f} | {event_count} |")
    if failed_status_files:
        lines += ["", "## Unreadable status files (excluded from the counts above)", "", "| file | reason |", "|---|---|"]
        for stem, reason in sorted(failed_status_files.items()):
            lines.append(f"| {stem}.json | {reason} |")
    return "\n".join(lines) + "\n"


def _mean_stage_durations(statuses: list[SubjectStatus]) -> list[tuple[str, float, int]]:
    """Averages StageEvent.duration_s per stage across every subject status
    read at aggregate time. stage1_process/stage2_process durations are
    chunk-wide (see StageEvent's docstring) and therefore repeated once per
    subject in that chunk - this average is over those per-subject-repeated
    values, not over distinct subprocess invocations, so it answers "what
    duration did a subject typically experience for this stage" rather than
    "how long did one subprocess call take"."""
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for status in statuses:
        for event in status.stages:
            totals[event.stage] = totals.get(event.stage, 0.0) + event.duration_s
            counts[event.stage] = counts.get(event.stage, 0) + 1
    return sorted((stage, totals[stage] / counts[stage], counts[stage]) for stage in totals)


def _log_path(config: SDCConfig, mode: str, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project / config.session_name
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{mode}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
