# Metodi di clustering della pipeline

Una nota per ogni metodo registrato in `CLUSTERING_METHODS` (`src/analysis/clustering.py`), con i parametri di `config/registry/params_clustering.json`. Ogni nota ha le stesse sezioni: cosa fa, perché (formule), il nostro contesto, parametri e default, tuning, valutazione, quando usarlo, pro e contro, un esempio, insidie, fonti.

Come si lancia la pipeline: `docs/guides/clustering.md`. Come leggere i grafici di una sweep: `../clustering_tuning_guide.md`. Rassegna della letteratura: `../clustering_literature_survey.md`. Il problema di clusterizzare sopra un embedding: `../challenge_of_clustering_after_dim_reduction.md`.

## Le note

| Nota | Metodi (`CLUSTERING_METHODS`) | Famiglia | Numero di cluster |
|---|---|---|---|
| [`kmeans.md`](kmeans.md) | `kmeans` | partizionale | fissato (`n_clusters`) |
| [`gmm.md`](gmm.md) | `gmm` | a modello (mistura di Gaussiane) | fissato (`n_components`), scelto con BIC/AIC |
| [`spectral.md`](spectral.md) | `spectral` | a grafo | fissato (`n_clusters`), eigengap come guida |
| [`agglomerative.md`](agglomerative.md) | `agglomerative` | gerarchico | fissato (`n_clusters`, taglio dell'albero) |
| [`hdbscan.md`](hdbscan.md) | `hdbscan`, `hdbscan_soft` | a densità | emerge dai dati, con rumore (`-1`) |
| [`adp.md`](adp.md) | `adp` | a densità (picchi) | emerge dai dati, governato da `Z` |
| [`evaluation_metrics.md`](evaluation_metrics.md) | tutti | metriche condivise | silhouette, Calinski-Harabasz, Davies-Bouldin, ARI/NMI, stabilità |

Le metriche specifiche di un metodo stanno nella sua nota: inertia e gap statistic in `kmeans.md`, BIC/AIC/ICL in `gmm.md`, eigengap in `spectral.md`, RSC, Monti e PAC in `evaluation_metrics.md`.

## Quando usare cosa

| Situazione | Metodo indicato | Perché | Da evitare |
|---|---|---|---|
| Serve una baseline veloce | `kmeans` | il più semplice ed economico [1] | - |
| Gruppi attesi compatti, convessi, di dimensione simile | `kmeans`, `agglomerative` con `ward` | stesso obiettivo (varianza entro i cluster) [1, 2] | `spectral` se non serve la connettività |
| Gruppi ellissoidali di forma e orientamento diversi | `gmm` (`full` o `diag`) | la covarianza per componente descrive la forma [3] | `kmeans` |
| Serve una probabilità di appartenenza | `gmm`, `hdbscan_soft` | soft clustering [3, 5] | - |
| Gruppi connessi ma non convessi, ben separati | `spectral` | connettività nel grafo [4] | `kmeans`, `gmm` |
| Interessa come i gruppi si dividono a più scale | `agglomerative` | l'albero contiene tutte le partizioni annidate [2] | - |
| Distanza non euclidea sull'embedding | `agglomerative` con `average`/`complete` | accetta altre metriche [2] | `kmeans`, `gmm`, `ward` |
| Numero di gruppi ignoto, densità diverse, soggetti atipici da lasciare fuori | `hdbscan`, `hdbscan_soft` | rumore esplicito, k dalla densità [5] | metodi che assegnano tutti |
| Clusterizzare la matrice **grezza** con distanze `dice`/`jaccard` | `adp` | clusterizza direttamente le distanze della matrice, con k dalla densità [7]; `agglomerative` accetta `dice`/`jaccard` come `metric`, ma con k fissato | metodi solo euclidei |
| Gruppi che si toccano o un continuo | nessun metodo discreto lo rivela; leggere con cautela tutti | [6]; `../clustering_literature_survey.md` §3 | - |

## Cose da sapere valide per tutti

- **Il tuning non sceglie per te**: ogni sweep produce indici e grafici, la scelta è umana (`../clustering_tuning_guide.md`).
- **Gli indici assoluti non si confrontano tra embedding diversi**: si confrontano le partizioni (ARI) e le dimensioni dei cluster ([`evaluation_metrics.md`](evaluation_metrics.md)).
- **Metodi stocastici e deterministici**: `kmeans` e `gmm` dipendono dal seme; `agglomerative`, `hdbscan`, `adp` sono deterministici; `spectral` con `cluster_qr` lo è in pratica ([`spectral.md`](spectral.md), sezione 3).

## Fonti

1. Lloyd, S. P. (1982). *Least squares quantization in PCM.* IEEE Transactions on Information Theory, 28(2), 129-137. doi:10.1109/TIT.1982.1056489. Dettagli e altre fonti: [`kmeans.md`](kmeans.md).
2. Fonti di [`agglomerative.md`](agglomerative.md) (scikit-learn, `AgglomerativeClustering`: https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.AgglomerativeClustering.html).
3. Fraley, C., Raftery, A. E. (2002). *Model-based clustering, discriminant analysis, and density estimation.* Journal of the American Statistical Association, 97(458), 611-631. doi:10.1198/016214502760047131. Dettagli: [`gmm.md`](gmm.md).
4. von Luxburg, U. (2007). *A tutorial on spectral clustering.* Statistics and Computing, 17(4), 395-416. doi:10.1007/s11222-007-9033-z. Dettagli: [`spectral.md`](spectral.md).
5. Fonti di [`hdbscan.md`](hdbscan.md) (scikit-learn, `HDBSCAN`: https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.HDBSCAN.html).
6. Fred, A. L. N., Jain, A. K. (2002). *Data clustering using evidence accumulation.* ICPR 2002, vol. 4, 276-280. doi:10.1109/ICPR.2002.1047450. Copia locale: `knowledge/papers/methods/Fred et al - 2002 - Data clustering using evidence accumulation/`.
7. d'Errico, M., Facco, E., Laio, A., Rodriguez, A. (2021). *Automatic topography of high-dimensional data sets by non-parametric density peak clustering.* Information Sciences, 560, 476-492. doi:10.1016/j.ins.2021.01.010. Dettagli: [`adp.md`](adp.md).
