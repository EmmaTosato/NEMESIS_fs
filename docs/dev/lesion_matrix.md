# Lesion feature matrix — technical reference

Audience: developers/agents working on `src/features/lesion.py`, `src/analysis/build_config.py` (the `build_lesion_matrix.json`-parsing half), and `src/pipeline/build_lesion_matrix.py`.

This file covers turning retrieved lesion masks into a feature matrix ready for dimensionality reduction. For the models that consume that matrix, see `docs/dev/models.md`. For the equivalent FC pipeline, see `docs/dev/fc_matrix.md`. For "how do I run this", see `docs/guides/matrix_building.md`.

**Found while writing the real configs**: `lesion_glob` in every doc/config up to this point (`docs/guides/analysis.md`, this file's earlier drafts, inherited from `notebooks/lesion_analysis.ipynb`/the handoff note) was `"*/lesion/mni/*_label-lesion_mask.nii.gz"` - checked against real retrieved data in `data/clinical_connectome/` and found wrong: the actual local layout (from `src/retrieval/output_layout.py`, post-BIDS-refactor) is `<subject>/lesion/manual_masks/anat/<subject>_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`. The notebook was written against an older/different local layout and nobody had re-verified its glob since. Fixed to `"*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz"` in `docs/guides/analysis.md` and the real `config/pipelines/build_lesion_matrix.json` - confirmed against all 4 datasets in scope at the time (`find` count of subject dirs vs. matching lesion files: WashU 202/202, PASPORT 83/83, PSP 168/168, UKLFR 697/697, all equal). `docs/notes/analysis_pipeline_v2_handoff.md` still has the old, wrong glob - left as-is, since that file is an intentionally-frozen historical plan snapshot, not maintained documentation.

**Parcellation removed (25/08/26)**: an earlier version of this module also supported an atlas-parcellated output shape (`parcellate: true` - each subject's feature vector was the proportion of damage per atlas region, the characterisation Thiebaut de Schotten et al. 2020 use ahead of their varimax-rotated PCA), built via `src/pipeline/build_combined_atlas.py`/`src/atlases/` (a Glasser MMP + Harvard-Oxford subcortical combined atlas). Both were removed as a project decision - the parcellation-then-varimax-PCA replication this fed is no longer pursued through this pipeline (see `management/notes/TODO.md`). Voxel-wise is now the only output shape `build_lesion_matrix()` produces.

## `src/features/lesion.py` — lesion feature matrix

`build_lesion_matrix(data_root, datasets, reference_template_path, lesion_glob, binarize_threshold, resample_interpolation, group_filter) -> (X, metadata, non_constant_mask, excluded_by_group)`

**`group_filter`** restricts subject discovery to specific naming-derived groups (`src.retrieval.dataset.group_of` - ST/HC/PD/GM), via the shared `src/features/subject_discovery.py::discover_files_by_subject` also used by `src/features/functional.py` (`docs/dev/fc_matrix.md`). `None` means no restriction. Subjects excluded this way are returned separately as `excluded_by_group`, never conflated with a genuine missing-file gap - see `debug_27_07_26.md` and `docs/guides/matrix_building.md`.

Migrated from `notebooks/lesion_analysis.ipynb` (voxel-wise path, cells 4-8): same algorithm, restructured into typed, independently testable functions. The notebook is left as-is as the exploratory reference — this module is the version pipeline code actually calls.

**`reference_template_path` is an explicit, caller-supplied file, not derived from `datasets`** — changed from the original "pick the first lesion file of `reference_dataset` (sorted)" behavior, on request: that implicit choice silently tied the common voxel grid to whatever resolution one arbitrary subject's file happened to have, with no guarantee it matched a canonical space (e.g. MNI152 2mm) rather than just *a* space with the same name. `load_reference_image(reference_template_path) -> nib.Nifti1Image` now does exactly one thing - load that file, raising `FileNotFoundError` with a clear message if it's missing.

**Known open question, not yet resolved (AUDIT_FINDINGS.md #47)**: production's real `reference_template_path` (`config/pipelines/build_lesion_matrix.json`, session `voxelwise_s2` as of 25/08 - successor of voxel-wise session `s1.1-vol`) points at `sub-STUNIPD0001`'s own lesion mask, not a canonical MNI152 template (e.g. FSL's `MNI152_T1_2mm_brain.nii.gz`) - the space (`MNI152NLin6Asym`) is correct, but the file is a specific patient's data, not a template in the sense this section's own wording implies. The entire voxel grid of every production lesion matrix depends on that one file continuing to exist. Left unchanged deliberately in the 18-08-26 audit-triage session (a data/config choice, not a code defect) - switching to a real template is a decision for whoever next touches `build_lesion_matrix.json`, not something to change silently here.

Each subject is a flattened binarized lesion volume, resampled onto `reference_template_path`'s grid when its native resolution differs. `_drop_constant_features` then drops columns (voxels) that are identical across every subject - they carry no information for downstream PCA/UMAP/clustering. `non_constant_mask` records which columns survived (against the pre-drop feature count) so the mask can be reapplied to related data (e.g. re-running with a different subject selection).

`_discover_lesion_files(data_root, datasets, lesion_glob, group_filter)` derives the subject-folder glob from `lesion_glob` itself (the last bare `"*"` path segment) rather than assuming subject folders are `dataset_root`'s immediate children (true only under the older subject-first retrieval layout, see `docs/dev/retrieval.md`) - works for either local layout without hardcoding one. Raises `FileNotFoundError` if the subject-folder glob itself finds nothing (an unreachable dataset - wrong path/name in config, or never retrieved) before `group_filter` narrows the list, since `Path.glob` on a missing directory returns `[]` with no exception and a typo'd dataset name would otherwise silently contribute 0 subjects rather than fail loudly. `group_of()` validates every discovered subject-dir name unconditionally, not only when `group_filter` is set (`AUDIT_FINDINGS.md` #46, `lessons_learned.md` #4/#28) - skipping that check for the common "this dataset doesn't mix groups" case let a malformed folder name through silently instead of raising.

`load_reference_image(reference_template_path)` requires an explicit, caller-supplied file rather than deriving one implicitly (e.g. "the first lesion file found") - see `AUDIT_FINDINGS.md` #47 above for the known, still-open gap in what that file currently points to in production.

### Validation

`binarize_threshold`/`resample_interpolation` are cross-validated at the config layer (`src/analysis/build_config.py`) before `build_lesion_matrix()` is ever called - see below.

## `src/analysis/build_config.py` — `build_lesion_matrix.json` parsing

`load_build_matrix_config(path) -> BuildMatrixConfig`, same shape and style as `src/retrieval/config.py`'s `load_config`: hand-written `_require_*`/`_optional_*` helpers (own copy, not shared with `src/retrieval/config.py` — each is a handful of lines, premature to abstract per the handoff note's explicit deferral), every field validated upfront so a malformed config is rejected before any file is touched.

Two upfront value-domain checks, beyond type checking, both deliberate (config validation is a system boundary — `code_standards.md` §0):

- **`binarize_threshold`** must be in `[0.0, 1.0]`. Lesion mask values after resampling are nominally binary/interpolated-to-[0,1]; a threshold outside that range produces a *silently degenerate* result (every voxel above or below threshold for every subject) that only surfaces much later, as an empty/collapsed feature matrix after `_drop_constant_features` — far from where the bad config value was set.
- **`resample_interpolation`** must be one of `{"linear", "nearest", "continuous"}` — the exact set `nilearn.image.resample_to_img` accepts. Without this check, a typo here (e.g. `"neareast"`) only surfaces when `resample_to_img` is actually called on a subject whose native resolution differs from the reference grid — potentially after a long run has already processed hundreds of subjects with matching resolution.

`load_build_matrix_config` also parses `MaskFcConfig`/`BuildFcMatrixConfig` for the FC pipeline (`docs/dev/fc_matrix.md`) - same module, same style, different config shape.

## `src/pipeline/build_lesion_matrix.py` — CLI entry point

`python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json`. Same shape as `retrieve_data.py` (`main(argv) -> int`, staged `try`/`except` per phase, `summaries/build_lesion_matrix/<project>/` + `logs/build_lesion_matrix/<project>/` written every run) but simpler control flow: `build_lesion_matrix()` either succeeds for every requested subject or raises - there's no per-subject error accumulation to report, unlike `retrieve_data.py`'s copy phase.

Phases, each with its own `try`/`except` (`lessons_learned.md` #9 - a later-added phase isn't automatically covered by an earlier phase's error boundary): load config → attach log file handler (`src/utils/logging_setup.py`, `docs/dev/config.md`) → `build_lesion_matrix()` → `artifacts.save_matrix()` (output dir = `output_root/<dd-mm>_<session_name>`) → write report.

**Found while testing this script**: `artifacts.save_matrix`'s original `extra_arrays` validation (added in `src/utils/artifacts.py` during that step) wrongly assumed every extra array is subject-row-aligned with `X`. `non_constant_mask` is feature-aligned (length = pre-drop feature count), not subject-aligned - the check was removed; `save_matrix` now makes no assumption about `extra_arrays`' shape relationship to `X`, since that meaning is caller-specific (documented in `artifacts.py`).
