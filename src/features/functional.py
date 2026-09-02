"""Mask FC (functional connectivity) matrices by lesion overlap, and build a
subjects x edges feature matrix from the masked output.

Two-stage pipeline, deliberately decoupled (config included) between two
pipeline scripts: `src/pipeline/mask_fc.py` (this module's `mask_dataset_fc`)
marks FC rows/cols of lesion-compromised parcels as NaN - never a concrete
fill value, which belongs only immediately before a method that cannot
accept missing values (see docs/dev/fc_matrix.md for the literature behind
this split). `src/pipeline/build_fc_matrix.py` (this module's
`build_fc_matrix_from_masked`) reads only the already-masked CSVs stage 1
wrote, never the raw lesion/FC data again.

Migrated from notebooks/fc_lesion_masking.ipynb, validated against real
WashU subjects before landing here - see docs/dev/fc_matrix.md for the
nilearn pitfalls found during that validation.
"""

from __future__ import annotations

import logging
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from nibabel.filebasedimages import ImageFileError
from nilearn.image import resample_to_img
from nilearn.maskers import NiftiLabelsMasker

from src.features.subject_discovery import discover_files_by_subject

# Single source of truth for the per-combo summary filename mask_fc.py writes
# (subject_id/dataset/n_compromised_nodes) - src.pipeline.mask_fc imports this rather than
# holding its own copy of the literal, and build_fc_matrix_from_masked reads it back to learn
# each subject's dataset (2026-09-02: build_fc_matrix.py's metadata.csv never carried a
# "dataset" column at all - stack_fc_vectors used to write subject_id only. dataset is only
# ever genuinely known where mask_fc.py's own config declares it, not something
# build_fc_matrix_from_masked can infer from a masked_fc/<combo>/ folder's own contents -
# reading it back from mask_summary.csv, rather than accepting a single per-run config value
# here, stays correct even if a combo folder is ever populated by more than one dataset's
# mask_fc.py run - lessons_learned.md #14/#20, never trust a folder's incidental structure).
MASK_SUMMARY_FILENAME = "mask_summary.csv"


def resolve_atlas_paths(atlas_root: Path, combo: str) -> tuple[Path, Path]:
    """Resolve the BIDS-Derivatives nii.gz + tsv paths for one atlas combo folder.

    combo is the bare name (e.g. "Yan200TianS2Buckner7N") - the "atlas-" BIDS
    prefix and the "_res-2_" (2mm) suffix are added here, matching the
    convention used by the server source (Atlases/fmriprep/) and mirrored
    locally at assets/atlases/fmriprep/.
    """
    combo_dir = Path(atlas_root) / f"atlas-{combo}"
    nii_path = combo_dir / f"atlas-{combo}_space-MNI152NLin6Asym_res-2_dseg.nii.gz"
    tsv_path = combo_dir / f"atlas-{combo}_dseg.tsv"
    return nii_path, tsv_path


def load_atlas(atlas_path: Path, label_table_path: Path) -> tuple[nib.Nifti1Image, pd.DataFrame]:
    """Load a combined label volume and its BIDS dseg.tsv (index/label) lookup.

    Raises FileNotFoundError if either file is missing, ValueError if the
    label table doesn't have the expected columns, has a duplicate 'index'
    value, or has an 'index' value absent from the volume itself - see
    docs/dev/fc_matrix.md for why each check exists.
    """
    atlas_path = Path(atlas_path)
    label_table_path = Path(label_table_path)
    if not atlas_path.is_file():
        raise FileNotFoundError(f"atlas_path not found: {atlas_path}")
    if not label_table_path.is_file():
        raise FileNotFoundError(f"label_table_path not found: {label_table_path}")

    atlas_img = nib.squeeze_image(nib.load(atlas_path))
    label_table = pd.read_csv(label_table_path, sep="\t")
    if not {"index", "label"}.issubset(label_table.columns):
        raise ValueError(
            f"label table {label_table_path} must have 'index' and 'label' columns, got {list(label_table.columns)}"
        )

    duplicated_indices = sorted(label_table.loc[label_table["index"].duplicated(), "index"].unique().tolist())
    if duplicated_indices:
        raise ValueError(
            f"label table {label_table_path} has duplicate 'index' value(s) {duplicated_indices} - "
            "expected exactly one row per parcel index"
        )

    volume_indices = set(np.unique(atlas_img.get_fdata()).astype(int).tolist()) - {0}  # 0 is background, not a parcel
    tsv_indices = set(int(i) for i in label_table["index"])
    missing_from_volume = sorted(tsv_indices - volume_indices)
    if missing_from_volume:
        raise ValueError(
            f"label table {label_table_path} has {len(missing_from_volume)} index value(s) "
            f"{missing_from_volume} absent from the atlas volume {atlas_path} "
            f"({len(volume_indices)} parcel label(s) found there) - tsv/volume are out of sync"
        )
    return atlas_img, label_table


def compute_parcel_coverage(atlas_img: nib.Nifti1Image, label_ids: list[int], healthy_img: nib.Nifti1Image) -> np.ndarray:
    """Fraction of healthy (non-lesioned) voxels per parcel, in label_ids order.

    Two library pitfalls handled explicitly (lessons_learned.md #13): a
    too-narrow counting-image dtype silently overflows NiftiLabelsMasker's
    "sum" strategy (fixed with int32, never uint8/int16), and a parcel with
    zero surviving voxels after masking is dropped from the masked masker's
    labels_ entirely rather than read as 0 - both maskers are therefore
    indexed by their own labels_, never by position, and an absent label is
    treated as coverage=0.0 explicitly.
    """
    ones_img = nib.Nifti1Image(np.ones(atlas_img.shape, dtype=np.int32), atlas_img.affine, atlas_img.header)

    masker_total = NiftiLabelsMasker(labels_img=atlas_img, background_label=0, strategy="sum", standardize=None)
    n_total = np.atleast_1d(np.squeeze(masker_total.fit_transform(ones_img)))
    # labels_[1:]: labels_[0] is always the "Background" placeholder (label 0), not a real parcel.
    total_by_label = dict(zip(masker_total.labels_[1:], n_total))

    masker_healthy = NiftiLabelsMasker(
        labels_img=atlas_img, mask_img=healthy_img, background_label=0, strategy="sum", standardize=None
    )
    n_healthy = np.atleast_1d(np.squeeze(masker_healthy.fit_transform(ones_img)))
    healthy_by_label = dict(zip(masker_healthy.labels_[1:], n_healthy))

    # .get(lbl, 0.0): a label absent from healthy_by_label (fully lesioned, 0 voxels
    # survived the mask) is 0.0 coverage - never a KeyError, never silently skipped.
    return np.array([healthy_by_label.get(lbl, 0.0) / total_by_label[lbl] for lbl in label_ids])


def resample_lesion_to_atlas(
    lesion_img: nib.Nifti1Image, atlas_img: nib.Nifti1Image, resample_interpolation: str, binarize_threshold: float
) -> np.ndarray:
    """Resample a lesion mask onto the atlas's voxel grid and re-binarize it.

    Resampling always happens, even when lesion_img.shape == atlas_img.shape:
    identical shape does not imply identical orientation (affine) - verified
    on real WashU data, where the lesion mask and the server atlas share the
    same shape but an opposite-sign X axis (docs/dev/fc_matrix.md).
    """
    lesion_resampled = resample_to_img(
        lesion_img, atlas_img, interpolation=resample_interpolation, force_resample=True, copy_header=True
    )
    return (np.asarray(lesion_resampled.get_fdata()) > binarize_threshold).astype(np.int32)


def find_compromised_nodes(parcel_coverage: np.ndarray, node_names: np.ndarray, min_coverage: float) -> np.ndarray:
    """Node names whose healthy-voxel coverage is below min_coverage."""
    return node_names[parcel_coverage < min_coverage]


def mask_fc_by_lesion(fc: pd.DataFrame, node_names: np.ndarray, compromised_names: np.ndarray) -> pd.DataFrame:
    """Set rows/columns of compromised_names to NaN in a copy of fc.

    Raises ValueError if fc's row/column labels don't exactly match
    node_names, in that order - a masking step must never align by position.
    """
    if list(fc.index) != list(node_names):
        raise ValueError("fc matrix row labels do not match the atlas node order - refusing to mask by position")
    if list(fc.columns) != list(node_names):
        raise ValueError("fc matrix column labels do not match the atlas node order - refusing to mask by position")

    fc_masked = fc.copy()
    fc_masked.loc[compromised_names, :] = np.nan
    fc_masked.loc[:, compromised_names] = np.nan
    return fc_masked


def vectorize_upper_triangle(matrix_df: pd.DataFrame, node_names: np.ndarray) -> pd.Series:
    """Upper triangle (diagonal excluded) as a named 1D vector - the FC
    matrix is symmetric with a non-informative diagonal (self-correlation
    1.0). Raises ValueError if the lower triangle actually disagrees with
    the upper one, instead of silently discarding whichever half the lower
    triangle held - see docs/dev/fc_matrix.md.
    """
    values_matrix = matrix_df.values
    if not np.allclose(values_matrix, values_matrix.T, equal_nan=True):
        raise ValueError(
            "matrix_df is not symmetric - refusing to vectorize only its upper triangle, "
            "which would silently discard real information in the (differing) lower triangle"
        )
    n = len(node_names)
    row_idx, col_idx = np.triu_indices(n, k=1)
    edge_names = [f"{node_names[i]}__{node_names[j]}" for i, j in zip(row_idx, col_idx)]
    values = values_matrix[row_idx, col_idx]
    return pd.Series(values, index=edge_names)


def mask_subject_fc(
    lesion_img: nib.Nifti1Image,
    fc: pd.DataFrame,
    atlas_img: nib.Nifti1Image,
    label_ids: list[int],
    node_names: np.ndarray,
    min_coverage: float,
    resample_interpolation: str,
    binarize_threshold: float,
) -> tuple[pd.DataFrame, np.ndarray]:
    """End-to-end per-subject masking: lesion -> parcel coverage -> NaN-mask the FC matrix.

    Returns (fc_masked, compromised_names). Writing fc_masked to disk and
    reporting compromised_names is the caller's job (mask_dataset_fc below).
    """
    lesion_data = resample_lesion_to_atlas(lesion_img, atlas_img, resample_interpolation, binarize_threshold)
    healthy_img = nib.Nifti1Image((1 - lesion_data), atlas_img.affine, atlas_img.header)
    parcel_coverage = compute_parcel_coverage(atlas_img, label_ids, healthy_img)
    compromised_names = find_compromised_nodes(parcel_coverage, node_names, min_coverage)
    fc_masked = mask_fc_by_lesion(fc, node_names, compromised_names)
    return fc_masked, compromised_names


def discover_subject_files(
    data_root: Path,
    dataset: str,
    atlas_combo: str,
    lesion_glob: str,
    fc_glob_template: str,
    group_filter: list[str] | None,
) -> tuple[dict[str, tuple[Path, Path]], list[str], list[str]]:
    """Subjects with both a lesion mask and an FC matrix for atlas_combo, restricted to group_filter.

    Returns ({subject_id: (lesion_path, fc_path)}, subjects_missing_lesion,
    subjects_excluded_by_group). group_filter restricts by each subject's
    naming-derived group BEFORE the lesion/FC intersection is computed - an
    HC subject (e.g. WashU) is not a "missing lesion mask" gap but a
    structurally different population this pipeline doesn't apply to (see
    docs/dev/fc_matrix.md). group_filter=None means no restriction.

    Raises ValueError if no subject has both, within group_filter (likely a
    config error - wrong dataset/atlas_combo/group_filter).
    """
    dataset_root = Path(data_root) / dataset
    fc_glob = fc_glob_template.format(combo=atlas_combo)
    if not any(dataset_root.glob(fc_glob)):
        raise FileNotFoundError(f"no FC files found matching {fc_glob!r} under {dataset_root}")

    fc_by_subject, fc_excluded = discover_files_by_subject(data_root, dataset, fc_glob, group_filter)
    lesion_by_subject, lesion_excluded = discover_files_by_subject(data_root, dataset, lesion_glob, group_filter)
    excluded_by_group = sorted(set(fc_excluded) | set(lesion_excluded))

    usable_subjects = sorted(fc_by_subject.keys() & lesion_by_subject.keys())
    missing_lesion = sorted(fc_by_subject.keys() - lesion_by_subject.keys())
    if not usable_subjects:
        raise ValueError(
            f"no subject under {dataset_root} has both a lesion mask and an FC file for {atlas_combo!r}"
            + (f" within group_filter={group_filter}" if group_filter is not None else "")
        )

    subject_files = {subject: (lesion_by_subject[subject], fc_by_subject[subject]) for subject in usable_subjects}
    return subject_files, missing_lesion, excluded_by_group


def mask_dataset_fc(
    data_root: Path,
    dataset: str,
    atlas_path: Path,
    label_table_path: Path,
    atlas_combo: str,
    lesion_glob: str,
    fc_glob_template: str,
    min_coverage: float,
    resample_interpolation: str,
    binarize_threshold: float,
    output_dir: Path,
    group_filter: list[str] | None,
) -> tuple[pd.DataFrame, list[str], list[str], dict[str, str]]:
    """Mask every discoverable subject's FC matrix and write it to output_dir.

    Returns (summary, missing_lesion, excluded_by_group, failed) - summary
    has one row per masked subject (subject_id, dataset, n_compromised_nodes),
    missing_lesion/excluded_by_group as in discover_subject_files, and
    failed is subject_id -> reason for any subject whose own lesion/FC file
    couldn't be read or masked - isolated per-subject (lesson #21) so one
    bad file costs only that subject, not the whole combo/run.
    """
    atlas_img, label_table = load_atlas(atlas_path, label_table_path)
    label_ids = label_table["index"].tolist()
    id_to_name = dict(zip(label_table["index"], label_table["label"]))
    node_names = np.array([id_to_name[i] for i in label_ids])

    subject_files, missing_lesion, excluded_by_group = discover_subject_files(
        data_root, dataset, atlas_combo, lesion_glob, fc_glob_template, group_filter
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    failed: dict[str, str] = {}
    for subject, (lesion_path, fc_path) in subject_files.items():
        # One bad subject (truncated lesion mask, malformed FC csv, node-order mismatch)
        # must not cost the whole combo - subjects already masked earlier in this same
        # loop stay written, and failed reports exactly which subject/why (lesson #21).
        try:
            lesion_img = nib.load(lesion_path)
            fc = pd.read_csv(fc_path, sep="\t", index_col=0)
            # mask_subject_fc -> mask_fc_by_lesion already raises ValueError for a node-order
            # mismatch (checking both .index/.columns) - no redundant pre-check here
            # (AUDIT_FINDINGS.md #50, see docs/dev/fc_matrix.md).
            fc_masked, compromised_names = mask_subject_fc(
                lesion_img, fc, atlas_img, label_ids, node_names, min_coverage, resample_interpolation, binarize_threshold
            )
            fc_masked.to_csv(output_dir / f"{subject}_masked_fc.csv")
        except (OSError, ValueError, ImageFileError, pd.errors.ParserError) as exc:
            logging.warning("%s: skipped, could not be masked: %s", subject, exc)
            failed[subject] = str(exc)
            continue
        rows.append({"subject_id": subject, "dataset": dataset, "n_compromised_nodes": len(compromised_names)})

    summary = pd.DataFrame(rows).sort_values("subject_id").reset_index(drop=True)
    return summary, missing_lesion, excluded_by_group, failed


def discover_masked_fc_files(masked_fc_dir: Path) -> dict[str, Path]:
    """One masked FC CSV per subject found under masked_fc_dir (<subject>_masked_fc.csv)."""
    masked_fc_dir = Path(masked_fc_dir)
    files = sorted(masked_fc_dir.glob("*_masked_fc.csv"))
    if not files:
        raise FileNotFoundError(f"no masked FC files found under {masked_fc_dir} - run mask_fc.py first")
    return {f.name.removesuffix("_masked_fc.csv"): f for f in files}


def stack_fc_vectors(vectors: dict[str, pd.Series], dataset_by_subject: dict[str, str]) -> tuple[np.ndarray, pd.DataFrame, list[str]]:
    """Stack per-subject edge vectors into X (subjects x edges) + metadata.

    dataset_by_subject must have an entry for every subject in vectors - raises ValueError
    listing whichever are missing, rather than writing a metadata.csv with a blank/guessed
    dataset for some subjects (code_standards.md §0).

    Raises ValueError if any subject's edge labels/order differ from the
    first subject's - never stacked by position across mismatched subjects.
    """
    subject_ids = list(vectors)
    missing_dataset = [s for s in subject_ids if s not in dataset_by_subject]
    if missing_dataset:
        raise ValueError(f"no 'dataset' entry for {len(missing_dataset)} subject(s): {missing_dataset}")

    reference_edges = list(vectors[subject_ids[0]].index)
    for subject_id in subject_ids[1:]:
        if list(vectors[subject_id].index) != reference_edges:
            raise ValueError(f"{subject_id}: edge labels do not match the reference subject {subject_ids[0]!r}")

    X = np.stack([vectors[subject_id].values for subject_id in subject_ids])
    metadata = pd.DataFrame({"subject_id": subject_ids, "dataset": [dataset_by_subject[s] for s in subject_ids]})
    return X, metadata, reference_edges


def _load_dataset_by_subject(masked_fc_dir: Path) -> dict[str, str]:
    """Reads {subject_id: dataset} from masked_fc_dir's own mask_summary.csv (mask_fc.py's
    output, written from its own config.dataset - see MASK_SUMMARY_FILENAME).

    Raises FileNotFoundError if mask_summary.csv is absent (masked_fc_dir wasn't produced by
    mask_fc.py, or predates 2026-09-02's dataset column and needs a one-off backfill instead
    of a silent guess here) - same for a "dataset" column missing from an old-format file.
    """
    summary_path = masked_fc_dir / MASK_SUMMARY_FILENAME
    if not summary_path.is_file():
        raise FileNotFoundError(
            f"{summary_path} not found - build_fc_matrix_from_masked needs mask_fc.py's own "
            f"{MASK_SUMMARY_FILENAME} to know each subject's dataset, not just the *_masked_fc.csv files"
        )
    summary = pd.read_csv(summary_path, dtype=str)
    if "dataset" not in summary.columns:
        raise ValueError(
            f"{summary_path} has no 'dataset' column - either re-run mask_fc.py, or this is an "
            "artifact from before 2026-09-02 and needs a one-off backfill, not a silent guess here"
        )
    return dict(zip(summary["subject_id"], summary["dataset"]))


def drop_constant_edges(X: np.ndarray, edge_names: list[str]) -> tuple[np.ndarray, list[str], list[tuple[str, float]]]:
    """Drop edges with an identical value across every subject that has one.

    An edge with any NaN is never evaluated for constancy - kept
    unconditionally (the per-subject/per-edge exclusion threshold question
    is settled, not open - see docs/dev/fc_matrix.md). Returns
    (X_filtered, kept_edge_names, dropped_info) - the caller (build_fc_matrix.py)
    logs dropped_info explicitly, since an exactly-identical continuous FC
    value across every subject is unexpected and worth a human look.

    A single-subject X is a degenerate input this check was never meant to
    answer (AUDIT_FINDINGS.md #55, see docs/dev/fc_matrix.md) - X is
    returned unchanged rather than silently discarding every edge.
    """
    if X.shape[0] <= 1:
        logging.warning(
            "drop_constant_edges: only %d subject(s) in X - the constant-edge check is undefined "
            "with a single subject (every fully-observed edge trivially has min==max), skipped "
            "entirely rather than dropping every edge",
            X.shape[0],
        )
        return X, list(edge_names), []

    fully_observed = ~np.isnan(X).any(axis=0)
    is_constant = np.zeros(X.shape[1], dtype=bool)
    if fully_observed.any():
        observed = X[:, fully_observed]
        is_constant[fully_observed] = observed.min(axis=0) == observed.max(axis=0)

    keep_mask = ~is_constant
    dropped_info = [(edge_names[i], float(X[0, i])) for i in np.where(is_constant)[0]]
    kept_edge_names = [name for name, keep in zip(edge_names, keep_mask) if keep]
    return X[:, keep_mask], kept_edge_names, dropped_info


def build_fc_matrix_from_masked(masked_fc_dir: Path) -> tuple[np.ndarray, pd.DataFrame, list[str], list[tuple[str, float]]]:
    """Vectorize + stack every masked FC matrix under masked_fc_dir into one X.

    Reads only the already-masked CSVs (stage 1's output) - no lesion mask,
    no atlas, no raw FC data touched here, by design (the two pipelines are
    fully decoupled). The node order is taken from the first subject found
    and every other subject is checked against it - never assumed to match.

    Returns (X, metadata, edge_names, dropped_constant_edges) - X still has
    NaN in it (compromised edges); imputation is a separate, later step
    (src/analysis/, not here - see module docstring).
    """
    masked_fc_dir = Path(masked_fc_dir)
    subject_files = discover_masked_fc_files(masked_fc_dir)
    dataset_by_subject = _load_dataset_by_subject(masked_fc_dir)

    vectors: dict[str, pd.Series] = {}
    reference_node_names: np.ndarray | None = None
    for subject, path in subject_files.items():
        fc_masked = pd.read_csv(path, index_col=0)
        if reference_node_names is None:
            reference_node_names = np.array(fc_masked.index)
        elif list(fc_masked.index) != list(reference_node_names) or list(fc_masked.columns) != list(
            reference_node_names
        ):
            raise ValueError(f"{subject}: node order in {path} does not match the reference subject's order")
        vectors[subject] = vectorize_upper_triangle(fc_masked, reference_node_names)

    X, metadata, edge_names = stack_fc_vectors(vectors, dataset_by_subject)
    X_filtered, kept_edge_names, dropped_info = drop_constant_edges(X, edge_names)
    return X_filtered, metadata, kept_edge_names, dropped_info
