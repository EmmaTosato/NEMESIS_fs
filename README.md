# NEMESIS

Data-driven stroke research project (Corbetta lab) building a **multimodal low-dimensional representation of stroke**: embedding lesions and structural/functional disconnectomes, clustering them, and relating the resulting clusters to clinical-behavioral outcomes (NIHSS, language, neglect, motor domains).

**Core hypothesis**: how different modalities (anatomical, structural, functional, physiological/EEG) overlap in explaining post-stroke deficit — informed by prior work (Corbetta 2015, Bisogno 2021, Talozzi 2023) showing that post-stroke deficits and disconnectome patterns are both low-dimensional, and that disconnection — not raw lesion location — best explains cross-domain behavioral impairment.

## Task breakdown

- **Task 1** — low-dimensional embedding of lesions (n~4000) + topographic clustering
- **Task 2** — low-dimensional embedding of structural disconnection / SDC (n~3000)
- **Task 3** — clustering on n~500 with fMRI (WashU + Padova + Freiburg), compared against healthy controls
- **Task 4** — EEG (n~80, Padova) — deferred to Sept/Oct 2026
- **Task 5** — correlating multimodal/multiscale features with behavioral outcomes (n~60)

## Repository structure

```
config/           # JSON configs driving the pipelines (data retrieval request + file-naming registry)
src/
├── retrieval/    # Dataset access layer: config parsing, per-dataset file resolution
└── pipeline/     # CLI entry points (e.g. retrieve_data.py)
scripts/          # accessory/one-off scripts, not the main pipeline
tests/
├── unit/         # synthetic fixtures, no external data required
└── integration/  # against the real EBRAIN mount, skipped automatically if unreachable
docs/
├── methods/      # methodological documentation and literature notes
├── setup.md      # environment setup
├── guides/       # how to use each pipeline (user-facing)
├── dev/          # architecture/implementation reference (developer-facing)
└── debugging/    # dated, per-session debug reports
assets/
├── atlases/      # Reference brain atlases
└── metadata/     # Project metadata
management/
├── meetings/     # raw dated meeting notes (primary source for project scope/decisions)
└── nemesis_project/ # project administrative documents
papers/           # reference literature, one folder per paper, extracted via docling
data/             # local copy of retrieved neuroimaging data (gitignored, not in repo)
summaries/, logs/   # per-run outputs of the pipelines (gitignored)
.claude/          # agent-facing project instructions and conventions (see below)
```

Raw neuroimaging data (`*.nii`, `*.nii.gz`) is never stored in this repo — it lives on EBRAIN (`/data/corbetta/Clinical_connectome`) and is copied locally into `data/` on demand by the retrieval pipeline.

## Environment

Conda environment **`nemesis`**, defined in [`environment.yml`](environment.yml). See [`docs/setup.md`](docs/setup.md) for creating/updating it. Quick start:

```bash
conda env create -f environment.yml
conda activate nemesis
```

## What's implemented so far

**Data retrieval** (`src/retrieval/`, `src/pipeline/retrieve_data.py`): copies lesion data and `participants.tsv` from the 4 in-scope stroke datasets (`UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`) into `data/`, driven by `config/pipelines/retrieval_local.json`/[`retrieval_server.json`](config/pipelines/retrieval_server.json) (per-run request, one per environment) and `config/registry/file_patterns_local.json`/[`file_patterns_server.json`](config/registry/file_patterns_server.json) (naming registry, per `object` — `lesion` today, `feature` reserved for later):

```bash
conda activate nemesis
python -m src.pipeline.retrieve_data --config config/pipelines/retrieval_server.json
```

Every run writes a summary (`summaries/`) and a matching log (`logs/`) summarizing what was copied and flagging anything that needs a human look (missing files, non-conforming subject folders). A separate, read-only `scripts/data_summary.py` gives the full per-subject availability picture across every registered modality, independent of any one run. Full usage guide: [`docs/guides/retrieval.md`](docs/guides/retrieval.md). Architecture/design rationale: [`docs/dev/retrieval.md`](docs/dev/retrieval.md).

**Combined parcellation atlas** (`src/atlases/`, `src/pipeline/build_combined_atlas.py`): merges the Glasser MMP cortical atlas (360 parcels) with 12 manually-selected Harvard-Oxford subcortical structures (thalamus, caudate, putamen, pallidum, hippocampus, amygdala — left/right) into a single 372-region label volume, reproducing the parcellation used by Thiebaut de Schotten et al. 2020 ahead of their varimax PCA (their own 12 subcortical ROIs were hand-drawn and not published as a reusable atlas — Harvard-Oxford is a documented practical substitute, not a faithful reproduction):

```bash
conda activate nemesis
python -m src.pipeline.build_combined_atlas --config config/pipelines/build_combined_atlas.json
```

Writes the combined atlas (`assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz`) and a label lookup CSV (`..._372_labels.csv`, value/name/hemisphere/source), ready to use as-is via any pipeline's `atlas_path` config field.

**FC lesion masking and matrix building** (`src/features/functional.py`, `src/pipeline/mask_fc.py` + `build_fc_matrix.py`): two deliberately decoupled pipelines that turn the WashU functional-connectivity CSVs (already computed via XCP-D, 12 atlas combos) into a subjects × edges feature matrix ready for `dim_reduction.py`. `mask_fc.py` marks as missing (`NaN`, not zero — see [`docs/dev/fc_matrix.md`](docs/dev/fc_matrix.md) for why) any FC node whose territory is substantially lesioned (`nilearn`-based coverage check, same `min_coverage` scheme as XCP-D's own BOLD-coverage thresholding), writing one masked matrix per subject to `data/derived/features/masked_fc/`; `build_fc_matrix.py` reads only that already-masked output, vectorizes and stacks it into `data/derived/features/fc_matrix/`. The per-subject exclusion threshold question is settled (no threshold, no subject excluded); NaN-imputation remains deliberately open, pending an empirical look at the full cohort (`docs/dev/fc_matrix.md`).

**Structural disconnectome (SDC) computation** (`src/sdc/`, `src/pipeline/compute_sdc.py`): orchestrates BCBToolKit/BCBlib (Stage 1 + Stage 2) over every retrievable lesion mask in `clinical_connectome`, split into 3 CLI modes (`manifest`/`run`/`aggregate`) so per-subject work can be parallelized across SLURM tasks — a per-subject failure (Stage 1/2 crash, failed output check) doesn't stop the batch, only a structural one (bad config, missing tool path) does. Cannot be run or tested locally (needs `bcblib`, cluster-only — see "Environment" above). Full guide: [`docs/guides/compute_sdc.md`](docs/guides/compute_sdc.md).

**Dimensionality reduction and clustering** (`src/analysis/`, `src/pipeline/dim_reduction.py`/`clustering.py`/`dim_reduction_clustering.py`): reduces a feature matrix (lesion voxels today) to a low-dimensional embedding (`umap`/`tsne`/`pca`/`pca_varimax`/`pacmap`) and/or clusters it (`kmeans`/`agglomerative`/`gmm`/`hdbscan`/`spectral`/`rsc`) — either as two separate steps or one combined CLI. Each script has a manual fine-tuning mode (`fine_tuning: true` — sweeps hyperparameters, writes a comparison table/plot, never picks automatically) and a production mode; production output includes static/interactive embedding and cluster scatter plots (configurable coloring by dataset/lesion side/volume), a per-sample silhouette diagnostic, and a per-method `runs.csv` run history. Full guides: [`docs/guides/dim_reduction.md`](docs/guides/dim_reduction.md)/[`clustering.md`](docs/guides/clustering.md)/[`dim_reduction_clustering.md`](docs/guides/dim_reduction_clustering.md); methodology: [`docs/knowledge/dim_reduction.md`](docs/knowledge/dim_reduction.md)/[`clustering.md`](docs/knowledge/clustering.md); architecture: [`docs/dev/models.md`](docs/dev/models.md)/[`config.md`](docs/dev/config.md)/[`plotting.md`](docs/dev/plotting.md).

Task 1 (lesion embedding/clustering) is the most mature piece above; Task 2's embedding runs on SDC features once `compute_sdc.py` has a completed real run, Task 3 (fMRI-based clustering) once FC matrices are built at scale — both reuse the same `dim_reduction`/`clustering` pipelines, not separate code. Task 4 (EEG) is deferred to Sept/Oct 2026. Task 5 (correlating features with clinical-behavioral outcomes) has early exploratory code (`src/analysis/prediction.py`, `src/features/clinical.py`) but no CLI entry point/pipeline/docs yet.

## Contributing / development conventions

Code standards (architecture, error handling, testing, config, logging) are defined in [`.claude/code_standards.md`](.claude/code_standards.md) and apply to everything under `src/`. `.claude/lessons_learned.md` is a running, concise index of recurring bug patterns and best practices found while working on this repo — worth a read before writing new pipeline code.
