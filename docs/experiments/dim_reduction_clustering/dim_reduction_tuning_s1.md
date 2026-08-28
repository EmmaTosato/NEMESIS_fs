# Log Esperimenti: Dimensionality Reduction

**Pipeline:** `dim_reduction`
**Dati:** Matrice lesionale voxel-wise:
- s1.1 = 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)
- s1.2 = 5269 soggetti (`data/derived/lesion_matrix/25-08_s1.2`) — + UCL-UK/UCLStrokeData (4119 soggetti)

---

## 03/04-08-2026 — s1.1 
#### Tuning iniziale

**Obiettivo:** valutare metriche di distanza (euclidean/dice/jaccard) e `n_components` su UMAP/t-SNE.

**Strategie testate** ([`dim_reduction_strategies.csv`](../../../results/dim_reduction_strategies.csv))
- modality: *Lesion in 2D matrix volumetric* 
- datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR

| Metodo | Run | Griglia                                                             | Link                                                                                                                                                                                        |
| ------ | --- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UMAP   | 180 | `metric`∈{euclidean,dice,jaccard} <br><br>`n_components`∈{2,3,5,10} | [config.md](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/03-08_s1.1/tuning_results.csv) |
| t-SNE  | 20  | `metric`∈{euclidean,dice,jaccard} <br><br>`n_components`=2          | —                                                                                                                                                                                           |

**Risultati (Trustworthiness):**
- *Euclidean*: bassa (~0.72), ma struttura continua realistica ("a ragno").
- *Jaccard/Dice*: alta (~0.93), ma cluster spaccati artificialmente per lato lesione.

**Decisioni aperte:** fissare i parametri per produzione (`n_neighbors`, `min_dist`, `perplexity`, `n_components`, `metric`).

---

## 13-08-2026 — s1.1
#### Estensione griglia UMAP (n_components 2 vs 3) + tuning t-SNE

**Obiettivo:** 
- UMAP — aggiungere `n_components`=3 per visualizzazioni 3D, verifica letteratura. 
- t-SNE — ripetere il tuning già fatto per UMAP, con griglia `perplexity` estesa.

**Nota:** `jaccard` escluso da entrambe le griglie rispetto al 03-08 (solo dice/euclidean); `regress_out_volume` rimosso repo-wide il 12-08.

| Metodo | Run | Griglia                                                                                                                                                            | Link                                                                                                                                                                                        |
| ------ | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UMAP   | 120 | `metric`∈{dice,euclidean}<br><br>`n_components`∈{2,3}                                                                                                              | [config.md](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/13-08_s1.1/tuning_results.csv) |
| t-SNE  | 14  | `metric`∈{dice,euclidean} <br><br>`perplexity`∈{5,15,30,50,75,100,200}, <br><br>`n_components`=2 fisso <br>t-SNE non supporta bene oltre le 3D, niente Barnes-Hut) | [config.md](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/tsne/13-08_s1.1/tuning_results.csv) |

**Risultati (Trustworthiness):** stesso pattern già visto il 03-08 (euclidean basso, dice alto).

**Salvati:** `embeddings.npz` per entrambi (UMAP e t-SNE), in vista di un futuro plot interattivo stile "Understanding UMAP".

---

## 26-08-2026 — s1.2 
#### Prima griglia su coorte estesa (5269 soggetti)

**Obiettivo:** ripetere il tuning UMAP/t-SNE già fatto su s1.1 sulla nuova matrice s1.2 (+UCL-UK), per verificare se il pattern trustworthiness euclidean-vs-dice si conferma a coorte estesa (4.6x più grande).

| Metodo | Run | Griglia                                                                                                                    | Link                                                                                                                                                                                        |
| ------ | --- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UMAP   | 120 | `metric`∈{dice,euclidean} <br><br>`n_components`∈{2,3} <br><br>`n_neighbors`∈{5,15,30,50,100} <br><br>`min_dist`∈{0.0,0.01,0.05,0.1,0.5,1.0} | [config.md](../../../results/lesion/dim_reduction/tuning/umap/26-08_s1.2/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/umap/26-08_s1.2/tuning_results.csv) |
| t-SNE  | 14  | `metric`∈{dice,euclidean} <br><br>`perplexity`∈{5,15,30,50,75,100,200} <br><br>`n_components`=2 fisso                                   | [config.md](../../../results/lesion/dim_reduction/tuning/tsne/26-08_s1.2/config.md) · [tuning_results.csv](../../../results/lesion/dim_reduction/tuning/tsne/26-08_s1.2/tuning_results.csv) |

**Risultati (Trustworthiness):** stesso pattern già visto su s1.1 (03-08/13-08), confermato a coorte estesa:

| | euclidean | dice |
|---|---|---|
| UMAP (n_components 2 vs 3) | ~0.67–0.71 | ~0.93–0.95 |
| t-SNE | ~0.73 | ~0.96 |


**Decisioni aperte:** invariate — fissare i parametri di produzione (`n_neighbors`, `min_dist`, `perplexity`, `n_components`, `metric`).
