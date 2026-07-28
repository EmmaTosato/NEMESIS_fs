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

## 28/29-07-2026 — metric × regress_out_volume (umap/tsne), rilancio dopo pulizia dei tuning precedenti

Sostituisce il round precedente (stessa griglia base, tuning cancellato e rilanciato con `regress_out_volume` come terza dimensione di confronto). Sessione unica a cavallo di mezzanotte: UMAP taggato `28-07`, t-SNE `29-07`, stessi dati/config altrimenti. `regress_out_volume=true` non è applicabile con `metric=jaccard`/`dice` (incompatibilità esplicita, `src/analysis/covariates.py`) — nessuna riga per quella combinazione.

**Dim tuning** (embedding, trustworthiness — invariato rispetto a prima, incluso per riferimento):

| Riduzione | euclidean | jaccard | dice |
|---|---|---|---|
| umap (n_neighbors 5→100) | 0.740 → 0.718 | 0.943 → 0.931 (best 0.945 @ 15) | 0.942 → 0.929 (best 0.945 @ 15) |
| tsne (perplexity 5→75) | 0.748 → 0.760 | 0.947 → 0.943 (best 0.952 @ 15) | 0.947 → 0.950 (best 0.954 @ 15) |

**Clustering tuning — UMAP**:

| Variante | kmeans | agglomerative | gmm | dbscan | spectral |
|---|---|---|---|---|---|
| euclidean, vol=ON | k=3 (0.472) | k=3, average (0.466) | n=3, spherical (0.475) | eps=0.3, min_samples=10 (0.199, noise 3.5%) | k=3, nn=100 (0.474) |
| euclidean, vol=OFF | k=4 (0.462) | k=3, average (0.443) | n=4, spherical (0.464) | eps=0.3, min_samples=3 (0.255, noise 0.1%) | k=5, nn=100 (0.464) |
| jaccard | k=2 (0.756) | k=2, ward (0.756) | n=2, full (0.756) | eps≥0.7 (0.677, noise ~0%) | k=2, nn=30 (0.756) |

**Clustering tuning — t-SNE** (perplexity=30 fissa):

| Variante | kmeans | agglomerative | gmm | dbscan | spectral |
|---|---|---|---|---|---|
| euclidean, vol=ON | k=2 (0.420) | k=2, average (0.423) | n=2, diag (0.428) | ⚠️ eps=0.5/min_samples=5 (0.984, noise 98.9%) | k=2, nn=10 (0.426) |
| euclidean, vol=OFF | k=2 (0.411) | k=2, complete (0.408) | n=2, diag (0.417) | ⚠️ eps=0.5/min_samples=5 (0.988, noise 98.9%) | k=2, nn=10 (0.415) |
| jaccard | k=2 (0.606) | k=2, complete (0.602) | n=2, tied (0.605) | ⚠️ eps=0.5/min_samples=3 (0.955, noise 98.3%) | k=2, nn=100 (0.605) |

**Letture numeriche**:
- `regress_out_volume` ON vs OFF (euclidean, unico confronto possibile): Δsilhouette ≤0.02 su entrambe le riduzioni — effetto trascurabile sulla qualità del clustering.
- euclidean → jaccard: +0.28 su umap (0.47→0.756), +0.19 su tsne (0.42→0.606) — salto molto più marcato su umap.
- umap-jaccard: le 5 combinazioni di metodo/parametro con silhouette più alta convergono **tutte** su k=2, silhouette identico (0.756) — incluso dbscan a eps≥0.7 con noise~0%, non un artefatto come altrove.
- dbscan resta inaffidabile ovunque tranne che su umap-jaccard: noise_fraction ≥90% su tutte le altre 5 combinazioni (euclidean umap escluso, dove noise è comunque basso ma silhouette bassa) — i valori di silhouette "alti" su tsne (0.955-0.988) sono calcolati su ~1-2% dei soggetti, non comparabili.

Le scelte operative conseguenti (quali valori usare per una run di produzione) sono tracciate separatamente in [`runs_history_dim_clustering_s1.1.md`](runs_history_dim_clustering_s1.1.md).

---

### Note metodologiche

- Tutti gli indici sono calcolati con `src/analysis/clustering_tuning.py::compute_clustering_metrics`; per DBSCAN i punti di rumore (`label -1`) sono esclusi da silhouette/CH/DB, `noise_fraction` è sempre riportato a parte.
- Dendrogrammi/eigengap/k-distance sono diagnostiche **standalone**, calcolate una sola volta dai `base_params` — non dipendono dal valore di k/eps scelto nella sweep.
- Dal 28-07-2026, `agglomerative`/`gmm`/`dbscan`/`spectral` sweepano un secondo parametro (`linkage`/`covariance_type`/`min_samples`/`n_neighbors`) accanto a quello principale — `tuning_plot.png` per questi metodi è quindi una heatmap (`plot_clustering_tuning_heatmaps`), non più una curva.
- Nessun valore riportato qui è stato applicato in produzione — i risultati di produzione su disco usano ancora i default del registry salvo dove esplicitamente annotato.
- Griglia `spectral` (`config/registry/params_clustering.json`) estesa da `[2,3,4,5,6,8,10]` a `[...,11,12,13,14,15]` per verificare l'indicazione dell'eigengap su umap/tsne — resta così nel registry, non impatta la produzione (usata solo in `fine_tuning: true`).
