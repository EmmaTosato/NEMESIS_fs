# Analysis pipeline (embedding/clustering) — user guide

4 independent CLI scripts that take lesion masks already retrieved by `retrieve_data.py` (`docs/guides/retrieval.md`) through to a 2D feature matrix, a dimensionality-reduction embedding, and/or a clustering. Each script is short and self-contained (`docs/dev/analysis.md` has the architecture/design rationale) — this guide is about running them and reading their output. For what UMAP/t-SNE/PCA actually do, see `docs/methods/dimensionality_reduction.md`; for KMeans, see `docs/methods/clustering.md`.

## The 4 scripts, and how they chain

```
build_lesion_matrix.py  →  produces a matrix artifact (matrix.npy + metadata.csv)
        │
        ├──→ dim_reduction.py              → embedding only
        ├──→ dim_reduction_clustering.py   → embedding + cluster_label + cluster_plot.png
        └──→ clustering.py                 → same matrix + cluster_label + cluster_plot.png (no reduction)
```

`build_lesion_matrix.py` runs first, always — the other three read its output via `input_path`. They don't chain into each other; each reads directly from a `build_lesion_matrix.py` output directory.

All 4: `conda activate nemesis`, then `python -m src.pipeline.<script> --config config/pipelines/<script>.json` — or the matching `sbatch jobs/run_<script>.sh` on the cluster (never a bare `python` on the login node).

## 1. Building the feature matrix — `build_lesion_matrix.py`

```bash
python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json
```

### Voxel-wise (default) — `config/pipelines/build_lesion_matrix.json`

```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome",
  "datasets": ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"],
  "reference_dataset": "UNIPD/WashU",
  "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
  "binarize_threshold": 0.5,
  "resample_interpolation": "nearest",
  "parcellate": false,
  "atlas_path": null,
  "parcel_aggregation": null,
  "save_parcellated_volumes": false,
  "output_root": "data/derived/lesion_matrix",
  "run_name": "run1",
  "overwrite": false
}
```

Each subject's lesion mask is resampled onto `reference_dataset`'s grid (only where its native resolution differs), re-binarized at `binarize_threshold`, and flattened into one row of `X`. Voxels that are constant across every subject (never lesioned in this cohort) are dropped.

### Parcellated — proportion of damage per atlas region

```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome",
  "datasets": ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"],
  "reference_dataset": "UNIPD/WashU",
  "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
  "binarize_threshold": 0.5,
  "resample_interpolation": "nearest",
  "parcellate": true,
  "atlas_path": "data/atlases/mmp_subcortical_mni.nii.gz",
  "parcel_aggregation": "fraction_lesioned",
  "save_parcellated_volumes": false,
  "output_root": "data/derived/lesion_matrix",
  "run_name": "mmp_run1",
  "overwrite": false
}
```

Each subject's row becomes one value per atlas parcel (the fraction of that parcel's voxels that are lesioned), instead of one value per voxel — hundreds of columns instead of hundreds of thousands. `atlas_path` must be a volumetric NIfTI with discrete integer labels (0 = background); any atlas works, not just MMP. Set `save_parcellated_volumes: true` to also write one QC `.nii.gz` per subject (parcel values painted back onto the atlas grid, for visual inspection in `fsleyes`) under `parcellated_volumes/` inside the output directory — off by default since it's one extra file per subject.

### Field reference

| field | meaning |
|---|---|
| `data_root` | local root holding the retrieved datasets (matches `retrieve_data.py`'s `output_root`) |
| `datasets` | which retrieved datasets to include, must be non-empty and duplicate-free |
| `reference_dataset` | must be one of `datasets` — its first (sorted) lesion file fixes the common voxel grid |
| `lesion_glob` | glob pattern (relative to each dataset root) matching one lesion file per subject folder |
| `binarize_threshold` | `[0.0, 1.0]` — threshold applied after resampling to re-binarize |
| `resample_interpolation` | `"linear"` / `"nearest"` / `"continuous"` — used for the lesion masks; the atlas (if `parcellate: true`) always uses `"nearest"` regardless of this value |
| `parcellate` | `false` = voxel-wise, `true` = parcellated (requires `atlas_path` + `parcel_aggregation`) |
| `atlas_path` | required iff `parcellate: true`, forbidden otherwise |
| `parcel_aggregation` | required iff `parcellate: true` — a key in `src.features.lesion.PARCEL_AGGREGATIONS` (today only `"fraction_lesioned"`) |
| `save_parcellated_volumes` | must be `false` when `parcellate: false` |
| `output_root` / `run_name` | output lands at `<output_root>/<dd-mm>_<run_name>/` |
| `overwrite` | `false` → a second run with the same `run_name` on the same day fails loudly instead of silently replacing it |

### Output

```
data/derived/lesion_matrix/20-07_run1/
├── matrix.npy              # (n_subjects, n_features)
├── metadata.csv             # subject_id, dataset — same row order as matrix.npy
├── non_constant_mask.npy    # which pre-drop voxels/parcels survived
├── parcel_ids.npy           # only if parcellate: true — atlas label id per column of matrix.npy
├── parcellated_volumes/     # only if save_parcellated_volumes: true — one .nii.gz per subject
├── manifest.json
└── README.md                 # per-dataset subject counts, matrix shape, config used
```

Plus `reports/build_lesion_matrix/clinical_connectome/build_summary__<timestamp>.md` and a matching file under `logs/`, written every run.

## 2. Dimensionality reduction only — `dim_reduction.py`

```bash
python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json
```

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/20-07_run1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/dim_reduction",
  "run_name": "run1",
  "overwrite": false
}
```

`input_path` must already exist (a `build_lesion_matrix.py` output directory) — no auto-build. `reduction_method` is one of `"umap"` / `"tsne"` / `"pca"`, and must have a matching entry in `params_file` (see "Method parameters" below). Output: `results/dim_reduction/umap/20-07_run1/{matrix.npy (the embedding), metadata.csv (unchanged), manifest.json, README.md}`.

## 3. Reduction + clustering — `dim_reduction_clustering.py`

```bash
python -m src.pipeline.dim_reduction_clustering --config config/pipelines/dim_reduction_clustering.json
```

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/20-07_run1",
  "reduction_method": "tsne",
  "reduction_params_file": "config/registry/params_reduction.json",
  "clustering_method": "kmeans",
  "clustering_params_file": "config/registry/params_clustering.json",
  "output_root": "results/dim_reduction_clustering",
  "run_name": "run1",
  "overwrite": false
}
```

Embeds with `reduction_method`, then clusters the **embedding** (not the raw matrix) with `clustering_method`. Output: `results/dim_reduction_clustering/tsne-kmeans/20-07_run1/`:

```
matrix.npy          # the embedding
metadata.csv         # subject_id, dataset, cluster_label
cluster_plot.png      # 2D scatter of the embedding's first 2 components, colored by cluster_label
manifest.json
README.md
```

If the embedding has fewer than 2 components (e.g. `n_components: 1`), `cluster_plot.png` is skipped with a logged warning — the matrix and labels are still written normally.

## 4. Clustering only, no reduction — `clustering.py`

```bash
python -m src.pipeline.clustering --config config/pipelines/clustering.json
```

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/20-07_mmp_run1",
  "clustering_method": "kmeans",
  "params_file": "config/registry/params_clustering.json",
  "output_root": "results/clustering",
  "run_name": "run1",
  "overwrite": false
}
```

Clusters the matrix directly — meant for a small, already-compact input (e.g. a parcellated matrix, a few hundred columns), not a full voxel-wise matrix. Output: `results/clustering/kmeans/20-07_run1/{matrix.npy (unchanged input), metadata.csv (+ cluster_label), cluster_plot.png, manifest.json, README.md}`. `cluster_plot.png` here scatters the **raw** first 2 features (explicitly labeled "raw" on the axes) — with no reduction step, those 2 axes aren't a meaningful projection, just the coarsest possible sanity check.

## Method parameters — `params_reduction.json` / `params_clustering.json`

```jsonc
// config/registry/params_reduction.json
{
  "umap": { "params": { "n_neighbors": 15, "min_dist": 0.1, "random_state": 0 } },
  "tsne": { "params": { "perplexity": 30, "early_exaggeration": 12, "learning_rate": 200, "max_iter": 1000, "init": "random", "random_state": 0 } },
  "pca":  { "params": { "n_components": 10 } }
}
```
```jsonc
// config/registry/params_clustering.json
{ "kmeans": { "params": { "n_clusters": 4, "random_state": 0, "n_init": "auto" } } }
```

Every key under `"params"` is passed straight to the underlying `sklearn`/`umap` estimator's constructor — no hidden defaults, no validation of individual keys here (a typo raises whatever error `sklearn`/`umap` itself gives for a bad constructor argument). See `docs/methods/dimensionality_reduction.md`/`docs/methods/clustering.md` for what each parameter actually controls.

## Chaining runs together

`input_path` for the 3 modeling scripts is always a `build_lesion_matrix.py` output directory — copy the exact path it printed/logged:

```bash
python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json
# -> INFO: matrix written to data/derived/lesion_matrix/20-07_run1 (shape (1300, 842))

# then, in dim_reduction.json / dim_reduction_clustering.json / clustering.json:
"input_path": "data/derived/lesion_matrix/20-07_run1"
```

The 3 modeling scripts don't feed into each other — running `dim_reduction_clustering.py` doesn't require having run `dim_reduction.py` first; both read straight from `build_lesion_matrix.py`'s output.

## Inspecting output

- **`README.md`** inside every output directory — self-contained summary (config used, shapes, per-dataset counts) that travels with the artifact if copied elsewhere.
- **`reports/<script>/<project>/*.md`** — same summary, kept as a chronological record of every run in this repo (not just the latest).
- **`logs/<script>/<project>/*.log`** — full console output of that run.
- **`cluster_plot.png`** — only for `dim_reduction_clustering.py`/`clustering.py`, a first visual check of cluster separation.

## Re-running

`overwrite: false` (the default) means re-running with the same `run_name` on the same day fails with a clear `FileExistsError` naming the existing directory, rather than silently replacing it — set `overwrite: true`, or change `run_name`, to intentionally redo a run.
