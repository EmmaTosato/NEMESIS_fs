# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-18. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message (cosa è cambiato e perché, a livello di codice), `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline: parametri, output, log grezzo). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `design_patterns.md`). Note metodologiche/di letteratura sotto `knowledge/dim_reduction_clustering/` (`docs/notes/` non esiste più, dissoltа nel merge del 18/08 — vedi vincoli sotto).

## Lavoro attivo / thread aperti

- **Audit di correttezza teorica del 15/08/26** (8 agenti paralleli), tracciato in `AUDIT_FINDINGS.md` (repo root): CRITICAL #1-8 tutti decisi/chiusi, HIGH #9-25 tutti implementati e testati **tranne #14** (`docs/dev/models.md` dichiara `assign_clusters_from_cooccurrence` tagliare a `n_clusters` fisso, il codice reale taglia a `threshold` — mismatch doc/codice reale, non incluso nel giro di fix approvato, ancora aperto). MEDIUM (#26+) e severità inferiori non ancora affrontati in nessuna sessione.
- **`management/notes/TODO.md`**: rimozione della feature `parcellate` da `build_lesion_matrix.py`/`src/features/lesion.py` — decisione loggata 17/08, non implementata. Tensione esplicita e irrisolta: la produzione attuale (`config/pipelines/build_lesion_matrix.json`, sessione `yan300s1`) usa `parcellate: true` per riprodurre Thiebaut de Schotten 2020; va deciso se questa rimozione sostituisce l'obiettivo di replica prima di procedere.

## Vincoli/regole in vigore oggi

- **Migrazione `dim_reduction_clustering.py` → `clustering.py` conclusa**: branch `docs/dr-clustering-literature-migration` mergiato in `main` (18/08) — `dim_reduction_clustering.py`/config/doc/job/test collegati non esistono più. `clustering.py` copre entrambi i casi (`reduced_data: true/false`), comparison plot include già l'HTML interattivo.
- **`AUDIT_FINDINGS.md` è la fonte di verità sullo stato dei finding dell'audit 15/08** — leggere lì lo stato di un finding prima di riproporne il triage da zero; non tutti i titoli riflettono accuratamente dove vive il difetto reale (vedi #14/#18: titoli che citavano `dim_reduction_clustering.py` per difetti in realtà altrove o ancora vivi in `clustering.py`).
- **Commit automatici**: solo su richiesta esplicita dell'utente (`.claude/CLAUDE.md`, `code_standards.md` §9).
- **Esecuzione locale vs SLURM**: locale diretto è il default attuale, non proporre `sbatch`/jobs cluster senza richiesta esplicita (`.claude/CLAUDE.md` § "Running pipelines").
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`, solo sul cluster) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione**: niente dump di tabelle/dati completi nei `.md` — solo tabelle corte + puntatore a `results/*.csv`.

## Prossimo passo esatto

Suite verde confermata (699 passed, 0 failed, 12 skipped, esclusi i 2 file `bcblib`-dipendenti) subito prima del commit di questa sessione. Nessuna azione bloccante in corso — prossimo lavoro dipende dalla direzione dell'utente: correggere il mismatch doc di #14, o procedere ai finding MEDIUM (#26+) di `AUDIT_FINDINGS.md`, non ancora presentati/discussi.
