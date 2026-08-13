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

---

## 13-08-2026: Estensione griglia — n_components 2 vs 3, verifica letteratura

- **Obiettivo:** valutare se una terza componente UMAP aggiunge struttura reale (non solo rumore) rispetto a 2.
- **Configurazione e Dati:**
  - **UMAP (120 run):**  [Vedi config.md](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1/config.md) | [Vedi tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1/tuning_results.csv)
  - Griglia ridotta rispetto al run del 03-08 (`jaccard` escluso, solo dice/euclidean)
- **Decisioni Aperte:**
-

---

## 13-08-2026: Tuning t-SNE — griglia perplexity estesa, salvataggio embeddings

- **Obiettivo:** ripetere per t-SNE lo stesso tuning già fatto per UMAP (drop `jaccard`, `regress_out_volume` rimosso repo-wide il 12-08, `lessons_learned.md` — feature dismessa perché la regola di incompatibilità con jaccard/dice non reggeva in letteratura), estendendo la griglia di `perplexity` e salvando per la prima volta `embeddings.npz`/`metadata.csv` (`save_tuning_embeddings: true`) per un futuro plot interattivo stile "Understanding UMAP" (vedi `dim_reduction_tuning_guide.md`).
- **Configurazione e Dati:**
  - **t-SNE (14 run):** [Vedi config.md](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1/config.md) | [Vedi tuning_results.csv](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1/tuning_results.csv)
  - Griglia: `metric: [dice, euclidean]` × `perplexity: [5, 15, 30, 50, 75, 100, 200]`, `n_components` fisso a 2 (t-SNE non supporta bene oltre le 3 dimensioni, niente Barnes-Hut).
- **Risultati (Trustworthiness):** stesso pattern già visto su UMAP il 03-08.
  - *Dice*: 0.932–0.954, massimo a `perplexity=15` (0.9539) — ma `embeddings_grid_side.png` conferma lo stesso artefatto: split netto sinistra/destra a quasi ogni perplexity, non struttura topografica reale.
  - *Euclidean*: 0.748–0.760, praticamente piatto su tutto il range, massimo a `perplexity=50` (0.7597) — gradiente continuo, nessuno split netto per lato lesione.
- **Decisioni Aperte:** scegliere `perplexity` finale per produzione (range piatto 5–200, nessun valore domina chiaramente); confermare `euclidean` come metrica di produzione anche per t-SNE, coerentemente con la scelta già fatta su UMAP (dice scartato per l'artefatto lato lesione, non per il numero più basso).
