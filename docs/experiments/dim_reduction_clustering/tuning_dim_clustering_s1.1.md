# Clustering Tuning Results s1.1

Tuning dei metodi di clustering (kmeans/agglomerative/gmm/dbscan/spectral) su vari embedding di dim reduction. Dati: matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`). Nessuna selezione automatica — valori scelti a mano dopo aver letto `tuning_results.csv`/i grafici. **Tutti i valori numerici completi restano nei CSV** (`results/lesion/dim_reduction_clustering/<riduzione>/<metodo>/tuning/*/tuning_results.csv` + plot nella stessa cartella) — qui solo il verdetto per ciascuna combinazione, non le tabelle intere.

## 26-07-2026 — griglia base (umap/pacmap/tsne/pca, un solo parametro per metodo)

| Riduzione | kmeans | agglomerative | gmm | dbscan | spectral |
|---|---|---|---|---|---|
| **umap** (n_neighbors=5, euclidean) | k=4 (confermato) | k=5 | n=4 (confermato) | ❌ nessuno affidabile (silhouette ~0 su tutto il range) | n=8 (confermato anche su griglia estesa a 15 — l'eigengap suggeriva n≈11 ma non regge sui dati) |
| **pacmap** (n_neighbors=5) | k=6 (o k=2 per split macro) | k=5 (metriche) / k=2 (dendrogramma) | n=6 (o n=2) | trade-off: eps=0.3 qualità (36% noise) vs eps=0.5 copertura (8% noise, qualità inferiore) | escluso di proposito (fonde i satelliti) |
| **tsne** (perplexity=30) | k=5 | k=2 | n=2 | ⚠️ eps=0.5 default è un **artefatto** (98.9% noise, silhouette "0.988" calcolato su ~13 soggetti superstiti); eps=1.5 meno peggio (33% noise) | n=5 (confermato anche su griglia estesa a 15) |
| **pca** 150 comp. | k=2 (debole) | k=2 ⚠️ sbilanciato (563/1150 soggetti in un'unica foglia del dendrogramma) | n=4 | ❌ >90% noise ovunque | ❌ nessuna struttura reale |
| **pca** 2 comp. (test di controllo) | k=3 ⚠️ confonde col volume | k=3 stesso confondimento | n=2 debole | eps=2.0 stesso confondimento | n=3 stesso confondimento |

**PCA scartato come riduzione**: a 150 componenti soffre di curse of dimensionality (struttura sistematicamente debole/inutilizzabile); a 2 componenti il segnale principale (silhouette più alto di tutto lo studio) si è rivelato ridondante col volume lesionale, non con la topografia — `PC2` correla r=0.92 (Pearson) col volume lesionale per soggetto, verificato direttamente sui cluster (kmeans k=3: il gruppo "lesioni piccole" separato quasi solo per dimensione). umap/pacmap/tsne restano tutte valide.

## 29-07-2026 — metric × regress_out_volume (umap/tsne), griglia a 1 parametro per metodo

Sostituisce il round precedente: stesso confronto (`metric` × `regress_out_volume`), ma tuning_grid tornata a **un solo parametro sweeppato per metodo** (agglomerative/gmm/dbscan/spectral avevano temporaneamente sweeppato anche `linkage`/`covariance_type`/`min_samples`/`n_neighbors` — tolto, vedi note metodologiche). Parametro secondario tenuto fisso al default di `params_clustering.json`: `linkage=ward`, `covariance_type` non specificato (default sklearn `full`), `min_samples=5`, `n_neighbors=50`. Sessione unica, tutte le run tag `29-07`. `regress_out_volume=true` non è applicabile con `metric=jaccard`/`dice` (incompatibilità esplicita, `src/analysis/covariates.py`) — nessuna riga per quella combinazione.

**Dim tuning** (embedding, trustworthiness — invariato rispetto a prima, incluso per riferimento):

| Riduzione | euclidean | jaccard | dice |
|---|---|---|---|
| umap (n_neighbors 5→100) | 0.740 → 0.718 | 0.943 → 0.931 (best 0.945 @ 15) | 0.942 → 0.929 (best 0.945 @ 15) |
| tsne (perplexity 5→75) | 0.748 → 0.760 | 0.947 → 0.943 (best 0.952 @ 15) | 0.947 → 0.950 (best 0.954 @ 15) |

**Clustering tuning — UMAP**:

| Variante | kmeans | agglomerative (ward) | gmm (full) | dbscan (min_samples=5) | spectral (nn=50) |
|---|---|---|---|---|---|
| euclidean, vol=ON | k=3 (0.472) | k=2 (0.435) | n=3 (0.471) | ❌ nessuna combinazione con ≥2 cluster non-noise (tutto NaN) | k=4 (0.457) |
| euclidean, vol=OFF | k=4 (0.462) | k=2 (0.434) | n=3 (0.452) | eps=0.3 (0.093, noise 0.2%) | k=5 (0.458) |
| jaccard | k=2 (0.756) | k=2 (0.756) | n=2 (0.756) | eps≥0.7 (0.677, noise ~0%) | k=2 (0.756) |

**Clustering tuning — t-SNE** (perplexity=30 fissa):

| Variante | kmeans | agglomerative (ward) | gmm (full) | dbscan (min_samples=5) | spectral (nn=50) |
|---|---|---|---|---|---|
| euclidean, vol=ON | k=2 (0.420) | k=2 (0.423) | n=2 (0.427) | ⚠️ eps=0.5 (0.984, noise 98.9%) | k=2 (0.419) |
| euclidean, vol=OFF | k=2 (0.411) | k=2 (0.398) | n=2 (0.416) | ⚠️ eps=0.5 (0.988, noise 98.9%) | k=2 (0.413) |
| jaccard | k=2 (0.606) | k=2 (0.602) | n=2 (0.604) | ⚠️ eps=1.0 (0.941, noise 96.7%) | k=2 (0.602) |

**Letture numeriche**:
- `regress_out_volume` ON vs OFF (euclidean, unico confronto possibile): Δsilhouette ≤0.02 su entrambe le riduzioni — effetto trascurabile sulla qualità del clustering, confermato anche con la griglia a 1 parametro.
- euclidean → jaccard: +0.28 su umap (0.47→0.756), +0.19 su tsne (0.42→0.606) — salto molto più marcato su umap.
- umap-jaccard: tutti e 5 i metodi convergono su k=2, silhouette identico (0.756) — incluso dbscan a eps≥0.7 con noise~0%, non un artefatto come altrove.
- dbscan resta inaffidabile ovunque tranne che su umap-jaccard: noise_fraction ≥90% su tutte le altre 5 combinazioni; su umap-euclidean/vol=ON, con `min_samples` fissato a 5 (non più sweeppato), **nessun `eps` produce un risultato valido** (era 0.199 quando `min_samples=10` era esplorabile) — differenza diretta dell'aver tolto il secondo parametro dalla griglia.
- agglomerative: con `linkage` fissato a `ward` (non più sweeppato), il valore ottimale scende da k=3 a k=2 sulle varianti euclidean di umap (`linkage=average` trovava k=3 quando era esplorabile) — stesso effetto collaterale del punto sopra, non un cambiamento nei dati.

Le scelte operative conseguenti (quali valori usare per una run di produzione) sono tracciate separatamente in [`runs_history_dim_clustering_s1.1.md`](runs_history_dim_clustering_s1.1.md).

**Da fare per chiudere questa sezione**: quanto sopra è solo l'estratto numerico di `tuning_results.csv` — non ancora incrociato con i grafici corrispondenti (`tuning_plot.png` per metodo/variante, `eigengap_plot.png`/`k_distance_plot.png`/`dendrogram.png` per gli standalone). In particolare va ancora guardato a occhio: la curva silhouette 2→10 di ciascuna variante (non solo l'argmax riportato qui), l'eigengap di spectral su umap-jaccard (l'euristica automatica indica un gap a n=20, ma i primi 3 autovalori sono già vicini a zero - da leggere a mano), e il k-distance plot di dbscan dove "ALL NaN"/noise alto rende il numero da solo poco informativo.

---

### Note metodologiche

- Tutti gli indici sono calcolati con `src/analysis/clustering_tuning.py::compute_clustering_metrics`; per DBSCAN i punti di rumore (`label -1`) sono esclusi da silhouette/CH/DB, `noise_fraction` è sempre riportato a parte.
- Dendrogrammi/eigengap/k-distance sono diagnostiche **standalone**, calcolate una sola volta dai `base_params` — non dipendono dal valore di k/eps scelto nella sweep.
- Il secondo parametro sweeppato per `agglomerative`/`gmm`/`dbscan`/`spectral` (`linkage`/`covariance_type`/`min_samples`/`n_neighbors`), introdotto il 28-07-2026, è stato tolto il 29-07-2026 su richiesta esplicita — `tuning_plot.png` per questi metodi è tornato a essere una curva singola (`plot_clustering_tuning_metrics`), non più una heatmap (`plot_clustering_tuning_heatmaps`, rimasta nel codice ma non più richiamata da questi metodi con la config attuale).
- Nessun valore riportato qui è stato applicato in produzione — i risultati di produzione su disco usano ancora i default del registry salvo dove esplicitamente annotato.
- Griglia `spectral` (`config/registry/params_clustering.json`) estesa da `[2,3,4,5,6,8,10]` a `[...,11,12,13,14,15]` per verificare l'indicazione dell'eigengap su umap/tsne — resta così nel registry, non impatta la produzione (usata solo in `fine_tuning: true`).
