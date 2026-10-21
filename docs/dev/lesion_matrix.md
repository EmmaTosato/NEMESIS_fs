# Lesion feature matrix — technical reference

Audience: developers/agents working on `src/features/lesion.py`, `src/analysis/build_config.py` (the `build_lesion_matrix.json`-parsing half), and `src/pipeline/build_lesion_matrix.py`.

This file covers turning lesion masks into a feature matrix ready for dimensionality reduction. For the models that consume that matrix, see `docs/dev/models.md`. For the equivalent FC pipeline, see `docs/dev/fc_matrix.md`. For "how do I run this", see `docs/guides/matrix_building.md`. For **which** interpolation to resample masks with and why, and for the 0.5 binarization (and which cohorts are actually resampled), see `knowledge/notes/neuroimaging/lesion_resampling.md`. For the MNI152NLin6Asym template, the 1mm vs 2mm grids and the theory behind dropping constant columns, see `knowledge/notes/neuroimaging/template_and_grids.md`.

**`lesion_glob`**: the real layout of `data/clinical_connectome/` is `<subject>/lesion/manual_masks/anat/<subject>_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`, so `config/pipelines/build_lesion_matrix.json` uses `"*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz"` (not the `"*/lesion/mni/*_label-lesion_mask.nii.gz"` of `notebooks/pipeline_building/lesion_matrix_build.ipynb`). The number of subject directories equals the number of matching lesion files in each of the 4 datasets in scope at the time (WashU 202/202, PASPORT 83/83, PSP 168/168, UKLFR 697/697).

**No parcellation**: voxel-wise is the only output shape `build_lesion_matrix()` produces. An atlas-parcellated shape (each subject's feature vector as the proportion of damage per atlas region, the characterisation Thiebaut de Schotten et al. 2020 use ahead of their varimax-rotated PCA, built from a combined atlas) is not supported: the parcellation-then-varimax-PCA replication is not pursued through this pipeline (project decision).

## `src/features/lesion.py` — lesion feature matrix

`build_lesion_matrix(data_root, datasets, reference_template_path, lesion_glob, binarize_threshold, resample_interpolation, group_filter, excluded_subjects, correct_out_of_brain, brain_mask_path) -> (X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, corrected_subjects)`

**Row order**: by dataset name, then `subject_id`, whatever the order of `datasets` in the config - the same criterion as the SDC builders (`docs/dev/sdc_matrix.md`), so a lesion matrix and an SDC matrix of the same cohort have the same row order and can be compared by position. Comparisons across runs still align by `subject_id` (`src/analysis/cluster_comparison.py::align_runs`), never by position.

**`metadata.csv` is row-aligned with `matrix.npy`**: row *i* of the metadata describes row *i* of `X`, always. It is the invariant every consumer relies on to attach anything per-subject (labels, covariates, colours) to the matrix by position. `artifacts.save_matrix` checks that the two have the same number of rows and raises otherwise; the order itself is guaranteed by construction (both are built in the same loop in `_stack_voxel_matrix`), so anything that reorders or filters one must do the same to the other.

**`group_filter`** restricts subject discovery to specific naming-derived groups (`src.utils.subject_ids.group_of` - ST/HC/PD/GM), via the shared `src/features/subject_discovery.py::discover_files_by_subject` also used by `src/features/functional.py` (`docs/dev/fc_matrix.md`). `None` means no restriction. Subjects excluded this way are returned separately as `excluded_by_group`, never conflated with a genuine missing-file gap - see `debug_27_07_26.md` and `docs/guides/matrix_building.md`.

### Subject admission: one curated list, no thresholds

`excluded_subjects` is the resolved id set of `assets/metadata/excluded_subjects.csv`, loaded by the **pipeline** (`src/utils/participants.py::load_excluded_subjects(path, scope)`, asked for scope `"lesion"` - it returns the `all` rows plus this matrix's own, see `docs/guides/metadata.md`) and passed in as data - the library gets a set, not a path, so one read serves the whole run and the file's own validation happens in exactly one place.

- Applied by `_drop_excluded_subjects` in `_voxelwise_matrix_with_volume`, **after** `_discover_lesion_files` and `group_filter` but **before** `_stack_voxel_matrix`: an excluded subject's mask is never read. The order matters in the other direction too - `_discover_lesion_files`' own mask-count consistency check must still see the complete set, because a subject deliberately kept out of a matrix is not a subject whose mask is missing from disk.
- Returned as `excluded_by_list`, restricted to the subjects this run actually discovered - never the whole file, most of which belongs to datasets a given run doesn't touch. Reporting the whole list would misstate what the matrix contains. `src/pipeline/build_lesion_matrix.py::_excluded_rows` joins those ids back to the file's `reason`/`value` for `config.md`; the library itself has no concept of *why* a subject is on the list.
- Never conflated with `excluded_by_group`, and the two can't double-count: the list is applied to the already-group-filtered set.
- If the list empties every discovered subject, `build_lesion_matrix` raises `ValueError` rather than writing an empty matrix (`_drop_constant_features`/`save_matrix` would accept one, and every downstream run would read a 0-subject artifact as legitimate).

**Why a hand-written list and not a threshold in the config**: the real distributions have no natural break (on 5853 subjects: 3 masks at 0 voxels on the 2mm grid, 132 at ≤ 10 voxels, a continuous tail; 234 subjects above 5% out-of-brain fraction, 73 above 10%), so any threshold picks an arbitrary point on that tail and applies it to every dataset at once. The decision is per-subject judgement, made from `assets/metadata/lesion_metadata.csv` in `notebooks/exploration/lesion_analysis.ipynb` - see `.claude/history/methods_changelog.md` for the alternatives rejected.

**Shared with the SDC matrix by design.** `src/features/parcellated_csv.py::subjects_with_lesion_mask` applies the same list (both representations go through it), so the two matrices drop exactly the same subjects. Without that, a lesion-vs-SDC comparison would silently compare two different cohorts. This is also why the file is one list rather than one per pipeline, and why the SDC side can honour it despite never loading a raw lesion mask (`docs/dev/sdc_matrix.md`, "Why participants.tsv, not manual_masks/ on disk"): the list is subject ids, not imaging.

### Resampling onto the common grid

Every lesion mask reaches its target grid through one function, `src/features/lesion.py::_binarize_on_grid`, shared by `build_lesion_matrix` and `compute_lesion_metadata` so a volume is computed the same way in both.

1. **Target grid**: fixed by an explicit `reference_template_path` (2mm template for the production matrix; `compute_lesion_metadata` declares one template per grid, 1mm and 2mm).
2. **Is a resample needed?** `_needs_resample` is true if the mask's shape differs from the reference **or** its affine is not `np.allclose` to the reference's (`atol=1e-3`). Shape alone is not enough: two images can share a shape while their affines place the same array at different physical coordinates. A mask already on the grid is not touched, so its count is the native one.
3. **Resample**: `nilearn.image.resample_to_img(img, reference, interpolation=resample_interpolation, force_resample=True, copy_header=True)`. `resample_interpolation` is `nearest` in both production configs, because a mask holds labels and any other interpolation produces values that are neither 0 nor 1.
4. **Re-binarize**: `img.get_fdata() > binarize_threshold` (`0.5` in production), then flattened in C order. This runs even when the source is already binary, since registration and interpolation can leave near-0/near-1 values.

### Binarization: where, when, how

- **One function**: `_binarize_on_grid(img, reference_img, resample_interpolation, binarize_threshold)`. Callers: `_load_and_binarize_lesion` (matrix rows, cast to `uint8`) and `_metrics_on_grid` (`compute_lesion_metadata`, once per grid). `load_brain_mask` has its own fixed `> 0.5` after a fixed `nearest` resample. The FC pipeline binarizes in `src/features/functional.py::resample_lesion_to_atlas`, same shape.
- **Mask shape**: `_binarize_on_grid` accepts a 3D mask or one with trailing singleton dimensions; a 4D mask with more than one volume raises `ValueError` naming the file.
- **Order**: always resample first (only if `_needs_resample`), then threshold. A mask already on the grid is thresholded too.
- **Strict inequality**: a voxel equal to exactly `binarize_threshold` is dropped. FSL's mask recipe keeps voxels overlapping "50% or more", i.e. `>= 0.5` (sources in the note). In the current data the two rules differ only for PSP's fractional masks on the 1mm grid, whose voxels at exactly `4/8` are dropped here; PSP's 1mm columns of `lesion_metadata.csv` are already flagged as unreliable (`docs/dev/metadata.md`).
- **When the threshold actually changes anything**: with `nearest` on a binary source it removes nothing. It is active for PSP on the 1mm grid (no resample, fractional values) and would become the majority threshold for `linear` on a grid pair whose voxel centres do not coincide.

**`nearest` downsampling is sampling, not averaging.** The centres of the 2mm template voxels fall exactly on centres of 1mm template voxels (origins `-90` and `-91` mm on x, equal on y and z), so `nearest` from 1mm to 2mm reads exactly one source voxel per target voxel - for a RAS `-91` mask, `mask[1::2, 0::2, 0::2]`. The 2mm volume is therefore not `native / 8` in general, and a very small lesion can lose all its voxels. This is why `lesion_metadata.csv` keeps both grids (see `docs/guides/metadata.md`). For the same reason `"linear"` gives **the same output as `"nearest"`** on this grid pair (a linear interpolant evaluated at a source voxel centre returns that voxel's value): checked with `resample_to_img` on all three mask headers (LAS `+90`, RAS `-90`, RAS `-91`). Switching `resample_interpolation` to `"linear"` would not change a single matrix; a true majority (partial-volume) downsampling would need an area-weighted average, which `resample_to_img` does not do and the repo does not implement. Measurements and literature: `knowledge/notes/neuroimaging/lesion_resampling.md` (Parts 2-3) and `template_and_grids.md` (§ 9-10).

**The brain mask is always `nearest`** (`load_brain_mask`, threshold `0.5`), whatever `resample_interpolation` the run uses: it is binary too.

**`compute_lesion_metadata` reads each mask once** and resamples it once per grid, not once per metric. Nothing in the repo resamples lesion masks for BCBToolKit: the SDC output is copied from EBRAIN, already computed on the 1mm grid (`docs/dev/sdc_matrix.md`).

### Template and grid

Both grids are TemplateFlow's MNI152NLin6Asym (`assets/templates/tpl-MNI152NLin6Asym_res-{1,2}_T1w.nii.gz`, RAS): `res-1` is 182x218x182 (7,221,032 voxels, origin `(-91, -126, -72)`), `res-2` is 91x109x91 (902,629 voxels, origin `(-90, -126, -72)`). It is the space the masks are named in and the one BCBToolKit/BCBlib work in, so no cross-template transform is ever applied. The production matrix uses `res-2` (project choice: the native detail of 5150/5853 masks is a 2mm lattice, and the full 1mm matrix would be ~42 GB). Template genealogy, the difference from MNI152NLin2009cAsym and the 1mm vs 2mm trade-off, with sources: `knowledge/notes/neuroimaging/template_and_grids.md`.

### `correct_out_of_brain` — fix the voxels, keep the subject

Zeroes every lesion voxel of every subject falling outside `brain_mask_path` (`src/features/lesion_correction.py::zero_out_of_brain_voxels`, applied in `_apply_out_of_brain_correction`, which also recomputes `lesion_volume_voxels` from the corrected data) and keeps the subject in the matrix. Disabled (`False`) by default - no correction is ever applied silently.

- **`brain_mask_path`** is its only use in this pipeline: **required** when the flag is set (config-load raises otherwise), ignored when it isn't. A checked-in MNI152 brain mask ships under `assets/templates/tpl-MNI152NLin6Asym_res-{1,2}_desc-brain_mask.nii.gz`, matching the two `_T1w` reference templates already used for `reference_template_path`; it must be on the same grid.
- `corrected_subjects` is `(subject_id, n_voxels_corrected)` pairs, not ids alone - a 1-voxel edge artifact and a large registration problem are different findings. A subject fully inside the brain mask isn't listed even when the flag is on (`n_voxels_corrected` would be 0).
- It is a **correction, not an admission criterion**: a subject too contaminated to keep at all belongs in `excluded_subjects.csv` with `reason=out_of_brain_fraction_too_high`. The two compose, and the fraction that decision is based on lives in `assets/metadata/lesion_metadata.csv`, measured on the raw mask (see `docs/dev/metadata.md`). Supersedes `scripts/lesion_fix.py` (see `.claude/history/project_changelog.md`).
- All exclusion/correction lists are persisted in full (never truncated) to `config.md`/the report (`src/pipeline/build_lesion_matrix.py::_summary_lines`).

**Immutable once built**: admission only takes effect for a run that hasn't happened yet - an already-built `data/derived/lesion_matrix/<session>/` is never filtered in place (would corrupt the reproducibility of every downstream analysis that already read it). Forgetting an exclusion before a run means deleting that run's output directory and its `runs.csv` row, then rebuilding - not patching the existing matrix/`metadata.csv`.

### `compute_lesion_metadata` — every mask-derived metric, in one streaming pass

`compute_lesion_metadata(data_root, datasets, lesion_glob, binarize_threshold, resample_interpolation, group_filter, grids, correct_out_of_brain, side_threshold) -> (metadata, excluded_by_group)`, the single computation behind `src/pipeline/compute_lesion_metadata.py` and `assets/metadata/lesion_metadata.csv`. Full reference in `docs/dev/metadata.md`; what matters here is how it relates to `build_lesion_matrix`:

- It applies **no** admission criterion: every discovered subject is measured, because its output is what the exclusion decision is made from.
- It deliberately does **not** reuse `_voxelwise_matrix_with_volume`. That function stacks every subject's flattened volume in memory - ~5.3 GB on the 2mm grid (902,629 voxels × 5853 subjects, uint8) and ~42 GB on the 1mm grid, which is not runnable anywhere. The streaming version keeps only scalars per subject, so its peak is independent of cohort size. Anyone tempted to "reuse the function that already exists" to add a fine grid hits exactly that wall.
- Both share `_binarize_on_grid` (resample-if-needed then re-binarize) and `_apply_out_of_brain_correction`'s underlying `zero_out_of_brain_voxels`, so a volume from either is computed the same way. They still differ by construction: a matrix run's `metadata.csv` column reflects *that run's* grid and correction settings, while the CSV's columns are one fixed set per grid for every subject. `src/analysis/cluster_description.py` reads the registry's copy for exactly this reason.

Migrated from `notebooks/pipeline_building/lesion_matrix_build.ipynb` (voxel-wise path): same algorithm, restructured into typed, independently testable functions. The notebook is left as-is as the exploratory reference — this module is the version pipeline code actually calls.

**`reference_template_path` is an explicit, caller-supplied file, not derived from `datasets`** — changed from the original "pick the first lesion file of `reference_dataset` (sorted)" behavior, on request: that implicit choice silently tied the common voxel grid to whatever resolution one arbitrary subject's file happened to have, with no guarantee it matched a canonical space (e.g. MNI152 2mm) rather than just *a* space with the same name. `load_reference_image(reference_template_path) -> nib.Nifti1Image` now does exactly one thing - load that file, raising `FileNotFoundError` with a clear message if it's missing.

Production's `reference_template_path` (`config/pipelines/build_lesion_matrix.json`, likewise `build_sdc_matrix.json` for the voxelwise SDC representation) points at a real, versioned MNI152NLin6Asym template under `assets/templates/` (`tpl-MNI152NLin6Asym_res-1_T1w.nii.gz`/`_res-2_T1w.nii.gz`, from TemplateFlow, verified shape/affine against project data), not a specific patient's lesion mask. `load_reference_image`/`resample_to_img` only ever read shape+affine, never pixel content, so a T1w structural image works identically to a binary mask as the grid reference - no code change needed, only the config path. Both resolutions are shipped; which one a pipeline uses is a plain config edit (`reference_template_path` pointing at the `_res-1_`/`_res-2_` file), not a code change.

A template under versioned `assets/templates/` cannot change grid by accident, unlike a patient's lesion mask under gitignored `data/` (replacing that file in a dataset refresh would silently change the grid, e.g. 2mm → 1mm). Already-built lesion matrices are unaffected (their voxel grid is fixed at build time); only new runs pick up whichever template the config names.

Each subject is a flattened binarized lesion volume, resampled onto `reference_template_path`'s grid when its native resolution differs. `_drop_constant_features` then drops columns (voxels) that are identical across every subject (`X.min(axis=0) != X.max(axis=0)` keeps a column; dropped are the never-lesioned voxels, all 0, and in principle the voxels lesioned in every subject, all 1 - none exist in a stroke cohort). Reasons: an all-0 column adds zero to every Euclidean distance, is ignored by Jaccard/Dice (which only count voxels lesioned in at least one of the two subjects), and centred it is a zero row/column of the covariance, so it carries no information for downstream PCA/UMAP/clustering; a constant column also makes standardization `(x - mean) / std` undefined (`src/analysis/covariance_pca.py` raises on one when `standardize=True`); and the full grid has 902,629 voxels at 2mm while `s1.4-vol` keeps 221,955, so dropping them shrinks memory and compute ~4x. An all-1 column would **not** be neutral for Jaccard/Dice/cosine (it adds to both intersection and union), which is why "neutral" holds in practice, not by construction. The only criterion is exact constancy: no minimum lesion frequency per voxel, unlike the 5%-or-N-patients rule of lesion-symptom mapping (project choice; theory and sources in `knowledge/notes/neuroimaging/template_and_grids.md`, Part 3). `non_constant_mask` records which columns survived (against the pre-drop feature count) so the mask can be reapplied to related data (e.g. re-running with a different subject selection).

**Rebuilding the full-grid matrix from the artifact.** `non_constant_mask.npy` is a boolean vector with one entry per voxel of the reference grid, in the C-order of the flattened 3D volume (the same order as `_binarize_on_grid`'s `ravel()`). The reduced `matrix.npy` has one column per `True` entry, in order, so:

```python
X_full = np.zeros((X.shape[0], non_constant_mask.size), dtype=np.uint8)
X_full[:, non_constant_mask] = X
```

restores the full grid. A per-voxel quantity computed on the reduced matrix (e.g. a frequency) goes back into a brain image the same way: write it into `np.zeros(non_constant_mask.size)` at the `True` positions, then `reshape` to the reference grid's shape.

`_discover_lesion_files(data_root, datasets, lesion_glob, group_filter)` derives the subject-folder glob from `lesion_glob` itself (the last bare `"*"` path segment) rather than assuming subject folders are `dataset_root`'s immediate children (true only under the older subject-first local layout) - works for either local layout without hardcoding one. Raises `ValueError` if, for a dataset, the number of (group-filtered) subject folders differs from the number of masks found (a folder without a mask, or a stray extra file), and if one subject matches more than one file or its filename and folder name disagree (`discover_files_by_subject`) - the contract is exactly one mask per subject. Raises `FileNotFoundError` if the subject-folder glob itself finds nothing (an unreachable dataset - wrong path/name in config, or never copied) before `group_filter` narrows the list, since `Path.glob` on a missing directory returns `[]` with no exception and a typo'd dataset name would otherwise silently contribute 0 subjects rather than fail loudly. `group_of()` validates every discovered subject-dir name unconditionally, not only when `group_filter` is set (`lessons_learned.md` #4/#28) - skipping that check for the common "this dataset doesn't mix groups" case let a malformed folder name through silently instead of raising.

`load_reference_image(reference_template_path)` requires an explicit, caller-supplied file rather than deriving one implicitly (e.g. "the first lesion file found") - production points it at the TemplateFlow MNI152NLin6Asym template under `assets/templates/` (see above).

### Checks on the built matrix

What the builder guarantees by construction, and what it checks:

- **Values in `{0, 1}`, no NaN**: structural. Every mask is thresholded to a boolean and stored as `uint8`, so no other value and no NaN can exist. The Jaccard/Dice distance paths re-check it downstream with `require_binary_matrix` (`docs/dev/models.md`).
- **Cohort-wide empty matrix**: `_voxelwise_matrix_with_volume` raises `ValueError` if *every* subject binarizes to zero voxels (a misconfigured `binarize_threshold`).
- **A single subject with zero lesion voxels** is not an error in the builder: it is a per-subject admission decision, taken from `lesion_metadata.csv` and recorded in `excluded_subjects.csv` with `reason=empty_mask`. A manual check on a built matrix is `X.sum(axis=1) == 0`.
- **After the column reduction**, no voxel has frequency 0 or frequency equal to the number of subjects (both are constant and have been dropped); a nonzero count of either means the reduction was not applied.

### Validation

`binarize_threshold`/`resample_interpolation` are cross-validated at the config layer (`src/analysis/build_config.py`) before `build_lesion_matrix()` is ever called - see below.

## `src/analysis/build_config.py` — `build_lesion_matrix.json` parsing

`load_build_matrix_config(path) -> BuildMatrixConfig`, hand-written `_require_*`/`_optional_*` helpers (each is a handful of lines, premature to abstract per the handoff note's explicit deferral), every field validated upfront so a malformed config is rejected before any file is touched.

Two upfront value-domain checks, beyond type checking, both deliberate (config validation is a system boundary — `code_standards.md` §0):

- **`binarize_threshold`** must be in `[0.0, 1.0]`. Lesion mask values after resampling are nominally binary/interpolated-to-[0,1]; a threshold outside that range produces a *silently degenerate* result (every voxel above or below threshold for every subject) that only surfaces much later, as an empty/collapsed feature matrix after `_drop_constant_features` — far from where the bad config value was set.
- **`resample_interpolation`** must be one of `{"linear", "nearest", "continuous"}` — the exact set `nilearn.image.resample_to_img` accepts. This is the validation rationale only — the *domain* rationale for picking `"nearest"` (discrete/binary data) over `"linear"`/`"continuous"` (continuous fields), and its interaction with `binarize_threshold` (a no-op under `"nearest"`), is in `knowledge/notes/neuroimaging/lesion_resampling.md`. Without this check, a typo here (e.g. `"neareast"`) only surfaces when `resample_to_img` is actually called on a subject whose native resolution differs from the reference grid — potentially after a long run has already processed hundreds of subjects with matching resolution.
- **`excluded_subjects_path`** is required (a non-empty string), not optional: there is no config-level way to say "admit everyone". That is expressed by the file itself holding only its header, so the two states ("I decided nobody is excluded" and "the list was never written") stay distinguishable - `load_excluded_subjects` raises on a missing file. The same field exists on `SdcMatrixConfig`, pointing at the same file.
- **`correct_out_of_brain`** (optional, `False` when absent) must be a boolean. **`brain_mask_path`** is required (a non-empty string) only when it is set, and is otherwise unused - the same conditional-field convention as `SdcMatrixConfig`'s representation-specific fields.

`load_build_matrix_config` also parses `MaskFcConfig`/`BuildFcMatrixConfig` for the FC pipeline (`docs/dev/fc_matrix.md`), and `load_compute_lesion_metadata_config` parses `LesionMetadataConfig` for `compute_lesion_metadata.py` - same module, same helpers, different config shapes. That loader lives here rather than in the pipeline because it needs exactly the same mask-handling validators (`data_root`/`datasets`/`group_filter`/`lesion_glob`/`binarize_threshold`/`resample_interpolation`), and it delegates grid-name validation to `src/features/lesion.py::validate_lesion_grids` rather than re-checking it - one definition of what makes a grid name usable, next to the code that turns it into a column suffix.

## `src/pipeline/build_lesion_matrix.py` — CLI entry point

`python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json`. `main(argv) -> int`, staged `try`/`except` per phase, `logs/build_lesion_matrix/<project>/` written every run) but simpler control flow: `build_lesion_matrix()` either succeeds for every requested subject or raises - there's no per-subject error accumulation to report.

Phases, each with its own `try`/`except` (`lessons_learned.md` #9 - a later-added phase isn't automatically covered by an earlier phase's error boundary): load config → attach log file handler (`src/utils/logging_setup.py`, `docs/dev/config.md`) → `build_lesion_matrix()` → `artifacts.save_matrix()` (output dir = `output_root/<dd-mm>_<session_name>`, `config.md` included) → append the run log.

**Found while testing this script**: `artifacts.save_matrix`'s original `extra_arrays` validation (added in `src/utils/artifacts.py` during that step) wrongly assumed every extra array is subject-row-aligned with `X`. `non_constant_mask` is feature-aligned (length = pre-drop feature count), not subject-aligned - the check was removed; `save_matrix` now makes no assumption about `extra_arrays`' shape relationship to `X`, since that meaning is caller-specific (documented in `artifacts.py`).
