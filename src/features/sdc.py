"""Build a 2D feature matrix (n_subjects x n_regions) from parcellated SDC output.

Each subject's disconnectome (or lesion) CSV under sdc/<subject>/ holds one
row per brain region disconnected/damaged above zero for a given atlas -
BCBToolKit omits rows for regions at zero overlap rather than writing them
explicitly (verified empirically on the real cohort: zero rows with an
explicit 0.0 value were ever found - see notebooks/exploration/sdc_analysis.ipynb).
Rows are not in a stable order across subjects, so alignment is done by
region_name (reindex against a fixed reference), never by row position -
unlike src/features/lesion.py's voxel grid, there is no common spatial grid to
resample onto here.

reference_labels_path (assets/atlases/sdc_labels/<atlas>.csv) is the
authoritative, fixed region list for a given atlas - derived once from the
full real cohort (every region reached its known/expected cardinality, see
docs/dev/sdc_matrix.md) and never re-derived per run. Every region_name found
in a subject's CSV must exist in this reference (raise ValueError otherwise -
an atlas mismatch or corrupt file, never guessed past); a reference region
missing from a subject's CSV is the expected/legitimate "omitted, zero
overlap" case, filled with 0.0. No column is ever dropped from X even if
constant across every admitted subject - the project decision here is that
column j always means the same region regardless of which subjects a given
run includes (2026-08-27, on request).

A subject is only admitted into X if it has BOTH a lesion mask registered in
the subject registry AND the requested SDC CSV - a subject present
in sdc/ without a lesion mask (a real case found in this cohort, see
docs/dev/sdc_matrix.md) is excluded explicitly (excluded_no_lesion_mask),
never silently included as an all-zero row indistinguishable from a genuine
"no disconnection" observation.

"Has a lesion mask" is resolved against `assets/metadata/participants.csv`
(via src.utils.participants), NOT by globbing manual_masks/ on disk directly
(unlike build_lesion_matrix.py) - a local `data/` copy can be a partial
retrieval sample (found 2026-08-27: this Mac had only 10 lesion masks per
dataset physically present, vs. 195-705 in sdc/), while the registry is
authoritative about which subjects genuinely have a lesion mask
regardless of what's currently retrieved on any one machine.

A second, alternative representation (`build_sdc_voxelwise_matrix`, added
03/09) builds a voxel-wise matrix directly from the `disconnectome-map`
`.nii.gz` (the pre-parcellation volume the `LF-disconnectome_atlas-*.csv`
files above are themselves derived from) - same resampling-onto-a-common-grid
approach as `src/features/lesion.py`'s voxel-wise lesion matrix, but the
disconnectome values are a **continuous** [0, 1] probability, never
binarized (unlike a lesion mask). Deliberately restricted to
`object_="disconnectome"` only: the equivalent for `object_="lesion"` (the
`lesion-map` .nii.gz, itself just the resampled input lesion mask BCBToolKit
used) would duplicate `build_lesion_matrix.py`'s own job from a different,
less authoritative source (`manual_masks/` is the real source; `sdc/`
only carries a copy of it as SDC's own computation input) - not built here,
raises explicitly if requested.
"""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.image import resample_to_img

from src.utils.participants import load_participants_registry
from src.features.lesion import load_reference_image
from src.features.subject_discovery import discover_files_by_subject
from src.retrieval.dataset import group_of

KNOWN_OBJECTS = frozenset({"disconnectome", "lesion"})
KNOWN_VALUE_COLUMNS = frozenset({
    "fraction_covered", "mean_overlap", "weighted_mean_overlap",
    "sum_overlap", "p90_overlap", "p95_overlap",
})
KNOWN_REPRESENTATIONS = frozenset({"parcellated", "voxelwise"})
_VOXELWISE_SUPPORTED_OBJECTS = frozenset({"disconnectome"})

_LESION_FLAG_COLUMN = "has_lesion"

# Same tolerance as src/features/lesion.py's _AFFINE_ATOL - loose enough to
# absorb float32-header round-tripping noise, tight enough that no real
# registration/resampling difference (always whole fractions of a mm) passes
# unnoticed. Not imported from lesion.py: a private helper, and this module's
# own copy is one line - see lesson_learned.md's general stance on premature
# cross-module sharing of private helpers in this repo (src/sdc/resample.py
# already has its own third, non-tolerant variant of the same check).
_AFFINE_ATOL = 1e-3


def _needs_resample(img: nib.Nifti1Image, reference_img: nib.Nifti1Image) -> bool:
    return img.shape != reference_img.shape or not np.allclose(img.affine, reference_img.affine, atol=_AFFINE_ATOL)


def build_sdc_matrix(
    data_root: Path,
    datasets: list[str],
    object_: str,
    atlas: str,
    value_column: str,
    reference_labels_path: Path,
    group_filter: list[str] | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str]]:
    """Build X (n_subjects x n_regions, fixed = len(region_names)), row-aligned
    metadata, and the region names naming each column.

    Returns (X, metadata, region_names, excluded_by_group,
    excluded_no_lesion_mask, sdc_not_yet_computed) - see module docstring and
    docs/dev/sdc_matrix.md. excluded_by_group merges the group-filter
    exclusions from both the lesion-mask-registry and the SDC-file discovery
    passes.
    """
    if object_ not in KNOWN_OBJECTS:
        raise ValueError(f"object_ must be one of {sorted(KNOWN_OBJECTS)}, got {object_!r}")
    if value_column not in KNOWN_VALUE_COLUMNS:
        raise ValueError(f"value_column must be one of {sorted(KNOWN_VALUE_COLUMNS)}, got {value_column!r}")

    region_names = load_reference_regions(reference_labels_path)

    lesion_subjects, excluded_lesion = _subjects_with_lesion_mask(datasets, group_filter)
    sdc_glob = f"sdc/*/*_LF-{object_}_atlas-{atlas}.csv"
    sdc_files, excluded_sdc = _discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    subject_dfs: dict[tuple[str, str], pd.DataFrame] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        excluded_no_lesion_mask.extend(sorted(sdc_ids - lesion_ids))
        sdc_not_yet_computed.extend(sorted(lesion_ids - sdc_ids))
        for subject_id in sorted(lesion_ids & sdc_ids):
            path = sdc_files[dataset][subject_id]
            subject_dfs[(dataset, subject_id)] = _load_and_validate_csv(path, region_names, value_column)

    if not subject_dfs:
        raise ValueError(
            "no subjects admitted - the intersection of subjects with a registered lesion mask "
            f"(assets/metadata/participants.csv, has_lesion) and subjects with an SDC file "
            f"(object={object_!r}, atlas={atlas!r}) is empty; check 'datasets'/'data_root' in the config"
        )

    X, metadata = _stack_aligned_matrix(subject_dfs, region_names, value_column)
    return X, metadata, region_names, excluded_by_group, sorted(excluded_no_lesion_mask), sorted(sdc_not_yet_computed)


def build_sdc_voxelwise_matrix(
    data_root: Path,
    datasets: list[str],
    object_: str,
    reference_template_path: Path,
    resample_interpolation: str,
    group_filter: list[str] | None,
) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str], list[str], list[str]]:
    """Build X (n_subjects x n_voxels) from the `disconnectome-map` .nii.gz -
    the pre-parcellation volume `build_sdc_matrix`'s CSVs are themselves
    derived from. Continuous [0, 1] disconnection probability per voxel,
    never binarized - see module docstring.

    Same two-pass admission criterion as build_sdc_matrix (a lesion mask
    registered in assets/metadata/participants.csv (has_lesion) AND the
    requested SDC file present), and the same constant-column drop as
    build_lesion_matrix.py (voxels outside every admitted subject's brain
    are identically 0.0 - dropped to keep X a manageable size, recoverable
    via non_constant_mask).

    Returns (X, metadata, non_constant_mask, excluded_by_group,
    excluded_no_lesion_mask, sdc_not_yet_computed).
    """
    if object_ not in _VOXELWISE_SUPPORTED_OBJECTS:
        raise ValueError(
            f"object_ must be one of {sorted(_VOXELWISE_SUPPORTED_OBJECTS)} for representation='voxelwise' "
            f"(the lesion-map equivalent is already built by build_lesion_matrix.py, from its own "
            f"authoritative manual_masks/ source), got {object_!r}"
        )

    lesion_subjects, excluded_lesion = _subjects_with_lesion_mask(datasets, group_filter)
    sdc_glob = f"sdc/*/*_res-1_desc-{object_}.nii.gz"
    sdc_files, excluded_sdc = _discover_by_dataset(data_root, datasets, sdc_glob, group_filter)
    excluded_by_group = sorted(set(excluded_lesion) | set(excluded_sdc))

    admitted: dict[tuple[str, str], Path] = {}
    excluded_no_lesion_mask: list[str] = []
    sdc_not_yet_computed: list[str] = []
    for dataset in datasets:
        lesion_ids = set(lesion_subjects.get(dataset, {}))
        sdc_ids = set(sdc_files.get(dataset, {}))
        excluded_no_lesion_mask.extend(sorted(sdc_ids - lesion_ids))
        sdc_not_yet_computed.extend(sorted(lesion_ids - sdc_ids))
        for subject_id in sorted(lesion_ids & sdc_ids):
            admitted[(dataset, subject_id)] = sdc_files[dataset][subject_id]

    if not admitted:
        raise ValueError(
            "no subjects admitted - the intersection of subjects with a registered lesion mask "
            f"(assets/metadata/participants.csv, has_lesion) and subjects with an SDC file "
            f"(object={object_!r}, representation='voxelwise') is empty; check 'datasets'/'data_root' "
            "in the config"
        )

    reference_img = load_reference_image(reference_template_path)
    X_voxelwise, metadata = _stack_voxelwise_matrix(admitted, reference_img, resample_interpolation)
    X, non_constant_mask = _drop_constant_features(X_voxelwise)
    return X, metadata, non_constant_mask, excluded_by_group, sorted(excluded_no_lesion_mask), sorted(sdc_not_yet_computed)


def load_reference_regions(reference_labels_path: Path) -> np.ndarray:
    """Load the authoritative, fixed region list for one atlas.

    Public so callers that only need the region set (e.g. a sanity check
    against a freshly-retrieved atlas combo) don't have to run full matrix
    discovery/validation via build_sdc_matrix.
    """
    if not reference_labels_path.is_file():
        raise FileNotFoundError(f"reference_labels_path not found: {reference_labels_path}")
    df = pd.read_csv(reference_labels_path)
    if "region_name" not in df.columns:
        raise ValueError(f"{reference_labels_path}: missing 'region_name' column")
    regions = df["region_name"].tolist()
    if len(set(regions)) != len(regions):
        raise ValueError(f"{reference_labels_path}: duplicate region_name entries in reference file")
    return np.array(sorted(regions))


def _discover_by_dataset(
    data_root: Path, datasets: list[str], glob_pattern: str, group_filter: list[str] | None
) -> tuple[dict[str, dict[str, Path]], list[str]]:
    """discover_files_by_subject run once per dataset, merged into one dict.

    Used for the SDC glob only (does this subject have this object/atlas's
    CSV?) - lesion mask presence is resolved from participants.csv instead,
    see _subjects_with_lesion_mask and the module docstring for why.
    """
    by_dataset: dict[str, dict[str, Path]] = {}
    excluded: list[str] = []
    for dataset in datasets:
        by_subject, excluded_here = discover_files_by_subject(data_root, dataset, glob_pattern, group_filter)
        by_dataset[dataset] = by_subject
        excluded.extend(excluded_here)
    return by_dataset, excluded


def _subjects_with_lesion_mask(
    datasets: list[str], group_filter: list[str] | None
) -> tuple[dict[str, dict[str, None]], list[str]]:
    """Which subjects have a lesion mask, per dataset - from
    assets/metadata/participants.csv's has_lesion flag, not from disk (see
    module docstring). Return shape matches _discover_by_dataset's
    {dataset: {subject_id: ...}} so both feed the same intersection logic in
    build_sdc_matrix - the per-subject value here carries no information
    (unlike _discover_by_dataset's Path), only the key set matters.

    Raises ValueError if a requested dataset has no row at all in the
    registry - a structural gap in the file this pipeline depends on for its
    core admission criterion, not something to silently treat as "nobody in
    that dataset has a lesion mask".
    """
    registry = load_participants_registry()
    known_datasets = set(registry["dataset"])
    unknown = [d for d in datasets if d not in known_datasets]
    if unknown:
        raise ValueError(
            f"dataset(s) {unknown} have no row in the subject registry "
            f"(assets/metadata/participants.csv); known datasets: {sorted(known_datasets)}"
        )

    by_dataset: dict[str, dict[str, None]] = {}
    excluded: list[str] = []
    for dataset in datasets:
        in_dataset = registry["dataset"] == dataset
        has_mask = registry.loc[in_dataset & registry[_LESION_FLAG_COLUMN], "subject_id"]
        groups = {s: group_of(s) for s in has_mask}
        excluded_here = sorted(s for s in has_mask if group_filter is not None and groups[s] not in group_filter)
        admitted = {s: None for s in has_mask if group_filter is None or groups[s] in group_filter}

        by_dataset[dataset] = admitted
        excluded.extend(excluded_here)
    return by_dataset, excluded


def _load_and_validate_csv(path: Path, region_names: np.ndarray, value_column: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "region_name" not in df.columns:
        raise ValueError(f"{path}: missing 'region_name' column - unexpected file shape")
    if value_column not in df.columns:
        raise ValueError(f"{path}: missing {value_column!r} column")

    dup = df["region_name"].duplicated()
    if dup.any():
        raise ValueError(
            f"{path}: {int(dup.sum())} duplicate region_name value(s): "
            f"{df.loc[dup, 'region_name'].tolist()}"
        )

    unknown = set(df["region_name"]) - set(region_names)
    if unknown:
        raise ValueError(
            f"{path}: {len(unknown)} region_name value(s) not in the reference label set: "
            f"{sorted(unknown)} - check that the reference file matches this atlas"
        )
    return df


def _stack_aligned_matrix(
    subject_dfs: dict[tuple[str, str], pd.DataFrame], region_names: np.ndarray, value_column: str
) -> tuple[np.ndarray, pd.DataFrame]:
    features = []
    subject_ids: list[str] = []
    dataset_labels: list[str] = []
    for (dataset, subject_id), df in sorted(subject_dfs.items()):
        if len(df) == 0:
            vector = np.zeros(len(region_names))
        else:
            series = df.set_index("region_name")[value_column]
            # BCBToolKit omits regions at zero overlap instead of writing them
            # explicitly - reindex restores them as 0.0 (verified assumption,
            # see module docstring).
            vector = series.reindex(region_names, fill_value=0.0).values
        features.append(vector)
        subject_ids.append(subject_id)
        dataset_labels.append(dataset)
    X = np.stack(features)
    metadata = pd.DataFrame({"subject_id": subject_ids, "dataset": dataset_labels})
    return X, metadata


def _load_disconnectome_voxels(
    path: Path, reference_img: nib.Nifti1Image, resample_interpolation: str
) -> np.ndarray:
    """Load one subject's disconnectome-map, resampled onto reference_img's
    grid if needed, flattened to float32 - never binarized (continuous [0, 1]
    disconnection probability, unlike src/features/lesion.py's
    _load_and_binarize_lesion)."""
    img = nib.load(path)
    if _needs_resample(img, reference_img):
        img = resample_to_img(
            img, reference_img, interpolation=resample_interpolation, force_resample=True, copy_header=True
        )
    return img.get_fdata().ravel().astype(np.float32)


def _stack_voxelwise_matrix(
    admitted: dict[tuple[str, str], Path], reference_img: nib.Nifti1Image, resample_interpolation: str
) -> tuple[np.ndarray, pd.DataFrame]:
    subject_ids: list[str] = []
    dataset_labels: list[str] = []
    vectors: list[np.ndarray] = []
    for (dataset, subject_id), path in sorted(admitted.items()):
        vectors.append(_load_disconnectome_voxels(path, reference_img, resample_interpolation))
        subject_ids.append(subject_id)
        dataset_labels.append(dataset)

    X = np.stack(vectors)
    metadata = pd.DataFrame({"subject_id": subject_ids, "dataset": dataset_labels})
    return X, metadata


def _drop_constant_features(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Same drop as src/features/lesion.py's own _drop_constant_features (not
    imported: private helper, one line - see the _needs_resample comment
    above for this module's stance on cross-module private sharing)."""
    non_constant_mask = X.min(axis=0) != X.max(axis=0)
    return X[:, non_constant_mask], non_constant_mask
