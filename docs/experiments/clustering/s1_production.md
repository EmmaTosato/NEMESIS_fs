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

## 01-09-2026 — s1.1

### 6 opzioni di k in esplorazione 

##### Input
- s1.1
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `11-08_s1.1_m_euclidean_nc2` 
- Dati originali: `data/derived/lesion_matrix/21-07_s1.1`
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
| A (k4) | agglomerative | `linkage=average` | 4 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1_m_euclidean_n2_k4_link_average/config.md) |
| A (k4) | gmm | `covariance_type=full` | 4 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1_m_euclidean_n2_n_comp4_cov_full/config.md) |
| A (k4) | kmeans | — | 4 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1_m_euclidean_n2_k4/config.md) |
| B (k5) | agglomerative | `linkage=average` | 5 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1_m_euclidean_n2_k5_link_average/config.md) |
| B (k5) | gmm | `covariance_type=full` | 5 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1_m_euclidean_n2_n_comp5_cov_full/config.md) |
| B (k5) | kmeans | — | 5 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1_m_euclidean_n2_k5/config.md) |
| B (k5) | spectral | `affinity=nearest_neighbors, n_neighbors=30` | 5 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1_m_euclidean_n2_k5_aff_nearest_neighbors/config.md) |
| C (k6) | agglomerative | `linkage=average` | 6 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1_m_euclidean_n2_k6_link_average/config.md) |
| C (k6) | gmm | `covariance_type=full` | 6 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1_m_euclidean_n2_n_comp6_cov_full/config.md) |
| C (k6) | kmeans | — | 6 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1_m_euclidean_n2_k6/config.md) |
| C (k6) | spectral | `affinity=rbf, gamma=1.0` | 6 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1_m_euclidean_n2_k6_aff_rbf/config.md) |
| D (k8, solo spectral) | spectral | `affinity=rbf, gamma=1.0` | 8 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1_m_euclidean_n2_k8_aff_rbf/config.md) |
| E (hdbscan A) | hdbscan | `min_cluster_size=20, min_samples=10` | 8 (+95 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/01-09_s1.1_m_euclidean_n2_mcs20_ms10/config.md) |
| F (hdbscan B) | hdbscan | `min_cluster_size=15, min_samples=5` | 20 (+107 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/01-09_s1.1_m_euclidean_n2_mcs15_ms5/config.md) |

##### Decisioni
