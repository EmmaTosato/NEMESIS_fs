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

from src.sdc.config import SDCConfig
from src.sdc.manifest import ManifestRow

_EXPECTED_SHAPE = (182, 218, 182)


def run_stage1(rows: list[ManifestRow], staging_dir: Path, prep_dir: Path, config: SDCConfig, *, dry_run: bool) -> None:
    """Runs bcb-lf-preprocess over staging_dir. Raises subprocess.CalledProcessError
    on a non-zero exit - a Stage 1 process failure is structural (bad
    bcbtoolkit_path, out-of-space tmpdir, ...), not a per-subject outcome, so
    it is not caught/absorbed here. Per-subject outcomes are decided by
    check_stage1_outputs() afterwards, once Stage 1 has actually run."""
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


def stage_validated_prep(passed: list[ManifestRow], prep_dir: Path, validated_prep_dir: Path) -> None:
    """Symlinks each subject that passed check_stage1_outputs() from prep_dir
    into validated_prep_dir, so Stage 2 (which has no per-subject filter
    either) only ever sees subjects with a verified Stage 1 output."""
    if validated_prep_dir.exists() and any(validated_prep_dir.iterdir()):
        raise FileExistsError(f"validated_prep_dir is not empty, refusing to reuse it: {validated_prep_dir}")
    validated_prep_dir.mkdir(parents=True, exist_ok=True)
    for row in passed:
        (validated_prep_dir / row.subject_id).symlink_to((prep_dir / row.subject_id).resolve())


def run_stage2(validated_prep_dir: Path, features_dir: Path, config: SDCConfig, *, dry_run: bool) -> None:
    """Runs bcb-lesion-features over validated_prep_dir. bcb-lesion-features
    has no --dry-run flag (unlike bcb-lf-preprocess) - dry_run=True here
    means the command is logged and never executed, instead of relying on
    the tool itself to no-op."""
    command = [
        "bcb-lesion-features",
        "--prep-dir", str(validated_prep_dir),
        "--output-dir", str(features_dir),
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
