"""CLI entry point: build a lesion feature matrix.

Usage:
    python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json

Two representations, picked by config.representation (src.analysis.build_config):
"voxelwise" (src.features.lesion.build_lesion_matrix, subjects x voxels, from the retrieved
lesion masks) or "parcellated" (src.features.parcellated_csv.build_parcellated_matrix,
subjects x anatomical regions, read from the `LF-lesion` CSVs BCBToolKit already computed).

There is no per-subject error accumulation here: either builder succeeds for every
requested subject or raises - a subject-count mismatch or a missing
reference file stops the whole run before anything is written, since a
feature matrix with a silently-missing row would corrupt every downstream
analysis reading it. The parcellated builder additionally reports the two explicit lists it
returns (excluded_no_lesion_mask, csv_not_yet_computed), persisted to config.md.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from src.analysis.build_config import BuildMatrixConfig, load_build_matrix_config
from src.features.lesion import build_lesion_matrix
from src.features.parcellated_csv import build_parcellated_matrix
from src.utils.artifacts import save_matrix
from src.utils.participants import load_excluded_subjects
from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.run_log import append_run_log_entry

LOGS_ROOT = Path("logs") / "build_lesion_matrix"
LOG_FILENAME_PREFIX = "build_summary"

# Which rows of the exclusion list this pipeline obeys: those scoped "lesion" plus those scoped
# "all" (src.utils.participants.load_excluded_subjects). A subject excluded only from an SDC
# representation stays in this matrix - see docs/guides/metadata.md. Both representations ask
# for the same scope: the parcellated one admits exactly the subjects the voxel-wise one does.
_EXCLUSION_SCOPE = "lesion"

_COLUMN_KIND_BY_REPRESENTATION = {"voxelwise": "voxels", "parcellated": "regions"}


@dataclass(frozen=True)
class _BuiltMatrix:
    """What either builder hands back, in the one shape the writer needs.

    `corrected_subjects` exists only for voxelwise (correct_out_of_brain);
    `excluded_no_lesion_mask`/`csv_not_yet_computed` only for parcellated. The other
    representation leaves them empty - for it they are not "none found", they do not apply.
    """

    X: np.ndarray
    metadata: pd.DataFrame
    extra_arrays: dict[str, np.ndarray]
    excluded_by_group: list[str]
    excluded_by_list: list[str]
    corrected_subjects: list[tuple[str, int]] = field(default_factory=list)
    excluded_no_lesion_mask: list[str] = field(default_factory=list)
    csv_not_yet_computed: list[str] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a lesion feature matrix (voxel-wise or parcellated)."
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
        try:
            log_path = _log_path(config, now)
            attach_file_handler(log_path)
        except OSError as exc:
            # No file handler yet at this point - this still reaches the console
            # StreamHandler from basicConfig() above.
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        # Its own error boundary, not folded into the build below: a missing/malformed
        # exclusion list is a config-level problem, and it must stop the run BEFORE any mask is
        # read (lessons_learned.md #9 - a later-added phase is not covered by its neighbour's).
        try:
            excluded_subjects = load_excluded_subjects(config.excluded_subjects_path, _EXCLUSION_SCOPE)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        try:
            built = _build(config, frozenset(excluded_subjects["subject_id"]))
        except (FileNotFoundError, ValueError, nib.filebasedimages.ImageFileError) as exc:
            # ImageFileError (HIGH #20): a truncated/corrupt .nii.gz raises this from nib.load,
            # for either the reference/atlas image or any subject's own lesion mask - neither
            # FileNotFoundError (the file exists) nor ValueError (nibabel's own exception, not
            # ours). Only the voxelwise builder opens images.
            logging.error(str(exc))
            return 1

        excluded_rows = _excluded_rows(excluded_subjects, built.excluded_by_list)
        _log_exclusions(config, built, excluded_rows)

        output_dir = _output_dir(config, now)
        try:
            save_matrix(
                output_dir,
                built.X,
                built.metadata,
                _build_readme_lines(config, built, excluded_rows, now),
                overwrite=config.overwrite,
                extra_arrays=built.extra_arrays,
            )
        except (FileExistsError, ValueError, OSError) as exc:
            logging.error(str(exc))
            return 1
        logging.info("matrix written to %s (shape %s)", output_dir, built.X.shape)

        try:
            append_run_log_entry(
                config.output_root,
                config.session_name,
                now,
                "production",
                _run_log_params(config),
                output_dir,
                config.run_notes,
                config.data_root,
            )
        except OSError as exc:
            logging.error("cannot write run log: %s", exc, exc_info=True)
            return 1

        logging.info("done - matrix written to %s, log written to %s", output_dir, log_path)
        return 0
    finally:
        log_duration(now)


def _build(config: BuildMatrixConfig, excluded_ids: frozenset[str]) -> _BuiltMatrix:
    if config.representation == "voxelwise":
        (
            X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, corrected_subjects,
        ) = build_lesion_matrix(
            data_root=config.data_root,
            datasets=config.datasets,
            reference_template_path=config.reference_template_path,
            lesion_glob=config.lesion_glob,
            binarize_threshold=config.binarize_threshold,
            resample_interpolation=config.resample_interpolation,
            group_filter=config.group_filter,
            excluded_subjects=excluded_ids,
            correct_out_of_brain=config.correct_out_of_brain,
            brain_mask_path=config.brain_mask_path,
        )
        return _BuiltMatrix(
            X, metadata, {"non_constant_mask": non_constant_mask}, excluded_by_group, excluded_by_list,
            corrected_subjects=corrected_subjects,
        )
    if config.representation == "parcellated":
        (
            X, metadata, region_names, excluded_by_group, excluded_by_list,
            excluded_no_lesion_mask, csv_not_yet_computed,
        ) = build_parcellated_matrix(
            data_root=config.data_root,
            datasets=config.datasets,
            object_="lesion",
            atlas=config.atlas,
            value_column=config.value_column,
            reference_labels_path=config.reference_labels_path,
            group_filter=config.group_filter,
            excluded_subjects=excluded_ids,
        )
        return _BuiltMatrix(
            X, metadata, {"region_names": region_names.astype(str)}, excluded_by_group, excluded_by_list,
            excluded_no_lesion_mask=excluded_no_lesion_mask, csv_not_yet_computed=csv_not_yet_computed,
        )
    raise ValueError(f"no builder registered for representation={config.representation!r}")


def _log_exclusions(
    config: BuildMatrixConfig, built: _BuiltMatrix, excluded_rows: list[tuple[str, str, float]]
) -> None:
    if built.excluded_by_group:
        logging.info(
            "%d subject(s) excluded by group_filter=%s: %s",
            len(built.excluded_by_group), config.group_filter, built.excluded_by_group,
        )
    if excluded_rows:
        logging.info(
            "%d subject(s) excluded by %s (subject_id, reason, value): %s",
            len(excluded_rows), config.excluded_subjects_path, excluded_rows,
        )
    if built.corrected_subjects:
        logging.info(
            "%d subject(s) corrected by correct_out_of_brain (subject_id, n_voxels_corrected): %s",
            len(built.corrected_subjects), built.corrected_subjects,
        )
    if built.excluded_no_lesion_mask:
        logging.info(
            "%d subject(s) excluded (LF-lesion CSV present but no lesion mask in the registry): %s",
            len(built.excluded_no_lesion_mask), built.excluded_no_lesion_mask,
        )
    if built.csv_not_yet_computed:
        logging.warning(
            "%d subject(s) have a registered lesion mask but no LF-lesion CSV, so they are NOT in the "
            "matrix: %s", len(built.csv_not_yet_computed), built.csv_not_yet_computed,
        )


def _output_dir(config: BuildMatrixConfig, now: datetime) -> Path:
    return config.output_root / f"{now.strftime('%d-%m')}_{config.session_name}"


def _excluded_rows(
    excluded_subjects: pd.DataFrame, excluded_by_list: list[str]
) -> list[tuple[str, str, float]]:
    """(subject_id, reason, value) for each subject this run actually dropped via the list.

    Joined here rather than inside the builders: the library returns ids, and the reason
    a subject is on the list is the file's business, not the matrix builder's."""
    by_id = excluded_subjects.set_index("subject_id")
    return [
        (subject_id, str(by_id.loc[subject_id, "reason"]), float(by_id.loc[subject_id, "value"]))
        for subject_id in excluded_by_list
    ]


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
        "representation": config.representation,
        "excluded_subjects_path": str(config.excluded_subjects_path),
        "excluded_subjects_scope": _EXCLUSION_SCOPE,
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    # Only the fields of the representation actually used - the other one's fields are None on
    # this config and would otherwise show up as the misleading string "None".
    if config.representation == "voxelwise":
        payload.update({
            "reference_template_path": str(config.reference_template_path),
            "lesion_glob": config.lesion_glob,
            "binarize_threshold": config.binarize_threshold,
            "resample_interpolation": config.resample_interpolation,
            "correct_out_of_brain": config.correct_out_of_brain,
            "brain_mask_path": str(config.brain_mask_path) if config.brain_mask_path is not None else None,
        })
    else:
        payload.update({
            "atlas": config.atlas,
            "value_column": config.value_column,
            "reference_labels_path": str(config.reference_labels_path),
        })
    return json.dumps(payload, indent=2)


def _params_used(config: BuildMatrixConfig) -> dict:
    """Same params dict passed to append_run_log_entry (main()) - the fields that actually
    control matrix construction. AUDIT_FINDINGS.md #49: exposed here too as a single
    "Params used: {...}" line (_summary_lines below), the same line-per-run convention
    dim_reduction.py/clustering.py already standardize on (and embedding_app.py's
    run_params already parses for those two pipelines) - this pipeline had only the
    generic full-config JSON dump, never that single-line form."""
    params = {
        "excluded_subjects_path": str(config.excluded_subjects_path),
        "excluded_subjects_scope": _EXCLUSION_SCOPE,
    }
    if config.representation == "voxelwise":
        return {
            "binarize_threshold": config.binarize_threshold,
            **params,
            "correct_out_of_brain": config.correct_out_of_brain,
        }
    return {"representation": config.representation, "atlas": config.atlas, "value_column": config.value_column, **params}


def _run_log_params(config: BuildMatrixConfig) -> dict:
    """The run-log `params` cell: the voxelwise one keeps its original single key, so every
    existing row of lesion_matrix/runs.csv stays comparable with a new voxelwise one."""
    if config.representation == "voxelwise":
        return {"binarize_threshold": config.binarize_threshold}
    return {"representation": config.representation, "atlas": config.atlas, "value_column": config.value_column}


def _list_section(title: str, ids: list[str]) -> list[str]:
    lines = ["", title, ""]
    if ids:
        lines.append(f"{len(ids)} subject(s):")
        lines += [f"- {subject_id}" for subject_id in ids]
    else:
        lines.append("None.")
    return lines


def _summary_lines(
    config: BuildMatrixConfig, built: _BuiltMatrix, excluded_rows: list[tuple[str, str, float]]
) -> list[str]:
    column_kind = _COLUMN_KIND_BY_REPRESENTATION[config.representation]
    lines = ["## Config", "", "```json", _config_summary(config), "```", "", "## Summary", ""]
    lines.append(f"Matrix shape: {built.X.shape[0]} subjects x {built.X.shape[1]} {column_kind}")
    lines.append(f"Params used: {json.dumps(_params_used(config))}")
    lines += ["", "| dataset | subjects |", "|---|---|"]
    for name, count in _dataset_counts(built.metadata).items():
        lines.append(f"| {name} | {count} |")
    # AUDIT_FINDINGS.md #48: excluded_by_group used to be logged only (logs/ isn't a
    # permanent artifact the way config.md is) - now persisted here too, so "why does this
    # matrix have fewer subjects than expected" is answerable from config.md alone, months
    # later, without the run's original log file. excluded_rows follows the same convention
    # (never logs-only) for the hand-curated exclusion list.
    lines += ["", "## Excluded by group_filter", ""]
    if built.excluded_by_group:
        lines.append(f"{len(built.excluded_by_group)} subject(s) excluded (group_filter={config.group_filter}):")
        lines += [f"- {subject_id}" for subject_id in built.excluded_by_group]
    else:
        lines.append("None.")
    # The reason/value of each exclusion, not just the id: "sub-X was dropped" cannot be
    # reviewed months later, "sub-X was dropped at 2 voxels" can. Only the subjects this run
    # actually discovered appear - the list itself covers every dataset.
    lines += ["", f"## Excluded by `{config.excluded_subjects_path}`", ""]
    if excluded_rows:
        lines.append(f"{len(excluded_rows)} subject(s) excluded by the hand-curated admission list:")
        lines += [f"- {subject_id} ({reason}, value={value:g})" for subject_id, reason, value in excluded_rows]
    else:
        lines.append("None.")
    if config.representation == "voxelwise":
        lines += ["", "## Corrected by correct_out_of_brain", ""]
        if built.corrected_subjects:
            lines.append(f"{len(built.corrected_subjects)} subject(s) had out-of-brain lesion voxels zeroed:")
            lines += [f"- {subject_id} (n_voxels_corrected={n})" for subject_id, n in built.corrected_subjects]
        else:
            lines.append("None.")
    else:
        lines += _list_section(
            "## Excluded (LF-lesion CSV present but no lesion mask in the registry)", built.excluded_no_lesion_mask
        )
        lines += _list_section(
            "## Have a registered lesion mask but no LF-lesion CSV (not in the matrix)", built.csv_not_yet_computed
        )
    return lines


def _build_readme_lines(
    config: BuildMatrixConfig, built: _BuiltMatrix, excluded_rows: list[tuple[str, str, float]], now: datetime
) -> list[str]:
    return [f"# {config.project} lesion matrix — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, built, excluded_rows
    )


def _log_path(config: BuildMatrixConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{LOG_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
