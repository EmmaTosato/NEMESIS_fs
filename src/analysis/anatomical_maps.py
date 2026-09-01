"""Subject-level and cluster-level lesion anatomy maps, in MNI space.

Two independently useful building blocks, both promoted (01-09-26) from the exploratory prototype
in notebooks/post-results_analysis/embedding_to_anatomy_mapping.ipynb §2 - same algorithm, given
type hints and tests, no behavior change:

- resolve_lesion_paths: subject_id -> real lesion mask path, under the retrieval layout of today
  (never a historical run's own config.md - see that notebook's "Configurazione" cell for why a
  run's own recorded layout can be stale).
- build_overlap_map: a set of already-resolved lesion masks -> (count_img, percentage_img), voxel-
  wise across the given subjects - resampled/binarized with the exact same parameters used to build
  whatever feature matrix the caller's subject selection came from (otherwise the map wouldn't
  faithfully represent what that matrix, and any embedding built from it, actually saw).

Consumed by src.pipeline.embedding_app (single-subject lesion viewer, per-cluster overlap map) - see
docs/guides/embedding_app.md.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn.image import resample_to_img

from src.features.subject_discovery import discover_files_by_subject


def resolve_lesion_paths(
    subject_ids: list[str],
    dataset_by_subject: dict[str, str],
    data_root: Path,
    lesion_glob: str,
) -> dict[str, Path]:
    """subject_id -> its lesion mask path, resolved under data_root/lesion_glob.

    One discover_files_by_subject call per distinct dataset among subject_ids (not one per
    subject - cheap, globs once per dataset). Raises ValueError naming every subject_id that
    couldn't be resolved (missing from dataset_by_subject, or not found on disk) - never a map
    silently smaller than requested (code_standards.md §0).
    """
    requested_by_dataset: dict[str, list[str]] = {}
    for subject_id in subject_ids:
        if subject_id not in dataset_by_subject:
            raise ValueError(f"{subject_id!r} has no known dataset in the supplied metadata")
        requested_by_dataset.setdefault(dataset_by_subject[subject_id], []).append(subject_id)

    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for dataset, wanted in requested_by_dataset.items():
        found_by_subject, _excluded_by_group = discover_files_by_subject(data_root, dataset, lesion_glob, group_filter=None)
        for subject_id in wanted:
            if subject_id in found_by_subject:
                resolved[subject_id] = found_by_subject[subject_id]
            else:
                missing.append(subject_id)

    if missing:
        raise ValueError(
            f"{len(missing)}/{len(subject_ids)} requested subject(s) not found on disk under "
            f"{data_root} (glob={lesion_glob!r}): {sorted(missing)}"
        )
    return resolved


def _load_and_binarize(
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str, binarize_threshold: float
) -> np.ndarray:
    img = nib.load(path)
    if img.shape != reference_img.shape:
        img = resample_to_img(img, reference_img, interpolation=resample_interpolation, force_resample=True, copy_header=True)
    return img.get_fdata() > binarize_threshold


def build_overlap_map(
    lesion_paths: dict[str, Path],
    reference_img: nib.Nifti1Image,
    binarize_threshold: float,
    resample_interpolation: str,
) -> tuple[nib.Nifti1Image, nib.Nifti1Image]:
    """(count_img, percentage_img) across every mask in lesion_paths, on reference_img's grid.

    count_img's voxel value is how many of the given subjects had a lesion there; percentage_img
    is that divided by len(lesion_paths) * 100. Same resample/binarize contract as
    src/features/lesion.py::_load_and_binarize_lesion (kept separate here - that helper is
    private and returns a raveled feature vector, not a volume). Raises ValueError on an empty
    lesion_paths - there is no meaningful overlap map over zero subjects.

    Per-subject load+resample runs on a thread pool (01-09-26, measured: ~40ms/subject,
    15.7s of a 16.7s cluster-overlap-map build on a real 408-subject cluster - dominates
    everything else in the app, unlike the small matrix.npy reads elsewhere) - nibabel's
    nib.load and nilearn's resample_to_img are both I/O- and SciPy-C-level-bound, releasing the
    GIL for the bulk of their work, so this is a real wall-clock win, not just concurrency
    theater. Same failure semantics as the original sequential loop: the first subject that
    raises (a corrupt/missing file) aborts the whole map, propagated by ThreadPoolExecutor.map
    exactly like a plain `for` loop would - no per-subject isolation added here (out of scope
    for this pass, see resolve_lesion_paths for where "which subject is missing" is already
    surfaced explicitly, before any loading is attempted).
    """
    if not lesion_paths:
        raise ValueError("build_overlap_map got an empty subject list - nothing to overlap")

    counts = np.zeros(reference_img.shape, dtype=np.int32)
    with ThreadPoolExecutor() as executor:
        for binary_mask in executor.map(
            lambda path: _load_and_binarize(path, reference_img, resample_interpolation, binarize_threshold),
            lesion_paths.values(),
        ):
            counts += binary_mask

    percentage = (100.0 * counts / len(lesion_paths)).astype(np.float32)
    count_img = nib.Nifti1Image(counts, reference_img.affine)
    percentage_img = nib.Nifti1Image(percentage, reference_img.affine)
    return count_img, percentage_img
