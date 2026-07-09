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

KNOWN_GROUPS = ("ST", "HC", "PD", "GM")
KNOWN_SPACES = ("native", "mni")


@dataclass(frozen=True)
class FilePatterns:
    """Registry of where to find a file on disk for a given (space, modality).

    Loaded from a JSON file (see load_file_patterns) that maps each known
    space to its known modalities, each modality to an ordered list of path
    templates (relative to a dataset's root, with `{subject_id}` as the only
    placeholder). This is the single source of truth for which (space,
    modality) combinations exist at all - NATIVE_MODALITIES/MNI_MODALITIES
    constants used to live here in code; now they are whatever keys are
    present in this registry, so adding a new modality (or a second MNI
    derivative) is a JSON edit, not a code change.

    More than one template under the same key means "these naming variants
    represent the same logical file" (e.g. lesion_roi named with or without
    an explicit `_space-T1w_` tag, depending on which pipeline produced it) -
    tried in the order listed, first match wins. See Dataset.resolve() for
    what happens when more than one template matches for the same subject.
    """

    patterns: dict[tuple[str, str], list[str]]

    def templates_for(self, space: str, modality: str) -> list[str]:
        key = (space, modality)
        if key not in self.patterns:
            raise ValueError(
                f"no file pattern registered for space={space!r} modality={modality!r}"
            )
        return self.patterns[key]

    def has(self, space: str, modality: str) -> bool:
        return (space, modality) in self.patterns


@dataclass(frozen=True)
class RetrieveItem:
    space: str
    modality: str

    def __post_init__(self) -> None:
        """Only `space` is validated here - it is a true structural constant
        (native/mni will not change). Whether `modality` is a registered
        combination for that space depends on the file_patterns registry,
        which is external, loaded data, not something a dataclass can check
        at construction time - see _require_known_combinations, which
        cross-validates config.retrieve against config.file_patterns in
        load_config."""
        if self.space not in KNOWN_SPACES:
            raise ValueError(f"RetrieveItem: unknown space {self.space!r} (known: {KNOWN_SPACES})")


@dataclass(frozen=True)
class RetrievalConfig:
    output_root: Path
    project: str
    project_root: Path
    file_patterns_path: Path
    file_patterns: FilePatterns
    datasets: list[str]
    group_filter: list[str] | None
    subjects: list[str] | None
    retrieve: list[RetrieveItem]
    include_tabular_data: bool
    overwrite: bool


def load_file_patterns(path: str | Path) -> FilePatterns:
    """Load and validate a file_patterns.json registry.

    Raises ValueError identifying the offending entry for any structural
    problem: unknown space, a modality with no templates, or a template
    missing the `{subject_id}` placeholder it must contain to be usable.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"file patterns registry not found: {path}")

    with path.open() as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"file_patterns: top-level content must be a JSON object, got {raw!r}")

    patterns: dict[tuple[str, str], list[str]] = {}
    for space, modalities in raw.items():
        if space not in KNOWN_SPACES:
            raise ValueError(f"file_patterns: unknown space {space!r} (known: {KNOWN_SPACES})")
        if not isinstance(modalities, dict) or not modalities:
            raise ValueError(f"file_patterns: space {space!r} must map to a non-empty object")
        for modality, templates in modalities.items():
            if not isinstance(templates, list) or not templates:
                raise ValueError(
                    f"file_patterns: {space}.{modality} must be a non-empty list of templates"
                )
            for template in templates:
                if not isinstance(template, str) or "{subject_id}" not in template:
                    raise ValueError(
                        f"file_patterns: {space}.{modality} template {template!r} must be a "
                        f"string containing '{{subject_id}}'"
                    )
            patterns[(space, modality)] = templates

    return FilePatterns(patterns=patterns)


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

    file_patterns_path = Path(_require_str(raw, "file_patterns"))
    file_patterns = load_file_patterns(file_patterns_path)
    retrieve = _require_retrieve_list(raw)
    _require_known_combinations(retrieve, file_patterns)

    return RetrievalConfig(
        output_root=Path(_require_str(raw, "output_root")),
        project=_require_str(raw, "project"),
        project_root=Path(_require_str(raw, "project_root")),
        file_patterns_path=file_patterns_path,
        file_patterns=file_patterns,
        datasets=_require_str_list(raw, "datasets", allow_empty=False),
        group_filter=_optional_group_filter(raw),
        subjects=_optional_str_list(raw, "subjects"),
        retrieve=retrieve,
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
    parsed = [_parse_retrieve_item(item) for item in items]
    _reject_duplicate_retrieve_items(parsed)
    return parsed


def _parse_retrieve_item(item: dict) -> RetrieveItem:
    if not isinstance(item, dict) or "space" not in item or "modality" not in item:
        raise ValueError(
            f"config: each 'retrieve' entry must have 'space' and 'modality', got {item!r}"
        )
    return RetrieveItem(space=item["space"], modality=item["modality"])


def _reject_duplicate_retrieve_items(items: list[RetrieveItem]) -> None:
    """Two identical (space, modality) entries would make the second one
    copy the exact same file to the exact same destination as the first,
    within the same run - it would show up as 'skipped (exists)' in the
    report, indistinguishable from a file genuinely already present from a
    previous run. Rejected upfront rather than silently deduplicated, so a
    copy-paste mistake in the config is never masked."""
    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    for item in items:
        key = (item.space, item.modality)
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        raise ValueError(f"config: field 'retrieve' contains duplicate entries: {sorted(duplicates)}")


def _require_known_combinations(retrieve: list[RetrieveItem], file_patterns: FilePatterns) -> None:
    """A (space, modality) requested in `retrieve` must be a combination the
    file_patterns registry actually knows how to look up - otherwise the
    request would only fail later, per-dataset, with a less direct error."""
    unknown = [item for item in retrieve if not file_patterns.has(item.space, item.modality)]
    if unknown:
        raise ValueError(
            "config: 'retrieve' requests combinations not registered in file_patterns: "
            f"{[(item.space, item.modality) for item in unknown]}"
        )
