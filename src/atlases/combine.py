"""Merge the Glasser MMP cortical atlas (360 parcels) with a fixed set of 12
subcortical structures from the Harvard-Oxford subcortical atlas into a single
combined label volume - the parcellation used by Thiebaut de Schotten et al.
2020 ahead of their varimax PCA (360 cortical + 12 subcortical = 372 regions;
see assets/papers/Thiebaut de Schotten et al - 2020 - .../markdown/_full.md,
"Data compression").

The paper states the 12 subcortical regions were "defined manually" without
naming a source atlas - there is no file that reproduces them exactly.
Harvard-Oxford subcortical (thr25, 2mm, MNI152) is used here as a documented
practical substitute: same 6 bilateral structures, standard MNI space,
publicly available - not a faithful reproduction of the paper's own ROIs.

The Harvard-Oxford source label values below were read from the atlas's own
authoritative LUT (/data/sw/fsl/data/atlases/HarvardOxford-Subcortical.xml,
0-based index + 1 = voxel value) and cross-checked against real cluster sizes
in the data (hippocampus > amygdala) - not inferred from an offset pattern
observed on a subset of structures, which was tried first and was wrong for
Hippocampus/Amygdala (see docs/debugging/debug_21_07_26.md).
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.image import resample_to_img

CORTICAL_PARCELS_PER_HEMISPHERE = 180
GLASSER_RIGHT_HEMISPHERE_OFFSET = 1000
EXPECTED_COMBINED_LABEL_COUNT = 372

# (name, left_source_value, right_source_value) in HarvardOxford-sub-maxprob-thr25.
# Order matches the atlas's own left-hemisphere block order in
# HarvardOxford-Subcortical.xml; output values below just need to be a stable
# bijection, not a semantically meaningful order.
SUBCORTICAL_STRUCTURES: list[tuple[str, int, int]] = [
    ("Thalamus", 4, 15),
    ("Caudate", 5, 16),
    ("Putamen", 6, 17),
    ("Pallidum", 7, 18),
    ("Hippocampus", 9, 19),
    ("Amygdala", 10, 20),
]


def subcortical_output_mapping() -> dict[int, tuple[int, str]]:
    """Map each Harvard-Oxford source label value to (output value, name).

    Output numbering continues Glasser's own convention (left 1-180, right =
    1000 + left) directly after the 180 cortical parcels per hemisphere: left
    subcortical labels are 181-186, right subcortical labels are 1181-1186.
    Returns e.g. {4: (181, "L_Thalamus"), 15: (1181, "R_Thalamus"), ...} - 12
    entries, one per (structure, hemisphere).
    """
    mapping: dict[int, tuple[int, str]] = {}
    for index, (name, left_source, right_source) in enumerate(SUBCORTICAL_STRUCTURES, start=1):
        left_output = CORTICAL_PARCELS_PER_HEMISPHERE + index
        right_output = GLASSER_RIGHT_HEMISPHERE_OFFSET + CORTICAL_PARCELS_PER_HEMISPHERE + index
        mapping[left_source] = (left_output, f"L_{name}")
        mapping[right_source] = (right_output, f"R_{name}")
    return mapping


def resample_subcortical_to_cortical_grid(
    subcortical_img: nib.Nifti1Image, cortical_img: nib.Nifti1Image
) -> np.ndarray:
    """Resample the subcortical atlas onto the cortical atlas's voxel grid.

    Nearest-neighbour, as for any discrete-label volume (same convention as
    src/features/lesion.py:load_and_resample_atlas) - any other interpolation
    would invent label values that match no real structure.
    """
    if subcortical_img.shape != cortical_img.shape:
        subcortical_img = resample_to_img(
            subcortical_img, cortical_img, interpolation="nearest", force_resample=True, copy_header=True
        )
    return np.asarray(subcortical_img.get_fdata()).astype(np.int64)


def remap_subcortical_labels(subcortical_labels: np.ndarray) -> np.ndarray:
    """Keep only the 12 registered structures, remapped to their output values.

    Every other Harvard-Oxford label (cerebral white matter, cerebral cortex,
    lateral ventricle, brain-stem, accumbens - not part of the paper's 12
    subcortical regions) is dropped: a deliberate, documented selection driven
    by SUBCORTICAL_STRUCTURES, not a silent fallback.
    """
    remapped = np.zeros_like(subcortical_labels)
    for source_value, (output_value, _name) in subcortical_output_mapping().items():
        remapped[subcortical_labels == source_value] = output_value
    return remapped


def merge_cortical_subcortical(
    cortical_labels: np.ndarray, subcortical_labels_remapped: np.ndarray
) -> tuple[np.ndarray, int]:
    """Merge cortical (Glasser) and remapped subcortical labels into one volume.

    Cortical takes priority on overlap: the MMP cortical ribbon is the primary
    parcellation in the source paper, subcortical is an added supplement, so a
    voxel belonging to both keeps its cortical label. Returns (merged,
    n_overlap_voxels) - the overlap count is reported by the caller (QC),
    never silently dropped.
    """
    overlap_mask = (cortical_labels != 0) & (subcortical_labels_remapped != 0)
    merged = np.where(cortical_labels != 0, cortical_labels, subcortical_labels_remapped)
    return merged, int(overlap_mask.sum())


def validate_combined_label_count(labels: np.ndarray) -> None:
    """Raise if the merged volume doesn't have exactly the 372 expected labels."""
    unique_labels = np.unique(labels)
    unique_labels = unique_labels[unique_labels != 0]
    if unique_labels.size != EXPECTED_COMBINED_LABEL_COUNT:
        raise ValueError(
            f"combined atlas has {unique_labels.size} non-zero labels, expected "
            f"{EXPECTED_COMBINED_LABEL_COUNT} (360 cortical + 12 subcortical) - "
            "check the source atlases and SUBCORTICAL_STRUCTURES"
        )


def cortical_label_names(cortical_img: nib.Nifti1Image) -> dict[int, str]:
    """Read the 360 cortical parcel names embedded in the Glasser atlas file.

    Parses the AFNI VALUE_LABEL_DTABLE text extension. That text is chunked
    into ~256-byte pieces by a closing+reopening quote around arbitrary
    newlines, which can split a token mid-word - handled by dropping every
    `"<newline>"` sequence before splitting on the real entry separator
    (`&#x0a;`, still literal at that point). Raises ValueError if the parsed
    result doesn't match the exact expected sequence (0, 1-180, 1001-1180),
    rather than silently returning a partial/misaligned table.
    """
    if not cortical_img.header.extensions:
        raise ValueError("cortical atlas file has no header extensions - cannot read embedded label names")
    content = cortical_img.header.extensions[0].get_content()
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    marker = "ROI_i256"
    if marker not in content:
        raise ValueError(f"cortical atlas file's AFNI extension has no {marker!r} label table")
    start = content.index("&gt;", content.index(marker)) + len("&gt;")
    end = content.index("</AFNI_atr>", start)
    body = content[start:end]

    body = re.sub(r'"\s*\n\s*"', "", body).strip().strip("'\"").strip()
    body = html.unescape(body.replace("&#x0a;", "\n"))

    names: dict[int, str] = {}
    for line in (l.strip() for l in body.split("\n") if l.strip()):
        value_str, _, name = line.partition(" ")
        if not value_str.lstrip("-").isdigit():
            raise ValueError(f"cortical atlas label table: unparsable line {line!r}")
        names[int(value_str)] = name

    expected_values = {0, *range(1, 181), *range(1001, 1181)}
    if names.keys() != expected_values:
        raise ValueError(
            f"cortical atlas label table has {len(names)} entries with unexpected values "
            f"(missing: {sorted(expected_values - names.keys())}, "
            f"unexpected: {sorted(names.keys() - expected_values)})"
        )
    return names


def build_label_table(cortical_names: dict[int, str]) -> pd.DataFrame:
    """Build the (value, name, hemisphere, source) table for all 372 combined labels."""
    rows = []
    for value, name in sorted(cortical_names.items()):
        if value == 0:
            continue
        rows.append(
            {
                "value": value,
                "name": name,
                "hemisphere": "L" if value < GLASSER_RIGHT_HEMISPHERE_OFFSET else "R",
                "source": "glasser_mmp",
            }
        )
    for source_value, (output_value, name) in subcortical_output_mapping().items():
        rows.append(
            {
                "value": output_value,
                "name": name,
                "hemisphere": name[0],
                "source": "harvard_oxford_subcortical",
            }
        )
    return pd.DataFrame(rows).sort_values("value").reset_index(drop=True)


def build_combined_atlas(cortical_path: Path, subcortical_path: Path) -> tuple[np.ndarray, pd.DataFrame, int]:
    """End-to-end: load, resample, remap, merge, validate, build the label table.

    Returns (combined_labels, label_table, n_overlap_voxels). Raises
    ValueError if the result doesn't have exactly the 372 expected labels.
    """
    cortical_img = nib.load(cortical_path)
    subcortical_img = nib.load(subcortical_path)

    subcortical_resampled = resample_subcortical_to_cortical_grid(subcortical_img, cortical_img)
    subcortical_remapped = remap_subcortical_labels(subcortical_resampled)

    cortical_labels = np.asarray(cortical_img.get_fdata()).astype(np.int64)
    combined_labels, n_overlap_voxels = merge_cortical_subcortical(cortical_labels, subcortical_remapped)
    validate_combined_label_count(combined_labels)

    label_table = build_label_table(cortical_label_names(cortical_img))
    return combined_labels, label_table, n_overlap_voxels
