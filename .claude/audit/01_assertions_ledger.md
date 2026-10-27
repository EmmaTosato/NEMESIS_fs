# 01 — Registro delle affermazioni (memoria a lungo termine)

Formato: `- [ID] | Fonte: file:riga | Affermazione | Stato`. Stati: **Verificato** · **Falso** · **Parziale** · **Da verificare in Fase 2** · **Da verificare in <file>**.
Consultare SEMPRE prima di validare una nuova frase. Rimandi `C-xxx` = voce in `02_contradictions_and_open_issues.md`.

## [ARCHITETTURA]

- [A-001] | `.claude/CLAUDE.md:7` | `src/` implementa matrix building (lesion/FC/SDC), metadata, pipeline embedding/clustering; suite pytest in `tests/unit/` + `tests/integration/` | Verificato (cartelle esistono; 5685 test raccolti)
- [A-002] | `CLAUDE.md:7` | `README.md` ha la sezione "What's implemented so far" | Verificato (README:64)
- [A-003] | `CLAUDE.md:17` | I dati grezzi stanno su EBRAIN, percorsi in `docs/guides/datasets.md` | Verificato (`datasets.md:5`: `/data/corbetta/Clinical_connectome`)
- [A-004] | `CLAUDE.md:17` | I `*.nii`/`*.nii.gz` sono gitignored | **Parziale**: nessun pattern `*.nii*` in `.gitignore`; sono esclusi solo da `data/*`; 22 `.nii.gz` sono tracciati (atlanti/template in `assets/`) → C-003
- [A-005] | `CLAUDE.md:21` | Ogni guida in `docs/guides/` documenta sia l'esecuzione locale sia quella `sbatch` | **Parziale**: 12 guide su 14 citano `sbatch`; `datasets.md`/`evaluation.md` no (non sono pipeline). Il "documenta entrambe" per ogni guida pipeline va ancora confermato guida per guida → C-008
- [A-006] | `CLAUDE.md:23` | `python -m src.pipeline...` per `src/pipeline/`; `PYTHONPATH="$PROJECT_ROOT" python scripts/...` per `scripts/` | Verificato per `scripts/` (`jobs/run_build_dataset_summary_table.sh`: `export PYTHONPATH` + `python scripts/...`; docstring di entrambi gli script con `PYTHONPATH=.`). Da verificare in `guides/pipeline_order.md:30`: `populate_metadata` "richiede anche PYTHONPATH" (ridondante con `-m` da root?)
- [A-007] | `CLAUDE.md:24` | Un job per pipeline in `jobs/run_<nome>.sh`, file singolo | Verificato: 18 job, nessun job orfano, nessuna sottocartella
- [A-008] | `CLAUDE.md:24-27` | Il job di riferimento `run_build_lesion_matrix.sh` ha header `#SBATCH`, `source conda.sh` + `conda activate nemesis`, `cd` root, stessa invocazione della guida | Verificato per header/conda/cd; invocazione vs `guides/matrix_building.md` da verificare in quel file
- [A-009] | `CLAUDE.md:25` | `-o`/`-e` puntano a `logs/slurm/<pipeline_name>/%j.{out,err}` | Verificato su tutti i 18 job (percorsi assoluti `/home/etosato/...`: vedi C-013)
- [A-010] | `CLAUDE.md:29` | Ogni pipeline/script in `src/pipeline/` o `scripts/` ha il suo `jobs/run_<nome>.sh` | **Falso** per `embedding_app.py` e `scripts/archive_local_raw_data.py` → C-007
- [A-011] | `CLAUDE.md:35` | Le guide elencate esistono (matrix_building, fc_matrix_building, sdc_matrix_building, dim_reduction, evaluate_dim_reduction_tuning, evaluate_clustering_tuning, clustering, embedding_app, understanding_umap_report, metadata, exploration, evaluation, pipeline_order, datasets) | Verificato: tutte e 14 esistono, nessuna in più
- [A-012] | `CLAUDE.md:35` | Ritirati: `dim_reduction_clustering.md` (14-08-26), `atlas_building.md` (25-08-26, commit `2ed3dcb`), `retrieval.md` e `compute_sdc.md` (05-10-26) | Parziale: i quattro file non esistono; `atlas_building.md` rimosso da `2ed3dcb` il 2026-08-25 ✓ (il messaggio del commit non cita gli atlanti: `--stat` sì); `retrieval`/`compute_sdc` rimossi da `d8dbdee` 2026-10-05 ✓; `dim_reduction_clustering.md` rimosso da `2991ec1` il **2026-08-15**, non 14 → C-009
- [A-013] | `CLAUDE.md:35` | `metadata.md` guide = `enrich_metadata.py` (06-09-26); `evaluate_clustering_tuning.md` = cofenetica, salto, quota cluster più grande | Parziale: le guide oggi coprono 5 pipeline metadata e DBCV/Dunn ecc. (stato_progetto:14, README:84-99) → C-004
- [A-014] | `CLAUDE.md:36` | Elenco di `docs/dev/` | Parziale: tutti i 14 file citati esistono; **manca `covariance_pca.md`** (esiste, 129 righe) → C-005
- [A-015] | `CLAUDE.md:36` | `docs/dev/metadata.md` descrive "i 3 livelli di metadati" | **Falso/obsoleto**: `dev/metadata.md:37` dice "Quattro file, cinque domande" → C-004
- [A-016] | `CLAUDE.md:36` | `cluster_comparison.md` copre la sezione "Confronto" di `embedding_app.py` | Parziale: la sezione non è montata (`comparison_content_for` :3206 e `cluster_pair_content_for` :3450 senza chiamanti; `stato_progetto:42`) → C-006
- [A-017] | `CLAUDE.md:37` | `docs/notes/` non esiste più; dissolta nel merge `docs/dr-clustering-literature-migration` il 18-08-26; contenuti in `knowledge/notes/{dim_reduction_clustering,neuroimaging}` | Parziale: `docs/notes/` assente ✓, contenuti nelle cartelle indicate ✓, merge `f9e2d30` datato **2026-08-21** → C-009
- [A-018] | `CLAUDE.md:38` | `docs/experiments/`: file `sX.Y-<formato>.md` + `README.md`, `lineage.md`, `pipelines.md` | Verificato (esistenti). Contenuto → audit di `docs/experiments/`
- [A-019] | `CLAUDE.md:39-40` | `docs/debugging/` e `docs/setup.md` esistono | Verificato
- [A-020] | `CLAUDE.md:33` | Le note grezze delle riunioni vivono sotto `assets/` | **Falso**: `management/meetings/` (CLAUDE.md:41, README:50) → C-001
- [A-021] | `CLAUDE.md:41-42` | `management/meetings/`, `management/cheatsheets/`, `management/nemesis_project/`, `management/slides/` | Verificato (esistono)
- [A-022] | `CLAUDE.md:44` | `knowledge/notes/` = `dim_reduction_clustering/`, `neuroimaging/`, `stroke_literature/` (`summaries_core.md`, `summaries_related.md`, `scope_by_category.md`) | Verificato
- [A-023] | `CLAUDE.md:45` | `knowledge/papers/` = `stroke_core/`, `stroke_related/`, `methods/`, `index.md` | Verificato (esistenza). Fuori perimetro Fase 1
- [A-024] | `CLAUDE.md:46` | Struttura docling per paper (`manifest.json`, `figures.json`, `figures/`...) | Da verificare (fuori perimetro: `knowledge/papers/`)
- [A-025] | `CLAUDE.md:47` | `src/` = `features/`, `analysis/`, `utils/`, `pipeline/` | Verificato (nessun'altra cartella)
- [A-026] | `CLAUDE.md:48` | `scripts/` solo utility accessorie; ogni CLI di analisi è in `src/pipeline/` | Verificato: 2 script (`archive_local_raw_data`, `build_dataset_summary_table`)
- [A-027] | `CLAUDE.md:54-58` | `.claude/history/` ha `data_changelog.md`, `methods_changelog.md`, `project_changelog.md`, `stato_progetto_archive.md`; skill `history` | Verificato (esistenza; `.claude/skills/history/SKILL.md`). Contenuto → audit `history/`
- [A-028] | `CLAUDE.md:53` | `docs/guides/`, `docs/dev/`, `README.md` parlano solo al presente | **Falso in pratica** (README:66-72 sezione "Retired pipelines"; `guides/datasets.md:5`; `dev/metadata.md:71,103`) → C-010 (conferma file per file)
- [A-029] | `CLAUDE.md:60` | Provenienza run in `runs.csv` + `logs/`/`summaries/` | Da verificare in Fase 2 (`logs/`, `summaries/`)
- [A-030] | `CLAUDE.md:63` | In ogni notebook ogni heading markdown sta da solo nella sua cella | Verificato: scansione di tutte le celle markdown dei 13 notebook, 0 violazioni (heading + altro testo, o più heading, nella stessa cella)
- [A-031] | `CLAUDE.md:64` | Nessun commit automatico: `code_standards.md` §9 | Verificato (§9 esiste e lo dice)
- [A-032] | `CLAUDE.md:68,74` | `@code_standards.md` e `@lessons_learned.md` sono import validi (relativi a `.claude/`) | Verificato (entrambi in `.claude/`, 123 e 191 righe)
- [A-033] | `CLAUDE.md:70` | `code_standards.md` si applica a `src/` e ai suoi test | Parziale: `code_standards.md:3` dice `src/`, `scripts/` e test → C-011
- [A-034] | `CLAUDE.md:76` | `lessons_learned.md` si aggiorna dopo ogni sessione di debug "per code_standards §8" | Verificato che §8 esiste. NB: §8 cita il file come `lesson_learned.md` (singolare), da verificare in `code_standards.md` → nota per quel file

## [CONFIG/PARAMETRI]

- [P-001] | `CLAUDE.md:11` | L'ambiente conda `nemesis` è in `environment.yml` con "numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn" | **Parziale**: ambiente `nemesis` esiste (`/opt/anaconda3/envs/nemesis`); il file ha anche python 3.11, hdbscan, plotly, openpyxl, pytest, pytest-cov, hypothesis, factor_analyzer, pacmap, e **non** ha `dash` (importato in `src/analysis/embedding_app.py`) → C-002
- [P-002] | `CLAUDE.md:13-17` | `conda activate nemesis`; crea/aggiorna da `environment.yml` (dettagli in `docs/setup.md`) | Verificato (setup.md esiste, 36 righe; contenuto da auditare)
- [P-003] | `docs/setup.md:31` (letto di passaggio) | `dadapy` non è in `environment.yml`, vive in `nemesis_fallback`, che "non ha dash" | Verificato: `nemesis_fallback` esiste; `dadapy` non è in `environment.yml`. Implica che `dash` sia in `nemesis`, ma non è in `environment.yml` → C-002

## [CODICE/API]

- [K-001] | `CLAUDE.md:23` | Comandi `python -m src.pipeline.<nome>` | Da verificare in Fase 2 (dry-run `--help`)
- [K-002] | `CLAUDE.md:47` | `src/utils/subject_ids.py` è il posto del naming dei soggetti (da README:69 / code_standards riferimenti) | Verificato (file esistente, 34 righe)

## [TEORIA/PAPER]

- (nessuna in `CLAUDE.md`)

## [ESPERIMENTI/METRICHE]

- [E-001] | `CLAUDE.md:7` | Suite pytest verde | Da verificare: 5685 test raccolti; esito della run completa → vedi `03_resolved_and_verified.md`

## [STATO_BRANCH]

- [B-001] | `CLAUDE.md:37` | Branch `docs/dr-clustering-literature-migration` mergiato | Verificato: `git log` mostra il merge `f9e2d30` (2026-08-21); il branch non esiste più. Branch attuali: `main`, `origin/main`, `origin/server-pnc` → confronto con `.claude/branch_alignment.md` quando lo si audita
- [B-002] | stato iniziale della sessione | working tree pulito, HEAD `f577b6a` ("logs"), `.claude/stato_progetto.md:34` dice "HEAD `790fcc1`" con lavoro non committato | **Falso/obsoleto** (stato_progetto) → da registrare quando si audita `stato_progetto.md`

---

# `.claude/stato_progetto.md` (50 righe) — audit del 2026-10-26

## [STATO_BRANCH]
- [B-003] | `stato_progetto.md:34` | Branch `main`, HEAD `790fcc1`, working tree con lavoro non committato (`anatomical_maps.py`, `cluster_overview.py`, `dendrogram_splits.py`, `tuning_match.py`, test, notebook, doc) | **Falso/obsoleto**: HEAD `f577b6a`, `790fcc1` è 16 commit indietro; a inizio sessione il tree era pulito; ora risulta modificato solo `.claude/history/project_changelog.md` (+17 righe, non fatte da me) → C-014
- [B-004] | `stato_progetto.md:3` | Ultimo aggiornamento 2026-10-23 | Verificato (mtime 23 ott)

## [ARCHITETTURA]
- [A-035] | `stato_progetto.md:7` | `docs/dev/` contiene `models, config, plotting, lesion_matrix, fc_matrix, sdc_matrix, design_patterns, metadata, covariance_pca` | Parziale: esistono tutti, ma mancano `anatomical_maps`, `cluster_comparison/composition/description/drivers`, `pipeline_flow` → C-016
- [A-036] | `stato_progetto.md:9` | "cinque file in `assets/metadata/`, ognuno scritto da una pipeline" | Parziale: 4 CSV + `participants_protected.json` + 2 `*.config.json`; le pipeline sono 5, `participants.csv` è scritto da due → C-004
- [A-037] | `stato_progetto.md:11` | `pca` in `REDUCTION_METHODS`, `src/analysis/pca_method.py`, varimax, `rotation_n_components`, `covariance_pca.py` | Verificato (`reduction.py`, `pca_method.py:13`, `covariance_pca.py`)
- [A-038] | `stato_progetto.md:13` | Le valutazioni si dichiarano in `tuning_evaluations` (`clustering.json`, `evaluate_clustering_tuning.json`), parametri in `config/registry/clustering_evaluations.json`, girano con `run_evaluations` | Verificato (`clustering_tuning_evaluations.py:303`; chiavi: k_curves, cophenetic_correlation, dendrogram_jump, linkage_agreement, largest_cluster_share, dunn_index, density_metrics, dbcv_curves, tuning_heatmaps, internal_metrics)
- [A-039] | `stato_progetto.md:13` | `report.md` scritto da `clustering_tuning_report.py` leggendo i file, senza calcolare | Parziale: modulo esiste e cita Dunn/quota; "senza calcolare" da verificare in Fase 2
- [A-040] | `stato_progetto.md:14` | HDBSCAN/`hdbscan_soft`: DBCV euclideo in `src/analysis/dbcv.py`, NaN con <2 cluster; valutazioni `density_metrics`, `tuning_heatmaps`, `dbcv_curves`; produzione: `dbcv_per_cluster.csv`, `dbcv_plot.png`, riga in `config.md`; pannello DBCV nell'app | Verificato (`dbcv.py:27,52,65`; `pipeline/clustering.py:707-708`; `embedding_app.py:2410`, `cluster_quality.build_dbcv_figure`); spec `_DENSITY_ONLY`
- [A-041] | `stato_progetto.md:14` | Silhouette/CH/DB/Dunn non si calcolano per HDBSCAN | Verificato (`clustering_tuning_report.py:84`)
- [A-042] | `stato_progetto.md:15` | Agglomerative: cofenetica, salto, ARI tra linkage, `largest_cluster_share`, `dunn_index`; il report ha `dunn` e quota nelle tabelle | Verificato (spec e `clustering_tuning_report.py:59,65`)
- [A-043] | `stato_progetto.md:16` | `kmeans`, `gmm`, `spectral`, `adp` fuori dalla catena; `evaluate_clustering_tuning` li rifiuta; `adp` solo `report.md` | Parziale: le spec sono ristrette ad agglomerative/densità e `adp` è trattato a parte (`evaluate_clustering_tuning.py:19,68`); il rifiuto esplicito degli altri tre non provato con una run → Fase 2
- [A-044] | `stato_progetto.md:17` | `internal_metrics` ricalcola le colonne dello sweep, solo con `overwrite: true`, non è nei config di default | Verificato per esistenza della valutazione e per `clustering_evaluations.json`; "non nei config di default" da verificare in Fase 2
- [A-045] | `stato_progetto.md:15` vs `:37` | CH e DB "solo con metric euclidea: vuoti altrimenti, ovunque" (L15) vs "per Dunn, CH e DB nel notebook e nella produzione di agglomerative resta da fare" (L37) | **Contraddizione interna** → C-017
- [A-046] | `stato_progetto.md:15` vs `:50 (3)` | Dunn e quota del cluster più grande già nel registro (L15) vs "decidere le metriche ancora fuori dal registro (Dunn, quota...)" (L50) | **Contraddizione interna** (il registro le ha entrambe) → C-017
- [A-047] | `stato_progetto.md:26` | `clustering_comparison.ipynb`: homogeneity e completeness scambiate, da togliere | **Falso/obsoleto**: nessuna chiamata sklearn nel notebook; usa `agreement_metrics` (`cluster_comparison.py:170-171`: `homogeneity_score(labels_b, labels_a)`); il testo della cella 59 coincide con quel codice → C-015
- [A-048] | `stato_progetto.md:27` | `clustering_evaluation.ipynb` ha la sezione 2.3 DBCV, non rieseguito, da spostare in `pipeline_building` | Parziale: sezione 2.3 presente (celle 27-28); riesecuzione/spostamento non verificabili senza esecuzione → Fase 2
- [A-049] | `stato_progetto.md:36` | Il criterio «usabile» è tolto da `s2.4-vol.md` ma resta in `s1.4-vol.md`, `s2.4-stream.md`, `pipelines.md` | Verificato (grep)
- [A-050] | `stato_progetto.md:41` | Script `build_dim_reduction_strategies_csv.py` ritirato, commit `3e53099` | Verificato (2026-10-16 "Retire build_dim_reduction_strategies_csv.py..."; script e CSV assenti)
- [A-051] | `stato_progetto.md:42` | Sezione "Confronto" rimossa, builder e test non montati | Verificato (nessun chiamante; vedi C-006)
- [A-052] | `stato_progetto.md:43` | Diagnostic grid oltre 2D via `plot_tuning_embedding_3d.py` | Parziale: il file esiste; comportamento → Fase 2
- [A-053] | `stato_progetto.md:44` | Solo `UNIPD/WashU/features/` e `masked_fc/` ridotte a 10 soggetti | Verificato: WashU features = 10 soggetti + 2 file archivio; `masked_fc/Yan100TianS1Buckner7N` = 10 soggetti + `mask_summary.csv`. Le altre cartelle (UCL-UK, UKE, UKLFR) sono voluminose
- [A-054] | `stato_progetto.md:45` | `enrich_metadata`: `overwrite` e `protected_path` obbligatori; con `true` una cella vuota svuota il registro | Verificato per i campi nel config e nel docstring (`enrich_metadata.py:98,106`); effetto "svuota" → Fase 2
- [A-055] | `stato_progetto.md:46` | `excluded_subjects.csv`: `false` aggiunge senza toccare, `true` ricostruisce dal solo config | Verificato (`build_excluded_subjects.py:11-18`, `run_notes`)

## [CONFIG/PARAMETRI]
- [P-004] | `stato_progetto.md:38` | `dim_reduction.json` = PCA di produzione su `16-10_s2.4-vol`; `clustering.json` = tuning su `19-10_s2.4-vol_nc12_varimax` | Verificato (`input_path`, `fine_tuning: true`, metodi agglomerative/hdbscan/hdbscan_soft)

## [ESPERIMENTI/METRICHE]
- [E-002] | `stato_progetto.md:21` | s2.4-vol del 16-10: 227235 colonne, 5845 soggetti; clustering di produzione 29 run su 30, manca `hdbscan_soft` nc10 mcs100 ms20 eom | Da verificare: in `results/sdc/clustering/production/` le cartelle sono `19-10_s2.4-vol_nc{2,12,30}_...` (agglomerative 31, hdbscan 20, hdbscan_soft 20), nessuna `nc10` → C-018; 5845 soggetti coerente con `participants.csv` (5853 righe incl. header? da confermare nei metadati)
- [E-003] | `stato_progetto.md:22,23,24,25,28` | Report HDBSCAN vecchi non rigenerati; `hdbscan_soft` non confrontabile con `hdbscan`; metadati 06-10-26; audit passi; s2.1 nc3 | Da verificare in `methods_changelog.md`, `open_problems.md`, `docs/experiments/*`
- [E-004] | `CLAUDE.md:7` (chiusura) | Suite pytest | **Verificato**: `5668 passed, 17 skipped` in 196 s (= 5685 raccolti)

---

# `.claude/code_standards.md` (123 righe) — audit del 2026-10-26

Scansioni statiche (AST) su `src/` (76 file) e `scripts/` (2 file): 960 funzioni, 478 pubbliche. Script non versionato (scratchpad); risultati qui sotto.

## [ARCHITETTURA] regole di struttura e qualità
- [S-001] | `code_standards.md:3` | Le regole valgono per `src/`, `scripts/` e test | Verificato come perimetro; rimanda a C-011
- [S-002] | `:16-29` | Esempio "Va bene": `Dataset.has_derivatives`, `manual_masks` | **Obsoleto**: nessun simbolo in repo (modulo ritirato) → C-027
- [S-003] | `:40` | Livelli `utils → features → models/analysis → pipeline`, mai dall'alto verso il basso | **Verificato**: 0 import verso livelli superiori. Non esiste `src/models/` → C-028
- [S-004] | `:41` | Una responsabilità per modulo | **Parziale**: `embedding_app.py` ha 5540 righe, `build_app` 1543 → C-022
- [S-005] | `:42` | Nessuno stato globale | Verificato: 0 `global`; 43 contenitori a livello di modulo, tutti in MAIUSCOLO (costanti/tabelle). Path `LOGS_ROOT`/`REPORTS_ROOT`/`METADATA_ROOT` → C-025
- [S-006] | `:44` | Entry point unico in `src/pipeline/`, niente script sparsi | Verificato: 18 pipeline; `scripts/` ha 2 utility (A-026)
- [S-007] | `:52` | Type hints su ogni funzione pubblica | **Parziale**: 472/478 complete (98,7%); mancanti `clustering.py:36 hdbscan_soft_fit` (ritorno), `:53 soft_membership_matrix` (parametro), più 4 funzioni interne → C-029
- [S-008] | `:53` | Funzioni piccole, idealmente <30 righe | **Parziale**: 211/960 (22%) >30, 55 >60, 18 >100, 2 >200 → C-022
- [S-009] | `:55` | Niente codice morto | **Parziale/Falso**: 0 definizioni senza riferimenti, ma 6 solo nei test → C-023 (+ C-006)
- [S-010] | `:56` | Niente shim/commenti `# rimosso` | **Parziale**: nessun wrapper trovato; `plotting.py:64-67` commenta una funzione rimossa → C-028
## [CODICE/API] errori, test, config, logging
- [S-011] | `:62` | Mai `except:` nudo o `except Exception: pass` | Verificato: 0 nudi, 0 con solo `pass`/`continue`
- [S-012] | `:63` | Eccezioni specifiche | **Parziale**: 9 `except Exception`, di cui 4 puliscono e rilanciano (`compute_sdc_metadata.py:156`, `compute_lesion_metadata.py:164`, `enrich_metadata.py:980`, `populate_metadata.py:324`) e `background_cache.py:64` (`BaseException`, rilancia): legittimi; 5 in `embedding_plots.py:63,72,88,115,134` inghiottono e proseguono → C-019
- [S-013] | `:64` | Ogni eccezione sollevata ha un messaggio | Verificato: 0 `raise X()` senza argomenti
- [S-014] | `:65` | `None` solo come caso di dominio documentato | Da verificare in Fase 2 (non decidibile staticamente)
- [S-015] | `:73` | `tests/` specchia `src/` | Verificato: ogni modulo di `src/` è citato da almeno un test
- [S-016] | `:74` | Ogni bug fix ha un test di regressione | Da verificare in `docs/debugging/` (un report alla volta)
- [S-017] | `:75` | Almeno un E2E con dati reali piccoli | Parziale: `tests/integration/test_pipeline_chain_e2e.py` (183 righe) esiste; contenuto → Fase 2
- [S-018] | `:76` | Mock solo su I/O esterno | **Parziale**: 315 `monkeypatch.setattr`, ~295 spostano costanti di percorso su `tmp_path`, ~13 sostituiscono funzioni del repo → C-024
- [S-019] | `:77` | Suite verde con conteggio esatto | Verificato: 5668 passed, 17 skipped (V-022)
- [S-020] | `:83` | Nessun valore d'ambiente hardcoded in codice | **Verificato** per `src/` e `scripts/` (0 percorsi assoluti). I `jobs/` restano C-013
- [S-021] | `:86` | Niente campi di config non letti | Verificato: tutte le chiavi dei 13 `config/pipelines/*.json` compaiono come stringa in `src/`; le uniche non trovate sono iperparametri passati alle librerie (`learning_rate`, `max_iter`, `approx_min_span_tree`, `assign_labels`, `covariance_type`, `FP_ratio`, `MN_ratio`, `apply_pca`, `early_exaggeration`) e nomi di dataset in `metadata_sources.json`
- [S-022] | `:92` | Log in inglese | Verificato (euristica): 257 chiamate, 0 messaggi con ≥3 parole italiane
- [S-023] | `:94` | Ogni eccezione loggata con `exc_info=True` | **Falso alla lettera**: 73 su 114 log di errore/warning dentro `except` non hanno `exc_info` e non rilanciano → C-020
- [S-024] | `:96` | Ogni entry point `src/pipeline/*.py` logga la durata dentro un `finally` | **Parziale**: 15/18 sì (tutti in `finally`); mancano `embedding_app.py`, `generate_understanding_umap_report.py`, `replot_dim_reduction.py` → C-021. `log_duration` esiste in `logging_setup.py:29`; `debug_25_08_26.md` esiste
## [DOCUMENTAZIONE / PROCESSO]
- [S-025] | `:109` | Report in `docs/debugging/debug_DD_MM_YY.md` | Verificato: tutti i 15 file rispettano il formato
- [S-026] | `:110` | Il file delle lezioni è `lesson_learned.md` | **Falso**: è `.claude/lessons_learned.md` → C-026 (chiude A-034)
- [S-027] | `:116` | Nessun commit automatico, fonte unica; `CLAUDE.md` vi rimanda | Verificato (`CLAUDE.md:64`)
- [S-028] | `:122-123` | Link a `CLAUDE.md` e `src/utils/subject_ids.py`; `subject_ids.py` solleva su sito non registrato | Verificato (`KNOWN_SITES` + `fullmatch`, `ValueError`)
- [S-029] | `:102` | Aggiornare `docs/` a ogni cambio, rimozioni comprese | Da verificare con l'audit di `docs/`

---

# `.claude/branch_alignment.md` (40 righe) — audit del 2026-10-26

## [STATO_BRANCH]
- [B-005] | `branch_alignment.md:3` | Si lavora su `main` da due checkout (server e PC); branch temporanei mergeati e cancellati | Verificato: l'unico branch locale è `main` (`f577b6a`), tracking `origin/main`, 0 avanti / 0 indietro; nessun branch temporaneo, nessuno stash, nessun tag
- [B-006] | `:3` | `origin/server-pnc` è un ref storico non più toccato | **Parziale**: ultimo commit 2026-08-22; ma 13 commit su 21 non sono in `main` (8 sono patch-equivalenti), tra cui log di produzione di `compute_sdc` del 3-7 agosto → C-030
- [B-007] | `:5` | Nessuna eccezione di file/cartelle su `main` | Verificato: nessun file escluso per checkout; i file solo locali (`.claude/settings.local.json`, `.claude/scheduled_tasks.lock`) sono ignorati da regole fuori dal repo (`~/.config/git/ignore`, `.git/info/exclude`), non da `.gitignore`
- [B-008] | `:9-12` | `git pull` prima di lavorare, `git push` dopo; il push fallisce se l'altro lato è avanti | Verificato come comportamento git (2.48.1; `pull.rebase` non impostato: su divergenza `git pull` si ferma, come descritto sotto)
- [B-009] | `:18-24, 31-35` | Sequenza `status`/`stash`/`fetch`/`rebase origin/main`/`stash pop`; `log main..origin/main` | Verificato (comandi validi; `origin/main` esiste)
- [B-010] | `:40` | `data/`, `results/`, `logs/`, `summaries/` sono gitignored e non tracciati | **Falso** per `logs/` (792 file) e `summaries/` (51 file): tracciati dal commit `f577b6a` (2026-10-23), che ha rimosso da `.gitignore` la regola `d0ecbbf` "ignore all logs and summaries directories" (2026-08-31) e ha aggiunto 813 file (+27402 righe). Vero per `data/` (0 tracciati) e `results/` (0) → C-003

---

# `.claude/open_problems.md` (215 righe) — audit del 2026-10-26

## [ESPERIMENTI/METRICHE] — dati (righe 11-75), verificati rieseguendo i calcoli sui dati locali
- [X-001] | `open_problems.md:15` | 168 maschere PSP frazionarie (multipli di 1/8), gli altri 7 dataset binari | **Verificato** (168/168 non binarie, tutte multipli di 1/8; PASPORT 83, NEMESIS_T0 76, WashU 195 binarie)
- [X-002] | `:17` | A 1 mm `>0,5` dà un volume 0,83 volte il vero (mediana) | **Verificato** (mediana 0,83 su 168)
- [X-003] | `:25` | WashU: 11 su 162 con lato clinico discordano (6 left→right, 5 right→left, |LI|≥0,95); header identico sulle 195 maschere | **Verificato** (11/162; 6+5; min |LI| 0,953; 1 header distinto su 195)
- [X-004] | `:25,30` | Mancini 5/16, destrimani 6/146, Fisher p=0,0016; i 6 casi `0002,0026,0056,0077,0147,0222`, i 2 `0008,0179`, indecidibili `0131,0151,0187` | **Verificato** (stessi numeri; i 11 ID coincidono)
- [X-005] | `:29` | Calibrazione sui 151 concordi: ARAT 90/92, 9HPT 102/119 | **Verificato** (ARAT 90/92; 9HPT 17/119 con "valore alto = peggiore", quindi 102/119 con il segno opposto: nel tsv 9HPT è evidentemente una velocità; la direzione non è scritta nel documento)
- [X-006] | `:34` | `geometric_override_datasets: []`; per gli 11 `lesion_side_source = "clinical"` | **Verificato** (`enrich_metadata.json:29`; `participants.csv`: 11 su 11 `clinical`)
- [X-007] | `:66` | UKLFR: braccio più deficitario omolaterale, 75/75; solo 5a/5b | **Parziale**: qualitativamente vero (82/82 omolaterali), ma i soggetti asimmetrici sono 82, non 75 → C-035
- [X-008] | `:68-74` | `sub-STUKLFR0671`: maschera 182×218×182, float64, 0 voxel; `mapstats` dice 0; in `excluded_subjects.csv` (`empty_mask`, `all`) | **Verificato** (anche `n_nonzero_voxels = 0`)
- [X-009] | `:60-62` | 5845 lesioni in scope; dominante «non etichettato» 27 (17 UCL-UK, 9 WAKEUP, 1 PSP); 121 con >20% non etichettato; infratentoriali >10%: UKLFR 0,1%, PASPORT 0% | **Verificato** (5853−8 esclusi=5845; 27; 121; 0,14%; 0%). Presente la categoria `cortex_white_boundary` (21)
- [X-010] | `:81-84` | FC `mask_summary.csv` (02-09) vs CSV mascherati (24-07): 7 su 10 coincidono, 0005 (3 vs 2), 0006 (10 vs 9), 0009 (2 vs 0) | **Verificato** (stessi dieci valori; `mask_summary` 169 righe)
- [X-011] | `:207` | `s2.2-vol` 1570 × 290940 `float32` | **Verificato**
- [X-012] | `:47-54,19,21,38` | Tabella dei baricentri 1 mm vs originali, `map_min_nonzero=0,125`, `bcblib 0.6.1`, T1 duplicate byte per byte (`0053/0060`, `0066/0077`), controlli E/F, 7 T1 con `AcquisitionTime` uguale | **Da verificare sul cluster** (le originali e le T1 non sono in locale; il testo stesso dice "riferito dall'agente, non rieseguito")
## [CODICE/API] (righe 76-203)
- [X-013] | `:110` | `dunn_index` e `largest_cluster_share` sono valutazioni del registro | Verificato (`clustering_evaluations.json`) — contraddetto da `:132` → C-017
- [X-014] | `:175-180` | `evaluate_pca`: docstring «unchanged by a rotation» (`tuning.py:127`); `_WARD_SAFE_METRICS` contiene `l2` (`clustering_tuning.py:99`); `_combo_key` duplica `tuning_embeddings.combo_key` (`clustering.py:1037`, il testo dice :1050); `SILHOUETTE_OWN_METRIC_METHODS = ("adp",)` (`clustering.py:619`); `dim_reduction.py:396-399` «already enriched» | **Verificato** (solo il numero di riga di `_combo_key` è cambiato)
- [X-015] | `:176` | 4 funzioni di `clustering_tuning.py` + `subsampling_stability_index` chiamate solo dai test | Parziale: lo scan AST ne ha trovate 2 (`integrated_completed_likelihood`, `compute_gap_statistic`); le altre sono riferite da altre funzioni → C-023
- [X-016] | `:133-148` | `FIGURE_DPI = 150`; `_quality_guide` (`embedding_app.py:2612`), `_adp_guide` (:2518); `HINT_*`, `REPORT_TERMS` costanti in `clustering_tuning_report.py` | Verificato
- [X-017] | `:139-146` | 48 cartelle con report rigenerate il 23-10; 12+12 senza report (agosto-10 settembre); i 4 prodotti d'analisi in `08-10_s1.4-vol_m_dice_nc{2,10}`, `m_euclidean_nc2`, `09-10_s2.4-stream` | Parziale: 48 `report.md` modificati il 23-10 (tutti agglomerative); senza report 15+15 → C-032
- [X-018] | `:155` | Il design record «project-clustering-tuning-redesign» non esiste più | Verificato (memoria privata; vedi C-010)
## [STATO_BRANCH] / processo
- [B-011] | `:181` | `anatomical_maps.py` non committato, `DiscoveredFiles` importato da `embedding_app.py` | **Obsoleto**: file tracciato, HEAD pulito → C-031
- [B-012] | `:159` | `CLAUDE.md` non contiene la regola sul markdown dei notebook | **Falso**: `CLAUDE.md:63` → C-031
- [B-013] | `:165` | 5150 vs 5151 maschere a 2 mm | **Già risolto**: `datasets.md:59` spiega 704 invece di 705 per `0671` → C-031
- [B-014] | `:209` | `s1_production.md` | **Obsoleto**: il file non esiste → C-031
- [B-015] | `:214` | `viz-niivue` eliminato, recuperabile da `facef6f` | **Falso oggi**: `facef6f` non è un oggetto valido → C-031
- [B-016] | `:195` | `lessons_learned.md` #41 obsoleta | Conferma C-015; `stato_progetto.md:26` la dà ancora come aperta
- [B-017] | `:213` | Righe tutte-zero di `s1.3-vol` (0146, 0201) lasciate, filtrate a valle | **Contraddetto**: `excluded_subjects.csv` le esclude (`empty_mask`, `all`) → C-034
- [B-018] | `:3,84-90` | Decisione 23-10: `lesion_side` tutto geometrico, supera la decisione A (`:34`) | Coerente ma non propagata → C-033

---

# `.claude/lessons_learned.md` (191 righe, 46 pattern) — audit del 2026-10-26

Estratti con script tutti i riferimenti a file, simboli, commit e sezioni `debug_*.md` (riga → pattern: #N = heading `### N.`).

## [ARCHITETTURA] struttura e riferimenti
- [L-001] | `lessons_learned.md:1-6` | Un'entrata per pattern, mai duplicata; "Seen in" rimanda al `debug_*.md` per la narrazione | Parziale: 46 pattern numerati, nessun duplicato evidente; ma `debug_17_08_26.md` e `debug_22_08_26.md` non sono mai citati come "Seen in" → C-038
- [L-002] | tutte le righe "Seen in" | Ogni `debug_DD_MM_YY.md` citato esiste e ogni `§N` citato esiste | **Verificato**: tutti i file citati esistono; nessun `§N` fuori intervallo (`debug_10_09_26.md` usa `## §N —`, gli altri `## N.`)
- [L-003] | `:14,18,26,42,46,54,61-62,70,82,86,90,102,106,114,126,142,154` | I percorsi citati esistono | **Falso per 22 percorsi**: `scripts/data_summary.py`, `scripts/verify_retrieval.py`, `src/sdc/{manifest,config,runner,status}.py`, `src/retrieval/{config,dataset}.py`, `docs/dev/retrieval.md`, `config/pipelines/dim_reduction_clustering.json`, `scripts/replot_dim_reduction.py` (ora `src/pipeline/`), `src/pipeline/compute_sdc.py`, `scripts/backfill_stale_tuning_output_paths.py`, `scripts/build_dim_reduction_strategies_csv.py`, `jobs/run_compute_sdc.sh`, `assets/metadata/UCL-UK_..._participants_lesions.tsv`, `src/pipeline/enrich_lesion_metadata.py` (ora `enrich_metadata.py`), `config/pipelines/enrich_lesion_metadata.json` → C-036
- [L-004] | tutti i commit citati (`2dcd0ae`, `0b49ccc`, `1e43759`, `ea619d0`, `9fb13fb`, `b71ff7c`, `cf6e1fe`, `46c3123`…) | Esistono | **Verificato** (0 commit non validi)
- [L-005] | `:116-117` (#28) | Fonte "AUDIT_FINDINGS.md #26/#46" | Parziale: il file non esiste più alla radice; il commit `b3d1d26` lo ha spostato in `docs/debugging/` (corrisponde a `debug_22_08_26.md` §1) → C-036
## [CODICE/API] simboli e test citati
- [L-006] | #17 `:72-75` | Flag `regress_out_volume`, test `test_dim_reduction_fine_tuning_nested_n_components_and_regress_out_volume_refits_viz` | **Falso oggi**: 0 occorrenze di `regress_out` in `src/` e `tests/`; `embedding_for_viz` e un test di refit (`test_embedding_for_viz_forwards_precompute_distance_metric_to_refit`) esistono → C-037
- [L-007] | #38 `:156-159` | `_subjects_with_lesion_mask`, tre builder `build_sdc_matrix`/`build_sdc_voxelwise_matrix`/`build_sdc_streamline_matrix` con `- set(excluded_by_list)` | Parziale: la correzione c'è in tutti e tre i punti (`sdc.py:165,268`, `parcellated_csv.py:110`), ma la funzione ora è `subjects_with_lesion_mask` e il builder parcellato sta in `parcellated_csv.py` → C-036
- [L-008] | #29, #31, #33, #42, #45, #46 | `PRECOMPUTABLE_METRICS`, `euclidean_pairwise_distance`, `plot_dendrograms_grid`, `plot_eigengaps_grid`, `STANDALONE_DIAGNOSTIC_METHODS`, test gmm `n_components`, `_euclidean_dispersion_scores`, `build_step_embedding_figure` (SVG: `dendrogram_splits.py:341`), `dbcv` cast a float64 e il suo test | **Verificato**
- [L-009] | #43 | `group_of` con `fullmatch` e `[0-9]` | Verificato (`subject_ids.py`)
- [L-010] | #35 | I `runs*.csv` finiscono tutti con a-capo | **Verificato**: 42 file `runs*.csv`, 0 senza a-capo finale (la lesson ne contava 28 al momento del bug)
- [L-011] | #44 `:181-183` | Cita `debug_21_10_26.md` §18 (`sum(n)==0` in `cluster_quality`) | Verificato che il §18 esiste e che dichiara il controllo "superato" da `ea619d0`; oggi `cluster_quality.py:49` solleva con `labels.size == 0` (comportamento equivalente, riga diversa)
- [L-012] | #41 `:169-171` | "Il notebook non è ancora corretto: homogeneity e completeness sono scambiate" | **Obsoleto** (C-015); `open_problems.md:195` lo dichiara già obsoleto
- [L-013] | #20 `:84-86` | `src/retrieval/dataset.py::_SUBJECT_RE` con regex pigra e `KNOWN_SITES` | Storico verificato: il codice vive ora in `src/utils/subject_ids.py` (`KNOWN_SITES`, alternanza, `fullmatch`) → C-036
## [TEORIA/PAPER]
- [L-014] | #11, #13, #16 | Indici atlante Harvard-Oxford, `NiftiLabelsMasker` (overflow `uint8`, etichette sparite), UMAP/t-SNE non ordinati per importanza | Da verificare in Fase 2 / con la letteratura (documentazione `nilearn`, `knowledge/notes`); non ricontrollato in questo ciclo
## [ESPERIMENTI/METRICHE]
- [L-015] | #26, #27 (SLURM/`sacct`, `SLURM_ARRAY_TASK_COUNT`) | Eventi di agosto sul cluster, `TASK_COUNT=575` | Non verificabile in locale (job `run_compute_sdc.sh` ritirato; `server-pnc` ha 13 commit non integrati, vedi C-030)
- [L-016] | #12 (06-10-26) | `KNOWN_LESION_SIDES` ripristinato e `tests/unit/test_calibrate_lesion_side_threshold.py` | Verificato (costante presente in 3 file, test esiste)

---

# `.claude/history/data_changelog.md` (223 righe) e `.claude/skills/history/SKILL.md` (79 righe) — audit del 2026-10-26

## [ARCHITETTURA] struttura
- [H-001] | `SKILL.md:27-43`, `CLAUDE.md:54-60` | Tre registri (dati/metodi/impianto) + archivio sola lettura; voci più recenti in cima, formato `GG-MM-AA — titolo` | Verificato per `data_changelog.md`: 14 voci in ordine cronologico inverso, intestazione e formato coerenti. Non ancora verificato per `methods_changelog.md` e `project_changelog.md`
- [H-002] | `SKILL.md:12-25` | Cosa non archiviare (codice, run, bug, pattern, stato, esperimenti) | Coerente con `CLAUDE.md:60`; la regola "una voce, una categoria" si verifica sui due changelog successivi
## [ESPERIMENTI/METRICHE] dati — verificati sul disco
- [D-001] | `data_changelog.md:13-21` (16-10) | 5845 righe in ordine alfabetico per dataset (UCL-UK, SFB936, WAKEUP, UKLFR, NEMESIS_T0, PASPORT, PSP, WashU), poi `subject_id`; nessun `*.orig` rimasto | **Verificato** su `lesion_matrix/07-10_s1.4-vol`, `sdc_matrix/07-10_s2.4-vol` e `16-10_s2.4-vol` (ordinate per `(dataset, subject_id)`)
- [D-002] | `:25-35` (14-10) | `sdc/` → `bcbtoolkit/` in 8 dataset con 4119/56/451/705/76/83/168/195 sottocartelle; cache con 5853 chiavi `bcbtoolkit|`; `BCBTOOLKIT_DIR`, `PRESENCE_COLUMN_BY_DATA_TYPE`, `SDC_DISCONNECTOME_GLOB`, `disconnectome_glob` | **Verificato** (0 cartelle `sdc/` residue; 0 chiavi `sdc|`; i 4 simboli esistono: `BCBTOOLKIT_DIR` è in `parcellated_csv.py:60`, non in `sdc.py`)
- [D-003] | `:53-63` (28-09) | `data/derived/enrich_lesion_metadata/` rimossa | Verificato (assente)
- [D-004] | `:65-102` (23-09 NEMESIS_T0) | 76 cartelle `sub-STUNIPD0586…0666`; tsv con `participant_id_dmp`, 82 righe `sub-p*` (72+6+4), 22 `sub-c*` | **Parziale**: 76 cartelle ✓, 104 righe ✓, nessun `sub-p*` rimasto ✓; ma `:82` elenca `sub-p123`→`sub-STUNIPD0667` tra le 76 cartelle rinominate, mentre `:91` lo dà senza scansione: la cartella `0667` non esiste → C-040
- [D-005] | `:98-102,130-134` | `participants.csv` non riflette ancora i 2 dataset nuovi né il delta UKLFR/WashU; `NEMESIS_T0` non è in `populate_metadata.json` | **Falso oggi**: `participants.csv` ha tutti e 8 i dataset (WashU 195, UKLFR 705, NEMESIS_T0 76, SFB936 56); `populate_metadata.json` li elenca → C-040
- [D-006] | `:116-119` | Maschere sostituite: UCL-UK 4119, WAKEUP 451, UKLFR 697→705, PASPORT 83, PSP 168, WashU 202→195 | Verificato come stato attuale (4119/451/705/83/168/195). `sdc_download/` non esiste in locale: non verificabile
- [D-007] | `:138-158` (07-09) | `0671`: disconnettoma a 0 voxel, maschera da 56.785 voxel; `7.221.032` voxel | 7.221.032 = 182×218×182 ✓; i 56.785 non riverificabili: la maschera di oggi ha 0 voxel (X-008) e la voce 23-09 non lo registra → C-040
- [D-008] | `:162-189` (06-09) | Run `06-09_s1.3-vol` di 5720 soggetti; `0146`/`0201` con 16 e 3 voxel a 1 mm; s1.2 senza righe nulle | **Parziale**: matrice 5720×266418 ✓ ed esiste, s1.2 5269×264274 ✓; i volumi a 1 mm oggi sono 8 e 3 (`lesion_metadata.csv`): il 16 non è più riproducibile; "nessuna decisione presa" è superato da `excluded_subjects.csv` → C-034, C-040
- [D-009] | `:193-199` (05-09) | `has_features` WashU 10 → 169 ST dopo il ripristino; manifest `<nome>_archive_subjects.tsv`, `README_ARCHIVE.md` | **Parziale**: manifest e README esistono; ma `participants.csv` oggi ha `has_features` = True per 10 soggetti WashU su 195, perché l'ultima run (23-09, `overwrite: true`) ha scandito la cartella potata → C-039
- [D-010] | `:201-207` (04-09) | 6 `participants.tsv` accorpati; livello `dwi/` appiattito | Verificato: `metadata_tsv/` ha 8 tsv (6 + 2 del 23-09); nessuna cartella `dwi/`
- [D-011] | `:209-215` (03-09) | WAKEUP: 451 soggetti × 35 file, poi `lesion-map` spostato sotto `manual_masks` | Verificato: 34 file per soggetto oggi (35 − la lesione spostata)
- [D-012] | `:217-223` (01-09, 26-08) | Solo `UNIPD/WashU/features/` e `masked_fc/` restano potate (10 soggetti), archivi `.tar.gz` accanto | **Verificato** (`features_archive.tar.gz`, `masked_fc_archive.tar.gz`; nessun archivio per le `manual_masks`)
- [D-013] | `:81,195,213` | Percorsi `scripts/rename_nemesis_t0_subjects.py`, `scripts/populate_metadata.py`, `Dataset.resolve()`, `sdc/` | Storici: non esistono più (ritirati/rinominati); il file spiega `sdc/` nella voce 14-10

---

# `.claude/history/project_changelog.md` (887 righe, 81 voci) — audit PARZIALE del 2026-10-26 (righe 1-64 lette; riferimenti dell'intero file verificati con script)

## [STATO_BRANCH]
- [B-019] | working tree | A metà audit (dopo il test `pytest` e le scansioni AST) l'utente ha modificato **36 file** non committati (`src/analysis/clustering_tuning*.py`, `clustering_evaluation.py`, `dendrogram_splits.py`, `embedding_app.py`, `plotting.py`, `src/pipeline/clustering.py`, `evaluate_clustering_tuning.py`, config, 13 test, doc, `project_changelog.md` +44 righe) e ha prodotto nuovi log in `logs/clustering/` | Le cifre degli audit precedenti su `src/` (righe dei difetti in C-019…C-029, 5668 test) si riferiscono a HEAD `f577b6a` e possono slittare: ricontrollare i numeri di riga prima di agire
## [ARCHITETTURA] struttura del file
- [H-003] | tutto il file | 81 voci in ordine cronologico inverso con intestazione `GG-MM-AA — titolo` | **Parziale**: ordine corretto per 80 voci; l'ultima (riga 883) è `## 2026-08 — …` (formato diverso) → C-042
- [H-004] | tutto il file | I commit citati esistono | **Parziale**: 2 non validi: `068d2ff` (riga 742, "backup-pre-split recuperabile") e `facef6f` (riga 752, "viz-niivue recuperabile") → C-041 (e C-031)
- [H-005] | tutto il file | I percorsi citati esistono | 110 su 174 esistono; i 64 mancanti sono quasi tutti ciò che la voce stessa dichiara ritirato/spostato (`src/retrieval`, `src/sdc`, `retrieve_data.py`, `compute_sdc.py`, `analyze_clustering_tuning`, `evaluate_tuning_embeddings`, `check_lesion_quality`, `management/notes/`, `results/reports/cluster_tuning_notebooks/`…): attesi in un registro di ritiri. Da rivedere nelle voci successive solo quelli che parlano al presente (es. riga 62, riga 256, riga 344)
## [ESPERIMENTI/METRICHE] voci del 26-10-26 (righe 9-62, non ancora committate) — verificate sul disco
- [D-014] | `:9-13` | `membership_share_below_half` tolta da `tuning_results.csv`/`density_metrics.csv` delle 16 cartelle `hdbscan_soft` di tuning (6 lesione, 10 SDC); il codice non la scrive | **Verificato** (0 file con la colonna nelle 16 cartelle vive; 0 occorrenze in `src/`; le copie vecchie sono in `results/legacy/.../old_membership_share/`)
- [D-015] | `:15-25` | Dendrogramma di agglomerative = valutazione `dendrograms` del registro; eliminate `_write_agglomerative_diagnostics`, `compute_interclass_distance_matrix`, `plot_interclass_distance_matrix`; `STANDALONE_DIAGNOSTIC_METHODS = {"spectral"}` | **Verificato** (`clustering_evaluations.json:5`, `clustering_tuning_evaluations.py:62`, `clustering_tuning.py:81`; le tre funzioni non compaiono più in `src/` né in `tests/`). **Conseguenza**: `lessons_learned.md` #31 cita ancora `STANDALONE_DIAGNOSTIC_METHODS` per agglomerative e spectral
- [D-016] | `:27-37` | La metrica entra nel nome delle run di agglomerative (`mk_<metric>`) | Verificato (`...19-10_s2.4-vol_nc2_varimax_k7_link_ward_mk_euclidean`)
- [D-017] | `:39-54` | Backup in `results/legacy/clustering_prodotti_flusso_vecchio_26-10-26/` (88 MB): 749/16/28/174 file in `old_products`/`_reports`/`_labels2d`/`_stale` | **Verificato** per i conteggi; la cartella pesa 95 MB e contiene anche `old_interclass` (28) e `old_membership_share` (32), cioè le due voci precedenti dello stesso giorno: la tabella non li elenca → C-042
- [D-018] | `:56-62` | `all_candidates.csv` e `comparison/` spostati in `results/legacy/cluster_tuning_notebooks_flusso_vecchio_26-10-26/` | Verificato (10 file); la voce dichiara anche che la cartella `…pre-split_18-10-26` non esiste più (verificato)

---

# `docs/setup.md` (36 righe) — audit del 2026-10-26 (ciclo 9)

Stato del repo a inizio ciclo: HEAD `d0ff0b2` ("logs"), 6 file modificati e non committati (`.claude/open_problems.md`, `docs/experiments/{pipelines,s1.4-vol,s2.4-stream}.md`, più `.claude/audit/`). I 36 file del ciclo 8 sono stati committati (`57ef5e9`, `d0ff0b2`): i numeri di riga di C-019…C-029 si riferiscono a `f577b6a` e vanno ricontrollati prima di agire.

## [CONFIG/PARAMETRI]
- [P-005] | `setup.md:5` | `environment.yml` alla radice definisce l'ambiente `nemesis` | Verificato (`name: nemesis`, file in radice)
- [P-006] | `setup.md:7` | "Pacchetti principali": numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn | **Parziale**: tutti e 11 sono in `environment.yml` (nilearn/nibabel nella sezione `pip:`), ma la lista omette `hdbscan, plotly, openpyxl, pytest, pytest-cov, hypothesis, factor_analyzer, pacmap` e **`dash`** (installato in `nemesis` da conda-forge fuori dal file) → C-002 (già aperto)
- [P-007] | `setup.md:12` | `conda env create -f environment.yml` crea l'ambiente | Verificato con `--dry-run -n nemesis_audit_dryrun`: il solver risolve (python 3.11.14, 220 righe di piano); il piano **non contiene `dash`** né `flask` → C-043
- [P-008] | `setup.md:18` | `conda activate nemesis` | Verificato (ambiente in `/opt/anaconda3/envs/nemesis`)
- [P-009] | `setup.md:23` | `dependencies` = pacchetti conda-forge, `pip:` = solo PyPI | **Parziale**: `pip:` contiene `nibabel`, `nilearn`, `factor_analyzer`, `pacmap`, tutti disponibili anche su conda-forge; l'esempio contraddice la regola. Inoltre `hdbscan` è in `dependencies` ma nell'ambiente locale risulta installato da PyPI (`pypi_0`) → C-044
- [P-010] | `setup.md:26` | `conda env update -f environment.yml -n nemesis --prune` aggiorna l'ambiente | Sintassi verificata (`conda env update --help`: `-f`, `-n`, `--prune`). **Effetto pericoloso**: `--prune` toglie i pacchetti non elencati nel file; `dash 4.4.1` è un pacchetto conda-forge fuori da `environment.yml` (`conda list`) → verrebbe rimosso e l'Embedding Explorer smetterebbe di partire. Non eseguito (modificherebbe l'ambiente) → C-043
- [P-011] | `setup.md:31` | ADP richiede `dadapy`, che dipende da `jax` e non è in `environment.yml`; vive in `nemesis_fallback` con `dadapy` 0.3.4 | **Verificato**: `nemesis_fallback` esiste; `dadapy 0.3.4`, `jax 0.4.30`, python 3.11.8, numpy 1.26.4, scikit-learn 1.9.1 (coincide con `guides/clustering.md:158`); `nemesis` non ha né `dadapy` né `jax`
- [P-012] | `setup.md:31` | `"adp"` è un valore di `clustering_methods`; sezione "ADP" in `guides/clustering.md` | Verificato (`clustering.md:150` "## ADP (DADApy)", `:231` elenca `"adp"`); import lazy in `src/analysis/adp.py:49-54` che solleva con un messaggio che indica l'ambiente separato
- [P-013] | `setup.md:31` | `nemesis_fallback` non ha `dash`, quindi `embedding_app` e i suoi test non vi girano | Verificato: `dash` assente (`ModuleNotFoundError`); `embedding_app.py:61` importa `dash` al livello di modulo. Nota: anche `hdbscan` è assente da `nemesis_fallback`, quindi solo ADP vi gira. Non ho lanciato `pytest` in quell'ambiente
- [P-014] | `setup.md:31` | "tutto il resto del progetto resta in `nemesis`" | Verificato per costruzione: i test che usano `dadapy` hanno `skipif(find_spec("dadapy") is None)` (`tests/unit/test_adp.py:19`, `tests/integration/test_clustering_pipeline.py:2151`), quindi in `nemesis` si saltano; nessun config ADP nel repo (`clustering.md:158`)
- [P-015] | `setup.md:31` | "oggi `nemesis_fallback`" | **Parziale**: il nome è vero oggi, ma `nemesis_fallback` non ha una ricetta nel repo (nessun `environment_*.yml`, nessuna riga che dica come crearlo) e il nome "fallback" compare solo qui e in `clustering.md` → C-046
## [ARCHITETTURA]
- [A-056] | `setup.md:35` | `src/` = "codice di progetto (pipeline SDC, embedding, clustering, ecc.)" | Verificato nella sostanza (`build_sdc_matrix`, `compute_sdc_metadata`, `dim_reduction`, `clustering`); la descrizione non cita lesioni, FC, metadati
- [A-057] | `setup.md:36` | `scripts/` = "script accessori/one-off (es. download e organizzazione dataset, utility di setup)" | **Falso negli esempi**: `scripts/` ha solo `archive_local_raw_data.py` (comprime i dati locali) e `build_dataset_summary_table.py` (tabella riassuntiva); nessun download, nessuna utility di setup. `README.md:35` e `CLAUDE.md:48` danno una descrizione diversa ("cache maintenance, tables, derived indices") → C-045
- [A-058] | `setup.md` (intero) | Il file è richiamato da `CLAUDE.md:17,40` e `README.md:24,41,118` | Verificato; `README.md:118` ripete la stessa lista di pacchetti di `setup.md:7` (terza copia, con `CLAUDE.md:11`)
- [A-059] | `setup.md` (intero) | Il testo parla al presente (`CLAUDE.md:53`) | Verificato salvo l'avverbio "oggi" (`:31`), che lega il nome dell'ambiente a un istante → C-046

---

# `docs/guides/` — ciclo 10 (2026-10-26): `evaluate_dim_reduction_tuning.md` (43), `fc_matrix_building.md` (57), `understanding_umap_report.md` (59)

Prefisso nuovo `G-` per le guide. Le prove sono state eseguite su **copie in scratchpad** (`.../scratchpad/edt`, `.../scratchpad/uu`), mai su `results/` o `data/` del repo. HEAD `d0ff0b2`.

## `evaluate_dim_reduction_tuning.md`
- [G-001] | `:5-6,13-16` | Script e config esistono; comando locale `python -m src.pipeline.evaluate_dim_reduction_tuning --config config/pipelines/evaluate_dim_reduction_tuning.json` | Verificato (`--help`: solo `--config`; config presente con `tuning_dir`, `overwrite`, `tuning_evaluations`). Eseguito su copia: rc=0, 12 file scritti, 34 s
- [G-002] | `:18-21` | `sbatch jobs/run_evaluate_dim_reduction_tuning.sh` | Verificato: stessa invocazione e stesso config; percorsi `/home/etosato/...` hardcoded (C-013)
- [G-003] | `:27` | Serve `embeddings.npz` + `config.md`; il numero di embedding deve coincidere con la griglia, altrimenti stop | Verificato (`load_tuning_run`: `tuning_embeddings.py:115-150`, `ValueError` sul confronto tra chiavi attese e presenti; `FileNotFoundError` se manca l'npz, provato: rc=1 con messaggio chiaro)
- [G-004] | `:29` | Embedding con >2 componenti: serve la gemella con `n_components=2`, mai una fetta; lo script si ferma prima di calcolare | Verificato (`_check_plot_hdbscan_feasible`, `visualization_key`, `tuning_evaluations.py:87-135`)
- [G-005] | `:29,37` | `trustworthiness` e `cumulative_explained_variance` sono rifiutati | Verificato (provato: `ERROR: config: tuning_evaluations['trustworthiness'] is a sweep_score and cannot be run here`). `plot_hdbscan` richiede esattamente `min_cluster_size` (>=2) e `min_samples` (>=1) interi: provato con `min_samples` mancante → errore chiaro
- [G-006] | `:35` | `tuning_dir` deve esistere; il metodo si legge da `config.md`; il titolo ne deriva la modalità | Verificato (`load_tuning_run` legge `reduction_method` da `config.md`; `_modality_title` usa il primo segmento dopo `results`). Provato: cartella inesistente → errore sul file `embeddings.npz` mancante, non sulla cartella
- [G-007] | `:36` | `overwrite: false` → lo script si ferma se i file esistono già | **Parziale**: si ferma, ma il controllo è per foglia, dentro il ciclo (`tuning_evaluations.py:155-158`): con la prima foglia libera e una successiva occupata la prima viene scritta e poi rc=1. Riprodotto sulla copia → C-047
- [G-008] | `:41` | Output `hdbscan_grid_mcs<N>_ms<M>.png` e `hdbscan_results_mcs<N>_ms<M>.csv` in ogni foglia dei `nested_params` | Verificato (`:155`; sulla copia: 6 foglie = 2 metriche × `n_components` {2,3,10}, 12 file scritti = 6 × 2)
- [G-009] | `:41` | "Con le stesse impostazioni il risultato è identico a quello calcolato durante lo sweep" | Verificato per i CSV: `cmp` byte per byte tra i CSV preesistenti di `metric=dice/n_components=2` e `=3` e quelli ricalcolati con `overwrite: true` → identici. Non verificato per i PNG
- [G-010] | `:41-43` | Rilanciare con altre impostazioni aggiunge file; `config.md` non viene modificato; ogni lancio scrive un log in `logs/evaluate_dim_reduction_tuning/` | Verificato nel codice (tag nel nome; nessuna scrittura su `config.md`; `LOGS_ROOT`). Provato: il log viene creato nella cartella relativa al cwd. `logs/evaluate_dim_reduction_tuning/` non esiste nel repo (mai lanciato qui; esiste `logs/evaluate_tuning_embeddings/`, nome precedente)
- [G-011] | `:37` | "Stessa sintassi del blocco omonimo di `dim_reduction.json` (vedi `dim_reduction.md`)" | Verificato (`dim_reduction.md:41-47` ha la tabella delle tre valutazioni; `dim_reduction.json:18-20`)
- [G-012] | `:3` | "oggi `plot_hdbscan`": è l'unica valutazione sugli embedding | Verificato (`EVALUATIONS`: due `KIND_SWEEP_SCORE` + `plot_hdbscan`); avverbio temporale → C-052

## `fc_matrix_building.md`
- [G-013] | `:3` | Le FC sono disponibili attualmente per la sola coorte WashU | Verificato: `mask_fc.json` ha `dataset: UNIPD/WashU`; `README.md:74` ("the WashU functional-connectivity CSVs"); `participants.csv`: WashU 195 ST. Avverbio → C-052
- [G-014] | `:5-6` | Script e config `mask_fc`/`build_fc_matrix` esistono | Verificato (`--help` di entrambi: solo `--config`)
- [G-015] | `:14-15` | `mask_fc` segna NaN le zone danneggiate; `build_fc_matrix` scarta la parte ridondante e impila | Verificato (`functional.py:163-175` NaN su righe e colonne dei nodi compromessi, per nome; la matrice di `Yan100TianS1` è 169 × 7503 = 123·122/2: `_dseg.tsv` ha 123 nodi (124 righe con l'intestazione), cioè il triangolo senza diagonale)
- [G-016] | `:23-36` | `sbatch jobs/run_mask_fc.sh`, poi `sbatch jobs/run_build_fc_matrix.sh` | Verificato: i due job esistono e invocano `python -m src.pipeline.mask_fc|build_fc_matrix --config ...`
- [G-017] | `:27` | Fase 1 scrive `masked_fc.csv` per paziente in `data/derived/features/masked_fc/...` e `mask_summary.csv` | Verificato: `masked_fc/<combo>/<subject>_masked_fc.csv` + `mask_summary.csv` (colonne `subject_id,dataset,n_compromised_nodes`); 12 cartelle di combo
- [G-018] | `:34` | Fase 2: `matrix.npy`, `metadata.csv`, `manifest.json` in `data/derived/features/fc_matrix/...` | Verificato (`fc_matrix/<combo>/27-07_s3.1-<combo>/` contiene anche `edge_names.npy` e `config.md`; manifest: 169 × 7503, float64)
- [G-019] | `:36` | In locale le due pipeline girano in sequenza con `python -m src.pipeline...` | **Parziale**: il comando non è esatto (manca `--config <file>`); CLAUDE.md chiede l'invocazione precisa → C-053
- [G-020] | `:43-48` | `group_filter` in `mask_fc.json` **e** `build_fc_matrix.json` | **Falso per `build_fc_matrix.json`**: la chiave non esiste né nel config né nel codice (`grep group_filter` in `build_fc_matrix.py`/`model_config.py`: nessun hit); il filtro vive in `mask_fc` → C-049
- [G-021] | `:47` | `["ST"]`: solo pazienti (i sani sono saltati di proposito) | Verificato (`discover_subject_files`: l'esclusione per gruppo precede l'intersezione; i sani sono in `excluded_by_group`, loggati a INFO)
- [G-022] | `:48` | `["ST","HC"]`: i sani vengono aggiunti con 0 nodi compromessi | **Falso**: un soggetto con FC ma senza maschera di lesione è in `missing_lesion` e viene **saltato** con WARNING (`functional.py:254-266`, `mask_fc.py:121-127`); `discover_subject_files` e `docs/dev/fc_matrix.md:38` dicono che i sani WashU non hanno mai maschera. Non ho potuto lanciare il caso (le FC degli HC sono nell'archivio `features_archive.tar.gz`, non in locale) → C-048
- [G-023] | `:54` | I NaN restano NaN; nessuna imputazione in questa pipeline | Verificato (`functional.py:439`: "imputation is a separate, later step"; 0 occorrenze di "imput" in `src/`)
- [G-024] | `:54` | "L'imputazione avverrà in un passaggio separato appena prima della Dim Reduction" | **Non verificabile / contraddetto**: nessun codice; `README.md:74` dice "NaN-imputation remains deliberately open" → C-050
- [G-025] | `:55` | Connessioni costanti per tutti i pazienti rimosse e loggate | Verificato (`drop_constant_edges`, `functional.py:395-440`: valutate solo se completamente osservate; `build_fc_matrix.py:90-99` logga). Manifest: la riga "constant edges dropped" in `config.md`
- [G-026] | `:56` | Nessuna soglia di esclusione paziente; `mask_summary.csv` conta i nodi; `notebooks/exploration/fc_analysis.ipynb`; nota `fc_lesion_masking.md` sezione "Scegliere una soglia di esclusione paziente" | Verificato (notebook e sezione esistono: `fc_lesion_masking.md:106`; `README.md:74` "no threshold, no subject excluded"; `docs/dev/fc_matrix.md:38`)
- [G-027] | `:57` | In locale 10 soggetti campione, comuni a tutte e 12 le combinazioni; resto in `masked_fc_archive.tar.gz`; `README_ARCHIVE.md` | Verificato: 12 cartelle con gli stessi 10 file (hash degli elenchi identico); `README_ARCHIVE.md` dice 169 totali, 159 in archivio. `datasets.md:174` riporta la stessa riga (169/10/159). L'archivio `.tar.gz` non è in locale: non riverificato
- [G-028] | `:12-17` | Il `mask_summary.csv` serve a ispezionare i nodi distrutti prima di costruire la matrice | Verificato (esiste per combo)

## `understanding_umap_report.md`
- [G-029] | `:5-7` | Script `src/pipeline/generate_understanding_umap_report.py` e logica `src/analysis/understanding_umap_report.py` | Verificato (esistono; `--help`: `--umap-tuning-dir`, `--tsne-tuning-dir`, nessun `--config`; non esiste un config JSON)
- [G-030] | `:13-16` | Servono `embeddings.npz` + `metadata.csv`; stessa coorte nello stesso ordine verificata riga per riga (`real_metadata.equals(tsne_metadata)`); UMAP `nested_params: [metric, n_components]` con 2 e 3; t-SNE `[metric]` | Verificato: `load_tuning_data` (`understanding_umap_report.py:1131-1171`) e `config.md` dei due tuning di esempio (`13-08_s1.1-vol`: UMAP `n_components=2,3`; tsne solo `metric=*`); 1150 soggetti in entrambi
- [G-031] | `:14` | `embeddings.npz` esiste solo con `save_tuning_embeddings: true`; se manca lo script fallisce con errore chiaro e non rifà il fit | Verificato (`_load_embeddings_npz`: `ValueError` "file is missing, empty, or corrupt")
- [G-032] | `:22-25` | `sbatch jobs/run_generate_understanding_umap_report.sh` | Verificato come file; le due cartelle sono variabili **dentro lo script** (`UMAP_TUNING_DIR=...13-08_s1.1-vol`, righe 14-15): per un altro tuning bisogna modificare il job → C-053
- [G-033] | `:30-32` | `PYTHONPATH=. python -m src.pipeline.generate_understanding_umap_report --umap-tuning-dir ... --tsne-tuning-dir ...` | Verificato: gira (rc=0, 3,6 s su copia). `PYTHONPATH=.` è ridondante con `-m` dalla radice (provato: `--help` senza `PYTHONPATH` funziona) → A-006, C-053
- [G-034] | `:39` | Un file `understanding_umap_<metric>.html` per ogni metrica della directory UMAP (`dice`, `euclidean`) scritto nella directory UMAP | Verificato (rigenerati i due file nella copia: 9,6 MB ciascuno; `output_dir=umap_tuning_dir`)
- [G-035] | `:41-51` | Cinque figure in due sezioni (griglia, slider, 2D vs 3D, UMAP vs t-SNE statica, UMAP vs t-SNE slider) | Verificato: l'HTML rigenerato contiene "Figure 1:"…"Figure 5:"; mappatura nel docstring del modulo (`:8-13`)
- [G-036] | `:44` | Griglia colorabile per `dataset`/`side`/`volume`/`nihss` | **Parziale/Falso per i run attuali**: i modi sono filtrati sulle colonne presenti in `metadata.csv` (`understanding_umap_report.py:996`); `dim_reduction.py:12-14` scrive solo `dataset` e (se c'è) `lesion_volume_voxels`, "`lesion_side`/`nihss` are NOT in metadata at all". Nel tuning di esempio `metadata.csv` = `subject_id,dataset`: il report offre solo `none` e `dataset` → C-051
- [G-037] | `:46` | Il 3D è un fit separato (`n_components=3`) | Verificato (le leaf `n_components=3` sono fit reali; `build_2d_vs_3d_section` legge le due leaf)
- [G-038] | `:50` | Un valore sweepato da un solo metodo lascia la cella dell'altro vuota, dichiarato in didascalia | Verificato nel codice (`missing_tsne` in `build_method_comparison_grid_figure`, `:493-495`); non ho letto la didascalia renderizzata
- [G-039] | `:58` | Palette importata da `plotting.py` (`_CATEGORICAL_PALETTE`, `_NOISE_COLOR`) | Verificato (`understanding_umap_report.py:57`)
- [G-040] | `:59` | `_CELL_PX=165`, canvas slider `440px`, calibrati su 1150 soggetti | Verificato (`:92,96`; commenti `:85-96`)
- [G-041] | `:16` | "se un giorno esisterà un run t-SNE con `n_components=3`... oggi assente" | Verificato che oggi la t-SNE è solo 2D (config); frase condizionale/futura → C-052

---

# `docs/guides/` — ciclo 11 (2026-10-27): `sdc_matrix_building.md` (117), `dim_reduction.md` (134), `evaluate_clustering_tuning.md` (121)

Nota: `.claude/CLAUDE.md` ha guadagnato la riga 49 (`utils/` = testi letti come dati, `utils/report_texts/clustering_tuning.md`, letto da `clustering_tuning_report.py` via `src/utils/text_registry.py`): i riferimenti `CLAUDE.md:NN` dei cicli precedenti per NN ≥ 49 sono slittati di +1 (es. la regola "presente" è ora `:54`, i notebook `:64`). Verificato: `utils/report_texts/clustering_tuning.md` e `src/utils/text_registry.py` esistono (non committati).

## `sdc_matrix_building.md`
- [G-042] | `:9-10,17-25` | Script, config, job; comando locale `python -m src.pipeline.build_sdc_matrix --config ...` | Verificato (`--help`: solo `--config`; job invoca lo stesso comando)
- [G-043] | `:3-7,29-40` | Tre `representation`: `parcellated`, `voxelwise`, `streamline` | Verificato (`KNOWN_REPRESENTATIONS`, `sdc.py:73`)
- [G-044] | `:5,33` | I CSV parcellati omettono le regioni a disconnessione nulla e le righe non sono in ordine stabile | **Verificato sui dati**: 200 soggetti WashU, `schaefer_200_tian_s2`: 43 conteggi di righe diversi (232 in 81 casi, minimo 29), 195 ordini distinti su 200
- [G-045] | `:7,38,40,85,87` | Il CSV streamline ha 87 tratti per soggetto, colonne `tract,streamline_ratio`, per tutti i 5853 soggetti | **Verificato**: 5853 file, tutti con 87 righe e intestazione `tract,streamline_ratio`; ogni soggetto ha 15 `LF-disconnectome` + 16 `LF-lesion` CSV (verificato per nome su tutti e 5853, 0 anomalie) → conferma `:50`. Le righe non sono nell'ordine del file di riferimento (5853/5853 con ordine diverso), coerente con l'allineamento per nome
- [G-046] | `:42-44` | Ammissione: `has_lesion` in `participants.csv`, file SDC presente, non in `excluded_subjects.csv` (`excluded_subjects_path` obbligatorio) | Verificato (`build_config.py:343-367,~495`: campo `_require_str`; docstring: nessun `lesion_glob`)
- [G-047] | `:65` | 8 dataset elencati | Verificato (`build_sdc_matrix.json:4-13`; i nomi coincidono con le cartelle)
- [G-048] | `:61-71` | Tabella parametri "comuni" | **Parziale**: `output_root` è dato come "default" ma è obbligatorio (`_require_str`); `excluded_subjects_path` (obbligatorio) e `run_notes` (opzionale) mancano dalla tabella; il titolo dice "entrambe le modalità" ma sono tre → C-054
- [G-049] | `:78` | `value_column`: 6 valori ("mean_overlap (default consigliato)") | Valori verificati (`KNOWN_VALUE_COLUMNS`, `parcellated_csv.py:54`); non c'è un default: il campo è obbligatorio per `parcellated` → C-054
- [G-050] | `:67,94-95` | `object` vincolato dalla `representation`; `correct_out_of_brain`/`brain_mask_path` rifiutati fuori da `voxelwise`; `brain_mask_path` obbligatorio con `correct_out_of_brain: true` | Verificato (`build_config.py:~395-440`)
- [G-051] | `:96` | `resample_interpolation` ∈ {linear, nearest, continuous}; si usa `nearest` | Verificato (`_KNOWN_INTERPOLATIONS`; config corrente `nearest`). Equivalenza `nearest`/`linear` e rumore ~1e-17 di `continuous`: non rieseguiti (rimando a `dev/sdc_matrix.md`, `template_and_grids.md` §9 che esiste: `:101`)
- [G-052] | `:100` | 64110 colonne su 291345 fuori dal cervello a 2 mm su 5845 soggetti; con il flag acceso la somma di ogni riga = `disconnection_load_voxels_2mm` | **Verificato**: `07-10_s2.4-vol` = 5845×291345, `16-10_s2.4-vol` = 5845×227235 (291345−227235 = 64110); 12 righe campione di `16-10_s2.4-vol` hanno somma uguale a `sdc_metadata.csv` (differenze ≤ 4e-12). Le statistiche di massa (mediana 0,80%, p99 6,7%, max 15,3%) non ricalcolate (richiedono le 5845 mappe a 1 mm); la mediana e il massimo coincidono con `run_notes` del config
- [G-053] | `:102` | `config.md` elenca `n_voxels_corrected` e `mass_removed` per soggetto; mappa non finita o negativa ferma la run | Verificato (`16-10_s2.4-vol/config.md:69-74`; `sdc.py:453`)
- [G-054] | `:105` | Atlanti: `schaefer_{200,300,400}_tian_s2` con 232/332/432 regioni; `buckner_7n` escluso (una riga per soggetto) | Verificato (file di riferimento 233/333/433 righe con intestazione; il CSV `buckner_7n` ha una sola riga di dati); sezione "Adding a new atlas" esiste in `dev/sdc_matrix.md:48`
- [G-055] | `:111-116` | Output in `data/derived/sdc_matrix/<GG-MM>_<session>/`: `matrix.npy`, `metadata.csv`, `region_names.npy` (parcellated), `tract_names.npy` (streamline), `non_constant_mask.npy` (voxelwise), `manifest.json`, `config.md` | Verificato sulle 6 cartelle esistenti (una e una sola delle tre ausiliarie per run)
- [G-056] | `:7` | "Nonostante la famiglia `LF-lesion` è una misura di disconnessione, quindi appartiene alla track `s2.x`" | Frase non grammaticale e circolare; la track `s2.x` è definita in `docs/experiments/README.md:11-16` (s2.3-stream, s2.4-stream = streamline) → C-054

## `dim_reduction.md`
- [G-057] | `:5-6,13-23` | Script, config, job; comando locale | Verificato (`--help`: solo `--config`); `dim_reduction.json` ha i campi del loader
- [G-058] | `:62-76` | Campi di `dim_reduction.json` | Verificato contro `load_dim_reduction_config` (`model_config.py:~85-105`): `reduction_method`, `params_file`, `fine_tuning`, `color_by`, `viz_n_components`, `save_tuning_embeddings`, `precompute_distance_metric`, `tuning_evaluations`, `session_name`, `output_root`, `input_path`, `overwrite`, `project`; `run_notes` opzionale non è in tabella
- [G-059] | `:66` | Metodi `umap, tsne, pca, pacmap`; t-SNE: tuning salvati con init casuale e lr 200, nuovo tuning con MDS classico e `"auto"` | Verificato in parte: `params_reduction.json` ha le 4 voci; `learning_rate: "auto"` e init MDS (`tuning.py:113`, `reduction.py:36`). I tuning "salvati con init casuale e lr 200" non riverificati
- [G-060] | `:41-53` | Tabella `tuning_evaluations`; punteggio dello sweep obbligatorio; gemello 2D | Verificato (cfr. G-004/G-005, `dim_reduction.json:18-20`)
- [G-061] | `:72` | `viz_n_components: 3` "fornisce solo l'HTML interattivo ruotabile" | **Falso**: con 3 colonne `write_embedding_plots` non scrive nessun PNG (`embedding_plots.py:42,56`) e nessun HTML per-run esiste; contraddice `:39` e `:120` della stessa guida → C-056
- [G-062] | `:76` | Sopra 4096 soggetti `umap-learn` passa dall'esatto all'approssimato | **Verificato** (`umap/umap_.py:2045,2550,2745`: `shape[0] < 4096`)
- [G-063] | `:82-97` | PCA: `solver` blocks/sklearn, `standardize`, `dual`, `rotation` (6 valori), `rotation_max_iter`, `rotation_n_components`, `n_components`/`variance_share`, `chunk_columns` 16384, `max_matrix_gib` 8; un `null` rifiutato | Verificato in parte (`covariance_pca.py:35` `DEFAULT_CHUNK_COLUMNS = 16384`, `pca_method.py:20` "never null", `_BLOCKS_ONLY`). `DEFAULT_MAX_MATRIX_GIB = 8` e l'elenco delle rotazioni non riletti riga per riga
- [G-064] | `:97` | `dual: false` su disconnettoma voxelwise = ~413 GB | **Verificato** per calcolo: 227235² × 8 byte = 413 GB; 5,3 GB = 5845×227235×4 byte
- [G-065] | `:99-104` | Tabella sessioni: `s1.4-vol` 5845×221.955; `s2.4-vol` 5845×227.235; `s2.1` 1119×232; `s2.4-stream` 5831×87 | **Verificato** sulle matrici (`07-10_s1.4-vol` 5845×221955; `16-10_s2.4-vol` 5845×227235; `27-08_s2.1-...` 1119×232; `07-10_s2.4-stream` 5831×87)
- [G-066] | `:114,131-133` | Rami `production/<metodo>/<Data>_<session>_<tag>` e `tuning/<metodo>/<Data>_<session>`; `runs.csv`/`runs_tuning.csv` | Verificato (es. `16-10_s2.4-vol_nc42`, `runs.csv`, `runs_tuning.csv`)
- [G-067] | `:118,128` | `metadata.csv` di produzione e di tuning "arricchita in automatico di `lesion_volume_voxels`, `lesion_side`, `nihss`" | **Falso**: `dim_reduction.py:9-16` passa i metadati dell'input così come sono; `lesion_side`/`nihss` non ci sono mai. Sui 40 `metadata.csv` di produzione: 33 hanno `subject_id,dataset`, 7 aggiungono `lesion_volume_voxels` (se l'input la ha). Nei tuning: `subject_id,dataset` (3) o + `lesion_volume_voxels` (1) → C-055
- [G-068] | `:119,124` | `eigenvalues.npy` (produzione pca), `eigenvalues.npz` (tuning pca) | Verificato (presenti in `production/pca/*` e `tuning/pca/16-10_s2.4-vol`)
- [G-069] | `:120` | Plot: `embedding_plot_unico.png` + uno per `color_by`; niente HTML per-run | Verificato (`embedding_plot_{unico,dataset,nihss,side}.png` in `production/pca/16-10_s2.4-vol_nc42`). Nella stessa cartella c'è `pca_covariates.png`, non scritto da alcun codice: l'ha spostato a mano la voce del 19-10-26 di `project_changelog.md` (2 file) — non è un difetto
- [G-070] | `:108` | PCA: il plot usa le prime `viz_n_components` componenti se `rotation: none` | Verificato (`reduction.py:203-204`, `_columns_ordered_by_variance`)
- [G-071] | `:41,66,74,76,127,128` | Avverbi/passato/futuro ("oggi disponibili", "correnti", "nessuna run precedente all'introduzione", "prima dell'introduzione", "futuro plot interattivo", "un plot futuro") | Trovati → C-052

## `evaluate_clustering_tuning.md`
- [G-072] | `:25-26,32-41` | Script, config, job; comando locale | Verificato (`--help`: solo `--config`; job stessa invocazione)
- [G-073] | `:51-57` | Campi `tuning_dir`, `overwrite`, `evaluations_file`, `tuning_evaluations`, `write_report` | Verificato (`load_evaluate_clustering_tuning_config`, `model_config.py:124-137`; config corrente presente con tutti e 5)
- [G-074] | `:20,55-56` | Nomi delle valutazioni e impostazioni nel registro (`dendrogram_jump.k_range`, `dendrograms.truncate_last_p`) | Verificato (`clustering_evaluations.json`: 11 voci; `k_range` 2-30, `truncate_last_p` 30)
- [G-075] | `:22` | Figure a 200 dpi (`FIGURE_DPI`); testi del report in `utils/report_texts/clustering_tuning.md`, il codice si ferma se i testi non coincidono | **Verificato**: `FIGURE_DPI = 200` (`clustering_tuning_evaluations.py:76`); `text_registry.py` solleva su chiave mancante/ripetuta/sconosciuta. (`open_problems.md`/X-016 citava 150: valore superato)
- [G-076] | `:23,74` | `kmeans`, `gmm`, `spectral`, `adp` rifiutati (`unsupported clustering_method`) | Verificato il messaggio (`clustering_tuning_analysis.py:106`); non eseguito su un tuning di quei metodi
- [G-077] | `:61` | `internal_metrics` gira solo con `overwrite: true` | **Verificato**: con `overwrite: false` → `FileExistsError: internal_metrics rewrites tuning_results.csv: set overwrite=true to allow it`
- [G-078] | `:78-92` | File di output delle valutazioni e loro nomi | **Verificato eseguendo** su copia di `08-10_s1.4-vol_m_dice_nc2` (rc=0, 39 s, 12 file): `cophenetic_correlation.csv`, `dendrogram_jump.csv`, `linkage_agreement.csv`, `largest_cluster_share.csv`, `dunn_index.csv`, `dendrogram_metric=<metric>.png` ×3, `k_curves_metric=<metric>.png` ×3, `report.md`; tutti i CSV identici byte per byte a quelli salvati
- [G-079] | `:89` | Struttura di `report.md` | Verificato in parte (sezioni per metrica, "Come leggerlo"); il `report.md` salvato (23-10) differisce in 36 righe da quello rigenerato dal codice di oggi: prima "Dendrogramma (ultime 30 fusioni)", ora "Dendrogramma" e testo senza il 30 → C-057. La guida (`:84`: "il numero sta sull'asse orizzontale") coincide col codice attuale
- [G-080] | `:94` | Ogni lancio scrive un log in `logs/evaluate_clustering_tuning/` | Verificato (77 log nel repo; il lancio su copia ne ha creato uno nel cwd)
- [G-081] | `:104-135` | Notebook `dendrogram_embedding_explorer`: parametri `RUN_DIR`, `LINKAGE`, `METRIC`, `K_MIN`, `K_MAX`, `LAST_P`, `MAP_MODALITY`, `MAP_THRESHOLD_FRACTION`, `CACHE_DIR`; `LAST_P` ≥ `K_MAX` e al massimo 20; `ward` solo euclidea; `MAP_THRESHOLD_FRACTION` in [0,1); `MAP_MODALITY` ∈ {None, lesion, sdc}; cache `results/cache/binary_masks` | **Verificato** nella cella dei parametri (`2 <= K_MIN <= K_MAX <= LAST_P`, `MAX_LEAVES` in `dendrogram_splits.py:45`, default `results/cache`+`binary_masks` in `src/pipeline/embedding_app.py:67`). Il calcolo delle mappe (soglia 0,5 sul disconnettoma) non rieseguito → audit di `dev/anatomical_maps.md`
- [G-082] | `:23,3` | "Si riprendono dopo aver chiuso i tre metodi sopra" | Piano futuro nel testo → C-052
