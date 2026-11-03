# 02 — Contraddizioni e problemi aperti (richiedono una decisione dell'utente)

Severità: **Alta** (la doc induce a un errore operativo) · **Media** (affermazione falsa/obsoleta con effetto pratico) · **Bassa** (imprecisione, omissione, stile).
Ogni voce è chiusa: la sua riga «Stato» dice cosa è stato fatto (le prime il 29-10-26, nella revisione delle Medie; l'ultima, C-022, il 02-11-26).

Aperti: 0 (114 voci registrate, tutte chiuse: C-001, C-002, C-003, C-004, C-005, C-006, C-007, C-008, C-009, C-010, C-011, C-012, C-013, C-014, C-015, C-016, C-017, C-018, C-019, C-020, C-021, C-022, C-023, C-024, C-025, C-026, C-027, C-028, C-029, C-030, C-031, C-032, C-033, C-034, C-035, C-036, C-037, C-038, C-039, C-040, C-041, C-042, C-043, C-044, C-045, C-046, C-047, C-048, C-049, C-050, C-051, C-052, C-053, C-054, C-055, C-056, C-057, C-058, C-059, C-060, C-061, C-062, C-063, C-064, C-065, C-066, C-067, C-068, C-069, C-070, C-071, C-072, C-073, C-074, C-075, C-076, C-077, C-078, C-079, C-080, C-081, C-082, C-083, C-084, C-085, C-086, C-087, C-088, C-089, C-090, C-091, C-092, C-093, C-094, C-095, C-096, C-097, C-098, C-099, C-100, C-101, C-102, C-103, C-104, C-105, C-106, C-107, C-108, C-109, C-110, C-111, C-112, C-113, C-114)

---

## C-001 — Media — Doc vs Doc: dove vivono le note delle riunioni
- **Dove**: `.claude/CLAUDE.md:33` ("raw meeting notes, which live under `assets/`") vs `CLAUDE.md:41`, `README.md:50`.
- **Prova**: `ls assets` → `atlases metadata templates`; `ls management/meetings` → `01_Kick-off.md`, `02_Seba.md`, ...
- **Impatto**: un agente cerca le riunioni nel posto sbagliato.
- **Domanda**: correggo `CLAUDE.md:33` in "`management/meetings/`"?
- **Stato (29-10-26): CHIUSA** — `.claude/CLAUDE.md` rimanda a `management/meetings/`.

## C-002 — Media — Doc vs Config: `environment.yml` incompleto e lista dei pacchetti incompleta
- **Dove**: `CLAUDE.md:11`; `environment.yml`; `src/analysis/embedding_app.py` (`from dash import ...`); `docs/setup.md:31`.
- **Prova**: `environment.yml` non elenca `dash`; l'ambiente locale `nemesis` ha `dash 4.4.1` (installato fuori dal file). `docs/setup.md:31` dà per scontato che `dash` stia in `nemesis`. La lista di `CLAUDE.md:11` omette `hdbscan, plotly, openpyxl, pytest, pytest-cov, hypothesis, factor_analyzer, pacmap` e `python=3.11`.
- **Impatto**: un ambiente ricreato da `environment.yml` non fa partire l'Embedding Explorer; la lista in `CLAUDE.md` è una seconda fonte che diverge (`code_standards.md` §5: un valore, un posto).
- **Domande**: (a) aggiungo `dash` (con quale versione: `4.4.1`?) a `environment.yml`? (b) in `CLAUDE.md:11` sostituisco la lista con "vedi `environment.yml`"?
- **Stato (ciclo 21): CHIUSA** — `dash` è in `environment.yml` (commit `bba292e`), `.claude/CLAUDE.md` rimanda a `environment.yml` come unica fonte dell'elenco e `docs/guides/setup.md:5` dice che l'elenco non è ripetuto altrove; `README.md` e `CLAUDE.md` non contengono più una lista di pacchetti.

## C-003 — Media — Doc vs Git: cosa è davvero ignorato da git
- **Dove**: `CLAUDE.md:17` e `README.md:62` ("`*.nii`, `*.nii.gz`, gitignored"); `README.md:58` ("`summaries/`, `logs/` (gitignored)"); `.gitignore`.
- **Prova**: `.gitignore` contiene `data/*`, `results/`, `tmp/`... ma nessun `*.nii*`, `logs/`, `summaries/`. `git ls-files | grep nii.gz` → 22 file tracciati (atlanti e template in `assets/`, voluti). `git ls-files logs summaries | wc -l` → **843** file tracciati (ultimo commit: "logs"). `.gitignore` ha anche `.claude/dim_reduction_clustering/*`, cartella che non esiste.
- **Storia (da `branch_alignment.md:40`, `git log`)**: `.gitignore` ignorava `logs/` e `summaries/` dal 2026-08-31 (`d0ecbbf`); il commit `f577b6a` del 2026-10-23 ("logs") ha tolto quelle regole e aggiunto 813 file (+27402 righe). Anche `branch_alignment.md:40` dice "gitignored... non sono nemmeno tracciati": falso dal 23-10.
- **Impatto**: la regola reale è "`data/` è ignorata", non "i nifti sono ignorati": un `.nii.gz` messo fuori da `data/` finirebbe in git. `logs/` e `summaries/` sono invece versionati, contro quanto scrive il README.
- **Domande**: (a) `logs/` e `summaries/` versionati sono una scelta voluta del 23-10? Se sì correggo `README.md:58` e `branch_alignment.md:40` (e annoto il rischio: con due checkout che scrivono log, i conflitti di rebase aumentano); altrimenti riaggiungo le regole a `.gitignore` e li tolgo dall'indice. (b) correggo `CLAUDE.md:17` in "sotto `data/`, gitignored"? (c) tolgo la riga morta di `.gitignore`?
- **Stato (29-10-26): CHIUSA** — decisione dell'utente: `logs/` e `summaries/` sono versionati di proposito. Corretti `README.md` («versioned in git»), `.claude/CLAUDE.md` («everything under `data/`») e `branch_alignment.md:40`; tolta da `.gitignore` la riga `.claude/dim_reduction_clustering/*`.

## C-004 — Media — Doc vs Doc: descrizioni obsolete delle guide metadata
- **Dove**: `CLAUDE.md:36` ("`metadata.md` (06-09-26, the 3 metadata layers...)"), `CLAUDE.md:35` (`metadata.md` = `enrich_metadata.py`; `evaluate_clustering_tuning.md` = cofenetica/salto/quota) vs `docs/dev/metadata.md:37` ("Quattro file, cinque domande"), `stato_progetto.md:9` ("cinque file in `assets/metadata/`"), `README.md:84-99`.
- **Prova** (anche `stato_progetto.md:9`, "cinque file... ognuno scritto da una pipeline"): `assets/metadata/` contiene 4 CSV (`participants`, `lesion_metadata`, `sdc_metadata`, `excluded_subjects`) + `participants_protected.json` + 2 `*.config.json`; le pipeline sono 5. Le tre fonti usano conteggi diversi ("3 livelli", "quattro file", "cinque file").
- **Impatto**: chi legge non sa quanti file/livelli esistano.
- **Domande**: qual è il conteggio canonico? Riscrivo le descrizioni di `CLAUDE.md:35-36` senza numeri né date (es. "i file in `assets/metadata/` e come si relazionano")?
- **Stato (29-10-26): CHIUSA** — `.claude/CLAUDE.md` descrive `metadata.md` (guida e dev) senza numeri né date.

## C-005 — Bassa — Omissione: `docs/dev/covariance_pca.md` non è nell'elenco di `CLAUDE.md`
- **Dove**: `CLAUDE.md:36`. **Prova**: il file esiste (129 righe) ed è citato da `stato_progetto.md:7`.
- **Domanda**: lo aggiungo all'elenco (o l'elenco diventa "vedi `docs/dev/`")?
- **Stato (29-10-26): CHIUSA** — `covariance_pca.md` aggiunto all'elenco di `docs/dev/` in `.claude/CLAUDE.md`.

## C-006 — Media — Doc vs Codice/Stato: la sezione "Confronto" non è montata
- **Dove**: `CLAUDE.md:36` e `docs/dev/cluster_comparison.md:3` (la presentano come parte di `embedding_app.py`) vs `stato_progetto.md:42` ("rimossa dall'app e parcheggiata").
- **Prova**: in `src/analysis/embedding_app.py`, `comparison_content_for` (:3206) e `cluster_pair_content_for` (:3450) hanno solo la definizione, nessun chiamante in `src/`. Contraddice `code_standards.md` §2 ("niente codice morto") salvo l'eccezione dichiarata in `stato_progetto.md:42`.
- **Domanda**: riscrivo `CLAUDE.md:36` e `dev/cluster_comparison.md:3` dicendo "non montata (parcheggiata)"? L'eccezione al §2 va scritta anche in `code_standards.md`?
- **Stato (29-10-26): CHIUSA** — `CLAUDE.md` dice «parked: not mounted in the app»; `docs/dev/cluster_comparison.md:3` rimanda alla sezione «non montata»; l'eccezione è scritta in `code_standards.md` §2 («Codice parcheggiato»).

## C-007 — Bassa — Doc vs Repo: job SLURM mancanti
- **Dove**: `CLAUDE.md:29`. **Prova**: nessun `jobs/run_embedding_app.sh` (`src/pipeline/embedding_app.py`, server Dash interattivo) né `jobs/run_archive_local_raw_data.sh` (`scripts/archive_local_raw_data.py`, comprime i dati locali).
- **Domanda**: sono eccezioni legittime (aggiungo la clausola alla regola) o servono i job?
- **Stato (29-10-26): CHIUSA** — `.claude/CLAUDE.md` dichiara le due eccezioni (`embedding_app.py`, server interattivo; `archive_local_raw_data.py`, dati locali) alla regola «un job per entry point», sia nella regola sui job sia nella descrizione di `jobs/`.

## C-008 — Bassa — Affermazione troppo generale
- **Dove**: `CLAUDE.md:21` ("every guide under `docs/guides/` documents both"). **Prova**: `datasets.md` ed `evaluation.md` non citano `sbatch`; non descrivono una pipeline.
- **Domanda**: restringo la frase a "ogni guida di una pipeline"? (La verifica guida per guida avverrà con `docs/guides/`.)
- **Stato (29-10-26): CHIUSA** — `.claude/CLAUDE.md:21` ora dice «every pipeline guide».

## C-009 — Bassa — Date non coerenti con git
- **Dove**: `CLAUDE.md:35` (`dim_reduction_clustering.md` ritirata il 14-08-26; `project_changelog.md:816` dice 14-08-26) e `CLAUDE.md:37` (merge `docs/dr-clustering-literature-migration` il 18-08-26).
- **Prova**: commit `2991ec1` (rimozione) = 2026-08-15 11:54; merge `f9e2d30` = 2026-08-21; `project_changelog.md` non cita il merge. Il commit `2ed3dcb` che ritira gli atlanti ha il messaggio "Extend build_lesion_matrix to UCL-UK, remove parcellate feature" (non cita il ritiro di `build_combined_atlas`).
- **Domanda**: tengo le date del changelog (data del lavoro) o allineo a git? Tolgo le date da `CLAUDE.md` (regola "presente, non passato")?
- **Stato (29-10-26): CHIUSA** — tolte da `.claude/CLAUDE.md` le due date non coerenti con git (ritiro di `dim_reduction_clustering.md`, merge `docs/dr-clustering-literature-migration`); restano i rimandi a `project_changelog.md` e `git log`. Le altre date dell'elenco non erano contestate.

## C-010 — Media — Regola `CLAUDE.md:53` violata dai file che governa (verifica preliminare)
- **Dove**: `README.md:66-72` (sezione "Retired pipelines"), `docs/guides/datasets.md:5` ("lo faceva in automatico: è stata ritirata"), `docs/dev/metadata.md:71` ("non esistono più: cancellati... è stato spostato"), `docs/dev/metadata.md:103` ("prima della separazione le metriche erano sparse"). Inoltre `docs/dev/models.md:76` cita "(project-clustering-tuning-redesign memory)", una memoria privata dell'agente, non un file del repo.
- **Prova**: grep mirato su `docs/guides`, `docs/dev`, `README.md`; da confermare file per file nell'audit di ciascuno.
- **Domanda**: la regola ammette eccezioni (es. una sezione "Retired" nel README) oppure si tolgono questi passaggi (e il riferimento alla memoria)?
- **Ciclo 20**: `docs/dev/models.md` cita memorie private dell'assistente in sei punti (`:72` «`project-clustering-tuning-evaluation-tables` memory», `:76`, `:108`, `:122`, `:136` «`project-clustering-tuning-redesign`», `:157`): nessuna è un file del repo.
- **Stato (29-10-26): CHIUSA** — decisione dell'utente: tolti i passaggi storici. `README.md` ha una sola riga che rimanda a `.claude/history/project_changelog.md`; `datasets.md:5`, `dev/metadata.md` (tsv, separazione) riscritti al presente; tolti i rimandi alle memorie in `dev/models.md`.

## C-011 — Bassa — Perimetro di `code_standards.md`
- **Dove**: `CLAUDE.md:70` ("`src/` (and its tests)") vs `code_standards.md:3` ("`src/`, `scripts/` (e i relativi test)").
- **Domanda**: allineo `CLAUDE.md:70` aggiungendo `scripts/`?
- **Stato (29-10-26): CHIUSA** — `.claude/CLAUDE.md` dice «`src/` and `scripts/` (and their tests in `tests/`)», come `code_standards.md:3`.

## C-012 — Bassa — `.claude/audit/` non è nella struttura di `CLAUDE.md`
- **Dove**: `CLAUDE.md:31-49` non cita `.claude/audit/`; `.claude/skills/` e `.claude/settings.local.json` non sono documentati né in `CLAUDE.md` né nel perimetro dell'audit.
- **Domanda**: a fine audit documento `.claude/audit/`? `skills/` e `settings.local.json` entrano nell'audit (li ho messi in `00_master_plan.md` §1.1c)?
- **Stato (29-10-26): APERTA, aggiornata** — decisione dell'utente: documentare `.claude/audit/` in `.claude/CLAUDE.md` a fine audit; `skills/` e `settings.local.json` restano fuori. Nulla da fare finché l'audit non finisce.
- **Stato (02-11-26): CHIUSA** — `.claude/audit/` documentato in `.claude/CLAUDE.md` (Repository structure): cosa contiene, a che punto sono le due fasi, da dove si riprende. `skills/` e `settings.local.json` restano fuori, come deciso.

## C-013 — Bassa — Percorsi dell'ambiente hardcoded nei job (da rivedere in Fase 2)
- **Dove**: `jobs/run_*.sh` (es. `jobs/run_build_lesion_matrix.sh:7,11,17`: `/home/etosato/Projects/NEMESIS_fs`, `/home/etosato/miniconda3/...`).
- **Prova**: il job "di riferimento" di `CLAUDE.md:24` contiene percorsi assoluti dell'utente sul cluster, contro `code_standards.md` §5 ("nessun valore ambiente-dipendente hardcoded").
- **Domanda**: accettabile per script SLURM (specifici del cluster) o vanno parametrizzati? Da decidere prima della Fase 2 sui `jobs/`.
- **Stato (29-10-26): CHIUSA** — decisione dell'utente: i percorsi del cluster nei 18 job (`PROJECT_ROOT`, `conda.sh`, log SLURM) restano; `code_standards.md` §5 li dichiara eccezione («`jobs/*.sh` contengono i percorsi del cluster»).

---

## `stato_progetto.md`

## C-014 — Media — Doc vs Git: HEAD e working tree obsoleti
- **Dove**: `stato_progetto.md:34` ("HEAD `790fcc1`... working tree contiene lavoro non committato dell'utente: `anatomical_maps.py`, `cluster_overview.py`, `dendrogram_splits.py`, `tuning_match.py`...").
- **Prova**: `git log -1` → `f577b6a logs`; `790fcc1` è 16 commit indietro; `git status` a inizio sessione: pulito. Ora risulta modificato solo `.claude/history/project_changelog.md` (+17 righe), che non ho toccato.
- **Impatto**: la regola "committare solo i propri file" descrive uno stato che non c'è più; un HEAD scritto a mano invecchia a ogni commit.
- **Domanda**: tolgo HEAD e l'elenco dei file non committati dalla riga (lo stato git si legge con `git`)? Il `project_changelog.md` modificato è una tua modifica in corso?
- **Stato (29-10-26): CHIUSA** — tolto l'elenco dei file non committati da `stato_progetto.md`.

## C-015 — Media — Thread aperto già chiuso: omogeneità/completezza nel notebook di confronto
- **Dove**: `stato_progetto.md:26`; `lessons_learned.md` #41 ("Il notebook non è ancora corretto").
- **Prova**: in `clustering_comparison.ipynb` nessuna cella chiama `homogeneity_score`/`completeness_score`; la cella 60 usa `agreement_metrics(labels_a, labels_b)`, che chiama `homogeneity_score(labels_b, labels_a)` (`src/analysis/cluster_comparison.py:170-171`). La cella 59 descrive homogeneity come "ogni cluster di A contiene soggetti di un solo cluster di B": coincide con quel codice (A = predetto, B = vero).
- **Impatto**: tolgo lavoro già fatto dalla lista dei thread aperti; la lesson #41 è parzialmente falsa.
- **Domanda**: confermi che è risolto? Se sì, rimuovo la riga da `stato_progetto.md` e correggo l'ultima frase di #41 quando audito `lessons_learned.md`.
- **Stato (29-10-26): CHIUSA** — tolta la riga su homogeneity/completeness da `stato_progetto.md`; l'ultima frase di `lessons_learned.md` #41 ora dice che il notebook usa `agreement_metrics`.

## C-016 — Bassa — Elenco di `docs/dev/` incompleto
- **Dove**: `stato_progetto.md:7`. **Prova**: mancano `anatomical_maps`, `cluster_comparison`, `cluster_composition`, `cluster_description`, `cluster_drivers`, `pipeline_flow` (tutti esistono). Stessa omissione di C-005.
- **Domanda**: sostituisco l'elenco con "vedi `docs/dev/`"?
- **Stato (29-10-26): CHIUSA** — `stato_progetto.md:7` rimanda all'elenco di `.claude/CLAUDE.md` invece di ripeterlo.

## C-017 — Media — Contraddizioni interne a `stato_progetto.md` sulle metriche di agglomerative
- **Dove**: `:15` (Dunn e quota del cluster più grande già valutazioni del registro; CH e DB vuoti con metrica non euclidea "ovunque") vs `:37` ("per Dunn, CH e DB nel notebook e nella produzione di agglomerative resta da fare") vs `:50 (3)` ("decidere le metriche di agglomerative ancora fuori dal registro (Dunn, quota del cluster più grande, silhouette per cluster)").
- **Prova**: anche `open_problems.md:110` dice che `dunn_index` e `largest_cluster_share` sono nel registro, mentre `open_problems.md:132` dice che `largest_cluster_share` e `n_small_clusters` "non sono calcolati per agglomerative". `config/registry/clustering_evaluations.json` contiene già `largest_cluster_share` e `dunn_index`; `clustering_tuning_report.py:59,65` le usa.
- **Impatto**: il "prossimo passo" (3) chiede di decidere ciò che è già deciso e implementato; "ovunque" (L15) contraddice "resta da fare" (L37).
- **Domande**: (a) del punto (3) resta solo la silhouette per cluster? (b) la regola euclidea è già applicata nel notebook e in produzione, oppure no?
- **Stato (29-10-26): CHIUSA** — decisione dell'utente: anche la silhouette per cluster è fatta. `stato_progetto.md` e `open_problems.md` allineati (Dunn, quota del cluster più grande e silhouette per cluster sono in produzione; resta aperto solo `n_small_clusters`).

## C-018 — Bassa — Riferimenti non riproducibili alla run mancante
- **Dove**: `stato_progetto.md:21` ("29 run su 30, manca `hdbscan_soft` nc10 `mcs=100`, `ms=20`, `eom` sulla matrice del 16-10").
- **Prova**: `results/sdc/clustering/production/hdbscan_soft/pca/` contiene `19-10_s2.4-vol_nc{2,12,30}_mcs.._ms.._sel_..` (20 cartelle); nessun `nc10`; la matrice è "16-10" ma i nomi riportano il 19-10 (data dell'embedding PCA). Il "30" non si ricostruisce dai conteggi (agglomerative 31, hdbscan 20, hdbscan_soft 20).
- **Domanda**: quale griglia dà 30 run, e qual è esattamente la run mancante (nc10 o nc12)?
- **Stato (29-10-26): CHIUSA** — riscritte le due frasi di `stato_progetto.md`: dicono solo cosa c'è su disco (`hdbscan_soft`, `19-10_s2.4-vol_nc*`, 5 run per nc in {2, 12, 30, 42}, nessuna nc10), senza il «29 su 30» e senza nominare una run mancante.

---

## `code_standards.md`

Scansioni AST su `src/` + `scripts/`; ogni numero è riproducibile con `grep`/`ast`.

## C-019 — Media — §0/§3/§6: errori inghiottiti in `embedding_plots.py`
- **Dove**: `src/analysis/embedding_plots.py:63, 72, 88, 115, 134` (`except Exception as exc: logging.warning(...)` e si prosegue).
- **Prova**: la rotta di errore non rilancia né usa `exc_info`; un plot che fallisce per un bug qualunque (non per I/O) produce solo un warning e la run risulta riuscita. Gli altri 4 `except Exception` di `src/pipeline/` rilanciano dopo la pulizia e sono corretti.
- **Impatto**: è esattamente il pattern che il §0 vieta ("`except: pass`"-like); il test non lo vede.
- **Domanda**: i plot sono ausiliari e la tolleranza è voluta (allora la scrivo come eccezione nel §0 e restringo le eccezioni catturate), oppure l'errore deve fermare la run?
- **Stato (29-10-26): CHIUSA** — via di mezzo: `embedding_plots.py` cattura solo `OSError` e `ValueError`, logga un WARNING con il conteggio dei grafici non scritti, ogni altra eccezione ferma la run; eccezione dichiarata in `code_standards.md` §0; 2 test nuovi, 4 test adattati.

## C-020 — Media — §6: "ogni eccezione loggata con `exc_info=True`" non è la pratica
- **Dove**: `code_standards.md:94`. **Prova**: 114 log di `error`/`warning`/`exception` dentro un `except`; 73 non hanno `exc_info` e non rilanciano (es. `embedding_app.py:707,757,776,840,2973`, `tuning_match.py:143`, `features/functional.py:324`, `embedding_plots.py`).
- **Impatto**: la regola letterale è violata in massa, oppure la regola è più larga di ciò che intende (errori di dominio attesi vs eccezioni inattese).
- **Domanda**: riscrivo il §6 ("`exc_info=True` per le eccezioni inattese; per gli errori di dominio basta il messaggio") o si corregge il codice?
- **Stato (29-10-26): CHIUSA** — `code_standards.md` §6 riscritto: `exc_info=True` per le eccezioni inattese, solo il messaggio con la causa per gli errori di dominio.

## C-021 — Media — §6: tre entry point senza `log_duration`
- **Dove**: `code_standards.md:96` vs `src/pipeline/embedding_app.py`, `generate_understanding_umap_report.py`, `replot_dim_reduction.py` (nessuno chiama `log_duration`).
- **Prova**: 15 dei 18 entry point la chiamano, tutti dentro un `finally`.
- **Domanda**: `embedding_app` (server Dash) è un'eccezione legittima? Per gli altri due aggiungo `log_duration` o li dichiaro eccezioni?
- **Stato (29-10-26): CHIUSA** — `generate_understanding_umap_report.py` e `replot_dim_reduction.py` chiamano `log_duration` in un `finally` (2 test nuovi); `embedding_app.py` dichiarato eccezione in `code_standards.md` §6.

## C-022 — Media — §1/§2: dimensione di moduli e funzioni
- **Dove**: `code_standards.md:41,53`. **Prova**: `src/analysis/embedding_app.py` = 5540 righe, `build_app` (:3998) = 1543 righe; altre >150: `understanding_umap_report.py:594` (219), `:934` (167), `embedding_app.py:1087` (185), `pipeline/clustering.py:335` (181), `build_sdc_matrix.py:46 main` (162). 211 funzioni su 960 superano 30 righe, 18 superano 100.
- **Impatto**: "idealmente <30" è un obiettivo, ma un modulo di 5540 righe con una funzione da 1543 contraddice "una responsabilità per modulo".
- **Domanda**: la regola resta indicativa, oppure pianifichiamo lo spezzamento di `embedding_app.py` (fuori dall'audit, che è sola lettura)?
- **Stato (29-10-26): APERTA, aggiornata** — decisione dell'utente: pianificare uno spezzamento modulare. Piano scritto in `06_piano_spezzamento_embedding_app.md`; nessun codice toccato. Resta aperta fino all'esecuzione.
- **Aggiornamento (29-10-26)**: l'utente la lascia aperta, l'esecuzione è complessa; nessun lavoro in corso.
- **Stato (02-11-26): CHIUSA** — piano eseguito in 12 commit (`9db71c3`..`2ebaa1b`): `src/analysis/embedding_app.py` è il pacchetto `src/analysis/embedding_app/` (18 moduli, 6180 righe, il più grande 652), `build_app` 1543 → 358. Esito e scostamenti dal piano nella §8 di `06_piano_spezzamento_embedding_app.md`; decisione e alternative scartate in `project_changelog.md` (02-11-26).
- **Ri-misurato**: 991 funzioni in `src/`+`scripts/` (erano 960), 225 sopra le 30 righe (erano 211), 21 sopra le 100 (18), 3 sopra le 200 (2). Il massimo scende da 1543 a 358 (`build_app`), ma le altre due oltre le 150 sono nuove: `panels/cluster_maps.py::register_callbacks` (266, 12 callback) e `anatomy.py::register_callbacks` (188, 9) — nessun callback al loro interno supera le 30 righe, è la lista delle registrazioni a essere lunga. Il §1 («una responsabilità per modulo») è soddisfatto; il §2 («idealmente <30») resta un obiettivo, come già scritto qui sopra.

## C-023 — Media — §2: codice morto (a meno dell'eccezione "Confronto")
- **Dove**: `src/analysis/clustering_tuning.py:861 integrated_completed_likelihood`, `:917 compute_gap_statistic`; `dendrogram_splits.py:167 colors_at`; `embedding_app.py:2964 comparable_runs`, `:3206 comparison_content_for`, `:3246 pair_cluster_option_label`.
- **Prova**: riferiti solo dai test (nessun uso in `src/`, notebook, config). Le ultime tre appartengono alla sezione "Confronto" parcheggiata (C-006). `integrated_completed_likelihood`/`compute_gap_statistic` servono a kmeans/gmm, in stand-by (`stato_progetto.md:16`); `colors_at` non ha una spiegazione.
- **Domanda**: i tre di kmeans/gmm e `colors_at` restano (e li annoto come parcheggiati) o si cancellano? L'eccezione del §2 per il codice parcheggiato va scritta nel §2?
- **Stato (29-10-26): CHIUSA** — mosse in `tests/legacy/kmeans_gmm_post_hoc_diagnostics.py` `integrated_completed_likelihood`, `compute_gap_statistic`, `gap_statistic_suggested_k` e in `tests/legacy/dendrogram_colors_at.py` `colors_at` (i test del Dendrogram Explorer usano un helper locale `_colors_at`, ultimo passo di `replay_splits`). Restano in `src/` le tre funzioni della sezione «Confronto» (eccezione dichiarata in `code_standards.md` §2).

## C-024 — Bassa — §4: mock su funzioni del repo
- **Dove**: `tests/` (315 `monkeypatch.setattr`). **Prova**: ~295 sostituiscono costanti di percorso con `tmp_path` (isolamento, legittimo); ~13 sostituiscono funzioni del repo: `embedding_app.build_app` ×3, `discover_production_runs` ×6, `load_*_config` ×4, `dim_reduction.load_matrix` ×2, `clustering.run_clustering_tuning_sweep`, `build_fc_matrix.save_matrix`.
- **Domanda**: li esamino uno a uno in Fase 2 (tests/) contro "mai mockare il codice sotto test"?
- **Stato (29-10-26): CHIUSA** — esaminati tutti i 51 punti dove un test sostituisce una funzione del repo (non erano 13): spie che chiamano la funzione vera, iniezioni di errore, dipendenze che non possono girare (server Dash). Due da correggere: `test_distances.py` forzava `_is_binary` (ora usa dati scalati ×2, che raggiungono il ramo continuo senza sostituzioni) e `test_build_dataset_summary_table_paths.py` sostituiva `group_of` (ora usa un ID PD vero). `code_standards.md` §4 elenca i casi ammessi.

## C-025 — Bassa — §5/§1: percorsi di output come costanti nei moduli
- **Dove**: `src/pipeline/*.py` (`LOGS_ROOT = Path("logs") / "<nome>"`, `REPORTS_ROOT`), `participants.py` (`METADATA_ROOT`). **Prova**: ~14 moduli; i test devono fare `monkeypatch` di una costante.
- **Domanda**: i percorsi relativi di log/report sono un'eccezione al §5 (da scrivere) o vanno in `config/`?
- **Stato (29-10-26): CHIUSA** — decisione dell'utente: `LOGS_ROOT`/`REPORTS_ROOT`/`METADATA_ROOT` restano costanti di modulo; `code_standards.md` §5 dichiara l'eccezione (struttura del repo, uguale su ogni macchina; i test usano `tmp_path`).

## C-026 — Bassa — §8: nome sbagliato del file delle lezioni
- **Dove**: `code_standards.md:110` (`lesson_learned.md`). **Prova**: il file è `.claude/lessons_learned.md`. **Domanda**: correggo?
- **Stato (29-10-26): CHIUSA** — `code_standards.md` §8 cita `lessons_learned.md`.

## C-027 — Bassa — §0: esempio che cita codice ritirato
- **Dove**: `code_standards.md:16-29` (`self.has_derivatives()`, `manual_masks`, `self.name`). **Prova**: nessuna occorrenza in `src/`; viene dal modulo ritirato `src/retrieval/dataset.py`. **Domanda**: lo sostituisco con un esempio vivo (es. `group_of` in `subject_ids.py:25`)?
- **Stato (29-10-26): CHIUSA** — l'esempio «Va bene» di `code_standards.md` §0 è ora `group_of` (`src/utils/subject_ids.py`).

## C-028 — Bassa — §1/§2: testo non più applicabile
- **Dove**: `code_standards.md:40` (livello `models`: non esiste `src/models/`; il livello è solo `analysis`); `:56` vs `src/analysis/plotting.py:64-67` (commento su una funzione rimossa il 01-09-26).
- **Domanda**: tolgo `models` dal §1 e riscrivo/cancello il commento in `plotting.py`?
- **Stato (29-10-26): CHIUSA** — tolto `models` dal §1 di `code_standards.md`; il commento di `src/analysis/plotting.py` (marker condivisi) descrive solo la regola attuale. Solo commento, nessun test cambiato.

## C-029 — Bassa — §2: due funzioni pubbliche senza annotazioni complete
- **Dove**: `src/analysis/clustering.py:36 hdbscan_soft_fit` (manca il tipo di ritorno), `:53 soft_membership_matrix(fitted)` (manca il tipo del parametro).
- **Prova**: 472/478 pubbliche complete; le altre 4 sono funzioni interne (`embedding_app.py:2713, 2992, 4763`, `clustering_tuning_analysis.py:229`). **Domanda**: le completo?
- **Stato (29-10-26): CHIUSA** — `src/analysis/clustering.py`: `hdbscan_soft_fit(...) -> hdbscan.HDBSCAN` e `soft_membership_matrix(fitted: hdbscan.HDBSCAN)`, con `hdbscan` importato sotto `TYPE_CHECKING` (il pacchetto resta importato dentro la funzione). Le altre 4 senza annotazioni (`other`, `cells`, `label`, `ordered`) sono funzioni annidate, non pubbliche. Nessun cambio di comportamento: suite 5754 passed, 17 skipped.

---

## `branch_alignment.md`

## C-030 — Bassa — `origin/server-pnc`: "storico" ma con 13 commit non in `main`
- **Dove**: `branch_alignment.md:3`. **Prova**: `git rev-list --count main..origin/server-pnc` = 21; `git cherry main origin/server-pnc`: 13 `+` (non in `main`), 8 `-` (equivalenti); ultimo commit 2026-08-22; merge-base `53dbab6` (2026-07-28, il commit che crea `branch_alignment.md`). I `+` includono "Resume compute_sdc production run, log TODO on streamline provenance" (3-8) e "Log compute_sdc production completion, add 2 lessons learned" (7-8).
- **Impatto**: se il branch viene cancellato, quel lavoro (log di produzione, 2 lezioni, TODO sulla provenienza dello streamline) sparisce dal remoto.
- **Domanda**: il contenuto è già in `main` per altra via (`lessons_learned.md` #26/#27 sembrano le due lezioni) e si può cancellare `origin/server-pnc`, o lo tengo com'è? Il documento deve dire "non integrato" invece di "storico"?
- **Stato (29-10-26): CHIUSA** — rimossa da `branch_alignment.md:3` la frase su `origin/server-pnc`; il ramo remoto lo gestisce l'utente. Le due lezioni erano già in `lessons_learned.md` #26/#27; la riga di `TODO.md` sul file `streamline.csv` di `sub_BCB_example/` resta solo nel ramo.

---

## `open_problems.md`

Le cifre sui dati (PSP, WashU, 0671, sede, FC) sono state ricalcolate sui dati locali e tornano (X-001…X-011). Restano non verificabili in locale le misure sul cluster (X-012).

## C-031 — Media — Voci di `open_problems.md` che non sono più aperte o non sono più vere
- **Dove**: `:159` ("`CLAUDE.md` non contiene la regola sul markdown dei notebook"), `:181` ("`anatomical_maps.py` non committato"), `:165` (5150 vs 5151 maschere), `:209` (`s1_production.md`), `:214` (`viz-niivue`, "recuperabile da `facef6f`"), `:195` (#41 obsoleta, mentre `stato_progetto.md:26` la dà ancora per aperta).
- **Prova**: `CLAUDE.md:63` contiene la regola; `git ls-files src/analysis/anatomical_maps.py` lo mostra tracciato e `git status` è pulito; `datasets.md:59` spiega già 5150/704; `find . -name s1_production.md` non trova il file; `git cat-file -t facef6f` → "Not a valid object name".
- **Impatto**: il file si definisce "elenco vivo, una voce si cancella quando è chiusa" (`:5`); sei voci non lo sono.
- **Domanda**: le rimuovo? (`:214` è una nota storica: tengo l'hash solo se è ancora valido.)
- **Stato (29-10-26): CHIUSA** — rimosse da `open_problems.md` le voci su regola dei notebook, `anatomical_maps.py`, `s1_production.md` e `viz-niivue`; la voce 5150/5151 ridotta alla differenza 5852/5853 ancora aperta (C-110); #41 tolta dalla voce «Storico».

## C-032 — Bassa — Conteggi dei tuning senza report non coincidenti
- **Dove**: `open_problems.md:113` ("12 di agglomerative, 12 di HDBSCAN... Le 48 cartelle con report sono state rigenerate il 23-10-26").
- **Prova**: senza `report.md`: agglomerative 15, hdbscan 15 (le 3 in più sono `09-10_*`); `report.md` presenti: agglomerative 48, hdbscan 32, hdbscan_soft 32; modificati il 23-10: 48, tutti agglomerative (i 64 di HDBSCAN restano vecchi, come dice `stato_progetto.md:22`).
- **Domanda**: aggiorno i numeri (15+15) e preciso che le 48 sono solo di agglomerative?
- **Stato (02-11-26): CHIUSA** — numeri già giusti (12+12 senza report, 48 con report, 16 per metodo); corretta la data: i 48 `report.md` sono del 27-10-26, non del 23-10 (`open_problems.md`, `stato_progetto.md`).

## C-033 — Bassa — Decisione del 23-10 non propagata
- **Dove**: `open_problems.md:34` (decisione A: `participants.csv` riporta il lato clinico) vs `:84-90` (il 23-10 il lato diventa tutto geometrico, "supera la decisione A"); `stato_progetto.md` non cita la decisione; `README.md:94` ("a clinical value is never overwritten") la contraddirà quando sarà implementata. `:86` dà ~1445 soggetti con lato clinico, `participants.csv` ne ha 1448.
- **Domanda**: marco la decisione A come superata nel testo di `:34` e aggiorno 1445→1448?
- **Stato (02-11-26): CHIUSA** — in `open_problems.md` la decisione A è segnata come superata dalla decisione del 23-10-26 (che vale quando sarà implementata); 1445 → 1448. `README.md:94` resta vero finché la decisione del 23-10 non è implementata.

## C-034 — Media — Soggetti tutti-zero: "lasciati" nella documentazione, esclusi nei dati
- **Dove**: `open_problems.md:213` e `docs/experiments/s1.3-vol.md:24` (`sub-STUKE0146`, `sub-STUKE0201` restano come righe tutte-zero, "2 su 5720") vs `assets/metadata/excluded_subjects.csv` (entrambi `empty_mask`, `scope=all`, che le due pipeline di matrici usano come lista di ammissione).
- **Impatto**: dopo l'introduzione di `excluded_subjects.csv` una nuova `s1.3-vol` non li conterrebbe; la decisione del 07-09 è stata superata senza che la nota lo dica.
- **Domanda**: la nota di `:213` e la sezione di `s1.3-vol.md` vanno riscritte (la matrice s1.3-vol esistente li contiene, le nuove no)? Lo verifico nell'audit di `docs/experiments/`.
- **Stato (29-10-26): CHIUSA** — riscritte la nota di `open_problems.md` e la sezione di `docs/experiments/s1.3-vol.md`: la matrice `s1.3-vol` li contiene, `excluded_subjects.csv` li esclude, una matrice nuova no.

## C-035 — Bassa — UKLFR `NIHSS_5a/5b`: 82 soggetti, non 75
- **Dove**: `open_problems.md:66`. **Prova**: nel tsv UKLFR i soggetti con `5a != 5b` e lato noto sono 82; tutti omolaterali (34 sinistra + 48 destra), quindi la conclusione regge, il conteggio no. **Domanda**: aggiorno 75/75 in 82/82 (o indico il filtro usato)?

---
- **Stato (02-11-26): CHIUSA** — ricontato sul tsv UKLFR: 82 soggetti con `5a != 5b`, tutti omolaterali (34 sinistra, 48 destra); 75/75 → 82/82.

## `lessons_learned.md`

## C-036 — Media — I rimandi "Seen in" puntano a file ritirati, rinominati o spostati
- **Dove**: `lessons_learned.md:5` ("per la narrazione completa segui il suo rimando in `docs/debugging/`") e i pattern #2 (:14), #3 (:18), #5 (:26), #9 (:42), #10 (:46), #12 (:54), #14 (:61-62), #16 (:70), #19 (:82), #20 (:86), #21 (:90), #24 (:102), #25 (:106), #27 (:114), #30 (:126), #34 (:142), #37 (:154), #38 (:156-159), #28 (:116-117).
- **Prova**: 22 percorsi non esistono. Ritirati (restano in `git log`): `src/retrieval/`, `src/sdc/`, `compute_sdc`, `scripts/verify_retrieval.py`, `scripts/data_summary.py`, `scripts/backfill_stale_tuning_output_paths.py`, `scripts/build_dim_reduction_strategies_csv.py`, `jobs/run_compute_sdc.sh`, `docs/dev/retrieval.md`. Rinominati/spostati: `scripts/replot_dim_reduction.py` → `src/pipeline/replot_dim_reduction.py`, `enrich_lesion_metadata.{py,json}` → `enrich_metadata`, `_subjects_with_lesion_mask` → `subjects_with_lesion_mask`, `AUDIT_FINDINGS.md` → `docs/debugging/`, il tsv UCL-UK di `assets/metadata/` cancellato.
- **Impatto**: chi segue un rimando trova un file mancante senza sapere se è un errore. Nessuna delle lezioni è falsa; sono i puntatori a essere stantii.
- **Domanda**: scelgo una convenzione per i riferimenti storici? (a) aggiungo "(ritirato, `git log`)" accanto ai percorsi che non esistono più, (b) aggiorno solo i nomi rinominati, o (c) lascio com'è, dato che sono storici.
- **Stato (29-10-26): CHIUSA** — scelta (a): annotati in `lessons_learned.md` i percorsi non più esistenti («ritirato, `git log`», «ora …», «cancellato»), 24 annotazioni.

## C-037 — Bassa — #17: il test di regressione citato non esiste più
- **Dove**: `lessons_learned.md:72-75` (#17: `regress_out_volume`, "Regression test added... `test_dim_reduction_fine_tuning_nested_n_components_and_regress_out_volume_refits_viz`").
- **Prova**: `grep regress_out` in `src/` e `tests/` → 0; il test con quel nome non c'è. Restano `embedding_for_viz` e `test_embedding_for_viz_forwards_precompute_distance_metric_to_refit`. La regola generale della lesson resta valida.
- **Domanda**: la funzionalità è stata rimossa di proposito (allora annoto "rimossa, la lezione resta") o il test è andato perso? Lo verifico in `docs/debugging/`/`methods_changelog.md`.
- **Stato (02-11-26): CHIUSA** — `regress_out_volume` è stato rimosso il 12-08-26 (`3edb5b9`); annotato in `lessons_learned.md` #17 che il test citato è sparito con la funzione e la lezione resta.

## C-038 — Bassa — `debug_17_08_26.md` e `debug_22_08_26.md` non sono citati dal registro delle lezioni
- **Dove**: `lessons_learned.md` (nessun "Seen in" verso i due file); `code_standards.md:110` (ogni bug ha "lessons learned" obbligatorio).
- **Prova**: i due report (2320 e 555 righe, 6 e 19 sezioni) citano le lezioni #14, #18, #26-28 al loro interno, ma il registro non li elenca. In più `debug_10_09_26.md` usa `## §N —` mentre gli altri 14 usano `## N.`.
- **Domanda**: aggiungo i rimandi inversi dove una lezione è nata da quei report? Uniformo il formato dei titoli?

---
- **Stato (02-11-26): CHIUSA** — aggiunti i rimandi a `debug_22_08_26.md` ai «Seen in» di #4, #5, #7, #15, #17, #21, #28 (`debug_17_08_26.md` era già in #28 dopo C-099). Formato dei titoli di `debug_10_09_26.md` (`## §N —`) lasciato com'è.

## `history/data_changelog.md` e skill `history`

Le cifre sui dati tornano; i problemi sono "conseguenze ancora vere oggi" che non lo sono più e un caso di `has_features` fuori dal vero.

## C-039 — Media — `has_features` di WashU nel registro: 10 su 195, non 169
- **Dove**: `data_changelog.md:193-197` (05-09: `has_features` da 10 a 169 ST dopo il ripristino; "la correzione resta manuale") e `docs/dev/metadata.md:57-63` ("dopo aver lanciato `populate_metadata.py`... correggi a mano i `has_*`").
- **Prova**: `participants.csv`: WashU 195 ST, `has_features=True` per 10; `config/pipelines/populate_metadata.json` (`run_notes`): la run del 23-09 con `overwrite: true` ha fatto il resync su tutti i dataset, con `features/` potata. `mask_summary.csv` ha 169 righe e il manifest della cartella potata elenca la popolazione reale.
- **Impatto**: chi filtra su `has_features` perde 159 soggetti WashU con FC reale; la correzione manuale non è stata rifatta dopo l'ultima run.
- **Domanda**: rifaccio la correzione (169, via manifest) e la registro, o `has_features` deve tornare a descrivere il disco locale e il dato reale va letto dal manifest?
- **Stato (29-10-26): CHIUSA** — decisione dell'utente: il dato vero si legge dal manifest. `dev/metadata.md` e `guides/metadata.md` dicono che `has_*` descrive il disco locale; nota «superata» in `data_changelog.md` (05-09).

## C-040 — Media — Conseguenze "ancora vere oggi" non più vere, o eventi non registrati
- **Dove**: `data_changelog.md`: (a) `:98-102` e `:130-134` (23-09: `participants.csv` non riflette NEMESIS_T0/SFB936/UKLFR/WashU); (b) `:156-158` (07-09: chi usa `07-09_s2.2-vol` deve escludere `0671`); (c) `:162-189` (06-09: nessuna decisione sui due soggetti UKE, restano in `06-09_s1.3-vol`); (d) `:82` vs `:91` (23-09: `sub-p123`→`0667` tra le cartelle rinominate, ma è solo-tsv).
- **Prova**: (a) `participants.csv` ha tutti e 8 i dataset e `populate_metadata.json` li elenca; (b) la sostituzione maschere del 23-09 ha reso vuota la maschera di `0671` (0 voxel), che oggi è in `excluded_subjects.csv`: `open_problems.md:72` rimanda a "data_changelog.md" per la cancellazione, ma il 23-09 non nomina `0671`; (c) `excluded_subjects.csv` esclude `0146`/`0201` (`empty_mask`, `all`), i loro volumi a 1 mm oggi sono 8 e 3 (la voce dice 16 e 3); (d) la cartella `sub-STUNIPD0667` non esiste (76 cartelle da 0586 a 0666).
- **Impatto**: l'archivio che dovrebbe spiegare "cosa è successo ai dati" tace sul fatto con più conseguenze (maschera di `0671` svuotata, volume di `0146` dimezzato) e afferma stati superati.
- **Domande**: (1) aggiungo una nota (con data) a ciascuna voce per dire come è stata superata, senza riscrivere la storia? (2) so qualcosa sul perché `0671` e `0146` sono cambiati il 23-09 (rsync, versione diversa del file)? Dimmelo e lo registro.
- **Stato (29-10-26): CHIUSA** — aggiunte note «superata» a `data_changelog.md` (23-09, 07-09, 05-09). Indagine: `sub-STUKE0146` 16→8 è la correzione dei voxel fuori dal brain, non un cambio dei dati; `sub-STUKLFR0671` ha oggi una maschera vuota e gli output di BCBToolKit (26-08, 03-09) sono nulli, mentre le matrici costruite prima del 23-09 la avevano non vuota (23.960 voxel a 2 mm). **Aperta**: perché la maschera sia cambiata; serve il file originale sul server. **Decisione dell'utente**: la maschera vuota di `sub-STUKLFR0671` è corretta (la vecchia copia non vuota non lo era); registrato in `data_changelog.md` e `open_problems.md`. Il motivo del cambio del 23-09 non è ricostruibile (l'utente non ha il file del server) e non serve.

---

## `history/project_changelog.md` (audit parziale: righe 1-64 + script su tutto il file)

## C-041 — Bassa — Due "recuperabile da <SHA>" non funzionano in questa copia del repo
- **Dove**: `project_changelog.md:742` (`backup-pre-split` da `068d2ff`) e `:752` (`viz-niivue` da `facef6f`, "finché il reflog lo conserva (~90 giorni)"); anche `open_problems.md:214`.
- **Prova**: `git cat-file -t 068d2ff` e `facef6f` → "Not a valid object name". Il secondo ha 49 giorni (07-09 → 26-10), cioè entro i 90.
- **Impatto**: lo SHA annotato "proprio perché un branch cancellato non compare in `git log`" non permette il recupero qui; può esistere solo nell'altro checkout (server) o essere stato ripulito da `git gc`.
- **Domanda**: i due oggetti esistono sul server? Se no, tolgo la frase "recuperabile" (la storia dei due branch non è più recuperabile) e chiudo anche la voce di `open_problems.md`.
- **Stato (02-11-26): CHIUSA** — i due SHA sono già segnati «non più recuperabile» (C-103); la voce in `open_problems.md` non c'è più; «ancora vera oggi» → «vera al 23-09-26».

## C-042 — Bassa — Formato e conteggi del registro
- **Dove**: `project_changelog.md:883` (`## 2026-08 — Produzione e tuning separati…`, data senza giorno, contro il formato `GG-MM-AA` dello skill `history`); `:39-54` (backup "88 MB", tabella di 4 sottocartelle, ma sul disco ce ne sono 6 e 95 MB); `00_master_plan.md` (832 righe al bootstrap, oggi 887: il file cresce mentre lo audito).
- **Domanda**: normalizzo il titolo dell'ultima voce con una data completa? Aggiorno il backup "88 MB / 4 cartelle" (le altre due sono descritte nelle due voci precedenti dello stesso giorno)?

---
- **Stato (02-11-26): CHIUSA** — backup in `project_changelog.md`: 95 MB e sette sottocartelle (aggiunte `old_interclass` e `old_membership_share`). Il titolo `## 08-26` resta senza giorno: non è ricostruibile.

## `docs/setup.md` (ciclo 9)

## C-043 — Media — `setup.md:26`: `--prune` rimuove `dash` dall'ambiente
- **Dove**: `docs/setup.md:23-27` ("Aggiungere un pacchetto": `conda env update -f environment.yml -n nemesis --prune`); causa a monte in C-002.
- **Prova**: `conda list -n nemesis` → `dash 4.4.1 ... conda-forge`, `flask 3.1.3` installati ma assenti da `environment.yml`; il `--dry-run` di `conda env create -f environment.yml` produce un piano senza `dash`. `--prune` rimuove i pacchetti non presenti nel file (`conda env update --help`). Il comando non è stato eseguito (modificherebbe l'ambiente).
- **Impatto**: seguendo la procedura scritta per aggiungere un pacchetto, l'Embedding Explorer (`embedding_app.py:61`) e i suoi test smettono di funzionare; un ambiente ricreato da zero non li ha mai.
- **Domande**: (a) aggiungo `dash` a `environment.yml` (con versione fissata? `4.4.1`)? (b) togliere `--prune` dal comando (più sicuro) oppure tenerlo dopo la correzione di (a)?
- **Stato (ciclo 20): CHIUSA** — `dash` è ora in `environment.yml` (commit `bba292e`) e `docs/guides/setup.md:29` spiega perché non usare `--prune`.

## C-044 — Bassa — `setup.md:23`: la regola "conda-forge vs pip" non è quella del file
- **Dove**: `setup.md:23` vs `environment.yml`. **Prova**: la sezione `pip:` contiene `nibabel`, `nilearn`, `factor_analyzer`, `pacmap` (tutti su conda-forge); `hdbscan` è in `dependencies` ma l'ambiente locale lo ha da PyPI (`pypi_0`). Nel dry-run il solver installa `hdbscan 0.8.41` da conda-forge e `plotly 7.1.0`, mentre l'ambiente locale ha `hdbscan 0.8.44` e `plotly 6.9.0`: l'ambiente di sviluppo non coincide con quello che `environment.yml` ricreerebbe (nessuna versione fissata).
- **Impatto**: la regola scritta non descrive il file; versioni non fissate, quindi due macchine possono divergere (la suite è verde con le versioni locali).
- **Domanda**: riscrivo la frase ("`pip:` per ciò che si vuole da PyPI") o sposto i quattro pacchetti in `dependencies`? Fissiamo le versioni (`conda env export --from-history` o pin) oppure no?
- **Stato (ciclo 20): CHIUSA** — `docs/guides/setup.md:7` dichiara che le versioni non sono fissate e `:23` spiega la regola conda/pip (`bba292e`).

## C-045 — Bassa — `setup.md:36`: esempi di `scripts/` che non esistono
- **Dove**: `setup.md:36` ("download e organizzazione dataset, utility di setup"). **Prova**: `scripts/` = `archive_local_raw_data.py`, `build_dataset_summary_table.py`. `README.md:35` e `CLAUDE.md:48` usano un'altra descrizione ("cache maintenance, tables, derived indices").
- **Domanda**: allineo `setup.md:35-36` alla descrizione di `CLAUDE.md:48`, o tolgo la sezione "Organizzazione del codice" (è già in `README.md` e `CLAUDE.md`, tre copie)?
- **Stato (29-10-26): CHIUSA** — già sistemata: `setup.md` non ha più la sezione con gli esempi di `scripts/`.

## C-046 — Bassa — `setup.md:29-31`: `nemesis_fallback` non è riproducibile dal repo
- **Dove**: `setup.md:31`, `guides/clustering.md:158-161`. **Prova**: nessun file nel repo crea `nemesis_fallback` (nessun `environment_*.yml`, nessun comando `conda create`); versioni note solo per testo (`dadapy 0.3.4`, numpy 1.26.4, scikit-learn 1.9.1, jax 0.4.30). "oggi" lega il testo a un istante. Il nome "fallback" non spiega il ruolo (è l'ambiente ADP).
- **Impatto**: su una macchina nuova ADP non si può far partire seguendo la documentazione.
- **Domande**: aggiungo un `environment_adp.yml` (o i comandi `conda create`/`pip install dadapy==0.3.4`) alla doc? Rinomino l'ambiente (es. `nemesis_adp`) o resta `nemesis_fallback`? Tolgo "oggi"?

---

## `docs/guides/` — ciclo 10 (`evaluate_dim_reduction_tuning.md`, `fc_matrix_building.md`, `understanding_umap_report.md`)
- **Stato (ciclo 20): CHIUSA** — `docs/guides/setup.md:33-43` dichiara che `nemesis_fallback` non si crea da file e che i comandi sono «ricostruiti… non provati»; l'«oggi» è sparito (`bba292e`).

## C-047 — Bassa — `evaluate_dim_reduction_tuning.md:36`: con `overwrite: false` lo script scrive una parte prima di fermarsi
- **Dove**: `docs/guides/evaluate_dim_reduction_tuning.md:36` ("lo script si ferma se i file della valutazione esistono già"); `src/analysis/tuning_evaluations.py:155-158`.
- **Prova** (copia in scratchpad di `07-10_s1.4-vol`, 6 foglie): tolti i file `hdbscan_*mcs100_ms10*` dalla sola foglia `metric=dice/n_components=2`, rilancio con `overwrite: false` → i file di quella foglia vengono scritti, poi rc=1 alla seconda foglia (già occupata). Il controllo è dentro il ciclo, per foglia. Inoltre `FileExistsError` è un `OSError`: `evaluate_dim_reduction_tuning.py:68` stampa un traceback completo per una condizione attesa.
- **Impatto**: nessuna perdita di dati (non sovrascrive), ma l'output può restare a metà; il comportamento descritto ("si ferma se esistono già") è vero solo se la prima foglia è già occupata. Stessa forma di `lessons_learned.md` #9/#18 (esito parziale).
- **Domanda**: correggo il codice (controllare tutte le foglie prima di scrivere, e non stampare il traceback) o riscrivo la guida ("si ferma alla prima foglia già occupata; le precedenti sono già scritte")?
- **Stato (29-10-26): CHIUSA** — corretto il codice: `_run_plot_hdbscan` controlla i target di tutte le foglie prima della prima scrittura; `evaluate_dim_reduction_tuning.main` non stampa il traceback per `FileExistsError` (condizione attesa). Due test di regressione, verificati falliti col codice vecchio; guida aggiornata.

## C-048 — Media — `fc_matrix_building.md:48`: i controlli sani non "vengono aggiunti con 0 nodi compromessi"
- **Dove**: `docs/guides/fc_matrix_building.md:47-48` (`"group_filter": ["ST","HC"]`: "I sani verranno aggiunti con 0 nodi compromessi"); contro `src/features/functional.py:240-267`, `src/pipeline/mask_fc.py:121-127`, `docs/dev/fc_matrix.md:38`.
- **Prova**: `discover_subject_files` usa solo i soggetti che hanno **sia** FC **sia** maschera di lesione; un sano ha FC ma nessuna maschera ("structurally never has a lesion mask", `fc_matrix.md:38`) → finisce in `missing_lesion` ed è **saltato con un WARNING**. Nessun codice assegna "0 nodi compromessi". Non ho potuto eseguire il caso: le FC dei sani non sono in locale (sono in `features_archive.tar.gz`); la conclusione viene dalla lettura del codice e dal doc di sviluppo, che si contraddicono con la guida.
- **Impatto**: chi mette `["ST","HC"]` per "task comparativi" otterrebbe lo stesso insieme di soggetti di `["ST"]` più un warning; il rimando di `fc_matrix.md:38` a questa guida punta a un testo che dice il contrario.
- **Domande**: (a) confermi che i sani vengono saltati? Allora riscrivo la guida (e `["ST","HC"]` non serve a niente: va sconsigliato o rimosso come opzione?). (b) Oppure vuoi davvero includerli con 0 nodi compromessi (richiederebbe una modifica al codice, non alla doc)?
- **Stato (29-10-26): CHIUSA** — deciso con l'utente: `mask_fc` resta solo sulle lesioni, `build_fc_matrix` deve poter prendere gli HC. Implementato `group` (`ST`/`HC`) in `build_fc_matrix` con `build_fc_matrix_from_raw`; guida, dev, `pipeline_order`, `pipeline_overview`, `pipeline_flow`, `README` aggiornati; 20 test nuovi; voce in `project_changelog.md`. La costruzione reale di una matrice HC non è stata lanciata (le FC dei sani sono nell'archivio).

## C-049 — Bassa — `fc_matrix_building.md:46`: `group_filter` non esiste in `build_fc_matrix.json`
- **Dove**: `docs/guides/fc_matrix_building.md:46` ("In `mask_fc.json` e `build_fc_matrix.json` puoi specificare"). **Prova**: `config/pipelines/build_fc_matrix.json` non ha la chiave; `src/pipeline/build_fc_matrix.py` e `model_config.py` non la leggono (il filtro agisce solo in `mask_fc`; `build_fc_matrix` legge ciò che trova in `masked_fc/<combo>/`). `docs/dev/pipeline_flow.md:41` dice che il ramo FC sceglie i soggetti dal filtro di gruppo.
- **Domanda**: tolgo `build_fc_matrix.json` dalla frase?
- **Stato (29-10-26): CHIUSA** — già sistemata: `fc_matrix_building.md:45` attribuisce `group_filter` a `mask_fc.json` e `group` a `build_fc_matrix.json`.

## C-050 — Bassa — `fc_matrix_building.md:54`: l'imputazione è presentata come già decisa
- **Dove**: `docs/guides/fc_matrix_building.md:54` ("L'imputazione intelligente... avverrà in un passaggio separato appena prima della *Dim Reduction*"); `README.md:74` ("NaN-imputation remains deliberately open, pending an empirical look at the full cohort").
- **Prova**: 0 occorrenze di "imput" in `src/`; `dim_reduction.md`/`pipeline_order.md` non la citano. La guida usa il futuro per un passaggio che non esiste e che il README dichiara aperto. Conseguenza pratica: la matrice FC ha NaN e `README.md:74` la dice "ready for `dim_reduction.py`" senza dire che non la accetterebbe.
- **Domanda**: scrivo al presente "nessuna imputazione: i NaN restano e la scelta è aperta (README)" e annoto che `dim_reduction` non gestisce i NaN? Verifico io cosa fa `dim_reduction` con una matrice con NaN in un ciclo successivo?
- **Stato (29-10-26): CHIUSA** — `fc_matrix_building.md`: al presente, nessuna pipeline imputa i `NaN`, la scelta è aperta (README). Dichiarato che cosa faccia `dim_reduction` con una matrice FC con `NaN` **non è verificato** (nessun controllo sui `NaN` trovato nel codice).

## C-051 — Media — `understanding_umap_report.md:44`: i modi `side` e `nihss` non sono disponibili nei run attuali
- **Dove**: `docs/guides/understanding_umap_report.md:44` ("colorabile per `dataset`/`side`/`volume`/`nihss`"); `src/analysis/understanding_umap_report.py:71,996`; `src/pipeline/dim_reduction.py:12-14`.
- **Prova**: il report offre solo i modi i cui dati stanno in `metadata.csv` del tuning; `dim_reduction.py:14` dichiara "lesion_side/nihss are NOT in metadata at all". Il tuning di esempio della guida (`13-08_s1.1-vol`) ha `metadata.csv` = `subject_id,dataset`; rigenerato il report su copia: il selettore ha solo `none` e `dataset`. L'altro tuning UMAP con lesione (`07-10_s1.4-vol`) ha `dataset` + `lesion_volume_voxels`. Anche `COLOR_BY_MODES`, `_METADATA_COLUMN_BY_MODE` (`lesion_side`, `nihss`) restano per una fonte che nessun run produce più.
- **Impatto**: la guida promette un colore per lato e NIHSS che il report non offre; chi apre l'HTML cerca un selettore che non c'è. Il codice di quei due modi è oggi raggiungibile solo con un `metadata.csv` scritto a mano (cfr. C-023, codice morto).
- **Domande**: riscrivo la guida ("i modi dipendono dalle colonne di `metadata.csv`: oggi `dataset` e, se presente, `volume`")? Il codice di `side`/`nihss` va tolto o tenuto?
- **Stato (29-10-26): CHIUSA** — `understanding_umap_report.md:44` dice che il report offre `dataset` e, se presente, `volume`.

## C-052 — Bassa — Avverbi temporali e futuro nelle guide (regola `CLAUDE.md:53`)
- **Dove**: `evaluate_dim_reduction_tuning.md:3` ("oggi `plot_hdbscan`"); `fc_matrix_building.md:3` ("disponibili attualmente per la coorte WashU"), `:54` ("avverrà" — vedi C-050); `understanding_umap_report.md:16` ("se un giorno esisterà un run t-SNE con `n_components=3`... oggi assente"), `:39` ("oggi `dice`, `euclidean`"); `setup.md:31` ("oggi", C-046).
- **Impatto**: leggero; ogni avverbio lega il testo a un istante e invecchia. `understanding_umap_report.md:39` elenca le metriche del tuning di esempio come se fossero universali.
- **Ciclo 11 (stessa voce)**: `sdc_matrix_building.md:65` ("oggi tutti e 8"), `:104` ("attualmente supportati"); `dim_reduction.md:41` ("oggi disponibili"), `:66` ("analisi correnti"), `:74` e `:76` ("nessuna run precedente all'introduzione di questo campo", "prima dell'introduzione"), `:127-128` ("futuro plot interattivo", "un plot futuro"); `evaluate_clustering_tuning.md:23` ("in stand by... Si riprendono dopo aver chiuso i tre metodi").
- **Ciclo 12 (stessa voce)**: `matrix_building.md:8` ("La produzione attuale"), `:57` ("oggi hanno tutte", "oggi il template a 2mm"), `:77` ("attualmente in uso"); `datasets.md:5` (retrieve "lo faceva... è stata ritirata", vedi C-010), `:67` ("Il dettaglio attuale"), `:90` e `:117` ("non è ancora normalizzato"), `:136` ("verrà calcolato geometricamente": già calcolato, 4401 soggetti); `pipeline_order.md:183` ("tiene quelli dell'ultima run" è invece un fatto presente).
- **Ciclo 13 (stessa voce)**: `exploration.md:53` ("schema non è ancora normalizzato"); `evaluation.md:43` ("Le Parti 1-3 sono ancora quelle della versione unica del notebook, in attesa di riorganizzazione": la stessa frase sta nella cella 1 del notebook).
- **Ciclo 14 (stessa voce)**: `clustering.md:235` ("Da quando `reduction_params_file` esiste, non serve più scriverci a mano l'embedding"); `metadata.md:234` ("oggi le due frazioni…"), `:236` ("il valore in uso"), `:253` e `:255` ("oggi spenta", "Opzione disponibile, spenta"), `:370` ("Oggi ce n'è una"), `:386` ("…al registro oggi"), `:392` ("oggi `UNIPD/WashU/features/`").
- **Ciclo 15 (stessa voce)**: `embedding_app.md:26` («oggi solo `lesion_volume_voxels`»), `:65` («non fa più fallire»), `:216` («il comportamento precedente»), `:433` («solo `volume` oggi»); storia dei notebook in `:168`/`:182` («promossa da…», «già validata in…»).
- **Ciclo 17 (stessa voce)**: `anatomical_maps.md:9` («under today's local data layout»), `:39` («today only SDC's own disconnectome map»), `:43` («la situazione attuale»); `config.md:7` («no longer exist… folded into»), `:9` e `:33` («built *after*… the handoff's original listing order»); `design_patterns.md` nessuno.
- **Domanda**: tolgo gli avverbi (e le frasi ipotetiche sul futuro) tenendo il fatto presente?
- **Aggiornamento (29-10-26): APERTA, parziale** — tolti gli avverbi e le frasi sul futuro in `evaluate_dim_reduction_tuning.md`, `fc_matrix_building.md`, `understanding_umap_report.md` (anche la frase ipotetica sul t-SNE 3D), `sdc_matrix_building.md`, `matrix_building.md`, `dim_reduction.md:41`, `datasets.md:67,136`. Restano i cicli 13-17 (`clustering.md:235`, `metadata.md`, `embedding_app.md`, `anatomical_maps.md`, `config.md`, ecc.) e `dim_reduction.md:66,74,76`: li chiudo con i blocchi su `metadata.md`/`docs/dev`. `embedding_app.md` non toccato (modifiche non committate dell'utente).
- **Aggiornamento 2 (29-10-26): APERTA, parziale** — su decisione dell'utente tolti anche i residui nelle guide: `metadata.md` (`oggi` in 6 punti, «il valore in uso»), `dim_reduction.md:74,76,127` (introduzione del campo, «futuro plot interattivo»), `clustering.md:237`, `evaluate_clustering_tuning.md:24`. **Lasciati di proposito**: `evaluation.md:44` (stato reale del notebook, scelta dell'utente), `dim_reduction.md:66`, «non è ancora normalizzato» (`datasets.md`, `exploration.md`), «in stand by» (`pipeline_overview.md`). Restano `embedding_app.md` (modifiche non committate dell'utente) e i file `docs/dev` (`anatomical_maps.md`, `config.md`): blocco `docs/dev`.
- **Aggiornamento 3 (30-10-26): APERTA, parziale** — tolti gli avverbi temporali e la storia in `embedding_app.md` (`oggi`, «non fa più fallire»), `anatomical_maps.md`, `config.md` e nelle altre guide `docs/dev` toccate dal blocco (`metadata.md`, `models.md`, `plotting.md`, `cluster_description.md`). Restano solo i casi **lasciati di proposito**: `evaluation.md:44`, `dim_reduction.md:66`, «non è ancora normalizzato» (`datasets.md`, `exploration.md`), «in stand by» (`pipeline_overview.md`).
- **Stato (02-11-26): CHIUSA** — i casi rimasti (`evaluation.md:44`, `dim_reduction.md:66`, «non è ancora normalizzato» in `datasets.md` ed `exploration.md`) sono lasciati di proposito dall'utente; «in stand by» di `pipeline_overview.md` riscritto («Fuori dalla catena»).

## C-053 — Bassa — Invocazioni non esatte o ridondanti nelle guide
- **Dove**: `fc_matrix_building.md:36` ("`python -m src.pipeline...`" senza `--config`); `understanding_umap_report.md:30` (`PYTHONPATH=.` con `-m`) e `:22-25`.
- **Prova**: (1) `CLAUDE.md:21-23` chiede "l'invocazione esatta" per ogni pipeline: la guida FC non la dà né per `mask_fc` né per `build_fc_matrix` (i comandi corretti sono in `pipeline_order.md:141`). (2) `python -m src.pipeline.generate_understanding_umap_report --help` funziona dalla radice **senza** `PYTHONPATH` (provato): la variabile è ridondante (conferma A-006; il job la esporta comunque). (3) Il job `run_generate_understanding_umap_report.sh` fissa le due cartelle (`13-08_s1.1-vol`) dentro lo script (righe 14-15), la guida non dice che per un altro tuning va modificato il job.
- **Domanda**: aggiungo i comandi esatti alla guida FC, tolgo `PYTHONPATH=.` e aggiungo la nota sul job?
- **Stato (29-10-26): CHIUSA** — `fc_matrix_building.md`: comandi esatti di `mask_fc` e `build_fc_matrix`; `understanding_umap_report.md`: tolto `PYTHONPATH=.`, aggiunta la nota che le cartelle di tuning stanno in `jobs/run_generate_understanding_umap_report.sh`.

## `docs/guides/` — ciclo 11 (`sdc_matrix_building.md`, `dim_reduction.md`, `evaluate_clustering_tuning.md`)

## C-054 — Bassa — `sdc_matrix_building.md`: tabella dei parametri e una frase del paragrafo introduttivo
- **Dove**: `sdc_matrix_building.md:59-71` (tabella "Comuni a entrambe le modalità"), `:78`, `:7`.
- **Prova** (`build_config.py:343-460`): (1) la modalità sono tre, non due; (2) `output_root` è presentato come "default `data/derived/sdc_matrix`" ma `_require_str(raw, "output_root")` lo rende obbligatorio, senza default; (3) `excluded_subjects_path` è obbligatorio e manca dalla tabella (è citato solo a `:42`); `run_notes` (opzionale) non c'è; (4) `value_column` "(default consigliato)": il campo è obbligatorio per `parcellated`, nessun default; (5) `:7` "Nonostante la famiglia `LF-lesion` è una misura di disconnessione, quindi appartiene alla track `s2.x`" non è una frase corretta (la `lesion`+`streamline` è in `s2.3-stream`/`s2.4-stream`, `docs/experiments/README.md:13,16`).
- **Domanda**: correggo la tabella (tre modalità, campi obbligatori marcati, niente "default" dove non c'è) e riscrivo la frase di `:7`?
- **Stato (29-10-26): CHIUSA** — `sdc_matrix_building.md`: titolo «tutte e tre le modalità», `output_root` e `value_column` obbligatori senza default, aggiunti `excluded_subjects_path` e `run_notes`, riscritta la frase sulla `streamline` (track `s2.3-stream`/`s2.4-stream`).

## C-055 — Media — `dim_reduction.md:118,128`: i metadati non vengono arricchiti con `lesion_side` e `nihss`
- **Dove**: `dim_reduction.md:118` ("`metadata.csv`: L'anagrafica arricchita in automatico di `lesion_volume_voxels`, `lesion_side`, e `nihss`") e `:128` (tuning: "identica per schema a quella di produzione"); `src/pipeline/dim_reduction.py:9-16` (docstring) e `:45-47`.
- **Prova**: il docstring di apertura dice che la pipeline "no longer enriches" i metadati: li passa dall'input; `lesion_volume_voxels` c'è se la matrice la ha, `lesion_side`/`nihss` non sono mai nei metadati (si risolvono al momento del plot dal registro). Sui 40 `metadata.csv` di produzione in `results/`: 33 hanno `subject_id,dataset`, 7 aggiungono `lesion_volume_voxels`. Nei 5 tuning con `embeddings.npz`: `subject_id,dataset` (4) o + volume (1: `07-10_s1.4-vol`). Un docstring stesso si contraddice (`:45-47`: "same enrichment _run_production always applies", dopo aver detto che non arricchisce).
- **Impatto**: stessa radice di C-051: chi si aspetta lato e NIHSS in `metadata.csv` (per rileggerlo senza il registro) non li trova; la frase di `:128` ("senza questo file un plot futuro non saprebbe come colorare") dà una ragione che non vale più.
- **Domanda**: riscrivo `:118` e `:128` ("i metadati dell'input, invariati; lato e NIHSS si leggono dal registro al momento del plot") e correggo il docstring `:45-47` di `dim_reduction.py`?
- **Stato (29-10-26): CHIUSA** — `dim_reduction.md:118,128` e il docstring di `dim_reduction.py` riscritti: `metadata.csv` è quello dell'input, lato e NIHSS si leggono dal registro al plot.

## C-056 — Media — `dim_reduction.md:72`: `viz_n_components: 3` non produce nessun HTML
- **Dove**: `dim_reduction.md:72` ("A `3`, fornisce solo l'HTML interattivo ruotabile") contro `:39` ("non viene scritto nessun PNG/HTML statico"), `:120` ("con `viz_n_components: 3` nessun PNG statico viene scritto... non viene scritto un file `.html` per-run") e `src/analysis/embedding_plots.py:42,56`.
- **Prova**: con 3 colonne `write_embedding_plots` non scrive nessun file; l'esplorazione 3D è solo `embedding_app`. La guida si contraddice al suo interno. Inoltre per `pca`/`pacmap` il raffittamento è impossibile (`reduction.py:205-212`): con `viz_n_components` ≠ `n_components` e rotazione senza ordine la run si ferma, cosa che `:72` non dice.
- **Domanda**: correggo `:72` ("a 3 non si scrive nessun file statico; si guarda con `embedding_app`")?
- **Stato (29-10-26): CHIUSA** — `dim_reduction.md:72`: a `viz_n_components: 3` nessun file statico; descritti anche i casi in cui si ferma.

## C-057 — Bassa — `report.md` salvati non coincidono con il codice attuale dei report
- **Dove**: `results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_m_dice_nc2/report.md` (23-10) contro `clustering_tuning_report.py` + `utils/report_texts/clustering_tuning.md` (non committati).
- **Prova**: rilanciando `evaluate_clustering_tuning` su una copia (overwrite: true, rc=0, 39 s) i 6 CSV sono identici byte per byte, ma `report.md` cambia in 36 righe: "Dendrogramma (ultime 30 fusioni)" → "Dendrogramma"; "sono mostrate solo le ultime 30 fusioni" → "(quante, sta sull'asse orizzontale della figura)". Il resto del file coincide.
- **Impatto**: lieve; i 48 report di agglomerative rigenerati il 23-10 (C-032, `stato_progetto.md:22`) sono già vecchi rispetto al codice di oggi. La guida descrive il comportamento nuovo.
- **Domanda**: è atteso (modifica in corso dei testi)? Quando i testi sono chiusi, rigenero i 48 report e aggiorno i conteggi di C-032?
- **Aggiornamento (29-10-26): APERTA** — su decisione dell'utente la voce resta aperta di proposito: a fine audit si rigenerano i 48 `report.md` insieme agli altri report. La rigenerazione scrive in `results/` e la lancia l'utente. Dopo la rigenerazione vanno aggiornati i conteggi di C-032.
- **Stato (02-11-26): CHIUSA** — i 48 `report.md` sono tutti del 27-10-26 e il codice dei report è committato. Rigenerati su copie nello scratchpad (agglomerative ×2, hdbscan, `hdbscan_soft`): identici al salvato, a parte il percorso. Non rifatti gli altri 44. Nessuna rigenerazione da lanciare.

## `docs/guides/` — ciclo 12 (`matrix_building.md`, `pipeline_order.md`, `datasets.md`)

## C-058 — Media — `matrix_building.md:15-16`: "non esiste una modalità parcellated" è falso
- **Dove**: `docs/guides/matrix_building.md:15-16` (e la tabella `:61-80`); stessa frase in `docs/dev/lesion_matrix.md:9` ("**No parcellation**: voxel-wise is the only output shape"); `pipeline_order.md:125` ("Matrice binaria soggetti × voxel").
- **Prova**: `src/analysis/build_config.py:49-52` richiede `representation` ∈ {`voxelwise`, `parcellated`}; `src/pipeline/build_lesion_matrix.py:6-8,157-180` chiama `build_parcellated_matrix`; il commit `0b55b60` (2026-10-15) la reintroduce; `project_changelog.md:442-446` lo registra e `methods_changelog.md:985` (25-08-26) registrava la rimozione precedente. `build_lesion_matrix.json` contiene `representation: "voxelwise"`: un config scritto seguendo la guida (senza `representation`) viene rifiutato.
- **Impatto**: la guida dice il contrario del codice e manca il campo obbligatorio `representation`, quindi il config "da guida" non parte; mancano anche `run_notes` e i tre campi parcellati (`atlas`, `value_column`, `reference_labels_path`).
- **Domande**: (a) la rappresentazione `parcellated` della lesione è una funzione voluta e mantenuta? Allora riscrivo la nota, la tabella (colonna "solo `voxelwise`/solo `parcellated`") e `dev/lesion_matrix.md:9`. (b) `pipeline_order.md:125` va esteso ("voxel o regioni")?
- **Ciclo 19**: stessa frase in `docs/dev/lesion_matrix.md:9` («No parcellation… is not supported… project decision»). Verificato su codice: `build_lesion_matrix.py` ha `representation: voxelwise|parcellated` e `parcellated_csv.build_parcellated_matrix` legge i csv `LF-lesion` di BCBToolKit (non applica un atlante alle maschere); `lesion.py::build_lesion_matrix()`, la funzione, è davvero solo voxelwise. `sdc_matrix.md:5` e `docs/guides/matrix_building.md` vanno allineati insieme.
- **Stato (29-10-26): CHIUSA** — `matrix_building.md` (nota, `representation`, campi della `parcellated`, `run_notes`), `dev/lesion_matrix.md:9` e `pipeline_order.md` riscritti.

## C-059 — Bassa — `pipeline_order.md:30,71`: `PYTHONPATH` per `populate_metadata` non serve
- **Dove**: `pipeline_order.md:30` ("`populate_metadata` richiede anche `PYTHONPATH="$PROJECT_ROOT"`") e `:71`; chiude A-006.
- **Prova**: `env -u PYTHONPATH python -m src.pipeline.populate_metadata --help` funziona dalla radice; `jobs/run_populate_metadata.sh:24` usa `python -m ... --config` senza `PYTHONPATH`; nessun riferimento nel sorgente. Con `python -m` dalla radice il pacchetto `src` è già importabile (vale per ogni pipeline, come C-053 per `understanding_umap_report`).
- **Ciclo 14**: stesso prefisso in `metadata.md:37`.
- **Domanda**: tolgo la riga `:30` e il prefisso di `:71` (e quello di `metadata.md:37`)?
- **Stato (29-10-26): CHIUSA** — tolto `PYTHONPATH` per `populate_metadata` da `pipeline_order.md` (riga e comando) e `metadata.md`.

## C-060 — Bassa — `pipeline_order.md:83`: "circa 15 minuti" non coincide con i log
- **Dove**: `pipeline_order.md:83`. **Prova**: `logs/compute_lesion_metadata/`: 27 min 43 s (30-09) e 32 min 24 s (07-10) per la coorte intera (il log da 52 s è un'uscita rapida). **Domanda**: scrivo "30 minuti circa" o tolgo il tempo (dipende dalla macchina)?
- **Stato (29-10-26): CHIUSA** — `pipeline_order.md:83`: «circa 30 minuti sull'intera coorte».

## C-061 — Media — `datasets.md:65`: `lesion_volume_voxels_1mm` non è "esattamente" 8 × il volume a 2 mm
- **Dove**: `docs/guides/datasets.md:65` ("`lesion_volume_voxels_1mm` è esattamente `8 x lesion_volume_voxels_2mm`: non aggiunge informazione").
- **Prova**: sulle maschere grezze la proprietà vale (WashU `sub-STUNIPD0002`: 41400 voxel a 1 mm = 8 × 5175 a 2 mm; stesso per UCL-UK `0001` e UKLFR `0170`; allineamento a blocchi (1,1,1) senza blocchi misti). Ma `lesion_metadata.csv` e `participants.csv` sono calcolati con `correct_out_of_brain: true` (`compute_lesion_metadata.json:35`), cioè dopo aver tolto i voxel fuori dal brain di ciascuna griglia: per `0002` il registro riporta 32660 (1 mm) e 4221 (2 mm). Il rapporto 1mm/(8·2mm) ha quantili 5-95% tra 0,98 e 1,01 e vale 1 esattamente nel 22% dei soggetti WashU, 19% UKLFR, 30% NEMESIS_T0, 39% SFB, 81% UCL-UK.
- **Impatto**: la conclusione pratica ("la colonna a 1 mm non aggiunge informazione per i reticoli a 2 mm") regge in sostanza (differenze ≤ 2% per il 90% dei soggetti), la parola "esattamente" no; chi controlla l'uguaglianza la vede fallire. È lo stesso tema di `dev/metadata.md` (colonne a 1 mm).
- **Ciclo 14**: `metadata.md:94` contiene già la formulazione corretta (3501 su 3501 esatti senza voxel fuori dal brain, 1608 che differiscono di pochi voxel; cifre ricalcolate e confermate): basta allinearsi a quel paragrafo.
- **Domanda**: riscrivo "uguale a 8 volte, salvo il diverso azzeramento dei voxel fuori dal brain sulle due griglie (differenza ≤ 2% per il 90% dei soggetti)" e lo allineo a `dev/metadata.md`?
- **Stato (29-10-26): CHIUSA** — `datasets.md:65` allineato a `dev/metadata.md:134` (conteggio grezzo esatto, colonne del csv entro il 2% per il 90% dei soggetti).

## C-062 — Bassa — Imprecisioni minori in `datasets.md` e `pipeline_order.md`
- **Dove**: (1) `datasets.md:169` "Le 5 `manual_masks/` sono complete": i dataset con `manual_masks` sono 8, tutti completi; (2) `pipeline_order.md` non cita 4 pipeline esistenti: `calibrate_lesion_side_threshold`, `generate_understanding_umap_report` (solo nel README), `plot_tuning_embedding_3d`, `replot_dim_reduction`; (3) `datasets.md:63` dichiara il test a blocchi "su tutti e 5853": rieseguito su 3 maschere (coerente), non su tutte; (4) `pipeline_order.md:110` il 30% delle esclusioni per voxel fuori dal brain non è scritto nel config (`build_excluded_subjects.json` elenca solo i soggetti).
- **Domande**: (1) correggo "Le 5" in "Le 8"? (2) le 4 pipeline mancanti vanno nella guida (come passi opzionali) o sono fuori dal flusso? (4) dove è registrata la soglia del 30% (`methods_changelog.md`)? La cito o la tolgo?
- **Stato (29-10-26): CHIUSA** — (1) «Le 8 `manual_masks/`»; (2) nuova sezione «Passi opzionali» in `pipeline_order.md` con le quattro pipeline; (3) tolto «su tutti e 5853» da `datasets.md`; (4) la soglia del 30% è attribuita a `methods_changelog.md` (07-10-26), non al config.

## C-063 — Media — `clustering_comparison.ipynb`: le run d'esempio non esistono (manca il suffisso `mk_`)
- **Dove**: notebook, cella 30 (`SELECTED_RUNS`, 14 run `…/agglomerative/umap/12-10_s1.4-vol_m_dice_nc*_k*_link_ward`) e cella 46 (`WITHIN_MODALITY_RUNS`, `…/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k4_link_average`). La guida (`evaluation.md:30`) dice di scegliere le run a mano in `SELECTED_RUNS`.
- **Prova**: nessuna delle 14 cartelle esiste; esistono tutte con `_mk_euclidean` in coda (es. `12-10_s1.4-vol_m_dice_nc10_k3_link_ward_mk_euclidean`), e la run sdc agglomerative ha `_link_average_mk_cosine`. `runs.csv` e `list_production_runs` riportano già i nomi con `mk_`. Causa: `config/registry/params_clustering.json:15` ha `"mk_"` in `tag_prefix` (commit `ecb1ba9`, "the clustering metric enters the production folder name"). `load_matrix` su una di quelle cartelle: `FileNotFoundError … has no manifest.json` (provato).
- **Impatto**: eseguito dall'alto, il notebook si ferma alla prima cella di caricamento (30) e, se saltata, alla 46. Le altre celle (kmeans, `PAIR_RUN`) puntano a cartelle che esistono.
- **Domanda**: aggiorno i percorsi d'esempio con il suffisso `mk_…` (e lo ripeto nella guida se serve)? Il notebook è tuo: lo lascio a te?
- **Stato (29-10-26): CHIUSA** — su richiesta dell'utente applicato a `clustering_comparison.ipynb`: suffisso `_mk_euclidean` alle 14 run di `SELECTED_RUNS` (cella 30, tutte le cartelle esistono); nella cella 46 la run `sdc_agglomerative_k4` ora termina in `_link_average_mk_cosine` (la cartella reale è `mk_cosine`, non `mk_euclidean` come proposto in chat per errore). JSON del notebook valido; celle non eseguite.

## C-064 — Bassa — Riferimenti al notebook eliminato `clustering_evaluation.ipynb`
- **Dove**: cella 1 di `clustering_comparison.ipynb` ("La valutazione di una run alla volta sta in `clustering_evaluation.ipynb`"; "Le sezioni sono quelle della vecchia versione unica… da riorganizzare"); `docs/dev/cluster_description.md:40,43` ("in section 4 of the notebook", "notebook section 4": la sezione 4 era di quel notebook); `management/project_scaffold_guide.md:340` (lo usa come esempio di nome).
- **Prova**: `clustering_evaluation.ipynb` non è in `notebooks/` (rimosso da `591e078`). Il difetto della cella è già noto: `stato_progetto.md:27`, `project_changelog.md:20`.
- **Impatto**: la guida (`evaluation.md:5`) dice che la valutazione sta nell'app Dash, il notebook e `cluster_description.md` ancora dicono un'altra cosa.
- **Ciclo 18**: anche `docs/dev/pipeline_flow.md:16` elenca `clustering_evaluation` tra i notebook che leggono `participants.csv`.
- **Domanda**: correggo la cella 1 del notebook e le due frasi di `cluster_description.md` (la seconda va riletta quando audito `docs/dev/`), o preferisci farlo tu?
- **Ciclo 20**: confermato in `docs/dev/cluster_description.md:40,43` («in section 4 of the notebook», «notebook section 4»).
- **Aggiornamento (02-11-26)**: fatte `cluster_description.md:40,43` (tolta la «sezione 4 del notebook») e `pipeline_flow.md:16` (`clustering_evaluation` → `clustering_comparison`). **APERTA**: resta la cella 1 di `clustering_comparison.ipynb`; il testo è stato consegnato in chat e il notebook non è modificato. `management/project_scaffold_guide.md:340` è fuori perimetro (nome usato come esempio).
- **Stato (02-11-26): CHIUSA** — su decisione dell'utente i notebook restano così per ora; la cella 1 di `clustering_comparison.ipynb` (rimando a `clustering_evaluation.ipynb`, eliminato) non è corretta. Il testo proposto è nel messaggio del 02-11-26; si riprende notebook per notebook, se e quando l'utente lo chiede.

## C-065 — Media — `evaluation.md:14`: dataset, lato e sede dominante non sono nel pannello "Cluster description"
- **Dove**: `docs/guides/evaluation.md:14` ("Tabelle descrittive per cluster su età, sesso, NIHSS, volume, dataset, lato, sede dominante (nessun test) → app Dash, pannello 'Cluster description'").
- **Prova**: `src/analysis/cluster_description.py:132-139` registra età, sesso, istruzione, NIHSS, volume della lesione. Dataset, lato (`lesion_side`) e sede dominante (`location_dominant_2mm`) stanno in `cluster_composition.py:55-59` (pannello "Cluster composition", `embedding_app.py:3927`), che mostra anche NIHSS e volume. La riga omette inoltre l'istruzione.
- **Impatto**: chi cerca dataset/lato/sede nel pannello "Cluster description" non li trova.
- **Domanda**: riscrivo la riga in due (Cluster description: età, sesso, istruzione, NIHSS, volume; Cluster composition: dataset, lato, sede dominante, NIHSS, volume)?
- **Stato (29-10-26): CHIUSA** — `evaluation.md:14` diviso in «Cluster description» e «Cluster composition».

## C-066 — Bassa — Cache di `thiebaut_2020_replication`: percorso scritto diverso da quello sul disco
- **Dove**: `exploration.md:150` e `docs/dev/covariance_pca.md:54` (`results/pipeline_building/thiebaut_2020_replication/<sessione>/`), cella 5 del notebook (`CACHE_DIR = Path("results/pipeline_building/…")`).
- **Prova**: `results/pipeline_building/` non esiste; la cache è in `results/cache/thiebaut_2020_replication/07-10_s2.4-vol/` (6 file: `pca.npz`, `varimax.npz`, `maps.npz` e tre `*_source.json`). `open_problems.md:193` segnala già la divergenza, ma dice "file piatti, nessuna cartella di sessione": oggi la cartella di sessione c'è.
- **Impatto**: rieseguito, il notebook non trova la cache e ricalcola (non dà errore); la cache esistente non è riusata.
- **Domanda**: sposto la cache in `results/pipeline_building/…` o allineo notebook, `exploration.md` e `covariance_pca.md` a `results/cache/…`? Aggiorno anche `open_problems.md:193`?
- **Ciclo 19**: stessa cartella inesistente in `docs/dev/covariance_pca.md:54` (`results/pipeline_building/thiebaut_2020_replication/<session>/`); i nomi dei file della cache (`pca.npz`, `varimax.npz`, `maps.npz`, `*_source.json`) sono giusti.
- **Stato (ciclo 20): CHIUSA** — cache in `results/cache/thiebaut_2020_replication/<session>/` nel notebook, in `exploration.md:150` e in `covariance_pca.md:54` (`9267f0f`); verificato che i nomi coincidono con il disco.

## C-067 — Bassa — La regola di apertura dei notebook (`exploration.md:211`) non è rispettata da alcuni notebook
- **Dove**: `exploration.md:211` ("la prima cella sotto il titolo dice la domanda, cosa legge, cosa scrive, e cosa non fa").
- **Prova**: cella 1 di `dataset_availability` = un solo rimando a `exploration.md`; `lesion_analysis` elenca i tre assi senza dire cosa legge e scrive; `dim_reduction` e `fc_lesion_masking` non dicono cosa scrivono; `clustering_comparison` non dice cosa legge né cosa scrive (e rimanda a un notebook eliminato, C-064). Controllo fatto sui testi delle celle, non con un criterio automatico.
- **Impatto**: leggero; la regola è in una guida, non in un test.
- **Domanda**: adeguo i notebook, o la regola dice più di quanto vuoi (ammettere un rimando alla guida)?
- **Aggiornamento (02-11-26)**: **APERTA** — testo della prima cella consegnato in chat per `dataset_availability`, `lesion_analysis`, `dim_reduction`, `fc_lesion_masking`, `clustering_comparison`; i notebook non sono modificati (si applica solo dopo «applica»).
- **Stato (02-11-26): CHIUSA** — su decisione dell'utente i notebook restano così per ora; le prime celle di `dataset_availability`, `lesion_analysis`, `dim_reduction`, `fc_lesion_masking` e `clustering_comparison` non rispettano la regola di `exploration.md:211`. Testi proposti nel messaggio del 02-11-26; si riprende notebook per notebook, se e quando l'utente lo chiede.

## C-068 — Media — `evaluation.md:16`: il notebook non calcola Mahalanobis né distanze "linkage" tra cluster
- **Dove**: `docs/guides/evaluation.md:16` ("Distanze tra cluster nello spazio dell'embedding (centroidi, Mahalanobis, linkage) → `clustering_comparison`").
- **Prova**: `grep -i mahalanobis` su `src/`, `notebooks/`, `docs/`: compare solo in `evaluation.md` e in `clustering_literature_survey.md`. Il notebook calcola la distanza euclidea centroide-centroide (Parte 1 §5, Parte 3) e, in Parte 4, la distanza tra centroidi rapportata al raggio. Nessuna distanza tra cluster di tipo "linkage" in `src/analysis/cluster_comparison.py` né in `cluster_pair.py`.
- **Impatto**: la tabella promette due analisi che non esistono.
- **Domanda**: tolgo "Mahalanobis, linkage" (la riga resta con "centroidi, raggio dei cluster") o sono analisi previste che vanno nella riga "non implementato"?
- **Stato (29-10-26): CHIUSA** — `evaluation.md:16`: tolti «Mahalanobis, linkage».

## C-069 — Media — `clustering.md`: nome della cartella, colonne di `runs.csv` e valutazioni del report non coincidono con il codice
- **Dove**: (1) `:254` esempio `31-08_s1.1-vol_m_euclidean_nc2_n_clust5_linkaverage`; (2) `:278` colonne di `runs.csv` per agglomerative «`n_clusters, linkage, timestamp, …`»; (3) `:241` «agglomerative: `cophenetic_correlation`, `dendrogram_jump`, `linkage_agreement`».
- **Prova**: (1) `params_clustering.json`: `tag_prefix` di agglomerative è `["k","link_","mk_"]` e le cartelle reali sono `26-10_s2.4-vol_m_euclidean_nc2_k9_link_average_mk_cosine` (il suffisso `mk_<metrica>` è dal commit `ecb1ba9`); anche i kmeans usano `k<n>` e non `n_clust<n>`. (2) l'intestazione reale di `results/lesion/clustering/production/agglomerative/runs.csv` è `session,reduction_method,reduction_n_components,reduction_metric,n_clusters,linkage,metric,timestamp,…`. (3) `REPORT_EVALUATIONS[agglomerative]` (già in HEAD) richiede anche `largest_cluster_share` e `dunn_index`: un config con `write_report: true` e solo le tre del testo viene rifiutato.
- **Ciclo 18**: il punto (3) è **chiuso** dal commit `ea552f7` (`clustering.md:241` elenca ora cophenetic, salto, linkage_agreement, largest_cluster_share, dunn_index); restano (1) e (2) (`:254`, `:278`).
- **Impatto**: chi cerca una run con il nome dell'esempio non la trova (lo stesso errore delle run d'esempio di `clustering_comparison`, C-063); chi copia la lista di (3) ottiene un `ValueError` al caricamento del config.
- **Domanda**: correggo i tre punti? Per (1) uso un nome reale (`…_k9_link_average_mk_cosine`)?
- **Stato (29-10-26): CHIUSA** — `clustering.md`: nome di cartella e `tag_clustering` d'esempio reali (`…_k4_link_average_mk_euclidean`), colonna `metric` in `runs.csv` di agglomerative.

## C-070 — Bassa — `clustering.md`: omissioni e un alias non accettato
- **Dove**: (1) `:73` `manhattan (l1)`; (2) tabella `:226-243` senza `reduced_data` (obbligatorio) né `viz_embedding_path` (opzionale); (3) `:270-274` elenco degli output di tuning.
- **Prova**: (1) `compute_silhouette_samples('l1')` solleva `ValueError` (accetta `euclidean`, `cosine`, `manhattan`, `dice`, `jaccard`): sklearn accetta `l1`, il progetto no; la griglia del registro usa `manhattan`. (2) `load_clustering_config` richiede `reduced_data` e legge `viz_embedding_path`; sono citati solo dentro altre righe. (3) la cartella reale `results/sdc/clustering/tuning/agglomerative/pca/19-10_s2.4-vol_nc12_varimax` contiene `config.md`, `report.md`, `cophenetic_correlation.csv`, `dendrogram_jump.csv`, `dunn_index.csv`, `largest_cluster_share.csv`, `linkage_agreement.csv`, `k_curves_metric=*.png`, `dendrogram_metric=*.png`: l'elenco ne cita due.
- **Impatto**: leggero.
- **Domanda**: tolgo `l1`, aggiungo le due chiavi alla tabella e rimando a `evaluate_clustering_tuning.md` per i file delle valutazioni?
- **Nota (lavoro in corso)**: il working tree dell'utente toglie `k_range` da `clustering_evaluations.json` e fa del salto del dendrogramma una colonna `jump` di `tuning_results.csv` (niente più `dendrogram_jump.csv`): `clustering.md:39,239,241` ed `evaluate_clustering_tuning.md` andranno riallineati al commit.
- **Aggiornamento (29-10-26): APERTA, parziale** — fatti (1) tolto `l1` e (2) aggiunte `reduced_data` e `viz_embedding_path` alla tabella. Resta (3) l'elenco dei file di output del tuning, da scrivere dopo che l'utente ha committato il lavoro su `k_range`/`jump` (altrimenti descriverei file che stanno per cambiare).
- **Stato (02-11-26): CHIUSA** — (3) `clustering.md`, sezione Fine-Tuning: aggiunti i file delle valutazioni e `report.md`, con rimando a `evaluate_clustering_tuning.md`.

## C-071 — Media — `metadata.md:46`: `--dry-run` non esiste in `populate_metadata`
- **Dove**: `metadata.md:46` («Tutte le pipeline accettano `--dry-run`… Usalo la prima volta dopo aver cambiato un config»); `:31` («Quattro passaggi… Un quarto…»: i comandi sono cinque); `:48` (quattro `sbatch`).
- **Prova**: `python -m src.pipeline.populate_metadata --help` non ha `--dry-run` (solo `--config`); lo hanno `compute_lesion_metadata`, `compute_sdc_metadata`, `enrich_metadata`, `build_excluded_subjects` (stessa cosa già in `pipeline_order.md`, V-065). `jobs/run_populate_metadata.sh` esiste e non è elencato.
- **Impatto**: `populate_metadata --dry-run` termina con un errore di `argparse`.
- **Domanda**: scrivo «le quattro pipeline successive accettano `--dry-run`», riordino il conteggio dei passaggi (cinque) e aggiungo `run_populate_metadata.sh`?
- **Stato (29-10-26): CHIUSA** — `guides/metadata.md`: `--dry-run` solo per le quattro pipeline successive, quinto passaggio, `run_populate_metadata.sh` elencato.

## C-072 — Media — `empty_mask`: colonna del `value` diversa tra guida, notebook e config reale
- **Dove**: `metadata.md:178` (esempio con `value_column: lesion_volume_voxels_1mm`), `exploration.md:127` e cella 55 di `lesion_analysis` (`VALUE_COLUMN_BY_REASON["empty_mask"] = lesion_volume_voxels_1mm`, «0 = vuota davvero») contro `config/pipelines/build_excluded_subjects.json` (`empty_mask` con `lesion_volume_voxels_2mm`).
- **Prova**: il `run_notes` del config spiega la scelta: «`empty_mask`: value dal conteggio sulla griglia di produzione a 2 mm… (maschera vuota in produzione: nulla a 1 mm o lesione persa nel ricampionamento)»; `excluded_subjects.csv` ha valore 0 per le tre righe. Il notebook e l'esempio dicono l'opposto.
- **Impatto**: chi incolla nel config il blocco stampato dal notebook ottiene `value` dal conteggio a 1 mm (vuota davvero), non quello a 2 mm che il config in uso ha scelto; la definizione di `empty_mask` cambia (una lesione persa nel ricampionamento non sarebbe più `empty_mask`).
- **Domanda**: quale è la regola voluta? Allineo notebook, `exploration.md:127` e l'esempio di `metadata.md` al config (2 mm), oppure il config al notebook (1 mm)?
- **Stato (29-10-26): CHIUSA** — documentazione allineata al config (2 mm) in `exploration.md:127` e `guides/metadata.md:178`; su richiesta dell'utente la cella 55 di `lesion_analysis.ipynb` ha ora `"empty_mask": "lesion_volume_voxels_2mm"` con commento «la griglia di produzione: 0 = vuota in produzione». Cella non eseguita.

## C-073 — Bassa — `metadata.md`: esempi e confronti che non coincidono con i file reali
- **Dove**: (1) `:224-230` esempio `lesion_metadata` con 2 `copy_columns`; (2) `:336-340` esempio di `participants_protected.json`; (3) `:302` «`lesion_metadata.config.json` coincide con `config/pipelines/compute_lesion_metadata.json`»; (4) `:115` «`~60 000` oppure `~0,033`»; (5) il `run_notes` di `compute_lesion_metadata.json` (97.4% a 1 mm).
- **Prova**: (1) il config reale copia 10 colonne (2 volumi, `location_dominant_2mm` e le 7 frazioni di sede); (2) il file reale è `{"columns": [], "subjects": []}`, l'esempio sembra il contenuto attuale; (3) il json salvato ha `written` e non ha `output_path`/`overwrite`, e il suo `run_notes` è più vecchio: un confronto letterale fallisce (lo stesso per `sdc`); (4) sono i valori a 1 mm (mediane 60265 e 0,0330; a 2 mm il carico mediano è 7538); (5) ricalcolato: 97,33% a 1 mm contro 97,44% a 2 mm, il testo del config dice 97.4% per entrambe.
- **Impatto**: leggero.
- **Domanda**: segnalo negli esempi che sono illustrativi, elenco le 10 colonne, dico quali chiavi si confrontano (griglie, soglie, atlanti) e specifico la griglia di (4)? Correggo il `run_notes` (5)?
- **Stato (29-10-26): CHIUSA** — `metadata.md`: esempio di `lesion_metadata` segnato come ridotto (10 colonne nel config reale), esempio di `participants_protected.json` segnato come illustrativo, elenco delle chiavi da confrontare tra json salvato e config, valori di (4) riferiti a 1 mm e 2 mm. Su decisione dell'utente corretto il `run_notes` di `config/pipelines/compute_lesion_metadata.json` (97.3% a 1 mm); `assets/metadata/lesion_metadata.config.json` non toccato (registrazione della run).

## C-074 — Media — `embedding_app.md`: le etichette dell'interfaccia citate sono in italiano, l'app è in inglese dal 23-10
- **Dove**: la guida cita come testo dell'interfaccia: «Neutro» (`:143`), «Clicca un punto…» (`:166`, `:198`), «Rumore» (`:190`, `:255`), «Statistica del modello» (`:332`), «Posizione nel cluster» (`:345`), «Appartenenza ai cluster» (`:346`), «Come leggere questi indici» (`:350`), «Valutabile» (`:356`), «Tuning compatibile» (`:387`), «Mappa» (`:389`), «not in registry» (`:253`).
- **Prova**: il commit `790fcc1` (23-10, «App: Embedding Explorer text in English») ha tradotto l'interfaccia e non ha toccato la guida. Nel codice: `Click a point`, `Noise`, `Evaluable`, `How to read…`, `Compatible tuning`, `Map`, `Position in the cluster`, `Membership…`, `Model statistic`, modo neutro `neutral`; «not in registry» non ha riscontro. Restano in inglese e coincidono i nomi dei pannelli (`Cluster description`, `Overlap map per cluster`, …) e dei bottoni `Save HTML`/`Save PNG`.
- **Impatto**: chi cerca nella pagina «Valutabile» o «Mappa» non li trova; le guide `docs/dev/` sono state aggiornate da `790fcc1`, questa no. Il resto del testo è descrittivo e coincide con le funzioni.
- **Ciclo 17**: stesso difetto in `docs/dev/plotting.md:82` («`description` the Italian sentence the app shows above the plot»: le `description` di `COLOR_MODES` sono in inglese, e lo stesso errore sta nel commento del dataclass `ColorMode` in `embedding_coloring.py`); stesso difetto in `docs/dev/anatomical_maps.md:53-54`: “% soggetti disconnessi” e “probabilità media” sono in codice `DISCONNECTION_MAP_MODE_LABELS` = «% of subjects disconnected» / «mean probability» (`embedding_app.py:1460-1463`). Anche `embedding_app.md:208,214` usa i titoli italiani.
- **Domanda**: allineo le etichette citate a quelle inglesi (e dico che l'interfaccia è in inglese)? Per «not in registry» serve vedere cosa mostra la colonna Subjects.
- **Ciclo 20**: `docs/dev/cluster_description.md:14,:96-104` (etichette «Età», «Sesso», «Istruzione», «Volume lesione» contro «Age (years)», «Sex», «Education (years)», «NIHSS», «Lesion volume (voxels)»), `:80` (titolo «soggetti» contro «subjects»), `:148` (etichetta «ATTENZIONE» contro «Warning», `embedding_app.py:1776`), `:174` («The whole app is in Italian»; `_format_number` formatta all'italiana ma l'interfaccia è inglese).
- **Ciclo 25**: la frase «The whole app is in Italian» è ora anche nel docstring di `src/utils/number_format.py` (nuovo file non committato), dove `format_number` prende il posto di `_format_number`; `docs/dev/cluster_description.md:174` la ripete ancora, con il rimando al nuovo percorso. L'interfaccia resta in inglese (`Purity of the…`, `Mean reproducibility…`, `Clusters`), tranne `mediana`/`min`/`max` nella sintesi statistica (`embedding_app.py`, stringhe italiane). Domanda aggiuntiva: la scelta è «numeri all'italiana in un'interfaccia inglese»? In tal caso riscrivo la frase come «numeri in formato italiano» senza dire che l'app è in italiano, e traduco anche `mediana`.
- **Stato (29-10-26): CHIUSA** — allineate le etichette nelle doc; su richiesta dell'utente riscritti i due commenti: `number_format.py` («the interface is in English but the numbers follow the Italian convention») ed `embedding_coloring.py` («English, like the rest of the app's interface»). Resta fuori dalla voce `mediana`/`min`/`max` nella sintesi statistica di `embedding_app.py` (stringhe italiane nel codice): non toccate.

## C-075 — Bassa — `embedding_app.md:168,:182`: due notebook citati non esistono
- **Dove**: `:168` («la stessa logica già validata in `notebooks/post-results_analysis/embeddings_analysis.ipynb` §4») e `:182` («promossa da `…/embedding_to_anatomy_mapping.ipynb` §2»).
- **Prova**: `notebooks/` contiene 12 notebook, nessuno con questi nomi; la sezione *Cosa NON è* e `CLAUDE.md:54` chiedono la forma presente.
- **Domanda**: tolgo i due rimandi (descrivono la storia del codice, non il presente)?
- **Stato (30-10-26): CHIUSA** — tolti i rimandi ai due notebook inesistenti in `embedding_app.md` (`:168`, `:182`) e in `anatomical_maps.md:5`.

## C-076 — Bassa — `embedding_app.md`: cifre e omissioni minori
- **Dove**: (1) `:3`, `:143` elencano sette bottoni (manca `lesion location`, presente in `COLOR_MODES` e al `:18`); (2) `:44` «`~60 000` è un soggetto tipico» è il valore a 1 mm, mentre il default è 2 mm (mediana ~7500, `:61` lo dice); (3) `:49` «massimo/mediana 7,6»: 7,683 → 7,7; (4) `:94` binary_masks «27 KB per soggetto: ~320 MB per tutti i 5845, il doppio per lesione e disconnettoma»: 27 KB × 5845 = 158 MB, e su disco ci sono 23396 file (19 KB in media, 453 MB).
- **Impatto**: leggero.
- **Domanda**: correggo i quattro punti (per (4) dimmi la cifra attesa: per modalità, per soggetto o totale)?
- **Ciclo 20**: stesso «7,6» in `docs/dev/metadata.md:249` (massimo / mediana del carico: 7,683).
- **Stato (30-10-26): CHIUSA** — `embedding_app.md`: `lesion location` aggiunto ai due elenchi di bottoni; `~60 000` detto a 1 mm (a 2 mm `~7 500`); 7,6 → 7,7 anche in `docs/dev/metadata.md`; `binary_masks` misurato: 23.396 file, ~17 KB l'uno, ~390 MB (453 MB su disco). La cifra 19 KB dell'audit era l'uso del disco, non la dimensione dei file.

## C-077 — Bassa — `cluster_drivers.md:33`: la correlazione 0,88 è sui logaritmi e il VIF non è «sopra 8»
- **Dove**: `docs/dev/cluster_drivers.md:33` («Lesion volume and disconnection load correlate 0.88 on the current cohort: using both gives VIF above 8»).
- **Prova**: su `participants.csv` (2 mm): correlazione dei logaritmi 0,881 (5849 soggetti con entrambi > 0); Pearson sui valori grezzi 0,797; Spearman 0,906. Con due soli termini VIF = 1/(1−r²) = 4,47 (2,74 sui grezzi). Un VIF sopra 8 richiederebbe r ≈ 0,94 oppure altri termini correlati nel modello.
- **Impatto**: leggero; il consiglio (tenerne uno solo) regge, la cifra no. Il `cluster_pair` dell'app regredisce con trasformazioni scelte dal chiamante, non è detto che usi i log.
- **Domanda**: scrivo «correlano 0,88 sui logaritmi (0,91 di Spearman): VIF ≈ 4,5 con questi due soli termini» e tolgo «sopra 8»?
- **Stato (30-10-26): CHIUSA** — `cluster_drivers.md:33`: 0,88 sui logaritmi (0,91 di Spearman), VIF ≈ 4,5 con i due soli termini; tolto «sopra 8».

## C-078 — Bassa — `cluster_composition.md:7`: la callback ascolta anche la scheda attiva
- **Dove**: `docs/dev/cluster_composition.md:7` («its callback listens to the run picker only»).
- **Prova**: `embedding_app.py:5112-5116`: `Input("run-picker", "value")` e `Input("selected-page-tab", "data")`; fuori dalla scheda Clustering restituisce `[]` (le schede si costruiscono quando si aprono, `embedding_app.md:114`). Il 7° output di `_update_cluster_picker` e la griglia 440 px sono giusti.
- **Domanda**: aggiorno la frase (due input: run e scheda)? Lo stesso vale probabilmente per gli altri pannelli della scheda (`cluster_description.md`).
- **Stato (30-10-26): CHIUSA** — `cluster_composition.md:7`: la callback ha due input, il selettore di run e la scheda attiva. Gli altri file dei pannelli (`cluster_description.md`, `cluster_drivers.md`, `cluster_comparison.md`) non descrivono i loro input: niente da correggere.

## C-079 — Bassa — `fc_matrix.md`: cartella di output, rimando vuoto e storia nel presente
- **Dove**: (1) `:39` cartella `fc_matrix/<combo>/<date>_<session_name>/`; (2) `:57` «(Phase C above)»; (3) `:13` («Resolved: … an earlier accidental transcription gap … has been closed»), `:33` («an earlier version re-checked only `.index`…»), `:19` («planned: `NAN_IMPUTATION_STRATEGIES`»), `:45` e `:47` («validated … before landing here»).
- **Prova**: (1) `build_fc_matrix.py:118-119`: `effective_session_name = f"{session_name}-{combo}"` → `24-07_s3.1-Yan200TianS2Buckner7N`; (2) nel file non c'è una "Phase C"; (3) `CLAUDE.md:54` chiede la forma presente per `docs/dev/`; `NAN_IMPUTATION_STRATEGIES` non esiste in `src/` (a `:19` è «planned», corretto, ma datato).
- **Domanda**: correggo (1) e (2) e riscrivo (3) come fatti presenti (spostando la storia in `project_changelog.md` se non c'è già)?
- **Stato (30-10-26): CHIUSA** — `fc_matrix.md`: cartella `<date>_<session_name>-<combo>`; tolto «Phase C above»; storia riscritta come fatti presenti (`:13`, `:33`, `:47`), imputazione descritta come passo che non esiste ancora.

## C-080 — Media — `config.md:49`: il report di agglomerative non usa le fasce di Kaufman & Rousseeuw
- **Dove**: `docs/dev/config.md:49` («The pipeline classifies nothing as good or usable with a threshold of ours… the only bands are the silhouette ones of a published convention (Kaufman & Rousseeuw 1990) in the agglomerative `report.md`, labelled as such»).
- **Prova**: `utils/report_texts/clustering_tuning.md:78`: «**Fasce della silhouette**: esistono fasce di lettura (Kaufman & Rousseeuw 1990…); questo report non le usa»; `clustering_tuning_report.py:10`: «The silhouette bands of Kaufman & Rousseeuw are only mentioned (note `silhouette_convention`)». Il testo è del commit `591e078` (27-10) e coerente con la preferenza «niente soglie nostre nei report».
- **Impatto**: la doc dice l'opposto del report: chi la legge cerca fasce che non ci sono.
- **Domanda**: riscrivo «il report non classifica nulla con una soglia: le fasce di Kaufman & Rousseeuw sono solo citate»?
- **Stato (29-10-26): CHIUSA** — `dev/config.md:49`: le fasce di Kaufman & Rousseeuw sono solo citate dal report.

## C-081 — Bassa — `design_patterns.md:50`: elenca `DimReductionClusteringConfig`, che non esiste
- **Dove**: `docs/dev/design_patterns.md:50` («`BuildMatrixConfig`, `DimReductionConfig`, `ClusteringConfig`, `DimReductionClusteringConfig` in `src/analysis/`»). `config.md:7` dice che la classe non esiste più.
- **Prova**: `grep class .*Config` in `build_config.py` e `model_config.py`: nessuna `DimReductionClusteringConfig`; resta citata solo in `docs/debugging/debug_17_08_26.md` (storico, ammesso) e nelle due doc.
- **Domanda**: la sostituisco con `EvaluateClusteringTuningConfig` (o la tolgo)?
- **Stato (30-10-26): CHIUSA** — `design_patterns.md:50`: `DimReductionClusteringConfig` sostituita con `EvaluateClusteringTuningConfig`.

## C-082 — Bassa — `config.md`: tag di esempio obsoleti, storia di processo e una frase in italiano
- **Dove**: (1) `:15` esempio `"tag_prefix": ["n_clust","link"]` → `n_clust4_linkward`; (2) `:7`, `:9`, `:33` (nota «built after… the handoff's original listing order»); (3) `:69` frase in italiano («Una chiave di `extra_columns` che coincide con una colonna di `FIELDNAMES`… solleva `ValueError`») in un file in inglese; (4) `:37` «the 5 regression tests in `test_model_config.py` that pin the validation order».
- **Prova**: (1) i tag reali sono `k3_link_ward_mk_euclidean`, `k6`, `mcs100_ms10_sel_eom` (`load_method_params` sul registro); (2) `CLAUDE.md:54` chiede presente anche in `docs/dev/`; (4) `test_model_config.py` ha 57 test e nessuno cita l'ordine di validazione.
- **Domanda**: aggiorno l'esempio con un tag reale, tolgo (2) e traduco (3), verifico (4) o tolgo il numero?
- **Stato (30-10-26): CHIUSA** — `config.md`: esempio con un tag reale (`k3_link_ward_mk_euclidean`, anche a `:69`), tolta la storia di processo (`:7`, `:9`, `:33`) e il «5 regression tests», tradotta la frase italiana.

## C-083 — Bassa — `anatomical_maps.md`: riferimenti a cose che non esistono, cifre e lingua mista
- **Dove**: (1) `:5`, `:9` notebook `embedding_to_anatomy_mapping.ipynb` (e la sua cella «Configurazione»); (2) `:33` helper `_load_and_binarize` «here»; (3) `:69`, `:86` immagini `tmp/anatomy_rendering/110_…`, `120_…`, `90_…`; (4) `:79` «about 27 KB» per entry; (5) paragrafi in italiano a `:41`, `:43`, `:63`, `:79`.
- **Prova**: (1) il notebook non esiste (C-075); (2) in `anatomical_maps.py` non c'è `_load_and_binarize` (c'è `lesion.py::_load_and_binarize_lesion`; la lettura passa da `_GridResampler.load`); (3) `tmp/anatomy_rendering/` contiene solo `prototype*.py` (`tmp/` è ignorato da git); (4) su disco 453 MB in 23396 file = 19 KB (stesso numero di C-076); (5) il resto del file è in inglese.
- **Impatto**: leggero; le evidenze citate non sono più controllabili.
- **Domanda**: tolgo i rimandi (1)-(3), correggo (4) con la misura e uniformo la lingua?
- **Stato (30-10-26): CHIUSA** — `anatomical_maps.md`: tolti notebook, `_load_and_binarize` e immagini di `tmp/`; «27 KB» → 17 KB (misura, vedi C-076); tradotti i quattro passaggi italiani; «today» tolti.

## C-084 — Bassa — `pipeline_flow.md:105`: non ogni pipeline scrive `summaries/`
- **Dove**: `docs/dev/pipeline_flow.md:105` («Ogni run di pipeline: `logs/<pipeline>/` (log grezzo), `summaries/<pipeline>/` (report)…»).
- **Prova**: `grep summaries src/pipeline/*.py`: lo scrivono `build_excluded_subjects`, `build_fc_matrix`, `build_sdc_matrix`, `calibrate_lesion_side_threshold`, `compute_lesion_metadata`, `compute_sdc_metadata`, `enrich_metadata`, `mask_fc`, `populate_metadata` (9 su 18). Non lo scrivono `build_lesion_matrix`, `clustering`, `dim_reduction`, `evaluate_clustering_tuning`, `evaluate_dim_reduction_tuning` (che hanno `config.md` e log) né `embedding_app`, `generate_understanding_umap_report`, `replot_dim_reduction`, `plot_tuning_embedding_3d`; questi ultimi quattro non scrivono nemmeno `logs/`. `ls summaries/` conferma sette cartelle.
- **Domanda**: scrivo quali pipeline hanno il report (o «le pipeline di metadati e matrici SDC/FC») e dove stanno i parametri delle altre (`config.md`)?
- **Stato (30-10-26): CHIUSA** — `pipeline_flow.md`: `logs/` per tutte tranne 4 pipeline; `summaries/` solo per le 9 pipeline dei metadati e delle matrici SDC/FC.

## C-085 — Bassa — `plotting.md`: lingua mista, storia di processo e `except Exception`
- **Dove**: (1) le sezioni *Naming dei file di plot* (`:60-76`) e *Figure dei notebook* (`:106-118`) sono in italiano dentro un file in inglese; (2) storia e decisioni di sessione nel presente: «a first attempt at this used a percentile… had **zero visible effect**» (`:27`), «(user decision)» (`:13`), «the real 1150-subject cohort» (`:90`), «Alpha was tried much lower first (0.35)» (`:25`); (3) `:96` documenta come voluti i `try/except Exception` + `logging.warning` dei due writer di `embedding_plots.py`.
- **Prova**: `CLAUDE.md:54` chiede il presente per `docs/dev/`; `grep "except Exception" src/analysis/embedding_plots.py`: 5 occorrenze, contro `code_standards.md` §3 («catturare eccezioni specifiche, non generiche»).
- **Domanda**: uniformo la lingua, sposto la storia in `methods_changelog.md` e per (3) decidi se il codice va ristretto (Fase 2) o la regola ammette l'eccezione?
- **Stato (30-10-26): CHIUSA** — `plotting.md`: sezioni *Naming* e *Figure dei notebook* tradotte in inglese; storia di processo tolta (decisioni registrate in `methods_changelog.md`, 30-10-26; la palette a 10 colori era già in `project_changelog.md`); `:96` riscritto sul codice già ristretto (`_EXPECTED_PLOT_ERRORS`, eccezione dichiarata in `code_standards.md` §0).

## C-086 — Bassa — `cluster_comparison.md:101`: rimando al notebook di interpretazione eliminato
- **Dove**: `docs/dev/cluster_comparison.md:101` («The laterality index of the interpretation notebook is not used: it lives in `lesion_metadata.csv`, not in the registry»).
- **Prova**: `cluster_interpretation.ipynb` è stato eliminato il 15-10-26 (`project_changelog.md`); i notebook sono 12 e nessuno è di interpretazione dei cluster.
- **Domanda**: tolgo la frase, tenendo solo «l'indice di lateralità sta in `lesion_metadata.csv`, non nel registro»?
- **Stato (30-10-26): CHIUSA** — `cluster_comparison.md:101`: tolto il rimando al notebook eliminato; resta «l'indice di lateralità sta in `lesion_metadata.csv`, non nel registro».

## C-087 — Bassa — `lesion_matrix.md`: numeri dopo la correzione, un loader descritto male, storia e una frase spezzata
- **Dove**: (1) `:30` «3 masks at 0 voxels on the 2mm grid, 132 at ≤ 10 voxels»; (2) `:127` «`load_build_matrix_config` also parses `MaskFcConfig`/`BuildFcMatrixConfig`»; (3) `:82` («changed from the original… on request»), `:118` («per the handoff note's explicit deferral»), `:135` («Found while testing this script»); (4) `:131` («`main(argv) -> int`, staged `try`/`except` per phase, `logs/…/` written every run) but simpler control flow…» con parentesi che non si apre e confronto senza il termine di paragone).
- **Prova**: (1) `lesion_metadata.csv` (volumi dopo `correct_out_of_brain`): 4 maschere a 0 voxel e 133 a ≤ 10 (la quarta è `sub-STUNIPD0558`, 100% fuori dal brain); 234 e 73 giusti; (2) in `build_config.py` ogni config ha il suo loader (`load_mask_fc_config`, `load_build_fc_matrix_config`, `load_compute_lesion_metadata_config`…); (3) `CLAUDE.md:54` chiede presente anche per `docs/dev/`; (4) leggere il testo.
- **Domanda**: aggiorno (1) a 4/133 (dicendo che i volumi sono dopo la correzione), correggo (2), riscrivo (3) come fatti presenti e sistemo (4)?
- **Stato (30-10-26): CHIUSA** — `lesion_matrix.md`: 4 maschere a 0 voxel e 133 a ≤ 10 (volumi dopo `correct_out_of_brain`); loader veri (`load_mask_fc_config`, `load_build_fc_matrix_config`); storia riscritta al presente; frase di `:131` sistemata (confronto con `mask_fc.py`).

## C-088 — Bassa — `sdc_matrix.md`: esempio di copia locale parziale e storia nel presente
- **Dove**: `:78-83` («con `manual_masks/` con soli 10 soggetti per dataset mentre `bcbtoolkit/` ha la coorte intera… un soggetto "no lesion mask" (es. `sub-STUKLFR0671`) può averla registrata»), `:44` («an earlier draft of this design used "max rows observed"…»), `:141` («validated against `src.features.sdc`'s known sets»).
- **Prova**: le maschere locali sono tutte e 5853 (8 dataset completi, `datasets.md`); `sub-STUKLFR0671` ha una maschera vuota (`empty_mask`, non assente); `KNOWN_OBJECTS` e `KNOWN_VALUE_COLUMNS` sono in `parcellated_csv.py` (importati da `build_config.py`). La regola «la presenza della maschera si risolve dal registro» resta valida.
- **Domanda**: tolgo l'esempio «10 soggetti per dataset» (tenendo la regola) e la storia di `:44`, e correggo il modulo di `:141`?
- **Stato (30-10-26): CHIUSA** — `sdc_matrix.md`: tolto l'esempio «10 soggetti per dataset» (regola mantenuta), la storia di `:44` e corretto il modulo dei set noti (`parcellated_csv.py`, `sdc.py`).

## C-089 — Bassa — `models.md`: cartelle e cifre superate, un file di riferimento inesistente, lingua mista
- **Dove**: (1) `:241` «`reports/<script>/<project>/` + `logs/<script>/<project>/`» contro `:297` «No `summaries/` report for these 2 modeling CLIs»; (2) `:257-293` percorsi `results/<project>/…`; (3) `:293` «A directory of that shape from earlier runs may still sit on disk»; (4) `:198` «Today. Of the 95 agglomerative production runs, 82 have a compatible tuning. 7 have none… and 6 raise»; (5) la sezione `adp.py` (`:215-232`) è in italiano dentro un file in inglese.
- **Prova**: (1) la cartella dei report è `summaries/` (non `reports/`) e `dim_reduction.py` / `clustering.py` non la scrivono (G-290); i log sono in `logs/<script>/<project>/` ✓. (2) il primo segmento è la modalità: `results/lesion/…` e `results/sdc/…`, mentre `<project>` (`clinical_connectome`) compare solo nei log. (3) nessuna `comparison/` sotto `results/*/clustering/production/`. (4) le run agglomerative di produzione sono oggi 156 (29 lesione + 127 sdc); i sei che sollevano (lesione `01-09` / `03-09`, k 4-6) restano, gli altri conteggi non sono più quelli.
- **Domanda**: correggo (1)-(3), tolgo «Today…» o lo rifaccio con `find_compatible_tunings` (serve un'esecuzione), e traduco (5)?
- **Stato (30-10-26): CHIUSA** — `models.md`: `summaries/` e `dim_reduction`/`clustering` che non la scrivono, `results/<modality>/`, tolta la frase sulla cartella `comparison/` rimasta su disco, tolti i conteggi di «Today» (restano le due regole), sezione `adp.py` tradotta.

## C-090 — Bassa — `cluster_description.md`: storia delle richieste e piano futuro dentro una doc al presente
- **Dove**: `:16` («5 of the 7 requested dimensions»), `:26-29` («kept despite low coverage, on request», «originally-requested dimension»), `:184-205` (sezione «Next session» con ordine di lavoro, coverage «on today's registry population»).
- **Prova**: `CLAUDE.md:54` chiede il presente per `docs/dev/`; il tipo di ictus non è nel registro (G-343) e la sezione è un piano, non un fatto.
- **Domanda**: sposto «Next session» in `open_problems.md` (o in un `project_changelog`) e riscrivo `:16` e `:26-29` come fatti presenti (cosa il registro contiene e cosa no)?
- **Stato (30-10-26): CHIUSA** — `cluster_description.md`: «Next session» spostata in `.claude/open_problems.md` (voce «Tipo di ictus…»); `:16` e `:26-29` riscritti come fatti presenti; sezione ora «Registry coverage».

## C-091 — Bassa — `docs/dev/metadata.md`: cifre dopo la correzione, referente mancante e storia nel presente
- **Dove**: (1) `:319` «3 maschere a 0 voxel a 2 mm, 132 con volume ≤ 10»; (2) `:325` «122 soggetti a 10 voxel o meno» tra gli inclusi; (3) `:155` «Quello script ora legge `laterality_index_<grid>`» senza antecedente; (4) `:5` («Il ridisegno è **in vigore**»), `:71` («non esistono più: cancellati»), `:91` («Una sola oggi»), `:241` («scoperta per caso… un primo calcolo esplorativo»).
- **Prova**: (1) e (2) ricalcolati da `lesion_metadata.csv` (volumi dopo `correct_out_of_brain`): 4 a 0 voxel e 133 a ≤ 10; tra gli inclusi (senza le 8 righe `scope = all`) i soggetti a ≤ 10 voxel sono 129. (3) il paragrafo precedente non nomina `calibrate_lesion_side_threshold`. (4) `CLAUDE.md:54`.
- **Domanda**: aggiorno (1)-(2) (stessa correzione di C-087 in `lesion_matrix.md:30`), nomino lo script in (3) e riscrivo (4) come fatti presenti?

- **Stato (30-10-26): CHIUSA** — `docs/dev/metadata.md`: 4 maschere a 0 voxel e 133 a ≤ 10 a 2 mm; tra gli inclusi 129 a ≤ 10 voxel (non 122); `calibrate_lesion_side_threshold` nominato; «in vigore», «una sola oggi», «scoperta per caso» riscritti al presente.

## C-092 — Media — `docs/experiments/`: i quattro metodi spostati in `results/legacy/` sono ancora descritti come presenti in `results/`
- **Dove**: commit `8c9b498` (28-10) ha spostato `spectral`, `kmeans`, `gmm`, `adp` (16 cartelle di metodo, 25 GB) sotto `results/legacy/clustering_spectral_kmeans_gmm_adp_28-10-26/` e ha corretto **solo due file** (`s1.4-vol.md` e `s2.4-stream.md`: link ai report di ADP). Restano riferimenti al vecchio posto in: `s1.1-vol.md:28,42` (tuning di «5 metodi» in `results/lesion/clustering/tuning/`), `s1.2-vol.md:28,49`, `s2.1-schaefer-200-tian-s2.md:35` (e la tabella dei 5 metodi), `s2.2-vol.md:58,77`, `s2.3-stream.md:27` (il link `runs.csv` elenca 8 run su 15: i 7 kmeans sono in `legacy`), `s1.4-vol.md:57,122` (`runs.csv` «di ogni metodo»; «`production/adp` pesa 4.8 GB»), `s2.4-stream.md:34`, `s2.4-vol.md:193,251` («`production/adp` pesa 25 GB»: ora sta in `results/legacy/sdc_s2.4-vol_07-10/clustering/production/adp`), `pipelines.md:256` («k-means, agglomerative, gmm, hdbscan, spectral») e i conteggi di `README.md:10-16` (79, 15, 30, 29, 19), che contano ancora i metodi spostati.
- **Prova**: `ls results/{lesion,sdc}/clustering/{production,tuning}` → solo `agglomerative`, `hdbscan`, `hdbscan_soft`; `du -sh` delle cartelle `adp` in `legacy`: 4,8 GB (lesione), 20 GB (SDC), 25 GB (`sdc_s2.4-vol_07-10`). Le righe di produzione in `results/` sono 75 (s1.4), 8 (s2.3), 13 (s2.4-stream), 25 (s2.4-vol 16-10), contro 79, 15, 19, 29 dichiarate.
- **Impatto**: chi segue un link o conta le run trova meno cartelle di quelle scritte, senza sapere che sono in `legacy/`.
- **Domanda**: aggiungo una nota unica in `docs/experiments/README.md` («le run di spectral, kmeans, gmm e adp stanno in `results/legacy/clustering_spectral_kmeans_gmm_adp_28-10-26/`, stessa struttura di `results/`») e aggiorno i link dove il metodo è citato, oppure preferisci riscrivere i conteggi?
- **Stato (29-10-26): CHIUSA** — nota unica in `docs/experiments/README.md`: le run dei quattro metodi sono in `results/legacy/…`.

## C-093 — Bassa — `runs*.csv` di `results/sdc/`: 39 righe puntano a cartelle spostate in `legacy` (il changelog del 28-10 dice di no)
- **Dove**: `results/sdc/clustering/production/{agglomerative,hdbscan,hdbscan_soft}/runs.csv` (14 + 7 + 5 righe `s2.4-vol`), `…/clustering/tuning/{agglomerative,hdbscan,hdbscan_soft}/runs_tuning.csv` (3 + 3 + 3), `dim_reduction/production/umap/runs.csv` (3) e `dim_reduction/tuning/umap/runs_tuning.csv` (1).
- **Prova**: `os.path.isdir(output)` falso per queste 39 righe; sono le run della matrice `07-10_s2.4-vol` (cartelle in `results/legacy/sdc_s2.4-vol_07-10/`, che non ha nessun `runs*.csv`) più una run del 16-10 mai prodotta (`hdbscan_soft` nc10 100/20 `eom`, dichiarata mancante in `s2.4-vol.md:143`). `project_changelog.md` (28-10) scrive «in `results/` non restano righe con `output` che punta a un percorso inesistente»: vero per i quattro metodi, falso per queste.
- **Impatto**: `lessons_learned.md` #24 (un `output` registrato è creduto valido): qualunque lettore di `runs.csv` conta 39 run che non ci sono (lo script `build_dim_reduction_strategies_csv.py`, che aveva il controllo `_output_dir_exists`, non esiste più in `scripts/`).
- **Domanda**: sposto le 39 righe in un `runs.csv` dentro `results/legacy/sdc_s2.4-vol_07-10/…` (come per i quattro metodi) o le cancello?
- **Stato (02-11-26): CHIUSA** — le 39 righe sono nei log di `results/legacy/sdc_s2.4-vol_07-10/…` (verbatim, `output` invariato; ogni `output` esiste lì); in `results/{lesion,sdc}` nessuna riga ha più un `output` inesistente. Voce in `data_changelog.md`.

## C-094 — Media — `s2.1-schaefer-200-tian-s2.md`: i numeri del tuning sono quelli di s1.1-vol
- **Dove**: `:19-30` (tabella «5 metodi su `euclidean nc2`» e «fascia compatta 0.45-0.50»), `:53` («`nc3` … Non è stato fatto»); di riflesso `s2.2-vol.md:79` («a differenza di s2.1, dove l'ottimo cadeva a k=3-4 in fascia 0.45-0.50»).
- **Prova**: la tabella è identica a `s1.1-vol.md:45-49` (KMeans k=4 0,497; GMM `full` 4 0,496; HDBSCAN 20/10 0,475 rumore 0,083; Spectral `rbf` k=8 0,502; agglomerative k=3 ~0,481, che in s1.1 è il valore di *nc3*). Sul tuning s2.1 vero (`01-09_s2.1-…_nc2`, `tuning_results.csv`): agglomerative `k=2 complete cosine` 0,827 (euclidean: average k=2 0,608, ward 0,621, k=3 0,536 ward/complete, 0,497 average); KMeans k=2 0,619; GMM `n_components=2` spherical/tied 0,622; HDBSCAN (rumore ≤ 0,1) `mcs=15, ms=5` 0,545; Spectral `k=2 rbf` 0,623. L'ottimo cade a k=2, come in s2.2. Inoltre esistono i tuning di clustering su `nc3` (`01-09_s2.1-…_nc3`, 5 metodi) e il `pipelines.md` stesso scrive «nc2/nc3»: la frase «Non è stato fatto» è falsa in parte.
- **Impatto**: la conclusione «a differenza di s2.1» di s2.2 e il confronto tra le due sessioni poggiano su numeri che non sono di s2.1.
- **Domanda**: riscrivo la tabella con i valori di s2.1 (nc2 e nc3), correggo `:13` e `s2.2-vol.md:79`, e tolgo «Non è stato fatto» a `:53`?
- **Stato (ciclo 25, su decisione dell'utente): CHIUSA** — il contenuto di `s2.1-schaefer-200-tian-s2.md` è stato cancellato e sostituito da «Evntualmente da rifare» (il file va rifatto con i valori veri di s2.1). Restano da gestire a parte: `s2.2-vol.md:79` («a differenza di s2.1…») e i rimandi a quel file da `README.md`, `lineage.md`, `pipelines.md` di `docs/experiments/`, che ora puntano a una pagina vuota.
- **Aggiornamento (02-11-26)**: tolta da `s2.2-vol.md` la frase «a differenza di s2.1, dove l'ottimo cadeva a k=3-4»; restano la pagina segnaposto di s2.1 e i rimandi da `README.md`, `lineage.md`, `pipelines.md`.

## C-095 — Bassa — `docs/experiments/`: date, conteggi e un intervallo che non tornano
- **Dove**: (1) `README.md:15` («PCA: tuning, nc30 e nc42, 2 run di clustering») contro `s2.4-vol.md:42-96` e `pipelines.md:92` (nc42, nc30, nc12, nc2; 53 run di clustering sulla PCA); (2) intestazioni «Tuning, **12-10**» in `s1.4-vol.md:61`, `s2.4-vol.md:195`, `s2.4-stream.md:36`, mentre le run di tuning sono del 08-10 (s1.4; ADP 08-10), 09-10 (s2.4-vol, s2.4-stream agglomerative/HDBSCAN) — così anche `pipelines.md:34,130,174`; (3) `s2.2-vol.md:67` «350 combinazioni, 175 per dimensionalità» contro 195 per nc (agglomerative 70 + HDBSCAN 18 + KMeans 7 + GMM 28 + Spectral 72) e 390 in tutto; (4) `s1.4-vol.md:105` «`euclidean` … il rumore è 13-67%»; (5) `s1.4-vol.md:28` («oggi l'indice interno… è il DBCV») e `:120` («che il notebook di tuning non calcola più»).
- **Prova**: (1)(2) `runs.csv`/`runs_tuning.csv` per data; (3) righe di `tuning_results.csv` in `results/` e `legacy/`; (4) sonda HDBSCAN (`mcs=100, ms=10`) sui 90 embedding `euclidean` del tuning 07-10: rumore da 0 a 100%, mediana 27%, 35 celle fuori da 13-67%.
- **Domanda**: correggo (1)-(3) e riscrivo (4) con l'intervallo vero (o «dipende dal riquadro: 0-100%»)? Per (5) `CLAUDE.md:54` copre `docs/experiments/`? Se no, sono accettabili.
- **Stato (02-11-26): CHIUSA** — (1)-(3) corretti in `experiments/README.md`, `s1.4-vol.md`, `s2.4-vol.md`, `s2.4-stream.md`, `s2.2-vol.md` (in `pipelines.md` le date erano già giuste: 12-10 è la data delle produzioni); (4) «dipende dal riquadro (0-100%, mediana 27%)»; (5) accettabili, perché `CLAUDE.md` ora dichiara `docs/experiments/` un registro cronologico.

## C-096 — Bassa — Le silhouette di HDBSCAN e `hdbscan_soft` citate nei file di sessione non stanno più in nessun file della run
- **Dove**: `s1.4-vol.md:25,32-35,74`, `s2.4-vol.md:167-179`, `s2.4-stream.md:23` (e `s1.4-vol.md:23`, «`tuning_results.csv` e `report.md`»).
- **Prova**: dal commit `ea552f7` `tuning_results.csv` dei tuning `hdbscan` e `hdbscan_soft` ha le colonne `noise_fraction, n_clusters_found, largest_cluster_share, dbcv` (e `membership_mean`, `persistence_mean` per il soft): **niente `silhouette`**; i `report.md` hanno solo DBCV. I cinque valori controllati (0,648, 0,654, 0,588, 0,569, 0,377 di `s1.4-vol.md:32-35`) tornano ricalcolando la silhouette sui non-rumore da `clusterings.npz` e dall'embedding di produzione, quindi i numeri sono giusti, ma non verificabili dai file citati.
- **Domanda**: la silhouette di HDBSCAN diventa una valutazione registrata (`clustering_evaluations.json`) o riscrivo le frasi con il DBCV e la quota di rumore?
- **Stato (02-11-26): CHIUSA** — nota di provenienza in `s1.4-vol.md`, `s2.4-vol.md`, `s2.4-stream.md`: la silhouette è ricalcolata sui non-rumore da `clusterings.npz`, non è più in `tuning_results.csv`. Nessuna nuova valutazione registrata.

## C-097 — Bassa — `docs/debugging/`: percorsi, funzioni e test di moduli ritirati citati senza dire che non esistono più
- **Dove**: quasi tutti i report. Moduli ritirati il 05-10 (`src/retrieval/`, `src/sdc/`, `retrieve_data`, `compute_sdc`, `verify_retrieval`, `data_summary`, `config/{file_patterns,retrieval}*.json`, `jobs/run_{retrieve_data,compute_sdc,…}.sh`, `docs/dev/retrieval.md`), il 06-09 (`enrich_lesion_metadata.py`, `src/features/clinical.py`, i tsv per dataset, `data/derived/clinical_metadata/`), il 14-08 (`dim_reduction_clustering.py`), il 18-08 (`docs/notes/`, `docs/methods/`, `docs/dev/analysis.md`, `knowledge/neuroimaging/`, `knowledge/dim_reduction_clustering/` ora sotto `knowledge/notes/`): `debug_09_07_26`, `11_08_26` (11 file di test, 5 file di `src/` e `docs/dev/retrieval.md`), `13_07_26`, `16_07_26`, `21_07_26`, `27_07_26` (cita `group_of` in `src/retrieval/dataset.py`, oggi `src/utils/subject_ids.py`), `28_07_26`, `26_08_26`, `02_09_26`, `17_08_26` (≥ 17 percorsi tra apici e 12 dei suoi 87 link a file, tutti verso `dim_reduction_clustering.py`, `enrich_lesion_metadata.py`, `clinical.py`), `22_08_26`; inoltre `notebooks/fc_lesion_masking.ipynb` (`23_07_26`), `management/notes/TODO.md` (`25_08_26`) e la skill `~/.claude/skills/silent-failure-audit/SKILL.md` (`09_07_26`) non esistono.
- **Prova**: script nello scratchpad (percorsi tra apici inversi → `os.path.exists`; `test_*` e identificatori → `grep` in `src/scripts/tests`). Il solo report che marca ciò che è stato tolto è `debug_21_10_26.md` («Superato, nessun fix in repo», «eliminata»).
- **Impatto**: il lettore non distingue un riferimento sbagliato da un modulo ritirato; molte entry «Seen in» di `lessons_learned.md` rimandano a sezioni il cui codice e il cui test non ci sono più.
- **Domanda**: aggiungo in testa a ciascun report una riga «Moduli ritirati dopo questa data: …» (con rimando a `project_changelog.md`), oppure una sola pagina `docs/debugging/README.md` che elenca per file cosa è stato ritirato?
- **Stato (02-11-26): CHIUSA** — `docs/debugging/README.md`: moduli ritirati con data e commit, e quali report li citano.

## C-098 — Bassa — `docs/debugging/`: fix descritti come presenti che sono stati rimossi, e report senza test di regressione
- **Dove**: (1) `debug_22_08_26.md` §11 (box `.caveats` in `understanding_umap_report`, con `test_generate_report_includes_umap_interpretation_caveats`): rimosso il 28-08 (`fbafb8b` «Remove interpretive-caveats box») e il testo non lo dice; stesso per §6 (Evidence Accumulation, `1e43759`, 21-10), §14 (`evaluate_pca_varimax`, `pca_varimax`) e per i test `test_dim_reduction_fine_tuning_grid_refit_reuses_distance_cache_across_cells`, `test_evaluate_pca_varimax_fits_pca_only_once`, `test_run_clustering_tuning_sweep_evidence_accumulation_reuses_cooccurrence_across_thresholds`, `test_clustering_comparison_*` citati da `17_08_26`, `22_08_26`, `25_08_26`; (2) `debug_09_07_26.md` (7 sezioni) e `debug_13_07_26.md` (5) non citano nessun test di regressione, contro `code_standards.md` §4 e §8. (3) `debug_21_10_26.md`, intestazione: «tutte le sezioni sono corrette tranne la §4, superata», ma anche la §18 dice «Poi **superato**» (commit `ea619d0`, 22-10: `build_silhouette_figure` cambiata, controllo e test spariti) e la §15 è una cancellazione (`load_participants` eliminata).
- **Prova**: `git log -S"caveats" -- src/analysis/understanding_umap_report.py`; `grep -rn "def test_…" tests/` vuoto; `grep` delle etichette «Test» sezione per sezione.
- **Impatto**: §11 descrive come attiva una scelta (avvertire il lettore che le distanze UMAP non si leggono) che il codice ha poi abbandonato; `guides/understanding_umap_report.md` non ne parla.
- **Domanda**: segno §11, §6, §14 come «Superato (rimosso il <data>, <commit>)» sul modello di `debug_21_10_26.md` §4, e per `09_07_26`/`13_07_26` basta una riga «test rimossi con il modulo»?
- **Stato (02-11-26): CHIUSA** — §11, §6, §14 di `debug_22_08_26.md` segnate «Superato (rimosso il <data>, <commit>)»; riga sui test rimossi con il modulo in `debug_09_07_26.md` e `debug_13_07_26.md`; intestazione di `debug_21_10_26.md` aggiornata per §18 e §15.

## C-099 — Bassa — `AUDIT_FINDINGS.md` è il vecchio nome di `debug_17_08_26.md`, citato 41 volte, e il file ha un'intestazione superata
- **Dove**: (1) `AUDIT_FINDINGS.md` è citato in 12 file di `src/` (`build_lesion_matrix.py`, `mask_fc.py`, `build_fc_matrix.py`, `embedding_app.py` ×2, `clustering_tuning.py`, `params.py`, `consensus_clustering.py`, `understanding_umap_report.py`, `subject_discovery.py`, `lesion.py`, `functional.py`), 12 file di `tests/`, `debug_22_08_26.md:3,555`, `debug_25_08_26.md:23` e `lessons_learned.md` #28; il file è `docs/debugging/debug_17_08_26.md` dal commit `b3d1d26`. (2) `debug_17_08_26.md:3-8` dice «Documento di lavoro (non un report di debug concluso)… da spostare/rinominare come report standard a lavoro concluso», mentre sta già in `docs/debugging/`, tutti i 69 finding sono chiusi e il titolo interno resta «Audit findings — 17/08/26». (3) Il finding #1 ha ancora «Stato: Deciso» ma `config/pipelines/clustering.json` ha `session_name: "s2.4-vol"`. (4) «Verificato e corretto», blocco MEDIUM: «18 finding implementati» con 16 numeri elencati; 16 + 4 + 2 + 2 = 24 = #26-#49, quindi 18 è un refuso. (5) `debug_17_08_26` e `debug_22_08_26` non compaiono in nessun «Seen in» di `lessons_learned.md`.
- **Prova**: `git show --stat b3d1d26`; `grep -rl AUDIT_FINDINGS`; `grep -n "Stato:" docs/debugging/debug_17_08_26.md`; `config/pipelines/clustering.json:8`.
- **Impatto**: chi segue un commento di `src/` o di un test cerca un file che non c'è; l'intestazione fa credere il documento ancora aperto.
- **Domanda**: rimpiazzo «`AUDIT_FINDINGS.md`» con «`docs/debugging/debug_17_08_26.md`» nelle 41 occorrenze (è Fase 2: il codice non lo tocco io), riscrivo l'intestazione di `debug_17_08_26.md`, correggo «18» in «16» e aggiorno lo stato di #1?
- **Stato (02-11-26): CHIUSA** — «AUDIT_FINDINGS.md» sostituito con `docs/debugging/debug_17_08_26.md` in 45 punti di 26 file di `src/` e `tests/` (solo commenti e docstring) e in `debug_22_08_26.md`, `debug_25_08_26.md`, `lessons_learned.md` #28; intestazione di `debug_17_08_26.md` riscritta, «18»→«16», stato attuale di #1. Suite: 5754 passed, 17 skipped. Non fatto: (5), aggiungere `debug_17`/`debug_22` ai «Seen in» di `lessons_learned.md` (nessuna domanda posta).

## C-100 — Bassa — `docs/README.md`: «il passato sta solo in `debugging/`», ma `experiments/` è un registro cronologico
- **Dove**: `docs/README.md:60` («È l'unica parte di `docs/` che racconta il passato») e `:73` («Il passato sta in `debugging/`, in `.claude/history/` e in `git log`»), contro `docs/experiments/*.md` (date delle run, «sono state rifatte lo stesso giorno», «ora in `results/legacy/`», «Tuning, 12-10»), `README.md:40` di `experiments/` («cosa è stato provato, cosa si è visto, cosa si è deciso») e `.claude/CLAUDE.md:54` (la regola del presente nomina `docs/guides/`, `docs/dev/` e `README.md`, non `docs/experiments/`).
- **Impatto**: un agente che applica «il passato solo in `debugging/`» a `experiments/` cancella la cronologia che quella cartella esiste per tenere (o, al contrario, non sa se una frase storica lì è un difetto).
- **Domanda**: scrivo in `docs/README.md` e in `CLAUDE.md:54` che `experiments/` è un registro cronologico per sessione, come `debugging/`?
- **Stato (02-11-26): CHIUSA** — `docs/README.md` (due frasi) e `.claude/CLAUDE.md:54`: `debugging/` ed `experiments/` sono registri cronologici per sessione.

## C-101 — Bassa — `pipeline_overview.md`: tre generalizzazioni troppo larghe e avverbi temporali
- **Dove**: (1) `:111` «Stabilità (opzionale, kmeans/gmm/spectral): ripetizione con seed diversi… e sottocampionamento»; (2) `:16` «Lesione e SDC leggono la stessa lista di esclusi, quindi un confronto tra modalità confronta gli stessi soggetti»; (3) `:38` «Il criterio oggi in uso è l'eccesso di voxel fuori dal brain (oltre il 30%)»; (4) `:38` «oggi», `:124` «In stand by… non sono ancora nella catena».
- **Prova**: (1) `STABILITY_ELIGIBLE_METHODS = {"kmeans", "gmm"}` (`clustering_tuning.py:65`) e il blocco `stability` esiste solo per kmeans e gmm in `params_clustering.json`; spectral ha il solo `consensus`; (2) lo scope `sdc-streamline` toglie 14 soggetti alla sola matrice streamline (5831 contro 5845; `lineage.md:44`); le due matrici voxel-wise condividono davvero 5845 righe; (3) `excluded_subjects.csv` ha 3 `empty_mask` (scope `all`) e 14 `all_zero_features` (scope `sdc-streamline`), oltre ai 5 `out_of_brain_fraction_too_high`; (4) `CLAUDE.md:54`.
- **Domanda**: restringo (1) a «kmeans e gmm per le ripetizioni con seed; kmeans, gmm e spectral per il sottocampionamento», aggiungo a (2) «salvo la matrice streamline» e a (3) i due motivi mancanti, e riformulo (4) al presente senza avverbi?
- **Stato (02-11-26): CHIUSA** — `pipeline_overview.md`: stabilità (seed solo kmeans/gmm), coorte «salvo la matrice streamline», motivi di esclusione `empty_mask` e `all_zero_features`, avverbi tolti.

## C-102 — Bassa — `debug_17_08_26.md` e `debug_22_08_26.md`: stato dei finding fermo al giorno del fix, senza nota per ciò che è cambiato dopo
- **Dove**: `debug_17_08_26.md` #1 (`session_name` vuoto), #36 (tag di `spectral`), #47 (`reference_template_path` = maschera di un paziente), #53 (11 combo di atlante, manca `Yan200TianS2Buckner7N`), #32 (`management/notes/TODO.md`), #14 e #35-#37, #57 (Evidence Accumulation, `pca_varimax`); gli identificatori `_update_*_picker`, `metric_options`, `runs_for`, `n_components_options`; `debug_22_08_26.md` §7 (stesso tag di `spectral`).
- **Prova**: `config/pipelines/clustering.json:9` ha `"session_name": "s2.4-vol"`; `params_clustering.json` ha `spectral` con `tag_param` `["n_clusters","affinity"]`, prefissi `["k","aff_"]` (non `n_clust`); `build_lesion_matrix.json` punta a `assets/templates/tpl-MNI152NLin6Asym_res-2_T1w.nii.gz` (`docs/dev/lesion_matrix.md:84` lo conferma); `mask_fc.json` e `build_fc_matrix.json` hanno 12 combo incluso `Yan200TianS2Buckner7N` (`docs/dev/fc_matrix.md:13` dice «Resolved»); `management/notes/` non esiste (`b397c85`); `grep -w` dei nomi dell'app in `src/` vuoto (script `dbg17.py` nello scratchpad). Il solo ritiro dichiarato nel report è #41 (28-08); #36, #47, #53 restano nello stato «documentato, valore non cambiato».
- **Impatto**: chi legge #47 o #53 crede aperti due rischi già chiusi; chi legge #36 cerca un tag `n_clust` che non c'è. Allargamento di C-097/C-098/C-099 (stesso rimedio), non un errore operativo.
- **Domanda**: nelle sezioni #1, #36, #47, #53 di `debug_17_08_26.md` e §7 di `debug_22_08_26.md` aggiungo una riga «Stato attuale (<data>): …» sul modello di #41, oppure basta la nota di apertura proposta in C-097?
- **Stato (02-11-26): CHIUSA** — righe «Stato attuale (02-11-26)» in `debug_17_08_26.md` #1, #36, #47, #53 e `debug_22_08_26.md` §7.

## C-103 — Bassa — `.claude/history/`: «ancora vero oggi» ormai falso, ricette di recupero non eseguibili, una reintroduzione non registrata
- **Dove**: `methods_changelog.md:985-991` (25-08-26: «rimossa la modalità `parcellated`… non esiste un parametro di rappresentazione»; rimanda a `management/notes/TODO.md`), `:893` (28-09-26: «`build_sdc_matrix.json` è ancora su `res-1`»), `:857` e `:829` (29-09-26: `correct_out_of_brain: false`; «oggi il file contiene solo l'intestazione»), `:451` (25 GB di ADP), `:689` («122 a 10 voxel o meno» tra gli inclusi), `:427` (voce 14-10 dopo 13-10); `project_changelog.md:558` («`build_sdc_matrix.json` oggi è streamline»), `:963` («restano sotto `results/lesion/dim_reduction_clustering/`»), `:826` e `:836` (hash `068d2ff`, `facef6f`), `:967` (intestazione `## 2026-08`).
- **Prova**: `build_lesion_matrix.json:20` `"representation": "voxelwise"` (campo obbligatorio dal 15-10-26, `project_changelog.md:494-502`); `build_sdc_matrix.json:19,24` `voxelwise` e `res-2`; `build_lesion_matrix.json:31` `true`; `excluded_subjects.csv` 22 righe; `ls results` → `cache legacy lesion sdc tables`; `git cat-file -t 068d2ff` e `facef6f` → «Not a valid object name» e nessuna riga in `git reflog --all`; `du -sh` di `…legacy/…/sdc/clustering/production/adp` = 20 GB; 122 vale per i 5831 senza alcuna esclusione, 129 per i 5845. Le cifre di dati (massa fuori dal brain 15,3%, 19 min 54 s, 5/0,41/0,30, sede, 88/61/7 run, 67/25/19 produzioni) sono tutte corrette (G-471…G-477).
- **Impatto**: negli archivi il passato è ammesso, ma la frase «ancora vero oggi» promette un fatto presente: chi legge `:985-991` crede che `build_lesion_matrix` non abbia la rappresentazione parcellata (e `methods_changelog.md` non contiene la reintroduzione del 15-10-26, che sta solo in `project_changelog.md`); chi esegue `git checkout -b … 068d2ff` ottiene un errore.
- **Domanda**: (a) cambio «ancora vera oggi» in «vera al <data>» nelle sei occorrenze sopra e aggiungo a `methods_changelog.md` una riga datata 15-10-26 sulla reintroduzione di `representation: parcellated`? (b) le due ricette con `068d2ff` e `facef6f` le segno «non più recuperabile (oggetto non nel repo)»? (c) riordino la voce del 14-10 e porto `## 2026-08` a `## 08-26`?
- **Stato (02-11-26): CHIUSA** — (a) «vera al <data>» nelle occorrenze citate di `methods_changelog.md` (con lo stato di oggi tra parentesi) e nuova voce del 15-10-26 sulla reintroduzione di `representation: parcellated`; in `project_changelog.md` `build_sdc_matrix.json` e la cartella `dim_reduction_clustering/` aggiornati; (b) `068d2ff` e `facef6f` segnati «non più recuperabile»; (c) voce del 14-10 spostata sopra quelle del 13-10, `## 2026-08` → `## 08-26`. Corretto anche 98,4% → 98,5% (1408/1430) in `methods_changelog.md`.

## C-104 — Bassa — `.claude/`: lock di sessione stantio e permessi su un percorso del cluster
- **Dove**: `.claude/scheduled_tasks.lock` (130 byte, JSON: `sessionId` `17b0e196-…`, `pid` 85638, `procStart` «Thu Sep 3 13:44:27 2026»); `.claude/settings.local.json` (due permessi: un `Bash(ls …)` una tantum e `Read(//home/etosato/Projects/NEMESIS_fs/**)`).
- **Prova**: `ps -p 85638` non restituisce processi; il lock risale al 3 settembre, oggi è il 28 ottobre; entrambi i file sono esclusi da git (`.git/info/exclude`, `~/.config/git/ignore`), quindi `git status` non li mostra; `/home/etosato/...` non esiste su questa macchina.
- **Impatto**: nessuno sul codice. Un lock stantio può far credere a uno strumento che una sessione programmata sia ancora attiva; un permesso `Read(//home/etosato/**)` allarga l'accesso in lettura a un percorso che su una macchina con quel home sarebbe valido.
- **Domanda**: cancello `scheduled_tasks.lock` e svuoto `settings.local.json` (restano i permessi che servono davvero)? `CLAUDE.md` non menziona nessuno dei due file.
- **Stato (02-11-26): CHIUSA** — `scheduled_tasks.lock` cancellato (il pid 85638 non esiste); `settings.local.json` con `permissions.allow` vuoto.

## C-105 — Media — `clustering_tuning_guide.md`: la silhouette «interpretabile da sola» e cinque metodi descritti come attivi
- **Dove**: `knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md:30` (tabella dei «3 indici universali»), `:26`, `:67-71`, `:115-157`, `:184-197`, `:222-223` (KMeans, GMM, Spectral, ADP e le stabilità).
- **Prova**: `:30` dice che la silhouette «è l'unico dei tre con un valore assoluto interpretabile da solo»; `evaluation_metrics.md:56-58` dice che le fasce sono «una convenzione, non un test» e che una nuvola senza cluster ha silhouette positiva; `:61` della stessa guida dice che i valori assoluti non si confrontano; la regola del progetto è nessun verdetto con soglie nostre (`methods_changelog.md:78-84`, 21-10-26). Quanto ai metodi: `project_changelog.md:162-168` (23-10-26) mette `kmeans`, `gmm`, `spectral` e `adp` fuori dalla catena `tuning_evaluations → report.md`, `evaluate_clustering_tuning` li rifiuta, e `8c9b498` (28-10-26) ne ha spostato run e tuning in `results/legacy/clustering_spectral_kmeans_gmm_adp_28-10-26/`; la guida non lo dice e le sezioni descrivono `inertia`, `bic`/`aic`, eigengap e plateau come output correnti di uno sweep.
- **Impatto**: chi segue la guida per leggere un tuning di `kmeans` o `spectral` cerca file e colonne che la catena attuale non produce e non può rifare; la frase di `:30` autorizza una lettura «assoluta» della silhouette che il progetto esclude.
- **Domanda**: (a) riscrivo `:30` come «la silhouette è confrontabile solo dentro la stessa run, vedi §2 di `evaluation_metrics.md`»? (b) aggiungo in testa un riquadro «kmeans, gmm, spectral, adp: in stand by dal 23-10-26, run e tuning in `results/legacy/…`» e segno le loro sezioni come descrizione del codice, non della catena?
- **Stato (29-10-26): CHIUSA** — `clustering_tuning_guide.md`: riquadro sui metodi in stand by e riga `:30` riscritta (silhouette confrontabile solo dentro la stessa run).

## C-106 — Bassa — `knowledge/notes/`: fonti elencate e mai citate, un percorso spostato, due cifre non ricostruibili
- **Dove**: `clustering_methods/evaluation_metrics.md` fonti [3] (Bicego 2021) e [11] (Dinh 2025, §4.2); `clustering_methods/hdbscan.md` fonte [3] (Moulavi 2014; il testo cita [6, 7]); `dim_reduction_methods/evaluation.md` fonte [6] (Lee & Verleysen 2009) e «Lee et al. 2015» (`:47`) assente dalla lista; `dim_reduction_methods/pacmap.md` fonte [3] e `umap.md` fonte [10] (de Bodt et al. 2025); `clustering_methods/spectral.md:79` (percorso di `spectral/runs_tuning.csv`); `neuroimaging/lesion_laterality.md:112` (1447 soggetti a 1 mm con PSP); `.claude/open_problems.md:187-188` (cita le attribuzioni a Dinh e Bicego come difetto presente).
- **Prova**: script sulle fonti numerate (`[n]` nel corpo contro l'elenco in «Fonti», nello scratchpad); `ls results/legacy/clustering_spectral_kmeans_gmm_adp_28-10-26/sdc/clustering/tuning/spectral`; `summaries/calibrate_lesion_side_threshold/` (nessun riepilogo a 1 mm con PSP); `methods_changelog.md:750` scrive 98,4% dove 1408/1430 dà 98,5%.
- **Impatto**: le attribuzioni sbagliate che `open_problems.md` segnala per `evaluation_metrics.md` §§1-2 non ci sono più, ma la voce di `open_problems.md` è rimasta e le due fonti restano in lista senza essere citate: chi legge crede che sostengano qualche affermazione. Le altre sono omissioni formali. Il punto di `open_problems.md:193` su `lesion_metrics.md` §3.3 `[5, 7]` è invece solo parziale (Salvalaggio ammette la lesione come maschera, Talozzi no).
- **Domanda**: (a) tolgo da `open_problems.md` la voce su Dinh/Bicego e aggiungo i richiami mancanti nelle note (o tolgo le fonti non usate)? (b) aggiorno `spectral.md:79` al percorso in `legacy`? (c) in `lesion_laterality.md:112` dichiaro che il riepilogo a 1 mm con PSP non è conservato e allineo 98,4%/98,5%?
- **Stato (02-11-26): CHIUSA** — (a) voce Dinh/Bicego tolta da `open_problems.md`; fonti non citate marcate «(non citata nel testo)» in 5 note e «Lee et al. 2015» segnalato come assente dalla lista; (b) `spectral.md` punta al percorso in `legacy`; (c) `lesion_laterality.md` dichiara che il riepilogo a 1 mm con PSP non è conservato.

## C-107 — Bassa — `knowledge/notes/dim_reduction_clustering/`: citazioni alterate e attribuzioni oltre il testo della fonte
- **Dove**: (a) `dim_reduction_tuning_guide.md:77` («more work is needed to validate this clustering approach»); (b) `dim_reduction_literature_survey.md:85` («Optimization… more work is needed to benchmark and study the theoretical properties»); (c) `dim_reduction_tuning_guide.md:17`, `dim_reduction_methods/pca.md:63`, `pca_varimax.md:56` (TdS 2020 avrebbe un criterio «>90%»); (d) `dim_reduction_methods/pca_varimax.md:7,82` (invarianza del sottospazio attribuita a Sorzano §2.2.4); (e) `employed_dim_reduction_methods.md:331` («da 0,39 a 0,98» attribuito al paper); (f) `challenge_of_clustering_after_dim_reduction.md:3` («165+ upvote sulla risposta principale»); (g) `tsne.md:53` e `dim_reduction_tuning_guide.md:68` («Supplementary Figure 1» a perplexity 40, 60, 80).
- **Prova**: de Bodt §3.5: «We believe more work is needed to better understand and validate this clustering approach»; §6.1: «More work is needed to benchmark and to study the theoretical properties of such approaches»; TdS 2020: «30 components, out of 46 in total, explained more than 90% of the variance» (Results) e, nei Methods, «in order to estimate the number of principal components to extract» senza soglia; Sorzano §2.2.4 (solo «possible solutions are rotating the eigenvectors…»); nel testo estratto di TdS non compaiono «0.39» né «0.98» e il supplemento non c'è; nella pagina StackExchange 165 è il punteggio della domanda, la risposta di Schubert ha 201 voti.
- **Impatto**: nessuna cifra operativa è sbagliata, ma tre virgolette non riproducono la fonte e due attribuzioni (la soglia del 90% come «criterio del paper», l'invarianza del sottospazio come contenuto di Sorzano) sono più forti del testo; per la tabella dei Metodi di un paper sono i punti che un revisore controllerebbe.
- **Domanda**: (a, b) riporto le frasi per intero (o le tolgo dalle virgolette)? (c) riscrivo «TdS 2020 tengono 30 componenti su 46, che spiegano più del 90%» invece di «usano una soglia del 90%»? (d) sposto il riferimento di Sorzano alla sola frase che c'è? (e) tolgo l'intervallo 0,39-0,98 o dico da dove viene (figura/supplemento)? (f) scrivo «201 voti la risposta di Schubert»? (g) segno come non verificato il supplemento?
- **Stato (02-11-26): CHIUSA** — (a)(b) frasi riportate per intero (riletto de Bodt §3.5 e §6.1); (c) «30 componenti su 46, più del 90%» in 3 note; (f) risposta di Schubert 201 voti, 165 è la domanda. **(d)(e)(g) corrette diversamente dalla proposta, dopo la rilettura**: Sorzano §2.2.4 dice davvero che sottospazio e ricostruzione restano gli stessi (attribuzione mantenuta, citazione spostata sulla frase che c'è); la cartella di Thiebaut de Schotten 2020 ha `supplementary.pdf` con i valori di riproducibilità per componente (0,393-0,975) e la Supplementary Figure 1 (t-SNE a perplexity 40, 60, 80): intervallo e figura restano, con il rimando al file. La prova dell'audit («supplemento non c'è») era sbagliata.

## C-108 — Bassa — `hdbscan.md` e `hdbscan_package.md`: la pagina di umap-learn non mostra 10 componenti; formula soft da documentazione senza la discrepanza
- **Dove**: `clustering_methods/hdbscan.md:219`; `hdbscan_package.md:81`.
- **Prova**: la pagina salvata (`websites/Using_UMAP_for_Clustering.html`) usa `umap.UMAP(n_neighbors=30, min_dist=0.0, n_components=2)` e scrive che si potrebbe ridurre a 10 dimensioni; `challenge_of_clustering_after_dim_reduction.md:45` lo riporta correttamente. In `hdbscan.md:96` la forma del punteggio di outlier del soft clustering è quella del codice (`exp(−λmax/h)` + softmax), mentre `hdbscan_package.md:81` dà `λmax/(λmax−h)` (documentazione) senza dire che il codice 0.8.44 fa altro.
- **Impatto**: `hdbscan.md` attribuisce all'esempio ufficiale una configurazione (10 componenti) che l'esempio non usa; `hdbscan_package.md` fa ricavare numeri che il codice non produce.
- **Domanda**: (a) correggo `hdbscan.md:219` in «dice che si può scendere a 10 componenti, ma l'esempio usa 2»? (b) aggiungo a `hdbscan_package.md:81` il rimando alla discrepanza descritta in `hdbscan.md:96`?
- **Stato (02-11-26): CHIUSA** — `hdbscan.md` («l'esempio usa 2» componenti); `hdbscan_package.md` rimanda alla discrepanza al §3 di `hdbscan.md`.

## C-109 — Bassa — `dim_reduction_methods/tsne.md`: elenco delle fonti con i numeri 11 e 12 usati due volte
- **Dove**: `tsne.md:136-140` (fonti 11 McInnes, 12 Böhm, poi 11 Torgerson, 12 Gower) e i richiami `[11, 12]` (riga 51), `[11]` (riga 100), `[12]` (riga 119).
- **Prova**: lettura della lista; le prime sei fonti e la 13 sono univoche.
- **Impatto**: `[11, 12]` a riga 51 si legge come McInnes e Böhm, ma intende Torgerson e Gower.
- **Domanda**: rinumero Torgerson e Gower come 14 e 15 e aggiorno `[11, 12]` a riga 51 in `[14, 15]`?
- **Stato (02-11-26): CHIUSA** — Torgerson e Gower rinumerati 14 e 15; richiamo `[14, 15]`.

## C-110 — Bassa — `knowledge/notes/`: un rimando sbagliato e un conteggio che non somma
- **Dove**: `dim_reduction_clustering/employed_dim_reduction_methods.md:25` («84% con Dice sulla matrice grezza, vedi `docs/guides/evaluation.md`»); `neuroimaging/lesion_resampling.md:94-96` (§8) e `template_and_grids.md:144,150` (5150 + 534 + 168).
- **Prova**: la cifra 84% (84,26% ricalcolato su `07-10_s1.4-vol`) è in `docs/guides/embedding_app.md:358` e `docs/dev/models.md:179-180`, non in `docs/guides/evaluation.md`; 5150 + 534 + 168 = 5852, mentre i soggetti con maschera sono 5853 (`sub-STUKLFR0671`, maschera vuota, non classificabile: `docs/guides/datasets.md:59`).
- **Impatto**: chi segue il rimando non trova la cifra; chi somma la tabella trova un soggetto in meno senza spiegazione.
- **Domanda**: (a) sposto il rimando su `embedding_app.md` (o `models.md`)? (b) aggiungo in `lesion_resampling.md` §8 e `template_and_grids.md` §11 una riga «un soggetto con maschera vuota non è classificabile»?
- **Stato (02-11-26): CHIUSA** — rimando dell'84% a `embedding_app.md` e `models.md`; riga sul soggetto con maschera vuota (5150 + 534 + 168 = 5852) in `lesion_resampling.md` §8 e `template_and_grids.md` §12.

## C-111 — Bassa — `knowledge/notes/stroke_literature/`: sintesi senza fonte locale
- **Dove**: `summaries_related.md` («Park et al. (2016)» riga 115; «Jimenez-Marin et al. (2022)» riga 149) e `summaries_core.md` («Cinetto et al. (2026)» riga 120); `knowledge/papers/index.md`.
- **Prova**: `knowledge/papers/stroke_related/` contiene solo Filatova, Keator, Wang e Zhou (4 cartelle, come l'indice), quindi Park e Jimenez-Marin non hanno fonte; `stroke_core/Cinetto et al - 2026/` ha solo `Manuscript.docx` (non nell'indice, G-502; il testo è leggibile con `zipfile` e la sintesi torna, G-536); Tshimanga 2025 è nell'indice (con 7 file estratti) ma non ha una sintesi.
- **Impatto**: i numeri di queste tre sintesi (24 per Cinetto) non sono verificabili sul repo; le altre 22 sezioni con una fonte locale tornano (G-532).
- **Domanda**: (a) aggiungo al repo (o all'indice) le tre fonti, o segno le sintesi come «da fonte non presente»? (b) scrivo la sintesi di Tshimanga 2025 o tolgo la voce dall'indice dei paper con sintesi?
- **Stato (02-11-26): CHIUSA** — Park 2016 e Jimenez-Marin 2022 marcate «da fonte non presente»; Cinetto 2026 aggiunta a `knowledge/papers/index.md` (solo `Manuscript.docx`) e nota nella sintesi; Tshimanga 2025 segnata «senza sintesi» nell'indice.

## C-112 — Bassa — `scope_by_category.md`: Thiebaut de Schotten 2020 non dice che le lesioni «seguono i vasi sanguigni»
- **Dove**: `knowledge/notes/stroke_literature/scope_by_category.md:7` (riga A, primo paper).
- **Prova**: nel testo estratto di Thiebaut de Schotten et al. 2020 le stringhe `vessel`, `vascular`, `arter` non compaiono (0 occorrenze); il paper scrive «The biased distribution of ischaemic stroke» e «strokes also seem to have a concentric distribution with a progressively increasing probability of damage from the surface of the brain to the deep white matter»; `summaries_core.md:480` lo riporta correttamente («distribuzione concentrica… dalla superficie alla materia bianca profonda»).
- **Impatto**: `scope_by_category.md` e `summaries_core.md` si contraddicono sullo stesso paper; la frase sui vasi attribuisce a un paper di disconnessione un'affermazione di anatomia vascolare che è un altro tema (quello di Bisogno 2025).
- **Domanda**: riscrivo la riga in «dimostra che le lesioni da ictus non sono distribuite a caso (concentriche, dalla superficie alla sostanza bianca profonda)»?
- **Stato (02-11-26): CHIUSA** — `scope_by_category.md:7` riscritta (distribuzione concentrica, non aleatoria).

## C-113 — Bassa — `stroke_literature/summaries_*.md`: cinque affermazioni non trovate nelle fonti locali
- **Dove**: (a) `summaries_core.md:92` (Pini: «ischemico o emorragico»); (b) `summaries_core.md:613` (Griffis 2019: «fattore ~2.5 (R²=0.10→0.25)») e `neuroimaging/disconnectome_bcbtoolkit.md:123` (stessa cifra); (c) `summaries_core.md:135` (Cinetto: «68 controlli sani abbinati»); (d) `summaries_related.md:25` (Keator: omette il giro precentrale, z = 3,09, associato a comprensione più alta, e la sede e gli z dell'opercolo rolandico non sono verificabili); (e) `summaries_core.md:26` (Zanola: il paper attribuisce il test H = 74,3 alle «motor abilities»).
- **Prova**: (a) il testo di Pini dice «first-time stroke patients», i criteri sono in «Supplementary Material S1.1» non estratto; (b) il testo di Griffis 2019 dà solo «F 1,110 = 22.6, p < 0.001» per il confronto tra i modelli: R² 0,10 e 0,25 non compaiono (forse nella Fig. 2B); (c) nel `Manuscript.docx` di Cinetto compare «a supplementary sample of healthy participants» senza numero; (d) il testo di Keator ha «precentral gyrus … higher speech comprehension scores (z = 3.09)»; (e) Zanola scrive «motor abilities at 90 days» dopo aver parlato della mRS.
- **Impatto**: nessuna cifra operativa; sono dettagli che una verifica sul paper non conferma (a, b, c, d) o che la sintesi risolve in silenzio (e).
- **Domanda**: (a) tolgo «o emorragico» o lo cito dal supplemento? (b) cito la figura (o tolgo i due R²) sia in `summaries_core.md` sia in `disconnectome_bcbtoolkit.md`? (c) tolgo «68» o indico la fonte? (d) aggiungo il risultato sul precentrale? (e) nota «il paper scrive “motor abilities”, ma il test è sulla mRS»?
- **Stato (02-11-26): CHIUSA** — (a) «o emorragico» tolto; (b) R² tolti in `summaries_core.md` e `disconnectome_bcbtoolkit.md` (restano il fattore 2,5, che il testo dà, e l'F); (c) «68» tolto; (d) aggiunto il precentrale (z = 3,09): gli z dell'opercolo rolandico sono nel paper e restano; (e) nota «motor abilities» contro mRS.

## C-114 — Bassa — `embedding_app.md:338`: la cofenetica è «(0-1)», l'interfaccia dice da -1 a 1
- **Dove**: `docs/guides/embedding_app.md:338` (riga `agglomerative` della tabella «Statistica del modello»).
- **Prova**: il lavoro non committato su `embedding_app.py` ha sostituito la nota unica con due frasi: «Cophenetic correlation: … From -1 to 1: the higher, the better…»; la correlazione cofenetica è una correlazione di Pearson (`evaluation_metrics.md:120`: «da -1 a 1»), e la guida scrive «correlazione (0-1)».
- **Impatto**: la guida e l'interfaccia danno due intervalli diversi per lo stesso numero.
- **Domanda**: scrivo «da -1 a 1» anche nella guida?
- **Stato (02-11-26): CHIUSA** — già corretto: `embedding_app.md:336` dice «correlazione (da -1 a 1)» per la cofenetica.

