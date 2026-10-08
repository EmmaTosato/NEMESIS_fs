# Diario Esperimenti

**Pipeline:** Dim Reduction (Tuning)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 07-10-2026 — s2.4-vol

### Tuning UMAP su SDC voxel-wise, coorte allargata (n=5845)

##### Input
- s2.4-vol
- Dati raw: matrice SDC **voxel-wise** (`disconnectome-map`, valori continui 0-1)
- Path: `data/derived/sdc_matrix/07-10_s2.4-vol`
- 5845 soggetti × 291.345 voxel non costanti

##### Metodi
umap

##### Obiettivo
- Ripetere il tuning di s2.2-vol sulla coorte allargata (8 dataset, 3.7x più soggetti), con `n_components`=10 in più, per fissare i parametri di produzione
- Solo `metric=euclidean`, stesso motivo di s2.2: valori continui, `dice` non applicabile
- Oltre alla trustworthiness, `plot_hdbscan` (`min_cluster_size=100`, `min_samples=10`) su ogni combinazione, solo come diagnostica

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 90 | `metric`=euclidean × `n_components`∈{2,3,10} × `n_neighbors`∈{5,15,30,50,100} × `min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/sdc/dim_reduction/tuning/umap/07-10_s2.4-vol/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/umap/07-10_s2.4-vol/tuning_results.csv) |

| n_components | Trustworthiness (range) | Massimo | A `n_neighbors=15`, `min_dist=0.0` |
| --- | --- | --- | --- |
| 2 | 0.916–0.980 | 0.980 (`n_neighbors=5`, `min_dist=0.01`) | 0.977 |
| 3 | 0.956–0.984 | 0.984 (`n_neighbors=5`, `min_dist=0.0`) | 0.983 |
| 10 | 0.984–0.992 | 0.992 (`min_dist=1.0`); 0.986 con `min_dist` ≤ 0.1 | 0.986 |

- **Profilo come s2.2-vol**: plateau per `min_dist` ≤ 0.1, calo a `min_dist` ≥ 0.5 (a `n_components=10` invece sale, ma i cluster si fondono e il rumore HDBSCAN arriva fino al 30%); trustworthiness che scende con `n_neighbors` crescente.
- **Nessun batch effect** per `dataset`: gli 8 dataset sono mescolati in ogni combinazione.
- **Separazione `lesion_side`**: due lobi con un ponte stretto al centro, come in s2.2-vol. Il segnale principale è la lateralità.
- **HDBSCAN non dà un k robusto**: k da 2 a 20, e cambia anche tra `min_dist` 0.0 e 0.01. L'embedding è un continuum a due lobi con isole piccole; a `n_neighbors` ≥ 30 compare quasi sempre un'isola in alto (circa 100+ soggetti, di più dataset), di cui non so ancora la natura.

##### Decisioni

- **Produzione: `n_neighbors=15`, `min_dist=0.0`**, per `n_components`∈{2,3,10}.
  - Stesso valore di s2.1 e s2.2, quindi le run restano confrontabili.
  - È entro 0.003 dal massimo di trustworthiness per ogni `n_components` (0.001 a 3, 0 a 10 con `min_dist` ≤ 0.1).
  - `n_neighbors=5` guadagna qualche millesimo ma frammenta (a `n_components=2`: k=19, rumore 12%).
  - `min_dist=0.0` resta fisso come in ogni produzione UMAP del progetto.
- Aperto: capire chi sono i soggetti dell'isola in alto.

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
| t-SNE | 7 | `metric`=euclidean × `perplexity`∈{5,15,30,50,75,100,200} × `n_components`=2 fisso | [config.md](../../../results/sdc/dim_reduction/tuning/tsne/07-09_s2.2-vol/config.md) · [tuning_results.csv](../../../results/sdc/dim_reduction/tuning/tsne/07-09_s2.2-vol/tuning_results.csv) |

Trustworthiness alta e stabile su tutta la griglia, con lo stesso profilo di s2.1:

| | s2.2-vol (voxel-wise) | s2.1 (parcellata) |
| --- | --- | --- |
| UMAP n_components=2 | 0.940–0.980 | 0.951–0.979 |
| UMAP n_components=3 | 0.974–0.983 | 0.971–0.983 |
| t-SNE | 0.979–0.985 | 0.974–0.985 |

- **Stesso ottimo di s2.1**: `n_components=3, n_neighbors=15, min_dist∈[0.05,0.5]` (~0.983). Anche l'andamento per `n_neighbors` coincide — 15 è il massimo, poi si degrada monotonicamente fino a 100.
- Ispezione visiva coerente con s2.1: `n_neighbors=5` frammenta, da 50 in su la struttura si impasta; `min_dist` ha effetto marginale fino a 0.1, da 0.5 collassa in un blob.
- **Separazione `lesion_side` netta e stabile** su tutte le 60 combinazioni — due lobi puliti, come su s2.1. Atteso: la SDC codifica per costruzione l'emisfero disconnesso.
- **Nessun batch effect** per `dataset`: i 5 dataset sono completamente mescolati in ogni combinazione, incluso UKE che qui entra per la prima volta.
- Durata: **2m54s** per 60 combinazioni, grazie alla matrice di distanze precalcolata una volta sola (`precompute_distance_metric: true`). Senza, il tuning su 290.940 feature non sarebbe praticabile in locale.

⚠️ **La trustworthiness di s2.2-vol e quella di s2.1 non sono confrontabili tra loro.** Ognuna misura quanto l'embedding preserva i vicinati *del proprio spazio di input*, e i due spazi di input sono diversi. Numeri uguali non significano "stessa informazione": significano che entrambe le riduzioni sono ugualmente fedeli a ciò da cui partono. Se il voxel-wise aggiunga qualcosa rispetto al parcellato è una domanda aperta, a cui rispondono il confronto strutturale degli embedding e il clustering a valle — non questa metrica.

**t-SNE** (7 combinazioni, 41s):

- Il massimo non è un picco ma un **plateau**: `perplexity`∈{15,30,50} stanno tutte a ~0.985, con uno scarto totale di **0.00024** tra le tre. L'argmax stretto è 50, ma la differenza è a livello di rumore e non giustifica da sola una scelta — la stessa situazione di s2.1, dove per la produzione era stato scelto 30 (valore standard di letteratura) invece dell'argmax 15.
- Ispezione visiva: la separazione `lesion_side` è pulita da `perplexity=5` a `50`; a **75 si confonde** nonostante una trustworthiness ancora buona (0.9836), e a 100–200 la struttura collassa in un gradiente diagonale. Il plateau metrico e quello visivo coincidono quindi solo fino a 50 — un buon motivo per non leggere l'argmax da solo.

##### Decisioni

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
