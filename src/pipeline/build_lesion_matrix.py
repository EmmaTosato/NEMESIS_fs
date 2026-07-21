"""CLI entry point: build a lesion feature matrix from retrieved lesion masks.

Usage:
    python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json

Unlike retrieve_data.py, there is no per-subject error accumulation here:
build_lesion_matrix() (src/features/lesion.py) either succeeds for every
requested subject or raises - a subject-count mismatch or a missing
reference/atlas file stops the whole run before anything is written, since a
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
from src.features.lesion import (
    build_lesion_matrix,
    load_and_resample_atlas,
    load_reference_image,
    reconstruct_parcel_volume,
)
from src.utils.artifacts import save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

REPORTS_ROOT = Path("reports") / "build_lesion_matrix"
LOGS_ROOT = Path("logs") / "build_lesion_matrix"
REPORT_FILENAME_PREFIX = "build_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a lesion feature matrix (voxel-wise or parcellated) from retrieved lesion masks."
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
        X, metadata, non_constant_mask, parcel_ids = build_lesion_matrix(
            data_root=config.data_root,
            datasets=config.datasets,
            reference_template_path=config.reference_template_path,
            lesion_glob=config.lesion_glob,
            binarize_threshold=config.binarize_threshold,
            resample_interpolation=config.resample_interpolation,
            parcellate=config.parcellate,
            atlas_path=config.atlas_path,
            parcel_aggregation=config.parcel_aggregation,
        )
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    output_dir = _output_dir(config, now)
    extra_arrays = {"non_constant_mask": non_constant_mask}
    if parcel_ids is not None:
        extra_arrays["parcel_ids"] = parcel_ids

    try:
        save_matrix(
            output_dir,
            X,
            metadata,
            _build_readme_lines(config, X, metadata, parcel_ids, now),
            overwrite=config.overwrite,
            extra_arrays=extra_arrays,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("matrix written to %s (shape %s)", output_dir, X.shape)

    if config.parcellate and config.save_parcellated_volumes:
        try:
            _write_parcellated_volumes(config, output_dir, X, metadata, parcel_ids)
        except OSError as exc:
            # The matrix artifact above already landed successfully - a failure here
            # only means the QC-only volumes are incomplete, not that the run's real
            # output is bad. Still a non-zero exit so a SLURM job surfaces it.
            logging.error("matrix saved, but writing parcellated QC volumes failed: %s", exc, exc_info=True)
            return 1
        logging.info("parcellated QC volumes written to %s", output_dir / "parcellated_volumes")

    try:
        report_path = _write_report(config, X, metadata, parcel_ids, now)
        append_run_log_entry(
            config.output_root / "RUNS.md",
            config.run_name,
            now,
            "production",
            {"parcellate": config.parcellate, "binarize_threshold": config.binarize_threshold},
            output_dir,
            config.run_notes,
        )
    except OSError as exc:
        logging.error("cannot write report/run log: %s", exc, exc_info=True)
        return 1

    logging.info(
        "done - matrix written to %s, report written to %s, log written to %s", output_dir, report_path, log_path
    )
    return 0


def _output_dir(config: BuildMatrixConfig, now: datetime) -> Path:
    return config.output_root / f"{now.strftime('%d-%m')}_{config.run_name}"


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
        "reference_template_path": str(config.reference_template_path),
        "lesion_glob": config.lesion_glob,
        "binarize_threshold": config.binarize_threshold,
        "resample_interpolation": config.resample_interpolation,
        "parcellate": config.parcellate,
        "atlas_path": str(config.atlas_path) if config.atlas_path else None,
        "parcel_aggregation": config.parcel_aggregation,
        "save_parcellated_volumes": config.save_parcellated_volumes,
        "output_root": str(config.output_root),
        "run_name": config.run_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(
    config: BuildMatrixConfig, X: np.ndarray, metadata: pd.DataFrame, parcel_ids: np.ndarray | None
) -> list[str]:
    lines = ["## Config", "", "```json", _config_summary(config), "```", "", "## Summary", ""]
    lines.append(f"Matrix shape: {X.shape[0]} subjects x {X.shape[1]} features")
    if parcel_ids is not None:
        lines.append(f"Parcellated: true ({parcel_ids.shape[0]} atlas parcels survived the constant-feature drop)")
    else:
        lines.append("Parcellated: false (voxel-wise)")
    lines += ["", "| dataset | subjects |", "|---|---|"]
    for name, count in _dataset_counts(metadata).items():
        lines.append(f"| {name} | {count} |")
    return lines


def _build_readme_lines(
    config: BuildMatrixConfig, X: np.ndarray, metadata: pd.DataFrame, parcel_ids: np.ndarray | None, now: datetime
) -> list[str]:
    return [f"# {config.project} lesion matrix — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, X, metadata, parcel_ids
    )


def _build_report(
    config: BuildMatrixConfig, X: np.ndarray, metadata: pd.DataFrame, parcel_ids: np.ndarray | None, now: datetime
) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')}", ""] + _summary_lines(
        config, X, metadata, parcel_ids
    )
    return "\n".join(lines)


def _write_report(
    config: BuildMatrixConfig, X: np.ndarray, metadata: pd.DataFrame, parcel_ids: np.ndarray | None, now: datetime
) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, X, metadata, parcel_ids, now))
    return report_path


def _log_path(config: BuildMatrixConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


def _write_parcellated_volumes(
    config: BuildMatrixConfig, output_dir: Path, X: np.ndarray, metadata: pd.DataFrame, parcel_ids: np.ndarray
) -> None:
    """Write one QC NIfTI per subject with parcel values painted back onto the atlas grid.

    Not atomic (unlike save_matrix): a failure partway through leaves some,
    but not all, subjects' volumes on disk. Acceptable here because these are
    QC-only outputs alongside an already-successfully-saved matrix, not the
    run's real output.
    """
    reference_img = load_reference_image(config.reference_template_path)
    atlas_labels, _ = load_and_resample_atlas(config.atlas_path, reference_img)

    volumes_dir = output_dir / "parcellated_volumes"
    volumes_dir.mkdir(parents=True, exist_ok=True)
    for row_index, subject_id in enumerate(metadata["subject_id"]):
        volume = reconstruct_parcel_volume(X[row_index], atlas_labels, parcel_ids)
        image = nib.Nifti1Image(volume.astype(np.float32), reference_img.affine)
        nib.save(image, volumes_dir / f"{subject_id}.nii.gz")


if __name__ == "__main__":
    raise SystemExit(main())
