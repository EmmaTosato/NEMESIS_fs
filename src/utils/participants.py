"""The project's single subject registry: assets/metadata/participants.csv.

One row per subject, written by src/pipeline/populate_metadata.py (who exists) and
src/pipeline/enrich_metadata.py (what we know about them). This module is the
read side: every pipeline that needs to know which subjects exist, or which of
them have a lesion mask, goes through here rather than globbing data/ (a local
copy can be a partial local sample) or re-reading a raw participants.tsv.

Replaces the retired src/features/clinical.py, whose per-dataset
assets/metadata/<DATASET>_participants_lesions.tsv files no longer exist - see
docs/dev/metadata.md.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

METADATA_ROOT = Path("assets/metadata")

# Consolidated subject registry written by src/pipeline/populate_metadata.py - the
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
    src/pipeline/populate_metadata.py, not by any pipeline that reads it), and
    ValueError if a required column is missing or a flag is unparseable.
    """
    path = participants_registry_path() if path is None else Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"subject registry not found: {path} - it is written by src/pipeline/populate_metadata.py "
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


# Why each excluded subject is excluded. A closed vocabulary, deliberately: the file is written
# by hand from a notebook, so a typo'd reason must fail loudly instead of quietly becoming a new
# category nothing counts. Extending it is one entry here plus one line in
# docs/guides/metadata.md - it is meant to grow.
KNOWN_EXCLUSION_REASONS = (
    # the mask has no lesion voxels at all on the grid it was measured on
    "empty_mask",
    # the lesion is too small for the subject to carry usable information
    "lesion_too_small",
    # too much of the lesion falls outside the brain mask (a registration/tracing problem)
    "out_of_brain_fraction_too_high",
    # the subject's whole feature row is zero in the representation named by `scope`, so every
    # distance metric reads it as maximally distant from everyone. Not a data defect: it can be a
    # true measurement (a lesion that cuts no tract's streamlines, see docs/dev/sdc_matrix.md),
    # which is exactly why it is scoped to one representation rather than excluded everywhere.
    "all_zero_features",
)

# Which matrix a row applies to. "all" means every one of them; the others name a single
# representation, because a subject can be unusable in one and perfectly valid in the others.
# A scope per representation, not a coarse "lesion"/"sdc": the SDC builders produce three
# different feature spaces from the same subject (see src/features/sdc.py).
KNOWN_EXCLUSION_SCOPES = (
    "all",
    "lesion",
    "sdc-parcellated",
    "sdc-voxelwise",
    "sdc-streamline",
)
_EXCLUDED_REQUIRED_COLUMNS = ("subject_id", "dataset", "reason", "scope", "value")


def load_excluded_subjects(path: Path, scope: str) -> pd.DataFrame:
    """Read the hand-curated list of subjects to keep out of a production matrix.

    `scope` names the matrix asking (one of KNOWN_EXCLUSION_SCOPES, never "all" - that is a
    value rows carry, not a question a caller can ask). Only the rows that apply are returned:
    those scoped "all" plus those scoped exactly to this matrix. It is a required argument on
    purpose - a default would let a new caller silently get somebody else's exclusions.

    This file is written BY HAND (notebooks/exploration/lesion_analysis.ipynb, after looking at
    assets/metadata/lesion_metadata.csv's distributions), not generated by any pipeline: which
    borderline subject is worth dropping is a judgement call, not a threshold. It is the single
    list both matrix pipelines read, so they exclude exactly the same subjects by construction
    rather than by two configs agreeing - see docs/dev/lesion_matrix.md.

    `value` is the metric that motivated the exclusion (a voxel count, a fraction), kept so the
    decision stays auditable months later: "sub-X was dropped" without "at 2 voxels" cannot be
    reviewed, only trusted.

    Rows scoped to one representation are what keeps "one list, read by every matrix pipeline"
    workable now that a subject can be unusable in one feature space and valid in the others:
    the file is still the single source, but "the same subjects by construction" now holds per
    scope rather than globally. A row must therefore say where it applies, and `scope: "all"` is
    how "everywhere" is stated explicitly rather than assumed.

    An existing file with only its header is valid and means "nothing is excluded, deliberately".
    A MISSING file raises instead: that is indistinguishable from "the file was never written",
    and silently building a production matrix with every borderline subject in it is exactly the
    outcome this list exists to prevent.

    Every row is validated against the subject registry, because a hand-written file drifts:
    an unknown or duplicated subject_id, a `dataset` that disagrees with the registry, an
    unregistered `reason` or a non-numeric `value` all raise, naming the offending rows.
    """
    if scope not in KNOWN_EXCLUSION_SCOPES or scope == "all":
        askable = [s for s in KNOWN_EXCLUSION_SCOPES if s != "all"]
        raise ValueError(f"scope must be one of {askable}, got {scope!r}")

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"excluded-subjects list not found: {path} - it is written by hand from "
            "notebooks/exploration/lesion_analysis.ipynb (see docs/guides/metadata.md). To build a "
            "matrix excluding nobody, create it with only its header row: "
            f"{','.join(_EXCLUDED_REQUIRED_COLUMNS)}"
        )

    excluded = pd.read_csv(path, dtype=str)
    missing = [c for c in _EXCLUDED_REQUIRED_COLUMNS if c not in excluded.columns]
    if missing:
        raise ValueError(f"{path}: missing required column(s) {missing}, got {list(excluded.columns)}")
    if excluded.empty:
        return excluded.assign(value=pd.Series(dtype="float64"))  # columns only, nothing to scope

    blank = excluded.loc[excluded["subject_id"].isna() | (excluded["subject_id"].str.strip() == "")]
    if not blank.empty:
        raise ValueError(f"{path}: {len(blank)} row(s) have an empty subject_id")

    duplicates = sorted(
        excluded.loc[excluded.duplicated(subset=["subject_id", "scope"]), "subject_id"]
    )
    if duplicates:
        raise ValueError(
            f"{path}: duplicate (subject_id, scope) row(s): {duplicates} - one row per subject per "
            "scope, so the reason a subject was dropped from a given matrix is unambiguous"
        )

    unknown_scopes = sorted(set(excluded["scope"].dropna()) - set(KNOWN_EXCLUSION_SCOPES))
    if unknown_scopes or excluded["scope"].isna().any():
        raise ValueError(
            f"{path}: unregistered scope(s) {unknown_scopes or ['<empty>']}; "
            f"known: {list(KNOWN_EXCLUSION_SCOPES)}"
        )

    # A subject scoped "all" plus a narrower row says two things at once, and which one wins
    # would depend on which matrix asks - so it is rejected rather than resolved.
    scoped_all = set(excluded.loc[excluded["scope"] == "all", "subject_id"])
    also_narrow = sorted(scoped_all & set(excluded.loc[excluded["scope"] != "all", "subject_id"]))
    if also_narrow:
        raise ValueError(
            f"{path}: subject(s) {also_narrow} have both a scope='all' row and a narrower one - "
            "'all' already covers every matrix, so the second row can only contradict it"
        )

    unknown_reasons = sorted(set(excluded["reason"].dropna()) - set(KNOWN_EXCLUSION_REASONS))
    if unknown_reasons or excluded["reason"].isna().any():
        raise ValueError(
            f"{path}: unregistered reason(s) {unknown_reasons or ['<empty>']}; "
            f"known: {list(KNOWN_EXCLUSION_REASONS)}"
        )

    registry = load_participants_registry().set_index("subject_id")
    unknown_ids = sorted(set(excluded["subject_id"]) - set(registry.index))
    if unknown_ids:
        raise ValueError(
            f"{path}: {len(unknown_ids)} subject_id(s) have no row in {participants_registry_path()}: "
            f"{unknown_ids[:5]} - a typo'd id would otherwise exclude nobody, silently"
        )

    expected_datasets = registry.loc[excluded["subject_id"], "dataset"].to_numpy()
    mismatched = excluded.loc[excluded["dataset"].to_numpy() != expected_datasets]
    if not mismatched.empty:
        pairs = [
            f"{row.subject_id} (listed {row.dataset!r}, registry says {expected!r})"
            for row, expected in zip(mismatched.itertuples(), expected_datasets[mismatched.index])
        ]
        raise ValueError(f"{path}: {len(mismatched)} row(s) name the wrong dataset: {pairs[:5]}")

    values = pd.to_numeric(excluded["value"], errors="coerce")
    unparseable = sorted(excluded.loc[values.isna(), "subject_id"])
    if unparseable:
        raise ValueError(
            f"{path}: non-numeric 'value' for subject(s) {unparseable[:5]} - it records the metric "
            "that motivated the exclusion (a voxel count, a fraction), so it must be a number"
        )
    # Validation above deliberately runs over the WHOLE file, not just this scope's rows: a typo
    # in a row meant for another matrix must fail here too, not lie dormant until that matrix runs.
    applies = excluded["scope"].isin(("all", scope))
    return excluded.assign(value=values).loc[applies].reset_index(drop=True)


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
