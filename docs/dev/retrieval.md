# Data retrieval — technical reference

Audience: developers/agents working on `src/retrieval/` and `src/pipeline/retrieve_data.py`. For "how do I run this", see `docs/guides/retrieval.md`.

Scope today: 4 stroke datasets in `Clinical_connectome` (`UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`). NEMESIS is a different source with a different layout (sessions, separate derivatives folders) and is **not** covered by this module — it will be addressed separately when that work starts, most likely by writing a second class alongside `Dataset`, not by generalizing this one speculatively.

## Module layout

```
config/
├── data_retrieval.json   # per-run request: which datasets, subjects, files, options
└── file_patterns.json    # registry: (space, modality) -> filename template(s) - see below
src/retrieval/
├── config.py    # parsing/validation of both JSON files - no filesystem I/O
└── dataset.py   # Dataset class - resolves paths for one dataset, does touch the filesystem
src/pipeline/
└── retrieve_data.py   # CLI entry point: validate upfront, copy, write report
```

Single-class design: **one** `Dataset` class is instantiated once per requested dataset name (`Dataset(project_root, "UNIPD/WashU", file_patterns)`), not a subclass per dataset. The 4 in-scope datasets share the same on-disk convention exactly; differences between them (which native modalities exist, presence of `participants.tsv`) are discovered from disk at runtime (`available()`), never hardcoded per dataset name.

### `Dataset` — what `lesion_root` actually points to

```python
self.lesion_root = project_root / name      # e.g. .../UNIPD/WashU - the WHOLE dataset tree
self.features_root = project_root / "features" / name   # separate tree, Task 3, not used yet
```

`lesion_root` contains **both** native files (`sub-*/anat/...`) **and** the dataset's own `derivatives/manual_masks/...` subfolder — it is not "native-only". The axis that matters for lookups is the `space` parameter passed to `resolve()`, not which root you start from. See the module docstring in `dataset.py` for the fuller writeup of this distinction (it caused real confusion during design — worth re-reading if extending this class).

## The `file_patterns.json` registry — why it exists

Originally, "where does a `(space, modality)` file live on disk" was hardcoded in `Dataset` as Python `glob()` calls (e.g. `*_{modality}.nii.gz`). Two problems with that:

1. **Ambiguous glob matches.** The pattern for `lesion_roi` (`*_lesion_roi.nii.gz`) matches *both* real naming variants found across datasets: `sub-X_lesion_roi.nii.gz` (used by PASPORT) and `sub-X_space-T1w_lesion_roi.nii.gz` (used by WashU and UKLFR/stroke_UKLFR — verified on real data: each dataset uses one variant consistently, never both for the same subject, but nothing in the code *guaranteed* that). If a subject ever had both, `next(glob(...), None)` picked whichever the filesystem happened to list first — non-deterministic, unlogged, and not reproducible across runs.
2. **Not inspectable.** The mapping was buried in Python string formatting - a non-programmer collaborator had no way to check "what file does `{space: mni, modality: lesion_mask}` actually mean" without reading source code.

The registry (`config/file_patterns.json`) fixes both: it is a plain JSON mapping from `space` → `modality` → an **ordered list of path templates** (relative to a dataset's root, `{subject_id}` as the only placeholder — note `subject_id` already includes the `sub-` prefix, e.g. `sub-STUNIPD0002`, so templates must not add a second one):

```json
{
  "native": {
    "T1w": ["{subject_id}/anat/{subject_id}_T1w.nii.gz"],
    "lesion_roi": [
      "{subject_id}/anat/{subject_id}_lesion_roi.nii.gz",
      "{subject_id}/anat/{subject_id}_space-T1w_lesion_roi.nii.gz"
    ]
  },
  "mni": {
    "lesion_mask": [
      "derivatives/manual_masks/{subject_id}/anat/{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
    ]
  }
}
```

Loaded by `config.load_file_patterns()` into a `FilePatterns` dataclass (`patterns: dict[(space, modality), list[str]]`), with two accessors: `.has(space, modality)` and `.templates_for(space, modality)` (raises `ValueError` if the combination isn't registered at all).

This registry is now the **single source of truth** for which `(space, modality)` combinations exist — the `NATIVE_MODALITIES`/`MNI_MODALITIES` constants that used to live in `config.py` are gone; "known modalities" is simply "whatever keys are in this file". Adding a new modality, or a second MNI derivative (the limitation the old design explicitly deferred), is now a JSON edit, not a code change.

**No glob wildcards inside templates.** Since `{subject_id}` is substituted with the real subject ID before checking `Path.is_file()`, resolution is a plain existence check on an exact filename — the non-determinism from point 1 above is eliminated at the root for any (space, modality) whose templates are fully registered, not just documented as a known caveat.

### Two ways to register naming variants — same key vs different key

If two filenames represent the *same logical thing*, named differently by different acquisition pipelines (this is the real, verified case for `lesion_roi` above), register both templates under the **same** key, in priority order. If they represent two *genuinely different* things, register them under **different** modality names instead, so they can be requested independently and are never conflated. This is a domain decision made by whoever edits `file_patterns.json`, not something the code infers.

### Ambiguous matches: priority + explicit flag, never silent

`Dataset.resolve(subject_id, space, modality)` tries each registered template, in order, and returns a `ResolvedFile`:

```python
@dataclass(frozen=True)
class ResolvedFile:
    path: Path                     # first template that matched - the one actually used
    extra_matches: tuple[Path, ...]  # any other templates that ALSO matched, in order after path
```

If more than one template matches for the same subject (a real data anomaly, or an as-yet-unseen coexistence of two naming variants), the first-priority file is still used deterministically — but `extra_matches` is non-empty, and `retrieve_data._retrieve_subject` turns that into a WARNING-category entry in `stats.ambiguous` (own report section, see below) plus a `logging.warning(...)` call. This was an explicit design decision: two lesion files for one subject might be an equivalent naming variant, or might be a real problem (e.g. a stale file left behind after a re-segmentation) — worth a human's attention either way, never resolved by silently trusting priority alone.

`resolve()` returns `None` (not a raise) when nothing matches for that specific subject — a legitimate per-subject miss, recorded in `stats.missing`. It only raises `ValueError` if `(space, modality)` is not a registered combination *at all* (a request the registry itself has no answer for) — this should never be reachable in the normal CLI flow, since `config.py._require_known_combinations` already rejects an unregistered combination at config-load time; the raise in `resolve()` is a defensive fallback for direct/programmatic use of `Dataset`.

`Dataset.available(space, modality)` mirrors this dataset-wide: true if *any* subject in the dataset has a file matching *any* registered template for that combination. Used by upfront validation (`_validate_retrieve_items`) to reject a request a dataset can never satisfy, before any copying starts.

## The STOP / WARNING / informational matrix

This is the core contract of the pipeline and is enforced in `src/pipeline/retrieve_data.py`:

| category | cases | where enforced |
|---|---|---|
| 🛑 STOP — validated upfront, across **all** requested datasets, before any file is copied | `(space, modality)` not registered in `file_patterns.json` at all · modality/space not structurally present in a dataset · `group_filter` matches 0 subjects in a dataset · unknown explicit `subjects` entry · duplicate `(space, modality)` pair in `retrieve` · dataset root unreachable · invalid config | `_build_datasets`, `_validate_upfront` (`retrieve_data.py`), `load_config`, `_require_known_combinations` (`config.py`) |
| ⚠️ WARNING — logged, run continues | file missing for a specific subject · an explicitly requested subject not present in a specific requested dataset · more than one registered file matched for a subject (highest-priority one used) · a `sub-*` folder found on disk that doesn't match the expected subject naming (excluded from retrieval) · copy fails for a specific file (permissions, disk full, ...) | `_retrieve_subject`, `_report_explicit_subjects_absent_from_dataset`, `_report_non_conforming_subject_folders`, `_copy_one` |
| ℹ️ informational | destination already exists: skipped (`overwrite=false`) or overwritten (`overwrite=true`) | `_copy_one`, `_retrieve_participants` |

`group_filter` is **not** validated (and not applied) when `config.subjects` is set explicitly — picking exact subject IDs already expresses full intent, so group filtering would be redundant and potentially confusing (see `_validate_upfront`: the group-filter check is skipped entirely when `subjects is not None`).

`_build_datasets` instantiates every requested `Dataset` before any validation or copying starts — a missing dataset root raises immediately and nothing is copied for any dataset in the request, including ones that would have been valid.

### Non-conforming `sub-*` folders: always excluded, never crash, always visible

`Dataset.subjects()` only returns folders whose name matches `_SUBJECT_RE` (the `sub-<DISEASE><SITE>[HC]<NUM>` convention). This used to be inconsistent: `group_of()` was only ever called (and only ever raised on a bad name) when a `group` filter was passed to `subjects()` — a request with no filter silently absorbed a stray non-conforming folder (e.g. a leftover QC/test directory) as if it were a real subject, while the exact same folder crashed the entire run the moment `group_filter` was used, with an error message that didn't explain the real cause. Both behaviors are gone: `subjects()` now filters non-conforming names out unconditionally, so `group_of()` is never invoked on one from within `Dataset`'s own code paths, regardless of how the request was made. `Dataset.non_conforming_subject_folders()` surfaces what got excluded, and `retrieve_data._report_non_conforming_subject_folders` turns that into its own report section per dataset (relevant to the ongoing subject-ID standardization effort) — never silently invisible, never a crash.

### Explicit `subjects` across multiple datasets

`_validate_explicit_subjects` only checks that each requested subject exists in **at least one** of the requested datasets (subject IDs are dataset-unique by naming convention, so a subject can never legitimately belong to two of them). That check alone would leave a dataset that doesn't have a given requested subject completely silent about it — `_select_subjects` just filters it out, no error, no trace. `_report_explicit_subjects_absent_from_dataset` closes that gap: for every dataset, it diffs `config.subjects` against the subjects actually selected from that dataset and records the difference as a WARNING-category miss (`"<dataset>: <subject_id> - not present in this dataset"`), distinct in wording from a file-missing-for-a-known-subject miss. Duplicate IDs in `config.subjects` are deduplicated before this diff, so a repeated ID in the request can't produce duplicate lines in the report.

### Why `RetrieveItem` validates itself (`__post_init__`)

`RetrieveItem.__post_init__` checks `space in KNOWN_SPACES` unconditionally, regardless of how the instance is constructed (`load_config`, a test, or future code) — `_retrieve_subject` used to pick `native()` vs `mni_mask()` with a plain `if item.space == "native" else ...`, so any other value would have silently fallen into the wrong branch. `modality` validity is **not** checked in `__post_init__` anymore (it used to be, against the old static `NATIVE_MODALITIES`/`MNI_MODALITIES` tuples) — it now depends on the external `file_patterns.json` registry, which a dataclass constructor can't reasonably depend on. That check moved to `config._require_known_combinations`, called once in `load_config` right after both `retrieve` and `file_patterns` are parsed.

### Duplicate `retrieve` entries are rejected, not deduplicated

Two identical `{space, modality}` entries would make the pipeline process the same subject twice for the same file: the first copies it, the second sees the same destination already exists and logs it as `skipped_existing` — indistinguishable in the report from a file genuinely already present from an earlier run (a duplicated `native/T1w` on 250 subjects would silently render as `copied: 250, skipped (exists): 250`, implying overlap with a previous run that never happened). `_reject_duplicate_retrieve_items` (`config.py`) rejects this upfront rather than silently keeping only one copy, so a copy-paste mistake in the config is never masked.

## Config schema (`src/retrieval/config.py`)

`RetrievalConfig` fields: `output_root`, `project`, `project_root`, `file_patterns_path`, `file_patterns` (parsed `FilePatterns`), `datasets`, `group_filter`, `subjects`, `retrieve` (list of `RetrieveItem(space, modality)`), `include_tabular_data`, `overwrite`. All required fields are validated with no silent defaults (`load_config` raises `ValueError` naming the offending field). `config.py` never touches the filesystem for *dataset* data — existence checks (dataset root, specific subject files) happen in `Dataset`/`retrieve_data.py`; it does read `file_patterns_path` off disk, since the registry itself is config, not dataset data.

Known groups: `ST`, `HC`, `PD`, `GM`. Known spaces: `native`, `mni`. Known modalities: whatever is registered in `file_patterns.json` (see above) — not a static list in code anymore.

## Output layout

```
<output_root>/<project>/<dataset>/
├── participants.tsv                        # verbatim copy, only if include_tabular_data and present at source
└── <subject_id>/lesion/
    ├── native/<original filename>.nii.gz
    └── mni/<original filename>.nii.gz
```

Filenames are preserved exactly as at the source (no renaming/transformation) — this is a straight copy, not a derived product.

## Report

Written to `reports/data_retrieval/<project>/<dd-mm-yy>__<hh-mm>.md` (fixed repo convention, like `data/`/`docs/`/`src/` — not itself in config, unlike `output_root`). Title is `<project>_<dd-mm-yy>` with the run time as a subtitle; the file name keeps minute precision so multiple runs on the same day don't collide.

Content, in order:
1. A verbatim JSON dump of the fields actually read from the config (derived from the parsed `RetrievalConfig`, not a re-read of the file, so it can't drift from what the run actually used — see `_config_summary`; `file_patterns` is shown as its configured path, not the full registry content).
2. The aggregate summary table per dataset (subjects selected, copied, skipped, failed, participants status).
3. **Missing** — file not found for a specific subject, or an explicitly requested subject not present in that dataset.
4. **Ambiguous** — more than one registered file matched for a subject; the highest-priority one was used regardless.
5. **Non-conforming subject folders** — `sub-*` folders found on disk that don't match the expected naming convention, excluded from retrieval.

Sections 3-5 share the same rendering (`_grouped_section`): grouped per dataset, a `<Section> Count = N` line per dataset, a `---` separator between datasets, `- none` if nothing to report anywhere. Never a list of successful copies — only anomalies.

## Log

`main()` writes the full narrative (skip/copied/warning/error lines, exactly as printed to console) to `logs/data_retrieval/<project>/<dd-mm-yy>__<hh-mm>.log` in addition to the console `StreamHandler` — the file is not a replacement for console output. The timestamp is shared with the report from the same run (`_write_report(config, stats, now)` reuses the `now` computed for the log path), so a report and its log always have the same file stem and can be matched by name.

The file handler is attached only once `config.project` is known (i.e. after `load_config` succeeds) — a config-load failure has nowhere to put a log file, so it only reaches the console. `_attach_file_handler` removes any `FileHandler` left on the root logger by a previous `main()` call in the same process before attaching a new one; without this, calling `main()` twice in one interpreter (e.g. a notebook) would keep writing the second run's lines into the first run's log file (see `test_main_does_not_leak_log_lines_across_runs`).

## Testing

`tests/unit/` — synthetic fixtures in `tmp_path`, no EBRAIN mount required, run always. `tests/integration/` — against the real mount and the real `config/file_patterns.json` registry, `pytest.mark.skipif` if unreachable; several assert exact counts verified manually during design (e.g. WashU MNI mask count is 201, not 202 — one subject, `sub-STUNIPD0001`, has an orphaned derivative with no matching raw subject folder; see the comment in `tests/integration/test_lesion_counts.py`), plus a check (`test_no_ambiguous_matches_across_real_data`) that no real subject today has files matching more than one registered `lesion_roi` variant simultaneously. Run with:

```bash
conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v
```
