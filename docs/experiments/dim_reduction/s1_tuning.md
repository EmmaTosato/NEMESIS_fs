# Diario Esperimenti

**Pipeline:** Dim Reduction (Tuning)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 07-10-2026 — s1.4-vol

### Tuning UMAP e scelta dei parametri di produzione

##### Input
- s1.4-vol
- Dati raw: matrice lesionale voxel-wise (2mm)
- Path: `data/derived/lesion_matrix/07-10_s1.4-vol`
- 5845 soggetti
##### Metodi
umap

##### Obiettivo
- Scegliere `n_neighbors` e `min_dist` di produzione per ogni modalità `metric × n_components`
- Criterio: HDBSCAN lanciato su ogni combinazione (`min_cluster_size=100`, `min_samples=10`) come sonda di stabilità. Si cerca il plateau, cioè i riquadri adiacenti della griglia con stesso disegno, stesso numero di cluster `k` e poco rumore ([`employed_dim_reduction_methods.md`](../../../knowledge/dim_reduction_clustering/employed_dim_reduction_methods.md), "Scegliere `n_neighbors` e `min_dist` di UMAP guardando le griglie")

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 180 | `metric`∈{dice,euclidean} × `n_components`∈{2,3,10} × `n_neighbors`∈{5,15,30,50,100} × `min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/lesion/dim_reduction/tuning/umap/07-10_s1.4-vol/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/07-10_s1.4-vol/tuning_results.csv) |

- `dice`: a `n_neighbors=100` e `min_dist` ≤ 0.1 il disegno è lo stesso a ogni `n_components` (due blob grandi, sinistro e destro, più una catena di circa 6 piccoli cluster; `k`=8, rumore 1–2%). A `n_neighbors` ≤ 15 i blob si spezzano in 5–6 pezzi e `k` oscilla; a `min_dist` ≥ 0.5 i blob si toccano e il rumore sale.
- `euclidean`: nessun plateau. Il disegno cambia a ogni riquadro, il rumore è 13–67% e c'è sempre un anello denso al centro.
- La separazione sinistra/destra compare in ogni riquadro `dice`: è una proprietà della metrica e non distingue una combinazione dall'altra.

##### Decisioni

| Modalità | `n_neighbors` | `min_dist` | Motivo |
| --- | --- | --- | --- |
| dice, nc2 | 100 | 0.0 | La riga 100 non cambia al variare di `min_dist` (`k`=8 fino a 0.5). Con 50 il riquadro `min_dist=0.01` salta a `k`=18 con 14% di rumore |
| dice, nc3 | 50 | 0.05 | Tutti i vicini danno `k`=7–8, rumore ≤1%. A `min_dist=0.0` il vicino a `n_neighbors=30` salta a `k`=11 |
| dice, nc10 | 50 | 0.0 | Vicini a `k`=7–8, rumore 0–1%; a `min_dist=0.5` il rumore è 9% (20% con `n_neighbors=100`) |
| euclidean, nc2 | 5 | 0.0 | Nessun plateau, vedi sotto |
| euclidean, nc3 | 5 | 0.0 | Nessun plateau, vedi sotto |
| euclidean, nc10 | 5 | 0.0 | Nessun plateau, vedi sotto |

- Un `min_dist` basso rende i gruppi netti per costruzione; qui è accettabile perché lo stesso `k` e lo stesso disegno restano a `min_dist` 0.01–0.1.
- Il plateau è il livello grossolano: ogni blob è un unico cluster. La sottostruttura interna ai blob compare solo a `n_neighbors` bassi, dove è instabile, e va cercata nel clustering.
- `euclidean` (nc2, nc3, nc10): per nc2 e nc3 gli stessi valori della produzione s1.2. Le griglie non mostrano alcun plateau, quindi non giustificano una scelta robusta; `n_neighbors=5` è inoltre il valore minimo della griglia.

---

## 26-08-2026 — s1.2-vol

### Tuning su coorte estesa UMAP + t-sne (n=5269 )

##### Input
- s1.2-vol
- Dati raw: matrice lesionale voxel-wise (+ UCL-UK/UCLStrokeData)
- Path: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
umap, tsne

##### Obiettivo
- Ripetere il tuning UMAP/t-SNE già fatto su s1.1-vol sulla matrice estesa, per verificare se il pattern trustworthiness euclidean-vs-dice si conferma a coorte estesa (4.6x più grande)

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 120 | `metric`∈{dice,euclidean} × `n_components`∈{2,3} × `n_neighbors`∈{5,15,30,50,100} × `min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/lesion/dim_reduction/tuning/umap/26-08_s1.2-vol/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/26-08_s1.2-vol/tuning_results.csv) |
| t-SNE | 14 | `metric`∈{dice,euclidean} × `perplexity`∈{5,15,30,50,75,100,200} × `n_components`=2 fisso | [config.md](../../../results/lesion/dim_reduction/tuning/tsne/26-08_s1.2-vol/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/tsne/26-08_s1.2-vol/tuning_results.csv) |

- Trustworthiness: stesso pattern già visto su s1.1-vol (03-08/13-08), confermato a coorte estesa:

| | euclidean | dice |
| --- | --- | --- |
| UMAP (n_components 2 vs 3) | ~0.67–0.71 | ~0.93–0.95 |
| t-SNE | ~0.73 | ~0.96 |

##### Decisioni

- Fissare i parametri di produzione (`n_neighbors`, `min_dist`, `perplexity`, `n_components`, `metric`).

---

## 13-08-2026 — s1.1-vol

### Estensione griglia UMAP (n_components 2 vs 3) + tuning t-SNE

##### Input
- s1.1-vol
- Dati raw: matrice lesionale voxel-wise
- Path: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
umap, tsne

##### Obiettivo
- UMAP — aggiungere `n_components`=3 per visualizzazioni 3D, verifica letteratura
- t-SNE — ripetere il tuning già fatto per UMAP, con griglia `perplexity` estesa
- Nota: `jaccard` escluso da entrambe le griglie rispetto al 03-08 (solo dice/euclidean); `regress_out_volume` rimosso repo-wide il 12-08

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 120 | `metric`∈{dice,euclidean} × `n_components`∈{2,3} | [config.md](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1-vol/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1-vol/tuning_results.csv) |
| t-SNE | 14 | `metric`∈{dice,euclidean} × `perplexity`∈{5,15,30,50,75,100,200}, `n_components`=2 fisso (niente Barnes-Hut oltre le 3D) | [config.md](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1-vol/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1-vol/tuning_results.csv) |

- Trustworthiness: stesso pattern già visto il 03-08 (euclidean basso, dice alto).
##### Decisioni

- Fissare i parametri di produzione (`n_neighbors`, `min_dist`, `perplexity`, `n_components`, `metric`).

---

## 03/04-08-2026 — s1.1-vol

### Tuning iniziale UMAP + t-sne

##### Input
- s1.1-vol
- Dati raw: matrice lesionale voxel-wise
- Path: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
umap, tsne

##### Obiettivo
- Valutare metriche di distanza (euclidean/dice/jaccard) e `n_components` su UMAP/t-SNE

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| UMAP | 180 | `metric`∈{euclidean,dice,jaccard} × `n_components`∈{2,3,5,10} | [config.md](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1-vol/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1-vol/tuning_results.csv) |
| t-SNE | 20 | `metric`∈{euclidean,dice,jaccard} × `n_components`=2 | — |

- Trustworthiness: *euclidean* bassa (~0.72) ma struttura continua realistica ("a ragno"); *jaccard/dice* alta (~0.93) ma cluster spaccati artificialmente per lato lesione.

##### Decisioni

- Fissare i parametri per produzione (`n_neighbors`, `min_dist`, `perplexity`, `n_components`, `metric`).
