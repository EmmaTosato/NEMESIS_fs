# Log Esperimenti: Clustering — Tuning

**Pipeline:** `clustering`
**Dati:** Embedding UMAP di produzione, sessione lesion matrix s1.1 (1150 soggetti).

---

## 27/28-08-2026 — s1.1

*Plot rigenerati 31-08-2026 (stessi parametri/griglia/dati - solo naming/titoli/spaziatura dei plot aggiornati dopo l'audit naming clustering; nessuna nuova run scientifica, nessuna cifra sotto cambiata).*

#### Tuning agglomerative su 6 embedding UMAP (metric × n_components)

**Obiettivo:**

- Sweep `n_clusters` × `linkage` × `metric` per agglomerative su tutti e 6 gli embedding UMAP di produzione (`dice`/`euclidean` × `n_components`∈{2,3,10}).
- Verificare se un `k` di produzione emerge in modo robusto, e se è indipendente da confondenti noti (`lesion_side`, `dataset`, volume).
- Tutti e 5 i metodi (agglomerative, GMM, KMeans, HDBSCAN, Spectral) analizzati (vedi sotto).

**Strategie testate**

- modality: Lesion embedding (UMAP, post dim_reduction)
- datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR

| Metodo                         | Run   | Griglia                                                                                                                     | Link                                                                             |
| ------------------------------ | ----- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Agglomerative                  | 6×70 | `n_clusters`∈{2,3,4,5,6,8,10} × `linkage`∈{ward,average,complete,single} × `metric`∈{euclidean,cosine,manhattan} | [tuning/agglomerative/](../../../results/lesion/clustering/tuning/agglomerative/) |
| GMM                            | 6×28 | `n_components`∈{2,3,4,5,6,8,10} × `covariance_type`∈{full,tied,diag,spherical}                                          | [tuning/gmm/](../../../results/lesion/clustering/tuning/gmm/)                     |
| KMeans                         | 6×7  | `n_clusters`∈{2,3,4,5,6,8,10}                                                                                            | [tuning/kmeans/](../../../results/lesion/clustering/tuning/kmeans/)               |
| HDBSCAN                        | 6×18 | `min_cluster_size`∈{5,10,15,20,30,50} × `min_samples`∈{5,10,20}                                                       | [tuning/hdbscan/](../../../results/lesion/clustering/tuning/hdbscan/)             |
| Spectral                       | 6×72 | `n_clusters`∈{2..15} × `affinity`∈{nearest_neighbors,rbf} (`n_neighbors`∈{10,30,50} / `gamma`∈{0.1,1,5})           | [tuning/spectral/](../../../results/lesion/clustering/tuning/spectral/)           |

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

**Risultati (HDBSCAN)**

| Check                                          | Esito                                                                                                                        |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Silhouette/CH più alti (`min_cluster_size=5, min_samples=5`) | **Trappola**: silhouette=0.609, CH=4321 (outlier), ma `noise_fraction`=0.245 — il rumore più alto di tutta la sweep, scarta i soggetti difficili invece di separarli |
| Filtro `noise_fraction`≤0.1                    | Solo 2 combinazioni sopravvivono. Vero candidato: `min_cluster_size=20, min_samples=10` (silhouette 0.475, noise 0.083, il più basso della sweep) |
| Sopra `min_samples`, `min_cluster_size` extra non cambia nulla | Coppie con valori identici (es. `(30,20)`≡`(50,20)`, `(30,10)`≡`(50,10)`) — il vincolo attivo è `min_samples`                |
| Crosstab `lesion_side`, `(20,10)`              | 7 cluster su 8 quasi puri per lato; 1 misto (left=176/right=114/unknown=56) ma **è il cluster più grande** (346 soggetti) — a differenza degli altri metodi, dove il misto è il più piccolo |
| Rumore (`-1`)                                  | Composizione non stabile tra combinazioni: sbilanciato `right` a `(15,10)`, `left` a `(20,10)` — da non sovra-interpretare        |

**Risultati (Spectral)**

| Check                                                    | Esito                                                                                                                                        |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Silhouette per combinazione                              | `nearest_neighbors(n_neighbors=10)` instabile/erratico (silhouette giù fino a 0.10-0.15) — grafo da scartare. Le altre convergono in una fascia 0.40-0.50, picco a `n_clusters`=4-8 |
| Miglior candidato (Silhouette)                           | `rbf`, `n_clusters`=8 (0.502) — alternativa con DB migliore: `nearest_neighbors(n_neighbors=30)`, `n_clusters`=5 (silhouette 0.494, DB 0.628, il più basso della tabella) |
| Eigengap vs Silhouette                                   | **Disaccordo netto**: eigengap suggerisce `n_clusters`≈10-14 (10 per `n_neighbors`=30, 11 per 50, 14 per 10) contro il picco Silhouette 4-8 — nessuna regola meccanica per risolverlo |
| Crosstab (`n_clusters=6, nearest_neighbors, n_neighbors=50`) vs `lesion_side` | 5 cluster su 6 quasi puri per lato; 1 misto (392 soggetti) — di nuovo il cluster più grande, come HDBSCAN                                    |

**Decisioni aperte:**

- `n_components` e k vanno decisi insieme — non convergono (tabella sopra). Assi possibili, nessuno ancora scelto: (A) convergenza cross-metodo a parità di `n_components`, (B) consenso/stabilità RSC/Monti su coorte reale (`management/notes/TODO.md`), (C) regressare `lesion_side`/volume pre-clustering, (D) criterio clinico.
- **Asse (A) chiuso, 5/5 conferme**: l'artefatto `lesion_side` si ripete in tutti e 5 i metodi (agglomerative, GMM, KMeans, HDBSCAN, Spectral) — è la struttura dei dati/embedding a portarlo, non un artefatto di un singolo algoritmo. Nessun metodo dà un candidato "pulito" a k basso.
- **Esplorazione tuning completa per tutti e 5 i metodi.** Prossimo passo: non più un check per-metodo, ma decidere tra (B) consenso/stabilità su coorte reale, (C) regressione di `lesion_side`/volume pre-clustering, o (D) criterio clinico — per arrivare a una config di produzione che non sia solo il re-splitting del lato lesione.

**Strumenti:** [`clustering_tuning_explorer.ipynb`](../../../notebooks/post-results_analysis/clustering_tuning_explorer.ipynb) — esplorazione `tuning_results.csv` + diagnostiche, ARI/NMI tra combinazioni, Subsampling Stability Index.
