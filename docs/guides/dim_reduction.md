# Guida alla Riduzione della Dimensionalità (Dim Reduction)

Questa guida descrive l'utilizzo della pipeline `dim_reduction.py`. Il suo scopo è comprimere una matrice di lesioni molto complessa estraendone le sole "caratteristiche matematiche salienti" (componenti principali o embedding), un passo essenziale per poter visualizzare grafici a dispersione o eseguire clustering.

- **Script**: `src/pipeline/dim_reduction.py`
- **Configurazione**: `config/pipelines/dim_reduction.json`

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione.
```bash
sbatch jobs/run_dim_reduction.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`:
```bash
python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json
```

---

## Cos'è la Riduzione della Dimensionalità?

Immagina una matrice *Voxel-wise*: ogni paziente è definito da centinaia di migliaia di voxel. Non è possibile graficare 800.000 assi. Gli algoritmi di riduzione riassumono il paziente in 2, 3 o più "coordinate". Se chiedi 2 coordinate, puoi visualizzare ogni paziente su un grafico X/Y. Pazienti clinicamente o strutturalmente simili si troveranno vicini.

---

## Modalità di Funzionamento

### 1. Modalità Fine-Tuning (`"fine_tuning": true`)
Gli algoritmi (come UMAP o t-SNE) richiedono parametri non universali, come `n_neighbors`. **Non esiste un valore giusto a priori.** 
In modalità Tuning, lo script esegue esperimenti su una griglia di combinazioni (*grid search*) elencate in `config/registry/params_reduction.json`, producendo tabelle e grafici di affidabilità (Trustworthiness).

- **Parametri Nested (`nested_params`)**: Con molteplici parametri (es. UMAP ha metric, n_components, n_neighbors...), la visualizzazione esploderebbe. Il registry permette di specificare `nested_params`. I parametri primari (es. la metrica) generano sottocartelle, e il grid visuale (`embeddings_grid_unico.png`) viene mostrato solo sulle 1 o 2 variabili libere rimanenti. **Regola**: nessuna combinazione a più di 2 componenti viene mai rifittata/mostrata in questo grid, né come PNG né come HTML — se `n_components` è tra i `nested_params` e la sottocartella corrisponde a un valore diverso da 2, quella foglia non riceve nessun file; se `n_components` è invece un parametro libero (variato dentro una foglia), solo le singole combinazioni con `n_components != 2` vengono scartate, le altre restano. Per vedere davvero una combinazione a più componenti (in 3D, interattivo) c'è `src/pipeline/plot_tuning_embedding_3d.py`, da lanciare a mano — vedi `docs/guides/embedding_app.md`. Stessa logica in Produzione: con `viz_n_components: 3` non viene scritto nessun PNG/HTML statico — l'esplorazione 3D è sempre e solo `src.pipeline.embedding_app`, l'app Dash live.

- **Valutazioni (`tuning_evaluations`)**: il blocco della config elenca, una chiave per meccanismo, tutto ciò con cui il tuning viene valutato. Valutazioni oggi disponibili:

  | Chiave | Tipo | Cosa fa |
  | :--- | :--- | :--- |
  | `trustworthiness` | punteggio dello sweep | la qualità di ogni combinazione per `umap`/`tsne`/`pacmap`: la colonna di `tuning_results.csv`. Il parametro `trustworthiness_n_neighbors` sta in `params_file` |
  | `cumulative_explained_variance` | punteggio dello sweep | lo stesso per `pca` (con o senza rotazione) |
  | `plot_hdbscan` | sugli embedding | HDBSCAN su ogni combinazione, nello spazio dell'embedding stesso, disegnato su un embedding 2D. Impostazioni: `min_cluster_size`, `min_samples` (entrambe obbligatorie) |

  Il punteggio dello sweep è sempre calcolato e va dichiarato: il blocco deve contenere esattamente quello del `reduction_method` (`trustworthiness` per umap/tsne/pacmap, `cumulative_explained_variance` per pca), altrimenti la pipeline si ferma **prima** dello sweep. Il blocco serve solo in `fine_tuning: true`; in produzione resta richiesto (può essere `{}`) e non ha effetto.

  `plot_hdbscan` disegna un embedding con più di 2 componenti sul suo **gemello 2D**: l'embedding con gli stessi iperparametri e `n_components=2`, che è un fit a sé, mai un taglio delle prime colonne. Per questo la griglia deve contenere `n_components: 2`; senza, la pipeline si ferma prima dello sweep. I colori dei cluster valgono dentro un solo subplot (HDBSCAN numera i cluster a caso), il grigio è il rumore.

  Le valutazioni sugli embedding si possono rilanciare in un secondo momento su un tuning già salvato, senza rifare lo sweep: [`evaluate_tuning_embeddings.md`](evaluate_tuning_embeddings.md).

### 2. Modalità Produzione (`"fine_tuning": false`)
Dopo aver scelto i parametri nel tuning, salvarli nel registry. L'avvio in modalità produzione elaborerà il file finale da usare nei passaggi successivi.

---

## Dettaglio Parametri JSON (`dim_reduction.json`)

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`project`** | *Stringa* | Nome del progetto (es. `"clinical_connectome"`). |
| **`input_path`** | *Stringa* | Percorso della matrice di output generata dal *Matrix Building*. DEVE esistere. |
| **`reduction_method`** | *Stringa* | L'algoritmo da usare. Valori: `"umap"`, `"tsne"`, `"pca"`, `"pacmap"`. |
| **`params_file`** | *Stringa* | Il percorso al registro logico: `"config/registry/params_reduction.json"`. |
| **`output_root`** | *Stringa* | Cartella per i risultati (es. `"results/lesion/dim_reduction"`). |
| **`session_name`** | *Stringa* | Nome dell'esperimento (es. `"umap_test_1"`). |
| **`overwrite`** | *Booleano* | Se `true`, sovrascrive esecuzioni preesistenti aventi lo stesso nome. |
| **`fine_tuning`** | *Booleano* | Attiva/disattiva il *grid search* dei parametri. |
| **`viz_n_components`** | *Intero (2 o 3)* | Dimensioni fisse del plot grafico, anche se la compressione vera è a più dimensioni. Evita distorsioni di "taglio". A `3`, fornisce solo l'HTML interattivo ruotabile. |
| **`color_by`** | *Lista* | Genera plot colorati per specifici tag: `"dataset"`, `"side"`, `"volume"`, `"nihss"`. |
| **`save_tuning_embeddings`** | *Booleano* | Se `true`, salva in `embeddings.npz` l'embedding effettivo di **ogni** combinazione valutata nel Fine-Tuning (non solo quelle mostrate in `embeddings_grid_*.png`), più un `metadata.csv` autosufficiente accanto — vedi sotto. Opt-in, `false` di default: nessuna run precedente all'introduzione di questo campo ha mai scritto questi file. |
| **`tuning_evaluations`** | *Oggetto* | Le valutazioni applicate al tuning, una chiave per meccanismo (vedi sopra). Obbligatorio, anche in produzione dove non ha effetto. |
| **`precompute_distance_metric`** | *Booleano* | Solo per la modalità **Produzione** (`fine_tuning: false`) — nessun effetto in Fine-Tuning. Se `true` (consigliato, comportamento di tutte le run prima dell'introduzione di questo campo), per `metric` in `jaccard`/`dice`/`euclidean` precalcola l'intera matrice di distanze una volta sola invece di farlo ricalcolare da UMAP/t-SNE ad ogni fit — molto più veloce, e garantisce ricerca dei vicini *esatta* indipendentemente dal numero di soggetti. Se `false`, passa la metrica grezza direttamente a UMAP/t-SNE (nessun precompute) — comportamento "standard" identico a un run UMAP/t-SNE esterno senza questo meccanismo, utile per confrontabilità con la letteratura. Nota: sopra i 4096 soggetti (soglia interna, non documentata, di `umap-learn`) i due modi danno risultati **diversi** (esatto vs approssimato) — sotto i 4096 sono equivalenti. Vedi `docs/debugging/debug_25_08_26.md`. |

---

## Il metodo `pca`

Tutte le scelte sono parametri della voce `pca` di `config/registry/params_reduction.json` (e di `params_reduction_sdc.json`), dentro `"params"`. Una chiave o c'è con un valore o manca: un `null` viene rifiutato, e una chiave sconosciuta o mancante ferma la run con un errore che la nomina.

| Parametro | Valori | Cosa decide |
| :--- | :--- | :--- |
| **`solver`** | `"blocks"`, `"sklearn"` | `blocks` legge la matrice un blocco di colonne alla volta e regge matrici che non entrano in memoria (il disconnettoma voxelwise, 6,8 GB); `sklearn` usa `sklearn.decomposition.PCA` su una copia in memoria, per matrici piccole e per controlli. Con `blocks` la matrice resta su disco (`np.memmap`). |
| **`standardize`** | `true`, `false` | `false`: PCA sulla covarianza, ogni colonna è solo centrata. `true`: PCA sulla correlazione, ogni colonna è anche divisa per la sua deviazione standard; una colonna costante ferma la run. La covarianza è la scelta quando le variabili sono nella stessa unità e una variabilità maggiore è informazione vera (come per un disconnettoma). |
| **`dual`** | `true`, `false` | Solo `blocks`, obbligatorio. `true` parte dalla matrice soggetti × soggetti (PCA duale, o metodo degli snapshot), `false` dalla covarianza tra variabili. Danno gli stessi risultati; conviene la matrice più piccola. |
| **`rotation`** | `"none"`, `"varimax"`, `"quartimax"`, `"equamax"`, `"oblimax"`, `"geomin_ort"` | `none` dà i punteggi delle componenti, ordinati per varianza. Le altre sono rotazioni ortogonali di `factor_analyzer`: i punteggi si ottengono per regressione multipla sui pesi ruotati, tutti con varianza 1 e senza più un ordine per varianza. Le rotazioni oblique non sono supportate. Solo `blocks`. |
| **`rotation_max_iter`** | intero | Obbligatorio con una rotazione (500 come nel paper di Thiebaut de Schotten et al. 2020). |
| **`n_components`** o **`variance_share`** | intero, oppure quota in (0, 1] | Quante componenti tenere: un numero fisso, oppure il numero minimo che raggiunge la quota di varianza (con `0.9`, qualunque sia il numero di componenti che servono). Esattamente uno dei due. |
| **`chunk_columns`**, **`max_matrix_gib`** | numero | Solo `blocks`, facoltativi: colonne per blocco (16384) e soglia in GiB oltre la quale la run si ferma invece di costruire la matrice quadrata (8). Non cambiano il risultato. |

**Con `solver: "sklearn"`** `dual`, `chunk_columns` e `max_matrix_gib` vanno tolti (si applicano solo a `blocks`) e `rotation` deve essere `"none"`.

**Come si sceglie `dual`.** Si usa la matrice più piccola: `true` quando le variabili sono più dei soggetti, `false` quando sono meno. Con la scelta sbagliata il risultato è lo stesso, ma costa molto di più o non entra in memoria (per `dual: false` su un disconnettoma voxelwise la matrice sarebbe di circa 680 GB, e la run si ferma prima).

| Sessione | Soggetti | Variabili | `dual` |
| :--- | :--- | :--- | :--- |
| `s1.4-vol` (lesione voxelwise) | 5845 | 221.955 | `true` |
| `s2.4-vol` (disconnettoma voxelwise) | 5845 | 291.345 | `true` |
| `s2.1-schaefer-200-tian-s2` (SDC parcellato) | 1119 | 232 | `false` |
| `s2.4-stream` (SDC per tratto) | 5831 | 87 | `false` |

**Fine-tuning.** Una griglia su `n_components`, `variance_share` o `rotation` fitta la decomposizione una sola volta: nessuno dei tre la cambia. Si rifitta solo per un nuovo valore di `standardize`, `dual` o `solver`. Il punteggio dello sweep è la quota di varianza spiegata dalle componenti tenute (una rotazione non la cambia). Una griglia su `variance_share` richiede che `n_components` non sia in `"params"`, e viceversa: con entrambi la run si ferma.

**Produzione.** `config.md` riporta in `Params used` il numero di componenti effettivamente tenute (`n_components`, accanto a `variance_share` se era quella la richiesta) e una riga "PCA kept N components"; l'intero spettro è in `eigenvalues.npy`. Il plot usa le prime `viz_n_components` componenti quando `rotation` è `"none"` (sono le direzioni che separano di più i soggetti); con una rotazione le colonne non hanno ordine, quindi `n_components` deve essere uguale a `viz_n_components` o la run si ferma.

---

## Output e Diari Storici

**I risultati di produzione e di tuning vivono in due rami separati sotto `output_root`, mai mescolati**: `results/lesion/dim_reduction/production/<metodo>/<Data>_<session_name>_<tag>` e `results/lesion/dim_reduction/tuning/<metodo>/<Data>_<session_name>`.

### In Modalità Produzione
- **`matrix.npy`**: La nuova matrice compressa.
- **`metadata.csv`**: L'anagrafica arricchita in automatico di `lesion_volume_voxels`, `lesion_side`, e `nihss`.
- **`eigenvalues.npy`** (solo `pca`): l'intero spettro di varianza, una voce per componente in ordine decrescente. È la curva da leggere per scegliere `variance_share`.
- **Plot Grafici**: Un `embedding_plot_unico.png` base (solo per embedding 2D — con `viz_n_components: 3` nessun PNG statico viene scritto, vedi sotto), più un PNG statico per ogni voce elencata in `color_by` (`embedding_plot_<voce>.png`). Non viene scritto un file `.html` interattivo per-run — l'esplorazione interattiva 2D/3D con bottoni di colorazione è `src.pipeline.embedding_app` (`docs/guides/embedding_app.md`), un'app Dash live che legge qualunque run di produzione già scritto, non un file da rigenerare per ogni run.

### In Modalità Fine-Tuning
- **`tuning_results.csv`**: I punteggi matematici estratti per ogni esperimento.
- **`tuning_plot.png`** e **`embeddings_grid_*.png`**: I plot per visualizzare come cambia la compressione al variare dei parametri, organizzati per sottocartelle se si usa la struttura *nested*.
- **`hdbscan_grid_mcs<N>_ms<M>.png`** e **`hdbscan_results_mcs<N>_ms<M>.csv`** (se `plot_hdbscan` è nel blocco): uno per ogni foglia (`metric=.../n_components=.../`), o nella cartella del run se non ci sono `nested_params`. La griglia ha una riga per `n_neighbors` e una colonna per `min_dist`; ogni subplot riporta tutti i parametri UMAP della combinazione, il numero di cluster trovati e la frazione di rumore. Il CSV ha una riga per combinazione con `n_clusters_found` e `noise_fraction`. Le impostazioni di HDBSCAN stanno nel nome del file, quindi impostazioni diverse non si sovrascrivono.
- **`embeddings.npz`** (solo se `save_tuning_embeddings: true`): un unico file con l'embedding vero e proprio di ogni combinazione valutata, non solo quelle disegnate nei plot. Ogni array è indicizzato da una chiave leggibile tipo `"n_neighbors=15,min_dist=0.1"` (stessi nomi/valori delle colonne di `tuning_results.csv`) — si ricostruisce la chiave dai valori di una riga per recuperare il suo embedding, senza bisogno di un indice separato. Pensato per essere lo strato dati di un futuro plot interattivo (vedi `knowledge/dim_reduction_clustering/dim_reduction_tuning_guide.md`) che legge e basta, senza dover rifittare nulla.
- **`metadata.csv`** (stesso trigger, un solo file in cima alla cartella — non per foglia, stessi soggetti per tutto lo sweep): l'anagrafica arricchita, identica per schema a quella di produzione (`lesion_volume_voxels`/`lesion_side`/`nihss`). Serve perché i colori di `embeddings_grid_*.png` si calcolano al volo (join live col registro clinico, somma su `X`) — senza questo file, un plot futuro che legge solo `embeddings.npz` non avrebbe modo di sapere di chi è ogni punto o come colorarlo.

### I Diari di Bordo (Runs)
In cima a ciascun ramo (es. `results/lesion/dim_reduction/production/umap/` e `results/lesion/dim_reduction/tuning/umap/`) viene generato e alimentato in **append-only** un file:
- `production/<metodo>/runs.csv` per le esecuzioni di produzione.
- `tuning/<metodo>/runs_tuning.csv` per gli esperimenti di tuning.
Questa traccia storica evita la perdita della memoria sulle configurazioni sperimentate. Non sono da confondere con `docs/experiments/`, un file per sessione scritto a mano dall'umano.
