# HDBSCAN

## Cosa fa

- Clustering **basato sulla densità**: i cluster sono regioni dense separate da regioni rade.
- **Non richiede k**: trova i cluster più stabili al variare della soglia di densità.
- I punti in zone rade sono etichettati come **rumore** (−1).

**Come funziona**

- **Densità locale** (`min_samples`): la densità di un punto si misura dalla distanza del suo `min_samples`-esimo vicino. Se è piccola, la zona è densa. Il modo di contare cambia tra sklearn e il pacchetto `hdbscan`, per questo i risultati non coincidono a parità di numeri.
- **Gerarchia**: si guarda alla densità a tutte le soglie. A soglia bassa c'è un blocco unico. Alzandola, i ponti rari spariscono e il blocco si spezza in cluster sempre più piccoli.
- **Taglia minima** (`min_cluster_size`): una divisione crea due cluster solo se entrambi i pezzi hanno abbastanza punti. Altrimenti i punti del pezzo piccolo "cadono fuori" dal cluster padre: restano nel padre, di solito con probabilità bassa, se il padre è un cluster scelto; sono rumore se non lo è.
- **Stabilità**: si tengono i cluster che sopravvivono su un ampio intervallo di densità.
  - `eom`: può preferire un cluster grande ai suoi figli.
  - `leaf`: prende sempre le foglie dell'albero, cioè i cluster più fini.
  - Nel progetto solo `hdbscan_soft` fa variare la scelta; `hdbscan` (sklearn) usa sempre `eom`.
- **Risultato**: il numero di cluster non si decide in anticipo. Lo determinano `min_cluster_size`, `min_samples` e la stabilità.

| parametro | valore | effetto |
|---|---|---|
| `min_samples` | basso | bastano pochi vicini per dire "zona densa": meno rumore (a 1 quasi tutti i punti sono in un cluster) |
| `min_samples` | alto | contano solo le zone davvero dense: più rumore, cluster ristretti alle zone più dense |
| `min_cluster_size` | basso | anche gruppi piccoli sono cluster: tanti cluster, alcuni poco affidabili |
| `min_cluster_size` | alto | servono gruppi grandi: meno cluster, alcuni si fondono; un gruppo sotto soglia non è un cluster: i suoi punti restano nel cluster padre con probabilità bassa, o sono rumore se il padre non è scelto |

## Che tipo di metodo è

- **Basato sulla densità** e **non supervisionato**.
- Non richiede il numero di cluster e non forza ogni soggetto in un cluster: chi sta in zone rade è rumore.
- Nel progetto, due implementazioni che non si confrontano combinazione per combinazione:
  - `hdbscan`: `sklearn.cluster.HDBSCAN`.
  - `hdbscan_soft`: il pacchetto `hdbscan`, che in più dà la probabilità di appartenere a ciascun cluster.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Etichetta** | il cluster di ogni soggetto; −1 = rumore | una per soggetto |
| **Probabilità di appartenenza** | quanto il soggetto sta nel nucleo del proprio cluster, da 0 a 1 | una per soggetto |
| **Soft membership** (solo `hdbscan_soft`) | la probabilità di stare in ciascun cluster | soggetti × cluster |
| **Stabilità** (solo `hdbscan_soft`) | quanto un cluster dura al variare della densità | una per cluster |

## Esempio concreto

Quattro soggetti e due cluster (valori inventati per illustrare):

| Soggetto | Etichetta | Soft: cluster 0 | Soft: cluster 1 |
|---|---|---|---|
| A | 0 | 0,90 | 0,05 |
| B | 0 | 0,55 | 0,30 |
| C | 1 | 0,02 | 0,85 |
| D | −1 (rumore) | 0,15 | 0,10 |

- A sta nel nucleo del cluster 0. B è nel cluster 0 ma al confine: la probabilità è bassa e l'altro cluster non è lontano.
- D è rumore: ha probabilità bassa su tutti i cluster. Le righe non sommano a 1, e la parte mancante è la probabilità di essere rumore.
- Con `min_cluster_size` = 50 un gruppo di 30 soggetti non è un cluster: se sta lontano da ogni cluster è rumore, se sta vicino a uno viene assorbito con probabilità bassa.

## Come si valuta

- **DBCV**: l'indice interno. Da -1 a 1, più alto è meglio. Per ogni cluster confronta quanto è rado dentro con quanto è lontano dal più vicino; il valore della run pesa ogni cluster per la sua quota di **tutti** i soggetti, rumore compreso, quindi il rumore lo abbassa. Non è definito con meno di 2 cluster.
- **Quota di rumore** e **numero di cluster**: si guardano sempre insieme al DBCV. Nessuna soglia.
- **Non si usano** silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn: si calcolano sui soli soggetti non rumore (se l'algoritmo scarta i soggetti difficili, salgono) e presuppongono cluster compatti.
- **Probabilità di appartenenza**: si legge come media, senza soglia.

Approfondimento: `knowledge/notes/dim_reduction_clustering/hdbscan_package.md` (come funziona, parametri, differenze da sklearn).
