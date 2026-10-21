# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-10-20. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/history/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `sdc_matrix.md`, `design_patterns.md`, `metadata.md`, `covariance_pca.md`). Registro delle sessioni sperimentali (un file per sessione `sX.Y-<formato>.md`, lineage, pipeline attraversate): `docs/experiments/`.

**Metadati**: cinque file in `assets/metadata/`, ognuno scritto da una pipeline (`populate_metadata`, `compute_lesion_metadata`, `compute_sdc_metadata`, `enrich_metadata`, `build_excluded_subjects`). Ordine di lancio in `docs/guides/metadata.md`, architettura in `docs/dev/metadata.md`.

**PCA**: è un metodo di `REDUCTION_METHODS` (`pca`, `src/analysis/pca_method.py`), con rotazione varimax come parametro; `rotation_n_components` ruota un pool più grande (es. 150) e tiene le componenti ruotate con più varianza. Calcolo per matrici larghe (percorso duale e covarianza tra variabili) in `src/analysis/covariance_pca.py`. `pca_varimax` non esiste più.

**Report di tuning del clustering**: `src/pipeline/evaluate_clustering_tuning.py` (guida `docs/guides/evaluate_clustering_tuning.md`) copre agglomerative (bande di silhouette Kaufman-Rousseeuw, nessuna soglia "usable"), `hdbscan` e `hdbscan_soft`, con tabella di accordo tra linkage.

## Lavoro attivo / thread aperti

- **s2.4-vol del 16-10** (SDC voxelwise, voxel fuori dal brain azzerati, 227235 colonne, 5845 soggetti): PCA in produzione a 12 componenti varimax (pool di 150, 69.4% della varianza); tuning di agglomerative, `hdbscan`, `hdbscan_soft` sugli score PCA. Dettaglio e decisioni in `docs/experiments/s2.4-vol.md`. Clustering di produzione: 29 run su 30, **manca** `hdbscan_soft` nc10 `min_cluster_size=100`, `min_samples=20`, `eom` sulla matrice del 16-10.
- **`hdbscan_soft`** (pacchetto `hdbscan`) è un metodo a sé con griglia propria, **non confrontabile** con `hdbscan` di sklearn. Decisione e alternative scartate: `methods_changelog.md` 15-10-26. Valutazione del soft clustering: `soft_membership` in `EVALUATIONS` e `SoftMembership` in `src/analysis/clustering_evaluation.py`.
- **Metadati (06-10-26)**: forzatura del lato WashU spenta (`geometric_override_datasets: []`). Restano i controlli E (maschera manuale contro maschera SDC; per `sub-STUKLFR0403` l'SDC inverte il lato) e F (7 T1 WashU con la stessa acquisizione), e cosa fare delle maschere capovolte nelle matrici (`open_problems.md`, `methods_changelog.md` 06-10-26). Esclusioni adottate: solo maschera vuota e più del 30% dei voxel fuori dal brain; la pipeline non applica la soglia (`docs/dev/metadata.md`).
- **Audit dei passi prima di `dim_reduction`/`clustering`**: aperto. Serve una mappa completa, verificata dal codice, di ciò che ogni pipeline legge (matrici, registri dei parametri, template e atlanti, registro delle sessioni), poi una guida unica con i comandi. `docs/experiments/pipelines.md` ne è un disegno parziale.
- **Notebook `clustering_comparison.ipynb`**: segnalato lo scambio homogeneity/completeness (`lessons_learned.md` #41, commit `0472f52`); verificare se il calcolo è stato corretto o solo annotato.
- **SDC clustering tuning s2.1-schaefer-200-tian-s2**: nc2 documentato; prossimo step già scritto nel doc: estendere a `nc3`.
- **Lesion clustering produzione s1.1-vol/s1.2-vol**: chiuso — non si elegge un k unico, le granularità restano aperte in parallelo (sezioni `Decisioni` dei rispettivi file in `docs/experiments/`).

L'elenco completo di problemi aperti e cose da fare sta in **`.claude/open_problems.md`**.

## Vincoli/regole in vigore oggi

- **Branch**: si lavora su `main` (un branch nasce solo per un task specifico, vedi `.claude/branch_alignment.md`). `main` è avanti di 5 commit rispetto a `origin/main` (non pushato) prima di questo aggiornamento. Working tree pulito.
- **`config/registry/params_*.json` e `config/pipelines/{dim_reduction,clustering}.json`** sono stato mutabile: contengono i valori dell'ultima run (ora `dim_reduction` = PCA di produzione su `16-10_s2.4-vol`, `clustering` = tuning di agglomerative/hdbscan/hdbscan_soft su `19-10_s2.4-vol_nc12_varimax`). Non sono default canonici: riportare la griglia giusta prima di rilanciare un tuning di allora (`lessons_learned.md` #36).
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **Documentazione e Codice**: niente dump di tabelle o dati completi nei `.md` (solo pointer a `results/*.csv`). Rationale verbosa confinata in `docs/dev/`. Niente soglie arbitrarie nei report di tuning: solo metriche agnostiche, l'interpretazione si costruisce con l'utente. Niente test statistici sulla descrizione clinica dei cluster.
- **Non rigenerare** `results/dim_reduction_strategies.csv`: lo script è stato ritirato (commit `3e53099`).
- **Sezione "Confronto" dell'Embedding Explorer**: rimossa dall'app e parcheggiata; i builder e i test restano non montati, non sono codice morto.
- **Diagnostic grid oltre 2D**: `n_components > 2` non emette un diagnostic grid automatico — ispezione on-demand via `src/pipeline/plot_tuning_embedding_3d.py`, non è un bug.
- **Copie locali ridotte**: solo `UNIPD/WashU/features/` e `data/derived/features/masked_fc/` restano a 10 soggetti campione (`docs/guides/datasets.md`).
- **`enrich_metadata`**: `overwrite` e `protected_path` obbligatori nel config; con `overwrite: true` una cella vuota nella fonte svuota quella del registro, senza avviso (`docs/guides/metadata.md`).
- **`excluded_subjects.csv`** è scritto da `build_excluded_subjects` (config `config/pipelines/build_excluded_subjects.json`): con `overwrite: false` aggiunge senza toccare le righe esistenti, con `true` ricostruisce dal solo config. Non lo scrive più nessuna cella di notebook.

## Prossimo passo esatto

A scelta dell'utente: (1) lanciare la run di produzione mancante `hdbscan_soft` nc10 `mcs=100`, `ms=20`, `eom` sulla matrice del 16-10 (`docs/experiments/s2.4-vol.md`, sezione "Clustering produzione, 16-10"); (2) valutare i cluster dei tuning su `19-10_s2.4-vol_nc12_varimax` nel notebook `clustering_evaluation.ipynb` e registrare le decisioni nella sezione `Decisioni` di `s2.4-vol.md`; (3) avviare l'audit dei passi prima di `dim_reduction`/`clustering`, partendo dal leggere dal codice gli input di `dim_reduction.py`, `clustering.py`, `build_lesion_matrix.py`, `build_sdc_matrix.py`, `mask_fc.py`/`build_fc_matrix.py`.
