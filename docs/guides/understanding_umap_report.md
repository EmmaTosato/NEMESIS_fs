# Guida al Report "Understanding UMAP"

Questa guida descrive l'utilizzo di `generate_understanding_umap_report.py`, che genera un report HTML interattivo — ispirato al layout di [pair-code.github.io/understanding-umap](https://pair-code.github.io/understanding-umap/) — a partire da un run di tuning già completato (UMAP + t-SNE), senza rieseguire alcun fit. Serve a esplorare visivamente l'effetto dei parametri (`n_neighbors`, `min_dist`, `perplexity`) sulla stessa coorte di soggetti, e a confrontare UMAP vs t-SNE fianco a fianco.

- **Script**: `src/pipeline/generate_understanding_umap_report.py`
- **Logica**: `src/analysis/understanding_umap_report.py`
- **Input**: due directory di tuning già scritte da `dim_reduction.py` (una UMAP, una t-SNE) con `fine_tuning: true` e `save_tuning_embeddings: true`

---

## Prerequisiti

Le due directory di tuning passate come input devono:
1. Contenere `embeddings.npz` + `metadata.csv` (scritti solo se `save_tuning_embeddings: true` era attivo nel run di `dim_reduction.py` che le ha prodotte — vedi `docs/guides/dim_reduction.md`).
2. Riferirsi **esattamente alla stessa coorte, nello stesso ordine** — lo script lo verifica esplicitamente confrontando i due `metadata.csv` riga per riga, e si ferma con un errore chiaro se non combaciano (mai un confronto silenzioso tra popolazioni diverse).
3. La directory UMAP deve avere `nested_params: ["metric", "n_components"]` (sia `n_components=2` che `n_components=3` valutati, per la Figura 3 2D-vs-3D); quella t-SNE `nested_params: ["metric"]` (sempre 2D — se un giorno esisterà un run t-SNE con `n_components=3`, si potrà reintrodurre un confronto 3D UMAP-vs-t-SNE, oggi assente per questo motivo).

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
```bash
sbatch jobs/run_generate_understanding_umap_report.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`:
```bash
PYTHONPATH=. python -m src.pipeline.generate_understanding_umap_report \
  --umap-tuning-dir results/lesion/dim_reduction/tuning/umap/13-08_s1.1 \
  --tsne-tuning-dir results/lesion/dim_reduction/tuning/tsne/13-08_s1.1
```

---

## Output

Un file `understanding_umap_<metric>.html` per ogni metrica presente nella directory UMAP (oggi `dice`, `euclidean`), scritto **dentro la directory di tuning UMAP stessa** — non in una cartella di report separata, stesso principio già seguito da `embeddings_grid_*.png` per ogni leaf.

Ogni pagina contiene 5 figure, in due sezioni:

**UMAP across parameters / dimensions** (dati reali, sempre):
1. Griglia statica `n_neighbors` × `min_dist`, colorabile per `dataset`/`side`/`volume`/`nihss`.
2. Stesso spazio, ma con due slider trascinabili al posto della griglia fissa.
3. UMAP 2D vs UMAP 3D affiancati, ciascuno con i propri slider — il 3D è un fit realmente separato (`n_components=3`), non una proiezione 2D con una coordinata aggiunta.

**UMAP vs t-SNE** (dati reali dal 13-08-26; prima di allora un fixture sintetico, finché non è arrivato un run t-SNE sulla stessa coorte):

4. Griglia statica a 2 righe (t-SNE per `perplexity`, UMAP per `n_neighbors` a `min_dist` fisso) — un valore sweepato da un solo metodo lascia la cella dell'altro vuota, dichiarato in didascalia, mai inventato.
5. Stesso confronto ma con slider live, un pannello per metodo.

---

---

## Versione interattiva (Dash)

Accanto al report HTML statico esiste una versione interattiva basata su [Dash](https://dash.plotly.com/), pensata come strumento di esplorazione **locale** — non fa parte della pipeline pubblicabile, non genera file in `results/`, resta un'app da avviare a mano quando serve guardare i dati più da vicino.

- **Script**: `src/pipeline/run_understanding_umap_dash.py`
- **Logica**: `src/analysis/understanding_umap_dash.py` (riusa `TuningData`/`load_tuning_data` e i builder di figure da `understanding_umap_report.py` — stesso loader, stesse regole di validazione coorte, mai duplicato)

### Esecuzione (solo locale, mai sbatch)
```bash
PYTHONPATH=. python -m src.pipeline.run_understanding_umap_dash \
  --umap-tuning-dir results/lesion/dim_reduction/tuning/umap/13-08_s1.1 \
  --tsne-tuning-dir results/lesion/dim_reduction/tuning/tsne/13-08_s1.1
```
Poi apri `http://127.0.0.1:8050` nel browser. `--port` per cambiare porta, `--debug` per il reload automatico di Dash durante lo sviluppo.

Nessun `jobs/run_*.sh`: un'app interattiva non ha una forma "batch job" — deve restare aperta e rispondere a un browser, non produce un output e finisce.

### Perché Dash e non solo l'HTML statico
Il report HTML statico pre-calcola OGNI combinazione di parametri e la incorpora tutta nella pagina (un blob JSON dentro un `<script>`, letto da JS per animare gli slider via `Plotly.animate`) — funziona offline/senza server, ma richiede un workaround esplicito per il range degli assi (vedi i commenti su `build_slider_section` nel modulo). La versione Dash calcola una sola combinazione per volta, lato Python, ad ogni interazione — nessun blob JSON, nessun workaround sul range (il ridisegno di Dash lo ricalcola da solo). Il compromesso è che serve un processo Python sempre attivo.

### Cosa copre
Le stesse 5 figure del report statico, un solo processo per entrambe le metriche (`dice`/`euclidean`, selezionabili con un picker in alto — non più un file HTML per metrica).

## Note tecniche

- **Nessun refit**: legge solo `tuning_results.csv`/`embeddings.npz`/`metadata.csv` già scritti — se una directory non ha `embeddings.npz` (perché `save_tuning_embeddings` era `false`), lo script fallisce con un errore chiaro invece di rieseguire UMAP/t-SNE.
- **Palette colori**: riusa direttamente `_CATEGORICAL_PALETTE`/`_NOISE_COLOR` da `src/analysis/plotting.py` (stessa palette CVD-safe validata, un'unica sorgente di verità — non una copia).
- **Dimensioni grid/slider** (`_CELL_PX=165`, canvas slider `440px`): calibrate sulla densità di punti reale della coorte (1150 soggetti), non un valore arbitrario — vedi i commenti nel modulo per la misurazione di riferimento contro la pagina PAIR originale.
