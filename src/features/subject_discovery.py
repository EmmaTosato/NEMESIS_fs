"""Shared subject-level file discovery under data/clinical_connectome/derivatives.

One glob pattern -> one file per subject_id, optionally restricted to a
group_filter (see src.retrieval.dataset.group_of for the ST/HC/PD/GM naming
convention). Used by both src/features/lesion.py (lesion masks) and
src/features/functional.py (FC matrices) - previously each had its own
independent glob + dict-comprehension for this, which is how a real dataset
mixing patients (ST) and healthy controls (HC) under the same `features/`
tree (WashU) went unnoticed until group_filter was added explicitly here.

Deliberately not src/retrieval/dataset.py's Dataset/FilePatterns registry:
that model registers file templates per (object, pipeline, datatype, suffix)
combination, with atlas combo baked in as one of several alternative
templates - a fit for retrieve_data.py's "copy whatever combo exists"
semantics, not for a pipeline that must process one caller-selected combo at
a time (mask_fc.py's atlas_combos loop). This module only reuses
src.retrieval.dataset.group_of, the one piece of subject-naming logic that's
genuinely project-wide.

data/derived (pipeline outputs: masked_fc/, fc_matrix/, lesion_matrix/, ...)
is a structurally different tree (per-run/per-combo artifacts, not
per-subject BIDS folders) and is not covered here.
"""

from __future__ import annotations

from pathlib import Path

from src.retrieval.dataset import group_of


def discover_files_by_subject(
    data_root: Path, dataset: str, glob_pattern: str, group_filter: list[str] | None
) -> tuple[dict[str, Path], list[str]]:
    """One file per subject_id matching glob_pattern under data_root/dataset.

    Returns (files_by_subject, excluded_by_group): files_by_subject is
    already restricted to group_filter (a subject whose group_of() isn't in
    group_filter is removed, not just flagged); excluded_by_group is that
    same removed subject list, for the caller to log explicitly - never a
    silent exclusion. group_filter=None means no restriction at all - only
    correct for a dataset/config known not to mix groups.

    subject_id is taken as the leading "_"-delimited token of the filename
    (e.g. "sub-STUNIPD0001_space-...-mask.nii.gz" -> "sub-STUNIPD0001"), the
    convention every caller of this function already relies on.
    """
    dataset_root = Path(data_root) / dataset
    files = sorted(dataset_root.glob(glob_pattern))
    by_subject = {f.name.split("_")[0]: f for f in files}

    excluded_by_group: list[str] = []
    if group_filter is not None:
        excluded_by_group = sorted(s for s in by_subject if group_of(s) not in group_filter)
        by_subject = {s: p for s, p in by_subject.items() if group_of(s) in group_filter}

    return by_subject, excluded_by_group
