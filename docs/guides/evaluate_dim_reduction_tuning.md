# Valutare un tuning già salvato (`evaluate_dim_reduction_tuning`)

Applica a un tuning di `dim_reduction` già concluso le valutazioni che lavorano sui soli embedding (oggi `plot_hdbscan`), senza rifare lo sweep. Funziona su lesione e SDC allo stesso modo: legge solo la cartella del tuning.

- **Script**: `src/pipeline/evaluate_dim_reduction_tuning.py`
- **Configurazione**: `config/pipelines/evaluate_dim_reduction_tuning.json`

---

## Esecuzione

### 1. In locale
```bash
conda activate nemesis
python -m src.pipeline.evaluate_dim_reduction_tuning --config config/pipelines/evaluate_dim_reduction_tuning.json
```

### 2. Sul server (tramite SLURM)
```bash
sbatch jobs/run_evaluate_dim_reduction_tuning.sh
```

---

## Cosa serve

Una cartella di tuning scritta da `dim_reduction` con `save_tuning_embeddings: true`: `embeddings.npz` (tutti gli embedding dello sweep) e `config.md` (la griglia del run). Il numero di embedding in `embeddings.npz` deve corrispondere esattamente alla griglia dichiarata in `config.md`, altrimenti lo script si ferma: una cartella riusata da un run con un'altra griglia non viene valutata.

Se gli embedding non hanno 2 componenti, per disegnarli serve nella griglia anche la stessa combinazione con `n_components=2` (la "gemella" a 2 componenti, mai una fetta delle prime colonne); senza, lo script si ferma prima di calcolare. Non servono la matrice originale né i metadati. Per questo il punteggio dello sweep (`trustworthiness`, `cumulative_explained_variance`), che richiede la matrice, non è accettato qui.

## Parametri JSON

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`tuning_dir`** | *Stringa* | La cartella del tuning, es. `results/lesion/dim_reduction/tuning/umap/07-10_s1.4-vol` o `results/sdc/...`. Deve esistere. Si usa il percorso relativo alla radice del repo: il titolo dei grafici ne deriva la modalità (lesione o SDC); il metodo si legge da `config.md`. |
| **`overwrite`** | *Booleano* | Se `false`, lo script si ferma se i file della valutazione esistono già; se `true`, li sostituisce. |
| **`tuning_evaluations`** | *Oggetto* | Le valutazioni da lanciare, almeno una. Stessa sintassi del blocco omonimo di `dim_reduction.json` (vedi [`dim_reduction.md`](dim_reduction.md)). `plot_hdbscan` vuole esattamente `min_cluster_size` (intero >= 2) e `min_samples` (intero >= 1). I punteggi dello sweep (`trustworthiness`, `cumulative_explained_variance`) sono rifiutati. |

## Output

Gli stessi file che scrive `dim_reduction` quando la valutazione è nel suo blocco, nelle stesse cartelle del tuning (una per foglia dei `nested_params`, es. `metric=.../n_components=.../`): per `plot_hdbscan`, `hdbscan_grid_mcs<N>_ms<M>.png` e `hdbscan_results_mcs<N>_ms<M>.csv`. Le impostazioni stanno nel nome del file: rilanciare con altre impostazioni aggiunge file accanto ai precedenti. Con le stesse impostazioni il risultato è identico a quello calcolato durante lo sweep.

`config.md` del tuning non viene modificato: descrive lo sweep, non le valutazioni successive. Ogni lancio scrive un log in `logs/evaluate_dim_reduction_tuning/`.
