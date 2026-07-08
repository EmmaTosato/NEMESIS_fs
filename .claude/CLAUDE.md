# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is not a software project — it's the working documentation repo for **NEMESIS**, a stroke neuroimaging research project (Corbetta lab) building low-dimensional embeddings of stroke lesions and structural/functional disconnectomes, clustering them, and relating clusters to clinical-behavioral outcomes (NIHSS, language, neglect, motor domains). There is currently no source code, build system, linter, or test suite. `scripts/` exists but is empty — future analysis code (the `.gitignore` entries for `__pycache__/`, `.ipynb_checkpoints/`, `*.pyc` indicate it will likely be Python/Jupyter based) will land there.

## Repository structure

- `docs/meetings/` — meeting notes (markdown) tracking project scope and decisions. Read these first to understand current project state, task definitions (Task 1-5), and dataset locations before doing any analysis work. Notes are dated at the top; the project's task breakdown and methodology evolve meeting to meeting, so prefer the most recent file over older ones when they conflict.
- `assets/papers/` — one subfolder per reference paper (named `<Author> et al - <Year> - <Title>`), extracted from PDFs via a docling-based pipeline. `assets/papers/paper_lists.md` is the index of all papers with full citations.
  - Within each paper folder: `markdown/_full.md` is the full extracted text (read this for paper content) — `manifest.json` and `figures.json` describe extraction metadata and page/figure mapping, `figures/` holds page-level SVG/PNG renders. Not every folder has a full docling extraction (e.g. `chunks.jsonl`, `tables.json`, `docling_document.json` referenced in `manifest.json` are frequently absent) — check what's actually present rather than assuming the full file set from the manifest.
- `.gitignore` excludes neuroimaging data (`*.nii`, `*.nii.gz`) — raw imaging data lives outside this repo (on EBRAIN, per `docs/meetings/`), not committed here.

## Working in this repo

- Treat `docs/meetings/` as the source of truth for project goals/scope and `assets/papers/*/markdown/_full.md` as the literature backing methodological decisions — cross-reference both when asked to reason about project design.
- When new papers are added under `assets/papers/`, add them to `assets/papers/paper_lists.md` for consistency with the existing index.
