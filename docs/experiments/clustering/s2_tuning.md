# Diario Esperimenti

**Pipeline:** Clustering (Tuning)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 12-10-2026 — s2.4

### Tuning agglomerative, HDBSCAN e ADP su SDC voxelwise (nc2, nc10) e streamline

##### Input
- s2.4-vol: UMAP `08-10_s2.4-vol_m_euclidean_nc{2,10}` (nc3 solo nel confronto tra embedding); ADP su `data/derived/sdc_matrix/07-10_s2.4-vol`; 5845 soggetti
- s2.4-stream: matrice grezza `data/derived/sdc_matrix/07-10_s2.4-stream`, 5831 soggetti × 87 tratti, nessun embedding
##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Leggere i tuning di ogni run con silhouette, Davies-Bouldin e Calinski-Harabasz, per decidere quali partizioni produrre

##### Risultati

| Run | Agglomerative | HDBSCAN | ADP dice | Link |
| --- | --- | --- | --- | --- |
| SDC nc2 | nessun k supera k=2 (0.48); picco a k=5 | nessuna riga utilizzabile | Z=5-6: 3 cluster, silhouette 0.169 | [report](../../../results/reports/cluster_tuning_notebooks/cluster_sdc_euclidean_nc2/report.md) |
| SDC nc10 | average k=3 (0.495); seconda zona a k=14-16 | nessuna riga utilizzabile | Z=5-6: 3 cluster, silhouette 0.169 | [report](../../../results/reports/cluster_tuning_notebooks/cluster_sdc_euclidean_nc10/report.md) |
| streamline | nessuna struttura: massimo a k=2-3 | inutilizzabile | plateau a Z 2.5-4, silhouette ≤ 0.067 | [report](../../../results/reports/cluster_tuning_notebooks/cluster_streamline_raw/report.md) |

- Le silhouette HDBSCAN alte hanno decine di cluster e il 22-40% di rumore; con rumore ≤ 11% la silhouette massima è 0.21 (nc2) e 0.31 (nc10).
- ADP `euclidean`: silhouette negativa a ogni Z.
- Sintesi tra le run: [SUMMARY](../../../results/reports/cluster_tuning_notebooks/SUMMARY.md)

##### Decisioni
- Vedi [`s2_production.md`](s2_production.md), 12-10-2026 e 14-10-2026

---

## 10-09-2026 — s2.2-vol (nc2 e nc3)

### Tuning SDC voxel-wise, 5 metodi

##### Input
- s2.2-vol
- Embedding: UMAP `euclidean`, n_components=2 e 3, `07-09_s2.2-vol_m_euclidean_nc2` / `_nc3`
- Dati raw: `data/derived/sdc_matrix/07-09_s2.2-vol` (1570 × 290940)
- 1570 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Verificare se la versione voxel-wise dell'SDC dà una struttura diversa da quella parcellata (s2.1)

##### Risultati

350 combinazioni (175 per dimensionalità). Miglior silhouette per metodo, `nc2`:

| Metodo | Miglior combo (silhouette) | Link |
| --- | --- | --- |
| Agglomerative | `k=2, average, cosine` (0.800) | [tuning/agglomerative/](../../../results/sdc/clustering/tuning/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| HDBSCAN | `mcs=10, ms=10` (0.619, 42 cluster, rumore 0.24) *[1]* | [tuning/hdbscan/](../../../results/sdc/clustering/tuning/hdbscan/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| KMeans | `k=2` (0.571) | [tuning/kmeans/](../../../results/sdc/clustering/tuning/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| GMM | `n_components=2, spherical` (0.570) | [tuning/gmm/](../../../results/sdc/clustering/tuning/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| Spectral | `k=2, rbf, gamma=1.0` (0.570) | [tuning/spectral/](../../../results/sdc/clustering/tuning/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2/) |

*[1] Soluzione degenere, non confrontabile con le altre righe.*

- Ogni metodo ha il massimo a k=2, in entrambe le dimensionalità (s2.1: k=3-4, silhouette 0.45-0.50). La silhouette è più alta (0.57-0.80) perché la partizione è più netta, non più informativa.
- Il k=2 è l'emisfero: KMeans nc2 ha un cluster con 666 `left` e 0 `right`, l'altro con 571 `right` e 101 `left`.
- A k=4 la struttura si frammenta senza cambiare natura: due cluster `left`, uno quasi tutto `right`, uno misto.
- `nc3` dà silhouette leggermente più basse, stessi ottimi.
- L'artefatto di lateralizzazione di s2.1 è accentuato dalla rappresentazione voxel-wise, non attenuato.

##### Decisioni
- Vedi [`s2_production.md`](s2_production.md), 10-09-2026

---

## 01-09-2026 — s2.1-schaefer-200-tian-s2 (nc2)

### Tuning SDC, 5 metodi

##### Input
- s2.1-schaefer-200-tian-s2
- Embedding: UMAP `euclidean`, n_components=2, `31-08_s2.1-schaefer-200-tian-s2_m_euclidean_nc2`
- Dati raw: `data/derived/sdc_matrix/27-08_s2.1-schaefer-200-tian-s2`
- 1119 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Verificare se l'artefatto `lesion_side` e la silhouette seguono l'andamento visto sulle lesioni (s1.1-vol, s1.2-vol)

##### Risultati

| Metodo | Miglior combo (silhouette) | Link |
| --- | --- | --- |
| Agglomerative | `k=3, average/ward/complete, euclidean` (~0.481) | [tuning/agglomerative/](../../../results/sdc/clustering/tuning/agglomerative/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| GMM | `n_components=4, full` (0.496) | [tuning/gmm/](../../../results/sdc/clustering/tuning/gmm/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| KMeans | `k=4` (0.497) | [tuning/kmeans/](../../../results/sdc/clustering/tuning/kmeans/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| HDBSCAN | `mcs=20, ms=10` (0.475, rumore 0.08) *[1]* | [tuning/hdbscan/](../../../results/sdc/clustering/tuning/hdbscan/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| Spectral | `n_clusters=8, rbf, gamma=1.0` (0.502) | [tuning/spectral/](../../../results/sdc/clustering/tuning/spectral/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |

*[1] Filtrato per `noise_fraction ≤ 0.1`, per escludere la soluzione degenere a 0.608 con ~25% di rumore.*

- Silhouette 0.45-0.50 per k=3-6 in quasi tutti gli algoritmi.
- Lateralizzazione sistematica come sulle lesioni: cluster puri per emisfero (oltre 200 soggetti tutti `left` o tutti `right`) più pochi cluster misti. In Spectral e HDBSCAN i misti concentrano più soggetti.
- La struttura SDC, derivata dalla maschera, ne eredita la lateralizzazione: nessun algoritmo standard la supera.

##### Decisioni
- Estendere l'analisi a `nc3` per vedere se più dimensioni la mitigano, poi uniformare la configurazione di produzione.
