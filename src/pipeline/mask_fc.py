"""CLI entry point: mask FC (functional connectivity) matrices by lesion overlap.

Usage:
    python -m src.pipeline.mask_fc --config config/pipelines/mask_fc.json

Deliberately decoupled from build_fc_matrix.py (own config, own output,
own run history) - this pipeline only ever reads raw lesion masks, raw FC
CSVs, and the atlas; its only output is one NaN-masked CSV per subject per
atlas combo. Nothing downstream of this script touches a lesion mask or an
atlas again (see src/features/functional.py module docstring).

Processes every atlas_combo listed in the config sequentially, one
mask_dataset_fc() call per combo, each writing to its own subfolder under
output_root - a subject-count mismatch or a missing atlas file for one combo
stops that combo's processing (raises), but does not touch combos already
written successfully earlier in the same run. AUDIT_FINDINGS.md #52: unlike
build_fc_matrix.py (which isolates a not-yet-ready combo from its siblings,
see #29), a raise here also aborts every *remaining* atlas_combo in the same
config, in list order - main()'s per-combo loop returns 1 immediately on the
first failure rather than continuing to the next combo. Deliberately not
changed to match build_fc_matrix.py's isolation here - a mask_fc.py failure
(atlas/lesion/FC data problem) is more often a config-wide issue likely to
recur on every subsequent combo too, unlike build_fc_matrix.py's "this
combo's masked_fc/ isn't ready yet" gap, which is genuinely per-combo.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.analysis.build_config import MaskFcConfig, load_mask_fc_config
from src.features.functional import mask_dataset_fc, resolve_atlas_paths
from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.run_log import append_run_log_entry

REPORTS_ROOT = Path("summaries") / "mask_fc"
LOGS_ROOT = Path("logs") / "mask_fc"
REPORT_FILENAME_PREFIX = "mask_summary"
SUMMARY_FILENAME = "mask_summary.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mask FC matrices by lesion overlap, per atlas combo.")
    parser.add_argument("--config", required=True, help="Path to a mask_fc.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_mask_fc_config(args.config)
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

        combo_summaries: dict[str, pd.DataFrame] = {}
        for combo in config.atlas_combos:
            output_dir = config.output_root / combo
            if output_dir.exists():
                if not config.overwrite:
                    logging.error(
                        "output dir %s already has masked FC files and overwrite=False - "
                        "set overwrite=true or choose a different output_root",
                        output_dir,
                    )
                    return 1
                # overwrite=True must mean "this combo's output is entirely from this run" -
                # rmtree before mask_dataset_fc recreates it, otherwise a stale file from a
                # previous run (e.g. subjects excluded by a since-tightened group_filter) would
                # keep sitting in output_dir and get silently picked up downstream by
                # build_fc_matrix.py's discover_masked_fc_files (lesson #18).
                try:
                    shutil.rmtree(output_dir)
                except OSError as exc:
                    logging.error("%s: cannot clear existing output dir %s: %s", combo, output_dir, exc, exc_info=True)
                    return 1

            atlas_path, label_table_path = resolve_atlas_paths(config.atlas_root, combo)
            try:
                summary, missing_lesion, excluded_by_group, failed = mask_dataset_fc(
                    data_root=config.data_root,
                    dataset=config.dataset,
                    atlas_path=atlas_path,
                    label_table_path=label_table_path,
                    atlas_combo=combo,
                    lesion_glob=config.lesion_glob,
                    fc_glob_template=config.fc_glob_template,
                    min_coverage=config.min_coverage,
                    resample_interpolation=config.resample_interpolation,
                    binarize_threshold=config.binarize_threshold,
                    output_dir=output_dir,
                    group_filter=config.group_filter,
                )
            except (FileNotFoundError, ValueError) as exc:
                logging.error("%s: %s", combo, exc)
                return 1

            if missing_lesion:
                logging.warning(
                    "%s: %d subject(s) have an FC matrix but no lesion mask, skipped: %s",
                    combo,
                    len(missing_lesion),
                    missing_lesion,
                )
            if excluded_by_group:
                logging.info(
                    "%s: %d subject(s) excluded by group_filter=%s: %s",
                    combo,
                    len(excluded_by_group),
                    config.group_filter,
                    excluded_by_group,
                )
            if failed:
                logging.warning(
                    "%s: %d subject(s) could not be masked, skipped: %s", combo, len(failed), failed
                )
            logging.info(
                "%s: masked %d subjects (mean %.1f compromised nodes/subject)",
                combo,
                len(summary),
                summary["n_compromised_nodes"].mean(),
            )

            try:
                summary.to_csv(output_dir / SUMMARY_FILENAME, index=False)
            except OSError as exc:
                logging.error("%s: cannot write %s: %s", combo, SUMMARY_FILENAME, exc, exc_info=True)
                return 1

            combo_summaries[combo] = summary

            try:
                append_run_log_entry(
                    config.output_root,
                    config.session_name,
                    now,
                    "production",
                    {"min_coverage": config.min_coverage, "n_subjects": len(summary)},
                    output_dir,
                    config.run_notes,
                    config.data_root,
                    extra_columns={"atlas_combo": combo},
                )
            except OSError as exc:
                logging.error("%s: cannot write run log: %s", combo, exc, exc_info=True)
                return 1

        try:
            report_path = _write_report(config, combo_summaries, now)
        except OSError as exc:
            logging.error("cannot write report: %s", exc, exc_info=True)
            return 1

        logging.info(
            "done - masked FC written under %s (%d combo(s)), report written to %s, log written to %s",
            config.output_root,
            len(config.atlas_combos),
            report_path,
            log_path,
        )
        return 0
    finally:
        log_duration(now)


def _config_summary(config: MaskFcConfig) -> str:
    payload = {
        "project": config.project,
        "data_root": str(config.data_root),
        "dataset": config.dataset,
        "group_filter": config.group_filter,
        "atlas_root": str(config.atlas_root),
        "atlas_combos": config.atlas_combos,
        "lesion_glob": config.lesion_glob,
        "fc_glob_template": config.fc_glob_template,
        "min_coverage": config.min_coverage,
        "resample_interpolation": config.resample_interpolation,
        "binarize_threshold": config.binarize_threshold,
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _write_report(config: MaskFcConfig, combo_summaries: dict[str, pd.DataFrame], now: datetime) -> Path:
    lines = [
        f"# {config.project}_{now.strftime('%d-%m-%y')}",
        f"## {now.strftime('%H:%M')}",
        "",
        "## Config",
        "",
        "```json",
        _config_summary(config),
        "```",
        "",
        "## Summary",
        "",
        "| atlas combo | subjects masked | mean compromised nodes |",
        "|---|---:|---:|",
    ]
    for combo, summary in combo_summaries.items():
        lines.append(f"| {combo} | {len(summary)} | {summary['n_compromised_nodes'].mean():.1f} |")

    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(lines) + "\n")
    return report_path


def _log_path(config: MaskFcConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
