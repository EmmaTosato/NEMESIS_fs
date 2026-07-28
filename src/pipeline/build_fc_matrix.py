"""CLI entry point: build a subjects x edges FC feature matrix from already-masked FC data.

Usage:
    python -m src.pipeline.build_fc_matrix --config config/pipelines/build_fc_matrix.json

Deliberately decoupled from mask_fc.py (own config, own output, own run
history) - this pipeline never touches a lesion mask or an atlas; it only
reads the NaN-masked per-subject CSVs mask_fc.py already wrote. The output
matrix still has NaN in it (compromised edges) - imputation to a concrete
fill value is a separate, later step that belongs next to
src/analysis/reduction.py, not here (see src/features/functional.py module
docstring for why).

Processes every atlas_combo listed in the config sequentially, one
build_fc_matrix_from_masked() call per combo, each writing its own matrix
artifact under output_root/<combo>/.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.build_config import BuildFcMatrixConfig, load_build_fc_matrix_config
from src.features.functional import build_fc_matrix_from_masked
from src.utils.artifacts import save_matrix
from src.utils.logging_setup import attach_file_handler
from src.utils.run_log import append_run_log_entry

REPORTS_ROOT = Path("summaries") / "build_fc_matrix"
LOGS_ROOT = Path("logs") / "build_fc_matrix"
REPORT_FILENAME_PREFIX = "build_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a subjects x edges FC feature matrix from already-masked FC data."
    )
    parser.add_argument("--config", required=True, help="Path to a build_fc_matrix.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_build_fc_matrix_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    try:
        log_path = _log_path(config, now)
        attach_file_handler(log_path)
    except OSError as exc:
        logging.error("cannot set up log file: %s", exc, exc_info=True)
        return 1

    combo_reports: dict[str, dict] = {}
    for combo in config.atlas_combos:
        input_dir = config.masked_fc_root / combo
        try:
            X, metadata, edge_names, dropped_info = build_fc_matrix_from_masked(input_dir)
        except (FileNotFoundError, ValueError) as exc:
            logging.error("%s: %s", combo, exc)
            return 1

        if dropped_info:
            logging.warning(
                "%s: %d edge(s) had an identical value across every subject and were dropped "
                "(unexpected for continuous FC data, verify upstream computation): %s",
                combo,
                len(dropped_info),
                dropped_info,
            )
        else:
            logging.info("%s: constant-edge check complete - 0 constant edges found, %d/%d kept", combo, len(edge_names), len(edge_names))

        nan_per_subject = pd.Series(np.isnan(X).sum(axis=1), index=metadata["subject_id"])
        nan_per_edge = pd.Series(np.isnan(X).sum(axis=0), index=edge_names)
        logging.info(
            "%s: matrix built (%d subjects x %d edges) - NaN per subject: min=%d max=%d mean=%.1f",
            combo,
            X.shape[0],
            X.shape[1],
            int(nan_per_subject.min()),
            int(nan_per_subject.max()),
            float(nan_per_subject.mean()),
        )

        output_dir = config.output_root / combo / f"{now.strftime('%d-%m')}_{config.session_name}"
        readme_lines = _build_readme_lines(config, combo, X, dropped_info, now)
        try:
            save_matrix(
                output_dir,
                X,
                metadata,
                readme_lines,
                overwrite=config.overwrite,
                # np.array(edge_names) without dtype=object: a plain unicode array, loadable via
                # np.load without allow_pickle=True - an object-dtype array would require it.
                extra_arrays={"edge_names": np.array(edge_names)},
            )
        except (FileExistsError, ValueError, OSError) as exc:
            logging.error("%s: %s", combo, exc)
            return 1
        logging.info("%s: matrix written to %s (shape %s)", combo, output_dir, X.shape)

        combo_reports[combo] = {
            "output_dir": output_dir,
            "shape": X.shape,
            "n_dropped_constant_edges": len(dropped_info),
            "nan_per_subject": nan_per_subject,
            "nan_per_edge": nan_per_edge,
        }

        try:
            append_run_log_entry(
                config.output_root,
                config.session_name,
                now,
                "production",
                {"n_subjects": X.shape[0], "n_edges": X.shape[1]},
                output_dir,
                config.run_notes,
                extra_columns={"atlas_combo": combo},
            )
        except OSError as exc:
            logging.error("%s: cannot write run log: %s", combo, exc, exc_info=True)
            return 1

    try:
        report_path = _write_report(config, combo_reports, now)
    except OSError as exc:
        logging.error("cannot write report: %s", exc, exc_info=True)
        return 1

    logging.info(
        "done - matrices written under %s (%d combo(s)), report written to %s, log written to %s",
        config.output_root,
        len(config.atlas_combos),
        report_path,
        log_path,
    )
    return 0


def _config_summary(config: BuildFcMatrixConfig) -> str:
    payload = {
        "project": config.project,
        "masked_fc_root": str(config.masked_fc_root),
        "atlas_combos": config.atlas_combos,
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }
    return json.dumps(payload, indent=2)


def _build_readme_lines(
    config: BuildFcMatrixConfig, combo: str, X: np.ndarray, dropped_info: list[tuple[str, float]], now: datetime
) -> list[str]:
    lines = [
        f"# {config.project} FC matrix ({combo}) — {now.strftime('%d-%m-%y %H:%M')}",
        "",
        "## Config",
        "",
        "```json",
        _config_summary(config),
        "```",
        "",
        "## Summary",
        "",
        f"Matrix shape: {X.shape[0]} subjects x {X.shape[1]} edges",
        f"Constant edges dropped: {len(dropped_info)}",
        "Matrix still contains NaN for lesion-compromised edges - imputation happens later, "
        "immediately before dimensionality reduction, not in this artifact.",
    ]
    return lines


def _write_report(config: BuildFcMatrixConfig, combo_reports: dict[str, dict], now: datetime) -> Path:
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
        "| atlas combo | shape | constant edges dropped | NaN/subject (min/mean/max) |",
        "|---|---|---:|---|",
    ]
    for combo, report in combo_reports.items():
        nan_per_subject = report["nan_per_subject"]
        shape = f"{report['shape'][0]}x{report['shape'][1]}"
        lines.append(
            f"| {combo} | {shape} | {report['n_dropped_constant_edges']} | "
            f"{int(nan_per_subject.min())}/{nan_per_subject.mean():.1f}/{int(nan_per_subject.max())} |"
        )

    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text("\n".join(lines) + "\n")
    return report_path


def _log_path(config: BuildFcMatrixConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
