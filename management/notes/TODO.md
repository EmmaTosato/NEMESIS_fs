# NEMESIS — TODO di progetto

Lista di lavoro derivata **alla lettera** dalla struttura di [`Research_Proposal.md`](Research_Proposal.md), integrata con lo stato reale di implementazione e i vari meeting. Non è un log — è una lista di lavoro aperta, da spuntare/aggiornare mano a mano.

**Legenda stato**:
- `[ ]` da iniziare
- `[ ]` 🔄 in corso
- `[ ]` ⛔ bloccato (dipendenza esterna)
- `[ ]` 💭 decisione aperta
- `[ ]` ⬛ deferred (rimandato esplicitamente)
- `[ ]` 🔥 priorità confermata

---

## 0. Prerequisiti trasversali

- [ ] ⛔ **Copertura dati incompleta rispetto alla N target**: Il retrieval copre oggi solo 4 dataset (N: 1150). Amburgo, UCL, Santiago in attesa.
- [ ] ⛔ **Copertura longitudinale non determinata**: Da chiarire quali dataset abbiano più timepoint e a quali distanze.
- [ ] ⛔ **SDC in produzione (Task 2)**: Installato e validato su 1 soggetto, ma il run di produzione su scala completa non è partito.
  - [ ] 🔄 installazione condivisa di `bcblib` sul server — in arrivo.
  - [ ] 💭 sogliare la probabilità continua di disconnessione, o tenerla continua?
  - [ ] 💭 il Task 2 usa l'output voxelwise di Stage 1 o le tabelle per-atlante di Stage 2?
  - [ ] 💭 quale sottoinsieme dei (fino a 15) atlanti EBRAINS serve davvero?
- [ ] 🔥 **Armonizzazione neuroCombat tra scanner diversi**: Necessaria almeno per la Fase 2b.
  - [ ] ⛔ **Sotto-blocco**: richiede una covariata di scanner/batch (es. da `acquisition.tsv`), oggi fuori scope.

---

## Fase 1 — Embedding lesioni + clustering (Task 1)

- [ ] 🔄 Coloring embedding per dataset, lato lesione, volume (scala log), NIHSS (punteggio totale) — da rivedere post-run.
- [ ] 🔄 Overlap map/mappa di probabilità delle lesioni per cluster su MNI — da rivedere post-run.
- [ ] ⛔ Estendere la N a tutti i dataset disponibili una volta recuperati (dipende da §0).
- [ ] 💭 **Dimensionalità dell'embedding per il clustering**: decidere n_components (2 vs 5 vs 10). Nessun precedente in letteratura prescrive un default valido in generale (verificato 2026-08 su 4 fonti — Talozzi 2023, de Bodt et al. 2025, doc ufficiale `umap-learn`, critica indipendente — vedi `knowledge/dim_reduction_clustering/dim_reduction_tuning_guide.md` sezione "Quante componenti per UMAP (`n_components`) prima del clustering"). Passi propedeutici, in ordine di priorità:
  - [ ] 🔥 1. Aggiungere a `params_reduction.json` combinazioni UMAP a **3 componenti** per le metriche `dice` ed `euclidean`, per poter sviluppare anche i grafici 3D (oggi solo 2D disponibile in produzione).
  - [x] 🔥💭 2. **Fatto 14-08-26**: `clustering.py` non slice-a più mai `X[:, :2]` (`lessons_learned.md` #16). Nuovo `_resolve_viz_embedding`: riusa `X` se ha già 2/3 colonne, altrimenti legge un embedding "gemello" 2D/3D da un nuovo campo config opzionale `viz_embedding_path` (calcolato a parte, es. via `dim_reduction.py`, stessi iperparametri tranne `n_components`), validato su stessi soggetti/stesso ordine; se nessuno dei due vale, **nessun plot** (mai uno slice) con warning esplicito. Non è un refit interno come `embedding_for_viz` (scartato per complessità, vedi `docs/dev/clustering_migration_plan.md` §2) - un path esplicito invece. Dettagli completi: `docs/dev/clustering_migration_plan.md` §2-3.
  - [x] 🔥 3. **Fatto 14-08-26**: `dim_reduction_clustering.py` eliminato (pipeline, config, job, guida, test) - `clustering.py` guadagna `reduced_data` (dichiarativo) + `viz_embedding_path`, incluso il comparison plot interattivo (`plot_clusters_comparison_interactive`, `cluster_comparison_interactive.html`) che mancava. Piano completo e checklist: `docs/dev/clustering_migration_plan.md`.
- [ ] 💭🔥 **Scelta finale `n_neighbors`/`min_dist` di produzione UMAP**.
- [ ] 🔥 **Clustering di consenso/stabilità**: Da eseguire sulla coorte reale (1150 soggetti) per scegliere il k di produzione.
- [ ] 💭 **Step di preprocessing neuroimaging mancanti**: Valutare se/quando serve intervenire in `build_lesion_matrix.py` (es. skull-stripping/denoising).
- [x] 💭 ~~Rimuovere del tutto la feature `parcellate` da `build_lesion_matrix.py`~~ — **Fatto 25/08.** Decisione esplicita dell'utente (non tecnica): rimossa `parcellate`/`atlas_path`/`parcel_aggregation`/`save_parcellated_volumes` da `src/features/lesion.py` (`_parcellate_matrix`, `load_and_resample_atlas`, `PARCEL_AGGREGATIONS`, `reconstruct_parcel_volume`), `src/analysis/build_config.py`, `src/pipeline/build_lesion_matrix.py` (`_write_parcellated_volumes`) e dal config, con relativi test. Rimossa anche l'intera pipeline `build_combined_atlas.py`/`src/atlases/` (Glasser+Harvard-Oxford 372 regioni) — esisteva solo per alimentare `parcellate` ed era già orfana rispetto alla produzione reale (che usava `Yan300TianS2Buckner7N`, un atlante diverso). Nota sulla sessione precedente (stessa giornata): la motivazione originale della rimozione (2026-08-17, CRITICAL #6/#7 dell'audit del 15/08) era già stata risolta diversamente il 17-18/08 senza toccare `parcellate` (disaccoppiamento di `lesion_volume_voxels`/coloring dalla binarietà di `X`) - quella soluzione tecnica resta valida e non è in conflitto con questa rimozione, che è una scelta di scope, non un fix di bug. `build_lesion_matrix.json` è ora voxel-wise-only, esteso 25/08 anche a UCL-UK/UCLStrokeData (`session_name: "voxelwise_s2"`).
- [ ] **Replicare la PCA varimax di Thiebaut de Schotten 2020** sulla lesion matrix NEMESIS — non più perseguita tramite la parcellazione di `build_lesion_matrix.py` (rimossa 25/08, sopra). Resta un obiettivo di progetto aperto; il meccanismo per arrivarci (nuova pipeline/step dedicato, o un'altra via) è da ripensare.
- [ ] **Confronto cluster vs territori vascolari noti**.
- [ ] **Coloring per subitem NIHSS specifici** (es. linguaggio, neglect, motorio).
- [ ] **Overlap % con atlanti** (vascolare/Yeo/Figley) per cluster.
- [ ] **Radar/spider plot del centroide di cluster**.
- [ ] **Numero di pazienti con lesione bilaterale**.
- [ ] **Confronto sistematico embedding×clustering alla scala n~5750**.

## Fase 2 — Embedding SDC + clustering (Task 2)

- [ ] ⛔ **Bloccata per intero da §0** (SDC non ancora in produzione).
- [ ] Una volta disponibile l'output SDC: stessi metodi di riduzione/clustering della Fase 1, stesse analisi/viz.
- [ ] Replicare il morfospazio UMAP di Talozzi 2023 partendo dalla SDC.

## Fase 2b — Embedding + clustering FC indipendente (Task 3)

- [ ] ⛔ **Copertura dati incompleta**: Solo WashU ha FC oggi. Padova e Friburgo da recuperare.
- [ ] ⛔💭 **Imputazione NaN nella matrice FC**: Decidere e implementare una strategia (imputazione o k-NN) prima del clustering/embedding.
- [ ] Embedding PCA/UMAP sulla matrice FC statica.
- [ ] 💭 Verificare disponibilità delle **timeseries BOLD grezze** per un embedding autoencoder in senso stretto.
- [ ] Armonizzazione neuroCombat (§0) tra scanner ST/HC WashU.
- [ ] Clustering FC (5 metodi).
- [ ] Viz dedicate: matrice FC media per cluster, riassunto per network Yeo, feature locali, composizione per sito.

## Fase 3 — Confronto cluster lesione vs SDC vs FC

- [ ] 🔄 **Non più bloccata rigidamente**: procedere con dati alternativi/già disponibili oggi.
- [ ] Nessun modulo di confronto cross-clustering presente in `src/` (da scrivere, es. `cluster_comparison.py`).
- [ ] Contingency table/heatmap cross-modale.
- [ ] Copertura per dataset nell'embedding.

## Fase 4 — Feature funzionali per cluster anatomico (Task 3)

- [ ] 🔄 Dipendenza da Fase 1/3 attenuata: valutare dati alternativi disponibili.
- [ ] **z-score per singolo paziente vs template sano**, poi mediato per cluster anatomico. Da implementare.

## Fase 5 — Inferenza fenotipo funzionale da cluster anatomico

- [ ] ⛔ Dipende per intero da Fase 1-4.
- [ ] Media delle feature funzionali per cluster anatomico.
- [ ] 💭 Validazione contro il cluster FC indipendente di Fase 2b/3.

## Fase 6 — Feature locali vs globali del segnale FC (Task 3)

- [ ] **Nessuna delle 50 feature del catalogo Volpi è implementata**. Da costruire da zero (ALFF, ReHo, ecc.).
- [ ] Prima applicazione di queste feature a una coorte stroke (esplorazione).
- [ ] Costruire predittori locali intra-cluster usando il catalogo Volpi come punto di partenza.
- [ ] 💭 Requisito dati: verificare se le timeseries BOLD grezze sono recuperabili per WU+PD+Fri.

## Fase 7 — Correlazione con outcome clinico-comportamentale (Task 5)

- [ ] 🔥⛔ **Pipeline Task 5 assente — da eliminare e riscrivere**: Eliminare `prediction.py`/`clinical.py` inutilizzato, verrà riscritto più avanti.
  - [ ] 💭 **Data leakage nella riproduzione Siegel 2016 (`prediction.py::pca_variance_retained`)**: la PCA viene fittata su *tutti* i soggetti (incluso quello poi tenuto fuori a ogni fold LOOCV), non dentro il fold — il soggetto held-out contribuisce a definire le componenti su cui viene poi predetto (leakage che gonfia l'accuratezza stimata). La scelta di λ è invece corretta (LOOCV interno annidato, mai sul soggetto held-out — solo la PCA ne è fuori). È verosimilmente fedele a Siegel et al. 2016 stesso (stesso ordine descritto nel paper), quindi non un bug introdotto qui, ma un limite metodologico noto di quella famiglia di lavori. Trovato durante una revisione di letteratura 2026-08, mai raggiunto in produzione (`predict_deficit.py` non esiste). Se si riscrive la pipeline: valutare uno spostamento del fit PCA dentro il fold (fit su train, transform su test) per una stima non ottimistica, o quantomeno documentare esplicitamente il limite nell'output/report della nuova pipeline. Dettagli completi in `src/analysis/prediction.py`'s module docstring.
- [ ] Ridge regression / PCA sui punteggi comportamentali.
- [ ] Test non parametrici + correzione FDR per validare i cluster contro NIHSS e subitem.
- [ ] Boxplot/violin delle variabili cliniche per cluster.
- [ ] 💭 Testare esplicitamente sulla coorte NEMESIS se i cluster anatomici/SDC aggiungono valore incrementale ai dati clinico-demografici.

## Fase 8 — EEG (Task 4)

- [ ] ⬛ **Deferred esplicitamente a settembre/ottobre 2026**.
- [ ] ⬛ Idea specifica: collegare la mappa di banda delta EEG alla topografia degli effetti di connettività funzionale di Siegel 2016.

---

## 9. Letteratura e mantenimento del proposal

- [ ] **Estendere la letteratura oltre la cerchia NEMESIS** (es. Fallani, clustering longitudinale).
- [ ] 💭 **Verificare la nota "da verificare" della sezione B del proposal**: Le timeseries BOLD grezze sono disponibili per WU+PD+Fri o no? (Condiziona Fase 2b/6).
