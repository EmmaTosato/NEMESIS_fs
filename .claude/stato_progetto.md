# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-26. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `design_patterns.md` — le docstring estese sono state snellite e spostate qui nella sessione 26/08 per preservare leggibilità del codice). Note metodologiche/di letteratura sotto `knowledge/dim_reduction_clustering/` e `knowledge/neuroimaging/`. 
Strumento aggiunto per il visual testing interattivo delle run: `scripts/plot_tuning_embedding_3d.py`. Archiviazione raw locale: `archive_local_raw_data.py`.

## Lavoro attivo / thread aperti

- **Audit di correttezza teorica del 15/08/26**, tracciato in `AUDIT_FINDINGS.md` (repo root): **tutti i finding CRITICAL/HIGH/MEDIUM/LOW (#1-68) ora chiusi/triageati**, inclusi gli ultimi 2 HIGH pre-esistenti (sessione 26/08): **HIGH #14** era un mismatch doc/codice (`docs/dev/models.md` dichiarava `assign_clusters_from_cooccurrence` tagliare a `n_clusters` fisso, il codice — corretto, fedele a Fred & Jain 2002 — taglia a `threshold`); fix solo di documentazione. **HIGH #15** (`clustering.py`'s comparison-plot fuori da try/except) risultava già implementato dal 18/08 (stesso fix di #16) ma il suo status-line in `AUDIT_FINDINGS.md` non era mai stato aggiornato da "Aperto" — riallineato, test di regressione già esistente. Nessun altro lavoro dell'audit resta da fare.
- **`management/notes/TODO.md`**: rimozione della feature `parcellate` da `build_lesion_matrix.py`/`src/features/lesion.py` — decisione loggata 17/08, non implementata. Tensione esplicita e irrisolta: la produzione attuale (`config/pipelines/build_lesion_matrix.json`, sessione `yan300s1`) usa `parcellate: true` per riprodurre Thiebaut de Schotten 2020; va deciso se questa rimozione sostituisce l'obiettivo di replica prima di procedere.
- **Visualizzazione > 2D**: `n_components > 2` non emette più un diagnostic grid schiacciato in 2D. Lo scarto dei plot generici è voluto, l'ispezione si fa ora on-demand tramite `scripts/plot_tuning_embedding_3d.py`.

## Vincoli/regole in vigore oggi

- **`AUDIT_FINDINGS.md` è la fonte di verità sullo stato dei finding dell'audit 15/08** — ora interamente chiuso/triageato (HIGH #14/#15 chiusi in sessione 26/08).
- **Commit automatici**: solo su richiesta esplicita dell'utente (`.claude/CLAUDE.md`, `code_standards.md` §9).
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione e Codice**: Niente dump di tabelle o dati completi nei `.md` (solo pointer a `results/*.csv`). Rationale/logica verbosa confinata in `docs/dev/`, il sorgente python deve rimanere conciso e snello.

## Prossimo passo esatto

HIGH #14/#15 chiusi in questa sessione (fix di documentazione, nessun cambio di codice) — restano da committare insieme al resto del working tree. Il thread operativo diretto per la ripresa dei lavori è la chiusura della disputa concettuale del `parcellate` in TODO.md, più la discussione in corso su tuning/evaluation del clustering (vedi conversazione). Un nuovo agente può fare affidamento totale su questo snapshot, su `TODO.md` e sul `git log` recente per orientarsi.
