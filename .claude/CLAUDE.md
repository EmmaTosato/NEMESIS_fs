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

## Working in this repo

- Treat `docs/project/` as the current-state synthesis of project goals/scope, and `assets/meetings/` + `assets/papers/*/markdown/_full.md` as the primary sources behind it — cross-reference the originals when reasoning about project design or when `docs/` doesn't cover something.
- When new papers are added under `assets/papers/`, add them to `assets/papers/paper_lists.md` for consistency with the existing index.
