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

from src.features.sdc import KNOWN_OBJECTS, KNOWN_VALUE_COLUMNS
from src.retrieval.config import KNOWN_GROUPS

_KNOWN_INTERPOLATIONS = frozenset({"linear", "nearest", "continuous"})


@dataclass(frozen=True)
class BuildMatrixConfig:
    project: str
    data_root: Path
    datasets: list[str]
    group_filter: list[str] | None
    reference_template_path: Path
    lesion_glob: str
    binarize_threshold: float
    resample_interpolation: str
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_build_matrix_config(path: str | Path) -> BuildMatrixConfig:
    """Load and validate a build_lesion_matrix.json file.

    Raises ValueError identifying the offending field for any structural
    problem (missing field, wrong type, out-of-domain value).
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

    return BuildMatrixConfig(
        project=_require_str(raw, "project"),
        data_root=Path(_require_str(raw, "data_root")),
        datasets=datasets,
        group_filter=_optional_group_filter(raw),
        reference_template_path=reference_template_path,
        lesion_glob=_require_str(raw, "lesion_glob"),
        binarize_threshold=binarize_threshold,
        resample_interpolation=resample_interpolation,
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
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


def _optional_group_filter(raw: dict) -> list[str] | None:
    """Same convention as src.retrieval.config._optional_group_filter: absent/null
    means no restriction, present means exactly these groups (src.retrieval.dataset.group_of)."""
    value = raw.get("group_filter")
    if value is None:
        return None
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"config: field 'group_filter' must be a non-empty list of non-empty strings, got {value!r}")
    unknown = [g for g in value if g not in KNOWN_GROUPS]
    if unknown:
        raise ValueError(f"config: group_filter contains unknown group(s) {unknown} (known: {KNOWN_GROUPS})")
    return value


def _validate_resample_interpolation(value: str) -> str:
    if value not in _KNOWN_INTERPOLATIONS:
        raise ValueError(
            f"config: field 'resample_interpolation' must be one of {sorted(_KNOWN_INTERPOLATIONS)}, got {value!r}"
        )
    return value


@dataclass(frozen=True)
class MaskFcConfig:
    project: str
    data_root: Path
    dataset: str
    group_filter: list[str] | None
    atlas_root: Path
    atlas_combos: list[str]
    lesion_glob: str
    fc_glob_template: str
    min_coverage: float
    resample_interpolation: str
    binarize_threshold: float
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_mask_fc_config(path: str | Path) -> MaskFcConfig:
    """Load and validate a mask_fc.json file.

    Deliberately decoupled from build_fc_matrix.json (own config, own loader,
    own dataclass) - the two pipelines are independent: this one turns raw
    lesion masks + raw FC matrices into NaN-masked per-subject matrices,
    nothing else reads a lesion mask or an atlas past this point.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    return MaskFcConfig(
        project=_require_str(raw, "project"),
        data_root=Path(_require_str(raw, "data_root")),
        dataset=_require_str(raw, "dataset"),
        group_filter=_optional_group_filter(raw),
        atlas_root=Path(_require_str(raw, "atlas_root")),
        atlas_combos=_require_unique_str_list(raw, "atlas_combos"),
        lesion_glob=_require_str(raw, "lesion_glob"),
        fc_glob_template=_require_str(raw, "fc_glob_template"),
        min_coverage=_require_float_in_range(raw, "min_coverage", 0.0, 1.0),
        resample_interpolation=_validate_resample_interpolation(_require_str(raw, "resample_interpolation")),
        binarize_threshold=_require_float_in_range(raw, "binarize_threshold", 0.0, 1.0),
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )


@dataclass(frozen=True)
class BuildFcMatrixConfig:
    project: str
    masked_fc_root: Path
    atlas_combos: list[str]
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_build_fc_matrix_config(path: str | Path) -> BuildFcMatrixConfig:
    """Load and validate a build_fc_matrix.json file.

    No lesion_glob, no atlas_path, no min_coverage here - this pipeline reads
    only the already-masked CSVs mask_fc.py already wrote (masked_fc_root),
    by design (see src/features/functional.py module docstring).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    return BuildFcMatrixConfig(
        project=_require_str(raw, "project"),
        masked_fc_root=Path(_require_str(raw, "masked_fc_root")),
        atlas_combos=_require_unique_str_list(raw, "atlas_combos"),
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )


@dataclass(frozen=True)
class EnrichLesionMetadataConfig:
    project: str
    metadata_path: Path
    compute_volume: bool
    variables: list[str]
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_enrich_lesion_metadata_config(path: str | Path) -> EnrichLesionMetadataConfig:
    """Load and validate an enrich_lesion_metadata.json file.

    metadata_path is read-only - any CSV with subject_id/dataset columns (typically, but not
    necessarily, a build_lesion_matrix.py output's own metadata.csv), the source of the
    subject list to enrich. Never written to - the result always lands in a brand-new
    output_root/<dd-mm>_<session_name> directory, same input->output separation as every
    other pipeline in this repo.

    compute_volume=true has no config fields of its own: it sums the matrix.npy that
    src.utils.artifacts.save_matrix always writes next to metadata_path's own metadata.csv
    (see src.pipeline.enrich_lesion_metadata) - deliberately only for a strictly binary,
    voxel-wise matrix. A parcellated matrix (continuous fraction_lesioned values) has already
    lost the voxel-level information a real voxel count needs, and there is no config-driven
    fallback here to recompute one from raw lesion masks (2026-08-17, on request: dropped
    after review - the only real consumer of this tool, a voxel-wise run, never needed it,
    and re-deriving from raw masks tied this tool's correctness to lesion-discovery
    parameters that can drift from the current retrieval layout over time).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    return EnrichLesionMetadataConfig(
        project=_require_str(raw, "project"),
        metadata_path=Path(_require_str(raw, "metadata_path")),
        compute_volume=_require_bool(raw, "compute_volume"),
        variables=_require_unique_str_list(raw, "variables"),
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )
