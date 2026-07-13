"""A single dataset (one collection/name pair) inside a project.

Assumes the BIDS-like convention observed in Clinical_connectome:
sub-<DISEASE><SITE>[HC]<NUM>/anat/..., derivatives/manual_masks/... . This
holds for the 4 in-scope stroke datasets (UNIPD/WashU, UNIPD/PASPORT,
UNIPD/PSP, UKLFR/stroke_UKLFR). NEMESIS is not covered - its structure is
different and will be addressed separately when that work starts.

Nothing here trusts a fixed root per `object` - `lesion` and `feature` each
have their own `project_root` (see config.FilePatterns), and even within one
object, different `space` values can have their subject folders living under
different sub-paths (e.g. `lesion` native subjects sit directly under the
dataset root, but `lesion` mni subjects sit under
`derivatives/manual_masks/`). Where subject folders for an (object, space)
actually live is derived from the registered templates themselves, never
assumed - see _subject_container().
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.retrieval.config import FilePatterns, RetrieveItem

_SUBJECT_RE = re.compile(r"^sub-(?P<disease>ST|PD|GM)(?P<site>[A-Z]+?)(?P<hc>HC)?(?P<num>\d+)$")


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

    def _subject_container(self, object_: str, space: str) -> Path:
        """Directory whose immediate sub-folders are subject folders, for
        this (object, space) - derived from wherever `{subject_id}` sits as
        its own path segment in the highest-priority registered template for
        any modality under this (object, space). Never assumes subjects live
        directly under the object's root: for `lesion`/`native` they do
        (`{subject_id}/anat/...`), but for `lesion`/`mni` they sit under
        `derivatives/manual_masks/{subject_id}/...` instead - deriving this
        from the template, rather than hardcoding one shape, is what lets a
        subject that only exists in one space (e.g. a derivative with no
        matching native folder) still be discovered."""
        combos = [c for c in self.file_patterns.combinations_for(object_) if c[1] == space]
        if not combos:
            raise ValueError(f"no modality registered for object={object_!r} space={space!r}")
        template = self.file_patterns.templates_for(*combos[0])[0]
        segments = template.split("/")
        if "{subject_id}" not in segments:
            raise ValueError(
                f"template {template!r} for object={object_!r} space={space!r} does not have "
                "{subject_id} as its own path segment - cannot derive where subject folders live"
            )
        subject_index = segments.index("{subject_id}")
        root = self._root_for(object_)
        return root.joinpath(*segments[:subject_index]) if subject_index else root

    def subjects(self, object_: str, space: str, group: str | None = None) -> list[str]:
        """List of subject_id (sub-* folders) that match the expected naming
        convention, for this (object, space), optionally filtered by group.
        Folders starting with sub-* that don't match the convention are
        never included here - see non_conforming_subject_folders()."""
        container = self._subject_container(object_, space)
        ids = sorted(
            p.name for p in container.glob("sub-*") if p.is_dir() and _SUBJECT_RE.match(p.name)
        )
        if group is None:
            return ids
        return [s for s in ids if self.group_of(s) == group]

    def non_conforming_subject_folders(self, object_: str, space: str) -> list[str]:
        """sub-* folders that exist on disk for this (object, space) but
        don't match the expected naming convention - never returned by
        subjects(). Surfaced separately as a data-quality signal (relevant to
        the ongoing subject-ID standardization effort) instead of being
        silently absorbed as a fake subject, or left to crash group_of() only
        when a group filter happens to be used."""
        container = self._subject_container(object_, space)
        return sorted(
            p.name for p in container.glob("sub-*") if p.is_dir() and not _SUBJECT_RE.match(p.name)
        )

    def group_of(self, subject_id: str) -> str:
        """Group of a subject_id ('ST' | 'HC' | 'PD' | 'GM'), from its naming."""
        match = _SUBJECT_RE.match(subject_id)
        if match is None:
            raise ValueError(f"subject_id does not match expected naming: {subject_id!r}")
        return "HC" if match.group("hc") else match.group("disease")

    def available(self, object_: str, space: str, modality: str) -> bool:
        """True if at least one subject has a file matching any template
        registered for this (object, space, modality) - dataset-wide, not
        per-subject. A dataset can pass this check while most of its
        subjects individually lack the file (see resolve() for that case,
        surfaced as a per-subject miss, not a dataset-level failure)."""
        root = self._root_for(object_)
        templates = self.file_patterns.templates_for(object_, space, modality)
        return any(
            next(root.glob(template.replace("{subject_id}", "*")), None) is not None
            for template in templates
        )

    def resolve(self, subject_id: str, item: RetrieveItem) -> list[Path]:
        """Every existing file for this subject matching any template
        registered for (item.object, item.space, item.modality) - not just
        the first found. There is no priority/ambiguity concept: if more
        than one registered template exists for this subject, all of them
        are returned (and, by the caller, all of them copied) - see
        FilePatterns docstring. Empty list if the subject has none of them;
        this covers both "subject exists but lacks this file" and "subject
        doesn't exist at all in this object/space's container" identically,
        since both simply produce no matching path on disk - resolve() never
        needs to check subject existence separately.

        Raises ValueError if (item.object, item.space, item.modality) is not
        a registered combination at all - a request the registry has no
        answer for, regardless of subject. Should never be reachable in the
        normal CLI flow (config._require_known_combinations already rejects
        this at load time); defensive for direct/programmatic use.
        """
        root = self._root_for(item.object)
        templates = self.file_patterns.templates_for(item.object, item.space, item.modality)
        candidates = [root / template.format(subject_id=subject_id) for template in templates]
        return [c for c in candidates if c.is_file()]

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
        template = self.file_patterns.templates_for(item.object, item.space, item.modality)[0]
        folder = (root / template.format(subject_id=subject_id)).parent
        if folder.is_dir() and not any(folder.iterdir()):
            return "empty folder"
        return "not found"

    def participants_tsv_path(self) -> Path | None:
        """Path to participants.tsv, or None if this dataset has none (e.g.
        WashU). Always relative to the `lesion` object's root - participants
        metadata is a property of the clinical dataset, not of any one
        space/modality."""
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
