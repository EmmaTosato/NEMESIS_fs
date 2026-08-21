# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-21. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `design_patterns.md`). Note metodologiche/di letteratura sotto `knowledge/dim_reduction_clustering/` e `knowledge/neuroimaging/` (`docs/notes/` non esiste più, dissolta nel merge del 18/08 — riferimenti stale corretti in questa sessione, vedi sotto).

## Lavoro attivo / thread aperti

- **Audit di correttezza teorica del 15/08/26** (8 agenti paralleli), tracciato in `AUDIT_FINDINGS.md` (repo root): CRITICAL #1-8 e HIGH #9-25 tutti chiusi (incl. #14, chiuso in una sessione precedente). **MEDIUM #26-49 chiuso in questa sessione (21/08)**: 18 finding implementati con fix di codice/config/test (#26, #27, #28, #29, #30, #31, #34, #35, #36, #41, #43, #44, #45, #46, #48, #49), 4 di sola documentazione (#32, #33, #38, #42), 2 documentati senza cambiare valori scientifici su decisione utente esplicita (#37 — split budget di `evidence_accumulation`; #47 — `reference_template_path` di produzione punta alla maschera di un singolo paziente, non un template MNI152), 2 chiusi in triage come moot/sussunti dalla rimozione di `dim_reduction_clustering.py` (#39, #40). **LOW #50-68 non ancora affrontato** — stesso ciclo triage→conferma→fix→test da ripetere.
- **`.claude/lessons_learned.md` #28 aggiunta** in questa sessione: tightening di `group_of()` (#26/#46) a validazione incondizionata ha rotto 44 test in 5 file usando ID soggetto sintetici non conformi (`sub-01` ecc.) — fixture helper riscritti con naming realistico (`sub-STUNIPD0001`), non le singole assert.
- **Debug report da scrivere**: `docs/debugging/debug_21_08_26.md` (o data di chiusura effettiva), un bug per sezione con livello di criticità e lesson learned, per i finding MEDIUM+LOW di questa sessione (§8 `code_standards.md`) — non ancora scritto.
- **`management/notes/TODO.md`**: rimozione della feature `parcellate` da `build_lesion_matrix.py`/`src/features/lesion.py` — decisione loggata 17/08, non implementata, tensione con la produzione attuale (`parcellate: true` per riprodurre Thiebaut de Schotten 2020) irrisolta.

## Vincoli/regole in vigore oggi

- **`AUDIT_FINDINGS.md` è la fonte di verità sullo stato dei finding dell'audit 15/08** — leggere lì lo stato di un finding prima di riproporne il triage da zero. Non fidarsi del titolo/riga citati senza riverificare contro il codice attuale: in questa sessione #39/#40 sono risultati moot per la rimozione di `dim_reduction_clustering.py` (14/08), e la verifica dei riferimenti `docs/notes/` per #32 ha trovato stale reference nuove non elencate nel finding originale (`knowledge/dim_reduction_clustering/clustering_tuning_guide.md`).
- **Commit automatici**: solo su richiesta esplicita dell'utente (`.claude/CLAUDE.md`, `code_standards.md` §9). In questa sessione l'utente ha esplicitamente richiesto commit+push per permettere la ripresa via agente cloud programmato (`/schedule`, one-shot fra 2:30h) — non un'eccezione permanente al vincolo.
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione**: niente dump di tabelle/dati completi nei `.md` — solo tabelle corte + puntatore a `results/*.csv`.

## Prossimo passo esatto

Suite verde confermata (727 passed, 0 failed, 12 skipped, esclusi i 2 file `bcblib`-dipendenti) subito prima del commit di questa sessione. Un agente cloud programmato (`/schedule`, one-shot) riprenderà il lavoro fra 2:30h dal commit: (1) triage dei finding LOW #50-68 di `AUDIT_FINDINGS.md` con lo stesso ciclo verifica-contro-codice→proposta→conferma utente→fix→test di regressione→aggiornamento tracker già usato per HIGH/MEDIUM; (2) al termine, scrivere `docs/debugging/debug_DD_MM_YY.md` con un bug per sezione (criticità + lesson learned) per ogni finding effettivamente corretto in questa sessione + quella successiva sui LOW.
