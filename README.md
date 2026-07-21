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
├── setup.md      # environment setup
├── guides/       # how to use each pipeline (user-facing)
├── dev/          # architecture/implementation reference (developer-facing)
└── debugging/    # dated, per-session debug reports
assets/
├── meetings/     # raw dated meeting notes (primary source for project scope/decisions)
├── papers/       # reference literature, one folder per paper, extracted via docling
└── notes/        # non-normative scratch notes (e.g. architecture drafts)
data/             # local copy of retrieved neuroimaging data (gitignored, not in repo)
reports/, logs/   # per-run outputs of the pipelines (gitignored)
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

Every run writes a report (`reports/`) and a matching log (`logs/`) summarizing what was copied and flagging anything that needs a human look (missing files, non-conforming subject folders). A separate, read-only `scripts/data_summary.py` gives the full per-subject availability picture across every registered modality, independent of any one run. Full usage guide: [`docs/guides/retrieval.md`](docs/guides/retrieval.md). Architecture/design rationale: [`docs/dev/retrieval.md`](docs/dev/retrieval.md).

**Combined parcellation atlas** (`src/atlases/`, `src/pipeline/build_combined_atlas.py`): merges the Glasser MMP cortical atlas (360 parcels) with 12 manually-selected Harvard-Oxford subcortical structures (thalamus, caudate, putamen, pallidum, hippocampus, amygdala — left/right) into a single 372-region label volume, reproducing the parcellation used by Thiebaut de Schotten et al. 2020 ahead of their varimax PCA (their own 12 subcortical ROIs were hand-drawn and not published as a reusable atlas — Harvard-Oxford is a documented practical substitute, not a faithful reproduction):

```bash
conda activate nemesis
python -m src.pipeline.build_combined_atlas --config config/pipelines/build_combined_atlas.json
```

Writes the combined atlas (`assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz`) and a label lookup CSV (`..._372_labels.csv`, value/name/hemisphere/source), ready to use as-is via any pipeline's `atlas_path` config field.

Everything past this (SDC computation, embedding, clustering, clinical correlation — Tasks 1-5 above) is not yet implemented.

## Contributing / development conventions

Code standards (architecture, error handling, testing, config, logging) are defined in [`.claude/code_standards.md`](.claude/code_standards.md) and apply to everything under `src/`. `.claude/lessons_learned.md` is a running, concise index of recurring bug patterns and best practices found while working on this repo — worth a read before writing new pipeline code.
