"""Loading and target-extraction for clinical/behavioral scores in participants.tsv.

Used to join a lesion/FC feature matrix's subjects against behavioral deficit
scores (NIHSS, ARAT, 9HPT, Boston naming, Clock, Corsi - see
docs/guides/datasets.md) for the lesion-deficit vs FC-deficit prediction
pipeline (src/pipeline/predict_deficit.py), reproducing Siegel et al. 2016
(docs/knowledge/Siegel2016_Reproduction.md).

participants.tsv's own subject-id column is "participant_id" - renamed to
"subject_id" here, to match the join key already used by every matrix
artifact's metadata.csv (src/utils/artifacts.py).
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

# The only missing-value sentinel observed in the real WashU participants.tsv
# (verified 27/07/26) - a genuinely empty field is already turned into a real
# NaN by pandas' own default NA handling in read_csv, even under dtype=str.
_MISSING_SENTINEL = "n/a"


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


def extract_target(participants: pd.DataFrame, target: str) -> pd.DataFrame:
    """subject_id + target score, numeric, with missing rows dropped explicitly.

    Raises ValueError if target isn't a column of participants, if it
    contains a non-numeric non-missing value (data corruption - never
    silently coerced to NaN), or if every value is missing (target unusable
    for this cohort, e.g. GDS_15 on the WashU FC cohort - docs/guides/datasets.md).
    """
    if target not in participants.columns:
        raise ValueError(f"unknown behavioral target {target!r} - not a column of participants.tsv")

    raw = participants[["subject_id", target]].copy()
    raw[target] = raw[target].map(_normalize_missing)
    try:
        raw[target] = pd.to_numeric(raw[target], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"target {target!r}: contains a non-numeric, non-missing value ({exc})") from exc

    n_total = len(raw)
    extracted = raw.dropna(subset=[target]).reset_index(drop=True)
    n_dropped = n_total - len(extracted)
    logging.info(
        "target=%s: %d/%d subjects have a usable score (%d dropped, missing)",
        target, len(extracted), n_total, n_dropped,
    )
    if extracted.empty:
        raise ValueError(f"target {target!r} has no usable (non-missing) values in this participants.tsv")

    return extracted


def _normalize_missing(value: object) -> object:
    if pd.isna(value):
        return np.nan
    return np.nan if str(value).strip() == _MISSING_SENTINEL else value
