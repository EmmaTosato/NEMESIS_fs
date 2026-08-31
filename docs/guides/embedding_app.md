# Guida all'Embedding Explorer (app Dash)

App web live per esplorare interattivamente un run **di produzione** (`dim_reduction.py` o, dal 15-08-26, `clustering.py`, entrambi con `fine_tuning: false`) - 2D o 3D, con un selettore di run e bottoni di colorazione (neutro/dataset/side/volume/nihss/cluster), stile editoriale. Sostituisce il vecchio `embedding_plot_interactive.html` scritto per-run (rimosso 2026-08-14): un solo processo copre **tutti** i run di produzione già scritti, non un file HTML da rigenerare ogni volta.

- **Script**: `src/pipeline/embedding_app.py`
- **Logica**: `src/analysis/embedding_app.py`
- **Input**: qualunque run di produzione già scritto sotto `results/*/dim_reduction/production/*/*` **o** `results/*/clustering/production/*/*` (`src.analysis.embedding_app.PRODUCTION_PIPELINES`; nessun refit, legge solo `matrix.npy`/`metadata.csv` già su disco)

---

## Cosa NON è

Non è il report "Understanding UMAP" (`src.pipeline.generate_understanding_umap_report`, vedi `docs/guides/understanding_umap_report.md`) - quello esplora una **griglia di tuning** (come cambia l'embedding al variare di `n_neighbors`/`min_dist`/`perplexity`) via HTML statico pre-generato, questo esplora **un risultato di produzione già scelto** via un'app Dash live. Due domande diverse, due strumenti diversi.

Per vedere in 3D interattivo/ruotabile una singola combinazione già calcolata di una sweep di tuning (invece del refit-a-2D che `embeddings_grid_*.png` mostra sempre, anche per una leaf `n_components=3`) c'è un terzo strumento, `scripts/plot_tuning_embedding_3d.py` - legge un `embeddings.npz` di tuning e scrive HTML statici auto-contenuti (uno per combo/color mode), riusando lo stesso `build_embedding_figure` di questa app ma senza il discovery/selettore di run di produzione (vedi il docstring dello script).

---

## Esecuzione

Locale soltanto - un'app interattiva non ha una forma "batch", non va lanciata via `sbatch`:

```bash
conda activate nemesis
python -m src.pipeline.embedding_app
```

Poi apri `http://127.0.0.1:8060` nel browser. Opzioni:

| Flag               | Default     | Descrizione                                                                                                         |
| :----------------- | :---------- | :------------------------------------------------------------------------------------------------------------------ |
| `--results-root` | `results` | Radice da scansionare (`<root>/*/dim_reduction/production/*/*` e `<root>/*/clustering/production/*/*`)          |
| `--port`         | `8060`    | Porta locale (non l'8050 di default di Dash, per non collidere con un'altra istanza Dash locale già in esecuzione) |
| `--debug`        | off         | Modalità debug di Dash (auto-reload, overlay errori nel browser)                                                   |

---

## Cosa mostra

- **Selettore a 6 passi** (in ordine di decisione, esteso 15-08-26 quando "Pipeline" è diventato un vero selettore invece di un'etichetta fissa - sostituisce il precedente dropdown unico che mischiava i run di ogni metodo/metrica/dimensionalità insieme):

  1. **Dato** - la modalità (oggi solo `lesion`).
  2. **Pipeline** - `dim_reduction` o `clustering` (le uniche 2 che questa app scopre - vedi `PRODUCTION_PIPELINES`/`discover_production_runs`), filtrata sulla modalità scelta; `dim_reduction` proposto per primo di default (pipeline più matura), non alfabeticamente.
  3. **Metodo** - il metodo dentro quella pipeline (`umap`/`pca`/`tsne`/`pacmap`... per dim_reduction, `kmeans`/`hdbscan`/`spectral`/... per clustering), filtrato su modalità + pipeline.
  4. **Metrica** - letta dai parametri realmente usati dal run (non dal nome della cartella - vedi sotto), `"—"` per i metodi/run che non hanno un parametro `metric` (pca/pacmap, i run più vecchi di umap/tsne precedenti all'introduzione di dice/jaccard, **e sempre** per la pipeline `clustering` - un metodo di clustering non ha un asse "metrica" in questo senso).
  5. **Componenti** - `n_components` realmente usato, filtrato su metrica; sempre `"—"` per la pipeline `clustering` (non ricampiona mai la dimensionalità di X, non c'è un `n_components` da riportare).
  6. **Run** - il run vero e proprio (es. `13-08_s1.1_nc3_m_dice`), filtrato su tutti i passi precedenti e ordinato cronologicamente (dal prefisso `DD-MM` del nome), selezionato di default sul più recente - oggi quasi sempre un'unica opzione (ogni combinazione è stata prodotta una volta sola), ma il picker non lo assume: un secondo run della stessa combinazione in una data diversa comparirebbe qui, non sovrascriverebbe silenziosamente il primo.

  Scoperta generica alla base (`results/*/{dim_reduction,clustering}/production/*/*`) - una futura modalità o metodo compare da solo nei passi 1/3, senza toccare il codice. La cartella `comparison/` che `clustering.py` scrive sotto `production/` (il confronto multi-metodo, non un run di un singolo metodo) è esclusa automaticamente: non ha mai un `manifest.json`, lo stesso controllo che scarta qualunque cartella incompleta.

  **Metrica/Componenti letti da `config.md`, non dal nome del run**: il nome (`13-08_s1.1_nc3_m_dice`) è una convenzione testuale scelta a mano da chi lancia la pipeline, non garantita per ogni metodo (pca/tsne/pacmap/clustering non seguono lo schema `nc<N>_m_<metrica>`) - `run_params` legge invece la riga `Params used: {...}` che sia `dim_reduction.py` che `clustering.py` scrivono per davvero in ogni `config.md`, la stessa fonte usata per l'anteprima "Params used" già presente in ogni run.
- **Bottoni di colorazione**: uno per "Neutro" più uno per ogni voce di `src.analysis.embedding_coloring.COLOR_MODES` (dataset/lesion side/lesion volume (voxels)/NIHSS (severity)/cluster) - lo stesso registro che usa `dim_reduction.py` in produzione, mai una copia. `cluster` è visibile solo per run che hanno davvero una colonna `cluster_label` in `metadata.csv` (cioè solo run `clustering.py`) - scegliere quel bottone su un run `dim_reduction.py` mostra un messaggio d'errore esplicito al posto del grafico, non un plot vuoto. Il label noise di HDBSCAN (`-1`) è mostrato come una categoria come le altre, senza colorazione grigia dedicata - a differenza del `cluster_plot.png` di produzione, questo è un esploratore generico su qualunque colonna di metadata, non il diagnostico dedicato al clustering.
- **Il grafico**: 2D o 3D, deciso automaticamente dalla forma dell'embedding salvato per quel run (`embedding.shape[1]`) - mai uno slicing di un embedding con più componenti (vedi sotto). Per un run `clustering.py`, la matrice mostrata è quella usata per il clustering stesso (`clustering.py` non trasforma mai lo spazio delle feature) - se quel run è stato lanciato su un embedding già a 2/3 componenti si vede direttamente, altrimenti risulta "non mostrabile" come qualunque altro run oltre le 3 dimensioni (vedi sotto).

## Un run non mostrabile

Un run il cui embedding salvato ha **più di 3 componenti** (es. un run lanciato con `n_components: 10`) non viene scartato dal selettore, ma mostra un messaggio esplicito al posto del grafico invece di un plot silenziosamente sbagliato: questa app, come `scripts/replot_dim_reduction.py`, non ricarica mai la matrice di feature originale, quindi non ha modo di rifittare una proiezione a 2/3 componenti per la visualizzazione (`embedding[:, :3]` sarebbe un taglio arbitrario, non un riassunto - vedi `.claude/lessons_learned.md` #16). Per vedere quel run, rilancia `dim_reduction.py` con `n_components`/`viz_n_components` a 2 o 3.

---

## Stile

Font system-ui/-apple-system, sfondo bianco, nessun bordo "a scatola", modebar di Plotly nascosta, palette categorica CVD-safe già validata (`src.analysis.plotting._CATEGORICAL_PALETTE`), assi sottili senza griglia, `aspectmode="data"` in 3D (nessuna distorsione tra assi). Stessi token di design (colore testo, font stack, bordo cella) di `src.analysis.understanding_umap_report`'s `_CSS` - non importati direttamente (quel modulo ha un DOM completamente diverso, griglie/slider che questa app non ha), ma deliberatamente identici, così le due app Dash del repo restano un'unica famiglia visiva invece di due stili scollegati.

Colorazione continua (`volume`/`nihss`) con `log_scale=True` (solo `volume` oggi): i valori sono trasformati in log10 per il colore del marker, con i tick della colorbar rietichettati ai valori reali (`1`, `10`, `100`, ...) - a differenza del vecchio `embedding_plot_interactive.html`, che restava lineare anche per i modi log-scale (Plotly Express non ha un asse colore log-scale diretto).
