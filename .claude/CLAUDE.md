# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is the working repo for **NEMESIS**, a stroke neuroimaging research project (Corbetta lab) building low-dimensional embeddings of stroke lesions and structural/functional disconnectomes, clustering them, and relating clusters to clinical-behavioral outcomes (NIHSS, language, neglect, motor domains). There is no source code yet, so no build/lint/test commands exist — see conventions below for where code will go.

## Environment

Conda environment **`nemesis`**, defined in `environment.yml` at repo root (numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn). Activate with:

```bash
conda activate nemesis
```

Create/update it from `environment.yml` (see `docs/setup.md` for details). Raw neuroimaging data (`*.nii`, `*.nii.gz`, gitignored) is not stored in this repo — it lives on EBRAIN (paths documented in `docs/project/datasets.md`).

## Running pipelines (SLURM)

This project runs on a shared cluster: every Python pipeline/script entry point (`src/pipeline/*.py`, `scripts/*.py`) is launched through an `sbatch` job script under `jobs/<pipeline_name>/run_<pipeline_name>.sh` — never invoked directly (no bare `python`/`conda run` on the login node). `jobs/retrieve_data/run_retrieve_data.sh` is the reference example; `jobs/data_summary/` and `jobs/verify_retrieval/` follow the same shape:

- `#SBATCH` header (job name, partition, cpus/mem/time, `-o`/`-e` pointing at `logs/slurm/<pipeline_name>/%j.{out,err}`) — that log directory must already exist before `sbatch` submission, SLURM does not create it.
- `source .../conda.sh && conda activate nemesis`, then `cd` to the repo root.
- The exact invocation documented in `docs/guides/` for that entry point (`python -m src.pipeline...` for `src/pipeline/`, `PYTHONPATH="$PROJECT_ROOT" python scripts/...` for `scripts/`, since those aren't run with `-m`).

Resource values in `jobs/` are conservative starting points (this is I/O-bound file-copying work, not compute-heavy), not fixed — adjust `--cpus-per-task`/`--mem`/`-t` per job as needed. When a new pipeline/script is added under `src/pipeline/` or `scripts/`, add a matching `jobs/<name>/run_<name>.sh` at the same time, not as an afterthought.

## Repository structure

- `docs/` — stable, incremental project documentation (distinct from raw meeting notes, which live under `assets/`):
  - `docs/project/overview.md` — project goal, hypothesis, pointers to tasks/datasets
  - `docs/project/tasks.md` — Task 1-5 breakdown and workflow, kept current as scope evolves
  - `docs/project/datasets.md` — EBRAIN paths, per-dataset N, per-subject folder structure, `participants.tsv` conventions (HC/ST)
  - `docs/methods/` — reserved for methodology write-ups (SDC/BCBtoolkit, embedding/clustering, clinical interpretation) once formalized; empty for now, don't assume files exist here without checking
  - `docs/setup.md` — environment setup instructions
- `assets/meetings/` — raw meeting notes (markdown, dated). Primary source for anything not yet reflected in `docs/project/` — check here when `docs/` seems incomplete or you need the original context/wording behind a decision. Prefer the most recent note over older ones when they conflict, and treat `docs/project/` as the up-to-date synthesis once it exists.
- `assets/papers/` — one subfolder per reference paper (named `<Author> et al - <Year> - <Title>`), extracted from PDFs via a docling-based pipeline. `assets/papers/paper_lists.md` is the index of all papers with full citations.
  - Within each paper folder: `markdown/_full.md` is the full extracted text (read this for paper content) — `manifest.json` and `figures.json` describe extraction metadata and page/figure mapping, `figures/` holds page-level SVG/PNG renders. Not every folder has a full docling extraction (e.g. `chunks.jsonl`, `tables.json`, `docling_document.json` referenced in `manifest.json` are frequently absent) — check what's actually present rather than assuming the full file set from the manifest.
- `src/` — project source code (pipelines: SDC, embedding, clustering, etc.) once written.
- `scripts/` — accessory/one-off scripts (data organization, setup utilities), not the main pipeline code.
- `jobs/` — one `sbatch` job script per `src/pipeline/`/`scripts/` entry point (see "Running pipelines (SLURM)" above).

## Working in this repo

- Treat `docs/project/` as the current-state synthesis of project goals/scope, and `assets/meetings/` + `assets/papers/*/markdown/_full.md` as the primary sources behind it — cross-reference the originals when reasoning about project design or when `docs/` doesn't cover something.
- When new papers are added under `assets/papers/`, add them to `assets/papers/paper_lists.md` for consistency with the existing index.

## Code standards

@code_standards.md

Applies to any code written under `src/` (and its tests, once they exist): architecture, error handling (no silent fallbacks — every edge case raises or is handled deliberately), testing, config, logging, docs conventions.

## Lessons learned

@lessons_learned.md

Cumulative, concise index of recurring error patterns and best practices found while debugging or reviewing this repo's code — one entry per pattern, never duplicated across sessions. Read it before starting a debugging session or writing new code in `src/`. Updated after every debugging session per `code_standards.md` §8.
