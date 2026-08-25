"""CLI entry point: build an enriched clinical metadata table from an existing subject_id/
dataset metadata table, by joining assets/metadata/*_participants_lesions.tsv - plus,
optionally, a freshly recomputed lesion_volume_voxels.

Usage:
    conda activate nemesis
    python -m src.pipeline.enrich_lesion_metadata --config config/pipelines/enrich_lesion_metadata.json

`metadata_path` (any CSV with subject_id/dataset columns - typically, but not necessarily,
a build_lesion_matrix.py output's own metadata.csv) is read-only, never mutated: the
enriched result always lands in a brand-new `output_root/<dd-mm>_<session_name>` directory,
the same input->output separation as every other pipeline in this repo.

compute_volume=true sums the matrix.npy that src.utils.artifacts.save_matrix always writes
right next to metadata_path's own metadata.csv - deliberately only for a strictly binary
matrix (raises otherwise, with no fallback: this tool never re-derives lesion_volume_voxels
from raw lesion masks - see _refresh_lesion_volume).

lesion_side and NIHSS are joined to match the exact column name/missing-value convention
every existing results/lesion/dim_reduction/**/metadata.csv already uses (lesion_side: the
"unknown" string sentinel, never NaN - src.features.clinical.join_lesion_side; NIHSS: renamed
to "nihss" on output, src.features.clinical.join_nihss's own convention) - not the generic
join_participant_variables path every other requested variable goes through. This matters
concretely, not just cosmetically: embedding_coloring.py's categorical color mode sorts
lesion_side as plain strings (pd.unique + sorted()) - a NaN mixed in would raise TypeError,
so a generic join (which has no per-variable missing-value convention) would silently corrupt
this specific column for any dataset with a structural gap (e.g. PASPORT has no lesion_side
column at all).

Always builds and writes a full coverage report first - which datasets/subjects/variables
are covered, which aren't - to summaries/enrich_lesion_metadata/ and to the log, before
writing anything (src.features.clinical.check_participant_variable_coverage). Only writes
the output artifact if every dataset in scope has a participants.tsv file AND every subject
has a row in it (both hard requirements - report.has_hard_failures); a variable missing from
one dataset's own tsv (a known structural gap, e.g. PASPORT has no baseline NIHSS) is not a
hard failure - every subject in that dataset gets NaN (or "unknown" for lesion_side),
reported but not blocking. --dry-run runs the same checks/report without writing anything.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.build_config import EnrichLesionMetadataConfig, load_enrich_lesion_metadata_config
from src.features.clinical import (
    VariableCoverageReport,
    check_participant_variable_coverage,
    join_lesion_side,
    join_participant_variables,
)
from src.utils.artifacts import MANIFEST_FILENAME, MATRIX_FILENAME, METADATA_FILENAME, README_FILENAME
from src.utils.logging_setup import attach_file_handler, log_duration
from src.utils.run_log import append_run_log_entry

# lesion_side has its own established join (join_lesion_side, "unknown" sentinel) reused as-is
# rather than through the generic joiner - see module docstring for why this isn't optional.
_LESION_SIDE_VARIABLE = "lesion_side"

# The tsv's own column is "NIHSS" (uppercase); every metadata.csv this repo has ever written
# names it "nihss" (src.features.clinical.join_nihss's own convention) - config.variables
# spells it "NIHSS" (the real tsv column, so the coverage report checks the right name), the
# written output is renamed to match.
_OUTPUT_COLUMN_RENAME = {"NIHSS": "nihss"}

REPORTS_ROOT = Path("summaries") / "enrich_lesion_metadata"
LOGS_ROOT = Path("logs") / "enrich_lesion_metadata"
REPORT_FILENAME_PREFIX = "enrich_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an enriched clinical metadata table from an existing subject_id/dataset "
        "metadata table, joining assets/metadata/*.tsv."
    )
    parser.add_argument("--config", required=True, help="Path to an enrich_lesion_metadata.json file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Build and write the coverage report only - never write an output artifact"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_enrich_lesion_metadata_config(args.config)
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

        try:
            metadata = _read_metadata(config.metadata_path)
        except (FileNotFoundError, ValueError) as exc:
            logging.error(str(exc))
            return 1

        if config.compute_volume:
            try:
                metadata = _refresh_lesion_volume(config.metadata_path, metadata)
            except (FileNotFoundError, ValueError) as exc:
                logging.error(str(exc))
                return 1
            logging.info("lesion_volume_voxels recomputed from %s", config.metadata_path.parent / MATRIX_FILENAME)

        try:
            report = check_participant_variable_coverage(metadata, config.variables)
        except ValueError as exc:
            logging.error(str(exc))
            return 1

        try:
            report_path = _write_report(config, report, now)
        except OSError as exc:
            logging.error("cannot write coverage report: %s", exc, exc_info=True)
            return 1
        logging.info("coverage report written to %s", report_path)

        if report.has_hard_failures:
            logging.error(
                "coverage check failed - %d dataset(s) with no participants.tsv, %d dataset(s) with "
                "unresolvable subject(s); see %s for the full detail. Nothing written.",
                len(report.missing_dataset_files),
                len(report.missing_subjects_by_dataset),
                report_path,
            )
            return 1

        for dataset, missing in sorted(report.missing_variable_by_dataset.items()):
            fallback_by_variable = {v: ("'unknown'" if v == _LESION_SIDE_VARIABLE else "NaN") for v in missing}
            logging.warning(
                "%s: not in this dataset's participants.tsv, will be filled per-variable: %s",
                dataset, fallback_by_variable,
            )

        if args.dry_run:
            logging.info("--dry-run: coverage check passed, nothing written")
            return 0

        try:
            metadata_out = _join_variables(metadata, config.variables)
        except (FileNotFoundError, ValueError) as exc:
            # Re-derives the same checks check_participant_variable_coverage already ran - only
            # reachable here if the tsv files changed between the report above and this call.
            logging.error("join failed after a clean coverage report - tsv files changed mid-run? %s", exc)
            return 1

        output_dir = _output_dir(config, now)
        try:
            _write_artifact(output_dir, metadata_out, config, now, overwrite=config.overwrite)
        except (FileExistsError, OSError) as exc:
            logging.error(str(exc))
            return 1
        logging.info("enriched metadata written to %s (%d subjects, columns %s)", output_dir, len(metadata_out), list(metadata_out.columns))

        try:
            append_run_log_entry(
                config.output_root,
                config.session_name,
                now,
                "production",
                {"compute_volume": config.compute_volume, "variables": config.variables},
                output_dir,
                config.run_notes,
                config.metadata_path,
            )
        except OSError as exc:
            logging.error("cannot write run log: %s", exc, exc_info=True)
            return 1

        logging.info("done - output written to %s, report written to %s, log written to %s", output_dir, report_path, log_path)
        return 0
    finally:
        log_duration(now)


def _read_metadata(metadata_path: Path) -> pd.DataFrame:
    if not metadata_path.is_file():
        raise FileNotFoundError(f"metadata_path not found: {metadata_path}")
    metadata = pd.read_csv(metadata_path)
    if "subject_id" not in metadata.columns or "dataset" not in metadata.columns:
        raise ValueError(
            f"{metadata_path} has no 'subject_id'/'dataset' column(s) - got {list(metadata.columns)}"
        )
    return metadata


def _refresh_lesion_volume(metadata_path: Path, metadata: pd.DataFrame) -> pd.DataFrame:
    """Sums matrix.npy (src.utils.artifacts.MATRIX_FILENAME) sitting next to metadata_path -
    the exact same file/row order src.utils.artifacts.save_matrix always writes alongside
    metadata.csv - into a copy of metadata, overwriting an already-present lesion_volume_voxels
    column rather than duplicating it.

    Raises FileNotFoundError if no matrix.npy sits there, ValueError if its row count doesn't
    match metadata's own, or if it isn't strictly binary (0/1) - a voxel count is only
    meaningful for a binary matrix, and this function never guesses at one otherwise.
    """
    matrix_path = metadata_path.parent / MATRIX_FILENAME
    if not matrix_path.is_file():
        raise FileNotFoundError(
            f"compute_volume=true but no {MATRIX_FILENAME} found next to {metadata_path} - "
            "lesion_volume_voxels needs the matrix metadata_path's metadata.csv was built alongside"
        )
    X = np.load(matrix_path)
    if X.shape[0] != len(metadata):
        raise ValueError(
            f"{matrix_path} has {X.shape[0]} rows but {metadata_path} has {len(metadata)} rows - must match"
        )
    if not np.all((X == 0) | (X == 1)):
        raise ValueError(
            f"{matrix_path} is not strictly binary (0/1) - cannot compute a real voxel count from it"
        )

    metadata_out = metadata.copy()
    metadata_out["lesion_volume_voxels"] = X.sum(axis=1, dtype=np.int64)
    return metadata_out


def _join_variables(metadata: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Joins every requested variable, routing lesion_side through its own established join
    (join_lesion_side) and renaming NIHSS->nihss on output - see this module's own docstring
    for why those two aren't just handled generically like every other variable.

    Output columns are ordered as (metadata's own columns) + (variables in the order they
    were requested, post-rename) - not however _join_variables happens to compute them
    internally (lesion_side is filled in separately from the rest) - so the result's column
    order matches config.variables regardless of that implementation detail. Matters
    concretely: matching the exact column order every existing
    results/lesion/dim_reduction/**/metadata.csv already has makes a manual merge into those
    files a straight column-append, not a reorder.
    """
    generic_variables = [v for v in variables if v != _LESION_SIDE_VARIABLE]
    metadata_out = join_participant_variables(metadata, generic_variables) if generic_variables else metadata.copy()
    if _LESION_SIDE_VARIABLE in variables:
        metadata_out[_LESION_SIDE_VARIABLE] = join_lesion_side(metadata)
    metadata_out = metadata_out.rename(columns=_OUTPUT_COLUMN_RENAME)
    ordered_variable_columns = [_OUTPUT_COLUMN_RENAME.get(v, v) for v in variables]
    return metadata_out[list(metadata.columns) + ordered_variable_columns]


def _output_dir(config: EnrichLesionMetadataConfig, now: datetime) -> Path:
    return config.output_root / f"{now.strftime('%d-%m')}_{config.session_name}"


def _config_summary(config: EnrichLesionMetadataConfig) -> dict:
    return {
        "project": config.project,
        "metadata_path": str(config.metadata_path),
        "compute_volume": config.compute_volume,
        "variables": config.variables,
        "output_root": str(config.output_root),
        "session_name": config.session_name,
        "overwrite": config.overwrite,
        "run_notes": config.run_notes,
    }


def _write_artifact(
    output_dir: Path, metadata: pd.DataFrame, config: EnrichLesionMetadataConfig, now: datetime, overwrite: bool
) -> None:
    """Atomic directory write - temp dir then rename, same all-or-nothing guarantee as
    src.utils.artifacts.save_matrix, hand-rolled here rather than reused since this artifact
    has no feature matrix (save_matrix always requires an X.npy alongside metadata.csv)."""
    if output_dir.exists() and not overwrite:
        raise FileExistsError(
            f"output directory {output_dir} already exists and overwrite=False - "
            "set overwrite=true or choose a different session_name"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}_tmp_", dir=output_dir.parent))
    try:
        metadata.to_csv(tmp_dir / METADATA_FILENAME, index=False)
        config_lines = [
            f"# {config.project} clinical metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
            "",
            "## Config",
            "",
            "```json",
            json.dumps(_config_summary(config), indent=2),
            "```",
            "",
            "## Summary",
            "",
            f"{len(metadata)} subjects, columns: {list(metadata.columns)}",
        ]
        (tmp_dir / README_FILENAME).write_text("\n".join(config_lines) + "\n")
        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "n_subjects": len(metadata),
            "columns": list(metadata.columns),
        }
        (tmp_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2))

        if output_dir.exists():  # only reachable with overwrite=True, checked above
            shutil.rmtree(output_dir)
        tmp_dir.rename(output_dir)
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


def _report_lines(config: EnrichLesionMetadataConfig, report: VariableCoverageReport, now: datetime) -> list[str]:
    lines = [
        f"# enrich_lesion_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"metadata_path: `{config.metadata_path}`",
        f"compute_volume: {config.compute_volume}",
        f"Requested variables: {config.variables}",
        "",
        "## Coverage by dataset",
        "",
        "| dataset | subjects | participants.tsv | missing subjects | missing variables |",
        "|---|---|---|---|---|",
    ]
    for dataset in report.datasets:
        tsv_status = "MISSING" if dataset in report.missing_dataset_files else "found"
        missing_subjects = report.missing_subjects_by_dataset.get(dataset, [])
        missing_vars = report.missing_variable_by_dataset.get(dataset, [])
        lines.append(
            f"| {dataset} | {report.n_subjects_by_dataset[dataset]} | {tsv_status} | "
            f"{', '.join(missing_subjects) or '—'} | {', '.join(missing_vars) or '—'} |"
        )
    lines += ["", "## Verdict", ""]
    if report.has_hard_failures:
        lines.append("**FAILED** - hard coverage problem(s) above, nothing written.")
    else:
        lines.append("**OK** - safe to join (missing-variable gaps above become NaN, not an error).")
    return lines


def _write_report(config: EnrichLesionMetadataConfig, report: VariableCoverageReport, now: datetime) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(_report_lines(config, report, now)) + "\n")
    return report_path


def _log_path(config: EnrichLesionMetadataConfig, now: datetime) -> Path:
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    return LOGS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"


if __name__ == "__main__":
    raise SystemExit(main())
