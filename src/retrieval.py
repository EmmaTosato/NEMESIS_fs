"""Retrieval dei dati di un dataset di lesioni.

La classe :class:`Dataset` rappresenta UN dataset (una cartella root) e sa
risolvere il path di un file per un dato soggetto. Assume la convenzione di
cartelle osservata in ``Clinical_connectome`` (BIDS-like):

    <root>/
    ├── sub-<ID>/anat/<sub>_<sequence>.nii.gz        # sequenze native
    │                 <sub>_..._lesion_roi.nii.gz    # lesione in spazio nativo
    └── derivatives/manual_masks/sub-<ID>/anat/
            <sub>_space-MNI152NLin6Asym_label-lesion_mask.nii.gz   # lesione in MNI

I nomi soggetto seguono ``sub-<DISEASE><SITE>[HC]<NUM>`` (es. ``sub-STUNIPD0002``,
``sub-STUNIPDHC0028``).

NEMESIS ha una struttura diversa e non è gestito qui: quando servirà si valuterà
se estendere questa classe o scriverne un'altra.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# Sequenze anat note. `lesion_roi` è la lesione in spazio nativo, trattata come
# una "sequenza" in più (risolta con glob permissivo per le due varianti di nome).
KNOWN_SEQUENCES = ("T1w", "T2w", "FLAIR", "CT", "lesion_roi")

_SUBJECT_RE = re.compile(r"^sub-(?P<disease>ST|PD|GM)(?P<site>[A-Z]+?)(?P<hc>HC)?(?P<num>\d+)$")


def subject_group(subject_id: str) -> str:
    """Gruppo del soggetto dal naming ``sub-<DISEASE><SITE>[HC]<NUM>``.

    Ritorna ``'HC'`` per i controlli sani (suffisso HC), altrimenti il codice
    malattia (``'ST'`` / ``'PD'`` / ``'GM'``).
    """
    m = _SUBJECT_RE.match(subject_id)
    if m is None:
        raise ValueError(f"subject_id non riconosciuto: {subject_id!r}")
    return "HC" if m.group("hc") else m.group("disease")


class Dataset:
    """Un dataset di lesioni (una cartella root)."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        if not self.root.is_dir():
            raise FileNotFoundError(f"root del dataset inesistente: {self.root}")
        self.name = self.root.name

    def __repr__(self) -> str:
        return f"Dataset({self.name!r})"

    # --- soggetti ---------------------------------------------------------

    def subjects(self, group: str | None = None) -> list[str]:
        """Lista ordinata dei subject_id (cartelle ``sub-*``).

        ``group`` opzionale (es. ``'ST'``, ``'HC'``) filtra per gruppo.
        """
        ids = sorted(p.name for p in self.root.glob("sub-*") if p.is_dir())
        if group is not None:
            ids = [s for s in ids if subject_group(s) == group]
        return ids

    def group_of(self, subject_id: str) -> str:
        """Gruppo del soggetto (vedi :func:`subject_group`)."""
        return subject_group(subject_id)

    # --- disponibilità (scoperta dai dati) --------------------------------

    def available_sequences(self) -> set[str]:
        """Sequenze anat effettivamente presenti nel dataset (almeno un soggetto)."""
        found = set()
        for seq in KNOWN_SEQUENCES:
            if next(self.root.glob(f"sub-*/anat/*_{seq}.nii.gz"), None) is not None:
                found.add(seq)
        return found

    def has_derivatives(self) -> bool:
        """True se esiste almeno una maschera di lesione in MNI (derivatives)."""
        pattern = "derivatives/manual_masks/sub-*/anat/*_label-lesion_mask.nii.gz"
        return next(self.root.glob(pattern), None) is not None

    # --- risoluzione file (Path se esiste, None se manca per il soggetto) --

    def anat(self, subject_id: str, sequence: str) -> Path | None:
        """Path della sequenza ``anat`` nativa, o ``None`` se manca per il soggetto.

        Solleva ``ValueError`` se la sequenza non è tra quelle note o se il
        dataset non la contiene affatto (combinazione strutturalmente impossibile).
        """
        if sequence not in KNOWN_SEQUENCES:
            raise ValueError(
                f"sequenza sconosciuta: {sequence!r} (attese: {', '.join(KNOWN_SEQUENCES)})"
            )
        if sequence not in self.available_sequences():
            raise ValueError(
                f"il dataset {self.name!r} non contiene la sequenza {sequence!r}"
            )
        # `*_<seq>.nii.gz` cattura anche le due varianti di lesion_roi
        # (`_lesion_roi` e `_space-T1w_lesion_roi`).
        match = next((self.root / subject_id / "anat").glob(f"*_{sequence}.nii.gz"), None)
        return match

    def lesion_mask(self, subject_id: str) -> Path | None:
        """Path della maschera di lesione in MNI (derivatives), o ``None`` se manca.

        Solleva ``ValueError`` se il dataset non ha affatto i derivatives.
        """
        if not self.has_derivatives():
            raise ValueError(f"il dataset {self.name!r} non contiene derivatives (manual_masks)")
        anat_dir = self.root / "derivatives" / "manual_masks" / subject_id / "anat"
        match = next(anat_dir.glob("*_label-lesion_mask.nii.gz"), None)
        return match

    # --- metadata ---------------------------------------------------------

    def participants(self) -> pd.DataFrame | None:
        """``participants.tsv`` come DataFrame, o ``None`` se assente (es. WashU)."""
        path = self.root / "participants.tsv"
        if not path.is_file():
            return None
        return pd.read_csv(path, sep="\t", dtype=str)
