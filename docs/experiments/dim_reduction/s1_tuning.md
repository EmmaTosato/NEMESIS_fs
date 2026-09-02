# Diario Esperimenti

**Pipeline:** Dim Reduction (Tuning)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

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
