"""Parsing/validation of dim_reduction.json, clustering.json.

Same style as build_config.py: hand-written
_require_* helpers, every field validated upfront. reduction_method is
checked against REDUCTION_METHODS; clustering_methods (a non-empty list,
duplicates rejected - lessons_learned.md #5) has every element checked
against CLUSTERING_METHODS - requires those registries to already exist,
which is why this module was built after reduction.py/clustering.py (see
docs/dev/config.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.analysis import clustering_tuning_evaluations as clustering_evaluations
from src.analysis.clustering import CLUSTERING_METHODS
from src.analysis.reduction import REDUCTION_METHODS
from src.analysis.tuning_evaluations import KIND_EMBEDDING_EVALUATION, validate_tuning_evaluations_block

# ClusteringConfig.reduction_method's valid values: any real dim_reduction method, plus the
# "raw" sentinel for clustering directly on an un-reduced feature matrix.
RAW_OR_REDUCTION_METHODS = set(REDUCTION_METHODS) | {"raw"}


@dataclass(frozen=True)
class DimReductionConfig:
    project: str
    input_path: Path
    reduction_method: str
    params_file: Path
    output_root: Path
    session_name: str
    overwrite: bool
    fine_tuning: bool
    color_by: tuple[str, ...]
    viz_n_components: int
    save_tuning_embeddings: bool
    precompute_distance_metric: bool
    tuning_evaluations: dict[str, dict]
    run_notes: str | None


@dataclass(frozen=True)
class EvaluateTuningEmbeddingsConfig:
    tuning_dir: Path
    overwrite: bool
    tuning_evaluations: dict[str, dict]


@dataclass(frozen=True)
class AnalyzeClusteringTuningConfig:
    tuning_dir: Path
    overwrite: bool
    evaluations_file: Path
    tuning_evaluations: dict[str, tuple[str, ...]]
    write_report: bool


@dataclass(frozen=True)
class ClusteringConfig:
    project: str
    input_path: Path
    reduction_method: str
    clustering_methods: tuple[str, ...]
    params_file: Path
    reduction_params_file: Path | None
    output_root: Path
    session_name: str
    overwrite: bool
    fine_tuning: bool
    reduced_data: bool
    viz_embedding_path: Path | None
    save_tuning_clusterings: bool
    evaluations_file: Path
    tuning_evaluations: dict[str, tuple[str, ...]]
    run_notes: str | None


def load_dim_reduction_config(path: str | Path) -> DimReductionConfig:
    raw = _read_config(path)
    project, input_path, output_root, session_name, overwrite, run_notes = _load_shared_fields(raw)
    return DimReductionConfig(
        project=project,
        input_path=input_path,
        reduction_method=_validate_method(_require_str(raw, "reduction_method"), REDUCTION_METHODS, "reduction_method"),
        params_file=Path(_require_str(raw, "params_file")),
        output_root=output_root,
        session_name=session_name,
        overwrite=overwrite,
        fine_tuning=_require_bool(raw, "fine_tuning"),
        color_by=_require_str_list_allow_empty(raw, "color_by"),
        viz_n_components=_require_viz_n_components(raw),
        save_tuning_embeddings=_require_bool(raw, "save_tuning_embeddings"),
        precompute_distance_metric=_require_bool(raw, "precompute_distance_metric"),
        # Required in every config (an empty object is valid) so a run always states which
        # evaluation mechanisms it applies; read only by fine_tuning=true, where the sweep's own
        # score must be listed (src/analysis/tuning_evaluations.py::require_native_score_declared).
        tuning_evaluations=_require_tuning_evaluations(raw),
        run_notes=run_notes,
    )


def load_evaluate_tuning_embeddings_config(path: str | Path) -> EvaluateTuningEmbeddingsConfig:
    """Config of src/pipeline/evaluate_tuning_embeddings.py: which stored tuning run to evaluate
    and with what. Only embedding evaluations are accepted - sweep scores need the original
    matrix, which this entry point never loads - and at least one is required.
    """
    raw = _read_config(path)
    evaluations = _require_tuning_evaluations(raw, allowed_kinds=frozenset({KIND_EMBEDDING_EVALUATION}))
    if not evaluations:
        raise ValueError("config: field 'tuning_evaluations' must list at least one evaluation to run")
    return EvaluateTuningEmbeddingsConfig(
        tuning_dir=Path(_require_str(raw, "tuning_dir")),
        overwrite=_require_bool(raw, "overwrite"),
        tuning_evaluations=evaluations,
    )


def load_analyze_clustering_tuning_config(path: str | Path) -> AnalyzeClusteringTuningConfig:
    """Config of src/pipeline/analyze_clustering_tuning.py: which stored clustering tuning run to analyse, which
    evaluations to run on it (the same `tuning_evaluations` block clustering.json takes; the block needs a key
    for the method of the run, checked once the run is read) and whether to write report.md. The settings of
    the evaluations (k range, noise limit) are in `evaluations_file`, not here. Every field is required.
    """
    raw = _read_config(path)
    return AnalyzeClusteringTuningConfig(
        tuning_dir=Path(_require_str(raw, "tuning_dir")),
        overwrite=_require_bool(raw, "overwrite"),
        evaluations_file=Path(_require_str(raw, "evaluations_file")),
        tuning_evaluations=_require_clustering_tuning_evaluations(raw),
        write_report=_require_bool(raw, "write_report"),
    )


def load_clustering_config(path: str | Path) -> ClusteringConfig:
    raw = _read_config(path)
    project, input_path, output_root, session_name, overwrite, run_notes = _load_shared_fields(raw)

    # Declares which dim_reduction method (if any) produced input_path's embedding - used
    # only to key an extra output-tree segment (production/tuning/<clustering_method>/
    # <reduction_method>/..., src/pipeline/clustering.py) so results from different source
    # embeddings never land in the same folder. "raw" is the explicit sentinel for
    # clustering directly on an un-reduced feature matrix (docs/dev/clustering_migration_plan.md
    # §1's reduced_data=False case) - required rather than inferred from input_path's own
    # path text (lessons_learned.md #20/#22: never parse structure back out of a path,
    # every caller declares it).
    reduction_method = _validate_method(_require_str(raw, "reduction_method"), RAW_OR_REDUCTION_METHODS, "reduction_method")
    clustering_methods = _require_method_list(raw, "clustering_methods", CLUSTERING_METHODS)
    params_file = Path(_require_str(raw, "params_file"))
    fine_tuning = _require_bool(raw, "fine_tuning")

    # Declarative only (docs/dev/clustering_migration_plan.md §1) - does not trigger any
    # different loading/computation, clustering.py always just clusters whatever load_matrix
    # returns for input_path. Forces every config to state explicitly whether input_path is
    # an already-computed embedding or a raw feature matrix, instead of the code silently
    # guessing from shape - matters for the viz-dimensionality handling in clustering.py.
    reduced_data = _require_bool(raw, "reduced_data")

    # Points at the config/registry/params_reduction*.json that produced input_path (31-08-26,
    # tag-params-multi-key session) - lets clustering.py read input_path's own tag_param/
    # tag_prefix and rebuild its embedding tag (e.g. "m_euclidean_nc2") from input_path's real,
    # already-recorded hyperparameters (read_run_params) instead of that string being hand-typed
    # into session_name, where it could silently drift from the real input_path (see
    # docs/guides/clustering.md, "Nome della cartella finale").
    # Required exactly when reduced_data is True (input_path is then itself a dim_reduction.py
    # run with its own tag_param registry to consult); forbidden otherwise (a raw feature matrix
    # has no embedding tag to derive - a value here would sit unread, code_standards.md §5).
    # Which of the two registries (lesion vs sdc) is never inferred from input_path's own path
    # text (lessons_learned.md #20/#22, same discipline as reduction_method above) - the config
    # states it explicitly, one file per modality.
    reduction_params_file = _optional_path(raw, "reduction_params_file")
    if reduced_data and reduction_params_file is None:
        raise ValueError("clustering config: 'reduction_params_file' is required when reduced_data=true")
    if not reduced_data and reduction_params_file is not None:
        raise ValueError("clustering config: 'reduction_params_file' must be omitted when reduced_data=false (input_path has no embedding tag to derive)")

    save_tuning_clusterings = _require_bool(raw, "save_tuning_clusterings")
    tuning_evaluations = _require_clustering_tuning_evaluations(raw)
    if fine_tuning:
        clustering_evaluations.require_methods_declared(tuning_evaluations, clustering_methods)
        if any(tuning_evaluations[key] for key in tuning_evaluations) and not save_tuning_clusterings:
            raise ValueError(
                "clustering config: 'tuning_evaluations' lists evaluations but 'save_tuning_clusterings' is false - "
                "they read the labels clusterings.npz stores"
            )

    return ClusteringConfig(
        project=project,
        input_path=input_path,
        reduction_method=reduction_method,
        clustering_methods=clustering_methods,
        params_file=params_file,
        reduction_params_file=reduction_params_file,
        output_root=output_root,
        session_name=session_name,
        overwrite=overwrite,
        fine_tuning=fine_tuning,
        reduced_data=reduced_data,
        # Optional (docs/dev/clustering_migration_plan.md §3) - only consulted when X has more
        # than 3 components and there is a cluster-colored scatter to plot; a companion 2D/3D
        # embedding computed separately (same reduction params as X's own, only n_components
        # different), never recomputed by clustering.py itself.
        viz_embedding_path=_optional_path(raw, "viz_embedding_path"),
        # Required, off-by-default opt-in (mirrors DimReductionConfig.save_tuning_embeddings) -
        # forces every config to state explicitly whether a fine-tuning sweep should persist
        # every combination's actual cluster labels (not just its scores) into clusterings.npz,
        # rather than the pipeline silently deciding on its own (code_standards.md §0). Read only
        # in fine-tuning mode (_write_tuning_output) - a production run never sweeps combinations,
        # so it has nothing to persist here regardless of this flag's value.
        save_tuning_clusterings=save_tuning_clusterings,
        # Required in every config like dim_reduction's tuning_evaluations (an empty "general" list is valid),
        # read only by fine_tuning=true: the settings file the evaluations take their thresholds from, and
        # which of them run for each method.
        evaluations_file=Path(_require_str(raw, "evaluations_file")),
        tuning_evaluations=tuning_evaluations,
        run_notes=run_notes,
    )


def _read_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")
    return raw


def _load_shared_fields(raw: dict) -> tuple[str, Path, Path, str, bool, str | None]:
    return (
        _require_str(raw, "project"),
        Path(_require_str(raw, "input_path")),
        Path(_require_str(raw, "output_root")),
        _require_str(raw, "session_name"),
        _require_bool(raw, "overwrite"),
        _optional_str(raw, "run_notes"),
    )


def _require_str(raw: dict, key: str) -> str:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string, got {value!r}")
    return value


def _require_bool(raw: dict, key: str) -> bool:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, bool):
        raise ValueError(f"config: field {key!r} must be a boolean, got {value!r}")
    return value


def _optional_str(raw: dict, key: str) -> str | None:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string when set, got {value!r}")
    return value


def _optional_path(raw: dict, key: str) -> Path | None:
    value = _optional_str(raw, key)
    return Path(value) if value is not None else None


def _validate_method(value: str, registry: dict | set[str], field_name: str) -> str:
    if value not in registry:
        raise ValueError(f"config: unknown {field_name} {value!r} - known: {sorted(registry)}")
    return value


def _require_str_list(raw: dict, key: str) -> tuple[str, ...]:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty list, got {value!r}")
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"config: field {key!r} must contain only non-empty strings, got {item!r}")
    if len(set(value)) != len(value):
        raise ValueError(f"config: field {key!r} contains duplicate entries: {value!r}")
    return tuple(value)


def _require_method_list(raw: dict, key: str, registry: dict) -> tuple[str, ...]:
    return tuple(_validate_method(m, registry, "clustering_method") for m in _require_str_list(raw, key))


def _require_str_list_allow_empty(raw: dict, key: str) -> tuple[str, ...]:
    """Like _require_str_list, but an empty list is valid (color_by's "no
    extra coloring" case) - only "the field is missing entirely" is an error,
    forcing every config to state the choice explicitly rather than fall
    back to a default. Actual color mode names (e.g. "dataset"/"volume") are
    resolved against src/analysis/embedding_coloring.COLOR_MODES at plot
    time, not here - keeps this module free of a dependency on that registry.
    """
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list):
        raise ValueError(f"config: field {key!r} must be a list, got {value!r}")
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"config: field {key!r} must contain only non-empty strings, got {item!r}")
    if len(set(value)) != len(value):
        raise ValueError(f"config: field {key!r} contains duplicate entries: {value!r}")
    return tuple(value)


def _require_tuning_evaluations(raw: dict, allowed_kinds: frozenset[str] | None = None) -> dict[str, dict]:
    if "tuning_evaluations" not in raw:
        raise ValueError("config: missing required field 'tuning_evaluations'")
    return validate_tuning_evaluations_block(raw["tuning_evaluations"], allowed_kinds)


def _require_clustering_tuning_evaluations(raw: dict) -> dict[str, tuple[str, ...]]:
    if "tuning_evaluations" not in raw:
        raise ValueError("config: missing required field 'tuning_evaluations'")
    return clustering_evaluations.validate_tuning_evaluations_block(raw["tuning_evaluations"])


def _require_viz_n_components(raw: dict) -> int:
    """viz_n_components must be 2 or 3 - the only dimensionalities any
    plotting function in this codebase supports (2D static+interactive, 3D
    interactive-only, see src/analysis/embedding_plots.py).
    """
    key = "viz_n_components"
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int) or value not in (2, 3):
        raise ValueError(f"config: field {key!r} must be 2 or 3, got {value!r}")
    return value
