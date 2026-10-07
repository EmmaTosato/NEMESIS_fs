"""CLI entry point: every per-subject metric derivable from a lesion mask, for every subject
that has one, cached to assets/metadata/lesion_metadata.csv.

Where this file sits among the metadata sources (see docs/dev/metadata.md):

- src/pipeline/populate_metadata.py writes WHO EXISTS into assets/metadata/participants.csv.
- this pipeline writes WHAT THE MASKS MEASURE into assets/metadata/lesion_metadata.csv, a
  separate file. It is deliberately agnostic of anything clinical: it never opens a
  participants.tsv and knows nothing about age, NIHSS or a clinically-recorded lesion side.
- src/pipeline/enrich_metadata.py then JOINS the two (plus the raw clinical tsvs) into
  participants.csv. It reads this CSV and no lesion mask of its own.

Per grid it writes the volume, the out-of-brain fraction and the laterality/side; on the one grid
named by `location.grid` (2mm) it also writes where the lesion sits - the dominant category and
the fraction in each of seven anatomical categories (src/features/lesion_location.py).

Every subject with a discoverable mask is measured - no exclusion threshold is applied here.
Which subjects to drop from an analysis is decided by looking at this file's distributions
(notebooks/exploration/lesion_analysis.ipynb) and written by hand into
assets/metadata/excluded_subjects.csv, the one list both matrix pipelines read.

Usage:
    conda activate nemesis
    python -m src.pipeline.compute_lesion_metadata --config config/pipelines/compute_lesion_metadata.json

`overwrite` (config) recomputes and replaces an existing CSV. With overwrite=false an existing
file is left untouched and the run exits immediately (0): the computation costs one mask read
plus one resampling per grid for the whole cohort, and this script is meant to be safe to
invoke repeatedly without re-paying that by accident. `--dry-run` validates the config, opens
nothing and writes only the report.

Alongside the CSV it writes <output>.config.json, the exact resolved config of the run that
produced it - a CSV whose grids/threshold/correction settings are unknown is not
interpretable, and this pipeline's output has no per-run directory to record them in
(lessons_learned.md #18/#36: a config file is only evidence of a run when it was written by
that run).
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

from src.analysis.build_config import LesionMetadataConfig, load_compute_lesion_metadata_config
from src.features.lesion import compute_lesion_metadata
from src.features.lesion_location import LOCATION_CATEGORIES
from src.utils.logging_setup import attach_file_handler, log_duration

REPORTS_ROOT = Path("summaries") / "compute_lesion_metadata"
LOGS_ROOT = Path("logs") / "compute_lesion_metadata"
REPORT_FILENAME_PREFIX = "compute_lesion_metadata_summary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute every mask-derived per-subject metric, on every configured grid, into a CSV."
    )
    parser.add_argument("--config", required=True, help="Path to a compute_lesion_metadata.json config")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the config and write the report, but open no mask and write no CSV",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    now = datetime.now()
    try:
        try:
            config = load_compute_lesion_metadata_config(args.config)
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
            logging.info("dry-run - no mask opened, nothing written to %s, report at %s",
                         config.output_path, report_path)
            return 0

        try:
            metadata, excluded_by_group = compute_lesion_metadata(
                data_root=config.data_root,
                datasets=config.datasets,
                lesion_glob=config.lesion_glob,
                binarize_threshold=config.binarize_threshold,
                resample_interpolation=config.resample_interpolation,
                group_filter=config.group_filter,
                grids=config.grids,
                correct_out_of_brain=config.correct_out_of_brain,
                side_threshold=config.side_threshold,
                location=config.location,
            )
        except (FileNotFoundError, ValueError, nib.filebasedimages.ImageFileError) as exc:
            # ImageFileError: a truncated/corrupt .nii.gz among the masks - same handling as
            # build_lesion_matrix.py, a clean logged error instead of a raw traceback.
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
    """Atomic write (temp file + os.replace, same convention as src/pipeline/populate_metadata.py's
    write_table) - a crash never leaves a half-written CSV, which the overwrite check above, the
    notebook, or enrich_metadata would otherwise read as a genuine complete cache."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_path.name}_tmp_", dir=output_path.parent)
    os.close(fd)
    try:
        metadata.to_csv(tmp_name, index=False)
        os.replace(tmp_name, output_path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _config_payload(config: LesionMetadataConfig) -> dict[str, object]:
    """The resolved config as plain JSON types - Path/dataclass reprs are unreadable in a file
    meant to be diffed against a later run's own."""
    return {
        "project": config.project,
        "data_root": str(config.data_root),
        "datasets": config.datasets,
        "group_filter": config.group_filter,
        "lesion_glob": config.lesion_glob,
        "binarize_threshold": config.binarize_threshold,
        "resample_interpolation": config.resample_interpolation,
        "grids": {
            grid.name: {
                "reference_template_path": str(grid.reference_template_path),
                "brain_mask_path": str(grid.brain_mask_path),
            }
            for grid in config.grids
        },
        "correct_out_of_brain": config.correct_out_of_brain,
        "side_threshold": config.side_threshold,
        "location": {
            "grid": config.location.grid,
            "atlases": {
                name: {"image_path": str(atlas.image_path), "labels_path": str(atlas.labels_path)}
                for name, atlas in (
                    ("cortical", config.location.cortical),
                    ("subcortical", config.location.subcortical),
                    ("cerebellum", config.location.cerebellum),
                )
            },
        },
        "run_notes": config.run_notes,
    }


def _write_run_config(config: LesionMetadataConfig, output_path: Path, now: datetime) -> Path:
    """<output>.config.json, next to the CSV: what this exact CSV was computed with."""
    config_path = output_path.with_suffix(".config.json")
    payload = {"written": now.strftime("%d-%m-%y %H:%M:%S"), **_config_payload(config)}
    config_path.write_text(json.dumps(payload, indent=2) + "\n")
    return config_path


# --- report ----------------------------------------------------------------------------------


def _grid_report_lines(metadata: pd.DataFrame, grid_name: str) -> list[str]:
    """One grid's distribution summary: enough to see at a glance whether the run is sane, not a
    substitute for the notebook's own analysis of the same columns."""
    volumes = metadata[f"lesion_volume_voxels_{grid_name}"]
    fractions = metadata[f"out_of_brain_fraction_{grid_name}"]
    sides = metadata[f"lesion_side_{grid_name}"]
    side_counts = ", ".join(f"{side}={count}" for side, count in sides.value_counts().sort_index().items())
    return [
        "",
        f"### {grid_name}",
        "",
        f"- volume (voxel): min={int(volumes.min())} · mediana={volumes.median():.0f} · max={int(volumes.max())}",
        f"- maschere vuote (volume = 0): {int((volumes == 0).sum())}",
        f"- frazione fuori dal brain: min={fractions.min():.4f} · mediana={fractions.median():.4f} · "
        f"max={fractions.max():.4f} (calcolata sulla maschera grezza, prima dell'eventuale azzeramento)",
        f"- lato: {side_counts or '—'} · senza lato (indice indefinito): {int(sides.isna().sum())}",
    ]


def _location_report_lines(metadata: pd.DataFrame, grid_name: str) -> list[str]:
    """How many lesions each category is dominant for, and the mean fraction per category: enough
    to see at a glance that the categories are populated as expected, not an analysis."""
    dominant = metadata[f"location_dominant_{grid_name}"]
    lines = [
        "",
        f"## Sede della lesione ({grid_name})",
        "",
        f"senza sede (maschera vuota o tutta fuori dal brain): {int(dominant.isna().sum())}",
        "",
        "| categoria | dominante per | frazione media |",
        "|---|---|---|",
    ]
    for category in LOCATION_CATEGORIES:
        fraction = metadata[f"location_{category}_{grid_name}"].mean()
        lines.append(f"| {category} | {int((dominant == category).sum())} | {fraction:.3f} |")
    return lines


def _report_lines(
    config: LesionMetadataConfig, metadata: pd.DataFrame | None, excluded_by_group: list[str], now: datetime
) -> list[str]:
    lines = [
        f"# compute_lesion_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"output: `{config.output_path}`" + ("" if metadata is None else f" ({len(metadata)} righe)"),
        f"griglie: {', '.join(grid.name for grid in config.grids)} · "
        f"correct_out_of_brain: {config.correct_out_of_brain} · side_threshold: {config.side_threshold} · "
        f"sede misurata su: {config.location.grid}",
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
        return lines + ["", "## Dry run", "", "Config validato, nessuna maschera aperta, nessun CSV scritto."]

    lines += ["", "## Soggetti per dataset", "", "| dataset | soggetti |", "|---|---|"]
    for name, count in metadata["dataset"].value_counts().sort_index().items():
        lines.append(f"| {name} | {int(count)} |")

    lines += ["", "## Metriche per griglia"]
    for grid in config.grids:
        lines += _grid_report_lines(metadata, grid.name)
    lines += _location_report_lines(metadata, config.location.grid)

    lines += ["", "## Esclusi da group_filter", ""]
    if excluded_by_group:
        lines.append(f"{len(excluded_by_group)} soggetto/i esclusi (group_filter={config.group_filter}):")
        lines += [f"- {subject_id}" for subject_id in excluded_by_group]
    else:
        lines.append("Nessuno.")
    return lines


def _write_report(
    config: LesionMetadataConfig, metadata: pd.DataFrame | None, excluded_by_group: list[str], now: datetime
) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(_report_lines(config, metadata, excluded_by_group, now)) + "\n")
    return report_path


if __name__ == "__main__":
    raise SystemExit(main())
