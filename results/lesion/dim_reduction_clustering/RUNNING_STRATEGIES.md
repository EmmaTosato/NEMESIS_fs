# Running strategies — Dimensionality reduction and clustering (Session 1.1)

Decisioni operative dall'analisi in [`TUNING_ANALYSIS.md`](TUNING_ANALYSIS.md), per l'input `data/derived/lesion_matrix/21-07_s1.1` (matrice voxel-wise, 1150 soggetti, session `s1.1`).

## Riduzioni

| Riduzione | Stato |
|---|---|
| umap | ✅ in produzione |
| pacmap | ✅ in produzione |
| tsne | ✅ in produzione |
| pca (150 e 2 componenti) | ❌ scartato — 150D debole/inutilizzabile (curse of dimensionality), 2D confuso col volume lesionale (r=0.92 con PC2), non con la topografia |

## Clustering di produzione (dbscan escluso ovunque, vedi sotto)

| Riduzione | kmeans | agglomerative | gmm | spectral |
|---|---|---|---|---|
| umap | k=4 | k=5 | n=4 | n=8 |
| pacmap | k=6 | k=2 | n=6 | escluso (fonde i satelliti) |
| tsne | k=5 | k=2 | n=2 | n=5 |

Run eseguite il 26/07: `results/lesion/dim_reduction_clustering/<riduzione>/<metodo>/26-07_s1.1_*`. Config di produzione checked-in (`config/pipelines/dim_reduction_clustering.json` + `config/registry/params_clustering.json`) puntano a **pacmap** con questi valori.

## Aperto: DBSCAN

Escluso dalla produzione su tutte le riduzioni — non capito abbastanza a fondo:
- umap/tsne/pca: nessuna struttura reale o quasi tutto rumore
- pacmap: unico caso con segnale reale, ma trade-off qualità/copertura mai risolto (eps=0.3 vs 0.5/0.7)

Da riprendere in una sessione dedicata prima di includerlo in produzione.
