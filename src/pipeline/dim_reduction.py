"""CLI entry point: apply a dimensionality-reduction method to an already-built feature matrix.

Usage:
    python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json

Reads a matrix artifact written by build_lesion_matrix.py (input_path must
already exist - no auto-build fallback), embeds it with the configured
method, and writes a new artifact holding the embedding. metadata is carried
over unchanged (same subjects/dataset, same row order) since reduction
doesn't touch it.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from src.analysis.model_config import DimReductionConfig, load_dim_reduction_config
from src.analysis.params import load_method_params
from src.analysis.reduction import REDUCTION_METHODS
from src.utils.artifacts import load_matrix, save_matrix
from src.utils.logging_setup import attach_file_handler

REPORTS_ROOT = Path("reports") / "dim_reduction"
LOGS_ROOT = Path("logs") / "dim_reduction"
REPORT_FILENAME_PREFIX = "dim_reduction_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Embed a feature matrix with a configured dimensionality-reduction method.")
    parser.add_argument("--config", required=True, help="Path to a dim_reduction.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_dim_reduction_config(args.config)
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

    try:
        X, metadata, _extra_arrays = load_matrix(config.input_path)
        params = load_method_params(config.params_file, config.reduction_method)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    embedding = REDUCTION_METHODS[config.reduction_method](X, params)

    output_dir = _output_dir(config, now)
    try:
        save_matrix(
            output_dir,
            embedding,
            metadata,
            _build_readme_lines(config, X, embedding, params, now),
            overwrite=config.overwrite,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        logging.error(str(exc))
        return 1
    logging.info("embedding written to %s (shape %s)", output_dir, embedding.shape)

    try:
        report_path = _write_report(config, X, embedding, params, now)
    except OSError as exc:
        logging.error("cannot write report: %s", exc, exc_info=True)
        return 1

    logging.info(
        "done - embedding written to %s, report written to %s, log written to %s", output_dir, report_path, log_path
    )
    return 0


def _output_dir(config: DimReductionConfig, now: datetime) -> Path:
    return config.output_root / config.reduction_method / f"{now.strftime('%d-%m')}_{config.run_name}"


def _config_summary(config: DimReductionConfig) -> str:
    payload = {
        "project": config.project,
        "input_path": str(config.input_path),
        "reduction_method": config.reduction_method,
        "params_file": str(config.params_file),
        "output_root": str(config.output_root),
        "run_name": config.run_name,
        "overwrite": config.overwrite,
    }
    return json.dumps(payload, indent=2)


def _summary_lines(config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict) -> list[str]:
    return [
        "## Config",
        "",
        "```json",
        _config_summary(config),
        "```",
        "",
        "## Summary",
        "",
        f"Input matrix shape: {X.shape[0]} subjects x {X.shape[1]} features",
        f"Embedding shape: {embedding.shape[0]} subjects x {embedding.shape[1]} components",
        f"Params used: {json.dumps(params)}",
    ]


def _build_readme_lines(
    config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict, now: datetime
) -> list[str]:
    return [f"# {config.project} dim_reduction ({config.reduction_method}) — {now.strftime('%d-%m-%y %H:%M')}", ""] + _summary_lines(
        config, X, embedding, params
    )


def _build_report(config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict, now: datetime) -> str:
    lines = [f"# {config.project}_{now.strftime('%d-%m-%y')}", f"## {now.strftime('%H:%M')}", ""] + _summary_lines(
        config, X, embedding, params
    )
    return "\n".join(lines)


def _write_report(config: DimReductionConfig, X: np.ndarray, embedding: np.ndarray, params: dict, now: datetime) -> Path:
    report_dir = REPORTS_ROOT / config.project
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, X, embedding, params, now))
    return report_path


def _log_path(config: DimReductionConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
