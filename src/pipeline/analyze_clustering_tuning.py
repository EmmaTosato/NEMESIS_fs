"""CLI entry point: analyse an already-stored clustering tuning run.

Usage:
    python -m src.pipeline.analyze_clustering_tuning --config config/pipelines/analyze_clustering_tuning.json

Reads the files `clustering.py --fine_tuning true` wrote (tuning_results.csv, clusterings.npz, config.md and,
for agglomerative, the matrix its config.md points to) and writes what the sweep does not, next to them:

- agglomerative: cophenetic_correlation.csv, dendrogram_jump.csv, k_curves_metric=<metric>.png
- hdbscan / hdbscan_soft: candidates.csv, noise_filtered_curves[_cluster_selection_method=<method>].png

Nothing is refitted. Lesion and sdc alike; adp is not handled (docs/guides/clustering.md).
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from src.analysis.clustering_tuning_analysis import (
    AGGLOMERATIVE,
    ClusteringTuningRun,
    agglomerative_analysis,
    density_candidates,
    k_curves_figure,
    load_clustering_tuning_run,
    noise_filtered_curves_figures,
)
from src.analysis.model_config import AnalyzeClusteringTuningConfig, load_analyze_clustering_tuning_config
from src.utils.artifacts import load_matrix
from src.utils.logging_setup import attach_file_handler, log_duration

LOGS_ROOT = Path("logs") / "analyze_clustering_tuning"
LOG_FILENAME_PREFIX = "analyze_clustering_tuning"


def _refuse_existing(paths: list[Path], overwrite: bool) -> None:
    existing = [path.name for path in paths if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"already in the run folder: {existing} - set overwrite=true to replace them")


def _save_figure(figure: Figure, path: Path) -> None:
    figure.savefig(path, dpi=150)


def _analyze_agglomerative(run: ClusteringTuningRun, config: AnalyzeClusteringTuningConfig) -> list[Path]:
    metrics = sorted(run.results["metric"].unique())
    outputs = {
        "cophenetic": run.run_dir / "cophenetic_correlation.csv",
        "jump": run.run_dir / "dendrogram_jump.csv",
        **{f"curves_{metric}": run.run_dir / f"k_curves_metric={metric}.png" for metric in metrics},
    }
    _refuse_existing(list(outputs.values()), config.overwrite)

    X, _, _ = load_matrix(run.input_path)
    cophenetic, jump = agglomerative_analysis(run, X, range(config.k_min, config.k_max + 1))
    cophenetic.to_csv(outputs["cophenetic"], index=False)
    jump.to_csv(outputs["jump"], index=False)
    for metric in metrics:
        _save_figure(k_curves_figure(run.results, metric), outputs[f"curves_{metric}"])
    return list(outputs.values())


def _analyze_density(run: ClusteringTuningRun, config: AnalyzeClusteringTuningConfig) -> list[Path]:
    candidates = density_candidates(run, config.usable)
    figures, without_figure = noise_filtered_curves_figures(candidates, config.curves_max_noise_fraction)
    for name in without_figure:
        logging.warning(
            "no combination has noise_fraction <= %s%s: no curves figure for it",
            config.curves_max_noise_fraction, f" for cluster_selection_method={name}" if name else "",
        )
    paths = {name: run.run_dir / (f"noise_filtered_curves_{name}.png" if name else "noise_filtered_curves.png") for name in figures}
    csv_path = run.run_dir / "candidates.csv"
    _refuse_existing([csv_path, *paths.values()], config.overwrite)  # candidates.csv is written even with no figure

    candidates.to_csv(csv_path, index=False)
    for name, figure in figures.items():
        _save_figure(figure, paths[name])
    logging.info("usable combinations: %d of %d", int(candidates["usable"].sum()), len(candidates))
    return [csv_path, *paths.values()]


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
            run = load_clustering_tuning_run(config.tuning_dir)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        logging.info("analysing %s: method=%s, %d combinations", run.run_dir, run.method, len(run.results))
        try:
            written = _analyze_agglomerative(run, config) if run.method == AGGLOMERATIVE else _analyze_density(run, config)
        except (FileExistsError, FileNotFoundError, OSError, ValueError, pd.errors.ParserError) as exc:
            logging.error("analysis failed: %s", exc, exc_info=isinstance(exc, OSError))
            return 1

        logging.info("done - %d file(s) written under %s, log written to %s", len(written), run.run_dir, log_path)
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
