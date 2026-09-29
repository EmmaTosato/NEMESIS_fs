# Changelog dell'impianto di progetto

Decisioni su **come è organizzato il repo**: fonti di verità uniche, pipeline ritirate, convenzioni di naming, formati degli artefatti — con le alternative scartate.

**Cosa NON va qui**: la storia del codice (già in `git log`), lo stato attuale (`docs/`, al presente), i cambiamenti ai dati (`data_changelog.md`).

Voci in ordine cronologico inverso.

---

## 29-09-26 — `check_lesion_quality.py` spostato da `scripts/` a `src/pipeline/`

**Cosa è cambiato**: `git mv scripts/check_lesion_quality.py src/pipeline/check_lesion_quality.py` (storia git preservata). Invocazione aggiornata da `PYTHONPATH=... python scripts/check_lesion_quality.py` a `python -m src.pipeline.check_lesion_quality`, coerentemente con ogni altro entry point in `src/pipeline/`. Aggiornati tutti i riferimenti al vecchio path: `jobs/run_check_lesion_quality.sh`, `tests/unit/test_check_lesion_quality.py` (import), `docs/guides/matrix_building.md`, `docs/dev/lesion_matrix.md`, `docs/guides/metadata.md`, commenti in `src/features/lesion.py`/`src/pipeline/enrich_metadata.py`/`src/analysis/build_config.py`/`scripts/calibrate_lesion_side_threshold.py`, `tests/unit/test_build_config.py`, e due celle markdown di `notebooks/exploration/dataset_exploration.ipynb` (una delle quali citava anche, per errore ormai superato, "il calcolo geometrico di lesion_side resta da fare" - corretta nella stessa modifica).

**Perché**: richiesto esplicitamente dall'utente - lo script è un vero entry point di pipeline (CLI con `--config`/`--output-path`/`--overwrite`, report/log propri, stessa forma di `enrich_metadata.py`/`build_lesion_matrix.py`), non uno script accessorio/one-off. `code_standards.md` §1: "Entry point centralizzati - punto d'ingresso unico in `src/pipeline/`, niente script sparsi". Era finito sotto `scripts/` solo perché creato lì il 28-09-26 (voce sotto), non per una scelta architetturale deliberata.

**Conseguenza ancora vera oggi**: `tests/unit/test_check_lesion_quality.py` resta comunque sotto `tests/unit/` (non spostato in una sottocartella `pipeline/`) - la struttura dei test in questo repo è piatta, non specchia la sottocartella di `src/` (stessa convenzione di `test_enrich_metadata.py`/`test_populate_metadata.py`, quest'ultimo per uno script rimasto deliberatamente sotto `scripts/`).

---

## 29-09-26 — `enrich_metadata.json`: `lesion_volume_config`/`lesion_side_geometric` unificati in `lesion_metrics`

**Cosa è cambiato**: i due campi di config separati per i metadati calcolati dalle maschere (`lesion_volume_config`, `lesion_side_geometric`, ognuno con la propria copia di `build_matrix_config`) sono diventati un unico blocco `lesion_metrics`, con due flag booleane indipendenti (`compute_volume`/`compute_side`) e una sola fonte condivisa (`build_matrix_config`). Aggiunta anche `correct_out_of_brain` (condivisa da entrambe le metriche): prima `compute_lesion_volumes()`/`compute_lesion_laterality_metrics()` bypassavano del tutto la correzione fuori-cervello di `build_lesion_matrix()` (`src/features/lesion_correction.py`, aggiunta lo stesso giorno da un'altra sessione), un gap silenzioso che avrebbe fatto tornare a divergere `lesion_volume_voxels`/`lesion_side` in `participants.csv` rispetto a una matrice di produzione costruita con quella correzione attiva — stessa famiglia di bug della voce "artefatto vs calcolo fresco" del 28-09-26 in `methods_changelog.md`, questa volta per omissione invece che per staleness. Rimossa anche `excluded_subjects` (era solo su `lesion_side_geometric`): mai popolata, nessun caso reale l'ha richiesta.

**Perché**: discusso esplicitamente con l'utente. Motivazione per l'unificazione: i due metadati condividono la stessa fonte (le maschere) e la stessa scelta di correzione — due config separati duplicavano `build_matrix_config` e rischiavano di far divergere `correct_out_of_brain` tra le due metriche senza alcun controllo. Motivazione per la rimozione di `excluded_subjects`: un'esclusione decisa dopo aver ispezionato la distribuzione in analisi richiede comunque di editare un config e rilanciare la pipeline (minuti di calcolo) — più macchinoso che correggere a mano la cella in `participants.csv` (un CSV versionato in git), che `fill: true` già lascia intatta alla run successiva. Stesso pattern già in uso nel progetto per `lesion_quality_metrics.csv` (`scripts/check_lesion_quality.py`): calcolo completo senza filtri, decisione a valle.

**Alternativa scartata**: mantenere `excluded_subjects` "per il futuro". Scartata per `code_standards.md` (non costruire per un bisogno ipotetico) — se un caso reale la richiederà, si reintroduce con un caso concreto in mano, non a priori.

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

**Conseguenza ancora vera oggi**: `assets/metadata/lesion_quality_metrics.csv` è una cache diagnostica per scegliere le soglie prima di una run di produzione - deliberatamente separata da `participants.csv` (la cui `lesion_volume_voxels` ha una provenienza diversa: copiata da uno specifico lesion matrix già costruito, non ricalcolata fresca). Di default lo script non ricalcola se il file esiste già (va passato `--overwrite`).

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
