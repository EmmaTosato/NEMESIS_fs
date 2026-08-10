# Audit documentazione `docs/` — file temporaneo di lavoro

Non fa parte della documentazione stabile del progetto — da cancellare a fine revisione.
Per ogni file: cosa è confermato corretto, cosa è obsoleto/errato (con riferimento file:riga sia nel `.md` sia nel codice reale), cosa non è verificabile da questo Mac.

---

## `docs/guides/retrieval.md` — ✅ FATTO

## `docs/guides/datasets.md` — ✅ FATTO

---

## `docs/guides/atlas_building.md` — ✅ FATTO (2 discrepanze trovate e corrette il 10/08: riga 54 sullo schema di numerazione Glasser 1-180/181-186/1001-1180/1181-1186 invece di "361-372", riga 60 sull'esempio Value/Hemisphere sbagliato)

---

## `docs/guides/matrix_building.md`

**✅ Confermato corretto**
- Comando SLURM/locale, path script/config — combaciano con `jobs/run_build_lesion_matrix.sh`/`src/pipeline/build_lesion_matrix.py`.
- Esempio "Categoria 1 - Voxel-wise" (`parcellate:false, atlas_path:null, parcel_aggregation:null, save_parcellated_volumes:false`) — **verificato sul run reale** `data/derived/lesion_matrix/21-07_s1.1/config.md`: config identico nella sostanza, output reale **1150×254865** (la doc dice "es. 1000 righe e 800.000 colonne", ordine di grandezza coerente).
- `metadata.csv` con colonne `subject_id`/`dataset`, una riga per paziente — verificato sul file reale, match esatto.
- `group_filter`: sintassi e default di produzione `["ST"]` — confermato nel config reale.
- `reference_template_path` = tipicamente un soggetto WashU 2mm — confermato (già verificato nel file precedente).
- `resample_interpolation: "nearest"` obbligatorio per maschere binarie — coerente con l'uso reale in `src/features/lesion.py` (`resample_to_img(..., interpolation=resample_interpolation)`).
- `parcel_aggregation`: "supportiamo solo `fraction_lesioned`" — confermato, `PARCEL_AGGREGATIONS` in `src/features/lesion.py` ha esattamente una sola entry registrata.
- Validazione `atlas_path`/`parcel_aggregation` obbligatori se `parcellate:true`, vietati se `false` — confermato in `src/analysis/build_config.py::_validate_parcellation_fields`.
- `overwrite`: `false`→`FileExistsError` esplicito, `true`→sostituzione atomica (temp-dir+rename) — confermato in `src/utils/artifacts.py::save_matrix`, comportamento "cancella e ricrea" è corretto in sostanza.
- `non_constant_mask.npy` — descrizione (array booleano lungo quanto il cervello originale, colonne costanti scartate) coerente con `manifest.json` reale (`"extra_arrays": {"non_constant_mask": [902629]}` — lunghezza pre-drop).

**⚠️ Discrepanze/imprecisioni**
1. **Sezione "File di Input e di Output" (righe 98-106) — omissione**: l'elenco dei file di output **non menziona `manifest.json`**, che invece è presente in ogni run reale (verificato su `data/derived/lesion_matrix/21-07_s1.1/manifest.json`, generato sempre da `save_matrix` insieme a `config.md`). Mancano anche i dettagli sul suo contenuto (matrix_shape, dtype, metadata_columns).
2. **Riga 22 — nota fuorviante**: *"in locale userai probabilmente ... config/pipelines/build_lesion_matrix_local.json"* — questo file **non esiste** (verificato `ls config/pipelines/`, esiste solo `build_lesion_matrix.json`). A differenza della pipeline di retrieval (che ha davvero una coppia `_local`/`_server`), questa pipeline non ha alcuna convenzione di split locale/server — la frase è formulata in modo dubitativo ("probabilmente", "se hai adattato") quindi non è tecnicamente falsa, ma rischia di far credere che quella convenzione sia già stabilita anche qui.
3. **Nota di contesto (non un errore della guida, ma rilevante)**: il config **realmente committato oggi** (`config/pipelines/build_lesion_matrix.json`) non è nello stato "voxel-wise" mostrato come esempio nella Categoria 1 — è configurato con `"parcellate": true` e `"atlas_path": ".../fmriprep/atlas-Yan300TianS2Buckner7N/..."` (un atlante Yan-Tian-Buckner, non quello Glasser+Harvard-Oxford usato come esempio a riga 62), `"session_name": "yan300s1"`. Nessun output corrispondente esiste in locale (`data/derived/lesion_matrix/` ha solo `21-07_s1.1`, voxel-wise) — sembra una run pianificata/sul cluster, non ancora eseguita qui o i cui risultati non sono stati sincronizzati su questo Mac. La guida stessa non descrive questo stato specifico del config (ragionevole, dato che documenta il meccanismo generale, non lo stato del file in un dato momento) ma vale la pena saperlo per non sorprendersi rilanciando la pipeline col config committato as-is.

**❓ Non verificabile da qui**: nessuno oltre a quanto sopra.

---

## `docs/guides/fc_matrix_building.md`

**✅ Confermato corretto (in gran parte verificato su dati reali locali)**
- Script/config di entrambe le pipeline, comandi SLURM/locale — combaciano con `jobs/run_mask_fc.sh`/`run_build_fc_matrix.sh` e `src/pipeline/mask_fc.py`/`build_fc_matrix.py`.
- Nomi file di output di `mask_fc.py`: `<subject>_masked_fc.csv` + `mask_summary.csv` — confermati sia nel codice (`SUMMARY_FILENAME`, `f"{subject}_masked_fc.csv"`) sia sui file reali in `data/derived/features/masked_fc/Yan200TianS2Buckner7N/`.
- Output di `build_fc_matrix.py` (`matrix.npy`, `metadata.csv`, `manifest.json`, `edge_names.npy`) — confermato sui file reali in `data/derived/features/fc_matrix/Yan200TianS2Buckner7N/24-07_s2/` (manifest.json presente, shape 169×28441, `edge_names.npy` con notazione `NodoA__NodoB` come descritto altrove).
- `group_filter`: sintassi, `excluded_by_group` vs `missing_lesion` come dicitura distinta — confermato in `src/features/functional.py` (`missing_lesion`/`excluded_by_group` sono effettivamente due liste separate restituite da `discover_subject_files`).
- "La matrice finale contiene ancora NaN, nessuna imputazione" — **verificato sul dato reale**: `matrix.npy` di `Yan200TianS2Buckner7N/24-07_s2` ha davvero NaN (3.56% delle celle).
- "Connessioni costanti rimosse e loggate" — confermato, `drop_constant_edges()` esiste in `src/features/functional.py` esattamente con questo scopo.

**⚠️ Discrepanza (framing, non tecnica)**
- **Riga 60**: *"Soglia di esclusione paziente: nessun paziente viene ancora escluso ... va decisa guardando i mask_summary.csv reali su tutta la coorte"* — presenta la soglia come una decisione **ancora aperta**. Ma `.claude/stato_progetto.md` (sessione 2026-07-27) registra che questa decisione è stata **chiusa esplicitamente**: *"decisione presa in questa sessione — non si esclude nessun paziente, nessuna soglia implementata. Non è un lavoro rimasto da fare, è chiusa."* Il comportamento del codice è coerente in entrambi i casi (nessuna soglia implementata, verificato: nessun campo `exclusion_threshold`/simile in `src/`/`config/`) — quindi non è un bug funzionale, ma la guida presenta come "da fare" qualcosa che il progetto ha già deciso di **non fare mai**, il che potrebbe portare qualcuno a riaprire una discussione già chiusa.

**❓ Non verificabile da qui**: nessuno.

---

## `docs/guides/compute_sdc.md`

Nota di scope: pipeline non eseguibile/testabile in locale (`bcblib` solo sul cluster, per vincolo noto in `.claude/CLAUDE.md`) — verificato leggendo `src/sdc/*.py`/`src/pipeline/compute_sdc.py`/`jobs/*.sh` reali, mai eseguendo nulla.

**✅ Confermato corretto**
- Moduli citati (`src/sdc/{config,manifest,staging,runner,status,resample}.py`) e le tre modalità `manifest`/`run`/`aggregate` — combaciano con i file reali.
- Colonne `manifest.csv` (`subject_id, dataset, lesion_mask_path`) — confermato esattamente, `src/sdc/manifest.py::_MANIFEST_FIELDS`.
- Stati per-soggetto (`ok`, `failed_resample`, `failed_stage1_process`, `failed_stage1_check`, `failed_stage2_process`, `failed_stage2_check`, `dry_run`) — confermato esattamente, `src/sdc/status.py`.
- Griglia canonica di resampling MNI152NLin6Asym — confermato (`src/sdc/resample.py` docstring), coerente col riferimento a `debug_23_07_26.md`/pattern #13 di `lessons_learned.md`.
- Job SLURM citati (`run_compute_sdc_manifest.sh`, `run_compute_sdc.sh`, `run_compute_sdc_aggregate.sh`) esistono tutti in `jobs/`.
- Tutti i campi della tabella parametri (`project`, `file_patterns`, `datasets`, `group_filter`, `bcbtoolkit_path`, `tracks_dir`, `cores_per_subject`, `stage2_ebrains`, `stage2_presets`, `output_root`, `session_name`, `overwrite`, `run_notes`) — combaciano esattamente con `config/pipelines/compute_sdc.json` reale.

**⚠️ Discrepanze reali (2)**
1. **Righe 78-81 — path sbagliato**: la guida dice *"Vive in `scripts/`, non in `jobs/`, perché non passa da `sbatch`"* per `run_compute_sdc_no_slurm.sh`. **Falso**: il file oggi vive fisicamente in **`jobs/run_compute_sdc_no_slurm.sh`** (verificato `find`), non in `scripts/`. Causa trovata via `git log`: uno spostamento reale `scripts/`→`jobs/` è avvenuto il 28/07 (commit `4e112d8`, "nee job") - **né la guida né il commento header dello script stesso sono stati aggiornati** dopo lo spostamento (lo script contiene ancora testualmente "this script intentionally lives in scripts/, not jobs/"). Pattern da manuale del `lessons_learned.md` #12 (rename non propagato ovunque) - qui il rename non è stato propagato né alla doc né al file spostato stesso.
2. **Riga 40 — schema di `runs.csv` obsoleto**: la guida descrive le colonne come *"run_id, timestamp, run_type, params, output, notes"* — questo è lo schema **pre-refactor**. Lo schema reale oggi (`src/utils/run_log.py::FIELDNAMES`) è `["session", "id", "timestamp", "params", "output", "notes"]` (niente `run_id`/`run_type` — sostituiti da `session`+`id` separati, refactor di sessione 2026-07-27(3), esteso a `compute_sdc.py` proprio per chiudere questo gap secondo `.claude/lessons_learned.md` #12/`stato_progetto.md`). Il codice (`compute_sdc.py` importa e usa `append_run_log_entry` col nuovo schema) è corretto; solo la doc non è stata aggiornata di conseguenza.

**❓ Non verificabile da qui (richiede cluster/bcblib)**
- "stage2_ebrains: true usa tutti e 15 gli atlanti EBRAINS" — richiede `bcblib.tools.lesion_features._constants.EBRAINS_ATLAS_SPECS`, non installabile in locale (`ModuleNotFoundError` confermato, atteso).
- Comportamento dettagliato di Stage 1/2, dry-run reale, timing per-stage — nessuna esecuzione possibile qui.

---

## `docs/guides/dim_reduction.md`

**✅ Confermato corretto (ampia verifica di codice)**
- Comando SLURM/locale, path script/config — combaciano con `jobs/run_dim_reduction.sh`/`src/pipeline/dim_reduction.py`.
- 5 `reduction_method` (`umap`/`tsne`/`pca`/`pca_varimax`/`pacmap`) — confermati in `REDUCTION_METHODS`/uso reale.
- Meccanismo `nested_params`: validazione "1 o 2 chiavi libere dopo nested_params" — confermato esattamente in `src/analysis/params.py::load_nested_params` (messaggio d'errore identico nella sostanza).
- `viz_n_components`/`embedding_for_viz` (riuso se coincide con `n_components`, rifit altrimenti con stessi iperparametri, mai un taglio di colonne) — confermato in `src/analysis/reduction.py::embedding_for_viz`.
- `write_embeddings_grid` — campo booleano confermato in `src/analysis/model_config.py`.
- `color_by`/arricchimento metadata: `enrich_metadata_with_lesion_info` aggiunge **esattamente** `lesion_volume_voxels`/`lesion_side`/`nihss`, sempre, indipendentemente da `color_by` — confermato leggendo `src/features/clinical.py` (anche il docstring della funzione conferma letteralmente "regardless of which one was run").
- `regress_out_volume`: incompatibilità esplicita con `metric: jaccard/dice` — coerente con quanto già verificato nel contesto di sessione (`covariates.py::check_volume_regression_compatible`).
- `scripts/replot_dim_reduction.py --run-dir <cartella>`, rifiuto esplicito se l'embedding salvato non ha 2 componenti — confermato letteralmente nel codice (`raise ValueError` su `X.shape[1] != 2`).

**⚠️ Discrepanza reale (stesso pattern già trovato in `compute_sdc.md`)**
- **Righe 108-109 — sbagliate su due punti**: *"lo script compilerà ... runs.csv (una riga per run: `run_id, timestamp, run_type, params, output, notes`) ... se era un test di fine tuning o una produzione"*.
  1. **Schema colonne obsoleto**: lo schema reale (`src/utils/run_log.py::FIELDNAMES`, e verificato sull'header reale di `results/lesion/dim_reduction/{umap,tsne,pca,pacmap}/runs.csv`) è `session, id, timestamp, params, output, notes` — non esistono più le colonne `run_id`/`run_type`.
  2. **Struttura sbagliata**: la doc descrive **un solo file** `runs.csv` che distingue tuning/produzione con una colonna `run_type`. In realtà (confermato: `results/lesion/dim_reduction/umap/` ha sia `runs.csv` **sia** `runs_tuning.csv`) sono **due file separati** — produzione in `runs.csv`, fine-tuning in `runs_tuning.csv` — non menzionato affatto nella guida.
  - Nota collaterale (fuori scope docs/, solo per completezza): anche il docstring interno di `src/pipeline/dim_reduction.py` ("Both modes append an entry to .../runs.csv") e quello di `src/utils/run_log.py` ("without splitting them into separate files") sono anch'essi obsoleti rispetto al comportamento reale del codice nella stessa funzione (`file_name = "runs.csv" if run_type == "production" else "runs_tuning.csv"`) — il gap non è solo nella doc utente ma si ripete nei commenti sorgente.

**❓ Non verificabile da qui**: contenuto discorsivo/didattico (spiegazioni concettuali su cosa "significa" la riduzione dimensionale) — non tecnicamente falsificabile.

---

## `docs/guides/clustering.md`

**✅ Confermato corretto (ampia verifica di codice)**
- Comando SLURM/locale — combaciano con `jobs/run_clustering.sh`/`src/pipeline/clustering.py`.
- 5 metodi (`kmeans`/`agglomerative`/`gmm`/`hdbscan`/`spectral`) — confermati esattamente (5 funzioni `*_cluster` in `src/analysis/clustering.py`).
- Un solo parametro di tuning per metodo (`n_clusters` per kmeans/agglomerative/spectral, `n_components` per gmm, `min_cluster_size` per hdbscan) — confermato esattamente sul `config/registry/params_clustering.json` reale.
- Colonne extra per metodo (`kmeans`→`inertia`, `gmm`→`bic`/`aic`, `hdbscan`→`noise_fraction`) — confermato esattamente in `src/analysis/clustering_tuning.py::METHOD_METRIC_COLUMNS`.
- Diagnostica standalone solo per agglomerative (dendrogramma)/spectral (eigengap), nessuna per hdbscan — confermato (`STANDALONE_DIAGNOSTIC_METHODS = {"agglomerative", "spectral"}`).
- Consensus/stability clustering (`rsc`/`monti`, colonne `rsc_eigengap`/`monti_stability`, disattivato di default) — **implementato** (`src/analysis/consensus_clustering.py` esiste con `run_rsc_repeats`/`run_monti_repeats`/`compute_rsc_eigengap`/`compute_monti_stability`; era ancora "nessun codice scritto" secondo `stato_progetto.md` del 28/07 — evidentemente completato dopo). Nome file `consensus_suggestions.md` confermato in `src/pipeline/clustering.py`.
- `cluster_plot.png` "disegna solo le primissime due colonne" — confermato letteralmente (`X[:, :2]` usato direttamente in `src/pipeline/clustering.py`, più occorrenze) — a differenza del bug di `lessons_learned.md` #16 (che riguardava `dim_reduction`/`dim_reduction_clustering`), qui è un comportamento noto e correttamente **documentato come limite esplicito** dalla guida stessa (non c'è una matrice grezza da cui rifittare, essendo `clustering.py` disaccoppiato da qualunque riduzione), quindi non è un bug della doc.

**⚠️ Discrepanza reale (stessa classe di bug di `dim_reduction.md`)**
- **Riga 101**: *"esattamente come per `dim_reduction.py`... accumula una riga per ogni esecuzione, di produzione o di fine-tuning"* in un solo `runs.csv`. `clustering.py` usa la stessa funzione condivisa `append_run_log_entry` (`src/utils/run_log.py`) di `dim_reduction.py` — che **separa** produzione (`runs.csv`) e tuning (`runs_tuning.csv`) in due file distinti, non una singola tabella con colonna `run_type`. La frase "esattamente come per dim_reduction.py" è in un certo senso vera (stesso meccanismo, stesso errore) ma eredita la stessa imprecisione già trovata in `docs/guides/dim_reduction.md` — non è stato possibile verificare su output reale locale (`results/lesion/clustering/` non esiste su questo Mac, nessun run mai eseguito qui), ma la conclusione segue direttamente dal codice condiviso già verificato.

**❓ Non verificabile da qui**: nessun run reale di `clustering.py` presente in locale per un controllo end-to-end sui file di output.

---

## `docs/guides/dim_reduction_clustering.md`

**✅ Confermato corretto — file di alta qualità, anche più accurato dei due precedenti sullo stesso argomento**
- Comando SLURM/locale — combaciano.
- `viz_n_components` "dev'essere 2 qui, non è ammesso 3" — confermato: `src/pipeline/dim_reduction_clustering.py:114` ha un check specifico (`if config.viz_n_components != 2: raise ...`) più stringente del limite generico 2-o-3 di `model_config.py::_require_viz_n_components`.
- `metadata.csv` guadagna sempre `lesion_volume_voxels`/`lesion_side`/`nihss` in produzione (mai in tuning) — confermato, stessa funzione condivisa già verificata per `dim_reduction.md`.
- **`runs.csv` (riga 81, 85) — QUESTA guida lo descrive correttamente**: schema `reduction_method, clustering_method, session, id, timestamp, params, output, notes` — confermato esattamente (`extra_columns={"reduction_method":..., "clustering_method":...}` in `src/pipeline/dim_reduction_clustering.py`, prependuto a `FIELDNAMES`). E dichiara esplicitamente **due file separati** (`runs.csv` produzione / `runs_tuning.csv` tuning, riga 85: *"non `runs.csv`, riservato alla produzione"*) — a differenza di `docs/guides/dim_reduction.md` e `docs/guides/clustering.md`, che invece descrivono erroneamente un unico file con colonna `run_type` (vedi le due voci sopra). Questo file è la fonte corretta; gli altri due andrebbero allineati a questo.
- Struttura output (`<metodo_riduzione>/<metodo_clustering>/...`, cartella `comparison/` con prefisso `<reduzione>_<dd-mm>_...`) e nomi file (`cluster_plot.png`, `cluster_plot_interactive.html`, `silhouette_plot.png`, `cluster_comparison.png`, `cluster_comparison_interactive.html`) — coerenti con quanto già verificato nel contesto di sessione e con `clustering.md`.

**⚠️ Discrepanza reale**
- **Riga 52 — riferimento a una feature rimossa**: elenca *"... dendrogramma/eigengap/**k-distance** a seconda del metodo"* tra le diagnosi disponibili in fine-tuning. `k-distance` **non esiste più nel codice** (`grep -rn "k_distance"` su tutto `src/`: zero occorrenze) — era il diagnostico per DBSCAN, rimosso insieme a `compute_k_distance`/`plot_k_distance` quando DBSCAN è stato sostituito da HDBSCAN (sessione 2026-07-29, vedi `.claude/stato_progetto.md`). Riferimento residuo mai ripulito — esattamente il caso che `code_standards.md` §7 segnala come "peggio di nessuna doc".

**❓ Non verificabile da qui**: nessun run reale di questa pipeline presente in locale per un controllo end-to-end diretto sui nomi cartella (`<dd-mm>_<session>_<reduction_tag>_<clustering_tag>`) — verosimile per coerenza con gli schemi già visti altrove, non riverificato byte-per-byte qui.

---

## `docs/dev/retrieval.md`

File molto denso e per lo più eccellente (spiega bene *perché*, non solo *cosa*) — ma contiene l'errore più significativo trovato finora nell'intero audit, **internamente incoerente con se stesso**.

**✅ Confermato corretto**
- `KNOWN_OBJECTS = ("lesion", "feature")`, `_OBJECTS_REQUIRING_PIPELINE`/`_OBJECTS_FORBIDDING_PIPELINE`, profondità variabile 3 vs 2 livelli — confermato in `src/retrieval/config.py`.
- `KNOWN_GROUPS`: qui la doc elenca correttamente **tutti e 4** i gruppi (`ST, HC, PD, GM`, riga 228) — a differenza di `docs/guides/retrieval.md` che ne omette 2 (vedi sopra). Questo file è la fonte corretta.
- Layout output pipeline-first, `output_layout.local_relative_path`/`local_dataset_root` — combacia esattamente col codice (già verificato per `docs/guides/retrieval.md`).
- Percorso `assets/dataset_summaries/data_summary__<dataset>.csv`, non timestampato, non annidato per progetto — confermato sui file reali (`ls assets/dataset_summaries/`).
- `_reject_duplicate_retrieve_items`, `RetrieveItem.__post_init__` con `if/elif/else: raise` — confermato in `config.py`.
- Tabella STOP/WARNING/ERROR/FATAL — coerente con `retrieve_data.py` (già verificato in dettaglio per la guida utente).

**⚠️ Errore maggiore — conteggio/nomi atlanti FC-pearson, il documento si contraddiceva da solo — RISOLTO il 10/08**
Il registro reale (`config/registry/file_patterns_{server,local}.json`, contato a mano) ha **12 template Yan-based**: `Yan{100,200,300,400}TianS{1,2,3}Buckner7N`.
- Righe 91, 128, 346 descrivevano **15 template Glasser+Schaefer-based**, un registro mai esistito sul disco reale (nessuna traccia di "Glasser"/"Schaefer" in `file_patterns_server.json`; via `git log` il registro usa Yan almeno dal 21/07, mai cambiato da allora). Righe 275, 304 dicevano invece correttamente "12", senza nominare gli atlanti — il documento era quindi incoerente al proprio interno (3 punti dicevano 15/Glasser-Schaefer, 2 dicevano 12).
- **Fix applicato**, su indicazione esplicita dell'utente di non "bloccare" di nuovo un numero/nome specifico che potrebbe ricambiare in futuro: le 3 righe sbagliate sono state corrette per riflettere lo stato Yan-based di oggi, ma **formulate come puntatori al registro** ("vedi `file_patterns_server.json` per la lista corrente, questo insieme è già cambiato una volta ed è previsto possa ricambiare"), non come un nuovo conteggio fisso destinato a ridiventare stale alla prossima modifica dell'atlante.

**⚠️ Sezione "Known follow-up, not yet done" (riga 338) — completamente superata — RISOLTO il 10/08**
Entrambi i problemi descritti come "non ancora sistemati" erano **già risolti** nel codice (verificato su `tests/integration/test_resolution_counts.py` reale: `FILE_PATTERNS_PATH` punta già a `file_patterns_server.json`, e il test FC-pearson deriva i template dinamicamente dal registro invece di hardcodare nomi/conteggi). **Fix applicato**: sezione riscritta per documentare che è stata risolta, invece di restare descritta come lavoro ancora da fare.

**⚠️ Riga 7 — stesso errore già trovato nella guida utente — RISOLTO il 10/08**: *"`_local.json` (Windows path convention, for a laptop-mounted copy)"* era falso. **Fix applicato**: riformulato per non affermare "Windows", e per riflettere la decisione dell'utente che i due `retrieval_*.json` restano allineati per contenuto (stesso `datasets`/`group_filter`/`retrieve`), differendo solo nel puntatore al registro — coerente con l'allineamento di `retrieval_server.json` applicato in `docs/guides/retrieval.md`.

**❓ Non verificabile da qui / dato ambiguo (non ancora toccato, in attesa di nuova evidenza)**
- Riga 9: *"176/196 subject folders actually populated"* per WashU `features/` alla sorgente — la copia locale ha **225** cartelle `sub-*` sotto `features/` (verificato `ls`), un numero diverso da entrambi quelli citati. Non è una prova di errore (la copia locale non è necessariamente uno snapshot identico all'istante in cui questa cifra fu misurata, ed EBRAIN è "attivamente curato" per stessa ammissione della doc, riga 336) ma il numero citato non è più riscontrabile oggi con i dati disponibili — da ri-misurare se questa cifra serve ancora a qualcosa.

---

## `docs/dev/analysis.md`

File enorme (321 righe) e per la maggior parte di qualità eccellente — molto probabilmente il documento più denso e accurato dell'intero audit finora. Ma la sezione "Status" iniziale e la sezione `run_log.py` contengono errori chiari e verificabili, in netto contrasto con la cura del resto del file.

**✅ Confermato corretto (verifica estesa)**
- `REDUCTION_METHODS`/`CLUSTERING_METHODS` (5 e 5, nomi esatti) — confermato.
- `params["metric"]` di produzione: `umap` → `"jaccard"`, `tsne` → `"euclidean"` — confermato esattamente su `config/registry/params_reduction.json` reale.
- `PARCEL_AGGREGATIONS` con solo `"fraction_lesioned"` — confermato (già verificato per `matrix_building.md`).
- I 2 bug reali di `nilearn.NiftiLabelsMasker` (overflow `uint8`, parcel scomparso invece di leggere 0) — coerenti con `lessons_learned.md` #13 e `debug_23_07_26.md`, verificabili nel codice.
- Struttura output/nomi (`embeddings_grid_*.png`, `consensus_suggestions.md`, `CONSENSUS_ELIGIBLE_METHODS = {kmeans, gmm, spectral}`, `STANDALONE_DIAGNOSTIC_METHODS = {agglomerative, spectral}`, rimozione di `compute_k_distance`/`plot_k_distance`) — tutto confermato nel codice reale già ispezionato per i file precedenti.
- `data/SESSIONS.md` come unico path sotto `data/` non ignorato da git (`!data/SESSIONS.md`) — verificabile in `.gitignore`, coerente col resto del progetto.

**⚠️ Errore confermato #1 — riga 7, sezione "Status" (proprio quella che dichiara di essere sempre aggiornata)**
*"`feature` not currently registered in `config/registry/file_patterns_local.json`/`file_patterns_server.json`"* — **falso**: verificato che entrambi i file hanno oggi `{"lesion": ..., "feature": ...}` come chiavi di primo livello, con `feature.func.FC-pearson`/`motion`/`outliers` pienamente popolati (12 template Yan-based). Ironico dato che l'introduzione del file dichiara esplicitamente *"This file documents what is actually implemented today... not a restatement of the plan"*.

**⚠️ Errore confermato #2 — schema `runs.csv`, ripetuto 3 volte nello stesso file (righe 110, 211, 220)**
Il file descrive esplicitamente e più volte, con motivazione dettagliata, che produzione e tuning finiscono **nello stesso file** `<output_root>/<method>/runs.csv`, distinti solo da una colonna `run_type` (*"the point is seeing... in one place, not two separate histories to cross-reference"*, riga 110). Questo **contraddice il codice reale** già verificato (`src/utils/run_log.py`: `file_name = "runs.csv" if run_type == "production" else "runs_tuning.csv"`, più gli header reali `session,id,timestamp,params,output,notes` senza `run_id`/`run_type` su `results/lesion/dim_reduction/*/runs.csv`). È lo stesso errore già trovato in `docs/guides/dim_reduction.md`/`docs/guides/clustering.md`, ma qui è più esteso: l'intera sezione "`src/utils/run_log.py`" (righe 106-114) descrive un design (`FIELDNAMES` include `run_id`/`run_type`, un solo file) che il codice reale ha da tempo sostituito con lo split `runs.csv`/`runs_tuning.csv` — `docs/guides/dim_reduction_clustering.md` (verificato sopra) ha invece la descrizione corretta.

**⚠️ Righe 318-319 — framing "non ancora deciso" doppiamente stale, stesso pattern già trovato in `fc_matrix_building.md`**
*"A per-subject exclusion threshold... not yet run for real; only synthetic/small-sample data so far"*: falso su entrambi i punti.
1. `mask_fc.py` **è stato eseguito su dati reali** (169 soggetti WashU reali, `mask_summary.csv` con numeri reali — confermato già nel file precedente e in `stato_progetto.md` sessione 2026-07-25).
2. La decisione sulla soglia di esclusione è stata **chiusa esplicitamente** in sessione 2026-07-27 ("non si esclude nessun paziente, nessuna soglia implementata... non è un lavoro rimasto da fare, è chiusa") — non è più "not yet decided".

**❓ Non verificabile da qui**: dettagli implementativi minori (es. formule esatte di `compute_monti_stability`/RSC) — plausibili e ben referenziati alla letteratura (`papers/Zanola et al - 2026`), non riverificati matematicamente riga per riga.

---

## `docs/dev/design_patterns.md`

File breve, concettuale, e **interamente confermato corretto** — nessuna discrepanza trovata.

**✅ Confermato corretto**
- Pattern Strategy/Registry (`REDUCTION_METHODS`/`CLUSTERING_METHODS`/`PARCEL_AGGREGATIONS` come `dict[str, Callable]`) — confermato ripetutamente nei file precedenti.
- Boundary validation (`resample_interpolation` contro l'insieme esatto accettato da nilearn, `binarize_threshold` in `[0.0, 1.0]`) — confermato in `src/analysis/build_config.py`.
- Atomic write: *"`load_matrix` ... treats 'no manifest.json' as 'this artifact was never successfully built'"* — confermato esattamente: `load_matrix` (`src/utils/artifacts.py`) solleva `FileNotFoundError` se `manifest.json` è assente.
- Layered architecture: *"`src/analysis/build_config.py` importing `PARCEL_AGGREGATIONS` from `src/features/lesion.py` è una dipendenza discendente legale"* — confermato: `from src.features.lesion import PARCEL_AGGREGATIONS` è realmente presente in `build_config.py`.

**❓ Non verificabile da qui**: nessuno.

---

## `docs/methods/dimensionality_reduction.md`

**✅ Confermato corretto**
- `metric` di produzione: `umap`→`jaccard`, `tsne`→`euclidean` — confermato (già verificato più volte).
- `regress_out_volume`: incompatibile con jaccard/dice, oggi "no-op" perché `dim_reduction.json`/`dim_reduction_clustering.json` hanno entrambi `"regress_out_volume": false` — confermato sui config reali.
- `pca_varimax_embed`: richiede `n_components`/`rotation_max_iter` in `params`, solleva `ValueError` se mancanti o se `n_components < 2` — confermato esattamente in `src/analysis/reduction.py`.
- `pacmap`: parametri `n_neighbors`/`MN_ratio`/`FP_ratio` — confermato sul registro reale (`config/registry/params_reduction.json`).
- `binary_pairwise_distance` (Jaccard/Dice via `X @ X.T`, ~19 minuti→pochi secondi) — coerente con quanto già verificato per `docs/dev/analysis.md`.

**⚠️ Scoperta significativa (non un errore di questo file specifico, ma una lacuna che questo file — insieme ad altri 4 — non segnala)**
Il documento presenta `pca_varimax` come uno dei 5 metodi pienamente disponibili, con tanto di guida al fine-tuning (`n_components` vs. varianza spiegata, righe 44-53). **Ma `pca_varimax` non è più configurabile oggi**: `config/registry/params_reduction.json` (il file che sia questo documento sia `docs/guides/dim_reduction.md` indicano come "l'unico posto" da modificare) **non ha più una entry `pca_varimax`** — rimossa nel commit `b6d0434` (21/07/26, "feat: add interactive plotly embeddings, param tags, and replotting script") durante un riordino del file, mai più reintrodotta. Verificato: `python -c "json.load(open('config/registry/params_reduction.json')).keys()"` → `['tsne', 'umap', 'pacmap', 'pca']`, nessun `pca_varimax`. Se qualcuno oggi impostasse `"reduction_method": "pca_varimax"` in `dim_reduction.json`, `load_method_params`/`load_tuning_grid` solleverebbero `ValueError` (metodo non registrato).
- **Il codice supporta ancora pienamente il metodo** (`REDUCTION_METHODS["pca_varimax"] = pca_varimax_embed` esiste in `src/analysis/reduction.py`, coperto da test unitari — `tests/unit/test_reduction.py`/`test_tuning.py` — che però costruiscono i `params` a mano, mai leggendo `params_reduction.json`, motivo per cui la suite non ha mai rilevato la lacuna).
- **La stessa incoerenza appare, verificato con `grep -rl pca_varimax`, in altri 4 documenti**: `docs/dev/analysis.md` (sezione "Status", lo elenca tra i `REDUCTION_METHODS` "oggi"), `docs/guides/dim_reduction.md`, `docs/guides/dim_reduction_clustering.md`, `docs/knowledge/dim_reduction_tuning_guide.md` — nessuno dei quali segnala che il metodo, pur implementato e testato, non è raggiungibile da CLI/config reale al momento. Non ancora corretto retroattivamente nei report di quei file sopra in questo audit — segnalato qui come scoperta trasversale, valida per tutti loro.

**❓ Non verificabile da qui**: contenuto puramente concettuale (differenze PCA/t-SNE/UMAP/PaCMAP) — corretto per quanto di dominio pubblico, non fact-checkabile riga per riga contro il codice.

---

## `docs/methods/clustering.md`

**✅ Confermato corretto**
- Default reali del registro: `agglomerative.linkage: "ward"`, `hdbscan.min_cluster_size: 5`, `spectral.affinity: "nearest_neighbors"` — tutti confermati esattamente su `config/registry/params_clustering.json`.
- `CONSENSUS_ELIGIBLE_METHODS = {kmeans, gmm, spectral}`, colonne `rsc_eigengap`/`monti_stability`, `consensus_suggestions.md` — confermato (già verificato per `docs/guides/clustering.md`/`docs/dev/analysis.md`).
- HDBSCAN senza diagnostica standalone, `-1` riportato separatamente da "Clusters found" — confermato nel codice.
- Spiegazioni concettuali di ciascun metodo (KMeans/Agglomerative/GMM/HDBSCAN/Spectral) — corrette per quanto di dominio pubblico/letteratura citata (Campello, Moulavi & Sander 2013 per HDBSCAN, Tshimanga et al. 2025/Zanola et al. 2026/Monti et al. 2003/Șenbabaoğlu et al. 2014 per il consensus clustering).

**⚠️ Discrepanza reale**
- **Riga 7 — riferimento a un file inesistente**: *"...see `docs/guides/analysis.md` for when each script applies"*. Questo file **non esiste** (`docs/guides/` non ha alcun `analysis.md` — verificato `ls`); la guida più vicina per lo scopo descritto è probabilmente `docs/guides/dim_reduction_clustering.md` o una combinazione di `dim_reduction.md`+`clustering.md`. Link morto.

**❓ Non verificabile da qui**: nessuno oltre a quanto sopra.

---

## `docs/knowledge/fc_lesion_masking.md`

**✅ Confermato corretto**
- `find_compromised_nodes`: confronto stretto `parcel_coverage < min_coverage` — confermato carattere per carattere in `src/features/functional.py`.
- `min_coverage` obbligatorio, validato in `[0.0, 1.0]`, nessun default implicito — confermato (`_require_float_in_range(raw, "min_coverage", 0.0, 1.0)` in `build_config.py`).
- "239 nodi, 28.441 connessioni uniche" per `Yan200TianS2Buckner7N` — confermato (`edge_names.npy` reale ha shape 28441, verificato nel file `fc_matrix_building.md` sopra).
- "mediana 1, media 3.9" nodi compromessi su 169 pazienti — coerente con `stato_progetto.md` sessione 2026-07-25 (stessa cifra).
- Notazione `NodoA__NodoB`, doppio masker `NiftiLabelsMasker`, NaN non azzerato, verifica allineamento etichette prima di impilare — tutto confermato nei file precedenti.

**⚠️ Discrepanza reale — riga 82, stessa area della sezione "Non ancora deciso" già trovata stale altrove**
*"12 combinazioni di atlante sono disponibili... oggi solo `Yan200TianS2Buckner7N` è stata validata/usata sui dati reali"* — **non più vero**: verificato che `data/derived/features/masked_fc/` contiene oggi **tutte e 12** le combinazioni Yan-based, ciascuna con **169 CSV mascherati reali** (non solo cartelle vuote/scaffolding) — il lavoro "ripetere su le altre 11 combinazioni" indicato come prossimo passo in `stato_progetto.md` (sessione 2026-07-25) risulta completato, ma questo documento di teoria non è stato aggiornato di conseguenza.

**❓ Non verificabile da qui**: nessuno oltre a quanto sopra.

---

## `docs/knowledge/Siegel2016_Reproduction.md`

Documento diverso dagli altri: è per lo più una **sintesi fedele di un paper esterno** (Siegel et al. 2016), non una descrizione del codice NEMESIS — la maggior parte del contenuto non è "vera/falsa" rispetto al nostro codebase, ma rispetto al testo del paper stesso. Ho fatto uno **spot-check di fedeltà** sulla prima sezione (Results, "Abnormal FC Patterns") contro il markdown reale del paper, poi verificato i 2 punti dove il documento tocca davvero il progetto NEMESIS.

**✅ Fedeltà al paper — spot-check positivo**
Confrontato riga per riga contro `papers/nemesis/Siegel et al - 2016 - .../Siegel et al - 2016.md` reale: **132 pazienti + 31 controlli** iniziali, **21 esclusi per hemodynamic lag**, **11 pazienti + 4 controlli esclusi per motion**, campione finale **100 pazienti/27 controlli**, **324 ROI**/**13 reti** (Gordon et al.), **t=4.26, P=10⁻⁴** sul t-test omotopico, **P=0.26** per l'effetto motion nell'ANOVA — **ogni singolo numero verificato combacia esattamente** con il testo del paper. Alta fiducia che il resto del documento (non riverificato riga per riga per limiti di tempo, ~250 righe restanti) sia altrettanto fedele, data la densità e precisione di questi primi riscontri. Il documento segnala inoltre onestamente 3 "incongruenze di lettura" trovate nel paper stesso (L1 vs formula L2 nell'MTL, "eight" vs "five" domini, "seven models" vs 8 modelli attesi) — non verificate contro il paper (richiederebbe leggere le sezioni esatte citate), ma presentate con onestà come letture aperte, non spacciate per certezze.

**⚠️ Discrepanza reale — riga 3, citazione del path del paper obsoleta**
*"Fonte: `papers/Siegel et al - 2016 - .../markdown/_full.md`"* — questo percorso **non esiste più**: la cartella `papers/` è stata riorganizzata (verificato `ls papers/`: oggi solo `papers/nemesis/` e `papers/related/`, nessun paper direttamente sotto `papers/`) e il file estratto non si chiama più `markdown/_full.md` ma `<Nome Paper>.md` direttamente nella cartella del paper (verificato: `papers/nemesis/Siegel et al - 2016 - .../Siegel et al - 2016.md`, senza sottocartella `markdown/`). Coerente con una serie di commit recenti (`2026-08-05/06/07`, "papers: fact-check and correct all 19 nemesis paper summaries", "papers reorganization") successivi alla stesura di questo documento — e nota bene, questa stessa convenzione (`markdown/_full.md`) è quella descritta come attuale anche in `.claude/CLAUDE.md` stesso, che quindi risulterebbe anch'esso stale su questo punto specifico (fuori scope di questo audit, che riguarda solo `docs/`, ma segnalato per completezza).

**⚠️ Discrepanza reale, più rilevante — riga 259, sezione "Vincolo aperto per una riproduzione NEMESIS"**
*"Da `docs/guides/datasets.md`: **WashU (l'unico dataset con FC oggi) non ha `participants.tsv`/dati clinici** nel formato disponibile"* — **falso oggi, e falso anche nel documento che cita**: `docs/guides/datasets.md` (verificato per intero in questo stesso audit, sezione sopra) dice oggi l'esatto contrario — *"È fornito per tutti e 4 i dataset, inclusa **WashU** (verificato 27/07: ... 319 soggetti — nota precedente su questa pagina, che lo dava assente per WashU, era stale/errata)"* — e riporta persino le percentuali di copertura per singolo punteggio clinico (NIHSS 73%, ARAT 98%, ecc.), tutte **verificate su dati reali** in questo stesso audit. Il file `data/clinical_connectome/derivatives/UNIPD/WashU/participants.tsv` esiste realmente con 319 righe. Questo documento sta quindi citando una versione ormai superata di `docs/guides/datasets.md` (probabilmente la "nota precedente... stale/errata" a cui quel file stesso fa riferimento) — il "vincolo aperto" descritto qui non è più un vincolo reale nella forma indicata (WashU ha dati clinici disponibili, anche se non organizzati negli stessi punteggi compositi per dominio di Siegel et al.).

**❓ Non verificabile da qui**: il resto della sintesi del paper (Experimental Procedures, Discussion) — non riletto integralmente contro il testo originale per limiti di tempo, ma nessun segnale di inaccuratezza dato l'alto tasso di fedeltà nello spot-check.

---

## `docs/knowledge/dim_reduction_tuning_guide.md`

**✅ Confermato corretto**
- Tabella metriche per metodo (`umap`/`tsne`/`pacmap` → trustworthiness, `pca`/`pca_varimax` → varianza cumulativa spiegata) — confermato esattamente su `TUNING_METRIC_NAMES` reale in `src/analysis/tuning.py`.
- `trustworthiness_n_neighbors` come parametro distinto da `n_neighbors` sweeppato — confermato (già verificato per `docs/dev/analysis.md`).
- Fix del bug metric-aware (jaccard/dice valutati con la stessa metrica, non l'euclidea di default) — coerente con quanto già verificato su `evaluate_umap`/`evaluate_tsne`.
- Meccanismo `nested_params`/`embeddings_grid_*.png`, file di output (`tuning_results.csv`, `tuning_plot.png` solo senza `nested_params` e con 1 parametro libero, `config.md`) — tutto confermato nei file precedenti di questo audit.
- Riferimenti incrociati (`docs/guides/dim_reduction.md`, `docs/knowledge/umap_tsne_guide.md`) — entrambi i file esistono davvero.

**⚠️ Nota già segnalata altrove, ripetuta qui per coerenza**
- **Riga 15** elenca `pca_varimax` tra i metodi con tuning disponibile — stesso problema già documentato nella sezione `docs/methods/dimensionality_reduction.md` di questo audit: `pca_varimax` non ha più una entry in `config/registry/params_reduction.json` da fine luglio, quindi il suo tuning non è oggi eseguibile da CLI nonostante il codice/i test lo supportino ancora. Non un errore specifico di questo file — è il 5° documento (su 5 già noti) con la stessa lacuna non segnalata.

**❓ Non verificabile da qui**: nessuno oltre a quanto sopra.

---

## `docs/knowledge/clustering_tuning_guide.md`

**✅ Confermato corretto — nessuna discrepanza trovata, incluso un riscontro empirico specifico verificato sul dato reale**
- `_square_grid_shape`, `plot_dendrogram(..., truncate_last_p=30)`, `plot_eigengap` — tutti confermati esattamente in `src/analysis/plotting.py`.
- I 3 indici generici, colonne extra per metodo (`inertia` KMeans, `bic`/`aic` GMM, `noise_fraction` HDBSCAN) — confermato su `METHOD_METRIC_COLUMNS` reale (già verificato più volte in questo audit).
- HDBSCAN senza diagnostica standalone, motivazione (nessun `eps` singolo da leggere) — confermato.
- **Esempio empirico specifico verificato sul dato reale**: *"Silhouette preferisce un k diverso da Davies-Bouldin... es. con pacmap: Silhouette premia k=2, Davies-Bouldin premia k=6"* — controllato su `results/lesion/dim_reduction_clustering/pacmap/kmeans/tuning/25-07_s1.1_n5/tuning_results.csv` reale: silhouette massimo a k=2 (0.506, k=6 vicino a 0.504), davies_bouldin minimo (migliore) a k=6 (0.581 contro 0.746 di k=2) — l'esempio nella doc è **esattamente riscontrabile** sul CSV reale, non un'illustrazione inventata.

**❓ Non verificabile da qui**: nessuno.

---

# `docs/debugging/` — narrativa storica, criterio di verifica diverso

Questi file non descrivono lo stato attuale del codice — sono report di sessioni di debug passate. "Vero" qui significa: coerente con `.claude/lessons_learned.md` (che li cita come fonte), coerente con la storia git reale (funzioni/nomi citati devono essere esistiti davvero, anche se poi rimossi/rinominati), e internamente coerente — **non** deve corrispondere al codice di oggi, che nel frattempo è stato ampiamente rifattorizzato (es. `space`/`modality` di questi vecchi report sono diventati `datatype`/`suffix`, `native()`/`mni_mask()` sono spariti in favore di `resolve()`, la sezione "Ambiguous" del report è stata rimossa del tutto). Non mi aspetto quindi di trovare "bug nel codice attuale" qui — l'obiettivo è verificare che il racconto di ciò che successe sia fedele, non che descriva l'oggi.

## `docs/debugging/debug_09_07_26.md`

**✅ Confermato corretto**
- **Tutte e 7 le categorie di bug (§1-7) hanno un riscontro esatto in `.claude/lessons_learned.md`** (pattern #1-7, ciascuno con `debug_09_07_26.md` citato come fonte) — verificato incrociando testo per testo: descrizione dell'errore, criticità, e persino il dettaglio "2 istanze nella stessa sessione" per il pattern #5 (duplicati) combaciano esattamente tra i due documenti.
- **Grounding storico reale**: cercato con `git log --all -S"mni_mask"` e `-S"_parse_retrieve_item"` (pickaxe search, trova i commit che hanno introdotto/rimosso quella stringa) — entrambi i nomi di funzione citati nel report **sono realmente esistiti** nel codice in quel periodo, non inventati a posteriori. Coerente con l'affermazione della doc che oggi quelle funzioni non esistono più (sostituite da `resolve()` con la convenzione `datatype`/`suffix`).
- La sezione "Ambiguous" del report che il fix di §3 introduce ("si segnala esplicitamente l'ambiguità... mai risolta in silenzio") è coerente con quanto trovato in `docs/dev/retrieval.md` — che oggi dice esplicitamente *"There is no 'Ambiguous' category anymore"* — quindi quella sezione è stata introdotta qui e poi rimossa in un refactor successivo, non una descrizione ora falsa ma una fase intermedia reale della storia del codice.

**⚠️ Discrepanza reale (minore)**
- **Riga 100 — riferimento a un file che non esiste**: *"Skill generale estratta da queste categorie: `silent-failure-audit` (vedi `~/.claude/skills/silent-failure-audit/SKILL.md`)"* — verificato `ls ~/.claude/skills/`: quella cartella/skill **non esiste** oggi (il contenuto reale è `README.md`, `convert_paper`, `export_full_md`, `git_committer.md`, `paper_downloader` — nessuna traccia di `silent-failure-audit`). O la skill non è mai stata effettivamente creata dopo questa sessione, o è stata rimossa/rinominata in seguito senza aggiornare questo riferimento.

**❓ Non verificabile da qui**: i dettagli specifici del fix (es. il codice esatto di `RetrieveItem.__post_init__` di allora) — il commit esatto di quella sessione non è stato identificato/isolato, solo confermata l'esistenza storica dei nomi citati.

---
