# Guida alla Riduzione della Dimensionalità (Dim Reduction)

Questa guida descrive l'utilizzo della pipeline `dim_reduction.py`. Il suo scopo è comprimere una matrice di lesioni molto complessa estraendone le sole "caratteristiche matematiche salienti" (componenti principali o embedding), un passo essenziale per poter visualizzare grafici a dispersione o eseguire clustering.

- **Script**: `src/pipeline/dim_reduction.py`
- **Configurazione**: `config/pipelines/dim_reduction.json`

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione.
```bash
sbatch jobs/run_dim_reduction.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`:
```bash
python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json
```

---

## Cos'è la Riduzione della Dimensionalità?

Immagina una matrice *Voxel-wise*: ogni paziente è definito da centinaia di migliaia di voxel. Non è possibile graficare 800.000 assi. Gli algoritmi di riduzione riassumono il paziente in 2, 3 o più "coordinate". Se chiedi 2 coordinate, puoi visualizzare ogni paziente su un grafico X/Y. Pazienti clinicamente o strutturalmente simili si troveranno vicini.

---

## Modalità di Funzionamento

### 1. Modalità Fine-Tuning (`"fine_tuning": true`)
Gli algoritmi (come UMAP o t-SNE) richiedono parametri non universali, come `n_neighbors`. **Non esiste un valore giusto a priori.** 
In modalità Tuning, lo script esegue esperimenti su una griglia di combinazioni (*grid search*) elencate in `config/registry/params_reduction.json`, producendo tabelle e grafici di affidabilità (Trustworthiness).

- **Parametri Nested (`nested_params`)**: Con molteplici parametri (es. UMAP ha metric, n_components, n_neighbors...), la visualizzazione esploderebbe. Il registry permette di specificare `nested_params`. I parametri primari (es. la metrica) generano sottocartelle, e il grid visuale (`embeddings_grid_unico.png`) viene mostrato solo sulle 1 o 2 variabili libere rimanenti. **Regola (26-08-26)**: nessuna combinazione a più di 2 componenti viene mai più rifittata/mostrata in questo grid, né come PNG né come HTML — se `n_components` è tra i `nested_params` e la sottocartella corrisponde a un valore diverso da 2, quella foglia non riceve nessun file; se `n_components` è invece un parametro libero (variato dentro una foglia), solo le singole combinazioni con `n_components != 2` vengono scartate, le altre restano. Per vedere davvero una combinazione a più componenti (in 3D, interattivo) c'è `scripts/plot_tuning_embedding_3d.py`, da lanciare a mano — vedi `docs/guides/embedding_app.md`. Stessa logica in Produzione: con `viz_n_components: 3` non viene scritto nessun PNG/HTML statico (mai, da prima del 26-08-26) — l'esplorazione 3D è sempre e solo `src.pipeline.embedding_app`, l'app Dash live.

### 2. Modalità Produzione (`"fine_tuning": false`)
Dopo aver scelto i parametri nel tuning, salvarli nel registry. L'avvio in modalità produzione elaborerà il file finale da usare nei passaggi successivi.

---

## Dettaglio Parametri JSON (`dim_reduction.json`)

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`project`** | *Stringa* | Nome del progetto (es. `"clinical_connectome"`). |
| **`input_path`** | *Stringa* | Percorso della matrice di output generata dal *Matrix Building*. DEVE esistere. |
| **`reduction_method`** | *Stringa* | L'algoritmo da usare. Valori: `"umap"`, `"tsne"`, `"pca"`, `"pacmap"`. *(Nota: `pca_varimax` è momentaneamente rimosso).* |
| **`params_file`** | *Stringa* | Il percorso al registro logico: `"config/registry/params_reduction.json"`. |
| **`output_root`** | *Stringa* | Cartella per i risultati (es. `"results/lesion/dim_reduction"`). |
| **`session_name`** | *Stringa* | Nome dell'esperimento (es. `"umap_test_1"`). |
| **`overwrite`** | *Booleano* | Se `true`, sovrascrive esecuzioni preesistenti aventi lo stesso nome. |
| **`fine_tuning`** | *Booleano* | Attiva/disattiva il *grid search* dei parametri. |
| **`viz_n_components`** | *Intero (2 o 3)* | Dimensioni fisse del plot grafico, anche se la compressione vera è a più dimensioni. Evita distorsioni di "taglio". A `3`, fornisce solo l'HTML interattivo ruotabile. |
| **`color_by`** | *Lista* | Genera plot colorati per specifici tag: `"dataset"`, `"side"`, `"volume"`, `"nihss"`. |
| **`write_embeddings_grid`** | *Booleano* | Se `false`, disattiva manualmente `embeddings_grid_*.png` in modalità Fine-Tuning (resta comunque scritto `tuning_results.csv`). Indipendente dallo skip automatico per foglie a `n_components` ≠ 2 (vedi sopra) — quello si applica comunque, `write_embeddings_grid` o no. |
| **`save_tuning_embeddings`** | *Booleano* | Se `true`, salva in `embeddings.npz` l'embedding effettivo di **ogni** combinazione valutata nel Fine-Tuning (non solo quelle mostrate in `embeddings_grid_*.png`), più un `metadata.csv` autosufficiente accanto — vedi sotto. Opt-in, `false` di default: nessuna run precedente all'introduzione di questo campo ha mai scritto questi file. |
| **`precompute_distance_metric`** | *Booleano* | Solo per la modalità **Produzione** (`fine_tuning: false`) — nessun effetto in Fine-Tuning. Se `true` (consigliato, comportamento di tutte le run prima dell'introduzione di questo campo), per `metric` in `jaccard`/`dice`/`euclidean` precalcola l'intera matrice di distanze una volta sola invece di farlo ricalcolare da UMAP/t-SNE ad ogni fit — molto più veloce, e garantisce ricerca dei vicini *esatta* indipendentemente dal numero di soggetti. Se `false`, passa la metrica grezza direttamente a UMAP/t-SNE (nessun precompute) — comportamento "standard" identico a un run UMAP/t-SNE esterno senza questo meccanismo, utile per confrontabilità con la letteratura. Nota: sopra i 4096 soggetti (soglia interna, non documentata, di `umap-learn`) i due modi danno risultati **diversi** (esatto vs approssimato) — sotto i 4096 sono equivalenti. Vedi `docs/debugging/debug_25_08_26.md`. |

---

## Output e Diari Storici

**Dal 2026-08, i risultati di produzione e di tuning vivono in due rami separati sotto `output_root`, mai mescolati**: `results/lesion/dim_reduction/production/<metodo>/<Data>_<session_name>_<tag>` e `results/lesion/dim_reduction/tuning/<metodo>/<Data>_<session_name>`. Prima di questa data `tuning/` viveva dentro la cartella del metodo (`<metodo>/tuning/...`) — se stai guardando risultati più vecchi di questa data, tienilo a mente.

### In Modalità Produzione
- **`matrix.npy`**: La nuova matrice compressa.
- **`metadata.csv`**: L'anagrafica arricchita in automatico di `lesion_volume_voxels`, `lesion_side`, e `nihss`.
- **Plot Grafici**: Un `embedding_plot_unico.png` base (solo per embedding 2D — con `viz_n_components: 3` nessun PNG statico viene scritto, vedi sotto), più un PNG statico per ogni voce elencata in `color_by` (`embedding_plot_<voce>.png`). Non viene più scritto un file `embedding_plot_interactive.html` per-run (rimosso 2026-08-14) — l'esplorazione interattiva 2D/3D con bottoni di colorazione è ora `src.pipeline.embedding_app` (`docs/guides/embedding_app.md`), un'app Dash live che legge qualunque run di produzione già scritto, non un file da rigenerare per ogni run.

### In Modalità Fine-Tuning
- **`tuning_results.csv`**: I punteggi matematici estratti per ogni esperimento.
- **`tuning_plot.png`** e **`embeddings_grid_*.png`**: I plot per visualizzare come cambia la compressione al variare dei parametri, organizzati per sottocartelle se si usa la struttura *nested*.
- **`embeddings.npz`** (solo se `save_tuning_embeddings: true`): un unico file con l'embedding vero e proprio di ogni combinazione valutata, non solo quelle disegnate nei plot. Ogni array è indicizzato da una chiave leggibile tipo `"n_neighbors=15,min_dist=0.1"` (stessi nomi/valori delle colonne di `tuning_results.csv`) — si ricostruisce la chiave dai valori di una riga per recuperare il suo embedding, senza bisogno di un indice separato. Pensato per essere lo strato dati di un futuro plot interattivo (vedi `knowledge/dim_reduction_clustering/dim_reduction_tuning_guide.md`) che legge e basta, senza dover rifittare nulla.
- **`metadata.csv`** (stesso trigger, un solo file in cima alla cartella — non per foglia, stessi soggetti per tutto lo sweep): l'anagrafica arricchita, identica per schema a quella di produzione (`lesion_volume_voxels`/`lesion_side`/`nihss`). Serve perché i colori di `embeddings_grid_*.png` si calcolano al volo (join live col registro clinico, somma su `X`) — senza questo file, un plot futuro che legge solo `embeddings.npz` non avrebbe modo di sapere di chi è ogni punto o come colorarlo.

### I Diari di Bordo (Runs)
In cima a ciascun ramo (es. `results/lesion/dim_reduction/production/umap/` e `results/lesion/dim_reduction/tuning/umap/`) viene generato e alimentato in **append-only** un file:
- `production/<metodo>/runs.csv` per le esecuzioni di produzione.
- `tuning/<metodo>/runs_tuning.csv` per gli esperimenti di tuning.
Questa traccia storica evita la perdita della memoria sulle configurazioni sperimentate. Non sono da confondere con `docs/experiments/SESSIONS.md` (spostato da `data/SESSIONS.md` il 15-08-26), un documento scritto a mano dall'umano. Per una vista d'insieme di tutte le combinazioni già prodotte (senza aprire N `runs.csv` a mano), vedi `results/dim_reduction_strategies.csv`, generato da `scripts/build_dim_reduction_strategies_csv.py` — mai scritto a mano, va rigenerato dopo ogni run (`docs/dev/config.md`).
