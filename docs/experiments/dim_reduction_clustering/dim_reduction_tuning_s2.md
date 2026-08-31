# Log Esperimenti: Dimensionality Reduction — SDC (Task 2)

**Pipeline:** `dim_reduction`
**Dati:** Matrice SDC region-wise (`schaefer_200_tian_s2`, `disconnectome`/`mean_overlap`):
- s2.1 = 1119 soggetti × 232 regioni (`data/derived/sdc_matrix/27-08_s2.1`) — UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR

---

## 28-08-2026 — s2.1
#### Tuning iniziale

**Obiettivo:** primo tuning UMAP/t-SNE sull'output di produzione `build_sdc_matrix.py` (s2.1), per fissare i parametri prima del clustering (Task 2).

**Nota:** solo `metric=euclidean` sweepato — a differenza del lesion embedding (s1), qui i valori sono probabilità di disconnessione continue (`mean_overlap`), non maschere binarie, quindi dice/jaccard non sono applicabili.

| Metodo | Run | Griglia | Link |
| ------ | --- | ------- | ---- |
| UMAP   | 60  | `metric`=euclidean <br><br>`n_components`∈{2,3} <br><br>`n_neighbors`∈{5,15,30,50,100} <br><br>`min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/sdc/dim_reduction/tuning/umap/28-08_s2.1/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/umap/28-08_s2.1/tuning_results.csv) |
| t-SNE  | 7   | `metric`=euclidean <br><br>`perplexity`∈{5,15,30,50,75,100,200} <br><br>`n_components`=2 fisso | [config.md](../../../results/sdc/dim_reduction/tuning/tsne/28-08_s2.1/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/tsne/28-08_s2.1/tuning_results.csv) |

**Risultati (Trustworthiness):**

| | range |
|---|---|
| UMAP (n_components=2) | 0.951–0.979 |
| UMAP (n_components=3) | 0.971–0.983 |
| t-SNE | 0.974–0.985 |

Trustworthiness alta e stabile su tutta la griglia (a differenza del lesion embedding, dove euclidean era il ramo debole) — atteso: qui è l'unica metrica sweepata, e i dati SDC sono continui/densi (non sparsi/binari come i voxel di lesione). Migliori combinazioni puntuali: UMAP `n_components=3, n_neighbors=15, min_dist∈[0.05,0.5]` (~0.983); t-SNE `perplexity=15` (~0.985), `perplexity=30` (~0.984).

**Salvati:** `embeddings.npz` per entrambi (UMAP e t-SNE); `understanding_umap_euclidean.html` per UMAP.

**Ispezione visiva** (`embeddings_grid_*.png`, solo nc=2 — nc=3 non emette una griglia diagnostica, vincolo noto): `n_neighbors=5` produce una struttura molto frammentata ("ragnatela"); `n_neighbors=30–100` torna a rompersi in anelli irregolari; `n_neighbors=15` è il punto di equilibrio, sia per trustworthiness che per continuità visiva. `min_dist` ha effetto marginale fino a 0.1, poi da 0.5 in su la struttura collassa in un blob unico poco informativo. Separazione `lesion_side` netta e stabile su tutta la griglia (atteso — la SDC codifica per costruzione l'emisfero disconnesso, non un artefatto come il caso `dice` di lesion). Nessun batch effect per `dataset`, nessun gradiente `NIHSS` chiaro.

**Decisione finale — parametri di produzione:**

| Metodo | n_components | n_neighbors | min_dist | perplexity | Trustworthiness | Note |
|---|---|---|---|---|---|---|
| UMAP | 2 | 15 | 0.0 | — | 0.9785 (argmax) | — |
| UMAP | 3 | 15 | 0.0 | — | 0.9812 | riusa i parametri di nc=2 (stessa logica lesion s1: nc3 non ri-derivato dal proprio argmax) — l'argmax nc=3 vero sarebbe `min_dist=0.5` (0.9827), scartato: mai ispezionato visivamente (nessuna griglia 3D) e in 2D `min_dist=0.5` è già il punto in cui la struttura collassa in blob |
| t-SNE | 2 | — | — | 30 | 0.9840 | valore standard di letteratura (van der Maaten, range 5–50), non l'argmax stretto (`perplexity=15`, 0.9847) — scarto trascurabile (0.0007) |

Prossimo passo: produzione (`results/sdc/dim_reduction/production/`, non ancora creata) e poi clustering (`results/sdc/clustering/`, ancora vuoto).
