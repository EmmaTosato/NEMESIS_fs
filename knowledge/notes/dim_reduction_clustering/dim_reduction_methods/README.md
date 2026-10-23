# Metodi di riduzione dimensionale in uso — indice

Una nota per ogni metodo registrato in `REDUCTION_METHODS` (`src/analysis/reduction.py`) e configurato in `config/registry/params_reduction.json` / `params_reduction_sdc.json`. Ogni nota ha le stesse dieci sezioni: cosa fa, perché (obiettivo matematico), il nostro contesto, parametri, tuning, valutazione, quando usarlo, pro e contro, un esempio, insidie. Le fonti sono solo letteratura primaria e documentazione ufficiale; ogni nota chiude con la sua sezione "Fonti".

## I metodi

| Nota | Metodo | Chiave in `REDUCTION_METHODS` | Libreria (versione installata) | Famiglia |
|---|---|---|---|---|
| [pca.md](pca.md) | PCA | `pca` con `rotation: "none"` | `covariance_pca.py` (propria) o `scikit-learn` 1.8.0 | lineare, spettrale |
| [pca_varimax.md](pca_varimax.md) | PCA con rotazione varimax | `pca` con `rotation: "varimax"` | `factor_analyzer` 0.5.1 | lineare + rotazione |
| [tsne.md](tsne.md) | t-SNE (Barnes-Hut), non usato nelle analisi correnti | `tsne` | `scikit-learn` 1.8.0 | neighbor embedding |
| [umap.md](umap.md) | UMAP | `umap` | `umap-learn` 0.5.12 | neighbor embedding |
| [pacmap.md](pacmap.md) | PaCMAP | `pacmap` | `pacmap` 0.9.1 | neighbor embedding a coppie |

Le versioni sono quelle dell'ambiente `nemesis` (verificate con `import umap, sklearn, pacmap`). `openTSNE` non è installato: il t-SNE del progetto è quello di `scikit-learn`.

## Note comuni a tutti i metodi

- [evaluation.md](evaluation.md): come si valuta un embedding (trustworthiness, continuity, conservazione dei *k* vicini, correlazione delle distanze, varianza spiegata) e cosa calcola oggi il repo.
- [`../challenge_of_clustering_after_dim_reduction.md`](../challenge_of_clustering_after_dim_reduction.md): il problema di clusterizzare sopra un embedding.
- [`../dim_reduction_tuning_guide.md`](../dim_reduction_tuning_guide.md): come si leggono i plot e gli indici del tuning nel progetto.
- [`../employed_dim_reduction_methods.md`](../employed_dim_reduction_methods.md): la spiegazione passo per passo di PCA, varimax, mappe *t* e riproducibilità, più il criterio di lettura delle griglie UMAP. Le note di questa cartella vi rimandano invece di ripeterla.
- [`../dim_reduction_literature_survey.md`](../dim_reduction_literature_survey.md): la tassonomia completa dei metodi, anche quelli non usati.

## Il nostro contesto, in breve

| Matrice | Soggetti × variabili | Tipo di valori |
|---|---|---|
| lesione voxel-wise (`s1.2-vol`, `s1.4-vol`) | 5269 × 264.274; 5845 × 221.955 | binari 0/1, molto sparsi |
| disconnettoma voxel-wise (`s2.4-vol`) | 5845 × 227.235 (291.345 nella prima tornata) | continui in [0, 1] (probabilità di disconnessione) |
| disconnettoma per tratto (`s2.4-stream`) | 5831 × 87 | continui |
| disconnettoma parcellato (`s2.1-schaefer-200-tian-s2`) | 1119 × 232 | continui |

Dimensioni da [`docs/guides/dim_reduction.md`](../../../../docs/guides/dim_reduction.md) e [`docs/experiments/README.md`](../../../../docs/experiments/README.md). In quasi tutte le matrici le variabili sono 38-50 volte più dei soggetti (*p* ≫ *n*). L'embedding non è il prodotto finale: è l'ingresso di `clustering.py` (`--reduced_data true`).

## Quale metodo, in una tabella

| Obiettivo | Metodo | Perché | Fonte |
|---|---|---|---|
| Riassumere la varianza, componenti leggibili come mappe | PCA (± varimax) | lineare, deterministica, le componenti sono combinazioni esplicite dei voxel | Jolliffe & Cadima 2016 [1] |
| Confrontarsi con Thiebaut de Schotten et al. 2020 | PCA + varimax sulla covarianza | è il metodo del paper | [2] |
| Vedere i vicinati locali in 2D | t-SNE | massima qualità locale nei benchmark | de Bodt et al. 2025 [3] |
| Embedding a 5-10 dimensioni per un clustering | UMAP | scala bene con `n_components`; prassi emergente, non consolidata | documentazione `umap-learn` [4]; de Bodt et al. 2025 [3] |
| Controllare se una struttura dipende dal metodo | PaCMAP accanto a UMAP/t-SNE | obiettivo diverso (coppie mid-near per il globale) | Wang et al. 2021 [5] |
| Distanze tra gruppi o dimensioni dei gruppi | nessun neighbor embedding | non le conservano | Wattenberg et al. 2016 [6]; de Bodt et al. 2025 [3] |

La raccomandazione comune a tutte le fonti è guardare più di un metodo e più di un valore degli iperparametri: nessun singolo embedding è "quello vero" [3, 6].

## Fonti

1. Jolliffe, I. T., Cadima, J. (2016). *Principal component analysis: a review and recent developments.* Phil. Trans. R. Soc. A 374: 20150202. https://doi.org/10.1098/rsta.2015.0202
2. Thiebaut de Schotten, M. et al. (2020). *Brain disconnections link structural connectivity with function and behaviour.* Nature Communications 11. https://doi.org/10.1038/s41467-020-18920-9 (in `knowledge/papers/stroke_core/`).
3. de Bodt, C., Diaz-Papkovich, A., Kobak, D. et al. (2025). *Low-dimensional embeddings of high-dimensional data.* arXiv:2508.15929 (in `knowledge/papers/methods/`), §4-§6.
4. umap-learn, *Using UMAP for Clustering* e *Frequently Asked Questions*. https://umap-learn.readthedocs.io/en/latest/clustering.html, https://umap-learn.readthedocs.io/en/latest/faq.html
5. Wang, Y., Huang, H., Rudin, C., Shaposhnik, Y. (2021). *Understanding How Dimension Reduction Tools Work: An Empirical Approach to Deciphering t-SNE, UMAP, TriMap, and PaCMAP for Data Visualization.* JMLR 22(201): 1-73. http://jmlr.org/papers/v22/20-1061.html
6. Wattenberg, M., Viégas, F., Johnson, I. (2016). *How to Use t-SNE Effectively.* Distill. https://doi.org/10.23915/distill.00002
