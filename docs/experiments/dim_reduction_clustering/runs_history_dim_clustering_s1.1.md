#  Dimensionality Reduction + Clustering S1.1
- **Pipeline:** `dim_reduction_clustering`
- **Dati in ingresso:** Matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)
- **Riferimento Log (CSV):** `results/lesion/dim_reduction_clustering/<riduzione>/runs.csv`
- **Parametri in input**: `config.md` in ogni risultato di output
- **Output:** I risultati di questa sessione sono stati scritti in directory del tipo `<data>_s1.1_*` sotto ogni metodo.


## 26-07-2026 Run
- **Data Run Produzione:** 26 Luglio 2026
- **Riduzioni in Produzione:** UMAP, PACMAP, t-SNE
- **Riduzioni Scartate:** PCA (150 e 2 componenti) — 150D inutilizzabile per curse of dimensionality, 2D confuso in modo quasi perfetto (r=0.92) col volume lesionale anziché con la topografia.
- **Clustering in produzione**
	- **UMAP:** K-Means (k=4), Agglomerative (k=5), GMM (n=4), Spectral (n=8)
	- **PACMAP:** K-Means (k=6), Agglomerative (k=2), GMM (n=6). *Spectral escluso di proposito (fonde i satelliti).*
	  - **t-SNE:**
	    - K-Means (k=5), Agglomerative (k=2), GMM (n=2), Spectral (n=5)
	    - t-sne seguie i parametri fissati da Thiebaut de Schotten et al. 2020
- **Casi Aperti (DBSCAN):** Escluso dalla produzione su tutte le riduzioni. Su umap/tsne/pca produce rumore totale o nessuna struttura; su pacmap c'è un trade-off irrisolto tra qualità e copertura della coorte (eps=0.3 vs 0.5/0.7). Da analizzare in sessione dedicata prima dell'uso.
- **Motivazione / Decisione:** Tuning parziale


## 03-08-2026 Run
