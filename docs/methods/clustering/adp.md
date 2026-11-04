# ADP in NEMESIS

- **Teoria:** [ADP: Advanced Density Peaks (DADApy)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/adp.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Clustering/adp.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/adp.md) (derivata, non è una fonte)

Metodo `adp` di `CLUSTERING_METHODS`, implementato in `src/analysis/adp.py` (`_AdpSession`) sopra `dadapy.Clustering`
(DADApy 0.3.4, ambiente conda `nemesis_fallback`). Parametri: `params_clustering.json`, voce `adp`.
Come si lancia: [guida al clustering](../../guides/clustering.md), sezione "ADP".
Altri metodi: [README](README.md). Metriche condivise: [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).

## Su cosa lo applichiamo
- **Input:** matrici **grezze**, non embedding: lesione binaria (circa 220-270 mila voxel per soggetto), disconnettoma SDC voxelwise
  (circa 230-290 mila), SDC streamline (87 tratti). Circa 1500-5850 soggetti secondo la matrice.
- **Distanza:** `dice`, `jaccard` o `euclidean` (`ADP_METRICS`). Su una matrice continua ≥ 0 (SDC) `dice`/`jaccard` sono le versioni pesate
  (Czekanowski/Ruzicka), che su matrici 0/1 coincidono con le classiche.
- **Distanze esatte:** la matrice $N \times N$ intera è calcolata dal progetto (`pairwise_distance`); a DADApy arrivano solo i `maxk` vicini
  (`Clustering(distances=(distanze, indici), maxk=...)`). Memoria: una matrice `float64` $N \times N$ per metrica, circa 270 MB a 5800 soggetti.
- **Righe a zero:** `dice`/`jaccard` non sono definite; quei soggetti prendono `-1` per ogni metrica.
  **Righe duplicate:** clusterizzate una volta, il gemello eredita l'etichetta (DADApy divide per la distanza dal primo vicino, che sarebbe 0).
- **Ambiente:** `dadapy` dipende da `jax` e vive in `nemesis_fallback` (Python 3.11, `dadapy` 0.3.4, scikit-learn 1.9.1); l'import è lazy.

## Parametri usati (significato: documentazione DADApy)
| Parametro | Nel progetto |
|---|---|
| `Z` | sweep 0,25-16 (18 valori); base 1,65 (= default DADApy) |
| `metric` | `dice`, `euclidean` (anche `jaccard`) |
| `maxk` | `100` fisso; deve essere minore del numero di righe distinte |
| `halo` | `False` fisso |
| `v2`, `alpha`, `algorithm`, `mu_fraction` | default |

Griglia attuale: `metric` ∈ {dice, euclidean} × `Z` (18 valori) = 36 combinazioni.

## Come lo ottimizziamo
`Z` è l'unica manopola. Il progetto non cerca un ottimo ma la **dipendenza da `Z`**:
1. `n_clusters_found` e `largest_cluster_share` (quota nel cluster più grande) al variare di `Z`, in scala logaritmica.
2. `ari_vs_prev_z`: ARI con la partizione al `Z` immediatamente più basso, sui soggetti clusterizzati. Un tratto vicino a 1 con
   `n_clusters_found` fisso è un **plateau**: lì la partizione non dipende dalla soglia.
3. Tabella dei plateau: per ogni numero di cluster, il `Z` minimo e massimo che lo producono (nessuno script la produce: si ricava da `tuning_results.csv`).
4. `n_small_clusters`: cluster con meno di 10 soggetti (`SMALL_CLUSTER_SIZE = 10` è una scelta del progetto, senza fonte).
5. `metric` nella stessa run: le due partizioni si confrontano con l'ARI e con variabili esterne (es. `lesion_side`), non con la silhouette.

Il criterio del plateau è una scelta del progetto. Lettura dei grafici: [clustering_tuning_guide](clustering_tuning_guide.md), "ADP".

## Come leggiamo l'output
- **Silhouette** sulla stessa distanza del clustering (`dice` o `euclidean`). Si legge **dopo** `pairs_at_distance_1`, la quota di coppie a distanza dice
  esattamente 1: sulle lesioni è l'84% e la silhouette resta vicina a 0 qualunque sia la struttura; sulle mappe SDC è lo 0,0015% e si legge normalmente
  (`docs/guides/embedding_app.md`).
- **Purezza dei k vicini** (`knn_purity`): quota dei vicini più prossimi nello stesso cluster, accanto al valore atteso per caso $(n_c - 1)/(n - 1)$.
  Usa solo l'ordine delle distanze, quindi non risente della saturazione. È in parte circolare: ADP costruisce i cluster proprio sui vicini.
- **CH e DB** solo con `euclidean` ([evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md), §3-4).
- **Stima 2NN:** salvata come `id_2nn` in `tuning_results.csv`, uno per `metric`; non dipende da `maxk` (usa solo i primi due vicini).
- Nessuna statistica propria del modello nel pannello "Clustering evaluation". La topografia di DADApy (densità dei picchi e delle selle) esiste
  nell'oggetto (`log_den_bord`) ma il progetto non la salva.

## Attenzioni specifiche
- **Distanza saturata:** con `dice` sulle lesioni l'84% delle coppie è a distanza 1. Un soggetto che si sovrappone a meno di `maxk` altri ha, tra i suoi
  `maxk` vicini, molti soggetti a distanza esattamente 1, a pari merito: i pareggi entrano nel rapporto $\mu$ del 2NN ($\mu = 1$ se primo e secondo vicino
  sono entrambi a 1) e nei volumi del PAk. Effetto sulla stima non verificato: è un ragionamento del progetto da controllare, non un risultato pubblicato.
- La silhouette è inutilizzabile sulle lesioni per la stessa saturazione.
- Con `halo=False` ADP assegna ogni soggetto con distanza definita: il `-1` nelle etichette viene solo dalle righe a zero, non da una decisione di densità.
- `maxk` vicino alla taglia dei cluster piccoli: l'intorno $\hat k_i$ di un soggetto di un cluster piccolo può includere soggetti di altri cluster;
  con `maxk` alto la densità si liscia. Il progetto non sweepa `maxk`: è un'osservazione nostra, non un risultato della fonte.
- ADP gira sulle matrici grezze anche perché UMAP non preserva del tutto la densità; le etichette ADP proiettate su un UMAP 2D servono solo a vederle.
- Distanze esatte $N \times N$: memoria e tempo quadratici.
- Poca letteratura applicativa rispetto ad agglomerativo e HDBSCAN; nessuna esperienza pubblicata nota al progetto su maschere di lesione.
