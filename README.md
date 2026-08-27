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
knowledge/           # reference literature, one folder per paper, extracted via docling
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

**Data retrieval** (`src/retrieval/`, `src/pipeline/retrieve_data.py`): copies lesion data and `participants.tsv` from the in-scope stroke datasets (see [`docs/guides/datasets.md`](docs/guides/datasets.md) for the current list) into `data/`, driven by `config/pipelines/retrieval_local.json`/[`retrieval_server.json`](config/pipelines/retrieval_server.json) (per-run request, one per environment) and `config/registry/file_patterns_local.json`/[`file_patterns_server.json`](config/registry/file_patterns_server.json) (naming registry, per `object` — `lesion`, `feature`, and `sdc`, see below). A dedicated `config/pipelines/retrieval_sdc.json` retrieves structural disconnectome output (the same BCBToolKit Stage1+Stage2 computation `src/sdc/`/`compute_sdc.py` itself performs, just not run through our own `--mode manifest/run/aggregate` orchestration for this particular run) for `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, and a new 6th site, `UKE/WAKEUP_acute` — lands locally under `sdc/` (see `docs/dev/retrieval.md`, `docs/guides/datasets.md`):

```bash
conda activate nemesis
python -m src.pipeline.retrieve_data --config config/pipelines/retrieval_server.json
```

Every run writes a summary (`summaries/`) and a matching log (`logs/`) summarizing what was copied and flagging anything that needs a human look (missing files, non-conforming subject folders). A separate, read-only `scripts/data_summary.py` gives the full per-subject availability picture across every registered modality, independent of any one run. Full usage guide: [`docs/guides/retrieval.md`](docs/guides/retrieval.md). Architecture/design rationale: [`docs/dev/retrieval.md`](docs/dev/retrieval.md).

Writes the combined atlas (`assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz`) and a label lookup CSV (`..._372_labels.csv`, value/name/hemisphere/source), ready to use as-is via any pipeline's `atlas_path` config field.

**FC lesion masking and matrix building** (`src/features/functional.py`, `src/pipeline/mask_fc.py` + `build_fc_matrix.py`): two deliberately decoupled pipelines that turn the WashU functional-connectivity CSVs (already computed via XCP-D, 12 atlas combos) into a subjects × edges feature matrix ready for `dim_reduction.py`. `mask_fc.py` marks as missing (`NaN`, not zero — see [`docs/dev/fc_matrix.md`](docs/dev/fc_matrix.md) for why) any FC node whose territory is substantially lesioned (`nilearn`-based coverage check, same `min_coverage` scheme as XCP-D's own BOLD-coverage thresholding), writing one masked matrix per subject to `data/derived/features/masked_fc/`; `build_fc_matrix.py` reads only that already-masked output, vectorizes and stacks it into `data/derived/features/fc_matrix/`. The per-subject exclusion threshold question is settled (no threshold, no subject excluded); NaN-imputation remains deliberately open, pending an empirical look at the full cohort (`docs/dev/fc_matrix.md`).

**Structural disconnectome (SDC) computation** (`src/sdc/`, `src/pipeline/compute_sdc.py`): orchestrates BCBToolKit/BCBlib (Stage 1 + Stage 2) over every retrievable lesion mask in `clinical_connectome`, split into 3 CLI modes (`manifest`/`run`/`aggregate`) so per-subject work can be parallelized across SLURM tasks — a per-subject failure (Stage 1/2 crash, failed output check) doesn't stop the batch, only a structural one (bad config, missing tool path) does. Cannot be run or tested locally (needs `bcblib`, cluster-only — see "Environment" above). Full guide: [`docs/guides/compute_sdc.md`](docs/guides/compute_sdc.md).

**SDC feature matrix building** (`src/features/sdc.py`, `src/pipeline/build_sdc_matrix.py`): turns `compute_sdc.py`'s already-parcellated per-atlas CSV output (`sdc/<subject_id>/dwi/*.csv`, one row per anatomical region) into a subjects × regions feature matrix ready for `dim_reduction.py` (Task 2). Alignment is by region name (`pandas.reindex` against a fixed, authoritative region list in `assets/atlases/sdc_labels/<atlas>.csv`), not by row position — CSV rows aren't in a stable order across subjects, and BCBToolKit omits zero-overlap regions rather than writing them explicitly (both verified empirically). A subject is admitted only if it has both a real lesion mask and the requested SDC output — a subject with SDC output but no lesion mask is excluded explicitly, never folded in as a false all-zero row. No column is ever dropped (unlike the lesion voxel matrix), so a run's column meaning stays stable across subject selections. Full guide: [`docs/guides/sdc_matrix_building.md`](docs/guides/sdc_matrix_building.md); architecture: [`docs/dev/sdc_matrix.md`](docs/dev/sdc_matrix.md).

**Dimensionality reduction and clustering** (`src/analysis/`, `src/pipeline/dim_reduction.py`/`clustering.py`): reduces a feature matrix (lesion voxels today) to a low-dimensional embedding (`umap`/`tsne`/`pca`/`pca_varimax`/`pacmap`) and/or clusters it (`kmeans`/`agglomerative`/`gmm`/`hdbscan`/`spectral`/`evidence_accumulation`) — two separate steps (`clustering.py --reduced_data true` on a `dim_reduction.py` output; the one-shot combined CLI, `dim_reduction_clustering.py`, was retired 14-08-26, see [`docs/dev/clustering_migration_plan.md`](docs/dev/clustering_migration_plan.md)). Each script has a manual fine-tuning mode (`fine_tuning: true` — sweeps hyperparameters, writes a comparison table/plot, never picks automatically) and a production mode; production output includes static/interactive embedding and cluster scatter plots (`dim_reduction.py`: configurable coloring by dataset/lesion side/volume; `clustering.py`: cluster-colored only), a per-sample silhouette diagnostic, and a per-method `runs.csv` run history. Full guides: [`docs/guides/dim_reduction.md`](docs/guides/dim_reduction.md)/[`clustering.md`](docs/guides/clustering.md); methodology/literature: [`knowledge/dim_reduction_clustering/`](knowledge/dim_reduction_clustering/) (`dim_reduction_literature_survey.md`, `dim_reduction_tuning_guide.md`, `clustering_literature_survey.md`, `clustering_tuning_guide.md`, `challenge_of_clustering_after_dim_reduction.md`); architecture: [`docs/dev/models.md`](docs/dev/models.md)/[`config.md`](docs/dev/config.md)/[`plotting.md`](docs/dev/plotting.md).

**Embedding exploration tools** (`src/analysis/embedding_app.py`, `src/pipeline/embedding_app.py`/`generate_understanding_umap_report.py`): two complementary viewers, neither a modeling pipeline itself. `embedding_app.py` is a live local Dash app that browses every already-saved `dim_reduction.py`/`clustering.py` production run (2D/3D scatter, color-mode picker) — full guide: [`docs/guides/embedding_app.md`](docs/guides/embedding_app.md). `generate_understanding_umap_report.py` renders a static, PAIR-style HTML report from an existing UMAP/t-SNE fine-tuning sweep (parameter grid, dual-slider explorer, UMAP-vs-t-SNE comparison) for non-technical readers — full guide: [`docs/guides/understanding_umap_report.md`](docs/guides/understanding_umap_report.md).

Task 1 (lesion embedding/clustering) is the most mature piece above; Task 2's embedding runs on SDC features once `build_sdc_matrix.py` output is available at scale (see above — the builder itself is done, a full-cohort production run is not yet), Task 3 (fMRI-based clustering) once FC matrices are built at scale — both reuse the same `dim_reduction`/`clustering` pipelines, not separate code. Task 4 (EEG) is deferred to Sept/Oct 2026. Task 5 (correlating features with clinical-behavioral outcomes) has early exploratory code (`src/analysis/prediction.py`, `src/features/clinical.py`) but no CLI entry point/pipeline/docs yet.

## Contributing / development conventions

Code standards (architecture, error handling, testing, config, logging) are defined in [`.claude/code_standards.md`](.claude/code_standards.md) and apply to everything under `src/`. `.claude/lessons_learned.md` is a running, concise index of recurring bug patterns and best practices found while working on this repo — worth a read before writing new pipeline code.
