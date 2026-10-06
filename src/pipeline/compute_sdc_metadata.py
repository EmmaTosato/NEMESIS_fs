"""CLI entry point: how disconnected each subject is, overall, for every subject that has SDC
output, cached to assets/metadata/sdc_metadata.csv.

Where this file sits among the metadata sources (see docs/dev/metadata.md): it is the
disconnection counterpart of assets/metadata/lesion_metadata.csv.

- src/pipeline/populate_metadata.py writes WHO EXISTS into assets/metadata/participants.csv.
- src/pipeline/compute_lesion_metadata.py writes WHAT THE LESION MASKS MEASURE.
- this pipeline writes WHAT THE DISCONNECTOME MAPS MEASURE into assets/metadata/sdc_metadata.csv,
  a separate file, agnostic of anything clinical.
- src/pipeline/enrich_metadata.py then JOINS it into participants.csv (config.sdc_metadata). It
  reads this CSV and no disconnectome of its own.

Two columns per subject and per grid (src.features.sdc.compute_sdc_metadata): the summed disconnection
probability inside the brain (disconnection_load_voxels_<grid>) and that sum over the number of
brain voxels (disconnection_mean_<grid>). Every subject the registry flags as having SDC output
is measured - no exclusion is applied here; which subjects to drop from an analysis is decided
downstream, in assets/metadata/excluded_subjects.csv.

Usage:
    conda activate nemesis
    python -m src.pipeline.compute_sdc_metadata --config config/pipelines/compute_sdc_metadata.json

`overwrite` (config) recomputes and replaces an existing CSV. With overwrite=false an existing
file is left untouched and the run exits immediately (0): the computation reads and resamples
one 1mm map per subject for the whole cohort, and this script is meant to be safe to invoke
repeatedly without re-paying that by accident. `--dry-run` validates the config, opens nothing
and writes only the report.

Alongside the CSV it writes <output>.config.json, the exact resolved config of the run that
produced it - a CSV whose grid/interpolation settings are unknown is not interpretable, and
this pipeline's output has no per-run directory to record them in (lessons_learned.md #18/#36:
a config file is only evidence of a run when it was written by that run).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

import nibabel as nib
import pandas as pd

from src.analysis.build_config import SdcMetadataConfig, load_compute_sdc_metadata_config
from src.features.sdc import DISCONNECTION_LOAD_PREFIX, DISCONNECTION_MEAN_PREFIX, compute_sdc_metadata
from src.utils.logging_setup import attach_file_handler, log_duration

REPORTS_ROOT = Path("summaries") / "compute_sdc_metadata"
LOGS_ROOT = Path("logs") / "compute_sdc_metadata"
REPORT_FILENAME_PREFIX = "compute_sdc_metadata_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute every subject's overall disconnection from its disconnectome map into a CSV."
    )
    parser.add_argument("--config", required=True, help="Path to a compute_sdc_metadata.json config")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the config and write the report, but open no map and write no CSV",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    now = datetime.now()
    try:
        try:
            config = load_compute_sdc_metadata_config(args.config)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            logging.error(str(exc))
            return 1

        if config.output_path.is_file() and not config.overwrite:
            logging.info(
                "%s already exists and 'overwrite' is false in %s - nothing to do (set overwrite=true "
                "to recompute and replace it)",
                config.output_path, args.config,
            )
            return 0

        try:
            log_path = LOGS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log"
            LOGS_ROOT.mkdir(parents=True, exist_ok=True)
            attach_file_handler(log_path)
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        if args.dry_run:
            try:
                report_path = _write_report(config, metadata=None, excluded_by_group=[], now=now)
            except OSError as exc:
                logging.error("cannot write output: %s", exc, exc_info=True)
                return 1
            logging.info("dry-run - no map opened, nothing written to %s, report at %s",
                         config.output_path, report_path)
            return 0

        try:
            metadata, excluded_by_group = compute_sdc_metadata(
                data_root=config.data_root,
                datasets=config.datasets,
                disconnectome_glob=config.disconnectome_glob,
                resample_interpolation=config.resample_interpolation,
                group_filter=config.group_filter,
                grids=config.grids,
            )
        except (FileNotFoundError, ValueError, nib.filebasedimages.ImageFileError) as exc:
            # ImageFileError: a truncated/corrupt .nii.gz among the maps - same handling as
            # compute_lesion_metadata.py, a clean logged error instead of a raw traceback.
            logging.error(str(exc))
            return 1

        if excluded_by_group:
            logging.info(
                "%d subject(s) excluded by group_filter=%s: %s",
                len(excluded_by_group), config.group_filter, excluded_by_group,
            )

        try:
            _write_csv(metadata, config.output_path)
            config_path = _write_run_config(config, config.output_path, now)
            report_path = _write_report(config, metadata, excluded_by_group, now)
        except OSError as exc:
            logging.error("cannot write output: %s", exc, exc_info=True)
            return 1

        logging.info(
            "done - %d subject(s) written to %s (config at %s), report written to %s, log written to %s",
            len(metadata), config.output_path, config_path, report_path, log_path,
        )
        return 0
    finally:
        log_duration(now)


# --- writing ---------------------------------------------------------------------------------


def _write_csv(metadata: pd.DataFrame, output_path: Path) -> None:
    """Atomic write (temp file + os.replace, same convention as compute_lesion_metadata.py) - a
    crash never leaves a half-written CSV, which the overwrite check above or enrich_metadata
    would otherwise read as a genuine complete cache."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_path.name}_tmp_", dir=output_path.parent)
    os.close(fd)
    try:
        metadata.to_csv(tmp_name, index=False)
        os.replace(tmp_name, output_path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _config_payload(config: SdcMetadataConfig) -> dict[str, object]:
    """The resolved config as plain JSON types - Path/dataclass reprs are unreadable in a file
    meant to be diffed against a later run's own."""
    return {
        "project": config.project,
        "data_root": str(config.data_root),
        "datasets": config.datasets,
        "group_filter": config.group_filter,
        "disconnectome_glob": config.disconnectome_glob,
        "resample_interpolation": config.resample_interpolation,
        "grids": {
            grid.name: {
                "reference_template_path": str(grid.reference_template_path),
                "brain_mask_path": str(grid.brain_mask_path),
            }
            for grid in config.grids
        },
        "run_notes": config.run_notes,
    }


def _write_run_config(config: SdcMetadataConfig, output_path: Path, now: datetime) -> Path:
    """<output>.config.json, next to the CSV: what this exact CSV was computed with."""
    config_path = output_path.with_suffix(".config.json")
    payload = {"written": now.strftime("%d-%m-%y %H:%M:%S"), **_config_payload(config)}
    config_path.write_text(json.dumps(payload, indent=2) + "\n")
    return config_path


# --- report ----------------------------------------------------------------------------------


def _distribution_report_lines(metadata: pd.DataFrame, grid_name: str) -> list[str]:
    """Enough to see at a glance whether the run is sane, not a substitute for analysing the
    same columns."""
    load = metadata[f"{DISCONNECTION_LOAD_PREFIX}_{grid_name}"]
    mean = metadata[f"{DISCONNECTION_MEAN_PREFIX}_{grid_name}"]
    return [
        f"- carico (somma delle probabilità, voxel): min={load.min():.0f} · mediana={load.median():.0f} · "
        f"max={load.max():.0f}",
        f"- media sul cervello (0-1): min={mean.min():.4f} · mediana={mean.median():.4f} · max={mean.max():.4f}",
        f"- soggetti con carico = 0: {int((load == 0).sum())}",
    ]


def _report_lines(
    config: SdcMetadataConfig, metadata: pd.DataFrame | None, excluded_by_group: list[str], now: datetime
) -> list[str]:
    lines = [
        f"# compute_sdc_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"output: `{config.output_path}`" + ("" if metadata is None else f" ({len(metadata)} righe)"),
        f"griglie: {', '.join(grid.name for grid in config.grids)} · interpolazione: {config.resample_interpolation} · "
        f"group_filter: {config.group_filter}",
        "",
        "config:",
        "```json",
        json.dumps(_config_payload(config), indent=2),
        "```",
        "",
        f"notes: {config.run_notes}",
    ]
    if metadata is None:
        return lines + ["", "## Dry run", "", "Config validato, nessuna mappa aperta, nessun CSV scritto."]

    lines += ["", "## Soggetti per dataset", "", "| dataset | soggetti |", "|---|---|"]
    for name, count in metadata["dataset"].value_counts().sort_index().items():
        lines.append(f"| {name} | {int(count)} |")

    for grid in config.grids:
        lines += ["", f"## Distribuzione ({grid.name})", ""]
        lines += _distribution_report_lines(metadata, grid.name)

    lines += ["", "## Esclusi da group_filter", ""]
    if excluded_by_group:
        lines.append(f"{len(excluded_by_group)} soggetto/i esclusi (group_filter={config.group_filter}):")
        lines += [f"- {subject_id}" for subject_id in excluded_by_group]
    else:
        lines.append("Nessuno.")
    return lines


def _write_report(
    config: SdcMetadataConfig, metadata: pd.DataFrame | None, excluded_by_group: list[str], now: datetime
) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(_report_lines(config, metadata, excluded_by_group, now)) + "\n")
    return report_path


if __name__ == "__main__":
    raise SystemExit(main())
