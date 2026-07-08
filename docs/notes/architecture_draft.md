# Bozza architettura NEMESIS (draft — non normativo, cambierà)

Nota di brainstorming, non documentazione ufficiale. Il contenuto qui si aggiorna man mano che decidiamo davvero le cose; non riflette per forza lo stato del codice.

Idea di massima: pipeline in 3 fasi, da costruire incrementalmente una alla volta, senza fissare ora l'interfaccia tra le fasi (si vede di volta in volta).

## 1. Data retrieval
Recuperare, per ora:
- lesioni: sequenze native (`anat`) e maschera di lesione in MNI (`derivatives/manual_masks`)
- metadata: `participants.tsv` quando presente

In futuro anche le features di connettività (funzionale/strutturale) già estratte.

Fonti dati:
- `Clinical_connectome` (WashU, PASPORT, PSP, stroke_UKLFR per ora) — in lavorazione
- NEMESIS (`NEMESIS_BIDS` + derivati separati) — struttura diversa (sessioni, prefissi soggetto diversi), da gestire più avanti, non ancora chiaro come si integra col resto

## 2. Processing
Pipeline vere e proprie, es.:
- eventuale pre-processing iniziale
- lesion mapping alla Thiebaut (BCBtoolkit) --> calcolo SDC — output di input per gli step successivi (da capire meglio quali)

## 3. Analysis
Prendere l'output del processing e:
- UMAP / altri embedding
- clustering
- confronto tra clustering diversi
- correlazione con behavior, demografia, dati clinici
- plotting

---
Tutto da rivedere. Non prendere questa nota come specifica.
