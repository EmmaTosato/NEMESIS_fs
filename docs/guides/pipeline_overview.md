# Panoramica metodologica delle pipeline

Cosa fa, in termini di metodo, ogni pipeline attiva, dal dato grezzo ai cluster. Comandi, input/output e ordine di lancio sono in [`pipeline_order.md`](pipeline_order.md); i parametri nella guida di ogni pipeline (link a ogni sezione); il perché delle scelte implementative in [`docs/dev/`](../dev/pipeline_flow.md).

## Il filo logico

```
registro soggetti ──► misure sulle maschere ──► lista esclusi ──► matrici ──► embedding ──► cluster ──► valutazione
 (chi esiste)          (volume, lato, sede,       (chi resta         (lesione,    (PCA, UMAP,   (6 metodi +   (report del tuning,
                        disconnessione)            fuori)             SDC, FC)     t-SNE, ...)   ADP)          app Dash)
```

Tre principi valgono in ogni passo:

- **Niente fallback silenziosi.** Un input mancante, ambiguo o fuori formato ferma la run con un errore che lo nomina; un caso limite si dichiara, non si copre.
- **Stessa coorte per costruzione.** Lesione e SDC leggono la stessa lista di esclusi, quindi un confronto tra modalità confronta gli stessi soggetti, salvo la matrice streamline (5831 soggetti invece di 5845: 14 hanno tutte le feature a zero).
- **Nessuna soglia nostra nelle valutazioni.** I report danno misure; l'interpretazione si costruisce a mano.

---

## 1. Metadati dei soggetti

Un solo registro (`participants.csv`), più tre file di misure separati. Guida: [`metadata.md`](metadata.md).

| Pipeline | Metodo |
|---|---|
| `populate_metadata` | Unisce i tsv grezzi alle cartelle dei soggetti su disco. Registra **chi esiste** e quali dati ha (`has_lesion`, `has_sdc`, `has_features`). Il gruppo (stroke, controllo...) si ricava dall'ID, validato contro un elenco chiuso di siti: un sito non registrato solleva, non viene indovinato. |
| `compute_lesion_metadata` | Per ogni maschera calcola volume, frazione fuori dal brain, indice di lateralità, lato e sede. Volume e lato si misurano **dopo** l'azzeramento dei voxel fuori dal brain; la frazione **prima**, perché serve a decidere chi escludere. |
| `compute_sdc_metadata` | Per ogni mappa di disconnessione calcola carico (somma delle probabilità) e media, solo **dentro** il cervello, senza soglia. |
| `enrich_metadata` | Join che porta nel registro età, sesso, istruzione, NIHSS, lato, sede, volumi e disconnessione. Non apre immagini. |
| `build_excluded_subjects` | Scrive la lista degli esclusi dal solo elenco del config, con motivo e valore. |

Scelte metodologiche:

- **Lateralità.** Indice `(sinistra − destra) / (sinistra + destra)`. Sotto la soglia `side_threshold` (0,20) il lato è `both`. La soglia è calibrata su 1445 soggetti con etichetta clinica vera (accordo 97,4%), non scelta a mano. Una lesione sul piano mediano non ha lato.
- **Due griglie (1 e 2 mm).** Il confronto dei volumi dice se una lesione piccola sia sparita nel ricampionamento a 2 mm.
- **Sede.** Ogni lesione dentro il brain è ripartita su sette categorie (sottocorticale, corteccia, sostanza bianca, infratentoriale...) con tre atlanti Harvard-Oxford; la categoria dominante è la sede. I voxel su cui due atlanti non concordano sono una categoria a parte: misurano l'incertezza dell'atlante, non una sede.
- **Esclusioni.** Nessuna soglia di qualità fissa nelle pipeline: i dati non hanno un salto naturale, il giudizio sul caso limite è dell'analisi. Il criterio di qualità in uso è l'eccesso di voxel fuori dal brain (oltre il 30%); a questo si aggiungono due motivi tecnici, la maschera vuota (`empty_mask`) e le feature tutte a zero nella matrice streamline (`all_zero_features`). Le lesioni piccole non si escludono.
- **Valori mancanti.** Una cella vuota è un caso di dominio (una maschera vuota non ha frazione fuori dal brain), mai uno 0 di comodo.
- **Variabili protette.** `enrich_metadata` con `overwrite: false` scrive solo le celle vuote; ciò che è in `participants_protected.json` non si tocca mai.

---

## 2. Matrici soggetti × feature

Tre rami indipendenti. Ognuno scrive `matrix.npy`, `metadata.csv` (stesso ordine di riga), `manifest.json`, `config.md`. Una colonna deve significare la stessa cosa per tutti i soggetti.

### 2a. Lesione — [`matrix_building.md`](matrix_building.md)

- **Cosa:** ogni maschera 3D binaria diventa una riga di voxel (0/1).
- **Griglia comune.** Le maschere hanno tre affine diversi (orientamento LAS o RAS, origini diverse) a parità di shape. Ogni maschera con shape **o** affine diversi dal template è ricampionata sulla sua griglia (2 mm), con interpolazione `nearest` e binarizzazione. Confrontare la sola shape non basta.
- **Un file per soggetto.** Il numero di maschere deve coincidere col numero di cartelle; un duplicato, un file mancante o una maschera nella cartella sbagliata fermano la run.
- **Fuori dal brain.** Con `correct_out_of_brain` i voxel fuori dalla maschera cerebrale sono azzerati e il soggetto resta, con il volume ricalcolato. È una correzione; l'esclusione dei casi troppo contaminati sta in `excluded_subjects.csv`.
- **Colonne costanti.** I voxel mai lesionati sono tolti (non cambiano nessuna distanza); `non_constant_mask.npy` permette di riportare le colonne sulla griglia piena.

### 2b. Disconnessione (SDC) — [`sdc_matrix_building.md`](sdc_matrix_building.md)

La disconnessione viene da BCBToolKit, a monte. Tre rappresentazioni, una per run:

| `representation` | Righe × colonne | Valori | Allineamento |
|---|---|---|---|
| `parcellated` | soggetti × regioni di un atlante (Schaefer + Tian) | una statistica per regione (es. sovrapposizione media) | per **nome regione**, su una lista fissa; le regioni omesse da BCBToolKit sono 0, nessuna colonna scartata |
| `voxelwise` | soggetti × voxel | probabilità di disconnessione continua 0-1, mai binarizzata | ricampionamento `nearest` sulla griglia comune; colonne costanti scartate |
| `streamline` | soggetti × 87 tratti di sostanza bianca | quota di streamline del tratto colpite | per **nome tratto**; un tratto mancante ferma la run |

- **Ammissione.** Un soggetto entra se ha lesione registrata, file SDC e non è escluso. Un soggetto con SDC ma senza maschera è escluso esplicitamente, non trattato come «disconnessione zero».
- **Fuori dal brain (`voxelwise`).** La trattografia esce dal cervello (mediana 0,80% della massa, massimo 15,3%). `correct_out_of_brain` azzera quei voxel: la somma di una riga coincide con `disconnection_load_voxels_2mm` dei metadati. Una matrice già costruita non si corregge sul posto: si costruisce una sessione nuova.

### 2c. Connettività funzionale (FC) — [`fc_matrix_building.md`](fc_matrix_building.md)

- **`mask_fc`**: sovrappone la lesione alla rete FC del paziente e marca `NaN` i nodi coperti dalla lesione. Il `mask_summary.csv` dice quanti nodi ha perso ogni soggetto.
- **`build_fc_matrix`**: vettorizza ogni rete (scarta la parte ridondante) e impila i soggetti di un solo gruppo (`ST` dalle reti mascherate, `HC` dalle reti grezze); le connessioni costanti per tutti sono rimosse e loggate.
- **Scelte:** i `NaN` restano `NaN` (queste pipeline non imputano); nessun paziente è escluso per troppi nodi persi (soglia non implementata di proposito). Il ramo non legge né il registro né la lista degli esclusi.

---

## 3. Riduzione della dimensionalità — [`dim_reduction.md`](dim_reduction.md)

Comprime la matrice in poche coordinate per soggetto. Metodi: `pca`, `umap`, `tsne`, `pacmap`. Teoria dei metodi in [`knowledge/notes/dim_reduction_clustering/dim_reduction_methods/`](../../knowledge/notes/dim_reduction_clustering/dim_reduction_methods/README.md).

**Due modalità.** *Tuning* (`fine_tuning: true`): griglia di iperparametri, una riga di `tuning_results.csv` per combinazione. *Produzione*: un solo embedding con i parametri scelti.

- **Punteggio dello sweep.** Trustworthiness per UMAP/t-SNE/PaCMAP (quanto i vicini nell'embedding erano vicini nei dati), varianza spiegata cumulata per PCA. Vale la stessa metrica con cui l'embedding è stato costruito (jaccard, dice, euclidea), non quella di default della libreria.
- **Distanze precalcolate.** Per jaccard/dice/euclidea la matrice delle distanze si calcola una volta e si riusa in tutte le combinazioni; così la ricerca dei vicini è esatta anche oltre i 4096 soggetti, dove `umap-learn` passerebbe a una ricerca approssimata.
- **PCA.**
  - Sulla covarianza (variabili centrate) o sulla correlazione.
  - Matrici larghe: calcolo a blocchi di colonne. Con più variabili che soggetti si usa la forma duale (matrice soggetti × soggetti), che dà gli stessi risultati a costo molto minore.
  - Rotazioni ortogonali (es. varimax) opzionali: le componenti ruotate non hanno più un ordine per varianza. `rotation_n_components` ruota un pool più grande e tiene le componenti con più varianza.
  - Il numero di componenti si fissa, oppure si chiede una quota di varianza.
- **Visualizzazione.** Un embedding a più di 2-3 componenti non si «taglia» alle prime colonne (UMAP/t-SNE non ordinano le dimensioni per importanza): si rifitta a 2 componenti con gli stessi iperparametri. Oltre 2 componenti l'esplorazione è nell'app Dash.
- **Valutazioni sugli embedding.** `plot_hdbscan` (HDBSCAN su ogni combinazione) e le altre di `tuning_evaluations` si rilanciano su un tuning salvato con `evaluate_dim_reduction_tuning`, senza rifare lo sweep ([`evaluate_dim_reduction_tuning.md`](evaluate_dim_reduction_tuning.md)).

---

## 4. Clustering — [`clustering.md`](clustering.md)

Raggruppa i soggetti sull'embedding (di norma) o sulla matrice. Il numero di cluster non si sceglie in automatico: si legge il tuning.

| Metodo | Idea | Si sceglie |
|---|---|---|
| `kmeans` | partizione per centroidi | `k` |
| `agglomerative` | fusioni successive dei cluster più vicini, poi taglio dell'albero; deterministico | `k`, `metric`, `linkage` (`ward` solo con euclidea) |
| `gmm` | miscela di gaussiane | `n_components`, `covariance_type` (confrontabile con AIC/BIC) |
| `spectral` | grafo di affinità, autovettori | `k`, affinità e suo iperparametro |
| `hdbscan` | zone dense a densità diversa; il numero di cluster emerge, `-1` è rumore | `min_cluster_size`, `min_samples` |
| `hdbscan_soft` | stesso algoritmo col pacchetto `hdbscan`: probabilità di appartenenza per cluster; **non confrontabile** con `hdbscan` (diversa convenzione su `min_samples`) | più `cluster_selection_method` |
| `adp` | Advanced Density Peaks (`dadapy`), sulla matrice grezza, in un ambiente a parte | — |

**Tuning.** Ogni combinazione riceve indici interni di qualità: silhouette (nella metrica della run), Calinski-Harabasz e Davies-Bouldin (solo con distanza euclidea; vuoti altrimenti), DBCV per gli HDBSCAN (rumore compreso; NaN con meno di 2 cluster). Per HDBSCAN si legge sempre insieme alla frazione di rumore.

**Stabilità** (opzionale): ripetizione con seed diversi (dipendenza dall'inizializzazione) per kmeans e gmm; sottocampionamento (dipendenza dal campione) per kmeans, gmm e spectral.

---

## 5. Valutazione del tuning di clustering — [`evaluate_clustering_tuning.md`](evaluate_clustering_tuning.md)

Una sola catena, usata sia alla fine dello sweep sia a posteriori su un tuning salvato: **sweep → valutazioni → `report.md`**. Quello che si fa nello sweep si può rifare a posteriori e viceversa.

- **Valutazioni per metodo** (`tuning_evaluations`):
  - `agglomerative`: correlazione cofenetica, salto del dendrogramma, accordo tra linkage (ARI), quota del cluster più grande, indice di Dunn, dendrogrammi.
  - `hdbscan` e `hdbscan_soft`: DBCV, quota del cluster più grande, heatmap e curve.
- **Dove vanno i risultati.** Una valutazione che dà un valore per combinazione aggiunge colonne a `tuning_results.csv` (unione per chiave, mai per posizione; una colonna esistente si sostituisce solo con `overwrite: true`). Le tabelle con altra chiave e le figure hanno file propri.
- **`report.md`** legge i file, non calcola. Le spiegazioni degli indici stanno in `utils/report_texts/clustering_tuning.md`.
- **Fuori dalla catena:** `kmeans`, `gmm`, `spectral`, `adp`; `evaluate_clustering_tuning` li rifiuta.

---

## 6. Esplorazione e confronto dei risultati

Non sono pipeline di calcolo a catena: leggono run già scritte.

- **Embedding Explorer** (`embedding_app`, [`embedding_app.md`](embedding_app.md)): app Dash su una run di produzione.
  - Colorazione per variabili cliniche e lesionali.
  - Anatomia della lesione, mappe di sovrapposizione e di disconnessione per cluster, soggetto rappresentativo.
  - Descrizione clinica dei cluster (tabelle, **senza test statistici**) e composizione.
  - Valutazione della run (indici geometrici o DBCV), dendrogramma, mappe delle componenti.
- **Confronto tra run** (`clustering_comparison.ipynb`, [`evaluation.md`](evaluation.md)): accordo tra partizioni (ARI, NMI, VI), tabella di contingenza, abbinamento dei cluster, distanze tra cluster nello spazio dell'embedding.
- **Report «Understanding UMAP»** ([`understanding_umap_report.md`](understanding_umap_report.md)): report HTML sull'effetto degli iperparametri, da un tuning UMAP + t-SNE salvato.
