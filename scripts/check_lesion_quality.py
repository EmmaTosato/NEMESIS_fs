"""CLI entry point: compute the per-subject fraction of lesion voxels falling outside
the brain for every subject with a discoverable lesion mask, and cache it to a CSV
under assets/metadata/.

A diagnostic companion to build_lesion_matrix.py's own max_out_of_brain_fraction
admission filter (src/features/lesion.py::compute_lesion_quality_metrics does the
actual work, no threshold applied here - every discovered subject is reported) -
useful for inspecting the real distribution and picking that threshold *before*
committing to a production run, since an already-built
data/derived/lesion_matrix/<session>/ can never be filtered after the fact (see
docs/dev/lesion_matrix.md).

Deliberately does NOT write lesion_volume_voxels (unlike an earlier version of this
script) - assets/metadata/participants.csv is the one place for that value
(src.pipeline.enrich_metadata, via src.features.lesion.compute_lesion_volumes); a
second, independently computed copy here drifted from it by up to 38x for some
subjects before this was fixed (found 28-09-26, see
.claude/history/methods_changelog.md).

Reuses config/pipelines/build_lesion_matrix.json for how to discover/load/resample
lesion masks (data_root, datasets, reference_template_path, lesion_glob,
binarize_threshold, resample_interpolation, group_filter, brain_mask_path) - single
source of truth for that shared concern, not a second config file prone to drifting
from the first. min_lesion_volume_voxels/max_out_of_brain_fraction/output_root/
session_name/overwrite from that same file are not read here - this script has its own
--output-path/--overwrite, a different concern (where the metrics CSV goes) from where
a matrix goes.

Usage:
    conda activate nemesis
    PYTHONPATH=. python scripts/check_lesion_quality.py \
        --config config/pipelines/build_lesion_matrix.json \
        --output-path assets/metadata/lesion_quality_metrics.csv

`--overwrite` recomputes and replaces the CSV even if it already exists (the expensive
part - one nibabel load + resample per subject - takes minutes over the full cohort,
see docs/debugging notes on notebooks/exploration/dataset_exploration.ipynb's own
out-of-brain section). Without it, an existing CSV is left untouched and the run exits
immediately (0) - this script is meant to be safe to invoke repeatedly (e.g. from a
notebook, before every use) without accidentally re-paying that cost.
"""

from __future__ import annotations

import argparse
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.analysis.build_config import load_build_matrix_config
from src.features.lesion import compute_lesion_quality_metrics
from src.utils.logging_setup import attach_file_handler, log_duration

REPORTS_ROOT = Path("summaries") / "check_lesion_quality"
LOGS_ROOT = Path("logs") / "check_lesion_quality"
REPORT_FILENAME_PREFIX = "check_lesion_quality_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute per-subject lesion-quality metrics (volume, out-of-brain fraction) and cache them to a CSV."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a build_lesion_matrix.json-shaped config (data_root/datasets/reference_template_path/"
        "lesion_glob/binarize_threshold/resample_interpolation/group_filter/brain_mask_path are read from it)",
    )
    parser.add_argument(
        "--output-path",
        default="assets/metadata/lesion_quality_metrics.csv",
        help="Where to write the metrics CSV (default: assets/metadata/lesion_quality_metrics.csv)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recompute and replace an existing output CSV. Without this flag, an existing file is left "
        "untouched and the run exits immediately (0) - the expensive computation is never re-paid by accident.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    output_path = Path(args.output_path)
    now = datetime.now()

    try:
        if output_path.is_file() and not args.overwrite:
            logging.info("%s already exists and --overwrite not set - nothing to do", output_path)
            return 0

        try:
            config = load_build_matrix_config(args.config)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        if config.brain_mask_path is None:
            logging.error(
                "%s has no brain_mask_path set (max_out_of_brain_fraction is null) - this script needs one "
                "regardless of whether build_lesion_matrix.py's own threshold is active",
                args.config,
            )
            return 1

        try:
            log_path = LOGS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"
            LOGS_ROOT.mkdir(parents=True, exist_ok=True)
            attach_file_handler(log_path)
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        try:
            metadata, excluded_by_group = compute_lesion_quality_metrics(
                data_root=config.data_root,
                datasets=config.datasets,
                reference_template_path=config.reference_template_path,
                lesion_glob=config.lesion_glob,
                binarize_threshold=config.binarize_threshold,
                resample_interpolation=config.resample_interpolation,
                group_filter=config.group_filter,
                brain_mask_path=config.brain_mask_path,
            )
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        if excluded_by_group:
            logging.info(
                "%d subject(s) excluded by group_filter=%s: %s",
                len(excluded_by_group),
                config.group_filter,
                excluded_by_group,
            )

        try:
            _write_csv(metadata, output_path)
            report_path = _write_report(config, metadata, excluded_by_group, output_path, now)
        except OSError as exc:
            logging.error("cannot write output: %s", exc, exc_info=True)
            return 1

        logging.info(
            "done - %d subject(s) written to %s, report written to %s, log written to %s",
            len(metadata),
            output_path,
            report_path,
            log_path,
        )
        return 0
    finally:
        log_duration(now)


def _write_csv(metadata: pd.DataFrame, output_path: Path) -> None:
    """Atomic write (temp file + os.replace, same convention as
    scripts/populate_metadata.py::write_table) - a crash never leaves a half-written CSV,
    which a downstream reader (this script's own --overwrite check, a notebook) would
    otherwise treat as a genuine, complete cache."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_path.name}_tmp_", dir=output_path.parent)
    os.close(fd)
    try:
        metadata.to_csv(tmp_name, index=False)
        os.replace(tmp_name, output_path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _dataset_counts(metadata: pd.DataFrame) -> dict[str, int]:
    return {name: int(count) for name, count in metadata["dataset"].value_counts().sort_index().items()}


def _report_lines(
    config,
    metadata: pd.DataFrame,
    excluded_by_group: list[str],
    output_path: Path,
    now: datetime,
) -> list[str]:
    lines = [
        f"# check_lesion_quality — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"output: `{output_path}` ({len(metadata)} rows) · group_filter: {config.group_filter}",
        f"brain_mask_path: `{config.brain_mask_path}`",
        "",
        "| dataset | subjects |",
        "|---|---|",
    ]
    for name, count in _dataset_counts(metadata).items():
        lines.append(f"| {name} | {count} |")
    lines += [
        "",
        "## out_of_brain_fraction",
        "",
        f"min={metadata['out_of_brain_fraction'].min():.4f} · median={metadata['out_of_brain_fraction'].median():.4f} · "
        f"max={metadata['out_of_brain_fraction'].max():.4f}",
        "",
        "## Excluded by group_filter",
        "",
    ]
    if excluded_by_group:
        lines.append(f"{len(excluded_by_group)} subject(s) excluded (group_filter={config.group_filter}):")
        lines += [f"- {subject_id}" for subject_id in excluded_by_group]
    else:
        lines.append("None.")
    return lines


def _write_report(config, metadata: pd.DataFrame, excluded_by_group: list[str], output_path: Path, now: datetime) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(_report_lines(config, metadata, excluded_by_group, output_path, now)) + "\n")
    return report_path


if __name__ == "__main__":
    raise SystemExit(main())
