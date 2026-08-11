# Guida al Clustering (Raggruppamento)

Questa guida illustra l'uso dello script `clustering.py`. L'obiettivo è analizzare una matrice matematica di pazienti e raggrupparli automaticamente in "cluster" in base alla similitudine delle lesioni.

- **Script**: `src/pipeline/clustering.py`
- **Configurazione**: `config/pipelines/clustering.json`

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione.
```bash
sbatch jobs/run_clustering.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`, lanciare direttamente da terminale:
```bash
python -m src.pipeline.clustering --config config/pipelines/clustering.json
```

---

## Cos'è il Clustering?

Mentre la *Dim Reduction* semplifica le informazioni, il **Clustering fa un passo interpretativo**. Analizza le "distanze matematiche" tra i pazienti e raggruppa i soggetti "vicini" assegnando loro un'etichetta (es. "Tipo 1"). 

> **Consiglio**: È preferibile lanciare il clustering sulla matrice **compressa** dopo la *Dim Reduction* (2-3 componenti) piuttosto che sulla matrice parcellizzata grezza.

---

## Modalità di Funzionamento

### 1. Modalità Fine-Tuning (`"fine_tuning": true`)
Utilizzata per trovare la configurazione ottimale. Calcola indici interni di compattezza per ogni combinazione di parametri in `config/registry/params_clustering.json`.

- **Metriche calcolate**: Silhouette score, Calinski-Harabasz, Davies-Bouldin.
- **Specifiche per metodo**: K-Means calcola anche `inertia`; GMM calcola `bic`/`aic`.
- **Grafici diagnostici**: Agglomerative genera un *dendrogramma*; Spectral genera un *eigengap plot*. HDBSCAN non ne ha uno dedicato.
- **Scelta manuale**: Il sistema non sceglie in automatico, spetta all'utente leggere `tuning_results.csv` e grafici.
- **Consensus/Stability (Opzionale per KMeans/GMM/Spectral)**: 
  Aggiungendo un blocco `"consensus"` in `params_clustering.json`, si possono misurare le stabilità:
  - `"rsc"`: Ripete sui dati con seed casuali diversi (misura la dipendenza dall'inizializzazione).
  - `"monti"`: Sottocampionamento casuale (misura la dipendenza dal campione).

### 2. Modalità Produzione (`"fine_tuning": false`)
Genera i cluster definitivi usando i parametri precedentemente scelti in `config/registry/params_clustering.json`.

---

## Dettaglio Parametri JSON (`clustering.json`)

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`project`** | *Stringa* | Nome del progetto (es. `"clinical_connectome"`). |
| **`input_path`** | *Stringa* | Percorso della matrice di input. Dati grezzi (`data/derived/...`) o compressi (`results/lesion/dim_reduction/...`). DEVE esistere. |
| **`clustering_methods`** | *Lista* | Algoritmi da usare. Opzioni: `"kmeans"`, `"agglomerative"`, `"gmm"`, `"hdbscan"`, `"spectral"`. È possibile metterne multipli per confrontarli. |
| **`params_file`** | *Stringa* | File configurazione interna algoritmi (di norma `"config/registry/params_clustering.json"`). |
| **`output_root`** | *Stringa* | Cartella radice per i risultati (es. `"results/lesion/clustering"`). |
| **`session_name`** | *Stringa* | Nome esecuzione (es. `"test_gruppi_1"`). |
| **`overwrite`** | *Booleano* | Se `true`, sovrascrive esecuzioni precedenti con lo stesso nome. |
| **`fine_tuning`** | *Booleano* | `true` per tuning, `false` per produzione. |
| **`run_notes`** | *Stringa* | Note libere sull'esecuzione. |

> **Nota su `params_clustering.json`**: Per la maggior parte dei metodi, bisogna specificare in questo file il numero di cluster voluti (es. `"n_clusters": 4`) prima di avviare l'esecuzione in produzione.

---

## Output e Grafici

A seconda della modalità, vengono generati risultati diversi.

### Se in "Produzione" (per ogni metodo, es. in `kmeans/` o `hdbscan/`)
1. **`matrix.npy`**: Copia della matrice di partenza.
2. **`metadata.csv`**: File arricchito con la colonna **`cluster_label`**.
3. **`cluster_plot.png` & `.html`**: Grafico 2D (prime 2 colonne) colorato per cluster. La versione HTML è interattiva.
4. **`silhouette_plot.png`**: Grafico di qualità del clustering paziente per paziente.
5. **Cartella `comparison/`**: (Solo se si usano più metodi) Affianca i risultati visivi degli algoritmi scelti (es. `cluster_plot_comparison.png`), utilissimo per decidere quale metodo "taglia" meglio i dati.

### Se in "Fine-Tuning" (nella cartella `tuning/`)
1. **`tuning_results.csv`**: Risultati numerici dello sweep parametri.
2. **`tuning_plot.png`**: Sottografici per metrica calcolata.
3. Grafici diagnostici aggiuntivi (se supportati, es. dendrogramma).
*(Non vengono salvati `matrix.npy` o grafici di assegnazione).*

### Diari di Bordo
Ogni metodo mantiene uno storico delle esecuzioni mai sovrascritto:
- `runs.csv` per Produzione.
- `runs_tuning.csv` per Fine-Tuning.
