# Task breakdown

Dettagli operativi definiti nel meeting con Sebastiano (07/07/2026); scope generale dal brainstorming (24/06/2026). La metodologia dettagliata (SDC, embedding, interpretazione clinica) andrà in `docs/methods/` quando formalizzata: qui resta la descrizione a livello di task/workflow.

## Task 1 — Embedding delle lesioni
- n ~ 4000
- Low-dimensional embedding delle lesioni → visualizzazione spaziale
- Clustering topografico

## Task 2 — Embedding degli SDC
- n ~ 3000
- Low-dimensional embedding delle mappe di **SDC** (structural disconnection)
- Metodo: whole-brain SDC alla Foulon/Thiebaut de Schotten, implementato dal **BCBtoolkit**
  - Output per soggetto: statistiche lesione + disconnettoma; disconnettoma parcellizzato su vari atlanti; lesione parcellizzata; disconnettoma non parcellizzato (volumetrico grezzo)
  - Ogni voxel: probabilità 0-1 che la streamline sia disconnessa
- Tecnica di embedding prevista: UMAP
- Razionale: le lesioni riflettono territori vascolari diversi; lesioni in cluster topografici diversi possono ricadere nello stesso cluster SDC se disconnettono le stesse streamline — l'SDC abbassa la dimensionalità rispetto alla sola lesione (che è molto più alto-dimensionale)

## Interpretazione clinica
- Media dei disconnettomi all'interno di ciascun cluster
- Fonte: `participants.tsv`
- NIHSS totale plottabile sull'embedding; sotto-item NIHSS corrispondono a domini specifici (es. item 9 = linguaggio → cluster frontale sinistro; item 11 = neglect; item 5a-6b = motorio)
- Colorare l'embedding con queste informazioni; confrontare la copertura fra i vari dataset

## Task 3 — Connettività funzionale/strutturale
- Feature strutturali e funzionali in arrivo per WashU + Padova + Friburgo (coorti con soggetti sani per costruire le matrici)
- Matrici di connettività funzionale (BOLD) e strutturale (diffusione)

**Workflow previsto:**
1. Cluster degli SDC
2. Per ogni cluster: descrivere la connettività funzionale/diffusione dei soggetti del cluster rispetto ai sani
3. Ripetibile sia per BOLD che per diffusione (numerosità simili)
4. Combinare col cluster anatomico (dalle lesioni): pazienti con la stessa lesione prototipica dovrebbero condividere lo stesso pattern funzionale/di diffusione → risposte contestualizzate e specifiche al sottogruppo clinico/neuroanatomico

Nota terminologica: SDC = stima indiretta del danno; DWI = dato diretto di diffusione (cosa è rimasto).

## Task 4 — EEG
- n ~ 80 (Padova)
- TBD, previsto settembre/ottobre 2026

## Task 5 — Correlazione comportamentale
- n ~ 60
- Correlazione multimodale/multiscala con misure comportamentali

## Aperti / hint
- Come confrontare i clustering ottenuti da embedding diversi
- A livello di spazio fisico nel cervello, capire come il delta (banda di frequenza EEG) spiega gli effetti trovati da Siegel 2016 (vedi letteratura in `assets/papers/`)
- **Meeting di fine luglio 2026** (non ancora verbalizzato in `assets/meetings/`): introduzione stroke, discussione feature space multimodale, Task 1 e Task 2, abbozzo risultati Task 3
