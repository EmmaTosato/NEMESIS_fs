# NEMESIS

Data-driven stroke research project (Corbetta lab) building a **multimodal low-dimensional representation of stroke**: embedding lesions and structural/functional disconnectomes, clustering them, and relating the resulting clusters to clinical-behavioral outcomes (NIHSS, language, neglect, motor domains).

**Core hypothesis**: how different modalities (anatomical, structural, functional, physiological/EEG) overlap in explaining post-stroke deficit — informed by prior work (Corbetta 2015, Bisogno 2021, Talozzi 2023) showing that post-stroke deficits and disconnectome patterns are both low-dimensional, and that disconnection — not raw lesion location — best explains cross-domain behavioral impairment.

## Task breakdown

| Task | Scope | Status |
|---|---|---|
| **1** | Low-dimensional embedding of lesions (n~4000) + topographic clustering | Most mature piece — production embeddings/clustering already run, see below |
| **2** | Low-dimensional embedding of structural disconnection (SDC, n~3000) | Reuses Task 1's pipelines; full-cohort production run pending |
| **3** | Clustering on n~500 with fMRI (WashU + Padova + Freiburg), vs. healthy controls | Reuses Task 1's pipelines; FC matrices not yet built at scale |
| **4** | EEG (n~80, Padova) | Deferred to Sept/Oct 2026 |
| **5** | Correlating multimodal/multiscale features with behavioral outcomes (n~60) | Early exploratory code only, no CLI/pipeline yet |

## Quick start

```bash
conda env create -f environment.yml
conda activate nemesis
```

See [`docs/setup.md`](docs/setup.md) for full environment setup, and each pipeline's guide under [`docs/guides/`](docs/guides/) for its exact invocation.

## Repository structure

```
config/           # JSON configs driving the pipelines (per-run request + naming registries)
src/
├── features/       # feature-matrix construction (lesion, FC, SDC, clinical)
├── analysis/       # dimensionality reduction, clustering, plotting, exploration apps
├── utils/          # shared I/O, logging, run-history helpers
└── pipeline/       # CLI entry points, one per pipeline
scripts/          # accessory utilities (cache maintenance, tables, derived indices), never analysis steps
jobs/             # one sbatch job script per pipeline, for cluster runs
tests/
├── unit/          # synthetic fixtures, no external data required
└── integration/   # against the real EBRAIN mount / tmp_path E2E, self-skipping if unreachable
docs/
├── setup.md       # environment setup
├── guides/        # how to use each pipeline (user-facing)
├── dev/           # architecture/implementation reference (developer-facing)
├── experiments/   # per-session run logs and cross-run experiment notes
└── debugging/     # dated, per-session debug reports
notebooks/        # exploration, pipeline prototyping, post-results analysis (index: docs/guides/exploration.md)
assets/
├── atlases/       # reference brain atlases
└── metadata/      # curated per-dataset clinical/demographic metadata
management/
├── meetings/      # raw dated meeting notes (primary source for project scope/decisions)
└── notes/         # working notes, TODOs
knowledge/        # reference literature, one folder per paper, extracted via docling
data/             # local copy of raw + derived data (gitignored, not in repo)
results/          # dimensionality-reduction/clustering outputs (gitignored, not in repo)
summaries/, logs/  # per-run outputs of the pipelines (gitignored)
.claude/          # agent-facing project instructions and conventions
```

Raw neuroimaging data (`*.nii`, `*.nii.gz`) is never stored in this repo — it lives on EBRAIN (`/data/corbetta/Clinical_connectome`) and is copied locally into `data/` by hand.

## What's implemented so far

### Retired pipelines
Three pipelines existed and have been removed; their code stays in `git log`, and no guide documents them anymore.

- **Data retrieval** (`retrieve_data.py`, `src/retrieval/`): copied lesion masks, FC features and SDC output from EBRAIN into `data/`. Data is now copied by hand; the subject-naming rule it carried lives on in `src/utils/subject_ids.py` ([`docs/guides/datasets.md`](docs/guides/datasets.md)).
- **SDC computation** (`compute_sdc.py`, `src/sdc/`): ran BCBToolKit Stage 1 + Stage 2 over the lesion masks on the cluster. The SDC output it produced is what `build_sdc_matrix.py` reads.
- **Atlas building** (`build_combined_atlas.py`, `src/atlases/`): combined-atlas construction for a parcellation-then-varimax-PCA replication, no longer pursued.

### FC lesion masking and matrix building
`src/features/functional.py`, `src/pipeline/mask_fc.py` + `build_fc_matrix.py` — two deliberately decoupled pipelines that turn the WashU functional-connectivity CSVs (already computed via XCP-D, 12 atlas combos) into a subjects × edges feature matrix ready for `dim_reduction.py`. `mask_fc.py` marks as missing (`NaN`, not zero — see [`docs/dev/fc_matrix.md`](docs/dev/fc_matrix.md) for why) any FC node whose territory is substantially lesioned (`nilearn`-based coverage check, same `min_coverage` scheme as XCP-D's own BOLD-coverage thresholding), writing one masked matrix per subject to `data/derived/features/masked_fc/`; `build_fc_matrix.py` reads only that already-masked output, vectorizes and stacks it into `data/derived/features/fc_matrix/`. The per-subject exclusion threshold question is settled (no threshold, no subject excluded); NaN-imputation remains deliberately open, pending an empirical look at the full cohort.

📖 Guides: [`fc_matrix_building.md`](docs/guides/fc_matrix_building.md) · Architecture: [`docs/dev/fc_matrix.md`](docs/dev/fc_matrix.md)

### SDC feature matrix building
`src/features/sdc.py`, `src/pipeline/build_sdc_matrix.py` — turns the SDC output (`sdc/<subject_id>/*`, computed upstream with BCBToolKit) into a feature matrix ready for `dim_reduction.py` (Task 2), in any of three representations picked by `config.representation`: **parcellated** (the already-parcellated per-atlas CSV output, one row per anatomical region, subjects × regions — alignment by region name via `pandas.reindex` against a fixed, authoritative region list in `assets/atlases/sdc_labels/<atlas>.csv`, not by row position, since CSV rows aren't in a stable order across subjects and BCBToolKit omits zero-overlap regions rather than writing them explicitly, both verified empirically; no column ever dropped, so a run's column meaning stays stable across subject selections) **voxelwise** (the pre-parcellation `disconnectome-map` `.nii.gz` directly, resampled onto a common grid same as the lesion voxel matrix, subjects × voxels, continuous disconnection values never binarized, constant columns dropped) or **streamline** (the `yeh_hcp1065_streamline` CSV, subjects × 87 white matter tracts, one `streamline_ratio` per tract — aligned by tract name like the parcellated one, but a *missing* tract raises instead of being filled with zero, since that file writes every tract explicitly). Every representation admits a subject only if it has both a lesion mask registered in the subject registry (`assets/metadata/participants.csv`, column `has_lesion` — not a glob against local disk, since a local `data/` copy can be a partial local sample) and the requested SDC output — a subject with SDC output but no registered lesion mask is excluded explicitly, never folded in as a false all-zero row.

📖 Guide: [`docs/guides/sdc_matrix_building.md`](docs/guides/sdc_matrix_building.md) · Architecture: [`docs/dev/sdc_matrix.md`](docs/dev/sdc_matrix.md)

### Clinical metadata
Every clinical/demographic value lives in one checked-in source of truth, `assets/metadata/participants.csv` — one row per subject, written by two scripts that never overwrite each other's columns.

`src/pipeline/populate_metadata.py` writes **who exists**: it joins each dataset's raw `participants.tsv` (`data/clinical_connectome/metadata_tsv/`, paths declared in `config/registry/metadata_sources.json`) against the subject folders actually on disk, one row per subject with `has_lesion`/`has_sdc`/`has_features` flags. `src/pipeline/enrich_metadata.py` adds **what we know about them** — age, sex, education, lesion_side, NIHSS, clinical_date, plus `lesion_volume_voxels_2mm`. The join onto the raw tsvs goes through `original_id`, since UCL-UK's raw `participant_id` is a legacy site id rather than the canonical subject id.

`enrich_metadata.py` computes nothing from imaging: it is a **join**. Everything measured on a lesion mask comes from a third file, `assets/metadata/lesion_metadata.csv`, written by `src/pipeline/compute_lesion_metadata.py` — one row per subject with a mask, and four columns per voxel grid (`lesion_volume_voxels_<g>`, `out_of_brain_fraction_<g>`, `laterality_index_<g>`, `lesion_side_<g>`), measured on both the 1mm grid the masks are natively on and the 2mm production grid. A fourth file, `assets/metadata/sdc_metadata.csv`, is its counterpart for the disconnectome, written by `src/pipeline/compute_sdc_metadata.py`: two columns per subject on each of the 2mm and 1mm grids (the disconnection probability summed over the brain, and its mean over the brain), which `enrich_metadata.py` joins into `participants.csv` and the Embedding Explorer offers as two colour buttons, with the same 1mm/2mm choice it offers for lesion volume. A fifth file, `assets/metadata/excluded_subjects.csv`, is generated by `src/pipeline/build_excluded_subjects.py` from the subjects listed explicitly in its config (`notebooks/exploration/lesion_analysis.ipynb` prints the blocks to paste there), and is the single admission list both matrix pipelines read, so they exclude exactly the same subjects.

📖 Guide: [`docs/guides/metadata.md`](docs/guides/metadata.md) · Architecture: [`docs/dev/metadata.md`](docs/dev/metadata.md)

Consumers read the registry directly rather than carrying copies: `build_sdc_matrix.py` takes its `has_lesion` admission criterion from it, and `dim_reduction.py`/`clustering.py`'s `side`/`nihss` colouring resolves against it at plot time — so a run gets those colours whether or not any enrichment step was ever applied to it.

`lesion_side` carries its own provenance in `lesion_side_source`: `"clinical"` where a dataset records it, `"geometric"` where it is filled from the mask's own laterality index against a threshold calibrated on 1445 clinically-labelled subjects (97.4% agreement on the 2mm grid). A clinical value is never overwritten by a geometric one. Still open: that threshold is verified on the 2mm grid only, so the 1mm side column is indicative until it is re-calibrated there ([`knowledge/neuroimaging/lesion_laterality.md`](knowledge/neuroimaging/lesion_laterality.md)).

📖 How it works, what's in the file, and what's left: [`docs/dev/metadata.md`](docs/dev/metadata.md) · Guide: [`docs/guides/metadata.md`](docs/guides/metadata.md)

### Dimensionality reduction and clustering
`src/analysis/`, `src/pipeline/dim_reduction.py`/`clustering.py` — reduces a feature matrix (lesion voxels today) to a low-dimensional embedding (`umap`/`tsne`/`pca`/`pacmap` — `pca_varimax` is implemented in code but has no `params_reduction.json` entry yet, so it isn't reachable via the CLI today) and/or clusters it (`kmeans`/`agglomerative`/`gmm`/`hdbscan`/`spectral`/`evidence_accumulation`) — two separate steps (`clustering.py --reduced_data true` on a `dim_reduction.py` output). Each script has a manual fine-tuning mode (`fine_tuning: true` — sweeps hyperparameters, writes a comparison table/plot, never picks automatically) and a production mode; production output includes static/interactive embedding and cluster scatter plots (`dim_reduction.py`: configurable coloring by dataset/lesion side/volume; `clustering.py`: cluster-colored only), a per-sample silhouette diagnostic, and a per-method `runs.csv` run history.

Each production/tuning run is tagged with a **session id** (`sX.Y[-<format>]` — track/cohort plus a mandatory format suffix, e.g. `s1.1-vol` for volumetric lesion data, `s2.1-schaefer-200-tian-s2` for SDC parcellated on that atlas) documented one entry per session in [`docs/experiments/data_sessions.md`](docs/experiments/data_sessions.md).

📖 Guides: [`dim_reduction.md`](docs/guides/dim_reduction.md) · [`clustering.md`](docs/guides/clustering.md)
📚 Methodology/literature: [`knowledge/dim_reduction_clustering/`](knowledge/dim_reduction_clustering/)
🏗️ Architecture: [`models.md`](docs/dev/models.md) · [`config.md`](docs/dev/config.md) · [`plotting.md`](docs/dev/plotting.md)

### Embedding exploration tools
`src/analysis/embedding_app.py`, `src/pipeline/embedding_app.py`/`generate_understanding_umap_report.py` — two complementary viewers, neither a modeling pipeline itself. `embedding_app.py` is a live local Dash app that browses every already-saved `dim_reduction.py`/`clustering.py` production run (2D/3D scatter, color-mode picker, interactive per-subject/per-cluster anatomy panels). `generate_understanding_umap_report.py` renders a static, PAIR-style HTML report from an existing UMAP/t-SNE fine-tuning sweep (parameter grid, dual-slider explorer, UMAP-vs-t-SNE comparison) for non-technical readers.

📖 Guides: [`embedding_app.md`](docs/guides/embedding_app.md) · [`understanding_umap_report.md`](docs/guides/understanding_umap_report.md)

---

Task 1 (lesion embedding/clustering) is the most mature piece above; Task 2's embedding runs on SDC features once `build_sdc_matrix.py` output is available at scale (the builder itself is done, a full-cohort production run is not yet), Task 3 (fMRI-based clustering) once FC matrices are built at scale — both reuse the same `dim_reduction`/`clustering` pipelines, not separate code. Task 4 (EEG) is deferred to Sept/Oct 2026. Task 5 (correlating features with clinical-behavioral outcomes) has early exploratory code (`src/analysis/prediction.py`) but no CLI entry point/pipeline/docs yet.

## Environment

Conda environment **`nemesis`**, defined in [`environment.yml`](environment.yml) (numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn). See [`docs/setup.md`](docs/setup.md) for creating/updating it — [Quick start](#quick-start) above covers the common case.

## Contributing / development conventions

Code standards (architecture, error handling, testing, config, logging) are defined in [`.claude/code_standards.md`](.claude/code_standards.md) and apply to everything under `src/`. `.claude/lessons_learned.md` is a running, concise index of recurring bug patterns and best practices found while working on this repo — worth a read before writing new pipeline code.
