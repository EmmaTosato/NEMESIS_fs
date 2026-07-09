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

Listing the same `{"space": ..., "modality": ...}` entry twice in `retrieve` is also rejected upfront (not silently deduplicated) — a duplicate would otherwise make the second copy look like "already existed from a previous run" in the report, when it was actually copied moments earlier by the first entry in the same run.

## Where `space`+`modality` actually points to: `config/file_patterns.json`

`{"space": "mni", "modality": "lesion_mask"}` has to mean *some specific file, with some specific name, in some specific folder*. That mapping is not hidden in code — it is written out, in plain JSON, in `config/file_patterns.json`, so anyone (not just whoever wrote the Python) can check exactly what gets fetched:

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

Read it as: "for `native`/`T1w`, look for a file named `<subject_id>/anat/<subject_id>_T1w.nii.gz` inside the dataset folder, with `<subject_id>` replaced by the real ID (e.g. `sub-STUNIPD0002`)".

Notice `lesion_roi` has **two** filenames listed, not one. That's because two different data-collection pipelines named the same kind of file differently: PASPORT calls it `sub-X_lesion_roi.nii.gz`, WashU and UKLFR/stroke_UKLFR call it `sub-X_space-T1w_lesion_roi.nii.gz`. Both names mean the same thing, so both are registered under the same `lesion_roi` entry, in a chosen order (the first one is tried first). If a naming convention ever changes again, or a new source uses yet another name for the same kind of file — **this is the file to edit**, not the Python code.

If, instead, two files really are two *different* things (not just two names for the same thing), they get **different** modality names in this file, so they can be requested separately and are never mixed up.

### What happens if a subject has more than one matching file?

Normally exactly one of the registered filenames exists for a given subject. If — for any reason — a subject has files matching **more than one** of the registered names for the same `space`+`modality` (e.g. both `lesion_roi` variants at once), the run does **not** fail and does **not** silently pick one at random: it always uses the first-listed one (the priority order you wrote in `file_patterns.json`), and it flags the subject in the report's **Ambiguous** section, naming both files it found — so you know it happened and can go check by hand whether it's an intentional duplicate or a data problem (e.g. an old file that should have been deleted).

### Where are HC (healthy controls)?

Only `UNIPD/WashU` has healthy controls (68 of them) alongside its 250 stroke subjects, embedded in the same dataset — useful as a reference cohort. The other 3 datasets are 100% stroke (`ST`). Use `"group_filter": ["HC"]` to get only those.

### Explicit `subjects` spanning more than one dataset

If `subjects` lists people from more than one of the requested `datasets`, each dataset only retrieves the ones it actually has (subject IDs already identify their dataset, e.g. `sub-STUNIPD...` vs `sub-STUKLFR...`). If you list a subject that isn't in a particular requested dataset, that dataset's entry in the report's "Missing" section will say so explicitly (`"<dataset>: <subject_id> - not present in this dataset"`) rather than staying silent about it.

### If a subject folder doesn't follow the naming convention

Every subject folder on disk is expected to be named `sub-<DISEASE><SITE>[HC]<NUM>` (e.g. `sub-STUNIPD0002`). If a folder starting with `sub-` doesn't match that pattern — a leftover test/QC folder, for instance — it is never treated as a real subject and never copied. It shows up, by name, in the report's **Non-conforming subject folders** section, so it stays visible as something worth looking into (relevant to the ongoing effort to keep subject IDs consistent), instead of either silently being mistaken for a real patient or crashing the whole run.

## What you get in `data/`

```
data/clinical_connectome/UNIPD/WashU/
├── participants.tsv                      (skipped for WashU - it doesn't have one at the source)
└── sub-STUNIPD0002/lesion/
    ├── native/sub-STUNIPD0002_T1w.nii.gz
    └── mni/sub-STUNIPD0002_space-MNI152NLin6Asym_label-lesion_mask.nii.gz
```

Filenames are exactly as at the source — nothing renamed or transformed.

## The report

Every run writes `reports/data_retrieval/clinical_connectome/<dd-mm-yy>__<hh-mm>.md` — starting with the config actually used (so you can always tell which settings produced it), then a summary table (subjects per dataset, files copied/skipped/failed, whether `participants.tsv` was copied), then three sections listing anything worth a second look, each grouped by dataset with a count:

- **Missing** — a specific file missing for a specific subject, or an explicitly requested subject not present in that dataset.
- **Ambiguous** — more than one registered filename matched for a subject (see above); the highest-priority one was used regardless.
- **Non-conforming subject folders** — folders that don't follow the naming convention, excluded from retrieval.

Never a list of successful copies — just the exceptions worth looking at.

Console output while it runs shows the same story live: which dataset is being processed, each file copied or skipped, any warnings, as they happen. That same narrative is also saved to `logs/data_retrieval/clinical_connectome/<dd-mm-yy>__<hh-mm>.log` — same file name as the report from that run, so you can always find the log matching a given report.

## Re-running

Safe to re-run the same config any time. With `overwrite: false` (default) nothing already present is touched — you'll just see "skip (exists)" for everything. Set `overwrite: true` only if you actually want to replace what's already there (e.g. the source was corrected upstream).
