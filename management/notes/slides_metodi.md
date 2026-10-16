# Note per le slide sui metodi

Spiegazioni brevi dei metodi di riduzione dimensionale e di clustering usati in NEMESIS, scritte per essere ridette a voce. Il dettaglio e le fonti stanno in `knowledge/notes/dim_reduction_clustering/`, indicato in fondo a ogni metodo. Ogni metodo ha le stesse quattro parti: cosa fa, che tipo di metodo è, cosa restituisce, esempio concreto.

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

- I pesi sono uguali nelle due righe: 
  - cambiano i valori dei voxel, quindi cambia lo score.
  - cambiando da componente a componente
- Un peso nullo (voxel₂) esclude quel voxel dalla componente.
- Il soggetto 1 ha lo score positivo e il soggetto 2 negativo: stanno ai due lati opposti della stessa componente.

Approfondimento: `knowledge/notes/dim_reduction_clustering/employed_dim_reduction_methods.md`, sezione "PCA e rotazione varimax".

---

## PCA con rotazione varimax

### Cosa fa

- Parte dalla PCA e **ruota le prime k componenti**, mantenendole ortogonali.
- L'obiettivo è che ogni componente abbia pesi forti su poche variabili e quasi nulli sulle altre.
- La **varianza totale** spiegata dalle k componenti non cambia, ma si ridistribuisce tra loro.
- Le componenti diventano più interpretabili: "regioni" o pattern distinti.

### Che tipo di metodo è

- **Lineare**, **deterministico** e **non supervisionato**, come la PCA da cui parte.
- Dopo la rotazione le componenti **non sono più ordinate per varianza**.
- Nel progetto: fino a 500 iterazioni, come in Thiebaut de Schotten et al. 2020.
- Per un clustering sulle componenti l'input consigliato sono i punteggi PCA non ruotati.

### Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Pesi ruotati** | il peso di ogni voxel nella componente ruotata | voxel × componenti |
| **Score ruotati** | la posizione di ogni soggetto sulla componente ruotata; si ottengono per regressione e hanno tutti varianza 1 | soggetti × componenti |
| **Quota di varianza** | somma dei pesi al quadrato della componente, divisa per la varianza totale | una per componente |

### Esempio concreto

Quattro voxel e due componenti. Prima della rotazione ogni voxel pesa su entrambe; dopo, ognuno pesa su una sola:

| Voxel | PCA comp. 1 | PCA comp. 2 | Varimax A | Varimax B |
|---|---|---|---|---|
| 1 | 0,71 | 0,71 | 1 | 0 |
| 2 | 0,71 | 0,71 | 1 | 0 |
| 3 | −0,71 | 0,71 | 0 | 1 |
| 4 | −0,71 | 0,71 | 0 | 1 |

- Prima: "un mix di tutto". Dopo: A è la zona dei voxel 1-2, B quella dei voxel 3-4.
- Ogni voxel ha la stessa energia prima e dopo (0,71² + 0,71² = 1² + 0² = 1): cambia solo come si divide tra le componenti.
- Nei dati veri la struttura non è mai così pulita: l'esempio è costruito per mostrare l'effetto.

Approfondimento: `employed_dim_reduction_methods.md`, sezione "La rotazione varimax".

---

## Agglomerative

### Cosa fa

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

### Che tipo di metodo è

- **Gerarchico**, dal basso verso l'alto, **deterministico** e **non supervisionato**.
- Il numero di cluster non è nell'algoritmo: si decide dopo, tagliando l'albero.
- Nel progetto: ward con distanza euclidea sugli embedding UMAP.

### Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Etichetta** | il cluster di ogni soggetto, dato `n_clusters` | una per soggetto |
| **Dendrogramma** | l'albero delle fusioni, con l'altezza (distanza) a cui avviene ciascuna | n − 1 fusioni |

### Esempio concreto

Quattro punti su una retta, in posizione 0, 1, 5 e 7:

| Passo | Fusione | Altezza |
|---|---|---|
| 1 | {0} e {1} | 1 |
| 2 | {5} e {7} | 2 |
| 3 | {0, 1} e {5, 7} | dipende dal linkage |

Altezza del passo 3, dalle quattro distanze tra i due gruppi (0-5 = 5, 0-7 = 7, 1-5 = 4, 1-7 = 6):

| linkage | altezza |
|---|---|
| single | 4 (la più piccola) |
| complete | 7 (la più grande) |
| average | 5,5 (la media) |

- Tagliando a `n_clusters` = 2 si ottengono {0, 1} e {5, 7}, qualunque sia il linkage.
- Il linkage cambia a che altezza si fondono i due gruppi, e con più punti anche quali gruppi si fondono per primi.

Approfondimento: `clustering_literature_survey.md` (sezione sul clustering gerarchico), `clustering_tuning_guide.md` (dendrogramma, regola di ward).

---

## HDBSCAN

### Cosa fa

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

### Che tipo di metodo è

- **Basato sulla densità** e **non supervisionato**.
- Non richiede il numero di cluster e non forza ogni soggetto in un cluster: chi sta in zone rade è rumore.
- Nel progetto, due implementazioni che non si confrontano combinazione per combinazione:
  - `hdbscan`: `sklearn.cluster.HDBSCAN`.
  - `hdbscan_soft`: il pacchetto `hdbscan`, che in più dà la probabilità di appartenere a ciascun cluster.

### Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Etichetta** | il cluster di ogni soggetto; −1 = rumore | una per soggetto |
| **Probabilità di appartenenza** | quanto il soggetto sta nel nucleo del proprio cluster, da 0 a 1 | una per soggetto |
| **Soft membership** (solo `hdbscan_soft`) | la probabilità di stare in ciascun cluster | soggetti × cluster |
| **Stabilità** | quanto un cluster dura al variare della densità | una per cluster |

### Esempio concreto

Quattro soggetti e due cluster (valori inventati per illustrare):

| Soggetto | Etichetta | Soft: cluster 0 | Soft: cluster 1 |
|---|---|---|---|
| A | 0 | 0,90 | 0,05 |
| B | 0 | 0,55 | 0,30 |
| C | 1 | 0,02 | 0,85 |
| D | −1 (rumore) | 0,15 | 0,10 |

- A sta nel nucleo del cluster 0. B è nel cluster 0 ma al confine: la probabilità è bassa e l'altro cluster non è lontano.
- D è rumore: ha probabilità bassa su tutti i cluster. Le righe non sommano a 1, e la parte mancante è la probabilità di essere rumore.
- Con `min_cluster_size` = 50 un gruppo di 30 soggetti non è un cluster: i suoi punti diventano rumore o restano nel cluster padre.

Approfondimento: `knowledge/notes/dim_reduction_clustering/hdbscan_package.md` (come funziona, parametri, differenze da sklearn).
