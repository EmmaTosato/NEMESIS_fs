# Changelog dell'impianto di progetto

Decisioni su **come è organizzato il repo**: fonti di verità uniche, pipeline ritirate, convenzioni di naming, formati degli artefatti — con le alternative scartate.

**Cosa NON va qui**: la storia del codice (già in `git log`), lo stato attuale (`docs/`, al presente), i cambiamenti ai dati (`data_changelog.md`).

Voci in ordine cronologico inverso.

## 07-10-26 — `build_lesion_matrix`: eliminato il summary in `summaries/`, resta il `config.md` accanto alla matrice

**Cosa è cambiato**: la pipeline non scrive più `summaries/build_lesion_matrix/<project>/build_summary__*.md`. Restano il `config.md` nella cartella della matrice, il log in `logs/build_lesion_matrix/<project>/` e la riga in `runs.csv`. Rimossi `REPORTS_ROOT`, `_build_report`, `_write_report`; `REPORT_FILENAME_PREFIX` rinominata `LOG_FILENAME_PREFIX`, stesso valore (`build_summary`), perché i nomi dei log restino uguali a quelli delle pipeline sorelle.

**Perché**: richiesta dell'utente. Il summary era il `config.md` con la sola intestazione diversa (verificato con `diff` sulla run `s1.4-vol`): stesso contenuto in due posti, nessuna informazione in più.

**Alternativa scartata**: tenere il summary come copia indipendente dalla cartella dei dati. Il log di ogni run riporta già esclusi e corretti e vive fuori da `data/`, quindi una copia fuori dalla cartella della matrice non serve.

**Non fatto**: le altre pipeline con lo stesso meccanismo (`build_sdc_matrix`, `build_fc_matrix`, `mask_fc` e le altre che definiscono `REPORTS_ROOT`) producono ancora il loro summary. Le cartelle `summaries/build_lesion_matrix/` già scritte restano su disco, non più alimentate.

## 06-10-26 — `enrich_metadata`: `overwrite` + file delle celle protette al posto di `fill`

**Cosa è cambiato**: il flag `fill` di `config/pipelines/enrich_metadata.json` è eliminato. Al suo posto, due campi obbligatori: `overwrite` (`false` = append, scrive solo le celle vuote; `true` = riscrittura, sostituisce ogni cella in scope) e `protected_path` (un json `{"columns": [...], "subjects": [...]}`, oggi `assets/metadata/participants_protected.json`, vuoto; `null` = nessuna protezione). Una cella la cui colonna o il cui soggetto è elencato non viene mai scritta, né in append né in riscrittura, nemmeno se è vuota. La regola vale per **tutte** le colonne che la run scrive, comprese quelle copiate da `lesion_metadata.csv` e `sdc_metadata.csv`, che con `fill` venivano sempre sovrascritte. Valore in uso: `overwrite: true`, cioè lo stesso comportamento di `fill: false` che c'era prima. Codice: `src/pipeline/enrich_metadata.py` (`_apply`, `_check_write_rules`, `ProtectedCells`), 92 test in `tests/unit/test_enrich_metadata.py`.

**Perché**: richiesta dell'utente. `participants.csv` è un join ma anche un file in cui si possono correggere a mano colonne o soggetti, e `fill` copriva solo una parte dei casi (le colonne cliniche; le derivate erano un'eccezione cablata nel codice). Stesso nome e stesso significato di `overwrite` in `populate_metadata` e in `build_excluded_subjects`.

**Alternative scartate**: (a) un terzo flag `update` accanto a `fill`: `fill: false` già propagava le correzioni dei tsv, e nessun flag può sia propagare le fonti sia proteggere le celle ritoccate a mano, perché il file non registra quali lo siano; (b) un `mode` a due valori al posto del booleano: stesso contenuto di `overwrite`, ma un nome diverso da quello che le altre due pipeline già usano; (c) protezione per cella (soggetto × colonna): più casi da validare di quelli che servono.

**Conseguenze ancora vere oggi**: (1) in append una colonna derivata resta al valore vecchio se la maschera è cambiata: la run lo segnala a `WARNING` per colonna (valori esistenti diversi dal fresco) ma non lo corregge, serve `overwrite: true`; la regola "le colonne derivate si sovrascrivono sempre" non esiste più. (2) Con `overwrite: true` una cella vuota nella fonte svuota quella del registro, senza avviso: ciò che esiste solo nel registro va protetto. (3) `geometric_override_datasets` non vuota richiede `overwrite: true`; `lesion_side` e `lesion_side_source` si proteggono insieme. (4) Il commit `9eca847` contiene una versione intermedia di queste modifiche al codice, rilasciata prima che config, test e doc fossero allineati: il working tree successivo è quello coerente.

## 05-10-26 — `build_excluded_subjects`: modo predefinito append, `overwrite: true` per ricostruire dal solo config

**Cosa è cambiato**: la pipeline `build_excluded_subjects` (voce successiva) riscriveva il csv per intero a ogni run, quindi il config doveva contenere tutti i soggetti esclusi. Ora ha un flag obbligatorio `overwrite` nel config. Con `false` (valore in uso) il csv esistente resta com'è, comprese le righe aggiunte o tolte a mano, e le righe del config vengono **aggiunte**: una riga già presente per lo stesso soggetto, scope e motivo non si tocca (se il `value` calcolato dal config è diverso resta quello del file, con una nota nel log e nel report), lo stesso soggetto e scope sotto un altro motivo solleva, un file assente viene creato, uno con lo schema vecchio non si può estendere. Con `true` il csv è ricostruito dal solo config. Il validatore delle pipeline di matrice gira sempre, sul risultato, prima di sostituire il file.

**Perché**: richiesta dell'utente. Con la scrittura per intero il config diventava lungo e andava tenuto allineato al csv; così il csv, una volta scritto, resta tale, il config contiene solo i soggetti da aggiungere e per togliere una riga basta cancellarla dal csv. Stesso schema di `overwrite` in `populate_metadata`.

**Alternativa scartata**: il csv sempre derivato dal config (modo unico `overwrite`), che dava una sola fonte di verità ma obbligava a tenere nel config anche i soggetti già scritti.

**Conseguenza ancora vera oggi**: con `overwrite: false` la fonte di verità è il **csv**, non il config: un soggetto tolto dal config resta nel csv, e uno tolto dal csv a mano ricompare alla run successiva se è ancora nel config (conviene svuotare il config dopo l'uso). Con `overwrite: true` la fonte torna a essere il config e ciò che il csv conteneva d'altro è perso. Config attuale: le stesse 15 righe di HEAD, già nel csv (la run in append le salta); il csv è identico a HEAD.

## 05-10-26 — `excluded_subjects.csv` è generato da una pipeline, `build_excluded_subjects`, da un config che elenca i soggetti

**Cosa è cambiato**: nuova pipeline `src/pipeline/build_excluded_subjects.py` (+ `config/pipelines/build_excluded_subjects.json`, `jobs/run_build_excluded_subjects.sh`, `tests/unit/test_build_excluded_subjects.py`). Il config contiene, per ogni coppia (motivo, scope), gli ID dei soggetti esclusi e da dove viene il `value` (una colonna di `lesion_metadata.csv`, oppure una costante). La pipeline ricava `dataset` dal registro, controlla il risultato con `load_excluded_subjects` su un file temporaneo e sostituisce il csv in modo atomico. Il csv non si modifica più a mano. Config iniziale: le 15 righe di HEAD (1 `empty_mask` con scope `all`, 14 `all_zero_features` con scope `sdc-streamline`); la prima run ha rigenerato un file identico a HEAD.

**Perché**: l'ultima cella di `lesion_analysis` possedeva solo tre dei quattro motivi del file e lo riscriveva per intero, cancellando le righe che non conosceva (voce precedente, stesso giorno). Una pipeline che possiede **tutto** il file, con tutti i motivi nel config, elimina il problema alla radice: non c'è più nessun altro scrittore del csv, quindi nessuna fusione.

**Alternative scartate**: (a) pipeline che possiede solo i tre motivi di lesione e lascia il resto del csv: rimette in gioco la fusione, due scrittori sullo stesso file; (b) regole con soglie invece di ID espliciti: contraddice la scelta del 29-09 (`cf6e1fe`) di sostituire le soglie di qualità con una lista curata a mano. Per `all_zero_features` il `value` è la costante `0` (numero di feature non nulle, per definizione): calcolarlo vorrebbe dire aprire la matrice SDC.

**Conseguenza ancora vera oggi**: la decisione sta nel config, non nel csv. Aggiungere o togliere un soggetto = modificare `exclusions` e rilanciare la pipeline; una modifica a mano al csv viene persa alla run successiva. L'ultima cella di `lesion_analysis` non scrive: stampa i blocchi da incollare nel config (la voce successiva descrive la versione precedente, "solo stampa" delle righe CSV).

## 05-10-26 — L'ultima cella di `lesion_analysis` non scrive più `excluded_subjects.csv`: stampa le righe da incollare

**Cosa è cambiato**: la cella finale del notebook (l'unica di esplorazione che scriveva un file di produzione) riscriveva `excluded_subjects.csv` per intero con le sole liste `EXCLUSIONS`, che partivano vuote, e non conosceva la colonna `scope`. Ora calcola `dataset` e `value` per gli ID dati (tre motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, scope `all`) e **stampa** le righe CSV da incollare a mano; non legge né scrive il file.

**Perché**: il file ha 15 righe in HEAD, 14 delle quali (`all_zero_features`, scope `sdc-streamline`) non vengono da questa cella, che non conosce quel motivo: qualunque esecuzione le cancellava. È successo due volte (la seconda il 05-10-26 alle 10:30: il file è rimasto alla sola intestazione `subject_id,dataset,reason,value`, senza `scope`).

**Alternativa scartata**: una cella che fonde i propri tre motivi nel file esistente, con `CONFIRM_WRITE` e validazione prima di scrivere. Implementata e collaudata, ma più complessa di quanto serva: dipendeva dallo schema del file (sollevava finché il file non era ripristinato) e aggiungeva parametri da tenere a mente. Scartata su richiesta dell'utente a favore della sola stampa.

**Conseguenza ancora vera oggi**: il file `assets/metadata/excluded_subjects.csv` in lavoro ha ancora lo schema vecchio e nessuna riga (HEAD ne ha 15 con `scope`): il notebook non lo tocca più, quindi va ripristinato o riscritto a mano.

## 05-10-26 — Ritirate le pipeline di retrieval e di calcolo SDC; la regola di naming dei soggetti passa a `src/utils/subject_ids.py`

**Cosa è cambiato**:
- Eliminati `src/retrieval/` (config, dataset, output_layout, verify), `src/sdc/` (config, manifest, resample, runner, staging, status), `src/pipeline/retrieve_data.py`, `src/pipeline/compute_sdc.py` (~2850 righe), `src/atlases/` (solo un `__pycache__` residuo: la pipeline atlas era già stata ritirata il 25-08-26).
- Config: `config/pipelines/{retrieval_server,retrieval_local,retrieval_sdc,compute_sdc}.json`, `config/registry/file_patterns_{local,server}.json`. Jobs: 6 (`run_retrieve_data`, `run_retrieve_sdc`, `run_compute_sdc{,_manifest,_aggregate,_no_slurm}`). Test: 16 file (12 unit, 4 integration; 183 test, di cui 22 in 2 file che giravano solo sul cluster per `bcblib`). Doc: `docs/guides/retrieval.md`, `docs/dev/retrieval.md`, `docs/guides/compute_sdc.md`.
- Suite: prima 1076 passed + 12 skipped (con i 2 file cluster esclusi con `--ignore`), dopo 918 passed, nessuno skipped, nessuna esclusione necessaria.

**Perché**: nessun codice vivo dipendeva da queste pipeline tranne un punto — `group_of`/`KNOWN_GROUPS`/`KNOWN_SITES`, la regola che dal nome di un soggetto (`sub-<DISEASE><SITE>[HC]<NUM>`) ricava il gruppo ST/HC/PD/GM, importata da `features/lesion.py`, `features/subject_discovery.py`, `features/sdc.py`, `populate_metadata.py`, `analysis/build_config.py` e `scripts/build_dataset_summary_table.py`. Spostata in `src/utils/subject_ids.py` (il livello più basso), con i suoi test di regressione (sito inventato che termina in "HC", lessons_learned #20). La spiegazione della regola vive ora in `docs/guides/datasets.md` ("Naming dei soggetti"), richiamata da `docs/dev/metadata.md`.

**Scartato**: tenere `src/retrieval/` solo per `group_of` (un pacchetto intero per una funzione, con la dipendenza `analysis → retrieval` che resterebbe senza motivo); documentare `compute_sdc` in una guida ridotta (deciso: la guida resta solo in git, nei doc una nota breve).

**Conseguenze ancora vere**:
- I dati si copiano a mano sotto `data/clinical_connectome/`; il formato delle cartelle non è cambiato ed è il contratto che i builder leggono.
- L'output SDC (`sdc/<subject_id>/*`) arriva da BCBToolKit fuori da questo repo; `build_sdc_matrix.py` lo legge come prima. Per rilanciare un soggetto (es. `sub-STUKLFR0671`, `open_problems.md`) non c'è più una pipeline qui.
- `assets/atlases/` NON è stato toccato: `fmriprep/` serve a `mask_fc.json`, `sdc_labels/` a `build_sdc_matrix.json`.
- `lessons_learned.md` e `docs/debugging/*` citano ancora i path eliminati nelle voci "Seen in": sono archivio, lasciati com'erano.

## 01-10-26 — Notebook riorganizzati per oggetto sotto ispezione: `lesion_analysis` si scioglie, `lesion_quality` ne prende il nome

**Cosa è cambiato**:
- Il vecchio `exploration/lesion_analysis.ipynb` (prototipo preistorico del costruttore di matrice + volumetria + overlap voxel-wise) è sciolto. Setup, caricamento maschere, costruzione di `X`, fast loading, sanity check, riduzione ai voxel non costanti, matrix visualization e frequenza voxel-wise → nuovo `pipeline_building/lesion_matrix_build.ipynb`.
- `exploration/lesion_quality.ipynb` è rinominato `exploration/lesion_analysis.ipynb` e riordinato per sezioni: Volume → Lateralità → Fuori dal brain → Soggetti esclusi. `show_scrollable` spostata nelle utilità in cima. La volumetria del vecchio notebook (ml, boxplot, violin/ECDF, percentili, coda lunga) vi è stata **riscritta su `lesion_metadata.csv`** (`lesion_volume_voxels_2mm` × 8 / 1000), non spostata: dipendeva da `X.sum(axis=1)`, cioè dalla matrice costruita nel notebook.
- `exploration/clinical_metadata_raw.ipynb` → `exploration/metadata_raw.ipynb`, con scope dichiarato in testa (legge i TSV grezzi, non `participants.csv`); titoli `###` → `##`.
- Nuova guida `docs/guides/exploration.md` (indice: domanda / legge / scrive per ogni notebook); rimandi in `README.md`, `.claude/CLAUDE.md`, 4 doc e 3 docstring aggiornati. Via le intestazioni "Parte X di 3".

**Perché**: gli scope si sovrapponevano (la distribuzione dei volumi stava in due notebook, calcolata in due modi). Criterio adottato: un notebook = un oggetto sotto ispezione + una domanda. Alternativa scartata: rinominare `lesion_quality` in `lesion_volume` — avrebbe descritto solo un terzo del contenuto (c'è anche lateralità, fuori dal brain e la cella che scrive `excluded_subjects.csv`, che legge soglie da tutte le sezioni); scissione in due notebook scartata per lo stesso motivo.

**Conseguenza ancora vera oggi**: l'ultima cella di `lesion_analysis` sovrascrive `assets/metadata/excluded_subjects.csv` con le sole liste `EXCLUSIONS` del notebook. Il file su disco ha una colonna `scope` che la cella non scrive e il notebook ha `EXCLUSIONS` vuoto: la cella è **indietro** rispetto al file e rieseguirla lo azzera. Non toccata in questa sessione.

## 29-09-26 — `scripts/` ridotto a 3 accessori: 4 entry point promossi a `src/pipeline/`, 6 script cancellati

`scripts/` conteneva 13 file (12 `.py` + 1 `.sh`) di tre nature diverse mescolate: veri entry point di pipeline, utility accessorie e one-off già eseguiti. Ora ne restano **3**, tutti e soli accessori: `archive_local_raw_data.py` (potatura/archiviazione della cache locale sotto `data/`), `build_dataset_summary_table.py` (tabelle LaTeX dei conteggi per dataset), `build_dim_reduction_strategies_csv.py` (indice derivato `results/dim_reduction_strategies.csv`).

**Promossi a `src/pipeline/`** (ora 16 entry point), per `code_standards.md` §1 "entry point centralizzati": `populate_metadata.py`, `calibrate_lesion_side_threshold.py`, `replot_dim_reduction.py`, `plot_tuning_embedding_3d.py`. Tutti e 4 avevano già la forma di una pipeline (argparse, report sotto `summaries/`, log sotto `logs/`, job in `jobs/`); `populate_metadata.py` in particolare ha config dedicata, `log_duration` e semantica `overwrite`, cioè la stessa struttura funzione-per-funzione di `enrich_metadata.py`, che stava già in `src/pipeline/`. Invocazione passata da `PYTHONPATH=. python scripts/X.py` a `python -m src.pipeline.X` ovunque (docstring, 3 job, guide, README, notebook, test); i 3 job hanno perso l'`export PYTHONPATH`, non più necessario. Aggiunto `jobs/run_calibrate_lesion_side_threshold.sh`, che mancava (ora 21 job).

**Cancellati (6)**, tutti recuperabili da `git log`:
- `download_sdc.py` (+ `jobs/run_download_sdc.sh`, `tests/unit/test_download_sdc.py`) — duplicava `config/pipelines/retrieval_sdc.json` + `jobs/run_retrieve_sdc.sh`: stessi 5 dataset, stessi 6 suffissi, stesso motore `retrieve_data.run()`. La lista dei 5 dataset era ricopiata a mano nello script, seconda fonte di verità per un elenco che sta già nella config. Il sottoinsieme che lo script otteneva via flag CLI si ottiene ora copiando la config e riducendone `datasets`/`retrieve` (documentato in `docs/guides/retrieval.md`).
- `download_lesions.sh` — `scp` in loop con IP, utente e path locale assoluto hardcoded, nessuna gestione errori, nome fuorviante (scaricava `desc-disconnectome.nii.gz`, cioè SDC). La sua destinazione `sdc_download/` era vuota (0 B): mai andato a buon fine.
- `verify_retrieval.py` (+ job + test) — la stessa `verify.verify_dataset` gira già in automatico nella fase post-copy di ogni run di `retrieve_data.py`; lo script serviva solo a ri-verificare senza fare una run, e per farlo importava tre funzioni **private** di `retrieve_data` (`_build_datasets`, `_select_subjects`, `_validate_upfront`).
- `backfill_runs_csv_input_path.py`, `backfill_stale_tuning_output_paths.py` (+ test), `rename_nemesis_t0_subjects.py` — one-off già eseguiti (i primi due ad agosto, il terzo il 23-09-26), non ripetibili con effetto: le cartelle `sub-p*` di NEMESIS_T0 sono già rinominate, le colonne `input_path` già riempite, i path pre-riorganizzazione già corretti.

**Alternative scartate**: (a) spostare in `src/pipeline/` anche i 3 accessori rimasti — `archive_local_raw_data.py` gestisce la cache locale e non produce nessun artefatto scientifico, gli altri due sono reporting/indici derivati: non sono passi di analisi e metterli fra gli entry point renderebbe `src/pipeline/` un contenitore indistinto; (b) conservare i 3 one-off in un `scripts/oneoff/` — la narrativa di cosa hanno fatto ai dati sta già in `data_changelog.md`, e il codice in `git log`: tenerli sarebbe codice morto (§2) con l'aggravante di sembrare rilanciabili.

**Conseguenza ancora vera oggi**: le voci più vecchie di `.claude/history/` e di `docs/debugging/` nominano questi file ai loro path di allora (`scripts/populate_metadata.py`, `scripts/replot_dim_reduction.py`, ...). Sono corrette per la data in cui sono state scritte e **non vanno riscritte**: questa voce è il punto di raccordo fra i vecchi path e quelli attuali.

---

## 29-09-26 — `enrich_metadata.py` diventa un join: non legge più nessuna maschera

`enrich_metadata` calcolava da sé i valori derivati dalle maschere, attraverso il blocco `lesion_metrics` (che nella prima versione della giornata ereditava perfino il config di `build_lesion_matrix.py`, poi reso autonomo — vedi la voce sostituita da questa). Ora è un **join fra sorgenti**: i tsv clinici per le variabili anagrafiche, e `assets/metadata/lesion_metadata.csv` per tutto ciò che viene dalle maschere. Rimossi `LesionMetricsConfig`, `MaskGrid`, `_load_lesion_metrics_config`, `_load_grids`, `compute_fresh_lesion_volumes`, `compute_geometric_lesion_sides` e gli import di `nibabel` e `src.features.lesion`: la pipeline non apre più nessun file NIfTI.

Il blocco di config è `lesion_metadata`, con tre chiavi: `path`, `copy_columns` (colonne copiate **con lo stesso nome**, per tutti i soggetti in scope, sovrascrivendo) e `lesion_side_from` (quale colonna del csv riempie `lesion_side`, **solo dove la risoluzione clinica ha lasciato la cella vuota**, scrivendo anche `lesion_side_source="geometric"`). In produzione: `copy_columns: ["lesion_volume_voxels_2mm"]`, `lesion_side_from: "lesion_side_2mm"`.

**Perché due chiavi invece di una lista sola**: `lesion_side` ha una regola di scrittura diversa da tutte le altre colonne (condizionale, e scrive anche una seconda colonna). Metterla in `copy_columns` avrebbe richiesto che la pipeline conoscesse per nome quella voce e la trattasse diversamente dalle altre — una regola implicita nel codice invece che dichiarata nel config. Discusso con l'utente, che ha prima chiesto di unificare e poi di tornare a due chiavi, per una ragione ulteriore: in `participants.csv` la colonna resta `lesion_side` **senza suffisso di griglia**, perché per i circa 1445 soggetti con etichetta clinica il valore non viene da nessuna griglia — un suffisso `_2mm` sarebbe falso per la maggioranza delle celle. `lesion_side_from` dice da quale griglia viene la parte geometrica, e `lesion_side_source` dice quale delle due provenienze ha vinto per ogni soggetto.

**Alternativa scartata**: rinominare la colonna del registro in `lesion_side_2mm`, così che sorgente e destinazione avessero sempre lo stesso nome e `copy_columns` fosse uniforme. Costava un rename in `embedding_coloring.py`, `calibrate_lesion_side_threshold.py`, 6 asserzioni di test, due notebook e tre docs — ma soprattutto avrebbe attribuito una risoluzione a valori clinici che non ne hanno una.

**Conseguenza ancora vera oggi**: il join è **stretto nei due sensi** e solleva invece di saltare: un soggetto in scope con `has_lesion=True` e senza riga nel csv significa csv vecchio; una riga per un soggetto che il registro non conosce, o che conosce come `has_lesion=False`, significa che i due file sono in disaccordo su chi ha una maschera. Le colonne derivate dalle maschere **non sono più correggibili a mano** in `participants.csv`: ogni run le ricopia. Un valore inaffidabile si sistema sulla maschera e si ricalcola, oppure il soggetto va in `excluded_subjects.csv`. `main()` legge il registro tramite `src.utils.participants.load_participants_registry`, non con un `read_csv` grezzo, perché il join ha bisogno di `has_lesion` come booleano vero: su un registro `dtype=str` un `astype(bool)` mapperebbe la stringa `"False"` a `True` e invertirebbe silenziosamente tutti i controlli (bug trovato e corretto durante l'implementazione, con test dedicato).

---

## 29-09-26 — `assets/metadata/lesion_metadata.csv`: le metriche dalle maschere diventano un livello a sé, `check_lesion_quality` ritirata

**Cosa è cambiato**: nuova pipeline `src/pipeline/compute_lesion_metadata.py` (config `config/pipelines/compute_lesion_metadata.json`, job `jobs/run_compute_lesion_metadata.sh`, log e summaries propri) che produce `assets/metadata/lesion_metadata.csv`: una riga per ogni soggetto con maschera, quattro colonne per griglia. È **agnostica del clinico**: non apre nessun `participants.tsv` e non sa cosa sia un NIHSS.

Ritirata `src/pipeline/check_lesion_quality.py` con il suo test, il suo job e le sue cartelle in `logs/`/`summaries/` (spostata sotto `src/pipeline/` solo poche ore prima, vedi la voce sotto — il nuovo file la sostituisce interamente e ne assorbe l'unica metrica, `out_of_brain_fraction`). `assets/metadata/lesion_quality_metrics.csv` resta su disco finché il nuovo csv non è prodotto e il notebook non gira. Cancellate da `src/features/lesion.py` le quattro funzioni rimaste senza chiamanti — `compute_lesion_volumes`, `compute_lesion_quality_metrics`, `compute_lesion_laterality_metrics`, `_out_of_brain_fractions`, 158 righe — sostituite da una sola `compute_lesion_metadata`.

**Perché**: prima le metriche derivate dalle maschere erano sparse su tre posti con tre scopi diversi (una cache diagnostica in `lesion_quality_metrics.csv`, due colonne nel registro scritte da `enrich_metadata`, una colonna nel `metadata.csv` di ogni matrice) e nessuno dei tre le aveva tutte. Tre funzioni di libreria rileggevano indipendentemente le stesse maschere, una per metrica. Un livello solo, prodotto da una pipeline sola, con `enrich_metadata` che ne copia un sottoinsieme nel registro: ogni metrica ha un posto dove nasce e uno solo.

**Alternativa scartata**: tenere il calcolo dentro `enrich_metadata` e aggiungerci le metriche mancanti. Avrebbe lasciato una pipeline che fa due lavori diversi (leggere imaging e leggere tsv clinici) e nessun posto dove stiano `out_of_brain_fraction` e l'indice di lateralità, che al registro non servono ma al notebook sì.

**Conseguenza ancora vera oggi**: il calcolo è **in streaming**, un soggetto per volta, e non passa per `_voxelwise_matrix_with_volume` come fa `build_lesion_matrix`. Quella funzione impila in memoria il volume appiattito di ogni soggetto: circa 5,3 GB sulla griglia a 2 mm (902.629 voxel x 5853 soggetti, uint8) e circa **42 GB** su quella a 1 mm, che non è eseguibile da nessuna parte. Chi in futuro volesse "riusare la funzione che c'è già" per aggiungere una griglia fine sbatterebbe esattamente lì. Accanto al csv la pipeline scrive `lesion_metadata.config.json`, il config risolto della run che l'ha prodotto: un csv di cui non si sappia su quali griglie e con quale correzione è stato calcolato non è interpretabile (`lessons_learned.md` #18/#36).

---

## 29-09-26 — `check_lesion_quality.py` spostato da `scripts/` a `src/pipeline/`

**Cosa è cambiato**: `git mv scripts/check_lesion_quality.py src/pipeline/check_lesion_quality.py` (storia git preservata). Invocazione aggiornata da `PYTHONPATH=... python scripts/check_lesion_quality.py` a `python -m src.pipeline.check_lesion_quality`, coerentemente con ogni altro entry point in `src/pipeline/`. Aggiornati tutti i riferimenti al vecchio path: `jobs/run_check_lesion_quality.sh`, `tests/unit/test_check_lesion_quality.py` (import), `docs/guides/matrix_building.md`, `docs/dev/lesion_matrix.md`, `docs/guides/metadata.md`, commenti in `src/features/lesion.py`/`src/pipeline/enrich_metadata.py`/`src/analysis/build_config.py`/`scripts/calibrate_lesion_side_threshold.py`, `tests/unit/test_build_config.py`, e due celle markdown di `notebooks/exploration/dataset_exploration.ipynb` (una delle quali citava anche, per errore ormai superato, "il calcolo geometrico di lesion_side resta da fare" - corretta nella stessa modifica).

**Perché**: richiesto esplicitamente dall'utente - lo script è un vero entry point di pipeline (CLI con `--config`/`--output-path`/`--overwrite`, report/log propri, stessa forma di `enrich_metadata.py`/`build_lesion_matrix.py`), non uno script accessorio/one-off. `code_standards.md` §1: "Entry point centralizzati - punto d'ingresso unico in `src/pipeline/`, niente script sparsi". Era finito sotto `scripts/` solo perché creato lì il 28-09-26 (voce sotto), non per una scelta architetturale deliberata.

**Conseguenza ancora vera oggi**: nessuna - `src/pipeline/check_lesion_quality.py` è stato **ritirato poche ore dopo**, nella stessa giornata (voce in cima a questo file): la pipeline che lo sostituisce, `compute_lesion_metadata.py`, è nata direttamente sotto `src/pipeline/`. Resta valida solo la convenzione che quello spostamento applicava, e che vale per il nuovo file: gli entry point stanno in `src/pipeline/`, e i loro test sotto `tests/unit/` piatto, senza specchiare la sottocartella di `src/`.

---

## 29-09-26 — `enrich_metadata.json`: `lesion_volume_config`/`lesion_side_geometric` unificati in `lesion_metrics`

**Cosa è cambiato**: i due campi di config separati per i metadati calcolati dalle maschere (`lesion_volume_config`, `lesion_side_geometric`, ognuno con la propria copia di `build_matrix_config`) sono diventati un unico blocco `lesion_metrics`, con due flag booleane indipendenti (`compute_volume`/`compute_side`) e una sola fonte condivisa (`build_matrix_config`). Aggiunta anche `correct_out_of_brain` (condivisa da entrambe le metriche): prima `compute_lesion_volumes()`/`compute_lesion_laterality_metrics()` bypassavano del tutto la correzione fuori-cervello di `build_lesion_matrix()` (`src/features/lesion_correction.py`, aggiunta lo stesso giorno da un'altra sessione), un gap silenzioso che avrebbe fatto tornare a divergere `lesion_volume_voxels`/`lesion_side` in `participants.csv` rispetto a una matrice di produzione costruita con quella correzione attiva — stessa famiglia di bug della voce "artefatto vs calcolo fresco" del 28-09-26 in `methods_changelog.md`, questa volta per omissione invece che per staleness. Rimossa anche `excluded_subjects` (era solo su `lesion_side_geometric`): mai popolata, nessun caso reale l'ha richiesta.

**Perché**: discusso esplicitamente con l'utente. Motivazione per l'unificazione: i due metadati condividono la stessa fonte (le maschere) e la stessa scelta di correzione — due config separati duplicavano `build_matrix_config` e rischiavano di far divergere `correct_out_of_brain` tra le due metriche senza alcun controllo. Motivazione per la rimozione di `excluded_subjects`: un'esclusione decisa dopo aver ispezionato la distribuzione in analisi richiede comunque di editare un config e rilanciare la pipeline (minuti di calcolo) — più macchinoso che correggere a mano la cella in `participants.csv` (un CSV versionato in git), che `fill: true` già lascia intatta alla run successiva. Stesso pattern già in uso nel progetto per `lesion_quality_metrics.csv` (`scripts/check_lesion_quality.py`): calcolo completo senza filtri, decisione a valle.

**Alternativa scartata**: mantenere `excluded_subjects` "per il futuro". Scartata per `code_standards.md` (non costruire per un bisogno ipotetico) — se un caso reale la richiederà, si reintroduce con un caso concreto in mano, non a priori.

**Aggiornamento, stessa giornata**: il caso concreto è arrivato nel giro di poche ore, e l'esclusione per soggetto è stata reintrodotta in forma diversa — non come campo di `enrich_metadata` ma come file unico letto dalle due pipeline di matrice (`assets/metadata/excluded_subjects.csv`, vedi `methods_changelog.md`). L'intero blocco `lesion_metrics` descritto in questa voce non esiste più: `enrich_metadata` è diventato un join (voce in cima a questo file).

**Conseguenza ancora vera oggi**: `correct_out_of_brain` è una flag indipendente in `enrich_metadata.json` e in `build_lesion_matrix.json` — **non c'è bisogno di tenerle allineate**. Le due pipeline hanno scopi diversi (registro anagrafico/demografico contro input dell'embedding, quest'ultimo rilanciabile più volte con impostazioni diverse tra una sessione e l'altra), quindi possono legittimamente divergere per scelta. Non è lo stesso problema del 28-09-26: lì un valore veniva copiato da un artefatto vecchio e spacciato per aggiornato; qui entrambe calcolano il proprio valore fresco con la propria configurazione esplicita. (Correzione della voce originale, scritta erroneamente come un vincolo di sincronizzazione.)

---

## 29-09-26 — Eliminato `scripts/lesion_fix.py`, superseduto da `src/features/lesion_correction.py`

**Cosa è cambiato**: rimosso `scripts/lesion_fix.py` — script standalone mai integrato in nessuna pipeline (nessun riferimento da `src/`/test), con un path hardcoded a `/Users/sebastiano/fsl/data/standard/MNI152_T1_2mm_brain_mask.nii.gz` (macchina di un altro utente, mai esistito su questo repo). Faceva esattamente la stessa correzione (azzerare i voxel di lesione fuori da una maschera cerebrale) ora implementata correttamente, testata e wired nella pipeline dal nuovo `src/features/lesion_correction.py`, attivabile via `correct_out_of_brain` — vedi la voce del 29-09-26 in `methods_changelog.md` per la decisione metodologica.

**Perché**: codice morto per `code_standards.md` §2 (nessun chiamante reale, path rotto) una volta che la stessa funzionalità esiste come modulo proprio, testato e raggiungibile da config.

**Conseguenza ancora vera oggi**: nessuna — la correzione va fatta tramite `correct_out_of_brain` in `build_lesion_matrix.json`, non più tramite quello script.

---

## 28-09-26 — Nuovo script `scripts/check_lesion_quality.py` + cache `assets/metadata/lesion_quality_metrics.csv`

**Cosa è cambiato**: `src/features/lesion.py` guadagna `compute_lesion_quality_metrics` (pubblica, senza soglie di ammissione - riusa `_voxelwise_matrix_with_volume`/`_load_and_binarize_brain_mask`/`_out_of_brain_fractions`, già scritte per `build_lesion_matrix.py`'s `min_lesion_volume_voxels`/`max_out_of_brain_fraction`, vedi voce del 28-09-26 in `methods_changelog.md`). Due nuovi consumatori la chiamano invece di ricalcolare da zero: `scripts/check_lesion_quality.py` (CLI, riusa `config/pipelines/build_lesion_matrix.json` come sorgente di configurazione, scrive `assets/metadata/lesion_quality_metrics.csv` in modo atomico, `--overwrite` per forzare il ricalcolo) e la sezione "Lesione fuori dal brain" di `notebooks/exploration/dataset_exploration.ipynb`, che prima usava una propria implementazione copiata (con `nilearn.datasets.load_mni152_brain_mask()`, una maschera MNI generica scaricata da internet, non l'asset di progetto) - ora importa la stessa funzione e usa lo stesso `assets/templates/tpl-MNI152NLin6Asym_res-1_desc-brain_mask.nii.gz` della pipeline di produzione, quindi notebook e script vedono esattamente gli stessi numeri. Aggiunto anche `jobs/run_check_lesion_quality.sh`.

**Perché**: il calcolo (un caricamento+resampling nibabel/nilearn per soggetto) è costoso - minuti sull'intera coorte di ~5700 soggetti, verificato eseguendo la vecchia versione nel notebook. Serve poterlo eseguire una volta sola e riusare il risultato, sia da script standalone sia da notebook, senza duplicare la logica di calcolo (solo il calcolo, non l'I/O: la cache CSV è nel chiamante, `compute_lesion_quality_metrics` resta puro, nessuna scrittura su disco).

**Superseduta il 29-09-26, stessa giornata**: `assets/metadata/lesion_quality_metrics.csv` e lo script che lo produceva non esistono più. Il file che ne prende il posto è `assets/metadata/lesion_metadata.csv` (voce in cima a questo file), che contiene *tutte* le metriche derivabili da una maschera invece della sola frazione fuori dal brain, e su ogni griglia. Resta valida l'idea per cui quel file era nato: la decisione di ammissione si prende guardando la distribuzione reale, non indovinando un valore — cambiato solo *come* la decisione viene registrata (una lista curata a mano, non una soglia in un config).

---

## 23-09-26 — `reference_template_path` sostituito con un vero template MNI152 versionato

**Cosa è cambiato**: `config/pipelines/build_lesion_matrix.json` e `build_sdc_matrix.json`
puntavano entrambi `reference_template_path` alla lesion mask di un singolo paziente
(`sub-STUNIPD0001`, WashU, sotto `data/`, gitignored) — funzionava solo perché shape/affine
di quel file coincidevano con una griglia MNI152 nota. Sostituito con due template reali,
versionati, sotto `assets/templates/` (`tpl-MNI152NLin6Asym_res-1_T1w.nii.gz` 1mm e
`_res-2_T1w.nii.gz` 2mm, scaricati da TemplateFlow, shape/affine verificati contro i dati del
progetto). Entrambi i config ora puntano al `_res-1_` (1mm). Nessuna modifica a codice:
`load_reference_image`/`resample_to_img` leggono solo shape+affine, mai il contenuto voxel —
un template T1w funziona in modo identico a una maschera binaria come riferimento di griglia.
Rimosso anche il pin `must_keep={"sub-STUNIPD0001"}` in `scripts/archive_local_raw_data.py`,
non più necessario. Scaricate anche le brain mask corrispondenti (`_res-1_desc-brain_mask.nii.gz`/
`_res-2_desc-brain_mask.nii.gz`, stessa fonte, griglia/affine verificati identici alle T1w) — non
ancora usate da nessun codice, disponibili sotto `assets/templates/` per quando servirà.

**Perché**: fragilità già segnalata come TODO aperta (`docs/dev/lesion_matrix.md`, sezione
"Known open question") — l'intera griglia voxel di produzione dipendeva dalla sopravvivenza
di un file paziente specifico, non versionato. Il rischio si è concretizzato lo stesso giorno:
una sostituzione non correlata delle lesion mask WashU/UKLFR (vedi `data_changelog.md`,
23-09-26) ha cambiato silenziosamente quel file da 2mm a 1mm, quindi la griglia di riferimento
per *ogni* dataset in ogni run futuro — scoperto solo verificando la risoluzione dei nuovi
file prima di aggiornare `docs/guides/datasets.md`, non da un errore/crash.

**Alternative scartate**: patchare l'affine del template scaricato per farlo combaciare
bit-per-bit con la griglia post-swap di `sub-STUNIPD0001` (origin -90 invece di -91) — scartata
perché quella griglia non era mai stata "la" griglia canonica del progetto, solo un artefatto
incidentale di un file paziente; adottare la griglia autoritativa TemplateFlow è più corretto,
e `resample_to_img` riallinea comunque correttamente qualunque sorgente al nuovo riferimento.

**Conseguenza ancora vera oggi**: le matrici già costruite in passato non sono toccate (la loro
griglia era fissata al momento del build); solo i nuovi run raccolgono il nuovo riferimento. La
scelta 1mm/2mm è un edit di config (`reference_template_path` punta a `_res-1_` o `_res-2_`),
non richiede codice.

---

## 23-09-26 — `main` riportato al passo e adottato come branch di lavoro di default

**Cosa è cambiato**: `main` era rimasto indietro di 121 file (+16516/-21005 righe) rispetto al lavoro reale, che da settimane continuava solo su branch di task mai rimersi. Fast-forward di `main` sulla punta di `fix/sdc-drop-dwi-folder` (nessun conflitto: `main` non aveva nemmeno un commit unico non già contenuto nel branch), pushato su `origin/main`. Ripuliti 6 branch locali: 4 già completamente mergeati (`clustering-embedding-tag-naming`, `clustering-runs-csv-reduction-columns`, `embedding-app-anatomy-panels`, `tag-params-multi-key` — cancellazione sicura), `fix/sdc-drop-dwi-folder` stesso (ridondante dopo il fast-forward, cancellato anche dal remoto), e `backup-pre-split` (non mergeato — 2 commit isolati su un punto vecchio pre-refactor "split", cancellazione forzata).

**Perché**: nessuno rimergeva mai i branch di task in `main`, che restava una fotografia vecchia mentre il lavoro vero viveva altrove — scoperto controllando lo stato reale dei branch dopo che `.claude/stato_progetto.md` è risultato disallineato (citava un branch, `metadata-restructuring`, che non era nemmeno più il checkout corrente).

**Decisione per il futuro**: si lavora su `main` di default; un branch nasce solo per un task specifico e viene mergeato/cancellato appena concluso — mai tenuto in vita come branch parallelo permanente. Vedi `.claude/branch_alignment.md`.

**Conseguenza ancora vera oggi**: `main` locale e `origin/main` sono allineati (stesso commit). `backup-pre-split` è recuperabile da `068d2ff` (`git checkout -b backup-pre-split 068d2ff`) finché il reflog lo conserva.

---

## 07-09-26 — Eliminato il branch `viz-niivue`

Esplorazione di **niivue** come renderer alternativo ai pannelli di anatomia di `embedding_app.py` (oggi su nilearn), 4 commit mai mergeati: prova iniziale, fix dell'hang al caricamento del volume (mancava l'hint di formato), template MNI152 anatomico reale come sfondo, fix del canvas che collassava a 150px.

Chiuso senza adottare niivue e senza una valutazione conclusiva dei due renderer: l'esplorazione era ferma da tempo e teneva aperto un branch che nessuno stava portando avanti. `main` resta su nilearn.

La punta era **`facef6f`**: `git checkout -b viz-niivue facef6f` lo ricrea finché il reflog lo conserva (~90 giorni). Lo SHA è annotato qui proprio perché un branch cancellato non compare in `git log`.

---

## 06-09-26 — I metadati clinici passano a una fonte di verità unica; ritirata la join per-run

**Cosa è cambiato.** I valori clinici (age, sex, education, lesion_side, NIHSS, clinical_date, lesion_volume_voxels) vivono ora in `assets/metadata/participants.csv`, una riga per soggetto, versionata. Prima venivano uniti dentro il `metadata.csv` di *ogni* run da `enrich_lesion_metadata.py`, che leggeva un tsv curato per dataset.

Nuovo: `src/pipeline/enrich_metadata.py` (+ config, job, 16 test), `src/utils/participants.py` (lettura del registro), `src/utils/metadata_sources.py` (parser del registry condiviso, estratto da `populate_metadata.py` perché un entry point non ne importi un altro), `docs/guides/metadata.md`.

Cancellati: `src/pipeline/enrich_lesion_metadata.py` + config + job, `src/features/clinical.py`, `EnrichLesionMetadataConfig`, i relativi test (51 test rimossi, 16 aggiunti; suite 928 passed).

Ricablati sul registro: `src/features/sdc.py` (`has_lesion` come criterio di ammissione), `src/analysis/embedding_coloring.py::color_values` (`side`/`nihss` risolti al plot), `notebooks/post-results_analysis/clustering_evaluation.ipynb`.

**Perché adesso.** I tsv per-dataset erano già stati cancellati dal commit `014dc2a`, ma nessun consumatore era stato spostato: `build_sdc_matrix.py` e `enrich_lesion_metadata.py` erano entrambi **non eseguibili** e nessun test se ne accorgeva, perché ogni test si scriveva da sé le fixture col nome ritirato dopo aver ridiretto `METADATA_ROOT` su `tmp_path`. Suite verde, due pipeline morte.

**Alternativa scartata**: ripuntare `src/features/clinical.py` ai tsv grezzi in `data/clinical_connectome/metadata_tsv/`. Sarebbe stato fattibile (il join corretto passa da `original_id`), ma avrebbe resuscitato proprio il meccanismo che il ridisegno stava smantellando — una join per-dataset ripetuta a ogni run, con N copie degli stessi valori che possono divergere.

**Due difetti trovati solo rilanciando la pipeline una seconda volta** (`.claude/lessons_learned.md` #17 — il ramo di merge esiste solo quando la colonna c'è già, quindi la prima run non lo esegue mai): un `TypeError` nello scrivere un NaN dentro una colonna di dtype `str`, e `lesion_volume_voxels` serializzato come `4616.0` invece di `4616` (la NaN dei soggetti non appaiati promuoveva la colonna a float64). Entrambi corretti, entrambi con test di regressione.

**Conseguenze ancora vere oggi.**

- Il `metadata.csv` di una run contiene solo ciò che appartiene alla run (`subject_id`, `dataset`, `lesion_volume_voxels`). Le run vecchie hanno ancora le colonne cliniche: `color_values` preferisce la colonna della run quando c'è, e altrimenti va al registro — quindi entrambe le generazioni si colorano.
- Colorare per `side`/`nihss` non richiede più nessuno step per-run: **anche le run vecchie** si colorano, e arricchire il registro oggi le migliora retroattivamente.
- Il join coi tsv grezzi passa da `original_id`, non da `subject_id` (per UCL-UK il `participant_id` grezzo è l'id legacy di sito) — `.claude/lessons_learned.md` #30.
- `lesion_side` è popolato solo dove il dato clinico esiste. Il calcolo geometrico previsto dal disegno **non è stato implementato**: serve calibrare la soglia "bilaterale" sui 4 dataset che hanno l'etichetta, e inventarne una avrebbe prodotto un valore plausibile e senza basi. `lesion_side_source` esiste già per distinguere le due provenienze.

---

## 01-09-26 — Rimossa `production/comparison/` da `clustering.py`

**Cosa è cambiato**: `clustering.py` non genera più, su richiesta, la cartella `comparison/` sotto `production/` (il plot di confronto cross-metodo `cluster_comparison.png`/`cluster_comparison_interactive.html`).

**Perché**: per confrontare più metodi oggi si aprono i `cluster_plot.png` di ciascuno, oppure si usa `embedding_app.py` (un run alla volta) — il confronto cross-metodo dedicato è stato ritenuto non necessario.

**Conseguenza ancora vera oggi**: nessuna pipeline produce un artefatto di confronto multi-metodo. Un'eventuale cartella `comparison/` residua da prima di questa data resta sul disco ma è esclusa automaticamente dalla discovery di `embedding_app.py` (non ha mai un `manifest.json`).

---

## 15-08-26 — `embedding_plot_interactive.html`/`plot_clusters_interactive` per-run rimossi, sostituiti da `embedding_app.py`

**Cosa è cambiato**: `dim_reduction.py` (14-08-26) e poi `clustering.py` (15-08-26, quando `embedding_app.py` è stato esteso a scoprire anche i run di `clustering.py`) hanno smesso di scrivere un file `.html` interattivo per-run (`embedding_plot_interactive.html`, `plot_clusters_interactive`). Un solo processo live, l'app Dash `src.pipeline.embedding_app`, copre invece tutti i run di produzione già scritti (di entrambe le pipeline), con un selettore di run e bottoni di colorazione.

**Perché**: un file HTML per-run va rigenerato ad ogni run e non scala con il numero di run prodotti; un'app che legge `matrix.npy`/`metadata.csv` già su disco copre tutti i run esistenti e futuri senza rigenerazione.

**Conseguenza ancora vera oggi**: nessuna pipeline di dim reduction/clustering scrive più un file `.html` interattivo per singolo run — l'esplorazione interattiva 2D/3D di qualunque run di produzione passa sempre da `embedding_app.py` (`docs/guides/embedding_app.md`).

---

## 15-08-26 — `data_sessions.md` spostato da `data/` a `docs/experiments/`

**Cosa è cambiato**: il diario umano delle sessioni (`data_sessions.md`, cosa significa un `session_name` — dataset, modalità, cosa è cambiato) si è spostato da `data/data_sessions.md` a `docs/experiments/data_sessions.md`. Il symlink `results/data_sessions.md` è stato rimosso.

**Perché**: è narrativa di progetto scritta a mano, non un dato grezzo/derivato — sta meglio con il resto di `docs/` che nell'albero `data/` (gitignored). La sua informazione confluisce anche nelle colonne `session`/`modality`/`datasets` di `results/dim_reduction_strategies.csv`, generato da `scripts/build_dim_reduction_strategies_csv.py`.

**Conseguenza ancora vera oggi**: `docs/experiments/data_sessions.md` è l'unica fonte per il significato di un `session_name`; non esiste più un symlink sotto `results/`.

---

## 14-08-26 — `dim_reduction_clustering.py` ritirato, capacità assorbita da `clustering.py`

**Cosa è cambiato**: lo script "riduci poi cluster" in un solo comando (`dim_reduction_clustering.py`, allora il più usato del progetto) è stato eliminato. `clustering.py` guadagna un campo di config obbligatorio `reduced_data: bool` — dichiara se `input_path` è un embedding già calcolato o una matrice grezza — e (26-08-26) `viz_embedding_path` per disegnare i cluster quando `X` non ha 2/3 colonne. Il flusso in due passi (`dim_reduction.py` poi `clustering.py --reduced_data true`) sostituisce integralmente il comando unico.

**Perché**: `dim_reduction_clustering.py` duplicava quasi per intero l'orchestrazione CLI di `clustering.py` (stesso `_run_one_method`, stesso `_write_tuning_output`, stessa run-log) solo per aggiungere un `embed()` a monte — la logica algoritmica vera era già condivisa in `src/analysis/`, la duplicazione era solo nel layer `src/pipeline/`.

**Alternativa scartata**: far ricalcolare la riduzione al volo dentro `clustering.py` stesso (un `embed()` interno). Scartata in sessione come troppo complessa da implementare bene subito — `clustering.py` non chiama mai `embed()`, in nessun ramo; `reduced_data` è puramente dichiarativo, mai un trigger di calcolo.

**Conseguenza ancora vera oggi**: `src/pipeline/dim_reduction_clustering.py`, il suo config e il suo job non esistono più. La logica di viz a 2/3/>3 componenti (`_resolve_viz_embedding` in `clustering.py`, `embedding_for_viz` in `reduction.py`) e i campi `reduced_data`/`viz_embedding_path` sono documentati in `docs/dev/models.md`/`config.md`. I risultati storici sotto `results/lesion/dim_reduction_clustering/` restano un archivio del vecchio pipeline, non spostati.

---

## 2026-08 — Produzione e tuning separati in due rami sotto `output_root` (`dim_reduction.py`/`clustering.py`)

**Cosa è cambiato**: `results/lesion/dim_reduction/production/<metodo>/...` e `results/lesion/dim_reduction/tuning/<metodo>/...` (stesso schema per `clustering.py`) sono due rami separati sotto `output_root`, mai mescolati. Prima di questa riorganizzazione, `tuning/` viveva dentro la cartella del metodo (`<metodo>/tuning/...`).

**Conseguenza ancora vera oggi**: risultati scritti prima di questa riorganizzazione possono trovarsi sul vecchio layout (`<metodo>/tuning/...`) invece che sotto un ramo `tuning/` di primo livello — chi ispeziona risultati storici più vecchi di questa riorganizzazione deve tenerlo a mente; i risultati nuovi seguono sempre lo schema a due rami.
