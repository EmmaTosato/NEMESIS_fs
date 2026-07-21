# Analysis pipeline (embedding/clustering) — user guide

4 independent CLI scripts that take lesion masks already retrieved by `retrieve_data.py` (`docs/guides/retrieval.md`) through to a 2D feature matrix, a dimensionality-reduction embedding, and/or a clustering. Each script is short and self-contained (`docs/dev/analysis.md` has the architecture/design rationale) — this guide is about running them and reading their output. For what each reduction method actually does (UMAP/t-SNE/PCA/PCA-varimax/PaCMAP), see `docs/methods/dimensionality_reduction.md`; for clustering methods (KMeans/Agglomerative/GaussianMixture/DBSCAN/SpectralClustering), see `docs/methods/clustering.md`.

## 0. Building a combined parcellation atlas (optional prerequisite) — `build_combined_atlas.py`

Only needed once, before running `build_lesion_matrix.py` with `parcellate: true`. Merges the Glasser MMP cortical atlas (360 parcels) with 12 Harvard-Oxford subcortical structures (thalamus, caudate, putamen, pallidum, hippocampus, amygdala — left/right) into a single 372-region label volume, reproducing the parcellation used by Thiebaut de Schotten et al. 2020 ahead of their varimax PCA:

```bash
python -m src.pipeline.build_combined_atlas --config config/pipelines/build_combined_atlas.json
```

```json
{
  "cortical_atlas_path": "assets/atlases/MNI_Glasser_HCP_v1.0.nii.gz",
  "subcortical_atlas_path": "assets/atlases/HarvardOxford-sub-maxprob-thr25-2mm.nii.gz",
  "output_atlas_path": "assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz",
  "output_label_table_path": "assets/atlases/glasser_hcp_harvardoxford_subcortical_372_labels.csv",
  "overwrite": false
}
```

Writes the combined atlas and a label lookup CSV (`value`, `name`, `hemisphere`, `source`). The output atlas is then pointed to directly by `build_lesion_matrix.json`'s `atlas_path` (see "Parcellated" below).

The paper's own 12 subcortical ROIs were hand-drawn and never published as a reusable atlas — Harvard-Oxford is a documented practical substitute (same 6 bilateral structures, standard MNI152 space), not a faithful reproduction of the paper's exact regions. See `src/atlases/combine.py` module docstring and `docs/debugging/debug_21_07_26.md` for the full rationale, including a subtle off-by-one bug caught in the right-hemisphere Harvard-Oxford indices before this ever reached code (never infer a bilateral atlas's right-hemisphere label from a left-hemisphere offset — read it from the atlas's own LUT).

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
  "reference_template_path": "data/templates/mni152_2mm.nii.gz",
  "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
  "binarize_threshold": 0.5,
  "resample_interpolation": "nearest",
  "parcellate": false,
  "atlas_path": null,
  "parcel_aggregation": null,
  "save_parcellated_volumes": false,
  "output_root": "data/derived/lesion_matrix",
  "run_name": "run1",
  "overwrite": false,
  "run_notes": null
}
```

Each subject's lesion mask is resampled onto `reference_template_path`'s grid (only where its native resolution differs), re-binarized at `binarize_threshold`, and flattened into one row of `X`. Voxels that are constant across every subject (never lesioned in this cohort) are dropped.

`reference_template_path` is an explicit, caller-supplied NIfTI (e.g. a canonical MNI152 2mm template) — **not** derived from any subject's lesion file. This is deliberate: the masks retrieved by `retrieve_data.py` are already named `space-MNI152NLin6Asym` (BIDS convention, produced upstream by the `manual_masks` pipeline, outside this repo), but that name alone doesn't guarantee a specific voxel resolution — picking "the first lesion file found" as the reference would silently tie the whole matrix's grid to whatever resolution that one file happens to have. Point this at a real template file with the resolution/grid actually wanted.

### Parcellated — proportion of damage per atlas region

```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome",
  "datasets": ["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"],
  "reference_template_path": "data/templates/mni152_2mm.nii.gz",
  "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
  "binarize_threshold": 0.5,
  "resample_interpolation": "nearest",
  "parcellate": true,
  "atlas_path": "data/atlases/mmp_subcortical_mni.nii.gz",
  "parcel_aggregation": "fraction_lesioned",
  "save_parcellated_volumes": false,
  "output_root": "data/derived/lesion_matrix",
  "run_name": "mmp_run1",
  "overwrite": false,
  "run_notes": null
}
```

Each subject's row becomes one value per atlas parcel (the fraction of that parcel's voxels that are lesioned), instead of one value per voxel — hundreds of columns instead of hundreds of thousands. `atlas_path` must be a volumetric NIfTI with discrete integer labels (0 = background); any atlas works, not just MMP. Set `save_parcellated_volumes: true` to also write one QC `.nii.gz` per subject (parcel values painted back onto the atlas grid, for visual inspection in `fsleyes`) under `parcellated_volumes/` inside the output directory — off by default since it's one extra file per subject.

### Field reference

| field | meaning |
|---|---|
| `data_root` | local root holding the retrieved datasets (matches `retrieve_data.py`'s `output_root`) |
| `datasets` | which retrieved datasets to include, must be non-empty and duplicate-free |
| `reference_template_path` | explicit reference NIfTI (e.g. MNI152 2mm) that fixes the common voxel grid — not derived from `datasets` |
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
  "overwrite": false,
  "fine_tuning": false,
  "run_notes": null
}
```

`input_path` must already exist (a `build_lesion_matrix.py` output directory) — no auto-build. `reduction_method` is one of `"umap"` / `"tsne"` / `"pca"` / `"pca_varimax"` / `"pacmap"`, and must have a matching entry in `params_file` (see "Method parameters" below). Output: `results/dim_reduction/umap/20-07_run1/{matrix.npy (the embedding), metadata.csv (unchanged), manifest.json, README.md}`.

### Fine-tuning `umap`/`pca`/`pca_varimax`/`pacmap` before a real run

t-SNE's parameters come straight from Thiebaut de Schotten et al. 2020 (`docs/methods/dimensionality_reduction.md`) — no tuning needed. For the 4 other methods, set `"fine_tuning": true` and pick a `run_name` for the sweep (e.g. `"tune1"`):

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/20-07_run1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/dim_reduction",
  "run_name": "tune1",
  "overwrite": false,
  "fine_tuning": true,
  "run_notes": null
}
```

This does **not** produce an embedding. It evaluates every combination in `params_reduction.json`'s `"umap"."tuning_grid"` (a Cartesian product — today `n_neighbors: [5,15,30,50]` × `min_dist: [0.0,0.1,0.25,0.5]`, 16 combinations) and writes a comparison table instead:

```
results/dim_reduction/umap/tuning/20-07_tune1/
├── tuning_results.csv    # one row per combination: n_neighbors, min_dist, trustworthiness
├── tuning_plot.png         # heatmap
└── README.md
```

Open the CSV or the plot, pick the best combination by eye (there is no automatic selection), write it into `params_reduction.json`'s `"umap"."params"`, then re-run with `"fine_tuning": false` and a new `run_name` to get the real embedding — fill in `"run_notes"` on that run to say why the parameters changed (see "Run history" below). PCA (and `pca_varimax`, same criterion — varimax rotation doesn't change total variance explained) works the same way, just with a single swept parameter (`n_components`) and `cumulative_explained_variance` as the metric instead of `trustworthiness`, plotted as a curve instead of a heatmap. `pacmap` reuses UMAP's `trustworthiness` metric (a generic neighbor-preservation criterion, not UMAP-specific).

`dim_reduction_clustering.py`/`clustering.py` have no fine-tuning mode — they consume whatever parameters were already chosen this way.

### Run history — `RUNS.md`

Every successful run of any of the 4 scripts (tuning or production) appends an entry to `<output_root>/<method>/RUNS.md` (e.g. `results/dim_reduction/umap/RUNS.md`; `data/derived/lesion_matrix/RUNS.md` for `build_lesion_matrix.py`, which has no method axis) — timestamp, params used, output path, and `run_notes` if you set one. Unlike a single run's own `README.md`, this file is **never overwritten**, just appended to: it's the place to see the full history of a method's runs and, via `run_notes`, *why* one differs from the previous one — set `run_notes` whenever a config change is methodologically meaningful (new fine-tuned parameters, a different atlas, a different subject selection), not for a routine re-run with the same settings.

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
  "clustering_methods": ["kmeans", "dbscan"],
  "clustering_params_file": "config/registry/params_clustering.json",
  "output_root": "results/dim_reduction_clustering",
  "run_name": "run1",
  "overwrite": false,
  "run_notes": null
}
```

Embeds **once** with `reduction_method`, then clusters that same embedding (not the raw matrix) with every method in `clustering_methods` — always a list, even for a single method (`["kmeans"]`), never a bare string. Each method gets its own full output, exactly as if it had been run alone: `results/dim_reduction_clustering/tsne-kmeans/20-07_run1/`, `results/dim_reduction_clustering/tsne-dbscan/20-07_run1/`, etc.:

```
matrix.npy          # the embedding
metadata.csv         # subject_id, dataset, cluster_label
cluster_plot.png      # 2D scatter of the embedding's first 2 components, colored by cluster_label
manifest.json
README.md
```

If the embedding has fewer than 2 components (e.g. `n_components: 1`), `cluster_plot.png` is skipped with a logged warning — the matrix and labels are still written normally.

### Comparing methods — `comparison/cluster_comparison.png`

When `clustering_methods` has more than one entry, after every method has finished, a side-by-side comparison is written to `results/dim_reduction_clustering/comparison/20-07_run1/{cluster_comparison.png, README.md}` — one subplot per method, same embedding, same shared x/y axis limits across subplots so the comparison is visually honest, each colored by that method's own `cluster_label`. This is a secondary, non-atomic artifact (like `reports/`/`logs/`, no `manifest.json`) built from the exact labels each method already wrote to its own `matrix.npy`/`metadata.csv` — not a re-run.

## 4. Clustering only, no reduction — `clustering.py`

```bash
python -m src.pipeline.clustering --config config/pipelines/clustering.json
```

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/20-07_mmp_run1",
  "clustering_methods": ["kmeans", "agglomerative", "gmm"],
  "params_file": "config/registry/params_clustering.json",
  "output_root": "results/clustering",
  "run_name": "run1",
  "overwrite": false,
  "run_notes": null
}
```

Clusters the matrix directly — meant for a small, already-compact input (e.g. a parcellated matrix, a few hundred columns), not a full voxel-wise matrix. `clustering_methods` is always a list (single method → single-element list); one full output per method: `results/clustering/kmeans/20-07_run1/{matrix.npy (unchanged input), metadata.csv (+ cluster_label), cluster_plot.png, manifest.json, README.md}`, same for `agglomerative`/`gmm`. `cluster_plot.png` here scatters the **raw** first 2 features (explicitly labeled "raw" on the axes) — with no reduction step, those 2 axes aren't a meaningful projection, just the coarsest possible sanity check.

With more than one method, `results/clustering/comparison/20-07_run1/cluster_comparison.png` is written too — same idea as `dim_reduction_clustering.py`'s comparison plot above, but on the raw first-2-features scatter instead of an embedding.

## Method parameters — `params_reduction.json` / `params_clustering.json`

```jsonc
// config/registry/params_reduction.json
{
  "umap": {
    "params": { "n_neighbors": 15, "min_dist": 0.1, "n_components": 2, "random_state": 0 },
    "tuning_grid": { "n_neighbors": [5, 15, 30, 50], "min_dist": [0.0, 0.1, 0.25, 0.5] },
    "trustworthiness_n_neighbors": 10
  },
  "tsne": { "params": { "perplexity": 30, "early_exaggeration": 12, "learning_rate": 200, "max_iter": 1000, "init": "random", "random_state": 0 } },
  "pca":  {
    "params": { "n_components": 10 },
    "tuning_grid": { "n_components": [2, 5, 10, 15, 20, 30] }
  },
  "pca_varimax": {
    "params": { "n_components": 10, "rotation_max_iter": 500 },
    "tuning_grid": { "n_components": [2, 5, 10, 15, 20, 30] }
  },
  "pacmap": {
    "params": { "n_components": 2, "n_neighbors": 10, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0 },
    "tuning_grid": { "n_neighbors": [5, 10, 20, 50] },
    "trustworthiness_n_neighbors": 10
  }
}
```

`tuning_grid`/`trustworthiness_n_neighbors` are only read when `dim_reduction.json` sets `"fine_tuning": true` (see above) — `"params"` alone is what a normal run uses. `pca_varimax` is the one method whose `"params"` isn't unpacked straight into a single estimator constructor: `n_components`/`rotation_max_iter` are read explicitly, since it wraps a PCA fit *and* a varimax rotation (`docs/methods/dimensionality_reduction.md`).
```jsonc
// config/registry/params_clustering.json
{
  "kmeans": { "params": { "n_clusters": 4, "random_state": 0, "n_init": "auto" } },
  "agglomerative": { "params": { "n_clusters": 4, "linkage": "ward" } },
  "gmm": { "params": { "n_components": 4, "random_state": 0 } },
  "dbscan": { "params": { "eps": 0.5, "min_samples": 5 } },
  "spectral": { "params": { "n_clusters": 4, "affinity": "nearest_neighbors", "random_state": 0 } }
}
```

No `tuning_grid` for any clustering method - fine-tuning is dim-reduction-only (see above). Unlike the others, `dbscan`'s `eps`/`min_samples` aren't a validated universal default — they're a literal distance threshold that must be re-tuned to whatever feature space is being clustered on (`docs/methods/clustering.md`).

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
