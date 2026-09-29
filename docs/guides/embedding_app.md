# Guida all'Embedding Explorer (app Dash)

App web live per esplorare interattivamente un run **di produzione** (`dim_reduction.py` o `clustering.py`, entrambi con `fine_tuning: false`) - 2D o 3D, con un selettore di run e bottoni di colorazione (neutro/dataset/side/volume/nihss/cluster), stile editoriale. Un solo processo copre **tutti** i run di produzione già scritti, non un file HTML da rigenerare ogni volta. Cliccando un punto si vede anche la vera anatomia lesionale di quel paziente; per un run di modalità `sdc` si vede anche il suo disconnettoma; per un run `clustering.py` lo scatter mostra anche i centroidi dei cluster cerchiati, e si può vedere la overlap map (lesione), la frequency map (disconnessione), il soggetto rappresentativo e la composizione demografica/clinica di ciascun cluster - vedi "Anatomia lesionale", "Disconnessione (SDC)", "Overlap map per cluster", "Frequency map disconnessione per cluster", "Soggetto rappresentativo del cluster" e "Descrizione del cluster" più sotto.

- **Script**: `src/pipeline/embedding_app.py`
- **Logica**: `src/analysis/embedding_app.py`, `src/analysis/anatomical_maps.py` (risoluzione path + overlap/mean map) — architettura/dettagli implementativi: `docs/dev/anatomical_maps.md`
- **Input**: qualunque run di produzione già scritto sotto `results/*/dim_reduction/production/*/*` **o** `results/*/clustering/production/*/*/*` (`clustering.py` ha un livello in più, `<reduction_method>` - vedi `docs/guides/clustering.md`; `src.analysis.embedding_app.PRODUCTION_PIPELINES`; nessun refit, legge solo `matrix.npy`/`metadata.csv` già su disco) più `config/pipelines/build_lesion_matrix.json` (`--lesion-config`, pannelli di anatomia lesionale) e `config/pipelines/build_sdc_matrix.json` (`--sdc-config`, pannelli di anatomia SDC - deve avere `representation: "voxelwise"`, l'unica con il `disconnectome-map.nii.gz` grezzo da visualizzare)

---

## Cosa NON è

Non è il report "Understanding UMAP" (`src.pipeline.generate_understanding_umap_report`, vedi `docs/guides/understanding_umap_report.md`) - quello esplora una **griglia di tuning** (come cambia l'embedding al variare di `n_neighbors`/`min_dist`/`perplexity`) via HTML statico pre-generato, questo esplora **un risultato di produzione già scelto** via un'app Dash live. Due domande diverse, due strumenti diversi.

Per vedere in 3D interattivo/ruotabile una singola combinazione già calcolata di una sweep di tuning (invece del refit-a-2D che `embeddings_grid_*.png` mostra sempre, anche per una leaf `n_components=3`) c'è un terzo strumento, `src/pipeline/plot_tuning_embedding_3d.py` - legge un `embeddings.npz` di tuning e scrive HTML statici auto-contenuti (uno per combo/color mode), riusando lo stesso `build_embedding_figure` di questa app ma senza il discovery/selettore di run di produzione (vedi il docstring dello script).

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
| `--results-root` | `results` | Radice da scansionare (`<root>/*/dim_reduction/production/*/*` e `<root>/*/clustering/production/*/*/*`)          |
| `--lesion-config` | `config/pipelines/build_lesion_matrix.json` | Config (stessa forma usata da `build_lesion_matrix.py`) che risolve `data_root`/`lesion_glob`/`reference_template_path`/`binarize_threshold`/`resample_interpolation` per i pannelli di anatomia lesionale sotto - caricato/validato con lo stesso loader (`load_build_matrix_config`), fallisce subito all'avvio se il config o il template di riferimento mancano |
| `--sdc-config` | `config/pipelines/build_sdc_matrix.json` | Config (stessa forma usata da `build_sdc_matrix.py`) che risolve `data_root`/`reference_template_path`/`resample_interpolation` per i pannelli di anatomia SDC sotto - deve avere `representation: "voxelwise"` (fallisce subito all'avvio altrimenti, `representation: "parcellated"` non ha un `disconnectome-map.nii.gz` grezzo da mostrare) |
| `--clustering-params-file` | `config/registry/params_clustering.json` | Registry (stesso file che usa `clustering.py`) da cui il passo "Parametri" del selettore legge il `tag_param` di ciascun metodo di clustering (`n_clusters`/`linkage` per agglomerative, ecc. - `load_tag_params`) |
| `--port`         | `8060`    | Porta locale (non l'8050 di default di Dash, per non collidere con un'altra istanza Dash locale già in esecuzione) |
| `--debug`        | off         | Modalità debug di Dash (auto-reload, overlay errori nel browser)                                                   |

---

## Cosa mostra

- **Selettore a 7 passi** (in ordine di decisione - sostituisce il precedente dropdown unico che mischiava i run di ogni metodo/metrica/dimensionalità insieme):

  1. **Dato** - la modalità (`lesion`, `sdc` - nessuna modifica di codice richiesta, discovery generica su `results/*/...`).
  2. **Pipeline** - `dim_reduction` o `clustering` (le uniche 2 che questa app scopre - vedi `PRODUCTION_PIPELINES`/`discover_production_runs`), filtrata sulla modalità scelta; `dim_reduction` proposto per primo di default (pipeline più matura), non alfabeticamente.
  3. **Metodo** - il metodo dentro quella pipeline (`umap`/`pca`/`tsne`/`pacmap`... per dim_reduction, `kmeans`/`hdbscan`/`spectral`/... per clustering), filtrato su modalità + pipeline.
  4. **Metrica** - la metrica dell'**embedding a monte** (letta dai parametri realmente usati dal run - vedi sotto): per un run `dim_reduction.py` è la sua stessa metrica; per un run `clustering.py` è la metrica dell'embedding su cui è stato calcolato (`reduction_metric`, letta da `config.md`), **non** un iperparametro del metodo di clustering. `"—"` solo quando l'asse non esiste davvero: pca/pacmap per dim_reduction, o un run `clustering.py` lanciato direttamente su dati non ridotti (`reduction_method: "raw"`).
  5. **Componenti** - `n_components` dello stesso embedding a monte (`reduction_n_components` per `clustering.py`), filtrato su metrica; stesso `"—"` di sentinella nei casi limite di cui sopra.
  6. **Parametri** - gli iperparametri propri del metodo di clustering scelto (`n_clusters`+`linkage` per agglomerative, `min_cluster_size`+`min_samples` per hdbscan, ecc. - registrati come `tag_param` in `config/registry/params_clustering.json`/`--clustering-params-file`, `load_tag_params`), mostrati come combinazioni leggibili (`"n_clusters=4, linkage=average"`) - una per ogni combinazione realmente eseguita per la metrica/componenti scelti. Sempre `"—"` per la pipeline `dim_reduction` (non ha iperparametri di clustering).
  7. **Run** - il run vero e proprio (es. `13-08_s1.1_m_dice_nc3`), filtrato su tutti i passi precedenti e ordinato cronologicamente (dal prefisso `DD-MM` del nome), selezionato di default sul più recente - per `clustering.py` questo passo raramente serve a scegliere tra più opzioni (Metrica+Componenti+Parametri di solito bastano a isolare un unico run), ma il picker non lo assume: un secondo run della stessa identica combinazione in una data diversa comparirebbe qui, non sovrascriverebbe silenziosamente il primo.

  Scoperta generica alla base (`results/*/dim_reduction/production/*/*`, `results/*/clustering/production/*/*/*` - profondità diversa per pipeline, `clustering.py` ha il segmento extra `<reduction_method>`) - una futura modalità o metodo compare da solo nei passi 1/3, senza toccare il codice. `clustering.py` non genera più la cartella `comparison/` sotto `production/` (il confronto multi-metodo tra `cluster_plot.png` non esiste) - un'eventuale cartella `comparison/` residua resta comunque esclusa automaticamente: non ha mai un `manifest.json`, lo stesso controllo che scarta qualunque cartella incompleta.

  **Metrica/Componenti/Parametri letti da `config.md`, non dal nome del run**: il nome (`13-08_s1.1_m_dice_nc3`, `01-09_s1.1_m_euclidean_n2_k4_link_average`) è una convenzione testuale scelta a mano da chi lancia la pipeline, non garantita per ogni metodo - `run_params`/`read_run_config` leggono invece rispettivamente la riga `Params used: {...}` e il blocco ` ```json ` sotto `## Config`, entrambi scritti per davvero in ogni `config.md` da `dim_reduction.py`/`clustering.py`, le stesse fonti usate per l'anteprima "Params used"/"Config" già presenti in ogni run.
- **Bottoni di colorazione**: uno per "Neutro" più uno per ogni voce di `src.analysis.embedding_coloring.COLOR_MODES` (dataset/lesion side/lesion volume (voxels)/NIHSS (severity)/cluster) - lo stesso registro che usa `dim_reduction.py` in produzione, mai una copia. `cluster` è visibile solo per run che hanno davvero una colonna `cluster_label` in `metadata.csv` (cioè solo run `clustering.py`) - scegliere quel bottone su un run `dim_reduction.py` mostra un messaggio d'errore esplicito al posto del grafico, non un plot vuoto. Il label noise di HDBSCAN (`-1`) è mostrato come una categoria come le altre, senza colorazione grigia dedicata - a differenza del `cluster_plot.png` di produzione, questo è un esploratore generico su qualunque colonna di metadata, non il diagnostico dedicato al clustering.
- **Il grafico** ("Embedding Visualization"): 2D o 3D, deciso automaticamente dalla forma dell'embedding salvato per quel run (`embedding.shape[1]`) - mai uno slicing di un embedding con più componenti (vedi sotto). Per un run `clustering.py`, la matrice mostrata è quella usata per il clustering stesso (`clustering.py` non trasforma mai lo spazio delle feature) - se quel run è stato lanciato su un embedding già a 2/3 componenti si vede direttamente, altrimenti risulta "non mostrabile" come qualunque altro run oltre le 3 dimensioni (vedi sotto). Per un run `clustering.py`, lo scatter mostra anche un cerchio nero (con il numero del cluster) in corrispondenza del **centroide** di ciascun cluster - il punto medio delle coordinate embedding di quel cluster, non un soggetto reale. Passandoci sopra col mouse si vede quale soggetto reale è il più vicino a quel centroide - lo stesso soggetto mostrato nel pannello "Soggetto rappresentativo del cluster" più sotto.

## Un run non mostrabile

Un run il cui embedding salvato ha **più di 3 componenti** (es. un run lanciato con `n_components: 10`) non viene scartato dal selettore, ma mostra un messaggio esplicito al posto del grafico invece di un plot silenziosamente sbagliato: questa app, come `src/pipeline/replot_dim_reduction.py`, non ricarica mai la matrice di feature originale, quindi non ha modo di rifittare una proiezione a 2/3 componenti per la visualizzazione (`embedding[:, :3]` sarebbe un taglio arbitrario, non un riassunto - vedi `.claude/lessons_learned.md` #16). Per vedere quel run, rilancia `dim_reduction.py` con `n_components`/`viz_n_components` a 2 o 3.

---

## Anatomia lesionale

Pannello sempre visibile sotto il grafico, indipendentemente dal run scelto: mostra un messaggio ("Clicca un punto...") finché non si clicca un punto dell'embedding, poi la vera lesione di quel paziente in un visualizzatore 3D interattivo `nilearn` (`nilearn.plotting.view_img`, sfondo MNI152, `black_bg=False` → pagina bianca, ruotabile/zoomabile nel browser, colormap `autumn`).

Il paziente è risolto tramite `subject_id`/`dataset` del run corrente (colonne già in `metadata.csv`) più `data_root`/`lesion_glob` di `--lesion-config` (`src.analysis.anatomical_maps.resolve_lesion_paths`, la stessa logica già validata in `notebooks/post-results_analysis/embeddings_analysis.ipynb` §4) - se il file non si trova sul disco locale (es. subset di retrieval parziale), il pannello mostra un messaggio d'errore esplicito al posto del viewer, mai un grafico vuoto/sbagliato. La soglia di binarizzazione usata per la visualizzazione è la stessa `binarize_threshold` del config (non un valore scelto a parte), così il viewer mostra esattamente ciò che la pipeline a monte ha effettivamente binarizzato.

## Overlap map per cluster

Visibile solo per un run **`clustering.py`** (cioè con una colonna `cluster_label` in `metadata.csv`) - per un run `dim_reduction.py` il pannello resta nascosto. Un dropdown "Cluster" (una mappa alla volta, non una griglia con tutti i cluster insieme) fa vedere, per i pazienti di quel cluster, la percentuale di sovrapposizione lesionale voxel per voxel (`src.analysis.anatomical_maps.build_overlap_map`, promossa da `notebooks/post-results_analysis/embedding_to_anatomy_mapping.ipynb` §2) - stesso viewer `nilearn.plotting.view_img` (sfondo bianco) del pannello sopra, colormap `hot`, titolo con il numero di soggetti nel cluster.

Se uno o più soggetti del cluster non hanno il file grezzo della lesione su disco (dato locale incompleto - può succedere con dati vecchi, vedi `.claude/history/data_changelog.md`), non fanno fallire il pannello: vengono esclusi dalla mappa (e dal numero di soggetti nel titolo) e appare una riga di avviso in arancione con l'elenco di chi è stato escluso.

## Disconnessione (SDC)

Pannello visibile solo per un run di modalità **`sdc`** (un run `lesion` non ha un disconnettoma da mostrare - il pannello resta nascosto, non vuoto). Stesso comportamento del pannello "Anatomia lesionale": mostra un messaggio finché non si clicca un punto, poi il vero disconnettoma di quel paziente (`nilearn.plotting.view_img`, sfondo MNI152, colormap `magma`, colorbar attiva - a differenza della maschera di lesione binaria, il disconnettoma è una probabilità continua [0, 1] per voxel, mai binarizzata, quindi la colorbar è informativa). Solo i valori sopra 0.02 vengono colorati, per evitare che il rumore quasi-zero appaia come puntinato nero sullo sfondo.

Il paziente è risolto tramite `subject_id`/`dataset` del run corrente più `data_root`/`--sdc-config`'s `reference_template_path` (`src.analysis.anatomical_maps.resolve_lesion_paths`, stessa funzione del pannello lesionale, riusata su un glob diverso) - se il file non si trova sul disco locale, messaggio d'errore esplicito, mai un grafico vuoto.

## Frequency map disconnessione per cluster

Visibile solo per un run che è **sia** `sdc` **sia** `clustering.py` insieme - riusa lo stesso dropdown "Cluster" del pannello "Overlap map per cluster" sopra (un run di clustering ha un solo insieme di cluster, indipendentemente da quale mappa si sta guardando). Per i pazienti del cluster scelto, mostra la probabilità *media* di disconnessione voxel per voxel (`src.analysis.anatomical_maps.build_mean_map` - la media continua, non una percentuale di soggetti sopra soglia come per la lesione, dato che il disconnettoma è già una probabilità continua per soggetto) - stesso viewer, colormap `magma`, colorbar attiva, stessa soglia 0.02 del pannello sopra (essenziale qui: senza soglia, la media su centinaia di soggetti mostra ancora più puntinato nero di rumore di fondo).

Stesso avviso arancione del pannello "Overlap map per cluster" sopra se qualche soggetto del cluster non ha il disconnettoma su disco - escluso dalla media, non causa di un pannello che fallisce.

## Soggetto rappresentativo del cluster

Visibile solo per un run **`clustering.py`** (qualunque modalità), dopo i due pannelli di mappa per cluster sopra - riusa lo stesso dropdown "Cluster" di "Overlap map per cluster" (il widget vero e proprio si trova fisicamente in quel pannello, ma pilota anche questo). Per il cluster scelto, mostra il soggetto reale più vicino al suo centroide nello spazio embedding (lo stesso cerchio nero visto nel grafico in cima alla pagina) - non un punto medio astratto, ma il paziente che più gli somiglia. Mostra la lesione di quel soggetto per un run di modalità `lesion`, il suo disconnettoma per un run `sdc` - stesso viewer interattivo, stessi bottoni "Salva HTML"/"Salva PNG" dei due pannelli a singolo soggetto sopra (senza il terzo bottone glass brain).

## Descrizione del cluster

Visibile per **qualunque** run `clustering.py`, indipendentemente dalla modalità (a differenza dei due pannelli "frequency map" sopra, qui non serve un file di lesione/disconnettoma - solo l'anagrafica del soggetto). Riusa lo stesso dropdown "Cluster". Due parti, una sopra l'altra.

### Il grafico del cluster selezionato

5 pannellini su **3 per riga**, uno per variabile:

- **Età**, **Istruzione**, **NIHSS**, **Volume lesione** (voxel) - un box plot con ogni soggetto disegnato come punto, per vedere sia la distribuzione sia i singoli valori; il trattino tratteggiato è la media
- **Sesso** - un grafico a barre, con il conteggio scritto sopra ogni barra

**Ogni variabile ha un colore suo** (Età blu, Sesso arancione, Istruzione viola, NIHSS verde, Volume rosa scuro) - lo stesso colore che ritrovi nell'intestazione della sua colonna nella tabella qui sotto, così si capisce a colpo d'occhio quale pannellino corrisponde a quale colonna. Le due barre del sesso hanno lo stesso colore fra loro: sono già distinte dalle etichette `F`/`M` e dal numero scritto sopra.

Il quadratino colorato accanto al titolo, invece, è il colore che quel **cluster** ha nello scatter in cima alla pagina.

Sotto ogni pannellino, `n=disponibili/totale` - quante volte quella variabile è effettivamente popolata sui soggetti del cluster, mai nascosto: Istruzione e NIHSS in particolare sono spesso disponibili solo per una parte dei soggetti (dipende dal dataset di provenienza), il grafico lo dice esplicitamente invece di lasciarlo intuire dal numero di punti.

### La tabella di confronto fra tutti i cluster

Sotto il grafico, una tabella con **una riga per cluster** e una colonna per variabile - così una variabile si legge in colonna confrontando i cluster fra loro, senza dover cambiare il dropdown ogni volta. La riga del cluster selezionato è evidenziata; il pallino colorato a sinistra è sempre il colore di quel cluster nello scatter.

- variabili continue: **media ± deviazione standard** (passa il mouse sulla cella per mediana, minimo e massimo)
- **Sesso**: conteggio e percentuale per categoria
- sotto ogni valore, sempre `n=` - i soggetti che hanno quella variabile sul totale del cluster
- `—` significa che nessun soggetto di quel cluster ha quel dato
- la colonna **Soggetti** segnala, quando capita, quanti soggetti sono "fuori registro" (vedi sotto)

Il bucket **rumore** di hdbscan/dbscan (label `-1`, i soggetti non assegnati) compare in tabella come "Rumore": è un gruppo reale di soggetti del run e vederne le statistiche è utile, ma non è un cluster.

Tutti i valori vengono da `assets/metadata/participants.csv` (l'anagrafica clinica del progetto), non dal `metadata.csv` del run - vedi `docs/dev/cluster_description.md` per l'elenco completo delle variabili e perché.

Se qualche soggetto del cluster **non ha affatto una riga** in `participants.csv` (caso distinto da un valore mancante per una singola variabile), il pannello si disegna comunque su tutti gli altri e mostra sopra il grafico una riga di avviso che elenca i soggetti coinvolti. Quei soggetti restano contati nel `totale` di ogni variabile - il cluster non rimpicciolisce - ma non contribuiscono alcun valore. Per farli sparire dall'avviso, rilancia `src/pipeline/populate_metadata.py` (vedi `docs/guides/metadata.md`) così che entrino nell'anagrafica.

Nessun bottone "Salva HTML"/"Salva PNG" dedicato - come per lo scatter dell'embedding in cima alla pagina, l'icona fotocamera di Plotly (visibile al passaggio del mouse) esporta un PNG dello stato attuale.

## Salvare un grafico

Ogni plot interattivo ha un modo di salvarlo:

- **Scatter dell'embedding**: passandoci sopra col mouse compare un'unica icona nella modebar di Plotly (fotocamera, "toImage") - esporta un PNG dello stato attuale (run/colorazione correnti). Il resto della modebar di Plotly resta nascosto (stile minimale).
- **Ognuno dei 5 pannelli di anatomia**: "Salva HTML" scarica l'HTML autonomo del viewer (stesso file che il browser sta già mostrando nell'iframe), riapribile offline con l'interattività intatta. "Salva PNG" scarica invece un'immagine statica (`nilearn.plotting.plot_stat_map`, stessa soglia/colormap/colorbar del viewer interattivo) - utile per incollare la vista in un documento o una presentazione, dove l'interattività non serve.
- **Solo i 2 pannelli a singolo soggetto** ("Anatomia lesionale", "Disconnessione (SDC)"): un terzo bottone, "Salva PNG (glass brain)" - una singola silhouette trasparente del cervello (`nilearn.plotting.plot_glass_brain`) invece delle 3 fette piatte di "Salva PNG". Per la lesione usa `autumn` (stesso colore del viewer interattivo sopra - una maschera binaria non ha un gradiente da mostrare); per il disconnettoma usa `magma` con una soglia più alta (0.1 invece di ~0) e leggera trasparenza - una proiezione glass-brain somma il segnale lungo tutta la profondità del volume, quindi a soglia quasi zero il rumore di fondo diventa visibile come sottili striature scure.

---

## Stile

Font system-ui/-apple-system, sfondo bianco, nessun bordo "a scatola", modebar di Plotly nascosta, palette categorica CVD-safe già validata (`src.analysis.plotting._CATEGORICAL_PALETTE`), assi sottili senza griglia, `aspectmode="data"` in 3D (nessuna distorsione tra assi). Stessi token di design (colore testo, font stack, bordo cella) di `src.analysis.understanding_umap_report`'s `_CSS` - non importati direttamente (quel modulo ha un DOM completamente diverso, griglie/slider che questa app non ha), ma deliberatamente identici, così le due app Dash del repo restano un'unica famiglia visiva invece di due stili scollegati.

Colorazione continua (`volume`/`nihss`) con `log_scale=True` (solo `volume` oggi): i valori sono trasformati in log10 per il colore del marker, con i tick della colorbar rietichettati ai valori reali (`1`, `10`, `100`, ...) - Plotly Express non ha un asse colore log-scale diretto.
