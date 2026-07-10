# Data retrieval — user guide

Copies lesion data (and, optionally, the clinical/demographic table) from the EBRAIN-mounted `Clinical_connectome` source into this project's local `data/` folder, driven by a single JSON config. Covers the 4 in-scope stroke datasets: `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`.

## How to run

```bash
conda activate nemesis
python -m src.pipeline.retrieve_data --config config/data_retrieval.json
```

One required argument, `--config`. Everything else — which datasets, which files, where to put them — is in the JSON file.

## Writing the config

Two things to decide: **which files** (`retrieve`) and **which subjects** (`group_filter` / `subjects`).

### Example 1 — the MNI-space lesion mask, all stroke subjects, 4 datasets

```json
{
  "output_root": "data/",
  "project": "clinical_connectome",
  "project_root": "/data/corbetta/Clinical_connectome",
  "file_patterns": "config/file_patterns.json",
  "datasets": ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"],
  "group_filter": ["ST"],
  "subjects": null,
  "retrieve": [
    { "space": "mni", "modality": "lesion_mask" }
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
  "project_root": "/data/corbetta/Clinical_connectome",
  "file_patterns": "config/file_patterns.json",
  "datasets": ["UNIPD/WashU"],
  "group_filter": null,
  "subjects": ["sub-STUNIPD0002", "sub-STUNIPD0003"],
  "retrieve": [
    { "space": "native", "modality": "T1w" }
  ],
  "include_tabular_data": false,
  "overwrite": false
}
```

### Field reference

| field | meaning |
|---|---|
| `output_root` | where copied files land locally (usually `"data/"`) |
| `project` / `project_root` | name used in the local folder layout / absolute source path on this machine |
| `file_patterns` | path to the registry file that says which real filename corresponds to each `space`+`modality` (see below) — normally leave it as `"config/file_patterns.json"` |
| `datasets` | which of the 4 datasets to include (`"UNIPD/WashU"` etc.) |
| `group_filter` | `["ST"]`, `["HC"]`, both, or `null` for everyone. Ignored entirely if `subjects` is set. |
| `subjects` | `null` for everyone (subject to `group_filter`), or an exact list of subject IDs to retrieve — bypasses `group_filter` |
| `retrieve` | list of `{"space": ..., "modality": ...}` — see below |
| `include_tabular_data` | copy `participants.tsv` too, when the dataset has one |
| `overwrite` | `false` (default, recommended): skip files that already exist locally. `true`: re-copy and replace them |

### `space` and `modality`

- `space: "native"` → the subject's own scan space. `modality` must be one the dataset actually has (table below).
- `space: "mni"` → the normalized lesion mask. `modality` is always `"lesion_mask"` (the only thing that exists there today).

| dataset | native modalities available | mni |
|---|---|---|
| UNIPD/WashU | T1w, T2w, FLAIR, lesion_roi | lesion_mask |
| UNIPD/PASPORT | CT, FLAIR, lesion_roi | lesion_mask |
| UNIPD/PSP | CT, FLAIR  | lesion_mask |
| UKLFR/stroke_UKLFR | T1w, T2w, FLAIR, lesion_roi | lesion_mask |

Asking for a modality a dataset doesn't have (e.g. `lesion_roi` on PSP) stops the whole run before anything is copied, with a clear error — fix the config and re-run.

Listing the same entry twice in `retrieve` is rejected upfront (not deduplicated) — otherwise the second copy would misleadingly look like it already existed from a previous run.

## Where `space`+`modality` actually points to: `config/file_patterns.json`

`{"space": "mni", "modality": "lesion_mask"}` maps to a specific filename template, registered in plain JSON in `config/file_patterns.json` — not hidden in Python:

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

Read it as: "for `native`/`T1w`, look for `<subject_id>/anat/<subject_id>_T1w.nii.gz` inside the dataset folder".

`lesion_roi` has two filenames because two pipelines name the same file differently (PASPORT vs. WashU/UKLFR) — both registered under the same key, in priority order (first one tried first). If a naming convention changes or a new one appears, edit this file, not the Python code. Two genuinely different files get different modality names instead, so they stay requestable separately.

### What happens if a subject has more than one matching file?

If a subject has files matching more than one registered name for the same `space`+`modality`, the run doesn't fail or pick one at random: it uses the first-listed (priority) one and flags the subject in the report's **Ambiguous** section, naming both files found — check by hand whether it's intentional or a leftover file.

### Where are HC (healthy controls)?

Only `UNIPD/WashU` has healthy controls (68 of them) alongside its 250 stroke subjects, embedded in the same dataset — useful as a reference cohort. The other 3 datasets are 100% stroke (`ST`). Use `"group_filter": ["HC"]` to get only those.

### Explicit `subjects` spanning more than one dataset

If `subjects` lists people from more than one of the requested `datasets`, each dataset only retrieves the ones it actually has (subject IDs already identify their dataset, e.g. `sub-STUNIPD...` vs `sub-STUKLFR...`). If you list a subject that isn't in a particular requested dataset, that dataset's entry in the report's "Missing" section will say so explicitly (`"<dataset>: <subject_id> - not present in this dataset"`) rather than staying silent about it.

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

Filenames are exactly as at the source — nothing renamed or transformed.

## After running: inspecting the output

1. **Open the report** — `reports/data_retrieval/clinical_connectome/<dd-mm-yy>__<hh-mm>.md`. Check the summary table first, then the sections below it for anything flagged (Missing, Ambiguous, Non-conforming, Mismatched, ...).
2. **Need more detail on a flagged item?** Open the matching log — `logs/data_retrieval/clinical_connectome/<dd-mm-yy>__<hh-mm>.log` (same filename stem as the report, so it's always easy to find). It has the full file-by-file narrative, in the order things happened.
3. **Optional — re-verify `data/` later without a new run**: `scripts/verify_retrieval.py` (see below) re-checks everything currently in `data/` against source, read-only. Useful before starting analysis on data fetched a while ago, or if you suspect local disk issues.

### The report

Every run writes the report above — starting with the config actually used (so you can always tell which settings produced it), then a summary table, then sections listing anything worth a second look, each grouped by dataset with a count.

The summary table has, per dataset: subjects selected, `native`, `mni`, copied/skipped/failed, participants status. `native`/`mni` say how many of the selected subjects have *any* file in that space at all (any of T1w/T2w/FLAIR/CT/lesion_roi for native, the lesion mask for mni — see `config/file_patterns.json`) — regardless of which one this run actually requested. Useful for a quick sanity check: e.g. if `native` is much higher than `mni` for a dataset, most subjects there simply don't have the MNI-space lesion mask produced yet.

- **Missing** — a specific file missing for a specific subject, or an explicitly requested subject not present in that dataset. When the subject has data in the *other* space, the line says so inline, e.g. `sub-STUNIPD0004 - no mni/lesion_mask (in native not in mni)` means: this subject has native (raw) data, it's specifically the MNI derivative that's missing — as opposed to a bare `no mni/lesion_mask` with no suffix, which means the subject has neither space at all. If `retrieve` asks for more than one `{space, modality}` (e.g. both `native/T1w` and `mni/lesion_mask`), each dataset's Missing entries are further split into one sub-list per requested item (`**native/T1w** (12)`, `**mni/lesion_mask** (5)`, ...) instead of being mixed together — the dataset's overall `Missing Count` still counts everything.
- **Ambiguous** — more than one registered filename matched for a subject (see above); the highest-priority one was used regardless.
- **Non-conforming subject folders** — folders that don't follow the naming convention, excluded from retrieval.
- **Mismatched** — a local file's content no longer matches its current source (see below).
- **Not copied despite source having it** — verification found the source file, but `data/` doesn't have it; a copy that silently failed to land.
- **Unexpected local files** — present in `data/` but not the current resolution for any expected subject/modality (stale naming, or a leftover from before the config or source changed).

The last three are also logged at ERROR/WARNING level, with an aggregate count line right before "done". Never a list of successful copies — just the exceptions worth looking at.

### Verification: a final pass, once every dataset has finished copying

After every requested dataset has been copied, the pipeline re-checks `data/` against the current source before writing the report: every file it just copied, or found already present and skipped, is checksum-compared against the source. This catches both a corrupted copy and a local file that's gone stale because the source changed since. This verification only starts once **all** datasets have finished copying — never interleaved with copying — so the log always has the full copy narrative before the verification narrative. Automatic on every run, nothing extra to configure.

The standalone script runs the exact same verification, read-only, without doing a retrieval:

```bash
PYTHONPATH=. conda run -n nemesis python scripts/verify_retrieval.py --config config/data_retrieval.json
```

It prints a summary and exits non-zero if anything looks wrong — nothing is copied or modified.

Console output while a run happens shows the same story live: which dataset is being processed, each file copied or skipped, any warnings, as they happen.

## Re-running

Safe to re-run the same config any time. With `overwrite: false` (default) nothing already present is touched — you'll just see "skip (exists)" for everything. Set `overwrite: true` only if you actually want to replace what's already there (e.g. the source was corrected upstream).
