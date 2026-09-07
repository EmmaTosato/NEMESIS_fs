"""A single dataset (one collection/name pair) inside a project.

Assumes the BIDS-like convention observed in Clinical_connectome:
sub-<DISEASE><SITE>[HC]<NUM>/anat/..., derivatives/manual_masks/... - see
docs/dev/retrieval.md for the exact in-scope datasets. NEMESIS is not
covered - its structure is different and will be addressed separately when
that work starts.

Nothing here trusts a fixed root per `object` - `lesion` and `feature` each
have their own `project_root` (see config.FilePatterns), and different
`pipeline` values can have their subject folders living under different
sub-paths. Where subject folders for an (object, pipeline) actually live is
derived from the registered templates themselves, never assumed - see
_subject_container().
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.retrieval.config import FilePatterns, RetrieveItem

# Every site code seen across the in-scope datasets' real subject IDs -
# deliberately a closed, explicit list, not `[A-Z]+?` free-form matching
# (see docs/dev/retrieval.md's "Subject-group naming" section for why).
KNOWN_SITES = ("UNIPD", "UKLFR", "UCLUK", "UKE")
_SITE_ALTERNATION = "|".join(sorted(KNOWN_SITES, key=len, reverse=True))
_SUBJECT_RE = re.compile(rf"^sub-(?P<disease>ST|PD|GM)(?P<site>{_SITE_ALTERNATION})(?P<hc>HC)?(?P<num>\d+)$")


def group_of(subject_id: str) -> str:
    """Group of a subject_id ('ST' | 'HC' | 'PD' | 'GM'), from its naming -
    module-level (not just Dataset.group_of) so any layer that discovers
    subjects by globbing directly (e.g. src/features/functional.py) can
    still tell a healthy control from a patient without duplicating
    _SUBJECT_RE. Raises ValueError both for a malformed subject_id and for
    one whose site code isn't in KNOWN_SITES (see docs/dev/retrieval.md) -
    a genuinely new site must be added by a human, never inferred.
    """
    match = _SUBJECT_RE.match(subject_id)
    if match is None:
        raise ValueError(f"subject_id does not match expected naming: {subject_id!r}")
    return "HC" if match.group("hc") else match.group("disease")


def _subject_id_pattern(template: str) -> re.Pattern[str]:
    """Regex for template with every "{subject_id}" occurrence bound to the
    same value via a backreference (first occurrence a named group, every
    later one (?P=subject_id)) - used by Dataset.available() so a template
    with {subject_id} in more than one path segment can't be satisfied by a
    file whose segments disagree on which subject it belongs to (see
    available()'s own docstring). Every other character is escaped, so only
    the placeholder itself is treated as a pattern."""
    escaped_chunks = [re.escape(chunk) for chunk in template.split("{subject_id}")]
    pieces = [escaped_chunks[0]]
    for i, chunk in enumerate(escaped_chunks[1:]):
        pieces.append("(?P<subject_id>[^/]+)" if i == 0 else "(?P=subject_id)")
        pieces.append(chunk)
    return re.compile("^" + "".join(pieces) + "$")


class Dataset:
    """One dataset (e.g. project='clinical_connectome', name='UNIPD/WashU').

    Holds no filesystem state at construction - every root/path is resolved
    lazily, per `object`, from `file_patterns` (see _root_for). A missing
    dataset root still surfaces early in practice, since the pipeline always
    calls subjects()/available() during upfront validation, before any file
    is copied.
    """

    def __init__(self, name: str, file_patterns: FilePatterns):
        self.name = name
        self.file_patterns = file_patterns

    def __repr__(self) -> str:
        return f"Dataset({self.name!r})"

    def _root_for(self, object_: str) -> Path:
        root = self.file_patterns.project_root_for(object_) / self.name
        if not root.is_dir():
            raise FileNotFoundError(f"dataset root not found: {root}")
        return root

    def has_object(self, object_: str) -> bool:
        """True if this dataset actually has a root on disk for this object -
        e.g. some datasets have no `features/` tree at all yet (feature
        extraction not run for them, while `lesion` always exists). For a
        specifically-requested object, a missing root is a real error
        (_root_for raises) - this method is for callers that iterate every
        object the registry knows about regardless of relevance (e.g.
        subject-discovery callers), where "this object simply
        doesn't apply to this dataset" is a legitimate outcome, not a
        failure."""
        try:
            self._root_for(object_)
            return True
        except FileNotFoundError:
            return False

    def _subject_container(self, object_: str, pipeline: str | None) -> Path:
        """Directory whose immediate sub-folders are subject folders, for
        this (object, pipeline) - derived from wherever `{subject_id}` sits
        as its own path segment in the highest-priority registered template
        for any leaf under this (object, pipeline). Never assumes subjects
        live directly under the object's root: for `lesion`/`manual_masks`
        they sit under `derivatives/manual_masks/{subject_id}/...`, but for
        `feature` (no pipeline) they sit directly under `{subject_id}/...` -
        deriving this from the template, rather than hardcoding one shape, is
        what lets a subject that only exists under one pipeline still be
        discovered."""
        combos = [
            c for c in self.file_patterns.combinations_for(object_)
            if RetrieveItem.from_path(*c).pipeline == pipeline
        ]
        if not combos:
            raise ValueError(f"no leaf registered for object={object_!r} pipeline={pipeline!r}")
        template = self.file_patterns.templates_for(*combos[0])[0]
        segments = template.split("/")
        if "{subject_id}" not in segments:
            raise ValueError(
                f"template {template!r} for object={object_!r} pipeline={pipeline!r} does not have "
                "{subject_id} as its own path segment - cannot derive where subject folders live"
            )
        subject_index = segments.index("{subject_id}")
        root = self._root_for(object_)
        return root.joinpath(*segments[:subject_index]) if subject_index else root

    def subjects(self, object_: str, pipeline: str | None, group: str | None = None) -> list[str]:
        """List of subject_id (sub-* folders) that match the expected naming
        convention, for this (object, pipeline), optionally filtered by
        group. Folders starting with sub-* that don't match the convention
        are never included here - see non_conforming_subject_folders()."""
        container = self._subject_container(object_, pipeline)
        ids = sorted(
            p.name for p in container.glob("sub-*") if p.is_dir() and _SUBJECT_RE.match(p.name)
        )
        if group is None:
            return ids
        return [s for s in ids if self.group_of(s) == group]

    def non_conforming_subject_folders(self, object_: str, pipeline: str | None) -> list[str]:
        """sub-* folders that exist on disk for this (object, pipeline) but
        don't match the expected naming convention - never returned by
        subjects(). Surfaced separately as a data-quality signal (relevant to
        the ongoing subject-ID standardization effort) instead of being
        silently absorbed as a fake subject, or left to crash group_of() only
        when a group filter happens to be used."""
        container = self._subject_container(object_, pipeline)
        return sorted(
            p.name for p in container.glob("sub-*") if p.is_dir() and not _SUBJECT_RE.match(p.name)
        )

    def group_of(self, subject_id: str) -> str:
        """Group of a subject_id ('ST' | 'HC' | 'PD' | 'GM'), from its naming."""
        return group_of(subject_id)

    def available(self, item: RetrieveItem) -> bool:
        """True if at least one subject has a file matching any template
        registered for item.path_key() - dataset-wide, not per-subject. A
        dataset can pass this check while most of its subjects individually
        lack the file (see resolve() for that case, surfaced as a
        per-subject miss, not a dataset-level failure).

        A template with {subject_id} in more than one path segment requires
        every occurrence to bind to the SAME subject, checked via
        _subject_id_pattern's backreferenced regex, not independent glob
        wildcards (see docs/dev/retrieval.md, lesson #22)."""
        root = self._root_for(item.object)
        templates = self.file_patterns.templates_for(*item.path_key())
        for template in templates:
            pattern = _subject_id_pattern(template)
            for candidate in root.glob(template.replace("{subject_id}", "*")):
                if pattern.match(candidate.relative_to(root).as_posix()):
                    return True
        return False

    def _candidates(self, subject_id: str, item: RetrieveItem) -> list[tuple[str, Path]]:
        """Every (template, path) pair registered for item.path_key(), for
        this subject - whether or not the path actually exists on disk.
        Single source of truth for how a template string maps to a candidate
        path, shared by resolve() (what matched) and missing_templates()
        (what didn't) so the two can never drift out of sync with each
        other."""
        root = self._root_for(item.object)
        templates = self.file_patterns.templates_for(*item.path_key())
        return [(template, root / template.format(subject_id=subject_id)) for template in templates]

    def resolve(self, subject_id: str, item: RetrieveItem) -> list[Path]:
        """Every existing file for this subject matching any template
        registered for item.path_key() - not just the first found, no
        priority/ambiguity concept (see docs/dev/retrieval.md). Empty list
        covers both "subject exists but lacks this file" and "subject
        doesn't exist at all" identically - resolve() never checks subject
        existence separately.

        Raises ValueError if item.path_key() isn't a registered combination
        at all - should never be reachable in the normal CLI flow
        (config._require_known_combinations already rejects this at load
        time); defensive for direct/programmatic use.
        """
        return [path for _, path in self._candidates(subject_id, item) if path.is_file()]

    def missing_templates(self, subject_id: str, item: RetrieveItem) -> list[str]:
        """Which of item.path_key()'s registered templates have no matching
        file for this subject - the complement of resolve(), same candidate
        list. Used only for reporting (see
        retrieve_data._incomplete_message): resolve() itself never needs
        this, it only cares about what DID match. Raises ValueError under
        the same condition as resolve() (unregistered item.path_key())."""
        return [template for template, path in self._candidates(subject_id, item) if not path.is_file()]

    def describe_absence(self, subject_id: str, item: RetrieveItem) -> str:
        """Why resolve() returned [] for this (subject, item) - call only
        once that's already been confirmed, this does not re-check. "empty
        folder" if the directory that would hold the file (the parent of the
        highest-priority registered template) exists but has nothing in it
        at all - the file was simply never produced for this subject. "not
        found" for every other case (the directory doesn't exist, or has
        other content but not this file). Reporting only - resolve()/
        available() never call this."""
        root = self._root_for(item.object)
        template = self.file_patterns.templates_for(*item.path_key())[0]
        folder = (root / template.format(subject_id=subject_id)).parent
        if folder.is_dir() and not any(folder.iterdir()):
            return "empty folder"
        return "not found"

    def participants_tsv_path(self) -> Path | None:
        """Path to participants.tsv, or None if this dataset has none (e.g.
        WashU). Always relative to the `lesion` object's root - participants
        metadata is a property of the clinical dataset, not of any one
        pipeline/datatype/suffix."""
        path = self._root_for("lesion") / "participants.tsv"
        return path if path.is_file() else None

    def participants(self) -> pd.DataFrame | None:
        """Contents of participants.tsv as a DataFrame, or None if this dataset has none.

        Absence is a legitimate, documented per-dataset fact (e.g. WashU has no
        participants.tsv), not an error.
        """
        path = self.participants_tsv_path()
        if path is None:
            return None
        return pd.read_csv(path, sep="\t", dtype=str)
