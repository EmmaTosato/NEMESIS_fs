"""A single dataset (one collection/name pair) inside a project.

Assumes the BIDS-like convention observed in Clinical_connectome:
sub-<DISEASE><SITE>[HC]<NUM>/anat/..., derivatives/manual_masks/... . This
holds for the 4 in-scope stroke datasets (UNIPD/WashU, UNIPD/PASPORT,
UNIPD/PSP, UKLFR/stroke_UKLFR). NEMESIS is not covered - its structure is
different and will be addressed separately when that work starts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.retrieval.config import FilePatterns

_SUBJECT_RE = re.compile(r"^sub-(?P<disease>ST|PD|GM)(?P<site>[A-Z]+?)(?P<hc>HC)?(?P<num>\d+)$")


@dataclass(frozen=True)
class ResolvedFile:
    """Result of Dataset.resolve(): the file to use, plus any other
    registered templates that also matched for the same subject (empty in
    the common case of exactly one match)."""

    path: Path
    extra_matches: tuple[Path, ...]


class Dataset:
    """One dataset (e.g. project='clinical_connectome', name='UNIPD/WashU')."""

    def __init__(self, project_root: Path, name: str, file_patterns: FilePatterns):
        self.name = name
        self.file_patterns = file_patterns
        # `lesion_root` points ONLY at the lesion data tree (native files and
        # its own derivatives/manual_masks/ subfolder) - it never resolves
        # anything under the separate `features/` tree. `space="native"` vs
        # `space="mni"` (see resolve()) are both subfolders inside this same
        # lesion_root, not two different roots.
        self.lesion_root = project_root / name
        self.features_root = project_root / "features" / name
        if not self.lesion_root.is_dir():
            raise FileNotFoundError(f"dataset root not found: {self.lesion_root}")

    def __repr__(self) -> str:
        return f"Dataset({self.name!r})"

    def subjects(self, group: str | None = None) -> list[str]:
        """List of subject_id (sub-* folders) that match the expected naming
        convention, optionally filtered by group. Folders starting with
        sub-* that don't match the convention are never included here -
        see non_conforming_subject_folders()."""
        ids = sorted(
            p.name
            for p in self.lesion_root.glob("sub-*")
            if p.is_dir() and _SUBJECT_RE.match(p.name)
        )
        if group is None:
            return ids
        return [s for s in ids if self.group_of(s) == group]

    def non_conforming_subject_folders(self) -> list[str]:
        """sub-* folders that exist on disk but don't match the expected
        naming convention - never returned by subjects(). Surfaced
        separately as a data-quality signal (relevant to the ongoing
        subject-ID standardization effort) instead of being silently
        absorbed as a fake subject, or left to crash group_of() only when a
        group filter happens to be used."""
        return sorted(
            p.name
            for p in self.lesion_root.glob("sub-*")
            if p.is_dir() and not _SUBJECT_RE.match(p.name)
        )

    def group_of(self, subject_id: str) -> str:
        """Group of a subject_id ('ST' | 'HC' | 'PD' | 'GM'), from its naming."""
        match = _SUBJECT_RE.match(subject_id)
        if match is None:
            raise ValueError(f"subject_id does not match expected naming: {subject_id!r}")
        return "HC" if match.group("hc") else match.group("disease")

    def _require_subject(self, subject_id: str) -> None:
        """Raise if subject_id does not exist in this dataset."""
        if subject_id not in self.subjects():
            raise ValueError(f"{subject_id!r} does not exist in dataset {self.name!r}")

    def available(self, space: str, modality: str) -> bool:
        """True if at least one subject in this dataset has a file matching
        any template registered for this (space, modality) - dataset-wide,
        not per-subject. A dataset can pass this check while most of its
        subjects individually lack the file (see resolve() for that case,
        surfaced as a per-subject miss, not a dataset-level failure)."""
        templates = self.file_patterns.templates_for(space, modality)
        return any(
            next(self.lesion_root.glob(template.replace("{subject_id}", "*")), None) is not None
            for template in templates
        )

    def resolve(self, subject_id: str, space: str, modality: str) -> ResolvedFile | None:
        """Path to the file for this subject/space/modality, or None if this
        subject doesn't have it.

        Raises ValueError if (space, modality) is not a combination the
        file_patterns registry knows about at all - a request this dataset
        can never satisfy, regardless of subject.

        If more than one registered template matches for this subject, the
        first one (by priority order in the registry) is returned as
        `.path`; the rest are returned as `.extra_matches` rather than
        silently discarded - two matching files for the same subject may be
        an equivalent naming variant, or may be a real data problem (e.g. a
        stale file left behind), and that distinction is for the report,
        not something to hide.
        """
        self._require_subject(subject_id)
        templates = self.file_patterns.templates_for(space, modality)
        candidates = [self.lesion_root / template.format(subject_id=subject_id) for template in templates]
        existing = [c for c in candidates if c.is_file()]
        if not existing:
            return None
        return ResolvedFile(path=existing[0], extra_matches=tuple(existing[1:]))

    def describe_absence(self, subject_id: str, space: str, modality: str) -> str:
        """Why resolve() returned None for this (subject, space, modality) -
        call only once that's already been confirmed, this does not
        re-check. "empty folder" if the directory that would hold the file
        (the parent of the highest-priority registered template) exists but
        has nothing in it at all - the file was simply never produced for
        this subject. "not found" for every other case (the directory
        doesn't exist, or has other content but not this file). Reporting
        only - resolve()/available() never call this."""
        template = self.file_patterns.templates_for(space, modality)[0]
        folder = (self.lesion_root / template.format(subject_id=subject_id)).parent
        if folder.is_dir() and not any(folder.iterdir()):
            return "empty folder"
        return "not found"

    def participants_tsv_path(self) -> Path | None:
        """Path to participants.tsv, or None if this dataset has none (e.g. WashU)."""
        path = self.lesion_root / "participants.tsv"
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
