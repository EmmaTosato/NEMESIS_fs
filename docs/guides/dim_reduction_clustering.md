# Guida alla Riduzione + Clustering (`dim_reduction_clustering`)

Questa guida tratta un singolo script, ma probabilmente il più utilizzato nell'intero progetto NEMESIS: `dim_reduction_clustering.py`. 

**Script**: `src/pipeline/dim_reduction_clustering.py`
**Configurazione**: `config/pipelines/dim_reduction_clustering.json`

## Esecuzione (Locale vs Server/SLURM)

**1. Esecuzione sul Server (con SLURM)**
Sul server, lancia lo script inviandolo alla coda tramite SLURM (così non si interrompe se chiudi la connessione). Trovi lo script in `jobs/`:
```bash
sbatch jobs/run_dim_reduction_clustering.sh
```

**2. Esecuzione in Locale (senza SLURM)**
Dal tuo PC locale, dopo aver attivato l'ambiente `nemesis`, lancia la pipeline direttamente da terminale:
```bash
python -m src.pipeline.dim_reduction_clustering --config config/pipelines/dim_reduction_clustering.json
```
## Il concetto: La "Scorciatoia" d'Eccellenza

Di norma, il workflow standard prevede due passaggi consecutivi e laboriosi: prendere la matrice grezza e comprimerla (*Dim Reduction*), segnarsi la cartella di output, aprire il file del *Clustering*, e far puntare il parametro a quella cartella per dividere i dati in gruppi.

Lo script `dim_reduction_clustering` fa tutto questo con un solo colpo di pistola. È il modulo principe di "Produzione". Prende i dati grezzi, comprime lo spazio geometrico seguendo le regole di *un singolo algoritmo* di riduzione, e poi lancia su questo spazio compresso *una batteria di molteplici algoritmi* di clustering.

---

## Dettaglio dei Parametri JSON

I parametri nel file `config/pipelines/dim_reduction_clustering.json` sono essenzialmente la fusione esatta delle impostazioni delle guide precedenti.

- **`project`**: `(Stringa)` `"clinical_connectome"`.
- **`input_path`**: `(Stringa)` La cartella esatta originata dalla pipeline base di *Matrix Building* (es. `"data/derived/lesion_matrix/21-07_s1.1"`). Non dargli in pasto dati già compressi, ci penserà lui.
- **`reduction_method`**: `(Stringa)` Seleziona UN SOLO algoritmo di compressione (es. `"umap"` oppure `"pca_varimax"` — quest'ultimo però non selezionabile oggi: `config/registry/params_reduction.json` non ha più una voce `"pca_varimax"`, vedi `docs/guides/dim_reduction.md`). È lo scultore che modellerà l'argilla per i clustering successivi.
- **`clustering_methods`**: `(Lista di Stringhe)` Seleziona I METODI di raggruppamento con cui vuoi tagliare i dati (es. `["kmeans", "agglomerative", "gmm"]`). Verranno eseguiti tutti, a ruota.
- **`reduction_params_file`**: `(Stringa)` Punta al registro matematico della riduzione (`"config/registry/params_reduction.json"`). 
- **`clustering_params_file`**: `(Stringa)` Punta al registro matematico dei raggruppamenti (`"config/registry/params_clustering.json"`).
- **`output_root`**: `(Stringa)` Sede finale dei risultati combinati (`"results/lesion/dim_reduction_clustering"` — il primo segmento dopo `results/` indica la modalità dato, `lesion`/`fc`/`sdc`; questa pipeline ha un ramo terzo dedicato, separato sia da `dim_reduction/` che da `clustering/`).
- **`session_name`**: `(Stringa)` Il nome dell'operazione massiva (es. `"run_1"`).
- **`overwrite`**: `(Booleano)` A `true` per sovrascrivere.
- **`fine_tuning`**: `(Booleano)` A `false` (default) esegue il clustering di produzione descritto sopra. A `true` passa in modalità tuning — vedi sotto.
- **`regress_out_volume`**: `(Booleano)` Come nella guida al *Dim Reduction*: rimuove per regressione lineare l'effetto del volume lesionale dall'embedding (calcolato una volta sola, prima del clustering) prima di clusterizzarlo. Incompatibile con `metric: "jaccard"`/`"dice"` in `reduction_params_file` (errore esplicito se combinati) — vedi `docs/methods/dimensionality_reduction.md`.
- **`viz_n_components`**: `(Intero, dev'essere `2` qui)` Dimensione dell'embedding usato **solo per i plot** (`cluster_plot.png`, `cluster_plot_interactive.html`, `silhouette_plot.png`, i plot di comparazione) — indipendente da `n_components` in `reduction_params_file`, che è quello davvero usato per clusterizzare. Se coincidono (caso di oggi, `n_components: 2` ovunque), l'embedding di plotting è lo stesso già calcolato, zero costo aggiuntivo; se `n_components` è più alto, viene rifittato un embedding separato solo a 2 dimensioni per i plot (stesso principio di `dim_reduction.py`, vedi quella guida) — mai un taglio arbitrario delle prime 2 colonne di un embedding a più dimensioni. A differenza di `dim_reduction.py`, qui **non è ammesso `3`**: tutti i plot di questa pipeline (colorati per cluster) sono statici 2D, non hanno una versione interattiva 3D.
- **`color_by`**: `(Lista di stringhe, può essere vuota)` Funzionalità **opzionale**, di scopo diverso dai plot di cluster: se non vuota, scrive *in aggiunta* una cartella `<reduction_method>/embedding/<dd-mm>_<session_name>/` con gli stessi plot "colora per dataset/volume/side/nihss" di `dim_reduction.py` (stesso registro, `src/analysis/embedding_coloring.py`), calcolati sull'embedding di visualizzazione. Lista vuota (default) = nessun output aggiuntivo, comportamento identico a prima che questo campo esistesse. **Indipendente** dall'arricchimento di `metadata.csv` sotto — quello è sempre attivo, `color_by` decide solo se vengono generati anche i plot dedicati.
- **`run_notes`**: `(Stringa)` Spazio libero per note su perché stai facendo il run.

### Note sul Funzionamento Interno

- **`metadata.csv` guadagna sempre 3 colonne prima di `cluster_label`** (non solo se richiesto in `color_by`): `lesion_volume_voxels`, `lesion_side`, `nihss` — stesso arricchimento, stessa funzione condivisa (`src/features/clinical.py::enrich_metadata_with_lesion_info`) usata da `dim_reduction.py`, così un risultato di questa pipeline ha sempre le stesse colonne di un risultato dell'altra, indipendentemente da quale hai lanciato. Vale solo in modalità produzione (`fine_tuning: false`) — la modalità tuning non scrive `metadata.csv`.
- **La riduzione non si tara mai qui**: qualunque sia `fine_tuning`, la riduzione dimensionale gira sempre una volta sola, con i parametri "assoluti" già scelti in `reduction_params_file` (mai il suo `tuning_grid`). Se devi ancora scegliere quei parametri, usa prima la guida al *Dim Reduction*.
- **`fine_tuning: true`** riguarda solo il clustering: invece di clusterizzare l'embedding con i parametri finali, per ogni metodo in `clustering_methods` prova tutta la griglia dichiarata nel `tuning_grid` di quel metodo (`config/registry/params_clustering.json`) — è la scorciatoia per tarare il clustering su un embedding specifico senza doverlo prima salvare su disco con `dim_reduction.py` e poi ripuntarci `clustering.py --fine_tuning`. Stesse metriche/diagnosi della guida al *Clustering* (silhouette, Calinski-Harabasz, Davies-Bouldin, + `inertia`/`bic`/`aic`/dendrogramma/eigengap a seconda del metodo). **Niente grafico di comparazione** in questa modalità, nemmeno con più metodi richiesti — uno sweep non produce un'unica assegnazione di cluster da confrontare.

---

## Output Finale

Immagina di lanciare la pipeline scegliendo `reduction_method: "umap"` e `clustering_methods: ["kmeans", "gmm"]`.
All'interno di `results/lesion/dim_reduction_clustering/` avverrà la seguente organizzazione, annidata per riduzione e poi per clustering (stessa logica di `results/lesion/dim_reduction/`):

```
results/lesion/dim_reduction_clustering/
└── umap/
    ├── kmeans/
    │   └── <dd-mm>_<session_name>_<reduction_tag>_<clustering_tag>/
    ├── gmm/
    │   └── <dd-mm>_<session_name>_<reduction_tag>_<clustering_tag>/
    ├── runs.csv
    └── comparison/
        └── umap_<dd-mm>_<session_name>_<reduction_tag>/
```

Cosa troverai dentro ciascuna cartella `umap/kmeans/...`/`umap/gmm/...`?
- `matrix.npy`: I dati compressi (es. una matrice con le sole 2 coordinate finali generate da UMAP).
- `metadata.csv`: Il file d'anagrafica con le colonne aggiornate — `subject_id`, `dataset`, `lesion_volume_voxels`, `lesion_side`, `nihss` (sempre, vedi sopra) e infine `cluster_label` (l'ID del paziente e accanto la dicitura es. Cluster 3).
- Un file `config.md` di riepilogo estremamente minuzioso.
- `cluster_plot.png`: Un meraviglioso grafico in due dimensioni con tutti i pazienti a puntini. Gli assi geometrici saranno quelli ricavati da UMAP, e i colori (il rosso per il Gruppo 0, il verde per il Gruppo 1) deriveranno in questa cartella da K-Means e nell'altra da GMM.
- `cluster_plot_interactive.html`: la stessa vista, ma interattiva (apribile in un browser) — passando sopra un punto vedi `subject_id`/`dataset`/gruppo del paziente. Colorato solo per cluster (niente più il menu a tendina per ricolorare per `dataset` di una versione precedente — quel confronto vive ora in `results/lesion/dim_reduction/<metodo>/.../embedding_plot_dataset.*`, vedi `docs/guides/dim_reduction.md`).
- `silhouette_plot.png`: il classico grafico a due pannelli per giudicare la qualità del clustering paziente per paziente, non solo con un numero medio. A sinistra una "banda" orizzontale per ogni gruppo, larga quanto il coefficiente di silhouette di ciascun paziente (banda larga e uniforme = gruppo ben separato; se scende sotto zero, quei pazienti sono più vicini a un altro gruppo), con una linea tratteggiata sulla media (la stessa "silhouette" riportata nel tuning). A destra lo stesso scatter di `cluster_plot.png`, per confronto immediato. Se il risultato è degenere (es. un solo gruppo), il file non viene creato e nel log compare un warning invece di un errore.

Il diario di bordo `runs.csv` (`reduction_method, clustering_method, session, id, timestamp, params, output, notes`) vive invece **a livello della riduzione**, non per ogni sottocartella di clustering: un solo `umap/runs.csv` raccoglie tutte le righe di K-Means, GMM e qualunque altro metodo lanciato su quella stessa riduzione, distinte dalle due colonne iniziali `reduction_method`/`clustering_method`.

Infine, come per il modulo di clustering classico, ti regalerà in automatico la super cartella speciale `umap/comparison/` in cui stamperà tutti i grafici di K-Means e di GMM uno a fianco all'altro (`cluster_comparison.png`). Siccome lo spazio generato da UMAP sotto è lo stesso, le posizioni dei puntini saranno le stesse, e potrai focalizzarti unicamente sul confrontare come i due diversi algoritmi di clustering si sono "litigati" i colori con cui colorarli. C'è anche una versione interattiva, `cluster_comparison_interactive.html`: stesso layout 2D, con un menu a tendina per far ricolorare i punti secondo l'assegnazione di ciascun metodo, uno alla volta, senza dover aprire N file separati. La cartella stessa porta il nome della riduzione prima del tag (`umap_<dd-mm>_...`) — l'unico posto in cui questo si ripete esplicitamente nel nome, dato che altrove è già implicito nella posizione nell'albero.

**Se invece eri in Fine-Tuning** (`"fine_tuning": true`): niente `matrix.npy`/`cluster_plot.png`/comparison — per ogni metodo trovi `results/lesion/dim_reduction_clustering/umap/<metodo>/tuning/<dd-mm>_<session_name>/` con `tuning_results.csv` + `tuning_plot.png`, più il grafico diagnostico specifico del metodo quando previsto (`dendrogram.png` per Agglomerative, `eigengap_plot.png` per Spectral — HDBSCAN non ne ha uno, vedi `docs/guides/clustering.md`). Le righe di tuning vanno in un file separato, `umap/runs_tuning.csv` (non `runs.csv`, riservato alla produzione).
