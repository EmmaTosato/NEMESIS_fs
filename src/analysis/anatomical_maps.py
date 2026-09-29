"""Subject-level and cluster-level anatomy maps (lesion and SDC disconnectome), in MNI space.

Building blocks, promoted (01-09-26) from the exploratory prototype in
notebooks/post-results_analysis/embedding_to_anatomy_mapping.ipynb §2 - same algorithm, given
type hints and tests, no behavior change; build_mean_map added later (see its own docstring) for
the same notebook's SDC extension:

- resolve_lesion_paths: subject_id -> real file path (a lesion mask OR, despite the name, any
  other per-subject NIfTI glob - e.g. an SDC disconnectome-map.nii.gz, see
  src.analysis.embedding_app.SDC_DISCONNECTOME_GLOB), under the retrieval layout of today (never
  a historical run's own config.md - see that notebook's "Configurazione" cell for why a run's
  own recorded layout can be stale). Raises if ANY requested subject can't be resolved.
- resolve_available_lesion_paths (29-09-26): same resolution, for a caller that can proceed with
  fewer subjects than requested - returns (resolved, missing) instead of raising for an
  individual gap, logging a WARNING naming what's excluded.
- build_overlap_map: a set of already-resolved *binary* lesion masks -> (count_img,
  percentage_img), voxelwise across the given subjects - resampled/binarized with the exact same
  parameters used to build whatever feature matrix the caller's subject selection came from
  (otherwise the map wouldn't faithfully represent what that matrix, and any embedding built from
  it, actually saw).
- build_mean_map: the *continuous*-data counterpart - a set of already-resolved images (e.g. SDC
  disconnectome maps, a [0, 1] per-voxel probability, never binarized) -> their voxelwise mean.

Consumed by src.pipeline.embedding_app (single-subject lesion/disconnectome viewers, per-cluster
lesion overlap map and disconnection mean map) - see docs/guides/embedding_app.md.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn.image import resample_to_img

from src.features.subject_discovery import discover_files_by_subject


def _resolve_lesion_paths_partial(
    subject_ids: list[str],
    dataset_by_subject: dict[str, str],
    data_root: Path,
    lesion_glob: str,
) -> tuple[dict[str, Path], list[str]]:
    """Shared resolution core for resolve_lesion_paths/resolve_available_lesion_paths - returns
    (resolved, missing) without deciding what "missing" means for the caller (hard-fail vs.
    skip-and-report); that decision belongs to whichever of the two public functions calls this.

    One discover_files_by_subject call per distinct dataset among subject_ids (not one per
    subject - cheap, globs once per dataset). Raises ValueError if a subject_id has no entry in
    dataset_by_subject at all - a caller bug (a subject genuinely missing from the metadata this
    request came from), never silently treated the same as "missing on disk"."""
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
    return resolved, missing


def resolve_lesion_paths(
    subject_ids: list[str],
    dataset_by_subject: dict[str, str],
    data_root: Path,
    lesion_glob: str,
) -> dict[str, Path]:
    """subject_id -> its lesion mask path, resolved under data_root/lesion_glob.

    Raises ValueError naming every subject_id that couldn't be resolved (missing from
    dataset_by_subject, or not found on disk) - never a map silently smaller than requested
    (code_standards.md §0). Used where a partial result is never legitimate - a single-subject
    viewer has no meaningful "show it anyway, minus the one subject that failed" mode. For a
    caller that CAN legitimately proceed with fewer subjects than requested (a per-cluster
    aggregate map), see resolve_available_lesion_paths instead.
    """
    resolved, missing = _resolve_lesion_paths_partial(subject_ids, dataset_by_subject, data_root, lesion_glob)
    if missing:
        raise ValueError(
            f"{len(missing)}/{len(subject_ids)} requested subject(s) not found on disk under "
            f"{data_root} (glob={lesion_glob!r}): {sorted(missing)}"
        )
    return resolved


def resolve_available_lesion_paths(
    subject_ids: list[str],
    dataset_by_subject: dict[str, str],
    data_root: Path,
    lesion_glob: str,
) -> tuple[dict[str, Path], list[str]]:
    """Like resolve_lesion_paths, but for a caller that can legitimately build its result from
    whichever subjects ARE resolvable, instead of needing every single one requested (29-09-26,
    on request - a per-cluster overlap/mean map, unlike a single-subject viewer, is still a
    meaningful map over however many of its subjects have local data, e.g. after a lesion-mask
    swap left some cluster members' raw files no longer retrieved on this machine, see
    .claude/history/data_changelog.md 23-09-26). Returns (resolved, missing) and never raises
    for an individual unresolvable subject - logs a WARNING naming every excluded one instead
    (code_standards.md §6), so the gap is visible in the server log even if a caller forgets to
    surface `missing` itself in its own UI.

    Still raises ValueError if a subject_id has no known dataset in `dataset_by_subject` at all
    (see _resolve_lesion_paths_partial) - a different kind of problem than "not found on disk",
    never silently absorbed into `missing` either.

    Raises ValueError if EVERY requested subject is unresolvable - an aggregate map built from
    zero subjects is not a legitimate partial result, just an empty one dressed up as a warning.
    """
    resolved, missing = _resolve_lesion_paths_partial(subject_ids, dataset_by_subject, data_root, lesion_glob)
    if missing:
        logging.warning(
            "%d/%d requested subject(s) not found on disk under %s (glob=%r), excluded from this "
            "map: %s", len(missing), len(subject_ids), data_root, lesion_glob, sorted(missing),
        )
    if not resolved:
        raise ValueError(
            f"none of the {len(subject_ids)} requested subject(s) were found on disk under "
            f"{data_root} (glob={lesion_glob!r})"
        )
    return resolved, missing


def _load_and_resample(path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str) -> np.ndarray:
    img = nib.load(path)
    if img.shape != reference_img.shape:
        img = resample_to_img(img, reference_img, interpolation=resample_interpolation, force_resample=True, copy_header=True)
    return img.get_fdata()


def _load_and_binarize(
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str, binarize_threshold: float
) -> np.ndarray:
    return _load_and_resample(path, reference_img, resample_interpolation) > binarize_threshold


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


def build_mean_map(
    image_paths: dict[str, Path],
    reference_img: nib.Nifti1Image,
    resample_interpolation: str,
) -> nib.Nifti1Image:
    """Voxelwise mean across every image in image_paths, on reference_img's grid - the
    continuous-data counterpart of build_overlap_map, for a map that is never binarized (e.g.
    SDC's own disconnectome-map.nii.gz, a [0, 1] per-voxel disconnection probability - see
    src/features/sdc.py's module docstring). No binarize_threshold/count_img here: there is no
    "how many subjects crossed a threshold" concept for a continuous value, only the sample mean
    itself - the value at each voxel is exactly what it says, the average disconnection
    probability across the given subjects at that voxel.

    Same resample-only contract as _load_and_resample (no thresholding), same per-call thread
    pool as build_overlap_map (identical perf reasoning - I/O- and SciPy-C-level-bound per-file
    work, releases the GIL), same failure semantics (the first subject that raises aborts the
    whole map - no per-subject isolation here, resolve_lesion_paths already surfaces "which
    subject is missing" explicitly before any loading is attempted). Raises ValueError on an
    empty image_paths - there is no meaningful mean map over zero subjects.
    """
    if not image_paths:
        raise ValueError("build_mean_map got an empty subject list - nothing to average")

    total = np.zeros(reference_img.shape, dtype=np.float64)
    with ThreadPoolExecutor() as executor:
        for values in executor.map(
            lambda path: _load_and_resample(path, reference_img, resample_interpolation),
            image_paths.values(),
        ):
            total += values

    mean = (total / len(image_paths)).astype(np.float32)
    return nib.Nifti1Image(mean, reference_img.affine)
