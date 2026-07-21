"""Adapts our data layout to the flat BIDS layout `bcb-lf-preprocess` expects.

Lesion masks live at
data/clinical_connectome/<dataset>/sub-XXX/lesion/manual_masks/anat/sub-XXX_..._label-lesion_mask.nii.gz
- one level deeper than the `sub-XXX/anat/*_label-lesion_mask.nii.gz` layout
`--bids-dir` requires. Rather than teach BCBToolKit our layout, this module
builds a throwaway symlink farm in the expected shape for exactly the
subjects a given task is responsible for. Symlinks only, never copies - a
lesion mask can be gigabytes-adjacent in aggregate across hundreds of
subjects, and the file content never needs duplicating for this.
"""

from __future__ import annotations

from pathlib import Path

from src.sdc.manifest import ManifestRow


def stage_subjects(rows: list[ManifestRow], staging_dir: Path) -> None:
    """Creates staging_dir/sub-XXX/anat/<original_filename> for each row, as
    a symlink to the real lesion mask. Raises FileExistsError if staging_dir
    already has content - a stale staging dir from a previous crashed run
    could otherwise mix subjects from two different task assignments."""
    if staging_dir.exists() and any(staging_dir.iterdir()):
        raise FileExistsError(f"staging_dir is not empty, refusing to reuse it: {staging_dir}")

    for row in rows:
        subject_anat_dir = staging_dir / row.subject_id / "anat"
        subject_anat_dir.mkdir(parents=True, exist_ok=True)
        link = subject_anat_dir / row.lesion_mask_path.name
        link.symlink_to(row.lesion_mask_path.resolve())
