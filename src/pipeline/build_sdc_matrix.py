"""CLI entry point: build an SDC feature matrix from retrieved SDC output.

Usage:
    python -m src.pipeline.build_sdc_matrix --config config/pipelines/build_sdc_matrix.json

Two representations, picked by config.representation (see
src.analysis.build_config.load_build_sdc_matrix_config / src/features/sdc.py):
"parcellated" (build_sdc_matrix, the original one, per-atlas region CSVs) or
"voxelwise" (build_sdc_voxelwise_matrix, added 03/09, the disconnectome-map
.nii.gz directly). Same shape as build_lesion_matrix.py either way:
either builder succeeds for the admitted subjects or raises - no per-subject
error accumulation beyond the two explicit exclusion lists both builders
return (excluded_no_lesion_mask, sdc_not_yet_computed), persisted to
config.md alongside the group_filter exclusion (see docs/dev/sdc_matrix.md).
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

from src.analysis.build_config import SdcMatrixConfig, load_build_sdc_matrix_config
from src.features.sdc import build_sdc_matrix, build_sdc_voxelwise_matrix
from src.utils.artifacts import save_matrix
from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.run_log import append_run_log_entry

REPORTS_ROOT = Path("summaries") / "build_sdc_matrix"
LOGS_ROOT = Path("logs") / "build_sdc_matrix"
REPORT_FILENAME_PREFIX = "build_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an SDC feature matrix (parcellated or voxelwise) from retrieved SDC output."
    )
    parser.add_argument("--config", required=True, help="Path to a build_sdc_matrix.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_build_sdc_matrix_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    try:
        try:
            log_path = _log_path(config, now)
            attach_file_handler(log_path)
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        try:
            if config.representation == "parcellated":
                X, metadata, column_labels, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed = (
                    build_sdc_matrix(
                        data_root=config.data_root,
                        datasets=config.datasets,
                        object_=config.object,
                        atlas=config.atlas,
                        value_column=config.value_column,
                        reference_labels_path=config.reference_labels_path,
                        group_filter=config.group_filter,
                    )
                )
            else:
                X, metadata, column_labels, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed = (
                    build_sdc_voxelwise_matrix(
                        data_root=config.data_root,
                        datasets=config.datasets,
                        object_=config.object,
                        reference_template_path=config.reference_template_path,
                        resample_interpolation=config.resample_interpolation,
                        group_filter=config.group_filter,
                    )
                )
        except (FileNotFoundError, ValueError, nib.filebasedimages.ImageFileError) as exc:
            # ImageFileError (voxelwise only): a truncated/corrupt .nii.gz raises this from
            # nib.load, for either the reference template or a subject's own disconnectome-map -
            # neither FileNotFoundError (the file exists) nor ValueError (nibabel's own
            # exception, not ours) - same reasoning as build_lesion_matrix.py.
            logging.error(str(exc))
            return 1

        if excluded_by_group:
            logging.info(
                "%d subject(s) excluded by group_filter=%s: %s",
                len(excluded_by_group), config.group_filter, excluded_by_group,
            )
        if excluded_no_lesion_mask:
            logging.info(
                "%d subject(s) excluded (SDC output present but no lesion mask): %s",
                len(excluded_no_lesion_mask), excluded_no_lesion_mask,
            )
        if sdc_not_yet_computed:
            logging.info(
                "%d subject(s) have a lesion mask but no SDC output yet: %s",
                len(sdc_not_yet_computed), sdc_not_yet_computed,
            )

        output_dir = _output_dir(config, now)
        # "region_names" (str labels) for parcellated, "non_constant_mask" (bool drop-mask,
        # same convention as build_lesion_matrix.py) for voxelwise - there is no drop mask in
        # the parcellated case (no column is ever dropped, see src/features/sdc.py).
        extra_arrays = (
            {"region_names": column_labels.astype(str)}
            if config.representation == "parcellated"
            else {"non_constant_mask": column_labels}
        )

        try:
            save_matrix(
                output_dir,
                X,
                metadata,
                _build_readme_lines(config, X, metadata, excluded_by_group, excluded_no_lesion_mask,
                                     sdc_not_yet_computed, now),
                overwrite=config.overwrite,
                extra_arrays=extra_arrays,
            )
        except (FileExistsError, ValueError, OSError) as exc:
            logging.error(str(exc))
            return 1
        logging.info("matrix written to %s (shape %s)", output_dir, X.shape)

        try:
            report_path = _write_report(config, X, metadata, excluded_by_group, excluded_no_lesion_mask,
                                         sdc_not_yet_computed, now)
            append_run_log_entry(
                config.output_root,
                config.session_name,
                now,
                "production",
                _params_used(config),
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
    finally:
        log_duration(now)


def _output_dir(config: SdcMatrixConfig, now: datetime) -> Path:
    return config.output_root / f"{now.strftime('%d-%m')}_{config.session_name}"


def _dataset_counts(metadata: pd.DataFrame) -> dict[str, int]:
    return {name: int(count) for name, count in metadata["dataset"].value_counts().sort_index().items()}


def _column_kind(config: SdcMatrixConfig) -> str:
    return "regions" if config.representation == "parcellated" else "voxels"


def _config_summary(config: SdcMatrixConfig) -> str:
    payload = {
        "project": config.project,
        "data_root": str(config.data_root),
        "datasets": config.datasets,
        "group_filter": config.group_filter,
        "object": config.object,
        "representation": config.representation,
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    # Only the fields relevant to the representation actually used - the other mode's
    # fields are None on this config and would otherwise show up as the misleading
    # string "None" rather than being absent.
    if config.representation == "parcellated":
        payload["atlas"] = config.atlas
        payload["value_column"] = config.value_column
        payload["reference_labels_path"] = str(config.reference_labels_path)
    else:
        payload["reference_template_path"] = str(config.reference_template_path)
        payload["resample_interpolation"] = config.resample_interpolation
    return json.dumps(payload, indent=2)


def _params_used(config: SdcMatrixConfig) -> dict:
    if config.representation == "parcellated":
        return {"object": config.object, "atlas": config.atlas, "value_column": config.value_column}
    return {"object": config.object, "representation": config.representation}


def _summary_lines(
    config: SdcMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    excluded_no_lesion_mask: list[str],
    sdc_not_yet_computed: list[str],
) -> list[str]:
    lines = ["## Config", "", "```json", _config_summary(config), "```", "", "## Summary", ""]
    lines.append(f"Matrix shape: {X.shape[0]} subjects x {X.shape[1]} {_column_kind(config)}")
    lines.append(f"Params used: {json.dumps(_params_used(config))}")
    lines += ["", "| dataset | subjects |", "|---|---|"]
    for name, count in _dataset_counts(metadata).items():
        lines.append(f"| {name} | {count} |")

    lines += ["", "## Excluded by group_filter", ""]
    if excluded_by_group:
        lines.append(f"{len(excluded_by_group)} subject(s) excluded (group_filter={config.group_filter}):")
        lines += [f"- {subject_id}" for subject_id in excluded_by_group]
    else:
        lines.append("None.")

    lines += ["", "## Excluded (SDC output present but no lesion mask)", ""]
    if excluded_no_lesion_mask:
        lines.append(f"{len(excluded_no_lesion_mask)} subject(s):")
        lines += [f"- {subject_id}" for subject_id in excluded_no_lesion_mask]
    else:
        lines.append("None.")

    lines += ["", "## Have a lesion mask but no SDC output yet", ""]
    if sdc_not_yet_computed:
        lines.append(f"{len(sdc_not_yet_computed)} subject(s):")
        lines += [f"- {subject_id}" for subject_id in sdc_not_yet_computed]
    else:
        lines.append("None.")

    return lines


def _build_readme_lines(
    config: SdcMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    excluded_no_lesion_mask: list[str],
    sdc_not_yet_computed: list[str],
    now: datetime,
) -> list[str]:
    return [f"# {config.project} sdc matrix — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, X, metadata, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed
    )


def _build_report(
    config: SdcMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    excluded_no_lesion_mask: list[str],
    sdc_not_yet_computed: list[str],
    now: datetime,
) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')}", ""] + _summary_lines(
        config, X, metadata, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed
    )
    return "\n".join(lines)


def _write_report(
    config: SdcMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    excluded_no_lesion_mask: list[str],
    sdc_not_yet_computed: list[str],
    now: datetime,
) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text(_build_report(config, X, metadata, excluded_by_group, excluded_no_lesion_mask,
                                          sdc_not_yet_computed, now))
    return report_path


def _log_path(config: SdcMatrixConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
