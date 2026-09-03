# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Parametri scelti a valle del tuning ([`s1_tuning.md`](s1_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

## 01-09-2026 — s1.1-vol

### 6 opzioni di k in esplorazione 

##### Input
- s1.1-vol
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `11-08_s1.1-vol_m_euclidean_nc2` 
- Dati originali: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Produrre 6 opzioni di k 
	- A/B/C variano k (4/5/6) in parallelo su più metodi per confrontare la struttura; 
	- D isola spectral a k=8 (miglior silhouette assoluto del tuning, 0.502); 
	- E/F esplorano hdbscan a due combinazioni `min_cluster_size`/`min_samples`

##### Risultati

| Opzione | Metodo | Parametri | Cluster trovati | Link |
| --- | --- | --- | --- | --- |
| A (k4) | agglomerative | `linkage=average` | 4 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1-vol_m_euclidean_n2_k4_link_average/config.md) |
| A (k4) | gmm | `covariance_type=full` | 4 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1-vol_m_euclidean_n2_n_comp4_cov_full/config.md) |
| A (k4) | kmeans | — | 4 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1-vol_m_euclidean_n2_k4/config.md) |
| B (k5) | agglomerative | `linkage=average` | 5 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1-vol_m_euclidean_n2_k5_link_average/config.md) |
| B (k5) | gmm | `covariance_type=full` | 5 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1-vol_m_euclidean_n2_n_comp5_cov_full/config.md) |
| B (k5) | kmeans | — | 5 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1-vol_m_euclidean_n2_k5/config.md) |
| B (k5) | spectral | `affinity=nearest_neighbors, n_neighbors=30` | 5 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1-vol_m_euclidean_n2_k5_aff_nearest_neighbors/config.md) |
| C (k6) | agglomerative | `linkage=average` | 6 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1-vol_m_euclidean_n2_k6_link_average/config.md) |
| C (k6) | gmm | `covariance_type=full` | 6 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1-vol_m_euclidean_n2_n_comp6_cov_full/config.md) |
| C (k6) | kmeans | — | 6 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1-vol_m_euclidean_n2_k6/config.md) |
| C (k6) | spectral | `affinity=rbf, gamma=1.0` | 6 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1-vol_m_euclidean_n2_k6_aff_rbf/config.md) |
| D (k8, solo spectral) | spectral | `affinity=rbf, gamma=1.0` | 8 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1-vol_m_euclidean_n2_k8_aff_rbf/config.md) |
| E (hdbscan A) | hdbscan | `min_cluster_size=20, min_samples=10` | 8 (+95 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/01-09_s1.1-vol_m_euclidean_n2_mcs20_ms10/config.md) |
| F (hdbscan B) | hdbscan | `min_cluster_size=15, min_samples=5` | 20 (+107 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/01-09_s1.1-vol_m_euclidean_n2_mcs15_ms5/config.md) |

##### Decisioni

---

## 03-09-2026 — s1.2-vol

### Stesso schema (A-C/E-F) su coorte estesa, parametri da s1_tuning.md

##### Input
- s1.2-vol
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `28-08_s1.2-vol_m_euclidean_nc2`
- Dati originali: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
kmeans, gmm, agglomerative, spectral, hdbscan

##### Obiettivo
- Stesso schema di esplorazione di s1.1-vol (opzioni k4/k5/k6 in parallelo su kmeans/gmm/agglomerative, spectral piegato dentro B/C, due candidati hdbscan), applicato ai parametri emersi dal tuning s1.2-vol ([`s1_tuning.md`](s1_tuning.md))
- Nessuna opzione D: a differenza di s1.1-vol (dove il miglior silhouette assoluto di spectral cadeva isolato a k=8), qui il picco assoluto della griglia spectral (`rbf, k=5, gamma=1.0`, 0.426) cade già dentro l'opzione B

##### Risultati

| Opzione | Metodo | Parametri | Cluster trovati | Link |
| --- | --- | --- | --- | --- |
| A (k4) | kmeans | — | 4 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/03-09_s1.2-vol_m_euclidean_n2_k4/config.md) |
| A (k4) | gmm | `covariance_type=full` | 4 | [config.md](../../../results/lesion/clustering/production/gmm/umap/03-09_s1.2-vol_m_euclidean_n2_n_comp4_cov_full/config.md) |
| A (k4) | agglomerative | `linkage=average` | 4 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/03-09_s1.2-vol_m_euclidean_n2_k4_link_average/config.md) |
| B (k5) | kmeans | — | 5 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/03-09_s1.2-vol_m_euclidean_n2_k5/config.md) |
| B (k5) | gmm | `covariance_type=full` | 5 | [config.md](../../../results/lesion/clustering/production/gmm/umap/03-09_s1.2-vol_m_euclidean_n2_n_comp5_cov_full/config.md) |
| B (k5) | agglomerative | `linkage=average` | 5 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/03-09_s1.2-vol_m_euclidean_n2_k5_link_average/config.md) |
| B (k5) | spectral | `affinity=rbf, gamma=1.0` | 5 | [config.md](../../../results/lesion/clustering/production/spectral/umap/03-09_s1.2-vol_m_euclidean_n2_k5_aff_rbf/config.md) |
| C (k6) | kmeans | — | 6 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/03-09_s1.2-vol_m_euclidean_n2_k6/config.md) |
| C (k6) | gmm | `covariance_type=full` | 6 | [config.md](../../../results/lesion/clustering/production/gmm/umap/03-09_s1.2-vol_m_euclidean_n2_n_comp6_cov_full/config.md) |
| C (k6) | agglomerative | `linkage=average` | 6 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/03-09_s1.2-vol_m_euclidean_n2_k6_link_average/config.md) |
| C (k6) | spectral | `affinity=rbf, gamma=0.1` | 6 | [config.md](../../../results/lesion/clustering/production/spectral/umap/03-09_s1.2-vol_m_euclidean_n2_k6_aff_rbf/config.md) |
| E (hdbscan A) | hdbscan | `min_cluster_size=100, min_samples=20` | 15 (+1289 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/03-09_s1.2-vol_m_euclidean_n2_mcs100_ms20/config.md) |
| F (hdbscan B) | hdbscan | `min_cluster_size=75, min_samples=20` | 19 (+1216 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/03-09_s1.2-vol_m_euclidean_n2_mcs75_ms20/config.md) |

- **E/F rifatte lo stesso giorno** (03-09-2026): la prima versione (`mcs=5,ms=10` → 143 cluster; `mcs=30,ms=5` → 53 cluster) era scelta alla cieca sul numero di cluster risultante, mai calcolato durante il tuning. Corretto aggiungendo `n_clusters_found` a `METHOD_METRIC_COLUMNS["hdbscan"]` (`src/analysis/clustering_tuning.py`) e rifacendo il tuning con `min_cluster_size`∈{10,20,30,50,75,100} (vedi `s1_tuning.md`, sezione 03-09-2026) — i due nuovi candidati sopra sono a una granularità comparabile a s1.1-vol (8-20 cluster) e hanno la migliore/seconda migliore silhouette dell'intera griglia rifatta. Le directory di output e le righe `runs.csv` dei due run originali (`mcs5_ms10`/`mcs30_ms5`) sono state rimosse, non lasciate come residuo.

##### Decisioni
