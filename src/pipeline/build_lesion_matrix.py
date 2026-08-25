"""CLI entry point: build a lesion feature matrix from retrieved lesion masks.

Usage:
    python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json

Unlike retrieve_data.py, there is no per-subject error accumulation here:
build_lesion_matrix() (src/features/lesion.py) either succeeds for every
requested subject or raises - a subject-count mismatch or a missing
reference file stops the whole run before anything is written, since a
feature matrix with a silently-missing row would corrupt every downstream
analysis reading it.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from src.analysis.build_config import BuildMatrixConfig, load_build_matrix_config
from src.features.lesion import build_lesion_matrix
from src.utils.artifacts import save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

REPORTS_ROOT = Path("summaries") / "build_lesion_matrix"
LOGS_ROOT = Path("logs") / "build_lesion_matrix"
REPORT_FILENAME_PREFIX = "build_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a voxel-wise lesion feature matrix from retrieved lesion masks."
    )
    parser.add_argument("--config", required=True, help="Path to a build_lesion_matrix.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_build_matrix_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    try:
        log_path = _log_path(config, now)
        attach_file_handler(log_path)
    except OSError as exc:
        # No file handler yet at this point - this still reaches the console
        # StreamHandler from basicConfig() above.
        logging.error("cannot set up log file: %s", exc, exc_info=True)
        return 1

    try:
        X, metadata, non_constant_mask, excluded_by_group = build_lesion_matrix(
            data_root=config.data_root,
            datasets=config.datasets,
            reference_template_path=config.reference_template_path,
            lesion_glob=config.lesion_glob,
            binarize_threshold=config.binarize_threshold,
            resample_interpolation=config.resample_interpolation,
            group_filter=config.group_filter,
        )
    except (FileNotFoundError, ValueError, nib.filebasedimages.ImageFileError) as exc:
        # ImageFileError (HIGH #20): a truncated/corrupt .nii.gz raises this from nib.load,
        # for either the reference/atlas image or any subject's own lesion mask - neither
        # FileNotFoundError (the file exists) nor ValueError (nibabel's own exception, not
        # ours).
        logging.error(str(exc))
        return 1

    if excluded_by_group:
        logging.info(
            "%d subject(s) excluded by group_filter=%s: %s",
            len(excluded_by_group),
            config.group_filter,
            excluded_by_group,
        )

    output_dir = _output_dir(config, now)
    extra_arrays = {"non_constant_mask": non_constant_mask}

    try:
        save_matrix(
            output_dir,
            X,
            metadata,
            _build_readme_lines(config, X, metadata, excluded_by_group, now),
            overwrite=config.overwrite,
            extra_arrays=extra_arrays,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("matrix written to %s (shape %s)", output_dir, X.shape)

    try:
        report_path = _write_report(config, X, metadata, excluded_by_group, now)
        append_run_log_entry(
            config.output_root,
            config.session_name,
            now,
            "production",
            {"binarize_threshold": config.binarize_threshold},
            output_dir,
            config.run_notes,
            config.data_root,
        )
    except OSError as exc:
        logging.error("cannot write report/run log: %s", exc, exc_info=True)
        return 1

    logging.info(
        "done - matrix written to %s, report written to %s, log written to %s", output_dir, report_path, log_path
    )
    return 0


def _output_dir(config: BuildMatrixConfig, now: datetime) -> Path:
    return config.output_root / f"{now.strftime('%d-%m')}_{config.session_name}"


def _dataset_counts(metadata: pd.DataFrame) -> dict[str, int]:
    return {name: int(count) for name, count in metadata["dataset"].value_counts().sort_index().items()}


def _config_summary(config: BuildMatrixConfig) -> str:
    """JSON dump of the fields actually used - derived from the parsed
    BuildMatrixConfig (not a re-read of the file) so it can never drift from
    what the run actually used."""
    payload = {
        "project": config.project,
        "data_root": str(config.data_root),
        "datasets": config.datasets,
        "group_filter": config.group_filter,
        "reference_template_path": str(config.reference_template_path),
        "lesion_glob": config.lesion_glob,
        "binarize_threshold": config.binarize_threshold,
        "resample_interpolation": config.resample_interpolation,
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _params_used(config: BuildMatrixConfig) -> dict:
    """Same params dict passed to append_run_log_entry (main()) - the fields that actually
    control matrix construction. AUDIT_FINDINGS.md #49: exposed here too as a single
    "Params used: {...}" line (_summary_lines below), the same line-per-run convention
    dim_reduction.py/clustering.py already standardize on (and embedding_app.py's
    run_params already parses for those two pipelines) - this pipeline had only the
    generic full-config JSON dump, never that single-line form."""
    return {"binarize_threshold": config.binarize_threshold}


def _summary_lines(
    config: BuildMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
) -> list[str]:
    lines = ["## Config", "", "```json", _config_summary(config), "```", "", "## Summary", ""]
    lines.append(f"Matrix shape: {X.shape[0]} subjects x {X.shape[1]} features")
    lines.append(f"Params used: {json.dumps(_params_used(config))}")
    lines += ["", "| dataset | subjects |", "|---|---|"]
    for name, count in _dataset_counts(metadata).items():
        lines.append(f"| {name} | {count} |")
    # AUDIT_FINDINGS.md #48: excluded_by_group used to be logged only (logs/ isn't a
    # permanent artifact the way config.md is) - now persisted here too, so "why does this
    # matrix have fewer subjects than expected" is answerable from config.md alone, months
    # later, without the run's original log file.
    lines += ["", "## Excluded by group_filter", ""]
    if excluded_by_group:
        lines.append(f"{len(excluded_by_group)} subject(s) excluded (group_filter={config.group_filter}):")
        lines += [f"- {subject_id}" for subject_id in excluded_by_group]
    else:
        lines.append("None.")
    return lines


def _build_readme_lines(
    config: BuildMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    now: datetime,
) -> list[str]:
    return [f"# {config.project} lesion matrix — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, X, metadata, excluded_by_group
    )


def _build_report(
    config: BuildMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    now: datetime,
) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')}", ""] + _summary_lines(
        config, X, metadata, excluded_by_group
    )
    return "\n".join(lines)


def _write_report(
    config: BuildMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    now: datetime,
) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text(_build_report(config, X, metadata, excluded_by_group, now))
    return report_path


def _log_path(config: BuildMatrixConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
