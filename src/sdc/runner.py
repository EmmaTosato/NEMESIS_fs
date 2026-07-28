"""Subprocess wrappers around bcb-lf-preprocess (Stage 1) and
bcb-lesion-features (Stage 2), plus the check gating one from the other.

Both tools operate on a whole directory of subjects, not a single subject -
there is no per-subject CLI flag (confirmed via `bcb-lf-preprocess --help` /
`bcb-lesion-features --help`, /data/etosato/tools/USAGE.md). Parallelism
across subjects therefore comes from calling these wrappers once per task,
each pointed at a staging/prep directory containing only that task's
subjects (see staging.py and _select_validated_prep below) - never from a
flag these tools don't have.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import nibabel as nib
from bcblib.tools.lesion_features._constants import EBRAINS_ATLAS_SPECS

from src.sdc.config import SDCConfig
from src.sdc.manifest import ManifestRow

_EXPECTED_SHAPE = (182, 218, 182)

# Imported from bcblib rather than hardcoded: this list's length was wrongly
# assumed to be 14 (see .claude/stato_progetto.md) when it is actually 15 in
# the bcblib version installed in the `nemesis` env - a hardcoded count here
# would silently go stale on a bcblib upgrade and fail every stage2_ebrains
# subject's check_stage2_outputs (28 expected vs 30 actual CSVs). _constants
# is a private bcblib module (leading underscore) but this integration
# already depends on bcblib's internal filename conventions elsewhere
# (build_lf_csv_path/build_lf_tsv_path's naming, mirrored in
# _check_stage2_mapstats below) - importing the source of truth directly is
# more robust than re-deriving a number that can drift.
_EBRAINS_ATLAS_COUNT = len(EBRAINS_ATLAS_SPECS)


def run_stage1(rows: list[ManifestRow], staging_dir: Path, prep_dir: Path, config: SDCConfig, *, dry_run: bool) -> None:
    """Runs bcb-lf-preprocess over staging_dir. Raises subprocess.CalledProcessError
    on a non-zero exit - not absorbed here, since bcblib aborts its whole
    batch on the first subject's error (lessons_learned.md #13), so a
    non-zero exit here does not necessarily mean every subject in the chunk
    failed. The caller (src/pipeline/compute_sdc.py::_run_task) still runs
    check_stage1_outputs() afterwards even on this exception, to salvage any
    subject whose output was actually written before the failure."""
    command = [
        "bcb-lf-preprocess",
        "--bids-dir", str(staging_dir),
        "--output-dir", str(prep_dir),
        "--bcbtoolkit", str(config.bcbtoolkit_path),
        "--ncores", str(config.cores_per_subject),
        "--skip-existing",
    ]
    if config.tracks_dir is not None:
        command += ["--tracks-dir", str(config.tracks_dir)]
    if dry_run:
        command += ["--dry-run"]

    logging.info("stage1: %d subject(s), command: %s", len(rows), " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    logging.info("stage1 stdout:\n%s", result.stdout)
    if result.returncode != 0:
        logging.error("stage1 stderr:\n%s", result.stderr)
        result.check_returncode()


def check_stage1_outputs(rows: list[ManifestRow], prep_dir: Path) -> tuple[list[ManifestRow], dict[str, str]]:
    """Verifies, per subject, that Stage 1 produced a loadable disconnectome
    map on the expected 182x218x182 MNI152NLin6Asym 1mm grid. Returns
    (passed, failed) - failed maps subject_id -> reason. A subject with a
    missing/corrupt/wrong-shape output is excluded here rather than passed
    into Stage 2, where it would otherwise crash the whole Stage 2 process
    for every subject in the same task (lessons_learned.md #4: the same bad
    input must not behave differently depending on which path reaches it -
    here, checking once before Stage 2 instead of leaving Stage 2 to
    discover it per-subject)."""
    passed: list[ManifestRow] = []
    failed: dict[str, str] = {}
    for row in rows:
        disconnectome_path = (
            prep_dir / row.subject_id / "lesion"
            / f"{row.subject_id}_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz"
        )
        if not disconnectome_path.is_file():
            failed[row.subject_id] = f"disconnectome output missing: {disconnectome_path}"
            logging.warning("stage1 check: %s - %s", row.subject_id, failed[row.subject_id])
            continue
        try:
            image = nib.load(disconnectome_path)
            shape = image.shape
        except (OSError, ValueError) as exc:
            failed[row.subject_id] = f"disconnectome not a loadable NIfTI: {exc}"
            logging.warning("stage1 check: %s - %s", row.subject_id, failed[row.subject_id], exc_info=True)
            continue
        if tuple(shape) != _EXPECTED_SHAPE:
            failed[row.subject_id] = f"disconnectome has shape {shape}, expected {_EXPECTED_SHAPE}"
            logging.warning("stage1 check: %s - %s", row.subject_id, failed[row.subject_id])
            continue
        passed.append(row)
    return passed, failed


def check_stage2_outputs(
    rows: list[ManifestRow], prep_dir: Path, config: SDCConfig
) -> tuple[list[ManifestRow], dict[str, str]]:
    """Verifies, per subject, that Stage 2 produced its expected output next
    to Stage 1's (same prep_dir/<subject_id>/lesion, see run_stage2's
    docstring): both mapstats TSVs, and one LF-{lesion,disconnectome} CSV
    pair per configured atlas. Matched via glob rather than an exact
    filename - the BIDS entities bcblib inserts between subject_id and each
    suffix aren't pinned down anywhere in this codebase (no access to
    bcblib's source in this environment), only the suffixes documented in
    docs/guides/compute_sdc.md from a prior real run are trusted.

    A subject whose Stage 2 process technically "succeeded" but produced
    missing/empty/incomplete output is excluded here rather than merged into
    the run's final output, same rationale as check_stage1_outputs - one
    checked gate between "the subprocess exited 0" and "this subject's
    output can be trusted downstream"."""
    expected_atlas_count = (_EBRAINS_ATLAS_COUNT if config.stage2_ebrains else 0) + len(config.stage2_presets)
    passed: list[ManifestRow] = []
    failed: dict[str, str] = {}
    for row in rows:
        lesion_dir = prep_dir / row.subject_id / "lesion"
        reason = _check_stage2_mapstats(lesion_dir, row.subject_id, "lesion")
        if reason is None:
            reason = _check_stage2_mapstats(lesion_dir, row.subject_id, "disconnectome")
        if reason is None and expected_atlas_count > 0:
            atlas_csvs = list(lesion_dir.glob(f"{row.subject_id}*_LF-*_atlas-*.csv"))
            expected_files = expected_atlas_count * 2  # one LF-lesion + one LF-disconnectome CSV per atlas
            if len(atlas_csvs) != expected_files:
                reason = (
                    f"expected {expected_files} atlas CSV(s) ({expected_atlas_count} atlas(es) x 2), "
                    f"found {len(atlas_csvs)} in {lesion_dir}"
                )
        if reason is not None:
            failed[row.subject_id] = reason
            logging.warning("stage2 check: %s - %s", row.subject_id, reason)
            continue
        passed.append(row)
    return passed, failed


def _check_stage2_mapstats(lesion_dir: Path, subject_id: str, desc: str) -> str | None:
    """Returns None if a non-empty, >=2-line mapstats TSV matching
    {subject_id}*_desc-{desc}_mapstats.tsv exists in lesion_dir, otherwise a
    reason string identifying what's wrong."""
    matches = list(lesion_dir.glob(f"{subject_id}*_desc-{desc}_mapstats.tsv"))
    if not matches:
        return f"{desc} mapstats TSV missing in {lesion_dir}"
    if len(matches) > 1:
        return f"{desc} mapstats TSV ambiguous - {len(matches)} files matched: {matches}"
    try:
        lines = [line for line in matches[0].read_text().splitlines() if line.strip()]
    except OSError as exc:
        return f"{desc} mapstats TSV not readable: {exc}"
    if len(lines) < 2:
        return f"{desc} mapstats TSV has {len(lines)} non-empty line(s), expected a header plus >=1 data row"
    return None


def stage_validated_prep(passed: list[ManifestRow], prep_dir: Path, validated_prep_dir: Path) -> None:
    """Symlinks each subject that passed check_stage1_outputs() from prep_dir
    into validated_prep_dir, so Stage 2 (which has no per-subject filter
    either) only ever sees subjects with a verified Stage 1 output."""
    if validated_prep_dir.exists() and any(validated_prep_dir.iterdir()):
        raise FileExistsError(f"validated_prep_dir is not empty, refusing to reuse it: {validated_prep_dir}")
    validated_prep_dir.mkdir(parents=True, exist_ok=True)
    for row in passed:
        (validated_prep_dir / row.subject_id).symlink_to((prep_dir / row.subject_id).resolve())


def run_stage2(validated_prep_dir: Path, config: SDCConfig, *, dry_run: bool) -> None:
    """Runs bcb-lesion-features over validated_prep_dir, writing its output
    (per-atlas overlap CSVs, mapstats TSVs) into that same directory rather
    than a separate features_dir - bcb-lesion-features only ever reads
    Stage 1's existing lesion/disconnectome NIfTIs and writes new files
    alongside them (bcblib.tools.lesion_features._pipeline._process_anat: no
    read-modify-write, no directory deletion), so this merges Stage 1 and
    Stage 2 output into one lesion/ folder per subject for free - each
    subject ends up on one physical grid, not split across prep/ and
    features/ trees (validated_prep_dir/<subject> is itself a symlink into
    prep_dir/<subject>, see stage_validated_prep, so writes here land in the
    same place Stage 1 already wrote to).

    bcb-lesion-features has no --dry-run flag (unlike bcb-lf-preprocess) -
    dry_run=True here means the command is logged and never executed,
    instead of relying on the tool itself to no-op."""
    command = [
        "bcb-lesion-features",
        "--prep-dir", str(validated_prep_dir),
        "--output-dir", str(validated_prep_dir),
        "--assume-yes",
        "--skip-existing",
    ]
    if config.stage2_ebrains:
        command.append("--ebrains")
    for preset in config.stage2_presets:
        command += ["--preset", preset]

    if dry_run:
        logging.info("stage2 [dry-run, not executed]: %s", " ".join(command))
        return

    logging.info("stage2: command: %s", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    logging.info("stage2 stdout:\n%s", result.stdout)
    if result.returncode != 0:
        logging.error("stage2 stderr:\n%s", result.stderr)
        result.check_returncode()
