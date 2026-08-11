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

- **Parametri Nested (`nested_params`)**: Con molteplici parametri (es. UMAP ha metric, regress, neighbors...), la visualizzazione esploderebbe. Il registry permette di specificare `nested_params`. I parametri primari (es. la metrica) generano sottocartelle, e il grid visuale (`embeddings_grid_unico.png`) viene mostrato solo sulle 1 o 2 variabili libere rimanenti.

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
| **`regress_out_volume`**| *Booleano* | Rimuove linearmente l'effetto volume lesionale. **Incompatibile** con metriche `jaccard` o `dice`. |
| **`viz_n_components`** | *Intero (2 o 3)* | Dimensioni fisse del plot grafico, anche se la compressione vera è a più dimensioni. Evita distorsioni di "taglio". A `3`, fornisce solo l'HTML interattivo ruotabile. |
| **`color_by`** | *Lista* | Genera plot colorati per specifici tag: `"dataset"`, `"side"`, `"volume"`, `"nihss"`. |
| **`write_embeddings_grid`** | *Booleano* | Se `false`, disattiva manualmente `embeddings_grid_*.png` in modalità Fine-Tuning (resta comunque scritto `tuning_results.csv`). |
| **`save_tuning_embeddings`** | *Booleano* | Se `true`, salva in `embeddings.npz` l'embedding effettivo di **ogni** combinazione valutata nel Fine-Tuning (non solo quelle mostrate in `embeddings_grid_*.png`) — vedi sotto. Opt-in, `false` di default: nessuna run precedente all'introduzione di questo campo ha mai scritto questo file. |

---

## Output e Diari Storici

**Dal 2026-08, i risultati di produzione e di tuning vivono in due rami separati sotto `output_root`, mai mescolati**: `results/lesion/dim_reduction/production/<metodo>/<Data>_<session_name>_<tag>` e `results/lesion/dim_reduction/tuning/<metodo>/<Data>_<session_name>`. Prima di questa data `tuning/` viveva dentro la cartella del metodo (`<metodo>/tuning/...`) — se stai guardando risultati più vecchi di questa data, tienilo a mente.

### In Modalità Produzione
- **`matrix.npy`**: La nuova matrice compressa.
- **`metadata.csv`**: L'anagrafica arricchita in automatico di `lesion_volume_voxels`, `lesion_side`, e `nihss`.
- **Plot Grafici**: Un `embedding_plot_unico.png` base, più una coppia PNG/HTML per ogni voce elencata in `color_by`. I file HTML sono interattivi.

### In Modalità Fine-Tuning
- **`tuning_results.csv`**: I punteggi matematici estratti per ogni esperimento.
- **`tuning_plot.png`** e **`embeddings_grid_*.png`**: I plot per visualizzare come cambia la compressione al variare dei parametri, organizzati per sottocartelle se si usa la struttura *nested*.
- **`embeddings.npz`** (solo se `save_tuning_embeddings: true`): un unico file con l'embedding vero e proprio di ogni combinazione valutata, non solo quelle disegnate nei plot. Ogni array è indicizzato da una chiave leggibile tipo `"n_neighbors=15,min_dist=0.1"` (stessi nomi/valori delle colonne di `tuning_results.csv`) — si ricostruisce la chiave dai valori di una riga per recuperare il suo embedding, senza bisogno di un indice separato. Pensato per essere lo strato dati di un futuro plot interattivo (vedi `docs/knowledge/dim_reduction_tuning_guide.md`) che legge e basta, senza dover rifittare nulla.

### I Diari di Bordo (Runs)
In cima a ciascun ramo (es. `results/lesion/dim_reduction/production/umap/` e `results/lesion/dim_reduction/tuning/umap/`) viene generato e alimentato in **append-only** un file:
- `production/<metodo>/runs.csv` per le esecuzioni di produzione.
- `tuning/<metodo>/runs_tuning.csv` per gli esperimenti di tuning.
Questa traccia storica evita la perdita della memoria sulle configurazioni sperimentate. Non sono da confondere con `data/SESSIONS.md`, un documento scritto a mano dall'umano.
