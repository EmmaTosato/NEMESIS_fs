"""Resamples lesion masks onto the canonical MNI152NLin6Asym 1mm grid before
staging, for the minority of subjects whose masks arrive on a non-canonical
grid (e.g. UKLFR/stroke_UKLFR, natively 1.5mm).

bcb-lf-preprocess's own normalisation (bcblib.tools.lesion_features
._preprocess.normalise_lesion_to_mni6) resamples correctly for any voxel
size - it derives the target affine/shape from the input's own affine - but
it is gated by detect_resolution_from_shape(), which only recognises a fixed
whitelist of canonical 1mm/2mm MNI grid shapes and raises ValueError on
anything else (e.g. the 1.5mm shape (121, 145, 121)), before that generic
resampling is ever reached. bcb-lf-preprocess has no CLI flag to bypass this
detection (confirmed against bcblib 0.6.1, a third-party pip package - not
something to patch in site-packages). Resampling here first means every mask
handed to bcb-lf-preprocess already sits on a shape it recognises (the
canonical grid itself), sidestepping the bug entirely. See
docs/debugging/debug_23_07_26.md.

Uses the same nilearn.image.resample_to_img + forced nearest-neighbour
pattern already established for discrete/binary volumes in
src/features/lesion.py (load_and_resample_atlas, _load_and_binarize_lesion).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import nibabel as nib
import numpy as np
from nibabel.filebasedimages import ImageFileError
from nilearn.image import resample_to_img

from src.sdc.manifest import ManifestRow


def resample_lesion_if_needed(lesion_path: Path, reference_img: nib.Nifti1Image, resampled_dir: Path) -> Path:
    """Returns lesion_path unchanged if it already sits on reference_img's
    exact grid (shape and affine), otherwise resamples it (nearest-neighbour,
    since a lesion mask is binary - any other interpolation would invent
    values that are neither 0 nor 1) and writes the result under
    resampled_dir, returning that new path."""
    img = nib.load(lesion_path)
    if img.shape == reference_img.shape and np.array_equal(img.affine, reference_img.affine):
        return lesion_path

    resampled_dir.mkdir(parents=True, exist_ok=True)
    resampled_img = resample_to_img(
        img, reference_img, interpolation="nearest", force_resample=True, copy_header=True
    )
    out_path = resampled_dir / lesion_path.name
    resampled_img.to_filename(out_path)
    return out_path


def resample_nonconforming_rows(
    rows: list[ManifestRow], reference_img: nib.Nifti1Image, resampled_dir: Path
) -> tuple[list[ManifestRow], dict[str, str]]:
    """Returns (rows, failed): rows with lesion_mask_path repointed at a
    resampled copy for any subject whose mask isn't already on
    reference_img's grid (returned unchanged if it already conforms).
    failed maps subject_id -> reason for any subject whose mask could not be
    loaded at all (corrupt/unreadable NIfTI) - excluded from rows rather
    than raising, so one bad file doesn't abort resampling (and therefore
    Stage 1) for the rest of the task's subjects, same per-subject isolation
    as check_stage1_outputs in runner.py."""
    result = []
    failed: dict[str, str] = {}
    for row in rows:
        try:
            resolved_path = resample_lesion_if_needed(row.lesion_mask_path, reference_img, resampled_dir)
        except (OSError, ValueError, ImageFileError) as exc:
            failed[row.subject_id] = f"lesion mask not a loadable NIfTI: {exc}"
            continue
        result.append(row if resolved_path == row.lesion_mask_path else replace(row, lesion_mask_path=resolved_path))
    return result, failed
