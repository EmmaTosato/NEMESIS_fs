"""Parsing/validation of build_lesion_matrix.json (and future build_*_matrix.json configs).

Same style as src/retrieval/config.py: hand-written _require_*/_optional_*
helpers, every field validated upfront so a bad config is rejected before any
file is touched - never a silent default, never an error surfacing later,
mid-run, from the library code that actually uses the value (e.g. nilearn
rejecting an unknown interpolation kind after minutes of processing).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.features.lesion import PARCEL_AGGREGATIONS

_KNOWN_INTERPOLATIONS = frozenset({"linear", "nearest", "continuous"})


@dataclass(frozen=True)
class BuildMatrixConfig:
    project: str
    data_root: Path
    datasets: list[str]
    reference_template_path: Path
    lesion_glob: str
    binarize_threshold: float
    resample_interpolation: str
    parcellate: bool
    atlas_path: Path | None
    parcel_aggregation: str | None
    save_parcellated_volumes: bool
    output_root: Path
    run_name: str
    overwrite: bool
    run_notes: str | None


def load_build_matrix_config(path: str | Path) -> BuildMatrixConfig:
    """Load and validate a build_lesion_matrix.json file.

    Raises ValueError identifying the offending field for any structural
    problem (missing field, wrong type, out-of-domain value, an impossible
    parcellate/atlas_path/parcel_aggregation combination).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    datasets = _require_unique_str_list(raw, "datasets")
    reference_template_path = Path(_require_str(raw, "reference_template_path"))

    resample_interpolation = _validate_resample_interpolation(_require_str(raw, "resample_interpolation"))
    binarize_threshold = _require_float_in_range(raw, "binarize_threshold", 0.0, 1.0)

    parcellate = _require_bool(raw, "parcellate")
    atlas_path, parcel_aggregation, save_parcellated_volumes = _validate_parcellation_fields(raw, parcellate)

    return BuildMatrixConfig(
        project=_require_str(raw, "project"),
        data_root=Path(_require_str(raw, "data_root")),
        datasets=datasets,
        reference_template_path=reference_template_path,
        lesion_glob=_require_str(raw, "lesion_glob"),
        binarize_threshold=binarize_threshold,
        resample_interpolation=resample_interpolation,
        parcellate=parcellate,
        atlas_path=atlas_path,
        parcel_aggregation=parcel_aggregation,
        save_parcellated_volumes=save_parcellated_volumes,
        output_root=Path(_require_str(raw, "output_root")),
        run_name=_require_str(raw, "run_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
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


def _require_unique_str_list(raw: dict, key: str) -> list[str]:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"config: field {key!r} must be a non-empty list of non-empty strings, got {value!r}")
    duplicates = {v for v in value if value.count(v) > 1}
    if duplicates:
        raise ValueError(f"config: field {key!r} has duplicate entries: {sorted(duplicates)}")
    return value


def _optional_str(raw: dict, key: str) -> str | None:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string when set, got {value!r}")
    return value


def _require_float_in_range(raw: dict, key: str, lo: float, hi: float) -> float:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"config: field {key!r} must be a number, got {value!r}")
    value = float(value)
    if not (lo <= value <= hi):
        raise ValueError(f"config: field {key!r} must be between {lo} and {hi}, got {value}")
    return value


def _validate_resample_interpolation(value: str) -> str:
    if value not in _KNOWN_INTERPOLATIONS:
        raise ValueError(
            f"config: field 'resample_interpolation' must be one of {sorted(_KNOWN_INTERPOLATIONS)}, got {value!r}"
        )
    return value


def _validate_parcellation_fields(raw: dict, parcellate: bool) -> tuple[Path | None, str | None, bool]:
    atlas_path_str = _optional_str(raw, "atlas_path")
    parcel_aggregation = _optional_str(raw, "parcel_aggregation")
    save_parcellated_volumes = _require_bool(raw, "save_parcellated_volumes")

    if parcellate:
        if atlas_path_str is None or parcel_aggregation is None:
            raise ValueError("config: atlas_path and parcel_aggregation are both required when parcellate=true")
        if parcel_aggregation not in PARCEL_AGGREGATIONS:
            raise ValueError(
                f"config: unknown parcel_aggregation {parcel_aggregation!r} - "
                f"known: {sorted(PARCEL_AGGREGATIONS)}"
            )
    else:
        if atlas_path_str is not None or parcel_aggregation is not None:
            raise ValueError("config: atlas_path/parcel_aggregation must not be set when parcellate=false")
        if save_parcellated_volumes:
            raise ValueError("config: save_parcellated_volumes must be false when parcellate=false")

    atlas_path = Path(atlas_path_str) if atlas_path_str is not None else None
    return atlas_path, parcel_aggregation, save_parcellated_volumes
