# Note per le slide sui metodi

Spiegazioni brevi dei metodi di riduzione dimensionale e di clustering usati in NEMESIS, scritte per essere ridette a voce. Il dettaglio e le fonti stanno in `knowledge/notes/dim_reduction_clustering/`, indicato in fondo a ogni metodo.

---

## PCA

### Cosa fa

- Trova nuovi assi, le **componenti**, lungo cui i soggetti differiscono di più.
- Ogni componente è una **combinazione lineare** delle variabili originali: una somma pesata dei voxel.
- Le componenti sono **ordinate per varianza spiegata**: la prima conta più della seconda.
- Tenendo le prime *k* componenti, ogni soggetto è riassunto da *k* numeri invece che da centinaia di migliaia di voxel, perdendo il meno possibile della variabilità.

### Che tipo di metodo è

- **Lineare**: non trova strutture curve.
- **Deterministico**: stessi dati, stesso risultato.
- **Non supervisionato**: usa solo la matrice, non conosce lato, NIHSS o altre variabili.
- Le componenti sono **ortogonali** per costruzione, e pochi soggetti con valori estremi possono dominarne una.
- Nel progetto è calcolata sulla **covarianza**: colonne centrate, non standardizzate, perché tutti i voxel sono sulla stessa scala.

### Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Varianza spiegata** | quanta variabilità cattura ogni componente | una per componente |
| **Loadings** (pesi) | il peso di ogni voxel nella componente; uguali per tutti i soggetti. | voxel × componenti |
| **Score** | la posizione di ogni soggetto sulla componente | soggetti × componenti |

- Lo score dice quanto il pattern del soggetto si allinea alla mappa, e con che intensità. Alto in valore assoluto vuol dire che la mappa è molto presente nel soggetto.
- Il **segno** indica la direzione rispetto alla mappa, ma il segno della componente stessa è arbitrario.
- Nota di vocabolario: tecnicamente i pesi sono gli autovettori, e i *loadings* in senso stretto sono gli autovettori scalati per la radice dell'autovalore. Nella slide si possono usare come sinonimi.

### Esempio concreto

Tre voxel (valori già centrati) e una componente con pesi (0,6; 0,0; 0,8):

| Soggetto | voxel₁ | voxel₂ | voxel₃ | Score |
|---|---|---|---|---|
| 1 | 2 | −1 | 1 | 0,6·2 + 0,0·(−1) + 0,8·1 = **2,0** |
| 2 | −1 | 3 | −2 | 0,6·(−1) + 0,0·3 + 0,8·(−2) = **−2,2** |

- I pesi sono uguali nelle due righe: cambiano i valori dei voxel, quindi cambia lo score.
- Un peso nullo (voxel₂) esclude quel voxel dalla componente.
- Il soggetto 1 ha lo score positivo e il soggetto 2 negativo: stanno ai due lati opposti della stessa componente.

Approfondimento: `knowledge/notes/dim_reduction_clustering/employed_dim_reduction_methods.md`, sezione "PCA e rotazione varimax".

---

## PCA con rotazione varimax

- Parte dalla PCA e **ruota le prime k componenti**, mantenendole ortogonali. L'obiettivo è che ogni componente abbia pesi forti su poche variabili e quasi nulli sulle altre.
- La **varianza totale** spiegata dalle k componenti non cambia, ma si ridistribuisce tra loro.
- Dopo la rotazione le componenti **non sono più ordinate per varianza**.
- Le componenti diventano più interpretabili: "regioni" o pattern distinti.

**Nel progetto**

- Fino a 500 iterazioni, come in Thiebaut de Schotten et al. 2020.
- I punteggi ruotati si ottengono per regressione e hanno tutti varianza 1.
- Per un clustering sulle componenti l'input consigliato sono i punteggi PCA non ruotati.

Approfondimento: `employed_dim_reduction_methods.md`, sezione "La rotazione varimax".

---

## UMAP

- Costruisce un **grafo dei vicini** (k-NN) nello spazio originale, poi cerca un layout a bassa dimensione che lo conservi.
- Preserva soprattutto la **struttura locale**. Le distanze tra cluster lontani, e la loro dimensione apparente, non sono affidabili.
- Iperparametri chiave:
  - `n_neighbors`: ampiezza del vicinato locale. Basso = dettaglio locale, alto = struttura più globale.
  - `min_dist`: quanto possono stare vicini i punti nello spazio ridotto. Non cambia il grafo, ma cambia il layout, quindi anche cosa trova un clustering a densità a valle.
  - `metric`: come si misura la distanza nello spazio originale.
- **Euclidean** va bene per dati continui.
- **Jaccard** e **Dice** sono per dati binari, come le maschere di lesione. Confrontano i voxel in comune rispetto ai totali (intersezione su unione, o 2 × intersezione su somma), non la distanza geometrica.

**Nel progetto**

- Embedding a 2 e a 10 dimensioni.
- Dice ed euclidean sulle lesioni; solo euclidean sull'SDC, che è continua.
- Con Dice i soggetti si separano quasi del tutto per lato: è un artefatto noto della metrica.

Approfondimento: `employed_dim_reduction_methods.md` (sezioni su UMAP e "Scegliere `n_neighbors` e `min_dist`"), `dim_reduction_tuning_guide.md`.

---

## PaCMAP

- Stessa famiglia di UMAP, ma ottimizza **tre tipi di coppie**: vicini, coppie "medie" e coppie lontane.
- Le coppie medie e lontane aiutano a conservare meglio anche la struttura globale.

Approfondimento: `management/notes/pacmap.md`. Non ancora eseguito: non è nelle slide.

---

## Agglomerative

- Parte con **ogni punto come cluster a sé**, poi fonde ripetutamente i **due cluster più vicini**, costruendo un dendrogramma.
- Il numero di cluster si sceglie **tagliando il dendrogramma** (`n_clusters`).
- `metric` misura la distanza tra due punti (euclidea, cosine, manhattan, dice...).
- `linkage` trasforma le distanze tra punti nella distanza tra due cluster, che contengono molti punti:

| linkage | distanza tra due cluster | effetto |
|---|---|---|
| single | la coppia di punti più vicina | tende a formare catene |
| complete | la coppia di punti più lontana | cluster compatti, ma un outlier può dominare |
| average | la media di tutte le coppie | compromesso tra single e complete |
| ward | fonde i due cluster che fanno crescere meno la varianza interna totale | cluster compatti e di taglia simile; richiede la distanza euclidea |

**Nel progetto**: ward con distanza euclidea sugli embedding UMAP.

Approfondimento: `clustering_literature_survey.md` (sezione sul clustering gerarchico), `clustering_tuning_guide.md` (dendrogramma, regola di ward).

---

## HDBSCAN

- Clustering **basato sulla densità**: i cluster sono regioni dense separate da regioni rade.
- **Non richiede k**: trova i cluster più stabili al variare della soglia di densità.
- I punti in zone rade sono etichettati come **rumore** (−1).

**Come funziona**

- **Densità locale** (`min_samples`): la densità di un punto si misura dalla distanza del suo `min_samples`-esimo vicino. Se è piccola, la zona è densa. Il modo di contare cambia tra sklearn e il pacchetto `hdbscan`, per questo i risultati non coincidono a parità di numeri.
- **Gerarchia**: si guarda alla densità a tutte le soglie. A soglia bassa c'è un blocco unico. Alzandola, i ponti rari spariscono e il blocco si spezza in cluster sempre più piccoli.
- **Taglia minima** (`min_cluster_size`): una divisione crea due cluster solo se entrambi i pezzi hanno abbastanza punti. Altrimenti i punti del pezzo piccolo escono dal cluster padre.
- **Stabilità**: si tengono i cluster che sopravvivono su un ampio intervallo di densità.
  - `eom`: può preferire un cluster grande ai suoi figli.
  - `leaf`: prende sempre le foglie dell'albero, cioè i cluster più fini.
- **Risultato**: il numero di cluster non si decide in anticipo. Lo determinano `min_cluster_size`, `min_samples` e la stabilità.

| parametro | valore | effetto |
|---|---|---|
| `min_samples` | basso | bastano pochi vicini per dire "zona densa": più cluster, meno rumore |
| `min_samples` | alto | contano solo le zone davvero dense: più punti diventano rumore |
| `min_cluster_size` | basso | anche gruppi piccoli sono cluster: tanti cluster, alcuni poco affidabili |
| `min_cluster_size` | alto | servono gruppi grandi: pochi cluster, e i gruppi piccoli diventano rumore o restano nel padre |

Approfondimento: `knowledge/notes/dim_reduction_clustering/hdbscan_package.md` (come funziona, parametri, differenze da sklearn).
