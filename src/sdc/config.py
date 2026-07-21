"""Parsing/validation of compute_sdc.json.

Subject discovery reuses FilePatterns/RetrieveItem from src/retrieval/config.py
directly instead of inventing a second config dialect - "which datasets, which
group, where does the lesion mask registry entry point" is exactly the same
question retrieval.json already answers. LESION_ITEM below is the one
(object, pipeline, datatype, suffix) this pipeline ever asks Dataset for.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.retrieval.config import KNOWN_GROUPS, FilePatterns, RetrieveItem, load_file_patterns

LESION_ITEM = RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")


@dataclass(frozen=True)
class SDCConfig:
    project: str
    file_patterns_path: Path
    file_patterns: FilePatterns
    datasets: list[str]
    group_filter: list[str] | None
    bcbtoolkit_path: Path
    tracks_dir: Path | None
    cores_per_subject: int
    stage2_ebrains: bool
    stage2_presets: list[str]
    output_root: Path
    run_name: str
    overwrite: bool
    run_notes: str | None


def load_sdc_config(path: str | Path) -> SDCConfig:
    """Load and validate a compute_sdc.json file.

    Raises ValueError identifying the offending field for any structural
    problem - never a silent default, matching the boundary-validation
    convention in src/retrieval/config.py and src/analysis/build_config.py
    (docs/dev/design_patterns.md, "Boundary validation").
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    file_patterns_path = Path(_require_str(raw, "file_patterns"))
    file_patterns = load_file_patterns(file_patterns_path)
    if not file_patterns.has(*LESION_ITEM.path_key()):
        raise ValueError(
            f"config: file_patterns registry {file_patterns_path} has no entry for "
            f"{LESION_ITEM.path_key()} - compute_sdc requires this exact leaf"
        )

    bcbtoolkit_path = Path(_require_str(raw, "bcbtoolkit_path"))
    if not (bcbtoolkit_path / "run_disco.sh").is_file():
        raise ValueError(f"config: bcbtoolkit_path {bcbtoolkit_path} does not contain run_disco.sh")

    return SDCConfig(
        project=_require_str(raw, "project"),
        file_patterns_path=file_patterns_path,
        file_patterns=file_patterns,
        datasets=_require_unique_str_list(raw, "datasets"),
        group_filter=_optional_group_filter(raw),
        bcbtoolkit_path=bcbtoolkit_path,
        tracks_dir=_optional_existing_dir(raw, "tracks_dir"),
        cores_per_subject=_require_positive_int(raw, "cores_per_subject"),
        stage2_ebrains=_require_bool(raw, "stage2_ebrains"),
        stage2_presets=_optional_str_list(raw, "stage2_presets") or [],
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


def _optional_str(raw: dict, key: str) -> str | None:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string when set, got {value!r}")
    return value


def _require_bool(raw: dict, key: str) -> bool:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, bool):
        raise ValueError(f"config: field {key!r} must be a boolean, got {value!r}")
    return value


def _require_positive_int(raw: dict, key: str) -> int:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"config: field {key!r} must be a positive integer, got {value!r}")
    return value


def _require_str_list(raw: dict, key: str, *, allow_empty: bool) -> list[str]:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"config: field {key!r} must be a list of non-empty strings, got {value!r}")
    if not allow_empty and not value:
        raise ValueError(f"config: field {key!r} must not be empty")
    return value


def _require_unique_str_list(raw: dict, key: str) -> list[str]:
    """Rejects duplicate entries explicitly rather than silently collapsing
    them, same rationale as retrieval.config._require_unique_str_list - a
    repeated dataset name here would silently double-count that dataset's
    subjects in the manifest."""
    value = _require_str_list(raw, key, allow_empty=False)
    duplicates = {v for v in value if value.count(v) > 1}
    if duplicates:
        raise ValueError(f"config: field {key!r} contains duplicate entries: {sorted(duplicates)}")
    return value


def _optional_str_list(raw: dict, key: str) -> list[str] | None:
    if raw.get(key) is None:
        return None
    return _require_str_list(raw, key, allow_empty=True)


def _optional_group_filter(raw: dict) -> list[str] | None:
    value = _optional_str_list(raw, "group_filter")
    if value is None:
        return None
    unknown = [g for g in value if g not in KNOWN_GROUPS]
    if unknown:
        raise ValueError(f"config: group_filter contains unknown group(s) {unknown} (known: {KNOWN_GROUPS})")
    return value


def _optional_existing_dir(raw: dict, key: str) -> Path | None:
    value = _optional_str(raw, key)
    if value is None:
        return None
    path = Path(value)
    if not path.is_dir():
        raise ValueError(f"config: field {key!r} must be an existing directory, got {value!r}")
    return path
