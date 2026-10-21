"""Registry of the evaluation mechanisms a dim_reduction tuning run applies, declared in the
`tuning_evaluations` block of dim_reduction.json (one key per mechanism, its settings as value).

Two kinds, told apart by what they need:

- KIND_SWEEP_SCORE (trustworthiness, cumulative_explained_variance): the quality number computed
  inside the sweep for every combination, from the original matrix X - it is the column of
  tuning_results.csv. Fixed by reduction_method (src/analysis/tuning.py::TUNING_METRIC_NAMES),
  never optional; it is listed in the config so the file states every mechanism that is applied,
  and require_native_score_declared makes sure that statement is true.
- KIND_EMBEDDING_EVALUATION (plot_hdbscan): reads only the saved embeddings, so it runs right
  after a sweep (in memory) or any time later on a stored run, with no refit and no X
  (src/pipeline/evaluate_tuning_embeddings.py). Same code path both ways: run_embedding_evaluations.

Adding a mechanism = one EvaluationSpec in EVALUATIONS (settings validation, optional feasibility
check against the grid, a run function). Nothing else - config parsing, the pipeline and the
standalone entry point iterate the registry.

Clustering tuning (src/analysis/clustering_tuning.py) is expected to reach the same structure
(.claude/open_problems.md).
"""

from __future__ import annotations

import itertools
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.clustering import hdbscan_cluster
from src.analysis.plotting import compose_tuning_leaf_title, plot_hdbscan_grid
from src.analysis.tuning_embeddings import TuningRun, combo_key, leaf_dir, parse_combo_key

TRUSTWORTHINESS = "trustworthiness"
CUMULATIVE_EXPLAINED_VARIANCE = "cumulative_explained_variance"
PLOT_HDBSCAN = "plot_hdbscan"

KIND_SWEEP_SCORE = "sweep_score"
KIND_EMBEDDING_EVALUATION = "embedding_evaluation"

# The only dimensionality a static grid can show - a higher-dimensional embedding is shown on its
# own twin fit at this many components (same hyperparameters, n_components changed), never a slice
# of its columns (lessons_learned.md #16).
VIZ_N_COMPONENTS = 2

_HDBSCAN_SETTINGS = ("min_cluster_size", "min_samples")


@dataclass(frozen=True)
class EvaluationSpec:
    kind: str
    validate_settings: Callable[[dict], None]
    run: Callable[[TuningRun, dict, bool], list[Path]] | None = None
    check_feasible: Callable[[dict, dict, dict], None] | None = None


def _validate_no_settings(name: str) -> Callable[[dict], None]:
    def validate(settings: dict) -> None:
        if settings:
            raise ValueError(
                f"tuning_evaluations[{name!r}] takes no settings here (got {sorted(settings)}) - its parameters "
                "live in the params_file registry"
            )

    return validate


def _validate_plot_hdbscan_settings(settings: dict) -> None:
    unknown = sorted(set(settings) - set(_HDBSCAN_SETTINGS))
    missing = sorted(set(_HDBSCAN_SETTINGS) - set(settings))
    if unknown or missing:
        raise ValueError(
            f"tuning_evaluations[{PLOT_HDBSCAN!r}] needs exactly {list(_HDBSCAN_SETTINGS)} "
            f"(missing {missing}, unknown {unknown})"
        )
    for name, minimum in (("min_cluster_size", 2), ("min_samples", 1)):
        value = settings[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"tuning_evaluations[{PLOT_HDBSCAN!r}][{name!r}] must be an integer >= {minimum}, got {value!r}")


def _check_plot_hdbscan_feasible(base_params: dict, tuning_grid: dict, settings: dict) -> None:
    """Fails before the sweep (hours of fits) when a higher-dimensional combination would have no
    VIZ_N_COMPONENTS twin to be drawn on. If the sweep's dimensionality cannot be known from the
    grid or base_params, the post-sweep check in visualization_key is the one that decides.
    Raises ValueError for a non-scalar n_components.
    """
    if "n_components" in tuning_grid:
        declared = list(tuning_grid["n_components"])
    elif "n_components" in base_params:
        declared = [base_params["n_components"]]
    else:
        return
    non_scalar = [value for value in declared if isinstance(value, (list, dict))]
    if non_scalar:
        raise ValueError(f"n_components must be an integer (or a list of integers in tuning_grid), got non-scalar {non_scalar!r}")
    dims = set(declared)
    if dims <= {VIZ_N_COMPONENTS}:
        return
    if "n_components" in tuning_grid and VIZ_N_COMPONENTS in tuning_grid["n_components"]:
        return
    raise ValueError(
        f"{PLOT_HDBSCAN} needs a {VIZ_N_COMPONENTS}-component twin fit to draw every higher-dimensional embedding "
        f"on, but n_components={sorted(dims)} and the sweep does not include n_components={VIZ_N_COMPONENTS} - "
        f"add {VIZ_N_COMPONENTS} to the tuning_grid's n_components list or drop {PLOT_HDBSCAN} from tuning_evaluations"
    )


def visualization_key(key: str, embedding_dim: int, available: Mapping[str, np.ndarray]) -> str:
    """Key of the embedding a combination is drawn on: itself when it already has VIZ_N_COMPONENTS
    columns, else its twin - the combination with the same hyperparameters and n_components=
    VIZ_N_COMPONENTS (a separate, real fit). Raises ValueError when no such twin was swept.
    """
    if embedding_dim == VIZ_N_COMPONENTS:
        return key
    tokens = parse_combo_key(key)
    if "n_components" not in tokens:
        raise ValueError(
            f"combination {key!r} has a {embedding_dim}-component embedding and no n_components in the sweep, "
            f"so there is no {VIZ_N_COMPONENTS}-component twin fit to draw it on"
        )
    twin = combo_key(list(tokens), [str(VIZ_N_COMPONENTS) if name == "n_components" else value for name, value in tokens.items()])
    if twin not in available:
        raise ValueError(f"combination {key!r} needs its {VIZ_N_COMPONENTS}-component twin {twin!r}, which was not swept")
    return twin


def _params_lines(values: Mapping[str, object], per_line: int = 2) -> list[str]:
    items = [f"{name}={value}" for name, value in values.items()]
    return [", ".join(items[i : i + per_line]) for i in range(0, len(items), per_line)]


def _run_plot_hdbscan(run: TuningRun, settings: dict, overwrite: bool) -> list[Path]:
    """HDBSCAN on every combination's own embedding (the space it was fitted in, however many
    components), drawn on its 2D twin: one grid PNG plus one results CSV per nested leaf (one
    folder per nested-parameter value, the same layout embeddings_grid_*.png uses). Files carry
    the HDBSCAN settings in their name, so re-running with other settings adds files instead of
    replacing them.
    """
    hdbscan_params = {name: settings[name] for name in _HDBSCAN_SETTINGS}
    tag = f"mcs{settings['min_cluster_size']}_ms{settings['min_samples']}"
    keys = list(run.tuning_grid)
    free_params = [name for name in keys if name not in run.nested_params]
    viz_keys = {key: visualization_key(key, emb.shape[1], run.embeddings) for key, emb in run.embeddings.items()}

    written: list[Path] = []
    for leaf_values in itertools.product(*(run.tuning_grid[name] for name in run.nested_params)):
        leaf = dict(zip(run.nested_params, leaf_values))
        directory = leaf_dir(run.run_dir, run.nested_params, leaf)
        png_path, csv_path = directory / f"hdbscan_grid_{tag}.png", directory / f"hdbscan_results_{tag}.csv"
        existing = [p for p in (png_path, csv_path) if p.exists()]
        if existing and not overwrite:
            raise FileExistsError(f"{existing} already exist - set overwrite=true to replace them")

        cells, rows = [], []
        for free_values in itertools.product(*(run.tuning_grid[name] for name in free_params)):
            values = {**leaf, **dict(zip(free_params, free_values))}
            values = {name: values[name] for name in keys}
            key = combo_key(keys, list(values.values()))
            labels = hdbscan_cluster(run.embeddings[key], hdbscan_params)
            n_clusters, noise_fraction = len(np.unique(labels[labels != -1])), float((labels == -1).mean())
            rows.append({**values, "n_clusters_found": n_clusters, "noise_fraction": noise_fraction})

            lines = _params_lines(values)
            if viz_keys[key] != key:
                lines.append(f"drawn on its n_components={VIZ_N_COMPONENTS} twin fit")
            lines.append(f"HDBSCAN k={n_clusters}, noise={noise_fraction:.0%}")
            cells.append(("\n".join(lines), run.embeddings[viz_keys[key]], labels))

        ncols = len(run.tuning_grid[free_params[-1]]) if free_params else 1
        grid = [cells[i : i + ncols] for i in range(0, len(cells), ncols)]
        suptitle = (
            f"{compose_tuning_leaf_title(run.run_dir, run.reduction_method, leaf)} - HDBSCAN "
            f"(min_cluster_size={settings['min_cluster_size']}, min_samples={settings['min_samples']})\n"
            "clusters found in each embedding's own space, gray = noise, colors are per subplot"
        )
        directory.mkdir(parents=True, exist_ok=True)
        plot_hdbscan_grid(grid, png_path, suptitle)
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        logging.info("%s: wrote %s and %s (%d combinations)", PLOT_HDBSCAN, png_path, csv_path, len(rows))
        written += [png_path, csv_path]
    return written


EVALUATIONS: dict[str, EvaluationSpec] = {
    TRUSTWORTHINESS: EvaluationSpec(KIND_SWEEP_SCORE, _validate_no_settings(TRUSTWORTHINESS)),
    CUMULATIVE_EXPLAINED_VARIANCE: EvaluationSpec(KIND_SWEEP_SCORE, _validate_no_settings(CUMULATIVE_EXPLAINED_VARIANCE)),
    PLOT_HDBSCAN: EvaluationSpec(
        KIND_EMBEDDING_EVALUATION, _validate_plot_hdbscan_settings, run=_run_plot_hdbscan, check_feasible=_check_plot_hdbscan_feasible
    ),
}


def validate_tuning_evaluations_block(raw: object, allowed_kinds: frozenset[str] | None = None) -> dict[str, dict]:
    """Checks the shape of a `tuning_evaluations` block: an object mapping registered mechanism
    names to their settings object. `allowed_kinds` restricts which kinds the caller can honour
    (the standalone entry point has no X, so it rejects sweep scores instead of ignoring them).
    """
    if not isinstance(raw, dict):
        raise ValueError(f"config: field 'tuning_evaluations' must be an object mapping evaluation names to settings, got {raw!r}")
    for name, settings in raw.items():
        if name not in EVALUATIONS:
            raise ValueError(f"config: unknown tuning evaluation {name!r} - known: {sorted(EVALUATIONS)}")
        if not isinstance(settings, dict):
            raise ValueError(f"config: tuning_evaluations[{name!r}] must be an object of settings, got {settings!r}")
        spec = EVALUATIONS[name]
        if allowed_kinds is not None and spec.kind not in allowed_kinds:
            raise ValueError(
                f"config: tuning_evaluations[{name!r}] is a {spec.kind} and cannot be run here - "
                f"allowed kinds: {sorted(allowed_kinds)}"
            )
        spec.validate_settings(settings)
    return dict(raw)


def require_native_score_declared(evaluations: Mapping[str, dict], expected_score: str, reduction_method: str) -> None:
    """The sweep always computes exactly one score for a reduction_method (TUNING_METRIC_NAMES) -
    the block must list that one and no other sweep score, so it never states something the run
    does not do (or omits something it does).
    """
    declared = {name for name in evaluations if EVALUATIONS[name].kind == KIND_SWEEP_SCORE}
    if declared != {expected_score}:
        raise ValueError(
            f"tuning_evaluations must declare exactly the sweep score reduction_method={reduction_method!r} computes, "
            f"{expected_score!r} (found {sorted(declared) or 'none'}) - it is always applied and cannot be disabled"
        )


def validate_embedding_evaluations_feasible(
    evaluations: Mapping[str, dict], base_params: dict, tuning_grid: dict
) -> None:
    for name, settings in evaluations.items():
        check = EVALUATIONS[name].check_feasible
        if check is not None:
            check(base_params, tuning_grid, settings)


def run_embedding_evaluations(evaluations: Mapping[str, dict], run: TuningRun, overwrite: bool) -> list[Path]:
    """Runs every KIND_EMBEDDING_EVALUATION in the block against `run`, in declaration order,
    and returns the files written. Sweep scores in the block are not run here - they are computed
    by the sweep itself.
    """
    written: list[Path] = []
    for name, settings in evaluations.items():
        spec = EVALUATIONS[name]
        if spec.kind != KIND_EMBEDDING_EVALUATION:
            continue
        logging.info("running tuning evaluation %s with settings %s", name, settings)
        written += spec.run(run, settings, overwrite)
    return written
