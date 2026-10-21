# Analizzare un tuning di clustering già salvato (`analyze_clustering_tuning`)

Calcola su un tuning di `clustering.py` già concluso ciò che lo sweep non scrive, senza rifare il clustering: legge `tuning_results.csv`, `clusterings.npz` e `config.md` della cartella della run e scrive i risultati accanto a quei file. Lesione e SDC allo stesso modo. ADP non è gestito (ha le sue diagnostiche: [`clustering.md`](clustering.md)).

- **Script**: `src/pipeline/analyze_clustering_tuning.py`
- **Configurazione**: `config/pipelines/analyze_clustering_tuning.json`

---

## Esecuzione

### 1. In locale
```bash
conda activate nemesis
python -m src.pipeline.analyze_clustering_tuning --config config/pipelines/analyze_clustering_tuning.json
```

### 2. Sul server (tramite SLURM)
```bash
sbatch jobs/run_analyze_clustering_tuning.sh
```

---

## Cosa serve

Una cartella di tuning scritta da `clustering.py` con `fine_tuning: true` e `save_tuning_clusterings: true` (senza `clusterings.npz` lo script si ferma). Le chiavi di `clusterings.npz` devono corrispondere esattamente alle righe di `tuning_results.csv`: una cartella riusata da una run con un'altra griglia non viene analizzata. Per agglomerative serve anche la matrice a cui punta `input_path` in `config.md`.

## Parametri JSON

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`tuning_dir`** | *Stringa* | La cartella della run, es. `results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_m_dice_nc2`. Il metodo si legge dal suo `config.md`. |
| **`overwrite`** | *Booleano* | Se `false`, lo script si ferma se uno dei suoi file esiste già; se `true`, li sostituisce. |
| **`evaluations_file`** | *Stringa* | Il file con i parametri delle valutazioni (di norma `config/registry/clustering_evaluations.json`): l'intervallo di k del salto del dendrogramma (`dendrogram_jump.k_range`) e il limite di rumore delle curve di HDBSCAN (`noise_filtered_curves.max_noise_fraction`, una scelta nostra). È lo stesso file che legge lo sweep di `clustering.py`. |
| **`tuning_evaluations`** | *Oggetto* | Quali valutazioni girano, con la stessa forma del blocco di `clustering.json`: `"general"` e una chiave per metodo, ciascuna una lista di nomi. Serve la chiave del metodo della run (lista vuota se nessuna). Nomi: `k_curves`, `cophenetic_correlation`, `dendrogram_jump`, `linkage_agreement` (agglomerative); `density_metrics`, `noise_filtered_curves` (hdbscan, hdbscan_soft). |
| **`write_report`** | *Booleano* | Se `true` scrive anche `report.md`. Il report legge dalla cartella i file delle valutazioni: se ne manca uno che gli serve (`cophenetic_correlation.csv`, `linkage_agreement.csv`, `dendrogram_jump.csv` per agglomerative; `density_metrics.csv` per HDBSCAN) lo script si ferma dicendo quale. |

Le stesse valutazioni girano anche alla fine di uno sweep, se `clustering.json` le elenca in `tuning_evaluations`: stessa funzione, stessi parametri, stessi file.

## Output

Nella cartella della run (rilanciare la pipeline del tuning con `overwrite: true` la ricrea da zero e questi file spariscono: si rilancia anche questa).

| Metodo | File | Contenuto |
| :--- | :--- | :--- |
| agglomerative | `cophenetic_correlation.csv` | Una riga per (`metric`, `linkage`) valido: correlazione tra le distanze vere e quelle dell'albero (da -1 a 1, vicino a 1 l'albero è fedele). Non si confronta tra `metric` diverse. |
| agglomerative | `dendrogram_jump.csv` | Una riga per (`metric`, `linkage`, `n_clusters`): altezza della fusione da k a k−1 divisa per quella da k+1 a k. Vicino a 1 non c'è un taglio naturale a k; più è alto, più il taglio è netto. |
| agglomerative | `linkage_agreement.csv` | Una riga per (`metric`, `n_clusters`, coppia di linkage): ARI tra le due partizioni (1 = identiche, 0 = quanto il caso). Dice dove i linkage danno la stessa partizione e dove no; non dice quale sia il giusto. |
| agglomerative | `k_curves_metric=<metric>.png` | Una figura per `metric`, senza `single`, con tre pannelli: silhouette su asse fisso (da -1 a 1), silhouette su asse adattato ai dati, Davies-Bouldin; una linea per linkage. Sui pannelli della silhouette le linee tratteggiate delle soglie della convenzione di Kaufman & Rousseeuw (1990) comprese nell'asse. Con `cosine` e `manhattan` Davies-Bouldin è vuoto e il suo pannello manca. |
| agglomerative | `k_curves_single_metric=<metric>.png` | Come sopra, solo per il linkage `single` (la sua silhouette scende molto sotto quella degli altri). Presente solo se la run ha `single`. |
| tutti | `report.md` | Le tabelle di `tuning_results.csv`, senza giudizi di merito. Agglomerative: una sezione per `metric` con le figure delle curve e, per ogni `linkage`, una tabella con silhouette, Davies-Bouldin e Calinski-Harabasz per `n_clusters`, seguita da punti che collocano la silhouette nelle fasce di Kaufman & Rousseeuw (1990), contano le silhouette negative e riportano il valore a k minimo e massimo. Poi, per ogni `metric`, la tabella del cophenetic (un valore per linkage), quella dell'accordo tra linkage (ARI, k in riga e una colonna per coppia di linkage), quella del salto del dendrogramma (k in riga, linkage in colonna) e i link ai dendrogrammi e alle etichette sul piano 2D che `clustering.py` ha scritto nella cartella (solo quelli presenti); Sotto ogni tabella e figura una riga "Come leggerlo" dice cosa mostra e cosa non dice, senza giudizi. Le fasce sono una convenzione di letteratura (non nostra) e descrivono la combinazione, non scelgono `n_clusters`. HDBSCAN e `hdbscan_soft`: i link alla heatmap di `clustering.py` (`tuning_plot*.png`) e alle curve con poco rumore (`noise_filtered_curves*.png`, se esistono) e una tabella per `min_samples` (una sezione per `cluster_selection_method` in `hdbscan_soft`), righe per `min_cluster_size`, con `n_clusters_found`, `noise_fraction`, `largest_cluster_share` e i tre indici (`hdbscan_soft` anche le tre misure di appartenenza); sotto, punti con le fasce della silhouette (calcolata sui soli soggetti non rumore), il rumore e il numero di cluster minimo e massimo. ADP: una tabella ordinata per silhouette decrescente. |
| hdbscan, hdbscan_soft | `density_metrics.csv` | `tuning_results.csv` più `n_clusters_found` (contato dalle etichette) e `largest_cluster_share` (sul totale dei soggetti, rumore compreso; vuoto se tutti i soggetti sono rumore). Sono misure: nessuna combinazione è classificata come buona o utilizzabile. |
| hdbscan, hdbscan_soft | `noise_filtered_curves[_<cluster_selection_method>].png` | Silhouette e Davies-Bouldin contro `min_cluster_size`, una linea per `min_samples`, solo le combinazioni con poco rumore. Se per un `cluster_selection_method` nessuna combinazione è sotto il limite (`leaf` non scende sotto il 15%), manca quel file e il log lo dice. |

Ogni lancio scrive un log in `logs/analyze_clustering_tuning/`.

---

## Notebook per leggere un tuning

Un notebook in `notebooks/post-results_analysis/` legge un tuning già salvato. Non rifà nessun tuning e non scrive nulla. Come leggere gli indici e i grafici: [`clustering_tuning_guide.md`](../../knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md).

### `dendrogram_embedding_explorer`

Segue l'agglomerative **k dopo k** su un tuning già eseguito. Passando da k-1 a k cluster esattamente un cluster si divide in due: per ogni k il notebook mostra dove stanno i due pezzi nell'embedding e che anatomia hanno, cioè la mappa di disconnessione per una run `sdc` e la mappa di sovrapposizione delle lesioni per una run `lesion`. Serve a capire da cosa è fatto il cluster grande mentre si spezza.

Legge `config.md`, `metadata.csv` e `clusterings.npz` della run, l'embedding a cui punta `input_path` (deve avere 2 colonne e gli stessi soggetti, nello stesso ordine, della run) e i file dei singoli soggetti su disco. Non scrive nulla. Dell'albero ricalcola solo la parte che serve, sull'embedding 2D (pochi secondi); la tipologia di mappa si decide da sola dalla cartella della run (`results/sdc/...` o `results/lesion/...`).

| Parametro | Significato |
| :--- | :--- |
| `RUN_DIR` | La cartella della run di tuning. |
| `LINKAGE`, `METRIC` | La combinazione da guardare. `ward` solo con `euclidean`. |
| `K_MIN`, `K_MAX` | Primo e ultimo numero di cluster da mostrare: per ogni k una coppia di figure. |
| `LAST_P` | Quante foglie ha l'albero troncato (al massimo 20, uno per colore). Deve essere almeno `K_MAX`, altrimenti il taglio spezzerebbe una foglia. |
| `MAP_THRESHOLD_FRACTION` | Quota del massimo di ciascuna mappa sotto cui non si colora (da 0 a 1, 1 escluso). Con `0.2` e un massimo del 76% dei soggetti si colorano i voxel sopra il 15%. |
| `CACHE_DIR` | Cache delle mappe dei singoli soggetti, la stessa dell'Embedding Explorer (`<--cache-dir>/binary_masks`, per default `results/cache/binary_masks`): un soggetto già visto lì non costa nulla qui, e viceversa. La prima volta costa qualche decina di millisecondi a soggetto; la prima esecuzione su molti soggetti può richiedere minuti. |

**Controllo di coerenza.** L'albero non è salvato nella run, quindi si ricalcola. Per ogni k da `K_MIN - 1` a `K_MAX` (da 2 in su) il taglio dell'albero si confronta con le etichette salvate per la stessa combinazione: l'ARI (*adjusted Rand index*, 1 = divisioni identiche, 0 = quanto il caso) deve essere esattamente 1, altrimenti il notebook si ferma. Controlla anche che ogni foglia stia dentro un solo cluster.

**Prima figura, per ogni k.** A sinistra l'albero troncato con le foglie `L1`, `L2`, ... (con il numero di soggetti) e la linea rossa del taglio a k; a destra l'embedding con esattamente k colori. Il titolo dice quale cluster si divide in quali due e a quale distanza di fusione. I cluster si nominano con le foglie che contengono (`L5–L6`): le foglie restano uguali a ogni k, mentre le etichette numeriche (0, 1, 2...) cambiano. Quando un cluster si divide, il pezzo più grande tiene il suo colore e il più piccolo ne prende uno nuovo; la legenda segna "nuovo" i due nati dall'ultima divisione. Convenzioni grafiche: [`plotting.md`](../dev/plotting.md).

**Seconda figura, per ogni k: la mappa anatomica.** Una riga per ciascuno dei due cluster nati dalla divisione: per voxel, la percentuale dei soggetti del cluster con quel voxel disconnesso (o lesionato). Per la disconnessione un voxel conta se la probabilità supera 0,5, la stessa convenzione dell'Embedding Explorer ([`embedding_app.md`](embedding_app.md)); la lesione è già una maschera. Tre sezioni (sagittale, coronale, assiale) sul template, tagliate sul voxel più acceso del cluster; dal rosso (appena sopra la soglia) al giallo (il massimo). La scala va dalla soglia al massimo di **ciascuna** mappa: si confrontano le zone, non il colore tra mappe diverse. Il massimo (in % dei soggetti) è nel titolo. Dettagli di calcolo: [`anatomical_maps.md`](../dev/anatomical_maps.md).

**Come leggerla.**

- Anatomie diverse tra i due figli (zone diverse accese): la divisione ha un significato anatomico.
- Mappe simili: la divisione separa soggetti simili per anatomia; si guarda se cambia solo la dimensione.

**Attenzione.**

- La mappa mostra solo tre fette: la parte del cluster fuori dalle fette non si vede. Se il massimo è basso (i soggetti si sovrappongono poco), il voxel su cui cadono le fette può rappresentare male il cluster.
- I soggetti senza file su disco sono esclusi dalla mappa, e il notebook scrive quanti sono.
- Il tipo di mappa si legge dalla cartella della run: una run fuori da `results/sdc/` e `results/lesion/` solleva errore.
