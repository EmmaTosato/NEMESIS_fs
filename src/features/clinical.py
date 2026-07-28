"""Loading and target-extraction for clinical/behavioral/demographic fields in participants.tsv.

Used to join a lesion/FC feature matrix's subjects against behavioral deficit
scores (NIHSS, ARAT, 9HPT, Boston naming, Clock, Corsi - see
docs/guides/datasets.md) for the lesion-deficit vs FC-deficit prediction
pipeline (src/pipeline/predict_deficit.py), reproducing Siegel et al. 2016
(docs/knowledge/Siegel2016_Reproduction.md). join_lesion_side serves a
different consumer (dim_reduction.py's embedding_plot_side.*) but reads the
same per-dataset participants.tsv files, via the same load_participants.

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

# Fixed repo asset root (assets/metadata/<DATASET>_participants_lesions.tsv,
# "/" in the dataset name turned into "_") - same class of constant as
# dim_reduction.py's LOGS_ROOT: never swapped per run/environment, so it's a
# module constant (monkeypatchable in tests) rather than a config field.
METADATA_ROOT = Path("assets/metadata")

# Sentinel for a subject whose lesion_side cannot be resolved - either the
# whole dataset structurally lacks the column (e.g. PASPORT, which has
# lesion_volume_ml instead) or this one subject's value is missing/blank.
UNKNOWN_LESION_SIDE = "unknown"


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


def join_lesion_side(metadata: pd.DataFrame) -> pd.Series:
    """subject_id-aligned lesion_side, joined from one participants.tsv per
    unique dataset value in metadata["dataset"].

    metadata must have "subject_id" and "dataset" columns - the schema every
    matrix artifact's metadata.csv already has. Reads
    METADATA_ROOT/f"{dataset.replace('/', '_')}_participants_lesions.tsv" via
    load_participants, which raises FileNotFoundError if that file doesn't
    exist at all - an unresolvable dataset name is a real configuration
    problem (wrong data_root/naming), never silently papered over.

    A dataset whose participants.tsv exists but has no lesion_side column at
    all (e.g. PASPORT, which has lesion_volume_ml instead) is a known,
    structural per-dataset gap, not an error: every subject in that dataset
    gets UNKNOWN_LESION_SIDE, logged once at WARNING. A subject with a
    genuinely missing per-row value (blank/"n/a") in a dataset that does have
    the column also gets UNKNOWN_LESION_SIDE. Raises ValueError if a subject
    in metadata has no matching row at all in its dataset's participants.tsv
    (data mismatch between the matrix and the metadata registry - not a
    legitimate "missing" case).
    """
    if "subject_id" not in metadata.columns or "dataset" not in metadata.columns:
        raise ValueError(
            f"join_lesion_side needs 'subject_id' and 'dataset' columns, got {list(metadata.columns)}"
        )

    side_by_subject: dict[str, str] = {}
    for dataset in metadata["dataset"].unique():
        path = METADATA_ROOT / f"{dataset.replace('/', '_')}_participants_lesions.tsv"
        participants = load_participants(path)
        subject_ids = metadata.loc[metadata["dataset"] == dataset, "subject_id"]

        if "lesion_side" not in participants.columns:
            logging.warning(
                "dataset=%s: participants file %s has no lesion_side column - %d subject(s) marked %r",
                dataset, path, len(subject_ids), UNKNOWN_LESION_SIDE,
            )
            for subject_id in subject_ids:
                side_by_subject[subject_id] = UNKNOWN_LESION_SIDE
            continue

        side_lookup = participants.set_index("subject_id")["lesion_side"]
        for subject_id in subject_ids:
            if subject_id not in side_lookup.index:
                raise ValueError(
                    f"dataset={dataset}: subject {subject_id!r} not found in {path} - cannot resolve its lesion_side"
                )
            value = _normalize_missing(side_lookup.loc[subject_id])
            side_by_subject[subject_id] = UNKNOWN_LESION_SIDE if pd.isna(value) else str(value).strip()

    return metadata["subject_id"].map(side_by_subject)
