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

Il fine-tuning è supportato per `umap` (`n_neighbors`/`metric`), `pca`/`pca_varimax` (`n_components`), `pacmap` (`n_neighbors`) e `tsne` (`perplexity`/`metric`, stesso meccanismo di `umap`) — gli altri parametri di t-SNE (`early_exaggeration`, `learning_rate`, `max_iter`) restano fissati da Thiebaut de Schotten et al. 2020 e non entrano nella sweep (vedi `docs/methods/dimensionality_reduction.md`).

### 2. Modalità Produzione (`"fine_tuning": false`)
Una volta scelti i parametri ottimali grazie alla modalità precedente (e avendoli salvati nel file dei parametri), lanci lo script in questa modalità. Lo script prenderà le impostazioni e produrrà la matrice compressa finale da passare ai passaggi successivi.

---

## Dettaglio dei Parametri JSON

Ecco la spiegazione di `config/pipelines/dim_reduction.json`:

- **`project`**: `(Stringa)` Il nome del progetto (es. `"clinical_connectome"`).
- **`input_path`**: `(Stringa)` La cartella esatta della matrice di partenza che vuoi comprimere. Questa cartella DEVE esistere ed essere un output di `build_lesion_matrix.py` (es. `"data/derived/lesion_matrix/21-07_s1.1"`).
- **`reduction_method`**: `(Stringa)` Il nome della formula matematica da usare. Valori possibili:
  - `"umap"`: Metodo moderno topologico. Ottimo per conservare sia distanze globali che locali.
  - `"tsne"`: Metodo classico. Ottimo per fare bei grafici, ma storicamente inaffidabile per il calcolo di vere distanze cliniche.
  - `"pca"`: L'Analisi delle Componenti Principali, pura e lineare.
  - `"pca_varimax"`: PCA seguita da una rotazione Varimax, usata per massimizzare la separazione ortogonale delle lesioni (metodo *Thiebaut de Schotten*).
  - `"pacmap"`: L'algoritmo Pairwise Controlled Manifold Approximation.
- **`params_file`**: `(Stringa)` Il percorso al file di registro che custodisce la matematica pura. Di base lasciate `"config/registry/params_reduction.json"`. *(Vedi sezione sotto)*.
- **`output_root`**: `(Stringa)` Dove vuoi che la pipeline crei la cartella con i risultati (`"results/lesion/dim_reduction"` — il primo segmento dopo `results/` indica la modalità dato, `lesion`/`fc`/`sdc`).
- **`session_name`**: `(Stringa)` Il nome dell'esperimento (es. `"umap_test_1"`). Se stai facendo Fine-Tuning chiamalo magari `"tune1"`.
- **`overwrite`**: `(Booleano)` A `true` permette allo script di sovrascrivere silenziosamente un file preesistente.
- **`fine_tuning`**: `(Booleano)` Attiva (`true`) o disattiva (`false`) la modalità di ricerca dei parametri di cui abbiamo parlato sopra.
- **`regress_out_volume`**: `(Booleano)` In modalità Produzione. A `true`, prima di salvare l'embedding, rimuove per regressione lineare l'effetto del volume lesionale (numero di voxel lesionati per soggetto) da ciascuna coordinata dell'embedding — utile perché su dati binari lesionali il volume può dominare la struttura trovata (visto con la PCA, dove una componente correlava r=0.92 col volume). **Incompatibile con `metric: "jaccard"`/`"dice"` in `params_reduction.json`**: quelle metriche già normalizzano per il volume di ciascun soggetto, quindi regredirlo di nuovo toglierebbe segnale topografico reale, non un confondimento — la pipeline si ferma con un errore esplicito se provi a combinare le due cose. Vedi `docs/methods/dimensionality_reduction.md` per il dettaglio metodologico.
  - **Sweepabile anche in Fine-Tuning** (umap/tsne): se `"regress_out_volume": [false, true]` è nel `tuning_grid` di `params_reduction.json`, ogni combinazione viene valutata con/senza regressione. Le combinazioni impossibili (`regress_out_volume: true` insieme a `metric: "jaccard"/"dice"`) non vengono calcolate — quella riga in `tuning_results.csv` ha il punteggio vuoto e una colonna `skipped_reason` che spiega perché, il resto della griglia continua normalmente. **Nota**: il Fine-Tuning genera un grafico (`tuning_plot.png`) solo quando sweepi **un unico parametro** — con 2 o più (es. `n_neighbors`/`perplexity` × `metric`, o × `regress_out_volume`) niente grafico, solo `tuning_results.csv` (le heatmap sono state rimosse su richiesta).
- **`run_notes`**: `(Stringa)` Note per descrivere storicamente perché stai lanciando questo test (es. "Provo UMAP a 10 componenti").

### Come funziona il file `params_reduction.json`?
Se apri `"config/registry/params_reduction.json"`, vedrai che per ogni algoritmo c'è un blocco `"params"` (usato in Produzione) e un blocco `"tuning_grid"` (usato nel Fine-Tuning).
Quando in modalità Fine-Tuning scopri che `n_neighbors: 30` è perfetto per te, apri questo file e alla voce `"params"` di UMAP sostituisci il valore attuale con `30`.

---

## Output e File Log Storici

Tutti i risultati, per ogni metodo, finiranno separati in `results/lesion/dim_reduction/<metodo>/<GIORNO-MESE>_<session_name>` (il nome cartella include anche un tag auto-generato dal parametro chiave del metodo, es. `21-07_s1.1_d01` per UMAP con `min_dist=0.1` — vedi `config/registry/params_reduction.json`).

- Se eri in **Fine-Tuning**: Troverai `tuning_results.csv` e `tuning_plot.png`. Niente matrice.
- Se eri in **Produzione**: Troverai `matrix.npy` (questa volta non avrà 800.000 colonne, ma magari solo 2), un `config.md` di riepilogo e il `metadata.csv` (che stavolta guadagna 2 colonne rispetto alla matrice originale: `lesion_volume_voxels`, il conteggio voxel della lesione di ogni soggetto, e `lesion_side`, il lato della lesione — `"unknown"` per un soggetto/dataset per cui non è risolvibile, es. PASPORT che non ha quella colonna). Se l'embedding ha almeno 2 componenti troverai 4 plot statici + 3 interattivi:
  - `embedding_plot.png` — puntini anonimi, un solo colore.
  - `embedding_plot_dataset.png`/`.html` — colorato per `dataset`.
  - `embedding_plot_volume.png`/`.html` — colorato per `lesion_volume_voxels` (colormap continua + colorbar).
  - `embedding_plot_side.png`/`.html` — colorato per `lesion_side` (categoria `"unknown"` per i soggetti senza lato risolvibile).

  Ogni file `.html` è interattivo (apribile in un browser), passando sopra un punto mostra tutte le colonne di `metadata.csv` (`subject_id`/`dataset`/`lesion_volume_voxels`/`lesion_side`) di quel soggetto. Per rigenerare tutti e 7 i plot da una run già esistente senza ricalcolare l'embedding: `scripts/replot_dim_reduction.py --run-dir <cartella_run>`.

**Molto Importante: Il file runs.csv**
Nella cartella base di ogni metodo (es. `results/lesion/dim_reduction/umap/runs.csv`), lo script compilerà un vero e proprio "Diario di Bordo" automatico, stavolta in formato CSV (una riga per run: `run_id, timestamp, run_type, params, output, notes`). Ogni volta che lanci la pipeline con successo, aggiungerà una riga con l'ora, se era un test di fine tuning o una produzione, quali parametri matematici esatti hai usato e le note che avevi scritto. In questo modo avrai una traccia storica scientifica di ogni singola prova fatta nei mesi, interrogabile con pandas, e non rischierai mai di scordarti con quali impostazioni avevi ottenuto un certo grafico.

**`SESSIONS.md` è un'altra cosa**: descrive cosa *significa* un numero di sessione (es. `s1.1`) — dataset usati, modalità, cosa è cambiato — scritto a mano da te, non generato dallo script. Vive in `data/SESSIONS.md` (canonico) con una copia/symlink in `results/SESSIONS.md`.
