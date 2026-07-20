# Analysis pipeline (embedding/clustering) — technical reference

Audience: developers/agents working on `src/features/`, `src/analysis/`, and the `src/pipeline/build_lesion_matrix.py` / `dim_reduction.py` / `dim_reduction_clustering.py` / `clustering.py` entry points.

Design rationale and full planned layout: `docs/notes/analysis_pipeline_v2_handoff.md`. This file documents what is actually implemented today, updated as each piece lands — not a restatement of the plan.

**Status**: `src/utils/artifacts.py`/`logging_setup.py`, `src/features/lesion.py`, all of `src/analysis/` (`build_config.py`, `reduction.py`, `clustering.py`, `params.py`, `model_config.py`, `plotting.py`), all 4 `src/pipeline/` CLI entry points (with matching `jobs/`), and the real `config/*.json` files implemented. Manually end-to-end tested on synthetic data (chained: build → reduce → reduce+cluster → cluster); the real configs' field *values* were validated against real retrieved data (subject-count parity, see below) but a full real run hasn't been executed yet (would run via `sbatch`, not interactively). Only the unit/integration test suite remains — see the handoff note's to-do list.

**Found while writing the real configs**: `lesion_glob` in every doc/config up to this point (`docs/guides/analysis.md`, this file's earlier drafts, inherited from `notebooks/lesion_analysis.ipynb`/the handoff note) was `"*/lesion/mni/*_label-lesion_mask.nii.gz"` - checked against real retrieved data in `data/clinical_connectome/` and found wrong: the actual local layout (from `src/retrieval/output_layout.py`, post-BIDS-refactor) is `<subject>/lesion/manual_masks/anat/<subject>_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`. The notebook was written against an older/different local layout and nobody had re-verified its glob since. Fixed to `"*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz"` in `docs/guides/analysis.md` and the real `config/pipelines/build_lesion_matrix.json` - confirmed against all 4 datasets (`find` count of subject dirs vs. matching lesion files: WashU 202/202, PASPORT 83/83, PSP 168/168, UKLFR 697/697, all equal). `docs/notes/analysis_pipeline_v2_handoff.md` still has the old, wrong glob - left as-is, since that file is an intentionally-frozen historical plan snapshot, not maintained documentation.

**Note on build order**: `model_config.py` was deliberately built *after* `reduction.py`/`clustering.py` (reversing the handoff's original listing order) - it validates `reduction_method`/`clustering_method` against `REDUCTION_METHODS`/`CLUSTERING_METHODS` upfront (same "fail fast at the config boundary" principle as `build_config.py`), which requires those registries to exist first.

## `src/analysis/reduction.py` / `clustering.py` — modeling strategies

Plain `dict[str, Callable]` registries (`REDUCTION_METHODS`, `CLUSTERING_METHODS`), not classes/ABCs — same "explicit registry over hardcoded dispatch" precedent as `config/registry/file_patterns.json`. Each entry is a pure `(X, params) -> array` function: `params` is unpacked with `**params` straight into the underlying `sklearn`/`umap` estimator's constructor, no in-code defaults for any hyperparameter (`code_standards.md` §5) — those live only in `config/registry/params_reduction.json`/`params_clustering.json` (`src/analysis/params.py`). Invalid/unexpected keys in `params` surface as whatever error `sklearn`/`umap` itself raises for a bad constructor argument — not re-validated here, since re-implementing each estimator's accepted-parameter surface would just duplicate their own API.

- `reduction.py`: `umap_embed`, `tsne_embed`, `pca_embed`.
- `clustering.py`: `kmeans_cluster`.

## `src/analysis/params.py` — per-method hyperparameters

`load_method_params(params_file, method) -> dict` reads `config/registry/params_reduction.json`/`params_clustering.json`'s `{method: {"params": {...}}}` shape and returns the raw `params` dict for one method. Validates the file exists, its top-level shape is a JSON object (`lessons_learned.md` #7), `method` has an entry, and that entry's `"params"` value is itself a JSON object — raises `ValueError` naming what's wrong and, for an unknown method, the list of methods actually registered in the file. Does **not** validate individual hyperparameter keys/values — that's `sklearn`/`umap`'s own job when `reduction.py`/`clustering.py` unpacks the returned dict into an estimator constructor.

## `src/analysis/model_config.py` — modeling config parsing

3 loaders, one per modeling pipeline script: `load_dim_reduction_config`, `load_clustering_config`, `load_dim_reduction_clustering_config` → `DimReductionConfig`/`ClusteringConfig`/`DimReductionClusteringConfig` (all `frozen=True`). 5 fields are identical across all three (`project`, `input_path`, `output_root`, `run_name`, `overwrite`) and are parsed once by a shared `_load_shared_fields` helper — the method-specific fields (`reduction_method`/`clustering_method`, and their `params_file`(s)) are parsed per-loader.

`reduction_method`/`clustering_method` are validated against `REDUCTION_METHODS`/`CLUSTERING_METHODS` (imported from `reduction.py`/`clustering.py`) at config-load time via `_validate_method` — same fail-fast-at-the-config-boundary principle as `build_config.py`'s `resample_interpolation` check, and the reason this module was built *after* `reduction.py`/`clustering.py` rather than in the handoff's original listing order.

## `src/pipeline/build_lesion_matrix.py` — CLI entry point

`python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json`. Same shape as `retrieve_data.py` (`main(argv) -> int`, staged `try`/`except` per phase, `reports/build_lesion_matrix/<project>/` + `logs/build_lesion_matrix/<project>/` written every run) but simpler control flow: `build_lesion_matrix()` either succeeds for every requested subject or raises - there's no per-subject error accumulation to report, unlike `retrieve_data.py`'s copy phase.

Phases, each with its own `try`/`except` (`lessons_learned.md` #9 - a later-added phase isn't automatically covered by an earlier phase's error boundary): load config → attach log file handler → `build_lesion_matrix()` → `artifacts.save_matrix()` (output dir = `output_root/<dd-mm>_<run_name>`) → optional QC-volume writing (only if `parcellate and save_parcellated_volumes`) → write report.

**QC-volume writing is intentionally not atomic**, unlike `save_matrix`: `_write_parcellated_volumes` reloads the reference image (`features.lesion.load_reference_image`, added alongside this script since `build_lesion_matrix()` itself doesn't return it) and the resampled atlas (`load_and_resample_atlas`, called a second time - cheap, the atlas is small), then writes one `.nii.gz` per subject directly into `output_dir/parcellated_volumes/`. A failure partway through leaves some but not all subjects' volumes on disk; this is accepted because the run's actual output (the matrix artifact) is already saved successfully by that point - a `return 1` still signals the incomplete QC step to the caller/SLURM job without discarding the real output.

**Found while testing this script**: `artifacts.save_matrix`'s original `extra_arrays` validation (added in `src/utils/artifacts.py` during that step) wrongly assumed every extra array is subject-row-aligned with `X`. `non_constant_mask` is feature-aligned (length = pre-drop feature count), not subject-aligned - the check was removed; `save_matrix` now makes no assumption about `extra_arrays`' shape relationship to `X`, since that meaning is caller-specific (documented in `artifacts.py`).

## `src/utils/logging_setup.py` — shared log-file-handler helper

`attach_file_handler(log_path)` - the same "console + file, remove any stale FileHandler from a previous `main()` call in-process" logic every pipeline script needs. Extracted once `build_lesion_matrix.py` plus the 3 modeling scripts below would otherwise have carried 4 near-identical copies (past the "revisit at the 4th consumer" threshold already applied to `_require_*`). **Deliberately not** used by `retrieve_data.py`, which keeps its own pre-existing copy - that script is stable/in production and wasn't touched.

## `src/analysis/plotting.py` — minimal cluster visualization

`plot_clusters_2d(X_2d, cluster_labels, output_path, xlabel, ylabel, title)`: one function, a 2D scatter of `X_2d`'s first two columns colored by `cluster_labels`, saved to `output_path`. Added on request specifically for the two clustering pipeline scripts below, ahead of the handoff note's original "plotting explicitly deferred" scope - a first visual sanity check of cluster separation, nothing richer (per-dataset coloring, >2D, interactivity) yet. Raises `ValueError` if `X_2d` has fewer than 2 columns rather than producing a degenerate/empty plot.

## `src/pipeline/dim_reduction.py` / `dim_reduction_clustering.py` / `clustering.py` — the 3 modeling CLIs

Same shape as `build_lesion_matrix.py` (`main(argv) -> int`, staged `try`/`except`, `reports/<script>/<project>/` + `logs/<script>/<project>/`), reading an existing matrix artifact via `artifacts.load_matrix(input_path)` rather than building one. Output dir layout adds a method-name segment: `<output_root>/<method>/<dd-mm>_<run_name>/` (`dim_reduction.py`, `clustering.py`), `<output_root>/<reduction_method>-<clustering_method>/<dd-mm>_<run_name>/` (`dim_reduction_clustering.py`).

**Where cluster labels live, and what `matrix.npy` means when there's no reduction** (decided during implementation, not fully specified in the handoff note): both clustering-involving scripts append `cluster_label` as a new column on the loaded `metadata.csv` - never a separate `cluster_labels.npy` file - so every artifact this pipeline produces stays loadable through the same `load_matrix(input_dir) -> (X, metadata, extra_arrays)` contract, no special case for "this one has labels in a different place." Consistently, `matrix.npy` always holds *the feature space clustering actually ran on*: the embedding for `dim_reduction_clustering.py`, the unchanged input `X` for `clustering.py` (which re-saves it into the new artifact dir - accepted storage duplication in exchange for one uniform contract instead of a one-off shape for the no-reduction case).

`dim_reduction_clustering.py` clusters the **embedding**, not the raw input matrix (`CLUSTERING_METHODS[method](embedding, params)`) - matches the handoff's stated flow ("reduction dispatch → clustering dispatch on the embedding").

Both clustering scripts write `cluster_plot.png` via `plotting.plot_clusters_2d` after a successful `save_matrix` - `dim_reduction_clustering.py` plots the embedding's first 2 components, `clustering.py` plots the raw matrix's first 2 features (explicitly labeled "raw" in the axis titles, since with no reduction those 2 axes are an arbitrary, not-necessarily-meaningful projection). If fewer than 2 columns are available (e.g. a 1-component reduction), the plot step is skipped with a `logging.warning` rather than failing the run - the matrix/labels are still the real output, the plot is a convenience.

`DimReductionClusteringConfig` uses two explicitly named fields, `reduction_params_file` and `clustering_params_file`, rather than the two-element positional list (`"params_file": [...]`) shown in the original handoff note — decided during implementation: a positional list makes the mapping from list index to method implicit, the same category of fragility as `lessons_learned.md` #1 (though in practice `params.py`'s own per-method validation would catch a swapped pair too, since a reduction-method key wouldn't be found in a clustering params file). Named fields cost nothing extra and remove the ambiguity outright.

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

Each entry reduces a `(n_subjects, n_voxels_in_parcel)` block to `(n_subjects,)`. Only `"fraction_lesioned"` exists today because binary lesion masks only support one meaningful reduction (proportion of damage) — kept as an explicit registry (same "registry over hardcoded dispatch" precedent as `config/registry/file_patterns.json` and `REDUCTION_METHODS`/`CLUSTERING_METHODS`, planned) because SDC/FC data is continuous and will need other reductions (e.g. mean/sum of connectivity weights) on the same parcellation machinery — not a speculative abstraction for lesion masks alone.

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
