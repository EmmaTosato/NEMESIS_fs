"""One-off CLI: calibrate the bilaterality threshold for a future geometric lesion_side
computation, against the clinical lesion_side labels already in assets/metadata/participants.csv.

Context (see docs/dev/metadata.md): lesion_side is populated only where a dataset records
it clinically; a geometric fallback (voxel counts either side of the MNI midline) is a
known open item, deliberately not implemented yet because the threshold above which a
lesion counts as "both" (bilateral) needs to be calibrated against real ground truth
first, not guessed (code_standards.md §0).

This script does NOT write lesion_side_source="geometric" anywhere, does NOT touch
participants.csv, and does NOT decide a final threshold - it only computes
laterality_index (src.features.lesion.compute_lesion_laterality_metrics) for every
subject in a clinically-labelled dataset, compares candidate thresholds against the real
labels, and writes a report so a threshold can be chosen with evidence.

laterality_index = (left_voxels - right_voxels) / (left_voxels + right_voxels) - the
standard lesion/fMRI laterality-index convention (Wilke & Lidzba LI-toolbox; Rorden's
Gigascience LI protocol for stroke lesion masks). A literature-typical bilaterality
threshold is |LI| < 0.2; this script checks that value AND grid-searches for the
threshold that best reproduces our own clinical labels, so both can be compared.

Usage:
    conda activate nemesis
    PYTHONPATH=. python scripts/calibrate_lesion_side_threshold.py \
        --config config/pipelines/build_lesion_matrix.json \
        --datasets UNIPD/WashU UNIPD/PSP UKLFR/stroke_UKLFR UKE/WAKEUP_acute UKE/SFB936_ses01

--datasets overrides the config's own `datasets` list for this run only (the production
build_lesion_matrix.json doesn't yet include every dataset that has clinical lesion_side
labels, e.g. UKE/SFB936_ses01 - see .claude/history/data_changelog.md 28-09-26) - every
other imaging parameter (data_root, reference_template_path, lesion_glob,
binarize_threshold, resample_interpolation, group_filter) is still read from --config, a
single source of truth shared with build_lesion_matrix.py/check_lesion_quality.py.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.build_config import load_build_matrix_config
from src.features.lesion import KNOWN_LESION_SIDES, compute_lesion_laterality_metrics, lesion_side_from_laterality_index
from src.utils.logging_setup import attach_file_handler, log_duration

REPORTS_ROOT = Path("summaries") / "calibrate_lesion_side_threshold"
LOGS_ROOT = Path("logs") / "calibrate_lesion_side_threshold"
REPORT_FILENAME_PREFIX = "calibrate_lesion_side_threshold_summary"

KNOWN_SIDES = KNOWN_LESION_SIDES
LITERATURE_DEFAULT_THRESHOLD = 0.2
# Grid searched around the literature default - fine enough to see the accuracy curve's
# real shape, not so fine it implies a false precision the underlying data doesn't support.
THRESHOLD_GRID = np.round(np.arange(0.0, 0.61, 0.02), 2)


@dataclass(frozen=True)
class ThresholdResult:
    threshold: float
    accuracy: float
    n_correct: int
    n_total: int
    confusion: pd.DataFrame  # rows=true side, columns=predicted side


def evaluate_threshold(merged: pd.DataFrame, threshold: float) -> ThresholdResult:
    predicted = merged["laterality_index"].map(lambda li: lesion_side_from_laterality_index(li, threshold))
    correct = predicted == merged["lesion_side"]
    confusion = pd.crosstab(merged["lesion_side"], predicted, dropna=False).reindex(
        index=KNOWN_SIDES, columns=KNOWN_SIDES, fill_value=0
    )
    return ThresholdResult(
        threshold=threshold,
        accuracy=correct.mean(),
        n_correct=int(correct.sum()),
        n_total=len(merged),
        confusion=confusion,
    )


def load_ground_truth(participants_path: Path, datasets: list[str]) -> pd.DataFrame:
    """subject_id/dataset/lesion_side for every subject with a clinically-sourced
    lesion_side, restricted to `datasets`. Raises if a requested dataset has zero
    clinical labels at all - that dataset shouldn't have been passed to --datasets."""
    participants = pd.read_csv(participants_path, dtype=str)
    for column in ("subject_id", "dataset", "lesion_side", "lesion_side_source"):
        if column not in participants.columns:
            raise ValueError(f"{participants_path}: missing required column {column!r}")

    in_scope = participants[participants["dataset"].isin(datasets)]
    labelled = in_scope[in_scope["lesion_side_source"] == "clinical"]
    unknown_sides = sorted(set(labelled["lesion_side"]) - set(KNOWN_SIDES))
    if unknown_sides:
        raise ValueError(f"{participants_path}: unexpected lesion_side value(s) {unknown_sides}, expected {KNOWN_SIDES}")

    per_dataset = labelled.groupby("dataset").size()
    empty = [d for d in datasets if per_dataset.get(d, 0) == 0]
    if empty:
        raise ValueError(f"no clinically-sourced lesion_side found for dataset(s) {empty} in {participants_path}")

    return labelled[["subject_id", "dataset", "lesion_side"]].reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Calibrate the bilaterality threshold for a future geometric lesion_side, "
        "against clinical labels already in participants.csv."
    )
    parser.add_argument("--config", required=True, help="Path to a build_lesion_matrix.json-shaped config")
    parser.add_argument(
        "--datasets", required=True, nargs="+",
        help="Datasets to calibrate on (overrides --config's own 'datasets' for this run) - "
        "every one of them must have clinically-sourced lesion_side in --participants-path",
    )
    parser.add_argument("--participants-path", default="assets/metadata/participants.csv")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    now = datetime.now()

    try:
        try:
            config = load_build_matrix_config(args.config)
            ground_truth = load_ground_truth(Path(args.participants_path), args.datasets)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        try:
            LOGS_ROOT.mkdir(parents=True, exist_ok=True)
            attach_file_handler(LOGS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log")
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        logging.info("computing laterality_index for %s (this reads/resamples every lesion mask - can take minutes)", args.datasets)
        try:
            metadata, excluded_by_group = compute_lesion_laterality_metrics(
                data_root=config.data_root,
                datasets=args.datasets,
                reference_template_path=config.reference_template_path,
                lesion_glob=config.lesion_glob,
                binarize_threshold=config.binarize_threshold,
                resample_interpolation=config.resample_interpolation,
                group_filter=config.group_filter,
            )
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1
        if excluded_by_group:
            logging.info("%d subject(s) excluded by group_filter=%s", len(excluded_by_group), config.group_filter)

        merged = ground_truth.merge(metadata, on=["subject_id", "dataset"], how="inner")
        unmatched = sorted(set(ground_truth["subject_id"]) - set(merged["subject_id"]))
        if unmatched:
            raise ValueError(
                f"{len(unmatched)} labelled subject(s) not found among computed masks (e.g. {unmatched[:5]}) - "
                "participants.csv and the disk are out of sync, see docs/dev/metadata.md"
            )

        undefined = merged["laterality_index"].isna()
        if undefined.any():
            logging.warning(
                "%d subject(s) have an undefined laterality_index (zero lesion voxels on both sides of the "
                "midline) and are excluded from calibration: %s",
                undefined.sum(), sorted(merged.loc[undefined, "subject_id"]),
            )
        merged = merged.loc[~undefined].reset_index(drop=True)

        results = [evaluate_threshold(merged, t) for t in THRESHOLD_GRID]
        best = max(results, key=lambda r: r.accuracy)
        literature = next(r for r in results if abs(r.threshold - LITERATURE_DEFAULT_THRESHOLD) < 1e-9)

        try:
            report_path = _write_report(config, args.datasets, merged, results, best, literature, now)
        except OSError as exc:
            logging.error("cannot write report: %s", exc, exc_info=True)
            return 1

        logging.info(
            "done - %d subject(s) calibrated on, best threshold=%.2f (accuracy=%.3f), "
            "literature default=%.2f (accuracy=%.3f), report written to %s",
            len(merged), best.threshold, best.accuracy, literature.threshold, literature.accuracy, report_path,
        )
        return 0
    finally:
        log_duration(now)


def _dataframe_to_markdown(df: pd.DataFrame) -> list[str]:
    """Plain markdown table, no external dependency (tabulate isn't in environment.yml -
    not worth adding for one one-off report's tables)."""
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    separator = "|" + "|".join(["---"] * len(df.columns)) + "|"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return [header, separator, *rows]


def _write_report(
    config, datasets: list[str], merged: pd.DataFrame, results: list[ThresholdResult],
    best: ThresholdResult, literature: ThresholdResult, now: datetime,
) -> Path:
    lines = [
        f"# calibrate_lesion_side_threshold — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"datasets: {datasets}",
        f"subjects with a usable clinical label + computable laterality_index: {len(merged)}",
        f"ground-truth label distribution: {merged['lesion_side'].value_counts().to_dict()}",
        "",
        "## Accuracy vs. threshold",
        "",
        "| threshold | accuracy | correct/total |",
        "|---|---|---|",
    ]
    for r in results:
        marker = " *(literature default)*" if r is literature else (" *(best)*" if r is best else "")
        lines.append(f"| {r.threshold:.2f}{marker} | {r.accuracy:.3f} | {r.n_correct}/{r.n_total} |")

    for label, result in (("Literature default (|LI| < 0.2)", literature), ("Best on this data", best)):
        lines += [
            "",
            f"## Confusion matrix — {label}, threshold={result.threshold:.2f}",
            "",
            "rows = clinical label, columns = geometric prediction",
            "",
            *_dataframe_to_markdown(result.confusion.reset_index().rename(columns={"lesion_side": "true \\ predicted"})),
        ]

    lines += [
        "",
        "## Per-subject laterality_index (first 20 rows, for spot-checking)",
        "",
        *_dataframe_to_markdown(
            merged[["subject_id", "dataset", "lesion_side", "left_voxels", "right_voxels", "laterality_index"]].head(20)
        ),
    ]

    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(lines) + "\n")
    return report_path


if __name__ == "__main__":
    raise SystemExit(main())
