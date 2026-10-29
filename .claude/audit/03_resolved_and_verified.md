# 03 — Verifiche superate e fix confermati

Formato: `[V-xxx] | Fonte | Cosa è stato provato | Come`.

## `.claude/CLAUDE.md` (76/76 righe)

- [V-001] | `CLAUDE.md:7` | `tests/unit/`, `tests/integration/` esistono; 5685 test raccolti senza errori di import | `pytest tests --collect-only -q` con l'ambiente `nemesis`
- [V-002] | `CLAUDE.md:9-17` | L'ambiente conda `nemesis` esiste; `docs/setup.md` esiste | `conda env list`, `ls`
- [V-003] | `CLAUDE.md:17` | `docs/guides/datasets.md` documenta il percorso EBRAIN `/data/corbetta/Clinical_connectome` | `grep -n -i ebrain`
- [V-004] | `CLAUDE.md:23` | Convenzione `PYTHONPATH` + `python scripts/...` per gli script | `jobs/run_build_dataset_summary_table.sh`, docstring di `scripts/*.py`
- [V-005] | `CLAUDE.md:24-27` | I 18 job in `jobs/` sono file singoli `run_<nome>.sh`, ognuno con `#SBATCH -o` su `logs/slurm/<nome>/%j.out`; tutti hanno `conda.sh`; nessun job senza sorgente | `grep`, loop su `src/pipeline/*.py` e `scripts/*.py`
- [V-006] | `CLAUDE.md:35` | Le 14 guide elencate esistono, nessuna guida esistente è omessa; le 4 guide "ritirate" non esistono | confronto elenco vs `ls docs/guides`
- [V-007] | `CLAUDE.md:35` | Il commit `2ed3dcb` rimuove `docs/guides/atlas_building.md`, `src/pipeline/build_combined_atlas.py`, `src/atlases/`, il job e il test | `git show --stat 2ed3dcb`
- [V-008] | `CLAUDE.md:35` | `retrieval.md`, `compute_sdc.md`, `retrieve_data.py`, `compute_sdc.py` rimossi dal commit `d8dbdee` (2026-10-05) | `git log --diff-filter=D`
- [V-009] | `CLAUDE.md:36` | Tutti i 14 file di `docs/dev/` citati esistono | loop su `ls`
- [V-010] | `CLAUDE.md:37` | `docs/notes/` non esiste; il merge `docs/dr-clustering-literature-migration` è avvenuto (`f9e2d30`); `knowledge/notes/neuroimaging/fc_lesion_masking.md` esiste | `git log`, `ls`
- [V-011] | `CLAUDE.md:38-40` | `docs/experiments/{README,lineage,pipelines}.md`, `docs/debugging/`, `docs/setup.md` esistono | `ls`
- [V-012] | `CLAUDE.md:41-42,44-45,47-49` | `management/{meetings,cheatsheets,nemesis_project,slides}`, `knowledge/notes/*`, `knowledge/papers/{stroke_core,stroke_related,methods,index.md}`, `src/{features,analysis,utils,pipeline}`, `scripts/`, `jobs/` esistono | `ls`
- [V-013] | `CLAUDE.md:54-58` | I 4 file di `.claude/history/` e lo skill `history` esistono | `ls`
- [V-014] | `CLAUDE.md:63` | Regola dei notebook: heading da solo nella sua cella. 13 notebook, tutte le celle markdown controllate, 0 violazioni | script Python che scorre le celle (ignora `#` dentro blocchi di codice recintati)
- [V-015] | `CLAUDE.md:64,68,74` | `code_standards.md` §9 esiste; `@code_standards.md`, `@lessons_learned.md` risolvono a file reali in `.claude/` | `ls`, lettura

## Fix confermati già applicati

- Nessuno: nessun file di progetto è stato modificato in questa sessione (solo creazione di `.claude/audit/`).

## Esecuzione di test

- `pytest tests -q`: 5668 passed, 17 skipped (vedi V-022).

## `.claude/stato_progetto.md` (50/50 righe)

- [V-016] | `stato_progetto.md:11,13-15,17` | `pca`/`rotation_n_components`/`covariance_pca.py`, `run_evaluations`, il registro `clustering_evaluations.json` (10 valutazioni), DBCV euclideo con NaN sotto 2 cluster, file di produzione `dbcv_per_cluster.csv`/`dbcv_plot.png`, valutazioni ristrette per metodo (`_AGGLOMERATIVE_ONLY`, `_DENSITY_ONLY`) | lettura mirata di `src/analysis/{reduction,pca_method,clustering_tuning_evaluations,dbcv}.py`, `src/pipeline/clustering.py`, `config/registry/clustering_evaluations.json`
- [V-017] | `stato_progetto.md:36` | Criterio «usabile»: assente da `s2.4-vol.md`, presente in `s1.4-vol.md`, `s2.4-stream.md`, `pipelines.md` | `grep -o`
- [V-018] | `stato_progetto.md:38` | Stato mutabile dei config: `dim_reduction.json` e `clustering.json` coincidono con quanto descritto | lettura dei due file
- [V-019] | `stato_progetto.md:41` | Commit `3e53099` (2026-10-16) ritira lo script; script e CSV assenti | `git cat-file`, `ls`
- [V-020] | `stato_progetto.md:44` | Copie locali ridotte a 10 soggetti (WashU features, `masked_fc`) | `ls | wc -l`
- [V-021] | `stato_progetto.md:45-46` | Semantica di `overwrite`/`protected_path` in `enrich_metadata` e di `overwrite` in `build_excluded_subjects` | config, docstring dei moduli
- [V-022] | **Suite di test** | `pytest tests -q` nell'ambiente `nemesis`: **5668 passed, 17 skipped, 0 failed** (5685 raccolti, 196 s, 420 warning) | esecuzione completa (output nello scratchpad della sessione)

## Fix già applicati
- Nessuno: nessun file del progetto modificato dall'audit.

## `.claude/code_standards.md` (123/123 righe)

- [V-023] | `:40` | Livelli rispettati: 0 import da un livello inferiore verso uno superiore | AST su `src/` (import `src.<livello>`)
- [V-024] | `:42` | Nessun `global`; nessun contenitore mutabile minuscolo a livello di modulo | AST
- [V-025] | `:62,64` | 0 `except:` nudi, 0 `except Exception` con solo `pass`/`continue`, 0 `raise X()` senza messaggio | AST
- [V-026] | `:63` (parte) | I 5 `except Exception` di `compute_sdc_metadata.py:156`, `compute_lesion_metadata.py:164`, `enrich_metadata.py:980`, `populate_metadata.py:324`, `background_cache.py:64` puliscono il file temporaneo e rilanciano | lettura del codice
- [V-027] | `:73` | Ogni modulo di `src/` è citato da almeno un test | `grep -rl` per modulo
- [V-028] | `:83` | 0 percorsi assoluti (`/home`, `/Users`, `/data`, `/mnt`, `/opt`) in `src/` e `scripts/` | scansione di stringhe
- [V-029] | `:86` | Chiavi dei config di pipeline tutte lette dal codice (le non trovate sono iperparametri passati alle librerie) | confronto chiavi JSON vs stringhe in `src/`
- [V-030] | `:92` | Nessun messaggio di log in italiano (257 chiamate) | euristica sulle parole
- [V-031] | `:96` | `log_duration` esiste e, dove usata, sta in un `finally` (15 entry point su 18) | AST
- [V-032] | `:109` | I 15 file di `docs/debugging/` seguono `debug_DD_MM_YY.md` | `ls`
- [V-033] | `:122-123` | I due link di "Riferimenti" risolvono; `group_of` solleva su sito non registrato | `ls`, lettura di `subject_ids.py`

## `.claude/branch_alignment.md` (40/40 righe)

- [V-034] | `:3` | Un solo branch locale `main`, in sync con `origin/main` (0/0), nessun branch temporaneo, stash o tag | `git branch -a -vv`, `git rev-list --left-right --count`
- [V-035] | `:9-12,14-24,28-36` | Procedura pull/push e rebase coerente con git 2.48.1 e con `pull.rebase` non impostato; `origin/main` esiste | `git --version`, `git config`
- [V-036] | `:5` | Nessuna eccezione di file tra i due checkout; i file locali (`settings.local.json`, `scheduled_tasks.lock`) sono ignorati da regole esterne al repo | `git check-ignore -v`
- [V-037] | `:40` (parte) | `data/` e `results/` non sono tracciati | `git ls-files data results | wc -l` = 0

## `.claude/open_problems.md` (215/215 righe)

- [V-038] | `:15-17,25,29-30` | PSP frazionarie (168, multipli di 1/8, mediana 0,83), WashU 11/162 (6+5), mancini 5/16 contro destrimani 6/146 (Fisher 0,0016), ARAT 90/92, 9HPT 102/119, header unico sulle 195 maschere | `nibabel` sulle maschere locali, `pandas`/`scipy` su `participants.csv`, `lesion_metadata.csv`, `participants_WashU.tsv`
- [V-039] | `:60-62,68-72` | 5845 lesioni in scope; 27 «non etichettati» (17/9/1); 121 con >20%; infratentoriali UKLFR 0,14% e PASPORT 0%; `0671` a 0 voxel e escluso | calcolo su `lesion_metadata.csv`, `excluded_subjects.csv`, maschera e `mapstats`
- [V-040] | `:81-84` | `mask_summary.csv` contro CSV mascherati: stessi 7 accordi e 3 disaccordi | confronto riga per riga su 10 soggetti
- [V-041] | `:175-180,133-148` | `tuning.py:127`, `_WARD_SAFE_METRICS`, `SILHOUETTE_OWN_METRIC_METHODS`, `_combo_key` duplicato, `FIGURE_DPI`, `_quality_guide`/`_adp_guide`, `HINT_*`/`REPORT_TERMS` | `grep`
- [V-042] | `:207`, `:170-171` | `s2.2-vol` = 1570 × 290940 `float32`; esiste `results/sdc/clustering/tuning/hdbscan/pca` | `np.load(mmap)`, `ls`

## `.claude/lessons_learned.md` (191/191 righe)

- [V-043] | tutte le righe "Seen in" | Tutti i `debug_*.md` citati esistono; nessun `§N` fuori dal numero di sezioni del file; nessun commit citato è invalido | script Python (regex su `debug_*.md`, `§N`, hash) + `git cat-file`
- [V-044] | #29, #31, #33, #42, #43, #45, #46 | I simboli e i test citati esistono e il comportamento descritto è nel codice (SVG nel Dendrogram, cast a `float64` in `dbcv`, `fullmatch`, `PRECOMPUTABLE_METRICS`, grid dei diagnostici) | `grep` e lettura del codice
- [V-045] | #35 | Le 42 `runs*.csv` del repo finiscono tutte con un a-capo | `tail -c1` su ogni file
- [V-046] | #38, #12 | `- set(excluded_by_list)` presente nei tre punti (`sdc.py:165,268`, `parcellated_csv.py:110`); `KNOWN_LESION_SIDES` e il suo test esistono | `grep`

## `.claude/history/data_changelog.md` (223/223) e `.claude/skills/history/SKILL.md` (79/79)

- [V-047] | `data_changelog.md:13-21,25-35,53-63` | Riordino alfabetico delle due matrici (5845 righe, nessun `*.orig`), rinomina `sdc/`→`bcbtoolkit/` in 8 dataset (4119/56/451/705/76/83/168/195), cache con 5853 chiavi, rimozione di `data/derived/enrich_lesion_metadata/` | `pandas` su `metadata.csv`, `os.listdir`, lettura di `file_types_cache.json`
- [V-048] | `:116-119,201-223` | Conteggi delle maschere per dataset, 8 tsv in `metadata_tsv/`, nessun `dwi/`, 34 file per soggetto WAKEUP, archivi `.tar.gz` accanto alle due cartelle potate, `features_archive_subjects.tsv` e `README_ARCHIVE.md` | `ls`, `find`
- [V-049] | `:65-102` | 76 cartelle `0586…0666`; tsv con `participant_id_dmp`, 104 righe, nessun `sub-p*` residuo | `pandas`, `os.listdir`
- [V-050] | `SKILL.md` | Coerenza con `CLAUDE.md:54-60` (tre registri + archivio sola lettura), ordine cronologico inverso rispettato in `data_changelog.md` | lettura

## `.claude/history/project_changelog.md` (parziale: righe 1-64)

- [V-051] | tutto il file | 81 voci in ordine decrescente (80 nel formato `GG-MM-AA`); 174 percorsi e tutti i commit estratti e controllati | script Python + `git cat-file`
- [V-052] | `:9-62` | Le 4 voci del 26-10 (colonna `membership_share_below_half`, `dendrograms`/interclasse, `mk_` nei nomi, backup `results/legacy/`) corrispondono a codice e dati | `grep` in `src/`/`tests/`, `ls`/`find` su `results/`, conteggio file per sottocartella

## `docs/setup.md` (36/36 righe)

- [V-053] | `setup.md:5,12,18` | `environment.yml` definisce `nemesis`; `conda env create -f environment.yml` risolve; l'ambiente `nemesis` esiste e si attiva | `cat environment.yml`, `conda env create -f environment.yml -n nemesis_audit_dryrun --dry-run` (piano di 220 righe, nessun ambiente creato: `conda env list` non lo mostra), `conda env list`
- [V-054] | `setup.md:26` | Sintassi di `conda env update -f ... -n ... --prune` | `conda env update --help`
- [V-055] | `setup.md:29-31` | `dadapy 0.3.4` in `nemesis_fallback`, assente da `environment.yml` e da `nemesis`; `dash` assente da `nemesis_fallback`; sezione "ADP" in `guides/clustering.md`; `"adp"` in `clustering_methods`; import lazy di `dadapy` | `importlib.metadata.version` con `python -I` nei due ambienti, `grep -n` su `docs/guides/clustering.md` e `src/analysis/adp.py`, `grep skipif` nei test
- [V-056] | `setup.md:7` | Tutti gli 11 pacchetti elencati sono in `environment.yml` e installati in `nemesis` (nilearn 0.14.0, nibabel 5.4.2, umap-learn 0.5.12...) | `conda list -n nemesis`, `importlib.metadata`

## `docs/guides/` — ciclo 10

- [V-057] | `evaluate_dim_reduction_tuning.md:10-21,27-41` | Esecuzione reale su copia di `07-10_s1.4-vol` (scratchpad): rc=0 con `overwrite: true`, 12 file, 34 s; CSV identici byte per byte a quelli preesistenti; errori chiari per config con `min_samples` mancante, per `trustworthiness` e per cartella inesistente; rc=1 con `overwrite: false` | `python -m src.pipeline.evaluate_dim_reduction_tuning --config ...` con `PYTHONPATH` e cwd = scratchpad, `cmp`
- [V-058] | `fc_matrix_building.md:5-6,23-36,52-57` | Script/config/job esistono; output `masked_fc/<combo>/` (12 combo × 10 soggetti identici) e `fc_matrix/<combo>/27-07_s3.1-<combo>/` (`matrix.npy`, `metadata.csv`, `manifest.json`, `edge_names.npy`, `config.md`); 169 × 7503 = triangolo senza diagonale di 123 nodi; `README_ARCHIVE.md` (169/10/159); nota `fc_lesion_masking.md:106` e notebook `fc_analysis.ipynb` esistono; costanti scartate e loggate | `ls`, `md5` degli elenchi, `wc -l` sul `_dseg.tsv`, lettura di `functional.py`/`build_fc_matrix.py`
- [V-059] | `understanding_umap_report.md:5-7,13-16,30-59` | Report rigenerato su copia di `13-08_s1.1-vol` (umap + tsne): rc=0, 3,6 s, due HTML da 9,6 MB con "Figure 1…5"; verifiche di coorte e di `embeddings.npz`; costanti `_CELL_PX=165`, `_CANVAS_PX=440`, 1150 soggetti; palette importata da `plotting.py` | esecuzione su scratchpad, `grep`, lettura di `understanding_umap_report.py`

## `docs/guides/` — ciclo 11

- [V-060] | `sdc_matrix_building.md:5,33,38,40,50,100,105,111-116` | 5853 soggetti × (15 `LF-disconnectome` + 16 `LF-lesion` CSV), 87 tratti streamline in tutti i file; omissione di regioni e ordine instabile nei CSV parcellati (200 soggetti: 43 conteggi, 195 ordini); matrici 5845×291345 e 5845×227235 (differenza 64110); 12 righe di `16-10_s2.4-vol` con somma = `disconnection_load_voxels_2mm`; 232/332/432 regioni; output per rappresentazione | script Python con `-I` sui file reali, `np.load(mmap_mode="r")`, `wc -l`, `ls`
- [V-061] | `dim_reduction.md:62-76,82-106,114-133` | Campi del loader; soglia 4096 di `umap-learn`; 413 GB e 5,3 GB per calcolo; forme delle quattro matrici della tabella; `eigenvalues.npy/.npz`, `runs*.csv`, nomi delle cartelle | lettura di `model_config.py`, `umap_.py`, `np.load(mmap)`, `ls`
- [V-062] | `evaluate_clustering_tuning.md:25-94,104-135` | Esecuzione reale su copia di `08-10_s1.4-vol_m_dice_nc2` (rc=0, 39 s, 12 file, 6 CSV identici byte per byte); `internal_metrics` rifiutata con `overwrite: false`; `FIGURE_DPI = 200`; parametri del notebook e limite `MAX_LEAVES` | `python -m src.pipeline.evaluate_clustering_tuning` con cwd = scratchpad, `cmp`, lettura della cella del notebook

## `docs/guides/` — ciclo 12

- [V-063] | `matrix_building.md:40,44-57,86-92,101-137` | 902.629 colonne (91·109·91) con 221.955 mantenute; matrice `uint8` {0,1} senza righe nulle; cinque file di output e tre sezioni di `config.md`; errori di scoperta delle maschere; heading e core al 10% nel notebook | `np.load(mmap)` su `07-10_s1.4-vol`, `grep`, lettura di `lesion.py`/`subject_discovery.py`
- [V-064] | `datasets.md:28-51,57-60,78,83,87-90,96-98,115-141,143-157,165-198` | Registro per dataset, maschere e `bcbtoolkit` per dataset; censimento degli header delle 5853 maschere (3 gruppi LAS+90/RAS−90/RAS−91, shape e zoom uniformi); manifest FC (169 ST + 56 HC, 10 in chiaro); tabella di copertura (6×7 celle) e punteggi WashU; 30 `both` UKE (25 con maschera); `KNOWN_SITES`; tutti i pesi in GB e le percentuali | `nibabel` sugli header di tutti i file, `pandas` sui tsv e su `participants.csv`, `os.path.getsize` su tutta la cartella
- [V-065] | `pipeline_order.md:7-18,31,62-64,75,93,101-102,117-176` | Config e job dei passi 1-7; `--dry-run` solo nei 4 file indicati; `reduced_data` e `viz_embedding_path` nel config di clustering; colonne di `participants.csv`/`sdc_metadata.csv`/`lesion_metadata.csv` | `grep`, `--help`, `pandas`

## `docs/guides/` — ciclo 13

- [V-066] | `exploration.md:1-215` | 12 notebook nelle tre cartelle; per ciascuno parametri, scritture e cache coincidono con le celle (scansione dei costanti in maiuscolo e delle chiamate di scrittura: solo `dataset_availability`, `metadata_raw`, `fc_lesion_masking` e `thiebaut_2020_replication` scrivono, come dichiara la tabella); `columns_by_dataset.xlsx` (foglio `colonne`, 7 dataset, riquadro in `B2`) e `file_types_cache.json` esistono; header di `participants_NEMESIS_T0.tsv` come scritto; 15 + 16 atlanti; 239 nodi, 28.441 connessioni; sette sezioni di `pca_evaluation`; nessuna cella mescola intestazione e testo (0 su 12 notebook); un solo `#` per notebook; tutti i rimandi (`datasets.md`, `metadata.md`, `matrix_building.md`, `evaluate_clustering_tuning.md`, `fc_matrix.md`, `sdc_matrix.md`, `covariance_pca.md`, `fc_lesion_masking.md`, `dim_reduction_tuning_guide.md`) esistono | Come: lettura del file; `nbscan.py`/`nbgrep.py` nello scratchpad sulle celle; `ls`, `openpyxl`, `head -1` sui dati; nessun notebook rieseguito
- [V-067] | `evaluation.md:1-123` | `clustering_comparison.ipynb` e la sua struttura Parte 1-4 (intestazioni e costanti `PAIR_RUN`, `LABEL_1`, `LABEL_2`); `aligned_labels`, `aligned_labels_intersection` (stampa N per lato, intersezione, esclusi; solleva se vuota), `require_shared_embedding` (4 chiavi, solleva); `agreement_metrics` passa `labels_b` come "true": la direzione di homogeneity/completeness del testo coincide con il codice e con la cella 59 del notebook; `AGREEMENT_SCALE` (ARI 0,2/0,4/0,6/0,8; NMI 0,3/0,5/0,7/0,85); `chi_square_independence` solleva sotto 2×2; `purity_table` ordinata per `purity_pct` crescente; `cluster_pair.py` (Mann-Whitney, Fisher, `r` rank-biserial, `p_fdr` Benjamini-Hochberg, raggio = distanza media dal centroide); `cluster_drivers.py` (coefficienti per deviazione standard, ValueError su separazione perfetta/collinearità); pannelli "Clustering evaluation"/"Cluster description" nell'app; il notebook `clustering_evaluation.ipynb` è rimosso; tutti i rimandi esistono | Come: lettura; `grep`/`sed` sui moduli; `load_matrix` su una cartella inesistente per riprodurre l'errore

## `docs/guides/` — ciclo 14

- [V-068] | `clustering.md:5-22,36-146,150-220` | Comando e `--help`; `jobs/run_clustering.sh`; griglie di tutti i metodi e valori di partenza (`params_clustering.json`); blocchi `consensus`/`stability`; rifiuto di `save_tuning_clusterings` con `affinity` sweeppata; elenco e applicabilità delle 11 valutazioni; regole di `reduction_params_file`/`reduced_data`; nomi dei file (`dendrogram_metric=`, `eigengap_affinity=`, `tuning_plot_cluster_selection_method=`…); cartella di tuning reale senza `tuning_plot.png` con 3 assi; produzione agglomerative con `silhouette_per_cluster.csv` e righe di `config.md` esatte (`Largest cluster`, `Average silhouette coefficient`, `— (Euclidean distance only)`, `Dendrogram jump (k=9)`); hdbscan_soft con `membership.npy` e `membership_own`; ADP (parametri, import lazy, righe a zero e duplicate, colonne di tuning, `SMALL_CLUSTER_SIZE = 10`); nessuna `production/comparison/`; intestazioni di `runs.csv`/`runs_tuning.csv`; tutti i link | Come: lettura; `--help`; `config/`, `src/analysis/*`; `ls` di `results/`; prova di `compute_silhouette_samples` con `l1`
- [V-069] | `metadata.md:3-25,58-100,108-137,153-203,207-219,240-263,265-293,310-370,390-392` | Ruolo dei due script e colonne di `participants.csv`; 18 colonne e frazioni di sede di `lesion_metadata.csv` (somma 1, dominante = primo argmax); parametri dei cinque config; numeri ricalcolati dai csv: 5150 soggetti su 5853 a 8×, 3501 esatti, 1608 che differiscono (0,2% / 2,3% / 12,8%), PSP −17% / −66%, 534 PASPORT+WAKEUP; soglia 0,20 con 1445 soggetti e 97,4% a 2 mm, 1350 e 97,3% a 1 mm con 0 differenze; `both` 25 clinici / 64 geometrici, 14 su 24 e 3 su 24; WashU 11/162 invertiti (6+5), UKLFR 2, WAKEUP 2, 1408/1430 = 98,5%; 22 righe di `excluded_subjects.csv`; registro e csv senza differenze di volume e nessuna maschera più recente; `VARIABLE_SOURCE_OVERRIDES`; messaggio «existing value(s) differ … were kept»; ancore dei rimandi | Come: lettura; script pandas su `assets/metadata/*.csv`; `--help`; `find -newer`; `grep` nel codice

## `docs/guides/` — ciclo 15 (ultima guida)

- [V-070] | `embedding_app.md:1-433` | Flag e default dell'app (`--help`); `PRODUCTION_PIPELINES`; registro dei colori e fonti; 21 e 4 soggetti su 5853 della sede; Spearman 0,9999994 tra i due carichi; massimo/mediana del volume (97); schede e indice dei pannelli (`_INDEX_SECTIONS`); i dieci selettori (`PICKER_FACETS` + `run`); `SPLIT_TAG_PARAMS`/`OPTIONAL_TAG_PARAMS`; soglie 0,02 / 0,1 / 0,5 / 30% e `MAX_QUALITY_COLUMNS = 1000`; larghezze 900 / 580 / 1700 / 560 px e `sticky` a 24 px; colori delle variabili di "Cluster description"; sei variabili di "Cluster composition"; stringhe «Tree (last merges)», «cut k=», «Will split», «Save PNG (glass brain)»; colori fino a 30; run senza `metric` del 01-09; `plot_tuning_embedding_3d` che riusa `build_embedding_figure`; tutti i link a `docs/dev/` e `knowledge/` | Come: lettura; `--help`; `grep` mirati su un file da 5538 righe; pandas su `participants.csv`; `ls`/`du` di `results/cache/`. Nessuna app avviata

## `docs/dev/` — ciclo 16

- [V-071] | `cluster_drivers.md:1-32` | Firma e ruolo del modulo; regressione senza regolarizzazione, standardizzazione, livelli di riferimento, mancanti scartati, Wald, diagnostica; costanti 10 / 15 / 1e8; il test di Woolf esiste; sezione "Confronto" non montata | Come: lettura; `cluster_drivers.py`; grep su `embedding_app.py` e `tests/`
- [V-072] | `cluster_composition.md:9-33,35` | Le sei variabili e le loro colonne; `composition_frame` e i suoi errori; `barnorm="percent"`; colori dei cluster dallo scatter; 7° output di `_update_cluster_picker`; 440 px | Come: lettura; `cluster_composition.py`; `embedding_app.py:5014-5026`
- [V-073] | `fc_matrix.md:3-47,49-56` | Moduli e 12 atlanti (2,1 MB) nelle due config; `min_coverage` 0,5; nessun Griffis 2021 in `knowledge/`; imputazione non implementata; i due bug (`int32`, parcella assente); le validazioni di `functional.py`; formato di `mask_summary.csv` (169 righe per combo); 239 → 28.441 / 57.121; 37 + 6 + 5 test | Come: lettura; `functional.py`; `config/pipelines/`; `ls` di `assets/` e `data/derived/`; conteggio dei test

## `docs/dev/` — ciclo 17

- [V-074] | `design_patterns.md:1-64` | Strategy su `REDUCTION_METHODS` / `CLUSTERING_METHODS`; registro `metadata_sources.json`; `_validate_method` con «known: […]»; controlli di `build_config.py` (interpolazione, soglia 0-1); dataclass `frozen`; `save_matrix` atomico con `manifest.json` per ultimo e `load_matrix`; nessun import verso l'alto tra `utils`, `features`, `analysis`, `pipeline`; `KNOWN_GROUPS` | Come: lettura; `grep`; `reduction.py`, `clustering.py`, `model_config.py`, `build_config.py`, `artifacts.py`
- [V-075] | `config.md:3-81` (tranne `:49`) | Tutte le funzioni di `params.py` e `model_config.py` citate; ruoli di `tag_param`/`tag_prefix`/`tag_omit` (pca); eligibilità di consensus e stability; quattro loader e quattro classi; `reduced_data`, `reduction_params_file`, `viz_embedding_path`, `save_tuning_*`, `write_report`; `run_log.py` (firma, `FIELDNAMES`, due file, nessun `id`, `extra_columns`, layout delle cartelle); `log_duration` in 16 entry point su 19 (tre esclusi come scritto); `DimReductionClusteringConfig` assente | Come: lettura; `grep`; `params.py`; `run_log.py`; `ls`/`head` di `results/*/runs*.csv`
- [V-076] | `anatomical_maps.md:7-98` | Funzioni, classi e costanti di `anatomical_maps.py` e `embedding_app.py` (36 simboli, nessuno mancante tranne `_load_and_binarize`); firme di `build_overlap_map`, `BinaryMaskStore`, `cluster_centroids_with_nearest_subject`; soglie 1e-6 / 0,02 / 0,1 / 0,5; `_GridResampler.load` con test su shape **e** affine; cache su disco (sha1, file temporaneo, una sola sottocartella); celle del notebook `dendrogram_embedding_explorer` (import, `cmap`, `black_bg`, `ortho`, `argmax`, `binary_masks`) | Come: lettura; `grep` mirati; `ls`/`du` di `results/cache`; celle del notebook

## `docs/dev/` — ciclo 18 (su HEAD `ea552f7`)

- [V-077] | `pipeline_flow.md` (tranne `:16` e `:105`) | Livelli e fonti di verità; dipendenze «per eseguire» e «per interpretare»; giro circolare della calibrazione; cartelle di matrice, nomi, layout di `results/`; scope delle esclusioni; semantica di `overwrite` (`OWN_COLUMNS` = 7, `_check_write_rules`); controlli che fanno fallire (`--dry-run` in 4 pipeline); registri mutabili | Come: lettura; `grep` di `participants`/`excluded` nelle pipeline; `--help`
- [V-078] | `cluster_comparison.md:1-100,102-115` | Sezione "Confronto" non montata; funzioni di `cluster_comparison.py` e `cluster_pair.py`; `AGREEMENT_SCALE`; direzione di homogeneity/completeness con due test; Mann-Whitney con `r = 2U/(n1 n2) − 1`, Fisher, BH; variabili numeriche e categoriche; regressione; `RdBu_r`; funzioni di `embedding_app.py` (confrontabilità) | Come: lettura; `grep` e `sed` su `cluster_pair.py`, `embedding_app.py`, `test_cluster_comparison.py`
- [V-079] | `plotting.md` (tranne `:82` per la lingua di `description`, `:96` e le parti storiche) | Palette di 10 tinte; tutte le funzioni `plot_*`/`compose_*` e le costanti numeriche di declutter, marcatori, silhouette, DPI; `wspace=0.35`; nessun grafico di confronto tra metodi; naming dei file (esempi reali su disco); campi di `ColorMode`, modi registrati, `GRID_MODES`; `PAPER_REPRODUCIBILITY = 0.813`; palette a 20 colori e `LAST_P ≤ 20` del notebook | Come: lettura; 41 pattern in `plotting.py`; `ls`/`find` in `results/`; celle del notebook

## `docs/dev/` — ciclo 19

- [V-080] | `covariance_pca.md` (tranne `:54`) | Simboli di `covariance_pca.py`, `pca_method.py`, `component_maps.py`, `pca_evaluation.py`, `background_cache.py`; dimensioni di memoria (6,8 / 5,3 GB, Gram 273 MB, 679 e 413 GB); `Rotator` con `normalize=True` e chiamata senza `normalize`; 42 componenti per il 90% (cache `pca.npz`); parametri e sezioni del notebook; cinque sezioni di `employed_dim_reduction_methods.md`; i tre file di test | Come: lettura; `grep`; `numpy` sulle forme e sugli autovalori in cache; `inspect.signature`
- [V-081] | `lesion_matrix.md` (tranne `:9`, `:30`, `:127`, `:131`) | Glob e conteggi delle 8 coorti; firma di `build_lesion_matrix`; `_binarize_on_grid`, `_needs_resample` (`_AFFINE_ATOL = 1e-3`), `force_resample=True, copy_header=True`; griglie `res-1`/`res-2` e 42 GB; `correct_out_of_brain` con `zero_out_of_brain_voxels`; 234 e 73 soggetti oltre il 5% e il 10%; config di produzione | Come: lettura; `grep`; pandas su `lesion_metadata.csv`; config
- [V-082] | `sdc_matrix.md` (tranne `:44`, `:78-83`, `:141`) | Rappresentazioni, 34 file per soggetto, etichette di riferimento 232/332/432/87, funzioni di `parcellated_csv.py` e `sdc.py`, 5852/5853 `map_min_nonzero` = 1/178, 64.110 + 227.235 colonne di `07-10`, 227.235 colonne di `16-10`, tabella dei campi del loader con quattro prove, sezioni di esclusione di `config.md` | Come: lettura; `numpy`/`nibabel` su maschere e matrici; lettura di 5853 `mapstats.tsv`; `load_build_sdc_matrix_config` su varianti del config

## `docs/dev/` — ciclo 20 (su HEAD `9267f0f`)

- [V-083] | `cluster_description.md` (tranne `:14,:40,:43,:80,:96-104,:148,:174,:184-205`) | Copertura delle cinque variabili (89,0 / 88,9 / 14,7 / 27,1 / 100%; UCL-UK 84,7 / 84,4 / 0 / 0 / 100%); colori e costanti del grafico; funzioni del pannello; numeri sul tipo di ictus (PSP 189 / 18 / 30 su 237, UKLFR 735 «ischemic stroke», 168/5853 = 2,9%); `KNOWN_VARIABLES`; file di test | Come: pandas su `participants.csv` e sui tsv; `grep` su `cluster_description.py` e `embedding_app.py`
- [V-084] | `metadata.md` (dev, tranne `:5,:71,:91,:155,:241,:249,:319,:325`) | Ruoli dei due script, `has_*` e cartelle potate, tutte le colonne di `lesion_metadata.csv` e `sdc_metadata.csv`, fino a 25 funzioni e test citati, ricalcolo di: PSP 0,83 (0,34-0,94), 4 volumi a zero (WAKEUP 8 e 3 voxel), due soggetti d'esempio, rapporti 1 mm / 2 mm per dataset, soglia 0,20 (97,44% a 0,20; 97,51% a 0,28; `both` 3 / 7 su 24), Spearman 0,906 e 0,9999994, `8×L2/L1` 1,001 (0,989-1,017), asimmetrie 1,49 / 4,10 / −0,83, 5 soggetti oltre il 30% (minimo 0,410), tre header delle mappe | Come: lettura; pandas su `assets/metadata/*.csv`; `scipy.stats`; `ls`; `grep`
- [V-085] | `models.md` | Scansione automatica di ~600 identificatori e percorsi tra apici inversi: nessun simbolo mancante tranne quattro nomi citati come rimossi / scartati / di libreria; sezioni su `tuning.py`, `distances.py`, `clustering_tuning.py`, `consensus_clustering.py`, `dbcv.py`, `clustering_evaluation.py`, `partition_shape.py`, `tuning_match.py`, `dendrogram_splits.py`, `cluster_overview.py`, `adp.py`; orchestrazione `dim_reduction.py` / `clustering.py` e inventario dei file (struttura giusta) | Come: script Python nello scratchpad su `docs/dev/models.md` contro `src/`, `tests/`, `config/`; `ls` di `results/` e `logs/`


## `docs/experiments/` — ciclo 21 (su HEAD `8c9b498`)

- [V-086] | `docs/experiments/` (12 file, tranne `README.md:10-16` conteggi di run e riga s2.4-vol 16-10, `s2.1-schaefer-200-tian-s2.md:13,19-30,53`, `s2.2-vol.md:67,79`, le intestazioni «Tuning, 12-10», `s1.4-vol.md:105`, e i riferimenti ai quattro metodi in `legacy`) | Forme, dtype e coorti per dataset di tutte e 10 le matrici; esclusioni (3 + 5 + 14); 1501 soggetti azzerati; relazioni tra le tre `metadata.csv`; colonne di s2.4-vol 07-10 / 16-10 e valori su 200 righe; maschere di s1.3 / s2.2 (238593 / 52347 / 27825; indici 4581 e 63637); righe nulle di s1.3; conteggi di run per data e per metodo in `runs.csv` / `runs_tuning.csv`; parametri di tutte le run UMAP / t-SNE di produzione; righe di tutti i `tuning_results.csv` di dim reduction (180, 20, 120, 14, 60, 7, 90, 40); tuning di s1.1, s1.2, s2.2, s2.4-stream (silhouette, rumore, salto, cluster, sonda HDBSCAN); dimensioni e rumore delle 13 produzioni di s2.4-stream; PCA 16-10 (varianza, autovalori); silhouette delle 5 combinazioni `hdbscan_soft` prodotte; tutti i link relativi e i percorsi tra apici dei 12 file | Come: `numpy`/`pandas` su `data/derived/` e `results/` (anche `legacy/`); `sklearn.cluster.HDBSCAN` e `silhouette_score` sugli embedding salvati; script dei link

## `docs/debugging/` — ciclo 21 (su HEAD `8c9b498`)

- [V-087] | `docs/debugging/` (15 file; letti per intero: `02_09_26`, `09_07_26`, `10_09_26`, `13_07_26`, `16_07_26`, `21_07_26`, `23_07_26`, `25_08_26`, `11_08_26`, `26_08_26`, `27_07_26`, `28_07_26`; parziali: `17_08_26`, `21_10_26`, `22_08_26`) | Struttura (criticità + lezione per sezione), 46+ «Seen in» → sezioni esistenti, riepilogo di `11_08_26` (2/3/5/5 + INFO), test `*_euclidean_metric_uses_distance_cache`, `test_append_to_file_missing_its_trailing_newline…`, 5 test di `27_07_26`, fix ancora in codice (`group_of` incondizionato, `app.run` con `except OSError`, `tag_param` di spectral, `drop_constant_edges`), 42 `runs*.csv` con a-capo finale e colonne coerenti, 695 mod 256 = 183 | Come: script nello scratchpad (`dbgscan.py` e varianti); `grep`; `git log -S`; lettura
- [V-088] | `docs/README.md` (tranne `:60,:73`), `docs/guides/setup.md` (intero), `docs/guides/pipeline_overview.md` (tranne `:16,:38,:111,:124`) | Link e ancore, copertura dei file di `guides/` e `dev/`, nessun rimando a `docs/setup.md`, `environment.yml` (dash incluso) e `conda env create … --dry-run`, versioni di `nemesis_fallback`, `CLUSTERING_METHODS` / `REDUCTION_METHODS`, pipeline di metadati, atlanti di sede, soglia 0,20 / 1445 / 97,4%, soglia 30%, FC senza registro né lista degli esclusi, registro delle valutazioni | Come: script dei link; `importlib.metadata` sull'ambiente `nemesis_fallback`; `conda env create --dry-run`; `grep` in `src/` e `config/`
- [V-089] | Suite di test, ciclo 21 (HEAD `8c9b498` + modifiche non committate dell'utente a `cluster_quality.py`, `embedding_app.py` e relativi test) | `pytest tests -q -x -p no:cacheprovider`: **5715 passed, 17 skipped, 0 failed** (5732 raccolti; exit code 0). Il conteggio è stato ricavato dai punti della barra di avanzamento perché `-q -q` nasconde la riga finale. Supera V-022 (5668 passed) | Come: `pytest`; `pytest --collect-only -q`

## `docs/debugging/` — ciclo 22 (HEAD `8c9b498`)

- [V-090] | `debug_22_08_26.md` (intero) e `debug_17_08_26.md` (intero) | Struttura (criticità, «Lezione», «Stato» per ogni sezione); coerenza dei conteggi finali (16+4+2+2 = 24 MEDIUM, 12+3+2+2 = 19 LOW); esistenza dei file linkati (86 link), dei test (22_08: 17/21; 17_08: 37/45) e degli identificatori (186 tra apici); stato odierno di config e codice per #1, #36, #47, #53, #41, #63, #66, #32 | Script `dbg17.py` nello scratchpad + `grep -rIw` + lettura di `config/pipelines/*.json` e `config/registry/params_clustering.json` + `git log -S`. Esiti: G-453…G-469, C-102. I fix descritti (`_needs_resample`, `_subject_dir_segment_index`, `_run_params_or_none`, `_load_embeddings_npz`, `color_values`, `_REFITTABLE_FOR_VIZ`, `_resolve_viz_embedding`) sono ancora nel codice.

## `.claude/history/` e restanti file di `.claude/` — ciclo 22

- [V-091] | `methods_changelog.md` (intero), `project_changelog.md` (r.64-971), `stato_progetto_archive.md` (riferimenti), `.claude/skills/stato-progetto/SKILL.md`, `settings.local.json`, `scheduled_tasks.lock` | Commit (`git cat-file -t`: 34 esistenti su 36 tra i due changelog), ordine delle date, percorsi, e ricalcolo delle cifre citate: massa fuori dal brain della matrice SDC 16-10 (15,3%, 112/13 soggetti, 227235 colonne), `s1.4-vol` 07-10 (1501 corretti, 177031 voxel), soglia 30% fuori dal brain, sede della lesione (conteggi per categoria), 88/61/7 run di agglomerative, 67/25/19/17 produzioni, 36 run cosine, durate 18m24s/19m54s/20m25s dai log di `compute_sdc_metadata`, 44 cartelle in `results/legacy/sdc_s2.4-vol_07-10`, struttura di `knowledge/papers/` | Script `hist.py`/`arch.py` (scratchpad) + pandas su `runs.csv`, `lesion_metadata.csv`, `config.md` di `data/derived/*` + `ps`. Esiti: G-470…G-490, C-103, C-104. Nessuna cifra di dati è sbagliata; i difetti sono frasi «oggi» superate e due hash non più nel repo.

## `knowledge/notes/` — ciclo 22

- [V-092] | `knowledge/notes/` (31 file) | Link, percorsi, fonti numerate, e ricalcolo dei numeri citati: sede della lesione (voxel per categoria a 2 mm, dominante), frazione fuori dal cervello (§3.4), calibrazione del lato (1445; 1408/1409), `gamma` di spectral su `s2.2-vol`, 413 GB / 5,3 GB della PCA, assenza di run PaCMAP, commit `8c964da` | Script `kn.py` + `build_location_categories` con il config di produzione + pandas su `lesion_metadata.csv` + `scipy.pdist` su `matrix.npy` + riepiloghi di `summaries/calibrate_lesion_side_threshold/` + `git rev-parse`. Esiti: G-491…G-502, C-105 (Media), C-106. Formule e parametri delle librerie (UMAP, HDBSCAN, PaCMAP, t-SNE) non sono verificabili nel repo: nessun controllo fatto contro i paper, a parte quelli del §3.3 di `lesion_metrics.md`.


## `knowledge/notes/` — ciclo 23 (lettura riga per riga di 29 file; verifica contro librerie, paper e pagine salvate)

- [V-093] | `knowledge/notes/dim_reduction_clustering/` (22 file) e `neuroimaging/` (7 file); `stroke_literature/` (3 file) solo nei numeri | Formule, parametri, esempi numerici, citazioni e cifre: firme e sorgente installati di `umap-learn` 0.5.12, scikit-learn 1.8.0 (`TSNE`, `trustworthiness`, `HDBSCAN`, `KMeans`, `GaussianMixture`, `SpectralClustering`, `AgglomerativeClustering`), `pacmap` 0.9.1, `hdbscan` 0.8.44, `factor_analyzer`, DADApy 0.3.4 (`nemesis_fallback`), nilearn 0.14; esempi riprodotti (HDBSCAN a 6 punti, agglomerativo a 5 punti, silhouette/DB/CH/DBCV, k-means 1D, spettrale a 4 nodi, ADP, GMM, varimax 2×2, PCA 3 punti, 84,26% di coppie a distanza dice 1, correlazione pesi–mappa t); citazioni e numeri confrontati con de Bodt, Wani, Sorzano, Fred, Dinh, le slide di Bicego, le quattro pagine web salvate, TdS 2020, Salvalaggio, Talozzi, Griffis 2019/2020, Siegel 2016/2018, Corbetta 2015, Bisogno 2021/2025, Zanola/Tshimanga; dati con pandas su `lesion_metadata.csv`, `participants.csv`, `masked_fc/*/mask_summary.csv` e i `manifest.json` di `data/derived/*` | Script `quotes.py`/`quotes2.py` (citazioni tra virgolette contro tutti i testi di `knowledge/papers/`) e `nums.py` (numeri di ogni sintesi contro il paper), più esecuzioni dirette. Esiti: G-503…G-532, C-107…C-111. Nessuna formula e nessun parametro sono sbagliati; i difetti sono citazioni alterate, attribuzioni più larghe del testo, una numerazione di fonti doppia, un rimando e un conteggio. **Non verificato**: le fonti esterne non presenti in `knowledge/papers/` (McInnes 2018, van der Maaten 2008, Wang 2021 PaCMAP, Damrich, Böhm, Kobak, Belkina, Chari & Pachter, Jolliffe & Cadima, Seghier, Foulon, ecc.) sono controllate solo dove il codice installato o un'altra fonte locale le conferma; le fasce di Kaufman & Rousseeuw sono dichiarate secondarie dalla nota.


## `knowledge/notes/stroke_literature/` — ciclo 24 (lettura riga per riga)

- [V-094] | `summaries_core.md` (20 sezioni), `summaries_related.md` (6), `scope_by_category.md` | Numeri **e** affermazioni qualitative di ogni sezione contro il testo del paper: campioni, soglie, valori, direzioni degli effetti, negazioni («solo un trend», «non significativo»), limiti dichiarati, sedi anatomiche, rapporti tra studi | Funzione `show()` (scratchpad, `ctx.py`) con ricerche mirate per ogni sezione sui `.md` di `knowledge/papers/stroke_core`/`stroke_related`; Cinetto dal `.docx` estratto con `zipfile`; Volpi 2025 letto direttamente (nome con `[18F]`). Esiti: G-533…G-552, C-112, C-113. Tutte le sintesi coincidono con le fonti nei punti controllati; i difetti sono una frase di `scope_by_category.md` e cinque dettagli non ritrovati. **Non verificato**: supplementi (Pini S1.1, TdS Supplementary Fig. 1-2, Corbetta 2015), figure (Griffis 2019 Fig. 2B), Park 2016 e Jimenez-Marin 2022 (nessuna fonte), Tshimanga 2025 (nessuna sintesi).


## `docs/dev` e `docs/guides` toccati dagli ultimi commit e dal working tree — ciclo 25

- [V-095] | `docs/dev/models.md` (sezione `dendrogram_splits`), `docs/dev/cluster_description.md:174`, `docs/dev/covariance_pca.md`, `docs/guides/embedding_app.md` (diff non committato), `docs/guides/exploration.md:150`, `README.md` (albero di `results/`) | Ogni frase modificata dopo l'ultimo audit contro il codice e il disco: firme e `ValueError` di `run_palette`/`build_split_tree`, `_italian_figure` su tutte le `dcc.Graph`, `format_number`/`PLOTLY_SEPARATORS`, gestione dell'errore nel callback del dendrogramma, percorsi `results/cache|tables|legacy`, assenza di `results/pipeline_building` in doc e codice; test del working tree | `git diff`, `grep`, `ls`, lettura di `dendrogram_splits.py` e di `embedding_app.py`; `pytest` su `test_dendrogram_splits`, `test_cluster_quality`, `test_number_format`, `test_embedding_app_{dendrogram,all_clusters,quality}`, `test_prop_cluster_quality`: **182 passed**, 6 warning (sklearn `copy`). Esiti: G-553…G-559, C-114, C-074 esteso. Non rilanciata l'intera suite (ultimo esito completo: 5715 passed, V-089).

## Correzioni applicate dopo la revisione delle Medie (29-10-26)

- [V-096] | `src/features/functional.py::build_fc_matrix_from_raw`, `src/pipeline/build_fc_matrix.py`, `src/analysis/build_config.py`, `src/analysis/embedding_plots.py`, `tests/legacy/`, `src/pipeline/{generate_understanding_umap_report,replot_dim_reduction}.py` | Le modifiche decise dall'utente (selettore `group` ST/HC in `build_fc_matrix`; errori attesi nei grafici; `log_duration` nei due entry point; funzioni di kmeans/gmm in `tests/legacy/`) sono nel codice e nei test | Verificato: `pytest tests/ -q` = **5771 passed, 17 skipped, 0 failed** (189 s). Prima 5715 passed (V-089); la differenza include 20 test nuovi per l'HC, 2+2 per i grafici, 2 per la durata e i test del lavoro non committato dell'utente.

