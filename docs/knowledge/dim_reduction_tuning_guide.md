# Tuning della dim reduction — come leggere plot e indici

> **Implementazione:**
>
> - `src/analysis/tuning.py` (calcolo indici, sweep)
> - `src/analysis/plotting.py` (`plot_tuning_curve`, `plot_embedding_grid_blocks`)
> - `src/analysis/embedding_plots.py`/`embedding_coloring.py` (colorazione embedding)
> - Orchestrazione in `src/pipeline/dim_reduction.py` quando `fine_tuning: true`.
>
> **Guida d'uso:** `docs/guides/dim_reduction.md`.
> **Cosa fanno i metodi (UMAP/t-SNE)**: `docs/knowledge/umap_tsne_guide.md`.

## Cos'è il tuning 

Per `umap`/`tsne`/`pacmap`/`pca`/`pca_varimax`, il tuning esegue lo stesso metodo su una griglia di iperparametri (`config/registry/params_reduction.json`'s `tuning_grid`) e calcola, per ogni combinazione, un solo numero di qualità (vedi sotto). **Nessuna selezione automatica**: la scelta finale resta sempre umana, guardando `tuning_results.csv` e i plot, poi scritta a mano in `params_reduction.json`'s `"params"`.

## Le due metriche di valutazione usate

| Metodo                         | Metrica                                | Perché questa e non un'altra                                                                                                                                           |
| ------------------------------ | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `umap`, `tsne`, `pacmap` | **Trustworthiness**              | Nessuna verità di base nota (i cluster non sono etichettati) — l'unica cosa verificabile è se l'embedding ha distorto la vicinanza locale rispetto ai dati originali |
| `pca`, `pca_varimax`       | **Varianza cumulativa spiegata** | Criterio nativo di PCA — quanta informazione (nel senso di varianza) sopravvive comprimendo a`n_components`                                                          |

### Trustworthiness (Venna & Kaski, 2006)

Confronta, per ogni punto, i suoi *k* vicini più prossimi nello spazio originale con i suoi *k* vicini più prossimi nell'embedding. Penalizza solo le **intrusioni**: un punto che nell'embedding sembra vicino ma nello spazio originale non lo era affatto (più è "lontano" nel ranking originale, più pesa la penalità).

- **Range**: `[0, 1]`, più alto = meglio. `1.0` = nessuna intrusione, il vicinato locale è preservato perfettamente.
- **`k` (il numero di vicini controllati) è un parametro a parte**, `trustworthiness_n_neighbors` in `params_reduction.json` — **non** lo stesso `n_neighbors` che UMAP sweeppa per costruire il proprio grafo. Sono due concetti distinti tenuti deliberatamente separati (`docs/dev/analysis.md`).
- **Cosa NON misura**: l'opposto (un vicino vero che nell'embedding finisce lontano) — quella si chiama *continuity*, un indice complementare **non implementato qui** (asimmetria nota della metrica, non un bug del progetto).
- **Va confrontata solo a parità di spazio di distanza**: se l'embedding è costruito con `metric="jaccard"`, il trustworthiness dev'essere calcolato con la *stessa* metrica jaccard, non con l'euclidea di default di `sklearn` — altrimenti si giudica un imbarazzo costruito con un righello con uno diverso (bug reale trovato e corretto in una sessione precedente, vedi `evaluate_umap`/`evaluate_tsne`).
- **Non è comparabile tra `n_components` diversi**: un embedding a più dimensioni ha strutturalmente più "spazio" per preservare i vicini, quindi trustworthiness cresce quasi meccanicamente con `n_components` — non usarla per decidere se un punteggio a 2 componenti è "peggiore" di uno a 10, solo per confrontare combinazioni allo **stesso** `n_components` (vedi sotto).
- **Attenzione ai confondimenti**: un punteggio alto non garantisce un pattern *clinico* interessante — può derivare da un artefatto strutturale della metrica (es. jaccard/dice su maschere binarie che separano nettamente per lato della lesione, non per topografia). Il numero da solo non lo rivela: va incrociato con i plot colorati (`embeddings_grid_dataset.png`/`_side.png`/`_volume.png`).

### Varianza cumulativa spiegata (PCA)

Somma delle prime `n_components` `explained_variance_ratio_` di `sklearn.decomposition.PCA`. Cresce monotonicamente con `n_components` (mai un massimo da cercare) — si legge come una curva a **gomito**: il punto oltre il quale aggiungere componenti aggiunge poca varianza in più. Thiebaut de Schotten et al. 2020 usa una soglia fissa (>90%) come criterio.

## Perché un numero solo non basta: griglia di embedding veri

A differenza del numero (`trustworthiness`/varianza), che è cieco a *come* è fatto l'embedding, `dim_reduction.py` produce anche gli scatter reali (`embeddings_grid_*.png`, uno per parametro libero — vedi `docs/guides/dim_reduction.md` per il meccanismo `nested_params`). Il numero dice "quale combinazione preserva meglio il vicinato"; il plot dice "che forma ha effettivamente l'embedding" — utile per:

- scartare a occhio combinazioni tecnicamente valide ma degeneri (un'unica nuvola informe)
- verificare se una struttura visivamente netta coincide con dataset/lato/volume (confondimento) invece che con un pattern reale

**Nessuno dei due sostituisce l'altro** — leggerli sempre insieme, mai scegliere dal solo plot ("sembra più separato") o dal solo numero.

## File di output per una run di tuning

- `tuning_results.csv`: una riga per combinazione valutata (colonna metrica secondo la tabella sopra). Se `nested_params` è dichiarato, una copia filtrata per ogni foglia (`<param>=<valore>/...`).
- `tuning_plot.png`: curva a 1 parametro (solo se **non** è dichiarato `nested_params` e la griglia libera ha 1 solo parametro) — es. il caso PCA/PaCMAP.
- `embeddings_grid_<colore>.png`: scatter reali per foglia, quando `nested_params` **è** dichiarato (umap/tsne) — vedi sopra.
- `config.md`: uno solo, in cima alla cartella del run — snapshot di `tuning_grid`/`nested_params`/parametri fissi usati, non un risultato.
