"""Registry of the evaluations a clustering tuning run applies, declared in the `tuning_evaluations` block
of clustering.json (and of evaluate_clustering_tuning.json).

Same idea as src/analysis/tuning_evaluations.py (dim_reduction), for a stored clustering tuning
(src/analysis/clustering_tuning_analysis.py::ClusteringTuningRun): one EvaluationSpec per evaluation, run
right after a sweep or any time later on the stored run, through the same function (run_evaluations) - so
the functions, the settings and the results are the same either way.

- The block lists evaluations by name, under "general" (valid for every clustering method) or under the
  name of a method: {"general": [], "agglomerative": ["cophenetic_correlation", ...], "hdbscan": [...]}.
  An evaluation is only accepted under a key it applies to (EvaluationSpec.methods).
- The settings of an evaluation (a threshold, a range of k) are not in the block: they live once, by
  evaluation name, in the evaluations registry (config/registry/clustering_evaluations.json), so every
  consumer reads the same values.

Adding an evaluation = one EvaluationSpec in EVALUATIONS and one entry in the registry file.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.clustering_tuning_analysis import (
    AGGLOMERATIVE,
    DENSITY_MAP_COLUMNS,
    DENSITY_METRICS_FILE,
    DENSITY_METHODS,
    ClusteringTuningRun,
    cophenetic_table,
    dbcv_curves_figures,
    density_groups,
    density_metrics,
    dunn_table,
    jump_table,
    k_curves_figure,
    k_curves_file_name,
    k_curves_targets,
    largest_cluster_share_table,
    linkage_agreement,
    read_density_metrics,
    recomputed_internal_metrics,
)
from src.analysis.plotting import compose_clustering_tuning_title, plot_clustering_tuning_heatmaps
from src.utils.artifacts import load_matrix

GENERAL = "general"

K_CURVES = "k_curves"
COPHENETIC_CORRELATION = "cophenetic_correlation"
DENDROGRAM_JUMP = "dendrogram_jump"
LINKAGE_AGREEMENT = "linkage_agreement"
LARGEST_CLUSTER_SHARE = "largest_cluster_share"
DUNN_INDEX = "dunn_index"
DENSITY_METRICS = "density_metrics"
DBCV_CURVES = "dbcv_curves"
TUNING_HEATMAPS = "tuning_heatmaps"
INTERNAL_METRICS = "internal_metrics"

_ALL_METHODS = frozenset(CLUSTERING_METHODS)
_AGGLOMERATIVE_ONLY = frozenset({AGGLOMERATIVE})
_DENSITY_ONLY = frozenset(DENSITY_METHODS)
_RECOMPUTABLE_METHODS = frozenset({AGGLOMERATIVE, *DENSITY_METHODS})

FIGURE_DPI = 150


@dataclass
class EvaluationContext:
    """What an evaluation reads: the stored run, whether it may replace existing files, and the matrix the
    run clustered (loaded from the run's own input_path the first time an evaluation asks for it, unless the
    caller already has it)."""

    run: ClusteringTuningRun
    overwrite: bool
    _matrix: np.ndarray | None = None
    distance_cache: dict[str, np.ndarray] = field(default_factory=dict)

    def matrix(self) -> np.ndarray:
        if self._matrix is None:
            self._matrix, _, _ = load_matrix(self.run.input_path)
        return self._matrix


@dataclass(frozen=True)
class EvaluationSpec:
    methods: frozenset[str]
    validate_settings: Callable[[dict], None]
    run: Callable[[EvaluationContext, dict], list[Path]]


def refuse_existing(paths: list[Path], overwrite: bool) -> None:
    existing = [path.name for path in paths if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"already in the run folder: {existing} - set overwrite=true to replace them")


def _validate_no_settings(name: str) -> Callable[[dict], None]:
    def validate(settings: dict) -> None:
        if settings:
            raise ValueError(f"evaluations registry: {name!r} takes no settings (got {sorted(settings)})")

    return validate


def _validate_dendrogram_jump_settings(settings: dict) -> None:
    if set(settings) != {"k_range"} or not isinstance(settings["k_range"], dict):
        raise ValueError(f"evaluations registry: {DENDROGRAM_JUMP!r} needs exactly a 'k_range' object, got {settings!r}")
    k_range = settings["k_range"]
    if set(k_range) != {"min", "max"}:
        raise ValueError(f"evaluations registry: {DENDROGRAM_JUMP!r} k_range needs exactly 'min' and 'max', got {sorted(k_range)}")
    for key in ("min", "max"):
        if isinstance(k_range[key], bool) or not isinstance(k_range[key], int) or k_range[key] < 2:
            raise ValueError(f"evaluations registry: {DENDROGRAM_JUMP!r} k_range.{key} must be an integer >= 2, got {k_range[key]!r}")
    if k_range["min"] > k_range["max"]:
        raise ValueError(f"evaluations registry: {DENDROGRAM_JUMP!r} k_range.min ({k_range['min']}) is greater than k_range.max ({k_range['max']})")


def _run_k_curves(context: EvaluationContext, settings: dict) -> list[Path]:
    run = context.run
    curves = {k_curves_file_name(metric): metric for metric in k_curves_targets(run.results)}
    paths = {name: run.run_dir / name for name in curves}
    refuse_existing(list(paths.values()), context.overwrite)
    for name, metric in curves.items():
        k_curves_figure(run.results, metric).savefig(paths[name], dpi=FIGURE_DPI)
    return list(paths.values())


def _write_table(context: EvaluationContext, name: str, table: Callable[[], pd.DataFrame]) -> list[Path]:
    """Writes `table()` as <run folder>/<name>; the file is checked before the table is computed, which can be slow."""
    path = context.run.run_dir / name
    refuse_existing([path], context.overwrite)
    table().to_csv(path, index=False)
    return [path]


def _run_cophenetic_correlation(context: EvaluationContext, settings: dict) -> list[Path]:
    return _write_table(
        context, "cophenetic_correlation.csv", lambda: cophenetic_table(context.run, context.matrix(), context.distance_cache)
    )


def _run_dendrogram_jump(context: EvaluationContext, settings: dict) -> list[Path]:
    k_range = range(settings["k_range"]["min"], settings["k_range"]["max"] + 1)
    return _write_table(
        context, "dendrogram_jump.csv", lambda: jump_table(context.run, context.matrix(), k_range, context.distance_cache)
    )


def _run_linkage_agreement(context: EvaluationContext, settings: dict) -> list[Path]:
    return _write_table(context, "linkage_agreement.csv", lambda: linkage_agreement(context.run))


def _run_largest_cluster_share(context: EvaluationContext, settings: dict) -> list[Path]:
    return _write_table(context, "largest_cluster_share.csv", lambda: largest_cluster_share_table(context.run))


def _run_dunn_index(context: EvaluationContext, settings: dict) -> list[Path]:
    return _write_table(context, "dunn_index.csv", lambda: dunn_table(context.run, context.matrix()))


def _run_density_metrics(context: EvaluationContext, settings: dict) -> list[Path]:
    return _write_table(context, DENSITY_METRICS_FILE, lambda: density_metrics(context.run, context.matrix()))


def _density_figure_paths(run_dir: Path, figures: Mapping[str, object], stem: str) -> dict[str, Path]:
    """`<stem>.png` for the single figure of hdbscan (key ""), `<stem>_cluster_selection_method=<value>.png` for each of hdbscan_soft."""
    return {name: run_dir / (f"{stem}_cluster_selection_method={name}.png" if name else f"{stem}.png") for name in figures}


def _run_dbcv_curves(context: EvaluationContext, settings: dict) -> list[Path]:
    run = context.run
    figures = dbcv_curves_figures(read_density_metrics(run.run_dir))
    paths = _density_figure_paths(run.run_dir, figures, "dbcv_curves")
    refuse_existing(list(paths.values()), context.overwrite)
    for name, figure in figures.items():
        figure.savefig(paths[name], dpi=FIGURE_DPI)
    return list(paths.values())


def _run_tuning_heatmaps(context: EvaluationContext, settings: dict) -> list[Path]:
    """The map of every column of density_metrics.csv over min_cluster_size x min_samples, one file per
    cluster_selection_method for hdbscan_soft (the name tuning_plot[_cluster_selection_method=<value>].png the sweep
    gave it before DBCV existed, which is what the report links)."""
    run = context.run
    groups = density_groups(read_density_metrics(run.run_dir))
    paths = _density_figure_paths(run.run_dir, groups, "tuning_plot")
    refuse_existing(list(paths.values()), context.overwrite)
    title = compose_clustering_tuning_title(run.run_dir, run.method)
    for name, group in groups.items():
        columns = [column for column in DENSITY_MAP_COLUMNS if column in group.columns and group[column].notna().any()]
        plot_clustering_tuning_heatmaps(
            group, "min_cluster_size", "min_samples", columns, paths[name], f"{title} - cluster_selection_method={name}" if name else title
        )
    return list(paths.values())


def _run_internal_metrics(context: EvaluationContext, settings: dict) -> list[Path]:
    """Recomputes from the stored labels the columns the sweep computes from them and rewrites them in
    tuning_results.csv, leaving every other column as it is. It replaces a file the sweep wrote, so it only runs
    with overwrite=true; the file is written to a temporary name first and renamed, never left half written."""
    run = context.run
    path = run.run_dir / "tuning_results.csv"
    if not context.overwrite:
        raise FileExistsError(f"{INTERNAL_METRICS} rewrites {path.name}: set overwrite=true to allow it")
    metrics = recomputed_internal_metrics(run, context.matrix(), context.distance_cache)
    temporary = path.with_suffix(".csv.tmp")
    metrics.to_csv(temporary, index=False)
    os.replace(temporary, path)
    for column in metrics.columns:  # the evaluations that follow read run.results: they must see the new values
        run.results[column] = metrics[column]
    return [path]


EVALUATIONS: dict[str, EvaluationSpec] = {
    K_CURVES: EvaluationSpec(_AGGLOMERATIVE_ONLY, _validate_no_settings(K_CURVES), _run_k_curves),
    COPHENETIC_CORRELATION: EvaluationSpec(_AGGLOMERATIVE_ONLY, _validate_no_settings(COPHENETIC_CORRELATION), _run_cophenetic_correlation),
    DENDROGRAM_JUMP: EvaluationSpec(_AGGLOMERATIVE_ONLY, _validate_dendrogram_jump_settings, _run_dendrogram_jump),
    LINKAGE_AGREEMENT: EvaluationSpec(_AGGLOMERATIVE_ONLY, _validate_no_settings(LINKAGE_AGREEMENT), _run_linkage_agreement),
    LARGEST_CLUSTER_SHARE: EvaluationSpec(_AGGLOMERATIVE_ONLY, _validate_no_settings(LARGEST_CLUSTER_SHARE), _run_largest_cluster_share),
    DUNN_INDEX: EvaluationSpec(_AGGLOMERATIVE_ONLY, _validate_no_settings(DUNN_INDEX), _run_dunn_index),
    DENSITY_METRICS: EvaluationSpec(_DENSITY_ONLY, _validate_no_settings(DENSITY_METRICS), _run_density_metrics),
    DBCV_CURVES: EvaluationSpec(_DENSITY_ONLY, _validate_no_settings(DBCV_CURVES), _run_dbcv_curves),
    TUNING_HEATMAPS: EvaluationSpec(_DENSITY_ONLY, _validate_no_settings(TUNING_HEATMAPS), _run_tuning_heatmaps),
    INTERNAL_METRICS: EvaluationSpec(_RECOMPUTABLE_METHODS, _validate_no_settings(INTERNAL_METRICS), _run_internal_metrics),
}


def load_evaluation_settings(path: str | Path) -> dict[str, dict]:
    """The evaluations registry file: one settings object per registered evaluation, by name. Every
    registered evaluation must have an entry (an empty object when it takes no settings) and no other name
    may appear - a threshold lives in exactly one place. Raises FileNotFoundError / ValueError."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"evaluations registry not found: {path}")
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"evaluations registry {path} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"evaluations registry {path} must be an object mapping evaluation names to settings, got {raw!r}")
    missing, unknown = sorted(set(EVALUATIONS) - set(raw)), sorted(set(raw) - set(EVALUATIONS))
    if missing or unknown:
        raise ValueError(f"evaluations registry {path}: missing {missing}, unknown {unknown} - it must list exactly {sorted(EVALUATIONS)}")
    for name, settings in raw.items():
        if not isinstance(settings, dict):
            raise ValueError(f"evaluations registry {path}: {name!r} must be an object of settings, got {settings!r}")
        EVALUATIONS[name].validate_settings(settings)
    return raw


def validate_tuning_evaluations_block(raw: object) -> dict[str, tuple[str, ...]]:
    """Checks the shape of a `tuning_evaluations` block: an object with a "general" key and optionally one
    key per clustering method, each a list of unique registered evaluation names that apply to that key.
    The "general" key is required (an empty list when nothing applies to every method). Raises ValueError."""
    if not isinstance(raw, dict):
        raise ValueError(f"config: field 'tuning_evaluations' must be an object keyed by {GENERAL!r} and clustering methods, got {raw!r}")
    if GENERAL not in raw:
        raise ValueError(f"config: 'tuning_evaluations' needs a {GENERAL!r} key (an empty list when nothing applies to every method)")
    unknown_keys = sorted(set(raw) - {GENERAL} - set(CLUSTERING_METHODS))
    if unknown_keys:
        raise ValueError(f"config: 'tuning_evaluations' has unknown key(s) {unknown_keys} - known: {[GENERAL, *sorted(CLUSTERING_METHODS)]}")
    block: dict[str, tuple[str, ...]] = {}
    for key, names in raw.items():
        if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            raise ValueError(f"config: tuning_evaluations[{key!r}] must be a list of evaluation names, got {names!r}")
        if len(set(names)) != len(names):
            raise ValueError(f"config: tuning_evaluations[{key!r}] contains duplicate entries: {names!r}")
        for name in names:
            if name not in EVALUATIONS:
                raise ValueError(f"config: unknown clustering tuning evaluation {name!r} in tuning_evaluations[{key!r}] - known: {sorted(EVALUATIONS)}")
            applies_to = EVALUATIONS[name].methods
            if (key == GENERAL and applies_to != _ALL_METHODS) or (key != GENERAL and key not in applies_to):
                where = "every method" if key == GENERAL else f"{key!r}"
                raise ValueError(
                    f"config: tuning_evaluations[{key!r}] lists {name!r}, which does not apply to {where} - it applies to {sorted(applies_to)}"
                )
        block[key] = tuple(names)
    return block


def require_methods_declared(block: Mapping[str, tuple[str, ...]], methods: tuple[str, ...]) -> None:
    """Every method the block is applied to must have its own key (an empty list when nothing is to be run
    for it): the config states what each method gets instead of leaving it to be inferred."""
    missing = [method for method in methods if method not in block]
    if missing:
        raise ValueError(f"config: tuning_evaluations has no key for {missing} - add each with a list of evaluations (empty for none)")


def evaluations_for(block: Mapping[str, tuple[str, ...]], method: str) -> tuple[str, ...]:
    """The evaluations that run for `method`: the "general" ones, then the method's own."""
    return (*block[GENERAL], *block[method])


def run_evaluations(
    block: Mapping[str, tuple[str, ...]],
    settings: Mapping[str, dict],
    run: ClusteringTuningRun,
    overwrite: bool,
    matrix: np.ndarray | None = None,
) -> list[Path]:
    """Runs, in declaration order, every evaluation the block lists for the run's method, and returns the
    files written. `matrix` is the matrix the run clustered, when the caller already holds it; otherwise
    the evaluations that need it load it from the run's input_path. Raises ValueError if the block has no
    key for the run's method."""
    require_methods_declared(block, (run.method,))
    context = EvaluationContext(run, overwrite, matrix)
    written: list[Path] = []
    for name in evaluations_for(block, run.method):
        logging.info("running clustering tuning evaluation %s with settings %s", name, settings[name])
        written += EVALUATIONS[name].run(context, settings[name])
    return written
