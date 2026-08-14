# Guida all'Embedding Explorer (app Dash)

App web live per esplorare interattivamente un embedding **di produzione** (`dim_reduction.py`, `fine_tuning: false`) - 2D o 3D, con un selettore di run e bottoni di colorazione (neutro/dataset/side/volume/nihss), stile editoriale. Sostituisce il vecchio `embedding_plot_interactive.html` scritto per-run (rimosso 2026-08-14): un solo processo copre **tutti** i run di produzione già scritti, non un file HTML da rigenerare ogni volta.

- **Script**: `src/pipeline/embedding_app.py`
- **Logica**: `src/analysis/embedding_app.py`
- **Input**: qualunque run di produzione già scritto sotto `results/*/dim_reduction/production/*/*` (nessun refit, legge solo `matrix.npy`/`metadata.csv` già su disco)

---

## Cosa NON è

Non è il report "Understanding UMAP" (`src.pipeline.generate_understanding_umap_report`/`run_understanding_umap_dash` - se presente) - quello esplora una **griglia di tuning** (come cambia l'embedding al variare di `n_neighbors`/`min_dist`/`perplexity`), questo esplora **un risultato di produzione già scelto**. Due domande diverse, due strumenti diversi.

---

## Esecuzione

Locale soltanto - un'app interattiva non ha una forma "batch", non va lanciata via `sbatch`:

```bash
conda activate nemesis
python -m src.pipeline.embedding_app
```

Poi apri `http://127.0.0.1:8060` nel browser. Opzioni:

| Flag | Default | Descrizione |
| :--- | :--- | :--- |
| `--results-root` | `results` | Radice da scansionare (`<root>/*/dim_reduction/production/*/*`) |
| `--port` | `8060` | Porta locale (8050 è già usata dal Dash del report di tuning - le due app possono girare insieme) |
| `--debug` | off | Modalità debug di Dash (auto-reload, overlay errori nel browser) |

---

## Cosa mostra

- **Selettore a 6 passi** (in ordine di decisione, 2026-08-14 su richiesta - sostituisce il precedente dropdown unico che mischiava i run di ogni metodo/metrica/dimensionalità insieme):
  1. **Dato** - la modalità (oggi solo `lesion`).
  2. **Pipeline** - campo informativo, non selezionabile: è sempre `dim_reduction · produzione` (l'unica combinazione che questa app scopre - vedi `discover_production_runs`).
  3. **Tipo di riduzione** - il metodo (`umap`/`pca`/`tsne`/`pacmap`...), filtrato sulla modalità scelta.
  4. **Metrica** - letta dai parametri realmente usati dal run (non dal nome della cartella - vedi sotto), `"—"` per i metodi/run che non hanno un parametro `metric` (pca/pacmap, e i run più vecchi di umap/tsne precedenti all'introduzione di dice/jaccard).
  5. **Componenti** - `n_components` realmente usato, filtrato su metrica.
  6. **Run** - il run vero e proprio (es. `13-08_s1.1_nc3_m_dice`), filtrato su tutti i passi precedenti e ordinato cronologicamente (dal prefisso `DD-MM` del nome), selezionato di default sul più recente - oggi quasi sempre un'unica opzione (ogni combinazione è stata prodotta una volta sola), ma il picker non lo assume: un secondo run della stessa combinazione in una data diversa comparirebbe qui, non sovrascriverebbe silenziosamente il primo.

  Scoperta generica alla base (`results/*/dim_reduction/production/*/*`) - una futura modalità o metodo compare da solo nei passi 1/3, senza toccare il codice.

  **Metrica/Componenti letti da `config.md`, non dal nome del run**: il nome (`13-08_s1.1_nc3_m_dice`) è una convenzione testuale scelta a mano da chi lancia la pipeline, non garantita per ogni metodo (pca/tsne/pacmap non seguono lo schema `nc<N>_m_<metrica>`) - `run_params` legge invece la riga `Params used: {...}` che `dim_reduction.py` scrive per davvero in ogni `config.md`, la stessa fonte usata per l'anteprima "Params used" già presente in ogni run.
- **Bottoni di colorazione**: uno per "Neutro" più uno per ogni voce di `src.analysis.embedding_coloring.COLOR_MODES` (dataset/lesion side/lesion volume (voxels)/NIHSS (severity)) - lo stesso registro che usa `dim_reduction.py` in produzione, mai una copia.
- **Il grafico**: 2D o 3D, deciso automaticamente dalla forma dell'embedding salvato per quel run (`embedding.shape[1]`) - mai uno slicing di un embedding con più componenti (vedi sotto).

## Un run non mostrabile

Un run il cui embedding salvato ha **più di 3 componenti** (es. un run lanciato con `n_components: 10`) non viene scartato dal selettore, ma mostra un messaggio esplicito al posto del grafico invece di un plot silenziosamente sbagliato: questa app, come `scripts/replot_dim_reduction.py`, non ricarica mai la matrice di feature originale, quindi non ha modo di rifittare una proiezione a 2/3 componenti per la visualizzazione (`embedding[:, :3]` sarebbe un taglio arbitrario, non un riassunto - vedi `.claude/lessons_learned.md` #16). Per vedere quel run, rilancia `dim_reduction.py` con `n_components`/`viz_n_components` a 2 o 3.

---

## Stile

Font system-ui/-apple-system, sfondo bianco, nessun bordo "a scatola", modebar di Plotly nascosta, palette categorica CVD-safe già validata (`src.analysis.plotting._CATEGORICAL_PALETTE`), assi sottili senza griglia, `aspectmode="data"` in 3D (nessuna distorsione tra assi). Stessi token di design (colore testo, font stack, bordo cella) di `src.analysis.understanding_umap_report`'s `_CSS` - non importati direttamente (quel modulo ha un DOM completamente diverso, griglie/slider che questa app non ha), ma deliberatamente identici, così le due app Dash del repo restano un'unica famiglia visiva invece di due stili scollegati.

Colorazione continua (`volume`/`nihss`) con `log_scale=True` (solo `volume` oggi): i valori sono trasformati in log10 per il colore del marker, con i tick della colorbar rietichettati ai valori reali (`1`, `10`, `100`, ...) - a differenza del vecchio `embedding_plot_interactive.html`, che restava lineare anche per i modi log-scale (Plotly Express non ha un asse colore log-scale diretto).
