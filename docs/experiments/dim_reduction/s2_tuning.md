# Diario Esperimenti

**Pipeline:** Dim Reduction (Tuning)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 28-08-2026 — s2.1-schaefer-200-tian-s2

### Tuning iniziale UMAP + t-sne

##### Input
- s2.1-schaefer-200-tian-s2
- Dati raw: matrice SDC region-wise 
	- `schaefer_200_tian_s2`
	- `disconnectome`/`mean_overlap`
- Path: `data/derived/sdc_matrix/27-08_s2.1-schaefer-200-tian-s2`
- 1119 soggetti × 232 regioni
##### Metodi
umap, tsne

##### Obiettivo
- Primo tuning UMAP/t-SNE sull'output di produzione `build_sdc_matrix.py` (s2.1-schaefer-200-tian-s2), per fissare i parametri
- **Nota**: solo `metric=euclidean` sweepato - a differenza del lesion embedding, qui i valori sono probabilità di disconnessione continue (`mean_overlap`), non maschere binarie, quindi dice/jaccard non sono applicabili

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 60 | `metric`=euclidean × `n_components`∈{2,3} × `n_neighbors`∈{5,15,30,50,100} × `min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/sdc/dim_reduction/tuning/umap/28-08_s2.1-schaefer-200-tian-s2/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/umap/28-08_s2.1-schaefer-200-tian-s2/tuning_results.csv) |
| t-SNE | 7 | `metric`=euclidean × `perplexity`∈{5,15,30,50,75,100,200} × `n_components`=2 fisso | [config.md](../../../results/sdc/dim_reduction/tuning/tsne/28-08_s2.1-schaefer-200-tian-s2/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/tsne/28-08_s2.1-schaefer-200-tian-s2/tuning_results.csv) |

Trustworthiness alta e stabile su tutta la griglia (a differenza del lesion embedding, dove euclidean era il ramo debole) - atteso: qui è l'unica metrica sweepata, e i dati SDC sono continui/densi (non sparsi/binari come i voxel di lesione).

| | range |
| --- | --- |
| UMAP (n_components=2) | 0.951–0.979 |
| UMAP (n_components=3) | 0.971–0.983 |
| t-SNE | 0.974–0.985 |

- Migliori combinazioni puntuali:
	- UMAP `n_components=3, n_neighbors=15, min_dist∈[0.05,0.5]` (~0.983); 
	- t-SNE `perplexity=15` (~0.985), `perplexity=30` (~0.984).
- Ispezione visiva: 
	- `n_neighbors=5` produce una struttura molto frammentata ("ragnatela"); `n_neighbors=30–100` torna a rompersi in anelli irregolari;
	- `n_neighbors=15` è il punto di equilibrio, sia per trustworthiness che per continuità visiva. `min_dist` ha effetto marginale fino a 0.1, poi da 0.5 in su la struttura collassa in un blob unico poco informativo.
- Separazione `lesion_side` netta e stabile su tutta la griglia (atteso - la SDC codifica per costruzione l'emisfero disconnesso, non un artefatto come il caso `dice` di lesion). Nessun batch effect per `dataset`, nessun gradiente NIHSS chiaro.

##### Decisioni

- Parametri di produzione fissati: vedi [`s2_production.md`](s2_production.md).

---

## 07-09-2026 — s2.2-vol

### Tuning UMAP su SDC voxel-wise

##### Input
- s2.2-vol
- Dati raw: matrice SDC **voxel-wise** (mappe `disconnectome-map` non parcellate, valori continui 0-1)
- Path: `data/derived/sdc_matrix/07-09_s2.2-vol`
- 1570 soggetti × 290.940 voxel

##### Metodi
umap

##### Obiettivo
- Primo tuning sulla rappresentazione voxel-wise, con la **stessa identica griglia** di s2.1-schaefer-200-tian-s2: a parità di iperparametri, l'unica cosa che cambia è la rappresentazione (232 regioni contro 290.940 voxel), quindi le differenze sono attribuibili a quella
- Solo `metric=euclidean`, stesso motivo di s2.1: valori di disconnessione continui, dice/jaccard non applicabili

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 60 | `metric`=euclidean × `n_components`∈{2,3} × `n_neighbors`∈{5,15,30,50,100} × `min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/sdc/dim_reduction/tuning/umap/07-09_s2.2-vol/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/umap/07-09_s2.2-vol/tuning_results.csv) |

Trustworthiness alta e stabile su tutta la griglia, con lo stesso profilo di s2.1:

| | s2.2-vol (voxel-wise) | s2.1 (parcellata) |
| --- | --- | --- |
| UMAP n_components=2 | 0.940–0.980 | 0.951–0.979 |
| UMAP n_components=3 | 0.974–0.983 | 0.971–0.983 |

- **Stesso ottimo di s2.1**: `n_components=3, n_neighbors=15, min_dist∈[0.05,0.5]` (~0.983). Anche l'andamento per `n_neighbors` coincide — 15 è il massimo, poi si degrada monotonicamente fino a 100.
- Ispezione visiva coerente con s2.1: `n_neighbors=5` frammenta, da 50 in su la struttura si impasta; `min_dist` ha effetto marginale fino a 0.1, da 0.5 collassa in un blob.
- **Separazione `lesion_side` netta e stabile** su tutte le 60 combinazioni — due lobi puliti, come su s2.1. Atteso: la SDC codifica per costruzione l'emisfero disconnesso.
- **Nessun batch effect** per `dataset`: i 5 dataset sono completamente mescolati in ogni combinazione, incluso UKE che qui entra per la prima volta.
- Durata: **2m54s** per 60 combinazioni, grazie alla matrice di distanze precalcolata una volta sola (`precompute_distance_metric: true`). Senza, il tuning su 290.940 feature non sarebbe praticabile in locale.

⚠️ **La trustworthiness di s2.2-vol e quella di s2.1 non sono confrontabili tra loro.** Ognuna misura quanto l'embedding preserva i vicinati *del proprio spazio di input*, e i due spazi di input sono diversi. Numeri uguali non significano "stessa informazione": significano che entrambe le riduzioni sono ugualmente fedeli a ciò da cui partono. Se il voxel-wise aggiunga qualcosa rispetto al parcellato è una domanda aperta, a cui rispondono il confronto strutturale degli embedding e il clustering a valle — non questa metrica.

##### Decisioni
