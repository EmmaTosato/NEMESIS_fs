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
KNOWN_OBJECTS = ("lesion", "feature", "sdc")

# Whether an object's file_patterns.json leaves nest under a BIDS-Derivatives
# pipeline name (e.g. lesion/manual_masks/anat/lesion_mask) or not (e.g.
# feature/func/FC-pearson - our features/ tree has no dataset_description.json
# anywhere and no discoverable pipeline name, so we don't invent one). `sdc`
# is externally-computed structural disconnectome output (BCBToolKit, run by
# a collaborator, not by src/sdc/) mirrored under
# Clinical_connectome/features/Clinical_connectome_stroke/<dataset>/lesion/ -
# same reasoning as `feature`: no discoverable BIDS-Derivatives pipeline name
# at the source, so no pipeline is invented for it either. Every object in
# KNOWN_OBJECTS must be in exactly one of these two sets - the asserts catch
# a new object added to KNOWN_OBJECTS without updating them, at import time;
# RetrieveItem.__post_init__ catches it defensively too.
_OBJECTS_REQUIRING_PIPELINE = frozenset({"lesion"})
_OBJECTS_FORBIDDING_PIPELINE = frozenset({"feature", "sdc"})
assert _OBJECTS_REQUIRING_PIPELINE | _OBJECTS_FORBIDDING_PIPELINE == set(KNOWN_OBJECTS)
assert not (_OBJECTS_REQUIRING_PIPELINE & _OBJECTS_FORBIDDING_PIPELINE)


@dataclass(frozen=True)
class FilePatterns:
    """Registry of where to find a file on disk, for a given `object` and the
    path of keys below it - loaded from a JSON file (see load_file_patterns).
    Depth genuinely varies by object (`lesion` nests 3 levels, `feature` 2 -
    see docs/dev/retrieval.md) - read from the JSON, never assumed here. See
    RetrieveItem.path_key()/from_path() for the one place that maps between
    this tuple shape and typed fields. More than one template under the same
    leaf key means "grab every one that exists for this subject", not just
    the first found - see Dataset.resolve().
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

    def subject_discovery_keys(self) -> set[tuple[str, str | None]]:
        """Every distinct (object, pipeline) pair registered anywhere in this
        registry - pipeline is None for objects that don't use one. The axis
        subject folders are discovered under (see docs/dev/retrieval.md).
        Used by matrix.select_all_subjects and
        retrieve_data._known_object_pipelines to discover subjects across
        every pipeline of a requested object, not just the exact
        (object, pipeline) pairs a run's `retrieve` list happens to name."""
        return {(combo[0], RetrieveItem.from_path(*combo).pipeline) for combo in self.patterns}


@dataclass(frozen=True)
class RetrieveItem:
    """One (object, *path) leaf to retrieve, in BIDS-aligned vocabulary -
    `pipeline` required for objects in _OBJECTS_REQUIRING_PIPELINE, forbidden
    for _OBJECTS_FORBIDDING_PIPELINE (see docs/dev/retrieval.md for why
    "pipeline" isn't a formal BIDS entity). `datatype`/`suffix` are the
    BIDS-official terms (`suffix` is what this project used to call
    "modality" - BIDS reserves that word for acquisition technology).

    Field *shape* is not the same for every object - see path_key()/
    from_path() for the one place that maps between this and the flat tuple
    keys used by FilePatterns."""

    object: str
    pipeline: str | None
    datatype: str
    suffix: str

    def __post_init__(self) -> None:
        """Only `object` is a true structural constant, validated directly.
        `pipeline`'s required-or-forbidden-ness is also validated here (a
        per-object rule known statically) - unlike `datatype`/`suffix`,
        whose *validity* depends on the external file_patterns registry and
        can't be checked at construction time (see _require_known_combinations
        in load_config). The explicit if/elif/else: raise (not a 2-branch
        if/else, lesson #1) means a 3rd object added to KNOWN_OBJECTS
        without updating the two pipeline-requirement sets fails loudly here
        too, not just via the module-level assert."""
        if self.object not in KNOWN_OBJECTS:
            raise ValueError(f"RetrieveItem: unknown object {self.object!r} (known: {KNOWN_OBJECTS})")
        if self.object in _OBJECTS_REQUIRING_PIPELINE:
            if not self.pipeline:
                raise ValueError(f"RetrieveItem: object={self.object!r} requires a non-empty 'pipeline'")
        elif self.object in _OBJECTS_FORBIDDING_PIPELINE:
            if self.pipeline is not None:
                raise ValueError(
                    f"RetrieveItem: object={self.object!r} must not set 'pipeline' (got {self.pipeline!r}) "
                    "- BIDS defines no formal pipeline concept for this object, see docs/dev/retrieval.md"
                )
        else:
            raise ValueError(
                f"RetrieveItem: object={self.object!r} has no pipeline-requirement rule registered - "
                "add it to _OBJECTS_REQUIRING_PIPELINE or _OBJECTS_FORBIDDING_PIPELINE"
            )
        if not self.datatype:
            raise ValueError(f"RetrieveItem: 'datatype' must be a non-empty string, got {self.datatype!r}")
        if not self.suffix:
            raise ValueError(f"RetrieveItem: 'suffix' must be a non-empty string, got {self.suffix!r}")

    def path_key(self) -> tuple[str, ...]:
        """The (object, *path) tuple this item resolves to in
        file_patterns.json - includes `pipeline` only for objects that
        require one. Variable length by design, not a bug - see class
        docstring."""
        if self.pipeline is not None:
            return (self.object, self.pipeline, self.datatype, self.suffix)
        return (self.object, self.datatype, self.suffix)

    @classmethod
    def from_path(cls, *path: str) -> "RetrieveItem":
        """Inverse of path_key() - the one place that knows how many fields
        follow `object` for a given object, so callers (matrix.py
        especially) never need their own knowledge of the schema shape.
        Raises ValueError with the same object-requirement rules as
        __post_init__ if the shape doesn't match."""
        if not path:
            raise ValueError("RetrieveItem.from_path: empty path")
        object_, *rest = path
        if object_ in _OBJECTS_REQUIRING_PIPELINE:
            if len(rest) != 3:
                raise ValueError(
                    f"RetrieveItem.from_path: object={object_!r} expects (pipeline, datatype, suffix), got {rest}"
                )
            pipeline, datatype, suffix = rest
            return cls(object=object_, pipeline=pipeline, datatype=datatype, suffix=suffix)
        if object_ in _OBJECTS_FORBIDDING_PIPELINE:
            if len(rest) != 2:
                raise ValueError(
                    f"RetrieveItem.from_path: object={object_!r} expects (datatype, suffix), got {rest}"
                )
            datatype, suffix = rest
            return cls(object=object_, pipeline=None, datatype=datatype, suffix=suffix)
        raise ValueError(f"RetrieveItem.from_path: unknown object {object_!r} (known: {KNOWN_OBJECTS})")


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
            raise ValueError(f"file_patterns: object {object_!r} has no leaves registered")
        _walk_patterns(patterns, (object_,), rest)

    return FilePatterns(project_roots=project_roots, patterns=patterns)


def _walk_patterns(patterns: dict[tuple[str, ...], list[str]], prefix: tuple[str, ...], node: object) -> None:
    """Recursively parses a nested file_patterns node into flat
    `(object, *path) -> templates` entries - handles `lesion`'s 3 levels
    (pipeline, datatype, suffix) and `feature`'s 2 levels (datatype, suffix),
    without assuming a fixed shape."""
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
        datasets=_require_unique_str_list(raw, "datasets"),
        group_filter=_optional_group_filter(raw),
        subjects=_optional_unique_str_list(raw, "subjects"),
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


def _require_unique_str_list(raw: dict, key: str) -> list[str]:
    """Like _require_str_list(allow_empty=False), but also rejects duplicate
    entries explicitly rather than silently collapsing them - a duplicate
    dataset name would otherwise dedupe invisibly (Dataset instances are
    keyed by name in a dict in _build_datasets), masking what's very likely
    a copy-paste mistake in the config."""
    value = _require_str_list(raw, key, allow_empty=False)
    duplicates = {v for v in value if value.count(v) > 1}
    if duplicates:
        raise ValueError(f"config: field {key!r} contains duplicate entries: {sorted(duplicates)}")
    return value


def _optional_str_list(raw: dict, key: str) -> list[str] | None:
    if raw.get(key) is None:
        return None
    return _require_str_list(raw, key, allow_empty=False)


def _optional_unique_str_list(raw: dict, key: str) -> list[str] | None:
    """Same duplicate rejection as _require_unique_str_list, for an optional
    field (unlike `datasets`/`retrieve`, may legitimately be absent) - see
    `subjects`, which previously tolerated duplicates silently deduped
    downstream (_select_subjects' set intersection), inconsistent with the
    "reject, don't silently dedupe" convention this file applies to
    `datasets`/`retrieve` two fields away."""
    if raw.get(key) is None:
        return None
    value = _require_str_list(raw, key, allow_empty=False)
    duplicates = {v for v in value if value.count(v) > 1}
    if duplicates:
        raise ValueError(f"config: field {key!r} contains duplicate entries: {sorted(duplicates)}")
    return value


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
    """`pipeline` is required only for objects in _OBJECTS_REQUIRING_PIPELINE,
    and explicitly rejected (not silently dropped - code_standards.md §0) if
    present for an object in _OBJECTS_FORBIDDING_PIPELINE, so a config typo
    (setting `pipeline` on a `feature` entry, expecting it to matter) fails
    loudly instead of being ignored."""
    if not isinstance(item, dict) or "object" not in item:
        raise ValueError(f"config: each 'retrieve' entry must have an 'object' field, got {item!r}")
    object_ = item["object"]
    if not isinstance(object_, str) or not object_:
        raise ValueError(f"config: 'retrieve' entry field 'object' must be a non-empty string, got {object_!r}")
    if object_ not in KNOWN_OBJECTS:
        raise ValueError(f"config: 'retrieve' entry has unknown object {object_!r} (known: {KNOWN_OBJECTS})")

    if object_ in _OBJECTS_FORBIDDING_PIPELINE and "pipeline" in item:
        raise ValueError(
            f"config: 'retrieve' entry for object={object_!r} must not set 'pipeline' (got {item['pipeline']!r}) "
            "- BIDS defines no formal pipeline concept for this object, see docs/dev/retrieval.md"
        )
    required = ("pipeline", "datatype", "suffix") if object_ in _OBJECTS_REQUIRING_PIPELINE else ("datatype", "suffix")
    if not all(key in item for key in required):
        raise ValueError(
            f"config: 'retrieve' entry for object={object_!r} must have fields {required}, got {item!r}"
        )
    for key in required:
        if not isinstance(item[key], str) or not item[key]:
            raise ValueError(
                f"config: 'retrieve' entry field {key!r} must be a non-empty string, got {item[key]!r}"
            )
    pipeline = item["pipeline"] if object_ in _OBJECTS_REQUIRING_PIPELINE else None
    return RetrieveItem(object=object_, pipeline=pipeline, datatype=item["datatype"], suffix=item["suffix"])


def _reject_duplicate_retrieve_items(items: list[RetrieveItem]) -> None:
    """Two identical entries (same path_key()) would make the second one
    copy the exact same file to the exact same destination as the first,
    within the same run - it would show up as 'skipped (exists)' in the
    report, indistinguishable from a file genuinely already present from a
    previous run. Rejected upfront rather than silently deduplicated, so a
    copy-paste mistake in the config is never masked."""
    seen: set[tuple[str, ...]] = set()
    duplicates: set[tuple[str, ...]] = set()
    for item in items:
        key = item.path_key()
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        raise ValueError(f"config: field 'retrieve' contains duplicate entries: {sorted(duplicates)}")


def _require_known_combinations(retrieve: list[RetrieveItem], file_patterns: FilePatterns) -> None:
    """A combination requested in `retrieve` must be registered in the
    file_patterns registry - otherwise the request would only fail later,
    per-dataset, with a less direct error."""
    unknown = [item for item in retrieve if not file_patterns.has(*item.path_key())]
    if unknown:
        raise ValueError(
            "config: 'retrieve' requests combinations not registered in file_patterns: "
            f"{[item.path_key() for item in unknown]}"
        )
