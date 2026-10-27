# 02 — Contraddizioni e problemi aperti (richiedono una decisione dell'utente)

Severità: **Alta** (la doc induce a un errore operativo) · **Media** (affermazione falsa/obsoleta con effetto pratico) · **Bassa** (imprecisione, omissione, stile).
Nessuna correzione è stata applicata: ogni voce attende una decisione.

Aperti: 57 · Alta: 0 · Media: 24 · Bassa: 33

---

## C-001 — Media — Doc vs Doc: dove vivono le note delle riunioni
- **Dove**: `.claude/CLAUDE.md:33` ("raw meeting notes, which live under `assets/`") vs `CLAUDE.md:41`, `README.md:50`.
- **Prova**: `ls assets` → `atlases metadata templates`; `ls management/meetings` → `01_Kick-off.md`, `02_Seba.md`, ...
- **Impatto**: un agente cerca le riunioni nel posto sbagliato.
- **Domanda**: correggo `CLAUDE.md:33` in "`management/meetings/`"?

## C-002 — Media — Doc vs Config: `environment.yml` incompleto e lista dei pacchetti incompleta
- **Dove**: `CLAUDE.md:11`; `environment.yml`; `src/analysis/embedding_app.py` (`from dash import ...`); `docs/setup.md:31`.
- **Prova**: `environment.yml` non elenca `dash`; l'ambiente locale `nemesis` ha `dash 4.4.1` (installato fuori dal file). `docs/setup.md:31` dà per scontato che `dash` stia in `nemesis`. La lista di `CLAUDE.md:11` omette `hdbscan, plotly, openpyxl, pytest, pytest-cov, hypothesis, factor_analyzer, pacmap` e `python=3.11`.
- **Impatto**: un ambiente ricreato da `environment.yml` non fa partire l'Embedding Explorer; la lista in `CLAUDE.md` è una seconda fonte che diverge (`code_standards.md` §5: un valore, un posto).
- **Domande**: (a) aggiungo `dash` (con quale versione: `4.4.1`?) a `environment.yml`? (b) in `CLAUDE.md:11` sostituisco la lista con "vedi `environment.yml`"?

## C-003 — Media — Doc vs Git: cosa è davvero ignorato da git
- **Dove**: `CLAUDE.md:17` e `README.md:62` ("`*.nii`, `*.nii.gz`, gitignored"); `README.md:58` ("`summaries/`, `logs/` (gitignored)"); `.gitignore`.
- **Prova**: `.gitignore` contiene `data/*`, `results/`, `tmp/`... ma nessun `*.nii*`, `logs/`, `summaries/`. `git ls-files | grep nii.gz` → 22 file tracciati (atlanti e template in `assets/`, voluti). `git ls-files logs summaries | wc -l` → **843** file tracciati (ultimo commit: "logs"). `.gitignore` ha anche `.claude/dim_reduction_clustering/*`, cartella che non esiste.
- **Storia (da `branch_alignment.md:40`, `git log`)**: `.gitignore` ignorava `logs/` e `summaries/` dal 2026-08-31 (`d0ecbbf`); il commit `f577b6a` del 2026-10-23 ("logs") ha tolto quelle regole e aggiunto 813 file (+27402 righe). Anche `branch_alignment.md:40` dice "gitignored... non sono nemmeno tracciati": falso dal 23-10.
- **Impatto**: la regola reale è "`data/` è ignorata", non "i nifti sono ignorati": un `.nii.gz` messo fuori da `data/` finirebbe in git. `logs/` e `summaries/` sono invece versionati, contro quanto scrive il README.
- **Domande**: (a) `logs/` e `summaries/` versionati sono una scelta voluta del 23-10? Se sì correggo `README.md:58` e `branch_alignment.md:40` (e annoto il rischio: con due checkout che scrivono log, i conflitti di rebase aumentano); altrimenti riaggiungo le regole a `.gitignore` e li tolgo dall'indice. (b) correggo `CLAUDE.md:17` in "sotto `data/`, gitignored"? (c) tolgo la riga morta di `.gitignore`?

## C-004 — Media — Doc vs Doc: descrizioni obsolete delle guide metadata
- **Dove**: `CLAUDE.md:36` ("`metadata.md` (06-09-26, the 3 metadata layers...)"), `CLAUDE.md:35` (`metadata.md` = `enrich_metadata.py`; `evaluate_clustering_tuning.md` = cofenetica/salto/quota) vs `docs/dev/metadata.md:37` ("Quattro file, cinque domande"), `stato_progetto.md:9` ("cinque file in `assets/metadata/`"), `README.md:84-99`.
- **Prova** (anche `stato_progetto.md:9`, "cinque file... ognuno scritto da una pipeline"): `assets/metadata/` contiene 4 CSV (`participants`, `lesion_metadata`, `sdc_metadata`, `excluded_subjects`) + `participants_protected.json` + 2 `*.config.json`; le pipeline sono 5. Le tre fonti usano conteggi diversi ("3 livelli", "quattro file", "cinque file").
- **Impatto**: chi legge non sa quanti file/livelli esistano.
- **Domande**: qual è il conteggio canonico? Riscrivo le descrizioni di `CLAUDE.md:35-36` senza numeri né date (es. "i file in `assets/metadata/` e come si relazionano")?

## C-005 — Bassa — Omissione: `docs/dev/covariance_pca.md` non è nell'elenco di `CLAUDE.md`
- **Dove**: `CLAUDE.md:36`. **Prova**: il file esiste (129 righe) ed è citato da `stato_progetto.md:7`.
- **Domanda**: lo aggiungo all'elenco (o l'elenco diventa "vedi `docs/dev/`")?

## C-006 — Media — Doc vs Codice/Stato: la sezione "Confronto" non è montata
- **Dove**: `CLAUDE.md:36` e `docs/dev/cluster_comparison.md:3` (la presentano come parte di `embedding_app.py`) vs `stato_progetto.md:42` ("rimossa dall'app e parcheggiata").
- **Prova**: in `src/analysis/embedding_app.py`, `comparison_content_for` (:3206) e `cluster_pair_content_for` (:3450) hanno solo la definizione, nessun chiamante in `src/`. Contraddice `code_standards.md` §2 ("niente codice morto") salvo l'eccezione dichiarata in `stato_progetto.md:42`.
- **Domanda**: riscrivo `CLAUDE.md:36` e `dev/cluster_comparison.md:3` dicendo "non montata (parcheggiata)"? L'eccezione al §2 va scritta anche in `code_standards.md`?

## C-007 — Bassa — Doc vs Repo: job SLURM mancanti
- **Dove**: `CLAUDE.md:29`. **Prova**: nessun `jobs/run_embedding_app.sh` (`src/pipeline/embedding_app.py`, server Dash interattivo) né `jobs/run_archive_local_raw_data.sh` (`scripts/archive_local_raw_data.py`, comprime i dati locali).
- **Domanda**: sono eccezioni legittime (aggiungo la clausola alla regola) o servono i job?

## C-008 — Bassa — Affermazione troppo generale
- **Dove**: `CLAUDE.md:21` ("every guide under `docs/guides/` documents both"). **Prova**: `datasets.md` ed `evaluation.md` non citano `sbatch`; non descrivono una pipeline.
- **Domanda**: restringo la frase a "ogni guida di una pipeline"? (La verifica guida per guida avverrà con `docs/guides/`.)

## C-009 — Bassa — Date non coerenti con git
- **Dove**: `CLAUDE.md:35` (`dim_reduction_clustering.md` ritirata il 14-08-26; `project_changelog.md:816` dice 14-08-26) e `CLAUDE.md:37` (merge `docs/dr-clustering-literature-migration` il 18-08-26).
- **Prova**: commit `2991ec1` (rimozione) = 2026-08-15 11:54; merge `f9e2d30` = 2026-08-21; `project_changelog.md` non cita il merge. Il commit `2ed3dcb` che ritira gli atlanti ha il messaggio "Extend build_lesion_matrix to UCL-UK, remove parcellate feature" (non cita il ritiro di `build_combined_atlas`).
- **Domanda**: tengo le date del changelog (data del lavoro) o allineo a git? Tolgo le date da `CLAUDE.md` (regola "presente, non passato")?

## C-010 — Media — Regola `CLAUDE.md:53` violata dai file che governa (verifica preliminare)
- **Dove**: `README.md:66-72` (sezione "Retired pipelines"), `docs/guides/datasets.md:5` ("lo faceva in automatico: è stata ritirata"), `docs/dev/metadata.md:71` ("non esistono più: cancellati... è stato spostato"), `docs/dev/metadata.md:103` ("prima della separazione le metriche erano sparse"). Inoltre `docs/dev/models.md:76` cita "(project-clustering-tuning-redesign memory)", una memoria privata dell'agente, non un file del repo.
- **Prova**: grep mirato su `docs/guides`, `docs/dev`, `README.md`; da confermare file per file nell'audit di ciascuno.
- **Domanda**: la regola ammette eccezioni (es. una sezione "Retired" nel README) oppure si tolgono questi passaggi (e il riferimento alla memoria)?

## C-011 — Bassa — Perimetro di `code_standards.md`
- **Dove**: `CLAUDE.md:70` ("`src/` (and its tests)") vs `code_standards.md:3` ("`src/`, `scripts/` (e i relativi test)").
- **Domanda**: allineo `CLAUDE.md:70` aggiungendo `scripts/`?

## C-012 — Bassa — `.claude/audit/` non è nella struttura di `CLAUDE.md`
- **Dove**: `CLAUDE.md:31-49` non cita `.claude/audit/`; `.claude/skills/` e `.claude/settings.local.json` non sono documentati né in `CLAUDE.md` né nel perimetro dell'audit.
- **Domanda**: a fine audit documento `.claude/audit/`? `skills/` e `settings.local.json` entrano nell'audit (li ho messi in `00_master_plan.md` §1.1c)?

## C-013 — Bassa — Percorsi dell'ambiente hardcoded nei job (da rivedere in Fase 2)
- **Dove**: `jobs/run_*.sh` (es. `jobs/run_build_lesion_matrix.sh:7,11,17`: `/home/etosato/Projects/NEMESIS_fs`, `/home/etosato/miniconda3/...`).
- **Prova**: il job "di riferimento" di `CLAUDE.md:24` contiene percorsi assoluti dell'utente sul cluster, contro `code_standards.md` §5 ("nessun valore ambiente-dipendente hardcoded").
- **Domanda**: accettabile per script SLURM (specifici del cluster) o vanno parametrizzati? Da decidere prima della Fase 2 sui `jobs/`.

---

## `stato_progetto.md`

## C-014 — Media — Doc vs Git: HEAD e working tree obsoleti
- **Dove**: `stato_progetto.md:34` ("HEAD `790fcc1`... working tree contiene lavoro non committato dell'utente: `anatomical_maps.py`, `cluster_overview.py`, `dendrogram_splits.py`, `tuning_match.py`...").
- **Prova**: `git log -1` → `f577b6a logs`; `790fcc1` è 16 commit indietro; `git status` a inizio sessione: pulito. Ora risulta modificato solo `.claude/history/project_changelog.md` (+17 righe), che non ho toccato.
- **Impatto**: la regola "committare solo i propri file" descrive uno stato che non c'è più; un HEAD scritto a mano invecchia a ogni commit.
- **Domanda**: tolgo HEAD e l'elenco dei file non committati dalla riga (lo stato git si legge con `git`)? Il `project_changelog.md` modificato è una tua modifica in corso?

## C-015 — Media — Thread aperto già chiuso: omogeneità/completezza nel notebook di confronto
- **Dove**: `stato_progetto.md:26`; `lessons_learned.md` #41 ("Il notebook non è ancora corretto").
- **Prova**: in `clustering_comparison.ipynb` nessuna cella chiama `homogeneity_score`/`completeness_score`; la cella 60 usa `agreement_metrics(labels_a, labels_b)`, che chiama `homogeneity_score(labels_b, labels_a)` (`src/analysis/cluster_comparison.py:170-171`). La cella 59 descrive homogeneity come "ogni cluster di A contiene soggetti di un solo cluster di B": coincide con quel codice (A = predetto, B = vero).
- **Impatto**: tolgo lavoro già fatto dalla lista dei thread aperti; la lesson #41 è parzialmente falsa.
- **Domanda**: confermi che è risolto? Se sì, rimuovo la riga da `stato_progetto.md` e correggo l'ultima frase di #41 quando audito `lessons_learned.md`.

## C-016 — Bassa — Elenco di `docs/dev/` incompleto
- **Dove**: `stato_progetto.md:7`. **Prova**: mancano `anatomical_maps`, `cluster_comparison`, `cluster_composition`, `cluster_description`, `cluster_drivers`, `pipeline_flow` (tutti esistono). Stessa omissione di C-005.
- **Domanda**: sostituisco l'elenco con "vedi `docs/dev/`"?

## C-017 — Media — Contraddizioni interne a `stato_progetto.md` sulle metriche di agglomerative
- **Dove**: `:15` (Dunn e quota del cluster più grande già valutazioni del registro; CH e DB vuoti con metrica non euclidea "ovunque") vs `:37` ("per Dunn, CH e DB nel notebook e nella produzione di agglomerative resta da fare") vs `:50 (3)` ("decidere le metriche di agglomerative ancora fuori dal registro (Dunn, quota del cluster più grande, silhouette per cluster)").
- **Prova**: anche `open_problems.md:110` dice che `dunn_index` e `largest_cluster_share` sono nel registro, mentre `open_problems.md:132` dice che `largest_cluster_share` e `n_small_clusters` "non sono calcolati per agglomerative". `config/registry/clustering_evaluations.json` contiene già `largest_cluster_share` e `dunn_index`; `clustering_tuning_report.py:59,65` le usa.
- **Impatto**: il "prossimo passo" (3) chiede di decidere ciò che è già deciso e implementato; "ovunque" (L15) contraddice "resta da fare" (L37).
- **Domande**: (a) del punto (3) resta solo la silhouette per cluster? (b) la regola euclidea è già applicata nel notebook e in produzione, oppure no?

## C-018 — Bassa — Riferimenti non riproducibili alla run mancante
- **Dove**: `stato_progetto.md:21` ("29 run su 30, manca `hdbscan_soft` nc10 `mcs=100`, `ms=20`, `eom` sulla matrice del 16-10").
- **Prova**: `results/sdc/clustering/production/hdbscan_soft/pca/` contiene `19-10_s2.4-vol_nc{2,12,30}_mcs.._ms.._sel_..` (20 cartelle); nessun `nc10`; la matrice è "16-10" ma i nomi riportano il 19-10 (data dell'embedding PCA). Il "30" non si ricostruisce dai conteggi (agglomerative 31, hdbscan 20, hdbscan_soft 20).
- **Domanda**: quale griglia dà 30 run, e qual è esattamente la run mancante (nc10 o nc12)?

---

## `code_standards.md`

Scansioni AST su `src/` + `scripts/`; ogni numero è riproducibile con `grep`/`ast`.

## C-019 — Media — §0/§3/§6: errori inghiottiti in `embedding_plots.py`
- **Dove**: `src/analysis/embedding_plots.py:63, 72, 88, 115, 134` (`except Exception as exc: logging.warning(...)` e si prosegue).
- **Prova**: la rotta di errore non rilancia né usa `exc_info`; un plot che fallisce per un bug qualunque (non per I/O) produce solo un warning e la run risulta riuscita. Gli altri 4 `except Exception` di `src/pipeline/` rilanciano dopo la pulizia e sono corretti.
- **Impatto**: è esattamente il pattern che il §0 vieta ("`except: pass`"-like); il test non lo vede.
- **Domanda**: i plot sono ausiliari e la tolleranza è voluta (allora la scrivo come eccezione nel §0 e restringo le eccezioni catturate), oppure l'errore deve fermare la run?

## C-020 — Media — §6: "ogni eccezione loggata con `exc_info=True`" non è la pratica
- **Dove**: `code_standards.md:94`. **Prova**: 114 log di `error`/`warning`/`exception` dentro un `except`; 73 non hanno `exc_info` e non rilanciano (es. `embedding_app.py:707,757,776,840,2973`, `tuning_match.py:143`, `features/functional.py:324`, `embedding_plots.py`).
- **Impatto**: la regola letterale è violata in massa, oppure la regola è più larga di ciò che intende (errori di dominio attesi vs eccezioni inattese).
- **Domanda**: riscrivo il §6 ("`exc_info=True` per le eccezioni inattese; per gli errori di dominio basta il messaggio") o si corregge il codice?

## C-021 — Media — §6: tre entry point senza `log_duration`
- **Dove**: `code_standards.md:96` vs `src/pipeline/embedding_app.py`, `generate_understanding_umap_report.py`, `replot_dim_reduction.py` (nessuno chiama `log_duration`).
- **Prova**: 15 dei 18 entry point la chiamano, tutti dentro un `finally`.
- **Domanda**: `embedding_app` (server Dash) è un'eccezione legittima? Per gli altri due aggiungo `log_duration` o li dichiaro eccezioni?

## C-022 — Media — §1/§2: dimensione di moduli e funzioni
- **Dove**: `code_standards.md:41,53`. **Prova**: `src/analysis/embedding_app.py` = 5540 righe, `build_app` (:3998) = 1543 righe; altre >150: `understanding_umap_report.py:594` (219), `:934` (167), `embedding_app.py:1087` (185), `pipeline/clustering.py:335` (181), `build_sdc_matrix.py:46 main` (162). 211 funzioni su 960 superano 30 righe, 18 superano 100.
- **Impatto**: "idealmente <30" è un obiettivo, ma un modulo di 5540 righe con una funzione da 1543 contraddice "una responsabilità per modulo".
- **Domanda**: la regola resta indicativa, oppure pianifichiamo lo spezzamento di `embedding_app.py` (fuori dall'audit, che è sola lettura)?

## C-023 — Media — §2: codice morto (a meno dell'eccezione "Confronto")
- **Dove**: `src/analysis/clustering_tuning.py:861 integrated_completed_likelihood`, `:917 compute_gap_statistic`; `dendrogram_splits.py:167 colors_at`; `embedding_app.py:2964 comparable_runs`, `:3206 comparison_content_for`, `:3246 pair_cluster_option_label`.
- **Prova**: riferiti solo dai test (nessun uso in `src/`, notebook, config). Le ultime tre appartengono alla sezione "Confronto" parcheggiata (C-006). `integrated_completed_likelihood`/`compute_gap_statistic` servono a kmeans/gmm, in stand-by (`stato_progetto.md:16`); `colors_at` non ha una spiegazione.
- **Domanda**: i tre di kmeans/gmm e `colors_at` restano (e li annoto come parcheggiati) o si cancellano? L'eccezione del §2 per il codice parcheggiato va scritta nel §2?

## C-024 — Bassa — §4: mock su funzioni del repo
- **Dove**: `tests/` (315 `monkeypatch.setattr`). **Prova**: ~295 sostituiscono costanti di percorso con `tmp_path` (isolamento, legittimo); ~13 sostituiscono funzioni del repo: `embedding_app.build_app` ×3, `discover_production_runs` ×6, `load_*_config` ×4, `dim_reduction.load_matrix` ×2, `clustering.run_clustering_tuning_sweep`, `build_fc_matrix.save_matrix`.
- **Domanda**: li esamino uno a uno in Fase 2 (tests/) contro "mai mockare il codice sotto test"?

## C-025 — Bassa — §5/§1: percorsi di output come costanti nei moduli
- **Dove**: `src/pipeline/*.py` (`LOGS_ROOT = Path("logs") / "<nome>"`, `REPORTS_ROOT`), `participants.py` (`METADATA_ROOT`). **Prova**: ~14 moduli; i test devono fare `monkeypatch` di una costante.
- **Domanda**: i percorsi relativi di log/report sono un'eccezione al §5 (da scrivere) o vanno in `config/`?

## C-026 — Bassa — §8: nome sbagliato del file delle lezioni
- **Dove**: `code_standards.md:110` (`lesson_learned.md`). **Prova**: il file è `.claude/lessons_learned.md`. **Domanda**: correggo?

## C-027 — Bassa — §0: esempio che cita codice ritirato
- **Dove**: `code_standards.md:16-29` (`self.has_derivatives()`, `manual_masks`, `self.name`). **Prova**: nessuna occorrenza in `src/`; viene dal modulo ritirato `src/retrieval/dataset.py`. **Domanda**: lo sostituisco con un esempio vivo (es. `group_of` in `subject_ids.py:25`)?

## C-028 — Bassa — §1/§2: testo non più applicabile
- **Dove**: `code_standards.md:40` (livello `models`: non esiste `src/models/`; il livello è solo `analysis`); `:56` vs `src/analysis/plotting.py:64-67` (commento su una funzione rimossa il 01-09-26).
- **Domanda**: tolgo `models` dal §1 e riscrivo/cancello il commento in `plotting.py`?

## C-029 — Bassa — §2: due funzioni pubbliche senza annotazioni complete
- **Dove**: `src/analysis/clustering.py:36 hdbscan_soft_fit` (manca il tipo di ritorno), `:53 soft_membership_matrix(fitted)` (manca il tipo del parametro).
- **Prova**: 472/478 pubbliche complete; le altre 4 sono funzioni interne (`embedding_app.py:2713, 2992, 4763`, `clustering_tuning_analysis.py:229`). **Domanda**: le completo?

---

## `branch_alignment.md`

## C-030 — Bassa — `origin/server-pnc`: "storico" ma con 13 commit non in `main`
- **Dove**: `branch_alignment.md:3`. **Prova**: `git rev-list --count main..origin/server-pnc` = 21; `git cherry main origin/server-pnc`: 13 `+` (non in `main`), 8 `-` (equivalenti); ultimo commit 2026-08-22; merge-base `53dbab6` (2026-07-28, il commit che crea `branch_alignment.md`). I `+` includono "Resume compute_sdc production run, log TODO on streamline provenance" (3-8) e "Log compute_sdc production completion, add 2 lessons learned" (7-8).
- **Impatto**: se il branch viene cancellato, quel lavoro (log di produzione, 2 lezioni, TODO sulla provenienza dello streamline) sparisce dal remoto.
- **Domanda**: il contenuto è già in `main` per altra via (`lessons_learned.md` #26/#27 sembrano le due lezioni) e si può cancellare `origin/server-pnc`, o lo tengo com'è? Il documento deve dire "non integrato" invece di "storico"?

---

## `open_problems.md`

Le cifre sui dati (PSP, WashU, 0671, sede, FC) sono state ricalcolate sui dati locali e tornano (X-001…X-011). Restano non verificabili in locale le misure sul cluster (X-012).

## C-031 — Media — Voci di `open_problems.md` che non sono più aperte o non sono più vere
- **Dove**: `:159` ("`CLAUDE.md` non contiene la regola sul markdown dei notebook"), `:181` ("`anatomical_maps.py` non committato"), `:165` (5150 vs 5151 maschere), `:209` (`s1_production.md`), `:214` (`viz-niivue`, "recuperabile da `facef6f`"), `:195` (#41 obsoleta, mentre `stato_progetto.md:26` la dà ancora per aperta).
- **Prova**: `CLAUDE.md:63` contiene la regola; `git ls-files src/analysis/anatomical_maps.py` lo mostra tracciato e `git status` è pulito; `datasets.md:59` spiega già 5150/704; `find . -name s1_production.md` non trova il file; `git cat-file -t facef6f` → "Not a valid object name".
- **Impatto**: il file si definisce "elenco vivo, una voce si cancella quando è chiusa" (`:5`); sei voci non lo sono.
- **Domanda**: le rimuovo? (`:214` è una nota storica: tengo l'hash solo se è ancora valido.)

## C-032 — Bassa — Conteggi dei tuning senza report non coincidenti
- **Dove**: `open_problems.md:113` ("12 di agglomerative, 12 di HDBSCAN... Le 48 cartelle con report sono state rigenerate il 23-10-26").
- **Prova**: senza `report.md`: agglomerative 15, hdbscan 15 (le 3 in più sono `09-10_*`); `report.md` presenti: agglomerative 48, hdbscan 32, hdbscan_soft 32; modificati il 23-10: 48, tutti agglomerative (i 64 di HDBSCAN restano vecchi, come dice `stato_progetto.md:22`).
- **Domanda**: aggiorno i numeri (15+15) e preciso che le 48 sono solo di agglomerative?

## C-033 — Bassa — Decisione del 23-10 non propagata
- **Dove**: `open_problems.md:34` (decisione A: `participants.csv` riporta il lato clinico) vs `:84-90` (il 23-10 il lato diventa tutto geometrico, "supera la decisione A"); `stato_progetto.md` non cita la decisione; `README.md:94` ("a clinical value is never overwritten") la contraddirà quando sarà implementata. `:86` dà ~1445 soggetti con lato clinico, `participants.csv` ne ha 1448.
- **Domanda**: marco la decisione A come superata nel testo di `:34` e aggiorno 1445→1448?

## C-034 — Media — Soggetti tutti-zero: "lasciati" nella documentazione, esclusi nei dati
- **Dove**: `open_problems.md:213` e `docs/experiments/s1.3-vol.md:24` (`sub-STUKE0146`, `sub-STUKE0201` restano come righe tutte-zero, "2 su 5720") vs `assets/metadata/excluded_subjects.csv` (entrambi `empty_mask`, `scope=all`, che le due pipeline di matrici usano come lista di ammissione).
- **Impatto**: dopo l'introduzione di `excluded_subjects.csv` una nuova `s1.3-vol` non li conterrebbe; la decisione del 07-09 è stata superata senza che la nota lo dica.
- **Domanda**: la nota di `:213` e la sezione di `s1.3-vol.md` vanno riscritte (la matrice s1.3-vol esistente li contiene, le nuove no)? Lo verifico nell'audit di `docs/experiments/`.

## C-035 — Bassa — UKLFR `NIHSS_5a/5b`: 82 soggetti, non 75
- **Dove**: `open_problems.md:66`. **Prova**: nel tsv UKLFR i soggetti con `5a != 5b` e lato noto sono 82; tutti omolaterali (34 sinistra + 48 destra), quindi la conclusione regge, il conteggio no. **Domanda**: aggiorno 75/75 in 82/82 (o indico il filtro usato)?

---

## `lessons_learned.md`

## C-036 — Media — I rimandi "Seen in" puntano a file ritirati, rinominati o spostati
- **Dove**: `lessons_learned.md:5` ("per la narrazione completa segui il suo rimando in `docs/debugging/`") e i pattern #2 (:14), #3 (:18), #5 (:26), #9 (:42), #10 (:46), #12 (:54), #14 (:61-62), #16 (:70), #19 (:82), #20 (:86), #21 (:90), #24 (:102), #25 (:106), #27 (:114), #30 (:126), #34 (:142), #37 (:154), #38 (:156-159), #28 (:116-117).
- **Prova**: 22 percorsi non esistono. Ritirati (restano in `git log`): `src/retrieval/`, `src/sdc/`, `compute_sdc`, `scripts/verify_retrieval.py`, `scripts/data_summary.py`, `scripts/backfill_stale_tuning_output_paths.py`, `scripts/build_dim_reduction_strategies_csv.py`, `jobs/run_compute_sdc.sh`, `docs/dev/retrieval.md`. Rinominati/spostati: `scripts/replot_dim_reduction.py` → `src/pipeline/replot_dim_reduction.py`, `enrich_lesion_metadata.{py,json}` → `enrich_metadata`, `_subjects_with_lesion_mask` → `subjects_with_lesion_mask`, `AUDIT_FINDINGS.md` → `docs/debugging/`, il tsv UCL-UK di `assets/metadata/` cancellato.
- **Impatto**: chi segue un rimando trova un file mancante senza sapere se è un errore. Nessuna delle lezioni è falsa; sono i puntatori a essere stantii.
- **Domanda**: scelgo una convenzione per i riferimenti storici? (a) aggiungo "(ritirato, `git log`)" accanto ai percorsi che non esistono più, (b) aggiorno solo i nomi rinominati, o (c) lascio com'è, dato che sono storici.

## C-037 — Bassa — #17: il test di regressione citato non esiste più
- **Dove**: `lessons_learned.md:72-75` (#17: `regress_out_volume`, "Regression test added... `test_dim_reduction_fine_tuning_nested_n_components_and_regress_out_volume_refits_viz`").
- **Prova**: `grep regress_out` in `src/` e `tests/` → 0; il test con quel nome non c'è. Restano `embedding_for_viz` e `test_embedding_for_viz_forwards_precompute_distance_metric_to_refit`. La regola generale della lesson resta valida.
- **Domanda**: la funzionalità è stata rimossa di proposito (allora annoto "rimossa, la lezione resta") o il test è andato perso? Lo verifico in `docs/debugging/`/`methods_changelog.md`.

## C-038 — Bassa — `debug_17_08_26.md` e `debug_22_08_26.md` non sono citati dal registro delle lezioni
- **Dove**: `lessons_learned.md` (nessun "Seen in" verso i due file); `code_standards.md:110` (ogni bug ha "lessons learned" obbligatorio).
- **Prova**: i due report (2320 e 555 righe, 6 e 19 sezioni) citano le lezioni #14, #18, #26-28 al loro interno, ma il registro non li elenca. In più `debug_10_09_26.md` usa `## §N —` mentre gli altri 14 usano `## N.`.
- **Domanda**: aggiungo i rimandi inversi dove una lezione è nata da quei report? Uniformo il formato dei titoli?

---

## `history/data_changelog.md` e skill `history`

Le cifre sui dati tornano; i problemi sono "conseguenze ancora vere oggi" che non lo sono più e un caso di `has_features` fuori dal vero.

## C-039 — Media — `has_features` di WashU nel registro: 10 su 195, non 169
- **Dove**: `data_changelog.md:193-197` (05-09: `has_features` da 10 a 169 ST dopo il ripristino; "la correzione resta manuale") e `docs/dev/metadata.md:57-63` ("dopo aver lanciato `populate_metadata.py`... correggi a mano i `has_*`").
- **Prova**: `participants.csv`: WashU 195 ST, `has_features=True` per 10; `config/pipelines/populate_metadata.json` (`run_notes`): la run del 23-09 con `overwrite: true` ha fatto il resync su tutti i dataset, con `features/` potata. `mask_summary.csv` ha 169 righe e il manifest della cartella potata elenca la popolazione reale.
- **Impatto**: chi filtra su `has_features` perde 159 soggetti WashU con FC reale; la correzione manuale non è stata rifatta dopo l'ultima run.
- **Domanda**: rifaccio la correzione (169, via manifest) e la registro, o `has_features` deve tornare a descrivere il disco locale e il dato reale va letto dal manifest?

## C-040 — Media — Conseguenze "ancora vere oggi" non più vere, o eventi non registrati
- **Dove**: `data_changelog.md`: (a) `:98-102` e `:130-134` (23-09: `participants.csv` non riflette NEMESIS_T0/SFB936/UKLFR/WashU); (b) `:156-158` (07-09: chi usa `07-09_s2.2-vol` deve escludere `0671`); (c) `:162-189` (06-09: nessuna decisione sui due soggetti UKE, restano in `06-09_s1.3-vol`); (d) `:82` vs `:91` (23-09: `sub-p123`→`0667` tra le cartelle rinominate, ma è solo-tsv).
- **Prova**: (a) `participants.csv` ha tutti e 8 i dataset e `populate_metadata.json` li elenca; (b) la sostituzione maschere del 23-09 ha reso vuota la maschera di `0671` (0 voxel), che oggi è in `excluded_subjects.csv`: `open_problems.md:72` rimanda a "data_changelog.md" per la cancellazione, ma il 23-09 non nomina `0671`; (c) `excluded_subjects.csv` esclude `0146`/`0201` (`empty_mask`, `all`), i loro volumi a 1 mm oggi sono 8 e 3 (la voce dice 16 e 3); (d) la cartella `sub-STUNIPD0667` non esiste (76 cartelle da 0586 a 0666).
- **Impatto**: l'archivio che dovrebbe spiegare "cosa è successo ai dati" tace sul fatto con più conseguenze (maschera di `0671` svuotata, volume di `0146` dimezzato) e afferma stati superati.
- **Domande**: (1) aggiungo una nota (con data) a ciascuna voce per dire come è stata superata, senza riscrivere la storia? (2) so qualcosa sul perché `0671` e `0146` sono cambiati il 23-09 (rsync, versione diversa del file)? Dimmelo e lo registro.

---

## `history/project_changelog.md` (audit parziale: righe 1-64 + script su tutto il file)

## C-041 — Bassa — Due "recuperabile da <SHA>" non funzionano in questa copia del repo
- **Dove**: `project_changelog.md:742` (`backup-pre-split` da `068d2ff`) e `:752` (`viz-niivue` da `facef6f`, "finché il reflog lo conserva (~90 giorni)"); anche `open_problems.md:214`.
- **Prova**: `git cat-file -t 068d2ff` e `facef6f` → "Not a valid object name". Il secondo ha 49 giorni (07-09 → 26-10), cioè entro i 90.
- **Impatto**: lo SHA annotato "proprio perché un branch cancellato non compare in `git log`" non permette il recupero qui; può esistere solo nell'altro checkout (server) o essere stato ripulito da `git gc`.
- **Domanda**: i due oggetti esistono sul server? Se no, tolgo la frase "recuperabile" (la storia dei due branch non è più recuperabile) e chiudo anche la voce di `open_problems.md`.

## C-042 — Bassa — Formato e conteggi del registro
- **Dove**: `project_changelog.md:883` (`## 2026-08 — Produzione e tuning separati…`, data senza giorno, contro il formato `GG-MM-AA` dello skill `history`); `:39-54` (backup "88 MB", tabella di 4 sottocartelle, ma sul disco ce ne sono 6 e 95 MB); `00_master_plan.md` (832 righe al bootstrap, oggi 887: il file cresce mentre lo audito).
- **Domanda**: normalizzo il titolo dell'ultima voce con una data completa? Aggiorno il backup "88 MB / 4 cartelle" (le altre due sono descritte nelle due voci precedenti dello stesso giorno)?

---

## `docs/setup.md` (ciclo 9)

## C-043 — Media — `setup.md:26`: `--prune` rimuove `dash` dall'ambiente
- **Dove**: `docs/setup.md:23-27` ("Aggiungere un pacchetto": `conda env update -f environment.yml -n nemesis --prune`); causa a monte in C-002.
- **Prova**: `conda list -n nemesis` → `dash 4.4.1 ... conda-forge`, `flask 3.1.3` installati ma assenti da `environment.yml`; il `--dry-run` di `conda env create -f environment.yml` produce un piano senza `dash`. `--prune` rimuove i pacchetti non presenti nel file (`conda env update --help`). Il comando non è stato eseguito (modificherebbe l'ambiente).
- **Impatto**: seguendo la procedura scritta per aggiungere un pacchetto, l'Embedding Explorer (`embedding_app.py:61`) e i suoi test smettono di funzionare; un ambiente ricreato da zero non li ha mai.
- **Domande**: (a) aggiungo `dash` a `environment.yml` (con versione fissata? `4.4.1`)? (b) togliere `--prune` dal comando (più sicuro) oppure tenerlo dopo la correzione di (a)?

## C-044 — Bassa — `setup.md:23`: la regola "conda-forge vs pip" non è quella del file
- **Dove**: `setup.md:23` vs `environment.yml`. **Prova**: la sezione `pip:` contiene `nibabel`, `nilearn`, `factor_analyzer`, `pacmap` (tutti su conda-forge); `hdbscan` è in `dependencies` ma l'ambiente locale lo ha da PyPI (`pypi_0`). Nel dry-run il solver installa `hdbscan 0.8.41` da conda-forge e `plotly 7.1.0`, mentre l'ambiente locale ha `hdbscan 0.8.44` e `plotly 6.9.0`: l'ambiente di sviluppo non coincide con quello che `environment.yml` ricreerebbe (nessuna versione fissata).
- **Impatto**: la regola scritta non descrive il file; versioni non fissate, quindi due macchine possono divergere (la suite è verde con le versioni locali).
- **Domanda**: riscrivo la frase ("`pip:` per ciò che si vuole da PyPI") o sposto i quattro pacchetti in `dependencies`? Fissiamo le versioni (`conda env export --from-history` o pin) oppure no?

## C-045 — Bassa — `setup.md:36`: esempi di `scripts/` che non esistono
- **Dove**: `setup.md:36` ("download e organizzazione dataset, utility di setup"). **Prova**: `scripts/` = `archive_local_raw_data.py`, `build_dataset_summary_table.py`. `README.md:35` e `CLAUDE.md:48` usano un'altra descrizione ("cache maintenance, tables, derived indices").
- **Domanda**: allineo `setup.md:35-36` alla descrizione di `CLAUDE.md:48`, o tolgo la sezione "Organizzazione del codice" (è già in `README.md` e `CLAUDE.md`, tre copie)?

## C-046 — Bassa — `setup.md:29-31`: `nemesis_fallback` non è riproducibile dal repo
- **Dove**: `setup.md:31`, `guides/clustering.md:158-161`. **Prova**: nessun file nel repo crea `nemesis_fallback` (nessun `environment_*.yml`, nessun comando `conda create`); versioni note solo per testo (`dadapy 0.3.4`, numpy 1.26.4, scikit-learn 1.9.1, jax 0.4.30). "oggi" lega il testo a un istante. Il nome "fallback" non spiega il ruolo (è l'ambiente ADP).
- **Impatto**: su una macchina nuova ADP non si può far partire seguendo la documentazione.
- **Domande**: aggiungo un `environment_adp.yml` (o i comandi `conda create`/`pip install dadapy==0.3.4`) alla doc? Rinomino l'ambiente (es. `nemesis_adp`) o resta `nemesis_fallback`? Tolgo "oggi"?

---

## `docs/guides/` — ciclo 10 (`evaluate_dim_reduction_tuning.md`, `fc_matrix_building.md`, `understanding_umap_report.md`)

## C-047 — Bassa — `evaluate_dim_reduction_tuning.md:36`: con `overwrite: false` lo script scrive una parte prima di fermarsi
- **Dove**: `docs/guides/evaluate_dim_reduction_tuning.md:36` ("lo script si ferma se i file della valutazione esistono già"); `src/analysis/tuning_evaluations.py:155-158`.
- **Prova** (copia in scratchpad di `07-10_s1.4-vol`, 6 foglie): tolti i file `hdbscan_*mcs100_ms10*` dalla sola foglia `metric=dice/n_components=2`, rilancio con `overwrite: false` → i file di quella foglia vengono scritti, poi rc=1 alla seconda foglia (già occupata). Il controllo è dentro il ciclo, per foglia. Inoltre `FileExistsError` è un `OSError`: `evaluate_dim_reduction_tuning.py:68` stampa un traceback completo per una condizione attesa.
- **Impatto**: nessuna perdita di dati (non sovrascrive), ma l'output può restare a metà; il comportamento descritto ("si ferma se esistono già") è vero solo se la prima foglia è già occupata. Stessa forma di `lessons_learned.md` #9/#18 (esito parziale).
- **Domanda**: correggo il codice (controllare tutte le foglie prima di scrivere, e non stampare il traceback) o riscrivo la guida ("si ferma alla prima foglia già occupata; le precedenti sono già scritte")?

## C-048 — Media — `fc_matrix_building.md:48`: i controlli sani non "vengono aggiunti con 0 nodi compromessi"
- **Dove**: `docs/guides/fc_matrix_building.md:47-48` (`"group_filter": ["ST","HC"]`: "I sani verranno aggiunti con 0 nodi compromessi"); contro `src/features/functional.py:240-267`, `src/pipeline/mask_fc.py:121-127`, `docs/dev/fc_matrix.md:38`.
- **Prova**: `discover_subject_files` usa solo i soggetti che hanno **sia** FC **sia** maschera di lesione; un sano ha FC ma nessuna maschera ("structurally never has a lesion mask", `fc_matrix.md:38`) → finisce in `missing_lesion` ed è **saltato con un WARNING**. Nessun codice assegna "0 nodi compromessi". Non ho potuto eseguire il caso: le FC dei sani non sono in locale (sono in `features_archive.tar.gz`); la conclusione viene dalla lettura del codice e dal doc di sviluppo, che si contraddicono con la guida.
- **Impatto**: chi mette `["ST","HC"]` per "task comparativi" otterrebbe lo stesso insieme di soggetti di `["ST"]` più un warning; il rimando di `fc_matrix.md:38` a questa guida punta a un testo che dice il contrario.
- **Domande**: (a) confermi che i sani vengono saltati? Allora riscrivo la guida (e `["ST","HC"]` non serve a niente: va sconsigliato o rimosso come opzione?). (b) Oppure vuoi davvero includerli con 0 nodi compromessi (richiederebbe una modifica al codice, non alla doc)?

## C-049 — Bassa — `fc_matrix_building.md:46`: `group_filter` non esiste in `build_fc_matrix.json`
- **Dove**: `docs/guides/fc_matrix_building.md:46` ("In `mask_fc.json` e `build_fc_matrix.json` puoi specificare"). **Prova**: `config/pipelines/build_fc_matrix.json` non ha la chiave; `src/pipeline/build_fc_matrix.py` e `model_config.py` non la leggono (il filtro agisce solo in `mask_fc`; `build_fc_matrix` legge ciò che trova in `masked_fc/<combo>/`). `docs/dev/pipeline_flow.md:41` dice che il ramo FC sceglie i soggetti dal filtro di gruppo.
- **Domanda**: tolgo `build_fc_matrix.json` dalla frase?

## C-050 — Bassa — `fc_matrix_building.md:54`: l'imputazione è presentata come già decisa
- **Dove**: `docs/guides/fc_matrix_building.md:54` ("L'imputazione intelligente... avverrà in un passaggio separato appena prima della *Dim Reduction*"); `README.md:74` ("NaN-imputation remains deliberately open, pending an empirical look at the full cohort").
- **Prova**: 0 occorrenze di "imput" in `src/`; `dim_reduction.md`/`pipeline_order.md` non la citano. La guida usa il futuro per un passaggio che non esiste e che il README dichiara aperto. Conseguenza pratica: la matrice FC ha NaN e `README.md:74` la dice "ready for `dim_reduction.py`" senza dire che non la accetterebbe.
- **Domanda**: scrivo al presente "nessuna imputazione: i NaN restano e la scelta è aperta (README)" e annoto che `dim_reduction` non gestisce i NaN? Verifico io cosa fa `dim_reduction` con una matrice con NaN in un ciclo successivo?

## C-051 — Media — `understanding_umap_report.md:44`: i modi `side` e `nihss` non sono disponibili nei run attuali
- **Dove**: `docs/guides/understanding_umap_report.md:44` ("colorabile per `dataset`/`side`/`volume`/`nihss`"); `src/analysis/understanding_umap_report.py:71,996`; `src/pipeline/dim_reduction.py:12-14`.
- **Prova**: il report offre solo i modi i cui dati stanno in `metadata.csv` del tuning; `dim_reduction.py:14` dichiara "lesion_side/nihss are NOT in metadata at all". Il tuning di esempio della guida (`13-08_s1.1-vol`) ha `metadata.csv` = `subject_id,dataset`; rigenerato il report su copia: il selettore ha solo `none` e `dataset`. L'altro tuning UMAP con lesione (`07-10_s1.4-vol`) ha `dataset` + `lesion_volume_voxels`. Anche `COLOR_BY_MODES`, `_METADATA_COLUMN_BY_MODE` (`lesion_side`, `nihss`) restano per una fonte che nessun run produce più.
- **Impatto**: la guida promette un colore per lato e NIHSS che il report non offre; chi apre l'HTML cerca un selettore che non c'è. Il codice di quei due modi è oggi raggiungibile solo con un `metadata.csv` scritto a mano (cfr. C-023, codice morto).
- **Domande**: riscrivo la guida ("i modi dipendono dalle colonne di `metadata.csv`: oggi `dataset` e, se presente, `volume`")? Il codice di `side`/`nihss` va tolto o tenuto?

## C-052 — Bassa — Avverbi temporali e futuro nelle guide (regola `CLAUDE.md:53`)
- **Dove**: `evaluate_dim_reduction_tuning.md:3` ("oggi `plot_hdbscan`"); `fc_matrix_building.md:3` ("disponibili attualmente per la coorte WashU"), `:54` ("avverrà" — vedi C-050); `understanding_umap_report.md:16` ("se un giorno esisterà un run t-SNE con `n_components=3`... oggi assente"), `:39` ("oggi `dice`, `euclidean`"); `setup.md:31` ("oggi", C-046).
- **Impatto**: leggero; ogni avverbio lega il testo a un istante e invecchia. `understanding_umap_report.md:39` elenca le metriche del tuning di esempio come se fossero universali.
- **Ciclo 11 (stessa voce)**: `sdc_matrix_building.md:65` ("oggi tutti e 8"), `:104` ("attualmente supportati"); `dim_reduction.md:41` ("oggi disponibili"), `:66` ("analisi correnti"), `:74` e `:76` ("nessuna run precedente all'introduzione di questo campo", "prima dell'introduzione"), `:127-128` ("futuro plot interattivo", "un plot futuro"); `evaluate_clustering_tuning.md:23` ("in stand by... Si riprendono dopo aver chiuso i tre metodi").
- **Domanda**: tolgo gli avverbi (e le frasi ipotetiche sul futuro) tenendo il fatto presente?

## C-053 — Bassa — Invocazioni non esatte o ridondanti nelle guide
- **Dove**: `fc_matrix_building.md:36` ("`python -m src.pipeline...`" senza `--config`); `understanding_umap_report.md:30` (`PYTHONPATH=.` con `-m`) e `:22-25`.
- **Prova**: (1) `CLAUDE.md:21-23` chiede "l'invocazione esatta" per ogni pipeline: la guida FC non la dà né per `mask_fc` né per `build_fc_matrix` (i comandi corretti sono in `pipeline_order.md:141`). (2) `python -m src.pipeline.generate_understanding_umap_report --help` funziona dalla radice **senza** `PYTHONPATH` (provato): la variabile è ridondante (conferma A-006; il job la esporta comunque). (3) Il job `run_generate_understanding_umap_report.sh` fissa le due cartelle (`13-08_s1.1-vol`) dentro lo script (righe 14-15), la guida non dice che per un altro tuning va modificato il job.
- **Domanda**: aggiungo i comandi esatti alla guida FC, tolgo `PYTHONPATH=.` e aggiungo la nota sul job?

## `docs/guides/` — ciclo 11 (`sdc_matrix_building.md`, `dim_reduction.md`, `evaluate_clustering_tuning.md`)

## C-054 — Bassa — `sdc_matrix_building.md`: tabella dei parametri e una frase del paragrafo introduttivo
- **Dove**: `sdc_matrix_building.md:59-71` (tabella "Comuni a entrambe le modalità"), `:78`, `:7`.
- **Prova** (`build_config.py:343-460`): (1) la modalità sono tre, non due; (2) `output_root` è presentato come "default `data/derived/sdc_matrix`" ma `_require_str(raw, "output_root")` lo rende obbligatorio, senza default; (3) `excluded_subjects_path` è obbligatorio e manca dalla tabella (è citato solo a `:42`); `run_notes` (opzionale) non c'è; (4) `value_column` "(default consigliato)": il campo è obbligatorio per `parcellated`, nessun default; (5) `:7` "Nonostante la famiglia `LF-lesion` è una misura di disconnessione, quindi appartiene alla track `s2.x`" non è una frase corretta (la `lesion`+`streamline` è in `s2.3-stream`/`s2.4-stream`, `docs/experiments/README.md:13,16`).
- **Domanda**: correggo la tabella (tre modalità, campi obbligatori marcati, niente "default" dove non c'è) e riscrivo la frase di `:7`?

## C-055 — Media — `dim_reduction.md:118,128`: i metadati non vengono arricchiti con `lesion_side` e `nihss`
- **Dove**: `dim_reduction.md:118` ("`metadata.csv`: L'anagrafica arricchita in automatico di `lesion_volume_voxels`, `lesion_side`, e `nihss`") e `:128` (tuning: "identica per schema a quella di produzione"); `src/pipeline/dim_reduction.py:9-16` (docstring) e `:45-47`.
- **Prova**: il docstring di apertura dice che la pipeline "no longer enriches" i metadati: li passa dall'input; `lesion_volume_voxels` c'è se la matrice la ha, `lesion_side`/`nihss` non sono mai nei metadati (si risolvono al momento del plot dal registro). Sui 40 `metadata.csv` di produzione in `results/`: 33 hanno `subject_id,dataset`, 7 aggiungono `lesion_volume_voxels`. Nei 5 tuning con `embeddings.npz`: `subject_id,dataset` (4) o + volume (1: `07-10_s1.4-vol`). Un docstring stesso si contraddice (`:45-47`: "same enrichment _run_production always applies", dopo aver detto che non arricchisce).
- **Impatto**: stessa radice di C-051: chi si aspetta lato e NIHSS in `metadata.csv` (per rileggerlo senza il registro) non li trova; la frase di `:128` ("senza questo file un plot futuro non saprebbe come colorare") dà una ragione che non vale più.
- **Domanda**: riscrivo `:118` e `:128` ("i metadati dell'input, invariati; lato e NIHSS si leggono dal registro al momento del plot") e correggo il docstring `:45-47` di `dim_reduction.py`?

## C-056 — Media — `dim_reduction.md:72`: `viz_n_components: 3` non produce nessun HTML
- **Dove**: `dim_reduction.md:72` ("A `3`, fornisce solo l'HTML interattivo ruotabile") contro `:39` ("non viene scritto nessun PNG/HTML statico"), `:120` ("con `viz_n_components: 3` nessun PNG statico viene scritto... non viene scritto un file `.html` per-run") e `src/analysis/embedding_plots.py:42,56`.
- **Prova**: con 3 colonne `write_embedding_plots` non scrive nessun file; l'esplorazione 3D è solo `embedding_app`. La guida si contraddice al suo interno. Inoltre per `pca`/`pacmap` il raffittamento è impossibile (`reduction.py:205-212`): con `viz_n_components` ≠ `n_components` e rotazione senza ordine la run si ferma, cosa che `:72` non dice.
- **Domanda**: correggo `:72` ("a 3 non si scrive nessun file statico; si guarda con `embedding_app`")?

## C-057 — Bassa — `report.md` salvati non coincidono con il codice attuale dei report
- **Dove**: `results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_m_dice_nc2/report.md` (23-10) contro `clustering_tuning_report.py` + `utils/report_texts/clustering_tuning.md` (non committati).
- **Prova**: rilanciando `evaluate_clustering_tuning` su una copia (overwrite: true, rc=0, 39 s) i 6 CSV sono identici byte per byte, ma `report.md` cambia in 36 righe: "Dendrogramma (ultime 30 fusioni)" → "Dendrogramma"; "sono mostrate solo le ultime 30 fusioni" → "(quante, sta sull'asse orizzontale della figura)". Il resto del file coincide.
- **Impatto**: lieve; i 48 report di agglomerative rigenerati il 23-10 (C-032, `stato_progetto.md:22`) sono già vecchi rispetto al codice di oggi. La guida descrive il comportamento nuovo.
- **Domanda**: è atteso (modifica in corso dei testi)? Quando i testi sono chiusi, rigenero i 48 report e aggiorno i conteggi di C-032?
