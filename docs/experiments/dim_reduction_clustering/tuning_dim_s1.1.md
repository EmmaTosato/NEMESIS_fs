
#  Dimensionality Reduction S1.1
- **Pipeline:** `dim_reduction`
- **Dati in ingresso:** Matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)
- **Riferimento Log (CSV):** `results/lesion/dim_reduction/<riduzione>/runs_tuning.csv`
- **Parametri in input**: `config.md` in ogni risultato di output
- **Output:** I risultati di questa sessione sono stati scritti nella directory `tuning`


## 03-08-2026 Tuning
- **Data Run Produzione:** 03 Agosto 2026
- **Riduzioni:** UMAP, t-SNE
- **Decisioni:** 
	- Ho fissato a 2 componenti
	- Pipeline (in teoria) completa
- **Risultati**