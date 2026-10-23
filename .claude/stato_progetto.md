# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-10-23. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/history/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `sdc_matrix.md`, `design_patterns.md`, `metadata.md`, `covariance_pca.md`). Registro delle sessioni sperimentali (un file per sessione `sX.Y-<formato>.md`, lineage, pipeline attraversate): `docs/experiments/`.

**Metadati**: cinque file in `assets/metadata/`, ognuno scritto da una pipeline (`populate_metadata`, `compute_lesion_metadata`, `compute_sdc_metadata`, `enrich_metadata`, `build_excluded_subjects`). Ordine di lancio in `docs/guides/metadata.md`, architettura in `docs/dev/metadata.md`.

**PCA**: è un metodo di `REDUCTION_METHODS` (`pca`, `src/analysis/pca_method.py`), con rotazione varimax come parametro; `rotation_n_components` ruota un pool più grande (es. 150) e tiene le componenti ruotate con più varianza. Calcolo per matrici larghe in `src/analysis/covariance_pca.py`.

**Valutazione del tuning del clustering**: le valutazioni si dichiarano in `tuning_evaluations` (`config/pipelines/clustering.json`, `evaluate_clustering_tuning.json`; parametri in `config/registry/clustering_evaluations.json`) e girano con una sola funzione, `run_evaluations`, dopo lo sweep e su un tuning già salvato (`evaluate_clustering_tuning.py`, guida `docs/guides/evaluate_clustering_tuning.md`). `report.md` lo scrive `clustering_tuning_report.py` leggendo i file prodotti, senza calcolare.
- **`hdbscan` e `hdbscan_soft`**: indice interno = **DBCV** (`src/analysis/dbcv.py`, euclideo; NaN con meno di 2 cluster, mai 0). Valutazioni `density_metrics` (colonna `dbcv` in `density_metrics.csv`), `tuning_heatmaps`, `dbcv_curves`. Silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn non si calcolano per questi metodi. Produzione: riga `DBCV` in `config.md`, `dbcv_per_cluster.csv`, `dbcv_plot.png`; app: pannello DBCV. Decisione e alternative scartate: `.claude/history/methods_changelog.md` 22-10-26.
- **`agglomerative`**: silhouette (nella `metric` della run), CH e DB (solo con `metric` euclidea: vuoti altrimenti, ovunque), cofenetica, salto del dendrogramma, ARI tra linkage, quota del cluster più grande (`largest_cluster_share`) e Dunn (`dunn_index`, solo euclidea). La silhouette per cluster resta fuori dal tuning: sta in produzione e nell'app. Il report non legge ancora quota e Dunn.
- **In stand by (scelta del 23-10-26)**: `kmeans`, `gmm`, `spectral` e `adp` non fanno parte della catena `tuning_evaluations` → `report.md` → produzione → app finché non è chiusa per `agglomerative`, `hdbscan` e `hdbscan_soft`. Le loro colonne dello sweep non si ricalcolano e `evaluate_clustering_tuning` li rifiuta (`adp`: solo `report.md`).
- **`internal_metrics`**: ricalcola dalle etichette salvate le colonne dello sweep (agglomerative, hdbscan, hdbscan_soft) e le riscrive in `tuning_results.csv`, solo con `overwrite: true`; non è nei config di default.

## Lavoro attivo / thread aperti

- **s2.4-vol del 16-10** (SDC voxelwise, voxel fuori dal brain azzerati, 227235 colonne, 5845 soggetti): PCA in produzione a 12 componenti varimax; tuning di agglomerative, `hdbscan`, `hdbscan_soft` sugli score PCA. Dettaglio e decisioni in `docs/experiments/s2.4-vol.md`. Clustering di produzione: 29 run su 30, **manca** `hdbscan_soft` nc10 `min_cluster_size=100`, `min_samples=20`, `eom` sulla matrice del 16-10.
- **Tuning e produzione già scritti prima del 22-10**: i `report.md`, `density_metrics.csv` e `tuning_plot*.png` di HDBSCAN hanno ancora le colonne vecchie (silhouette, CH, DB) e non il DBCV. Si rigenerano con `evaluate_clustering_tuning` e `overwrite: true`; le run di produzione non si rigenerano.
- **`hdbscan_soft`** (pacchetto `hdbscan`) è un metodo a sé, **non confrontabile** con `hdbscan` di sklearn (`methods_changelog.md` 15-10-26). `membership_mean` e `persistence_mean` nascono dal fit e nessuna valutazione le ricalcola; la persistenza non esiste per `hdbscan` di sklearn (decisione: non si calcola).
- **Metadati (06-10-26)**: forzatura del lato WashU spenta. Restano i controlli E e F e cosa fare delle maschere capovolte nelle matrici (`open_problems.md`, `methods_changelog.md` 06-10-26).
- **Audit dei passi prima di `dim_reduction`/`clustering`**: aperto. Serve una mappa completa, verificata dal codice, di ciò che ogni pipeline legge, poi una guida unica con i comandi. `docs/experiments/pipelines.md` ne è un disegno parziale.
- **`clustering_comparison.ipynb`**: homogeneity e completeness scambiate (`lessons_learned.md` #41), da togliere dal notebook; non toccare senza chiederlo all'utente.
- **`clustering_evaluation.ipynb`**: ha la sezione 2.3 (DBCV) ma non è stato rieseguito dopo le modifiche; da spostare in `notebooks/pipeline_building`.
- **SDC clustering tuning s2.1-schaefer-200-tian-s2**: nc2 documentato; prossimo step: estendere a `nc3`.

L'elenco completo di problemi aperti sta in **`.claude/open_problems.md`**.

## Vincoli/regole in vigore oggi

- **Branch**: `main`. HEAD `790fcc1`. Il working tree contiene lavoro non committato dell'utente (`anatomical_maps.py`, `cluster_overview.py`, `dendrogram_splits.py`, `tuning_match.py` e relativi test, notebook `dendrogram_embedding_explorer`, alcune doc): trattare come suo ciò che non si è toccato, committare solo i propri file, per un file misto solo le proprie modifiche.
- **Regola delle valutazioni del tuning**: tutto ciò che si fa durante lo sweep si può rifare con `evaluate_clustering_tuning.json` e viceversa; una metrica o una figura nuova è una valutazione del registro, non una colonna dello sweep.
- **Niente soglie nostre nei report**: solo misure; l'interpretazione si costruisce con l'utente. Tolti il limite di rumore del 10% e la soglia 0,5 sulla probabilità; il criterio «usabile» è tolto da `s2.4-vol.md` ma resta in `s1.4-vol.md`, `s2.4-stream.md` e `pipelines.md`.
- **Calinski-Harabasz e Davies-Bouldin solo con distanza euclidea**, in ogni posto; regola decisa il 23-10-26: con una distanza non euclidea le celle di CH, DB, Dunn e DBCV restano vuote con la scritta «solo euclidea», la run si vede e la silhouette è nella sua distanza. Applicata al DBCV (`run_dbcv`); per Dunn, CH e DB nel notebook e nella produzione di agglomerative resta da fare.
- **`config/registry/params_*.json` e `config/pipelines/{dim_reduction,clustering}.json`** sono stato mutabile: contengono i valori dell'ultima run (ora `dim_reduction` = PCA di produzione su `16-10_s2.4-vol`, `clustering` = tuning su `19-10_s2.4-vol_nc12_varimax`). Non sono default canonici: riportare la griglia giusta prima di rilanciare un tuning di allora (`lessons_learned.md` #36).
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **Documentazione e codice**: niente dump di tabelle o dati completi nei `.md` (solo pointer a `results/*.csv`). Rationale verbosa confinata in `docs/dev/`. Niente test statistici sulla descrizione clinica dei cluster.
- **Non rigenerare** `results/dim_reduction_strategies.csv` (script ritirato, commit `3e53099`) né le run di produzione già scritte.
- **Sezione "Confronto" dell'Embedding Explorer**: rimossa dall'app e parcheggiata; i builder e i test restano non montati, non sono codice morto.
- **Diagnostic grid oltre 2D**: `n_components > 2` non emette un diagnostic grid automatico — ispezione on-demand via `src/pipeline/plot_tuning_embedding_3d.py`, non è un bug.
- **Copie locali ridotte**: solo `UNIPD/WashU/features/` e `data/derived/features/masked_fc/` restano a 10 soggetti campione (`docs/guides/datasets.md`).
- **`enrich_metadata`**: `overwrite` e `protected_path` obbligatori nel config; con `overwrite: true` una cella vuota nella fonte svuota quella del registro, senza avviso.
- **`excluded_subjects.csv`** è scritto da `build_excluded_subjects`: con `overwrite: false` aggiunge senza toccare le righe esistenti, con `true` ricostruisce dal solo config.

## Prossimo passo esatto

A scelta dell'utente: (1) rigenerare le valutazioni dei tuning HDBSCAN di `19-10_s2.4-vol_*` con DBCV (`evaluate_clustering_tuning.json`, `overwrite: true`, `density_metrics`, `tuning_heatmaps`, `dbcv_curves`) e leggerli con l'utente; (2) lanciare la run di produzione mancante `hdbscan_soft` nc10 `mcs=100`, `ms=20`, `eom` sulla matrice del 16-10; (3) decidere le metriche di agglomerative ancora fuori dal registro (Dunn, quota del cluster più grande, silhouette per cluster); (4) la parte 3 del prompt "Metriche": stessa analisi per la dim reduction.
