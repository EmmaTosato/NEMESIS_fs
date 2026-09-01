# Diario Esperimenti

**Pipeline:** Dim Reduction (Tuning)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 28-08-2026 — s2.1

#### Tuning iniziale

- **Input:**
    - s2.1
    - Dati raw: matrice SDC region-wise (`schaefer_200_tian_s2`, `disconnectome`/`mean_overlap`)
    - Path: `data/derived/sdc_matrix/27-08_s2.1`
    - 1119 soggetti × 232 regioni
- **Metodi:** umap, tsne
- **Obiettivo:**
    - Primo tuning UMAP/t-SNE sull'output di produzione `build_sdc_matrix.py` (s2.1), per fissare i parametri prima del clustering
    - Nota: solo `metric=euclidean` sweepato — a differenza del lesion embedding, qui i valori sono probabilità di disconnessione continue (`mean_overlap`), non maschere binarie, quindi dice/jaccard non sono applicabili

**Risultati**

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 60 | `metric`=euclidean × `n_components`∈{2,3} × `n_neighbors`∈{5,15,30,50,100} × `min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/sdc/dim_reduction/tuning/umap/28-08_s2.1/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/umap/28-08_s2.1/tuning_results.csv) |
| t-SNE | 7 | `metric`=euclidean × `perplexity`∈{5,15,30,50,75,100,200} × `n_components`=2 fisso | [config.md](../../../results/sdc/dim_reduction/tuning/tsne/28-08_s2.1/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/tsne/28-08_s2.1/tuning_results.csv) |

Trustworthiness alta e stabile su tutta la griglia (a differenza del lesion embedding, dove euclidean era il ramo debole) — atteso: qui è l'unica metrica sweepata, e i dati SDC sono continui/densi (non sparsi/binari come i voxel di lesione).

| | range |
| --- | --- |
| UMAP (n_components=2) | 0.951–0.979 |
| UMAP (n_components=3) | 0.971–0.983 |
| t-SNE | 0.974–0.985 |

- Migliori combinazioni puntuali: UMAP `n_components=3, n_neighbors=15, min_dist∈[0.05,0.5]` (~0.983); t-SNE `perplexity=15` (~0.985), `perplexity=30` (~0.984).
- Ispezione visiva (`embeddings_grid_*.png`, solo nc=2 — nc=3 non emette una griglia diagnostica, vincolo noto): `n_neighbors=5` produce una struttura molto frammentata ("ragnatela"); `n_neighbors=30–100` torna a rompersi in anelli irregolari; `n_neighbors=15` è il punto di equilibrio, sia per trustworthiness che per continuità visiva. `min_dist` ha effetto marginale fino a 0.1, poi da 0.5 in su la struttura collassa in un blob unico poco informativo.
- Separazione `lesion_side` netta e stabile su tutta la griglia (atteso — la SDC codifica per costruzione l'emisfero disconnesso, non un artefatto come il caso `dice` di lesion). Nessun batch effect per `dataset`, nessun gradiente NIHSS chiaro.

**Decisioni**

- Parametri di produzione fissati: vedi [`s2_production.md`](s2_production.md).
