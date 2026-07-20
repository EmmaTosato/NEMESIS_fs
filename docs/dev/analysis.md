# Analysis pipeline (embedding/clustering) — technical reference

Audience: developers/agents working on `src/features/`, `src/analysis/`, and the `src/pipeline/build_lesion_matrix.py` / `dim_reduction.py` / `dim_reduction_clustering.py` / `clustering.py` entry points.

Design rationale and full planned layout: `docs/notes/analysis_pipeline_v2_handoff.md`. This file documents what is actually implemented today, updated as each piece lands — not a restatement of the plan.

**Status**: `src/features/lesion.py` implemented. Everything else in the planned layout (`src/utils/artifacts.py` is done too; `src/analysis/*`, the 4 CLI entry points, `config/*.json`) is not yet written — see the handoff note's to-do list for the remaining scope.

## `src/features/lesion.py` — lesion feature matrix

`build_lesion_matrix(data_root, datasets, reference_dataset, lesion_glob, binarize_threshold, resample_interpolation, parcellate, atlas_path=None, parcel_aggregation=None) -> (X, metadata, non_constant_mask, parcel_ids)`

Migrated from `notebooks/lesion_analysis.ipynb` (voxel-wise path, cells 4-8): same algorithm, restructured into typed, independently testable functions. The notebook is left as-is as the exploratory reference — this module is the version pipeline code actually calls.

Two output shapes for `X`, chosen by `parcellate`:

- **`parcellate=False`** (voxel-wise, the notebook's original behaviour): each subject is a flattened binarized lesion volume, resampled onto `reference_dataset`'s first lesion file (sorted) when its native resolution differs. `parcel_ids` is `None` — voxel-wise has no parcel identity to report.
- **`parcellate=True`**: each subject is the **proportion of damage per atlas region** — the same characterisation Thiebaut de Schotten et al. 2020 (`assets/papers/Thiebaut de Schotten et al - 2020 - Brain disconnections link structural connectivity with function and behaviour/`) use ahead of their varimax-rotated PCA (MMP + 12 manually-defined subcortical regions, 372 ROIs total). `atlas_path` is caller-supplied — any volumetric, discrete-label NIfTI atlas works, not just MMP; swapping atlases is a config change (`atlas_path` + a distinct `run_name`), no code change.

Both paths end with `_drop_constant_features`: columns (voxels or parcels) that are identical across every subject carry no information for downstream PCA/UMAP/clustering and are dropped. `non_constant_mask` records which columns survived (against the pre-drop feature count) so the mask can be reapplied to related data (e.g. re-running with a different subject selection) — `parcel_ids` is filtered to the same surviving columns, so it always lines up 1:1 with `X`'s columns when `parcellate=True`.

### Parcel aggregation is a registry, not hardcoded

```python
PARCEL_AGGREGATIONS: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "fraction_lesioned": lambda voxel_block: voxel_block.mean(axis=1),
}
```

Each entry reduces a `(n_subjects, n_voxels_in_parcel)` block to `(n_subjects,)`. Only `"fraction_lesioned"` exists today because binary lesion masks only support one meaningful reduction (proportion of damage) — kept as an explicit registry (same "registry over hardcoded dispatch" precedent as `config/file_patterns.json` and `REDUCTION_METHODS`/`CLUSTERING_METHODS`, planned) because SDC/FC data is continuous and will need other reductions (e.g. mean/sum of connectivity weights) on the same parcellation machinery — not a speculative abstraction for lesion masks alone.

### Atlas resampling always uses nearest-neighbor interpolation

`load_and_resample_atlas(atlas_path, reference_img)` forces `interpolation="nearest"` regardless of the lesion masks' own `resample_interpolation` config value. A label atlas holds discrete parcel ids, not continuous intensities — any other interpolation would invent label values that match no real parcel. This is the one place in the module where an interpolation choice is *not* a config value, deliberately: it isn't a real degree of freedom, unlike the lesion masks' own interpolation.

### `reconstruct_parcel_volume` — QC only, not part of the matrix-building path

`reconstruct_parcel_volume(parcel_values, atlas_labels, parcel_ids) -> np.ndarray` paints one subject's per-parcel value vector back onto the atlas voxel grid, for visual inspection (e.g. in `fsleyes`) of what a parcellated feature actually looks like spatially. It is pure numpy — no file I/O — and is not called by `build_lesion_matrix`. It exists for the planned `save_parcellated_volumes` config flag on `build_lesion_matrix.py` (not yet implemented): when set, the pipeline script calls `load_and_resample_atlas` again (cheap — the atlas is small) and writes one `.nii.gz` per subject via `nibabel`, using the reference image's affine.

### Validation

`parcellate=True` requires both `atlas_path` and `parcel_aggregation`; `parcellate=False` forbids both — validated in `build_lesion_matrix` itself (`_validate_parcellation_args`), not left to config-layer callers, since the function can be invoked directly (tests, notebooks) as well as through `src/pipeline/build_lesion_matrix.py`.
