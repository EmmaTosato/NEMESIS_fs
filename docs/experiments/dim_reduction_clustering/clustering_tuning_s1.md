# Log Esperimenti: Clustering — Tuning

**Pipeline:** `clustering`
**Dati:** Embedding UMAP di produzione, sessione lesion matrix s1.1 (1150 soggetti).

---

## 27/28-08-2026 — s1.1

#### Tuning agglomerative su 6 embedding UMAP (metric × n_components)

**Obiettivo:**

- Sweep `n_clusters` × `linkage` × `metric` per agglomerative su tutti e 6 gli embedding UMAP di produzione (`dice`/`euclidean` × `n_components`∈{2,3,10}).
- Verificare se un `k` di produzione emerge in modo robusto, e se è indipendente da confondenti noti (`lesion_side`, `dataset`, volume).
- GMM/KMeans analizzate (vedi sotto). HDBSCAN/Spectral: sweep lanciata (27-08) sugli stessi 6 embedding, non ancora analizzata in dettaglio.

**Strategie testate**

- modality: Lesion embedding (UMAP, post dim_reduction)
- datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR

| Metodo                         | Run   | Griglia                                                                                                                     | Link                                                                             |
| ------------------------------ | ----- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Agglomerative                  | 6×70 | `n_clusters`∈{2,3,4,5,6,8,10} × `linkage`∈{ward,average,complete,single} × `metric`∈{euclidean,cosine,manhattan} | [tuning/agglomerative/](../../../results/lesion/clustering/tuning/agglomerative/) |
| GMM                            | 6×28 | `n_components`∈{2,3,4,5,6,8,10} × `covariance_type`∈{full,tied,diag,spherical}                                          | [tuning/gmm/](../../../results/lesion/clustering/tuning/gmm/)                     |
| KMeans                         | 6×7  | `n_clusters`∈{2,3,4,5,6,8,10}                                                                                            | [tuning/kmeans/](../../../results/lesion/clustering/tuning/kmeans/)               |
| HDBSCAN, Spectral               | —    | vedi`tuning_grid` per metodo in `params_clustering.json`                                                                | [tuning/](../../../results/lesion/clustering/tuning/) — non ancora analizzato    |

**Risultati**

| Check                                                      | Esito                                                                                                   |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| k=2                                                        | Artefatto`lesion_side`, su tutti e 6 gli embedding                                                    |
| Interclass matrix (proxy`dataset`)                       | Piatta su`euclidean` — nessuna metrica separa i siti. Eccezione: PSP ~12% più compatto internamente |
| Dendrogramma (`euclidean_n2`)                            | `single` scartato (chaining); `ward`/`average` concordano solo al primo taglio (k=2)              |
| k migliore oltre k=2 (`ward`/`average`, `euclidean`) | **Non converge tra `n_components`** — vedi tabella sotto                                       |
| `dataset` nei k candidati                                | Non confondente, ben distribuito                                                                        |
| `average` vs `ward` a k=5 fisso (`n3`)               | ARI 0.68 / NMI 0.81 — accordo parziale, entrambi stabili (SSI 1.00 / 0.96)                             |

| `n_components` | k migliore | Silhouette (average / ward) |
| ---------------- | ---------- | --------------------------- |
| 2                | 5          | 0.497 / 0.485               |
| 3                | 3          | 0.481 / 0.482               |
| 10               | 4          | 0.444 / 0.444               |

Struttura ricorrente in ogni k candidato: 1-2 cluster quasi puri per lato lesione + volume, 1 cluster misto a basso volume.

**Risultati (GMM)**

| Check                                          | Esito                                                                                                                                             |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stabilità init (`kmeans` vs `random`)        | Entrambe piatte da subito (nessuna instabilità di seed) — ma `kmeans` domina sempre in BIC, gap crescente con `n_components`. `random` da scartare |
| BIC/AIC                                        | Monotoni decrescenti su tutta la griglia, nessun gomito — non informativi qui, ignorati come criterio                                              |
| Davies-Bouldin                                 | Buono ovunque tranne un outlier netto: `full`@`n_components`=10 (~1.7 vs ~0.7-0.9) — fit degenere nonostante il BIC più basso in assoluto        |
| Miglior candidato (Silhouette)                 | `full`, `n_components`=4 (silhouette 0.496, DB 0.693 — coerente, non l'anomalia di nc=10)                                                       |
| Crosstab (`full`, `n_components`=4) vs `lesion_side` | Stesso artefatto di agglomerative: 2 cluster puri per lato lesione (left/right) + 2 misti                                                       |

**Risultati (KMeans)**

| Check                                          | Esito                                                                                                                  |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Stabilità init (`k-means++` vs `random`)     | Entrambe convergono alla stessa inertia già a `n_init`≥5, a ogni `n_clusters` — nessun vincitore netto, nessuna instabilità |
| Silhouette / Davies-Bouldin                    | Concordano esattamente: picco Silhouette e minimo Davies-Bouldin entrambi a **k=4** (0.497 / 0.693)                    |
| Calinski-Harabasz / inertia                    | CH cresce quasi sempre con k (non decisivo, ma non contraddice k=4); inertia senza gomito netto, coerente con k=4-5    |
| Crosstab `lesion_side`, k=4 (miglior candidato) | Stesso artefatto: cluster puro left (215/0/49), cluster puro right (1/243/41), 2 cluster misti a maggioranza left      |
| Crosstab `lesion_side`, k=5                    | Stesso pattern, un cluster misto in più (3 quasi-puri per lato + 2 misti)                                              |

**Decisioni aperte:**

- `n_components` e k vanno decisi insieme — non convergono (tabella sopra). Assi possibili, nessuno ancora scelto: (A) convergenza cross-metodo a parità di `n_components`, (B) consenso/stabilità RSC/Monti su coorte reale (`management/notes/TODO.md`), (C) regressare `lesion_side`/volume pre-clustering, (D) criterio clinico.
- **Asse (A), 3 conferme indipendenti**: l'artefatto `lesion_side` si ripete identico in agglomerative, GMM e KMeans — è la struttura dei dati/embedding a portarlo, non un artefatto di un singolo algoritmo.
- Prossimo: stesso check crosstab su `diag`@4/`tied`@6 (GMM); poi stesso schema (diagnostica → tuning → crosstab) su HDBSCAN/Spectral.

**Strumenti:** [`clustering_tuning_explorer.ipynb`](../../../notebooks/post-results_analysis/clustering_tuning_explorer.ipynb) — esplorazione `tuning_results.csv` + diagnostiche, ARI/NMI tra combinazioni, Subsampling Stability Index.
