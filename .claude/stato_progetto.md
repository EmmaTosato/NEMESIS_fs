# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-07-09. Scritto per permettere a un nuovo agente/sessione di riprendere senza contesto pregresso. Il file copre più sessioni, in ordine cronologico inverso (la più recente in cima).

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
