# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-09-03. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/history/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `sdc_matrix.md`, `design_patterns.md`, `metadata.md` — i 3 livelli di metadati e come si relazionano).

**Ridisegno metadati completato 06-09-26**: `src/pipeline/enrich_metadata.py` (nuovo) scrive le colonne cliniche direttamente in `assets/metadata/participants.csv`; `enrich_lesion_metadata.py` e `src/features/clinical.py` cancellati; `src/utils/participants.py` è il lettore del registro; `embedding_coloring.color_values` risolve `side`/`nihss` dal registro al momento del plot. Resta non implementato il `lesion_side` geometrico (serve la calibrazione della soglia bilaterale). Vedi `docs/dev/metadata.md`.

**Naming convention sessioni estesa 02-09-26** (commit `e734f5d`): `sX.Y` → `sX.Y-<formato>`, suffisso di formato ora obbligatorio ovunque (vocabolario chiuso, mai `_` al suo interno - `run_log.py::append_run_log_entry` splitta `run_id` sul primo `_`). Applicata retroattivamente a tutto ciò che esisteva: `s1.1`→`s1.1-vol`, `s1.2`→`s1.2-vol`, `s2.1`→`s2.1-schaefer-200-tian-s2` (101 directory rinominate sotto `data/derived/`/`results/`, tutti i `runs*.csv`/`manifest.json`/`config.md` coerenti). FC corretta da `s2` (numero sbagliato, riservato a SDC in `data_sessions.md`) a `s3.1` + tag per-atlas_combo (`mask_fc.py`/`build_fc_matrix.py` ora derivano `effective_session_name = f"{session_name}-{combo}"`, evita collisioni future tra combo della stessa coorte). Registro narrativo riscritto: `docs/experiments/data_sessions.md` (header `### Session X.Y-<formato>`, vocabolario tag in testa). `scripts/build_dim_reduction_strategies_csv.py` aveva un bug preesistente (`_SESSION_HEADER_RE` cercava `## Session`, il doc usa H1/H3 - mai stato un match, fallback silenzioso a "undocumented" per ogni sessione) - fisso nello stesso commit, verificato con una run reale (21/21 sessioni risolte, 0 "undocumented").

## Lavoro attivo / thread aperti

- **Renderer anatomia**: `main` resta su nilearn. Il branch `viz-niivue` è stato eliminato il 07-09-26 (recuperabile da `facef6f` finché dura il reflog).
- **Lesion clustering produzione s1.1-vol/s1.2-vol**: chiuso. La decisione registrata (`docs/experiments/clustering/s1_production.md`, sezioni `Decisioni`) è che *non* si elegge un k unico — le granularità restano aperte in parallelo e si confrontano nel notebook di valutazione.
- **SDC clustering tuning s2.1-schaefer-200-tian-s2**: nc2 documentato (`docs/experiments/clustering/s2_tuning.md`) — forte lateralizzazione su `lesion_side` confermata. Prossimo step già scritto nel doc: estendere a `nc3`.
- **Audit naming plot-level**: ancora aperto, non toccato di recente.

L'elenco completo di problemi aperti e cose da fare sta in **`.claude/open_problems.md`**.

## Vincoli/regole in vigore oggi

- **Branch**: lavoro corrente su `metadata-restructuring` (non `main`, non ancora mergeato/pushato). `TODO.md` ha una modifica non committata dell'utente, precedente alla sessione odierna — non toccata.
- **`config/registry/params_clustering.json`**: lasciato ai valori dell'ultima opzione lanciata per metodo — non sono i default "canonici", sono lo stato dell'ultima run reale.
- **`clustering.py` non genera più `comparison/`** (rimosso 01-09-26): cartelle `comparison/` residue da run precedenti restano su disco ma non vengono più rigenerate.
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster. `config/pipelines/compute_sdc.json` **non** toccato dalla migrazione naming 02-09-26 (escluso esplicitamente - il suo `session_name` ha un problema separato, non ancora affrontato).
- **Documentazione e Codice**: niente dump di tabelle o dati completi nei `.md` (solo pointer a `results/*.csv`). Rationale/logica verbosa confinata in `docs/dev/`, il sorgente python deve rimanere conciso e snello.
- **Diagnostic grid oltre 2D**: `n_components > 2` non emette un diagnostic grid automatico — ispezione solo on-demand via `scripts/plot_tuning_embedding_3d.py`, non è un bug.
- **Copie locali ridotte**: solo `UNIPD/WashU/features/` e `data/derived/features/masked_fc/` restano a 10 soggetti campione (vedi `docs/guides/datasets.md`) — `manual_masks` è pieno per tutti e 5 i dataset dal 01-09-26.
- **`assets/metadata/`**: contiene solo `participants.csv` (5752 soggetti) e `columns_by_dataset.xlsx`. I tsv per-dataset sono cancellati e nessuno li rigenera.
- **FC `runs.csv` (`data/derived/features/{fc_matrix,masked_fc}/runs.csv`)**: la colonna `notes` delle 12 righe storiche per-combo dice ancora "stessa sessione s2 delle altre 11 combo" (vero nello schema pre-02-09-26, non più letteralmente vero ora che ogni riga ha un tag combo-specifico distinto) — lasciata invariata come narrativa storica; solo le colonne funzionali `session`/`output` sono state aggiornate.

## Prossimo passo esatto

Sessione naming convention conclusa (2 commit `e734f5d`/`4e892e5`, README.md riscritto, `stato_progetto.md`/`lessons_learned.md` aggiornati). Prossimo lavoro, a scelta: decidere il k di produzione finale per lesion s1.1-vol (`docs/experiments/clustering/s1_production.md`), estendere l'analisi SDC s2.1-schaefer-200-tian-s2 a `nc3`, riprendere l'audit naming a livello di plot, o continuare a provare renderer alternativi per i pannelli di anatomia (branch `viz-niivue`).
