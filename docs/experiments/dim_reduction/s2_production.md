# Diario Esperimenti

**Pipeline:** Dim Reduction (Produzione)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Parametri scelti a valle del tuning ([`s2_tuning.md`](s2_tuning.md)).
- Vedi SESSIONS.md per specifica sulle sessioni

---

## 31-08-2026 — s2.1

#### Prima produzione UMAP (n_components 2 e 3) + t-SNE

- **Input:**
    - s2.1
    - Dati raw: matrice SDC region-wise (`schaefer_200_tian_s2`, `disconnectome`/`mean_overlap`)
    - Path: `data/derived/sdc_matrix/27-08_s2.1`
    - 1119 soggetti × 232 regioni
- **Metodi:** umap, tsne
- **Obiettivo:**
    - Produrre i primi embedding SDC di produzione dopo il tuning (28-08)

**Risultati**

| ID | Metodo | n_neighbors | min_dist | perplexity | n_components | Link |
| --- | --- | --- | --- | --- | --- | --- |
| s2.1_nc2 | UMAP | 15 | 0.0 | — | 2 | [config.md](../../../results/sdc/dim_reduction/production/umap/31-08_s2.1_m_euclidean_nc2/config.md) |
| s2.1_nc3 | UMAP | 15 | 0.0 | — | 3 | [config.md](../../../results/sdc/dim_reduction/production/umap/31-08_s2.1_m_euclidean_nc3/config.md) |
| s2.1 | t-SNE | — | — | 30 | 2 | [config.md](../../../results/sdc/dim_reduction/production/tsne/31-08_s2.1_m_euclidean_p_30/config.md) |

- `s2.1_nc3`: stessi parametri baseline della run 2D gemella (`s2.1_nc2`), non ri-derivati dall'argmax nc=3 proprio — vedi [`s2_tuning.md`](s2_tuning.md) (argmax mai ispezionato visivamente).
- `s2.1_nc3` non scrive PNG statici (regola nota per `n_components > 2`) — esplorazione solo via `src.pipeline.embedding_app`.
- `color_by` = `["dataset", "side", "nihss"]` su tutte e 3 le run (no `volume`: `metadata.csv` di `build_sdc_matrix.py` non ha `lesion_volume_voxels`, a differenza della matrice voxel-wise lesion).

**Decisioni**

- Clustering (`clustering.py --reduced_data true`) su uno di questi tre output.
