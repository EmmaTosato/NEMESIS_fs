"""Standalone script: builds the curated per-dataset TSV metadata files under
`assets/metadata/` by intersecting the data_summary availability CSVs
(`assets/dataset_summaries/data_summary__*.csv`, see scripts/data_summary.py)
with each dataset's raw `participants.tsv`
(`data/clinical_connectome/derivatives/<center>/<dataset>/participants.tsv`).

Formerly a cell in notebooks/exploration/dataset_exploration.ipynb (see
docs/dev/metadata.md, layer 2) - moved here so it can be re-run without
opening the notebook, e.g. whenever a dataset is onboarded or its
data_summary changes. Which datasets get which output file is a deliberate,
per-dataset curation choice, not auto-detected from presence flags alone -
see config/pipelines/build_participant_metadata.json.

Three file types, all `<DATASET>_participants_<suffix>.tsv`:
- `_lesions.tsv`: subjects with a validated lesion mask ("present").
- `_features.tsv`: subjects with complete validated fMRI data ("present", never "incomplete").
- `_join.tsv`: the intersection of the two above.

A dataset with no local participants.tsv, or whose data_summary is missing
the relevant availability column, is a legitimate per-dataset gap (skipped,
logged as a warning) - not a config error. A `participant_id` that matches
neither the canonical `sub-*` form nor the raw `{disease}_{site}_{num}`
fallback pattern is a config/data error and stops the run (see
to_subject_id).

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/build_participant_metadata.py \\
        --config config/pipelines/build_participant_metadata.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATASET_SUMMARIES_DIR = Path("assets") / "dataset_summaries"
DERIVATIVES_ROOT = Path("data") / "clinical_connectome" / "derivatives"
METADATA_OUT_ROOT = Path("assets") / "metadata"
SUMMARY_PREFIX = "data_summary__"

LESION_COL = "lesion/manual_masks/anat/lesion_mask"
FEATURE_COL = "feature/func/FC-pearson"
PRESENT = "present"

# Matches a raw, non-canonical participant_id like "ST_UCL-UK_0001" (UCL-UK's shape) -
# {disease}_{site, possibly hyphenated}_{numeric id}.
_RAW_PARTICIPANT_ID_RE = re.compile(r"^(?P<disease>[A-Z]+)_(?P<site>[A-Za-z-]+)_(?P<num>\d+)$")


@dataclass(frozen=True)
class BuildParticipantMetadataConfig:
    datasets_with_lesions: list[str]
    datasets_with_features: list[str]


def load_config(path: str) -> BuildParticipantMetadataConfig:
    with open(path) as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(raw).__name__}")
    for key in ("datasets_with_lesions", "datasets_with_features"):
        if key not in raw:
            raise ValueError(f"{path}: missing required key {key!r}")
        if not isinstance(raw[key], list) or not all(isinstance(v, str) for v in raw[key]):
            raise ValueError(f"{path}: {key!r} must be a list of strings")
    return BuildParticipantMetadataConfig(
        datasets_with_lesions=raw["datasets_with_lesions"],
        datasets_with_features=raw["datasets_with_features"],
    )


def load_data_summaries() -> dict[str, pd.DataFrame]:
    """One DataFrame per dataset, keyed by the same safe_name
    scripts/data_summary.py uses for its own filenames (dataset name with
    "/" replaced by "_")."""
    paths = sorted(DATASET_SUMMARIES_DIR.glob(f"{SUMMARY_PREFIX}*.csv"))
    if not paths:
        raise FileNotFoundError(
            f"no {SUMMARY_PREFIX}*.csv files found under {DATASET_SUMMARIES_DIR} - "
            "run scripts/data_summary.py first"
        )
    return {p.stem[len(SUMMARY_PREFIX):]: pd.read_csv(p, dtype=str) for p in paths}


def to_subject_id(participant_id: str) -> str:
    """Canonical `sub-{disease}{site}{num}` form (matching `subject` in the
    data_summary CSVs) from a raw participants.tsv `participant_id`. Most
    datasets already store the canonical form; UCL-UK is the one exception
    ("ST_UCL-UK_0001"). Raises if neither shape matches, rather than
    silently producing a merge with zero matches."""
    if participant_id.startswith("sub-"):
        return participant_id
    match = _RAW_PARTICIPANT_ID_RE.match(participant_id)
    if match is None:
        raise ValueError(
            f"participant_id {participant_id!r} matches neither the canonical 'sub-*' form "
            "nor the '{disease}_{site}_{num}' fallback pattern"
        )
    return f"sub-{match['disease']}{match['site'].replace('-', '')}{match['num']}"


def _participants_tsv_path(dataset_name: str) -> Path:
    """dataset_name is the data_summary safe_name (e.g. "UNIPD_WashU",
    "UCL-UK_UCLStrokeData") - splits on the first "_" into center/dataset,
    matching data/clinical_connectome/derivatives/<center>/<dataset>/."""
    center, _, rest = dataset_name.partition("_")
    if not rest:
        return DERIVATIVES_ROOT / dataset_name / "participants.tsv"
    return DERIVATIVES_ROOT / center / rest / "participants.tsv"


def load_participants(dataset_name: str) -> pd.DataFrame | None:
    """Raw participants.tsv for this dataset, with `participant_id`
    promoted to the canonical `sub-*` form (original preserved under
    `original_id` whenever it wasn't already canonical). Returns None if the
    dataset has no participants.tsv locally - a legitimate per-dataset gap,
    not an error."""
    path = _participants_tsv_path(dataset_name)
    if not path.exists():
        return None
    df = pd.read_csv(path, sep="\t", dtype=str)
    canonical_ids = df["participant_id"].apply(to_subject_id)
    if (df["participant_id"] == canonical_ids).all():
        return df
    if "original_id" in df.columns:
        raise ValueError(
            f"{dataset_name}: participant_id isn't canonical and participants.tsv already "
            "has an 'original_id' column - column name conflict"
        )
    df["original_id"] = df["participant_id"]
    df["participant_id"] = canonical_ids
    return df


def merge_with_summary(participants: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    summary = summary.drop_duplicates(subset=["subject"])
    return participants.merge(summary, left_on="participant_id", right_on="subject", how="left")


def _write_tsv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, sep="\t", index=False)
    logging.info("wrote %s (%d subjects)", path, len(df))


def export_dataset(dataset_name: str, merged: pd.DataFrame, config: BuildParticipantMetadataConfig) -> None:
    lesions = pd.DataFrame()
    if dataset_name in config.datasets_with_lesions:
        if LESION_COL not in merged.columns:
            logging.warning("%s: column %r not found, skipping lesion export", dataset_name, LESION_COL)
        else:
            lesions = merged[merged[LESION_COL] == PRESENT].copy()
            if not lesions.empty:
                _write_tsv(lesions, METADATA_OUT_ROOT / f"{dataset_name}_participants_lesions.tsv")

    if dataset_name not in config.datasets_with_features:
        return
    if FEATURE_COL not in merged.columns:
        logging.warning("%s: column %r not found, skipping feature export", dataset_name, FEATURE_COL)
        return
    features = merged[merged[FEATURE_COL] == PRESENT].copy()
    if features.empty:
        return
    _write_tsv(features, METADATA_OUT_ROOT / f"{dataset_name}_participants_features.tsv")
    if lesions.empty:
        return
    join = merged[(merged[LESION_COL] == PRESENT) & (merged[FEATURE_COL] == PRESENT)].copy()
    if not join.empty:
        _write_tsv(join, METADATA_OUT_ROOT / f"{dataset_name}_participants_join.tsv")


def build_participant_metadata(config: BuildParticipantMetadataConfig) -> None:
    METADATA_OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for dataset_name, summary in load_data_summaries().items():
        participants = load_participants(dataset_name)
        if participants is None:
            logging.warning("%s: participants.tsv not found, skipping", dataset_name)
            continue
        merged = merge_with_summary(participants, summary)
        export_dataset(dataset_name, merged, config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="Path to a build_participant_metadata.json config")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        config = load_config(args.config)
        build_participant_metadata(config)
    except (ValueError, FileNotFoundError) as exc:
        logging.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
