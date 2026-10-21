"""CLI entry point: analyse an already-stored clustering tuning run.

Usage:
    python -m src.pipeline.analyze_clustering_tuning --config config/pipelines/analyze_clustering_tuning.json

Reads the files `clustering.py --fine_tuning true` wrote (tuning_results.csv, clusterings.npz, config.md and,
for the evaluations that need it, the matrix its config.md points to) and runs on them the evaluations
the config's `tuning_evaluations` block lists for the run's method
(src/analysis/clustering_tuning_evaluations.py - the same function the sweep runs when its own config lists them),
writing their files next to the run's:

- agglomerative: cophenetic_correlation.csv, dendrogram_jump.csv, linkage_agreement.csv, k_curves_metric=<metric>.png and
  k_curves_single_metric=<metric>.png (the single linkage, in a figure of its own)
- hdbscan / hdbscan_soft: density_metrics.csv, noise_filtered_curves[_cluster_selection_method=<method>].png

With `write_report` it then writes report.md, the tables of those files and of tuning_results.csv with no verdict;
it reads them from the run folder, so the evaluations it needs must have been run (now or by the sweep).
Nothing is refitted. Lesion and sdc alike; adp has no evaluation and only gets report.md (its own diagnostics:
docs/guides/clustering.md).
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.analysis.clustering_tuning_analysis import ADP, load_clustering_tuning_run, read_run_config
from src.analysis.clustering_tuning_evaluations import load_evaluation_settings, refuse_existing, run_evaluations
from src.analysis.clustering_tuning_report import REPORT_FILENAME, write_report
from src.analysis.model_config import load_analyze_clustering_tuning_config
from src.utils.logging_setup import attach_file_handler, log_duration

LOGS_ROOT = Path("logs") / "analyze_clustering_tuning"
LOG_FILENAME_PREFIX = "analyze_clustering_tuning"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyse a stored clustering tuning run.")
    parser.add_argument("--config", required=True, help="Path to an analyze_clustering_tuning.json file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_analyze_clustering_tuning_config(args.config)
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
            run_config = read_run_config(config.tuning_dir)
            run = None if run_config["clustering_method"] == ADP else load_clustering_tuning_run(config.tuning_dir)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        logging.info("analysing %s: method=%s", config.tuning_dir, run_config["clustering_method"])
        report_path = config.tuning_dir / REPORT_FILENAME
        try:
            if config.write_report:
                refuse_existing([report_path], config.overwrite)
            settings = load_evaluation_settings(config.evaluations_file)
            written = [] if run is None else run_evaluations(config.tuning_evaluations, settings, run, config.overwrite)
            if config.write_report:
                written.append(write_report(config.tuning_dir, config.overwrite))
        except (FileExistsError, FileNotFoundError, OSError, ValueError, pd.errors.ParserError) as exc:
            logging.error("analysis failed: %s", exc, exc_info=isinstance(exc, OSError))
            return 1

        logging.info("done - %d file(s) written under %s, log written to %s", len(written), config.tuning_dir, log_path)
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
