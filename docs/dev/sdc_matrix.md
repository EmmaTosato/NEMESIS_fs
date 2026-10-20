# SDC feature matrix — technical reference

Audience: developers/agents working on `src/features/sdc.py`, `src/analysis/build_config.py` (the `build_sdc_matrix.json`-parsing half), and `src/pipeline/build_sdc_matrix.py`.

This file covers turning SDC output (`bcbtoolkit/<subject_id>/*`, produced upstream by BCBToolKit Stage 1+2) into a feature matrix ready for dimensionality reduction, in any of three representations picked by `config.representation`: **parcellated** (`build_parcellated_matrix` in `src/features/parcellated_csv.py`, the original one - one CSV per atlas, `LF-{object}_atlas-*.csv`), **voxelwise** (`build_sdc_voxelwise_matrix`, added 03/09 - the pre-parcellation `disconnectome-map` `.nii.gz` directly, same resampling-onto-a-common-grid approach as the lesion pipeline, with the same optional `correct_out_of_brain`) or **streamline** (`build_sdc_streamline_matrix`, added 30/09 - the `yeh_hcp1065_streamline` CSV, one `streamline_ratio` per white matter tract). For the equivalent lesion (voxel-wise) pipeline, see `docs/dev/lesion_matrix.md`. For "how do I run this", see `docs/guides/sdc_matrix_building.md`.

## Why this pipeline looks different from `build_lesion_matrix.py`

`build_lesion_matrix.py`'s voxel-wise matrix aligns subjects onto a common spatial grid via resampling - every subject's raw NIfTI has the same shape after `resample_to_img`, so columns line up by *position*. SDC's per-subject output is not a NIfTI grid but one CSV per (subject, atlas, object) pair, one row per anatomical region - and rows are **not in a stable order across subjects** (verified empirically: real CSVs are sorted by `mean_overlap` descending, not by region). Alignment here is done by `region_name` as a key (`pandas.reindex`), never by row position.

**BCBToolKit omits regions at zero overlap instead of writing them explicitly** - verified across the full local cohort (zero rows with `mean_overlap==0.0` written explicitly, out of >1000 subjects sampled during `notebooks/exploration/sdc_analysis.ipynb`). A missing row is therefore filled with `0.0` via `reindex`, not treated as a data gap.

**Row order, every representation**: by dataset name, then `subject_id` (`sorted(admitted.items())`, and the same for the parcellated builder). It is the criterion `build_lesion_matrix` uses too, so the two matrices of one cohort have the same row order.

## What a subject's `bcbtoolkit/<subject_id>/` must contain

A flat folder (no intermediate `dwi/` subfolder), with exactly:

- **31 parcellated CSVs** named `<subject_id>_space-MNI152NLin6Asym_LF-{object}_atlas-{atlas}.csv`: 15 `LF-disconnectome` (one per atlas: `aal`, `buckner_7n`, `rojkova`, `schaefer_{200,300,400}_7n`, `schaefer_{200,300,400}_tian_s{1,2}`, `tian_s1`, `tian_s2`, `yeh_hcp1065`) and 16 `LF-lesion` (the same 15 plus `yeh_hcp1065_streamline`, which has no disconnectome counterpart);
- the voxel-wise `*_res-1_desc-disconnectome.nii.gz` and the two `*_mapstats.tsv`, for 34 files in total.

The check that matters is on the **set of names**, not the count: 31 files with a wrong or duplicated atlas pass a cardinality check. `notebooks/exploration/sdc_analysis.ipynb` (section 1) derives the expected set from the two atlas lists and raises on any missing or unexpected CSV, and on any entry of `bcbtoolkit/` that is not a `sub-*` folder. A subject that is registered (`has_sdc`) but incomplete is therefore caught there, before a builder fails on the first missing file.

## Sanity checks on a built parcellated matrix

The exploration notebook applies three checks to the in-memory `X`: every value in `[0, 1]` and no NaN (both raise), and the **number** of zero-variance columns (printed, never an error). The last is a diagnostic and not a guarantee in either direction: the production parcellated `X` never drops a column (see below), so constant columns are expected whenever no admitted subject disconnects a region.

## Reference labels (`assets/atlases/sdc_labels/<atlas>.csv`)

The set of columns (regions) `build_parcellated_matrix()` produces for a given atlas is **fixed and authoritative**, read from `assets/atlases/sdc_labels/<atlas>.csv` (one `region_name` per row) - not re-derived per run as the union of whatever regions happen to appear in the current subject selection. This matters for two reasons:

1. **Completeness**: an atlas region never disconnected by any subject in a given run's selection would otherwise silently vanish from the matrix. The reference file was derived once from the *entire* local cohort (all 4 in-scope SDC datasets, ~1150 subjects) for each atlas currently supported, confirmed to reach that atlas's known/expected cardinality (e.g. `schaefer_200_tian_s2` = 200 Schaefer cortical + 32 Tian S2 subcortical = 232 regions, `schaefer_400_tian_s2` = 432 - both confirmed to reach exactly that count across the full cohort, no region ever missing).
2. **Validation**: every `region_name` found in a subject's CSV must exist in the reference set - a region name the reference doesn't know about raises `ValueError` immediately (an atlas mismatch, a corrupt file, or a naming change upstream), never silently added as an extra column or ignored.

Cardinalities for atlases not yet backed by a reference file are **not** derived from an empirical proxy (an earlier draft of this design used "max rows observed in a single subject" - dropped once the reference-file approach was adopted, since it can only ever be a lower bound, not the true cardinality). Adding support for a new atlas means adding its reference file first (see "Adding a new atlas" below).

**A known atlas anomaly, not currently supported**: `buckner_7n`'s CSV holds exactly one row per subject, with `region_name` set to the atlas's own filename (`atl-Buckner7_space-MNI_dseg`) rather than one row per cerebellar network - its CSV structure doesn't match the other 14 atlases and is excluded from this pipeline for now (2026-08-27, on request - not currently a target atlas). `yeh_hcp1065_streamline` (lesion-side only) is a different schema entirely (`tract,streamline_ratio`, no `region_name`) and is out of scope **for this builder** - it has its own, `representation: "streamline"` (see below), rather than being forced into the parcellated one.

### Adding a new atlas

1. Confirm the atlas isn't `buckner_7n` (see above) or `yeh_hcp1065_streamline` (which has its own representation, not a reference file added here).
2. Derive the reference region list from the full local cohort (same approach as `schaefer_200_tian_s2`/`schaefer_400_tian_s2`): union every `region_name` across every subject's CSV for that atlas, across all in-scope datasets, and confirm the union reaches the atlas's known/expected cardinality (published value, or a locally-verified fmriprep `dseg.tsv` for atlas combos that include one - see `assets/atlases/fmriprep/atlas-Yan<N>Tian<Sx>Buckner7N/*_dseg.tsv`, whose additive structure - e.g. 200 Schaefer + 16 Tian S1 + 7 Buckner = 223 - helped cross-check the individual-component cardinalities used here).
3. Write the confirmed list, one `region_name` per row (header included), to `assets/atlases/sdc_labels/<atlas>.csv`.

## `src/features/parcellated_csv.py`

The parcellated builder and the subject-admission helpers every BCBToolKit-based builder shares (`registered_subjects`, `subjects_with_lesion_mask`, `discover_by_dataset`, `load_reference_regions`) live here, below `sdc.py` in the layering: `sdc.py` imports `src.features.lesion`, so a module both of them need cannot sit in either.

`build_parcellated_matrix(data_root, datasets, object_, atlas, value_column, reference_labels_path, group_filter, excluded_subjects) -> (X, metadata, region_names, excluded_by_group, excluded_by_list, excluded_no_lesion_mask, csv_not_yet_computed)`

- **`object_`**: `"disconnectome"` or `"lesion"` - which of the two parcellated CSV families to read (`docs/guides/sdc_matrix_building.md` for the difference). Validated against `KNOWN_OBJECTS`.
- **`value_column`**: which per-region statistic to extract - `"fraction_covered"`, `"mean_overlap"`, `"weighted_mean_overlap"`, `"sum_overlap"`, `"p90_overlap"`, or `"p95_overlap"` (`KNOWN_VALUE_COLUMNS`; these 6 are the columns common to all 14 in-scope atlases - `buckner_7n`/`rojkova`/`yeh_hcp1065` additionally have `sum_atlas_in_tract`/`pwll_normalised`/`max_atlas_prob_in_overlap`/`continuous_dice`, not currently exposed here).
- **`X` never drops a constant column** - unlike `build_lesion_matrix.py`'s `_drop_constant_features`, column `j` always names the same region regardless of which subjects a given run admits (2026-08-27, project decision: keeps `X`'s shape - and therefore its meaning - stable across runs with different subject selections, at the cost of carrying always-zero columns for regions no admitted subject ever disconnects).

### Subject admission: two discovery passes, one intersection, one curated list

A subject is admitted into `X` only if it has **both**:
1. A lesion mask **registered** in `assets/metadata/participants.csv` (column `has_lesion == True`, via `src.utils.participants.load_participants_registry`) - not a glob against `manual_masks/` on disk (see "Why participants.tsv, not `manual_masks/` on disk" below).
2. The requested `object_`/`atlas` SDC CSV (`bcbtoolkit/*/*_LF-{object_}_atlas-{atlas}.csv`, discovered via `discover_files_by_subject` same as `build_lesion_matrix.py`).

...and is not in `excluded_subjects`, the hand-curated admission list (`assets/metadata/excluded_subjects.csv`, resolved by the pipeline via `src.utils.participants.load_excluded_subjects` and passed in as an id set). Applied inside `_subjects_with_lesion_mask`, which is the one place **both** representations resolve their admitted subjects - so one call site covers `build_sdc_matrix` and `build_sdc_voxelwise_matrix`, and the SDC matrices drop exactly the subjects the lesion matrix drops (`src/features/lesion.py::_drop_excluded_subjects`). Without that guarantee a lesion-vs-SDC comparison would silently compare two different cohorts, which is why the list is one shared file rather than one per pipeline - and why this module can honour it at all despite never loading a raw lesion mask: the list is subject ids, not imaging.

Applied **after** `group_filter`, so a subject is never reported twice: an HC subject that also appears on the list is `excluded_by_group`, not `excluded_by_list`. `excluded_by_list` names only the subjects in scope for this run, never the whole file.

`excluded_no_lesion_mask` tracks subjects with SDC output but no registered lesion mask (logged and persisted to `config.md`, never silently dropped or zero-filled); `csv_not_yet_computed` (`sdc_not_yet_computed` in the voxelwise and streamline builders) tracks the opposite gap (a registered lesion mask but SDC not computed for that subject yet - not an error, just work not yet done upstream).

If the intersection is empty across every dataset, `build_parcellated_matrix` raises `ValueError` rather than returning an empty matrix.

### Why `participants.tsv`, not `manual_masks/` on disk (found 27-08-26)

The first version of this pipeline resolved "has a lesion mask" by globbing `manual_masks/` directly (same glob `build_lesion_matrix.py` uses) - this is wrong whenever a local `data/` copy is a **partial local sample**: on this Mac, `manual_masks/` held only 10 subjects per dataset while `sdc/` held the full cohort (195/83/168/705), so a local run only ever admitted the 40-subject intersection available on disk, and (confirmed by re-checking the subject registry directly) at least one subject flagged as "no lesion mask" this way (`sub-STUKLFR0671`) in fact **does** have one registered - the local `manual_masks/` gap was a local-sampling artifact, not a genuine missing-lesion case.

Fixed by resolving lesion-mask presence from `assets/metadata/participants.csv` instead - the authoritative registry of which subjects have a lesion mask at all, independent of what's currently copied on any one machine. A genuine `excluded_no_lesion_mask` case is a subject whose registry row has `has_lesion == False`, or which has no registry row at all (verified real example: `sub-STUKLFR0005`). `_subjects_with_lesion_mask` raises `ValueError` if a requested dataset has no row whatsoever in the registry - a structural gap this pipeline's core admission criterion depends on, never silently treated as "nobody in that dataset has a lesion mask".

A full local run before this fix admitted 40/1151 subjects; after the fix, the same local run (SDC CSVs untouched, only the admission criterion changed) admits 1119/1151 - the remaining 32 exclusions are all genuine registry gaps (subject not flagged `has_lesion` in the registry), confirmed individually, not local-sampling artifacts.

### Per-CSV validation (`load_and_validate_csv`)

For every admitted subject's CSV:
- `region_name` column must be present.
- `value_column` must be present.
- No duplicate `region_name` values (raise `ValueError` listing them - a duplicate would otherwise make `.set_index("region_name")` produce a non-unique index, and the resulting `.reindex()` failure is a confusing pandas `ValueError` that doesn't name the offending file).
- Every `region_name` found must exist in the reference set (raise `ValueError` otherwise - see "Reference labels" above).

A header-only (zero-row) CSV is a legitimate domain case handled by `stack_aligned_matrix`: the subject's vector is all-zero, same result as if every reference region had been individually omitted.

## `build_sdc_voxelwise_matrix` — the voxel-wise representation (added 03/09)

`build_sdc_voxelwise_matrix(data_root, datasets, object_, reference_template_path, resample_interpolation, group_filter, excluded_subjects, correct_out_of_brain, brain_mask_path) -> (X, metadata, non_constant_mask, excluded_by_group, excluded_by_list, excluded_no_lesion_mask, sdc_not_yet_computed, corrected_subjects)`

Reads the `disconnectome-map` `.nii.gz` directly (`bcbtoolkit/*/*_res-1_desc-{object_}.nii.gz`) instead of the parcellated CSVs - the same pre-parcellation volume `build_parcellated_matrix`'s CSVs are themselves derived from. Same admission criterion as `build_sdc_matrix` (a lesion mask registered in `assets/metadata/participants.csv`, not on the exclusion list, **and** the requested SDC file present) - both go through the same `_subjects_with_lesion_mask`.

- **Deliberately restricted to `object_="disconnectome"`** - `object_="lesion"` raises `ValueError` immediately (both here and, redundantly, at config-load time - see below). The `lesion-map` `.nii.gz` (the resampled *input* lesion mask BCBToolKit used, not the real mask) would duplicate `build_lesion_matrix.py`'s own job from a less authoritative source; `manual_masks/` (via the `has_lesion` registry flag) stays the one place a lesion mask is built from.
- **Never binarized** - disconnection values are a continuous [0, 1] probability, unlike `build_lesion_matrix.py`'s binary lesion mask. No `binarize_threshold` field exists for this representation.
- **Resampling**: reuses the same `nibabel`/`nilearn.image.resample_to_img` pattern as `src/features/lesion.py` (own local `_needs_resample`, same `_AFFINE_ATOL` tolerance - not imported cross-module, see the code comment on why), onto `reference_template_path`'s grid, with `resample_interpolation` chosen by the caller. Unlike a binary mask, nothing here *forces* a discrete interpolation - the disconnectome is a continuous [0, 1] field, so `"linear"` would also be principled. **The project uses `"nearest"`** anyway, for consistency with the three pipelines that already resample (`build_lesion_matrix.py`, `mask_fc.py`), and because on the real data the choice is measurably free: all 5 SDC datasets are 1mm isotropic at `(182, 218, 182)` and differ from the reference only by axis flips and integer shifts, so every target voxel centre lands exactly on a source voxel centre and `"nearest"`/`"linear"` produce **bit-identical** output (verified 06-09-26 on UNIPD/PASPORT vs. UNIPD/WashU). Should a dataset with a genuinely misaligned or lower-resolution grid ever be onboarded, revisit this - `"nearest"` would then quantise by up to half a voxel where `"linear"` would not.
  - **Do not use `"continuous"`** (cubic spline): its kernel has negative lobes, so in the background - where the true value is exactly 0 - the ~64 weighted products fail to cancel in the last bits, leaving symmetric ±1 ULP noise (measured min `-2.0e-17`, 1.90M negative voxels, none beyond `-1e-12`). That noise is not an accuracy problem in itself, but it defeats `_drop_constant_features`' exact `min != max` test: voxels that are identically zero for every subject stop being constant and survive the drop. Measured on a 4-subject sample, 3.56M of the 5.57M surviving columns (64%) were pure rounding noise. `"nearest"` and `"linear"` both leave an exact `0.0` minimum and are unaffected.
- **Constant-column drop**: unlike the parcellated representation (never drops a column - see above), voxels that are identically `0.0` for every admitted subject get dropped (same rule as `build_lesion_matrix.py`: a column is constant when its min equals its max, so a NaN voxel is kept), keeping `X`'s size manageable. The drop is done in two passes over the maps (`_stack_voxelwise_matrix`): the first reads every map and keeps only the running per-voxel min and max, the second reads them again and writes just the kept voxels into a preallocated array. The full n_subjects x n_grid_voxels matrix is never in memory (it would be ~21 GB for 5845 subjects on the 2mm grid, ~42 GB at the `np.stack` peak), at the price of reading and resampling each map twice. `non_constant_mask` is persisted (`extra_arrays`) so the drop is always recoverable - this doesn't contradict the parcellated representation's "column always means the same thing" decision, since that reasoning was specifically about atlas *region identity* staying comparable across differently-scoped runs, not about voxel grids (whose meaning is already pinned by `reference_template_path`, independent of which subjects a given run admits).

### `correct_out_of_brain` — the same choice as the lesion matrix

Zeroes every voxel of every map outside `brain_mask_path` (`src/features/lesion_correction.py::zero_out_of_brain_voxels`, the function the lesion matrix uses) and keeps the subject. Disabled (`False`) by default - no correction is ever applied silently.

**Why it exists.** BCBToolKit's tractography leaves the brain: a median 0.80% of a map's mass (99th percentile 6.7%, maximum 15.3%, measured on the 5845 subjects of the 2mm cohort; the 8.9% quoted in `docs/dev/metadata.md` is the maximum of a 400-subject sample) lies outside the brain mask. Without the correction those voxels are columns of `X`: on the 5845-subject cohort, 64110 of the 291345 non-constant columns lie outside the 2mm brain mask (227235 inside). `compute_sdc_metadata` sums only inside the brain (`docs/dev/metadata.md`, "Solo dentro il cervello"), so an uncorrected matrix and its own disconnection load describe different quantities. With the flag on the two coincide: the sum of each row of `X` is `disconnection_load_voxels_2mm` (checked on real subjects, difference below float64 rounding).

- **Where it is applied**: after the map is resampled onto the reference grid (`_disconnectome_values`) and **before** anything is compared or stored, in **both** passes of `_stack_voxelwise_matrix` (`_load_disconnectome_voxels`, one function for both). Pass 1 must see the corrected values, or the constant-column mask would be computed on one matrix and applied to another; zeroed voxels become constant columns and disappear from `X`, with `non_constant_mask` still recording which columns of the full grid survived.
- **`brain_mask_path`** is required exactly when the flag is set (config-load and the builder both raise otherwise), and is read through `load_brain_mask`, the lesion matrix's own check: it must be on the reference grid, or it is resampled onto it with nearest-neighbour. An empty mask raises (it would zero everything), and so does a correction that leaves no varying voxel (`X` with 0 columns).
- **`corrected_subjects`** is `(subject_id, n_voxels_corrected, mass_removed_fraction)` triples, sorted by subject, only for subjects with at least one voxel zeroed (empty when the flag is off). The map is continuous, so the voxel count alone is not enough: `mass_removed_fraction` is the sum of the probability outside the brain over the sum overall, the share of the map that was discarded. `n_voxels_corrected` counts non-zero voxels outside the brain.
- **A map with a NaN, an infinity or a negative value raises** when the flag is on: the mass fraction is only defined for a finite, non-negative field.
- **Only `voxelwise`.** `parcellated` and `streamline` read CSVs and never touch a voxel, so a flag on there is rejected at config load rather than ignored (a run that looked corrected and was not). `s2.4-stream` and `sdc_metadata.csv` are unaffected: the first reads per-tract CSVs, the second already measures only inside the brain.
- **Reported in `config.md` and the run report**, in full, never truncated: a "Corrected by correct_out_of_brain" section with the number of corrected subjects, the median and maximum mass share, and one line per subject (`n_voxels_corrected`, `mass_removed`). With the flag off the section says so.

**Immutable once built**, as for the lesion matrix: a `data/derived/sdc_matrix/<session>/` built without the correction is never corrected in place. The corrected matrix is a new session.

## `build_sdc_streamline_matrix` — the streamline representation (added 30/09)

`build_sdc_streamline_matrix(data_root, datasets, object_, reference_labels_path, group_filter, excluded_subjects) -> (X, metadata, tract_names, excluded_by_group, excluded_by_list, excluded_no_lesion_mask, sdc_not_yet_computed)`

Reads `bcbtoolkit/*/*_LF-lesion_atlas-yeh_hcp1065_streamline.csv` (columns `tract,streamline_ratio`) into a subjects x 87 tracts matrix - one value per white matter tract, the proportion of its streamlines affected. Same admission criterion as the other two builders, via the same `_subjects_with_lesion_mask`.

**Why its own builder, not a parameter of `build_sdc_matrix`.** The schema shares nothing with the parcellated CSVs: no `region_name` column, and exactly one value column instead of the 6 interchangeable statistics in `KNOWN_VALUE_COLUMNS`. Generalising the parcellated builder to take configurable identifier/value column names would have put a rarely-varying parameter on the hot path of the representation every existing run uses, for no gain.

- **Deliberately restricted to `object_="lesion"`** - BCBToolKit writes this file only in the `LF-lesion` family; there is no `LF-disconnectome` variant of it. `object_="disconnectome"` raises immediately (and, redundantly, at config-load time). Despite the `LF-lesion` name the quantity *is* a disconnection measure (streamlines of a tract interrupted by the lesion), which is why a run of it belongs to the s2.x track in `docs/experiments/`, not s1.x.
- **A missing tract raises, it is not filled with `0.0`** - the one real behavioural difference from `build_sdc_matrix`. That builder fills omitted regions with `0.0` because BCBToolKit genuinely omits zero-overlap regions there; this file instead writes **every** tract explicitly, zeros included. Verified on the full local cohort (30-09-26): all 1734 files across the 7 datasets that have one carry the same 87 tracts in the same order, with 2-42 non-zero per subject. An incomplete file is therefore truncated or corrupt, and filling it would be exactly the silent fallback `code_standards.md` §0 rules out. An *unknown* tract raises too, same as the parcellated builder.
- **Alignment is by tract name anyway** - `reindex` against the reference list, even though the row order happens to be stable across the whole cohort. Nothing in the format guarantees it (`lessons_learned.md` #3), and after the completeness check above the reindex can only ever reorder, never fill.
- **No constant-column drop** - same rule as the parcellated representation: column `j` must always name the same tract regardless of which subjects a run admits.
- **No `atlas`/`value_column` config field** - there is exactly one streamline file per subject and one value column in it, so neither is a choice (`code_standards.md` §5: no unread config fields). `atlas` is pinned to `src.features.sdc.STREAMLINE_ATLAS` and recorded in `config.md` anyway, so a written matrix still states which file it came from.

The reference tract list lives at `assets/atlases/sdc_labels/yeh_hcp1065_streamline.csv`, alongside the parcellated atlases' own reference files but with a `tract` column instead of `region_name` (`load_reference_regions`' `column` parameter) - the reference file mirrors its own atlas's schema rather than renaming it. Derived 30-09-26 as the union of every tract across all 1734 real files, which reached exactly 87.

## `src/analysis/build_config.py` — `build_sdc_matrix.json` parsing

`load_build_sdc_matrix_config(path) -> SdcMatrixConfig`, same style as `load_build_matrix_config`/`load_config`: hand-written `_require_*`/`_optional_*` helpers, every field validated upfront. `object`/`value_column`/`representation` are validated against `src.features.sdc`'s known sets at config-load time - a typo here would otherwise only surface after the first subject's file is opened (`object`) or column-indexed (`value_column`), potentially after hundreds of files have already been read. No `lesion_glob` field - unlike `build_lesion_matrix.json`, lesion mask presence is resolved from `assets/metadata/participants.csv`, not from a glob against `data_root`.

**`representation`** (`"parcellated"`, `"voxelwise"` (03/09) or `"streamline"` (30/09), required) picks which builder runs and which of the remaining fields are required - never a silent default for an unused mode's fields, never required-but-ignored:

| Field | `"parcellated"` | `"voxelwise"` | `"streamline"` |
|---|---|---|---|
| `atlas` | required | not read (must be omitted from the config, or simply ignored if present - not validated either way) | not read (pinned to `STREAMLINE_ATLAS`) |
| `value_column` | required, validated against `KNOWN_VALUE_COLUMNS` | not read | not read (the CSV has exactly one) |
| `reference_labels_path` | required | not read | required |
| `reference_template_path` | not read | required | not read (nothing is resampled) |
| `resample_interpolation` | not read | required, validated against the same `_KNOWN_INTERPOLATIONS` set `build_lesion_matrix.json` uses | not read |
| `correct_out_of_brain` | `true` raises (`false`/absent ok) | optional boolean, `false` when absent | `true` raises (`false`/absent ok) |
| `brain_mask_path` | present raises | required when `correct_out_of_brain` is `true`, otherwise unused | present raises |

Each representation also constrains `object`, raising `ValueError` at config-load time before the builder would raise the same thing again at call time: `"voxelwise"` requires `object="disconnectome"`, `"streamline"` requires `object="lesion"` - see the two sections above for why.

## `src/pipeline/build_sdc_matrix.py` — CLI entry point

`python -m src.pipeline.build_sdc_matrix --config config/pipelines/build_sdc_matrix.json`. Same shape as `build_lesion_matrix.py` (staged `try`/`except` per phase, `summaries/build_sdc_matrix/<project>/` + `logs/build_sdc_matrix/<project>/` written every run, `output_root/<dd-mm>_<session_name>/` via `save_matrix`). Dispatches on `config.representation`:

- **`"parcellated"`**: `extra_arrays` holds `region_names` (the column labels, `str` dtype) - no drop mask, no column is ever dropped. `Params used:` records `{"object": ..., "atlas": ..., "value_column": ...}`.
- **`"streamline"`**: `extra_arrays` holds `tract_names` (the column labels, `str` dtype) - no drop mask, same as parcellated. `Params used:` records `{"object": ..., "representation": ..., "atlas": ...}`.
- **`"voxelwise"`**: `extra_arrays` holds `non_constant_mask` (boolean drop-mask, same convention as `build_lesion_matrix.py` - `region_names.npy` is not written in this mode). `Params used:` records `{"object": ..., "representation": ..., "correct_out_of_brain": ...}`; `config.md` also carries the "Corrected by correct_out_of_brain" section. `nib.filebasedimages.ImageFileError` is caught alongside `FileNotFoundError`/`ValueError` (a truncated/corrupt `.nii.gz`, same reasoning as `build_lesion_matrix.py`) - the parcellated path never touches `nibabel` at all, so that exception type is only reachable via this mode.
- Every mode: `config.md`/the report carry four exclusion sections - **"Excluded by group_filter"**, **"Excluded by `<excluded_subjects_path>`"** (shared with `build_lesion_matrix.py`), **"Excluded (SDC output present but no lesion mask)"** and **"Have a lesion mask but no SDC output yet"** - all persisted, not just logged (same reasoning as for `excluded_by_group`).
