# Runs History S1.1

## 26-06-2026 Run

- **Data Run Produzione:** 26 Luglio 2026
- **Pipeline:** `dim_reduction_clustering`
- **Dati in ingresso:** Matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)
- **Riduzioni in Produzione:** UMAP, PACMAP, t-SNE
- **Riduzioni Scartate:** PCA (150 e 2 componenti) — 150D inutilizzabile per curse of dimensionality, 2D confuso in modo quasi perfetto (r=0.92) col volume lesionale anziché con la topografia.
- **Configurazioni Scelte (Clustering):**
  - **UMAP:** K-Means (k=4), Agglomerative (k=5), GMM (n=4), Spectral (n=8)
  - **PACMAP:** K-Means (k=6), Agglomerative (k=2), GMM (n=6). *Spectral escluso di proposito (fonde i satelliti).*
  - **t-SNE:**
    - K-Means (k=5), Agglomerative (k=2), GMM (n=2), Spectral (n=5)
    - t-sne seguie i parametri fissati da Thiebaut de Schotten et al. 2020
- **Casi Aperti (DBSCAN):** Escluso dalla produzione su tutte le riduzioni. Su umap/tsne/pca produce rumore totale o nessuna struttura; su pacmap ha un trade-off irrisolto tra qualità e copertura della coorte (eps=0.3 vs 0.5/0.7). Da analizzare in sessione dedicata prima dell'uso.
- **Motivazione / Decisione:** Valori determinati dall'analisi quantitativa e visiva documentata in [`tuning_dim_clustering_s1.1.md`](tuning_dim_clustering_s1.1.md) (tuning dei metodi di riduzione dimensionale: [`tuning_dim_s1.1.md`](tuning_dim_s1.1.md)).
- **Riferimento Log (CSV):** `results/lesion/dim_reduction_clustering/<riduzione>/runs.csv`
- **Output:** I risultati di questa sessione sono stati scritti in directory del tipo `26-07_s1.1_*` sotto ogni metodo.
