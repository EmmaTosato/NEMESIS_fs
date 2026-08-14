# Lesion feature matrix — technical reference

Audience: developers/agents working on `src/features/lesion.py`, `src/analysis/build_config.py` (the `build_lesion_matrix.json`-parsing half), and `src/pipeline/build_lesion_matrix.py`.

This file covers turning retrieved lesion masks into a feature matrix ready for dimensionality reduction. For the models that consume that matrix, see `docs/dev/models.md`. For the equivalent FC pipeline, see `docs/dev/fc_matrix.md`. For "how do I run this", see `docs/guides/matrix_building.md`.

**Found while writing the real configs**: `lesion_glob` in every doc/config up to this point (`docs/guides/analysis.md`, this file's earlier drafts, inherited from `notebooks/lesion_analysis.ipynb`/the handoff note) was `"*/lesion/mni/*_label-lesion_mask.nii.gz"` - checked against real retrieved data in `data/clinical_connectome/` and found wrong: the actual local layout (from `src/retrieval/output_layout.py`, post-BIDS-refactor) is `<subject>/lesion/manual_masks/anat/<subject>_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`. The notebook was written against an older/different local layout and nobody had re-verified its glob since. Fixed to `"*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz"` in `docs/guides/analysis.md` and the real `config/pipelines/build_lesion_matrix.json` - confirmed against all 4 datasets (`find` count of subject dirs vs. matching lesion files: WashU 202/202, PASPORT 83/83, PSP 168/168, UKLFR 697/697, all equal). `docs/notes/analysis_pipeline_v2_handoff.md` still has the old, wrong glob - left as-is, since that file is an intentionally-frozen historical plan snapshot, not maintained documentation.

## `src/features/lesion.py` — lesion feature matrix

`build_lesion_matrix(data_root, datasets, reference_template_path, lesion_glob, binarize_threshold, resample_interpolation, parcellate, group_filter, atlas_path=None, parcel_aggregation=None) -> (X, metadata, non_constant_mask, parcel_ids, excluded_by_group)`

**`group_filter`** restricts subject discovery to specific naming-derived groups (`src.retrieval.dataset.group_of` - ST/HC/PD/GM), via the shared `src/features/subject_discovery.py::discover_files_by_subject` also used by `src/features/functional.py` (`docs/dev/fc_matrix.md`). `None` means no restriction. Subjects excluded this way are returned separately as `excluded_by_group`, never conflated with a genuine missing-file gap - see `debug_27_07_26.md` and `docs/guides/matrix_building.md`.

Migrated from `notebooks/lesion_analysis.ipynb` (voxel-wise path, cells 4-8): same algorithm, restructured into typed, independently testable functions. The notebook is left as-is as the exploratory reference — this module is the version pipeline code actually calls.

**`reference_template_path` is an explicit, caller-supplied file, not derived from `datasets`** — changed from the original "pick the first lesion file of `reference_dataset` (sorted)" behavior, on request: that implicit choice silently tied the common voxel grid to whatever resolution one arbitrary subject's file happened to have, with no guarantee it matched a canonical space (e.g. MNI152 2mm) rather than just *a* space with the same name. `load_reference_image(reference_template_path) -> nib.Nifti1Image` now does exactly one thing - load that file, raising `FileNotFoundError` with a clear message if it's missing - and is also the function `build_lesion_matrix.py`'s `_write_parcellated_volumes` calls directly for QC reconstruction, without re-running subject discovery. The old `reference_dataset` field/param and its "must be one of `datasets`" validation are gone entirely, not deprecated-in-place.

Two output shapes for `X`, chosen by `parcellate`:

- **`parcellate=False`** (voxel-wise, the notebook's original behaviour): each subject is a flattened binarized lesion volume, resampled onto `reference_template_path`'s grid when its native resolution differs. `parcel_ids` is `None` — voxel-wise has no parcel identity to report.
- **`parcellate=True`**: each subject is the **proportion of damage per atlas region** — the same characterisation Thiebaut de Schotten et al. 2020 (`knowledge/Thiebaut de Schotten et al - 2020 - Brain disconnections link structural connectivity with function and behaviour/`) use ahead of their varimax-rotated PCA (MMP + 12 manually-defined subcortical regions, 372 ROIs total). `atlas_path` is caller-supplied — any volumetric, discrete-label NIfTI atlas works, not just MMP; swapping atlases is a config change (`atlas_path` + a distinct `session_name`), no code change.

Both paths end with `_drop_constant_features`: columns (voxels or parcels) that are identical across every subject carry no information for downstream PCA/UMAP/clustering and are dropped. `non_constant_mask` records which columns survived (against the pre-drop feature count) so the mask can be reapplied to related data (e.g. re-running with a different subject selection) — `parcel_ids` is filtered to the same surviving columns, so it always lines up 1:1 with `X`'s columns when `parcellate=True`.

### Parcel aggregation is a registry, not hardcoded

```python
PARCEL_AGGREGATIONS: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "fraction_lesioned": lambda voxel_block: voxel_block.mean(axis=1),
}
```

Each entry reduces a `(n_subjects, n_voxels_in_parcel)` block to `(n_subjects,)`. Only `"fraction_lesioned"` exists today because binary lesion masks only support one meaningful reduction (proportion of damage) — kept as an explicit registry (same "registry over hardcoded dispatch" precedent as `config/registry/file_patterns.json` and `REDUCTION_METHODS`/`CLUSTERING_METHODS`, `docs/dev/models.md`) because SDC/FC data is continuous and will need other reductions (e.g. mean/sum of connectivity weights) on the same parcellation machinery — not a speculative abstraction for lesion masks alone.

### Atlas resampling always uses nearest-neighbor interpolation

`load_and_resample_atlas(atlas_path, reference_img)` forces `interpolation="nearest"` regardless of the lesion masks' own `resample_interpolation` config value. A label atlas holds discrete parcel ids, not continuous intensities — any other interpolation would invent label values that match no real parcel. This is the one place in the module where an interpolation choice is *not* a config value, deliberately: it isn't a real degree of freedom, unlike the lesion masks' own interpolation.

### `reconstruct_parcel_volume` — QC only, not part of the matrix-building path

`reconstruct_parcel_volume(parcel_values, atlas_labels, parcel_ids) -> np.ndarray` paints one subject's per-parcel value vector back onto the atlas voxel grid, for visual inspection (e.g. in `fsleyes`) of what a parcellated feature actually looks like spatially. It is pure numpy — no file I/O — and is not called by `build_lesion_matrix`. It backs the `save_parcellated_volumes` config flag on `build_lesion_matrix.py` (`_write_parcellated_volumes`, see that section below): when set, the pipeline script calls `load_and_resample_atlas` again (cheap — the atlas is small) and writes one `.nii.gz` per subject via `nibabel`, using the reference image's affine.

### Validation

`parcellate=True` requires both `atlas_path` and `parcel_aggregation`; `parcellate=False` forbids both — validated in `build_lesion_matrix` itself (`_validate_parcellation_args`), not left to config-layer callers, since the function can be invoked directly (tests, notebooks) as well as through `src/pipeline/build_lesion_matrix.py`.

## `src/analysis/build_config.py` — `build_lesion_matrix.json` parsing

`load_build_matrix_config(path) -> BuildMatrixConfig`, same shape and style as `src/retrieval/config.py`'s `load_config`: hand-written `_require_*`/`_optional_*` helpers (own copy, not shared with `src/retrieval/config.py` — each is a handful of lines, premature to abstract per the handoff note's explicit deferral), every field validated upfront so a malformed config is rejected before any file is touched.

Two upfront value-domain checks, beyond type checking, both deliberate (config validation is a system boundary — `code_standards.md` §0):

- **`binarize_threshold`** must be in `[0.0, 1.0]`. Lesion mask values after resampling are nominally binary/interpolated-to-[0,1]; a threshold outside that range produces a *silently degenerate* result (every voxel above or below threshold for every subject) that only surfaces much later, as an empty/collapsed feature matrix after `_drop_constant_features` — far from where the bad config value was set.
- **`resample_interpolation`** must be one of `{"linear", "nearest", "continuous"}` — the exact set `nilearn.image.resample_to_img` accepts. Without this check, a typo here (e.g. `"neareast"`) only surfaces when `resample_to_img` is actually called on a subject whose native resolution differs from the reference grid — potentially after a long run has already processed hundreds of subjects with matching resolution.

`parcellate`/`atlas_path`/`parcel_aggregation`/`save_parcellated_volumes` are cross-validated the same way as `build_lesion_matrix` itself (`_validate_parcellation_fields` mirrors `_validate_parcellation_args`) — kept as two separate checks (config layer + function layer) deliberately, since `build_lesion_matrix` can be called directly without going through this config loader (see "Validation" above). `parcel_aggregation`, when given, is checked against `src.features.lesion.PARCEL_AGGREGATIONS` directly (`analysis` importing from `features` is a downward, architecture-compliant dependency).

`load_build_matrix_config` also parses `MaskFcConfig`/`BuildFcMatrixConfig` for the FC pipeline (`docs/dev/fc_matrix.md`) - same module, same style, different config shape.

## `src/pipeline/build_lesion_matrix.py` — CLI entry point

`python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json`. Same shape as `retrieve_data.py` (`main(argv) -> int`, staged `try`/`except` per phase, `summaries/build_lesion_matrix/<project>/` + `logs/build_lesion_matrix/<project>/` written every run) but simpler control flow: `build_lesion_matrix()` either succeeds for every requested subject or raises - there's no per-subject error accumulation to report, unlike `retrieve_data.py`'s copy phase.

Phases, each with its own `try`/`except` (`lessons_learned.md` #9 - a later-added phase isn't automatically covered by an earlier phase's error boundary): load config → attach log file handler (`src/utils/logging_setup.py`, `docs/dev/config.md`) → `build_lesion_matrix()` → `artifacts.save_matrix()` (output dir = `output_root/<dd-mm>_<session_name>`) → optional QC-volume writing (only if `parcellate and save_parcellated_volumes`) → write report.

**QC-volume writing is intentionally not atomic**, unlike `save_matrix`: `_write_parcellated_volumes` reloads the reference image (`features.lesion.load_reference_image`, added alongside this script since `build_lesion_matrix()` itself doesn't return it) and the resampled atlas (`load_and_resample_atlas`, called a second time - cheap, the atlas is small), then writes one `.nii.gz` per subject directly into `output_dir/parcellated_volumes/`. A failure partway through leaves some but not all subjects' volumes on disk; this is accepted because the run's actual output (the matrix artifact) is already saved successfully by that point - a `return 1` still signals the incomplete QC step to the caller/SLURM job without discarding the real output.

**Found while testing this script**: `artifacts.save_matrix`'s original `extra_arrays` validation (added in `src/utils/artifacts.py` during that step) wrongly assumed every extra array is subject-row-aligned with `X`. `non_constant_mask` is feature-aligned (length = pre-drop feature count), not subject-aligned - the check was removed; `save_matrix` now makes no assumption about `extra_arrays`' shape relationship to `X`, since that meaning is caller-specific (documented in `artifacts.py`).
