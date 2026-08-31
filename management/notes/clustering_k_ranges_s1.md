# Range k/parametri per metodo × embedding — appunto molto approssimativo

> Nota scratch, non un'analisi definitiva: range di valori "competitivi" (vicini al massimo Silhouette,
> letti a occhio dai `tuning_results.csv`, nessuna soglia formale) per ciascun metodo, sui 3 embedding
> UMAP euclidean di produzione (`n2`/`n3`/`n10`, run `27-08_s1.1`, coorte lesion s1.1 - 1150 soggetti).
> Non un confronto/interpretazione — solo i numeri grezzi, da riprendere quando si arriva alla decisione
> di produzione. Fonte: `results/lesion/clustering/tuning/<metodo>/umap/27-08_s1.1_euclidean_n{2,3,10}/tuning_results.csv`.

## Agglomerative (euclidean, `linkage`≠single)

| Embedding | Range k competitivo | Silhouette |
|---|---|---|
| n2 | 4, 5, 6 | 0.49–0.50 |
| n3 | 3 (isolato) — poi 5, 8 | 0.48 / 0.467–0.469 |
| n10 | 4 (isolato) — poi 5 | 0.444–0.446 / 0.418–0.425 |

## GMM (qualsiasi `covariance_type`)

| Embedding | Range n_components competitivo | Silhouette |
|---|---|---|
| n2 | 4, 5 | 0.485–0.496 |
| n3 | bimodale: 8 **oppure** 3 | 0.488–0.491 / 0.483–0.485 |
| n10 | 5, 6 | 0.429–0.448 |

## KMeans

| Embedding | Range k competitivo | Silhouette |
|---|---|---|
| n2 | 4, 5 | 0.496–0.497 |
| n3 | bimodale: 8 **oppure** 3 | 0.489 / 0.485 |
| n10 | 3, 5, 6 | 0.431–0.443 |

## HDBSCAN (solo `noise_fraction`≤0.1)

| Embedding | Range (min_cluster_size, min_samples) | Silhouette | Noise |
|---|---|---|---|
| n2 | (20,10), (15,5) | 0.44–0.47 | 8–9% |
| n3 | (50,5), (20,5) | 0.50–0.51 | 8–9% |
| n10 | nessuna combinazione qualifica | — | min raggiungibile 25% |

## Spectral

| Embedding | Range n_clusters competitivo | Affinity | Silhouette |
|---|---|---|---|
| n2 | 5, 6, 8 | rbf domina, nn competitivo a 5 | 0.487–0.502 |
| n3 | 3, 6, 8 | quasi tutto rbf | 0.480–0.490 |
| n10 | 4, 5, 6 | tutto rbf | 0.434–0.456 |
