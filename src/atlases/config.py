"""Parsing/validation of build_combined_atlas.json.

Same style as src/retrieval/config.py and src/analysis/build_config.py:
hand-written _require_* helpers, every field validated upfront so a bad
config is rejected before any file is touched.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BuildCombinedAtlasConfig:
    cortical_atlas_path: Path
    subcortical_atlas_path: Path
    output_atlas_path: Path
    output_label_table_path: Path
    overwrite: bool


def load_build_combined_atlas_config(path: str | Path) -> BuildCombinedAtlasConfig:
    """Load and validate a build_combined_atlas.json file.

    Raises FileNotFoundError if the config or either source atlas is missing,
    ValueError for any structural problem in the config content.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    cortical_atlas_path = Path(_require_str(raw, "cortical_atlas_path"))
    subcortical_atlas_path = Path(_require_str(raw, "subcortical_atlas_path"))
    _require_existing_file(cortical_atlas_path, "cortical_atlas_path")
    _require_existing_file(subcortical_atlas_path, "subcortical_atlas_path")

    return BuildCombinedAtlasConfig(
        cortical_atlas_path=cortical_atlas_path,
        subcortical_atlas_path=subcortical_atlas_path,
        output_atlas_path=Path(_require_str(raw, "output_atlas_path")),
        output_label_table_path=Path(_require_str(raw, "output_label_table_path")),
        overwrite=_require_bool(raw, "overwrite"),
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


def _require_existing_file(path: Path, field_name: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"config: field {field_name!r} points to a non-existent file: {path}")
