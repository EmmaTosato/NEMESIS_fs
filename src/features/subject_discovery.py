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


def _subject_dir_segment_index(glob_pattern: str) -> int | None:
    """Index into a matched file's path (relative to dataset_root) of the subject
    directory segment - the one path component that is a bare "*" in glob_pattern
    (e.g. "manual_masks/*/anat/*_label-lesion_mask.nii.gz" -> index 1). None if
    glob_pattern has no bare "*" segment - nothing to cross-check the filename
    against in that case, not an error (a hypothetical caller with a flatter
    layout, none exist in this repo today).
    """
    parts = glob_pattern.split("/")
    indices = [i for i, part in enumerate(parts) if part == "*"]
    if not indices:
        return None
    if len(indices) > 1:
        # Ambiguous which "*" is the subject directory - lesson #3, never guess the first.
        raise ValueError(
            f"glob_pattern={glob_pattern!r} has {len(indices)} bare '*' path segments - "
            "cannot tell which one is the subject directory for the filename/folder cross-check"
        )
    return indices[0]


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
    convention every caller of this function already relies on - cross-checked
    against the subject directory the file actually lives in (the glob_pattern
    segment that is a bare "*", e.g. "manual_masks/*/anat/..." - every real
    caller's pattern has exactly one), raising ValueError on a mismatch (lesson
    #22: a placeholder repeated in more than one place - here, "which subject
    does this file belong to" implied both by its folder and by its own name -
    must agree, not be trusted from only one of the two). A file physically
    misfiled under the wrong subject's folder (e.g. copied by hand during a
    manual retrieval repair, filename left unchanged) is exactly the case this
    catches - the filename alone would otherwise associate it with the wrong
    subject, silently.

    Raises ValueError if more than one file maps to the same subject_id (a
    leftover/duplicate file, not a legitimate multiplicity - unlike the
    retrieval registry's atlas-combo templates, this function's contract is
    exactly one file per subject per glob_pattern; the caller is expected to
    call it once per combo/variant when more than one legitimately exists).
    Never picks one arbitrarily - the caller must resolve/clean up the
    conflict before this can proceed.
    """
    dataset_root = Path(data_root) / dataset
    files = sorted(dataset_root.glob(glob_pattern))
    subject_dir_index = _subject_dir_segment_index(glob_pattern)

    matches_by_subject: dict[str, list[Path]] = {}
    mismatched: list[tuple[str, str, Path]] = []
    for f in files:
        subject_id = f.name.split("_")[0]
        if subject_dir_index is not None:
            dir_subject_id = f.relative_to(dataset_root).parts[subject_dir_index]
            if dir_subject_id != subject_id:
                mismatched.append((subject_id, dir_subject_id, f))
                continue
        matches_by_subject.setdefault(subject_id, []).append(f)

    if mismatched:
        details = "; ".join(
            f"{f} (filename says {name!r}, folder says {folder!r})" for name, folder, f in mismatched
        )
        raise ValueError(
            f"{dataset}: {len(mismatched)} file(s) whose filename and parent subject directory disagree "
            f"for glob_pattern={glob_pattern!r} - a real subject/folder mismatch is data corruption "
            f"(e.g. a file copied into the wrong subject's folder), not something to guess past: {details}"
        )

    ambiguous = {subject: paths for subject, paths in matches_by_subject.items() if len(paths) > 1}
    if ambiguous:
        details = "; ".join(
            f"{subject}: {[str(p) for p in paths]}" for subject, paths in sorted(ambiguous.items())
        )
        raise ValueError(
            f"{dataset}: {len(ambiguous)} subject(s) matched more than one file for "
            f"glob_pattern={glob_pattern!r} - expected exactly one file per subject ({details})"
        )

    by_subject = {subject: paths[0] for subject, paths in matches_by_subject.items()}

    excluded_by_group: list[str] = []
    if group_filter is not None:
        excluded_by_group = sorted(s for s in by_subject if group_of(s) not in group_filter)
        by_subject = {s: p for s, p in by_subject.items() if group_of(s) in group_filter}

    return by_subject, excluded_by_group
