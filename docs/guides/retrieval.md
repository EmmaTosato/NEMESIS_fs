# Data retrieval — user guide

Copies lesion data (and, optionally, the clinical/demographic table) from the EBRAIN-mounted `Clinical_connectome` source into this project's local `data/` folder, driven by a single JSON config. Covers the 4 in-scope stroke datasets: `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`.

## How to run

```bash
conda activate nemesis
python -m src.pipeline.retrieve_data --config config/retrieval.json
```

One required argument, `--config`. Everything else — which datasets, which files, where to put them — is in the JSON file.

## Writing the config

Two things to decide: **which files** (`retrieve`) and **which subjects** (`group_filter` / `subjects`).

### Example 1 — the MNI-space lesion mask, all stroke subjects, 4 datasets

```json
{
  "output_root": "data/",
  "project": "clinical_connectome",
  "file_patterns": "config/file_patterns.json",
  "datasets": ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"],
  "group_filter": ["ST"],
  "subjects": null,
  "retrieve": [
    { "object": "lesion", "space": "mni", "modality": "lesion_mask" }
  ],
  "include_tabular_data": true,
  "overwrite": false
}
```

### Example 2 — native T1w, only 2 specific subjects

```json
{
  "output_root": "data/",
  "project": "clinical_connectome",
  "file_patterns": "config/file_patterns.json",
  "datasets": ["UNIPD/WashU"],
  "group_filter": null,
  "subjects": ["sub-STUNIPD0002", "sub-STUNIPD0003"],
  "retrieve": [
    { "object": "lesion", "space": "native", "modality": "T1w" }
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
| `file_patterns` | path to the registry file that says which real filename corresponds to each `object`/`space`/`modality`, and where each `object`'s data actually lives on the source (see below) — normally leave it as `"config/file_patterns.json"` |
| `datasets` | which of the 4 datasets to include (`"UNIPD/WashU"` etc.) |
| `group_filter` | `["ST"]`, `["HC"]`, both, or `null` for everyone. Ignored entirely if `subjects` is set. |
| `subjects` | `null` for everyone (subject to `group_filter`), or an exact list of subject IDs to retrieve — bypasses `group_filter` |
| `retrieve` | list of `{"object": ..., "space": ..., "modality": ...}` — see below |
| `include_tabular_data` | copy `participants.tsv` too, when the dataset has one |
| `overwrite` | `false` (default, recommended): skip files that already exist locally. `true`: re-copy and replace them |

Note: unlike an older version of this config, there is no `project_root` field here anymore — each `object` (see below) has its own source root, declared in `config/file_patterns.json` instead, since `lesion` and features live under different directory trees.

### `object`, `space`, and `modality`

- `object: "lesion"` → anatomical/lesion data (the only thing actually retrievable today). Nests into:
  - `space: "native"` → the subject's own scan space. `modality` must be one the dataset actually has (table below).
  - `space: "mni"` → the normalized lesion mask. `modality` is always `"lesion_mask"` (the only thing that exists there today).
- `object: "feature"` exists in `config/file_patterns.json` (e.g. `func`/`motion`) but isn't wired into `retrieve` yet — not usable in a config today.

| dataset | native modalities available | mni |
|---|---|---|
| UNIPD/WashU | T1w, T2w, FLAIR, lesion_roi | lesion_mask |
| UNIPD/PASPORT | CT, FLAIR, lesion_roi | lesion_mask |
| UNIPD/PSP | CT, FLAIR  | lesion_mask |
| UKLFR/stroke_UKLFR | T1w, T2w, FLAIR, lesion_roi | lesion_mask |

Asking for a modality a dataset doesn't have (e.g. `lesion_roi` on PSP) stops the whole run before anything is copied, with a clear error — fix the config and re-run.

Listing the same entry twice in `retrieve` is rejected upfront (not deduplicated) — otherwise the second copy would misleadingly look like it already existed from a previous run.

## Where `object`+`space`+`modality` actually points to: `config/file_patterns.json`

`{"object": "lesion", "space": "mni", "modality": "lesion_mask"}` maps to a specific filename template, registered in plain JSON in `config/file_patterns.json` — not hidden in Python:

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
  }
}
```

Read it as: "for `lesion`/`native`/`T1w`, look for `<subject_id>/anat/<subject_id>_T1w.nii.gz` inside the `lesion` object's project root (its own field here) + dataset folder".

`lesion_roi` has two filenames because two pipelines name the same file differently (PASPORT vs. WashU/UKLFR) — both registered under the same key. If a naming convention changes or a new one appears, edit this file, not the Python code. Two genuinely different files get different modality names instead, so they stay requestable separately.

### What happens if a subject has more than one matching file?

If a subject has files matching more than one registered name for the same `object`/`space`/`modality`, **both get copied** — there's no "pick one and flag the rest" step anymore. If that's ever surprising (e.g. you expected only one naming convention per dataset), check `data/` by hand for that subject; it means the source genuinely has more than one file registered under that key.

### Where are HC (healthy controls)?

Only `UNIPD/WashU` has healthy controls (68 of them) alongside its 250 stroke subjects, embedded in the same dataset — useful as a reference cohort. The other 3 datasets are 100% stroke (`ST`). Use `"group_filter": ["HC"]` to get only those.

### Explicit `subjects` spanning more than one dataset

If `subjects` lists people from more than one of the requested `datasets`, each dataset only retrieves the ones it actually has (subject IDs already identify their dataset, e.g. `sub-STUNIPD...` vs `sub-STUKLFR...`). If you list a subject that isn't in a particular requested dataset, that dataset's entry in the report's "File not found" section will say so explicitly (`"<dataset>: <subject_id> - not present in this dataset"`) rather than staying silent about it.

### If a subject folder doesn't follow the naming convention

Subject folders are expected to be named `sub-<DISEASE><SITE>[HC]<NUM>` (e.g. `sub-STUNIPD0002`). A `sub-*` folder that doesn't match (leftover test/QC folder, etc.) is never treated as a subject or copied — it's listed by name in the report's **Non-conforming subject folders** section instead.

## What you get in `data/`

```
data/clinical_connectome/UNIPD/WashU/
├── participants.tsv                      (skipped for WashU - it doesn't have one at the source)
└── sub-STUNIPD0002/lesion/
    ├── native/sub-STUNIPD0002_T1w.nii.gz
    └── mni/sub-STUNIPD0002_space-MNI152NLin6Asym_label-lesion_mask.nii.gz
```

`lesion` in that path is the `object` you requested (only `lesion` is retrievable today). Filenames are exactly as at the source — nothing renamed or transformed.

## After running: inspecting the output

1. **Open the report** — `reports/data_retrieval/clinical_connectome/copy_summary__<dd-mm-yy>__<hh-mm>.md`. Check the summary table first, then the sections below it for anything flagged (Failed, File not found, Non-conforming, Mismatched, ...).
2. **Need more detail on a flagged item?** Open the matching log — `logs/data_retrieval/clinical_connectome/copy_summary__<dd-mm-yy>__<hh-mm>.log` (same filename stem as the report, so it's always easy to find). It has the full file-by-file narrative, in the order things happened.
3. **Want the full picture of what a dataset has, not just this run's gaps?** See [Data summary CSVs](#data-summary-csvs-the-full-picture) below.
4. **Optional — re-verify `data/` later without a new run**: `scripts/verify_retrieval.py` (see below) re-checks everything currently in `data/` against source, read-only. Useful before starting analysis on data fetched a while ago, or if you suspect local disk issues.

### The report

Every run writes the report above — starting with the config actually used (so you can always tell which settings produced it), then a summary table (copied, skipped (exists), failed - per dataset), then sections listing anything worth a second look, each a title heading with an explanation on the line right below it, grouped by dataset with a count.

This report only explains **this run**: what it looked for (`retrieve`) and what it did or didn't find. It does not say anything about whether a subject has other data your `retrieve` list didn't ask about - for that, see [Data summary CSVs](#data-summary-csvs-the-full-picture) below.

- **Failed** — a file whose copy didn't complete correctly, with the reason (e.g. permissions, disk full).
- **File not found** — no registered file found for a specific subject, or an explicitly requested subject not present in that dataset. Each line ends with `(empty folder)` - the directory that would hold the file exists but has nothing in it - or `(not found)` - every other case (the directory doesn't exist at all, or has other content but not this file).
- **Non-conforming subject folders** — folders that don't follow the naming convention, excluded from retrieval.
- **Mismatched** — a local file's content no longer matches its current source (see below).
- **Not copied despite source having it** — verification found the source file, but `data/` doesn't have it; a copy that silently failed to land.
- **Unexpected local files** — present in `data/` but not the current resolution for any expected subject/modality (stale naming, or a leftover from before the config or source changed).

If `retrieve` asks for more than one `{object, space, modality}` (e.g. both `lesion/native/T1w` and `lesion/mni/lesion_mask`), the Failed/File-not-found entries in each section are split into one sub-list per requested item (`**lesion/native/T1w** (12)`, `**lesion/mni/lesion_mask** (5)`, ...) instead of being mixed together — the section's overall count still counts everything.

The last three sections are also logged at ERROR/WARNING level, with an aggregate count line right before "done". Never a list of successful copies — just the exceptions worth looking at.

### Data summary CSVs: the full picture

`copy_summary` only tells you about the exact `(object, space, modality)` combinations a given run's `retrieve` asked for. To see everything a dataset has - every registered modality, for every subject, at once - run the separate, read-only summary:

```bash
PYTHONPATH=. conda run -n nemesis python scripts/data_summary.py --config config/retrieval.json
```

Writes one CSV per dataset - `reports/data_retrieval/clinical_connectome/data_summary__UNIPD_WashU.csv`, `..._UNIPD_PASPORT.csv`, etc. (same fixed filename every time, overwritten on each run - a current snapshot, not a dated report). One row per subject, one column per `(object, space, modality)` registered in `config/file_patterns.json` (e.g. `lesion/native/T1w`, `lesion/native/lesion_roi`, `lesion/mni/lesion_mask`, `feature/func/motion`). Each cell is `-` if the file is present, `missing` if not - open it in a spreadsheet and filter for `missing` to scan gaps quickly. A trailing `present` row counts how many subjects have a real file per column - for a combination you actually retrieve, that count should match `copied + skipped (exists)` in the corresponding `copy_summary` report; if it doesn't, something changed on the source between the two runs, or one of the reports is stale.

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
