# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Parametri scelti a valle del tuning ([`s2_tuning.md`](s2_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

_s2.1-schaefer-200-tian-s2 è ferma al tuning (vedi `s2_tuning.md`), in attesa di estendere l'analisi a `nc3` e di decidere la config di produzione. s2.2-vol ha la sua prima run di produzione qui sotto. Struttura entry da usare per le prossime:_

```
## DD-MM-YYYY — sX.X

### <titolo>

##### Input
- sX.X
- Embedding: <metodo, parametri>
- Path Embedding: <cartella `input_path` in `dim_reduction/production/`, es. `31-08_s2.1-schaefer-200-tian-s2_m_euclidean_nc2` — NON la cartella di output di clustering stesso>
- Dati originali: data/derived/sdc_matrix/<...>
- N soggetti
##### Metodi
<metodo scelto>

##### Obiettivo
- ...

##### Risultati

<tabella o descrizione>

##### Decisioni

- ...
```

---

## 10-09-2026 — s2.2-vol

### 5 opzioni di k in esplorazione

##### Input
- s2.2-vol
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `07-09_s2.2-vol_m_euclidean_nc2`
- Dati originali: `data/derived/sdc_matrix/07-09_s2.2-vol`
- 1570 soggetti

##### Metodi
agglomerative, gmm, kmeans, spectral, hdbscan

##### Obiettivo
- Produrre più granularità con la stessa profondità di s1.1-vol/s1.2-vol (l'intero sweep k=2..6 in parallelo su 4 metodi, non solo 2-3 valori), sapendo dal tuning ([`s2_tuning.md`](s2_tuning.md)) che ogni metodo converge sullo stesso taglio emisfero:
  - A-E: k=2/3/4/5/6 su 4 metodi in parallelo (agglomerative, kmeans, gmm, spectral) — stessa struttura a risoluzione crescente, non letture alternative. **C/D/E (k=4/5/6) sono esattamente gli stessi k prodotti per s1.1-vol/s1.2-vol** ([`results/lesion/clustering/production`](../../../results/lesion/clustering/production)); A/B (k=2/3) estendono lo sweep verso il basso, dove il tuning di s2.2-vol (a differenza di s1) mostra il vero massimo
  - F: isola spectral al suo secondo picco (`gamma=5.0`, k=8), un regime diverso da A-E — come l'opzione D di s1.1-vol
  - G/H: hdbscan a due granularità (fine/grossolana), come in s1.1-vol

##### Risultati

| Opzione | Metodo | Parametri | Cluster trovati | Purezza per emisfero *[1]* | Link |
| --- | --- | --- | --- | --- | --- |
| A (k2) | agglomerative | `linkage=average, metric=cosine` | 2 | 0.78 / 0.86 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k2_link_average/config.md) |
| A (k2) | kmeans | — | 2 | 0.72 / 0.86 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k2/config.md) |
| A (k2) | gmm | `covariance_type=spherical` | 2 | 0.73 / 0.86 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp2_cov_spherical/config.md) |
| A (k2) | spectral | `affinity=rbf, gamma=1.0` | 2 | 0.86 / 0.71 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k2_aff_rbf/config.md) |
| B (k3) | agglomerative | `linkage=average, metric=cosine` | 3 | 0.72–0.86 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k3_link_average/config.md) |
| B (k3) | kmeans | — | 3 | 0.66–0.86 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k3/config.md) |
| B (k3) | gmm | `covariance_type=diag` | 3 | 0.66–0.86 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp3_cov_diag/config.md) |
| B (k3) | spectral | `affinity=rbf, gamma=1.0` | 3 | 0.74–0.86 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k3_aff_rbf/config.md) |
| C (k4) | agglomerative | `linkage=average, metric=cosine` | 4 | 0.72–0.90 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k4_link_average/config.md) |
| C (k4) | kmeans | — | 4 | 0.55–0.88 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k4/config.md) |
| C (k4) | gmm | `covariance_type=diag` | 4 | 0.57–0.88 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp4_cov_diag/config.md) |
| C (k4) | spectral | `affinity=rbf, gamma=0.1` | 4 | 0.60–0.87 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k4_aff_rbf/config.md) |
| D (k5) | agglomerative | `linkage=average, metric=cosine` | 5 | 0.52–0.90 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k5_link_average/config.md) |
| D (k5) | kmeans | — | 5 | 0.54–0.88 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k5/config.md) |
| D (k5) | gmm | `covariance_type=tied` | 5 | 0.51–0.89 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp5_cov_tied/config.md) |
| D (k5) | spectral | `affinity=rbf, gamma=0.1` | 5 | 0.62–0.88 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k5_aff_rbf/config.md) |
| E (k6) | agglomerative | `linkage=average, metric=cosine` | 6 | 0.52–0.91 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k6_link_average/config.md) |
| E (k6) | kmeans | — | 6 | 0.49–0.89 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k6/config.md) |
| E (k6) | gmm | `covariance_type=spherical` | 6 | 0.51–0.88 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp6_cov_spherical/config.md) |
| E (k6) | spectral | `affinity=rbf, gamma=1.0` | 6 | 0.42–0.90 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k6_aff_rbf/config.md) |
| F (k8, solo spectral) | spectral | `affinity=rbf, gamma=5.0` | 8 | 0.56–0.91 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k8_aff_rbf/config.md) |
| G (hdbscan A) | hdbscan | `min_cluster_size=10, min_samples=10` | 42 (+369 noise) | 0.40–1.0 | [config.md](../../../results/sdc/clustering/production/hdbscan/umap/10-09_s2.2-vol_m_euclidean_nc2_mcs10_ms10/config.md) |
| H (hdbscan B) | hdbscan | `min_cluster_size=100, min_samples=10` | 5 (+189 noise) | 0.50–0.91 | [config.md](../../../results/sdc/clustering/production/hdbscan/umap/10-09_s2.2-vol_m_euclidean_nc2_mcs100_ms10/config.md) |

*[1] Frazione del cluster occupata dalla categoria `lesion_side` più frequente (left/right/both/unknown) — quanto un cluster è "puro" per emisfero.*

- Ogni opzione, a ogni granularità, resta dominata dal lato della lesione: anche a k=8 (opzione F) e nei 5 cluster di H, la purezza per emisfero non scende mai sotto 0.40 e nella maggior parte dei cluster supera 0.80.
- **Agglomerative non è monotono in k**: la silhouette del tuning cala da k=2 (0.80) a k=4 (0.745), ma risale a k=6 (0.761) — più alta di k=4 e k=5. Non indica una struttura genuinamente diversa a k=6: la purezza per emisfero resta nella stessa fascia (0.52–0.91) delle altre granularità.
- hdbscan (G) trova strutture quasi pure (>0.9 in 30 dei 42 cluster) ma a costo di 369 soggetti (23.5%) scartati come rumore — coerente con quanto già visto nel tuning.
- Nessuna opzione produce un cluster genuinamente misto per emisfero di dimensione paragonabile ai puri — a differenza di s1 (lesioni), dove alcuni cluster misti erano sostanziali.

##### Decisioni

**Stessa decisione di s1: nessun k unico, si tengono aperte le granularità A-H.** Ma qui la ragione è diversa da s1 — non è che criteri diversi indichino k diversi in modo legittimamente ambiguo: è che **nessuna granularità sfugge all'artefatto di lateralizzazione**, quindi tenerle aperte non è "più letture della stessa struttura clinica", è "documentare che la struttura trovabile qui è l'emisfero, a qualunque risoluzione si guardi". Chi userà queste run a valle deve saperlo prima di interpretare un cluster come un sottotipo clinico.
