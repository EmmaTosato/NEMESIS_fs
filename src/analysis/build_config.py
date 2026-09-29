"""Parsing/validation of the pipeline configs that read subject imaging off disk
(build_lesion_matrix.json, build_*_matrix.json, compute_lesion_metadata.json).

Same style as src/retrieval/config.py: hand-written _require_*/_optional_*
helpers, every field validated upfront so a bad config is rejected before any
file is touched - never a silent default, never an error surfacing later,
mid-run, from the library code that actually uses the value (e.g. nilearn
rejecting an unknown interpolation kind after minutes of processing).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.features.lesion import LesionGrid, validate_lesion_grids
from src.features.sdc import KNOWN_OBJECTS, KNOWN_REPRESENTATIONS, KNOWN_VALUE_COLUMNS
from src.retrieval.config import KNOWN_GROUPS

_KNOWN_INTERPOLATIONS = frozenset({"linear", "nearest", "continuous"})


@dataclass(frozen=True)
class BuildMatrixConfig:
    project: str
    data_root: Path
    datasets: list[str]
    group_filter: list[str] | None
    reference_template_path: Path
    lesion_glob: str
    binarize_threshold: float
    resample_interpolation: str
    excluded_subjects_path: Path
    correct_out_of_brain: bool
    brain_mask_path: Path | None
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_build_matrix_config(path: str | Path) -> BuildMatrixConfig:
    """Load and validate a build_lesion_matrix.json file.

    Raises ValueError identifying the offending field for any structural
    problem (missing field, wrong type, out-of-domain value).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    datasets = _require_unique_str_list(raw, "datasets")
    reference_template_path = Path(_require_str(raw, "reference_template_path"))

    resample_interpolation = _validate_resample_interpolation(_require_str(raw, "resample_interpolation"))
    binarize_threshold = _require_float_in_range(raw, "binarize_threshold", 0.0, 1.0)

    # correct_out_of_brain zeroes a subject's out-of-brain lesion voxels and keeps the subject.
    # It is the only use of brain_mask_path here, so that field is required exactly when it is
    # active. There is no threshold-based admission filter in this config any more: which
    # borderline subject to drop is decided from assets/metadata/lesion_metadata.csv and
    # recorded in excluded_subjects_path, read by the SDC matrix too - see
    # docs/dev/lesion_matrix.md and .claude/history/methods_changelog.md.
    correct_out_of_brain = _optional_bool(raw, "correct_out_of_brain")
    brain_mask_path_raw = _optional_str(raw, "brain_mask_path")
    brain_mask_path = Path(brain_mask_path_raw) if brain_mask_path_raw is not None else None
    if correct_out_of_brain and brain_mask_path is None:
        raise ValueError("config: correct_out_of_brain is set but brain_mask_path is missing")

    return BuildMatrixConfig(
        project=_require_str(raw, "project"),
        data_root=Path(_require_str(raw, "data_root")),
        datasets=datasets,
        group_filter=_optional_group_filter(raw),
        reference_template_path=reference_template_path,
        lesion_glob=_require_str(raw, "lesion_glob"),
        binarize_threshold=binarize_threshold,
        resample_interpolation=resample_interpolation,
        excluded_subjects_path=Path(_require_str(raw, "excluded_subjects_path")),
        correct_out_of_brain=correct_out_of_brain,
        brain_mask_path=brain_mask_path,
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )


def _require_str(raw: dict, key: str) -> str:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string, got {value!r}")
    return value


def _require_bool(raw: dict, key: str) -> bool:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, bool):
        raise ValueError(f"config: field {key!r} must be a boolean, got {value!r}")
    return value


def _require_unique_str_list(raw: dict, key: str) -> list[str]:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"config: field {key!r} must be a non-empty list of non-empty strings, got {value!r}")
    duplicates = {v for v in value if value.count(v) > 1}
    if duplicates:
        raise ValueError(f"config: field {key!r} has duplicate entries: {sorted(duplicates)}")
    return value


def _optional_str(raw: dict, key: str) -> str | None:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"config: field {key!r} must be a non-empty string when set, got {value!r}")
    return value


def _require_float_in_range(raw: dict, key: str, lo: float, hi: float) -> float:
    if key not in raw:
        raise ValueError(f"config: missing required field {key!r}")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"config: field {key!r} must be a number, got {value!r}")
    value = float(value)
    if not (lo <= value <= hi):
        raise ValueError(f"config: field {key!r} must be between {lo} and {hi}, got {value}")
    return value


def _optional_bool(raw: dict, key: str) -> bool:
    if key not in raw or raw[key] is None:
        return False
    value = raw[key]
    if not isinstance(value, bool):
        raise ValueError(f"config: field {key!r} must be a boolean when set, got {value!r}")
    return value


def _optional_group_filter(raw: dict) -> list[str] | None:
    """Same convention as src.retrieval.config._optional_group_filter: absent/null
    means no restriction, present means exactly these groups (src.retrieval.dataset.group_of)."""
    value = raw.get("group_filter")
    if value is None:
        return None
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f"config: field 'group_filter' must be a non-empty list of non-empty strings, got {value!r}")
    unknown = [g for g in value if g not in KNOWN_GROUPS]
    if unknown:
        raise ValueError(f"config: group_filter contains unknown group(s) {unknown} (known: {KNOWN_GROUPS})")
    return value


def _validate_resample_interpolation(value: str) -> str:
    if value not in _KNOWN_INTERPOLATIONS:
        raise ValueError(
            f"config: field 'resample_interpolation' must be one of {sorted(_KNOWN_INTERPOLATIONS)}, got {value!r}"
        )
    return value


@dataclass(frozen=True)
class MaskFcConfig:
    project: str
    data_root: Path
    dataset: str
    group_filter: list[str] | None
    atlas_root: Path
    atlas_combos: list[str]
    lesion_glob: str
    fc_glob_template: str
    min_coverage: float
    resample_interpolation: str
    binarize_threshold: float
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_mask_fc_config(path: str | Path) -> MaskFcConfig:
    """Load and validate a mask_fc.json file.

    Deliberately decoupled from build_fc_matrix.json (own config, own loader,
    own dataclass) - the two pipelines are independent: this one turns raw
    lesion masks + raw FC matrices into NaN-masked per-subject matrices,
    nothing else reads a lesion mask or an atlas past this point.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    return MaskFcConfig(
        project=_require_str(raw, "project"),
        data_root=Path(_require_str(raw, "data_root")),
        dataset=_require_str(raw, "dataset"),
        group_filter=_optional_group_filter(raw),
        atlas_root=Path(_require_str(raw, "atlas_root")),
        atlas_combos=_require_unique_str_list(raw, "atlas_combos"),
        lesion_glob=_require_str(raw, "lesion_glob"),
        fc_glob_template=_require_str(raw, "fc_glob_template"),
        min_coverage=_require_float_in_range(raw, "min_coverage", 0.0, 1.0),
        resample_interpolation=_validate_resample_interpolation(_require_str(raw, "resample_interpolation")),
        binarize_threshold=_require_float_in_range(raw, "binarize_threshold", 0.0, 1.0),
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )


@dataclass(frozen=True)
class BuildFcMatrixConfig:
    project: str
    masked_fc_root: Path
    atlas_combos: list[str]
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_build_fc_matrix_config(path: str | Path) -> BuildFcMatrixConfig:
    """Load and validate a build_fc_matrix.json file.

    No lesion_glob, no atlas_path, no min_coverage here - this pipeline reads
    only the already-masked CSVs mask_fc.py already wrote (masked_fc_root),
    by design (see src/features/functional.py module docstring).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    return BuildFcMatrixConfig(
        project=_require_str(raw, "project"),
        masked_fc_root=Path(_require_str(raw, "masked_fc_root")),
        atlas_combos=_require_unique_str_list(raw, "atlas_combos"),
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )


@dataclass(frozen=True)
class SdcMatrixConfig:
    project: str
    data_root: Path
    datasets: list[str]
    group_filter: list[str] | None
    excluded_subjects_path: Path
    object: str
    representation: str
    # parcellated-only (None when representation="voxelwise")
    atlas: str | None
    value_column: str | None
    reference_labels_path: Path | None
    # voxelwise-only (None when representation="parcellated")
    reference_template_path: Path | None
    resample_interpolation: str | None
    output_root: Path
    session_name: str
    overwrite: bool
    run_notes: str | None


def load_build_sdc_matrix_config(path: str | Path) -> SdcMatrixConfig:
    """Load and validate a build_sdc_matrix.json file.

    `representation` ("parcellated" or "voxelwise", added 03/09) picks which
    of the two src.features.sdc builders runs - see that module's docstring.
    Each representation has its own required fields, validated only for the
    representation actually requested (never a silent default for the other
    mode's fields, never required-but-unused):
    - "parcellated": atlas, value_column, reference_labels_path.
    - "voxelwise": reference_template_path, resample_interpolation - same
      field names as build_lesion_matrix.json's own voxel-wise config, no
      binarize_threshold (disconnectome values are continuous, never
      binarized - see src.features.sdc.build_sdc_voxelwise_matrix).

    object/value_column/representation are validated against
    src.features.sdc's known sets upfront - a typo here would otherwise only
    surface after the first subject's file is opened, possibly after
    hundreds have already been discovered. "voxelwise" additionally rejects
    object="lesion" here too (src.features.sdc raises the same check again at
    call time - config-load time just fails faster).

    No lesion_glob field - unlike build_lesion_matrix.json, lesion mask
    presence is resolved from assets/metadata/participants.csv (has_lesion)
    (src.utils.participants), not from a glob against data_root - see
    docs/dev/sdc_matrix.md.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    object_ = _require_str(raw, "object")
    if object_ not in KNOWN_OBJECTS:
        raise ValueError(f"config: field 'object' must be one of {sorted(KNOWN_OBJECTS)}, got {object_!r}")

    representation = _require_str(raw, "representation")
    if representation not in KNOWN_REPRESENTATIONS:
        raise ValueError(
            f"config: field 'representation' must be one of {sorted(KNOWN_REPRESENTATIONS)}, got {representation!r}"
        )

    if representation == "voxelwise" and object_ != "disconnectome":
        raise ValueError(
            "config: representation='voxelwise' only supports object='disconnectome' - the lesion-map "
            f"equivalent is already built by build_lesion_matrix.json from its own authoritative source, "
            f"got object={object_!r}"
        )

    if representation == "parcellated":
        value_column = _require_str(raw, "value_column")
        if value_column not in KNOWN_VALUE_COLUMNS:
            raise ValueError(
                f"config: field 'value_column' must be one of {sorted(KNOWN_VALUE_COLUMNS)}, got {value_column!r}"
            )
        atlas = _require_str(raw, "atlas")
        reference_labels_path = Path(_require_str(raw, "reference_labels_path"))
        reference_template_path = None
        resample_interpolation = None
    else:
        atlas = None
        value_column = None
        reference_labels_path = None
        reference_template_path = Path(_require_str(raw, "reference_template_path"))
        resample_interpolation = _validate_resample_interpolation(_require_str(raw, "resample_interpolation"))

    return SdcMatrixConfig(
        project=_require_str(raw, "project"),
        data_root=Path(_require_str(raw, "data_root")),
        datasets=_require_unique_str_list(raw, "datasets"),
        group_filter=_optional_group_filter(raw),
        excluded_subjects_path=Path(_require_str(raw, "excluded_subjects_path")),
        object=object_,
        representation=representation,
        atlas=atlas,
        value_column=value_column,
        reference_labels_path=reference_labels_path,
        reference_template_path=reference_template_path,
        resample_interpolation=resample_interpolation,
        output_root=Path(_require_str(raw, "output_root")),
        session_name=_require_str(raw, "session_name"),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )


@dataclass(frozen=True)
class LesionMetadataConfig:
    """Config for src/pipeline/compute_lesion_metadata.py.

    Shares its mask-handling fields with BuildMatrixConfig (data_root/datasets/group_filter/
    lesion_glob/binarize_threshold/resample_interpolation) because it reads the same masks the
    same way - but deliberately as its own file, not by reading build_lesion_matrix.json: the
    metrics registry describes every subject with a mask, while a matrix run describes one
    chosen cohort, and coupling the two is what previously made "the volume" ambiguous
    (.claude/history/project_changelog.md, 29-09-26).

    `grids` replaces BuildMatrixConfig's single reference_template_path/brain_mask_path pair:
    every metric is computed once per grid, and each grid's name becomes the suffix of the four
    columns it produces (see src.features.lesion.compute_lesion_metadata).
    """

    project: str
    data_root: Path
    datasets: list[str]
    group_filter: list[str] | None
    lesion_glob: str
    binarize_threshold: float
    resample_interpolation: str
    grids: list[LesionGrid]
    correct_out_of_brain: bool
    side_threshold: float
    output_path: Path
    overwrite: bool
    run_notes: str | None


def load_compute_lesion_metadata_config(path: str | Path) -> LesionMetadataConfig:
    """Load and validate a compute_lesion_metadata.json file.

    `grids` is an object of {name: {reference_template_path, brain_mask_path}}, both required
    for every grid - unlike build_lesion_matrix.json, where brain_mask_path is optional because
    the correction it feeds is optional. Here there is no run without it: the out-of-brain
    fraction and the correction are the reason a grid exists.

    Grid names are validated by src.features.lesion.validate_lesion_grids (non-empty, alphanumeric,
    unique) rather than re-checked here - one definition of what makes a grid name usable,
    living next to the code that turns it into a column suffix.

    `side_threshold` is range-checked here but its *calibration* is a separate concern
    (src/pipeline/calibrate_lesion_side_threshold.py): 0.20 reproduces 97.4% of 1445
    clinically-labelled subjects on the 2mm grid, and that calibration does not automatically
    transfer to a finer grid - see knowledge/neuroimaging/lesion_laterality.md.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open() as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config: top-level content must be a JSON object, got {raw!r}")

    grids = _require_lesion_grids(raw)
    # Validated here, at config-load time, rather than only inside compute_lesion_metadata:
    # a duplicate/unusable grid name must be rejected before any mask is opened.
    validate_lesion_grids(grids)

    return LesionMetadataConfig(
        project=_require_str(raw, "project"),
        data_root=Path(_require_str(raw, "data_root")),
        datasets=_require_unique_str_list(raw, "datasets"),
        group_filter=_optional_group_filter(raw),
        lesion_glob=_require_str(raw, "lesion_glob"),
        binarize_threshold=_require_float_in_range(raw, "binarize_threshold", 0.0, 1.0),
        resample_interpolation=_validate_resample_interpolation(_require_str(raw, "resample_interpolation")),
        grids=grids,
        correct_out_of_brain=_require_bool(raw, "correct_out_of_brain"),
        # Upper bound exclusive: a threshold of 1.0 would classify every subject "both",
        # including a strictly unilateral lesion (|index| == 1.0 is not < 1.0 - but nothing
        # can exceed it either, so no subject could ever be left/right).
        side_threshold=_require_float_in_range(raw, "side_threshold", 0.0, 1.0),
        output_path=Path(_require_str(raw, "output_path")),
        overwrite=_require_bool(raw, "overwrite"),
        run_notes=_optional_str(raw, "run_notes"),
    )


def _require_lesion_grids(raw: dict) -> list[LesionGrid]:
    """Parse 'grids': {name: {reference_template_path, brain_mask_path}}, preserving the file's
    own key order (that order is the column order of the resulting CSV)."""
    if "grids" not in raw:
        raise ValueError("config: missing required field 'grids'")
    value = raw["grids"]
    if not isinstance(value, dict) or not value:
        raise ValueError(f"config: field 'grids' must be a non-empty object, got {value!r}")

    grids: list[LesionGrid] = []
    for name, entry in value.items():
        if not isinstance(entry, dict):
            raise ValueError(f"config: field 'grids.{name}' must be an object, got {entry!r}")
        for field in ("reference_template_path", "brain_mask_path"):
            if field not in entry:
                raise ValueError(
                    f"config: field 'grids.{name}' is missing {field!r} - both are required for every "
                    "grid (the out-of-brain fraction and the correction are why a grid is measured)"
                )
            if not isinstance(entry[field], str) or not entry[field]:
                raise ValueError(f"config: field 'grids.{name}.{field}' must be a non-empty string")
        grids.append(
            LesionGrid(
                name=name,
                reference_template_path=Path(entry["reference_template_path"]),
                brain_mask_path=Path(entry["brain_mask_path"]),
            )
        )
    return grids
