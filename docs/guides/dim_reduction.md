# Guida alla Riduzione della Dimensionalità (Dim Reduction)

Questa guida descrive come utilizzare la pipeline `dim_reduction.py`. Il suo scopo è prendere una matrice di lesioni molto complessa e comprimerla, estraendo solo le "caratteristiche matematiche salienti". Questo passaggio è spesso essenziale per poter visualizzare i dati su un grafico a dispersione o prima di lanciare gli algoritmi di raggruppamento (clustering).

**Script**: `src/pipeline/dim_reduction.py`
**Configurazione**: `config/pipelines/dim_reduction.json`

## Esecuzione (Locale vs Server/SLURM)

**1. Esecuzione sul Server (con SLURM)**
Sul server, lancia lo script inviandolo alla coda tramite SLURM (così non si interrompe se chiudi la connessione). Trovi lo script in `jobs/`:
```bash
sbatch jobs/run_dim_reduction.sh
```

**2. Esecuzione in Locale (senza SLURM)**
Dal tuo PC locale, dopo aver attivato l'ambiente `nemesis`, lancia la pipeline direttamente da terminale:
```bash
python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json
```
## Il concetto: cosa significa "Riduzione della Dimensionalità"?

Immagina di avere una matrice *Voxel-wise* generata nel passaggio di *Matrix Building*: ogni paziente è definito da 800.000 numeri (uno per voxel). Non puoi disegnare un grafico con 800.000 assi. Gli algoritmi di Riduzione della Dimensionalità sono equazioni avanzate che "guardano" questi 800.000 numeri e trovano i modelli intrinseci, riassumendo tutto il paziente in 2, 3 o 10 coordinate (componenti principali o embedding).

Se chiedi all'algoritmo di estrarre "2 componenti", potrai usare queste due coordinate per posizionare il paziente su un piano cartesiano (Asse X e Asse Y). Pazienti con lesioni clinicamente simili si troveranno vicini sul grafico.

---

## Le Due Modalità di Funzionamento: Produzione e Fine-Tuning

Questo script è molto potente e possiede due modalità, controllate dal parametro `"fine_tuning"`.

### 1. Modalità Fine-Tuning (`"fine_tuning": true`)
Questi algoritmi matematici necessitano spesso di essere "tarati". Ad esempio, per l'algoritmo UMAP c'è un parametro chiamato `n_neighbors` (quanto l'algoritmo si deve concentrare sulla struttura locale vs globale). **Non esiste un valore giusto a priori, dipende dai tuoi dati.**
Attivando questa modalità, lo script **non** calcolerà il risultato finale, ma avvierà decine di esperimenti automatici provando tutte le combinazioni di parametri possibili.
Alla fine ti fornirà un file Excel (CSV) e dei grafici colorati a mappa di calore (Heatmap) mostrandoti quale combinazione matematica di parametri ottiene il punteggio di "bontà del dato" (Trustworthiness) più alto.
Spetta a te umano analizzare il grafico e scegliere il set di parametri vincenti.

### 2. Modalità Produzione (`"fine_tuning": false`)
Una volta scelti i parametri ottimali grazie alla modalità precedente (e avendoli salvati nel file dei parametri), lanci lo script in questa modalità. Lo script prenderà le impostazioni e produrrà la matrice compressa finale da passare ai passaggi successivi.

---

## Dettaglio dei Parametri JSON

Ecco la spiegazione di `config/pipelines/dim_reduction.json`:

- **`project`**: `(Stringa)` Il nome del progetto (es. `"clinical_connectome"`).
- **`input_path`**: `(Stringa)` La cartella esatta della matrice di partenza che vuoi comprimere. Questa cartella DEVE esistere ed essere un output di `build_lesion_matrix.py` (es. `"data/derived/lesion_matrix/20-07_run1"`).
- **`reduction_method`**: `(Stringa)` Il nome della formula matematica da usare. Valori possibili:
  - `"umap"`: Metodo moderno topologico. Ottimo per conservare sia distanze globali che locali.
  - `"tsne"`: Metodo classico. Ottimo per fare bei grafici, ma storicamente inaffidabile per il calcolo di vere distanze cliniche.
  - `"pca"`: L'Analisi delle Componenti Principali, pura e lineare.
  - `"pca_varimax"`: PCA seguita da una rotazione Varimax, usata per massimizzare la separazione ortogonale delle lesioni (metodo *Thiebaut de Schotten*).
  - `"pacmap"`: L'algoritmo Pairwise Controlled Manifold Approximation.
- **`params_file`**: `(Stringa)` Il percorso al file di registro che custodisce la matematica pura. Di base lasciate `"config/registry/params_reduction.json"`. *(Vedi sezione sotto)*.
- **`output_root`**: `(Stringa)` Dove vuoi che la pipeline crei la cartella con i risultati (`"results/dim_reduction"`).
- **`run_name`**: `(Stringa)` Il nome dell'esperimento (es. `"umap_test_1"`). Se stai facendo Fine-Tuning chiamalo magari `"tune1"`.
- **`overwrite`**: `(Booleano)` A `true` permette allo script di sovrascrivere silenziosamente un file preesistente.
- **`fine_tuning`**: `(Booleano)` Attiva (`true`) o disattiva (`false`) la modalità di ricerca dei parametri di cui abbiamo parlato sopra.
- **`run_notes`**: `(Stringa)` Note per descrivere storicamente perché stai lanciando questo test (es. "Provo UMAP a 10 componenti").

### Come funziona il file `params_reduction.json`?
Se apri `"config/registry/params_reduction.json"`, vedrai che per ogni algoritmo c'è un blocco `"params"` (usato in Produzione) e un blocco `"tuning_grid"` (usato nel Fine-Tuning).
Quando in modalità Fine-Tuning scopri che `n_neighbors: 30` è perfetto per te, apri questo file e alla voce `"params"` di UMAP sostituisci il valore attuale con `30`.

---

## Output e File Log Storici

Tutti i risultati, per ogni metodo, finiranno separati in `results/dim_reduction/<metodo>/<GIORNO-MESE>_<run_name>`.

- Se eri in **Fine-Tuning**: Troverai `tuning_results.csv` e `tuning_plot.png`. Niente matrice.
- Se eri in **Produzione**: Troverai `matrix.npy` (questa volta non avrà 800.000 colonne, ma magari solo 2), un `README.md` di riepilogo e il `metadata.csv` (che copia i dati dei pazienti dalla matrice originale senza alterarli).

**Molto Importante: Il file RUNS.md**
Nella cartella base di ogni metodo (es. `results/dim_reduction/umap/RUNS.md`), lo script compilerà un vero e proprio "Diario di Bordo" automatico. Ogni volta che lanci la pipeline con successo, scriverà nel diario l'ora, se era un test di fine tuning o una produzione, quali parametri matematici esatti hai usato e le note che avevi scritto. In questo modo avrai una traccia storica scientifica di ogni singola prova fatta nei mesi, e non rischierai mai di scordarti con quali impostazioni avevi ottenuto un certo grafico.
