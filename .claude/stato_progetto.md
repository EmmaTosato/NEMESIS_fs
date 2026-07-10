# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-07-09. Scritto per permettere a un nuovo agente/sessione di riprendere senza contesto pregresso. Il file copre più sessioni, in ordine cronologico inverso (la più recente in cima).

## Sessione 2026-07-09 (4) — Verifica checksum integrata nel pipeline (design a due fasi) + test di integrazione senza numeri hardcoded

### Obiettivo

Verificare che i file copiati in `data/` corrispondano davvero alla sorgente EBRAIN (soggetto giusto, contenuto giusto), poi integrare questa verifica nel pipeline di retrieval stesso invece di lasciarla solo come script separato.

**Nota per chi legge dopo**: questa sessione **non** corrisponde al racconto della sessione (3) qui sotto (quella descrive la feature come "già presente nel repo, scoperta durante il run" — probabilmente un'altra conversazione parallela sullo stesso repo). In questa sessione la feature di verifica è stata **costruita da zero, in due iterazioni**, con il design finale diverso da quello di un primo tentativo — vedi sotto.

### Decisioni prese / concetti discussi

1. **Prima iterazione (scartata)**: verifica checksum inline dentro `_copy_one`/`_retrieve_participants`, subito dopo ogni singola copia/skip. Scartata perché l'utente ha chiarito due cose: (a) la verifica va fatta **solo dopo che tutte le copie di tutti i dataset sono finite**, non interfogliata file per file; (b) la logica di verifica esisteva già in `scripts/verify_retrieval.py` (script standalone scritto in una sessione/turno precedente) — andava **riusata**, non riscritta dentro il pipeline.
2. **Design finale**: logica di verifica estratta in un modulo condiviso **`src/retrieval/verify.py`** (`verify_dataset(name, ds, subjects, config) -> VerificationResult`), usato da due chiamanti:
   - `src/pipeline/retrieve_data.py`: `_retrieve_all` ora fa due passate sequenziali — prima copia *tutti* i dataset richiesti (`_retrieve_dataset`), poi verifica *tutti* i dataset (`_verify_dataset_copies`), mai interfogliate.
   - `scripts/verify_retrieval.py`: ridotto a thin wrapper CLI che richiama la stessa funzione, tenuto come backup per un controllo manuale senza rilanciare tutto il retrieval.
3. **Cosa controlla `verify_dataset`**: per ogni soggetto della selezione, ri-risolve il file sorgente con `Dataset.resolve()` (mai fidandosi della copia già fatta) e confronta sha256 sorgente vs locale → 3 categorie di esito: `mismatched` (contenuto diverso — corruzione o sorgente cambiata), `missing_locally` (sorgente ce l'ha, `data/` no — copia fallita silenziosamente), `unexpected_local_files` (file presente in locale ma non risolvibile da nessuna combinazione attesa oggi — naming vecchio/residuo). Tutti e 3 aggiunti a `DatasetStats` (`src/pipeline/retrieve_data.py:33-44`), loggati (ERROR i primi due, WARNING il terzo) e resi come nuove sezioni nel report.
4. **Test di integrazione riscritti per non usare numeri hardcoded** (obiezione esplicita dell'utente: "il numero di partecipanti cambia in maniera dinamica", "tu devi contare in tempo reale"). Causa scatenante: un run reale della suite ha fatto emergere che 3 test con conteggi scritti a mano (201/296 maschere MNI/T1w per WashU, "WashU non ha participants.tsv") erano diventati falsi — non per un bug, ma perché un collega (`nazziale`) aveva aggiunto mesi fa (verificato con `ls -la`, mtime maggio/ottobre 2025) la cartella raw mancante per `sub-STUNIPD0001` (prima un'anomalia nota, "derivative orfana") e un `participants.tsv` per WashU. Fix: `tests/integration/test_lesion_counts.py` e `test_participants.py` ora calcolano il valore atteso **al momento del test**, con un metodo indipendente da `Dataset`/`file_patterns.json` (glob diretto sul filesystem reale), e confrontano quell'insieme con l'output di `Dataset.resolve()` — un mismatch segnala sempre un vero bug nella logica di risoluzione, mai un dato cambiato nel frattempo. Unica tabella rimasta hardcoded: `EXPECTED_AVAILABLE_MODALITIES` (quali *tipi* di scan esistono per dataset — fatto strutturale stabile, diverso da un conteggio).
5. Chiarito con l'utente un falso allarme: durante un run di prova ho trovato che `data/` era stata svuotata tra un mio comando e l'altro — non un bug, l'utente l'aveva cancellata di persona per testare il retrieval da zero.

### File modificati/creati (verificato con `git status`/`git diff`)

- **Codice nuovo**: `src/retrieval/verify.py`
- **Codice modificato**: `src/pipeline/retrieve_data.py` (+58/-0 circa: `DatasetStats` con 3 nuovi campi, `_verify_dataset_copies`, doppio loop in `_retrieve_all`, nuove sezioni report, log ERROR aggregato in `main()`), `scripts/verify_retrieval.py` (riscritto da zero come thin wrapper, -100 righe circa)
- **Test nuovi**: `tests/unit/test_verify.py` (7 test per `verify_dataset`)
- **Test modificati**: `tests/unit/test_retrieve_pipeline.py` (firma `_copy_one` invariata rispetto a prima della prima iterazione, nuovo test sul doppio-loop), `tests/integration/test_lesion_counts.py`, `tests/integration/test_participants.py` (riscritti per non hardcodare conteggi/fatti, vedi punto 4 sopra)
- **Doc**: `docs/dev/retrieval.md` (matrice STOP/WARNING/ERROR aggiornata, sezione dedicata alla verifica, layout moduli, sezione testing riscritta), `docs/guides/retrieval.md` (sezione "Verification: a final pass...", elenco sezioni report aggiornato)
- **Dati locali (gitignored)**: `data/`, `logs/`, `reports/` ripopolati da un run reale dell'utente

### Stato dei test

**97/97 passati** (`conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v`, ultima esecuzione — include sia i nuovi `test_verify.py` sia i test di integrazione riscritti, contro il mount EBRAIN reale). Il run reale del pipeline fatto dall'utente in questa sessione ha prodotto una verifica pulita: 0 `mismatched`, 0 `missing_locally`, 0 `unexpected_local_files` su tutti e 4 i dataset.

### Osservazione da verificare

Il log di un run intermedio (`09-07-26__16-51.log`) dice "report written to ... 09-07-26__16-51.md", ma quel file non esiste in `reports/` — probabilmente cancellato manualmente dall'utente (coerente con l'abitudine, già vista in sessione precedente, di trattare i report come artefatti rigenerabili). Non confermato esplicitamente dall'utente in questa sessione, a differenza del caso analogo in sessione (3).

### Prossimo passo esatto

1. Lavoro attuale (retrieval + verify + doc + test) tutto in working tree, non committato — decidere se/quando committare (nessun commit richiesto esplicitamente in questa sessione).
2. Se si vuole, chiarire con l'utente il file di report mancante (vedi sopra) — non bloccante.
3. Tornare al filone SDC/BCBToolKit o Task1 (vedi "Prossimo passo esatto" di sessione (2) più sotto) quando si vuole riprendere il lavoro di modellazione, oppure proseguire sul modulo di retrieval se emergono altri dataset/modalità da aggiungere a `file_patterns.json`.

---

## Sessione 2026-07-09 (3) — Rilancio retrieval dopo refactor `file_patterns` + scoperta feature di verifica checksum

### Obiettivo

Eseguire il "prossimo passo esatto" lasciato dalla sessione (2) precedente: rilanciare la suite di test (mai fatto dopo il refactor `file_patterns.json`), poi un run reale della pipeline di retrieval, e ispezionare l'output.

### Sequenza eseguita

1. **Suite completa** (`conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v`): **87/87 passed**, inclusi gli integration test contro il mount EBRAIN reale. Nota: questo run **non includeva ancora** `tests/unit/test_verify.py` (comparso nel working tree solo dopo, vedi punto 3) — quei test non sono stati verificati in questa sessione.
2. **Run reale della pipeline** (`python -m src.pipeline.retrieve_data --config config/data_retrieval.json`), config invariata (4 dataset, `group_filter: ["ST"]`, `mni/lesion_mask`, `include_tabular_data: true`, `overwrite: false`). Report/log `09-07-26__16-44`:
   - 1150 file copiati (WashU 202, PASPORT 83, PSP 168, UKLFR 697), 0 falliti, `participants.tsv` copiato per tutti i dataset che lo hanno a sorgente.
   - Missing (per-soggetto, normale — file assente a sorgente): 170 totali (49+14+69+38).
   - Ambiguous = 0, Non-conforming subject folders = 0.
   - Log pulito: solo righe `INFO: copied: ...`, nessun WARNING/ERROR.
   - Rilanciata una seconda volta (report `16-51`, poi **cancellato dall'utente** — non fa parte dello storico, ignorare/non cercarlo) solo per conferma idempotenza (`overwrite: false` → tutto skipped, 0 copiati).
3. **Scoperta**: nel repo era già presente (fuori da questa conversazione, probabilmente modifiche dirette dell'utente nell'IDE in parallelo alla chat) una feature di **verifica checksum** non documentata all'inizio della sessione: `src/retrieval/verify.py` (nuovo, non tracciato), integrata in `retrieve_data.py` (`_verify_dataset_copies`, gira dopo che *tutti* i dataset hanno finito la copia, mai interleaved), `scripts/verify_retrieval.py` ridotto a thin wrapper CLI attorno allo stesso modulo, `tests/unit/test_verify.py` nuovo. Il report del run (punto 2) mostrava solo la sezione **Mismatched** (vuota) — le due sezioni aggiuntive introdotte dal codice attuale (**Not copied despite source having it**, **Unexpected local files**) non comparivano nel report perché il codice è stato esteso *dopo* quel run: il report è quindi "stale" rispetto all'ultima versione del codice su questi due punti specifici (il valore comunque risulta 0 per entrambi, vedi punto 4, solo non era nel report scritto su disco).
4. **Verifica standalone** (`PYTHONPATH=. conda run -n nemesis python scripts/verify_retrieval.py --config config/data_retrieval.json`), con il codice nella sua versione più recente: **0 checksum mismatch, 0 missing local file, 0 unexpected local files**. Conferma che `data/` è coerente con la sorgente EBRAIN secondo tutti e 3 i controlli.
5. `docs/guides/retrieval.md` e `docs/dev/retrieval.md` risultano **già aggiornati** (modificati, non commitati) per documentare la feature di verifica — non serve intervento di documentazione da parte mia, era stato erroneamente segnalato come "non documentato" in un turno precedente di questa sessione prima che l'utente completasse l'editing.

### File modificati (non commitati — verificato con `git status`/`git diff`)

- **Codice**: `src/pipeline/retrieve_data.py` (+58, integrazione verifica), `scripts/verify_retrieval.py` (riscritto come thin wrapper, -100 righe circa)
- **Nuovo, non tracciato**: `src/retrieval/verify.py`, `tests/unit/test_verify.py`
- **Test modificati**: `tests/integration/test_lesion_counts.py`, `tests/integration/test_participants.py`, `tests/unit/test_retrieve_pipeline.py`
- **Doc**: `docs/dev/retrieval.md`, `docs/guides/retrieval.md`
- **Dati locali (gitignored, non impattano commit)**: `data/`, `logs/`, `reports/` popolati dal run

### Stato dei test

87/87 (unit+integration, **prima** dell'introduzione di `test_verify.py` nel working tree) — vedi nota al punto 1. `test_verify.py` non ancora incluso in un run pytest in questa sessione.

### Prossimo passo esatto

1. Rilanciare `conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v` includendo il nuovo `tests/unit/test_verify.py`, per avere un conteggio verde che copra anche la feature di verifica checksum.
2. Se si vuole un report su disco allineato al codice attuale (con tutte e 5 le sezioni: Missing, Ambiguous, Non-conforming, Mismatched, Not copied, Unexpected), rilanciare la pipeline un'altra volta.
3. Decidere se/quando committare il lavoro corrente (retrieval + verify + doc), attualmente tutto in working tree non staged.
4. Tornare al filone SDC/BCBToolKit (sessione (2)): email al gestore server ancora da inviare da parte dell'utente; nel frattempo Task1 (embedding UMAP/t-SNE su lesioni grezze) può partire senza aspettare.

---

## Sessione 2026-07-09 (2) — SDC/BCBToolKit: blocco permessi e mappatura pipeline del paper

### Obiettivo

Dare seguito ai due item aperti in TODO.md ("implementa SDC pipeline", "vedi se c'è da implementare lesion embedding"), partendo dal paper Thiebaut de Schotten et al. 2020 e dalle istruzioni di setup mandate da Chris Foulon (BCBToolKit/BCBlib maintainer).

### Blocco trovato: permessi insufficienti per il setup di Chris

Le istruzioni di Chris richiedono 4 step, verificati uno per uno su questo server:

| Step di Chris | Verificato | Esito |
|---|---|---|
| `git pull` su BCBToolKit esistente | `ls -la /data/tshimanga/BCBToolKit` | **Permission denied** — la cartella appartiene a `tshimanga`, non leggibile dall'utente `etosato` |
| `pip install` BCBlib | `pip show bcblib` in tutti e 4 gli env conda (`base`, `cebra`, `nemesis`, `rhosts`) | Non installato in nessuno — ma installabile senza problemi nel proprio env, nessun blocco di permessi qui |
| Cache condivisa atlanti `/shared/bcblib_atlases` | `ls /shared`, `find` fino a 4 livelli in `/data/corbetta` | La cartella **non esiste**, mai creata; creazione richiede permessi di sistema |
| Riga in `/etc/environment` (`BCBLIB_ATLAS_DIR`, `TEMPLATEFLOW_HOME`) | `cat /etc/environment`, `grep` in `/etc/profile.d/*.sh` | Nessuna traccia — richiede root |

Confermato anche con `df -h` la topologia storage: `/data/corbetta` è l'area di lab condivisa (NAS "memory:/corbetta"), `/data/<username>` sono aree personali di ogni utente — non esiste un meccanismo tipo "moduli" (niente cluster HPC/module system) che possa impostare queste variabili altrove.

**Conclusione verificata (non supposta)**: nessuna parte del setup di Chris risulta già fatta sul server. La richiesta a chi amministra il server è legittima e non ridondante.

### Azione presa

Bozza email pronta (in italiano, formale, con "Lei") per il gestore dei server, che:
- si presenta come dottoranda del laboratorio Corbetta (mail girata da Sebastiano Cinetto),
- elenca i 3 blocchi di permessi trovati,
- chiede di occuparsene lui o di dare accesso in scrittura a `/data/tshimanga/BCBToolKit`,
- propone il fallback: installazione locale nella propria home (clone BCBToolKit personale, BCBlib nell'env `nemesis`, cache atlanti/TemplateFlow sotto la propria home invece che `/shared`) se il gestore non può intervenire a breve.

**Stato**: mail da inviare da parte dell'utente (io non ho inviato nulla, non ho capacità di invio email). In attesa di risposta.

### Mappatura pipeline del paper → Task NEMESIS

Riletto Methods del paper e incrociato con `assets/meetings/Brainstorming.md` (Task1-5) e `assets/meetings/Seba Meeting.md`. Elenco completo delle pipeline del paper, in ordine di dipendenza, con dipendenza da BCBToolKit:

1. Stroke lesions (dato di partenza) — nessuna dipendenza
2. Synthetic lesions (k-means + smoothing, script BCBlib standalone) — nessuna dipendenza da BCBToolKit, non richiesto esplicitamente nei Task NEMESIS
3. **Disconnectome/SDC** (trattografia su 163 controlli HCP 7T) — **richiede BCBToolKit**, è il blocco attuale
4. Spatial embedding (t-SNE su mappe grezze, NON su punteggi PCA — le due sezioni Methods "Spatial embedding" e "Data compression" sono indipendenti) — versione lesione: nessun blocco; versione SDC: bloccata da #3
5. Data compression (parcellazione MMP+sottocorticali a 372 regioni + PCA varimax) — versione lesione: nessun blocco; versione SDC: bloccata da #3. **Nota**: la parcellazione non va reimplementata a mano, è un output diretto di `bcb-lesion-features` (CSV per atlante/soggetto)
6. Relazione con task-fMRI Neurosynth (590 mappe curate) — fuori scope NEMESIS (serve dataset esterno che non abbiamo, e il progetto usa outcome clinici, non fMRI meta-analitici)
7. Confronto statistico bootstrap sulle relazioni — fuori scope NEMESIS, specifico del contributo scientifico del paper
8. Component maps via FSL `randomise` (regressione permutata voxel-wise, split-half) — bloccata da #3; nei Task NEMESIS l'equivalente è molto più semplice ("media dei disconnettomi nel cluster", non regressione permutata)
9. Atlas of white matter function — fuori scope NEMESIS
10. Visualizzazione (Surf Ice/Trackvis) — solo estetica, tool esterni

**Mappatura diretta**: Task1 NEMESIS ("low dim embedding lesions + clustering topografico") = punto #4 versione lesione, sbloccato subito. Task2 NEMESIS ("low dim embedding SDC") = punti #3+#4 versione SDC, bloccato.

### Prossimo passo esatto

1. Attendere risposta del gestore server sulla mail (BCBToolKit/BCBlib/cache condivisa).
2. Nel frattempo, **si può iniziare il Task1** senza aspettare: codice in `src/` per embedding (t-SNE o UMAP, coerente con `Seba Meeting.md` che menziona UMAP) applicato **direttamente sulle maschere di lesione grezze** (non su feature parcellizzate/PCA — quello è un'analisi parallela, non un prerequisito), seguito da clustering. Ambiente già pronto (`nemesis` ha nibabel/nilearn/scikit-learn/umap-learn).
3. Attenzione se si riusa il pattern PCA-varimax del paper per altri scopi: `sklearn.manifold.TSNE` in questo ambiente ha `scikit-learn==1.8.0`, dove il parametro è `max_iter` (non più `n_iter`, deprecato/rimosso). `factor_analyzer` non è né in `environment.yml` né installato, va aggiunto se si vuole la rotazione varimax.
4. Non ancora scritto nessun codice per Task1/Task2 in questa sessione — solo ricerca, verifica permessi e bozza email.

---

## Obiettivo della sessione (retrieval, sessione precedente)

Costruire da zero il modulo di **data retrieval**: copia lesioni/derivatives/`participants.tsv` da EBRAIN (`/data/corbetta/Clinical_connectome`) a `data/` locale, pilotato da config JSON. Poi: verifica end-to-end, audit di silent-failure sul codice scritto, refactor architetturale (registro `file_patterns.json`), infrastruttura di lezioni apprese per agenti futuri.

## Architettura attuale (stato finale)

```
config/
├── data_retrieval.json   # request per-run: dataset, subject, retrieve, opzioni
└── file_patterns.json    # registro: (space, modality) -> [template path con {subject_id}]
src/retrieval/
├── config.py    # RetrieveItem, RetrievalConfig, FilePatterns, load_config, load_file_patterns
└── dataset.py   # Dataset: subjects(), group_of(), resolve(), available(), participants()
src/pipeline/
└── retrieve_data.py   # CLI: validate upfront (STOP) -> copy (WARNING) -> report + log
tests/unit/, tests/integration/   # 70 unit test (verdi), integration da rilanciare (vedi Prossimo passo)
docs/dev/retrieval.md      # tecnico
docs/guides/retrieval.md   # utente
docs/debugging/debug_09_07_26.md   # report storico di questa sessione, per categorie
.claude/lessons_learned.md          # indice cumulativo sintetico, riferito da CLAUDE.md
~/.claude/skills/silent-failure-audit/SKILL.md   # skill generale (scope utente, riutilizzabile)
```

## Decisioni architetturali chiave (con motivazione)

1. **Una sola classe `Dataset`**, non subclass per dataset — le differenze tra i 4 dataset (UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR) si scoprono da disco a runtime (`available()`), mai hardcoded per nome.

2. **`config/file_patterns.json`** — registro esplicito `space -> modality -> [template]`, sostituisce il vecchio approccio con `glob()` hardcoded in Python. Motivazione: (a) il glob per `lesion_roi` matchava ambiguamente due varianti di naming reali (`sub-X_lesion_roi.nii.gz` vs `sub-X_space-T1w_lesion_roi.nii.gz`) — verificato che ogni dataset usa consistentemente UNA delle due, mai entrambe per lo stesso soggetto, ma nulla lo garantiva nel codice; (b) l'utente vuole che il mapping sia "in chiaro", ispezionabile anche da colleghi non programmatori; (c) risolve anche il vecchio limite noto "non possiamo aggiungere una seconda mni derivative senza toccare Python".
   - **Importante**: `{subject_id}` nei template include già il prefisso `sub-` (es. `sub-STUNIPD0002`) — i template NON devono aggiungere un secondo `sub-` davanti. Bug reale trovato e corretto durante l'implementazione (vedi debug report §3 per dettagli, era `"sub-{subject_id}/anat/..."` invece di `"{subject_id}/anat/..."`).
   - Due modi per registrare varianti: stessa chiave con lista ordinata (priorità) se sono la stessa cosa logica; chiavi diverse se sono cose diverse. Scelta lasciata all'umano che edita il JSON, non inferita dal codice.
   - Se più template matchano per lo stesso soggetto: si usa il primo per priorità, MA si segnala sempre (mai silenzioso) — nuova sezione "Ambiguous" nel report + `stats.ambiguous` + log warning.

3. **`Dataset.resolve(subject_id, space, modality) -> ResolvedFile | None`** e **`Dataset.available(space, modality) -> bool`** sostituiscono i vecchi `native()`/`mni_mask()`/`available_sequences()`/`has_mni_mask()` — unificati perché con il registro la logica è identica per native/mni, non serve più duplicarla.

4. **`subjects()` filtra sempre le cartelle non conformi allo schema `sub-<DISEASE><SITE>[HC]<NUM>`**, indipendentemente da `group_filter`. Prima: crashava SOLO se si usava `group_filter` (perché `group_of()` veniva chiamato solo lì), altrimenti la cartella veniva assorbita silenziosamente come soggetto vero. Ora: sempre esclusa, mai crash, sempre segnalata esplicitamente in una nuova sezione "Non-conforming subject folders" del report (`Dataset.non_conforming_subject_folders()` + `stats.non_conforming`).

5. **`RetrieveItem.__post_init__`** valida solo `space` (invariante statica, native/mni). La validità di `modality` per un dato `space` dipende ora dal registro esterno `file_patterns.json`, quindi è stata spostata in `config._require_known_combinations`, chiamata una volta in `load_config` dopo aver caricato sia `retrieve` che `file_patterns`.

6. **Duplicati rigettati esplicitamente, mai deduplicati in silenzio**: sia in `retrieve` (config.py, `_reject_duplicate_retrieve_items`) sia — bug trovato e corretto nella stessa sessione — in `config.subjects` quando si calcolano i soggetti assenti da un dataset specifico (`_report_explicit_subjects_absent_from_dataset`, ora usa `dict.fromkeys` per deduplicare prima di generare le righe di report).

7. **Report** (`reports/data_retrieval/<project>/<dd-mm-yy>__<hh-mm>.md`): titolo `<project>_<dd-mm-yy>`, sottotitolo orario, dump JSON del config effettivamente usato, tabella riassuntiva, poi 3 sezioni raggruppate per dataset con conteggio e separatore `---`: **Missing**, **Ambiguous**, **Non-conforming subject folders**.

8. **Log** (`logs/data_retrieval/<project>/<dd-mm-yy>__<hh-mm>.log`): stesso timestamp del report (accoppiati per nome file), narrativa completa oltre alla console. Handler ripulito a ogni chiamata di `main()` per evitare leak tra run multipli nello stesso processo (rilevante per uso in notebook).

## File modificati/creati in questa sessione

**Codice**: `src/retrieval/config.py`, `src/retrieval/dataset.py`, `src/pipeline/retrieve_data.py` (riscritti quasi interamente più volte durante la sessione)

**Config**: `config/data_retrieval.json` (aggiunto campo `file_patterns`), `config/file_patterns.json` (nuovo)

**Test**: tutti riscritti/aggiornati per il nuovo schema `Dataset(project_root, name, file_patterns)`:
`tests/unit/test_config.py`, `test_dataset_identity.py`, `test_dataset_lesion.py`, `test_dataset_participants.py`, `test_retrieve_pipeline.py`; `tests/integration/test_lesion_counts.py`, `test_participants.py`, `test_retrieve_pipeline.py`

**Documentazione**: `docs/dev/retrieval.md`, `docs/guides/retrieval.md` (riscritti con la nuova architettura)

**Infrastruttura lezioni apprese** (nuova, questa sessione):
`docs/debugging/debug_09_07_26.md`, `.claude/lessons_learned.md`, `.claude/CLAUDE.md` (aggiunta sezione "Lessons learned" con `@lessons_learned.md`), `~/.claude/skills/silent-failure-audit/SKILL.md` (skill generale, scope utente `~/.claude/skills/`, riutilizzabile in altri progetti)

**Nota**: `.claude/code_standards.md` §8 era stato temporaneamente esteso con un protocollo di aggiornamento del cumulativo, poi **rimosso su richiesta esplicita dell'utente** ("c'è già la skill, è troppo specifico per gli agenti più che sullo stile") — §8 ora è tornato quasi alla forma originale, solo il path corretto da `debug_reports/` a `debugging/`.

## Errori trovati e corretti (dettaglio completo in `docs/debugging/debug_09_07_26.md`, sintesi in `.claude/lessons_learned.md`)

7 categorie: (1) fallback implicito in if/else senza else esplicito — fix: validazione in `__post_init__`; (2) validazione ancorata a un solo call site — fix: cross-validazione centralizzata; (3) match multipli su glob ambiguo — fix: registro esplicito con priorità + segnalazione; (4) comportamento incoerente tra percorsi di codice (crash vs assorbimento silenzioso per cartelle non conformi) — fix: controllo unificato in `subjects()`; (5) duplicati non rilevati in liste — fix: rigetto esplicito, trovato in due punti diversi nella stessa sessione; (6) disponibilità aggregata vs per-elemento — non un bug, documentato; (7) forma dati esterni non validata — fix: controllo `isinstance(raw, dict)` esplicito.

## Stato dei test

**70/70 unit test passano** (`conda run -n nemesis python -m pytest tests/unit/ -v`, ultima esecuzione dopo il refactor `file_patterns`).

**Test di integrazione (EBRAIN reale) NON ancora rilanciati dopo il refactor `file_patterns`** — erano stati aggiornati per usare il registro reale `config/file_patterns.json` via `load_file_patterns()`, ma l'ultima esecuzione completa (`tests/unit/ tests/integration/`) risale a PRIMA di questo refactor (quando l'API era ancora `native()`/`mni_mask()`).

## Osservazione da verificare nella prossima sessione

`git status` mostra `D reports/data_retrieval/clinical_connectome/09-07-26__10-49.md` — un file di report che risultava **tracciato da git** (probabilmente incluso in un commit parallelo dell'utente) è stato cancellato durante un cleanup di file di smoke-test in questa sessione. Verificare con l'utente se va ripristinato o se la cancellazione va bene (i report sono normalmente artefatti rigenerabili, non dati permanenti).

## Prossimo passo esatto

1. Rilanciare la suite completa: `conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v` (richiede mount EBRAIN) e riportare il conteggio esatto — è il primo vero test del registro `file_patterns.json` contro i dati reali (in particolare `test_no_ambiguous_matches_across_real_data` e i conteggi mni/T1w/available in `test_lesion_counts.py`).
2. Se verde: fare un run reale completo (`python -m src.pipeline.retrieve_data --config config/data_retrieval.json`) per generare un report/log con il nuovo formato completo (incluse le sezioni Ambiguous/Non-conforming) su dati reali, e ispezionarlo.
3. Chiarire con l'utente il punto sul file di report cancellato (vedi sopra).
4. Chiedere se procedere con la fase successiva del progetto (processing/embedding — vedi `docs/notes/architecture_draft.md` non normativo) o restare sul modulo di retrieval.
