# Spectral clustering in NEMESIS

- **Teoria:** [Spectral clustering](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/spectral.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Clustering/spectral.md`)
- **Letteratura:** nei `sources` della nota teorica

Metodo a grafo: `"spectral"` in `CLUSTERING_METHODS` (`src/analysis/clustering.py`), implementato con `sklearn.cluster.SpectralClustering`
(scikit-learn 1.8.0, ambiente `nemesis`). Parametri: `config/registry/params_clustering.json`, voce `"spectral"`.
Altri metodi: [README](README.md). Metriche condivise: [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).
L'eigengap, specifico di questo metodo, è definito nella nota teorica.

## Su cosa lo applichiamo
- **Input:** embedding UMAP (2, 3, 10 componenti) o score PCA, circa 1100-5900 soggetti a seconda della coorte (1119, 1150, 1570, 5269, 5845 nelle matrici salvate).
  Le run di tuning registrate in `results/legacy/clustering_spectral_kmeans_gmm_adp_28-10-26/{lesion,sdc}/clustering/tuning/spectral/runs_tuning.csv`
  sono tutte su embedding UMAP (metrica UMAP `euclidean`; per le lesioni anche `dice`).
- **Distanza:** lo spectral lavora in distanza euclidea sulle coordinate dell'embedding.
- **`gamma` dipende dalla scala dell'embedding.** Misura sull'UMAP a 2 componenti di `s2.2-vol` (1570 soggetti,
  `results/sdc/dim_reduction/production/umap/07-09_s2.2-vol_m_euclidean_nc2`): distanza al quadrato mediana tra due soggetti circa 25.9.
  Quota di coppie con affinità sotto $10^{-6}$: 7% con $\gamma=0.1$, 66% con $\gamma=1$, 89% con $\gamma=5$.
  Lo stesso $\gamma$ su uno spazio PCA, con scala diversa, costruisce un grafo diverso: i valori della griglia non sono trasferibili tra embedding.
- **Memoria:** `rbf` costruisce una matrice densa $n \times n$ in `float64`, circa 273 MB a 5845 soggetti; `nearest_neighbors` una matrice sparsa.
- **Connettività:** con un grafo `nearest_neighbors` a `n_neighbors` piccolo, isole separate dell'embedding diventano componenti connesse distinte,
  e lo spectral le separa per costruzione. scikit-learn avvisa quando il grafo non è connesso.
- **Determinismo:** con `assign_labels="cluster_qr"` e il solutore di default (`arpack`), `random_state` fissa solo il vettore di partenza di ARPACK (letto nel codice installato).
  Se il grafo è connesso le etichette sono identiche tra semi; se ha più componenti connesse l'autospazio dell'autovalore 0 è degenere,
  ARPACK ne restituisce una base che dipende dal seme e le etichette cambiano. Con lo stesso seme due run danno sempre lo stesso risultato.
  Prova sull'UMAP a 2 componenti di `s2.2-vol` (1570 soggetti), 4 semi, `n_clusters` in 2, 3, 5, 8, 12, 20, 30:
  - etichette identiche tra semi per `rbf` (`gamma` 0.1, 1, 5), per `nearest_neighbors` con 50 vicini e (provati `n_clusters` 5 e 12) con 30 vicini, tutti a grafo connesso;
  - diverse per `nearest_neighbors` con 10 vicini in tutti e 7 i `n_clusters` (grafo a 4 componenti connesse; l'ARI minimo tra semi va da -0.02 a 0.87).

  Conseguenza: le diagnostiche a semi diversi (RSC) non vedono variabilità solo quando il grafo è connesso
  ([evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md), sezione 7).

## Parametri usati (significato: documentazione scikit-learn)
Default verificati con `inspect.signature(SpectralClustering)` su scikit-learn 1.8.0.

| Parametro | Nel progetto |
|---|---|
| `n_clusters` | base 6; griglia 2-30 |
| `affinity` | base `rbf`; griglia `nearest_neighbors`, `rbf` |
| `gamma` | base 1.0; griglia 0.1, 1.0, 5.0 |
| `n_neighbors` | griglia 10, 30, 50 |
| `assign_labels` | `cluster_qr` |
| `n_components`, `eigen_solver` | default |
| `n_init` | non usato |
| `random_state` | 0 |

La sweep è *affinity-aware* (`run_spectral_affinity_aware_sweep`, `src/analysis/clustering_tuning.py`): `n_neighbors` si prova solo con `nearest_neighbors`
e `gamma` solo con `rbf`, perché scikit-learn ignora in silenzio il parametro che non si applica. Totale: $29 \times (3 + 3) = 174$ fit.

## Come lo ottimizziamo
1. **Prima il grafo, poi $k$:** la scelta di `affinity` e del suo iperparametro decide quale struttura lo spectral può vedere.
   Punto di partenza per i vicini: ordine di $\log n$ ($\log 5845 \approx 8.7$), controllando che il grafo sia connesso (von Luxburg).
2. **Eigengap** (`eigengap_affinity=<affinity>.png`, un pannello per valore di `n_neighbors` o `gamma`): $\hat k$ è dove cade il salto più grande tra autovalori consecutivi.
   Lettura: [clustering_tuning_guide](clustering_tuning_guide.md), "Spectral - eigengap".
3. **Indici geometrici per `n_clusters`:** silhouette, CH, DB in `tuning_plot.png`, una linea per combinazione (`affinity`, iperparametro).
4. **Self-tuning** (Zelnik-Manor & Perona): funzione post-hoc `compute_self_tuning_eigengap`, non collegata alla pipeline; ogni punto ha la sua scala $\sigma_i$,
   la distanza dal suo 7° vicino. Toglie `gamma` dalla sweep: se l'eigengap self-tuning indica lo stesso $k$ della griglia, la scelta di `gamma` non era decisiva.
5. **Stabilità del numero di cluster** (opzionale, blocco `"consensus"`): vedi sezione 7 di
   [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).
   Con `cluster_qr` la stabilità rispetto al seme è perfetta se il grafo è connesso, e non lo è con un grafo a più componenti (`n_neighbors` piccolo):
   in quel caso misura la degenerazione dell'autospazio, non la struttura dei dati. La versione su sottocampioni (Monti) resta informativa in entrambi i casi.

## Come leggiamo l'output
- **Eigengap** come criterio interno del metodo.
- **Indici geometrici:** `compute_clustering_metrics` li calcola in distanza euclidea su $X$ (accetta `rbf` e `nearest_neighbors` come compatibili).
  Vanno letti come confronto tra combinazioni, non come giudizio assoluto.
- **Connettività:** un avviso "graph is not fully connected" significa che parte dei cluster è determinata da componenti già separate nel grafo.
- **Dimensioni dei cluster:** cluster tutti di dimensione simile sono un effetto atteso del normalized cut, non necessariamente dei dati.

## Attenzioni specifiche
- **`gamma` non è trasferibile** tra embedding o sessioni: con $\gamma=1$ su un UMAP 2D due terzi delle coppie hanno affinità praticamente nulla.
- **Un solo parametro del grafo per volta:** `n_neighbors` con `rbf`, o `gamma` con `nearest_neighbors`, vengono ignorati senza errore. La sweep del progetto lo evita.
- **Eigengap del progetto e grafo di sklearn non coincidono del tutto:** `compute_eigengap` costruisce il grafo `nearest_neighbors` con `include_self=False`,
  mentre `SpectralClustering` usa `include_self=True` (codice di scikit-learn 1.8.0). `include_self=True` conta il punto stesso tra i `n_neighbors`:
  il grafo clusterizzato ha `n_neighbors` - 1 vicini veri per nodo, quello dell'eigengap `n_neighbors`. La diagonale di $W$ non conta, perché `csgraph.laplacian` la ignora (verificato).
  Gli autovalori del plot sono quindi di un grafo leggermente diverso da quello clusterizzato
  (a 2000 punti sintetici e 50 vicini, il secondo autovalore vale 0.00433 nel plot contro 0.00423 con `include_self=True`).
- **`cluster_qr` rende le ripetizioni identiche solo a grafo connesso:** lì ripetere lo spectral a semi diversi non produce diversità, quindi l'RSC non dice nulla.
  Con un grafo a più componenti il seme cambia la base dell'autospazio degenere e quindi le etichette.
- **Indici euclidei su un metodo a grafo:** possono sottovalutare cluster non convessi.
