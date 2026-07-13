# Data retrieval — technical reference

Audience: developers/agents working on `src/retrieval/` and `src/pipeline/retrieve_data.py`. For "how do I run this", see `docs/guides/retrieval.md`.

Scope today: 4 stroke datasets in `Clinical_connectome` (`UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`). NEMESIS_BIDS is a different source with a different layout (sessions, different subject-ID convention) and is **not** covered by this module — deliberately deferred, most likely a second class alongside `Dataset` when that work starts, not a speculative generalization of this one.

## The `object` axis

Everything in this module is organized around a top-level `object`: **`lesion`** (native/mni anatomical data — the only one actually wired into the pipeline today) and **`feature`** (derived per-subject data under a separate `features/` tree on the source — e.g. `func.motion`; registered in `file_patterns.json` but not yet requestable end-to-end, see below). `object` is a true structural invariant (`KNOWN_OBJECTS = ("lesion", "feature")` in `config.py`) — like `native`/`mni` used to be the fixed axis before `feature` existed, `object` is now that fixed axis, and everything below it (`space`, `modality`, or whatever a given object needs) is fully data-driven from `file_patterns.json`, not hardcoded.

Each object has its **own `project_root`** (`lesion` → `/data/corbetta/Clinical_connectome`, `feature` → `/data/corbetta/Clinical_connectome/features`) and its own on-disk shape below that root — `lesion` nests `space` (`native`/`mni`) then `modality`; `feature` nests directly to `modality`-equivalent keys (e.g. `func` → `motion`). Both happen to be 3 levels deep today (`object → X → modality`), which is why `RetrieveItem` still has exactly 3 fields (`object, space, modality`) — this is not assumed to hold forever; see "Extending to a new object" below.

## Module layout

```
config/
├── retrieval.json       # per-run request: which datasets, subjects, files, options
└── file_patterns.json   # registry: object -> ... -> modality -> filename template(s) - see below
src/retrieval/
├── config.py    # parsing/validation of both JSON files - no filesystem I/O
├── dataset.py   # Dataset class - resolves paths for one dataset, does touch the filesystem
├── verify.py    # post-copy checksum verification - shared by retrieve_data.py and scripts/verify_retrieval.py
└── matrix.py    # full per-subject data-availability matrix - shared by scripts/data_summary.py
src/pipeline/
└── retrieve_data.py   # CLI entry point: validate upfront, copy, verify, write the copy_summary report
scripts/
├── verify_retrieval.py   # accessory: standalone, on-demand re-check of data/ against source
└── data_summary.py       # accessory: standalone, read-only data_summary CSVs (see matrix.py)
```

Single-class design: **one** `Dataset` class is instantiated once per requested dataset name (`Dataset("UNIPD/WashU", file_patterns)` — no `project_root` argument, see below), not a subclass per dataset or per object. The 4 in-scope datasets share the same on-disk convention exactly; differences between them (which native modalities exist, presence of `participants.tsv`) are discovered from disk at runtime (`available()`), never hardcoded per dataset name.

### `Dataset` construction is lazy — no filesystem I/O at all

```python
def __init__(self, name: str, file_patterns: FilePatterns):
    self.name = name
    self.file_patterns = file_patterns
```

No root is resolved or checked at construction time. `_root_for(object_)` (`file_patterns.project_root_for(object_) / name`) is called lazily by every method that actually needs a root (`subjects()`, `resolve()`, `available()`, ...), and raises `FileNotFoundError` there if that object's root doesn't exist for this dataset. In practice a missing root still surfaces immediately in the CLI flow, since `_validate_upfront` always calls `subjects()`/`available()` for every requested dataset before any copying starts (see the STOP/WARNING matrix below) — construction just no longer needs to guess in advance which object(s) will actually be touched.

## The `file_patterns.json` registry — why it exists, and its shape

Originally, "where does a `(space, modality)` file live on disk" was hardcoded in `Dataset` as Python `glob()` calls. Two problems with that:

1. **Ambiguous glob matches.** The pattern for `lesion_roi` (`*_lesion_roi.nii.gz`) matches *both* real naming variants found across datasets (verified on real data: each dataset uses one variant consistently, never both for the same subject, but nothing in the code *guaranteed* that).
2. **Not inspectable.** The mapping was buried in Python string formatting — a non-programmer collaborator had no way to check "what file does this actually mean" without reading source code.

The registry (`config/file_patterns.json`) fixes both. Top level is `object`; each object maps its own `project_root` plus however many nested levels it needs down to an ordered list of path templates (relative to that object's `project_root`, with `{subject_id}` as the only placeholder — it already includes the `sub-` prefix, e.g. `sub-STUNIPD0002`, so templates must not add a second one):

```json
{
  "lesion": {
    "project_root": "/data/corbetta/Clinical_connectome",
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
  },
  "feature": {
    "project_root": "/data/corbetta/Clinical_connectome/features",
    "func": {
      "motion": ["{subject_id}/func/{subject_id}_desc-motion.tsv"]
    }
  }
}
```

Loaded by `config.load_file_patterns()` into a `FilePatterns` dataclass:

```python
@dataclass(frozen=True)
class FilePatterns:
    project_roots: dict[str, Path]              # object -> its project_root
    patterns: dict[tuple[str, ...], list[str]]   # (object, *path) -> templates
```

Accessors: `.project_root_for(object_)`, `.templates_for(object_, *path)` (raises `ValueError` if unregistered), `.has(object_, *path)`, `.combinations_for(object_)` (every full leaf key under that object, for `matrix.py`), `.all_object_spaces()` (every distinct `(object, space)` pair across the whole registry — used by `retrieve_data.py` for subject discovery, see below).

`load_file_patterns()` parses this generically via `_walk_patterns` — recursion, not a fixed 2-level assumption — so `lesion`'s `space → modality` (2 levels below object) and any future object's different depth are handled by the same code path. Each object entry requires a non-empty `project_root` string; every leaf list must be non-empty and every template must contain `{subject_id}`.

**No glob wildcards inside templates.** Since `{subject_id}` is substituted with the real subject ID before checking `Path.is_file()`, resolution is a plain existence check on an exact filename.

### Two ways to register naming variants — same key vs different key

If two filenames represent the *same logical thing*, named differently by different acquisition pipelines (this is the real, verified case for `lesion_roi` above), register both templates under the **same** key. If they represent two *genuinely different* things, register them under **different** modality names instead, so they can be requested independently and are never conflated. This is a domain decision made by whoever edits `file_patterns.json`, not something the code infers.

### `resolve()` returns every match — no priority, no ambiguity concept

```python
def resolve(self, subject_id: str, item: RetrieveItem) -> list[Path]:
```

Tries every registered template for `(item.object, item.space, item.modality)` and returns **all** that exist as real files — not "the first one, plus the rest flagged as ambiguous" (that mechanism, and the whole `Ambiguous` report section, existed in an earlier version of this module and was deliberately removed). If two naming variants of `lesion_roi` both exist for the same subject, both get copied. `[]` means the subject has none of them — this covers *both* "subject exists but lacks this file" and "subject doesn't exist at all in this object/space's container" identically; `resolve()` never validates subject existence separately (there used to be a `_require_subject` check — removed, since with per-space subject discovery (see below) "does this subject exist" is itself a `(object, space)`-relative question, not a single yes/no `resolve()` could answer up front). Raises `ValueError` only if `(object, space, modality)` isn't a registered combination *at all* — should never be reachable in the normal CLI flow, since `config._require_known_combinations` already rejects that at config-load time.

`Dataset.available(object_, space, modality)` mirrors this dataset-wide: true if *any* subject has a file matching *any* registered template for that combination. Used by upfront validation to reject a request a dataset can never satisfy, before any copying starts.

### Subject discovery is per `(object, space)`, derived from the templates — not one fixed root

This is the piece that fixes a real historical gap. `Dataset.subjects(object_, space, group=None)` doesn't glob a single hardcoded root — it derives **where subject folders live for this specific `(object, space)`** from the templates themselves:

```python
def _subject_container(self, object_: str, space: str) -> Path:
    combos = [c for c in self.file_patterns.combinations_for(object_) if c[1] == space]
    template = self.file_patterns.templates_for(*combos[0])[0]
    segments = template.split("/")
    subject_index = segments.index("{subject_id}")  # raises clearly if {subject_id} isn't its own segment
    root = self._root_for(object_)
    return root.joinpath(*segments[:subject_index]) if subject_index else root
```

For `lesion`/`native`, `{subject_id}` is the *first* path segment (`{subject_id}/anat/...`), so the container is the dataset root itself. For `lesion`/`mni`, `{subject_id}` sits *after* `derivatives/manual_masks/`, so the container is `<root>/derivatives/manual_masks/` — a different directory entirely. **Why this matters**: a real historical incident (see `.claude/stato_progetto.md`) found a subject whose mni derivative existed *before* their native folder was ever created — an "orphaned derivative". With the old design (`subjects()` always anchored to the native root, regardless of what was being requested), such a subject would have been structurally invisible to the entire pipeline — never discovered, never reported as missing anything, simply absent from every report. Deriving the container per `(object, space)` means a subject visible *only* in `derivatives/manual_masks/` is discovered exactly like any other, the moment `mni` is one of the spaces being looked at.

`non_conforming_subject_folders(object_, space)` uses the same container derivation.

## The STOP / WARNING / informational matrix

This is the core contract of the pipeline, enforced in `src/pipeline/retrieve_data.py`:

| category | cases | where enforced |
|---|---|---|
| 🛑 STOP — validated upfront, across **all** requested datasets, before any file is copied | `(object, space, modality)` not registered in `file_patterns.json` at all · modality not structurally present in a dataset · `group_filter` matches 0 subjects in a dataset · unknown explicit `subjects` entry · duplicate `(object, space, modality)` pair in `retrieve` · dataset root unreachable · invalid config | `_build_datasets`, `_validate_upfront` (`retrieve_data.py`), `load_config`, `_require_known_combinations` (`config.py`) |
| ⚠️ WARNING — logged, run continues | file missing for a specific subject · an explicitly requested subject not present in a specific requested dataset · a `sub-*` folder found on disk that doesn't match the expected subject naming (excluded from retrieval) · copy fails for a specific file (permissions, disk full, ...) · a local file no longer resolvable from any current source pattern | `_retrieve_subject`, `_report_explicit_subjects_absent_from_dataset`, `_report_non_conforming_subject_folders`, `_copy_one`, `verify._find_unexpected_local_files` |
| 🔴 ERROR — logged, run continues, but surfaced above WARNING (found only in the verification phase, after ALL datasets have finished copying) | local file's checksum doesn't match its current source · source has the file but `data/` doesn't (a copy that silently failed to land) | `_verify_dataset_copies` (`retrieve_data.py`), `verify.verify_dataset` (`src/retrieval/verify.py`) |
| ℹ️ informational | destination already exists: skipped (`overwrite=false`) or overwritten (`overwrite=true`) | `_copy_one`, `_retrieve_participants` |

There is no "Ambiguous" category anymore — see `resolve()` above.

`group_filter` is **not** validated (and not applied) when `config.subjects` is set explicitly (see `_validate_upfront`: skipped entirely when `subjects is not None`).

`_build_datasets` instantiates every requested `Dataset` (no I/O — see above); `_validate_upfront` is what actually touches disk, for every requested dataset, before any copying.

### Subject discovery is broadened across every space of a *requested* object

`config.retrieve` might request only `lesion/mni/lesion_mask`, but a subject who only has *native* data (no mni derivative yet — the common, expected case) must still show up in the run as a per-item "File not found: mni", not silently vanish from the report entirely. `retrieve_data._known_object_spaces(config)` computes this: every `(object, space)` the registry knows about, for any object `config.retrieve` touches — broader than the exact `(object, space)` pairs literally named in `retrieve`. `_discover_subjects` (used by `_select_subjects`, `_validate_group_filter`, `_validate_explicit_subjects`, `_report_non_conforming_subject_folders`) unions `ds.subjects(object_, space, group=...)` across that broadened set.

This is deliberately *not* scoped down to only `feature` objects/spaces the run doesn't touch — iterating every object registered in `file_patterns.json` regardless of relevance would call `_root_for("feature")` even for a run that never asked for `feature`, and could raise `FileNotFoundError` if that object's root doesn't happen to exist for a given dataset. Scoping to "every space of a *requested* object" avoids that while still fixing the visibility gap described above.

### Explicit `subjects` across multiple datasets

`_validate_explicit_subjects` checks that each requested subject exists (per the broadened discovery above) in **at least one** of the requested datasets. `_report_explicit_subjects_absent_from_dataset` reports, per dataset, any explicitly-named subject not found there specifically (`"<dataset>: <subject_id> - not present in this dataset"`, `group=""` since it isn't tied to one retrieve item) — distinct wording from a file-missing-for-a-known-subject miss. Duplicate IDs in `config.subjects` are deduplicated before this diff.

### Why `RetrieveItem` validates itself (`__post_init__`)

```python
@dataclass(frozen=True)
class RetrieveItem:
    object: str
    space: str
    modality: str

    def __post_init__(self) -> None:
        if self.object not in KNOWN_OBJECTS:
            raise ValueError(...)
```

Only `object` is validated here — it's the one true structural constant (see "The `object` axis" above). `space`/`modality` validity depends on the external `file_patterns.json` registry, which a dataclass can't reasonably depend on at construction time — cross-validated once in `load_config` via `_require_known_combinations`.

### Duplicate `retrieve` entries are rejected, not deduplicated

Two identical `{object, space, modality}` entries would make the pipeline process the same subject twice for the same file, showing up as `skipped_existing` the second time — indistinguishable in the report from a file genuinely already present from an earlier run. `_reject_duplicate_retrieve_items` (`config.py`) rejects this upfront.

## Config schema (`src/retrieval/config.py`)

`RetrievalConfig` fields: `output_root`, `project`, `file_patterns_path`, `file_patterns` (parsed `FilePatterns`), `datasets`, `group_filter`, `subjects`, `retrieve` (list of `RetrieveItem(object, space, modality)`), `include_tabular_data`, `overwrite`. **No `project_root` field** — each object's root now lives in `file_patterns.json` (see above), since `lesion` and `feature` live under genuinely different trees on the source. All required fields are validated with no silent defaults.

Known groups: `ST`, `HC`, `PD`, `GM`. Known objects: `lesion`, `feature` (`KNOWN_OBJECTS`). Known spaces/modalities: whatever is registered in `file_patterns.json` for a given object — not a static list in code.

### Checksum verification: a distinct phase, run only after every dataset has finished copying

`shutil.copy2` succeeding, or a destination already existing (`skipped (exists)`), used to be treated as proof the local file was correct. Neither actually is: a copy can be truncated by a disk-full mid-write without raising, and a file already present locally may have been copied from a source that has since changed upstream — `overwrite=false` would then keep serving stale content silently forever.

This is closed by `src/retrieval/verify.py` (`verify_dataset(name, ds, subjects, config) -> VerificationResult`), shared by two callers:

- `src/pipeline/retrieve_data.py` — `_retrieve_all` runs the copy phase for **every** requested dataset first, then, only once that loop has fully completed, runs a second loop calling `_verify_dataset_copies` per dataset. Never interleaved with any dataset's copy phase.
- `scripts/verify_retrieval.py` — a standalone, read-only, on-demand re-check that calls the exact same `verify.verify_dataset`, without running a retrieval at all.

`verify_dataset` re-resolves the source file(s) for every `(subject, retrieve item)` via `ds.resolve(subject_id, item)` (now a list — every existing match is verified, not just one), skipping items where `resolve()` returns `[]` (source doesn't have it either — covered by `stats.missing`, not a verification concern), and for each resolved path:
- if `data/` doesn't have the corresponding local file at all → `VerificationResult.missing_locally`,
- if it does, compares `verify.sha256()` of source vs. local file → `VerificationResult.mismatched` on any difference,
- afterwards, walks every file actually present under the dataset's local root and flags any that isn't one of the paths just verified → `VerificationResult.unexpected_local_files`.

`local_destination(config, dataset_name, subject_id, object_, space, filename)` now includes `object_` in the local path, matching `retrieve_data._destination_path`.

## Output layout

```
<output_root>/<project>/<dataset>/
├── participants.tsv                        # verbatim copy, only if include_tabular_data and present at source
└── <subject_id>/<object>/
    ├── native/<original filename>.nii.gz   # (object=lesion example)
    └── mni/<original filename>.nii.gz
```

`<object>` is whatever `RetrieveItem.object` was for that file (today always `lesion`) — no longer a hardcoded `"lesion"` string in `_destination_path`. Filenames are preserved exactly as at the source.

## Report (`copy_summary`)

Written to `reports/data_retrieval/<project>/copy_summary__<dd-mm-yy>__<hh-mm>.md` (the `copy_summary` prefix distinguishes it from the `data_summary` CSVs, see below). Title is `<project>_<dd-mm-yy>` with the run time as a subtitle.

This report only explains what **this run** did and did or didn't find for the exact `(object, space, modality)` combinations in its `retrieve` list — it deliberately does not try to answer "what does this dataset have in general" (that's `data_summary`). Content, in order:
1. A verbatim JSON dump of the fields actually read from the config (see `_config_summary`; `retrieve` items now include `object`).
2. The aggregate summary table per dataset: `copied`, `skipped (exists)`, `failed` (= `len(stats.failed)`) — no `subjects` column (`stats.subjects_selected` still exists internally, asserted by tests, just not rendered).
3. **Failed** — a file whose copy didn't complete correctly, with the reason (`OSError` message).
4. **File not found** — no registered file found for a specific subject, or an explicitly requested subject not present in that dataset.
5. **Non-conforming subject folders** — `sub-*` folders that don't match the expected naming convention, excluded from retrieval.
6. **Mismatched** — a local file's checksum doesn't match its current source — the most severe entry.
7. **Not copied despite source having it** — verification found the source file but `data/` doesn't have it (`stats.missing_locally`).
8. **Unexpected local files** — present locally but not the current resolution for any expected subject/modality.

Every section is a title heading followed by a separate italic subtitle line (`_section_header`). Sections 5-8 (Non-conforming, Mismatched, Not-copied, Unexpected) share one flat-list rendering (`_grouped_section`). Sections 3-4 (Failed, File not found) additionally sub-group by `(object, space, modality)` within each dataset (`_grouped_by_modality_section`) — see below. Never a list of successful copies — only anomalies.

`participants.tsv` has no dedicated status field anymore — `_retrieve_participants` copies it through the same `_copy_one` path as any other file, folding its outcome into `copied`/`skipped (exists)`/`failed` (and, on failure, into Failed, `group=""`).

### Sub-grouping Failed/File-not-found by `(object, space, modality)`

`config.retrieve` can list more than one `{object, space, modality}` triple in a single run. Each entry these two stats hold is a `ReportEntry(group, line)` — `group` is `f"{item.object}/{item.space}/{item.modality}"` for entries tied to a specific retrieve item, or `""` for the ones that aren't (`_report_explicit_subjects_absent_from_dataset`'s line; a failed `participants.tsv` copy). `_grouped_by_modality_section` renders each dataset's block as one sub-list per group, with its own `**object/space/modality** (n)` sub-heading — the dataset-level `<Section> Count = N` line still counts everything across sub-groups.

### Why a File-not-found line only ever says "empty folder" or "not found"

A `File not found` line (`"<dataset>: <subject_id> - no <object>/<space>/<modality> (<reason>)"`) does **not** say anything about whether the subject has data in some other object/space/modality — an earlier version tried this inline (a `has_any`-based cross-space suffix), but that conflated things that aren't equivalent (a `T1w` scan says nothing about whether `lesion_roi` was segmented) and required deciding, per modality, what its "counterpart" even is. That comparison is now `data_summary`'s job (one column per registered leaf combination, not a collapsed binary) — see below.

Instead, `Dataset.describe_absence(subject_id, item)` (called only once `resolve()` has already confirmed `[]`) checks the directory that would hold the highest-priority registered template:
- **"empty folder"** — the directory exists but has nothing in it at all (verified on real data: happens for `native` — e.g. 22/319 WashU subjects have a completely empty `anat/`).
- **"not found"** — every other case: the directory doesn't exist at all (verified: always the case for `mni` misses — `derivatives/manual_masks/<subject_id>/` is never pre-created, unlike `native/<subject_id>/anat/` which always exists even when empty), or it has other content but not this file.

## Data summary CSVs (`data_summary`, `src/retrieval/matrix.py` + `scripts/data_summary.py`)

A second, independent report answering "what does this dataset actually have, across everything we know how to look for" — as opposed to `copy_summary`, which only explains one run's gaps for the exact combinations it requested. Read-only; takes the same `retrieval.json`/`file_patterns.json` a normal run would.

- `matrix.combinations_from_file_patterns(config)` — every `(object, space, modality)` triple registered anywhere in the registry, across every known object, sorted — the matrix's columns. Assumes 3-level leaves (true for everything registered today); raises clearly if a future object registers a different depth, rather than silently mis-columning it.
- `matrix.select_all_subjects(ds, config)` — every subject visible in **any** `(object, space)` the registry knows about (`file_patterns.all_object_spaces()`), filtered by `group_filter`/`subjects` the same way a run would. Deliberately broader than `retrieve_data._select_subjects` (which only looks at what a run's `retrieve` list touches) — this script shows the full picture regardless of what's being retrieved.
- `matrix.build_matrix(ds, subjects, combinations)` — one `MatrixRow(subject_id, cells)` per subject; `cells["object/space/modality"]` is the first resolved filename or `matrix.MISSING_CELL`.
- `matrix.count_present(rows, combinations)` — per-column count of non-missing cells.
- `matrix.to_csv_rows(rows, combinations)` — header row, one row per subject (`matrix.PRESENT_CELL` `"-"` or `matrix.MISSING_CELL` `"missing"` per column — deliberately not the filename), trailing `"present"` row with totals. For a combination a `copy_summary` run actually requested, that count should reconcile with that run's `copied + skipped (exists)` — a mismatch means the source changed between runs, or a bug in one of them.

Written to `reports/data_retrieval/<project>/data_summary__<dataset with "/" replaced by "_">.csv` — one file per dataset (a `.csv` has no multi-sheet concept, unlike `.xlsx`), **not timestamped**: same fixed filename every time, overwritten on each call — a current snapshot, not a run log. No STOP/WARNING semantics — a raw availability snapshot, not a run outcome.

## Log

`main()` writes the full narrative to `logs/data_retrieval/<project>/copy_summary__<dd-mm-yy>__<hh-mm>.log`, timestamp-paired with the report. `data_summary.py` writes no log (read-only, prints each written CSV's path to stdout).

`_attach_file_handler` removes any `FileHandler` left on the root logger by a previous `main()` call in the same process before attaching a new one (see `test_main_does_not_leak_log_lines_across_runs`).

## Standalone accessory scripts

Neither is part of the pipeline entry point; both reuse `retrieve_data._select_subjects` or `matrix.select_all_subjects` directly (accessory scripts aren't a layered module).

**`scripts/verify_retrieval.py`** — on-demand, read-only re-check of `data/` against source. Calls the exact same `verify.verify_dataset` the pipeline's post-copy phase uses.

```bash
PYTHONPATH=. conda run -n nemesis python scripts/verify_retrieval.py --config config/retrieval.json
```

**`scripts/data_summary.py`** — writes the `data_summary` CSVs described above.

```bash
PYTHONPATH=. conda run -n nemesis python scripts/data_summary.py --config config/retrieval.json
```

## Testing

`tests/unit/` — synthetic fixtures in `tmp_path`, no EBRAIN mount required (includes `test_matrix.py`, `Dataset.describe_absence`/`resolve()`-returns-a-list cases in `test_dataset_lesion.py`). `tests/integration/` — against the real mount and the real `config/file_patterns.json` registry, `pytest.mark.skipif` if unreachable.

Datasets on EBRAIN are actively curated, so integration tests never hardcode an exact expected count — counts are checked as a **differential**: `test_mni_mask_resolution_matches_raw_filesystem`/`test_native_t1w_resolution_matches_raw_filesystem` (`test_lesion_counts.py`) independently re-glob the real filesystem at test run time and assert that set matches what `Dataset.resolve()` reports *right now*. `EXPECTED_AVAILABLE_MODALITIES` is the one table still hardcoded — which *kinds* of native scans a dataset has is a stable protocol fact, unlike a count. `test_no_subject_has_more_than_one_lesion_roi_naming_variant` (renamed from the old ambiguous-matching test, now purely a data-quality signal since there's no ambiguity mechanism left to regress) checks that no real subject has more than one `lesion_roi` naming variant simultaneously — if one ever does, `resolve()` now copies both rather than flagging it.

```bash
conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v
```

## Extending to a new object, or a deeper `feature`

Two situations, both deliberately deferred until actually needed rather than speculatively built now:

- **A new top-level `object`** (not `lesion` or `feature`): add it to `KNOWN_OBJECTS` in `config.py`, add its entry (with `project_root`) to `file_patterns.json`. `Dataset._root_for`/`_subject_container`, `resolve()`, `describe_absence()` all already work generically off the registry — no other code change needed, as long as the new object's registered leaves are 3 levels deep like `lesion`/`feature` today.
- **A `feature` leaf that needs more than 3 levels** (e.g. per-atlas FC matrices, which have `{atlas}` as a second filename placeholder beyond `{subject_id}` — real files already inspected under `Clinical_connectome/features/<dataset>/<subject>/func/*_atlas-<Name>.csv`): `RetrieveItem`'s fixed 3 fields, and `matrix.combinations_from_file_patterns`'s hard 3-level assumption, would both need generalizing at that point — not attempted here since the exact shape (one registry key per atlas vs. a second template placeholder) hasn't been decided yet.
