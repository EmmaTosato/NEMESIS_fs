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

from src.analysis.clustering_tuning_analysis import (
    ADP,
    AGGLOMERATIVE,
    ClusteringTuningRun,
    load_clustering_tuning_run,
    read_run_config,
    tuning_report_markdown,
)
from src.analysis.clustering_tuning_evaluations import load_evaluation_settings, refuse_existing, run_evaluations
from src.analysis.model_config import load_analyze_clustering_tuning_config
from src.utils.logging_setup import attach_file_handler, log_duration

LOGS_ROOT = Path("logs") / "analyze_clustering_tuning"
LOG_FILENAME_PREFIX = "analyze_clustering_tuning"
REPORT_FILENAME = "report.md"


def _read_evaluation_csv(run_dir: Path, name: str, report_of: str) -> pd.DataFrame:
    path = run_dir / name
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found - the {report_of} report reads it: list its evaluation in tuning_evaluations and run again")
    return pd.read_csv(path)


def _report_text(run_dir: Path, run_config: dict, run: ClusteringTuningRun | None) -> str:
    """The text of report.md from the files in the run folder. Raises FileNotFoundError naming the file the
    report needs and the run lacks."""
    if run is None:  # adp: no evaluation, only the table
        results_path = run_dir / "tuning_results.csv"
        if not results_path.is_file():
            raise FileNotFoundError(f"{results_path} not found")
        return tuning_report_markdown(run_dir, ADP, Path(run_config["input_path"]), pd.read_csv(results_path))
    if run.method == AGGLOMERATIVE:
        frames = {
            name: _read_evaluation_csv(run_dir, f"{name}.csv", "agglomerative")
            for name in ("cophenetic_correlation", "linkage_agreement", "dendrogram_jump")
        }
        return tuning_report_markdown(
            run_dir, run.method, run.input_path, run.results,
            frames["cophenetic_correlation"], frames["linkage_agreement"], frames["dendrogram_jump"],
        )
    return tuning_report_markdown(run_dir, run.method, run.input_path, _read_evaluation_csv(run_dir, "density_metrics.csv", run.method))


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
                report_path.write_text(_report_text(config.tuning_dir, run_config, run))
                written.append(report_path)
        except (FileExistsError, FileNotFoundError, OSError, ValueError, pd.errors.ParserError) as exc:
            logging.error("analysis failed: %s", exc, exc_info=isinstance(exc, OSError))
            return 1

        logging.info("done - %d file(s) written under %s, log written to %s", len(written), config.tuning_dir, log_path)
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
