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
├── dataset.py   # Dataset class - resolves paths for one dataset, does touch the filesystem
├── verify.py    # post-copy checksum verification - shared by retrieve_data.py and scripts/verify_retrieval.py
└── matrix.py    # full per-subject data-availability matrix - shared by scripts/dataset_matrix.py
src/pipeline/
└── retrieve_data.py   # CLI entry point: validate upfront, copy, verify, write the copy_summary report
scripts/
├── verify_retrieval.py   # accessory: standalone, on-demand re-check of data/ against source
└── dataset_matrix.py     # accessory: standalone, read-only dataset_matrix report (see matrix.py)
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
| ⚠️ WARNING — logged, run continues | file missing for a specific subject · an explicitly requested subject not present in a specific requested dataset · more than one registered file matched for a subject (highest-priority one used) · a `sub-*` folder found on disk that doesn't match the expected subject naming (excluded from retrieval) · copy fails for a specific file (permissions, disk full, ...) · a local file no longer resolvable from any current source pattern | `_retrieve_subject`, `_report_explicit_subjects_absent_from_dataset`, `_report_non_conforming_subject_folders`, `_copy_one`, `verify._find_unexpected_local_files` |
| 🔴 ERROR — logged, run continues, but surfaced above WARNING (found only in the verification phase, after ALL datasets have finished copying) | local file's checksum doesn't match its current source · source has the file but `data/` doesn't (a copy that silently failed to land) | `_verify_dataset_copies` (`retrieve_data.py`), `verify.verify_dataset` (`src/retrieval/verify.py`) |
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

### Checksum verification: a distinct phase, run only after every dataset has finished copying

`shutil.copy2` succeeding, or a destination already existing (`skipped (exists)`), used to be treated as proof the local file was correct. Neither actually is: a copy can be truncated by a disk-full mid-write without raising, and a file already present locally may have been copied from a source that has since changed upstream (a corrected lesion mask, a re-run segmentation) — `overwrite=false` would then keep serving stale content silently forever.

This is closed by `src/retrieval/verify.py` (`verify_dataset(name, ds, subjects, config) -> VerificationResult`), a module shared by two callers rather than logic duplicated in each:

- `src/pipeline/retrieve_data.py` — `_retrieve_all` runs the copy phase for **every** requested dataset first (`_retrieve_dataset` in a loop), then, only once that loop has fully completed, runs a second loop calling `_verify_dataset_copies` per dataset. Verification is never interleaved with any dataset's copy phase — this was an explicit design choice (see lessons_learned pattern about aggregate vs per-item timing): copying dataset A must not be blocked or reordered by verification noise from dataset B, and the log's copy narrative for a run is always complete before its verification narrative begins.
- `scripts/verify_retrieval.py` — a standalone, read-only, on-demand re-check that calls the exact same `verify.verify_dataset`, without running a retrieval at all (see below).

`verify_dataset` re-resolves the source file for every `(subject, retrieve item)` the given `subjects` selection actually has (skipping ones where `resolve()` returns `None` — source doesn't have it either, not a verification concern, already covered by `stats.missing`), and for each one:
- if `data/` doesn't have the corresponding file at all → `VerificationResult.missing_locally` (a copy that silently failed to land — distinct from `stats.missing`, which means the *source* doesn't have it),
- if it does, compares `verify.sha256()` of source vs. local file → `VerificationResult.mismatched` on any difference,
- afterwards, walks every file actually present under the dataset's local root and flags any that isn't one of the paths just verified → `VerificationResult.unexpected_local_files` (stale naming, or a leftover from before the config or source changed).

`_verify_dataset_copies` copies these three lists onto `stats.mismatched` / `stats.missing_locally` / `stats.unexpected_local_files`, logging `mismatched`/`missing_locally` at `logging.error` (data corruption or drift, not a normal per-subject gap) and `unexpected_local_files` at `logging.warning`. `main()` additionally logs one aggregate `ERROR` line with the total mismatch+missing-locally count across all datasets right before the final "done" line, so it's impossible to miss in the console/log even when scrolling past a long per-subject narrative.

This makes the run itself self-verifying — no separate step needed to know the copies are byte-correct. `scripts/verify_retrieval.py` still exists as a standalone, on-demand re-check: useful when you want to re-verify `data/` against source *without* doing a run (e.g. after suspecting local disk corruption, or before starting analysis on data copied a while ago), since it doesn't require `overwrite=true` to re-touch anything — it only reads.

## Output layout

```
<output_root>/<project>/<dataset>/
├── participants.tsv                        # verbatim copy, only if include_tabular_data and present at source
└── <subject_id>/lesion/
    ├── native/<original filename>.nii.gz
    └── mni/<original filename>.nii.gz
```

Filenames are preserved exactly as at the source (no renaming/transformation) — this is a straight copy, not a derived product.

## Report (`copy_summary`)

Written to `reports/data_retrieval/<project>/copy_summary__<dd-mm-yy>__<hh-mm>.md` (fixed repo convention, like `data/`/`docs/`/`src/` — not itself in config, unlike `output_root`; the `copy_summary` prefix distinguishes it from the `dataset_matrix` report, see below). Title is `<project>_<dd-mm-yy>` with the run time as a subtitle; the file name keeps minute precision so multiple runs on the same day don't collide.

This report only explains what **this run** did and did or didn't find for the exact `(space, modality)` combinations in its `retrieve` list — it deliberately does not try to answer "what does this dataset have in general" (that's `dataset_matrix`, see below). Content, in order:
1. A verbatim JSON dump of the fields actually read from the config (derived from the parsed `RetrievalConfig`, not a re-read of the file, so it can't drift from what the run actually used — see `_config_summary`; `file_patterns` is shown as its configured path, not the full registry content).
2. The aggregate summary table per dataset: subjects selected, copied, skipped (exists), failed.
3. **Missing** — file not found for a specific subject, or an explicitly requested subject not present in that dataset.
4. **Ambiguous** — more than one registered file matched for a subject; the highest-priority one was used regardless.
5. **Non-conforming subject folders** — `sub-*` folders found on disk that don't match the expected naming convention, excluded from retrieval.
6. **Mismatched** — a local file's checksum doesn't match its current source (see checksum verification above) — the most severe entry, since it means the local copy is actually wrong, not just absent or ambiguous.
7. **Not copied despite source having it** — verification found the source file but `data/` doesn't have it (`stats.missing_locally`) — a copy that silently failed to land, distinct from section 3 (source itself lacking the file).
8. **Unexpected local files** — present under the dataset's local root but not the current resolution for any expected subject/modality (`stats.unexpected_local_files`) — stale naming, or a leftover from before the config or source changed.

Every section (3-8) is rendered as a title heading followed by a separate italic subtitle line with the explanation (`_section_header`) — kept apart so the heading itself stays scannable instead of one long line mixing the section name and its explanation. Sections 4-8 (Ambiguous, Non-conforming, Mismatched, Not-copied, Unexpected) share one body rendering (`_grouped_section`): grouped per dataset, a `<Section> Count = N` line per dataset, a `---` separator between datasets, `- none` if nothing to report anywhere. Section 3 (Missing) and the Ambiguous entries within section 4 additionally sub-group by `(space, modality)` within each dataset (`_grouped_by_modality_section`, see below) — everything else stays a flat per-dataset list. Never a list of successful copies — only anomalies.

`participants.tsv` has no dedicated status field or report column anymore - `_retrieve_participants` copies it through the same `_copy_one` path as any other file, so its outcome folds into the same `copied`/`skipped (exists)`/`failed` counts in the summary table. Whether a dataset has a `participants.tsv` at source at all is a `dataset_matrix` question, not this report's.

### Sub-grouping Missing/Ambiguous by `(space, modality)`

`config.retrieve` can list more than one `{space, modality}` pair in a single run (e.g. `native/T1w` and `mni/lesion_mask` together). Each entry `_retrieve_subject` appends to `stats.missing`/`stats.ambiguous` is a `ReportEntry(group, line)`, not a bare string — `group` is `f"{item.space}/{item.modality}"` for entries produced while resolving a specific retrieve item, or `""` for the one entry type that isn't tied to one (`_report_explicit_subjects_absent_from_dataset`'s "not present in this dataset" line).

`_grouped_by_modality_section` uses `group` to render each dataset's block as one sub-list per `(space, modality)`, each with its own `**space/modality** (n)` sub-heading, instead of interleaving every requested item's misses into one flat list per dataset — the more retrieve items a run asks for, the more this matters for readability. The dataset-level `Missing Count = N` / `Ambiguous Count = N` line still reports the dataset total across all sub-groups, unchanged.

A `Missing` line only states what this run looked for and didn't find (`"<dataset>: <subject_id> - no <space>/<modality>"`) — it does **not** say anything about whether the subject has data in some other space/modality. An earlier version of this report tried to answer that inline (a `has_any`-based "(in native not in mni)" suffix), but that comparison conflated things that aren't equivalent (e.g. having a `T1w` scan says nothing about whether a `lesion_roi` was ever segmented) and required deciding, for each modality, what its "counterpart" even is — a judgment call not derivable from `file_patterns.json` alone. That comparison is now the `dataset_matrix` report's job instead, done properly (one column per registered `(space, modality)`, not a collapsed native/mni binary) — see below.

## Dataset matrix report (`dataset_matrix`, `src/retrieval/matrix.py` + `scripts/dataset_matrix.py`)

A second, independent report answering "what does this dataset actually have, across everything we know how to look for" - as opposed to `copy_summary`, which only explains one run's gaps for the exact combinations it requested. Read-only, never copies or modifies anything; takes the same `data_retrieval.json` (for project/dataset/subject selection) and `file_patterns.json` (for which columns exist) a normal run would.

- `matrix.combinations_from_file_patterns(config)` — every `(space, modality)` pair registered in the project's `file_patterns.json`, `native` before `mni`, alphabetical within each — the matrix's columns, independent of what any particular run's `retrieve` list asks for.
- `matrix.build_matrix(ds, subjects, combinations)` — one `MatrixRow(subject_id, cells)` per subject; `cells["<space>/<modality>"]` is the resolved filename (via `Dataset.resolve()`) or the literal string `"missing"` (`matrix.MISSING_CELL`) if nothing matches.
- `matrix.count_present(rows, combinations)` — per-column count of non-missing cells, rendered as a `**present**` row at the bottom of each dataset's table. For a `(space, modality)` a `copy_summary` run actually requested, this count should reconcile with that run's `copied + skipped (exists)` for the same combination — a mismatch between the two reports means something changed on the source between the two runs, or a bug in one of them.

Written to `reports/data_retrieval/<project>/dataset_matrix__<dd-mm-yy>__<hh-mm>.md`, one table per requested dataset (subjects as rows, `(space, modality)` as columns), separated by `## <dataset name>` headings. No STOP/WARNING semantics here — it's a raw availability snapshot, not a run outcome.

## Log

`main()` writes the full narrative (skip/copied/warning/error lines, exactly as printed to console) to `logs/data_retrieval/<project>/copy_summary__<dd-mm-yy>__<hh-mm>.log` in addition to the console `StreamHandler` — the file is not a replacement for console output. The timestamp is shared with the report from the same run (`_write_report(config, stats, now)` reuses the `now` computed for the log path), so a report and its log always have the same file stem and can be matched by name. `dataset_matrix.py` writes no log (read-only, prints its report path to stdout).

The file handler is attached only once `config.project` is known (i.e. after `load_config` succeeds) — a config-load failure has nowhere to put a log file, so it only reaches the console. `_attach_file_handler` removes any `FileHandler` left on the root logger by a previous `main()` call in the same process before attaching a new one; without this, calling `main()` twice in one interpreter (e.g. a notebook) would keep writing the second run's lines into the first run's log file (see `test_main_does_not_leak_log_lines_across_runs`).

## Standalone accessory scripts

Neither of these is part of the pipeline entry point (`python -m src.pipeline.retrieve_data`); both are thin CLI wrappers around a `src/retrieval/` module, reusing `retrieve_data._select_subjects` for subject selection (imported directly — accessory scripts aren't a layered module, so reusing this rather than re-deriving it is the pragmatic choice).

**`scripts/verify_retrieval.py`** — on-demand, read-only re-check of `data/` against source, independent of running a retrieval. Calls the exact same `verify.verify_dataset` the pipeline's post-copy phase uses — no separate logic to keep in sync.

```bash
PYTHONPATH=. conda run -n nemesis python scripts/verify_retrieval.py --config config/data_retrieval.json
```

**`scripts/dataset_matrix.py`** — writes the `dataset_matrix` report described above.

```bash
PYTHONPATH=. conda run -n nemesis python scripts/dataset_matrix.py --config config/data_retrieval.json
```

## Testing

`tests/unit/` — synthetic fixtures in `tmp_path`, no EBRAIN mount required, run always (includes `test_matrix.py` for `src/retrieval/matrix.py`). `tests/integration/` — against the real mount and the real `config/file_patterns.json` registry, `pytest.mark.skipif` if unreachable.

Datasets on EBRAIN are actively curated (subjects and files are added over time - e.g. `UNIPD/WashU` gained a raw folder for a previously-orphaned derivative, and its own `participants.tsv`, between one working session and the next), so integration tests here never hardcode an exact expected count or a fixed "this dataset does/doesn't have X" fact — that would fail the moment the data legitimately changes, indistinguishable from a real code regression. Instead, counts are checked as a **differential**: `test_mni_mask_resolution_matches_raw_filesystem`/`test_native_t1w_resolution_matches_raw_filesystem` (`test_lesion_counts.py`) independently re-glob the real filesystem at test run time (bypassing `Dataset`/`file_patterns.json` entirely) and assert that set matches what `Dataset.resolve()` reports *right now* — a mismatch always means the resolution logic disagrees with reality at this exact moment, never a stale number. Per-dataset `participants.tsv` presence is similarly not asserted either way (`test_participants.py`); only that when present, it's well-formed. `EXPECTED_AVAILABLE_MODALITIES` is the one table still hardcoded — which *kinds* of native scans a dataset has is a stable protocol fact (adding subjects doesn't add new modality types), unlike a count. `test_no_ambiguous_matches_across_real_data` checks that no real subject today has files matching more than one registered `lesion_roi` variant simultaneously. Run with:

```bash
conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v
```
