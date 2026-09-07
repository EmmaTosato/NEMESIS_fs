"""The project's single subject registry: assets/metadata/participants.csv.

One row per subject, written by scripts/populate_metadata.py (who exists) and
src/pipeline/enrich_metadata.py (what we know about them). This module is the
read side: every pipeline that needs to know which subjects exist, or which of
them have a lesion mask, goes through here rather than globbing data/ (a local
copy can be a partial retrieval sample) or re-reading a raw participants.tsv.

Replaces the retired src/features/clinical.py, whose per-dataset
assets/metadata/<DATASET>_participants_lesions.tsv files no longer exist - see
docs/dev/metadata.md.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

METADATA_ROOT = Path("assets/metadata")

# Consolidated subject registry written by scripts/populate_metadata.py - the
# single source of truth for which subjects exist and what each one has on
# disk (docs/dev/metadata.md). Same class of constant as METADATA_ROOT: fixed
# repo asset, never swapped per run, monkeypatchable in tests.
_PARTICIPANTS_CSV_NAME = "participants.csv"


def participants_registry_path() -> Path:
    """Path of the consolidated subject registry.

    Resolved at call time from METADATA_ROOT (not bound once at import) so
    tests can redirect the whole metadata root with a single monkeypatch -
    same convention the retired participants_tsv_path() followed.
    """
    return METADATA_ROOT / _PARTICIPANTS_CSV_NAME

_REGISTRY_FLAG_COLUMNS = ("has_lesion", "has_sdc", "has_features")
_REGISTRY_REQUIRED_COLUMNS = ("subject_id", "dataset", *_REGISTRY_FLAG_COLUMNS)
_REGISTRY_BOOL_VALUES = {"True": True, "False": False}


def load_participants_registry(path: Path | None = None) -> pd.DataFrame:
    """Read assets/metadata/participants.csv, with the has_* flags as real bools.

    Read with dtype=str (docs/dev/metadata.md: never let pandas re-type a
    subject id or strip a leading zero), then the has_* columns are converted
    explicitly: anything that is not literally "True"/"False" raises rather
    than being coerced - a blank or "n/a" flag means the registry is
    incomplete, which is not the same fact as "this subject has no lesion".

    Raises FileNotFoundError if the registry doesn't exist (it is written by
    scripts/populate_metadata.py, not by any pipeline that reads it), and
    ValueError if a required column is missing or a flag is unparseable.
    """
    path = participants_registry_path() if path is None else Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"subject registry not found: {path} - it is written by scripts/populate_metadata.py "
            "(see docs/dev/metadata.md); no pipeline regenerates it on the fly"
        )

    registry = pd.read_csv(path, dtype=str)
    missing = [c for c in _REGISTRY_REQUIRED_COLUMNS if c not in registry.columns]
    if missing:
        raise ValueError(f"{path}: missing required column(s) {missing}, got {list(registry.columns)}")

    for column in _REGISTRY_FLAG_COLUMNS:
        unparseable = sorted(set(registry[column].dropna()) - set(_REGISTRY_BOOL_VALUES))
        if unparseable or registry[column].isna().any():
            raise ValueError(
                f"{path}: column {column!r} must be exactly 'True'/'False' for every row, "
                f"found {unparseable or ['<empty>']}"
            )
        registry[column] = registry[column].map(_REGISTRY_BOOL_VALUES)

    duplicates = sorted(registry.loc[registry["subject_id"].duplicated(), "subject_id"])
    if duplicates:
        raise ValueError(f"{path}: duplicate subject_id rows: {duplicates}")
    return registry


def load_participants(path: Path) -> pd.DataFrame:
    """Read participants.tsv, rename participant_id -> subject_id.

    Raises FileNotFoundError if path doesn't exist, ValueError if the
    expected participant_id column is absent (wrong/malformed file - never
    guessed at from a different column name).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"participants.tsv not found: {path}")

    participants = pd.read_csv(path, sep="\t", dtype=str)
    if "participant_id" not in participants.columns:
        raise ValueError(
            f"{path}: expected a 'participant_id' column, got {list(participants.columns)}"
        )
    return participants.rename(columns={"participant_id": "subject_id"})
