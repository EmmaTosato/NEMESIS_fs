# Valutare un tuning di clustering (`evaluate_clustering_tuning`)

Esegue le valutazioni di un tuning di `clustering.py` (cophenetic, salto del dendrogramma, quota del cluster più grande, curve per k, ...) e scrive `report.md`, senza rifare il clustering. Lavora su un tuning già concluso: legge `tuning_results.csv`, `clusterings.npz` e `config.md` della cartella della run e scrive i risultati accanto a quei file. Lesione e SDC allo stesso modo. ADP ha solo il report (le sue diagnostiche: [`clustering.md`](clustering.md)).

## Dove girano le valutazioni

Le valutazioni e il report sono lo stesso codice in due punti di ingresso. Cambia solo da dove parte la run:

```
python -m src.pipeline.clustering   (fine_tuning: true)
  1. sweep                          -> tuning_results.csv, clusterings.npz
  2. clustering_tuning_evaluations  -> csv e png delle valutazioni
  3. clustering_tuning_report       -> report.md   (se write_report)

python -m src.pipeline.evaluate_clustering_tuning   (su un tuning già salvato)
  2. clustering_tuning_evaluations  -> csv e png delle valutazioni
  3. clustering_tuning_report       -> report.md   (se write_report)
```

- **Quali valutazioni girano**: le elenca il blocco `tuning_evaluations` del config, per metodo (`clustering.json` per lo sweep, `evaluate_clustering_tuning.json` a posteriori). Le impostazioni (l'intervallo di k del salto del dendrogramma) sono in `config/registry/clustering_evaluations.json`, lette dallo stesso file in entrambi i casi: stessi parametri, stessi file, stessi numeri.
- **Perché due ingressi**: con le valutazioni dichiarate in `clustering.json` hai tutto alla fine dello sweep; se poi cambi una soglia, aggiungi una valutazione o ritocchi un plot, rilanci solo questa pipeline sul tuning salvato, senza rifare lo sweep.
- **Dove sta il codice**: le valutazioni in `src/analysis/clustering_tuning_evaluations.py` (un registro, una voce per valutazione); il report in `src/analysis/clustering_tuning_report.py`, che non calcola nulla e legge i file della cartella.
- **Metodi coperti**: `agglomerative`, `hdbscan` e `hdbscan_soft`. `kmeans`, `gmm`, `spectral` e `adp` sono in stand by: questa pipeline rifiuta il loro tuning (`unsupported clustering_method`, tranne `adp`, che ha solo `report.md`), le colonne che il loro sweep scrive non si ricalcolano, e produzione e app li valutano come prima. Si riprendono dopo aver chiuso i tre metodi sopra.

- **Script**: `src/pipeline/evaluate_clustering_tuning.py`
- **Configurazione**: `config/pipelines/evaluate_clustering_tuning.json`

---

## Esecuzione

### 1. In locale
```bash
conda activate nemesis
python -m src.pipeline.evaluate_clustering_tuning --config config/pipelines/evaluate_clustering_tuning.json
```

### 2. Sul server (tramite SLURM)
```bash
sbatch jobs/run_evaluate_clustering_tuning.sh
```

---

## Cosa serve

Una cartella di tuning scritta da `clustering.py` con `fine_tuning: true` e `save_tuning_clusterings: true` (senza `clusterings.npz` lo script si ferma). Le chiavi di `clusterings.npz` devono corrispondere esattamente alle righe di `tuning_results.csv`: una cartella riusata da una run con un'altra griglia non viene analizzata. Le valutazioni che ricalcolano dalle etichette (`cophenetic_correlation`, `dendrogram_jump`, `density_metrics`, `internal_metrics`) servono anche la matrice a cui punta `input_path` in `config.md`.

## Parametri JSON

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`tuning_dir`** | *Stringa* | La cartella della run, es. `results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_m_dice_nc2`. Il metodo si legge dal suo `config.md`. |
| **`overwrite`** | *Booleano* | Se `false`, lo script si ferma se uno dei suoi file esiste già; se `true`, li sostituisce. |
| **`evaluations_file`** | *Stringa* | Il file con i parametri delle valutazioni (di norma `config/registry/clustering_evaluations.json`): l'intervallo di k del salto del dendrogramma (`dendrogram_jump.k_range`). Non ci sono limiti di rumore. È lo stesso file che legge lo sweep di `clustering.py`. |
| **`tuning_evaluations`** | *Oggetto* | Quali valutazioni girano, con la stessa forma del blocco di `clustering.json`: `"general"` e una chiave per metodo, ciascuna una lista di nomi. Serve la chiave del metodo della run (lista vuota se nessuna). Nomi: `k_curves`, `cophenetic_correlation`, `dendrogram_jump`, `linkage_agreement`, `largest_cluster_share`, `dunn_index` (agglomerative); `density_metrics`, `tuning_heatmaps`, `dbcv_curves` (hdbscan, hdbscan_soft); `internal_metrics` (agglomerative, hdbscan, hdbscan_soft). Girano nell'ordine in cui sono elencate: `density_metrics` prima di `tuning_heatmaps` e `dbcv_curves`, che ne leggono il file. |
| **`write_report`** | *Booleano* | Se `true` scrive anche `report.md`. Il report legge dalla cartella i file delle valutazioni: se ne manca uno che gli serve (`cophenetic_correlation.csv`, `linkage_agreement.csv`, `dendrogram_jump.csv`, `largest_cluster_share.csv`, `dunn_index.csv` per agglomerative; `density_metrics.csv` per HDBSCAN) lo script si ferma dicendo quale. |

Le stesse valutazioni girano anche alla fine di uno sweep, se `clustering.json` le elenca in `tuning_evaluations`: stessa funzione, stessi parametri, stessi file.

**`internal_metrics`** ricalcola dalle etichette salvate le colonne che lo sweep scrive in `tuning_results.csv` (`silhouette`, `calinski_harabasz`, `davies_bouldin` per agglomerative; `noise_fraction` per HDBSCAN) con le stesse funzioni dello sweep, e le riscrive nello stesso file lasciando intatte tutte le altre colonne (`membership_mean` e `persistence_mean` di `hdbscan_soft` nascono dal fit e non si ricalcolano). Sostituisce un file scritto dallo sweep, quindi gira **solo con `overwrite: true`**, altrimenti si ferma; la scrittura passa da un file temporaneo. Per questo non è nei config di default: per usarla si aggiunge il nome alla lista del metodo in `evaluate_clustering_tuning.json` e si mette `overwrite: true`, mettendola per prima, così le valutazioni che seguono (e il report) leggono i valori nuovi. Calinski-Harabasz e Davies-Bouldin valgono solo con la distanza euclidea: con un'altra metrica restano vuoti.

## Output

Nella cartella della run (rilanciare la pipeline del tuning con `overwrite: true` la ricrea da zero e questi file spariscono: si rilancia anche questa).

| Metodo | File | Contenuto |
| :--- | :--- | :--- |
| agglomerative | `cophenetic_correlation.csv` | Una riga per (`metric`, `linkage`) valido: correlazione tra le distanze vere e quelle dell'albero (da -1 a 1, vicino a 1 l'albero è fedele). Non si confronta tra `metric` diverse. |
| agglomerative | `dendrogram_jump.csv` | Una riga per (`metric`, `linkage`, `n_clusters`): altezza della fusione da k a k−1 divisa per quella da k+1 a k. Vicino a 1 non c'è un taglio naturale a k; più è alto, più il taglio è netto. |
| agglomerative | `linkage_agreement.csv` | Una riga per (`metric`, `n_clusters`, coppia di linkage): ARI tra le due partizioni (1 = identiche, 0 = quanto il caso). Dice dove i linkage danno la stessa partizione e dove no; non dice quale sia il giusto. |
| agglomerative | `largest_cluster_share.csv` | Una riga per combinazione (`n_clusters`, `linkage`, `metric`): la quota dei soggetti nel cluster più grande, sul totale dei soggetti. Dice se la partizione divide i soggetti o ne stacca pochi da un blocco unico; non dice se sia giusta. |
| agglomerative | `dunn_index.csv` | Una riga per combinazione: indice di Dunn (distanza minima tra due cluster divisa per il diametro massimo di un cluster; più alto è meglio). Vale solo con la distanza euclidea: con un'altra `metric` la cella è vuota. |
| agglomerative | `k_curves_metric=<metric>.png` | Una figura per `metric`, con una linea per linkage e due pannelli: silhouette e Davies-Bouldin. `single` non è disegnato (resta nelle tabelle). Gli assi sono quelli della run, uguali in ogni figura: l'intervallo dei dati di tutte le `metric` (senza `single`) con un margine dell'8%, arrotondato al decimo; il report ne scrive i valori. Con `cosine` e `manhattan` Davies-Bouldin è vuoto e il suo pannello manca. Una `metric` con soli linkage `single` non ha figura. |
| tutti | `report.md` | Le tabelle di `tuning_results.csv`, senza giudizi di merito. Agglomerative: una sezione per `metric` (con la riga che dice che Calinski-Harabasz, Davies-Bouldin e Dunn non sono definiti per una `metric` non euclidea) con le figure delle curve e, per ogni `linkage`, una tabella con silhouette, Davies-Bouldin, Calinski-Harabasz, Dunn e quota del cluster più grande per `n_clusters`, seguita da punti che contano le silhouette negative e riportano il valore a k minimo e massimo. Poi, per ogni `metric`, la tabella del cophenetic (un valore per linkage), quella dell'accordo tra linkage (ARI, k in riga e una colonna per coppia di linkage), quella del salto del dendrogramma (k in riga, linkage in colonna) e i link ai dendrogrammi e alle etichette sul piano 2D che `clustering.py` ha scritto nella cartella (solo quelli presenti); Sotto le curve, il cophenetic, l'accordo tra linkage, il salto, il dendrogramma e le etichette 2D (e sotto heatmap e curve di HDBSCAN) un riquadro "Come leggerlo" dice cosa mostra e cosa non dice, senza giudizi. Il report non usa le fasce di lettura della silhouette (Kaufman & Rousseeuw 1990): ne dice solo l'esistenza e rimanda a `knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md`. HDBSCAN e `hdbscan_soft`: i link alla heatmap (`tuning_plot*.png`) e alle curve (`dbcv_curves*.png`), se le rispettive valutazioni le hanno scritte, e una tabella per `min_samples` (una sezione per `cluster_selection_method` in `hdbscan_soft`), righe per `min_cluster_size`, con `n_clusters_found`, `noise_fraction`, `largest_cluster_share` e `dbcv` (`hdbscan_soft` anche `membership_mean` e `persistence_mean`); sotto, punti con il minimo e il massimo di DBCV, di rumore e di cluster trovati e le combinazioni con meno di 2 cluster (DBCV non definito). Silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn non sono calcolati: il report ne dà il motivo. ADP: una tabella ordinata per silhouette decrescente. |
| hdbscan, hdbscan_soft | `density_metrics.csv` | `tuning_results.csv` più `n_clusters_found` (contato dalle etichette), `largest_cluster_share` (sul totale dei soggetti, rumore compreso; vuoto se tutti i soggetti sono rumore) e `dbcv` (`src/analysis/dbcv.py`, sulla matrice di input della run; vuoto con meno di 2 cluster, mai 0). Sono misure: nessuna combinazione è classificata come buona o utilizzabile. |
| hdbscan, hdbscan_soft | `tuning_plot[_cluster_selection_method=<valore>].png` | La mappa di DBCV, rumore, quota del cluster più grande, numero di cluster e, per `hdbscan_soft`, probabilità media e persistenza su `min_cluster_size` × `min_samples`, da `density_metrics.csv`. |
| hdbscan, hdbscan_soft | `dbcv_curves[_cluster_selection_method=<valore>].png` | DBCV, rumore, quota del cluster più grande e numero di cluster contro `min_cluster_size`, una linea per `min_samples`. Tutte le combinazioni, nessun filtro sul rumore; un punto manca dove i cluster sono meno di 2. |

Ogni lancio scrive un log in `logs/evaluate_clustering_tuning/`.

La silhouette per cluster (media dei cluster, cluster peggiore) non è una valutazione del tuning: serve a guardare una run scelta, quindi sta nella produzione (`silhouette_per_cluster.csv`, `silhouette_plot.png`) e nell'Embedding Explorer. Nel tuning resta la silhouette media sui soggetti.

---

## Notebook per leggere un tuning

Un notebook in `notebooks/post-results_analysis/` legge un tuning già salvato. Non rifà nessun tuning e non scrive nulla. Come leggere gli indici e i grafici: [`clustering_tuning_guide.md`](../../knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md).

### `dendrogram_embedding_explorer`

Segue l'agglomerative **k dopo k** su un tuning già eseguito. Passando da k-1 a k cluster esattamente un cluster si divide in due: per ogni k il notebook mostra dove stanno i due pezzi nell'embedding e che anatomia hanno, cioè la mappa di sovrapposizione delle lesioni o quella di disconnessione, a scelta con `MAP_MODALITY`. Serve a capire da cosa è fatto il cluster grande mentre si spezza.

Legge `config.md`, `metadata.csv` e `clusterings.npz` della run, l'embedding a cui punta `input_path` (deve avere 2 colonne e gli stessi soggetti, nello stesso ordine, della run) e i file dei singoli soggetti su disco. Non scrive nulla. Dell'albero ricalcola solo la parte che serve, sull'embedding 2D (pochi secondi); il tipo di mappa lo sceglie `MAP_MODALITY`.

| Parametro | Significato |
| :--- | :--- |
| `RUN_DIR` | La cartella della run di tuning. |
| `LINKAGE`, `METRIC` | La combinazione da guardare. `ward` solo con `euclidean`. |
| `K_MIN`, `K_MAX` | Primo e ultimo numero di cluster da mostrare: per ogni k una coppia di figure. |
| `LAST_P` | Quante foglie ha l'albero troncato (al massimo 20, uno per colore). Deve essere almeno `K_MAX`, altrimenti il taglio spezzerebbe una foglia. |
| `MAP_MODALITY` | Quale mappa disegnare: `"lesion"` (lesione) o `"sdc"` (disconnessione). I cluster sono sempre quelli della run, quindi `"lesion"` su una run sdc mostra la lesione dei soggetti raggruppati per disconnessione. Con `None` si legge dalla cartella della run (`results/sdc/...` o `results/lesion/...`). |
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
- Con `MAP_MODALITY = None` il tipo di mappa si legge dalla cartella della run: una run fuori da `results/sdc/` e `results/lesion/` solleva errore. Un valore diverso da `None`, `"sdc"`, `"lesion"` solleva errore.
