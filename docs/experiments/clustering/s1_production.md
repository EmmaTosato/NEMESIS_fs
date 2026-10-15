# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Parametri scelti a valle del tuning ([`s1_tuning.md`](s1_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni
- In ogni `config.md` `params_file` punta a un file temporaneo: i parametri veri sono in `config.md` e `runs.csv`.

---

## 12-10-2026 — s1.4-vol

### Produzione ampia dopo il tuning

##### Input
- s1.4-vol
- Embedding: UMAP `{dice,euclidean}` × `n_components`∈{2,10}, `08-10_s1.4-vol_m_{dice,euclidean}_nc{2,10}`
- ADP: matrice grezza `data/derived/lesion_matrix/07-10_s1.4-vol` (5845 × 221955)
- 5845 soggetti
##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Produrre i cluster dei candidati del tuning del 12-10 ([`s1_tuning.md`](s1_tuning.md)), non un solo k: ogni run è una lettura a una risoluzione diversa

##### Risultati

67 run concluse.

| Metodo | Parametri | Input | Run | Cluster | Link |
| --- | --- | --- | --- | --- | --- |
| agglomerative | `ward, euclidean`, k = 3, 6, 8, 11, 13, 16, 20 | dice nc2 | 7 | k | [runs.csv](../../../results/lesion/clustering/production/agglomerative/runs.csv) |
| agglomerative | k = 3, 4, 5, 7, 8, 9, 17 | dice nc10 | 7 | k | stesso |
| agglomerative | k = 3, 7, 11 | euclidean nc2 | 3 | k | stesso |
| agglomerative | k = 3, 4, 5, 6, 8, 10 | euclidean nc10 | 6 | k | stesso |
| hdbscan | 100/{1,5,10,20}, 75/{10,20}, 50/20, 30/20, 10/20, 15/20, 20/20, 75/1, 75/5, 50/10 | dice nc2 | 14 | 8-20 (rumore 0.6-12.7%) | [runs.csv](../../../results/lesion/clustering/production/hdbscan/runs.csv) |
| hdbscan | 100/{1,5,10,20}, 75/20, 50/10, 50/20, 30/20, 75/5, 75/10, 75/1, 30/10 | dice nc10 | 12 | 8-20 (0.3-13.6%) | stesso |
| hdbscan | 100/10, 100/1, 75/10, 75/5, 75/1 | euclidean nc2 | 5 | 11-19 (10.9-13.6%) | stesso |
| hdbscan | 100/20, 100/5, 75/20, 100/1, 100/10, 75/10, 50/20, 75/5, 75/1 | euclidean nc10 | 9 | 12-20 (12.7-19.6%) | stesso |
| adp | `dice`, Z = 2.5, 3.0, 3.5, 4.0 | matrice grezza | 4 | 17, 15, 12, 7 | [runs.csv](../../../results/lesion/clustering/production/adp/runs.csv) |

HDBSCAN: sigla `min_cluster_size/min_samples`. Cartelle: `<dd-mm>_s1.4-vol_<embedding>_<tag>` sotto `production/<metodo>/umap/` (`raw/` per ADP).

- Il k nel nome e il numero di cluster coincidono con il tuning in tutte le run.
- Le 19 run su dice nc10 sono disegnate sul gemello 2D `12-10_s1.4-vol_m_dice_nc2` (`n_neighbors=50`, creato apposta): il dice nc2 scelto ha `n_neighbors=100` e il controllo di coerenza lo rifiutava.

##### Decisioni
- HDBSCAN: tutte le righe con 8-20 cluster (40 run). Molte condividono la stessa partizione (ARI ≥ 0.995 tra le righe a 8 cluster dei `dice`): non sono 40 letture indipendenti.
- ADP solo con `dice`: `euclidean` è degenere a ogni Z.
- Il lato lesionale non è trattato: i cluster puri per lato sono attesi (il lato è calcolato dalla maschera).
- ADP copia `matrix.npy` in ogni run (1.2 GB): `production/adp` pesa 4.8 GB.

---

## 03-09-2026 — s1.2-vol

### Schema A-C/E-F su coorte estesa

##### Input
- s1.2-vol
- Embedding: UMAP `euclidean`, n_components=2, `28-08_s1.2-vol_m_euclidean_nc2`
- Dati raw: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
kmeans, gmm, agglomerative, spectral, hdbscan

##### Obiettivo
- Stesso schema di s1.1-vol (k=4/5/6 in parallelo, due candidati HDBSCAN) sui parametri del tuning s1.2-vol ([`s1_tuning.md`](s1_tuning.md))

##### Risultati

| Opzione | Metodi e parametri | Cluster | 
| --- | --- | --- |
| A (k4) | kmeans; gmm `full`; agglomerative `average` | 4 |
| B (k5) | kmeans; gmm `full`; agglomerative `average`; spectral `rbf, gamma=1.0` | 5 |
| C (k6) | kmeans; gmm `full`; agglomerative `average`; spectral `rbf, gamma=0.1` | 6 |
| E | hdbscan `min_cluster_size=100, min_samples=20` | 15 (+1289 rumore) |
| F | hdbscan `min_cluster_size=75, min_samples=20` | 19 (+1216 rumore) |
| G | hdbscan `min_cluster_size=200, min_samples=5` | 7 (+1443 rumore) |

Output: `results/lesion/clustering/production/<metodo>/umap/03-09_s1.2-vol_m_euclidean_nc2_*` ([cartella](../../../results/lesion/clustering/production/)).

- E/F rifatte lo stesso giorno: la prima versione (`mcs=5, ms=10` → 143 cluster; `mcs=30, ms=5` → 53 cluster) era scelta senza conoscere il numero di cluster ([`s1_tuning.md`](s1_tuning.md), re-tuning). Le vecchie cartelle e righe di `runs.csv` sono state rimosse.
- G affianca E/F con granularità più grossolana (silhouette 0.429 contro 0.464 / 0.449). A `mcs=200`, `min_samples` 10 e 20 collassano a 2-3 cluster.

##### Decisioni
- Nessun k unico: le granularità restano aperte in parallelo, come in s1.1-vol.
- Niente opzione D: il picco di spectral (`rbf, k=5, gamma=1.0`) cade già in B.
- Tre candidati HDBSCAN invece di due (E/F/G).

---

## 01-09-2026 — s1.1-vol

### 6 opzioni di k in esplorazione

##### Input
- s1.1-vol
- Embedding: UMAP `euclidean`, n_components=2, `11-08_s1.1-vol_m_euclidean_nc2`
- Dati raw: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- A/B/C: k=4/5/6 in parallelo su più metodi
- D: spectral a k=8 (miglior silhouette assoluto del tuning, 0.502)
- E/F: HDBSCAN a due combinazioni di `min_cluster_size` / `min_samples`

##### Risultati

| Opzione | Metodi e parametri | Cluster |
| --- | --- | --- |
| A (k4) | agglomerative `average`; gmm `full`; kmeans | 4 |
| B (k5) | agglomerative `average`; gmm `full`; kmeans; spectral `nearest_neighbors, n_neighbors=30` | 5 |
| C (k6) | agglomerative `average`; gmm `full`; kmeans; spectral `rbf, gamma=1.0` | 6 |
| D (solo spectral) | spectral `rbf, gamma=1.0` | 8 |
| E | hdbscan `min_cluster_size=20, min_samples=10` | 8 (+95 rumore) |
| F | hdbscan `min_cluster_size=15, min_samples=5` | 20 (+107 rumore) |

Output: `results/lesion/clustering/production/<metodo>/umap/01-09_s1.1-vol_m_euclidean_nc2_*` ([cartella](../../../results/lesion/clustering/production/)).

##### Decisioni
- Nessun k unico: si portano avanti più granularità in parallelo.
- Nessun criterio interno indica un k solo: la silhouette premia k alti, CH cresce con k, l'inertia non ha gomito.
- k non è separabile da `n_components`: il k migliore non converge tra nc2, nc3 e nc10, quindi si decidono insieme, a valle.
- Il confronto tra le opzioni è in [`clustering_comparison.ipynb`](../../../notebooks/post-results_analysis/clustering_comparison.ipynb).
