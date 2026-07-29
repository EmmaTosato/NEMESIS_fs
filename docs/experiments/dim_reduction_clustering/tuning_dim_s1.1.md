# Dim Reduction Tuning Results s1.1

Tuning degli iperparametri dell'embedding stesso (non del clustering a valle — per quello vedi [`tuning_dim_clustering_s1.1.md`](tuning_dim_clustering_s1.1.md)). Dati: matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`), sessione `s1.1`. Metrica: trustworthiness(X, embedding).

## 29-07-2026 Analysis — UMAP, t-SNE (+ regress_out_volume)

Rilancio pulito dopo aver eliminato i tuning confusi del 28-07 (griglie riscritte più volte nella stessa cartella, log incoerenti — vedi `.claude/lessons_learned.md`). Griglia estesa: `n_neighbors`/`metric` per UMAP, `perplexity`/`metric` per t-SNE (`perplexity` era prima fissata a 30 dal paper, Thiebaut de Schotten et al. 2020), più `regress_out_volume` (nuovo, sweepabile anche in fine-tuning) per entrambi. Niente più `tuning_plot.png`: con 3 parametri sweepati non viene generato nessun grafico (heatmap rimosse su richiesta) — solo `tuning_results.csv`, sempre completo.

**UMAP** (`results/lesion/dim_reduction/umap/tuning/29-07_s1.1`, griglia `n_neighbors`×`metric`×`regress_out_volume`, 30 combinazioni — 10 skippate per costruzione, `regress_out_volume=true` incompatibile con `metric=jaccard/dice`; tabella sotto è una selezione, dati completi in `tuning_results.csv`):

| n_neighbors | metric    | regress_out_volume | trustworthiness  |
| ----------- | --------- | ------------------- | ---------------- |
| **15**  | **jaccard** | **False**        | **0.945**   |
| 15          | dice      | False                | 0.945            |
| 5           | jaccard   | False                | 0.943            |
| 5           | euclidean | False                | 0.740            |
| 5           | euclidean | True                 | 0.724            |
| 100         | euclidean | True                 | 0.708 (peggiore)  |

**Raccomandazione: n_neighbors=15, metric=jaccard, regress_out_volume=false.** Coincide già con la produzione attuale (`config/registry/params_reduction.json`'s `umap.params`) — nessun cambio necessario.

**t-SNE** (`results/lesion/dim_reduction/tsne/tuning/29-07_s1.1`, griglia `perplexity`×`metric`×`regress_out_volume`, 30 combinazioni — 10 skippate per lo stesso motivo):

| perplexity | metric    | regress_out_volume | trustworthiness  |
| ---------- | --------- | -------------------- | ---------------- |
| **15** | **dice**  | **False**        | **0.954**   |
| 15         | jaccard   | False                 | 0.952            |
| 30         | dice      | False                 | 0.952            |
| 50         | euclidean | False                 | 0.760 (migliore euclidean) |
| 5          | euclidean | True                  | 0.708 (peggiore) |

`jaccard`/`dice` battono `euclidean` di ~0.19–0.20 su ogni `perplexity`, stesso pattern già visto su UMAP. **Raccomandazione: perplexity=15, metric=dice (o jaccard, quasi pari).** La produzione attuale (`tsne.params`: `perplexity=30, metric=euclidean`, trustworthiness≈0.756) **non** usa questi valori — da aggiornare a mano se si decide di adottare la raccomandazione.

**`regress_out_volume` — nessuna combinazione vincente lo usa**: su entrambi i metodi, a parità di `n_neighbors`/`perplexity` ed `euclidean`, `regress_out_volume=true` **abbassa sempre** la trustworthiness (es. UMAP `n_neighbors=5`: 0.740→0.724; t-SNE `perplexity=5`: 0.748→0.708) — coerente con l'essere ridondante/dannoso quando non serve a rimuovere un confondimento reale nell'embedding già scelto. Con `jaccard`/`dice` non è nemmeno valutabile (skip esplicito, incompatibilità per costruzione — vedi `docs/methods/dimensionality_reduction.md`).

Trustworthiness non è comparabile direttamente tra UMAP e t-SNE (dipende dalla metrica sottostante, precomputed per jaccard/dice) — non usarlo per dire "quale riduzione è migliore in assoluto", solo per scegliere i parametri dentro lo stesso metodo.

### Note metodologiche

- Dati sorgente completi: `results/lesion/dim_reduction/<metodo>/tuning/29-07_s1.1/tuning_results.csv` (colonna `skipped_reason` per le combinazioni non valutate) + `config.md` nella stessa cartella (snapshot di `base_params`/`tuning_grid`).
- Nessun valore riportato qui è stato applicato in produzione oltre a quanto già coincidente (UMAP) — `config/pipelines/dim_reduction.json`/`config/registry/params_reduction.json` restano da aggiornare a mano per t-SNE se si decide di adottare la raccomandazione.
