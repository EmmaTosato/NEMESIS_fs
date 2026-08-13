# Log Esperimenti: Dimensionality Reduction S1.1

**Pipeline:** `dim_reduction`
**Dati:** Matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)

---

## 03-08-2026: Tuning Iniziale

- **Obiettivo:** Valutare metriche spaziali, volume e parametri strutturali su UMAP/t-SNE.
- **Configurazione e Dati:**
  - UMAP (180 run): [Vedi config.md](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1/config.md) | [Vedi tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1/tuning_results.csv)
  - t-SNE (20 run, n=2): (completato il 04-08)
- **Risultati (Trustworthiness):**
  - *Euclidean*: Bassa (~0.72) ma struttura continua realistica ("a ragno").
  - *Jaccard/Dice*: Alta (~0.93) ma cluster spaccati artificialmente per lato lesione.
- **Decisioni Aperte:** Fissare i parametri per produzione (`n_neighbors`, `min_dist`, `perplexity`, `n_components`).

---

## 04-08-2026: Estensione Sweep e Fixes

- **Obiettivo:** Estendere le dimensioni per UMAP e correggere le visualizzazioni (colorazione NIHSS).
- **Risultati:** Run UMAP fusi retroattivamente nella cartella `03-08_s1.1/`. t-SNE scartato per dimensioni >2 per limitazioni computazionali di `sklearn`.
- **Fix Viz:** Ripristinata colorbar, corretti NaN, aggiunta scala logaritmica per il volume.

---

## 13-08-2026: Estensione griglia — n_components 2 vs 3, verifica letteratura

- **Obiettivo:** computare  una terza componente UMAP per visualizzazioni 3D
- **Risultati (Trustworthiness):** stesso pattern già visto su UMAP il 03-08.
- **Configurazione e Dati:**
	- UMAP (120 run):  [Vedi config.md](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1/config.md) | [Vedi tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1/tuning_results.csv)
	- Griglia ridotta rispetto al run del 03-08 --> `jaccard` escluso, solo dice/euclidean
	- rimosso repo-wide il 12-08
 - **Salvati** **Embeddings**  Salvando `embeddings.npz` per un futuro plot interattivo stile "Understanding UMAP"

---

## 13-08-2026: Tuning t-SNE — griglia perplexity estesa, salvataggio embeddings

- **Obiettivo:** ripetere per t-SNE lo stesso tuning già fatto per UMAP (drop `jaccard`, `regress_out_volume` rimosso repo-wide il 12-08)
- **Configurazione e Dati:**
	- t-SNE (14 run):  [Vedi config.md](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1/config.md) | [Vedi tuning_results.csv](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1/tuning_results.csv)
	- estendendo la griglia di `perplexity`: [5, 15, 30, 50, 75, 100, 200]`
	- `n_components` fisso a 2 (t-SNE non supporta bene oltre le 3 dimensioni, niente Barnes-Hut)
- **Risultati (Trustworthiness):** stesso pattern già visto su UMAP il 03-08.
- **Salvati** **Embeddings**  Salvando `embeddings.npz` per un futuro plot interattivo stile "Understanding UMAP"
