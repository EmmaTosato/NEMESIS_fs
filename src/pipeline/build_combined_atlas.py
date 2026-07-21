"""CLI entry point: merge the Glasser MMP cortical atlas with 12 Harvard-Oxford
subcortical structures into a single 372-region atlas.

Usage:
    python -m src.pipeline.build_combined_atlas --config config/pipelines/build_combined_atlas.json

Writes the combined NIfTI atlas, a label lookup CSV (value, name, hemisphere,
source), and a build report. The combined atlas file can then be used as-is
via any pipeline's `atlas_path` config field (e.g. build_lesion_matrix.json)
- src/features/lesion.py accepts any discrete-label NIfTI.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from src.atlases.combine import build_combined_atlas
from src.atlases.config import BuildCombinedAtlasConfig, load_build_combined_atlas_config
from src.utils.logging_setup import attach_file_handler

REPORTS_ROOT = Path("reports") / "build_combined_atlas"
LOGS_ROOT = Path("logs") / "build_combined_atlas"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge the Glasser MMP cortical atlas with 12 Harvard-Oxford subcortical structures."
    )
    parser.add_argument("--config", required=True, help="Path to a build_combined_atlas.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_build_combined_atlas_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    try:
        log_path = _log_path(now)
        attach_file_handler(log_path)
    except OSError as exc:
        logging.error("cannot set up log file: %s", exc, exc_info=True)
        return 1

    if config.output_atlas_path.exists() and not config.overwrite:
        logging.error(
            "output atlas %s already exists and overwrite=False - set overwrite=True or change output_atlas_path",
            config.output_atlas_path,
        )
        return 1

    try:
        combined_labels, label_table, n_overlap_voxels = build_combined_atlas(
            config.cortical_atlas_path, config.subcortical_atlas_path
        )
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    if n_overlap_voxels > 0:
        logging.warning(
            "%d voxel(s) belonged to both a cortical and a subcortical label - cortical label kept "
            "(see src/atlases/combine.py:merge_cortical_subcortical)",
            n_overlap_voxels,
        )

    try:
        _write_outputs(config, combined_labels, label_table)
    except OSError as exc:
        logging.error("cannot write output files: %s", exc, exc_info=True)
        return 1

    try:
        report_path = _write_report(config, label_table, n_overlap_voxels, now)
    except OSError as exc:
        logging.error("cannot write report: %s", exc, exc_info=True)
        return 1

    logging.info(
        "done - atlas written to %s (%d labels), label table written to %s, report written to %s, log written to %s",
        config.output_atlas_path,
        len(label_table),
        config.output_label_table_path,
        report_path,
        log_path,
    )
    return 0


def _write_outputs(
    config: BuildCombinedAtlasConfig, combined_labels: np.ndarray, label_table: pd.DataFrame
) -> None:
    cortical_img = nib.load(config.cortical_atlas_path)
    combined_img = nib.Nifti1Image(combined_labels.astype("int32"), cortical_img.affine)

    config.output_atlas_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(combined_img, config.output_atlas_path)

    config.output_label_table_path.parent.mkdir(parents=True, exist_ok=True)
    label_table.to_csv(config.output_label_table_path, index=False)


def _write_report(
    config: BuildCombinedAtlasConfig, label_table: pd.DataFrame, n_overlap_voxels: int, now: datetime
) -> Path:
    n_cortical = int((label_table["source"] == "glasser_mmp").sum())
    n_subcortical = int((label_table["source"] == "harvard_oxford_subcortical").sum())
    lines = [
        f"# build_combined_atlas — {now.strftime('%d-%m-%y %H:%M')}",
        "",
        "## Config",
        "",
        "```json",
        (
            "{\n"
            f'  "cortical_atlas_path": "{config.cortical_atlas_path}",\n'
            f'  "subcortical_atlas_path": "{config.subcortical_atlas_path}",\n'
            f'  "output_atlas_path": "{config.output_atlas_path}",\n'
            f'  "output_label_table_path": "{config.output_label_table_path}"\n'
            "}"
        ),
        "```",
        "",
        "## Summary",
        "",
        f"Total labels: {len(label_table)} ({n_cortical} cortical + {n_subcortical} subcortical)",
        f"Overlap voxels (cortical/subcortical, resolved in favour of cortical): {n_overlap_voxels}",
    ]

    report_dir = REPORTS_ROOT
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"build_summary__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text("\n".join(lines) + "\n")
    return report_path


def _log_path(now: datetime) -> Path:
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    return LOGS_ROOT / f"build_summary__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
