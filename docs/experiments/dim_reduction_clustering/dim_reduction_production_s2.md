# Log Esperimenti: Dimensionality Reduction — Produzione — SDC (Task 2)

**Pipeline:** `dim_reduction`
**Dati:** Matrice SDC region-wise (`schaefer_200_tian_s2`, `disconnectome`/`mean_overlap`):
- s2.1 = 1119 soggetti × 232 regioni (`data/derived/sdc_matrix/27-08_s2.1`)

Parametri scelti a valle del tuning ([`dim_reduction_tuning_s2.md`](dim_reduction_tuning_s2.md)).

---

## 31-08-2026 — s2.1
#### Prima produzione UMAP (n_components 2 e 3) + t-SNE

**Obiettivo:** produrre i primi embedding SDC di produzione dopo il tuning (28-08).

| ID | Metodo | n_neighbors | min_dist | perplexity | n_components | Link |
| --- | --- | --- | --- | --- | --- | --- |
| s2.1_nc2 | UMAP | 15 | 0.0 | — | 2 | [config.md](../../../results/sdc/dim_reduction/production/umap/31-08_s2.1_nc2_m_euclidean/config.md) |
| s2.1_nc3 | UMAP | 15 | 0.0 | — | 3 | [config.md](../../../results/sdc/dim_reduction/production/umap/31-08_s2.1_nc3_m_euclidean/config.md) |
| s2.1 | t-SNE | — | — | 30 | 2 | [config.md](../../../results/sdc/dim_reduction/production/tsne/31-08_s2.1_m_euclidean/config.md) |

**Note:**
- `s2.1_nc3`: stessi parametri baseline della run 2D gemella (`s2.1_nc2`), non ri-derivati dall'argmax nc=3 proprio — vedi `dim_reduction_tuning_s2.md` per il motivo (argmax mai ispezionato visivamente).
- `s2.1_nc3` non scrive PNG statici (regola nota per `n_components > 2`) — esplorazione solo via `src.pipeline.embedding_app`.
- `color_by` = `["dataset", "side", "nihss"]` su tutte e 3 le run (no `volume`: `metadata.csv` di `build_sdc_matrix.py` non ha `lesion_volume_voxels`, a differenza della matrice voxel-wise lesion).

Prossimo passo: clustering (`clustering.py --reduced_data true`) su uno di questi tre output.
