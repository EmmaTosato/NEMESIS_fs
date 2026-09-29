"""Zero lesion voxels falling outside a brain mask.

The "correct" counterpart to excluding a contaminated subject outright
(assets/metadata/excluded_subjects.csv): it keeps the subject and removes only the
offending voxels. Used by build_lesion_matrix.py (correct_out_of_brain) before
counting a matrix row's volume, and by compute_lesion_metadata.py before counting
volume and laterality on each grid. Supersedes scripts/lesion_fix.py
(a standalone, never-integrated script with a hardcoded path to another user's
machine - deleted 29-09-26, see .claude/history/project_changelog.md).
"""

from __future__ import annotations

import numpy as np


def zero_out_of_brain_voxels(X_voxelwise: np.ndarray, brain_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Zero every lesion voxel falling outside brain_mask, for every subject.

    Returns (X_corrected, n_corrected_voxels) - n_corrected_voxels[i] is the
    count of subject i's lesion voxels that were actually zeroed (0 for a
    subject with no lesion voxels outside brain_mask, i.e. "not corrected").
    A count rather than a boolean flag, so a caller can report not just who
    was corrected but how much - collapsing to a boolean (n_corrected_voxels
    > 0) loses that, so callers that only need "was this subject touched at
    all" derive it explicitly rather than this function deciding for them.
    """
    outside_brain = ~brain_mask
    n_corrected_voxels = (X_voxelwise.astype(bool) & outside_brain).sum(axis=1)
    X_corrected = X_voxelwise.copy()
    X_corrected[:, outside_brain] = 0
    return X_corrected, n_corrected_voxels
