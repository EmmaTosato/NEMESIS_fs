# Clinical/demographic metadata — technical reference

Audience: developers/agents working on `src/features/clinical.py`, `src/pipeline/enrich_lesion_metadata.py`, `src/analysis/build_config.py` (the `EnrichLesionMetadataConfig`-parsing half), or anyone trying to figure out where a given clinical/demographic value (age, sex, NIHSS, lesion_side, ...) actually lives and how it got there.

There is no single metadata store — three layers, each with a different scope, owner, and update mechanism. For "which fields exist per dataset" (age/sex/NIHSS/ARAT/Boston naming/...), see `docs/guides/datasets.md` §2 — not repeated here.

## The three layers

**Layer 2's generation mechanism is being redesigned as of 04-09-26 — treat this whole section as a description of what's on disk *today*, not of a live, rerunnable pipeline.** `scripts/data_summary.py`/`assets/dataset_summaries/` (the availability-flag input layer 2 used to be built from) and `scripts/build_participant_metadata.py` (the script that built it) have both been retired — nothing currently regenerates `assets/metadata/*.tsv`. A new design (a single raw+enriched participant table, replacing the per-dataset `_lesions/_features/_join.tsv` split) is in progress; this doc will be rewritten once it lands.

```
data/clinical_connectome/metadata_tsv/participants_*.tsv   (raw, per dataset)
        ▼
assets/metadata/<DATASET>_participants_{lesions,features,join}.tsv   (curated, per dataset — stale, see above)
        │  src/pipeline/enrich_lesion_metadata.py
        ▼
data/derived/<pipeline>/<...>/metadata.csv   (per-matrix, enriched)
```

### 1. `data/clinical_connectome/metadata_tsv/participants_*.tsv` — raw

The retrieval pipeline's object #2 ("Dati Clinici e Anagrafici", `docs/guides/datasets.md`) — a per-dataset copy from EBRAIN. Moved 04-09-26 from a per-dataset path (`data/clinical_connectome/derivatives/<dataset>/participants.tsv`) into one flat directory, ahead of the layer-2 redesign. Gitignored, not curated in any way: whatever the source clinical database exports is what's here, including dataset-specific quirks (e.g. UCL-UK's `participant_id` holds the legacy site ID, not the project's canonical `sub-*` form — see layer 2 below).

### 2. `assets/metadata/<DATASET>_participants_{lesions,features,join}.tsv` — curated, checked-in (stale, generator retired)

These files are still on disk and still what `src/features/clinical.py` reads (see below) — but nothing regenerates them today. They were last written by `scripts/build_participant_metadata.py` (retired 04-09-26), which intersected the now-also-retired `assets/dataset_summaries/data_summary__*.csv` (retrieval availability flags) with each dataset's raw `participants.tsv`.

Three file types, all `<DATASET>_participants_<suffix>.tsv`:

- **`_lesions.tsv`** (all 5 lesion-bearing datasets) — subjects with a validated lesion mask. The only one any pipeline code actually reads: `src/features/clinical.py::METADATA_ROOT`/`load_participants`/`join_participant_variables`/`join_lesion_side`/`join_nihss` all hardcode this exact suffix. This is `enrich_lesion_metadata.py`'s sole data source.
- **`_features.tsv`** (WashU only — the only dataset with FC data) — subjects with complete validated fMRI data.
- **`_join.tsv`** (WashU only) — the intersection of the two above. Matches `fc_matrix`'s own subject population by construction: `src/features/functional.py::discover_subject_files` already restricts to "subjects with both a lesion mask and an FC matrix", so `fc_matrix`'s `metadata.csv` should be compared against `_join.tsv`, never `_features.tsv` directly (checked 02-09-26: `fc_matrix` subject count matches `_join.tsv` exactly, not `_features.tsv`).

`_features.tsv`/`_join.tsv` have no consumer yet — not dead, just waiting for an FC-specific enrichment mechanism (the `enrich_lesion_metadata.py` equivalent for the FC modality) that doesn't exist today.

**Canonical vs. legacy subject id** (a property of the files as they sit on disk today, produced by the now-retired generator): every column set mirrors the source `participants.tsv` plus retrieval-availability flag columns. In 4 of 5 datasets, the source `participant_id` is already in the project's canonical `sub-{disease}{site}{num}` form (matching `subject_id` everywhere else in the repo). **UCL-UK is the one exception**: its raw `participant_id` is the legacy site id (`ST_UCL-UK_0001`), not canonical — `assets/metadata/UCL-UK_UCLStrokeData_participants_lesions.tsv` therefore has `participant_id` = canonical `sub-STUCLUK*` and `original_id` = the legacy id, the opposite of what the raw file has under those same column names. Whatever regenerates layer 2 next needs to preserve this same promotion rule.

### 3. `data/derived/<pipeline>/<...>/metadata.csv` — per-matrix, enriched

Every `build_*_matrix.py` writes a base `metadata.csv` (`subject_id`, `dataset`, plus whatever that pipeline computes itself — e.g. `lesion_volume_voxels` for `build_lesion_matrix.py`) alongside its `matrix.npy`. `src/pipeline/enrich_lesion_metadata.py` is the only pipeline that adds clinical/demographic columns to it, joined from layer 2's `_lesions.tsv` (never `_features.tsv`/`_join.tsv` — see above).

**Per-family target header** (verified 02-09-26, `docs/debugging/debug_02_09_26.md`):

| Family | Header | Note |
|---|---|---|
| lesion (`build_lesion_matrix.py`) | `subject_id, dataset, lesion_volume_voxels, lesion_side, nihss, age, sex, education, clinical_date` | 9 columns |
| SDC (`build_sdc_matrix.py`) | `subject_id, dataset, lesion_side, nihss, age, sex, education, clinical_date` | 8 columns — `lesion_volume_voxels` deliberately excluded, not meaningful for a continuous SDC `mean_overlap` matrix |
| FC (`build_fc_matrix.py`) | `subject_id, dataset` | today's floor only — never enriched by `enrich_lesion_metadata.py` yet, no `_lesions.tsv`-based enrichment mechanism wired up for it (see layer 2) |

Column order matches the order `variables` is listed in the config, appended after whatever base columns aren't being refreshed — set `config/pipelines/enrich_lesion_metadata.json`'s `variables` list in the target order shown above if you want the on-disk header to match it exactly.

**`write_in_place` / `copy_output_path`** (`EnrichLesionMetadataConfig`, redesigned 02-09-26): `metadata_path` is read-only unless `write_in_place=true`, in which case the enriched columns are written back into `metadata_path`'s own directory (the only pipeline in this repo allowed to mutate an already-written `data/derived/` output). When `write_in_place=false`, the result lands at the caller-chosen `copy_output_path` instead — required exactly when `write_in_place` is `false`, forbidden (`null`) when `true` (same required-exactly-when pattern as `ClusteringConfig.reduction_params_file`/`reduced_data`). There is no `output_root` config field: this pipeline's own `runs.csv` always lives at the fixed, non-configurable `RUNS_LOG_ROOT` (`data/derived/enrich_lesion_metadata/`, same pattern as its `REPORTS_ROOT`/`LOGS_ROOT`) — `output_root` used to double as both the run-log location and the auto-derived standalone-copy path, and the latter is exactly how `data/derived/clinical_metadata/` accumulated orphaned, unconsumed copies nobody remembered requesting; deleted along with the field.

**Re-enriching an already-enriched artifact** (a refresh, e.g. after fixing a stale upstream `assets/metadata` tsv) is a normal, supported use of `write_in_place=true` with `overwrite=true` — re-request the same `variables` again. `_join_variables` was buggy here until 02-09-26 (duplicated columns when the requested variables were already present — every historical run before that date had always requested a disjoint variable set, so the bug was latent; see `.claude/lessons_learned.md` #34 and `docs/debugging/debug_02_09_26.md`), now fixed and covered by regression tests.
