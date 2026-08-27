# SDC feature matrix — technical reference

Audience: developers/agents working on `src/features/sdc.py`, `src/analysis/build_config.py` (the `build_sdc_matrix.json`-parsing half), and `src/pipeline/build_sdc_matrix.py`.

This file covers turning retrieved, atlas-parcellated SDC output (`sdc/<subject_id>/dwi/*.csv`, produced upstream by `src/sdc/`/`compute_sdc.py`'s BCBToolKit Stage 1+2) into a feature matrix ready for dimensionality reduction. For the equivalent lesion (voxel-wise) pipeline, see `docs/dev/lesion_matrix.md`. For "how do I run this", see `docs/guides/sdc_matrix_building.md`.

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

`build_sdc_matrix(data_root, datasets, lesion_glob, object_, atlas, value_column, reference_labels_path, group_filter) -> (X, metadata, region_names, excluded_by_group, excluded_no_lesion_mask, sdc_not_yet_computed)`

- **`object_`**: `"disconnectome"` or `"lesion"` - which of the two parcellated CSV families to read (`docs/guides/sdc_matrix_building.md` for the difference). Validated against `KNOWN_OBJECTS`.
- **`value_column`**: which per-region statistic to extract - `"fraction_covered"`, `"mean_overlap"`, `"weighted_mean_overlap"`, `"sum_overlap"`, `"p90_overlap"`, or `"p95_overlap"` (`KNOWN_VALUE_COLUMNS`; these 6 are the columns common to all 14 in-scope atlases - `buckner_7n`/`rojkova`/`yeh_hcp1065` additionally have `sum_atlas_in_tract`/`pwll_normalised`/`max_atlas_prob_in_overlap`/`continuous_dice`, not currently exposed here).
- **`X` never drops a constant column** - unlike `build_lesion_matrix.py`'s `_drop_constant_features`, column `j` always names the same region regardless of which subjects a given run admits (2026-08-27, project decision: keeps `X`'s shape - and therefore its meaning - stable across runs with different subject selections, at the cost of carrying always-zero columns for regions no admitted subject ever disconnects).

### Subject admission: two discovery passes, one intersection

A subject is admitted into `X` only if it has **both**:
1. A real lesion mask (`lesion_glob`, same glob `build_lesion_matrix.json` uses, discovered the same way via `discover_files_by_subject`).
2. The requested `object_`/`atlas` SDC CSV (`sdc/*/dwi/*_LF-{object_}_atlas-{atlas}.csv`).

This is not a redundant check: a real subject in this cohort (`sub-STUKLFR0671`) has SDC output (both `lesion` and `disconnectome` CSVs, empty - header only) but **no lesion mask at all** in `manual_masks/` - almost certainly a retrieval/upstream gap, not a genuine "zero disconnection" clinical observation. Admitting it as an all-zero row would be indistinguishable, downstream, from a subject who genuinely has no disconnected regions - the two are not the same claim. `excluded_no_lesion_mask` tracks subjects like this explicitly (logged and persisted to `config.md`, never silently dropped); `sdc_not_yet_computed` tracks the opposite gap (a lesion mask exists but SDC hasn't been computed for that subject yet - not an error, just work not yet done upstream).

If the intersection is empty across every dataset, `build_sdc_matrix` raises `ValueError` rather than returning an empty matrix.

### Per-CSV validation (`_load_and_validate_csv`)

For every admitted subject's CSV:
- `region_name` column must be present.
- `value_column` must be present.
- No duplicate `region_name` values (raise `ValueError` listing them - a duplicate would otherwise make `.set_index("region_name")` produce a non-unique index, and the resulting `.reindex()` failure is a confusing pandas `ValueError` that doesn't name the offending file).
- Every `region_name` found must exist in the reference set (raise `ValueError` otherwise - see "Reference labels" above).

A header-only (zero-row) CSV is a legitimate domain case handled by `_stack_aligned_matrix`: the subject's vector is all-zero, same result as if every reference region had been individually omitted.

## `src/analysis/build_config.py` — `build_sdc_matrix.json` parsing

`load_build_sdc_matrix_config(path) -> SdcMatrixConfig`, same style as `load_build_matrix_config`/`load_config`: hand-written `_require_*`/`_optional_*` helpers, every field validated upfront. `object`/`value_column` are validated against `src.features.sdc.KNOWN_OBJECTS`/`KNOWN_VALUE_COLUMNS` at config-load time - a typo here would otherwise only surface after the first subject's CSV is opened (`object`) or column-indexed (`value_column`), potentially after hundreds of files have already been read.

## `src/pipeline/build_sdc_matrix.py` — CLI entry point

`python -m src.pipeline.build_sdc_matrix --config config/pipelines/build_sdc_matrix.json`. Same shape as `build_lesion_matrix.py` (staged `try`/`except` per phase, `summaries/build_sdc_matrix/<project>/` + `logs/build_sdc_matrix/<project>/` written every run, `output_root/<dd-mm>_<session_name>/` via `save_matrix`). Differences:

- `extra_arrays` holds `region_names` (the column labels, `str` dtype) instead of a boolean drop-mask - there is no drop mask, since no column is ever dropped.
- `config.md`/the report add two sections beyond `build_lesion_matrix.py`'s single "Excluded by group_filter": **"Excluded (SDC output present but no lesion mask)"** and **"Have a lesion mask but no SDC output yet"** - both persisted, not just logged (same reasoning as `AUDIT_FINDINGS.md #48` for `build_lesion_matrix.py`'s `excluded_by_group`: "why does this matrix have fewer subjects than expected" must be answerable from `config.md` alone).
- `Params used:` records `{"object": ..., "atlas": ..., "value_column": ...}` instead of `{"binarize_threshold": ...}`.

## Known local-environment caveat (found 27-08-26)

On this Mac, `manual_masks/` (lesion masks) holds only a small local sample (10 subjects per dataset) while `sdc/` holds the full retrieved cohort (195/83/168/705 across the 4 in-scope datasets) - confirmed via a raw `Path.glob` independent of this module's own code, not a bug in subject-ID parsing/matching. A local test run therefore only ever admits the intersection available locally (40 subjects, verified 27-08-26) - a full production run (server, or after a full local retrieval) is expected to admit close to the full cohort, modulo the few genuine `excluded_no_lesion_mask` cases like `sub-STUKLFR0671`.
