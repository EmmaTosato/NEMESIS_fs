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

### Where are HC (healthy controls)?

Only `UNIPD/WashU` has healthy controls (68 of them) alongside its 250 stroke subjects, embedded in the same dataset — useful as a reference cohort. The other 3 datasets are 100% stroke (`ST`). Use `"group_filter": ["HC"]` to get only those.

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

Every run writes `reports/data_retrieval/clinical_connectome/<dd-mm-yy>__<hh-mm>.md` — starting with the config actually used (so you can always tell which settings produced it), then a summary table (subjects per dataset, files copied/skipped/failed, whether `participants.tsv` was copied), then an explicit list of anything that went wrong (a specific file missing for a specific subject), grouped by dataset with a count — never a list of successful copies, just the exceptions worth looking at.

Console output while it runs shows the same story live: which dataset is being processed, each file copied or skipped, any warnings, as they happen. This narrative is **not** saved anywhere — only the report file persists after the run ends.

## Re-running

Safe to re-run the same config any time. With `overwrite: false` (default) nothing already present is touched — you'll just see "skip (exists)" for everything. Set `overwrite: true` only if you actually want to replace what's already there (e.g. the source was corrected upstream).
