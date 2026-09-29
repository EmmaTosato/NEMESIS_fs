"""Zero lesion voxels falling outside a brain mask.

The "correct" counterpart to build_lesion_matrix.py's max_out_of_brain_fraction
admission filter (src/features/lesion.py), which only measures/excludes a
contaminated subject, never modifies voxels. Supersedes scripts/lesion_fix.py
(a standalone, never-integrated script with a hardcoded path to another user's
machine - deleted 29-09-26, see .claude/history/project_changelog.md).
"""

from __future__ import annotations

import numpy as np


def zero_out_of_brain_voxels(X_voxelwise: np.ndarray, brain_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Zero every lesion voxel falling outside brain_mask, for every subject.

    Returns (X_corrected, was_corrected) - was_corrected[i] is True iff subject
    i had at least one voxel actually zeroed (genuinely contaminated). A
    subject with 0 lesion voxels, or whose lesion lies entirely inside
    brain_mask, is left untouched and not flagged.
    """
    outside_brain = ~brain_mask
    was_corrected = (X_voxelwise.astype(bool) & outside_brain).any(axis=1)
    X_corrected = X_voxelwise.copy()
    X_corrected[:, outside_brain] = 0
    return X_corrected, was_corrected
