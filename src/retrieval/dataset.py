"""A single dataset (one collection/name pair) inside a project.

Assumes the BIDS-like convention observed in Clinical_connectome:
sub-<DISEASE><SITE>[HC]<NUM>/anat/..., derivatives/manual_masks/... . This
holds for the 4 in-scope stroke datasets (UNIPD/WashU, UNIPD/PASPORT,
UNIPD/PSP, UKLFR/stroke_UKLFR). NEMESIS is not covered - its structure is
different and will be addressed separately when that work starts.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.retrieval.config import NATIVE_MODALITIES

_SUBJECT_RE = re.compile(r"^sub-(?P<disease>ST|PD|GM)(?P<site>[A-Z]+?)(?P<hc>HC)?(?P<num>\d+)$")


class Dataset:
    """One dataset (e.g. project='clinical_connectome', name='UNIPD/WashU')."""

    def __init__(self, project_root: Path, name: str):
        self.name = name
        # `lesion_root` points ONLY at the lesion data tree (native files and
        # its own derivatives/manual_masks/ subfolder) - it never resolves
        # anything under the separate `features/` tree. `space="native"` vs
        # `space="mni"` (see native()/mni_mask()) are both subfolders inside
        # this same lesion_root, not two different roots.
        self.lesion_root = project_root / name
        self.features_root = project_root / "features" / name
        if not self.lesion_root.is_dir():
            raise FileNotFoundError(f"dataset root not found: {self.lesion_root}")

    def __repr__(self) -> str:
        return f"Dataset({self.name!r})"

    def subjects(self, group: str | None = None) -> list[str]:
        """List of subject_id (sub-* folders), optionally filtered by group."""
        ids = sorted(p.name for p in self.lesion_root.glob("sub-*") if p.is_dir())
        if group is None:
            return ids
        return [s for s in ids if self.group_of(s) == group]

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

    def available_sequences(self) -> set[str]:
        """Native modalities actually present in this dataset (discovered from disk)."""
        return {
            modality
            for modality in NATIVE_MODALITIES
            if next(self.lesion_root.glob(f"sub-*/anat/*_{modality}.nii.gz"), None) is not None
        }

    def has_mni_mask(self) -> bool:
        """True if this dataset has any MNI-space lesion mask (derivatives/manual_masks)."""
        pattern = "derivatives/manual_masks/sub-*/anat/*_label-lesion_mask.nii.gz"
        return next(self.lesion_root.glob(pattern), None) is not None

    def native(self, subject_id: str, modality: str) -> Path | None:
        """Path to a native-space file, or None if missing for this subject.

        Raises ValueError if `modality` is not structurally available anywhere
        in this dataset - a request this dataset can never satisfy.
        """
        self._require_subject(subject_id)
        available = self.available_sequences()
        if modality not in available:
            raise ValueError(
                f"dataset {self.name!r} does not have modality {modality!r} "
                f"(available: {sorted(available)})"
            )
        # native files live under the BIDS "anat" datatype folder on disk.
        native_dir = self.lesion_root / subject_id / "anat"
        # `*_<modality>.nii.gz` also matches the two lesion_roi naming variants
        # (`_lesion_roi.nii.gz` and `_space-T1w_lesion_roi.nii.gz`).
        return next(native_dir.glob(f"*_{modality}.nii.gz"), None)

    def mni_mask(self, subject_id: str) -> Path | None:
        """Path to the MNI-space lesion mask (derivatives), or None if missing for this subject.

        Raises ValueError if this dataset has no derivatives/manual_masks at all.

        NOTE: this method is hardcoded to the single derivative that exists today
        (derivatives/manual_masks). `space="mni"` is not a generic "search any
        MNI-space file" lookup - it only works because manual_masks is currently
        the only derivative, and it happens to be in MNI space. If a second
        derivative appears (in MNI space or otherwise), this method will not
        find it; disambiguating between multiple derivatives (e.g. via a
        `derivative` selector alongside `space`) is a design decision to make
        when that second derivative actually exists, not now.
        """
        self._require_subject(subject_id)
        if not self.has_mni_mask():
            raise ValueError(f"dataset {self.name!r} has no derivatives/manual_masks")
        # the mask lives under derivatives/manual_masks/<subject>/anat/ on disk
        # (BIDS reuses the "anat" datatype label here too, unrelated to space=native).
        mask_dir = self.lesion_root / "derivatives" / "manual_masks" / subject_id / "anat"
        return next(mask_dir.glob("*_label-lesion_mask.nii.gz"), None)

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
