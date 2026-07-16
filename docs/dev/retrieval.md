# Data retrieval — technical reference

Audience: developers/agents working on `src/retrieval/` and `src/pipeline/retrieve_data.py`. For "how do I run this", see `docs/guides/retrieval.md`.

Scope today: 4 stroke datasets in `Clinical_connectome` (`UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`). NEMESIS_BIDS is a different source with a different layout (sessions, different subject-ID convention) and is **not** covered by this module — deliberately deferred, most likely a second class alongside `Dataset` when that work starts, not a speculative generalization of this one.

## The `object` axis, and why field *shape* varies by object

Everything in this module is organized around a top-level `object`: **`lesion`** and **`feature`** (`KNOWN_OBJECTS = ("lesion", "feature")` in `config.py` — a true structural invariant). Everything below it is fully data-driven from `file_patterns.json`, in BIDS-aligned vocabulary:

- **`pipeline`** — a BIDS-Derivatives pipeline name (e.g. `manual_masks`). BIDS itself does **not** define "pipeline" as a formal entity or term — verified against the spec (bids.neuroimaging.io/getting_started/folders_and_files/derivatives.html): the word appears once, purely descriptively ("Derivatives are outputs of (pre-)processing pipelines..."), and the `derivatives/<name>/` folder segment has no official designation. It's our own vocabulary choice for "which derivatives-style folder tree this comes from", not a borrowed formal term.
- **`datatype`** — BIDS-official content type: `anat` / `dwi` / `func`.
- **`suffix`** — the BIDS-official term for what earlier versions of this module (incorrectly) called `modality`. BIDS reserves "modality" for acquisition *technology* (MRI/PET/EEG/...), a different, higher-level concept this project doesn't need.

The critical design point: **`pipeline` is not present for every object**. `lesion` retrieves from a real BIDS-Derivatives pipeline (`manual_masks`) and requires it; `feature` has no discoverable pipeline name at all (`Clinical_connectome/features/` has no `dataset_description.json` anywhere, and isn't itself a BIDS-conformant `derivatives/` tree), so `pipeline` must be `None` for it — enforced, not just omitted:

```python
_OBJECTS_REQUIRING_PIPELINE = frozenset({"lesion"})
_OBJECTS_FORBIDDING_PIPELINE = frozenset({"feature"})
```

This means `lesion`'s leaves nest **3** levels below `object` (`pipeline → datatype → suffix`, e.g. `lesion.manual_masks.anat.lesion_mask`) while `feature`'s nest **2** (`datatype → suffix`, e.g. `feature.func.FC-pearson`) — depth genuinely varies by object, not a fixed number. `RetrieveItem.path_key()`/`RetrieveItem.from_path()` (`config.py`) are the single place that map between this variable-length tuple and typed fields — nothing else (`matrix.py` especially) re-derives the shape itself.

Each object also has its **own `project_root`** (`lesion` → `/data/corbetta/Clinical_connectome`, `feature` → `/data/corbetta/Clinical_connectome/features`), since they live under genuinely different trees on the source.

## Module layout

```
config/
├── retrieval.json       # per-run request: which datasets, subjects, files, options
└── file_patterns.json   # registry: object -> pipeline? -> datatype -> suffix -> filename template(s)
src/retrieval/
├── config.py          # parsing/validation of both JSON files - no filesystem I/O
├── dataset.py          # Dataset class - resolves paths for one dataset, does touch the filesystem
├── output_layout.py    # single source of truth for the LOCAL output path shape - shared by retrieve_data.py and verify.py
├── verify.py            # post-copy checksum verification - shared by retrieve_data.py and scripts/verify_retrieval.py
└── matrix.py            # full per-subject data-availability matrix - shared by scripts/data_summary.py
src/pipeline/
└── retrieve_data.py   # CLI entry point: validate upfront, copy, verify, write the copy_summary report
scripts/
├── verify_retrieval.py   # accessory: standalone, on-demand re-check of data/ against source
└── data_summary.py       # accessory: standalone, read-only data_summary CSVs (see matrix.py)
```

Single-class design: **one** `Dataset` class is instantiated once per requested dataset name (`Dataset("UNIPD/WashU", file_patterns)` — no `project_root` argument), not a subclass per dataset or per object. The 4 in-scope datasets share the same on-disk convention exactly; differences between them (which pipelines/leaves exist, presence of `participants.tsv`) are discovered from disk at runtime (`available()`, `has_object()`), never hardcoded per dataset name.

### `Dataset` construction is lazy — no filesystem I/O at all

```python
def __init__(self, name: str, file_patterns: FilePatterns):
    self.name = name
    self.file_patterns = file_patterns
```

No root is resolved or checked at construction time. `_root_for(object_)` (`file_patterns.project_root_for(object_) / name`) is called lazily by every method that actually needs a root (`subjects()`, `resolve()`, `available()`, ...), and raises `FileNotFoundError` there if that object's root doesn't exist for this dataset. `has_object(object_)` wraps that same check into a boolean for callers that need to check many objects at once without treating absence as fatal (see the WARNING case below).

## The `file_patterns.json` registry — why it exists, and its shape

Originally, "where does a file live on disk" was hardcoded in `Dataset` as Python `glob()` calls. Two problems with that:

1. **Ambiguous glob matches.** A loose pattern could match more than one real naming variant without anything *guaranteeing* it wouldn't.
2. **Not inspectable.** The mapping was buried in Python string formatting — a non-programmer collaborator had no way to check "what file does this actually mean" without reading source code.

The registry (`config/file_patterns.json`) fixes both. Top level is `object`; each object maps its own `project_root` plus however many nested levels it needs down to an ordered list of path templates (relative to that object's `project_root`, with `{subject_id}` as the only placeholder — it already includes the `sub-` prefix, e.g. `sub-STUNIPD0002`, so templates must not add a second one):

```json
{
  "lesion": {
    "project_root": "/data/corbetta/Clinical_connectome",
    "manual_masks": {
      "anat": {
        "lesion_mask": [
          "derivatives/manual_masks/{subject_id}/anat/{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
        ]
      }
    }
  },
  "feature": {
    "project_root": "/data/corbetta/Clinical_connectome/features",
    "func": {
      "FC-pearson": [
        "{subject_id}/func/{subject_id}_space-MNI152NLin6Asym_FC-pearson_atlas-Schaefer200TianS1Buckner7N.csv",
        "{subject_id}/func/{subject_id}_space-MNI152NLin6Asym_FC-pearson_atlas-Schaefer200TianS2Buckner7N.csv"
      ]
    }
  }
}
```

Note `lesion` nests one level deeper than `feature` (`manual_masks` between `project_root` and `anat`) — this isn't an oversight, it's `pipeline` being present for one object and absent for the other (see above).

Loaded by `config.load_file_patterns()` into a `FilePatterns` dataclass:

```python
@dataclass(frozen=True)
class FilePatterns:
    project_roots: dict[str, Path]              # object -> its project_root
    patterns: dict[tuple[str, ...], list[str]]   # (object, *path) -> templates
```

Accessors: `.project_root_for(object_)`, `.templates_for(object_, *path)` (raises `ValueError` if unregistered), `.has(object_, *path)`, `.combinations_for(object_)` (every full leaf key under that object, for `matrix.py`), `.subject_discovery_keys()` (every distinct `(object, pipeline)` pair across the whole registry, `pipeline` possibly `None` — used by `retrieve_data.py` and `matrix.py` for subject discovery, see below).

`load_file_patterns()` parses this generically via `_walk_patterns` — recursion, not a fixed-depth assumption — so `lesion`'s 3 levels and `feature`'s 2 (and any future object's different depth) are handled by the same code path. Each object entry requires a non-empty `project_root` string; every leaf list must be non-empty and every template must contain `{subject_id}`.

**No glob wildcards inside templates.** Since `{subject_id}` is substituted with the real subject ID before checking `Path.is_file()`, resolution is a plain existence check on an exact filename.

### Two different reasons for "more than one template under the same leaf key"

More than one template under the same leaf key means `resolve()` grabs **every one that exists** for a subject — but this mechanism serves two semantically distinct situations, both handled by the identical code path:

1. **Naming-variant alternates** — two filenames represent the *same logical thing*, named differently depending on which pipeline produced it (the historical, real case for the old `lesion_roi` leaf, before native retrieval was descoped this round — see below).
2. **Genuinely different, simultaneously-present files** — the current real case: the two `FC-pearson` templates above (`Schaefer200TianS1Buckner7N`, `Schaefer200TianS2Buckner7N`) are **not** alternate names for the same atlas — they are two different atlases' connectivity matrices that legitimately coexist for the same subject. `resolve()` correctly returns both, and both get copied — that's the desired behavior — but it's worth remembering this is "grab every registered file that exists", not "resolve ambiguity between spellings of one file".

Whether a given leaf's multiple templates mean (1) or (2) is a domain decision made by whoever edits `file_patterns.json`, not something the code infers or distinguishes.

### `resolve()` returns every match — no priority, no ambiguity concept

```python
def resolve(self, subject_id: str, item: RetrieveItem) -> list[Path]:
```

Tries every registered template for `item.path_key()` and returns **all** that exist as real files — not "the first one, plus the rest flagged as ambiguous" (that mechanism, and the whole `Ambiguous` report section, existed in an earlier version of this module and was deliberately removed). `[]` means the subject has none of them — this covers *both* "subject exists but lacks this file" and "subject doesn't exist at all in this object/pipeline's container" identically; `resolve()` never validates subject existence separately. Raises `ValueError` only if `item.path_key()` isn't a registered combination *at all* — should never be reachable in the normal CLI flow, since `config._require_known_combinations` already rejects that at config-load time.

`Dataset.available(item)` mirrors this dataset-wide: true if *any* subject has a file matching *any* registered template for `item.path_key()`. Used by upfront validation to reject a request a dataset can never satisfy, before any copying starts.

### Subject discovery is per `(object, pipeline)`, derived from the templates — not one fixed root

`Dataset.subjects(object_, pipeline, group=None)` doesn't glob a single hardcoded root — it derives **where subject folders live for this specific `(object, pipeline)`** from the templates themselves:

```python
def _subject_container(self, object_: str, pipeline: str | None) -> Path:
    combos = [c for c in self.file_patterns.combinations_for(object_) if RetrieveItem.from_path(*c).pipeline == pipeline]
    template = self.file_patterns.templates_for(*combos[0])[0]
    segments = template.split("/")
    subject_index = segments.index("{subject_id}")  # raises clearly if {subject_id} isn't its own segment
    root = self._root_for(object_)
    return root.joinpath(*segments[:subject_index]) if subject_index else root
```

For `lesion`/`manual_masks`, `{subject_id}` sits *after* `derivatives/manual_masks/`, so the container is `<root>/derivatives/manual_masks/`. For `feature` (no pipeline), `{subject_id}` is the *first* path segment, so the container is the object's root itself. **Why deriving this from the template (rather than assuming one fixed shape) matters**: a real historical incident (see `.claude/stato_progetto.md`) found a subject whose derivative existed *before* any raw folder was ever created for them — an "orphaned derivative". Deriving the container per `(object, pipeline)` means such a subject is discovered exactly like any other, the moment that pipeline is one of the ones being looked at — no assumption that every subject's data lives under one fixed root.

`non_conforming_subject_folders(object_, pipeline)` uses the same container derivation.

## The STOP / WARNING / informational matrix

This is the core contract of the pipeline, enforced in `src/pipeline/retrieve_data.py`:

| category | cases | where enforced |
|---|---|---|
| 🛑 STOP — validated upfront, across **all** requested datasets, before any file is copied | combination not registered in `file_patterns.json` at all · a dataset supports **none** of the requested `retrieve` items at all (every item's object is structurally absent — very likely the wrong dataset in `datasets`) · an item whose object **is** present still resolves to nothing anywhere for a dataset (a genuinely broken/misconfigured template) · `group_filter` matches 0 subjects in a dataset · unknown explicit `subjects` entry · duplicate retrieve item (same `path_key()`) · dataset root unreachable · invalid config | `_build_datasets`, `_validate_upfront`, `_validate_retrieve_items` (`retrieve_data.py`), `load_config`, `_require_known_combinations` (`config.py`) |
| ⚠️ WARNING — logged, run continues | **a retrieve item whose object a *specific dataset* structurally lacks entirely** (e.g. `feature` on a dataset with no `features/` tree at all) — skipped for that dataset only, every other dataset and item still runs · file missing for a specific subject · an explicitly requested subject not present in a specific requested dataset · a `sub-*` folder found on disk that doesn't match the expected subject naming (excluded from retrieval) · copy fails for a specific file (permissions, disk full, ...) · a local file no longer resolvable from any current source pattern | `_report_skipped_retrieve_items`, `_retrieve_subject`, `_report_explicit_subjects_absent_from_dataset`, `_report_non_conforming_subject_folders`, `_copy_one`, `verify._find_unexpected_local_files` |
| 🔴 ERROR — logged, run continues, but surfaced above WARNING (found only in the verification phase, after ALL datasets have finished copying) | local file's checksum doesn't match its current source · source has the file but `data/` doesn't (a copy that silently failed to land) | `_verify_dataset_copies` (`retrieve_data.py`), `verify.verify_dataset` (`src/retrieval/verify.py`) |
| ℹ️ informational | destination already exists: skipped (`overwrite=false`) or overwritten (`overwrite=true`) | `_copy_one`, `_retrieve_participants` |

The distinction between the first STOP case (object present but the item resolves nowhere) and the WARNING case (object entirely absent) matters and is deliberate: an item whose object doesn't exist for a dataset at all (e.g. `feature` on `UNIPD/PASPORT`, which has no `features/` tree) is a legitimate, expected per-dataset gap, not a config error — `Dataset.has_object()` already treats this as legitimate elsewhere (`src.retrieval.matrix.select_all_subjects`/`build_matrix` skip it the same way for the `data_summary` report). `_retrieve_items_for_dataset(ds, config)` filters `config.retrieve` down to items whose object `ds.has_object()` is true for, and every per-dataset consumer (`_known_object_pipelines`, `_validate_retrieve_items`, `_retrieve_subject`, `_report_non_conforming_subject_folders`) uses that filtered list instead of the raw `config.retrieve` — a single source of truth for "does this apply to this dataset", so the STOP-path and the copy-path never drift on the question independently. If a dataset supports **none** of the requested items at all, that's still a STOP (`_validate_retrieve_items`) — silently copying 0 subjects for an entire listed dataset would look like success when it's very likely a config mistake.

There is no "Ambiguous" category anymore — see `resolve()` above.

`group_filter` is **not** validated (and not applied) when `config.subjects` is set explicitly (see `_validate_upfront`: skipped entirely when `subjects is not None`).

`_build_datasets` instantiates every requested `Dataset` (no I/O — see above); `_validate_upfront` is what actually touches disk, for every requested dataset, before any copying.

### Subject discovery is scoped to exactly what `retrieve` asks for, and this dataset has

`retrieve_data._known_object_pipelines(ds, config)` returns exactly the `(object, pipeline)` pairs named in `_retrieve_items_for_dataset(ds, config)` — nothing broader, and already filtered to what this specific dataset structurally supports. `_discover_subjects` (used by `_select_subjects`, `_validate_group_filter`, `_validate_explicit_subjects`, `_report_non_conforming_subject_folders`) unions `ds.subjects(object_, pipeline, group=...)` across exactly that set.

A subject who only exists under some *other* object/pipeline not requested at all (e.g. only has a `feature` file, when this run only requests `lesion`) is not a member of this run at all: not selected, not counted in `subjects_selected`, and — the point of this design — **not reported as "File not found" either**. `copy_summary` only ever explains gaps for exactly what was asked for; the broader "what does this dataset have everywhere" picture is `data_summary`'s job (see below), not this report's.

### Explicit `subjects` across multiple datasets

`_validate_explicit_subjects` checks that each requested subject exists — in one of the exact `(object, pipeline)` pairs this run's `retrieve` list asks for and this dataset has, per `_known_object_pipelines` above — in **at least one** of the requested datasets. `_report_explicit_subjects_absent_from_dataset` reports, per dataset, any explicitly-named subject not found there specifically (`"<dataset>: <subject_id> - not present in this dataset"`, `group=""` since it isn't tied to one retrieve item) — distinct wording from a file-missing-for-a-known-subject miss. Duplicate IDs in `config.subjects` are deduplicated before this diff.

Note the consequence: if `config.subjects` explicitly names a subject who has zero presence in every requested `(object, pipeline)`, validation raises `"subjects not found"` for them — same as a genuine typo. This is intentional, not a special case to work around: for an explicitly-named subject, "not present in any requested pipeline" and "doesn't exist" are indistinguishable from this pipeline's perspective, and per `code_standards.md` §0 that should fail loudly rather than proceed silently. Use `group_filter` instead of explicit `subjects` when the goal is "show me every gap for this group", not a specific named subject.

### Why `RetrieveItem` validates itself (`__post_init__`)

```python
@dataclass(frozen=True)
class RetrieveItem:
    object: str
    pipeline: str | None
    datatype: str
    suffix: str

    def __post_init__(self) -> None:
        if self.object not in KNOWN_OBJECTS:
            raise ValueError(...)
        if self.object in _OBJECTS_REQUIRING_PIPELINE:
            if not self.pipeline:
                raise ValueError(...)
        elif self.object in _OBJECTS_FORBIDDING_PIPELINE:
            if self.pipeline is not None:
                raise ValueError(...)
        else:
            raise ValueError(...)  # no rule registered for this object - fail loudly, don't guess
        ...
```

`object` is the one true structural constant (see above). Whether `pipeline` is required or forbidden is *also* a static, per-object rule (`_OBJECTS_REQUIRING_PIPELINE`/`_OBJECTS_FORBIDDING_PIPELINE`), so it's validated here too — unlike `datatype`/`suffix`, whose *validity* depends on the external `file_patterns.json` registry and can't reasonably be checked at construction time (cross-validated once in `load_config` via `_require_known_combinations`). The explicit `if/elif/else: raise` (not a 2-branch `if/else`) means a 3rd object added to `KNOWN_OBJECTS` without updating the two pipeline-requirement sets fails loudly here, and a module-level `assert` at import time catches the same gap even earlier.

### Duplicate `retrieve` entries are rejected, not deduplicated

Two identical entries (same `path_key()`) would make the pipeline process the same subject twice for the same file, showing up as `skipped_existing` the second time — indistinguishable in the report from a file genuinely already present from an earlier run. `_reject_duplicate_retrieve_items` (`config.py`) rejects this upfront.

## Config schema (`src/retrieval/config.py`)

`RetrievalConfig` fields: `output_root`, `project`, `file_patterns_path`, `file_patterns` (parsed `FilePatterns`), `datasets`, `group_filter`, `subjects`, `retrieve` (list of `RetrieveItem(object, pipeline, datatype, suffix)`), `include_tabular_data`, `overwrite`. **No `project_root` field** — each object's root lives in `file_patterns.json` (see above), since `lesion` and `feature` live under genuinely different trees on the source. All required fields are validated with no silent defaults.

Known groups: `ST`, `HC`, `PD`, `GM`. Known objects: `lesion`, `feature` (`KNOWN_OBJECTS`). Whether `pipeline` is required or forbidden per object: `_OBJECTS_REQUIRING_PIPELINE`/`_OBJECTS_FORBIDDING_PIPELINE`. Known `datatype`/`suffix` values: whatever is registered in `file_patterns.json` for a given object — not a static list in code.

### Checksum verification: a distinct phase, run only after every dataset has finished copying

`shutil.copy2` succeeding, or a destination already existing (`skipped (exists)`), used to be treated as proof the local file was correct. Neither actually is: a copy can be truncated by a disk-full mid-write without raising, and a file already present locally may have been copied from a source that has since changed upstream — `overwrite=false` would then keep serving stale content silently forever.

This is closed by `src/retrieval/verify.py` (`verify_dataset(name, ds, subjects, config) -> VerificationResult`), shared by two callers:

- `src/pipeline/retrieve_data.py` — `_retrieve_all` runs the copy phase for **every** requested dataset first, then, only once that loop has fully completed, runs a second loop calling `_verify_dataset_copies` per dataset. Never interleaved with any dataset's copy phase.
- `scripts/verify_retrieval.py` — a standalone, read-only, on-demand re-check that calls the exact same `verify.verify_dataset`, without running a retrieval at all.

`verify_dataset` re-resolves the source file(s) for every `(subject, retrieve item)` via `ds.resolve(subject_id, item)`, skipping items whose object this dataset structurally lacks (`ds.has_object(item.object)` false — the same items `_report_skipped_retrieve_items` already skipped at copy time, so they were never expected to land locally either) and items where `resolve()` returns `[]` (source doesn't have it either — covered by `stats.missing`, not a verification concern), and for each remaining resolved path:
- if `data/` doesn't have the corresponding local file at all → `VerificationResult.missing_locally`,
- if it does, compares `verify.sha256()` of source vs. local file → `VerificationResult.mismatched` on any difference,
- afterwards, walks every file actually present under the dataset's local root and flags any that isn't one of the paths just verified → `VerificationResult.unexpected_local_files`.

## Output layout

```
<output_root>/<project>/<dataset>/
├── participants.tsv                              # verbatim copy, only if include_tabular_data and present at source
└── <subject_id>/
    ├── lesion/manual_masks/anat/<filename>       # object with a pipeline: one extra directory level
    └── feature/func/<filename>                   # object without a pipeline: no extra level
```

Both shapes come out of the same single-source-of-truth function, **`output_layout.local_relative_path(item, filename)`** — `item.path_key()` minus its trailing `suffix` element (`suffix` identifies *which* file, not a folder level). `retrieve_data._destination_path` and `verify.local_destination` both delegate to it, so the copy phase and the verification phase can never independently drift on where a file is supposed to land — a real duplication that existed before this round (`_destination_path` and `local_destination` each had their own copy of the same layout logic) and was deliberately collapsed into one function as part of this refactor. Filenames are preserved exactly as at the source.

## Report (`copy_summary`)

Written to `reports/data_retrieval/<project>/copy_summary__<dd-mm-yy>__<hh-mm>.md` (the `copy_summary` prefix distinguishes it from the `data_summary` CSVs, see below). Title is `<project>_<dd-mm-yy>` with the run time as a subtitle.

This report only explains what **this run** did and did or didn't find for the exact combinations in its `retrieve` list — it deliberately does not try to answer "what does this dataset have in general" (that's `data_summary`). Content, in order:
1. A verbatim JSON dump of the fields actually read from the config (see `_config_summary`; each `retrieve` item now dumps `object`/`pipeline`/`datatype`/`suffix`, with `pipeline: null` shown explicitly for objects that don't use one — honest about the field's absence-by-design, not omitted).
2. The aggregate summary table per dataset: `copied`, `skipped (exists)`, `failed` (= `len(stats.failed)`, data files only — `participants.tsv` is metadata, not one of the requested `retrieve` items, and is deliberately excluded from these counts), `participants.tsv` (`stats.participants_outcome`, one of `copied`/`skipped (exists)`/`failed`/`—`) — no `subjects` column (`stats.subjects_selected` still exists internally, asserted by tests, just not rendered).
3. **Failed** — a file whose copy didn't complete correctly, with the reason (`OSError` message).
4. **File not found** — no registered file found for a specific subject, or an explicitly requested subject not present in that dataset.
5. **Skipped — object not present in this dataset** — a retrieve item WARNING-skipped for this dataset only (see the STOP/WARNING matrix above). Not an error; expected whenever a dataset structurally lacks an object a run also requests for other datasets.
6. **Non-conforming subject folders** — `sub-*` folders that don't match the expected naming convention, excluded from retrieval.
7. **Mismatched** — a local file's checksum doesn't match its current source — the most severe entry.
8. **Not copied despite source having it** — verification found the source file but `data/` doesn't have it (`stats.missing_locally`).
9. **Unexpected local files** — present locally but not the current resolution for any expected subject/retrieve item.

Every section is a title heading followed by a separate italic subtitle line (`_section_header`). Sections 5-9 share one flat-list rendering (`_grouped_section`). Sections 3-4 (Failed, File not found) additionally sub-group by `path_key()` within each dataset (`_grouped_by_modality_section`) — see below. Never a list of successful copies — only anomalies.

`participants.tsv` goes through the same `_copy_one` path as any other file, but tagged `is_participants=True` — its outcome lands in `DatasetStats.participants_outcome` (`"copied"` / `"skipped (exists)"` / `"failed"` / `None` if never attempted), rendered as its own column in the summary table, and **not** folded into `copied`/`skipped_existing` (a real bug found after this round's first production run: those counts came out off-by-one against the true number of data files, e.g. 203 "copied" for 202 real WashU manual_masks subjects — the +1 was `participants.tsv`). A failed `participants.tsv` copy still lands in the shared `Failed` section too, `group=""`, so it's still visible there even though it's excluded from the numeric counts.

### Sub-grouping Failed/File-not-found by retrieve item

`config.retrieve` can list more than one item in a single run. Each entry these two stats hold is a `ReportEntry(group, line)` — `group` is `"/".join(item.path_key())` for entries tied to a specific retrieve item, or `""` for the ones that aren't (`_report_explicit_subjects_absent_from_dataset`'s line; a failed `participants.tsv` copy). `_grouped_by_modality_section` renders each dataset's block as one sub-list per group, with its own `**object/pipeline?/datatype/suffix** (n)` sub-heading — the dataset-level `<Section> Count = N` line still counts everything across sub-groups.

### Why a File-not-found line only ever says "empty folder" or "not found"

A `File not found` line (`"<dataset>: <subject_id> - no <path_key joined by '/'> (<reason>)"`) does **not** say anything about whether the subject has data under some other retrieve item — that comparison is `data_summary`'s job (one column per registered leaf combination, not a collapsed binary) — see below.

Instead, `Dataset.describe_absence(subject_id, item)` (called only once `resolve()` has already confirmed `[]`) checks the directory that would hold the highest-priority registered template:
- **"empty folder"** — the directory exists but has nothing in it at all.
- **"not found"** — every other case: the directory doesn't exist at all, or it has other content but not this file.

## Data summary CSVs (`data_summary`, `src/retrieval/matrix.py` + `scripts/data_summary.py`)

A second, independent report answering "what does this dataset actually have, across everything we know how to look for" — as opposed to `copy_summary`, which only explains one run's gaps for the exact combinations it requested. Read-only; takes the same `retrieval.json`/`file_patterns.json` a normal run would.

- `matrix.combinations_from_file_patterns(config)` — every leaf combination registered anywhere in the registry, across every known object, sorted — the matrix's columns. Depth varies by object (see above); shape validated via `RetrieveItem.from_path()` for each combo (single source of truth, not an ad hoc depth check).
- `matrix.select_all_subjects(ds, config)` — every subject visible in **any** `(object, pipeline)` the registry knows about (`file_patterns.subject_discovery_keys()`), filtered by `group_filter`/`subjects` the same way a run would. Deliberately broader than `retrieve_data._select_subjects` (which only looks at what a run's `retrieve` list touches) — this script shows the full picture regardless of what's being retrieved. Skips objects a dataset structurally lacks (`ds.has_object`) rather than raising.
- `matrix.build_matrix(ds, subjects, combinations)` — one `MatrixRow(subject_id, cells)` per subject; `cells["/".join(combo)]` is the first resolved filename or `matrix.MISSING_CELL`.
- `matrix.to_csv_rows(rows, combinations)` — header row, one row per subject (`matrix.PRESENT_CELL` `"present"` or `matrix.MISSING_CELL` `"missing"` per column — deliberately not the filename). No aggregate rows: per-column present/missing totals are computed separately, outside this module (e.g. in a notebook, from the written CSV).

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

`tests/unit/` — synthetic fixtures in `tmp_path`, no EBRAIN mount required. `tests/integration/` — against the real mount and the real `config/file_patterns.json` registry, `pytest.mark.skipif` if unreachable.

Datasets on EBRAIN are actively curated, so integration tests never hardcode an exact expected count — counts are checked as a **differential**: `test_manual_masks_lesion_mask_resolution_matches_raw_filesystem`/`test_feature_fc_pearson_resolution_matches_raw_filesystem` (`test_resolution_counts.py`) independently re-glob the real filesystem at test run time and assert that set matches what `Dataset.resolve()` reports *right now*. `test_subjects_with_both_fc_pearson_atlases_get_both_files` checks the "2 genuinely different simultaneous files" nuance specifically: a real subject known (via glob, not hardcoded) to have both Schaefer200 atlas variants must resolve to exactly 2 paths.

```bash
conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v
```

## This round vs. a future native/raw round

This refactor deliberately covers only `lesion`/`manual_masks` (derivatives) and `feature`/`FC-pearson` (2 of ~30 available atlas templates) — **native/raw BIDS data is fully descoped**, for concrete reasons found while surveying the real EBRAIN mount:

- func run-naming differs per dataset (WashU: `task-rest_run-01..07_bold`, 0-14 runs/subject; UKLFR: single `task-rest_bold`, no `run` entity at all).
- dwi has 5 acquisition variants for WashU (`acq-b1000_dir-AP`, `acq-b2000_dir-AP`, `acq-b300_dir-AP`, `acq-b300_dir-PA`, plain) vs. a single plain file for UKLFR.
- PASPORT/PSP have zero raw dwi/func at all (anat only).
- PSP has no raw `lesion_roi` at all (only PASPORT/WashU/UKLFR do, with 2 different naming conventions between them).

None of this complexity was worth generalizing into `file_patterns.json` speculatively. Adding native/raw retrieval in a future round means: registering `pipeline: "raw"` leaves per datatype/suffix (literal per-dataset templates, same "enumerate what's real" approach used for `FC-pearson`'s 2 atlases here — no new code needed, `resolve()`/`_walk_patterns` are already depth- and content-agnostic), and deciding per-dataset which combinations are even registered (a dataset with zero dwi files simply gets no `lesion.raw.dwi.*` entries, rather than being registered-but-always-empty).

Extending to a **new top-level `object`** (not `lesion`/`feature`) at that point: add it to `KNOWN_OBJECTS`, add it to exactly one of `_OBJECTS_REQUIRING_PIPELINE`/`_OBJECTS_FORBIDDING_PIPELINE`, add its entry (with `project_root`) to `file_patterns.json`. `Dataset._root_for`/`_subject_container`, `resolve()`, `describe_absence()`, `RetrieveItem.path_key()`/`from_path()` all already work generically off the registry and the two pipeline-requirement sets — no other code change needed.
