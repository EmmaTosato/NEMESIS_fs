# Dim Reduction Tuning Results s1.1

Tuning degli iperparametri dell'embedding stesso (non del clustering a valle — per quello vedi [`tuning_dim_clustering_s1.1.md`](tuning_dim_clustering_s1.1.md)). Dati: matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`), sessione `s1.1`. Metrica: trustworthiness(X, embedding).

## 28-07-2026 Analysis — UMAP, t-SNE

`n_neighbors`/`metric` per UMAP, `perplexity` per t-SNE — prima fissata a 30 dal paper (Thiebaut de Schotten et al. 2020), ora sweepata per la prima volta.

**UMAP** (`results/lesion/dim_reduction/umap/tuning/28-07_s1.1`, griglia `n_neighbors`×`metric`, 15 combinazioni):

| n_neighbors    | metric          | trustworthiness  |
| -------------- | --------------- | ---------------- |
| **15**   | **jaccard**| **0.945**  |
| 15             | dice            | 0.945            |
| 5              | jaccard         | 0.943            |
| 30             | dice/jaccard    | 0.941            |
| 5              | euclidean       | 0.740            |
| 100            | euclidean       | 0.718 (peggiore) |

`jaccard`/`dice` battono `euclidean` di ~0.20 su ogni `n_neighbors` (atteso: normalizzano per il volume lesionale, coerente con `docs/methods/dimensionality_reduction.md`). **Raccomandazione: n_neighbors=15, metric=jaccard.** Nota: la produzione attuale (`params.umap`: `n_neighbors=5, metric=euclidean`, trustworthiness=0.740 nel `runs.csv`) non usa ancora nessuna delle due — da aggiornare.

**t-SNE** (`results/lesion/dim_reduction/tsne/tuning/28-07_s1.1`, griglia `perplexity`, 5 combinazioni):

| perplexity     | trustworthiness |
| -------------- | --------------- |
| **50**   | **0.760** |
| 30             | 0.756           |
| 15             | 0.755           |
| 75             | 0.754           |
| 5              | 0.748           |

Range piatto (0.748–0.760) — a differenza di UMAP, `perplexity` incide poco. **Raccomandazione: perplexity=50**, ma il default attuale (30, 0.756) è comunque a un soffio dal massimo — cambiamento facoltativo.

Trustworthiness non è comparabile direttamente tra UMAP e t-SNE (per UMAP jaccard/dice usa una distanza precomputed, per t-SNE sempre euclidean) — non usarlo per dire "quale riduzione è migliore in assoluto", solo per scegliere i parametri dentro lo stesso metodo.

### Note metodologiche

- Dati sorgente completi: `results/lesion/dim_reduction/<metodo>/tuning/*/tuning_results.csv` + plot nella stessa cartella.
- Nessun valore riportato qui è stato applicato in produzione — `config/pipelines/dim_reduction.json`/`config/registry/params_reduction.json` restano da aggiornare a mano se si decide di adottare i parametri raccomandati.
