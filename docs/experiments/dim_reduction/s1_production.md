# Diario Esperimenti

**Pipeline:** Dim Reduction (Produzione)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Parametri scelti a valle del tuning ([`s1_tuning.md`](s1_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

## 11-08-2026 — s1.1-vol

### Prima produzione UMAP (n_components 2 e 10)

##### Input
- s1.1-vol
- Dati raw: matrice lesionale voxel-wise
- Path: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
umap

##### Obiettivo
- Produrre i primi embedding UMAP dopo il tuning (03/04-08), fissando i parametri migliori per ogni combo metric × n_components

##### Risultati

| ID | metric | n_neighbors | min_dist | n_components | Link |
| --- | --- | --- | --- | --- | --- |
| nc2_m_dice | dice | 15 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1-vol_m_dice_nc2/config.md) |
| nc2_m_euclidean | euclidean | 5 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1-vol_m_euclidean_nc2/config.md) |
| nc10_m_dice | dice | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1-vol_m_dice_nc10/config.md) |
| nc10_m_euclidean | euclidean | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1-vol_m_euclidean_nc10/config.md) |


---

## 13-08-2026 — s1.1-vol

### Produzione UMAP 3D (n_components=3)

##### Input
- s1.1-vol
- Dati raw: matrice lesionale voxel-wise
- Path: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
umap

##### Obiettivo
- Produrre l'embedding UMAP a 3 componenti per visualizzazione 3D dopo il tuning (13-08 

##### Risultati

| ID              | metric    | n_neighbors | min_dist | n_components | Link                                                                                                    |
| --------------- | --------- | ----------- | -------- | ------------ | ------------------------------------------------------------------------------------------------------- |
| nc3_m_euclidean | euclidean | 5           | 0.0      | 3            | [config.md](../../../results/lesion/dim_reduction/production/umap/13-08_s1.1-vol_m_euclidean_nc3/config.md) |
| nc3_m_dice      | dice      | 30          | 0.0      | 3            | [config.md](../../../results/lesion/dim_reduction/production/umap/13-08_s1.1-vol_m_dice_nc3/config.md)      |
|                 |           |             |          |              |                                                                                                         |

- `nc3_m_euclidean` — stessi parametri baseline della produzione 2D euclidean (11-08), solo `n_components` cambiato.


---

## 28-08-2026 — s1.1-vol

### Prima produzione t-SNE 

##### Input
- s1.1-vol
- Dati raw: matrice lesionale voxel-wise
- Path: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
tsne

##### Obiettivo
- Prima produzione t-SNE valida per s1.1-vol dopo il tuning (03/04/13-08) 

##### Risultati

| ID | metric | perplexity | Link |
| --- | --- | --- | --- |
| s1.1-vol_m_dice | dice | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.1-vol_m_dice_p_30/config.md) |
| s1.1-vol_m_euclidean | euclidean | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.1-vol_m_euclidean_p_30/config.md) |

- `perplexity=30` per entrambe le metriche (non l'argmax per-metrica) — coerenza tra le due run compagne, stessa logica del `min_dist=0.0` condiviso in produzione UMAP.
- Verifica visiva dell'artefatto `dice`/`lesion_side` 


---

## 28-08-2026 — s1.2-vol

### Produzione UMAP  su coorte allargta (n=5269)

##### Input
- s1.2-vol
- Dati raw: matrice lesionale voxel-wise (+ UCL-UK/UCLStrokeData)
- Path: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
umap

##### Obiettivo
- Riprodurre su s1.2-vol gli stessi 6 embedding di produzione già fatti su s1.1-vol (`{dice,euclidean}×{2,3,10}`), stessi `n_neighbors`/`min_dist` per combo 
- Post tuning del `26-08`

##### Risultati

| ID | metric | n_neighbors | min_dist | n_components | Link |
| --- | --- | --- | --- | --- | --- |
| nc2_m_dice | dice | 15 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2-vol_m_dice_nc2/config.md) |
| nc2_m_euclidean | euclidean | 5 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2-vol_m_euclidean_nc2/config.md) |
| nc3_m_dice | dice | 30 | 0.0 | 3 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2-vol_m_dice_nc3/config.md) |
| nc3_m_euclidean | euclidean | 5 | 0.0 | 3 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2-vol_m_euclidean_nc3/config.md) |
| nc10_m_dice | dice | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2-vol_m_dice_nc10/config.md) |
| nc10_m_euclidean | euclidean | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2-vol_m_euclidean_nc10/config.md) |

- Stesso caveat noto per `dice`: alto trustworthiness, split artificiale per `lesion_side`.


---

## 28-08-2026 — s1.2-vol

### Produzione t-SNE  su coorte allargta (n=5269)

##### Input
- s1.2-vol
- Dati raw: matrice lesionale voxel-wise (+ UCL-UK/UCLStrokeData)
- Path: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
tsne

##### Obiettivo
- Prima produzione t-SNE valida per s1.2-vol dopo tuning del `26-08`

##### Risultati

| ID | metric | perplexity | Link |
| --- | --- | --- | --- |
| s1.2-vol_m_dice | dice | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.2-vol_m_dice_p_30/config.md) |
| s1.2-vol_m_euclidean | euclidean | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.2-vol_m_euclidean_p_30/config.md) |

-  I grid `embeddings_grid_side.png` mostrano lo stesso artefatto già noto su UMAP: con `dice`, i soggetti `right`/`left` si separano in due bande nette, stabili a **ogni** valore di perplexity testato (5→200) — non è un effetto della perplexity, è strutturale alla metrica. 
- `perplexity=30` e `min_dist=0.0`per entrambe le metriche (non l'argmax per-metrica) --> coerenza tra le due run compagne 
