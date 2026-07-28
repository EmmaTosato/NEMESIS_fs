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

## 28-07-2026 — griglia estesa (umap aggiornato a jaccard, tsne invariato; +linkage/covariance_type/min_samples/n_neighbors)

Embedding aggiornati rispetto al round precedente: **umap** ora con `n_neighbors=15, metric=jaccard` (vedi [`tuning_dim_s1.1.md`](tuning_dim_s1.1.md)) al posto del vecchio `n_neighbors=5, euclidean`; **tsne** invariato (`perplexity=30` — il guadagno a 50 era marginale, non adottato).

| Riduzione | kmeans | agglomerative | gmm | dbscan | spectral |
|---|---|---|---|---|---|
| **umap** (jaccard) | k=2 (silhouette 0.756, nettamente più alto che con l'euclidean di prima) | k=2 con qualunque `linkage` (identico); ⚠️ `single` degrada da k=4 in su, arriva negativo a k=8 | n=2 con qualunque `covariance_type` (identico) | ⚠️ stesso artefatto di prima, ancora più marcato: eps 0.7-2.0 collassano tutti sullo stesso risultato (0.677, identico ad agglomerative k=3) | k=2 con `n_neighbors`≥30; ⚠️ `n_neighbors=10` è chiaramente troppo basso (silhouette negativo anche a k=2) — conferma che il default 50 è una buona scelta |
| **tsne** (perplexity=30) | k=2 (debole, 0.41 — separazione molto più bassa che su umap-jaccard) | k=2 con `linkage=complete` | n=2 con `covariance_type=diag` | ⚠️ stesso artefatto (eps=0.5 default: 98.9% noise, silhouette "ottimo" fittizio) | k=2, `n_neighbors` ha impatto minimo qui |

**Osservazione principale**: con l'embedding UMAP corretto (jaccard), la separazione a k=2 è nettamente più netta di tutto lo studio precedente (0.756 contro 0.37-0.5) — e quasi ogni metodo/parametro aggiuntivo converge sullo stesso k=2, segno di una struttura più semplice di quanto suggerisse l'embedding euclidean. Su tsne la separazione resta debole (~0.41), coerente col fatto che qui non c'è un'opzione di metrica binaria da sfruttare.

**dbscan**: confermato inaffidabile su entrambe le riduzioni (stessi artefatti di rumore) — resta fuori da qualunque scelta di produzione finché non si esplora una griglia `eps` dedicata più fine (proposta non ancora eseguita: `[0.3, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7]`, per risolvere la zona di transizione tra 0.5 e 0.7 dove oggi non abbiamo risoluzione).

Le scelte operative conseguenti (quali valori usare per una run di produzione) sono tracciate separatamente in [`runs_history_dim_clustering_s1.1.md`](runs_history_dim_clustering_s1.1.md).

---

### Note metodologiche

- Tutti gli indici sono calcolati con `src/analysis/clustering_tuning.py::compute_clustering_metrics`; per DBSCAN i punti di rumore (`label -1`) sono esclusi da silhouette/CH/DB, `noise_fraction` è sempre riportato a parte.
- Dendrogrammi/eigengap/k-distance sono diagnostiche **standalone**, calcolate una sola volta dai `base_params` — non dipendono dal valore di k/eps scelto nella sweep.
- Dal 28-07-2026, `agglomerative`/`gmm`/`dbscan`/`spectral` sweepano un secondo parametro (`linkage`/`covariance_type`/`min_samples`/`n_neighbors`) accanto a quello principale — `tuning_plot.png` per questi metodi è quindi una heatmap (`plot_clustering_tuning_heatmaps`), non più una curva.
- Nessun valore riportato qui è stato applicato in produzione — i risultati di produzione su disco usano ancora i default del registry salvo dove esplicitamente annotato.
- Griglia `spectral` (`config/registry/params_clustering.json`) estesa da `[2,3,4,5,6,8,10]` a `[...,11,12,13,14,15]` per verificare l'indicazione dell'eigengap su umap/tsne — resta così nel registry, non impatta la produzione (usata solo in `fine_tuning: true`).
