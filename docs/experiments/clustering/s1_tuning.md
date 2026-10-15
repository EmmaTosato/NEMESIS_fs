# Diario Esperimenti

**Pipeline:** Clustering (Tuning)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 12-10-2026 — s1.4-vol

### Tuning agglomerative, HDBSCAN e ADP su UMAP dice / euclidean (nc2, nc10)

##### Input
- s1.4-vol
- Embedding: UMAP `08-10_s1.4-vol_m_{dice,euclidean}_nc{2,10}` (nc3 solo nel confronto tra embedding)
- ADP: matrice grezza `data/derived/lesion_matrix/07-10_s1.4-vol`
- 5845 soggetti
##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Leggere i tuning di ogni embedding con silhouette, Davies-Bouldin e Calinski-Harabasz, per decidere quali partizioni produrre

##### Risultati

| Run | Agglomerative | HDBSCAN | ADP dice | Link |
| --- | --- | --- | --- | --- |
| dice nc2 | **k=3**: silhouette 0.719, DB 0.367, uguali nei tre linkage | 8 cluster, rumore < 1% | silhouette ≤ 0.034 | [report](../../../results/reports/cluster_tuning_notebooks/cluster_lesion_dice_nc2/report.md) |
| dice nc10 | **k=2-3**: silhouette 0.71 a k=2, DB minimo 0.37 a k=3 | 8 cluster, rumore < 1% | silhouette ≤ 0.034 | [report](../../../results/reports/cluster_tuning_notebooks/cluster_lesion_dice_nc10/report.md) |
| euclidean nc2 | nessun taglio (silhouette 0.32-0.43) | nessuna riga utilizzabile | silhouette ≤ 0.034 | [report](../../../results/reports/cluster_tuning_notebooks/cluster_lesion_euclidean_nc2/report.md) |
| euclidean nc10 | nessun taglio (silhouette 0.33-0.43) | nessuna riga utilizzabile | silhouette ≤ 0.034 | [report](../../../results/reports/cluster_tuning_notebooks/cluster_lesion_euclidean_nc10/report.md) |

- Solo `dice` ha una struttura netta. Con `euclidean` nessun k si stacca.
- Le silhouette HDBSCAN più alte scartano il 14-24% dei soggetti come rumore: non sono candidati.
- ADP `euclidean` è degenere (silhouette negativa, un cluster al 93-99%).
- Accordo tra embedding (ward k=3, ARI nc2-nc3 / nc2-nc10 / nc3-nc10): `dice` 0.80 / 0.82 / 0.97; `euclidean` 0.76 / 0.58 / 0.78.
- Dendrogrammi e viste 2D confermano le tabelle: con `dice` l'embedding ha tre parti separate a occhio e ward k=3 taglia lì; con `euclidean` è una nuvola unica e i cluster sono fette. Su `dice` nc2, HDBSCAN (100/20) è esattamente ward k=3 col terzo gruppo diviso in sei.
- Sintesi tra le run: [SUMMARY](../../../results/reports/cluster_tuning_notebooks/SUMMARY.md)

##### Decisioni
- Nessun k unico: vedi [`s1_production.md`](s1_production.md), 12-10-2026

---

## 03-09-2026 — s1.2-vol (agglomerative su matrice raw)

### Clustering diretto sui voxel, senza dimensionality reduction

##### Input
- s1.2-vol
- Matrice raw: `data/derived/lesion_matrix/25-08_s1.2-vol`, 5269 × 264274 voxel
- Nessun embedding (`reduced_data: false`, `reduction_method: "raw"`)
##### Metodi
agglomerative

##### Obiettivo
- Verificare se la struttura topografica emerge dai voxel nativi, senza UMAP
- Confrontare `dice` ed `euclidean` sullo stesso dato

##### Risultati

20 combinazioni: `n_clusters`∈{2..6} × `linkage`∈{average,complete} × `metric`∈{euclidean,dice} — [tuning/agglomerative/raw/](../../../results/lesion/clustering/tuning/agglomerative/raw/03-09_s1.2-vol/)

| metrica | linkage | silhouette (k=2→6) | partizione a k=6 |
| --- | --- | --- | --- |
| euclidean | average | 0.734 → 0.706 | `[5257, 5, 2, 2, 2, 1]` |
| euclidean | complete | 0.474 → 0.465 | `[4790, 330, 119, 19, 6, 5]` |
| dice | average | ~0.011 (costante) | `[5264, 1, 1, 1, 1, 1]` |
| dice | complete | 0.006 → −0.028 | `[5118, 75, 23, 22, 19, 12]` |

- Tutte le 20 combinazioni sono degeneri: il cluster maggiore ha il 90.9-100% dei soggetti.
- La silhouette più alta (0.734) è la partizione `[5262, 7]`: 7 outlier, non struttura.
- `euclidean` misura il volume: `corr(distanza euclidea, somma dei volumi) = 0.942`.
- `dice` non ha gradiente globale: l'86.1% delle coppie di soggetti è a distanza 1.0.
- Su UMAP 2D (stesso k=6) le partizioni sono bilanciate (cluster maggiore 19.8-46.8%): UMAP ricostruisce per transitività una geometria globale che nel dato raw non esiste.

##### Decisioni
- Nessun candidato di produzione.
- Il percorso `reduced_data: false` è chiuso per agglomerative sui voxel lesionali a questa scala.
- Il limite vale per le metriche globali su binario raw (`dice`, `jaccard`, `euclidean`). I metodi a densità locale (HDBSCAN) non sono coperti.

---

## 03-09-2026 — s1.2-vol (re-tuning HDBSCAN)

### `n_clusters_found` aggiunto e `min_cluster_size` alzato

##### Input
- Embedding: UMAP `28-08_s1.2-vol_m_euclidean_nc2`
- 5269 soggetti
##### Metodi
hdbscan

##### Obiettivo
- Il tuning non calcolava il numero di cluster: `mcs=5, ms=10` dava 143 cluster in produzione, invisibili qui
- Aggiungere `n_clusters_found` e portare `min_cluster_size` da {5..50} a {10,20,30,50,75,100}

##### Risultati

Griglia 6 × 3 — [tuning_results.csv](../../../results/lesion/clustering/tuning/hdbscan/umap/03-09_s1.2-vol_m_euclidean_nc2/tuning_results.csv)

| `min_cluster_size` / `min_samples` | Cluster | Silhouette | Rumore |
| --- | --- | --- | --- |
| 10 / 10 | 121 | 0.612 | 0.308 |
| 100 / 20 | 15 | **0.464** | 0.245 |
| 75 / 20 | 19 | 0.449 | 0.231 |
| 50 / 20 | 25 | 0.417 | 0.195 |

- Anche `mcs=10` con `min_samples` 5-10 dà 121-149 cluster: serve `mcs` ≥ 50 per scendere sotto i ~30.

##### Decisioni
- `100/20` (15 cluster) e `75/20` (19 cluster) sostituiscono i due candidati precedenti: [`s1_production.md`](s1_production.md), 03-09-2026

---

## 01-09-2026 — s1.2-vol

### Tuning su coorte estesa (n=5269), 5 metodi

##### Input
- s1.2-vol
- Embedding: UMAP `euclidean`, n_components=2, `28-08_s1.2-vol_m_euclidean_nc2`
- Dati raw: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Ripetere il tuning di s1.1-vol sulla coorte estesa, per verificare se i candidati reggono

##### Risultati

| Metodo | Griglia | Miglior combo (silhouette) | Link |
| --- | --- | --- | --- |
| KMeans | `n_clusters`∈{2,3,4,5,6,8,10} | `k=5` (0.443) | [tuning/kmeans/](../../../results/lesion/clustering/tuning/kmeans/umap/01-09_s1.2-vol_m_euclidean_nc2/) |
| Agglomerative | `n_clusters`×`linkage`×`metric` (70/84, 14 saltate: `ward`+metrica non euclidea) | `k=2, average, cosine` (0.761) | [tuning/agglomerative/](../../../results/lesion/clustering/tuning/agglomerative/umap/01-09_s1.2-vol_m_euclidean_nc2/) |
| GMM | `n_components`×`covariance_type` | `n_components=5, full` (0.447) | [tuning/gmm/](../../../results/lesion/clustering/tuning/gmm/umap/01-09_s1.2-vol_m_euclidean_nc2/) |
| HDBSCAN | `min_cluster_size`×`min_samples` | `mcs=5, ms=10` (0.613, rumore 0.32) | [tuning/hdbscan/](../../../results/lesion/clustering/tuning/hdbscan/umap/01-09_s1.2-vol_m_euclidean_nc2/) |
| Spectral | `n_clusters`×`affinity` | `rbf, k=5, gamma=1.0` (0.426) | [tuning/spectral/](../../../results/lesion/clustering/tuning/spectral/umap/01-09_s1.2-vol_m_euclidean_nc2/) |

- `k=2` di agglomerative è lo stesso artefatto `lesion_side` di s1.1-vol.
- HDBSCAN: la silhouette migliore scarta un terzo dei soggetti; con rumore 0.14 (`mcs=30, ms=5`) scende a 0.34.

##### Decisioni
- Vedi [`s1_production.md`](s1_production.md), 03-09-2026

---

## 31-08-2026 — s1.1-vol

### Tuning su coorte originale, 5 metodi

##### Input
- s1.1-vol
- Embedding: UMAP `{dice,euclidean}` × `n_components`∈{2,3,10} (6 combinazioni, `11-08_s1.1-vol_*` e `13-08_s1.1-vol_*`)
- Dati raw: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Verificare se un `k` di produzione emerge in modo robusto e se è indipendente da `lesion_side`, `dataset`, volume

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| Agglomerative | 6×70 | `n_clusters`∈{2,3,4,5,6,8,10} × `linkage`∈{ward,average,complete,single} × `metric`∈{euclidean,cosine,manhattan} | [tuning/agglomerative/](../../../results/lesion/clustering/tuning/agglomerative/) |
| GMM | 6×28 | `n_components`∈{2,3,4,5,6,8,10} × `covariance_type`∈{full,tied,diag,spherical} | [tuning/gmm/](../../../results/lesion/clustering/tuning/gmm/) |
| KMeans | 6×7 | `n_clusters`∈{2,3,4,5,6,8,10} | [tuning/kmeans/](../../../results/lesion/clustering/tuning/kmeans/) |
| HDBSCAN | 6×18 | `min_cluster_size`∈{5,10,15,20,30,50} × `min_samples`∈{5,10,20} | [tuning/hdbscan/](../../../results/lesion/clustering/tuning/hdbscan/) |
| Spectral | 6×72 | `n_clusters`∈{2..15} × `affinity`∈{nearest_neighbors,rbf} | [tuning/spectral/](../../../results/lesion/clustering/tuning/spectral/) |

- **Agglomerative:** k=2 è l'artefatto `lesion_side` su tutti i 6 embedding; `single` scartato (chaining). Il k migliore oltre 2 non converge tra `n_components`:

| `n_components` | k migliore | Silhouette (average / ward) |
| --- | --- | --- |
| 2 | 5 | 0.497 / 0.485 |
| 3 | 3 | 0.481 / 0.482 |
| 10 | 4 | 0.444 / 0.444 |

- **GMM:** `kmeans` batte `random` in BIC; BIC/AIC senza gomito; `full` a `n_components`=10 è degenere (DB ~1.7). Migliore: `full, n_components=4` (0.496, DB 0.693).
- **KMeans:** silhouette e Davies-Bouldin concordano a k=4 (0.497 / 0.693).
- **HDBSCAN:** la silhouette più alta (`mcs=5, ms=5`, 0.609) ha rumore 0.245. Con rumore ≤ 0.1 restano 2 combinazioni; la migliore è `mcs=20, ms=10` (0.475, rumore 0.083).
- **Spectral:** `nearest_neighbors` con `n_neighbors=10` è instabile. Migliore: `rbf, k=8` (0.502). L'eigengap indica 10-14 cluster, la silhouette 4-8.
- In ogni k candidato: 1-2 cluster quasi puri per lato lesione e volume, più un cluster misto. `dataset` non è confondente.

##### Decisioni
- Vedi [`s1_production.md`](s1_production.md), 01-09-2026
