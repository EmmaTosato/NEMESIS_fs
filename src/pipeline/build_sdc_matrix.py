"""CLI entry point: build an SDC feature matrix from retrieved SDC output.

Usage:
    python -m src.pipeline.build_sdc_matrix --config config/pipelines/build_sdc_matrix.json

Three representations, picked by config.representation (see
src.analysis.build_config.load_build_sdc_matrix_config / src/features/sdc.py):
"parcellated" (build_sdc_matrix, the original one, per-atlas region CSVs),
"voxelwise" (build_sdc_voxelwise_matrix, added 03/09, the disconnectome-map
.nii.gz directly) or "streamline" (build_sdc_streamline_matrix, added 30/09,
one streamline_ratio per white matter tract). Same shape as
build_lesion_matrix.py in every case:
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
from src.features.sdc import build_sdc_matrix, build_sdc_streamline_matrix, build_sdc_voxelwise_matrix
from src.utils.artifacts import save_matrix
from src.utils.participants import load_excluded_subjects
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

        # Its own error boundary, before any SDC file is opened (lessons_learned.md #9). The same
        # list the lesion matrix reads, asked for this representation's scope: rows scoped "all"
        # apply to every matrix, so a lesion-vs-SDC comparison still shares one cohort unless a
        # row deliberately narrows itself to one feature space.
        try:
            excluded_subjects = load_excluded_subjects(
                config.excluded_subjects_path, _exclusion_scope(config)
            )
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1
        excluded_ids = frozenset(excluded_subjects["subject_id"])

        try:
            if config.representation == "parcellated":
                (
                    X, metadata, column_labels, excluded_by_group, excluded_by_list,
                    excluded_no_lesion_mask, sdc_not_yet_computed,
                ) = build_sdc_matrix(
                    data_root=config.data_root,
                    datasets=config.datasets,
                    object_=config.object,
                    atlas=config.atlas,
                    value_column=config.value_column,
                    reference_labels_path=config.reference_labels_path,
                    group_filter=config.group_filter,
                    excluded_subjects=excluded_ids,
                )
            elif config.representation == "streamline":
                (
                    X, metadata, column_labels, excluded_by_group, excluded_by_list,
                    excluded_no_lesion_mask, sdc_not_yet_computed,
                ) = build_sdc_streamline_matrix(
                    data_root=config.data_root,
                    datasets=config.datasets,
                    object_=config.object,
                    reference_labels_path=config.reference_labels_path,
                    group_filter=config.group_filter,
                    excluded_subjects=excluded_ids,
                )
            else:
                (
                    X, metadata, column_labels, excluded_by_group, excluded_by_list,
                    excluded_no_lesion_mask, sdc_not_yet_computed,
                ) = build_sdc_voxelwise_matrix(
                    data_root=config.data_root,
                    datasets=config.datasets,
                    object_=config.object,
                    reference_template_path=config.reference_template_path,
                    resample_interpolation=config.resample_interpolation,
                    group_filter=config.group_filter,
                    excluded_subjects=excluded_ids,
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
        if excluded_by_list:
            logging.info(
                "%d subject(s) excluded by %s: %s",
                len(excluded_by_list), config.excluded_subjects_path, excluded_by_list,
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
        extra_arrays = _extra_arrays(config, column_labels)

        try:
            save_matrix(
                output_dir,
                X,
                metadata,
                _build_readme_lines(
                    config, X, metadata, excluded_by_group, excluded_by_list,
                    excluded_no_lesion_mask, sdc_not_yet_computed, now,
                ),
                overwrite=config.overwrite,
                extra_arrays=extra_arrays,
            )
        except (FileExistsError, ValueError, OSError) as exc:
            logging.error(str(exc))
            return 1
        logging.info("matrix written to %s (shape %s)", output_dir, X.shape)

        try:
            report_path = _write_report(
                config, X, metadata, excluded_by_group, excluded_by_list,
                excluded_no_lesion_mask, sdc_not_yet_computed, now,
            )
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


def _exclusion_scope(config: SdcMatrixConfig) -> str:
    """Which rows of the exclusion list this run obeys: its own representation's, plus "all".

    Derived from `representation` rather than hardcoded per branch, so a fourth representation
    cannot silently inherit another one's exclusions - src.utils.participants validates the
    result against KNOWN_EXCLUSION_SCOPES and raises on an unregistered one.
    """
    return f"sdc-{config.representation}"


def _output_dir(config: SdcMatrixConfig, now: datetime) -> Path:
    return config.output_root / f"{now.strftime('%d-%m')}_{config.session_name}"


def _dataset_counts(metadata: pd.DataFrame) -> dict[str, int]:
    return {name: int(count) for name, count in metadata["dataset"].value_counts().sort_index().items()}


_COLUMN_KIND_BY_REPRESENTATION = {"parcellated": "regions", "voxelwise": "voxels", "streamline": "tracts"}


def _column_kind(config: SdcMatrixConfig) -> str:
    """What one column of X means, for the report/config.md wording.

    An explicit lookup rather than an if/else: the set of representations has
    grown twice already, and a two-branch expression silently labels any new
    one with whichever branch it falls into (lessons_learned.md #1).
    """
    if config.representation not in _COLUMN_KIND_BY_REPRESENTATION:
        raise ValueError(
            f"no column kind registered for representation={config.representation!r} - "
            f"known: {sorted(_COLUMN_KIND_BY_REPRESENTATION)}"
        )
    return _COLUMN_KIND_BY_REPRESENTATION[config.representation]


def _extra_arrays(config: SdcMatrixConfig, column_labels: np.ndarray) -> dict[str, np.ndarray]:
    """The per-representation array saved alongside matrix.npy.

    Label arrays ("region_names"/"tract_names") for the two representations
    that never drop a column, a bool drop-mask ("non_constant_mask", same
    convention as build_lesion_matrix.py) for the voxelwise one - which is the
    only one that does drop columns (see src/features/sdc.py).
    """
    if config.representation == "parcellated":
        return {"region_names": column_labels.astype(str)}
    if config.representation == "streamline":
        return {"tract_names": column_labels.astype(str)}
    if config.representation == "voxelwise":
        return {"non_constant_mask": column_labels}
    raise ValueError(f"no extra array registered for representation={config.representation!r}")


def _config_summary(config: SdcMatrixConfig) -> str:
    payload = {
        "project": config.project,
        "data_root": str(config.data_root),
        "datasets": config.datasets,
        "group_filter": config.group_filter,
        "excluded_subjects_path": str(config.excluded_subjects_path),
        "excluded_subjects_scope": _exclusion_scope(config),
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
    elif config.representation == "streamline":
        # atlas is pinned by the representation, not read from the config - recorded
        # anyway so config.md states which file the matrix was actually built from.
        payload["atlas"] = config.atlas
        payload["reference_labels_path"] = str(config.reference_labels_path)
    else:
        payload["reference_template_path"] = str(config.reference_template_path)
        payload["resample_interpolation"] = config.resample_interpolation
    return json.dumps(payload, indent=2)


def _params_used(config: SdcMatrixConfig) -> dict:
    if config.representation == "parcellated":
        return {"object": config.object, "atlas": config.atlas, "value_column": config.value_column}
    if config.representation == "streamline":
        return {"object": config.object, "representation": config.representation, "atlas": config.atlas}
    return {"object": config.object, "representation": config.representation}


def _summary_lines(
    config: SdcMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    excluded_by_list: list[str],
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
    lines += ["", f"## Excluded by `{config.excluded_subjects_path}`", ""]
    if excluded_by_list:
        lines.append(f"{len(excluded_by_list)} subject(s) excluded by the hand-curated admission list:")
        lines += [f"- {subject_id}" for subject_id in excluded_by_list]
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
    excluded_by_list: list[str],
    excluded_no_lesion_mask: list[str],
    sdc_not_yet_computed: list[str],
    now: datetime,
) -> list[str]:
    return [f"# {config.project} sdc matrix — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, X, metadata, excluded_by_group, excluded_by_list, excluded_no_lesion_mask,
        sdc_not_yet_computed,
    )


def _build_report(
    config: SdcMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    excluded_by_list: list[str],
    excluded_no_lesion_mask: list[str],
    sdc_not_yet_computed: list[str],
    now: datetime,
) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')}", ""] + _summary_lines(
        config, X, metadata, excluded_by_group, excluded_by_list, excluded_no_lesion_mask,
        sdc_not_yet_computed,
    )
    return "\n".join(lines)


def _write_report(
    config: SdcMatrixConfig,
    X: np.ndarray,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    excluded_by_list: list[str],
    excluded_no_lesion_mask: list[str],
    sdc_not_yet_computed: list[str],
    now: datetime,
) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text(
        _build_report(
            config, X, metadata, excluded_by_group, excluded_by_list, excluded_no_lesion_mask,
            sdc_not_yet_computed, now,
        )
    )
    return report_path


def _log_path(config: SdcMatrixConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
