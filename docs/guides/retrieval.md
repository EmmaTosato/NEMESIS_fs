# Data retrieval — user guide

Copies lesion masks and functional-connectivity features (and, optionally, the clinical/demographic table) from the EBRAIN-mounted `Clinical_connectome` source into this project's local `data/` folder, driven by a single JSON config. Covers the 4 in-scope stroke datasets: `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`.

## How to run

```bash
conda activate nemesis
python -m src.pipeline.retrieve_data --config config/retrieval.json
```

One required argument, `--config`. Everything else — which datasets, which files, where to put them — is in the JSON file.

## Writing the config

Two things to decide: **which files** (`retrieve`) and **which subjects** (`group_filter` / `subjects`).

### The real, current config — `config/retrieval.json`

```json
{
  "output_root": "data/",
  "project": "clinical_connectome",
  "file_patterns": "config/file_patterns.json",
  "datasets": ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"],
  "group_filter": ["ST"],
  "subjects": null,
  "retrieve": [
    { "object": "lesion", "pipeline": "manual_masks", "datatype": "anat", "suffix": "lesion_mask" },
    { "object": "feature", "datatype": "func", "suffix": "FC-pearson" }
  ],
  "include_tabular_data": true,
  "overwrite": false
}
```

This is the exact starting point to copy-paste from and adapt — both examples below are variations on it.

### Example — only the lesion masks, no features

```json
{
  "output_root": "data/",
  "project": "clinical_connectome",
  "file_patterns": "config/file_patterns.json",
  "datasets": ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"],
  "group_filter": ["ST"],
  "subjects": null,
  "retrieve": [
    { "object": "lesion", "pipeline": "manual_masks", "datatype": "anat", "suffix": "lesion_mask" }
  ],
  "include_tabular_data": true,
  "overwrite": false
}
```

### Example — only functional-connectivity features, 2 specific subjects

```json
{
  "output_root": "data/",
  "project": "clinical_connectome",
  "file_patterns": "config/file_patterns.json",
  "datasets": ["UNIPD/WashU"],
  "group_filter": null,
  "subjects": ["sub-STUNIPD0002", "sub-STUNIPD0003"],
  "retrieve": [
    { "object": "feature", "datatype": "func", "suffix": "FC-pearson" }
  ],
  "include_tabular_data": false,
  "overwrite": false
}
```

### Field reference

| field | meaning |
|---|---|
| `output_root` | where copied files land locally (usually `"data/"`) |
| `project` | name used in the local folder layout |
| `file_patterns` | path to the registry file that says which real filename corresponds to each entry in `retrieve`, and where each `object`'s data actually lives on the source (see below) — normally leave it as `"config/file_patterns.json"` |
| `datasets` | which of the 4 datasets to include (`"UNIPD/WashU"` etc.) |
| `group_filter` | `["ST"]`, `["HC"]`, both, or `null` for everyone. Ignored entirely if `subjects` is set. |
| `subjects` | `null` for everyone (subject to `group_filter`), or an exact list of subject IDs to retrieve — bypasses `group_filter` |
| `retrieve` | list of items to copy — see "Writing `retrieve` items" below |
| `include_tabular_data` | copy `participants.tsv` too, when the dataset has one |
| `overwrite` | `false` (default, recommended): skip files that already exist locally. `true`: re-copy and replace them |

No `project_root` field — each `object` has its own source root, declared in `config/file_patterns.json` instead, since `lesion` and `feature` live under different directory trees on the source.

## Writing `retrieve` items

Each entry in `retrieve` is one thing to copy, described in BIDS-aligned vocabulary. **The set of fields is not the same for every `object`** — this is the one thing to get right:

| field | meaning | required for `lesion`? | required for `feature`? |
|---|---|---|---|
| `object` | `"lesion"` or `"feature"` — which data family | always | always |
| `pipeline` | which BIDS-Derivatives pipeline produced it (today, always `"manual_masks"`) | **yes** | **must be omitted entirely** |
| `datatype` | BIDS content type: `"anat"`, `"dwi"`, or `"func"` | always | always |
| `suffix` | which specific file — BIDS calls this "suffix" (not "modality" — BIDS reserves "modality" for the acquisition technology, e.g. MRI vs. PET, a different concept this project doesn't use) | always | always |

If you set `pipeline` on a `feature` entry, or omit it on a `lesion` entry, the config fails to load with a clear error — this is checked before anything is copied, not silently ignored. Why `feature` has no `pipeline`: `Clinical_connectome/features/` has no `dataset_description.json` anywhere and isn't itself a BIDS `derivatives/` tree, so there's no real pipeline name to put there.

The two exact items usable today (copy-paste from `config/retrieval.json` above):

```json
{ "object": "lesion", "pipeline": "manual_masks", "datatype": "anat", "suffix": "lesion_mask" }
```
The normalized (MNI-space) lesion mask — available on all 4 datasets.

```json
{ "object": "feature", "datatype": "func", "suffix": "FC-pearson" }
```
Functional-connectivity matrices for 2 atlases (`Schaefer200TianS1Buckner7N`, `Schaefer200TianS2Buckner7N`) — **`UNIPD/WashU` only**, see the availability table below. More atlases (and other feature types like `ALFF`/`ReHo`/motion/QC metrics) are registered incrementally in `config/file_patterns.json` as they're needed — ask before assuming one exists.

### Availability per dataset

| dataset | `lesion`/`manual_masks`/`lesion_mask` | `feature`/`FC-pearson` |
|---|:-:|:-:|
| UNIPD/WashU | yes | yes |
| UNIPD/PASPORT | yes | **no — no `features/` tree at all** |
| UNIPD/PSP | yes | **no — no `features/` tree at all** |
| UKLFR/stroke_UKLFR | yes | **no — no `features/` tree at all** |

Asking for a combination not registered in `file_patterns.json` at all stops the whole run before anything is copied, with a clear error. But asking for `feature`/`FC-pearson` while `datasets` includes PASPORT/PSP/UKLFR does **not** stop the run — see "A dataset entirely missing an object" below, this is the one case handled as a warning instead.

Listing the same entry twice in `retrieve` is rejected upfront (not deduplicated) — otherwise the second copy would misleadingly look like it already existed from a previous run.

## Where `retrieve` items actually point to: `config/file_patterns.json`

Each item maps to one or more filename templates, registered in plain JSON — not hidden in Python:

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

Read the `lesion` entry as: "for `pipeline=manual_masks`/`datatype=anat`/`suffix=lesion_mask`, look for `derivatives/manual_masks/<subject_id>/anat/<subject_id>_space-MNI152NLin6Asym_label-lesion_mask.nii.gz` inside the `lesion` object's project root + dataset folder". Note `lesion` nests one level deeper than `feature` (the `manual_masks` pipeline level) — that's `pipeline` being present for one object and absent for the other, not a mistake.

If a naming convention changes or a new one appears, edit this file, not the Python code.

### What happens if a subject has more than one matching file?

If a subject has files matching more than one registered template for the same item, **all of them get copied** — there's no "pick one and flag the rest" step. This happens for two different reasons, both handled identically:
- Two filenames are alternate spellings of the *same* file (different naming conventions from different acquisition pipelines) — not currently the case for anything registered today.
- Two filenames are genuinely *different* files that legitimately coexist — this **is** the case for `FC-pearson` above: a subject with both atlas variants on disk gets both CSVs copied, because both are real, independently useful files, not duplicates of each other.

If that's ever surprising, check `data/` by hand for that subject.

### Where are HC (healthy controls)?

Only `UNIPD/WashU` has healthy controls (68 of them) alongside its stroke subjects, embedded in the same dataset — useful as a reference cohort. The other 3 datasets are 100% stroke (`ST`). Use `"group_filter": ["HC"]` to get only those.

### Explicit `subjects` spanning more than one dataset

If `subjects` lists people from more than one of the requested `datasets`, each dataset only retrieves the ones it actually has (subject IDs already identify their dataset, e.g. `sub-STUNIPD...` vs `sub-STUKLFR...`). If you list a subject that isn't in a particular requested dataset, that dataset's entry in the report's "File not found" section will say so explicitly (`"<dataset>: <subject_id> - not present in this dataset"`) rather than staying silent about it.

### If a subject folder doesn't follow the naming convention

Subject folders are expected to be named `sub-<DISEASE><SITE>[HC]<NUM>` (e.g. `sub-STUNIPD0002`). A `sub-*` folder that doesn't match (leftover test/QC folder, etc.) is never treated as a subject or copied — it's listed by name in the report's **Non-conforming subject folders** section instead.

### A dataset entirely missing an object — expected, not a bug

`config/retrieval.json`'s `datasets` lists all 4 datasets, but `feature`/`FC-pearson` only exists for WashU. Rather than stopping the whole run over that, PASPORT/PSP/UKLFR each get a **Skipped — object not present in this dataset** entry in the report for the `feature` item, and continue normally for `lesion`/`manual_masks`. If you see this for `feature` on those 3 datasets, that's expected, not something to fix. It would only be worth investigating if it showed up for `lesion`/`manual_masks` (which really is registered everywhere) or for `feature` on WashU itself.

## What you get in `data/`

```
data/clinical_connectome/UNIPD/WashU/
├── participants.tsv                                              (skipped for WashU - it doesn't have one at the source)
└── sub-STUNIPD0002/
    ├── lesion/manual_masks/anat/sub-STUNIPD0002_space-MNI152NLin6Asym_label-lesion_mask.nii.gz
    └── feature/func/
        ├── sub-STUNIPD0002_space-MNI152NLin6Asym_FC-pearson_atlas-Schaefer200TianS1Buckner7N.csv
        └── sub-STUNIPD0002_space-MNI152NLin6Asym_FC-pearson_atlas-Schaefer200TianS2Buckner7N.csv
```

Note `lesion/manual_masks/anat/...` (one extra folder level, for the `pipeline`) vs. `feature/func/...` (no `pipeline` level) — the folder depth mirrors whether that `object` uses a pipeline (see "Writing `retrieve` items" above). Filenames are exactly as at the source — nothing renamed or transformed.

## After running: inspecting the output

1. **Open the report** — `reports/data_retrieval/clinical_connectome/copy_summary__<dd-mm-yy>__<hh-mm>.md`. Check the summary table first, then the sections below it for anything flagged (Failed, File not found, Skipped, Non-conforming, Mismatched, ...).
2. **Need more detail on a flagged item?** Open the matching log — `logs/data_retrieval/clinical_connectome/copy_summary__<dd-mm-yy>__<hh-mm>.log` (same filename stem as the report, so it's always easy to find). It has the full file-by-file narrative, in the order things happened.
3. **Want the full picture of what a dataset has, not just this run's gaps?** See [Data summary CSVs](#data-summary-csvs-the-full-picture) below.
4. **Optional — re-verify `data/` later without a new run**: `scripts/verify_retrieval.py` (see below) re-checks everything currently in `data/` against source, read-only. Useful before starting analysis on data fetched a while ago, or if you suspect local disk issues.

### The report

Every run writes the report above — starting with the config actually used (so you can always tell which settings produced it — note `"pipeline": null` shown explicitly for the `feature` item, not omitted, since that's a deliberate fact about that item, not a missing value), then a summary table (copied, skipped (exists), failed, participants.tsv - per dataset; the `copied`/`skipped (exists)`/`failed` columns count data files only - lesion masks and feature CSVs - `participants.tsv` is metadata and gets its own column instead of inflating those counts by one), then sections listing anything worth a second look, each a title heading with an explanation on the line right below it, grouped by dataset with a count.

This report only explains **this run**: what it looked for (`retrieve`) and what it did or didn't find. It does not say anything about whether a subject has other data your `retrieve` list didn't ask about - for that, see [Data summary CSVs](#data-summary-csvs-the-full-picture) below.

- **Failed** — a file whose copy didn't complete correctly, with the reason (e.g. permissions, disk full).
- **File not found** — no registered file found for a specific subject, or an explicitly requested subject not present in that dataset. Each line ends with `(empty folder)` - the directory that would hold the file exists but has nothing in it - or `(not found)` - every other case (the directory doesn't exist at all, or has other content but not this file). Scoped strictly to the retrieve items in `retrieve`, and only for datasets that actually have that item's object: a subject who only exists under a *different* object/pipeline your config didn't ask for isn't a member of this run at all and won't appear here - see [Data summary CSVs](#data-summary-csvs-the-full-picture) for that broader picture.
- **Skipped — object not present in this dataset** — a retrieve item whose object a specific dataset structurally lacks entirely (see "A dataset entirely missing an object" above). Not an error.
- **Non-conforming subject folders** — folders that don't follow the naming convention, excluded from retrieval.
- **Mismatched** — a local file's content no longer matches its current source (see below).
- **Not copied despite source having it** — verification found the source file, but `data/` doesn't have it; a copy that silently failed to land.
- **Unexpected local files** — present in `data/` but not the current resolution for any expected subject/retrieve item (stale naming, or a leftover from before the config or source changed).

If `retrieve` asks for more than one item, the Failed/File-not-found entries in each section are split into one sub-list per requested item (`**lesion/manual_masks/anat/lesion_mask** (12)`, `**feature/func/FC-pearson** (5)`, ...) instead of being mixed together — the section's overall count still counts everything.

The last four sections are also logged at ERROR/WARNING level, with an aggregate count line right before "done". Never a list of successful copies — just the exceptions worth looking at.

### Data summary CSVs: the full picture

`copy_summary` only tells you about the exact combinations a given run's `retrieve` asked for. To see everything a dataset has - every registered leaf, for every subject, at once - run the separate, read-only summary:

```bash
PYTHONPATH=. conda run -n nemesis python scripts/data_summary.py --config config/retrieval.json
```

Writes one CSV per dataset - `reports/data_retrieval/clinical_connectome/data_summary__UNIPD_WashU.csv`, `..._UNIPD_PASPORT.csv`, etc. (same fixed filename every time, overwritten on each run - a current snapshot, not a dated report). One row per subject, one column per leaf registered in `config/file_patterns.json` (e.g. `lesion/manual_masks/anat/lesion_mask`, `feature/func/FC-pearson`). Each cell is `present` if the file exists, `missing` if not - open it in a spreadsheet and filter for `missing` to scan gaps quickly. No trailing totals row - per-column counts (e.g. to reconcile against `copied + skipped (exists)` in a `copy_summary` report) are computed separately, outside this CSV.

Nothing is copied or modified - purely a read of the current source, same as `verify_retrieval.py`.

### Verification: a final pass, once every dataset has finished copying

After every requested dataset has been copied, the pipeline re-checks `data/` against the current source before writing the report: every file it just copied, or found already present and skipped, is checksum-compared against the source. This catches both a corrupted copy and a local file that's gone stale because the source changed since. This verification only starts once **all** datasets have finished copying — never interleaved with copying — so the log always has the full copy narrative before the verification narrative. Automatic on every run, nothing extra to configure.

The standalone script runs the exact same verification, read-only, without doing a retrieval:

```bash
PYTHONPATH=. conda run -n nemesis python scripts/verify_retrieval.py --config config/retrieval.json
```

It prints a summary and exits non-zero if anything looks wrong — nothing is copied or modified.

Console output while a run happens shows the same story live: which dataset is being processed, each file copied or skipped, any warnings, as they happen.

## Re-running

Safe to re-run the same config any time. With `overwrite: false` (default) nothing already present is touched — you'll just see "skip (exists)" for everything. Set `overwrite: true` only if you actually want to replace what's already there (e.g. the source was corrected upstream).
