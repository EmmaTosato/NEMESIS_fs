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
