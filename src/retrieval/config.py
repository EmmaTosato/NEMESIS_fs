"""Parsing and validation for retrieval.json configuration files.

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
KNOWN_OBJECTS = ("lesion", "feature")


@dataclass(frozen=True)
class FilePatterns:
    """Registry of where to find a file on disk, for a given `object` and the
    path of keys below it.

    Loaded from a JSON file (see load_file_patterns) nested first by
    `object` (`lesion`/`feature` - a true structural invariant, see
    KNOWN_OBJECTS), then by however many levels that object's own data needs
    down to an ordered list of path templates (relative to that object's own
    `project_root`, with `{subject_id}` as the only placeholder). `lesion`
    nests two levels below object (space, then modality - e.g.
    `lesion.native.T1w`); `feature` nests whatever levels its own registered
    keys need (e.g. `feature.func.motion`) - the depth is read from the JSON,
    never assumed by this class.

    Each object has its own `project_root`, since `lesion` and `feature` live
    under different directory trees at the source (see
    `Clinical_connectome/features/` vs `Clinical_connectome/<dataset>/`).

    More than one template under the same leaf key means "grab every one of
    these that exists for this subject" (e.g. `lesion_roi` named with or
    without an explicit `_space-T1w_` tag, depending on which pipeline
    produced it) - all of them, not just the first found. See
    Dataset.resolve().
    """

    project_roots: dict[str, Path]
    patterns: dict[tuple[str, ...], list[str]]  # (object, *path) -> templates

    def project_root_for(self, object_: str) -> Path:
        if object_ not in self.project_roots:
            raise ValueError(f"no project_root registered for object={object_!r}")
        return self.project_roots[object_]

    def templates_for(self, object_: str, *path: str) -> list[str]:
        key = (object_, *path)
        if key not in self.patterns:
            raise ValueError(f"no file pattern registered for {key}")
        return self.patterns[key]

    def has(self, object_: str, *path: str) -> bool:
        return (object_, *path) in self.patterns

    def combinations_for(self, object_: str) -> list[tuple[str, ...]]:
        """Every full (object, *path) leaf combination registered under this
        object, whatever their depth - used to enumerate all columns of the
        dataset-wide availability report (src.retrieval.matrix), independent
        of what any specific retrieval run's `retrieve` list asks for."""
        return sorted(key for key in self.patterns if key[0] == object_)

    def all_object_spaces(self) -> set[tuple[str, str]]:
        """Every distinct (object, space) pair registered anywhere in this
        registry - i.e. the second path segment under each object (for
        `lesion`: native/mni; for `feature`: whatever its own registered
        keys are). Used by retrieve_data.py to discover subjects across every
        space of a requested object, not just the exact (object, space)
        pairs a run's `retrieve` list happens to name - so a subject known
        via one space is never invisible just because this run only asked
        for a different space of the same object."""
        return {(key[0], key[1]) for key in self.patterns}


@dataclass(frozen=True)
class RetrieveItem:
    object: str
    space: str
    modality: str

    def __post_init__(self) -> None:
        """Only `object` is validated here - it is a true structural
        constant (lesion/feature will not change, see KNOWN_OBJECTS).
        `space`/`modality` validity depends on the external file_patterns
        registry, which a dataclass can't reasonably depend on at
        construction time - see _require_known_combinations, which
        cross-validates config.retrieve against config.file_patterns once in
        load_config."""
        if self.object not in KNOWN_OBJECTS:
            raise ValueError(f"RetrieveItem: unknown object {self.object!r} (known: {KNOWN_OBJECTS})")


@dataclass(frozen=True)
class RetrievalConfig:
    output_root: Path
    project: str
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
    problem: unknown object, an object missing `project_root`, a leaf with no
    templates, or a template missing the `{subject_id}` placeholder it must
    contain to be usable.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"file patterns registry not found: {path}")

    with path.open() as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"file_patterns: top-level content must be a JSON object, got {raw!r}")

    project_roots: dict[str, Path] = {}
    patterns: dict[tuple[str, ...], list[str]] = {}
    for object_, node in raw.items():
        if object_ not in KNOWN_OBJECTS:
            raise ValueError(f"file_patterns: unknown object {object_!r} (known: {KNOWN_OBJECTS})")
        if not isinstance(node, dict):
            raise ValueError(f"file_patterns: object {object_!r} must map to a JSON object")
        project_root = node.get("project_root")
        if not isinstance(project_root, str) or not project_root:
            raise ValueError(f"file_patterns: object {object_!r} missing a non-empty 'project_root'")
        project_roots[object_] = Path(project_root)
        rest = {k: v for k, v in node.items() if k != "project_root"}
        if not rest:
            raise ValueError(f"file_patterns: object {object_!r} has no modalities registered")
        _walk_patterns(patterns, (object_,), rest)

    return FilePatterns(project_roots=project_roots, patterns=patterns)


def _walk_patterns(patterns: dict[tuple[str, ...], list[str]], prefix: tuple[str, ...], node: object) -> None:
    """Recursively parses a nested file_patterns node into flat
    `(object, *path) -> templates` entries - handles `lesion`'s fixed 2 levels
    (space, modality) and whatever depth `feature` needs, without assuming a
    fixed shape."""
    label = ".".join(prefix)
    if isinstance(node, list):
        if not node:
            raise ValueError(f"file_patterns: {label} must be a non-empty list of templates")
        for template in node:
            if not isinstance(template, str) or "{subject_id}" not in template:
                raise ValueError(
                    f"file_patterns: {label} template {template!r} must be a string "
                    "containing '{subject_id}'"
                )
        patterns[prefix] = node
        return
    if not isinstance(node, dict) or not node:
        raise ValueError(f"file_patterns: {label} must be a non-empty object or a list of templates")
    for key, child in node.items():
        _walk_patterns(patterns, (*prefix, key), child)


def load_config(path: str | Path) -> RetrievalConfig:
    """Load and validate a retrieval.json file.

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
    required = ("object", "space", "modality")
    if not isinstance(item, dict) or not all(key in item for key in required):
        raise ValueError(
            f"config: each 'retrieve' entry must have 'object', 'space' and 'modality', got {item!r}"
        )
    return RetrieveItem(object=item["object"], space=item["space"], modality=item["modality"])


def _reject_duplicate_retrieve_items(items: list[RetrieveItem]) -> None:
    """Two identical (object, space, modality) entries would make the second
    one copy the exact same file to the exact same destination as the first,
    within the same run - it would show up as 'skipped (exists)' in the
    report, indistinguishable from a file genuinely already present from a
    previous run. Rejected upfront rather than silently deduplicated, so a
    copy-paste mistake in the config is never masked."""
    seen: set[tuple[str, str, str]] = set()
    duplicates: set[tuple[str, str, str]] = set()
    for item in items:
        key = (item.object, item.space, item.modality)
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        raise ValueError(f"config: field 'retrieve' contains duplicate entries: {sorted(duplicates)}")


def _require_known_combinations(retrieve: list[RetrieveItem], file_patterns: FilePatterns) -> None:
    """An (object, space, modality) requested in `retrieve` must be a
    combination the file_patterns registry actually knows how to look up -
    otherwise the request would only fail later, per-dataset, with a less
    direct error."""
    unknown = [item for item in retrieve if not file_patterns.has(item.object, item.space, item.modality)]
    if unknown:
        raise ValueError(
            "config: 'retrieve' requests combinations not registered in file_patterns: "
            f"{[(item.object, item.space, item.modality) for item in unknown]}"
        )
