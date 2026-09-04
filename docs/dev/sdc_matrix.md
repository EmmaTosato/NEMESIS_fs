# SDC feature matrix — technical reference

Audience: developers/agents working on `src/features/sdc.py`, `src/analysis/build_config.py` (the `build_sdc_matrix.json`-parsing half), and `src/pipeline/build_sdc_matrix.py`.

This file covers turning retrieved SDC output (`sdc/<subject_id>/*`, produced upstream by `src/sdc/`/`compute_sdc.py`'s BCBToolKit Stage 1+2) into a feature matrix ready for dimensionality reduction, in either of two representations picked by `config.representation` (added 03/09): **parcellated** (`build_sdc_matrix`, the original one - one CSV per atlas, `LF-{object}_atlas-*.csv`) or **voxelwise** (`build_sdc_voxelwise_matrix` - the pre-parcellation `disconnectome-map` `.nii.gz` directly, same resampling-onto-a-common-grid approach as the lesion pipeline). For the equivalent lesion (voxel-wise) pipeline, see `docs/dev/lesion_matrix.md`. For "how do I run this", see `docs/guides/sdc_matrix_building.md`.

## Why this pipeline looks different from `build_lesion_matrix.py`

`build_lesion_matrix.py`'s voxel-wise matrix aligns subjects onto a common spatial grid via resampling - every subject's raw NIfTI has the same shape after `resample_to_img`, so columns line up by *position*. SDC's per-subject output is not a NIfTI grid but one CSV per (subject, atlas, object) pair, one row per anatomical region - and rows are **not in a stable order across subjects** (verified empirically: real CSVs are sorted by `mean_overlap` descending, not by region). Alignment here is done by `region_name` as a key (`pandas.reindex`), never by row position.

**BCBToolKit omits regions at zero overlap instead of writing them explicitly** - verified across the full local cohort (zero rows with `mean_overlap==0.0` written explicitly, out of >1000 subjects sampled during `notebooks/exploration/sdc_analysis.ipynb`). A missing row is therefore filled with `0.0` via `reindex`, not treated as a data gap.

## Reference labels (`assets/atlases/sdc_labels/<atlas>.csv`)

The set of columns (regions) `build_sdc_matrix()` produces for a given atlas is **fixed and authoritative**, read from `assets/atlases/sdc_labels/<atlas>.csv` (one `region_name` per row) - not re-derived per run as the union of whatever regions happen to appear in the current subject selection. This matters for two reasons:

1. **Completeness**: an atlas region never disconnected by any subject in a given run's selection would otherwise silently vanish from the matrix. The reference file was derived once from the *entire* local cohort (all 4 in-scope SDC datasets, ~1150 subjects) for each atlas currently supported, confirmed to reach that atlas's known/expected cardinality (e.g. `schaefer_200_tian_s2` = 200 Schaefer cortical + 32 Tian S2 subcortical = 232 regions, `schaefer_400_tian_s2` = 432 - both confirmed to reach exactly that count across the full cohort, no region ever missing).
2. **Validation**: every `region_name` found in a subject's CSV must exist in the reference set - a region name the reference doesn't know about raises `ValueError` immediately (an atlas mismatch, a corrupt file, or a naming change upstream), never silently added as an extra column or ignored.

Cardinalities for atlases not yet backed by a reference file are **not** derived from an empirical proxy (an earlier draft of this design used "max rows observed in a single subject" - dropped once the reference-file approach was adopted, since it can only ever be a lower bound, not the true cardinality). Adding support for a new atlas means adding its reference file first (see "Adding a new atlas" below).

**A known atlas anomaly, not currently supported**: `buckner_7n`'s CSV holds exactly one row per subject, with `region_name` set to the atlas's own filename (`atl-Buckner7_space-MNI_dseg`) rather than one row per cerebellar network - its CSV structure doesn't match the other 14 atlases and is excluded from this pipeline for now (2026-08-27, on request - not currently a target atlas). `yeh_hcp1065_streamline` (lesion-side only) is a different schema entirely (`tract,streamline_ratio`, no `region_name`) and is likewise out of scope.

### Adding a new atlas

1. Confirm the atlas isn't `buckner_7n` or `yeh_hcp1065_streamline` (see above).
2. Derive the reference region list from the full local cohort (same approach as `schaefer_200_tian_s2`/`schaefer_400_tian_s2`): union every `region_name` across every subject's CSV for that atlas, across all in-scope datasets, and confirm the union reaches the atlas's known/expected cardinality (published value, or a locally-verified fmriprep `dseg.tsv` for atlas combos that include one - see `assets/atlases/fmriprep/atlas-Yan<N>Tian<Sx>Buckner7N/*_dseg.tsv`, whose additive structure - e.g. 200 Schaefer + 16 Tian S1 + 7 Buckner = 223 - helped cross-check the individual-component cardinalities used here).
3. Write the confirmed list, one `region_name` per row (header included), to `assets/atlases/sdc_labels/<atlas>.csv`.

## `src/features/sdc.py`

`build_sdc_matrix(data_root, datasets, object_, atlas, value_column, reference_labels_path, group_filter) -> (X, metadata, region_names, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed)`

- **`object_`**: `"disconnectome"` or `"lesion"` - which of the two parcellated CSV families to read (`docs/guides/sdc_matrix_building.md` for the difference). Validated against `KNOWN_OBJECTS`.
- **`value_column`**: which per-region statistic to extract - `"fraction_covered"`, `"mean_overlap"`, `"weighted_mean_overlap"`, `"sum_overlap"`, `"p90_overlap"`, or `"p95_overlap"` (`KNOWN_VALUE_COLUMNS`; these 6 are the columns common to all 14 in-scope atlases - `buckner_7n`/`rojkova`/`yeh_hcp1065` additionally have `sum_atlas_in_tract`/`pwll_normalised`/`max_atlas_prob_in_overlap`/`continuous_dice`, not currently exposed here).
- **`X` never drops a constant column** - unlike `build_lesion_matrix.py`'s `_drop_constant_features`, column `j` always names the same region regardless of which subjects a given run admits (2026-08-27, project decision: keeps `X`'s shape - and therefore its meaning - stable across runs with different subject selections, at the cost of carrying always-zero columns for regions no admitted subject ever disconnects).

### Subject admission: two discovery passes, one intersection

A subject is admitted into `X` only if it has **both**:
1. A lesion mask **registered** in its dataset's `assets/metadata/<dataset>_participants_lesions.tsv` (column `lesion/manual_masks/anat/lesion_mask == "present"`, via `src.features.clinical.load_participants`/`participants_tsv_path`) - not a glob against `manual_masks/` on disk (see "Why participants.tsv, not `manual_masks/` on disk" below).
2. The requested `object_`/`atlas` SDC CSV (`sdc/*/*_LF-{object_}_atlas-{atlas}.csv`, discovered via `discover_files_by_subject` same as `build_lesion_matrix.py`).

`excluded_no_lesion_mask` tracks subjects with SDC output but no registered lesion mask (logged and persisted to `config.md`, never silently dropped or zero-filled); `sdc_not_yet_computed` tracks the opposite gap (a registered lesion mask but SDC not computed for that subject yet - not an error, just work not yet done upstream).

If the intersection is empty across every dataset, `build_sdc_matrix` raises `ValueError` rather than returning an empty matrix.

### Why `participants.tsv`, not `manual_masks/` on disk (found 27-08-26)

The first version of this pipeline resolved "has a lesion mask" by globbing `manual_masks/` directly (same glob `build_lesion_matrix.py` uses) - this is wrong whenever a local `data/` copy is a **partial retrieval sample**: on this Mac, `manual_masks/` held only 10 subjects per dataset while `sdc/` held the full retrieved cohort (195/83/168/705), so a local run only ever admitted the 40-subject intersection available on disk, and (confirmed by re-checking `assets/metadata/UKLFR_stroke_UKLFR_participants_lesions.tsv` directly) at least one subject flagged as "no lesion mask" this way (`sub-STUKLFR0671`) in fact **does** have one registered - the local `manual_masks/` gap was a retrieval sampling artifact, not a genuine missing-lesion case.

Fixed by resolving lesion-mask presence from each dataset's `assets/metadata/<dataset>_participants_lesions.tsv` instead - the authoritative registry of which subjects have a lesion mask at all, independent of what's currently retrieved on any one machine. Every row in these files already has `lesion/manual_masks/anat/lesion_mask == "present"` (subjects without a mask simply aren't rows at all, as of 27-08-26) - a genuine `excluded_no_lesion_mask` case is now a subject_id that doesn't appear as a row in the tsv at all (verified real example: `sub-STUKLFR0005`, confirmed absent from the registry, not just locally unretrieved). `_subjects_with_lesion_mask` raises `ValueError` if a dataset's tsv is missing the `lesion/manual_masks/anat/lesion_mask` column entirely - a structural registry gap this pipeline's core admission criterion depends on, never silently treated as "nobody has a lesion mask".

A full local retrieval run before this fix admitted 40/1151 subjects; after the fix, the same local run (SDC CSVs untouched, only the admission criterion changed) admits 1119/1151 - the remaining 32 exclusions are all genuine registry gaps (subject_id absent from `UKLFR_stroke_UKLFR_participants_lesions.tsv`), confirmed individually, not local-retrieval artifacts.

### Per-CSV validation (`_load_and_validate_csv`)

For every admitted subject's CSV:
- `region_name` column must be present.
- `value_column` must be present.
- No duplicate `region_name` values (raise `ValueError` listing them - a duplicate would otherwise make `.set_index("region_name")` produce a non-unique index, and the resulting `.reindex()` failure is a confusing pandas `ValueError` that doesn't name the offending file).
- Every `region_name` found must exist in the reference set (raise `ValueError` otherwise - see "Reference labels" above).

A header-only (zero-row) CSV is a legitimate domain case handled by `_stack_aligned_matrix`: the subject's vector is all-zero, same result as if every reference region had been individually omitted.

## `build_sdc_voxelwise_matrix` — the voxel-wise representation (added 03/09)

`build_sdc_voxelwise_matrix(data_root, datasets, object_, reference_template_path, resample_interpolation, group_filter) -> (X, metadata, non_constant_mask, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed)`

Reads the `disconnectome-map` `.nii.gz` directly (`sdc/*/*_res-1_desc-{object_}.nii.gz`) instead of the parcellated CSVs - the same pre-parcellation volume `build_sdc_matrix`'s CSVs are themselves derived from. Same two-pass admission criterion as `build_sdc_matrix` (a lesion mask registered in `assets/metadata/*_participants_lesions.tsv` **and** the requested SDC file present).

- **Deliberately restricted to `object_="disconnectome"`** - `object_="lesion"` raises `ValueError` immediately (both here and, redundantly, at config-load time - see below). The `lesion-map` `.nii.gz` (the resampled *input* lesion mask BCBToolKit used, not a retrieval of the real mask) would duplicate `build_lesion_matrix.py`'s own job from a less authoritative source; `manual_masks/` (via `assets/metadata/*_participants_lesions.tsv`) stays the one place a lesion mask is built from.
- **Never binarized** - disconnection values are a continuous [0, 1] probability, unlike `build_lesion_matrix.py`'s binary lesion mask. No `binarize_threshold` field exists for this representation.
- **Resampling**: reuses the same `nibabel`/`nilearn.image.resample_to_img` pattern as `src/features/lesion.py` (own local `_needs_resample`, same `_AFFINE_ATOL` tolerance - not imported cross-module, see the code comment on why), onto `reference_template_path`'s grid, with `resample_interpolation` chosen by the caller (typically `"linear"`/`"continuous"` for a continuous field, not `"nearest"` - unlike a binary mask, nothing here forces a discrete interpolation).
- **Constant-column drop**: unlike the parcellated representation (never drops a column - see above), voxels outside every admitted subject's brain are identically `0.0` and get dropped via the same `_drop_constant_features` as `build_lesion_matrix.py`, keeping `X`'s size manageable. `non_constant_mask` is persisted (`extra_arrays`) so the drop is always recoverable - this doesn't contradict the parcellated representation's "column always means the same thing" decision, since that reasoning was specifically about atlas *region identity* staying comparable across differently-scoped runs, not about voxel grids (whose meaning is already pinned by `reference_template_path`, independent of which subjects a given run admits).

## `src/analysis/build_config.py` — `build_sdc_matrix.json` parsing

`load_build_sdc_matrix_config(path) -> SdcMatrixConfig`, same style as `load_build_matrix_config`/`load_config`: hand-written `_require_*`/`_optional_*` helpers, every field validated upfront. `object`/`value_column`/`representation` are validated against `src.features.sdc`'s known sets at config-load time - a typo here would otherwise only surface after the first subject's file is opened (`object`) or column-indexed (`value_column`), potentially after hundreds of files have already been read. No `lesion_glob` field - unlike `build_lesion_matrix.json`, lesion mask presence is resolved from `assets/metadata/*_participants_lesions.tsv`, not from a glob against `data_root`.

**`representation`** (`"parcellated"` or `"voxelwise"`, required, added 03/09) picks which builder runs and which of the remaining fields are required - never a silent default for the unused mode's fields, never required-but-ignored:

| Field | `"parcellated"` | `"voxelwise"` |
|---|---|---|
| `atlas` | required | not read (must be omitted from the config, or simply ignored if present - not validated either way) |
| `value_column` | required, validated against `KNOWN_VALUE_COLUMNS` | not read |
| `reference_labels_path` | required | not read |
| `reference_template_path` | not read | required |
| `resample_interpolation` | not read | required, validated against the same `_KNOWN_INTERPOLATIONS` set `build_lesion_matrix.json` uses |

`representation="voxelwise"` combined with `object="lesion"` raises `ValueError` at config-load time already (before `src.features.sdc.build_sdc_voxelwise_matrix` would raise the same thing again at call time) - see "the voxel-wise representation" above for why.

## `src/pipeline/build_sdc_matrix.py` — CLI entry point

`python -m src.pipeline.build_sdc_matrix --config config/pipelines/build_sdc_matrix.json`. Same shape as `build_lesion_matrix.py` (staged `try`/`except` per phase, `summaries/build_sdc_matrix/<project>/` + `logs/build_sdc_matrix/<project>/` written every run, `output_root/<dd-mm>_<session_name>/` via `save_matrix`). Dispatches on `config.representation`:

- **`"parcellated"`**: `extra_arrays` holds `region_names` (the column labels, `str` dtype) - no drop mask, no column is ever dropped. `Params used:` records `{"object": ..., "atlas": ..., "value_column": ...}`.
- **`"voxelwise"`**: `extra_arrays` holds `non_constant_mask` (boolean drop-mask, same convention as `build_lesion_matrix.py` - `region_names.npy` is not written in this mode). `Params used:` records `{"object": ..., "representation": ...}`. `nib.filebasedimages.ImageFileError` is caught alongside `FileNotFoundError`/`ValueError` (a truncated/corrupt `.nii.gz`, same reasoning as `build_lesion_matrix.py`) - the parcellated path never touches `nibabel` at all, so that exception type is only reachable via this mode.
- Both modes: `config.md`/the report add two sections beyond `build_lesion_matrix.py`'s single "Excluded by group_filter": **"Excluded (SDC output present but no lesion mask)"** and **"Have a lesion mask but no SDC output yet"** - both persisted, not just logged (same reasoning as `AUDIT_FINDINGS.md #48` for `build_lesion_matrix.py`'s `excluded_by_group`).
