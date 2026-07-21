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
- **`reduction_method`**: `(Stringa)` Seleziona UN SOLO algoritmo di compressione (es. `"umap"` oppure `"pca_varimax"`). È lo scultore che modellerà l'argilla per i clustering successivi.
- **`clustering_methods`**: `(Lista di Stringhe)` Seleziona I METODI di raggruppamento con cui vuoi tagliare i dati (es. `["kmeans", "agglomerative", "gmm"]`). Verranno eseguiti tutti, a ruota.
- **`reduction_params_file`**: `(Stringa)` Punta al registro matematico della riduzione (`"config/registry/params_reduction.json"`). 
- **`clustering_params_file`**: `(Stringa)` Punta al registro matematico dei raggruppamenti (`"config/registry/params_clustering.json"`).
- **`output_root`**: `(Stringa)` Sede finale dei risultati combinati (`"results/lesion/dim_reduction_clustering"` — il primo segmento dopo `results/` indica la modalità dato, `lesion`/`fc`/`sdc`; questa pipeline ha un ramo terzo dedicato, separato sia da `dim_reduction/` che da `clustering/`).
- **`session_name`**: `(Stringa)` Il nome dell'operazione massiva (es. `"run_1"`).
- **`overwrite`**: `(Booleano)` A `true` per sovrascrivere.
- **`run_notes`**: `(Stringa)` Spazio libero per note su perché stai facendo il run.

### Note sul Funzionamento Interno

- **Niente Fine-Tuning**: Questa pipeline è pensata per "calcolare", non per sperimentare. Non troverai qui il parametro `fine_tuning`. Presume che tu abbia già scelto i parametri ottimali per UMAP/PCA e K-Means nei rispettivi file `json` (tramite l'apposita guida al *Dim Reduction*). Prenderà quei parametri come "assoluti" ed eseguirà il lavoro finale.

---

## Output Finale

Immagina di lanciare la pipeline scegliendo `reduction_method: "umap"` e `clustering_methods: ["kmeans", "gmm"]`.
All'interno di `results/lesion/dim_reduction_clustering/` avverrà la seguente organizzazione:

Verranno create due cartelle basate sulla combinazione nominale dei due passaggi:
1. `umap-kmeans/`
2. `umap-gmm/`

Cosa troverai dentro ciascuna?
- `matrix.npy`: I dati compressi (es. una matrice con le sole 2 coordinate finali generate da UMAP).
- `metadata.csv`: Il file d'anagrafica con le colonne aggiornate (ora avrai l'ID del paziente e accanto la dicitura es. Cluster 3).
- Un file `config.md` di riepilogo estremamente minuzioso.
- Il file cumulativo del diario di bordo `RUNS.md`.
- `cluster_plot.png`: Un meraviglioso grafico in due dimensioni con tutti i pazienti a puntini. Gli assi geometrici saranno quelli ricavati da UMAP, e i colori (il rosso per il Gruppo 0, il verde per il Gruppo 1) deriveranno in questa cartella da K-Means e nell'altra da GMM.
- `cluster_plot_interactive.html`: la stessa vista, ma interattiva (apribile in un browser) — passando sopra un punto vedi `subject_id`/`dataset`/gruppo del paziente, e un menu a tendina permette di ricolorare al volo i punti per `dataset` invece che per cluster, per controllare se un raggruppamento riflette un effetto sito piuttosto che una vera struttura clinica.

Infine, come per il modulo di clustering classico, ti regalerà in automatico la super cartella speciale `comparison/` in cui stamperà tutti i grafici di K-Means e di GMM uno a fianco all'altro. Siccome lo spazio generato da UMAP sotto è lo stesso, le posizioni dei puntini saranno le stesse, e potrai focalizzarti unicamente sul confrontare come i due diversi algoritmi di clustering si sono "litigati" i colori con cui colorarli.
