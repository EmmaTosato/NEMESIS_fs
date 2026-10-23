# 02 — Contraddizioni e problemi aperti (richiedono una decisione dell'utente)

Severità: ALTA (rompe esecuzione/riproducibilità) · MEDIA (doc fuorviante o regola violata) · BASSA (imprecisione/igiene).
Ultimo aggiornamento: dopo audit di `.claude/CLAUDE.md`.

---
## ISS-001 — Impossibile verificare gli hash git citati (limite di ambiente, non errore del progetto)
- **Tipo**: Doc vs Git · **Severità**: BASSA (finché non verificato)
- **Dove**: `CLAUDE.md` (cita `2ed3dcb`), `lessons_learned.md` (`cf6e1fe`, `2dcd0ae`, `b71ff7c`, `9fb13fb`)
- **Prova**: `git rev-parse --is-shallow-repository` → `true`; `git cat-file -t <hash>` → "Not a valid object name" per tutti e 5; `git log` ha solo 50 commit.
- **Impatto**: tutte le affermazioni "commit X ha fatto Y" restano non verificate.
- **Decisione richiesta**: posso eseguire `git fetch --unshallow origin` (sola lettura, ma scarica storia) per verificare questi riferimenti? [sì/no]

## ISS-002 — `dash` mancante da `environment.yml` ma richiesto da `embedding_app`
- **Tipo**: Doc/Config vs Codice · **Severità**: ALTA (riproducibilità)
- **Dove**: `environment.yml` (nessuna riga `dash`) vs `src/analysis/embedding_app.py:61-62` (`from dash import ALL, Dash, ...`); `docs/setup.md:31` implica che l'env `nemesis` abbia dash ("Quell'ambiente [nemesis_fallback] non ha `dash`").
- **Prova**: `grep -n -i dash environment.yml` → nessun risultato; l'import è top-level (nessun guard).
- **Impatto**: un `conda env create -f environment.yml` pulito non può avviare `embedding_app` né i suoi test (se non saltati). Verosimilmente `dash` è installato a mano nell'env reale.
- **Decisione richiesta**: aggiungere `dash` (e versione) a `environment.yml`? Se `dash` arriva già come dipendenza di `plotly`/altro, indicare quale env lock usate.

## ISS-003 — Nessun job SLURM per `scripts/archive_local_raw_data.py` e `src/pipeline/embedding_app.py`
- **Tipo**: Doc vs Filesystem (regola violata) · **Severità**: MEDIA
- **Dove**: `CLAUDE.md:29` ("When a new pipeline/script is added ... add a matching `jobs/run_<name>.sh` at the same time") e `CLAUDE.md:~8-9`/`24` ("one `sbatch` job script per `src/pipeline/`/`scripts/` entry point").
- **Prova**: `ls jobs` (18 file) non contiene `run_archive_local_raw_data.sh` né `run_embedding_app.sh`; `scripts/` ha 2 file, `src/pipeline/` 18 moduli (+`__init__`). Le altre 17 pipeline/script hanno il job.
- **Impatto**: regola dichiarata non rispettata o eccezione non documentata. `embedding_app` è un'app Dash interattiva (eccezione plausibile); `archive_local_raw_data` opera su dati locali (plausibile "solo locale").
- **Decisione richiesta**: dichiarare esplicitamente in CLAUDE.md le due eccezioni (interattiva / solo-locale), oppure creare i due job?

## ISS-004 — `docs/dev/covariance_pca.md` non è elencato nell'indice di CLAUDE.md
- **Tipo**: Doc vs Doc · **Severità**: BASSA
- **Dove**: `CLAUDE.md:36` (elenco dei file in `docs/dev/`, 14 voci) vs `ls docs/dev` (15 file, extra: `covariance_pca.md`, 129 righe). Il modulo `src/analysis/covariance_pca.py` esiste.
- **Impatto**: l'indice è incompleto; un nuovo agente non scopre il doc.
- **Decisione richiesta**: aggiungere `covariance_pca.md` all'elenco in CLAUDE.md? (fix triviale, lo applico se confermi)

## ISS-005 — "`*.nii`/`*.nii.gz` gitignored" non corrisponde a `.gitignore`
- **Tipo**: Doc vs Config · **Severità**: BASSA/MEDIA
- **Dove**: `CLAUDE.md:17` vs `.gitignore` (nessuna regola `*.nii*`; ignorati solo `data/*`, `results/`, `logs/`, `summaries/`).
- **Prova**: `git ls-files | grep -E "\.nii"` → **22 file tracciati** (atlanti Yan/Tian/Buckner e template MNI in `assets/`, ad es. `assets/atlases/fmriprep/atlas-Yan100TianS1Buckner7N/..._dseg.nii.gz`, `assets/templates/tpl-MNI152NLin6Asym_res-1_T1w.nii.gz`).
- **Impatto**: la frase è vera solo per `data/` (ignorato per cartella). Un `.nii.gz` messo fuori da `data/` verrebbe tracciato per errore.
- **Decisione richiesta**: riformulare la frase ("i dati grezzi stanno sotto `data/`, ignorato; atlanti/template piccoli in `assets/` sono tracciati") oppure aggiungere una regola `*.nii*` con eccezioni per `assets/`?

## ISS-006 — `code_standards.md` §8 cita `lesson_learned.md` (nome inesistente) e CLAUDE.md gli attribuisce una regola che non contiene
- **Tipo**: Doc vs Doc · **Severità**: BASSA
- **Dove**: `code_standards.md:110` → `(`lesson_learned.md`)`; il file reale è `.claude/lessons_learned.md`. `CLAUDE.md` (sezione "Lessons learned") afferma "Updated after every debugging session per `code_standards.md` §8", ma §8 chiede solo una sezione "lessons learned" per bug dentro il report, non di aggiornare l'indice cumulativo.
- **Impatto**: riferimento rotto + regola di processo non scritta dove dichiarato.
- **Decisione richiesta**: correggere il nome in §8 e aggiungere in §8 la regola "aggiorna `.claude/lessons_learned.md`"?

## ISS-007 — `CLAUDE.md:11` e `docs/setup.md:11` elencano una parte dei pacchetti, non tutti
- **Tipo**: Doc vs Config · **Severità**: BASSA
- **Dove**: elenco "numpy, scipy, ..., nilearn" vs `environment.yml` che contiene anche `python=3.11`, `hdbscan`, `plotly`, `openpyxl`, `pytest`, `pytest-cov`, `hypothesis`, `factor_analyzer`, `pacmap`.
- **Impatto**: nessuno funzionale (setup.md dice "Pacchetti principali"), ma `hdbscan`/`pacmap`/`factor_analyzer` sono metodi centrali del progetto e non compaiono.
- **Decisione richiesta**: allineare l'elenco o rimandare a `environment.yml` come unica fonte?

## ISS-008 — `summaries/` citata nel perimetro ma assente (info)
- **Tipo**: Filesystem · **Severità**: BASSA
- **Prova**: `ls summaries` → assente; è in `.gitignore` (`summaries/`), come `logs/` (nel workspace `logs/` ha solo 44 file: sottoinsieme, non la storia completa).
- **Impatto**: la Fase 2 non può auditare `summaries/`; le affermazioni dei doc su `summaries/` e su `logs/` per run non committate non sono verificabili.
- **Decisione richiesta**: confermare che `summaries/` e i log completi vivono solo sul cluster/locale e che vanno trattati come "non verificabili"; oppure fornirli.

## ISS-009 — `pytest` non eseguibile nel container corrente (info/limite)
- **Prova**: nessun `conda`; `python3` = 3.13.17 senza `numpy`/`sklearn`; `environment.yml` richiede python=3.11 + stack scientifico.
- **Impatto**: il punto 4bis.4 (esecuzione dei test) non è fattibile finché l'ambiente non è creato.
- **Decisione richiesta**: posso creare un ambiente (es. `pip install` o micromamba di `environment.yml`) nel container? Richiede rete + molti GB (umap/nilearn/dash); oppure rimandare i test a una macchina vostra e incollarmi l'output.
