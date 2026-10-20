# Guida all'Embedding Explorer (app Dash)

App web live per esplorare interattivamente un run **di produzione** (`dim_reduction.py` o `clustering.py`, entrambi con `fine_tuning: false`) - 2D o 3D, con un selettore di run e bottoni di colorazione (neutro/dataset/side/volume/disconnection load/mean disconnection/nihss/cluster), stile editoriale. Un solo processo copre **tutti** i run di produzione già scritti, non un file HTML da rigenerare ogni volta. Cliccando un punto si vede anche la vera anatomia lesionale di quel paziente; per un run di modalità `sdc` si vede anche il suo disconnettoma; per un run `clustering.py` lo scatter può mostrare anche i centroidi dei cluster cerchiati (spenti di default, si accendono dalla legenda), e si può vedere la overlap map (lesione), la mappa di disconnessione, il soggetto rappresentativo e la composizione demografica/clinica di ciascun cluster - vedi "Anatomia lesionale", "Disconnessione (SDC)", "Overlap map per cluster", "Disconnessione per cluster", "Soggetto rappresentativo del cluster", "Descrizione del cluster" e "Composizione dei cluster" più sotto.

- **Script**: `src/pipeline/embedding_app.py`
- **Logica**: `src/analysis/embedding_app.py`, `src/analysis/anatomical_maps.py` (risoluzione path + overlap/mean map) — architettura/dettagli implementativi: `docs/dev/anatomical_maps.md`
- **Input**: qualunque run di produzione già scritto sotto `results/*/dim_reduction/production/*/*` **o** `results/*/clustering/production/*/*/*` (`clustering.py` ha un livello in più, `<reduction_method>` - vedi `docs/guides/clustering.md`; `src.analysis.embedding_app.PRODUCTION_PIPELINES`; nessun refit, legge solo `matrix.npy`/`metadata.csv` già su disco) più `config/pipelines/build_lesion_matrix.json` (`--lesion-config`, pannelli di anatomia lesionale) e `config/pipelines/build_sdc_matrix.json` (`--sdc-config`, pannelli di anatomia SDC - deve avere `representation: "voxelwise"`, l'unica con il `disconnectome-map.nii.gz` grezzo da visualizzare)

---

## Da dove vengono i valori di colorazione

Regola unica: **un dato del soggetto viene da `assets/metadata/participants.csv`, un dato del run dal `metadata.csv` di quel run.**

| Bottone | Fonte | Colonna |
|---|---|---|
| `side` | participants.csv | `lesion_side` |
| `lesion location` | participants.csv | `location_dominant_2mm` |
| `nihss` | participants.csv | `NIHSS` |
| `volume` | participants.csv | `lesion_volume_voxels_2mm` (o `_1mm`, vedi sotto) |
| `disconnection load` | participants.csv | `disconnection_load_voxels_2mm` (o `_1mm`, vedi sotto) |
| `mean disconnection` | participants.csv | `disconnection_mean_2mm` (o `_1mm`, vedi sotto) |
| `dataset` | metadata.csv del run | `dataset` |
| `cluster` | metadata.csv del run | `cluster_label` |

Un run più vecchio può portare ancora nel suo `metadata.csv` una **copia** di quelle colonne cliniche, che può divergere dal registro: il registro vince sempre, così due run degli stessi soggetti si colorano allo stesso modo.

Sul volume la differenza è sostanziale: il `lesion_volume_voxels` di un run conta i voxel sulla griglia che *quel* `build_lesion_matrix` ha usato, mentre le colonne del registro sono calcolate una volta sola su una griglia fissa per tutti i soggetti — le uniche confrontabili fra run.

### Sede della lesione

Il bottone **lesion location** colora ogni punto per **dove sta la lesione**: la categoria anatomica che ne contiene la quota maggiore, una tra sette (`infratentorial`, `subcortical_gray`, `cortex_only`, `cortex_white_boundary`, `white_matter_only`, `ventricle`, `unlabeled`). `cortex_white_boundary` non è una sede: sono i voxel su cui i due atlanti Harvard-Oxford non concordano (corteccia per uno, sostanza bianca per l'altro). Definizioni e regole: [`docs/dev/metadata.md`](../dev/metadata.md), sezione *La sede della lesione*.

- **Ogni etichetta ha sempre lo stesso colore**, in qualunque run e anche se in quel run un'altra etichetta non compare (di solito `cortex_white_boundary`, rara: 21 soggetti su 5853). La legenda segue l'ordine delle categorie, non quello alfabetico.
- **Grigio**: sede non disponibile, cioè i soggetti con la lesione tutta fuori dal cervello (4 su 5853).
- **Disponibile su ogni modalità di run**, `lesion` e `sdc`: su un run `sdc` serve a vedere dove stanno le lesioni di un cluster di disconnessione.
- **Il colore è la categoria dominante, non una misura continua**: una lesione 40% / 35% / 25% prende il colore del 40%. Le quote per categoria sono nel registro (`location_<categoria>_2mm`), ma non hanno ancora un bottone.
- I valori vengono da `lesion_metadata.csv` tramite `enrich_metadata.py` (`lesion_metadata.copy_columns`, [`docs/guides/metadata.md`](metadata.md)); finché quel passaggio non è stato eseguito il bottone mostra un messaggio che dice di lanciarlo.

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
| `--cache-dir` | `results/cache` | Dove si salva ciò che è troppo lento da rifare a ogni clic o a ogni avvio, calcolato una volta: in `raw_distances/` la matrice delle distanze dice di un run `adp` (sezione "Valutazione del clustering", circa 270 MB per matrice), in `component_maps/` le mappe t delle componenti di un run `pca` (sezione "Mappe delle componenti"), in `binary_masks/` i voxel sopra soglia di ogni maschera lesionale e di ogni disconnettoma (circa 27 KB per soggetto: ~320 MB per tutti i 5845 soggetti, il doppio per lesione e disconnettoma), che rendono istantanea l'overlap map di un cluster già visto anche dopo un riavvio |
| `--preload`      | off         | All'avvio, in un thread di background, legge una volta tutti i soggetti di tutti i run di clustering (maschere lesionali sempre; disconnettomi SDC solo per i run `sdc`) popolando la cache condivisa di `src/analysis/anatomical_maps.py::BinaryMaskStore` - da quel momento la mappa di anatomia di qualunque cluster di qualunque run si apre in circa un secondo invece che ricalcolarsi da zero al primo clic |
| `--port`         | `8060`    | Porta locale (non l'8050 di default di Dash, per non collidere con un'altra istanza Dash locale già in esecuzione) |
| `--debug`        | off         | Modalità debug di Dash (auto-reload, overlay errori nel browser)                                                   |

---

## Cosa mostra

- **Nove selettori** + il bottone **Riavvia** (in ordine di decisione, da sinistra a destra - sostituiscono il dropdown unico che mischiava i run di ogni metodo/metrica/dimensionalità insieme; i primi otto sono filtri facoltativi, vedi sotto):

  1. **Dato** - la modalità (`lesion`, `sdc` - nessuna modifica di codice richiesta, discovery generica su `results/*/...`).
  2. **Soggetti** - il numero di soggetti della matrice del run (letto da `manifest.json`, senza caricare la matrice): serve a distinguere run dello stesso tipo fatte su coorti di dimensione diversa, per esempio prima e dopo un'esclusione.
  3. **Pipeline** - `dim_reduction` o `clustering` (le uniche 2 che questa app scopre - vedi `PRODUCTION_PIPELINES`/`discover_production_runs`); `dim_reduction` è elencata per prima (pipeline più matura), non alfabeticamente.
  4. **Metodo** - il metodo dentro quella pipeline (`umap`/`pca`/`tsne`/`pacmap`... per dim_reduction, `kmeans`/`hdbscan`/`spectral`/... per clustering).
  5. **Riduzione** - il metodo di riduzione su cui è calcolato il run: per un run `clustering.py` è `umap`, `tsne`, ... oppure `raw` (dati non ridotti, mostrato per ultimo, così il default è un embedding vero quando esiste); per la pipeline `dim_reduction` il campo è nascosto, perché il Metodo *è* già il metodo di riduzione. Senza questo passo i run su `umap` e su `raw` finivano nelle stesse liste Metrica/Componenti/Run.
  6. **Metrica** - la metrica dell'**embedding a monte** (letta dai parametri realmente usati dal run - vedi sotto): per un run `dim_reduction.py` è la sua stessa metrica; per un run `clustering.py` è la metrica dell'embedding su cui è stato calcolato (`reduction_metric`, letta da `config.md`), **non** un iperparametro del metodo di clustering. `"—"` solo quando l'asse non esiste davvero: pca/pacmap per dim_reduction, o un run `clustering.py` lanciato direttamente su dati non ridotti (`reduction_method: "raw"`).
  7. **Componenti** - `n_components` dello stesso embedding a monte (`reduction_n_components` per `clustering.py`); stesso `"—"` di sentinella nei casi limite di cui sopra.
  8. **Parametri** - gli iperparametri propri del metodo di clustering scelto (`n_clusters`+`linkage` per agglomerative, `min_cluster_size`+`min_samples` per hdbscan, ecc. - registrati come `tag_param` in `config/registry/params_clustering.json`/`--clustering-params-file`, `load_tag_params`), mostrati come combinazioni leggibili (`"n_clusters=4, linkage=average"`) - una per ogni combinazione realmente eseguita per i valori scelti a sinistra. Sempre `"—"` per la pipeline `dim_reduction` (non ha iperparametri di clustering).
  9. **Run** - il run vero e proprio (es. `13-08_s1.1_m_dice_nc3`), la lista delle run che hanno i valori dei selettori impostati, ordinata cronologicamente (dal prefisso `DD-MM` del nome, una senza data in fondo), con la più recente scelta di default. Un secondo run della stessa identica combinazione in una data diversa compare qui, non sovrascrive il primo.

  **Una cascata da sinistra a destra.** Ogni selettore offre solo i valori delle run compatibili con le scelte fatte **a sinistra**: dopo aver scelto Pipeline e Metodo, Metrica offre solo le metriche di quel metodo, e così via. I selettori a destra non restringono mai quelli a sinistra. Ognuno ha come prima voce `---`, che significa "nessun filtro": si può quindi **fermarsi in qualunque punto** (per esempio a Componenti) e scegliere direttamente la Run.

  **Scegliere la Run riempie i selettori ancora a `---`** con i valori di quella run: i parametri seguono la run, non il contrario. Dopo, la lista Run contiene solo le run con gli stessi valori; per allargarla si rimette a `---` un selettore a sinistra.

  **Se cambi un selettore** e uno di quelli a destra non è più compatibile, torna a `---` e lo vedi. La run scelta resta se i selettori la elencano ancora, altrimenti è la più recente. Con Run a `---` (nessuna run scelta) i grafici e i pannelli sotto i selettori sono nascosti e la pagina lo dice; `---` resta scelto finché non ne scegli una, anche se cambi i filtri. All'apertura la pagina parte invece su una run, con Dato la prima modalità e Pipeline `dim_reduction`, gli altri a `---`. Quando un selettore (per esempio Metodo) è a `---`, il nome di ogni run nella barra è seguito dal suo valore per quel selettore, `12-10_s1.4-vol_m_dice_nc2  (dim_reduction / umap)`, così run di metodi diversi si distinguono. `—` (una sola lineetta) è invece un **valore** vero, "questa run non ha quell'asse" (per esempio la metrica di una PCA): non è `---`. Tutti i selettori si aggiornano insieme, in una sola callback (`resolve_pickers`), mai uno dopo l'altro.

  **Riavvia** (a destra di Run) rimette tutti i selettori a `---`, Run compresa: i grafici si nascondono finché non si sceglie una run (`open_pickers`).

  Scoperta generica alla base (`results/*/dim_reduction/production/*/*`, `results/*/clustering/production/*/*/*` - profondità diversa per pipeline, `clustering.py` ha il segmento extra `<reduction_method>`) - una futura modalità o metodo compare da solo nei passi 1/3, senza toccare il codice. `clustering.py` non genera più la cartella `comparison/` sotto `production/` (il confronto multi-metodo tra `cluster_plot.png` non esiste) - un'eventuale cartella `comparison/` residua resta comunque esclusa automaticamente: non ha mai un `manifest.json`, lo stesso controllo che scarta qualunque cartella incompleta.

  **Metrica/Componenti/Parametri letti da `config.md`, non dal nome del run**: il nome (`13-08_s1.1_m_dice_nc3`, `01-09_s1.1_m_euclidean_n2_k4_link_average`) è una convenzione testuale scelta a mano da chi lancia la pipeline, non garantita per ogni metodo - `run_params`/`read_run_config` leggono invece rispettivamente la riga `Params used: {...}` e il blocco ` ```json ` sotto `## Config`, entrambi scritti per davvero in ogni `config.md` da `dim_reduction.py`/`clustering.py`, le stesse fonti usate per l'anteprima "Params used"/"Config" già presenti in ogni run.
- **Descrizione del colore**: sotto il titolo "Embedding Visualization" e sopra il plot, una o due frasi dicono cosa significa il colore attivo e cosa significa il grigio. Il testo è il campo `description` di ogni voce di `COLOR_MODES` (quella del bottone neutro sta in `embedding_app.py`), accanto a etichetta e scala.
- **Bottoni di colorazione**: uno per "Neutro" più uno per ogni voce di `src.analysis.embedding_coloring.COLOR_MODES` (dataset/lesion side/lesion volume/disconnection load/mean disconnection/NIHSS (severity)/cluster) - lo stesso registro che usa `dim_reduction.py` in produzione, mai una copia. `cluster` è visibile solo per run che hanno davvero una colonna `cluster_label` in `metadata.csv` (cioè solo run `clustering.py`) - scegliere quel bottone su un run `dim_reduction.py` mostra un messaggio d'errore esplicito al posto del grafico, non un plot vuoto. Il label noise di HDBSCAN (`-1`) è mostrato come una categoria come le altre, senza colorazione grigia dedicata - a differenza del `cluster_plot.png` di produzione, questo è un esploratore generico su qualunque colonna di metadata, non il diagnostico dedicato al clustering.
- **Il grafico** ("Embedding Visualization"): 2D o 3D, deciso automaticamente dalla forma dell'embedding salvato per quel run (`embedding.shape[1]`) - mai uno slicing di un embedding con più componenti (vedi sotto). Per un run `clustering.py`, la matrice mostrata è quella usata per il clustering stesso (`clustering.py` non trasforma mai lo spazio delle feature) - se quel run è stato lanciato su un embedding già a 2/3 componenti si vede direttamente, altrimenti si disegna sul suo embedding gemello 2D/3D, se ne ha registrato uno (`viz_embedding_path`), o risulta "non mostrabile" (vedi sotto). Per un run `clustering.py`, lo scatter mostra anche un cerchio nero (con il numero del cluster) in corrispondenza del **centroide** di ciascun cluster - il punto medio delle coordinate embedding di quel cluster, non un soggetto reale. Passandoci sopra col mouse si vede quale soggetto reale è il più vicino a quel centroide - lo stesso soggetto mostrato nel pannello "Soggetto rappresentativo del cluster" più sotto.

## Un run con più di 3 componenti

Un run `clustering.py` fatto su un embedding a **più di 3 componenti** (es. `n_components: 10`) o su una matrice grezza ha un `matrix.npy` che l'app non può disegnare: scegliere due colonne a caso sarebbe un taglio arbitrario (`embedding[:, :3]`, vedi `.claude/lessons_learned.md` #16), e l'app non ricarica mai la matrice originale per rifare una proiezione.

L'app lo disegna sulle coordinate dell'**embedding gemello 2D/3D** che il run stesso ha registrato come `viz_embedding_path` nel suo `config.md` (lo stesso embedding con gli stessi parametri tranne `n_components`, già verificato da `clustering.py` quando il run è stato scritto):

- **Punti e colori:** le posizioni vengono dal gemello, i colori sono i cluster calcolati sulle componenti del run. Sotto il grafico compare una nota che dice quale embedding è disegnato e che non è lo spazio in cui sono calcolati i cluster.
- **Controllo:** l'app verifica di nuovo che il gemello sia 2D/3D e copra gli stessi soggetti nello stesso ordine; altrimenti mostra un messaggio invece del grafico, perché le etichette finirebbero sui soggetti sbagliati.
- **Centroidi e soggetto rappresentativo:** per un run su un embedding (`reduced_data: true`) si cercano nello spazio del clustering (le componenti del run), non nel disegno: il cerchio sta sulla posizione disegnata del soggetto reale più vicino al centro del cluster. Per un run su matrice grezza (es. ADP) non c'è uno spazio dove fare la media coerente con la metrica del clustering (dice su 221955 colonne): il cerchio è calcolato sulle coordinate disegnate.

Un run senza `viz_embedding_path` resta non mostrabile e non viene scartato dal selettore: mostra un messaggio al posto del grafico. Per vederlo, rilancia `clustering.py` con un `viz_embedding_path`. Un run `dim_reduction.py` con più di 3 componenti è sempre non mostrabile: rilancialo con `viz_n_components` a 2 o 3.

---

## Indice della pagina

In alto a destra c'è un menu **Indice**, chiuso di default e fisso sullo schermo mentre scorri. Aprendolo si salta a una sezione. Elenca solo le sezioni che il run scelto ha davvero: un run `lesion` non mostra "Disconnessione (SDC)", un run di `dim_reduction` non mostra le sezioni per cluster.

## Anatomia lesionale

Pannello sempre visibile sotto il grafico, indipendentemente dal run scelto: mostra un messaggio ("Clicca un punto...") finché non si clicca un punto dell'embedding, poi la vera lesione di quel paziente in un visualizzatore 3D interattivo `nilearn` (`nilearn.plotting.view_img`, sfondo MNI152, `black_bg=False` → pagina bianca, ruotabile/zoomabile nel browser, colormap `autumn`).

Il paziente è risolto tramite `subject_id`/`dataset` del run corrente (colonne già in `metadata.csv`) più `data_root`/`lesion_glob` di `--lesion-config` (`src.analysis.anatomical_maps.resolve_lesion_paths`, la stessa logica già validata in `notebooks/post-results_analysis/embeddings_analysis.ipynb` §4) - se il file non si trova sul disco locale (es. subset locale parziale), il pannello mostra un messaggio d'errore esplicito al posto del viewer, mai un grafico vuoto/sbagliato. La soglia di binarizzazione usata per la visualizzazione è la stessa `binarize_threshold` del config (non un valore scelto a parte), così il viewer mostra esattamente ciò che la pipeline a monte ha effettivamente binarizzato.

## Clustering Explorer

Per un run `clustering.py` la pagina si divide in due, separate da una riga netta e da questo titolo: **sopra** tutto ciò che riguarda l'intero run o un singolo soggetto (scatter, anatomia lesionale, disconnettoma), **sotto** tutto ciò che riguarda un cluster alla volta.

La prima cosa della sezione è il selettore **Cluster**, centrato: pilota *tutti* i pannelli che seguono (overlap map, frequency map, soggetto rappresentativo, descrizione del cluster).

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

Visibile solo per un run **`clustering.py`** (qualunque modalità), dopo i due pannelli di mappa per cluster sopra - usa il selettore "Cluster" in cima alla sezione. Per il cluster scelto, mostra il soggetto reale più vicino al suo centroide nello spazio del clustering (lo stesso cerchio nero visto nel grafico in cima alla pagina) - non un punto medio astratto, ma il paziente che più gli somiglia. Mostra la lesione di quel soggetto per un run di modalità `lesion`, il suo disconnettoma per un run `sdc` - stesso viewer interattivo, stessi bottoni "Salva HTML"/"Salva PNG" dei due pannelli a singolo soggetto sopra (senza il terzo bottone glass brain).

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

Il pannello descrive e non testa: nessun numero dice se una differenza tra cluster supera il caso. Per le variabili asimmetriche, come il volume, la mediana (nel tooltip) descrive meglio della media; volume e disconnessione derivano dai dati del clustering, quindi la loro differenza tra cluster è in parte per costruzione; Istruzione e NIHSS esistono solo per alcuni dataset (UCL-UK non ha nessuno dei due). Le cautele complete sono in `docs/dev/cluster_description.md` ("Reading a cluster description").

Nessun bottone "Salva HTML"/"Salva PNG" dedicato - come per lo scatter dell'embedding in cima alla pagina, l'icona fotocamera di Plotly (visibile al passaggio del mouse) esporta un PNG dello stato attuale.

## Composizione dei cluster

Ultimo pannello della pagina, per un run di clustering. Mette **tutti i cluster del run affiancati**, un grafico per variabile, per vedere come si distribuiscono le variabili da un cluster all'altro. Non dipende dal cluster scelto nel dropdown.

Variabili categoriche, barre orizzontali al 100%: una barra per cluster, divisa per categoria, così cluster di dimensioni diverse si confrontano sulla stessa scala.

- dataset

- lato della lesione

- localizzazione dominante della lesione

Variabili numeriche, un box plot per cluster nel colore che il cluster ha nello scatter:

- NIHSS

- volume della lesione (scala logaritmica)

- carico di disconnessione

Passando il mouse su una barra compaiono il **numero di soggetti** e la **quota del cluster** (es. `42 soggetti (31.8% del cluster)`); la quota è calcolata sui soli soggetti che hanno il dato.

Sotto il titolo di ogni grafico, `n=` indica i soggetti con il dato sul totale del run. I valori vengono da `participants.csv`; un soggetto assente dal registro resta nei grafici come dato mancante ed è nominato in una riga di avviso. L'icona fotocamera di Plotly esporta il PNG.

Dettagli di implementazione: `docs/dev/cluster_composition.md`.

## Mappe delle componenti

Per un run `dim_reduction` con metodo **`pca`** compare una sezione che mostra **dove nel cervello vive ogni componente**, come nel § 6 di `notebooks/pipeline_building/thiebaut_2020_replication.ipynb`. Si sceglie la componente dal menu e si vede la sua mappa in un viewer interattivo (rosso e blu, le tre sezioni che si incrociano sul picco).

**Cosa è la mappa.** Non sono i pesi della componente. Per ogni voxel si fa una regressione multipla `valore del voxel ~ intercetta + score di tutte le componenti` sui soggetti, e la mappa della componente è il **t** del suo coefficiente: un t alto è un effetto solido, vicino a 0 nessun effetto, il segno è la direzione. È simile alla mappa dei pesi ma tiene conto dell'incertezza di ogni voxel. Il paper usa `randomise` (1000 permutazioni); qui **non c'è test di permutazione**.

**Come si legge.**

| Cosa vedi | Significa |
|---|---|
| **Rosso** (t positivo) | più il soggetto ha questa componente, più quel voxel è disconnesso |
| **Blu** (t negativo) | più il soggetto ha questa componente, meno quel voxel è disconnesso |
| **Colore forte** | effetto solido |
| **Colore assente** | effetto sotto soglia, o nessun effetto |

Si cerca dove sta la zona rossa: se è compatta, la componente è una zona del cervello. Il **segno di una componente è arbitrario**: ogni mappa è orientata con il picco rosso, quindi si guarda la forma, non il colore. Sono colorati solo i voxel con |t| di almeno il **30% del picco** della componente (`COMPONENT_MAP_THRESHOLD_FRACTION`): con migliaia di soggetti anche effetti piccoli hanno un t alto, e una soglia fissa come |t| > 3 colorerebbe quasi tutto il cervello.

**Riproducibilità.** Sopra la mappa, un grafico a barre con una barra per componente: i soggetti si dividono in due metà a caso (seme fisso), la regressione si rifà in ciascuna e si correla (Pearson, sui voxel) la mappa delle due metà. 1 = uguali, 0 = niente in comune. Una componente la cui mappa non si ritrova non è un pattern stabile, per quanto pulita sembri: è la verifica che serve soprattutto dopo un varimax, che dà componenti dall'aspetto pulito anche quando nei dati non ci sono gruppi. Gli score sono quelli di tutti i soggetti, quindi si verifica che la **mappa** si ritrovi, non che la PCA sia stabile. La linea tratteggiata è la media del paper (0,813 con metà da 666 soggetti): qui le metà sono molto più grandi, quindi i valori non sono direttamente confrontabili.

**Da dove vengono i dati.** Gli score sono la matrice del run; la matrice dei voxel è quella indicata da `input_path` nel `config.md` del run (si cerca a partire dalla cartella da cui si lancia l'app, cioè la radice del repo), con la sua maschera `non_constant_mask.npy` e la griglia del suo `reference_template_path`. Il pannello dice la causa invece della mappa se la matrice sorgente non esiste, **non è voxelwise** (parcellata, streamline, connettività funzionale: non hanno una mappa cerebrale) o **non ha gli stessi soggetti nello stesso ordine** del run (la regressione accoppia la riga i degli score con la riga i della matrice: un altro ordine darebbe una mappa dall'aspetto normale e sbagliata). Se la matrice sorgente è stata **modificata dopo la scrittura del run** compare un avviso: i soggetti coincidono, ma i valori potrebbero non essere quelli da cui sono nati gli score.

**La prima volta è lenta.** Le mappe si calcolano con un passaggio sulla matrice sorgente, **in background**: il pannello lo dice e si aggiorna da solo ogni 5 secondi, il resto dell'app resta usabile. Il risultato si salva in `<--cache-dir>/component_maps` e il nome della cartella dipende dal **contenuto** (gli score, i `subject_id`, forma, tipo e un campione di righe della matrice sorgente): una matrice corretta o un run nuovo ne genera una nuova invece di riusare una vecchia. Le cartelle non più usate non si cancellano da sole.

Dettagli di implementazione: `docs/dev/covariance_pca.md` (sezione "Component maps").

## Valutazione del clustering

Ultimo pannello della pagina, per un run di clustering. Dà gli **indici geometrici dell'intero run** (non del cluster scelto nel dropdown): quanto i cluster sono compatti e separati nello spazio su cui è stato fatto il clustering, con il rumore di HDBSCAN (`-1`) escluso. È la sezione 2 di `clustering_evaluation.ipynb`, calcolata nell'app.

Una tabella con valore e lettura di:

- **Silhouette** (da -1 a 1, più alta è meglio) in tre sintesi: media sui soggetti (pesa di più i cluster grandi), media dei cluster (ogni cluster pesa uguale) e **silhouette del cluster peggiore**. Per ogni soggetto confronta la distanza media dal proprio cluster con quella dal cluster più vicino: vicino a 1 cluster netti, vicino a 0 confini ambigui, negativo il soggetto è più vicino a un altro cluster che al proprio
- **Calinski-Harabasz** (più alto è meglio): dispersione tra i cluster divisa per la dispersione dentro i cluster
- **Davies-Bouldin** (più basso è meglio): 0 = cluster compatti e separati
- **Dunn** (più alto è meglio, sensibile agli outlier): distanza minima tra due cluster divisa per il diametro massimo di un cluster
- numero di **cluster** (rumore escluso), quota del **cluster più grande** e quota di **rumore**, sul totale dei soggetti

Sotto la tabella, **Silhouette per cluster**: una barra per cluster con la sua silhouette media (da -1 a 1), nel colore che il cluster ha nello scatter. L'etichetta di ogni barra porta la dimensione del cluster (`3 · n=412`), perché la media di pochi soggetti non è confrontabile con quella di centinaia: un cluster di un soggetto ha silhouette 0 per convenzione, e uno di 2 o 3 può avere una media estrema per caso. Passando il mouse su una barra compare la quota dei suoi soggetti con silhouette negativa, cioè più vicini a un altro cluster che al proprio. Serve a vedere quali cluster hanno confini ambigui anche quando la media complessiva è buona. L'icona fotocamera di Plotly esporta il PNG.

In fondo alla tabella, **Statistica del modello** (sezione 3 del notebook), la statistica propria del metodo del run:

| Metodo | Statistica | Lettura |
|---|---|---|
| `kmeans` | inertia | somma delle distanze al quadrato dai centroidi; più bassa è meglio, ma cala sempre al crescere di k, quindi serve a guardare *come* cala |
| `gmm` | BIC e AIC | verosimiglianza penalizzata per la complessità; più basso è meglio, il BIC penalizza di più |
| `agglomerative` | correlazione cofenetica e salto del dendrogramma al k del run | cofenetica: correlazione (0-1) tra le distanze vere tra soggetti e quelle dell'albero, più è alta più l'albero è fedele, non si confronta tra metriche diverse; salto: altezza della fusione da k a k−1 divisa per quella da k+1 a k, vicino a 1 non c'è un taglio naturale a k, più è alto più è netto |
| `hdbscan`, `hdbscan_soft` | quota di rumore e numero di cluster trovati | il numero di cluster è un risultato, non un parametro: molti cluster piccoli = parametri troppo permissivi, molto rumore = troppo restrittivi |

`kmeans`, `gmm` e `agglomerative` sono **rifittati** con i parametri del run e il valore è accettato solo se il rifit riproduce **esattamente** le etichette salvate (altrimenti, per esempio con `random_state` non fissato, descriverebbe un altro modello): in quel caso il blocco dice perché invece di mostrare un numero. `hdbscan` legge le etichette, senza rifit. `spectral`, `evidence_accumulation` e `adp` non hanno una statistica propria e il blocco lo dice (gli indici geometrici sopra valgono comunque). inertia e BIC/AIC non sono sulla stessa scala: non si confrontano tra metodi. Il rifit costa meno di 2 secondi su tutti i run provati e il risultato è in memoria per run. Se la tabella geometrica non è calcolabile (per esempio un solo cluster) la statistica del modello compare comunque.

Per i run `hdbscan` e `hdbscan_soft` il pannello aggiunge un blocco sull'**appartenenza** dei soggetti al proprio cluster. Le soglie (0,5) sono esempi: in letteratura non c'è un riferimento.

- **`hdbscan` - Posizione nel cluster** (sezione 3.1): HDBSCAN di sklearn è rifittato con i parametri del run e accettato solo se riproduce esattamente le etichette salvate. Per ogni cluster: numero di soggetti, probabilità media (`probabilities_`) e quota di soggetti sotto 0,5. La probabilità va da 0 a 1 ed è calcolata **dentro il cluster**: vicino a 1 il soggetto sta nel cuore, vicino a 0 sta al margine. **Non** è la probabilità di stare in questo cluster invece che in un altro, e non è confrontabile tra cluster di densità diversa. Su un UMAP con `min_dist` = 0 misura anche quanto UMAP ha impacchettato il cluster.
- **`hdbscan_soft` - Appartenenza ai cluster** (sezione 3.2): legge `membership.npy`, la matrice soggetti × cluster salvata con il run, senza rifit. Una tabella per cluster (soggetti, probabilità media nel proprio, quota sotto 0,5, altro cluster più probabile e la sua probabilità media), una **heatmap dei vettori medi** (righe: cluster dei soggetti, e "rumore"; colonne: cluster di appartenenza; la diagonale è la probabilità media nel proprio cluster, le celle fuori diagonale dicono quali cluster si sovrappongono) e i **10 soggetti meno saldi** nel proprio cluster, con l'altro cluster più probabile. Le righe non sommano a 1: la parte mancante è la probabilità di essere rumore, quindi 0,4 nel proprio cluster e 0,1 negli altri è un soggetto debole vicino al rumore, mentre 0,4 e 0,35 in un altro è un soggetto conteso tra i due. Non è confrontabile con la probabilità di `hdbscan`, che è un'altra implementazione e dice un'altra cosa.

Un blocco che non si può calcolare (rifit che non riproduce le etichette, run senza `membership.npy`, run con tutti i soggetti rumore) dice la causa e non nasconde il resto del pannello. I due blocchi costano da meno di un secondo a circa 2 secondi sui run provati e restano in memoria per run.

Se il rumore supera il 10% compare un avviso: gli indici descrivono solo i soggetti rimasti. Subito sotto il titolo del pannello, "Come leggere questi indici" (menu a tendina, chiuso di default) dice la direzione di ogni indice e i limiti della lettura: **nessuno ha un valore di riferimento**. Una nuvola senza cluster divisa da un algoritmo ha comunque una silhouette positiva, e Calinski-Harabasz, Davies-Bouldin e Dunn di un run solo non hanno una scala. Embedding diversi (2 o 10 componenti, lesion o sdc) non sono confrontabili tra loro. Gli indici assumono cluster compatti e convessi, quindi favoriscono `kmeans` e `gmm`: per gli altri metodi un valore basso non dimostra che i cluster siano sbagliati. La lettura sezione per sezione (compresa la silhouette per cluster, micro e macro) è in `docs/guides/evaluation.md`; le fasce della silhouette citate in letteratura sono in `knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md`.

### Run `adp`

`adp` clusterizza la distanza dice sulla matrice grezza, che gli indici euclidei sopra misurerebbero in un'altra geometria. Per questi run il pannello mostra invece (sezione 2.2 del notebook), tutti sulla **distanza dice** e sui soli soggetti clusterizzati:

- **Purezza dei 10 vicini**: la quota dei 10 soggetti più vicini che sta nello stesso cluster, accanto al valore **atteso a caso**. Un cluster con 10 soggetti o meno non può raggiungere 1: resta in tabella (colonna "Valutabile") ma fuori dal riassunto.
- **Silhouette sulla distanza dice**: media sui soggetti, media dei cluster, cluster peggiore, e le barre per cluster.
- **Coppie a distanza 1**: la quota di coppie senza voxel in comune. Va guardata prima della silhouette: se è alta (le lesioni: 84%) quasi tutte le distanze valgono 1 e la silhouette sta vicino a 0 qualunque sia la struttura, quindi si usa la purezza.
- **Cluster, rumore, soggetti in cluster piccoli, quota con pareggio** (soggetti con vicini a pari distanza), e una tabella con una riga per cluster.

La purezza è in parte circolare: adp forma i cluster proprio su questi vicini, quindi una purezza alta dice che i cluster sono coerenti, non che siano "veri". La silhouette non è confrontabile con quella euclidea dei run su embedding. Il rumore e i soggetti con la matrice tutta a zero (distanza non definita, etichettati `-1` da adp) sono esclusi.

**La prima volta è lenta.** La matrice delle distanze tra tutti i soggetti si calcola **in background**: circa 4 minuti per le lesioni, fino a circa 25 per il disconnettoma voxelwise (la `stream`, 87 colonne, qualche secondo). Il pannello lo dice e si aggiorna da solo ogni 5 secondi; il resto dell'app resta usabile. La matrice si salva in `<--cache-dir>/raw_distances` (default `results/cache/raw_distances`, circa 270 MB per matrice) e il nome della cartella dipende dal **contenuto** della matrice del run (forma, tipo, un campione di righe, i `subject_id`, la metrica): una matrice corretta ne genera una nuova invece di riusare una vecchia, e i run della stessa matrice la condividono. Le cartelle non più usate non si cancellano da sole. Una volta pronta la matrice, il pannello di un run costa pochi secondi.

Quando il pannello dice una causa invece dei numeri:

- **Run su una matrice con più di 1000 colonne** (`MAX_QUALITY_COLUMNS`), cioè su dato grezzo come i 221955 voxel della matrice lesionale: silhouette e Dunn leggono tutte le coppie di soggetti e non si calcolano qui; si fanno nel notebook.
- **Run non euclideo** (metrica o affinità diversa da euclidea, es. `cosine`): gli indici sarebbero calcolati nella geometria sbagliata.
- **Meno di 2 cluster** una volta tolto il rumore.

Il calcolo richiede da meno di un secondo a pochi secondi (5845 soggetti, 10 componenti: circa 4 s) e viene fatto una volta per run: il secondo passaggio sullo stesso run è immediato.

Dettagli di implementazione: `docs/dev/models.md` (`geometric_summary`).

## Salvare un grafico

Ogni plot interattivo ha un modo di salvarlo:

- **Scatter dell'embedding**: passandoci sopra col mouse compare un'unica icona nella modebar di Plotly (fotocamera, "toImage") - esporta un PNG dello stato attuale (run/colorazione correnti). Il resto della modebar di Plotly resta nascosto (stile minimale).
- **Ognuno dei 5 pannelli di anatomia**: "Salva HTML" scarica l'HTML autonomo del viewer (stesso file che il browser sta già mostrando nell'iframe), riapribile offline con l'interattività intatta. "Salva PNG" scarica invece un'immagine statica (`nilearn.plotting.plot_stat_map`, stessa soglia/colormap/colorbar del viewer interattivo) - utile per incollare la vista in un documento o una presentazione, dove l'interattività non serve.
- **Solo i 2 pannelli a singolo soggetto** ("Anatomia lesionale", "Disconnessione (SDC)"): un terzo bottone, "Salva PNG (glass brain)" - una singola silhouette trasparente del cervello (`nilearn.plotting.plot_glass_brain`) invece delle 3 fette piatte di "Salva PNG". Per la lesione usa `autumn` (stesso colore del viewer interattivo sopra - una maschera binaria non ha un gradiente da mostrare); per il disconnettoma usa `magma` con una soglia più alta (0.1 invece di ~0) e leggera trasparenza - una proiezione glass-brain somma il segnale lungo tutta la profondità del volume, quindi a soglia quasi zero il rumore di fondo diventa visibile come sottili striature scure.

---

## Stile

Font system-ui/-apple-system, sfondo bianco, nessun bordo "a scatola", modebar di Plotly nascosta, palette categorica CVD-safe già validata (`src.analysis.plotting._CATEGORICAL_PALETTE`), assi sottili senza griglia, `aspectmode="data"` in 3D (nessuna distorsione tra assi). Stessi token di design (colore testo, font stack, bordo cella) di `src.analysis.understanding_umap_report`'s `_CSS` - non importati direttamente (quel modulo ha un DOM completamente diverso, griglie/slider che questa app non ha), ma deliberatamente identici, così le due app Dash del repo restano un'unica famiglia visiva invece di due stili scollegati.

Colorazione continua (`volume`/`nihss`) con `log_scale=True` (solo `volume` oggi): i valori sono trasformati in log10 per il colore del marker, con i tick della colorbar rietichettati ai valori reali (`1`, `10`, `100`, ...) - Plotly Express non ha un asse colore log-scale diretto.
