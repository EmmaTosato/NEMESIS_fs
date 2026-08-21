# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-17. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message (cosa è cambiato e perché, a livello di codice), `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline: parametri, output, log grezzo). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `design_patterns.md`). Note metodologiche/di letteratura sotto `docs/notes/`/`knowledge/dim_reduction_clustering/`.

## Lavoro attivo / thread aperti

- **Due linee di sviluppo divergenti sulla migrazione `dim_reduction_clustering.py` → `clustering.py`** (`docs/dev/clustering_migration_plan.md`), non ancora riconciliate:
  - **`main`** (working tree principale): avanti di 2 commit su `origin/main`, con modifiche **non committate in corso da una sessione parallela** su `embedding_app.py`/`reduction.py`/`dim_reduction.py`/`dim_reduction_clustering.py`/relativi test — contenuto e stato di completamento sconosciuti da qui, verificare `git status`/`git diff` prima di toccare questi file.
  - **`docs/dr-clustering-literature-migration`**, checked out in una **worktree separata** (`/private/tmp/claude-501/.../scratchpad/nemesis-migration-wt` — path di scratchpad, non garantito sopravvivere a un riavvio/nuova sessione): contiene il piano §3 (embedding_app scopre anche i run `clustering.py`, color mode `cluster_label`) e §6 (`results/dim_reduction_strategies.csv` generato, `SESSIONS.md` spostato/irrigidito, backfill path obsoleti) **completati, testati (647/647) e committati** (`51adabb`, `392b9da`). Branch solo locale, non pushato su `origin`.
  - **Da decidere con l'utente**: come riconciliare le due linee — `main` ha probabilmente già ri-implementato (parzialmente?) lo stesso lavoro in modo indipendente. Non tentare un merge automatico senza prima confrontare i due stati.
- **`results/dim_reduction_strategies.csv`** (dato gitignored, generato da `scripts/build_dim_reduction_strategies_csv.py`) e i `runs_tuning.csv` corretti da `scripts/backfill_stale_tuning_output_paths.py` sono già scritti su disco nel repo reale, indipendenti dal branch — coerenti con lo stato del branch `docs/dr-clustering-literature-migration`, non con `main`.

## Vincoli/regole in vigore oggi

- **Working tree condiviso con una sessione parallela attiva** (stesso autore git, `EmmaTosato`) su `main`: file modificati "sotto i piedi" durante il lavoro sono un evento reale osservato in questa sessione (branch cambiato, commit apparsi/spariti). Sempre verificare `git status --short`/`git branch --show-current`/`git log` prima di stage/commit — mai assumere che un file modificato sia proprio o che il branch corrente sia quello atteso.
- **Commit automatici**: solo su richiesta esplicita dell'utente (`.claude/CLAUDE.md`, `code_standards.md` §9).
- **Esecuzione locale vs SLURM**: locale diretto è il default attuale, non proporre `sbatch`/jobs cluster senza richiesta esplicita (`.claude/CLAUDE.md` § "Running pipelines").
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`, solo sul cluster) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione**: niente dump di tabelle/dati completi nei `.md` — solo tabelle corte + puntatore a `results/*.csv`.

## Prossimo passo esatto

Con l'utente: confrontare lo stato non committato di `main` (embedding_app.py/reduction.py/dim_reduction.py/dim_reduction_clustering.py) con i 2 commit già pronti su `docs/dr-clustering-literature-migration` (`51adabb`, `392b9da`) e decidere come riconciliare — probabile sovrapposizione di lavoro sullo stesso piano (§3/§6), da capire chi/cosa tenere prima di qualunque merge/push.
