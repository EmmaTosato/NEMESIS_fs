"""The cascading selectors that narrow the discovered runs down to the one on screen.

Each facet (data, pipeline, method, metric, components, parameters) offers only the values
still reachable given the others, so a combination that matches no run cannot be picked. The
options are computed from the runs themselves, never hardcoded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.analysis.embedding_app.runs import (
    NO_METRIC,
    NO_N_COMPONENTS,
    PRODUCTION_PIPELINES,
    ProductionRun,
    _matrix_shape,
    _run_chronological_key,
    _run_params_or_none,
    run_reduction_axis,
)
from src.analysis.params import load_tag_params


def _n_components_option_label(n: int) -> str:
    """Dropdown label for one n_components value - AUDIT_FINDINGS.md #64:
    NO_N_COMPONENTS (-1, the clustering-pipeline sentinel) gets NO_METRIC's own readable
    placeholder ("—") instead of the literal string "-1", the same treatment NO_METRIC
    already gets on the metric picker for the analogous case."""
    return NO_METRIC if n == NO_N_COMPONENTS else str(n)


def _reduction_method_label(run: ProductionRun) -> str:
    """The "Riduzione" picker value of `run`: the dimensionality reduction a clustering run was
    computed on (umap, tsne, ..., or "raw" for un-reduced data), NO_METRIC for a dim_reduction
    run (its own Metodo already *is* the reduction method, ProductionRun.reduction_method is None)."""
    return NO_METRIC if run.reduction_method is None else run.reduction_method


def _run_tag_param_label(run: ProductionRun, tag_param: list[str], optional: tuple[str, ...] = ()) -> str | None:
    """Human-readable "key=value, key2=value2" combination of `run`'s own values for
    `tag_param` (params_clustering.json's registered hyperparameter names for this method, in
    their own declared order) - doubles as the tag_param picker's own option value (two runs
    with the same combination share the same label by construction, no separate encode/decode
    step needed). None if `run`'s own params can't be read, or don't actually carry one of the
    registered keys (a registry/artifact mismatch - excluded, not guessed). The keys in `optional` are the
    exception: a run that never recorded one of them (OPTIONAL_TAG_PARAMS) just has it left out of the label."""
    params = _run_params_or_none(run)
    if params is None:
        return None
    try:
        values = {key: params[key] for key in tag_param if key in params or key not in optional}
    except KeyError as exc:
        logging.warning("%s: params missing tag_param key %s, excluding this run from picker options", run.path, exc)
        return None
    return ", ".join(f"{key}={value}" for key, value in values.items())


def _load_tag_params_or_none(clustering_params_file: str | Path, method: str) -> list[str] | None:
    """load_tag_params(clustering_params_file, method), isolated the same way
    _run_params_or_none isolates a single run's own corrupt config.md (lesson #21) - but here
    the failure isn't per-run, it's per-method: `method` has production runs on disk (that's
    the only way this app ever offers it as a choice, see method_options) yet has no entry at
    all in clustering_params_file (config/registry/params_clustering.json) - a real
    registry/artifact mismatch, e.g. a method renamed/dropped from the registry after its
    production output was already written (lessons_learned.md #12 - this happened for real,
    dbscan -> hdbscan). None on failure, logged as a warning - callers treat it the same as "no
    tag_param declared for this method" (NO_METRIC), never a raw crash of the Parametri picker
    step."""
    try:
        return load_tag_params(clustering_params_file, method)
    except ValueError as exc:
        logging.warning(
            "%s: method %r has production runs but no entry in the clustering params registry, "
            "cannot resolve its tag_param combinations: %s", clustering_params_file, method, exc,
        )
        return None


# What a selector shows when it is not a filter: the runs listed are then not narrowed by it.
UNSET = "---"

# The selectors that filter the run list, in the order they are shown. "run" is the list itself: the runs that
# match every filter that is set; choosing one of them does not set the filters that are not.
PICKER_FACETS: tuple[str, ...] = (
    "modality", "pipeline", "method", "reduction", "n_subjects", "metric", "n_components", "tag_params", "tag_params_rest",
)
PICKER_FIELDS: tuple[str, ...] = (*PICKER_FACETS, "run")

# The methods whose hyperparameters take two selectors instead of one: the registered `tag_param` keys listed here go to
# the first ("tag_params"), the others to the second ("tag_params_rest"). Every other method has all of them in the
# first and NO_METRIC in the second.
SPLIT_TAG_PARAMS: dict[str, tuple[str, ...]] = {"agglomerative": ("n_clusters",)}

# Registered `tag_param` keys that some runs never recorded in their params (agglomerative runs from before the metric
# was a param): those runs stay in the picker, the key just does not appear in their label.
OPTIONAL_TAG_PARAMS: dict[str, tuple[str, ...]] = {"agglomerative": ("metric",)}

# Shown next to a run's name for the facets that are not set, so runs of different methods are told apart.
_RUN_LABEL_FACETS = ("modality", "pipeline", "method", "reduction")


def _run_n_subjects(run: ProductionRun) -> int:
    """The number of subjects (rows) of the run's matrix, read from manifest.json without loading matrix.npy.
    Raises ValueError if the manifest does not carry it."""
    try:
        return int(_matrix_shape(run)[0])
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"{run.path}: manifest.json has no usable matrix_shape: {exc!r}") from exc


def run_picker_values(run: ProductionRun, clustering_params_file: str | Path) -> dict[str, object]:
    """The value `run` has at every filter selector (PICKER_FACETS). Raises ValueError if `run`'s own
    params/config cannot be read."""
    metric, n_components = run_reduction_axis(run)
    tag_params = tag_params_rest = NO_METRIC
    if run.pipeline == "clustering":
        tag_param = _load_tag_params_or_none(clustering_params_file, run.method)
        if tag_param:
            first = [key for key in tag_param if key in SPLIT_TAG_PARAMS.get(run.method, tag_param)]
            rest = [key for key in tag_param if key not in first]
            labels = [_run_tag_param_label(run, keys, OPTIONAL_TAG_PARAMS.get(run.method, ())) if keys else NO_METRIC for keys in (first, rest)]
            if None in labels:
                raise ValueError(f"{run.path}: params do not carry the registered tag_param keys {tag_param}")
            tag_params, tag_params_rest = labels
    return {
        "modality": run.modality, "pipeline": run.pipeline, "method": run.method,
        "reduction": _reduction_method_label(run), "metric": metric, "n_components": n_components,
        "n_subjects": _run_n_subjects(run), "tag_params": tag_params, "tag_params_rest": tag_params_rest,
    }


@dataclass(frozen=True)
class IndexedRun:
    """A run with its value at every filter selector, read once (not on every click)."""

    run: ProductionRun
    values: dict[str, object]


def index_runs(runs: list[ProductionRun], clustering_params_file: str | Path) -> list[IndexedRun]:
    """`runs` with their selector values, oldest first (_run_chronological_key). A run whose own params or config
    cannot be read is left out, with a warning naming it and why: one corrupt config.md must not take the
    whole picker down. Raises ValueError if no run is left."""
    indexed = []
    for run in sorted(runs, key=_run_chronological_key):
        try:
            indexed.append(IndexedRun(run, run_picker_values(run, clustering_params_file)))
        except ValueError as exc:
            logging.warning("%s: cannot read its selector values, leaving it out of the picker: %s", run.path, exc)
    if not indexed:
        raise ValueError("no run has readable params: nothing the picker can offer")
    return indexed


def _matches(item: IndexedRun, filters: dict[str, object]) -> bool:
    return all(item.values[facet] == value for facet, value in filters.items())


def _facet_sort_key(facet: str, value: object) -> tuple:
    if facet == "pipeline":
        return (PRODUCTION_PIPELINES.index(value),)
    if facet == "reduction":  # "raw" last, so a real embedding comes first
        return (value == "raw", str(value))
    return (str(value),) if isinstance(value, str) else (value,)


@dataclass(frozen=True)
class PickerState:
    """What every selector shows: `options` (UNSET first; for "run" then the run keys), `chosen` (its
    current value) and `run_labels` (the text of each run key)."""

    options: dict[str, list]
    chosen: dict[str, object]
    run_labels: dict[str, str]


def resolve_pickers(indexed: list[IndexedRun], current: dict[str, object], changed: str | None) -> PickerState:
    """The state of every selector, computed together from one consistent selection.

    The selectors are a left-to-right cascade (PICKER_FACETS order): each one offers only the values found among
    the runs that match the filters set to its *left*, so what it offers is always compatible with what was
    chosen before it, and a value it offers gives at least one run. A selector set to UNSET is not a filter;
    one can stop at any point and pick the run directly. "Run" lists the runs that match every filter that is set
    and also offers UNSET: no run chosen, which stays chosen until the user picks one.

    Choosing a run fills every selector still at UNSET with that run's own value (its parameters follow the run).
    Changing a filter keeps the run while the filters still list it, else the most recent one.

    `changed` is the selector the user just touched (None at the first render, when only the modality and the
    pipeline are set, to the first ones, and the run is left at UNSET: the page opens with no run chosen). The changed
    filter wins: filters are applied starting from it, and one that would leave no run at all goes back to UNSET,
    which the selector then shows.
    """
    filters: dict[str, object] = {}
    first_render = changed is None and all(current.get(facet) in (None, UNSET) for facet in PICKER_FACETS)
    if first_render:
        modality = min(item.values["modality"] for item in indexed)
        pipelines = {item.values["pipeline"] for item in indexed if item.values["modality"] == modality}
        filters = {"modality": modality, "pipeline": next(p for p in PRODUCTION_PIPELINES if p in pipelines)}
    else:
        order = [changed, *(f for f in PICKER_FACETS if f != changed)] if changed in PICKER_FACETS else list(PICKER_FACETS)
        for facet in order:
            value = current.get(facet)
            if value in (None, UNSET):
                continue
            trial = {**filters, facet: value}
            if any(_matches(item, trial) for item in indexed):
                filters = trial

    listed = [item for item in indexed if _matches(item, filters)]
    run_keys = [item.run.key for item in listed]
    if first_render:
        run = UNSET
    else:
        run = current.get("run") if current.get("run") in (UNSET, *run_keys) else run_keys[-1]
    if changed == "run" and run != UNSET:
        filters = dict(next(item for item in listed if item.run.key == run).values)
    return _picker_state(indexed, filters, run)


def open_pickers(indexed: list[IndexedRun]) -> PickerState:
    """Every selector at UNSET, the run included (the "Riavvia" button)."""
    return _picker_state(indexed, {}, UNSET)


def _picker_state(indexed: list[IndexedRun], filters: dict[str, object], run: object) -> PickerState:
    """The options of every selector for `filters` (the cascade of resolve_pickers) and `run` as chosen."""
    options: dict[str, list] = {}
    for position, facet in enumerate(PICKER_FACETS):
        left = {f: filters[f] for f in PICKER_FACETS[:position] if f in filters}
        values = {item.values[facet] for item in indexed if _matches(item, left)}
        options[facet] = [UNSET, *sorted(values, key=lambda value: _facet_sort_key(facet, value))]
    chosen: dict[str, object] = {facet: filters.get(facet, UNSET) for facet in PICKER_FACETS}

    listed = [item for item in indexed if _matches(item, filters)]
    options["run"] = [UNSET, *(item.run.key for item in listed)]
    chosen["run"] = run
    shown = [facet for facet in _RUN_LABEL_FACETS if chosen[facet] == UNSET]
    run_labels = {item.run.key: _run_label(item, shown) for item in listed}
    return PickerState(options=options, chosen=chosen, run_labels=run_labels)


def _run_label(item: IndexedRun, shown_facets: list[str]) -> str:
    """The run's name, followed by its value at each facet that is not a filter (the n.a. ones left out)."""
    extras = [str(item.values[facet]) for facet in shown_facets if item.values[facet] != NO_METRIC]
    return item.run.run_name if not extras else f"{item.run.run_name}  ({' / '.join(extras)})"
