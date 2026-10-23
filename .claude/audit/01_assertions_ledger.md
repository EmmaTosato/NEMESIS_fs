# 01 — Assertions ledger (memoria a lungo termine)

Formato: `- [ID] | Fonte: file:riga | Affermazione | Stato`
Stati: Verificato / Falso / Parziale / Da verificare in Fase 2 / Non verificabile (motivo)
Limite ambiente (2026-10-23): clone **shallow** (50 commit), niente conda, Python 3.13 senza numpy/sklearn → hash git storici e `pytest` NON verificabili qui (vedi 04_handoff).

## [ARCHITETTURA]
- [A-001] | Fonte: CLAUDE.md:7 | Progetto NEMESIS, lab Corbetta, embedding+clustering di lesioni/disconnettomi | Da verificare (letteratura/management in file successivi)
- [A-002] | Fonte: CLAUDE.md:21 | Entry point in `src/pipeline/*.py` e `scripts/*.py` | Verificato (19 file in src/pipeline incl. `__init__`, 2 in scripts/)
- [A-003] | Fonte: CLAUDE.md:21 | "ogni guida in docs/guides documenta locale e sbatch" | Parziale: 12/14 guide citano sbatch; `datasets.md` ed `evaluation.md` no (giustificato: non sono pipeline CLI)
- [A-004] | Fonte: CLAUDE.md:24 | Job in `jobs/run_<pipeline>.sh`, file singolo, niente sottocartelle | Verificato (18 file, 0 sottocartelle)
- [A-005] | Fonte: CLAUDE.md:25 | `#SBATCH -o/-e` → `logs/slurm/<pipeline>/%j.{out,err}` | Verificato su tutti e 18 i job (nome cartella = nome job)
- [A-006] | Fonte: CLAUDE.md:24-27 | `jobs/run_build_lesion_matrix.sh` è l'esempio di riferimento con header, conda, cd, invocazione | Verificato (letto per intero)
- [A-007] | Fonte: CLAUDE.md:29 | Ogni nuova pipeline/script ha un `jobs/run_<name>.sh` | Falso per `scripts/archive_local_raw_data.py` (nessun job) e `src/pipeline/embedding_app.py` (nessun job; interattivo) → ISS-003
- [A-008] | Fonte: CLAUDE.md:~33-50 | Struttura `docs/{guides,dev,experiments,debugging}`, `docs/setup.md` | Verificato
- [A-009] | Fonte: CLAUDE.md:35 | 14 guide elencate esistono; 4 ritirate (`dim_reduction_clustering`, `atlas_building`, `retrieval`, `compute_sdc`) assenti | Verificato
- [A-010] | Fonte: CLAUDE.md:36 | 14 doc dev elencati esistono | Verificato; ma `docs/dev/covariance_pca.md` esiste e NON è elencato → ISS-004
- [A-011] | Fonte: CLAUDE.md:37 | `docs/notes/` non esiste più | Verificato
- [A-012] | Fonte: CLAUDE.md:~40 | `management/{meetings,cheatsheets,nemesis_project,slides}` | Verificato (9 meeting, 9 cheatsheet, 6 file project, 1 slide)
- [A-013] | Fonte: CLAUDE.md:~43 | `knowledge/{notes,papers}`, `knowledge/papers/{stroke_core,stroke_related,methods,index.md}` | Verificato
- [A-014] | Fonte: CLAUDE.md:~48 | `src/` = features, analysis, utils, pipeline | Verificato
- [A-015] | Fonte: CLAUDE.md:~50, 54 | Esiste `README.md` con "What's implemented so far" ; skill `history` | Verificato (README.md:64; `.claude/skills/history/SKILL.md`)
- [A-016] | Fonte: CLAUDE.md:~5 | Suite pytest in `tests/unit` e `tests/integration` | Verificato (esistenza); esito run → Da verificare in Fase 2 (ambiente)
- [A-017] | Fonte: CLAUDE.md:~72 | `@code_standards.md` e `@lessons_learned.md` importati | Verificato (risolvono in `.claude/`, import relativo)
- [A-018] | Fonte: CLAUDE.md (history) | Esistono `data_changelog`, `methods_changelog`, `project_changelog`, `stato_progetto_archive` in `.claude/history/` | Verificato
- [A-019] | Fonte: CLAUDE.md (history) | Esiste `.claude/stato_progetto.md` | Verificato

## [CONFIG/PARAMETRI]
- [C-001] | Fonte: CLAUDE.md:11 | `environment.yml` contiene numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn | Verificato (tutti presenti; nibabel/nilearn via pip)
- [C-002] | Fonte: environment.yml / src/analysis/embedding_app.py:61 | `embedding_app` importa `dash`; `environment.yml` NON lo include | Falso/lacuna → ISS-002
- [C-003] | Fonte: CLAUDE.md:11 | Env `nemesis` | Verificato (`environment.yml:1`)
- [C-004] | Fonte: setup.md:31 | Env `nemesis_fallback` con dadapy 0.3.4 senza dash | Da verificare (env esterno, non ispezionabile)
- [C-005] | Fonte: CLAUDE.md:17 | `*.nii`/`*.nii.gz` gitignored | Parziale: `.gitignore` non ha regole `*.nii*`; sono ignorati solo `data/*`, `results/`, `logs/`, `summaries/`. 22 `.nii.gz` sono tracciati (atlanti/template in `assets/`) → ISS-005

## [CODICE/API]
- [K-001] | Fonte: CLAUDE.md:35 | Moduli `cluster_description/composition/comparison/pair/drivers`, `anatomical_maps` in `src/analysis/` | Verificato (6/6)
- [K-002] | Fonte: CLAUDE.md:21-23 | Invocazione `python -m src.pipeline...` / `PYTHONPATH=... python scripts/...` | Da verificare nelle singole guide

## [TEORIA/PAPER]
(nessuna affermazione teorica in CLAUDE.md)

## [ESPERIMENTI/METRICHE]
(nessuna in CLAUDE.md)

## [STATO_BRANCH]
- [S-001] | Fonte: CLAUDE.md:35 | Commit `2ed3dcb` (atlas_building retired), `cf6e1fe`, `2dcd0ae`, `b71ff7c`, `9fb13fb` (citati in CLAUDE.md/lessons_learned) | Non verificabile: clone shallow, oggetti assenti → richiedere `git fetch --unshallow`
- [S-002] | Fonte: CLAUDE.md:37 | Merge `docs/dr-clustering-literature-migration` (18-08-26) | Non verificabile (shallow)
- [S-003] | Fonte: git | Branch: `claude/bold-ritchie-7ekm6v` (corrente), `main`; remoti corrispondenti | Verificato

## Nota per file futuri (cross-check)
- code_standards.md §8 cita `lesson_learned.md` (singolare) mentre il file è `lessons_learned.md` → confermato, ISS-006.
- CLAUDE.md dice che lessons_learned è aggiornato "per code_standards §8": verificato: §8 (code_standards.md:110) parla di 'lessons learned' per-bug ma non ordina di aggiornare l'indice lessons_learned.md → ISS-006.
