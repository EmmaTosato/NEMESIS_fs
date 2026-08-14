# Tuning della dim reduction — come leggere plot e indici

> **Implementazione:** `src/analysis/tuning.py` (calcolo indici, sweep), `src/analysis/plotting.py` (`plot_tuning_curve`, `plot_embedding_grid_blocks`), `src/analysis/embedding_plots.py`/`embedding_coloring.py` (colorazione embedding). Orchestrazione in `src/pipeline/dim_reduction.py` quando `fine_tuning: true`.
> **Guida d'uso:** `docs/guides/dim_reduction.md`. **Cosa fanno i metodi**: `dim_reduction.md`, `umap_tsne_guide.md`.

## Cos'è il tuning

Per `umap`/`tsne`/`pacmap`/`pca`/`pca_varimax`, il tuning esegue lo stesso metodo su una griglia di iperparametri (`config/registry/params_reduction.json`'s `tuning_grid`) e calcola, per ogni combinazione, un solo numero di qualità. **Nessuna selezione automatica**: la scelta finale resta sempre umana, guardando `tuning_results.csv` e i plot, poi scritta a mano in `params_reduction.json`'s `"params"`.

## Le due metriche

| Metodo | Metrica | Perché |
|---|---|---|
| `umap`, `tsne`, `pacmap` | **Trustworthiness** (Venna & Kaski, 2006) | Nessun ground truth noto — l'unica cosa verificabile è se l'embedding ha distorto la vicinanza locale rispetto ai dati originali |
| `pca`, `pca_varimax` | **Varianza cumulativa spiegata** | Criterio nativo di PCA — quanta informazione sopravvive comprimendo a `n_components` |

**Trustworthiness**: confronta, per ogni punto, i suoi *k* vicini nello spazio originale con i suoi *k* vicini nell'embedding, penalizzando solo le **intrusioni** (un punto vicino nell'embedding ma non nello spazio originale — non misura l'opposto). Range `[0,1]`, più alto = meglio.

- `k` è un parametro a parte (`trustworthiness_n_neighbors`), **non** lo stesso `n_neighbors` di UMAP (`docs/dev/config.md`).
- Va calcolata con la **stessa metrica** con cui è costruito l'embedding (jaccard con jaccard, non l'euclidea di default di sklearn) — bug reale trovato e corretto in una sessione precedente.
- **Non comparabile tra `n_components` diversi**: cresce quasi meccanicamente con più dimensioni — confrontare solo a parità di `n_components` (da qui la scelta di tenerlo tra i `nested_params`).
- Un punteggio alto non garantisce un pattern *clinico* interessante (può essere un artefatto strutturale, es. jaccard/dice che separa nettamente per lato lesione) — va sempre incrociato con i plot colorati.

**Varianza cumulativa spiegata**: somma delle prime `n_components` `explained_variance_ratio_` di sklearn. Cresce monotonicamente — si legge come curva a **gomito**. Thiebaut de Schotten et al. 2020 usa soglia fissa >90%.

## Numero e plot, mai uno solo

Il numero è cieco a *come* è fatto l'embedding — `dim_reduction.py` produce anche gli scatter reali (`embeddings_grid_*.png`, uno per parametro libero, meccanismo `nested_params` in `docs/guides/dim_reduction.md`). Il numero dice "quale combinazione preserva meglio il vicinato"; il plot dice "che forma ha l'embedding" — utile per scartare combinazioni tecnicamente valide ma degeneri, o per notare se una struttura netta coincide con dataset/lato/volume (confondimento) invece che un pattern reale. **Leggerli sempre insieme.**

## File di output

- `tuning_results.csv`: una riga per combinazione (colonna metrica secondo la tabella sopra). Se `nested_params` è dichiarato, una copia filtrata per ogni foglia.
- `tuning_plot.png`: curva a 1 parametro (solo se **non** c'è `nested_params` e la griglia libera ha 1 solo parametro — es. PCA/PaCMAP).
- `embeddings_grid_<colore>.png`: scatter reali per foglia, quando `nested_params` **è** dichiarato (umap/tsne).
- `embeddings.npz` (opt-in, `save_tuning_embeddings: true`): l'embedding vero di **ogni** combinazione sweeppata, indicizzato da una chiave `"chiave1=valore1,..."` — pensato per un futuro plot interattivo stile Figura 4 di [pair-code.github.io/understanding-umap](https://pair-code.github.io/understanding-umap/) (griglia `n_neighbors`×`min_dist`, solo lettura/plotting, mai rifit lato browser — non ancora implementato).
- `metadata.csv` (stesso trigger di `embeddings.npz`): anagrafica arricchita (`lesion_volume_voxels`/`lesion_side`/`nihss`), necessaria perché `embeddings_grid_*.png` colora i punti al volo.
- `config.md`: snapshot di `tuning_grid`/`nested_params`/parametri fissi per l'intero run.
