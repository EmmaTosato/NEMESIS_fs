"""Parsing and validation for data_retrieval.json configuration files.

This module performs structural validation only (types, allowed values,
required fields) - it never touches the filesystem. Filesystem-dependent
checks (does this dataset root actually exist, does this dataset support
this modality for a specific subject) are the responsibility of Dataset
(see retrieval/dataset.py).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# NOTE: MNI_MODALITIES has one entry today because the only derivative that
# exists (manual_masks) happens to be in MNI space - "mni" is not a generic
# space selector, see Dataset.mni_mask() for the full caveat. Adding a second
# derivative (in MNI space or otherwise) will require revisiting this, not
# just appending a value here.
NATIVE_MODALITIES = ("T1w", "T2w", "FLAIR", "CT", "lesion_roi")
MNI_MODALITIES = ("lesion_mask",)
KNOWN_GROUPS = ("ST", "HC", "PD", "GM")
KNOWN_SPACES = ("native", "mni")


@dataclass(frozen=True)
class RetrieveItem:
    space: str
    modality: str


@dataclass(frozen=True)
class RetrievalConfig:
    output_root: Path
    project: str
    project_root: Path
    datasets: list[str]
    group_filter: list[str] | None
    subjects: list[str] | None
    retrieve: list[RetrieveItem]
    include_tabular_data: bool
    overwrite: bool


def load_config(path: str | Path) -> RetrievalConfig:
    """Load and validate a data_retrieval.json file.

    Raises ValueError identifying the offending field for any structural
    problem (missing field, wrong type, unknown value). No field is ever
    given a silent default - every value used downstream is either present
    and valid, or the config is rejected outright.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)

    return RetrievalConfig(
        output_root=Path(_require_str(raw, "output_root")),
        project=_require_str(raw, "project"),
        project_root=Path(_require_str(raw, "project_root")),
        datasets=_require_str_list(raw, "datasets", allow_empty=False),
        group_filter=_optional_group_filter(raw),
        subjects=_optional_str_list(raw, "subjects"),
        retrieve=_require_retrieve_list(raw),
        include_tabular_data=_require_bool(raw, "include_tabular_data"),
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


def _require_str_list(raw: dict, key: str, *, allow_empty: bool) -> list[str]:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"config: field {key!r} must be a list of non-empty strings, got {value!r}")
    if not allow_empty and not value:
        raise ValueError(f"config: field {key!r} must not be empty")
    return value


def _optional_str_list(raw: dict, key: str) -> list[str] | None:
    if raw.get(key) is None:
        return None
    return _require_str_list(raw, key, allow_empty=False)


def _optional_group_filter(raw: dict) -> list[str] | None:
    value = _optional_str_list(raw, "group_filter")
    if value is None:
        return None
    unknown = [g for g in value if g not in KNOWN_GROUPS]
    if unknown:
        raise ValueError(
            f"config: group_filter contains unknown group(s) {unknown} (known: {KNOWN_GROUPS})"
        )
    return value


def _require_retrieve_list(raw: dict) -> list[RetrieveItem]:
    if "retrieve" not in raw:
        raise ValueError("config: missing required field 'retrieve'")
    items = raw["retrieve"]
    if not isinstance(items, list) or not items:
        raise ValueError(f"config: field 'retrieve' must be a non-empty list, got {items!r}")
    return [_parse_retrieve_item(item) for item in items]


def _parse_retrieve_item(item: dict) -> RetrieveItem:
    if not isinstance(item, dict) or "space" not in item or "modality" not in item:
        raise ValueError(
            f"config: each 'retrieve' entry must have 'space' and 'modality', got {item!r}"
        )
    space = item["space"]
    modality = item["modality"]
    if space not in KNOWN_SPACES:
        raise ValueError(f"config: unknown space {space!r} (known: {KNOWN_SPACES})")
    allowed = MNI_MODALITIES if space == "mni" else NATIVE_MODALITIES
    if modality not in allowed:
        raise ValueError(
            f"config: modality {modality!r} not valid for space={space!r} (known: {allowed})"
        )
    return RetrieveItem(space=space, modality=modality)
