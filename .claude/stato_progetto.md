# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-09-01. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `sdc_matrix.md`, `design_patterns.md`).

`src/analysis/plotting.py::_CATEGORICAL_PALETTE` estesa 5→10 colori (01-09-26, commit `4b4111e`), CVD-safe solo su coppie adiacenti (non all-pairs — limite strutturale per uno scatter con >3-4 serie, non risolvibile ampliando la palette, vedi `docs/dev/plotting.md`). Stesso commit: `_MARKER_SIZE`/`_MARKER_ALPHA`/`_declutter_points` (già validati sui plot di embedding) ora applicati anche a `plot_clusters_2d`/`plot_clusters_comparison`/`plot_silhouette_analysis` (prima fuori scope, marker opachi troppo grandi su run HDBSCAN con 8-20 cluster reali).

## Lavoro attivo / thread aperti

- **Lesion clustering produzione s1.1**: 6 opzioni di k lanciate (`results/lesion/clustering/production/*/umap/01-09_s1.1_*`: A k4, B k5, C k6, D k8-solo-spectral, E/F hdbscan). **Nessuna scelta finale del k di produzione ancora fatta** — decisione dell'utente, non presa in questa sessione. La cartella `comparison/` condivisa (stesso `session_name`+embedding per tutte le opzioni) contiene solo l'ultima run (F, hdbscan) — le altre sono state sovrascritte di proposito; il confronto cross-opzione è demandato a un notebook (non ancora scritto) che mixa liberamente le cartelle per-metodo.
- **Lesion clustering tuning s1.2** (5269 soggetti) e **SDC clustering tuning s2.1** (nc2+nc3): entrambi completi, tutti e 5 i metodi. Risultati s1.2 documentati in `docs/experiments/dim_reduction_clustering/clustering_tuning_s1.md` (sezione `01-09-2026 — s1.2`); s2.1/nc3 **non ancora documentato** in un file esperimenti analogo per SDC.
- **Audit naming plot-level**: ancora aperto, non toccato in questa sessione (prompt preparato in una sessione precedente, non lanciato).
- **File non correlati modificati/non tracciati nella working tree** (non toccati in questa sessione, esclusi dal commit `4b4111e`): `src/analysis/embedding_app.py`, `src/pipeline/embedding_app.py`, `docs/guides/embedding_app.md`, `tests/unit/test_embedding_app.py`, `tests/unit/test_pipeline_embedding_app.py` (modificati) + `src/analysis/anatomical_maps.py`, `tests/unit/test_anatomical_maps.py` (nuovi, non tracciati) — lavoro di un'altra sessione/finestra, ancora in corso.

## Vincoli/regole in vigore oggi

- **Branch**: `main` avanti di 3 commit locali su `origin/main` (incluso `4b4111e`), mai pushato — nessuna richiesta esplicita in tal senso.
- **`config/registry/params_clustering.json`**: lasciato ai valori dell'ultima opzione lanciata per metodo (kmeans/agglomerative/gmm su opzione C: k6; hdbscan su opzione F: mcs15/ms5; spectral su opzione D: k8/rbf/gamma1.0) — non sono i default "canonici" del repo, sono lo stato dell'ultima run reale.
- **Collision nota su `clustering.json` produzione**: più run con lo stesso `session_name`+embedding (es. le opzioni A-F di s1.1) collidono sulla cartella `comparison/` condivisa (`overwrite: false` la blocca) — nessun flag per disattivarla. Soluzione adottata: `overwrite: true` solo per bypassarla, comparison trattata come disposable/da ricostruire a parte.
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione e Codice**: niente dump di tabelle o dati completi nei `.md` (solo pointer a `results/*.csv`). Rationale/logica verbosa confinata in `docs/dev/`, il sorgente python deve rimanere conciso e snello.
- **Diagnostic grid oltre 2D**: `n_components > 2` non emette un diagnostic grid automatico (schiacciato in 2D sarebbe fuorviante) — ispezione solo on-demand via `scripts/plot_tuning_embedding_3d.py`, non è un bug.

## Prossimo passo esatto

Decidere il k di produzione finale per lesion s1.1 confrontando le 6 opzioni già lanciate (`results/lesion/clustering/production/*/umap/01-09_s1.1_*`) — via il notebook di confronto ancora da scrivere, o ispezione diretta dei `cluster_plot.png`/`silhouette_plot.png` per-metodo. In alternativa: documentare s2.1/nc3 in un file esperimenti SDC analogo a `clustering_tuning_s1.md`, o riprendere l'audit naming a livello di plot (prompt già pronto da sessione precedente).
