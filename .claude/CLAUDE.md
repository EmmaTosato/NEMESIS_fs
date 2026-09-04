# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is the working repo for **NEMESIS**, a stroke neuroimaging research project (Corbetta lab) building low-dimensional embeddings of stroke lesions and structural/functional disconnectomes, clustering them, and relating clusters to clinical-behavioral outcomes (NIHSS, language, neglect, motor domains). Data retrieval, atlas building, SDC computation, and the embedding/clustering analysis pipeline are implemented under `src/` (see `README.md`'s "What's implemented so far" for the current picture) with a `pytest` suite under `tests/unit/`/`tests/integration/` — see `code_standards.md` §4 for testing conventions.

## Environment

Conda environment **`nemesis`**, defined in `environment.yml` at repo root (numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn). Activate with:

```bash
conda activate nemesis
```

Create/update it from `environment.yml` (see `docs/setup.md` for details). Raw neuroimaging data (`*.nii`, `*.nii.gz`, gitignored) is not stored in this repo — it lives on EBRAIN (paths documented in `docs/guides/datasets.md`).

**SDC pipeline (`src/sdc/`, `src/pipeline/compute_sdc.py`) cannot be run or tested locally**: it imports `bcblib` (BCBToolKit), a tool installed only in the cluster's conda environment, not in any local `nemesis` env (this Mac included). `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fail at collection with `ModuleNotFoundError: No module named 'bcblib'` outside the server — this is an environment gap, not a code regression; don't try to fix/install around it locally, and exclude those two files (`pytest --ignore=...`) when running the suite outside the cluster.

## Running pipelines (local vs. SLURM)

Two supported ways to invoke a pipeline entry point (`src/pipeline/*.py`, `scripts/*.py`) — every guide under `docs/guides/` documents both for its own pipeline:

- **Local, direct (current default)**: `conda activate nemesis`, `cd` to the repo root, then the exact invocation from that pipeline's guide (`python -m src.pipeline...` for `src/pipeline/`, `PYTHONPATH="$PROJECT_ROOT" python scripts/...` for `scripts/`, since those aren't run with `-m`). Pipelines run directly like this for now — don't propose `sbatch`/cluster jobs unless the user asks for it, or a run genuinely needs cluster-scale resources.
- **On the shared cluster, via `sbatch`** (production/full-scale runs, or anything that must survive a closed SSH connection): submitted through a job script at `jobs/run_<pipeline_name>.sh` — a single file directly under `jobs/`, not a per-pipeline subfolder (only switch a pipeline to a `jobs/<name>/` subfolder if it genuinely needs more than one `.sh` script) — never invoked directly (no bare `python`/`conda run` on the login node). `jobs/run_retrieve_data.sh` is the reference example; `jobs/run_verify_retrieval.sh` follows the same shape:
  - `#SBATCH` header (job name, partition, cpus/mem/time, `-o`/`-e` pointing at `logs/slurm/<pipeline_name>/%j.{out,err}`) — that log directory must already exist before `sbatch` submission, SLURM does not create it.
  - `source .../conda.sh && conda activate nemesis`, then `cd` to the repo root.
  - The same invocation as the local case, taken from the pipeline's guide.

Resource values in `jobs/` are conservative starting points (this is I/O-bound file-copying work, not compute-heavy), not fixed — adjust `--cpus-per-task`/`--mem`/`-t` per job as needed. When a new pipeline/script is added under `src/pipeline/` or `scripts/`, add a matching `jobs/run_<name>.sh` at the same time, not as an afterthought — it's needed the moment that pipeline runs on the cluster, even if only run locally for now.

## Repository structure

- `docs/` — stable, incremental project documentation (distinct from raw meeting notes, which live under `assets/`):
  - `README.md` (repo root) — project goal, hypothesis, Task 1-5 breakdown, and the current "what's implemented so far" picture
  - `docs/guides/` — user-facing "how do I run this" guides, one per pipeline (`retrieval.md`, `matrix_building.md`, `fc_matrix_building.md`, `sdc_matrix_building.md` (27-08-26, `build_sdc_matrix.py`), `dim_reduction.md`, `clustering.md`, `compute_sdc.md`, `embedding_app.md`, `understanding_umap_report.md`, `evaluation.md` (28-08-26, `notebooks/post-results_analysis/clustering_evaluation.ipynb` - human-in-the-loop cross-run clustering comparison, not a pipeline CLI) — `dim_reduction_clustering.md` retired 14-08-26 along with the one-shot CLI it documented, see `docs/dev/clustering_migration_plan.md`; `atlas_building.md` retired 25-08-26 along with the `build_combined_atlas.py` pipeline it documented, see `management/notes/TODO.md`) plus `datasets.md` (EBRAIN paths, per-dataset N, per-subject folder structure, `participants.tsv` conventions)
  - `docs/dev/` — developer-facing architecture/implementation reference per module (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `sdc_matrix.md` (27-08-26), `anatomical_maps.md` (03-09-26, `src/analysis/anatomical_maps.py` + `embedding_app.py`'s anatomy panels), `design_patterns.md`), kept current as each piece lands — not a restatement of any original plan
  - `docs/notes/` no longer exists (dissolved in the `docs/dr-clustering-literature-migration` merge, 18-08-26) — its former content (per-method guides, literature/reproduction notes, tuning-output reading guides) now lives under `knowledge/dim_reduction_clustering/` (dim-reduction/clustering methodology and literature) and `knowledge/neuroimaging/` (e.g. `fc_lesion_masking.md`), both alongside the extracted-paper folders under `knowledge/`
  - `docs/debugging/` — dated, per-session debug reports (see `code_standards.md` §8)
  - `docs/setup.md` — environment setup instructions
- `management/meetings/` — raw meeting notes (markdown, dated). Primary source for anything not yet reflected in `docs/` — check here when `docs/` seems incomplete or you need the original context/wording behind a decision. Prefer the most recent note over older ones when they conflict, and treat `docs/` as the up-to-date synthesis.
- `knowledge/` — one subfolder per reference paper (named `<Author> et al - <Year> - <Title>`), extracted from PDFs via a docling-based pipeline. `knowledge/paper_lists.md` is the index of all papers with full citations.
  - Within each paper folder: `markdown/_full.md` is the full extracted text (read this for paper content) — `manifest.json` and `figures.json` describe extraction metadata and page/figure mapping, `figures/` holds page-level SVG/PNG renders. Not every folder has a full docling extraction (e.g. `chunks.jsonl`, `tables.json`, `docling_document.json` referenced in `manifest.json` are frequently absent) — check what's actually present rather than assuming the full file set from the manifest.
- `src/` — project source code: `retrieval/`, `atlases/`, `features/`, `sdc/`, `analysis/`, `utils/`, and `pipeline/` (CLI entry points).
- `scripts/` — accessory/one-off scripts (data organization, setup utilities), not the main pipeline code.
- `jobs/` — one `sbatch` job script per `src/pipeline/`/`scripts/` entry point, for cluster runs (see "Running pipelines (local vs. SLURM)" above).

## Working in this repo

- Treat `README.md` + `docs/guides/`/`docs/dev/` as the current-state synthesis of project goals/scope, and `management/meetings/` + `knowledge/*/markdown/_full.md` as the primary sources behind it — cross-reference the originals when reasoning about project design or when `docs/` doesn't cover something.
- When new papers are added under `knowledge/`, add them to `knowledge/paper_lists.md` for consistency with the existing index.
- **Never make git commits automatically**. Do not run `git commit` unless explicitly requested by the user.

## Code standards

@code_standards.md

Applies to any code written under `src/` (and its tests in `tests/`): architecture, error handling (no silent fallbacks — every edge case raises or is handled deliberately), testing, config, logging, docs conventions.

## Lessons learned

@lessons_learned.md

Cumulative, concise index of recurring error patterns and best practices found while debugging or reviewing this repo's code — one entry per pattern, never duplicated across sessions. Read it before starting a debugging session or writing new code in `src/`. Updated after every debugging session per `code_standards.md` §8.
