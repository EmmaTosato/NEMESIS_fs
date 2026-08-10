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

Il fine-tuning è supportato per `umap` (`n_neighbors`/`min_dist`/`metric`/`n_components`/`regress_out_volume`), `pca`/`pca_varimax` (`n_components`), `pacmap` (`n_neighbors`) e `tsne` (`perplexity`/`metric`/`regress_out_volume`, stesso meccanismo di `umap`) — gli altri parametri di t-SNE (`early_exaggeration`, `learning_rate`, `max_iter`) restano fissati da Thiebaut de Schotten et al. 2020 e non entrano nella sweep (vedi `docs/methods/dimensionality_reduction.md`).

#### `nested_params`: parametri "decisi a priori" vs il vero grid search

Quando `tuning_grid` ha più di 2 parametri (es. UMAP: `metric`, `n_components`, `regress_out_volume`, `n_neighbors`, `min_dist`), non ha senso incrociarli tutti in un'unica tabella/grafico — alcuni sono decisioni teoriche/a-priori (che metrica usare, quante componenti servono a valle), altri sono il vero grid search da esplorare visivamente. `nested_params` (opzionale, in `params_reduction.json` per metodo) dichiara **quali** parametri fissare uno alla volta, in **che ordine** di annidamento cartelle:

```json
"umap": {
  "tuning_grid": {
    "metric": ["euclidean", "jaccard", "dice"],
    "n_components": [2, 5, 10],
    "regress_out_volume": [false, true],
    "n_neighbors": [5, 15, 30, 50, 100],
    "min_dist": [0.0, 0.1, 0.25]
  },
  "nested_params": ["metric", "n_components", "regress_out_volume"]
}
```

Quello che resta di `tuning_grid` dopo `nested_params` (qui `n_neighbors`/`min_dist`) dev'essere esattamente 1 o 2 chiavi — è il grid libero, quello davvero visualizzato. Per ogni combinazione **reale** dei parametri annidati (una combinazione con `regress_out_volume: true` + `metric: jaccard/dice` non esiste mai, è incompatibile per costruzione — vedi sotto) viene creata una sottocartella `metric=.../n_components=.../regress_out_volume=.../`, con dentro:
- `tuning_results.csv` — solo le righe di quella combinazione
- `embeddings_grid_unico.png` (+ una copia per ogni voce di `color_by`, vedi sotto) — non un numero, ma gli **embedding veri**: un blocco per ogni parametro libero (es. "n_neighbors", poi "min_dist"), ciascuno una riga di scatter, uno per valore, con l'altro parametro libero tenuto al valore di `params` — separati da spazio bianco, sottotitolo per blocco.

Se `nested_params` non è dichiarato (es. `pca`, `pacmap`, o qualunque metodo con al massimo 2 parametri in `tuning_grid`), il comportamento resta quello di sempre: un `tuning_plot.png` a curva se c'è un solo parametro sweepato, nessun grafico (solo CSV) se ce ne sono 2+.

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
  - `"pca_varimax"`: PCA seguita da una rotazione Varimax, usata per massimizzare la separazione ortogonale delle lesioni (metodo *Thiebaut de Schotten*). **Non selezionabile oggi**: `config/registry/params_reduction.json` non ha più una voce `"pca_varimax"` (rimossa in un riordino del file, mai reintrodotta) — il codice la implementa e la testa ancora, ma finché quella voce non torna nel registro, impostare `"reduction_method": "pca_varimax"` fa fallire la pipeline con un errore di metodo non registrato.
  - `"pacmap"`: L'algoritmo Pairwise Controlled Manifold Approximation.
- **`params_file`**: `(Stringa)` Il percorso al file di registro che custodisce la matematica pura. Di base lasciate `"config/registry/params_reduction.json"`. *(Vedi sezione sotto)*.
- **`output_root`**: `(Stringa)` Dove vuoi che la pipeline crei la cartella con i risultati (`"results/lesion/dim_reduction"` — il primo segmento dopo `results/` indica la modalità dato, `lesion`/`fc`/`sdc`).
- **`session_name`**: `(Stringa)` Il nome dell'esperimento (es. `"umap_test_1"`). Se stai facendo Fine-Tuning chiamalo magari `"tune1"`.
- **`overwrite`**: `(Booleano)` A `true` permette allo script di sovrascrivere silenziosamente un file preesistente.
- **`fine_tuning`**: `(Booleano)` Attiva (`true`) o disattiva (`false`) la modalità di ricerca dei parametri di cui abbiamo parlato sopra.
- **`regress_out_volume`**: `(Booleano)` In modalità Produzione. A `true`, prima di salvare l'embedding, rimuove per regressione lineare l'effetto del volume lesionale (numero di voxel lesionati per soggetto) da ciascuna coordinata dell'embedding — utile perché su dati binari lesionali il volume può dominare la struttura trovata (visto con la PCA, dove una componente correlava r=0.92 col volume). **Incompatibile con `metric: "jaccard"`/`"dice"` in `params_reduction.json`**: quelle metriche già normalizzano per il volume di ciascun soggetto, quindi regredirlo di nuovo toglierebbe segnale topografico reale, non un confondimento — la pipeline si ferma con un errore esplicito se provi a combinare le due cose. Vedi `docs/methods/dimensionality_reduction.md` per il dettaglio metodologico.
  - **Sweepabile anche in Fine-Tuning** (umap/tsne): se `"regress_out_volume": [false, true]` è nel `tuning_grid` di `params_reduction.json`, ogni combinazione viene valutata con/senza regressione. Le combinazioni impossibili (`regress_out_volume: true` insieme a `metric: "jaccard"/"dice"`) **non compaiono affatto** in `tuning_results.csv`, né generano una cartella `nested_params` — vengono escluse a monte (un WARNING viene comunque loggato durante il run).
- **`color_by`**: `(Lista di stringhe)` Quali modalità di colorazione generare per gli embedding, oltre a quella base "unico colore" (sempre generata, non va elencata). Valori riconosciuti oggi: `"dataset"`, `"side"` (lato della lesione), `"volume"` (voxel lesionati — **scala logaritmica**: la distribuzione del volume lesionale è molto asimmetrica, in lineare pochi outlier enormi schiacciano tutti gli altri punti sullo stesso colore scuro), `"nihss"` (punteggio di gravità NIHSS basale — continuo, scala lineare, `NaN` per un soggetto/dataset dove non è risolvibile, es. PASPORT che non ha una colonna `NIHSS` semplice; i punti mancanti sono disegnati in grigio neutro, esclusi dalla scala colore). `"volume"` e `"nihss"` condividono la stessa palette (`viridis`) — si distinguono per la scala (log vs lineare), non per il colore. Il registro è in `src/analysis/embedding_coloring.py`, estendibile aggiungendo una entry lì + il nome qui. Lista vuota `[]` = solo "unico colore". Usato sia in Produzione (`embedding_plot_<nome>.*`, anche l'HTML interattivo — ma lì la scala resta sempre lineare, plotly non ha un colore log nativo, l'hover mostra comunque il valore reale) sia in Fine-Tuning con `nested_params` (`embeddings_grid_<nome>.png`).
- **`viz_n_components`**: `(Intero, 2 o 3)` Quante componenti usare per **visualizzare** l'embedding — indipendente da quante ne usa realmente la riduzione/il clustering. Se coincide con `n_components` di `params`, viene riusato l'embedding già calcolato (costo zero, il caso di oggi con `n_components: 2` ovunque); se è diverso, viene rifittato un embedding **separato** solo per il plotting (stessi `metric`/`n_neighbors`/`min_dist`/`random_state`, vedi `src/analysis/reduction.py::embedding_for_viz`) — mai un taglio arbitrario delle prime 2/3 colonne di un embedding a più dimensioni (UMAP/t-SNE/PaCMAP non sono ordinati per varianza come la PCA, tagliare produce un disegno che può mostrare cluster falsamente sovrapposti o separati). Con `3`: solo il plot interattivo (`.html`, rotabile nel browser), nessun PNG statico 3D (poco leggibile senza poter ruotare).
- **`write_embeddings_grid`**: `(Booleano)` Solo in Fine-Tuning con `nested_params` dichiarato. A `true` (comportamento di sempre), ogni foglia scrive anche `embeddings_grid_*.png` — ma se quella foglia ha `n_components` diverso da 2, questo richiede un rifit (stesso meccanismo di `viz_n_components` sopra) per **ogni** cella del grid, uno sweep dentro lo sweep. Con `random_state` fissato quel rifit è **deterministico**: se un'altra foglia della stessa run ha già sweeppato `n_neighbors`/`min_dist` a `n_components=2`, il rifit produce un embedding identico byte-per-byte — puro calcolo sprecato. Metti `false` quando lo sai già (es. stai sweeppando `n_components: [5, 10]` avendo già una foglia a 2 componenti da un run precedente): salta tutti i rifit, tiene comunque `tuning_results.csv` per foglia (il numero, mai skippato).
- **`run_notes`**: `(Stringa)` Note per descrivere storicamente perché stai lanciando questo test (es. "Provo UMAP a 10 componenti").

### Come funziona il file `params_reduction.json`?
Se apri `"config/registry/params_reduction.json"`, vedrai che per ogni algoritmo c'è un blocco `"params"` (usato in Produzione) e un blocco `"tuning_grid"` (usato nel Fine-Tuning).
Quando in modalità Fine-Tuning scopri che `n_neighbors: 30` è perfetto per te, apri questo file e alla voce `"params"` di UMAP sostituisci il valore attuale con `30`.

---

## Output e File Log Storici

Tutti i risultati, per ogni metodo, finiranno separati in `results/lesion/dim_reduction/<metodo>/<GIORNO-MESE>_<session_name>` (il nome cartella include anche un tag auto-generato dal parametro chiave del metodo, es. `21-07_s1.1_d01` per UMAP con `min_dist=0.1` — vedi `config/registry/params_reduction.json`).

- Se eri in **Fine-Tuning**: Troverai `tuning_results.csv` e, se `nested_params` non è dichiarato, `tuning_plot.png` (solo con un parametro sweepato). Se `nested_params` **è** dichiarato, invece di un unico `tuning_plot.png` trovi le sottocartelle `<param>=<valore>/...` descritte sopra, ciascuna con la propria `tuning_results.csv` filtrata e `embeddings_grid_<colore>.png`. Niente matrice in nessuno dei due casi.
- Se eri in **Produzione**: Troverai `matrix.npy` (questa volta non avrà 800.000 colonne, ma magari solo 2, o quante ne hai messe in `n_components`), un `config.md` di riepilogo e il `metadata.csv` (che stavolta guadagna 3 colonne rispetto alla matrice originale, sempre — indipendentemente da cosa c'è in `color_by`: `lesion_volume_voxels`, il conteggio voxel della lesione di ogni soggetto, `lesion_side`, il lato della lesione — `"unknown"` per un soggetto/dataset per cui non è risolvibile, es. PASPORT che non ha quella colonna — e `nihss`, il punteggio di gravità basale — `NaN` con lo stesso tipo di gap). Questo arricchimento è condiviso con `dim_reduction_clustering.py` (`src/features/clinical.py::enrich_metadata_with_lesion_info`): un risultato prodotto da una delle due pipeline ha sempre le stesse colonne. Troverai sempre `embedding_plot_unico.png` (puntini anonimi, un solo colore) più una coppia PNG+HTML per ogni voce di `color_by` (es. `embedding_plot_dataset.png`/`.html`, `embedding_plot_volume.png`/`.html`, `embedding_plot_side.png`/`.html`, `embedding_plot_nihss.png`/`.html`) — se `n_components` (o `viz_n_components`) è diverso da 2, l'embedding usato per questi plot è un fit separato solo-per-visualizzazione, non l'embedding salvato in `matrix.npy` (vedi `viz_n_components` sopra).

  Ogni file `.html` è interattivo (apribile in un browser), passando sopra un punto mostra tutte le colonne di `metadata.csv` di quel soggetto. Per rigenerare i plot da una run già esistente senza ricalcolare l'embedding: `scripts/replot_dim_reduction.py --run-dir <cartella_run>` — funziona solo se l'embedding salvato ha esattamente 2 componenti (non ha la matrice grezza originale per rifittare una proiezione, a differenza della pipeline vera).

**Molto Importante: i file `runs.csv`/`runs_tuning.csv`**
Nella cartella base di ogni metodo (es. `results/lesion/dim_reduction/umap/`), lo script compila un vero e proprio "Diario di Bordo" automatico, in formato CSV — ma **due file separati**, non uno solo: `runs.csv` per le run di produzione, `runs_tuning.csv` per le run di fine-tuning (colonne identiche in entrambi: `session, id, timestamp, params, output, notes`). Ogni volta che lanci la pipeline con successo, aggiunge una riga nel file giusto con l'ora, quali parametri matematici esatti hai usato e le note che avevi scritto. In questo modo avrai una traccia storica scientifica di ogni singola prova fatta nei mesi, interrogabile con pandas, e non rischierai mai di scordarti con quali impostazioni avevi ottenuto un certo grafico.

**`SESSIONS.md` è un'altra cosa**: descrive cosa *significa* un numero di sessione (es. `s1.1`) — dataset usati, modalità, cosa è cambiato — scritto a mano da te, non generato dallo script. Vive in `data/SESSIONS.md` (canonico) con una copia/symlink in `results/SESSIONS.md`.
