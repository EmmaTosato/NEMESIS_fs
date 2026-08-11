# Log Esperimenti: Dimensionality Reduction S1.1

**Pipeline:** `dim_reduction`
**Dati:** Matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)

---

## 03-08-2026: Tuning Iniziale

- **Obiettivo:** Valutare metriche spaziali, volume e parametri strutturali su UMAP/t-SNE.
- **Configurazione e Dati:**
  - **UMAP (180 run):** [Vedi config.md](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1/config.md) | [Vedi tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1/tuning_results.csv)
  - **t-SNE (20 run, n=2):** (completato il 04-08)
- **Risultati (Trustworthiness):**
  - *Euclidean*: Bassa (~0.72) ma struttura continua realistica ("a ragno").
  - *Jaccard/Dice*: Alta (~0.93) ma cluster spaccati artificialmente per lato lesione.
- **Confronto `n_components`:** (Δ calcolato in `notebooks/dim_reduction.ipynb` §6)
  - *Dice/Jaccard/Euclidean (senza regress)*: Saturano a 5 (Δ5→10 ≈ 0).
  - *Euclidean (con regress=True)*: Migliora fino a 10 (Δ5→10 ≈ +0.011).
- **Decisioni Aperte:** Fissare i parametri per produzione (`n_neighbors`, `min_dist`, `perplexity`, `n_components`).

---

## 04-08-2026: Estensione Sweep e Fixes

- **Obiettivo:** Estendere le dimensioni per UMAP e correggere le visualizzazioni (colorazione NIHSS).
- **Risultati:** Run UMAP fusi retroattivamente nella cartella `03-08_s1.1/`. t-SNE scartato per dimensioni >2 per limitazioni computazionali di `sklearn`.
- **Note Tecniche e Ottimizzazioni:**
  - **Bug Fix `regress_out_volume`:** Corretto crash al rifit omettendo il parametro dal costruttore UMAP (`lessons_learned.md` #17).
  - **Fix Viz:** Ripristinata colorbar, corretti NaN, aggiunta scala logaritmica per il volume.
  - **Ottimizzazioni:** Aggiunto flag `write_embeddings_grid` per evitare calcoli e plot ridondanti.
  - **Letteratura:** Creati `dim_reduction_tuning_guide.md` e `umap_tsne_guide.md`.
