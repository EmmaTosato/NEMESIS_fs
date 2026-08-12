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
- [ ] 💭 **Dimensionalità dell'embedding per il clustering**: decidere n_components (2 vs 5 vs 10).
- [ ] 💭🔥 **Scelta finale `n_neighbors`/`min_dist` di produzione UMAP**.
- [ ] 🔥 **Clustering di consenso/stabilità**: Da eseguire sulla coorte reale (1150 soggetti) per scegliere il k di produzione.
- [ ] 💭 **Step di preprocessing neuroimaging mancanti**: Valutare se/quando serve intervenire in `build_lesion_matrix.py` (es. skull-stripping/denoising).
- [ ] **Config obsoleta `config/pipelines/build_lesion_matrix.json`**: Pulire la config svuotando i campi obsoleti (`"parcellate": false`, `atlas_path` vuoto/rimosso).
- [ ] **Replicare la PCA varimax di Thiebaut de Schotten 2020** sulla lesion matrix NEMESIS.
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
