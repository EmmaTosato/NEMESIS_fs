# Guida all'Embedding Explorer (app Dash)

App web live per esplorare interattivamente un run **di produzione** (`dim_reduction.py` o `clustering.py`, entrambi con `fine_tuning: false`) - 2D o 3D, con un selettore di run e bottoni di colorazione (neutro/dataset/side/volume/disconnection load/mean disconnection/nihss/cluster), stile editoriale. Un solo processo copre **tutti** i run di produzione già scritti, non un file HTML da rigenerare ogni volta. Cliccando un punto si vede anche la vera anatomia lesionale di quel paziente; per un run di modalità `sdc` si vede anche il suo disconnettoma; per un run `clustering.py` lo scatter può mostrare anche i centroidi dei cluster cerchiati (spenti di default, si accendono dalla legenda), e si può vedere la overlap map (lesione), la mappa di disconnessione, il soggetto rappresentativo e la composizione demografica/clinica di ciascun cluster - vedi "Anatomia lesionale", "Disconnessione (SDC)", "Overlap map per cluster", "Disconnessione per cluster", "Soggetto rappresentativo del cluster" e "Descrizione del cluster" più sotto.

- **Script**: `src/pipeline/embedding_app.py`
- **Logica**: `src/analysis/embedding_app.py`, `src/analysis/anatomical_maps.py` (risoluzione path + overlap/mean map) — architettura/dettagli implementativi: `docs/dev/anatomical_maps.md`
- **Input**: qualunque run di produzione già scritto sotto `results/*/dim_reduction/production/*/*` **o** `results/*/clustering/production/*/*/*` (`clustering.py` ha un livello in più, `<reduction_method>` - vedi `docs/guides/clustering.md`; `src.analysis.embedding_app.PRODUCTION_PIPELINES`; nessun refit, legge solo `matrix.npy`/`metadata.csv` già su disco) più `config/pipelines/build_lesion_matrix.json` (`--lesion-config`, pannelli di anatomia lesionale) e `config/pipelines/build_sdc_matrix.json` (`--sdc-config`, pannelli di anatomia SDC - deve avere `representation: "voxelwise"`, l'unica con il `disconnectome-map.nii.gz` grezzo da visualizzare)

---

## Da dove vengono i valori di colorazione

Regola unica (30-09-26): **un dato del soggetto viene da `assets/metadata/participants.csv`, un dato del run dal `metadata.csv` di quel run.**

| Bottone | Fonte | Colonna |
|---|---|---|
| `side` | participants.csv | `lesion_side` |
| `nihss` | participants.csv | `NIHSS` |
| `volume` | participants.csv | `lesion_volume_voxels_2mm` (o `_1mm`, vedi sotto) |
| `disconnection load` | participants.csv | `disconnection_load_voxels_2mm` (o `_1mm`, vedi sotto) |
| `mean disconnection` | participants.csv | `disconnection_mean_2mm` (o `_1mm`, vedi sotto) |
| `dataset` | metadata.csv del run | `dataset` |
| `cluster` | metadata.csv del run | `cluster_label` |

Prima l'ordine era invertito: si guardava prima il `metadata.csv` del run. Un run costruito prima del 06/09/26 porta ancora una **copia** di quelle colonne cliniche, e quella copia poteva divergere dal registro — due run degli stessi soggetti si coloravano in modo diverso. Ora il registro vince sempre.

Sul volume la differenza è sostanziale: il `lesion_volume_voxels` di un run conta i voxel sulla griglia che *quel* `build_lesion_matrix` ha usato, mentre le colonne del registro sono calcolate una volta sola su una griglia fissa per tutti i soggetti — le uniche confrontabili fra run.

### Disconnessione del paziente

Due bottoni colorano ogni punto per **quanto è disconnesso il paziente in totale**, l'analogo del volume lesionale per il disconnettoma:

- **disconnection load**: la somma della probabilità di disconnessione sui voxel del cervello. Si legge come un volume (`~60 000` è un soggetto tipico).
- **mean disconnection**: la stessa somma divisa per i voxel del cervello, cioè la probabilità media di disconnessione. Si legge come una frazione (`~0,033` è un soggetto tipico).

I due colorano i punti **in modo identico**: il divisore è una costante, quindi cambia solo il numero scritto sulla barra dei colori. Ne esistono due perché una cifra in voxel e una frazione si leggono in modo diverso.

La scala è **lineare**, non logaritmica come il volume: il carico di disconnessione non ha pochi valori enormi che schiacciano tutti gli altri (misurato sull'intera coorte: massimo/mediana 7,6, contro 97 per il volume lesionale), e una scala log allungherebbe la coda dei soggetti poco disconnessi. Un soggetto con carico **0** è quindi un valore vero in fondo alla scala, non un "missing".

Come il volume, hanno la riga **Griglia** (vedi sotto). I valori vengono da `sdc_metadata.csv` tramite `enrich_metadata.py` (sezione `sdc_metadata`, [`docs/guides/metadata.md`](metadata.md)): finché quel passaggio non è stato eseguito, i due bottoni mostrano un messaggio che dice di lanciarlo, non un grafico vuoto.

**Non è la stessa quantità della mappa "Disconnessione per cluster"**, più sotto: quella conta un voxel come disconnesso solo se la probabilità supera `0.5`, il colore somma ogni probabilità senza soglia. Ordinano i soggetti quasi allo stesso modo (Spearman 0,99 su 200 soggetti) ma non sono la stessa formula.

I due bottoni sono **visibili solo per un run di modalità `sdc`**: su un run `lesion` mostrano un messaggio esplicito invece di un grafico, anche se il valore esiste nel registro per quasi tutti i soggetti (il contrario non vale - `volume`/`side`/`nihss` restano disponibili su un run `sdc`, per relazionare un cluster di disconnessione al lato o al volume della lesione).

### Griglia

Quando il colore attivo è **volume**, **disconnection load** o **mean disconnection**, sotto ai bottoni compare una riga **Griglia** con `2mm` (il default, la griglia di produzione) e `1mm`. Il bottone scelto decide quale colonna del registro si legge (`..._2mm` oppure `..._1mm`); la riga sparisce con qualunque altro colore. Mostra solo le griglie che il registro ha davvero: una griglia appare da sé appena `enrich_metadata.py` ne copia la colonna (`copy_columns`, [`docs/guides/metadata.md`](metadata.md)), e scegliere una griglia che manca a quel colore mostra il messaggio che dice di rilanciarlo, non un grafico diverso.

Il numero sulla barra dei colori cambia con la griglia: a 2 mm un voxel vale 8 mm³, quindi il carico è circa 8 volte più piccolo (`~37 000` contro `~297 000` per lo stesso soggetto), mentre la media sul cervello (0-1) resta la stessa. Il **colore** dei punti no: sui 5853 soggetti i due carichi ordinano i soggetti quasi identicamente (Spearman 0,9999994).

Un soggetto con volume **0** su quella griglia è disegnato in grigio come "missing": a 2 mm il ricampionamento può azzerare una lesione piccola (`docs/dev/metadata.md`), e 0 non ha posizione su una scala logaritmica. Un valore negativo invece è un errore e blocca il grafico.

Un soggetto **senza riga nel registro** è disegnato in grigio (o `unknown` per una variabile categorica), non fa più fallire l'intero grafico: il conteggio finisce nei log.

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
| `--preload`      | off         | All'avvio, in un thread di background, legge una volta tutti i soggetti di tutti i run di clustering (maschere lesionali sempre; disconnettomi SDC solo per i run `sdc`) popolando la cache condivisa di `src/analysis/anatomical_maps.py::BinaryMaskStore` - da quel momento la mappa di anatomia di qualunque cluster di qualunque run si apre in circa un secondo invece che ricalcolarsi da zero al primo clic |
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
- **Bottoni di colorazione**: uno per "Neutro" più uno per ogni voce di `src.analysis.embedding_coloring.COLOR_MODES` (dataset/lesion side/lesion volume/disconnection load/mean disconnection/NIHSS (severity)/cluster) - lo stesso registro che usa `dim_reduction.py` in produzione, mai una copia. `cluster` è visibile solo per run che hanno davvero una colonna `cluster_label` in `metadata.csv` (cioè solo run `clustering.py`) - scegliere quel bottone su un run `dim_reduction.py` mostra un messaggio d'errore esplicito al posto del grafico, non un plot vuoto. Il label noise di HDBSCAN (`-1`) è mostrato come una categoria come le altre, senza colorazione grigia dedicata - a differenza del `cluster_plot.png` di produzione, questo è un esploratore generico su qualunque colonna di metadata, non il diagnostico dedicato al clustering.
- **Il grafico** ("Embedding Visualization"): 2D o 3D, deciso automaticamente dalla forma dell'embedding salvato per quel run (`embedding.shape[1]`) - mai uno slicing di un embedding con più componenti (vedi sotto). Per un run `clustering.py`, la matrice mostrata è quella usata per il clustering stesso (`clustering.py` non trasforma mai lo spazio delle feature) - se quel run è stato lanciato su un embedding già a 2/3 componenti si vede direttamente, altrimenti risulta "non mostrabile" come qualunque altro run oltre le 3 dimensioni (vedi sotto). Per un run `clustering.py`, lo scatter mostra anche un cerchio nero (con il numero del cluster) in corrispondenza del **centroide** di ciascun cluster - il punto medio delle coordinate embedding di quel cluster, non un soggetto reale. Passandoci sopra col mouse si vede quale soggetto reale è il più vicino a quel centroide - lo stesso soggetto mostrato nel pannello "Soggetto rappresentativo del cluster" più sotto.

## Un run non mostrabile

Un run il cui embedding salvato ha **più di 3 componenti** (es. un run lanciato con `n_components: 10`) non viene scartato dal selettore, ma mostra un messaggio esplicito al posto del grafico invece di un plot silenziosamente sbagliato: questa app, come `src/pipeline/replot_dim_reduction.py`, non ricarica mai la matrice di feature originale, quindi non ha modo di rifittare una proiezione a 2/3 componenti per la visualizzazione (`embedding[:, :3]` sarebbe un taglio arbitrario, non un riassunto - vedi `.claude/lessons_learned.md` #16). Per vedere quel run, rilancia `dim_reduction.py` con `n_components`/`viz_n_components` a 2 o 3.

---

## Anatomia lesionale

Pannello sempre visibile sotto il grafico, indipendentemente dal run scelto: mostra un messaggio ("Clicca un punto...") finché non si clicca un punto dell'embedding, poi la vera lesione di quel paziente in un visualizzatore 3D interattivo `nilearn` (`nilearn.plotting.view_img`, sfondo MNI152, `black_bg=False` → pagina bianca, ruotabile/zoomabile nel browser, colormap `autumn`).

Il paziente è risolto tramite `subject_id`/`dataset` del run corrente (colonne già in `metadata.csv`) più `data_root`/`lesion_glob` di `--lesion-config` (`src.analysis.anatomical_maps.resolve_lesion_paths`, la stessa logica già validata in `notebooks/post-results_analysis/embeddings_analysis.ipynb` §4) - se il file non si trova sul disco locale (es. subset locale parziale), il pannello mostra un messaggio d'errore esplicito al posto del viewer, mai un grafico vuoto/sbagliato. La soglia di binarizzazione usata per la visualizzazione è la stessa `binarize_threshold` del config (non un valore scelto a parte), così il viewer mostra esattamente ciò che la pipeline a monte ha effettivamente binarizzato.

## Clustering Explorer

Per un run `clustering.py` la pagina si divide in due, separate da una riga netta e da questo titolo: **sopra** tutto ciò che riguarda l'intero run o un singolo soggetto (scatter, anatomia lesionale, disconnettoma), **sotto** tutto ciò che riguarda un cluster alla volta.

La prima cosa della sezione è il selettore **Cluster**, centrato: pilota *tutti* i pannelli che seguono (overlap map, frequency map, soggetto rappresentativo, descrizione del cluster). Fino al 30/09/26 viveva dentro il primo pannello, il che lo faceva sembrare un controllo di quel pannello soltanto.

Per un run `dim_reduction.py` l'intera sezione è nascosta.

---

## Overlap map per cluster

Visibile solo per un run **`clustering.py`** (cioè con una colonna `cluster_label` in `metadata.csv`) - per un run `dim_reduction.py` il pannello resta nascosto. Un dropdown "Cluster" (una mappa alla volta, non una griglia con tutti i cluster insieme) fa vedere, per i pazienti di quel cluster, la percentuale di sovrapposizione lesionale voxel per voxel (`src.analysis.anatomical_maps.build_overlap_map`, promossa da `notebooks/post-results_analysis/embedding_to_anatomy_mapping.ipynb` §2) - stesso viewer `nilearn.plotting.view_img` (sfondo bianco) del pannello sopra, colormap `hot`, titolo con il numero di soggetti nel cluster.

Se uno o più soggetti del cluster non hanno il file grezzo della lesione su disco (dato locale incompleto - può succedere con dati vecchi, vedi `.claude/history/data_changelog.md`), non fanno fallire il pannello: vengono esclusi dalla mappa (e dal numero di soggetti nel titolo) e appare una riga di avviso in arancione con l'elenco di chi è stato escluso.

## Disconnessione (SDC)

Pannello visibile solo per un run di modalità **`sdc`** (un run `lesion` non ha un disconnettoma da mostrare - il pannello resta nascosto, non vuoto). Stesso comportamento del pannello "Anatomia lesionale": mostra un messaggio finché non si clicca un punto, poi il vero disconnettoma di quel paziente (`nilearn.plotting.view_img`, sfondo MNI152, colormap `magma`, colorbar attiva - a differenza della maschera di lesione binaria, il disconnettoma è una probabilità continua [0, 1] per voxel, mai binarizzata, quindi la colorbar è informativa). Solo i valori sopra 0.02 vengono colorati, per evitare che il rumore quasi-zero appaia come puntinato nero sullo sfondo.

Il paziente è risolto tramite `subject_id`/`dataset` del run corrente più `data_root`/`--sdc-config`'s `reference_template_path` (`src.analysis.anatomical_maps.resolve_lesion_paths`, stessa funzione del pannello lesionale, riusata su un glob diverso) - se il file non si trova sul disco locale, messaggio d'errore esplicito, mai un grafico vuoto.

## Disconnessione per cluster

Visibile solo per un run che è **sia** `sdc` **sia** `clustering.py` insieme. Usa il selettore "Cluster" della sezione.

Due letture degli **stessi** soggetti, scelte da un bottone:

### % soggetti disconnessi (default)

Per ogni voxel, la percentuale dei soggetti del cluster il cui disconnettoma supera **0,5** in quel voxel. È la **stessa identica quantità** della overlap map lesionale — stessa funzione (`build_overlap_map`), stessa scala 0-100% — quindi le due mappe si confrontano direttamente: "il 40% del cluster ha una lesione qui, ma il 70% è disconnesso qui".

La soglia 0,5 significa "più probabile che no", la stessa convenzione usata per binarizzare una maschera lesionale probabilistica. È una costante dichiarata (`DISCONNECTION_PROBABILITY_THRESHOLD`), non un cursore: una soglia regolabile invita a cercare il valore che fa sembrare separabile un cluster.

### Probabilità media

La media continua delle probabilità, voxel per voxel — il comportamento precedente.

⚠️ **Non è una percentuale di soggetti.** Un voxel a 0,6 può voler dire "tutti i soggetti a 0,6" oppure "il 60% a 1,0 e il 40% a 0,0": indistinguibili. Non si può leggere come "il 60% del cluster è disconnesso qui".

Serve comunque: usa **tutta** l'informazione continua invece di buttarla via a una soglia, quindi vede una disconnessione diffusa e sotto-soglia che la mappa a percentuale mostra vuota. Le due insieme dicono cose diverse: la percentuale dice *quanti* pazienti, la media dice *quanto* forte.

Stesso avviso arancione se qualche soggetto del cluster non ha il disconnettoma su disco.

## Soggetto rappresentativo del cluster

Visibile solo per un run **`clustering.py`** (qualunque modalità), dopo i due pannelli di mappa per cluster sopra - usa il selettore "Cluster" in cima alla sezione. Per il cluster scelto, mostra il soggetto reale più vicino al suo centroide nello spazio embedding (lo stesso cerchio nero visto nel grafico in cima alla pagina) - non un punto medio astratto, ma il paziente che più gli somiglia. Mostra la lesione di quel soggetto per un run di modalità `lesion`, il suo disconnettoma per un run `sdc` - stesso viewer interattivo, stessi bottoni "Salva HTML"/"Salva PNG" dei due pannelli a singolo soggetto sopra (senza il terzo bottone glass brain).

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
