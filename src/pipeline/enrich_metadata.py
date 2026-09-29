"""CLI entry point: add clinical/demographic attributes to the project's single
participant table - what we know about each subject.

The counterpart of scripts/populate_metadata.py (which answers "who exists"):
this script writes further columns into that SAME file, assets/metadata/participants.csv.
Neither script ever destroys the other's columns. See docs/dev/metadata.md.

Usage:
    conda activate nemesis
    python -m src.pipeline.enrich_metadata --config config/pipelines/enrich_metadata.json

Where each value comes from:

- Clinical/demographic variables (age, sex, education, lesion_side, NIHSS,
  clinical_date, ...) are read from each dataset's RAW participants.tsv
  (data/clinical_connectome/metadata_tsv/, paths in
  config/registry/metadata_sources.json) - the same registry populate_metadata
  reads, so the dataset -> path mapping exists in exactly one place.
- lesion_volume_voxels and, as a fallback, lesion_side are computed fresh from
  the raw lesion masks (config.lesion_metrics, a single block shared by both -
  see below) - src.features.lesion.compute_lesion_volumes/
  compute_lesion_laterality_metrics do the actual work, the same functions
  build_lesion_matrix.py and src/pipeline/check_lesion_quality.py already share.

  Previously copied lesion_volume_voxels from a specific already-built
  lesion_matrix artifact's own metadata.csv instead, on the reasoning that
  recomputing it here would create "a second, independently-drifting
  definition of the same quantity" - reversed 28-09-26 (see
  .claude/history/methods_changelog.md): that artifact's own grid/config is
  itself just as capable of drifting from what build_lesion_matrix.json
  currently says (confirmed - 900/5721 subjects, up to 38x apart, after the
  grid moved from 1mm to 2mm and the referenced artifact didn't). One fresh
  computation, reused by every consumer, is more stable than trusting whichever
  artifact happens to be named in the config.

The join is on `original_id`, NOT on `subject_id`: a raw tsv's participant_id is
the canonical subject id for most datasets but the legacy site id for UCL-UK
("ST_UCL-UK_0001"). participants.csv already stores both, so it is the bridge -
joining on subject_id would silently match nothing for that whole dataset
(.claude/lessons_learned.md #30).

Missing values are a plain empty cell, uniformly, for every variable. This file
is a registry, not a plotting input: a consumer that needs a categorical
sentinel (e.g. "unknown" for a colour legend) applies its own on read. The one
exception carrying extra information is lesion_side_source, which records where
a lesion_side value came from - "clinical" (the raw tsv) or "geometric" (a
subject with no clinical value, filled from its own lesion mask - see
config.lesion_metrics below and knowledge/neuroimaging/lesion_laterality.md).
A clinical value is never overwritten by a geometric one.

lesion_metrics (config, optional, null disables every mask-derived metric this
run): one shared block for everything computed fresh from the lesion masks,
rather than one config field per metric (a second metric would otherwise mean
a second copy of the same data_root/reference_template_path/... path).

- `build_matrix_config`: a build_lesion_matrix.json-shaped config supplying
  data_root/datasets/reference_template_path/lesion_glob/binarize_threshold/
  resample_interpolation/brain_mask_path.
- `correct_out_of_brain`: zero lesion voxels falling outside the brain mask
  (src.features.lesion_correction.zero_out_of_brain_voxels, the same
  correction build_lesion_matrix.py's own correct_out_of_brain applies) before
  computing anything below - so a subject's lesion_volume_voxels/lesion_side
  here always matches what a production matrix built with the same setting
  would show for them, never a second, uncorrected definition of the same
  subject's lesion.
- `compute_volume`: write lesion_volume_voxels.
- `compute_side`: fill lesion_side (only where the clinical resolution above
  left it empty - a clinical value is never touched), classified from
  laterality_index = (left_voxels - right_voxels) / (left_voxels + right_voxels)
  against `side_threshold` (src.features.lesion.lesion_side_from_laterality_index)
  - calibrated 28-09-26 against 1445 clinically-labelled subjects (97.4%
  agreement at the literature-default threshold 0.20, see
  scripts/calibrate_lesion_side_threshold.py and
  .claude/history/methods_changelog.md). Requires `lesion_side` in `variables`.

No per-subject exclusion list for either metric: a value later found unreliable
in analysis is corrected by hand directly in participants.csv (a git-versioned
CSV) - `fill: true` on the next run leaves a hand-corrected cell untouched,
same as any other manually-fixed value. Simpler than a config-editing round
trip for a case-by-case judgement call that belongs in analysis, not in this
pipeline's config.

Two kinds of gap are reported and are NOT errors:
- a variable absent from one dataset's tsv entirely (structural per-dataset gap,
  e.g. UCL-UK has no NIHSS column at all) - every subject of that dataset gets
  an empty cell, logged once at WARNING;
- a per-subject blank/"n/a" cell in a dataset that does have the column.

A subject present in participants.csv but absent from its own dataset's raw tsv
IS an error: the two files disagree about who exists, which populate_metadata's
own inner join should have made impossible.

`fill` (config):
- true  - only empty cells of the requested variables are written; any value
          already present is left exactly as it is.
- false - every requested variable is recomputed for every in-scope subject.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from src.analysis.build_config import load_build_matrix_config
from src.features.lesion import compute_lesion_laterality_metrics, compute_lesion_volumes, lesion_side_from_laterality_index
from src.utils.metadata_sources import DatasetSource, load_metadata_sources
from src.utils.logging_setup import attach_file_handler, log_duration

REPORTS_ROOT = Path("summaries") / "enrich_metadata"
LOGS_ROOT = Path("logs") / "enrich_metadata"
REPORT_FILENAME_PREFIX = "enrich_summary"

# Columns this script owns. populate_metadata.py owns the rest and is never
# allowed to be overwritten from here (and vice versa).
KNOWN_VARIABLES = ("age", "sex", "education", "lesion_side", "NIHSS", "clinical_date")
LESION_SIDE_VARIABLE = "lesion_side"
LESION_SIDE_SOURCE_COLUMN = "lesion_side_source"
LESION_SIDE_SOURCE_CLINICAL = "clinical"
LESION_SIDE_SOURCE_GEOMETRIC = "geometric"
LESION_VOLUME_COLUMN = "lesion_volume_voxels"

# The only missing-value sentinel observed in the real participants.tsv files
# (verified 27/07/26); a genuinely empty field is already NaN from read_csv.
_MISSING_SENTINEL = "n/a"

# Deliberate, reviewable per-dataset substitutions: a variable read from a
# differently-named column because the canonical one does not exist for that
# cohort. Every substitution is logged at WARNING and listed in the run report -
# it is a clinical equivalence assumption, so it must never be invisible.
# PASPORT has no baseline NIHSS at all, only NIHSS_at_presentation/24H/3m
# (docs/dev/metadata.md, "Due eccezioni che enrich dovrà codificare esplicitamente").
VARIABLE_SOURCE_OVERRIDES: dict[tuple[str, str], str] = {
    ("UNIPD/PASPORT", "NIHSS"): "NIHSS_at_presentation",
}


@dataclass(frozen=True)
class LesionMetricsConfig:
    """Config for the metadata computed fresh from the lesion masks
    (docs/dev/metadata.md, knowledge/neuroimaging/lesion_laterality.md) - one
    shared mask source/correction setting, two independent per-metric flags."""

    build_matrix_config: Path
    correct_out_of_brain: bool
    compute_volume: bool
    compute_side: bool
    side_threshold: float


@dataclass(frozen=True)
class EnrichMetadataConfig:
    project: str
    sources: dict[str, DatasetSource]
    participants_path: Path
    datasets: list[str] | None
    variables: list[str]
    lesion_metrics: LesionMetricsConfig | None
    fill: bool
    run_notes: str


@dataclass(frozen=True)
class DatasetCoverage:
    """What one dataset could and could not supply, for the run report."""

    dataset: str
    n_subjects: int
    missing_variables: list[str]
    substituted: dict[str, str]
    n_missing_cells: dict[str, int]


# --- config ---------------------------------------------------------------------------------


def load_config(path: str | Path) -> EnrichMetadataConfig:
    """Load and validate an enrich_metadata.json file.

    Every field is validated before any file is read, so a typo'd variable name
    fails immediately instead of after every dataset has been parsed.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(raw).__name__}")
    for key in ("project", "metadata_sources", "participants_path", "variables", "fill", "run_notes"):
        if key not in raw:
            raise ValueError(f"{path}: missing required key {key!r}")
    if not isinstance(raw["fill"], bool):
        raise ValueError(f"{path}: 'fill' must be a boolean, got {raw['fill']!r}")

    variables = _unique_str_list(raw["variables"], "variables", path)
    if not variables:
        raise ValueError(f"{path}: 'variables' is empty - nothing to enrich")
    unknown = [v for v in variables if v not in KNOWN_VARIABLES]
    if unknown:
        raise ValueError(f"{path}: unknown variable(s) {unknown}; known: {list(KNOWN_VARIABLES)}")

    sources = load_metadata_sources(Path(raw["metadata_sources"]))
    datasets = None if raw.get("datasets") is None else _unique_str_list(raw["datasets"], "datasets", path)
    if datasets is not None:
        if not datasets:
            raise ValueError(f"{path}: 'datasets' is an empty list - use null to mean 'every dataset'")
        missing = [d for d in datasets if d not in sources]
        if missing:
            raise ValueError(f"{path}: dataset(s) not in {raw['metadata_sources']}: {missing}")

    lesion_metrics = _load_lesion_metrics_config(raw.get("lesion_metrics"), variables, path)

    return EnrichMetadataConfig(
        project=str(raw["project"]),
        sources=sources,
        participants_path=Path(str(raw["participants_path"])),
        datasets=datasets,
        variables=variables,
        lesion_metrics=lesion_metrics,
        fill=raw["fill"],
        run_notes=str(raw["run_notes"]),
    )


def _load_lesion_metrics_config(raw_block: object, variables: list[str], path: Path) -> LesionMetricsConfig | None:
    """Parse the optional 'lesion_metrics' block - null (the default) disables every
    mask-derived metric this run. Only shape/type validated here (build_matrix_config
    isn't resolved until it's actually used) - see compute_fresh_lesion_volumes/
    compute_geometric_lesion_sides for what happens with a bad path."""
    if raw_block is None:
        return None
    if not isinstance(raw_block, dict):
        raise ValueError(f"{path}: 'lesion_metrics' must be an object or null")
    for key in ("build_matrix_config", "correct_out_of_brain", "compute_volume", "compute_side", "side_threshold"):
        if key not in raw_block:
            raise ValueError(f"{path}: 'lesion_metrics' is missing required key {key!r}")

    build_matrix_config = raw_block["build_matrix_config"]
    if not isinstance(build_matrix_config, str) or not build_matrix_config:
        raise ValueError(f"{path}: 'lesion_metrics.build_matrix_config' must be a non-empty string")

    for flag_key in ("correct_out_of_brain", "compute_volume", "compute_side"):
        if not isinstance(raw_block[flag_key], bool):
            raise ValueError(f"{path}: 'lesion_metrics.{flag_key}' must be a boolean")
    compute_volume, compute_side = raw_block["compute_volume"], raw_block["compute_side"]
    if not compute_volume and not compute_side:
        raise ValueError(
            f"{path}: 'lesion_metrics' is set but both 'compute_volume' and 'compute_side' are false - "
            "nothing to compute; use null to disable the block entirely"
        )
    if compute_side and LESION_SIDE_VARIABLE not in variables:
        raise ValueError(
            f"{path}: 'lesion_metrics.compute_side' is true but {LESION_SIDE_VARIABLE!r} is not in 'variables' - "
            "the fallback has nothing to fill without it"
        )

    side_threshold = raw_block["side_threshold"]
    if (
        not isinstance(side_threshold, (int, float))
        or isinstance(side_threshold, bool)
        or not (0.0 <= side_threshold < 1.0)
    ):
        raise ValueError(f"{path}: 'lesion_metrics.side_threshold' must be a number in [0.0, 1.0)")

    return LesionMetricsConfig(
        build_matrix_config=Path(build_matrix_config),
        correct_out_of_brain=raw_block["correct_out_of_brain"],
        compute_volume=compute_volume,
        compute_side=compute_side,
        side_threshold=float(side_threshold),
    )


def _unique_str_list(value: object, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"{path}: {field!r} must be a list of non-empty strings")
    duplicates = sorted({v for v in value if value.count(v) > 1})
    if duplicates:
        raise ValueError(f"{path}: {field!r} has duplicate entrie(s): {duplicates}")
    return list(value)


# --- reading the sources --------------------------------------------------------------------


def _normalize_missing(value: object) -> object:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    return np.nan if text == "" or text == _MISSING_SENTINEL else text


def read_raw_participants(source: DatasetSource, dataset: str) -> pd.DataFrame:
    """One dataset's raw participants.tsv, indexed by its own participant_id.

    Read with dtype=str: these files carry ids with leading zeros and dates,
    both of which pandas' type inference would silently mangle.
    """
    if not source.participants_tsv.is_file():
        raise FileNotFoundError(f"{dataset}: raw participants.tsv not found at {source.participants_tsv}")
    participants = pd.read_csv(source.participants_tsv, sep="\t", dtype=str)
    if "participant_id" not in participants.columns:
        raise ValueError(
            f"{source.participants_tsv}: expected a 'participant_id' column, got {list(participants.columns)}"
        )
    duplicated = sorted(participants.loc[participants["participant_id"].duplicated(), "participant_id"])
    if duplicated:
        raise ValueError(f"{source.participants_tsv}: duplicate participant_id(s): {duplicated}")
    return participants.set_index("participant_id")


def source_column_for(dataset: str, variable: str, available: list[str]) -> str | None:
    """Which raw column supplies `variable` for `dataset` - None if that dataset
    simply doesn't have it (a structural gap, not an error).

    Resolution order: the canonical name if present, otherwise an explicitly
    registered substitution. A substitution is never guessed from a similar
    name - only VARIABLE_SOURCE_OVERRIDES' hand-written entries are honoured.
    """
    if variable in available:
        return variable
    override = VARIABLE_SOURCE_OVERRIDES.get((dataset, variable))
    if override is not None and override in available:
        return override
    return None


# --- per-dataset resolution -----------------------------------------------------------------


def resolve_dataset_values(
    dataset: str,
    source: DatasetSource,
    registry_rows: pd.DataFrame,
    variables: list[str],
) -> tuple[dict[str, dict[str, object]], DatasetCoverage]:
    """{variable: {subject_id: value}} for one dataset, plus its coverage record.

    Raises ValueError if a subject listed in participants.csv has no row in its
    own dataset's raw tsv - the two files disagreeing about who exists is a real
    inconsistency (populate_metadata's inner join should make it impossible),
    never a legitimate "missing value".
    """
    participants = read_raw_participants(source, dataset)
    available = list(participants.columns)

    unknown_ids = sorted(set(registry_rows["original_id"]) - set(participants.index))
    if unknown_ids:
        raise ValueError(
            f"{dataset}: {len(unknown_ids)} subject(s) in the registry have no row in "
            f"{source.participants_tsv} (original_id): {unknown_ids[:5]}"
        )

    values: dict[str, dict[str, object]] = {}
    missing_variables: list[str] = []
    substituted: dict[str, str] = {}
    n_missing_cells: dict[str, int] = {}

    for variable in variables:
        column = source_column_for(dataset, variable, available)
        if column is None:
            missing_variables.append(variable)
            values[variable] = {s: np.nan for s in registry_rows["subject_id"]}
            n_missing_cells[variable] = len(registry_rows)
            logging.warning(
                "dataset=%s: no %r column in %s - %d subject(s) left empty",
                dataset, variable, source.participants_tsv, len(registry_rows),
            )
            continue
        if column != variable:
            substituted[variable] = column
            logging.warning(
                "dataset=%s: %r resolved from column %r (registered substitution - a clinical "
                "equivalence assumption, see VARIABLE_SOURCE_OVERRIDES)", dataset, variable, column,
            )

        lookup = participants[column]
        per_subject = {
            row.subject_id: _normalize_missing(lookup.loc[row.original_id])
            for row in registry_rows.itertuples()
        }
        values[variable] = per_subject
        n_missing_cells[variable] = sum(1 for v in per_subject.values() if pd.isna(v))

    coverage = DatasetCoverage(
        dataset=dataset,
        n_subjects=len(registry_rows),
        missing_variables=missing_variables,
        substituted=substituted,
        n_missing_cells=n_missing_cells,
    )
    return values, coverage


def compute_fresh_lesion_volumes(
    build_matrix_config: Path, datasets: list[str], correct_out_of_brain: bool
) -> dict[str, int]:
    """lesion_volume_voxels per subject, computed fresh from the raw lesion masks -
    reuses src.features.lesion.compute_lesion_volumes (the same discovery/
    resampling/binarization/correction build_lesion_matrix.py and
    src/pipeline/check_lesion_quality.py already share), driven by a
    build_lesion_matrix.json-shaped config rather than a second,
    independently-shaped config for this one field.

    Only the intersection of `datasets` (this run's own scope) and the referenced
    config's own `datasets` (the cohorts it actually knows have masks) is computed -
    every uncovered dataset is logged at WARNING by name, whether the intersection is
    empty or just partial (regression: NEMESIS_T0 silently dropped from a real
    dry-run with zero log line naming it, 28-09-26, because the intersection wasn't
    empty overall - see .claude/history/methods_changelog.md), never raising: an
    enrich_metadata run can legitimately be scoped wider than any one
    build_lesion_matrix.json happens to cover.
    """
    matrix_config = load_build_matrix_config(build_matrix_config)
    in_scope = [d for d in datasets if d in matrix_config.datasets]
    uncovered = sorted(set(datasets) - set(in_scope))
    if uncovered:
        logging.warning(
            "lesion_metrics: dataset(s) %s are not covered by %s's own 'datasets' %s - "
            "lesion_volume_voxels left untouched for them",
            uncovered, build_matrix_config, matrix_config.datasets,
        )
    if not in_scope:
        return {}
    if correct_out_of_brain and matrix_config.brain_mask_path is None:
        raise ValueError(
            f"lesion_metrics.correct_out_of_brain is true but {build_matrix_config}'s own brain_mask_path is "
            "null - cannot zero out-of-brain voxels without a brain mask"
        )

    metadata, _ = compute_lesion_volumes(
        data_root=matrix_config.data_root,
        datasets=in_scope,
        reference_template_path=matrix_config.reference_template_path,
        lesion_glob=matrix_config.lesion_glob,
        binarize_threshold=matrix_config.binarize_threshold,
        resample_interpolation=matrix_config.resample_interpolation,
        group_filter=None,
        correct_out_of_brain=correct_out_of_brain,
        brain_mask_path=matrix_config.brain_mask_path,
    )
    return dict(zip(metadata["subject_id"], metadata[LESION_VOLUME_COLUMN].astype(int)))


def compute_geometric_lesion_sides(
    build_matrix_config: Path, datasets: list[str], threshold: float, correct_out_of_brain: bool
) -> tuple[dict[str, str], set[str]]:
    """left/right/both per subject, computed fresh from the raw lesion masks via
    src.features.lesion.compute_lesion_laterality_metrics/lesion_side_from_laterality_index
    - same discovery/resampling/correction machinery compute_fresh_lesion_volumes
    above already shares with build_lesion_matrix.py.

    Only the intersection of `datasets` (the ones that still have a subject missing
    lesion_side) and the referenced config's own `datasets` is computed - an
    enrich_metadata run can legitimately need a fallback for a dataset no
    build_lesion_matrix.json happens to cover yet. Every uncovered dataset is logged
    at WARNING by name, whether the intersection is empty or just partial - a
    dataset silently dropped from a *partial* overlap is exactly as invisible as one
    dropped from a total miss, and must be exactly as loud (same regression as
    compute_fresh_lesion_volumes above, 28-09-26, .claude/history/methods_changelog.md).

    Runs dataset-wide (every subject of `datasets`, not just the ones actually
    missing lesion_side - mask discovery has no concept of "just these subjects"),
    so a subject with an undefined laterality_index here is NOT necessarily a
    subject that still needs a value - most of the time it already has a clinical
    one. The WARNING below names every such candidate but never claims their cell
    is empty; `undefined_ids` (the second return value) lets enrich() intersect
    against its own `missing_ids` to find out which of them genuinely still lack a
    value, and log that final, precise set separately (see enrich(), and
    lessons_learned.md-style note in docs/dev/metadata.md: an aggregate/candidate
    log is not a substitute for the final per-subject state).

    Returns (computed, undefined_ids): `computed` is {subject_id: left/right/both}
    for every subject with a defined laterality_index; `undefined_ids` is every
    subject_id whose laterality_index came back NaN (zero lesion voxels on both
    sides of the midline - see compute_lesion_laterality_metrics), a legitimate,
    rare domain case, not an error.
    """
    matrix_config = load_build_matrix_config(build_matrix_config)
    in_scope = [d for d in datasets if d in matrix_config.datasets]
    uncovered = sorted(set(datasets) - set(in_scope))
    if uncovered:
        logging.warning(
            "lesion_metrics: dataset(s) %s are not covered by %s's own 'datasets' %s - "
            "lesion_side left untouched for them",
            uncovered, build_matrix_config, matrix_config.datasets,
        )
    if not in_scope:
        return {}, set()
    if correct_out_of_brain and matrix_config.brain_mask_path is None:
        raise ValueError(
            f"lesion_metrics.correct_out_of_brain is true but {build_matrix_config}'s own brain_mask_path is "
            "null - cannot zero out-of-brain voxels without a brain mask"
        )

    metadata, _ = compute_lesion_laterality_metrics(
        data_root=matrix_config.data_root,
        datasets=in_scope,
        reference_template_path=matrix_config.reference_template_path,
        lesion_glob=matrix_config.lesion_glob,
        binarize_threshold=matrix_config.binarize_threshold,
        resample_interpolation=matrix_config.resample_interpolation,
        group_filter=None,
        correct_out_of_brain=correct_out_of_brain,
        brain_mask_path=matrix_config.brain_mask_path,
    )
    undefined = metadata["laterality_index"].isna()
    undefined_ids = set(metadata.loc[undefined, "subject_id"])
    if undefined_ids:
        logging.warning(
            "lesion_metrics: %d subject(s) in %s have an undefined laterality_index (zero lesion voxels on "
            "both sides of the midline) - no geometric lesion_side computed for them (most likely already "
            "have a clinical value; see enrich()'s own 'lesion_side still empty' warning below for exactly "
            "who, if anyone, is still empty because of this): %s",
            len(undefined_ids), in_scope, sorted(undefined_ids),
        )
    computed = metadata.loc[~undefined]
    return {
        row.subject_id: lesion_side_from_laterality_index(row.laterality_index, threshold)
        for row in computed.itertuples()
    }, undefined_ids


# --- assembling the enriched table ------------------------------------------------------------


def enrich(registry: pd.DataFrame, config: EnrichMetadataConfig) -> tuple[pd.DataFrame, list[DatasetCoverage]]:
    """Add the requested columns to `registry`, returning the new table and per-dataset coverage."""
    for column in ("subject_id", "original_id", "dataset"):
        if column not in registry.columns:
            raise ValueError(f"{config.participants_path}: missing required column {column!r}")

    datasets = config.datasets if config.datasets is not None else sorted(set(registry["dataset"]))
    unknown = sorted(set(datasets) - set(registry["dataset"]))
    if unknown:
        raise ValueError(f"dataset(s) {unknown} have no row in {config.participants_path}")

    values_by_variable: dict[str, dict[str, object]] = {v: {} for v in config.variables}
    coverages: list[DatasetCoverage] = []
    for dataset in datasets:
        rows = registry.loc[registry["dataset"] == dataset, ["subject_id", "original_id"]]
        resolved, coverage = resolve_dataset_values(dataset, config.sources[dataset], rows, config.variables)
        for variable, per_subject in resolved.items():
            values_by_variable[variable].update(per_subject)
        coverages.append(coverage)
        logging.info(
            "%s: %d subject(s), missing variables=%s, substituted=%s",
            dataset, coverage.n_subjects, coverage.missing_variables or "-", coverage.substituted or "-",
        )

    out = registry.copy()
    in_scope = out["dataset"].isin(datasets)
    for variable in config.variables:
        fresh = out["subject_id"].map(values_by_variable[variable])
        out[variable] = _apply(out.get(variable), fresh, in_scope, config.fill)

    if LESION_SIDE_VARIABLE in config.variables:
        resolved_side = out[LESION_SIDE_VARIABLE].notna()
        source = pd.Series(np.nan, index=out.index, dtype=object)
        source.loc[resolved_side] = LESION_SIDE_SOURCE_CLINICAL
        out[LESION_SIDE_SOURCE_COLUMN] = _apply(
            out.get(LESION_SIDE_SOURCE_COLUMN), source, in_scope, config.fill
        )

    if config.lesion_metrics is not None:
        metrics = config.lesion_metrics

        if metrics.compute_side:
            missing = in_scope & out[LESION_SIDE_VARIABLE].isna()
            if not missing.any():
                logging.info("lesion_metrics: no in-scope subject needs a geometric lesion_side fallback")
            else:
                target_datasets = sorted(set(out.loc[missing, "dataset"]))
                computed, undefined_ids = compute_geometric_lesion_sides(
                    metrics.build_matrix_config, target_datasets, metrics.side_threshold, metrics.correct_out_of_brain
                )
                # compute_geometric_lesion_sides works dataset-wide (mask discovery has no
                # concept of "just these subjects"), so `computed` can include subjects
                # outside `missing` (already clinical) - restrict to exactly who needed it
                # before writing anything, or an already-resolved subject sharing a
                # dataset with a genuinely missing one would get overwritten too.
                missing_ids = set(out.loc[missing, "subject_id"])
                sides = {sid: side for sid, side in computed.items() if sid in missing_ids}
                # fill=True regardless of config.fill: `missing` already restricts this to
                # currently-empty cells, so this branch only ever writes into a gap the
                # clinical resolution above left behind - never a value config.fill=false's
                # full-recompute semantics would otherwise expect this branch to overwrite.
                fresh_side = out["subject_id"].map(sides)
                out[LESION_SIDE_VARIABLE] = _apply(out.get(LESION_SIDE_VARIABLE), fresh_side, in_scope, fill=True)
                fresh_source = out["subject_id"].map({sid: LESION_SIDE_SOURCE_GEOMETRIC for sid in sides})
                out[LESION_SIDE_SOURCE_COLUMN] = _apply(
                    out.get(LESION_SIDE_SOURCE_COLUMN), fresh_source, in_scope, fill=True
                )
                logging.info(
                    "lesion_metrics: %d/%d subject(s) missing lesion_side filled geometrically (threshold=%.2f)",
                    len(sides), int(missing.sum()), metrics.side_threshold,
                )
                # The final, per-subject state - not a candidate/pre-filter count like the
                # "undefined laterality_index" warning above, which can include subjects that
                # already had a clinical value and never needed filling. Split by cause so
                # "why is this subject still empty" never needs cross-referencing two warnings
                # and participants.csv by hand (found 29-09-26 while auditing this pipeline's
                # own logging - see docs/dev/metadata.md).
                still_missing_ids = missing_ids - set(sides)
                if still_missing_ids:
                    undefined_and_still_missing = sorted(still_missing_ids & undefined_ids)
                    if undefined_and_still_missing:
                        logging.warning(
                            "lesion_metrics: %d subject(s) remain without lesion_side - undefined "
                            "laterality_index (zero lesion voxels on both sides of the midline): %s",
                            len(undefined_and_still_missing), undefined_and_still_missing,
                        )
                    other_still_missing = sorted(still_missing_ids - undefined_ids)
                    if other_still_missing:
                        logging.warning(
                            "lesion_metrics: %d subject(s) remain without lesion_side - dataset not covered "
                            "by %s (no clinical value and no geometric fallback attempted): %s",
                            len(other_still_missing), metrics.build_matrix_config, other_still_missing,
                        )

        if metrics.compute_volume:
            volumes = compute_fresh_lesion_volumes(metrics.build_matrix_config, datasets, metrics.correct_out_of_brain)
            # Nullable Int64, not the float64 a plain map() produces: a subject absent from
            # the fresh computation introduces a NaN, which would promote the whole column to
            # float and write a voxel *count* as "4616.0". Int64 keeps NA and stays integral.
            fresh = out["subject_id"].map(volumes).astype("Int64")
            out[LESION_VOLUME_COLUMN] = _apply(out.get(LESION_VOLUME_COLUMN), fresh, in_scope, config.fill)
            logging.info(
                "lesion_metrics: %d/%d subject(s) matched for lesion_volume_voxels (config=%s)",
                int(fresh.notna().sum()), len(out), metrics.build_matrix_config,
            )

    return out, coverages


def _apply(existing: pd.Series | None, fresh: pd.Series, in_scope: pd.Series, fill: bool) -> pd.Series:
    """Merge freshly resolved values into an existing column, honouring `fill`.

    Out-of-scope rows (a dataset this run didn't touch) always keep whatever
    they had - a partial run never blanks a dataset it wasn't asked about.
    """
    if existing is None:
        return fresh.where(in_scope, np.nan)
    # astype(object) first: participants.csv is read with dtype=str, and pandas' "str"
    # dtype rejects a NaN assignment outright (TypeError). A re-run over an
    # already-enriched file always writes some NaN back (a subject whose value is
    # genuinely missing), so without this the second run of any variable fails while
    # the first one - when the column didn't exist yet and this branch was skipped
    # entirely - looked fine (.claude/lessons_learned.md #17).
    kept = existing.astype(object).copy()
    writable = in_scope & (existing.isna() if fill else True)
    kept.loc[writable] = fresh.loc[writable]
    return kept


def write_table(table: pd.DataFrame, output_path: Path) -> None:
    """Atomic write (temp file + os.replace) - same guarantee as populate_metadata.py:
    a crash never leaves a half-written participants file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_path.name}_tmp_", dir=output_path.parent)
    os.close(fd)
    try:
        table.to_csv(tmp_name, index=False)
        os.replace(tmp_name, output_path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


# --- report ---------------------------------------------------------------------------------


def _lesion_metrics_summary(lesion_metrics: LesionMetricsConfig | None) -> str:
    """JSON dump of lesion_metrics (or 'null'), not the dataclass's own repr() -
    the latter (e.g. "LesionMetricsConfig(build_matrix_config=PosixPath('...'), ...)")
    is illegible in a report meant to be read as a document, not a Python session."""
    if lesion_metrics is None:
        return "null"
    payload = {
        "build_matrix_config": str(lesion_metrics.build_matrix_config),
        "correct_out_of_brain": lesion_metrics.correct_out_of_brain,
        "compute_volume": lesion_metrics.compute_volume,
        "compute_side": lesion_metrics.compute_side,
        "side_threshold": lesion_metrics.side_threshold,
    }
    return json.dumps(payload, indent=2)


def report_lines(config: EnrichMetadataConfig, coverages: list[DatasetCoverage], now: datetime) -> list[str]:
    lines = [
        f"# enrich_metadata — {now.strftime('%d-%m-%y %H:%M:%S')}",
        "",
        f"file: `{config.participants_path}` · fill: {config.fill} · variables: {', '.join(config.variables)}",
        "",
        "lesion_metrics:",
        "```json",
        _lesion_metrics_summary(config.lesion_metrics),
        "```",
        "",
        f"notes: {config.run_notes}",
        "",
        "## Celle vuote per dataset e variabile",
        "",
        "| dataset | soggetti | " + " | ".join(config.variables) + " |",
        "|---" * (len(config.variables) + 2) + "|",
    ]
    for coverage in coverages:
        cells = []
        for variable in config.variables:
            n = coverage.n_missing_cells.get(variable, 0)
            cells.append("— (assente)" if variable in coverage.missing_variables else f"{n}")
        lines.append(f"| {coverage.dataset} | {coverage.n_subjects} | " + " | ".join(cells) + " |")

    substitutions = {c.dataset: c.substituted for c in coverages if c.substituted}
    if substitutions:
        lines += ["", "## Sostituzioni di colonna applicate", "",
                  "Assunzioni di equivalenza clinica registrate in `VARIABLE_SOURCE_OVERRIDES`, non dedotte:", ""]
        for dataset, mapping in substitutions.items():
            for variable, column in mapping.items():
                lines.append(f"- **{dataset}**: `{variable}` letta da `{column}`")
    return lines


def write_report(config: EnrichMetadataConfig, coverages: list[DatasetCoverage], now: datetime) -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.md"
    report_path.write_text("\n".join(report_lines(config, coverages, now)) + "\n")
    return report_path


# --- entry point ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add clinical/demographic attributes to participants.csv.")
    parser.add_argument("--config", required=True, help="Path to an enrich_metadata.json config")
    parser.add_argument("--dry-run", action="store_true", help="Run every check and write the report, but not the table")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    now = datetime.now()
    try:
        try:
            config = load_config(args.config)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            logging.error(str(exc))
            return 1

        try:
            LOGS_ROOT.mkdir(parents=True, exist_ok=True)
            attach_file_handler(LOGS_ROOT / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M-%S')}.log")
        except OSError as exc:
            logging.error("cannot set up log file: %s", exc, exc_info=True)
            return 1

        try:
            if not config.participants_path.is_file():
                raise FileNotFoundError(
                    f"{config.participants_path} not found - run scripts/populate_metadata.py first "
                    "(it creates the file this script enriches)"
                )
            registry = pd.read_csv(config.participants_path, dtype=str)
            table, coverages = enrich(registry, config)
        except (FileNotFoundError, ValueError, nib.filebasedimages.ImageFileError) as exc:
            # ImageFileError (see build_lesion_matrix.py's own handling): reachable here
            # too, from compute_fresh_lesion_volumes/compute_geometric_lesion_sides,
            # whenever config.lesion_metrics is set and a subject's .nii.gz is
            # truncated/corrupt.
            logging.error(str(exc))
            return 1

        try:
            report_path = write_report(config, coverages, now)
            if args.dry_run:
                logging.info("dry-run - nothing written to %s, report at %s", config.participants_path, report_path)
                return 0
            write_table(table, config.participants_path)
        except OSError as exc:
            logging.error("cannot write output: %s", exc, exc_info=True)
            return 1

        logging.info(
            "done - %d subject(s) in %s, report written to %s", len(table), config.participants_path, report_path
        )
        return 0
    finally:
        log_duration(now)


if __name__ == "__main__":
    raise SystemExit(main())
