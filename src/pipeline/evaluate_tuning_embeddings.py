"""CLI entry point: run embedding-based evaluations on an already-stored dim_reduction tuning run.

Usage:
    python -m src.pipeline.evaluate_tuning_embeddings --config config/pipelines/evaluate_tuning_embeddings.json

The same evaluations dim_reduction.py applies right after a sweep when its config declares them in
`tuning_evaluations` (today plot_hdbscan), run later on the embeddings.npz that sweep saved
(save_tuning_embeddings=true) - no refit, no original matrix, lesion and sdc alike. The run is read
from `tuning_dir` (embeddings.npz + the grid snapshot in its config.md); outputs are written next to
the sweep's own files, into the same nested leaf folders, with the evaluation's settings in the file
name so another run with other settings adds files instead of replacing them.

Only evaluations that need the embeddings alone are accepted: the sweep's own score
(trustworthiness, explained variance) needs the original matrix and is rejected at config load.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

from src.analysis.model_config import load_evaluate_tuning_embeddings_config
from src.analysis.tuning_embeddings import load_tuning_run
from src.analysis.tuning_evaluations import run_embedding_evaluations, validate_embedding_evaluations_feasible
from src.utils.logging_setup import attach_file_handler, log_duration

LOGS_ROOT = Path("logs") / "evaluate_tuning_embeddings"
LOG_FILENAME_PREFIX = "evaluate_tuning_embeddings"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run embedding-based evaluations on a stored dim_reduction tuning run.")
    parser.add_argument("--config", required=True, help="Path to an evaluate_tuning_embeddings.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_evaluate_tuning_embeddings_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    try:
        try:
            LOGS_ROOT.mkdir(parents=True, exist_ok=True)
            log_path = LOGS_ROOT / f"{LOG_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"
            attach_file_handler(log_path)
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        try:
            run = load_tuning_run(config.tuning_dir)
            validate_embedding_evaluations_feasible(config.tuning_evaluations, run.base_params, run.tuning_grid)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        logging.info("evaluating %s: %d combinations, nested_params=%s", run.run_dir, len(run.embeddings), run.nested_params)
        try:
            written = run_embedding_evaluations(config.tuning_evaluations, run, config.overwrite)
        except (FileExistsError, OSError, ValueError) as exc:
            logging.error("tuning evaluation failed: %s", exc, exc_info=isinstance(exc, OSError))
            return 1

        logging.info("done - %d file(s) written under %s, log written to %s", len(written), run.run_dir, log_path)
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
